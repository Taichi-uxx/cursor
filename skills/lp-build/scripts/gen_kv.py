#!/usr/bin/env python3
"""gen_kv.py — テキストを含まない LP ファーストビュー用「背景キービジュアル(KV)」生成スクリプト.

このスクリプトは LP のファーストビュー(FV)で使う *背景画像のみ* を生成する。
キャッチコピー・CTA・ロゴ等の文字は後段 (compose_fv.py + Playwright) で
HTML/CSS により正確な日本語で重ねるため、画像には一切テキストを入れさせない。

------------------------------------------------------------------------------
プロバイダ・フォールバックチェーン (provider-agnostic 設計)
------------------------------------------------------------------------------
複数プロバイダを「順に試し、エラーが出たら次へ」フォールバックする。
チェーンの決定順:
  1. 環境変数 `IMAGE_PROVIDER_CHAIN` (カンマ区切り) があればそれを使う
  2. 無く `IMAGE_PROVIDER` (単一) があれば、それ1つだけ (自動フォールバックなし)
  3. どちらも無ければ **既定チェーン = gemini,openai**
     ＝ Gemini を基本、エラー時 OpenAI(GPT Image) で代替
     (2026-05-19時点 OpenAI は請求ハード上限のため当面 Gemini 主)

対応プロバイダとキー / モデル上書き用環境変数:
  - openai     : OPENAI_API_KEY            / model: OPENAI_IMAGE_MODEL (既定 gpt-image-1)
  - gemini     : GEMINI_API_KEY|GOOGLE_API_KEY / model: GEMINI_IMAGE_MODEL
                 (既定 gemini-3.1-flash-image-preview。
                  別モデルを使う場合のみ GEMINI_IMAGE_MODEL で上書き)
  - fal        : FAL_KEY
  - replicate  : REPLICATE_API_TOKEN

チェーン全てが失敗した場合のみ非ゼロ終了する:
  - 全て「キー未設定」起因          -> exit 2 (設定不足。必要キー名を表示)
  - 1つでも実呼び出しが失敗(API等) -> exit 1 (集約エラーを表示)

新しいプロバイダ "foo" を追加したい場合:
  1. `def _generate_foo(prompt, size_key, count) -> list[bytes]:` を実装
     (APIキーは os.environ.get 経由。不在時 MissingApiKeyError を raise)
  2. `_PROVIDERS` に `"foo": _generate_foo` を登録
  3. `_provider_env_hint` にキー名を追加
  4. requirements.txt / README.md に SDK・環境変数名を追記 (キー値は書かない)

秘匿情報 (APIキー・.env の中身) は stdout/stderr/ログに一切出力しない。
正常時、標準出力には JSON 1 行のみを出す:
  {"images":[{"size":"sp","path":"<abs>"},...],"provider":"<使用provider>"}
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# .env 読み込み (find_dotenv で上方向探索 + パス明示の両方)
# ---------------------------------------------------------------------------
_DOTENV_LOADED = False
try:
    from dotenv import load_dotenv  # type: ignore

    try:
        from dotenv import find_dotenv  # type: ignore

        _auto = find_dotenv(usecwd=True)
    except Exception:
        _auto = ""

    # 探索順 (中身は読まず存在のみ判定 -> load_dotenv が読み込む):
    #   1) 明示指定 LP_BUILD_ENV_FILE
    #   2) cwd から上方向探索
    #   3) 既知の候補パス
    _candidates: list[str] = []
    _explicit_var = os.environ.get("LP_BUILD_ENV_FILE", "").strip()
    if _explicit_var:
        _candidates.append(_explicit_var)
    if _auto:
        _candidates.append(_auto)
    _candidates += [
        "/Users/apple/.cursor/.env",
        str(Path(__file__).resolve().parents[1] / ".env"),  # skills/lp-build/.env
        str(Path.home() / ".cursor" / ".env"),
        str(Path.home() / ".env"),
    ]
    _seen: set[str] = set()
    for _c in _candidates:
        if not _c or _c in _seen:
            continue
        _seen.add(_c)
        try:
            if Path(_c).is_file():
                load_dotenv(_c, override=False)
                _DOTENV_LOADED = True
        except Exception:
            pass
except Exception:
    # python-dotenv 未導入でも環境変数が直接設定されていれば動作させる。
    # ここでは .env の内容に一切触れない。
    pass


# ---------------------------------------------------------------------------
# 例外
# ---------------------------------------------------------------------------
class MissingApiKeyError(Exception):
    """画像生成 API キーが未設定 (チェーン全滅時に exit 2 へ集約)。"""


class ProviderError(Exception):
    """プロバイダ呼び出しに失敗 (ネットワーク/サーバ/レスポンス不正等)。"""


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
_TIMEOUT_SEC = 180
_MAX_RETRIES = 2  # 初回 + リトライ2回 = 計3回試行 (各プロバイダ内)
_RETRY_BACKOFF_SEC = 4

# OpenAI gpt-image-1 がサポートするサイズ (sp=スマホ縦長 / pc=PC横長)
_OPENAI_SIZE = {"sp": "1024x1536", "pc": "1536x1024"}
_OPENAI_MODEL_DEFAULT = "gpt-image-1"

# Gemini 既定モデルID＝gemini-3.1-flash-image-preview（最新flash・田村確認/ListModels実在確認済）。
# 別IDを使う場合は GEMINI_IMAGE_MODEL で上書き可。
_GEMINI_MODEL_DEFAULT = "gemini-3.1-flash-image-preview"

# 既定フォールバックチェーン: Gemini を基本 -> エラー時 OpenAI で代替
# （2026-05-19時点 OpenAI は請求ハード上限のため当面 Gemini 主。
#   OpenAI 上限解除後は IMAGE_PROVIDER_CHAIN=openai,gemini に戻す想定）
_DEFAULT_CHAIN = ["gemini", "openai"]

_PROMPT_HARDENING_TMPL = (
    " no text, no letters, no typography, no logo, no watermark; "
    "leave clean negative space at the {focal} for a headline overlay; "
    "high-end editorial advertising key visual"
)


def _provider_env_hint(provider: str) -> str:
    return {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "fal": "FAL_KEY",
        "replicate": "REPLICATE_API_TOKEN",
    }.get(provider, "OPENAI_API_KEY")


def _harden_prompt(user_prompt: str, focal: str) -> str:
    """ユーザープロンプト末尾に必ずテキスト禁止/ネガティブスペース指示を付与。"""
    base = user_prompt.strip().rstrip(".") if user_prompt else "abstract premium brand background"
    return base + _PROMPT_HARDENING_TMPL.format(focal=focal)


def _img_ext(data: bytes) -> str:
    """マジックバイトから実フォーマットの拡張子を判定 (既定 png)。

    プロバイダにより JPEG/PNG/WebP が返るため、拡張子を中身に一致させる
    (下流は本スクリプトの出力 JSON の path をそのまま使うので整合は保たれる)。
    """
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return "png"


# ---------------------------------------------------------------------------
# OpenAI プロバイダ (GPT Image。model は OPENAI_IMAGE_MODEL で上書き可)
# ---------------------------------------------------------------------------
def _generate_openai(prompt: str, size_key: str, count: int) -> list[bytes]:
    """GPT Image で画像生成。openai SDK があれば使用、無ければ requests REST。"""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise MissingApiKeyError("OPENAI_API_KEY")

    size = _OPENAI_SIZE[size_key]
    model = os.environ.get("OPENAI_IMAGE_MODEL", _OPENAI_MODEL_DEFAULT).strip() or _OPENAI_MODEL_DEFAULT

    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            # --- 優先: 公式 SDK ---
            try:
                from openai import OpenAI  # type: ignore

                client = OpenAI(api_key=api_key, timeout=_TIMEOUT_SEC)
                resp = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    n=count,
                )
                images: list[bytes] = []
                for item in resp.data:
                    b64 = getattr(item, "b64_json", None)
                    if not b64:
                        raise ProviderError("OpenAI レスポンスに画像データ(b64_json)が含まれていません。")
                    images.append(base64.b64decode(b64))
                return images
            except ImportError:
                pass  # SDK 無し -> REST にフォールバック

            # --- フォールバック: requests で REST ---
            import requests  # type: ignore

            r = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "prompt": prompt, "size": size, "n": count},
                timeout=_TIMEOUT_SEC,
            )
            if r.status_code == 401:
                # 認証失敗はキー不正。キー値そのものは絶対に出さない。
                raise MissingApiKeyError("OPENAI_API_KEY")
            if r.status_code >= 400:
                msg = ""
                try:
                    msg = r.json().get("error", {}).get("message", "")
                except Exception:
                    msg = ""
                raise ProviderError(
                    f"OpenAI API がエラーを返しました (HTTP {r.status_code}) {msg}".strip()
                )
            payload = r.json()
            data = payload.get("data") or []
            if not data:
                raise ProviderError("OpenAI レスポンスに画像データが含まれていません。")
            images = []
            for item in data:
                b64 = item.get("b64_json")
                if not b64:
                    raise ProviderError("OpenAI レスポンスに画像データ(b64_json)が含まれていません。")
                images.append(base64.b64decode(b64))
            return images

        except MissingApiKeyError:
            raise  # キー問題はリトライしない (上位でフォールバック判定)
        except (binascii.Error, ValueError) as e:
            raise ProviderError(f"画像データのデコードに失敗しました: {e}") from e
        except Exception as e:  # ネットワーク/タイムアウト/サーバ等
            last_err = e
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise ProviderError(
                f"OpenAI 画像生成に {(_MAX_RETRIES + 1)} 回失敗しました: {e}"
            ) from e

    raise ProviderError(f"OpenAI 画像生成に失敗しました: {last_err}")


# ---------------------------------------------------------------------------
# Gemini プロバイダ (Nano Banana。model は GEMINI_IMAGE_MODEL で上書き可)
# ---------------------------------------------------------------------------
def _extract_gemini_image_rest(data: dict) -> bytes:
    for cand in data.get("candidates", []) or []:
        content = cand.get("content", {}) or {}
        for part in content.get("parts", []) or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise ProviderError("Gemini レスポンスに画像データ(inlineData)が含まれていません。")


def _extract_gemini_image_sdk(resp) -> bytes:
    try:
        for cand in resp.candidates:
            for part in cand.content.parts:
                inline = getattr(part, "inline_data", None)
                if inline is not None and getattr(inline, "data", None):
                    raw = inline.data
                    if isinstance(raw, (bytes, bytearray)):
                        return bytes(raw)
                    return base64.b64decode(raw)
    except Exception:
        pass
    raise ProviderError("Gemini レスポンスに画像データが含まれていません。")


def _generate_gemini(prompt: str, size_key: str, count: int) -> list[bytes]:
    """Gemini(Nano Banana) で画像生成。google-genai SDK があれば使用、無ければ REST。

    Gemini 画像系はサイズを明示パラメータで取らないため、アスペクト指示は
    プロンプト末尾に言語で付与する (sp=縦長 / pc=横長)。
    """
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    ).strip()
    if not api_key:
        raise MissingApiKeyError("GEMINI_API_KEY")

    model = os.environ.get("GEMINI_IMAGE_MODEL", _GEMINI_MODEL_DEFAULT).strip() or _GEMINI_MODEL_DEFAULT
    aspect = (
        "vertical 2:3 portrait composition"
        if size_key == "sp"
        else "horizontal 3:2 landscape composition"
    )
    full_prompt = f"{prompt}; {aspect}"

    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            # --- 優先: 公式 SDK (google-genai) ---
            try:
                from google import genai  # type: ignore
                from google.genai import types  # type: ignore

                client = genai.Client(api_key=api_key)
                images: list[bytes] = []
                for _ in range(count):
                    resp = client.models.generate_content(
                        model=model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        ),
                    )
                    images.append(_extract_gemini_image_sdk(resp))
                return images
            except ImportError:
                pass  # SDK 無し -> REST にフォールバック

            # --- フォールバック: requests で REST ---
            import requests  # type: ignore

            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent"
            )
            images = []
            for _ in range(count):
                r = requests.post(
                    url,
                    headers={
                        "x-goog-api-key": api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {"responseModalities": ["IMAGE"]},
                    },
                    timeout=_TIMEOUT_SEC,
                )
                if r.status_code in (401, 403):
                    raise MissingApiKeyError("GEMINI_API_KEY")
                if r.status_code >= 400:
                    msg = ""
                    try:
                        msg = r.json().get("error", {}).get("message", "")
                    except Exception:
                        msg = ""
                    raise ProviderError(
                        f"Gemini API がエラーを返しました (HTTP {r.status_code}) {msg}".strip()
                    )
                images.append(_extract_gemini_image_rest(r.json()))
            return images

        except MissingApiKeyError:
            raise
        except (binascii.Error, ValueError) as e:
            raise ProviderError(f"画像データのデコードに失敗しました: {e}") from e
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise ProviderError(
                f"Gemini 画像生成に {(_MAX_RETRIES + 1)} 回失敗しました: {e}"
            ) from e

    raise ProviderError(f"Gemini 画像生成に失敗しました: {last_err}")


# ---------------------------------------------------------------------------
# fal プロバイダ (実装済み・SDK/キー不在時は明快に終了)
# ---------------------------------------------------------------------------
def _generate_fal(prompt: str, size_key: str, count: int) -> list[bytes]:
    """fal.ai で画像生成。

    リクエスト形 (拡張時の参考):
        import fal_client
        result = fal_client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "portrait_16_9" if size_key == "sp" else "landscape_16_9",
                "num_images": count,
            },
        )
        # result["images"][i]["url"] を requests.get で取得し PNG バイト列へ
    """
    api_key = os.environ.get("FAL_KEY", "").strip()
    if not api_key:
        raise MissingApiKeyError("FAL_KEY")

    image_size = "portrait_16_9" if size_key == "sp" else "landscape_16_9"

    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            try:
                import fal_client  # type: ignore
            except ImportError as e:
                raise ProviderError(
                    "fal を使うには `pip install fal-client` が必要です。"
                ) from e

            import requests  # type: ignore

            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": image_size,
                    "num_images": count,
                },
            )
            urls = [img.get("url") for img in (result or {}).get("images", []) if img.get("url")]
            if not urls:
                raise ProviderError("fal レスポンスに画像 URL が含まれていません。")
            images: list[bytes] = []
            for u in urls:
                rr = requests.get(u, timeout=_TIMEOUT_SEC)
                if rr.status_code >= 400:
                    raise ProviderError(f"fal 画像の取得に失敗しました (HTTP {rr.status_code})。")
                images.append(rr.content)
            return images
        except MissingApiKeyError:
            raise
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise ProviderError(f"fal 画像生成に失敗しました: {e}") from e
    raise ProviderError(f"fal 画像生成に失敗しました: {last_err}")


# ---------------------------------------------------------------------------
# replicate プロバイダ (実装済み・SDK/キー不在時は明快に終了)
# ---------------------------------------------------------------------------
def _generate_replicate(prompt: str, size_key: str, count: int) -> list[bytes]:
    """Replicate で画像生成。

    リクエスト形 (拡張時の参考):
        import replicate
        out = replicate.run(
            "black-forest-labs/flux-dev",
            input={
                "prompt": prompt,
                "aspect_ratio": "2:3" if size_key == "sp" else "3:2",
                "num_outputs": count,
            },
        )
        # out は URL or file-like のリスト。requests.get で PNG バイト列へ
    """
    api_key = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not api_key:
        raise MissingApiKeyError("REPLICATE_API_TOKEN")

    aspect = "2:3" if size_key == "sp" else "3:2"

    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            try:
                import replicate  # type: ignore
            except ImportError as e:
                raise ProviderError(
                    "replicate を使うには `pip install replicate` が必要です。"
                ) from e

            import requests  # type: ignore

            out = replicate.run(
                "black-forest-labs/flux-dev",
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect,
                    "num_outputs": count,
                },
            )
            items = out if isinstance(out, (list, tuple)) else [out]
            images: list[bytes] = []
            for it in items:
                if hasattr(it, "read"):
                    images.append(it.read())
                else:
                    rr = requests.get(str(it), timeout=_TIMEOUT_SEC)
                    if rr.status_code >= 400:
                        raise ProviderError(
                            f"Replicate 画像の取得に失敗しました (HTTP {rr.status_code})。"
                        )
                    images.append(rr.content)
            if not images:
                raise ProviderError("Replicate レスポンスに画像が含まれていません。")
            return images
        except MissingApiKeyError:
            raise
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SEC * (attempt + 1))
                continue
            raise ProviderError(f"Replicate 画像生成に失敗しました: {e}") from e
    raise ProviderError(f"Replicate 画像生成に失敗しました: {last_err}")


_PROVIDERS: dict[str, Callable[[str, str, int], list[bytes]]] = {
    "openai": _generate_openai,
    "gemini": _generate_gemini,
    "fal": _generate_fal,
    "replicate": _generate_replicate,
}


# ---------------------------------------------------------------------------
# チェーン解決
# ---------------------------------------------------------------------------
def _resolve_chain() -> list[str]:
    """フォールバックチェーンを決定 (順序保持・重複除去)。"""
    raw_chain = os.environ.get("IMAGE_PROVIDER_CHAIN", "").strip()
    if raw_chain:
        chain = [p.strip().lower() for p in raw_chain.split(",") if p.strip()]
    else:
        single = os.environ.get("IMAGE_PROVIDER", "").strip().lower()
        chain = [single] if single else list(_DEFAULT_CHAIN)
    seen: set[str] = set()
    return [p for p in chain if not (p in seen or seen.add(p))]


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="gen_kv.py",
        description="LP ファーストビュー用の背景キービジュアル(KV)を生成 (テキスト無し)。",
    )
    p.add_argument("--prompt", required=True, help="背景ビジュアルの説明 (文字指示は不要)")
    p.add_argument("--out-dir", required=True, help="出力ディレクトリ")
    p.add_argument("--n", type=int, default=1, help="各サイズあたりの生成枚数 (default 1)")
    p.add_argument(
        "--size",
        choices=["sp", "pc", "both"],
        default="both",
        help="生成サイズ (default both)",
    )
    p.add_argument(
        "--focal",
        choices=["center-left", "center", "center-right"],
        default="center-left",
        help="見出しを重ねる余白の位置 (default center-left)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    chain = _resolve_chain()
    if not chain:
        sys.stderr.write("プロバイダチェーンが空です。IMAGE_PROVIDER_CHAIN を確認してください\n")
        return 2
    unknown = [p for p in chain if p not in _PROVIDERS]
    if unknown:
        sys.stderr.write(
            f"未対応のプロバイダ {unknown} が含まれています。"
            f"対応: {', '.join(sorted(_PROVIDERS))}\n"
        )
        return 2

    if args.n < 1:
        sys.stderr.write("--n は 1 以上を指定してください\n")
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"出力ディレクトリを作成できません: {e}\n")
        return 1

    sizes = ["sp", "pc"] if args.size == "both" else [args.size]

    # プロバイダを順に試行 (1プロバイダで全サイズ成功してから採用＝SP/PC混在を防ぐ)
    errors: list[tuple[str, str, str]] = []  # (provider, kind, message)
    collected: list[tuple[str, int, bytes]] = []
    used: str | None = None

    for provider in chain:
        generator = _PROVIDERS[provider]
        try:
            tmp: list[tuple[str, int, bytes]] = []
            for size_key in sizes:
                prompt = _harden_prompt(args.prompt, args.focal)
                images = generator(prompt, size_key, args.n)
                if not images:
                    raise ProviderError(f"{size_key}: 画像が生成されませんでした")
                for i, png in enumerate(images, start=1):
                    if not png:
                        raise ProviderError(f"{size_key}#{i}: 空の画像データを受信しました")
                    tmp.append((size_key, i, png))
            collected = tmp
            used = provider
            break
        except MissingApiKeyError as e:
            errors.append((provider, "missing_key", str(e)))
            sys.stderr.write(
                f"[{provider}] APIキー未設定。次のプロバイダへフォールバックします\n"
            )
            continue
        except ProviderError as e:
            errors.append((provider, "provider_error", str(e)))
            sys.stderr.write(
                f"[{provider}] 失敗。次のプロバイダへフォールバックします: {e}\n"
            )
            continue
        except KeyboardInterrupt:
            sys.stderr.write("中断されました\n")
            return 130

    if used is None:
        only_missing = bool(errors) and all(k == "missing_key" for _, k, _ in errors)
        if only_missing or not errors:
            keys = ", ".join(_provider_env_hint(p) for p in chain)
            hint = (
                ""
                if _DOTENV_LOADED
                else " ※.env を読み込めていません: python-dotenv 未導入か、"
                "環境変数 LP_BUILD_ENV_FILE で .env の絶対パスを指定してください"
            )
            sys.stderr.write(
                "画像生成APIキーが未設定です。.env に対応キーのいずれかを設定してください "
                f"(チェーン {','.join(chain)} / 必要キー候補: {keys}). "
                f"既定は openai→gemini フォールバック{hint}\n"
            )
            return 2
        detail = "; ".join(f"{p}:{msg}" for p, _, msg in errors)
        sys.stderr.write(f"全プロバイダで画像生成に失敗しました: {detail}\n")
        return 1

    # ここまで来たら採用プロバイダで全サイズ成功。ファイル書き出し。
    results: list[dict[str, str]] = []
    try:
        for size_key, i, png in collected:
            dest = out_dir / f"kv_{size_key}_{i}.{_img_ext(png)}"
            dest.write_bytes(png)
            results.append({"size": size_key, "path": str(dest)})
    except OSError as e:
        sys.stderr.write(f"画像の保存に失敗しました: {e}\n")
        return 1

    # 標準出力には JSON のみ (秘匿情報なし)。provider は参考情報。
    sys.stdout.write(
        json.dumps({"images": results, "provider": used}, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

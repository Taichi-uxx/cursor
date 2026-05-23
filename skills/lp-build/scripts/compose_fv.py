#!/usr/bin/env python3
"""compose_fv.py — KV 背景画像の上に FV コピー/CTA/ロゴを HTML/CSS で重ねる.

gen_kv.py が生成したテキスト無し背景KV画像 (SP/PC) の上に、日本語が正確に
表示されるファーストビュー(FV)のメインコピー・サブコピー・CTA・ロゴを
HTML/CSS で重ね合わせ、SP 用 / PC 用の 2 つの HTML を出力する。

出力HTMLはKVを**相対参照**する。Playwright MCP は `file:` を
ブロックするため、レンダリングは呼び出し側スキルが out_dir を
ローカルHTTP配信し `http://127.0.0.1:PORT/fv_sp.html` を開いて行う。
このスクリプトの責務は HTML 生成までとする。

------------------------------------------------------------------------------
copy JSON スキーマ
------------------------------------------------------------------------------
{
  "eyebrow":   "(任意 小ラベル)",
  "main":      "<メインコピー>",          # 必須
  "sub":       "<サブコピー>",            # 必須
  "cta":       "<CTAラベル>",             # 必須
  "logo_text": "(任意)",
  "theme": {                              # 省略時は妥当なデフォルト
    "text_color": "#ffffff",
    "accent":     "#ff5a2b",
    "overlay":    "rgba(0,0,0,0.35)",
    "align":      "left" | "center",
    "position":   "top" | "center" | "bottom"
  }
}

依存は標準ライブラリのみ (string.Template)。jinja 等の外部依存は使わない。
ネットワークアクセスなし。フォントは system フォントのみ。
正常時、標準出力には JSON 1 行のみ:
  {"sp":"<abs fv_sp.html>","pc":"<abs fv_pc.html>"}
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from string import Template

# テンプレートの位置 (scripts/ から見て ../templates/fv_template.html)
_TEMPLATE_PATH = (Path(__file__).resolve().parent / ".." / "templates" / "fv_template.html").resolve()

# fv_template.html と厳密一致させるプレースホルダ集合 (整合性検証に使用)
_REQUIRED_PLACEHOLDERS = {
    "bg_image_url",
    "eyebrow_html",
    "main_html",
    "sub_html",
    "cta_label",
    "logo_html",
    "text_color",
    "accent_color",
    "overlay_color",
    "align",
    "position",
    "viewport",
}

# theme デフォルト
_DEFAULT_THEME = {
    "text_color": "#ffffff",
    "accent": "#ff5a2b",
    "overlay": "rgba(0,0,0,0.35)",
    "align": "left",
    "position": "bottom",
}

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_COLOR_FN_RE = re.compile(r"^(?:rgb|rgba|hsl|hsla)\([0-9.,\s%/-]+\)$", re.IGNORECASE)


def _safe_color(value: object, fallback: str) -> str:
    """CSS 注入を防ぐため色値を厳格に検証。不正なら fallback。"""
    if not isinstance(value, str):
        return fallback
    v = value.strip()
    if _HEX_RE.match(v) or _COLOR_FN_RE.match(v):
        return v
    return fallback


def _esc(text: object) -> str:
    """HTML エスケープ。改行は <br> に変換 (見出しの意図的改行を許容)。"""
    s = "" if text is None else str(text)
    s = html.escape(s, quote=True)
    return s.replace("\n", "<br>")


def _localize_kv(path_str: str, label: str, out_dir: Path) -> str:
    """KV画像を out_dir 配下に置き、HTMLからの**相対URL(ファイル名)**を返す。

    Playwright MCP は `file:` プロトコルをブロックするため、出力HTMLは
    KVを相対参照し、スキル側が out_dir をローカルHTTPで配信して開く。
    相対参照なら http 配信でも（将来 file: 許可時でも）解決できる。
    """
    import shutil
    from urllib.parse import quote

    p = Path(path_str).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"{label} の画像が見つかりません: {p}")
    if p.parent == out_dir:
        rel = p.name  # 既に out_dir 内（gen_kv 出力の通常ケース）→ コピー不要
    else:
        dest = out_dir / p.name
        if dest.resolve() != p:
            shutil.copy2(p, dest)
        rel = dest.name
    return quote(rel)


def _load_copy(spec: str) -> dict:
    """--copy 引数を解釈。ファイルパスなら読み込み、それ以外は inline JSON。"""
    candidate = Path(spec).expanduser()
    raw: str
    if candidate.is_file():
        raw = candidate.read_text(encoding="utf-8")
    else:
        raw = spec
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"--copy の JSON 解析に失敗しました ({e})。ファイルパスまたは "
            f"有効な JSON 文字列を指定してください。"
        ) from e
    if not isinstance(data, dict):
        raise ValueError("--copy の JSON はオブジェクト({...})である必要があります。")
    return data


def _build_blocks(copy: dict) -> dict[str, str]:
    """copy dict から各プレースホルダ値を構築 (検証 + エスケープ済み)。"""
    main = copy.get("main")
    sub = copy.get("sub")
    cta = copy.get("cta")
    missing = [k for k, v in (("main", main), ("sub", sub), ("cta", cta)) if not (isinstance(v, str) and v.strip())]
    if missing:
        raise ValueError(f"copy JSON に必須項目が不足/空です: {', '.join(missing)}")

    theme = copy.get("theme") or {}
    if not isinstance(theme, dict):
        theme = {}

    text_color = _safe_color(theme.get("text_color"), _DEFAULT_THEME["text_color"])
    accent = _safe_color(theme.get("accent"), _DEFAULT_THEME["accent"])
    overlay = _safe_color(theme.get("overlay"), _DEFAULT_THEME["overlay"])

    align = theme.get("align")
    align = align if align in ("left", "center") else _DEFAULT_THEME["align"]
    position = theme.get("position")
    position = position if position in ("top", "center", "bottom") else _DEFAULT_THEME["position"]

    eyebrow = copy.get("eyebrow")
    eyebrow_html = (
        f'<span class="fv__eyebrow">{_esc(eyebrow)}</span>'
        if isinstance(eyebrow, str) and eyebrow.strip()
        else ""
    )
    logo_text = copy.get("logo_text")
    logo_html = (
        f'<div class="fv__logo">{_esc(logo_text)}</div>'
        if isinstance(logo_text, str) and logo_text.strip()
        else ""
    )

    return {
        "eyebrow_html": eyebrow_html,
        "main_html": _esc(main),
        "sub_html": _esc(sub),
        "cta_label": _esc(cta),
        "logo_html": logo_html,
        "text_color": text_color,
        "accent_color": accent,
        "overlay_color": overlay,
        "align": align,
        "position": position,
    }


def _verify_template(template_text: str) -> None:
    """テンプレ側のプレースホルダ集合とコード側が厳密一致するか検証。"""
    found = set(re.findall(r"\$(?:\{)?([a-zA-Z_][a-zA-Z0-9_]*)", template_text))
    missing_in_template = _REQUIRED_PLACEHOLDERS - found
    extra_in_template = found - _REQUIRED_PLACEHOLDERS
    if missing_in_template:
        raise ValueError(
            "テンプレートに必要なプレースホルダがありません: "
            + ", ".join(sorted(missing_in_template))
        )
    if extra_in_template:
        raise ValueError(
            "テンプレートに未知のプレースホルダがあります: "
            + ", ".join(sorted(extra_in_template))
        )


def _render(template_text: str, mapping: dict[str, str]) -> str:
    """string.Template で厳密置換 ($identifier の取りこぼしを許さない)。"""
    return Template(template_text).substitute(mapping)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="compose_fv.py",
        description="KV 背景に FV コピー/CTA を重ねた SP/PC HTML を生成。",
    )
    p.add_argument("--kv-sp", required=True, help="SP 用 KV 画像パス")
    p.add_argument("--kv-pc", required=True, help="PC 用 KV 画像パス")
    p.add_argument(
        "--copy",
        required=True,
        help="copy JSON のファイルパス、または inline JSON 文字列",
    )
    p.add_argument("--out-dir", required=True, help="出力ディレクトリ")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    try:
        if not _TEMPLATE_PATH.is_file():
            sys.stderr.write(
                f"テンプレートが見つかりません: {_TEMPLATE_PATH}\n"
            )
            return 1
        template_text = _TEMPLATE_PATH.read_text(encoding="utf-8")
        _verify_template(template_text)

        copy = _load_copy(args.copy)
        blocks = _build_blocks(copy)

        out_dir = Path(args.out_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        sp_bg = _localize_kv(args.kv_sp, "--kv-sp", out_dir)
        pc_bg = _localize_kv(args.kv_pc, "--kv-pc", out_dir)

        sp_html = _render(
            template_text, {**blocks, "bg_image_url": sp_bg, "viewport": "sp"}
        )
        pc_html = _render(
            template_text, {**blocks, "bg_image_url": pc_bg, "viewport": "pc"}
        )

        sp_path = out_dir / "fv_sp.html"
        pc_path = out_dir / "fv_pc.html"
        sp_path.write_text(sp_html, encoding="utf-8")
        pc_path.write_text(pc_html, encoding="utf-8")

    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"FV 合成に失敗しました: {e}\n")
        return 1
    except KeyError as e:
        # string.Template.substitute が未対応プレースホルダを検出した場合
        sys.stderr.write(
            f"テンプレートとコードのプレースホルダ不整合: {e}\n"
        )
        return 1
    except OSError as e:
        sys.stderr.write(f"ファイル入出力エラー: {e}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("中断されました\n")
        return 130

    sys.stdout.write(
        json.dumps({"sp": str(sp_path), "pc": str(pc_path)}, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

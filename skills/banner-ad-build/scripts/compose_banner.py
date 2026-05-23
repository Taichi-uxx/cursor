#!/usr/bin/env python3
"""compose_banner.py — BG 背景画像の上にバナーのコピー/CTA/ロゴ/数値を HTML/CSS で重ねる.

gen_bg.py が生成したテキスト無し背景BG画像 (square/horizontal/vertical) の
上に、日本語が正確に表示されるバナーのメインコピー・サブコピー・CTA・ロゴ・
数値訴求を HTML/CSS で重ね合わせ、指定された各バナーサイズごとに 1 つの
HTML を出力する。

レンダリング (スクリーンショット化) は呼び出し側のスキルが Playwright で
file:// 経由で行う。このスクリプトの責務は HTML 生成までとする。

------------------------------------------------------------------------------
サイズ → アスペクト対応 (どの背景を使うか)
------------------------------------------------------------------------------
各 --sizes トークン (例 1080x1080) の縦横比からアスペクトを決定し、
対応する背景を選ぶ:
  - 比 ~1:1〜4:5 (やや縦長まで)      -> square
  - 比 横長 (1.2:1 以上)             -> horizontal
  - 比 縦長 (0.7:1 以下)             -> vertical
該当アスペクトの背景が未指定なら square をフォールバックし、stderr に
1 行警告を出す (秘匿情報なし)。square も無ければエラー。

------------------------------------------------------------------------------
copy JSON スキーマ
------------------------------------------------------------------------------
{
  "eyebrow":      "(任意 小ラベル)",
  "main":         "<メインコピー>",          # 必須
  "sub":          "<サブコピー>",            # 必須
  "cta":          "<CTAラベル>",             # 必須
  "number":       "(任意 数値訴求の主役 例 98%)",   # --type number のとき必須
  "number_label": "(任意 数値の説明 例 買取成立率)",
  "logo_text":    "(任意)",
  "theme": {                                 # 省略時は妥当なデフォルト
    "text_color": "#ffffff",
    "accent":     "#ff5a2b",
    "overlay":    "rgba(0,0,0,0.4)",
    "align":      "left" | "center",
    "position":   "top" | "center" | "bottom"
  }
}

依存は標準ライブラリのみ (string.Template)。jinja 等の外部依存は使わない。
ネットワークアクセスなし。フォントは system フォントのみ。
正常時、標準出力には JSON 1 行のみ:
  {"banners":[{"size":"1080x1080","type":"copy-strong","html":"<abs>"},...]}
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from string import Template

# テンプレートの位置 (scripts/ から見て ../templates/banner_template.html)
_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / ".." / "templates" / "banner_template.html"
).resolve()

# banner_template.html と厳密一致させるプレースホルダ集合 (整合性検証に使用)
_REQUIRED_PLACEHOLDERS = {
    "bg_image_url",
    "eyebrow_html",
    "main_html",
    "sub_html",
    "cta_label",
    "number_html",
    "logo_html",
    "text_color",
    "accent_color",
    "overlay_color",
    "align",
    "position",
    "viewport",
    "type_class",
}

# theme デフォルト
_DEFAULT_THEME = {
    "text_color": "#ffffff",
    "accent": "#ff5a2b",
    "overlay": "rgba(0,0,0,0.4)",
    "align": "left",
    "position": "bottom",
}

# --type -> テンプレ側 $type_class の CSS クラス
_TYPE_CLASS = {
    "copy-strong": "t-copy",
    "visual-strong": "t-visual",
    "number": "t-number",
}

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_COLOR_FN_RE = re.compile(r"^(?:rgb|rgba|hsl|hsla)\([0-9.,\s%/-]+\)$", re.IGNORECASE)
_SIZE_RE = re.compile(r"^\s*(\d{2,5})\s*[xX]\s*(\d{2,5})\s*$")


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


def _file_url(path_str: str, label: str) -> str:
    """ローカル画像パスを file:// 絶対 URL に変換 (存在検証込み)。"""
    p = Path(path_str).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"{label} の画像が見つかりません: {p}")
    # POSIX 絶対パスを file:// へ。空白等は URL エンコード。
    from urllib.parse import quote

    return "file://" + quote(str(p))


def _load_copy(spec: str) -> dict:
    """--copy 引数を解釈。ファイルパスなら読み込み、それ以外は inline JSON。"""
    candidate = Path(spec).expanduser()
    raw: str
    try:
        is_file = candidate.is_file()
    except OSError:
        # inline JSON が長大でパス扱いできない場合 (ENAMETOOLONG 等)
        is_file = False
    if is_file:
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


def _parse_sizes(spec: str) -> list[tuple[str, int, int]]:
    """--sizes (カンマ区切り <W>x<H>) を解釈。順序保持・重複除去。"""
    tokens = [t.strip() for t in (spec or "").split(",") if t.strip()]
    if not tokens:
        raise ValueError("--sizes が空です。例: 1080x1080,1200x628")
    out: list[tuple[str, int, int]] = []
    seen: set[str] = set()
    for t in tokens:
        m = _SIZE_RE.match(t)
        if not m:
            raise ValueError(
                f"--sizes の指定が不正です: '{t}' (<幅>x<高さ> 形式で指定)"
            )
        w, h = int(m.group(1)), int(m.group(2))
        if w <= 0 or h <= 0:
            raise ValueError(f"--sizes の寸法が不正です: '{t}'")
        canon = f"{w}x{h}"
        if canon in seen:
            continue
        seen.add(canon)
        out.append((canon, w, h))
    return out


def _aspect_for(w: int, h: int) -> str:
    """寸法比から背景アスペクト (square/horizontal/vertical) を決定。

    比 r = w / h:
      - r >= 1.2          -> horizontal (例 1200x628=1.91, 1280x720=1.78,
                              728x90=8.09, 970x250=3.88)
      - r <= 0.7          -> vertical   (例 1080x1920=0.56, 9:16=0.56)
      - それ以外 (~1:1〜4:5) -> square    (例 1080x1080=1.0, 1080x1350=0.8)
    """
    r = w / h
    if r >= 1.2:
        return "horizontal"
    if r <= 0.7:
        return "vertical"
    return "square"


def _build_blocks(copy: dict, banner_type: str) -> dict[str, str]:
    """copy dict から各プレースホルダ値を構築 (検証 + エスケープ済み)。"""
    main = copy.get("main")
    sub = copy.get("sub")
    cta = copy.get("cta")
    missing = [
        k
        for k, v in (("main", main), ("sub", sub), ("cta", cta))
        if not (isinstance(v, str) and v.strip())
    ]
    if missing:
        raise ValueError(f"copy JSON に必須項目が不足/空です: {', '.join(missing)}")

    number = copy.get("number")
    number_ok = isinstance(number, str) and number.strip()
    if banner_type == "number" and not number_ok:
        raise ValueError(
            "--type number では copy JSON の 'number' が必須です "
            "(数値訴求の主役。例 \"98%\")"
        )
    number_label = copy.get("number_label")

    theme = copy.get("theme") or {}
    if not isinstance(theme, dict):
        theme = {}

    text_color = _safe_color(theme.get("text_color"), _DEFAULT_THEME["text_color"])
    accent = _safe_color(theme.get("accent"), _DEFAULT_THEME["accent"])
    overlay = _safe_color(theme.get("overlay"), _DEFAULT_THEME["overlay"])

    align = theme.get("align")
    align = align if align in ("left", "center") else _DEFAULT_THEME["align"]
    position = theme.get("position")
    position = (
        position
        if position in ("top", "center", "bottom")
        else _DEFAULT_THEME["position"]
    )

    eyebrow = copy.get("eyebrow")
    eyebrow_html = (
        f'<span class="bn__eyebrow">{_esc(eyebrow)}</span>'
        if isinstance(eyebrow, str) and eyebrow.strip()
        else ""
    )
    logo_text = copy.get("logo_text")
    logo_html = (
        f'<div class="bn__logo">{_esc(logo_text)}</div>'
        if isinstance(logo_text, str) and logo_text.strip()
        else ""
    )

    if number_ok:
        label_html = (
            f'<span class="bn__number-label">{_esc(number_label)}</span>'
            if isinstance(number_label, str) and number_label.strip()
            else ""
        )
        number_html = (
            '<div class="bn__number">'
            f'<span class="bn__number-value">{_esc(number)}</span>'
            f"{label_html}"
            "</div>"
        )
    else:
        number_html = ""

    return {
        "eyebrow_html": eyebrow_html,
        "main_html": _esc(main),
        "sub_html": _esc(sub),
        "cta_label": _esc(cta),
        "number_html": number_html,
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
        prog="compose_banner.py",
        description="BG 背景に各サイズのバナーコピー/CTA を重ねた HTML を生成。",
    )
    p.add_argument("--bg-square", default="", help="正方形系 背景画像パス (空可)")
    p.add_argument("--bg-horizontal", default="", help="横長系 背景画像パス (空可)")
    p.add_argument("--bg-vertical", default="", help="縦長系 背景画像パス (空可)")
    p.add_argument(
        "--sizes",
        required=True,
        help='バナーサイズ (カンマ区切り <W>x<H>)。例 "1080x1080,1200x628,1080x1920,300x250"',
    )
    p.add_argument(
        "--type",
        required=True,
        choices=["copy-strong", "visual-strong", "number"],
        help="強調タイプ (copy-strong=コピー大 / visual-strong=余白大 / number=数値主役)",
    )
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
            sys.stderr.write(f"テンプレートが見つかりません: {_TEMPLATE_PATH}\n")
            return 1
        template_text = _TEMPLATE_PATH.read_text(encoding="utf-8")
        _verify_template(template_text)

        banner_type = args.type
        type_class = _TYPE_CLASS[banner_type]

        copy = _load_copy(args.copy)
        blocks = _build_blocks(copy, banner_type)

        sizes = _parse_sizes(args.sizes)

        # 背景を file:// URL 化 (指定されたものだけ・存在検証込み)。
        bg_urls: dict[str, str] = {}
        if str(args.bg_square).strip():
            bg_urls["square"] = _file_url(args.bg_square, "--bg-square")
        if str(args.bg_horizontal).strip():
            bg_urls["horizontal"] = _file_url(args.bg_horizontal, "--bg-horizontal")
        if str(args.bg_vertical).strip():
            bg_urls["vertical"] = _file_url(args.bg_vertical, "--bg-vertical")
        if not bg_urls:
            raise ValueError(
                "背景画像が 1 つも指定されていません "
                "(--bg-square / --bg-horizontal / --bg-vertical のいずれか必須)"
            )

        out_dir = Path(args.out_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        banners: list[dict[str, str]] = []
        for canon, w, h in sizes:
            aspect = _aspect_for(w, h)
            chosen = aspect
            if aspect not in bg_urls:
                # 該当アスペクト未指定 -> square にフォールバック。
                if "square" in bg_urls:
                    sys.stderr.write(
                        f"[warn] {canon}: {aspect} 背景が未指定のため "
                        f"square 背景にフォールバックします\n"
                    )
                    chosen = "square"
                elif bg_urls:
                    # square も無い場合は手元にある最初の背景で代替。
                    chosen = next(iter(bg_urls))
                    sys.stderr.write(
                        f"[warn] {canon}: {aspect}/square 背景が未指定のため "
                        f"{chosen} 背景にフォールバックします\n"
                    )
                else:
                    raise ValueError(
                        f"{canon}: 使用できる背景画像がありません ({aspect} 要求)"
                    )

            viewport = f"{w}px x {h}px"
            html_text = _render(
                template_text,
                {
                    **blocks,
                    "bg_image_url": bg_urls[chosen],
                    "viewport": viewport,
                    "type_class": type_class,
                },
            )
            dest = out_dir / f"banner_{banner_type}_{canon}.html"
            dest.write_text(html_text, encoding="utf-8")
            banners.append(
                {"size": canon, "type": banner_type, "html": str(dest)}
            )

    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"バナー合成に失敗しました: {e}\n")
        return 1
    except KeyError as e:
        # string.Template.substitute が未対応プレースホルダを検出した場合
        sys.stderr.write(f"テンプレートとコードのプレースホルダ不整合: {e}\n")
        return 1
    except OSError as e:
        sys.stderr.write(f"ファイル入出力エラー: {e}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("中断されました\n")
        return 130

    sys.stdout.write(
        json.dumps({"banners": banners}, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

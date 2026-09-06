#!/usr/bin/env python3
"""競合ウォッチ週報のHTMLレポート生成器。

競合ウォッチスキルが集約したシグナル（JSON）を受け取り、Meta広告バナー画像込みの
リッチなHTMLレポートを生成する。ローカルファイルとして保存し、Chatworkメッセージ
本文にはこのファイルのパスをリンクとして貼り付ける想定。

入力（stdin）: 集約シグナルJSON
{
  "client_display": "株式会社TOEZ（ベビーパーク）",
  "period_from": "2026-08-23",
  "period_to": "2026-09-06",
  "meta_ads": { "<競合名>": [ {..creative..} ] },
  "listings": [ {..listing..} ],
  "releases": [ {..release..} ],
  "so_what": ["示唆1", "示唆2", ...]
}

出力: /Users/apple/.cursor/work/AI活用/competitor-weekly/reports/<YYYY-MM-DD>/<client_dir>.html
     ローカルファイルパスを標準出力に返す（呼び出し元がChatworkメッセージに貼り付ける）

使い方:
  cat aggregated.json | python3 build_html_report.py --client-dir toez
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

REPORTS_ROOT = Path("/Users/apple/.cursor/work/AI活用/competitor-weekly/reports")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
      background: #f5f5f7;
      color: #1d1d1f;
      margin: 0;
      padding: 24px;
      line-height: 1.6;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    header {{
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 32px;
      border-radius: 16px;
      margin-bottom: 32px;
    }}
    header h1 {{ margin: 0 0 8px; font-size: 24px; }}
    header .meta {{ opacity: 0.9; font-size: 14px; }}
    header .totals {{
      display: flex; gap: 16px; margin-top: 20px;
    }}
    .totals .card {{
      background: rgba(255,255,255,0.15);
      padding: 12px 20px; border-radius: 8px;
      backdrop-filter: blur(10px);
    }}
    .totals .num {{ font-size: 28px; font-weight: bold; display: block; }}
    .totals .lbl {{ font-size: 12px; opacity: 0.85; }}
    section {{
      background: white;
      padding: 24px 28px;
      border-radius: 12px;
      margin-bottom: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    section h2 {{
      font-size: 20px; margin: 0 0 20px;
      padding-bottom: 12px; border-bottom: 2px solid #e5e5e7;
    }}
    .so-what {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
    .so-what h2 {{ border-color: #f59e0b; }}
    .so-what ul {{ margin: 0; padding-left: 20px; }}
    .so-what li {{ margin-bottom: 8px; }}
    .competitor-block {{ margin-bottom: 32px; }}
    .competitor-block h3 {{
      font-size: 16px; margin: 0 0 12px;
      color: #6e6e73;
    }}
    .ads-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}
    .ad-card {{
      border: 1px solid #e5e5e7;
      border-radius: 10px;
      overflow: hidden;
      background: #fafafa;
      transition: transform 0.15s, box-shadow 0.15s;
    }}
    .ad-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    .ad-card .img-wrap {{
      background: #000;
      aspect-ratio: 1;
      display: flex; align-items: center; justify-content: center;
      overflow: hidden;
    }}
    .ad-card img {{
      width: 100%; height: 100%;
      object-fit: cover;
      display: block;
    }}
    .ad-card .no-img {{
      color: #999; font-size: 40px;
    }}
    .ad-card .body {{ padding: 12px 14px; }}
    .ad-card .badge {{
      display: inline-block;
      background: #007aff; color: white;
      font-size: 10px; padding: 2px 8px;
      border-radius: 10px; margin-right: 4px;
    }}
    .ad-card .badge-vid {{ background: #ff3b30; }}
    .ad-card .badge-car {{ background: #af52de; }}
    .ad-card .badge-cnt {{ background: #34c759; }}
    .ad-card .date {{ font-size: 11px; color: #86868b; margin-bottom: 6px; }}
    .ad-card .headline {{
      font-size: 13px; font-weight: 600; margin: 4px 0;
      line-height: 1.4;
    }}
    .ad-card .pitch {{
      font-size: 12px; color: #48484a; margin: 4px 0;
      line-height: 1.4;
    }}
    .ad-card .links {{
      display: flex; gap: 8px; margin-top: 8px;
      font-size: 11px;
    }}
    .ad-card .links a {{ color: #007aff; text-decoration: none; }}
    .ad-card .links a:hover {{ text-decoration: underline; }}
    .list-item {{
      padding: 10px 0; border-bottom: 1px solid #f0f0f0;
    }}
    .list-item:last-child {{ border: none; }}
    .list-item .lead {{ font-size: 14px; font-weight: 500; }}
    .list-item .sub {{ font-size: 12px; color: #6e6e73; margin-top: 3px; }}
    .list-item .warn {{ color: #ff3b30; font-weight: 600; }}
    a.plain {{ color: #007aff; text-decoration: none; }}
    a.plain:hover {{ text-decoration: underline; }}
    .empty {{ color: #86868b; font-style: italic; padding: 12px 0; }}
    footer {{
      text-align: center; color: #86868b; font-size: 11px;
      margin-top: 40px; padding: 20px;
    }}
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>🕵️ 競合ウォッチ週報 — {client}</h1>
    <div class="meta">対象期間: {period_from} 〜 {period_to} ／ 生成: {generated_at}</div>
    <div class="totals">
      <div class="card"><span class="num">{n_meta}</span><span class="lbl">Meta広告</span></div>
      <div class="card"><span class="num">{n_listing}</span><span class="lbl">リスティングLP</span></div>
      <div class="card"><span class="num">{n_release}</span><span class="lbl">リリース</span></div>
    </div>
  </header>

  <section class="so-what">
    <h2>📌 今週のSo What（AI観察）</h2>
    {so_what_html}
  </section>

  <section>
    <h2>▼ Meta広告クリエイティブ</h2>
    {meta_html}
  </section>

  <section>
    <h2>▼ リスティング広告LP</h2>
    {listing_html}
  </section>

  <section>
    <h2>▼ プレスリリース／お知らせ</h2>
    {release_html}
  </section>

  <footer>
    Generated by competitor-weekly skill · {generated_at}
  </footer>
</div>
</body>
</html>
"""


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render_meta(meta_ads: dict) -> str:
    parts: list[str] = []
    has_any = False
    for comp, creatives in meta_ads.items():
        if not creatives:
            continue
        has_any = True
        parts.append(f'<div class="competitor-block">')
        parts.append(f'<h3>■ {esc(comp)} ({len(creatives)}件)</h3>')
        parts.append('<div class="ads-grid">')
        for c in creatives:
            img = ""
            imgs = c.get("image_urls") or []
            if imgs:
                img = f'<img src="{esc(imgs[0])}" alt="" loading="lazy">'
            else:
                img = '<span class="no-img">🖼️</span>'

            fmt = c.get("format", "image")
            badge_class = "badge-vid" if fmt == "video" else ("badge-car" if fmt == "carousel" else "")
            badges = f'<span class="badge {badge_class}">{esc(fmt)}</span>'
            cc = c.get("collation_count", 1)
            if cc > 1:
                badges += f'<span class="badge badge-cnt">{cc}バリエ</span>'

            pitch = esc(c.get("pitch") or c.get("body_snippet","")[:120])
            link_line = ""
            links = []
            links.append(f'<a href="{esc(c["url"])}" target="_blank" rel="noopener">Meta広告ライブラリ↗</a>')
            if c.get("link_url"):
                cta = f' ({esc(c.get("cta_text","LP"))})' if c.get("cta_text") else ""
                links.append(f'<a href="{esc(c["link_url"])}" target="_blank" rel="noopener">遷移先LP↗{cta}</a>')
            link_line = '<div class="links">' + '｜'.join(links) + '</div>'

            parts.append(f'''
              <div class="ad-card">
                <div class="img-wrap">{img}</div>
                <div class="body">
                  {badges}
                  <div class="date">{esc(c.get("started_on",""))} · {esc(c.get("page_name",""))}</div>
                  <div class="headline">{esc(c.get("headline",""))}</div>
                  <div class="pitch">{pitch}</div>
                  {link_line}
                </div>
              </div>''')
        parts.append('</div>')
        parts.append('</div>')

    if not has_any:
        return '<div class="empty">今週は新規Meta広告なし</div>'
    return "\n".join(parts)


def render_listing(listings: list) -> str:
    if not listings:
        return '<div class="empty">今週は新規リスティングLPなし</div>'
    parts: list[str] = []
    # 自社/他社で分ける
    own = [l for l in listings if l.get("own")]
    alt = [l for l in listings if not l.get("own")]
    if own:
        parts.append(f'<div class="competitor-block"><h3>■ 競合本体のLP ({len(own)}件)</h3>')
        for l in own:
            parts.append(f'''<div class="list-item">
              <div class="lead">[kw: {esc(l.get("keyword",""))}] {esc(l.get("title",""))}</div>
              <div class="sub">{esc(l.get("summary_1line") or l.get("summary",""))}</div>
              <div class="sub"><a class="plain" href="{esc(l.get("canonical_url",""))}" target="_blank">{esc(l.get("canonical_url",""))}↗</a></div>
            </div>''')
        parts.append('</div>')
    if alt:
        parts.append(f'<div class="competitor-block"><h3>■ 他競合／類似業種の横流入LP ({len(alt)}件・<span class="warn">キーワード奪取要警戒</span>)</h3>')
        for l in alt:
            parts.append(f'''<div class="list-item">
              <div class="lead">[kw: {esc(l.get("keyword",""))}] {esc(l.get("title",""))} <span class="sub">({esc(l.get("display_domain") or l.get("domain",""))})</span></div>
              <div class="sub">{esc(l.get("summary_1line") or l.get("summary",""))}</div>
              <div class="sub"><a class="plain" href="{esc(l.get("canonical_url",""))}" target="_blank">{esc(l.get("canonical_url",""))}↗</a></div>
            </div>''')
        parts.append('</div>')
    return "\n".join(parts)


def render_release(releases: list) -> str:
    if not releases:
        return '<div class="empty">今週は新規リリースなし</div>'
    by_c: dict[str, list] = {}
    for r in releases:
        by_c.setdefault(r.get("competitor", "不明"), []).append(r)
    parts: list[str] = []
    for comp, items in by_c.items():
        parts.append(f'<div class="competitor-block"><h3>■ {esc(comp)} ({len(items)}件)</h3>')
        for r in items:
            parts.append(f'''<div class="list-item">
              <div class="lead">[{esc(r.get("posted_at",""))}] {esc(r.get("title",""))}</div>
              <div class="sub">{esc(r.get("summary_1line",""))}</div>
              <div class="sub"><a class="plain" href="{esc(r.get("url",""))}" target="_blank">{esc(r.get("url",""))}↗</a></div>
            </div>''')
        parts.append('</div>')
    return "\n".join(parts)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--client-dir", required=True, help="案件フォルダ名（例: toez）ファイル名に使う")
    p.add_argument("--out-root", default=str(REPORTS_ROOT), help="出力ルート")
    args = p.parse_args()

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"ERROR: stdin JSON parse失敗: {e}", file=sys.stderr)
        return 1

    period_from = data.get("period_from", "")
    period_to = data.get("period_to", datetime.now().date().isoformat())
    client = data.get("client_display", args.client_dir)
    meta_ads = data.get("meta_ads", {})
    listings = data.get("listings", [])
    releases = data.get("releases", [])
    so_what = data.get("so_what", [])

    n_meta = sum(len(v) for v in meta_ads.values())
    n_listing = len(listings)
    n_release = len(releases)

    so_what_html = "<ul>" + "".join(f"<li>{esc(s)}</li>" for s in so_what) + "</ul>" if so_what else '<div class="empty">今週は特筆すべき動きなし</div>'

    html_str = HTML_TEMPLATE.format(
        title=f"競合ウォッチ週報 {period_to} - {client}",
        client=esc(client),
        period_from=esc(period_from),
        period_to=esc(period_to),
        generated_at=datetime.now().isoformat(timespec="seconds"),
        n_meta=n_meta,
        n_listing=n_listing,
        n_release=n_release,
        so_what_html=so_what_html,
        meta_html=render_meta(meta_ads),
        listing_html=render_listing(listings),
        release_html=render_release(releases),
    )

    out_dir = Path(args.out_root) / period_to
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.client_dir}.html"
    out_path.write_text(html_str, encoding="utf-8")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
WebFetchが403で弾かれるサイト向けに、ブラウザUA付き requests で取得するヘルパー。
Referer を https://www.google.com/ に偽装し、日本語 Accept-Language を送る。

使い方:
  # 生HTMLをstdoutへ
  python3 fetch_ua.py "https://anagrams.jp/blog/listing_new/"

  # <a>タグのhref＋アンカーテキストだけ抽出（記事一覧ページ向け）
  python3 fetch_ua.py "https://anagrams.jp/blog/listing_new/" --links

  # 本文テキスト抽出（記事詳細ページ向け）
  python3 fetch_ua.py "https://anagrams.jp/blog/xxxxxx/" --text

  # UA/Referer を上書き
  python3 fetch_ua.py URL --ua "..." --referer "..."

  # 出力を <N> 文字で打ち切る（stdoutに落とすトークン節約）
  python3 fetch_ua.py URL --max-chars 8000
"""

from __future__ import annotations

import argparse
import re
import sys

try:
    import requests
except ImportError:
    print("ERROR: requests が必要", file=sys.stderr)
    sys.exit(1)


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
DEFAULT_REFERER = "https://www.google.com/"


def fetch(url: str, ua: str, referer: str, timeout: int) -> str:
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": referer,
    }
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    return r.text


def extract_links(html: str, base_url: str) -> str:
    """<a href>＋アンカーテキストを1行1エントリで抽出"""
    from urllib.parse import urljoin

    out: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        href = m.group(1).strip()
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        text = re.sub(r"\s+", " ", text)
        if not text or len(text) < 3:
            continue
        full = urljoin(base_url, href)
        if full.startswith(("javascript:", "mailto:", "#")):
            continue
        key = f"{text}|{full}"
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{text}\t{full}")
    return "\n".join(out)


def extract_text(html: str) -> str:
    """簡易的な本文抽出。script/styleを除去して可視テキスト化"""
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<!--[\s\S]*?-->", " ", html)
    # 段落・見出し等の区切りに改行を残す
    html = re.sub(r"</(p|div|li|h[1-6]|br|tr|section|article)>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", html)
    # HTMLエンティティ簡易デコード（頻出のみ）
    entities = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'"}
    for k, v in entities.items():
        text = text.replace(k, v)
    # 空白圧縮
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--links", action="store_true", help="<a href>＋アンカーテキストだけ抽出")
    p.add_argument("--text", action="store_true", help="本文可視テキスト抽出")
    p.add_argument("--ua", default=DEFAULT_UA)
    p.add_argument("--referer", default=DEFAULT_REFERER)
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--max-chars", type=int, default=0, help="出力の最大文字数(0=無制限)")
    args = p.parse_args()

    try:
        html = fetch(args.url, args.ua, args.referer, args.timeout)
    except requests.HTTPError as e:
        print(f"HTTP ERROR: {e.response.status_code} {e.response.reason}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"REQUEST ERROR: {e}", file=sys.stderr)
        return 1

    if args.links:
        out = extract_links(html, args.url)
    elif args.text:
        out = extract_text(html)
    else:
        out = html

    if args.max_chars > 0 and len(out) > args.max_chars:
        out = out[: args.max_chars] + f"\n[... truncated {len(out) - args.max_chars} chars ...]"
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

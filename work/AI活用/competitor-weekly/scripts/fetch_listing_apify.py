#!/usr/bin/env python3
"""Apify Google Search Scraper 経由でリスティング広告のLPを取得する。

Actor: apify/google-search-scraper（公式・$1.80/1000 SERPs → 週20SERP = 月$0.15）

Actor返却の `paidResults` 配列（オーガニックと構造分離済み）から
広告カードのみを取り出し、canonical化して返す。

環境変数:
  APIFY_TOKEN : Apify APIトークン（必須）

使い方:
  # 単一キーワード
  python3 fetch_listing_apify.py --query "七田式教室" --country jp --json

  # 複数キーワード一括（stdin JSON）
  echo '{
    "queries": [
      {"competitor":"七田式教室","keyword":"七田式"},
      {"competitor":"EQWEL","keyword":"EQWEL"},
      {"competitor":"_BIG","keyword":"幼児教室"}
    ],
    "exclude_domains": ["babypark.jp"],
    "exclude_keywords": ["ベビーパーク","TOEZ","BabyPark"]
  }' | python3 fetch_listing_apify.py --batch --country jp --json

出力JSON:
  {
    "listings": [
      {
        "competitor": "七田式教室",
        "keyword": "七田式",
        "canonical_url": "https://...",
        "raw_url": "<元URL>",
        "display_domain": "shichida.co.jp",
        "title": "<LPタイトル>",
        "summary_1line": "<説明文>",
        "ad_position": 1
      }
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
try:
    import requests
except ImportError:
    print("ERROR: requests / python-dotenv が必要", file=sys.stderr)
    sys.exit(1)


ACTOR_ID = "apify~google-search-scraper"
APIFY_API_BASE = "https://api.apify.com/v2"
SYNC_ENDPOINT = f"{APIFY_API_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items"

ENV_CANDIDATES = [
    Path("/Users/apple/.cursor/設定まわり/taichi-tamura/.env"),
    Path.home() / ".cursor" / ".env",
]

DEFAULT_HTTP_TIMEOUT = 360  # 5min（Apify run-syncの上限）

# URLから除去する変動パラメータ
TRACKING_PARAMS = {
    "utm_source","utm_medium","utm_campaign","utm_content","utm_term",
    "gclid","gbraid","wbraid","fbclid","dclid","msclkid",
    "gad_source","gad_campaignid","dmai","argument","yclid",
}


def load_env() -> None:
    if not load_dotenv:
        return
    for p in ENV_CANDIDATES:
        if p.exists():
            load_dotenv(p)
            return


def canonicalize_url(u: str) -> str:
    """トラッキング系変動パラメータを除去したcanonical URL。"""
    if not u:
        return u
    try:
        parsed = urlparse(u)
        q = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if k not in TRACKING_PARAMS]
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params,
                          urlencode(q), ""))
    except Exception:  # noqa: BLE001
        return u


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def call_apify(queries: list[str], country: str, token: str,
               results_per_page: int = 10) -> list[dict]:
    """Actorを1回叩いて、複数queryの結果を返す。
    focusOnPaidAds=true + RESIDENTIAL proxy(JP) で広告取得を確実にする
    （デフォルト設定だとGoogleのbot検知で paidResults がほぼ0件になる問題を回避）。
    """
    payload = {
        "queries": "\n".join(queries),
        "countryCode": country,
        "languageCode": "ja" if country == "jp" else "en",
        "maxPagesPerQuery": 1,
        "resultsPerPage": results_per_page,
        "mobileResults": False,
        "saveHtml": False,
        "includeUnfilteredResults": False,
        "focusOnPaidAds": True,  # 広告取得優先モード（ad-specialized proxy + リトライ）
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": country.upper(),
        },
    }
    resp = requests.post(
        SYNC_ENDPOINT,
        params={"token": token, "clean": "true", "format": "json"},
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=DEFAULT_HTTP_TIMEOUT,
    )
    if resp.status_code == 402:
        raise RuntimeError("Apify クレジット不足（402）")
    if resp.status_code == 401:
        raise RuntimeError("APIFY_TOKEN が無効（401）")
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response: {str(data)[:300]}")
    if data and isinstance(data[0], dict) and set(data[0].keys()) == {"error"}:
        raise RuntimeError(f"Actor error: {data[0]['error']}")
    return data


def process_paid(paid_results: list, competitor_kw_map: dict[str, str],
                 exclude_domains: set[str], exclude_kw: list[str]) -> list[dict]:
    """paidResults を canonical化してcompetitor/キーワードに紐付ける。
    Google SERPの `url` フィールドは aclk 経由の追跡URL。実際の遷移先ドメインは
    `displayedUrl` に含まれる（例: "https://www.flow.or.jp"）。
    """
    out: list[dict] = []
    seen: set[tuple] = set()  # (advertiser_domain, keyword) dedupe
    for item in paid_results or []:
        raw_url = item.get("url", "")
        displayed = (item.get("displayedUrl") or "").strip()
        # displayedUrlは "example.com › path" 形式のこともある
        display_root = displayed.split("›")[0].strip()
        # advertiser URL 推定: displayedUrl優先、なければraw_urlから
        advertiser_url = display_root or raw_url
        canonical = canonicalize_url(advertiser_url)
        domain = extract_domain(canonical) if canonical.startswith("http") else display_root
        if not canonical:
            continue
        # 除外（advertiser domainベース）
        if any(d in domain for d in exclude_domains):
            continue
        title = item.get("title", "")
        desc = item.get("description", "")
        blob = (title + " " + desc + " " + domain).lower()
        if any(x.lower() in blob for x in exclude_kw):
            continue
        keyword = item.get("_keyword", "")
        competitor = competitor_kw_map.get(keyword, "_unknown")
        key = (domain, keyword)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "competitor": competitor,
            "keyword": keyword,
            "canonical_url": canonical,
            "raw_url": raw_url,
            "display_domain": domain,
            "title": title.strip(),
            "summary_1line": desc.strip()[:200],
            "ad_position": item.get("adPosition") or item.get("position", 0),
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", help="単一クエリ")
    p.add_argument("--competitor", help="単一クエリ時のcompetitor名")
    p.add_argument("--batch", action="store_true", help="stdinからJSON入力（queries配列）")
    p.add_argument("--country", default="jp")
    p.add_argument("--results-per-page", type=int, default=10)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    load_env()
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("ERROR: APIFY_TOKEN が未設定", file=sys.stderr)
        return 1

    if args.batch:
        try:
            spec = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(f"ERROR: stdin JSON parse失敗: {e}", file=sys.stderr)
            return 1
        queries_spec = spec.get("queries", [])
        exclude_domains = set(spec.get("exclude_domains", []))
        exclude_kw = spec.get("exclude_keywords", [])
    else:
        if not args.query:
            print("ERROR: --query か --batch のどちらかが必要", file=sys.stderr)
            return 1
        queries_spec = [{"competitor": args.competitor or "_manual", "keyword": args.query}]
        exclude_domains = set()
        exclude_kw = []

    # queryごとにActor呼ぶ（1runで複数queryもいけるがsearchQueryを見て紐付けるのが厄介）
    # → 1queryずつsync呼びで結果を積む（15-20queryなら十分に収まる）
    all_listings: list[dict] = []
    for q in queries_spec:
        kw = q.get("keyword", "")
        comp = q.get("competitor", "_unknown")
        if not kw:
            continue
        try:
            raw = call_apify([kw], args.country, token, args.results_per_page)
        except Exception as e:  # noqa: BLE001
            print(f"WARN: {kw}: {e}", file=sys.stderr)
            continue
        for page in raw:
            paid = page.get("paidResults") or []
            # 各広告に元キーワードを付与
            for item in paid:
                item["_keyword"] = kw
            listings = process_paid(paid, {kw: comp}, exclude_domains, exclude_kw)
            all_listings.extend(listings)
        time.sleep(0.5)  # Actor rate limit配慮

    out = {"listings": all_listings}
    if args.json:
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        for l in all_listings:
            print(f"[{l['competitor']} / kw:{l['keyword']}] {l['title']}")
            print(f"  {l['canonical_url']} ({l['display_domain']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

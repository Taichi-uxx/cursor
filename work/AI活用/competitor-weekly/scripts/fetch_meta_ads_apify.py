#!/usr/bin/env python3
"""Apify経由でMeta広告ライブラリからactive広告を取得する。

Actor: curious_coder/facebook-ads-library-scraper
  - 料金: $0.75 / 1,000 ads（週次70広告なら月$0.23）
  - Apify Console → Settings → Integrations で API Token 発行

環境変数（`/Users/apple/.cursor/設定まわり/taichi-tamura/.env` 想定）:
  APIFY_TOKEN : Apify APIトークン（必須）

使い方:

  # 単一クエリ
  python3 fetch_meta_ads_apify.py --query "七田式教室" --country JP --days 14 --limit 10 --json

  # 複数競合を一括（stdin にJSON）
  echo '[
    {"competitor":"七田式教室","search_terms":["七田式教室","しちだ・教育研究所"]},
    {"competitor":"EQWEL","search_terms":["EQWEL","イクウェル"]},
    {"competitor":"Baby Kumon","search_terms":["Baby Kumon","ベビーくもん"]}
  ]' | python3 fetch_meta_ads_apify.py --batch --country JP --days 14 --limit 10 --json

  # smoke test（1件だけ叩いて疎通確認）
  python3 fetch_meta_ads_apify.py --query "七田式教室" --limit 3 --json

出力JSON:
  {
    "results": [
      {
        "competitor": "七田式教室",
        "query": "七田式教室",
        "creatives": [
          {
            "ad_archive_id": "...",
            "url": "https://www.facebook.com/ads/library/?id=...",
            "started_on": "YYYY-MM-DD",
            "format": "image|video|carousel|unknown",
            "page_name": "...",
            "headline": "...",
            "body_snippet": "..."
          }
        ]
      }
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import requests
except ImportError:
    print("ERROR: requests / python-dotenv が必要です", file=sys.stderr)
    sys.exit(1)


ACTOR_ID = "curious_coder~facebook-ads-library-scraper"
APIFY_API_BASE = "https://api.apify.com/v2"
# 同期実行エンドポイント（Apify側でruntimeを待ち、datasetをそのまま返す）
SYNC_ENDPOINT = f"{APIFY_API_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items"

ENV_CANDIDATES = [
    Path("/Users/apple/.cursor/設定まわり/taichi-tamura/.env"),
    Path.home() / ".cursor" / ".env",
]

# Apify Actorのrun-syncはデフォルト300秒。1広告主あたり100件未満なら十分。
DEFAULT_HTTP_TIMEOUT = 360


def load_env() -> None:
    if not load_dotenv:
        return
    for p in ENV_CANDIDATES:
        if p.exists():
            load_dotenv(p)
            return


def build_search_url(query: str, country: str) -> str:
    """Meta広告ライブラリのSearch URLを組む（Apifyに渡す入力）。"""
    q = quote_plus(query)
    return (
        "https://www.facebook.com/ads/library/"
        f"?active_status=active&ad_type=all&country={country}"
        f"&q={q}&search_type=keyword_unordered&media_type=all"
    )


def normalize_format(display_format: str) -> str:
    if not display_format:
        return "unknown"
    f = display_format.upper()
    if f == "IMAGE":
        return "image"
    if f == "VIDEO":
        return "video"
    if f in ("DCO", "CAROUSEL", "MULTI_IMAGES"):
        return "carousel"
    return "unknown"


def extract_headline_and_body(ad: dict) -> tuple[str, str]:
    """Actorレスポンスから headline / body を取り出す（複数バリエ対応）。"""
    snap = ad.get("snapshot") or {}
    # 単一クリエイティブ
    title = (snap.get("title") or "").strip()
    body_obj = snap.get("body") or {}
    body = ""
    if isinstance(body_obj, dict):
        body = (body_obj.get("text") or "").strip()
    elif isinstance(body_obj, str):
        body = body_obj.strip()
    # カルーセルはcards[0]から
    if not title or not body:
        cards = snap.get("cards") or []
        if cards and isinstance(cards[0], dict):
            title = title or (cards[0].get("title") or "").strip()
            body = body or (cards[0].get("body") or "").strip()
    return title, body[:400]


def parse_start_date(ad: dict) -> str | None:
    """started_on を YYYY-MM-DD で返す。読み取れなければ None（推測禁止）。"""
    # 優先: start_date_string（YYYY-MM-DD形式が多い）
    s = ad.get("start_date_string")
    if s:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass
    # 次: start_date（UNIX秒 or ISO文字列）
    sd = ad.get("start_date")
    if isinstance(sd, (int, float)):
        try:
            return datetime.fromtimestamp(int(sd), tz=timezone.utc).date().isoformat()
        except (ValueError, OSError):
            return None
    if isinstance(sd, str):
        try:
            return datetime.fromisoformat(sd.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return None
    return None


def call_apify(query: str, country: str, limit: int, token: str) -> list[dict]:
    """Apify Actor を run-sync で叩いて dataset items を返す。"""
    # Actor制約: count は最低10必要。--limit=3 等でも API は10で呼び、クライアント側で後段トリム
    api_count = max(limit, 10)
    payload = {
        "urls": [{"url": build_search_url(query, country)}],
        "count": api_count,
        "limitPerSource": api_count,
        "scrapeAdDetails": False,
        "proxy": {"useApifyProxy": True},
    }
    resp = requests.post(
        SYNC_ENDPOINT,
        params={"token": token, "clean": "true", "format": "json"},
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=DEFAULT_HTTP_TIMEOUT,
    )
    if resp.status_code == 402:
        raise RuntimeError("Apify クレジット不足（402 Payment Required）")
    if resp.status_code == 401:
        raise RuntimeError("APIFY_TOKEN が無効（401 Unauthorized）")
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response type: {type(data).__name__}: {str(data)[:300]}")
    # Actor側の入力バリデーションエラーは [{error: "..."}] 形式で返る
    if data and isinstance(data[0], dict) and set(data[0].keys()) == {"error"}:
        raise RuntimeError(f"Apify Actor error: {data[0]['error']}")
    return data


def extract_media_urls(ad: dict) -> tuple[list[str], list[str]]:
    """画像URL・動画URL(またはthumb)のリストを取得。HTMLレポート埋め込み用。"""
    snap = ad.get("snapshot") or {}
    images: list[str] = []
    videos: list[str] = []
    # IMAGE
    for img in snap.get("images") or []:
        if not isinstance(img, dict):
            continue
        u = img.get("resized_image_url") or img.get("original_image_url")
        if u:
            images.append(u)
    # VIDEO
    for v in snap.get("videos") or []:
        if not isinstance(v, dict):
            continue
        thumb = v.get("video_preview_image_url")
        if thumb:
            images.append(thumb)  # 動画はサムネイルを画像扱いで並べる
        hd = v.get("video_hd_url") or v.get("video_sd_url")
        if hd:
            videos.append(hd)
    # CAROUSEL / DCO
    for card in snap.get("cards") or []:
        if not isinstance(card, dict):
            continue
        u = card.get("resized_image_url") or card.get("original_image_url") or card.get("video_preview_image_url")
        if u:
            images.append(u)
        v_hd = card.get("video_hd_url")
        if v_hd:
            videos.append(v_hd)
    return images, videos


def transform(ad: dict) -> dict | None:
    """Apify生データを競合ウォッチ標準フィールドに整形。started_on取れないカードはNone。"""
    aid = ad.get("ad_archive_id") or ad.get("adArchiveID") or ad.get("id")
    if not aid:
        return None
    started_on = parse_start_date(ad)
    if not started_on:
        return None  # 推測禁止、日付不明はスキップ
    snap = ad.get("snapshot") or {}
    headline, body = extract_headline_and_body(ad)
    collation_count = ad.get("collation_count") or 1
    images, videos = extract_media_urls(ad)
    return {
        "ad_archive_id": str(aid),
        "url": f"https://www.facebook.com/ads/library/?id={aid}",
        "started_on": started_on,
        "format": normalize_format(snap.get("display_format") or ""),
        "page_name": (ad.get("page_name") or snap.get("page_name") or "").strip(),
        "page_id": str(ad.get("page_id") or ""),
        "headline": headline,
        "body_snippet": body,
        "is_active": bool(ad.get("is_active", True)),
        "collation_count": int(collation_count) if isinstance(collation_count, (int, float)) else 1,
        "link_url": (snap.get("link_url") or "").strip(),
        "cta_text": (snap.get("cta_text") or "").strip(),
        "image_urls": images,
        "video_urls": videos,
    }


def run_one(query: str, country: str, days: int, limit: int, token: str) -> list[dict]:
    """1クエリぶん実行して過去daysに絞ったcreativesを返す。--limitでクライアント側トリム。"""
    raw = call_apify(query, country, limit, token)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    creatives: list[dict] = []
    seen: set[str] = set()
    for ad in raw:
        t = transform(ad)
        if not t:
            continue
        if t["ad_archive_id"] in seen:
            continue
        try:
            if datetime.strptime(t["started_on"], "%Y-%m-%d").date() < cutoff:
                continue
        except ValueError:
            continue
        seen.add(t["ad_archive_id"])
        creatives.append(t)
        if len(creatives) >= limit:
            break
    return creatives


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", help="単一クエリ（会社名など）")
    p.add_argument("--batch", action="store_true", help="stdinからJSON配列で複数競合を一括処理")
    p.add_argument("--country", default="JP")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--limit", type=int, default=10, help="1クエリあたり最大取得件数")
    p.add_argument("--json", action="store_true", help="JSON出力（デフォルトはpretty）")
    args = p.parse_args()

    load_env()
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("ERROR: APIFY_TOKEN 未設定（.env に APIFY_TOKEN=... を追加してください）", file=sys.stderr)
        return 1

    results: list[dict] = []

    if args.batch:
        try:
            targets = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(f"ERROR: stdin JSON parse失敗: {e}", file=sys.stderr)
            return 1
        if not isinstance(targets, list):
            print("ERROR: stdin は配列にしてください", file=sys.stderr)
            return 1
        for t in targets:
            comp = t.get("competitor", "")
            terms = t.get("search_terms") or []
            if not terms:
                continue
            # search_terms を | で OR結合してMeta広告ライブラリに投げる代わりに、
            # 各termで叩いて ad_archive_id で dedupe（Metaの検索精度が語ごとに違うため）
            merged: dict[str, dict] = {}
            for term in terms:
                try:
                    cs = run_one(term, args.country, args.days, args.limit, token)
                except Exception as e:  # noqa: BLE001
                    print(f"WARN: {comp} / {term}: {e}", file=sys.stderr)
                    continue
                for c in cs:
                    merged.setdefault(c["ad_archive_id"], c)
                time.sleep(1)  # Actor 側のrate limit配慮
            results.append({
                "competitor": comp,
                "queries": terms,
                "creatives": list(merged.values()),
            })
    else:
        if not args.query:
            print("ERROR: --query か --batch のどちらかが必要", file=sys.stderr)
            return 1
        cs = run_one(args.query, args.country, args.days, args.limit, token)
        results.append({
            "competitor": args.query,
            "query": args.query,
            "creatives": cs,
        })

    out = {"results": results}
    if args.json:
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        for r in results:
            print(f"■ {r.get('competitor')}: {len(r.get('creatives', []))}件")
            for c in r.get("creatives", []):
                print(f"  ・[{c['started_on']} / {c['format']}] {c['headline'][:60]}")
                print(f"    {c['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

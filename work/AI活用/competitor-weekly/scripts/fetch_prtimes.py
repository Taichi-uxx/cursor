#!/usr/bin/env python3
"""PRTimes企業ページから直近リリースを取得する。

PRTimesは各社ページの RSS が `https://prtimes.jp/companyrdf.php?company_id=<ID>` で
配信されている（RDF/RSS 1.0）。過去N日以内のリリースだけ返す。

使い方:
  python3 fetch_prtimes.py --ids 12345,67890 --days 7 --json
出力:
  {"releases": [
    {"company_id":"12345","title":"...","url":"...","posted_at":"YYYY-MM-DD","description":"..."},
    ...
  ]}
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

try:
    import feedparser
except ImportError:
    print("ERROR: feedparser が必要です。pip install feedparser", file=sys.stderr)
    sys.exit(1)


RSS_TMPL = "https://prtimes.jp/companyrdf.php?company_id={cid}"


def parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    for attr in ("published", "updated", "dc_date"):
        s = getattr(entry, attr, None)
        if s:
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00"))
            except ValueError:
                continue
    return None


def fetch_one(cid: str, since: datetime) -> list[dict]:
    url = RSS_TMPL.format(cid=cid)
    d = feedparser.parse(url)
    out: list[dict] = []
    for entry in d.entries:
        posted = parse_date(entry)
        if posted is None or posted < since:
            continue
        out.append({
            "company_id": cid,
            "title": getattr(entry, "title", "").strip(),
            "url": getattr(entry, "link", "").strip(),
            "posted_at": posted.astimezone().date().isoformat(),
            "description": (getattr(entry, "summary", "") or "").strip()[:400],
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ids", required=True, help="カンマ区切りのPRTimes企業ID")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    releases: list[dict] = []
    for cid in [x.strip() for x in args.ids.split(",") if x.strip()]:
        try:
            releases.extend(fetch_one(cid, since))
        except Exception as e:  # noqa: BLE001
            print(f"WARN: failed for company_id={cid}: {e}", file=sys.stderr)

    releases.sort(key=lambda r: r.get("posted_at", ""), reverse=True)

    if args.json:
        json.dump({"releases": releases}, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        for r in releases:
            print(f"[{r['posted_at']}] {r['title']}\n  {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

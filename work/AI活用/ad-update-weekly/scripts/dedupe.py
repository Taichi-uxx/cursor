#!/usr/bin/env python3
"""
既通知URL履歴の check / add を担うヘルパー。

履歴ファイル: /Users/apple/.cursor/work/AI活用/ad-update-weekly/data/notified_urls.txt
形式: 1行1URL（先頭にタイムスタンプ、TAB区切り）。
      例: 2026-09-03T09:00:00\thttps://example.com/blog/xxx

使い方:
  # URLが既通知か判定（0=新規, 1=既通知）
  python3 dedupe.py check "https://..."

  # URLを記録
  python3 dedupe.py add "https://..."

  # 複数URLを一括判定（stdin 1行1URL）
  cat urls.txt | python3 dedupe.py filter    # 未通知URLだけを出力

  # 複数URLを一括記録
  cat urls.txt | python3 dedupe.py add-batch

  # 直近90日以外は自動プルーニング
  python3 dedupe.py prune --days 90
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = Path("/Users/apple/.cursor/work/AI活用/ad-update-weekly/data/notified_urls.txt")


def load_history() -> set[str]:
    if not HISTORY_FILE.exists():
        return set()
    urls: set[str] = set()
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        url = parts[1] if len(parts) == 2 else parts[0]
        urls.add(url.strip())
    return urls


def append(urls: list[str]) -> int:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        for u in urls:
            u = u.strip()
            if u:
                f.write(f"{ts}\t{u}\n")
    return len(urls)


def prune(days: int) -> int:
    if not HISTORY_FILE.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    kept: list[str] = []
    dropped = 0
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            try:
                ts = datetime.fromisoformat(parts[0])
                if ts >= cutoff:
                    kept.append(line)
                else:
                    dropped += 1
                    continue
            except ValueError:
                kept.append(line)
        else:
            kept.append(line)
    HISTORY_FILE.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    return dropped


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("check")
    sp.add_argument("url")

    sp = sub.add_parser("add")
    sp.add_argument("url")

    sub.add_parser("filter")
    sub.add_parser("add-batch")

    sp = sub.add_parser("prune")
    sp.add_argument("--days", type=int, default=90)

    args = p.parse_args()

    if args.cmd == "check":
        return 1 if args.url.strip() in load_history() else 0

    if args.cmd == "add":
        append([args.url])
        return 0

    if args.cmd == "filter":
        history = load_history()
        for line in sys.stdin:
            u = line.strip()
            if u and u not in history:
                print(u)
        return 0

    if args.cmd == "add-batch":
        urls = [line.strip() for line in sys.stdin if line.strip()]
        n = append(urls)
        print(f"added {n} urls")
        return 0

    if args.cmd == "prune":
        n = prune(args.days)
        print(f"pruned {n} old records (older than {args.days} days)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

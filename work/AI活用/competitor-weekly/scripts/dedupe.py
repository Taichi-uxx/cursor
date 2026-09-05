#!/usr/bin/env python3
"""既通知シグナルID履歴 check/add ヘルパー（competitor-weekly 用）。

競合ウォッチでは以下の "ID" を1つの履歴として一元管理する:
  - meta_ad:<ad_archive_id>
  - listing_lp:<url>
  - release:<url>

履歴ファイル: /Users/apple/.cursor/work/AI活用/competitor-weekly/data/notified_ids.txt
形式: 1行1レコード（先頭タイムスタンプ TAB ID）
  例: 2026-09-08T09:00:00\tmeta_ad:1234567890

使い方:
  python3 dedupe.py check "meta_ad:xxxx"
  python3 dedupe.py add "meta_ad:xxxx"
  cat ids.txt | python3 dedupe.py filter        # 未通知IDだけ出力
  cat ids.txt | python3 dedupe.py add-batch
  python3 dedupe.py prune --days 180
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = Path("/Users/apple/.cursor/work/AI活用/competitor-weekly/data/notified_ids.txt")


def load_history() -> set[str]:
    if not HISTORY_FILE.exists():
        return set()
    ids: set[str] = set()
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        ids.add((parts[1] if len(parts) == 2 else parts[0]).strip())
    return ids


def append(ids: list[str]) -> int:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        for i in ids:
            i = i.strip()
            if i:
                f.write(f"{ts}\t{i}\n")
    return len(ids)


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
    sp = sub.add_parser("check"); sp.add_argument("id")
    sp = sub.add_parser("add"); sp.add_argument("id")
    sub.add_parser("filter")
    sub.add_parser("add-batch")
    sp = sub.add_parser("prune"); sp.add_argument("--days", type=int, default=180)
    args = p.parse_args()

    if args.cmd == "check":
        return 1 if args.id.strip() in load_history() else 0
    if args.cmd == "add":
        append([args.id]); return 0
    if args.cmd == "filter":
        history = load_history()
        for line in sys.stdin:
            i = line.strip()
            if i and i not in history:
                print(i)
        return 0
    if args.cmd == "add-batch":
        ids = [line.strip() for line in sys.stdin if line.strip()]
        n = append(ids); print(f"added {n} ids"); return 0
    if args.cmd == "prune":
        n = prune(args.days); print(f"pruned {n} old records (older than {args.days} days)"); return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

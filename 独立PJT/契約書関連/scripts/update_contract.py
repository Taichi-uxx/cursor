#!/usr/bin/env python3
"""
契約一覧.md の1行を更新するヘルパー。
Cursor/Claude Code の contract-manager スキルから呼ばれる想定。

使い方:
  # 自動延長 +3ヶ月（終了日+3ヶ月・通知期日+3ヶ月）
  python3 update_contract.py "エムエム" extend --months 3

  # 終了日を明示指定
  python3 update_contract.py "エムエム" extend --until 2027-05-31

  # 契約終了で確定
  python3 update_contract.py "エムエム" end

  # active に戻す（誤発火の巻き戻し用）
  python3 update_contract.py "エムエム" reactivate

案件名は前方一致で1件ヒットすればOK（複数ヒットでエラー）。
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_contracts import parse_contracts, write_contracts, CONTRACT_FILE, parse_date  # type: ignore


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    # 月末補正
    from calendar import monthrange
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def find_contract(contracts, query: str):
    hits = [c for c in contracts if query in c.name]
    if not hits:
        return None, f"該当なし: {query}"
    if len(hits) > 1:
        return None, f"複数ヒット: {[c.name for c in hits]}"
    return hits[0], None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("name", help="案件名（部分一致OK）")
    p.add_argument("action", choices=["extend", "end", "reactivate"])
    p.add_argument("--months", type=int, help="延長月数（extend時）")
    p.add_argument("--until", type=str, help="延長後の終了日 YYYY-MM-DD（extend時）")
    p.add_argument("--notify-offset-days", type=int, default=None,
                   help="通知期日を終了日の何日前にするか（未指定なら既存のオフセットを維持）")
    p.add_argument("--note", type=str, help="備考に追記")
    args = p.parse_args()

    contracts, lines = parse_contracts(CONTRACT_FILE)
    c, err = find_contract(contracts, args.name)
    if err:
        print(err, file=sys.stderr)
        return 1

    if args.action == "extend":
        if not c.end:
            print(f"既存終了日が無いので --until が必須: {c.name}", file=sys.stderr)
            return 1
        old_end = c.end
        old_notify = c.notify_by
        # 通知期日と終了日のオフセットを既存から算出（デフォルト30日前）
        offset_days = args.notify_offset_days
        if offset_days is None:
            offset_days = (old_end - old_notify).days if old_notify else 30

        if args.until:
            new_end = parse_date(args.until)
            if not new_end:
                print(f"--until は YYYY-MM-DD 形式: {args.until}", file=sys.stderr)
                return 1
        elif args.months:
            new_end = add_months(old_end, args.months)
        else:
            print("extend には --months か --until のいずれかが必要", file=sys.stderr)
            return 1

        c.end = new_end
        c.notify_by = new_end - timedelta(days=offset_days)
        c.status = "active"
        if args.note:
            c.note = (c.note + " / " if c.note else "") + args.note
        print(f"更新: {c.name}  終了日 {old_end} → {new_end}  通知期日 {old_notify} → {c.notify_by}")

    elif args.action == "end":
        c.status = "ended"
        if args.note:
            c.note = (c.note + " / " if c.note else "") + args.note
        print(f"終了確定: {c.name}")

    elif args.action == "reactivate":
        c.status = "active"
        if args.note:
            c.note = (c.note + " / " if c.note else "") + args.note
        print(f"active に戻した: {c.name}")

    write_contracts(CONTRACT_FILE, lines, contracts)
    return 0


if __name__ == "__main__":
    sys.exit(main())

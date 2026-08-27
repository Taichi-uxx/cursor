#!/usr/bin/env python3
"""
契約一覧.md を読み、月初のタイミングで以下2種の通知をChatworkへ送信する。

  ① 通知期日通知: 今月末が「契約終了通知期日」の案件を [info][title]契約終了通知期日[/title][/info] で通知
  ② 終了確認通知: 契約期間終了日を過ぎた案件を [info][title]契約終了確認[/title][/info] で通知
     └ ステータスを active → pending_confirm に自動更新（回答受領後は /contract-manager で active に戻す想定）

環境変数（~/.cursor/.env 等に格納）:
  - CHATWORK_API_TOKEN  : Chatwork APIトークン
  - CHATWORK_ROOM_ID    : 通知先ルームID
  - CHATWORK_TO_ACCOUNT : （任意）自分宛To指定するアカウントID

使い方:
  python3 check_contracts.py                # 通常実行（当月分をチェック）
  python3 check_contracts.py --dry-run      # Chatworkへは送らず内容だけ出力
  python3 check_contracts.py --date 2026-10-01  # 実行日を上書きしてテスト
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # 未インストールでも動くようフォールバック

try:
    import requests
except ImportError:
    print("ERROR: requests パッケージが必要です。 pip3 install requests python-dotenv", file=sys.stderr)
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_FILE = ROOT / "契約一覧.md"
LOG_FILE = ROOT / "scripts" / "check_contracts.log"

CHATWORK_API_BASE = "https://api.chatwork.com/v2"


@dataclass
class Contract:
    name: str
    kind: str
    content: str
    start: Optional[date]
    end: Optional[date]
    notify_by: Optional[date]
    auto_renew: str
    status: str
    note: str
    row_index: int  # ファイル書き戻し用（何行目のtable rowか）


def parse_date(s: str) -> Optional[date]:
    s = s.strip()
    if not s or s == "-":
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_contracts(md_path: Path) -> tuple[list[Contract], list[str]]:
    """契約一覧.md をパース。返り値: (契約リスト, 元のファイル行リスト)"""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    contracts: list[Contract] = []

    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| 案件名") and "終了日" in line:
            header_idx = i
            break

    if header_idx is None:
        return contracts, lines

    # header_idx+1 は区切り行（| --- | ... |）
    for i in range(header_idx + 2, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 9:
            continue
        contracts.append(
            Contract(
                name=cols[0],
                kind=cols[1],
                content=cols[2],
                start=parse_date(cols[3]),
                end=parse_date(cols[4]),
                notify_by=parse_date(cols[5]),
                auto_renew=cols[6],
                status=cols[7],
                note=cols[8],
                row_index=i,
            )
        )

    return contracts, lines


def write_contracts(md_path: Path, lines: list[str], contracts: list[Contract]) -> None:
    """変更を契約一覧.mdへ書き戻す（ステータス更新用）"""
    for c in contracts:
        cols = [
            c.name, c.kind, c.content,
            c.start.isoformat() if c.start else "-",
            c.end.isoformat() if c.end else "-",
            c.notify_by.isoformat() if c.notify_by else "-",
            c.auto_renew, c.status, c.note,
        ]
        lines[c.row_index] = "| " + " | ".join(cols) + " |"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def is_first_day(today: date) -> bool:
    return today.day == 1


def is_same_month(d: Optional[date], today: date) -> bool:
    return d is not None and d.year == today.year and d.month == today.month


def build_notice_period(contracts: list[Contract], today: date) -> Optional[str]:
    """① 今月が通知期日の案件をまとめる"""
    hits = [c for c in contracts if c.status == "active" and is_same_month(c.notify_by, today)]
    if not hits:
        return None
    body = ["[info][title]📅 今月が契約終了通知期日の案件[/title]"]
    body.append(f"実行日: {today.isoformat()}")
    body.append("")
    for c in hits:
        body.append(f"■ {c.name}")
        body.append(f"  契約: {c.kind} / {c.content}")
        body.append(f"  通知期日: {c.notify_by.isoformat()}（今月中）")
        body.append(f"  終了日: {c.end.isoformat() if c.end else '-'}")
        body.append(f"  自動更新: {c.auto_renew}")
        body.append("")
    body.append("→ 継続 or 終了の判断を通知期日までに。")
    body.append("継続でOKなら何もしなくてよい（自動更新で延長される）。")
    body.append("終了させる場合は通知期日までに先方へ書面通知を出すこと。")
    body.append("延長／終了が決まったら Claude Code で /contract-manager <案件名> <アクション> を実行してファイル更新。")
    body.append("[/info]")
    return "\n".join(body)


def build_end_confirm(contracts: list[Contract], today: date) -> tuple[Optional[str], list[Contract]]:
    """② 契約終了日を過ぎた案件の確認通知"""
    hits = [c for c in contracts if c.status == "active" and c.end is not None and c.end < today]
    if not hits:
        return None, []
    body = ["[info][title]❓ 契約終了？確認をお願いします[/title]"]
    body.append(f"実行日: {today.isoformat()}")
    body.append("")
    for c in hits:
        body.append(f"■ {c.name}")
        body.append(f"  契約: {c.kind} / {c.content}")
        body.append(f"  終了日: {c.end.isoformat()}（経過済み）")
        body.append(f"  自動更新: {c.auto_renew}")
        body.append("")
    body.append("→ Cursor/Claude Code で以下のように回答:")
    body.append("   /contract-manager <案件名の一部> <アクション>")
    body.append("   例) /contract-manager Hajimari 自動延長 +3ヶ月")
    body.append("   例) /contract-manager NDA 延長 +1年")
    body.append("   例) /contract-manager ワンスター 終了")
    body.append("   例) /contract-manager 個別 延長 2027-05-31 まで")
    body.append("[/info]")
    # 確認中ステータスへ更新
    for c in hits:
        c.status = "pending_confirm"
    return "\n".join(body), hits


def send_chatwork(message: str, dry_run: bool = False) -> None:
    if dry_run:
        print("--- DRY RUN Chatwork message ---")
        print(message)
        print("--------------------------------")
        return

    token = os.environ.get("CHATWORK_API_TOKEN")
    room_id = os.environ.get("CHATWORK_ROOM_ID")
    to_account = os.environ.get("CHATWORK_TO_ACCOUNT")

    if not token or not room_id:
        raise RuntimeError("CHATWORK_API_TOKEN / CHATWORK_ROOM_ID が環境変数に無い")

    body = message
    if to_account:
        body = f"[To:{to_account}]\n" + body

    resp = requests.post(
        f"{CHATWORK_API_BASE}/rooms/{room_id}/messages",
        headers={"X-ChatWorkToken": token},
        data={"body": body},
        timeout=10,
    )
    resp.raise_for_status()


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Chatworkへ送信せず標準出力へ")
    parser.add_argument("--date", type=str, help="実行日をYYYY-MM-DDで上書き（テスト用）")
    parser.add_argument("--force", action="store_true", help="月初でなくても実行する")
    args = parser.parse_args()

    if load_dotenv:
        # 田村太一の .env は /Users/apple/.cursor/設定まわり/taichi-tamura/.env
        env_candidates = [
            Path("/Users/apple/.cursor/設定まわり/taichi-tamura/.env"),
            Path.home() / ".cursor" / ".env",
            ROOT / ".env",
        ]
        for env_path in env_candidates:
            if env_path.exists():
                load_dotenv(env_path)
                break

    today = parse_date(args.date) if args.date else date.today()
    if today is None:
        print("--date は YYYY-MM-DD 形式で指定してください", file=sys.stderr)
        return 1

    if not is_first_day(today) and not args.force:
        log(f"skip (not day 1): {today.isoformat()}")
        return 0

    if not CONTRACT_FILE.exists():
        log(f"missing contract file: {CONTRACT_FILE}")
        print(f"契約一覧ファイルが無い: {CONTRACT_FILE}", file=sys.stderr)
        return 1

    contracts, lines = parse_contracts(CONTRACT_FILE)

    notice = build_notice_period(contracts, today)
    end_notice, changed = build_end_confirm(contracts, today)

    sent_any = False
    if notice:
        send_chatwork(notice, dry_run=args.dry_run)
        log(f"sent notice_period: {len([c for c in contracts if c.status == 'active' and is_same_month(c.notify_by, today)])} cases")
        sent_any = True
    if end_notice:
        send_chatwork(end_notice, dry_run=args.dry_run)
        log(f"sent end_confirm: {len(changed)} cases")
        sent_any = True

    if changed and not args.dry_run:
        write_contracts(CONTRACT_FILE, lines, contracts)
        log(f"updated status pending_confirm: {[c.name for c in changed]}")

    if not sent_any:
        log(f"nothing to notify: {today.isoformat()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

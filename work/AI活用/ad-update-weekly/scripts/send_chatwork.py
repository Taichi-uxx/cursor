#!/usr/bin/env python3
"""
Chatworkに通知メッセージを送信するヘルパー。

環境変数（`/Users/apple/.cursor/設定まわり/taichi-tamura/.env` 等に格納）:
  - CHATWORK_API_TOKEN : Chatwork APIトークン
  - CHATWORK_ROOM_ID   : 送信先ルームID（AD_UPDATE専用ルームIDを分けたい場合は
                         CHATWORK_ROOM_ID_AD_UPDATE を優先読みする）
  - CHATWORK_TO_ACCOUNT: (任意) 自分宛To指定するアカウントID

使い方:
  # 標準入力からメッセージ本文を渡す（推奨）
  cat message.txt | python3 send_chatwork.py
  cat message.txt | python3 send_chatwork.py --dry-run

  # 直接引数で渡す
  python3 send_chatwork.py --body "テスト送信"
  python3 send_chatwork.py --body "..." --room-id 1234567890
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import requests
except ImportError:
    print("ERROR: requests が必要です。 pip install requests python-dotenv", file=sys.stderr)
    sys.exit(1)


CHATWORK_API_BASE = "https://api.chatwork.com/v2"

ENV_CANDIDATES = [
    Path("/Users/apple/.cursor/設定まわり/taichi-tamura/.env"),
    Path.home() / ".cursor" / ".env",
]


def load_env() -> None:
    if not load_dotenv:
        return
    for p in ENV_CANDIDATES:
        if p.exists():
            load_dotenv(p)
            return


def send(body: str, room_id: str, token: str, to_account: str | None, dry_run: bool) -> None:
    if to_account:
        body = f"[To:{to_account}]\n" + body

    if dry_run:
        print("--- DRY RUN Chatwork message ---")
        print(f"room_id: {room_id}")
        print(body)
        print("--------------------------------")
        return

    resp = requests.post(
        f"{CHATWORK_API_BASE}/rooms/{room_id}/messages",
        headers={"X-ChatWorkToken": token},
        data={"body": body},
        timeout=15,
    )
    resp.raise_for_status()
    print(f"sent: room={room_id} len={len(body)}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--body", type=str, help="メッセージ本文（省略時は標準入力から読む）")
    p.add_argument("--room-id", type=str, help="送信先ルームID（省略時はenv）")
    p.add_argument("--dry-run", action="store_true", help="送信せず内容だけ表示")
    args = p.parse_args()

    load_env()

    body = args.body if args.body is not None else sys.stdin.read()
    if not body or not body.strip():
        print("ERROR: メッセージ本文が空", file=sys.stderr)
        return 1

    token = os.environ.get("CHATWORK_API_TOKEN")
    # AD_UPDATE 専用ルームIDを分けたければ CHATWORK_ROOM_ID_AD_UPDATE を優先
    room_id = (
        args.room_id
        or os.environ.get("CHATWORK_ROOM_ID_AD_UPDATE")
        or os.environ.get("CHATWORK_ROOM_ID")
    )
    to_account = os.environ.get("CHATWORK_TO_ACCOUNT")

    if not args.dry_run:
        if not token:
            print("ERROR: CHATWORK_API_TOKEN が未設定", file=sys.stderr)
            return 1
        if not room_id:
            print("ERROR: CHATWORK_ROOM_ID が未設定（--room-id で明示指定も可）", file=sys.stderr)
            return 1

    send(body, room_id or "-", token or "-", to_account, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

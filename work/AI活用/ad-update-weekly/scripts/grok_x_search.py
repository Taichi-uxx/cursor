#!/usr/bin/env python3
"""
xAI Grok API の Live Search 機能で、指定X（Twitter）アカウントの
直近投稿から「広告アップデート」関連ツイートを抽出する。

環境変数:
  - XAI_API_KEY : xAI APIキー（https://console.x.ai で発行）

使い方:
  # 単一アカウント
  python3 grok_x_search.py --handles GoogleAdsJP --days 7

  # 複数アカウント（カンマ区切り or 複数指定）
  python3 grok_x_search.py --handles GoogleAdsJP,MetaJapan,YJmarketing --days 7

  # JSON出力（他スクリプトからのパイプ用）
  python3 grok_x_search.py --handles ... --days 7 --json

Live Search 仕様: https://docs.x.ai/docs/guides/live-search
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
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


XAI_API_BASE = "https://api.x.ai/v1"

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


SYSTEM_PROMPT = """あなたは広告運用者向けの情報キュレーターです。
指定されたX（Twitter）アカウントの投稿から、以下に該当する投稿だけを抽出してください:

該当する投稿:
- 広告媒体（Google/Meta/Yahoo!/LINE/TikTok/X/その他DSP）の仕様変更、新機能、アップデート、廃止、β提供
- 管理画面の変更、レポート機能の変更
- 広告ポリシーの変更、審査基準の変更
- API・タグ・計測系のアップデート

該当しない投稿（除外）:
- 一般的な事例紹介、勉強会告知、採用情報、雑談
- 過去アップデートの振り返り記事

出力形式は必ず以下のJSONのみ（前後に説明文を入れない）:
{
  "posts": [
    {
      "handle": "<アカウント名>",
      "url": "<投稿URL>",
      "posted_at": "<YYYY-MM-DD>",
      "text": "<投稿本文の要旨(150字以内)>",
      "media": "<Google|Meta|Yahoo!|LINE|TikTok|X|その他>",
      "summary_3line": "<3行要約(改行区切り)>"
    }
  ]
}
該当投稿が無い場合は {"posts": []} を返す。
"""


def build_user_prompt(handles: list[str], days: int) -> str:
    handle_list = ", ".join(f"@{h.lstrip('@')}" for h in handles)
    from_date = (date.today() - timedelta(days=days)).isoformat()
    to_date = date.today().isoformat()
    return (
        f"以下のXアカウントの {from_date} 〜 {to_date} の投稿を確認し、"
        f"広告媒体のアップデート情報に該当するものだけを上記フォーマットで抽出してください。\n\n"
        f"対象アカウント: {handle_list}\n"
        f"抽出期間: {from_date} 〜 {to_date}"
    )


def call_grok(handles: list[str], days: int, api_key: str, model: str = "grok-3-latest") -> dict:
    from_date = (date.today() - timedelta(days=days)).isoformat()
    to_date = date.today().isoformat()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(handles, days)},
        ],
        "search_parameters": {
            "mode": "on",
            "sources": [
                {
                    "type": "x",
                    "x_handles": [h.lstrip("@") for h in handles],
                }
            ],
            "from_date": from_date,
            "to_date": to_date,
            "return_citations": True,
        },
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    resp = requests.post(
        f"{XAI_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()

    content = data["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Grokが説明文を混ぜて返した場合はJSON部分だけ抽出を試みる
        import re

        m = re.search(r"\{[\s\S]*\}", content)
        parsed = json.loads(m.group(0)) if m else {"posts": []}

    citations = data.get("citations") or []
    parsed["_citations"] = citations
    parsed["_raw_model"] = model
    return parsed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--handles", type=str, required=True, help="Xアカウント名（カンマ区切り、@は任意）")
    p.add_argument("--days", type=int, default=7, help="過去何日分を対象にするか（デフォルト7）")
    p.add_argument("--model", type=str, default="grok-3-latest")
    p.add_argument("--json", action="store_true", help="JSONで標準出力")
    args = p.parse_args()

    load_env()
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("ERROR: XAI_API_KEY が未設定（.env に追記が必要）", file=sys.stderr)
        return 1

    handles = [h.strip() for h in args.handles.split(",") if h.strip()]
    if not handles:
        print("ERROR: --handles が空", file=sys.stderr)
        return 1

    result = call_grok(handles, args.days, api_key, args.model)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    posts = result.get("posts", [])
    if not posts:
        print("該当投稿なし")
        return 0
    for post in posts:
        print("---")
        print(f"[{post.get('media', '?')}] {post.get('handle', '?')} ({post.get('posted_at', '?')})")
        print(f"URL: {post.get('url', '-')}")
        print(post.get("summary_3line", post.get("text", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

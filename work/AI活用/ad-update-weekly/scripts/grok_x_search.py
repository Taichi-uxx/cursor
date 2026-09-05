#!/usr/bin/env python3
"""
xAI Grok API の X Search ツール（/v1/responses エンドポイント）で、
指定X（Twitter）アカウントの直近投稿から「広告アップデート」関連ツイートを抽出する。

環境変数:
  - XAI_API_KEY : xAI APIキー（https://console.x.ai で発行）

使い方:
  # 単一アカウント
  python3 grok_x_search.py --handles ishigurodo --days 7

  # 複数アカウント（カンマ区切り or 複数指定、@は任意）
  python3 grok_x_search.py --handles ishigurodo,AdsShogun,LAPPER_s_HIGH --days 7

  # JSON出力（他スクリプトからのパイプ用）
  python3 grok_x_search.py --handles ... --days 7 --json

xAI docs: https://docs.x.ai/developers/tools/x-search
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
XAI_MAX_HANDLES = 20  # x_search の allowed_x_handles 上限

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


PROMPT_TEMPLATE = """指定されたXアカウントの {from_date} 〜 {to_date} の投稿を x_search で確認し、
以下に該当する投稿だけを抽出してください。

該当する投稿:
- 広告媒体（Google/Meta/Yahoo!/LINE/TikTok/X/その他DSP）の仕様変更、新機能、アップデート、廃止、β提供
- 管理画面の変更、レポート機能の変更
- 広告ポリシーの変更、審査基準の変更
- API・タグ・計測系のアップデート

該当しない投稿（除外）:
- 一般的な事例紹介、勉強会告知、採用情報、雑談
- 過去アップデートの単なる振り返り

出力は **必ず以下のJSONオブジェクト形式のみ**（前後に説明文を入れない、コードフェンスも不要）:
{{
  "posts": [
    {{
      "handle": "<アカウント名（@なし）>",
      "url": "<投稿URL>",
      "posted_at": "<YYYY-MM-DD>",
      "text": "<投稿本文の要旨(150字以内)>",
      "media": "<Google|Meta|Yahoo!|LINE|TikTok|X|その他>",
      "summary_3line": "<3行要約(改行区切り)>"
    }}
  ]
}}
該当投稿が無ければ {{"posts": []}} を返す。

対象アカウント: {handle_list}
抽出期間: {from_date} 〜 {to_date}
"""


def build_prompt(handles: list[str], from_date: str, to_date: str) -> str:
    handle_list = ", ".join(f"@{h}" for h in handles)
    return PROMPT_TEMPLATE.format(
        from_date=from_date, to_date=to_date, handle_list=handle_list
    )


def _call_grok_once(handles: list[str], from_date: str, to_date: str, api_key: str, model: str) -> dict:
    payload = {
        "model": model,
        "input": [
            {"role": "user", "content": build_prompt(handles, from_date, to_date)},
        ],
        "tools": [
            {
                "type": "x_search",
                "allowed_x_handles": handles,
                "from_date": from_date,
                "to_date": to_date,
            }
        ],
    }

    resp = requests.post(
        f"{XAI_API_BASE}/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def call_grok(handles: list[str], days: int, api_key: str, model: str, max_retries: int = 1) -> dict:
    """Grok x_search を実行。JSON生成に失敗したら最大 max_retries 回再試行。"""
    from_date = (date.today() - timedelta(days=days)).isoformat()
    to_date = date.today().isoformat()

    if len(handles) > XAI_MAX_HANDLES:
        raise ValueError(
            f"x_search の allowed_x_handles は最大 {XAI_MAX_HANDLES} 件まで（現在 {len(handles)}）"
        )

    attempts = max(1, max_retries + 1)
    last_parsed: dict = {}
    last_assistant_text = ""
    last_citations: list[str] = []

    for attempt in range(1, attempts + 1):
        data = _call_grok_once(handles, from_date, to_date, api_key, model)
        assistant_text = _extract_assistant_text(data)
        citations = _extract_citations(data)
        parsed = _parse_json_object(assistant_text)

        last_parsed = parsed
        last_assistant_text = assistant_text
        last_citations = citations

        # 成功条件: parse_error=False かつ (posts>0 or citations少ない)
        # ＝ Grokが検索を打ち切ってJSON返せなかったケース(parse_error+citations多)は再試行
        parse_ok = not parsed.get("_parse_error")
        looks_stuck = parsed.get("_parse_error") and len(citations) >= 20
        if parse_ok and not looks_stuck:
            parsed["_attempts"] = attempt
            parsed["_citations"] = citations
            parsed["_raw_model"] = model
            parsed["_assistant_text"] = assistant_text
            return parsed

        if attempt < attempts:
            print(
                f"[grok_x_search] parse_error/stuck (attempt {attempt}/{attempts}) → retry",
                file=sys.stderr,
            )

    last_parsed["_attempts"] = attempts
    last_parsed["_citations"] = last_citations
    last_parsed["_raw_model"] = model
    last_parsed["_assistant_text"] = last_assistant_text
    return last_parsed


def _extract_assistant_text(data: dict) -> str:
    """/v1/responses の output 配列から assistant のテキストを抽出"""
    for item in data.get("output", []):
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue
        parts: list[str] = []
        for c in item.get("content", []):
            if c.get("type") in ("output_text", "text"):
                parts.append(c.get("text", ""))
        if parts:
            return "\n".join(parts)
    return ""


def _extract_citations(data: dict) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for c in item.get("content", []):
            for ann in c.get("annotations", []) or []:
                if ann.get("type") == "url_citation":
                    u = ann.get("url")
                    if u and u not in seen:
                        seen.add(u)
                        urls.append(u)
    return urls


def _parse_json_object(text: str) -> dict:
    if not text:
        return {"posts": []}
    # コードフェンス除去
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", stripped)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"posts": [], "_parse_error": True}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--handles", type=str, required=True, help="Xアカウント名（カンマ区切り、@は任意）")
    p.add_argument("--days", type=int, default=7, help="過去何日分を対象にするか（デフォルト7）")
    p.add_argument("--model", type=str, default="grok-4.6")
    p.add_argument("--retries", type=int, default=1, help="JSON生成失敗時の再試行回数（デフォルト1=最大2回試行）")
    p.add_argument("--json", action="store_true", help="JSONで標準出力")
    args = p.parse_args()

    load_env()
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print("ERROR: XAI_API_KEY が未設定（.env に追記が必要）", file=sys.stderr)
        return 1

    handles = [h.strip().lstrip("@") for h in args.handles.split(",") if h.strip()]
    if not handles:
        print("ERROR: --handles が空", file=sys.stderr)
        return 1

    result = call_grok(handles, args.days, api_key, args.model, max_retries=args.retries)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    posts = result.get("posts", [])
    if not posts:
        print("該当投稿なし")
        if result.get("_parse_error"):
            print("(JSONパース失敗。--json で生レスポンスを確認)", file=sys.stderr)
        return 0
    for post in posts:
        print("---")
        print(f"[{post.get('media', '?')}] @{post.get('handle', '?')} ({post.get('posted_at', '?')})")
        print(f"URL: {post.get('url', '-')}")
        print(post.get("summary_3line", post.get("text", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""active_clients.yaml を読み、対象案件それぞれの competitor_sources.yaml を統合してJSONで返す。

SKILL.md（Claude側）から Bash 経由で呼ばれ、返ってきたJSONを見て並列サブエージェントに
配分する前提。

使い方:
  python3 resolve_clients.py                    # 有効案件を全部
  python3 resolve_clients.py --client toez      # 特定案件のみ
  python3 resolve_clients.py --list             # 有効案件名だけ列挙

出力（--list 以外）:
  {
    "generated_at": "2026-09-08T09:30:00",
    "clients": [
      {
        "dir": "toez",
        "client_dir_abs": "/Users/apple/.cursor/work/client/toez",
        "display": "株式会社TOEZ（ベビーパーク）",
        "sources_path": "/Users/apple/.cursor/work/client/toez/competitor_sources.yaml",
        "sources_ok": true,
        "sources": { ...competitor_sources.yaml の中身... },
        "memory_path": "/Users/apple/.cursor/work/client/toez/memory.md",
        "memory_exists": true
      },
      ...
    ]
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です。pip install PyYAML", file=sys.stderr)
    sys.exit(1)

REGISTRY = Path(__file__).parent / "active_clients.yaml"
CLIENT_ROOT = Path("/Users/apple/.cursor/work/client")


def load_registry() -> list[dict]:
    if not REGISTRY.exists():
        print(f"ERROR: registry not found: {REGISTRY}", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    return data.get("clients", []) or []


def resolve_client(entry: dict) -> dict:
    dir_name = entry.get("dir")
    if not dir_name:
        return {}
    cdir = CLIENT_ROOT / dir_name
    sources_path = cdir / "competitor_sources.yaml"
    memory_path = cdir / "memory.md"
    sources_data: dict | None = None
    sources_ok = False
    error: str | None = None
    if sources_path.exists():
        try:
            sources_data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
            sources_ok = True
        except Exception as e:  # noqa: BLE001
            error = f"failed to parse yaml: {e}"
    else:
        error = "competitor_sources.yaml not found"
    return {
        "dir": dir_name,
        "client_dir_abs": str(cdir),
        "display": entry.get("display", dir_name),
        "sources_path": str(sources_path),
        "sources_ok": sources_ok,
        "sources": sources_data,
        "sources_error": error,
        "memory_path": str(memory_path),
        "memory_exists": memory_path.exists(),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--client", type=str, help="特定案件（dir名）だけ返す")
    p.add_argument("--list", action="store_true", help="有効案件のdir名だけ列挙")
    args = p.parse_args()

    entries = [e for e in load_registry() if e.get("enabled", True)]
    if args.client:
        entries = [e for e in entries if e.get("dir") == args.client]

    if args.list:
        for e in entries:
            print(e.get("dir", ""))
        return 0

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "clients": [resolve_client(e) for e in entries],
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

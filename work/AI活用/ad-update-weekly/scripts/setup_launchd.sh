#!/bin/bash
# ad-update-weekly の launchd（週次自動化）登録スクリプト。
# 実行方法: bash /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/setup_launchd.sh

set -e

PLIST_SRC="/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/com.taichi.ad-update-weekly.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.taichi.ad-update-weekly.plist"

echo "==> plistをLaunchAgentsへコピー"
cp "$PLIST_SRC" "$PLIST_DST"

echo "==> 既存があればアンロード"
launchctl unload "$PLIST_DST" 2>/dev/null || true

echo "==> ロード（登録）"
launchctl load "$PLIST_DST"

echo "==> 登録確認"
if launchctl list | grep -q ad-update-weekly; then
  echo "✅ 登録成功: 毎週月曜9:00に自動実行されます"
  launchctl list | grep ad-update-weekly
else
  echo "❌ 登録失敗: 上のエラーメッセージを確認してください"
  exit 1
fi

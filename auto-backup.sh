#!/bin/bash
# .cursorフォルダの自動GitHubバックアップ

export PATH="/opt/homebrew/bin:/usr/bin:/bin"

REPO_DIR="/Users/apple/.cursor"
LOG_FILE="/Users/apple/.cursor/auto-backup.log"

cd "$REPO_DIR" || exit 1

if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "自動バックアップ: $(date '+%Y-%m-%d %H:%M')"
    git push origin main >> "$LOG_FILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M') バックアップ完了" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M') 変更なし、スキップ" >> "$LOG_FILE"
fi

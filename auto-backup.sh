#!/bin/bash
# .cursorフォルダの自動GitHubバックアップ

set -uo pipefail

export PATH="/opt/homebrew/bin:/usr/bin:/bin"

REPO_DIR="/Users/apple/.cursor"
LOG_FILE="/Users/apple/.cursor/auto-backup.log"
LOCK_FILE="$REPO_DIR/.git/index.lock"

ts() { date '+%Y-%m-%d %H:%M'; }
log() { echo "$(ts) $*" >> "$LOG_FILE"; }

cd "$REPO_DIR" || { log "[ERROR] cd $REPO_DIR 失敗"; exit 1; }

# 孤児index.lockの自動回復
# - 5分以上前のlockは無条件で削除（前回プロセスは確実に死んでいる）
# - 5分未満でも他にgitプロセスが動いていなければ削除
if [[ -e "$LOCK_FILE" ]]; then
    lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if (( lock_age > 300 )); then
        log "[FIX] 古いindex.lock検出 (${lock_age}秒経過) → 削除"
        rm -f "$LOCK_FILE"
    elif pgrep -x git >/dev/null; then
        log "[WARN] index.lock あり & gitプロセス稼働中。今回はスキップ"
        exit 0
    else
        log "[FIX] 孤児index.lock検出 → 削除"
        rm -f "$LOCK_FILE"
    fi
fi

if [[ -z $(git status --porcelain) ]]; then
    log "[SKIP] 変更なし"
    exit 0
fi

if ! git add -A >> "$LOG_FILE" 2>&1; then
    log "[ERROR] git add 失敗"
    exit 1
fi

if ! git commit -m "自動バックアップ: $(ts)" >> "$LOG_FILE" 2>&1; then
    log "[ERROR] git commit 失敗"
    exit 1
fi

if ! git push origin main >> "$LOG_FILE" 2>&1; then
    log "[ERROR] git push 失敗"
    exit 1
fi

log "[OK] バックアップ完了"

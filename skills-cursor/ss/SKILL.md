---
name: ss
description: >-
  Read a screenshot from the macOS clipboard. Use when the user types /ss to
  share a screenshot for analysis, OCR, or visual review.
disable-model-invocation: true
---

# Screenshot Reader

Reads the current clipboard image and displays it for analysis.

## Instructions

1. Save the clipboard image to a temporary file:

```bash
pngpaste /tmp/claude_clipboard_screenshot.png
```

2. If the command succeeds, read the image file using the Read tool:
   - Path: `/tmp/claude_clipboard_screenshot.png`

3. If the command fails (exit code 1), tell the user:
   - "クリップボードに画像がありません。Cmd+Shift+4 などでスクショを撮ってから再度 /ss を実行してください。"

4. After reading the image, describe or analyze its contents based on any additional user instructions provided via $ARGUMENTS. If no arguments given, describe what you see and ask how the user wants to use it.

## Gotchas

_まだ記録なし。実行中にハマったポイントがあればここに自動追記される。_

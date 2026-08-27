---
name: contract-manager
description: >-
  田村太一の業務委託契約を一元管理するスキル。契約一覧ファイル
  （/Users/apple/.cursor/独立PJT/契約書関連/契約一覧.md）の追加・更新、
  月初のChatwork通知（check_contracts.py）のセットアップ、
  Chatwork通知を受けたユーザー回答（自動延長／終了／期日指定延長など）を
  元にした一覧ファイル更新までを担当。ユーザーが `/contract-manager`
  を呼び出したとき、または「契約」「契約書」「契約管理」「契約更新」
  「契約終了」に関連する会話で使う。
disable-model-invocation: true
---

# 契約管理スキル

田村太一の業務委託契約（クライアント側・パートナー側）を一元管理する。
契約書実体（docx/pdf）は `/Users/apple/.cursor/独立PJT/契約書関連/<クライアント名>/` に、
契約情報の索引は `/Users/apple/.cursor/独立PJT/契約書関連/契約一覧.md` に置く。

## 三大機能

1. **契約追加** — 新規契約を `契約一覧.md` に登録
2. **契約更新** — Chatwork通知への回答を受けて一覧を書き換え
3. **セットアップ** — 月初通知（launchd）の導入・停止

## 呼び出しパターン

ユーザーの入力から以下を判定し、対応する節へ進む。

| 入力例 | 判定 |
|---|---|
| `/contract-manager` （引数なし） | ユーザーへ「追加／更新／セットアップ／一覧表示」のいずれかを聞く |
| `/contract-manager 追加` / `新規契約` / `契約登録` | → **契約追加** |
| `/contract-manager <案件名> 延長 …` / `自動延長` / `+Nヶ月` / `〜まで` | → **契約更新（延長）** |
| `/contract-manager <案件名> 終了` | → **契約更新（終了）** |
| `/contract-manager セットアップ` / `cron` / `launchd` | → **セットアップ** |
| `/contract-manager 一覧` / `list` | → 契約一覧を表示 |

---

## 1. 契約追加

ユーザーから以下を1つずつ、または一括で受け取る（欠けている項目のみ聞く）。

- 案件名（必須）
- 契約種別（例: 業務委託基本契約 / 個人業務委託 / 秘密保持契約）
- 契約内容（1行）
- 開始日（YYYY-MM-DD）
- 終了日（YYYY-MM-DD）
- 通知期日（YYYY-MM-DD）
- 自動更新（"あり(+3ヶ月)" / "あり(+6ヶ月)" / "あり(+1年)" / "なし"）
- 備考（任意）

受け取ったら `契約一覧.md` の表末尾に1行追加する（Editツールで表の最後の行の後に挿入）。
ステータスは常に `active` で登録する。

契約書ファイル（docx/pdf）が別途あるなら、格納先パスを提示する:
`/Users/apple/.cursor/独立PJT/契約書関連/<クライアント名>/` （存在しなければ作成を促す）

---

## 2. 契約更新（Chatwork通知への回答を受けて）

月初にChatwork通知が来た後、ユーザーが以下のように答える:

- `/contract-manager エムエム 自動延長 +3ヶ月`
- `/contract-manager エムエム 延長 2027-05-31 まで`
- `/contract-manager エムエム 終了`

### 判定と実行

**延長パターン**を検出したら:
- `+Nヶ月` / `Nヶ月延長` → `extend --months N`
- `YYYY-MM-DD まで` / `YYYY/MM/DD` → `extend --until YYYY-MM-DD`

**終了パターン**を検出したら → `end`

### 実行コマンド

Bashツールで以下を実行:

```bash
/Users/apple/.cursor/独立PJT/契約書関連/scripts/.venv/bin/python \
  /Users/apple/.cursor/独立PJT/契約書関連/scripts/update_contract.py \
  "<案件名の一部>" <action> [--months N | --until YYYY-MM-DD] [--note "回答日時など"]
```

スクリプトの出力（更新前後の日付）をそのままユーザーに提示して確認を取る。
複数案件ヒットで失敗した場合、候補を提示してどれか選んでもらう。

### 特殊ケース

- **回答が曖昧**（例: "たぶん延長される"）→ 確定してから再度呼んでもらう旨返す。書き換えない。
- **回答が新規条件**（例: "終了だけど成果報酬で3ヶ月継続"）→ 一旦 `end` で既存を終了させ、続けて **契約追加** で新条件の契約を登録する。

---

## 3. セットアップ（launchd）

macOSでは cron よりも launchd を推奨（スリープ中でもキャッチアップ実行される）。
初回セットアップ時に、以下の手順をユーザーに提示する。

### Step 1: .env に Chatwork API 情報を追記

`/Users/apple/.cursor/設定まわり/taichi-tamura/.env` に以下3行を追記（**Claudeは .env を読み書きしないので、ユーザー自身が追記**）:

```
CHATWORK_API_TOKEN=<Chatworkの個人APIトークン>
CHATWORK_ROOM_ID=<通知先ルームID>
CHATWORK_TO_ACCOUNT=<自分のアカウントID>   # 任意。To指定したい場合のみ
```

- APIトークンは https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php で発行
- ルームIDはChatworkのURL末尾の数字（`https://www.chatwork.com/#!rid1234567890` の `1234567890`）
- アカウントIDは https://www.chatwork.com/service/packages/chatwork/subpackages/profile.php で確認

### Step 2: 事前テスト

Bashツールで以下を実行し、Chatworkへ実際に届くかテスト:

```bash
/Users/apple/.cursor/独立PJT/契約書関連/scripts/.venv/bin/python \
  /Users/apple/.cursor/独立PJT/契約書関連/scripts/check_contracts.py --force --date $(date +%Y-%m-01)
```

`--force` で月初以外でも実行、`--date` で当月1日として扱わせる。
（`--dry-run` を付けるとChatworkに送らず内容だけ確認できる）

### Step 3: launchd 登録

`~/Library/LaunchAgents/com.taichi.contract-check.plist` を Writeツールで以下内容で作成:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taichi.contract-check</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/apple/.cursor/独立PJT/契約書関連/scripts/.venv/bin/python</string>
        <string>/Users/apple/.cursor/独立PJT/契約書関連/scripts/check_contracts.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/apple/.cursor/独立PJT/契約書関連/scripts/launchd.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/apple/.cursor/独立PJT/契約書関連/scripts/launchd.stderr.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

その後、以下のコマンドをユーザーに実行してもらう:

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.contract-check.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.taichi.contract-check.plist
launchctl list | grep contract-check   # 登録確認
```

### Step 4: 停止したい場合

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.contract-check.plist
```

---

## Gotchas

- `.env` は絶対に Read/Write/表示しない（CLAUDE.md ルール）。ユーザー自身に貼ってもらう
- 契約一覧.mdの表フォーマット（列数=9）を崩さない。Editツールで行追加するときは必ず既存表と同じ `|` 数
- `check_contracts.py` は月初1日以外はスキップ（`--force` で強制実行）。テスト時は `--dry-run --force --date` を組み合わせる
- 案件名の日本語スラッシュ・記号は launchd/shell では正しく扱われる（bytes safe）。慎重に扱う
- venv Python のパスは絶対パスで固定（`/Users/apple/.cursor/独立PJT/契約書関連/scripts/.venv/bin/python`）。launchd はシェル環境を継承しないので相対パス不可
- 終了確認通知を送るとステータスが自動で `pending_confirm` になる。ユーザーが回答するまで、翌月以降は同じ案件は再通知されない。回答時に必ず `update_contract.py` で `active`（延長）または `ended`（終了）に確定させること

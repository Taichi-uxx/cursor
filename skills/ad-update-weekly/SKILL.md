---
name: ad-update-weekly
description: >-
  広告媒体（Google/Meta/Yahoo!/LINE/TikTok/X 等）のアップデート情報を、
  広告代理店ブログ5サイト＋LINEヤフー公式ニュース＋X投稿から週次で収集し、
  過去7日 & 既通知URL除外でフィルタし、AI要約（タイトル＋URL＋3行）＋
  媒体別グループ化してChatworkに通知する。X投稿は xAI Grok API の X Search ツール
  （/v1/responses）を使用。
  ユーザーが `/ad-update-weekly` を呼び出したとき、または「広告アップデート」
  「媒体アップデート」「週次通知」に関連する会話で使う。
disable-model-invocation: true
---

# 広告媒体アップデート週次通知スキル

広告代理店ブログ＋LINEヤフー公式ニュース＋X投稿から広告媒体のアップデート情報を
週次で拾い、Chatworkに媒体別グループでまとめて通知する。

## 抽出方針（前提）

- **期間**: 過去7日以内の記事・投稿
- **フィルタ**: 「広告アップデート／新機能／仕様変更／β提供／廃止／管理画面変更／
  ポリシー変更／API・タグ変更」に該当するものだけ。事例紹介・採用・雑談は除外
- **重複排除**: `data/notified_urls.txt` に記録済みのURLはスキップ
- **粒度**: 各エントリ「タイトル＋URL＋3行要約（AI要約）」
- **グループ**: Google / Meta / Yahoo! / LINE / TikTok / X / その他 の順で媒体別セクション
- **1回のChatworkメッセージ**にまとめて送る（媒体ごとにセクション見出し）

## 呼び出しパターン

| 入力例 | 判定 |
|---|---|
| `/ad-update-weekly` （引数なし） | 通常実行（過去7日・重複排除・Chatwork送信） |
| `/ad-update-weekly --dry-run` | Chatworkに送らず内容だけ表示（重複履歴も更新しない） |
| `/ad-update-weekly --days 14` | 抽出期間を過去14日に拡張（初回や見逃し補完用） |
| `/ad-update-weekly セットアップ` | Chatwork認証・XAI認証チェック＋launchd登録手順を案内 |
| `/ad-update-weekly セットアップ停止` | launchdを停止する手順を案内 |

---

## 通常実行のフロー

### Step 1: 環境チェック（軽く1発）

Bashツールで以下を実行し、必要な環境変数が読めるか確認:

```bash
/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  -c "import os; from dotenv import load_dotenv; \
      load_dotenv('/Users/apple/.cursor/設定まわり/taichi-tamura/.env'); \
      print('CHATWORK_API_TOKEN:', 'ok' if os.environ.get('CHATWORK_API_TOKEN') else 'MISSING'); \
      print('CHATWORK_ROOM_ID:', 'ok' if (os.environ.get('CHATWORK_ROOM_ID_AD_UPDATE') or os.environ.get('CHATWORK_ROOM_ID')) else 'MISSING'); \
      print('XAI_API_KEY:', 'ok' if os.environ.get('XAI_API_KEY') else 'MISSING (Xスキップ)')"
```

- CHATWORK_API_TOKEN / CHATWORK_ROOM_ID が MISSING → **セットアップ節** へ誘導
- XAI_API_KEY が MISSING → X投稿収集はスキップし、ブログ・LYCのみで続行

### Step 2: 収集対象の読み込み

`/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/sources.yaml` を Read して
`blogs`, `lyc`, `x_handles` を取得する。

### Step 3: ブログ＋LYC の巡回・記事抽出

各 URL に対して以下を並列に実行（Agent tool の Explore or general-purpose、
subagent_type=Explore を1件1エージェントで並列起動する。**トークン節約と抽出精度のため
親コンテキストにHTML本文を落とさない**）:

各エージェントへの指示:
```
以下のURLを Playwright MCP または WebFetch で取得し、
過去{days}日以内かつ「広告媒体のアップデート／新機能／仕様変更／β提供／廃止／
管理画面変更／ポリシー変更／API・タグ変更」に該当する記事のみ抽出せよ。

URL: <ソースURL>
ヒント: <sources.yamlのhint>
今日の日付: <YYYY-MM-DD>
過去何日以内か: <days>

出力（必ずJSONのみ、前後に文章不要）:
{
  "articles": [
    {
      "title": "<記事タイトル>",
      "url": "<記事フルURL>",
      "posted_at": "<YYYY-MM-DD>",
      "media": "Google|Meta|Yahoo!|LINE|TikTok|X|その他",
      "summary_3line": "<3行要約(改行区切り)>"
    }
  ]
}

該当なしなら {"articles": []}。
リンクだけ抽出して終わらせず、必ず記事本文まで確認して 3行要約と media を埋めること。
記事日付が読み取れない場合はスキップ（推測しない）。
```

**注意**:
- ブログの記事一覧ページを解析 → 各記事URLに個別アクセス → 本文から要約、まで踏み込む
- 1ソースあたり最大10件までに絞る（多すぎるならAIが上位10件を選ぶ）
- Playwright MCP を使うときは isolated モード前提（グローバル `.mcp.json` で設定済）

**403 Forbidden時のフォールバック**:

WebFetch/curl直接が403で弾かれるサイト（例: anagrams.jp）は、ブラウザUAとRefererを
偽装する `fetch_ua.py` ヘルパーで取得する。**サブエージェントには最初からこのヘルパーの
存在を伝え、WebFetchが403だったら即Bashで切り替えるよう指示すること**。

```bash
# 記事一覧ページ → <a>タグとアンカーテキストだけ抽出（トークン節約）
/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/fetch_ua.py \
  "<URL>" --links --max-chars 5000

# 記事詳細ページ → 本文テキスト抽出
/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/fetch_ua.py \
  "<記事URL>" --text --max-chars 8000
```

`fetch_ua.py` は Chrome UA + `Referer: https://www.google.com/` + `Accept-Language: ja` を送る。
`--links` は `<a href>	<アンカーテキスト>` タブ区切り、`--text` は script/style除去済み可視テキスト。

### Step 4: X投稿の取得（XAI_API_KEY があるときのみ）

`sources.yaml` の `x_handles` が空でなく XAI_API_KEY があるなら、Bashツールで実行:

```bash
/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/grok_x_search.py \
  --handles <カンマ区切り> --days 7 --json
```

出力JSONの `posts` 配列を後段で統合する。`x_handles` が空なら **X収集はスキップ**
（ユーザーにアカウント名を渡してもらう案内をログに残す）。

`grok_x_search.py` は `--retries N`（デフォルト1）で JSON生成に失敗した場合に自動再試行。
Grokが検索途中で reasoning に token を使い切って生JSONを返せないケース（`_parse_error: true`
かつ citations多数）で1回だけリトライする。それでも失敗するアカウントは
ハンドルを1つずつ分割して個別リクエストにする（ハンドル数を減らすと安定する）。

### Step 5: URL重複排除

全エントリのURLを1行1URLで stdin に渡して `dedupe.py filter` を実行し、
未通知URLだけを受け取る:

```bash
printf '%s\n' "url1" "url2" "url3" | \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/dedupe.py filter
```

返ってきたURLに該当するエントリだけを残す。

### Step 6: 媒体別グループ化＋Chatworkメッセージ組み立て

以下のフォーマットで組み立てる（Chatwork記法）:

```
[info][title]📣 広告媒体アップデート週報 YYYY-MM-DD[/title]
対象期間: YYYY-MM-DD 〜 YYYY-MM-DD
新規: <合計件数>件（ブログ <N> / LYC <N> / X <N>）

━━━ Google ━━━
■ <タイトル>
  <URL>
  <3行要約 1行目>
  <3行要約 2行目>
  <3行要約 3行目>
  出典: <ソース名（ブログ名 or @ハンドル）>

━━━ Meta ━━━
（以下同様）

━━━ Yahoo! ━━━
━━━ LINE ━━━
━━━ TikTok ━━━
━━━ X（プラットフォーム全般） ━━━
━━━ その他 ━━━
[/info]
```

- 該当ゼロの媒体セクションは省略する
- 全媒体ゼロなら「今週は該当アップデートなし」の1行だけ送る（履歴更新もなし）
- Chatworkの1メッセージ上限は5000文字程度。超えそうなら媒体ごとに分割送信

### Step 7: Chatworkへ送信

`--dry-run` なら:
```bash
echo "<message>" | python send_chatwork.py --dry-run
```

本番なら:
```bash
echo "<message>" | /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/send_chatwork.py
```

### Step 8: 履歴更新（`--dry-run` でない場合のみ）

送信成功後、通知したURL一覧を `dedupe.py add-batch` で記録:

```bash
printf '%s\n' "url1" "url2" "url3" | \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/dedupe.py add-batch
```

月に1回程度、`dedupe.py prune --days 90` で古い履歴を掃除するのを推奨（省略可）。

---

## セットアップ（初回のみ）

### Step 1: venv 作成 + 依存パッケージインストール

Bashツールで以下を実行:

```bash
cd "/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts" && \
  python3 -m venv .venv && \
  .venv/bin/pip install -r requirements.txt
```

### Step 2: .env に必要キーを追記

`/Users/apple/.cursor/設定まわり/taichi-tamura/.env` に以下を追記
（**Claudeは .env を読み書きしないので、ユーザー自身が追記**）:

```
# Chatwork（未設定なら追加。contract-manager 用と共通で OK）
CHATWORK_API_TOKEN=<個人APIトークン>
CHATWORK_ROOM_ID=<既定の通知先ルームID>

# 広告アップデート通知を別ルームに送りたい場合のみ（優先される）
CHATWORK_ROOM_ID_AD_UPDATE=<専用ルームID>

# xAI Grok API（X投稿収集用）
XAI_API_KEY=<xAIのAPIキー、https://console.x.ai で発行>
```

**取得場所**:
- Chatwork APIトークン: https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php
- Chatwork ルームID: 対象ルームを開き URL 末尾 `#!rid1234567890` の `1234567890`
- xAI APIキー: https://console.x.ai （※月$5〜のクレジット購入が必要）

### Step 3: X監視アカウントを sources.yaml に追記

ユーザーから渡された X アカウント名を、`sources.yaml` の `x_handles` へ列挙:

```yaml
x_handles:
  - GoogleAdsJP
  - MetaJapan_M
  - YJmarketing
```

`@` は付けない（スクリプト側で除去する）。

### Step 4: 手動ドライラン

```bash
/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/.venv/bin/python \
  -c "print('venv ok')"
```

その後、ユーザーに `/ad-update-weekly --dry-run --days 14` を実行してもらい、
出力メッセージを目視で確認。品質OKなら本番実行 `/ad-update-weekly` へ。

### Step 5: launchd 登録（週次実行）

plist 本体は `scripts/com.taichi.ad-update-weekly.plist` に**同梱済み**なので、
ユーザーに以下3コマンドを実行してもらうだけでよい:

```bash
cp "/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/com.taichi.ad-update-weekly.plist" ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.taichi.ad-update-weekly.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.taichi.ad-update-weekly.plist
launchctl list | grep ad-update-weekly   # 登録確認
```

plistの中身は以下相当（毎週月曜9:00に `claude -p "/ad-update-weekly"` を叩く）:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taichi.ad-update-weekly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>claude -p "/ad-update-weekly" --output-format text >> /Users/apple/.cursor/work/AI活用/ad-update-weekly/data/launchd.log 2>&amp;1</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/apple/.cursor/work/AI活用/ad-update-weekly/data/launchd.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/apple/.cursor/work/AI活用/ad-update-weekly/data/launchd.stderr.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

- Weekday 1 = 月曜日、9:00 実行（変更したければ数字を編集）
- Claude Code CLI (`claude` コマンド) が PATH に通っている前提。無ければ `~/.local/bin/claude` 等の絶対パスに変更
- スリープ中に発火時刻を過ぎた場合、launchd は起動後にキャッチアップ実行してくれる

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.ad-update-weekly.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.taichi.ad-update-weekly.plist
launchctl list | grep ad-update-weekly
```

### Step 6: 停止したい場合

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.ad-update-weekly.plist
```

---

## Gotchas

- **.env は絶対に Read/Write/表示しない**（CLAUDE.md ルール）。追記はユーザーに依頼
- ブログ記事の抽出は **必ず並列サブエージェント**で行い、本文HTMLを親コンテキストに落とさない
  （品質優先で速度を犠牲にしていい。CLAUDE.mdルール）
- 記事の日付が読み取れないケースはスキップ（推測禁止）
- LYC (`lycbiz.com`) は Yahoo!広告と LINE広告の情報が混在するので、media 判定は本文を読んで判別
- X投稿は Grok API のレスポンス品質にムラがある。返ってこないアカウント名は
  `sources.yaml` から一時外す or `--days` を延ばして再試行
- xAI の Live Search（`search_parameters`）は2026年時点で廃止済み。現在は Agent Tools API
  の `x_search` ツール（`/v1/responses` エンドポイント）を使う。`grok_x_search.py` は
  対応済みだが、xAI 側で再びスキーマ変更されたら要追従（410 Gone が出たらここを疑う）
- x_search の `allowed_x_handles` は **1リクエスト最大20件**。sources.yaml で20超になったら
  複数リクエストに分割する
- 全媒体ゼロ件のときは Chatwork送信しない（履歴も更新しない）→ 見逃し防止
- Chatworkメッセージが長すぎるとき（5000字目安）は媒体単位で分割送信
- launchd はシェル環境を継承しないので、Python も `claude` コマンドも絶対パスで指定
- launchd で `claude -p` を使う場合、Claude Code側の認証（`claude auth`）が
  事前に済んでいる必要あり。初回はターミナルで手動確認
- Playwright MCP は `--isolated` オプション必須（グローバル `.mcp.json` で設定済。
  プラグイン更新で上書きされたら再適用が必要）

## 関連ファイル

- スクリプト実体: `/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/`
- 履歴・ログ: `/Users/apple/.cursor/work/AI活用/ad-update-weekly/data/`
- ソース設定: `/Users/apple/.cursor/work/AI活用/ad-update-weekly/scripts/sources.yaml`
- 参考: 契約管理スキル `/Users/apple/.cursor/skills/contract-manager/SKILL.md`
  （同様に launchd + Chatwork API を使う）

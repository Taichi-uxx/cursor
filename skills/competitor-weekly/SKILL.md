---
name: competitor-weekly
description: >-
  クライアント案件ごとに定義した競合（3c分析.md 2-1 直接競合マップの企業）を対象に、
  過去7日の「新規Meta広告クリエイティブ／リスティング広告の遷移先LP／自社ニュース・PRTimesリリース」
  を週次で収集し、Chatwork集約ルームに通知＋各案件の memory.md に週次サマリを蓄積する。
  Meta広告ライブラリはAPIではなく Playwright MCP で各社ページを直接見に行く（API経由は非推奨）。
  対象案件は scripts/active_clients.yaml、案件別の探索設定は各案件フォルダの
  competitor_sources.yaml で管理。ユーザーが `/competitor-weekly` を呼び出したとき、
  または「競合ウォッチ」「競合の動き」「競合の週次通知」に関連する会話で使う。
disable-model-invocation: true
---

# 競合ウォッチ週次通知スキル

各クライアント案件の競合について、新しい打ち手（Meta広告クリエイティブ／リスティングLP／
プレスリリース）を過去7日で収集し、Chatwork集約ルームに通知＋案件フォルダの memory.md
に蓄積する。

## 抽出方針（前提）

- **期間**: 過去7日以内に検出できた新規シグナル
- **フィルタ**: 3種類のシグナル
  - **Meta広告**: 過去7日で `active` 状態のクリエイティブ（`ad_archive_id` 単位で重複排除）
  - **リスティングLP**: 社名/BIGワード検索結果の広告リンク遷移先URL（`?utm_*` 等の変動パラメータは除去して重複排除）
  - **リリース**: newsroom / PRTimes 掲載の直近リリース（URL単位で重複排除）
- **既通知除外**: `data/notified_ids.txt` に記録済みIDはスキップ（`meta_ad:*` / `listing_lp:*` / `release:*` の prefix で1本管理）
- **通知先**: 単一の集約ルーム `CHATWORK_ROOM_ID_COMPETITOR`（案件別セクションで区切る）
- **memory.md**: 各案件フォルダの `memory.md` に `## 競合ウォッチ（週次自動更新）` セクションを新設・追記（既存があれば新エントリを上に追加）

## 呼び出しパターン

| 入力例 | 判定 |
|---|---|
| `/competitor-weekly`（引数なし） | 有効案件を全部・過去7日・重複排除・Chatwork送信・memory.md更新 |
| `/competitor-weekly --dry-run` | Chatworkに送らず・memory.mdも更新しない・内容だけ表示 |
| `/competitor-weekly --client toez` | 特定案件だけ実行（登録済みかつ enabled=true が前提） |
| `/competitor-weekly --days 14` | 抽出期間を過去14日に拡張 |
| `/competitor-weekly セットアップ` | Chatwork認証チェック＋venv＋launchd登録手順を案内 |
| `/competitor-weekly セットアップ停止` | launchd停止手順を案内 |

---

## 通常実行のフロー

### Step 1: 環境チェック

Bashで以下を実行し、必要なキーとvenvが読めるか確認:

```bash
/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  -c "import os,yaml,feedparser; from dotenv import load_dotenv; \
      load_dotenv('/Users/apple/.cursor/設定まわり/taichi-tamura/.env'); \
      print('CHATWORK_API_TOKEN:', 'ok' if os.environ.get('CHATWORK_API_TOKEN') else 'MISSING'); \
      print('CHATWORK_ROOM_ID:', 'ok' if (os.environ.get('CHATWORK_ROOM_ID_COMPETITOR') or os.environ.get('CHATWORK_ROOM_ID')) else 'MISSING')"
```

- CHATWORK_API_TOKEN / ROOM_ID が MISSING → **セットアップ節** へ誘導
- venvが無い（ImportError）→ **セットアップ節** へ誘導

### Step 2: 対象案件の解決

```bash
/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/resolve_clients.py \
  [--client <dir>]
```

戻り値のJSONを Read し、`clients[].sources_ok=true` の案件だけ後段に流す。
`sources_ok=false` の案件は Chatworkメッセージ末尾に「⚠️ competitor_sources.yaml 未整備」
として列挙して補完を促す（処理は続行）。

### Step 3: 案件×競合×シグナル種別で並列サブエージェントを起動

**重要（品質優先）**: 全てのシグナル収集は **1エージェント=1タスク** で並列に切り出す
（親コンテキストにHTMLを落とさない・トークン節約・抽出精度両立）。
`subagent_type=Explore` を基本、Meta広告ライブラリ／リスティングは Playwright MCP を使うため
`subagent_type=general-purpose` を使う（Playwright MCPが必要な場合）。

#### 3-A. Meta広告ライブラリ収集（競合1社=1エージェント）

各社に対して `general-purpose` サブエージェントを1つ起動:

```
Meta広告ライブラリを Playwright MCP で開き、以下の広告主の過去{days}日以内に
active になっている広告クリエイティブを抽出せよ。API経由は使わない。

対象広告主: <競合名 / 会社名>
Page ID（あれば優先）: <page_ids>
検索フォールバック語: <search_terms>
URL例: https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=JP&q=<会社名>
今日の日付: <YYYY-MM-DD>
過去何日以内か: <days>

手順:
1. Playwright MCP でMeta広告ライブラリを開き、日本(JP) × 全広告 × Active に絞る
2. Page ID があればページ直接指定、無ければ search_terms で検索
3. 表示された各広告カードから ad_archive_id を必ず取得（URL末尾のid）
4. 「Started running on YYYY-MM-DD」の日付が過去{days}日以内のもののみ抽出
5. クリエイティブの要点（ヘッドライン／訴求／フォーマット：静止画・動画・カルーセル）を短く要約

出力（JSONのみ、前後に文章不要）:
{
  "creatives": [
    {
      "ad_archive_id": "1234567890",
      "url": "https://www.facebook.com/ads/library/?id=1234567890",
      "started_on": "YYYY-MM-DD",
      "format": "静止画|動画|カルーセル|不明",
      "headline": "<ヘッドライン or 主要コピー>",
      "summary_1line": "<訴求・見どころ 1行>"
    }
  ]
}

該当なしなら {"creatives": []}。
ad_archive_id が取れないカードはスキップ（推測禁止）。
1広告主あたり最大10件までに絞る（多すぎるなら新しい順に上位10件）。
```

**Gotcha**: Meta広告ライブラリは頻繁にレイアウトが変わる。カードのDOMが取れないときは
Playwright MCPで `browser_snapshot` して構造を再確認してから抽出セレクタを組み直す。

#### 3-B. リスティング広告のLP収集（案件1件=1エージェント）

案件ごとに `general-purpose` サブエージェントを1つ起動（各社×keywords を1つのエージェントで捌く）:

```
Google検索でリスティング広告の遷移先LPを Playwright MCP で収集する。
「広告」「Ad」「Sponsored」の表記があるカードだけ対象。オーガニックは無視する。

案件: <display>
検索語リスト:
  # 競合の指名/BIGワード（各社ごと）
  - {"competitor":"七田式教室","keywords":["七田式","七田式教室"]}
  - {"competitor":"EQWEL","keywords":["EQWEL","イクウェル"]}
  ...
  # 案件全体のBIGワード（competitor="_BIG" とする）
  - {"competitor":"_BIG","keywords":["幼児教室","0歳 習い事"]}

除外語（自社を弾く）: <self_exclude_keywords>

手順（1keywordずつ）:
1. Playwright MCP で https://www.google.co.jp/search?q=<keyword> を開く
2. 検索結果のうち「広告」「Sponsored」表記があるカードを列挙
3. 各広告カードから遷移先URLを取得（クリックせずaタグhref優先。JSリダイレクトなら実際に開いて最終URL）
4. self_exclude_keywords がURLまたは表示ドメインに含まれるものは除外
5. `?utm_*` `&gclid=*` `&fbclid=*` 等の変動パラメータを除去して canonical_url を作る
6. 遷移先LPのタイトル・ヘッドライン（<title> or FVコピー）を短く要約

出力（JSONのみ）:
{
  "listings": [
    {
      "competitor": "七田式教室",
      "keyword": "七田式",
      "canonical_url": "https://www.shichida.co.jp/lp/xxx",
      "raw_url": "<元URL>",
      "display_domain": "shichida.co.jp",
      "title": "<LPタイトル>",
      "summary_1line": "<FVコピー・訴求 1行>"
    }
  ]
}

該当なしなら {"listings": []}。
Google側で reCAPTCHA が出たら、Playwrightで待機し人間介入は求めず、
最大3回リトライして駄目ならその keyword はスキップ（他keywordは続行）。
```

**Gotcha**: Google検索は連続アクセスでCAPTCHAが出やすい。keyword間に短い待機を入れる
（Playwright側で `browser_wait_for` 2-3秒）。それでもCAPTCHAならスキップ。

#### 3-C. リリース情報収集（案件1件=1エージェント）

PRTimes分は Bash で一括取得できるので Bash から実行:

```bash
# 案件ごとに PRTimes 企業IDを集約してカンマ区切り
/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/fetch_prtimes.py \
  --ids <id1>,<id2>,<id3> --days <days> --json
```

**PRTimes ノイズ対策（重要）**: PRTimes企業IDが「持株会社／グループ会社」と紐付いている競合
（例: 小学館集英社プロダクションはドラキッズ以外にアニメ・ゲームリリース多数、学研HDは
めばえ以外のリリースも大量）は、取得したリリースを **競合の name / company / search_terms
のいずれかがタイトル or description に含まれるものだけ**にフィルタする。含まれない
リリースはスキップ（Chatwork通知にも memory.md にも載せない）。この判定は Claude が
Read で確認した後に手動で行う。1リリースずつ「タイトルに七田/しちだが含まれるか」判定するだけの軽い処理。

各社のnewsroom URL は `Explore` サブエージェントに投げる:

```
以下の企業ニュースページから過去{days}日以内に公開された記事のみ抽出せよ。

対象:
  - {"competitor":"七田式教室","url":"https://www.shichida.co.jp/news/"}
  - {"competitor":"EQWEL","url":"https://www.eqwel.jp/news/"}
  ...

手順:
1. Playwright MCP または WebFetch でページ本体を取得
2. 各記事の 見出し・URL・掲載日 を抽出
3. 掲載日が読めない記事はスキップ（推測禁止）
4. 掲載日が過去{days}日以内のもののみ返す

出力（JSONのみ）:
{
  "releases": [
    {
      "competitor": "七田式教室",
      "title": "<記事タイトル>",
      "url": "<記事URL>",
      "posted_at": "YYYY-MM-DD",
      "summary_1line": "<要点1行>"
    }
  ]
}

該当なしなら {"releases": []}。
```

### Step 4: 重複排除

全シグナルに prefix 付きの ID を割り当てて dedupe.py に通す:

- Meta広告: `meta_ad:<ad_archive_id>`
- リスティング: `listing_lp:<canonical_url>`
- リリース（newsroom）: `release:<url>`
- リリース（PRTimes）: `release:<url>`

```bash
printf '%s\n' "meta_ad:xxx" "listing_lp:https://..." "release:https://..." | \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/dedupe.py filter
```

返ってきたIDに該当するシグナルだけ残す。

### Step 5: Chatworkメッセージ組み立て

**単一メッセージ**として以下フォーマットで組み立てる（案件が複数なら案件セクションで区切る）:

```
[info][title]🕵️ 競合ウォッチ週報 YYYY-MM-DD[/title]
対象期間: YYYY-MM-DD 〜 YYYY-MM-DD
対象案件: <N>件 / 新規シグナル合計: <M>件（Meta広告 <a> / リスティングLP <b> / リリース <c>）

━━━━━━━━━━━━━━━━━━━━
【<案件display>】
━━━━━━━━━━━━━━━━━━━━

▼ Meta広告クリエイティブ（新規 <n>件）
■ <競合名>
  ・[YYYY-MM-DD / 動画] <ヘッドライン>
    要点: <summary_1line>
    URL: https://www.facebook.com/ads/library/?id=<id>

▼ リスティング広告LP（新規 <n>件）
■ <競合名>
  ・[kw: <keyword>] <LPタイトル>
    要点: <summary_1line>
    URL: <canonical_url>

▼ プレスリリース／お知らせ（新規 <n>件）
■ <競合名>
  ・[YYYY-MM-DD] <タイトル>
    URL: <url>

━━━━━━━━━━━━━━━━━━━━
【<次の案件>】
（同様）

⚠️ 設定未整備（要対応）
・toez の 七田式教室: PRTimes企業ID未登録
・green: competitor_sources.yaml 未作成
[/info]
```

**ルール**:
- 各案件で該当ゼロのシグナル種別セクションは省略
- 全案件・全種別ゼロなら「今週は新規シグナルなし」の1行だけ送る（履歴更新もmemory.md更新もなし）
- Chatwork 1メッセージ上限は5000文字目安。超えそうなら案件単位で分割送信
- ⚠️ 設定未整備は本文末尾。空なら省略

### Step 6: Chatworkへ送信

`--dry-run` なら:
```bash
echo "<message>" | python send_chatwork.py --dry-run
```

本番なら:
```bash
echo "<message>" | /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/send_chatwork.py
```

### Step 7: 各案件の memory.md に週次サマリを追記

**`--dry-run` でない場合のみ実施。案件×シグナル0件のケースはその案件をスキップ**。

各案件について:

1. `Read` で memory.md 全体を読む
2. `## 競合ウォッチ（週次自動更新）` セクションを検索
   - 無い場合: 冒頭のフロントマター終了後（`---` の直後の空行後）に新セクションとして挿入
   - ある場合: セクション見出しの直後に新エントリを挿入（新しいものが上）
3. 新エントリのフォーマット:

```markdown
### YYYY-MM-DD 週報（対象期間 YYYY-MM-DD 〜 YYYY-MM-DD）
- **新規Meta広告**: <競合A>（n本）／<競合B>（n本）
  - <競合A>: <代表的なsummary_1line>
  - リンク: [ad_archive_id](url), ...
- **新規リスティングLP**: <競合A>（n本）
  - <競合A>: <LPタイトルとキーワード>
  - リンク: <canonical_url>
- **新規リリース**: <競合A>（n本）
  - [YYYY-MM-DD] <タイトル>
    <url>
- **観察So What**: <競合全体の動きの1〜2文の総括>

---
```

`観察So What` は、拾ったシグナル群からClaudeが1〜2文で書く（数値・事実は本文リンク先を根拠に、
憶測は避ける）。特筆すべき動きが無い週は「今週は目立った動きなし」と1行だけ書く。

Edit ツールで既存構造を壊さないよう最小差分で挿入すること。

### Step 8: 履歴更新（`--dry-run` でない場合のみ）

送信成功後、通知した全IDを dedupe.py add-batch で記録:

```bash
printf '%s\n' "meta_ad:xxx" "listing_lp:https://..." "release:https://..." | \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/dedupe.py add-batch
```

月1回程度、`dedupe.py prune --days 180` で古い履歴を掃除するのを推奨（省略可）。

---

## セットアップ（初回のみ）

### Step 1: venv + 依存パッケージ

```bash
cd "/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts" && \
  python3 -m venv .venv && \
  .venv/bin/pip install -r requirements.txt
```

### Step 2: .env に必要キーを追記

`/Users/apple/.cursor/設定まわり/taichi-tamura/.env` に以下を追記
（**Claudeは .env を読み書きしないので、ユーザー自身が追記**）:

```
# Chatwork（未設定なら追加。ad-update-weekly / contract-manager と共通で OK）
CHATWORK_API_TOKEN=<個人APIトークン>
CHATWORK_ROOM_ID=<既定の通知先ルームID>

# 競合ウォッチを別ルームに送りたい場合のみ（優先される）
CHATWORK_ROOM_ID_COMPETITOR=<競合ウォッチ専用ルームID>
```

- Chatwork APIトークン: https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php
- Chatwork ルームID: 対象ルームを開き URL 末尾 `#!rid1234567890` の `1234567890`

### Step 3: 案件を登録

1. `work/AI活用/competitor-weekly/scripts/active_clients.yaml` に案件（`dir`, `display`, `enabled`）を追加
2. `work/client/<dir>/competitor_sources.yaml` を toez を雛形にコピーして中身を書き換え
   - `3c分析.md` 2-1 直接競合マップの各社について、Meta Page ID／リスティングkeywords／
     newsroom URL／PRTimes企業ID を可能な範囲で埋める
   - 未確定フィールドは空でOK（skillは動作可能な範囲でレポートし、未整備は通知末尾で警告する）

### Step 4: 手動ドライラン

```bash
/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
  /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/resolve_clients.py --list
```

有効案件が列挙されればOK。続けて:

```
/competitor-weekly --dry-run --days 14
```

出力を目視で品質確認。OKなら `/competitor-weekly` で本番実行。

### Step 5: launchd 登録（週次月曜 9:30、ad-update-weekly の30分後）

`~/Library/LaunchAgents/com.taichi.competitor-weekly.plist` を Write ツールで作成:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taichi.competitor-weekly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>claude -p "/competitor-weekly" --output-format text >> /Users/apple/.cursor/work/AI活用/competitor-weekly/data/launchd.log 2>&amp;1</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/apple/.cursor/work/AI活用/competitor-weekly/data/launchd.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/apple/.cursor/work/AI活用/competitor-weekly/data/launchd.stderr.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

- Weekday 1 = 月曜、9:30 実行（ad-update-weekly が 9:00 なので30分ずらす）
- Claude Code CLI (`claude` コマンド) が PATH に通っている前提
- スリープ中に発火時刻を過ぎた場合、launchd は起動後にキャッチアップ実行

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.competitor-weekly.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.taichi.competitor-weekly.plist
launchctl list | grep competitor-weekly
```

### 停止したい場合

```bash
launchctl unload ~/Library/LaunchAgents/com.taichi.competitor-weekly.plist
```

---

## Gotchas

- **.env は絶対に Read/Write/表示しない**（CLAUDE.md ルール）。追記はユーザーに依頼
- **Meta広告ライブラリはAPIを使わない**（ユーザー方針）。必ず Playwright MCP で各社ページを直接見る
- **収集は必ず並列サブエージェント**で行い、本文HTMLを親コンテキストに落とさない（品質優先）
- 掲載日が読み取れない記事・広告はスキップ（推測禁止）
- リスティング検索で reCAPTCHA が出たら最大3回リトライしてダメならそのkeywordはスキップ（他は続行）
- 検索クエリの URL変動パラメータ（`utm_*`, `gclid`, `fbclid`）は canonical化してから重複排除。ここを怠ると毎週同じLPを"新規"として通知してしまう
- self_exclude_keywords は必ずリスティング側で適用（自社案件が"競合の動き"として通知される事故を防ぐ）
- Meta広告カードのDOMが変わったら Playwright MCP の `browser_snapshot` で構造を再確認して抽出セレクタを組み直す（Metaは頻繁にレイアウト変更する）
- Playwright MCP は `--isolated` オプション必須（グローバル `.mcp.json` で設定済。プラグイン更新で上書きされたら再適用）
- memory.md 追記は Edit で最小差分。既存構造（フロントマター・イベントログ）を壊さない
- 全案件・全種別ゼロの週は Chatwork送信も memory.md 更新もしない（見逃し防止・ログ肥大化防止）
- Chatworkメッセージが長すぎるとき（5000字目安）は案件単位で分割送信
- launchd はシェル環境を継承しないので、Python も `claude` コマンドも絶対パスで指定
- launchd で `claude -p` を使う場合、Claude Code側の認証（`claude auth`）が事前に済んでいる必要あり
- `active_clients.yaml` に登録したのに `competitor_sources.yaml` が無い案件は、Chatwork通知末尾の「⚠️ 設定未整備」に列挙して補完を促す（スキル自体は落ちない）
- PRTimes RSS は `feedparser` で読める `companyrdf.php?company_id=<ID>` エンドポイント。企業IDは各社PRTimesページ（`prtimes.jp/main/html/searchrlp/company_id/<ID>`）のURLから取得

## 関連ファイル

- スクリプト実体: `/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/`
- 履歴・ログ: `/Users/apple/.cursor/work/AI活用/competitor-weekly/data/`
- 案件レジストリ: `/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/active_clients.yaml`
- 案件別探索設定: `/Users/apple/.cursor/work/client/<案件>/competitor_sources.yaml`
- 参考: 広告アップデート週次スキル `/Users/apple/.cursor/skills/ad-update-weekly/SKILL.md`（同様に launchd + Chatwork API + 並列サブエージェント設計）

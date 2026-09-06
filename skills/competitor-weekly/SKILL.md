---
name: competitor-weekly
description: >-
  クライアント案件ごとに定義した競合（3c分析.md 2-1 直接競合マップの企業）を対象に、
  過去7日の「新規Meta広告クリエイティブ／リスティング広告の遷移先LP／自社ニュース・PRTimesリリース」
  を週次で収集し、Chatwork集約ルームに軽量サマリを通知＋詳細HTMLレポート（バナー画像込み）
  をローカルに生成＋各案件のmemory.mdに週次サマリを蓄積する。
  Meta広告ライブラリは Apify Actor `curious_coder/facebook-ads-library-scraper` で取得
  （Meta公式APIは政治広告のみカバーのため商業広告用途に非対応）。リスティングLPも
  Apify Actor `apify/google-search-scraper`（focusOnPaidAds+RESIDENTIAL proxy）で取得。
  newsroomのみPlaywright/WebFetchのサブエージェントで収集。対象案件は
  scripts/active_clients.yaml、案件別の探索設定は各案件フォルダの
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
      print('CHATWORK_ROOM_ID:', 'ok' if (os.environ.get('CHATWORK_ROOM_ID_COMPETITOR') or os.environ.get('CHATWORK_ROOM_ID')) else 'MISSING'); \
      print('APIFY_TOKEN:', 'ok' if os.environ.get('APIFY_TOKEN') else 'MISSING (Meta広告収集スキップ)')"
```

- CHATWORK_API_TOKEN / ROOM_ID が MISSING → **セットアップ節** へ誘導
- APIFY_TOKEN が MISSING → Meta広告収集Step 3-Aはスキップし、リスティング＋リリースのみで続行
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

#### 3-A. Meta広告ライブラリ収集（Apify経由・1案件=1バッチ呼び出し）

Meta広告ライブラリの一般商業広告はAPI非公開（政治広告のみ公式APIあり）のため、
Apify Actor `curious_coder/facebook-ads-library-scraper` 経由で取得する。
Playwright並列サブエージェント方式は廃止（Meta仕様変更に脆く、DOM/CAPTCHA対応が重かった）。

**特徴**:
- 料金 $0.75 / 1,000 ads（週次70広告なら **月$0.23**、Apify無料枠$5内で十分収まる）
- Actor側でproxy/CAPTCHA対応済み、Meta仕様変更にメンテナー追随
- 1案件全競合を1回のBashコマンドで捌ける（サブエージェント不要）

**実行手順**:

案件ごとに、`competitor_sources.yaml` の全competitorから `{competitor, search_terms}` を
抽出したJSON配列を組み立て、stdin経由で `fetch_meta_ads_apify.py --batch` に流す:

```bash
# 例: toez案件
echo '[
  {"competitor":"七田式教室","search_terms":["七田式教室","しちだ・教育研究所"]},
  {"competitor":"EQWEL","search_terms":["EQWEL","イクウェル"]},
  {"competitor":"Baby Kumon","search_terms":["Baby Kumon","ベビーくもん"]},
  {"competitor":"キッズパル","search_terms":["ミキハウス キッズパル","キッズパル"]},
  {"competitor":"めばえ教室","search_terms":["めばえ教室"]},
  {"competitor":"コペル","search_terms":["幼児教室コペル","コペル 幼児教室"]},
  {"competitor":"ドラキッズ","search_terms":["ドラキッズ"]}
]' | /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
     /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/fetch_meta_ads_apify.py \
     --batch --country JP --days 14 --limit 10 --json
```

**出力スキーマ**（そのままChatworkメッセージ組み立てに使える）:
```json
{
  "results": [
    {
      "competitor": "七田式教室",
      "queries": ["七田式教室","しちだ・教育研究所"],
      "creatives": [
        {
          "ad_archive_id": "1234567890",
          "url": "https://www.facebook.com/ads/library/?id=1234567890",
          "started_on": "YYYY-MM-DD",
          "format": "image|video|carousel|unknown",
          "page_name": "...",
          "page_id": "...",
          "headline": "...",
          "body_snippet": "...",
          "is_active": true
        }
      ]
    }
  ]
}
```

**後段の追加フィルタ（Claudeが手動で判定）**:
Actor は search_terms でマッチした広告を全部返すので、以下のノイズ除去はClaude側で行う:
1. **業態違い**: 例）「コペル」で「コペルプラス」（療育系）が混ざる → page_name / headline で
   幼児教室と関係ないものを除外
2. **同名別会社**: 例）「ミキハウス」の場合、キッズパル運営会社と服飾会社を区別 → page_name / URL で判定
3. **採用広告など目的違い**: 例）「公文教育研究会」で「くもんの先生募集」の採用広告が返る →
   headline/body に「募集」「採用」等が含まれるものを除外

判定はClaudeが Read で JSON を確認して自然言語で行う（複雑ルールを持たせない）。

#### 3-B. リスティング広告のLP収集（Apify経由・1案件=1バッチ呼び出し）

Apify Actor `apify/google-search-scraper` 経由で取得。`focusOnPaidAds=true` + RESIDENTIAL proxy(JP) 必須
（デフォルト設定だとGoogleのbot検知で paidResults がほぼ0件になる）。Playwright方式は廃止。

**特徴**:
- 料金 $1.80 / 1,000 SERPs（週20SERP = **月$0.15**）
- Actor側でproxy切替・広告カード判別済み（paidResults配列に分離）
- 1案件全kwを1回のBashコマンドで捌ける（サブエージェント不要）

**実行手順**:

案件ごとに、`competitor_sources.yaml` の全competitor.listing.keywords＋big_keywordsを
JSON配列に組み立てて stdin経由で `fetch_listing_apify.py --batch` に流す:

```bash
# 例: toez案件
echo '{
  "queries": [
    {"competitor":"七田式教室","keyword":"七田式"},
    {"competitor":"七田式教室","keyword":"七田式教室"},
    {"competitor":"EQWEL","keyword":"EQWEL"},
    {"competitor":"EQWEL","keyword":"イクウェル"},
    {"competitor":"Baby Kumon","keyword":"ベビーくもん"},
    {"competitor":"キッズパル","keyword":"キッズパル"},
    {"competitor":"めばえ教室","keyword":"めばえ教室"},
    {"competitor":"コペル","keyword":"幼児教室 コペル"},
    {"competitor":"ドラキッズ","keyword":"ドラキッズ"},
    {"competitor":"_BIG","keyword":"幼児教室"},
    {"competitor":"_BIG","keyword":"0歳 習い事"},
    {"competitor":"_BIG","keyword":"幼児教育"},
    {"competitor":"_BIG","keyword":"ベビースクール"},
    {"competitor":"_BIG","keyword":"早期教育"}
  ],
  "exclude_domains": ["babypark.jp"],
  "exclude_keywords": ["ベビーパーク","BabyPark","TOEZ"]
}' | /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
     /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/fetch_listing_apify.py \
     --batch --country jp --json
```

**出力スキーマ**:
```json
{
  "listings": [
    {
      "competitor": "七田式教室",
      "keyword": "七田式",
      "canonical_url": "https://center.shichida.co.jp/...",
      "raw_url": "<Google aclk URL>",
      "display_domain": "center.shichida.co.jp",
      "title": "<LP見出し>",
      "summary_1line": "<説明文>",
      "ad_position": 1
    }
  ]
}
```

**own判定（Chatwork組み立て時にClaudeが行う）**:
- `display_domain` が対象competitorの公式ドメイン → `own=true`（本体LP）
- それ以外 → `own=false`（他競合／類似業種の横流入 LP）
- 分類はChatworkメッセージで「■ 競合本体LP」「■ 他競合／類似業種の横流入LP（要警戒）」と分ける

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

### Step 5A: HTMLレポート生成（案件ごと）

**まずHTMLレポートを生成する**（Chatworkメッセージにはこのファイルパスをリンクとして埋め込む）。
集約したシグナル（Meta広告×フィルタ後、リスティング、リリース、So What）を `build_html_report.py`
に流し込む。出力先は `reports/YYYY-MM-DD/<client_dir>.html` （ローカルファイル）。

```bash
echo '{
  "client_display":"株式会社TOEZ（ベビーパーク）",
  "period_from":"YYYY-MM-DD",
  "period_to":"YYYY-MM-DD",
  "meta_ads": {"七田式教室":[...], "コペル":[...], "ドラキッズ":[...]},
  "listings": [{"competitor":..., "keyword":..., "canonical_url":..., "own":true|false, ...}],
  "releases": [{"competitor":..., "posted_at":..., "title":..., "url":..., "summary_1line":...}],
  "so_what": ["示唆1", "示唆2", ...]
}' | /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/.venv/bin/python \
     /Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/build_html_report.py \
     --client-dir <案件dir>
```

戻り値：生成HTML絶対パス（`/Users/apple/.cursor/work/AI活用/competitor-weekly/reports/YYYY-MM-DD/<案件dir>.html`）
→ Chatworkメッセージに `file://<絶対パス>` として埋め込み

Meta広告のcreativeオブジェクトに事前に `pitch` フィールドを追加する（Claudeがbody_snippetを読んで
「キャンペーン＋主訴求＋CTA」の1行に要約したもの。HTMLレポート・Chatworkメッセージ両方で使う）。

### Step 5B: Chatworkメッセージ組み立て（軽量版）

**方針**: Chatworkは骨格だけ、詳細（画像・全文body・全件）はHTMLレポートに任せる。
目安: 3000字前後。各競合上位5件までChatworkに、残りは「他N件（HTMLレポート参照）」で流す。

**各Meta広告の1行要点は「キャンペーン＋主訴求＋CTA」**の形式でClaudeがbody_snippetを読んで生成:
- 例: `入会金0円CP(〜9/30) ／ 少人数月齢別・低年齢帯訴求 ／ →無料体験誘導`
- キャンペーン: 「入会金0円」「初月半額」「秋のスタート応援」等（期限があれば併記）
- 主訴求: 「少人数月齢別」「低年齢帯」「オンライン」「英会話」「知育」等
- CTA: `snapshot.cta_text` を日本語化（Learn more→無料体験誘導、Sign up→申込誘導 等）

```
[info][title]🕵️ 競合ウォッチ週報 YYYY-MM-DD[/title]
対象期間: YYYY-MM-DD 〜 YYYY-MM-DD
シグナル: <M>件（Meta <a> / LP <b> / リリース <c>）

📊 詳細レポート（画像・訴求軸込み）:
file:///Users/apple/.cursor/work/AI活用/competitor-weekly/reports/YYYY-MM-DD/<案件dir>.html

━━━━━━━━━━━━━━━━━━━━
【<案件display>】
━━━━━━━━━━━━━━━━━━━━

▼ Meta広告 (<n>件)
■ <競合名>（<n>件）
  ・[YYYY-MM-DD/format/Nバリエ] <キャンペーン ／ 主訴求 ／ →CTA>
    <Meta広告ライブラリURL>
  ・…他N件（HTMLレポート参照）
■ 新規Meta広告なし: <競合A> / <競合B>

▼ リスティングLP (<n>件)
■ 競合本体LP（<n>件）
  ・[kw:<keyword>] <LPタイトル> (<display_domain>)
■ 他競合/類似業種の横流入LP（<n>件・要警戒）
  ・[kw:<複数kwカンマ結合>] <LPタイトル> (<display_domain>)

▼ プレスリリース／お知らせ (<n>件)
■ <競合名>（<n>件）
  ・[YYYY-MM-DD] <タイトル>
  ・…他N件

📌 今週のSo What
・<示唆1>
・<示唆2>
・<示唆3>

⚠️ ノイズ除外: <n>件（詳細はHTMLレポート末尾）
[/info]
```

**ルール**:
- 各競合で新規5件超なら上位5件のみChatworkに出し、残りは「他N件（HTMLレポート参照）」表記
- Chatworkメッセージ内には個別広告のbody_snippet／link_url／画像URLは載せない（HTMLに任せる）
- 各案件で該当ゼロのシグナル種別セクションは省略
- 全案件・全種別ゼロなら「今週は新規シグナルなし」の1行だけ送る（HTML生成もmemory.md更新もなし）
- Chatwork 1メッセージ上限は5000文字目安。案件数が多くて超えそうなら案件単位で分割
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

# Apify（Meta広告ライブラリ収集用・必須）
APIFY_TOKEN=<Apify Console → Settings → Integrations で発行>
```

- Chatwork APIトークン: https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php
- Chatwork ルームID: 対象ルームを開き URL 末尾 `#!rid1234567890` の `1234567890`
- Apify サインアップ: https://apify.com/sign-up （無料プランで月$5クレジット付与、本用途は月$0.23程度）
- Apify APIトークン: サインアップ後 Console → Settings → Integrations → Personal API tokens

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
- **Meta広告ライブラリはApify経由**（`curious_coder/facebook-ads-library-scraper`）。Meta公式APIは政治広告のみのため一般商業広告は取れない
- **リスティングLPもApify経由**（`apify/google-search-scraper`）。**`focusOnPaidAds=true` + RESIDENTIAL proxy(JP) 必須**（デフォルトだとJP paidResults がほぼ0件）。`fetch_listing_apify.py` は設定済み
- Playwright方式は Meta広告・リスティングの両方から廃止。newsroom収集のみサブエージェントで実施
- **Apify Actor返却データのノイズ除去はClaude側で行う**: 業態違い（例: コペルプラス=療育、公文=採用広告）、同名別会社（例: ミキハウス=服飾/教室）を page_name / headline を見て除外
- **各Meta広告に `pitch` フィールドをClaudeが付与**する必要あり（build_html_report.pyとChatworkメッセージ両方で使う）。「キャンペーン＋主訴求＋CTA」形式（例: `入会金0円CP(〜9/30) ／ 少人数月齢別 ／ →無料体験誘導`）でbody_snippetから自然要約
- **HTMLレポートは毎週別ディレクトリ**（`reports/YYYY-MM-DD/<案件dir>.html`）に生成。過去分も自然に蓄積・閲覧可能
- **ローカルHTMLファイルなので、Chatworkでは`file:///Users/apple/...`形式のパスを載せる**。ユーザーは自分のMacで開く（他デバイスからは見れない・将来的にホスティング検討）
- 掲載日が読み取れない記事・広告はスキップ（推測禁止）
- 検索クエリの URL変動パラメータ（`utm_*`, `gclid`, `fbclid`, `gad_source` 等）は canonical化してから重複排除。`fetch_listing_apify.py` の canonicalize_url で自動処理済み
- self_exclude_keywords は必ずApify呼び出し時の `exclude_keywords` に渡す（自社案件が"競合の動き"として通知される事故を防ぐ）
- Apifyクレジット切れ（HTTP 402）が出たら通知末尾に警告を出して残りカテゴリで続行
- Google SERPの `url` フィールドは aclk 経由の追跡URLで実際の遷移先ドメインは `displayedUrl` に入る（例: `example.com › パンくず` 形式）。process_paid で handled 済み
- memory.md 追記は Edit で最小差分。既存構造（フロントマター・イベントログ）を壊さない
- 全案件・全種別ゼロの週は Chatwork送信も memory.md 更新もしない（見逃し防止・ログ肥大化防止）
- Chatworkメッセージが長すぎるとき（5000字目安）は案件単位で分割送信
- launchd はシェル環境を継承しないので、Python も `claude` コマンドも絶対パスで指定
- launchd で `claude -p` を使う場合、Claude Code側の認証（`claude auth`）が事前に済んでいる必要あり
- `active_clients.yaml` に登録したのに `competitor_sources.yaml` が無い案件は、Chatwork通知末尾の「⚠️ 設定未整備」に列挙して補完を促す（スキル自体は落ちない）
- PRTimes RSS は `feedparser` で読める `companyrdf.php?company_id=<ID>` エンドポイント。企業IDは各社PRTimesページ（`prtimes.jp/main/html/searchrlp/company_id/<ID>`）のURLから取得

## 関連ファイル

- スクリプト実体: `/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/`
  - `fetch_meta_ads_apify.py` - Meta広告収集（Apify curious_coder Actor）
  - `fetch_listing_apify.py` - リスティングLP収集（Apify apify/google-search-scraper）
  - `fetch_prtimes.py` - PRTimesリリース収集
  - `build_html_report.py` - HTMLレポート生成
  - `send_chatwork.py` - Chatwork送信
  - `dedupe.py` - 通知IDの重複排除履歴管理
  - `resolve_clients.py` - active_clients.yaml→案件別competitor_sources.yaml展開
- HTMLレポート出力先: `/Users/apple/.cursor/work/AI活用/competitor-weekly/reports/YYYY-MM-DD/<案件dir>.html`
- 履歴・ログ: `/Users/apple/.cursor/work/AI活用/competitor-weekly/data/`
- 案件レジストリ: `/Users/apple/.cursor/work/AI活用/competitor-weekly/scripts/active_clients.yaml`
- 案件別探索設定: `/Users/apple/.cursor/work/client/<案件>/competitor_sources.yaml`
- 参考: 広告アップデート週次スキル `/Users/apple/.cursor/skills/ad-update-weekly/SKILL.md`（同様に launchd + Chatwork API 設計）

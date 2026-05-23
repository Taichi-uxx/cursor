# AI-Studio 設計書

マーケティング支援会社の組織体を、複数AIエージェントの並走で再現するシステム。
9つの業務領域を、ディレクター層と専門家層の階層構造で回す。
詳細な組織構成は `組織図.md` を参照。

---

## 0. ひとめでわかるAI-Studio（初見の人向け）

### これは何？
**マーケ業務でやる「制作」「分析」「戦略立案」を、AIエージェントの組織で実行する仕組み**。
人間（田村）は対外CSとして案件をディレクションし、AI組織が制作・分析・戦略をすべて回す。
ツイートで紹介されていた「Claude Code 8体並走」のアイデアを、マーケ支援会社の組織体に拡張したもの。

### 何を解決する？
- **量産の壁**: 1人で4-10社並行は限界 → AI組織が並列でこなす
- **属人化**: 自分の戦略・評価軸をエージェント定義とドメイン知識ファイルに外出し
- **So Whatの欠如**: 数値報告で終わらず、運用ディレクターが「次のアクション」まで踏み込む

### 組織構成（16人 + 案件別ペルソナ3人 = 19ロール）

```
① CMO（兼Strategy Director）
   ├ 戦略チーム（②Market Researcher / ③Customer Analyzer / ④Business Strategist）
   ├ ⑤ Creative Director ─ ⑥Copywriter / ⑦Video Ad Dir / ⑧Banner Conceptor / ⑰FV/アイキャッチ Designer / ⑨LP Architect
   ├ ⑩ Operations Director ─ ⑪Search Ads Spec. / ⑫SNS Ads Spec.
   └ ⑬ Content Director ─ ⑭YouTube Dir / ⑮Short Video Dir / ⑯Scriptwriter

外部リソース: ㉑㉒㉓ Persona A/B/C（案件ごとに差し替え）
```

詳細は `組織図.md`。

### 提供する9つの仕組み

| 種別 | 仕組み | コマンド | 主な召集ロール |
|---|---|---|---|
| 生成 | コピー生成 | `/copy-build` | ①⑤⑥ + ペルソナ3 |
| 生成 | 動画広告構成案 | `/video-ad-build` | ①⑤⑦ + ペルソナ3 |
| 生成 | バナー広告構成案 | `/banner-ad-build` | ①⑤⑧ + ペルソナ3 |
| 生成 | LP（アイキャッチ＋本文構成） | `/lp-build` | ①⑤⑰⑨ + ペルソナ3 |
| 生成 | YouTube構成案＆台本 | `/youtube-build` | ①⑬⑭⑯ + ②⑯ + ペルソナ3 |
| 生成 | ショート動画構成案＆台本 | `/short-video-build` | ①⑬⑮⑯ + ②⑯ + ペルソナ3 |
| 分析 | 検索広告分析＆改善 | `/search-ads-review` | ①⑩⑪ |
| 分析 | SNS広告分析＆改善 | `/sns-ads-review` | ①⑩⑫ |
| 戦略 | マーケティング戦略立案 | `/strategy-build` | ①②③④ |

### 仕組みの正体（3つのパターン）

```
A. 生成パターン（6種）
   CMO戦略確認 → 中間Director → 専門家3案並列 → ペルソナ3評価 → Director採否 → CMO最終QC

B. 分析パターン（2種）
   CMO戦略確認 → 運用Director → 媒体専門家分析 → 運用DirectorがSo What抽出 → CMO最終QC

C. 戦略パターン（1種）
   CMO初期方針 → 戦略チーム3観点並列分析 → CMO統合
```

### 何で動く？
Claude Code の **サブエージェント機能** + **スラッシュコマンド**。MCPもプラグインも追加不要。
ペルソナはクライアント案件ごとに `work/client/<name>/.claude/agents/` で上書きされる。

### 田村が用意するもの
**エージェントの汎用思考力 ≠ 業務固有の知識**。
業界規制／媒体仕様／ベンチマーク数値／勝ちパターン などのドメイン知識を `work/principle/`（精選原則）と `work/knowledge/`（蓄積アーカイブ）の二層構造で田村が用意する（詳細は §5）。

### このドキュメントの読み方
- **§1** 設計思想
- **§2** 全体アーキテクチャ（ディレクトリ構造・3パターン）
- **§3** 組織構成（→ 詳細は `組織図.md`）
- **§4** 9ワークフロー詳細
- **§5** 田村が用意するドメイン知識のマップ ← ★重要
- **§6** クライアント案件ごとの運用ルール
- **§7** 実装フェーズ計画
- **§9** 決定事項（要件確定済み）

### 関連ドキュメント

- `組織図.md` ─ 16人+3ペルソナの組織体の詳細
- `agent-drafts/` ─ 各ロールの agent.md タタキ台
- `01_基盤整備/進捗.md`
- `02_クリエイティブ生成/進捗.md`
- `03_広告運用改善/進捗.md`
- `04_戦略立案/進捗.md`
- `05_動画コンテンツ制作/進捗.md`

---

## 1. 設計思想

| 原則 | 業務との接続 |
|---|---|
| 組織メタファーで構築 | 実在のマーケ支援会社の組織体に近い形 → 田村が直感的にレビューできる |
| ディレクター層が出口を担保 | 質の責任が明確（CDは制作物、運用Dirは数値、CMOは戦略） |
| 専門家は3案並列で出す | 自分は書かず、AIに複数案作らせて選ぶディレクターワークフロー |
| ペルソナは外部リソース | 案件別に差し替え。組織内の固定メンバーではなく「フォーカスグループ」 |
| 中間生成物は進捗ファイル化 | 後で示唆・法則を抽象化する素材 |
| ペルソナは思考過程＋感情リアクション＋スコアを出力 | 「感情を動かす」の評価を可視化 |

---

## 2. 全体アーキテクチャ

### 2.1 ディレクトリ構造

```
~/.claude/
├── agents/                                # 共通プール（17ロール）
│   ├── 01_cmo.md
│   ├── 02_market-researcher.md
│   ├── 03_customer-analyzer.md
│   ├── 04_business-strategist.md
│   ├── 05_creative-director.md
│   ├── 06_copywriter.md
│   ├── 07_video-ad-director.md
│   ├── 08_banner-conceptor.md
│   ├── 09_lp-architect.md
│   ├── 10_operations-director.md
│   ├── 11_search-ads-specialist.md
│   ├── 12_sns-ads-specialist.md
│   ├── 13_content-director.md
│   ├── 14_youtube-director.md
│   ├── 15_short-video-director.md
│   ├── 16_scriptwriter.md
│   └── persona-template.md
│
├── commands/                              # ワークフロー入口
│   ├── copy-build.md
│   ├── video-ad-build.md
│   ├── banner-ad-build.md
│   ├── lp-build.md
│   ├── search-ads-review.md
│   ├── sns-ads-review.md
│   ├── strategy-build.md
│   ├── youtube-build.md
│   └── short-video-build.md
│
└── skills/                                # ドメイン知識スキル（後述）
    ├── copy-rubric/
    ├── ads-frameworks/
    ├── video-hooks/
    └── ...

work/AI-Studio PJT/
├── AI-Studio設計.md                       # 本ファイル
├── 組織図.md                              # 16人+3ペルソナの組織詳細
├── 進捗.md                                # 親PJT全体管理
├── agent-drafts/                          # 各ロールのagent.mdタタキ台（17ファイル）
├── 01_基盤整備/進捗.md
├── 02_クリエイティブ生成/進捗.md
├── 03_広告運用改善/進捗.md
├── 04_戦略立案/進捗.md
└── 05_動画コンテンツ制作/進捗.md

work/principle/                            # ★精選原則層（エージェント常時参照）
├── INDEX.md
├── マーケ戦略/                            # 田村の判断軸/ペルソナ設計/ヒアリング項目
├── マーケ施策/                            # SEO/LLMO/CRM/MA/モール/アフィリエイト
├── 業界知見/                              # 人材/美容/店舗/不動産/クリニック/BtoB/EC
├── 広告運用/                              # Search/Shopping/P-MAX/Dynamic/Meta/TikTok/YDA
├── クリエイティブ/                        # コピー/バナー/LP/動画
└── SNS運用/                               # Instagram/LINE/TikTok/YouTube

work/knowledge/                            # ★蓄積アーカイブ層（雑多に蓄積）
├── INDEX.md
├── マーケ戦略/                            # 戦略系の詳細事例・調査ログ
├── マーケ施策/
├── 業界知見/                              # 業界別の詳細・競合・トレンドログ
├── 広告運用/                              # 媒体別の詳細・月次スナップショット
├── クリエイティブ/                        # 勝ち/負け事例蓄積
├── SNS運用/                               # アルゴリズム観察・バズ事例
└── archive/                               # 古くなったもの・降格したもの

work/client/<クライアント名>/
├── .claude/agents/                        # 案件固有ペルソナ
│   ├── persona-A.md
│   ├── persona-B.md
│   └── persona-C.md
├── strategy.md                            # 案件の戦略MD
└── outputs/                               # 生成物のログ
    └── <date>/<workflow>/
```

### 2.2 3つの基本パターン

#### A. 生成パターン（コピー/動画/バナー/LP/YT/ショート）

```
CMO（①）  戦略確認・キックオフブリーフ
  ↓
中間Director（⑤ or ⑬）  ブリーフを部下に渡す
  ↓
専門家  並列で3案を生成
  ↓
ペルソナ × 3（㉑㉒㉓）  各案を各ペルソナが評価（9評価）
  ↓
中間Director  採点（ルーブリック）と採否判断、必要なら差戻し
  ↓
CMO  最終QC
  ↓
採用案 + 制作経緯ログ
```

#### B. 分析パターン（検索広告/SNS広告）

```
CMO（①）  戦略確認・分析依頼
  ↓
Operations Director（⑩）  分析の観点を専門家に指示
  ↓
媒体専門家（⑪ or ⑫）  数値の構造分析・打ち手の候補出し
  ↓
Operations Director  So What抽出・優先順位付け・改善アクション5つに集約
  ↓
CMO  事業視点での承認・予算配分の調整
  ↓
アクションリスト
```

#### C. 戦略パターン（マーケ戦略立案）

```
CMO（①）  初期方針・ヒアリング情報の整理
  ├ Market Researcher（②）       競合・市場・トレンド
  ├ Customer Analyzer（③）       ペルソナ・ジャーニー
  └ Business Strategist（④）     STP・4P・3C
       並列
  ↓
CMO  統合・優先順位付け
  ↓
3C/STP/4P/90日ロードマップ
```

---

## 3. 組織構成

**17人の常駐スタッフ + 案件別ペルソナ3人 = 計20ロール**。詳細は `組織図.md`。

### 3.1 階層構造サマリー

| 階層 | 人数 | メンバー |
|---|---|---|
| 最上位 | 1人 | ① CMO（兼Strategy Director） |
| 戦略チーム（CMO直下） | 3人 | ②③④ |
| 中間ディレクター | 3人 | ⑤ Creative Director / ⑩ Operations Director / ⑬ Content Director |
| クリエイティブ team（⑤配下） | 5人 | ⑥⑦⑧⑨⑰ |
| 運用 team（⑩配下） | 2人 | ⑪⑫ |
| コンテンツ team（⑬配下） | 3人 | ⑭⑮⑯ |
| **常駐スタッフ計** | **17人** | |
| 外部リソース（案件別） | 3人 | ㉑㉒㉓ Persona A/B/C |

### 3.2 ロール一覧

各ロールの責任と参照すべきドメイン知識：

| # | ロール | 主な責任 | 参照ドメイン知識 |
|---|---|---|---|
| ① | CMO | 戦略・最終QC | frameworks/, industries/ |
| ② | Market Researcher | 競合・市場・トレンドリサーチ | industries/, playbooks/ |
| ③ | Customer Analyzer | ペルソナ・ジャーニー設計 | frameworks/persona.md, frameworks/journey.md |
| ④ | Business Strategist | 3C/STP/4P | frameworks/ |
| ⑤ | Creative Director | 制作物の評価採点と採否 | frameworks/copy-rubric.md |
| ⑥ | Copywriter | コピー18案執筆（6アプローチ×各3案） | principle/クリエイティブ/コピー/, playbooks/copy/, industries/ |
| ⑦ | Video Ad Director | 動画広告構成3案 | playbooks/video/, video-hooks/, platforms/youtube-ads.md他 |
| ⑧ | Banner Conceptor | バナー構成3案 | playbooks/banner/, platforms/banner-specs.md |
| ⑨ | LP Architect | LP本文構成3案（確定FVを与件に地続き設計） | principle/クリエイティブ/LP/ |
| ⑰ | FV/アイキャッチ Designer | FV企画→ビジュアル→実画像（3ゲート・先行） | principle/クリエイティブ/LP/, /バナー/, /媒体別コピー指針.md |
| ⑩ | Operations Director | 数値So What抽出・改善アクション | benchmarks/ |
| ⑪ | Search Ads Specialist | Google+Yahoo広告分析 | platforms/search/ |
| ⑫ | SNS Ads Specialist | Meta+TikTok広告分析 | platforms/meta/, platforms/tiktok/ |
| ⑬ | Content Director | コンテンツ統括・QC | frameworks/ |
| ⑭ | YouTube Director | 長尺動画構成 | playbooks/video/, platforms/youtube.md |
| ⑮ | Short Video Director | 短尺動画構成 | platforms/shorts/, video-hooks/ |
| ⑯ | Scriptwriter | 動画台本3案執筆 | playbooks/video/ |
| ㉑㉒㉓ | Persona A/B/C | ターゲット評価 | （案件固有のペルソナ設定） |

---

## 4. ワークフロー詳細

### 4.1 コピー生成 `/copy-build <URL>`

| 項目 | 内容 |
|---|---|
| 入力 | **LP URL（必須）/ 媒体（必須）** + 案件・商品情報（任意）/ ターゲット情報（任意）。LPはPlaywright取得。媒体別コピー指針で媒体補正。案件にペルソナ無ければ入力から3体自動生成 |
| 召集 | ①CMO → ⑤CD → ⑥Copywriter（6アプローチ×各3案=18案：LP逆算/価値種別/動機心理/勝ちCR要素/良いコピーの型/行動経済学） → ㉑㉒㉓Persona（18案採点） → ⑤CD評価 → ①CMO最終QC = 8体 |
| 出力 | 採用コピー1案 + 差替候補2案 + 制作経緯ログ + ペルソナ別感情リアクション |
| 想定処理時間 | 2〜4分 |
| 主な使いどころ | 入稿前のコピー量産、既存コピーの差替案出し |

### 4.2 動画広告構成案 `/video-ad-build <URL or 商品MD>`

| 項目 | 内容 |
|---|---|
| 入力 | 商品情報＋目的（CV/認知）＋媒体＋秒数 |
| 召集 | ①CMO → ⑤CD → ⑦Video Ad Director（3案：フック型/物語型/比較型） → ㉑㉒㉓Persona → ⑤CD → ①CMO = 8体 |
| 出力 | 秒数別カット割り＋台本（ナレ・テロップ）＋撮影指示 |
| 想定処理時間 | 3〜5分 |
| 主な使いどころ | 動画広告の構成案たたき台、撮影発注前の方向性決め |

### 4.3 バナー広告構成案 `/banner-ad-build <URL>`

| 項目 | 内容 |
|---|---|
| 入力 | 商品/LPのURL＋訴求軸＋媒体サイズ |
| 召集 | ①CMO → ⑤CD → ⑧Banner Conceptor（3案：コピー強/ビジュアル強/数値訴求） → ㉑㉒㉓Persona → ⑤CD → ①CMO = 8体 |
| 出力 | 訴求軸＋レイアウト指示＋コピー＋トーン（実画像は別ステップ） |
| 想定処理時間 | 2〜3分 |
| 主な使いどころ | デザイナー発注前のディレクション資料作成 |

### 4.4 LP（アイキャッチ＋本文構成）`/lp-build <LP URL> 媒体=<媒体>`

**アイキャッチ先行**で進める。⑰がFVを3段階ゲートで確定 → その確定FVを与件に⑨が本文構成 → ⑤が合体整合。一気通貫で一発生成せず、「分けて作り合体させる」のが本ワークフローの設計思想。

| 項目 | 内容 |
|---|---|
| 入力 | **LP URL（必須）/ 媒体（必須）** + 案件・商品情報（任意）/ ターゲット情報（任意）。LPはPlaywright取得。媒体未指定なら停止して確認（/copy-build踏襲） |
| 召集 | ①CMO → ⑤CD → ⑰〔G1 FVコピー企画N案 → ⑤承認 → G2 ビジュアル設計 → ⑤承認 → G3 実画像（生成AI背景KV＋HTML/CSSコピー重ね＋Playwright SP/PC書き出し）〕 → ㉑㉒㉓Persona評価 → ⑤CD採択（確定FV） → ⑨LP Architect（本文構成3案：PASONA/AIDMA/物語型・確定FV制約） → ⑤CD合体整合 → ①CMO最終QC = 11体 |
| 出力 | 確定アイキャッチ（FVコピー＋実画像SP/PC）＋本文セクション構成3案＋CTA設計＋FV合体整合スコア＋不採用理由＋ペルソナ反応 |
| 画像生成 | ハイブリッド＝生成AIで**背景KVのみ**（テキスト無し）生成し、コピー/CTAはHTML/CSSで重ねPlaywrightで書き出し（日本語テキストの正確性を構造的に担保）。**OpenAI(GPT Image)を基本 → エラー時 Gemini(Nano Banana=gemini-3-flash-image)へ自動フォールバック**（既定チェーン `openai,gemini`）。`load_dotenv()`経由、.env直接参照しない |
| 想定処理時間 | 8〜15分（3ゲート＋画像生成＋本文＋合体のため /copy-build より長い。品質優先） |
| 主な使いどころ | 新規LP制作の骨子作り、既存LPのFV刷新＋本文再設計 |
| 前提ブロッカー | OpenAI/Gemini **両方**のキーが `.env` 未設定だとG3が動かない（最低 `OPENAI_API_KEY`、推奨で `GEMINI_API_KEY` も。モデルIDは `OPENAI_IMAGE_MODEL`/`GEMINI_IMAGE_MODEL` で上書き可） |

### 4.5 検索広告分析＆改善提案 `/search-ads-review <CSV path>`

| 項目 | 内容 |
|---|---|
| 入力 | 管理画面CSV または Looker Studio URL |
| 召集 | ①CMO → ⑩Operations Director → ⑪Search Ads Specialist → ⑩運用Dir（So What抽出） → ①CMO = 4体 |
| 出力 | アクションTop5＋根拠数値＋優先順位＋月内ロードマップ |
| 想定処理時間 | 3〜5分 |
| 主な使いどころ | 週次/月次の改善会議前準備、クライアント報告資料の素材 |

### 4.6 SNS広告分析＆改善提案 `/sns-ads-review <CSV path>`

| 項目 | 内容 |
|---|---|
| 入力 | Meta/TikTok管理画面データ＋クリエイティブ一覧 |
| 召集 | ①CMO → ⑩Operations Director → ⑫SNS Ads Specialist → ⑩運用Dir → ①CMO = 4体 |
| 出力 | クリエイティブ次手＋オーディエンス次手＋フリークエンシー診断 |
| 想定処理時間 | 3〜5分 |
| 主な使いどころ | 週次のクリエイティブピボット判断、停滞アカウントの再起動 |

### 4.7 マーケティング戦略立案 `/strategy-build <client>`

| 項目 | 内容 |
|---|---|
| 入力 | ヒアリングシート＋クライアントURL＋競合URL |
| 召集 | ①CMO → ②Market Researcher + ③Customer Analyzer + ④Business Strategist（並列） → ①CMO統合 = 4体 |
| 出力 | 3C／STP／4P／90日ロードマップ＋優先施策3つ |
| 想定処理時間 | 5〜8分 |
| 主な使いどころ | 新規受注時のキックオフ、四半期ごとの戦略見直し |

### 4.8 YouTube動画構成案＆台本 `/youtube-build <theme>`

| 項目 | 内容 |
|---|---|
| 入力 | テーマ＋チャンネル方針＋参考動画URL |
| 召集 | ①CMO → ⑬Content Director → ②Market Researcher（リサーチ招集）+ ⑭YouTube Director + ⑯Scriptwriter（3案） → ㉑㉒㉓Persona → ⑬CD評価 → ①CMO = 9体 |
| 出力 | 10〜15分構成＋完成台本＋サムネ案＋タイトル案5つ |
| 想定処理時間 | 5〜8分 |
| 主な使いどころ | コンテンツ発信用（contents/）の動画制作、クライアントYT運用代行 |

### 4.9 ショート動画構成案＆台本 `/short-video-build <theme>`

| 項目 | 内容 |
|---|---|
| 入力 | テーマ＋媒体（YT Shorts/Reels/TikTok）＋秒数 |
| 召集 | ①CMO → ⑬Content Director → ②Market Researcher + ⑮Short Video Director + ⑯Scriptwriter（3案） → ㉑㉒㉓Persona → ⑬CD → ①CMO = 9体 |
| 出力 | 15〜60秒台本＋1秒フック案×5＋撮影指示 |
| 想定処理時間 | 3〜5分 |
| 主な使いどころ | 世界一周発信用ショート、クライアントSNS運用代行 |

---

## 5. ドメイン知識マップ（田村が用意するもの）

エージェントは「汎用的な思考力」を持つが、業務固有の知識は外から与える必要がある。
**二層構造**で運用する：
- **`work/principle/`** — 精選された原則・鉄則・判断基準（エージェントが常時参照）
- **`work/knowledge/`** — 詳細スペック・生事例・蓄積アーカイブ（必要時に深掘り参照）

両層とも**業務領域ベース**で同じ構成（マーケ戦略 / マーケ施策 / 業界知見 / 広告運用 / クリエイティブ / SNS運用）。
詳細は `work/principle/INDEX.md` と `work/knowledge/INDEX.md` を参照。

### 5.1 principle/ の主要ファイル（精選原則・必須参照）

| カテゴリ | ファイル/フォルダ | 内容 | 主に使うロール | 優先度 |
|---|---|---|---|---|
| マーケ戦略 | `principle/マーケ戦略/田村の判断軸.md` | CLAUDE.md準拠の事業観 | 全ロール | ★★★ |
| マーケ戦略 | `principle/マーケ戦略/ペルソナ設計要点.md` | ペルソナフォーマット | ③ ㉑㉒㉓ ⑯ | ★★★ |
| マーケ戦略 | `principle/マーケ戦略/ヒアリング項目.md` | ヒアリング標準項目 | /strategy-build入力 | ★★★ |
| 業界知見 | `principle/業界知見/<業界>/` | 業界規制・トーン・勝ち型の要点 | ①CMO ⑥⑦⑧⑨ | ★★★ |
| 広告運用 | `principle/広告運用/Search/`, `Shopping/`, `P-MAX/` | 検索広告系の鉄則 | ⑪ | ★★★ |
| 広告運用 | `principle/広告運用/Meta/`, `TikTok/`, `YDA/` | SNS広告系の鉄則 | ⑫ | ★★★ |
| 広告運用 | `principle/広告運用/Dynamic/` | 動的広告の鉄則 | ⑪⑫ | ★★ |
| クリエイティブ | `principle/クリエイティブ/コピー/` | コピー執筆鉄則・採点ルーブリック関連 | ⑤⑥ | ★★★ |
| クリエイティブ | `principle/クリエイティブ/LP/` | LP定石（PASONA/AIDMA/物語型） | ⑨ | ★★★ |
| クリエイティブ | `principle/クリエイティブ/動画/` | 動画構成・フック型 | ⑦⑭⑮⑯ | ★★★ |
| クリエイティブ | `principle/クリエイティブ/バナー/` | バナー鉄則 | ⑧ | ★★ |
| SNS運用 | `principle/SNS運用/{Instagram, LINE, TikTok, YouTube}/` | SNS別運用原則 | ⑬⑭⑮ | ★★★ |
| マーケ施策 | `principle/マーケ施策/{SEO, LLMO, CRM, ...}/` | 施策別の鉄則 | ①④ | ★★ |

### 5.2 knowledge/ の主要カテゴリ（蓄積アーカイブ）

knowledge/ は principle/ と同じ業務領域カテゴリで構成し、**詳細・事例・生データ**を蓄積。

| カテゴリ | 蓄積内容例 | 主に使うロール |
|---|---|---|
| `knowledge/マーケ戦略/` | 過去案件の戦略MD、調査ログ、ペルソナ事例 | ②③④ |
| `knowledge/マーケ施策/` | 施策別の効果実績、参考記事抜粋 | ④ |
| `knowledge/業界知見/<業界>/` | 競合一覧、ケーススタディ、トレンドログ | 全ロール |
| `knowledge/広告運用/<媒体>/` | 媒体仕様の細部、アルゴリズム観察記、月次スナップショット | ⑩⑪⑫ |
| `knowledge/クリエイティブ/<種別>/` | 勝ち/負け事例集、参考スクショ | ⑤⑥⑦⑧⑨ |
| `knowledge/SNS運用/<媒体>/` | アルゴリズム観察、バズ事例 | ⑬⑭⑮ |
| `knowledge/archive/` | 古い情報・principleから降格したもの | 参照少 |

### 5.3 ロール固有原則の格納方針

- **ロール別の「採点ルール」「判断ロジック」「So What抽出手順」は agent.md 内に直書き**
- principle/ の役割は「業務領域別の知識」、エージェントの動作仕様は agent.md 内に統合
- 例: ⑤Creative Director の採点ルール → `work/AI-Studio PJT/agent-drafts/05_creative-director.md` に統合済み

### 5.4 推奨フォーマット

各ドメイン知識ファイルは以下の構造で揃えると、エージェントが解釈しやすい：

```markdown
# <タイトル>

## 概要
（1〜3行で何の知識か）

## 適用条件
（いつ・どの案件で使うか）

## 本体
（知識の中身。表・箇条書き推奨）

## 使用例
（ロールがどう使うかの例）

## 出典・参考
（あれば）
```

### 5.5 用意の優先順位

**Week 1（最優先 ★★★）**:
1. `principle/マーケ戦略/田村の判断軸.md` — 全ロール参照（雛型済）
2. `principle/マーケ戦略/ペルソナ設計要点.md` — ③Customer Analyzer 参照（雛型済）
3. `principle/マーケ戦略/ヒアリング項目.md` — /strategy-build 入力（雛型済）
4. `principle/業界知見/<主要1業界>/` — まず1業界の鉄則
5. `principle/広告運用/Search/` — ⑪Search Ads Specialist が参照

**Week 2-3（★★）**:
6. `principle/業界知見/` を担当業界ぶん拡張
7. `principle/クリエイティブ/LP/` — LP定石
8. `principle/クリエイティブ/動画/` — 動画フック型
9. `principle/広告運用/Meta/`, `principle/広告運用/TikTok/`, `principle/SNS運用/` を順次

**運用しながら（★）**:
- `knowledge/` 配下を実案件のたびに追記
- 月次レビューで `knowledge/` → `principle/` への昇格候補を抽出

---

## 6. クライアント別カスタマイズ運用ルール

### 6.1 新規案件起動フロー

```
1. work/client/<クライアント名>/ を作成
2. /strategy-build <クライアント名> 実行（①→②③④）
   → strategy.md が生成される
3. strategy.md から③Customer Analyzerがペルソナ3体を派生
   → work/client/<name>/.claude/agents/persona-A.md, B.md, C.md に配置
4. 以降、その案件で生成系ワークフローを叩くと自動でそのペルソナで評価される
```

### 6.2 ペルソナの上書き優先順

Claude Code のサブエージェント探索順：
1. プロジェクト直下の `.claude/agents/` （案件固有ペルソナ、最優先）
2. ユーザー全体の `~/.claude/agents/` （共通プール）

つまり、`work/client/<name>/.claude/agents/persona-A.md` を置けば、その案件では `persona-template.md` ではなくそのペルソナが使われる。

### 6.3 ログ運用

各ワークフロー実行時、中間生成物を `work/client/<name>/outputs/<date>/<workflow>/` に保存：
- `01_cmo-brief.md` （CMOのキックオフブリーフ）
- `02_director-instruction.md` （中間ディレクターの指示）
- `03_drafts/<specialist>-1.md`, `-2.md`, `-3.md` （3案）
- `04_persona-evaluations.md`
- `05_director-decision.md` （中間ディレクターの採否）
- `06_final.md` （CMO最終確認後）
- `99_log.md` （ロール間のやりとりログ）

→ 後で「どの専門家の出力が勝率高いか」「どのペルソナの指摘が的中するか」を抽象化するための素材。

---

## 7. 実装フェーズ計画

| Phase | 内容 | 所要 | 田村のタスク |
|---|---|---|---|
| Phase 0 | ドメイン知識 ★★★ を用意 | 田村が3〜5日 | §5.4のWeek1リスト |
| Phase 1 | 16ロールの agent.md 実装＋ペルソナテンプレ | AIが1〜2日 | agent-drafts/をレビューしOK出し |
| Phase 2 | 9ワークフローのコマンド実装 | AIが半日 × 9 | 1つずつ実案件で検証 |
| Phase 3 | 運用しながらドメイン知識★★追加、playbooks蓄積 | 継続 | 案件ごとに追記 |
| Phase 4 | ログから「示唆・法則」抽出、エージェントをチューニング | 月次 | レビューと改善指示 |

---

## 8. 想定される拡張

- **MCP連携**: Looker Studio MCP / Notion MCP で入力収集と出力配置を自動化
- **画像生成連携**: ⑧Banner Conceptorの出力から Midjourney / Nano Banana に接続し、画像までワンショット生成
- **Slack通知**: ワークフロー完了をSlack通知（hooksで実装）
- **A/Bテスト自動設計**: コピー/バナーで「迷い案」を残し、ABテスト案として自動出力
- **ロール拡張**: 案件規模に応じてYahoo広告専門/動画スクリプター特化など追加可能

---

## 9. 決定事項（要件確定済み）

| 項目 | 決定内容 | 補足 |
|---|---|---|
| ペルソナ数 | **3体固定**（A/B/C） | 案件横断で比較しやすい。案件にペルソナ/ターゲット情報が無い場合は、③Customer Analyzerが実行時に入力（LP/商品情報）から3体を自動生成して評価ループに供給（/copy-build等の生成WF共通） |
| 専門家の案数 | **原則3案固定**（動画/バナー/台本）<br>**⑥Copywriterのみ6アプローチ×各3案=18案**（例外）<br>**LPは⑰アイキャッチ先行＋⑨本文構成3案の分離フロー**（例外） | ライター×ペルソナ×CD三層を踏襲。LPはFV(⑰)を3ゲートで先行確定し、その制約下で本文(⑨)3案＝§4.4 |
| ループ許容回数 | **最大3回**まで差戻し可 | 3回でスコア閾値到達しなければ最高点案を「条件付き採用」としてCMOに上げる |
| スコア閾値 | **80点**（100点満点換算） | ⑤CD評価ルーブリック5軸×5点=25点 → 100点換算で80以上が採用ライン |
| 分析系入力フォーマット | **CSVメイン** | 将来的にMCPで媒体データ直接参照（Looker Studio/Meta/Google Ads等）を追加予定 |
| CMO最終QC判断軸 | **① 期待値プラス**（成功確率×売上インパクト − 失敗確率×損失インパクト > 0）<br>**② 戦略マッチ度 80%超** | 両方を満たさなければ差戻し |
| ショート動画媒体差分の管理方針 | **`knowledge/` 内のフォルダ分けで管理**（`platforms/shorts/youtube-shorts/` `reels/` `tiktok/`） | 媒体別の詳細スペック・アルゴリズム特性・成功事例を分けて蓄積 |
| LP生成方式 | **アイキャッチ(⑰)先行 → 本文構成(⑨)を確定FV制約下で設計 → ⑤合体**（一発生成しない） | FVと本文は別ゲーム（LP本質①FV3秒勝負 vs ②物語温度）。分離でFVを独立変数化でき切り分け改善が効く。新ロール⑰新設（常駐17・計20ロール） |
| LPアイキャッチ画像方式 | **ハイブリッド＝生成AI背景KV（テキスト無し）＋HTML/CSSコピー重ね＋Playwright SP/PC書き出し**。生成は **OpenAI(GPT Image)基本 → エラー時 Gemini(Nano Banana=gemini-3-flash-image)自動代替**（既定チェーン `openai,gemini`） | 生成AI一枚絵は日本語テキストが崩れCVを毀損するため。プロバイダ非依存ラッパーで`load_dotenv()`参照（.env直接参照禁止）。両キー未設定/両API失敗のときのみG3ブロック |

### CMO最終QC判断ロジック（詳細）

```
判断軸①: 期待値プラス
  期待値 = (成功確率 × 想定売上インパクト) − (失敗確率 × 想定損失インパクト)
  → 期待値 ≤ 0 → 却下（事業視点で採算合わない）

判断軸②: 戦略マッチ度
  戦略MDに記載された方向性（誰に/何を/どのKPI）との一致度を0-100%で評価
  → 80%未満 → 差戻し（戦略軸に戻すよう指示）

両方クリア → ✅ 採用
片方でも不足 → 🔄 差戻し or ❌ 却下
```

### ⑤Creative Director採点と差戻しロジック（詳細）

```
1. 専門家の全案を5軸×5点満点で採点（コピー=18案〔6アプローチ×3案〕 / 動画・バナー・LP・台本=3案）→ 各案 25点満点
2. 100点換算（×4）
3. 採否判定:
   - 最高点案が80点以上 → ✅ 採用 → CMOへ
   - 全案80点未満 → 🔄 差戻し（具体的改善指示つき）→ 再生成
4. ループ管理:
   - 最大3回まで再生成
   - 3回後も全案80点未満 → 最高点案を「⚠️条件付き採用」としてCMOに上げる
     CMOが戦略マッチ度＋期待値で最終判定
```

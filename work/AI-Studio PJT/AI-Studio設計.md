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
   ├ ⑤ Creative Director ─ ⑥Copywriter / ⑦Video Ad Dir / ⑧Banner Conceptor / ⑨LP Architect
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
| 生成 | LP構成案 | `/lp-build` | ①⑤⑨ + ペルソナ3 |
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
業界規制／媒体仕様／ベンチマーク数値／勝ちパターン などのドメイン知識を `work/AI活用/knowledge/` に田村が用意する（詳細は §5）。

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
├── agents/                                # 共通プール（16ロール）
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
├── agent-drafts/                          # 各ロールのagent.mdタタキ台
├── 01_基盤整備/進捗.md
├── 02_クリエイティブ生成/進捗.md
├── 03_広告運用改善/進捗.md
├── 04_戦略立案/進捗.md
└── 05_動画コンテンツ制作/進捗.md

work/AI活用/knowledge/                     # ドメイン知識ベース（田村が用意）
├── industries/                            # 業界別知識
├── platforms/                             # 媒体仕様
├── benchmarks/                            # 数値ベンチマーク
├── frameworks/                            # フレームワーク集
├── playbooks/                             # 勝ちパターン集
└── templates/                             # ヒアリングシート等

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

**16人の常駐スタッフ + 案件別ペルソナ3人 = 計19ロール**。詳細は `組織図.md`。

### 3.1 階層構造サマリー

| 階層 | 人数 | メンバー |
|---|---|---|
| 最上位 | 1人 | ① CMO（兼Strategy Director） |
| 戦略チーム（CMO直下） | 3人 | ②③④ |
| 中間ディレクター | 3人 | ⑤ Creative Director / ⑩ Operations Director / ⑬ Content Director |
| クリエイティブ team（⑤配下） | 4人 | ⑥⑦⑧⑨ |
| 運用 team（⑩配下） | 2人 | ⑪⑫ |
| コンテンツ team（⑬配下） | 3人 | ⑭⑮⑯ |
| **常駐スタッフ計** | **16人** | |
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
| ⑥ | Copywriter | コピー3案執筆 | playbooks/copy/, industries/ |
| ⑦ | Video Ad Director | 動画広告構成3案 | playbooks/video/, video-hooks/, platforms/youtube-ads.md他 |
| ⑧ | Banner Conceptor | バナー構成3案 | playbooks/banner/, platforms/banner-specs.md |
| ⑨ | LP Architect | LP構成3案 | playbooks/lp/, frameworks/lp-patterns.md |
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
| 入力 | 商品/LPのURL（または商品MD） |
| 召集 | ①CMO → ⑤CD → ⑥Copywriter（3案並列） → ㉑㉒㉓Persona → ⑤CD評価 → ①CMO最終QC = 8体 |
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

### 4.4 LP構成案 `/lp-build <URL>`

| 項目 | 内容 |
|---|---|
| 入力 | 商品/サービスURL＋ゴール |
| 召集 | ①CMO → ⑤CD → ⑨LP Architect（3案：PASONA/AIDMA/物語型） → ㉑㉒㉓Persona → ⑤CD → ①CMO = 8体 |
| 出力 | セクション構成＋各セクションコピー骨子＋CTA設計＋ファーストビュー案 |
| 想定処理時間 | 4〜6分 |
| 主な使いどころ | 新規LP制作の骨子作り、既存LPの改善提案 |

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
以下のファイル/フォルダを `work/AI活用/knowledge/` 配下に田村が用意する。
各エージェントは agent.md 内で `@work/AI活用/knowledge/...` の形で参照する。

### 5.1 必須のドメイン知識（最初に揃える）

| カテゴリ | ファイル/フォルダ | 内容 | 主に使うロール | 優先度 |
|---|---|---|---|---|
| 業界別知識 | `industries/<業界名>.md` | 業界規制（薬機法/景表法/金商法等）、トーン、訴求NG事項、専門用語 | ①CMO ⑥⑦⑧⑨ | ★★★ |
| 媒体仕様（検索） | `platforms/search/google-ads.md`, `yahoo-ads.md` | 入稿規定、品質スコア改善定石、自動入札 | ⑪ | ★★★ |
| 媒体仕様（SNS） | `platforms/meta/`, `platforms/tiktok/` | ピクセル/オーディエンス/CBO・ABO/クリエイティブ規定 | ⑫ | ★★★ |
| 媒体仕様（動画） | `platforms/youtube-ads.md`, `meta-video.md`, `tiktok-ads.md` | 秒数規定、アスペクト比、スキッパブル等 | ⑦⑭ | ★★★ |
| 媒体仕様（バナー） | `platforms/banner-specs.md` | GDN/YDN/Metaサイズ別仕様、FV要件 | ⑧ | ★★ |
| 媒体仕様（ショート） | `platforms/shorts/youtube-shorts.md`, `reels.md`, `tiktok.md` | アルゴリズム特性、推奨秒数 | ⑮ | ★★★ |
| 業界ベンチマーク数値 | `benchmarks/<業界>_<媒体>.md` | 業界×媒体の平均CPC/CPM/CVR/CPA | ⑩⑪⑫ | ★★★ |
| コピー評価ルーブリック | `frameworks/copy-rubric.md` | 5段階評価軸（自分ごと化/便益明示/具体性/独自性/CTA強度等） | ⑤ | ★★★ |
| LP定石パターン | `frameworks/lp-patterns.md` | PASONA/AIDMA/QUEST/物語型 | ⑨ | ★★ |
| 動画フック型集 | `video-hooks/hooks.md` | 1秒/3秒フック型 | ⑦⑮ | ★★ |
| ヒアリングシート | `templates/hearing-sheet.md` | 新規受注時のヒアリング項目 | /strategy-build入力 | ★★★ |
| ペルソナ作成テンプレ | `frameworks/persona.md` | ペルソナのフォーマット | ③ | ★★★ |
| カスタマージャーニー | `frameworks/journey.md` | フェーズ別の設計フォーマット | ③ | ★★ |

### 5.2 蓄積していくドメイン知識（運用しながら育てる）

| カテゴリ | ファイル/フォルダ | 内容 | 主に使うロール | 優先度 |
|---|---|---|---|---|
| 勝ちパターン（コピー） | `playbooks/copy/<業界>.md` | 過去の勝ちコピー＋負け＋分析 | ⑥⑤ | ★★ |
| 勝ちパターン（LP） | `playbooks/lp/<業界>.md` | CVR高いLPの構成分析 | ⑨ | ★★ |
| 勝ちパターン（動画） | `playbooks/video/<業界>.md` | バズ動画/CV取れた動画分析 | ⑦⑭⑮ | ★★ |
| 勝ちパターン（バナー） | `playbooks/banner/<業界>.md` | CTR高いバナーの分析 | ⑧ | ★ |
| 失敗パターン集 | `playbooks/anti-patterns.md` | やってはいけない訴求/表現/媒体運用ミス | 全ロール | ★★ |
| 競合データベース | `industries/<業界>/competitors.md` | 主要競合の戦略/クリエイティブ/価格 | ②④ | ★ |
| クライアント別過去案件 | `work/client/<name>/history.md` | 過去のクリエイティブ・成果データ | 全ロール（案件起動時） | ★★ |

### 5.3 推奨フォーマット

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

### 5.4 用意の優先順位

**Week 1（最優先 ★★★）**:
1. `frameworks/copy-rubric.md` — ⑤Creative Director が参照
2. `frameworks/persona.md` — ③Customer Analyzer が参照
3. `templates/hearing-sheet.md` — /strategy-build入力テンプレ
4. `industries/<主要1業界>.md` — まず1業界
5. `platforms/search/google-ads.md` — ⑪Search Ads Specialist が参照

**Week 2-3（★★）**:
6. `benchmarks/<主要業界>_<主要媒体>.md`
7. `frameworks/lp-patterns.md`
8. `video-hooks/hooks.md`
9. 他の `platforms/` を順次

**運用しながら（★）**:
- `playbooks/` 配下を実案件のたびに追記
- `industries/` を担当業界ぶん拡張

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
| ペルソナ数 | **3体固定**（A/B/C） | 案件横断で比較しやすい |
| 専門家の案数 | **3案固定** | ライター×ペルソナ×CD三層を踏襲 |
| ループ許容回数 | **最大3回**まで差戻し可 | 3回でスコア閾値到達しなければ最高点案を「条件付き採用」としてCMOに上げる |
| スコア閾値 | **80点**（100点満点換算） | ⑤CD評価ルーブリック5軸×5点=25点 → 100点換算で80以上が採用ライン |
| 分析系入力フォーマット | **CSVメイン** | 将来的にMCPで媒体データ直接参照（Looker Studio/Meta/Google Ads等）を追加予定 |
| CMO最終QC判断軸 | **① 期待値プラス**（成功確率×売上インパクト − 失敗確率×損失インパクト > 0）<br>**② 戦略マッチ度 80%超** | 両方を満たさなければ差戻し |
| ショート動画媒体差分の管理方針 | **`knowledge/` 内のフォルダ分けで管理**（`platforms/shorts/youtube-shorts/` `reels/` `tiktok/`） | 媒体別の詳細スペック・アルゴリズム特性・成功事例を分けて蓄積 |

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
1. 専門家3案を5軸×5点満点で採点 → 各案 25点満点
2. 100点換算（×4）
3. 採否判定:
   - 最高点案が80点以上 → ✅ 採用 → CMOへ
   - 全案80点未満 → 🔄 差戻し（具体的改善指示つき）→ 再生成
4. ループ管理:
   - 最大3回まで再生成
   - 3回後も全案80点未満 → 最高点案を「⚠️条件付き採用」としてCMOに上げる
     CMOが戦略マッチ度＋期待値で最終判定
```

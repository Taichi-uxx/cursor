# AIニュース取得＋投稿文作成 ワークフロー解説

## 概要

AI関連ニュースを自動収集し、X（旧Twitter）用の投稿文を生成するn8nワークフロー。毎日自動実行され、記事の選別から投稿文作成までを自動化する。

## 実際のワークフロー
https://kota-rehatch.app.n8n.cloud/workflow/lhfMwsk5a0cWEb7s
参考：https://rehatchhq.slack.com/archives/C05LGGA3MG9/p1755477775567549

## ワークフロー構成

### 処理フロー

```
定時実行（9時）
    ↓
[並列] 10個のRSS取得
    ↓
[並列] 10個のFilter Fields（データ整形）
    ↓
Merge All Sources（統合）
    ↓
Filter by Datetime（24時間以内）
    ↓
Remove Non-AI Content（AI関連のみ）
    ↓
Aggregate（配列化）
    ├→ News Analyzer（AI選別）→ Post Creator（投稿文生成）→ Slack通知
    │                                                          ↓
    │                                                   厳選記事データ整形
    │                                                          ↓
    │                                                   厳選記事をシートに保存
    │
    └→ 全記事配列を個別行に分割
            ↓
        全記事データ整形
            ↓
        全記事をシートに保存
```

## 各フェーズの詳細

### 1. トリガー：定時実行

- **ノード名**: 定時実行（毎日朝8時）
- **実行タイミング**: 毎日朝9時（設定値とノード名に不一致あり）
- **タイプ**: Cronトリガー

### 2. 記事取得フェーズ

10個のRSSフィードから並列で記事を取得する。

#### 取得ソース一覧

1. **ITmedia** - 日本語技術メディア
2. **TechCrunch AI** - 英語AI専門メディア
3. **日経クロステック** - 日本語技術メディア
4. **WIRED AI** - 英語AI記事
5. **AI News** - AI専門ニュースサイト
6. **OpenAI Blog** - 公式ブログ
7. **Google AI Blog** - 公式ブログ
8. **Google News 日本語AI** - 日本語AI検索結果
9. **Google News 英語AI** - 英語AI検索結果
10. **Google News 企業別AI** - 主要AI企業検索結果

#### エラーハンドリング

各RSS取得ノードは以下の設定により、エラー時も処理を継続する：
- `alwaysOutputData: true`
- `onError: "continueRegularOutput"`

### 3. データ整形フェーズ

各ソースの記事データを統一フォーマットに変換する。

#### 抽出フィールド

- `title`: 記事タイトル
- `pubDate`: 公開日時
- `link`: 記事URL
- `content`: 本文（`contentSnippet` → `content` → `summary` の順で取得）
- `source`: ソース名（各Filter Fieldsで固定値として設定）

### 4. マージフェーズ

10個のソースから取得したデータを1つのストリームに統合する。

- **ノード名**: Merge All Sources
- **入力数**: 10

### 5. フィルタリングフェーズ

#### 5-1. 日付フィルタ

- **ノード名**: Filter by Datetime
- **条件**: 公開日が昨日以降（24時間以内の記事のみ通過）
- **実装**: `$today.minus({ days: 1 })` を使用

#### 5-2. AI関連コンテンツフィルタ

- **ノード名**: Remove Non-AI Content
- **条件**:
  - タイトルにAI関連キーワードを含む（正規表現マッチ）
  - 本文が空でない
- **キーワード**: `(AI|artificial intelligence|machine learning|deep learning|ChatGPT|OpenAI|Claude|Anthropic|Gemini|GPT|LLM|人工知能|機械学習|生成AI|ディープラーニング)`

### 6. 集約フェーズ

複数の記事を1つのアイテムに集約し、各フィールドを配列形式に変換する。

- **ノード名**: Aggregate
- **集約フィールド**: title, pubDate, link, content, source

### 7. AI分析フェーズ（記事選別）

#### 設定

- **ノード名**: News Analyzer
- **使用モデル**: Claude Sonnet 4.5
- **Temperature**: 0.7
- **出力形式**: JSON（構造化出力パーサー使用）

#### 選別基準（優先順位順）

1. **情報の新鮮度** - 直近24-48時間以内の記事を最優先
2. **革新性・注目度の高さ** - 業界への影響度
3. **記事の信頼性** - 公式ブログ、大手メディア優先
4. **実用性・ビジネスインパクト** - 実際の活用可能性
5. **読者への価値提供度** - SNSでの反応見込み

#### 必須条件

- 掲載日時が2024年12月以降の記事のみ選択
- 古い記事（2024年11月以前）は除外
- 日付不明の記事も除外

#### 出力フォーマット

```json
{
  "selectedArticles": [
    {
      "title": "記事タイトル",
      "url": "記事URL",
      "source": "メディア名",
      "published_date": "掲載日時",
      "selectionReason": "選択理由（新鮮度を含む）"
    }
  ],
  "selectionSummary": "選別の総括（最新性重視の説明）"
}
```

### 8. 投稿文生成フェーズ

#### 設定

- **ノード名**: Post Creator
- **使用モデル**: Claude Sonnet 4.5
- **Temperature**: 0.8（より創造的な出力のため）

#### 投稿パターン

記事の内容に応じて以下の3パターンから選択：

- **パターンA: 技術紹介型** - 新技術発表/企業発表
- **パターンB: 体験談型** - ツール体験/実用的内容
- **パターンC: 解説型** - Tips/ハウツー系

#### 出力要件

- 500文字以内
- 絵文字1-2個
- 改行で読みやすく構成
- 人間らしい自然な文章

#### 出力フォーマット

```
【記事1】
投稿文
[選択したパターンに基づく自然な投稿文]
参考記事: [記事タイトル]
掲載メディア: [メディア名]
掲載日時: [掲載日時]
URL: [記事URL]

【記事2】
...

【記事3】
...
```

### 9. 通知フェーズ

- **ノード名**: Slack通知（投稿文のみ）
- **送信先**: 指定Slackチャンネル（チャンネルID: C09A3G1SLJ1）
- **通知内容**: 生成された投稿文
- **メンション**: 特定ユーザー（U05136SA1FS）にメンション付き

### 10. データ保存フェーズ

#### 10-1. 全記事の保存

- **処理**: Aggregateノードから来た配列データを個別の記事アイテムに変換
- **保存先**: Googleシート「全記事ログ」シート
- **保存項目**:
  - 実行日時
  - 記事番号
  - 記事タイトル
  - メディア名
  - 掲載日時
  - URL
  - 記事内容
  - 内容文字数

#### 10-2. 厳選記事の保存

- **保存先**: Googleシート「厳選記事+投稿文」シート
- **保存項目**:
  - 実行日時
  - 厳選記事JSON
  - 選別サマリ
  - 生成投稿文
  - 厳選記事数
  - 記事1〜3の詳細情報（タイトル、メディア、URL、掲載日時、選択理由）

## ワークフローの特徴

### 強み

1. **並列処理**: 10個のソースを同時に取得し、処理時間を短縮
2. **エラーハンドリング**: 一部のソースが失敗しても処理を継続
3. **多段階フィルタリング**: 日付、AI関連、内容の有無で段階的に絞り込み
4. **AI活用**: Claude Sonnet 4.5を使用した高品質な記事選別と投稿文生成
5. **データ蓄積**: 全記事と厳選記事をGoogleシートに保存し、履歴管理

### 改善ポイント

1. **日付フィルタの固定値**: 2024年12月以降の条件がハードコードされている（現在は2025年）
2. **実行時間の不一致**: ノード名は「8時」だが実際の設定は9時

## 技術仕様

### 使用ノードタイプ

- `n8n-nodes-base.cron`: 定時実行
- `n8n-nodes-base.rssFeedRead`: RSS取得
- `n8n-nodes-base.set`: データ整形
- `n8n-nodes-base.merge`: データ統合
- `n8n-nodes-base.filter`: フィルタリング
- `n8n-nodes-base.aggregate`: データ集約
- `@n8n/n8n-nodes-langchain.agent`: AIエージェント
- `@n8n/n8n-nodes-langchain.lmChatAnthropic`: Claude API連携
- `@n8n/n8n-nodes-langchain.outputParserStructured`: JSON出力パーサー
- `n8n-nodes-base.slack`: Slack通知
- `n8n-nodes-base.code`: JavaScriptコード実行
- `n8n-nodes-base.googleSheets`: Googleシート連携

### 認証情報

- **Anthropic API**: Claude Sonnet 4.5使用
- **Slack API**: チャンネル通知用
- **Google Sheets OAuth2**: データ保存用

## データフロー

1. **入力**: 10個のRSSフィード
2. **処理**: フィルタリング → 集約 → AI分析 → 投稿文生成
3. **出力**: 
   - Slack通知（投稿文）
   - Googleシート（全記事ログ、厳選記事+投稿文）

## 実行頻度

- **スケジュール**: 毎日朝9時
- **現在の状態**: 非アクティブ（`active: false`）


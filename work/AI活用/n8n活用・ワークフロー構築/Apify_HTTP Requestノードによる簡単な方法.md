# n8nでApifyを使用する最も簡単な方法

## 概要

n8nのHTTP Requestノードを使用してApifyからデータをスクレイピングする最もシンプルな方法。わずか2つのノード（HTTP Request + Split Out）で実現可能。

**動画URL**: https://www.youtube.com/watch?v=rlgrHhNafNU

## 使用ツール

- **n8n**: ワークフロー自動化プラットフォーム
- **Apify**: スクレイピングプラットフォーム
- **Google Sheets**: データエクスポート先（オプション）

## ワークフロー全体の流れ

1. Manual Triggerでワークフローを開始
2. HTTP RequestノードでApify APIを呼び出し
3. Split Outノードでデータを整形
4. Google Sheetsに出力（オプション）

## 各ステップの詳細

### 1. Apifyアカウントの準備

1. Apifyアカウントを作成
2. 使用したいスクレイパーを検索・選択（例: Google Maps extractor）
3. スクレイパーの設定を定義（入力パラメータを設定）

### 2. APIエンドポイントの取得

1. Apifyのスクレイパーページで「Integrations」をクリック
2. 「Add integration」をクリック
3. 「Use API endpoints」を選択
4. 「Run actor synchronously and get dataset items」を選択
5. 表示されたURLをコピー

**特徴**:
- APIトークンがURLに含まれているため、手動で認証設定を行う必要がない
- 1つのエンドポイントでアクターの実行とデータセットの取得を同時に行う

### 3. HTTP Requestノードの設定

#### 基本設定

- **ノード**: HTTP Request
- **Method**: POST
- **URL**: ApifyからコピーしたAPIエンドポイント（APIトークンが含まれている）

#### リクエストボディ

- **Content Type**: JSON
- **Body**: ApifyのInputタブから取得したJSONをそのまま使用

**JSON取得方法**:
1. Apifyのスクレイパーページで「Input」タブを開く
2. 「JSON」タブを選択
3. 設定したパラメータのJSONをコピー
4. HTTP RequestノードのBodyに貼り付け

### 4. Split Outノードでデータ整形

- **ノード**: Split Out
- **設定**:
  - **Split by field**: データの配列を分割するフィールドを指定（例: `title`）
  - **Include selected fields**: 必要なフィールドのみ選択

**選択可能なフィールド例**:
- `address`: 住所
- `city`: 都市
- `website`: ウェブサイト
- `phoneUnformatted`: 電話番号（未フォーマット、後続処理に便利）
- `totalScore`: 総合スコア

**出力**: 各アイテムが個別の配列要素として出力される

### 5. Google Sheetsへの出力（オプション）

- **ノード**: Google Sheets - Append Row
- **設定**:
  - **Spreadsheet**: 対象のスプレッドシート名（例: "leads from Automation"）
  - **Sheet**: シート名（例: "Sheet1"）
  - **Fields**: Split Outで取得したフィールドをマッピング
    - `title` → ビジネス名
    - `address` → 住所
    - `city` → 都市
    - `website` → ウェブサイト
    - `phoneUnformatted` → 電話番号
    - `totalScore` → 総合スコア

## この方法の特徴

### メリット

1. **シンプル**: わずか2つのノードで実現可能
2. **認証不要**: APIトークンがURLに含まれているため、手動で認証設定が不要
3. **1つのエンドポイント**: アクターの実行とデータ取得を1つのリクエストで完了
4. **汎用性**: どのApifyスクレイパーでも同じ方法で使用可能

### 他の方法との比較

**ネイティブApifyノードを使用する方法**:
- より多くのノードが必要（Run Actor + Get Dataset Items）
- 設定がより詳細
- エラーハンドリングが改善

**HTTP Requestを使用する方法（本方法）**:
- 最小限のノード数
- 設定が簡単
- 1つのリクエストで完了

## 使用例

### Google Maps Extractorの例

**入力パラメータ例**:
```json
{
  "searchQuery": "roofers in Boston",
  "maxCrawledPlaces": 5
}
```

**出力結果**:
- ボストンの屋根工事業者5件の情報を取得
- 各事業者の詳細情報（名前、住所、電話番号、ウェブサイト等）

## 注意点

1. **APIトークンの管理**: URLにAPIトークンが含まれているため、セキュリティに注意
2. **レート制限**: Apifyのプランに応じたレート制限がある
3. **データ形式**: スクレイパーによって出力データの形式が異なるため、Split Outの設定を調整
4. **電話番号のフォーマット**: `phoneUnformatted`を使用することで、後続の処理（電話番号の検証、フォーマット等）が容易

## 拡張可能性

1. **複数のスクレイパー**: 同じワークフローで複数のApifyスクレイパーを連続実行
2. **データ処理**: Split Outの後に追加のデータ処理ノードを配置
3. **条件分岐**: 取得したデータに基づいて異なる処理に分岐
4. **複数の出力先**: Google Sheets以外にも、データベースやCRMへの連携が可能

## ワークフロー構成のポイント

1. **最小限のノード**: HTTP RequestとSplit Outの2ノードで基本機能を実現
2. **データの整形**: Split Outで必要なフィールドのみ抽出し、後続処理を簡素化
3. **柔軟性**: どのApifyスクレイパーでも同じパターンで使用可能

## 関連リソース

- **Apifyストア**: 様々なスクレイパーが利用可能
- **Apify APIドキュメント**: APIエンドポイントの詳細情報
- **n8n HTTP Requestノード**: n8nのHTTP Requestノードのドキュメント


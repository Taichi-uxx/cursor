# n8nとApifyを使用したInstagramスクレイピングワークフロー

## 概要

n8nとApifyを使用して、Instagramのハッシュタグから投稿をスクレイピングし、投稿者のアカウント情報を取得してGoogleスプレッドシートにエクスポートするワークフロー。

**動画URL**: https://www.youtube.com/watch?v=h2qIGkkCzdg

## 使用ツール

- **n8n**: ワークフロー自動化プラットフォーム
- **Apify**: スクレイピングアクター（2種類）
  - Instagram Hashtag Scraper
  - Instagram Profile Scraper
- **Google Sheets**: データエクスポート先

## ワークフロー全体の流れ

1. フォームからハッシュタグを入力
2. ハッシュタグに関連する投稿をスクレイピング
3. 投稿データからフィールドを編集（ユーザー名のみ抽出）
4. ユーザー名をフォーマット（リスト形式に変換）
5. Instagramプロフィール情報をスクレイピング
6. 必要なフィールドのみ抽出（ユーザー名、バイオ、フォロワー数、非公開アカウント判定）
7. フィルター適用（フォロワー数500以上、非公開アカウント除外）
8. Googleスプレッドシートに追加

## 各ステップの詳細

### 1. フォームトリガー

- **ノード**: Form Trigger
- **設定**: 
  - フォーム名: "Instagram profiles per hashtag"
  - フィールド: ハッシュタグ（テキスト入力）
- **出力**: ハッシュタグのJSONデータ

### 2. Apifyアクターの実行（ハッシュタグスクレイピング）

#### 2-1. Run Actor

- **ノード**: Apify - Run Actor
- **設定方法**:
  1. ApifyアカウントでAPIキーを取得（Settings → API integrations）
  2. n8nの設定でApify APIキーを登録
  3. アクターURLを指定（console.apify.com/actors/...）
  4. 入力JSONを設定
- **入力JSON例**:
```json
{
  "hashtags": ["#sportscards"]
}
```
- **注意**: 複数のハッシュタグを同時に実行可能（カンマ区切り）

#### 2-2. Get Dataset Items

- **ノード**: Apify - Get Dataset Items
- **設定**: 
  - Default Dataset ID: Run Actorの出力から取得
- **出力**: ハッシュタグに関連する投稿データ

### 3. フィールド編集

- **ノード**: Edit Fields
- **抽出フィールド**: 
  - `owner.username`（投稿者のユーザー名）
- **理由**: 投稿内容やキャプションは不要なため、ユーザー名のみ抽出

### 4. ユーザー名のフォーマット

- **ノード**: Code (Python)
- **処理内容**: ユーザー名のリストをカンマ区切りの文字列に変換
- **コード例**:
```python
usernames = [item['username'] for item in $input.all()]
return [{'usernames': ','.join(usernames)}]
```
- **注意**: 重複するユーザー名が存在する可能性があるため、将来的にはユニーク化処理を追加推奨

### 5. Apifyアクターの実行（プロフィールスクレイピング）

#### 5-1. Run Actor

- **ノード**: Apify - Run Actor
- **アクター**: Instagram Profile Scraper
- **入力JSON**:
```json
{
  "usernames": "username1,username2,username3,..."
}
```
- **設定**: "Wait to finish"を有効化

#### 5-2. Get Dataset Items

- **ノード**: Apify - Get Dataset Items
- **出力**: 各ユーザーのプロフィール情報

### 6. フィールド編集（プロフィール情報）

- **ノード**: Edit Fields
- **抽出フィールド**:
  - `username`: ユーザー名
  - `bio`: バイオ
  - `followersCount`: フォロワー数
  - `isPrivate`: 非公開アカウント判定

### 7. フィルター

- **ノード**: Filter
- **条件**:
  1. `followersCount > 500`（フォロワー数500以上）
  2. `isPrivate = false`（非公開アカウントを除外）

### 8. Googleスプレッドシートへの追加

- **ノード**: Google Sheets - Append Row
- **設定**:
  - スプレッドシート: "Instagram leads"
  - カラムマッピング:
    - `username` → ユーザー名
    - `bio` → バイオ
    - `followersCount` → フォロワー数

## Apifyノードの使用方法

### 旧方法（非推奨）

以前はHTTP Requestノードを使用していたが、現在は非推奨。

**旧手順**:
1. HTTP RequestノードでPOSTリクエスト
2. Apify APIエンドポイント（`https://api.apify.com/v2/acts/{actorId}/runs`）に接続
3. 認証: Query Auth（トークンをパラメータとして送信）
4. データセット取得: `https://api.apify.com/v2/datasets/{datasetId}/items`

### 新方法（推奨）

n8nにネイティブのApifyノードが追加されたため、より簡単に使用可能。

**新 hand順**:
1. ApifyアカウントでAPIキーを取得
2. n8nの設定でApify APIキーを登録
3. "Run Actor"ノードを使用
4. "Get Dataset Items"ノードでデータを取得

**メリット**:
- 設定が簡素化
- エラーハンドリングが改善
- ノード数が増えるが、可読性と保守性が向上

## 拡張可能性

### 1. スクレイピング対象の拡張

ハッシュタグ以外にも以下の方法でスクレイピング可能:
- 特定の投稿から
- リールから
- その他ApifyストアにあるInstagramスクレイパーを活用

### 2. フォーム入力の拡張

- 複数のフィールドを追加
- フォーム入力に基づいて異なるワークフローに分岐

### 3. データ処理の拡張

- **バイオの要約**: AIエージェントを使用してバイオを2-3語で要約
- **バイオのフィルタリング**: 特定のキーワードを含むバイオのみ抽出
- **追加フィルター**: 
  - 投稿数（例: 20投稿以上）
  - その他のプロフィール情報

### 4. 出力先の拡張

- スプレッドシートに追加情報を記録（ハッシュタグ、その他のスクレイパーから取得した情報）
- 他のデータベースやCRMへの連携

## 注意点

1. **重複ユーザー名**: 同じユーザーが複数の投稿で出現する可能性があるため、ユニーク化処理を推奨
2. **データのクリーンアップ**: Instagramのデータには不要な情報が含まれる可能性があるため、フィルターとEdit Fieldsノードで適切にクリーンアップ
3. **フォロワー数のフィルター**: ビジネス要件に応じて閾値を調整（例: 5,000フォロワー以上、10,000フォロワー以上）
4. **非公開アカウント**: マーケティング目的の場合は非公開アカウントを除外

## ワークフロー構成のポイント

1. **2段階のスクレイピング**: ハッシュタグから投稿を取得し、その後プロフィール情報を取得する2段階構成
2. **データの整形**: Edit Fieldsノードで必要な情報のみ抽出
3. **フィルタリング**: 最終段階でフィルターを適用し、データの質を向上
4. **ネイティブノードの活用**: HTTP Requestではなく、Apifyのネイティブノードを使用

## 関連リソース

- Apifyストア: 様々なInstagramスクレイパーが利用可能
- n8nのApify統合: ネイティブノードによる簡単な連携
- Google Sheets連携: データの可視化と管理


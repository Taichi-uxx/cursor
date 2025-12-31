# Salesforce × Slack 新規リード営業ナレッジ連携 セットアップガイド

## 必要な環境変数とクレデンシャル

### 1. Salesforce OAuth2設定
```env
SALESFORCE_CLIENT_ID=your_salesforce_client_id
SALESFORCE_CLIENT_SECRET=your_salesforce_client_secret
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
```

**設定手順:**
1. Salesforceの「Setup」→「Apps」→「App Manager」
2. 「New Connected App」を作成
3. OAuth Settingsを有効化
4. Selected OAuth Scopes: `api`, `refresh_token`, `offline_access`
5. Callback URL: `https://your-n8n-instance.com/rest/oauth2-credential/callback`

### 2. PostgreSQL（営業ナレッジDB）
```env
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DATABASE=sales_knowledge
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
```

**必要なテーブル構造:**
```sql
-- 営業ナレッジテーブル
CREATE TABLE sales_knowledge (
  id SERIAL PRIMARY KEY,
  approach_method VARCHAR(255),
  talk_script TEXT,
  success_rate DECIMAL(5,2),
  key_points TEXT,
  industry VARCHAR(100),
  company_size INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知履歴テーブル
CREATE TABLE lead_notifications (
  id SERIAL PRIMARY KEY,
  lead_id VARCHAR(18),
  company VARCHAR(255),
  industry VARCHAR(100),
  assigned_team VARCHAR(100),
  ai_suggestions TEXT,
  notified_at TIMESTAMP
);

-- サンプルデータ投入
INSERT INTO sales_knowledge (approach_method, talk_script, success_rate, key_points, industry, company_size) VALUES
('課題ヒアリング型', '現在の業務プロセスでお困りの点はございますか？', 78.5, '相手の話を8割聞く、解決策は後回し', 'IT', 100),
('ROI提示型', '導入により年間○○万円のコスト削減が見込めます', 65.3, '具体的な数字を準備、競合との比較表を用意', '製造業', 500),
('段階導入型', 'まずは一部署でトライアル導入はいかがでしょうか', 82.1, 'リスクを最小化、成功体験を作る', '小売業', 50);
```

### 3. OpenAI API
```env
OPENAI_API_KEY=sk-your_openai_api_key
```

### 4. Slack OAuth2設定
```env
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
```

**設定手順:**
1. https://api.slack.com/apps で新規アプリ作成
2. OAuth & Permissions設定
3. Bot Token Scopes: `chat:write`, `chat:write.public`, `users:read`
4. OAuth Redirect URL: `https://your-n8n-instance.com/rest/oauth2-credential/callback`

### 5. カスタムフィールド（Salesforce）
以下のカスタムフィールドを作成：
- Opportunity: `Loss_Reason__c` (Text)
- Opportunity: `Competitors__c` (Text)

## n8nへのインポート手順

1. n8nにログイン
2. 左メニューの「Workflows」をクリック
3. 「Import from File」を選択
4. `salesforce-slack-lead-workflow.json`をアップロード
5. 各ノードのクレデンシャルを設定
6. ワークフローをアクティベート

## 動作テスト

1. Salesforceで新規リードを作成
2. Slackの`#sales-leads`チャンネルに通知が来ることを確認
3. AI提案内容が適切か確認

## トラブルシューティング

- **Webhook URLの設定**: SalesforceのProcess BuilderまたはFlowでWebhook URLを設定
- **権限エラー**: 各APIの権限設定を再確認
- **PostgreSQL接続エラー**: ファイアウォール設定とSSL設定を確認
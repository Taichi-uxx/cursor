---
# === 案件基本情報 ===
client:
project_name:
service_name:
business_area:
domain:

# === 契約条件 ===
contract:
  status:
  started_at:
  renewal_month:
  period:
  service:
  support_scope: []
  monthly_budget:
  fee:
  kpi:

# === 担当者 ===
cs_front:
supervisor:
team: []
client_contacts:
  main:
  others: []

# === 通知先Slack（社内連絡用） ===
slack:
  internal:
  internal_mentions:
    main_cc: []
    operators:
      default: []
      google:  []
      meta:    []

# === クライアント宛通知先（リリース告知・分析結果通知） ===
notification:
  tool:
  channel_name:
  channel_id:
  updated_at:

# === Notion参照URL（資料インプット元） ===
notion:
  client_page:

# === 配信媒体（種別のみ静的） ===
channels: []

# === Google広告アカウント ===
google_ads:
  customer_id:
  login_customer_id:
  ocid:

# === Meta広告アカウント ===
meta_ads:
  ad_account_id:
  business_id:
  page_id:

# === BigQuery参照 ===
bq:
  project_id:
  datasets: []
  tables: []
  notes: |

# === 定例MTG ===
meeting:
  frequency:
  week_of_month:
  weekday:
  start_time:
  duration_min:
  format:
  doc_format:
  doc_url:
  doc_title:
  notta_video_ext: []
  notta_video_int: []

# === 動的スナップショット ===
freshness:
  profile:
  context:
  history:

persona:
  near_churn_history: []
  upsell_candidates: []

# === メタ ===
updated_at:
source:
confidence:
---

# {会社名} - {案件名} プロファイル

{案件概要1〜2行で。プロスペクトの場合は契約締結後の運用フォルダ移行想定も記載}

## 案件概要
- **支援領域**: -
- **契約経緯**: -
- **KPI**: -
- **支援形態**: -

## 契約条件
- **契約サービス**: -
- **予算**: -
- **手数料**: -
- **契約開始**: -
- **契約期間**: -
- **契約更新月**: -

## 担当者（案件固有）
| 役割 | 氏名 | 備考 |
|------|------|------|
| 弊社メイン |  |  |
| 弊社統括 |  |  |
| 弊社サブ |  |  |
| 先方メイン |  |  |
| 先方サブ |  |  |

## 配信媒体（種別のみ。実績値は `status.md`）
- **Google広告**: -
- **Microsoft広告**: -
- **Meta広告**: -
- **その他**: -

## 定例MTG
- **頻度**: -
- **曜日・時間**: -
- **形式**: -
- **定例資料の形式**: -
- **定例資料/資料蓄積URL**: -

## Notion参照URL
- **クライアントページURL**: -

## 通知先

### 社内連絡用Slack
- **社内通知先**: -

### クライアント宛通知先（リリース告知・分析結果）
- **通知ツール**: -
- **チャネル名**: -
- **チャネルID**: -

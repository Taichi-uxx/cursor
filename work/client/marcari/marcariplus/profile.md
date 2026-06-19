---
# === 案件基本情報 ===
client: マーキャリ
project_name: マーキャリ Plus（新規受託）
service_name: マーキャリ Plus
business_area: GM
domain: LP制作 + 広告運用

# === 契約条件 ===
contract:
  status: 受託確定（契約書取り交わし予定）
  started_at: 2026-07（LP制作着手予定）
  renewal_month:
  period:
  service: LP制作 + 広告運用（Meta中心）+ クリエイティブ制作
  support_scope:
    - LP制作（パートナー経由）
    - Meta広告運用
    - クリエイティブ制作（バナー）
  monthly_budget: 200,000〜300,000円/月（広告費・クライアント負担）
  fee:
    lp_production: 約500,000円（パートナー込み・40〜45万前後 + α）
    monthly_management: 広告費の20%
  kpi:

# === 担当者 ===
cs_front: 田村
supervisor:
team: []
client_contacts:
  main: 今井さん
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
channels:
  - Meta広告（中心）

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
  profile: 2026-06-18
  context: 2026-06-18
  history: 2026-06-18

persona:
  near_churn_history: []
  upsell_candidates: []

# === メタ ===
updated_at: 2026-06-18
source: 商談一次情報（2026-06-18 今井さんMTG）
confidence: high
---

# マーキャリ - マーキャリ Plus プロファイル

以前作成したまま運用が止まっていた marcari Plus LP を、SaaS 業界の経験者採用シフトに対応するべく内容刷新＋広告配信を新規に立ち上げる案件。田村が個人（副業）で受託し、LP 制作はパートナー経由、広告運用は Meta 中心で開始する。

## 案件概要
- **支援領域**: LP制作（パートナー経由）+ Meta広告運用 + クリエイティブ制作
- **契約経緯**: 2026-03 今井さんと食事で初期相談 → 2026-06-18 商談で正式受託
- **KPI**: 未定（面談・登録獲得 → CPA／CVR を初期 KPI として設計予定）
- **支援形態**: 個人契約（副業）。先方とは契約書を取り交わし予定

## 契約条件
- **契約サービス**: LP制作 + 広告運用 + クリエイティブ制作
- **予算**: 月次広告費 200,000〜300,000円（クライアント負担）
- **手数料**: 月次広告費の20%
- **LP制作費**: 約500,000円（パートナー費用 40〜45万前後 + 田村側構成・調整費）
- **契約開始**: 2026-07（LP制作着手予定）
- **契約期間**: -
- **契約更新月**: -

## 担当者（案件固有）
| 役割 | 氏名 | 備考 |
|------|------|------|
| 弊社メイン | 田村 | 個人契約・副業OK |
| 弊社統括 |  |  |
| 弊社サブ | LP制作パートナー | 田村経由で発注 |
| 先方メイン | 今井さん |  |
| 先方サブ |  |  |

## 配信媒体（種別のみ。実績値は `status.md`）
- **Google広告**: -
- **Microsoft広告**: -
- **Meta広告**: あり（中心媒体）
- **その他**: 動画クリエイティブ活用余地あり（YouTube 動画素材を Meta 広告に流用検討）

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

## 参考リンク
- マーキャリ Plus LP: https://next.mar-cari.jp/plus/
- マーキャリ Next CAREER LP（トンマナ参考）: https://next.mar-cari.jp/lp/0007/

## 制作スコープ・納品形態
- **納品形態**: 静的HTML一式（ZIP）→ 先方でアップロード
- **デザイン方針**: 既存マーキャリ LP のオレンジトンマナをベースに、Plus は赤系トンマナへ変更／ロゴ・中身も差し替え
- **原稿**: 基本的に先方（今井さん）で用意。LP 構成案も先方が下書きし、田村サイドで仕上げ
- **コンテンツ要素**:
  - 強み・差別化セクション（求人直接訴求は外す）
  - 成功者の声セクション（既存セクションを継承）
  - **キャリア図鑑（縦軸：年収アップ／横軸：職種チェンジ）** — Plus の目玉セクション
  - 事例セクション（SaaS to SaaS 転職事例。顔出しなしのイラスト中心）

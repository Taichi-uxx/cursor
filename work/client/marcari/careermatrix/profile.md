---
# === 案件基本情報 ===
client: マーキャリ
project_name: キャリアマトリックス診断（相談段階）
service_name: キャリアマトリックス診断
business_area: GM
domain: 広告運用 + LINEナーチャリング

# === 契約条件 ===
contract:
  status: 相談段階（先方社内で意思決定中／来週火曜までに回答予定）
  started_at:
  renewal_month:
  period:
  service: Meta広告運用 + LINEナーチャリング設計 + クリエイティブ制作（想定）
  support_scope:
    - Meta広告運用
    - LINEナーチャリング設計（L-Step）
    - クリエイティブ制作
    - L-Step × Meta CV連携設定
  monthly_budget: 250,000円/月（Meta 20万 + リスティング 5万・9月時点）
  fee:
  kpi: 面談CV獲得（月平均2件目標／現状平均1件）

# === 担当者 ===
cs_front: 田村
supervisor:
team: []
client_contacts:
  main: 寺本 和美
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
  - Meta広告
  - Google広告（リスティング）

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
  profile: 2026-09-11
  context: 2026-09-11
  history: 2026-09-11

persona:
  near_churn_history: []
  upsell_candidates: []

# === メタ ===
updated_at: 2026-09-11
source: 商談一次情報（2026-09-11 寺本さんMTG）
confidence: high
---

# マーキャリ - キャリアマトリックス診断 プロファイル

エムエム総研が運営するキャリアマトリックス診断（営業職向けキャリアポテンシャル診断）の広告運用・LINEナーチャリング支援案件。マーキャリ本体・マーキャリPLUSとは別の広告運用領域として相談を受けている。田村のフリーランス独立（2026-10-01）に合わせて10月から切り替えたい先方意向。

## 案件概要
- **支援領域**: Meta広告運用・LINEナーチャリング設計・クリエイティブ制作
- **サービス構成**: 二段階診断（①MBTIライクな16タイプ診断 → ②マッチング診断＝相性企業・5年後年収グラフ・おすすめ求人）
- **KGI**: 面談CV獲得
- **重要指標**: マッチング診断完了率（面談CVは全員マッチング診断完了者）
- **月平均面談CV目標**: 2件（現状平均1件、最大3件・累計11件）
- **契約経緯**: 2025-08頃初回接点 → 2026-09-11 相談MTG再開 → 田村独立に合わせて10月切替検討中
- **支援形態**: 個人契約（フリーランス）想定

## 契約条件
- **契約サービス**: 未確定（Meta広告運用＋LINEナーチャリング設計をコア想定）
- **予算**: 月次広告費 25万円（Meta 20万 + リスティング 5万・9月時点、LINE広告は停止済み）
- **手数料**: 未確定
- **契約開始**: 2026-10 想定
- **契約期間**: 未確定
- **契約更新月**: -

## 担当者（案件固有）
| 役割 | 氏名 | 備考 |
|------|------|------|
| 弊社メイン | 田村 | フリーランス（2026-10-01独立） |
| 弊社統括 |  |  |
| 弊社サブ |  |  |
| 先方メイン | 寺本 和美 | 広告運用担当 |
| 先方サブ |  | テルモン（L-Step運用担当） |

## 配信媒体（種別のみ。実績値は `status.md`）
- **Google広告（リスティング）**: あり（月5万・「キャリア診断」「転職診断」中心・完全一致＋インテントマッチ）
- **Microsoft広告**: -
- **Meta広告**: あり（月20万・動画1本＋静止画風動画2本＋昨日追加2本＝計5本、配信・友達登録の9割が動画経由）
- **LINE広告**: 停止済み（8月まで実施・友達登録単価100円台だが面談CVにつながらず）

## 定例MTG
- **頻度**: 未定（10月切替後に設定想定）
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
- キャリアマトリックス診断 LP: 要共有（寺本さんから資料送付予定）

## サービス・流入導線
- **流入経路**: Meta広告・リスティング・オウンドメディア・YouTube → キャリアマトリックスLP → 公式LINE登録
- **LINE統合状況**: 2026-08頭に専用LINEアカウントから公式LINEへ統合済み。LPのCTAも公式LINE誘導へ変更済み
- **LINEツール**: ChatBoost → L-Step 移行済み
- **ナーチャリング現状**: 友達登録後1〜3日目のシナリオ配信のみ（16タイプ診断未実施者促し／マッチング診断未実施者促し）。面談訴求まで未到達
- **既知の課題**: 16タイプ診断結果ページに面談促進CTAなし（寺本自己指摘）

## タムラ側スコープ（想定）
- Meta広告運用刷新（クリエイティブ多様化・ターゲティング分離・第三者視点広告検討）
- LINEナーチャリング設計（流入直後1〜3日以内のシナリオ強化・マッチング診断完了→面談導線・YouTube動画活用）
- L-Step × Meta CV連携（友達登録CVを返す・Google広告連携も可）
- リスティングは現運用継続（寺本担当）を想定

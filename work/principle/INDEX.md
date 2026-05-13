# principle/ — 精選原則層

エージェントが常時参照する「鉄則・原則・判断基準」を格納する。
**少数精鋭・月次レビュー**で運用し、抽象化された原則のみを置く。詳細な蓄積は `/Users/apple/.cursor/work/knowledge/` 側へ。

---

## 構成（業務領域ベース）

| サブフォルダ | 役割 | 主な利用ロール |
|---|---|---|
| `マーケ戦略/` | 田村の判断軸・ペルソナ設計・ヒアリング項目など戦略の土台 | ①CMO ②Market Res. ③Customer Anlz. ④Bus.Strg. + 全ロール（判断軸） |
| `マーケ施策/` | 施策別の原則（SEO/LLMO/CRM/MA/モール/アフィリエイト） | ①CMO ④Bus.Strg. |
| `業界知見/` | 業界別の規制・トーン・勝ち型（人材/美容/店舗/不動産/クリニック/BtoB/EC） | 全ロール（業界が関与する場面） |
| `広告運用/` | 媒体別の運用原則（Search/Shopping/P-MAX/Dynamic/Meta/TikTok/YDA） | ⑦ ⑧ ⑩ ⑪ ⑫ |
| `クリエイティブ/` | 制作物別の原則（コピー/バナー/LP/動画） | ⑤ ⑥ ⑦ ⑧ ⑨ ⑭ ⑮ ⑯ |
| `SNS運用/` | SNS別の運用原則（Instagram/LINE/TikTok/YouTube） | ⑬ ⑭ ⑮ |

---

## ロール別の必須参照マップ

| ロール | 必須参照フォルダ |
|---|---|
| ① CMO | `マーケ戦略/` `マーケ施策/` `業界知見/<業界>/` |
| ② Market Researcher | `マーケ戦略/` |
| ③ Customer Analyzer | `マーケ戦略/`（特に ペルソナ設計要点.md・ヒアリング項目.md） |
| ④ Business Strategist | `マーケ戦略/` `マーケ施策/` `業界知見/<業界>/` |
| ⑤ Creative Director | `マーケ戦略/田村の判断軸.md` `クリエイティブ/` `業界知見/<業界>/` |
| ⑥ Copywriter | `クリエイティブ/コピー/` `業界知見/<業界>/` |
| ⑦ Video Ad Director | `クリエイティブ/動画/` `広告運用/Meta/` `広告運用/TikTok/` `広告運用/YDA/` |
| ⑧ Banner Conceptor | `クリエイティブ/バナー/` `広告運用/` `業界知見/<業界>/` |
| ⑨ LP Architect | `クリエイティブ/LP/` `業界知見/<業界>/` |
| ⑩ Operations Director | `マーケ戦略/田村の判断軸.md` `広告運用/` `業界知見/<業界>/` |
| ⑪ Search Ads Specialist | `広告運用/Search/` `広告運用/Shopping/` `広告運用/P-MAX/` |
| ⑫ SNS Ads Specialist | `広告運用/Meta/` `広告運用/TikTok/` `広告運用/YDA/` |
| ⑬ Content Director | `SNS運用/` `クリエイティブ/動画/` |
| ⑭ YouTube Director | `SNS運用/YouTube/` `クリエイティブ/動画/` |
| ⑮ Short Video Director | `SNS運用/TikTok/` `SNS運用/Instagram/` `SNS運用/YouTube/` `クリエイティブ/動画/` |
| ⑯ Scriptwriter | `クリエイティブ/動画/` `マーケ戦略/ペルソナ設計要点.md` |
| ㉑㉒㉓ Persona | `マーケ戦略/ペルソナ設計要点.md` `マーケ戦略/田村の判断軸.md` |

---

## 既存ファイル（2026-05-13時点）

### マーケ戦略/
- 田村の判断軸.md
- ヒアリング項目.md
- ペルソナ設計要点.md

### 各カテゴリのサブフォルダ（中身はこれから田村が肉付け）
- 業界知見/{人材, 美容, 店舗, 不動産, クリニック, BtoB, EC}/
- 広告運用/{Dynamic, Meta, P-MAX, P-MAX/Demand, Search, Shopping, TikTok, YDA, YDA/LINE}/
- マーケ施策/{モール, アフィリエイト, CRM, CRM/MA, LLMO, SEO}/
- クリエイティブ/{動画, コピー, バナー, LP}/
- SNS運用/{Instagram, LINE, TikTok, YouTube}/

---

## principle 昇格ルール

knowledge/ から principle/ に「昇格」させる判断基準：

| 昇格条件 | 例 |
|---|---|
| 複数案件で再現性が確認された勝ち型 | 「医療業界のLPは PASONA型 が勝率高い」 |
| 失敗の共通原因が抽出された | 「Reelsの1秒目に文字を出すと離脱+30%」 |
| 媒体仕様の変更で重要なルール変化 | 「Google広告のRSA入稿規定が変わった」 |
| 法規制の最新ガイドライン | 「景表法の優良誤認に新ガイドライン」 |

### 運用
- **月次レビュー**: 自動化＋手動ハイブリッド
- **逆方向**: principleにあるが古い・参照されない → knowledge/archive/ へ降格

---

## 関連
- 雑多な蓄積アーカイブ: `/Users/apple/.cursor/work/knowledge/INDEX.md`
- 設計書: `/Users/apple/.cursor/work/AI-Studio PJT/AI-Studio設計.md`
- 組織図: `/Users/apple/.cursor/work/AI-Studio PJT/組織図.md`

---

## 注意事項

- ロール別の「採点ルール」「判断ロジック」「So What抽出手順」などの**ロール固有原則は agent.md 内に直書き**する方針（`role-principles/` フォルダは廃止）
- 各 agent.md は `work/AI-Studio PJT/agent-drafts/<NN>_<role>.md` を参照

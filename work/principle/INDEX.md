# principle/ — 精選原則層

エージェントが常時参照する「鉄則・原則・判断基準」を格納する。
**少数精鋭・月次レビュー**で運用し、抽象化された原則のみを置く。詳細な蓄積は `/Users/apple/.cursor/knowledge/` 側へ。

---

## 構成

| サブフォルダ | 役割 | 主な利用ロール |
|---|---|---|
| `core/` | 全ロール共通の原則（田村の事業観・出力品質・法規制） | 全ロール必読 |
| `role-principles/` | 各ロール固有の鉄則・判断ロジック | 該当ロール |
| `frameworks/` | フレームワーク要点（3C/STP/4P/PASONA/AIDMA/ペルソナ/ジャーニー） | 戦略系・LP系 |
| `platforms/` | 媒体仕様の要点（Google/Yahoo/Meta/TikTok/YouTube/Shorts/Reels/Banner） | 運用系・制作系 |
| `winning-patterns/` | 勝ち型（コピー/LP/動画フック/バナー） | 制作系 |
| `benchmarks/` | 業界×媒体ベンチマーク要点 | 分析系 |

---

## ファイル一覧（適宜更新）

### core/
- [ ] 田村の判断軸.md ★Week1雛型作成済
- [ ] 出力品質基準.md
- [ ] 法規制チェック.md
- [ ] 案件運用ルール.md

### role-principles/
- [ ] 01_cmo判断ロジック.md
- [ ] 05_creative-director採点ルール.md ★Week1雛型作成済
- [ ] 10_operations-director-sowhat.md
- [ ] persona評価フォーマット.md
- [ ] 06_copywriter原則.md
- [ ] 07_video-ad-director原則.md
- [ ] 08_banner-conceptor原則.md
- [ ] 09_lp-architect原則.md
- [ ] 11_search-ads原則.md
- [ ] 12_sns-ads原則.md
- [ ] 13_content-director原則.md
- [ ] 14_youtube-director原則.md
- [ ] 15_short-video-director原則.md
- [ ] 16_scriptwriter原則.md

### frameworks/
- [ ] 3C要点.md
- [ ] STP要点.md
- [ ] 4P要点.md
- [ ] PASONA要点.md
- [ ] AIDMA要点.md
- [ ] ペルソナ設計要点.md ★Week1雛型作成済
- [ ] ジャーニー設計要点.md

### platforms/
- [ ] google-ads要点.md ★Week1雛型作成済
- [ ] yahoo-ads要点.md
- [ ] meta要点.md
- [ ] tiktok要点.md
- [ ] youtube要点.md
- [ ] youtube-shorts要点.md
- [ ] reels要点.md
- [ ] tiktok-shorts要点.md
- [ ] banner-specs要点.md

### winning-patterns/
- [ ] コピー勝ちパターン.md
- [ ] LP勝ちパターン.md
- [ ] 動画フック勝ちパターン.md
- [ ] バナー勝ちパターン.md

### benchmarks/
- [ ] <業界>_search.md
- [ ] <業界>_meta.md
- [ ] ...

---

## principle昇格ルール

knowledge/ から principle/ に「昇格」させる判断基準：

| 昇格条件 | 例 |
|---|---|
| 複数案件で再現性が確認された勝ち型 | 「医療業界のLPは PASONA型 が勝率高い」 |
| 失敗の共通原因が抽出された | 「Reelsの1秒目に文字を出すと離脱+30%」 |
| 媒体仕様の変更で重要なルール変化 | 「Google広告のRSA入稿規定が変わった」 |
| 法規制の最新ガイドライン | 「景表法の優良誤認に新ガイドライン」 |

### 運用
- **月次レビュー**: knowledge新規追加分から昇格候補を抽出 → principle更新（自動化＋手動ハイブリッド）
- **逆方向**: principleにあるが古い・参照されない → knowledgeに降格 or archive/へ

---

## 関連
- 雑多な蓄積アーカイブ: `/Users/apple/.cursor/knowledge/INDEX.md`
- 設計書: `/Users/apple/.cursor/work/AI-Studio PJT/AI-Studio設計.md`
- 組織図: `/Users/apple/.cursor/work/AI-Studio PJT/組織図.md`

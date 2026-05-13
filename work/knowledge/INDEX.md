# knowledge/ — 蓄積アーカイブ層

詳細スペック・生事例・参考資料・過去レポートを**雑多に貯める**フォルダ。
気軽に追加し、必要時にエージェントが深掘り参照する。
重要なものは月次レビューで `/Users/apple/.cursor/principle/` に昇格させる。

---

## 構成

| サブフォルダ | 役割 |
|---|---|
| `industries/` | 業界別の詳細（規制細部・競合・ケーススタディ・トレンドログ） |
| `platforms/` | 媒体別の詳細（spec詳細・アルゴリズム観察記・参考記事・仕様変更履歴） |
| `benchmarks/` | 業界×媒体の月次スナップショット |
| `playbooks/` | 過去案件の蓄積（copy/video/lp/banner/short-video） |
| `research/` | ②Market Researcherの調査ログ |
| `templates/` | ヒアリングシート等のテンプレ |
| `archive/` | 古くなったもの・principleから降格したもの |

---

## 推奨ファイル構造

```
industries/
  <業界名>/
    overview.md
    regulations-detail.md
    competitors/
    case-studies/
    trends-log/

platforms/
  <媒体名>/
    spec-detail.md
    algorithm-notes.md
    reference-articles/
    version-history.md

benchmarks/
  <業界>_<媒体>/
    monthly-snapshots/
      YYYY-MM.md

playbooks/
  copy/<業界>/
    win-cases.md
    loss-cases.md
  video/<業界>/
  lp/<業界>/
  banner/<業界>/
  short-video/

research/
  <YYYY-MM-DD>_<テーマ>.md

templates/
  hearing-sheet.md ★Week1雛型作成済
  ...

archive/
```

---

## ファイル蓄積の心得

- **雑多OK**: 思いついたら入れる。整理は後追い
- **出典明示**: WEB記事・参考資料は必ずソースを記載（CLAUDE.mdルール）
- **日付管理**: 時系列で意味があるもの（トレンド・スナップショット）は `YYYY-MM-DD_` プレフィックスで
- **principleに昇格させる候補**は `## 昇格候補メモ` セクションを末尾に置くと、月次レビューで拾いやすい

---

## 月次レビュー（自動化＋手動）

### 自動化対象
- `/loop monthly /knowledge-review`（コマンド未作成）
- 新規追加ファイルから「昇格候補」を抽出して報告

### 手動対象
- 重要度が高いもの・直感で決めたいものは手動で昇格させる
- archive/への降格判断

---

## 関連
- 精選原則層: `/Users/apple/.cursor/principle/INDEX.md`
- 設計書: `/Users/apple/.cursor/work/AI-Studio PJT/AI-Studio設計.md`

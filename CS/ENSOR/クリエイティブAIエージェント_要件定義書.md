# クリエイティブAIエージェント UI設計書

**作成日**: 2025年11月24日  
**バージョン**: 1.0（モックUI作成用）  
**ステータス**: UI設計

---

## 📋 目次

1. [サービス概要](#サービス概要)
2. [コア機能](#コア機能)
3. [画面仕様](#画面仕様)
4. [UI/UX設計](#uiux設計)
5. [ゲーミフィケーション](#ゲーミフィケーション)
6. [V0用プロンプト](#v0用プロンプト)

---

## サービス概要

### サービス名
**ENSOR Creative AI Agent**（仮称）

### サービスコンセプト
**「クリエイティブ版Cursor」** - 過去のクリエイティブ実績を学習し、高精度な広告クリエイティブを生成するAIエージェントサービス

### ターゲットユーザー
- デジタルマーケター
- 広告代理店
- インハウスマーケティングチーム
- クリエイティブディレクター

### 提供価値
1. **データドリブンなクリエイティブ制作**: 過去実績から勝ちパターンを学習
2. **制作効率の向上**: AI活用により制作時間を大幅削減
3. **成果の可視化**: クリエイティブ別実績を一元管理・分析
4. **継続的な改善**: フィードバックループによる精度向上

---

## コア機能

### 1. BIインターフェース（分析）
**目的**: クリエイティブ別の実績を可視化・分析

#### 主要機能
- **パフォーマンスダッシュボード**
  - カード形式表示（ビジュアル重視）
  - テーブル形式表示（データ詳細）
  - 表示形式の切替可能
  
- **フィルタリング機能**
  - 期間指定
  - 媒体（Meta, Google, TikTok, LINE）
  - CPA範囲
  - ターゲット属性
  - 訴求軸（価格、品質、限定など）
  
- **実績指標**
  - IMP（インプレッション）
  - CTR（クリック率）
  - CVR（コンバージョン率）
  - CPC（クリック単価）
  - CPA（獲得単価）
  - CPM（インプレッション単価）
  
- **メタデータ表示**
  - 媒体
  - ターゲット
  - 訴求軸
  - コピー
  - レイアウトパターン
  
- **AIチャット機能**
  - 自然言語での質問対応
  - データ取得（「先月のCPAトップ5は？」）
  - 分析（「なぜこのクリエイティブの成果が良いの？」）
  - 提案（「次に試すべき訴求は？」）
  
- **自動インサイト提示**
  - パフォーマンス異常値の検知
  - トレンド分析
  - 改善提案の自動生成

### 2. 生成インターフェース（AI生成）
**目的**: 新規クリエイティブのアイデア・ラフ案を生成

#### 主要機能
- **ナレッジベース参照**
  - Cursor風の@メンション機能
  - クリエイティブ名で検索・選択
  - 最大5件まで同時参照可能
  
- **生成パラメータ入力**
  - 目的（購入、資料請求、認知など）
  - 媒体（Meta, Google, TikTok, LINE）
  - ターゲット（テキスト入力）
  - 訴求軸（価格、品質、限定など）
  - その他の指示（自由記述）
  
- **生成アウトプット**
  - ヘッドラインコピー
  - ボディコピー
  - CTA（Call to Action）提案
  - レイアウト説明文
  - デザインノート（配色、雰囲気など）
  - ※画像ラフ生成は将来対応
  
- **イテレーション機能**（Phase 2）
  - 生成結果へのフィードバック
  - 再生成
  - バージョン履歴管理

### 3. ナレッジベース（データ蓄積）
**目的**: クリエイティブデータを整理・蓄積し、学習精度を向上

#### 主要機能
- **クリエイティブアップロード**
  - 画像ファイル（JPEG, PNG, WebP）
  - 動画ファイル（MP4, MOV）※Phase 2
  - ドラッグ&ドロップ対応
  
- **自動メタデータ抽出**
  - レイアウトパターン判定
    - 商品中心型
    - 人物メイン型
    - テキストメイン型
  - ドミナントカラー抽出
  - テキスト要素の抽出（OCR）
  
- **手動編集機能**
  - 自動抽出されたメタデータの修正
  - 追加情報の入力
    - ターゲット属性
    - 訴求軸
    - カスタムタグ
    - メモ
  
- **ナレッジベース追加**
  - 「学習に使う」ボタンでナレッジベースに追加
  - 追加したデータのみがAI生成時に参照される
  - XP獲得（+10XP）
  
- **広告実績の自動連携**
  - API経由で各媒体から自動取得
  - 日次で実績データ更新
  - クリエイティブIDで自動紐付け

---

## 画面仕様

### 1. 生成機能の流れ

#### 生成フロー
```
1. ユーザーがナレッジベースから参照データを選択（最大5件）
   ↓
2. 生成パラメータを入力
   - 目的
   - 媒体
   - ターゲット
   - 訴求軸
   - その他指示
   ↓
3. バックエンドでRAG（Retrieval-Augmented Generation）実行
   a. 選択されたクリエイティブをベクトル検索
   b. 類似する高パフォーマンスクリエイティブを追加取得
   c. コンテキストを構築
   d. LLM（GPT-4/Claude）に送信
   ↓
4. 生成結果を表示
   - ヘッドライン
   - ボディコピー
   - CTA
   - レイアウト説明
   - デザインノート
   ↓
5. ユーザーがフィードバック（評価、メモ）
   ↓
6. XP獲得（+5XP）
```

### 2. BIダッシュボードの画面仕様

#### カード形式表示
```
┌─────────────────────────┐
│   [サムネイル画像]       │
│   （16:9アスペクト比）   │
├─────────────────────────┤
│ CPA: ¥1,200             │
│ CTR: 2.3%               │
│ IMP: 123,456            │
├─────────────────────────┤
│ 🏷️ 価格訴求             │
│ 📱 Meta                 │
│ 📅 2024/11/01-11/07    │
└─────────────────────────┘
※ホバーで「詳細を見る」ボタン表示
```

#### テーブル形式表示
```
| サムネ | 媒体 | CPA    | CTR  | IMP    | 訴求   | 期間      | 操作 |
|--------|------|--------|------|--------|--------|-----------|------|
| [IMG]  | Meta | ¥1,200 | 2.3% | 123,456| 価格   | 11/01-07  | [...] |
| [IMG]  | Google| ¥1,450| 1.8% | 98,765 | 品質   | 11/01-07  | [...] |
```

#### フィルターパネル
- **期間**: カレンダーピッカー（開始日〜終了日）
- **媒体**: チェックボックス（複数選択可）
- **CPA範囲**: スライダー（¥0 〜 ¥10,000）
- **訴求軸**: ドロップダウン（単一選択）
- **ターゲット**: テキスト検索

#### デフォルト表示順
- CPA昇順（低い方が優秀）
- ユーザーがカスタマイズ可能（CPA, CTR, IMP, 日付）

### 3. ナレッジベースの画面仕様

#### アップロードエリア
- ドラッグ&ドロップゾーン
- 対応形式: JPEG, PNG, WebP
- 複数ファイル同時アップロード可能

#### クリエイティブ一覧
- グリッド表示（カード形式）
- サムネイル + 基本情報（媒体、訴求軸、CPA）
- 検索バー、タグフィルター

#### メタデータ編集画面
- 自動抽出された情報の表示・編集
- ターゲット、訴求軸、カスタムタグの入力
- 「ナレッジベースに追加」ボタン

---

## UI/UX設計

### ページ構成

```
/
├── /login                    # ログイン
├── /signup                   # 新規登録
├── /dashboard                # ダッシュボードトップ
├── /bi                       # BIダッシュボード
│   └── /bi/[id]              # クリエイティブ詳細
├── /generate                 # 生成インターフェース
│   ├── /generate/history     # 生成履歴
│   └── /generate/[id]        # 生成結果詳細
├── /knowledge                # ナレッジベース
│   └── /knowledge/[id]       # クリエイティブ詳細・編集
├── /chat                     # AIチャット
├── /insights                 # インサイト一覧
├── /settings
│   ├── /settings/profile     # プロフィール
│   ├── /settings/accounts    # 広告アカウント管理
│   └── /settings/billing     # 課金設定
└── /profile                  # ゲーミフィケーションプロフィール
```

### 共通レイアウト

```
┌────────────────────────────────────────────────────────┐
│  Header: Logo | Search | Notification | Level | Avatar │
├──────────┬─────────────────────────────────────────────┤
│          │                                             │
│ Sidebar  │          Main Content                      │
│          │                                             │
│ - BI     │                                             │
│ - 生成   │                                             │
│ - KB     │                                             │
│ - Chat   │                                             │
│ - 設定   │                                             │
│          │                                             │
└──────────┴─────────────────────────────────────────────┘
```

### 主要コンポーネント

#### BIダッシュボード
- FilterPanel（フィルター）
- ViewToggle（カード/テーブル切替）
- CreativeCard（カード形式）
- CreativeTable（テーブル形式）
- PerformanceChart（パフォーマンスグラフ）
- ChatPanel（AIチャットサイドパネル）

#### 生成インターフェース
- KnowledgeSelector（@メンション選択）
- GenerationForm（生成フォーム）
- GeneratedResult（生成結果カード）
- IterationPanel（イテレーション）

#### ナレッジベース
- UploadZone（ドラッグ&ドロップ）
- CreativeGrid（グリッド表示）
- MetadataEditor（メタデータ編集）
- AddToKnowledgeButton（KB追加ボタン）

#### ゲーミフィケーション
- LevelBadge（レベル表示）
- XPProgressBar（経験値バー）
- MilestoneCard（マイルストーンカード）
- XPToast（XP獲得トースト通知）

---

## ゲーミフィケーション

### XP獲得アクション

| アクション | XP | 説明 |
|-----------|-----|------|
| クリエイティブアップロード | +10 | 1件あたり |
| ナレッジベースに追加 | +10 | 1件あたり |
| クリエイティブ生成 | +5 | 1件あたり |
| 広告実績連携 | +20 | 1件あたり |
| 生成クリエイティブへのフィードバック | +3 | 1件あたり |
| 高成果クリエイティブ作成（CPA上位10%） | +50 | ボーナス |

### レベル設計（案）

| レベル | 必要XP | 報酬 |
|-------|--------|------|
| Lv.1 | 0 | 生成枠: 月5件 |
| Lv.2 | 100 | 生成枠: 月10件 |
| Lv.3 | 300 | 生成枠: 月20件 + クリエイティブ3枚プレゼント |
| Lv.4 | 600 | 生成枠: 月30件 |
| Lv.5 | 1,000 | 生成枠: 月50件 + 高度な分析機能アンロック |
| Lv.6 | 1,500 | 生成枠: 月75件 |
| Lv.7 | 2,100 | 生成枠: 月100件 + クリエイティブ5枚プレゼント |
| Lv.8 | 2,800 | 生成枠: 月150件 |
| Lv.9 | 3,600 | 生成枠: 月200件 + 画像ラフ生成機能アンロック |
| Lv.10 | 5,000 | 生成枠: 無制限 + 全機能アンロック |

### マイルストーン報酬詳細

#### クリエイティブプレゼント
- CSチームがユーザーの業界・商材に合わせたクリエイティブを制作
- 画像形式で納品
- バリエーション込み（横型、縦型、正方形など）

#### 機能アンロック
- **高度な分析機能**（Lv.5）
  - クリエイティブ間の相関分析
  - 予測CPA算出
  - トレンド分析
  
- **画像ラフ生成**（Lv.9）
  - DALL-E 3による画像生成
  - レイアウトモックアップ生成

### UX設計

#### レベルアップ演出
- 画面全体にアニメーション
- レベルアップサウンド（オプション）
- 新しい報酬の説明モーダル
- SNSシェアボタン

#### XP獲得通知
- 右上にトースト通知
- 「+10 XP」アニメーション
- プログレスバーが伸びる演出

#### マイルストーン表示
- タイムライン形式で表示
- 達成済み：緑チェックマーク
- 現在：パルス（点滅）アニメーション
- 未達成：グレーアウト

---

## V0用プロンプト

以下はV0でUI作成する際に使用できるプロンプト集です。

### プロンプト1: BIダッシュボード（カード形式）

```
Create a modern BI dashboard for a creative analytics platform using Next.js, TypeScript, and shadcn/ui.

Requirements:
1. Filter panel at the top with:
   - Date range picker
   - Platform multi-select (Meta, Google, TikTok, LINE)
   - CPA range slider
   - Appeal type select (価格訴求, 品質訴求, 限定訴求)

2. View toggle buttons (Card view / Table view)

3. Card grid layout showing creative performance:
   - Thumbnail image (16:9 aspect ratio)
   - CPA (¥1,200 format)
   - CTR (2.3% format)
   - Impressions (formatted with commas)
   - Appeal type badge
   - Platform icon badge
   - Date range text
   - Hover effect with "View Details" button

4. Responsive grid (1 col mobile, 2 col tablet, 3-4 col desktop)

5. Empty state when no data

6. Loading skeleton states

Use Tailwind CSS for styling, Lucide React for icons, and make it beautiful and modern.
```

### プロンプト2: 生成インターフェース

```
Create a creative generation interface using Next.js, TypeScript, and shadcn/ui.

Requirements:
1. Knowledge selector with:
   - Input field with "@" trigger to search and select creatives
   - Show selected items as removable chips/badges
   - Max 5 selections
   - Dropdown menu showing thumbnail + name

2. Generation form with:
   - Objective radio buttons (Purchase, Lead, Awareness, Other)
   - Platform checkbox group (Meta, Google, TikTok, LINE)
   - Target audience textarea
   - Appeal type select dropdown
   - Additional notes textarea

3. Generate button (primary, full width, with loading state)

4. Generated result card showing:
   - Headline (large text)
   - Body copy (paragraph)
   - CTA suggestion (badge)
   - Layout description (with simple diagram)
   - Design notes (bullet list)
   - Action buttons: "Regenerate", "Save", "Edit"

5. Generation progress indicator during AI processing

6. Side panel showing referenced creatives with thumbnails

Use modern, clean design with smooth animations.
```

### プロンプト3: ゲーミフィケーション要素

```
Create a gamification profile page using Next.js, TypeScript, and shadcn/ui.

Requirements:
1. Level badge component:
   - Large level number (Lv.5)
   - XP progress bar (450/1000 XP)
   - "Next reward" preview

2. Milestone timeline:
   - Vertical timeline with icons
   - Completed milestones (green checkmark)
   - Current milestone (highlighted, pulsing)
   - Locked milestones (grayed out)
   - Each milestone shows: Level, Required XP, Reward description, Icon

3. XP activity log:
   - Recent XP gains in a list
   - Icon + Description + XP amount + Timestamp
   - Examples: "Uploaded creative +10 XP", "Generated creative +5 XP"

4. Stats cards:
   - Total creatives uploaded
   - Total generations this month
   - Generation limit (15/20)
   - Days streak

5. Rewards section:
   - Unlocked features list
   - Available free creatives counter

Use vibrant colors for rewards, smooth progress animations, and celebratory effects.
```

### プロンプト4: ナレッジベース

```
Create a knowledge base interface for creative assets using Next.js, TypeScript, and shadcn/ui.

Requirements:
1. Upload zone:
   - Drag and drop area with dashed border
   - "Drop images here or click to upload"
   - Show uploading progress
   - Support multiple files

2. Search and filter bar:
   - Search input with icon
   - Tag filter chips (removable)
   - Sort dropdown (CPA, Date, Platform)

3. Creative grid:
   - Masonry or regular grid layout
   - Each card shows:
     - Thumbnail
     - Platform badge
     - Appeal type tag
     - CPA value
     - "Add to Knowledge Base" button (star icon)
   - Hover effects

4. Creative detail modal:
   - Large image preview
   - Metadata editor form (Target, Appeal, Tags, Notes)
   - Performance metrics
   - "Save" and "Add to KB" buttons

5. Empty states and loading skeletons

Use clean, organized design with good spacing.
```

### プロンプト5: 共通レイアウト

```
Create a dashboard layout with sidebar navigation using Next.js, TypeScript, and shadcn/ui.

Requirements:
1. Header:
   - Logo on the left
   - Search bar in center
   - Right side: Notification bell, Level badge (Lv.5), User avatar

2. Sidebar (collapsible):
   - Navigation items with icons:
     - BI Dashboard
     - Generate
     - Knowledge Base
     - AI Chat
     - Insights
     - Settings
   - Active state highlighting
   - Collapse button

3. Main content area:
   - Takes remaining space
   - Padding and max-width for readability
   - Scroll independently

4. Responsive:
   - Mobile: Hidden sidebar (hamburger menu)
   - Tablet: Icon-only sidebar
   - Desktop: Full sidebar

5. Dark mode support

Use modern design with smooth transitions.
```

---

**Document Version**: 1.0 (UI Design Focus)  
**Last Updated**: 2025-11-24  
**Status**: Ready for UI Development


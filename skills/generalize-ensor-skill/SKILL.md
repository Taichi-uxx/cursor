---
name: generalize-ensor-skill
description: >-
  ENSOR環境（内部プラグイン・独自ツール・環境固有パスなどに依存する）向けに書かれたスキル文言を
  受け取り、ENSOR依存を全て剥がして素のClaude Codeで動く汎用スキル（SKILL.md＋必要ファイル）に
  変換する。ユーザーがENSORのSKILL.md本文や関連ファイルをペースト／指定した上で
  `/generalize-ensor-skill` を呼び出したときに使う。
disable-model-invocation: true
---

# Generalize ENSOR Skill → Claude Code Skill

ENSOR環境に依存したスキル文言を、素のClaude Code（`~/.claude/skills/` or `.claude/skills/`）で
そのまま動く汎用スキルに変換する。

**大原則: スキルの「目的・ワークフロー・ユーザー体験」は完全に保存する。**
**変えるのはENSOR環境に依存している「実装手段の記述」だけ。**

## When to use

- ユーザーが「このENSORスキルを汎用化して」「Claude Codeでも使えるようにして」と依頼したとき
- ユーザーがSKILL.md本文（もしくはファイルパス）をペーストしてこのスキルを呼び出したとき

## Inputs

以下のいずれかを受け取る:

1. **本文貼付**: ENSORのSKILL.md本文（frontmatter含む）を直接ペースト
2. **ファイルパス**: `~/ensor/skills/foo/SKILL.md` などのパス指定
3. **スキルパッケージ**: SKILL.md + `scripts/` + `reference.md` などの一式

いずれでもよい。スキル一式ならディレクトリ全体をREADして扱う。

## Workflow

以下の5ステップで進める。各ステップは飛ばさない。

### Step 1: 入力の取り込みと構造把握

1. ユーザーが本文をペーストした場合はそのまま解析。ファイルパスが渡された場合はRead。
2. スキルディレクトリごと渡された場合は `SKILL.md`、`scripts/*`、`reference.md` 等を
   全てRead（`ls` で構成を先に確認）。
3. 以下を抽出してメモする:
   - **元スキル名**（frontmatter `name`）
   - **元description**
   - **主目的**（何を達成するスキルか、1〜2文で要約）
   - **入力仕様**（引数・ペースト内容・必須/任意）
   - **出力仕様**（何が生成される・どこに保存される）
   - **ワークフロー骨格**（何ステップで、各ステップで何をするか）

**この段階で「このスキルの本質」を掴む。以降の変換で「本質を保つ」判断基準になる。**

### Step 2: ENSOR依存要素の検出

以下の観点で本文・スクリプト・参照ファイルを走査し、**依存要素のリスト**を作る。

#### 2.1 ツール依存

Claude Code標準ツール以外の呼び出しを検出:

- **標準ツール（残してよい）**: `Read` / `Write` / `Edit` / `Bash` / `Grep` / `Glob` /
  `WebFetch` / `WebSearch` / `Agent` / `TaskCreate` / `NotebookEdit` /
  MCP標準系（Playwright MCP 等、`.mcp.json` に定義があるもの）
- **非標準ツール（要置換 or 要削除）**: ENSOR内部専用ツール、Cursor固有API、
  ENSORが提供するMCPサーバ、独自CLI（`ensor-cli` 等）、独自SDK呼び出し

判別基準:
- Claude Code公式ドキュメント／`AGENTS.md`／`.mcp.json` に登場するかどうか
- 迷ったら「置換候補あり」としてメモしておき、Step 4でユーザーに確認する

#### 2.2 パス依存

- **絶対パス**（`/Users/apple/.cursor/`, `~/ensor/`, `/opt/ensor/` 等）→
  Claude Code規約の相対パスに書き換え候補
  - スキル本体: `~/.claude/skills/<name>/` or `.claude/skills/<name>/`
  - スクリプト: スキル配下の `scripts/`
  - ワークスペース配下: `.`（cwd）基準
- **環境固有変数**（`$ENSOR_HOME`, `$ENSOR_PROJECT_ROOT` 等）→ 汎用変数（`$HOME`, cwd）に置換

#### 2.3 プラグイン／サービス依存

- ENSOR固有のプラグイン参照（`ensor-plugin:xxx` 形式など）
- ENSOR固有のバックエンドサービス（社内API、認証機構、内部LLMゲートウェイなど）
- ENSOR固有のシークレット参照方法（`ensor.secrets.get()` など）

これらは以下のいずれかで処理:
- **汎用代替がある**: 標準SDK（Anthropic SDK直叩き、`openai` SDK 等）／
  環境変数からのシークレット読み込み（`.env` + `python-dotenv`）に置換
- **代替がない**: 該当ステップを「ユーザーが自分で用意する外部依存」として明記し、
  スキル冒頭に **Prerequisites** セクションを追加

#### 2.4 実行環境依存

- ENSOR特有のランタイム前提（特定Pythonバージョン、特定Node環境、ENSOR sandboxなど）
- ENSORが自動で提供する context injection（現在の案件、ユーザーID、組織情報など）
  → これらは汎用環境では取得できないので、**ユーザー引数で明示的に受け取る形**に変換

#### 2.5 UI／通知依存

- ENSOR固有のUI（Canvas、独自ペイン、独自通知など）
- Chatwork/Slack/Discord 等の外部通知連携（これは残せる場合が多い。API/webhook経由なら汎用）
- 「ENSORのUIに描画する」系の指示 → 標準出力（Markdown）／ファイル書き出しに置換

### Step 3: 依存マップの提示

Step 2で作った依存リストを、以下のテーブル形式でユーザーに提示する:

```markdown
## 検出されたENSOR依存要素

| # | カテゴリ | 元の記述 | 依存度 | 提案する置換 |
|---|---------|---------|--------|-------------|
| 1 | ツール | `ensor.canvas.render(...)` | 高（代替なし） | 削除 or Markdownファイル書き出しに変更 |
| 2 | パス | `/opt/ensor/skills/foo/` | 中 | `~/.claude/skills/foo/` |
| 3 | サービス | ENSOR内部LLMゲートウェイ | 高 | `anthropic` SDK直接呼び出し（要APIキー） |
| 4 | プラグイン | `ensor-plugin:pdf-reader` | 低（Claude Code標準にあり） | Read tool（PDFネイティブ対応） |
| ... | | | | |
```

ユーザーに「この置換方針でよいか」を確認。置換方針の修正指示があれば反映する。

**依存度が高＝代替なし** のものが1つでもある場合は、
「このスキルは汎用化するとコア機能が失われます。続行しますか？」と警告する。

### Step 4: 汎用SKILL.md の生成

置換方針が確定したら、以下の手順で新スキルを組み立てる。

#### 4.1 メタデータ

- `name`: 元のスキル名をそのまま流用。ENSOR固有の接頭辞（`ensor-`）があれば剥がす。
  衝突する既存スキル（`~/.cursor/skills/<name>/` 存在）があれば、
  `<name>-generic` などの候補をユーザーに提示。
- `description`: 元のdescriptionをベースに、ENSOR固有の言及を削除。
  「〜〜のとき使う」の部分は保持（トリガー語として重要）。
- `disable-model-invocation: true` を付ける（スラッシュコマンド起動を前提とするため）。
  ただし元スキルが「文脈から自動起動」型なら外す。

#### 4.2 本文

以下の順で構成する:

```markdown
# <スキル名>

<1〜2文の目的説明。元スキルの本質を保存>

## Prerequisites  ← 汎用化で外部依存が生まれた場合のみ追加

- 必要な環境変数（例: `ANTHROPIC_API_KEY`）
- 必要な外部ツール（例: `python 3.11+`, `ffmpeg`）
- 事前セットアップ手順（あれば）

## Inputs

<元スキルの入力仕様を転記>

## Workflow

<元スキルのワークフローを転記＋ENSOR依存箇所だけ置換>

## Outputs

<元スキルの出力仕様を転記。ENSOR UI描画は Markdown/ファイル書き出しに変換>

## Gotchas

<CLAUDE.md の指示に従い、必ずこのセクションを設ける（空でも見出しだけは残す）>

- <日付>: <ENSOR→汎用化で気づいた注意点があればここに記載>
```

**本文の書き換え原則:**

- ワークフローの**ステップ数・順番**は変えない
- 各ステップの**目的**は変えない
- **実装手段の記述**（どのツールで、どのパスに、どのAPIで）だけ書き換える
- 元がプロンプト指示（「サブエージェントに〜させる」）ならそのまま残す
- 元スキルに `## Gotchas` があれば内容を保持しつつ、汎用化に伴う注意点を追記

#### 4.3 付随ファイル

- `scripts/` にPython/シェルスクリプトがあった場合:
  - ENSOR固有のimport（`from ensor.xxx import ...`）を汎用SDKに書き換え
  - パス依存を修正（`os.path.expanduser("~/.claude/skills/...")` 等）
  - 環境変数の読み込みを標準化（`os.getenv("ANTHROPIC_API_KEY")` など）
  - ENSOR依存が剥がせないスクリプトは **削除** し、SKILL.md本文で
    「該当機能はユーザー環境で自作が必要」と明記
- `reference.md` などのドキュメントは、ENSOR固有記述を書き換えた上で保持

### Step 5: 保存と登録

1. 保存先を確認（デフォルト提案 → ユーザー変更可）:
   - **Personal**: `~/.cursor/skills/<name>/`（Claude Code は `~/.claude/skills/` から参照）
   - **Project**: `.claude/skills/<name>/`（プロジェクト内共有）

2. ディレクトリを作成し `SKILL.md` および付随ファイルを書き出し。

3. Personal保存の場合、`~/.cursor/skills/SKILLS_INDEX.md` に1行追加（既存カテゴリに追記
   or 新カテゴリ作成）。

4. 最後にサマリを提示:
   - 生成された `SKILL.md` の保存先パス
   - 剥がしたENSOR依存要素の一覧
   - Prerequisites（あれば）
   - 動作確認のためにユーザーがすべきこと（環境変数設定、外部ツール導入など）

## Anti-patterns

- ❌ 「ENSOR依存が多いから汎用化不可能」と早々に諦める → まず依存マップを作って提示
- ❌ ワークフローを勝手に簡略化する → 実装手段だけ変え、ロジックは保持
- ❌ 元のプロンプト文言を「よりよい表現」に書き換える → 動作に関わらない文言は verbatim 保持
- ❌ ENSOR固有UIをMarkdownに置換したことを黙って進める → 出力形式が変わる旨をサマリで明示
- ❌ 依存要素検出をスキップして「よさそうに書き換える」 → 必ず Step 2 の走査を行う

## Gotchas

（日付＋教訓を随時追記）

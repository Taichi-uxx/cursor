# 非エンジニアがObsidianとCursorの環境を整えた

## 記事の目標

本記事では、以下を達成するための手順を説明する。

- CursorでObsidianを編集できるようになる
- Kindle書籍の知識をObsidianに蓄えられるようにする
- iPhoneとPCでObsidianを同期し、iPhoneでメモを取れるようにする（同期にはGithubを利用）
- iPhoneとPC両方から、Web上のコンテンツをObsidianに蓄えられるようにする

### 対象者

- これからCursorでObsidianを始めたい方（特に非エンジニアの方向け）
- CursorとObsidianをセットアップし、メモ管理の環境を整えたい方
- スマホとPCの同期方法に悩んでいる方

### この記事で述べていないこと

- メモ管理の具体的な運用方法、ノウハウ
- Cursorを使った効率的な記事作成方法

## ObsidianとCursorについて

### Cursorとは

AIと一緒にコーディングができるコードエディタ。画面中央はファイルスペース、右側にチャットスペースがあり、AIにさまざまな作業をお願いしながら、一緒に共同作業する感覚でファイルを作成することができる。最近では、**記事を生成・編集するツール**としても注目を集めている。

### Obsidianについて

ローカル端末で動作する、Markdown形式のノートアプリ（ドキュメントエディタ）。現在、Notionの代替ツールとして注目を集めている。

注目されている理由：

- Markdown形式（.md）がAIに読み取られやすい
- Notionは階層が深くなりがちだが、Obsidianはフラットでタグベースの管理のため、AIが読み取りやすい
- 拡張機能が充実しており、色々なアプリと連携したり、カスタマイズしやすい

AIフレンドリーなエディタのため、これからのAIネイティブな知的生産や仕事にとても親和性がある。

## なぜObsidian in Cursorを始めたのか

- **育児と仕事がある中で日々の内省・タスク管理・インプットとアウトプットを効率化したい**
- **生成AIを使うことに慣れていきたい**
- **職場でNotionが使えない**

## セットアップ手順

### 1. CursorでObsidianを編集できるようにする

#### 1-1. Obsidianのインストール

Obsidianをインストールし、新しいVault（ノートを保存するフォルダ）を作成する。

#### 1-2. CursorでObsidianのVaultを開く

Cursorを起動し、File > Open Folderから、作成したObsidianのVaultフォルダを開く。これでCursorでObsidianのMarkdownファイルを編集できるようになる。

### 2. Kindle書籍の知識をObsidianに蓄える

#### 2-1. Kindle Highlightsプラグインのインストール

Obsidianの設定画面から「コミュニティプラグイン」→「ブラウズ」を開き、「Kindle Highlights」を検索してインストールする。

#### 2-2. Kindle Highlightsプラグインの設定

1. 設定画面の「Kindle Highlights」を開く
2. 「Kindleのデータファイルの場所」に、Kindleのデータファイルのパスを入力する
   - Macの場合：`~/Library/Application Support/Kindle/My Kindle Content/`
3. 「ハイライトを保存するフォルダ」を指定する（例：`20_LiteratureNote`）
4. 「テンプレート」を設定する

#### 2-3. テンプレートの設定

後日インデックスノートでギャラリーライクに表示させるために、プロパティを追加する。設定しておかないとサムネが表示されずクリップし直したくなる。

テンプレート例：

```markdown
---
title: {{title}}
author: {{author}}
image: {{image}}
tags: []
created: {{date}}
---

# {{title}}

## メタ情報
- 著者: {{author}}
- 読了日: {{date}}

## ハイライト

{{highlights}}
```

### 3. iPhoneとPCでObsidianを同期する（Githubを利用）

#### 3-1. Githubアカウントの作成

Githubアカウントを作成する（既にある場合はスキップ）。

#### 3-2. ObsidianのGitプラグインのインストール

Obsidianの設定画面から「コミュニティプラグイン」→「ブラウズ」を開き、「Obsidian Git」を検索してインストールする。

#### 3-3. Obsidian Gitプラグインの設定

1. 設定画面の「Obsidian Git」を開く
2. 「Vault backup interval (minutes)」で自動同期の間隔を設定する（例：60分）
3. 「Disable push」のチェックを外す（プッシュを有効にする）
4. 「Pull updates on startup」にチェックを入れる（起動時にプルする）

#### 3-4. Githubリポジトリの作成と接続

1. Githubで新しいリポジトリを作成する
2. ObsidianのVaultフォルダで、ターミナルを開く
3. 以下のコマンドを実行する：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin [リポジトリのURL]
git push -u origin main
```

#### 3-5. iPhoneでObsidianを開く

1. iPhoneにObsidianアプリをインストールする
2. Obsidianアプリを開き、「Open folder as vault」を選択
3. 「Clone an existing remote vault」を選択
4. 「Git」を選択し、GithubリポジトリのURLを入力
5. 認証情報を入力して同期する

#### 3-6. iPhoneでメモを取る

iPhoneのObsidianアプリでメモを取ると、自動的にGithubに同期される（設定した間隔で）。PC側でも同様に、Obsidian Gitプラグインが自動的に同期を行う。

### 4. Web上のコンテンツをObsidianに蓄える

#### 4-1. PCでWebページをストックする

**Obsidian Web Clipper**（Chrome拡張機能）をインストールする。

使い方：
1. インストール後、ChromeのタブからObsidianのアイコンをクリックして保存する
2. 設定画面の「デフォルト」→「ノートの場所」で、特定のフォルダ（例：`20_LiteratureNote`）を保存先として指定する

**テンプレートの編集**

Web clipperの方も、後日インデックスノートでギャラリーライクに表示させるために、プロパティを追加する。設定しておかないとサムネが表示されずクリップし直したくなる。

左メニューの「デフォルト」をクリック→「＋プロパティを追加」をクリックし、以下のように**image:{{image}}**を追加する。

#### 4-2. スマホでWebページをストックする

スマホの場合、Chromeの拡張機能が使えないため、Safariを使う。

**Obsidian Web Clipper**（iOSアプリ）をインストールする。

使い方：
1. SafariでWebページを開く
2. 下部のURL入力タブ左の拡張機能アイコンをクリック
3. 「Obsidian Web Clipper」をタップしてページを保存する
4. PC版と同様に、事前に保存先フォルダを設定する

#### 4-3. ObsidianでGithubに同期する

記事を保存したあと、手動同期の設定にしている場合は、Gitプラグインを用いてコミット・プッシュする。自動同期の設定になっている場合は自動でプッシュされる。

## 今後やりたいこと

- タグやリンクを使ってメモ（LiteratureNote）同士を繋げていき情報を探しやすくする＆知識を関連づけていく
- Cursorを使って効率的にアウトプット（note記事など）を作る

## 参考記事

- [内部リンク - Obsidian 日本語ヘルプ](https://publish.obsidian.md/help-ja/How+to/Internal+links)
- [Cursorを使った文章執筆は、AIファーストな環境整備から始まる - 本しゃぶり](https://honeshabri.hatenablog.com/entry/cursor-writing-environment)

## 出典

- [非エンジニアがObsidianとCursorの環境をいい感じに整えた](https://note.com/akienakai/n/nad947525d548#dd083f6d-3264-46ae-ba10-5951d2f3d6e6)


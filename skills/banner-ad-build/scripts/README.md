# banner-ad-build / scripts

バナー広告の画像処理パイプライン。

1. **gen_bg.py** — テキストを含まない背景ビジュアル(BG)を生成
2. **compose_banner.py** — BG 背景の上に日本語コピー/CTA/ロゴ/数値を HTML/CSS で重ねる
3. レンダリング (スクショ化) は **スキル側が Playwright で `file://` を開いて実行**

設計方針: プロバイダ非依存・標準ライブラリ中心・決定論的・堅牢なエラー処理。
秘匿情報 (APIキー / `.env` の中身) は stdout/stderr/ログに一切出さない。

---

## セットアップ

システムPython は PEP 668 (Homebrew) で pip 保護されるため、**スキル専用 venv** を使う:

```bash
cd /Users/apple/.cursor/skills/banner-ad-build
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt openai google-genai
# 以降スクリプトは必ず .venv/bin/python3 で実行する
```

### `.env` に設定すべき変数 (キー値は記載しない)

`.env` は `python-dotenv` の `load_dotenv()` 経由でのみ参照される (中身は読まない)。
**lp-build と同じ `/Users/apple/.cursor/.env` を共有する** (キーは一元管理)。
探索順:
1. 環境変数 `BANNER_BUILD_ENV_FILE` で **`.env` の絶対パスを明示** (標準パスに無いときはこれを使う)
2. cwd から上方向に自動探索
3. 既知候補 `/Users/apple/.cursor/.env` → `skills/banner-ad-build/.env` → `~/.cursor/.env` → `~/.env`

`.env` をどこにも読み込めなかった場合、キー未設定エラーにその旨を明示する。

**既定動作 = Gemini(Nano Banana) を基本、エラー時 OpenAI(GPT Image) で自動代替。**
何も設定しなければチェーンは `gemini,openai`。1プロバイダで全アスペクト成功してから採用する
(アスペクトが別プロバイダ混在しない)。

| 変数名 | 用途 | 必須 |
|---|---|---|
| `BANNER_BUILD_ENV_FILE` | `.env` の絶対パス明示 (標準パスに `.env` が無いとき必須) | 状況により |
| `IMAGE_PROVIDER_CHAIN` | フォールバック順 (カンマ区切り)。既定 `gemini,openai` | 任意 |
| `IMAGE_PROVIDER` | 単一固定したいときのみ (自動フォールバック無効) | 任意 |
| `OPENAI_API_KEY` | チェーンに openai を含むとき | 条件付き必須 |
| `OPENAI_IMAGE_MODEL` | OpenAI 画像モデルID。既定 `gpt-image-1`。新モデル時はここで上書き | 任意 |
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | チェーンに gemini を含むとき | 条件付き必須 |
| `GEMINI_IMAGE_MODEL` | Gemini 画像モデルID。既定 `gemini-3.1-flash-image-preview`（田村確認済）。別モデル時のみ上書き | 任意 |
| `FAL_KEY` / `REPLICATE_API_TOKEN` | チェーンに fal / replicate を含むとき | 条件付き必須 |

> 実際のキー値はこの README にもコードにも書かない。必ず `.env` に記述する
> (lp-build と共有の `/Users/apple/.cursor/.env`)。
> モデルIDは時期で変わりうるため、最新IDは `OPENAI_IMAGE_MODEL` /
> `GEMINI_IMAGE_MODEL` で上書きする (コード変更不要)。

チェーンの**全プロバイダ**が失敗した場合のみ非ゼロ終了する (トレースバック無し):

- 全て「キー未設定」起因 → `exit 2` ＋ 必要キー候補を stderr 表示
- 1つでも実呼び出し失敗 (API/ネットワーク等) → `exit 1` ＋ 集約エラー

フォールバック発生時は stderr に `[gemini] 失敗。次のプロバイダへ…` を出すが、
stdout は常に JSON 1 行のみ (秘匿情報なし)。正常時の stdout に採用
`"provider"` を含む: `{"images":[...],"provider":"gemini"}`

---

## 1) gen_bg.py

バナー広告の背景画像のみを生成する。文字は一切入れない (後段で HTML 合成)。

### CLI 契約

```bash
python3 gen_bg.py \
  --prompt "<背景ビジュアルの説明>" \
  --out-dir <dir> \
  [--n <int default 1>] \
  [--aspect square,horizontal,vertical|all default square] \
  [--focal center-left|center|center-right default center]
```

- `--aspect` はカンマ区切りで複数指定可。許容値 `square` / `horizontal` /
  `vertical`、`all` で 3 種全部。
- ユーザープロンプト末尾に必ず次が自動付与される:
  `no text, no letters, no typography, no logo, no watermark; leave clean
  negative space at the {focal} for a headline overlay; high-end editorial
  advertising key visual`
- OpenAI サイズ: `square -> 1024x1024`, `horizontal -> 1536x1024`,
  `vertical -> 1024x1536`
- Gemini アスペクト言語ヒント (サイズパラメータ非対応のため):
  `square -> "square 1:1 composition"`,
  `horizontal -> "horizontal 1.91:1 landscape composition"`,
  `vertical -> "vertical 9:16 portrait composition"`
- タイムアウト 180s / リトライ 2 回 (計 3 試行) / バックオフあり

### 標準出力 (正常時のみ・JSON 1 行)

```json
{"images":[{"aspect":"square","path":"/abs/bg_square_1.png"}],"provider":"gemini"}
```

保存名: `<out-dir>/bg_<aspect>_<i>.<ext>`（`ext` は実フォーマット＝png/jpg/webp。Geminiはjpg返却が多い）。下流は本JSONの `path` をそのまま使うので整合は保たれる

### 終了コード

| code | 意味 |
|---|---|
| 0 | 成功 |
| 1 | 生成/IO 失敗 (親切なエラー文を stderr) |
| 2 | APIキー未設定 / 未対応プロバイダ / 引数不正 |
| 130 | 中断 (Ctrl-C) |

### プロバイダ拡張手順

`gen_bg.py` 冒頭 docstring 参照。要点:

1. `_generate_<name>(prompt, size_key, count) -> list[bytes]` を実装
   (キーは `os.environ.get` 経由、不在時 `MissingApiKeyError` を raise)
2. `_PROVIDERS` に `"<name>": _generate_<name>` を登録
3. `_provider_env_hint` にキー名を追加
4. `requirements.txt` / 本 README に SDK・環境変数名を追記 (キー値は書かない)

---

## 2) compose_banner.py

BG 背景の上にバナーのコピー/CTA/ロゴ/数値を重ね、指定された各サイズごとに
1 つの HTML を生成。`../templates/banner_template.html` を `string.Template`
で置換 (外部依存なし)。

### CLI 契約

```bash
python3 compose_banner.py \
  --bg-square <path|空可> \
  --bg-horizontal <path|空可> \
  --bg-vertical <path|空可> \
  --sizes "1080x1080,1200x628,1080x1920,300x250" \
  --type copy-strong|visual-strong|number \
  --copy <json file or inline json> \
  --out-dir <dir>
```

- `--sizes` の各 `<W>x<H>` の縦横比からアスペクトを決定し背景を選択:
  - 比 `>= 1.2`（横長: 1200x628, 1280x720, 728x90, 970x250）→ horizontal
  - 比 `<= 0.7`（縦長: 1080x1920, 9:16）→ vertical
  - それ以外（~1:1〜4:5: 1080x1080, 1080x1350）→ square
- 該当アスペクトの背景が未指定なら **square にフォールバック**し stderr に
  1 行警告 (秘匿情報なし)。square も無ければ手元の最初の背景で代替。

### copy JSON スキーマ

```json
{
  "eyebrow": "(任意 小ラベル)",
  "main": "<メインコピー>",
  "sub": "<サブコピー>",
  "cta": "<CTAラベル>",
  "number": "(任意 数値訴求の主役 例 98%)",
  "number_label": "(任意 数値の説明 例 買取成立率)",
  "logo_text": "(任意)",
  "theme": {
    "text_color": "#ffffff",
    "accent": "#ff5a2b",
    "overlay": "rgba(0,0,0,0.4)",
    "align": "left|center",
    "position": "top|center|bottom"
  }
}
```

- `main` / `sub` / `cta` は必須 (空文字不可)。
- `number` は `--type number` のとき必須 (無ければ `exit 1` で明示エラー)。
- `theme` 省略時のデフォルト: text `#ffffff` / accent `#ff5a2b` /
  overlay `rgba(0,0,0,0.4)` / align `left` / position `bottom`。
- 色値は hex か `rgb()/rgba()/hsl()/hsla()` のみ許可 (CSS 注入対策)。
  不正値はデフォルトにフォールバック。
- テキストは HTML エスケープされる。`\n` 改行は `<br>` に変換され、
  見出しの意図的改行に使える。
- BG 画像は `file://` 絶対 URL として `background-image` に設定
  (Playwright が `file://` で開ける)。

### --type による強調の出し分け

`--type` はテンプレ側 `$type_class` に CSS クラスを渡して切り替える:

| type | クラス | 効果 |
|---|---|---|
| `copy-strong` | `t-copy` | コピー特大・スクリム濃いめ |
| `visual-strong` | `t-visual` | コピー最小・余白大・スクリム薄め |
| `number` | `t-number` | `number` を巨大表示 (数値訴求の主役) |

### 標準出力 (正常時のみ・JSON 1 行)

```json
{"banners":[{"size":"1080x1080","type":"copy-strong","html":"/abs/banner_copy-strong_1080x1080.html"}]}
```

各サイズごとに 1 HTML。保存名: `<out-dir>/banner_<type>_<W>x<H>.html`。

### 終了コード

| code | 意味 |
|---|---|
| 0 | 成功 |
| 1 | テンプレ欠落 / コピー不正 / 数値欠落 / 画像欠落 / IO 失敗 |
| 130 | 中断 (Ctrl-C) |

> `compose_banner.py` は実行時にテンプレ側プレースホルダ集合とコード側を
> 厳密照合し、不整合なら `exit 1` で明示エラーにする。

---

## 3) templates/banner_template.html

プロ品質・self-contained CSS の単一 HTML テンプレ。
プレースホルダ (compose_banner.py と厳密一致):

```
$bg_image_url $eyebrow_html $main_html $sub_html $cta_label
$number_html $logo_html $text_color $accent_color $overlay_color
$align $position $viewport $type_class
```

日本語フォントスタック:
`"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic",sans-serif`
スクリム(二層グラデ) + text-shadow で可読性を確保。ネットワーク不使用。

> **重要**: バナーは 300x250 〜 1080x1920 と寸法差が極端なため、コンテナを
> `$viewport`（`<width>px x <height>px`）ちょうどに実寸固定し、文字サイズは
> `cqmin` / `clamp` 等のビューポート相対で破綻しないようにしている。

---

## スキルからの呼び出し例

```bash
SCRIPTS=/Users/apple/.cursor/skills/banner-ad-build/scripts
WORK=/path/to/work-dir

# 1) 背景 BG を 3 アスペクト生成
python3 "$SCRIPTS/gen_bg.py" \
  --prompt "明るく洗練されたオフィスで微笑むビジネスパーソン、暖色の自然光" \
  --out-dir "$WORK" --n 1 --aspect all --focal center
# -> {"images":[{"aspect":"square","path":".../bg_square_1.png"},...],"provider":"gemini"}

# 2) コピーを重ねた各サイズのバナー HTML を生成
python3 "$SCRIPTS/compose_banner.py" \
  --bg-square "$WORK/bg_square_1.png" \
  --bg-horizontal "$WORK/bg_horizontal_1.png" \
  --bg-vertical "$WORK/bg_vertical_1.png" \
  --sizes "1080x1080,1200x628,1080x1920,300x250" \
  --type number \
  --copy '{"main":"廃車でも値がつく","sub":"最短即日・無料査定","cta":"無料査定する","number":"98%","number_label":"買取成立率","theme":{"accent":"#ff5a2b","position":"bottom"}}' \
  --out-dir "$WORK"
# -> {"banners":[{"size":"1080x1080","type":"number","html":".../banner_number_1080x1080.html"},...]}

# 3) スキル側が Playwright で file:// を開いてスクショ化 (本リポの責務外)
```

---

## 4) gen_full_banner.py（実験・文字込み一枚絵）

文字（コピー/数値/CTA/ロゴ）まで含めた **一枚絵バナー** を直接生成する
実験用スクリプト。デザイン性検証・着想出し用途。
gen_bg.py の確立エンジン（プロバイダ非依存・秘匿安全・exit 0/1/2/130・
`load_dotenv` 経由）を **ロジック完全保持** で踏襲した独立スクリプト。

> 安定品質が必要なときは **`compose_banner.py` のハイブリッド方式**
> （背景を生成AI、コピーは HTML/CSS で重ねて Playwright で書き出し）を
> 使うこと。本スクリプトはあくまで実験用途で残置する。

### 用途

- 1080×1080 (1:1 square) 固定の文字込み一枚絵バナーを直接生成
- 日本語タイポグラフィ崩れリスクを許容し、構図/世界観/表現の検証に使う

### CLI 契約

```bash
python3 gen_full_banner.py \
  --prompt "<コピー込みの完全プロンプト・日本語コピー原文を含めて良い>" \
  --out-dir <dir> \
  [--n <int default 1>] \
  [--variant <ラベル文字列・複数生成時の識別子・例 copy-strong|visual-strong|number>]
```

- `--variant` 未指定なら `v` をデフォルト識別子に使う
- `--aspect` / `--focal` は **無い**（1080×1080固定、文字配置はプロンプト本体で指示）
- OpenAI サイズ: `1024x1024`（gpt-image-1 の最寄り1:1値・実用上1080と差なし）
- Gemini アスペクト言語ヒント:
  `"square 1:1 composition, exact 1080x1080 social media banner"` を末尾固定付与
- ユーザープロンプト末尾に必ず次が自動付与される（最低限の崩れ抑制）:
  `produce a finished social media advertising banner; copy must be
  rendered crisply and legibly; high-quality typography and clean composition`

### copy 指示の書き方 Tips

- 日本語コピーは **プロンプト本体に原文をそのまま含める**
  （例: `メインコピー「廃車でも値がつく」、サブコピー「最短即日・無料査定」、CTAボタン「無料査定する」`）
- フォント/色/レイアウトは生成AIの描画依存。媒体ガイドに沿った
  指示語（serif/sans-serif/書体イメージ/ブランドカラー hex 等）を文中で渡す
- 文字配置（FV上下/中央寄せ/CTA位置）もプロンプトで言語指示する
- **崩れチェックは ⑤CD（クリエイティブディレクター）が行う**
  （目視で日本語タイポ崩れ・誤字・冗長字を判定し、不採用なら再生成）

### 既知の弱点

- **日本語タイポ崩れリスク**: 字形破綻・架空文字・誤字脱字が発生しうる
- 数値訴求（％記号・カンマ区切り）が崩れる場合あり
- ロゴテキストは描画依存のため、正確な企業ロゴ再現は不可
  （CI 厳格な案件は必ずハイブリッド方式に戻す）

### 標準出力 (正常時のみ・JSON 1 行)

```json
{"images":[{"variant":"copy-strong","path":"/abs/banner_copy-strong_1.jpg"}],"provider":"gemini"}
```

保存名: `<out-dir>/banner_<variant>_<i>.<ext>`
（`ext` は実フォーマット＝png/jpg/webp。Gemini は jpg 返却が多い）

### 終了コード（gen_bg.py と同一規約）

| code | 意味 |
|---|---|
| 0 | 成功 |
| 1 | 生成/IO 失敗 (親切なエラー文を stderr) |
| 2 | APIキー未設定 / 未対応プロバイダ / 引数不正 |
| 130 | 中断 (Ctrl-C) |

### 安定モードへの戻し方

- スクリプト自体は残置のまま、SKILL 側で `compose_banner.py` 経路
  （`gen_bg.py` で背景生成 → `compose_banner.py` で HTML 合成 →
  Playwright で file:// を開いてスクショ化）を呼べばハイブリッド方式に戻る
- 案件 CI が厳しい/日本語コピー精度必須のときは必ずハイブリッドに戻すこと

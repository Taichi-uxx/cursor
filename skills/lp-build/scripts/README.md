# lp-build / scripts

LP ファーストビュー(FV)の画像処理パイプライン。

1. **gen_kv.py** — テキストを含まない背景キービジュアル(KV)を生成
2. **compose_fv.py** — KV 背景の上に日本語コピー/CTA/ロゴを HTML/CSS で重ねる
3. レンダリング (スクショ化) は **スキル側が `<out-dir>` をローカルHTTP配信し
   Playwright で `http://127.0.0.1:<PORT>/fv_sp.html` を開いて実行**
   （Playwright MCP は `file:` をブロックするため。KVは相対参照で同origin解決）

設計方針: プロバイダ非依存・標準ライブラリ中心・決定論的・堅牢なエラー処理。
秘匿情報 (APIキー / `.env` の中身) は stdout/stderr/ログに一切出さない。

---

## セットアップ

システムPython は PEP 668 (Homebrew) で pip 保護されるため、**スキル専用 venv** を使う:

```bash
cd /Users/apple/.cursor/skills/lp-build
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt openai google-genai
# 以降スクリプトは必ず .venv/bin/python3 で実行する
```

### `.env` に設定すべき変数 (キー値は記載しない)

`.env` は `python-dotenv` の `load_dotenv()` 経由でのみ参照される (中身は読まない)。
探索順:
1. 環境変数 `LP_BUILD_ENV_FILE` で **`.env` の絶対パスを明示** (標準パスに無いときはこれを使う)
2. cwd から上方向に自動探索
3. 既知候補 `/Users/apple/.cursor/.env` → `skills/lp-build/.env` → `~/.cursor/.env` → `~/.env`

`.env` をどこにも読み込めなかった場合、キー未設定エラーにその旨を明示する。

**既定動作 = OpenAI(GPT Image) を基本、エラー時 Gemini(Nano Banana / `gemini-3-flash-image`) で自動代替。**
何も設定しなければチェーンは `openai,gemini`。1プロバイダで全サイズ成功してから採用する
(SP/PC が別プロバイダ混在しない)。

| 変数名 | 用途 | 必須 |
|---|---|---|
| `LP_BUILD_ENV_FILE` | `.env` の絶対パス明示 (標準パスに `.env` が無いとき必須) | 状況により |
| `IMAGE_PROVIDER_CHAIN` | フォールバック順 (カンマ区切り)。既定 `openai,gemini` | 任意 |
| `IMAGE_PROVIDER` | 単一固定したいときのみ (自動フォールバック無効) | 任意 |
| `OPENAI_API_KEY` | チェーンに openai を含むとき | 条件付き必須 |
| `OPENAI_IMAGE_MODEL` | OpenAI 画像モデルID。既定 `gpt-image-1`。新モデル時はここで上書き | 任意 |
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | チェーンに gemini を含むとき | 条件付き必須 |
| `GEMINI_IMAGE_MODEL` | Gemini 画像モデルID。既定 `gemini-3-flash-image`（Nano Banana・田村確認済）。別モデル時のみ上書き | 任意 |
| `FAL_KEY` / `REPLICATE_API_TOKEN` | チェーンに fal / replicate を含むとき | 条件付き必須 |

> 実際のキー値はこの README にもコードにも書かない。必ず `.env` に記述する。
> モデルIDは時期で変わりうるため、最新IDは `OPENAI_IMAGE_MODEL` /
> `GEMINI_IMAGE_MODEL` で上書きする (コード変更不要)。

チェーンの**全プロバイダ**が失敗した場合のみ非ゼロ終了する (トレースバック無し):

- 全て「キー未設定」起因 → `exit 2` ＋ 必要キー候補を stderr 表示
- 1つでも実呼び出し失敗 (API/ネットワーク等) → `exit 1` ＋ 集約エラー

フォールバック発生時は stderr に `[openai] 失敗。次のプロバイダへ…` を出すが、
stdout は常に JSON 1 行のみ (秘匿情報なし)。正常時の stdout に採用
`"provider"` を含む: `{"images":[...],"provider":"openai"}`

---

## 1) gen_kv.py

LP の FV 背景画像のみを生成する。文字は一切入れない (後段で HTML 合成)。

### CLI 契約

```bash
python3 gen_kv.py \
  --prompt "<背景ビジュアルの説明>" \
  --out-dir <dir> \
  [--n <int default 1>] \
  [--size sp|pc|both default both] \
  [--focal center-left|center|center-right default center-left]
```

- ユーザープロンプト末尾に必ず次が自動付与される:
  `no text, no letters, no typography, no logo, no watermark; leave clean
  negative space at the {focal} for a headline overlay; high-end editorial
  advertising key visual`
- OpenAI サイズ: `sp -> 1024x1536`, `pc -> 1536x1024`
- タイムアウト 180s / リトライ 2 回 (計 3 試行) / バックオフあり

### 標準出力 (正常時のみ・JSON 1 行)

```json
{"images":[{"size":"sp","path":"/abs/kv_sp_1.png"},{"size":"pc","path":"/abs/kv_pc_1.png"}]}
```

保存名: `<out-dir>/kv_<size>_<i>.<ext>`（`ext` は実フォーマット＝png/jpg/webp。Geminiはjpg返却が多い）。下流は本JSONの `path` をそのまま使うので整合は保たれる

### 終了コード

| code | 意味 |
|---|---|
| 0 | 成功 |
| 1 | 生成/IO 失敗 (親切なエラー文を stderr) |
| 2 | APIキー未設定 / 未対応プロバイダ / 引数不正 |
| 130 | 中断 (Ctrl-C) |

### プロバイダ拡張手順

`gen_kv.py` 冒頭 docstring 参照。要点:

1. `_generate_<name>(prompt, size_key, count) -> list[bytes]` を実装
   (キーは `os.environ.get` 経由、不在時 `MissingApiKeyError` を raise)
2. `_PROVIDERS` に `"<name>": _generate_<name>` を登録
3. `_provider_env_hint` にキー名を追加
4. `requirements.txt` / 本 README に SDK・環境変数名を追記 (キー値は書かない)

---

## 2) compose_fv.py

KV 背景の上に FV コピー/CTA/ロゴを重ねた SP/PC 2 種の HTML を生成。
`../templates/fv_template.html` を `string.Template` で置換 (外部依存なし)。

### CLI 契約

```bash
python3 compose_fv.py \
  --kv-sp <path> \
  --kv-pc <path> \
  --copy <json file or inline json> \
  --out-dir <dir>
```

### copy JSON スキーマ

```json
{
  "eyebrow": "(任意 小ラベル)",
  "main": "<メインコピー>",
  "sub": "<サブコピー>",
  "cta": "<CTAラベル>",
  "logo_text": "(任意)",
  "theme": {
    "text_color": "#ffffff",
    "accent": "#ff5a2b",
    "overlay": "rgba(0,0,0,0.35)",
    "align": "left|center",
    "position": "top|center|bottom"
  }
}
```

- `main` / `sub` / `cta` は必須 (空文字不可)。
- `theme` 省略時のデフォルト: text `#ffffff` / accent `#ff5a2b` /
  overlay `rgba(0,0,0,0.35)` / align `left` / position `bottom`。
- 色値は hex か `rgb()/rgba()/hsl()/hsla()` のみ許可 (CSS 注入対策)。
  不正値はデフォルトにフォールバック。
- テキストは HTML エスケープされる。`\n` 改行は `<br>` に変換され、
  見出しの意図的改行に使える。
- KV 画像は **HTMLからの相対参照(ファイル名)** で `background-image` に設定。
  KVが out-dir 外なら out-dir へコピーして相対化する。スキルが out-dir を
  HTTP配信するのでHTML/画像とも同origin httpで解決（`file:`非依存）。

### 標準出力 (正常時のみ・JSON 1 行)

```json
{"sp":"/abs/fv_sp.html","pc":"/abs/fv_pc.html"}
```

### 終了コード

| code | 意味 |
|---|---|
| 0 | 成功 |
| 1 | テンプレ欠落 / コピー不正 / 画像欠落 / IO 失敗 |
| 130 | 中断 (Ctrl-C) |

> `compose_fv.py` は実行時にテンプレ側プレースホルダ集合とコード側を
> 厳密照合し、不整合なら `exit 1` で明示エラーにする。

---

## 3) templates/fv_template.html

プロ品質・self-contained CSS の単一 HTML テンプレ。
プレースホルダ (compose_fv.py と厳密一致):

```
$bg_image_url $eyebrow_html $main_html $sub_html $cta_label
$logo_html $text_color $accent_color $overlay_color
$align $position $viewport
```

日本語フォントスタック:
`"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic",sans-serif`
スクリム(二層グラデ) + text-shadow で可読性を確保。ネットワーク不使用。

---

## スキルからの呼び出し例

```bash
SCRIPTS=/Users/apple/.cursor/skills/lp-build/scripts
WORK=/path/to/work-dir

# 1) 背景 KV を SP/PC 生成
python3 "$SCRIPTS/gen_kv.py" \
  --prompt "明るく洗練されたオフィスで微笑むビジネスパーソン、暖色の自然光" \
  --out-dir "$WORK" --n 1 --size both --focal center-left
# -> {"images":[{"size":"sp","path":".../kv_sp_1.png"},{"size":"pc","path":".../kv_pc_1.png"}]}

# 2) コピーを重ねた FV HTML を生成
python3 "$SCRIPTS/compose_fv.py" \
  --kv-sp "$WORK/kv_sp_1.png" \
  --kv-pc "$WORK/kv_pc_1.png" \
  --copy '{"eyebrow":"期間限定","main":"成果に\n直結する広告運用","sub":"売上と利益から逆算した戦略設計を。","cta":"無料で相談する","logo_text":"REHATCH","theme":{"accent":"#ff5a2b","align":"left","position":"bottom"}}' \
  --out-dir "$WORK"
# -> {"sp":".../fv_sp.html","pc":".../fv_pc.html"}

# 3) スキル側が out-dir をHTTP配信→Playwrightで http://127.0.0.1:PORT/fv_sp.html を開きスクショ化 (本リポの責務外)
```

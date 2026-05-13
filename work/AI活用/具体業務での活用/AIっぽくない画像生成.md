- 参照：https://x.com/mmmiyama_d/status/1961204992460955842?s=46&t=cPgkwaTs3CY0yrfe3oVnQg

#### 「AIっぽさ」をなくすために重要なプロンプト要素

**1. 物理的な素材・質感の明示（最重要）**
- `textured washi paper`（和紙の質感）
- `Paper tooth visible`（紙の繊維が見える）
- `matte finish`（マット仕上げ）
- `subtle pigment granulation`（顔料の粒子感）
→ AIが「完璧すぎる」デジタル感を避け、手描きの物理的痕跡を再現

**2. 不規則性・不完全性の許容**
- `slightly uneven`（わずかに不均一な線）
- `feathered edges`（ぼかされたエッジ）
- `lost-and-found contours`（途切れた輪郭）
- `controlled bloom/backrun effects`（水彩の滲み）
→ 完璧すぎない、人間らしい「揺らぎ」を意図的に導入

**3. 具体的な技法の指定**
- `Hand-drawn pencil line`（手描きの鉛筆線）
- `Wet-on-wet + glazing`（ウェットオンウェット＋グレージング）
- `Dry-brush accents`（ドライブラシのアクセント）
→ 実際のアーティストが使う技法名を明示することで、AIの推測を抑制

**4. 詳細度のコントラスト（人間の描画習慣を再現）**
- `Face and hands highly refined; clothing and background simplified`
- `Detail contrast: facial features smooth and precise; clothing & background kept painterly`
→ 人間が描くときの自然な優先順位（顔・手は詳細、背景は簡略化）を指定

**5. 具体的なカラーコード指定**
- `#1F242A–#2B2F36`（髪の色の範囲）
- `#EFCAD3`（頬の赤み）
- `#6E7A87 → #B8C1C8`（服のグラデーション）
→ AIの推測に任せず、具体的な色を指定することで「AIらしい配色」を回避

**6. ネガティブプロンプトの徹底**
- `white hair, silver hair, gray hair`（不要な色を排除）
- `kimono, yukata, hakama`（不要な要素を排除）
→ 不要な要素を明確に排除することで、意図しない「AIらしい」要素を防ぐ

**7. スタイルの具体化**
- `Japanese watercolor illustration`
- `pixiv-trending`
- `semi-realistic`
→ 曖昧な表現を避け、特定のスタイルを明確に指定

**8. パラメータ調整（Midjourneyの場合）**
- `--style raw`（デフォルトの過剰なスタイライズを無効化）
- `--stylize 50`（スタイライズを控えめに）
→ モデルの「AIらしい」過剰な処理を抑制
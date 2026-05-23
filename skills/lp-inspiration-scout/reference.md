# reference — ギャラリー一覧・検索クエリ雛形・除外基準

SKILL.md の Step2（ロングリスト収集）で使う。リサーチサブエージェントにこの内容を渡す。

## デザインギャラリー一覧（意匠の鮮度・横断）

JS描画前提。`browser_navigate`→`browser_wait_for`→`browser_snapshot` で見る。
業界・カテゴリで絞れるものはタグ/カテゴリページを使う。**全部回す必要はない**。
業界に合いそうな2〜4個を選んで深掘りする。

| ギャラリー | URL | 強み・使いどころ |
|---|---|---|
| Land-book | https://land-book.com | LP特化・業界/スタイルで絞れる王道。まず見る |
| Lapa Ninja | https://www.lapa.ninja | LPギャラリー。カテゴリ豊富 |
| SaaS Landing Page | https://saaslandingpage.com | SaaS/BtoBに最適。要素別の参照も可 |
| Godly | https://godly.website | 最先端・先進的意匠。鮮度重視のとき |
| Refero | https://refero.design | 実プロダクトの画面/LP。フロー単位で見れる |
| Mobbin | https://mobbin.com | Web/モバイルのUIパターン。導線・構成の参照 |
| Awwwards | https://www.awwwards.com | 受賞サイト。最高峰の見せ方（攻めすぎ注意） |
| One Page Love | https://onepagelove.com | 1ページLP特化。構成がシンプルで盗みやすい |
| SiteInspire | https://www.siteinspire.com | カテゴリ/スタイルで横断 |
| Httpster | https://httpster.net | トレンド感のあるサイト群 |
| Dark Mode Design | https://www.darkmodedesign.com | ダーク基調の先進系を探すとき |
| Landingfolio | https://www.landingfolio.com | LP＋セクション単位の参照 |

> 上記が基本セット。ユーザーがソース指定した場合や、業界特化ギャラリーが
> 別にある場合はそちらを優先（エスケープハッチ）。

## 検索クエリ雛形（事業の勢い・実LPへ到達）

`WebSearch` で使う。`<業界>` を英語の業界語に置換（例: スキンケアD2C→"skincare D2C" / "DTC beauty"、フィンテック→"fintech"、人材→"recruiting" "HR tech"）。
ギャラリーのサムネではなく**ライブの実サイト/トップページ**へ到達すること。

```
best <業界> landing page design
<業界> startup website design inspiration
<業界> Series A OR Series B website
top funded <業界> startups <地域>
<業界> SaaS homepage redesign
fastest growing <業界> companies website
<業界> product landing page 2 column hero
Y Combinator <業界> startup
<業界> brand site award winning
```

- 「funded」「Series A/B」「YC」「fastest growing」で**勢い**を担保。
- 「award winning」「inspiration」「redesign」で**意匠の鮮度**を担保。

### モメンタム裏取りクエリ（候補ごとに会社名で実行）

ロングリスト各候補を `勢い枠` に格上げできるか確認する。`<会社名>` を実名に置換。

```
<会社名> funding round Crunchbase
<会社名> Series A OR Series B OR seed 2025 OR 2024
<会社名> raises million TechCrunch
<会社名> careers OR jobs hiring          # 採用急拡大シグナル
<会社名> Y Combinator batch
<会社名> ARR OR growth OR revenue milestone
```

- 裏取り出典の信頼順: 自社プレス/IR ＞ TechCrunch等一次報道 ＞ Crunchbase等DB ＞ 業界メディアの注目リスト。SEOまとめ記事は不可。
- 直アクセスできない有料DB（Crunchbase/Similarweb本体）はWebSearchで露出した断片＋公開ページで判断。憶測で「勢いあり」と書かない＝裏取れなければ `意匠枠` か未確認扱い。

## 「勢力を伸ばしている」モメンタム階層（Step3で機械適用）

- **時間窓**: シグナルは**直近18〜24ヶ月以内**のみ有効。古い実績単独は失格。
- **強シグナル（1つで勢い枠可）**: 直近24ヶ月の資金調達（ラウンド名＋時期が裏取れる）／著名アクセラレータ直近バッチ（YC直近2期等）／公開された急成長指標（ARR・利用者数の前年比、決算/プレス明示）。
- **中シグナル（2つ以上で勢い枠可）**: 信頼メディアの注目/急成長リスト掲載（リスト自体を吟味）／採用の急拡大（複数職種同時・自社採用ページ）／業界アワード直近受賞かつ現役プロダクト。
- **弱シグナル（補強のみ・単独不可）**: SNS言及量、Product Hunt上位、コミュニティ話題。
- 各勢い枠サイトに **シグナル種別＋時期＋裏取りURL** を1行必須。

## 選定基準（Step3で機械的に適用）

採用 = 下記をできるだけ満たすもの。減点 = 満たさないもの。
1. 海外・地域条件に適合（日本語主体LPは地域=日本以外なら除外）
2. 意匠が鮮度を持つ（テンプレ然・古いデザインは除外）
3. **モメンタム判定**（上記階層：時間窓内＋強1 or 中2＋裏取りURL）→ 満たせば `勢い枠`、意匠優秀だが未達/未確認なら `意匠枠`
4. 業界・補足ターゲットに近い
5. 見せ方/構成の型が他候補と被らない（多様性確保）
6. ライブURLが生きている／重複・別ドメイン重複でない

**枠クォータ**: `意匠枠` は最終リストの**最大3割**。`勢い枠` が7割に届かなければ件数を下げる（意匠枠で水増ししない）。

## 除外（明確に落とす）

- 日本語主体のLP（地域指定が日本のときを除く）
- リンク切れ・メンテ画面・ログイン必須で中身が見えない
- 明らかに古い／テンプレそのまま／個人ブログ・記事ページ
- 業界と無関係（"かっこいいだけ"で着想にならないもの）
- ギャラリー内サムネ止まりで実URLに到達できないもの
- **モメンタムが時間窓外の古い実績のみ／弱シグナルのみ／裏取り不能** → `勢い枠`不可（意匠が突出していれば`意匠枠`で最大3割内に限り可）

## サイト名スラッグ

スクショファイル名用。英小文字・数字・ハイフン。例: `linear`, `stripe`, `notion-calendar`。
日本語/記号は使わない。

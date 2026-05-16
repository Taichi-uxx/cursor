## 最短レシピ（HubSpot → Yahoo!広告）

### ゴール
- HubSpotのイベントをYahoo!広告（検索/ディスプレイ）へオフラインCVとして計上する最短手順

### 全体フロー
- 計測ID取得（YCLID または ハッシュ化ID） → 保存 → 連携（CSV / API）

## 事前設定（Yahoo!側）
- アカウント設定で自動タグ（YCLID付与）をON。
- コンバージョンを新規作成し、種別：インポート（名前は後でCSV/APIで指定）を用意。 ads-help.yahoo-net.jp+1

## HubSpotで識別子を保存
### フォーム設定
- すべてのフォームに隠し項目「yclid」（必要なら「email」「phone」も）を追加。

### LPでURLの yclid を拾って保存（例：90日Cookie保持）
```html
<script>
  const y = new URL(location.href).searchParams.get('yclid');
  if (y) {document.cookie = "yclid="+encodeURIComponent(y)+";path=/;max-age="+60*60*24*90;
          const i = document.querySelector('input[name=yclid]'); if(i) i.value = y;}
</script>
```
- ※SafariのITP等でパラメータが落ちないケースもあるので、サーバー側保存も推奨。

## yclid取得のためのタグ・フォームの変更について
- 以下ページのページ下段にスクリプト等が詳しく記載あり
https://ads-help.yahoo-net.jp/s/article/H000044478?language=ja

### スクリプトの全体的な流れ
- ページの読み込み完了後に処理を開始します (window.addEventListener('load', ...)).
- 現在のページのURLに yclid パラメータがあるかを確認します。
もし yclid があれば、その値と**有効期限（90日間）**をセットでブラウザの localStorage に保存します。
- localStorage に保存された yclid、またはURLから直接取得した yclid を、指定されたWebフォームの入力項目（隠しフィールドなど）に自動で設定します。
- ユーザーがフォームを送信すると、yclid の情報も一緒に送信され、広告の成果として計測できるようになります。

### スクリプトの詳細
#### getParam(p) 関数
- この関数は、URLの ? 以降の部分（クエリ文字列）から、指定されたパラメータの値を取得する役割を持ちます。

JavaScript

function getParam(p) {
  // 例：URLが https://example.com/?yclid=abcde の場合
  var match = RegExp('[?&]' + p + '=([^&]*)').exec(window.location.search);
  // p に 'yclid' を渡すと、'abcde' が取得できる
  return match && decodeURIComponent(match[1].replace(/+/g, ' '));
}
- window.location.search: 現在のページのURLの ? から後ろの部分（例: ?yclid=abcde&source=google）を取得します。
- RegExp(...): 正規表現を使い、p= の直後から & が来るまでの文字列を抜き出します。
役割: URLに yclid=xxxxx という部分があれば、xxxxx の部分を取り出します。

#### getExpiryRecord(value) 関数
- この関数は、取得した yclid の値に有効期限を設定するためのオブジェクトを作成します。

JavaScript

function getExpiryRecord(value) {
  var expiryPeriod = 90 * 24 * 60 * 60 * 1000; // 90日をミリ秒に変換
  var expiryDate = new Date().getTime() + expiryPeriod; // 現在時刻から90日後の日時を取得
  return {
    value: value,       // yclidの値
    expiryDate: expiryDate // 有効期限の日時
  };
}
- expiryPeriod: yclid を保持する期間です。このスクリプトでは90日に設定されています。ユーザーが広告をクリックしてから90日以内であれば、そのユーザーのコンバージョンとして計測できます。
役割: yclid の値と、その有効期限をセットにしたデータを作成します。

#### addYclid() 関数
- これがスクリプトの中核となるメインの関数です。

JavaScript

function addYclid() {
  // URLから'yclid'パラメータを取得
  var yclidParam = getParam('yclid');

  // yclidを埋め込むフォーム項目のIDを指定
  var yclidFormFields = ['yclid_field'];

  // ... (中略) ...

  // もしURLにyclidがあれば、有効期限付きでlocalStorageに保存
  if (yclidParam) {
    yclidRecord = getExpiryRecord(yclidParam);
    localStorage.setItem('yclid', JSON.stringify(yclidRecord));
  }

  // localStorageからyclidの記録を読み込む
  var yclid = yclidRecord || JSON.parse(localStorage.getItem('yclid'));

  // yclidが存在し、かつ有効期限内であるかを確認
  var isYclidValid = yclid && new Date().getTime() < yclid.expiryDate;

  // 有効なyclidであれば、フォーム項目にその値を設定
  currYclidFormField.forEach(function (field_obj) {
    if (field_obj && isYclidValid) {
      field_obj.value = yclid.value;
    }
  });
}
- yclidFormFields = ['yclid_field']: ここで yclid を埋め込みたいフォームの <input> タグの id を指定します。通常、type="hidden" の隠しフィールドが使われます。複数のフォームがある場合は、['id1', 'id2'] のようにカンマで区切って複数指定できます。
- localStorage.setItem(...): 広告クリックで取得した yclid をブラウザ内に保存します。これにより、ユーザーが広告をクリックした直後ではなく、後日サイトを再訪問してフォームを送信した場合でも yclid を取得できます。
- isYclidValid: yclid が存在するか、そして有効期限（90日）を過ぎていないかをチェックします。
- field_obj.value = yclid.value: 有効な yclid が見つかった場合、指定したフォーム項目（例：<input type="hidden" id="yclid_field">）の value 属性に yclid の値をセットします。

#### window.addEventListener('load', addYclid);
- この行は、Webページのすべての要素（画像、CSSなど）が完全に読み込まれた後に addYclid 関数を実行するよう指示しています。
役割: ページが完全に表示される前にスクリプトが実行され、まだ存在しないフォーム項目にアクセスしようとしてエラーが出るのを防ぎます。

## 連携方法（選択）
### 1) 手動CSV（まずは試す）
- Yahoo!管理画面のテンプレに従い、以下の列を作成：`YCLID`／`Conversion Name`／`Conversion Time`／`Value`(任意)
- 形式：CSV。 ads-help.yahoo-net.jp株式会社キーワードマーケティング

### 2) Search Ads API
- `OfflineConversionService.upload` にCSVをPOST（20MBまで）。バッチで自動化。 ads-developers.yahoo.co.jp

### 3) DisplayのConversion API
- `hashed_email` / `hashed_phone` / `ifa` / `yclid` のうち最低1つ＋`event_time` を送信（UNIX10/13桁対応）。
- n8nや自前サーバーでHTTP送信。 ads-developers.yahoo.co.jp

## 仕様のツボ（必読）
- 90日ルール：YCLIDは発行から90日のみ有効。リードタイムが長い商材は、**中間CV（例：アポ取得）**をオフラインCVにするのが現実的。 ads-help.yahoo-net.jp株式会社プリンシプル
- 重複と名称：CSV/API側のコンバージョン名は管理画面と一致させる。YCLID重複は多重計上の原因に。 ads-help.yahoo-net.jp
- タイムスタンプ：DisplayのConversion APIは `event_time` のUNIX10/13桁を受理（13桁は下3桁切捨て）。未来時刻は±30秒以内のみ許容。 ads-developers.yahoo.co.jp
- 個人情報：メール／電話はSHA-256で正規化＆ハッシュして送信（小文字・トリム）。同意取得の運用も必須。

## HubSpot ↔ Yahoo! フィールド対応（例）
| HubSpot側 | Yahoo!側 |
|---|---|
| yclid（カスタム） | YCLID |
| 取引ステージ到達日時 | Conversion Time（JSTでもOK。APIはUNIX推奨） ads-developers.yahoo.co.jp |
| 受注金額 | Conversion Value |
| 固定値／変数 | Conversion Name（管理画面で作成した名称） ads-help.yahoo-net.jp |
| email / phone（Display向け代替） | hashed_email / hashed_phone、モバイルは ifa。 ads-developers.yahoo.co.jp |

## 実装パターン（運用のしやすさ順）
1. CSV手動：まずは正しく計上されるか検証。
2. n8n自動化：HubSpotのワークフロー or Webhook →（関数で正規化/ハッシュ）→
   - 検索：`OfflineConversionService.upload` にCSV生成＆POST
   - ディスプレイ：Conversion APIにJSONでPOST（yclid or hashed_email など＋event_time） ads-developers.yahoo.co.jp+1
3. CDP/ツール連携：KARTEやTreasure Data等のコネクタを使ってDisplayのオフラインCVを送る。 
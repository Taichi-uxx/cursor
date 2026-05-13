### 画像生成＆ドライブ格納
- セリフと字コンテをスプレッドシートに入れると自動で素材がドライブに生成できるように
- open ai apiとgasで作成
- 参考：https://rehatchhq.slack.com/archives/C05LGGA3MG9/p1755595547668499

### ペルソナ作成
- gasとgptのAPIを組み合わせてペルソナを自動生成できるように
- 参考：https://rehatchhq.slack.com/archives/C05LGGA3MG9/p1754524548234189

### 競合クエリの検知
- 以前はアドベロでスプシに吐き出したデータをもとに作成しましたが、Yahoo!はアドベロ対象外なのでYahoo!広告スクリプト活用で作成
▼流れ
①Yahoo!スクリプト定期実行
②スプシにクエリレポート吐き出し
③GAS×Gemini APIで競合名を判別・検知
④検知した内容をSlackの該当チャンネルに通知
- 参照：https://rehatchhq.slack.com/archives/C05LGGA3MG9/p1756624923882079
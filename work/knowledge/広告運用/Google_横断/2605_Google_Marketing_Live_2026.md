# Google Marketing Live 2026

## 出典
- URL① (anagrams): https://anagrams.jp/blog/gml2026/
- URL② (ishigurodo): https://ishigurodo.com/2026/05/11/post-5162/
- URL③ (atara): https://www.atara.co.jp/unyoojp/2026/05/google-marketing-live-2026_report/
- 内容: 3社の記事（アナグラム／ishigurodo／アタラ）を統合・重複排除・補完したGML2026レポートまとめ
- 開催: 2026年5月20日（米国時間）／日本時間5月21日午前1時〜キーノート配信

## どんな時に活用できるか
- **AI Mode／AI Overviewsへの広告対応**を顧客に提案するとき（4種の新フォーマットの仕様・対象市場・前提キャンペーン種別）
- **DSA運用アカウントの移行計画**を立てるとき（2026年9月の自動移行に向けたAI Max準備）
- **入札・予算戦略の刷新**を検討するとき（Journey-aware Bidding／Smart Bidding Exploration／Campaign Total Budgets／Demand-led Pacing）
- **計測基盤の再設計**（Meridian / Data Manager API / ECAPI / QFC / ABS / Google Tag Gateway）を提案するとき
- **クリエイティブ運用の効率化**（Asset Studio＋Gemini Omni）の導入支援を進めるとき
- **YouTube Demand Gen（旧デマンドジェネレーション）の評価軸**をCFO／クライアント役員に説明するとき
- **エージェンティックコマース／UCP対応**を小売・旅行系クライアントに提案するとき

## サマリ
GML2026のキーワードは「**Unification（統合性）**」。Geminiを核に、**Search入口（AI Modeの4新フォーマット）→ 購買導線（Universal Cart／UCP）→ 計測（Meridian＋QFC＋ECAPI準拠Data Manager API）→ 運用統合（Ask Advisor）**までを一気通貫させる構図が鮮明になった。AI Overviewsは月間25億人、AI Modeは10億人超が利用し、AI Modeの広告枠は**AI Max for Search／Shopping、P-MAXからしか配信できない**ため、対応の遅れが即機会損失に直結する。入札・予算は**Journey-aware Bidding／Smart Bidding Exploration（ユニークCV+27%）／Campaign Total Budgets（手動調整-66%）／Demand-led Pacing**で自動化が進み、DSAは**2026年9月新規作成停止→AI Maxへ自動移行**が確定。広告主に求められるのは、AIの使い方以上に「**AIが力を発揮できる統合データ基盤**」をいかに早く整えるかである。

## 発表内容一覧
1. AI Mode上の新広告フォーマット4種（Conversational Discovery ads／Highlighted Answers／AI-powered Shopping ads／Business Agent for Leads）
2. Direct Offers パイロット版の拡大（プロモーションバンドル／ネイティブチェックアウト／旅行業界拡大）
3. Merchant Center 新機能（AI Performance Insights／Conversational Attributes）
4. AI Max の本格化（AI Max for Shopping campaigns／AI Max for Travel／AI Brief）
5. DSA（動的検索広告）の段階的廃止と AI Max への自動移行
6. 入札／予算自動化4機能（Journey-aware Bidding／Smart Bidding Exploration／Campaign Total Budgets／Demand-led Pacing）
7. Agentic Commerce：Universal Cart と UCP の Google 全体導入・カテゴリ拡張
8. Affirm／Klarna 統合と Google Pay 経由 Native Checkout
9. AI時代のSEOベストプラクティス（Unique／Helpful／Agent-Ready）
10. YouTube Demand Gen 強化（Google マップ広告枠／Checkout Links 9市場拡大／クリエイター動画の発見＆広告化）
11. YouTube 計測：Engaged-View Conversions／Campaign Type Attribution／Product Feeds Expansion（CV +33%）
12. Asset Studio のマルチモーダル化（Gemini Omni統合／1-Click Creative Testing／自然言語ブリーフ／Adobe・Canva・YouTube Studio・Product Studio・Pameli連携・API）
13. Meridian の GA360 統合（クロスチャネルMMM／シナリオプランニング）
14. Qualified Future Conversions（QFC）／Attributed Brand Searches（ABS）
15. Data Manager API の ECAPI 1.0 準拠／Google Tag Gateway
16. Ask Advisor：Google 広告／Analytics／Merchant Center／Marketing Platform 横断の対話型AI

---

# 1. AI Mode 上の新広告フォーマット（4種）

## 概要
Search関連発表の中核。AI Mode（月間10億人超）・AI Overviews（月間25億人）の利用拡大を背景に、生成AI回答面に広告を組み込む4つの新フォーマットが投入された。Googleの調査では消費者の**75%が「AI Modeでより迅速・確信を持って意思決定できるようになった」**と回答。

## 要点
- **配信前提**：AI Mode広告枠は **AI Max for Search／AI Max for Shopping campaigns／Performance Max（P-MAX）からのみ配信可能**
- 4種すべて当初は米国でのテスト／オープンベータ、英語環境から段階展開
- いずれもGeminiが生成・対話・選定を担う

## 詳細（実装・仕様・数値）

| フォーマット | 役割 | 仕様・例 | 提供状況 |
|---|---|---|---|
| **Conversational Discovery ads（会話型ディスカバリー広告）** | ユーザーのニッチな質問に広告内で対話型回答 | 例：「家を高級スパや雨の森のような香りにしたい。手入れが簡単な方法は？」に対し、Geminiが製品の機能・メリットを生成して回答 | 米国テスト中 |
| **Highlighted Answers（ハイライトされた回答）** | AI Mode が生成する「おすすめリスト」内に広告を埋め込む | 例：語学学習アプリのリサーチ時、高品質な広告がリスト内にシームレスに掲出 | 米国テスト中 |
| **AI-powered Shopping ads** | 高額商品の選択を支援するため、Gemini が**カスタム解説文**を瞬時生成 | 例：エスプレッソマシン検索 → Geminiが最適商品を選び「なぜ最善か」を生成 | 2026年後半 米国展開予定 |
| **Business Agent for Leads（リード獲得向けビジネスエージェント）** | 広告内に対話型ブランドエージェント（チャットボット）を配置 | 例：ビジネススクール検討者が静的フォームの代わりにチャットで質問→Webサイトデータに基づく即時回答→リード化 | 米国オープンベータ |

## 各記事の補足
- **anagrams**：4種をひとまとめにし「米国テスト中／オープンベータ／2026年後半展開」と簡潔に整理。
- **atara**：各フォーマットの**ユースケース例（香りの相談、語学学習アプリ、エスプレッソマシン、ビジネススクール）**を最も具体的に記述。「**配信にはAI Max for Search／Shopping／P-MAXが必須**」という運用上の重要前提を明記。
- **ishigurodo**：この領域は触れず（入札系に特化）。

---

# 2. Direct Offers パイロット版の拡大

## 概要
2026年1月から始まったダイレクトオファーのパイロットを拡張。Chewy／Gap／L'Orealなどが既に活用済みで、買い物検討中のユーザーにお得情報を提示する仕組み。

## 要点
- 対応プロモーション型を拡張：**割引／プレゼント（ギブアウェイ）／地域限定クーポン／商品バンドル（セット販売）**
- **AI Brief** を使い、適切なオーディエンスにバンドル等のオファーを最適配信
- **UCP対応小売向けにネイティブチェックアウト**を追加（広告→決済までシームレス）
- **旅行業界に拡張**：Booking.com、Expedia が AI 旅行計画内で直接オファーを表示

## 詳細（実装・仕様・数値）
- 提供方式：Google 広告にプロモーションをアップロード→AI Brief で訴求／オーディエンスを指示
- 旅行領域は AI を活用した旅行計画フローに統合

## 各記事の補足
- **anagrams**：Direct Offersを「Geminiが動的に割引・ギブアウェイ・ローカルクーポン・商品バンドルを構築」と表現し、Booking／Expediaの参画を明記。
- **atara**：パイロット参画ブランドとして**Chewy／Gap／L'Oreal**を実名で挙げ、3つの拡張軸（バンドル／ネイティブチェックアウト／旅行）に整理。
- **ishigurodo**：言及なし。

---

# 3. Merchant Center 新機能

## 概要
AI検索面でのプレゼンス可視化と、会話型検索への商品データ最適化を支援する2機能。

## 要点
- **AI Performance Insights tool**：自社ブランドのAI面シェアを「**類似ブランドと比較**」して把握
- **Conversational Attributes**：会話型検索向けの商品属性を追加（グローバル提供）

## 詳細（実装・仕様・数値）
- AI Performance Insights：**米国・オーストラリア・カナダ・インド・ニュージーランド**で今後数カ月のうちにロールアウト
- Conversational Attributes：すでにグローバル利用可

## 各記事の補足
- **anagrams**：AI Performance Insights を「AI面での表示状況把握」、Conversational Attributes を「会話型検索向け商品属性追加」と短く整理。
- **atara**：「類似ブランドとの比較」というベンチマーク用途を強調。展開対象国を明記。
- **ishigurodo**：言及なし。

---

# 4. AI Max の本格化

## 概要
Search だけでなく **Shopping／Travel** にも AI Max が拡張。AI Mode 広告枠の配信前提キャンペーンとなり、DSA／ACA／ブロードマッチからの移行先となる。

## 要点
- **AI Max for Shopping campaigns**：新展開
- **AI Max for Travel**：新展開
- **AI Brief**：自然言語で「使用する表現」「避ける表現」「狙う検索」をAIに指示できる新インターフェース
- **AI Mode上の新フォーマット配信は AI Max／P-MAX が必須**

## 詳細（実装・仕様・数値）
- AI Brief は今後のキャンペーン構築の中心UIになる位置付け。プロンプト設計力がそのまま運用品質に直結。

## 各記事の補足
- **anagrams**：AI Max を独立セクションで扱い、DSA移行スケジュールと一体で整理。
- **atara**：AI Brief を「マーケターの言語化能力が試される部分」と評価。AI Mode配信前提の論点を強調。
- **ishigurodo**：言及なし。

---

# 5. DSA（動的検索広告）の段階的廃止と AI Max への自動移行

## 概要
DSA・ACA・ブロードマッチ系キャンペーンを順次 AI Max に集約する大型ロードマップ。

## 要点
- **2026年9月：新規 DSA の作成停止**
- **既存 DSA／ACA／ブロードマッチを AI Max へ自動移行**
- **anagrams は「6月中の着手」を推奨**（移行検証期間を確保）

## 詳細（実装・仕様・数値）
- 移行は段階的だが、既存資産の特性（除外URL／ターゲットページ／カスタムラベル等）が AI Max でどう扱われるかの検証が必須
- AI Mode新フォーマットの配信前提でもあるため、移行は「いつかやる」ではなく**広告枠アクセス権の獲得**に直結

## 各記事の補足
- **anagrams**：このスケジュールを最も明確に記載。運用者向けに**「DSA運用アカウントは6月着手推奨」**と具体アクションを提示。
- **atara／ishigurodo**：明示的なDSA廃止スケジュールへの言及は薄め。

---

# 6. 入札／予算自動化（4機能）

## 概要
Googleが「**2025年以降、Search・Shoppingの入札戦略に20以上の改善**」を加えた延長線上での発表。4機能で「ジャーニー全体の学習」「探索の拡大」「期間予算」「需要連動配分」を一気に進める。

## 要点・詳細

| 機能 | 対象 | 中身 | 数値・効果 | 提供状況 |
|---|---|---|---|---|
| **Journey-Aware Bidding** | Search（Target CPA） | リード→販売までの全行程をAIが学習。**フォーム送信後の電話問い合わせや契約成立**も学習に組み込む | 複数CVポイントのトラッキングが利用条件 | ベータ提供中 |
| **Smart Bidding Exploration 拡大** | P-MAX／Shopping（Searchで既存実績あり） | tROAS の許容幅を設定し、**通常では入札に勝てなかったクエリからもCVを獲得** | Searchで**平均27%多くのユニークCVユーザー獲得** | P-MAXベータ中、Shoppingは数週間後 |
| **Campaign Total Budgets** | Search／Shopping／P-MAX | 日予算ではなく**期間全体の合計予算**を設定（セール期間等に有効） | **手動の予算調整が平均66%削減** | 全キャンペーンに展開済み |
| **Demand-Led Pacing**（=Demand-led Budget Pacing） | Search／Shopping | AIが消費者の需要パターンを予測し、**需要が高い日は多く、低い日は抑える**動的配分 | 月間バジェット上限／日次支出上限は維持 | 今後数カ月内に導入予定 |

## 各記事の補足
- **ishigurodo**：4機能を**ステータス表で整然と整理**し、各機能の利用条件・効果を最も詳しく解説（特に Journey-Aware Bidding の利用条件＝複数CVポイント計測、Demand-Led Pacing の安全装置＝月間／日次上限保持）。
- **anagrams**：「手動調整-66%」「ユニークCV+27%」の主要数値を明記。
- **atara**：入札系の機能名列挙は薄め。代わりに杉原氏のコメントで「Geminiが全プロダクトをスーパーチャージ」と俯瞰的に位置付け。

---

# 7. Agentic Commerce：Universal Cart と UCP の Google 全体導入

## 概要
**Universal Cart**＝小売業者・検索・Geminiを横断するインテリジェントなショッピングカート。**UCP（Universal Commerce Protocol）**＝AIエージェントが小売横断で商品検索・カート追加・決済を一気通貫で実行できるGoogle主導のオープンプロトコル。

## 要点
- 数タップで Google Pay 決済も可、小売業者サイトへ遷移完結も可
- UCP は**広告キャンペーンにも統合**：Direct Offers の限定プロモーション、YouTube Demand Gen の商品フィードからその場で購入可
- 参画パートナー：**Nike、Sephora、Target、Ulta Beauty、Walmart、Wayfair、Shopifyマーチャント（Fenty、Steve Madden 等）**
- **展開時期**：米国 2026年5月19日から開始、英国・カナダ・オーストラリアに数か月内に拡大
- **新カテゴリ拡張**：従来の小売中心から **ホテル予約／地域フードデリバリー** に拡大
  - 数カ月内に **Search の AI Mode からホテル予約**、**Google マップでの会話からフードデリバリー注文** が可能に
- 決済機能：**Affirm／Klarna**（後払い）統合、Google Pay 経由 **Native Checkout** 導入

## 詳細（実装・仕様・数値）
- UCP はオープンプロトコル。Googleが業界全体に開く形をとり、Agentic Commerce のインフラを先に押さえる戦略
- atara 杉原氏は「**広告から購入完了まで離脱なし**というエージェンティックコマースのゴールに、現実のプロダクトとして大きく近づいた」と評価

## 各記事の補足
- **anagrams**：パートナー実名（Nike／Sephora／Target／Ulta／Walmart／Wayfair／Shopify系）と決済機能（Affirm／Klarna／Google Pay Native Checkout）、米国2026年5月19日開始の具体日付を明記。
- **atara**：UCPを「Search入口→チェックアウト出口→計測フィードバック」の統合戦略の中核として位置付け。**OpenAI など新興プレイヤーが広告・コマース領域に本格参入する前にスタックを先回りで固める意図**を読み解く独自視点。
- **ishigurodo**：言及なし。

---

# 8. AI時代のSEOベストプラクティス（Unique / Helpful / Agent-Ready）

## 概要
Agentic Commerce関連で言及された、AI／LLM時代の自社サイト整備指針。

## 要点
- **Unique**：一般的なありふれた情報を避け、自社ブランドだからこそ語れる具体的・唯一無二のコンテンツを主軸に
- **Helpful**：検索エンジンのボット向けではなく、**顧客にとって最も役立つコンテンツ**に焦点
- **Agent-Ready**：AIエージェントにも理解しやすいよう、**コンテンツの構造化／アクセス・ナビゲーション容易性／正確なデータフィードの維持**を整備

## 各記事の補足
- **atara**：唯一明記。Agentic Commerceセッションの一部として整理。
- **anagrams／ishigurodo**：言及なし。

---

# 9. YouTube：Demand Gen の強化

## 概要
YouTube は「**独自オーディエンス × 高いアテンション**」を兼ね備えたパフォーマンスマーケティング基盤。Demand Gen（旧デマンドジェネレーション）を3つの問いで再定義した。

## 要点（3つの問い）
1. **なぜ YouTube がパフォーマンスマーケに最適か？**
   - YouTube Shorts 視聴者の **45% は TikTok を利用していない**、**65% は Reels を利用していない**
   - 受動スクロールではなく目的を持って視聴 → 広告注目度も購買決定もより良い
2. **Demand Gen で最高のパフォーマンスを出すには？**
   - **Google マップ広告枠への配信**（周辺検索ユーザーとの接続）
   - **Checkout Links を9つの新市場に拡大**（「発見→購入」を少クリックで）
   - キャンペーン設定時に**ブランド起用クリエイターの動画を発見→広告として追加**可
   - **Product Feeds Expansion**：平均 **+33% のCV増加**
3. **CFOが納得する成果の示し方は？**
   - **Engaged-View Conversions**：YouTubeでは「**5秒以上視聴**」を確かなエンゲージメント基準に
   - **Campaign Type Attribution**：Demand Gen が他チャネルと並行して CV にどう貢献したかを明確化。サードパーティツール連携で客観検証も可
   - **Demand Gen発のCVのうち、最初の30日間で発生するのは40%のみ**。残り60%は長期で創出 → CFO説得材料に

## 詳細（実装・仕様・数値）
- 「ラストクリックCV以外を評価のより所にし、中長期ROIを可視化する」運用思想の転換を伴う

## 各記事の補足
- **atara**：3つの問い構造で最も網羅的。**Shorts視聴者の45%/65%、最初30日でCV発生40%**という独自数値を明記。星野コメントで「短期CPA評価と長期視点の両立」という現場ジレンマを言語化。
- **anagrams**：**Product Feeds Expansion 平均33%CV増**、Campaign Type Attribution、Uplift Experiments の存在を明記。
- **ishigurodo**：言及なし。

---

# 10. Creative：Asset Studio のマルチモーダル化

## 概要
Google 広告のクリエイティブアセット開発のワンストップソリューション。マーケティングプラン／ブランドガイドライン／Webサイト／目標を理解し、自然言語で生成・調整。

## 要点
- **連携先**：YouTube Studio、Product Studio、Pameli、**Adobe**、**Canva**。エンタープライズ向け**API**も提供
- **Gemini Omni 統合**：動画も画像・テキストと同インターフェース内で生成
- **1-Click A/B Testing（Creative Testing）**：新規素材とトップパフォーマー素材を自動比較
- **自然言語ブリーフ**：ブランドガイドラインから自動でクリエイティブ生成

## 詳細（実装・仕様・数値）
- **2026年夏、英語環境から世界各国に順次展開**
- atara 星野氏：「インハウスマーケターは同じ時間でより多くの**質の高いクリエイティブ検証**を回せる」一方、「**広告主側のAI活用ルール整備度合いで活用度が変わる**リスク」を指摘

## 各記事の補足
- **atara**：連携先の最も網羅的なリスト（**YouTube Studio／Product Studio／Pameli／Adobe／Canva＋API**）と、Gemini Omni 統合の意味を解説。
- **anagrams**：1-Click Creative Testing と自然言語ブリーフを明記。「クリエイティブ運用を**ブリーフィングと検証中心に再設計**」というアクション示唆。
- **ishigurodo**：言及なし。

---

# 11. Data and Measurement：3つの軸（Data Strength／Causality／Unified View）

## 概要
計測領域では「**データの強度／因果関係／統合された視点**」の3点が重要と位置付けられた。AI効果の最大化には信頼できるタイムリーなシグナルが不可欠。

## 要点

| 機能・指標 | 役割 | 数値・事例 |
|---|---|---|
| **ファーストパーティデータ活用** | 正確なデータでGoogle広告を最適化 | **インクリメンタルROAS（増分効果）が平均+11%**。事例：Dr. Martens が 1stP データを P-MAX 連携し**収益+16%** |
| **Meridian の GA360 統合** | MMM／マルチタッチアトリビューション／Liftデータを統合。**TikTok／Pinterest／Snap** などクロスチャネル分析、**シナリオプランニング**機能 | 全言語対応でグローバル展開 |
| **Attributed Brand Searches（ABS）** | 広告接触→ブランド検索の直接的つながりを可視化。**短期影響**追跡指標 | 新発表 |
| **Qualified Future Conversions（QFC）** | ブランド検索／動画視聴／Web訪問などのシグナルをAI分析し、**最大6カ月先の予測CV**を結びつける。**長期影響**指標 | 限定パイロット中、2026年中にベータ拡大予定 |
| **Data Manager API** | 全データソースを1カ所に集約。**IAB Tech Lab の ECAPI 1.0 準拠** | マルチプラットフォーム共通仕様化 |
| **Google Tag Gateway** | 計測シグナルを保護（広告ブロッカー／ブラウザ制限対策）。**オフラインCRMデータ統合**で結合 | — |

## 詳細（ECAPI の意味＝杉原コメントから）
- ECAPI（Event and Conversion API）は **2026年3月にIAB Tech Labが1.0として確定**したサーバー間CV送信の業界標準
- 共同策定：**Meta、Google、Walmart、TikTok、Roku** など主要プラットフォーム
- これまで Meta CAPI／Google Enhanced Conversions／TikTok Events API など個別仕様乱立 → **ECAPIで一つの仕様で複数プラットフォームに配信できる「共通言語」が確立**
- IAB Tech Lab のエージェンティック広告ロードマップに直接組み込まれており、「**AIエージェントがリアルタイムCVシグナルを受け取り、自律的に入札・クリエイティブを最適化**」する前提インフラとして設計
- Googleが ECAPI 1.0 確定からわずか2カ月で準拠 → 業界標準採用シグナル
- **広告主目線**：Data Manager API への投資が「Googleだけのためのもの」ではなく「マルチプラットフォーム共通の計測基盤」となり、投資対効果が一段高まる

## 各記事の補足
- **atara**：3軸（Data Strength／Causality／Unified View）の全体フレーム、ファーストパーティデータの+11%／Dr. Martens +16%事例、ECAPI の業界標準化の意味を最も詳しく解説。
- **anagrams**：QFC・ABS・Meridian・Data Manager API（ECAPI 1.0準拠）の存在を簡潔に整理。
- **ishigurodo**：言及なし。

---

# 12. Ask Advisor：4プロダクト横断の対話型AI

## 概要
Google 広告／Google アナリティクス／Merchant Center／Google Marketing Platform に横串で配置される対話型AIアシスタント。自然言語で複数プロダクト横断のキャンペーン構築・分析が可能。

## 要点
- 例1（GA360）：「**次の四半期の予算配分はどうすべき？**」と聞く → Meridian を用いたインサイト提供からキャンペーン立ち上げまで実行
- 例2（Google広告×Merchant Center）：「**ヘアケア製品の新規顧客を見つけたい**」 → Merchant Center から商品情報を自動取得し、Google広告で新キャンペーン設定。**アイデア出しからキャンペーン開始まで数クリック**
- **提供状況**：英語アカウント向けベータ版。今後数カ月で新機能順次展開
- atara 星野氏：「AIは**こちらが問いかけないことには自発的に教えてくれない**」=自社マーケ全体像の理解と問いの立て方が成否を分ける

## 各記事の補足
- **atara**：2つの具体的ユースケース（予算配分相談／ヘアケア新規顧客）を提示。AIへの問いの立て方の重要性を強調。
- **anagrams**：「Ask Advisor＝4プロダクト統合エージェント」として位置付け、複数プロダクト横断のキャンペーン自動構築の意義を明示。
- **ishigurodo**：言及なし。

---

# 13. GML2026を貫く方向性とアタラの総括

## 概要
3社それぞれが提示した「総括観点」を統合する。

## 要点

### anagrams：3つの方向性
1. **AIの深化**：構築・最適化・分析の横断的自動化
2. **測定・予測精度向上**：短期＋アッパーファネル＋未来予測の3層構造
3. **ショッピング・クリエイティブ効率化**：発見から購買までの摩擦排除

### anagrams：運用者の3アクション
1. **商品フィード・ファーストパーティデータの整備**（+11% ROAS 実績）
2. **計測フレームの再設計**（短期CV一本足からの脱却）
3. **クリエイティブ運用を「ブリーフィングと検証」中心に再設計**
4. **DSA運用アカウントは6月中の着手を推奨**（9月自動移行に備える）

### atara 杉原コメント：Unification（統合性）
- データ・プロダクト・計測の統合、Geminiによる全プロダクトのスーパーチャージ、Ask Advisorによるワンストップ化
- **Search入口 → チェックアウト出口 → 計測フィードバック**までを Gemini と UCP で一気通貫
- OpenAI など新興プレイヤーの本格参入前にエージェンティック時代のスタックを先回りで固める競争戦略
- ECAPI 1.0 準拠は Google が「**独自仕様囲い込みではなく業界標準採用**」を選んだ重要シグナル
- 享受側にも代償：AI Max for Search／Shopping、P-MAX 整備、UCP 統合、Ads／GA／MC／GMP のデータ整備、ECAPI 準拠 Data Manager API への移行が事実上必須

### atara 星野コメント：実用フェーズへ
- 商品データを基にした画像・動画生成のクオリティ向上 → インハウスマーケターのクリエイティブ検証回転数が増加。ただし**広告主側のAI活用ルール整備度合い次第**でフル活用度に差
- **AI Mode広告枠は AI Max 関連からしか出ない → 導入の遅れ＝機会損失**
- **AI Brief への情報の与え方＝マーケターの言語化能力**が試される
- データ領域：**UCP／MMM／Ask Advisor は新鮮で正しいデータがあってこそ効果発揮**。Google アナリティクスを**あらゆるデータのハブ**にしたい Google の意図
- YouTube：30日内CVが40%のみという長期データと、現場の短期CPA評価のジレンマ。**ラストクリック以外を評価軸**にする姿勢が必要

---

## 太一の示唆

1. **DSA運用アカウントの棚卸しを今月中に完了する**。9月新規作成停止＋既存自動移行が確定しているため、AI Max への移行検証ウィンドウは実質「6〜8月の3ヶ月」しかない。除外URL・ターゲットページ・カスタムラベル・CVデータ品質を「AI Max でどう振る舞うか」観点で再評価し、各クライアントごとに移行プランを作る。

2. **AI Max for Search／Shopping、P-MAX のアカウント全展開を優先KPI化する**。AI Mode 新フォーマット（Conversational Discovery／Highlighted Answers／AI-powered Shopping／Business Agent for Leads）は **AI Max／P-MAX からしか配信できない＝広告枠アクセス権そのもの**。米国限定とはいえ、対応キャンペーンを持たないアカウントは半年後の機会損失が確定するため、「日本未対応でも先行整備」を提案する。

3. **AI Brief を前提にした「指示書テンプレ」をクライアント別に整える**。AI Brief は「使う表現／避ける表現／狙う検索」を自然言語で渡す入口。マーケターの言語化能力が運用品質を直接決めるため、**ブランドトーン・NGワード・指名／非指名分離・購入意図シグナル**などをテンプレ化して再利用可能にする。これは「広告運用者の新しい職能」として明確に位置付ける。

4. **入札・予算自動化4機能の試験運用ロードマップを作る**。Journey-aware Bidding（複数CVポイント計測が前提）、Smart Bidding Exploration（tROAS許容幅で+27%ユニークCV）、Campaign Total Budgets（手動調整-66%）、Demand-led Pacing。クライアントごとに「**どのCVをトラッキングできているか／許容幅をどれだけ取れるか／期間予算が活きるイベントカレンダーは何か**」を整理し、ベータ提供順に当てはめる。

5. **ファーストパーティデータ統合プロジェクトをCS提案の標準メニューに格上げする**。インクリメンタルROAS +11%、Dr. Martens の収益 +16% は「広告運用の枠を超えた経営インパクト」として通る数字。**Data Manager API 経由の ECAPI 準拠移行**を Meta／TikTok と同時提案できれば、「Google だけのため」ではない投資対効果として説得力が出る。

6. **計測の二段構え（ABS＝短期影響／QFC＝最大6カ月先の予測）を提案資料に組み込む**。クライアント役員・CFO が短期CPAに偏った評価をしている案件ほど、QFCで「**長期価値の見える化**」を訴求する余地が大きい。特に YouTube Demand Gen は「最初の30日で40%、残り60%は長期」というアタラ提示の数値を持って交渉できる。

7. **YouTube Demand Gen を「指名検索／純広以外の第3チャネル」として再評価する**。Shorts視聴者の45%がTikTok非利用／65%がReels非利用＝**他SNSではリーチできない独自層**。Engaged-View Conversions（5秒以上視聴）と Campaign Type Attribution で短期CPA以外の評価軸を作り、Google マップ広告枠と Checkout Links 拡大を実装に組み込む。

8. **Asset Studio 導入を見据え、「ブランドガイドライン×商品データ×NGリスト」のクリエイティブブリーフ資産化を進める**。Gemini Omni で動画まで自然言語生成できるようになる前提で、**入力の品質**が出力の品質を決める。Adobe／Canva 連携前提のワークフロー再設計と、1-Click A/B Testing のプロセス組み込みを並行で準備する。

9. **Ask Advisor を見越して、Ads／GA／Merchant Center／Marketing Platform の「データ統合度監査」を全クライアントで実施する**。星野コメント通り、AI は問いに答えるだけで自発的にデータの欠損を教えてくれない。**Ask Advisor をフル活用できる状態にしておくこと自体が、AI時代の競争優位**になる。GA への各種データソース集約を急ぐ。

10. **UCP 対応の小売・旅行クライアントには「決済導線統合」を新規論点として提案する**。日本展開はまだ先だが、**Booking／Expedia／Affirm／Klarna／Google Pay Native Checkout** の組み合わせは「広告から購入完了まで離脱なし」というゴールに直結。海外展開／越境ECクライアントには即座に検討課題化する。

11. **「AIが力を発揮できる統合データ基盤」を経営アジェンダとして提案する文脈を持つ**。GML2026の本質メッセージは「AIの使い方」ではなく「**AIが効くデータ基盤を持っているか**」。CS としてクライアント経営層に対し、データ統合・ECAPI移行・1stPデータ整備を**広告予算とは別予算**で取りに行く構造を作る。

12. **3記事を読み比べた所感を社内ナレッジに残す**：anagrams は数値と運用アクションが具体的、ishigurodo は入札系を最も詳細に解説（特に Journey-Aware Bidding の利用条件＝複数CVポイント計測の必須要件）、atara は ECAPI／UCP の戦略的意味付けが秀逸。**運用者向けには ishigurodo、戦略・経営層向けには atara、現場展開には anagrams**、と引用元を使い分けると説得力が増す。

---

## 補足：3記事の網羅マトリクス

| トピック | anagrams | ishigurodo | atara |
|---|:---:|:---:|:---:|
| AI Mode 新フォーマット4種 | ○ | − | ◎（事例詳細） |
| Direct Offers 拡張 | ○ | − | ◎（参画ブランド名） |
| Merchant Center 新機能 | ○ | − | ○（展開国） |
| AI Max（Shopping／Travel／Brief） | ○ | − | ◎ |
| DSA 廃止スケジュール | ◎（6月着手推奨） | − | △ |
| 入札・予算自動化4機能 | ○ | ◎（最詳細） | △ |
| Universal Cart／UCP | ◎（パートナー実名） | − | ◎（戦略解説） |
| Affirm/Klarna／Native Checkout | ○ | − | ○ |
| SEO（Unique/Helpful/Agent-Ready） | − | − | ◎ |
| YouTube Demand Gen 強化 | ○ | − | ◎（3つの問い） |
| Asset Studio（Gemini Omni） | ○ | − | ◎（連携先網羅） |
| Meridian／QFC／ABS | ○ | − | ◎ |
| Data Manager API／ECAPI | ○（言及） | − | ◎（業界標準論） |
| Google Tag Gateway | − | − | ○ |
| Ask Advisor | ○ | − | ◎（具体例2件） |
| 杉原／星野コメント | − | − | ◎ |

→ **入札系の深掘りは ishigurodo、戦略・思想層は atara、現場アクション化は anagrams** が最も価値が高い。

---

## 補足：覚えておくべき主要数値（クイックリファレンス）

- **AI Overviews 月間 25億人 / AI Mode 月間 10億人超** 利用
- AI Mode 利用者の **75%** が「より迅速・確信を持って意思決定できる」
- Smart Bidding Exploration：Search で **平均 +27% のユニークCVユーザー**
- Campaign Total Budgets：**手動の予算調整 -66%**
- YouTube Shorts 視聴者の **45% は TikTok 非利用 / 65% は Reels 非利用**
- Demand Gen 発のCVのうち、最初の **30日間で発生するのは 40%** のみ
- Engaged-View Conversions：**5秒以上視聴** を確かなエンゲージメント基準に
- Demand Gen の **Product Feeds Expansion で平均 +33% CV増**
- ファーストパーティデータ活用で **インクリメンタル ROAS 平均 +11%**
- Dr. Martens：1stP データを P-MAX 連携で **収益 +16%**
- QFC：**最大 6カ月先** の予測コンバージョン
- ECAPI 1.0：**2026年3月確定** → Google は **わずか 2カ月で準拠**
- DSA：**2026年9月 新規作成停止**、既存は AI Max へ自動移行
- Asset Studio：**2026年夏、英語環境から順次展開**
- Universal Cart：**米国 2026年5月19日開始**、英・加・豪に数か月内に拡大

---

## 補足：日本市場での実務影響（CS視点の論点整理）

- **AI Mode 関連の新4フォーマットは現時点で米国限定**。ただし AI Max／P-MAX の整備自体は今からできる。**「日本展開時にゼロから対応するか／既に整っているか」が半年〜1年の差を生む**。
- **DSA 自動移行は日本アカウントにも適用見込み**。**英語UI／米国アカウント基準でアナウンスされた変更は、日本でも数週間〜数ヶ月遅れで適用される**のが慣例。クライアント説明資料に「日本展開時期は別途確認」と注記しつつ、**移行計画は前倒しで進める**のが現実解。
- **入札系4機能（特に Campaign Total Budgets）は日本でも展開済み**。**セール／キャンペーン期間のあるEC・サブスク系クライアントから順次試験運用**できる。
- **Meridian の GA360 統合は日本でも GA360 契約クライアントから順次活用可**。MMM 提案を持っていけば**広告予算の最適配分という上位レイヤーの議論**に持ち込める。
- **UCP／Universal Cart は日本展開未定**。ただし**越境EC／インバウンド関連クライアント**には海外動向として早めに共有しておくと、競合との情報差別化になる。
- **Ask Advisor は英語アカウント限定**。日本語対応待ちだが、対応時に「すぐ使える状態」にしておくには **GA・Ads・MC・GMP のデータ統合度**が前提。**今のうちに統合度監査を済ませる**のがコスパ最良。

# 研究インデックス

このページは「今なにを研究しているか」を忘れないための入口です。  
詳しい生データ、個人情報、元ドキュメント、元チャート画像は公開せず、GitHub には公開してよい概要と次の作業だけを残します。

## 運用ルール

- 会話で出た研究メモは、公開してよい形に要約してこの研究インデックスへ反映する
- 個人情報、元ドキュメント、元チャート画像、匿名化前データは GitHub に載せない
- 「研究の問い」「途中経過」「次にやること」を必ず残す
- 新しい発見は、あとから教材・検証・Pine 化のどれに使うか分けて記録する

## いまのアクティブ研究（2026-06〜）

**心理・恐怖ゾーン・受講生マップ一連はフラット化（アーカイブ）。**  
新規は収益のみ → **[ORIGINAL_RESEARCH_2026-06.md](ORIGINAL_RESEARCH_2026-06.md)**

| 区分 | 入口 |
|------|------|
| **オリジナル研究（本線）** | [ORIGINAL_RESEARCH_2026-06.md](ORIGINAL_RESEARCH_2026-06.md) |
| **A-path 最終判断** | [original_a_path_DECISION_2026-06-01.md](original_a_path_DECISION_2026-06-01.md) |
| **本番運用・数値** | [ultimate_method_v1_2026-06-01.md](ultimate_method_v1_2026-06-01.md) |
| ~~踏み上げ・投げ切り（SQZ）~~ | **退役** — [DECISION（RETIRED）](cap_sqz_thorough_validation_2026-06-01/DECISION.md) ／ [ローソク足（教材）](market_psychology_capitulation_squeeze_candlestick_2026-06-01.md) |
| **系統B（10レーン）** | [system_b_lanes_validation_2026-06-01/DECISION.md](system_b_lanes_validation_2026-06-01/DECISION.md) |
| **系統B 本番運用** | [operations/system_b/README.md](../operations/system_b/README.md) |
| **系統B B06 Pine照合** | [DECISION_b06_tv_oanda_parity.md](system_b_pine_parity_2026-06-01/DECISION_b06_tv_oanda_parity.md) |
| **Lower High 3 Touch 仮説** | [lower_high_three_touch_breakdown_hypothesis_2026-06-08.md](lower_high_three_touch_breakdown_hypothesis_2026-06-08.md) ／ [B抜け危険除外](lower_high_b_break_danger_filters_2026-06-08/REPORT_ja.md) ／ [B床化確認](lower_high_b_support_confirmation_2026-06-08/REPORT_ja.md) ／ [確認フィルタ勝率PF](lower_high_synapse_confirm_filters_2026-06-08/REPORT_ja.md) ／ [赤LINE勝率PF](lower_high_synapse_reclaim_long_strategy_2026-06-08/REPORT_ja.md) ／ [下抜け実測](lower_high_three_touch_breakdown_2026-06-08/REPORT_ja.md) ／ [上抜けロング実測](lower_high_synapse_reclaim_long_2026-06-08/REPORT_ja.md) ／ [Synapse接続](lower_high_synapse_bridge_2026-06-08.md) |
| **上位足戻し x 下位足H&S 仮説** | [MTF Pullback H&S 可視化Pine](../../pine/research/mtf_pullback_head_shoulders_visual_v0_1.pine) |
| **旧心理スプリント（参照のみ）** | [ARCHIVE_psychology_sprint_2026-05_06.md](ARCHIVE_psychology_sprint_2026-05_06.md) |

## 次にやること

1. **本番** — TB baseline のまま + **T5優先**（重複時はT5）— [DECISION](original_a_path_DECISION_2026-06-01.md)
2. **TB に追加フィルタを入れない**（検証で総R↓のみ）
3. ~~SQZ フォワード~~ — 退役（2026-05-31）
4. Lower High 3 Touch は、XAUUSD H4で `LINE上抜け + B抜け + Aまで0.5R以上` をENTRY候補にし、D1 EMA20上を強い追い風ラベル、終値位置60%以上を軽い品質ラベルとしてTradingViewで目視照合する
5. 上位足戻し x 下位足H&S は、H4/D1の戻し背景と下位足H&Sのネックライン候補が、人間の目で見た「戻しの終わり」に近いかをTradingViewで目視照合する

## 進捗ログ（アクティブ）

| 日付 | 研究テーマ | 進捗 | 次の判断 |
|---|---|---|---|
| 2026-06-01 | **A-path 決定** | TBフィルタ追加却下。**T5優先**採用 +212.7R vs TB単体 +194.6R。 | [DECISION](original_a_path_DECISION_2026-06-01.md) を運用に固定 |
| 2026-06-01 | **フラット化** | 心理スプリントを [ARCHIVE](ARCHIVE_psychology_sprint_2026-05_06.md) へ。 | — |
| 2026-06-08 | **Lower High 3 Touch Breakdown** | H1/H4で3回の高値切り下げ後、下降ライン3回目タッチから下抜けした場合、次legの下落幅が大きいかを検証する仮説メモとPine Event scanner v0.1を追加。 | XAUUSD H1/H4で発火位置を目視確認し、24/48/120本のMFE/MAEを見る |
| 2026-06-08 | **Lower High 3 Touch 実測** | 1578イベントを実測。H1 MFE48中央値3.18ATR、H4 MFE48中央値2.93ATR。ただしMFE48/前2leg平均はH1 0.77倍、H4 0.88倍で、広い条件の売り継続仮説は未支持。 | ラインを上抜けない売り継続と、ライン上抜け+水平線BのSynapse転換を分けて測る |
| 2026-06-08 | **Lower High x Synapse 接続** | LH3下降ラインがSynapse手法の初期斜めラインに近いと発見。LINE上抜け、B水平線、A水平線を分けて見る研究用Pineを追加。 | XAUUSD H1/H4で、LINE/B/Aの表示が人間の目に近いか確認 |
| 2026-06-08 | **LH3赤LINE上抜けロング実測** | 赤いLH3下降LINEを終値で上抜けた足をロング仮エントリーとして2389件実測。H4はMFE48 3.34ATR、MAE48 2.78ATR、fwd48 +0.40ATRでH1より良い。XAUUSD H4とSILVER H4が強い。 | B水平線、A水平線、戻り確認を足して再測定 |
| 2026-06-08 | **LH3赤LINE上抜け 勝率/PF** | SL/TPを置いて14334シナリオを検証。H4全体RR2/120本は勝率40.21%、PF1.07。XAUUSD H4 RR2/120本は勝率49.53%、PF1.52、+26.70R。SILVER H4 RR1/120本は勝率63.64%、PF1.54。 | XAUUSD H4を中心にB水平線、A水平線、戻り確認で絞る |
| 2026-06-08 | **LH3 Synapse確認フィルタ 勝率/PF** | 赤LINE後の確認条件を比較。H4 B水平線上抜け RR2/120本は勝率44.72%、PF1.22、+60.14R。H4 B水平線 RR2/48本は勝率48.66%、PF1.23、+48.82R。XAUUSD H4 B水平線 RR2/48本は勝率63.38%、PF2.58、+28.93R。 | 赤LINE上抜け単体は本番化しない。XAUUSD H4 B水平線を本命候補として、A水平線と浅い戻りは補助フィルタ扱いで目視照合する |
| 2026-06-08 | **LH3 B床化確認 勝率/PF** | B抜け即、B床化後再上昇、A/H3上抜けを比較。H4 B抜け即 RR2/120本は勝率44.72%、PF1.22、+60.14R。H4 B床化 RR2/120本は勝率46.70%、PF1.20、+20.58R、最大DDは34.84Rから14.88Rへ低下。H1 B床化 RR1.5/120本はPF1.16、最大DD13.49R。 | H4はB抜け即を本線、B床化はDD低減補助。次はXAUUSD H4で、巨大足・Aまで距離不足・D1抵抗直下などの除外条件を見る |
| 2026-06-08 | **LH3 B抜け即 危険除外** | XAUUSD H4 RR2/48で、baselineは71件・勝率63.38%・PF2.58・+28.93R・最大DD5.55R。A余白0.5Rは58件・勝率67.24%・PF2.98・+26.45R・最大DD2.50R。D1 EMA20上はPF3.52だが32件。 | [ENTRY候補Pine](../../pine/research/lower_high_synapse_b_danger_filter_visual_v0_1.pine) で、A余白0.5R・D1 EMA20・終値位置60%以上を目視照合 |
| 2026-06-08 | **上位足戻し x 下位足H&S** | 新規仮説。上位足では戻しに見える場所を背景で出し、その中の下位足H&S/逆H&Sを後から確認するPine v0.5を追加。v0.5は上位足EMA20-EMA50の戻し帯をfill表示し、上下端ラインとテーブル数値でも表示確認できるようにした。 | まずXAUUSDとUSDJPYで、D1戻し帯が人間の目に近いか確認する |

## 進捗ログ（アーカイブ — 心理スプリント 2026-05〜06）

| 日付 | 研究テーマ | 進捗 | 次の判断 |
|---|---|---|---|
| 2026-06-01 | 恐怖ゾーン未来運用 | Live v1.0.4 等 — 詳細は ARCHIVE | 新研究では使わない |
| 2026-06-01 | 心理マップ実践検証 | TBフィルタは総R↓ — 詳細は ARCHIVE | 同上 |
| 2026-06-01 | 恐怖・損切・どテン可視化 | 教材・可視化まで完了 | 同上 |
| 2026-05-31 | トレード心理研究 | 失敗チャートの代表例7ケースをローカルで選び、可視化第一版を作成。公開版には画像・元データは載せない。 | 代表ケースごとに「実際の入口」「本来待つ場所」「損切り位置」を手動でより正確に重ねる |
| 2026-05-31 | トレード心理研究 | 代表7ケースに、赤=実際の入口、青=本来待つ場所、黄=損切り位置、緑=次回ルールの手動マーキング下書きをローカルで作成。 | 位置を微調整したあと、教材化できるケースと研究保留ケースに分ける |
| 2026-05-31 | トレード心理研究 | 代表7ケースを仕分けし、優先教材3ケース、教材候補3ケース、研究保留1ケースに分類。優先教材3ケースの1枚教材下書きをローカルで作成。 | 優先教材3ケースの文章を調整し、教材として使える形に整える |
| 2026-05-31 | トレード心理研究 | 優先教材3ケースについて、完成版テキストと完成版カードをローカルで作成。テーマは「節目抜けですぐ入らない」「レンジ内の急落に反応しない」「ローソク足1本だけで決めない」。 | 受講者に伝わりやすい短い表現へ整える |
| 2026-05-31 | トレード心理研究 | 失敗パターン3ケースをPine可視化プロトタイプに変換。赤=失敗しやすい入口、緑=待てた場合の候補として表示する設計。 | TradingView上で目視確認し、赤と緑の出方を調整する |
| 2026-05-31 | トレード心理研究 | TradingViewで初期版を確認し、表示が多すぎてチャートが読みにくい問題を確認。Pineをv0.2へ改善し、ラベル初期OFF、背景初期OFF、同種サイン間引き、C07条件の厳格化を実施。 | H4でC01とC03だけを先に確認し、次にC07をONにして表示量を調整する |
| 2026-05-31 | トレード心理研究 | 資料量が多いため、失敗パターンだけでなく最適エントリーパターンも抽出できる可能性が高いと判断。成功例と失敗例を同じ列で比較する研究ノートを追加。 | 成功トレード10から20件を抽出し、E01からE05の候補に分類する |
| 2026-05-31 | トレード心理研究 | 匿名化済み705トレードから最適エントリー一次抽出を開始。結果既知537件、利益/利確247件を母数に、成功候補20件をローカルで抽出。E04「押し戻り継続」が全体平均より少し良く、E01は抜け単体では弱いと確認。 | 成功候補20件を目視確認し、失敗例とペア比較する |
| 2026-05-31 | トレード心理研究 | 成功候補20件と失敗教材候補をペア比較。勝ちに多い条件は「抜け後の停滞」「レンジ外定着」「押し戻り継続」「否定ライン先置き」。V字・ヒゲは単体では緑サインにしない方針。 | P01からP03をPineの緑サイン条件へ変換する |
| 2026-05-31 | トレード心理研究 | 研究目的を「気づきを得ること」と明確化。売買ルール化を急がず、エントリー直前の心理、失敗の逆利用、成功候補に混ざる危険な成功体験を細かい気づきとして整理。 | 気づきからPine化するもの、教材化するもの、保留するものに分ける |
| 2026-05-31 | トレード心理研究 | 細かい気づきをPine化し、群衆心理検出器 v0.1 を作成。FOMO、PANIC、WICKを群衆反応として表示し、WAIT、OUT、PBを待てた候補として表示する。 | TradingViewで表示量と位置を確認し、研究用に条件を絞る |
| 2026-05-31 | トレード心理研究 | TradingViewでv0.1を確認し、WICKとPBが多すぎてローソク足が読みにくい問題を確認。v0.2でWICK/PB/状態テーブル/否定ラインを初期OFF、表示間隔を24本へ変更。 | まずFOMO、PANIC、WAIT/OUTだけで気づきを確認する |
| 2026-05-31 | トレード心理研究 | GBPJPY H1でv0.2を確認。FOMOは入口ではなく観察開始点、PANICは保留ゾーン、WAITは反応を遅らせた候補として見える。FOMO/PANIC直後に入るより、WAIT/OUTや再確認を待つ仮説が強まった。 | v0.3でFOMOを継続候補と伸び切り注意に分け、PANICを保留ゾーン化する |
| 2026-05-31 | トレード心理研究 | リアルタイムへの落とし込みを整理。FOMO/PANICは即エントリー禁止、WAIT/OUTは追加条件確認、最終判断はA=見送り、B=観察、C=候補、D=実行可能の4段階にする。 | A/B/C/D判定を記録できるシートまたはCSVを作る |
| 2026-05-31 | トレード心理研究 | 複雑化したため、リアルタイム表示を `STOP`、`WAIT`、`CHECK` の3つに簡略化。シンプル版Pineを追加。 | STOPで待てたか、CHECKまで待てたかだけを記録する |
| 2026-05-31 | 受講生エントリー集中パターン研究 | 匿名化705トレードから、エントリー根拠文だけを使って複数人が同じ形で入る候補を一次抽出。節目抜け449件/54名、トレンド継続期待305件/52名、V字192件/50名、レンジ急変179件/46名。 | P01の画像20件を並べ、失敗の早い入口と成功の待った入口を比較する |
| 2026-05-31 | 受講生エントリー集中パターン研究 | P01「節目抜け・ブレイク飛び乗り」で画像照合できた候補162件/28名を抽出。確認用20枚シートは損失10件/利益10件。勝ち負けの両方に抵抗線抜け、高値停滞、V字、2回目ブレイクが出るため、形そのものではなく待ち方が分岐と判断。 | 20枚シートに早い入口と待った入口を手動マーキングする |
| 2026-05-31 | 受講生エントリー集中パターン研究 | P01の20枚シートにSTOP/CHECK暫定マーキングを作成。損失側は抜け/停滞を見てすぐ意味づけするSTOP候補、利益側は戻り・再停滞・再ブレイクを見るCHECK候補として整理し、シンプル版Pineをv0.2へ更新。 | TradingViewでSimple v0.2のSTOP/CHECK表示を確認する |
| 2026-05-31 | 受講生エントリー集中パターン研究 | TradingViewでSimple v0.2を確認。CHECKが多すぎ、STOP文字が目立ち、節目が細かすぎる問題を確認。v0.3でCHECKを最低4本待機+再加速余白+EMA方向一致に厳格化し、表示をS/W/Cに短縮、表示間隔を48本へ変更。 | Simple v0.3をTradingViewで確認し、候補が減ったか見る |
| 2026-05-31 | 受講生エントリー集中パターン研究 | GBPJPY H1でSimple v0.3を確認。Sは人が反応したくなる場所をよく拾えており、W/Cで待った後の候補も見やすくなった。ただしCも売買サインではなく、上位足方向と損切り位置が必要。 | v0.3のままS/W/Cを20例だけ目視記録する |
| 2026-05-31 | 受講生つまずきクラスタ研究 | 失敗チャート137件から entry_datetime / entry_price を画像抽出。48時間×価格近接で29クラスタ、うち15が全敗。GBPJPY 199円台5人全敗・XAUUSD天井買い3ゾーンなどを特定。Pine v0.3で GBPJPY / USDJPY / XAUUSD の実エントリー重ね表示を作成。 | 全敗ゾーンごとに本来待つ場所をマーキングし、v2.x フィルタ候補を試験実装する |
| 2026-05-31 | 受講生つまずきクラスタ研究 | 全敗15クラスタに「待つ場所」をマーキング（pullback/bounce/confirmation）。wait_zones CSV と Pine v0.4（赤=失敗・青=待つ）を GBPJPY/USDJPY/XAUUSD に追加。 | TradingView で v0.4 の青帯を目視確認し、v2.x 節目飛び乗り抑制フィルタを試験実装する |
| 2026-05-31 | 節目飛び乗り抑制フィルタ試験 | GBPJPY 1H で OFF/ON 実測。ON で件数63%減・DD改善、全期間PFは微悪化。**137件データで十分**と確定。v0.1.1 の F1 を v2.x 移植候補に。 | v2.x 本体へ F1 だけ AND 移植 |
| 2026-05-31 | 通貨別の心理傾向 | 137件の実エントリー抽出データと705件の匿名化済み心理データから、GBPJPYは勢いの罠、XAUUSDは値幅の罠、USDJPYは節目抜けの罠として見る仮説を追加。 | GBPJPY、XAUUSD、USDJPYで `S/W/C` を各20例ずつ記録し、通貨別にC条件を少し変えるか判断する |
| 2026-05-31 | 2期生トレード心理データ取り込み | 2期生共有Docから49件を取り込み、145行の匿名化済み構造化データをローカル作成。既存705行と合わせて統合850行。公開版には件数と研究メモのみ記録。 | 2期生の「2回目以降ブレイクアウト」「高値/安値停滞」を1期生のつまずき研究と比較する |
| 2026-05-31 | 受講生つまずきクラスタ研究 | 1期235+2期145=**380件**へ座標抽出を拡張。66クラスタ・全敗18。XAUUSD 2934–2954（6人全敗）・GBPJPY 205円台（2期3人全敗）など新規。Pine **v0.5** + wait_zones **v0.2**（v0.1手動9件引継）。 | TradingView で v0.5 青帯を目視確認。新規全敗期間で F1 A/B |
| 2026-05-31 | 850件テキスト失敗理由研究 | 850行から失敗パターン・心理・入口テーマを集計。Pine不要の台帳方針を確定。公開版は集計CSV・タグのみindex・全敗18カード。 | 損失367行をパターン別教材カード化（ローカル） |
| 2026-06-01 | 投げ売り・踏み上げ研究 | 用語の例え、ローソク足の出方、Pine化する条件を公開メモ化。投げ売りは買い手の降参、踏み上げは売り手の降参として整理。 | `CAPITULATION` / `SQUEEZE` の観察ラベルをPineへ入れる |
| 2026-06-01 | ブログ教材化 | 教材化しやすい公開レポート10本を `docs/blog_materials/reports/` へ複製し、ブログ連載案と記事テンプレートを追加。 | まず1本目「投げ売りと踏み上げをローソク足で読む」を記事化する |
| 2026-06-01 | 準本命4手法検証 | TrendBreak+T5以外で主要に近い候補4つ（SQZ/VIS/LSS/DTS）を優先順・昇格ゲート・フォワード台帳で整理。 | 第1週: VIS+SQZ Pine照合 |
| 2026-06-01 | 大トレンドブレイク相性検証 | 休眠レベル（A/B/C）× TB/T5。TBロング+休眠同時ブレイク PF2.37、TB+T5+直近48本 PF2.28。単独エントリーは非採用。踏み上げ研究は終了。 | [dormant_synergy_validation_2026-06-01/DECISION.md](dormant_synergy_validation_2026-06-01/DECISION.md) |
| 2026-06-01 | 敗者コホート・イベントスキャナー | E1〜E4＋ランダム対照、2936イベント、forward MFE48のみ。E1 SQZはランダムよりMFE/fwd優位。売買なし。 | [loser_cohort_event_scanner_2026-06-01/DECISION.md](loser_cohort_event_scanner_2026-06-01/DECISION.md) |
| 2026-06-01 | **系統B 10レーン検証** | V1/T5除外。98件→重複排除88件/年7.9。SQZ5本PF2.26。B03 EURJPY Researchマイナス。B06↔B07重複9。 | [system_b_lanes_validation_2026-06-01/DECISION.md](system_b_lanes_validation_2026-06-01/DECISION.md) |
| 2026-06-01 | **系統B 本番準備** | portfolio_slots.yaml・フォワードログ・B03除外文書化。 | [operations/system_b](../operations/system_b/) |
| 2026-06-01 | **系統B Pine照合準備** | Python再実行OK。B06 Pine TPデフォルト→Signal基準。 | [usdjpy_b06_smoke.md](system_b_pine_parity_2026-06-01/usdjpy_b06_smoke.md) |
| 2026-06-05 | **B06 TV OANDA 照合完了** | 4通貨37件 OK。正=`python_expected_b06_tv_oanda_*.csv`。 | `pine_ready: yes` フォワード継続 |
| 2026-05-31 | **B07 TV-OHLC baseline** | 先ほどの4本 `tv_*_h4.csv` で12件。H4日時=B06照合済み。旧9件exportは不使用。 | [B07_TV_PARITY_CHECKLIST_ja.md](system_b_pine_parity_2026-06-01/B07_TV_PARITY_CHECKLIST_ja.md) → D1Trap Pine最終確認 |
| 2026-06-01 | ブログ記事作成 | ブログ用の記事5本を作成。「ブレイク直後」「投げ売り/踏み上げ」「失敗の逆利用」「同じ場所での同じ失敗」「STOP/WAIT/CHECK」を教材化。 | 次は各記事にアイキャッチ案とSNS導入文を付ける |
| 2026-06-01 | ブログ記事作成 | ユーザー指定タイトル20本をすべて記事化し、`docs/blog_materials/articles/` に一覧ページを追加。 | 各記事にアイキャッチ案、リード文、投稿順を付ける |
| 2026-06-01 | ブログ記事作成 | 「自分のことだと思わせる」追加タイトル25本を記事化し、記事下書きは合計45本に拡張。 | 45本から投稿優先順位を決め、各記事にアイキャッチ案を付ける |
| 2026-06-01 | ブログ記事作成 | 損切り位置を損失方向へずらす心理をテーマに、46本目の記事を追加。 | 損切り心理シリーズとして並び替える |
| 2026-06-01 | ブログタイトル改善 | 46本の記事タイトルを、抽象語ではなく「大陽線・大陰線」「抜けた後の戻り」「損切り幅」「次の足」などチャート上で確認できる言葉へリライト。 | 投稿優先順位を決め、上位10本からアイキャッチ案とSNS導入文を付ける |
| 2026-06-01 | トレード実践記録 | 作成したインジケータの実戦記録場所を `docs/trade_practice_records/` に追加。USDJPY H4 159.674 のエントリーを1件目として記録。 | 決済後に結果、感情、損切り位置、次回ルールを追記する |
| 2026-06-01 | 究極手法 v1.0 実検証 | 本番2柱+アンサンブル+準本番4手法の Python バックテストを再実行。+219.9R / PF1.86 を再現確認。 | [ultimate_method_validation_results_2026-06-01.md](ultimate_method_validation_results_2026-06-01.md) を参照し、VIS+SQZ の TV parity へ |
| 2026-06-01 | H4 T5 徹底リサーチ | 13本の検証スクリプト・6フェーズ進化史・通貨別/トリガー別/出口/却下 variant を統合。 | Pine parity → フォワード30件 → T5×VIS 重複 study |
| 2026-06-01 | H4 T5 Pine parity 期待値 | Python 99件+OOS15件+Practical34件の TV 照合用 CSV/checklist をエクスポート。 | USDJPY スモーク → 全通貨 Phase A/B |

## 進行中の研究

| 優先 | 研究テーマ | 状態 | 目的 | 現在地 | 次の作業 |
|---:|---|---|---|---|---|
| 1 | **850件テキスト失敗理由** | **集計確定** | なぜ失敗するかを分類・台帳化（Pine不要） | 850行・損失367・公開集計6ファイル | パターン別教材カード |
| 2 | 受講生つまずきクラスタ研究 | **データ確定** | 380件・全敗18・Pine v0.5 + F1試験 v0.1.1 完了 | 1期+2期座標抽出完了 | v2.x へ F1 移植 / 新規全敗期間で A/B |
| 3 | Market Psychology Squeeze | 記録済み | スクイーズ、投げ売り、踏み上げを戦略化する | 通貨別の相性、厳格条件、ローソク足の例えを整理済み | `CAPITULATION` / `SQUEEZE` の観察ラベルをPineへ入れる |
| 4 | トレード実践記録 | 記録開始 | 作成したインジケータを実戦で使った結果を残す | USDJPY H4 159.674 を1件目として記録 | 決済後レビューを追記 |
| 5 | Lower High 3 Touch Breakdown | B抜け危険除外v0.1 | 3回高値切り下げ後の売り継続と転換候補を分ける | 下抜け1578件、上抜け2389件、勝率PF14334シナリオ、B床化22698シナリオ、危険除外30474スコープ行を実測 | XAUUSD H4でA余白0.5R・D1 EMA20・終値位置60%以上をPineへ表示する |
| 6 | Wavebox / Rebreak | 記録済み | 波形、再ブレイク、押し戻りの有効条件を調べる | 運用前提、監査、Pine 実装メモを整理済み | 実運用に使う版と研究保留版を分ける |

## トレード心理研究の中間整理

研究の問い:

- 人はどのチャート形状で焦って入りやすいか
- どの感情が損切り遅れ、飛び乗り、根拠の後付けにつながるか
- 成功したトレードと失敗したトレードで、エントリー前の待ち方がどう違うか
- Sai フィードバックを、再現できるルールに変換できるか
- 勝っている人は、入る直前にどの条件がそろうまで待っているか

構造化する項目:

| 項目 | 内容 |
|---|---|
| 匿名ID | 個人を特定しない研究用ID |
| 回数 | 同じ人の何回目の報告か |
| 通貨ペア | 取引対象 |
| エントリー根拠 | 入った理由 |
| 決済理由 | 利確、損切り、撤退の理由 |
| 感情 | 焦り、期待、不安、悔しさ、安心など |
| 失敗パターン | 飛び乗り、損切り遅れ、レンジ中央、根拠不足など |
| 成功パターン | 待てた、節目確認、損切り明確、環境認識一致など |
| Saiフィードバック | 指摘、改善案、次の見る場所 |
| 心理ラベル | 研究用に付ける短い心理分類 |
| エントリー型 | 抜け再確認、押し戻り、レンジ端反発、レンジ外定着、転換確認など |
| 入る直前の確認 | 次足確認、戻り確認、再加速、否定ライン明確化など |

## 失敗チャート研究の見方

チャートを見るときは、勝ち負けだけでなく「どこで心が動いたか」を見る。

| 見る場所 | 確認すること |
|---|---|
| エントリー直前 | 待つべきローソク足が残っていたか |
| 節目付近 | 抜けた瞬間に飛び乗っていないか |
| レンジ中央 | 方向感がない場所で入っていないか |
| 損切り位置 | 入る前に撤退場所が決まっていたか |
| 決済後 | 反省がルール化されているか、感情だけで終わっていないか |

次に作るもの:

1. 代表チャートの比較表
2. 失敗パターン別のチャート画像集
3. エントリー位置、待つ場所、損切り位置を重ねた教材画像
4. 心理ラベル別の改善ルール

## 公開済み研究ノート

| テーマ | ファイル |
|---|---|
| Market Psychology | [market_psychology_pattern_library_2026-05-30.md](market_psychology_pattern_library_2026-05-30.md) |
| Market Psychology Squeeze | [market_psychology_squeeze_strict_2026-05-30.md](market_psychology_squeeze_strict_2026-05-30.md) |
| **踏み上げ・投げ切り 実装前検証** | [cap_sqz_thorough_validation_2026-06-01/DECISION.md](cap_sqz_thorough_validation_2026-06-01/DECISION.md) |
| 通貨別相性 | [market_psychology_squeeze_currency_compatibility_2026-05-30.md](market_psychology_squeeze_currency_compatibility_2026-05-30.md) |
| Wavebox 運用条件 | [wavebox_operational_preconditions_v1.md](wavebox_operational_preconditions_v1.md) |
| Wavebox フォワード検証 | [wavebox_forward_validation_protocol.md](wavebox_forward_validation_protocol.md) |
| ショート側研究 | [short_side_research_2026-05-28_in_progress.md](short_side_research_2026-05-28_in_progress.md) |
| H4 V字回復候補 | [h4_v_recovery_strategy_candidates_2026-05-30.md](h4_v_recovery_strategy_candidates_2026-05-30.md) |
| トレード心理Pine化 | [trade_psychology_failure_patterns_to_pine_2026-05-31.md](trade_psychology_failure_patterns_to_pine_2026-05-31.md) |
| トレード心理 最適エントリー研究 | [trade_psychology_optimal_entry_pattern_research_2026-05-31.md](trade_psychology_optimal_entry_pattern_research_2026-05-31.md) |
| リアルタイム心理記録テンプレート | [realtime_trade_psychology_log_template.csv](realtime_trade_psychology_log_template.csv) |
| 受講生エントリー集中パターン研究 | [student_entry_cluster_research_2026-05-31.md](student_entry_cluster_research_2026-05-31.md) |
| 受講生つまずきクラスタ研究 | [student_stumble_clusters_research_2026-05-31.md](student_stumble_clusters_research_2026-05-31.md) |
| 節目飛び乗り抑制フィルタ試験 | [stumble_chase_suppression_filter_v0_1.md](stumble_chase_suppression_filter_v0_1.md) |
| 通貨別の心理傾向 | [currency_pair_personality_hypothesis_2026-05-31.md](currency_pair_personality_hypothesis_2026-05-31.md) |
| 2期生トレード心理データ取り込み | [second_cohort_trade_psychology_import_2026-05-31.md](second_cohort_trade_psychology_import_2026-05-31.md) |
| **850件テキスト失敗理由** | [trade_psychology_failure_reason_research_2026-05-31.md](trade_psychology_failure_reason_research_2026-05-31.md) |
| **準本命4手法 検証ロードマップ** | [near_main_validation_roadmap_2026-06-01.md](near_main_validation_roadmap_2026-06-01.md) |
| **究極手法 v1.0（研究統合）** | [ultimate_method_v1_2026-06-01.md](ultimate_method_v1_2026-06-01.md) |
| **究極手法 v1.0 実検証結果（再実行）** | [ultimate_method_validation_results_2026-06-01.md](ultimate_method_validation_results_2026-06-01.md) |
| **H4 T5 手法 徹底リサーチ** | [t5_method_deep_research_2026-06-01.md](t5_method_deep_research_2026-06-01.md) |
| **H4 T5 Pine parity（TV照合用）** | [t5_pine_parity/tradingview_parity_checklist.md](../../backtests/elliott_fibo/results_2026_06_01/t5_pine_parity/tradingview_parity_checklist.md) |
| 日次チェックリスト | [ultimate_method_daily_checklist.csv](../trade_practice_records/ultimate_method_daily_checklist.csv) |
| フォワード検証台帳 | [near_main_forward_validation_log.csv](../trade_practice_records/near_main_forward_validation_log.csv) |
| 全敗18クラスタ失敗カード | [student_stumble_all_loss_failure_cards_v0_1.md](student_stumble_all_loss_failure_cards_v0_1.md) |
| ブログ教材用フォルダ | [../blog_materials/README.md](../blog_materials/README.md) |
| トレード実践記録 | [../trade_practice_records/README.md](../trade_practice_records/README.md) |
| Lower High 3 Touch Breakdown | [lower_high_three_touch_breakdown_hypothesis_2026-06-08.md](lower_high_three_touch_breakdown_hypothesis_2026-06-08.md) |
| Lower High 3 Touch 実測結果 | [lower_high_three_touch_breakdown_2026-06-08/REPORT_ja.md](lower_high_three_touch_breakdown_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch 上抜けロング実測 | [lower_high_synapse_reclaim_long_2026-06-08/REPORT_ja.md](lower_high_synapse_reclaim_long_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch 上抜けロング勝率PF | [lower_high_synapse_reclaim_long_strategy_2026-06-08/REPORT_ja.md](lower_high_synapse_reclaim_long_strategy_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch Synapse確認フィルタ勝率PF | [lower_high_synapse_confirm_filters_2026-06-08/REPORT_ja.md](lower_high_synapse_confirm_filters_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch B床化確認勝率PF | [lower_high_b_support_confirmation_2026-06-08/REPORT_ja.md](lower_high_b_support_confirmation_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch B抜け即危険除外 | [lower_high_b_break_danger_filters_2026-06-08/REPORT_ja.md](lower_high_b_break_danger_filters_2026-06-08/REPORT_ja.md) |
| Lower High 3 Touch B抜け危険除外 Pine | [../../pine/research/lower_high_synapse_b_danger_filter_visual_v0_1.pine](../../pine/research/lower_high_synapse_b_danger_filter_visual_v0_1.pine) |
| Lower High 3 Touch B確認 目視照合Pine | [../../pine/research/lower_high_synapse_b_confirm_visual_v0_1.pine](../../pine/research/lower_high_synapse_b_confirm_visual_v0_1.pine) |
| Lower High x Synapse 接続 | [lower_high_synapse_bridge_2026-06-08.md](lower_high_synapse_bridge_2026-06-08.md) |

## 新しい研究を書くとき

新しいメモは [RESEARCH_NOTE_TEMPLATE.md](RESEARCH_NOTE_TEMPLATE.md) をコピーして使います。  
最初に「研究の問い」と「次にやること」を書くと、あとで読み返したときに迷いにくくなります。

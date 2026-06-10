# 研究インデックス

このページは「今なにを研究しているか」を忘れないための入口です。  
詳しい生データ、個人情報、元ドキュメント、元チャート画像は公開せず、GitHub には公開してよい概要と次の作業だけを残します。

## 運用ルール

- 会話で出た研究メモは、公開してよい形に要約してこの研究インデックスへ反映する
- 個人情報、元ドキュメント、元チャート画像、匿名化前データは GitHub に載せない
- 「研究の問い」「途中経過」「次にやること」を必ず残す
- 新しい発見は、あとから教材・検証・Pine 化のどれに使うか分けて記録する

## 次にやること（2026-06-10 更新）

**受講生データ研究は一旦終了。** 研究リソースは **既存2本柱** の検証・拡張に集中する。

1. **TrendBreakV1 + H4 T5** の OOS 継続確認（2025-2026）
2. **H4 Double V Reclaim / 初動V** — D1 V Context + H4 Execute の目視・Strategy 検証
3. **H4 V Denial Re-Acceleration** — H4T5 / Shelf Breakout との比較、勝ち負け各5件記録
4. **ショート側研究** — 1ヶ月安値更新後の安値停滞ブレイクショートの精査
5. **Market Psychology Squeeze** — 実運用に残す条件と除外条件の整理

## 進行中の研究

| 優先 | 研究テーマ | 状態 | 目的 | 次の作業 |
|---:|---|---|---|---|
| 1 | **既存2本柱（TrendBreakV1 + H4 T5）** | **本番運用中** | 採用戦略の OOS 継続・監査 | [BACKTEST_INDEX.md](../BACKTEST_INDEX.md) ／ [STRATEGY_GUIDE.md](../../STRATEGY_GUIDE.md) |
| 2 | **H4 Double V Reclaim / 初動V** | **最重要・検証中** | D1 V Context + H4 Execute でトレンド初動を狙う | 目視検証、Strategy Tester 照合 |
| 3 | **H4 V Denial Re-Acceleration** | **重要・検証中** | 売り手の損切り連鎖を検出する | GBPJPY / USDJPY / EURJPY / AUDJPY H4 で勝ち負け各5件 |
| 4 | **ショート側研究** | 検証途中 | ロング版ミラーの代替ショート入口 | 暫定候補の精査 |
| 5 | **Market Psychology Squeeze** | TV OHLC照合済み | スクイーズ→踏み上げの戦略化 | 実運用条件の整理 |
| 6 | Wavebox / Rebreak | 記録済み | 波形・再ブレイクの有効条件 | 実運用版と研究保留版の切り分け |

## 終了した研究

| 日付 | 研究テーマ | 終了理由 | アーカイブ |
|---|---|---|---|
| **2026-06-10** | **受講生データ研究（一括）** | 気づき・教材としては有用だが、単独の売買手法（PF改善）にはならない。本番自動売買への組み込みは見送り | 下記「受講生データ研究アーカイブ」 |
| 2026-06-03 | Short Covering Psychology Flow | 入口の優位性が H4T5 / D1 V Context / Double V ほど明確ではない | [short_covering_psychology_flow_2026-06-03.md](short_covering_psychology_flow_2026-06-03.md) |

### 受講生データ研究アーカイブ（2026-06-10 クローズ）

| テーマ | 成果 | ファイル |
|---|---|---|
| つまずきクラスタ | 137件 / 29クラスタ / 全敗15 | [student_stumble_clusters_research_2026-05-31.md](student_stumble_clusters_research_2026-05-31.md) |
| エントリー集中パターン | P01 節目抜け・S/W/C Pine | [student_entry_cluster_research_2026-05-31.md](student_entry_cluster_research_2026-05-31.md) |
| トレード心理 / 群衆心理 | FOMO/PANIC/WAIT 可視化 | [trade_psychology_failure_patterns_to_pine_2026-05-31.md](trade_psychology_failure_patterns_to_pine_2026-05-31.md) |
| 節目飛び乗り抑制 F1 試験 | OFF/ON 件数照合済み。**v2.x 移植は見送り** | [stumble_chase_suppression_filter_v0_1.md](stumble_chase_suppression_filter_v0_1.md) |
| 市場心理図鑑 | Vol.1 + 収集ライブラリ（教材として継続） | [市場心理図鑑/README.md](市場心理図鑑/README.md) |
| Pine v0.4 | 赤=失敗 / 青=待つ（教材用） | `pine/research/student_stumble_zones_*_v0_4.pine` |

**F1 試験の結論（再掲）:** つまずき型エントリーの約6割は削れるが、PF 改善は確認できず。F1 は **売買手法ではなく安全装置の候補** だったが、本番 TrendBreakV1 との合成検証前に研究終了。

## 進捗ログ

| 日付 | 研究テーマ | 進捗 | 次の判断 |
|---|---|---|---|
| 2026-06-10 | 受講生データ研究 | **研究一旦終了。** 137件つまずき・F1試験・心理Pine・市場心理図鑑まで完了。README / 研究台帳を既存手法優先に整理 | 既存2本柱（TrendBreakV1 + H4 T5）の研究続行 |
| 2026-06-10 | F1 OANDA 照合 | GBPJPY 1H OANDA CSV で Python/TV 件数パリティ確認（OFF 1193/458 vs TV 1279/473） | v2.x 移植は見送り（研究終了に伴う） |
| 2026-06-05 | H4 V Denial Re-Acceleration | Strategy 研究版を追加 | H4T5 等と比較目視 |
| 2026-06-03 | Short Covering Psychology Flow | 研究終了・本番不採用 | アーカイブ |
| 2026-05-31 | 受講生つまずきクラスタ研究 | 137件・全敗15・Pine v0.4 + F1試験 v0.1.1 完了 | **2026-06-10 研究終了** |
| 2026-05-31 | 節目飛び乗り抑制フィルタ試験 | GBPJPY 1H OFF/ON 実測。件数63%減・DD改善、PF微悪化 | **v2.x 移植見送り** |

<details>
<summary>2026-05-31 以前の進捗ログ（折りたたみ）</summary>

| 日付 | 研究テーマ | 進捗 | 次の判断 |
|---|---|---|---|
| 2026-05-31 | トレード心理研究 | 失敗チャートの代表例7ケースをローカルで選び、可視化第一版を作成 | **2026-06-10 研究終了** |
| 2026-05-31 | 受講生エントリー集中パターン研究 | P01「節目抜け・ブレイク飛び乗り」162件/28名。Simple v0.3 で S/W/C 確認 | **2026-06-10 研究終了** |
| 2026-05-31 | 通貨別の心理傾向 | GBPJPY=勢いの罠、XAUUSD=値幅の罠、USDJPY=節目抜けの罠 | **2026-06-10 研究終了** |

</details>

## トレード心理研究の中間整理（アーカイブ）

研究の問い:

- 人はどのチャート形状で焦って入りやすいか
- どの感情が損切り遅れ、飛び乗り、根拠の後付けにつながるか
- 成功したトレードと失敗したトレードで、エントリー前の待ち方がどう違うか

**2026-06-10:** 上記は教材・気づきとして成果物を残すが、新規研究は行わない。

## 公開済み研究ノート

| テーマ | ファイル |
|---|---|
| **既存2本柱** | [two_method_practical_research_2026-05-24.md](../two_method_practical_research_2026-05-24.md) ／ [BACKTEST_INDEX.md](../BACKTEST_INDEX.md) |
| H4 Double V Reclaim | [h4_double_v_reclaim_2026-06-02.md](h4_double_v_reclaim_2026-06-02.md) |
| H4 V Denial Re-Acceleration | [h4_v_denial_reacceleration_2026-06-05.md](h4_v_denial_reacceleration_2026-06-05.md) |
| Market Psychology Squeeze | [market_psychology_squeeze_strict_2026-05-30.md](market_psychology_squeeze_strict_2026-05-30.md) |
| ショート側研究 | [short_side_research_2026-05-28_in_progress.md](short_side_research_2026-05-28_in_progress.md) |
| Wavebox 運用条件 | [wavebox_operational_preconditions_v1.md](wavebox_operational_preconditions_v1.md) |
| **市場心理図鑑（教材）** | [市場心理図鑑/README.md](市場心理図鑑/README.md) |
| 受講生つまずき（終了） | [student_stumble_clusters_research_2026-05-31.md](student_stumble_clusters_research_2026-05-31.md) |
| F1 試験（終了） | [stumble_chase_suppression_filter_v0_1.md](stumble_chase_suppression_filter_v0_1.md) |
| Short Covering（終了） | [short_covering_psychology_flow_2026-06-03.md](short_covering_psychology_flow_2026-06-03.md) |

## 新しい研究を書くとき

新しいメモは [RESEARCH_NOTE_TEMPLATE.md](RESEARCH_NOTE_TEMPLATE.md) をコピーして使います。  
最初に「研究の問い」と「次にやること」を書くと、あとで読み返したときに迷いにくくなります。

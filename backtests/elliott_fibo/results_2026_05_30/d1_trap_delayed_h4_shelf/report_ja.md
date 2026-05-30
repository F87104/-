# D1 Trap Delayed H4 Shelf Study

作成日: 2026-05-30

## 仮説

D1 120本級の安値更新否定は、その場で買うより、少し時間が経ってからH4でV棚ブレイクが出た時に効くのではないか。

心理構造:

1. D1で長期安値を割る
2. 下方向ブレイクが否定される
3. 売り方が完全には崩れず、しばらく揉む
4. 後日H4で急落Vから上側の棚を作る
5. 棚高値を抜けると、売り方の買い戻しと遅れた買いが重なる

## 検証方法

- H4側は既存の `H4 V Initial Shelf Breakout` 現行トレードを使用。
- D1側は `D1 120本 安値Trap` のみを見る。
- D1 Trapは日足確定後の翌日から有効。
- これはポストフィルタ検証。実装候補になった場合は、次に統合バックテストで確認する。

## 結果

| label | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline selected | 34 | 58.82 | 15.55 | 0.46 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 5 | 4.93 |
| D1 low trap age 30-120d + H4 Initial Shelf | 8 | 75.00 | 7.04 | 0.88 | 4.46 | 2.03 | 2 | 1.56 | 0.80 | 1 | 1.50 |

## 条件別サマリー 上位

| universe | label | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| selected_ex_xau_chf_silver | REQUIRE_D1_LOW_TRAP_WITHIN_120D | 9 | 77.78 | 8.52 | 0.95 | 5.19 | 2.03 | 2 | 1.57 | 0.73 | 2 | 2.97 |
| selected_ex_xau_chf_silver | D1_LOW_TRAP_AGE_30_120D | 8 | 75.00 | 7.04 | 0.88 | 4.46 | 2.03 | 2 | 1.56 | 0.80 | 1 | 1.50 |
| selected_ex_xau_chf_silver | REQUIRE_D1_LOW_TRAP_WITHIN_240D | 16 | 75.00 | 13.88 | 0.87 | 4.40 | 4.09 | 4 | 1.55 | 0.62 | 3 | 4.46 |
| selected_ex_xau_chf_silver | D1_LOW_TRAP_AGE_60_240D | 13 | 69.23 | 9.36 | 0.72 | 3.29 | 4.09 | 4 | 1.43 | 0.69 | 2 | 2.99 |
| selected_ex_xau_chf_silver | BASELINE | 34 | 58.82 | 15.55 | 0.46 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 5 | 4.93 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_7D | 34 | 58.82 | 15.55 | 0.46 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 5 | 4.93 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_15D | 33 | 57.58 | 14.07 | 0.43 | 1.99 | 5.11 | 5 | 1.32 | 0.77 | 4 | 3.45 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_30D | 33 | 57.58 | 14.07 | 0.43 | 1.99 | 5.11 | 5 | 1.32 | 0.77 | 4 | 3.45 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_60D | 31 | 54.84 | 11.03 | 0.36 | 1.77 | 5.11 | 5 | 1.26 | 0.80 | 4 | 3.45 |
| selected_ex_xau_chf_silver | D1_LOW_TRAP_AGE_120_9999D | 25 | 52.00 | 7.03 | 0.28 | 1.58 | 4.09 | 4 | 1.24 | 0.76 | 3 | 1.96 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_120D | 25 | 52.00 | 7.03 | 0.28 | 1.58 | 4.09 | 4 | 1.24 | 0.76 | 3 | 1.96 |
| selected_ex_xau_chf_silver | AVOID_D1_LOW_TRAP_WITHIN_240D | 18 | 44.44 | 1.66 | 0.09 | 1.16 | 3.12 | 2 | 1.13 | 0.87 | 2 | 0.47 |

## 候補トレード

| symbol | entry_time | d1_low_trap_age_days | d1_low_trap_source | shelf_range_atr | shelf_hold_actual | breakout_atr | r_after_cost | exit_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURJPY | 2015-04-27 16:00:00 | 41.67 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.72 | 1.09 | 0.14 | 1.54 | TP |
| EURJPY | 2015-05-29 12:00:00 | 73.50 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.71 | 0.92 | 0.23 | 1.51 | TP |
| GBPJPY | 2016-08-24 12:00:00 | 43.50 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.26 | 0.85 | 0.35 | 1.51 | TP |
| EURJPY | 2016-10-04 00:00:00 | 106.00 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.15 | 1.01 | 0.12 | 1.52 | TP |
| GBPJPY | 2016-11-08 20:00:00 | 119.83 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.48 | 1.12 | 0.41 | -1.02 | SL |
| USDJPY | 2020-11-11 16:00:00 | 102.67 | WICK_L120_BODY_RR15 | 1.61 | 0.84 | 0.25 | -1.01 | SL |
| GBPJPY | 2024-10-09 12:00:00 | 61.50 | CLOSEFAIL_L120_W6_BODY_RR15 | 1.32 | 0.54 | 0.49 | 1.50 | TP |
| USDJPY | 2025-07-07 04:00:00 | 75.17 | WICK_L120_BODY_RR15 | 1.13 | 0.66 | 0.50 | 1.50 | TP |

## 通貨別

| symbol | label | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURJPY |  | 3 | 100.00 | 4.57 | 1.52 | inf | 0.00 | 0 | 2.32 | 0.46 | 0 | 0.00 |
| GBPJPY |  | 3 | 66.67 | 1.99 | 0.66 | 2.95 | 1.02 | 1 | 1.19 | 1.29 | 0 | 0.00 |
| USDJPY |  | 2 | 50.00 | 0.48 | 0.24 | 1.48 | 0.00 | 1 | 0.95 | 0.58 | 1 | 1.50 |

## 期間別

| period | label | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Research_2015_2024 |  | 7 | 71.43 | 5.54 | 0.79 | 3.73 | 2.03 | 2 | 1.51 | 0.90 | 0 | 0.00 |
| OOS_2025_2026 |  | 1 | 100.00 | 1.50 | 1.50 | inf | 0.00 | 0 | 1.88 | 0.06 | 1 | 1.50 |

## D1 Trapソース別

| d1_low_trap_source | label | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOSEFAIL_L120_W6_BODY_RR15 |  | 6 | 83.33 | 6.56 | 1.09 | 7.43 | 1.02 | 1 | 1.76 | 0.87 | 0 | 0.00 |
| WICK_L120_BODY_RR15 |  | 2 | 50.00 | 0.48 | 0.24 | 1.48 | 0.00 | 1 | 0.95 | 0.58 | 1 | 1.50 |

## 初期判断

これは面白い。D1 Trap直後ではなく、**30-120日後** が良いという形が出た。

ただし候補は selected universe で8件。PFは高いが、まだ本番候補ではなく、次は統合バックテストと条件緩和が必要。

現時点では、`D1 Trap Delayed H4 Shelf` は新しい研究テーマとして継続価値あり。

## 次にやること

1. 統合バックテスト化して、contextなしシグナルでポジションブロックされないようにする。
2. D1 Trapの有効期間を 30-180日 まで滑らかに確認する。
3. H4側を Shelf6 固定ではなく Shelf4-8 / RR1.2-2.0 で再確認する。
4. D1 Trap後すぐの15日以内が弱い理由を負けトレードで見る。

## 出力

- `annotated_h4_shelf_trades.csv`
- `context_filter_summary.csv`
- `candidate_trades_30_120d_selected.csv`
- `summary_candidate_by_symbol.csv`
- `summary_candidate_by_period.csv`
- `summary_candidate_by_source.csv`
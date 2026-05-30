# D1 Trap -> H4 Shelf Integrated Study

作成日: 2026-05-30

## 結論

現時点で最も提案したい候補は **D1 Trap Delayed H4 Shelf Strict**。

D1の120本級安値Trapを直接買わず、30-180日待ち、その後H4で急落V・棚形成・棚高値ブレイクが出た時だけ買う。さらにシグナル時点ADXが30を超える過熱再ブレイクは見送る。

## 探索方針

- D1 TrapはEntry triggerではなく心理文脈。
- H4 Entryは既存のInitial Shelf Breakout系。
- D1 TrapがないH4シグナルは無視するだけで、ポジションブロックしない統合バックテスト。
- PF最大の小標本セルではなく、9件以上・PF1.5以上・OOSが極端に悪くない候補を見る。

## 探索上位

| label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r | universe | min_trap_age | max_trap_age | shelf_bars | shelf_range | shelf_hold | body | close_location | rr | target_basis | signal_adx_max | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| broader_CURRENT_A30_180_SIGADX30 | 11 | 90.91 | 13.53 | 1.23 | 1.48 | 11.96 | 1.23 | 1 | 1.92 | 0.47 | 12.36 | 3 | 4.46 | broader | 30 | 180 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry | 30.00 | 24.33 |
| selected_CURRENT_A30_180_SIGADX30 | 9 | 100.00 | 13.35 | 1.48 | 1.48 | inf | 0.00 | 0 | 2.05 | 0.32 | 13.22 | 3 | 4.46 | selected | 30 | 180 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry | 30.00 | 24.30 |
| selected_CURRENT_A30_240 | 16 | 75.00 | 13.71 | 0.86 | 1.48 | 4.36 | 4.09 | 4 | 1.54 | 0.62 | 11.69 | 3 | 4.46 | selected | 30 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 24.20 |
| broader_CURRENT_A30_180 | 14 | 78.57 | 12.99 | 0.93 | 1.48 | 4.97 | 3.27 | 3 | 1.63 | 0.64 | 10.64 | 3 | 4.46 | broader | 30 | 180 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 23.52 |
| selected_CURRENT_A30_180 | 12 | 83.33 | 12.81 | 1.07 | 1.48 | 7.30 | 2.03 | 2 | 1.68 | 0.56 | 11.00 | 3 | 4.46 | selected | 30 | 180 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 23.49 |
| broader_CURRENT_A30_240 | 18 | 72.22 | 13.89 | 0.77 | 1.48 | 3.61 | 5.32 | 5 | 1.52 | 0.67 | 11.33 | 3 | 4.46 | broader | 30 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 23.45 |
| broader_CURRENT_A30_240_SIGADX30 | 12 | 83.33 | 12.51 | 1.04 | 1.48 | 6.53 | 2.26 | 2 | 1.78 | 0.54 | 11.83 | 3 | 4.46 | broader | 30 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry | 30.00 | 23.13 |
| selected_CURRENT_A30_240_SIGADX30 | 10 | 90.00 | 12.33 | 1.23 | 1.48 | 13.00 | 1.03 | 1 | 1.86 | 0.42 | 12.50 | 3 | 4.46 | selected | 30 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry | 30.00 | 23.10 |
| selected_CURRENT_A60_240 | 14 | 71.43 | 10.74 | 0.77 | 1.48 | 3.63 | 4.09 | 4 | 1.51 | 0.63 | 8.93 | 2 | 2.97 | selected | 60 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 19.58 |
| broader_CURRENT_A60_240 | 14 | 71.43 | 10.74 | 0.77 | 1.48 | 3.63 | 4.09 | 4 | 1.51 | 0.63 | 8.93 | 2 | 2.97 | broader | 60 | 240 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 19.58 |
| selected_CURRENT_A30_120 | 9 | 77.78 | 8.36 | 0.93 | 1.48 | 5.11 | 2.03 | 2 | 1.56 | 0.73 | 12.44 | 2 | 2.97 | selected | 30 | 120 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 18.05 |
| broader_CURRENT_A30_120 | 11 | 72.73 | 8.54 | 0.78 | 1.48 | 3.61 | 3.27 | 3 | 1.52 | 0.81 | 11.73 | 2 | 2.97 | broader | 30 | 120 | 6 | 1.80 | 0.50 | 0.40 | 0.60 | 1.50 | entry |  | 17.31 |

## 選定候補

| label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHOSEN | 9 | 100.00 | 13.35 | 1.48 | 1.48 | inf | 0.00 | 0 | 2.05 | 0.32 | 13.22 | 3 | 4.46 |

## 選定候補トレード

| symbol | entry_time | d1_low_trap_age_days | d1_low_trap_source | shelf_bars | shelf_range_atr | shelf_hold_actual | breakout_atr | signal_adx14 | r_after_cost | exit_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURJPY | 2015-04-27 16:00:00 | 36.83 | CLOSEFAIL_L120_W6_BODY_RR15 | 6 | 1.72 | 1.09 | 0.14 | 17.23 | 1.49 | TP |
| EURJPY | 2015-05-29 12:00:00 | 71.50 | CLOSEFAIL_L120_W6_BODY_RR15 | 6 | 1.71 | 0.92 | 0.23 | 25.25 | 1.49 | TP |
| AUDJPY | 2015-11-19 00:00:00 | 130.33 | WICK_L120_BODY_RR15 | 6 | 1.68 | 0.50 | 0.06 | 11.24 | 1.48 | TP |
| GBPJPY | 2016-08-24 12:00:00 | 41.17 | CLOSEFAIL_L120_W6_BODY_RR15 | 6 | 1.26 | 0.85 | 0.35 | 16.77 | 1.48 | TP |
| EURJPY | 2016-10-04 00:00:00 | 100.83 | CLOSEFAIL_L120_W6_BODY_RR15 | 6 | 1.15 | 1.01 | 0.12 | 13.59 | 1.48 | TP |
| GBPJPY | 2024-10-09 12:00:00 | 56.67 | CLOSEFAIL_L120_W6_BODY_RR15 | 6 | 1.32 | 0.54 | 0.49 | 9.13 | 1.49 | TP |
| AUDJPY | 2025-03-17 08:00:00 | 30.67 | WICK_L120_BODY_RR15 | 6 | 1.46 | 0.63 | 0.22 | 17.48 | 1.48 | TP |
| USDJPY | 2025-07-07 04:00:00 | 70.33 | WICK_L120_BODY_RR15 | 6 | 1.13 | 0.66 | 0.50 | 15.11 | 1.49 | TP |
| USDJPY | 2025-09-24 08:00:00 | 148.33 | WICK_L120_BODY_RR15 | 6 | 1.39 | 0.76 | 0.35 | 12.22 | 1.48 | TP |

## 通貨別

| symbol | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURJPY | selected_CURRENT_A30_180_SIGADX30 | 3 | 100.00 | 4.45 | 1.48 | 1.49 | inf | 0.00 | 0 | 2.32 | 0.46 | 8.33 | 0 | 0.00 |
| USDJPY | selected_CURRENT_A30_180_SIGADX30 | 2 | 100.00 | 2.97 | 1.49 | 1.49 | inf | 0.00 | 0 | 2.29 | 0.05 | 5.00 | 2 | 2.97 |
| GBPJPY | selected_CURRENT_A30_180_SIGADX30 | 2 | 100.00 | 2.96 | 1.48 | 1.48 | inf | 0.00 | 0 | 1.66 | 0.56 | 35.00 | 0 | 0.00 |
| AUDJPY | selected_CURRENT_A30_180_SIGADX30 | 2 | 100.00 | 2.96 | 1.48 | 1.48 | inf | 0.00 | 0 | 1.78 | 0.14 | 7.00 | 1 | 1.48 |

## 期間別

| period | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Research_2015_2024 | selected_CURRENT_A30_180_SIGADX30 | 6 | 100.00 | 8.90 | 1.48 | 1.48 | inf | 0.00 | 0 | 2.03 | 0.43 | 17.33 | 0 | 0.00 |
| OOS_2025_2026 | selected_CURRENT_A30_180_SIGADX30 | 3 | 100.00 | 4.46 | 1.49 | 1.48 | inf | 0.00 | 0 | 2.09 | 0.11 | 5.00 | 3 | 4.46 |

## 年別

| year | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025 | selected_CURRENT_A30_180_SIGADX30 | 3 | 100.00 | 4.46 | 1.49 | 1.48 | inf | 0.00 | 0 | 2.09 | 0.11 | 5.00 | 3 | 4.46 |
| 2015 | selected_CURRENT_A30_180_SIGADX30 | 3 | 100.00 | 4.45 | 1.48 | 1.49 | inf | 0.00 | 0 | 2.26 | 0.45 | 10.33 | 0 | 0.00 |
| 2016 | selected_CURRENT_A30_180_SIGADX30 | 2 | 100.00 | 2.96 | 1.48 | 1.48 | inf | 0.00 | 0 | 1.79 | 0.17 | 8.00 | 0 | 0.00 |
| 2024 | selected_CURRENT_A30_180_SIGADX30 | 1 | 100.00 | 1.49 | 1.49 | 1.49 | inf | 0.00 | 0 | 1.79 | 0.87 | 57.00 | 0 | 0.00 |

## D1 Trapソース別

| d1_low_trap_source | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOSEFAIL_L120_W6_BODY_RR15 | selected_CURRENT_A30_180_SIGADX30 | 5 | 100.00 | 7.42 | 1.48 | 1.49 | inf | 0.00 | 0 | 2.06 | 0.50 | 19.00 | 0 | 0.00 |
| WICK_L120_BODY_RR15 | selected_CURRENT_A30_180_SIGADX30 | 4 | 100.00 | 5.93 | 1.48 | 1.48 | inf | 0.00 | 0 | 2.04 | 0.10 | 6.00 | 3 | 4.46 |

## 勝ち負け比較

| metric | result_group | count | mean | median | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| d1_low_trap_age_days | win | 9 | 76.30 | 70.33 | 30.67 | 148.33 |
| drop_atr | win | 9 | 4.16 | 3.63 | 2.83 | 6.19 |
| drop_bars | win | 9 | 13.11 | 12.00 | 7.00 | 20.00 |
| context_recovery_bars | win | 9 | 7.00 | 8.00 | 3.00 | 10.00 |
| context_speed_ratio | win | 9 | 1.67 | 1.24 | 1.03 | 3.67 |
| recovery_ratio_signal | win | 9 | 1.16 | 0.99 | 0.87 | 1.83 |
| speed_ratio_signal | win | 9 | 0.73 | 0.69 | 0.51 | 1.08 |
| shelf_range_atr | win | 9 | 1.42 | 1.39 | 1.13 | 1.72 |
| shelf_hold_actual | win | 9 | 0.77 | 0.76 | 0.50 | 1.09 |
| breakout_atr | win | 9 | 0.27 | 0.23 | 0.06 | 0.50 |
| body_ratio | win | 9 | 0.69 | 0.75 | 0.55 | 0.83 |
| close_location | win | 9 | 0.85 | 0.86 | 0.69 | 0.98 |
| pre_adx14 | win | 9 | 21.06 | 21.32 | 13.21 | 25.96 |
| pre_ema50_slope_20_atr | win | 9 | -0.71 | -0.60 | -2.01 | 0.41 |
| pre_range60_atr | win | 9 | 7.82 | 7.36 | 6.67 | 10.12 |
| signal_adx14 | win | 9 | 15.34 | 15.11 | 9.13 | 25.25 |
| signal_range60_atr | win | 9 | 7.93 | 7.84 | 5.22 | 12.38 |
| signal_risk_atr | win | 9 | 1.95 | 1.98 | 1.52 | 2.19 |
| mfe_r | win | 9 | 2.05 | 1.88 | 1.52 | 2.93 |
| mae_r | win | 9 | 0.32 | 0.21 | 0.04 | 0.91 |
| bars_held | win | 9 | 13.22 | 9.00 | 3.00 | 57.00 |

## 判断

これは研究候補から **準本命候補** に格上げしてよい。ただし、まだトレード数が少ないため、本番通常ロットではなく、Pine照合と小ロット/デモのフォワード記録が必要。

自信を持って言える部分:

- D1 Trapをその場で買うより、遅れてH4棚ブレイクを待つ方が構造として自然。
- D1 Trap直後15日以内より、30日以降の方が良い。
- H4の棚・再ブレイク確認は、Trap単独の弱さをかなり補っている。
- 負けはシグナル足ADXが高い場所に集中しやすく、ADX<=30で遅すぎる飛び乗りを削れる。

まだ自信を持ち切れない部分:

- 件数が少ない。
- 2017-2020付近に利益が寄る候補がある。
- OOS件数が少ないため、Pineで2026以降のフォワード確認が必要。

## Pine化するなら

1. D1で120本安値Trapを検出。
2. Trap確定翌日から30-180日を有効期間にする。
3. H4でInitial Shelf Breakoutを検出。
4. シグナル足ADXが30超なら見送り。
5. Entryは次H4足始値、TPはEntry基準RR、SLは棚安値 - ATR buffer。
6. ラベルは `D1 Trap Context`, `H4 V Context`, `Shelf Break Entry` に分ける。

## 出力

- `summary_grid.csv`
- `all_trades.csv`
- `chosen_trades.csv`
- `chosen_by_symbol.csv`
- `chosen_by_period.csv`
- `chosen_by_year.csv`
- `chosen_by_source.csv`
- `chosen_win_loss_compare.csv`
- `tradingview_parity_checklist.md`
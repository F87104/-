# H4 V Initial Shelf Breakout 深掘り検証

作成日: 2026-05-30

## 結論

現時点では **採用候補だが、本番ロット投入は保留**。

理由は、構造は良いが、現行の初動寄りルールは 34 trades とまだ少なく、Research 期間より OOS に成績が寄っているため。過剰最適化というより、まだ標本数不足のリスクが大きい。

ただし、Vを直接買うより、売り失敗後に上側で棚を作って再点火する局面を買う、という本質は検証上も残っている。

## 再現確認

| check | value |
| --- | --- |
| source_trades | 34.00 |
| reproduced_trades | 34.00 |
| matched_entry_times | 34.00 |
| source_only | 0.00 |
| reproduced_only | 0.00 |
| max_abs_diff_entry | 0.00 |
| max_abs_diff_stop | 0.00 |
| max_abs_diff_target | 0.00 |
| max_abs_diff_r_after_cost | 0.00 |

## 現行成績

| label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current selected | 34 | 58.82 | 15.55 | 0.46 | 1.48 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 13.00 | 5 | 4.93 |
| Current all symbols | 55 | 50.91 | 13.57 | 0.25 | 1.40 | 1.49 | 8.49 | 8 | 1.23 | 0.88 | 13.76 | 7 | 5.40 |

## 監査メモ

- confirmed pivot は `confirm_i <= signal_i` のものだけを active に入れており、pivot確定前の未来情報は使っていない。
- 棚6本は `signal_i - shelf_bars : signal_i` で、シグナル足を含まない過去6本のみ。
- Entryは次足始値。ただし36d90e6版はTPをシグナル終値基準で計算しており、次足始値にギャップがあると厳密な1.5Rではない。Pine本番版ではEntry基準TPを推奨。
- PRECALMはV左肩起点時点のADX/EMA50傾き/EMA乖離/60本レンジ幅を見ている。これは過去情報でありlookaheadではない。
- 仕様書のベースV条件は3.5ATR完全回復だが、現行コードの本命は2.8ATRかつ65%-125%回復のV候補。初動狙いとしては合理的だが、仕様書では明確に分けるべき。

## 勝ち負け比較 上位差分

| feature | win_count | loss_count | win_mean | loss_mean | win_median | loss_median | win_p25 | loss_p25 | win_p75 | loss_p75 | mean_diff_win_minus_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mfe_atr_trade | 20 | 14 | 3.63 | 1.06 | 3.51 | 0.96 | 3.05 | 0.34 | 3.78 | 1.29 | 2.57 |
| mfe_r | 20 | 14 | 1.88 | 0.54 | 1.84 | 0.46 | 1.62 | 0.16 | 1.98 | 0.77 | 1.34 |
| pre_range60_atr | 20 | 14 | 7.53 | 6.73 | 7.45 | 6.67 | 6.69 | 5.48 | 8.16 | 7.49 | 0.80 |
| close_location | 20 | 14 | 0.85 | 0.85 | 0.90 | 0.84 | 0.76 | 0.78 | 0.96 | 0.90 | 0.01 |
| breakout_atr | 20 | 14 | 0.25 | 0.25 | 0.21 | 0.22 | 0.15 | 0.12 | 0.35 | 0.40 | 0.01 |
| shelf_bars | 20 | 14 | 6.00 | 6.00 | 6.00 | 6.00 | 6.00 | 6.00 | 6.00 | 6.00 | 0.00 |
| body_ratio | 20 | 14 | 0.68 | 0.68 | 0.62 | 0.66 | 0.58 | 0.60 | 0.77 | 0.73 | -0.01 |
| pre_adx14 | 20 | 14 | 18.99 | 18.99 | 19.15 | 19.85 | 15.90 | 14.62 | 21.54 | 22.14 | -0.01 |
| shelf_range_atr | 20 | 14 | 1.42 | 1.47 | 1.39 | 1.47 | 1.29 | 1.38 | 1.58 | 1.60 | -0.05 |
| risk_atr_entry | 20 | 14 | 1.92 | 1.98 | 1.92 | 2.06 | 1.82 | 1.90 | 2.08 | 2.12 | -0.05 |
| shelf_hold_actual | 20 | 14 | 0.97 | 1.03 | 0.92 | 1.01 | 0.74 | 0.81 | 1.09 | 1.17 | -0.06 |
| drop_atr | 20 | 14 | 4.11 | 4.18 | 3.92 | 3.85 | 3.42 | 3.38 | 4.64 | 5.29 | -0.07 |

## パラメータ感度 上位候補

| label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r | family | shelf_bars | shelf_range | shelf_hold | breakout_buffer | body | close_location | adx_max | range60_max | ema_slope_mode | rr | stop_buffer | max_hold | entry_mode | target_basis | robust_min_trades |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAKGRID_BUF0.08_BODY0.3_CL0.5 | 31 | 64.52 | 18.66 | 0.60 | 1.49 | 2.67 | 4.08 | 4 | 1.34 | 0.73 | 12.77 | 5 | 4.93 | breakout_quality | 6 | 1.80 | 0.50 | 0.08 | 0.30 | 0.50 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.1_BODY0.3_CL0.5 | 31 | 64.52 | 18.66 | 0.60 | 1.49 | 2.67 | 4.08 | 4 | 1.34 | 0.73 | 12.77 | 5 | 4.93 | breakout_quality | 6 | 1.80 | 0.50 | 0.10 | 0.30 | 0.50 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.08_BODY0.3_CL0.7 | 28 | 64.29 | 16.68 | 0.60 | 1.48 | 2.64 | 3.06 | 3 | 1.36 | 0.70 | 12.86 | 4 | 3.45 | breakout_quality | 6 | 1.80 | 0.50 | 0.08 | 0.30 | 0.70 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.1_BODY0.3_CL0.7 | 28 | 64.29 | 16.68 | 0.60 | 1.48 | 2.64 | 3.06 | 3 | 1.36 | 0.70 | 12.86 | 4 | 3.45 | breakout_quality | 6 | 1.80 | 0.50 | 0.10 | 0.30 | 0.70 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.08_BODY0.3_CL0.6 | 30 | 63.33 | 17.14 | 0.57 | 1.48 | 2.53 | 4.08 | 4 | 1.33 | 0.73 | 12.73 | 5 | 4.93 | breakout_quality | 6 | 1.80 | 0.50 | 0.08 | 0.30 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.1_BODY0.3_CL0.6 | 30 | 63.33 | 17.14 | 0.57 | 1.48 | 2.53 | 4.08 | 4 | 1.33 | 0.73 | 12.73 | 5 | 4.93 | breakout_quality | 6 | 1.80 | 0.50 | 0.10 | 0.30 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.08_BODY0.6_CL0.5 | 21 | 61.90 | 11.28 | 0.54 | 1.49 | 2.39 | 3.07 | 3 | 1.32 | 0.79 | 13.48 | 3 | 1.95 | breakout_quality | 6 | 1.80 | 0.50 | 0.08 | 0.60 | 0.50 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| BREAKGRID_BUF0.08_BODY0.6_CL0.6 | 21 | 61.90 | 11.28 | 0.54 | 1.49 | 2.39 | 3.07 | 3 | 1.32 | 0.79 | 13.48 | 3 | 1.95 | breakout_quality | 6 | 1.80 | 0.50 | 0.08 | 0.60 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENTRYMODE_next_open_signal | 34 | 58.82 | 15.55 | 0.46 | 1.48 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 13.00 | 5 | 4.93 | entry_mode | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENTRYMODE_next_open_entry | 34 | 58.82 | 15.38 | 0.45 | 1.47 | 2.08 | 5.11 | 5 | 1.33 | 0.75 | 12.94 | 5 | 4.92 | entry_mode | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | entry | True |
| ENTRYMODE_signal_close_signal | 34 | 58.82 | 15.38 | 0.45 | 1.47 | 2.08 | 5.11 | 5 | 1.33 | 0.75 | 14.00 | 5 | 4.92 | entry_mode | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | signal_close | signal | True |
| ENTRYMODE_signal_close_entry | 34 | 58.82 | 15.38 | 0.45 | 1.47 | 2.08 | 5.11 | 5 | 1.33 | 0.75 | 14.00 | 5 | 4.92 | entry_mode | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | signal_close | entry | True |
| SHELFGRID_B7_R1.8_H0.4 | 20 | 70.00 | 14.65 | 0.73 | 1.49 | 3.38 | 3.08 | 3 | 1.40 | 0.63 | 9.40 | 3 | 4.47 | entry_shelf | 7 | 1.80 | 0.40 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B7_R2.1_H0.5 | 20 | 70.00 | 14.58 | 0.73 | 1.48 | 3.38 | 3.07 | 3 | 1.39 | 0.69 | 9.55 | 3 | 4.47 | entry_shelf | 7 | 2.10 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B7_R2.4_H0.5 | 20 | 70.00 | 14.58 | 0.73 | 1.48 | 3.38 | 3.07 | 3 | 1.39 | 0.69 | 9.55 | 3 | 4.47 | entry_shelf | 7 | 2.40 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B7_R2.1_H0.4 | 22 | 68.18 | 15.06 | 0.68 | 1.48 | 3.10 | 4.10 | 4 | 1.36 | 0.71 | 9.14 | 3 | 4.47 | entry_shelf | 7 | 2.10 | 0.40 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B7_R2.4_H0.4 | 22 | 68.18 | 15.06 | 0.68 | 1.48 | 3.10 | 4.10 | 4 | 1.36 | 0.71 | 9.14 | 3 | 4.47 | entry_shelf | 7 | 2.40 | 0.40 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B6_R1.5_H0.5 | 21 | 61.90 | 11.24 | 0.54 | 1.48 | 2.38 | 4.09 | 4 | 1.31 | 0.71 | 12.14 | 5 | 4.93 | entry_shelf | 6 | 1.50 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B6_R1.5_H0.4 | 23 | 60.87 | 11.71 | 0.51 | 1.48 | 2.28 | 5.12 | 5 | 1.29 | 0.72 | 11.52 | 5 | 4.93 | entry_shelf | 6 | 1.50 | 0.40 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| SHELFGRID_B6_R1.8_H0.5 | 34 | 58.82 | 15.55 | 0.46 | 1.48 | 2.09 | 5.11 | 5 | 1.33 | 0.75 | 13.00 | 5 | 4.93 | entry_shelf | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R20_none | 34 | 64.71 | 20.32 | 0.60 | 1.48 | 2.66 | 4.68 | 4 | 1.39 | 0.68 | 12.76 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 20.00 | none | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R14_none | 33 | 63.64 | 18.83 | 0.57 | 1.48 | 2.54 | 4.68 | 4 | 1.39 | 0.69 | 12.64 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 14.00 | none | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R16_none | 33 | 63.64 | 18.83 | 0.57 | 1.48 | 2.54 | 4.68 | 4 | 1.39 | 0.69 | 12.64 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 16.00 | none | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R18_none | 33 | 63.64 | 18.83 | 0.57 | 1.48 | 2.54 | 4.68 | 4 | 1.39 | 0.69 | 12.64 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 18.00 | none | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX24_R20_none | 41 | 60.98 | 20.68 | 0.50 | 1.48 | 2.27 | 4.36 | 4 | 1.35 | 0.69 | 11.93 | 5 | 4.93 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 24.00 | 20.00 | none | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R12_strict | 20 | 60.00 | 9.76 | 0.49 | 1.48 | 2.20 | 3.06 | 3 | 1.22 | 0.62 | 10.95 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 12.00 | strict | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R14_strict | 20 | 60.00 | 9.76 | 0.49 | 1.48 | 2.20 | 3.06 | 3 | 1.22 | 0.62 | 10.95 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 14.00 | strict | 1.50 | 0.25 | 120 | next_open | signal | True |
| ENVGRID_ADX22_R16_strict | 20 | 60.00 | 9.76 | 0.49 | 1.48 | 2.20 | 3.06 | 3 | 1.22 | 0.62 | 10.95 | 4 | 3.44 | environment | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 22.00 | 16.00 | strict | 1.50 | 0.25 | 120 | next_open | signal | True |
| EXITGRID_RR1.8_SL0.4_H12 | 21 | 76.19 | 14.05 | 0.67 | 0.67 | 4.90 | 1.03 | 1 | 1.29 | 0.40 | 9.05 | 5 | 4.40 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.80 | 0.40 | 12 | next_open | signal | True |
| EXITGRID_RR1.5_SL0.4_H12 | 21 | 76.19 | 12.82 | 0.61 | 0.69 | 4.56 | 1.03 | 1 | 1.24 | 0.40 | 8.24 | 5 | 4.60 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.40 | 12 | next_open | signal | True |
| EXITGRID_RR1.5_SL0.4_H18 | 21 | 71.43 | 14.76 | 0.70 | 1.47 | 4.35 | 1.05 | 2 | 1.36 | 0.44 | 10.71 | 5 | 6.23 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.50 | 0.40 | 18 | next_open | signal | True |
| EXITGRID_RR1.2_SL0.4_H12 | 21 | 76.19 | 11.17 | 0.53 | 1.17 | 4.10 | 1.03 | 1 | 1.07 | 0.40 | 7.38 | 5 | 3.70 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.20 | 0.40 | 12 | next_open | signal | True |
| EXITGRID_RR1.2_SL0.4_H18 | 21 | 71.43 | 12.48 | 0.59 | 1.18 | 3.83 | 1.05 | 2 | 1.14 | 0.44 | 8.90 | 5 | 5.03 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.20 | 0.40 | 18 | next_open | signal | True |
| EXITGRID_RR2.0_SL0.4_H12 | 21 | 71.43 | 12.44 | 0.59 | 0.52 | 3.69 | 2.49 | 3 | 1.32 | 0.46 | 9.71 | 5 | 4.80 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 2.00 | 0.40 | 12 | next_open | signal | True |
| EXITGRID_RR2.5_SL0.4_H12 | 21 | 71.43 | 11.85 | 0.56 | 0.39 | 3.56 | 2.49 | 3 | 1.41 | 0.48 | 10.52 | 5 | 5.80 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 2.50 | 0.40 | 12 | next_open | signal | True |
| EXITGRID_RR1.8_SL0.4_H18 | 21 | 66.67 | 13.60 | 0.65 | 0.86 | 3.51 | 2.03 | 2 | 1.41 | 0.48 | 12.14 | 5 | 4.01 | exit | 6 | 1.80 | 0.50 | 0.05 | 0.40 | 0.60 | 26.00 | 16.00 | standard | 1.80 | 0.40 | 18 | next_open | signal | True |

## ロバスト性

### 通貨別

| symbol | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EURJPY | CURRENT_PRECALM_SHELF6_RR15 | 10 | 70.00 | 7.41 | 0.74 | 1.49 | 3.43 | 1.02 | 1 | 1.61 | 0.73 | 15.00 | 2 | 0.47 |
| AUDJPY | CURRENT_PRECALM_SHELF6_RR15 | 7 | 71.43 | 5.35 | 0.76 | 1.48 | 3.61 | 1.03 | 1 | 1.33 | 0.54 | 10.71 | 1 | 1.48 |
| USDJPY | CURRENT_PRECALM_SHELF6_RR15 | 13 | 46.15 | 1.82 | 0.14 | -1.01 | 1.26 | 3.62 | 3 | 1.22 | 0.72 | 10.15 | 2 | 2.99 |
| GBPJPY | CURRENT_PRECALM_SHELF6_RR15 | 4 | 50.00 | 0.97 | 0.24 | 0.24 | 1.47 | 2.04 | 2 | 0.96 | 1.29 | 21.25 | 0 | 0.00 |

### 開発/検証/OOS

| split | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EARLY_2015_2017 | CURRENT_PRECALM_SHELF6_RR15 | 10 | 90.00 | 12.39 | 1.24 | 1.49 | 13.16 | 1.02 | 1 | 1.77 | 0.60 | 11.60 | 0 | 0.00 |
| OOS_2024_2026 | CURRENT_PRECALM_SHELF6_RR15 | 10 | 60.00 | 4.88 | 0.49 | 1.48 | 2.20 | 1.02 | 2 | 1.25 | 0.76 | 13.60 | 5 | 4.93 |
| VALID_2022_2023 | CURRENT_PRECALM_SHELF6_RR15 | 5 | 60.00 | 2.48 | 0.50 | 1.49 | 2.23 | 2.02 | 2 | 1.46 | 0.59 | 14.20 | 0 | 0.00 |
| DEV_2018_2021 | CURRENT_PRECALM_SHELF6_RR15 | 9 | 22.22 | -4.21 | -0.47 | -1.02 | 0.41 | 4.08 | 5 | 0.85 | 1.00 | 13.22 | 0 | 0.00 |

### 年別

| year | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | CURRENT_PRECALM_SHELF6_RR15 | 6 | 83.33 | 6.46 | 1.08 | 1.49 | 7.34 | 1.02 | 1 | 1.48 | 0.63 | 10.00 | 0 | 0.00 |
| 2025 | CURRENT_PRECALM_SHELF6_RR15 | 4 | 100.00 | 5.95 | 1.49 | 1.49 | inf | 0.00 | 0 | 1.96 | 0.31 | 7.25 | 4 | 5.95 |
| 2015 | CURRENT_PRECALM_SHELF6_RR15 | 3 | 100.00 | 4.53 | 1.51 | 1.51 | inf | 0.00 | 0 | 2.26 | 0.45 | 10.33 | 0 | 0.00 |
| 2023 | CURRENT_PRECALM_SHELF6_RR15 | 3 | 66.67 | 1.97 | 0.66 | 1.49 | 2.96 | 0.00 | 1 | 1.48 | 0.56 | 11.67 | 0 | 0.00 |
| 2017 | CURRENT_PRECALM_SHELF6_RR15 | 1 | 100.00 | 1.40 | 1.40 | 1.40 | inf | 0.00 | 0 | 1.99 | 0.87 | 25.00 | 0 | 0.00 |
| 2021 | CURRENT_PRECALM_SHELF6_RR15 | 4 | 50.00 | 0.90 | 0.23 | 0.23 | 1.44 | 2.05 | 2 | 1.57 | 0.83 | 18.75 | 0 | 0.00 |
| 2022 | CURRENT_PRECALM_SHELF6_RR15 | 2 | 50.00 | 0.50 | 0.25 | 0.25 | 1.50 | 1.01 | 1 | 1.43 | 0.63 | 18.00 | 0 | 0.00 |
| 2024 | CURRENT_PRECALM_SHELF6_RR15 | 5 | 40.00 | -0.05 | -0.01 | -1.01 | 0.98 | 1.02 | 2 | 0.80 | 0.98 | 17.00 | 0 | 0.00 |
| 2026 | CURRENT_PRECALM_SHELF6_RR15 | 1 | 0.00 | -1.02 | -1.02 | -1.02 | 0.00 | 0.00 | 1 | 0.68 | 1.48 | 22.00 | 1 | -1.02 |
| 2018 | CURRENT_PRECALM_SHELF6_RR15 | 1 | 0.00 | -1.02 | -1.02 | -1.02 | 0.00 | 0.00 | 1 | 0.50 | 1.02 | 5.00 | 0 | 0.00 |
| 2020 | CURRENT_PRECALM_SHELF6_RR15 | 2 | 0.00 | -2.04 | -1.02 | -1.02 | 0.00 | 1.01 | 2 | 0.14 | 1.19 | 10.00 | 0 | 0.00 |
| 2019 | CURRENT_PRECALM_SHELF6_RR15 | 2 | 0.00 | -2.05 | -1.02 | -1.02 | 0.00 | 1.03 | 2 | 0.33 | 1.16 | 9.50 | 0 | 0.00 |

### ADX帯

| adx_band | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18-22 | CURRENT_PRECALM_SHELF6_RR15 | 12 | 66.67 | 7.89 | 0.66 | 1.48 | 2.94 | 2.05 | 2 | 1.26 | 0.58 | 11.58 | 2 | 2.97 |
| <=18 | CURRENT_PRECALM_SHELF6_RR15 | 13 | 53.85 | 4.30 | 0.33 | 1.48 | 1.70 | 3.05 | 3 | 1.15 | 0.82 | 13.38 | 2 | 0.47 |
| 22-26 | CURRENT_PRECALM_SHELF6_RR15 | 9 | 55.56 | 3.36 | 0.37 | 1.40 | 1.82 | 4.07 | 4 | 1.67 | 0.87 | 14.33 | 1 | 1.49 |
| 26-30 |  | 0 | 0.00 | 0.00 | 0.00 |  |  | 0.00 | 0 |  |  |  | 0 | 0.00 |
| >30 |  | 0 | 0.00 | 0.00 | 0.00 |  |  | 0.00 | 0 |  |  |  | 0 | 0.00 |

### 棚幅帯

| shelf_range_band | label | trades | win_rate | total_r_after_cost | avg_r_after_cost | median_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | avg_bars_held | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.2-1.5 | CURRENT_PRECALM_SHELF6_RR15 | 16 | 56.25 | 6.25 | 0.39 | 1.47 | 1.88 | 4.18 | 4 | 1.21 | 0.79 | 13.81 | 3 | 4.45 |
| <=1.2 | CURRENT_PRECALM_SHELF6_RR15 | 5 | 80.00 | 4.98 | 1.00 | 1.49 | 5.89 | 1.02 | 1 | 1.65 | 0.43 | 6.80 | 2 | 0.48 |
| 1.5-1.8 | CURRENT_PRECALM_SHELF6_RR15 | 13 | 53.85 | 4.31 | 0.33 | 1.40 | 1.71 | 3.10 | 3 | 1.36 | 0.83 | 14.38 | 0 | 0.00 |
| 1.8-2.1 |  | 0 | 0.00 | 0.00 | 0.00 |  |  | 0.00 | 0 |  |  |  | 0 | 0.00 |
| >2.1 |  | 0 | 0.00 | 0.00 | 0.00 |  |  | 0.00 | 0 |  |  |  | 0 | 0.00 |

## 本番判断

採用区分: **保留寄りの採用候補**。

運用するなら、通常リスクではなく 0.25R からフォワード記録。最低30件、できれば50件までTradingView/Python時刻一致を確認してから判断する。

強く残った解釈:

- 勝ち負けを分けたのは「Vの派手さ」より、V前が過熱していないことと、棚形成後にすぐ順行できること。
- 実体比率・終値位置・ブレイク幅は必要条件ではあるが、そこを厳しくしすぎても勝ち負けの説明力はあまり増えない。
- ADXは18-22帯がもっとも素直。ADX<=22案は有望だが、件数と時期偏りを考えると本線へ即採用は早い。
- 棚幅は1.8ATR以内で十分。1.5ATR以内は品質改善候補だが、件数を落とすため監視バリアント扱い。
- 2018-2021の弱さが最大の懸念。ここを完全に消す条件だけを探すと過剰最適化になりやすい。

残す条件:

- V後に棚を作る
- 棚高値を終値で抜く
- 棚安値がVの50%前後を維持
- PRECALMで既存トレンド途中乗りを抑える

削る/保留する条件:

- 自作休眠ラインの同時ブレイクは件数不足
- Donchian55は大きく伸びる前兆だがOOS件数不足
- 過度に厳しい棚幅・終値位置条件は件数が細りすぎる
- 棚7本、SL0.4ATR、最大保有12/18本は高PFだが、入口本質ではなく別研究として保留

追加すべき検証:

- Entry基準TPでPine/Pythonを統一
- 固定1.5Rと半分利確+トレーリングの比較
- 2026年以降のフォワード記録
- TradingViewのシグナル時刻とPython `current_trades_detail.csv` の一致確認

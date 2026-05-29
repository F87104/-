# H4 Low Stagnation Short: Previous D1 Regime Filter Study

Status: 検証途中。H4安値停滞ショートに、前日確定の日足地合いを重ねる検証。

## 結論候補

- 最も実戦向きに見える追加条件は `前日D1 RSI 35-55`。
- 意味: 日足は弱いが、まだ売られ過ぎすぎない状態だけを残す。
- Pineでは未確定日足を使わず、`request.security(..., "D", ta.rsi(close, 14)[1])` の形にする。
- H4側は既存の品質フィルタ `break_depth>=0.10ATR` と `break_close_location<=0.50` を重ねると強い。
- さらに厳選するなら `support_age>10 or break_depth>=0.20ATR` を追加する。

## 重要候補

| sample | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_no_AUD_USD | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55 | 37 | 23 | 62.16 | 56.52 | 13.28 | 14.13 | 5.76 | 0.61 | 2.31 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | quality | 37 | 27 | 72.97 | 51.85 | 8.61 | 13.34 | 4.98 | 0.49 | 1.98 | 2.36 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | strict | 37 | 24 | 64.86 | 54.17 | 10.92 | 13.60 | 5.24 | 0.57 | 2.17 | 2.36 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__quality | 37 | 16 | 43.24 | 75.00 | 31.76 | 18.90 | 10.54 | 1.18 | 5.56 | 1.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__strict | 37 | 14 | 37.84 | 78.57 | 35.33 | 18.14 | 9.77 | 1.30 | 6.84 | 1.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55__strict | 26 | 11 | 42.31 | 72.73 | 30.42 | 12.60 | 6.43 | 1.15 | 5.06 | 1.07 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | H1_LH_confirm | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | H1_LH_confirm__prevD1_RSI_35_55 | 26 | 7 | 26.92 | 71.43 | 29.12 | 7.68 | 1.52 | 1.10 | 4.58 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | prevD1_close_below_EMA50 | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |

## 改善候補一覧

ベースラインより勝率とPFが改善し、5件以上ある条件。

| sample | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | prevD1_RSI_35_55__strict | 26 | 11 | 42.31 | 72.73 | 30.42 | 12.60 | 6.43 | 1.15 | 5.06 | 1.07 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55__quality | 26 | 12 | 46.15 | 66.67 | 24.36 | 11.56 | 5.40 | 0.96 | 3.79 | 1.07 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | strict | 26 | 18 | 69.23 | 55.56 | 13.25 | 11.46 | 5.30 | 0.64 | 2.40 | 2.09 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55__break_depth_ge_0_15 | 26 | 10 | 38.46 | 70.00 | 27.69 | 10.60 | 4.44 | 1.06 | 4.39 | 1.07 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | H1_LH_confirm | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.54 | 3.38 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55__close_location_le_0_50 | 26 | 14 | 53.85 | 57.14 | 14.84 | 9.49 | 3.33 | 0.68 | 2.53 | 2.06 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | quality | 26 | 20 | 76.92 | 50.00 | 7.69 | 9.39 | 3.23 | 0.47 | 1.91 | 2.09 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55__support60_119 | 26 | 6 | 23.08 | 83.33 | 41.03 | 8.74 | 2.58 | 1.46 | 9.56 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_30_55 | 26 | 24 | 92.31 | 45.83 | 3.53 | 8.22 | 2.06 | 0.34 | 1.61 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | H1_LH_confirm__prevD1_RSI_35_55 | 26 | 7 | 26.92 | 71.43 | 29.12 | 7.68 | 1.52 | 1.10 | 4.58 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_35_55 | 26 | 16 | 61.54 | 50.00 | 7.69 | 7.40 | 1.23 | 0.46 | 1.89 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_stack_down | 26 | 14 | 53.85 | 50.00 | 7.69 | 6.56 | 0.40 | 0.47 | 1.92 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_close_below_EMA50 | 26 | 23 | 88.46 | 43.48 | 1.17 | 6.28 | 0.12 | 0.27 | 1.47 | 3.14 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_close_location_lt_0_50 | 26 | 13 | 50.00 | 46.15 | 3.85 | 4.57 | -1.59 | 0.35 | 1.63 | 2.07 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | prevD1_RSI_40_55 | 26 | 9 | 34.62 | 44.44 | 2.14 | 2.73 | -3.43 | 0.30 | 1.53 | 3.13 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | H1_LH_rebreak24__prevD1_RSI_35_55 | 26 | 7 | 26.92 | 42.86 | 0.55 | 1.74 | -4.43 | 0.25 | 1.42 | 1.08 | EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__quality | 37 | 16 | 43.24 | 75.00 | 31.76 | 18.90 | 10.54 | 1.18 | 5.56 | 1.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__strict | 37 | 14 | 37.84 | 78.57 | 35.33 | 18.14 | 9.77 | 1.30 | 6.84 | 1.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__break_depth_ge_0_15 | 37 | 15 | 40.54 | 73.33 | 30.09 | 16.73 | 8.37 | 1.12 | 4.85 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__close_location_le_0_50 | 37 | 19 | 51.35 | 63.16 | 19.91 | 15.57 | 7.20 | 0.82 | 3.08 | 2.06 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55 | 37 | 23 | 62.16 | 56.52 | 13.28 | 14.13 | 5.76 | 0.61 | 2.31 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | strict | 37 | 24 | 64.86 | 54.17 | 10.92 | 13.60 | 5.24 | 0.57 | 2.17 | 2.36 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | quality | 37 | 27 | 72.97 | 51.85 | 8.61 | 13.34 | 4.98 | 0.49 | 1.98 | 2.36 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_30_55 | 37 | 33 | 89.19 | 48.48 | 5.24 | 12.85 | 4.48 | 0.39 | 1.71 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | H1_LH_confirm | 37 | 14 | 37.84 | 57.14 | 13.90 | 9.54 | 1.18 | 0.68 | 2.53 | 2.10 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_close_location_lt_0_50 | 37 | 19 | 51.35 | 52.63 | 9.39 | 9.38 | 1.01 | 0.49 | 1.96 | 2.07 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_35_55__support60_119 | 37 | 6 | 16.22 | 83.33 | 40.09 | 8.74 | 0.38 | 1.46 | 9.56 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_close_below_EMA50 | 37 | 34 | 91.89 | 44.12 | 0.87 | 8.49 | 0.12 | 0.25 | 1.42 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_RSI_40_55 | 37 | 12 | 32.43 | 58.33 | 15.09 | 8.18 | -0.18 | 0.68 | 2.58 | 3.13 | CHFJPY,EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | H1_LH_confirm__prevD1_RSI_35_55 | 37 | 7 | 18.92 | 71.43 | 28.19 | 7.68 | -0.69 | 1.10 | 4.58 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | prevD1_stack_down | 37 | 19 | 51.35 | 47.37 | 4.13 | 6.86 | -1.51 | 0.36 | 1.65 | 2.58 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | strict | 11 | 8 | 72.73 | 100.00 | 27.27 | 15.71 | 3.15 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | quality | 11 | 9 | 81.82 | 88.89 | 16.16 | 14.67 | 2.12 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_close_below_EMA50 | 11 | 10 | 90.91 | 80.00 | 7.27 | 13.59 | 1.04 | 1.36 | 7.43 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_RSI_35_55__strict | 11 | 6 | 54.55 | 100.00 | 27.27 | 11.75 | -0.81 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | H1_LH_confirm | 11 | 7 | 63.64 | 85.71 | 12.99 | 10.72 | -1.83 | 1.53 | 10.97 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_RSI_35_55__quality | 11 | 7 | 63.64 | 85.71 | 12.99 | 10.71 | -1.85 | 1.53 | 11.31 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_RSI_35_55__break_depth_ge_0_15 | 11 | 7 | 63.64 | 85.71 | 12.99 | 10.71 | -1.85 | 1.53 | 11.31 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_stack_down | 11 | 5 | 45.45 | 100.00 | 27.27 | 9.77 | -2.78 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | prevD1_RSI_35_55__close_location_le_0_50 | 11 | 8 | 72.73 | 75.00 | 2.27 | 9.67 | -2.89 | 1.21 | 5.65 | 1.04 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | H1_LH_confirm__prevD1_RSI_35_55 | 11 | 5 | 45.45 | 80.00 | 7.27 | 6.76 | -5.79 | 1.35 | 7.29 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | strict | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | prevD1_close_below_EMA50 | 9 | 8 | 88.89 | 100.00 | 11.11 | 15.71 | 1.04 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | H1_LH_confirm | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.80 | -2.87 | 1.97 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | prevD1_RSI_35_55__strict | 9 | 6 | 66.67 | 100.00 | 11.11 | 11.75 | -2.92 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | prevD1_stack_down | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.77 | -4.90 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## RSI閾値感度

| sample | rsi_low | rsi_high | h4_filter | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | 35 | 50 | strict | 11 | 72.73 | 12.60 | 1.15 | 5.06 | 1.07 |
| practical_core4 | 35 | 55 | strict | 11 | 72.73 | 12.60 | 1.15 | 5.06 | 1.07 |
| practical_core4 | 35 | 60 | strict | 11 | 72.73 | 12.60 | 1.15 | 5.06 | 1.07 |
| practical_core4 | 30 | 50 | strict | 17 | 58.82 | 12.47 | 0.73 | 2.73 | 2.09 |
| practical_core4 | 30 | 55 | strict | 17 | 58.82 | 12.47 | 0.73 | 2.73 | 2.09 |
| practical_core4 | 30 | 60 | strict | 17 | 58.82 | 12.47 | 0.73 | 2.73 | 2.09 |
| practical_core4 | 35 | 50 | quality | 12 | 66.67 | 11.56 | 0.96 | 3.79 | 1.07 |
| practical_core4 | 35 | 55 | quality | 12 | 66.67 | 11.56 | 0.96 | 3.79 | 1.07 |
| practical_core4 | 35 | 60 | quality | 12 | 66.67 | 11.56 | 0.96 | 3.79 | 1.07 |
| practical_core4 | 25 | 50 | strict | 18 | 55.56 | 11.46 | 0.64 | 2.40 | 2.09 |
| practical_core4 | 25 | 55 | strict | 18 | 55.56 | 11.46 | 0.64 | 2.40 | 2.09 |
| practical_core4 | 25 | 60 | strict | 18 | 55.56 | 11.46 | 0.64 | 2.40 | 2.09 |
| practical_core4 | 30 | 50 | quality | 19 | 52.63 | 10.41 | 0.55 | 2.12 | 2.09 |
| practical_core4 | 30 | 55 | quality | 19 | 52.63 | 10.41 | 0.55 | 2.12 | 2.09 |
| practical_core4 | 30 | 60 | quality | 19 | 52.63 | 10.41 | 0.55 | 2.12 | 2.09 |
| practical_core4 | 25 | 50 | quality | 20 | 50.00 | 9.39 | 0.47 | 1.91 | 2.09 |
| practical_core4 | 25 | 55 | quality | 20 | 50.00 | 9.39 | 0.47 | 1.91 | 2.09 |
| practical_core4 | 25 | 60 | quality | 20 | 50.00 | 9.39 | 0.47 | 1.91 | 2.09 |
| practical_core4 | 30 | 50 | none | 24 | 45.83 | 8.22 | 0.34 | 1.61 | 3.08 |
| practical_core4 | 30 | 55 | none | 24 | 45.83 | 8.22 | 0.34 | 1.61 | 3.08 |
| practical_core4 | 30 | 60 | none | 24 | 45.83 | 8.22 | 0.34 | 1.61 | 3.08 |
| practical_core4 | 35 | 50 | none | 16 | 50.00 | 7.40 | 0.46 | 1.89 | 3.08 |
| practical_core4 | 35 | 55 | none | 16 | 50.00 | 7.40 | 0.46 | 1.89 | 3.08 |
| practical_core4 | 35 | 60 | none | 16 | 50.00 | 7.40 | 0.46 | 1.89 | 3.08 |
| practical_core4 | 25 | 50 | none | 26 | 42.31 | 6.16 | 0.24 | 1.40 | 3.08 |
| practical_core4 | 25 | 55 | none | 26 | 42.31 | 6.16 | 0.24 | 1.40 | 3.08 |
| practical_core4 | 25 | 60 | none | 26 | 42.31 | 6.16 | 0.24 | 1.40 | 3.08 |
| practical_core4 | 40 | 50 | strict | 6 | 66.67 | 5.83 | 0.97 | 3.79 | 1.02 |
| practical_core4 | 40 | 55 | strict | 6 | 66.67 | 5.83 | 0.97 | 3.79 | 1.02 |
| practical_core4 | 40 | 60 | strict | 6 | 66.67 | 5.83 | 0.97 | 3.79 | 1.02 |
| practical_core4 | 40 | 50 | quality | 7 | 57.14 | 4.79 | 0.68 | 2.53 | 1.07 |
| practical_core4 | 40 | 55 | quality | 7 | 57.14 | 4.79 | 0.68 | 2.53 | 1.07 |
| practical_core4 | 40 | 60 | quality | 7 | 57.14 | 4.79 | 0.68 | 2.53 | 1.07 |
| practical_core4 | 40 | 50 | none | 9 | 44.44 | 2.73 | 0.30 | 1.53 | 3.13 |
| practical_core4 | 40 | 55 | none | 9 | 44.44 | 2.73 | 0.30 | 1.53 | 3.13 |
| practical_core4 | 40 | 60 | none | 9 | 44.44 | 2.73 | 0.30 | 1.53 | 3.13 |
| practical_no_AUD_USD | 35 | 50 | quality | 16 | 75.00 | 18.90 | 1.18 | 5.56 | 1.07 |
| practical_no_AUD_USD | 35 | 55 | quality | 16 | 75.00 | 18.90 | 1.18 | 5.56 | 1.07 |
| practical_no_AUD_USD | 35 | 60 | quality | 16 | 75.00 | 18.90 | 1.18 | 5.56 | 1.07 |
| practical_no_AUD_USD | 35 | 50 | strict | 14 | 78.57 | 18.14 | 1.30 | 6.84 | 1.07 |
| practical_no_AUD_USD | 35 | 55 | strict | 14 | 78.57 | 18.14 | 1.30 | 6.84 | 1.07 |
| practical_no_AUD_USD | 35 | 60 | strict | 14 | 78.57 | 18.14 | 1.30 | 6.84 | 1.07 |
| practical_no_AUD_USD | 30 | 50 | strict | 22 | 59.09 | 15.91 | 0.72 | 2.71 | 2.09 |
| practical_no_AUD_USD | 30 | 55 | strict | 22 | 59.09 | 15.91 | 0.72 | 2.71 | 2.09 |
| practical_no_AUD_USD | 30 | 60 | strict | 22 | 59.09 | 15.91 | 0.72 | 2.71 | 2.09 |
| practical_no_AUD_USD | 30 | 50 | quality | 25 | 56.00 | 15.65 | 0.63 | 2.38 | 2.09 |
| practical_no_AUD_USD | 30 | 55 | quality | 25 | 56.00 | 15.65 | 0.63 | 2.38 | 2.09 |
| practical_no_AUD_USD | 30 | 60 | quality | 25 | 56.00 | 15.65 | 0.63 | 2.38 | 2.09 |
| practical_no_AUD_USD | 35 | 50 | none | 23 | 56.52 | 14.13 | 0.61 | 2.31 | 3.08 |
| practical_no_AUD_USD | 35 | 55 | none | 23 | 56.52 | 14.13 | 0.61 | 2.31 | 3.08 |
| practical_no_AUD_USD | 35 | 60 | none | 23 | 56.52 | 14.13 | 0.61 | 2.31 | 3.08 |
| practical_no_AUD_USD | 25 | 50 | strict | 24 | 54.17 | 13.60 | 0.57 | 2.17 | 2.36 |
| practical_no_AUD_USD | 25 | 55 | strict | 24 | 54.17 | 13.60 | 0.57 | 2.17 | 2.36 |
| practical_no_AUD_USD | 25 | 60 | strict | 24 | 54.17 | 13.60 | 0.57 | 2.17 | 2.36 |
| practical_no_AUD_USD | 25 | 50 | quality | 27 | 51.85 | 13.34 | 0.49 | 1.98 | 2.36 |
| practical_no_AUD_USD | 25 | 55 | quality | 27 | 51.85 | 13.34 | 0.49 | 1.98 | 2.36 |
| practical_no_AUD_USD | 25 | 60 | quality | 27 | 51.85 | 13.34 | 0.49 | 1.98 | 2.36 |
| practical_no_AUD_USD | 30 | 50 | none | 33 | 48.48 | 12.85 | 0.39 | 1.71 | 3.08 |
| practical_no_AUD_USD | 30 | 55 | none | 33 | 48.48 | 12.85 | 0.39 | 1.71 | 3.08 |
| practical_no_AUD_USD | 30 | 60 | none | 33 | 48.48 | 12.85 | 0.39 | 1.71 | 3.08 |

## 本線候補の期間別

| rule | period | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| prevD1_RSI35_55__strict | test_2021_2024 | 5 | 100.00 | 9.77 | 1.95 | inf | 0.00 |
| prevD1_RSI35_55__strict | train_2015_2020 | 8 | 62.50 | 6.38 | 0.80 | 3.05 | 2.09 |
| prevD1_RSI35_55__strict | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |

## 本線候補の通貨別

| rule | symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| prevD1_RSI35_55__strict | SILVER | 3 | 100.00 | 5.54 | 1.85 | inf | 0.00 |
| prevD1_RSI35_55__strict | GBPJPY | 4 | 75.00 | 4.91 | 1.23 | 5.81 | 1.02 |
| prevD1_RSI35_55__strict | EURJPY | 3 | 66.67 | 2.94 | 0.98 | 3.89 | 0.00 |
| prevD1_RSI35_55__strict | CHFJPY | 3 | 66.67 | 2.80 | 0.93 | 3.62 | 1.07 |
| prevD1_RSI35_55__strict | XAUUSD | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |

## 本線候補のトレード一覧

| symbol | entry_time | period | base_r_after_cost | prev_d1_rsi14 | support_age_bars | break_depth_atr | break_close_location | lookback_bars | pre_break_regime |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | 2015-06-05 12:00:00 | train_2015_2020 | 1.94 | 37.17 | 111 | 0.21 | 0.24 | 120 | mixed_or_wide_range |
| SILVER | 2015-11-03 12:00:00 | train_2015_2020 | 1.77 | 42.91 | 1 | 0.32 | 0.37 | 120 | trend_continuation_break |
| GBPJPY | 2016-09-19 12:00:00 | train_2015_2020 | 1.97 | 40.33 | 84 | 0.12 | 0.08 | 90 | range_support_break |
| SILVER | 2016-11-16 12:00:00 | train_2015_2020 | 1.90 | 36.23 | 3 | 0.22 | 0.07 | 180 | trend_continuation_break |
| GBPJPY | 2018-11-16 20:00:00 | train_2015_2020 | -1.02 | 42.03 | 60 | 0.29 | 0.00 | 60 | range_support_break |
| CHFJPY | 2019-04-22 16:00:00 | train_2015_2020 | 1.90 | 37.61 | 114 | 0.18 | 0.41 | 120 | mixed_or_wide_range |
| CHFJPY | 2020-01-28 12:00:00 | train_2015_2020 | -1.07 | 46.11 | 1 | 0.20 | 0.06 | 60 | trend_continuation_break |
| EURJPY | 2020-04-02 12:00:00 | train_2015_2020 | -1.02 | 39.12 | 55 | 0.15 | 0.17 | 60 | mixed_or_wide_range |
| EURJPY | 2022-03-03 12:00:00 | test_2021_2024 | 1.98 | 37.99 | 116 | 0.15 | 0.00 | 120 | range_support_break |
| SILVER | 2023-06-21 08:00:00 | test_2021_2024 | 1.86 | 38.76 | 19 | 0.26 | 0.01 | 60 | mixed_or_wide_range |
| GBPJPY | 2023-12-13 12:00:00 | test_2021_2024 | 1.98 | 40.55 | 73 | 0.21 | 0.23 | 120 | range_support_break |
| EURJPY | 2024-07-22 04:00:00 | test_2021_2024 | 1.98 | 45.91 | 17 | 0.59 | 0.03 | 60 | mixed_or_wide_range |
| CHFJPY | 2024-11-29 00:00:00 | test_2021_2024 | 1.97 | 35.58 | 1 | 0.26 | 0.41 | 120 | trend_continuation_break |
| GBPJPY | 2025-01-15 08:00:00 | oos_2025_2026 | 1.98 | 43.44 | 3 | 0.42 | 0.49 | 120 | trend_continuation_break |

## 暫定解釈

- D1 RSI 35-55 は、日足が強すぎる局面と売られ過ぎの反発局面を同時に避けるフィルタとして働いている。
- `practical_no_AUD_USD + D1 RSI35-55 + H4品質` は、37件から16件へ絞って、総R +8.36R -> +18.90R、PF 1.37 -> 5.56。
- `strict` まで入れると、14件、勝率78.57%、PF 6.84。精度重視のPineラベル候補。
- SILVERは過去の停滞型ショートでは弱かったが、この条件では3件全勝。最初はCore4版とSILVER込み版を別ラベルで比較するのが安全。
- H1戻り高値切り下げとの重複は、精度タグとしては良いが7件まで減るため、最初から必須化しない。

## 出力CSV

- `enriched_with_prev_d1.csv`
- `rule_summary.csv`
- `threshold_sweep.csv`
- `candidate_period_summary.csv`
- `candidate_symbol_summary.csv`
- `candidate_trades.csv`
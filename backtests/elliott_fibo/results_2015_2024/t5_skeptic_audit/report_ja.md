# T5 + MACD + BB 懐疑監査

## 目的

結果が良すぎる候補について、未来参照ではなくても起こりうる「最適化しすぎ」「重複カウント」「約定/コストの甘さ」をチェックする。

## 重要なコード確認

- V候補のピボットは `confirm_i <= 現在バー` になってからだけ active に入るため、ピボット確定前の未来情報は使っていない。
- エントリーはシグナル足ではなく、シグナル次足の始値。
- MACD/BB等のフィルタは `signal_time` の足で付与しており、次足エントリー前に確定している情報だけを見る設計。
- SL/TP同時到達時は SL 優先で処理しているため、同一足内の約定判定は保守的。

## 候補別サマリー

| candidate | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Current_060_110 | 157 | 49.68 | 57.17 | 0.36 | 1.78 | 11.89 | 13 |
| Robust_075_105_width7 | 129 | 52.71 | 64.52 | 0.50 | 2.17 | 8.78 | 10 |
| Strict_075_100_width7 | 102 | 54.90 | 59.26 | 0.58 | 2.49 | 5.74 | 7 |

## 重複・同時保有チェック

| candidate | trades | exact_duplicate_rows | same_v_candidate_reuse | removed_by_one_global_position | removed_by_one_symbol_position |
| --- | --- | --- | --- | --- | --- |
| Current_060_110 | 157 | 0 | 0 | 84 | 0 |
| Robust_075_105_width7 | 129 | 0 | 0 | 62 | 0 |
| Strict_075_100_width7 | 102 | 0 | 0 | 44 | 0 |

## ストレステスト

| candidate | stress | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current_060_110 | normal | 157 | 49.68 | 57.17 | 0.36 | 1.78 | 11.89 | 13 |
| Current_060_110 | extra_cost_0.05R_each | 157 | 49.68 | 49.32 | 0.31 | 1.64 | 12.69 | 13 |
| Current_060_110 | extra_cost_0.10R_each | 157 | 49.68 | 41.47 | 0.26 | 1.51 | 13.65 | 13 |
| Current_060_110 | extra_cost_0.20R_each | 157 | 47.77 | 25.77 | 0.16 | 1.29 | 16.15 | 13 |
| Current_060_110 | original_cost_x2 | 157 | 49.68 | 55.09 | 0.35 | 1.74 | 12.24 | 13 |
| Current_060_110 | original_cost_x3 | 157 | 49.68 | 53.01 | 0.34 | 1.70 | 12.58 | 13 |
| Current_060_110 | original_cost_x5 | 157 | 49.68 | 48.84 | 0.31 | 1.63 | 13.26 | 13 |
| Current_060_110 | one_global_position | 73 | 50.68 | 28.88 | 0.40 | 1.90 | 5.72 | 7 |
| Current_060_110 | one_symbol_position | 157 | 49.68 | 57.17 | 0.36 | 1.78 | 11.89 | 13 |
| Current_060_110 | first_signal_per_day | 140 | 49.29 | 50.48 | 0.36 | 1.78 | 11.89 | 13 |
| Current_060_110 | first_signal_per_week | 125 | 49.60 | 46.90 | 0.38 | 1.82 | 10.80 | 12 |
| Current_060_110 | exclude_silver | 134 | 51.49 | 56.39 | 0.42 | 1.94 | 8.26 | 9 |
| Current_060_110 | 2021_2024_only | 69 | 59.42 | 40.77 | 0.59 | 2.57 | 7.26 | 4 |
| Current_060_110 | 2023_2024_only | 29 | 72.41 | 28.32 | 0.98 | 4.92 | 3.04 | 3 |
| Robust_075_105_width7 | normal | 129 | 52.71 | 64.52 | 0.50 | 2.17 | 8.78 | 10 |
| Robust_075_105_width7 | extra_cost_0.05R_each | 129 | 52.71 | 58.07 | 0.45 | 2.00 | 9.43 | 10 |
| Robust_075_105_width7 | extra_cost_0.10R_each | 129 | 52.71 | 51.62 | 0.40 | 1.84 | 10.08 | 10 |
| Robust_075_105_width7 | extra_cost_0.20R_each | 129 | 50.39 | 38.72 | 0.30 | 1.57 | 11.38 | 10 |
| Robust_075_105_width7 | original_cost_x2 | 129 | 52.71 | 62.83 | 0.49 | 2.13 | 9.01 | 10 |
| Robust_075_105_width7 | original_cost_x3 | 129 | 52.71 | 61.14 | 0.47 | 2.08 | 9.24 | 10 |
| Robust_075_105_width7 | original_cost_x5 | 129 | 52.71 | 57.75 | 0.45 | 1.99 | 9.69 | 10 |
| Robust_075_105_width7 | one_global_position | 67 | 50.75 | 31.86 | 0.48 | 2.14 | 3.61 | 5 |
| Robust_075_105_width7 | one_symbol_position | 129 | 52.71 | 64.52 | 0.50 | 2.17 | 8.78 | 10 |
| Robust_075_105_width7 | first_signal_per_day | 119 | 52.94 | 61.44 | 0.52 | 2.23 | 8.78 | 10 |
| Robust_075_105_width7 | first_signal_per_week | 110 | 51.82 | 53.83 | 0.49 | 2.15 | 8.78 | 10 |
| Robust_075_105_width7 | exclude_silver | 112 | 54.46 | 61.00 | 0.54 | 2.33 | 5.62 | 7 |
| Robust_075_105_width7 | 2021_2024_only | 53 | 64.15 | 41.95 | 0.79 | 3.48 | 4.22 | 3 |
| Robust_075_105_width7 | 2023_2024_only | 24 | 75.00 | 26.76 | 1.11 | 6.16 | 3.04 | 3 |
| Strict_075_100_width7 | normal | 102 | 54.90 | 59.26 | 0.58 | 2.49 | 5.74 | 7 |
| Strict_075_100_width7 | extra_cost_0.05R_each | 102 | 54.90 | 54.16 | 0.53 | 2.29 | 6.09 | 7 |
| Strict_075_100_width7 | extra_cost_0.10R_each | 102 | 54.90 | 49.06 | 0.48 | 2.10 | 6.44 | 7 |
| Strict_075_100_width7 | extra_cost_0.20R_each | 102 | 52.94 | 38.86 | 0.38 | 1.79 | 7.14 | 7 |
| Strict_075_100_width7 | original_cost_x2 | 102 | 54.90 | 58.00 | 0.57 | 2.43 | 5.92 | 7 |
| Strict_075_100_width7 | original_cost_x3 | 102 | 54.90 | 56.74 | 0.56 | 2.38 | 6.10 | 7 |
| Strict_075_100_width7 | original_cost_x5 | 102 | 54.90 | 54.22 | 0.53 | 2.28 | 6.46 | 7 |
| Strict_075_100_width7 | one_global_position | 58 | 51.72 | 29.37 | 0.51 | 2.28 | 3.63 | 5 |
| Strict_075_100_width7 | one_symbol_position | 102 | 54.90 | 59.26 | 0.58 | 2.49 | 5.74 | 7 |
| Strict_075_100_width7 | first_signal_per_day | 94 | 56.38 | 58.39 | 0.62 | 2.68 | 5.74 | 7 |
| Strict_075_100_width7 | first_signal_per_week | 90 | 56.67 | 56.46 | 0.63 | 2.72 | 5.74 | 7 |
| Strict_075_100_width7 | exclude_silver | 89 | 57.30 | 57.47 | 0.65 | 2.75 | 5.08 | 4 |
| Strict_075_100_width7 | 2021_2024_only | 40 | 67.50 | 34.60 | 0.86 | 4.18 | 3.03 | 3 |
| Strict_075_100_width7 | 2023_2024_only | 19 | 78.95 | 23.06 | 1.21 | 8.28 | 2.03 | 2 |

## 2年ごとの成績

| candidate | period | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current_060_110 | 2015-2016 | 31 | 29.03 | -2.22 | -0.07 | 0.89 | 11.89 | 13 |
| Current_060_110 | 2017-2018 | 26 | 42.31 | 4.79 | 0.18 | 1.35 | 4.10 | 4 |
| Current_060_110 | 2019-2020 | 31 | 54.84 | 13.83 | 0.45 | 2.02 | 5.06 | 5 |
| Current_060_110 | 2021-2022 | 40 | 50.00 | 12.45 | 0.31 | 1.66 | 7.26 | 4 |
| Current_060_110 | 2023-2024 | 29 | 72.41 | 28.32 | 0.98 | 4.92 | 3.04 | 3 |
| Robust_075_105_width7 | 2015-2016 | 27 | 33.33 | 1.91 | 0.07 | 1.12 | 8.78 | 10 |
| Robust_075_105_width7 | 2017-2018 | 23 | 43.48 | 5.73 | 0.25 | 1.50 | 4.21 | 3 |
| Robust_075_105_width7 | 2019-2020 | 26 | 57.69 | 14.94 | 0.57 | 2.41 | 4.05 | 4 |
| Robust_075_105_width7 | 2021-2022 | 29 | 55.17 | 15.19 | 0.52 | 2.29 | 4.22 | 3 |
| Robust_075_105_width7 | 2023-2024 | 24 | 75.00 | 26.76 | 1.11 | 6.16 | 3.04 | 3 |
| Strict_075_100_width7 | 2015-2016 | 20 | 40.00 | 5.95 | 0.30 | 1.60 | 5.74 | 7 |
| Strict_075_100_width7 | 2017-2018 | 19 | 42.11 | 4.91 | 0.26 | 1.52 | 3.20 | 3 |
| Strict_075_100_width7 | 2019-2020 | 23 | 56.52 | 13.79 | 0.60 | 2.44 | 4.05 | 4 |
| Strict_075_100_width7 | 2021-2022 | 21 | 57.14 | 11.53 | 0.55 | 2.49 | 3.03 | 3 |
| Strict_075_100_width7 | 2023-2024 | 19 | 78.95 | 23.06 | 1.21 | 8.28 | 2.03 | 2 |

## 通貨別

| candidate | symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current_060_110 | AUDJPY | 21 | 52.38 | 7.50 | 0.36 | 1.74 | 5.06 | 5 |
| Current_060_110 | CHFJPY | 17 | 47.06 | 4.55 | 0.27 | 1.50 | 3.02 | 3 |
| Current_060_110 | EURJPY | 25 | 44.00 | 3.99 | 0.16 | 1.30 | 7.04 | 7 |
| Current_060_110 | GBPJPY | 26 | 57.69 | 12.88 | 0.50 | 2.16 | 4.03 | 4 |
| Current_060_110 | SILVER | 23 | 39.13 | 0.79 | 0.03 | 1.06 | 4.52 | 5 |
| Current_060_110 | USDJPY | 24 | 54.17 | 16.24 | 0.68 | 2.89 | 3.48 | 4 |
| Current_060_110 | XAUUSD | 21 | 52.38 | 11.22 | 0.53 | 2.41 | 2.02 | 3 |
| Robust_075_105_width7 | AUDJPY | 21 | 52.38 | 7.50 | 0.36 | 1.74 | 5.06 | 5 |
| Robust_075_105_width7 | CHFJPY | 14 | 50.00 | 5.89 | 0.42 | 1.83 | 2.03 | 2 |
| Robust_075_105_width7 | EURJPY | 18 | 44.44 | 3.81 | 0.21 | 1.41 | 5.03 | 5 |
| Robust_075_105_width7 | GBPJPY | 21 | 66.67 | 15.97 | 0.76 | 3.26 | 2.02 | 2 |
| Robust_075_105_width7 | SILVER | 17 | 41.18 | 3.52 | 0.21 | 1.39 | 3.16 | 4 |
| Robust_075_105_width7 | USDJPY | 21 | 57.14 | 16.15 | 0.77 | 3.42 | 2.47 | 3 |
| Robust_075_105_width7 | XAUUSD | 17 | 52.94 | 11.67 | 0.69 | 2.96 | 1.58 | 3 |
| Strict_075_100_width7 | AUDJPY | 17 | 52.94 | 7.35 | 0.43 | 1.91 | 4.04 | 4 |
| Strict_075_100_width7 | CHFJPY | 11 | 45.45 | 3.86 | 0.35 | 1.64 | 2.03 | 2 |
| Strict_075_100_width7 | EURJPY | 13 | 53.85 | 5.77 | 0.44 | 2.12 | 3.02 | 3 |
| Strict_075_100_width7 | GBPJPY | 21 | 66.67 | 15.97 | 0.76 | 3.26 | 2.02 | 2 |
| Strict_075_100_width7 | SILVER | 13 | 38.46 | 1.78 | 0.14 | 1.26 | 3.16 | 4 |
| Strict_075_100_width7 | USDJPY | 14 | 64.29 | 14.55 | 1.04 | 6.54 | 1.46 | 2 |
| Strict_075_100_width7 | XAUUSD | 13 | 53.85 | 9.97 | 0.77 | 3.53 | 2.02 | 2 |

## トリガー別

| candidate | trigger_type | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current_060_110 | rebreak | 99 | 47.47 | 33.27 | 0.34 | 1.70 | 8.87 | 10 |
| Current_060_110 | stagnation | 36 | 50.00 | 8.72 | 0.24 | 1.52 | 4.17 | 4 |
| Current_060_110 | stagnation+rebreak | 22 | 59.09 | 15.19 | 0.69 | 2.69 | 2.92 | 3 |
| Robust_075_105_width7 | rebreak | 81 | 49.38 | 35.99 | 0.44 | 1.99 | 6.69 | 8 |
| Robust_075_105_width7 | stagnation | 28 | 53.57 | 11.43 | 0.41 | 1.98 | 2.10 | 3 |
| Robust_075_105_width7 | stagnation+rebreak | 20 | 65.00 | 17.10 | 0.85 | 3.41 | 2.02 | 2 |
| Strict_075_100_width7 | rebreak | 57 | 49.12 | 27.71 | 0.49 | 2.15 | 4.68 | 7 |
| Strict_075_100_width7 | stagnation | 27 | 55.56 | 12.44 | 0.46 | 2.16 | 2.10 | 3 |
| Strict_075_100_width7 | stagnation+rebreak | 18 | 72.22 | 19.11 | 1.06 | 4.78 | 1.03 | 1 |

## 出力

- `summary.csv`
- `stress_tests.csv`
- `two_year_windows.csv`
- `duplicate_and_overlap_checks.csv`
- `by_symbol.csv`
- `by_trigger.csv`
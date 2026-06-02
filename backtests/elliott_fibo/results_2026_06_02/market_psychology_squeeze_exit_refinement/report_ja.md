# Market Psychology Squeeze Exit Refinement

作成日: 2026-06-02

## 目的

`SQZ_STRICT_RR2` の入口を変えず、負けを早く切る出口だけで改善するかを確認した。

## 全通貨サマリー

| strategy | label | trades | win_rate | total_r | avg_r | median_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RR25 | BASE_RR25 | 51 | 43.14 | 19.88 | 0.39 | -1.01 | 1.67 | 6.14 | 7 | 1.49 | 0.93 | 10 | 10.14 |
| BASE_RR2 | BASE_RR2 | 51 | 47.06 | 18.06 | 0.35 | -1.01 | 1.65 | 4.11 | 4 | 1.27 | 0.88 | 10 | 7.87 |
| BASE_RR15 | BASE_RR15 | 51 | 50.98 | 12.55 | 0.25 | 1.34 | 1.49 | 3.64 | 4 | 1.06 | 0.83 | 10 | 4.87 |
| RETURN_INSIDE_2_RR2 | RETURN_INSIDE_2_RR2 | 51 | 33.33 | 9.45 | 0.19 | -0.29 | 1.42 | 4.87 | 8 | 0.95 | 0.67 | 10 | 4.24 |
| NO_PROGRESS_8_05R_RR2 | NO_PROGRESS_8_05R_RR2 | 51 | 47.06 | 9.35 | 0.18 | -0.15 | 1.39 | 4.11 | 4 | 1.02 | 0.82 | 10 | 2.70 |
| RETURN_INSIDE_3_RR2 | RETURN_INSIDE_3_RR2 | 51 | 29.41 | 6.93 | 0.14 | -0.33 | 1.33 | 4.39 | 8 | 0.86 | 0.61 | 10 | 4.24 |
| RETURN3_PLUS_NOPROG6_RR2 | RETURN3_PLUS_NOPROG6_RR2 | 51 | 31.37 | 6.50 | 0.13 | -0.29 | 1.36 | 4.39 | 8 | 0.78 | 0.56 | 10 | 2.53 |
| NO_PROGRESS_6_05R_RR2 | NO_PROGRESS_6_05R_RR2 | 51 | 41.18 | 6.07 | 0.12 | -0.14 | 1.28 | 4.99 | 7 | 0.86 | 0.76 | 10 | 2.26 |

## GBPJPY除外サマリー

| strategy | label | trades | win_rate | total_r | avg_r | median_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RR25 | BASE_RR25 | 43 | 48.84 | 26.54 | 0.62 | -1.00 | 2.18 | 5.12 | 6 | 1.63 | 0.85 | 9 | 11.16 |
| BASE_RR2 | BASE_RR2 | 43 | 53.49 | 24.72 | 0.57 | 1.88 | 2.21 | 3.09 | 3 | 1.38 | 0.80 | 9 | 8.89 |
| BASE_RR15 | BASE_RR15 | 43 | 55.81 | 15.72 | 0.37 | 1.38 | 1.81 | 2.62 | 3 | 1.13 | 0.76 | 9 | 5.89 |
| NO_PROGRESS_8_05R_RR2 | NO_PROGRESS_8_05R_RR2 | 43 | 53.49 | 15.52 | 0.36 | 0.20 | 1.88 | 3.09 | 3 | 1.08 | 0.73 | 9 | 3.72 |
| RETURN_INSIDE_2_RR2 | RETURN_INSIDE_2_RR2 | 43 | 37.21 | 15.02 | 0.35 | -0.28 | 1.92 | 4.55 | 7 | 0.99 | 0.61 | 9 | 5.26 |
| RETURN_INSIDE_3_RR2 | RETURN_INSIDE_3_RR2 | 43 | 32.56 | 12.04 | 0.28 | -0.29 | 1.79 | 4.07 | 7 | 0.89 | 0.55 | 9 | 5.26 |
| NO_PROGRESS_6_05R_RR2 | NO_PROGRESS_6_05R_RR2 | 43 | 46.51 | 11.83 | 0.28 | -0.03 | 1.76 | 3.89 | 6 | 0.89 | 0.66 | 9 | 3.28 |
| RETURN3_PLUS_NOPROG6_RR2 | RETURN3_PLUS_NOPROG6_RR2 | 43 | 34.88 | 10.71 | 0.25 | -0.28 | 1.81 | 4.07 | 7 | 0.80 | 0.50 | 9 | 3.55 |

## GBPJPY除外 期間別

| strategy | period | label | trades | win_rate | total_r | avg_r | median_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RR25 | OOS_2024_2026 | BASE_RR25_OOS_2024_2026 | 9 | 66.67 | 11.16 | 1.24 | 2.48 | 4.68 | 1.02 | 1 | 2.00 | 0.67 | 9 | 11.16 |
| BASE_RR2 | DEV_2015_2021 | BASE_RR2_DEV_2015_2021 | 27 | 48.15 | 11.03 | 0.41 | -1.01 | 1.77 | 3.09 | 3 | 1.36 | 0.87 | 0 | 0.00 |
| NO_PROGRESS_8_05R_RR2 | DEV_2015_2021 | NO_PROGRESS_8_05R_RR2_DEV_2015_2021 | 27 | 48.15 | 10.46 | 0.39 | -0.01 | 1.91 | 3.09 | 3 | 1.19 | 0.77 | 0 | 0.00 |
| BASE_RR2 | OOS_2024_2026 | BASE_RR2_OOS_2024_2026 | 9 | 66.67 | 8.89 | 0.99 | 1.99 | 3.93 | 1.02 | 1 | 1.57 | 0.66 | 9 | 8.89 |
| BASE_RR25 | DEV_2015_2021 | BASE_RR25_DEV_2015_2021 | 27 | 40.74 | 8.59 | 0.32 | -1.01 | 1.52 | 5.12 | 6 | 1.52 | 0.96 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | DEV_2015_2021 | NO_PROGRESS_6_05R_RR2_DEV_2015_2021 | 27 | 48.15 | 7.50 | 0.28 | -0.02 | 1.79 | 3.89 | 6 | 0.92 | 0.68 | 0 | 0.00 |
| RETURN_INSIDE_2_RR2 | DEV_2015_2021 | RETURN_INSIDE_2_RR2_DEV_2015_2021 | 27 | 37.04 | 7.07 | 0.26 | -0.29 | 1.57 | 4.55 | 7 | 1.05 | 0.71 | 0 | 0.00 |
| BASE_RR15 | DEV_2015_2021 | BASE_RR15_DEV_2015_2021 | 27 | 51.85 | 7.03 | 0.26 | 1.34 | 1.53 | 2.62 | 3 | 1.10 | 0.81 | 0 | 0.00 |
| BASE_RR25 | VALID_2022_2023 | BASE_RR25_VALID_2022_2023 | 7 | 57.14 | 6.79 | 0.97 | 2.42 | 3.25 | 2.01 | 2 | 1.58 | 0.71 | 0 | 0.00 |
| RETURN3_PLUS_NOPROG6_RR2 | DEV_2015_2021 | RETURN3_PLUS_NOPROG6_RR2_DEV_2015_2021 | 27 | 37.04 | 6.74 | 0.25 | -0.28 | 1.74 | 4.07 | 7 | 0.87 | 0.55 | 0 | 0.00 |
| RETURN_INSIDE_3_RR2 | DEV_2015_2021 | RETURN_INSIDE_3_RR2_DEV_2015_2021 | 27 | 33.33 | 6.36 | 0.24 | -0.33 | 1.57 | 4.07 | 7 | 0.95 | 0.63 | 0 | 0.00 |
| BASE_RR15 | OOS_2024_2026 | BASE_RR15_OOS_2024_2026 | 9 | 66.67 | 5.89 | 0.65 | 1.49 | 2.94 | 1.02 | 1 | 1.33 | 0.66 | 9 | 5.89 |
| RETURN_INSIDE_2_RR2 | OOS_2024_2026 | RETURN_INSIDE_2_RR2_OOS_2024_2026 | 9 | 44.44 | 5.26 | 0.58 | -0.22 | 2.95 | 1.46 | 3 | 1.10 | 0.53 | 9 | 5.26 |
| RETURN_INSIDE_3_RR2 | OOS_2024_2026 | RETURN_INSIDE_3_RR2_OOS_2024_2026 | 9 | 44.44 | 5.26 | 0.58 | -0.22 | 2.95 | 1.46 | 3 | 1.10 | 0.53 | 9 | 5.26 |
| BASE_RR2 | VALID_2022_2023 | BASE_RR2_VALID_2022_2023 | 7 | 57.14 | 4.79 | 0.68 | 1.92 | 2.59 | 2.01 | 2 | 1.18 | 0.71 | 0 | 0.00 |
| NO_PROGRESS_8_05R_RR2 | OOS_2024_2026 | NO_PROGRESS_8_05R_RR2_OOS_2024_2026 | 9 | 66.67 | 3.72 | 0.41 | 0.22 | 2.23 | 1.64 | 1 | 1.01 | 0.65 | 9 | 3.72 |
| RETURN3_PLUS_NOPROG6_RR2 | OOS_2024_2026 | RETURN3_PLUS_NOPROG6_RR2_OOS_2024_2026 | 9 | 44.44 | 3.55 | 0.39 | -0.22 | 2.32 | 1.46 | 3 | 0.91 | 0.53 | 9 | 3.55 |
| NO_PROGRESS_6_05R_RR2 | OOS_2024_2026 | NO_PROGRESS_6_05R_RR2_OOS_2024_2026 | 9 | 55.56 | 3.28 | 0.36 | 0.25 | 2.02 | 2.19 | 3 | 0.96 | 0.65 | 9 | 3.28 |
| BASE_RR15 | VALID_2022_2023 | BASE_RR15_VALID_2022_2023 | 7 | 57.14 | 2.79 | 0.40 | 1.42 | 1.92 | 2.01 | 2 | 0.99 | 0.71 | 0 | 0.00 |
| RETURN_INSIDE_2_RR2 | VALID_2022_2023 | RETURN_INSIDE_2_RR2_VALID_2022_2023 | 7 | 28.57 | 2.69 | 0.38 | -0.18 | 3.33 | 0.90 | 3 | 0.63 | 0.30 | 0 | 0.00 |
| NO_PROGRESS_8_05R_RR2 | VALID_2022_2023 | NO_PROGRESS_8_05R_RR2_VALID_2022_2023 | 7 | 57.14 | 1.35 | 0.19 | 0.20 | 1.45 | 2.01 | 2 | 0.71 | 0.71 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | VALID_2022_2023 | NO_PROGRESS_6_05R_RR2_VALID_2022_2023 | 7 | 28.57 | 1.05 | 0.15 | -0.22 | 1.37 | 1.60 | 3 | 0.70 | 0.63 | 0 | 0.00 |
| RETURN3_PLUS_NOPROG6_RR2 | VALID_2022_2023 | RETURN3_PLUS_NOPROG6_RR2_VALID_2022_2023 | 7 | 14.29 | 0.42 | 0.06 | -0.28 | 1.28 | 0.90 | 3 | 0.36 | 0.29 | 0 | 0.00 |
| RETURN_INSIDE_3_RR2 | VALID_2022_2023 | RETURN_INSIDE_3_RR2_VALID_2022_2023 | 7 | 14.29 | 0.42 | 0.06 | -0.28 | 1.28 | 0.90 | 3 | 0.36 | 0.29 | 0 | 0.00 |

## 通貨別

| strategy | symbol | label | trades | win_rate | total_r | avg_r | median_r | pf | max_dd_r | max_losing_streak | avg_mfe_r | avg_mae_r | oos_trades | oos_total_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RR2 | XAUUSD | BASE_RR2_XAUUSD | 10 | 70.00 | 10.73 | 1.07 | 1.97 | 4.45 | 2.07 | 2 | 1.56 | 0.64 | 3 | 5.95 |
| BASE_RR25 | XAUUSD | BASE_RR25_XAUUSD | 10 | 60.00 | 10.73 | 1.07 | 2.47 | 3.59 | 3.11 | 4 | 1.90 | 0.75 | 3 | 7.45 |
| BASE_RR25 | SILVER | BASE_RR25_SILVER | 7 | 71.43 | 9.83 | 1.40 | 2.38 | 5.66 | 1.03 | 1 | 2.03 | 0.67 | 0 | 0.00 |
| BASE_RR2 | SILVER | BASE_RR2_SILVER | 7 | 71.43 | 7.33 | 1.05 | 1.88 | 4.47 | 1.03 | 1 | 1.66 | 0.67 | 0 | 0.00 |
| RETURN_INSIDE_2_RR2 | SILVER | RETURN_INSIDE_2_RR2_SILVER | 7 | 71.43 | 7.33 | 1.05 | 1.88 | 4.47 | 1.03 | 1 | 1.66 | 0.67 | 0 | 0.00 |
| BASE_RR15 | XAUUSD | BASE_RR15_XAUUSD | 10 | 70.00 | 7.23 | 0.72 | 1.47 | 3.33 | 2.07 | 2 | 1.24 | 0.64 | 3 | 4.45 |
| NO_PROGRESS_8_05R_RR2 | XAUUSD | NO_PROGRESS_8_05R_RR2_XAUUSD | 10 | 70.00 | 7.22 | 0.72 | 1.11 | 3.32 | 2.07 | 2 | 1.21 | 0.64 | 3 | 4.16 |
| NO_PROGRESS_8_05R_RR2 | SILVER | NO_PROGRESS_8_05R_RR2_SILVER | 7 | 71.43 | 7.01 | 1.00 | 1.84 | 10.85 | 0.01 | 1 | 1.39 | 0.47 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | SILVER | NO_PROGRESS_6_05R_RR2_SILVER | 7 | 57.14 | 6.89 | 0.98 | 1.84 | 11.86 | 0.05 | 2 | 1.39 | 0.46 | 0 | 0.00 |
| RETURN3_PLUS_NOPROG6_RR2 | SILVER | RETURN3_PLUS_NOPROG6_RR2_SILVER | 7 | 57.14 | 6.57 | 0.94 | 1.84 | 7.88 | 0.36 | 2 | 1.36 | 0.43 | 0 | 0.00 |
| RETURN3_PLUS_NOPROG6_RR2 | XAUUSD | RETURN3_PLUS_NOPROG6_RR2_XAUUSD | 10 | 40.00 | 6.38 | 0.64 | -0.14 | 5.15 | 0.88 | 3 | 0.94 | 0.32 | 3 | 3.75 |
| RETURN_INSIDE_3_RR2 | XAUUSD | RETURN_INSIDE_3_RR2_XAUUSD | 10 | 40.00 | 6.38 | 0.64 | -0.14 | 5.15 | 0.88 | 3 | 0.94 | 0.32 | 3 | 3.75 |
| RETURN_INSIDE_2_RR2 | XAUUSD | RETURN_INSIDE_2_RR2_XAUUSD | 10 | 40.00 | 5.69 | 0.57 | -0.14 | 3.55 | 1.58 | 3 | 0.94 | 0.44 | 3 | 3.75 |
| RETURN_INSIDE_3_RR2 | SILVER | RETURN_INSIDE_3_RR2_SILVER | 7 | 57.14 | 5.55 | 0.79 | 1.84 | 3.82 | 1.38 | 2 | 1.39 | 0.59 | 0 | 0.00 |
| BASE_RR2 | USDJPY | BASE_RR2_USDJPY | 13 | 46.15 | 4.87 | 0.37 | -1.00 | 1.69 | 2.02 | 2 | 1.16 | 0.89 | 4 | 1.98 |
| BASE_RR15 | SILVER | BASE_RR15_SILVER | 7 | 71.43 | 4.83 | 0.69 | 1.38 | 3.29 | 1.03 | 1 | 1.27 | 0.60 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | XAUUSD | NO_PROGRESS_6_05R_RR2_XAUUSD | 10 | 50.00 | 4.80 | 0.48 | 0.11 | 2.43 | 2.10 | 3 | 1.00 | 0.64 | 3 | 4.21 |
| BASE_RR25 | USDJPY | BASE_RR25_USDJPY | 13 | 38.46 | 3.63 | 0.28 | -1.01 | 1.45 | 2.02 | 3 | 1.34 | 0.97 | 4 | 2.24 |
| BASE_RR2 | AUDJPY | BASE_RR2_AUDJPY | 6 | 50.00 | 2.90 | 0.48 | 0.49 | 1.95 | 2.04 | 2 | 1.32 | 0.83 | 1 | 1.99 |
| RETURN_INSIDE_2_RR2 | USDJPY | RETURN_INSIDE_2_RR2_USDJPY | 13 | 30.77 | 2.84 | 0.22 | -0.29 | 1.56 | 3.33 | 5 | 0.84 | 0.62 | 4 | 2.97 |
| RETURN_INSIDE_3_RR2 | USDJPY | RETURN_INSIDE_3_RR2_USDJPY | 13 | 30.77 | 2.84 | 0.22 | -0.29 | 1.56 | 3.33 | 5 | 0.84 | 0.62 | 4 | 2.97 |
| BASE_RR25 | CHFJPY | BASE_RR25_CHFJPY | 1 | 100.00 | 2.47 | 2.47 | 2.47 | inf | 0.00 | 0 | 2.53 | 0.56 | 0 | 0.00 |
| BASE_RR25 | AUDJPY | BASE_RR25_AUDJPY | 6 | 50.00 | 2.46 | 0.41 | -0.23 | 1.81 | 2.04 | 2 | 1.59 | 0.88 | 1 | 2.49 |
| NO_PROGRESS_8_05R_RR2 | AUDJPY | NO_PROGRESS_8_05R_RR2_AUDJPY | 6 | 50.00 | 2.17 | 0.36 | 0.12 | 1.99 | 2.04 | 2 | 1.03 | 0.72 | 1 | 0.38 |
| BASE_RR2 | CHFJPY | BASE_RR2_CHFJPY | 1 | 100.00 | 1.97 | 1.97 | 1.97 | inf | 0.00 | 0 | 2.20 | 0.56 | 0 | 0.00 |
| RETURN_INSIDE_2_RR2 | CHFJPY | RETURN_INSIDE_2_RR2_CHFJPY | 1 | 100.00 | 1.97 | 1.97 | 1.97 | inf | 0.00 | 0 | 2.20 | 0.56 | 0 | 0.00 |
| BASE_RR15 | USDJPY | BASE_RR15_USDJPY | 13 | 46.15 | 1.87 | 0.14 | -1.00 | 1.26 | 2.02 | 2 | 0.97 | 0.89 | 4 | 0.98 |
| NO_PROGRESS_6_05R_RR2 | AUDJPY | NO_PROGRESS_6_05R_RR2_AUDJPY | 6 | 66.67 | 1.53 | 0.26 | 0.17 | 2.28 | 1.02 | 1 | 0.66 | 0.55 | 1 | -0.17 |
| BASE_RR15 | CHFJPY | BASE_RR15_CHFJPY | 1 | 100.00 | 1.47 | 1.47 | 1.47 | inf | 0.00 | 0 | 1.92 | 0.56 | 0 | 0.00 |
| BASE_RR15 | AUDJPY | BASE_RR15_AUDJPY | 6 | 50.00 | 1.40 | 0.23 | 0.24 | 1.46 | 2.04 | 2 | 1.11 | 0.83 | 1 | 1.49 |
| RETURN3_PLUS_NOPROG6_RR2 | USDJPY | RETURN3_PLUS_NOPROG6_RR2_USDJPY | 13 | 30.77 | 1.13 | 0.09 | -0.29 | 1.22 | 3.33 | 5 | 0.71 | 0.62 | 4 | 1.26 |
| NO_PROGRESS_8_05R_RR2 | USDJPY | NO_PROGRESS_8_05R_RR2_USDJPY | 13 | 38.46 | 0.63 | 0.05 | -1.00 | 1.08 | 3.52 | 4 | 0.88 | 0.86 | 4 | 0.20 |
| NO_PROGRESS_8_05R_RR2 | CHFJPY | NO_PROGRESS_8_05R_RR2_CHFJPY | 1 | 100.00 | 0.33 | 0.33 | 0.33 | inf | 0.00 | 0 | 0.45 | 0.56 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | EURJPY | NO_PROGRESS_6_05R_RR2_EURJPY | 6 | 50.00 | -0.35 | -0.06 | -0.34 | 0.89 | 2.03 | 2 | 0.80 | 0.77 | 1 | -1.02 |
| NO_PROGRESS_6_05R_RR2 | CHFJPY | NO_PROGRESS_6_05R_RR2_CHFJPY | 1 | 0.00 | -0.36 | -0.36 | -0.36 | 0.00 | 0.00 | 1 | 0.45 | 0.53 | 0 | 0.00 |
| RETURN3_PLUS_NOPROG6_RR2 | CHFJPY | RETURN3_PLUS_NOPROG6_RR2_CHFJPY | 1 | 0.00 | -0.44 | -0.44 | -0.44 | 0.00 | 0.00 | 1 | 0.45 | 0.46 | 0 | 0.00 |
| RETURN_INSIDE_3_RR2 | CHFJPY | RETURN_INSIDE_3_RR2_CHFJPY | 1 | 0.00 | -0.44 | -0.44 | -0.44 | 0.00 | 0.00 | 1 | 0.45 | 0.46 | 0 | 0.00 |
| NO_PROGRESS_6_05R_RR2 | USDJPY | NO_PROGRESS_6_05R_RR2_USDJPY | 13 | 30.77 | -0.68 | -0.05 | -0.59 | 0.90 | 3.26 | 5 | 0.72 | 0.81 | 4 | 0.27 |
| BASE_RR15 | EURJPY | BASE_RR15_EURJPY | 6 | 33.33 | -1.09 | -0.18 | -1.01 | 0.73 | 2.03 | 2 | 1.01 | 0.84 | 1 | -1.02 |
| RETURN_INSIDE_2_RR2 | AUDJPY | RETURN_INSIDE_2_RR2_AUDJPY | 6 | 16.67 | -1.12 | -0.19 | -0.39 | 0.64 | 2.76 | 4 | 0.60 | 0.70 | 1 | -0.44 |
| RETURN_INSIDE_3_RR2 | AUDJPY | RETURN_INSIDE_3_RR2_AUDJPY | 6 | 16.67 | -1.12 | -0.19 | -0.39 | 0.64 | 2.76 | 4 | 0.60 | 0.70 | 1 | -0.44 |
| RETURN3_PLUS_NOPROG6_RR2 | EURJPY | RETURN3_PLUS_NOPROG6_RR2_EURJPY | 6 | 16.67 | -1.17 | -0.19 | -0.47 | 0.63 | 1.64 | 3 | 0.68 | 0.62 | 1 | -1.02 |
| RETURN_INSIDE_3_RR2 | EURJPY | RETURN_INSIDE_3_RR2_EURJPY | 6 | 16.67 | -1.17 | -0.19 | -0.47 | 0.63 | 1.64 | 3 | 0.68 | 0.62 | 1 | -1.02 |
| RETURN_INSIDE_2_RR2 | EURJPY | RETURN_INSIDE_2_RR2_EURJPY | 6 | 16.67 | -1.68 | -0.28 | -0.72 | 0.54 | 1.64 | 3 | 0.83 | 0.69 | 1 | -1.02 |
| RETURN3_PLUS_NOPROG6_RR2 | AUDJPY | RETURN3_PLUS_NOPROG6_RR2_AUDJPY | 6 | 33.33 | -1.75 | -0.29 | -0.32 | 0.16 | 1.75 | 3 | 0.27 | 0.53 | 1 | -0.44 |
| NO_PROGRESS_8_05R_RR2 | EURJPY | NO_PROGRESS_8_05R_RR2_EURJPY | 6 | 33.33 | -1.83 | -0.31 | -1.01 | 0.55 | 3.05 | 3 | 1.05 | 0.96 | 1 | -1.02 |
| BASE_RR25 | EURJPY | BASE_RR25_EURJPY | 6 | 16.67 | -2.59 | -0.43 | -1.01 | 0.49 | 3.05 | 3 | 1.25 | 1.03 | 1 | -1.02 |
| BASE_RR2 | EURJPY | BASE_RR2_EURJPY | 6 | 16.67 | -3.09 | -0.51 | -1.01 | 0.39 | 3.05 | 3 | 1.14 | 1.03 | 1 | -1.02 |
| BASE_RR15 | GBPJPY | BASE_RR15_GBPJPY | 8 | 25.00 | -3.17 | -0.40 | -1.02 | 0.48 | 3.07 | 4 | 0.69 | 1.17 | 1 | -1.02 |
| RETURN3_PLUS_NOPROG6_RR2 | GBPJPY | RETURN3_PLUS_NOPROG6_RR2_GBPJPY | 8 | 12.50 | -4.21 | -0.53 | -0.60 | 0.11 | 3.90 | 4 | 0.70 | 0.88 | 1 | -1.02 |
| RETURN_INSIDE_3_RR2 | GBPJPY | RETURN_INSIDE_3_RR2_GBPJPY | 8 | 12.50 | -5.11 | -0.64 | -0.83 | 0.09 | 4.79 | 4 | 0.71 | 0.93 | 1 | -1.02 |
| RETURN_INSIDE_2_RR2 | GBPJPY | RETURN_INSIDE_2_RR2_GBPJPY | 8 | 12.50 | -5.57 | -0.70 | -1.02 | 0.08 | 5.25 | 4 | 0.71 | 1.01 | 1 | -1.02 |
| NO_PROGRESS_6_05R_RR2 | GBPJPY | NO_PROGRESS_6_05R_RR2_GBPJPY | 8 | 12.50 | -5.77 | -0.72 | -1.02 | 0.08 | 4.74 | 4 | 0.70 | 1.26 | 1 | -1.02 |
| NO_PROGRESS_8_05R_RR2 | GBPJPY | NO_PROGRESS_8_05R_RR2_GBPJPY | 8 | 12.50 | -6.17 | -0.77 | -1.02 | 0.07 | 5.15 | 4 | 0.70 | 1.30 | 1 | -1.02 |
| BASE_RR2 | GBPJPY | BASE_RR2_GBPJPY | 8 | 12.50 | -6.66 | -0.83 | -1.02 | 0.07 | 5.64 | 4 | 0.71 | 1.31 | 1 | -1.02 |
| BASE_RR25 | GBPJPY | BASE_RR25_GBPJPY | 8 | 12.50 | -6.66 | -0.83 | -1.02 | 0.07 | 5.64 | 4 | 0.71 | 1.31 | 1 | -1.02 |

## 暫定判断

- 入口の本質は変えない。急落後の棚上抜けだけを見る。
- `return_inside_shelf` は、踏み上げ失敗を早く認めるための自然な撤退候補。
- `no_progress` はやや裁量的なので、PFだけ良くても過剰最適化疑いとして扱う。

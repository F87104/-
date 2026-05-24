# T5 + MACD + BB V字速度定義 比較検証

## 比較した定義

- `REC15`: 回復本数 / 下落本数 <= 1.5。過去の探索に近い定義。
- `REC10`: 回復本数 / 下落本数 <= 1.0。左肩と同じ本数以内で戻す、より厳格なV字定義。

## サマリー

| spec | candidate | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 142 | 50.70 | 53.87 | 0.38 | 1.81 | 9.76 | 9 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 117 | 53.85 | 59.75 | 0.51 | 2.18 | 6.64 | 7 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 92 | 57.61 | 58.47 | 0.64 | 2.65 | 5.62 | 6 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 157 | 49.68 | 57.17 | 0.36 | 1.78 | 11.89 | 13 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 129 | 52.71 | 64.52 | 0.50 | 2.17 | 8.78 | 10 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 102 | 54.90 | 59.26 | 0.58 | 2.49 | 5.74 | 7 |

## 通貨別

| spec | candidate | symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | AUDJPY | 21 | 57.14 | 8.70 | 0.41 | 1.96 | 6.07 | 6 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | CHFJPY | 12 | 66.67 | 9.59 | 0.80 | 3.38 | 2.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | EURJPY | 22 | 36.36 | -1.23 | -0.06 | 0.91 | 7.04 | 8 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | GBPJPY | 29 | 55.17 | 12.85 | 0.44 | 1.98 | 3.02 | 3 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | SILVER | 21 | 33.33 | -2.13 | -0.10 | 0.84 | 5.25 | 5 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | USDJPY | 24 | 54.17 | 15.25 | 0.64 | 2.60 | 2.47 | 3 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | XAUUSD | 13 | 61.54 | 10.84 | 0.83 | 3.98 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | AUDJPY | 20 | 55.00 | 7.57 | 0.38 | 1.83 | 6.07 | 6 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | CHFJPY | 9 | 77.78 | 10.93 | 1.21 | 6.42 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | EURJPY | 15 | 33.33 | -1.42 | -0.09 | 0.86 | 5.03 | 6 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | GBPJPY | 25 | 60.00 | 14.94 | 0.60 | 2.48 | 3.02 | 3 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | SILVER | 16 | 37.50 | 1.54 | 0.10 | 1.17 | 3.73 | 5 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | USDJPY | 21 | 57.14 | 15.16 | 0.72 | 2.98 | 2.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | XAUUSD | 11 | 63.64 | 11.02 | 1.00 | 5.19 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | AUDJPY | 15 | 60.00 | 8.43 | 0.56 | 2.39 | 5.05 | 5 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | CHFJPY | 8 | 75.00 | 9.89 | 1.24 | 5.90 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | EURJPY | 10 | 40.00 | 0.54 | 0.05 | 1.09 | 3.02 | 4 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | GBPJPY | 23 | 65.22 | 16.95 | 0.74 | 3.10 | 2.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | SILVER | 12 | 33.33 | -0.19 | -0.02 | 0.97 | 3.16 | 4 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | USDJPY | 15 | 60.00 | 12.55 | 0.84 | 3.72 | 2.01 | 3 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | XAUUSD | 9 | 66.67 | 10.30 | 1.14 | 7.34 | 1.01 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | AUDJPY | 21 | 52.38 | 7.50 | 0.36 | 1.74 | 5.06 | 5 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | CHFJPY | 17 | 47.06 | 4.55 | 0.27 | 1.50 | 3.02 | 3 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | EURJPY | 25 | 44.00 | 3.99 | 0.16 | 1.30 | 7.04 | 7 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | GBPJPY | 26 | 57.69 | 12.88 | 0.50 | 2.16 | 4.03 | 4 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | SILVER | 23 | 39.13 | 0.79 | 0.03 | 1.06 | 4.52 | 5 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | USDJPY | 24 | 54.17 | 16.24 | 0.68 | 2.89 | 3.48 | 4 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | XAUUSD | 21 | 52.38 | 11.22 | 0.53 | 2.41 | 2.02 | 3 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | AUDJPY | 21 | 52.38 | 7.50 | 0.36 | 1.74 | 5.06 | 5 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | CHFJPY | 14 | 50.00 | 5.89 | 0.42 | 1.83 | 2.03 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | EURJPY | 18 | 44.44 | 3.81 | 0.21 | 1.41 | 5.03 | 5 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | GBPJPY | 21 | 66.67 | 15.97 | 0.76 | 3.26 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | SILVER | 17 | 41.18 | 3.52 | 0.21 | 1.39 | 3.16 | 4 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | USDJPY | 21 | 57.14 | 16.15 | 0.77 | 3.42 | 2.47 | 3 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | XAUUSD | 17 | 52.94 | 11.67 | 0.69 | 2.96 | 1.58 | 3 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | AUDJPY | 17 | 52.94 | 7.35 | 0.43 | 1.91 | 4.04 | 4 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | CHFJPY | 11 | 45.45 | 3.86 | 0.35 | 1.64 | 2.03 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | EURJPY | 13 | 53.85 | 5.77 | 0.44 | 2.12 | 3.02 | 3 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | GBPJPY | 21 | 66.67 | 15.97 | 0.76 | 3.26 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | SILVER | 13 | 38.46 | 1.78 | 0.14 | 1.26 | 3.16 | 4 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | USDJPY | 14 | 64.29 | 14.55 | 1.04 | 6.54 | 1.46 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | XAUUSD | 13 | 53.85 | 9.97 | 0.77 | 3.53 | 2.02 | 2 |

## トリガー別

| spec | candidate | trigger_type | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | rebreak | 90 | 45.56 | 25.63 | 0.28 | 1.56 | 6.37 | 6 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | stagnation | 33 | 57.58 | 13.01 | 0.39 | 1.95 | 4.21 | 5 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | stagnation+rebreak | 19 | 63.16 | 15.22 | 0.80 | 3.18 | 2.03 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | rebreak | 76 | 47.37 | 28.03 | 0.37 | 1.76 | 5.16 | 5 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation | 24 | 62.50 | 14.59 | 0.61 | 2.71 | 3.11 | 4 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation+rebreak | 17 | 70.59 | 17.13 | 1.01 | 4.39 | 1.03 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | rebreak | 53 | 49.06 | 24.74 | 0.47 | 2.04 | 4.15 | 4 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation | 23 | 65.22 | 15.60 | 0.68 | 3.07 | 3.11 | 4 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation+rebreak | 16 | 75.00 | 18.13 | 1.13 | 5.47 | 1.03 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | rebreak | 99 | 47.47 | 33.27 | 0.34 | 1.70 | 8.87 | 10 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | stagnation | 36 | 50.00 | 8.72 | 0.24 | 1.52 | 4.17 | 4 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | stagnation+rebreak | 22 | 59.09 | 15.19 | 0.69 | 2.69 | 2.92 | 3 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | rebreak | 81 | 49.38 | 35.99 | 0.44 | 1.99 | 6.69 | 8 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation | 28 | 53.57 | 11.43 | 0.41 | 1.98 | 2.10 | 3 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation+rebreak | 20 | 65.00 | 17.10 | 0.85 | 3.41 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | rebreak | 57 | 49.12 | 27.71 | 0.49 | 2.15 | 4.68 | 7 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation | 27 | 55.56 | 12.44 | 0.46 | 2.16 | 2.10 | 3 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation+rebreak | 18 | 72.22 | 19.11 | 1.06 | 4.78 | 1.03 | 1 |
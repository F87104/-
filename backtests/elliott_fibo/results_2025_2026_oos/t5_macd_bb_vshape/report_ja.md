# T5 + MACD + BB 2025-2026 OOS V字速度定義 比較

- OOS期間: 2025-01-01〜2026-12-31
- `REC15`: 回復本数 / 下落本数 <= 1.5
- `REC10`: 回復本数 / 下落本数 <= 1.0
- インジケータ閾値は2015-2024研究から固定。ここでは再最適化しない。

## データカバレッジ

| symbol | rows_h1 | first | last | has_2025_plus |
| --- | --- | --- | --- | --- |
| XAUUSD | 70410 | 2013-12-31 21:00:00 | 2026-05-22 20:00:00 | True |
| USDJPY | 75960 | 2013-12-31 21:00:00 | 2026-05-22 20:00:00 | True |
| EURJPY | 75174 | 2013-12-31 19:00:00 | 2026-05-22 20:00:00 | True |
| GBPJPY | 81199 | 2013-01-01 00:00:00 | 2026-05-19 23:00:00 | True |
| CHFJPY | 76982 | 2014-01-01 22:00:00 | 2026-05-22 20:00:00 | True |
| AUDJPY | 73953 | 2013-12-31 21:00:00 | 2026-05-22 20:00:00 | True |
| SILVER | 70218 | 2013-12-31 21:00:00 | 2026-05-22 20:00:00 | True |

## サマリー

| spec | candidate | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 24 | 54.17 | 4.71 | 0.20 | 1.42 | 2.27 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 19 | 57.89 | 5.33 | 0.28 | 1.66 | 3.26 | 2 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 15 | 60.00 | 5.28 | 0.35 | 1.87 | 2.25 | 2 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 27 | 59.26 | 10.54 | 0.39 | 2.03 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 21 | 61.90 | 9.16 | 0.44 | 2.27 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 16 | 62.50 | 7.11 | 0.44 | 2.37 | 2.02 | 2 |

## 通貨別

| spec | candidate | symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | AUDJPY | 2 | 0.00 | -2.01 | -1.01 | 0.00 | 1.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | CHFJPY | 4 | 75.00 | 3.58 | 0.89 | 4.54 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | EURJPY | 5 | 40.00 | -0.63 | -0.13 | 0.79 | 1.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | GBPJPY | 4 | 25.00 | -2.47 | -0.62 | 0.18 | 2.02 | 3 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | SILVER | 5 | 80.00 | 3.23 | 0.65 | 4.15 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | USDJPY | 3 | 66.67 | 1.02 | 0.34 | 2.02 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | XAUUSD | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | AUDJPY | 2 | 0.00 | -2.01 | -1.01 | 0.00 | 1.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | CHFJPY | 4 | 75.00 | 3.58 | 0.89 | 4.54 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | EURJPY | 2 | 50.00 | 0.99 | 0.49 | 1.99 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | GBPJPY | 3 | 33.33 | -1.46 | -0.49 | 0.27 | 1.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | SILVER | 4 | 75.00 | 1.23 | 0.31 | 2.20 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | USDJPY | 3 | 66.67 | 1.02 | 0.34 | 2.02 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | XAUUSD | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | AUDJPY | 2 | 0.00 | -2.01 | -1.01 | 0.00 | 1.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | CHFJPY | 4 | 75.00 | 3.58 | 0.89 | 4.54 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | GBPJPY | 2 | 50.00 | -0.45 | -0.23 | 0.55 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | SILVER | 3 | 66.67 | 1.15 | 0.38 | 2.12 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | USDJPY | 3 | 66.67 | 1.02 | 0.34 | 2.02 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | XAUUSD | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | AUDJPY | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.01 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | CHFJPY | 3 | 100.00 | 4.59 | 1.53 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | EURJPY | 6 | 33.33 | -0.78 | -0.13 | 0.75 | 1.01 | 2 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | GBPJPY | 5 | 20.00 | -3.48 | -0.70 | 0.14 | 2.47 | 3 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | SILVER | 5 | 80.00 | 3.23 | 0.65 | 4.15 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | USDJPY | 3 | 100.00 | 3.01 | 1.00 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | XAUUSD | 2 | 100.00 | 3.99 | 1.99 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | AUDJPY | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.01 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | CHFJPY | 3 | 100.00 | 4.59 | 1.53 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | EURJPY | 3 | 33.33 | 0.84 | 0.28 | 1.73 | 0.15 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | GBPJPY | 4 | 25.00 | -2.47 | -0.62 | 0.18 | 1.47 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | SILVER | 4 | 75.00 | 1.23 | 0.31 | 2.20 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | USDJPY | 3 | 100.00 | 3.01 | 1.00 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | XAUUSD | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | AUDJPY | 2 | 0.00 | -2.01 | -1.01 | 0.00 | 1.01 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | CHFJPY | 3 | 100.00 | 4.59 | 1.53 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | EURJPY | 1 | 0.00 | -0.15 | -0.15 | 0.00 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | GBPJPY | 3 | 33.33 | -1.46 | -0.49 | 0.27 | 1.01 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | SILVER | 3 | 66.67 | 1.15 | 0.38 | 2.12 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | USDJPY | 3 | 100.00 | 3.01 | 1.00 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | XAUUSD | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |

## 月別

| spec | candidate | month | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-01 | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.00 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-04 | 1 | 100.00 | 0.08 | 0.08 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-05 | 2 | 50.00 | 0.39 | 0.19 | 1.39 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-07 | 1 | 100.00 | 0.39 | 0.39 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-08 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-10 | 2 | 50.00 | 0.99 | 0.49 | 1.98 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2025-11 | 2 | 50.00 | -0.30 | -0.15 | 0.70 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2026-01 | 2 | 50.00 | 0.99 | 0.49 | 1.98 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2026-02 | 2 | 50.00 | -0.45 | -0.23 | 0.55 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2026-03 | 2 | 50.00 | -0.79 | -0.39 | 0.21 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | 2026-04 | 1 | 0.00 | -1.01 | -1.01 | 0.00 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-01 | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.00 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-04 | 1 | 100.00 | 0.08 | 0.08 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-05 | 1 | 100.00 | 1.39 | 1.39 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-08 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-10 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-11 | 2 | 50.00 | -0.30 | -0.15 | 0.70 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-01 | 1 | 0.00 | -1.01 | -1.01 | 0.00 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-02 | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-03 | 2 | 50.00 | -0.79 | -0.39 | 0.21 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-04 | 1 | 0.00 | -1.01 | -1.01 | 0.00 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-01 | 2 | 50.00 | 0.98 | 0.49 | 1.98 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-05 | 1 | 100.00 | 1.39 | 1.39 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-08 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-11 | 2 | 50.00 | -0.30 | -0.15 | 0.70 | 1.01 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-02 | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 | 0 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-03 | 2 | 50.00 | -0.79 | -0.39 | 0.21 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-04 | 1 | 0.00 | -1.01 | -1.01 | 0.00 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-01 | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.00 | 2 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-04 | 2 | 100.00 | 2.08 | 1.04 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-05 | 2 | 50.00 | 0.39 | 0.19 | 1.39 | 1.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-07 | 1 | 100.00 | 0.39 | 0.39 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-08 | 2 | 50.00 | 1.84 | 0.92 | 13.35 | 0.15 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-10 | 2 | 50.00 | 0.99 | 0.49 | 1.98 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2025-11 | 1 | 100.00 | 0.71 | 0.71 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2026-01 | 3 | 66.67 | 2.98 | 0.99 | 3.95 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2026-02 | 2 | 50.00 | -0.45 | -0.23 | 0.55 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2026-03 | 2 | 100.00 | 1.20 | 0.60 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | 2026-04 | 2 | 0.00 | -2.02 | -1.01 | 0.00 | 1.01 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-01 | 3 | 33.33 | -0.02 | -0.01 | 0.99 | 1.00 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-04 | 1 | 100.00 | 0.08 | 0.08 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-05 | 1 | 100.00 | 1.39 | 1.39 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-08 | 2 | 50.00 | 1.84 | 0.92 | 13.35 | 0.15 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-10 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2025-11 | 1 | 100.00 | 0.71 | 0.71 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-01 | 2 | 50.00 | 0.98 | 0.49 | 1.97 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-02 | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-03 | 2 | 100.00 | 1.20 | 0.60 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | 2026-04 | 2 | 0.00 | -2.02 | -1.01 | 0.00 | 1.01 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-01 | 2 | 50.00 | 0.98 | 0.49 | 1.98 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-03 | 3 | 33.33 | -0.82 | -0.27 | 0.59 | 1.02 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-05 | 1 | 100.00 | 1.39 | 1.39 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-06 | 2 | 100.00 | 3.28 | 1.64 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-08 | 2 | 50.00 | 1.84 | 0.92 | 13.35 | 0.15 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2025-11 | 1 | 100.00 | 0.71 | 0.71 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-02 | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-03 | 2 | 100.00 | 1.20 | 0.60 | inf | 0.00 | 0 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | 2026-04 | 2 | 0.00 | -2.02 | -1.01 | 0.00 | 1.01 | 2 |

## トリガー別

| spec | candidate | trigger_type | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | rebreak | 16 | 62.50 | 7.08 | 0.44 | 2.17 | 2.02 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | stagnation | 6 | 50.00 | -0.34 | -0.06 | 0.89 | 2.01 | 2 |
| REC10_T5_STAG_OR_REBREAK | Current_060_110 | stagnation+rebreak | 2 | 0.00 | -2.03 | -1.01 | 0.00 | 1.00 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | rebreak | 13 | 61.54 | 5.69 | 0.44 | 2.13 | 2.26 | 2 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation | 5 | 60.00 | 0.67 | 0.13 | 1.33 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation+rebreak | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | rebreak | 10 | 70.00 | 5.71 | 0.57 | 2.89 | 1.25 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation | 4 | 50.00 | 0.59 | 0.15 | 1.29 | 1.00 | 1 |
| REC10_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation+rebreak | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | rebreak | 19 | 63.16 | 10.92 | 0.57 | 2.76 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | stagnation | 6 | 66.67 | 1.64 | 0.27 | 1.82 | 1.01 | 1 |
| REC15_T5_STAG_OR_REBREAK | Current_060_110 | stagnation+rebreak | 2 | 0.00 | -2.03 | -1.01 | 0.00 | 1.00 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | rebreak | 15 | 60.00 | 7.54 | 0.50 | 2.45 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation | 5 | 80.00 | 2.65 | 0.53 | 3.64 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Robust_075_105_width7 | stagnation+rebreak | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | rebreak | 11 | 63.64 | 5.56 | 0.51 | 2.75 | 2.02 | 2 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation | 4 | 75.00 | 2.57 | 0.64 | 3.56 | 0.00 | 1 |
| REC15_T5_STAG_OR_REBREAK | Strict_075_100_width7 | stagnation+rebreak | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 |
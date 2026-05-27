# WaveBox Cross-Symbol Filter Audit

## Preset Comparison

同じUSDJPY系プリセットを各銘柄へそのまま適用。

| symbol | preset | trades | win_rate | total_r | avg_r | pf | max_dd_r | oos_trades | oos_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | a_plus_shallow | 25 | 68.00 | 17.05 | 0.68 | 3.15 | 3.11 | 1 | 1.48 |
| GBPJPY | a_plus_shallow | 49 | 46.94 | 7.11 | 0.15 | 1.27 | 7.26 | 3 | -2.20 |
| EURJPY | a_plus_shallow | 34 | 47.06 | 4.86 | 0.14 | 1.26 | 4.79 | 1 | 1.48 |
| XAUUSD | a_plus_shallow | 52 | 42.31 | 0.33 | 0.01 | 1.01 | 8.50 | 2 | 0.48 |
| AUDJPY | a_plus_shallow | 26 | 34.62 | -4.51 | -0.17 | 0.74 | 7.59 | 0 | 0.00 |
| SILVER | a_plus_shallow | 50 | 44.00 | -5.52 | -0.11 | 0.84 | 8.93 | 5 | 2.16 |
| CHFJPY | a_plus_shallow | 38 | 34.21 | -6.71 | -0.18 | 0.73 | 9.40 | 3 | -2.55 |
| USDJPY | base | 145 | 48.28 | 24.43 | 0.17 | 1.32 | 17.71 | 11 | 11.30 |
| XAUUSD | base | 180 | 43.33 | 6.15 | 0.03 | 1.06 | 14.63 | 14 | 1.92 |
| EURJPY | base | 146 | 41.10 | -1.89 | -0.01 | 0.98 | 12.30 | 16 | 1.05 |
| SILVER | base | 190 | 46.32 | -11.10 | -0.06 | 0.91 | 35.44 | 16 | 12.94 |
| AUDJPY | base | 130 | 37.69 | -11.97 | -0.09 | 0.85 | 17.69 | 4 | -0.41 |
| GBPJPY | base | 152 | 38.16 | -12.75 | -0.08 | 0.87 | 22.65 | 12 | -9.06 |
| CHFJPY | base | 155 | 37.42 | -19.40 | -0.13 | 0.81 | 32.81 | 9 | -3.78 |
| USDJPY | h4_not_oppose_v04 | 43 | 62.79 | 23.20 | 0.54 | 2.42 | 4.18 | 3 | 4.43 |
| EURJPY | h4_not_oppose_v04 | 53 | 43.40 | 2.62 | 0.05 | 1.08 | 8.90 | 3 | 1.93 |
| SILVER | h4_not_oppose_v04 | 71 | 49.30 | 0.61 | 0.01 | 1.01 | 8.97 | 8 | 6.48 |
| CHFJPY | h4_not_oppose_v04 | 54 | 42.59 | -1.66 | -0.03 | 0.95 | 8.21 | 4 | -1.11 |
| XAUUSD | h4_not_oppose_v04 | 58 | 39.66 | -2.91 | -0.05 | 0.92 | 13.93 | 4 | -1.53 |
| GBPJPY | h4_not_oppose_v04 | 65 | 38.46 | -4.54 | -0.07 | 0.89 | 6.42 | 6 | -5.32 |
| AUDJPY | h4_not_oppose_v04 | 44 | 29.55 | -14.50 | -0.33 | 0.55 | 17.34 | 1 | 0.20 |
| USDJPY | usdjpy_v03_strict | 68 | 61.76 | 34.95 | 0.51 | 2.31 | 4.16 | 6 | 8.88 |
| EURJPY | usdjpy_v03_strict | 82 | 45.12 | 7.48 | 0.09 | 1.16 | 8.02 | 6 | 3.83 |
| SILVER | usdjpy_v03_strict | 103 | 50.49 | 4.65 | 0.05 | 1.07 | 18.04 | 11 | 10.62 |
| XAUUSD | usdjpy_v03_strict | 102 | 42.16 | 1.80 | 0.02 | 1.03 | 12.50 | 4 | 0.96 |
| GBPJPY | usdjpy_v03_strict | 89 | 35.96 | -12.09 | -0.14 | 0.79 | 13.82 | 6 | -5.30 |
| AUDJPY | usdjpy_v03_strict | 66 | 33.33 | -13.69 | -0.21 | 0.69 | 18.68 | 1 | 1.47 |
| CHFJPY | usdjpy_v03_strict | 91 | 35.16 | -16.81 | -0.18 | 0.72 | 22.90 | 5 | -4.63 |
| USDJPY | usdjpy_v04_filtered | 74 | 62.16 | 38.71 | 0.52 | 2.34 | 4.16 | 6 | 8.88 |
| EURJPY | usdjpy_v04_filtered | 88 | 44.32 | 6.29 | 0.07 | 1.12 | 8.69 | 8 | 4.26 |
| SILVER | usdjpy_v04_filtered | 119 | 48.74 | -0.11 | -0.00 | 1.00 | 18.57 | 11 | 10.62 |
| XAUUSD | usdjpy_v04_filtered | 117 | 41.03 | -1.43 | -0.01 | 0.98 | 14.17 | 6 | 1.45 |
| CHFJPY | usdjpy_v04_filtered | 97 | 37.11 | -13.19 | -0.14 | 0.79 | 22.70 | 6 | -3.18 |
| GBPJPY | usdjpy_v04_filtered | 98 | 35.71 | -13.97 | -0.14 | 0.78 | 16.89 | 7 | -6.34 |
| AUDJPY | usdjpy_v04_filtered | 79 | 32.91 | -17.71 | -0.22 | 0.67 | 22.14 | 2 | 1.67 |

## Best Coarse Filters By Symbol

| symbol | verdict | trades | win_rate | total_r | avg_r | pf | max_dd_r | worst_2y_r | oos_trades | oos_r | direction | h4 | retrace | hours | recovery | body |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | research_candidate | 26 | 69.23 | 18.53 | 0.71 | 3.33 | 3.11 | -0.62 | 2 | 2.97 | both | any | r50_618 | ex_1_6 | any | any |
| GBPJPY | research_candidate | 26 | 61.54 | 13.75 | 0.53 | 2.45 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6 | rec25_85 | ge45 |
| SILVER | weak_candidate | 30 | 60.00 | 8.84 | 0.29 | 1.60 | 6.90 | -3.20 | 6 | 3.71 | short | not_oppose | r50_800 | ex_1_6_11_14 | rec25_85 | any |
| AUDJPY | weak_candidate | 32 | 53.12 | 8.61 | 0.27 | 1.55 | 5.22 | -2.72 | 0 | 0.00 | long | any | r50_764 | none | rec25_85 | ge45 |
| EURJPY | weak_candidate | 30 | 50.00 | 6.41 | 0.21 | 1.41 | 4.18 | -2.75 | 3 | 1.93 | long | not_oppose | r50_764 | ex_1_6_14 | any | any |
| XAUUSD | weak_candidate | 29 | 48.28 | 4.64 | 0.16 | 1.30 | 6.72 | -1.83 | 2 | 0.49 | short | not_oppose | r50_764 | none | any | ge45 |
| CHFJPY | weak_candidate | 28 | 50.00 | 3.95 | 0.14 | 1.28 | 6.15 | -2.82 | 5 | 0.36 | long | not_oppose | r50_800 | ex_1 | any | ge45 |

## Top Filters

| symbol | score | trades | win_rate | total_r | avg_r | pf | max_dd_r | worst_2y_r | oos_trades | oos_r | direction | h4 | retrace | hours | recovery | body |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUDJPY | 28.75 | 32 | 53.12 | 8.61 | 0.27 | 1.55 | 5.22 | -2.72 | 0 | 0.00 | long | any | r50_764 | none | rec25_85 | ge45 |
| AUDJPY | 26.78 | 28 | 50.00 | 6.08 | 0.22 | 1.44 | 2.42 | -1.23 | 0 | 0.00 | long | not_oppose | r50_886 | none | rec25_85 | ge45 |
| AUDJPY | 24.12 | 33 | 51.52 | 7.54 | 0.23 | 1.45 | 5.22 | -2.72 | 0 | 0.00 | long | any | r50_786 | none | rec25_85 | ge45 |
| AUDJPY | 21.55 | 30 | 50.00 | 6.34 | 0.21 | 1.41 | 4.17 | -3.12 | 0 | 0.00 | long | any | r50_886 | ex_1_6_11_14 | rec25_85 | any |
| AUDJPY | 20.01 | 27 | 51.85 | 4.89 | 0.18 | 1.36 | 4.38 | -2.10 | 1 | 0.20 | long | not_oppose | r50_786 | none | any | ge45 |
| AUDJPY | 19.81 | 34 | 50.00 | 6.48 | 0.19 | 1.37 | 5.22 | -2.72 | 0 | 0.00 | long | any | r50_800 | none | rec25_85 | ge45 |
| AUDJPY | 18.86 | 44 | 47.73 | 7.03 | 0.16 | 1.31 | 5.04 | -1.78 | 0 | 0.00 | long | any | r50_886 | none | rec25_85 | ge45 |
| AUDJPY | 16.61 | 40 | 50.00 | 7.81 | 0.20 | 1.38 | 5.22 | -3.76 | 1 | -1.05 | long | any | r50_764 | none | rec25_85 | any |
| CHFJPY | 13.34 | 28 | 50.00 | 3.95 | 0.14 | 1.28 | 6.15 | -2.82 | 5 | 0.36 | long | not_oppose | r50_800 | ex_1 | any | ge45 |
| CHFJPY | 12.78 | 26 | 50.00 | 3.50 | 0.13 | 1.27 | 5.66 | -2.82 | 5 | 0.36 | long | not_oppose | r50_764 | ex_1 | any | ge45 |
| CHFJPY | 12.78 | 26 | 50.00 | 3.50 | 0.13 | 1.27 | 5.66 | -2.82 | 5 | 0.36 | long | not_oppose | r50_786 | ex_1 | any | ge45 |
| CHFJPY | 11.27 | 29 | 48.28 | 4.03 | 0.14 | 1.26 | 5.66 | -3.84 | 4 | 1.39 | long | not_oppose | r50_786 | ex_1 | rec25_85 | any |
| CHFJPY | 11.27 | 29 | 48.28 | 4.03 | 0.14 | 1.26 | 5.66 | -3.84 | 4 | 1.39 | long | not_oppose | r50_800 | ex_1 | rec25_85 | any |
| CHFJPY | 8.04 | 34 | 47.06 | 3.78 | 0.11 | 1.21 | 6.30 | -3.84 | 5 | 0.36 | long | not_oppose | r50_886 | ex_1 | rec25_85 | any |
| CHFJPY | 8.01 | 33 | 48.48 | 3.70 | 0.11 | 1.21 | 8.24 | -2.82 | 6 | -0.67 | long | not_oppose | r50_886 | ex_1 | any | ge45 |
| CHFJPY | 7.91 | 28 | 46.43 | 2.63 | 0.09 | 1.17 | 6.39 | -2.82 | 4 | 1.39 | long | not_oppose | r50_764 | none | rec25_85 | ge45 |
| EURJPY | 22.57 | 30 | 50.00 | 6.41 | 0.21 | 1.41 | 4.18 | -2.75 | 3 | 1.93 | long | not_oppose | r50_764 | ex_1_6_14 | any | any |
| EURJPY | 22.57 | 30 | 50.00 | 6.41 | 0.21 | 1.41 | 4.18 | -2.75 | 3 | 1.93 | long | not_oppose | r50_764 | ex_1_6_11_14 | any | any |
| EURJPY | 18.09 | 25 | 48.00 | 4.15 | 0.17 | 1.31 | 4.39 | -2.08 | 3 | 1.93 | long | not_oppose | r50_764 | ex_1_6_14 | any | ge45 |
| EURJPY | 18.09 | 25 | 48.00 | 4.15 | 0.17 | 1.31 | 4.39 | -2.08 | 3 | 1.93 | long | not_oppose | r50_764 | ex_1_6_11_14 | any | ge45 |
| EURJPY | 18.09 | 25 | 48.00 | 4.15 | 0.17 | 1.31 | 4.39 | -2.08 | 3 | 1.93 | long | not_oppose | r50_786 | ex_1_6_14 | any | ge45 |
| EURJPY | 18.09 | 25 | 48.00 | 4.15 | 0.17 | 1.31 | 4.39 | -2.08 | 3 | 1.93 | long | not_oppose | r50_786 | ex_1_6_11_14 | any | ge45 |
| EURJPY | 18.07 | 31 | 48.39 | 5.38 | 0.17 | 1.32 | 4.18 | -2.75 | 3 | 1.93 | long | not_oppose | r50_786 | ex_1_6_14 | any | any |
| EURJPY | 18.07 | 31 | 48.39 | 5.38 | 0.17 | 1.32 | 4.18 | -2.75 | 3 | 1.93 | long | not_oppose | r50_786 | ex_1_6_11_14 | any | any |
| GBPJPY | 57.27 | 26 | 61.54 | 13.75 | 0.53 | 2.45 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6 | rec25_85 | ge45 |
| GBPJPY | 57.27 | 26 | 61.54 | 13.75 | 0.53 | 2.45 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6_14 | rec25_85 | ge45 |
| GBPJPY | 57.27 | 26 | 61.54 | 13.75 | 0.53 | 2.45 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6_11_14 | rec25_85 | ge45 |
| GBPJPY | 54.75 | 28 | 60.71 | 14.16 | 0.51 | 2.34 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1 | rec25_85 | ge45 |
| GBPJPY | 50.31 | 27 | 59.26 | 12.72 | 0.47 | 2.21 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6 | any | ge45 |
| GBPJPY | 50.31 | 27 | 59.26 | 12.72 | 0.47 | 2.21 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6_14 | any | ge45 |
| GBPJPY | 50.31 | 27 | 59.26 | 12.72 | 0.47 | 2.21 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | ex_1_6_11_14 | any | ge45 |
| GBPJPY | 46.59 | 31 | 58.06 | 13.52 | 0.44 | 2.07 | 2.20 | -2.20 | 3 | -2.20 | long | any | r50_618 | none | rec25_85 | ge45 |
| SILVER | 29.70 | 30 | 60.00 | 8.84 | 0.29 | 1.60 | 6.90 | -3.20 | 6 | 3.71 | short | not_oppose | r50_800 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 29.32 | 34 | 58.82 | 8.51 | 0.25 | 1.50 | 4.77 | -1.51 | 6 | 3.71 | short | not_oppose | r50_886 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 24.86 | 29 | 58.62 | 7.35 | 0.25 | 1.50 | 6.90 | -3.20 | 5 | 2.22 | short | not_oppose | r50_786 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 21.44 | 54 | 55.56 | 9.95 | 0.18 | 1.34 | 5.83 | -2.03 | 9 | 7.97 | both | not_oppose | r50_800 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 20.64 | 67 | 58.21 | 17.23 | 0.26 | 1.52 | 8.21 | -6.97 | 11 | 8.20 | short | any | r50_886 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 20.58 | 40 | 57.50 | 7.86 | 0.20 | 1.37 | 5.35 | -2.84 | 6 | 3.71 | short | not_oppose | r50_886 | ex_1_6_11_14 | any | any |
| SILVER | 20.54 | 28 | 57.14 | 6.05 | 0.22 | 1.41 | 6.90 | -3.20 | 5 | 2.22 | short | not_oppose | r50_764 | ex_1_6_11_14 | rec25_85 | any |
| SILVER | 19.67 | 52 | 57.69 | 12.73 | 0.24 | 1.48 | 9.14 | -5.79 | 9 | 7.84 | short | any | r50_800 | ex_1_6_11_14 | rec25_85 | any |
| USDJPY | 88.01 | 26 | 69.23 | 18.53 | 0.71 | 3.33 | 3.11 | -0.62 | 2 | 2.97 | both | any | r50_618 | ex_1_6 | any | any |
| USDJPY | 83.66 | 28 | 67.86 | 18.97 | 0.68 | 3.11 | 3.11 | -0.62 | 2 | 2.97 | both | any | r50_618 | ex_1 | any | any |
| USDJPY | 83.58 | 25 | 68.00 | 17.05 | 0.68 | 3.15 | 3.11 | -0.62 | 1 | 1.48 | both | any | r50_618 | ex_1_6_14 | any | any |
| USDJPY | 83.58 | 25 | 68.00 | 17.05 | 0.68 | 3.15 | 3.11 | -0.62 | 1 | 1.48 | both | any | r50_618 | ex_1_6_11_14 | any | any |
| USDJPY | 79.77 | 44 | 65.91 | 27.02 | 0.61 | 2.73 | 2.08 | -0.20 | 4 | 5.91 | long | any | r50_886 | ex_1_6_11_14 | rec25_85 | any |
| USDJPY | 77.34 | 40 | 65.00 | 23.92 | 0.60 | 2.69 | 2.13 | 1.26 | 4 | 5.93 | short | any | r50_800 | ex_1_6_14 | any | any |
| USDJPY | 76.30 | 37 | 64.86 | 22.01 | 0.59 | 2.67 | 2.13 | 0.77 | 3 | 4.45 | short | any | r50_786 | ex_1_6_14 | any | any |
| USDJPY | 76.30 | 37 | 64.86 | 22.01 | 0.59 | 2.67 | 2.13 | 0.77 | 3 | 4.45 | short | any | r50_786 | ex_1_6_11_14 | any | any |
| XAUUSD | 17.12 | 29 | 48.28 | 4.64 | 0.16 | 1.30 | 6.72 | -1.83 | 2 | 0.49 | short | not_oppose | r50_764 | none | any | ge45 |
| XAUUSD | 13.92 | 36 | 47.22 | 5.15 | 0.14 | 1.26 | 3.76 | -2.32 | 1 | -1.01 | long | not_oppose | r50_886 | ex_1_6_11_14 | any | any |
| XAUUSD | 13.62 | 37 | 48.65 | 6.24 | 0.17 | 1.32 | 8.72 | -3.86 | 5 | 2.46 | short | not_oppose | r50_886 | ex_1_6_14 | any | any |
| XAUUSD | 13.54 | 25 | 48.00 | 3.81 | 0.15 | 1.28 | 6.05 | -3.23 | 2 | 0.49 | short | not_oppose | r50_786 | ex_1_6_14 | any | ge45 |
| XAUUSD | 13.54 | 25 | 48.00 | 3.81 | 0.15 | 1.28 | 6.05 | -3.23 | 2 | 0.49 | short | not_oppose | r50_800 | ex_1_6_14 | any | ge45 |
| XAUUSD | 13.39 | 27 | 48.15 | 4.16 | 0.15 | 1.29 | 7.09 | -3.23 | 2 | 0.49 | short | not_oppose | r50_786 | ex_1_6_14 | any | any |
| XAUUSD | 13.39 | 27 | 48.15 | 4.16 | 0.15 | 1.29 | 7.09 | -3.23 | 2 | 0.49 | short | not_oppose | r50_800 | ex_1_6_14 | any | any |
| XAUUSD | 13.21 | 25 | 48.00 | 3.83 | 0.15 | 1.28 | 7.08 | -3.22 | 2 | 0.49 | short | not_oppose | r50_764 | ex_1_6 | any | any |

## Notes

- This is not a final optimizer.
- Month exclusions are intentionally excluded.
- Symbols with weak OOS or negative rolling windows remain research only.
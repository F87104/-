# H1 vs H4 V候補後トリガー比較 2015-2024

## 比較対象

- 再ブレイク型: 61.8〜80%回復後、一度押してから戻り高値を再ブレイク。
- 高値停滞+再ブレイク型: 高値停滞と再ブレイクが同時に重なるものだけ。
- 買いのみ、コスト込みR、シグナル次足始値エントリー。

## H1/H4 比較

| timeframe | strategy | pattern | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | all accepted | 332 | 38.86 | 47.89 | 0.14 | 1.23 | 19.52 |
| H4 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | all accepted | 98 | 47.96 | 17.98 | 0.18 | 1.38 | 7.27 |
| H1 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | all accepted | 335 | 38.81 | 47.81 | 0.14 | 1.23 | 19.52 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | all accepted | 124 | 50.00 | 32.15 | 0.26 | 1.55 | 6.41 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | all accepted | 718 | 36.63 | 43.97 | 0.06 | 1.09 | 44.56 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | all accepted | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | all accepted | 718 | 36.91 | 50.00 | 0.07 | 1.11 | 41.57 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | all accepted | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 |
| H1 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | rebreak including overlap | 332 | 38.86 | 47.89 | 0.14 | 1.23 | 19.52 |
| H4 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | rebreak including overlap | 98 | 47.96 | 17.98 | 0.18 | 1.38 | 7.27 |
| H1 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | rebreak including overlap | 330 | 38.48 | 43.88 | 0.13 | 1.21 | 20.53 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | rebreak including overlap | 89 | 49.44 | 20.47 | 0.23 | 1.49 | 7.27 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | rebreak including overlap | 718 | 36.63 | 43.97 | 0.06 | 1.09 | 44.56 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | rebreak including overlap | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | rebreak including overlap | 711 | 36.57 | 42.09 | 0.06 | 1.09 | 44.54 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | rebreak including overlap | 228 | 46.05 | 48.00 | 0.21 | 1.42 | 11.34 |
| H1 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | stagnation+rebreak only | 4 | 0.00 | -4.06 | -1.01 | 0.00 | 3.03 |
| H4 | VCTX_618_800_FAST_REBREAK_ONLY_RR2 | stagnation+rebreak only | 23 | 52.17 | 7.94 | 0.35 | 1.79 | 2.64 |
| H1 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | stagnation+rebreak only | 4 | 0.00 | -4.06 | -1.01 | 0.00 | 3.03 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | stagnation+rebreak only | 19 | 57.89 | 10.45 | 0.55 | 2.49 | 2.05 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | stagnation+rebreak only | 4 | 0.00 | -4.05 | -1.01 | 0.00 | 3.02 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | stagnation+rebreak only | 47 | 48.94 | 16.09 | 0.34 | 1.74 | 4.79 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | stagnation+rebreak only | 4 | 0.00 | -4.05 | -1.01 | 0.00 | 3.02 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | stagnation+rebreak only | 42 | 50.00 | 16.60 | 0.40 | 1.89 | 5.30 |

## 再ブレイク型 通貨別

| timeframe | strategy | symbol | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | GBPJPY | 122 | 40.16 | 20.09 | 0.16 | 1.27 | 6.15 | 4 | 177.70 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | GBPJPY | 44 | 52.27 | 14.91 | 0.34 | 1.76 | 3.03 | 3 | 104.80 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | AUDJPY | 101 | 38.61 | 13.94 | 0.14 | 1.22 | 13.74 | 12 | 237.20 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | CHFJPY | 91 | 38.46 | 12.17 | 0.13 | 1.21 | 9.19 | 7 | 216.03 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | XAUUSD | 34 | 47.06 | 10.97 | 0.32 | 1.80 | 3.62 | 4 | 112.65 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | USDJPY | 41 | 46.34 | 8.24 | 0.20 | 1.43 | 9.36 | 8 | 113.95 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | CHFJPY | 26 | 46.15 | 7.35 | 0.28 | 1.59 | 4.03 | 4 | 99.96 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | EURJPY | 124 | 35.48 | 6.41 | 0.05 | 1.08 | 10.93 | 7 | 178.46 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | AUDJPY | 35 | 42.86 | 2.76 | 0.08 | 1.14 | 8.10 | 7 | 91.97 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | XAUUSD | 95 | 34.74 | 2.14 | 0.02 | 1.03 | 15.47 | 12 | 217.32 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | EURJPY | 40 | 40.00 | 1.65 | 0.04 | 1.07 | 10.03 | 5 | 103.28 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | SILVER | 33 | 39.39 | -0.22 | -0.01 | 0.99 | 6.29 | 4 | 84.88 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | USDJPY | 106 | 34.91 | -2.55 | -0.02 | 0.96 | 18.38 | 9 | 233.62 |
| H1 | VCTX_618_800_REBREAK_ONLY_RR2 | SILVER | 79 | 32.91 | -8.22 | -0.10 | 0.86 | 15.60 | 8 | 219.82 |

## 高値停滞+再ブレイク型 通貨別

| timeframe | strategy | symbol | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | GBPJPY | 7 | 71.43 | 7.06 | 1.01 | 5.90 | 1.44 | 2 | 118.57 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | CHFJPY | 5 | 60.00 | 4.81 | 0.96 | 5.20 | 0.13 | 2 | 120.60 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | EURJPY | 8 | 50.00 | 3.58 | 0.45 | 2.17 | 2.04 | 3 | 119.38 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | XAUUSD | 4 | 50.00 | 1.96 | 0.49 | 1.97 | 2.02 | 2 | 111.00 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | USDJPY | 4 | 50.00 | 0.85 | 0.21 | 1.45 | 0.90 | 1 | 98.50 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | SILVER | 4 | 50.00 | 0.52 | 0.13 | 1.25 | 1.03 | 1 | 62.50 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | USDJPY | 1 | 0.00 | -1.00 | -1.00 | 0.00 | 0.00 | 1 | 69.00 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | CHFJPY | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 | 87.00 |
| H1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | EURJPY | 2 | 0.00 | -2.02 | -1.01 | 0.00 | 1.01 | 2 | 198.50 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | AUDJPY | 10 | 30.00 | -2.18 | -0.22 | 0.69 | 5.04 | 5 | 76.00 |
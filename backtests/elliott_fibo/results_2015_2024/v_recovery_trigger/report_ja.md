# V候補後トリガー検証 2015-2024

## 検証した考え方

- 急落後V字を即エントリー条件にせず、まず候補として扱う。
- 候補: 確定スイング高値から安値への急落後、終値が下落幅の61.8%〜80.0%まで戻す。
- エントリー: 候補発生後に、狭い高値停滞を上抜ける、または一度押してから戻り高値を再ブレイクする。
- 買いのみ。売りの逆V字は今回含めていません。
- エントリーはシグナル次足の始値、コスト込みRで集計。

## 全体結果

| timeframe | strategy | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | 288 | 44.79 | 42.25 | 0.15 | 1.29 | 14.39 | 12 | 99.28 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | 246 | 44.72 | 39.71 | 0.16 | 1.31 | 11.97 | 10 | 94.27 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | 247 | 45.75 | 37.64 | 0.15 | 1.31 | 17.77 | 13 | 102.80 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | 124 | 50.00 | 32.15 | 0.26 | 1.55 | 6.41 | 6 | 102.58 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | 156 | 46.79 | 29.71 | 0.19 | 1.39 | 10.43 | 6 | 97.63 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | 99 | 51.52 | 24.99 | 0.25 | 1.55 | 7.36 | 7 | 103.32 |
| D1 | VCTX_618_800_STAG_OR_REBREAK_RR2 | 46 | 65.22 | 14.62 | 0.32 | 2.17 | 5.04 | 3 | 46.37 |
| D1 | VCTX_618_786_STAG_OR_REBREAK_RR2 | 44 | 65.91 | 13.63 | 0.31 | 2.19 | 4.04 | 2 | 46.45 |
| D1 | VCTX_618_800_STAG_ONLY_RR2 | 38 | 68.42 | 11.62 | 0.31 | 2.18 | 5.32 | 3 | 46.87 |
| D1 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | 39 | 64.10 | 11.35 | 0.29 | 2.00 | 4.03 | 3 | 45.21 |
| D1 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | 16 | 75.00 | 8.58 | 0.54 | 3.80 | 2.06 | 3 | 46.25 |
| D1 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | 35 | 62.86 | 7.82 | 0.22 | 1.83 | 5.65 | 3 | 48.49 |
| D1 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | 11 | 72.73 | 4.38 | 0.40 | 3.13 | 2.02 | 3 | 49.91 |
| D1 | VCTX_618_800_REBREAK_ONLY_RR2 | 27 | 51.85 | 2.39 | 0.09 | 1.27 | 3.02 | 2 | 45.59 |

## H4結果

| timeframe | strategy | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | 288 | 44.79 | 42.25 | 0.15 | 1.29 | 14.39 | 12 | 99.28 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | 246 | 44.72 | 39.71 | 0.16 | 1.31 | 11.97 | 10 | 94.27 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | 247 | 45.75 | 37.64 | 0.15 | 1.31 | 17.77 | 13 | 102.80 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | 124 | 50.00 | 32.15 | 0.26 | 1.55 | 6.41 | 6 | 102.58 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | 156 | 46.79 | 29.71 | 0.19 | 1.39 | 10.43 | 6 | 97.63 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | 99 | 51.52 | 24.99 | 0.25 | 1.55 | 7.36 | 7 | 103.32 |

## H4 通貨別

| timeframe | strategy | symbol | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | GBPJPY | 49 | 57.14 | 18.63 | 0.38 | 1.90 | 3.02 | 3 | 108.02 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | GBPJPY | 46 | 56.52 | 17.54 | 0.38 | 1.90 | 2.90 | 2 | 101.00 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | GBPJPY | 44 | 52.27 | 14.91 | 0.34 | 1.76 | 3.03 | 3 | 104.80 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | USDJPY | 40 | 52.50 | 14.88 | 0.37 | 1.90 | 6.36 | 4 | 99.95 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | USDJPY | 44 | 50.00 | 14.22 | 0.32 | 1.75 | 6.36 | 5 | 108.41 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | USDJPY | 37 | 48.65 | 13.75 | 0.37 | 1.81 | 7.23 | 7 | 95.08 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | GBPJPY | 42 | 57.14 | 13.69 | 0.33 | 1.78 | 3.49 | 3 | 117.24 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | GBPJPY | 46 | 54.35 | 13.61 | 0.30 | 1.66 | 2.02 | 2 | 105.37 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | USDJPY | 43 | 48.84 | 13.44 | 0.31 | 1.71 | 6.36 | 5 | 106.74 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | GBPJPY | 20 | 65.00 | 13.03 | 0.65 | 2.85 | 1.19 | 2 | 106.45 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | XAUUSD | 39 | 46.15 | 11.52 | 0.30 | 1.69 | 3.91 | 4 | 109.74 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | XAUUSD | 39 | 46.15 | 11.52 | 0.30 | 1.69 | 3.91 | 4 | 108.28 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | XAUUSD | 34 | 47.06 | 10.97 | 0.32 | 1.80 | 3.62 | 4 | 112.65 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | GBPJPY | 28 | 53.57 | 10.38 | 0.37 | 1.83 | 4.18 | 4 | 94.18 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | XAUUSD | 26 | 50.00 | 10.35 | 0.40 | 1.94 | 4.32 | 4 | 103.88 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | GBPJPY | 16 | 68.75 | 10.12 | 0.63 | 3.01 | 1.01 | 2 | 118.44 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | USDJPY | 25 | 52.00 | 8.68 | 0.35 | 1.74 | 2.76 | 2 | 96.32 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | CHFJPY | 23 | 52.17 | 8.40 | 0.37 | 1.82 | 5.05 | 5 | 105.13 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | AUDJPY | 23 | 56.52 | 8.31 | 0.36 | 1.82 | 5.05 | 5 | 83.39 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | USDJPY | 41 | 46.34 | 8.24 | 0.20 | 1.43 | 9.36 | 8 | 113.95 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | XAUUSD | 33 | 42.42 | 7.60 | 0.23 | 1.52 | 3.91 | 3 | 110.33 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | CHFJPY | 26 | 46.15 | 7.35 | 0.28 | 1.59 | 4.03 | 4 | 99.96 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | CHFJPY | 32 | 46.88 | 6.68 | 0.21 | 1.41 | 5.05 | 5 | 100.03 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | CHFJPY | 32 | 46.88 | 6.68 | 0.21 | 1.41 | 5.05 | 5 | 97.22 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | USDJPY | 17 | 58.82 | 6.47 | 0.38 | 2.20 | 2.37 | 3 | 130.94 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | USDJPY | 15 | 60.00 | 5.69 | 0.38 | 2.15 | 1.92 | 2 | 124.40 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | AUDJPY | 18 | 55.56 | 4.37 | 0.24 | 1.54 | 4.03 | 4 | 94.67 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | AUDJPY | 32 | 50.00 | 4.29 | 0.13 | 1.27 | 7.36 | 7 | 100.47 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | XAUUSD | 16 | 43.75 | 4.27 | 0.27 | 1.57 | 4.40 | 5 | 102.19 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | AUDJPY | 27 | 51.85 | 3.99 | 0.15 | 1.32 | 7.55 | 8 | 101.74 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | CHFJPY | 26 | 46.15 | 3.75 | 0.14 | 1.28 | 5.04 | 5 | 103.81 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | AUDJPY | 42 | 45.24 | 3.75 | 0.09 | 1.17 | 8.60 | 8 | 91.67 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | EURJPY | 22 | 40.91 | 2.97 | 0.14 | 1.26 | 3.82 | 4 | 97.41 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | AUDJPY | 35 | 42.86 | 2.76 | 0.08 | 1.14 | 8.10 | 7 | 91.97 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | CHFJPY | 13 | 46.15 | 2.48 | 0.19 | 1.35 | 3.02 | 3 | 96.08 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | CHFJPY | 16 | 43.75 | 2.35 | 0.15 | 1.32 | 2.02 | 3 | 113.25 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | XAUUSD | 15 | 40.00 | 2.29 | 0.15 | 1.27 | 5.35 | 6 | 100.60 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | AUDJPY | 41 | 43.90 | 1.75 | 0.04 | 1.08 | 8.60 | 8 | 93.71 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | EURJPY | 40 | 40.00 | 1.65 | 0.04 | 1.07 | 10.03 | 5 | 103.28 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | CHFJPY | 9 | 44.44 | 1.61 | 0.18 | 1.32 | 2.02 | 2 | 96.67 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | XAUUSD | 13 | 38.46 | 1.32 | 0.10 | 1.18 | 5.35 | 6 | 88.00 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | SILVER | 12 | 50.00 | 1.12 | 0.09 | 1.18 | 2.90 | 3 | 114.17 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | AUDJPY | 35 | 42.86 | 1.03 | 0.03 | 1.05 | 8.56 | 6 | 89.91 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | EURJPY | 16 | 37.50 | 0.77 | 0.05 | 1.08 | 2.05 | 3 | 86.25 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | EURJPY | 19 | 36.84 | 0.68 | 0.04 | 1.07 | 2.05 | 3 | 92.21 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | SILVER | 33 | 39.39 | -0.22 | -0.01 | 0.99 | 6.29 | 4 | 84.88 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | EURJPY | 48 | 37.50 | -0.72 | -0.02 | 0.97 | 10.42 | 5 | 96.88 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | EURJPY | 42 | 35.71 | -0.97 | -0.02 | 0.96 | 10.16 | 9 | 100.19 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | SILVER | 17 | 41.18 | -1.11 | -0.07 | 0.89 | 3.94 | 4 | 113.94 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | EURJPY | 49 | 36.73 | -1.73 | -0.04 | 0.94 | 10.42 | 5 | 96.69 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | SILVER | 22 | 36.36 | -2.94 | -0.13 | 0.79 | 6.53 | 6 | 84.05 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | SILVER | 39 | 35.90 | -4.02 | -0.10 | 0.84 | 8.89 | 6 | 85.41 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | SILVER | 39 | 35.90 | -4.02 | -0.10 | 0.84 | 8.89 | 6 | 85.41 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | SILVER | 33 | 33.33 | -4.40 | -0.13 | 0.80 | 6.77 | 6 | 78.85 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | SILVER | 32 | 34.38 | -5.59 | -0.17 | 0.73 | 9.73 | 8 | 84.56 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | EURJPY | 46 | 32.61 | -6.96 | -0.15 | 0.77 | 10.42 | 5 | 90.39 |

## H4 トリガー別

| timeframe | strategy | trigger_type | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | rebreak | 186 | 45.16 | 31.40 | 0.17 | 1.33 | 12.90 | 13 | 100.43 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | rebreak | 206 | 44.17 | 29.57 | 0.14 | 1.28 | 11.89 | 12 | 102.80 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | rebreak | 184 | 44.57 | 28.35 | 0.15 | 1.30 | 12.90 | 13 | 98.94 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | rebreak | 156 | 44.87 | 23.82 | 0.15 | 1.30 | 15.93 | 11 | 101.64 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | rebreak | 150 | 42.67 | 22.34 | 0.15 | 1.28 | 10.86 | 10 | 93.34 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | stagnation+rebreak | 61 | 47.54 | 16.92 | 0.28 | 1.57 | 5.20 | 6 | 95.74 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 42 | 50.00 | 16.60 | 0.40 | 1.89 | 5.30 | 5 | 100.86 |
| H4 | VCTX_618_800_REBREAK_ONLY_RR2 | stagnation+rebreak | 47 | 48.94 | 16.09 | 0.34 | 1.74 | 4.79 | 5 | 99.70 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 36 | 50.00 | 15.01 | 0.42 | 1.96 | 4.29 | 4 | 97.81 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 39 | 48.72 | 14.84 | 0.38 | 1.84 | 5.30 | 5 | 102.54 |
| H4 | VCTX_618_800_STAG_ONLY_RR2 | stagnation | 95 | 46.32 | 12.79 | 0.13 | 1.27 | 6.88 | 5 | 98.85 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 33 | 51.52 | 11.68 | 0.35 | 1.81 | 6.73 | 4 | 105.21 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | stagnation | 35 | 51.43 | 11.68 | 0.33 | 1.68 | 5.03 | 5 | 86.26 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 19 | 57.89 | 10.45 | 0.55 | 2.49 | 2.05 | 3 | 120.95 |
| H4 | VCTX_618_800_FAST_STAG_OR_REBREAK_RR2 | rebreak | 70 | 47.14 | 10.03 | 0.14 | 1.29 | 6.26 | 6 | 105.76 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | stagnation | 27 | 51.85 | 8.86 | 0.33 | 1.67 | 4.07 | 4 | 92.33 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | rebreak | 58 | 50.00 | 8.78 | 0.15 | 1.32 | 4.23 | 4 | 104.57 |
| H4 | VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2 | stagnation+rebreak | 14 | 57.14 | 7.35 | 0.53 | 2.48 | 1.04 | 2 | 119.36 |
| H4 | VCTX_618_800_REC1_STAG_OR_REBREAK_RR2 | stagnation | 60 | 46.67 | 2.36 | 0.04 | 1.07 | 7.71 | 6 | 94.47 |
| H4 | VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2 | stagnation | 58 | 44.83 | 2.14 | 0.04 | 1.07 | 9.33 | 5 | 104.53 |
| H4 | VCTX_618_800_STAG_OR_REBREAK_RR2 | stagnation | 66 | 43.94 | 1.05 | 0.02 | 1.03 | 7.45 | 4 | 99.20 |
| H4 | VCTX_618_786_STAG_OR_REBREAK_RR2 | stagnation | 65 | 43.08 | -0.93 | -0.01 | 0.97 | 7.45 | 4 | 98.31 |

## 出力ファイル

- `trades.csv`
- `summary_overall.csv`
- `summary_by_symbol.csv`
- `summary_by_trigger.csv`
- `summary_by_year.csv`
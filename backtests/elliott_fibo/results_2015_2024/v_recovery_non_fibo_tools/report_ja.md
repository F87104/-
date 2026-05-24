# H4 V候補後トリガー 非フィボツール研究 2015-2024

## 目的

フィボナッチ水準だけに頼らず、EMA/ADX/RSI/ボリンジャー/ドンチャン/ATR/ローソク足の視点で、V候補後トリガーの質を判定する。

## 使ったベース

- H4のみ。
- 買いのみ。
- 既存のV候補後トリガーから、`T4_REBREAK_ONLY` と `T5_STAG_OR_REBREAK` をベースにした。
- 各フィルターは、シグナル足の状態だけで判定。

## フィルター別 結果

| base_strategy | filter | family | description | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T4_REBREAK_ONLY | CloseLoc_ge_65 | Candle | 終値が足の上側35%以内 | 246 | 45.93 | 49.26 | 0.20 | 1.40 | 11.55 | 11 | 102.80 |
| T4_REBREAK_ONLY | RSI_45_75 | RSI | RSI14が45〜75 | 244 | 45.08 | 45.98 | 0.19 | 1.37 | 10.36 | 11 | 101.18 |
| T4_REBREAK_ONLY | RSI_50_75 | RSI | RSI14が50〜75 | 244 | 45.08 | 45.98 | 0.19 | 1.37 | 10.36 | 11 | 101.18 |
| T4_REBREAK_ONLY | RSI_lt_75 | RSI | RSI14 < 75で過熱回避 | 244 | 45.08 | 45.98 | 0.19 | 1.37 | 10.36 | 11 | 101.18 |
| T4_REBREAK_ONLY | ALL_BASELINE | baseline | フィルターなし | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| T4_REBREAK_ONLY | RSI_gt_50 | RSI | RSI14 > 50 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| T4_REBREAK_ONLY | ATR_ratio_lt_1_5 | ATR | ATR14がATR50の1.5倍未満 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| T4_REBREAK_ONLY | Body_ge_60 | Candle | 実体比率60%以上 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| T4_REBREAK_ONLY | Range5_le_6ATR | Compression | 直近5本レンジが6ATR以下 | 253 | 45.06 | 45.66 | 0.18 | 1.36 | 11.34 | 11 | 102.23 |
| T4_REBREAK_ONLY | BB_pos_60_110 | Bollinger | BB内位置が上側60%〜軽い上抜け | 199 | 45.23 | 45.65 | 0.23 | 1.46 | 11.35 | 10 | 101.81 |
| T4_REBREAK_ONLY | EMA_close_gt_50 | EMA | 終値がEMA50より上 | 243 | 44.86 | 41.32 | 0.17 | 1.34 | 13.19 | 11 | 102.23 |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | Bollinger | BB幅が3ATR以上 | 222 | 45.50 | 40.38 | 0.18 | 1.37 | 12.58 | 10 | 106.29 |
| T4_REBREAK_ONLY | EMA_close_gt_200 | EMA | 終値がEMA200より上 | 183 | 44.81 | 33.21 | 0.18 | 1.36 | 12.49 | 9 | 100.41 |
| T4_REBREAK_ONLY | Trend_Momentum_Close | Combo | EMA20>50、RSI>50、終値位置65%以上 | 162 | 46.91 | 32.99 | 0.20 | 1.41 | 8.08 | 8 | 104.56 |
| T4_REBREAK_ONLY | EMA_20_gt_50 | EMA | EMA20がEMA50より上 | 167 | 46.11 | 30.85 | 0.18 | 1.37 | 8.08 | 8 | 103.76 |
| T4_REBREAK_ONLY | ATR_pctile_lt_85 | ATR | ATR上位15%の荒れ相場を除外 | 205 | 43.41 | 30.30 | 0.15 | 1.28 | 12.00 | 10 | 97.88 |
| T4_REBREAK_ONLY | EMA_RSI_ATR | Combo | EMA20>50、RSI50〜75、ATR過大除外 | 135 | 45.93 | 29.64 | 0.22 | 1.43 | 8.19 | 8 | 97.54 |
| T4_REBREAK_ONLY | EMA20_slope_pos | EMA | EMA20の10本傾きがプラス | 227 | 43.17 | 25.55 | 0.11 | 1.22 | 15.17 | 11 | 103.26 |
| T4_REBREAK_ONLY | BB_width_ge_4ATR | Bollinger | BB幅が4ATR以上 | 142 | 45.77 | 23.02 | 0.16 | 1.34 | 15.71 | 10 | 113.84 |
| T4_REBREAK_ONLY | ADX_ge_18 | ADX | ADX14 >= 18 | 176 | 43.18 | 21.19 | 0.12 | 1.24 | 18.72 | 15 | 105.17 |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | EMA | EMA20 > EMA50 > EMA200 | 114 | 45.61 | 18.76 | 0.16 | 1.32 | 7.07 | 7 | 100.44 |
| T4_REBREAK_ONLY | Donchian20_break | Donchian | 20本高値を終値で更新 | 208 | 42.79 | 17.23 | 0.08 | 1.16 | 18.69 | 10 | 106.19 |
| T4_REBREAK_ONLY | ADX_ge_22 | ADX | ADX14 >= 22 | 116 | 43.97 | 14.85 | 0.13 | 1.26 | 13.86 | 10 | 107.79 |
| T4_REBREAK_ONLY | Donchian55_break | Donchian | 55本高値を終値で更新 | 88 | 45.45 | 8.69 | 0.10 | 1.20 | 6.36 | 6 | 119.47 |
| T4_REBREAK_ONLY | ADX_Donchian_Body | Combo | ADX>=18、20本高値更新、実体60%以上 | 143 | 41.96 | 7.20 | 0.05 | 1.10 | 19.79 | 12 | 111.27 |
| T4_REBREAK_ONLY | ATR_pctile_20_90 | ATR | ATRが過小/過大すぎない 20〜90% | 164 | 40.85 | 4.50 | 0.03 | 1.05 | 14.72 | 10 | 103.99 |
| T4_REBREAK_ONLY | ADX_ge_25 | ADX | ADX14 >= 25 | 87 | 39.08 | 0.61 | 0.01 | 1.01 | 16.49 | 10 | 110.53 |
| T5_STAG_OR_REBREAK | RSI_45_75 | RSI | RSI14が45〜75 | 287 | 45.64 | 49.47 | 0.17 | 1.34 | 13.38 | 13 | 99.82 |
| T5_STAG_OR_REBREAK | RSI_50_75 | RSI | RSI14が50〜75 | 287 | 45.64 | 49.47 | 0.17 | 1.34 | 13.38 | 13 | 99.82 |
| T5_STAG_OR_REBREAK | RSI_lt_75 | RSI | RSI14 < 75で過熱回避 | 287 | 45.64 | 49.47 | 0.17 | 1.34 | 13.38 | 13 | 99.82 |
| T5_STAG_OR_REBREAK | ALL_BASELINE | baseline | フィルターなし | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| T5_STAG_OR_REBREAK | RSI_gt_50 | RSI | RSI14 > 50 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| T5_STAG_OR_REBREAK | ATR_ratio_lt_1_5 | ATR | ATR14がATR50の1.5倍未満 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| T5_STAG_OR_REBREAK | Body_ge_60 | Candle | 実体比率60%以上 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| T5_STAG_OR_REBREAK | Range5_le_6ATR | Compression | 直近5本レンジが6ATR以下 | 294 | 45.58 | 49.05 | 0.17 | 1.33 | 15.39 | 13 | 100.21 |
| T5_STAG_OR_REBREAK | CloseLoc_ge_65 | Candle | 終値が足の上側35%以内 | 285 | 45.96 | 48.66 | 0.17 | 1.34 | 15.39 | 13 | 101.06 |
| T5_STAG_OR_REBREAK | BB_pos_60_110 | Bollinger | BB内位置が上側60%〜軽い上抜け | 241 | 45.64 | 46.33 | 0.19 | 1.38 | 14.40 | 9 | 100.83 |
| T5_STAG_OR_REBREAK | EMA_close_gt_50 | EMA | 終値がEMA50より上 | 283 | 45.58 | 45.72 | 0.16 | 1.32 | 17.24 | 13 | 100.48 |
| T5_STAG_OR_REBREAK | BB_width_ge_3ATR | Bollinger | BB幅が3ATR以上 | 255 | 46.27 | 44.67 | 0.18 | 1.36 | 14.36 | 11 | 104.88 |
| T5_STAG_OR_REBREAK | EMA_close_gt_200 | EMA | 終値がEMA200より上 | 206 | 46.12 | 40.92 | 0.20 | 1.40 | 15.75 | 9 | 97.11 |
| T5_STAG_OR_REBREAK | EMA_20_gt_50 | EMA | EMA20がEMA50より上 | 191 | 47.12 | 37.86 | 0.20 | 1.40 | 8.86 | 9 | 100.09 |
| T5_STAG_OR_REBREAK | EMA_RSI_ATR | Combo | EMA20>50、RSI50〜75、ATR過大除外 | 160 | 46.88 | 35.42 | 0.22 | 1.44 | 8.17 | 9 | 95.26 |
| T5_STAG_OR_REBREAK | Trend_Momentum_Close | Combo | EMA20>50、RSI>50、終値位置65%以上 | 185 | 47.03 | 35.01 | 0.19 | 1.38 | 9.57 | 9 | 101.11 |
| T5_STAG_OR_REBREAK | ATR_pctile_lt_85 | ATR | ATR上位15%の荒れ相場を除外 | 240 | 43.75 | 31.53 | 0.13 | 1.25 | 15.40 | 12 | 95.65 |
| T5_STAG_OR_REBREAK | EMA20_slope_pos | EMA | EMA20の10本傾きがプラス | 265 | 44.15 | 30.37 | 0.11 | 1.22 | 18.13 | 13 | 101.13 |
| T5_STAG_OR_REBREAK | BB_width_ge_4ATR | Bollinger | BB幅が4ATR以上 | 173 | 47.40 | 29.31 | 0.17 | 1.36 | 14.92 | 12 | 111.90 |
| T5_STAG_OR_REBREAK | EMA_stack_20_50_200 | EMA | EMA20 > EMA50 > EMA200 | 133 | 45.11 | 21.29 | 0.16 | 1.31 | 10.68 | 7 | 93.86 |
| T5_STAG_OR_REBREAK | Donchian20_break | Donchian | 20本高値を終値で更新 | 210 | 42.86 | 18.99 | 0.09 | 1.17 | 17.80 | 10 | 103.45 |
| T5_STAG_OR_REBREAK | ADX_ge_18 | ADX | ADX14 >= 18 | 205 | 42.93 | 18.70 | 0.09 | 1.18 | 20.20 | 16 | 102.18 |
| T5_STAG_OR_REBREAK | ADX_ge_22 | ADX | ADX14 >= 22 | 138 | 43.48 | 11.04 | 0.08 | 1.16 | 16.16 | 10 | 104.83 |
| T5_STAG_OR_REBREAK | ATR_pctile_20_90 | ATR | ATRが過小/過大すぎない 20〜90% | 186 | 43.01 | 9.11 | 0.05 | 1.09 | 13.24 | 11 | 103.82 |
| T5_STAG_OR_REBREAK | Donchian55_break | Donchian | 55本高値を終値で更新 | 82 | 43.90 | 6.72 | 0.08 | 1.16 | 8.19 | 7 | 111.66 |
| T5_STAG_OR_REBREAK | ADX_Donchian_Body | Combo | ADX>=18、20本高値更新、実体60%以上 | 145 | 40.69 | 2.34 | 0.02 | 1.03 | 19.31 | 12 | 106.34 |
| T5_STAG_OR_REBREAK | ADX_ge_25 | ADX | ADX14 >= 25 | 101 | 39.60 | -1.47 | -0.01 | 0.97 | 18.09 | 9 | 107.03 |

## 通貨別 結果

| strategy | filter | symbol | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_r | max_losing_streak | avg_hold_bars | family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T4_REBREAK_ONLY | ALL_BASELINE | GBPJPY | 44 | 52.27 | 14.91 | 0.34 | 1.76 | 3.03 | 3 | 104.80 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | XAUUSD | 34 | 47.06 | 10.97 | 0.32 | 1.80 | 3.62 | 4 | 112.65 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | USDJPY | 41 | 46.34 | 8.24 | 0.20 | 1.43 | 9.36 | 8 | 113.95 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | CHFJPY | 26 | 46.15 | 7.35 | 0.28 | 1.59 | 4.03 | 4 | 99.96 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | AUDJPY | 35 | 42.86 | 2.76 | 0.08 | 1.14 | 8.10 | 7 | 91.97 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | EURJPY | 40 | 40.00 | 1.65 | 0.04 | 1.07 | 10.03 | 5 | 103.28 | baseline |
| T4_REBREAK_ONLY | ALL_BASELINE | SILVER | 33 | 39.39 | -0.22 | -0.01 | 0.99 | 6.29 | 4 | 84.88 | baseline |
| T4_REBREAK_ONLY | EMA_close_gt_50 | GBPJPY | 43 | 53.49 | 15.92 | 0.37 | 1.85 | 3.03 | 3 | 106.88 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | XAUUSD | 32 | 46.88 | 9.99 | 0.31 | 1.78 | 2.61 | 4 | 113.91 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | USDJPY | 41 | 46.34 | 8.24 | 0.20 | 1.43 | 9.36 | 8 | 113.95 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | CHFJPY | 23 | 47.83 | 7.37 | 0.32 | 1.71 | 3.02 | 3 | 100.00 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | SILVER | 32 | 40.62 | 0.81 | 0.03 | 1.04 | 6.29 | 4 | 83.03 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | AUDJPY | 34 | 41.18 | 0.78 | 0.02 | 1.04 | 8.10 | 7 | 90.03 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_50 | EURJPY | 38 | 36.84 | -1.79 | -0.05 | 0.92 | 11.85 | 5 | 102.92 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | USDJPY | 35 | 48.57 | 10.16 | 0.29 | 1.68 | 6.35 | 6 | 110.77 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | XAUUSD | 22 | 45.45 | 8.25 | 0.38 | 1.98 | 2.59 | 4 | 111.91 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | GBPJPY | 32 | 46.88 | 5.83 | 0.18 | 1.37 | 3.03 | 3 | 108.22 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | CHFJPY | 18 | 44.44 | 4.38 | 0.24 | 1.52 | 3.04 | 3 | 96.00 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | SILVER | 26 | 46.15 | 3.31 | 0.13 | 1.23 | 4.19 | 3 | 82.46 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | AUDJPY | 22 | 40.91 | 2.32 | 0.11 | 1.18 | 7.06 | 7 | 82.00 | EMA |
| T4_REBREAK_ONLY | EMA_close_gt_200 | EURJPY | 28 | 39.29 | -1.04 | -0.04 | 0.94 | 8.02 | 5 | 103.46 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | GBPJPY | 32 | 56.25 | 13.20 | 0.41 | 2.00 | 3.03 | 3 | 110.44 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | USDJPY | 29 | 55.17 | 10.98 | 0.38 | 1.88 | 4.02 | 4 | 117.17 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | XAUUSD | 23 | 47.83 | 10.24 | 0.45 | 2.22 | 2.59 | 4 | 114.48 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | CHFJPY | 16 | 37.50 | 0.41 | 0.03 | 1.05 | 4.03 | 4 | 100.19 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | AUDJPY | 20 | 40.00 | 0.18 | 0.01 | 1.01 | 6.05 | 6 | 89.65 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | SILVER | 23 | 39.13 | -1.59 | -0.07 | 0.89 | 4.19 | 3 | 80.48 | EMA |
| T4_REBREAK_ONLY | EMA_20_gt_50 | EURJPY | 24 | 37.50 | -2.58 | -0.11 | 0.83 | 8.01 | 4 | 104.83 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | XAUUSD | 15 | 53.33 | 9.48 | 0.63 | 3.01 | 1.58 | 3 | 105.07 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | USDJPY | 22 | 59.09 | 8.82 | 0.40 | 1.99 | 4.02 | 4 | 118.68 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | GBPJPY | 15 | 53.33 | 4.89 | 0.33 | 1.69 | 2.41 | 2 | 121.00 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | CHFJPY | 12 | 33.33 | 1.54 | 0.13 | 1.24 | 3.03 | 3 | 93.08 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | AUDJPY | 14 | 35.71 | -1.62 | -0.12 | 0.82 | 6.05 | 6 | 80.86 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | EURJPY | 18 | 38.89 | -2.07 | -0.11 | 0.81 | 4.51 | 5 | 100.72 | EMA |
| T4_REBREAK_ONLY | EMA_stack_20_50_200 | SILVER | 18 | 38.89 | -2.29 | -0.13 | 0.80 | 4.59 | 3 | 77.00 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | GBPJPY | 38 | 52.63 | 11.94 | 0.31 | 1.72 | 3.03 | 3 | 109.76 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | USDJPY | 39 | 46.15 | 6.28 | 0.16 | 1.33 | 9.36 | 8 | 114.38 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | CHFJPY | 22 | 45.45 | 5.39 | 0.25 | 1.52 | 3.02 | 3 | 101.23 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | XAUUSD | 30 | 40.00 | 5.02 | 0.17 | 1.36 | 3.62 | 4 | 110.00 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | AUDJPY | 31 | 41.94 | 0.81 | 0.03 | 1.05 | 6.08 | 5 | 93.94 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | SILVER | 31 | 38.71 | -1.13 | -0.04 | 0.94 | 6.29 | 4 | 82.77 | EMA |
| T4_REBREAK_ONLY | EMA20_slope_pos | EURJPY | 36 | 36.11 | -2.76 | -0.08 | 0.87 | 10.84 | 5 | 105.64 | EMA |
| T4_REBREAK_ONLY | ADX_ge_18 | XAUUSD | 30 | 43.33 | 6.02 | 0.20 | 1.47 | 3.02 | 4 | 114.37 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | GBPJPY | 26 | 50.00 | 4.68 | 0.18 | 1.40 | 4.16 | 4 | 110.96 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | AUDJPY | 22 | 50.00 | 4.54 | 0.21 | 1.43 | 4.02 | 4 | 105.86 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | CHFJPY | 18 | 44.44 | 4.38 | 0.24 | 1.52 | 4.03 | 4 | 102.61 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | USDJPY | 28 | 42.86 | 3.56 | 0.13 | 1.26 | 7.35 | 7 | 113.36 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | SILVER | 22 | 40.91 | 1.69 | 0.08 | 1.13 | 6.02 | 6 | 80.77 | ADX |
| T4_REBREAK_ONLY | ADX_ge_18 | EURJPY | 30 | 33.33 | -3.68 | -0.12 | 0.80 | 11.21 | 10 | 102.23 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | XAUUSD | 22 | 40.91 | 5.23 | 0.24 | 1.55 | 2.51 | 4 | 121.95 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | AUDJPY | 11 | 54.55 | 4.00 | 0.36 | 1.80 | 4.02 | 4 | 100.27 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | SILVER | 17 | 47.06 | 3.87 | 0.23 | 1.45 | 3.91 | 4 | 89.24 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | GBPJPY | 22 | 45.45 | 1.35 | 0.06 | 1.13 | 4.58 | 5 | 106.91 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | CHFJPY | 9 | 44.44 | 0.63 | 0.07 | 1.15 | 3.03 | 3 | 113.11 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | EURJPY | 22 | 40.91 | 0.17 | 0.01 | 1.01 | 7.18 | 8 | 102.27 | ADX |
| T4_REBREAK_ONLY | ADX_ge_22 | USDJPY | 13 | 38.46 | -0.40 | -0.03 | 0.94 | 5.43 | 7 | 121.62 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | XAUUSD | 21 | 42.86 | 6.24 | 0.30 | 1.74 | 2.51 | 4 | 123.52 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | SILVER | 8 | 62.50 | 4.33 | 0.54 | 2.83 | 1.05 | 2 | 119.38 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | CHFJPY | 8 | 50.00 | 1.64 | 0.21 | 1.51 | 2.02 | 2 | 125.25 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | AUDJPY | 4 | 25.00 | -1.02 | -0.26 | 0.66 | 2.01 | 3 | 77.75 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | USDJPY | 9 | 33.33 | -1.76 | -0.20 | 0.66 | 4.02 | 5 | 107.78 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | EURJPY | 18 | 27.78 | -4.19 | -0.23 | 0.67 | 7.70 | 9 | 87.61 | ADX |
| T4_REBREAK_ONLY | ADX_ge_25 | GBPJPY | 19 | 36.84 | -4.62 | -0.24 | 0.56 | 6.13 | 5 | 116.16 | ADX |
| T4_REBREAK_ONLY | RSI_45_75 | GBPJPY | 43 | 53.49 | 15.91 | 0.37 | 1.85 | 3.03 | 3 | 103.44 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | XAUUSD | 32 | 46.88 | 11.24 | 0.35 | 1.88 | 3.62 | 3 | 112.53 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | USDJPY | 40 | 45.00 | 7.38 | 0.18 | 1.39 | 9.36 | 8 | 112.30 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | CHFJPY | 24 | 45.83 | 5.55 | 0.23 | 1.45 | 4.03 | 4 | 95.67 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | AUDJPY | 34 | 44.12 | 3.77 | 0.11 | 1.20 | 7.09 | 6 | 93.68 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | EURJPY | 39 | 41.03 | 2.66 | 0.07 | 1.12 | 9.03 | 5 | 103.74 | RSI |
| T4_REBREAK_ONLY | RSI_45_75 | SILVER | 32 | 37.50 | -0.52 | -0.02 | 0.97 | 6.59 | 5 | 81.91 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | GBPJPY | 43 | 53.49 | 15.91 | 0.37 | 1.85 | 3.03 | 3 | 103.44 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | XAUUSD | 32 | 46.88 | 11.24 | 0.35 | 1.88 | 3.62 | 3 | 112.53 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | USDJPY | 40 | 45.00 | 7.38 | 0.18 | 1.39 | 9.36 | 8 | 112.30 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | CHFJPY | 24 | 45.83 | 5.55 | 0.23 | 1.45 | 4.03 | 4 | 95.67 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | AUDJPY | 34 | 44.12 | 3.77 | 0.11 | 1.20 | 7.09 | 6 | 93.68 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | EURJPY | 39 | 41.03 | 2.66 | 0.07 | 1.12 | 9.03 | 5 | 103.74 | RSI |
| T4_REBREAK_ONLY | RSI_50_75 | SILVER | 32 | 37.50 | -0.52 | -0.02 | 0.97 | 6.59 | 5 | 81.91 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | GBPJPY | 44 | 52.27 | 14.91 | 0.34 | 1.76 | 3.03 | 3 | 104.80 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | XAUUSD | 34 | 47.06 | 10.97 | 0.32 | 1.80 | 3.62 | 4 | 112.65 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | USDJPY | 41 | 46.34 | 8.24 | 0.20 | 1.43 | 9.36 | 8 | 113.95 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | CHFJPY | 26 | 46.15 | 7.35 | 0.28 | 1.59 | 4.03 | 4 | 99.96 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | AUDJPY | 35 | 42.86 | 2.76 | 0.08 | 1.14 | 8.10 | 7 | 91.97 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | EURJPY | 40 | 40.00 | 1.65 | 0.04 | 1.07 | 10.03 | 5 | 103.28 | RSI |
| T4_REBREAK_ONLY | RSI_gt_50 | SILVER | 33 | 39.39 | -0.22 | -0.01 | 0.99 | 6.29 | 4 | 84.88 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | GBPJPY | 43 | 53.49 | 15.91 | 0.37 | 1.85 | 3.03 | 3 | 103.44 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | XAUUSD | 32 | 46.88 | 11.24 | 0.35 | 1.88 | 3.62 | 3 | 112.53 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | USDJPY | 40 | 45.00 | 7.38 | 0.18 | 1.39 | 9.36 | 8 | 112.30 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | CHFJPY | 24 | 45.83 | 5.55 | 0.23 | 1.45 | 4.03 | 4 | 95.67 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | AUDJPY | 34 | 44.12 | 3.77 | 0.11 | 1.20 | 7.09 | 6 | 93.68 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | EURJPY | 39 | 41.03 | 2.66 | 0.07 | 1.12 | 9.03 | 5 | 103.74 | RSI |
| T4_REBREAK_ONLY | RSI_lt_75 | SILVER | 32 | 37.50 | -0.52 | -0.02 | 0.97 | 6.59 | 5 | 81.91 | RSI |
| T4_REBREAK_ONLY | Donchian20_break | GBPJPY | 39 | 53.85 | 13.93 | 0.36 | 1.84 | 3.03 | 3 | 111.13 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | XAUUSD | 28 | 42.86 | 5.05 | 0.18 | 1.43 | 2.59 | 4 | 122.89 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | CHFJPY | 18 | 44.44 | 3.46 | 0.19 | 1.41 | 3.02 | 3 | 106.22 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | USDJPY | 36 | 44.44 | 2.74 | 0.08 | 1.15 | 9.36 | 8 | 113.08 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | AUDJPY | 28 | 39.29 | -1.24 | -0.04 | 0.93 | 8.10 | 7 | 92.79 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | EURJPY | 34 | 35.29 | -2.93 | -0.09 | 0.86 | 11.01 | 9 | 106.00 | Donchian |
| T4_REBREAK_ONLY | Donchian20_break | SILVER | 25 | 36.00 | -3.77 | -0.15 | 0.76 | 6.02 | 5 | 85.12 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | USDJPY | 15 | 66.67 | 6.53 | 0.44 | 2.32 | 3.02 | 3 | 140.13 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | GBPJPY | 14 | 57.14 | 4.62 | 0.33 | 1.90 | 2.06 | 2 | 133.93 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | EURJPY | 14 | 42.86 | 0.93 | 0.07 | 1.12 | 4.16 | 4 | 105.50 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | CHFJPY | 9 | 33.33 | 0.12 | 0.01 | 1.03 | 3.23 | 4 | 126.67 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | XAUUSD | 16 | 37.50 | -0.14 | -0.01 | 0.98 | 2.31 | 3 | 127.12 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | SILVER | 13 | 38.46 | -1.66 | -0.13 | 0.80 | 2.88 | 2 | 92.38 | Donchian |
| T4_REBREAK_ONLY | Donchian55_break | AUDJPY | 7 | 28.57 | -1.70 | -0.24 | 0.66 | 5.04 | 5 | 97.71 | Donchian |
| T4_REBREAK_ONLY | BB_pos_60_110 | GBPJPY | 34 | 52.94 | 12.16 | 0.36 | 1.83 | 3.30 | 3 | 106.74 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | USDJPY | 29 | 48.28 | 11.78 | 0.41 | 1.98 | 5.43 | 6 | 111.00 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | CHFJPY | 25 | 48.00 | 8.37 | 0.33 | 1.73 | 4.03 | 4 | 102.12 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | XAUUSD | 27 | 40.74 | 6.74 | 0.25 | 1.57 | 2.61 | 4 | 117.67 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | AUDJPY | 31 | 45.16 | 5.10 | 0.16 | 1.30 | 7.09 | 6 | 88.87 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | EURJPY | 31 | 38.71 | 0.85 | 0.03 | 1.05 | 9.54 | 7 | 99.32 | Bollinger |
| T4_REBREAK_ONLY | BB_pos_60_110 | SILVER | 22 | 40.91 | 0.66 | 0.03 | 1.05 | 3.93 | 3 | 84.00 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | GBPJPY | 39 | 56.41 | 16.92 | 0.43 | 2.08 | 4.04 | 4 | 106.36 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | XAUUSD | 31 | 48.39 | 11.00 | 0.35 | 1.94 | 2.61 | 4 | 118.61 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | CHFJPY | 22 | 45.45 | 6.34 | 0.29 | 1.61 | 4.03 | 4 | 101.41 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | AUDJPY | 33 | 45.45 | 4.79 | 0.15 | 1.27 | 6.07 | 6 | 95.73 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | USDJPY | 38 | 42.11 | 3.81 | 0.10 | 1.20 | 9.36 | 8 | 116.16 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | EURJPY | 35 | 40.00 | 0.13 | 0.00 | 1.01 | 9.02 | 5 | 107.74 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_3ATR | SILVER | 24 | 37.50 | -2.62 | -0.11 | 0.82 | 4.96 | 5 | 91.50 | Bollinger |
| T4_REBREAK_ONLY | BB_width_ge_4ATR | GBPJPY | 28 | 57.14 | 10.03 | 0.36 | 1.95 | 3.03 | 3 | 126.54 | Bollinger |

## 出力

- `trades_enriched.csv`
- `summary_filters.csv`
- `summary_by_symbol.csv`
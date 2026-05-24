# TrendBreakV1 騙し回避フィルタ 前後比較 2015-2024

## 結論

- 総利益最大: `baseline` / 191.53R / 勝率 36.88% / PF 1.624
- PF最大: `body60_plus_early1` / PF 1.788 / 169.50R
- DD最小: `body60_plus_early1` / Max DD 9.39R / 169.50R

## 全体比較

| rule_name | trades | win_rate | total_r_after_cost | avg_r_after_cost | pf_after_cost | max_dd_after_cost_r | early_exit_rate | delta_total_r_after_cost | delta_win_rate | delta_max_dd_after_cost_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 461 | 36.88 | 191.53 | 0.42 | 1.62 | 17.95 | 0.00 | 0.00 | 0.00 | 0.00 |
| body60_filter | 377 | 38.20 | 176.27 | 0.47 | 1.72 | 11.70 | 0.00 | -15.26 | 1.32 | -6.25 |
| early_back_inside_1 | 461 | 32.97 | 181.72 | 0.39 | 1.69 | 11.67 | 20.17 | -9.81 | -3.90 | -6.29 |
| body60_plus_early1 | 377 | 34.75 | 169.50 | 0.45 | 1.79 | 9.39 | 18.30 | -22.03 | -2.13 | -8.56 |

## 通貨別比較

| symbol | rule_name | trades | win_rate | total_r_after_cost | pf_after_cost | max_dd_after_cost_r | early_exit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | baseline | 75 | 44.00 | 53.20 | 2.21 | 6.19 | 0.00 |
| USDJPY | baseline | 64 | 37.50 | 29.91 | 1.72 | 9.37 | 0.00 |
| EURJPY | baseline | 55 | 30.91 | 11.42 | 1.29 | 9.39 | 0.00 |
| GBPJPY | baseline | 59 | 42.37 | 39.11 | 2.11 | 6.16 | 0.00 |
| CHFJPY | baseline | 64 | 35.94 | 24.35 | 1.56 | 9.37 | 0.00 |
| AUDJPY | baseline | 80 | 25.00 | -3.08 | 0.95 | 17.95 | 0.00 |
| SILVER | baseline | 64 | 43.75 | 36.62 | 1.86 | 6.41 | 0.00 |
| XAUUSD | body60_filter | 65 | 46.15 | 51.59 | 2.41 | 5.18 | 0.00 |
| USDJPY | body60_filter | 53 | 39.62 | 29.26 | 1.89 | 7.29 | 0.00 |
| EURJPY | body60_filter | 49 | 34.69 | 17.55 | 1.53 | 9.39 | 0.00 |
| GBPJPY | body60_filter | 50 | 42.00 | 32.37 | 2.08 | 5.28 | 0.00 |
| CHFJPY | body60_filter | 51 | 35.29 | 18.10 | 1.52 | 7.43 | 0.00 |
| AUDJPY | body60_filter | 55 | 23.64 | -5.13 | 0.88 | 11.70 | 0.00 |
| SILVER | body60_filter | 54 | 44.44 | 32.53 | 1.92 | 5.20 | 0.00 |
| XAUUSD | early_back_inside_1 | 75 | 37.33 | 42.96 | 2.09 | 5.58 | 18.67 |
| USDJPY | early_back_inside_1 | 64 | 35.94 | 32.27 | 1.90 | 9.37 | 17.19 |
| EURJPY | early_back_inside_1 | 55 | 30.91 | 15.74 | 1.45 | 9.39 | 14.55 |
| GBPJPY | early_back_inside_1 | 59 | 35.59 | 34.66 | 2.25 | 5.39 | 27.12 |
| CHFJPY | early_back_inside_1 | 64 | 31.25 | 21.19 | 1.56 | 9.15 | 20.31 |
| AUDJPY | early_back_inside_1 | 80 | 22.50 | 4.17 | 1.09 | 11.67 | 26.25 |
| SILVER | early_back_inside_1 | 64 | 39.06 | 30.74 | 1.77 | 6.83 | 15.62 |
| XAUUSD | body60_plus_early1 | 65 | 40.00 | 42.75 | 2.27 | 6.12 | 16.92 |
| USDJPY | body60_plus_early1 | 53 | 39.62 | 33.65 | 2.18 | 7.29 | 15.09 |
| EURJPY | body60_plus_early1 | 49 | 34.69 | 21.11 | 1.72 | 9.39 | 14.29 |
| GBPJPY | body60_plus_early1 | 50 | 34.00 | 27.05 | 2.15 | 6.64 | 30.00 |
| CHFJPY | body60_plus_early1 | 51 | 31.37 | 15.13 | 1.47 | 7.74 | 15.69 |
| AUDJPY | body60_plus_early1 | 55 | 21.82 | 0.30 | 1.01 | 7.49 | 23.64 |
| SILVER | body60_plus_early1 | 54 | 40.74 | 29.51 | 1.90 | 4.82 | 12.96 |

## ルール定義

- `baseline`: 現行TrendBreakV1 HYBRID。
- `body60_filter`: シグナル足の実体が足全体の60%以上のときだけ入る。
- `early_back_inside_1`: 通常通り入るが、エントリー後1本以内に終値がブレイク水準内へ戻ったら次足始値で撤退。
- `body60_plus_early1`: 上記2つを同時に適用。

## 注意

この検証はPython上の再現バックテストです。TradingView/Pineの約定モデルやブローカー実約定とは完全一致しません。
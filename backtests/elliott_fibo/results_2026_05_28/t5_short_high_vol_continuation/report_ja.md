# H4 T5 ショート: 高ボラ下落継続アイディア検証

## 結論

- 鏡写しのショート条件は明確に負け。
- ただし `ADX高め`, `BB幅7〜10ATR`, `rebreak`, `MACD slope3>0`, `GBPJPY/AUDJPY` にはプラス断片が残る。
- OOSはまだ弱い。2025-2026で発生ゼロ、または少数マイナスの候補が多いため、採用ではなく研究継続候補。

## 母集団

- Source trades: 202
- Source file: `short_t5_broad_trades_2015_2026.csv`

## 名前付き候補

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | research_trades | research_total_r | oos_trades | oos_total_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Broad short T5 | 202 | 32.67 | -37.49 | -0.19 | 0.68 | 43.57 | 187 | -27.54 | 15 | -9.95 | 逆V候補後T5ショート全体。比較用。 |
| Mirror practical loser | 27 | 18.52 | -12.88 | -0.48 | 0.39 | 13.71 | 23 | -11.20 | 4 | -1.68 | 前回負けた鏡写し条件。比較用。 |
| HV core rebreak ADX25 BBW7-10 BBpos0-25 | 11 | 54.55 | 7.69 | 0.70 | 4.58 | 1.80 | 11 | 7.69 | 0 | 0.00 | 高ボラ下落継続の中心仮説。OOS発生数も確認する。 |
| HV ADX25 BBW7-10 any trigger | 16 | 56.25 | 8.10 | 0.51 | 2.95 | 2.65 | 14 | 8.95 | 2 | -0.85 | rebreak限定を外し、高ボラ・トレンド強度だけを見る。 |
| HV rebreak ADX25 BBW>=7 BBpos0-25 | 12 | 50.00 | 6.68 | 0.56 | 3.12 | 1.80 | 12 | 6.68 | 0 | 0.00 | BB幅上限10ATRを外す。極端な荒れ相場が混ざるか確認。 |
| HV MACD-turn rebreak | 29 | 48.28 | 9.06 | 0.31 | 1.74 | 5.70 | 28 | 10.06 | 1 | -1.00 | 売りが伸びきった直後ではなく、MACDが下げ止まり方向のrebreakだけ。 |
| HV GBP/AUD ADX25 | 25 | 48.00 | 11.45 | 0.46 | 2.45 | 4.21 | 22 | 12.46 | 3 | -1.01 | 通貨特性を優先。GBPJPY/AUDJPYの強いトレンド化だけを見る。 |
| HV GBP/AUD ADX25 rebreak | 20 | 45.00 | 8.07 | 0.40 | 2.14 | 3.60 | 19 | 8.61 | 1 | -0.54 | 通貨特性 + rebreak。シンプルな実戦候補。 |
| HV GBP/AUD ATRpct80 rebreak | 17 | 52.94 | 9.11 | 0.54 | 2.67 | 3.06 | 17 | 9.11 | 0 | 0.00 | 高ボラをBB幅ではなくATRパーセンタイルで見る。 |

## 推奨候補の年別

| year | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 1 | 0.00 | -0.22 | -0.22 | 0.00 | 0.00 | 1 |
| 2016 | 4 | 75.00 | 4.54 | 1.14 | 164.41 | 0.03 | 1 |
| 2017 | 1 | 100.00 | 1.96 | 1.96 | inf | 0.00 | 0 |
| 2018 | 3 | 66.67 | 3.21 | 1.07 | 32.90 | 0.00 | 1 |
| 2022 | 1 | 0.00 | -0.79 | -0.79 | 0.00 | 0.00 | 1 |
| 2024 | 1 | 0.00 | -1.00 | -1.00 | 0.00 | 0.00 | 1 |

## グリッド上位

| symbol | trigger | adx | bb_width | bb_pos | macd | atr | recovery | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_total_r | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gbp_aud | any | 30_40 | any | any | any | any | any | 10 | 70.00 | 11.67 | 1.17 | 21.79 | 0.39 | 0 | 0.00 | 20.42 |
| gbp_aud | not_combo | 30_40 | any | any | any | any | any | 8 | 75.00 | 9.80 | 1.23 | 24.11 | 0.26 | 0 | 0.00 | 18.88 |
| gbp_aud | any | ge25 | any | any | any | any | any | 25 | 48.00 | 11.45 | 0.46 | 2.45 | 4.21 | 3 | -1.01 | 15.35 |
| gbp_only | any | ge25 | any | any | any | any | any | 13 | 61.54 | 8.30 | 0.64 | 3.71 | 1.74 | 2 | -0.48 | 14.85 |
| gbp_only | any | any | any | any | any | any | gt16 | 14 | 57.14 | 8.56 | 0.61 | 3.08 | 2.02 | 2 | -0.48 | 14.29 |
| all | any | ge25 | 7_10 | 0_025 | any | any | any | 13 | 53.85 | 8.69 | 0.67 | 3.75 | 1.80 | 0 | 0.00 | 13.42 |
| all | rebreak | ge25 | 7_10 | 0_025 | any | any | any | 11 | 54.55 | 7.69 | 0.70 | 4.58 | 1.80 | 0 | 0.00 | 13.40 |
| gbp_aud | not_combo | ge25 | any | any | any | any | any | 23 | 47.83 | 9.58 | 0.42 | 2.24 | 4.07 | 3 | -1.01 | 13.09 |
| all | any | ge25 | 7_10 | any | any | any | any | 16 | 56.25 | 8.10 | 0.51 | 2.95 | 2.65 | 2 | -0.85 | 13.05 |
| gbp_aud | rebreak | any | any | any | neg008_neg005 | any | any | 8 | 75.00 | 6.59 | 0.82 | 4.27 | 1.01 | 0 | 0.00 | 12.78 |
| all | any | any | 7_10 | 0_025 | any | any | any | 14 | 50.00 | 7.68 | 0.55 | 2.85 | 2.80 | 1 | -1.00 | 12.72 |
| all | rebreak | ge25 | 7_10 | any | any | any | any | 13 | 53.85 | 6.95 | 0.53 | 3.20 | 2.80 | 1 | -1.00 | 12.26 |
| gbp_only | any | any | any | le0 | any | any | gt16 | 8 | 62.50 | 5.52 | 0.69 | 3.48 | 1.01 | 1 | 0.15 | 12.25 |
| gbp_only | not_combo | any | any | le0 | any | any | gt16 | 8 | 62.50 | 5.52 | 0.69 | 3.48 | 1.01 | 1 | 0.15 | 12.25 |
| gbp_aud | any | ge25 | any | any | gt_neg001 | any | any | 14 | 50.00 | 8.59 | 0.61 | 2.99 | 2.19 | 0 | 0.00 | 12.21 |
| gbp_aud | any | any | any | any | neg008_neg005 | any | any | 10 | 70.00 | 6.12 | 0.61 | 3.31 | 1.48 | 2 | -0.48 | 12.19 |
| gbp_aud | not_combo | any | any | any | neg008_neg005 | any | any | 10 | 70.00 | 6.12 | 0.61 | 3.31 | 1.48 | 2 | -0.48 | 12.19 |
| gbp_only | any | ge25 | any | 0_025 | any | any | any | 9 | 55.56 | 6.04 | 0.67 | 3.09 | 1.89 | 1 | -0.63 | 12.10 |
| all | rebreak | any | 7_10 | 0_025 | any | any | any | 12 | 50.00 | 6.69 | 0.56 | 3.12 | 2.80 | 1 | -1.00 | 12.03 |
| gbp_aud | rebreak | any | any | any | any | pct_ge80 | any | 17 | 52.94 | 9.11 | 0.54 | 2.67 | 3.06 | 0 | 0.00 | 11.85 |
| gbp_only | any | any | any | any | neg008_neg005 | any | any | 9 | 66.67 | 5.76 | 0.64 | 3.18 | 1.48 | 2 | -0.48 | 11.83 |
| gbp_only | not_combo | any | any | any | neg008_neg005 | any | any | 9 | 66.67 | 5.76 | 0.64 | 3.18 | 1.48 | 2 | -0.48 | 11.83 |
| gbp_only | not_combo | ge25 | any | any | any | any | any | 12 | 58.33 | 6.29 | 0.52 | 3.06 | 1.74 | 2 | -0.48 | 11.63 |
| gbp_aud | not_combo | any | any | any | any | any | gt16 | 24 | 45.83 | 8.36 | 0.35 | 1.95 | 2.26 | 3 | -1.01 | 11.59 |
| gbp_aud | rebreak | ge25 | any | any | any | any | any | 20 | 45.00 | 8.07 | 0.40 | 2.14 | 3.60 | 1 | -0.54 | 11.50 |
| gbp_only | not_combo | any | any | any | any | any | gt16 | 13 | 53.85 | 6.56 | 0.50 | 2.59 | 2.02 | 2 | -0.48 | 11.27 |
| all | rebreak | any | any | any | gt0 | any | any | 29 | 48.28 | 9.06 | 0.31 | 1.74 | 5.70 | 1 | -1.00 | 11.22 |
| gbp_aud | any | ge25 | any | 0_025 | any | any | any | 19 | 42.11 | 7.73 | 0.41 | 2.08 | 3.85 | 1 | -0.63 | 11.08 |
| all | any | ge25 | ge7 | any | any | any | any | 18 | 55.56 | 7.13 | 0.40 | 2.38 | 2.65 | 2 | -0.85 | 10.96 |
| gbp_aud | any | any | any | any | any | any | gt16 | 28 | 42.86 | 8.21 | 0.29 | 1.75 | 2.40 | 3 | -1.01 | 10.94 |
| all | rebreak | 30_40 | any | any | any | any | any | 20 | 45.00 | 7.94 | 0.40 | 2.05 | 5.60 | 3 | -2.32 | 10.85 |
| all | any | any | 7_10 | any | any | any | any | 17 | 52.94 | 7.09 | 0.42 | 2.38 | 3.65 | 3 | -1.85 | 10.83 |
| all | any | ge25 | ge7 | 0_025 | any | any | any | 15 | 53.33 | 7.72 | 0.51 | 2.86 | 1.80 | 0 | 0.00 | 10.79 |
| gbp_aud | any | any | any | any | any | pct_ge80 | any | 19 | 47.37 | 7.48 | 0.39 | 2.05 | 3.69 | 1 | -0.63 | 10.76 |
| gbp_aud | not_combo | any | any | any | any | pct_ge80 | any | 19 | 47.37 | 7.48 | 0.39 | 2.05 | 3.69 | 1 | -0.63 | 10.76 |
| gbp_only | rebreak | any | any | any | any | any | gt16 | 9 | 55.56 | 6.05 | 0.67 | 3.44 | 1.01 | 0 | 0.00 | 10.65 |
| all | any | any | ge7 | 0_025 | any | any | any | 16 | 50.00 | 6.72 | 0.42 | 2.30 | 2.80 | 1 | -1.00 | 10.56 |
| gbp_aud | any | any | any | any | any | any | gt24 | 14 | 50.00 | 6.06 | 0.43 | 2.71 | 3.07 | 3 | -1.01 | 10.33 |
| gbp_aud | not_combo | any | any | any | any | any | gt24 | 14 | 50.00 | 6.06 | 0.43 | 2.71 | 3.07 | 3 | -1.01 | 10.33 |
| all | any | any | 7_10 | 0_025 | gt0 | any | any | 10 | 50.00 | 6.33 | 0.63 | 3.16 | 1.80 | 0 | 0.00 | 10.29 |
| all | any | ge25 | 7_10 | 0_025 | gt0 | any | any | 10 | 50.00 | 6.33 | 0.63 | 3.16 | 1.80 | 0 | 0.00 | 10.29 |
| all | any | ge25 | 7_10 | 0_025 | gt_neg001 | any | any | 10 | 50.00 | 6.33 | 0.63 | 3.16 | 1.80 | 0 | 0.00 | 10.29 |
| all | rebreak | any | any | any | gt0 | any | gt16 | 19 | 52.63 | 7.17 | 0.38 | 2.15 | 4.69 | 1 | -1.00 | 10.27 |
| all | rebreak | ge25 | ge7 | 0_025 | any | any | any | 12 | 50.00 | 6.68 | 0.56 | 3.12 | 1.80 | 0 | 0.00 | 10.23 |
| all | not_combo | ge25 | 7_10 | 0_025 | any | any | any | 12 | 50.00 | 6.68 | 0.56 | 3.12 | 1.80 | 0 | 0.00 | 10.23 |
| gbp_aud | any | ge25 | any | any | any | any | gt16 | 16 | 43.75 | 6.38 | 0.40 | 2.36 | 3.21 | 3 | -1.01 | 10.10 |
| all | rebreak | any | 7_10 | 0_025 | gt0 | any | any | 8 | 50.00 | 5.33 | 0.67 | 3.77 | 1.80 | 0 | 0.00 | 10.07 |
| all | rebreak | ge25 | 7_10 | 0_025 | gt0 | any | any | 8 | 50.00 | 5.33 | 0.67 | 3.77 | 1.80 | 0 | 0.00 | 10.07 |
| all | rebreak | ge25 | 7_10 | 0_025 | gt_neg001 | any | any | 8 | 50.00 | 5.33 | 0.67 | 3.77 | 1.80 | 0 | 0.00 | 10.07 |
| all | not_combo | ge25 | 7_10 | any | any | any | any | 15 | 53.33 | 6.09 | 0.41 | 2.47 | 2.65 | 2 | -0.85 | 10.06 |
| all | rebreak | ge25 | ge7 | any | any | any | any | 14 | 50.00 | 5.95 | 0.42 | 2.43 | 2.80 | 1 | -1.00 | 9.94 |
| all | any | any | any | 0_025 | gt0 | any | gt16 | 28 | 53.57 | 9.07 | 0.32 | 1.97 | 3.83 | 0 | 0.00 | 9.89 |
| all | rebreak | any | any | any | neg008_neg005 | any | any | 17 | 64.71 | 6.49 | 0.38 | 2.08 | 3.02 | 2 | -2.01 | 9.88 |
| all | rebreak | any | 7_10 | any | any | any | any | 14 | 50.00 | 5.95 | 0.42 | 2.43 | 3.80 | 2 | -2.01 | 9.74 |
| gbp_aud | not_combo | ge25 | any | any | gt_neg001 | any | any | 12 | 50.00 | 6.72 | 0.56 | 2.61 | 2.06 | 0 | 0.00 | 9.73 |
| all | rebreak | any | ge7 | 0_025 | any | any | any | 13 | 46.15 | 5.68 | 0.44 | 2.37 | 2.80 | 1 | -1.00 | 9.68 |
| all | not_combo | any | 7_10 | 0_025 | any | any | any | 13 | 46.15 | 5.68 | 0.44 | 2.37 | 2.80 | 1 | -1.00 | 9.67 |
| all | rebreak | any | any | le0 | any | pct_ge80 | any | 18 | 61.11 | 7.43 | 0.41 | 2.58 | 2.03 | 0 | 0.00 | 9.66 |
| all | any | 30_40 | any | any | any | any | any | 28 | 42.86 | 7.76 | 0.28 | 1.66 | 5.74 | 3 | -2.32 | 9.66 |
| all | any | any | 7_10 | 0_025 | gt_neg001 | any | any | 11 | 45.45 | 5.33 | 0.48 | 2.35 | 2.80 | 1 | -1.00 | 9.54 |

## 実戦メモ

- `BB幅<=4ATR` のようなロング版の安全条件は、ショートではむしろ優位性を消していた。
- 下側BBに張り付いてMACDも悪い場面は売り遅れになりやすい。
- 高ボラ継続ショートとして使うなら、まずはデモ/研究で `rebreak + ADX>=25 + BB幅7〜10ATR` を監視する。
- OOSが不足しているため、本番採用候補ではなくフォワード観察候補。

## 出力CSV

- `named_candidates.csv`
- `grid_candidates.csv`
- `recommended_trades.csv`
- `recommended_by_year.csv`
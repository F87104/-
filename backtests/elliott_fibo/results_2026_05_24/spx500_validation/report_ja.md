# SPX500 検証レポート

- データ: `/Users/asamifujita/Documents/Codex/2026-05-21/fx-ai/F87104_test/SPX500 2014-2026`
- H1行数: 67,862
- H4行数: 17,977
- 期間: 2014-11-19 01:00:00 〜 2026-05-22 20:00:00
- コスト仮定: spread=2.0pt, slippage=1.0pt
- Research: 2015-2024 / OOS: 2025-2026

## H4 T5

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_total_r | oos_avg_r | oos_pf | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 Broad T5 universe | 62 | 53.23 | 10.42 | 0.17 | 1.36 | 7.71 | 10 | -1.91 | -0.19 | 0.73 | V候補後にstagnation/rebreak。追加フィルタなし |
| 01 Research practical strict | 4 | 25.00 | -1.92 | -0.48 | 0.38 | 2.05 | 0 | 0.00 | 0.00 |  | BB0.60-0.95, recovery<=16, MACD>0, BB幅<=4ATR |
| 02 Pine default signal set | 8 | 50.00 | 1.85 | 0.23 | 1.45 | 1.07 | 1 | -1.01 | -1.01 | 0.00 | Pine現行デフォルトに近い候補。FULL/HALF/SKIP前 |
| 03 Pine default operation weighted | 5 | 20.00 | -1.92 | -0.38 | 0.38 | 1.52 | 1 | -0.50 | -0.50 | 0.00 | FULL=1R, HALF=0.5Rとして口座R換算 |
| Pine default cost x1 | 5 | 20.00 | -2.95 | -0.59 | 0.29 | 2.03 | 1 | -1.01 | -1.01 | 0.00 | same trades, stressed execution |
| Pine default cost x2 | 5 | 20.00 | -3.15 | -0.63 | 0.27 | 2.06 | 1 | -1.02 | -1.02 | 0.00 | same trades, stressed execution |
| Pine default cost x3 | 5 | 20.00 | -3.35 | -0.67 | 0.24 | 2.21 | 1 | -1.03 | -1.03 | 0.00 | same trades, stressed execution |
| Pine default extra -0.10R | 5 | 20.00 | -3.45 | -0.69 | 0.24 | 2.30 | 1 | -1.11 | -1.11 | 0.00 | same trades, stressed execution |
| Pine default extra -0.20R | 5 | 20.00 | -3.95 | -0.79 | 0.20 | 2.70 | 1 | -1.21 | -1.21 | 0.00 | same trades, stressed execution |

## H4 T5 Pine default 年別

| year | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 2 | 0.00 | -1.59 | -0.80 | 0.00 | 1.07 | 2 |
| 2017 | 1 | 100.00 | 1.20 | 1.20 | inf | 0.00 | 0 |
| 2020 | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 | 1 |
| 2025 | 1 | 0.00 | -0.50 | -0.50 | 0.00 | 0.00 | 1 |

## TrendBreak 参考検証

SPX500はTrendBreakV1 HYBRIDの専用プリセット未確定のため、以下は最適化前の参考値です。

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_total_r | oos_avg_r | oos_pf | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TrendBreak manual_default_H1_mid_session | 220 | 25.00 | -64.88 | -0.29 | 0.70 | 73.66 | 22 | -9.15 | -0.42 | 0.56 | SPX500専用最適化なしの参考値 |
| TrendBreak index_conservative_H1_mid | 75 | 32.00 | 2.48 | 0.03 | 1.04 | 13.86 | 6 | 1.20 | 0.20 | 1.26 | SPX500専用最適化なしの参考値 |
| TrendBreak index_conservative_H1_any | 80 | 33.75 | 8.29 | 0.10 | 1.12 | 14.37 | 7 | 4.09 | 0.58 | 1.89 | SPX500専用最適化なしの参考値 |
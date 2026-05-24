# NAS100 / US100 H4 T5 検証

- データ: `/Users/asamifujita/Documents/Codex/2026-05-21/fx-ai/F87104_test` の `NAS100_H1_2014.csv` 〜 `NAS100_H1_2026.csv`
- H1行数: 67,391
- H4行数: 17,945
- 期間: 2014-11-19 00:00:00 〜 2026-05-22 20:00:00
- コスト仮定: spread=2.0pt, slippage=1.0pt
- Research: 2015-2024 / OOS: 2025-2026

## Summary

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_total_r | oos_avg_r | oos_pf | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 Broad T5 universe | 75 | 49.33 | 17.97 | 0.24 | 1.49 | 6.02 | 8 | -0.30 | -0.04 | 0.94 | V候補後にstagnation/rebreak。追加フィルタなし |
| 01 Research practical strict | 10 | 50.00 | 4.90 | 0.49 | 1.97 | 2.01 | 1 | -1.00 | -1.00 | 0.00 | BB0.60-0.95, recovery<=16, MACD>0, BB幅<=4ATR |
| 02 Pine default signal set | 17 | 58.82 | 12.00 | 0.71 | 2.91 | 3.01 | 1 | -1.00 | -1.00 | 0.00 | Pine現行デフォルトに近い候補。FULL/HALF/SKIP前 |
| 03 Pine default operation weighted | 11 | 72.73 | 8.90 | 0.81 | 3.96 | 2.01 | 1 | -1.00 | -1.00 | 0.00 | FULL=1R, HALF=0.5Rとして口座R換算 |
| Pine default cost x1 | 11 | 72.73 | 12.87 | 1.17 | 5.28 | 2.01 | 1 | -1.00 | -1.00 | 0.00 | same trades, stressed execution |
| Pine default cost x2 | 11 | 72.73 | 12.75 | 1.16 | 5.22 | 2.01 | 1 | -1.01 | -1.01 | 0.00 | same trades, stressed execution |
| Pine default cost x3 | 11 | 72.73 | 12.64 | 1.15 | 5.17 | 2.02 | 1 | -1.01 | -1.01 | 0.00 | same trades, stressed execution |
| Pine default extra -0.10R | 11 | 72.73 | 11.77 | 1.07 | 4.56 | 2.21 | 1 | -1.10 | -1.10 | 0.00 | same trades, stressed execution |
| Pine default extra -0.20R | 11 | 72.73 | 10.67 | 0.97 | 3.96 | 2.41 | 1 | -1.20 | -1.20 | 0.00 | same trades, stressed execution |

## Pine default operation breakdown

| operation | trades | win_rate | raw_total_r | account_total_r | avg_raw_r |
| --- | --- | --- | --- | --- | --- |
| FULL | 7 | 57.14 | 4.93 | 4.93 | 0.70 |
| HALF | 4 | 100.00 | 7.94 | 3.97 | 1.99 |
| SKIP | 6 | 33.33 | -0.87 | 0.00 | -0.15 |

## Pine default by year

| year | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 1 | 100.00 | 0.99 | 0.99 | inf | 0.00 | 0 |
| 2017 | 1 | 100.00 | 0.99 | 0.99 | inf | 0.00 | 0 |
| 2018 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 | 0 |
| 2019 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 | 0 |
| 2020 | 3 | 66.67 | 0.99 | 0.33 | 1.98 | 1.00 | 1 |
| 2022 | 1 | 0.00 | -1.00 | -1.00 | 0.00 | 0.00 | 1 |
| 2023 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 | 0 |
| 2024 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| 2026 | 1 | 0.00 | -1.00 | -1.00 | 0.00 | 0.00 | 1 |

## Interpretation

- US100/NAS100は値幅が大きいため、H4 T5の形は出るが、通貨ペアとは別枠で評価する必要がある。
- `03 Pine default operation weighted` が、通常ロット/半ロット運用まで含めた実戦寄りの見方。
- OOSの取引数が少ない場合は、結論を急がずフォワード観察対象にする。
- 実コストはブローカー差が大きいため、x2/x3ストレスでも崩れないかを必ず確認する。
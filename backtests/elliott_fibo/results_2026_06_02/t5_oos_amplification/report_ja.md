# T5 OOS Amplification Check 2026-06-02

## 目的

2025-2026の真のOOSが4件しかない問題に対して、過去各年を疑似OOSとして扱い、固定ルールが複数年で崩れないかを確認した。

重要: これは未来データを増やす検証ではない。真のOOS不足を補助するための年別ロバスト性チェック。

## 固定ルール別サマリー

| rule_name                   | rule_desc                                                                      | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | pseudo_2018_2024_trades | pseudo_2018_2024_total_r | pseudo_2018_2024_pf | true_oos_2025_2026_trades | true_oos_2025_2026_total_r | active_years | positive_years | positive_year_rate | worst_year_total_r |
| --------------------------- | ------------------------------------------------------------------------------ | ---------- | ------------ | ----------- | --------- | ------ | ------------ | ----------------------- | ------------------------ | ------------------- | ------------------------- | -------------------------- | ------------ | -------------- | ------------------ | ------------------ |
| T5_MORE_TRADES_ADX30        | BB 0.75-1.00 / recovery<=16 / MACD>0 / BB width<=4ATR / ADX<=30 / all triggers | 27         | 77.778       | 35.321      | 1.308     | 8.712  | 2.029        | 18                      | 22.590                   | 7.407               | 3                         | 3.865                      | 11           | 10             | 90.909             | -1.054             |
| T5_CORE_STRICT_BEST         | BB 0.75-1.00 / recovery<=16 / MACD>0.03 / BB width<=4ATR / all triggers        | 20         | 80.000       | 26.105      | 1.305     | 11.504 | 1.007        | 12                      | 13.464                   | 6.418               | 4                         | 4.718                      | 11           | 10             | 90.909             | -0.022             |
| T5_SAFE_LIVE_GUARD          | BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard     | 20         | 80.000       | 25.491      | 1.275     | 9.256  | 1.054        | 9                       | 9.917                    | 5.877               | 4                         | 4.718                      | 11           | 10             | 90.909             | -0.022             |
| T5_WIDTH5_GUARD             | BB 0.75-0.95 / recovery<=20 / MACD>0 / BB width<=5ATR / weak rebreak guard     | 32         | 68.750       | 32.088      | 1.003     | 4.818  | 3.348        | 15                      | 18.838                   | 7.200               | 5                         | 6.707                      | 12           | 10             | 83.333             | -1.081             |
| T5_CURRENT_STRICT_PRACTICAL | BB 0.60-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard     | 23         | 69.565       | 22.351      | 0.972     | 4.589  | 2.152        | 11                      | 7.876                    | 2.933               | 4                         | 4.718                      | 11           | 9              | 81.818             | -1.032             |

## 最上位ルールの年別成績

- Rule: `T5_MORE_TRADES_ADX30`

| rule_name            | year | trades | win_rate | total_r | avg_r  | pf      | max_dd_r | max_losing_streak |
| -------------------- | ---- | ------ | -------- | ------- | ------ | ------- | -------- | ----------------- |
| T5_MORE_TRADES_ADX30 | 2015 | 1      | 0.000    | -1.054  | -1.054 | 0.000   | 0.000    | 1                 |
| T5_MORE_TRADES_ADX30 | 2016 | 4      | 100.000  | 7.947   | 1.987  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2017 | 1      | 100.000  | 1.974   | 1.974  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2018 | 3      | 66.667   | 4.283   | 1.428  | 194.752 | 0.022    | 1                 |
| T5_MORE_TRADES_ADX30 | 2019 | 1      | 100.000  | 1.979   | 1.979  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2020 | 5      | 60.000   | 4.429   | 0.886  | 4.003   | 1.023    | 1                 |
| T5_MORE_TRADES_ADX30 | 2021 | 3      | 100.000  | 5.954   | 1.985  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2022 | 1      | 100.000  | 1.993   | 1.993  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2024 | 5      | 60.000   | 3.952   | 0.790  | 2.948   | 2.029    | 2                 |
| T5_MORE_TRADES_ADX30 | 2025 | 2      | 100.000  | 3.310   | 1.655  | inf     | 0.000    | 0                 |
| T5_MORE_TRADES_ADX30 | 2026 | 1      | 100.000  | 0.554   | 0.554  | inf     | 0.000    | 0                 |

## 読み方

- `true_oos_2025_2026_trades` は本当の未来扱い。ここは時間が進まない限り自然には増えない。
- `pseudo_2018_2024_trades` は固定条件を過去の各年へ当てた疑似OOS件数。
- `positive_year_rate` が高いほど、一部の年だけに依存していない可能性が高い。
- それでも最終判断にはTradingView照合とフォワード記録が必要。

## 出力

- `fixed_rules_summary.csv`
- `fixed_rules_by_year.csv`
- `<rule_name>_trades.csv`
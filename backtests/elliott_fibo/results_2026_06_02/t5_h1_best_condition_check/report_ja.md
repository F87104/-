# T5 H1 Best Condition Check 2026-06-02

## 目的

H4で強かった `BB 0.75-1.00 / 回復<=16 / MACD>0.03 / BB幅<=4ATR` をH1で検証した。

H4の16本は64時間に相当するため、H1では数値そのままの16本版と、時間換算の64本版を両方確認した。

## サマリー

| case                     | notes                         | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | all_max_losing_streak | research_trades | research_win_rate | research_total_r | research_avg_r | research_pf | research_max_dd_r | research_max_losing_streak | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | oos_max_losing_streak |
| ------------------------ | ----------------------------- | ---------- | ------------ | ----------- | --------- | ------ | ------------ | --------------------- | --------------- | ----------------- | ---------------- | -------------- | ----------- | ----------------- | -------------------------- | ---------- | ------------ | ----------- | --------- | ------ | ------------ | --------------------- |
| H1_LITERAL_RECOVERY16    | H4上位条件を数値そのままH1へ適用。回復<=16時間。  | 18         | 33.333       | -0.290      | -0.016    | 0.976  | 7.199        | 6                     | 14              | 21.429            | -5.269           | -0.376         | 0.531       | 7.199             | 6                          | 4          | 75.000       | 4.979       | 1.245     | 5.958  | 1.004        | 1                     |
| H1_TIME_EQUIV_RECOVERY64 | H4の回復<=16本を時間換算。H1では回復<=64時間。 | 31         | 38.710       | 2.888       | 0.093     | 1.149  | 4.165        | 4                     | 24              | 33.333            | -0.465           | -0.019         | 0.971       | 4.165             | 4                          | 7          | 57.143       | 3.353       | 0.479     | 2.115  | 2.004        | 2                     |

## 解釈メモ

- `H1_LITERAL_RECOVERY16`: H1で16時間以内のかなり速い回復だけを見る。
- `H1_TIME_EQUIV_RECOVERY64`: H4条件と時間感覚を合わせた確認。
- H1はノイズが増えるため、H4と同じPF/勝率を期待するより、先行察知や補助確認として残るかを見る。

## 出力

- `t5_h1_broad_trades_2015_2026.csv`
- `summary.csv`
- `h1_literal_recovery16_trades.csv`
- `h1_time_equiv_recovery64_trades.csv`
- `*_by_symbol.csv`, `*_by_year.csv`, `*_by_trigger.csv`
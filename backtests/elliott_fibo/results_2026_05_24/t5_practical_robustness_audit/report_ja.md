# H4 V候補 T5 + MACD + BB ロバスト性監査

## 前提

- 研究期間: 2015-2024。
- OOS/未使用期間: 2025-2026。追加ファイルがある範囲まで使用。
- 母集団: H4で急落後61.8%〜80%回復候補を作り、その後 `stagnation` または `rebreak` が出たT5。
- V候補は環境認識。実際のエントリーはT5トリガー後。
- Rはコスト込み `r_after_cost`。

## データ件数

- T5 broad trades: 303
- V candidate only trades: 379

## 1. 条件寄与率分析

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 Broad T5 universe | 303 | 45.54 | 47.85 | 0.16 | 1.31 | 13.18 | 37 | 59.46 | 11.47 | 0.31 | 1.80 | 2.02 | V候補後にstagnation/rebreak。追加フィルタなし |
| 01 Full strict practical | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, MACD>0, BB幅<=4ATR, 弱い単独rebreak除外 |
| LOO remove BB<=0.95 | 28 | 64.29 | 23.23 | 0.83 | 3.50 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB上限だけ外す |
| LOO remove recovery<=16 | 31 | 64.52 | 24.51 | 0.79 | 3.39 | 2.15 | 6 | 83.33 | 5.10 | 0.85 | 6.07 | 1.01 | 回復本数上限だけ外す |
| LOO remove MACD>0 | 28 | 64.29 | 21.20 | 0.76 | 3.28 | 3.16 | 6 | 83.33 | 4.45 | 0.74 | 5.44 | 1.00 | MACD slope3プラスだけ外す |
| LOO remove BB幅<=4ATR | 46 | 60.87 | 32.54 | 0.71 | 2.96 | 5.45 | 5 | 100.00 | 6.71 | 1.34 | inf | 0.00 | BB幅上限だけ外す |
| LOO remove weak rebreak guard | 26 | 69.23 | 25.29 | 0.97 | 4.49 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | 弱い単独rebreak除外だけ外す |
| Only stagnation | 4 | 50.00 | 1.84 | 0.46 | 1.85 | 1.10 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | Full条件 + stagnation単独 |
| Only rebreak | 15 | 66.67 | 12.56 | 0.84 | 4.08 | 2.04 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | Full条件 + rebreak単独 |
| Only stagnation+rebreak | 4 | 100.00 | 7.96 | 1.99 | inf | 0.00 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | Full条件 + 両方重なる |

### Leave-one-out 判定

| case | all_trades | all_total_r | all_avg_r | all_pf | all_max_dd_r | pf_change_vs_full | dd_change_vs_full | avg_r_change_vs_full | fragility_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOO remove BB<=0.95 | 28 | 23.23 | 0.83 | 3.50 | 2.15 | -1.09 | 0.00 | -0.14 | 外しても致命傷ではない |
| LOO remove recovery<=16 | 31 | 24.51 | 0.79 | 3.39 | 2.15 | -1.20 | 0.00 | -0.18 | 外すと悪化が大きい |
| LOO remove MACD>0 | 28 | 21.20 | 0.76 | 3.28 | 3.16 | -1.31 | 1.01 | -0.21 | 外すと悪化が大きい |
| LOO remove BB幅<=4ATR | 46 | 32.54 | 0.71 | 2.96 | 5.45 | -1.63 | 3.30 | -0.26 | 外すと悪化が大きい |
| LOO remove weak rebreak guard | 26 | 25.29 | 0.97 | 4.49 | 2.15 | -0.10 | 0.00 | 0.00 | 外しても致命傷ではない |

## 2. 閾値感度分析

### bb_position

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BB<=0.85 | 11 | 54.55 | 3.52 | 0.32 | 1.68 | 2.11 | 3 | 100.00 | 2.76 | 0.92 | inf | 0.00 | lower BB fixed at 0.60 |
| BB<=0.90 | 17 | 64.71 | 12.46 | 0.73 | 3.01 | 2.15 | 3 | 100.00 | 2.76 | 0.92 | inf | 0.00 | lower BB fixed at 0.60 |
| BB<=0.95 | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | lower BB fixed at 0.60 |
| BB<=1.00 | 26 | 69.23 | 25.25 | 0.97 | 4.48 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | lower BB fixed at 0.60 |

### recovery_bars

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Recovery<=8 | 8 | 62.50 | 6.76 | 0.85 | 3.15 | 2.11 | 1 | 100.00 | 1.96 | 1.96 | inf | 0.00 | BB<=0.95, MACD>0, BB幅<=4ATR |
| Recovery<=12 | 19 | 68.42 | 17.38 | 0.91 | 4.33 | 2.15 | 3 | 100.00 | 2.73 | 0.91 | inf | 0.00 | BB<=0.95, MACD>0, BB幅<=4ATR |
| Recovery<=16 | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, MACD>0, BB幅<=4ATR |
| Recovery<=20 | 24 | 66.67 | 21.34 | 0.89 | 3.95 | 2.15 | 5 | 80.00 | 3.71 | 0.74 | 4.69 | 1.01 | BB<=0.95, MACD>0, BB幅<=4ATR |
| Recovery<=24 | 28 | 64.29 | 22.70 | 0.81 | 3.46 | 2.15 | 6 | 83.33 | 5.10 | 0.85 | 6.07 | 1.01 | BB<=0.95, MACD>0, BB幅<=4ATR |

### macd_slope3

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MACD slope3>0.00 | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, BB幅<=4ATR |
| MACD slope3>0.01 | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, BB幅<=4ATR |
| MACD slope3>0.02 | 20 | 75.00 | 22.51 | 1.13 | 6.53 | 1.03 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, BB幅<=4ATR |
| MACD slope3>0.03 | 19 | 73.68 | 20.52 | 1.08 | 6.04 | 1.03 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, BB幅<=4ATR |
| MACD slope3>0.05 | 7 | 57.14 | 3.15 | 0.45 | 2.04 | 3.02 | 1 | 100.00 | 0.22 | 0.22 | inf | 0.00 | BB<=0.95, recovery<=16, BB幅<=4ATR |

### bb_width

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BB幅<=2ATR | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | BB<=0.95, recovery<=16, MACD>0 |
| BB幅<=4ATR | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | BB<=0.95, recovery<=16, MACD>0 |
| BB幅<=5ATR | 35 | 62.86 | 28.95 | 0.83 | 3.51 | 4.45 | 5 | 100.00 | 6.71 | 1.34 | inf | 0.00 | BB<=0.95, recovery<=16, MACD>0 |
| BB幅<=7ATR | 45 | 62.22 | 33.55 | 0.75 | 3.15 | 5.45 | 5 | 100.00 | 6.71 | 1.34 | inf | 0.00 | BB<=0.95, recovery<=16, MACD>0 |

### 感度分析の警告

- 大きな一点突出は検出されませんでした。ただしOOS取引数が少ない箇所は保守的に見るべきです。

## 3. 構造分析

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A V candidate only | 379 | 44.06 | 73.27 | 0.19 | 1.35 | 12.69 | 44 | 47.73 | 10.22 | 0.23 | 1.46 | 7.90 | 61.8-80%回復候補で即エントリー |
| B V + stagnation | 13 | 61.54 | 9.41 | 0.72 | 2.82 | 2.11 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | V候補後の高値停滞のみ |
| C V + rebreak | 39 | 53.85 | 19.20 | 0.49 | 2.16 | 3.05 | 6 | 83.33 | 5.70 | 0.95 | 6.67 | 1.01 | V候補後の再ブレイクのみ |
| D V + stagnation+rebreak | 8 | 75.00 | 8.82 | 1.10 | 5.38 | 1.01 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 高値停滞と再ブレイクが同時に成立 |
| T5 either broad | 303 | 45.54 | 47.85 | 0.16 | 1.31 | 13.18 | 37 | 59.46 | 11.47 | 0.31 | 1.80 | 2.02 | V候補後にどちらかのT5トリガー |
| T5 either practical | 46 | 60.87 | 32.54 | 0.71 | 2.96 | 5.45 | 5 | 100.00 | 6.71 | 1.34 | inf | 0.00 | T5 + BB<=0.95 + recovery<=16 + MACD>0 |

## 4. 通貨別比較

| symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | oos_max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | 4 | 75.00 | 5.95 | 1.49 | 270.22 | 0.02 | 1 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| XAUUSD | 4 | 75.00 | 4.95 | 1.24 | 5.91 | 1.01 | 1 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| CHFJPY | 4 | 75.00 | 4.93 | 1.23 | 5.91 | 1.00 | 1 | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 |
| GBPJPY | 3 | 100.00 | 4.55 | 1.52 | inf | 0.00 | 0 | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 | 0 |
| AUDJPY | 2 | 100.00 | 3.99 | 1.99 | inf | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| EURJPY | 1 | 0.00 | -1.01 | -1.01 | 0.00 | 0.00 | 1 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| SILVER | 5 | 40.00 | -1.01 | -0.20 | 0.68 | 2.13 | 3 | 2 | 100.00 | 2.17 | 1.09 | inf | 0.00 | 0 |

## 5. 市場環境別比較

| environment | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | oos_max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Crisis windows | 1 | 100.00 | 1.99 | 1.99 | inf | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| Range/choppy | 5 | 100.00 | 9.96 | 1.99 | inf | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| Gold Monday proxy | 2 | 100.00 | 3.98 | 1.99 | inf | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| High ATR percentile | 7 | 71.43 | 8.89 | 1.27 | 9.67 | 1.00 | 1 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| Normal ATR | 10 | 60.00 | 4.59 | 0.46 | 2.12 | 2.02 | 2 | 3 | 100.00 | 2.73 | 0.91 | inf | 0.00 | 0 |
| Trend up | 2 | 50.00 | 0.91 | 0.46 | 1.87 | 0.00 | 1 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| Vol spike | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |
| Rate/news proxy | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 0 |

## 6. TrendBreakV1 との重複リスク

| case | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T5 all 2015-2024 | 34 | 61.76 | 29.20 | 0.86 | 3.55 | 4.35 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 |  |
| T5 overlaps TrendBreak | 14 | 71.43 | 16.40 | 1.17 | 7.94 | 1.01 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 同通貨で保有期間が重なる |
| T5 independent from TrendBreak | 20 | 55.00 | 12.79 | 0.64 | 2.41 | 3.02 | 0 | 0.00 | 0.00 | 0.00 |  | 0.00 | 同通貨の保有期間重複なし |

## 7. 実戦性ストレス

| case | notes | all_trades | all_win_rate | all_total_r | all_avg_r | all_pf | all_max_dd_r | all_max_losing_streak | oos_trades | oos_win_rate | oos_total_r | oos_avg_r | oos_pf | oos_max_dd_r | oos_max_losing_streak | research_trades | research_win_rate | research_total_r | research_avg_r | research_pf | research_max_dd_r | research_max_losing_streak | oos_positive | oos_avg_retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Base current cost | same trades, stressed R | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 2 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Spread/slippage x1.5 | same trades, stressed R | 23 | 69.57 | 22.15 | 0.96 | 4.50 | 2.23 | 2 | 4 | 100.00 | 4.69 | 1.17 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Spread/slippage x2.0 | same trades, stressed R | 23 | 69.57 | 21.94 | 0.95 | 4.41 | 2.30 | 2 | 4 | 100.00 | 4.66 | 1.17 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Spread/slippage x3.0 | same trades, stressed R | 23 | 69.57 | 21.53 | 0.94 | 4.24 | 2.46 | 2 | 4 | 100.00 | 4.61 | 1.15 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Extra execution -0.10R | same trades, stressed R | 23 | 69.57 | 20.05 | 0.87 | 3.89 | 2.35 | 2 | 4 | 100.00 | 4.32 | 1.08 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Extra execution -0.20R | same trades, stressed R | 23 | 69.57 | 17.75 | 0.77 | 3.33 | 2.55 | 2 | 4 | 100.00 | 3.92 | 0.98 | inf | 0.00 | 0 |  |  |  |  |  |  |  | nan |  |
| Exclude ATR ratio>=1.5 | 高ボラ急増を除外 | 23 | 69.57 | 22.35 | 0.97 | 4.59 | 2.15 | 2 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | 0 | 19.00 | 63.16 | 17.63 | 0.93 | 3.83 | 2.15 | 2.00 | True | 1.27 |
| Exclude ATR pctile>=80 | ATR上位20%を除外 | 16 | 68.75 | 13.46 | 0.84 | 3.59 | 1.10 | 2 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | 0 | 12.00 | 58.33 | 8.74 | 0.73 | 2.68 | 1.10 | 2.00 | True | 1.62 |
| Exclude XAU Monday proxy | ゴールド週明けギャップ代理条件を除外 | 21 | 66.67 | 18.37 | 0.87 | 3.95 | 2.04 | 2 | 4 | 100.00 | 4.72 | 1.18 | inf | 0.00 | 0 | 17.00 | 58.82 | 13.65 | 0.80 | 3.19 | 2.04 | 2.00 | True | 1.47 |

## 崩れやすい条件

- OOS取引数が少ないため、PFだけで判断すると危険。
- `V candidate only` が弱い場合、V字そのものではなく、その後の再加速構造が本体。
- `rebreak` 単独はMACDが弱い時に崩れやすい。単独rebreakは選別が必要。
- ボラ急増・ATR上位・BB幅過大は、方向が合ってもSLに触れやすい。

## 実戦で残すべき条件

- BB位置上限は残す。ただし0.90〜1.00付近で滑らかに残るかを見る。
- V候補からシグナルまでの時間制限は残す。遅い戻りはV字の本質から外れやすい。
- MACD slope3は単独rebreakの弱さを避ける目的で残す。
- BB幅<=4ATRはDD抑制条件として残す。取引数を増やす場合でも5ATRまでを上限候補にする。
- stagnation / rebreak はエントリー条件。V候補だけで入らない。

## 削除または降格してもよい条件

- weak rebreak guardはBB位置/MACD条件と重複しやすいので、必須条件ではなく警告・補助条件へ降格可能。
- stagnation+rebreakだけに限定すると強いが、取引数が少なすぎる場合は候補として残すだけにする。

## 実戦で最も壊れにくい最小構成案

1. H4で急落後V候補を作る。V候補だけでは入らない。
2. 回復候補は急落の61.8%〜80%。回復は急落本数の1.20倍以内を基本にする。
3. T5トリガーは `stagnation` または `rebreak`。両方重なる場合は最優先。
4. BB位置は0.60〜0.95を基本。0.95超は見送り。
5. MACD slope3はプラスを要求。単独rebreakは0.03以下なら見送り。
6. BB幅<=4ATRを標準にする。取引数を増やす検証では5ATRまで緩和し、それ以上は過熱扱い。
7. TrendBreakV1と同通貨で同時期に重なる場合は、同じ相場リスクとみなし合計リスクを下げる。

## 出力CSV

- `t5_broad_trades_2015_2026.csv`
- `v_candidate_only_trades_2015_2026.csv`
- `condition_contribution.csv`
- `leave_one_out_fragility.csv`
- `sweep_*.csv`
- `structure_analysis.csv`
- `by_symbol_practical.csv`
- `market_environment.csv`
- `execution_stress.csv`
- `trendbreak_overlap.csv`
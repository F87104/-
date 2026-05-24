# TrendBreakV1 + H4 T5 MACD BB 実戦用フィルタ 組み合わせ分析 2015-2024

## 前提

- TrendBreakV1: `fakeout_before_after_2015_2024/trades.csv` の baseline。
- H4 T5 MACD BB: V候補を環境認識にし、BB<=0.95、V候補から16本以内、弱い単独rebreak除外の実戦用フィルタ。
- Rはコスト込み。資産推定は100万円スタート、1トレード1%リスク。

## 全通貨

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_dd_pct_compounded | max_loss_streak | linear_final_jpy_1pct | compound_final_jpy_1pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trendbreak_only | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13.15% | 13 | 2,915,298円 | 6,216,135円 |
| t5_practical_only | 34 | 61.76% | 29.20R | 0.859R | 3.555 | 4.35R | 4.28% | 5 | 1,291,959円 | 1,333,028円 |
| all_trades | 495 | 38.59% | 220.73R | 0.446R | 1.693 | 14.02R | 13.15% | 13 | 3,207,258円 | 8,286,279円 |
| trendbreak_priority_add_t5_when_free | 481 | 37.63% | 204.32R | 0.425R | 1.646 | 14.02R | 13.15% | 13 | 3,043,246円 | 7,046,232円 |
| same_symbol_first_wins | 481 | 38.67% | 215.59R | 0.448R | 1.698 | 14.02R | 13.15% | 13 | 3,155,900円 | 7,892,485円 |

## 推奨6通貨のみ（AUDJPY除外）

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_dd_pct_compounded | max_loss_streak | linear_final_jpy_1pct | compound_final_jpy_1pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trendbreak_only | 381 | 39.37% | 194.61R | 0.511R | 1.794 | 11.94R | 11.31% | 11 | 2,946,071円 | 6,486,396円 |
| t5_practical_only | 30 | 60.00% | 25.33R | 0.844R | 3.431 | 4.35R | 4.28% | 5 | 1,253,346円 | 1,283,154円 |
| all_trades | 411 | 40.88% | 219.94R | 0.535R | 1.861 | 11.94R | 11.31% | 11 | 3,199,417円 | 8,323,043円 |
| trendbreak_priority_add_t5_when_free | 399 | 40.10% | 206.42R | 0.517R | 1.816 | 11.94R | 11.31% | 11 | 3,064,168円 | 7,282,304円 |
| same_symbol_first_wins | 399 | 40.85% | 212.73R | 0.533R | 1.858 | 11.94R | 11.31% | 11 | 3,127,305円 | 7,763,826円 |

## TrendBreak優先 + T5追加時の内訳

### 戦略別

| strategy | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TrendBreakV1 | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13 |
| H4 T5 MACD BB | 20 | 55.00% | 12.79R | 0.640R | 2.412 | 3.02R | 3 |

### 通貨別

| symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | 79 | 45.57% | 58.15R | 0.736R | 2.294 | 6.19R | 6 |
| GBPJPY | 64 | 42.19% | 40.08R | 0.626R | 2.050 | 6.16R | 6 |
| SILVER | 64 | 43.75% | 36.62R | 0.572R | 1.865 | 6.41R | 5 |
| USDJPY | 68 | 38.24% | 31.88R | 0.469R | 1.737 | 9.37R | 9 |
| CHFJPY | 67 | 37.31% | 27.29R | 0.407R | 1.616 | 9.37R | 10 |
| EURJPY | 57 | 31.58% | 12.39R | 0.217R | 1.309 | 7.41R | 7 |
| AUDJPY | 82 | 25.61% | -2.09R | -0.026R | 0.967 | 17.95R | 12 |

### T5トリガー別

| trigger_type | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stagnation | 10 | 70.00% | 10.84R | 1.084R | 4.529 | 1.01R | 2 |
| rebreak | 16 | 50.00% | 9.53R | 0.596R | 2.502 | 1.03R | 2 |
| stagnation+rebreak | 8 | 75.00% | 8.82R | 1.103R | 5.383 | 1.01R | 1 |

## 読み取り

- 厳格V字をそのまま足した旧分析とは違い、T5/MACD/BBで絞ったV候補手法は単体でプラス。
- ただし取引回数は少ないため、TrendBreakを主軸、T5を補助にするのが自然。
- 同一通貨でポジションが空いている時だけT5を追加する案では、総RはTrendBreak単体より上がるが、DDもやや増える可能性がある。
- 実運用ではT5を0.25Rから0.5Rで始め、フォワード30から50回で安定確認してから通常リスク化するのが現実的。

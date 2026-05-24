# TrendBreakV1 + H4急落後V字回復 組み合わせ分析 2015-2024

## 前提

- TrendBreakV1: `fakeout_before_after_2015_2024/trades.csv` の `baseline`。現行HYBRID、騙し回避フィルタOFF、同方向最大保有数は初期値1の想定。
- H4急落後V字回復: `strict_v_recovery/strict_v_trades_h4.csv`。現在の `h4_sharp_drop_v_recovery_visual.pine` に近い、完全回復・回復速度重視の厳格V字。
- Rはコスト込み。資産推定は `100万円スタート / 1トレード1%リスク`。

## 全通貨の比較

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_dd_pct_compounded | max_loss_streak | linear_final_jpy_1pct | compound_final_jpy_1pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trendbreak_only | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13.15% | 13 | 2,915,298円 | 6,216,135円 |
| h4_v_only | 39 | 30.77% | -7.16R | -0.184R | 0.723 | 13.20R | 12.58% | 5 | 928,354円 | 928,038円 |
| all_trades | 500 | 36.40% | 184.37R | 0.369R | 1.554 | 18.62R | 17.29% | 13 | 2,843,652円 | 5,768,808円 |
| trendbreak_priority_add_h4_when_free | 500 | 36.40% | 184.37R | 0.369R | 1.554 | 18.62R | 17.29% | 13 | 2,843,652円 | 5,768,808円 |
| same_symbol_first_wins | 500 | 36.40% | 184.37R | 0.369R | 1.554 | 18.62R | 17.29% | 13 | 2,843,652円 | 5,768,808円 |

## 推奨6通貨のみ（AUDJPY除外）

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_dd_pct_compounded | max_loss_streak | linear_final_jpy_1pct | compound_final_jpy_1pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trendbreak_only | 381 | 39.37% | 194.61R | 0.511R | 1.794 | 11.94R | 11.31% | 11 | 2,946,071円 | 6,486,396円 |
| h4_v_only | 38 | 28.95% | -9.16R | -0.241R | 0.646 | 13.20R | 12.58% | 5 | 908,432円 | 909,910円 |
| all_trades | 419 | 38.42% | 185.45R | 0.443R | 1.685 | 18.43R | 17.05% | 11 | 2,854,503円 | 5,902,039円 |
| trendbreak_priority_add_h4_when_free | 419 | 38.42% | 185.45R | 0.443R | 1.685 | 18.43R | 17.05% | 11 | 2,854,503円 | 5,902,039円 |
| same_symbol_first_wins | 419 | 38.42% | 185.45R | 0.443R | 1.685 | 18.43R | 17.05% | 11 | 2,854,503円 | 5,902,039円 |

## 実運用寄りの採用案

`trendbreak_priority_add_h4_when_free` は、TrendBreakV1を主軸として全て採用し、H4 Vは同一通貨でポジションが空いている時だけ追加する案です。

### 戦略別

| strategy | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H4 Sharp Drop V | 39 | 30.77% | -7.16R | -0.184R | 0.723 | 13.20R | 5 |
| TrendBreakV1 | 461 | 36.88% | 191.53R | 0.415R | 1.624 | 14.02R | 13 |

### 通貨別

| symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | 82 | 42.68% | 52.11R | 0.635R | 2.063 | 9.44R | 7 |
| SILVER | 66 | 43.94% | 37.11R | 0.562R | 1.855 | 6.41R | 5 |
| GBPJPY | 70 | 40.00% | 35.96R | 0.514R | 1.850 | 7.44R | 6 |
| USDJPY | 74 | 36.49% | 28.82R | 0.390R | 1.596 | 9.37R | 9 |
| CHFJPY | 67 | 35.82% | 22.39R | 0.334R | 1.494 | 9.37R | 10 |
| EURJPY | 60 | 30.00% | 9.05R | 0.151R | 1.213 | 9.39R | 7 |
| AUDJPY | 81 | 25.93% | -1.09R | -0.013R | 0.983 | 17.95R | 12 |

### 年別

| year | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015.0 | 34 | 35.29% | 11.44R | 0.336R | 1.486 | 5.38R | 5 |
| 2016.0 | 44 | 34.09% | 13.70R | 0.311R | 1.448 | 8.21R | 6 |
| 2017.0 | 43 | 34.88% | 14.38R | 0.334R | 1.485 | 7.68R | 7 |
| 2018.0 | 55 | 32.73% | 13.42R | 0.244R | 1.341 | 14.02R | 13 |
| 2019.0 | 53 | 49.06% | 46.01R | 0.868R | 2.583 | 4.44R | 4 |
| 2020.0 | 52 | 36.54% | 21.35R | 0.411R | 1.620 | 10.41R | 10 |
| 2021.0 | 46 | 39.13% | 23.39R | 0.509R | 1.792 | 5.69R | 4 |
| 2022.0 | 44 | 40.91% | 25.97R | 0.590R | 1.953 | 4.28R | 4 |
| 2023.0 | 46 | 32.61% | 12.09R | 0.263R | 1.375 | 9.37R | 9 |
| 2024.0 | 44 | 31.82% | 9.78R | 0.222R | 1.311 | 7.47R | 7 |
| nan | 39 | 30.77% | -7.16R | -0.184R | 0.723 | 13.20R | 5 |

## 読み取り

- H4急落後V字回復は単体では成績が弱いため、今の厳格V字をそのまま売買システムとして足す価値は低いです。
- TrendBreakV1を主軸にして、H4 Vを同一通貨が空いている時だけ追加しても、改善幅は限定的か、悪化する可能性があります。
- H4 Vは売買トリガーではなく、以前の結論どおり「環境認識・候補抽出」として使い、高値停滞/再ブレイク/MACD/BBなどの追加条件で絞る方が自然です。

## 出力ファイル

- `overall_all_symbols.csv`
- `overall_recommended_ex_audjpy.csv`
- `trendbreak_priority_add_h4_when_free_trades.csv`
- `trendbreak_priority_by_strategy.csv`
- `trendbreak_priority_by_symbol.csv`
- `trendbreak_priority_by_year.csv`
# TrendBreakV1 vs Sai (Best Method) 同一期間厳密比較

- Period: 2015-01-01 to 2024-12-31
- Timeframe: H1
- Metric: R-multiple
- Data source: F87104_test (両戦略とも同じ)

## ⭐ Main Comparison

| label | trades | wins | losses | win_rate_pct | total_r | avg_r | median_r | profit_factor | max_dd_r | expectancy_per_trade_r | avg_hold_days | trades_per_year | calmar_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TrendBreakV1 [Combined] | 1501 | 513 | 988 | 34.18 | 551.0 | 0.367 | -1.0 | 1.56 | 41.0 | 0.367 | 1.02 | 150.1 | 13.44 |
| TrendBreakV1 [Conservative] | 392 | 144 | 248 | 36.73 | 184.0 | 0.469 | -1.0 | 1.74 | 15.0 | 0.469 | 1.56 | 39.2 | 12.27 |
| TrendBreakV1 [Relaxed] | 1109 | 369 | 740 | 33.27 | 367.0 | 0.331 | -1.0 | 1.5 | 48.0 | 0.331 | 0.82 | 110.9 | 7.65 |
| Sai H1 [BestMethod=急な揺り戻し+高値停滞] | 378 | 168 | 210 | 44.44 | 98.84 | 0.261 | -1.0 | 1.47 | 13.21 | 0.261 | 1.71 | 37.8 | 7.48 |

## Key Findings

### 1. 純利益 (Total R)
- TrendBreakV1 Combined: **+551.0R**
- Sai Best Method:        **+98.84R**
- **倍率: 5.57x** (TrendBreakが Sai best の何倍稼いだか)

### 2. プロフィットファクター
- TrendBreakV1 Combined: **1.56**
- Sai Best Method:        **1.47**

### 3. リスク調整リターン (Calmar Proxy = Total R / MaxDD R)
- TrendBreakV1 Combined: **13.44**
- Sai Best Method:        **7.48**

### 4. 1トレード当たり期待値 (Avg R)
- TrendBreakV1 Combined: **0.367R**
- Sai Best Method:        **0.261R**

### 5. 年間取引機会
- TrendBreakV1 Combined: **150.1 trades/年**
- Sai Best Method:        **37.8 trades/年**

### 6. 平均保有期間
- TrendBreakV1 Combined: **1.02 日**
- Sai Best Method:        **1.71 日**

## Year-by-Year (4 strategies side by side)

| strategy | year | trades | wr | total_r | max_dd |
| --- | --- | --- | --- | --- | --- |
| TrendBreakV1_Combined | 2015 | 133 | 33.83 | 47.0 | 8.0 |
| TrendBreakV1_Combined | 2016 | 164 | 36.59 | 76.0 | 13.0 |
| TrendBreakV1_Combined | 2017 | 146 | 32.19 | 42.0 | 11.0 |
| TrendBreakV1_Combined | 2018 | 152 | 22.37 | -16.0 | 30.0 |
| TrendBreakV1_Combined | 2019 | 174 | 41.38 | 114.0 | 9.0 |
| TrendBreakV1_Combined | 2020 | 145 | 34.48 | 55.0 | 15.0 |
| TrendBreakV1_Combined | 2021 | 149 | 38.93 | 83.0 | 8.0 |
| TrendBreakV1_Combined | 2022 | 149 | 36.24 | 67.0 | 11.0 |
| TrendBreakV1_Combined | 2023 | 142 | 30.28 | 30.0 | 12.0 |
| TrendBreakV1_Combined | 2024 | 147 | 34.01 | 53.0 | 12.0 |
| TrendBreakV1_Conservative | 2015 | 34 | 35.29 | 14.0 | 7.0 |
| TrendBreakV1_Conservative | 2016 | 41 | 31.71 | 11.0 | 13.0 |
| TrendBreakV1_Conservative | 2017 | 39 | 33.33 | 13.0 | 11.0 |
| TrendBreakV1_Conservative | 2018 | 44 | 29.55 | 8.0 | 6.0 |
| TrendBreakV1_Conservative | 2019 | 51 | 49.02 | 49.0 | 4.0 |
| TrendBreakV1_Conservative | 2020 | 38 | 34.21 | 14.0 | 7.0 |
| TrendBreakV1_Conservative | 2021 | 32 | 40.62 | 20.0 | 6.0 |
| TrendBreakV1_Conservative | 2022 | 40 | 45.0 | 32.0 | 6.0 |
| TrendBreakV1_Conservative | 2023 | 36 | 33.33 | 12.0 | 10.0 |
| TrendBreakV1_Conservative | 2024 | 37 | 32.43 | 11.0 | 6.0 |
| TrendBreakV1_Relaxed | 2015 | 99 | 33.33 | 33.0 | 8.0 |
| TrendBreakV1_Relaxed | 2016 | 123 | 38.21 | 65.0 | 12.0 |
| TrendBreakV1_Relaxed | 2017 | 107 | 31.78 | 29.0 | 9.0 |
| TrendBreakV1_Relaxed | 2018 | 108 | 19.44 | -24.0 | 28.0 |
| TrendBreakV1_Relaxed | 2019 | 123 | 38.21 | 65.0 | 9.0 |
| TrendBreakV1_Relaxed | 2020 | 107 | 34.58 | 41.0 | 15.0 |
| TrendBreakV1_Relaxed | 2021 | 117 | 38.46 | 63.0 | 8.0 |
| TrendBreakV1_Relaxed | 2022 | 109 | 33.03 | 35.0 | 11.0 |
| TrendBreakV1_Relaxed | 2023 | 106 | 29.25 | 18.0 | 12.0 |
| TrendBreakV1_Relaxed | 2024 | 110 | 34.55 | 42.0 | 12.0 |
| Sai_BestMethod | 2015 | 18 | 38.89 | -2.71 | 6.53 |
| Sai_BestMethod | 2016 | 32 | 65.62 | 13.15 | 4.0 |
| Sai_BestMethod | 2017 | 34 | 47.06 | 10.7 | 4.0 |
| Sai_BestMethod | 2018 | 44 | 36.36 | -4.95 | 7.49 |
| Sai_BestMethod | 2019 | 36 | 47.22 | 8.22 | 6.53 |
| Sai_BestMethod | 2020 | 33 | 54.55 | 42.79 | 3.0 |
| Sai_BestMethod | 2021 | 40 | 30.0 | -7.09 | 9.85 |
| Sai_BestMethod | 2022 | 34 | 41.18 | 9.16 | 6.63 |
| Sai_BestMethod | 2023 | 49 | 44.9 | 12.1 | 5.83 |
| Sai_BestMethod | 2024 | 58 | 43.1 | 17.47 | 11.81 |

## Symbol-by-Symbol

| strategy | symbol | trades | wr | total_r | pf |
| --- | --- | --- | --- | --- | --- |
| TrendBreakV1 | XAUUSD | 237 | 39.66 | 139.0 | 1.97 |
| TrendBreakV1 | GBPJPY | 281 | 33.1 | 91.0 | 1.48 |
| TrendBreakV1 | SILVER | 214 | 35.05 | 86.0 | 1.62 |
| TrendBreakV1 | USDJPY | 183 | 34.97 | 73.0 | 1.61 |
| TrendBreakV1 | CHFJPY | 137 | 36.5 | 63.0 | 1.72 |
| TrendBreakV1 | AUDJPY | 246 | 31.3 | 62.0 | 1.37 |
| TrendBreakV1 | EURJPY | 203 | 29.56 | 37.0 | 1.26 |
| Sai_BestMethod | XAUUSD | 74 | 45.95 | 49.83 | 2.25 |
| Sai_BestMethod | XAGUSD | 55 | 47.27 | 25.52 | 1.88 |
| Sai_BestMethod | EURJPY | 57 | 49.12 | 19.32 | 1.67 |
| Sai_BestMethod | AUDJPY | 59 | 44.07 | 6.22 | 1.19 |
| Sai_BestMethod | GBPJPY | 63 | 42.86 | -0.39 | 0.99 |
| Sai_BestMethod | CHFJPY | 70 | 38.57 | -1.65 | 0.96 |

## 結論

### 🏆 総合勝者: **TrendBreakV1 (Combined)**

- 純利益で Sai best の **5.57倍**
- PF: TrendBreak 1.56 vs Sai 1.47
- 年間取引機会: TrendBreak 150.1 vs Sai 37.8
- リスク調整リターン (Calmar): TrendBreak 13.44 vs Sai 7.48

### Sai best method の唯一の優位点
- **勝率**: Sai 44.44% vs TrendBreak 34.18%
  → ただし、利益は TrendBreak が圧勝。勝率は本質的指標ではない。
  → Sai は Long-only (買いのみ) なので、市場の長期上昇バイアスを利用している面もある。

### 結論
- **本番戦略は TrendBreakV1_Final.pine で決まり**
- Sai の best method ロジック (急な揺り戻し+高値停滞 = 上昇トレンド中の押し目) を
  TrendBreak に組み込む案は、過剰最適化リスクが高いため非推奨
- Sai 系のスクリプトは引き続き **裁量補助の可視化ツール** として活用
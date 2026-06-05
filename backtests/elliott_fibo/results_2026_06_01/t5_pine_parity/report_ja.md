# H4 T5 Pine Parity Export

Status: **TradingView 照合待ち**（Python 期待値エクスポート済み）

## 目的

Strict REC1.2 + MACD/BB の Python 99件（Research 2015–2024）と、
`h4_t5_macd_bb_live_ready.pine` の **signal_time / entry_time** が一致するか確認する。

## Python ソース

- `backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv`
- 設定: Strict_075_100_width7 + max_recovery_to_drop=1.20

## 期待サマリー

| case | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- |
| BASE Research 2015-2024 | 99 | 55.56 | 59.76 | 0.60 | 2.55 | 6.67 |
| BASE OOS 2025-2026 | 15 | 66.67 | 7.26 | 0.48 | 2.44 | 2.02 |
| BASE ALL | 114 | 57.02 | 67.03 | 0.59 | 2.54 | 6.67 |
| Practical Research | 34 | 61.76 | 29.20 | 0.86 | 3.55 | 4.35 |
| Practical OOS | 5 | 100.00 | 6.71 | 1.34 | inf | 0.00 |
| Practical Research ex-AUDJPY | 30 | 60.00 | 25.33 | 0.84 | 3.43 | 4.35 |

## Phase A: BASE 99件 — 通貨別

| symbol | trades | total_r |
| --- | --- | --- |
| GBPJPY | 23 | 16.95 |
| USDJPY | 16 | 12.53 |
| AUDJPY | 15 | 9.37 |
| SILVER | 14 | 0.78 |
| EURJPY | 11 | -0.01 |
| XAUUSD | 11 | 11.27 |
| CHFJPY | 9 | 8.87 |

## 最初に見る USDJPY（16件）

件数が中程度で OOS も良好。最初のスモークテスト用。

| trade_id | signal_time | entry_time | trigger_type | signal_close | stop | target | r_after_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 2015-03-31 00:00:00 | 2015-03-31 04:00:00 | rebreak | 120.27 | 118.25 | 124.30 | -0.14 |
| 8 | 2015-12-07 08:00:00 | 2015-12-07 12:00:00 | stagnation | 123.45 | 122.23 | 125.88 | -1.01 |
| 11 | 2016-04-19 08:00:00 | 2016-04-19 12:00:00 | rebreak | 109.45 | 107.74 | 112.87 | -1.01 |
| 19 | 2016-12-07 04:00:00 | 2016-12-07 08:00:00 | stagnation | 114.34 | 112.76 | 117.52 | 2.00 |
| 20 | 2017-01-19 12:00:00 | 2017-01-19 16:00:00 | stagnation | 115.31 | 112.42 | 121.09 | -1.00 |
| 30 | 2017-09-18 04:00:00 | 2017-09-18 08:00:00 | rebreak | 111.41 | 109.45 | 115.32 | 1.24 |
| 36 | 2018-10-22 04:00:00 | 2018-10-22 08:00:00 | rebreak | 112.75 | 111.57 | 115.13 | -1.01 |
| 37 | 2018-10-30 00:00:00 | 2018-10-30 04:00:00 | rebreak | 112.66 | 111.30 | 115.37 | -0.02 |

## Pine 設定（Phase A）

| 項目 | 値 |
|---|---|
| プリセット Strict + REC1.2 | ON |
| 騙し回避フィルタ | **OFF** |
| 運用判定 FULL/HALF/SKIP | **OFF** |
| 年末年始除外 | ON |

## 次のアクション

1. `tradingview_parity_checklist.md` に従い USDJPY から照合
2. `parity_log_template.csv` に TV 結果を記入
3. Phase A 100% 一致 → Phase B（guards ON, 34件）
4. 一致後 `near_main_forward_validation_log.csv` で 0.25R 開始

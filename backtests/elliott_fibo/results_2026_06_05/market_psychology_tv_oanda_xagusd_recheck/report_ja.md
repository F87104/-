# TradingView OANDA XAGUSD CSV Recheck

作成日: 2026-06-05

## 結論

この再検証では、TradingView のエクスポートCSVを正として扱う。ローカルPythonの `SILVER` OHLC検証とはシグナル日付が大きくズレたため、XAGUSD/OANDA についてはPython結果をそのまま採用しない。

## TradingView CSV 集計

- 入力CSV: `/Users/asamifujita/Downloads/Market_Psychology_Strategy_(Squeeze_+_Capitulation)_OANDA_XAGUSD_2026-05-30_94cc7.csv`
- Trades: 15
- 勝率: 60.00%
- Net: 124981.04 USD
- PF: 2.896
- Avg: 8332.07 USD
- Median: 20400.33 USD
- Max DD (trade close equity): 43932.04 USD
- Avg hold: 251.7 hours

## 年別

| year | trades | wins | net_usd |
|---:|---:|---:|---:|
| 2018 | 1 | 1 | 20000.13 |
| 2019 | 1 | 1 | 20400.33 |
| 2020 | 1 | 1 | 20808.37 |
| 2021 | 1 | 0 | -10612.10 |
| 2022 | 3 | 3 | 64305.30 |
| 2023 | 2 | 0 | -22186.72 |
| 2024 | 3 | 1 | -508.69 |
| 2025 | 2 | 2 | 44137.87 |
| 2026 | 1 | 0 | -11363.45 |

## Python既存検証との照合

最大一致でも `SQZ_DEFAULT_RR2 / SQZ_DEFAULT_RR15 / SQZ_WIDE_RR2` の **6日/15日** のみ。これは単なる約定時刻ズレではなく、データ元またはTradingView側設定差が大きい可能性を示す。

| strategy | py_trades | common_dates | tv_only | py_only | py_total_r | py_pf |
|---|---:|---:|---:|---:|---:|---:|
| SQZ_DEFAULT_RR15 | 16 | 6 | 9 | 10 | -2.38 | 0.778 |
| SQZ_DEFAULT_RR2 | 16 | 6 | 9 | 10 | 0.62 | 1.058 |
| SQZ_WIDE_RR2 | 16 | 6 | 9 | 10 | 0.62 | 1.058 |
| SQZ_STRICT_RR2 | 7 | 3 | 12 | 4 | 7.33 | 4.475 |
| CAP_STRICT_RR2 | 10 | 0 | 15 | 10 | -4.02 | 0.471 |
| CAP_DEFAULT_RR15 | 42 | 0 | 15 | 42 | -6.01 | 0.785 |
| CAP_DEFAULT_RR2 | 42 | 0 | 15 | 42 | -7.51 | 0.761 |
| CAP_NO_D1_RR2 | 61 | 0 | 15 | 60 | -20.32 | 0.583 |

## 今後の扱い

- TradingView/OANDA XAGUSD は、このCSV結果を基準に再評価する。
- 既存Pythonの `SILVER` 結果は参考値に降格する。
- XAGUSDを本番候補にする場合は、TradingView Strategy Testerから同形式CSVを継続的に出し、同じスクリプトで追跡する。
- Pythonに完全一致させるには、TradingView/OANDAのH4 OHLCそのものをPythonへ取り込む必要がある。

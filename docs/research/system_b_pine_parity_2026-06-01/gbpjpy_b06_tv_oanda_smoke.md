# B06 GBPJPY — TV OANDA 基準スモーク

**執行の正 = TVテスター / Pine CSV 5件**（`python_expected_b06_tv_oanda_gbpjpy_pine_authoritative.csv`）

Python TV-OHLC は **8件**（過検出3）。詳細: `GBPJPY_b06_pine_gap_diagnosis.md`

## Pine 設定

- `pine/research/h4_v_initial_shelf_breakout_strategy.pine`
- OANDA **GBPJPY** / **4H**
- TP: **Signal基準(36d90e6再現)** / 4通貨のみ / PRECALM ON / shelf 6

## 期待シグナル（Pine確定 5件）

| # | signal_time_tv | entry |
|---|----------------|-------|
| 1 | 2016-11-04 22:00 | 129.093 |
| 2 | 2018-07-05 14:00 | 146.432 |
| 3 | 2019-02-19 15:00 | 143.116 |
| 4 | 2020-05-26 06:00 | 131.640 |
| 5 | 2024-10-09 18:00 | 194.818 |

CSV: `python_expected_b06_tv_oanda_gbpjpy_pine_authoritative.csv`

Python研究用8件: `python_expected_b06_tv_oanda_gbpjpy.csv`（2021/2025/2026の3件はTV未確認）

## 旧 F87104 との差

| F87104のみ（TVでは出ない想定） | TV-OHLCのみ |
|-------------------------------|-------------|
| 2016-08-24 08:00 | 2016-11-04 13:00（11/08ではない） |
| 2016-11-08 16:00 | 2018-07-05, 2019-02-19, 2020-05-25, 2021-07-23 |
| 2020-10-09 12:00 | 2025-03-21, 2026-03-23 |
| 2024-10-09 08:00 | 2024-10-09 **09:00**（1本ずれ） |

## TVテスター

USDJPY同様、テスター一覧CSVがあれば `tv_strategy_trades_gbpjpy.csv` に保存 → 再実行で 8/8 照合可能。

再計算: `python3 scripts/run_b06_tv_oanda_parity.py`

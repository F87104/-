# GBPJPY B06 — TV/Pine 照合（確定）

更新: 2026-05-31

## 判定

**執行の正 = TradingView 5件**（Python TV-OHLC 8件は **過検出3件**）

**ユーザー TV チャート確認（2026-05-31）:** 以下3日は **シグナルなし**

| signal_time_tv | TV |
|----------------|-----|
| 2021-07-23 18:00 | なし |
| 2025-03-21 10:00 | なし |
| 2026-03-23 18:00 | なし |

| 系列 | 件数 |
|------|------|
| TV Pine CSV `Initial Shelf Long` | 5 |
| TV ストラテジーテスター | **5**（ユーザー確認） |
| Python TV-OHLC | 8（**本番では使わない**） |

## Pine 確定シグナル（5件）

| # | signal_time_tv | 期待 |
|---|----------------|------|
| 1 | 2016-11-04 22:00:00 | 棚B |
| 2 | 2018-07-05 14:00:00 | 棚B |
| 3 | 2019-02-19 15:00:00 | 棚B |
| 4 | 2020-05-26 06:00:00 | 棚B |
| 5 | 2024-10-09 18:00:00 | 棚B |

CSV: `python_expected_b06_tv_oanda_gbpjpy_pine_authoritative.csv`

## Pythonのみ（Pineに無い — 執行しない）

| signal_time_tv | pair_key | Python R |
|----------------|----------|----------|
| 2021-07-23 18:00:00 | 13263-13282 | -1.02R |
| 2025-03-21 10:00:00 | 18957-18965 | +1.49R |
| 2026-03-23 18:00:00 | 20537-20542 | -1.02R |

CSV: `python_expected_b06_tv_oanda_gbpjpy_python_only.csv`

**原因:** Pivot/V文脈または棚条件の **Pine↔Python 実装差**（ポジション重複ではない）。GBPJPY は **Pine 優先**。

## 運用

- フォワードログ・実弾は **上記5シグナル時刻のみ**
- `python_expected_b06_tv_oanda_gbpjpy.csv`（8件）は研究用。本番照合は `*_pine_authoritative.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`

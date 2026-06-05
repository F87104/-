# EURJPY B06 — TVチャート CSV と Python 照合

更新: 2026-05-31

## データ

- ソース: `OANDA_EURJPY, 240_b8f7b.csv` → `tv_eurjpy_h4.csv`
- Pine: `h4_v_initial_shelf_breakout_strategy.pine`（チャートに載せた状態でエクスポート）
- 照合列: **`Initial Shelf Long` = 1**

## 結果

| 系列 | 件数 |
|------|------|
| TV Pine（CSV列） | **9** |
| Python TV-OHLC | **9** |
| **signal_time_tv 一致** | **9/9 OK** |

## TV Pine シグナル（表示時刻 UTC+9）

| signal_time_tv |
|----------------|
| 2016-08-30 18:00:00 |
| 2016-10-04 06:00:00 |
| 2018-05-22 14:00:00 |
| 2018-07-03 14:00:00 |
| 2022-08-30 22:00:00 |
| 2023-06-09 10:00:00 |
| 2023-11-02 18:00:00 |
| 2025-04-11 14:00:00 |
| 2026-03-25 06:00:00 |

**判定: EURJPY B06 — Pine ラベルと Python 期待値が完全一致。**

再現: `python3 scripts/run_b06_tv_oanda_parity.py`

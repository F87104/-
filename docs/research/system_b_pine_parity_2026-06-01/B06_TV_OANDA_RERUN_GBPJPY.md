# B06 GBPJPY — TV OANDA データでの Python 再実行

## 目的

TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。

## 件数

| 系列 | 件数 |
|------|------|
| F87104 H1→H4（従来） | **4** |
| TV OANDA H4 CSV（今回） | **8** |
| 同一 signal_time | **0** |
| TVテスターと1日以内（TV-OHLC Python） | **0/8** |

## F87104 vs TV-OHLC Python

**F87104のみ:**
- GBPJPY|2016-08-24 08:00:00
- GBPJPY|2016-11-08 16:00:00
- GBPJPY|2020-10-09 12:00:00
- GBPJPY|2024-10-09 08:00:00

**TV-OHLC Pythonのみ:**
- GBPJPY|2016-11-04 13:00:00
- GBPJPY|2018-07-05 05:00:00
- GBPJPY|2019-02-19 06:00:00
- GBPJPY|2020-05-25 21:00:00
- GBPJPY|2021-07-23 09:00:00
- GBPJPY|2024-10-09 09:00:00
- GBPJPY|2025-03-21 01:00:00
- GBPJPY|2026-03-23 09:00:00

## 次の作業（Pine）

1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか
2. 無い日は `showSkips=ON` で skipCode を記録
3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す
4. ストラテジーテスター件数も同じ signal に揃うか確認

## ファイル

- `python_expected_b06_tv_oanda_gbpjpy.csv`
- `b06_f87104_vs_tv_oanda_gbpjpy.csv`
- `b06_tv_oanda_vs_tester_gbpjpy.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`
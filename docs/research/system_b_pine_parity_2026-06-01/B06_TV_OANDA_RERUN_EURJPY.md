# B06 EURJPY — TV OANDA データでの Python 再実行

## 目的

TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。

## 件数

| 系列 | 件数 |
|------|------|
| F87104 H1→H4（従来） | **10** |
| TV OANDA H4 CSV（今回） | **9** |
| 同一 signal_time | **0** |
| TVテスターと1日以内（TV-OHLC Python） | **0/9** |

## F87104 vs TV-OHLC Python

**F87104のみ:**
- EURJPY|2015-04-27 12:00:00
- EURJPY|2015-05-29 08:00:00
- EURJPY|2016-10-03 20:00:00
- EURJPY|2017-03-03 08:00:00
- EURJPY|2019-01-29 08:00:00
- EURJPY|2022-06-02 08:00:00
- EURJPY|2022-06-24 12:00:00
- EURJPY|2023-08-07 12:00:00
- EURJPY|2025-06-03 00:00:00
- EURJPY|2026-03-24 16:00:00

**TV-OHLC Pythonのみ:**
- EURJPY|2016-08-30 09:00:00
- EURJPY|2016-10-03 21:00:00
- EURJPY|2018-05-22 05:00:00
- EURJPY|2018-07-03 05:00:00
- EURJPY|2022-08-30 13:00:00
- EURJPY|2023-06-09 01:00:00
- EURJPY|2023-11-02 09:00:00
- EURJPY|2025-04-11 05:00:00
- EURJPY|2026-03-24 21:00:00

## 次の作業（Pine）

1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか
2. 無い日は `showSkips=ON` で skipCode を記録
3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す
4. ストラテジーテスター件数も同じ signal に揃うか確認

## ファイル

- `python_expected_b06_tv_oanda_eurjpy.csv`
- `b06_f87104_vs_tv_oanda_eurjpy.csv`
- `b06_tv_oanda_vs_tester_eurjpy.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`
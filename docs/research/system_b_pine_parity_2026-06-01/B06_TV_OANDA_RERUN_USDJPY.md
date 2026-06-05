# B06 USDJPY — TV OANDA データでの Python 再実行

## 目的

TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。

## 件数

| 系列 | 件数 |
|------|------|
| F87104 H1→H4（従来） | **13** |
| TV OANDA H4 CSV（今回） | **9** |
| 同一 signal_time | **0** |
| TVテスターと1日以内（TV-OHLC Python） | **9/9** |

## F87104 vs TV-OHLC Python

**F87104のみ:**
- USDJPY|2016-10-03 20:00:00
- USDJPY|2018-11-12 00:00:00
- USDJPY|2020-11-11 12:00:00
- USDJPY|2021-02-01 08:00:00
- USDJPY|2021-08-09 16:00:00
- USDJPY|2021-11-12 00:00:00
- USDJPY|2023-08-01 08:00:00
- USDJPY|2023-10-25 16:00:00
- USDJPY|2024-02-05 12:00:00
- USDJPY|2024-06-19 16:00:00
- USDJPY|2024-09-24 04:00:00
- USDJPY|2025-07-07 00:00:00
- USDJPY|2025-09-24 04:00:00

**TV-OHLC Pythonのみ:**
- USDJPY|2018-11-06 14:00:00
- USDJPY|2018-12-11 22:00:00
- USDJPY|2020-07-02 09:00:00
- USDJPY|2021-02-01 10:00:00
- USDJPY|2021-11-11 22:00:00
- USDJPY|2022-07-20 21:00:00
- USDJPY|2023-10-25 13:00:00
- USDJPY|2024-06-19 17:00:00
- USDJPY|2025-05-28 13:00:00

## 次の作業（Pine）

1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか
2. 無い日は `showSkips=ON` で skipCode を記録
3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す
4. ストラテジーテスター件数も同じ signal に揃うか確認

## ファイル

- `python_expected_b06_tv_oanda_usdjpy.csv`
- `b06_f87104_vs_tv_oanda_usdjpy.csv`
- `b06_tv_oanda_vs_tester_usdjpy.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`
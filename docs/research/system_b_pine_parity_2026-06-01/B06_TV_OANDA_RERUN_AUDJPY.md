# B06 AUDJPY — TV OANDA データでの Python 再実行

## 目的

TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。

## 件数

| 系列 | 件数 |
|------|------|
| F87104 H1→H4（従来） | **7** |
| TV OANDA H4 CSV（今回） | **11** |
| 同一 signal_time | **0** |
| TVテスターと1日以内（TV-OHLC Python） | **11/11** |

## F87104 vs TV-OHLC Python

**F87104のみ:**
- AUDJPY|2015-11-18 20:00:00
- AUDJPY|2016-03-04 04:00:00
- AUDJPY|2016-10-03 16:00:00
- AUDJPY|2019-04-05 00:00:00
- AUDJPY|2021-02-05 08:00:00
- AUDJPY|2024-03-25 12:00:00
- AUDJPY|2025-03-17 04:00:00

**TV-OHLC Pythonのみ:**
- AUDJPY|2015-01-19 22:00:00
- AUDJPY|2016-02-01 18:00:00
- AUDJPY|2016-09-28 17:00:00
- AUDJPY|2016-10-03 17:00:00
- AUDJPY|2018-11-01 01:00:00
- AUDJPY|2019-07-22 09:00:00
- AUDJPY|2020-05-14 17:00:00
- AUDJPY|2020-07-19 21:00:00
- AUDJPY|2021-04-05 21:00:00
- AUDJPY|2021-07-06 01:00:00
- AUDJPY|2023-07-25 01:00:00

## 次の作業（Pine）

1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか
2. 無い日は `showSkips=ON` で skipCode を記録
3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す
4. ストラテジーテスター件数も同じ signal に揃うか確認

## ファイル

- `python_expected_b06_tv_oanda_audjpy.csv`
- `b06_f87104_vs_tv_oanda_audjpy.csv`
- `b06_tv_oanda_vs_tester_audjpy.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`
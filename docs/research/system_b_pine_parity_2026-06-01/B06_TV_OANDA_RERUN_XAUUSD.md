# B06 XAUUSD — TV OANDA データでの Python 再実行

## 目的

TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。

## 件数

| 系列 | 件数 |
|------|------|
| F87104 H1→H4（従来） | **0** |
| TV OANDA H4 CSV（今回） | **9** |
| 同一 signal_time | **0** |
| TVテスターと1日以内（TV-OHLC Python） | **0/9** |

## F87104 vs TV-OHLC Python

## 次の作業（Pine）

1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか
2. 無い日は `showSkips=ON` で skipCode を記録
3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す
4. ストラテジーテスター件数も同じ signal に揃うか確認

## ファイル

- `python_expected_b06_tv_oanda_xauusd.csv`
- `b06_f87104_vs_tv_oanda_xauusd.csv`
- `b06_tv_oanda_vs_tester_xauusd.csv`

再現: `python3 scripts/run_b06_tv_oanda_parity.py`
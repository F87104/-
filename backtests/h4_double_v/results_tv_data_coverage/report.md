# H4 Double V — TradingView OHLC coverage

- Checked: `/workspace/data/raw/tv_oanda/h4`
- Period filter for count: 2015-01-01 → 2026-12-31

| symbol | status | rows | bars_2015_2026 | median_minutes | start | end |
| --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | missing | 0 | 0 |  |  |  |
| USDJPY | missing | 0 | 0 |  |  |  |
| EURJPY | missing | 0 | 0 |  |  |  |
| CHFJPY | missing | 0 | 0 |  |  |  |
| AUDJPY | missing | 0 | 0 |  |  |  |
| XAUUSD | missing | 0 | 0 |  |  |  |

## Missing symbols

Export from TradingView (OANDA, **H4**, same date range as Strategy Tester):

```
Chart → Export chart data → time,open,high,low,close
```

Place files under:

```
data/raw/tv_oanda/h4/GBPJPY_H4.csv
data/raw/tv_oanda/h4/USDJPY_H4.csv
...
```

Or upload to repo root as `OANDA_GBPJPY, 240_xxxx.csv` and rerun.
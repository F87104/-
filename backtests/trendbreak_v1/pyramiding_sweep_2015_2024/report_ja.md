# TrendBreakV1 HYBRID Same-Direction Pyramiding Sweep

- Period: `2015-01-01` to `2024-12-31`
- Data: local `F87104_test` H1 OHLC
- Cost: spread + slippage table used in prior audit scripts
- Entry: next bar open after confirmed signal close
- Add-on rule: same direction only, opposite direction blocked
- Basket SL/TP: recalculated from average entry after each add-on
- High-vol filter: ATR14 > SMA(ATR14,100) x 2 blocks new entries
- DD stop approximation: 20% with 1R ~= 1%

## Best By Symbol

| Symbol | Best Profit Max Entries | Profit R | WR | Entries | Baskets | Best WR Max Entries | Best WR | WR Profit R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XAUUSD | 2 | 53.91 | 44.74% | 76 | 75 | 2 | 44.74% | 53.91 |
| USDJPY | 1 | 29.91 | 37.50% | 64 | 64 | 1 | 37.50% | 29.91 |
| EURJPY | 1 | 11.42 | 30.91% | 55 | 55 | 1 | 30.91% | 11.42 |
| GBPJPY | 2 | 41.87 | 43.33% | 60 | 59 | 2 | 43.33% | 41.87 |
| CHFJPY | 2 | 26.50 | 36.36% | 66 | 64 | 2 | 36.36% | 26.50 |
| AUDJPY | 1 | -3.08 | 25.00% | 80 | 80 | 1 | 25.00% | -3.08 |
| SILVER | 1 | 36.62 | 43.75% | 64 | 64 | 1 | 43.75% | 36.62 |

## Overall By Max Entries

| Max Entries | Entries | Baskets | WR | Profit R | PF | Max DD R |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 461 | 461 | 36.88% | 191.53 | 1.624 | 18.27 |
| 2 | 465 | 461 | 37.20% | 197.15 | 1.640 | 18.27 |
| 3 | 465 | 461 | 37.20% | 197.15 | 1.640 | 18.27 |
| 4 | 465 | 461 | 37.20% | 197.15 | 1.640 | 18.27 |
| 5 | 465 | 461 | 37.20% | 197.15 | 1.640 | 18.27 |

## Notes

- `entries` counts each add-on entry as one closed leg.
- `baskets` counts one campaign from first entry until aggregate SL/TP exit.
- The result is a research approximation, not a TradingView broker emulator clone.

## Output Files

- `pyramiding_trades.csv`
- `summary_by_symbol_entries.csv`
- `best_by_profit.csv`
- `best_by_win_rate.csv`
- `overall_by_entries.csv`
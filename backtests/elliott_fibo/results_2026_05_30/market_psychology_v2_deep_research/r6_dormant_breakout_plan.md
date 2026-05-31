Dormant Breakout (Pattern 10)

Goal: catch breakouts of long-untouched levels.

Signal definition (proposed):
  1. Donchian-N high or low untouched for N bars (N in [120, 360, 1250])
  2. Close breaks the level (no wick-only)
  3. After break, 5-bar pullback that holds above the level (long) / below (short)
  4. Re-break of the prior 5-bar high / low

Entry: next bar open after re-break
SL: opposite side of the 5-bar pullback - 0.25 * ATR
TP: 2R
Max hold: 240 bars

Why dormant?  Long-untouched levels accumulate stop orders (sell stops below
multi-year low, buy stops above multi-year high).  Breaking them releases
liquidity and accelerates the move.

Requires OHLC scan and Donchian computation; not feasible here.  Sketch a
Pine implementation in pine/research/market_psychology_dormant_breakout_strategy.pine
(future).

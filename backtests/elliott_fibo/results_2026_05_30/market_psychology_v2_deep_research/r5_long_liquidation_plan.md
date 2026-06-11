Long Liquidation (short side, mirror of Short Squeeze)

Goal: detect 'buyers giving up' after a rally.
Signal definition (proposed):
  1. Sharp rally:    last 6 bars high - last 12 bars low >= 3 * ATR
  2. Failure to make new high after the rally (within 6 bars)
  3. Upper shelf:   6-bar range <= 2.0 * ATR formed at the rally top
  4. Break:         close < shelfLow

Entry: next bar open, short
SL: shelfHigh + 0.25 * ATR
TP: 2R
Max hold: 120 bars
Currency filter:  exclude GBPJPY (likely mirror imbalance)

Why mirror of SHORT_SQUEEZE failed in earlier studies:
  - In long-direction crashes the new short positions trapped at the bottom
    are forced to cover.  At the top the new long positions trapped at the top
    are NOT forced (they can hold, set wider stops, etc.).
  - That is why we need 'failure to make new high' + 'volume divergence'
    (TV-only) as additional rigor on the short side.

Requires OHLC scan; not feasible in this post-hoc analysis.  See Pine sketch
in pine/research/market_psychology_long_liquidation_strategy.pine (future).

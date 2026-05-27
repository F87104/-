# SILVER/XAGUSD H1 Short: M15 Execution Audit

## Coverage

| m15_start | m15_end | m15_rows | h1_guard_trades_all | h1_guard_trades_in_m15_range | h1_range_total_r | h1_range_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| 2013-12-31 21:45:00 | 2026-05-22 20:45:00 | 291760 | 27 | 27 | 12.410 | 77.778 |

## Execution Variants

| variant | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mae_r | avg_mfe_r | avg_risk_atr | tp | sl | time | early |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m15_open | 27 | 77.778 | 12.951 | 0.480 | 2.838 | 1.573 | 0.695 | 1.245 | 1.818 | 20 | 5 | 2 | 0 |
| m15_retest_025r_2h | 17 | 88.235 | 11.416 | 0.672 | 4.759 | 1.764 | 0.478 | 1.337 | 1.288 | 15 | 2 | 0 | 0 |
| m15_retest_box_1h | 16 | 81.250 | 8.733 | 0.546 | 3.182 | 2.386 | 0.662 | 1.458 | 1.458 | 13 | 3 | 0 | 0 |
| m15_bear_confirm_1h | 12 | 75.000 | 5.778 | 0.482 | 2.680 | 1.354 | 0.828 | 1.216 | 1.749 | 9 | 3 | 0 | 0 |
| m15_open_no_progress_exit | 27 | 25.926 | -3.332 | -0.123 | 0.677 | 4.495 | 0.476 | 0.525 | 1.818 | 7 | 3 | 1 | 16 |

## Read

- M15 local coverage is 2013-12-31 21:45:00 to 2026-05-22 20:45:00 across 291,760 rows; H1 guard coverage is 27/27 trades.
- The H1 setup is fixed to the practical guard rule: pullback rebreak, box 8, H4 down, ex 11/12, TP 1.2R.
- `m15_open` matches the H1 next-open idea but uses M15 candles for intrabar exit ordering.
- Retest entries reduced risk and improved MFE, but also reduced trade count when the retest did not happen.
- Early no-progress exit damaged the edge: two trades that eventually reached TP were cut too early.

## Practical Implication

- Do not add an automatic 1-hour early exit to SILVER yet.
- M15 can be useful for a better entry if price retests upward, but skipping non-retest trades must be tested on the full 2014-2026 sample.
- Current evidence still favors H1 as the decision timeframe and M15 as an execution aid only.
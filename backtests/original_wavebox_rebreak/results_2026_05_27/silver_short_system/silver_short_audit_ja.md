# SILVER H1 Short Candidate Audit

## Candidate Comparison

| name | trades | win_rate | total_r | avg_r | pf | max_dd_r | oos_trades | oos_r | oos_2025_trades | oos_2025_r | ex_2026_r | worst_year_r | worst_2y_r | avg_mae_r | same_bar_ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aggressive_ex_7_11_12 | 25 | 80.00 | 13.00 | 0.52 | 3.20 | 1.27 | 3 | 3.52 | 1 | 1.15 | 10.63 | -1.18 | 0.84 | 0.76 | 0 |
| loose_close65_guard_ex_11_12 | 30 | 76.67 | 12.42 | 0.41 | 2.41 | 2.48 | 3 | 3.52 | 1 | 1.15 | 10.05 | -1.50 | 0.84 | 0.76 | 0 |
| guard_ex_11_12 | 27 | 77.78 | 12.41 | 0.46 | 2.66 | 1.57 | 3 | 3.52 | 1 | 1.15 | 10.04 | -0.41 | 0.84 | 0.78 | 0 |
| maxhold12_guard_ex_11_12 | 27 | 62.96 | 9.17 | 0.34 | 2.20 | 1.57 | 3 | 3.52 | 1 | 1.15 | 6.80 | -0.63 | 0.68 | 0.74 | 0 |
| core_no_time | 31 | 67.74 | 8.44 | 0.27 | 1.74 | 3.61 | 3 | 3.52 | 1 | 1.15 | 6.07 | -1.44 | 0.01 | 0.81 | 0 |
| tp1_guard_ex_11_12 | 27 | 77.78 | 8.41 | 0.31 | 2.12 | 1.57 | 3 | 2.92 | 1 | 0.95 | 6.44 | -0.61 | 0.24 | 0.78 | 0 |
| strict_pullback_1_0 | 21 | 66.67 | 6.13 | 0.29 | 1.78 | 2.53 | 3 | 3.52 | 1 | 1.15 | 3.76 | -1.27 | -0.81 | 0.81 | 0 |

## Cost Stress

| name | spread | slip | trades | win_rate | total_r | pf | max_dd_r | oos_r | worst_year_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aggressive_ex_7_11_12 | 0.03 | 0.01 | 25 | 80.00 | 13.00 | 3.20 | 1.27 | 3.52 | -1.18 |
| aggressive_ex_7_11_12 | 0.05 | 0.02 | 25 | 76.00 | 9.03 | 2.34 | 1.58 | 3.45 | -1.32 |
| aggressive_ex_7_11_12 | 0.08 | 0.03 | 25 | 72.00 | 4.07 | 1.52 | 2.02 | 3.37 | -1.51 |
| aggressive_ex_7_11_12 | 0.12 | 0.05 | 25 | 52.00 | -3.87 | 0.67 | 6.14 | 3.24 | -2.49 |
| core_no_time | 0.03 | 0.01 | 31 | 67.74 | 8.44 | 1.74 | 3.61 | 3.52 | -1.44 |
| core_no_time | 0.05 | 0.02 | 31 | 64.52 | 3.21 | 1.24 | 4.57 | 3.45 | -1.96 |
| core_no_time | 0.08 | 0.03 | 31 | 61.29 | -3.32 | 0.79 | 8.37 | 3.37 | -2.60 |
| core_no_time | 0.12 | 0.05 | 31 | 45.16 | -13.77 | 0.37 | 18.05 | 3.24 | -3.64 |
| guard_ex_11_12 | 0.03 | 0.01 | 27 | 77.78 | 12.41 | 2.66 | 1.57 | 3.52 | -0.41 |
| guard_ex_11_12 | 0.05 | 0.02 | 27 | 74.07 | 7.80 | 1.89 | 2.03 | 3.45 | -0.90 |
| guard_ex_11_12 | 0.08 | 0.03 | 27 | 70.37 | 2.05 | 1.20 | 3.25 | 3.37 | -1.72 |
| guard_ex_11_12 | 0.12 | 0.05 | 27 | 51.85 | -7.17 | 0.53 | 11.45 | 3.24 | -3.50 |
| loose_close65_guard_ex_11_12 | 0.03 | 0.01 | 30 | 76.67 | 12.42 | 2.41 | 2.48 | 3.52 | -1.50 |
| loose_close65_guard_ex_11_12 | 0.05 | 0.02 | 30 | 73.33 | 7.32 | 1.71 | 2.99 | 3.45 | -2.06 |
| loose_close65_guard_ex_11_12 | 0.08 | 0.03 | 30 | 66.67 | 0.96 | 1.08 | 5.24 | 3.37 | -2.77 |
| loose_close65_guard_ex_11_12 | 0.12 | 0.05 | 30 | 50.00 | -9.23 | 0.48 | 13.51 | 3.24 | -3.89 |
| maxhold12_guard_ex_11_12 | 0.03 | 0.01 | 27 | 62.96 | 9.17 | 2.20 | 1.57 | 3.52 | -0.63 |
| maxhold12_guard_ex_11_12 | 0.05 | 0.02 | 27 | 62.96 | 4.57 | 1.48 | 2.03 | 3.45 | -0.95 |
| maxhold12_guard_ex_11_12 | 0.08 | 0.03 | 27 | 59.26 | -1.19 | 0.90 | 3.90 | 3.37 | -1.72 |
| maxhold12_guard_ex_11_12 | 0.12 | 0.05 | 27 | 40.74 | -10.40 | 0.40 | 12.39 | 3.24 | -3.50 |
| strict_pullback_1_0 | 0.03 | 0.01 | 21 | 66.67 | 6.13 | 1.78 | 2.53 | 3.52 | -1.27 |
| strict_pullback_1_0 | 0.05 | 0.02 | 21 | 66.67 | 2.54 | 1.27 | 3.21 | 3.45 | -1.49 |
| strict_pullback_1_0 | 0.08 | 0.03 | 21 | 61.90 | -1.94 | 0.82 | 5.33 | 3.37 | -1.75 |
| strict_pullback_1_0 | 0.12 | 0.05 | 21 | 52.38 | -9.11 | 0.40 | 10.61 | 3.24 | -3.50 |
| tp1_guard_ex_11_12 | 0.03 | 0.01 | 27 | 77.78 | 8.41 | 2.12 | 1.57 | 2.92 | -0.61 |
| tp1_guard_ex_11_12 | 0.05 | 0.02 | 27 | 74.07 | 3.80 | 1.43 | 2.03 | 2.85 | -1.10 |
| tp1_guard_ex_11_12 | 0.08 | 0.03 | 27 | 66.67 | -1.95 | 0.82 | 5.86 | 2.77 | -2.12 |
| tp1_guard_ex_11_12 | 0.12 | 0.05 | 27 | 44.44 | -11.17 | 0.32 | 14.45 | 2.64 | -3.90 |

## Key Findings

- The robust core is not upside exhaustion. It is H4-down pullback compression rebreak.
- The best score uses `ex_7_11_12`, but this is more likely overfit. `ex_11_12` is a safer operational guard.
- Without any time filter, the same structural setup remains positive but weaker.
- OOS has only three trades, so the strategy is not production-grade yet.
- All simulations are conservative for same-bar SL/TP: SL wins when both are touched.
- The 2026 silver price regime is very different from prior years; results should be checked separately.

## Additional Manual Tests

### H4 slope filter

Adding `H4 slope <= -0.20 ATR` to `guard_ex_11_12` improved the headline:

- 22 trades / win rate 81.82% / +11.58R / PF 3.28 / DD 1.57R

But it removed the 2025 winner, leaving OOS effectively dependent on 2026.  This is useful as a quality label, not yet safe as a formal production filter.

### Adverse-exit test

Forcing an exit at adverse excursion worsened results:

- 0.6R adverse exit: 27 trades / +0.64R / PF 1.05
- 0.8R adverse exit: 27 trades / +5.84R / PF 1.52
- no adverse exit: 27 trades / +12.41R / PF 2.66

Silver often breathes against the position before continuing lower.  Early adverse exit should be an alert only, not a forced exit.

### Breakeven test

Moving stop to breakeven after partial profit also worsened results:

- BE after 0.4R: -5.16R
- BE after 0.6R: -1.56R
- BE after 0.8R: +5.04R
- BE after 1.0R: +7.61R
- no BE: +12.41R

The method needs room.  Premature defensive management destroys the edge.

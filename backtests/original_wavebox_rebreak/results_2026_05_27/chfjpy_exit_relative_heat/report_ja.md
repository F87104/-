# CHFJPY Exit / Relative Heat Research

## 1. Adverse Exit

| label | trades | win_rate | total_r | avg_r | pf | max_dd_r | worst_year_r | worst_2y_r | oos_trades | oos_r | adverse_exit_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base24_no_ae | 30 | 76.67 | 8.25 | 0.28 | 2.06 | 1.18 | -0.44 | -0.44 | 4 | 1.03 |  |
| base12_no_ae | 30 | 73.33 | 7.22 | 0.24 | 1.89 | 1.86 | -1.38 | -1.19 | 4 | 1.03 |  |
| base24_no_ae_ae0.9 | 30 | 70.00 | 5.55 | 0.19 | 1.61 | 2.13 | -0.71 | -0.96 | 4 | 1.13 | 0.90 |
| base12_no_ae_ae0.9 | 30 | 66.67 | 4.52 | 0.15 | 1.48 | 2.38 | -1.28 | -1.99 | 4 | 1.13 | 0.90 |
| base24_no_ae_ae0.8 | 30 | 60.00 | 1.65 | 0.06 | 1.15 | 2.01 | -1.27 | -1.44 | 4 | 1.23 | 0.80 |
| base12_no_ae_ae0.8 | 30 | 56.67 | 0.62 | 0.02 | 1.05 | 2.01 | -1.27 | -1.59 | 4 | 1.23 | 0.80 |
| base24_no_ae_ae0.6 | 30 | 50.00 | -0.15 | -0.00 | 0.99 | 1.97 | -1.21 | -1.94 | 4 | 1.43 | 0.60 |
| base12_no_ae_ae0.6 | 30 | 46.67 | -1.18 | -0.04 | 0.89 | 3.00 | -1.21 | -2.19 | 4 | 1.43 | 0.60 |
| base24_no_ae_ae0.7 | 30 | 50.00 | -1.65 | -0.05 | 0.87 | 2.88 | -1.61 | -2.44 | 4 | 1.33 | 0.70 |
| base12_no_ae_ae0.7 | 30 | 46.67 | -2.68 | -0.09 | 0.79 | 3.91 | -1.61 | -2.69 | 4 | 1.33 | 0.70 |

## 2. Relative JPY-Cross Heat Filters

| label | trades | win_rate | total_r | avg_r | pf | max_dd_r | worst_year_r | worst_2y_r | oos_trades | oos_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| usd_up_6h | 20 | 85.00 | 8.36 | 0.42 | 3.45 | 1.63 | -0.53 | -0.90 | 4 | 1.03 |
| usd_not_down_6h | 20 | 85.00 | 8.36 | 0.42 | 3.45 | 1.63 | -0.53 | -0.90 | 4 | 1.03 |
| base | 30 | 76.67 | 8.25 | 0.28 | 2.06 | 1.18 | -0.44 | -0.44 | 4 | 1.03 |
| other_preheated | 30 | 76.67 | 8.25 | 0.28 | 2.06 | 1.18 | -0.44 | -0.44 | 4 | 1.03 |
| usd_up_and_chf_rel | 16 | 87.50 | 7.61 | 0.48 | 4.41 | 1.13 | -0.44 | -0.44 | 4 | 1.03 |
| chf_relative_bb_pos | 26 | 76.92 | 7.50 | 0.29 | 2.14 | 1.16 | -0.44 | -0.44 | 4 | 1.03 |
| chf_relative_cross_bb_pos | 26 | 76.92 | 7.50 | 0.29 | 2.14 | 1.16 | -0.44 | -0.44 | 4 | 1.03 |
| preheated_and_chf_rel | 26 | 76.92 | 7.50 | 0.29 | 2.14 | 1.16 | -0.44 | -0.44 | 4 | 1.03 |
| broad_yen_heat | 20 | 80.00 | 6.77 | 0.34 | 2.52 | 1.63 | -0.53 | -0.90 | 4 | 1.03 |
| chf_highest_bb_cross4 | 17 | 82.35 | 6.64 | 0.39 | 3.04 | 1.50 | -0.48 | -0.83 | 1 | 0.76 |
| cross_yen_heat | 22 | 77.27 | 6.33 | 0.29 | 2.15 | 1.18 | -0.44 | -0.44 | 4 | 1.03 |
| broad_heat_and_chf_rel | 16 | 81.25 | 6.02 | 0.38 | 2.84 | 1.13 | -0.44 | -0.44 | 4 | 1.03 |
| chf_highest_bb_all5 | 16 | 81.25 | 5.98 | 0.37 | 2.84 | 1.50 | -0.48 | -0.83 | 1 | 0.76 |
| usd_up_and_chf_highest_cross | 8 | 100.00 | 5.65 | 0.71 | inf | 0.00 | 0.65 | 0.65 | 1 | 0.76 |
| usd_down_6h | 10 | 60.00 | -0.11 | -0.01 | 0.98 | 2.59 | -1.05 | -1.73 | 0 | 0.00 |

## 2b. Relative Heat Buckets

| axis | bucket | label | trades | win_rate | total_r | avg_r | pf | max_dd_r | worst_year_r | worst_2y_r | oos_trades | oos_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| usd_ret6 | USD down | USD down | 10 | 60.00 | -0.11 | -0.01 | 0.98 | 2.59 | -1.05 | -1.73 | 0 | 0.00 |
| usd_ret6 | USD up | USD up | 20 | 85.00 | 8.36 | 0.42 | 3.45 | 1.63 | -0.53 | -0.90 | 4 | 1.03 |
| chf_minus_other_bb | slightly lower | slightly lower | 4 | 75.00 | 0.75 | 0.19 | 1.63 | 1.18 | -1.18 | -1.18 | 0 | 0.00 |
| chf_minus_other_bb | slightly higher | slightly higher | 5 | 100.00 | 3.55 | 0.71 | inf | 0.00 | 0.65 | 0.65 | 0 | 0.00 |
| chf_minus_other_bb | much higher | much higher | 21 | 71.43 | 3.96 | 0.19 | 1.60 | 2.21 | -1.05 | -1.54 | 4 | 1.03 |
| chf_bb_rank_cross4 | 1 | 1 | 17 | 82.35 | 6.64 | 0.39 | 3.04 | 1.50 | -0.48 | -0.83 | 1 | 0.76 |
| chf_bb_rank_cross4 | 2 | 2 | 8 | 75.00 | 1.99 | 0.25 | 1.90 | 1.11 | -1.11 | -1.11 | 2 | 1.39 |
| chf_bb_rank_cross4 | 3 | 3 | 3 | 66.67 | 0.17 | 0.06 | 1.15 | 1.13 | -1.13 | -1.13 | 1 | -1.13 |
| chf_bb_rank_cross4 | 4 | 4 | 2 | 50.00 | -0.55 | -0.27 | 0.54 | 1.18 | -1.18 | -1.18 | 0 | 0.00 |
| other_preheated | preheated | preheated | 30 | 76.67 | 8.25 | 0.28 | 2.06 | 1.18 | -0.44 | -0.44 | 4 | 1.03 |

## 3. Monthly USDJPY / CHFJPY Relation

| monthly_corr | usd_total_r | chf_base24_total_r | combined_total_r | usd_monthly_dd | chf_monthly_dd | combined_monthly_dd |
| --- | --- | --- | --- | --- | --- | --- |
| -0.16 | 41.47 | 8.25 | 49.72 | 3.13 | 2.99 | 3.13 |

## Notes

- Adverse exit is applied to the same entry set to isolate exit-rule impact.
- Relative heat is evaluated at the signal candle close.
- Intrabar adverse-vs-TP ambiguity is handled conservatively: adverse exit first.
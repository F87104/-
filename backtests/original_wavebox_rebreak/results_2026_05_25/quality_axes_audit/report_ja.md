# USDJPY H1 WaveBox Quality Axes Audit

## 結論

- A+は最優先で打つ候補。
- Aは無条件ではなく、Box位置・ブレイク足・直近フェーズがきれいなものを優先する。
- StrictのBは観察または小ロット。ExpansionのBは捨てる。
- 1波をBalancedへ緩めるのは許容範囲。戻し上限を82%へ広げるとBが弱くなる。

## Mode Summary

| mode | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | tp_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Expansion88 | 88 | 61.36 | 44.28 | 0.50 | 2.27 | 4.17 | 4 | 61.36 |
| Balanced | 73 | 64.38 | 42.31 | 0.58 | 2.59 | 3.13 | 3 | 64.38 |
| Strict | 69 | 65.22 | 41.47 | 0.60 | 2.69 | 3.13 | 3 | 65.22 |

## Rank Summary

| mode | rank | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | tp_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Balanced | A | 27 | 62.96 | 14.48 | 0.54 | 2.39 | 2.11 | 2 | 62.96 |
| Balanced | A+ | 24 | 70.83 | 18.08 | 0.75 | 3.62 | 2.08 | 2 | 70.83 |
| Balanced | B | 22 | 59.09 | 9.75 | 0.44 | 2.04 | 2.11 | 2 | 59.09 |
| Expansion88 | A | 35 | 60.00 | 16.21 | 0.46 | 2.12 | 4.16 | 4 | 60.00 |
| Expansion88 | A+ | 25 | 72.00 | 19.57 | 0.78 | 3.83 | 2.08 | 2 | 72.00 |
| Expansion88 | B | 28 | 53.57 | 8.50 | 0.30 | 1.63 | 3.36 | 3 | 53.57 |
| Strict | A | 25 | 64.00 | 14.08 | 0.56 | 2.50 | 2.11 | 2 | 64.00 |
| Strict | A+ | 23 | 69.57 | 16.61 | 0.72 | 3.41 | 2.08 | 2 | 69.57 |
| Strict | B | 21 | 61.90 | 10.78 | 0.51 | 2.30 | 2.11 | 2 | 61.90 |

## Quality Axis Summary

| mode | axis | bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | tp_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Balanced | action_class | GO_A_PLUS | 24 | 70.83 | 18.08 | 0.75 | 3.62 | 2.08 | 2 | 70.83 |
| Balanced | action_class | GO_CLEAN_A | 15 | 66.67 | 9.48 | 0.63 | 2.81 | 3.18 | 3 | 66.67 |
| Balanced | action_class | SELECTIVE_A | 12 | 58.33 | 5.00 | 0.42 | 1.97 | 3.12 | 3 | 58.33 |
| Balanced | box_position | bottom | 27 | 66.67 | 17.46 | 0.65 | 2.93 | 3.18 | 3 | 66.67 |
| Balanced | box_position | late | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Balanced | box_position | low-mid | 22 | 63.64 | 12.18 | 0.55 | 2.47 | 2.08 | 2 | 63.64 |
| Balanced | box_position | mid-high | 2 | 100.00 | 2.92 | 1.46 | inf | 0.00 | 0 | 100.00 |
| Balanced | break_quality | ok_close | 15 | 66.67 | 9.42 | 0.63 | 2.81 | 4.16 | 4 | 66.67 |
| Balanced | break_quality | strong_close | 24 | 70.83 | 17.72 | 0.74 | 3.43 | 3.18 | 3 | 70.83 |
| Balanced | break_quality | weak_or_wick | 12 | 58.33 | 5.42 | 0.45 | 2.12 | 2.08 | 2 | 58.33 |
| Balanced | h4_state | align | 40 | 60.00 | 18.88 | 0.47 | 2.16 | 4.18 | 4 | 60.00 |
| Balanced | h4_state | neutral | 3 | 100.00 | 4.38 | 1.46 | inf | 0.00 | 0 | 100.00 |
| Balanced | h4_state | oppose | 8 | 87.50 | 9.30 | 1.16 | 10.10 | 1.02 | 1 | 87.50 |
| Balanced | recent_phase | early | 12 | 66.67 | 7.99 | 0.67 | 3.09 | 2.13 | 2 | 66.67 |
| Balanced | recent_phase | late_or_chase | 17 | 64.71 | 9.84 | 0.58 | 2.58 | 3.11 | 3 | 64.71 |
| Balanced | recent_phase | normal | 22 | 68.18 | 14.74 | 0.67 | 3.03 | 3.14 | 3 | 68.18 |
| Balanced | retrace_bin | 50-61.8 | 24 | 70.83 | 18.08 | 0.75 | 3.62 | 2.08 | 2 | 70.83 |
| Balanced | retrace_bin | 61.8-70 | 12 | 75.00 | 10.11 | 0.84 | 4.29 | 1.03 | 2 | 75.00 |
| Balanced | retrace_bin | 70-78.6 | 15 | 53.33 | 4.37 | 0.29 | 1.60 | 4.88 | 4 | 53.33 |
| Balanced | retrace_bin | 78.6-82 | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Balanced | retrace_bin | 82-88.6 | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Expansion88 | action_class | GO_A_PLUS | 25 | 72.00 | 19.57 | 0.78 | 3.83 | 2.08 | 2 | 72.00 |
| Expansion88 | action_class | GO_CLEAN_A | 22 | 63.64 | 12.24 | 0.56 | 2.47 | 5.24 | 5 | 63.64 |
| Expansion88 | action_class | SELECTIVE_A | 13 | 53.85 | 3.98 | 0.31 | 1.64 | 3.12 | 3 | 53.85 |
| Expansion88 | box_position | bottom | 34 | 64.71 | 20.23 | 0.59 | 2.67 | 3.18 | 3 | 64.71 |
| Expansion88 | box_position | late | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Expansion88 | box_position | low-mid | 24 | 62.50 | 12.63 | 0.53 | 2.36 | 3.10 | 3 | 62.50 |
| Expansion88 | box_position | mid-high | 2 | 100.00 | 2.92 | 1.46 | inf | 0.00 | 0 | 100.00 |
| Expansion88 | break_quality | ok_close | 18 | 66.67 | 11.34 | 0.63 | 2.83 | 4.16 | 4 | 66.67 |
| Expansion88 | break_quality | strong_close | 30 | 66.67 | 19.01 | 0.63 | 2.83 | 4.22 | 4 | 66.67 |
| Expansion88 | break_quality | weak_or_wick | 12 | 58.33 | 5.42 | 0.45 | 2.12 | 2.08 | 2 | 58.33 |
| Expansion88 | h4_state | align | 48 | 58.33 | 20.61 | 0.43 | 2.01 | 4.77 | 4 | 58.33 |
| Expansion88 | h4_state | neutral | 3 | 100.00 | 4.38 | 1.46 | inf | 0.00 | 0 | 100.00 |
| Expansion88 | h4_state | oppose | 9 | 88.89 | 10.78 | 1.20 | 11.55 | 1.02 | 1 | 88.89 |
| Expansion88 | recent_phase | early | 16 | 62.50 | 8.84 | 0.55 | 2.50 | 3.13 | 3 | 62.50 |
| Expansion88 | recent_phase | late_or_chase | 18 | 61.11 | 8.82 | 0.49 | 2.22 | 3.11 | 3 | 61.11 |
| Expansion88 | recent_phase | normal | 26 | 69.23 | 18.12 | 0.70 | 3.18 | 3.14 | 3 | 69.23 |
| Expansion88 | retrace_bin | 50-61.8 | 25 | 72.00 | 19.57 | 0.78 | 3.83 | 2.08 | 2 | 72.00 |
| Expansion88 | retrace_bin | 61.8-70 | 13 | 69.23 | 9.09 | 0.70 | 3.22 | 2.06 | 3 | 69.23 |
| Expansion88 | retrace_bin | 70-78.6 | 15 | 53.33 | 4.37 | 0.29 | 1.60 | 4.88 | 4 | 53.33 |
| Expansion88 | retrace_bin | 78.6-82 | 7 | 57.14 | 2.75 | 0.39 | 1.89 | 2.06 | 2 | 57.14 |
| Expansion88 | retrace_bin | 82-88.6 | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Strict | action_class | GO_A_PLUS | 23 | 69.57 | 16.61 | 0.72 | 3.41 | 2.08 | 2 | 69.57 |
| Strict | action_class | GO_CLEAN_A | 15 | 66.67 | 9.48 | 0.63 | 2.81 | 3.18 | 3 | 66.67 |
| Strict | action_class | SELECTIVE_A | 10 | 60.00 | 4.59 | 0.46 | 2.11 | 2.08 | 2 | 60.00 |
| Strict | box_position | bottom | 27 | 66.67 | 17.46 | 0.65 | 2.93 | 3.18 | 3 | 66.67 |
| Strict | box_position | late | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Strict | box_position | low-mid | 20 | 65.00 | 11.75 | 0.59 | 2.62 | 2.08 | 2 | 65.00 |
| Strict | box_position | mid-high | 1 | 100.00 | 1.48 | 1.48 | inf | 0.00 | 0 | 100.00 |
| Strict | break_quality | ok_close | 14 | 64.29 | 7.98 | 0.57 | 2.54 | 4.16 | 4 | 64.29 |
| Strict | break_quality | strong_close | 24 | 70.83 | 17.72 | 0.74 | 3.43 | 3.18 | 3 | 70.83 |
| Strict | break_quality | weak_or_wick | 10 | 60.00 | 4.99 | 0.50 | 2.32 | 2.08 | 2 | 60.00 |
| Strict | h4_state | align | 38 | 60.53 | 18.48 | 0.49 | 2.21 | 4.18 | 4 | 60.53 |
| Strict | h4_state | neutral | 3 | 100.00 | 4.38 | 1.46 | inf | 0.00 | 0 | 100.00 |
| Strict | h4_state | oppose | 7 | 85.71 | 7.82 | 1.12 | 8.65 | 1.02 | 1 | 85.71 |
| Strict | recent_phase | early | 12 | 66.67 | 7.99 | 0.67 | 3.09 | 2.13 | 2 | 66.67 |
| Strict | recent_phase | late_or_chase | 14 | 64.29 | 7.96 | 0.57 | 2.54 | 2.08 | 2 | 64.29 |
| Strict | recent_phase | normal | 22 | 68.18 | 14.74 | 0.67 | 3.03 | 3.14 | 3 | 68.18 |
| Strict | retrace_bin | 50-61.8 | 23 | 69.57 | 16.61 | 0.72 | 3.41 | 2.08 | 2 | 69.57 |
| Strict | retrace_bin | 61.8-70 | 12 | 75.00 | 10.11 | 0.84 | 4.29 | 1.03 | 2 | 75.00 |
| Strict | retrace_bin | 70-78.6 | 13 | 53.85 | 3.97 | 0.31 | 1.63 | 3.84 | 3 | 53.85 |
| Strict | retrace_bin | 78.6-82 | 0 |  | 0.00 |  |  | 0.00 | 0 |  |
| Strict | retrace_bin | 82-88.6 | 0 |  | 0.00 |  |  | 0.00 | 0 |  |

## Clean Rule Candidates

| group | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | tp_rate | mode | rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | 51 | 66.67 | 32.56 | 0.64 | 2.88 | 4.18 | 4 | 66.67 | Balanced | A/A+ all |
| ALL | 39 | 69.23 | 27.56 | 0.71 | 3.27 | 4.18 | 4 | 69.23 | Balanced | A+ or clean A |
| ALL | 39 | 69.23 | 27.14 | 0.70 | 3.17 | 2.72 | 2 | 69.23 | Balanced | A/A+ strong_or_ok_break |
| ALL | 34 | 67.65 | 22.73 | 0.67 | 3.05 | 3.14 | 3 | 67.65 | Balanced | A/A+ early_or_normal |
| ALL | 27 | 70.37 | 19.59 | 0.73 | 3.34 | 2.11 | 2 | 70.37 | Balanced | A/A+ clean_all |
| ALL | 24 | 70.83 | 18.08 | 0.75 | 3.62 | 2.08 | 2 | 70.83 | Balanced | A+ only |
| ALL | 22 | 59.09 | 9.75 | 0.44 | 2.04 | 2.11 | 2 | 59.09 | Balanced | B only |
| ALL | 60 | 65.00 | 35.78 | 0.60 | 2.67 | 4.77 | 4 | 65.00 | Expansion88 | A/A+ all |
| ALL | 47 | 68.09 | 31.80 | 0.68 | 3.09 | 4.77 | 4 | 68.09 | Expansion88 | A+ or clean A |
| ALL | 48 | 66.67 | 30.36 | 0.63 | 2.83 | 3.76 | 3 | 66.67 | Expansion88 | A/A+ strong_or_ok_break |
| ALL | 42 | 66.67 | 26.96 | 0.64 | 2.90 | 3.73 | 3 | 66.67 | Expansion88 | A/A+ early_or_normal |
| ALL | 35 | 68.57 | 23.82 | 0.68 | 3.08 | 2.70 | 2 | 68.57 | Expansion88 | A/A+ clean_all |
| ALL | 25 | 72.00 | 19.57 | 0.78 | 3.83 | 2.08 | 2 | 72.00 | Expansion88 | A+ only |
| ALL | 28 | 53.57 | 8.50 | 0.30 | 1.63 | 3.36 | 3 | 53.57 | Expansion88 | B only |
| ALL | 48 | 66.67 | 30.69 | 0.64 | 2.89 | 4.18 | 4 | 66.67 | Strict | A/A+ all |
| ALL | 38 | 68.42 | 26.09 | 0.69 | 3.15 | 4.18 | 4 | 68.42 | Strict | A+ or clean A |
| ALL | 38 | 68.42 | 25.70 | 0.68 | 3.06 | 2.72 | 2 | 68.42 | Strict | A/A+ strong_or_ok_break |
| ALL | 34 | 67.65 | 22.73 | 0.67 | 3.05 | 3.14 | 3 | 67.65 | Strict | A/A+ early_or_normal |
| ALL | 27 | 70.37 | 19.59 | 0.73 | 3.34 | 2.11 | 2 | 70.37 | Strict | A/A+ clean_all |
| ALL | 23 | 69.57 | 16.61 | 0.72 | 3.41 | 2.08 | 2 | 69.57 | Strict | A+ only |
| ALL | 21 | 61.90 | 10.78 | 0.51 | 2.30 | 2.11 | 2 | 61.90 | Strict | B only |

## 実戦ルール案

- `GO_A_PLUS`: A+。通常の実戦候補。
- `GO_CLEAN_A`: Aかつ、Box位置が遅くなく、ブレイク足がstrong/ok、直近がearly/normal。
- `SELECTIVE_A`: Aだが何かが弱い。裁量確認。
- `OBSERVE_STRICT_B`: StrictモードのBのみ。小ロットまたは記録。
- `SKIP`: Expansion B、弱いA、条件緩和で出た低品質候補。
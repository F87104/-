# H4 Low-Stag Short H&S Filter Study

Status: 検証途中。ユーザー提供の `Beautiful H&S / Inverse H&S Scanner` をPythonへ移植し、H4安値停滞ショートの補助条件として確認。

## 検証した使い方

- `hs_pattern`: 三尊の形がシグナル前に確定。戻り売り構造の候補。
- `hs_break`: 三尊ネックライン割れがシグナル前に確定。短期下落の追い風候補。
- `inv_pattern` / `inv_break`: 逆三尊。ショートでは反転警戒または除外候補。
- `after_low_break`: 1ヶ月安値ブレイク後からH4安値停滞シグナルまでに出たか。

## 重要な実装注意

- Pineと同じく、ピボットは `pivotRight` 本後に確定するため、Pythonでも確定バー `confirm_i <= trigger_i` のイベントだけ使用。
- 三尊/逆三尊は `形の確定` と `ネックラインブレイク` を分離。ブレイクは形成後 `breakBars` 本以内のみ追跡。
- default条件だけでなく、loose/default/strict、pivot 3/5/8、事前トレンドあり/なしを比較。ただし採用候補は説明しやすいものだけ。

## ベースライン

| sample | hs_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 7 | 7 | 100.00 | 85.71 | 0.00 | 10.72 | 0.00 | 1.53 | 11.50 | 1.02 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 18 | 18 | 100.00 | 61.11 | 0.00 | 13.61 | 0.00 | 0.76 | 2.78 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 6 | 6 | 100.00 | 83.33 | 0.00 | 8.71 | 0.00 | 1.45 | 9.18 | 0.00 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | baseline | 5 | 5 | 100.00 | 100.00 | 0.00 | 9.77 | 0.00 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## サンプル別 改善候補

PFと勝率がベースライン以上、かつ3件以上の条件だけを表示。

| sample | hs_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | inv_pattern_48 | 26 | 5 | 19.23 | 100.00 | 57.69 | 9.85 | 3.69 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | inv_pattern_48 | 26 | 5 | 19.23 | 100.00 | 57.69 | 9.85 | 3.69 | 1.97 | inf | 0.00 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_48 | 26 | 6 | 23.08 | 83.33 | 41.03 | 8.84 | 2.67 | 1.47 | 9.71 | 1.01 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_48 | 26 | 6 | 23.08 | 83.33 | 41.03 | 8.84 | 2.67 | 1.47 | 9.71 | 1.01 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 26 | 18 | 69.23 | 50.00 | 7.69 | 8.39 | 2.23 | 0.47 | 1.90 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 26 | 7 | 26.92 | 71.43 | 29.12 | 7.80 | 1.64 | 1.11 | 4.81 | 1.03 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 26 | 7 | 26.92 | 71.43 | 29.12 | 7.80 | 1.64 | 1.11 | 4.81 | 1.03 | EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_240 | 26 | 16 | 61.54 | 50.00 | 7.69 | 7.44 | 1.28 | 0.46 | 1.90 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | no_inv_pattern_120 | 37 | 28 | 75.68 | 50.00 | 6.76 | 11.98 | 3.61 | 0.43 | 1.80 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | no_inv_pattern_120 | 37 | 28 | 75.68 | 50.00 | 6.76 | 11.98 | 3.61 | 0.43 | 1.80 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 37 | 26 | 70.27 | 50.00 | 6.76 | 11.21 | 2.85 | 0.43 | 1.81 | 3.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | no_inv_break_120 | 37 | 30 | 81.08 | 46.67 | 3.42 | 9.77 | 1.41 | 0.33 | 1.57 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_DEF_TR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 37 | 33 | 89.19 | 45.45 | 2.21 | 9.49 | 1.13 | 0.29 | 1.49 | 3.70 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 37 | 33 | 89.19 | 45.45 | 2.21 | 9.49 | 1.13 | 0.29 | 1.49 | 3.70 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 37 | 33 | 89.19 | 45.45 | 2.21 | 9.47 | 1.11 | 0.29 | 1.49 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 37 | 33 | 89.19 | 45.45 | 2.21 | 9.47 | 1.11 | 0.29 | 1.49 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 7 | 5 | 71.43 | 100.00 | 14.29 | 9.76 | -0.96 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P5_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | hs_break_240 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | no_inv_pattern_120 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.82 | 0.21 | 0.92 | 3.53 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | no_inv_pattern_120 | 18 | 15 | 83.33 | 66.67 | 5.56 | 13.82 | 0.21 | 0.92 | 3.53 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | no_inv_pattern_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.76 | -0.85 | 0.80 | 2.96 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | no_inv_pattern_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.76 | -0.85 | 0.80 | 2.96 | 1.29 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.69 | -0.92 | 0.79 | 2.93 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P8_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.69 | -0.92 | 0.79 | 2.93 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.66 | -0.95 | 0.79 | 2.92 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_all | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 18 | 16 | 88.89 | 62.50 | 1.39 | 12.66 | -0.95 | 0.79 | 2.92 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 11 | 9 | 81.82 | 77.78 | 5.05 | 11.61 | -0.95 | 1.29 | 6.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_break_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 9 | 7 | 77.78 | 100.00 | 11.11 | 13.72 | -0.95 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P8_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P8_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | no_inv_pattern_120 | 6 | 5 | 83.33 | 100.00 | 16.67 | 9.77 | 1.06 | 1.95 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | no_inv_break_120 | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | no_inv_break_120 | 6 | 4 | 66.67 | 100.00 | 16.67 | 7.83 | -0.87 | 1.96 | inf | 0.00 | CHFJPY,EURJPY,GBPJPY | test_2021_2024,train_2015_2020 |

## 三尊系だけを見る

| sample | hs_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 26 | 7 | 26.92 | 57.14 | 14.84 | 4.64 | -1.52 | 0.66 | 2.46 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 26 | 7 | 26.92 | 57.14 | 14.84 | 4.64 | -1.52 | 0.66 | 2.46 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P8_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.95 | -5.21 | 0.47 | 1.93 | 0.00 | CHFJPY | test_2021_2024 |
| practical_core4 | P8_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.95 | -5.21 | 0.47 | 1.93 | 0.00 | CHFJPY | test_2021_2024 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_after_low_break_break | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.95 | -5.22 | 0.47 | 1.92 | 1.03 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_after_low_break_break | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.95 | -5.22 | 0.47 | 1.92 | 1.03 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 37 | 7 | 18.92 | 57.14 | 13.90 | 4.20 | -4.17 | 0.60 | 2.26 | 1.22 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_after_low_break_break | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.95 | -7.42 | 0.47 | 1.92 | 1.03 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_after_low_break_break | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.95 | -7.42 | 0.47 | 1.92 | 1.03 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | hs_pattern_120 | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.85 | -7.52 | 0.42 | 1.83 | 0.00 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | hs_pattern_120 | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.85 | -7.52 | 0.42 | 1.83 | 0.00 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_STRICT_NOTR_TL40_TA1.5_BB80_BUF0.1 | hs_break_120 | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.85 | -7.52 | 0.42 | 1.83 | 0.00 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 7 | 4 | 57.14 | 100.00 | 14.29 | 7.79 | -2.93 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 7 | 3 | 42.86 | 100.00 | 14.29 | 5.85 | -4.87 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 7 | 3 | 42.86 | 100.00 | 14.29 | 5.85 | -4.87 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 18 | 7 | 38.89 | 71.43 | 10.32 | 7.65 | -5.96 | 1.09 | 4.62 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P5_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 18 | 7 | 38.89 | 71.43 | 10.32 | 7.39 | -6.22 | 1.06 | 4.49 | 1.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P5_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 18 | 6 | 33.33 | 66.67 | 5.56 | 5.41 | -8.20 | 0.90 | 3.56 | 1.08 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 18 | 8 | 44.44 | 62.50 | 1.39 | 6.65 | -6.96 | 0.83 | 3.13 | 1.08 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P5_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 18 | 8 | 44.44 | 62.50 | 1.39 | 6.33 | -7.28 | 0.79 | 2.99 | 1.08 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P5_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 18 | 8 | 44.44 | 62.50 | 1.39 | 6.33 | -7.28 | 0.79 | 2.99 | 1.08 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 11 | 7 | 63.64 | 71.43 | -1.30 | 7.65 | -4.90 | 1.09 | 4.62 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 11 | 7 | 63.64 | 71.43 | -1.30 | 7.65 | -4.90 | 1.09 | 4.62 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 11 | 7 | 63.64 | 71.43 | -1.30 | 7.65 | -4.90 | 1.09 | 4.62 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 11 | 7 | 63.64 | 71.43 | -1.30 | 7.65 | -4.90 | 1.09 | 4.62 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 11 | 6 | 54.55 | 66.67 | -6.06 | 5.71 | -6.85 | 0.95 | 3.70 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 11 | 6 | 54.55 | 66.67 | -6.06 | 5.71 | -6.85 | 0.95 | 3.70 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.77 | -4.90 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.77 | -4.90 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.77 | -4.90 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 9 | 5 | 55.56 | 100.00 | 11.11 | 9.77 | -4.90 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 9 | 4 | 44.44 | 100.00 | 11.11 | 7.82 | -6.85 | 1.96 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 9 | 4 | 44.44 | 100.00 | 11.11 | 7.82 | -6.85 | 1.96 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 6 | 3 | 50.00 | 100.00 | 16.67 | 5.85 | -2.85 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 6 | 3 | 50.00 | 100.00 | 16.67 | 5.81 | -2.89 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 6 | 3 | 50.00 | 100.00 | 16.67 | 5.81 | -2.89 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 6 | 2 | 33.33 | 100.00 | 16.67 | 3.96 | -4.75 | 1.98 | inf | 0.00 | GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 6 | 2 | 33.33 | 100.00 | 16.67 | 3.87 | -4.83 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_support60_119 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | hs_pattern_120 | 6 | 2 | 33.33 | 100.00 | 16.67 | 3.84 | -4.87 | 1.92 | inf | 0.00 | CHFJPY,XAUUSD | train_2015_2020 |
| primary_support60_119_core4 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.85 | -3.92 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.85 | -3.92 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_break_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.85 | -3.92 | 1.95 | inf | 0.00 | CHFJPY,GBPJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_pattern_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.81 | -3.95 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | hs_break_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.81 | -3.95 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | hs_pattern_120 | 5 | 3 | 60.00 | 100.00 | 0.00 | 5.81 | -3.95 | 1.94 | inf | 0.00 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## 逆三尊系だけを見る

| sample | hs_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 26 | 4 | 15.38 | 25.00 | -17.31 | -1.10 | -7.26 | -0.28 | 0.64 | 1.03 | CHFJPY,EURJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 26 | 4 | 15.38 | 25.00 | -17.31 | -1.10 | -7.26 | -0.28 | 0.64 | 1.03 | CHFJPY,EURJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 26 | 4 | 15.38 | 25.00 | -17.31 | -1.10 | -7.26 | -0.28 | 0.64 | 1.03 | CHFJPY,EURJPY,GBPJPY | train_2015_2020 |
| practical_core4 | P5_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 26 | 4 | 15.38 | 25.00 | -17.31 | -1.09 | -7.25 | -0.27 | 0.65 | 2.05 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P5_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 26 | 4 | 15.38 | 25.00 | -17.31 | -1.09 | -7.25 | -0.27 | 0.65 | 2.05 | CHFJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 26 | 6 | 23.08 | 33.33 | -8.97 | -0.19 | -6.35 | -0.03 | 0.95 | 1.03 | CHFJPY,EURJPY,GBPJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 37 | 9 | 24.32 | 22.22 | -21.02 | -3.61 | -11.98 | -0.40 | 0.52 | 4.51 | EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 37 | 9 | 24.32 | 22.22 | -21.02 | -3.61 | -11.98 | -0.40 | 0.52 | 4.51 | EURJPY,GBPJPY,SILVER | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P3_DEF_TR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 37 | 4 | 10.81 | 25.00 | -18.24 | -1.13 | -9.49 | -0.28 | 0.64 | 2.09 | EURJPY,GBPJPY,SILVER | train_2015_2020 |
| practical_no_AUD_USD | P3_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 37 | 4 | 10.81 | 25.00 | -18.24 | -1.13 | -9.49 | -0.28 | 0.64 | 2.09 | EURJPY,GBPJPY,SILVER | train_2015_2020 |
| practical_no_AUD_USD | P8_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 37 | 4 | 10.81 | 25.00 | -18.24 | -1.11 | -9.47 | -0.28 | 0.64 | 1.04 | GBPJPY,SILVER | oos_2025_2026,train_2015_2020 |
| practical_no_AUD_USD | P8_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 37 | 4 | 10.81 | 25.00 | -18.24 | -1.11 | -9.47 | -0.28 | 0.64 | 1.04 | GBPJPY,SILVER | oos_2025_2026,train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| practical_support60_119_no_AUD_USD | P3_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| practical_support60_119_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| practical_support60_119_no_AUD_USD | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| practical_support60_119_no_AUD_USD | P8_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| practical_support60_119_no_AUD_USD | P8_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 7 | 2 | 28.57 | 100.00 | 14.29 | 3.91 | -6.81 | 1.96 | inf | 0.00 | GBPJPY,XAUUSD | train_2015_2020 |
| primary_all | P8_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.21 | -13.82 | -0.07 | 0.90 | 1.13 | AUDJPY,GBPJPY,SILVER | test_2021_2024,train_2015_2020 |
| primary_all | P8_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 18 | 3 | 16.67 | 33.33 | -27.78 | -0.21 | -13.82 | -0.07 | 0.90 | 1.13 | AUDJPY,GBPJPY,SILVER | test_2021_2024,train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 18 | 6 | 33.33 | 50.00 | -11.11 | 2.30 | -11.31 | 0.38 | 1.68 | 1.29 | AUDJPY,CHFJPY,GBPJPY,SILVER,XAUUSD | train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 18 | 6 | 33.33 | 50.00 | -11.11 | 2.30 | -11.31 | 0.38 | 1.68 | 1.29 | AUDJPY,CHFJPY,GBPJPY,SILVER,XAUUSD | train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 18 | 8 | 44.44 | 50.00 | -11.11 | 3.15 | -10.46 | 0.39 | 1.70 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_all | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 18 | 8 | 44.44 | 50.00 | -11.11 | 3.15 | -10.46 | 0.39 | 1.70 | 2.42 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4 | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4 | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.95 | -11.61 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_DEF_NOTR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_pattern_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_core4_quality | P3_STRICT_NOTR_TL40_TA1.5_BB40_BUF0.1 | inv_break_120 | 9 | 2 | 22.22 | 50.00 | -38.89 | 0.95 | -13.72 | 0.47 | 1.91 | 0.00 | CHFJPY,GBPJPY | train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.87 | -7.83 | 0.44 | 1.82 | 0.00 | AUDJPY,XAUUSD | train_2015_2020 |
| primary_support60_119 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.87 | -7.83 | 0.44 | 1.82 | 0.00 | AUDJPY,XAUUSD | train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_break_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.87 | -7.83 | 0.44 | 1.82 | 0.00 | AUDJPY,XAUUSD | train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_break_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.87 | -7.83 | 0.44 | 1.82 | 0.00 | AUDJPY,XAUUSD | train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.91 | -7.79 | 0.46 | 1.86 | 0.00 | AUDJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119 | P5_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 6 | 2 | 33.33 | 50.00 | -33.33 | 0.91 | -7.79 | 0.46 | 1.86 | 0.00 | AUDJPY,EURJPY | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_NOTR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 5 | 2 | 40.00 | 100.00 | 0.00 | 3.92 | -5.85 | 1.96 | inf | 0.00 | EURJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_NOTR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 5 | 2 | 40.00 | 100.00 | 0.00 | 3.92 | -5.85 | 1.96 | inf | 0.00 | EURJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_TR_TL40_TA1_BB40_BUF0.1 | inv_pattern_120 | 5 | 2 | 40.00 | 100.00 | 0.00 | 3.92 | -5.85 | 1.96 | inf | 0.00 | EURJPY,XAUUSD | test_2021_2024,train_2015_2020 |
| primary_support60_119_core4 | P3_LOOSE_TR_TL40_TA1_BB80_BUF0.1 | inv_pattern_120 | 5 | 2 | 40.00 | 100.00 | 0.00 | 3.92 | -5.85 | 1.96 | inf | 0.00 | EURJPY,XAUUSD | test_2021_2024,train_2015_2020 |

## 元Pine設定に近い条件

`pivot=5`, `Beautiful DEF`, `事前トレンドあり`, `breakBars=80`。まずTradingViewで見るならこの条件。

| sample | hs_spec | rule | base_trades | trades | coverage_pct | win_rate | delta_win_rate | total_r | delta_total_r | avg_r | pf | max_dd_r | symbols | periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | baseline | 26 | 26 | 100.00 | 42.31 | 0.00 | 6.16 | 0.00 | 0.24 | 1.40 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_pattern_120 | 26 | 1 | 3.85 | 0.00 | -42.31 | -1.04 | -7.20 | -1.04 | 0.00 | 0.00 | EURJPY | test_2021_2024 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_120 | 26 | 1 | 3.85 | 0.00 | -42.31 | -1.04 | -7.20 | -1.04 | 0.00 | 0.00 | EURJPY | test_2021_2024 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_240 | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.94 | -5.22 | 0.47 | 1.90 | 0.00 | EURJPY,GBPJPY | test_2021_2024 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 26 | 2 | 7.69 | 50.00 | 7.69 | 0.96 | -5.20 | 0.48 | 1.94 | 1.03 | GBPJPY | train_2015_2020 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 26 | 1 | 3.85 | 0.00 | -42.31 | -1.03 | -7.19 | -1.03 | 0.00 | 0.00 | GBPJPY | train_2015_2020 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 26 | 24 | 92.31 | 41.67 | -0.64 | 5.20 | -0.96 | 0.22 | 1.36 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 26 | 25 | 96.15 | 44.00 | 1.69 | 7.19 | 1.03 | 0.29 | 1.50 | 3.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | baseline | 37 | 37 | 100.00 | 43.24 | 0.00 | 8.36 | 0.00 | 0.23 | 1.37 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_pattern_120 | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.77 | -7.60 | 0.38 | 1.74 | 0.00 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_120 | 37 | 2 | 5.41 | 50.00 | 6.76 | 0.77 | -7.60 | 0.38 | 1.74 | 0.00 | EURJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_240 | 37 | 3 | 8.11 | 66.67 | 23.42 | 2.74 | -5.62 | 0.91 | 3.64 | 0.00 | EURJPY,GBPJPY,SILVER | test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 37 | 3 | 8.11 | 33.33 | -9.91 | -0.10 | -8.47 | -0.03 | 0.95 | 2.09 | GBPJPY,SILVER | train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 37 | 1 | 2.70 | 0.00 | -43.24 | -1.03 | -9.39 | -1.03 | 0.00 | 0.00 | GBPJPY | train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 37 | 34 | 91.89 | 44.12 | 0.87 | 8.47 | 0.10 | 0.25 | 1.41 | 3.70 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| practical_no_AUD_USD | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 37 | 36 | 97.30 | 44.44 | 1.20 | 9.39 | 1.03 | 0.26 | 1.44 | 4.76 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | baseline | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_pattern_120 | 11 | 1 | 9.09 | 0.00 | -72.73 | -1.04 | -13.59 | -1.04 | 0.00 | 0.00 | EURJPY | test_2021_2024 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_120 | 11 | 1 | 9.09 | 0.00 | -72.73 | -1.04 | -13.59 | -1.04 | 0.00 | 0.00 | EURJPY | test_2021_2024 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_240 | 11 | 2 | 18.18 | 50.00 | -22.73 | 0.94 | -11.62 | 0.47 | 1.90 | 0.00 | EURJPY,GBPJPY | test_2021_2024 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 11 | 1 | 9.09 | 100.00 | 27.27 | 1.98 | -10.57 | 1.98 | inf | 0.00 | GBPJPY | train_2015_2020 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 11 | 0 | 0.00 | 0.00 | -72.73 | 0.00 | -12.55 | 0.00 |  | 0.00 |  |  |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 11 | 10 | 90.91 | 70.00 | -2.73 | 10.57 | -1.98 | 1.06 | 4.35 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4 | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 11 | 11 | 100.00 | 72.73 | 0.00 | 12.55 | 0.00 | 1.14 | 4.98 | 1.08 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | baseline | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_pattern_120 | 9 | 0 | 0.00 | 0.00 | -88.89 | 0.00 | -14.67 | 0.00 |  | 0.00 |  |  |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_120 | 9 | 0 | 0.00 | 0.00 | -88.89 | 0.00 | -14.67 | 0.00 |  | 0.00 |  |  |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | hs_break_240 | 9 | 1 | 11.11 | 100.00 | 11.11 | 1.98 | -12.69 | 1.98 | inf | 0.00 | GBPJPY | test_2021_2024 |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_pattern_120 | 9 | 1 | 11.11 | 100.00 | 11.11 | 1.98 | -12.69 | 1.98 | inf | 0.00 | GBPJPY | train_2015_2020 |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | inv_break_120 | 9 | 0 | 0.00 | 0.00 | -88.89 | 0.00 | -14.67 | 0.00 |  | 0.00 |  |  |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_pattern_120 | 9 | 8 | 88.89 | 87.50 | -1.39 | 12.69 | -1.98 | 1.59 | 13.21 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |
| primary_core4_quality | P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1 | no_inv_break_120 | 9 | 9 | 100.00 | 88.89 | 0.00 | 14.67 | 0.00 | 1.63 | 15.12 | 0.00 | CHFJPY,EURJPY,GBPJPY,XAUUSD | oos_2025_2026,test_2021_2024,train_2015_2020 |

## Pineでまず試す条件

1. 三尊そのものは、H4安値停滞ショートのエントリー強化条件としては件数不足。元設定では `hs_break_120` が practical_core4 で 1件のみ、しかも -1.04R。
2. 逆三尊は、ショートの逆方向シグナルとして一応見る価値あり。元設定では `inv_break_120` を避けると practical_core4 が 26 trades / +6.16R / PF 1.40 から 25 trades / +7.19R / PF 1.50。
3. ただし改善はほぼ1件除外の効果なので、現時点では `逆三尊上抜け注意` ラベルに留める。即見送りルールにはしない。
4. Loose/NoTrend/P3系は良く見える条件もあるが、元の目的である「綺麗な三尊」から外れやすい。実戦条件ではなく検証用表示だけ。

## 暫定解釈

- 三尊は、現時点ではH4安値停滞ショートの本体条件に足さない。
- 逆三尊ネック上抜けは、反転警戒タグとしてPineに表示する価値がある。
- 件数が少ない条件はPine表示だけにし、実戦ルールには入れない。

## 出力CSV

- `annotated_trades.csv`
- `rule_summary.csv`
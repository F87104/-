# H4 安値停滞ブレイク 深掘り分析

Status: 検証途中。H4 1ヶ月安値更新後の安値停滞ブレイクを、停滞レンジ品質とブレイク後の動きで再分析。

## 見た角度

- 停滞レンジの狭さ: シグナル前3本の高安幅をATR換算。
- 下抜け足の強さ: 停滞レンジ安値からどれだけ終値で下に抜けたか、足の実体、終値位置。
- サポートの見え方: 安値保持期間、接触回数、レンジ割れ/トレンド継続の分類。
- 直後フォロースルー: エントリー後3〜6本で1Rに届くか。
- 戻りやすさ: エントリー後6本以内に停滞レンジ中央へ戻るか。

## ベースサンプル

| sample | trades | total_r | avg_r | PF | maxDD |
|---|---:|---:|---:|---:|---:|
| primary L120 + ADX30 + risk<=1.5 + BB幅3-8 | 18 | 13.61 | 0.76 | 2.78 | 3.41 |
| practical all lookbacks | 198 | 38.66 | 0.20 | 1.32 | 42.52 |

## Primary: 通貨別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 | 2.20 | 50.00 | 50.00 | 0.00 |
| CHFJPY | 3 | 66.67 | 2.83 | 0.94 | 3.72 | 0.00 | 1.75 | 66.67 | 33.33 | 0.00 |
| SILVER | 4 | 50.00 | 1.15 | 0.29 | 1.48 | 2.42 | 2.02 | 75.00 | 25.00 | 50.00 |
| EURJPY | 2 | 50.00 | 0.94 | 0.47 | 1.90 | 0.00 | 1.17 | 50.00 | 50.00 | 0.00 |
| XAUUSD | 2 | 50.00 | 0.86 | 0.43 | 1.80 | 1.08 | 1.01 | 50.00 | 100.00 | 0.00 |
| AUDJPY | 3 | 33.33 | -0.10 | -0.03 | 0.95 | 1.06 | 0.81 | 33.33 | 66.67 | 0.00 |

## Primary: 期間別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_2015_2020 | 11 | 54.55 | 5.90 | 0.54 | 2.08 | 3.41 | 1.48 | 36.36 | 72.73 | 9.09 |
| test_2021_2024 | 6 | 66.67 | 5.73 | 0.95 | 3.64 | 1.04 | 1.76 | 83.33 | 16.67 | 16.67 |
| oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 | 2.03 | 100.00 | 0.00 | 0.00 |

## Primary: 停滞レンジ幅別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02_wide_0.70-1.00 | 17 | 58.82 | 11.63 | 0.68 | 2.52 | 3.41 | 1.57 | 52.94 | 52.94 | 11.76 |
| 01_mid_0.40-0.70 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 | 2.15 | 100.00 | 0.00 | 0.00 |

## Primary: 下抜け深さ別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02_strong_0.20-0.40 | 7 | 71.43 | 7.56 | 1.08 | 4.65 | 2.07 | 1.61 | 71.43 | 42.86 | 0.00 |
| 01_clean_0.05-0.20 | 8 | 50.00 | 3.37 | 0.42 | 1.79 | 2.17 | 1.51 | 37.50 | 62.50 | 12.50 |
| 03_too_deep_>0.40 | 3 | 66.67 | 2.68 | 0.89 | 3.07 | 1.29 | 1.85 | 66.67 | 33.33 | 33.33 |

## Primary: 下抜け足の終値位置

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00_close_near_low | 10 | 70.00 | 10.42 | 1.04 | 4.25 | 2.17 | 1.81 | 50.00 | 60.00 | 10.00 |
| 01_lower_mid | 7 | 57.14 | 4.26 | 0.61 | 2.27 | 2.30 | 1.55 | 71.43 | 28.57 | 14.29 |
| 02_upper_mid | 1 | 0.00 | -1.08 | -1.08 | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 |

## Practical All: サポート保持期間別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02_60-119bars | 26 | 69.23 | 26.92 | 1.04 | 4.20 | 6.38 | 1.65 | 38.46 | 69.23 | 0.00 |
| 00_<=24bars | 106 | 38.68 | 9.12 | 0.09 | 1.13 | 43.10 | 1.20 | 36.79 | 63.21 | 15.09 |
| 04_>=240bars | 6 | 66.67 | 5.67 | 0.95 | 3.51 | 2.26 | 1.84 | 33.33 | 66.67 | 33.33 |
| 03_120-239bars | 14 | 42.86 | 3.55 | 0.25 | 1.43 | 4.38 | 1.17 | 28.57 | 85.71 | 0.00 |
| 01_25-59bars | 46 | 30.43 | -6.61 | -0.14 | 0.81 | 19.92 | 1.22 | 43.48 | 60.87 | 34.78 |

## Practical All: 通貨別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 66 | 56.06 | 43.54 | 0.66 | 2.46 | 14.39 | 1.30 | 22.73 | 83.33 | 3.03 |
| CHFJPY | 26 | 46.15 | 8.65 | 0.33 | 1.59 | 9.35 | 1.39 | 53.85 | 53.85 | 7.69 |
| XAUUSD | 10 | 60.00 | 7.52 | 0.75 | 2.83 | 4.11 | 1.47 | 80.00 | 100.00 | 20.00 |
| EURJPY | 12 | 50.00 | 5.72 | 0.48 | 1.93 | 6.16 | 1.36 | 66.67 | 50.00 | 16.67 |
| SILVER | 54 | 37.04 | -2.16 | -0.04 | 0.95 | 30.20 | 1.66 | 51.85 | 29.63 | 48.15 |
| USDJPY | 6 | 0.00 | -6.03 | -1.01 | 0.00 | 5.03 | 0.51 | 0.00 | 100.00 | 0.00 |
| AUDJPY | 24 | 8.33 | -18.58 | -0.77 | 0.18 | 19.48 | 0.30 | 8.33 | 91.67 | 0.00 |

## Practical All: 期間別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train_2015_2020 | 134 | 43.28 | 31.44 | 0.23 | 1.39 | 21.21 | 1.22 | 22.39 | 79.10 | 10.45 |
| oos_2025_2026 | 14 | 42.86 | 3.69 | 0.26 | 1.45 | 8.22 | 1.32 | 57.14 | 57.14 | 14.29 |
| test_2021_2024 | 50 | 38.00 | 3.53 | 0.07 | 1.11 | 20.58 | 1.42 | 74.00 | 30.00 | 36.00 |

## Practical All: 事前状態別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mixed_or_wide_range | 75 | 46.67 | 26.04 | 0.35 | 1.61 | 20.15 | 1.46 | 44.00 | 64.00 | 25.33 |
| range_support_break | 24 | 45.83 | 8.13 | 0.34 | 1.60 | 11.55 | 1.12 | 33.33 | 70.83 | 0.00 |
| trend_continuation_break | 99 | 37.37 | 4.48 | 0.05 | 1.07 | 43.14 | 1.18 | 34.34 | 64.65 | 15.15 |

## Practical All: 直後フォロースルー別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00_hit_1r_<=3 | 54 | 59.26 | 37.39 | 0.69 | 2.51 | 20.15 | 1.90 | 100.00 | 22.22 | 40.74 |
| 01_hit_1r_<=6 | 21 | 52.38 | 9.95 | 0.47 | 1.87 | 11.42 | 1.65 | 100.00 | 28.57 | 38.10 |
| 02_no_fast_1r | 123 | 32.52 | -8.68 | -0.07 | 0.90 | 40.47 | 0.94 | 0.00 | 90.24 | 3.25 |

## Practical All: 6本以内の戻り別

| bucket | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate | giveback_1r_to_loss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00_no_mid_retest_6 | 69 | 65.22 | 58.91 | 0.85 | 3.09 | 18.12 | 1.98 | 82.61 | 0.00 | 34.78 |
| 01_mid_retest_6 | 129 | 29.46 | -20.25 | -0.16 | 0.79 | 50.77 | 0.90 | 13.95 | 100.00 | 7.75 |

## 複合条件チェック

| combo | trades | win_rate | total_r | avg_r | pf | max_dd_r | avg_mfe_r | hit_1r_within_6_rate | retest_mid_6_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| danger_wide_zone_or_big_risk | 171 | 45.61 | 52.62 | 0.31 | 1.53 | 42.26 | 1.34 | 38.60 | 64.91 |
| close_near_low_large_body | 108 | 50.00 | 48.51 | 0.45 | 1.85 | 33.64 | 1.37 | 37.04 | 64.81 |
| fast_followthrough_1r_6bars | 75 | 57.33 | 47.34 | 0.63 | 2.31 | 22.29 | 1.83 | 100.00 | 24.00 |
| support_age_60_119_clean_break | 26 | 69.23 | 26.92 | 1.04 | 4.20 | 6.38 | 1.65 | 38.46 | 69.23 |
| tight_or_mid_zone_clean_break_no_mid_retest | 7 | 42.86 | 1.07 | 0.15 | 1.22 | 3.65 | 1.97 | 42.86 | 0.00 |
| danger_mid_retest_6 | 129 | 29.46 | -20.25 | -0.16 | 0.79 | 50.77 | 0.90 | 13.95 | 100.00 |

## 出口管理比較

| sample | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_L120_ADX30_RISK1_5_BBW3_8 | base_fixed_2R | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 3.41 | 3 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | fixed_1_5R | 18 | 61.11 | 8.11 | 0.45 | 2.06 | 3.77 | 3 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | fixed_2R_no_1R_by_6bars | 18 | 55.56 | 8.75 | 0.49 | 2.17 | 5.09 | 5 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | fixed_2R_no_1R_by_12bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 3.41 | 3 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | BE_after_1R_to_2R | 18 | 27.78 | 3.61 | 0.20 | 1.60 | 4.01 | 6 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | half_1R_BE_rest_2R | 18 | 72.22 | 5.11 | 0.28 | 1.98 | 2.64 | 2 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | half_1R_trail1ATR_rest_2R | 18 | 72.22 | 5.39 | 0.30 | 2.03 | 2.64 | 2 |
| primary_L120_ADX30_RISK1_5_BBW3_8 | exit_if_mid_retest_within_6 | 18 | 44.44 | 9.38 | 0.52 | 2.53 | 4.54 | 7 |
| practical_all_lookbacks | base_fixed_2R | 198 | 41.92 | 38.66 | 0.20 | 1.32 | 42.52 | 39 |
| practical_all_lookbacks | fixed_1_5R | 198 | 43.94 | 7.16 | 0.04 | 1.06 | 48.25 | 39 |
| practical_all_lookbacks | fixed_2R_no_1R_by_6bars | 198 | 32.83 | -16.55 | -0.08 | 0.85 | 64.33 | 43 |
| practical_all_lookbacks | fixed_2R_no_1R_by_12bars | 198 | 44.95 | 50.91 | 0.26 | 1.46 | 42.52 | 39 |
| practical_all_lookbacks | BE_after_1R_to_2R | 198 | 18.69 | -19.34 | -0.10 | 0.79 | 36.77 | 60 |
| practical_all_lookbacks | half_1R_BE_rest_2R | 198 | 59.09 | 2.16 | 0.01 | 1.03 | 20.54 | 14 |
| practical_all_lookbacks | half_1R_trail1ATR_rest_2R | 198 | 59.09 | -1.56 | -0.01 | 0.98 | 21.42 | 14 |
| practical_all_lookbacks | exit_if_mid_retest_within_6 | 198 | 25.76 | 13.86 | 0.07 | 1.16 | 35.46 | 39 |
| support_age_60_119_practical | base_fixed_2R | 26 | 69.23 | 26.92 | 1.04 | 4.20 | 6.38 | 6 |
| support_age_60_119_practical | fixed_1_5R | 26 | 69.23 | 17.92 | 0.69 | 3.13 | 6.38 | 6 |
| support_age_60_119_practical | fixed_2R_no_1R_by_6bars | 26 | 69.23 | 16.79 | 0.65 | 3.60 | 6.38 | 6 |
| support_age_60_119_practical | fixed_2R_no_1R_by_12bars | 26 | 76.92 | 30.07 | 1.16 | 5.71 | 6.38 | 6 |
| support_age_60_119_practical | BE_after_1R_to_2R | 26 | 46.15 | 14.92 | 0.57 | 2.71 | 8.65 | 11 |
| support_age_60_119_practical | half_1R_BE_rest_2R | 26 | 69.23 | 11.92 | 0.46 | 2.41 | 7.63 | 6 |
| support_age_60_119_practical | half_1R_trail1ATR_rest_2R | 26 | 69.23 | 12.27 | 0.47 | 2.46 | 7.63 | 6 |
| support_age_60_119_practical | exit_if_mid_retest_within_6 | 26 | 38.46 | 11.17 | 0.43 | 2.34 | 4.95 | 10 |

## 暫定解釈

- 安値停滞は、単にレンジが狭ければ良いわけではない。今回の主軸は `サポート保持期間`、`下抜け足の終値位置`、`抜けた後の反応速度`。
- Practical Allでは、GBPJPYが大きく寄与し、AUDJPYとUSDJPYは弱い。全通貨へ広げるより、通貨別に採否を分ける必要がある。
- 6本以内に停滞レンジ中央へ戻るものは、ショートの勢いが弱い疑いがある。ただし、そこで機械的に全撤退すると期待値も削られた。
- `6本以内に1R未達なら撤退` は早すぎて悪化。`12本以内に1R未達なら撤退` はPractical Allとサポート60-119本で改善したため、次の管理ルール候補。
- Primary 1ヶ月安値停滞は、サンプル18件では固定2Rがまだ最も素直。サポート60-119本は強いが、2025-2026のOOSが未発生のため過信しない。
- 直後フォロースルーや中央戻りは、エントリー前には分からないため入口フィルタではなく、建玉後の観察・撤退判断として扱う。

## 出力CSV

- `enriched_stagnation.csv`
- `stagnation_feature_summary.csv`
- `stagnation_combo_summary.csv`
- `stagnation_management_summary.csv`
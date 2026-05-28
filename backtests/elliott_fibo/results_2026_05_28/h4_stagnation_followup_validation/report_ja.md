# H4 安値停滞 追加検証

Status: 検証途中。前回の発見を、入口ルールと出口管理に分けて再検証。

注: 実戦想定に近づけるため、`trigger_mode=stagnation` を基準にし、同じ通貨・同じエントリー時刻は1回だけに重複除去して集計。

## 検証した仮説

- `サポート保持60-119本` は本当に強いのか。
- `GBPJPY寄せ` と `AUDJPY/USDJPY除外` は有効か。
- `6本以内に戻る` は即撤退ではなく、12本時間切れと組み合わせるべきか。
- `12本以内に1R未達なら撤退` は、特定サンプルだけの偶然か。

## 重要ルール比較

| rule | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| support60_119_no_AUD_USD | mid6_then_no12_only | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_core4 | mid6_then_no12_only | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_no_AUD_USD | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_core4 | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_depth_close | fixed_2R_no_1R_by_12bars | 6 | 100.00 | 10.40 | 1.73 | inf | 0.00 | 0 | EURJPY,GBPJPY,XAUUSD |
| support60_119_depth_close | mid6_then_no12_only | 6 | 100.00 | 10.40 | 1.73 | inf | 0.00 | 0 | EURJPY,GBPJPY,XAUUSD |
| support60_119_no_AUD_USD | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_core4 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_all | mid6_then_no12_only | 8 | 87.50 | 11.23 | 1.40 | 11.56 | 0.00 | 1 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_all | fixed_2R_no_1R_by_12bars | 8 | 87.50 | 11.23 | 1.40 | 11.56 | 0.00 | 1 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD |
| support60_119_depth_close | fixed_2R | 6 | 83.33 | 8.82 | 1.47 | 9.64 | 1.02 | 1 | EURJPY,GBPJPY,XAUUSD |
| support60_119_GBPJPY | fixed_2R_no_1R_by_12bars | 4 | 100.00 | 6.48 | 1.62 | inf | 0.00 | 0 | GBPJPY |
| support60_119_GBPJPY | mid6_then_no12_only | 4 | 100.00 | 6.48 | 1.62 | inf | 0.00 | 0 | GBPJPY |
| support60_119_all | fixed_2R | 8 | 75.00 | 9.66 | 1.21 | 5.63 | 1.02 | 1 | AUDJPY,CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_no_AUD_USD | fixed_2R | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | mid6_then_no12_only | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | fixed_2R_no_1R_by_12bars | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| support60_119_GBPJPY | fixed_2R | 4 | 75.00 | 4.91 | 1.23 | 5.81 | 1.02 | 1 | GBPJPY |
| primary_L120_all | fixed_2R | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_all | mid6_then_no12_only | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_all | fixed_2R_no_1R_by_12bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | fixed_2R_no_1R_by_12bars | 37 | 48.65 | 11.71 | 0.32 | 1.59 | 4.76 | 4 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | mid6_then_no12_only | 37 | 45.95 | 10.36 | 0.28 | 1.49 | 4.76 | 4 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_GBPJPY | mid6_then_no12_only | 11 | 54.55 | 5.33 | 0.48 | 2.04 | 1.50 | 2 | GBPJPY |
| practical_GBPJPY | fixed_2R_no_1R_by_12bars | 11 | 54.55 | 5.33 | 0.48 | 2.04 | 1.50 | 2 | GBPJPY |
| practical_no_AUD_USD | fixed_2R | 37 | 43.24 | 8.36 | 0.23 | 1.37 | 4.76 | 4 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_GBPJPY | fixed_2R | 11 | 45.45 | 3.75 | 0.34 | 1.61 | 3.08 | 3 | GBPJPY |

## スコア上位ルール

| rule | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_L120_core4 | fixed_2R | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_core4 | mid6_then_no12_only | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_core4 | fixed_2R_no_1R_by_12bars | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_no_AUD_USD | fixed_2R | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | mid6_then_no12_only | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | fixed_2R_no_1R_by_12bars | 15 | 66.67 | 13.71 | 0.91 | 3.46 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_core4 | mid6_exit | 11 | 54.55 | 9.22 | 0.84 | 4.65 | 1.07 | 2 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_all | fixed_2R | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_all | mid6_then_no12_only | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_all | fixed_2R_no_1R_by_12bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_core4 | fixed_1_5R | 11 | 72.73 | 8.55 | 0.78 | 3.71 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| primary_L120_all | mid6_exit | 18 | 44.44 | 9.38 | 0.52 | 2.53 | 2.53 | 3 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | fixed_1_5R | 15 | 66.67 | 8.71 | 0.58 | 2.56 | 2.42 | 2 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | mid6_exit | 15 | 46.67 | 8.47 | 0.56 | 2.68 | 2.53 | 3 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| primary_L120_no_AUD_USD | half_1R_BE_rest_2R | 15 | 80.00 | 6.71 | 0.45 | 3.13 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | fixed_2R_no_1R_by_12bars | 37 | 48.65 | 11.71 | 0.32 | 1.59 | 4.76 | 4 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_no_AUD_USD | mid6_exit | 37 | 35.14 | 10.79 | 0.29 | 1.75 | 3.10 | 6 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_all_lookbacks | mid6_exit | 42 | 33.33 | 10.64 | 0.25 | 1.65 | 3.10 | 6 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,USDJPY,XAUUSD |
| primary_L120_all | fixed_1_5R | 18 | 61.11 | 8.11 | 0.45 | 2.06 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| practical_core4 | mid6_exit | 26 | 34.62 | 8.90 | 0.34 | 2.01 | 3.09 | 6 | CHFJPY,EURJPY,GBPJPY,XAUUSD |

## サポート60-119本: 通貨別

| symbol | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | fixed_2R | 4 | 75.00 | 4.91 | 1.23 | 5.81 | 1.02 |
| EURJPY | fixed_2R | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| XAUUSD | fixed_2R | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |
| CHFJPY | fixed_2R | 1 | 100.00 | 1.90 | 1.90 | inf | 0.00 |
| AUDJPY | fixed_2R | 1 | 0.00 | -1.06 | -1.06 | 0.00 | 0.00 |
| GBPJPY | fixed_2R_no_1R_by_12bars | 4 | 100.00 | 6.48 | 1.62 | inf | 0.00 |
| EURJPY | fixed_2R_no_1R_by_12bars | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| XAUUSD | fixed_2R_no_1R_by_12bars | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |
| CHFJPY | fixed_2R_no_1R_by_12bars | 1 | 100.00 | 1.90 | 1.90 | inf | 0.00 |
| AUDJPY | fixed_2R_no_1R_by_12bars | 1 | 0.00 | -1.06 | -1.06 | 0.00 | 0.00 |

## サポート60-119本: lookback別

| lookback_label | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5m | fixed_2R | 1 | 0.00 | -1.02 | -1.02 | 0.00 | 0.00 |
| 0.75m | fixed_2R | 1 | 100.00 | 1.97 | 1.97 | inf | 0.00 |
| 1m | fixed_2R | 6 | 83.33 | 8.71 | 1.45 | 9.18 | 0.00 |
| 0.5m | fixed_2R_no_1R_by_12bars | 1 | 100.00 | 0.55 | 0.55 | inf | 0.00 |
| 0.75m | fixed_2R_no_1R_by_12bars | 1 | 100.00 | 1.97 | 1.97 | inf | 0.00 |
| 1m | fixed_2R_no_1R_by_12bars | 6 | 83.33 | 8.71 | 1.45 | 9.18 | 0.00 |

## サポート保持期間の近傍スイープ

| scope | age_window | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 40-89 | fixed_2R | 5 | 80.00 | 6.89 | 1.38 | 7.75 | 1.02 |
| GBPJPY | 40-89 | fixed_2R_no_1R_by_12bars | 5 | 100.00 | 8.47 | 1.69 | inf | 0.00 |
| all_symbols | 60-119 | fixed_2R | 8 | 75.00 | 9.66 | 1.21 | 5.63 | 1.02 |
| all_symbols | 70-139 | fixed_2R | 7 | 71.43 | 7.66 | 1.09 | 4.64 | 1.04 |
| all_symbols | 80-159 | fixed_2R | 7 | 57.14 | 4.64 | 0.66 | 2.48 | 1.04 |
| all_symbols | 40-89 | fixed_2R | 9 | 44.44 | 2.66 | 0.30 | 1.51 | 2.04 |
| all_symbols | 24-59 | fixed_2R | 7 | 42.86 | 1.68 | 0.24 | 1.40 | 1.13 |
| all_symbols | 50-99 | fixed_2R | 7 | 42.86 | 1.81 | 0.26 | 1.44 | 2.04 |
| all_symbols | 100-199 | fixed_2R | 7 | 42.86 | 1.62 | 0.23 | 1.39 | 2.09 |
| all_symbols | 120-239 | fixed_2R | 5 | 40.00 | 0.83 | 0.17 | 1.27 | 2.09 |
| all_symbols | 60-119 | fixed_2R_no_1R_by_12bars | 8 | 87.50 | 11.23 | 1.40 | 11.56 | 0.00 |
| all_symbols | 70-139 | fixed_2R_no_1R_by_12bars | 7 | 71.43 | 7.66 | 1.09 | 4.64 | 1.04 |
| all_symbols | 80-159 | fixed_2R_no_1R_by_12bars | 7 | 57.14 | 4.64 | 0.66 | 2.48 | 1.04 |
| all_symbols | 40-89 | fixed_2R_no_1R_by_12bars | 9 | 55.56 | 4.23 | 0.47 | 2.00 | 2.04 |
| all_symbols | 50-99 | fixed_2R_no_1R_by_12bars | 7 | 57.14 | 3.38 | 0.48 | 2.09 | 2.04 |
| all_symbols | 24-59 | fixed_2R_no_1R_by_12bars | 7 | 42.86 | 1.68 | 0.24 | 1.40 | 1.13 |
| all_symbols | 100-199 | fixed_2R_no_1R_by_12bars | 7 | 42.86 | 1.62 | 0.23 | 1.39 | 2.09 |
| all_symbols | 120-239 | fixed_2R_no_1R_by_12bars | 5 | 40.00 | 0.83 | 0.17 | 1.27 | 2.09 |
| core4 | 60-119 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 |
| core4 | 70-139 | fixed_2R | 6 | 83.33 | 8.72 | 1.45 | 9.39 | 1.04 |
| core4 | 80-159 | fixed_2R | 5 | 80.00 | 6.75 | 1.35 | 7.49 | 1.04 |
| core4 | 40-89 | fixed_2R | 6 | 66.67 | 5.87 | 0.98 | 3.88 | 1.02 |
| core4 | 50-99 | fixed_2R | 5 | 60.00 | 3.89 | 0.78 | 2.91 | 1.02 |
| core4 | 100-199 | fixed_2R | 5 | 60.00 | 3.73 | 0.75 | 2.79 | 1.05 |
| core4 | 60-119 | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 |
| core4 | 70-139 | fixed_2R_no_1R_by_12bars | 6 | 83.33 | 8.72 | 1.45 | 9.39 | 1.04 |
| core4 | 40-89 | fixed_2R_no_1R_by_12bars | 6 | 83.33 | 7.45 | 1.24 | 8.32 | 0.00 |
| core4 | 80-159 | fixed_2R_no_1R_by_12bars | 5 | 80.00 | 6.75 | 1.35 | 7.49 | 1.04 |
| core4 | 50-99 | fixed_2R_no_1R_by_12bars | 5 | 80.00 | 5.46 | 1.09 | 6.37 | 0.00 |
| core4 | 100-199 | fixed_2R_no_1R_by_12bars | 5 | 60.00 | 3.73 | 0.75 | 2.79 | 1.05 |
| no_AUD_USD | 60-119 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 |
| no_AUD_USD | 70-139 | fixed_2R | 6 | 83.33 | 8.72 | 1.45 | 9.39 | 1.04 |

## 時間切れ撤退スイープ

| sample | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_GBPJPY | no_1R_by_12bars | 11 | 54.55 | 5.33 | 0.48 | 2.04 | 1.50 | 2 |
| practical_GBPJPY | no_1R_by_20bars | 11 | 54.55 | 4.99 | 0.45 | 1.98 | 1.84 | 2 |
| practical_GBPJPY | no_1R_by_16bars | 11 | 54.55 | 4.84 | 0.44 | 1.94 | 1.99 | 2 |
| practical_GBPJPY | no_1R_by_10bars | 11 | 45.45 | 4.72 | 0.43 | 1.91 | 2.11 | 3 |
| practical_GBPJPY | fixed_2R | 11 | 45.45 | 3.75 | 0.34 | 1.61 | 3.08 | 3 |
| practical_GBPJPY | no_1R_by_24bars | 11 | 45.45 | 3.75 | 0.34 | 1.61 | 3.08 | 3 |
| practical_GBPJPY | no_1R_by_8bars | 11 | 45.45 | 3.03 | 0.28 | 1.57 | 2.85 | 3 |
| practical_GBPJPY | no_1R_by_6bars | 11 | 36.36 | 1.07 | 0.10 | 1.20 | 2.83 | 3 |
| practical_GBPJPY | no_1R_by_4bars | 11 | 36.36 | -1.34 | -0.12 | 0.77 | 4.29 | 3 |
| practical_all | no_1R_by_10bars | 42 | 45.24 | 10.43 | 0.25 | 1.46 | 4.76 | 4 |
| practical_all | no_1R_by_12bars | 42 | 45.24 | 10.14 | 0.24 | 1.43 | 4.76 | 4 |
| practical_all | no_1R_by_16bars | 42 | 42.86 | 8.87 | 0.21 | 1.37 | 4.76 | 4 |
| practical_all | no_1R_by_20bars | 42 | 45.24 | 8.78 | 0.21 | 1.36 | 4.76 | 4 |
| practical_all | no_1R_by_8bars | 42 | 45.24 | 6.45 | 0.15 | 1.29 | 4.76 | 4 |
| practical_all | fixed_2R | 42 | 40.48 | 6.24 | 0.15 | 1.23 | 4.76 | 4 |
| practical_all | no_1R_by_24bars | 42 | 40.48 | 6.24 | 0.15 | 1.23 | 4.76 | 4 |
| practical_all | no_1R_by_6bars | 42 | 40.48 | 5.16 | 0.12 | 1.24 | 5.01 | 5 |
| practical_all | no_1R_by_4bars | 42 | 38.10 | 3.74 | 0.09 | 1.20 | 5.45 | 5 |
| practical_no_AUD_USD | no_1R_by_10bars | 37 | 48.65 | 11.75 | 0.32 | 1.61 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_12bars | 37 | 48.65 | 11.71 | 0.32 | 1.59 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_16bars | 37 | 45.95 | 10.99 | 0.30 | 1.55 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_20bars | 37 | 48.65 | 10.91 | 0.29 | 1.54 | 4.76 | 4 |
| practical_no_AUD_USD | fixed_2R | 37 | 43.24 | 8.36 | 0.23 | 1.37 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_24bars | 37 | 43.24 | 8.36 | 0.23 | 1.37 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_8bars | 37 | 48.65 | 7.68 | 0.21 | 1.40 | 4.76 | 4 |
| practical_no_AUD_USD | no_1R_by_6bars | 37 | 40.54 | 5.12 | 0.14 | 1.27 | 5.01 | 5 |
| practical_no_AUD_USD | no_1R_by_4bars | 37 | 40.54 | 3.88 | 0.10 | 1.23 | 5.45 | 5 |
| primary_L120_all | fixed_2R | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_10bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_12bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_16bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_20bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_24bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 |
| primary_L120_all | no_1R_by_8bars | 18 | 61.11 | 10.73 | 0.60 | 2.46 | 2.42 | 2 |
| primary_L120_all | no_1R_by_6bars | 18 | 55.56 | 8.75 | 0.49 | 2.17 | 2.42 | 2 |
| primary_L120_all | no_1R_by_4bars | 18 | 55.56 | 7.79 | 0.43 | 2.20 | 1.40 | 2 |

## 通貨除外スイープ

| scope | sample | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_AUDJPY_USDJPY | practical | fixed_2R | 37 | 43.24 | 8.36 | 0.23 | 1.37 | 4.76 |
| exclude_AUDJPY | practical | fixed_2R | 38 | 42.11 | 7.36 | 0.19 | 1.31 | 4.76 |
| exclude_USDJPY | practical | fixed_2R | 41 | 41.46 | 7.25 | 0.18 | 1.28 | 4.76 |
| core4_only | practical | fixed_2R | 26 | 42.31 | 6.16 | 0.24 | 1.40 | 3.08 |
| all_symbols | practical | fixed_2R | 42 | 40.48 | 6.24 | 0.15 | 1.23 | 4.76 |
| GBPJPY_only | practical | fixed_2R | 11 | 45.45 | 3.75 | 0.34 | 1.61 | 3.08 |
| exclude_AUDJPY_USDJPY | practical | fixed_2R_no_1R_by_12bars | 37 | 48.65 | 11.71 | 0.32 | 1.59 | 4.76 |
| exclude_AUDJPY | practical | fixed_2R_no_1R_by_12bars | 38 | 47.37 | 11.25 | 0.30 | 1.55 | 4.76 |
| exclude_USDJPY | practical | fixed_2R_no_1R_by_12bars | 41 | 46.34 | 10.59 | 0.26 | 1.46 | 4.76 |
| all_symbols | practical | fixed_2R_no_1R_by_12bars | 42 | 45.24 | 10.14 | 0.24 | 1.43 | 4.76 |
| core4_only | practical | fixed_2R_no_1R_by_12bars | 26 | 46.15 | 8.16 | 0.31 | 1.58 | 3.08 |
| GBPJPY_only | practical | fixed_2R_no_1R_by_12bars | 11 | 54.55 | 5.33 | 0.48 | 2.04 | 1.50 |
| exclude_AUDJPY | support60_119 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 |
| exclude_AUDJPY_USDJPY | support60_119 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 |
| core4_only | support60_119 | fixed_2R | 7 | 85.71 | 10.72 | 1.53 | 11.50 | 1.02 |
| all_symbols | support60_119 | fixed_2R | 8 | 75.00 | 9.66 | 1.21 | 5.63 | 1.02 |
| exclude_USDJPY | support60_119 | fixed_2R | 8 | 75.00 | 9.66 | 1.21 | 5.63 | 1.02 |
| GBPJPY_only | support60_119 | fixed_2R | 4 | 75.00 | 4.91 | 1.23 | 5.81 | 1.02 |
| exclude_AUDJPY | support60_119 | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 |
| exclude_AUDJPY_USDJPY | support60_119 | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 |
| core4_only | support60_119 | fixed_2R_no_1R_by_12bars | 7 | 100.00 | 12.29 | 1.76 | inf | 0.00 |
| all_symbols | support60_119 | fixed_2R_no_1R_by_12bars | 8 | 87.50 | 11.23 | 1.40 | 11.56 | 0.00 |
| exclude_USDJPY | support60_119 | fixed_2R_no_1R_by_12bars | 8 | 87.50 | 11.23 | 1.40 | 11.56 | 0.00 |
| GBPJPY_only | support60_119 | fixed_2R_no_1R_by_12bars | 4 | 100.00 | 6.48 | 1.62 | inf | 0.00 |

## 期間別チェック

| rule | exit_model | period | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| practical_GBPJPY | fixed_2R | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| practical_GBPJPY | fixed_2R | test_2021_2024 | 2 | 50.00 | 0.97 | 0.48 | 1.96 | 0.00 |
| practical_GBPJPY | fixed_2R | train_2015_2020 | 8 | 37.50 | 0.80 | 0.10 | 1.16 | 2.07 |
| practical_GBPJPY | fixed_2R_no_1R_by_12bars | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| practical_GBPJPY | fixed_2R_no_1R_by_12bars | test_2021_2024 | 2 | 50.00 | 0.97 | 0.48 | 1.96 | 0.00 |
| practical_GBPJPY | fixed_2R_no_1R_by_12bars | train_2015_2020 | 8 | 50.00 | 2.38 | 0.30 | 1.58 | 1.05 |
| practical_no_AUD_USD | fixed_2R | oos_2025_2026 | 2 | 50.00 | 0.94 | 0.47 | 1.90 | 1.04 |
| practical_no_AUD_USD | fixed_2R | test_2021_2024 | 11 | 54.55 | 6.42 | 0.58 | 2.23 | 1.13 |
| practical_no_AUD_USD | fixed_2R | train_2015_2020 | 24 | 37.50 | 1.00 | 0.04 | 1.06 | 4.08 |
| practical_no_AUD_USD | fixed_2R_no_1R_by_12bars | oos_2025_2026 | 2 | 50.00 | 0.94 | 0.47 | 1.90 | 1.04 |
| practical_no_AUD_USD | fixed_2R_no_1R_by_12bars | test_2021_2024 | 11 | 54.55 | 6.42 | 0.58 | 2.23 | 1.13 |
| practical_no_AUD_USD | fixed_2R_no_1R_by_12bars | train_2015_2020 | 24 | 45.83 | 4.35 | 0.18 | 1.32 | 4.08 |
| primary_L120_all | fixed_2R | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| primary_L120_all | fixed_2R | test_2021_2024 | 6 | 66.67 | 5.73 | 0.95 | 3.64 | 1.13 |
| primary_L120_all | fixed_2R | train_2015_2020 | 11 | 54.55 | 5.90 | 0.54 | 2.08 | 2.10 |
| primary_L120_all | fixed_2R_no_1R_by_12bars | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| primary_L120_all | fixed_2R_no_1R_by_12bars | test_2021_2024 | 6 | 66.67 | 5.73 | 0.95 | 3.64 | 1.13 |
| primary_L120_all | fixed_2R_no_1R_by_12bars | train_2015_2020 | 11 | 54.55 | 5.90 | 0.54 | 2.08 | 2.10 |
| primary_L120_no_AUD_USD | fixed_2R | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| primary_L120_no_AUD_USD | fixed_2R | test_2021_2024 | 5 | 60.00 | 3.76 | 0.75 | 2.73 | 1.13 |
| primary_L120_no_AUD_USD | fixed_2R | train_2015_2020 | 9 | 66.67 | 7.97 | 0.89 | 3.34 | 1.29 |
| primary_L120_no_AUD_USD | fixed_2R_no_1R_by_12bars | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| primary_L120_no_AUD_USD | fixed_2R_no_1R_by_12bars | test_2021_2024 | 5 | 60.00 | 3.76 | 0.75 | 2.73 | 1.13 |
| primary_L120_no_AUD_USD | fixed_2R_no_1R_by_12bars | train_2015_2020 | 9 | 66.67 | 7.97 | 0.89 | 3.34 | 1.29 |
| support60_119_all | fixed_2R | test_2021_2024 | 2 | 100.00 | 3.96 | 1.98 | inf | 0.00 |
| support60_119_all | fixed_2R | train_2015_2020 | 6 | 66.67 | 5.70 | 0.95 | 3.73 | 1.02 |
| support60_119_all | fixed_2R_no_1R_by_12bars | test_2021_2024 | 2 | 100.00 | 3.96 | 1.98 | inf | 0.00 |
| support60_119_all | fixed_2R_no_1R_by_12bars | train_2015_2020 | 6 | 83.33 | 7.28 | 1.21 | 7.84 | 0.00 |
| support60_119_no_AUD_USD | fixed_2R | test_2021_2024 | 2 | 100.00 | 3.96 | 1.98 | inf | 0.00 |
| support60_119_no_AUD_USD | fixed_2R | train_2015_2020 | 5 | 80.00 | 6.76 | 1.35 | 7.63 | 1.02 |
| support60_119_no_AUD_USD | fixed_2R_no_1R_by_12bars | test_2021_2024 | 2 | 100.00 | 3.96 | 1.98 | inf | 0.00 |
| support60_119_no_AUD_USD | fixed_2R_no_1R_by_12bars | train_2015_2020 | 5 | 100.00 | 8.34 | 1.67 | inf | 0.00 |

## 暫定解釈

- 重複除去後、`サポート保持60-119本` は 26件ではなく実質8件。優秀だが件数不足なので、採用条件ではなく強い観察タグとして扱う。
- 実戦候補として一番きれいに残ったのは `Primary L120 + core4`。core4は GBPJPY/CHFJPY/XAUUSD/EURJPY で、SILVER/AUDJPY/USDJPYを外す形。
- AUDJPY/USDJPY除外は、広いPracticalでもPrimaryでも改善方向。特にAUDJPYはサポート60-119本の負けを作っていた。
- GBPJPY単独は強いが、重複除去後は11件だけ。汎用ルールというより、優先監視通貨として扱う。
- 12本以内1R未達撤退は、Primary L120ではほぼ効果なし。広いPracticalやsupport60-119では改善するが、これは補助管理案。
- 6本撤退はやはり早すぎる。10-12本が候補で、16-20本も大きく崩れない。24本は固定2Rとほぼ同じ。
- 6本以内の停滞レンジ中央戻りは、入口では使えない。即撤退より、10-12本以内1R未達の時間切れ管理で吸収する方が自然。

## 出力CSV

- `rule_exit_summary.csv`
- `period_summary.csv`
- `support60_119_by_symbol.csv`
- `support60_119_by_lookback.csv`
- `support_age_window_sweep.csv`
- `time_stop_sweep.csv`
- `symbol_exclusion_sweep.csv`
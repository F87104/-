# H4 安値停滞 精度向上検証

Status: 検証途中。Pine実装に向けて、説明しやすい品質フィルタだけで精度を上げられるかを確認。

## 母集団

- Primary L120: H4で過去120本安値更新後の安値停滞下抜け。
- 共通フィルタ: ADX>=30、risk<=1.5ATR、BB幅3-8ATR。
- 同一通貨・同一エントリー時刻は1回に重複除去。

## 追加した品質フィルタ

- 品質フィルタ: 下抜け深さ `>=0.10ATR`、かつ下抜け足の終値位置 `<=0.50`。
- 厳選フィルタ: 品質フィルタに加えて、support age が10本以内なら下抜け深さ `>=0.20ATR` を要求。
- 目的: 浅い下抜けや、新しい安値を弱く割っただけの形を避ける。

## 重要ルール比較

| rule | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_core4_strict | fixed_2R | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_strict | no_1R_by_12bars | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_strict | fixed_2R | 10 | 90.00 | 16.19 | 1.62 | 13.53 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_no_AUD_USD_strict | no_1R_by_12bars | 10 | 90.00 | 16.19 | 1.62 | 13.53 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4_quality | fixed_2R | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_quality | no_1R_by_12bars | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_age30_119 | fixed_2R | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_age30_119 | no_1R_by_12bars | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_strict | fixed_1_5R | 8 | 100.00 | 11.71 | 1.46 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_quality | fixed_1_5R | 9 | 88.89 | 10.67 | 1.19 | 11.27 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_age30_119 | fixed_1_5R | 6 | 100.00 | 8.75 | 1.46 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_strict | fixed_1_5R | 10 | 90.00 | 11.69 | 1.17 | 10.04 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4 | fixed_2R | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4 | no_1R_by_12bars | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_all | fixed_2R | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_all | no_1R_by_12bars | 18 | 61.11 | 13.61 | 0.76 | 2.78 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4 | fixed_1_5R | 11 | 72.73 | 8.55 | 0.78 | 3.71 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_all | fixed_1_5R | 18 | 61.11 | 8.11 | 0.45 | 2.06 | 2.42 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |

## スコア上位

| rule | exit_model | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_losing_streak | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base_core4_strict | fixed_2R | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_strict | no_1R_by_12bars | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_strict | fixed_2R | 10 | 90.00 | 16.19 | 1.62 | 13.53 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_no_AUD_USD_strict | no_1R_by_12bars | 10 | 90.00 | 16.19 | 1.62 | 13.53 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4_quality | fixed_2R | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_quality | no_1R_by_12bars | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_quality | fixed_2R | 12 | 83.33 | 16.96 | 1.41 | 8.27 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_no_AUD_USD_quality | no_1R_by_12bars | 12 | 83.33 | 16.96 | 1.41 | 8.27 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4_age30_119 | fixed_2R | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_age30_119 | no_1R_by_12bars | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_strict | fixed_1_5R | 8 | 100.00 | 11.71 | 1.46 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_all_strict | fixed_2R | 13 | 76.92 | 16.09 | 1.24 | 5.78 | 1.29 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_all_strict | no_1R_by_12bars | 13 | 76.92 | 16.09 | 1.24 | 5.78 | 1.29 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_no_AUD_USD_age30_119 | fixed_2R | 7 | 85.71 | 10.62 | 1.52 | 10.38 | 1.13 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_no_AUD_USD_age30_119 | no_1R_by_12bars | 7 | 85.71 | 10.62 | 1.52 | 10.38 | 1.13 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_all_quality | fixed_2R | 15 | 73.33 | 16.86 | 1.12 | 4.83 | 1.29 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_all_quality | no_1R_by_12bars | 15 | 73.33 | 16.86 | 1.12 | 4.83 | 1.29 | 2 | AUDJPY,CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4_strict | mid6_exit | 8 | 75.00 | 10.68 | 1.33 | 10.99 | 1.07 | 2 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_quality | fixed_1_5R | 9 | 88.89 | 10.67 | 1.19 | 11.27 | 0.00 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_core4_age30_119 | fixed_1_5R | 6 | 100.00 | 8.75 | 1.46 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_strict | fixed_1_5R | 10 | 90.00 | 11.69 | 1.17 | 10.04 | 1.29 | 1 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4_quality | mid6_exit | 9 | 66.67 | 10.16 | 1.13 | 7.41 | 1.07 | 2 | CHFJPY,EURJPY,GBPJPY,XAUUSD |
| base_no_AUD_USD_strict | half_1R_BE_rest_2R | 10 | 100.00 | 9.19 | 0.92 | inf | 0.00 | 0 | CHFJPY,EURJPY,GBPJPY,SILVER,XAUUSD |
| base_core4 | fixed_2R | 11 | 72.73 | 12.55 | 1.14 | 4.98 | 1.08 | 1 | CHFJPY,EURJPY,GBPJPY,XAUUSD |

## 期間別

| rule | period | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base_core4 | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| base_core4 | test_2021_2024 | 4 | 75.00 | 4.89 | 1.22 | 5.70 | 1.04 |
| base_core4 | train_2015_2020 | 6 | 66.67 | 5.68 | 0.95 | 3.69 | 1.08 |
| core4_quality | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| core4_quality | test_2021_2024 | 3 | 100.00 | 5.93 | 1.98 | inf | 0.00 |
| core4_quality | train_2015_2020 | 5 | 80.00 | 6.76 | 1.35 | 7.51 | 0.00 |
| core4_strict | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| core4_strict | test_2021_2024 | 3 | 100.00 | 5.93 | 1.98 | inf | 0.00 |
| core4_strict | train_2015_2020 | 4 | 100.00 | 7.80 | 1.95 | inf | 0.00 |
| no_AUD_USD_strict | oos_2025_2026 | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| no_AUD_USD_strict | test_2021_2024 | 3 | 100.00 | 5.93 | 1.98 | inf | 0.00 |
| no_AUD_USD_strict | train_2015_2020 | 6 | 83.33 | 8.28 | 1.38 | 7.40 | 1.29 |

## 通貨別

| rule | symbol | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base_core4 | GBPJPY | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 |
| base_core4 | CHFJPY | 3 | 66.67 | 2.83 | 0.94 | 3.72 | 0.00 |
| base_core4 | EURJPY | 2 | 50.00 | 0.94 | 0.47 | 1.90 | 0.00 |
| base_core4 | XAUUSD | 2 | 50.00 | 0.86 | 0.43 | 1.80 | 1.08 |
| core4_quality | GBPJPY | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 |
| core4_quality | CHFJPY | 3 | 66.67 | 2.83 | 0.94 | 3.72 | 0.00 |
| core4_quality | EURJPY | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| core4_quality | XAUUSD | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |
| core4_strict | GBPJPY | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 |
| core4_strict | CHFJPY | 2 | 100.00 | 3.87 | 1.93 | inf | 0.00 |
| core4_strict | EURJPY | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| core4_strict | XAUUSD | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |
| no_AUD_USD_strict | GBPJPY | 4 | 100.00 | 7.92 | 1.98 | inf | 0.00 |
| no_AUD_USD_strict | CHFJPY | 2 | 100.00 | 3.87 | 1.93 | inf | 0.00 |
| no_AUD_USD_strict | EURJPY | 1 | 100.00 | 1.98 | 1.98 | inf | 0.00 |
| no_AUD_USD_strict | XAUUSD | 1 | 100.00 | 1.94 | 1.94 | inf | 0.00 |
| no_AUD_USD_strict | SILVER | 2 | 50.00 | 0.48 | 0.24 | 1.37 | 1.29 |

## 負け・除外監査

| audit | symbol | entry_time | period | base_r_after_cost | support_age_bars | break_depth_atr | break_close_location | pre_break_regime | passes_strict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kept_winner | XAUUSD | 2015-06-05 12:00:00 | train_2015_2020 | 1.94 | 111 | 0.21 | 0.24 | mixed_or_wide_range | True |
| kept_winner | GBPJPY | 2016-10-10 04:00:00 | train_2015_2020 | 1.98 | 48 | 0.43 | 0.11 | mixed_or_wide_range | True |
| kept_winner | GBPJPY | 2018-05-25 08:00:00 | train_2015_2020 | 1.98 | 68 | 0.17 | 0.23 | mixed_or_wide_range | True |
| kept_winner | CHFJPY | 2019-04-22 16:00:00 | train_2015_2020 | 1.90 | 114 | 0.18 | 0.41 | mixed_or_wide_range | True |
| kept_winner | EURJPY | 2022-03-03 12:00:00 | test_2021_2024 | 1.98 | 116 | 0.15 | 0.00 | range_support_break | True |
| kept_winner | GBPJPY | 2023-12-13 12:00:00 | test_2021_2024 | 1.98 | 73 | 0.21 | 0.23 | range_support_break | True |
| kept_winner | CHFJPY | 2024-11-29 00:00:00 | test_2021_2024 | 1.97 | 1 | 0.26 | 0.41 | trend_continuation_break | True |
| kept_winner | GBPJPY | 2025-01-15 08:00:00 | oos_2025_2026 | 1.98 | 3 | 0.42 | 0.49 | trend_continuation_break | True |
| loss | CHFJPY | 2017-01-17 08:00:00 | train_2015_2020 | -1.04 | 9 | 0.18 | 0.22 | trend_continuation_break | False |
| loss | XAUUSD | 2017-06-21 16:00:00 | train_2015_2020 | -1.08 | 1 | 0.09 | 0.52 | trend_continuation_break | False |
| loss | EURJPY | 2021-11-10 04:00:00 | test_2021_2024 | -1.04 | 120 | 0.08 | 0.11 | range_support_break | False |

## 閾値感度

| depth_min | fresh_depth_min | trades | win_rate | total_r | avg_r | pf | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 0.20 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.10 | 0.23 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.10 | 0.25 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.12 | 0.20 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.12 | 0.23 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.12 | 0.25 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.15 | 0.20 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.15 | 0.23 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.15 | 0.25 | 8 | 100.00 | 15.71 | 1.96 | inf | 0.00 |
| 0.10 | 0.15 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.10 | 0.17 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.12 | 0.15 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.12 | 0.17 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.15 | 0.15 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.15 | 0.17 | 9 | 88.89 | 14.67 | 1.63 | 15.12 | 0.00 |
| 0.17 | 0.20 | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 |
| 0.17 | 0.23 | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 |
| 0.17 | 0.25 | 6 | 100.00 | 11.75 | 1.96 | inf | 0.00 |
| 0.05 | 0.20 | 9 | 88.89 | 14.67 | 1.63 | 15.11 | 1.04 |
| 0.05 | 0.23 | 9 | 88.89 | 14.67 | 1.63 | 15.11 | 1.04 |

## 暫定解釈

- `Primary L120 core4` はそのままでも良いが、浅い下抜けを避けると精度が上がる。
- `break_depth>=0.10ATR` は、core4の負け3件中2件を落とし、勝ちを落とさなかった。
- `support age<=10ならbreak_depth>=0.20ATR` は、残った弱いfresh support負けを落とし、OOSのGBPJPY勝ちを残した。
- 厳選フィルタ後のcore4は8件全勝だが、件数が少ない。これは本番ロットではなく、Pineの `実戦用シグナル` 候補。
- SILVERを戻すと件数と総Rは増えるが、SILVERの急落継続失敗を1件拾う。精度重視ならcore4維持。
- 出口は固定2Rがまだ最も素直。12本撤退はPrimary L120では改善が小さく、広いPractical条件用の補助案。

## 実装候補

1. 候補ラベル: Primary L120 core4。
2. 実戦候補ラベル: 候補 + `break_depth>=0.10ATR` + `break_close_location<=0.50`。
3. 厳選ラベル: 実戦候補 + `support_age>10 or break_depth>=0.20ATR`。
4. support60-119はエントリー条件ではなく、強い観察タグとして表示。

## 出力CSV

- `rule_summary.csv`
- `period_summary.csv`
- `symbol_summary.csv`
- `failure_audit.csv`
- `threshold_sweep.csv`
- `primary_trades.csv`
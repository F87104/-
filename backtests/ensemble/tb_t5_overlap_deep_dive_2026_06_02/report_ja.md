# TB + T5 Overlap Deep Dive

作成日: 2026-06-02

## 目的

TB+T5アンサンブルの結果から、T5を単純な追加手法ではなく、TBより早い初動サインとして扱えるかを確認した。

## T5重複バケット

| overlap_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| free | bucket_free | 18 | 55.56% | 11.81 | 0.656 | 2.47 | 3.02 | 3 |
| overlap_opposite_or_mixed | bucket_overlap_opposite_or_mixed | 2 | 0.00% | -1.29 | -0.644 | 0.00 | 1.01 | 2 |
| overlap_same_direction | bucket_overlap_same_direction | 10 | 80.00% | 14.81 | 1.481 | 14.77 | 0.02 | 1 |

## T5重複バケット x トリガー

| overlap_bucket | trigger_type | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| free | rebreak | bucket_trigger_free_rebreak | 11 | 54.55% | 6.87 | 0.625 | 2.36 | 2.01 | 2 |
| free | stagnation | bucket_trigger_free_stagnation | 4 | 50.00% | 1.96 | 0.491 | 1.97 | 1.01 | 1 |
| free | stagnation+rebreak | bucket_trigger_free_stagnation+rebreak | 3 | 66.67% | 2.98 | 0.992 | 3.96 | 1.01 | 1 |
| overlap_opposite_or_mixed | rebreak | bucket_trigger_overlap_opposite_or_mixed_rebreak | 2 | 0.00% | -1.29 | -0.644 | 0.00 | 1.01 | 2 |
| overlap_same_direction | rebreak | bucket_trigger_overlap_same_direction_rebreak | 2 | 50.00% | 1.96 | 0.979 | 89.57 | 0.00 | 1 |
| overlap_same_direction | stagnation | bucket_trigger_overlap_same_direction_stagnation | 5 | 80.00% | 6.89 | 1.377 | 7.53 | 0.00 | 1 |
| overlap_same_direction | stagnation+rebreak | bucket_trigger_overlap_same_direction_stagnation+rebreak | 3 | 100.00% | 5.97 | 1.990 | inf | 0.00 | 0 |

## T5重複バケット x 通貨

| symbol | overlap_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHFJPY | free | symbol_bucket_CHFJPY_free | 3 | 66.67% | 2.94 | 0.981 | 3.93 | 1.00 | 1 |
| CHFJPY | overlap_same_direction | symbol_bucket_CHFJPY_overlap_same_direction | 1 | 100.00% | 2.00 | 1.996 | inf | 0.00 | 0 |
| EURJPY | free | symbol_bucket_EURJPY_free | 2 | 50.00% | 0.97 | 0.486 | 1.96 | 0.00 | 1 |
| GBPJPY | free | symbol_bucket_GBPJPY_free | 5 | 40.00% | 0.97 | 0.194 | 1.32 | 1.01 | 2 |
| GBPJPY | overlap_opposite_or_mixed | symbol_bucket_GBPJPY_overlap_opposite_or_mixed | 1 | 0.00% | -1.01 | -1.009 | 0.00 | 0.00 | 1 |
| GBPJPY | overlap_same_direction | symbol_bucket_GBPJPY_overlap_same_direction | 3 | 100.00% | 5.95 | 1.984 | inf | 0.00 | 0 |
| SILVER | overlap_same_direction | symbol_bucket_SILVER_overlap_same_direction | 1 | 0.00% | -1.05 | -1.054 | 0.00 | 0.00 | 1 |
| USDJPY | free | symbol_bucket_USDJPY_free | 4 | 50.00% | 1.97 | 0.494 | 1.98 | 1.01 | 2 |
| USDJPY | overlap_same_direction | symbol_bucket_USDJPY_overlap_same_direction | 4 | 75.00% | 5.94 | 1.485 | 269.73 | 0.00 | 1 |
| XAUUSD | free | symbol_bucket_XAUUSD_free | 4 | 75.00% | 4.95 | 1.237 | 5.91 | 1.01 | 1 |
| XAUUSD | overlap_opposite_or_mixed | symbol_bucket_XAUUSD_overlap_opposite_or_mixed | 1 | 0.00% | -0.28 | -0.280 | 0.00 | 0.00 | 1 |
| XAUUSD | overlap_same_direction | symbol_bucket_XAUUSD_overlap_same_direction | 1 | 100.00% | 1.98 | 1.980 | inf | 0.00 | 0 |

## TB側から見たT5コンテキスト

| tb_context_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tb_no_t5_context | tb_context_tb_no_t5_context | 369 | 39.30% | 187.40 | 0.508 | 1.79 | 11.94 | 11 |
| tb_with_opp_or_mixed_t5_context | tb_context_tb_with_opp_or_mixed_t5_context | 2 | 50.00% | 1.92 | 0.961 | 2.83 | 0.00 | 1 |
| tb_with_same_dir_t5_context | tb_context_tb_with_same_dir_t5_context | 10 | 40.00% | 5.29 | 0.529 | 1.81 | 4.21 | 5 |

## T5 + 後続TB ペア合算

| overlap_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overlap_opposite_or_mixed | pair_bucket_overlap_opposite_or_mixed | 2 | 50.00% | 0.63 | 0.316 | 1.48 | 0.00 | 1 |
| overlap_same_direction | pair_bucket_overlap_same_direction | 10 | 80.00% | 20.10 | 2.010 | 6.91 | 1.08 | 1 |

## T5保有中にTBが出た時の管理テスト

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T5_original | 30 | 60.00% | 25.33 | 0.844 | 3.43 | 4.35 | 5 |
| T5_close_on_opposite_or_mixed_TB | 30 | 60.00% | 25.06 | 0.835 | 3.34 | 4.79 | 5 |
| T5_close_on_any_TB | 30 | 66.67% | 18.42 | 0.614 | 2.91 | 3.74 | 4 |

## シナリオ比較

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TB_only | 381 | 39.37% | 194.61 | 0.511 | 1.79 | 11.94 | 11 |
| TB_plus_T5_free_only | 399 | 40.10% | 206.42 | 0.517 | 1.82 | 11.94 | 11 |
| TB_plus_T5_free_and_same_overlap_full | 409 | 41.08% | 221.23 | 0.541 | 1.87 | 11.94 | 11 |
| TB_plus_T5_free_and_same_overlap_half | 409 | 41.08% | 213.82 | 0.523 | 1.84 | 11.94 | 11 |
| TB_plus_T5_free_and_same_overlap_quarter | 409 | 41.08% | 210.12 | 0.514 | 1.83 | 11.94 | 11 |
| TB_plus_all_T5 | 411 | 40.88% | 219.94 | 0.535 | 1.86 | 11.94 | 11 |
| same_symbol_first_wins | 399 | 40.85% | 212.73 | 0.533 | 1.86 | 11.94 | 11 |
| T5_only | 30 | 60.00% | 25.33 | 0.844 | 3.43 | 4.35 | 5 |
| T5_free_only | 18 | 55.56% | 11.81 | 0.656 | 2.47 | 3.02 | 3 |
| T5_overlap_same_direction_only | 10 | 80.00% | 14.81 | 1.481 | 14.77 | 0.02 | 1 |
| T5_overlap_opposite_or_mixed_only | 2 | 0.00% | -1.29 | -0.644 | 0.00 | 1.01 | 2 |

## T5重複詳細

| symbol | trigger_type | entry_time | exit_time | r | overlap_bucket | overlap_tb_r_sum | overlap_tb_directions | overlap_tb_after_t5_hours_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | stagnation+rebreak | 2015-07-27 08:00:00 | 2015-08-21 00:00:00 | 1.989 | free | 0.000 |  | nan |
| SILVER | stagnation | 2015-10-12 08:00:00 | 2015-11-02 12:00:00 | -1.054 | overlap_same_direction | -1.264 | long | 390.000 |
| USDJPY | stagnation | 2015-12-07 12:00:00 | 2015-12-09 12:00:00 | -1.008 | free | 0.000 |  | nan |
| XAUUSD | rebreak | 2016-02-24 12:00:00 | 2016-04-06 12:00:00 | -0.280 | overlap_opposite_or_mixed | -1.051 | short | 781.000 |
| USDJPY | rebreak | 2016-04-19 12:00:00 | 2016-04-29 00:00:00 | -1.006 | free | 0.000 |  | nan |
| GBPJPY | stagnation+rebreak | 2016-05-25 08:00:00 | 2016-06-01 08:00:00 | -1.006 | free | 0.000 |  | nan |
| GBPJPY | stagnation+rebreak | 2016-08-24 00:00:00 | 2016-09-01 08:00:00 | 1.991 | overlap_same_direction | -1.032 | long | 123.000 |
| CHFJPY | rebreak | 2016-11-30 12:00:00 | 2016-12-14 20:00:00 | 1.967 | free | 0.000 |  | nan |
| USDJPY | stagnation | 2016-12-07 08:00:00 | 2016-12-15 00:00:00 | 1.996 | free | 0.000 |  | nan |
| XAUUSD | rebreak | 2017-05-26 08:00:00 | 2017-06-06 08:00:00 | 1.974 | free | 0.000 |  | nan |
| GBPJPY | rebreak | 2017-08-15 04:00:00 | 2017-08-17 16:00:00 | -1.012 | free | 0.000 |  | nan |
| USDJPY | rebreak | 2018-10-30 04:00:00 | 2018-12-10 04:00:00 | -0.022 | overlap_same_direction | -1.062 | long | 171.000 |
| USDJPY | stagnation | 2019-02-04 04:00:00 | 2019-03-01 08:00:00 | 1.991 | overlap_same_direction | -1.050 | long | 518.000 |
| EURJPY | stagnation | 2019-02-04 08:00:00 | 2019-02-08 00:00:00 | -1.010 | free | 0.000 |  | nan |
| XAUUSD | rebreak | 2019-05-06 00:00:00 | 2019-06-03 16:00:00 | 1.980 | overlap_same_direction | -1.068 | long | 182.000 |
| CHFJPY | rebreak | 2019-06-03 20:00:00 | 2019-06-30 20:00:00 | 1.979 | free | 0.000 |  | nan |
| GBPJPY | rebreak | 2020-02-05 12:00:00 | 2020-02-28 00:00:00 | -1.009 | overlap_opposite_or_mixed | 2.973 | short | 538.000 |
| GBPJPY | rebreak | 2020-07-16 16:00:00 | 2020-07-31 08:00:00 | 2.008 | free | 0.000 |  | nan |
| XAUUSD | rebreak | 2021-01-20 04:00:00 | 2021-02-04 12:00:00 | -1.007 | free | 0.000 |  | nan |
| GBPJPY | stagnation | 2021-10-05 08:00:00 | 2021-10-15 00:00:00 | 1.978 | overlap_same_direction | 2.958 | long | 77.000 |
| GBPJPY | stagnation | 2022-05-23 20:00:00 | 2022-06-08 04:00:00 | 1.985 | free | 0.000 |  | nan |
| GBPJPY | rebreak | 2022-07-11 00:00:00 | 2022-08-01 20:00:00 | -1.005 | free | 0.000 |  | nan |
| EURJPY | rebreak | 2022-08-17 08:00:00 | 2022-09-07 00:00:00 | 1.982 | free | 0.000 |  | nan |
| USDJPY | rebreak | 2022-10-06 16:00:00 | 2022-10-14 12:00:00 | 1.993 | free | 0.000 |  | nan |
| CHFJPY | stagnation+rebreak | 2023-03-22 12:00:00 | 2023-04-28 12:00:00 | 1.996 | overlap_same_direction | 2.960 | long | 483.000 |
| USDJPY | stagnation | 2023-09-25 12:00:00 | 2023-10-31 12:00:00 | 1.987 | overlap_same_direction | 2.941 | long | 729.000 |
| USDJPY | stagnation+rebreak | 2024-04-08 04:00:00 | 2024-04-15 04:00:00 | 1.984 | overlap_same_direction | 2.955 | long | 57.000 |
| GBPJPY | stagnation | 2024-05-17 16:00:00 | 2024-06-27 20:00:00 | 1.982 | overlap_same_direction | -1.048 | long | 617.000 |
| CHFJPY | rebreak | 2024-08-07 04:00:00 | 2024-09-12 12:00:00 | -1.004 | free | 0.000 |  | nan |
| XAUUSD | stagnation+rebreak | 2024-08-26 08:00:00 | 2024-09-23 00:00:00 | 1.993 | free | 0.000 |  | nan |

## 暫定発見

- T5がTB保有中に後から出るケースはなく、T5が先に出て後からTBが重なるケースだけだった。
- 推奨6通貨では、T5単体30件のうち18件はTBと重ならず、12件は後続TBと重なった。
- 後続TBと同方向に重なるT5は10件、T5合計+14.81R、後続TB合計+5.29R。T5を初動、TBを追加確認として見る余地がある。
- 逆方向または混在の重なりは2件のみで、まだ判断不能。実戦では逆方向TBは新規追加ではなく注意タグ扱いが妥当。
- 同方向重なりT5をフルリスクで足すと数字は伸びるが、同一通貨の二重リスクになる。半分リスクまたは0.25R追加が実戦候補。
- 同方向T5コンテキスト中のTB自体は10件で+5.29R、PF 1.81。TB追加だけが特別強いわけではないため、追加よりもT5の保有継続・利確判断の根拠として使う方が自然。
- T5の同方向重なりは、あとからTBが出たという未来情報でしか確定しない。T5エントリー時点のフィルタには使わず、保有中の管理ルールとして扱う。
- T5保有中に逆方向/混在TBが出たら即撤退、という単純ルールはT5単体より悪化した。T5 original +25.33R / PF 3.43 に対し、conflict撤退は +25.06R / PF 3.34。
- T5保有中に同方向TBが出ても、T5をそこで早利確すると +18.42R / PF 2.91 まで期待値を削る。T5は早逃げより、元のSL/TP管理を維持する方が現時点では自然。

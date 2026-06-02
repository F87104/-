# T5 Deeper Research

作成日: 2026-06-02

## 目的

H4 T5 + MACD + BBを、単なる補助手法から実戦運用ルールへ近づけるため、勝ち負けの特徴・削る条件・残す条件を再点検した。

## 全体

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source_all_114 | 114 | 57.02% | 67.03 | 0.588 | 2.54 | 6.67 | 7 |
| practical_c125_all_symbols | 39 | 66.67% | 35.90 | 0.921 | 4.14 | 4.35 | 5 |
| practical_c125_recommended6 | 35 | 65.71% | 32.04 | 0.915 | 4.07 | 4.35 | 5 |

## フィルタ候補

| scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C125_current | 39 | 66.67% | 35.90 | 0.921 | 4.14 | 4.35 | 5 | 現行C125 |
| C125_ex_xau | 28 | 64.29% | 23.40 | 0.836 | 3.56 | 3.02 | 4 | 現行C125からXAUUSDも除外 |
| no_single_rebreak | 18 | 72.22% | 19.66 | 1.092 | 4.87 | 3.07 | 3 | 単独rebreak除外 |
| stag_or_combo_only | 18 | 72.22% | 19.66 | 1.092 | 4.87 | 3.07 | 3 | stagnation系のみ |
| combo_only | 8 | 75.00% | 8.82 | 1.103 | 5.38 | 1.01 | 1 | stagnation+rebreakのみ |
| exclude_gbpjpy_rebreak | 30 | 70.00% | 32.50 | 1.083 | 5.39 | 4.35 | 5 | 推奨6 + GBPJPY単独rebreak除外 |
| bb_le_090 | 24 | 62.50% | 16.39 | 0.683 | 2.80 | 4.07 | 4 | BB位置<=0.90 |
| bb_085_095 | 26 | 69.23% | 28.30 | 1.088 | 5.46 | 2.04 | 3 | BB位置0.85-0.95 |
| bb_width_le4 | 20 | 80.00% | 25.49 | 1.275 | 9.26 | 1.05 | 1 | BB幅<=4ATR |
| macd_gt006 | 13 | 53.85% | 6.82 | 0.524 | 2.28 | 2.29 | 3 | MACD slope3>0.06 |
| rec_bars_le12 | 32 | 65.62% | 27.96 | 0.874 | 3.97 | 4.35 | 5 | signal recovery<=12 |
| close_loc_ge070 | 36 | 63.89% | 29.95 | 0.832 | 3.62 | 4.35 | 5 | 終値位置>=0.70 |
| body_ge060 | 39 | 66.67% | 35.90 | 0.921 | 4.14 | 4.35 | 5 | 実体比率>=0.60 |
| lean_candidate | 13 | 69.23% | 13.81 | 1.063 | 4.39 | 2.01 | 3 | 実戦候補: XAU/AUD除外 + stagnation系 |
| quality_candidate | 11 | 72.73% | 12.83 | 1.166 | 5.18 | 1.01 | 2 | 品質候補: 実戦候補 + BB幅<=5.5 |
| balanced_candidate | 27 | 70.37% | 29.54 | 1.094 | 5.62 | 3.35 | 4 | バランス候補: 推奨6 + GBPJPY単独rebreak除外 + BB幅<=5.5 |
| bb_or_width_candidate | 30 | 70.00% | 31.09 | 1.036 | 5.20 | 2.34 | 3 | 勢い候補: BB位置0.85-0.95 または BB幅<=4 |

## Practical C125 推奨6 通貨別

| symbol | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHFJPY | by_symbol_CHFJPY | 5 | 80.00% | 6.93 | 1.386 | 7.90 | 1.00 | 1 |
| EURJPY | by_symbol_EURJPY | 2 | 50.00% | 0.97 | 0.486 | 1.96 | 0.00 | 1 |
| GBPJPY | by_symbol_GBPJPY | 10 | 60.00% | 6.47 | 0.647 | 2.60 | 2.02 | 2 |
| SILVER | by_symbol_SILVER | 3 | 66.67% | 1.12 | 0.373 | 2.06 | 0.00 | 1 |
| USDJPY | by_symbol_USDJPY | 8 | 62.50% | 7.92 | 0.989 | 4.89 | 1.01 | 2 |
| XAUUSD | by_symbol_XAUUSD | 7 | 71.43% | 8.64 | 1.234 | 7.71 | 1.01 | 1 |

## Practical C125 推奨6 トリガー別

| trigger_type | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rebreak | by_trigger_rebreak | 20 | 60.00% | 14.25 | 0.712 | 3.25 | 2.01 | 2 |
| stagnation | by_trigger_stagnation | 9 | 66.67% | 8.85 | 0.983 | 3.88 | 1.01 | 2 |
| stagnation+rebreak | by_trigger_stagnation+rebreak | 6 | 83.33% | 8.95 | 1.491 | 9.89 | 1.01 | 1 |

## Practical C125 推奨6 BB位置

| bb_pos_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=0.85 | by_bb_pos_bucket_<=0.85 | 12 | 58.33% | 5.61 | 0.468 | 2.10 | 2.05 | 3 |
| 0.85-0.90 | by_bb_pos_bucket_0.85-0.90 | 10 | 60.00% | 7.91 | 0.791 | 2.96 | 2.02 | 2 |
| 0.90-0.95 | by_bb_pos_bucket_0.90-0.95 | 13 | 76.92% | 18.53 | 1.425 | 15.17 | 1.00 | 1 |
| >0.95 | by_bb_pos_bucket_>0.95 | 0 | 0.00% | 0.00 | nan | nan | 0.00 | 0 |

## Practical C125 推奨6 MACD slope

| macd_slope_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=0.03 | by_macd_slope_bucket_<=0.03 | 7 | 71.43% | 7.88 | 1.126 | 4.82 | 1.01 | 1 |
| 0.03-0.06 | by_macd_slope_bucket_0.03-0.06 | 15 | 73.33% | 17.34 | 1.156 | 6.69 | 1.03 | 2 |
| 0.06-0.10 | by_macd_slope_bucket_0.06-0.10 | 4 | 25.00% | -1.03 | -0.259 | 0.66 | 2.01 | 3 |
| >0.10 | by_macd_slope_bucket_>0.10 | 9 | 66.67% | 7.85 | 0.872 | 4.43 | 2.01 | 2 |

## Practical C125 推奨6 回復本数

| recovery_bars_bucket | scenario | trades | win_rate | total_r | avg_r | pf | max_dd_r | max_loss_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=8 | by_recovery_bars_bucket_<=8 | 8 | 62.50% | 6.87 | 0.859 | 3.27 | 2.02 | 2 |
| 9-12 | by_recovery_bars_bucket_9-12 | 20 | 65.00% | 17.24 | 0.862 | 4.20 | 2.29 | 4 |
| 13-16 | by_recovery_bars_bucket_13-16 | 7 | 71.43% | 7.94 | 1.134 | 4.95 | 1.01 | 1 |
| >16 | by_recovery_bars_bucket_>16 | 0 | 0.00% | 0.00 | nan | nan | 0.00 | 0 |

## 勝ち負け特徴量比較

| feature | win_mean | loss_mean | win_median | loss_median | win_q25 | loss_q25 | win_q75 | loss_q75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bb_pos | 0.875 | 0.854 | 0.888 | 0.867 | 0.846 | 0.794 | 0.910 | 0.903 |
| bb_width_atr | 3.880 | 4.534 | 3.700 | 4.464 | 3.305 | 3.914 | 4.634 | 5.014 |
| macd_hist_slope3 | 0.239 | 0.122 | 0.040 | 0.063 | 0.031 | 0.034 | 0.161 | 0.083 |
| signal_recovery_bars | 10.783 | 10.417 | 10.000 | 10.500 | 9.000 | 8.750 | 12.000 | 11.250 |
| signal_fib_ratio | 0.908 | 0.894 | 0.846 | 0.861 | 0.809 | 0.840 | 0.941 | 0.930 |
| v_move_atr | 4.456 | 4.819 | 4.299 | 4.797 | 3.880 | 4.387 | 5.040 | 5.353 |
| v_move_bars | 7.522 | 8.667 | 7.000 | 8.000 | 5.000 | 6.750 | 9.000 | 10.500 |
| v_drop_speed_atr_per_bar | 0.666 | 0.616 | 0.658 | 0.680 | 0.532 | 0.409 | 0.746 | 0.740 |
| body_ratio | 0.765 | 0.786 | 0.766 | 0.778 | 0.651 | 0.726 | 0.874 | 0.847 |
| close_location | 0.864 | 0.878 | 0.891 | 0.869 | 0.800 | 0.848 | 0.960 | 0.918 |
| adx14 | 21.665 | 22.460 | 16.779 | 21.122 | 15.255 | 18.516 | 22.429 | 25.521 |
| ema20_slope_10_atr | 0.188 | 0.238 | 0.209 | 0.175 | -0.327 | -0.087 | 0.602 | 0.625 |
| atr_ratio_50 | 0.972 | 1.030 | 0.942 | 0.995 | 0.903 | 0.935 | 1.043 | 1.127 |
| range5_atr | 2.227 | 2.096 | 2.182 | 1.899 | 1.767 | 1.763 | 2.510 | 2.416 |
| chop14 | 48.137 | 46.138 | 48.331 | 45.953 | 43.318 | 42.814 | 53.598 | 47.774 |

## 暫定結論

- 現行C125は全期間・全7通貨で39件 +35.90R / PF 4.14、推奨6通貨では35件 +32.04R / PF 4.07。まだかなり強い。
- 2015-2024だけで見ると現行C125は34件 +29.20R / PF 3.55、OOS 2025-2026は5件 +6.71R。OOS件数は少ないが崩れてはいない。
- XAUUSDはT5単体では悪くないが、別研究でボラや重複リスクが大きいため、運用上は除外候補として別枠管理が妥当。
- 単独rebreakを丸ごと除外すると件数は減る。通貨別に見ると、弱いのは特にGBPJPY単独rebreakで、CHFJPY/XAUUSDなどのrebreakは残す余地がある。
- 推奨6からGBPJPY単独rebreakだけを除外すると30件 +32.50R / PF 5.39。構造説明と件数のバランスが良い改善候補。
- BB幅<=4ATRは過去研究では超厳選寄り。今回も件数が減りやすいので、通常ロット条件ではなくロット増減条件として扱う方が自然。
- T5の本質は、急落後のV候補を直接買うことではなく、売り失敗後に上側で崩れず再点火する場所だけを買うこと。

## 実戦向け次案

1. C125を基本にする。
2. 通常監視は推奨6、ただしXAUUSDは小ロットまたは別集計。
3. trigger_typeはstagnation+rebreakを最優先、stagnationを通常、単独rebreakは0.25RまたはMACD強い時だけ。
4. GBPJPYの単独rebreakは見送り候補。GBPJPYはstagnation系だけを使う。
5. BB幅<=4ATRはロット通常、4-7ATRは半分、7ATR超は見送り。
6. T5後にTBが同方向で出ても早利確しない。保有継続または小さな追加候補にする。

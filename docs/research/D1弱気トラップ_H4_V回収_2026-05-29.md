# D1売り否定 + H4 V右肩リクレイム 深掘りメモ

作成日: 2026-05-29

## 検証した仮説

仮説:

**D1で売りが否定された直後、H4でV右肩が強く、左肩起点を超えたら買う。**

この仮説は、以下の組み合わせとして検証した。

- D1売り否定: Donchian20下抜け否定_Q / Donchian55下抜け否定_Q / RSI30割れ否定_Q
- D1否定は日足確定後しか分からないため、H4側では翌日から有効
- H4エントリー: 右肩速度が左肩速度以上、または1.2倍以上
- H4エントリー: 終値がV左肩起点を0.05ATR上抜け
- 主候補: `RS120_BODY45_CLOSE60_RR1.5`
- Entry: 次H4足始値
- SL: V安値 - 0.25ATR
- TP: 固定RR1.5
- Research: 2015-2024
- OOS: 2025-2026

## 重要発見

最初の仮説は、そのままでは強くなかった。

**D1売り否定の直後にH4 V右肩リクレイムを買うと、主候補はむしろ悪化した。**

XAUUSD除外、`RS120_BODY45_CLOSE60_RR1.5`:

| rule | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 103 | 51.46% | +26.75R | +0.26R | 1.57 | 9.09R |
| D20Q_5D | 4 | 50.00% | +0.17R | +0.04R | 1.12 | 1.47R |
| D20Q_10D | 10 | 30.00% | -3.38R | -0.34R | 0.48 | 3.39R |
| D20_OR_RSI_15D | 17 | 29.41% | -5.44R | -0.32R | 0.53 | 5.03R |

つまり、D1売り否定は「H4 V右肩買いの追い風」ではなかった。

## 逆発見

本当に強かったのは逆だった。

**直近20-30日以内にD1売り否定がない時だけ、H4 V右肩リクレイムを買う。**

XAUUSD除外、`RS120_BODY45_CLOSE60_RR1.5`:

| rule | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 103 | 51.46% | +26.75R | +0.26R | 1.57 | 9.09R |
| AVOID_D20_OR_RSI_20D | 83 | 55.42% | +30.30R | +0.37R | 1.89 | 5.64R |
| AVOID_D20_OR_RSI_30D | 73 | 57.53% | +30.55R | +0.42R | 2.08 | 4.51R |

期間別:

| rule | period | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | Research_2015_2024 | 88 | 50.00% | +19.70R | +0.22R | 1.48 | 9.09R |
| baseline | OOS_2025_2026 | 15 | 60.00% | +7.06R | +0.47R | 2.30 | 2.01R |
| AVOID_D20_OR_RSI_30D | Research_2015_2024 | 60 | 55.00% | +21.49R | +0.36R | 1.87 | 4.51R |
| AVOID_D20_OR_RSI_30D | OOS_2025_2026 | 13 | 69.23% | +9.06R | +0.70R | 3.63 | 1.01R |

これはかなり重要。取引数は減るが、総R・平均R・PF・DDが全部改善した。

## 解釈

D1売り否定は「強い買い環境」ではあるが、H4 V右肩リクレイムとの相性は別。

おそらく以下の違いがある。

- D1売り否定直後: すでに一度大きく戻しており、H4 Vリクレイムが遅い追随になりやすい
- D1売り否定がないH4 Vリクレイム: 日足レベルではまだ過熱した罠が出ておらず、H4の急落否定が新鮮な転換/継続になりやすい

つまり、H4右肩Vは **D1の売り罠に乗る手法ではなく、D1で罠が出ていないクリーンな状態のH4急落否定を買う手法** と見る方がよい。

## 手法案

暫定名: **Clean H4 V Reclaim**

条件:

1. H4で confirmed pivot high -> confirmed pivot low の急落V
2. 下落幅 >= 3.2ATR
3. 下落速度 >= 0.25ATR/本
4. 右肩速度 >= 左肩速度 x 1.2
5. 右肩終値が左肩起点を0.05ATR上抜け
6. シグナル足の実体 >= 45%
7. シグナル足の終値位置 >= 60%
8. 直近30日以内にD1 Donchian20下抜け否定_Q または D1 RSI30割れ否定_Q がない
9. XAUUSDは除外候補

売買:

- Entry: 次H4足始値
- SL: V安値 - 0.25ATR
- TP: 1.5R
- 保有上限: H4 180本

## 通貨別

`AVOID_D20_OR_RSI_30D + RS120_BODY45_CLOSE60_RR1.5`:

| symbol | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| CHFJPY | 11 | 72.73% | +8.06R | +0.73R | 3.66 | 2.02R |
| AUDJPY | 14 | 57.14% | +6.55R | +0.47R | 2.22 | 2.01R |
| USDJPY | 11 | 63.64% | +6.19R | +0.56R | 3.03 | 2.01R |
| EURJPY | 11 | 54.55% | +3.91R | +0.36R | 1.78 | 3.02R |
| GBPJPY | 16 | 50.00% | +3.19R | +0.20R | 1.46 | 2.38R |
| SILVER | 10 | 50.00% | +2.65R | +0.27R | 1.56 | 2.07R |
| XAUUSD | 12 | 41.67% | +0.38R | +0.03R | 1.05 | 4.05R |

XAUUSDは改善するが、それでも弱い。実戦候補からは外した方が素直。

## 追加候補

もう少し緩めるなら `RS120_RECLAIM_RR1.5` に `AVOID_D20_OR_RSI_30D` を重ねる案もある。

XAUUSD除外:

| rule | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| baseline RS120_RECLAIM | 123 | 48.78% | +23.06R | +0.19R | 1.39 | 8.61R |
| AVOID_D20_OR_RSI_30D | 81 | 56.79% | +32.60R | +0.40R | 2.02 | 5.53R |

ただし、`BODY45_CLOSE60` の方が視覚的にきれいでPine化しやすい。まずは主候補を優先。

## 判断

この深掘りからの実戦的なヒントは、以下。

**D1売り否定はH4 V買いのエントリー理由ではなく、直近に出ていたら見送るフィルタとして使う。**

この発見は手法作りにかなり使える。次にPine化するなら、`Clean H4 V Reclaim` として、D1の直近売り否定なしフィルタを入れるのが自然。

## 出力

- `backtests/elliott_fibo/run_d1_bear_trap_h4_v_reclaim_study.py`
- `backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/report_ja.md`
- `backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/trades.csv`
- `backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/contexts.csv`
- `backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/summary_practical_ex_xau.csv`

# 一般インジケータ否定後の相場反応 検証メモ

作成日: 2026-05-29

## 仮説

一般的に使われるインジケータの売買シグナルがすぐ否定された時、シグナル方向へ入った参加者が捕まり、逆方向へ反応しやすい可能性がある。

今回の目的は、これを感覚ではなく数字で確認し、新しい手法の環境認識やフィルタに使えるかを見ること。

## 検証した否定パターン

- Bollinger Band外側否定: 終値が外側へ出た後、指定本数以内にバンド内へ戻る
- RSI 70/30否定: RSIが70上抜け後に70割れ、または30割れ後に30上抜け
- EMA50/EMA200クロス否定: 終値のクロスが指定本数以内に逆側へ戻る
- MACDシグナルクロス否定: MACDクロス後、指定本数以内に逆クロス
- Donchian 20/55否定: 20本/55本の高安値更新が指定本数以内にブレイク水準内へ戻る

共通売買モデル:

- 時間足: H4 / D1
- Entry: 否定成立後の次足始値
- SL: 1ATR
- TP: 1.5R
- 最大保有: H4は24本、D1は20本
- Research: 2015-2024
- OOS: 2025-2026
- `_Q` は実体40%以上、終値位置が否定方向に強い品質フィルタ付き

## 一番大事な結論

**H4で一般インジケータ否定を見つけて、そのまま逆張りするのは弱い。**

H4上位ですら、最良の `MACD_SIGNAL_CROSS_FAIL_6_Q` が 1657 trades / -24.78R / PF 0.98。その他のH4 Donchian、BB、RSI、EMAはかなり大きくマイナス。

一方で、**D1の下方向ブレイクや売られすぎシグナルが否定された後のロング** は明確に数字が残った。

これは「インジケータ否定そのものが強い」のではなく、**D1で売り手が捕まった後のロング環境** が使える、という解釈が自然。

## 実戦候補

### 候補1: D1 Donchian20 下抜け否定ロング

`DONCHIAN20_FALSE_BREAK_6_Q / long`

| trades | winrate | total_r | avg_r | PF | max_dd | hit_1ATR_first_16 |
|---:|---:|---:|---:|---:|---:|---:|
| 368 | 47.28% | +63.29R | +0.17R | 1.32 | 14.87R | 57.07% |

期間別:

| period | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| Research_2015_2024 | 345 | 45.80% | +47.09R | +0.14R | 1.25 | 14.87R |
| OOS_2025_2026 | 23 | 69.57% | +16.20R | +0.70R | 3.59 | 2.01R |

通貨別では、SILVER / EURJPY / GBPJPY / CHFJPY が良い。USDJPY と AUDJPY は除外候補。

### 候補2: D1 RSI 70/30否定ロング

`RSI_70_30_REJECT_6_Q / long`

| trades | winrate | total_r | avg_r | PF | max_dd | hit_1ATR_first_16 |
|---:|---:|---:|---:|---:|---:|---:|
| 163 | 50.92% | +40.81R | +0.25R | 1.50 | 9.98R | 61.96% |

期間別:

| period | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| Research_2015_2024 | 155 | 50.97% | +38.88R | +0.25R | 1.50 | 9.98R |
| OOS_2025_2026 | 8 | 50.00% | +1.93R | +0.24R | 1.48 | 2.01R |

件数は少なめだが、平均RとPFはDonchian20より良い。単独エントリーではなく、上位環境フィルタとして使いやすい。

### 候補3: D1 Donchian55 下抜け否定ロング

`DONCHIAN55_FALSE_BREAK_6_Q / long`

| trades | winrate | total_r | avg_r | PF | max_dd |
|---:|---:|---:|---:|---:|---:|
| 174 | 46.55% | +24.58R | +0.14R | 1.26 | 14.46R |

20日より件数は少ないが、やや長い期間の安値更新否定として意味はある。実戦では20日否定と重複するため、優先順位の整理が必要。

## 捨ててよさそうなもの

- H4のインジケータ否定を直接逆張りする
- BB外側否定だけで入る
- EMAクロス否定だけで入る
- MACDクロス否定だけで入る
- D1否定ショートを主力にする

ショート側の否定はプラスもあるが、D1ロングほど安定していない。今回の有望パターンは、かなりはっきり **下方向シグナルの否定後ロング** に偏っている。

## 手法化するなら

暫定名: **D1 Bear Trap Context + H4 Trigger**

上位環境:

1. D1終値が20日安値を下抜ける
2. 6本以内に、その20日安値水準の上へ終値で戻る
3. 否定足の実体が40%以上
4. 否定足の終値位置が60%以上
5. その後5-10日間をロング優先環境にする

実際のエントリー:

- D1否定だけでは入らない
- H4で右肩優位V、棚ブレイク、またはT5系の再ブレイクを待つ
- USDJPY / AUDJPY はDonchian20否定ロングでは除外候補
- XAUUSDは弱めなので、別条件または除外を検討

## 次に検証すること

次は、D1否定を単独エントリーではなく環境フィルタとして使い、以下を比較する。

1. `H4 RS120_BODY45_CLOSE60_RR1.5` にD1 Donchian20否定ロング環境を重ねる
2. H4 V棚ブレイクにD1 Donchian20否定ロング環境を重ねる
3. T5 / MACD / BBのロング候補にD1 RSI否定ロング環境を重ねる

狙いは、取引数を少し削ってPFとDDを改善できるか。

## 出力

- `backtests/elliott_fibo/run_indicator_denial_reaction_study.py`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/report_ja.md`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/events.csv`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/summary_overall.csv`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/summary_candidate_direction.csv`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/summary_candidate_period_direction.csv`
- `backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/summary_candidate_symbol.csv`

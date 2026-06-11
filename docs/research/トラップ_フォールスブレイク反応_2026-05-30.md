# Trap / False Break Reaction 検証メモ

作成日: 2026-05-30

## 目的

Market Psychology Pattern Library の **Trap** を数値化した。

狙いは、単に「高値更新失敗」「安値更新失敗」を見つけることではなく、ブレイクに飛び乗った参加者が閉じ込められたあと、本当に逆方向へ走りやすいかを見ること。

## 検証した定義

時間足:

- H4
- D1

節目:

- Donchian 20
- Donchian 55
- Donchian 120

Trap定義:

| 種類 | 条件 |
|---|---|
| wick trap | prior Donchian 高値/安値をヒゲで更新し、同じ足の終値で内側へ戻る |
| close fail | prior Donchian 高値/安値を終値で更新し、6-8本以内に終値で内側へ戻る |

売買モデル:

- Entry: 否定成立足の次足始値
- SL: Trap極値 ± 0.25ATR
- TP: 1.5R
- 最大保有: H4は36本、D1は20本
- コスト: 既存のspread/slippageテーブル
- volume列がないため、出来高増加は True Range / 直近30本TR平均 で代替

品質フィルタ:

| quality | 条件 |
|---|---|
| none | 形のみ |
| body_close | 実体35%以上、終値位置が方向に合う |
| wick_activity | body_close + ヒゲ0.20ATR以上 + range 0.70ATR以上 + 活動量1.05以上 |
| strict | 実体45%以上、終値位置65/35%以上、ヒゲ0.25ATR以上、range 0.85ATR以上、活動量1.10以上 |

## 主要結果

### 1. H4 Trap単独は弱い

H4上位ですらマイナス。

| rule | trades | winrate | total_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|
| CLOSEFAIL_L55_W8_STRICT_RR15 | 360 | 39.44% | -17.00R | 0.92 | 36.11R |
| CLOSEFAIL_L55_W6_ACTIVITY_RR15 | 693 | 40.84% | -18.40R | 0.95 | 56.21R |
| CLOSEFAIL_L120_W6_ACTIVITY_RR15 | 434 | 40.78% | -19.12R | 0.93 | 51.89R |

解釈:

H4の高安値更新否定は頻発しすぎる。Trapとしては見えるが、単独で逆張りエントリーするにはノイズが多い。

## 2. D1の120本Trapだけ候補として残る

実戦候補フィルタ:

- 20 trades以上
- total R > 0
- PF > 1.25

| rule | trades | winrate | total_r | avg_r | PF | max_dd |
|---|---:|---:|---:|---:|---:|---:|
| D1 CLOSEFAIL_L120_W6_BODY_RR15 | 287 | 49.83% | +42.27R | +0.15R | 1.31 | 10.55R |
| D1 WICK_L120_BODY_RR15 | 132 | 48.48% | +18.97R | +0.14R | 1.29 | 6.62R |
| D1 WICK_L120_ACTIVITY_RR15 | 90 | 50.00% | +12.37R | +0.14R | 1.28 | 5.62R |
| D1 WICK_L120_STRICT_RR15 | 42 | 52.38% | +4.80R | +0.11R | 1.25 | 6.81R |

解釈:

Trapは短期足ではなく、**長く意識されていた節目の否定** で初めて意味が出る。

20本や55本より、120本が強い。これは Dormant Breakout / Pain Trade の性質に近い。

## 3. OOSを見ると、採用はまだ保留

最も件数がある `D1 CLOSEFAIL_L120_W6_BODY_RR15`:

| period | trades | winrate | total_r | PF |
|---|---:|---:|---:|---:|
| Research_2015_2024 | 245 | 51.43% | +43.52R | 1.38 |
| OOS_2025_2026 | 42 | 40.48% | -1.25R | 0.95 |

一方、wick系はOOSが強いが、Research側が弱い。

| rule | Research R | OOS R | コメント |
|---|---:|---:|---|
| WICK_L120_BODY_RR15 | +9.56R | +9.41R | OOSは良いがResearchは薄い |
| WICK_L120_ACTIVITY_RR15 | +4.27R | +8.10R | 2025-2026偏重 |
| WICK_L120_STRICT_RR15 | +0.12R | +4.68R | 件数42で少ない |

結論:

単独手法として即採用はできない。D1 120本Trapは「強い文脈」だが、エントリーは別のH4構造を待つ方がよい。

## 4. 方向別

`D1 CLOSEFAIL_L120_W6_BODY_RR15`:

| direction | trades | winrate | total_r | avg_r | PF |
|---|---:|---:|---:|---:|---:|
| long | 84 | 54.76% | +20.55R | +0.24R | 1.58 |
| short | 203 | 47.78% | +21.72R | +0.11R | 1.21 |

ロング側の方が質が高い。これはこれまでのV回復系の研究と一致している。

## 5. 通貨別

`D1 CLOSEFAIL_L120_W6_BODY_RR15`:

| symbol | trades | winrate | total_r | PF |
|---|---:|---:|---:|---:|
| AUDJPY | 36 | 61.11% | +12.60R | 1.96 |
| GBPJPY | 42 | 54.76% | +11.53R | 1.63 |
| SILVER | 26 | 57.69% | +8.30R | 1.85 |
| USDJPY | 42 | 47.62% | +6.75R | 1.31 |
| XAUUSD | 39 | 51.28% | +5.19R | 1.27 |
| EURJPY | 58 | 44.83% | +1.03R | 1.03 |
| CHFJPY | 44 | 38.64% | -3.14R | 0.88 |

AUDJPY/GBPJPY/SILVERが良く、CHFJPYは弱い。

ただし、この時点では通貨別最適化はまだ採用しない。まずは構造の説明が優先。

## 現時点の判断

Trapは検証価値があるが、**H4で直接エントリーする手法ではない**。

一番使えそうなのは次の形。

1. D1で120本級の高値/安値更新否定が出る
2. その直後に飛び乗らない
3. H4で棚、V右肩、再ブレイク、ボラ拡大などの再点火構造を待つ

つまりTrapは、

- Entry triggerではなく、
- Market psychology context
- もしくは「直近に出ていたら見送る/待つ」フィルタ

として使う方が自然。

## 次に検証すること

優先度順:

1. **D1 120本Trap後、H4で棚を作って再ブレイクした時だけ入る**
2. **D1 120本Trap後、すぐ入らず3-15日後のH4 Ignitionだけを拾う**
3. **D1 Trapが直近にないClean H4 V Reclaimとの比較**
4. **D1 120本TrapをDormant Breakout否定として扱い、TrendBreakV1の利確/見送り条件に使う**

## 出力

- `backtests/elliott_fibo/run_trap_false_break_reaction_study.py`
- `backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/report_ja.md`
- `backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/events.csv`
- `backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/summary_overall.csv`
- `backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/summary_practical.csv`


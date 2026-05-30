# Market Psychology Squeeze Strict 研究メモ

作成日: 2026-05-30

## 結論

ユーザー提示の `Market Psychology Strategy (Squeeze + Capitulation)` は、2つの構造を分けて扱うべき。

- **Short Squeeze**: 採用候補。急落後の棚上抜けとして期待値がある。
- **Capitulation直買い**: 単独では保留。ヒゲ底の見た目は良いが、反転継続の確認が足りない。

現時点で一番きれいなのは、`SQZ_STRICT_RR2` から GBPJPY を除外した形。

| variant | trades | winrate | total_r | avg_r | pf | max_dd_r | max_losing_streak | OOS total_r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQZ_DEFAULT_RR2 | 135 | 43.70% | +36.37R | +0.27R | 1.48 | 13.15R | 9 | +15.81R |
| SQZ_STRICT_RR2 | 51 | 47.06% | +18.06R | +0.35R | 1.65 | 4.11R | 4 | +7.87R |
| **SQZ_STRICT_RR2 ex GBPJPY** | **43** | **53.49%** | **+24.72R** | **+0.57R** | **2.21** | **3.09R** | **3** | **+8.89R** |

## 手法の意味

これは「底買い」ではなく、**売り方が追加下落を期待したのに、下がらず、棚の上抜けで買い戻しが始まる局面**を狙う。

心理構造:

1. 急落で売りが増える
2. その後、安値圏で6本前後の棚を作る
3. 追加下落せず、売り方が困り始める
4. 棚高値を終値で抜く
5. 売り方の損切りと新規買いが重なりやすい

## 本線仕様

- 時間足: H4
- 方向: ロングのみ
- 棚本数: 6本
- 棚幅: `<= 2.0 ATR`
- 棚直前の急落: `>= 3.5 ATR`
- エントリー: 棚高値を終値で上抜けした次足始値
- SL: 棚安値 - `0.25 ATR`
- TP: `2.0R`
- 最大保有: 120本
- GBPJPY: 除外候補
- 出来高: ローカルOHLCでは未検証。TradingViewでは `volume > sma(volume,20) * 1.3` をON/OFF比較する。

## 勝ち負け比較から見えたこと

`SQZ_STRICT_RR2 ex GBPJPY` の勝ち組と負け組では、急落幅や実体比率よりも、**エントリー後にすぐ逆行しないこと**が差になっている。

| group | trades | total_r | shelf_atr_mean | drop_atr_mean | body_mean | close_loc_mean | avg_mfe_r | avg_mae_r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| win | 23 | +45.13R | 1.70 | 4.13 | 0.67 | 0.77 | 2.15 | 0.44 |
| loss | 20 | -20.41R | 1.61 | 4.20 | 0.70 | 0.86 | 0.49 | 1.22 |

注意点:

- 負け組の方が実体比率・終値位置はむしろ高い。ここを強くしすぎても改善しにくい。
- 勝ち組は平均MAEが浅い。つまり、棚上抜け後にすぐ沈む形を避ける追加条件が次の研究候補。
- GBPJPYはこの構造と相性が悪い。strictでは 8 trades / -6.66R / PF 0.07。

## 通貨別の示唆

強い:

- XAUUSD: default/strictとも優秀。V系では除外候補だったが、この踏み上げ棚ブレイクでは別扱い。
- EURJPY: defaultで安定。ただしstrictでは件数が少なく落ちるため、strict一択にしすぎない。
- SILVER: strictは良いが件数が少ない。
- USDJPY/AUDJPY: strictで改善。

弱い:

- GBPJPY: 除外候補。急落後の棚上抜けがだましになりやすい。

## Pine実装

TradingView確認用:

- [`pine/research/market_psychology_squeeze_strict_strategy.pine`](../../pine/research/market_psychology_squeeze_strict_strategy.pine)

推奨初期設定:

- `H4チャートのみ売買 = true`
- `GBPJPYを除外 = true`
- `棚の本数 = 6`
- `棚直前の急落窓 = 6`
- `棚幅上限 = 2.0 ATR`
- `急落幅下限 = 3.5 ATR`
- `TP RR = 2.0`
- `出来高増加 = false` から開始し、次に `true / 1.3倍` を比較

## 判定

**研究候補から一段上げて、フォワード監視候補。**

ただし、本番通常ロットはまだ早い。理由は、2015-2021の開発期間ではプラスだが強烈ではなく、2024-2026のOOSでかなり良くなっているため。直近相場に合っている可能性はあるが、構造としては説明できるので、Pineで時刻照合しながら30件程度のフォワード記録を取る価値がある。

次に見るべきこと:

1. TradingViewの実volumeで `volume > sma(volume,20) * 1.3` を追加した時にDDが下がるか
2. 棚上抜け後、1〜2本以内に棚内へ戻る形を早期撤退できるか
3. D1 Trap / H4 V Initial Shelf と重複した時だけ強くなるか
4. GBPJPY除外を固定してよいか、別パラメータなら復活するか

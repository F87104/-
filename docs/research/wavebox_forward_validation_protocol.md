# USDJPY H1 WaveBox Forward Validation Protocol

作成日: 2026-05-26

## 目的

USDJPY H1 WaveBox Rebreak を実戦に入れる前に、TradingView上のPine表示とPython検証のズレを潰し、リアルタイムで同じ判断を再現できるか確認する。

前提条件は以下に固定する。

- `/Users/asamifujita/Documents/Codex/2026-05-21/fx-ai/docs/wavebox_operational_preconditions_v1.md`

ここで見るのは勝率の上振れではなく、次の3点。

- Pineのシグナルが確定足だけで出ているか
- SIGNAL足ではなく、次のH1始値がENTRYになっているか
- 人間が見ても「強い1波、押し目停滞、再ブレイク」に見えるか

## 標準設定

- 対象: USDJPYのみ
- 時間足: H1
- Pine: `pine/wavebox_usdjpy_h1_rebreak_v1_2.pine`
- 標準Mode: `Strict`
- 比較Mode: `Balanced`
- 実戦候補: `GO A+` と `GO A`
- 記録対象: `GO A+`, `GO A`, `SELECT A`, `OBS B`, `SKIP`
- ENTRY: SIGNALの次のH1始値
- TP: 1.5R
- SL: P2またはBox外側 + 0.2ATR
- 最大保有: 72本

## 記録ルール

シグナルが出たら、打つ/見送るに関係なくLogへ記録する。

必須項目:

- Signal Time
- Entry Time
- Direction
- Rank
- Action
- Entry / Stop / Target
- H4 State
- Retrace %
- Box Position
- Break Quality
- Phase
- Screenshot / TV Link
- Decision Note

見送った場合も `Action=SKIP` または `SELECT A` として残す。後から「あれは打たなかったことにする」を禁止する。

## 合格ゲート

初期フォワードは利益ではなく再現性を見る。

| Gate | Minimum | 合格条件 |
| --- | ---: | --- |
| GO A+ / GO A | 20件 | Pine表示、ENTRY、SL/TPが手動確認と一致 |
| GO A+ / GO A | 30件 | 勝率とPFが大崩れせず、見た目にも納得できる |
| SELECT A | 10件 | 打つべきものと見送るべきものの差が説明できる |
| OBS B | 20件 | Bを実戦に残すか捨てるか判断する |

## 実戦投入基準

最初に実弾化できるのは `GO A+` と `GO A` のみ。

`SELECT A` は、目視で以下が全てきれいなときだけ検討する。

- Boxが押しの底付近にある
- ブレイク足が実体で抜けている
- 直近が伸び切り後ではなく再加速初動
- スプレッドや重要指標が邪魔していない

`OBS B` は当面記録のみ。Strict Bは成績上は残っているが、実戦の迷いを増やすので最初から主力にしない。

## 停止ルール

- 3連敗: いったん停止してスクリーンショットレビュー
- 月間 -3R: その月の実弾エントリー停止
- PineとPythonで時刻/方向/Entry/Stopが明確にズレる: 修正まで停止
- スプレッド異常または重要指標直前: 見送り

## Pine/Python差異監査

1件ずつ、次を比較する。

- Signal Time
- Direction
- Rank
- Action
- Entry Time
- Entry
- Stop
- Target

ズレの分類:

- `TIME`: 時刻ズレ。タイムゾーン、確定足、HTF参照を疑う。
- `PRICE`: Entry/SL/TPズレ。四本値、ATR、Box計算を疑う。
- `RANK`: A+/A/B/Actionズレ。Quality Axis分類を疑う。
- `DATA`: TradingViewフィードとCSVデータ差。
- `OK`: 許容範囲内。

## 次の判断

20件までは、手法をいじらない。

30件到達時点でだけ、次を判断する。

- `Strict` のままでよいか
- `Balanced` を採用して回数を増やすか
- `GO A+` と `GO A` のロット差をつけるか
- `OBS B` を完全に捨てるか

現時点の本線は `Strict / GO A+ or GO A`。

## 再現確認 2026-05-26

既存のPython検証を再実行し、フォワード台帳に使う基準値が再現することを確認した。

Practical Audit:

| Mode | Trades | Win rate | Total R | Avg R | PF | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Strict | 69 | 65.22% | +41.47R | +0.601R | 2.69 | 3.13R |
| Balanced | 73 | 64.38% | +42.31R | +0.580R | 2.59 | 3.13R |
| Expansion88 | 88 | 61.36% | +44.28R | +0.503R | 2.27 | 4.17R |

Quality Axes:

| Rule | Trades | Win rate | Total R | Avg R | PF | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Strict A+ or clean A | 38 | 68.42% | +26.09R | +0.687R | 3.15 | 4.18R |
| Balanced A+ or clean A | 39 | 69.23% | +27.56R | +0.707R | 3.27 | 4.18R |
| Expansion88 A+ or clean A | 47 | 68.09% | +31.80R | +0.677R | 3.09 | 4.77R |
| Strict B only | 21 | 61.90% | +10.78R | +0.514R | 2.30 | 2.11R |
| Expansion88 B only | 28 | 53.57% | +8.50R | +0.304R | 1.63 | 3.36R |

判断:

- 主力は `Strict A+ or clean A`。
- 回数を増やす候補は `Balanced A+ or clean A`。
- `Expansion88` はA+ or clean Aだけなら研究価値あり。ただしBは弱いので捨てる。
- Bは成績だけなら残っているが、実戦初期では観察に回す。

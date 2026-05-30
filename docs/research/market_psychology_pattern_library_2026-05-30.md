# Market Psychology Pattern Library

作成日: 2026-05-30

## 目的

チャート形状を単なる形ではなく、参加者心理として分類し、Python/Pineで検証できる条件に変換する。

このライブラリは売買ルールそのものではなく、**相場が動き出す理由を分類するための辞書**として使う。
最初は各パターンをイベント検出し、その後の12/24/48/72本のMFE/MAEを測る。

## 共通の数値化軸

| 軸 | 数値化 |
|---|---|
| 急落/急騰 | N本以内にATR x M以上動く |
| 出来高増加 | TradingView: `volume > sma(volume, 20) * X`。ローカルOHLCではTrue Range活動量で代用 |
| 急反発/急反落 | 戻り速度 >= 先行方向速度 x X |
| 否定 | ブレイク後、元の節目内へ終値で戻る |
| 棚形成 | 直近N本レンジ <= ATR x M |
| 高値/安値更新 | Donchian高値/安値またはpivot起点の終値ブレイク |
| ボラ拡大 | ATR拡大、BB幅拡大、シグナル足TR拡大 |
| 失敗 | 押し/戻り後に崩れず、逆方向へ再ブレイク |

## パターン定義

| ID | パターン | 方向 | 検証可能な条件 | Entry候補 | 除外/注意 | 既存研究との対応 |
|---|---|---|---|---|---|---|
| 01 | Capitulation | Long | 長期下落、最後の急落、出来高増加、長い下ヒゲ、急反転 | 下ヒゲ高値上抜け、または翌足押し目 | 本物のvolumeが重要。OHLCだけでは精度が落ちる | 未実装。Pine向き |
| 02 | Short Squeeze | Long | 急落、急反発、左肩起点/棚高値更新、売りの戻り失敗 | V後の棚ブレイク、または押し高値再ブレイク | XAUUSDは荒れやすい。直接V買いは弱い | H4 Initial Shelf / Ignition Strict |
| 03 | Long Liquidation | Short | 急騰、急反落、右肩で崩れ、高値更新失敗後に棚安値割れ | 高値否定後の下棚割れ | ロング版の単純ミラーは弱い可能性。別検証が必要 | 次検証候補 |
| 04 | Trap | Both | 高値/安値更新後、N本以内にブレイク水準を終値で否定 | 否定足後の押し/戻り再ブレイク | H4単独逆張りは弱い。D1文脈が必要 | Indicator Denial Reaction |
| 05 | Expectation Failure | Long | 急落後、続落できず、高値更新。売り期待が崩れる | 続落失敗後の高値更新 | D1売り否定直後のH4 V買いは悪化した | H4 Ignition Strict |
| 06 | Compression | Both | ATR/BB幅低下、狭いレンジ、出来高低下後の急拡大 | レンジ高値/安値ブレイク | 単独ではノイズ。方向フィルタが必要 | Range5/BB幅フィルタ |
| 07 | FOMO | Long | 押し目なし、高値更新連発、ADX/ATR加速 | ブレイク継続、または浅い押し目 | 天井掴みリスク。利確設計が重要 | TrendBreakV1寄り |
| 08 | Relief Rally | Long | 悪材料/急落後、下げ渋り、出来高増加、上抜け | 下げ渋りレンジ上抜け | ニュース日付はデータ外。出来高/ギャップで代用 | Capitulation近縁 |
| 09 | Pain Trade | Both | 大多数が傾いた方向の否定。片側に伸びた後の逆走 | 過熱方向の失敗後、逆方向ブレイク | ポジションデータなしでは近似になる | RSI/Donchian否定 |
| 10 | Dormant Breakout | Both | 数ヶ月から数年触れていない高値/安値を更新 | 休眠節目更新後の初押し/棚ブレイク | V手法の追加フィルタでは改善せず。別手法化が自然 | 自作大トレンドブレイク |

## 現時点の重要発見

もっとも現在の研究と相性がよいのは、以下の合成。

**Short Squeeze + Expectation Failure + Volatility Expansion**

つまり、

1. 急落する
2. 出来高または価格活動量が増える
3. 急反発する
4. 左肩起点または直近高値を更新する
5. 押しても売りが続かない
6. 押し高値を再上抜ける
7. ボラが拡大する

この形は `H4 Ignition Pattern Search` の `IGNITION_STRICT` として検証済み。

結果:

| rule | trades | winrate | total_r | PF | OOS |
|---|---:|---:|---:|---:|---:|
| IGNITION_STRICT | 8 | 62.50% | +4.32R | 2.40 | +2.98R / 2 trades |
| IGNITION_STRICT ex-XAUUSD | 7 | 71.43% | +5.36R | 3.62 | +2.98R / 2 trades |

件数は少ないが、構造はかなり説明しやすい。
このため、現段階では売買ルールより **点火候補スキャナー**として使う。

## 次に検証する優先順位

1. **Long Liquidation**
   - Short Squeezeの上下反転。
   - ただし、過去の単純ショートミラーは弱かったので、急騰後の「買い方の投げ」に限定する。

2. **Capitulation / Relief Rally**
   - TradingViewのvolumeありで検証する。
   - 条件: 長期下落、急落、volume急増、下ヒゲ、次足高値更新。

3. **Dormant Breakout**
   - V手法のフィルタではなく、独立したブレイク手法として検証する。
   - 条件: 120/360/1250本の休眠高値更新 + 初押し維持 + 再ブレイク。

4. **Compression to Expansion**
   - BB幅/ATRが低下した後のレンジブレイク。
   - 単独ではなく、Dormant BreakoutまたはTrap否定と組み合わせる。

## 実装方針

まずは1つの巨大ストラテジーにしない。

各心理パターンを以下の順で扱う。

1. Event scanner
   - エントリーせず、該当イベントだけ記録する。
   - 12/24/48/72本後のMFE/MAEを測る。

2. Trigger study
   - イベント後の押し目、棚ブレイク、再ブレイクだけを検証する。

3. Strategy
   - 期待値が残ったものだけ売買ルール化する。

4. Pine parity
   - Pythonのイベント時刻とTradingViewのラベル時刻を一致させる。

## Pine化での注意

- FX/CFDのvolumeはブローカー差が大きい。volume条件はON/OFF可能にする。
- Pivotはconfirmedのみ。
- 否定/Trapは確定足の終値で判定する。
- Event labelとEntry labelを分ける。
- シグナルが少ないパターンは、勝率やPFではなく「その後の伸び方」を先に見る。


# 心理パターン辞書 (Pattern Library)

> 10 心理パターンを、Python / Pine で検証できる **数値条件** に変換した辞書。
> [`SKILL.md`](./SKILL.md) / [`framework.md`](./framework.md) の補助資料。

このライブラリは売買ルールそのものではなく、**相場が動き出す理由を分類するための辞書** として使う。
最初は各パターンをイベント検出し、その後の 12 / 24 / 48 / 72 本の MFE / MAE を測る。

---

## 1. 共通の数値化軸 (再掲)

| 軸 | 数値化 |
|---|---|
| 急落 / 急騰 | N 本以内に ATR × M 以上動く |
| 出来高増加 | TradingView: `volume > sma(volume, 20) × X`。ローカル OHLC では True Range 活動量で代用 |
| 急反発 / 急反落 | 戻り速度 ≥ 先行方向速度 × X |
| 否定 | ブレイク後、元の節目内へ終値で戻る |
| 棚形成 | 直近 N 本レンジ ≤ ATR × M |
| 高値 / 安値更新 | Donchian 高安値または pivot 起点の終値ブレイク |
| ボラ拡大 | ATR 拡大、BB 幅拡大、シグナル足 TR 拡大 |
| 失敗 | 押し戻り後に崩れず、逆方向へ再ブレイク |

---

## 2. パターン定義

| ID | パターン | 方向 | 検証可能な条件 | Entry 候補 | 除外 / 注意 |
|---|---|---|---|---|---|
| 01 | Capitulation | Long | 長期下落、最後の急落、出来高増加、長い下ヒゲ、急反転 | 下ヒゲ高値上抜け、または翌足押し目 | 本物の volume が重要。OHLC だけでは精度が落ちる |
| 02 | Short Squeeze | Long | 急落、急反発、左肩起点 / 棚高値更新、売りの戻り失敗 | V 後の棚ブレイク、または押し高値再ブレイク | XAUUSD は荒れやすい。直接 V 買いは弱い |
| 03 | Long Liquidation | Short | 急騰、急反落、右肩で崩れ、高値更新失敗後に棚安値割れ | 高値否定後の下棚割れ | ロング版の単純ミラーは弱い可能性。別検証が必要 |
| 04 | Trap | Both | 高安値更新後、N 本以内にブレイク水準を終値で否定 | 否定足後の押し戻り再ブレイク | H4 単独逆張りは弱い。D1 文脈が必要 |
| 05 | Expectation Failure | Long | 急落後、続落できず、高値更新。売り期待が崩れる | 続落失敗後の高値更新 | D1 売り否定直後の H4 V 買いは悪化した |
| 06 | Compression | Both | ATR / BB 幅低下、狭いレンジ、出来高低下後の急拡大 | レンジ高値 / 安値ブレイク | 単独ではノイズ。方向フィルタが必要 |
| 07 | FOMO | Long | 押し目なし、高値更新連発、ADX / ATR 加速 | ブレイク継続、または浅い押し目 | 天井掴みリスク。利確設計が重要 |
| 08 | Relief Rally | Long | 悪材料 / 急落後、下げ渋り、出来高増加、上抜け | 下げ渋りレンジ上抜け | ニュース日付はデータ外。出来高 / ギャップで代用 |
| 09 | Pain Trade | Both | 大多数が傾いた方向の否定。片側に伸びた後の逆走 | 過熱方向の失敗後、逆方向ブレイク | ポジションデータなしでは近似になる |
| 10 | Dormant Breakout | Both | 数ヶ月から数年触れていない高値 / 安値を更新 | 休眠節目更新後の初押し / 棚ブレイク | V 手法の追加フィルタでは改善せず。別手法化が自然 |

---

## 3. 既存研究との対応 (実装例)

| ID | パターン | 既に検証されている形 | ステータス |
|---|---|---|---|
| 01 | Capitulation | `CAP_DEFAULT_RR2` 等 | 単独直買いは保留 |
| 02 | Short Squeeze | `SQZ_STRICT_RR2 ex GBPJPY` 43 / +24.72R / PF 2.21 | フォワード候補 |
| 03 | Long Liquidation | 旧短側ミラー検証 | 不採用、要再定義 |
| 04 | Trap | `D1 CLOSEFAIL_L120_W6_BODY_RR15` 287 / PF 1.31, OOS PF 0.95 | 単独不採用、文脈用途 |
| 05 | Expectation Failure | `IGNITION_STRICT` の一部 | Squeeze との合成として有効 |
| 06 | Compression | Range5 / BB 幅フィルタとして既存戦略に組み込み済 | 単独は未検証 |
| 07 | FOMO | TrendBreakV1 寄り | 既存本線 |
| 08 | Relief Rally | Capitulation 近縁 | 未独立検証 |
| 09 | Pain Trade | RSI / Donchian 否定として近似 | 文脈フィルタ |
| 10 | Dormant Breakout | 未独立検証 | 次の研究候補 |

---

## 4. 現時点の重要発見

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

この形は `H4 Ignition Pattern Search` の `IGNITION_STRICT` として検証済み:

| rule | trades | winrate | total_r | PF | OOS |
|---|---:|---:|---:|---:|---:|
| IGNITION_STRICT | 8 | 62.50% | +4.32R | 2.40 | +2.98R / 2 trades |
| IGNITION_STRICT ex-XAUUSD | 7 | 71.43% | +5.36R | 3.62 | +2.98R / 2 trades |

件数は少ないが、構造はかなり説明しやすい。現段階では売買ルールより **点火候補スキャナー** として使う。

---

## 5. 次に検証する優先順位

1. **Long Liquidation**
   - Short Squeeze の上下反転。
   - ただし、過去の単純ショートミラーは弱かったので、急騰後の「買い方の投げ」に限定する。

2. **Capitulation / Relief Rally**
   - TradingView の volume ありで検証する。
   - 条件: 長期下落、急落、volume 急増、下ヒゲ、次足高値更新。

3. **Dormant Breakout**
   - V 手法のフィルタではなく、独立したブレイク手法として検証する。
   - 条件: 120 / 360 / 1250 本の休眠高値更新 + 初押し維持 + 再ブレイク。

4. **Compression to Expansion**
   - BB 幅 / ATR が低下した後のレンジブレイク。
   - 単独ではなく、Dormant Breakout または Trap 否定と組み合わせる。

---

## 6. 実装方針

まずは 1 つの巨大ストラテジーにしない。各心理パターンを以下の順で扱う。

| 段階 | 内容 |
|---|---|
| 1. Event scanner | エントリーせず、該当イベントだけ記録。12 / 24 / 48 / 72 本後の MFE / MAE を測る |
| 2. Trigger study | イベント後の押し目、棚ブレイク、再ブレイクだけを検証 |
| 3. Strategy | 期待値が残ったものだけ売買ルール化 |
| 4. Pine parity | Python のイベント時刻と TradingView のラベル時刻を一致 |

---

## 7. Pine 化での注意

- FX / CFD の volume はブローカー差が大きい。volume 条件は ON / OFF 可能にする。
- Pivot は confirmed のみ。
- 否定 / Trap は確定足の終値で判定する。
- Event label と Entry label を分ける。
- シグナルが少ないパターンは、勝率や PF ではなく「その後の伸び方」を先に見る。

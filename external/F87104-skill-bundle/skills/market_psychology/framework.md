# 市場心理 研究フレームワーク (Framework)

> このスキルが扱う「市場心理」の **共通の言葉と数値化軸** をまとめる。
> [`SKILL.md`](./SKILL.md) の補助資料。

---

## 1. 基本姿勢

- チャート形状を「形」として扱わない。**「誰が、何を期待して、何に裏切られたか」** に変換する。
- 心理を直接観測できないので、価格・ボラ・節目・速度の **代理指標** を積み重ねる。
- 1 つの巨大ストラテジーにしない。**Event scanner → Trigger study → Strategy → Pine parity** の 4 段階で扱う。

### 4 段階フロー

| 段階 | 目的 | 出力 |
|---|---|---|
| 1. Event scanner | 該当イベントだけ記録、エントリーせず | 12 / 24 / 48 / 72 本後の MFE / MAE |
| 2. Trigger study | 押し目、棚ブレイク、再ブレイク等の Entry 契機を絞る | trades / PF / DD |
| 3. Strategy | 期待値が残ったものだけ売買ルール化 | 検証コード + Pine |
| 4. Pine parity | Python の時刻と TradingView のラベル時刻を一致 | parity audit |

---

## 2. 共通の数値化軸

| 軸 | 数値化 | 補足 |
|---|---|---|
| 急落 / 急騰 | `N 本以内に ATR × M 以上` 動く | M = 2.8〜5.0、N = 4〜10 本が現実的 |
| 出来高増加 | TradingView: `volume > sma(volume, 20) × X` (X=1.3〜1.8) | ローカル OHLC では True Range / 30 本 TR 平均 で代用 (活動量代理) |
| 急反発 / 急反落 | 右肩速度 ≥ 左肩速度 × X (X=1.0〜1.2) | 「左肩起点」を超えるかも別軸 |
| 否定 (Denial / Trap) | ブレイク後、**終値** で元の節目内へ戻る | ヒゲではなく終値ベースが重要 |
| 棚形成 (Shelf) | 直近 N 本のレンジ ≤ `ATR × M` | N=6, M=1.8〜2.5 が中心 |
| 高値 / 安値更新 | Donchian 高安値 または pivot 起点の **終値ブレイク** | 20 / 55 / 120 本がよく使われる |
| ボラ拡大 | ATR 拡大 / BB 幅拡大 / シグナル足 TR 拡大 | PRECALM (前段ボラ低下) も別軸 |
| 失敗 / Re-ignition | 押し戻り後に崩れず、逆方向へ再ブレイク | Shelf 高値再上抜けが代表 |

### 終値ベースの徹底

- **Trap 判定 / 否定判定 / ブレイク判定** は、ヒゲではなく **終値** を基準にする。
- Pine の `confirmed pivot` も同様。シグナル発生はバー確定後。
- これを徹底しないと、Pine ↔ Python の parity がずれる。

---

## 3. 「文脈」と「Entry trigger」の分け方

研究で繰り返し見えてきた重要な区別:

| 種類 | 性質 | 例 |
|---|---|---|
| **Entry trigger** | 売買シグナルそのもの | H4 棚高値の終値上抜け / V 右肩リクレイム |
| **文脈 (Context)** | エントリーを「許す/見送る」上位条件 | D1 売り否定の有無 / 過熱トレンドの有無 |
| **アンチパターン** | 単独では使えないことを確認済み | H4 Trap 単独逆張り / V 字単独買い |

ルール: **「文脈 AND Entry trigger」で初めて売買、文脈だけでは入らない、Entry trigger だけでも入らない。**

---

## 4. Pine 化での共通ルール

- FX / CFD の `volume` はブローカー差が大きい。volume 条件は **ON / OFF 切替可能** にする。
- Pivot は `confirmed` のみ使う。`request.security` の lookahead は避ける。
- 否定 / Trap は **確定足の終値** で判定する。
- **Event label** と **Entry label** は別の色 / 別のラベル名で出す (parity audit のため)。
- シグナルが少ないパターンは、勝率や PF を最初に見ない。**MFE / MAE / 24-72 本後の伸び方** を先に見る。
- D1 文脈は `request.security(syminfo.tickerid, "D", ..., lookahead=barmerge.lookahead_off)` を徹底し、`[1]` で過去確定値を読む。

---

## 5. データ前提 (推奨)

| 項目 | 内容 |
|---|---|
| OHLC | ローカル CSV (volume なし) を 1 次データとする |
| volume | ローカルでは活動量代理 (TR / 30 本 TR 平均) を使用。本物の volume は Pine で再検証 |
| Research 期間 | 2015-01-01 〜 2024-12-31 |
| OOS 期間 | 2025-01-01 〜 現在 |
| コスト | spread + slippage を R ベースで控除 |
| TF | H4 と D1 が中心。H1 / M15 は補助 |

---

## 6. 単位

| 用語 | 意味 |
|---|---|
| R | 1 リスクあたりの損益 (1R = SL までの距離 = 口座 1% 相当) |
| Total R | 期間中の累計 R |
| PF | Profit Factor = 総利益 R / 総損失 R |
| WR | 勝率 (%) |
| DD | 累計 R の peak-to-trough 最大ドローダウン |
| IS / OOS | In-Sample (2015-2024) / Out-of-Sample (2025-) |
| 棚 / Shelf | 直近 N 本のレンジが ATR × M 以内に収まった停滞構造 |
| Trap | 高安値更新に飛び乗った参加者が、直後に節目内へ戻されて閉じ込められる形 |
| Squeeze | 売り方が踏み上げられる連鎖。本フレームでは「急落後の安値棚上抜け」を指す |
| Capitulation | 投げ売りの最終局面。長い下ヒゲ + 急反転 |

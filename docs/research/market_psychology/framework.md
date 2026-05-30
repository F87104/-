# 市場心理 研究フレームワーク (Framework)

> このリポジトリで「市場心理」を扱う時の **共通の言葉と数値化軸** をまとめる。
> 個別の研究ノートは、この枠組みに沿って書かれている。

**最終更新**: 2026-05-30
**親ドキュメント**: [`README.md`](./README.md)
**出典**: [`market_psychology_pattern_library_2026-05-30.md`](../market_psychology_pattern_library_2026-05-30.md) を整理した版

---

## 1. 基本姿勢

- チャート形状を「形」として扱わない。**「誰が、何を期待して、何に裏切られたか」** に変換する。
- 心理を直接観測できないので、価格・ボラ・節目・速度の **代理指標** を積み重ねる。
- 1つの巨大ストラテジーにしない。**Event scanner → Trigger study → Strategy → Pine parity** の4段階で扱う。

### 4段階フロー

| 段階 | 目的 | 出力 |
|---|---|---|
| 1. Event scanner | 該当イベントだけ記録、エントリーせず | 12/24/48/72本後のMFE/MAE |
| 2. Trigger study | 押し目、棚ブレイク、再ブレイク等のEntry契機を絞る | trades / PF / DD |
| 3. Strategy | 期待値が残ったものだけ売買ルール化 | 検証コード + Pine |
| 4. Pine parity | Pythonの時刻とTradingViewのラベルを一致 | parity audit |

---

## 2. 共通の数値化軸

| 軸 | 数値化 | 補足 |
|---|---|---|
| 急落 / 急騰 | `N本以内にATR × M以上` 動く | M = 2.8〜5.0、N = 4〜10本が現実的 |
| 出来高増加 | TradingView: `volume > sma(volume, 20) × X` (X=1.3〜1.8) | ローカルOHLCでは True Range / 30本TR平均 で代用 (活動量代理) |
| 急反発 / 急反落 | 右肩速度 ≥ 左肩速度 × X (X=1.0〜1.2) | 「左肩起点」を超えるかも別軸 |
| 否定 (Denial / Trap) | ブレイク後、**終値** で元の節目内へ戻る | ヒゲではなく終値ベースが重要 |
| 棚形成 (Shelf) | 直近N本のレンジ ≤ `ATR × M` | N=6, M=1.8〜2.5 が中心 |
| 高値 / 安値更新 | Donchian高値/安値 または pivot起点の **終値ブレイク** | 20 / 55 / 120本がよく使われる |
| ボラ拡大 | ATR拡大 / BB幅拡大 / シグナル足TR拡大 | PRECALM (前段ボラ低下) も別軸 |
| 失敗 / Re-ignition | 押し/戻り後に崩れず、逆方向へ再ブレイク | Shelf高値再上抜けが代表 |

### 終値ベースの徹底

- **Trap判定 / 否定判定 / ブレイク判定** は、ヒゲではなく **終値** を基準にする。
- Pineの `confirmed pivot` も同様。シグナル発生はバー確定後。
- これを徹底しないと、Pine ↔ Pythonの parity がずれる。

---

## 3. 心理パターン10種 (要約版)

| ID | パターン | 方向 | 一文の心理 |
|---|---|---|---|
| 01 | Capitulation | Long | 「もう耐えられない」最後の投げ |
| 02 | Short Squeeze | Long | 「下がらない」売り方の困惑からの踏み上げ |
| 03 | Long Liquidation | Short | 「もう買えない」買い方の投げ |
| 04 | Trap | Both | 「抜けた」と思った人が閉じ込められる |
| 05 | Expectation Failure | Long | 「続落するはず」が崩れる |
| 06 | Compression → Expansion | Both | 「動かない」が続いた後に「一気に動く」 |
| 07 | FOMO | Long | 「乗り遅れたくない」買い |
| 08 | Relief Rally | Long | 「悪材料は織り込んだ」買戻し |
| 09 | Pain Trade | Both | 「みんな同じ方向」の逆走 |
| 10 | Dormant Breakout | Both | 「長く触れていない節目」を超える |

詳細条件と既存研究との対応は [`market_psychology_pattern_library_2026-05-30.md`](../market_psychology_pattern_library_2026-05-30.md) 参照。

---

## 4. 「文脈」と「Entry trigger」の分け方

研究で繰り返し見えてきた重要な区別:

| 種類 | 性質 | 例 |
|---|---|---|
| **Entry trigger** | 売買シグナルそのもの | H4棚高値の終値上抜け / V右肩リクレイム |
| **文脈 (Context)** | エントリーを「許す/見送る」上位条件 | D1売り否定の有無 / 過熱トレンドの有無 |
| **アンチパターン** | 単独では使えないことを確認済み | H4 Trap単独逆張り / V字単独買い |

ルールは: **「文脈 AND Entry trigger」で初めて売買、文脈だけでは入らない、Entry triggerだけでも入らない。**

---

## 5. Pine化での共通ルール

- FX / CFD の `volume` はブローカー差が大きい。volume条件は **ON/OFF切替可能** にする。
- Pivotは `confirmed` のみ使う。`request.security` の lookahead は避ける。
- 否定 / Trapは **確定足の終値** で判定する。
- **Event label** と **Entry label** は別の色/別のラベル名で出す (parity audit のため)。
- シグナルが少ないパターンは、勝率やPFを最初に見ない。**MFE / MAE / 24-72本後の伸び方** を先に見る。
- D1文脈は `request.security(syminfo.tickerid, "D", ..., lookahead=barmerge.lookahead_off)` を徹底し、`[1]` で過去確定値を読む。

---

## 6. データ前提

| 項目 | 内容 |
|---|---|
| OHLC | ローカルCSV (volume無し)。F87104_test配下 |
| volume | ローカルでは活動量代理 (TR / 30本TR平均) を使用。本物のvolumeはPineで再検証 |
| Research期間 | 2015-01-01 〜 2024-12-31 |
| OOS期間 | 2025-01-01 〜 2026-現在 |
| コスト | spread + slippage を Rベースで控除 (`audit/` 配下のテーブル) |
| TF | H4 と D1 が中心。H1 / M15 は補助 |

---

## 7. 「市場心理研究」 vs 「TrendBreakV1 / H4 T5 + MACD + BB」 の関係

本リポジトリの **本番運用** は TrendBreakV1 と H4 T5 + MACD + BB の2本柱 (詳細は [`STRATEGY_GUIDE.md`](../../../STRATEGY_GUIDE.md))。

市場心理研究は、これらを **置き換える** ものではなく、以下の役割で並走させる。

- 既存戦略の **見送りフィルタ** を提供する (例: D1売り否定が直近にあるか)
- 既存戦略の **方向確信度** を上げる (例: D1 120本Trap文脈がある時のロング)
- 新しい **独立手法候補** を吟味する (例: Squeeze Strict / D1 Trap Delayed)
- 本番未採用でも、**辞書としての言葉** を共通化する

つまり、市場心理研究は「2本柱の補強と次の柱の探索」。
本番昇格は、Pine parity + フォワード20〜30件 + DD/PF/OOS要件を満たした手法に限る。

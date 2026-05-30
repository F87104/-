# 市場心理構造 研究ハブ (Market Psychology Structure Research)

> チャート形状を「形」ではなく、**参加者の心理イベント** として数値化し、検証可能な売買候補へ落とし込むための研究ハブ。

**最終更新**: 2026-05-30
**親ドキュメント**: [`docs/BACKTEST_INDEX.md`](../../BACKTEST_INDEX.md) §6-4.5 〜 §6-6 / [`README.md`](../../../README.md)

---

## 1. このハブの目的

市場心理に関するノートは、もともと `docs/research/` 直下に時系列で並んでいた。
ここでは以下を1ヶ所にまとめる。

- **共通の枠組み** (10パターン辞書 + 数値化軸)
- **個別研究** の状態 (候補 / フォワード / 保留 / 不採用)
- **検証コード/レポート/Pine** へのクロスリンク
- **読む順番** と **本番への昇格条件**

各ファイル本体は移動していない (リンク先・コミット履歴の互換性のため)。
このハブは「入り口と地図」の役割。

---

## 2. 最初に読むべき順番

| # | ドキュメント | 役割 |
|---|---|---|
| 1 | [`market_psychology_pattern_library_2026-05-30.md`](../market_psychology_pattern_library_2026-05-30.md) | 10パターン辞書。共通の数値化軸と心理分類 |
| 2 | [`indicator_denial_reaction_2026-05-29.md`](../indicator_denial_reaction_2026-05-29.md) | 一般インジケータ否定後の反応。D1売り否定が文脈として残った |
| 3 | [`d1_bear_trap_h4_v_reclaim_2026-05-29.md`](../d1_bear_trap_h4_v_reclaim_2026-05-29.md) | D1売り否定 + H4 V右肩。「直近にD1売り否定がない時」の方が強い、という逆発見 |
| 4 | [`trap_false_break_reaction_2026-05-30.md`](../trap_false_break_reaction_2026-05-30.md) | Trap (高安値更新の即時否定) を数値化。H4単独は弱く、D1 120本のみ文脈 |
| 5 | [`d1_trap_h4_shelf_strict_2026-05-30.md`](../d1_trap_h4_shelf_strict_2026-05-30.md) | D1 Trap直後ではなく、30〜180日後のH4棚ブレイクだけ買う準本命 |
| 6 | [`market_psychology_squeeze_strict_2026-05-30.md`](../market_psychology_squeeze_strict_2026-05-30.md) | Short Squeeze (急落後の安値棚上抜け) フォワード候補 |
| 7 | [`market_psychology_squeeze_currency_compatibility_2026-05-30.md`](../market_psychology_squeeze_currency_compatibility_2026-05-30.md) | Squeezeの通貨別/組み合わせ別の相性分析 |

1〜2 = 共通枠組み / 3〜4 = フィルタ系の発見 / 5〜7 = 候補手法 という流れ。

---

## 3. 心理パターン辞書 (要約)

詳細: [`market_psychology_pattern_library_2026-05-30.md`](../market_psychology_pattern_library_2026-05-30.md)

| ID | パターン | 方向 | 心理 | 現在のステータス |
|---|---|---|---|---|
| 01 | Capitulation | Long | 投げ売りの最終局面、長い下ヒゲ、急反転 | 単独直買いは保留 (反転継続の確認不足) |
| 02 | Short Squeeze | Long | 急落後の追加下落失敗、棚高値抜けで踏み上げ | **フォワード候補** (§5) |
| 03 | Long Liquidation | Short | 急騰後の右肩崩れ、買い方の投げ | 単純ミラーは不採用 (別検証必要) |
| 04 | Trap | Both | 高安値更新に飛び乗った参加者の閉じ込め | H4単独は不採用、D1 120本のみ文脈フィルタ |
| 05 | Expectation Failure | Long | 急落後の続落失敗、売り期待が崩れる | Squeezeとの合成として有効 (`IGNITION_STRICT`) |
| 06 | Compression | Both | ATR/BB幅低下後の急拡大 | 単独ではノイズ、方向フィルタが必要 |
| 07 | FOMO | Long | 押し目なしの高値更新連発 | TrendBreakV1寄り |
| 08 | Relief Rally | Long | 悪材料/急落後の下げ渋り上抜け | Capitulation近縁、未独立検証 |
| 09 | Pain Trade | Both | 過熱方向の失敗からの逆走 | RSI/Donchian否定として近似 |
| 10 | Dormant Breakout | Both | 数ヶ月〜数年触れていない節目の更新 | 別手法として研究予定 |

**共通の数値化軸** (詳細は辞書本体):

| 軸 | 数値化 |
|---|---|
| 急落/急騰 | N本以内に `ATR × M` 以上動く |
| 棚形成 | 直近N本レンジ ≤ `ATR × M` |
| 急反発/急反落 | 戻り速度 ≥ 先行方向速度 × X |
| 否定 | ブレイク後、元の節目内へ **終値** で戻る |
| ボラ拡大 | ATR拡大 / BB幅拡大 / シグナル足TR拡大 |
| 失敗 | 押し/戻り後に崩れず、逆方向へ再ブレイク |

---

## 4. 個別研究のステータス一覧

| # | 研究 | パターンID | TF | 主候補成績 | OOS | 判定 |
|---|---|---|---|---|---|---|
| R1 | [Pattern Library](../market_psychology_pattern_library_2026-05-30.md) | (辞書) | — | — | — | 共通枠組み |
| R2 | [Indicator Denial Reaction](../indicator_denial_reaction_2026-05-29.md) | 04 / 09 | D1 | `D1 Donchian20否定L` 368 / +63.29R / PF 1.32 | OOS 23 / +16.20R / PF 3.59 | 文脈フィルタとして有効 |
| R3 | [D1 Bear Trap + H4 V Reclaim](../d1_bear_trap_h4_v_reclaim_2026-05-29.md) | 04 (逆発見) | H4 | `AVOID_D20_OR_RSI_30D + RS120_BODY45_CLOSE60` 73 / +30.55R / PF 2.08 / DD 4.51R | OOS 13 / +9.06R / PF 3.63 | **見送りフィルタ** として採用 (Clean H4 V Reclaim) |
| R4 | [Trap / False Break Reaction](../trap_false_break_reaction_2026-05-30.md) | 04 | D1/H4 | `D1 CLOSEFAIL_L120_W6_BODY_RR15` 287 / +42.27R / PF 1.31 | OOS 42 / -1.25R / PF 0.95 | 単独不採用。D1 120本のみ文脈 |
| R5 | [D1 Trap Delayed H4 Shelf Strict](../d1_trap_h4_shelf_strict_2026-05-30.md) | 04 + 02 | H4 | `A30_180 + signal ADX<=30` **9 / +13.35R / PF inf / DD 0.00R** | OOS +4.46R | **準本命** (件数不足、Pine照合中) |
| R6 | [Market Psychology Squeeze Strict](../market_psychology_squeeze_strict_2026-05-30.md) | 02 | H4 | `SQZ_STRICT_RR2 ex GBPJPY` **43 / +24.72R / PF 2.21 / DD 3.09R** | OOS +8.89R | **フォワード候補** |
| R7 | [Squeeze 通貨相性分析](../market_psychology_squeeze_currency_compatibility_2026-05-30.md) | 02 (補助) | H4 | XAUUSD strict 10 / +10.73R / PF 4.45 | OOS +5.95R | XAUUSD = 本命 / GBPJPY = 除外 |

凡例:
- **フォワード候補**: 期待値あり。Pine照合とフォワード記録30件以上で本番昇格を判断
- **準本命**: 構造説明力が高いが件数不足。小ロット/デモで監視
- **文脈フィルタ**: 単独エントリーに使わず、上位環境の判定に使う
- **不採用**: 単独でPF/DD要件未達。アンチパターンとして記録

---

## 5. 一番の現実的な候補 (要約)

### 5-1. Market Psychology Squeeze Strict (R6 + R7)

**心理構造**:

1. 急落で売りが増える
2. 安値圏で6本前後の棚を作る
3. 追加下落せず、売り方が困り始める
4. 棚高値を **終値で抜く**
5. 売り方の損切り + 新規買いが重なる (踏み上げ)

**本線仕様**:

- 時間足: H4 / 方向: Long のみ
- 棚本数: 6 / 棚幅 ≤ 2.0ATR / 直前急落 ≥ 3.5ATR
- Entry: 棚高値を終値で上抜けした次足始値
- SL: 棚安値 − 0.25ATR / TP: 2.0R / 最大保有: 120本
- 通貨: **XAUUSD = 本命 / USDJPY / AUDJPY** (GBPJPYは除外)
- 出来高フィルタ: ローカルOHLCでは未検証。TradingViewで `volume > sma(volume,20) × 1.3` をON/OFF比較する

**成績** (`SQZ_STRICT_RR2 ex GBPJPY`):

| 期間 | trades | WR | total R | PF | DD | losing streak |
|---|---:|---:|---:|---:|---:|---:|
| Research_2015_2024 | 43 | 53.5% | +24.72R | 2.21 | 3.09R | 3 |
| OOS_2024_2026 | (内) | — | +8.89R | — | — | — |

**Pine**: [`pine/research/market_psychology_squeeze_strict_strategy.pine`](../../../pine/research/market_psychology_squeeze_strict_strategy.pine)
**検証コード**: [`backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py`](../../../backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py)
**レポート**: [`backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/report_ja.md)

### 5-2. D1 Trap Delayed H4 Shelf Strict (R5)

**心理構造**:

1. D1で120本級の安値割れ → すぐ終値で戻る (D1 売り否定 / Trap)
2. 直後30日は入らない
3. 30〜180日のうちに、H4で急落V → 上側で6本の棚 → 棚高値ブレイク
4. つまり「売り直しが失敗して再点火する局面」

**本線仕様**:

- 時間足: H4 / 通貨: USDJPY, EURJPY, GBPJPY, AUDJPY (XAUUSD/CHFJPY/SILVERは除外)
- D1 Trap文脈: 30日 ≤ Trap age < 180日
- H4 V条件: 下落 ≥ 2.8ATR / 右肩 ≥ 左肩速度 / 回復率 0.65-1.25
- 棚: 6本 / 幅 ≤ 1.8ATR / V 50%回復ラインを維持
- ブレイク足: 実体 ≥ 40% / 終値位置 ≥ 60% / signal ADX14 ≤ 30
- Entry: 次H4足始値 / SL: 棚安値 − 0.25ATR / TP: 1.5R

**成績** (`selected_CURRENT_A30_180_SIGADX30`):

| 期間 | trades | WR | total R | PF | DD |
|---|---:|---:|---:|---:|---:|
| Research_2015_2024 | 9 | 100% | +13.35R | inf | 0.00R |
| OOS_2024_2026 | — | — | +4.46R | — | — |

件数が9と少ないため、**通常ロットの本番採用はしない**。Pine照合 + フォワード20件以上が条件。

**Pine**: [`pine/research/d1_trap_h4_shelf_strict_strategy.pine`](../../../pine/research/d1_trap_h4_shelf_strict_strategy.pine)
**検証コード**: [`backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py`](../../../backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py)
**レポート**: [`backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/report_ja.md)

---

## 6. 個別研究の判定詳細

### R2: Indicator Denial Reaction → 文脈フィルタ採用

- **H4 単独逆張りは不採用** (最良の `MACD_SIGNAL_CROSS_FAIL_6_Q` でも 1657 trades / -24.78R / PF 0.98)。
- **D1の下方向シグナル否定後ロング** は明確にプラス。
  - D1 Donchian20否定L: 368 / +63.29R / PF 1.32 (OOS 23 / +16.20R / PF 3.59)
  - D1 RSI 70/30否定L: 163 / +40.81R / PF 1.50
- → **D1 Bear Trap Context (環境認識)** として使う。エントリー判断は別構造に任せる。

### R3: D1 Bear Trap + H4 V Reclaim → 逆発見

- 当初仮説 (D1売り否定直後にH4 V右肩を買う) は **悪化** した。
- 逆に **直近20〜30日以内にD1売り否定がない時だけ** H4 V右肩を買うと改善:
  - baseline 103 / +26.75R / PF 1.57 / DD 9.09R
  - AVOID_D20_OR_RSI_30D 73 / +30.55R / PF 2.08 / DD 4.51R
- → **`Clean H4 V Reclaim`** として手法化。D1売り否定は「直近に出ていたら見送る」フィルタ。
- 関連: [`pine/research/clean_h4_v_reclaim_strategy.pine`](../../../pine/research/clean_h4_v_reclaim_strategy.pine)

### R4: Trap / False Break Reaction → 単独不採用

- H4 Trap単独はノイズ過多。`CLOSEFAIL_L55_W8_STRICT_RR15` でも 360 / -17.00R / PF 0.92。
- D1 では 120本Trapだけ候補に残る (287 / +42.27R / PF 1.31) が、**OOS が -1.25R / PF 0.95** で崩れる。
- → Trapは **Entry triggerではなく** 、(a) 直近に出ていたら見送る、(b) D1 120本Trap後の遅延H4再点火を待つ、というフィルタ用途。
- 方向別では Long が PF 1.58、Short が PF 1.21 で **ロング寄り** 。

### R5: D1 Trap Delayed H4 Shelf Strict → 準本命

- D1 Trap直後の即買いは弱い。30日以上経過後 + H4の棚ブレイクのみ採用。
- `selected_CURRENT_A30_180_SIGADX30`: **9 / 100% / +13.35R / PF inf / DD 0.00R** / OOS +4.46R
- 件数9は少ない。**Pine照合とフォワード20件以上** が本番昇格の最低条件。
- 採用候補通貨: USDJPY / EURJPY / GBPJPY / AUDJPY。XAUUSD・CHFJPY・SILVERは外す。

### R6: Market Psychology Squeeze Strict → フォワード候補

- ユーザー提示 Pine `Market Psychology Strategy (Squeeze + Capitulation)` を分解。
  - **Short Squeeze**: 採用候補。急落後の棚上抜けで踏み上げを狙う。
  - **Capitulation 直買い**: 単独では保留。ヒゲ底見た目は良いが反転継続の確認不足。
- `SQZ_STRICT_RR2 ex GBPJPY`: **43 / +24.72R / PF 2.21 / DD 3.09R**、OOS +8.89R。
- 勝ち負け差は急落幅や実体比率ではなく **エントリー後にすぐ逆行しないこと** (勝avg MAE 0.44R / 負avg MAE 1.22R) 。

### R7: Squeeze 通貨相性

| symbol | strict total R | strict PF | strict DD | strict OOS R | 使い方 |
|---|---:|---:|---:|---:|---|
| XAUUSD | +10.73R | 4.45 | 2.07R | +5.95R | A 本命 |
| USDJPY | +4.87R | 1.69 | 2.02R | +1.98R | B strict候補 |
| AUDJPY | +2.90R | 1.95 | 2.04R | +1.99R | B strict候補 |
| SILVER | +7.33R | 4.47 | 1.03R | 0.00R | B− 監視 (OOS不足) |
| EURJPY | -3.09R | 0.39 | 3.05R | -1.02R | strict悪化、default向き |
| CHFJPY | +1.97R | inf | 0.00R | 0.00R | C 保留 (1件のみ) |
| GBPJPY | -6.66R | 0.07 | 5.64R | -1.02R | **除外** |

XAUUSDが本命になる理由 = 急落後のショートカバーが速いため。これは H4 V系で XAUUSDを除外していた話とは別軸。

---

## 7. 全体の操作的な結論

| 役割 | 採用 | 備考 |
|---|---|---|
| **本線エントリー候補** | Squeeze Strict (R6) | XAUUSD/USDJPY/AUDJPY、GBPJPY除外。Pine + フォワード30件で昇格判断 |
| **準本命エントリー候補** | D1 Trap Delayed H4 Shelf (R5) | 件数9、フォワード20件で昇格判断 |
| **環境認識フィルタ** | D1 Bear Trap (R2のD1否定 / R3の見送りロジック) | Clean H4 V Reclaim で実装済み |
| **辞書 / 次の研究タネ** | Pattern Library (R1) | Long Liquidation / Capitulation+Volume / Dormant Breakout は未独立 |
| **アンチパターン** | H4 Trap単独逆張り (R4) | 直接エントリーはノイズ過多 |

---

## 8. 次に検証すること (優先度順)

1. **Squeeze Strict** に TradingViewの実 volume (`volume > sma(volume,20) × 1.3`) を付与してDD/PFが改善するか
2. **Squeeze Strict** で、棚上抜け後1〜2本以内に棚内へ戻る形を早期撤退できるか
3. **R5 ∩ R6** が重複した時だけのエントリー (構造重複ロング) で勝率がさらに上がるか
4. **Long Liquidation** (急騰後の買い方投げ) を独立検証 (短側はミラーが弱かったため別定義が必要)
5. **Capitulation + Volume** を TradingView volume付きで本格検証 (Pattern 01)
6. **Dormant Breakout** (120/360/1250本の休眠節目更新) を独立手法として検証 (Pattern 10)
7. **Compression → Expansion** (BB幅/ATR低下後のレンジブレイク) と Dormant Breakout の合成

---

## 9. 関連ファイル一覧 (フラット)

### 研究ノート (このフォルダの兄弟)

- [`../market_psychology_pattern_library_2026-05-30.md`](../market_psychology_pattern_library_2026-05-30.md)
- [`../market_psychology_squeeze_strict_2026-05-30.md`](../market_psychology_squeeze_strict_2026-05-30.md)
- [`../market_psychology_squeeze_currency_compatibility_2026-05-30.md`](../market_psychology_squeeze_currency_compatibility_2026-05-30.md)
- [`../trap_false_break_reaction_2026-05-30.md`](../trap_false_break_reaction_2026-05-30.md)
- [`../d1_trap_h4_shelf_strict_2026-05-30.md`](../d1_trap_h4_shelf_strict_2026-05-30.md)
- [`../indicator_denial_reaction_2026-05-29.md`](../indicator_denial_reaction_2026-05-29.md)
- [`../d1_bear_trap_h4_v_reclaim_2026-05-29.md`](../d1_bear_trap_h4_v_reclaim_2026-05-29.md)

### バックテストレポート

- [`backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/report_ja.md)
- [`backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/report_ja.md)
- [`backtests/elliott_fibo/results_2026_05_30/d1_trap_delayed_h4_shelf/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/d1_trap_delayed_h4_shelf/report_ja.md)
- [`backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_30/trap_false_break_reaction/report_ja.md)
- [`backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/report_ja.md)
- [`backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/report_ja.md`](../../../backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/report_ja.md)

### Pine実装 (研究版)

- [`pine/research/market_psychology_squeeze_strict_strategy.pine`](../../../pine/research/market_psychology_squeeze_strict_strategy.pine)
- [`pine/research/d1_trap_h4_shelf_strict_strategy.pine`](../../../pine/research/d1_trap_h4_shelf_strict_strategy.pine)
- [`pine/research/clean_h4_v_reclaim_strategy.pine`](../../../pine/research/clean_h4_v_reclaim_strategy.pine)

### 検証コード (Python)

- [`backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py`](../../../backtests/elliott_fibo/run_market_psychology_strategy_tv_check.py)
- [`backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py`](../../../backtests/elliott_fibo/run_d1_trap_h4_shelf_integrated_study.py)
- [`backtests/elliott_fibo/run_d1_trap_delayed_h4_shelf_study.py`](../../../backtests/elliott_fibo/run_d1_trap_delayed_h4_shelf_study.py)
- [`backtests/elliott_fibo/run_trap_false_break_reaction_study.py`](../../../backtests/elliott_fibo/run_trap_false_break_reaction_study.py)
- [`backtests/elliott_fibo/run_d1_bear_trap_h4_v_reclaim_study.py`](../../../backtests/elliott_fibo/run_d1_bear_trap_h4_v_reclaim_study.py)
- [`backtests/elliott_fibo/run_indicator_denial_reaction_study.py`](../../../backtests/elliott_fibo/run_indicator_denial_reaction_study.py)

---

## 10. 用語

| 用語 | 意味 |
|---|---|
| R | 1リスクあたりの損益 (1R = SLまでの距離 = 口座1%相当) |
| Total R | 期間中の累計R |
| PF | Profit Factor = 総利益R / 総損失R |
| WR | 勝率 (%) |
| DD | 累計Rの peak-to-trough 最大ドローダウン |
| IS / OOS | In-Sample (2015-2024) / Out-of-Sample (2025-2026) |
| 棚 / Shelf | 直近N本のレンジが ATR × M 以内に収まった停滞構造 |
| Trap | 高安値更新に飛び乗った参加者が、直後に節目内へ戻されて閉じ込められる形 |
| Squeeze | 売り方が踏み上げられる連鎖。本ハブでは「急落後の安値棚上抜け」を指す |
| Capitulation | 投げ売りの最終局面。長い下ヒゲ + 急反転 |

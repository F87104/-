# 準本命4手法 — 検証続行ロードマップ

作成日: 2026-06-01

## 前提

本番の2本柱（TrendBreakV1 + H4 T5実戦用）は確定済み。  
ここでは **第3・第4候補に昇格しうる研究** だけを並べる。

混線防止ルール:

- 受講生研究（850件・つまずきPine）は **フィルタ/教材**。売買手法候補に含めない。
- `pine/visual/` のインジケータは **観察用**。成績判断・実弾エントリーに使わない（リペイント疑いあり）。
- 昇格条件は **Python/Pine一致 → 0.25Rフォワード30件 → 本柱との重複ルール** の順。

---

## 準本命4選（優先順）

| 優先 | 代号 | 手法 | 方向 | TF | バックテスト | ボトルネック |
|---:|---|---|---|---|---|---|
| **1** | **SQZ** | Market Psychology Squeeze Strict（GBPJPY除外） | ロング | H4 | 43t / +24.7R / PF2.21 / OOS+8.9R | フォワード30件・volumeフィルタ |
| **2** | **VIS** | H4 V Initial Shelf Breakout（PRECALM） | ロング | H4 | 34t / +15.6R / PF2.09 / OOS+4.9R | Pine照合・visualと混同しない |
| **3** | **LSS** | H4 1ヶ月安値更新→安値停滞下抜けショート | ショート | H4 | core4 strict 8t / +15.7R（標本少） | **Pine不一致未解決** |
| **4** | **DTS** | D1 Trap Delayed H4 Shelf Strict | ロング | H4 | 9t / +13.4R / PF inf（標本極少） | 件数・Pine照合 |

---

## 各候補の次アクション

### 1. SQZ — Squeeze Strict

**意味:** 急落後の棚上抜け（売り方の踏み上げ）。底買いではない。

| 項目 | 内容 |
|---|---|
| Pine | [`pine/research/market_psychology_squeeze_strict_strategy.pine`](../../pine/research/market_psychology_squeeze_strict_strategy.pine) |
| 研究メモ | [`market_psychology_squeeze_strict_2026-05-30.md`](market_psychology_squeeze_strict_2026-05-30.md) |
| 通貨 | XAUUSD/EURJPY/USDJPY/SILVER 強め。**GBPJPY除外固定** |

**検証タスク（順番固定）:**

1. TradingViewで Python期待シグナルと **日時一致** を確認（`currency_compatibility_squeeze_strict_by_period.csv` 参照）
2. `volume > sma(20)*1.3` を ON/OFF で DD が下がるか比較
3. 棚上抜け後1〜2本で棚内戻り → 早期撤退ルールをバックテスト
4. **0.25R** でフォワード30件（台帳: [`near_main_forward_validation_log.csv`](../trade_practice_records/near_main_forward_validation_log.csv)）
5. T5/H4 V Initial と同時シグナル時の **重複ルール** を決める（片方のみ）

**昇格条件:** フォワード30件で PF≥1.5 かつ DD≤5R → 第3本柱候補

---

### 2. VIS — H4 V Initial Shelf

**意味:** Vを直接買わず、売り失敗後の **上側6本棚ブレイク** で初動を取る。

| 項目 | 内容 |
|---|---|
| Pine | [`pine/research/h4_v_initial_shelf_breakout_strategy.pine`](../../pine/research/h4_v_initial_shelf_breakout_strategy.pine) |
| 仕様書 | [`backtests/elliott_fibo/results_2026_05_30/h4_v_initial_shelf_deep_dive/final_spec_ja.md`](../../backtests/elliott_fibo/results_2026_05_30/h4_v_initial_shelf_deep_dive/final_spec_ja.md) |
| 照合リスト | [`tradingview_parity_checklist.md`](../../backtests/elliott_fibo/results_2026_05_30/h4_v_initial_shelf_deep_dive/tradingview_parity_checklist.md) |
| 通貨 | USDJPY/EURJPY/GBPJPY/AUDJPY。**XAU/CHF/SILVER除外** |

**検証タスク:**

1. Pine strategy で **34件の entry_time が Python と一致** するか（最優先）
2. `Sharp Drop V Recovery Visual` 等の **visual版で実弾しない**（2026-06-01 USDJPY事例: リペイント疑い）
3. 出口は本線 **1.5R固定**。`ExitFast`（SL0.4ATR/18本）はラベル監視のみ、昇格しない
4. 0.25Rフォワード30件
5. 既存 **H4 T5** との関係: T5=MACD+BB+V候補、VIS=PRECALM+棚。近いが独立 → 同足同方向はロット半減 or 片方

**昇格条件:** Pine完全一致 + フォワード30件 PF≥1.5

---

### 3. LSS — H4 Low Stagnation Short

**意味:** 1ヶ月安値更新後、安値圏停滞の **下抜けショート**（落ちるナイフ売りではない）。

| 項目 | 内容 |
|---|---|
| Pine strategy | [`pine/research/h4_low_stagnation_short_strategy.pine`](../../pine/research/h4_low_stagnation_short_strategy.pine) |
| Pine visual | [`pine/visual/h4_low_stagnation_short_visual.pine`](../../pine/visual/h4_low_stagnation_short_visual.pine) |
| 不一致問題 | [`pine_parity_issue_h4_low_stag_short_2026-05-29.md`](pine_parity_issue_h4_low_stag_short_2026-05-29.md) |
| 精度検証 | [`backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/report_ja.md`](../../backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/report_ja.md) |

**検証タスク:**

1. **Pine parity 修正**（GBPJPY期待4件 vs Pine7件の差を解消）
2. 本線ルール: `Primary L120 core4_strict`（CHFJPY/EURJPY/GBPJPY/XAUUSD、fixed 2R）
3. support age 60-119 は **観察タグ**（件数6・PF高いが単独採用は保留）
4. Pine一致後に 0.1〜0.25R フォワード30件
5. TrendBreakV1 ロングと同時期の **方向相反** ルール（同通貨ロング保有中はショート見送り）

**注意:** TV strategy の PF2.44 等は **Python不一致時の数字**。採用判断に使わない。

**昇格条件:** Pine完全一致 + フォワード30件 + 2017年型の負け集中が再発しないこと

---

### 4. DTS — D1 Trap Delayed H4 Shelf

**意味:** D1安値Trap否定の **30〜180日後** に H4 V+棚ブレイク。説明力は最強、件数は最少。

| 項目 | 内容 |
|---|---|
| Pine | [`pine/research/d1_trap_h4_shelf_strict_strategy.pine`](../../pine/research/d1_trap_h4_shelf_strict_strategy.pine) |
| 研究メモ | [`d1_trap_h4_shelf_strict_2026-05-30.md`](d1_trap_h4_shelf_strict_2026-05-30.md) |
| 選定トレード | [`chosen_trades.csv`](../../backtests/elliott_fibo/results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_trades.csv) |

**検証タスク:**

1. Pine vs Python **9件一致**
2. VIS とロジックが近い → VIS昇格後に **統合 or 排他** を決める（Trap文脈フィルタとして VIS に足す案あり）
3. 0.25Rフォワード **20件**（年1〜2件想定なので30は時間がかかる）
4. SILVER追加は見送り（検証済み）

**昇格条件:** 20件フォワード + VIS/SQZとの重複整理完了

---

## やらないこと（検証続行中も触らない）

| 項目 | 理由 |
|---|---|
| Sai H1 4手法混在 | PF1.05 で不採用確定 |
| Synapse / Elliott W5 / VFIB単独 | BACKTEST_INDEX ❌ |
| Wavebox USDJPY | 別トラック。準本命4と並行しない |
| psychology_text Pine | 教材用。売買候補外 |
| 受講生つまずき v0.5 | 赤青帯=教材。F1フィルタ移植は別作業 |

---

## 週次の進め方（おすすめ）

| 週 | 集中 |
|---|---|
| 第1週 | VIS + SQZ の Pine照合（ロング系2つ） |
| 第2週 | LSS Pine parity 修正 |
| 第3週 | 3手法を 0.25R アラート監視開始 |
| 第4週 | DTS Pine照合 + 重複ルール文書化 |

**同時に進めるのは最大2候補。** 4つ並行すると再び迷子になる。

---

## 昇格ゲート（第3本柱になる条件）

| # | ゲート | 合格基準 |
|---|---|---|
| G1 | 再現性 | Python ↔ Pine entry_time 100%一致 |
| G2 | フォワード | 0.25Rで30件（DTSは20件）、PF≥1.5 |
| G3 | リスク | MaxDD≤5R（検証枠内） |
| G4 | 共存 | TrendBreak/T5/SQZ/VIS/LSS の重複ルール文書化 |
| G5 | 判断 | BACKTEST_INDEX の ✅ 行を1行追加 |

---

## 関連ファイル

| 種類 | パス |
|---|---|
| フォワード台帳 | [`docs/trade_practice_records/near_main_forward_validation_log.csv`](../trade_practice_records/near_main_forward_validation_log.csv) |
| 採用判定一覧 | [`docs/spreadsheet/01_overall_judgment.csv`](../spreadsheet/01_overall_judgment.csv) |
| 全検証カタログ | [`docs/BACKTEST_INDEX.md`](../BACKTEST_INDEX.md) |

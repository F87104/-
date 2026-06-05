# FX-AI — 自動売買・群衆心理研究リポジトリ

> **3本の実装ライン:** 系統A（ブレイク追い+V字）／ **踏み上げ・投げ切り** ／ 系統B（棚ブレイク系）  
> 10年バックテスト (2015-2024) + OOS (2025-2026) で検証済み。

**最終更新**: 2026-06-01

---

## ⭐ 最重要研究（迷ったらここ）

収益検証が完了した **本番・準本番** だけを載せています。心理マップ・つまずき研究は [アーカイブ](docs/research/ARCHIVE_psychology_sprint_2026-05_06.md)（教材用）。

```text
系統A  V1(H1) + T5(H4) + 踏み上げ投げ切り(H4)  … 本番（H4は3本セット）
系統B  棚抜け + トラップ待ち棚                 … TV照合済み〜照合中（JPY4）
```

---

### 系統A — 本番エンジン（V1 + H4 T5 + 踏み上げ投げ切り）

| ネーム | TF | 一言 | Pine | 状態 |
|--------|-----|------|------|------|
| **ブレイク追い** | H1 | 高安ブレイク | [TrendBreakV1_Final.pine](pine/production/TrendBreakV1_Final.pine) | **本番** |
| **V字反転買い** | H4 | 急落V→停滞ブレイク | [h4_t5_macd_bb_live_ready.pine](pine/production/h4_t5_macd_bb_live_ready.pine) | **本番** |
| **踏み上げ投げ切り** | H4 | 投げ切り①+踏み上げ②の観測 | [market_psychology_cap_sqz_visual.pine](pine/visual/market_psychology_cap_sqz_visual.pine) | **本番表示** |
| **踏み上げ** | H4 | 棚上抜け買い（翌足始値） | [h4_sqz_tv_validation.pine](pine/production/h4_sqz_tv_validation.pine) | **本番**（XAU・円・瑞・銀） |

**6通貨（AUDJPY除外）:** XAUUSD・USDJPY・EURJPY・GBPJPY・CHFJPY・SILVER  
**H4は3本セット:** T5 + 踏み上げ投げ切り（インジ）+ 踏み上げ TV検証 → [系統A 運用](docs/operations/system_a/README.md)

**運用ルール（確定）:** TB/T5 重複時は **T5優先**。T5 と踏み上げが重なれば **T5優先** → [A-path 決定](docs/research/original_a_path_DECISION_2026-06-01.md)  
**数値:** TB+T5 = **+219.9R** / 411件 / PF1.86 → [究極手法 v1.0](docs/research/ultimate_method_v1_2026-06-01.md)

---

### 踏み上げ・投げ切り — 詳細（系統A H4 に含む）

上の **系統A** 表の 3・4行目がこれです。H4 チャートには T5 と一緒に載せます。

**踏み上げ strategy の対象通貨（H4・OANDA）**

| タグ | 通貨 | リスク | 備考 |
|------|------|--------|------|
| **踏金** | **XAUUSD** | 1.0R | フルサイズ候補 |
| **踏銀** | **XAGUSD** | 1.0R | フルサイズ候補 |
| **踏円** | **USDJPY** | 0.25R | OOS注意・フォワード監視 |
| **踏瑞** | CHFJPY | 観測 | 10年1件（統計未成立） |
| ~~踏欧~~ | EURJPY | **OFF** | Research マイナス → 本番除外 |
| — | GBPJPY・AUDJPY | **禁止** | SQZ常時除外 |

**条件（メイン）:** 棚≤**2.5**ATR / 急落≥**3.0**ATR（インジ②・strategy と同一）  
**コア数値（Python STRICT 2.0/3.5・参考）:** コア4通貨 PF **3.62** / +26.9R / maxDD 2.1R  
**投げ切り単独:** PF≈1.04 → **エントリーしない**（踏み上げの文脈把握用）

| 読む順 | ドキュメント |
|--------|--------------|
| 1 | [用語・ローソク足の読み方](docs/research/market_psychology_capitulation_squeeze_candlestick_2026-06-01.md) |
| 2 | [徹底検証 DECISION（GO判定）](docs/research/cap_sqz_thorough_validation_2026-06-01/DECISION.md) |
| 3 | [本番導入判定](docs/research/cap_sqz_production_validation_2026-06-01/DECISION.md) |
| 4 | TV CSV: [XAU](docs/research/system_b_pine_parity_2026-06-01/tv_xauusd_h4.csv) / [XAG](docs/research/system_b_pine_parity_2026-06-01/tv_xagusd_h4.csv)（照合待ち） |

**TB/T5との関係:** SQZ と TB/T5 の同時保有重複 ≈ **0%**。空きスロットで SQZ を足す候補（合算 PF1.79 想定）→ [徹底検証](docs/research/cap_sqz_thorough_validation_2026-06-01/DECISION.md)

---

### 系統B — 棚ブレイク系（TV照合・フォワード）

| タグ | ネーム | 一言 | 監視通貨 | Pine | 実装 | リスク |
|------|--------|------|----------|------|------|--------|
| **棚抜** | 棚抜け買い | 急落V→棚→抜け買い | **USDJPY・EURJPY・GBPJPY・AUDJPY** | [h4_v_initial_shelf_breakout_strategy.pine](pine/research/h4_v_initial_shelf_breakout_strategy.pine) | ✅ TV37件OK | 0.25R |
| **ﾄﾗ棚** | トラップ待ち棚抜け | 日足トラップ後に棚抜け | 同上4通貨 | [d1_trap_h4_shelf_strict_strategy.pine](pine/research/d1_trap_h4_shelf_strict_strategy.pine) | ⏳ 12件照合中 | 0.25R |

**入口:** [系統B 運用](docs/operations/system_b/README.md) ／ [10レーン判定](docs/research/system_b_lanes_validation_2026-06-01/DECISION.md)  
**B06 TV照合:** [37件確定](docs/research/system_b_pine_parity_2026-06-01/DECISION_b06_tv_oanda_parity.md) ／ **B07:** [12件チェックリスト](docs/research/system_b_pine_parity_2026-06-01/B07_TV_PARITY_CHECKLIST_ja.md)

**重複ルール（全系統）:** 同日・同銘柄は `踏金→踏円→踏銀→棚抜→ﾄﾗ棚` で **1件のみ**（棚抜とﾄﾗ棚が重なれば **棚抜優先**）

---

### 監視チャート最小セット（OANDA・6通貨）

| 通貨 | H1（1本） | H4（3本セット） |
|------|-----------|-----------------|
| **XAUUSD** | [TrendBreakV1](pine/production/TrendBreakV1_Final.pine) | T5 → [踏み上げ投げ切り](pine/visual/market_psychology_cap_sqz_visual.pine) → [踏み上げ TV検証](pine/production/h4_sqz_tv_validation.pine) |
| **USDJPY** | 同上 | 同上（踏円・0.25R） |
| **EURJPY** | 同上 | T5 + インジのみ（踏み上げ strategy **OFF**） |
| **GBPJPY** | 同上 | T5 + インジのみ（SQZ禁止） |
| **CHFJPY** | 同上 | T5 + インジ（踏瑞・strategy OFF） |
| **XAGUSD** | 同上 | T5 + インジ + 踏み上げ（踏銀） |

**系統B（JPY4）を足す場合:** USDJPY/EURJPY/GBPJPY/AUDJPY H4 に [棚抜](pine/research/h4_v_initial_shelf_breakout_strategy.pine)・[ﾄﾗ棚](pine/research/d1_trap_h4_shelf_strict_strategy.pine) を追加 → [系統B 運用](docs/operations/system_b/README.md)

---

### 研究の入口（台帳）

| 用途 | ファイル |
|------|----------|
| **全研究の索引** | [RESEARCH_INDEX.md](docs/research/RESEARCH_INDEX.md) |
| **本線（収益のみ）** | [ORIGINAL_RESEARCH_2026-06.md](docs/research/ORIGINAL_RESEARCH_2026-06.md) |
| **バックテスト一覧** | [BACKTEST_INDEX.md](docs/BACKTEST_INDEX.md) |
| **戦略の読み物** | [STRATEGY_GUIDE.md](STRATEGY_GUIDE.md) |

---

## 🔍 参考 — 受講生つまずきクラスタ研究（教材・アーカイブ）

**迷ったらここから。** 複数の受講生が **同じ日時・同じ価格帯** で入って失敗した場所を、TradingView 上に重ねた研究です。

### 3ステップで辿る

| 順番 | やること | ファイル |
|:---:|---|---|
| **1** | **結論を読む**（何がつまずきか） | 👉 **[student_stumble_clusters_research_2026-05-31.md](docs/research/student_stumble_clusters_research_2026-05-31.md)** |
| **2** | **生データを見る**（380件・66クラスタ） | [student_entries_extracted.csv](docs/research/student_entries_extracted.csv) ／ [student_stumble_clusters_v0_3.csv](docs/research/student_stumble_clusters_v0_3.csv) |
| **3** | **TradingView で重ねる**（1H チャートに貼る） | 下の Pine **v0.5** 表を参照 |

### TradingView 用 Pine（`pine/research/` フォルダ）— **最新 v0.5**

| 通貨 | チャート | Pine ファイル | 中身 |
|---|---|---|---|
| **GBPJPY** | 1H | [student_stumble_zones_gbpjpy_v0_5.pine](pine/research/student_stumble_zones_gbpjpy_v0_5.pine) | 145件 + 赤8 + **青8（待つ場所）** |
| **USDJPY** | 1H | [student_stumble_zones_usdjpy_v0_5.pine](pine/research/student_stumble_zones_usdjpy_v0_5.pine) | 29件 + 赤4 + **青4** |
| **XAUUSD** | 1H | [student_stumble_zones_xauusd_v0_5.pine](pine/research/student_stumble_zones_xauusd_v0_5.pine) | 122件 + 赤4 + **青4** |
| **EURJPY** | 1H | [student_stumble_zones_eurjpy_v0_5.pine](pine/research/student_stumble_zones_eurjpy_v0_5.pine) | 38件（全敗ゾーンなし・参考表示） |

**使い方:** GitHub で `.pine` を開く → 中身をコピー → TradingView Pine Editor に貼る → **同じ通貨の 1H** チャートで Add to chart。

**重要:** `GBPJPY` 用スクリプトを `USDJPY` チャートに貼ると、ラベルが210円台など**別通貨の価格**に表示されローソク足から大きく離れます。ファイル名の通貨とチャートを必ず一致させてください（v0.5.1 で不一致時は警告表示）。

| 表示 | 意味 |
|---|---|
| 緑/赤三角 | 受講生の実エントリー（勝/負） |
| **赤い帯** | 複数人が全員負けたゾーン（つまずき） |
| **青い帯** | 本来待つべき場所（v0.5） |

待つ場所データ: [student_stumble_wait_zones_v0_2.csv](docs/research/student_stumble_wait_zones_v0_2.csv)（v0.1 手動9件 + 勝ち参照/幾何推定9件）

**v2.x 試験フィルタ:** [stumble_chase_suppression_experiment_v0_1.pine](pine/research/stumble_chase_suppression_experiment_v0_1.pine) — フィルタOFF/ON で A/B 比較

### 心理テキスト専用 Pine（v0.5非重複）— **v0.1**

v0.5（380件・実行価格）と**重ならない**意識価格帯のみ。紫帯＝本文から抽出した「見ていた節目」（約定ではない・日時なし）。

| 通貨 | Pine | ソース行 | ゾーン |
|---|---|---:|---:|
| **GBPJPY** | [psychology_text_zones_gbpjpy_v0_1.pine](pine/research/psychology_text_zones_gbpjpy_v0_1.pine) | 45 | 14 |
| **USDJPY** | [psychology_text_zones_usdjpy_v0_1.pine](pine/research/psychology_text_zones_usdjpy_v0_1.pine) | 15 | 14 |
| **XAUUSD** | [psychology_text_zones_xauusd_v0_1.pine](pine/research/psychology_text_zones_xauusd_v0_1.pine) | 3 | 2 |

監査: [psychology_text_zones_pine_v0_1_audit_2026-05-31.md](docs/research/psychology_text_zones_pine_v0_1_audit_2026-05-31.md)

### 最重要つまずき（全員が負けた18クラスタの代表）

| 通貨 | 人数 | 売買 | 価格帯 | 構造 |
|---|---:|---|---|---|
| XAUUSD | **6人** | 買い | **2934–2954** | 史上高値追い（1期） |
| GBPJPY | **5人** | 買い | 195円台 | 節目高値追い |
| GBPJPY | **4人** | 売り | 188円台 | 安値売り（落ちるナイフ） |
| USDJPY | **4人** | 売り | 140円台 | 割れ狙い→反発 |
| GBPJPY | 3人 | 買い | **205–206** | 高値追い（2期のみ） |
| XAUUSD | 3人 | 買い | **2775–2780** | 天井買い |

### フォルダの場所（GitHub 上）

```
docs/research/          ← 研究ノート・CSV（ここ）
  student_stumble_clusters_research_2026-05-31.md   … まとめ（最初に読む）
  student_entries_extracted.csv                     … 380件の実エントリー（1期235+2期145）
  student_stumble_clusters_v0_3.csv                 … 66クラスタ集計（全敗18）
  student_stumble_wait_zones_v0_2.csv               … 待つ場所18件
  RESEARCH_INDEX.md                                 … 全研究の台帳

pine/research/          ← TradingView 用 Pine（ここ）
  student_stumble_zones_gbpjpy_v0_5.pine   ⭐ 最新（赤+青）
  student_stumble_zones_usdjpy_v0_5.pine
  student_stumble_zones_xauusd_v0_5.pine
  student_stumble_zones_eurjpy_v0_5.pine
```

---

## 研究ダッシュボード

| 優先 | 研究テーマ | 状態 | 入口 |
|---:|---|---|---|
| 1 | **系統A 本番（V1+T5+踏み上げ）** | **運用確定** | [系統A 運用](docs/operations/system_a/README.md) |
| 2 | **踏み上げ SQZ 研究** | 徹底検証・準本番判定 | [cap_sqz DECISION](docs/research/cap_sqz_thorough_validation_2026-06-01/DECISION.md) |
| 3 | **系統B — 棚抜（B06）** | **TV照合37件OK** | [DECISION_b06](docs/research/system_b_pine_parity_2026-06-01/DECISION_b06_tv_oanda_parity.md) |
| 4 | **系統B — ﾄﾗ棚（B07）** | Pine最終確認中 | [B07 チェックリスト](docs/research/system_b_pine_parity_2026-06-01/B07_TV_PARITY_CHECKLIST_ja.md) |
| 5 | **H4 T5 深掘り** | 記録済み | [t5_method_deep_research](docs/research/t5_method_deep_research_2026-06-01.md) |
| 6 | 受講生つまずき（教材） | アーカイブ | 下の [つまずき研究](#-参考--受講生つまずきクラスタ研究教材アーカイブ) |
| 7 | **トレード実践記録** | 記録中 | [trade_practice_records/](docs/trade_practice_records/) |

---

## 📚 ドキュメント目次

| ドキュメント | 内容 |
|---|---|
| 👉 **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** | **メインの説明書 (これを読めばOK)** |
| 👉 **[docs/BACKTEST_INDEX.md](docs/BACKTEST_INDEX.md)** | **全検証カタログ (試したもの全部の一覧)** |
| 📊 [docs/spreadsheet/](docs/spreadsheet/) | **Google スプレッドシート用 CSV/TSV** (9シート) |
| [docs/two_method_practical_research_2026-05-24.md](docs/two_method_practical_research_2026-05-24.md) | 2本柱研究ノート (公式版) |
| [docs/h4_t5_macd_bb_practical_audit_2026-05-24.md](docs/h4_t5_macd_bb_practical_audit_2026-05-24.md) | H4 T5 補助手法の実用監査 |
| [docs/h4_t5_macd_bb_live_ready_notes.md](docs/h4_t5_macd_bb_live_ready_notes.md) | H4 T5 本番運用ノート |
| [docs/research/short_side_research_2026-05-28_in_progress.md](docs/research/short_side_research_2026-05-28_in_progress.md) | ショート側研究ノート (**検証途中・本番未採用**) |
| [docs/FX検証研究ノート_2015-2024.docx](docs/FX検証研究ノート_2015-2024.docx) | Word版総合レポート |
| [backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md](backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md) | TrendBreak+T5 アンサンブル検証 |

---

## 🎯 結論 (TL;DR)

### 究極手法 v1.0 — 研究統合版

> **2本柱エンジン × 三重ゲート（相場状態 / 心理 / リスク）**  
> 詳細: **[ultimate_method_v1_2026-06-01.md](docs/research/ultimate_method_v1_2026-06-01.md)**

```text
EXECUTE = エンジンシグナル × ゲート通過 × リスク枠内
```

### 採用戦略 — 系統A（V1 + H4 T5 + 踏み上げ）

| TF | 役割 | Pine ファイル | 中身 |
|-----|------|---------------|------|
| H1 | **主力** TrendBreakV1 | [`TrendBreakV1_Final.pine`](pine/production/TrendBreakV1_Final.pine) | 高安ブレイク |
| H4 | **補助** T5 | [`h4_t5_macd_bb_live_ready.pine`](pine/production/h4_t5_macd_bb_live_ready.pine) | 急落V→停滞ブレイク |
| H4 | **観測** 踏み上げ投げ切り | [`market_psychology_cap_sqz_visual.pine`](pine/visual/market_psychology_cap_sqz_visual.pine) | 投げ切り①+踏み上げ②（▲のみ） |
| H4 | **追加** 踏み上げ | [`h4_sqz_tv_validation.pine`](pine/production/h4_sqz_tv_validation.pine) | 棚上抜け買い（XAU・円・銀） |

### 進行中の研究

| 研究 | 状態 | メモ |
|---|---|---|
| [ショート側研究 2026-05-28](docs/research/short_side_research_2026-05-28_in_progress.md) | 🔬 検証途中 | ロング版ミラーは不採用。H4 1ヶ月安値更新後の安値停滞ブレイクショートが暫定候補 |

### 推奨運用構成

**6通貨ペア** で両戦略を同時運用 (AUDJPY は除外):

| 通貨 | TF | コメント |
|---|---|---|
| XAUUSD (金) | H1+H4 | エースアセット |
| USDJPY | H1+H4 | 安定 |
| EURJPY | H1+H4 | 中庸 |
| GBPJPY | H1+H4 | 高ボラ |
| CHFJPY | H1+H4 | 中庸 |
| SILVER | H1+H4 | TrendBreakV1 主役 |

### 10年バックテスト成績 (6通貨, 2015-2024, コスト込み)

| 構成 | Trades | WR | PF | Total R | MaxDD | 連敗 |
|---|---|---|---|---|---|---|
| TrendBreakV1 単独 | 381 | 39.4% | 1.79 | +194.6R | 11.9R | 11 |
| H4 T5 MACD BB 単独 | 30 | 60.0% | 3.43 | +25.3R | 4.4R | 5 |
| **両方フル運用** | **411** | **40.9%** | **1.86** | **+219.9R** | **11.9R** | **11** |

### 資産推定 (100万円スタート, 1R = 1%)

| 構成 | 単利 | 複利 |
|---|---|---|
| **両方フル運用** | **3,199,417円** | **8,323,043円** |

---

## 🚀 すぐ使う場合（系統A 本番）

1. **TradingView** を開く（OANDA 推奨）
2. **H1 × 6通貨** に [TrendBreakV1_Final.pine](pine/production/TrendBreakV1_Final.pine)（preset **Auto**）
3. **H4 × 6通貨** に **この順で3本** Add to chart:
   1. [h4_t5_macd_bb_live_ready.pine](pine/production/h4_t5_macd_bb_live_ready.pine) — Strict + Balanced REC1.2
   2. [market_psychology_cap_sqz_visual.pine](pine/visual/market_psychology_cap_sqz_visual.pine) — 観測専用（▲印）
   3. [h4_sqz_tv_validation.pine](pine/production/h4_sqz_tv_validation.pine) — 踏み上げ（XAU・USDJPY・銀のみ／▲描画OFF）
4. 通貨: **XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, SILVER**（**AUDJPY除外**）
5. アラート → 手動または API で発注。**T5 と踏み上げが重なれば T5 優先**

詳細: **[系統A 運用](docs/operations/system_a/README.md)** ／ **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)**

---

## 📂 リポジトリ構成

```
fx-ai/
├── README.md                       ← このファイル (入り口)
├── STRATEGY_GUIDE.md               ← 戦略の説明書 (本体)
├── pine/                           ← TradingView Pine Script
│   ├── production/                    本番運用中 ⭐
│   │   ├── TrendBreakV1_Final.pine        系統A H1
│   │   ├── h4_t5_macd_bb_live_ready.pine  系統A H4 T5
│   │   └── h4_sqz_tv_validation.pine      系統A H4 踏み上げ
│   ├── visual/                        可視化ツール (Indicator)
│   │   ├── market_psychology_cap_sqz_visual.pine  系統A 踏み上げ投げ切り ⭐
│   │   ├── h4_t5_macd_bb_visual.pine
│   │   └── ...
│   ├── research/                      研究中 (各通貨個別戦略)
│   │   ├── student_stumble_zones_gbpjpy_v0_3.pine   ⭐ つまずき可視化
│   │   ├── student_stumble_zones_usdjpy_v0_3.pine   ⭐ つまずき可視化
│   │   ├── student_stumble_zones_xauusd_v0_3.pine   ⭐ つまずき可視化
│   │   ├── wavebox_usdjpy_h1_rebreak_v1_2.pine
│   │   └── ... (その他研究用 Pine)
│   └── archive/                       旧版・採用しなかった戦略
│       ├── sai_best_method_strategy.pine
│       ├── trendbreak_v1_final_fixed.pine
│       ├── wavebox_usdjpy_h1_rebreak_v0_3.pine
│       ├── wavebox_usdjpy_h1_rebreak_v1.pine
│       ├── wavebox_usdjpy_h1_rebreak_v1_1.pine
│       └── synapse_mtf_wave_reversal_v3.pine
├── docs/                           ← 研究ノート ⭐
│   ├── operations/system_a/             系統A 本番（chart_bundle.yaml）
│   ├── BACKTEST_INDEX.md              全検証カタログ
│   ├── two_method_practical_research_2026-05-24.md  最新の総括
│   ├── h4_t5_macd_bb_practical_audit_2026-05-24.md  実用監査
│   ├── h4_t5_macd_bb_live_ready_notes.md            運用ノート
│   ├── research/                      研究中 (各戦略のメモ)
│   │   ├── student_stumble_clusters_research_2026-05-31.md  ⭐ つまずき研究まとめ
│   │   ├── student_entries_extracted.csv                  ⭐ 137件エントリー
│   │   ├── student_stumble_clusters_v0_2.csv              ⭐ 29クラスタ
│   │   ├── RESEARCH_INDEX.md                              全研究台帳
│   │   └── ... (wavebox, chfjpy 等)
│   ├── reference/                     参考資料 (Word/Doc 等)
│   │   ├── FX検証研究ノート_2015-2024.docx
│   │   └── FX検証研究ノート_2015-2024_GoogleDocs.docx
│   └── spreadsheet/                   Google スプレッドシート用 CSV
├── backtests/                      ← Python バックテスト
│   ├── ensemble/                      アンサンブル運用検証 ⭐
│   │   ├── trendbreak_t5_practical_combo_2015_2024/   採用案の検証
│   │   ├── trendbreak_h4_v_combo_2015_2024/           V字単独の検証
│   │   ├── run_trendbreak_t5_practical_combo.py
│   │   └── ...
│   ├── trendbreak_v1/                 TrendBreakV1 単独検証
│   │   ├── results_2026_05_24/           最新OOS含む結果
│   │   ├── fakeout_*/                    フェイクアウト研究
│   │   ├── pyramiding_sweep_*/           ピラミディング検証
│   │   └── ...
│   ├── elliott_fibo/                  T5/MACD/BB 系の研究
│   │   ├── results_2015_2024/            ベースライン
│   │   ├── results_2025_2026_oos/        OOS検証
│   │   └── run_*.py                      多数の検証スクリプト
│   ├── sai_h1/                        旧 Sai 戦略 (archive)
│   ├── audit/                         コスト・OOS監査
│   ├── relaxation/                    パラメータ緩和スタディ
│   └── comparison/                    戦略間比較
├── backtest/                       ← 既存のバックテストツール (archive)
├── F87104_test/                    ← OHLCデータ (gitignore済)
└── scripts/                        ← ユーティリティ
    └── build_research_note_docx.py    DOCX生成スクリプト
```

---

## 📈 戦略開発の経緯

```
[初期]  Sai H1 戦略 (PF 1.05) → 改善必要と判断
   ↓
[2025年下期] TrendBreakV1 発見 → PF 1.79 / +194R
   ↓
[初期検証] Sai Best Method 抽出 → PF 1.47 (10年 +99R)
   ↓
[精密監査] TrendBreakV1 コスト込みでも +146R (-21%) → 頑健性確認
   ↓
[緩和スタディ] 通貨別 HYBRID 最適化 → 頻度 +27%, R +23%
   ↓
[OOS検証] 2025-2026 で +24R 維持 → 過剰最適化なし
   ↓
[V字研究] H4 急落V字回復だけでは弱い (-7R) → 単独では NG
   ↓
[T5フィルタ追加] V候補 + MACD + BB + 高値停滞/再ブレイク → PF 3.43 で復活
   ↓
[アンサンブル検証] TrendBreakV1 + H4 T5 MACD BB → +219.9R / 11.9R DD
   ↓
[現状]  両方フル運用 (推奨6通貨) を採用 ⭐
```

---

## ⚠️ 注意事項

- **過去パフォーマンスは将来を保証しない**。資金は失っても困らない範囲で。
- **スプレッド・スリッページは想定済み** (audit 参照)
- **AUDJPY は除外**すること (PF 0.97、足を引っ張る)
- **H4 T5 MACD BB は 30トレード/10年** = 年3回程度の低頻度
  - 焦らず厳選シグナルを待つ
  - 0.25R〜0.5R から始めて 30件後に通常リスクへ
- **2018年は全体的に苦戦する年**だった (低ボラ環境)
- **DD 20%超え時は運用停止**を Pine Script に組み込み済み

---

## 📜 ライセンス

このリポジトリのコードは個人運用目的での使用を想定。商用利用・再配布は控えてください。

# FX-AI — 2 本柱 + 市場心理研究 自動売買戦略リポジトリ

> H1/H4 ベースの自動売買戦略コレクション。
> **本番運用**: 10 年バックテスト + OOS 検証済みの **2 本柱戦略** (TrendBreakV1 + H4 T5 + MACD + BB)
> **進行中**: **市場心理 v2.1 マトリクス** (最優先研究、TV 実測 +50.71% / 128 trades)

**最終更新**: 2026-05-30

---

# 🧠 進行中の研究 (最優先タスク)

> このセクションには **今後の精度向上で重点的に検証する研究** を集約します。
> 最優先は **#1 市場心理 v2.1 マトリクス**。フォワード 30 件達成で本番昇格判定。

## 🥇 #1 市場心理 v2.1 マトリクス (Currency × Structure Auto-routing)

**現状ステータス**: 🟠 **本番候補** (TV Strategy Tester で 7 通貨 × 8〜13 年 = 128 件、Net +50.71%、最大 DD 6.16% 確認済み)
**昇格条件**: フォワード 30 件記録 + 月次レビューで再現確認

TradingView Strategy Tester での実測 (STEP 1+2+3) を統合した、**通貨ごとに最適な心理構造を自動 ON/OFF** する本命 Pine。
チャートに **1 本載せるだけで運用可能**。

### 採用マトリクス (TV 実測 8〜13 年データ)

| Symbol | Sqz | Cap | LL | 採用 | Net% | trades | PF | DD |
|---|:-:|:-:|:-:|---|---:|---:|---:|---:|
| XAUUSD | ✅ | ❌ | ❌ | Sqz only | +0.98% | 2 | 1.97 | 1.40% |
| XAGUSD (SILVER) | ✅ | ❌ | ❌ | Sqz only | +7.16% | 5 | 8.16 | 1.49% |
| EURJPY | ✅ | ✅ | ❌ | Sqz + Cap | +4.12% | 5 | 5.07 | 1.89% |
| AUDJPY | ✅ | ✅ | ❌ | Sqz + Cap | +6.07% | 4 | 275.9 | 0.68% |
| **USDJPY** | ❌ | ✅ | ✅ | **Cap + LL** | **+20.28%** 🏆 | 60 | 1.63 | 4.06% |
| CHFJPY | ✅ | ✅ | ✅ | 全 3 構造 | +12.10% | 52 | 1.44 | 6.16% |
| GBPJPY | ❌ | ❌ | ❌ | 全除外 | — | 0 | — | — |
| **6 通貨合算 (LL 含)** | | | | | **+50.71%** | **128** | — | **6.16%** (max) |

→ **USDJPY が 40%、CHFJPY が 24%** を稼ぐ。この 2 通貨が本命。

### 🏆 メインの Pine (これだけでまず動かす)

| ファイル | TradingView 表示名 |
|---|---|
| **[`pine/research/market_psychology_v2_matrix_strategy.pine`](pine/research/market_psychology_v2_matrix_strategy.pine)** | `本命v2.1 Market Psychology Matrix (Sqz + Cap + LL)` |

→ TradingView の Pine エディタに貼り付け → 7 通貨のチャートで Strategy Tester / アラート設定。

### 📂 研究資料 (すべてここに集約)

#### 設計 / 仕様書

| ファイル | 内容 |
|---|---|
| [`docs/research/market_psychology/v2_spec.md`](docs/research/market_psychology/v2_spec.md) | v2 / v2.1 統合仕様書、本番昇格チェックリスト |
| [`docs/research/market_psychology/README.md`](docs/research/market_psychology/README.md) | 研究ハブ (10 心理パターン辞書 / R1〜R7 ステータス) |
| [`docs/research/market_psychology/framework.md`](docs/research/market_psychology/framework.md) | 共通枠組み (4 段階フロー / 数値化軸 / Pine 化ルール) |
| [`docs/research/market_psychology/status.md`](docs/research/market_psychology/status.md) | 判定スナップショット / アンチパターン |

#### 検証ログ (TradingView 実測の生データ)

| ファイル | 内容 |
|---|---|
| [`docs/research/market_psychology/forward_log_2026_05_step1.md`](docs/research/market_psychology/forward_log_2026_05_step1.md) | STEP 1: Squeeze 単独 6 通貨 |
| [`docs/research/market_psychology/forward_log_2026_05_step2.md`](docs/research/market_psychology/forward_log_2026_05_step2.md) | STEP 2: Capitulation 単独 + STEP 1+2 統合 |
| [`docs/research/market_psychology/forward_log_2026_05_step3.md`](docs/research/market_psychology/forward_log_2026_05_step3.md) | STEP 3: Long Liquidation 単独 + STEP 1+2+3 完全マトリクス |
| 🏆 [`docs/research/market_psychology/forward_log_2026_05_v2_1_matrix.md`](docs/research/market_psychology/forward_log_2026_05_v2_1_matrix.md) | **v2.1 Matrix 統合検証**: 128t / +50.71% の決定打 |
| [`docs/research/market_psychology/forward_log_template.md`](docs/research/market_psychology/forward_log_template.md) | 月次フォワード記録テンプレート |

#### Python 検証 (Deep Research、10 項目掘り下げ)

| ファイル | 内容 |
|---|---|
| [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md) | 10 項目 deep research レポート |
| [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/`](backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/) | 結果 CSV 17 ファイル (heatmap / sweep / 通貨別 等) |
| [`backtests/elliott_fibo/run_market_psychology_v2_deep_research.py`](backtests/elliott_fibo/run_market_psychology_v2_deep_research.py) | Python 検証コード |

#### 元になった研究ノート (個別パターン)

| ファイル | 心理パターン |
|---|---|
| [`docs/research/market_psychology_pattern_library_2026-05-30.md`](docs/research/market_psychology_pattern_library_2026-05-30.md) | 10 心理パターン辞書 |
| [`docs/research/market_psychology_squeeze_strict_2026-05-30.md`](docs/research/market_psychology_squeeze_strict_2026-05-30.md) | Squeeze 構造 |
| [`docs/research/market_psychology_squeeze_currency_compatibility_2026-05-30.md`](docs/research/market_psychology_squeeze_currency_compatibility_2026-05-30.md) | Squeeze 通貨相性 |
| [`docs/research/trap_false_break_reaction_2026-05-30.md`](docs/research/trap_false_break_reaction_2026-05-30.md) | Trap / False Break |
| [`docs/research/d1_trap_h4_shelf_strict_2026-05-30.md`](docs/research/d1_trap_h4_shelf_strict_2026-05-30.md) | D1 Trap + H4 Shelf |
| [`docs/research/d1_bear_trap_h4_v_reclaim_2026-05-29.md`](docs/research/d1_bear_trap_h4_v_reclaim_2026-05-29.md) | D1 Bear Trap + H4 V |
| [`docs/research/indicator_denial_reaction_2026-05-29.md`](docs/research/indicator_denial_reaction_2026-05-29.md) | Indicator Denial |

#### 派生 / 比較用 Pine (v2 系)

| ファイル | 用途 |
|---|---|
| [`pine/research/market_psychology_strict_v2_strategy.pine`](pine/research/market_psychology_strict_v2_strategy.pine) | v2 Sqz + Cap (手動制御版) |
| [`pine/research/market_psychology_long_liquidation_strategy.pine`](pine/research/market_psychology_long_liquidation_strategy.pine) | LL 単独検証用 |
| [`pine/research/market_psychology_dormant_breakout_strategy.pine`](pine/research/market_psychology_dormant_breakout_strategy.pine) | Dormant Breakout 単独 |
| [`pine/visual/market_psychology_long_liquidation_visual.pine`](pine/visual/market_psychology_long_liquidation_visual.pine) | LL 観測 (indicator) |
| [`pine/visual/market_psychology_dormant_breakout_visual.pine`](pine/visual/market_psychology_dormant_breakout_visual.pine) | Dormant 観測 (indicator) |

### v1 → v2 → v2.1 の進化

| バージョン | 主な変更 | PF | DD |
|---|---|---:|---:|
| v1 SQZ_STRICT ex GBPJPY | (ベースライン) | 2.21 | 3.09R |
| v2 統合 (Sqz + Cap) | 棚 ≤ 2.2 / 急落 ≥ 4.0 / sig_range ≥ 3.0 / 早期撤退 | 2.88 | 2.06R |
| **v2.1 Matrix (Sqz + Cap + LL)** | **通貨×構造自動 ON/OFF + 短側 LL 追加** | **マトリクス全体で Net +50.71%** | **6.16%** |

### 残課題 (本番採用前)

- [ ] フォワード 30+ 件記録 (USDJPY / CHFJPY を最優先で)
- [ ] Pine ↔ Python parity audit
- [ ] Volume フィルタ実 volume で効果検証 (#1)
- [ ] STEP 4: Dormant Breakout 検証
- [ ] **エントリー精度向上策** (棚の質スコア / D1 文脈強化 / 同時シグナル相関フィルタ / ボラ regime ← 次の作業候補)

### 次のアクション候補

| 案 | 内容 |
|---|---|
| **A** | エントリー精度向上策の Phase 1 (棚の質スコア / D1 文脈 / 相関 / ボラ regime) を Pine に組み込み |
| B | STEP 4 (Dormant Breakout) の 6 通貨検証 |
| C | フォワード 30 件記録開始 (`forward_log_2026_06.md` 作成) |

---

## #2 ショート側研究 2026-05-28 (旧)

**現状ステータス**: 🔬 検証途中、本番未採用

| ファイル | 状態 |
|---|---|
| [`docs/research/short_side_research_2026-05-28_in_progress.md`](docs/research/short_side_research_2026-05-28_in_progress.md) | ロング版ミラーは不採用。H4 1 ヶ月安値更新後の安値停滞ブレイクショートが暫定候補 |

→ 市場心理 v2.1 の LL (Long Liquidation) で **ショート側はある程度カバーできた** ため、優先度は #1 より下。

---

## 📚 ドキュメント目次

### 🧠 最優先: 市場心理 v2.1 (進行中)

| ドキュメント | 内容 |
|---|---|
| 🏆 **[`pine/research/market_psychology_v2_matrix_strategy.pine`](pine/research/market_psychology_v2_matrix_strategy.pine)** | **v2.1 Matrix Pine 本体 (これだけで動作)** |
| 🏆 **[`docs/research/market_psychology/forward_log_2026_05_v2_1_matrix.md`](docs/research/market_psychology/forward_log_2026_05_v2_1_matrix.md)** | **v2.1 検証ログ (128t / +50.71% / DD 6.16%)** |
| 📋 [`docs/research/market_psychology/v2_spec.md`](docs/research/market_psychology/v2_spec.md) | v2 / v2.1 仕様書 + 本番昇格チェックリスト |
| 🧭 [`docs/research/market_psychology/`](docs/research/market_psychology/) | 研究ハブ全体 (README / framework / status / 検証ログ全て) |
| 🔬 [`backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md`](backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/report_ja.md) | Deep Research レポート (10 項目掘り下げ) |

### 本番 2 本柱 (採用済み)

| ドキュメント | 内容 |
|---|---|
| 👉 **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** | **メインの説明書 (これを読めば OK)** |
| 👉 **[docs/BACKTEST_INDEX.md](docs/BACKTEST_INDEX.md)** | **全検証カタログ (試したもの全部の一覧)** |
| 📊 [docs/spreadsheet/](docs/spreadsheet/) | Google スプレッドシート用 CSV / TSV (9 シート) |
| [docs/two_method_practical_research_2026-05-24.md](docs/two_method_practical_research_2026-05-24.md) | 2 本柱研究ノート (公式版) |
| [docs/h4_t5_macd_bb_practical_audit_2026-05-24.md](docs/h4_t5_macd_bb_practical_audit_2026-05-24.md) | H4 T5 補助手法の実用監査 |
| [docs/h4_t5_macd_bb_live_ready_notes.md](docs/h4_t5_macd_bb_live_ready_notes.md) | H4 T5 本番運用ノート |
| [docs/research/short_side_research_2026-05-28_in_progress.md](docs/research/short_side_research_2026-05-28_in_progress.md) | ショート側研究ノート (検証途中・本番未採用) |
| [docs/FX検証研究ノート_2015-2024.docx](docs/FX検証研究ノート_2015-2024.docx) | Word 版総合レポート |
| [backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md](backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md) | TrendBreak + T5 アンサンブル検証 |

---

# ✅ 本番運用 (採用済み 2 本柱)

> ここからは **既に検証 + 採用済み** の本番戦略 (2015-2024 10 年 BT + 2025-2026 OOS で確認済み)。
> 上記の「進行中の研究」 (市場心理 v2.1) **とは別ライン** で並走運用する想定。

### 採用戦略 — 2 本柱

| 役割 | 戦略 | Pine ファイル | 中身 |
|---|---|---|---|
| **主力** | **TrendBreakV1 HYBRID** | [`pine/production/TrendBreakV1_Final.pine`](pine/production/TrendBreakV1_Final.pine) | 高安値ブレイクアウト (H1) |
| **補助** | **H4 T5 + MACD + BB** | [`pine/production/h4_t5_macd_bb_live_ready.pine`](pine/production/h4_t5_macd_bb_live_ready.pine) | 急落 V 字回復後の停滞ブレイク (H4) |

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

## 🚀 すぐ使う場合

1. **TradingView** を開く
2. **H1チャート 6枚** に `pine/production/TrendBreakV1_Final.pine` (Auto preset)
3. **H4チャート 6枚** に `pine/production/h4_t5_macd_bb_live_ready.pine` (デフォルト = Strict + Balanced REC1.2)
4. 通貨: **XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, SILVER** の6つ
5. アラート設定 → 通知が来たら手動 (または API 経由) で発注

詳細は **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** を参照。

---

## 📂 リポジトリ構成

```
fx-ai/
├── README.md                       ← このファイル (入り口)
├── STRATEGY_GUIDE.md               ← 戦略の説明書 (本体)
├── pine/                           ← TradingView Pine Script
│   ├── production/                    本番運用中 ⭐
│   │   ├── TrendBreakV1_Final.pine        主力 (H1 ブレイクアウト)
│   │   └── h4_t5_macd_bb_live_ready.pine  補助 (H4 T5+MACD+BB)
│   ├── research/                      研究中 (各通貨個別戦略)
│   │   ├── wavebox_usdjpy_h1_rebreak_v1_2.pine
│   │   ├── wavebox_gbpjpy_h1_long_rebreak_v0_1.pine
│   │   ├── synapse_mtf_wave_reversal_v4.pine
│   │   ├── chfjpy_h1_exhaustion_short_v0_2.pine
│   │   └── silver_xagusd_h1_short_rebreak_v0_1.pine
│   ├── visual/                        可視化ツール (Indicator)
│   │   ├── h4_t5_macd_bb_visual.pine
│   │   ├── h4_sharp_drop_v_recovery_visual.pine
│   │   ├── sai_h1_visual_scanner.pine
│   │   ├── sai_mtf_visual_checker.pine
│   │   └── synapse_usdjpy_m5_v2_context_visual.pine
│   └── archive/                       旧版・採用しなかった戦略
│       ├── sai_best_method_strategy.pine
│       ├── trendbreak_v1_final_fixed.pine
│       ├── wavebox_usdjpy_h1_rebreak_v0_3.pine
│       ├── wavebox_usdjpy_h1_rebreak_v1.pine
│       ├── wavebox_usdjpy_h1_rebreak_v1_1.pine
│       └── synapse_mtf_wave_reversal_v3.pine
├── docs/                           ← 研究ノート ⭐
│   ├── BACKTEST_INDEX.md              全検証カタログ
│   ├── two_method_practical_research_2026-05-24.md  最新の総括
│   ├── h4_t5_macd_bb_practical_audit_2026-05-24.md  実用監査
│   ├── h4_t5_macd_bb_live_ready_notes.md            運用ノート
│   ├── research/                      研究中 (各戦略のメモ)
│   │   ├── wavebox_*.md (7ファイル)
│   │   ├── synapse_method_definition_v0_1.md
│   │   ├── chfjpy_*.md (4ファイル)
│   │   ├── silver_xagusd_*.md
│   │   ├── sequential_countertrend_*.md
│   │   └── original_wavebox_rebreak_*.md
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

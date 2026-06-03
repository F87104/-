# FX-AI — 2本柱 自動売買戦略リポジトリ

> H1/H4 ベースの自動売買戦略コレクション。10年バックテスト (2015-2024) + OOS (2025-2026) で検証済みの **2本柱戦略** を運用するためのコード一式。

**最終更新**: 2026-05-31

---

## 🔍 いま見るべき場所 — 受講生つまずきクラスタ研究

**迷ったらここから。** 複数の受講生が **同じ日時・同じ価格帯** で入って失敗した場所を、TradingView 上に重ねた研究です。

### 3ステップで辿る

| 順番 | やること | ファイル |
|:---:|---|---|
| **1** | **結論を読む**（何がつまずきか） | 👉 **[student_stumble_clusters_research_2026-05-31.md](docs/research/student_stumble_clusters_research_2026-05-31.md)** |
| **2** | **生データを見る**（137件・29クラスタ） | [student_entries_extracted.csv](docs/research/student_entries_extracted.csv) ／ [student_stumble_clusters_v0_2.csv](docs/research/student_stumble_clusters_v0_2.csv) |
| **3** | **TradingView で重ねる**（1H チャートに貼る） | 下の Pine **v0.4** 表を参照 |

### TradingView 用 Pine（`pine/research/` フォルダ）— **最新 v0.4**

| 通貨 | チャート | Pine ファイル | 中身 |
|---|---|---|---|
| **GBPJPY** | 1H | [student_stumble_zones_gbpjpy_v0_4.pine](pine/research/student_stumble_zones_gbpjpy_v0_4.pine) | 60件 + 赤9 + **青9（待つ場所）** |
| **USDJPY** | 1H | [student_stumble_zones_usdjpy_v0_4.pine](pine/research/student_stumble_zones_usdjpy_v0_4.pine) | 16件 + 赤3 + **青3** |
| **XAUUSD** | 1H | [student_stumble_zones_xauusd_v0_4.pine](pine/research/student_stumble_zones_xauusd_v0_4.pine) | 42件 + 赤3 + **青3** |

**使い方:** GitHub で `.pine` を開く → 中身をコピー → TradingView Pine Editor に貼る → 同じ通貨の **1H** チャートで Add to chart。

| 表示 | 意味 |
|---|---|
| 緑/赤三角 | 受講生の実エントリー（勝/負） |
| **赤い帯** | 複数人が全員負けたゾーン（つまずき） |
| **青い帯** | 本来待つべき場所（v0.4 追加） |

待つ場所データ: [student_stumble_wait_zones_v0_1.csv](docs/research/student_stumble_wait_zones_v0_1.csv)

**v2.x 試験フィルタ:** [stumble_chase_suppression_experiment_v0_1.pine](pine/research/stumble_chase_suppression_experiment_v0_1.pine) — フィルタOFF/ON で A/B 比較

### 最重要つまずき（全員が負けた15クラスタの代表）

| 通貨 | 人数 | 売買 | 価格帯 | 構造 |
|---|---:|---|---|---|
| GBPJPY | **5人** | 買い | 199円台 | 高値追い |
| GBPJPY | **4人** | 売り | 188円台 | 安値売り（落ちるナイフ） |
| USDJPY | 3人 | 売り | 140円台 | 割れ狙い→反発 |
| XAUUSD | 2人 | 買い | **2719** | 天井買い |
| XAUUSD | 2人 | 買い | **2777** | 天井買い |
| XAUUSD | 2人 | 買い | **2948** | 天井買い |

### フォルダの場所（GitHub 上）

```
docs/research/          ← 研究ノート・CSV（ここ）
  student_stumble_clusters_research_2026-05-31.md   … まとめ（最初に読む）
  student_entries_extracted.csv                     … 137件の実エントリー
  student_stumble_clusters_v0_2.csv                 … 29クラスタ集計
  student_stumble_wait_zones_v0_1.csv             … 待つ場所15件
  RESEARCH_INDEX.md                                 … 全研究の台帳

pine/research/          ← TradingView 用 Pine（ここ）
  student_stumble_zones_gbpjpy_v0_4.pine   ⭐ 最新（赤+青）
  student_stumble_zones_usdjpy_v0_4.pine
  student_stumble_zones_xauusd_v0_4.pine
```

---

## 研究ダッシュボード

このリポジトリは、戦略コードだけでなく「何を研究しているか」を忘れないための研究台帳としても使います。

### 重要研究: H4 Double V Reclaim / 初動V

- 研究メモ: [docs/research/h4_double_v_reclaim_2026-06-02.md](docs/research/h4_double_v_reclaim_2026-06-02.md)
- TradingView可視化: [pine/visual/h4_double_v_short_denial_visual.pine](pine/visual/h4_double_v_short_denial_visual.pine)
- D1 V -> H4確認可視化: [pine/visual/d1_v_context_h4_visual.pine](pine/visual/d1_v_context_h4_visual.pine)
- Strategy検証: [pine/production/h4_double_v_reclaim_strategy.pine](pine/production/h4_double_v_reclaim_strategy.pine)
- D1 V -> H4検証Strategy: [pine/production/d1_v_context_h4_strategy.pine](pine/production/d1_v_context_h4_strategy.pine)
- 狙い: 急落後のVそのものではなく、**V1売り失敗 -> V2押し -> V1右肩ゾーン突破**で、トレンド初動候補を探す研究。
- 最新仮説: H4単独ではなく、**D1 V Context + H4 Execute** に分けると、日足級の反転初動を拾える可能性がある。
- 最新更新: D1 Vの谷足と確認足に、下ヒゲ・終値位置・値幅ATR・陽線/前日終値超えの品質チェックを追加。

| 優先 | 研究テーマ | 状態 | 入口 |
|---:|---|---|---|
| 1 | **受講生つまずきクラスタ** | 進行中 | 👉 上の **[3ステップ表](#-いま見るべき場所--受講生つまずきクラスタ研究)** |
| 2 | **H4 Double V Reclaim / 初動V** | **最重要・検証中** | [研究メモ](docs/research/h4_double_v_reclaim_2026-06-02.md) ／ [D1 V->H4可視化](pine/visual/d1_v_context_h4_visual.pine) ／ [D1 V->H4検証](pine/production/d1_v_context_h4_strategy.pine) ／ [H4 Double V](pine/visual/h4_double_v_short_denial_visual.pine) |
| 3 | 受講生エントリー集中パターン | 進行中 | [student_entry_cluster_research_2026-05-31.md](docs/research/student_entry_cluster_research_2026-05-31.md) |
| 4 | トレード心理 / 群衆心理 | 進行中 | [RESEARCH_INDEX.md](docs/research/RESEARCH_INDEX.md) ／ [crowd_psychology_simple_visual.pine](pine/visual/crowd_psychology_simple_visual.pine) |
| 5 | Market Psychology Squeeze | 記録済み | [market_psychology_squeeze_strict_2026-05-30.md](docs/research/market_psychology_squeeze_strict_2026-05-30.md) |
| 6 | **市場心理図鑑** | **Vol.1 + 収集ライブラリ** | [図鑑](docs/research/市場心理図鑑/README.md) ／ [収集90件+](docs/research/市場心理図鑑/collection/index.md) |
| 7 | Wavebox / Rebreak | 記録済み | [wavebox_operational_preconditions_v1.md](docs/research/wavebox_operational_preconditions_v1.md) |

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
| [docs/research/h4_double_v_reclaim_2026-06-02.md](docs/research/h4_double_v_reclaim_2026-06-02.md) | H4 Double V Reclaim / 初動V研究 (**重要・可視化中**) |
| [docs/FX検証研究ノート_2015-2024.docx](docs/FX検証研究ノート_2015-2024.docx) | Word版総合レポート |
| [backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md](backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md) | TrendBreak+T5 アンサンブル検証 |

---

## 🎯 結論 (TL;DR)

### 採用戦略 — 2本柱

| 役割 | 戦略 | Pine ファイル | 中身 |
|---|---|---|---|
| **主力** | **TrendBreakV1 HYBRID** | [`pine/production/TrendBreakV1_Final.pine`](pine/production/TrendBreakV1_Final.pine) | 高安値ブレイクアウト (H1) |
| **補助** | **H4 T5 + MACD + BB** | [`pine/production/h4_t5_macd_bb_live_ready.pine`](pine/production/h4_t5_macd_bb_live_ready.pine) | 急落V字回復後の停滞ブレイク (H4) |

### 進行中の研究

| 研究 | 状態 | メモ |
|---|---|---|
| [H4 Double V Reclaim / 初動V](docs/research/h4_double_v_reclaim_2026-06-02.md) | 🔬 最重要・可視化中 | V1売り失敗後、V2押しからV1右肩ゾーン突破を狙う。小さいノイズVを削って「トレンド初動のV」を探す研究 |
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
│   │   ├── student_stumble_zones_gbpjpy_v0_3.pine   ⭐ つまずき可視化
│   │   ├── student_stumble_zones_usdjpy_v0_3.pine   ⭐ つまずき可視化
│   │   ├── student_stumble_zones_xauusd_v0_3.pine   ⭐ つまずき可視化
│   │   ├── wavebox_usdjpy_h1_rebreak_v1_2.pine
│   │   └── ... (その他研究用 Pine)
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

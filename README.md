# FX-AI — 2本柱 自動売買戦略リポジトリ

> H1/H4 ベースの自動売買戦略コレクション。10年バックテスト (2015-2024) + OOS (2025-2026) で検証済みの **2本柱戦略** を運用するためのコード一式。

**最終更新**: 2026-06-18

---

## 🔥 いま進めている研究（最優先2件）

| 研究 | 状態 | 次のアクション | 計画書 |
|---|---|---|---|
| **LH3 Synapse B** | ✅ **検証完了** | NAS100 PF2.21⭐ / ポンド円1.39 / 豪ドル円1.41 / ユーロ円1.31 / ゴールド1.20 |
| **v2.3 Market Psychology** | ✅ **検証完了** | ドル円 PF1.63⭐ / スイス円1.44 |

👉 **[最終結果](docs/research/2大研究_最終結果_2026-06-12.md)** — 全銘柄の最適手法・RR・フィルタ設定の確定版

**運用7銘柄**: USDJPY / CHFJPY / NAS100 / GBPJPY / AUDJPY / EURJPY / XAUUSD  
**データ**: TradingView H4 実測を正とする

### すぐ使うファイル

| 目的 | ファイル |
|---|---|
| **Synapse Pine（検証反映・銘柄別自動）⭐** | `pine/research/synapse_h4_verified_strategy.pine` |
| **v2.3 Matrix Pine（NAS100対応）⭐** | `pine/research/market_psychology_v2_3_matrix_strategy.pine` |
| Synapse Pine（旧・波形可視化） | `pine/research/synapse_mtf_wave_reversal_v4.pine` |
| v2.1 Matrix Pine（旧版） | `pine/research/market_psychology_v2_matrix_strategy.pine` |
| Synapse 手法定義書 | [Synapse手法定義_v0_1.md](docs/research/Synapse手法定義_v0_1.md) |
| v2.1 仕様書 | [v2_spec.md](docs/research/market_psychology/v2_spec.md) |
| v2.1 フォワード記録 | [forward_log_v2_1_matrix.md](docs/research/market_psychology/forward_log_2026_05_v2_1_matrix.md) |
| 2大研究 検証計画（全体） | [2大研究_検証計画_2026-06-11.md](docs/research/2大研究_検証計画_2026-06-11.md) |

### 検証で得た銘柄別ベスト（Pineに反映済み）

| 銘柄 | Synapse構造/フィルタ/TP | v2.3 構造 |
|---|---|---|
| USDJPY | ihs / context / 1.5R | Sqz+Cap+LL |
| GBPJPY | ihs / diag / 1.5R（PF2.41★） | 除外 |
| XAGUSD | role / basic / 2.0R（PF2.19★） | Sqz |
| NAS100 | ihs / diag / 1.5R | Sqz+Cap（指数専用param） |

---

## 研究ダッシュボード

このリポジトリは、戦略コードだけでなく「何を研究しているか」を忘れないための研究台帳としても使います。

### 重要研究: H4 Double V Reclaim / 初動V

- 研究メモ: [docs/research/H4ダブルV回収_初動V_2026-06-02.md](docs/research/H4ダブルV回収_初動V_2026-06-02.md)
- TradingView可視化: [pine/visual/h4_double_v_short_denial_visual.pine](pine/visual/h4_double_v_short_denial_visual.pine)
- D1 V 日足専用可視化: [pine/visual/d1_v_context_daily_visual.pine](pine/visual/d1_v_context_daily_visual.pine)
- D1 V -> H4確認可視化: [pine/visual/d1_v_context_h4_visual.pine](pine/visual/d1_v_context_h4_visual.pine)
- H4T5級 高精度V可視化: [pine/visual/h4_psychological_v_t5_quality_visual.pine](pine/visual/h4_psychological_v_t5_quality_visual.pine)
- Strategy検証: [pine/production/h4_double_v_reclaim_strategy.pine](pine/production/h4_double_v_reclaim_strategy.pine)
- D1 V -> H4検証Strategy: [pine/production/d1_v_context_h4_strategy.pine](pine/production/d1_v_context_h4_strategy.pine)
- 狙い: 急落後のVそのものではなく、**V1売り失敗 -> V2押し -> V1右肩ゾーン突破**で、トレンド初動候補を探す研究。
- 最新仮説: H4単独ではなく、**D1 V Context + H4 Execute** に分けると、日足級の反転初動を拾える可能性がある。
- 最新更新: **日足チャートでD1 Vそのものを見る専用可視化** を追加。H4T5と同じ思想で、Vを直接エントリーにせず、**WATCH -> SIGNAL -> SKIP理由** に分ける。

### 重要研究: H4 V Denial Re-Acceleration / 売り手の損切り連鎖

- 研究メモ: [docs/research/H4_V否定_再加速_2026-06-05.md](docs/research/H4_V否定_再加速_2026-06-05.md)
- TradingView Strategy: [pine/research/h4_v_denial_reacceleration_strategy.pine](pine/research/h4_v_denial_reacceleration_strategy.pine)
- 狙い: **急落 -> 急反発 -> 上側棚 -> 売り手の損切りライン突破**を、チャートパターンではなく「売り手が負けを認める瞬間」として検出する。
- 表示順: **WATCH = 売り失敗の文脈 / SIGNAL = 損切りライン突破 / SIM FILL = 次足始値約定**。
- 現時点の扱い: **研究中・本番未採用**。H4T5やH4 V Initial Shelf Breakoutと比較し、目視で納得できる場所にだけ出るか確認する。

### 重要メモ: Market Psychology Squeeze / TradingView XAGUSD照合

- 研究メモ: [docs/research/市場心理スクイーズ厳選_2026-05-30.md](docs/research/市場心理スクイーズ厳選_2026-05-30.md)
- TradingView確認用Pine: [pine/research/market_psychology_squeeze_strict_strategy.pine](pine/research/market_psychology_squeeze_strict_strategy.pine)
- TradingView/OANDA XAGUSD再検証: [backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_oanda_xagusd_recheck/report_ja.md](backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_oanda_xagusd_recheck/report_ja.md)
- TradingView H4 OHLC再検証: [backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_ohlc_check/report_ja.md](backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_ohlc_check/report_ja.md)
- 狙い: 急落後の安値棚が崩れず、棚高値を抜けるところを **売り方の買い戻し連鎖** として捉える。
- 一言: **売り方が勝っているように見えた後、下がらなくなり、損切りの買い戻しが始まる瞬間を狙う研究**。
- 重要な扱い: **XAGUSD/OANDA はTradingView H4 OHLCを正として別管理**。ローカルPythonの `SILVER` 結果とは混ぜない。
- TradingViewトレード一覧照合: **15 trades / 勝率60.00% / PF 2.896 / Net +124,981.04 USD**。
- TradingView H4 OHLC基準の再検証: `SQZ_DEFAULT_RR2` が **TV一覧15件と日付15/15一致**。同期間R建てでは **15 trades / +12.00R / PF 3.00 / DD 4.00R**。
- 照合注意: TradingView確認用Pineの初期値は `SQZ_DEFAULT_RR2` に合わせる。`SQZ_STRICT_RR2` 条件のまま比較すると件数が減り、TradingView一覧とは一致しない。

### 終了研究: Short Covering Psychology Flow

- 研究メモ: [docs/research/ショートカバリング心理フロー_2026-06-03.md](docs/research/ショートカバリング心理フロー_2026-06-03.md)
- TradingView可視化: [pine/visual/short_covering_psychology_flow_visual.pine](pine/visual/short_covering_psychology_flow_visual.pine)
- 狙い: ローソク足の形ではなく、**売り手が安心していた状態が崩れ、損切りから買い戻しに変わる心理遷移**を可視化する。
- 表示順: **SELL DOMINANCE -> SELL FAILURE -> SHORT COVERING -> ACCELERATION**
- 現時点の扱い: **研究終了・本番不採用**。心理フローの参考アーカイブとして残す。
- 最新更新: ラベル洪水対策として、初期表示を **実戦レビュー** に変更。SELL DOMINANCE / SELL FAILURE の詳細は隠し、SHORT COVERING / ACCELERATION を主役にする。検出条件は厳選しすぎず、標準感度で候補が出る状態を維持。
- 終了理由: 入口の優位性が H4T5 / D1 V Context / Double V ほど明確ではなく、裁量判断が増えやすい。

| 優先 | 研究テーマ | 状態 | 入口 |
|---:|---|---|---|
| 1 | **受講生つまずきクラスタ** | 進行中 | [研究まとめ](docs/research/受講生つまずきクラスタ研究_2026-05-31.md) ／ [Pine v0.4](pine/research/student_stumble_zones_gbpjpy_v0_4.pine) |
| 2 | **H4 Double V Reclaim / 初動V** | **最重要・検証中** | [研究メモ](docs/research/H4ダブルV回収_初動V_2026-06-02.md) ／ [D1 V日足表示](pine/visual/d1_v_context_daily_visual.pine) ／ [D1 V->H4可視化](pine/visual/d1_v_context_h4_visual.pine) ／ [D1 V->H4検証](pine/production/d1_v_context_h4_strategy.pine) ／ [H4T5級 高精度V](pine/visual/h4_psychological_v_t5_quality_visual.pine) ／ [H4 Double V](pine/visual/h4_double_v_short_denial_visual.pine) |
| 3 | **H4 V Denial Re-Acceleration** | **重要・研究中** | [研究メモ](docs/research/H4_V否定_再加速_2026-06-05.md) ／ [Pine Strategy](pine/research/h4_v_denial_reacceleration_strategy.pine) |
| 4 | **Short Covering Psychology Flow** | **終了・本番不採用** | [研究メモ](docs/research/ショートカバリング心理フロー_2026-06-03.md) ／ [Pine可視化](pine/visual/short_covering_psychology_flow_visual.pine) |
| 5 | 受講生エントリー集中パターン | 進行中 | [受講生エントリー集中パターン研究_2026-05-31.md](docs/research/受講生エントリー集中パターン研究_2026-05-31.md) |
| 6 | トレード心理 / 群衆心理 | 進行中 | [研究インデックス.md](docs/research/研究インデックス.md) ／ [crowd_psychology_simple_visual.pine](pine/visual/crowd_psychology_simple_visual.pine) |
| 7 | Market Psychology Squeeze | TV OHLC照合済み | [研究メモ](docs/research/市場心理スクイーズ厳選_2026-05-30.md) ／ [XAGUSD TV一覧](backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_oanda_xagusd_recheck/report_ja.md) ／ [TV H4 OHLC再検証](backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_ohlc_check/report_ja.md) |
| 8 | **市場心理図鑑** | **Vol.1 + 収集ライブラリ** | [図鑑](docs/research/市場心理図鑑/README.md) ／ [収集90件+](docs/research/市場心理図鑑/collection/index.md) |
| 9 | Wavebox / Rebreak | 記録済み | [ウェーブボックス運用前提条件_v1.md](docs/research/ウェーブボックス運用前提条件_v1.md) |

---

## 📚 ドキュメント目次

| ドキュメント | 内容 |
|---|---|
| 👉 **[docs/trade_diary/README.md](docs/trade_diary/README.md)** | **トレード日誌トップ** — 実践日誌・心理記録・受講生記録 |
| 👉 **[戦略ガイド.md](戦略ガイド.md)** | **メインの説明書 (これを読めばOK)** |
| 👉 **[docs/バックテスト一覧.md](docs/バックテスト一覧.md)** | **全検証カタログ (試したもの全部の一覧)** |
| 📊 [docs/spreadsheet/](docs/spreadsheet/) | **Google スプレッドシート用 CSV/TSV** (9シート) |
| [docs/2本柱実用研究_2026-05-24.md](docs/2本柱実用研究_2026-05-24.md) | 2本柱研究ノート (公式版) |
| [docs/H4_T5_MACD_BB_実用監査_2026-05-24.md](docs/H4_T5_MACD_BB_実用監査_2026-05-24.md) | H4 T5 補助手法の実用監査 |
| [docs/H4_T5_本番運用ノート.md](docs/H4_T5_本番運用ノート.md) | H4 T5 本番運用ノート |
| [docs/research/ショート側研究_進行中_2026-05-28.md](docs/research/ショート側研究_進行中_2026-05-28.md) | ショート側研究ノート (**検証途中・本番未採用**) |
| [docs/research/H4ダブルV回収_初動V_2026-06-02.md](docs/research/H4ダブルV回収_初動V_2026-06-02.md) | H4 Double V Reclaim / 初動V研究 (**重要・可視化中**) |
| [docs/research/H4_V否定_再加速_2026-06-05.md](docs/research/H4_V否定_再加速_2026-06-05.md) | H4 V Denial Re-Acceleration 研究 (**重要・検証中**) |
| [docs/research/ショートカバリング心理フロー_2026-06-03.md](docs/research/ショートカバリング心理フロー_2026-06-03.md) | Short Covering Psychology Flow研究 (**終了・本番不採用**) |
| [docs/FX検証研究ノート_2015-2024.docx](docs/FX検証研究ノート_2015-2024.docx) | Word版総合レポート |
| [backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md](backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/report_ja.md) | TrendBreak+T5 アンサンブル検証 |

---

## 🎯 結論 (TL;DR)

### 採用戦略 — 5本柱

| 役割 | 戦略 | Pine ファイル | 時間足 | 対象銘柄 |
|---|---|---|---|---|
| **主力①** | **TrendBreakV1 HYBRID** | [`pine/production/TrendBreakV1_Final.pine`](pine/production/TrendBreakV1_Final.pine) | H1 | 6通貨 |
| **主力②** | **LH3 Synapse B** | [`pine/research/lower_high_synapse_b_symbol_presets_strategy_v0_1.pine`](pine/research/lower_high_synapse_b_symbol_presets_strategy_v0_1.pine) | H4 | NAS100⭐/XAUUSD/USDJPY/AUDJPY/EURJPY/GBPJPY |
| **主力③** | **B7棚 V Shelf Breakout** ⭐新 | [`pine/research/b7_shelf_breakout_strategy.pine`](pine/research/b7_shelf_breakout_strategy.pine) | H4 | 全7銘柄（プリセット選択） |
| **補助①** | **v2.3 Market Psychology** | [`pine/research/market_psychology_v2_3_matrix_strategy.pine`](pine/research/market_psychology_v2_3_matrix_strategy.pine) | H4 | USDJPY⭐/CHFJPY |
| **補助②** | **H4 T5 + MACD + BB** | [`pine/production/h4_t5_macd_bb_live_ready.pine`](pine/production/h4_t5_macd_bb_live_ready.pine) | H4 | 6通貨 |

### ⭐ LH3 Synapse B 研究経緯（2026-06-11〜13）

波動の「Lower High 3（切り下げ3回目）」の反転をA/B線とダイアゴナルブレイクで捉える手法。研究の流れ:

```
[着想] 波動2の終わりで波動3の初動を狙う = 「3回下げ止まった」確認後のエントリー
  ↓
[Python検証] tv_data/のH4データで8銘柄×複数構造(ihs/role/role_ab等)バックテスト
  → NAS100 PF2.21⭐ / XAGUSD PF2.19 / USDJPY PF1.27
  → CHFJPY PF0.47で除外 / XAGUSD 0件(構造依存)
  ↓
[精度フィルタ検証] ADX・adjust_ratio・body_ratioをオーバーレイテスト
  → Balanced/Precisionモードの有効性を確認
  → XAGUSDは role_ab_5pivot + Precision で復活(PF2.19)
  ↓
[Pine作成] synapse_h4_verified_strategy.pine — 銘柄別自動プリセット
  ↓
[バグ①] ポジションサイジング暴走 — 自作qty計算でロットが際限なく増加
  → 原因: equity×risk% / dist の計算がJPY通貨で異常値に
  → 修正: strategy.percent_of_equity(100) に統一
  ↓
[バグ②] ポジション持ちっぱなし — ゴールド8年/ポンド5年保有等
  → 原因: strategy.exit が risk0 > 0 の条件内にあり、
    bad fillでrisk0 ≤ 0の時にSL/TPもtimeoutも発動しない
  → 修正: 「保留→確定ラッチ」システムを導入
    pendStop/activeStop 2段構成でfill時に確定、
    risk0 ≤ 0 は即close("bad_fill")、
    timeoutはrisk0ガード外で常時チェック
  ↓
[RR最適化] 全銘柄でRR 1.5〜4.0をTV実測
  → 「早く取る型」(NAS100/USDJPY/AUDJPY/GBPJPY → RR2.0)
  → 「伸ばす型」(EURJPY/XAUUSD → RR3.0)
  → RR3.0が天井。4.0はほぼ同じ
  ↓
[フィルタ最適化] NO ENTRYフィルタのON/OFF をTV実測
  → XAUUSD: ON(PF2.98) / NAS100: OFF(PF2.21) / 他: OFF
  ↓
[V1スタイル可視化] Entry/SL/TP線 + IN/OUTラベル + R倍率表示
  ↓
[現在] 6銘柄対応・設定不要・全自動プリセット完成
```

**最終成績（TradingView H4 実測・設定不要）:**

| 銘柄 | PF | 勝率 | 件数 | RR | フィルタ |
|---|---:|---:|---:|---:|---|
| **NAS100** | **2.03** | 67% | 21 | 2.0 | OFF |
| **XAUUSD** | **1.30** | 46% | 41 | 3.0 | ON |
| **USDJPY** | **1.30** | 45% | 40 | 2.0 | OFF |
| **AUDJPY** | **1.29** | 51% | 45 | 2.0 | OFF |
| **EURJPY** | **1.23** | 53% | 34 | 3.0 | OFF |
| GBPJPY | 1.08 | 45% | 42 | 2.0 | OFF |

> Pine: [`pine/research/lower_high_synapse_b_symbol_presets_strategy_v0_1.pine`](pine/research/lower_high_synapse_b_symbol_presets_strategy_v0_1.pine)
> 検証詳細: [`docs/research/2大研究_最終結果_2026-06-12.md`](docs/research/2大研究_最終結果_2026-06-12.md)
> 手法定義: [`docs/research/Synapse手法定義_v0_1.md`](docs/research/Synapse手法定義_v0_1.md)
> 精度フィルタ: [`docs/research/Synapse_精度向上フィルタ_2026-06-11.md`](docs/research/Synapse_精度向上フィルタ_2026-06-11.md)

### ⭐ B7棚 V Shelf Breakout 研究経緯（2026-06-14〜18）

急落後のV字回復 → 棚形成 → 棚高値ブレイクを狙う手法。研究の流れ:

```
[着想] 急落否定後の棚ブレイクは「売り手の損切り連鎖」を捉えられるのでは？
  ↓
[Python検証] tv_data/のH4データで8銘柄バックテスト → AUDJPY除外
  ↓
[Pine v1→v2] var状態遷移バグ多発 → ローリングウィンドウ方式に全面書き直し
  ↓
[全銘柄パラメータ最適化] 棚数×棚幅×急落×RR×TIME×SL余白を網羅スイープ
  → 発見: SL幅を広くした方が良い銘柄が多い、TIMEは銘柄で最適が分かれる
  ↓
[★重要な発見: 先読みバイアス] TradingViewの警告から calc_on_order_fills=true が
  バックテストを楽観的にしていたと判明（同足で決済→再エントリーする挙動）
  → 例: ゴールド PF2.88 → 0.766 と激変
  ↓
[正直版で再最適化] calc_on_order_fills=false（現実的）に変更し全銘柄を再検証
  → Pythonのhonestバックテスト(SL優先・同足再エントリーなし)で候補を出し、
    TVで1銘柄ずつ実測確認
  ↓
[現在] 全7銘柄を「先読みバイアスなしの本物の数値」で確定。全銘柄PF1.4以上
```

**銘柄別最適パラメータ（2026-06-18 正直版・calc_on_order_fills=false）:**

| 銘柄 | PF | 勝率 | 件数 | 棚数 | 急落 | 棚幅 | SL余白 | RR | TIME | リスク幅 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **USDJPY** | **2.96** | 53% | 17 | 7 | 3.0 | 1.8 | 0.85 | 2.5 | OFF | 2.5 |
| **NAS100** | **2.23** | 52% | 21 | 3 | 3.0 | 2.0 | 0.80 | 4.2 | 60 | 1.6 |
| **GBPJPY** | **1.95** | 50% | 42 | 5 | 2.8 | 2.5 | 0.80 | 2.5 | 60 | 2.5 |
| **CHFJPY** | **1.81** | 43% | 91 | 5 | 3.0 | 2.5 | 0.20 | 2.2 | OFF | 2.5 |
| **XAUUSD** | **1.78** | 47% | 77 | 4 | 2.8 | 2.5 | 0.80 | 2.2 | OFF | 2.5 |
| **EURJPY** | **1.52** | 54% | 70 | 6 | 3.5 | 2.5 | 0.50 | 1.2 | OFF | 2.5 |
| **XAGUSD** | **1.47** | 37% | 126 | 3 | 2.8 | 2.5 | 1.00 | 3.0 | OFF | 2.7 |

> **重要:** 上記は先読みバイアスを排除した**実際の取引で再現できる現実的な数値**。
> 設定画面で各値を手動入力（プリセット廃止済み・表示値=実際の値）。
>
> Pine: [`pine/research/b7_shelf_breakout_strategy.pine`](pine/research/b7_shelf_breakout_strategy.pine)
> 検証詳細: [`docs/research/B7棚_TV検証_2026-06-14.md`](docs/research/B7棚_TV検証_2026-06-14.md)
> パラメータ解説: [`docs/research/B7棚_パラメータ解説_2026-06-16.md`](docs/research/B7棚_パラメータ解説_2026-06-16.md)
> 手法条件: [`docs/research/B7棚_発動条件_2026-06-14.md`](docs/research/B7棚_発動条件_2026-06-14.md)

### ⭐ Synapse B スイング版 成績（2026-06-12 TradingView H4 実測・設定不要）

| 銘柄 | PF | 勝率 | 件数 | 自動設定 |
|---|---:|---:|---:|---|
| **NAS100** | **2.03** | 67% | 21 | RR2.0 / TIME60 |
| XAUUSD | 1.30 | 46% | 41 | RR3.0 / TIME60 / フィルタON |
| USDJPY | 1.30 | 45% | 40 | RR2.0 / TIME60 |
| AUDJPY | 1.29 | 51% | 45 | RR2.0 / TIME60 |
| EURJPY | 1.23 | 53% | 34 | RR3.0 / TIME60 |
| GBPJPY | 1.08 | 45% | 42 | RR2.0 / TIME60 |

👉 **[最終結果の詳細](docs/research/2大研究_最終結果_2026-06-12.md)**

### 進行中の研究

| 研究 | 状態 | メモ |
|---|---|---|
| [H4 Double V Reclaim / 初動V](docs/research/H4ダブルV回収_初動V_2026-06-02.md) | 🔬 最重要・可視化中 | V1売り失敗後、V2押しからV1右肩ゾーン突破を狙う。小さいノイズVを削って「トレンド初動のV」を探す研究 |
| [H4 V Denial Re-Acceleration](docs/research/H4_V否定_再加速_2026-06-05.md) | 🔬 重要・検証中 | 急落後のVを売り失敗の文脈として使い、上側棚から売り手の損切りライン突破を狙う研究 |
| [Short Covering Psychology Flow](docs/research/ショートカバリング心理フロー_2026-06-03.md) | 終了・本番不採用 | 売り優勢から売り失敗、損切り買い戻し、加速までの心理遷移をH4で可視化する研究。優位性が明確でないため終了 |
| [ショート側研究 2026-05-28](docs/research/ショート側研究_進行中_2026-05-28.md) | 🔬 検証途中 | ロング版ミラーは不採用。H4 1ヶ月安値更新後の安値停滞ブレイクショートが暫定候補 |

### 推奨運用構成（4本柱・全銘柄）

| 銘柄 | TrendBreak H1 | Synapse B H4 | B7棚 H4 | v2心理 H4 | T5 H4 | 手法数 |
|---|:---:|:---:|:---:|:---:|:---:|---:|
| **NAS100** | - | ⭐PF2.03 | ⭐PF2.23 | - | - | 2 |
| **USDJPY** | ✅ | ✅PF1.30 | ⭐**PF2.96** | ⭐PF1.63 | ✅ | 5 |
| **XAUUSD** | ✅ | ✅PF1.30 | ✅PF1.78 | - | ✅ | 4 |
| **AUDJPY** | - | ✅PF1.29 | ❌ | ✅PF5.67 | - | 2 |
| **EURJPY** | ✅ | ✅PF1.23 | ✅PF1.52 | - | ✅ | 4 |
| **CHFJPY** | ✅ | - | ✅PF1.81 | ⭐PF1.44 | ✅ | 4 |
| **GBPJPY** | ✅ | △PF1.08 | ⭐**PF1.95** | - | ✅ | 4 |
| **XAGUSD** | ✅ | - | ⭐**PF1.47** | - | ✅ | 3 |

> ※B7棚は2026-06-18に先読みバイアスを排除した正直版で全銘柄再確定。

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

### Synapse B（⭐新・スイング向け）— 設定不要で銘柄切替だけ

1. `pine/research/lower_high_synapse_b_symbol_presets_strategy_v0_1.pine` をPine Editorに貼る
2. **H4チャート**で以下の銘柄に載せる: NAS100 / XAUUSD / USDJPY / AUDJPY / EURJPY / GBPJPY
3. **設定は一切不要**（銘柄別にRR/TIME/フィルタが全自動）

### v2.3 Market Psychology — 設定不要

1. `pine/research/market_psychology_v2_3_matrix_strategy.pine` をPine Editorに貼る
2. **H4チャート**で USDJPY / CHFJPY に載せる
3. **設定は一切不要**

### TrendBreakV1 + H4 T5（従来の2本柱）

1. **H1チャート 6枚** に `pine/production/TrendBreakV1_Final.pine` (Auto preset)
2. **H4チャート 6枚** に `pine/production/h4_t5_macd_bb_live_ready.pine`
3. 通貨: **XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, SILVER** の6つ

詳細は **[戦略ガイド.md](戦略ガイド.md)** ／ **[最終結果](docs/research/2大研究_最終結果_2026-06-12.md)** を参照。

---

## 📂 リポジトリ構成

```
fx-ai/
├── README.md                       ← このファイル (入り口)
├── 戦略ガイド.md               ← 戦略の説明書 (本体)
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
│   ├── バックテスト一覧.md              全検証カタログ
│   ├── 2本柱実用研究_2026-05-24.md  最新の総括
│   ├── H4_T5_MACD_BB_実用監査_2026-05-24.md  実用監査
│   ├── H4_T5_本番運用ノート.md            運用ノート
│   ├── research/                      研究中 (各戦略のメモ)
│   │   ├── 受講生つまずきクラスタ研究_2026-05-31.md  ⭐ つまずき研究まとめ
│   │   ├── student_entries_extracted.csv                  ⭐ 137件エントリー
│   │   ├── student_stumble_clusters_v0_2.csv              ⭐ 29クラスタ
│   │   ├── 研究インデックス.md                              全研究台帳
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

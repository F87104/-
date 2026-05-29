# 検証結果 全カタログ (BACKTEST_INDEX.md)

> このリポジトリで実施した **全バックテスト** の一覧。
> 何をやったか・どこに結果があるか・採用/不採用の判定 を一覧化。

**最終更新**: 2026-05-28
**対応戦略バージョン**: v2.0 (TrendBreakV1 HYBRID + H4 T5 MACD BB)

---

## 目次

1. [採用判定マトリクス (一目で全部)](#1-採用判定マトリクス)
2. [手法別カタログ](#2-手法別カタログ)
3. [通貨別 主要成績マトリクス](#3-通貨別-主要成績マトリクス)
4. [期間別 (IS / OOS) 比較](#4-期間別-is--oos-比較)
5. [時間軸 (TF) 比較](#5-時間軸比較)
6. [研究系・補助検証](#6-研究系補助検証)
7. [インデックス系 (NAS100 / SPX500)](#7-インデックス系)
8. [アンチパターン (やったけどダメだった)](#8-アンチパターン)

---

## 1. 採用判定マトリクス

| # | 手法 | 期間 | Trades | WR | PF | Total R | DD | 判定 | コメント |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **TrendBreakV1 HYBRID** | 2015-2024 (7通貨) | 461 | 36.9% | 1.62 | **+191.5R** | 14.0R | ✅ **採用 (主力)** | H1 ブレイクアウト |
| 1' | TrendBreakV1 HYBRID | 2015-2024 (6通貨 AUDJPY除外) | 381 | 39.4% | 1.79 | +194.6R | 11.9R | ✅ 採用 | AUDJPY抜きが現実的 |
| 2 | **H4 T5 + MACD + BB (実戦用)** | 2015-2024 | 34 | 61.8% | 3.56 | **+29.2R** | 4.4R | ✅ **採用 (補助)** | 急落V字回復+停滞ブレイク |
| 2' | H4 T5 + MACD + BB (実戦用) | 2025-2026 OOS | 15 | 66.7% | 2.44 | +7.3R | 2.0R | ✅ OOSで再現 | 過剰最適化なし |
| 3 | TrendBreakV1 + T5実戦 (両方フル) | 2015-2024 (6通貨) | **411** | 40.9% | **1.86** | **+219.9R** | **11.9R** | ✅ **本番運用** | 採用構成 |
| 4 | Sai Best Method (急な揺り戻し) | 2015-2024 | 378 | 44.4% | 1.47 | +98.8R | 13.2R | ⚠️ **archive** | v1 旧採用、v2 では外す |
| 5 | Sai H1 全体 (4手法込み) | 2015-2024 | 1108 | 41.6% | 1.05 | +99.9R | 21.9R | ❌ 不採用 | 平均が低い、外す価値 |
| 6 | H4 急落V字 単独 (strict_v) | 2015-2024 | 39 | 30.8% | 0.72 | **-7.2R** | 13.2R | ❌ **単独NG** | フィルタなしでは赤字 |
| 7 | Synapse v0 (Tobi系初期) | 2015-2024 (H4) | 413 | 32.0% | 0.85 | **-42.4R** | 48.8R | ❌ 不採用 | エリオット風はそのままでは弱い |
| 8 | Synapse v1 (Tobi系改善) | 2015-2024 (H1) | 81 | 56.8% | 1.42 | +14.8R | 5.4R | ⚠️ 研究中 | A_early モードが有望 |
| 9 | Elliott W5 RR3 LOOSE (5波目) | 2015-2024 (H1) | 450 | 30.0% | 1.23 | +73.3R | 34.7R | ❌ 不採用 | DD大きく実用厳しい |
| 10 | VFIB_618_BODY60_LONG (V字フィボ) | 2015-2024 (H1) | 1513 | 38.6% | 1.19 | +186.6R | 50.9R | ❌ 不採用 | 件数◎ DD◎ 平均R薄い |
| 11 | TrendBreakV1 (NAS100) | 2015-2024 | (参考) | - | - | - | - | 📊 参考 | インデックス検証 |
| 12 | TrendBreakV1 (SPX500) | 2015-2024 | (参考) | - | - | - | - | 📊 参考 | インデックス検証 |
| 13 | TrendBreakV1 Pyramiding sweep | 2015-2024 | 各種 | - | - | - | - | 🔬 研究 | エントリー数1が最適確認 |
| 14 | TrendBreakV1 騙し回避フィルタ | 2015-2024 | 各種 | - | - | - | - | 🔬 研究 | body60+early1 が候補 |
| 15 | ショート側研究 2026-05-28 | 2015-2026 | 各種 | - | - | - | - | 🔬 検証途中 | ロング版ミラーは不採用。1ヶ月安値更新後の安値停滞下抜けが暫定候補 |

**凡例**:
- ✅ 採用 = 現在の本番運用に使用中
- ⚠️ archive = 過去の採用案、現在は参考
- ❌ 不採用 = 検証で不合格
- 🔬 研究 = パラメータ調整・補助研究
- 📊 参考 = 拡張性検証 (FX以外)

---

## 2. 手法別カタログ

### 2-1. TrendBreakV1 系 (✅ 主力採用)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **HYBRID 標準** | [`backtests/trendbreak_v1/results_2015_2024/report.md`](../backtests/trendbreak_v1/results_2015_2024/report.md) | 4モード × 7通貨 × 10年 | conservative が最安定 (+184R) |
| **緩和スタディ** | [`backtests/relaxation/RELAXATION_REPORT.md`](../backtests/relaxation/RELAXATION_REPORT.md) | 19パターンの緩和案 | HYBRID 最適化で +23%, 頻度 +27% |
| **コスト監査** | [`backtests/audit/`](../backtests/audit/) | スプレッド・スリッページ込み | -21% でも +146R 維持 |
| **fakeout 前後比較** | [`backtests/trendbreak_v1/fakeout_before_after_2015_2024/report_ja.md`](../backtests/trendbreak_v1/fakeout_before_after_2015_2024/report_ja.md) | 騙し回避フィルタ 4ルール | baseline最強 / body60+early1 で PF最大 |
| **fakeout feature 詳細** | [`backtests/trendbreak_v1/fakeout_feature_study_2015_2024/report_ja.md`](../backtests/trendbreak_v1/fakeout_feature_study_2015_2024/report_ja.md) | 1000+ ルール組合せスイープ | 単独フィルタは効果限定的 |
| **fakeout rule matrix** | [`backtests/trendbreak_v1/fakeout_rule_matrix_2015_2024/rule_matrix_report_ja.md`](../backtests/trendbreak_v1/fakeout_rule_matrix_2015_2024/rule_matrix_report_ja.md) | フィルタ組合せ行列 | 3条件以上重ねるとTrades激減 |
| **Pyramiding スイープ** | [`backtests/trendbreak_v1/pyramiding_sweep_2015_2024/report_ja.md`](../backtests/trendbreak_v1/pyramiding_sweep_2015_2024/report_ja.md) | エントリー数 1〜5 | エントリー数 1 (現状) が最適 |
| **2026-05-24 最新** | [`backtests/trendbreak_v1/results_2026_05_24/`](../backtests/trendbreak_v1/results_2026_05_24/) | NAS100/SPX500 参考データ | FX以外でも機能可能性 |

**🏆 採用パラメータ**: HYBRID (通貨別最適化) + 騙し回避OFF (baseline)
**🏆 採用設定**: エントリー数 1, RR 1:3, ATR×1.5 stop, リスク 1%/トレード

---

### 2-2. H4 T5 + MACD + BB 系 (✅ 補助採用)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **V字回復 + T5 検証 (本命)** | [`backtests/elliott_fibo/results_2015_2024/t5_macd_bb_vshape_validation/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/t5_macd_bb_vshape_validation/report_ja.md) | 全プリセット網羅 | **Strict 0.75-1.00 + REC1.2 が最良** |
| **MACD+BB Harsh 検証** | [`backtests/elliott_fibo/results_2015_2024/t5_macd_bb_harsh_validation/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/t5_macd_bb_harsh_validation/report_ja.md) | 厳しめフィルタ群 | Strict 確認 |
| **OOS 2025-2026** | [`backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb/report_ja.md`](../backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb/report_ja.md) | 未使用期間検証 | +7.3R / PF 2.44 / 過剰最適化なし |
| **OOS Vshape** | [`backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb_vshape/report_ja.md`](../backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb_vshape/report_ja.md) | OOSでのV字版 | OOS再現性確認 |
| **回復比率スイープ** | [`backtests/elliott_fibo/results_2025_2026_oos/t5_recovery_ratio_sweep/report_ja.md`](../backtests/elliott_fibo/results_2025_2026_oos/t5_recovery_ratio_sweep/report_ja.md) | 0.80〜2.00 まで全比率 | **1.20〜1.22 が黄金比率** |
| **失敗フィルタ検証** | [`backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/`](../backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/) | 失敗時の特徴抽出 | BB高、MACD弱い、時間経過が原因 |
| **実用ロバスト監査** | [`backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/report_ja.md`](../backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/report_ja.md) | Leave-one-out + 閾値感度 | BB幅<=4ATR が最も重要 |
| **運用堅牢化** | [`backtests/elliott_fibo/results_2026_05_24/t5_operational_hardening/report_ja.md`](../backtests/elliott_fibo/results_2026_05_24/t5_operational_hardening/report_ja.md) | 本番運用想定の追加チェック | live ready で確認済 |
| **V字回復 トリガー研究** | [`backtests/elliott_fibo/results_2015_2024/v_recovery_trigger/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/v_recovery_trigger/report_ja.md) | stagnation / rebreak / 両方 | **stagnation+rebreak が最強** WR75% |
| **V字回復 緩和ラダー** | [`backtests/elliott_fibo/results_2015_2024/v_recovery_relaxation_ladder/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/v_recovery_relaxation_ladder/report_ja.md) | 条件緩和の段階検証 | 緩めすぎは赤字 |
| **V字回復 H1/H4 比較** | [`backtests/elliott_fibo/results_2015_2024/v_recovery_h1_h4_compare/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/v_recovery_h1_h4_compare/report_ja.md) | TF比較 | **H4 が H1 より明確に優位** |
| **非フィボ系ツール検証** | [`backtests/elliott_fibo/results_2015_2024/v_recovery_non_fibo_tools/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/v_recovery_non_fibo_tools/report_ja.md) | RSI/MA/VWAPなど | MACD+BB に勝るものなし |
| **vshape quant filters** | [`backtests/elliott_fibo/results_2015_2024/vshape_quant/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/vshape_quant/report_ja.md) | 定量フィルタ探索 | recovery比率1.20が黄金 |
| **indicator robust search** | [`backtests/elliott_fibo/results_2015_2024/t5_indicator_robust_search/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/t5_indicator_robust_search/report_ja.md) | 各種指標の組合せ | MACD+BB 確定 |
| **indicator compatibility** | [`backtests/elliott_fibo/results_2015_2024/indicator_compatibility_search/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/indicator_compatibility_search/report_ja.md) | 指標相性 | BB幅+MACDが最相性 |
| **indicator deep validation** | [`backtests/elliott_fibo/results_2015_2024/indicator_deep_validation/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/indicator_deep_validation/report_ja.md) | 深掘り検証 | フィルタ強度の最終調整 |
| **t5 skeptic audit** | [`backtests/elliott_fibo/results_2015_2024/t5_skeptic_audit/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/t5_skeptic_audit/report_ja.md) | 「これは本当?」監査 | データ漏洩なし確認 |

**🏆 採用パラメータ**:
- V字定義: Balanced REC1.2 (下落本数の 1.20 倍以内に 61.8〜80% 回復)
- フィルタ: Strict 0.75-1.00 + width<=7
- MACD: ヒストグラムが3本前より上昇
- 騙し回避: BB<=0.95 + 16本以内 + 弱いrebreak除外
- SL: V字の安値 - ATR×0.25, TP: RR 1:2

---

### 2-2.5. ショート側研究 2026-05-28 (🔬 検証途中)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **研究ノート** | [`docs/research/short_side_research_2026-05-28_in_progress.md`](research/short_side_research_2026-05-28_in_progress.md) | ショート側検証の途中経過まとめ | まずここを読む |
| **結果フォルダ入口** | [`backtests/elliott_fibo/results_2026_05_28/README.md`](../backtests/elliott_fibo/results_2026_05_28/README.md) | ショート検証フォルダの地図 | 検証途中であることを明記 |
| **T5ショート反転ミラー** | [`backtests/elliott_fibo/results_2026_05_28/t5_short_mirror_validation/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/t5_short_mirror_validation/report_ja.md) | ロング版 H4 V候補 T5 + MACD + BB の上下反転 | 実戦ミラーは 18 trades / -12.82R / PF 0.15 で不採用 |
| **高ボラ下落継続** | [`backtests/elliott_fibo/results_2026_05_28/t5_short_high_vol_continuation/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/t5_short_high_vol_continuation/report_ja.md) | ADX高め、BB幅7-10ATR、rebreakなどを検証 | プラス断片はあるがOOS不足 |
| **高ボラ下落継続 実戦化監査** | [`backtests/elliott_fibo/results_2026_05_28/t5_short_practical_hardening/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/t5_short_practical_hardening/report_ja.md) | 出口、建値移動、時間撤退を検証 | DDは抑えられるが本番採用には不足 |
| **1ヶ月安値更新後の安値停滞ブレイク** | [`backtests/elliott_fibo/results_2026_05_28/monthly_low_rebreak_short/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/monthly_low_rebreak_short/report_ja.md) | 1〜3ヶ月安値更新後の戻り再下落/安値停滞を検証 | 暫定本命。深掘り後の主条件は18 trades / +13.61R / PF 2.78。ただしOOS1件のみ |
| **安値更新期間・利確基準の深掘り** | [`backtests/elliott_fibo/results_2026_05_28/low_break_lookback_exit_study/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/low_break_lookback_exit_study/report_ja.md) | 0.5〜6ヶ月lookback、レンジ/トレンド分類、利確基準を比較 | 1ヶ月が最も強い。3ヶ月以上は強くならず、長期lookbackは戻りやすい |
| **H1安値更新ショート検証** | [`backtests/elliott_fibo/results_2026_05_28/h1_low_break_lookback_exit_study/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/h1_low_break_lookback_exit_study/report_ja.md) | H4本命をH1へ換算し、0.5〜6ヶ月lookbackを比較 | H1安値停滞型は弱い。GBPJPY 0.5ヶ月rebreakは別候補として有望 |
| **H4安値停滞 深掘り** | [`backtests/elliott_fibo/results_2026_05_28/h4_stagnation_deep_dive/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/h4_stagnation_deep_dive/report_ja.md) | 停滞レンジ品質、下抜け足、サポート保持期間、直後フォロースルー、出口管理を比較 | サポート保持60-119本とGBPJPYが強い。12本以内1R未達撤退が次の候補 |
| **H4安値停滞 追加検証** | [`backtests/elliott_fibo/results_2026_05_28/h4_stagnation_followup_validation/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/h4_stagnation_followup_validation/report_ja.md) | 重複除去後に、通貨除外、support age、時間切れ撤退を再評価 | Primary L120 core4 + 固定2Rが最もきれい。support60-119は強いが実質8件 |
| **H4安値停滞 精度向上** | [`backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/h4_stagnation_precision_hardening/report_ja.md) | Pine実装に向け、下抜け深さ、終値位置、新しい支持線の強さを検証 | core4厳選は8 trades / +15.71R / 全勝。ただし件数不足 |
| **H4安値停滞 Pine可視化** | [`pine/visual/h4_low_stagnation_short_visual.pine`](../pine/visual/h4_low_stagnation_short_visual.pine) | 候補/実戦候補/厳選候補/見送り理由をTradingView上で表示 | 検証用。CSV照合とフォワード記録に使う |
| **H4安値停滞 Pine strategy** | [`pine/research/h4_low_stagnation_short_strategy.pine`](../pine/research/h4_low_stagnation_short_strategy.pine) | TradingViewのストラテジーテスターで候補/実戦候補/厳選候補を検証 | H4チャート専用の研究版 |
| **H4安値停滞 Pine変換監査** | [`backtests/elliott_fibo/results_2026_05_28/h4_low_stag_pine_parity_audit/report_ja.md`](../backtests/elliott_fibo/results_2026_05_28/h4_low_stag_pine_parity_audit/report_ja.md) | Python検証を正として、Pineが同じシグナルを出すか照合 | Pine成績は一致確認まで採用判断に使わない |

**暫定ルール**: H4で過去120本の安値を終値更新 → 安値圏の停滞下抜け → ADX>=30, BB幅3-8ATR, risk<=1.5ATR → 次足ショート, SLは停滞レンジ上, TPは2R。

追加メモ: 重複除去後は、広いPracticalより `Primary L120 core4` が最も実戦候補に近い。Pineでは `候補`, `実戦候補`, `厳選候補`, `強い観察タグ` の4段階表示が現実的。厳選候補は core4 + 下抜け深さ>=0.10ATR + 終値位置<=0.50 + fresh supportなら下抜け深さ>=0.20ATR。

**判定**: 本番未採用。Primary L120 core4を中心にアラート監視し、30から50件のフォワード記録が必要。

---

### 2-3. Sai H1 系 (⚠️ archive)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **Sai H1 全体** | [`backtests/sai_h1/results_2015_2024/report.md`](../backtests/sai_h1/results_2015_2024/report.md) | 4手法 (停滞・V字・急揺戻し・レンジ2回目) | 全体 PF 1.05 弱い |
| **Best Method 深堀り** | [`backtests/sai_h1/deep_dive_best_method/report.md`](../backtests/sai_h1/deep_dive_best_method/report.md) | 急な揺り戻し+高値停滞 | PF 1.47 / +98.8R |
| **TF 比較** | [`backtests/sai_h1/timeframe_comparison_2015_2024/report_ja.md`](../backtests/sai_h1/timeframe_comparison_2015_2024/report_ja.md) | H1/H4/D1 比較 | H4 と D1 が有望 → 後のV字研究へ |
| **XAUUSD テスト** | [`backtests/sai_h1/test_xau/report.md`](../backtests/sai_h1/test_xau/report.md) | XAUUSD単独テスト | アセット分析 |

**判定**: v1 アンサンブルでは採用したが、v2 では H4 T5 MACD BB に置き換え。
Pine: [`pine/archive/sai_best_method_strategy.pine`](../pine/archive/sai_best_method_strategy.pine), [`pine/visual/sai_h1_visual_scanner.pine`](../pine/visual/sai_h1_visual_scanner.pine), [`pine/visual/sai_mtf_visual_checker.pine`](../pine/visual/sai_mtf_visual_checker.pine)

---

### 2-4. 急落V字回復 系 (❌ 単独NG, 環境認識用)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **Strict V字回復 (単独)** | [`backtests/elliott_fibo/results_2015_2024/strict_v_recovery/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/strict_v_recovery/report_ja.md) | 完全回復・速度重視のV字 | 単独 -7R PF 0.72 ❌ |
| **TrendBreakV1 + H4 V字 (組合せ)** | [`backtests/ensemble/trendbreak_h4_v_combo_2015_2024/report_ja.md`](../backtests/ensemble/trendbreak_h4_v_combo_2015_2024/report_ja.md) | アンサンブル検証 | 同一通貨空き時追加でも改善せず |

**判定**: V字単独で売買NG。**環境認識・候補抽出**として使い、T5+MACD+BBで絞る。
Pine: [`pine/visual/h4_sharp_drop_v_recovery_visual.pine`](../pine/visual/h4_sharp_drop_v_recovery_visual.pine) は可視化のみ。

---

### 2-5. Synapse / Tobi 系 (⚠️ 研究中)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **Synapse v0** | [`backtests/synapse_v0/results_2026_05_24/report_ja.md`](../backtests/synapse_v0/results_2026_05_24/report_ja.md) | エリオット風 H4 / 全通貨 | 全体 -42R ❌ XAUUSD/GBPJPYで大負け |
| **Synapse v1** | [`backtests/synapse_v1/results_2026_05_24/report_ja.md`](../backtests/synapse_v1/results_2026_05_24/report_ja.md) | 改善版 H1 / 全通貨 | 全体 +14.8R / PF 1.42 / A_early モード WR70% 有望 |
| **Synapse v1 (USDJPY M1)** | [`backtests/synapse_v1/results_usdjpy_m1_timeframes_2026_05_24/report_ja.md`](../backtests/synapse_v1/results_usdjpy_m1_timeframes_2026_05_24/report_ja.md) | M1 時間軸の検証 | 短期では PF低下 |

**判定**: v1 の A_early モードは WR 70.8% / PF 2.33 で有望。本番採用には件数とOOS確認が必要。

---

### 2-6. V字フィボ / Elliott (❌ 不採用, 研究済)

| 検証 | パス | 概要 | 結論 |
|---|---|---|---|
| **Elliott + V字フィボ 全体** | [`backtests/elliott_fibo/results_2015_2024/report_ja.md`](../backtests/elliott_fibo/results_2015_2024/report_ja.md) | 数百パターン網羅 | 件数◎ だが PF<1.3, DD大 |

**TOP 5 (Total R 順, 全体表より)**:

| 戦略 | TF | Trades | WR | PF | Total R | DD |
|---|---|---|---|---|---|---|
| VFIB_618_BODY60_LONG_RR2 | H1 | 1513 | 38.6% | 1.19 | +186.6R | 50.9R |
| VFIB_618_BODY60_LONG_REC1_RR2 | H1 | 1074 | 39.1% | 1.22 | +148.9R | 29.5R |
| VFIB_618_BODY60_LONG_SPEED030_RR2 | H1 | 1191 | 38.2% | 1.18 | +134.0R | 32.3R |
| VFIB_618_RR2 | H4 | 887 | 41.8% | 1.25 | +126.9R | 18.6R |
| VFIB_618_BODY50_RR2 | H4 | 812 | 42.5% | 1.28 | +126.9R | 16.1R |

**判定**: 件数とTotal Rは出るが、PF 1.2 前後・DD が大きく実用にならない。
→ 結局この研究から **H4 V候補 + T5 MACD BB** が生まれた (品質を絞る方向)。

---

## 3. 通貨別 主要成績マトリクス

### 採用構成 (TrendBreakV1 + T5 MACD BB) 2015-2024 (両方フル運用, baseline)

| 通貨 | Trades | WR | PF | Total R | MaxDD | 連敗 | 採用判定 |
|---|---|---|---|---|---|---|---|
| **XAUUSD** | 79 | 45.6% | 2.29 | **+58.2R** | 6.2R | 6 | ✅ **エース** |
| **GBPJPY** | 64 | 42.2% | 2.05 | +40.1R | 6.2R | 6 | ✅ |
| **SILVER** | 64 | 43.8% | 1.87 | +36.6R | 6.4R | 5 | ✅ |
| **USDJPY** | 68 | 38.2% | 1.74 | +31.9R | 9.4R | 9 | ✅ |
| **CHFJPY** | 67 | 37.3% | 1.62 | +27.3R | 9.4R | 10 | ✅ |
| **EURJPY** | 57 | 31.6% | 1.31 | +12.4R | 7.4R | 7 | ✅ (弱め) |
| ❌ **AUDJPY** | 82 | 25.6% | 0.97 | **-2.1R** | **18.0R** | **12** | ❌ **除外** |

### TrendBreakV1 単独 (baseline, 2015-2024)

| 通貨 | Trades | WR | PF | Total R |
|---|---|---|---|---|
| XAUUSD | 75 | 44.0% | 2.21 | +53.2R |
| USDJPY | 64 | 37.5% | 1.72 | +29.9R |
| EURJPY | 55 | 30.9% | 1.29 | +11.4R |
| GBPJPY | 59 | 42.4% | 2.11 | +39.1R |
| CHFJPY | 64 | 35.9% | 1.56 | +24.4R |
| AUDJPY | 80 | 25.0% | 0.95 | -3.1R |
| SILVER | 64 | 43.8% | 1.86 | +36.6R |

### H4 T5 MACD BB (実戦用フィルタ, 2015-2024)

| 通貨 | Trades | WR | PF | Total R |
|---|---|---|---|---|
| XAUUSD | 7 | 71.4% | 7.71 | +8.6R |
| USDJPY | 8 | 62.5% | 4.89 | +7.9R |
| CHFJPY | 5 | 80.0% | 7.90 | +6.9R |
| GBPJPY | 10 | 60.0% | 2.60 | +6.5R |
| AUDJPY | 4 | 75.0% | 4.83 | +3.9R |
| SILVER | 3 | 66.7% | 2.06 | +1.1R |
| EURJPY | 2 | 50.0% | 1.96 | +1.0R |

### Sai Best Method (急な揺り戻し+停滞, 2015-2024)

| 通貨 | Trades | WR | PF | Total R |
|---|---|---|---|---|
| XAUUSD | 68 | 50.0% | 2.64 | +55.8R |
| SILVER | 0 | - | - | - |
| EURJPY | 56 | 50.0% | 1.73 | +20.3R |
| GBPJPY | (内訳要参照) | - | - | - |
| (詳細は deep_dive_best_method 参照) | | | | |

---

## 4. 期間別 (IS / OOS) 比較

### TrendBreakV1 年別 (2015-2024)

| 年 | Trades | WR | PF | Total R | DD | 連敗 | コメント |
|---|---|---|---|---|---|---|---|
| 2015 | 34 | 35.3% | 1.49 | +11.4R | 5.4R | 5 | 中庸 |
| 2016 | 44 | 34.1% | 1.45 | +13.7R | 8.2R | 6 | 中庸 |
| 2017 | 43 | 34.9% | 1.49 | +14.4R | 7.7R | 7 | 中庸 |
| **2018** | 55 | 32.7% | 1.34 | +13.4R | **14.0R** | **13** | ⚠️ 苦戦年 |
| **2019** | 53 | 49.1% | **2.58** | **+46.0R** | 4.4R | 4 | 🟢 大当たり |
| 2020 | 52 | 36.5% | 1.62 | +21.4R | 10.4R | 10 | 中庸 |
| 2021 | 46 | 39.1% | 1.79 | +23.4R | 5.7R | 4 | 中庸 |
| **2022** | 44 | 40.9% | 1.95 | **+26.0R** | 4.3R | 4 | 🟢 大当たり |
| 2023 | 46 | 32.6% | 1.38 | +12.1R | 9.4R | 9 | 中庸 |
| 2024 | 44 | 31.8% | 1.31 | +9.8R | 7.5R | 7 | 中庸 |

### H4 T5 MACD BB IS/OOS 比較

| プリセット | 期間 | Trades | WR | Total R | PF | DD |
|---|---|---|---|---|---|---|
| **Strict 0.75-1.00 + REC1.2** | IS 2015-2024 | 99 | 55.6% | +59.8R | 2.55 | 6.7R |
| **Strict 0.75-1.00 + REC1.2** | OOS 2025-2026 | 15 | 66.7% | +7.3R | 2.44 | 2.0R |
| Robust 0.75-1.05 + REC1.5 | IS 2015-2024 | 129 | 52.7% | +64.5R | 2.17 | 8.8R |
| Robust 0.75-1.05 + REC1.5 | OOS 2025-2026 | 21 | 61.9% | +9.2R | 2.27 | 2.0R |
| Current 0.60-1.10 + REC1.0 | IS 2015-2024 | 142 | 50.7% | +53.9R | 1.81 | 9.8R |
| Current 0.60-1.10 + REC1.0 | OOS 2025-2026 | 24 | 54.2% | +4.7R | 1.42 | 2.3R |

**判定**: Strict が IS/OOS 共に PF 安定 → 採用。

### Synapse v1 IS/OOS

| サンプル | 通貨 | Trades | WR | Total R | PF |
|---|---|---|---|---|---|
| IS_2015_2024 | USDJPY | 8 | 75.0% | +6.5R | 7.07 |
| IS_2015_2024 | CHFJPY | 8 | 75.0% | +4.8R | 3.27 |
| IS_2015_2024 | GBPJPY | 11 | 63.6% | +4.1R | 2.00 |
| OOS_2025_2026 | (各通貨) | (少) | - | - | (要追加検証) |

---

## 5. 時間軸比較

### V字回復: H1 vs H4 (2015-2024)

| TF | Trades | WR | PF | Total R | DD | 採用 |
|---|---|---|---|---|---|---|
| H1 (VFIB_618_BODY60_LONG_RR2) | 1513 | 38.6% | 1.19 | +186.6R | 50.9R | ❌ DD大 |
| H4 (VFIB_618_BODY60_LONG_RR2) | 566 | 43.3% | 1.33 | +103.8R | 14.6R | ⚠️ |
| D1 (VFIB_618_BODY60_LONG_RR2) | 160 | 51.3% | 1.41 | +29.8R | 18.2R | (件数少) |
| **H4 + T5 + MACD + BB Strict** | **99** | **55.6%** | **2.55** | **+59.8R** | **6.7R** | ✅ **採用** |

→ **H4 + フィルタ厳格化** が品質最高。

### Sai H1 系 TF 比較

| TF | 全体 PF | 採用判定 |
|---|---|---|
| H1 | 1.05 | ❌ |
| H4 | (報告書参照) | ⚠️ V候補抽出に転換 |
| D1 | (報告書参照) | ⚠️ 件数少 |

詳細: [`backtests/sai_h1/timeframe_comparison_2015_2024/report_ja.md`](../backtests/sai_h1/timeframe_comparison_2015_2024/report_ja.md)

---

## 6. 研究系・補助検証

### 6-1. TrendBreakV1 ピラミディング検証

[`backtests/trendbreak_v1/pyramiding_sweep_2015_2024/report_ja.md`](../backtests/trendbreak_v1/pyramiding_sweep_2015_2024/report_ja.md)

- エントリー数 1〜5 でスイープ
- **エントリー数 1 (現状) が最適** → ピラミディングは効果なし
- 2エントリー以降は DD が指数的に増加

### 6-2. TrendBreakV1 騙し回避フィルタ研究

| ルール | Trades | WR | Total R | PF | DD |
|---|---|---|---|---|---|
| baseline | 461 | 36.9% | **+191.5R** | 1.62 | 18.0R |
| body60_filter | 377 | 38.2% | +176.3R | 1.72 | 11.7R |
| early_back_inside_1 | 461 | 33.0% | +181.7R | 1.69 | 11.7R |
| **body60_plus_early1** | 377 | 34.7% | +169.5R | **1.79** | **9.4R** |

**判定**: baseline 最強 (絶対R)、body60+early1 が PF/DD 最良。
**現状**: 騙し回避OFF (baseline) を採用。1%リスクなら baseline で問題ない。

### 6-3. TrendBreakV1 コスト監査

[`backtests/audit/`](../backtests/audit/)

- スプレッド + スリッページ込みで再評価
- 184R → **146R (-21%)**
- それでも PF 1.5 維持
- → **頑健性確認**

### 6-4. TrendBreakV1 緩和スタディ

[`backtests/relaxation/RELAXATION_REPORT.md`](../backtests/relaxation/RELAXATION_REPORT.md)

- 19パターンの緩和案を検証
- 通貨ごとに最適パラメータが違う
- **HYBRID 最適化案** で **頻度 +27%, R +23%**

### 6-5. 一般インジケータ否定後の相場反応 2026-05-29

| 検証 | パス | 結論 |
|---|---|---|
| 研究ノート | [`docs/research/indicator_denial_reaction_2026-05-29.md`](research/indicator_denial_reaction_2026-05-29.md) | D1の下方向シグナル否定後ロングが候補 |
| 検証結果 | [`backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/report_ja.md`](../backtests/elliott_fibo/results_2026_05_29/indicator_denial_reaction/report_ja.md) | H4直接逆張りは弱い。D1 Donchian20/RSI否定ロングが有望 |

- D1 Donchian20下抜け否定ロング: 368 trades / +63.29R / PF 1.32
- D1 RSI 70/30否定ロング: 163 trades / +40.81R / PF 1.50
- H4否定シグナル単独逆張りは不採用寄り
- 次はD1否定を環境認識にして、H4 V右肩優位・棚ブレイクと組み合わせる

---

## 7. インデックス系

### NAS100 / SPX500 検証 (2026-05-24)

| 検証 | パス | 結論 |
|---|---|---|
| TrendBreakV1 (NAS100) | [`backtests/trendbreak_v1/results_2026_05_24/nas100_reference/`](../backtests/trendbreak_v1/results_2026_05_24/nas100_reference/) | 拡張性検証 |
| TrendBreakV1 (SPX500) | [`backtests/trendbreak_v1/results_2026_05_24/spx500_reference/`](../backtests/trendbreak_v1/results_2026_05_24/spx500_reference/) | 拡張性検証 |
| T5 MACD BB (NAS100) | [`backtests/elliott_fibo/results_2026_05_24/nas100_us100_validation/report_ja.md`](../backtests/elliott_fibo/results_2026_05_24/nas100_us100_validation/report_ja.md) | 適用可能性確認 |
| T5 MACD BB (SPX500) | [`backtests/elliott_fibo/results_2026_05_24/spx500_validation/report_ja.md`](../backtests/elliott_fibo/results_2026_05_24/spx500_validation/report_ja.md) | 適用可能性確認 |

**判定**: 参考データ。本番運用するには追加検証必要。

---

## 8. アンチパターン (やったけどダメだった)

| #  | 試したこと | なぜダメだったか | 教訓 |
|---|---|---|---|
| A1 | Sai H1 全手法そのまま | 4手法混在で平均PF 1.05 | 弱い手法も全部混ぜると全体が薄まる |
| A2 | H4 急落V字 単独売買 | フィルタなしで PF 0.72 | V字だけでは方向確度不足 |
| A3 | TrendBreakV1 + ピラミディング (2-5) | DD が指数的に増加 | 1エントリーが正解 |
| A4 | エリオット5波目 (LOOSE版) | DD 34R / PF 1.23 | エリオット風はDD大 |
| A5 | V字フィボ単独 (フィルタ無し) | PF 1.07-1.30, DD 30-50R | V字単独はノイズ多 |
| A6 | Synapse v0 (エリオット H4) | -42R / PF 0.85 | 機械化が難しい |
| A7 | H1 短期V字 (REC1.0) | DD 9-12R, PF 1.81 | H4 の方が圧倒的に優秀 |
| A8 | 騙し回避フィルタ 3条件以上重ね | Trades 激減で実用厳しい | 過剰フィルタは益が出ない |
| A9 | AUDJPY 採用 | PF 0.97, DD 18R | この通貨では機能しない |
| A10 | 非フィボ系ツール (RSI/MA/VWAP) | MACD+BB 以下 | MACD+BB の組合せが正解 |

---

## 9. 関連ドキュメント

- 📘 [`STRATEGY_GUIDE.md`](../STRATEGY_GUIDE.md) — 戦略運用の説明書
- 📘 [`README.md`](../README.md) — リポジトリ入口
- 📘 [`docs/two_method_practical_research_2026-05-24.md`](two_method_practical_research_2026-05-24.md) — 公式総括
- 📘 [`docs/h4_t5_macd_bb_practical_audit_2026-05-24.md`](h4_t5_macd_bb_practical_audit_2026-05-24.md) — H4 T5 監査
- 📘 [`docs/h4_t5_macd_bb_live_ready_notes.md`](h4_t5_macd_bb_live_ready_notes.md) — H4 T5 運用ノート
- 📄 [`docs/FX検証研究ノート_2015-2024.docx`](FX検証研究ノート_2015-2024.docx) — Word版総合

---

## 10. 一覧の見方

### 「採用」マーク (✅ ⚠️ ❌) の基準

- ✅ **採用**: PF ≥ 1.5, DD ≤ 1/3 of Total R, OOS で再現確認済み
- ⚠️ **archive / 研究中**: 一定の成果はあるが現行版では使わない / 追加検証必要
- ❌ **不採用**: PF < 1.3 または DD > Total R/2 または OOS で崩れる

### よく使う指標の定義

| 用語 | 意味 |
|---|---|
| **R** | 1リスクあたりの損益 (1R = SL までの距離 = 口座1%相当) |
| **Total R** | 期間中の累計R (例: +100R = 100%リターン @ 1Rリスク) |
| **PF** | Profit Factor = 総利益R / 総損失R (1.0で損益分岐) |
| **WR** | 勝率 (%) |
| **Max DD R** | 累計R の peak-to-trough 最大ドローダウン (R単位) |
| **連敗** | 最大連続損失回数 |
| **IS** | In-Sample (検証期間) = 2015-2024 |
| **OOS** | Out-of-Sample (未使用期間) = 2025-2026 |

---

**最終更新**: 2026-05-24
**コミット履歴**: `git log --oneline` で確認可能

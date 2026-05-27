from __future__ import annotations

import csv
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "fx_ai_sheet_csv_20260524"
ZIP_PATH = ROOT / "outputs" / "fx_ai_sheet_csv_20260524.zip"


SHEETS: dict[str, list[list[object]]] = {
    "00_読み方.csv": [
        ["項目", "内容", "見る場所", "メモ"],
        ["更新日", "2026-05-24", "全体", "Google Sheetsを検証結果ダッシュボード形式に整理"],
        ["主力手法", "TrendBreakV1 HYBRID", "01_総合判定 / 03_通貨別", "AUDJPY除外の6通貨が現時点の推奨"],
        ["補助手法", "H4 T5 + MACD + BB", "01_総合判定 / 05_OOS", "V字は単独売買ではなく候補抽出。T5/MACD/BBで絞る"],
        ["本番候補", "TrendBreakV1 + T5 両方フル", "01_総合判定", "Total +219.94R / PF 1.86 / DD 11.94R"],
        ["見る順番", "1 総合判定 -> 2 通貨別 -> 3 OOS -> 4 見送り条件", "各タブ", "採用可否を先に見てから詳細へ"],
        ["注意", "NAS100/SPX500は参考検証", "01_総合判定 / 08_詳細研究", "専用最適化なし。SPX500は弱い"],
        ["注意", "Synapseは研究段階", "05_OOS / 06_見送り条件", "波形認識の機械化はまだ不安定"],
        ["単位", "R基準", "99_用語", "資金100万円・1R=1%なら +100R は概算+100万円相当"],
    ],
    "01_総合判定.csv": [
        ["No", "手法名", "期間", "TF", "通貨数", "Trades", "WR%", "PF", "Total_R", "Max_DD_R", "連敗", "判定", "コメント"],
        [1, "TrendBreakV1 HYBRID baseline", "2015-2024", "H1", 7, 461, 36.88, 1.62, 191.53, 14.02, 13, "採用(主力)", "fakeout filterなし"],
        ["1'", "TrendBreakV1 HYBRID AUDJPY除外", "2015-2024", "H1", 6, 381, 39.37, 1.79, 194.61, 11.94, 11, "採用", "推奨6通貨。AUDJPY除外でPF/DD改善"],
        [2, "H4 T5+MACD+BB 実戦用", "2015-2024", "H4", 7, 34, 61.76, 3.56, 29.20, 4.35, 5, "採用(補助)", "Strict 0.75-1.00 + REC1.2"],
        ["2'", "H4 T5+MACD+BB OOS", "2025-2026 OOS", "H4", 7, 15, 66.67, 2.44, 7.26, 2.02, 2, "OOS再現", "未使用データでも崩れにくいが件数は少ない"],
        [3, "TrendBreakV1 + T5 両方フル", "2015-2024", "H1+H4", 6, 411, 40.88, 1.86, 219.94, 11.94, 11, "本番候補", "TrendBreak主力 + T5補助の採用案"],
        [4, "Sai Best Method 急な揺り戻し", "2015-2024", "H1", 7, 378, 44.40, 1.47, 98.84, 13.21, 9, "archive", "v1では有望。現行主力からは外す"],
        [5, "Sai H1 全体 4手法込み", "2015-2024", "H1", 7, 1108, 41.60, 1.05, 99.91, 21.90, "?", "不採用", "弱い手法も混ざり期待値が薄い"],
        [6, "H4 急落V字 単独 strict", "2015-2024", "H4", 7, 39, 30.77, 0.72, -7.16, 13.20, 5, "単独NG", "V字は環境認識用。単独エントリー不可"],
        [7, "Synapse v0 エリオット風H4", "2015-2024", "H4", 7, 413, 31.96, 0.85, -42.41, 48.82, 19, "不採用", "機械化困難。DD大"],
        [8, "Synapse v1 H1", "2015-2024", "H1", 7, 81, 56.79, 1.42, 14.78, 5.39, 5, "研究中", "A_earlyモード有望だがOOS不足"],
        [9, "Elliott W5 RR3 LOOSE", "2015-2024", "H1", 7, 450, 30.00, 1.23, 73.33, 34.70, 17, "不採用", "DDが大きく本番向きではない"],
        [10, "VFIB_618_BODY60_LONG_RR2", "2015-2024", "H1", 7, 1513, 38.60, 1.19, 186.64, 50.87, 16, "不採用", "件数は多いが平均Rが薄くDD大"],
        [11, "TrendBreakV1 NAS100 reference", "2015-2026", "H1", 1, 201, 32.84, 1.29, 43.50, 20.66, 6, "参考", "専用最適化なし。OOS +3.43R/PF1.24"],
        [12, "TrendBreakV1 SPX500 reference", "2015-2026", "H1", 1, 80, 33.75, 1.12, 8.29, 14.37, 7, "参考弱い", "専用最適化なし。SPXは優位性薄い"],
        [13, "H4 T5+MACD+BB NAS100 reference", "2015-2026", "H4", 1, 11, 72.73, 3.96, 8.90, 2.01, 2, "参考", "件数少。OOS 1件は負け"],
        [14, "H4 T5+MACD+BB SPX500 reference", "2015-2026", "H4", 1, 5, 20.00, 0.38, -1.92, 1.52, 2, "不採用", "SPX500はT5と相性悪い"],
        [15, "TrendBreakV1 Pyramiding sweep", "2015-2024", "H1", 7, "各種", "-", "-", "-", "-", "-", "研究", "1エントリーが最適"],
        [16, "TrendBreakV1 騙し回避フィルタ", "2015-2024", "H1", 7, "各種", "-", "-", "-", "-", "-", "研究", "body60+early1はPF/DD改善。ただし総R低下"],
    ],
    "02_検証一覧.csv": [
        ["カテゴリ", "検証名", "パス", "概要", "結論"],
        ["TrendBreakV1", "HYBRID 標準", "backtests/trendbreak_v1/results_2015_2024/", "4モード×7通貨×10年", "conservative が最安定 +184R"],
        ["TrendBreakV1", "緩和スタディ", "backtests/relaxation/RELAXATION_REPORT.md", "19パターン緩和案", "HYBRID最適化で頻度+27%, R+23%"],
        ["TrendBreakV1", "コスト監査", "backtests/audit/", "スプレッド/滑り込み", "-21%でも+146R維持"],
        ["TrendBreakV1", "fakeout 前後比較", "backtests/trendbreak_v1/fakeout_before_after_2015_2024/", "騙し回避4ルール", "baseline最強, body60+early1でPF最大"],
        ["TrendBreakV1", "fakeout feature 詳細", "backtests/trendbreak_v1/fakeout_feature_study_2015_2024/", "1000+ ルール組合せ", "単独フィルタは限定的"],
        ["TrendBreakV1", "fakeout rule matrix", "backtests/trendbreak_v1/fakeout_rule_matrix_2015_2024/", "フィルタ組合せ行列", "3条件以上重ねるとTrades激減"],
        ["TrendBreakV1", "Pyramiding スイープ", "backtests/trendbreak_v1/pyramiding_sweep_2015_2024/", "エントリー数1-5", "エントリー数1が最適"],
        ["TrendBreakV1", "2026-05-24 最新検証", "backtests/trendbreak_v1/results_2026_05_24/", "NAS100/SPX500参考", "FX以外でも機能可能性"],
        ["H4 T5 MACD BB", "V字回復+T5 検証(本命)", "backtests/elliott_fibo/results_2015_2024/t5_macd_bb_vshape_validation/", "全プリセット網羅", "Strict 0.75-1.00+REC1.2 最良"],
        ["H4 T5 MACD BB", "MACD+BB Harsh 検証", "backtests/elliott_fibo/results_2015_2024/t5_macd_bb_harsh_validation/", "厳しめフィルタ群", "Strict 確認"],
        ["H4 T5 MACD BB", "OOS 2025-2026", "backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb/", "未使用期間", "+7.3R/PF2.44/再現性◯"],
        ["H4 T5 MACD BB", "OOS Vshape版", "backtests/elliott_fibo/results_2025_2026_oos/t5_macd_bb_vshape/", "OOS V字版", "OOS再現確認"],
        ["H4 T5 MACD BB", "回復比率スイープ", "backtests/elliott_fibo/results_2025_2026_oos/t5_recovery_ratio_sweep/", "0.80-2.00 全比率", "1.20-1.22 が黄金"],
        ["H4 T5 MACD BB", "失敗フィルタ検証", "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/", "失敗時特徴抽出", "BB高/MACD弱/時間経過が原因"],
        ["H4 T5 MACD BB", "実用ロバスト監査", "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/", "LOO+閾値感度", "BB幅<=4ATR が最重要"],
        ["H4 T5 MACD BB", "運用堅牢化", "backtests/elliott_fibo/results_2026_05_24/t5_operational_hardening/", "本番運用想定", "live ready 確認"],
        ["H4 T5 MACD BB", "トリガー研究", "backtests/elliott_fibo/results_2015_2024/v_recovery_trigger/", "stagnation/rebreak/両方", "stagnation+rebreakが最強WR75%"],
        ["H4 T5 MACD BB", "緩和ラダー", "backtests/elliott_fibo/results_2015_2024/v_recovery_relaxation_ladder/", "条件緩和の段階検証", "緩めすぎは赤字"],
        ["H4 T5 MACD BB", "H1/H4 比較", "backtests/elliott_fibo/results_2015_2024/v_recovery_h1_h4_compare/", "TF比較", "H4 が圧倒的に優位"],
        ["H4 T5 MACD BB", "非フィボ系ツール", "backtests/elliott_fibo/results_2015_2024/v_recovery_non_fibo_tools/", "RSI/MA/VWAPなど", "MACD+BBに勝るものなし"],
        ["H4 T5 MACD BB", "vshape quant filters", "backtests/elliott_fibo/results_2015_2024/vshape_quant/", "定量フィルタ探索", "recovery比率1.20が黄金"],
        ["H4 T5 MACD BB", "indicator robust search", "backtests/elliott_fibo/results_2015_2024/t5_indicator_robust_search/", "各種指標組合せ", "MACD+BB 確定"],
        ["H4 T5 MACD BB", "indicator compatibility", "backtests/elliott_fibo/results_2015_2024/indicator_compatibility_search/", "指標相性", "BB幅+MACDが最相性"],
        ["H4 T5 MACD BB", "indicator deep validation", "backtests/elliott_fibo/results_2015_2024/indicator_deep_validation/", "深掘り検証", "フィルタ強度最終調整"],
        ["H4 T5 MACD BB", "t5 skeptic audit", "backtests/elliott_fibo/results_2015_2024/t5_skeptic_audit/", "監査", "データ漏洩なし確認"],
        ["アンサンブル", "TB+T5 採用案検証", "backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/", "両方フル運用案", "+219.9R/PF1.86"],
        ["アンサンブル", "TB+H4 V字 単独検証", "backtests/ensemble/trendbreak_h4_v_combo_2015_2024/", "V字単独追加", "改善せず"],
        ["アンサンブル", "TB+Sai Best (v1)", "backtests/ensemble/ensemble_report.md", "旧採用案", "Calmar 17 (v1版)"],
        ["アンサンブル", "通貨フィルタ比較", "backtests/ensemble/portfolio_comparison.md", "TOP3/5/全 比較", "v1: TOP5でCalmar20.8"],
        ["Sai H1 系", "Sai H1 全体", "backtests/sai_h1/results_2015_2024/", "4手法 (停滞・V字・急揺戻し・レンジ2回目)", "全体PF1.05弱い"],
        ["Sai H1 系", "Best Method 深堀り", "backtests/sai_h1/deep_dive_best_method/", "急な揺り戻し+高値停滞", "PF1.47/+98.8R"],
        ["Sai H1 系", "TF 比較", "backtests/sai_h1/timeframe_comparison_2015_2024/", "H1/H4/D1", "H4/D1 が有望→V字研究へ"],
        ["Sai H1 系", "XAUUSD 単独テスト", "backtests/sai_h1/test_xau/", "アセット分析", "参考"],
        ["急落V字 単独", "Strict V字回復", "backtests/elliott_fibo/results_2015_2024/strict_v_recovery/", "完全回復・速度重視", "単独 -7R 不可"],
        ["Elliott V字フィボ", "全体 (数百パターン)", "backtests/elliott_fibo/results_2015_2024/", "網羅検証", "PF<1.3 / DD大"],
        ["Synapse", "Synapse v0 H4", "backtests/synapse_v0/results_2026_05_24/", "エリオット風 H4 全通貨", "-42R 不採用"],
        ["Synapse", "Synapse v1 H1", "backtests/synapse_v1/results_2026_05_24/", "改善版 H1 全通貨", "+14.8R/PF1.42"],
        ["Synapse", "Synapse v1 USDJPY M1", "backtests/synapse_v1/results_usdjpy_m1_timeframes_2026_05_24/", "M1時間軸", "短期PF低下"],
        ["インデックス", "TrendBreakV1 NAS100", "backtests/trendbreak_v1/results_2026_05_24/nas100_reference/", "拡張性検証", "参考"],
        ["インデックス", "TrendBreakV1 SPX500", "backtests/trendbreak_v1/results_2026_05_24/spx500_reference/", "拡張性検証", "参考"],
        ["インデックス", "T5 NAS100/US100", "backtests/elliott_fibo/results_2026_05_24/nas100_us100_validation/", "適用可能性", "確認"],
        ["インデックス", "T5 SPX500", "backtests/elliott_fibo/results_2026_05_24/spx500_validation/", "適用可能性", "確認"],
        ["比較", "戦略間比較", "backtests/comparison/", "TrendBreakV1 vs Sai", "TB圧勝 +551R vs +99R (4モード合計)"],
    ],
    "03_通貨別.csv": [
        ["通貨", "TB単独_Trades", "TB単独_WR", "TB単独_PF", "TB単独_Total_R", "TB単独_DD", "T5実戦_Trades", "T5実戦_WR", "T5実戦_PF", "T5実戦_Total_R", "T5実戦_DD", "両方フル_Trades", "両方フル_WR", "両方フル_PF", "両方フル_Total_R", "両方フル_DD", "採用判定"],
        ["XAUUSD", 75, 44.00, 2.21, 53.20, 6.19, 7, 71.43, 7.71, 8.64, 1.01, 79, 45.57, 2.29, 58.15, 6.19, "採用 エース"],
        ["USDJPY", 64, 37.50, 1.72, 29.91, 9.37, 8, 62.50, 4.89, 7.92, 1.01, 68, 38.24, 1.74, 31.88, 9.37, "採用"],
        ["EURJPY", 55, 30.91, 1.29, 11.42, 9.39, 2, 50.00, 1.96, 0.97, 0.00, 57, 31.58, 1.31, 12.39, 7.41, "採用 弱め"],
        ["GBPJPY", 59, 42.37, 2.11, 39.11, 6.16, 10, 60.00, 2.60, 6.47, 2.02, 64, 42.19, 2.05, 40.08, 6.16, "採用"],
        ["CHFJPY", 64, 35.94, 1.56, 24.35, 9.37, 5, 80.00, 7.90, 6.93, 1.00, 67, 37.31, 1.62, 27.29, 9.37, "採用"],
        ["SILVER", 64, 43.75, 1.86, 36.62, 6.41, 3, 66.67, 2.06, 1.12, 0.00, 64, 43.75, 1.87, 36.62, 6.41, "採用"],
        ["AUDJPY", 80, 25.00, 0.95, -3.08, 17.95, 4, 75.00, 4.83, 3.86, 0.00, 82, 25.61, 0.97, -2.09, 17.95, "除外"],
        ["NAS100", 201, 32.84, 1.29, 43.50, 20.66, 11, 72.73, 3.96, 8.90, 2.01, "-", "-", "-", "-", "-", "参考。TBは可能性あり/T5は件数不足"],
        ["SPX500", 80, 33.75, 1.12, 8.29, 14.37, 5, 20.00, 0.38, -1.92, 1.52, "-", "-", "-", "-", "-", "参考弱い。T5は不採用"],
    ],
    "04_年別_TB.csv": [
        ["年", "Trades", "WR%", "PF", "Total_R", "DD_R", "連敗", "コメント"],
        [2015, 34, 35.29, 1.49, 11.44, 5.38, 5, "中庸"],
        [2016, 44, 34.09, 1.45, 13.70, 8.21, 6, "中庸"],
        [2017, 43, 34.88, 1.49, 14.38, 7.68, 7, "中庸"],
        [2018, 55, 32.73, 1.34, 13.42, 14.02, 13, "苦戦年 低ボラ環境"],
        [2019, 53, 49.06, 2.58, 46.01, 4.44, 4, "大当たり トレンド相場"],
        [2020, 52, 36.54, 1.62, 21.35, 10.41, 10, "中庸"],
        [2021, 46, 39.13, 1.79, 23.39, 5.69, 4, "中庸"],
        [2022, 44, 40.91, 1.95, 25.97, 4.28, 4, "大当たり 利上げ局面"],
        [2023, 46, 32.61, 1.38, 12.09, 9.37, 9, "中庸"],
        [2024, 44, 31.82, 1.31, 9.78, 7.47, 7, "中庸"],
    ],
    "05_OOS.csv": [
        ["手法", "プリセット", "期間", "Trades", "WR%", "PF", "Total_R", "DD_R", "連敗"],
        ["H4 T5 MACD BB", "Strict 0.75-1.00 + REC1.2", "IS 2015-2024", 99, 55.60, 2.55, 59.80, 6.70, 6],
        ["H4 T5 MACD BB", "Strict 0.75-1.00 + REC1.2", "OOS 2025-2026", 15, 66.70, 2.44, 7.30, 2.00, 2],
        ["H4 T5 MACD BB", "Robust 0.75-1.05 + REC1.5", "IS 2015-2024", 129, 52.70, 2.17, 64.50, 8.80, 10],
        ["H4 T5 MACD BB", "Robust 0.75-1.05 + REC1.5", "OOS 2025-2026", 21, 61.90, 2.27, 9.20, 2.00, 2],
        ["H4 T5 MACD BB", "Current 0.60-1.10 + REC1.0", "IS 2015-2024", 142, 50.70, 1.81, 53.90, 9.80, 9],
        ["H4 T5 MACD BB", "Current 0.60-1.10 + REC1.0", "OOS 2025-2026", 24, 54.20, 1.42, 4.70, 2.30, 2],
        ["Synapse v1", "USDJPY", "IS 2015-2024", 8, 75.00, 7.07, 6.50, 1.02, 1],
        ["Synapse v1", "CHFJPY", "IS 2015-2024", 8, 75.00, 3.27, 4.80, 2.10, 2],
        ["Synapse v1", "GBPJPY", "IS 2015-2024", 11, 63.60, 2.00, 4.10, 3.08, 3],
    ],
    "06_見送り条件.csv": [
        ["No", "試したこと", "なぜダメだったか", "教訓"],
        ["A1", "Sai H1 全手法そのまま", "4手法混在で平均PF 1.05", "弱い手法も全部混ぜると全体が薄まる"],
        ["A2", "H4 急落V字 単独売買", "フィルタなしで PF 0.72", "V字だけでは方向確度不足"],
        ["A3", "TrendBreakV1 + ピラミディング 2-5", "DD が指数的に増加", "1エントリーが正解"],
        ["A4", "エリオット5波目 LOOSE版", "DD 34R / PF 1.23", "エリオット風はDD大"],
        ["A5", "V字フィボ単独 フィルタ無し", "PF 1.07-1.30 / DD 30-50R", "V字単独はノイズ多"],
        ["A6", "Synapse v0 エリオット H4 機械化", "-42R / PF 0.85", "機械化が難しい"],
        ["A7", "H1 短期V字 REC1.0", "DD 9-12R / PF 1.81", "H4 の方が圧倒的に優秀"],
        ["A8", "騙し回避フィルタ 3条件以上重ね", "Trades 激減で実用厳しい", "過剰フィルタは益が出ない"],
        ["A9", "AUDJPY 採用", "PF 0.97 / DD 18R", "この通貨では機能しない"],
        ["A10", "非フィボ系ツール RSI/MA/VWAP", "MACD+BB 以下", "MACD+BB の組合せが正解"],
    ],
    "07_TF比較.csv": [
        ["TF", "戦略", "Trades", "WR%", "PF", "Total_R", "DD_R", "採用判定"],
        ["H1", "VFIB_618_BODY60_LONG_RR2", 1513, 38.60, 1.19, 186.64, 50.87, "DD大"],
        ["H4", "VFIB_618_BODY60_LONG_RR2", 566, 43.29, 1.33, 103.78, 14.62, "研究"],
        ["D1", "VFIB_618_BODY60_LONG_RR2", 160, 51.25, 1.41, 29.77, 18.15, "件数少"],
        ["H4", "T5 + MACD + BB Strict 採用", 99, 55.56, 2.55, 59.76, 6.67, "採用"],
        ["H4", "T5 + MACD + BB 実戦用", 39, 66.67, 4.14, 35.90, 4.35, "採用 絞り版"],
        ["H4", "T5 + MACD + BB 超厳選", 17, 82.35, 12.09, 22.56, 1.01, "件数少すぎ"],
    ],
    "08_詳細研究.csv": [
        ["カテゴリ", "ルール / 設定", "Trades", "WR%", "PF", "Total_R", "DD_R", "コメント"],
        ["Fakeout", "baseline", 461, 36.88, 1.62, 191.53, 17.95, "現状採用 / 総R最大"],
        ["Fakeout", "body60_filter", 377, 38.20, 1.72, 176.27, 11.70, "WR↑ DD↓"],
        ["Fakeout", "early_back_inside_1", 461, 32.97, 1.69, 181.72, 11.67, "early exit"],
        ["Fakeout", "body60_plus_early1", 377, 34.75, 1.79, 169.50, 9.39, "PF最大 / DD最小"],
        ["Pyramiding", "entries=1 現状", "-", "-", "-", "-", "-", "最適 / 推奨"],
        ["Pyramiding", "entries=2", "-", "-", "-", "-", "-", "DD増加"],
        ["Pyramiding", "entries=3+", "-", "-", "-", "-", "-", "DD指数増"],
        ["Cost", "コストなし", "-", "-", "-", 184.00, "-", "audit前"],
        ["Cost", "スプレッド+滑り込み", "-", "-", "-", 146.00, "-", "-21%でも維持"],
        ["Relaxation", "HYBRID最適化", "-", "-", "-", "+23%", "-", "頻度+27%"],
        ["Index", "TrendBreak NAS100 pine fallback", 201, 32.84, 1.29, 43.50, 20.66, "参考。OOS +3.43R"],
        ["Index", "TrendBreak SPX500 index any", 80, 33.75, 1.12, 8.29, 14.37, "参考弱い"],
        ["Index", "T5 NAS100 weighted", 11, 72.73, 3.96, 8.90, 2.01, "件数少 / OOS負け1件"],
        ["Index", "T5 SPX500 weighted", 5, 20.00, 0.38, -1.92, 1.52, "不採用"],
    ],
    "99_用語.csv": [
        ["用語", "意味"],
        ["R", "1リスクあたりの損益。1R = SLまでの距離 = 口座1%相当など"],
        ["Total R", "期間中の累計R。例 +100R = 1Rリスクなら約+100%"],
        ["PF", "Profit Factor = 総利益R / 総損失R。1.0で損益分岐"],
        ["WR", "勝率"],
        ["Max DD R", "累計Rのpeak-to-trough最大ドローダウン"],
        ["連敗", "最大連続損失回数"],
        ["IS", "In-Sample。主に2015-2024の検証期間"],
        ["OOS", "Out-of-Sample。未使用データ。主に2025-2026"],
        ["TF", "Time Frame。時間軸"],
        ["RR", "Risk Reward。TP距離 / SL距離"],
        ["Calmar", "Total R / Max DD R。リスク調整後リターン"],
        ["HYBRID", "TrendBreakV1の通貨別最適化パラメータ集"],
        ["REC1.2", "V字回復速度。下落本数の1.20倍以内に61.8-80%回復"],
        ["BB位置", "現在価格のBB内位置。0=下バンド 0.5=中央 1=上バンド"],
        ["T5", "V候補 + stagnation/rebreak の総称トリガー"],
        ["TrendBreakV1", "過去lookback高安値更新 + no-touch 条件のブレイクアウト手法"],
        ["H4 T5", "急落後V候補を環境認識に使い MACD/BB/stagnation/rebreakで絞るH4補助手法"],
        ["採用", "現時点で本番候補"],
        ["研究", "有望だがOOSや件数不足"],
        ["不採用", "PF/DD/件数/再現性のどこかで不合格"],
    ],
}


def write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in SHEETS.items():
        write_csv(OUT_DIR / name, rows)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in SHEETS:
            zf.write(OUT_DIR / name, arcname=name)

    print(f"created: {OUT_DIR}")
    print(f"created: {ZIP_PATH}")
    for name in SHEETS:
        print(name)


if __name__ == "__main__":
    main()

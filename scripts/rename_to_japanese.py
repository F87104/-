#!/usr/bin/env python3
"""
Rename English-named markdown files to Japanese names and update all internal links.
"""

import os
import subprocess
import re

# Mapping: (directory, old_name) -> new_name
RENAME_MAP = {
    # Top-level
    ("", "STRATEGY_GUIDE.md"): "戦略ガイド.md",
    ("", "sai_method_automation_spec_v0_2.md"): "SAI手法自動化仕様_v0_2.md",

    # docs/
    ("docs", "BACKTEST_INDEX.md"): "バックテスト一覧.md",
    ("docs", "h4_t5_macd_bb_live_ready_notes.md"): "H4_T5_本番運用ノート.md",
    ("docs", "h4_t5_macd_bb_practical_audit_2026-05-24.md"): "H4_T5_MACD_BB_実用監査_2026-05-24.md",
    ("docs", "two_method_practical_research_2026-05-24.md"): "2本柱実用研究_2026-05-24.md",

    # docs/research/
    ("docs/research", "RESEARCH_INDEX.md"): "研究インデックス.md",
    ("docs/research", "RESEARCH_NOTE_TEMPLATE.md"): "研究ノートテンプレート.md",
    ("docs/research", "chfjpy_countertrend_hypothesis_2026-05-27.md"): "CHFJPY逆張り仮説_2026-05-27.md",
    ("docs/research", "chfjpy_exit_relative_heat_2026-05-27.md"): "CHFJPY出口相対熱量_2026-05-27.md",
    ("docs/research", "chfjpy_rank_timing_breakdown_2026-05-27.md"): "CHFJPYランク_タイミング分解_2026-05-27.md",
    ("docs/research", "chfjpy_stretch_deep_dive_2026-05-27.md"): "CHFJPY伸長深掘り_2026-05-27.md",
    ("docs/research", "clean_h4_v_reclaim_pine_note_2026-05-29.md"): "H4_V回収Pine整理版_2026-05-29.md",
    ("docs/research", "currency_pair_personality_hypothesis_2026-05-31.md"): "通貨ペア性格仮説_2026-05-31.md",
    ("docs/research", "d1_bear_trap_h4_v_reclaim_2026-05-29.md"): "D1弱気トラップ_H4_V回収_2026-05-29.md",
    ("docs/research", "d1_trap_h4_shelf_strict_2026-05-30.md"): "D1トラップ_H4棚厳選_2026-05-30.md",
    ("docs/research", "future_trade_psychology_research_themes_2026-05-31.md"): "トレード心理研究の将来テーマ_2026-05-31.md",
    ("docs/research", "h4_double_v_reclaim_2026-06-02.md"): "H4ダブルV回収_初動V_2026-06-02.md",
    ("docs/research", "h4_low_stag_d1_regime_pine_note_2026-05-29.md"): "H4低位停滞_D1レジームPine注記_2026-05-29.md",
    ("docs/research", "h4_low_stag_pine_parity_audit_2026-05-29.md"): "H4低位停滞Pine同等性監査_2026-05-29.md",
    ("docs/research", "h4_right_shoulder_v_reclaim_practical_2026-06-02.md"): "H4右肩V回収実用_2026-06-02.md",
    ("docs/research", "h4_sharp_v_visual_application_2026-05-29.md"): "H4急落V可視化応用_2026-05-29.md",
    ("docs/research", "h4_v_denial_reacceleration_2026-06-05.md"): "H4_V否定_再加速_2026-06-05.md",
    ("docs/research", "h4_v_kickoff_catalyst_2026-05-30.md"): "H4_Vキックオフ触媒_2026-05-30.md",
    ("docs/research", "h4_v_recovery_strategy_candidates_2026-05-30.md"): "H4_V字回復戦略候補_2026-05-30.md",
    ("docs/research", "h4_v_right_shoulder_strength_2026-05-29.md"): "H4_V字右肩強度_2026-05-29.md",
    ("docs/research", "h4_v_shelf_breakout_method_2026-05-29.md"): "H4_V字棚ブレイクアウト手法_2026-05-29.md",
    ("docs/research", "indicator_denial_reaction_2026-05-29.md"): "指標否定反応_2026-05-29.md",
    ("docs/research", "market_psychology_pattern_library_2026-05-30.md"): "市場心理パターンライブラリ_2026-05-30.md",
    ("docs/research", "market_psychology_squeeze_currency_compatibility_2026-05-30.md"): "市場心理スクイーズ通貨別相性_2026-05-30.md",
    ("docs/research", "market_psychology_squeeze_strict_2026-05-30.md"): "市場心理スクイーズ厳選_2026-05-30.md",
    ("docs/research", "original_wavebox_rebreak_v0_1.md"): "オリジナルウェーブボックス再ブレイク_v0_1.md",
    ("docs/research", "pine_parity_issue_h4_low_stag_short_2026-05-29.md"): "Pine同等性問題_H4低位停滞ショート_2026-05-29.md",
    ("docs/research", "realtime_trade_psychology_log_template.md"): "リアルタイムトレード心理ログテンプレート.md",
    ("docs/research", "sequential_countertrend_research_2026-05-27.md"): "順次逆張り研究_2026-05-27.md",
    ("docs/research", "short_covering_psychology_flow_2026-06-03.md"): "ショートカバリング心理フロー_2026-06-03.md",
    ("docs/research", "short_side_research_2026-05-28_in_progress.md"): "ショート側研究_進行中_2026-05-28.md",
    ("docs/research", "silver_xagusd_h1_m15_execution_rules_v0_1.md"): "シルバーXAGUSD_H1_M15執行ルール_v0_1.md",
    ("docs/research", "student_entries_extracted.md"): "受講生エントリー抽出済み.md",
    ("docs/research", "student_entry_cluster_research_2026-05-31.md"): "受講生エントリー集中パターン研究_2026-05-31.md",
    ("docs/research", "student_stumble_clusters_research_2026-05-31.md"): "受講生つまずきクラスタ研究_2026-05-31.md",
    ("docs/research", "stumble_chase_suppression_filter_v0_1.md"): "つまずき追いかけ抑制フィルタ_v0_1.md",
    ("docs/research", "synapse_method_definition_v0_1.md"): "Synapse手法定義_v0_1.md",
    ("docs/research", "tb_t5_ensemble_audit_2026-06-02.md"): "TrendBreak_T5アンサンブル監査_2026-06-02.md",
    ("docs/research", "trade_practice_diary.md"): "トレード実践日誌メモ.md",
    ("docs/research", "trade_psychology_failure_patterns_to_pine_2026-05-31.md"): "トレード心理失敗パターンPine化_2026-05-31.md",
    ("docs/research", "trade_psychology_optimal_entry_pattern_research_2026-05-31.md"): "トレード心理最適エントリーパターン研究_2026-05-31.md",
    ("docs/research", "trap_false_break_reaction_2026-05-30.md"): "トラップ_フォールスブレイク反応_2026-05-30.md",
    ("docs/research", "wavebox_forward_validation_protocol.md"): "ウェーブボックスフォワード検証プロトコル.md",
    ("docs/research", "wavebox_operational_preconditions_v1.md"): "ウェーブボックス運用前提条件_v1.md",
    ("docs/research", "wavebox_pine_static_audit_2026-05-26.md"): "ウェーブボックスPine静的監査_2026-05-26.md",
    ("docs/research", "wavebox_pine_v1_2_completion_note.md"): "ウェーブボックスPine_v1_2完成ノート.md",
    ("docs/research", "wavebox_red_team_audit_2026-05-26.md"): "ウェーブボックスレッドチーム監査_2026-05-26.md",
    ("docs/research", "wavebox_usdjpy_h1_rebreak_v1_practical.md"): "ウェーブボックスUSDJPY_H1再ブレイク_v1実用.md",

    # docs/trade_diary/
    ("docs/trade_diary", "slack_reflection_setup.md"): "Slack反省点設定.md",

    # docs/trade_diary/practice/entries/
    ("docs/trade_diary/practice/entries", "2026-06-01_usdjpy_h4t5_signal_buy.md"): "2026-06-01_USDJPY_H4T5シグナル買い.md",
    ("docs/trade_diary/practice/entries", "2026-06-03_xauusd_h1_alert_buy.md"): "2026-06-03_XAUUSD_H1アラート買い.md",
    ("docs/trade_diary/practice/entries", "2026-06-04_gbpjpy_nagekiri_signal_buy.md"): "2026-06-04_GBPJPY_投げ切りシグナル買い.md",
    ("docs/trade_diary/practice/entries", "2026-06-04_xauusd_v1_short_signal.md"): "2026-06-04_XAUUSD_V1ショートシグナル.md",
    ("docs/trade_diary/practice/entries", "2026-06-09_chfjpy_v21_sqz_signal_buy.md"): "2026-06-09_CHFJPY_v2_1_SQZシグナル買い.md",
    ("docs/trade_diary/practice/entries", "2026-06-10_xauusd_offstrategy_short.md"): "2026-06-10_XAUUSD_手法外ショート.md",
}

def build_flat_map():
    """Build a flat map of old_filename -> new_filename for link replacement."""
    flat = {}
    for (dirpath, old_name), new_name in RENAME_MAP.items():
        flat[old_name] = new_name
    return flat

def git_mv(src, dst):
    result = subprocess.run(["git", "mv", src, dst], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return False
    return True

def rename_files(root):
    print("=== Step 1: Renaming files with git mv ===")
    for (dirpath, old_name), new_name in RENAME_MAP.items():
        if dirpath:
            old_path = os.path.join(root, dirpath, old_name)
            new_path = os.path.join(root, dirpath, new_name)
        else:
            old_path = os.path.join(root, old_name)
            new_path = os.path.join(root, new_name)

        if not os.path.exists(old_path):
            print(f"  SKIP (not found): {old_path}")
            continue

        print(f"  {old_name} -> {new_name}")
        git_mv(old_path, new_path)

def update_links_in_file(filepath, flat_map):
    """Replace all occurrences of old filenames with new filenames in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False

    original = content
    for old_name, new_name in flat_map.items():
        # Replace in markdown links: [text](path/old_name) or just old_name in paths
        # Use word boundary-like approach: replace the filename portion
        content = content.replace(old_name, new_name)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def update_all_links(root, flat_map):
    print("\n=== Step 2: Updating internal links in all Markdown files ===")
    updated = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden dirs and node_modules etc
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != 'node_modules']
        for fname in filenames:
            if fname.endswith('.md') or fname.endswith('.csv') or fname.endswith('.tsv'):
                fpath = os.path.join(dirpath, fname)
                if update_links_in_file(fpath, flat_map):
                    rel = os.path.relpath(fpath, root)
                    updated.append(rel)
                    print(f"  Updated links in: {rel}")
    return updated

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Repository root: {root}")

    flat_map = build_flat_map()

    rename_files(root)
    updated = update_all_links(root, flat_map)

    print(f"\nDone. Updated links in {len(updated)} files.")

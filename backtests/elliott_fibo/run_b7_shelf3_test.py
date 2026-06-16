#!/usr/bin/env python3
"""棚7本 vs 棚3本 の全銘柄比較"""
from __future__ import annotations
import sys, math
from pathlib import Path
import numpy as np, pandas as pd

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from run_b7_shelf_tv import add_features, find_v_shocks, stats
from run_b7_all_symbols_sweep import sweep_symbol, SYMBOLS

REPO_ROOT = THIS_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "backtests" / "synapse_v2_definition_grid"))
import importlib.util
_s = importlib.util.spec_from_file_location("synapse_tv",
    REPO_ROOT / "backtests" / "synapse_v2_definition_grid" / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_s)
sys.modules["synapse_tv"] = tv
_s.loader.exec_module(tv)

BEST_7 = {
    "USDJPY": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 3.5, "rr": 2.0},
    "EURJPY": {"shelf_bars": 5, "shelf_atr": 2.0, "drop_atr_min": 3.0, "rr": 2.5},
    "GBPJPY": {"shelf_bars": 7, "shelf_atr": 1.5, "drop_atr_min": 3.5, "rr": 2.5},
    "CHFJPY": {"shelf_bars": 7, "shelf_atr": 2.5, "drop_atr_min": 2.8, "rr": 2.5},
    "XAGUSD": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 3.5, "rr": 1.5},
    "NAS100": {"shelf_bars": 7, "shelf_atr": 1.5, "drop_atr_min": 2.8, "rr": 2.5},
    "XAUUSD": {"shelf_bars": 3, "shelf_atr": 2.0, "drop_atr_min": 4.0, "rr": 2.0},
}

BASE = {
    "shelf_hold": 0.4, "rec_min": 0.65, "rec_max": 1.25,
    "break_buf": 0.05, "min_body": 0.30, "min_cloc": 0.50,
    "stop_buf": 0.25, "max_risk_atr": 2.5,
}

def main():
    files = sorted((REPO_ROOT / "tv_data").glob("*.csv"))
    data = {}
    for p in files:
        sym = tv.detect_symbol(p)
        if sym in SYMBOLS:
            raw = tv.load_tv_csv(p)
            if len(raw) >= 500:
                data[sym] = add_features(raw)

    print(f"{'銘柄':<8} | {'--- 現在の最適(棚7or5) ---':^30} | {'--- 棚3本に変更 ---':^30} | {'--- 棚3+最適RR/急落/棚幅 ---':^30}")
    print(f"{'':8} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7} {'RR':>4} {'急落':>5} {'棚幅':>5}")
    print("-" * 120)

    for sym in SYMBOLS:
        if sym not in data:
            continue
        h4 = data[sym]
        best7 = BEST_7[sym]

        # 現在の最適
        p_cur = {**BASE, **best7}
        tr_cur = sweep_symbol(h4, sym, p_cur)
        s_cur = stats(pd.Series(tr_cur))

        # 棚3に変更（他はそのまま）
        p_3 = {**BASE, **best7, "shelf_bars": 3}
        tr_3 = sweep_symbol(h4, sym, p_3)
        s_3 = stats(pd.Series(tr_3))

        # 棚3で急落/棚幅/RRを再最適化
        best_pf = 0
        best_combo = {}
        best_s = {}
        for da in [2.0, 2.5, 2.8, 3.0, 3.5, 4.0, 4.5]:
            for sa in [1.2, 1.5, 1.8, 2.0, 2.5, 3.0]:
                for r in [1.5, 2.0, 2.5, 3.0]:
                    p = {**BASE, "shelf_bars": 3, "shelf_atr": sa, "drop_atr_min": da, "rr": r}
                    tr = sweep_symbol(h4, sym, p)
                    s = stats(pd.Series(tr))
                    if s["trades"] >= 5 and s["pf"] > best_pf:
                        best_pf = s["pf"]
                        best_combo = {"rr": r, "drop_atr_min": da, "shelf_atr": sa}
                        best_s = s

        print(f"{sym:<8} | {s_cur['trades']:4} {s_cur['win_rate']:5.1f}% {s_cur['pf']:6.2f} {s_cur['total_r']:7.2f} | "
              f"{s_3['trades']:4} {s_3['win_rate']:5.1f}% {s_3['pf']:6.2f} {s_3['total_r']:7.2f} | "
              f"{best_s.get('trades',0):4} {best_s.get('win_rate',0):5.1f}% {best_s.get('pf',0):6.2f} {best_s.get('total_r',0):7.2f} "
              f"{best_combo.get('rr',0):4.1f} {best_combo.get('drop_atr_min',0):5.1f} {best_combo.get('shelf_atr',0):5.1f}")

if __name__ == "__main__":
    main()

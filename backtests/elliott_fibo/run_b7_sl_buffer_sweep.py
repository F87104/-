#!/usr/bin/env python3
"""
B7棚 SL余白(stopBuf)の細かいスイープ — 全銘柄

SL余白を0.05刻みで0.05〜1.00まで検証し、銘柄ごとの最適値を特定。
"""
from __future__ import annotations
import sys, math
from pathlib import Path
import numpy as np, pandas as pd

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from run_b7_shelf_tv import add_features, find_v_shocks, stats

REPO_ROOT = THIS_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "backtests" / "synapse_v2_definition_grid"))
import importlib.util
_s = importlib.util.spec_from_file_location("synapse_tv",
    REPO_ROOT / "backtests" / "synapse_v2_definition_grid" / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_s)
sys.modules["synapse_tv"] = tv
_s.loader.exec_module(tv)

RUN_START = pd.Timestamp("2015-01-01")
SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "XAGUSD", "NAS100", "XAUUSD"]

ENTRY_PARAMS = {
    "USDJPY": {"shelf_bars": 5, "shelf_atr": 1.8, "drop_atr_min": 3.5, "rr": 2.0, "max_hold": 60},
    "EURJPY": {"shelf_bars": 5, "shelf_atr": 2.0, "drop_atr_min": 3.0, "rr": 2.0, "max_hold": 15},
    "GBPJPY": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 2.8, "rr": 2.0, "max_hold": 60},
    "CHFJPY": {"shelf_bars": 7, "shelf_atr": 2.5, "drop_atr_min": 2.8, "rr": 3.0, "max_hold": 30},
    "XAGUSD": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 3.5, "rr": 1.5, "max_hold": 80},
    "NAS100": {"shelf_bars": 7, "shelf_atr": 1.5, "drop_atr_min": 2.8, "rr": 2.5, "max_hold": 60},
    "XAUUSD": {"shelf_bars": 3, "shelf_atr": 2.0, "drop_atr_min": 4.0, "rr": 2.0, "max_hold": 60},
}

BASE = {
    "shelf_hold": 0.4, "rec_min": 0.65, "rec_max": 1.25,
    "break_buf": 0.05, "min_body": 0.30, "min_cloc": 0.50,
    "max_risk_atr": 2.5,
}

SL_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
             0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.90, 1.00]


def sweep_sl(h4, symbol, params, stop_buf):
    idx = h4.index
    o, hi, lo, cl = h4["open"].to_numpy(), h4["high"].to_numpy(), h4["low"].to_numpy(), h4["close"].to_numpy()
    atrs, body, cloc = h4["atr"].to_numpy(), h4["body_ratio"].to_numpy(), h4["close_location"].to_numpy()
    n = len(h4)
    spread, slip = tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))
    shocks = find_v_shocks(h4)
    trades = []
    in_pos_until = -1

    for shock in shocks:
        lo_conf = shock["lo_conf"]
        hi_p, lo_p = shock["hi_p"], shock["lo_p"]
        drop = hi_p - lo_p
        a_shock = atrs[shock["lo_i"]]
        if a_shock > 0 and drop / a_shock < params["drop_atr_min"]:
            continue
        for ri in range(lo_conf, min(n, lo_conf + 60)):
            recovery = (cl[ri] - lo_p) / drop if drop > 0 else 0
            if recovery < 0.65 or recovery > 1.25:
                if recovery > 1.25:
                    break
                continue
            shelf_start = ri + 1
            shelf_end = shelf_start + params["shelf_bars"]
            if shelf_end >= n - 1:
                break
            a = atrs[shelf_end]
            if not math.isfinite(a) or a <= 0:
                continue
            shelf_hi = np.max(hi[shelf_start:shelf_end])
            shelf_lo = np.min(lo[shelf_start:shelf_end])
            if (shelf_hi - shelf_lo) / a > params["shelf_atr"]:
                continue
            if shelf_lo < lo_p + drop * 0.4:
                continue
            for bi in range(shelf_end, min(n - 1, shelf_end + 30)):
                if idx[bi] < RUN_START or bi <= in_pos_until:
                    continue
                a_b = atrs[bi]
                if not math.isfinite(a_b) or a_b <= 0:
                    continue
                if cl[bi - 1] > shelf_hi:
                    break
                if cl[bi] <= shelf_hi + 0.05 * a_b:
                    continue
                if body[bi] < 0.30 or cloc[bi] < 0.50:
                    continue
                stop = shelf_lo - stop_buf * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * params["rr"]
                if risk / a_b > 2.5:
                    break
                end_i = min(n - 1, entry_i + params["max_hold"])
                exit_i, exit_price = end_i, cl[end_i]
                for j in range(entry_i, end_i + 1):
                    if lo[j] <= stop:
                        exit_i, exit_price = j, stop
                        break
                    if hi[j] >= target:
                        exit_i, exit_price = j, target
                        break
                after = (exit_price - slip) - (entry + spread / 2.0)
                trades.append(after / risk)
                in_pos_until = exit_i
                break
            break
    return trades


def main():
    files = sorted((REPO_ROOT / "tv_data").glob("*.csv"))
    data = {}
    for p in files:
        sym = tv.detect_symbol(p)
        if sym in SYMBOLS:
            raw = tv.load_tv_csv(p)
            if len(raw) >= 500:
                data[sym] = add_features(raw)

    print("=" * 90)
    print("B7棚 SL余白 細かいスイープ（全銘柄）")
    print("=" * 90)

    all_best = {}

    for symbol in SYMBOLS:
        if symbol not in data:
            continue
        h4 = data[symbol]
        entry = ENTRY_PARAMS[symbol]
        params = {**BASE, **entry}

        print(f"\n■ {symbol} (RR={entry['rr']} / TIME={entry['max_hold']})")
        print(f"  {'SL余白':>6} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7} {'DD':>6}")
        print(f"  {'-'*50}")

        best_pf = 0
        best_sl = 0.25
        best_r = 0

        for sl in SL_VALUES:
            tr = sweep_sl(h4, symbol, params, sl)
            s = stats(pd.Series(tr))
            is_current = (abs(sl - entry.get("stop_buf_current", 0.25)) < 0.001)
            mark = " ←現在" if sl == 0.25 else ""
            if s["trades"] >= 5 and s["pf"] > best_pf:
                best_pf = s["pf"]
                best_sl = sl
                best_r = s["total_r"]
                if not is_current:
                    mark = " ⭐"
            print(f"  {sl:6.2f} {s['trades']:4} {s['win_rate']:5.1f}% {s['pf']:6.2f} {s['total_r']:7.2f} {s['max_dd_r']:5.1f}{mark}")

        all_best[symbol] = {"sl": best_sl, "pf": best_pf, "total_r": best_r}
        print(f"  → 最適: SL余白={best_sl:.2f} (PF{best_pf:.2f})")

    print(f"\n{'='*90}")
    print("■ 全銘柄 SL余白 最適値まとめ")
    print(f"{'='*90}")
    print(f"{'銘柄':<10} {'現在':>6} {'最適':>6} {'PF':>6} {'合計R':>7}")
    print("-" * 40)
    for sym in SYMBOLS:
        if sym in all_best:
            b = all_best[sym]
            current = 0.25
            print(f"{sym:<10} {current:6.2f} {b['sl']:6.2f} {b['pf']:6.2f} {b['total_r']:7.2f}")


if __name__ == "__main__":
    main()

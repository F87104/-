#!/usr/bin/env python3
"""
B7棚 エグジット最適化スイープ

全銘柄で TIME(タイムアウト) × RR × SL余白(損切り幅) を網羅的にテスト。
各銘柄の最適な棚数/棚幅/急落は確定済み前提で、出口戦略のみ最適化。
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
    "USDJPY": {"shelf_bars": 5, "shelf_atr": 1.8, "drop_atr_min": 3.5},
    "EURJPY": {"shelf_bars": 5, "shelf_atr": 2.0, "drop_atr_min": 3.0},
    "GBPJPY": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 2.8},
    "CHFJPY": {"shelf_bars": 7, "shelf_atr": 2.5, "drop_atr_min": 2.8},
    "XAGUSD": {"shelf_bars": 7, "shelf_atr": 1.8, "drop_atr_min": 3.5},
    "NAS100": {"shelf_bars": 7, "shelf_atr": 1.5, "drop_atr_min": 2.8},
    "XAUUSD": {"shelf_bars": 3, "shelf_atr": 2.0, "drop_atr_min": 4.0},
}

BASE = {
    "shelf_hold": 0.4, "rec_min": 0.65, "rec_max": 1.25,
    "break_buf": 0.05, "min_body": 0.30, "min_cloc": 0.50,
    "max_risk_atr": 2.5,
}

TIME_VALUES = [10, 15, 20, 30, 40, 50, 60, 80, 100, 120]
RR_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0]
STOP_BUF_VALUES = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def sweep_exit(h4, symbol, params, max_hold, stop_buf, rr):
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
            if recovery < params["rec_min"]:
                continue
            if recovery > params["rec_max"]:
                break
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
            if shelf_lo < lo_p + drop * params["shelf_hold"]:
                continue
            for bi in range(shelf_end, min(n - 1, shelf_end + 30)):
                if idx[bi] < RUN_START or bi <= in_pos_until:
                    continue
                a_b = atrs[bi]
                if not math.isfinite(a_b) or a_b <= 0:
                    continue
                if cl[bi - 1] > shelf_hi:
                    break
                if cl[bi] <= shelf_hi + params["break_buf"] * a_b:
                    continue
                if body[bi] < params["min_body"] or cloc[bi] < params["min_cloc"]:
                    continue
                stop = shelf_lo - stop_buf * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * rr
                if risk / a_b > params["max_risk_atr"]:
                    break
                end_i = min(n - 1, entry_i + max_hold)
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

    for symbol in SYMBOLS:
        if symbol not in data:
            continue
        h4 = data[symbol]
        entry = ENTRY_PARAMS[symbol]
        params = {**BASE, **entry}

        print(f"\n{'='*90}")
        print(f"■ {symbol}")
        print(f"{'='*90}")

        # 1) TIME単独スイープ (RR=2.0, SL余白=0.25 固定)
        print(f"\n  --- TIME(タイムアウト)スイープ [RR=2.0, SL余白=0.25] ---")
        print(f"  {'TIME':>5} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
        for t in TIME_VALUES:
            tr = sweep_exit(h4, symbol, params, t, 0.25, 2.0)
            s = stats(pd.Series(tr))
            mark = " ⭐" if s["trades"] >= 5 and s["pf"] > 1.5 else ""
            print(f"  {t:5} {s['trades']:4} {s['win_rate']:5.1f}% {s['pf']:6.2f} {s['total_r']:7.2f}{mark}")

        # 2) SL余白スイープ (RR=2.0, TIME=60 固定)
        print(f"\n  --- SL余白(損切り幅)スイープ [RR=2.0, TIME=60] ---")
        print(f"  {'SL余白':>6} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
        for sb in STOP_BUF_VALUES:
            tr = sweep_exit(h4, symbol, params, 60, sb, 2.0)
            s = stats(pd.Series(tr))
            mark = " ⭐" if s["trades"] >= 5 and s["pf"] > 1.5 else ""
            print(f"  {sb:6.2f} {s['trades']:4} {s['win_rate']:5.1f}% {s['pf']:6.2f} {s['total_r']:7.2f}{mark}")

        # 3) RRスイープ (SL余白=0.25, TIME=60 固定)
        print(f"\n  --- RRスイープ [SL余白=0.25, TIME=60] ---")
        print(f"  {'RR':>4} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
        for r in RR_VALUES:
            tr = sweep_exit(h4, symbol, params, 60, 0.25, r)
            s = stats(pd.Series(tr))
            mark = " ⭐" if s["trades"] >= 5 and s["pf"] > 1.5 else ""
            print(f"  {r:4.1f} {s['trades']:4} {s['win_rate']:5.1f}% {s['pf']:6.2f} {s['total_r']:7.2f}{mark}")

        # 4) 組み合わせ最適化 (TIME × RR × SL余白)
        results = []
        for t in [15, 20, 30, 40, 60, 80]:
            for r in [1.5, 2.0, 2.5, 3.0]:
                for sb in [0.15, 0.25, 0.35, 0.50]:
                    tr = sweep_exit(h4, symbol, params, t, sb, r)
                    s = stats(pd.Series(tr))
                    if s["trades"] >= 5 and s["pf"] > 1.0:
                        results.append({"time": t, "rr": r, "sl_buf": sb, **s})

        if results:
            df = pd.DataFrame(results).sort_values("pf", ascending=False)
            top = df.head(10)
            print(f"\n  === TOP10 組み合わせ ===")
            print(f"  {'TIME':>4} {'RR':>4} {'SL余白':>6} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
            print(f"  {'-'*55}")
            for _, row in top.iterrows():
                print(f"  {int(row['time']):4} {row['rr']:4.1f} {row['sl_buf']:6.2f} | "
                      f"{int(row['trades']):4} {row['win_rate']:5.1f}% {row['pf']:6.2f} {row['total_r']:7.2f}")

    print("\n" + "=" * 90)
    print("完了")


if __name__ == "__main__":
    main()

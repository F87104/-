#!/usr/bin/env python3
"""
B7棚 全銘柄パラメータスイープ

7銘柄(AUDJPY除外)に対して主要パラメータを個別スイープし、
銘柄ごとの最適パラメータを特定。
"""
from __future__ import annotations
import sys, math
from pathlib import Path

import numpy as np
import pandas as pd

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
MAX_HOLD = 60
SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "XAGUSD", "NAS100", "XAUUSD"]


def sweep_symbol(h4, symbol, params):
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
                stop = shelf_lo - params["stop_buf"] * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * params["rr"]
                if risk / a_b > params["max_risk_atr"]:
                    break
                end_i = min(n - 1, entry_i + MAX_HOLD)
                exit_i, exit_price, reason = end_i, cl[end_i], "time"
                for j in range(entry_i, end_i + 1):
                    if lo[j] <= stop:
                        exit_i, exit_price, reason = j, stop, "stop"
                        break
                    if hi[j] >= target:
                        exit_i, exit_price, reason = j, target, "target"
                        break
                after = (exit_price - slip) - (entry + spread / 2.0)
                trades.append(after / risk)
                in_pos_until = exit_i
                break
            break
    return trades


def main():
    base_params = {
        "drop_atr_min": 2.8, "shelf_bars": 7, "shelf_atr": 1.8,
        "shelf_hold": 0.4, "rec_min": 0.65, "rec_max": 1.25,
        "break_buf": 0.05, "min_body": 0.30, "min_cloc": 0.50,
        "stop_buf": 0.25, "max_risk_atr": 2.5, "rr": 2.0,
    }

    sweeps = {
        "RR":             {"rr": [1.5, 2.0, 2.5, 3.0]},
        "急落ATR":         {"drop_atr_min": [2.0, 2.5, 2.8, 3.0, 3.5, 4.0]},
        "棚本数":          {"shelf_bars": [3, 5, 7, 10]},
        "棚幅ATR":         {"shelf_atr": [1.2, 1.5, 1.8, 2.0, 2.5, 3.0]},
        "保持率":          {"shelf_hold": [0.3, 0.4, 0.5, 0.6]},
        "回復率下限":       {"rec_min": [0.55, 0.65, 0.70, 0.80]},
        "終値位置":         {"min_cloc": [0.40, 0.50, 0.60, 0.70]},
        "実体下限":         {"min_body": [0.20, 0.30, 0.40, 0.50]},
    }

    files = sorted((REPO_ROOT / "tv_data").glob("*.csv"))
    data = {}
    for p in files:
        sym = tv.detect_symbol(p)
        if sym in SYMBOLS:
            raw = tv.load_tv_csv(p)
            if len(raw) >= 500:
                data[sym] = add_features(raw)

    print("=" * 90)
    print("B7棚 全銘柄パラメータスイープ")
    print("=" * 90)

    best_per_symbol = {}

    for symbol in SYMBOLS:
        if symbol not in data:
            print(f"\n[skip] {symbol}: データなし")
            continue
        h4 = data[symbol]
        print(f"\n{'='*90}")
        print(f"■ {symbol} ({len(h4)} bars)")
        print(f"{'='*90}")

        # ベースライン
        base_tr = sweep_symbol(h4, symbol, base_params)
        base_s = stats(pd.Series(base_tr))
        print(f"ベースライン: {base_s['trades']}件 勝率{base_s['win_rate']:.1f}% "
              f"PF{base_s['pf']:.2f} 合計{base_s['total_r']:.1f}R")

        best_pf = base_s["pf"] if base_s["trades"] >= 5 else 0
        best_label = "ベースライン"
        best_params = dict(base_params)

        # 個別スイープ
        for group_name, param_dict in sweeps.items():
            param_key = list(param_dict.keys())[0]
            values = param_dict[param_key]
            print(f"\n  --- {group_name} ({param_key}) ---")
            print(f"  {'値':<8} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
            for val in values:
                p = {**base_params, param_key: val}
                tr = sweep_symbol(h4, symbol, p)
                s = stats(pd.Series(tr))
                is_base = (val == base_params[param_key])
                mark = " ←ベース" if is_base else (" ⭐" if s["pf"] > best_pf and s["trades"] >= 5 else "")
                print(f"  {str(val):<8} {s['trades']:4} {s['win_rate']:5.1f}% "
                      f"{s['pf']:6.2f} {s['total_r']:7.2f}{mark}")

        # 組み合わせ最適化: 各パラメータで最良のものを組み合わせ
        print(f"\n  === 組み合わせテスト ===")

        combos = []
        for sb in [3, 5, 7]:
            for sa in [1.5, 1.8, 2.0, 2.5]:
                for da in [2.0, 2.5, 2.8, 3.0, 3.5]:
                    for r in [1.5, 2.0, 2.5]:
                        combos.append({"shelf_bars": sb, "shelf_atr": sa, "drop_atr_min": da, "rr": r})

        results = []
        for combo in combos:
            p = {**base_params, **combo}
            tr = sweep_symbol(h4, symbol, p)
            s = stats(pd.Series(tr))
            if s["trades"] >= 5 and s["pf"] > 1.0:
                results.append({
                    "shelf_bars": combo["shelf_bars"],
                    "shelf_atr": combo["shelf_atr"],
                    "drop_atr_min": combo["drop_atr_min"],
                    "rr": combo["rr"],
                    **s,
                })

        if results:
            df = pd.DataFrame(results).sort_values("pf", ascending=False)
            top = df.head(10)
            print(f"  {'棚数':>4} {'棚幅':>5} {'急落':>5} {'RR':>4} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
            print(f"  {'-'*60}")
            for _, row in top.iterrows():
                print(f"  {int(row['shelf_bars']):4} {row['shelf_atr']:5.1f} {row['drop_atr_min']:5.1f} {row['rr']:4.1f} | "
                      f"{int(row['trades']):4} {row['win_rate']:5.1f}% {row['pf']:6.2f} {row['total_r']:7.2f}")

            best_row = df.iloc[0]
            best_per_symbol[symbol] = {
                "shelf_bars": int(best_row["shelf_bars"]),
                "shelf_atr": best_row["shelf_atr"],
                "drop_atr_min": best_row["drop_atr_min"],
                "rr": best_row["rr"],
                "pf": best_row["pf"],
                "trades": int(best_row["trades"]),
                "win_rate": best_row["win_rate"],
                "total_r": best_row["total_r"],
            }

    # 最終サマリ
    print("\n" + "=" * 90)
    print("■ 全銘柄最適パラメータまとめ")
    print("=" * 90)
    print(f"{'銘柄':<8} {'棚数':>4} {'棚幅':>5} {'急落':>5} {'RR':>4} | {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
    print("-" * 70)
    for sym in SYMBOLS:
        if sym in best_per_symbol:
            b = best_per_symbol[sym]
            print(f"{sym:<8} {b['shelf_bars']:4} {b['shelf_atr']:5.1f} {b['drop_atr_min']:5.1f} {b['rr']:4.1f} | "
                  f"{b['trades']:4} {b['win_rate']:5.1f}% {b['pf']:6.2f} {b['total_r']:7.2f}")
        else:
            print(f"{sym:<8}  -- データなし --")


if __name__ == "__main__":
    main()

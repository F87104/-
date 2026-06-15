#!/usr/bin/env python3
"""
B7棚 XAUUSD 精度向上パラメータスイープ

ゴールド専用パラメータ(急落4.0/棚幅2.0/棚3本)をベースに、
エントリー精度を高めるフィルターを網羅的にテスト。
"""
from __future__ import annotations
import sys, math
from pathlib import Path
from itertools import product

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
OOS_START = pd.Timestamp("2025-01-01")
MAX_HOLD = 60


def sweep_gold(h4, params):
    """1パラメータセットでゴールドB7棚をバックテスト"""
    drop_atr_min = params["drop_atr_min"]
    shelf_bars = params["shelf_bars"]
    shelf_atr = params["shelf_atr"]
    shelf_hold = params["shelf_hold"]
    min_body = params["min_body"]
    min_cloc = params["min_cloc"]
    break_buf = params["break_buf"]
    stop_buf = params["stop_buf"]
    max_risk_atr = params["max_risk_atr"]
    rec_min = params["rec_min"]
    rec_max = params["rec_max"]
    rr = params["rr"]

    idx = h4.index
    o = h4["open"].to_numpy()
    hi = h4["high"].to_numpy()
    lo = h4["low"].to_numpy()
    cl = h4["close"].to_numpy()
    atrs = h4["atr"].to_numpy()
    body = h4["body_ratio"].to_numpy()
    cloc = h4["close_location"].to_numpy()
    n = len(h4)
    spread, slip = tv.COST_BY_SYMBOL.get("XAUUSD", (0.30, 0.15))

    shocks = find_v_shocks(h4)
    trades = []
    in_pos_until = -1

    for shock in shocks:
        lo_conf = shock["lo_conf"]
        hi_p, lo_p = shock["hi_p"], shock["lo_p"]
        drop = hi_p - lo_p
        a_shock = atrs[shock["lo_i"]]
        if a_shock > 0 and drop / a_shock < drop_atr_min:
            continue

        for ri in range(lo_conf, min(n, lo_conf + 60)):
            recovery = (cl[ri] - lo_p) / drop if drop > 0 else 0
            if recovery < rec_min:
                continue
            if recovery > rec_max:
                break

            shelf_start = ri + 1
            shelf_end = shelf_start + shelf_bars
            if shelf_end >= n - 1:
                break

            a = atrs[shelf_end]
            if not math.isfinite(a) or a <= 0:
                continue

            shelf_hi = np.max(hi[shelf_start:shelf_end])
            shelf_lo = np.min(lo[shelf_start:shelf_end])
            shelf_range = (shelf_hi - shelf_lo) / a
            if shelf_range > shelf_atr:
                continue

            recovery_line = lo_p + drop * shelf_hold
            if shelf_lo < recovery_line:
                continue

            for bi in range(shelf_end, min(n - 1, shelf_end + 30)):
                ts = idx[bi]
                if ts < RUN_START:
                    continue
                if bi <= in_pos_until:
                    continue
                a_b = atrs[bi]
                if not math.isfinite(a_b) or a_b <= 0:
                    continue
                if cl[bi - 1] > shelf_hi:
                    break
                if cl[bi] <= shelf_hi + break_buf * a_b:
                    continue
                if body[bi] < min_body or cloc[bi] < min_cloc:
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
                risk_atr = risk / a_b
                if risk_atr > max_risk_atr:
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
                r_after = after / risk
                trades.append(r_after)
                in_pos_until = exit_i
                break
            break

    return trades


def main():
    gold_path = None
    for p in sorted((REPO_ROOT / "tv_data").glob("*.csv")):
        if tv.detect_symbol(p) == "XAUUSD":
            gold_path = p
            break
    if gold_path is None:
        print("XAUUSD CSV not found")
        return

    raw = tv.load_tv_csv(gold_path)
    h4 = add_features(raw)
    print(f"XAUUSD H4: {len(h4)} bars ({h4.index[0]} ~ {h4.index[-1]})\n")

    base = {
        "drop_atr_min": 4.0,
        "shelf_bars": 3,
        "shelf_atr": 2.0,
        "shelf_hold": 0.4,
        "min_body": 0.30,
        "min_cloc": 0.50,
        "break_buf": 0.05,
        "stop_buf": 0.25,
        "max_risk_atr": 2.5,
        "rec_min": 0.65,
        "rec_max": 1.25,
        "rr": 2.0,
    }

    # ベースライン
    base_trades = sweep_gold(h4, base)
    base_s = stats(pd.Series(base_trades))
    print("=" * 70)
    print(f"ベースライン (急落4.0/棚2.0/棚3本/RR2.0)")
    print(f"  {base_s['trades']}件 / 勝率{base_s['win_rate']:.1f}% / "
          f"PF{base_s['pf']:.2f} / 合計{base_s['total_r']:.1f}R")
    print("=" * 70)

    # 精度向上フィルタースイープ
    sweeps = {
        "ブレイク実体下限(min_body)": [
            ("0.30 ベース", {"min_body": 0.30}),
            ("0.40", {"min_body": 0.40}),
            ("0.50", {"min_body": 0.50}),
            ("0.60", {"min_body": 0.60}),
            ("0.70", {"min_body": 0.70}),
        ],
        "終値位置下限(min_cloc)": [
            ("0.50 ベース", {"min_cloc": 0.50}),
            ("0.60", {"min_cloc": 0.60}),
            ("0.70", {"min_cloc": 0.70}),
            ("0.80", {"min_cloc": 0.80}),
        ],
        "リスク幅上限(max_risk_atr)": [
            ("2.5 ベース", {"max_risk_atr": 2.5}),
            ("2.0", {"max_risk_atr": 2.0}),
            ("1.5", {"max_risk_atr": 1.5}),
            ("1.0", {"max_risk_atr": 1.0}),
        ],
        "回復率(rec_min)": [
            ("0.65 ベース", {"rec_min": 0.65}),
            ("0.70", {"rec_min": 0.70}),
            ("0.75", {"rec_min": 0.75}),
            ("0.80", {"rec_min": 0.80}),
        ],
        "棚安値保持率(shelf_hold)": [
            ("0.40 ベース", {"shelf_hold": 0.40}),
            ("0.50", {"shelf_hold": 0.50}),
            ("0.60", {"shelf_hold": 0.60}),
            ("0.70", {"shelf_hold": 0.70}),
        ],
        "急落幅下限(drop_atr_min)": [
            ("4.0 ベース", {"drop_atr_min": 4.0}),
            ("4.5", {"drop_atr_min": 4.5}),
            ("5.0", {"drop_atr_min": 5.0}),
            ("5.5", {"drop_atr_min": 5.5}),
        ],
        "RR": [
            ("2.0 ベース", {"rr": 2.0}),
            ("2.5", {"rr": 2.5}),
            ("3.0", {"rr": 3.0}),
        ],
    }

    print("\n■ 個別フィルター影響")
    for group_name, variants in sweeps.items():
        print(f"\n--- {group_name} ---")
        print(f"{'値':<15} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
        for label, override in variants:
            p = {**base, **override}
            tr = sweep_gold(h4, p)
            s = stats(pd.Series(tr))
            mark = " ⭐" if s["pf"] > base_s["pf"] and s["trades"] > 5 else ""
            print(f"{label:<15} {s['trades']:4} {s['win_rate']:5.1f}% "
                  f"{s['pf']:6.2f} {s['total_r']:7.2f}{mark}")

    # 組み合わせ最適化: 有望なフィルターを組み合わせ
    print("\n" + "=" * 70)
    print("■ 有望組み合わせテスト")
    print("=" * 70)

    combos = [
        ("1: 保持0.60のみ",
         {"shelf_hold": 0.60}),
        ("2: 回復0.70のみ",
         {"rec_min": 0.70}),
        ("3: 保持0.60+回復0.70",
         {"shelf_hold": 0.60, "rec_min": 0.70}),
        ("4: 保持0.60+終値0.70",
         {"shelf_hold": 0.60, "min_cloc": 0.70}),
        ("5: 保持0.60+終値0.80",
         {"shelf_hold": 0.60, "min_cloc": 0.80}),
        ("6: 回復0.70+終値0.70",
         {"rec_min": 0.70, "min_cloc": 0.70}),
        ("7: 回復0.70+終値0.80",
         {"rec_min": 0.70, "min_cloc": 0.80}),
        ("8: 保持0.60+回復0.70+終値0.70",
         {"shelf_hold": 0.60, "rec_min": 0.70, "min_cloc": 0.70}),
        ("9: 保持0.60+回復0.70+終値0.80",
         {"shelf_hold": 0.60, "rec_min": 0.70, "min_cloc": 0.80}),
        ("10: 保持0.60+回復0.70+RR2.5",
         {"shelf_hold": 0.60, "rec_min": 0.70, "rr": 2.5}),
        ("11: 保持0.60+回復0.70+RR3.0",
         {"shelf_hold": 0.60, "rec_min": 0.70, "rr": 3.0}),
        ("12: 保持0.60+回復0.70+終値0.70+RR2.5",
         {"shelf_hold": 0.60, "rec_min": 0.70, "min_cloc": 0.70, "rr": 2.5}),
        ("13: 保持0.60+回復0.70+終値0.70+RR3.0",
         {"shelf_hold": 0.60, "rec_min": 0.70, "min_cloc": 0.70, "rr": 3.0}),
        ("14: 保持0.60+急落5.0",
         {"shelf_hold": 0.60, "drop_atr_min": 5.0}),
        ("15: 保持0.60+回復0.70+急落5.0",
         {"shelf_hold": 0.60, "rec_min": 0.70, "drop_atr_min": 5.0}),
        ("16: 保持0.60+回復0.70+急落5.0+終値0.70",
         {"shelf_hold": 0.60, "rec_min": 0.70, "drop_atr_min": 5.0, "min_cloc": 0.70}),
    ]

    print(f"\n{'ラベル':<45} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
    print("-" * 75)
    print(f"{'ベースライン':<45} {base_s['trades']:4} {base_s['win_rate']:5.1f}% "
          f"{base_s['pf']:6.2f} {base_s['total_r']:7.2f}")
    print("-" * 75)
    for label, override in combos:
        p = {**base, **override}
        tr = sweep_gold(h4, p)
        s = stats(pd.Series(tr))
        mark = " ⭐" if s["pf"] > base_s["pf"] and s["trades"] >= 5 else ""
        print(f"{label:<45} {s['trades']:4} {s['win_rate']:5.1f}% "
              f"{s['pf']:6.2f} {s['total_r']:7.2f}{mark}")


if __name__ == "__main__":
    main()

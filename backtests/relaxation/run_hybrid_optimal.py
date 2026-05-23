"""
ハイブリッド最適化: 通貨ペア毎に最良の緩和パターンを選択

per-symbol 結果から:
  EURJPY: BASE (level=any で悪化)
  XAUUSD: L6 only (level=any で悪化)
  CHFJPY: L5 (or SAFE1)
  GBPJPY: SAFE1
  SILVER: SAFE1
  USDJPY: SAFE1
"""
from __future__ import annotations

import copy
import os
import sys
import numpy as np
import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backtest"))

from trendbreak_backtest import (
    PRESETS_CONSERVATIVE, compute_signals, simulate,
)
from sai_backtest import load_instrument

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30,  "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}

# Per-symbol で最適化された緩和パターン
HYBRID_OPTIMAL = {
    "XAUUSD": lambda c: {**c, "session": False},                      # L6 only
    "USDJPY": lambda c: {**c, "level_kind": "any", "session": False}, # SAFE1
    "EURJPY": lambda c: c,                                             # BASE
    "GBPJPY": lambda c: {**c, "level_kind": "any", "session": False}, # SAFE1
    "CHFJPY": lambda c: {**c, "level_kind": "any"},                   # L5
    "SILVER": lambda c: {**c, "level_kind": "any", "session": False}, # SAFE1
}

# 比較用: 全通貨 SAFE1 一律
SAFE1_UNIFORM = {sym: (lambda c: {**c, "level_kind": "any", "session": False})
                 for sym in HYBRID_OPTIMAL.keys()}

# 比較用: BASE Conservative
BASE_UNIFORM = {sym: (lambda c: c) for sym in HYBRID_OPTIMAL.keys()}


def apply_cost_to_trades(trades, spread, slip):
    if not trades:
        return np.array([])
    r_after = []
    for t in trades:
        ent = t.entry + spread / 2 if t.direction == "long" else t.entry - spread / 2
        ex = (t.exit_price - slip) if t.direction == "long" else (t.exit_price + slip)
        pnl = (ex - ent) if t.direction == "long" else (ent - ex)
        sl_dist = abs(t.entry - t.sl)
        r_after.append(pnl / sl_dist if sl_dist > 0 else 0)
    return np.array(r_after)


def streaks(r):
    if len(r) == 0:
        return 0, 0
    s = np.where(r > 0, 1, -1)
    mw, ml, cw, cl = 0, 0, 0, 0
    for x in s:
        if x == 1:
            cw += 1; cl = 0
        else:
            cl += 1; cw = 0
        mw = max(mw, cw); ml = max(ml, cl)
    return mw, ml


def run_modifier_map(modifier_map: dict, year_from=2015, year_to=2024):
    all_trades_with_meta = []
    per_sym_rows = []
    for sym, modifier in modifier_map.items():
        cfg = modifier(copy.deepcopy(PRESETS_CONSERVATIVE[sym]))
        try:
            df = load_instrument(sym)
        except Exception:
            continue
        df = df[(df.index.year >= year_from) & (df.index.year <= year_to)]
        sig = compute_signals(df, cfg)
        trades = simulate(sig, cfg)
        if not trades:
            continue
        r_clean = np.array([t.pnl_r for t in trades])
        r_after = apply_cost_to_trades(trades,
                                        COST_TABLE[sym]["spread_price"],
                                        COST_TABLE[sym]["slip_price"])
        all_trades_with_meta.extend([(sym, t.entry_time, t.pnl_r, r_after[i]) for i, t in enumerate(trades)])
        gp = r_after[r_after > 0].sum()
        gl = r_after[r_after <= 0].sum()
        pf_a = gp / abs(gl) if gl < 0 else np.inf
        per_sym_rows.append({
            "symbol": sym,
            "cfg": str(cfg),
            "trades": len(trades),
            "win_rate": round(float((r_clean > 0).mean() * 100), 2),
            "total_r_clean": round(float(r_clean.sum()), 2),
            "total_r_after_cost": round(float(r_after.sum()), 2),
            "avg_r_after_cost": round(float(r_after.mean()), 4),
            "pf_after_cost": round(pf_a, 3) if np.isfinite(pf_a) else np.inf,
            "max_losing_streak": streaks(r_clean)[1],
        })

    # 全通貨を時系列でソート → 全体ストリーク・DD を計算
    all_trades_with_meta.sort(key=lambda x: x[1])
    r_clean_all = np.array([x[2] for x in all_trades_with_meta])
    r_after_all = np.array([x[3] for x in all_trades_with_meta])
    eq_after = np.cumsum(r_after_all)
    dd_after = float((np.maximum.accumulate(eq_after) - eq_after).max()) if len(eq_after) else 0.0
    mw, ml = streaks(r_after_all)
    gp_a = r_after_all[r_after_all > 0].sum()
    gl_a = r_after_all[r_after_all <= 0].sum()
    pf_a = gp_a / abs(gl_a) if gl_a < 0 else np.inf

    summary = {
        "total_trades": len(r_clean_all),
        "trades_per_year": round(len(r_clean_all) / (year_to - year_from + 1), 1),
        "win_rate": round(float((r_clean_all > 0).mean() * 100), 2),
        "total_r_clean": round(float(r_clean_all.sum()), 2),
        "total_r_after_cost": round(float(r_after_all.sum()), 2),
        "avg_r_after_cost": round(float(r_after_all.mean()), 4),
        "pf_after_cost": round(pf_a, 3) if np.isfinite(pf_a) else np.inf,
        "max_dd_after_cost_r": round(dd_after, 2),
        "max_losing_streak": ml,
        "max_winning_streak": mw,
    }
    return summary, pd.DataFrame(per_sym_rows)


def main():
    print("=" * 100)
    print("HYBRID OPTIMAL EVALUATION  |  per-symbol best parameter relaxation")
    print("=" * 100)

    scenarios = [
        ("BASE_uniform",   BASE_UNIFORM),
        ("SAFE1_uniform",  SAFE1_UNIFORM),
        ("HYBRID_optimal", HYBRID_OPTIMAL),
    ]

    rows = []
    for name, m in scenarios:
        s, per_sym = run_modifier_map(m)
        s["scenario"] = name
        rows.append(s)
        print(f"\n--- {name} ---")
        for k, v in s.items():
            print(f"  {k:30} {v}")
        per_sym.to_csv(os.path.join(THIS_DIR, f"hybrid_{name}_per_symbol.csv"), index=False)

    summary_df = pd.DataFrame(rows)
    summary_df = summary_df[["scenario", "total_trades", "trades_per_year", "win_rate",
                              "total_r_clean", "total_r_after_cost", "avg_r_after_cost",
                              "pf_after_cost", "max_losing_streak", "max_dd_after_cost_r"]]
    print("\n" + "=" * 100)
    print("FINAL COMPARISON")
    print("=" * 100)
    print(summary_df.to_string(index=False))
    summary_df.to_csv(os.path.join(THIS_DIR, "hybrid_comparison.csv"), index=False)


if __name__ == "__main__":
    main()

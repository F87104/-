"""
パラメータ緩和の多角的調査

目的: エントリー機会を増やしながら、勝率・PF・期待値・連敗がどう変化するか測定。

スイープ対象 (Conservative ベースラインを基準に、緩和方向に1パラメータずつ動かす):
  L1: lookback_3m   ↓ (短くする = 短期ブレイクで多く発火)
  L2: exclude_bars  ↓ (狭くする = "直近触れていない"条件を緩める)
  L3: sl_atr        ↓ (SLを近づける = 取引数増 / 勝率低下 / リスク量増)
  L4: tp_rr         ↓ (TPを近づける = 早期利確 / 勝率増 / 期待値減)
  L5: level_kind    "any" (mid + long の OR = 緩い)
  L6: session       False (全時間取引)
  L7: combined_easy (上記の中間値を全部適用)
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

# Audit と同じコストテーブル
COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30,  "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}

# 採用対象 (監査で AUDJPY は除外)
SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]
YEAR_FROM, YEAR_TO = 2015, 2024

OUT_DIR = THIS_DIR


def apply_cost_to_trades(trades: list, spread: float, slip: float) -> np.ndarray:
    if not trades:
        return np.array([])
    r_after = []
    for t in trades:
        ent = t.entry + spread / 2 if t.direction == "long" else t.entry - spread / 2
        if t.direction == "long":
            ex = t.exit_price - slip
        else:
            ex = t.exit_price + slip
        pnl = (ex - ent) if t.direction == "long" else (ent - ex)
        sl_dist = abs(t.entry - t.sl)
        r_after.append(pnl / sl_dist if sl_dist > 0 else 0)
    return np.array(r_after)


def streaks(r: np.ndarray) -> tuple[int, int]:
    if len(r) == 0:
        return 0, 0
    signs = np.where(r > 0, 1, -1)
    max_w, max_l, cw, cl = 0, 0, 0, 0
    for s in signs:
        if s == 1:
            cw += 1; cl = 0
        else:
            cl += 1; cw = 0
        max_w = max(max_w, cw)
        max_l = max(max_l, cl)
    return max_w, max_l


def metrics_set(trades: list, cost_spread: float, cost_slip: float) -> dict:
    if not trades:
        return {"trades": 0}
    r = np.array([t.pnl_r for t in trades])
    r_after = apply_cost_to_trades(trades, cost_spread, cost_slip)
    wins = int((r > 0).sum())
    wr = wins / len(r) * 100
    gp = r[r > 0].sum()
    gl = r[r <= 0].sum()
    pf = gp / abs(gl) if gl < 0 else np.inf
    pf_a = (r_after[r_after > 0].sum() / abs(r_after[r_after <= 0].sum())
            if (r_after <= 0).any() else np.inf)
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0
    eq_a = np.cumsum(r_after)
    dd_a = float((np.maximum.accumulate(eq_a) - eq_a).max()) if len(eq_a) else 0.0
    mw, ml = streaks(r)
    return {
        "trades": len(r),
        "win_rate": round(wr, 2),
        "total_r": round(r.sum(), 2),
        "total_r_after_cost": round(r_after.sum(), 2),
        "avg_r": round(float(r.mean()), 4),
        "avg_r_after_cost": round(float(r_after.mean()), 4),
        "pf": round(pf, 3) if np.isfinite(pf) else np.inf,
        "pf_after_cost": round(pf_a, 3) if np.isfinite(pf_a) else np.inf,
        "max_dd_r": round(dd, 2),
        "max_dd_after_cost_r": round(dd_a, 2),
        "max_winning_streak": mw,
        "max_losing_streak": ml,
        "avg_hold_bars": round(float(np.mean([t.bars_held for t in trades])), 2),
        "trades_per_year": round(len(r) / (YEAR_TO - YEAR_FROM + 1), 1),
    }


def run_scenario(label: str, modify: callable) -> dict:
    """全 SYMBOLS で modify(cfg) を適用してバックテストし、全集計を返す。"""
    all_trades = []
    per_symbol = []
    for sym in SYMBOLS:
        base = copy.deepcopy(PRESETS_CONSERVATIVE[sym])
        cfg = modify(base)
        try:
            df = load_instrument(sym)
        except Exception:
            continue
        df = df[(df.index.year >= YEAR_FROM) & (df.index.year <= YEAR_TO)]
        sig = compute_signals(df, cfg)
        trades = simulate(sig, cfg)
        all_trades.extend(trades)
        m = metrics_set(trades,
                        COST_TABLE[sym]["spread_price"],
                        COST_TABLE[sym]["slip_price"])
        m.update({"label": label, "symbol": sym, "cfg": str(cfg)})
        per_symbol.append(m)

    # 全通貨集計 (after-cost を symbol別に集めた合計から)
    r_all_clean = []
    r_all_after = []
    for sym in SYMBOLS:
        base = copy.deepcopy(PRESETS_CONSERVATIVE[sym])
        cfg = modify(base)
        try:
            df = load_instrument(sym)
        except Exception:
            continue
        df = df[(df.index.year >= YEAR_FROM) & (df.index.year <= YEAR_TO)]
        sig = compute_signals(df, cfg)
        trades = simulate(sig, cfg)
        if not trades:
            continue
        r_all_clean.extend([t.pnl_r for t in trades])
        r_all_after.extend(apply_cost_to_trades(
            trades, COST_TABLE[sym]["spread_price"], COST_TABLE[sym]["slip_price"]).tolist())

    r_c = np.array(r_all_clean)
    r_a = np.array(r_all_after)
    summary = {
        "label": label,
        "total_trades": len(r_c),
        "trades_per_year": round(len(r_c) / (YEAR_TO - YEAR_FROM + 1), 1),
        "win_rate": round(float((r_c > 0).mean() * 100), 2) if len(r_c) else 0,
        "total_r_clean": round(float(r_c.sum()), 2) if len(r_c) else 0,
        "total_r_after_cost": round(float(r_a.sum()), 2) if len(r_a) else 0,
        "avg_r_clean": round(float(r_c.mean()), 4) if len(r_c) else 0,
        "avg_r_after_cost": round(float(r_a.mean()), 4) if len(r_a) else 0,
        "pf_clean": round(float(r_c[r_c > 0].sum() / abs(r_c[r_c <= 0].sum())), 3)
                    if (r_c <= 0).any() else np.inf,
        "pf_after_cost": round(float(r_a[r_a > 0].sum() / abs(r_a[r_a <= 0].sum())), 3)
                          if (r_a <= 0).any() else np.inf,
        "max_streak_lose": streaks(r_c)[1] if len(r_c) else 0,
        "max_dd_clean_r": round(float((np.maximum.accumulate(np.cumsum(r_c))
                                       - np.cumsum(r_c)).max()), 2) if len(r_c) else 0,
        "max_dd_after_cost_r": round(float((np.maximum.accumulate(np.cumsum(r_a))
                                            - np.cumsum(r_a)).max()), 2) if len(r_a) else 0,
    }
    return {"summary": summary, "per_symbol": per_symbol}


# =====================================================================
# スイープシナリオ
# =====================================================================

SCENARIOS = [
    # ベースライン (Conservative)
    ("BASE: Conservative",
     lambda c: c),

    # L1: lookback_3m を緩める (短くする = 短期ブレイク多発)
    ("L1a: lookback x0.75",
     lambda c: {**c, "lookback_3m": int(c["lookback_3m"] * 0.75)}),
    ("L1b: lookback x0.5",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5))}),
    ("L1c: lookback x0.33",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.33))}),

    # L2: exclude_bars を緩める
    ("L2a: exclude x0.5",
     lambda c: {**c, "exclude": max(5, int(c["exclude"] * 0.5))}),
    ("L2b: exclude x0.25",
     lambda c: {**c, "exclude": max(5, int(c["exclude"] * 0.25))}),
    ("L2c: exclude=10",
     lambda c: {**c, "exclude": 10}),

    # L3: sl_atr を狭める (取引数増・勝率下がる傾向)
    ("L3a: sl_atr x0.75",
     lambda c: {**c, "sl_atr": c["sl_atr"] * 0.75}),
    ("L3b: sl_atr=1.0",
     lambda c: {**c, "sl_atr": 1.0}),

    # L4: tp_rr を下げる (早期利確 → 勝率増)
    ("L4a: tp_rr=2.0",
     lambda c: {**c, "tp_rr": 2.0}),
    ("L4b: tp_rr=2.5",
     lambda c: {**c, "tp_rr": 2.5}),

    # L5: level_kind を緩める
    ("L5: level_kind=any",
     lambda c: {**c, "level_kind": "any"}),

    # L6: session OFF (全時間取引)
    ("L6: session OFF",
     lambda c: {**c, "session": False}),

    # 中間緩和パターン (複合)
    ("M1: lb x0.75 + exclude x0.5",
     lambda c: {**c, "lookback_3m": int(c["lookback_3m"] * 0.75),
                "exclude": max(5, int(c["exclude"] * 0.5))}),

    ("M2: lb x0.5 + exclude x0.5",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5)),
                "exclude": max(5, int(c["exclude"] * 0.5))}),

    ("M3: M2 + level=any",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5)),
                "exclude": max(5, int(c["exclude"] * 0.5)),
                "level_kind": "any"}),

    ("M4: M2 + tp=2.5",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5)),
                "exclude": max(5, int(c["exclude"] * 0.5)),
                "tp_rr": 2.5}),

    ("M5: M2 + session OFF",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5)),
                "exclude": max(5, int(c["exclude"] * 0.5)),
                "session": False}),

    # ALL: 全緩和
    ("ALL: lb x0.5 + ex x0.5 + level=any + session OFF + tp=2.5",
     lambda c: {**c, "lookback_3m": max(60, int(c["lookback_3m"] * 0.5)),
                "exclude": max(5, int(c["exclude"] * 0.5)),
                "level_kind": "any", "session": False, "tp_rr": 2.5}),

    # 安全緩和パターン (L5/L6 の組み合わせを基点として段階的に追加)
    ("SAFE1: L5+L6 (level=any, session OFF)",
     lambda c: {**c, "level_kind": "any", "session": False}),
    ("SAFE2: SAFE1 + tp=2.5",
     lambda c: {**c, "level_kind": "any", "session": False, "tp_rr": 2.5}),
    ("SAFE3: SAFE1 + lb x0.75",
     lambda c: {**c, "level_kind": "any", "session": False,
                "lookback_3m": int(c["lookback_3m"] * 0.75)}),
    ("SAFE4: SAFE1 + ex x0.5",
     lambda c: {**c, "level_kind": "any", "session": False,
                "exclude": max(5, int(c["exclude"] * 0.5))}),
    ("SAFE5: SAFE1 + lb x0.75 + ex x0.5",
     lambda c: {**c, "level_kind": "any", "session": False,
                "lookback_3m": int(c["lookback_3m"] * 0.75),
                "exclude": max(5, int(c["exclude"] * 0.5))}),
]


def main() -> None:
    summaries = []
    per_symbol_rows = []
    print("=" * 100)
    print(f"PARAMETER RELAXATION STUDY  |  base: Conservative  |  symbols: {SYMBOLS}")
    print("=" * 100)
    print(f"{'Label':45} {'Trd/Y':>7} {'WR':>6} {'TotR_clean':>11} "
          f"{'TotR_cost':>11} {'PF_cost':>8} {'AvgR_cost':>10} {'MaxLose':>8}")
    print("-" * 110)

    for label, modify in SCENARIOS:
        res = run_scenario(label, modify)
        s = res["summary"]
        summaries.append(s)
        per_symbol_rows.extend(res["per_symbol"])
        print(f"{label:45} "
              f"{s['trades_per_year']:>7.1f} "
              f"{s['win_rate']:>5.1f}% "
              f"{s['total_r_clean']:>+10.1f}R "
              f"{s['total_r_after_cost']:>+10.1f}R "
              f"{s['pf_after_cost']:>7.2f}  "
              f"{s['avg_r_after_cost']:>+9.3f}R "
              f"{s['max_streak_lose']:>8}")

    sum_df = pd.DataFrame(summaries)
    sum_df.to_csv(os.path.join(OUT_DIR, "relaxation_summary.csv"), index=False)

    per_sym_df = pd.DataFrame(per_symbol_rows)
    per_sym_df.to_csv(os.path.join(OUT_DIR, "relaxation_per_symbol.csv"), index=False)

    # トップ3 by after-cost net R (取引数増加を期待値で正当化できているか)
    print("\n" + "=" * 110)
    print("RANK BY: After-Cost Total R (収益面)")
    print("=" * 110)
    by_net = sum_df.sort_values("total_r_after_cost", ascending=False)
    print(by_net[["label", "trades_per_year", "win_rate", "total_r_after_cost",
                  "pf_after_cost", "avg_r_after_cost", "max_streak_lose",
                  "max_dd_after_cost_r"]].to_string(index=False))

    print("\n" + "=" * 110)
    print("RANK BY: Trades/Year (機会面)")
    print("=" * 110)
    by_trades = sum_df.sort_values("trades_per_year", ascending=False)
    print(by_trades[["label", "trades_per_year", "win_rate", "total_r_after_cost",
                     "pf_after_cost", "avg_r_after_cost", "max_streak_lose"]].to_string(index=False))

    print("\n" + "=" * 110)
    print("OUTPUT FILES")
    print("=" * 110)
    for fn in sorted(os.listdir(OUT_DIR)):
        if fn.endswith(".csv"):
            sz = os.path.getsize(os.path.join(OUT_DIR, fn))
            print(f"  {fn:40} {sz:>10} bytes")


if __name__ == "__main__":
    main()

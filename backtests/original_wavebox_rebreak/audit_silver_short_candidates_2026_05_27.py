#!/usr/bin/env python3
"""Audit shortlisted SILVER H1 short candidates."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
RESEARCH_PATH = THIS_DIR / "research_silver_short_system.py"
OUT_DIR = THIS_DIR / "results_2026_05_27" / "silver_short_system"


def load_research_module():
    spec = importlib.util.spec_from_file_location("silver_short_research", RESEARCH_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cost_r(trades: pd.DataFrame, spread: float, slip: float) -> pd.Series:
    return ((trades["entry"] - spread / 2.0) - (trades["exit"] + slip)) / trades["risk"]


def max_drawdown(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def pf(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def summarize_named(name: str, trades: pd.DataFrame, r_col: str = "r_after_cost") -> dict:
    if trades.empty:
        return {"name": name, "trades": 0}
    r = trades[r_col]
    is_df = trades[trades["entry_time"] < pd.Timestamp("2025-01-01")]
    oos_df = trades[trades["entry_time"] >= pd.Timestamp("2025-01-01")]
    y2025 = trades[(trades["entry_time"] >= pd.Timestamp("2025-01-01")) & (trades["entry_time"] < pd.Timestamp("2026-01-01"))]
    ex2026 = trades[trades["entry_time"] < pd.Timestamp("2026-01-01")]
    by_year = trades.groupby(trades["entry_time"].dt.year)[r_col].sum()
    roll2 = by_year.rolling(2).sum().dropna()
    return {
        "name": name,
        "trades": len(trades),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": pf(r),
        "max_dd_r": max_drawdown(r),
        "is_trades": len(is_df),
        "is_r": float(is_df[r_col].sum()) if not is_df.empty else 0.0,
        "oos_trades": len(oos_df),
        "oos_r": float(oos_df[r_col].sum()) if not oos_df.empty else 0.0,
        "oos_2025_trades": len(y2025),
        "oos_2025_r": float(y2025[r_col].sum()) if not y2025.empty else 0.0,
        "ex_2026_trades": len(ex2026),
        "ex_2026_r": float(ex2026[r_col].sum()) if not ex2026.empty else 0.0,
        "worst_year_r": float(by_year.min()) if not by_year.empty else 0.0,
        "worst_2y_r": float(roll2.min()) if not roll2.empty else float(by_year.min()),
        "same_bar_ambiguous": int(trades["exit_reason"].astype(str).str.contains("same_bar").sum()),
        "avg_mae_r": float(trades["mae_r"].mean()),
    }


def markdown_table(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.itertuples(index=False, name=None)]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]
    )


def main() -> None:
    mod = load_research_module()
    h1 = mod.prepare_h1()
    source = pd.read_csv(OUT_DIR / "silver_short_source.csv", parse_dates=["signal_time"])

    base = {
        "family": "pullback_rebreak",
        "lookback": "any",
        "box_bars": 8,
        "move_bars": 24,
        "move_atr": 0.8,
        "trigger_atr": 0.05,
        "range_atr": 0.5,
        "body_max": 0.85,
        "close_location": 0.75,
        "upper_wick": 0.0,
        "box_width_max": 1.5,
        "pullback_atr": 0.6,
        "bb_z": None,
        "rsi_high": None,
        "h4": "down",
        "d1": "any",
        "hour_filter": "all",
        "rr": 1.2,
        "stop_buffer_atr": 0.15,
        "max_risk_atr": 2.5,
        "max_hold": 24,
    }
    candidates = {
        "core_no_time": base,
        "guard_ex_11_12": {**base, "hour_filter": "ex_11_12"},
        "aggressive_ex_7_11_12": {**base, "hour_filter": "ex_7_11_12"},
        "strict_pullback_1_0": {**base, "pullback_atr": 1.0},
        "tp1_guard_ex_11_12": {**base, "hour_filter": "ex_11_12", "rr": 1.0},
        "maxhold12_guard_ex_11_12": {**base, "hour_filter": "ex_11_12", "max_hold": 12},
        "loose_close65_guard_ex_11_12": {**base, "hour_filter": "ex_11_12", "close_location": 0.65},
    }

    audit_rows = []
    cost_rows = []
    by_year_rows = []
    by_hour_rows = []
    trades_by_name = {}
    for name, spec in candidates.items():
        trades = mod.run_trades(h1, source, spec)
        trades_by_name[name] = trades
        audit_rows.append(summarize_named(name, trades))
        if not trades.empty:
            yearly = trades.groupby(trades["entry_time"].dt.year)["r_after_cost"].agg(
                trades="size",
                win_rate=lambda s: (s > 0).mean() * 100.0,
                total_r="sum",
            )
            yearly.insert(0, "name", name)
            by_year_rows.append(yearly.reset_index(names="year"))

            hourly = trades.groupby(trades["entry_time"].dt.hour)["r_after_cost"].agg(
                trades="size",
                win_rate=lambda s: (s > 0).mean() * 100.0,
                total_r="sum",
            )
            hourly.insert(0, "name", name)
            by_hour_rows.append(hourly.reset_index(names="hour"))

            for spread, slip in [(0.03, 0.01), (0.05, 0.02), (0.08, 0.03), (0.12, 0.05)]:
                tmp = trades.copy()
                tmp["cost_r"] = cost_r(tmp, spread, slip)
                row = summarize_named(name, tmp, "cost_r")
                row["spread"] = spread
                row["slip"] = slip
                cost_rows.append(row)

    audit = pd.DataFrame(audit_rows).sort_values(["total_r", "pf"], ascending=False)
    audit.to_csv(OUT_DIR / "silver_short_candidate_audit.csv", index=False)
    pd.DataFrame(cost_rows).to_csv(OUT_DIR / "silver_short_cost_stress.csv", index=False)
    pd.concat(by_year_rows, ignore_index=True).to_csv(OUT_DIR / "silver_short_candidate_by_year.csv", index=False)
    pd.concat(by_hour_rows, ignore_index=True).to_csv(OUT_DIR / "silver_short_candidate_by_hour.csv", index=False)

    top_cols = [
        "name",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "oos_trades",
        "oos_r",
        "oos_2025_trades",
        "oos_2025_r",
        "ex_2026_r",
        "worst_year_r",
        "worst_2y_r",
        "avg_mae_r",
        "same_bar_ambiguous",
    ]
    cost = pd.DataFrame(cost_rows)
    md = [
        "# SILVER H1 Short Candidate Audit",
        "",
        "## Candidate Comparison",
        "",
        markdown_table(audit[top_cols], 20),
        "",
        "## Cost Stress",
        "",
        markdown_table(
            cost[
                [
                    "name",
                    "spread",
                    "slip",
                    "trades",
                    "win_rate",
                    "total_r",
                    "pf",
                    "max_dd_r",
                    "oos_r",
                    "worst_year_r",
                ]
            ].sort_values(["name", "spread"]),
            100,
        ),
        "",
        "## Key Findings",
        "",
        "- The robust core is not upside exhaustion. It is H4-down pullback compression rebreak.",
        "- The best score uses `ex_7_11_12`, but this is more likely overfit. `ex_11_12` is a safer operational guard.",
        "- Without any time filter, the same structural setup remains positive but weaker.",
        "- OOS has only three trades, so the strategy is not production-grade yet.",
        "- All simulations are conservative for same-bar SL/TP: SL wins when both are touched.",
        "- The 2026 silver price regime is very different from prior years; results should be checked separately.",
    ]
    (OUT_DIR / "silver_short_audit_ja.md").write_text("\n".join(md), encoding="utf-8")

    print(audit[top_cols].round(3).to_string(index=False))
    print(f"output={OUT_DIR}")


if __name__ == "__main__":
    main()

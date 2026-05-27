#!/usr/bin/env python3
"""
Stability audit for WaveBox USDJPY H1 Rebreak v0.3.

This script intentionally uses the already-generated trade list so the audit is
about the selected rule's stability, not a new optimization pass.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_25"
AUDIT_DIR = OUT_DIR / "v0_3_stability_audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

TRADES_CSV = OUT_DIR / "trades.csv"
DATA_COVERAGE_CSV = OUT_DIR / "data_coverage.csv"


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def max_drawdown(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def max_losing_streak(values: Iterable[float]) -> int:
    cur = 0
    best = 0
    for value in values:
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
        }
    r = df["r_after_cost"]
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
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


def load_h1_base() -> pd.DataFrame:
    trades = pd.read_csv(TRADES_CSV, parse_dates=["signal_time", "entry_time", "exit_time"])
    h1 = trades[
        (trades["timeframe"] == "H1")
        & (trades["filter"] == "base")
        & (trades["box_bars"] == 8)
        & (trades["box_atr"] == 2.0)
        & (trades["target_model"] == "fixed_1_5R")
    ].copy()
    h1["entry_hour"] = h1["entry_time"].dt.hour
    h1["signal_hour"] = h1["signal_time"].dt.hour
    h1["year"] = h1["entry_time"].dt.year
    h1["month"] = h1["entry_time"].dt.month
    return h1


def apply_v03(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["retrace"].between(0.50, 0.764) & (~df["entry_hour"].isin([1, 6, 11, 14]))].copy()


def add_summary_row(rows: list[dict], label: str, df: pd.DataFrame, **extra: object) -> None:
    row = {"label": label, **summarize(df), **extra}
    rows.append(row)


def main() -> None:
    base = load_h1_base()
    v03 = apply_v03(base)

    # Stability by broad sample periods.
    period_rows: list[dict] = []
    add_summary_row(period_rows, "2014-2019", v03[(v03["year"] >= 2014) & (v03["year"] <= 2019)])
    add_summary_row(period_rows, "2020-2026", v03[(v03["year"] >= 2020) & (v03["year"] <= 2026)])
    add_summary_row(period_rows, "2014-2016", v03[(v03["year"] >= 2014) & (v03["year"] <= 2016)])
    add_summary_row(period_rows, "2017-2019", v03[(v03["year"] >= 2017) & (v03["year"] <= 2019)])
    add_summary_row(period_rows, "2020-2022", v03[(v03["year"] >= 2020) & (v03["year"] <= 2022)])
    add_summary_row(period_rows, "2023-2026", v03[(v03["year"] >= 2023) & (v03["year"] <= 2026)])
    period_df = pd.DataFrame(period_rows)
    period_df.to_csv(AUDIT_DIR / "period_stability.csv", index=False)

    # Leave-one-year-out.
    loo_rows: list[dict] = []
    for year in sorted(v03["year"].unique()):
        sub = v03[v03["year"] != year]
        add_summary_row(loo_rows, f"without_{year}", sub, removed_year=int(year))
    loo_df = pd.DataFrame(loo_rows).sort_values("total_r")
    loo_df.to_csv(AUDIT_DIR / "leave_one_year_out.csv", index=False)

    # Rolling windows.
    roll_rows: list[dict] = []
    years = sorted(v03["year"].unique())
    for width in [2, 3, 4]:
        for start in range(min(years), max(years) - width + 2):
            end = start + width - 1
            sub = v03[(v03["year"] >= start) & (v03["year"] <= end)]
            add_summary_row(roll_rows, f"{start}-{end}", sub, window_years=width, start_year=start, end_year=end)
    roll_df = pd.DataFrame(roll_rows).sort_values(["window_years", "total_r"])
    roll_df.to_csv(AUDIT_DIR / "rolling_windows.csv", index=False)

    # Parameter-neighborhood from the base trade universe.
    hour_sets = {
        "none": [],
        "ex_1": [1],
        "ex_1_6": [1, 6],
        "ex_1_6_14": [1, 6, 14],
        "ex_1_6_11_14": [1, 6, 11, 14],
        "ex_1_6_8_11_14": [1, 6, 8, 11, 14],
    }
    retrace_maxes = [0.618, 0.700, 0.764, 0.800, 0.886]
    neigh_rows: list[dict] = []
    for rmax in retrace_maxes:
        for hours_name, hours in hour_sets.items():
            sub = base[base["retrace"].between(0.50, rmax)]
            if hours:
                sub = sub[~sub["entry_hour"].isin(hours)]
            add_summary_row(neigh_rows, f"r50_{str(rmax).replace('.', '')}_{hours_name}", sub, retrace_max=rmax, hours=hours_name)
    neigh_df = pd.DataFrame(neigh_rows).sort_values(["retrace_max", "hours"])
    neigh_df.to_csv(AUDIT_DIR / "parameter_neighborhood.csv", index=False)

    # Entry-hour sensitivity: remove one bad hour at a time and compare.
    hour_rows: list[dict] = []
    r50_764 = base[base["retrace"].between(0.50, 0.764)].copy()
    add_summary_row(hour_rows, "no_hour_filter", r50_764)
    for h in range(24):
        add_summary_row(hour_rows, f"exclude_{h:02d}", r50_764[r50_764["entry_hour"] != h], removed_hour=h)
    hour_df = pd.DataFrame(hour_rows).sort_values("total_r", ascending=False)
    hour_df.to_csv(AUDIT_DIR / "single_hour_exclusion.csv", index=False)

    # Data quality notes from existing coverage.
    coverage = pd.read_csv(DATA_COVERAGE_CSV)
    coverage.to_csv(AUDIT_DIR / "data_coverage_copy.csv", index=False)

    report = [
        "# WaveBox v0.3 Stability Audit",
        "",
        "## Core",
        "",
        markdown_table(pd.DataFrame([{"label": "v0.3 core", **summarize(v03)}])),
        "",
        "## Period Stability",
        "",
        markdown_table(period_df),
        "",
        "## Leave-One-Year-Out",
        "",
        markdown_table(loo_df),
        "",
        "## Worst Rolling Windows",
        "",
        markdown_table(roll_df.head(20)),
        "",
        "## Parameter Neighborhood",
        "",
        markdown_table(neigh_df),
        "",
        "## Single Hour Exclusion Top",
        "",
        markdown_table(hour_df.head(12)),
        "",
        "## Data Coverage",
        "",
        markdown_table(coverage),
        "",
        "## Notes",
        "",
        "- `v0.3 core` uses entry-hour exclusion, not signal-hour exclusion.",
        "- The 2021 source file is one-minute-like, but the rule is evaluated on resampled H1 bars.",
        "- This audit does not prove future profitability; it checks whether the discovered rule is fragile inside the available sample.",
    ]
    (AUDIT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Cross-symbol audit for WaveBox H1 Rebreak.

This is a coarse robustness search, not a final optimizer. It avoids month
exclusions and reports OOS separately so symbol-specific candidates are not
accepted only because they look good in-sample.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
BASE_DIR = THIS_DIR / "results_2026_05_25"
CROSS_DIR = BASE_DIR / "cross_symbol_h1"
OUT_DIR = BASE_DIR / "cross_symbol_filter_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CROSS_TRADES = CROSS_DIR / "trades.csv"
OOS_START = pd.Timestamp("2025-01-01")


DIRECTION_FILTERS = ["both", "long", "short"]
H4_FILTERS = ["any", "not_oppose"]
RETRACE_FILTERS = {
    "r50_618": (0.50, 0.618),
    "r50_764": (0.50, 0.764),
    "r50_786": (0.50, 0.786),
    "r50_800": (0.50, 0.800),
    "r50_886": (0.50, 0.886),
}
HOUR_FILTERS = {
    "none": [],
    "ex_1": [1],
    "ex_1_6": [1, 6],
    "ex_1_6_14": [1, 6, 14],
    "ex_1_6_11_14": [1, 6, 11, 14],
}
RECOVERY_FILTERS = {
    "any": None,
    "rec25_85": (0.25, 0.85),
}
BODY_FILTERS = {
    "any": None,
    "ge45": "ge45",
}


PRESETS = {
    "base": {
        "direction": "both",
        "h4": "any",
        "retrace": "r50_886",
        "hours": "none",
        "recovery": "any",
        "body": "any",
    },
    "usdjpy_v03_strict": {
        "direction": "both",
        "h4": "any",
        "retrace": "r50_764",
        "hours": "ex_1_6_11_14",
        "recovery": "any",
        "body": "any",
    },
    "usdjpy_v04_filtered": {
        "direction": "both",
        "h4": "any",
        "retrace": "r50_786",
        "hours": "ex_1_6_14",
        "recovery": "any",
        "body": "any",
    },
    "h4_not_oppose_v04": {
        "direction": "both",
        "h4": "not_oppose",
        "retrace": "r50_786",
        "hours": "ex_1_6_14",
        "recovery": "any",
        "body": "any",
    },
    "a_plus_shallow": {
        "direction": "both",
        "h4": "any",
        "retrace": "r50_618",
        "hours": "ex_1_6_14",
        "recovery": "any",
        "body": "any",
    },
}


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
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "is_trades": 0,
            "is_r": 0.0,
            "oos_trades": 0,
            "oos_r": 0.0,
        }
    r = df["r_after_cost"]
    years = sorted(df["entry_time"].dt.year.unique())
    year_r = df.groupby(df["entry_time"].dt.year)["r_after_cost"].sum()
    rolling = []
    for start in years:
        sub = df[(df["entry_time"].dt.year >= start) & (df["entry_time"].dt.year <= start + 1)]
        if not sub.empty:
            rolling.append(float(sub["r_after_cost"].sum()))
    is_df = df[df["entry_time"] < OOS_START]
    oos_df = df[df["entry_time"] >= OOS_START]
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "worst_year_r": float(year_r.min()) if len(year_r) else np.nan,
        "worst_2y_r": float(min(rolling)) if rolling else np.nan,
        "is_trades": int(len(is_df)),
        "is_r": float(is_df["r_after_cost"].sum()) if len(is_df) else 0.0,
        "oos_trades": int(len(oos_df)),
        "oos_r": float(oos_df["r_after_cost"].sum()) if len(oos_df) else 0.0,
    }


def apply_filter(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = df
    if spec["direction"] != "both":
        out = out[out["direction"] == spec["direction"]]
    if spec["h4"] == "not_oppose":
        out = out[out["upper_oppose"] == 0]
    lo, hi = RETRACE_FILTERS[spec["retrace"]]
    out = out[out["retrace"].between(lo, hi, inclusive="both")]
    hours = HOUR_FILTERS[spec["hours"]]
    if hours:
        out = out[~out["hour"].isin(hours)]
    rec = RECOVERY_FILTERS[spec["recovery"]]
    if rec is not None:
        out = out[out["recovery"].between(rec[0], rec[1], inclusive="both")]
    body = BODY_FILTERS[spec["body"]]
    if body == "ge45":
        out = out[out["signal_body_ratio"] >= 0.45]
    return out.copy()


def score(row: dict) -> float:
    if row["trades"] < 25 or row["is_trades"] < 18:
        return -9999.0
    # OOS is low count, but strongly penalize clearly negative OOS.
    return (
        row["avg_r"] * 90.0
        + min(row["total_r"], 35.0) * 0.35
        + row["pf"] * 6.0
        + min(row["worst_2y_r"], 0.0) * 2.0
        + min(row["oos_r"], 0.0) * 2.0
        - row["max_dd_r"] * 0.45
        - max(row["max_losing_streak"] - 5, 0) * 1.0
    )


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


def main() -> None:
    trades = pd.read_csv(CROSS_TRADES, parse_dates=["signal_time", "entry_time", "exit_time"])
    trades["hour"] = trades["entry_time"].dt.hour
    trades["year"] = trades["entry_time"].dt.year

    preset_rows = []
    for symbol, group in trades.groupby("symbol"):
        for name, spec in PRESETS.items():
            filtered = apply_filter(group, spec)
            preset_rows.append({"symbol": symbol, "preset": name, **summarize(filtered), **spec})
    preset_df = pd.DataFrame(preset_rows).sort_values(["preset", "total_r"], ascending=[True, False])
    preset_df.to_csv(OUT_DIR / "preset_comparison.csv", index=False)

    search_rows = []
    keys = {
        "direction": DIRECTION_FILTERS,
        "h4": H4_FILTERS,
        "retrace": list(RETRACE_FILTERS),
        "hours": list(HOUR_FILTERS),
        "recovery": list(RECOVERY_FILTERS),
        "body": list(BODY_FILTERS),
    }
    for symbol, group in trades.groupby("symbol"):
        for combo in itertools.product(*keys.values()):
            spec = dict(zip(keys.keys(), combo))
            filtered = apply_filter(group, spec)
            row = {"symbol": symbol, **summarize(filtered), **spec}
            row["score"] = score(row)
            search_rows.append(row)
    search_df = pd.DataFrame(search_rows)
    search_df = search_df.sort_values(["symbol", "score"], ascending=[True, False])
    search_df.to_csv(OUT_DIR / "symbol_filter_grid.csv", index=False)

    top_df = (
        search_df[search_df["score"] > -9999]
        .groupby("symbol", group_keys=False)
        .head(8)
        .sort_values(["symbol", "score"], ascending=[True, False])
    )
    top_df.to_csv(OUT_DIR / "symbol_top_filters.csv", index=False)

    best_rows = []
    for symbol, group in search_df[search_df["score"] > -9999].groupby("symbol"):
        if group.empty:
            continue
        best = group.iloc[0].to_dict()
        if best["total_r"] >= 10 and best["pf"] >= 1.25 and best["worst_2y_r"] >= -5:
            verdict = "research_candidate"
        elif best["total_r"] > 0 and best["pf"] >= 1.05:
            verdict = "weak_candidate"
        else:
            verdict = "exclude"
        best["verdict"] = verdict
        best_rows.append(best)
    best_df = pd.DataFrame(best_rows).sort_values("score", ascending=False)
    best_df.to_csv(OUT_DIR / "symbol_best_verdict.csv", index=False)

    report = [
        "# WaveBox Cross-Symbol Filter Audit",
        "",
        "## Preset Comparison",
        "",
        "同じUSDJPY系プリセットを各銘柄へそのまま適用。",
        "",
        markdown_table(
            preset_df[
                [
                    "symbol",
                    "preset",
                    "trades",
                    "win_rate",
                    "total_r",
                    "avg_r",
                    "pf",
                    "max_dd_r",
                    "oos_trades",
                    "oos_r",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Best Coarse Filters By Symbol",
        "",
        markdown_table(
            best_df[
                [
                    "symbol",
                    "verdict",
                    "trades",
                    "win_rate",
                    "total_r",
                    "avg_r",
                    "pf",
                    "max_dd_r",
                    "worst_2y_r",
                    "oos_trades",
                    "oos_r",
                    "direction",
                    "h4",
                    "retrace",
                    "hours",
                    "recovery",
                    "body",
                ]
            ],
            max_rows=30,
        ),
        "",
        "## Top Filters",
        "",
        markdown_table(
            top_df[
                [
                    "symbol",
                    "score",
                    "trades",
                    "win_rate",
                    "total_r",
                    "avg_r",
                    "pf",
                    "max_dd_r",
                    "worst_2y_r",
                    "oos_trades",
                    "oos_r",
                    "direction",
                    "h4",
                    "retrace",
                    "hours",
                    "recovery",
                    "body",
                ]
            ],
            max_rows=80,
        ),
        "",
        "## Notes",
        "",
        "- This is not a final optimizer.",
        "- Month exclusions are intentionally excluded.",
        "- Symbols with weak OOS or negative rolling windows remain research only.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()

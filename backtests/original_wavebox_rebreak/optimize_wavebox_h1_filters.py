#!/usr/bin/env python3
"""
Iterative filter hardening for WaveBox H1 Rebreak.

Searches practical filters on the already-generated best candidate:
  USDJPY H1 / base / box 8 / 2.0 ATR / fixed 1.5R

The ranking is intentionally conservative:
  - enough trades
  - positive IS and OOS when possible
  - positive or less-bad worst rolling windows
  - smaller drawdown
  - cross-symbol side effects are reported separately, not optimized blindly
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
OUT_DIR = BASE_DIR / "h1_filter_search"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_TRADES = BASE_DIR / "trades.csv"
CROSS_TRADES = BASE_DIR / "cross_symbol_h1" / "trades.csv"
OOS_START = pd.Timestamp("2025-01-01")


HOUR_FILTERS = {
    "none": [],
    "ex_1": [1],
    "ex_1_6": [1, 6],
    "ex_1_6_14": [1, 6, 14],
    "ex_1_6_11_14": [1, 6, 11, 14],
    "ex_1_6_8_11_14": [1, 6, 8, 11, 14],
}

MONTH_FILTERS = {
    "none": [],
    "ex_aug": [8],
    "ex_aug_dec": [8, 12],
}

RETRACE_FILTERS = {
    "r50_886": (0.50, 0.886),
    "r50_764": (0.50, 0.764),
    "r50_618": (0.50, 0.618),
    "r618_886": (0.618, 0.886),
}

RECOVERY_FILTERS = {
    "any": None,
    "rec25_75": (0.25, 0.75),
    "rec25_85": (0.25, 0.85),
    "rec_le75": (0.0, 0.75),
}

BODY_FILTERS = {
    "any": None,
    "not_35_45": "not_35_45",
    "ge45": "ge45",
}

H4_FILTERS = {
    "any": "any",
    "not_oppose": "not_oppose",
    "align": "align",
}

DIRECTION_FILTERS = {
    "both": "both",
    "long": "long",
    "short": "short",
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


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "is_r": np.nan,
            "oos_r": np.nan,
            "oos_trades": 0,
        }
    r = df["r_after_cost"]
    year_r = df.groupby(df["entry_time"].dt.year)["r_after_cost"].sum()
    rolling = []
    years = sorted(df["entry_time"].dt.year.unique())
    for start in years:
        end = start + 1
        sub = df[(df["entry_time"].dt.year >= start) & (df["entry_time"].dt.year <= end)]
        if not sub.empty:
            rolling.append(float(sub["r_after_cost"].sum()))
    is_df = df[df["entry_time"] < OOS_START]
    oos_df = df[df["entry_time"] >= OOS_START]
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "worst_year_r": float(year_r.min()) if len(year_r) else np.nan,
        "worst_2y_r": float(min(rolling)) if rolling else np.nan,
        "is_r": float(is_df["r_after_cost"].sum()) if not is_df.empty else 0.0,
        "is_trades": int(len(is_df)),
        "oos_r": float(oos_df["r_after_cost"].sum()) if not oos_df.empty else 0.0,
        "oos_trades": int(len(oos_df)),
        "oos_wr": float((oos_df["r_after_cost"] > 0).mean() * 100) if not oos_df.empty else np.nan,
    }


def apply_filter(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = df.copy()
    if spec["direction"] != "both":
        out = out[out["direction"] == spec["direction"]]
    if spec["h4"] == "not_oppose":
        out = out[out["upper_oppose"] == 0]
    elif spec["h4"] == "align":
        out = out[out["upper_align"] > 0]
    lo, hi = RETRACE_FILTERS[spec["retrace"]]
    out = out[out["retrace"].between(lo, hi, inclusive="both")]
    rec = RECOVERY_FILTERS[spec["recovery"]]
    if rec is not None:
        out = out[out["recovery"].between(rec[0], rec[1], inclusive="both")]
    body = BODY_FILTERS[spec["body"]]
    if body == "not_35_45":
        out = out[(out["signal_body_ratio"] < 0.35) | (out["signal_body_ratio"] >= 0.45)]
    elif body == "ge45":
        out = out[out["signal_body_ratio"] >= 0.45]
    hours = HOUR_FILTERS[spec["hours"]]
    if hours:
        out = out[~out["hour"].isin(hours)]
    months = MONTH_FILTERS[spec["months"]]
    if months:
        out = out[~out["month"].isin(months)]
    return out


def score_row(row: dict) -> float:
    if row["trades"] < 35:
        return -9999.0
    if row["is_trades"] < 25:
        return -9999.0
    # Prefer robust conditions. Do not require OOS because only 2025-2026 has few trades.
    return (
        row["avg_r"] * 100.0
        + row["pf"] * 8.0
        + min(row["total_r"], 45.0) * 0.35
        + min(row["oos_r"], 10.0) * 0.6
        + min(row["worst_2y_r"], 0.0) * 1.5
        - row["max_dd_r"] * 0.35
    )


def load_usdjpy_base() -> pd.DataFrame:
    df = pd.read_csv(BASE_TRADES, parse_dates=["signal_time", "entry_time", "exit_time"])
    base = df[
        (df["timeframe"] == "H1")
        & (df["filter"] == "base")
        & (df["box_bars"] == 8)
        & (df["box_atr"] == 2.0)
        & (df["target_model"] == "fixed_1_5R")
    ].copy()
    base["hour"] = base["entry_time"].dt.hour
    base["month"] = base["entry_time"].dt.month
    return base


def load_cross_base() -> pd.DataFrame:
    df = pd.read_csv(CROSS_TRADES, parse_dates=["signal_time", "entry_time", "exit_time"])
    df["hour"] = df["entry_time"].dt.hour
    df["month"] = df["entry_time"].dt.month
    return df


def search_usdjpy(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = {
        "direction": list(DIRECTION_FILTERS),
        "h4": list(H4_FILTERS),
        "retrace": list(RETRACE_FILTERS),
        "recovery": list(RECOVERY_FILTERS),
        "body": list(BODY_FILTERS),
        "hours": list(HOUR_FILTERS),
        "months": list(MONTH_FILTERS),
    }
    for combo in itertools.product(*keys.values()):
        spec = dict(zip(keys.keys(), combo))
        frame = apply_filter(base, spec)
        summary = summarize(frame)
        summary.update(spec)
        summary["score"] = score_row(summary)
        rows.append(summary)
    return pd.DataFrame(rows).sort_values("score", ascending=False)


def cross_check(cross: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, spec_row in specs.iterrows():
        spec = {k: spec_row[k] for k in ["direction", "h4", "retrace", "recovery", "body", "hours", "months"]}
        filtered = apply_filter(cross, spec)
        for symbol, group in filtered.groupby("symbol"):
            s = summarize(group)
            s["symbol"] = symbol
            s.update(spec)
            rows.append(s)
    return pd.DataFrame(rows)


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
    base = load_usdjpy_base()
    cross = load_cross_base()
    search = search_usdjpy(base)
    good = search[(search["score"] > -9999) & (search["trades"] >= 35)].copy()
    top = good.head(50)
    cross_top = cross_check(cross, top.head(12))

    search.to_csv(OUT_DIR / "usdjpy_filter_grid.csv", index=False)
    top.to_csv(OUT_DIR / "usdjpy_top_filters.csv", index=False)
    cross_top.to_csv(OUT_DIR / "cross_check_top_filters.csv", index=False)

    cols = [
        "score",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "worst_year_r",
        "worst_2y_r",
        "is_r",
        "oos_r",
        "oos_trades",
        "direction",
        "h4",
        "retrace",
        "recovery",
        "body",
        "hours",
        "months",
    ]
    lines = [
        "# WaveBox H1 Filter Search",
        "",
        "対象: USDJPY H1 / box8 / 2.0ATR / 1.5R",
        "",
        "## Top Filters",
        "",
        markdown_table(top[cols], 50),
        "",
        "## Cross Symbol Check For Top 12",
        "",
        markdown_table(
            cross_top[
                [
                    "symbol",
                    "trades",
                    "win_rate",
                    "total_r",
                    "avg_r",
                    "pf",
                    "direction",
                    "h4",
                    "retrace",
                    "recovery",
                    "body",
                    "hours",
                    "months",
                ]
            ].sort_values(["direction", "h4", "retrace", "hours", "symbol"]),
            120,
        ),
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nTop")
    print(top[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()

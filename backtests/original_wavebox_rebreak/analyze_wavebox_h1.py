#!/usr/bin/env python3
"""
Additional diagnostics for the WaveBox H1 Rebreak candidate.

This script analyzes the best first-pass variant:
  H1 / base / box 8 / 2.0 ATR / fixed 1.5R

It checks whether the edge survives practical filters, yearly splits, rolling
windows, direction splits, time-of-day, and higher transaction-cost stress.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_25"
TRADES_PATH = OUT_DIR / "trades.csv"
ANALYSIS_DIR = OUT_DIR / "h1_hardening"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


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


def summarize(df: pd.DataFrame, group_cols: list[str] | None = None, r_col: str = "r_after_cost") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    if group_cols is None:
        groups = [((), df)]
        group_cols = []
    else:
        groups = df.groupby(group_cols, dropna=False)
    rows = []
    for key, group in groups:
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = group[r_col]
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": int(len(group)),
                "win_rate": float((r > 0).mean() * 100),
                "total_r": float(r.sum()),
                "avg_r": float(r.mean()),
                "pf": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "avg_hold_bars": float(group["bars_held"].mean()),
                "tp_rate": float((group["exit_reason"] == "TP").mean() * 100),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


def condition_frames(base: pd.DataFrame) -> dict[str, pd.DataFrame]:
    h4_not_oppose = base["upper_oppose"] == 0
    shallow = base["retrace"].between(0.50, 0.618, inclusive="both")
    body_not_dead_zone = (base["signal_body_ratio"] < 0.35) | (base["signal_body_ratio"] >= 0.45)
    recovery_mid = base["recovery"].between(0.25, 0.75, inclusive="both")
    box_tight = base["box_width_atr"] <= 1.6
    return {
        "all_h1_base_8_2_15r": base,
        "h4_not_oppose": base[h4_not_oppose],
        "shallow_50_618": base[shallow],
        "shallow_and_h4_not_oppose": base[shallow & h4_not_oppose],
        "body_not_35_45_dead_zone": base[body_not_dead_zone],
        "recovery_25_75": base[recovery_mid],
        "shallow_recovery_25_75": base[shallow & recovery_mid],
        "h4_not_oppose_body_filter": base[h4_not_oppose & body_not_dead_zone],
        "box_width_le_1_6": base[box_tight],
    }


def stress_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, frame in frames.items():
        if frame.empty:
            continue
        cost_r = frame["r_clean"] - frame["r_after_cost"]
        for mult in [1.0, 1.5, 2.0, 3.0]:
            tmp = frame.copy()
            tmp["r_stress"] = tmp["r_clean"] - cost_r * mult
            s = summarize(tmp, r_col="r_stress")
            if not s.empty:
                row = s.iloc[0].to_dict()
                row.insert if False else None
                row["condition"] = name
                row["cost_mult"] = mult
                rows.append(row)
    return pd.DataFrame(rows)[
        [
            "condition",
            "cost_mult",
            "trades",
            "win_rate",
            "total_r",
            "avg_r",
            "pf",
            "max_dd_r",
            "max_losing_streak",
            "tp_rate",
        ]
    ].sort_values(["condition", "cost_mult"])


def rolling_years(frame: pd.DataFrame, years: int = 2) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    out = []
    frame = frame.copy()
    frame["year"] = frame["entry_time"].dt.year
    all_years = sorted(frame["year"].unique())
    for start in all_years:
        end = start + years - 1
        sub = frame[(frame["year"] >= start) & (frame["year"] <= end)]
        if sub.empty:
            continue
        s = summarize(sub).iloc[0].to_dict()
        s["window"] = f"{start}-{end}"
        out.append(s)
    return pd.DataFrame(out)[
        ["window", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak", "tp_rate"]
    ]


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
    trades = pd.read_csv(TRADES_PATH, parse_dates=["signal_time", "entry_time", "exit_time"])
    base = trades[
        (trades["timeframe"] == "H1")
        & (trades["filter"] == "base")
        & (trades["box_bars"] == 8)
        & (trades["box_atr"] == 2.0)
        & (trades["target_model"] == "fixed_1_5R")
    ].copy()
    base["year"] = base["entry_time"].dt.year
    base["month"] = base["entry_time"].dt.month
    base["hour"] = base["entry_time"].dt.hour
    base["sample2"] = np.where(base["entry_time"] >= pd.Timestamp("2025-01-01"), "OOS_2025_2026", "IS_2014_2024")

    frames = condition_frames(base)
    condition_rows = []
    for name, frame in frames.items():
        s = summarize(frame)
        if not s.empty:
            row = s.iloc[0].to_dict()
            row["condition"] = name
            condition_rows.append(row)
    by_condition = pd.DataFrame(condition_rows)[
        [
            "condition",
            "trades",
            "win_rate",
            "total_r",
            "avg_r",
            "pf",
            "max_dd_r",
            "max_losing_streak",
            "tp_rate",
        ]
    ].sort_values("total_r", ascending=False)

    by_sample_condition_rows = []
    for name, frame in frames.items():
        s = summarize(frame, ["sample2"])
        if not s.empty:
            s.insert(0, "condition", name)
            by_sample_condition_rows.append(s)
    by_sample_condition = pd.concat(by_sample_condition_rows, ignore_index=True)

    by_year = summarize(base, ["year"]).sort_values("year")
    by_direction = summarize(base, ["direction"])
    by_hour = summarize(base, ["hour"]).sort_values("hour")
    by_month = summarize(base, ["month"]).sort_values("month")
    by_exit = summarize(base, ["exit_reason"])
    stress = stress_summary(frames)
    roll2 = rolling_years(base, years=2)
    roll3 = rolling_years(base, years=3)

    by_condition.to_csv(ANALYSIS_DIR / "summary_by_condition.csv", index=False)
    by_sample_condition.to_csv(ANALYSIS_DIR / "summary_by_sample_condition.csv", index=False)
    by_year.to_csv(ANALYSIS_DIR / "summary_by_year.csv", index=False)
    by_direction.to_csv(ANALYSIS_DIR / "summary_by_direction.csv", index=False)
    by_hour.to_csv(ANALYSIS_DIR / "summary_by_hour.csv", index=False)
    by_month.to_csv(ANALYSIS_DIR / "summary_by_month.csv", index=False)
    by_exit.to_csv(ANALYSIS_DIR / "summary_by_exit.csv", index=False)
    stress.to_csv(ANALYSIS_DIR / "cost_stress.csv", index=False)
    roll2.to_csv(ANALYSIS_DIR / "rolling_2y.csv", index=False)
    roll3.to_csv(ANALYSIS_DIR / "rolling_3y.csv", index=False)

    lines = [
        "# WaveBox H1 Rebreak 追加診断",
        "",
        "対象: `H1 / base / box 8本 / 2.0ATR / TP 1.5R`",
        "",
        "## 条件別",
        "",
        markdown_table(by_condition, 40),
        "",
        "## IS/OOS x 条件",
        "",
        markdown_table(by_sample_condition.sort_values(["condition", "sample2"]), 80),
        "",
        "## 年別",
        "",
        markdown_table(by_year, 30),
        "",
        "## 2年ローリング",
        "",
        markdown_table(roll2, 30),
        "",
        "## 3年ローリング",
        "",
        markdown_table(roll3, 30),
        "",
        "## 方向別",
        "",
        markdown_table(by_direction, 10),
        "",
        "## 時間帯別",
        "",
        markdown_table(by_hour, 30),
        "",
        "## 月別",
        "",
        markdown_table(by_month, 20),
        "",
        "## コスト耐性",
        "",
        markdown_table(stress, 80),
    ]
    (ANALYSIS_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {ANALYSIS_DIR / 'report_ja.md'}")
    print("\nBy condition")
    print(by_condition.to_string(index=False))
    print("\nBy year")
    print(by_year.to_string(index=False))
    print("\nCost stress")
    print(stress.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

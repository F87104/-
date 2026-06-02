#!/usr/bin/env python3
"""
One-by-one numeric sweeps for H4 T5 + MACD + BB.

Baseline:
    BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR
    / weak single-rebreak guard

Each sweep changes exactly one numeric condition from the baseline.  This is not
a grid optimizer.  The goal is to understand which number is carrying edge and
which number is just cosmetic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv"
)
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_one_by_one_numeric_sweeps"
OUT.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Rule:
    bb_lo: float = 0.75
    bb_hi: float = 0.95
    recovery_max: int = 16
    macd_min: float = 0.0
    bb_width_max: float = 4.0
    use_guard: bool = True
    guard_bb_hi: float = 0.95
    guard_macd_weak: float = 0.03


BASE_RULE = Rule()

SWEEPS: dict[str, list[Any]] = {
    "bb_lo": [0.60, 0.65, 0.70, 0.75, 0.80, 0.85],
    "bb_hi": [0.85, 0.90, 0.95, 1.00, 1.05],
    "recovery_max": [8, 10, 12, 14, 16, 18, 20, 24, 28, 32],
    "macd_min": [-0.02, 0.00, 0.01, 0.02, 0.03, 0.05, 0.08],
    "bb_width_max": [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0],
    "guard_macd_weak": [0.00, 0.01, 0.02, 0.03, 0.05, 0.08],
    "use_guard": [False, True],
}


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    curve = r.astype(float).cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(r: pd.Series) -> int:
    cur = 0
    best = 0
    for value in r.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def metrics(df: pd.DataFrame) -> dict[str, float | int]:
    r = df["r_after_cost"].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def prefixed(sample: pd.DataFrame, prefix: str) -> dict[str, float | int]:
    return {f"{prefix}_{key}": value for key, value in metrics(sample).items()}


def weak_rebreak_guard(df: pd.DataFrame, rule: Rule) -> pd.Series:
    trigger = df["trigger_type"].astype(str)
    weak = trigger.eq("rebreak") & (
        (df["bb_pos"] > rule.guard_bb_hi) | (df["macd_hist_slope3"] <= rule.guard_macd_weak)
    )
    return ~weak


def mask_for(df: pd.DataFrame, rule: Rule) -> pd.Series:
    mask = (
        df["bb_pos"].between(rule.bb_lo, rule.bb_hi)
        & df["signal_recovery_bars"].le(rule.recovery_max)
        & df["macd_hist_slope3"].gt(rule.macd_min)
        & df["bb_width_atr"].le(rule.bb_width_max)
    )
    if rule.use_guard:
        mask &= weak_rebreak_guard(df, rule)
    return mask.fillna(False)


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_No rows_"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    headers = list(view.columns)
    rows = [[fmt(value) for value in row] for row in view.itertuples(index=False, name=None)]
    widths = [len(str(h)) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    lines = []
    lines.append("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    lines.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows:
        lines.append("| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |")
    return "\n".join(lines)


def row_for(df: pd.DataFrame, parameter: str, value: Any, rule: Rule) -> dict[str, object]:
    sample = df[mask_for(df, rule)].copy()
    research = sample[sample["period"].eq("Research_2015_2024")]
    oos = sample[sample["period"].eq("OOS_2025_2026")]
    row: dict[str, object] = {
        "parameter": parameter,
        "value": value,
        "bb_lo": rule.bb_lo,
        "bb_hi": rule.bb_hi,
        "recovery_max": rule.recovery_max,
        "macd_min": rule.macd_min,
        "bb_width_max": rule.bb_width_max,
        "use_guard": rule.use_guard,
        "guard_macd_weak": rule.guard_macd_weak,
    }
    row.update(prefixed(sample, "all"))
    row.update(prefixed(research, "research"))
    row.update(prefixed(oos, "oos"))
    return row


def best_by_parameter(sweeps: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for parameter, group in sweeps.groupby("parameter"):
        candidates = group[
            (group["all_trades"] >= 12)
            & (group["research_trades"] >= 8)
            & (group["all_total_r"] > 0)
            & (group["research_total_r"] > 0)
            & (group["all_max_dd_r"] <= 4.5)
        ].copy()
        if candidates.empty:
            candidates = group.copy()
        candidates["score"] = (
            candidates["all_avg_r"].clip(-2, 2) * 0.35
            + candidates["research_avg_r"].clip(-2, 2) * 0.25
            + candidates["oos_avg_r"].clip(-2, 2) * 0.15
            + (candidates["all_pf"].replace(math.inf, 8).clip(0, 8) - 1) * 0.08
            - candidates["all_max_dd_r"].clip(0, 10) * 0.04
            + candidates["all_trades"].clip(0, 30) * 0.004
        )
        rows.append(candidates.sort_values("score", ascending=False).iloc[0].to_dict())
    return pd.DataFrame(rows).sort_values("score", ascending=False)


def main() -> None:
    trades = pd.read_csv(SRC, parse_dates=["entry_time", "signal_time", "exit_time"])

    rows = [row_for(trades, "BASE", "BASE", BASE_RULE)]
    for parameter, values in SWEEPS.items():
        param_rows = []
        for value in values:
            rule = replace(BASE_RULE, **{parameter: value})
            row = row_for(trades, parameter, value, rule)
            rows.append(row)
            param_rows.append(row)
        table = pd.DataFrame(param_rows)
        table.to_csv(OUT / f"sweep_{parameter}.csv", index=False)

    sweeps = pd.DataFrame(rows)
    sweeps.to_csv(OUT / "one_by_one_sweeps.csv", index=False)
    best = best_by_parameter(sweeps[sweeps["parameter"].ne("BASE")])
    best.to_csv(OUT / "best_by_parameter.csv", index=False)

    base_row = sweeps[sweeps["parameter"].eq("BASE")]
    report = [
        "# T5 One-by-One Numeric Sweeps 2026-06-02",
        "",
        "## 基準条件",
        "",
        "`BB 0.75-0.95 / 回復<=16 / MACD>0 / BB幅<=4ATR / 弱い単独rebreak除外`",
        "",
        "## 基準結果",
        "",
        md_table(
            base_row[
                [
                    "all_trades",
                    "all_win_rate",
                    "all_total_r",
                    "all_avg_r",
                    "all_pf",
                    "all_max_dd_r",
                    "research_trades",
                    "research_total_r",
                    "oos_trades",
                    "oos_total_r",
                ]
            ]
        ),
        "",
        "## 各パラメータの候補ベスト",
        "",
        md_table(
            best[
                [
                    "parameter",
                    "value",
                    "all_trades",
                    "all_win_rate",
                    "all_total_r",
                    "all_avg_r",
                    "all_pf",
                    "all_max_dd_r",
                    "research_total_r",
                    "oos_total_r",
                    "score",
                ]
            ]
        ),
        "",
    ]
    for parameter in SWEEPS:
        part = sweeps[sweeps["parameter"].eq(parameter)].copy()
        report.extend(
            [
                f"## Sweep: {parameter}",
                "",
                md_table(
                    part[
                        [
                            "value",
                            "all_trades",
                            "all_win_rate",
                            "all_total_r",
                            "all_avg_r",
                            "all_pf",
                            "all_max_dd_r",
                            "research_total_r",
                            "oos_total_r",
                        ]
                    ]
                ),
                "",
            ]
        )
    report.extend(
        [
            "## 出力",
            "",
            "- `one_by_one_sweeps.csv`",
            "- `best_by_parameter.csv`",
            "- `sweep_<parameter>.csv`",
        ]
    )
    (OUT / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT / 'report_ja.md'}")
    print("BASE")
    print(base_row.to_string(index=False))
    print("\nBEST BY PARAMETER")
    print(best[["parameter", "value", "all_trades", "all_win_rate", "all_total_r", "all_avg_r", "all_pf", "all_max_dd_r", "research_total_r", "oos_total_r", "score"]].to_string(index=False))


if __name__ == "__main__":
    main()

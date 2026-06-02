#!/usr/bin/env python3
"""
Recovery-bars sweep for H4 T5 + MACD + BB.

Fixed condition:
    BB 0.75-0.95 / MACD>0 / BB width<=4ATR / weak single-rebreak guard

Only signal_recovery_bars is varied to see whether <=16 is too strict, too
loose, or a robust middle point.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv"
)
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_recovery_sweep"
OUT.mkdir(parents=True, exist_ok=True)


RECOVERY_VALUES = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32]


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


def weak_rebreak_guard(df: pd.DataFrame) -> pd.Series:
    trigger = df["trigger_type"].astype(str)
    weak = trigger.eq("rebreak") & ((df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03))
    return ~weak


def base_mask(df: pd.DataFrame) -> pd.Series:
    return (
        df["bb_pos"].between(0.75, 0.95)
        & df["macd_hist_slope3"].gt(0)
        & df["bb_width_atr"].le(4.0)
        & weak_rebreak_guard(df)
    ).fillna(False)


def prefixed(sample: pd.DataFrame, prefix: str) -> dict[str, float | int]:
    return {f"{prefix}_{key}": value for key, value in metrics(sample).items()}


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows_"
    headers = list(df.columns)
    rows = [[fmt(value) for value in row] for row in df.itertuples(index=False, name=None)]
    widths = [len(str(h)) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    lines = []
    lines.append("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    lines.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows:
        lines.append("| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |")
    return "\n".join(lines)


def main() -> None:
    trades = pd.read_csv(SRC, parse_dates=["entry_time", "signal_time", "exit_time"])
    base = base_mask(trades)
    rows = []
    for recovery_max in RECOVERY_VALUES:
        sample = trades[base & trades["signal_recovery_bars"].le(recovery_max)].copy()
        research = sample[sample["period"].eq("Research_2015_2024")]
        oos = sample[sample["period"].eq("OOS_2025_2026")]
        row = {"recovery_max": recovery_max}
        row.update(prefixed(sample, "all"))
        row.update(prefixed(research, "research"))
        row.update(prefixed(oos, "oos"))
        rows.append(row)
    sweep = pd.DataFrame(rows)
    sweep.to_csv(OUT / "recovery_sweep.csv", index=False)

    # Incremental rows show what is added when the upper bound is relaxed.
    inc_rows = []
    prev = -1
    for recovery_max in RECOVERY_VALUES:
        bucket = trades[
            base
            & trades["signal_recovery_bars"].gt(prev)
            & trades["signal_recovery_bars"].le(recovery_max)
        ].copy()
        row = {
            "bucket": f"{prev + 1}-{recovery_max}" if prev >= 0 else f"<= {recovery_max}",
            "from_exclusive": prev,
            "to_inclusive": recovery_max,
        }
        row.update(metrics(bucket))
        inc_rows.append(row)
        prev = recovery_max
    incremental = pd.DataFrame(inc_rows)
    incremental.to_csv(OUT / "recovery_incremental_buckets.csv", index=False)

    # Main practical candidates to inspect directly.
    for recovery_max in [12, 14, 16, 18, 20, 24]:
        sample = trades[base & trades["signal_recovery_bars"].le(recovery_max)].copy()
        sample.to_csv(OUT / f"trades_recovery_le_{recovery_max}.csv", index=False)

    report = [
        "# T5 Recovery Bars Sweep 2026-06-02",
        "",
        "## 固定条件",
        "",
        "`BB 0.75-0.95 / MACD>0 / BB幅<=4ATR / 弱い単独rebreak除外` を固定し、`signal_recovery_bars` の上限だけを変更した。",
        "",
        "## 累積結果",
        "",
        md_table(sweep),
        "",
        "## 追加される回復帯ごとの成績",
        "",
        md_table(incremental),
        "",
        "## 読み方",
        "",
        "- 累積結果は `回復<=N` の実戦ルール候補。",
        "- 追加帯は、上限を緩めた時に増えるトレードだけの質を見る。",
        "- 追加帯が悪ければ、その手前を上限にするのが自然。",
        "",
        "## 出力",
        "",
        "- `recovery_sweep.csv`",
        "- `recovery_incremental_buckets.csv`",
        "- `trades_recovery_le_*.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT / 'report_ja.md'}")
    print(sweep.to_string(index=False))
    print()
    print(incremental.to_string(index=False))


if __name__ == "__main__":
    main()

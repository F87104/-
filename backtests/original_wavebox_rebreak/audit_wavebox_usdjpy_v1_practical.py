#!/usr/bin/env python3
"""
Practical audit for USDJPY H1 WaveBox Rebreak.

This script starts from the broad H1/base/box8/2.0ATR/1.5R trade list and
rebuilds the practical v1 rule set used for TradingView/Pine.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
BASE_DIR = THIS_DIR / "results_2026_05_25"
TRADES_PATH = BASE_DIR / "trades.csv"
OUT_DIR = BASE_DIR / "usdjpy_v1_practical_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OOS_START = pd.Timestamp("2025-01-01")
RNG_SEED = 87104
STANDARD_CANDIDATE = "standard_v1_wave1_quality"


CANDIDATES: dict[str, dict] = {
    "standard_v1_v04_filtered": {
        "description": "旧標準比較（1波剪定なし）: 戻し50%-78.6%、entry hour 1/6/14除外",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
    },
    "standard_v1_wave1_quality": {
        "description": "実戦標準 + 1波剪定: 1波3.0ATR以上、0.35ATR/本以上、24本以内",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
        "wave1_quality": True,
    },
    "standard_v1_wave1_balanced": {
        "description": "回数増加候補: 1波2.7ATR以上、0.32ATR/本以上、28本以内",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
        "wave1_quality": True,
        "wave1_min_atr": 2.7,
        "wave1_min_speed": 0.32,
        "wave1_max_bars": 28,
    },
    "standard_v1_wave1_loose": {
        "description": "回数増加候補: 1波2.5ATR以上、0.30ATR/本以上、30本以内",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
        "wave1_quality": True,
        "wave1_min_atr": 2.5,
        "wave1_min_speed": 0.30,
        "wave1_max_bars": 30,
    },
    "expanded_v1_082_ex16_wave1_balanced": {
        "description": "回数増加候補: 戻し50%-82%、entry hour 1/6除外、1波Balanced",
        "retrace": (0.50, 0.820),
        "exclude_hours": [1, 6],
        "h4": "any",
        "direction": "both",
        "wave1_quality": True,
        "wave1_min_atr": 2.7,
        "wave1_min_speed": 0.32,
        "wave1_max_bars": 28,
    },
    "conservative_v03_strict": {
        "description": "旧保守比較（1波剪定なし）: 戻し50%-76.4%、entry hour 1/6/11/14除外",
        "retrace": (0.50, 0.764),
        "exclude_hours": [1, 6, 11, 14],
        "h4": "any",
        "direction": "both",
    },
    "simple_v04_less_fit": {
        "description": "旧標準の過剰最適化を弱めた比較（1波剪定なし）: 戻し50%-78.6%、entry hour 1/6除外",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6],
        "h4": "any",
        "direction": "both",
    },
    "standard_a_h4_not_oppose": {
        "description": "旧標準比較（1波剪定なし）: H4逆行なし",
        "retrace": (0.50, 0.786),
        "exclude_hours": [1, 6, 14],
        "h4": "not_oppose",
        "direction": "both",
    },
    "standard_h4_and_shallow_compare": {
        "description": "旧標準比較（1波剪定なし）: H4逆行なし + 戻し50%-61.8%",
        "retrace": (0.50, 0.618),
        "exclude_hours": [1, 6, 14],
        "h4": "not_oppose",
        "direction": "both",
    },
    "standard_shallow_no_h4": {
        "description": "旧標準比較（1波剪定なし）: 戻し50%-61.8%",
        "retrace": (0.50, 0.618),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
    },
    "standard_wave1_quality_shallow": {
        "description": "1波剪定 + A+浅い押し: 戻し50%-61.8%",
        "retrace": (0.50, 0.618),
        "exclude_hours": [1, 6, 14],
        "h4": "any",
        "direction": "both",
        "wave1_quality": True,
    },
}


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(values[values <= 0].sum())
    if gross_loss < 0:
        return gross_profit / abs(gross_loss)
    return math.inf if gross_profit > 0 else math.nan


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
                "tp_rate": float((group["exit_reason"] == "TP").mean() * 100),
                "avg_hold_bars": float(group["bars_held"].mean()),
                "median_hold_bars": float(group["bars_held"].median()),
            }
        )
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


def load_base() -> pd.DataFrame:
    trades = pd.read_csv(TRADES_PATH, parse_dates=["signal_time", "entry_time", "exit_time"])
    base = trades[
        (trades["symbol"] == "USDJPY")
        & (trades["timeframe"] == "H1")
        & (trades["filter"] == "base")
        & (trades["box_bars"] == 8)
        & (trades["box_atr"] == 2.0)
        & (trades["target_model"] == "fixed_1_5R")
    ].copy()
    base["year"] = base["entry_time"].dt.year
    base["month"] = base["entry_time"].dt.month
    base["hour"] = base["entry_time"].dt.hour
    base["sample"] = np.where(base["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    base = base.sort_values("entry_time").reset_index(drop=True)
    return base


def apply_candidate(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = df.copy()
    lo, hi = spec["retrace"]
    out = out[out["retrace"].between(lo, hi, inclusive="both")]
    hours = spec["exclude_hours"]
    if hours:
        out = out[~out["hour"].isin(hours)]
    if spec["h4"] == "not_oppose":
        out = out[out["upper_oppose"] == 0]
    elif spec["h4"] == "align":
        out = out[out["upper_align"] > 0]
    if spec["direction"] != "both":
        out = out[out["direction"] == spec["direction"]]
    if spec.get("wave1_quality", False):
        min_atr = spec.get("wave1_min_atr", 3.0)
        min_speed = spec.get("wave1_min_speed", 0.35)
        max_bars = spec.get("wave1_max_bars", 24)
        speed = out["wave1_atr"] / out["wave1_bars"].clip(lower=1)
        out = out[(out["wave1_atr"] >= min_atr) & (speed >= min_speed) & (out["wave1_bars"] <= max_bars)]
    return out.sort_values("entry_time").reset_index(drop=True)


def rolling_years(df: pd.DataFrame, years: int) -> pd.DataFrame:
    rows = []
    all_years = range(int(df["year"].min()), int(df["year"].max()) + 1)
    for start in all_years:
        end = start + years - 1
        sub = df[(df["year"] >= start) & (df["year"] <= end)]
        if sub.empty:
            continue
        row = summarize(sub).iloc[0].to_dict()
        row["window"] = f"{start}-{end}"
        row["start_year"] = start
        row["end_year"] = end
        rows.append(row)
    return pd.DataFrame(rows)


def frequency_stats(df: pd.DataFrame, label: str) -> dict:
    if df.empty:
        return {"candidate": label, "trades": 0}
    first_month = df["entry_time"].min().to_period("M")
    last_month = df["entry_time"].max().to_period("M")
    months = pd.period_range(first_month, last_month, freq="M")
    counts = df.groupby(df["entry_time"].dt.to_period("M")).size().reindex(months, fill_value=0)
    intervals_days = df["entry_time"].sort_values().diff().dt.total_seconds().dropna() / 86400.0
    return {
        "candidate": label,
        "trades": int(len(df)),
        "first_trade": df["entry_time"].min(),
        "last_trade": df["entry_time"].max(),
        "calendar_months": int(len(counts)),
        "months_with_signal": int((counts > 0).sum()),
        "months_without_signal": int((counts == 0).sum()),
        "avg_trades_per_year": float(len(df) / max((df["entry_time"].max() - df["entry_time"].min()).days / 365.25, 0.01)),
        "avg_trades_per_calendar_month": float(len(df) / max(len(counts), 1)),
        "median_interval_days": float(intervals_days.median()) if len(intervals_days) else math.nan,
        "max_interval_days": float(intervals_days.max()) if len(intervals_days) else math.nan,
    }


def cost_stress(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame()
    cost_r = df["r_clean"] - df["r_after_cost"]
    for mult in [1, 2, 3, 5, 10]:
        tmp = df.copy()
        tmp["r_stress"] = tmp["r_clean"] - cost_r * mult
        row = summarize(tmp, r_col="r_stress").iloc[0].to_dict()
        row["candidate"] = label
        row["cost_mult"] = mult
        rows.append(row)
    return pd.DataFrame(rows)


def monte_carlo(df: pd.DataFrame, label: str, n: int = 5000) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(RNG_SEED)
    values = df["r_after_cost"].to_numpy(dtype=float)
    perm_dd = []
    boot_total = []
    boot_dd = []
    for _ in range(n):
        shuffled = values.copy()
        rng.shuffle(shuffled)
        perm_dd.append(max_drawdown(shuffled))
        boot = rng.choice(values, size=len(values), replace=True)
        boot_total.append(float(boot.sum()))
        boot_dd.append(max_drawdown(boot))
    rows = []
    for kind, arr in [
        ("permutation_dd", np.asarray(perm_dd)),
        ("bootstrap_total_r", np.asarray(boot_total)),
        ("bootstrap_dd", np.asarray(boot_dd)),
    ]:
        rows.append(
            {
                "candidate": label,
                "metric": kind,
                "p05": float(np.quantile(arr, 0.05)),
                "p50": float(np.quantile(arr, 0.50)),
                "p90": float(np.quantile(arr, 0.90)),
                "p95": float(np.quantile(arr, 0.95)),
                "p99": float(np.quantile(arr, 0.99)),
            }
        )
    return pd.DataFrame(rows)


def grade_standard(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rank"] = "B"
    out.loc[out["upper_oppose"] == 0, "rank"] = "A"
    out.loc[out["retrace"] <= 0.618, "rank"] = "A+"
    return out


def write_report(
    candidate_summary: pd.DataFrame,
    rank_summary: pd.DataFrame,
    sample_summary: pd.DataFrame,
    yearly_standard: pd.DataFrame,
    rolling2_standard: pd.DataFrame,
    rolling3_standard: pd.DataFrame,
    direction_standard: pd.DataFrame,
    hour_standard: pd.DataFrame,
    month_standard: pd.DataFrame,
    frequency: pd.DataFrame,
    stress: pd.DataFrame,
    mc: pd.DataFrame,
) -> None:
    lines = [
        "# USDJPY H1 WaveBox Rebreak v1 Practical Audit",
        "",
        "## 結論",
        "",
        f"- 実戦標準は `{STANDARD_CANDIDATE}` とする。",
        "- これは `H1 / box8 / 2.0ATR / TP 1.5R / 戻し50%-78.6% / entry hour 1,6,14除外 / 1波剪定あり`。",
        "- `conservative_v03_strict` は保守表示、`A` と `A+` はロット調整・優先順位に使う。",
        "- A+はH4条件ではなく、戻し50%-61.8%の浅い押しを最優先にする。",
        "- 1波剪定は `3.0ATR以上 / 0.35ATR以上/本 / 24本以内` を標準候補にする。",
        "- この監査は過去検証であり、実運用前に20-30件のフォワード確認が必要。",
        "",
        "## Candidate Summary",
        "",
        markdown_table(candidate_summary, 30),
        "",
        "## Standard Rank Summary",
        "",
        markdown_table(rank_summary, 20),
        "",
        "## IS/OOS Summary",
        "",
        markdown_table(sample_summary, 40),
        "",
        "## Standard Yearly",
        "",
        markdown_table(yearly_standard, 40),
        "",
        "## Standard Rolling 2Y",
        "",
        markdown_table(rolling2_standard, 40),
        "",
        "## Standard Rolling 3Y",
        "",
        markdown_table(rolling3_standard, 40),
        "",
        "## Standard Direction",
        "",
        markdown_table(direction_standard, 20),
        "",
        "## Standard Entry Hour",
        "",
        markdown_table(hour_standard, 30),
        "",
        "## Standard Month",
        "",
        markdown_table(month_standard, 20),
        "",
        "## Frequency",
        "",
        markdown_table(frequency, 20),
        "",
        "## Cost Stress",
        "",
        markdown_table(stress, 40),
        "",
        "## Monte Carlo",
        "",
        markdown_table(mc, 20),
        "",
        "## 実戦メモ",
        "",
        "- B: 標準シグナル。最小ロットまたは観察から開始。",
        "- A: H4逆行なし。標準より心理的に扱いやすいが、単独では過信しない。",
        "- A+: 戻し50%-61.8%。この検証では最も質が高い。",
        "- 1回リスクはフォワード完了まで0.25%-0.5%を上限にする。",
        "- 連敗4回、または月間-3Rで停止して目視レビューする。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    base = load_base()
    candidate_frames = {name: apply_candidate(base, spec) for name, spec in CANDIDATES.items()}

    candidate_rows = []
    sample_rows = []
    frequency_rows = []
    stress_rows = []
    mc_rows = []
    for name, frame in candidate_frames.items():
        summary = summarize(frame).iloc[0].to_dict() if not frame.empty else {}
        summary["candidate"] = name
        summary["description"] = CANDIDATES[name]["description"]
        candidate_rows.append(summary)

        sample = summarize(frame, ["sample"])
        if not sample.empty:
            sample.insert(0, "candidate", name)
            sample_rows.append(sample)

        frequency_rows.append(frequency_stats(frame, name))
        stress_rows.append(cost_stress(frame, name))
        mc_rows.append(monte_carlo(frame, name, n=5000))
        frame.to_csv(OUT_DIR / f"trades_{name}.csv", index=False)

    candidate_summary = pd.DataFrame(candidate_rows)
    candidate_summary = candidate_summary[
        [
            "candidate",
            "description",
            "trades",
            "win_rate",
            "total_r",
            "avg_r",
            "pf",
            "max_dd_r",
            "max_losing_streak",
            "tp_rate",
            "avg_hold_bars",
        ]
    ].sort_values("total_r", ascending=False)

    standard = grade_standard(candidate_frames[STANDARD_CANDIDATE])
    rank_summary = summarize(standard, ["rank"]).sort_values("rank")
    sample_summary = pd.concat(sample_rows, ignore_index=True)
    yearly_standard = summarize(standard, ["year"]).sort_values("year")
    rolling2_standard = rolling_years(standard, 2).sort_values("start_year")
    rolling3_standard = rolling_years(standard, 3).sort_values("start_year")
    direction_standard = summarize(standard, ["direction"]).sort_values("direction")
    hour_standard = summarize(standard, ["hour"]).sort_values("hour")
    month_standard = summarize(standard, ["month"]).sort_values("month")
    frequency = pd.DataFrame(frequency_rows)
    stress = pd.concat(stress_rows, ignore_index=True)
    mc = pd.concat(mc_rows, ignore_index=True)

    candidate_summary.to_csv(OUT_DIR / "summary_candidates.csv", index=False)
    rank_summary.to_csv(OUT_DIR / "summary_standard_by_rank.csv", index=False)
    sample_summary.to_csv(OUT_DIR / "summary_by_sample.csv", index=False)
    yearly_standard.to_csv(OUT_DIR / "standard_by_year.csv", index=False)
    rolling2_standard.to_csv(OUT_DIR / "standard_rolling_2y.csv", index=False)
    rolling3_standard.to_csv(OUT_DIR / "standard_rolling_3y.csv", index=False)
    direction_standard.to_csv(OUT_DIR / "standard_by_direction.csv", index=False)
    hour_standard.to_csv(OUT_DIR / "standard_by_hour.csv", index=False)
    month_standard.to_csv(OUT_DIR / "standard_by_month.csv", index=False)
    frequency.to_csv(OUT_DIR / "frequency.csv", index=False)
    stress.to_csv(OUT_DIR / "cost_stress.csv", index=False)
    mc.to_csv(OUT_DIR / "monte_carlo.csv", index=False)

    write_report(
        candidate_summary,
        rank_summary,
        sample_summary,
        yearly_standard,
        rolling2_standard,
        rolling3_standard,
        direction_standard,
        hour_standard,
        month_standard,
        frequency,
        stress,
        mc,
    )

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(candidate_summary.to_string(index=False))


if __name__ == "__main__":
    main()

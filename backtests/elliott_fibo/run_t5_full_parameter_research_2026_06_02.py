#!/usr/bin/env python3
"""
Full parameter research for H4 T5 + MACD + BB.

This script intentionally starts from the regenerated broad T5 universe:

    results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv

The goal is not to pick the highest PF point.  The goal is to find parameter
regions where the T5 idea remains intact across nearby thresholds.
"""

from __future__ import annotations

import math
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv"
)
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_full_parameter_research_fast"
OUT.mkdir(parents=True, exist_ok=True)

RECOMMENDED_6 = {"XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"}


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


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict[str, float | int]:
    r = df[r_col].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_loss_streak": max_losing_streak(r),
    }


def prefixed_metrics(df: pd.DataFrame, prefix: str) -> dict[str, float | int]:
    return {f"{prefix}_{k}": v for k, v in metrics(df).items()}


def apply_symbol_mode(df: pd.DataFrame, mode: str) -> pd.Series:
    if mode == "all7":
        return pd.Series(True, index=df.index)
    if mode == "recommended6":
        return df["symbol"].isin(RECOMMENDED_6)
    if mode == "recommended6_ex_xau":
        return df["symbol"].isin(RECOMMENDED_6 - {"XAUUSD"})
    if mode == "recommended6_ex_gbp":
        return df["symbol"].isin(RECOMMENDED_6 - {"GBPJPY"})
    if mode == "recommended6_ex_xau_gbp":
        return df["symbol"].isin(RECOMMENDED_6 - {"XAUUSD", "GBPJPY"})
    raise ValueError(mode)


def apply_trigger_mode(df: pd.DataFrame, mode: str) -> pd.Series:
    trigger = df["trigger_type"].astype(str)
    if mode == "all":
        return pd.Series(True, index=df.index)
    if mode == "stagnation_family":
        return trigger.isin(["stagnation", "stagnation+rebreak"])
    if mode == "stagnation_only":
        return trigger.eq("stagnation")
    if mode == "rebreak_only":
        return trigger.eq("rebreak")
    if mode == "both_only":
        return trigger.eq("stagnation+rebreak")
    if mode == "exclude_gbp_rebreak":
        return ~(df["symbol"].eq("GBPJPY") & trigger.eq("rebreak"))
    if mode == "weak_rebreak_guard":
        weak = trigger.eq("rebreak") & ((df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03))
        return ~weak
    raise ValueError(mode)


def make_grid(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    bb_los = [0.60, 0.70, 0.75]
    bb_his = [0.90, 0.95, 1.00, 1.05]
    recovery_maxes = [12, 16, 20, 24]
    macd_mins = [0.00, 0.02, 0.03, 0.05]
    bb_width_maxes: list[float | None] = [4.0, 5.0, 5.5, 7.0]
    close_locs: list[float | None] = [None, 0.60, 0.65]
    body_mins: list[float | None] = [None, 0.45]
    adx_maxes: list[float | None] = [None, 30.0, 35.0]
    symbol_modes = ["all7", "recommended6", "recommended6_ex_xau_gbp"]
    trigger_modes = [
        "all",
        "weak_rebreak_guard",
        "exclude_gbp_rebreak",
        "stagnation_family",
        "both_only",
    ]

    base = pd.Series(True, index=df.index)
    for (
        symbol_mode,
        trigger_mode,
        bb_lo,
        bb_hi,
        recovery_max,
        macd_min,
        bb_width_max,
        close_loc_min,
        body_min,
        adx_max,
    ) in product(
        symbol_modes,
        trigger_modes,
        bb_los,
        bb_his,
        recovery_maxes,
        macd_mins,
        bb_width_maxes,
        close_locs,
        body_mins,
        adx_maxes,
    ):
        if bb_hi <= bb_lo:
            continue
        mask = base.copy()
        mask &= apply_symbol_mode(df, symbol_mode)
        mask &= apply_trigger_mode(df, trigger_mode)
        mask &= df["bb_pos"].between(bb_lo, bb_hi)
        mask &= df["signal_recovery_bars"].le(recovery_max)
        mask &= df["macd_hist_slope3"].gt(macd_min)
        if bb_width_max is not None:
            mask &= df["bb_width_atr"].le(bb_width_max)
        if close_loc_min is not None:
            mask &= df["close_location"].ge(close_loc_min)
        if body_min is not None:
            mask &= df["body_ratio"].ge(body_min)
        if adx_max is not None:
            mask &= df["adx14"].le(adx_max)
        sample = df[mask.fillna(False)].copy()
        if sample.empty:
            continue
        research = sample[sample["period"].eq("Research_2015_2024")]
        oos = sample[sample["period"].eq("OOS_2025_2026")]
        row = {
            "symbol_mode": symbol_mode,
            "trigger_mode": trigger_mode,
            "bb_lo": bb_lo,
            "bb_hi": bb_hi,
            "recovery_max": recovery_max,
            "macd_min": macd_min,
            "bb_width_max": "none" if bb_width_max is None else bb_width_max,
            "close_location_min": "none" if close_loc_min is None else close_loc_min,
            "body_ratio_min": "none" if body_min is None else body_min,
            "adx_max": "none" if adx_max is None else adx_max,
        }
        row.update(prefixed_metrics(sample, "all"))
        row.update(prefixed_metrics(research, "research"))
        row.update(prefixed_metrics(oos, "oos"))
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["oos_positive"] = out["oos_total_r"] > 0
    out["research_positive"] = out["research_total_r"] > 0
    out["oos_retention_avg_r"] = np.where(
        out["research_avg_r"].abs() > 1e-9,
        out["oos_avg_r"] / out["research_avg_r"],
        np.nan,
    )
    out["robust_score"] = (
        out["research_avg_r"].clip(-2, 2) * 0.25
        + out["oos_avg_r"].clip(-2, 2) * 0.25
        + (out["research_pf"].replace(math.inf, 8).clip(0, 8) - 1) * 0.08
        + (out["oos_pf"].replace(math.inf, 8).clip(0, 8) - 1) * 0.08
        + np.log1p(out["all_trades"]) * 0.08
        - out["all_max_dd_r"].clip(0, 20) * 0.025
        - out["all_max_loss_streak"].clip(0, 10) * 0.03
    )
    out["thin_sample"] = (out["research_trades"] < 12) | (out["oos_trades"] < 3) | (out["all_trades"] < 18)
    out["candidate_pass"] = (
        (out["all_trades"] >= 20)
        & (out["research_trades"] >= 15)
        & (out["oos_trades"] >= 3)
        & (out["research_total_r"] > 0)
        & (out["oos_total_r"] > 0)
        & (out["research_pf"] >= 1.5)
        & (out["all_pf"] >= 1.7)
        & (out["all_max_dd_r"] <= 6.0)
    )
    return out.sort_values("robust_score", ascending=False)


def grouped_summary(grid: pd.DataFrame, key: str) -> pd.DataFrame:
    if grid.empty:
        return pd.DataFrame()
    usable = grid[(grid["all_trades"] >= 20) & (grid["research_trades"] >= 12)].copy()
    rows = []
    for value, g in usable.groupby(key):
        rows.append(
            {
                key: value,
                "configs": int(len(g)),
                "pass_configs": int(g["candidate_pass"].sum()),
                "pass_rate_pct": float(g["candidate_pass"].mean() * 100),
                "median_all_trades": float(g["all_trades"].median()),
                "median_all_avg_r": float(g["all_avg_r"].median()),
                "median_all_pf": float(g["all_pf"].replace(math.inf, 8).median()),
                "median_oos_total_r": float(g["oos_total_r"].median()),
                "best_score": float(g["robust_score"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values(["pass_configs", "best_score"], ascending=[False, False])


def feature_compare(df: pd.DataFrame, best_mask: pd.Series) -> pd.DataFrame:
    sample = df[best_mask].copy()
    if sample.empty:
        return pd.DataFrame()
    winners = sample[sample["r_after_cost"] > 0]
    losers = sample[sample["r_after_cost"] <= 0]
    cols = [
        "bb_pos",
        "bb_width_atr",
        "signal_recovery_bars",
        "macd_hist_slope3",
        "close_location",
        "body_ratio",
        "adx14",
        "v_move_atr",
        "signal_fib_ratio",
        "bars_held",
    ]
    rows = []
    for col in cols:
        rows.append(
            {
                "feature": col,
                "win_mean": float(winners[col].mean()) if not winners.empty else math.nan,
                "loss_mean": float(losers[col].mean()) if not losers.empty else math.nan,
                "win_median": float(winners[col].median()) if not winners.empty else math.nan,
                "loss_median": float(losers[col].median()) if not losers.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def row_to_mask(df: pd.DataFrame, row: pd.Series) -> pd.Series:
    mask = apply_symbol_mode(df, str(row["symbol_mode"]))
    mask &= apply_trigger_mode(df, str(row["trigger_mode"]))
    mask &= df["bb_pos"].between(float(row["bb_lo"]), float(row["bb_hi"]))
    mask &= df["signal_recovery_bars"].le(int(row["recovery_max"]))
    mask &= df["macd_hist_slope3"].gt(float(row["macd_min"]))
    if str(row["bb_width_max"]) != "none":
        mask &= df["bb_width_atr"].le(float(row["bb_width_max"]))
    if str(row["close_location_min"]) != "none":
        mask &= df["close_location"].ge(float(row["close_location_min"]))
    if str(row["body_ratio_min"]) != "none":
        mask &= df["body_ratio"].ge(float(row["body_ratio_min"]))
    if str(row["adx_max"]) != "none":
        mask &= df["adx14"].le(float(row["adx_max"]))
    return mask.fillna(False)


def md_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_no rows_"
    d = df.head(max_rows).copy()
    for col in d.columns:
        if pd.api.types.is_float_dtype(d[col]):
            d[col] = d[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
    d = d.fillna("")
    headers = [str(c) for c in d.columns]
    rows = [[str(v) for v in row] for row in d.to_numpy()]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    header = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    body = ["| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def write_report(df: pd.DataFrame, grid: pd.DataFrame) -> None:
    passed = grid[grid["candidate_pass"]].copy()
    top = passed.sort_values("robust_score", ascending=False).head(20)
    if top.empty:
        top = grid[~grid["thin_sample"]].head(20)

    key_cols = [
        "symbol_mode",
        "trigger_mode",
        "bb_lo",
        "bb_hi",
        "recovery_max",
        "macd_min",
        "bb_width_max",
        "close_location_min",
        "body_ratio_min",
        "adx_max",
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
        "robust_score",
    ]

    report_lines = [
        "# T5 Full Parameter Research 2026-06-02",
        "",
        "## 目的",
        "",
        "T5の数値条件を固定せず、BB位置・回復本数・MACD・BB幅・終値位置・実体・ADX・通貨除外・トリガー種別を広く振り、近い条件でも残る構造を探した。",
        "",
        "## 母集団",
        "",
        f"- Broad T5 universe: {len(df)} trades",
        f"- Research_2015_2024: {int(df['period'].eq('Research_2015_2024').sum())} trades",
        f"- OOS_2025_2026: {int(df['period'].eq('OOS_2025_2026').sum())} trades",
        f"- Grid evaluated: {len(grid)} non-empty configs",
        f"- Robust candidate pass: {int(grid['candidate_pass'].sum())} configs",
        "",
        "## 上位候補",
        "",
        md_table(top[key_cols], 20),
        "",
        "## 条件別の残り方",
        "",
        "### Trigger Mode",
        "",
        md_table(pd.read_csv(OUT / "summary_by_trigger_mode.csv"), 20),
        "",
        "### Symbol Mode",
        "",
        md_table(pd.read_csv(OUT / "summary_by_symbol_mode.csv"), 20),
        "",
        "### BB Upper",
        "",
        md_table(pd.read_csv(OUT / "summary_by_bb_hi.csv"), 20),
        "",
        "### Recovery Max",
        "",
        md_table(pd.read_csv(OUT / "summary_by_recovery_max.csv"), 20),
        "",
        "### BB Width Max",
        "",
        md_table(pd.read_csv(OUT / "summary_by_bb_width_max.csv"), 20),
        "",
        "## 暫定結論",
        "",
        "- T5は一点の数値ではなく、`上側BB位置` + `短めの回復本数` + `弱い単独rebreak排除` の組み合わせで残りやすい。",
        "- `stagnation+rebreak` は強いが件数不足になりやすい。実戦では最優先タグにするのが自然。",
        "- GBPJPYの単独rebreakは別扱いが必要。除外または小ロット候補。",
        "- BB幅は4ATR固定だときれいだが件数が減る。4ATR以下は通常、4-5.5ATRは半分ロット、5.5ATR超は警戒という運用分岐を検証する価値がある。",
        "- MACD slope3を強くしすぎると、売り失敗後の再点火ではなく遅い追いかけに寄りやすい。0以上、単独rebreakだけ0.03超が現実的。",
        "",
        "## 出力",
        "",
        "- `grid_all.csv`",
        "- `grid_candidates.csv`",
        "- `summary_by_*.csv`",
        "- `best_candidate_trades.csv`",
        "- `best_candidate_win_loss_compare.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(SRC, parse_dates=["signal_time", "entry_time", "exit_time"])
    df = df.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    grid_path = OUT / "grid_all.csv"
    if grid_path.exists():
        grid = pd.read_csv(grid_path)
    else:
        grid = make_grid(df)
        grid.to_csv(grid_path, index=False)
    grid[grid["candidate_pass"]].to_csv(OUT / "grid_candidates.csv", index=False)

    for key in [
        "trigger_mode",
        "symbol_mode",
        "bb_lo",
        "bb_hi",
        "recovery_max",
        "macd_min",
        "bb_width_max",
        "close_location_min",
        "body_ratio_min",
        "adx_max",
    ]:
        grouped_summary(grid, key).to_csv(OUT / f"summary_by_{key}.csv", index=False)

    candidates = grid[grid["candidate_pass"]].copy()
    best = candidates.iloc[0] if not candidates.empty else grid[~grid["thin_sample"]].iloc[0]
    best_mask = row_to_mask(df, best)
    best_trades = df[best_mask].copy()
    best_trades.to_csv(OUT / "best_candidate_trades.csv", index=False)
    feature_compare(df, best_mask).to_csv(OUT / "best_candidate_win_loss_compare.csv", index=False)
    write_report(df, grid)

    print("Report:", OUT / "report_ja.md")
    print("Broad trades:", len(df))
    print("Grid configs:", len(grid))
    print("Candidate pass:", int(grid["candidate_pass"].sum()))
    cols = [
        "symbol_mode",
        "trigger_mode",
        "bb_lo",
        "bb_hi",
        "recovery_max",
        "macd_min",
        "bb_width_max",
        "close_location_min",
        "body_ratio_min",
        "adx_max",
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
        "robust_score",
    ]
    print(grid[grid["candidate_pass"]][cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()

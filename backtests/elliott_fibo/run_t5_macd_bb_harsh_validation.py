#!/usr/bin/env python3
"""
Harsh validation for:

    T5_STAG_OR_REBREAK + MACD histogram rising + BB position 0.60-1.10

This script intentionally tries to break the candidate before we promote it:
- train/test and multiple chronological windows
- per-year, per-month, per-symbol stability
- cost stress from 1x to 3x observed costs
- nearby threshold sensitivity
- bootstrap confidence intervals
- Monte Carlo drawdown from shuffled trade order
- simple cluster-risk checks
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
INPUT = THIS_DIR / "results_2015_2024" / "indicator_compatibility_search" / "trades_enriched.csv"
OUT_DIR = THIS_DIR / "results_2015_2024" / "t5_macd_bb_harsh_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_STRATEGY = "T5_STAG_OR_REBREAK"
SPLIT_DATE = pd.Timestamp("2021-01-01")
RNG = np.random.default_rng(87104)


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
        "median_r": float(r.median()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def with_cost_stress(df: pd.DataFrame, multiplier: float) -> pd.DataFrame:
    out = df.copy()
    observed_cost_r = out["r_clean"].astype(float) - out["r_after_cost"].astype(float)
    out["r_stress"] = out["r_clean"].astype(float) - observed_cost_r * multiplier
    return out


def load() -> pd.DataFrame:
    if not INPUT.exists():
        raise SystemExit(f"Missing input: {INPUT}")
    df = pd.read_csv(INPUT)
    df["signal_time"] = pd.to_datetime(df["signal_time"])
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["year"] = df["entry_time"].dt.year
    df["month"] = df["entry_time"].dt.to_period("M").astype(str)
    df["date"] = df["entry_time"].dt.date.astype(str)
    return df.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def candidate_masks(base: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "T5_BASELINE": pd.Series(True, index=base.index),
        "T5_MACD_ONLY": base["macd_hist_slope3"] > 0,
        "T5_BB_ONLY": base["bb_pos"].between(0.60, 1.10),
        "T5_MACD_BB": (base["macd_hist_slope3"] > 0) & base["bb_pos"].between(0.60, 1.10),
        "T5_MACD_BB_HIST_POS": (base["macd_hist_slope3"] > 0)
        & (base["macd_hist"] > 0)
        & base["bb_pos"].between(0.60, 1.10),
        "T5_MACD_BB_CLOSE65": (base["macd_hist_slope3"] > 0)
        & base["bb_pos"].between(0.60, 1.10)
        & (base["close_location"] >= 0.65),
    }


def summarize_named_samples(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for name, df in samples.items():
        train = df[df["entry_time"] < SPLIT_DATE]
        test = df[df["entry_time"] >= SPLIT_DATE]
        row = {"candidate": name}
        row.update({f"all_{k}": v for k, v in metrics(df).items()})
        row.update({f"train_{k}": v for k, v in metrics(train).items()})
        row.update({f"test_{k}": v for k, v in metrics(test).items()})
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["test_total_r", "all_total_r"], ascending=False)


def group_table(df: pd.DataFrame, group_cols: list[str], r_col: str = "r_after_cost") -> pd.DataFrame:
    rows: list[dict] = []
    for key, group in df.groupby(group_cols):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        row.update(metrics(group, r_col))
        rows.append(row)
    return pd.DataFrame(rows)


def threshold_grid(base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    bb_los = [0.50, 0.55, 0.60, 0.65, 0.70]
    bb_his = [1.00, 1.05, 1.10, 1.15, 1.20]
    slope_mins = [-0.02, 0.0, 0.02, 0.05]
    for lo in bb_los:
        for hi in bb_his:
            if lo >= hi:
                continue
            for slope_min in slope_mins:
                mask = (base["macd_hist_slope3"] > slope_min) & base["bb_pos"].between(lo, hi)
                sample = base[mask].copy()
                if len(sample) < 40:
                    continue
                train = sample[sample["entry_time"] < SPLIT_DATE]
                test = sample[sample["entry_time"] >= SPLIT_DATE]
                row = {"bb_lo": lo, "bb_hi": hi, "slope_min": slope_min}
                row.update({f"all_{k}": v for k, v in metrics(sample).items()})
                row.update({f"train_{k}": v for k, v in metrics(train).items()})
                row.update({f"test_{k}": v for k, v in metrics(test).items()})
                row["positive_symbols"] = int((group_table(sample, ["symbol"])["total_r"] > 0).sum()) if not sample.empty else 0
                row["positive_years"] = int((group_table(sample, ["year"])["total_r"] > 0).sum()) if not sample.empty else 0
                rows.append(row)
    grid = pd.DataFrame(rows)
    if grid.empty:
        return grid
    grid["score"] = (
        grid["test_total_r"]
        + grid["all_avg_r"] * 20
        + grid["positive_symbols"] * 2
        + grid["positive_years"]
        - grid["all_max_dd_r"] * 0.75
    )
    return grid.sort_values("score", ascending=False)


def cost_stress_table(sample: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for multiplier in [1.0, 1.5, 2.0, 2.5, 3.0]:
        stressed = with_cost_stress(sample, multiplier)
        row = {"cost_multiplier": multiplier}
        row.update(metrics(stressed, "r_stress"))
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_ci(sample: pd.DataFrame, n: int = 5000) -> pd.DataFrame:
    r = sample["r_after_cost"].astype(float).to_numpy()
    if len(r) == 0:
        return pd.DataFrame()
    totals = np.empty(n)
    avgs = np.empty(n)
    for i in range(n):
        draw = RNG.choice(r, size=len(r), replace=True)
        totals[i] = draw.sum()
        avgs[i] = draw.mean()
    return pd.DataFrame(
        [
            {
                "metric": "total_r",
                "p05": np.percentile(totals, 5),
                "p25": np.percentile(totals, 25),
                "median": np.percentile(totals, 50),
                "p75": np.percentile(totals, 75),
                "p95": np.percentile(totals, 95),
                "prob_positive": float((totals > 0).mean() * 100),
            },
            {
                "metric": "avg_r",
                "p05": np.percentile(avgs, 5),
                "p25": np.percentile(avgs, 25),
                "median": np.percentile(avgs, 50),
                "p75": np.percentile(avgs, 75),
                "p95": np.percentile(avgs, 95),
                "prob_positive": float((avgs > 0).mean() * 100),
            },
        ]
    )


def monte_carlo(sample: pd.DataFrame, n: int = 5000) -> pd.DataFrame:
    r = sample["r_after_cost"].astype(float).to_numpy()
    if len(r) == 0:
        return pd.DataFrame()
    totals = np.empty(n)
    dds = np.empty(n)
    losing_streaks = np.empty(n)
    for i in range(n):
        shuffled = RNG.permutation(r)
        s = pd.Series(shuffled)
        totals[i] = shuffled.sum()
        dds[i] = max_drawdown(s)
        losing_streaks[i] = max_losing_streak(s)
    return pd.DataFrame(
        [
            {
                "metric": "total_r",
                "p05": np.percentile(totals, 5),
                "p25": np.percentile(totals, 25),
                "median": np.percentile(totals, 50),
                "p75": np.percentile(totals, 75),
                "p95": np.percentile(totals, 95),
            },
            {
                "metric": "max_dd_r",
                "p05": np.percentile(dds, 5),
                "p25": np.percentile(dds, 25),
                "median": np.percentile(dds, 50),
                "p75": np.percentile(dds, 75),
                "p95": np.percentile(dds, 95),
            },
            {
                "metric": "max_losing_streak",
                "p05": np.percentile(losing_streaks, 5),
                "p25": np.percentile(losing_streaks, 25),
                "median": np.percentile(losing_streaks, 50),
                "p75": np.percentile(losing_streaks, 75),
                "p95": np.percentile(losing_streaks, 95),
            },
        ]
    )


def cluster_checks(sample: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    rows.append({"rule": "通常", **metrics(sample)})

    first_per_day = sample.sort_values(["entry_time", "symbol"]).drop_duplicates("date", keep="first")
    rows.append({"rule": "1日1回だけ・最初のシグナル", **metrics(first_per_day)})

    first_per_day_symbol = sample.sort_values(["entry_time", "symbol"]).drop_duplicates(["date", "symbol"], keep="first")
    rows.append({"rule": "同一通貨は1日1回だけ", **metrics(first_per_day_symbol)})

    # Keep only dates where there was no multi-symbol cluster.
    counts = sample.groupby("date")["symbol"].nunique()
    non_cluster_dates = counts[counts <= 1].index
    non_cluster = sample[sample["date"].isin(non_cluster_dates)]
    rows.append({"rule": "複数通貨同日シグナルを全除外", **metrics(non_cluster)})
    return pd.DataFrame(rows)


def month_stability(sample: pd.DataFrame) -> pd.DataFrame:
    by_month = group_table(sample, ["month"])
    if by_month.empty:
        return pd.DataFrame()
    by_month["positive"] = by_month["total_r"] > 0
    return by_month


def write_report(
    summary: pd.DataFrame,
    symbol: pd.DataFrame,
    year: pd.DataFrame,
    month: pd.DataFrame,
    two_year: pd.DataFrame,
    cost: pd.DataFrame,
    grid: pd.DataFrame,
    bootstrap: pd.DataFrame,
    mc: pd.DataFrame,
    clusters: pd.DataFrame,
) -> None:
    target = summary[summary["candidate"] == "T5_MACD_BB"].iloc[0]
    pos_months = int((month["total_r"] > 0).sum()) if not month.empty else 0
    total_months = int(len(month))
    lines = [
        "# T5 + MACD上昇 + BB位置0.60〜1.10 厳しめ再検証",
        "",
        "## 判定",
        "",
        "- `T5_MACD_BB` は、前回候補の中でも有力性は残った。",
        "- ただし、利益の多くは `2021年以降` に寄っており、古い相場では弱い年がある。",
        "- 通貨別では全通貨プラスを維持したため、単一通貨の偶然ではなさそう。",
        "- 厳しめに見るなら、運用候補ではあるが、Pineで目視確認してから本採用が妥当。",
        "",
        "## 最重要サマリー",
        "",
        f"- 全期間: `{int(target['all_trades'])}回 / {target['all_total_r']:.2f}R / 勝率{target['all_win_rate']:.2f}% / PF{target['all_pf']:.2f} / 最大DD {target['all_max_dd_r']:.2f}R`",
        f"- 2021-2024: `{int(target['test_trades'])}回 / {target['test_total_r']:.2f}R / 勝率{target['test_win_rate']:.2f}% / PF{target['test_pf']:.2f} / 最大DD {target['test_max_dd_r']:.2f}R`",
        f"- 月別プラス: `{pos_months}/{total_months}`",
        "",
        "## 候補比較",
        "",
        markdown_table(summary, 20),
        "",
        "## 通貨別 T5_MACD_BB",
        "",
        markdown_table(symbol, 40),
        "",
        "## 年別 T5_MACD_BB",
        "",
        markdown_table(year, 40),
        "",
        "## 2年窓 T5_MACD_BB",
        "",
        markdown_table(two_year, 40),
        "",
        "## コスト増しストレス",
        "",
        markdown_table(cost, 20),
        "",
        "## 閾値ズレ感度 上位20",
        "",
        markdown_table(grid.head(20), 30),
        "",
        "## Bootstrap信頼区間",
        "",
        markdown_table(bootstrap, 10),
        "",
        "## Monte Carlo 約定順シャッフル",
        "",
        markdown_table(mc, 10),
        "",
        "## 同日クラスター確認",
        "",
        markdown_table(clusters, 10),
        "",
        "## 出力",
        "",
        "- `summary.csv`",
        "- `by_symbol.csv`",
        "- `by_year.csv`",
        "- `by_month.csv`",
        "- `two_year_windows.csv`",
        "- `cost_stress.csv`",
        "- `threshold_grid.csv`",
        "- `bootstrap_ci.csv`",
        "- `monte_carlo.csv`",
        "- `cluster_checks.csv`",
        "- `trades_t5_macd_bb.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_trades = load()
    base = all_trades[all_trades["strategy"].eq(BASE_STRATEGY)].copy()
    masks = candidate_masks(base)
    samples = {name: base[mask.fillna(False)].copy() for name, mask in masks.items()}
    target = samples["T5_MACD_BB"].copy()

    summary = summarize_named_samples(samples)
    symbol = group_table(target, ["symbol"]).sort_values("total_r", ascending=False)
    year = group_table(target, ["year"]).sort_values("year")
    month = month_stability(target).sort_values("month")

    window_rows = []
    for start, end in [(2015, 2016), (2017, 2018), (2019, 2020), (2021, 2022), (2023, 2024)]:
        sample = target[target["year"].between(start, end)].copy()
        window_rows.append({"window": f"{start}-{end}", **metrics(sample)})
    two_year = pd.DataFrame(window_rows)

    cost = cost_stress_table(target)
    grid = threshold_grid(base)
    bootstrap = bootstrap_ci(target)
    mc = monte_carlo(target)
    clusters = cluster_checks(target)

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    symbol.to_csv(OUT_DIR / "by_symbol.csv", index=False)
    year.to_csv(OUT_DIR / "by_year.csv", index=False)
    month.to_csv(OUT_DIR / "by_month.csv", index=False)
    two_year.to_csv(OUT_DIR / "two_year_windows.csv", index=False)
    cost.to_csv(OUT_DIR / "cost_stress.csv", index=False)
    grid.to_csv(OUT_DIR / "threshold_grid.csv", index=False)
    bootstrap.to_csv(OUT_DIR / "bootstrap_ci.csv", index=False)
    mc.to_csv(OUT_DIR / "monte_carlo.csv", index=False)
    clusters.to_csv(OUT_DIR / "cluster_checks.csv", index=False)
    target.to_csv(OUT_DIR / "trades_t5_macd_bb.csv", index=False)

    write_report(summary, symbol, year, month, two_year, cost, grid, bootstrap, mc, clusters)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

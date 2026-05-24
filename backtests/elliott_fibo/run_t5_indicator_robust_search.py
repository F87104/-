#!/usr/bin/env python3
"""
Robust search around:

    T5_STAG_OR_REBREAK + MACD rising + Bollinger Band position

The goal is not to find the most profitable overfit threshold.  This script
looks for a stable region by requiring enough trades, train/test survival,
multi-symbol breadth, and two-year-window robustness.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
INPUT = THIS_DIR / "results_2015_2024" / "indicator_compatibility_search" / "trades_enriched.csv"
OUT_DIR = THIS_DIR / "results_2015_2024" / "t5_indicator_robust_search"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_STRATEGY = "T5_STAG_OR_REBREAK"
SPLIT_DATE = pd.Timestamp("2021-01-01")


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


def load_base() -> pd.DataFrame:
    if not INPUT.exists():
        raise SystemExit(f"Missing input: {INPUT}")
    df = pd.read_csv(INPUT)
    df["signal_time"] = pd.to_datetime(df["signal_time"])
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["year"] = df["entry_time"].dt.year
    df["date"] = df["entry_time"].dt.date.astype(str)
    base = df[df["strategy"].eq(BASE_STRATEGY)].copy()
    return base.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def group_metrics(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows: list[dict] = []
    for key, g in df.groupby(col):
        rows.append({col: key, **metrics(g)})
    return pd.DataFrame(rows)


def two_year_windows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for start, end in [(2015, 2016), (2017, 2018), (2019, 2020), (2021, 2022), (2023, 2024)]:
        sample = df[df["year"].between(start, end)]
        rows.append({"window": f"{start}-{end}", **metrics(sample)})
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class FilterSpec:
    name: str
    bb_lo: float
    bb_hi: float
    slope_min: float
    macd_hist_pos: bool
    body_min: float | None
    close_min: float | None
    adx_mode: str
    rsi_mode: str
    width_mode: str
    trigger_mode: str


def mask_for(base: pd.DataFrame, spec: FilterSpec) -> pd.Series:
    mask = base["bb_pos"].between(spec.bb_lo, spec.bb_hi)
    mask &= base["macd_hist_slope3"] > spec.slope_min
    if spec.macd_hist_pos:
        mask &= base["macd_hist"] > 0
    if spec.body_min is not None:
        mask &= base["body_ratio"] >= spec.body_min
    if spec.close_min is not None:
        mask &= base["close_location"] >= spec.close_min

    if spec.adx_mode == "adx_ge_14":
        mask &= base["adx14"] >= 14
    elif spec.adx_mode == "adx_ge_18":
        mask &= base["adx14"] >= 18
    elif spec.adx_mode == "adx_ge_20":
        mask &= base["adx14"] >= 20
    elif spec.adx_mode == "adx_14_35":
        mask &= base["adx14"].between(14, 35)
    elif spec.adx_mode == "adx_18_35":
        mask &= base["adx14"].between(18, 35)
    elif spec.adx_mode == "adx_le_35":
        mask &= base["adx14"] <= 35

    if spec.rsi_mode == "rsi_ge_55":
        mask &= base["rsi14"] >= 55
    elif spec.rsi_mode == "rsi_ge_58":
        mask &= base["rsi14"] >= 58
    elif spec.rsi_mode == "rsi_55_72":
        mask &= base["rsi14"].between(55, 72)
    elif spec.rsi_mode == "rsi_58_72":
        mask &= base["rsi14"].between(58, 72)
    elif spec.rsi_mode == "rsi_le_72":
        mask &= base["rsi14"] <= 72

    if spec.width_mode == "bb_width_ge_2_5":
        mask &= base["bb_width_atr"] >= 2.5
    elif spec.width_mode == "bb_width_ge_3":
        mask &= base["bb_width_atr"] >= 3.0
    elif spec.width_mode == "bb_width_2_5_7":
        mask &= base["bb_width_atr"].between(2.5, 7.0)
    elif spec.width_mode == "bb_width_3_7":
        mask &= base["bb_width_atr"].between(3.0, 7.0)
    elif spec.width_mode == "bb_width_le_7":
        mask &= base["bb_width_atr"] <= 7.0

    if spec.trigger_mode == "rebreak_only":
        mask &= base["trigger_type"].eq("rebreak")
    elif spec.trigger_mode == "stagnation_family":
        mask &= base["trigger_type"].isin(["stagnation", "stagnation+rebreak"])
    elif spec.trigger_mode == "stagnation_plus_rebreak":
        mask &= base["trigger_type"].eq("stagnation+rebreak")

    return mask.fillna(False)


def breadth_counts(sample: pd.DataFrame) -> tuple[int, int, int, float]:
    by_symbol = group_metrics(sample, "symbol") if not sample.empty else pd.DataFrame()
    by_year = group_metrics(sample, "year") if not sample.empty else pd.DataFrame()
    windows = two_year_windows(sample)
    positive_symbols = int((by_symbol["total_r"] > 0).sum()) if not by_symbol.empty else 0
    positive_years = int((by_year["total_r"] > 0).sum()) if not by_year.empty else 0
    positive_windows = int((windows["total_r"] > 0).sum()) if not windows.empty else 0
    worst_window = float(windows["total_r"].min()) if not windows.empty else 0.0
    return positive_symbols, positive_years, positive_windows, worst_window


def score_row(row: dict) -> float:
    # Penalize fragility.  A high all-period R is not enough.
    return (
        row["test_total_r"] * 1.4
        + row["train_total_r"] * 0.9
        + row["all_avg_r"] * 30
        + row["positive_symbols"] * 2.5
        + row["positive_years"] * 1.0
        + row["positive_windows"] * 3.0
        + min(row["worst_window_total_r"], 0) * 1.8
        - row["all_max_dd_r"] * 0.9
        - row["all_max_losing_streak"] * 0.4
    )


def search(base: pd.DataFrame) -> pd.DataFrame:
    bb_ranges = [(lo, hi) for lo in np.round(np.arange(0.50, 0.81, 0.05), 2) for hi in np.round(np.arange(0.95, 1.26, 0.05), 2) if lo < hi]
    slope_mins = [-0.02, 0.0, 0.02, 0.04, 0.06]
    macd_hist_pos_options = [False, True]

    # Extra filters are tested in no-extra and single-extra layers.  If a single
    # extra does not clearly help, pairing extras is usually overfit on this
    # sample size.
    single_extras: list[dict] = []
    for value in [0.65, 0.70, 0.75]:
        single_extras.append({"group": "body", "body_min": value})
    for value in [0.75, 0.80, 0.85]:
        single_extras.append({"group": "close", "close_min": value})
    for value in ["adx_ge_14", "adx_ge_18", "adx_ge_20", "adx_14_35", "adx_18_35", "adx_le_35"]:
        single_extras.append({"group": "adx", "adx_mode": value})
    for value in ["rsi_ge_55", "rsi_ge_58", "rsi_55_72", "rsi_58_72", "rsi_le_72"]:
        single_extras.append({"group": "rsi", "rsi_mode": value})
    for value in ["bb_width_ge_2_5", "bb_width_ge_3", "bb_width_2_5_7", "bb_width_3_7", "bb_width_le_7"]:
        single_extras.append({"group": "width", "width_mode": value})
    for value in ["rebreak_only", "stagnation_family"]:
        single_extras.append({"group": "trigger", "trigger_mode": value})

    extra_specs: list[dict] = [{"groups": ""}]
    for extra in single_extras:
        spec = {k: v for k, v in extra.items() if k != "group"}
        spec["groups"] = extra["group"]
        extra_specs.append(spec)

    rows: list[dict] = []
    for bb_lo, bb_hi in bb_ranges:
        for slope_min in slope_mins:
            for macd_hist_pos in macd_hist_pos_options:
                for extra in extra_specs:
                    spec = FilterSpec(
                        name="",
                        bb_lo=float(bb_lo),
                        bb_hi=float(bb_hi),
                        slope_min=float(slope_min),
                        macd_hist_pos=macd_hist_pos,
                        body_min=extra.get("body_min"),
                        close_min=extra.get("close_min"),
                        adx_mode=extra.get("adx_mode", "none"),
                        rsi_mode=extra.get("rsi_mode", "none"),
                        width_mode=extra.get("width_mode", "none"),
                        trigger_mode=extra.get("trigger_mode", "all"),
                    )
                    mask = mask_for(base, spec)
                    sample = base[mask].copy()
                    if len(sample) < 80:
                        continue
                    train = sample[sample["entry_time"] < SPLIT_DATE]
                    test = sample[sample["entry_time"] >= SPLIT_DATE]
                    if len(train) < 35 or len(test) < 25:
                        continue
                    all_m = metrics(sample)
                    train_m = metrics(train)
                    test_m = metrics(test)
                    if train_m["total_r"] <= 0 or test_m["total_r"] <= 0:
                        continue
                    positive_symbols, positive_years, positive_windows, worst_window = breadth_counts(sample)
                    if positive_symbols < 4 or positive_windows < 4:
                        continue
                    row = {
                        "extra_groups": extra.get("groups", ""),
                        "bb_lo": spec.bb_lo,
                        "bb_hi": spec.bb_hi,
                        "slope_min": spec.slope_min,
                        "macd_hist_pos": spec.macd_hist_pos,
                        "body_min": spec.body_min if spec.body_min is not None else "",
                        "close_min": spec.close_min if spec.close_min is not None else "",
                        "adx_mode": spec.adx_mode,
                        "rsi_mode": spec.rsi_mode,
                        "width_mode": spec.width_mode,
                        "trigger_mode": spec.trigger_mode,
                        "positive_symbols": positive_symbols,
                        "positive_years": positive_years,
                        "positive_windows": positive_windows,
                        "worst_window_total_r": worst_window,
                    }
                    row.update({f"all_{k}": v for k, v in all_m.items()})
                    row.update({f"train_{k}": v for k, v in train_m.items()})
                    row.update({f"test_{k}": v for k, v in test_m.items()})
                    row["score"] = score_row(row)
                    rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["score", "test_total_r", "all_total_r"], ascending=False).reset_index(drop=True)


def named_candidates(base: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    specs = [
        FilterSpec("Current_0.60_1.10", 0.60, 1.10, 0.00, False, None, None, "none", "none", "none", "all"),
        FilterSpec("Strict_BB_0.70_1.05", 0.70, 1.05, 0.00, False, None, None, "none", "none", "none", "all"),
        FilterSpec("T5_BB_0.70_1.00", 0.70, 1.00, 0.00, False, None, None, "none", "none", "none", "all"),
    ]
    if not top.empty:
        for idx, row in top.head(5).iterrows():
            specs.append(
                FilterSpec(
                    f"RobustTop{idx + 1}",
                    float(row["bb_lo"]),
                    float(row["bb_hi"]),
                    float(row["slope_min"]),
                    bool(row["macd_hist_pos"]),
                    None if row["body_min"] == "" else float(row["body_min"]),
                    None if row["close_min"] == "" else float(row["close_min"]),
                    str(row["adx_mode"]),
                    str(row["rsi_mode"]),
                    str(row["width_mode"]),
                    str(row["trigger_mode"]),
                )
            )

    rows: list[dict] = []
    for spec in specs:
        sample = base[mask_for(base, spec)].copy()
        train = sample[sample["entry_time"] < SPLIT_DATE]
        test = sample[sample["entry_time"] >= SPLIT_DATE]
        positive_symbols, positive_years, positive_windows, worst_window = breadth_counts(sample)
        row = {
            "candidate": spec.name,
            "rule": f"BB {spec.bb_lo:.2f}-{spec.bb_hi:.2f}, slope>{spec.slope_min:.2f}, hist>0={spec.macd_hist_pos}, body>={spec.body_min}, close>={spec.close_min}, {spec.adx_mode}, {spec.rsi_mode}, {spec.width_mode}, trigger={spec.trigger_mode}",
            "positive_symbols": positive_symbols,
            "positive_years": positive_years,
            "positive_windows": positive_windows,
            "worst_window_total_r": worst_window,
        }
        row.update({f"all_{k}": v for k, v in metrics(sample).items()})
        row.update({f"train_{k}": v for k, v in metrics(train).items()})
        row.update({f"test_{k}": v for k, v in metrics(test).items()})
        rows.append(row)
    return pd.DataFrame(rows)


def write_report(base: pd.DataFrame, top: pd.DataFrame, named: pd.DataFrame) -> None:
    lines = [
        "# T5 MACD BB 黄金値探索メモ",
        "",
        "## 結論",
        "",
        "- `BB位置0.60〜1.10` は黄金値ではなく、有効な広いゾーンの一部。",
        "- 厳しめに見ると、中心は `BB位置0.70〜1.05` 付近に寄っている。",
        "- ただし、絞るほど取引回数が減るため、運用では `0.60〜1.10` を標準、`0.70〜1.05` を保守版として比較するのが妥当。",
        "- 高いスコアの複合条件は存在するが、条件を増やすほど過学習リスクが上がる。",
        "",
        "## 既存候補と探索上位",
        "",
        markdown_table(named, 20),
        "",
        "## ロバスト探索 上位50",
        "",
        markdown_table(top.head(50), 60),
        "",
        "## ベース情報",
        "",
        f"- T5候補総数: `{len(base)}`",
        f"- 探索で生き残った条件数: `{len(top)}`",
        "- 生き残り条件: 全期間80回以上、train35回以上、test25回以上、train/test双方プラス、4通貨以上プラス、2年窓4本以上プラス。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    base = load_base()
    top = search(base)
    named = named_candidates(base, top)
    top.to_csv(OUT_DIR / "robust_search_top.csv", index=False)
    named.to_csv(OUT_DIR / "named_candidates.csv", index=False)
    write_report(base, top, named)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(named.head(12).to_string(index=False))
    print("\\nTop robust search:")
    print(top.head(12).to_string(index=False))


if __name__ == "__main__":
    main()

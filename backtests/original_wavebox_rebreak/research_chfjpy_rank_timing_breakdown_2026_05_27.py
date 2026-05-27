#!/usr/bin/env python3
"""CHFJPY rank-change, timing edge, and breakdown-condition research."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import research_chfjpy_stretch_deep_dive_2026_05_27 as deep
import research_sequence_countertrend_portfolio_2026_05_27 as seq


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_27" / "chfjpy_rank_timing_breakdown"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["USDJPY", "CHFJPY", "GBPJPY", "AUDJPY", "EURJPY"]
CROSS_SYMBOLS = ["CHFJPY", "GBPJPY", "AUDJPY", "EURJPY"]

BASE_SPEC = {
    **seq.BASE_STRETCH_SHORT,
    "hours": seq.HOUR_SETS["exclude_0_only"],
    "rr": 0.8,
    "max_hold": 24,
}


def summarize(label: str, trades: pd.DataFrame) -> dict:
    return deep.summarize(label, trades)


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
    return deep.markdown_table(df, max_rows)


def symbol_heat(symbol: str) -> pd.DataFrame:
    h1_raw, _ = seq.get_symbol_data(symbol)
    h1 = deep.add_deep_features(h1_raw)
    out = pd.DataFrame(index=h1.index)
    out[f"{symbol}_bb_z"] = h1["bb_z"]
    out[f"{symbol}_ret6_atr"] = (h1["close"] - h1["close"].shift(6)) / h1["atr"]
    out[f"{symbol}_ret12_atr"] = (h1["close"] - h1["close"].shift(12)) / h1["atr"]
    out[f"{symbol}_bb_z_lag6"] = out[f"{symbol}_bb_z"].shift(6)
    out[f"{symbol}_bb_z_lag12"] = out[f"{symbol}_bb_z"].shift(12)
    out[f"{symbol}_ret6_atr_lag6"] = out[f"{symbol}_ret6_atr"].shift(6)
    out[f"{symbol}_ret6_atr_lag12"] = out[f"{symbol}_ret6_atr"].shift(12)
    out[f"{symbol}_preheat_bb12"] = out[f"{symbol}_bb_z"].shift(1).rolling(12).max()
    out[f"{symbol}_preheat_ret12"] = out[f"{symbol}_ret6_atr"].shift(1).rolling(12).max()
    return out.reset_index(names="signal_time").sort_values("signal_time")


def attach_rank_features(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.sort_values("signal_time").copy()
    for symbol in SYMBOLS:
        out = pd.merge_asof(out, symbol_heat(symbol), on="signal_time", direction="backward")

    for suffix in ["bb_z", "ret6_atr", "bb_z_lag6", "bb_z_lag12", "ret6_atr_lag6", "ret6_atr_lag12"]:
        all_cols = [f"{s}_{suffix}" for s in SYMBOLS]
        cross_cols = [f"{s}_{suffix}" for s in CROSS_SYMBOLS]
        out[f"chf_{suffix}_rank_all5"] = out[all_cols].rank(axis=1, ascending=False, method="min")[
            f"CHFJPY_{suffix}"
        ].astype(int)
        out[f"chf_{suffix}_rank_cross4"] = out[cross_cols].rank(axis=1, ascending=False, method="min")[
            f"CHFJPY_{suffix}"
        ].astype(int)

    out["chf_bb_rank_improve6_cross4"] = out["chf_bb_z_lag6_rank_cross4"] - out["chf_bb_z_rank_cross4"]
    out["chf_bb_rank_improve12_cross4"] = out["chf_bb_z_lag12_rank_cross4"] - out["chf_bb_z_rank_cross4"]
    out["chf_ret_rank_improve6_cross4"] = out["chf_ret6_atr_lag6_rank_cross4"] - out["chf_ret6_atr_rank_cross4"]
    out["chf_ret_rank_improve12_cross4"] = out["chf_ret6_atr_lag12_rank_cross4"] - out["chf_ret6_atr_rank_cross4"]

    other_cross_bb = [f"{s}_bb_z" for s in ["GBPJPY", "AUDJPY", "EURJPY"]]
    other_cross_ret = [f"{s}_ret6_atr" for s in ["GBPJPY", "AUDJPY", "EURJPY"]]
    other_all_ret = [f"{s}_ret6_atr" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    other_all_bb = [f"{s}_bb_z" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]

    out["other_cross_mean_bb_z"] = out[other_cross_bb].mean(axis=1)
    out["other_cross_mean_ret6_atr"] = out[other_cross_ret].mean(axis=1)
    out["other_all_mean_bb_z"] = out[other_all_bb].mean(axis=1)
    out["other_all_mean_ret6_atr"] = out[other_all_ret].mean(axis=1)
    out["chf_minus_cross_bb_z"] = out["CHFJPY_bb_z"] - out["other_cross_mean_bb_z"]
    out["chf_minus_all_bb_z"] = out["CHFJPY_bb_z"] - out["other_all_mean_bb_z"]
    out["chf_minus_cross_ret6"] = out["CHFJPY_ret6_atr"] - out["other_cross_mean_ret6_atr"]

    out["usd_up_6h"] = out["USDJPY_ret6_atr"] > 0.5
    out["usd_down_6h"] = out["USDJPY_ret6_atr"] < -0.5
    out["cross_yen_sell"] = out["other_cross_mean_ret6_atr"] > 0.5
    out["cross_yen_drop"] = out["other_cross_mean_ret6_atr"] < -0.5
    out["normal_yen_sell_heat"] = out["usd_up_6h"] & out["cross_yen_sell"]
    out["riskoff_price_proxy"] = out["usd_down_6h"] | out["cross_yen_drop"]
    out["chf_relative_overheat"] = out["chf_minus_cross_bb_z"] >= 0.0
    out["chf_top_bb_cross4"] = out["chf_bb_z_rank_cross4"] == 1
    out["chf_top_ret_cross4"] = out["chf_ret6_atr_rank_cross4"] == 1
    out["chf_rank_jump_to_top_bb6"] = (out["chf_bb_z_lag6_rank_cross4"] >= 3) & out["chf_top_bb_cross4"]
    out["chf_rank_jump_to_top2_bb6"] = (out["chf_bb_z_lag6_rank_cross4"] >= 3) & (
        out["chf_bb_z_rank_cross4"] <= 2
    )
    out["chf_rank_jump_to_top_ret6"] = (out["chf_ret6_atr_lag6_rank_cross4"] >= 3) & out["chf_top_ret_cross4"]
    out["chf_late_heat_structure"] = out["usd_up_6h"] & out["chf_rank_jump_to_top2_bb6"]
    out["chf_isolated_heat"] = out["chf_relative_overheat"] & (out["other_cross_mean_ret6_atr"] <= 0.3)
    out["broad_then_chf_heat"] = out["normal_yen_sell_heat"] & out["chf_relative_overheat"]
    return out


def timing_features(h1: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in trades.sort_values("entry_time").itertuples(index=False):
        item = row._asdict()
        entry_i = int(item["entry_i"])
        exit_i = int(item["exit_i"])
        entry = float(item["entry"])
        risk = float(item["risk"])
        direction = item["direction"]
        for n in [1, 3, 6, 12, 24]:
            end_i = min(entry_i + n, len(h1) - 1)
            window = h1.iloc[entry_i : end_i + 1]
            if direction == "short":
                mfe_n = (entry - float(window["low"].min())) / risk
                mae_n = (float(window["high"].max()) - entry) / risk
                close_r_n = (entry - float(h1["close"].iloc[end_i])) / risk
            else:
                mfe_n = (float(window["high"].max()) - entry) / risk
                mae_n = (entry - float(window["low"].min())) / risk
                close_r_n = (float(h1["close"].iloc[end_i]) - entry) / risk
            item[f"mfe_{n}b_r"] = mfe_n
            item[f"mae_{n}b_r"] = mae_n
            item[f"close_{n}b_r"] = close_r_n
            item[f"hit_0_5r_by_{n}b"] = mfe_n >= 0.5
            item[f"hit_0_8r_by_{n}b"] = mfe_n >= 0.8
        rows.append(item)
    return pd.DataFrame(rows)


def binary_filter_table(trades: pd.DataFrame, tests: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for name, mask in tests.items():
        rows.append(summarize(name, trades[mask.fillna(False)].copy()))
    return pd.DataFrame(rows).sort_values(["total_r", "avg_r"], ascending=False)


def timing_summary(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for n in [1, 3, 6, 12, 24]:
        rows.append(
            {
                "bars": n,
                "hit_0_5r_rate": float(trades[f"hit_0_5r_by_{n}b"].mean() * 100.0),
                "hit_0_8r_rate": float(trades[f"hit_0_8r_by_{n}b"].mean() * 100.0),
                "avg_mfe_r": float(trades[f"mfe_{n}b_r"].mean()),
                "median_mfe_r": float(trades[f"mfe_{n}b_r"].median()),
                "avg_mae_r": float(trades[f"mae_{n}b_r"].mean()),
                "avg_close_r": float(trades[f"close_{n}b_r"].mean()),
                "positive_close_rate": float((trades[f"close_{n}b_r"] > 0).mean() * 100.0),
            }
        )
    by_bars = pd.DataFrame(rows)

    group_rows = []
    for group_name, group in {
        "winner": trades[trades["r_after_cost"] > 0],
        "loser": trades[trades["r_after_cost"] <= 0],
    }.items():
        for n in [1, 3, 6, 12, 24]:
            group_rows.append(
                {
                    "group": group_name,
                    "bars": n,
                    "trades": len(group),
                    "hit_0_5r_rate": float(group[f"hit_0_5r_by_{n}b"].mean() * 100.0) if len(group) else np.nan,
                    "hit_0_8r_rate": float(group[f"hit_0_8r_by_{n}b"].mean() * 100.0) if len(group) else np.nan,
                    "avg_mfe_r": float(group[f"mfe_{n}b_r"].mean()) if len(group) else np.nan,
                    "avg_mae_r": float(group[f"mae_{n}b_r"].mean()) if len(group) else np.nan,
                    "avg_close_r": float(group[f"close_{n}b_r"].mean()) if len(group) else np.nan,
                }
            )
    return by_bars, pd.DataFrame(group_rows)


def main() -> None:
    h1, source = deep.base_data()
    base = deep.run_spec_on_source(h1, source, BASE_SPEC)
    base = deep.add_mae_mfe(h1, base)
    ranked = attach_rank_features(base)
    timed = timing_features(h1, ranked)
    timed.to_csv(OUT_DIR / "base_rank_timing_trades.csv", index=False)

    rank_tests = {
        "base": pd.Series(True, index=timed.index),
        "chf_top_bb_cross4": timed["chf_top_bb_cross4"],
        "chf_top_ret_cross4": timed["chf_top_ret_cross4"],
        "rank_jump_to_top_bb6": timed["chf_rank_jump_to_top_bb6"],
        "rank_jump_to_top2_bb6": timed["chf_rank_jump_to_top2_bb6"],
        "rank_jump_to_top_ret6": timed["chf_rank_jump_to_top_ret6"],
        "usd_up": timed["usd_up_6h"],
        "normal_yen_sell_heat": timed["normal_yen_sell_heat"],
        "broad_then_chf_heat": timed["broad_then_chf_heat"],
        "late_heat_structure": timed["chf_late_heat_structure"],
        "chf_isolated_heat": timed["chf_isolated_heat"],
        "riskoff_proxy": timed["riskoff_price_proxy"],
        "not_riskoff_proxy": ~timed["riskoff_price_proxy"],
        "usd_down": timed["usd_down_6h"],
    }
    rank_summary = binary_filter_table(timed, rank_tests)
    rank_summary.to_csv(OUT_DIR / "step1_rank_change_breakdown_summary.csv", index=False)

    bucket_rows = []
    buckets = {
        "bb_rank_now": timed["chf_bb_z_rank_cross4"].astype(str),
        "bb_rank_lag6": timed["chf_bb_z_lag6_rank_cross4"].astype(str),
        "bb_rank_improve6": pd.cut(
            timed["chf_bb_rank_improve6_cross4"],
            [-9, -1, 0, 1, 9],
            labels=["worse", "same", "improve1", "improve2plus"],
            include_lowest=True,
        ),
        "ret_rank_improve6": pd.cut(
            timed["chf_ret_rank_improve6_cross4"],
            [-9, -1, 0, 1, 9],
            labels=["worse", "same", "improve1", "improve2plus"],
            include_lowest=True,
        ),
    }
    for axis, series in buckets.items():
        tmp = timed.copy()
        tmp["bucket"] = series
        for bucket, group in tmp.groupby("bucket", observed=True):
            bucket_rows.append({**summarize(str(bucket), group), "axis": axis, "bucket": str(bucket)})
    bucket_summary = pd.DataFrame(bucket_rows)
    bucket_summary.to_csv(OUT_DIR / "step1_rank_buckets.csv", index=False)

    time_by_bars, time_by_result = timing_summary(timed)
    time_by_bars.to_csv(OUT_DIR / "step2_timing_by_bars.csv", index=False)
    time_by_result.to_csv(OUT_DIR / "step2_timing_by_result.csv", index=False)

    # Breakdown conditions and losses.
    breakdown_rows = []
    for name, mask in {
        "all_losers": timed["r_after_cost"] <= 0,
        "riskoff_losers": timed["riskoff_price_proxy"] & (timed["r_after_cost"] <= 0),
        "usd_down_losers": timed["usd_down_6h"] & (timed["r_after_cost"] <= 0),
        "not_top_bb_losers": (~timed["chf_top_bb_cross4"]) & (timed["r_after_cost"] <= 0),
        "no_rank_jump_losers": (~timed["chf_rank_jump_to_top2_bb6"]) & (timed["r_after_cost"] <= 0),
        "mae_gt_08_losers": (timed["mae_r"] > 0.8) & (timed["r_after_cost"] <= 0),
    }.items():
        sub = timed[mask].copy()
        row = summarize(name, sub)
        row["avg_mae_r"] = float(sub["mae_r"].mean()) if len(sub) else np.nan
        row["avg_mfe_r"] = float(sub["mfe_r"].mean()) if len(sub) else np.nan
        breakdown_rows.append(row)
    breakdown_summary = pd.DataFrame(breakdown_rows)
    breakdown_summary.to_csv(OUT_DIR / "step3_breakdown_loss_conditions.csv", index=False)

    cols = [
        "label",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "worst_year_r",
        "worst_2y_r",
        "oos_trades",
        "oos_r",
    ]
    lines = [
        "# CHFJPY Rank / Timing / Breakdown Research",
        "",
        "## 1. Rank-Change / Market Structure Filters",
        "",
        markdown_table(rank_summary[cols], 40),
        "",
        "## 1b. Rank Buckets",
        "",
        markdown_table(bucket_summary[["axis", "bucket", *cols]], 60),
        "",
        "## 2. Time-Progress Edge",
        "",
        markdown_table(time_by_bars, 20),
        "",
        "## 2b. Time-Progress by Final Result",
        "",
        markdown_table(time_by_result, 30),
        "",
        "## 3. Breakdown / Loss Conditions",
        "",
        markdown_table(breakdown_summary[[*cols, "avg_mae_r", "avg_mfe_r"]], 20),
        "",
        "## Notes",
        "",
        "- Rank 1 means the strongest upper deviation among the JPY crosses.",
        "- `rank_jump_to_top2_bb6` means CHFJPY was rank 3 or worse six hours ago and is rank 1-2 now.",
        "- Risk-off is proxied from prices only: USDJPY 6h down or other JPY crosses broadly down.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nRank summary")
    print(rank_summary[cols].to_string(index=False))
    print("\nRank buckets")
    print(bucket_summary[["axis", "bucket", *cols]].to_string(index=False))
    print("\nTiming")
    print(time_by_bars.to_string(index=False))
    print(time_by_result.to_string(index=False))
    print("\nBreakdown")
    print(breakdown_summary[[*cols, "avg_mae_r", "avg_mfe_r"]].to_string(index=False))


if __name__ == "__main__":
    main()

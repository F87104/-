#!/usr/bin/env python3
"""CHFJPY exit management and relative JPY-cross heat validation.

Checks requested after the CHFJPY stretch-reversal deep dive:
1. Force exit when adverse excursion reaches 0.8R.
2. Test whether CHFJPY works because it is the last/weak overheat inside a
   broader JPY-cross move.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import audit_wavebox_usdjpy_v1_practical as usd
import research_chfjpy_countertrend as ct
import research_chfjpy_stretch_deep_dive_2026_05_27 as deep
import research_sequence_countertrend_portfolio_2026_05_27 as seq


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_27" / "chfjpy_exit_relative_heat"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["USDJPY", "CHFJPY", "GBPJPY", "AUDJPY", "EURJPY"]


def summarize(label: str, trades: pd.DataFrame) -> dict:
    return deep.summarize(label, trades)


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
    return deep.markdown_table(df, max_rows)


def run_chf_spec(h1: pd.DataFrame, source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    return deep.run_spec_on_source(h1, source, spec)


def reprice_with_adverse_exit(
    h1: pd.DataFrame,
    trades: pd.DataFrame,
    adverse_r: float,
    label: str,
) -> pd.DataFrame:
    """Apply an adverse-exit rule to the same entries as an existing trade set.

    Intrabar ambiguity is handled conservatively: if TP and adverse exit are
    both touched on the same candle, the adverse exit is assumed first.
    """
    rows = []
    for row in trades.sort_values("entry_time").itertuples(index=False):
        item = row._asdict()
        entry_i = int(item["entry_i"])
        max_exit_i = int(item["exit_i"])
        direction = item["direction"]
        entry = float(item["entry"])
        risk = float(item["risk"])
        target = float(item["target"])

        if direction == "short":
            adverse_price = entry + risk * adverse_r
        else:
            adverse_price = entry - risk * adverse_r

        exit_i = max_exit_i
        exit_price = float(item["exit"])
        reason = item["exit_reason"]
        for j in range(entry_i, max_exit_i + 1):
            hi = float(h1["high"].iloc[j])
            lo = float(h1["low"].iloc[j])
            if direction == "short":
                hit_adverse = hi >= adverse_price
                hit_tp = lo <= target
            else:
                hit_adverse = lo <= adverse_price
                hit_tp = hi >= target
            if hit_adverse or hit_tp:
                exit_i = j
                if hit_adverse:
                    exit_price = adverse_price
                    reason = f"AE_{adverse_r:.2f}R"
                else:
                    exit_price = target
                    reason = "TP"
                break

        item["exit_i"] = exit_i
        item["exit_time"] = h1.index[exit_i]
        item["exit"] = exit_price
        item["exit_reason"] = reason
        item["bars_held"] = exit_i - entry_i
        item["adverse_exit_r"] = adverse_r
        item["r_after_cost"] = seq.rp.direction_cost_r(direction, entry, exit_price, risk)
        rows.append(item)

    out = pd.DataFrame(rows)
    out["label"] = label
    for col in ["signal_time", "entry_time", "exit_time"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col])
    return out


def symbol_features(symbol: str) -> pd.DataFrame:
    h1_raw, _ = seq.get_symbol_data(symbol)
    h1 = deep.add_deep_features(h1_raw)
    out = h1[
        [
            "close",
            "atr",
            "bb_z",
            "rsi14",
            "ema20_dist_atr",
            "high_bb_excess_atr",
            "pre_bb_width_ratio_96",
            "H4_ema100_slope",
        ]
    ].copy()
    out[f"{symbol}_ret6_atr"] = (out["close"] - out["close"].shift(6)) / out["atr"]
    out[f"{symbol}_ret12_atr"] = (out["close"] - out["close"].shift(12)) / out["atr"]
    out[f"{symbol}_bb_z"] = out["bb_z"]
    out[f"{symbol}_rsi14"] = out["rsi14"]
    out[f"{symbol}_high_bb_excess_atr"] = out["high_bb_excess_atr"]
    out[f"{symbol}_preheat_bb12"] = out["bb_z"].shift(1).rolling(12).max()
    out[f"{symbol}_preheat_ret12"] = out[f"{symbol}_ret6_atr"].shift(1).rolling(12).max()
    keep = [c for c in out.columns if c.startswith(f"{symbol}_")]
    return out[keep].reset_index(names="signal_time").sort_values("signal_time")


def attach_relative_heat(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.sort_values("signal_time").copy()
    for symbol in SYMBOLS:
        feats = symbol_features(symbol)
        out = pd.merge_asof(out, feats, on="signal_time", direction="backward")

    bb_cols_all = [f"{s}_bb_z" for s in SYMBOLS]
    ret_cols_all = [f"{s}_ret6_atr" for s in SYMBOLS]
    bb_cols_cross = [f"{s}_bb_z" for s in ["CHFJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    ret_cols_cross = [f"{s}_ret6_atr" for s in ["CHFJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    other_bb = [f"{s}_bb_z" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    other_ret = [f"{s}_ret6_atr" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    other_cross_bb = [f"{s}_bb_z" for s in ["GBPJPY", "AUDJPY", "EURJPY"]]
    other_cross_ret = [f"{s}_ret6_atr" for s in ["GBPJPY", "AUDJPY", "EURJPY"]]

    out["other_mean_bb_z"] = out[other_bb].mean(axis=1)
    out["other_cross_mean_bb_z"] = out[other_cross_bb].mean(axis=1)
    out["other_mean_ret6_atr"] = out[other_ret].mean(axis=1)
    out["other_cross_mean_ret6_atr"] = out[other_cross_ret].mean(axis=1)
    out["chf_minus_other_bb"] = out["CHFJPY_bb_z"] - out["other_mean_bb_z"]
    out["chf_minus_cross_bb"] = out["CHFJPY_bb_z"] - out["other_cross_mean_bb_z"]
    out["chf_minus_other_ret6"] = out["CHFJPY_ret6_atr"] - out["other_mean_ret6_atr"]
    out["chf_bb_rank_all5"] = out[bb_cols_all].rank(axis=1, ascending=False, method="min")["CHFJPY_bb_z"].astype(int)
    out["chf_bb_rank_cross4"] = out[bb_cols_cross].rank(axis=1, ascending=False, method="min")["CHFJPY_bb_z"].astype(int)
    out["chf_ret_rank_all5"] = out[ret_cols_all].rank(axis=1, ascending=False, method="min")["CHFJPY_ret6_atr"].astype(int)
    out["chf_ret_rank_cross4"] = out[ret_cols_cross].rank(axis=1, ascending=False, method="min")["CHFJPY_ret6_atr"].astype(int)

    preheat_bb_cols = [f"{s}_preheat_bb12" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    preheat_ret_cols = [f"{s}_preheat_ret12" for s in ["USDJPY", "GBPJPY", "AUDJPY", "EURJPY"]]
    out["other_preheat_bb12_max"] = out[preheat_bb_cols].max(axis=1)
    out["other_preheat_ret12_max"] = out[preheat_ret_cols].max(axis=1)
    out["usd_up_6h"] = out["USDJPY_ret6_atr"] > 0.5
    out["usd_down_6h"] = out["USDJPY_ret6_atr"] < -0.5
    out["broad_yen_heat"] = out["other_mean_ret6_atr"] > 0.5
    out["cross_yen_heat"] = out["other_cross_mean_ret6_atr"] > 0.5
    out["chf_highest_bb_all5"] = out["chf_bb_rank_all5"] == 1
    out["chf_highest_bb_cross4"] = out["chf_bb_rank_cross4"] == 1
    out["chf_relative_bb_pos"] = out["chf_minus_other_bb"] >= 0
    out["chf_relative_cross_bb_pos"] = out["chf_minus_cross_bb"] >= 0
    out["other_preheated"] = (out["other_preheat_bb12_max"] >= 1.8) | (out["other_preheat_ret12_max"] >= 1.2)
    return out


def filter_summary(trades: pd.DataFrame, name: str, mask: pd.Series) -> dict:
    return summarize(name, trades[mask.fillna(False)].copy())


def relative_heat_tables(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tests = {
        "base": pd.Series(True, index=trades.index),
        "usd_up_6h": trades["usd_up_6h"],
        "usd_not_down_6h": ~trades["usd_down_6h"],
        "usd_down_6h": trades["usd_down_6h"],
        "broad_yen_heat": trades["broad_yen_heat"],
        "cross_yen_heat": trades["cross_yen_heat"],
        "chf_highest_bb_all5": trades["chf_highest_bb_all5"],
        "chf_highest_bb_cross4": trades["chf_highest_bb_cross4"],
        "chf_relative_bb_pos": trades["chf_relative_bb_pos"],
        "chf_relative_cross_bb_pos": trades["chf_relative_cross_bb_pos"],
        "other_preheated": trades["other_preheated"],
        "usd_up_and_chf_rel": trades["usd_up_6h"] & trades["chf_relative_bb_pos"],
        "usd_up_and_chf_highest_cross": trades["usd_up_6h"] & trades["chf_highest_bb_cross4"],
        "preheated_and_chf_rel": trades["other_preheated"] & trades["chf_relative_bb_pos"],
        "broad_heat_and_chf_rel": trades["broad_yen_heat"] & trades["chf_relative_bb_pos"],
    }
    rows = [filter_summary(trades, name, mask) for name, mask in tests.items()]
    summary = pd.DataFrame(rows).sort_values(["total_r", "avg_r"], ascending=False)

    buckets = []
    bucket_defs = {
        "usd_ret6": pd.cut(
            trades["USDJPY_ret6_atr"],
            [-99, -0.5, 0.5, 99],
            labels=["USD down", "USD flat", "USD up"],
            include_lowest=True,
        ),
        "chf_minus_other_bb": pd.cut(
            trades["chf_minus_other_bb"],
            [-99, -0.5, 0.0, 0.5, 99],
            labels=["much lower", "slightly lower", "slightly higher", "much higher"],
            include_lowest=True,
        ),
        "chf_bb_rank_cross4": trades["chf_bb_rank_cross4"].astype(str),
        "other_preheated": trades["other_preheated"].map({True: "preheated", False: "not_preheated"}),
    }
    for axis, series in bucket_defs.items():
        tmp = trades.copy()
        tmp["bucket"] = series
        for bucket, group in tmp.groupby("bucket", observed=True):
            buckets.append({**summarize(str(bucket), group), "axis": axis, "bucket": str(bucket)})
    bucket_summary = pd.DataFrame(buckets)
    return summary, bucket_summary


def main() -> None:
    h1, source = deep.base_data()

    base12_spec = {**seq.BASE_STRETCH_SHORT, "hours": seq.HOUR_SETS["exclude_0_only"], "rr": 0.8, "max_hold": 12}
    base24_spec = {**base12_spec, "max_hold": 24}
    base12 = run_chf_spec(h1, source, base12_spec)
    base24 = run_chf_spec(h1, source, base24_spec)

    exit_rows = []
    exit_sets = {
        "base12_no_ae": base12,
        "base24_no_ae": base24,
    }
    for name, df in exit_sets.items():
        exit_rows.append(summarize(name, df))
        df.to_csv(OUT_DIR / f"{name}_trades.csv", index=False)
        for adverse_r in [0.6, 0.7, 0.8, 0.9]:
            priced = reprice_with_adverse_exit(h1, df, adverse_r, f"{name}_ae{adverse_r}")
            priced.to_csv(OUT_DIR / f"{name}_ae{adverse_r}_trades.csv", index=False)
            row = summarize(f"{name}_ae{adverse_r}", priced)
            row["adverse_exit_r"] = adverse_r
            exit_rows.append(row)
    exit_summary = pd.DataFrame(exit_rows).sort_values(["total_r", "avg_r"], ascending=False)
    exit_summary.to_csv(OUT_DIR / "step1_adverse_exit_summary.csv", index=False)

    # Relative heat is evaluated on the current preferred base24 setup.
    rel_base = attach_relative_heat(base24.copy())
    rel_base.to_csv(OUT_DIR / "step2_relative_heat_trades.csv", index=False)
    rel_summary, rel_bucket = relative_heat_tables(rel_base)
    rel_summary.to_csv(OUT_DIR / "step2_relative_heat_filter_summary.csv", index=False)
    rel_bucket.to_csv(OUT_DIR / "step2_relative_heat_bucket_summary.csv", index=False)

    # Monthly relation with USDJPY WaveBox using the updated base24 CHFJPY set.
    usd_base = usd.apply_candidate(usd.load_base(), usd.CANDIDATES[usd.STANDARD_CANDIDATE]).copy()
    usd_month = usd_base.groupby(usd_base["entry_time"].dt.to_period("M"))["r_after_cost"].sum()
    chf_month = base24.groupby(base24["entry_time"].dt.to_period("M"))["r_after_cost"].sum()
    monthly = pd.concat([usd_month.rename("usdjpy_wavebox_r"), chf_month.rename("chfjpy_base24_r")], axis=1).fillna(0.0)
    monthly["combined_r"] = monthly["usdjpy_wavebox_r"] + monthly["chfjpy_base24_r"]
    monthly.to_csv(OUT_DIR / "step3_monthly_usdjpy_chfjpy_base24.csv")
    monthly_summary = pd.DataFrame(
        [
            {
                "monthly_corr": monthly["usdjpy_wavebox_r"].corr(monthly["chfjpy_base24_r"]),
                "usd_total_r": monthly["usdjpy_wavebox_r"].sum(),
                "chf_base24_total_r": monthly["chfjpy_base24_r"].sum(),
                "combined_total_r": monthly["combined_r"].sum(),
                "usd_monthly_dd": deep.max_drawdown(monthly["usdjpy_wavebox_r"]),
                "chf_monthly_dd": deep.max_drawdown(monthly["chfjpy_base24_r"]),
                "combined_monthly_dd": deep.max_drawdown(monthly["combined_r"]),
            }
        ]
    )
    monthly_summary.to_csv(OUT_DIR / "step3_monthly_summary.csv", index=False)

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
        "# CHFJPY Exit / Relative Heat Research",
        "",
        "## 1. Adverse Exit",
        "",
        markdown_table(exit_summary[[c for c in cols + ["adverse_exit_r"] if c in exit_summary.columns]], 30),
        "",
        "## 2. Relative JPY-Cross Heat Filters",
        "",
        markdown_table(rel_summary[cols], 30),
        "",
        "## 2b. Relative Heat Buckets",
        "",
        markdown_table(rel_bucket[["axis", "bucket", *cols]], 40),
        "",
        "## 3. Monthly USDJPY / CHFJPY Relation",
        "",
        markdown_table(monthly_summary, 10),
        "",
        "## Notes",
        "",
        "- Adverse exit is applied to the same entry set to isolate exit-rule impact.",
        "- Relative heat is evaluated at the signal candle close.",
        "- Intrabar adverse-vs-TP ambiguity is handled conservatively: adverse exit first.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nAdverse exit")
    print(exit_summary[[c for c in cols + ["adverse_exit_r"] if c in exit_summary.columns]].to_string(index=False))
    print("\nRelative heat")
    print(rel_summary[cols].to_string(index=False))
    print("\nRelative buckets")
    print(rel_bucket[["axis", "bucket", *cols]].to_string(index=False))
    print("\nMonthly")
    print(monthly_summary.to_string(index=False))


if __name__ == "__main__":
    main()

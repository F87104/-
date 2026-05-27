#!/usr/bin/env python3
"""Deep dive for CHFJPY H1 stretch reversal short.

Focus:
- Why CHFJPY responds better than GBPJPY/AUDJPY.
- Whether the move works best after a quiet pre-state.
- How much overextension is enough.
- Which stall definition matters.
- MAE/MFE behavior.
- TP / max-hold curve.
- Relation with USDJPY WaveBox.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import audit_wavebox_usdjpy_v1_practical as usd
import research_chfjpy_countertrend as ct
import research_chfjpy_personality as rp
import research_sequence_countertrend_portfolio_2026_05_27 as seq


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_27" / "chfjpy_stretch_deep_dive"
OUT_DIR.mkdir(parents=True, exist_ok=True)


BASE_SPEC = {
    **seq.BASE_STRETCH_SHORT,
    "hours": seq.HOUR_SETS["exclude_0_only"],
}


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return np.inf if gp > 0 else np.nan


def max_drawdown(values: pd.Series | np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def summarize(label: str, trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {
            "label": label,
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "oos_trades": 0,
            "oos_r": 0.0,
        }
    df = trades.sort_values("entry_time").copy()
    r = df["r_after_cost"]
    df["year"] = df["entry_time"].dt.year
    by_year = df.groupby("year")["r_after_cost"].sum()
    rolling_2y = []
    for year in sorted(df["year"].unique()):
        rolling_2y.append(float(df[df["year"].between(year, year + 1)]["r_after_cost"].sum()))
    oos = df[df["entry_time"] >= rp.OOS_START]
    return {
        "label": label,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "worst_year_r": float(by_year.min()) if len(by_year) else np.nan,
        "worst_2y_r": float(min(rolling_2y)) if rolling_2y else np.nan,
        "oos_trades": int(len(oos)),
        "oos_r": float(oos["r_after_cost"].sum()) if len(oos) else 0.0,
    }


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


def add_deep_features(h1: pd.DataFrame) -> pd.DataFrame:
    out = h1.copy()
    abs_body = (out["close"] - out["open"]).abs()
    bb_width = out["std20"] * 4.0
    upper_bb = out["sma20"] + out["std20"] * 2.0
    lower_bb = out["sma20"] - out["std20"] * 2.0

    pre_atr = out["atr"].shift(1)
    pre_width = bb_width.shift(1)
    out["pre_atr_ratio_96"] = pre_atr / pre_atr.rolling(96).median()
    out["pre_atr_ratio_240"] = pre_atr / pre_atr.rolling(240).median()
    out["pre_bb_width_atr"] = pre_width / out["atr"]
    out["pre_bb_width_ratio_96"] = pre_width / pre_width.rolling(96).median()
    out["pre_range_6_atr"] = (out["high"].shift(1).rolling(6).max() - out["low"].shift(1).rolling(6).min()) / out["atr"]
    out["pre_range_12_atr"] = (out["high"].shift(1).rolling(12).max() - out["low"].shift(1).rolling(12).min()) / out["atr"]
    out["pre_body_mean_6_atr"] = abs_body.shift(1).rolling(6).mean() / out["atr"]
    out["pre_body_mean_12_atr"] = abs_body.shift(1).rolling(12).mean() / out["atr"]

    out["high_bb_excess_atr"] = (out["high"] - upper_bb) / out["atr"]
    out["close_bb_excess_atr"] = (out["close"] - upper_bb) / out["atr"]
    out["low_bb_excess_atr"] = (lower_bb - out["low"]) / out["atr"]
    out["signal_body_atr"] = abs_body / out["atr"]
    out["body_vs_avg20"] = abs_body / abs_body.shift(1).rolling(20).mean()
    out["signal_bear"] = out["close"] < out["open"]
    out["signal_bull"] = out["close"] > out["open"]
    out["bear_engulf"] = (
        (out["close"] < out["open"])
        & (out["open"] >= out["close"].shift(1))
        & (out["close"] <= out["open"].shift(1))
    )
    out["higher_high_atr"] = (out["high"] - out["high"].shift(1)) / out["atr"]
    return out


def enrich_source(h1: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    out = source.copy()
    idx = out["signal_i"].astype(int).to_numpy()
    columns = [
        "pre_atr_ratio_96",
        "pre_atr_ratio_240",
        "pre_bb_width_atr",
        "pre_bb_width_ratio_96",
        "pre_range_6_atr",
        "pre_range_12_atr",
        "pre_body_mean_6_atr",
        "pre_body_mean_12_atr",
        "high_bb_excess_atr",
        "close_bb_excess_atr",
        "signal_body_atr",
        "body_vs_avg20",
        "signal_bear",
        "signal_bull",
        "bear_engulf",
        "higher_high_atr",
    ]
    for col in columns:
        values = h1[col].to_numpy()
        out[col] = values[idx]
    out["quiet_atr"] = out["pre_atr_ratio_96"] <= 0.90
    out["quiet_bb"] = out["pre_bb_width_ratio_96"] <= 0.90
    out["quiet_range6"] = out["pre_range_6_atr"] <= 1.60
    out["quiet_body6"] = out["pre_body_mean_6_atr"] <= 0.25
    out["quiet_combo"] = out[["quiet_atr", "quiet_bb", "quiet_range6"]].sum(axis=1) >= 2
    return out.replace([np.inf, -np.inf], np.nan)


def run_spec_on_source(h1: pd.DataFrame, source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    old_cost = seq.set_symbol_cost("CHFJPY")
    try:
        trades = ct.run_trades(h1, source, spec)
    finally:
        seq.restore_cost(old_cost)
    return trades


def base_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    h1_raw, source_raw = seq.get_symbol_data("CHFJPY")
    h1 = add_deep_features(h1_raw)
    source = enrich_source(h1, source_raw)
    return h1, source


def add_mae_mfe(h1: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    rows = []
    for row in trades.itertuples(index=False):
        item = row._asdict()
        entry_i = int(item["entry_i"])
        exit_i = int(item["exit_i"])
        entry = float(item["entry"])
        risk = float(item["risk"])
        direction = item["direction"]
        window = h1.iloc[entry_i : exit_i + 1]
        if direction == "short":
            mae = (window["high"].max() - entry) / risk
            mfe = (entry - window["low"].min()) / risk
            first_fav = window.index[(entry - window["low"]) / risk >= 0.5]
        else:
            mae = (entry - window["low"].min()) / risk
            mfe = (window["high"].max() - entry) / risk
            first_fav = window.index[(window["high"] - entry) / risk >= 0.5]
        item["mae_r"] = float(mae)
        item["mfe_r"] = float(mfe)
        item["time_to_0_5r_bars"] = (
            int(h1.index.get_loc(first_fav[0]) - entry_i) if len(first_fav) else np.nan
        )
        rows.append(item)
    return pd.DataFrame(rows)


def bucket_summaries(trades: pd.DataFrame, feature: str, bins: list[float], labels: list[str]) -> pd.DataFrame:
    if trades.empty or feature not in trades:
        return pd.DataFrame()
    out = trades.copy()
    out["bucket"] = pd.cut(out[feature], bins=bins, labels=labels, include_lowest=True)
    rows = []
    for bucket, group in out.groupby("bucket", observed=True):
        rows.append({**summarize(str(bucket), group), "feature": feature, "bucket": str(bucket)})
    return pd.DataFrame(rows)


def main() -> None:
    h1, source = base_data()
    base_trades = run_spec_on_source(h1, source, BASE_SPEC)
    base_trades_mae = add_mae_mfe(h1, base_trades)
    base_trades_mae.to_csv(OUT_DIR / "base_trades_with_mae_mfe.csv", index=False)

    # 1. Quiet pre-state.
    quiet_tests = {
        "base": source,
        "pre_atr_low": source[source["quiet_atr"]],
        "pre_bb_compressed": source[source["quiet_bb"]],
        "pre_range6_quiet": source[source["quiet_range6"]],
        "pre_body6_quiet": source[source["quiet_body6"]],
        "quiet_combo_2of3": source[source["quiet_combo"]],
        "not_quiet_combo": source[~source["quiet_combo"]],
    }
    quiet_rows = []
    for label, src in quiet_tests.items():
        trades = run_spec_on_source(h1, src, BASE_SPEC)
        quiet_rows.append(summarize(label, trades))
    quiet_df = pd.DataFrame(quiet_rows).sort_values("total_r", ascending=False)
    quiet_df.to_csv(OUT_DIR / "step1_pre_calm_filters.csv", index=False)

    # 2. Overextension thresholds.
    over_rows = []
    for bb_z in [1.8, 2.1, 2.4, 2.7]:
        for high_excess in [-999.0, 0.0, 0.3, 0.6]:
            for move_atr in [0.8, 1.2, 1.6, 2.0]:
                spec = {**BASE_SPEC, "bb_z": bb_z, "rsi_high": 101, "move_atr": move_atr}
                src = source if high_excess < -100 else source[source["high_bb_excess_atr"] >= high_excess]
                trades = run_spec_on_source(h1, src, spec)
                label = f"bbz{bb_z}_highEx{high_excess}_move{move_atr}"
                over_rows.append(
                    {
                        **summarize(label, trades),
                        "bb_z": bb_z,
                        "high_bb_excess_atr": high_excess,
                        "move_atr": move_atr,
                    }
                )
    over_df = pd.DataFrame(over_rows).sort_values(["total_r", "avg_r"], ascending=False)
    over_df.to_csv(OUT_DIR / "step2_overextension_grid.csv", index=False)

    # 3. Stall definitions.
    stall_rows = []
    stall_filters = {
        "base": source,
        "signal_bear": source[source["signal_bear"]],
        "bear_engulf": source[source["bear_engulf"]],
        "wick_ge_065": source[source["wick_ratio"] >= 0.65],
        "wick_ge_075": source[source["wick_ratio"] >= 0.75],
        "close_lower_25": source[source["close_location"] >= 0.75],
        "wick065_close075": source[(source["wick_ratio"] >= 0.65) & (source["close_location"] >= 0.75)],
        "high_update_small": source[source["higher_high_atr"] <= 0.30],
        "body_not_huge": source[source["body_vs_avg20"] <= 2.0],
    }
    for label, src in stall_filters.items():
        trades = run_spec_on_source(h1, src, BASE_SPEC)
        stall_rows.append(summarize(label, trades))
    stall_df = pd.DataFrame(stall_rows).sort_values("total_r", ascending=False)
    stall_df.to_csv(OUT_DIR / "step3_stall_definition.csv", index=False)

    # 4. MAE/MFE.
    mae_rows = []
    for label, group in {
        "all": base_trades_mae,
        "winner": base_trades_mae[base_trades_mae["r_after_cost"] > 0],
        "loser": base_trades_mae[base_trades_mae["r_after_cost"] <= 0],
    }.items():
        if group.empty:
            continue
        mae_rows.append(
            {
                "group": label,
                "trades": len(group),
                "avg_mae_r": group["mae_r"].mean(),
                "median_mae_r": group["mae_r"].median(),
                "p75_mae_r": group["mae_r"].quantile(0.75),
                "avg_mfe_r": group["mfe_r"].mean(),
                "median_mfe_r": group["mfe_r"].median(),
                "p75_mfe_r": group["mfe_r"].quantile(0.75),
                "avg_r": group["r_after_cost"].mean(),
            }
        )
    mae_summary = pd.DataFrame(mae_rows)
    mae_summary.to_csv(OUT_DIR / "step4_mae_mfe_summary.csv", index=False)
    mae_bucket = bucket_summaries(
        base_trades_mae,
        "mae_r",
        [-0.01, 0.25, 0.50, 0.80, 1.20, 99.0],
        ["<=0.25R", "0.25-0.50R", "0.50-0.80R", "0.80-1.20R", ">1.20R"],
    )
    mae_bucket.to_csv(OUT_DIR / "step4_mae_bucket_summary.csv", index=False)

    # 5. TP / max-hold curve.
    curve_rows = []
    for rr in [0.5, 0.8, 1.0, 1.2, 1.5]:
        for max_hold in [3, 5, 8, 12, 24]:
            spec = {**BASE_SPEC, "rr": rr, "max_hold": max_hold}
            trades = run_spec_on_source(h1, source, spec)
            curve_rows.append({**summarize(f"tp{rr}_hold{max_hold}", trades), "rr": rr, "max_hold": max_hold})
    curve_df = pd.DataFrame(curve_rows).sort_values(["total_r", "avg_r"], ascending=False)
    curve_df.to_csv(OUT_DIR / "step5_tp_hold_curve.csv", index=False)

    # 6. USDJPY relation.
    usd_h1, _ = seq.get_symbol_data("USDJPY")
    usd_h1 = ct.add_countertrend_features(usd_h1)
    usd_ctx = usd_h1[["close", "atr", "bb_z", "ema20_dist_atr", "H4_ema100_slope"]].copy()
    usd_ctx["usd_6h_ret_atr"] = (usd_ctx["close"] - usd_ctx["close"].shift(6)) / usd_ctx["atr"]
    usd_ctx["usd_24h_ret_atr"] = (usd_ctx["close"] - usd_ctx["close"].shift(24)) / usd_ctx["atr"]
    usd_ctx = usd_ctx.reset_index(names="entry_time").sort_values("entry_time")
    chf_ctx = base_trades_mae.sort_values("entry_time")
    chf_ctx = pd.merge_asof(chf_ctx, usd_ctx, on="entry_time", direction="backward", suffixes=("", "_usd"))
    usd_env_rows = []
    chf_ctx["usd_6h_bucket"] = pd.cut(
        chf_ctx["usd_6h_ret_atr"],
        [-99, -0.5, 0.5, 99],
        labels=["USDJPY_down", "USDJPY_flat", "USDJPY_up"],
        include_lowest=True,
    )
    for bucket, group in chf_ctx.groupby("usd_6h_bucket", observed=True):
        usd_env_rows.append({**summarize(str(bucket), group), "bucket": str(bucket)})
    usd_env = pd.DataFrame(usd_env_rows)
    usd_env.to_csv(OUT_DIR / "step6_usdjpy_environment.csv", index=False)

    usd_base = usd.apply_candidate(usd.load_base(), usd.CANDIDATES[usd.STANDARD_CANDIDATE]).copy()
    usd_month = usd_base.groupby(usd_base["entry_time"].dt.to_period("M"))["r_after_cost"].sum()
    chf_month = base_trades_mae.groupby(base_trades_mae["entry_time"].dt.to_period("M"))["r_after_cost"].sum()
    monthly = pd.concat([usd_month.rename("usdjpy_wavebox_r"), chf_month.rename("chfjpy_stretch_r")], axis=1).fillna(0.0)
    monthly["combined_r"] = monthly["usdjpy_wavebox_r"] + monthly["chfjpy_stretch_r"]
    monthly.to_csv(OUT_DIR / "step6_monthly_usdjpy_chfjpy.csv")
    corr = float(monthly["usdjpy_wavebox_r"].corr(monthly["chfjpy_stretch_r"]))
    monthly_summary = pd.DataFrame(
        [
            {
                "monthly_corr": corr,
                "usd_monthly_dd": max_drawdown(monthly["usdjpy_wavebox_r"]),
                "chf_monthly_dd": max_drawdown(monthly["chfjpy_stretch_r"]),
                "combined_monthly_dd": max_drawdown(monthly["combined_r"]),
                "usd_total_r": monthly["usdjpy_wavebox_r"].sum(),
                "chf_total_r": monthly["chfjpy_stretch_r"].sum(),
                "combined_total_r": monthly["combined_r"].sum(),
            }
        ]
    )
    monthly_summary.to_csv(OUT_DIR / "step6_monthly_correlation_summary.csv", index=False)

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
        "# CHFJPY Stretch Reversal Deep Dive",
        "",
        "## Base",
        "",
        markdown_table(pd.DataFrame([summarize("base_ex0", base_trades_mae)])[cols], 10),
        "",
        "## 1. Pre-Calm Filters",
        "",
        markdown_table(quiet_df[cols], 20),
        "",
        "## 2. Overextension Grid",
        "",
        markdown_table(over_df[[*cols, "bb_z", "high_bb_excess_atr", "move_atr"]], 30),
        "",
        "## 3. Stall Definition",
        "",
        markdown_table(stall_df[cols], 20),
        "",
        "## 4. MAE / MFE Summary",
        "",
        markdown_table(mae_summary, 20),
        "",
        "## 4b. MAE Buckets",
        "",
        markdown_table(mae_bucket[["feature", "bucket", *cols]], 20),
        "",
        "## 5. TP / Hold Curve",
        "",
        markdown_table(curve_df[[*cols, "rr", "max_hold"]], 40),
        "",
        "## 6. USDJPY Environment",
        "",
        markdown_table(usd_env[[*cols, "bucket"]], 20),
        "",
        "## 6b. Monthly USDJPY/CHFJPY Relation",
        "",
        markdown_table(monthly_summary, 10),
        "",
        "## Notes",
        "",
        "- Pre-calm tests are evaluated on the same stretch short framework.",
        "- TP/hold curve changes overlap because exits change the next allowed entry.",
        "- Sample size remains small; robust conclusions should prefer broad, intuitive filters.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Base")
    print(pd.DataFrame([summarize("base_ex0", base_trades_mae)])[cols].to_string(index=False))
    print("\nPre-calm")
    print(quiet_df[cols].to_string(index=False))
    print("\nOverextension top")
    print(over_df[[*cols, "bb_z", "high_bb_excess_atr", "move_atr"]].head(15).to_string(index=False))
    print("\nStall")
    print(stall_df[cols].to_string(index=False))
    print("\nMAE")
    print(mae_summary.to_string(index=False))
    print(mae_bucket[["feature", "bucket", *cols]].to_string(index=False))
    print("\nTP curve")
    print(curve_df[[*cols, "rr", "max_hold"]].head(20).to_string(index=False))
    print("\nUSD relation")
    print(usd_env[[*cols, "bucket"]].to_string(index=False))
    print(monthly_summary.to_string(index=False))


if __name__ == "__main__":
    main()

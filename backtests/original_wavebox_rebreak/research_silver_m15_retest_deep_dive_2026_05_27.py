#!/usr/bin/env python3
"""Deep dive for SILVER/XAGUSD H1 short M15 retest execution.

The H1 setup is fixed to the practical guard.  This script explores whether
the M15 retest entry edge is structural or just a lucky 0.25R parameter.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
AUDIT_PATH = THIS_DIR / "audit_silver_m15_execution_2026_05_27.py"
RESEARCH_PATH = THIS_DIR / "research_silver_short_system.py"
OUT_DIR = THIS_DIR / "results_2026_05_27" / "silver_m15_retest_deep_dive"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def max_drawdown(values) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.itertuples(index=False, name=None)]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]
    )


def summarize(name: str, trades: pd.DataFrame, total_setups: int) -> dict:
    if trades.empty:
        return {
            "variant": name,
            "setups": total_setups,
            "trades": 0,
            "fill_rate": 0.0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "avg_mae_r": np.nan,
            "avg_mfe_r": np.nan,
            "avg_risk_atr": np.nan,
            "avg_fill_delay_m15": np.nan,
            "tp": 0,
            "sl": 0,
            "time": 0,
            "worst_year_r": 0.0,
        }
    r = trades["r_after_cost"]
    by_year = trades.groupby(trades["entry_time"].dt.year)["r_after_cost"].sum()
    fill_delay = trades["fill_delay_m15"] if "fill_delay_m15" in trades.columns else pd.Series(dtype=float)
    return {
        "variant": name,
        "setups": total_setups,
        "trades": len(trades),
        "fill_rate": len(trades) / total_setups * 100.0 if total_setups else np.nan,
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "avg_mae_r": float(trades["mae_r"].mean()),
        "avg_mfe_r": float(trades["mfe_r"].mean()),
        "avg_risk_atr": float(trades["risk_atr"].mean()),
        "avg_fill_delay_m15": float(fill_delay.mean()) if not fill_delay.empty else np.nan,
        "tp": int((trades["exit_reason"] == "TP").sum()),
        "sl": int(trades["exit_reason"].astype(str).str.startswith("SL").sum()),
        "time": int((trades["exit_reason"] == "TIME").sum()),
        "worst_year_r": float(by_year.min()) if not by_year.empty else 0.0,
    }


def get_h1_and_m15():
    audit = load_module(AUDIT_PATH, "silver_m15_audit")
    research = load_module(RESEARCH_PATH, "silver_short_research")
    h1 = research.prepare_h1()
    source = pd.read_csv(
        THIS_DIR / "results_2026_05_27" / "silver_short_system" / "silver_short_source.csv",
        parse_dates=["signal_time"],
    )
    h1_trades = research.run_trades(h1, source, audit.guard_spec())
    m15 = audit.load_m15()
    return audit, h1, h1_trades, m15


def short_cost_r(entry: float, exit_price: float, risk: float, spread: float = 0.03, slip: float = 0.01) -> float:
    after_cost = (entry - spread / 2.0) - (exit_price + slip)
    return after_cost / risk


def m15_window(m15: pd.DataFrame, start: pd.Timestamp, hours: float) -> pd.DataFrame:
    return m15[(m15.index >= start) & (m15.index < start + pd.Timedelta(hours=hours))]


def first_m15_features(m15: pd.DataFrame, entry_time: pd.Timestamp, entry: float, risk: float) -> dict:
    first = m15_window(m15, entry_time, 1.0)
    if first.empty:
        return {}
    row = first.iloc[0]
    rng = float(row["high"] - row["low"])
    close_loc_short = (float(row["high"]) - float(row["close"])) / rng if rng > 0 else np.nan
    return {
        "first_m15_bear": bool(float(row["close"]) < float(row["open"])),
        "first_m15_close_loc_short": close_loc_short,
        "first_m15_mfe_r": max(0.0, (entry - float(row["low"])) / risk) if risk > 0 else np.nan,
        "first_m15_mae_r": max(0.0, (float(row["high"]) - entry) / risk) if risk > 0 else np.nan,
    }


def retest_fill(
    m15: pd.DataFrame,
    h1_entry_time: pd.Timestamp,
    h1_entry: float,
    h1_risk: float,
    retest_r: float,
    wait_hours: float,
) -> dict | None:
    win = m15_window(m15, h1_entry_time, wait_hours)
    if win.empty:
        return None
    limit = h1_entry + retest_r * h1_risk
    pre_low = h1_entry
    pre_high = h1_entry
    for idx, (ts, row) in enumerate(win.iterrows()):
        hi = float(row["high"])
        lo = float(row["low"])
        pre_low = min(pre_low, lo)
        pre_high = max(pre_high, hi)
        if hi >= limit:
            rng = hi - lo
            close_loc_short = (hi - float(row["close"])) / rng if rng > 0 else np.nan
            return {
                "fill_time": ts,
                "fill": limit,
                "fill_delay_m15": idx,
                "pre_fill_mfe_from_h1_open_r": max(0.0, (h1_entry - pre_low) / h1_risk) if h1_risk > 0 else np.nan,
                "pre_fill_mae_from_h1_open_r": max(0.0, (pre_high - h1_entry) / h1_risk) if h1_risk > 0 else np.nan,
                "touch_bar_bear": bool(float(row["close"]) < float(row["open"])),
                "touch_bar_close_loc_short": close_loc_short,
            }
    return None


def confirm_after_retest(
    m15: pd.DataFrame,
    h1_entry_time: pd.Timestamp,
    h1_entry: float,
    h1_risk: float,
    retest_r: float,
    wait_hours: float,
    confirm_bars: int,
    close_loc_min: float,
    require_close_below_limit: bool,
) -> dict | None:
    fill = retest_fill(m15, h1_entry_time, h1_entry, h1_risk, retest_r, wait_hours)
    if fill is None:
        return None
    limit = float(fill["fill"])
    after = m15[(m15.index >= fill["fill_time"]) & (m15.index <= fill["fill_time"] + pd.Timedelta(minutes=15 * confirm_bars))]
    if len(after) < 2:
        return None
    rows = list(after.iterrows())
    for idx in range(min(confirm_bars, len(rows) - 1)):
        ts, row = rows[idx]
        rng = float(row["high"] - row["low"])
        if rng <= 0:
            continue
        close_loc_short = (float(row["high"]) - float(row["close"])) / rng
        bearish = float(row["close"]) < float(row["open"])
        level_ok = not require_close_below_limit or float(row["close"]) <= limit
        if bearish and close_loc_short >= close_loc_min and level_ok:
            next_ts, next_row = rows[idx + 1]
            return {
                **fill,
                "fill_time": next_ts,
                "fill": float(next_row["open"]),
                "confirm_delay_m15": idx + 1,
            }
    return None


def simulate_exit(
    m15: pd.DataFrame,
    entry_time: pd.Timestamp,
    entry: float,
    stop: float,
    rr: float = 1.2,
    max_hold_h1: int = 24,
) -> dict | None:
    risk = stop - entry
    if not math.isfinite(risk) or risk <= 0:
        return None
    target = entry - risk * rr
    win = m15[(m15.index >= entry_time) & (m15.index <= entry_time + pd.Timedelta(hours=max_hold_h1))]
    if win.empty:
        return None
    exit_time = win.index[-1]
    exit_price = float(win["close"].iloc[-1])
    exit_reason = "TIME"
    mae_r = 0.0
    mfe_r = 0.0
    for ts, row in win.iterrows():
        hi = float(row["high"])
        lo = float(row["low"])
        mae_r = max(mae_r, (hi - entry) / risk)
        mfe_r = max(mfe_r, (entry - lo) / risk)
        hit_sl = hi >= stop
        hit_tp = lo <= target
        if hit_sl or hit_tp:
            exit_time = ts
            exit_price = stop if hit_sl else target
            exit_reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
            break
    return {
        "target": target,
        "exit_time": exit_time,
        "exit": exit_price,
        "exit_reason": exit_reason,
        "bars_held_m15": int((exit_time - entry_time) / pd.Timedelta(minutes=15)),
        "mae_r": mae_r,
        "mfe_r": mfe_r,
        "r_after_cost": short_cost_r(entry, exit_price, risk),
    }


def run_retest_variant(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    h1_trades: pd.DataFrame,
    variant: str,
    retest_r: float,
    wait_hours: float,
    confirm: bool = False,
    confirm_bars: int = 4,
    close_loc_min: float = 0.65,
    require_close_below_limit: bool = False,
) -> pd.DataFrame:
    rows = []
    for sig in h1_trades.to_dict("records"):
        h1_entry_time = pd.Timestamp(sig["entry_time"])
        h1_entry = float(sig["entry"])
        h1_risk = float(sig["risk"])
        stop = float(sig["stop"])
        atr = float(sig["atr"])
        if confirm:
            fill = confirm_after_retest(
                m15,
                h1_entry_time,
                h1_entry,
                h1_risk,
                retest_r,
                wait_hours,
                confirm_bars,
                close_loc_min,
                require_close_below_limit,
            )
        else:
            fill = retest_fill(m15, h1_entry_time, h1_entry, h1_risk, retest_r, wait_hours)
        if fill is None:
            continue
        entry_time = pd.Timestamp(fill["fill_time"])
        entry = float(fill["fill"])
        risk = stop - entry
        if not math.isfinite(risk) or risk <= 0 or risk / atr > 2.5:
            continue
        outcome = simulate_exit(m15, entry_time, entry, stop, 1.2, 24)
        if outcome is None:
            continue
        rows.append(
            {
                **sig,
                "variant": variant,
                "retest_r": retest_r,
                "wait_hours": wait_hours,
                "entry_time": entry_time,
                "entry": entry,
                "stop": stop,
                "risk": risk,
                "risk_atr": risk / atr,
                **fill,
                **first_m15_features(m15, h1_entry_time, h1_entry, h1_risk),
                **outcome,
            }
        )
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    return out


def apply_named_filter(trades: pd.DataFrame, name: str) -> pd.DataFrame:
    if trades.empty:
        return trades
    out = trades.copy()
    if name == "all":
        return out
    if name == "ex_6_7":
        return out[~out["entry_hour"].isin([6, 7])]
    if name == "ex_7":
        return out[out["entry_hour"] != 7]
    if name == "trigger_ge_0_08":
        return out[out["trigger_atr"] >= 0.08]
    if name == "trigger_ge_0_10":
        return out[out["trigger_atr"] >= 0.10]
    if name == "fill_delay_ge_2":
        return out[out["fill_delay_m15"] >= 2]
    if name == "touch_reject":
        return out[(out["touch_bar_bear"]) & (out["touch_bar_close_loc_short"] >= 0.65)]
    if name == "first_bear":
        return out[out["first_m15_bear"]]
    if name == "not_h4_flat":
        return out[out["h4_slope_atr"] <= -0.20]
    if name == "not_extreme_drop":
        return out[out["move_24_atr"] <= 5.0]
    if name == "range_ge_0_8":
        return out[out["range_atr"] >= 0.8]
    raise ValueError(name)


def skipped_vs_filled(open_trades: pd.DataFrame, retest_trades: pd.DataFrame) -> pd.DataFrame:
    filled_signals = set(retest_trades["signal_i"].astype(int).tolist())
    rows = []
    for label, part in [
        ("filled_by_025r_2h", open_trades[open_trades["signal_i"].astype(int).isin(filled_signals)]),
        ("skipped_by_025r_2h", open_trades[~open_trades["signal_i"].astype(int).isin(filled_signals)]),
    ]:
        rows.append(summarize(label, part, len(open_trades)))
    return pd.DataFrame(rows)


def main() -> None:
    audit, h1, h1_trades, m15 = get_h1_and_m15()
    h1_trades = h1_trades.copy()
    total_setups = len(h1_trades)

    # Baseline open using the prior script for fair comparison.
    open_trades = audit.run_variant(h1, m15, h1_trades, "m15_open")
    open_trades.to_csv(OUT_DIR / "baseline_m15_open_trades.csv", index=False)

    grid_rows = []
    grid_trades = {}
    for retest_r in [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
        for wait_hours in [1.0, 2.0, 3.0, 4.0, 6.0]:
            name = f"retest_{retest_r:.2f}r_{wait_hours:g}h"
            trades = run_retest_variant(h1, m15, h1_trades, name, retest_r, wait_hours)
            grid_rows.append(summarize(name, trades, total_setups) | {"retest_r": retest_r, "wait_hours": wait_hours})
            grid_trades[name] = trades
    grid = pd.DataFrame(grid_rows).sort_values(["total_r", "pf", "trades"], ascending=False)
    grid.to_csv(OUT_DIR / "step1_retest_depth_wait_grid.csv", index=False)

    base_name = "retest_0.25r_2h"
    base_retest = grid_trades[base_name]
    base_retest.to_csv(OUT_DIR / "base_retest_025r_2h_trades.csv", index=False)

    filter_rows = []
    for filt in [
        "all",
        "ex_7",
        "ex_6_7",
        "trigger_ge_0_08",
        "trigger_ge_0_10",
        "fill_delay_ge_2",
        "touch_reject",
        "first_bear",
        "not_h4_flat",
        "not_extreme_drop",
        "range_ge_0_8",
    ]:
        part = apply_named_filter(base_retest, filt)
        filter_rows.append(summarize(filt, part, total_setups) | {"filter": filt})
    filters = pd.DataFrame(filter_rows).sort_values(["total_r", "pf"], ascending=False)
    filters.to_csv(OUT_DIR / "step2_base025_filter_tests.csv", index=False)

    confirm_rows = []
    confirm_trades = {}
    for retest_r in [0.20, 0.25, 0.30]:
        for wait_hours in [2.0, 3.0, 4.0]:
            for confirm_bars in [2, 4, 8]:
                for close_loc in [0.60, 0.65, 0.75]:
                    for close_below in [False, True]:
                        name = f"confirm_{retest_r:.2f}r_{wait_hours:g}h_{confirm_bars}b_cl{close_loc:.2f}_{'below' if close_below else 'any'}"
                        trades = run_retest_variant(
                            h1,
                            m15,
                            h1_trades,
                            name,
                            retest_r,
                            wait_hours,
                            True,
                            confirm_bars,
                            close_loc,
                            close_below,
                        )
                        confirm_rows.append(
                            summarize(name, trades, total_setups)
                            | {
                                "retest_r": retest_r,
                                "wait_hours": wait_hours,
                                "confirm_bars": confirm_bars,
                                "close_loc_min": close_loc,
                                "close_below_limit": close_below,
                            }
                        )
                        confirm_trades[name] = trades
    confirms = pd.DataFrame(confirm_rows).sort_values(["total_r", "pf", "trades"], ascending=False)
    confirms.to_csv(OUT_DIR / "step3_confirm_after_retest_grid.csv", index=False)
    if not confirms.empty:
        best_confirm_name = str(confirms.iloc[0]["variant"])
        confirm_trades[best_confirm_name].to_csv(OUT_DIR / "best_confirm_after_retest_trades.csv", index=False)

    skip = skipped_vs_filled(open_trades, base_retest)
    skip.to_csv(OUT_DIR / "step4_skipped_vs_filled_by_025r.csv", index=False)

    # Buckets are diagnostic, not formal filters.
    bucket_rows = []
    if not base_retest.empty:
        bucket_specs = [
            ("fill_delay", pd.cut(base_retest["fill_delay_m15"], [-1, 1, 3, 7, 99], labels=["0-1", "2-3", "4-7", "8+"])),
            ("trigger", pd.cut(base_retest["trigger_atr"], [0, 0.08, 0.15, 0.30, 99], labels=["<=0.08", "0.08-0.15", "0.15-0.30", "0.30+"])),
            ("h4_slope", pd.cut(base_retest["h4_slope_atr"], [-99, -1.0, -0.5, -0.2, 0], labels=["<=-1.0", "-1.0--0.5", "-0.5--0.2", "-0.2-0"])),
            ("move24", pd.cut(base_retest["move_24_atr"], [0, 1.5, 3.0, 5.0, 99], labels=["<=1.5", "1.5-3.0", "3.0-5.0", "5.0+"])),
        ]
        for bucket_name, buckets in bucket_specs:
            tmp = base_retest.copy()
            tmp["bucket"] = buckets
            for bucket, part in tmp.groupby("bucket", observed=True):
                bucket_rows.append(summarize(f"{bucket_name}:{bucket}", part, len(tmp)) | {"bucket_type": bucket_name, "bucket": str(bucket)})
    buckets = pd.DataFrame(bucket_rows)
    if not buckets.empty:
        buckets.to_csv(OUT_DIR / "step5_base025_buckets.csv", index=False)

    report_cols = [
        "variant",
        "trades",
        "fill_rate",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "avg_mae_r",
        "avg_mfe_r",
        "avg_risk_atr",
        "avg_fill_delay_m15",
        "tp",
        "sl",
        "time",
        "worst_year_r",
    ]
    top_grid = grid[report_cols + ["retest_r", "wait_hours"]].head(15)
    top_filters = filters[report_cols + ["filter"]]
    top_confirms = confirms[report_cols + ["retest_r", "wait_hours", "confirm_bars", "close_loc_min", "close_below_limit"]].head(15)
    md = [
        "# SILVER/XAGUSD M15 Retest Deep Dive",
        "",
        "## Baseline Question",
        "",
        "- Fixed H1 setup: SILVER H1 short, H4 down, pullback box rebreak.",
        "- Baseline execution: H1 signal -> next H1 open short.",
        "- Current improvement candidate: M15 retest to H1 entry + 0.25R within 2 hours.",
        "",
        "## Step 1: Retest Depth / Wait Grid",
        "",
        markdown_table(top_grid),
        "",
        "## Step 2: Filters On 0.25R / 2h Retest",
        "",
        markdown_table(top_filters),
        "",
        "## Step 3: M15 Confirmation After Retest",
        "",
        markdown_table(top_confirms),
        "",
        "## Step 4: Skipped vs Filled",
        "",
        markdown_table(skip[report_cols]),
        "",
        "## Read",
        "",
        "- A retest improves average risk and MAE, but it also skips trades. This is an execution-quality filter, not a new direction signal.",
        "- If a filter removes both losses but also cuts too many winners, treat it as a warning label rather than a production rule.",
        "- Confirmation after retest is tested separately because it may reduce false retests, but it can also enter later and give back the better price.",
    ]
    if not buckets.empty:
        md.extend(["", "## Diagnostic Buckets", "", markdown_table(buckets[report_cols + ["bucket_type", "bucket"]], max_rows=40)])
    (OUT_DIR / "report_ja.md").write_text("\n".join(md), encoding="utf-8")

    print("baseline")
    print(summarize("m15_open", open_trades, total_setups))
    print("top retest grid")
    print(top_grid.round(3).to_string(index=False))
    print("filters")
    print(top_filters.round(3).to_string(index=False))
    print("top confirmations")
    print(top_confirms.round(3).to_string(index=False))
    print(f"output={OUT_DIR}")


if __name__ == "__main__":
    main()

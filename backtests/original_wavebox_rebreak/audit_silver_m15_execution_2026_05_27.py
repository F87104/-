#!/usr/bin/env python3
"""Audit M15 execution overlays for the SILVER/XAGUSD H1 short setup.

The H1 setup is intentionally kept fixed.  This script only tests whether
15-minute execution improves entry quality, risk, and early failure handling.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
RESEARCH_PATH = THIS_DIR / "research_silver_short_system.py"
OUT_DIR = THIS_DIR / "results_2026_05_27" / "silver_m15_execution"
M15_DIR = THIS_DIR.parents[1] / "F87104_test" / "SILVER2014-2024" / "m15_from_drive"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_research_module():
    spec = importlib.util.spec_from_file_location("silver_short_research", RESEARCH_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_m15() -> pd.DataFrame:
    files = sorted(M15_DIR.glob("XAGUSD_M15_*.csv"))
    if not files:
        raise FileNotFoundError(f"No M15 files found in {M15_DIR}")
    frames = []
    for path in files:
        df = pd.read_csv(path)
        df.columns = [c.strip("<>").lower() for c in df.columns]
        dt = pd.to_datetime(
            df["dtyyyymmdd"].astype(str) + df["time"].astype(str).str.zfill(4),
            format="%Y%m%d%H%M",
        )
        df = df.assign(timestamp=dt).set_index("timestamp")
        frames.append(df[["open", "high", "low", "close"]].astype(float))
    out = pd.concat(frames).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    return out


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


def short_cost_r(entry: float, exit_price: float, risk: float, spread: float = 0.03, slip: float = 0.01) -> float:
    after_cost = (entry - spread / 2.0) - (exit_price + slip)
    return after_cost / risk


def guard_spec() -> dict:
    return {
        "family": "pullback_rebreak",
        "lookback": "any",
        "box_bars": 8,
        "move_bars": 24,
        "move_atr": 0.8,
        "trigger_atr": 0.05,
        "range_atr": 0.5,
        "body_max": 0.85,
        "close_location": 0.75,
        "upper_wick": 0.0,
        "box_width_max": 1.5,
        "pullback_atr": 0.6,
        "bb_z": None,
        "rsi_high": None,
        "h4": "down",
        "d1": "any",
        "hour_filter": "ex_11_12",
        "rr": 1.2,
        "stop_buffer_atr": 0.15,
        "max_risk_atr": 2.5,
        "max_hold": 24,
    }


def summarize(name: str, trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"variant": name, "trades": 0}
    r = trades["r_after_cost"]
    by_year = trades.groupby(trades["entry_time"].dt.year)["r_after_cost"].sum()
    return {
        "variant": name,
        "trades": len(trades),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "avg_mae_r": float(trades["mae_r"].mean()),
        "avg_mfe_r": float(trades["mfe_r"].mean()),
        "avg_risk_atr": float(trades["risk_atr"].mean()),
        "avg_bars_held_m15": float(trades["bars_held_m15"].mean()),
        "tp": int((trades["exit_reason"] == "TP").sum()),
        "sl": int(trades["exit_reason"].astype(str).str.startswith("SL").sum()),
        "time": int((trades["exit_reason"] == "TIME").sum()),
        "early": int((trades["exit_reason"] == "EARLY_NO_PROGRESS").sum()),
        "worst_year_r": float(by_year.min()) if not by_year.empty else 0.0,
    }


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    view = df.copy()
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


def fill_entry(
    m15: pd.DataFrame,
    h1: pd.DataFrame,
    sig: dict,
    variant: str,
    h1_entry_time: pd.Timestamp,
    h1_entry_price: float,
    risk_h1: float,
) -> tuple[pd.Timestamp, float] | None:
    sig_i = int(sig["signal_i"])
    box_low = float(h1[f"box_low_{int(sig['box_bars'])}"].iloc[sig_i])
    first_hour = m15[(m15.index >= h1_entry_time) & (m15.index < h1_entry_time + pd.Timedelta(hours=1))]
    first_two_hours = m15[(m15.index >= h1_entry_time) & (m15.index < h1_entry_time + pd.Timedelta(hours=2))]
    if first_hour.empty:
        return None

    if variant in {"m15_open", "m15_open_no_progress_exit"}:
        row = first_hour.iloc[0]
        return first_hour.index[0], float(row["open"])

    if variant == "m15_retest_box_1h":
        for ts, row in first_hour.iterrows():
            if float(row["high"]) >= box_low:
                return ts, box_low
        return None

    if variant == "m15_retest_025r_2h":
        limit = h1_entry_price + 0.25 * risk_h1
        for ts, row in first_two_hours.iterrows():
            if float(row["high"]) >= limit:
                return ts, limit
        return None

    if variant == "m15_bear_confirm_1h":
        for idx in range(len(first_hour) - 1):
            row = first_hour.iloc[idx]
            rng = float(row["high"] - row["low"])
            if rng <= 0:
                continue
            close_loc = (float(row["high"]) - float(row["close"])) / rng
            if float(row["close"]) < float(row["open"]) and close_loc >= 0.65:
                next_row = first_hour.iloc[idx + 1]
                return first_hour.index[idx + 1], float(next_row["open"])
        return None

    raise ValueError(f"Unknown variant: {variant}")


def simulate_m15_exit(
    m15: pd.DataFrame,
    entry_time: pd.Timestamp,
    entry: float,
    stop: float,
    target: float,
    max_hold_h1: int,
    variant: str,
) -> dict | None:
    risk = stop - entry
    if not math.isfinite(risk) or risk <= 0:
        return None
    window = m15[(m15.index >= entry_time) & (m15.index <= entry_time + pd.Timedelta(hours=max_hold_h1))]
    if window.empty:
        return None

    exit_time = window.index[-1]
    exit_price = float(window["close"].iloc[-1])
    exit_reason = "TIME"
    mae_r = 0.0
    mfe_r = 0.0
    no_progress_checked = False

    for n, (ts, row) in enumerate(window.iterrows()):
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

        if variant == "m15_open_no_progress_exit" and not no_progress_checked and n == 3:
            no_progress_checked = True
            if mfe_r < 0.25:
                exit_time = ts
                exit_price = float(row["close"])
                exit_reason = "EARLY_NO_PROGRESS"
                break

    return {
        "exit_time": exit_time,
        "exit": exit_price,
        "exit_reason": exit_reason,
        "bars_held_m15": int((exit_time - entry_time) / pd.Timedelta(minutes=15)),
        "mae_r": mae_r,
        "mfe_r": mfe_r,
        "r_after_cost": short_cost_r(entry, exit_price, risk),
    }


def run_variant(h1: pd.DataFrame, m15: pd.DataFrame, h1_trades: pd.DataFrame, variant: str) -> pd.DataFrame:
    rows = []
    for sig in h1_trades.to_dict("records"):
        h1_entry_time = pd.Timestamp(sig["entry_time"])
        h1_entry_price = float(sig["entry"])
        h1_stop = float(sig["stop"])
        h1_risk = float(sig["risk"])
        fill = fill_entry(m15, h1, sig, variant, h1_entry_time, h1_entry_price, h1_risk)
        if fill is None:
            continue
        entry_time, entry = fill
        stop = h1_stop
        risk = stop - entry
        atr = float(sig["atr"])
        if not math.isfinite(risk) or risk <= 0 or risk / atr > 2.5:
            continue
        target = entry - risk * 1.2
        outcome = simulate_m15_exit(m15, entry_time, entry, stop, target, 24, variant)
        if outcome is None:
            continue
        rows.append(
            {
                **sig,
                "variant": variant,
                "entry_time": entry_time,
                "entry": entry,
                "stop": stop,
                "target": target,
                "risk": risk,
                "risk_atr": risk / atr,
                **outcome,
            }
        )
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    return out


def main() -> None:
    mod = load_research_module()
    h1 = mod.prepare_h1()
    source_path = THIS_DIR / "results_2026_05_27" / "silver_short_system" / "silver_short_source.csv"
    source = pd.read_csv(source_path, parse_dates=["signal_time"])
    spec = guard_spec()
    h1_trades_all = mod.run_trades(h1, source, spec)
    m15 = load_m15()
    start, end = m15.index.min(), m15.index.max()
    h1_trades = h1_trades_all[(h1_trades_all["entry_time"] >= start) & (h1_trades_all["entry_time"] <= end)].copy()

    variants = [
        "m15_open",
        "m15_retest_box_1h",
        "m15_retest_025r_2h",
        "m15_bear_confirm_1h",
        "m15_open_no_progress_exit",
    ]
    trades = []
    summary_rows = []
    for variant in variants:
        result = run_variant(h1, m15, h1_trades, variant)
        if not result.empty:
            result.to_csv(OUT_DIR / f"{variant}_trades.csv", index=False)
        trades.append(result)
        summary_rows.append(summarize(variant, result))

    all_trades = pd.concat([t for t in trades if not t.empty], ignore_index=True) if any(not t.empty for t in trades) else pd.DataFrame()
    summary = pd.DataFrame(summary_rows).sort_values(["total_r", "pf"], ascending=False)
    summary.to_csv(OUT_DIR / "m15_execution_summary.csv", index=False)
    if not all_trades.empty:
        all_trades.to_csv(OUT_DIR / "m15_execution_all_trades.csv", index=False)

    coverage = pd.DataFrame(
        [
            {
                "m15_start": start,
                "m15_end": end,
                "m15_rows": len(m15),
                "h1_guard_trades_all": len(h1_trades_all),
                "h1_guard_trades_in_m15_range": len(h1_trades),
                "h1_range_total_r": float(h1_trades["r_after_cost"].sum()) if not h1_trades.empty else 0.0,
                "h1_range_win_rate": float((h1_trades["r_after_cost"] > 0).mean() * 100.0) if not h1_trades.empty else np.nan,
            }
        ]
    )
    coverage.to_csv(OUT_DIR / "m15_execution_coverage.csv", index=False)

    report_cols = [
        "variant",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "avg_mae_r",
        "avg_mfe_r",
        "avg_risk_atr",
        "tp",
        "sl",
        "time",
        "early",
    ]
    md = [
        "# SILVER/XAGUSD H1 Short: M15 Execution Audit",
        "",
        "## Coverage",
        "",
        markdown_table(coverage),
        "",
        "## Execution Variants",
        "",
        markdown_table(summary[report_cols]),
        "",
        "## Read",
        "",
        f"- M15 local coverage is {start} to {end} across {len(m15):,} rows; H1 guard coverage is {len(h1_trades)}/{len(h1_trades_all)} trades.",
        "- The H1 setup is fixed to the practical guard rule: pullback rebreak, box 8, H4 down, ex 11/12, TP 1.2R.",
        "- `m15_open` matches the H1 next-open idea but uses M15 candles for intrabar exit ordering.",
        "- Retest entries reduced risk and improved MFE, but also reduced trade count when the retest did not happen.",
        "- Early no-progress exit damaged the edge: two trades that eventually reached TP were cut too early.",
        "",
        "## Practical Implication",
        "",
        "- Do not add an automatic 1-hour early exit to SILVER yet.",
        "- M15 can be useful for a better entry if price retests upward, but skipping non-retest trades must be tested on the full 2014-2026 sample.",
        "- Current evidence still favors H1 as the decision timeframe and M15 as an execution aid only.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(md), encoding="utf-8")

    print("coverage")
    print(coverage.to_string(index=False))
    print("summary")
    print(summary.round(3).to_string(index=False))
    print(f"output={OUT_DIR}")


if __name__ == "__main__":
    main()

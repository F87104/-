#!/usr/bin/env python3
"""SILVER H1 short-side strategy research.

The goal is not to force the USDJPY/CHFJPY logic onto silver.  This script
tests short-only families that match silver's likely personality:

1. breakdown continuation
2. pullback compression rebreak
3. failed high sweep
4. overextension wick exhaustion
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "results_2026_05_27" / "silver_short_system"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))
sys.path.insert(0, str(THIS_DIR))

from sai_backtest import load_instrument  # noqa: E402
import run_wavebox_rebreak as wb  # noqa: E402


SYMBOL = "SILVER"
START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")

# Silver is cheap enough that transaction cost matters.  Keep this conservative.
SPREAD_PRICE = 0.030
SLIP_PRICE = 0.010


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


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


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def short_cost_r(entry: float, exit_price: float, risk: float) -> float:
    after_cost = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return after_cost / risk


def prepare_h1() -> pd.DataFrame:
    raw = load_instrument(SYMBOL).loc[START:END].copy()
    raw["volume"] = 0.0
    h1 = wb.add_indicators(raw, "H1")
    h4 = wb.add_indicators(wb.resample_ohlc(raw, "4h"), "H4")
    d1 = wb.add_indicators(wb.resample_ohlc(raw, "1D"), "D1")
    h1 = wb.attach_upper_context(h1, {"H4": h4}, "H1")

    # Attach D1 manually because WaveBox's H1 helper only attaches H4.
    out = h1.reset_index(names="timestamp").sort_values("timestamp")
    d1_ctx = d1[["close", "ema100", "ema100_slope"]].reset_index(names="timestamp")
    d1_ctx["context_time"] = d1_ctx["timestamp"] + pd.Timedelta(days=1)
    d1_ctx = d1_ctx.drop(columns=["timestamp"]).rename(
        columns={
            "close": "D1_close",
            "ema100": "D1_ema100",
            "ema100_slope": "D1_ema100_slope",
        }
    )
    out["context_time"] = out["timestamp"] + pd.Timedelta(hours=1)
    h1 = (
        pd.merge_asof(
            out.sort_values("context_time"),
            d1_ctx.sort_values("context_time"),
            on="context_time",
            direction="backward",
        )
        .drop(columns=["context_time"])
        .sort_values("timestamp")
        .set_index("timestamp")
    )

    rng = (h1["high"] - h1["low"]).replace(0, np.nan)
    h1["range_atr"] = rng / h1["atr"]
    h1["body_ratio2"] = (h1["close"] - h1["open"]).abs() / rng
    h1["upper_wick_ratio"] = (h1["high"] - h1[["open", "close"]].max(axis=1)) / rng
    h1["lower_wick_ratio"] = (h1[["open", "close"]].min(axis=1) - h1["low"]) / rng
    h1["close_loc_short"] = (h1["high"] - h1["close"]) / rng
    h1["rsi14"] = rsi(h1["close"], 14)
    h1["sma20"] = h1["close"].rolling(20).mean()
    h1["std20"] = h1["close"].rolling(20).std()
    h1["bb_z"] = (h1["close"] - h1["sma20"]) / h1["std20"].replace(0.0, np.nan)
    h1["ema20_dist_atr"] = (h1["close"] - h1["ema20"]) / h1["atr"]
    h1["ema100_dist_atr"] = (h1["close"] - h1["ema100"]) / h1["atr"]
    h1["h4_slope_atr"] = h1["H4_ema100_slope"] / h1["atr"]
    h1["d1_slope_atr"] = h1["D1_ema100_slope"] / h1["atr"]

    for lb in [24, 48, 72, 96, 144]:
        h1[f"prior_high_{lb}"] = h1["high"].shift(1).rolling(lb).max()
        h1[f"prior_low_{lb}"] = h1["low"].shift(1).rolling(lb).min()
    for box in [6, 8, 12, 16]:
        h1[f"box_high_{box}"] = h1["high"].shift(1).rolling(box).max()
        h1[f"box_low_{box}"] = h1["low"].shift(1).rolling(box).min()
        h1[f"box_width_{box}_atr"] = (h1[f"box_high_{box}"] - h1[f"box_low_{box}"]) / h1["atr"]
    for bars in [3, 6, 12, 24, 48]:
        h1[f"rise_{bars}_atr"] = (h1["high"] - h1["close"].shift(bars)) / h1["atr"]
        h1[f"down_{bars}_atr"] = (h1["close"].shift(bars) - h1["close"]) / h1["atr"]
        h1[f"drop_to_low_{bars}_atr"] = (h1["close"].shift(bars) - h1["low"]) / h1["atr"]
    return h1.replace([np.inf, -np.inf], np.nan)


def h4_state(row: pd.Series) -> tuple[bool, bool, bool]:
    c = float(row.get("H4_close", np.nan))
    e = float(row.get("H4_ema100", np.nan))
    s = float(row.get("H4_ema100_slope", np.nan))
    if not all(math.isfinite(x) for x in [c, e, s]):
        return False, False, False
    down = c <= e and s <= 0
    up = c > e and s > 0
    neutral = not down and not up
    return down, up, neutral


def d1_state(row: pd.Series) -> tuple[bool, bool, bool]:
    c = float(row.get("D1_close", np.nan))
    e = float(row.get("D1_ema100", np.nan))
    s = float(row.get("D1_ema100_slope", np.nan))
    if not all(math.isfinite(x) for x in [c, e, s]):
        return False, False, False
    down = c <= e and s <= 0
    up = c > e and s > 0
    neutral = not down and not up
    return down, up, neutral


def build_source(h1: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    start_i = 220
    for i in range(start_i, len(h1) - 1):
        ts = h1.index[i]
        if holiday_market(ts):
            continue
        row = h1.iloc[i]
        atr = float(row["atr"])
        if not math.isfinite(atr) or atr <= 0:
            continue
        h4_down, h4_up, h4_neutral = h4_state(row)
        d1_down, d1_up, d1_neutral = d1_state(row)
        common = {
            "signal_i": i,
            "signal_time": ts,
            "entry_hour": int(h1.index[i + 1].hour),
            "atr": atr,
            "range_atr": float(row["range_atr"]),
            "body_ratio": float(row["body_ratio2"]),
            "upper_wick_ratio": float(row["upper_wick_ratio"]),
            "lower_wick_ratio": float(row["lower_wick_ratio"]),
            "close_location": float(row["close_loc_short"]),
            "bb_z": float(row["bb_z"]),
            "rsi14": float(row["rsi14"]),
            "ema20_dist_atr": float(row["ema20_dist_atr"]),
            "ema100_dist_atr": float(row["ema100_dist_atr"]),
            "h4_down": h4_down,
            "h4_up": h4_up,
            "h4_neutral": h4_neutral,
            "d1_down": d1_down,
            "d1_up": d1_up,
            "d1_neutral": d1_neutral,
            "h4_slope_atr": float(row["h4_slope_atr"]),
            "d1_slope_atr": float(row["d1_slope_atr"]),
        }

        # 1. Breakdown continuation: silver loses support and closes near low.
        for lb in [24, 48, 72, 96]:
            prior_low = float(row[f"prior_low_{lb}"])
            if math.isfinite(prior_low) and float(row["close"]) < prior_low:
                rows.append(
                    {
                        **common,
                        "family": "breakdown",
                        "lookback": lb,
                        "box_bars": 0,
                        "trigger_atr": (prior_low - float(row["close"])) / atr,
                        "move_6_atr": float(row["down_6_atr"]),
                        "move_12_atr": float(row["down_12_atr"]),
                        "move_24_atr": float(row["down_24_atr"]),
                        "pullback_atr": 0.0,
                        "box_width_atr": 999.0,
                        "stop_anchor": float(row["high"]),
                    }
                )

        # 2. Pullback box rebreak: trend down, bounce/stall, then box low break.
        for box in [6, 8, 12, 16]:
            box_low = float(row[f"box_low_{box}"])
            box_high = float(row[f"box_high_{box}"])
            box_width_atr = float(row[f"box_width_{box}_atr"])
            if math.isfinite(box_low) and math.isfinite(box_high) and float(row["close"]) < box_low:
                rows.append(
                    {
                        **common,
                        "family": "pullback_rebreak",
                        "lookback": 0,
                        "box_bars": box,
                        "trigger_atr": (box_low - float(row["close"])) / atr,
                        "move_6_atr": float(row["down_6_atr"]),
                        "move_12_atr": float(row["down_12_atr"]),
                        "move_24_atr": float(row["down_24_atr"]),
                        "pullback_atr": max(float(row["rise_6_atr"]), float(row["rise_12_atr"])),
                        "box_width_atr": box_width_atr,
                        "stop_anchor": box_high,
                    }
                )

        # 3. Failed high sweep: a high is taken, but the candle rejects it.
        for lb in [24, 48, 72, 96]:
            prior_high = float(row[f"prior_high_{lb}"])
            if math.isfinite(prior_high) and float(row["high"]) > prior_high and float(row["close"]) < prior_high:
                rows.append(
                    {
                        **common,
                        "family": "failed_high_sweep",
                        "lookback": lb,
                        "box_bars": 0,
                        "trigger_atr": (float(row["high"]) - prior_high) / atr,
                        "move_6_atr": float(row["rise_6_atr"]),
                        "move_12_atr": float(row["rise_12_atr"]),
                        "move_24_atr": float(row["rise_24_atr"]),
                        "pullback_atr": 0.0,
                        "box_width_atr": 999.0,
                        "stop_anchor": float(row["high"]),
                    }
                )

        # 4. Stretch wick short: overbought/upper-band extension that stalls.
        if float(row["bb_z"]) >= 1.6 or float(row["rsi14"]) >= 68.0 or float(row["ema20_dist_atr"]) >= 1.0:
            rows.append(
                {
                    **common,
                    "family": "stretch_wick_short",
                    "lookback": 20,
                    "box_bars": 0,
                    "trigger_atr": max(float(row["bb_z"]), float(row["ema20_dist_atr"])),
                    "move_6_atr": float(row["rise_6_atr"]),
                    "move_12_atr": float(row["rise_12_atr"]),
                    "move_24_atr": float(row["rise_24_atr"]),
                    "pullback_atr": 0.0,
                    "box_width_atr": 999.0,
                    "stop_anchor": float(row["high"]),
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["signal_i", "family"]).reset_index(drop=True)


def apply_spec(source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = source[source["family"] == spec["family"]].copy()
    if spec["lookback"] != "any":
        out = out[out["lookback"] == spec["lookback"]]
    if spec["box_bars"] != "any":
        out = out[out["box_bars"] == spec["box_bars"]]
    move_col = f"move_{spec['move_bars']}_atr"
    out = out[out[move_col] >= spec["move_atr"]]
    out = out[out["trigger_atr"] >= spec["trigger_atr"]]
    out = out[out["range_atr"] >= spec["range_atr"]]
    out = out[out["body_ratio"] <= spec["body_max"]]
    out = out[out["close_location"] >= spec["close_location"]]
    out = out[out["upper_wick_ratio"] >= spec["upper_wick"]]
    out = out[out["box_width_atr"] <= spec["box_width_max"]]
    out = out[out["pullback_atr"] >= spec["pullback_atr"]]
    if spec["bb_z"] is not None:
        out = out[out["bb_z"] >= spec["bb_z"]]
    if spec["rsi_high"] is not None:
        out = out[out["rsi14"] >= spec["rsi_high"]]
    if spec["h4"] == "down":
        out = out[out["h4_down"]]
    elif spec["h4"] == "not_up":
        out = out[~out["h4_up"]]
    elif spec["h4"] == "down_or_neutral":
        out = out[out["h4_down"] | out["h4_neutral"]]
    if spec["d1"] == "down":
        out = out[out["d1_down"]]
    elif spec["d1"] == "not_up":
        out = out[~out["d1_up"]]
    if spec["hour_filter"] == "no_rollover":
        out = out[~out["entry_hour"].isin([0, 21, 22, 23])]
    elif spec["hour_filter"] == "london_ny":
        out = out[out["entry_hour"].between(7, 20)]
    elif spec["hour_filter"] == "ex_11_12":
        out = out[~out["entry_hour"].isin([11, 12])]
    elif spec["hour_filter"] == "ex_7_11_12":
        out = out[~out["entry_hour"].isin([7, 11, 12])]
    return out.sort_values("signal_i")


def simulate_trade(h1: pd.DataFrame, sig: dict, spec: dict) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(h1):
        return None
    entry = float(h1["open"].iloc[entry_i])
    atr = float(sig["atr"])
    stop_anchor = float(sig["stop_anchor"])
    stop = stop_anchor + atr * spec["stop_buffer_atr"]
    risk = stop - entry
    if not math.isfinite(risk) or risk <= 0:
        return None
    if risk / atr > spec["max_risk_atr"]:
        return None
    target = entry - risk * spec["rr"]

    exit_i = min(len(h1) - 1, entry_i + spec["max_hold"])
    exit_price = float(h1["close"].iloc[exit_i])
    reason = "TIME"
    min_r = 0.0
    max_adverse_r = 0.0
    for j in range(entry_i, min(len(h1), entry_i + spec["max_hold"] + 1)):
        hi = float(h1["high"].iloc[j])
        lo = float(h1["low"].iloc[j])
        min_r = min(min_r, (entry - lo) / risk)
        max_adverse_r = max(max_adverse_r, (hi - entry) / risk)
        hit_sl = hi >= stop
        hit_tp = lo <= target
        if hit_sl or hit_tp:
            exit_i = j
            exit_price = stop if hit_sl else target
            reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
            break

    return {
        "entry_i": entry_i,
        "entry_time": h1.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "risk_atr": risk / atr,
        "exit_i": exit_i,
        "exit_time": h1.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "mae_r": max_adverse_r,
        "mfe_r": min_r,
        "r_after_cost": short_cost_r(entry, exit_price, risk),
    }


def run_trades(h1: pd.DataFrame, source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    filtered = apply_spec(source, spec)
    rows = []
    in_pos_until = -1
    for row in filtered.itertuples(index=False):
        sig = row._asdict()
        if int(sig["signal_i"]) <= in_pos_until:
            continue
        trade = simulate_trade(h1, sig, spec)
        if trade is None:
            continue
        rows.append({**sig, **trade})
        in_pos_until = int(trade["exit_i"])
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    out["sample"] = np.where(out["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    out["year"] = out["entry_time"].dt.year
    return out


def summarize(trades: pd.DataFrame) -> dict:
    empty = {
        "trades": 0,
        "wins": 0,
        "win_rate": np.nan,
        "total_r": 0.0,
        "avg_r": np.nan,
        "pf": np.nan,
        "max_dd_r": 0.0,
        "max_loss_streak": 0,
        "is_trades": 0,
        "is_r": 0.0,
        "oos_trades": 0,
        "oos_r": 0.0,
        "worst_year_r": 0.0,
        "worst_2y_r": 0.0,
        "avg_mae_r": np.nan,
        "avg_mfe_r": np.nan,
    }
    if trades.empty:
        return empty
    r = trades["r_after_cost"]
    by_year = trades.groupby("year")["r_after_cost"].sum().sort_index()
    rolling_2y = by_year.rolling(2).sum().dropna()
    is_df = trades[trades["sample"] == "IS_2014_2024"]
    oos_df = trades[trades["sample"] == "OOS_2025_2026"]
    return {
        "trades": len(trades),
        "wins": int((r > 0).sum()),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": float(profit_factor(r)),
        "max_dd_r": max_drawdown(r),
        "max_loss_streak": max_losing_streak(r),
        "is_trades": len(is_df),
        "is_r": float(is_df["r_after_cost"].sum()) if not is_df.empty else 0.0,
        "oos_trades": len(oos_df),
        "oos_r": float(oos_df["r_after_cost"].sum()) if not oos_df.empty else 0.0,
        "worst_year_r": float(by_year.min()) if not by_year.empty else 0.0,
        "worst_2y_r": float(rolling_2y.min()) if not rolling_2y.empty else float(by_year.min()),
        "avg_mae_r": float(trades["mae_r"].mean()),
        "avg_mfe_r": float(trades["mfe_r"].mean()),
    }


def score(row: dict) -> float:
    if row["trades"] < 20 or row["is_trades"] < 12 or row["oos_trades"] < 3:
        return -9999.0
    pf = 0.0 if not math.isfinite(float(row["pf"])) else min(float(row["pf"]), 4.0)
    return (
        row["avg_r"] * 100.0
        + min(row["total_r"], 45.0) * 0.35
        + pf * 5.0
        - row["max_dd_r"] * 0.90
        + min(row["oos_r"], 0.0) * 10.0
        + min(row["worst_2y_r"], 0.0) * 2.0
        - max(0.0, row["avg_mae_r"] - 0.7) * 10.0
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
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


def main() -> None:
    h1 = prepare_h1()
    source = build_source(h1)
    source.to_csv(OUT_DIR / "silver_short_source.csv", index=False)

    configs = [
        {
            "family": ["breakdown"],
            "lookback": [48, 72],
            "box_bars": ["any"],
            "move_bars": [6, 12],
            "move_atr": [0.8, 1.2],
            "trigger_atr": [0.05, 0.15],
            "range_atr": [0.8],
            "body_max": [0.85],
            "close_location": [0.70, 0.80],
            "upper_wick": [0.0],
            "box_width_max": [999.0],
            "pullback_atr": [0.0],
            "bb_z": [None],
            "rsi_high": [None],
            "h4": ["down", "not_up"],
            "d1": ["any"],
            "hour_filter": ["all", "no_rollover", "ex_11_12"],
            "rr": [0.8, 1.0, 1.2],
            "stop_buffer_atr": [0.15, 0.25],
            "max_risk_atr": [2.5],
            "max_hold": [12, 24],
        },
        {
            "family": ["pullback_rebreak"],
            "lookback": ["any"],
            "box_bars": [8, 12],
            "move_bars": [12, 24],
            "move_atr": [0.0, 0.8],
            "trigger_atr": [0.05],
            "range_atr": [0.5],
            "body_max": [0.85],
            "close_location": [0.65, 0.75],
            "upper_wick": [0.0],
            "box_width_max": [1.5, 2.5],
            "pullback_atr": [0.6, 1.0],
            "bb_z": [None],
            "rsi_high": [None],
            "h4": ["down", "not_up"],
            "d1": ["any"],
            "hour_filter": ["all", "no_rollover", "ex_11_12", "ex_7_11_12"],
            "rr": [0.8, 1.0, 1.2],
            "stop_buffer_atr": [0.15, 0.25],
            "max_risk_atr": [2.5],
            "max_hold": [12, 24],
        },
        {
            "family": ["failed_high_sweep"],
            "lookback": [48, 72],
            "box_bars": ["any"],
            "move_bars": [6, 12],
            "move_atr": [0.8, 1.2],
            "trigger_atr": [0.05, 0.15],
            "range_atr": [0.7],
            "body_max": [0.85],
            "close_location": [0.65, 0.75],
            "upper_wick": [0.45, 0.55],
            "box_width_max": [999.0],
            "pullback_atr": [0.0],
            "bb_z": [None, 1.6],
            "rsi_high": [None],
            "h4": ["not_up", "down_or_neutral"],
            "d1": ["any"],
            "hour_filter": ["all", "no_rollover", "ex_11_12"],
            "rr": [0.6, 0.8, 1.0],
            "stop_buffer_atr": [0.15, 0.25],
            "max_risk_atr": [2.5],
            "max_hold": [8, 12, 24],
        },
        {
            "family": ["stretch_wick_short"],
            "lookback": ["any"],
            "box_bars": ["any"],
            "move_bars": [6, 12],
            "move_atr": [0.8, 1.2],
            "trigger_atr": [1.2, 1.8],
            "range_atr": [0.7],
            "body_max": [0.85],
            "close_location": [0.65, 0.75],
            "upper_wick": [0.40, 0.55],
            "box_width_max": [999.0],
            "pullback_atr": [0.0],
            "bb_z": [1.6, 2.0],
            "rsi_high": [None, 68.0],
            "h4": ["not_up", "down_or_neutral"],
            "d1": ["any"],
            "hour_filter": ["all", "no_rollover", "ex_11_12"],
            "rr": [0.6, 0.8, 1.0],
            "stop_buffer_atr": [0.15, 0.25],
            "max_risk_atr": [2.5],
            "max_hold": [8, 12, 24],
        },
    ]

    rows: list[dict] = []
    best_by_family: dict[str, tuple[dict, pd.DataFrame]] = {}
    total = sum(math.prod(len(v) for v in cfg.values()) for cfg in configs)
    done = 0
    for cfg in configs:
        for combo in itertools.product(*cfg.values()):
            spec = dict(zip(cfg.keys(), combo))
            trades = run_trades(h1, source, spec)
            summary = summarize(trades)
            row = {**spec, **summary}
            row["score"] = score(row)
            rows.append(row)
            family = str(spec["family"])
            if row["score"] > -9999 and (
                family not in best_by_family or row["score"] > best_by_family[family][0]["score"]
            ):
                best_by_family[family] = (row, trades)
            done += 1
            if done % 1000 == 0:
                print(f"progress {done}/{total}", flush=True)

    grid = pd.DataFrame(rows).sort_values("score", ascending=False)
    grid.to_csv(OUT_DIR / "silver_short_grid.csv", index=False)
    top = grid[grid["score"] > -9999].head(100).copy()
    top.to_csv(OUT_DIR / "silver_short_top.csv", index=False)

    family_summary = (
        grid[grid["score"] > -9999]
        .groupby("family", as_index=False)
        .head(1)
        .sort_values("score", ascending=False)
    )
    family_summary.to_csv(OUT_DIR / "silver_short_family_summary.csv", index=False)

    for family, (_, trades) in best_by_family.items():
        trades.to_csv(OUT_DIR / f"silver_short_{family}_best_trades.csv", index=False)

    cols = [
        "family",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "is_trades",
        "is_r",
        "oos_trades",
        "oos_r",
        "worst_year_r",
        "worst_2y_r",
        "avg_mae_r",
        "lookback",
        "box_bars",
        "move_bars",
        "move_atr",
        "trigger_atr",
        "close_location",
        "upper_wick",
        "bb_z",
        "rsi_high",
        "h4",
        "d1",
        "rr",
        "max_hold",
        "stop_buffer_atr",
        "hour_filter",
    ]
    md = []
    md.append("# SILVER H1 Short System Research")
    md.append("")
    md.append(f"- Data: `{h1.index.min()}` to `{h1.index.max()}`")
    md.append(f"- OOS: `{OOS_START.date()}` onward")
    md.append(f"- Cost: spread `{SPREAD_PRICE}`, slip `{SLIP_PRICE}`")
    md.append("- Direction: short only")
    md.append("")
    md.append("## Best By Family")
    md.append("")
    md.append(markdown_table(family_summary[cols], 20))
    md.append("")
    md.append("## Top Candidates")
    md.append("")
    md.append(markdown_table(top[cols], 30))
    md.append("")
    md.append("## Reading")
    md.append("")
    md.append("- `breakdown`: support break continuation.")
    md.append("- `pullback_rebreak`: downtrend pullback/stall, then box-low rebreak.")
    md.append("- `failed_high_sweep`: prior high sweep that closes back under the level.")
    md.append("- `stretch_wick_short`: local upside stretch with upper-wick stall.")
    md.append("")
    (OUT_DIR / "report_ja.md").write_text("\n".join(md), encoding="utf-8")

    print(f"rows={len(grid)} valid={len(top)} source={len(source)}")
    print(f"output={OUT_DIR}")
    if not top.empty:
        print(top[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()

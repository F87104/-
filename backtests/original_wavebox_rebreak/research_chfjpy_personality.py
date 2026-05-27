#!/usr/bin/env python3
"""
CHFJPY H1 personality research.

Goal:
  Find strategy hints from CHFJPY's own behavior instead of copying USDJPY or
  GBPJPY presets.  Two families are tested:
    1. failed sweep / wick reversal
    2. simple Donchian breakout continuation
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
OUT_DIR = THIS_DIR / "results_2026_05_27" / "chfjpy_personality"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))
sys.path.insert(0, str(THIS_DIR))

from sai_backtest import load_instrument  # noqa: E402
import run_wavebox_rebreak as wb  # noqa: E402


SYMBOL = "CHFJPY"
START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")
SPREAD_PRICE = 0.020
SLIP_PRICE = 0.010

LOOKBACKS = [24, 48, 72]
PREMOVE_BARS = [6, 12]
RR_LIST = [1.0, 1.2, 1.5]
MAX_HOLD_LIST = [12, 24]
H4_FILTERS = ["any", "not_oppose", "align"]
DIRECTION_FILTERS = ["long", "short", "both"]


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


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


def direction_cost_r(direction: str, entry: float, exit_price: float, risk: float) -> float:
    if direction == "long":
        after = (exit_price - SLIP_PRICE) - (entry + SPREAD_PRICE / 2.0)
    else:
        after = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return after / risk


def prepare_h1() -> pd.DataFrame:
    raw = load_instrument(SYMBOL).loc[START:END].copy()
    raw["volume"] = 0.0
    h1 = wb.add_indicators(raw, "H1")
    h4 = wb.add_indicators(wb.resample_ohlc(raw, "4h"), "H4")
    h1 = wb.attach_upper_context(h1, {"H4": h4}, "H1")

    rng = (h1["high"] - h1["low"]).replace(0, np.nan)
    h1["range_atr"] = rng / h1["atr"]
    h1["body_ratio2"] = (h1["close"] - h1["open"]).abs() / rng
    h1["upper_wick_ratio"] = (h1["high"] - h1[["open", "close"]].max(axis=1)) / rng
    h1["lower_wick_ratio"] = (h1[["open", "close"]].min(axis=1) - h1["low"]) / rng
    h1["close_loc_long"] = (h1["close"] - h1["low"]) / rng
    h1["close_loc_short"] = (h1["high"] - h1["close"]) / rng
    for lb in LOOKBACKS:
        h1[f"prior_high_{lb}"] = h1["high"].shift(1).rolling(lb).max()
        h1[f"prior_low_{lb}"] = h1["low"].shift(1).rolling(lb).min()
    for bars in PREMOVE_BARS:
        h1[f"drop_{bars}_atr"] = (h1["close"].shift(bars) - h1["low"]) / h1["atr"]
        h1[f"rise_{bars}_atr"] = (h1["high"] - h1["close"].shift(bars)) / h1["atr"]
        h1[f"up_{bars}_atr"] = (h1["close"] - h1["close"].shift(bars)) / h1["atr"]
        h1[f"down_{bars}_atr"] = (h1["close"].shift(bars) - h1["close"]) / h1["atr"]
    return h1


def h4_state(row: pd.Series, direction: str) -> tuple[bool, bool, str]:
    c = row.get("H4_close", np.nan)
    e = row.get("H4_ema100", np.nan)
    s = row.get("H4_ema100_slope", np.nan)
    if not all(math.isfinite(float(x)) for x in [c, e, s]):
        return False, False, "H4_NA"
    if direction == "long":
        align = c >= e and s >= 0
        oppose = c < e and s < 0
    else:
        align = c <= e and s <= 0
        oppose = c > e and s > 0
    return align, oppose, "H4順" if align else "H4逆" if oppose else "H4中立"


def generate_wick_source(h1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(max(LOOKBACKS + PREMOVE_BARS) + 1, len(h1) - 1):
        ts = h1.index[i]
        if holiday_market(ts):
            continue
        row = h1.iloc[i]
        atr = float(row["atr"])
        if not math.isfinite(atr) or atr <= 0:
            continue
        for lb in LOOKBACKS:
            prior_low = float(row[f"prior_low_{lb}"])
            prior_high = float(row[f"prior_high_{lb}"])
            if not (math.isfinite(prior_low) and math.isfinite(prior_high)):
                continue
            long_sweep_atr = (prior_low - float(row["low"])) / atr
            short_sweep_atr = (float(row["high"]) - prior_high) / atr
            if long_sweep_atr >= 0 and float(row["close"]) > prior_low:
                align, oppose, note = h4_state(row, "long")
                for pre in PREMOVE_BARS:
                    rows.append(
                        {
                            "family": "wick_sweep",
                            "signal_i": i,
                            "signal_time": ts,
                            "direction": "long",
                            "lookback": lb,
                            "pre_bars": pre,
                            "move_atr": float(row[f"drop_{pre}_atr"]),
                            "trigger_atr": long_sweep_atr,
                            "wick_ratio": float(row["lower_wick_ratio"]),
                            "close_location": float(row["close_loc_long"]),
                            "range_atr": float(row["range_atr"]),
                            "body_ratio": float(row["body_ratio2"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_context": note,
                            "entry_hour": int(h1.index[i + 1].hour),
                            "stop": float(row["low"]) - atr * 0.20,
                        }
                    )
            if short_sweep_atr >= 0 and float(row["close"]) < prior_high:
                align, oppose, note = h4_state(row, "short")
                for pre in PREMOVE_BARS:
                    rows.append(
                        {
                            "family": "wick_sweep",
                            "signal_i": i,
                            "signal_time": ts,
                            "direction": "short",
                            "lookback": lb,
                            "pre_bars": pre,
                            "move_atr": float(row[f"rise_{pre}_atr"]),
                            "trigger_atr": short_sweep_atr,
                            "wick_ratio": float(row["upper_wick_ratio"]),
                            "close_location": float(row["close_loc_short"]),
                            "range_atr": float(row["range_atr"]),
                            "body_ratio": float(row["body_ratio2"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_context": note,
                            "entry_hour": int(h1.index[i + 1].hour),
                            "stop": float(row["high"]) + atr * 0.20,
                        }
                    )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["signal_i", "direction"]).reset_index(drop=True)


def generate_breakout_source(h1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(max(LOOKBACKS + PREMOVE_BARS) + 1, len(h1) - 1):
        ts = h1.index[i]
        if holiday_market(ts):
            continue
        row = h1.iloc[i]
        atr = float(row["atr"])
        if not math.isfinite(atr) or atr <= 0:
            continue
        for lb in LOOKBACKS:
            prior_low = float(row[f"prior_low_{lb}"])
            prior_high = float(row[f"prior_high_{lb}"])
            if not (math.isfinite(prior_low) and math.isfinite(prior_high)):
                continue
            long_break_atr = (float(row["close"]) - prior_high) / atr
            short_break_atr = (prior_low - float(row["close"])) / atr
            if long_break_atr >= 0:
                align, oppose, note = h4_state(row, "long")
                for pre in PREMOVE_BARS:
                    rows.append(
                        {
                            "family": "breakout",
                            "signal_i": i,
                            "signal_time": ts,
                            "direction": "long",
                            "lookback": lb,
                            "pre_bars": pre,
                            "move_atr": float(row[f"up_{pre}_atr"]),
                            "trigger_atr": long_break_atr,
                            "wick_ratio": float(row["upper_wick_ratio"]),
                            "close_location": float(row["close_loc_long"]),
                            "range_atr": float(row["range_atr"]),
                            "body_ratio": float(row["body_ratio2"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_context": note,
                            "entry_hour": int(h1.index[i + 1].hour),
                            "stop": float(row["low"]) - atr * 0.20,
                        }
                    )
            if short_break_atr >= 0:
                align, oppose, note = h4_state(row, "short")
                for pre in PREMOVE_BARS:
                    rows.append(
                        {
                            "family": "breakout",
                            "signal_i": i,
                            "signal_time": ts,
                            "direction": "short",
                            "lookback": lb,
                            "pre_bars": pre,
                            "move_atr": float(row[f"down_{pre}_atr"]),
                            "trigger_atr": short_break_atr,
                            "wick_ratio": float(row["lower_wick_ratio"]),
                            "close_location": float(row["close_loc_short"]),
                            "range_atr": float(row["range_atr"]),
                            "body_ratio": float(row["body_ratio2"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_context": note,
                            "entry_hour": int(h1.index[i + 1].hour),
                            "stop": float(row["high"]) + atr * 0.20,
                        }
                    )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["signal_i", "direction"]).reset_index(drop=True)


def apply_filter(source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = source
    if spec["direction"] != "both":
        out = out[out["direction"] == spec["direction"]]
    out = out[out["lookback"] == spec["lookback"]]
    out = out[out["pre_bars"] == spec["pre_bars"]]
    out = out[out["trigger_atr"] >= spec["trigger_atr"]]
    out = out[out["move_atr"] >= spec["move_atr"]]
    out = out[out["range_atr"] >= spec["range_atr"]]
    out = out[out["body_ratio"] >= spec["body_min"]]
    out = out[out["body_ratio"] <= spec["body_max"]]
    out = out[out["close_location"] >= spec["close_location"]]
    if spec["family"] == "wick_sweep":
        out = out[out["wick_ratio"] >= spec["wick_ratio"]]
    else:
        out = out[out["wick_ratio"] <= spec["wick_max"]]
    if spec["h4"] == "not_oppose":
        out = out[~out["h4_oppose"]]
    elif spec["h4"] == "align":
        out = out[out["h4_align"]]
    return out.sort_values("signal_i").copy()


def simulate_trade(h1: pd.DataFrame, sig: dict, rr: float, max_hold: int) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(h1):
        return None
    direction = sig["direction"]
    entry = float(h1["open"].iloc[entry_i])
    stop = float(sig["stop"])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * rr
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * rr
    exit_i = min(len(h1) - 1, entry_i + max_hold)
    exit_price = float(h1["close"].iloc[exit_i])
    reason = "TIME"
    for j in range(entry_i, min(len(h1), entry_i + max_hold + 1)):
        hi = float(h1["high"].iloc[j])
        lo = float(h1["low"].iloc[j])
        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = hi >= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break
        else:
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
        "target": target,
        "exit_i": exit_i,
        "exit_time": h1.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "rr": rr,
        "max_hold": max_hold,
        "r_after_cost": direction_cost_r(direction, entry, exit_price, risk),
    }


def run_filtered_trades(h1: pd.DataFrame, source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    filtered = apply_filter(source, spec)
    rows = []
    in_pos_until = -1
    seen: set[tuple] = set()
    for row in filtered.itertuples(index=False):
        sig = row._asdict()
        if int(sig["signal_i"]) <= in_pos_until:
            continue
        key = (sig["signal_i"], sig["direction"])
        if key in seen:
            continue
        trade = simulate_trade(h1, sig, spec["rr"], spec["max_hold"])
        if trade is None:
            continue
        rows.append({**sig, **trade})
        seen.add(key)
        in_pos_until = int(trade["exit_i"])
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    out["sample"] = np.where(out["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    out["year"] = out["entry_time"].dt.year
    return out


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "is_trades": 0,
            "is_r": 0.0,
            "oos_trades": 0,
            "oos_r": 0.0,
        }
    r = df["r_after_cost"]
    by_year = df.groupby("year")["r_after_cost"].sum()
    years = sorted(df["year"].unique())
    rolling_2y = []
    for start in years:
        sub = df[(df["year"] >= start) & (df["year"] <= start + 1)]
        if not sub.empty:
            rolling_2y.append(float(sub["r_after_cost"].sum()))
    is_df = df[df["entry_time"] < OOS_START]
    oos_df = df[df["entry_time"] >= OOS_START]
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "worst_year_r": float(by_year.min()) if len(by_year) else np.nan,
        "worst_2y_r": float(min(rolling_2y)) if rolling_2y else np.nan,
        "is_trades": int(len(is_df)),
        "is_r": float(is_df["r_after_cost"].sum()) if len(is_df) else 0.0,
        "oos_trades": int(len(oos_df)),
        "oos_r": float(oos_df["r_after_cost"].sum()) if len(oos_df) else 0.0,
    }


def score(row: dict) -> float:
    if row["trades"] < 25 or row["is_trades"] < 18 or row["oos_trades"] < 3:
        return -9999.0
    return (
        row["avg_r"] * 90.0
        + min(row["total_r"], 40.0) * 0.35
        + min(row["pf"], 4.0) * 5.0
        - row["max_dd_r"] * 0.70
        - max(row["max_losing_streak"] - 5, 0) * 1.2
        + min(row["worst_2y_r"], 0.0) * 2.0
        + min(row["oos_r"], 0.0) * 10.0
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
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


def baseline_wavebox() -> tuple[pd.DataFrame, pd.DataFrame]:
    path = THIS_DIR / "results_2026_05_25" / "cross_symbol_h1" / "trades.csv"
    if not path.exists():
        return pd.DataFrame(), pd.DataFrame()
    trades = pd.read_csv(path, parse_dates=["entry_time"])
    chf = trades[trades["symbol"] == SYMBOL].copy()
    if chf.empty:
        return chf, pd.DataFrame()
    rows = []
    for group_name, group_cols in {
        "direction": ["direction"],
        "h4": ["upper_context"],
        "sample": ["sample"],
    }.items():
        for key, g in chf.groupby(group_cols):
            r = g["r_after_cost"]
            rows.append(
                {
                    "axis": group_name,
                    "bucket": key if isinstance(key, str) else "/".join(map(str, key)),
                    "trades": len(g),
                    "win_rate": (r > 0).mean() * 100,
                    "total_r": r.sum(),
                    "avg_r": r.mean(),
                    "pf": profit_factor(r),
                }
            )
    return chf, pd.DataFrame(rows)


def write_report(
    coverage: dict,
    baseline_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    top: pd.DataFrame,
    chosen_trades: dict[str, pd.DataFrame],
) -> None:
    cols = [
        "family",
        "score",
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
        "direction",
        "lookback",
        "pre_bars",
        "trigger_atr",
        "move_atr",
        "wick_ratio",
        "wick_max",
        "close_location",
        "range_atr",
        "body_min",
        "body_max",
        "h4",
        "rr",
        "max_hold",
    ]
    trade_cols = [
        "entry_time",
        "family",
        "direction",
        "entry",
        "exit_time",
        "exit_reason",
        "r_after_cost",
        "lookback",
        "trigger_atr",
        "move_atr",
        "wick_ratio",
        "close_location",
        "range_atr",
        "body_ratio",
        "h4_context",
    ]
    lines = [
        "# CHFJPY Personality Research",
        "",
        "## Data",
        "",
        f"- rows: `{coverage['rows']}`",
        f"- first: `{coverage['first']}`",
        f"- last: `{coverage['last']}`",
        "",
        "## Existing WaveBox Baseline",
        "",
        markdown_table(baseline_summary, 50),
        "",
        "## Family Summary",
        "",
        markdown_table(family_summary, 20),
        "",
        "## Top Candidates",
        "",
        markdown_table(top[cols], 50),
    ]
    for name, trades in chosen_trades.items():
        lines += [
            "",
            f"## Chosen Trades: {name}",
            "",
            markdown_table(trades[trade_cols] if not trades.empty else trades, 80),
        ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    h1 = prepare_h1()
    coverage = {"rows": len(h1), "first": h1.index.min(), "last": h1.index.max()}

    wavebox_trades, baseline_summary = baseline_wavebox()
    wavebox_trades.to_csv(OUT_DIR / "chfjpy_wavebox_baseline_trades.csv", index=False)
    baseline_summary.to_csv(OUT_DIR / "chfjpy_wavebox_baseline_summary.csv", index=False)

    wick_source = generate_wick_source(h1)
    breakout_source = generate_breakout_source(h1)
    wick_source.to_csv(OUT_DIR / "chfjpy_wick_source.csv", index=False)
    breakout_source.to_csv(OUT_DIR / "chfjpy_breakout_source.csv", index=False)

    grid_rows = []
    family_configs = [
        (
            "wick_sweep",
            wick_source,
            {
                "direction": DIRECTION_FILTERS,
                "lookback": [24, 48],
                "pre_bars": PREMOVE_BARS,
                "trigger_atr": [0.05],
                "move_atr": [0.8, 1.2],
                "wick_ratio": [0.55, 0.65],
                "wick_max": [1.0],
                "close_location": [0.65, 0.75],
                "range_atr": [1.0],
                "body_min": [0.0],
                "body_max": [0.65],
                "h4": H4_FILTERS,
                "rr": [1.0, 1.2],
                "max_hold": [12, 24],
            },
        ),
        (
            "breakout",
            breakout_source,
            {
                "direction": DIRECTION_FILTERS,
                "lookback": [24, 48],
                "pre_bars": PREMOVE_BARS,
                "trigger_atr": [0.05],
                "move_atr": [0.8, 1.2],
                "wick_ratio": [0.0],
                "wick_max": [0.45, 0.60],
                "close_location": [0.60, 0.70],
                "range_atr": [0.8],
                "body_min": [0.35, 0.50],
                "body_max": [1.0],
                "h4": H4_FILTERS,
                "rr": RR_LIST,
                "max_hold": MAX_HOLD_LIST,
            },
        ),
    ]

    best_by_family: dict[str, tuple[dict, pd.DataFrame]] = {}
    total = sum(math.prod(len(v) for v in config.values()) for _, _, config in family_configs)
    done = 0
    for family, source, config in family_configs:
        for combo in itertools.product(*config.values()):
            spec = {"family": family, **dict(zip(config.keys(), combo))}
            trades = run_filtered_trades(h1, source, spec)
            row = {**spec, **summarize(trades)}
            row["score"] = score(row)
            grid_rows.append(row)
            if row["score"] > -9999 and (
                family not in best_by_family or row["score"] > best_by_family[family][0]["score"]
            ):
                best_by_family[family] = (row, trades)
            done += 1
            if done % 3000 == 0:
                print(f"progress {done}/{total}", flush=True)

    grid = pd.DataFrame(grid_rows).sort_values("score", ascending=False)
    grid.to_csv(OUT_DIR / "chfjpy_personality_grid.csv", index=False)
    top = grid[grid["score"] > -9999].head(80).copy()
    top.to_csv(OUT_DIR / "chfjpy_top_candidates.csv", index=False)

    family_summary = (
        grid[grid["score"] > -9999]
        .groupby("family", as_index=False)
        .head(1)
        .sort_values("score", ascending=False)
    )
    family_summary.to_csv(OUT_DIR / "chfjpy_family_summary.csv", index=False)

    chosen_trades = {}
    for family, (_, trades) in best_by_family.items():
        chosen_trades[family] = trades
        trades.to_csv(OUT_DIR / f"chfjpy_{family}_chosen_trades.csv", index=False)

    write_report(coverage, baseline_summary, family_summary, top, chosen_trades)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(family_summary.to_string(index=False))
    print(top.head(20).to_string(index=False))


if __name__ == "__main__":
    main()

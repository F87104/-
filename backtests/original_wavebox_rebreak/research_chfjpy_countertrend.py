#!/usr/bin/env python3
"""CHFJPY countertrend research.

The prior CHFJPY probe showed that continuation breakouts are weak and simple
failed sweeps are only marginal.  This pass focuses on countertrend ideas that
match CHFJPY's observed behavior:

1. failed breakdown/breakout reclaim
2. Bollinger/EMA stretch reversal
3. RSI exhaustion reversal
4. range-edge rejection
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

import research_chfjpy_personality as rp


OUT_DIR = Path(__file__).resolve().parent / "results_2026_05_27" / "chfjpy_countertrend"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def add_countertrend_features(h1: pd.DataFrame) -> pd.DataFrame:
    out = h1.copy()
    out["rsi14"] = rsi(out["close"], 14)
    out["sma20"] = out["close"].rolling(20).mean()
    out["std20"] = out["close"].rolling(20).std()
    out["bb_z"] = (out["close"] - out["sma20"]) / out["std20"].replace(0.0, np.nan)
    out["ema20_dist_atr"] = (out["close"] - out["ema20"]) / out["atr"]
    out["ema100_slope_atr"] = out["ema100_slope"] / out["atr"]
    out["h4_slope_atr"] = out["H4_ema100_slope"] / out["atr"]
    for lb in [48, 72, 96]:
        out[f"range_high_{lb}"] = out["high"].shift(1).rolling(lb).max()
        out[f"range_low_{lb}"] = out["low"].shift(1).rolling(lb).min()
        out[f"range_width_{lb}_atr"] = (out[f"range_high_{lb}"] - out[f"range_low_{lb}"]) / out["atr"]
    return out


def trend_state(row: pd.Series, direction: str) -> tuple[bool, bool, bool, str]:
    """Return align, oppose, neutral, note for a countertrend setup direction."""
    align, oppose, note = rp.h4_state(row, direction)
    slope_abs = abs(float(row.get("h4_slope_atr", np.nan)))
    neutral = (not align and not oppose) or (math.isfinite(slope_abs) and slope_abs <= 0.35)
    return align, oppose, neutral, note


def build_source(h1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    max_lb = 96
    for i in range(max_lb + 20, len(h1) - 1):
        ts = h1.index[i]
        if rp.holiday_market(ts):
            continue
        row = h1.iloc[i]
        atr = float(row["atr"])
        if not math.isfinite(atr) or atr <= 0:
            continue

        common = {
            "signal_i": i,
            "signal_time": ts,
            "entry_hour": int(h1.index[i + 1].hour),
            "atr": atr,
            "rsi14": float(row["rsi14"]),
            "bb_z": float(row["bb_z"]),
            "range_atr": float(row["range_atr"]),
            "body_ratio": float(row["body_ratio2"]),
            "ema20_dist_atr": float(row["ema20_dist_atr"]),
            "ema100_slope_atr": float(row["ema100_slope_atr"]),
            "h4_slope_atr": float(row["h4_slope_atr"]),
        }

        for lb in [48, 72]:
            prior_low = float(row[f"prior_low_{lb}"])
            prior_high = float(row[f"prior_high_{lb}"])
            if math.isfinite(prior_low):
                sweep_atr = (prior_low - float(row["low"])) / atr
                if sweep_atr >= 0 and float(row["close"]) > prior_low:
                    align, oppose, neutral, note = trend_state(row, "long")
                    rows.append(
                        {
                            **common,
                            "family": "failed_sweep",
                            "direction": "long",
                            "lookback": lb,
                            "move_6_atr": float(row["drop_6_atr"]),
                            "move_12_atr": float(row["drop_12_atr"]),
                            "trigger_atr": sweep_atr,
                            "wick_ratio": float(row["lower_wick_ratio"]),
                            "close_location": float(row["close_loc_long"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_neutral": neutral,
                            "h4_context": note,
                            "stop_anchor": float(row["low"]),
                        }
                    )
            if math.isfinite(prior_high):
                sweep_atr = (float(row["high"]) - prior_high) / atr
                if sweep_atr >= 0 and float(row["close"]) < prior_high:
                    align, oppose, neutral, note = trend_state(row, "short")
                    rows.append(
                        {
                            **common,
                            "family": "failed_sweep",
                            "direction": "short",
                            "lookback": lb,
                            "move_6_atr": float(row["rise_6_atr"]),
                            "move_12_atr": float(row["rise_12_atr"]),
                            "trigger_atr": sweep_atr,
                            "wick_ratio": float(row["upper_wick_ratio"]),
                            "close_location": float(row["close_loc_short"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_neutral": neutral,
                            "h4_context": note,
                            "stop_anchor": float(row["high"]),
                        }
                    )

        lower_extreme = (
            float(row["bb_z"]) <= -1.8
            or float(row["ema20_dist_atr"]) <= -1.2
            or float(row["rsi14"]) <= 30
        )
        upper_extreme = (
            float(row["bb_z"]) >= 1.8
            or float(row["ema20_dist_atr"]) >= 1.2
            or float(row["rsi14"]) >= 70
        )
        if lower_extreme:
            align, oppose, neutral, note = trend_state(row, "long")
            rows.append(
                {
                    **common,
                    "family": "stretch_reversal",
                    "direction": "long",
                    "lookback": 20,
                    "move_6_atr": float(row["drop_6_atr"]),
                    "move_12_atr": float(row["drop_12_atr"]),
                    "trigger_atr": abs(float(row["ema20_dist_atr"])),
                    "wick_ratio": float(row["lower_wick_ratio"]),
                    "close_location": float(row["close_loc_long"]),
                    "h4_align": align,
                    "h4_oppose": oppose,
                    "h4_neutral": neutral,
                    "h4_context": note,
                    "stop_anchor": float(row["low"]),
                }
            )
        if upper_extreme:
            align, oppose, neutral, note = trend_state(row, "short")
            rows.append(
                {
                    **common,
                    "family": "stretch_reversal",
                    "direction": "short",
                    "lookback": 20,
                    "move_6_atr": float(row["rise_6_atr"]),
                    "move_12_atr": float(row["rise_12_atr"]),
                    "trigger_atr": abs(float(row["ema20_dist_atr"])),
                    "wick_ratio": float(row["upper_wick_ratio"]),
                    "close_location": float(row["close_loc_short"]),
                    "h4_align": align,
                    "h4_oppose": oppose,
                    "h4_neutral": neutral,
                    "h4_context": note,
                    "stop_anchor": float(row["high"]),
                }
            )

        for lb in [72, 96]:
            range_low = float(row[f"range_low_{lb}"])
            range_high = float(row[f"range_high_{lb}"])
            range_width = float(row[f"range_width_{lb}_atr"])
            if math.isfinite(range_low) and math.isfinite(range_width):
                touch_atr = (range_low - float(row["low"])) / atr
                if touch_atr >= -0.10 and float(row["close"]) > range_low:
                    align, oppose, neutral, note = trend_state(row, "long")
                    rows.append(
                        {
                            **common,
                            "family": "range_edge",
                            "direction": "long",
                            "lookback": lb,
                            "range_width_atr": range_width,
                            "move_6_atr": float(row["drop_6_atr"]),
                            "move_12_atr": float(row["drop_12_atr"]),
                            "trigger_atr": touch_atr,
                            "wick_ratio": float(row["lower_wick_ratio"]),
                            "close_location": float(row["close_loc_long"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_neutral": neutral,
                            "h4_context": note,
                            "stop_anchor": float(row["low"]),
                        }
                    )
            if math.isfinite(range_high) and math.isfinite(range_width):
                touch_atr = (float(row["high"]) - range_high) / atr
                if touch_atr >= -0.10 and float(row["close"]) < range_high:
                    align, oppose, neutral, note = trend_state(row, "short")
                    rows.append(
                        {
                            **common,
                            "family": "range_edge",
                            "direction": "short",
                            "lookback": lb,
                            "range_width_atr": range_width,
                            "move_6_atr": float(row["rise_6_atr"]),
                            "move_12_atr": float(row["rise_12_atr"]),
                            "trigger_atr": touch_atr,
                            "wick_ratio": float(row["upper_wick_ratio"]),
                            "close_location": float(row["close_loc_short"]),
                            "h4_align": align,
                            "h4_oppose": oppose,
                            "h4_neutral": neutral,
                            "h4_context": note,
                            "stop_anchor": float(row["high"]),
                        }
                    )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    if "range_width_atr" not in out.columns:
        out["range_width_atr"] = np.nan
    out["range_width_atr"] = out["range_width_atr"].fillna(999.0)
    return out.replace([np.inf, -np.inf], np.nan).dropna().sort_values(["signal_i", "family", "direction"]).reset_index(drop=True)


def apply_spec(source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = source[source["family"] == spec["family"]].copy()
    if spec["direction"] != "both":
        out = out[out["direction"] == spec["direction"]]
    if spec["lookback"] != "any":
        out = out[out["lookback"] == spec["lookback"]]
    move_col = "move_6_atr" if spec["move_bars"] == 6 else "move_12_atr"
    out = out[out[move_col] >= spec["move_atr"]]
    out = out[out["trigger_atr"] >= spec["trigger_atr"]]
    out = out[out["wick_ratio"] >= spec["wick_ratio"]]
    out = out[out["close_location"] >= spec["close_location"]]
    out = out[out["range_atr"] >= spec["bar_range_atr"]]
    out = out[out["body_ratio"] <= spec["body_max"]]
    out = out[out["range_width_atr"] <= spec["range_width_max"]]
    if spec["family"] == "stretch_reversal":
        if spec["direction"] == "long":
            out = out[(out["bb_z"] <= -spec["bb_z"]) | (out["rsi14"] <= spec["rsi_low"])]
        elif spec["direction"] == "short":
            out = out[(out["bb_z"] >= spec["bb_z"]) | (out["rsi14"] >= spec["rsi_high"])]
        else:
            out = out[
                ((out["direction"] == "long") & ((out["bb_z"] <= -spec["bb_z"]) | (out["rsi14"] <= spec["rsi_low"])))
                | ((out["direction"] == "short") & ((out["bb_z"] >= spec["bb_z"]) | (out["rsi14"] >= spec["rsi_high"])))
            ]
    if spec["h4"] == "neutral":
        out = out[out["h4_neutral"]]
    elif spec["h4"] == "not_oppose":
        out = out[~out["h4_oppose"]]
    elif spec["h4"] == "against":
        out = out[out["h4_oppose"]]
    hours = spec.get("hours")
    if hours:
        out = out[out["entry_hour"].isin(hours)]
    return out.sort_values("signal_i")


def simulate_trade(h1: pd.DataFrame, sig: dict, spec: dict) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(h1):
        return None
    direction = sig["direction"]
    entry = float(h1["open"].iloc[entry_i])
    atr = float(sig["atr"])
    stop_anchor = float(sig["stop_anchor"])
    if direction == "long":
        stop = stop_anchor - atr * spec["stop_buffer_atr"]
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * spec["rr"]
    else:
        stop = stop_anchor + atr * spec["stop_buffer_atr"]
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * spec["rr"]
    if risk / atr > spec["max_risk_atr"]:
        return None

    exit_i = min(len(h1) - 1, entry_i + spec["max_hold"])
    exit_price = float(h1["close"].iloc[exit_i])
    reason = "TIME"
    for j in range(entry_i, min(len(h1), entry_i + spec["max_hold"] + 1)):
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
        "stop": stop,
        "target": target,
        "risk": risk,
        "risk_atr": risk / atr,
        "exit_i": exit_i,
        "exit_time": h1.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "r_after_cost": rp.direction_cost_r(direction, entry, exit_price, risk),
    }


def run_trades(h1: pd.DataFrame, source: pd.DataFrame, spec: dict) -> pd.DataFrame:
    filtered = apply_spec(source, spec)
    rows = []
    in_pos_until = -1
    seen: set[tuple[int, str, str]] = set()
    for row in filtered.itertuples(index=False):
        sig = row._asdict()
        if int(sig["signal_i"]) <= in_pos_until:
            continue
        key = (int(sig["signal_i"]), str(sig["family"]), str(sig["direction"]))
        if key in seen:
            continue
        trade = simulate_trade(h1, sig, spec)
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
    out["sample"] = np.where(out["entry_time"] >= rp.OOS_START, "OOS_2025_2026", "IS_2014_2024")
    out["year"] = out["entry_time"].dt.year
    return out


def score(row: dict) -> float:
    if row["trades"] < 25 or row["is_trades"] < 18 or row["oos_trades"] < 3:
        return -9999.0
    return (
        row["avg_r"] * 100.0
        + min(row["total_r"], 35.0) * 0.45
        + min(row["pf"], 3.5) * 5.0
        - row["max_dd_r"] * 0.80
        + min(row["worst_2y_r"], 0.0) * 2.2
        + min(row["oos_r"], 0.0) * 12.0
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 50) -> str:
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
    h1 = add_countertrend_features(rp.prepare_h1())
    source = build_source(h1)
    source.to_csv(OUT_DIR / "chfjpy_countertrend_source.csv", index=False)

    configs = [
        (
            "failed_sweep",
            {
                "family": ["failed_sweep"],
                "direction": ["long", "short", "both"],
                "lookback": [48, 72],
                "move_bars": [6],
                "move_atr": [1.2],
                "trigger_atr": [0.03],
                "wick_ratio": [0.55, 0.65],
                "close_location": [0.75],
                "bar_range_atr": [1.1],
                "body_max": [0.70],
                "range_width_max": [999.0],
                "bb_z": [1.8],
                "rsi_low": [30],
                "rsi_high": [70],
                "h4": ["neutral", "not_oppose", "any"],
                "hours": [None],
                "rr": [0.8, 1.0],
                "stop_buffer_atr": [0.15, 0.25],
                "max_risk_atr": [2.0],
                "max_hold": [8, 12],
            },
        ),
        (
            "stretch_reversal",
            {
                "family": ["stretch_reversal"],
                "direction": ["long", "short", "both"],
                "lookback": ["any"],
                "move_bars": [6],
                "move_atr": [1.2],
                "trigger_atr": [1.0],
                "wick_ratio": [0.45, 0.55],
                "close_location": [0.65],
                "bar_range_atr": [0.8],
                "body_max": [0.75],
                "range_width_max": [999.0],
                "bb_z": [1.8, 2.1],
                "rsi_low": [25, 30],
                "rsi_high": [70, 75],
                "h4": ["neutral", "not_oppose", "any"],
                "hours": [None],
                "rr": [0.8, 1.0],
                "stop_buffer_atr": [0.15, 0.25],
                "max_risk_atr": [2.0],
                "max_hold": [8, 12],
            },
        ),
        (
            "range_edge",
            {
                "family": ["range_edge"],
                "direction": ["long", "short", "both"],
                "lookback": [72, 96],
                "move_bars": [6],
                "move_atr": [0.8],
                "trigger_atr": [-0.10, 0.03],
                "wick_ratio": [0.45, 0.55],
                "close_location": [0.65],
                "bar_range_atr": [0.6],
                "body_max": [0.75],
                "range_width_max": [12.0, 999.0],
                "bb_z": [1.8],
                "rsi_low": [30],
                "rsi_high": [70],
                "h4": ["neutral", "not_oppose", "any"],
                "hours": [None],
                "rr": [0.8, 1.0],
                "stop_buffer_atr": [0.15, 0.25],
                "max_risk_atr": [2.0],
                "max_hold": [8, 12],
            },
        ),
    ]

    rows = []
    best_by_family: dict[str, tuple[dict, pd.DataFrame]] = {}
    total = sum(math.prod(len(v) for v in config.values()) for _, config in configs)
    done = 0
    for family, config in configs:
        for combo in itertools.product(*config.values()):
            spec = dict(zip(config.keys(), combo))
            trades = run_trades(h1, source, spec)
            summary = rp.summarize(trades)
            row = {**spec, **summary}
            row["score"] = score(row)
            rows.append(row)
            if row["score"] > -9999 and (
                family not in best_by_family or row["score"] > best_by_family[family][0]["score"]
            ):
                best_by_family[family] = (row, trades)
            done += 1
            if done % 5000 == 0:
                print(f"progress {done}/{total}", flush=True)

    grid = pd.DataFrame(rows).sort_values("score", ascending=False)
    grid.to_csv(OUT_DIR / "chfjpy_countertrend_grid.csv", index=False)
    valid = grid[grid["score"] > -9999].copy()
    valid.head(100).to_csv(OUT_DIR / "chfjpy_countertrend_top.csv", index=False)

    family_summary = valid.groupby("family", as_index=False).head(1).sort_values("score", ascending=False)
    family_summary.to_csv(OUT_DIR / "chfjpy_countertrend_family_summary.csv", index=False)

    chosen = {}
    for family, (row, trades) in best_by_family.items():
        chosen[family] = trades
        trades.to_csv(OUT_DIR / f"chfjpy_countertrend_{family}_best_trades.csv", index=False)

    cols = [
        "family",
        "direction",
        "lookback",
        "move_bars",
        "move_atr",
        "trigger_atr",
        "wick_ratio",
        "close_location",
        "bar_range_atr",
        "body_max",
        "range_width_max",
        "bb_z",
        "rsi_low",
        "rsi_high",
        "h4",
        "rr",
        "stop_buffer_atr",
        "max_risk_atr",
        "max_hold",
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
        "score",
    ]
    lines = [
        "# CHFJPY Countertrend Research",
        "",
        f"- source signals: `{len(source)}`",
        f"- data first: `{h1.index.min()}`",
        f"- data last: `{h1.index.max()}`",
        "",
        "## Family Summary",
        "",
        markdown_table(family_summary[cols], 20),
        "",
        "## Top Candidates",
        "",
        markdown_table(valid[cols], 80),
    ]
    for family, trades in chosen.items():
        lines += [
            "",
            f"## Best Trades: {family}",
            "",
            markdown_table(
                trades[
                    [
                        "entry_time",
                        "direction",
                        "entry",
                        "stop",
                        "target",
                        "exit_time",
                        "exit_reason",
                        "r_after_cost",
                        "risk_atr",
                        "rsi14",
                        "bb_z",
                        "wick_ratio",
                        "close_location",
                        "h4_context",
                    ]
                ],
                80,
            ),
        ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(family_summary[cols].to_string(index=False))
    print(valid[cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Original method v0.1: WaveBox Rebreak.

This is not a Synapse clone. It is a new method built from the Synapse
definition-grid findings:

- Avoid M5 noise as the main battlefield.
- Keep the wave-2 -> wave-3 idea.
- Replace fragile small H&S detection with pullback compression box breakout.
- Compare 1.5R and 2R exits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
DATA_ROOT = REPO_ROOT / "F87104_test"
OUT_DIR = THIS_DIR / "results_2026_05_25"
OUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")

ATR_PERIOD = 14
BREAK_BUFFER_ATR = 0.05
STOP_BUFFER_ATR = 0.20
SPREAD_PRICE = 0.010
SLIP_PRICE = 0.005

TIMEFRAME_CONFIGS = {
    "M15": {"rule": "15min", "pivot_width": 5, "min_swing_atr": 1.35, "max_hold": 120},
    "M30": {"rule": "30min", "pivot_width": 4, "min_swing_atr": 1.25, "max_hold": 96},
    "H1": {"rule": "1h", "pivot_width": 3, "min_swing_atr": 1.15, "max_hold": 72},
    "H4": {"rule": "4h", "pivot_width": 2, "min_swing_atr": 1.05, "max_hold": 48},
}

# First pass is intentionally narrow. Wider sweeps can be re-enabled after the
# candidate logic proves useful.
BOX_BARS_LIST = [8]
BOX_ATR_LIST = [1.6, 2.0]
TARGET_MODELS = ["fixed_1_5R", "fixed_2R"]

FILTER_SPECS = [
    {
        "filter": "base",
        "description": "50%-88.6%戻し + 圧縮ボックス再ブレイク。上位足は問わない。",
        "retrace_min": 0.50,
        "retrace_max": 0.886,
        "min_adjust_ratio": 0.30,
        "max_recovery": 0.92,
        "min_body": 0.25,
        "min_align": 0,
        "max_oppose": 99,
        "require_ema_flip": True,
        "max_chase_atr": 0.80,
        "min_planned_rr": 1.20,
    },
    {
        "filter": "context",
        "description": "base + 上位足1つ以上順行、明確な逆行なし。",
        "retrace_min": 0.50,
        "retrace_max": 0.886,
        "min_adjust_ratio": 0.50,
        "max_recovery": 0.85,
        "min_body": 0.35,
        "min_align": 1,
        "max_oppose": 0,
        "require_ema_flip": True,
        "max_chase_atr": 0.65,
        "min_planned_rr": 1.30,
    },
]


@dataclass(frozen=True)
class Pivot:
    pivot_i: int
    confirm_i: int
    kind: str
    price: float
    atr: float


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def timeframe_minutes(label: str) -> int:
    return {"M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}[label]


def discover_m5_files() -> list[Path]:
    return sorted(p for p in DATA_ROOT.rglob("USDJPY_M5_*.csv") if p.is_file())


def load_m5() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    coverage = []
    for path in discover_m5_files():
        frame = pd.read_csv(path)
        frame.columns = [c.strip().strip("<>").lower() for c in frame.columns]
        required = {"dtyyyymmdd", "time", "open", "high", "low", "close"}
        if not required.issubset(frame.columns):
            continue
        date_s = frame["dtyyyymmdd"].astype(str)
        time_s = frame["time"].astype(str).str.zfill(4)
        dt = pd.to_datetime(date_s + time_s, format="%Y%m%d%H%M", errors="coerce")
        frame = frame.assign(timestamp=dt).dropna(subset=["timestamp"])
        if "vol" in frame.columns:
            frame = frame.rename(columns={"vol": "volume"})
        if "volume" not in frame.columns:
            frame["volume"] = 0.0
        frame = frame[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["open", "high", "low", "close"])
        coverage.append(
            {
                "file": str(path.relative_to(REPO_ROOT)),
                "rows_raw": len(frame),
                "first": frame["timestamp"].min(),
                "last": frame["timestamp"].max(),
            }
        )
        rows.append(frame)

    if not rows:
        raise FileNotFoundError("No USDJPY_M5_*.csv files found under F87104_test")

    all_df = pd.concat(rows, ignore_index=True)
    before = len(all_df)
    all_df = all_df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    after = len(all_df)
    all_df = all_df.set_index("timestamp").sort_index()
    all_df = all_df.loc[(all_df.index >= START) & (all_df.index <= END)]
    coverage_df = pd.DataFrame(coverage)
    coverage_df.loc[len(coverage_df)] = {
        "file": "COMBINED_DEDUPED_RAW",
        "rows_raw": after,
        "first": all_df.index.min(),
        "last": all_df.index.max(),
    }
    coverage_df.loc[len(coverage_df)] = {
        "file": "DUPLICATE_TIMESTAMPS_REMOVED",
        "rows_raw": before - after,
        "first": pd.NaT,
        "last": pd.NaT,
    }
    return all_df, coverage_df


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    out = df.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    return out.dropna(subset=["open", "high", "low", "close"])


def add_indicators(df: pd.DataFrame, tf_label: str) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"], ATR_PERIOD)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_ratio"] = ((out["close"] - out["open"]).abs() / rng).fillna(0.0)
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema20_slope"] = out["ema20"] - out["ema20"].shift(3)
    out["ema100"] = out["close"].ewm(span=100, adjust=False).mean()
    slope_bars = max(3, round(24 * 60 / timeframe_minutes(tf_label)))
    out["ema100_slope"] = out["ema100"] - out["ema100"].shift(slope_bars)
    for bars in BOX_BARS_LIST:
        out[f"box_high_{bars}"] = out["high"].shift(1).rolling(bars).max()
        out[f"box_low_{bars}"] = out["low"].shift(1).rolling(bars).min()
        out[f"box_width_{bars}"] = out[f"box_high_{bars}"] - out[f"box_low_{bars}"]
    return out


def attach_upper_context(df: pd.DataFrame, uppers: dict[str, pd.DataFrame], tf_label: str) -> pd.DataFrame:
    labels = ["H1", "H4"] if tf_label in {"M15", "M30"} else ["H4"] if tf_label == "H1" else ["D1"]
    base_delta = pd.Timedelta(minutes=timeframe_minutes(tf_label))
    out = df.reset_index(names="timestamp").sort_values("timestamp")
    out["context_time"] = out["timestamp"] + base_delta
    for label in labels:
        upper = uppers.get(label)
        if upper is None or upper.empty:
            continue
        upper_delta = pd.Timedelta(minutes=timeframe_minutes(label))
        cols = upper[["close", "ema100", "ema100_slope"]].reset_index(names="timestamp")
        cols["context_time"] = cols["timestamp"] + upper_delta
        cols = cols.rename(
            columns={
                "close": f"{label}_close",
                "ema100": f"{label}_ema100",
                "ema100_slope": f"{label}_ema100_slope",
            }
        )
        cols = cols.drop(columns=["timestamp"]).sort_values("context_time")
        out = pd.merge_asof(out.sort_values("context_time"), cols, on="context_time", direction="backward")
    return out.drop(columns=["context_time"]).sort_values("timestamp").set_index("timestamp")


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def build_confirmed_pivots(df: pd.DataFrame, width: int, min_swing_atr: float) -> list[Pivot]:
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    atrs = df["atr"].to_numpy()
    raw: list[Pivot] = []
    for i in range(width, len(df) - width):
        if not math.isfinite(atrs[i]) or atrs[i] <= 0:
            continue
        hwin = highs[i - width : i + width + 1]
        lwin = lows[i - width : i + width + 1]
        is_high = highs[i] >= np.nanmax(hwin)
        is_low = lows[i] <= np.nanmin(lwin)
        if is_high and not is_low:
            raw.append(Pivot(i, i + width, "H", float(highs[i]), float(atrs[i])))
        elif is_low and not is_high:
            raw.append(Pivot(i, i + width, "L", float(lows[i]), float(atrs[i])))

    raw.sort(key=lambda p: (p.confirm_i, p.pivot_i))
    pivots: list[Pivot] = []
    for p in raw:
        if not pivots:
            pivots.append(p)
            continue
        last = pivots[-1]
        if p.kind == last.kind:
            if (p.kind == "H" and p.price > last.price) or (p.kind == "L" and p.price < last.price):
                pivots[-1] = p
            continue
        swing = abs(p.price - last.price)
        threshold = max(p.atr, last.atr) * min_swing_atr
        if swing >= threshold:
            pivots.append(p)
    return pivots


def pivots_until(pivots: list[Pivot], pointer: int, bar_i: int, active: list[Pivot]) -> int:
    while pointer < len(pivots) and pivots[pointer].confirm_i <= bar_i:
        active.append(pivots[pointer])
        if len(active) > 12:
            active.pop(0)
        pointer += 1
    return pointer


def upper_context(df: pd.DataFrame, i: int, direction: str) -> tuple[int, int, str]:
    align = 0
    oppose = 0
    notes = []
    for label in ["H1", "H4", "D1"]:
        close_col = f"{label}_close"
        ema_col = f"{label}_ema100"
        slope_col = f"{label}_ema100_slope"
        if close_col not in df.columns:
            continue
        c = float(df[close_col].iloc[i]) if pd.notna(df[close_col].iloc[i]) else math.nan
        e = float(df[ema_col].iloc[i]) if pd.notna(df[ema_col].iloc[i]) else math.nan
        s = float(df[slope_col].iloc[i]) if pd.notna(df[slope_col].iloc[i]) else math.nan
        if not (math.isfinite(c) and math.isfinite(e) and math.isfinite(s)):
            continue
        if direction == "long":
            ok = c >= e and s >= 0
            bad = c < e and s < 0
        else:
            ok = c <= e and s <= 0
            bad = c > e and s > 0
        if ok:
            align += 1
            notes.append(f"{label}順")
        elif bad:
            oppose += 1
            notes.append(f"{label}逆")
        else:
            notes.append(f"{label}中立")
    return align, oppose, ",".join(notes)


def signal_from_wavebox(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    tf_label: str,
    box_bars: int,
    box_atr: float,
    spec: dict,
) -> dict | None:
    if len(active) < 3:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    body = float(df["body_ratio"].iloc[i])
    ema20 = float(df["ema20"].iloc[i])
    ema20_slope = float(df["ema20_slope"].iloc[i])
    box_high = float(df[f"box_high_{box_bars}"].iloc[i])
    box_low = float(df[f"box_low_{box_bars}"].iloc[i])
    box_width = float(df[f"box_width_{box_bars}"].iloc[i])
    if not all(math.isfinite(x) for x in [box_high, box_low, box_width]):
        return None
    if box_width <= 0 or box_width > atr_i * box_atr:
        return None

    p0, p1, p2 = active[-3:]
    kinds = p0.kind + p1.kind + p2.kind
    max_setup_age = max(12, int(TIMEFRAME_CONFIGS[tf_label]["pivot_width"] * 12))
    setup_age = i - p2.confirm_i
    if setup_age < 0 or setup_age > max_setup_age:
        return None

    buffer = atr_i * BREAK_BUFFER_ATR
    direction = ""
    if kinds == "LHL":
        direction = "long"
        wave1 = p1.price - p0.price
        if wave1 <= atr_i * 1.60 or p2.price <= p0.price + buffer:
            return None
        retrace = (p1.price - p2.price) / wave1
        recovery = (close - p2.price) / max(p1.price - p2.price, atr_i * 0.01)
        breakout = close > box_high + buffer and prev_close <= box_high + buffer
        ema_ok = close > ema20 and ema20_slope > 0
        chase_atr = (close - box_high) / atr_i
        stop = min(p2.price, box_low) - atr_i * STOP_BUFFER_ATR
    elif kinds == "HLH":
        direction = "short"
        wave1 = p0.price - p1.price
        if wave1 <= atr_i * 1.60 or p2.price >= p0.price - buffer:
            return None
        retrace = (p2.price - p1.price) / wave1
        recovery = (p2.price - close) / max(p2.price - p1.price, atr_i * 0.01)
        breakout = close < box_low - buffer and prev_close >= box_low - buffer
        ema_ok = close < ema20 and ema20_slope < 0
        chase_atr = (box_low - close) / atr_i
        stop = max(p2.price, box_high) + atr_i * STOP_BUFFER_ATR
    else:
        return None

    if not breakout:
        return None
    if not (spec["retrace_min"] <= retrace <= spec["retrace_max"]):
        return None
    wave1_bars = max(p1.pivot_i - p0.pivot_i, 1)
    adjust_bars = max(p2.pivot_i - p1.pivot_i, 1)
    adjust_ratio = adjust_bars / wave1_bars
    if adjust_ratio < spec["min_adjust_ratio"] or recovery > spec["max_recovery"]:
        return None
    if body < spec["min_body"]:
        return None
    if spec["require_ema_flip"] and not ema_ok:
        return None
    if chase_atr < 0 or chase_atr > spec["max_chase_atr"]:
        return None

    align, oppose, upper_notes = upper_context(df, i, direction)
    if align < spec["min_align"] or oppose > spec["max_oppose"]:
        return None

    return {
        "symbol": "USDJPY",
        "timeframe": tf_label,
        "filter": spec["filter"],
        "filter_description": spec["description"],
        "box_bars": box_bars,
        "box_atr": box_atr,
        "signal_i": i,
        "signal_time": df.index[i],
        "direction": direction,
        "close": close,
        "p0": p0.price,
        "p1": p1.price,
        "p2": p2.price,
        "wave1_atr": wave1 / atr_i,
        "retrace": retrace,
        "recovery": recovery,
        "wave1_bars": wave1_bars,
        "adjust_bars": adjust_bars,
        "adjust_ratio": adjust_ratio,
        "setup_age": setup_age,
        "box_high": box_high,
        "box_low": box_low,
        "box_width_atr": box_width / atr_i,
        "chase_atr": chase_atr,
        "signal_body_ratio": body,
        "ema_ok": ema_ok,
        "upper_align": align,
        "upper_oppose": oppose,
        "upper_context": upper_notes,
        "stop": stop,
        "pivots": f"{p0.pivot_i}-{p1.pivot_i}-{p2.pivot_i}",
    }


def direction_cost_r(direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - SLIP_PRICE) - (entry + SPREAD_PRICE / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return clean / risk, after / risk


def simulate_trade(df: pd.DataFrame, sig: dict, target_model: str, max_hold_bars: int, min_planned_rr: float) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(df):
        return None
    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * (1.5 if target_model == "fixed_1_5R" else 2.0)
        reward = target - entry
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * (1.5 if target_model == "fixed_1_5R" else 2.0)
        reward = entry - target

    planned_rr = reward / risk
    if planned_rr < min_planned_rr:
        return None

    exit_i = min(len(df) - 1, entry_i + max_hold_bars)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "time_exit"
    for j in range(entry_i, min(len(df), entry_i + max_hold_bars + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
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

    r_clean, r_after_cost = direction_cost_r(direction, entry, exit_price, risk)
    return {
        "entry_i": entry_i,
        "entry_time": df.index[entry_i],
        "entry": entry,
        "target_model": target_model,
        "target": target,
        "planned_rr": planned_rr,
        "exit_i": exit_i,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after_cost,
    }


def run_timeframe(df: pd.DataFrame, tf_label: str, config: dict) -> pd.DataFrame:
    pivots = build_confirmed_pivots(df, config["pivot_width"], config["min_swing_atr"])
    rows = []
    for spec in FILTER_SPECS:
        for box_bars in BOX_BARS_LIST:
            for box_atr in BOX_ATR_LIST:
                active: list[Pivot] = []
                pointer = 0
                in_pos_until = {target_model: -1 for target_model in TARGET_MODELS}
                seen_setup: set[tuple] = set()
                for i in range(2, len(df) - 1):
                    pointer = pivots_until(pivots, pointer, i, active)
                    ts = df.index[i]
                    if ts < START or ts > END or holiday_market(ts):
                        continue
                    sig = signal_from_wavebox(df, i, active, tf_label, box_bars, box_atr, spec)
                    if sig is None:
                        continue
                    for target_model in TARGET_MODELS:
                        if i <= in_pos_until[target_model]:
                            continue
                        setup_key = (sig["direction"], sig["pivots"], box_bars, box_atr, spec["filter"], target_model)
                        if setup_key in seen_setup:
                            continue
                        trade = simulate_trade(df, sig, target_model, config["max_hold"], spec["min_planned_rr"])
                        if trade is None:
                            continue
                        rows.append({**sig, **trade})
                        seen_setup.add(setup_key)
                        in_pos_until[target_model] = int(trade["exit_i"])
    return pd.DataFrame(rows)


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


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def summarize(trades: pd.DataFrame, group_cols: list[str], r_col: str = "r_after_cost") -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = group[r_col]
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": int(len(group)),
                "win_rate": float((r > 0).mean() * 100),
                "total_r": float(r.sum()),
                "avg_r": float(r.mean()),
                "pf": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "avg_planned_rr": float(group["planned_rr"].mean()),
                "avg_hold_bars": float(group["bars_held"].mean()),
                "tp_rate": float((group["exit_reason"] == "TP").mean() * 100),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


def diagnostics(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    specs = [
        ("retrace", pd.cut(trades["retrace"], [0, 0.5, 0.618, 0.764, 0.886, 1.2], include_lowest=True)),
        ("box_width_atr", pd.cut(trades["box_width_atr"], [0, 0.8, 1.2, 1.6, 2.0, 99], include_lowest=True)),
        ("recovery", pd.cut(trades["recovery"], [0, 0.25, 0.5, 0.75, 0.92, 99], include_lowest=True)),
        ("adjust_ratio", pd.cut(trades["adjust_ratio"], [0, 0.3, 0.5, 0.8, 1.2, 99], include_lowest=True)),
        ("body_ratio", pd.cut(trades["signal_body_ratio"], [0, 0.25, 0.35, 0.45, 0.65, 1.0], include_lowest=True)),
        ("setup_age", pd.cut(trades["setup_age"], [0, 3, 6, 12, 24, 48, 999], include_lowest=True)),
    ]
    for feature, bins in specs:
        tmp = trades.copy()
        tmp["bin"] = bins.astype(str)
        for key, group in tmp.groupby("bin", dropna=False):
            r = group["r_after_cost"]
            rows.append(
                {
                    "feature": feature,
                    "bin": str(key),
                    "trades": int(len(group)),
                    "win_rate": float((r > 0).mean() * 100),
                    "total_r": float(r.sum()),
                    "avg_r": float(r.mean()),
                    "pf": profit_factor(r),
                }
            )
    return pd.DataFrame(rows)


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


def write_report(
    coverage: pd.DataFrame,
    overall: pd.DataFrame,
    by_tf_filter: pd.DataFrame,
    by_combo: pd.DataFrame,
    by_oos: pd.DataFrame,
    diag: pd.DataFrame,
) -> None:
    lines = [
        "# Original Method v0.1: WaveBox Rebreak 検証",
        "",
        "## 定義",
        "",
        "- 三尊/逆三尊は使わない",
        "- 中波の1波と2波をpivotで認識する",
        "- 2波戻しは50%-88.6%",
        "- 2波終端後の圧縮ボックスを3波方向へ抜けたら候補",
        "- M5は主戦場にしない。M15/M30/H1/H4を比較",
        "- TPは固定1.5R/2R",
        "- SLはP2またはbox外側 + 0.2ATR",
        "",
        "## データ品質",
        "",
        markdown_table(coverage, 40),
        "",
        "## 全体",
        "",
        markdown_table(overall, 20),
        "",
        "## 時間足 x フィルタ",
        "",
        markdown_table(by_tf_filter, 80),
        "",
        "## 詳細組み合わせ",
        "",
        markdown_table(by_combo, 120),
        "",
        "## OOS 2025-2026",
        "",
        markdown_table(by_oos, 120),
        "",
        "## 条件診断",
        "",
        markdown_table(diag.sort_values(["feature", "total_r"], ascending=[True, False]), 120),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_timeframe_filter.csv`",
        "- `summary_by_combo.csv`",
        "- `summary_oos.csv`",
        "- `diagnostics.csv`",
        "- `data_coverage.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m5, coverage = load_m5()
    datasets: dict[str, pd.DataFrame] = {}
    for label, config in TIMEFRAME_CONFIGS.items():
        datasets[label] = add_indicators(resample_ohlc(m5, config["rule"]), label)
    datasets["D1"] = add_indicators(resample_ohlc(m5, "1D"), "D1")
    for label in list(TIMEFRAME_CONFIGS):
        datasets[label] = attach_upper_context(datasets[label], datasets, label)

    tf_rows = []
    for label, frame in datasets.items():
        if label == "D1":
            continue
        tf_rows.append({"file": f"RESAMPLED_{label}", "rows_raw": len(frame), "first": frame.index.min(), "last": frame.index.max()})
    coverage = pd.concat([coverage, pd.DataFrame(tf_rows)], ignore_index=True)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    all_rows = []
    for label, config in TIMEFRAME_CONFIGS.items():
        rows = run_timeframe(datasets[label], label, config)
        if not rows.empty:
            all_rows.append(rows)

    if not all_rows:
        (OUT_DIR / "report_ja.md").write_text("# WaveBox Rebreak 検証\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades = pd.concat(all_rows, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col])
    trades["sample"] = np.where(trades["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    trades = trades.sort_values(["entry_time", "timeframe", "filter", "box_bars", "box_atr", "target_model"]).reset_index(drop=True)
    trades.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades, ["symbol"])
    by_tf_filter = summarize(trades, ["timeframe", "filter"])
    by_combo = summarize(trades, ["timeframe", "filter", "box_bars", "box_atr", "target_model"])
    by_oos = summarize(trades, ["sample", "timeframe", "filter", "target_model"])
    diag = diagnostics(trades)

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_tf_filter.to_csv(OUT_DIR / "summary_by_timeframe_filter.csv", index=False)
    by_combo.to_csv(OUT_DIR / "summary_by_combo.csv", index=False)
    by_oos.to_csv(OUT_DIR / "summary_oos.csv", index=False)
    diag.to_csv(OUT_DIR / "diagnostics.csv", index=False)
    write_report(coverage, overall, by_tf_filter, by_combo, by_oos, diag)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nOverall")
    print(overall.to_string(index=False))
    print("\nTimeframe x filter")
    print(by_tf_filter.to_string(index=False))
    print("\nTop combos")
    print(by_combo.head(30).to_string(index=False))
    print("\nOOS")
    print(by_oos.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Synapse definition grid backtest.

Purpose:
  Compare several mechanical interpretations of the Synapse definition before
  rewriting Pine entries:

  - 6-pivot classic wave continuation
  - 5-pivot inverse H&S / H&S turn
  - 5-pivot role-based A/B turn

The goal is not to prove a final profitable system. It is to see which
definition produces reasonable candidates, win rate, RR, PF, DD, and OOS
behavior when tested on USDJPY M5 data resampled into multiple timeframes.
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
    "M5": {"rule": "5min", "pivot_width": 8, "min_swing_atr": 1.60, "max_hold": 144},
    "M15": {"rule": "15min", "pivot_width": 5, "min_swing_atr": 1.45, "max_hold": 120},
    "M30": {"rule": "30min", "pivot_width": 4, "min_swing_atr": 1.30, "max_hold": 96},
    "H1": {"rule": "1h", "pivot_width": 3, "min_swing_atr": 1.20, "max_hold": 96},
    "H4": {"rule": "4h", "pivot_width": 2, "min_swing_atr": 1.10, "max_hold": 60},
}

STRUCTURES = ["classic_6pivot", "ihs_5pivot", "role_ab_5pivot"]
ENTRY_MODES = ["B_confirmed", "B_plus_diag", "A_plus_diag"]
TARGET_MODELS = ["half_wave", "fixed_1_5R", "fixed_2R"]

FILTER_SPECS = [
    {
        "filter": "observe_loose",
        "description": "候補量確認。浅い戻しも許容し、文脈フィルタなし。",
        "retrace_min": 0.382,
        "retrace_max": 1.05,
        "min_adjust_ratio": 0.00,
        "min_body": 0.00,
        "min_align": 0,
        "max_oppose": 99,
        "require_right_shoulder": False,
        "require_momentum": False,
        "require_diag_now": False,
        "max_chase_atr": 999.0,
        "min_abs_tl_slope_atr": 0.00,
        "max_abs_tl_slope_atr": 99.0,
        "min_planned_rr": 0.50,
    },
    {
        "filter": "basic_role",
        "description": "A/B役割とB抜けを優先。戻し50%以上、右肩維持。",
        "retrace_min": 0.50,
        "retrace_max": 0.95,
        "min_adjust_ratio": 0.00,
        "min_body": 0.00,
        "min_align": 0,
        "max_oppose": 99,
        "require_right_shoulder": True,
        "require_momentum": False,
        "require_diag_now": False,
        "max_chase_atr": 3.00,
        "min_abs_tl_slope_atr": 0.00,
        "max_abs_tl_slope_atr": 99.0,
        "min_planned_rr": 0.80,
    },
    {
        "filter": "diag_break",
        "description": "B抜けに加えて斜め抜け、実体、追いかけすぎ除外。",
        "retrace_min": 0.50,
        "retrace_max": 0.886,
        "min_adjust_ratio": 0.25,
        "min_body": 0.35,
        "min_align": 0,
        "max_oppose": 99,
        "require_right_shoulder": True,
        "require_momentum": False,
        "require_diag_now": True,
        "max_chase_atr": 2.00,
        "min_abs_tl_slope_atr": 0.03,
        "max_abs_tl_slope_atr": 1.50,
        "min_planned_rr": 1.00,
    },
    {
        "filter": "context",
        "description": "斜め+Bに上位足順行を追加。横軸も少し要求。",
        "retrace_min": 0.50,
        "retrace_max": 0.886,
        "min_adjust_ratio": 0.50,
        "min_body": 0.35,
        "min_align": 1,
        "max_oppose": 0,
        "require_right_shoulder": True,
        "require_momentum": False,
        "require_diag_now": True,
        "max_chase_atr": 1.80,
        "min_abs_tl_slope_atr": 0.03,
        "max_abs_tl_slope_atr": 1.20,
        "min_planned_rr": 1.00,
    },
    {
        "filter": "strict_synapse",
        "description": "61.8%-88.6%、横軸、上位足、実体、右側更新を要求。",
        "retrace_min": 0.618,
        "retrace_max": 0.886,
        "min_adjust_ratio": 1.00,
        "min_body": 0.45,
        "min_align": 1,
        "max_oppose": 0,
        "require_right_shoulder": True,
        "require_momentum": True,
        "require_diag_now": True,
        "max_chase_atr": 1.50,
        "min_abs_tl_slope_atr": 0.05,
        "max_abs_tl_slope_atr": 0.80,
        "min_planned_rr": 1.20,
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
    return {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}[label]


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
    out["ema100"] = out["close"].ewm(span=100, adjust=False).mean()
    slope_bars = max(3, round(24 * 60 / timeframe_minutes(tf_label)))
    out["ema100_slope"] = out["ema100"] - out["ema100"].shift(slope_bars)
    return out


def attach_upper_context(df: pd.DataFrame, uppers: dict[str, pd.DataFrame], tf_label: str) -> pd.DataFrame:
    labels = ["H1", "H4"] if tf_label in {"M5", "M15", "M30"} else ["H4"] if tf_label == "H1" else ["D1"]
    out = df.reset_index(names="timestamp").sort_values("timestamp")
    for label in labels:
        upper = uppers.get(label)
        if upper is None or upper.empty:
            continue
        cols = upper[["close", "ema100", "ema100_slope"]].reset_index(names="timestamp")
        cols = cols.rename(
            columns={
                "close": f"{label}_close",
                "ema100": f"{label}_ema100",
                "ema100_slope": f"{label}_ema100_slope",
            }
        )
        out = pd.merge_asof(out, cols.sort_values("timestamp"), on="timestamp", direction="backward")
    return out.set_index("timestamp")


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
        if len(active) > 20:
            active.pop(0)
        pointer += 1
    return pointer


def line_value(p0: Pivot, p1: Pivot, at_i: int) -> tuple[float, float]:
    bars = max(p1.pivot_i - p0.pivot_i, 1)
    slope = (p1.price - p0.price) / bars
    return p1.price + slope * (at_i - p1.pivot_i), slope


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


def _entry_trigger(direction: str, entry_mode: str, close: float, prev_close: float, a_level: float, b_level: float, tl_now: float, atr_i: float) -> tuple[bool, bool, bool, float]:
    buffer = atr_i * BREAK_BUFFER_ATR
    if direction == "long":
        b_cross = close > b_level + buffer and prev_close <= b_level + buffer
        a_break = close > a_level + buffer
        diag_now = close > tl_now + buffer
        diag_cross = diag_now and prev_close <= tl_now + atr_i * 0.20
        trigger_level = b_level if entry_mode.startswith("B") else max(a_level, tl_now)
    else:
        b_cross = close < b_level - buffer and prev_close >= b_level - buffer
        a_break = close < a_level - buffer
        diag_now = close < tl_now - buffer
        diag_cross = diag_now and prev_close >= tl_now - atr_i * 0.20
        trigger_level = b_level if entry_mode.startswith("B") else min(a_level, tl_now)

    if entry_mode == "B_confirmed":
        ok = b_cross
    elif entry_mode == "B_plus_diag":
        ok = b_cross and diag_now
    else:
        ok = diag_cross and a_break
    return ok, b_cross, diag_now, trigger_level


def _finalize_candidate(
    df: pd.DataFrame,
    i: int,
    structure: str,
    entry_mode: str,
    direction: str,
    pivots: list[Pivot],
    p0: Pivot,
    p1: Pivot,
    p2: Pivot,
    a_pivot: Pivot,
    b_pivot: Pivot,
    tl0: Pivot,
    tl1: Pivot,
    stop_pivot: Pivot,
    right_shoulder_ok: bool,
    momentum_ok: bool,
    pivot_note: str,
) -> dict | None:
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    tl_now, tl_slope = line_value(tl0, tl1, i)
    trigger_ok, b_cross, diag_now, trigger_level = _entry_trigger(
        direction, entry_mode, close, prev_close, a_pivot.price, b_pivot.price, tl_now, atr_i
    )
    if not trigger_ok:
        return None

    if direction == "long":
        wave1 = p1.price - p0.price
        retrace = (p1.price - p2.price) / wave1 if wave1 > 0 else math.nan
        stop = stop_pivot.price - atr_i * STOP_BUFFER_ATR
        target_half = p2.price + wave1 * 0.50
        stop_valid = close > stop
        half_ahead = target_half > close
        chase_atr = (close - trigger_level) / atr_i
        mid_recovery = (close - p2.price) / max(p1.price - p2.price, atr_i * 0.01)
        ema_ok = float(df["ema100_slope"].iloc[i]) > 0
    else:
        wave1 = p0.price - p1.price
        retrace = (p2.price - p1.price) / wave1 if wave1 > 0 else math.nan
        stop = stop_pivot.price + atr_i * STOP_BUFFER_ATR
        target_half = p2.price - wave1 * 0.50
        stop_valid = close < stop
        half_ahead = target_half < close
        chase_atr = (trigger_level - close) / atr_i
        mid_recovery = (p2.price - close) / max(p2.price - p1.price, atr_i * 0.01)
        ema_ok = float(df["ema100_slope"].iloc[i]) < 0

    if wave1 <= atr_i * 1.20 or not stop_valid:
        return None

    align, oppose, upper_notes = upper_context(df, i, direction)
    wave1_bars = max(p1.pivot_i - p0.pivot_i, 1)
    adjust_bars = max(p2.pivot_i - p1.pivot_i, 1)
    body = float(df["body_ratio"].iloc[i])

    return {
        "structure": structure,
        "entry_mode": entry_mode,
        "direction": direction,
        "signal_i": i,
        "signal_time": df.index[i],
        "close": close,
        "a_level": a_pivot.price,
        "b_level": b_pivot.price,
        "trendline": tl_now,
        "trendline_slope_atr": tl_slope / atr_i,
        "trigger_level": trigger_level,
        "b_cross": b_cross,
        "diag_now": diag_now,
        "retrace": retrace,
        "wave1_atr": wave1 / atr_i,
        "wave1_bars": wave1_bars,
        "adjust_bars": adjust_bars,
        "adjust_ratio": adjust_bars / wave1_bars,
        "right_shoulder_ok": right_shoulder_ok,
        "momentum_ok": momentum_ok,
        "ema_ok": ema_ok,
        "upper_align": align,
        "upper_oppose": oppose,
        "upper_context": upper_notes,
        "signal_body_ratio": body,
        "chase_atr": chase_atr,
        "mid_recovery": mid_recovery,
        "stop": stop,
        "target_half": target_half,
        "half_target_ahead": half_ahead,
        "pivots": pivot_note,
        "pivot_count": len(pivots),
    }


def candidate_from_active(df: pd.DataFrame, i: int, active: list[Pivot], structure: str, entry_mode: str) -> dict | None:
    if structure == "classic_6pivot":
        if len(active) < 6:
            return None
        p = active[-6:]
        kinds = "".join(x.kind for x in p)
        if kinds == "LHLHLH":
            l0, h1, l2, h3, l4, h5 = p
            right_ok = l4.price >= l2.price - float(df["atr"].iloc[i]) * 0.75
            momentum_ok = h5.price > h3.price
            return _finalize_candidate(df, i, structure, entry_mode, "long", p, l0, h1, l4, h3, h5, h1, h3, l4, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        if kinds == "HLHLHL":
            h0, l1, h2, l3, h4, l5 = p
            right_ok = h4.price <= h2.price + float(df["atr"].iloc[i]) * 0.75
            momentum_ok = l5.price < l3.price
            return _finalize_candidate(df, i, structure, entry_mode, "short", p, h0, l1, h4, l3, l5, l1, l3, h4, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        return None

    if structure == "ihs_5pivot":
        if len(active) < 5:
            return None
        p = active[-5:]
        kinds = "".join(x.kind for x in p)
        if kinds == "LHLHL":
            l0, h1, l2, h3, l4 = p
            right_ok = l4.price >= l2.price - float(df["atr"].iloc[i]) * 0.75
            momentum_ok = h3.price >= h1.price - float(df["atr"].iloc[i]) * 0.25
            stop_p = l2 if l2.price <= l4.price else l4
            return _finalize_candidate(df, i, structure, entry_mode, "long", p, l0, h1, l4, h1, h3, h1, h3, stop_p, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        if kinds == "HLHLH":
            h0, l1, h2, l3, h4 = p
            right_ok = h4.price <= h2.price + float(df["atr"].iloc[i]) * 0.75
            momentum_ok = l3.price <= l1.price + float(df["atr"].iloc[i]) * 0.25
            stop_p = h2 if h2.price >= h4.price else h4
            return _finalize_candidate(df, i, structure, entry_mode, "short", p, h0, l1, h4, l1, l3, l1, l3, stop_p, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        return None

    if structure == "role_ab_5pivot":
        if len(active) < 5:
            return None
        p = active[-5:]
        kinds = "".join(x.kind for x in p)
        if kinds == "HLHLH":
            h0, l1, h2, l3, h4 = p
            right_ok = l3.price > l1.price - float(df["atr"].iloc[i]) * 0.50
            momentum_ok = h4.price > h2.price
            return _finalize_candidate(df, i, structure, entry_mode, "long", p, l1, h2, l3, h2, h4, h0, h2, l3, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        if kinds == "LHLHL":
            l0, h1, l2, h3, l4 = p
            right_ok = h3.price < h1.price + float(df["atr"].iloc[i]) * 0.50
            momentum_ok = l4.price < l2.price
            return _finalize_candidate(df, i, structure, entry_mode, "short", p, h1, l2, h3, l2, l4, l0, l2, h3, right_ok, momentum_ok, "-".join(str(x.pivot_i) for x in p))
        return None

    raise ValueError(f"Unknown structure: {structure}")


def collect_candidates(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    pivots = build_confirmed_pivots(df, config["pivot_width"], config["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows = []
    seen: set[tuple] = set()
    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < START or ts > END or holiday_market(ts):
            continue
        for structure in STRUCTURES:
            for entry_mode in ENTRY_MODES:
                cand = candidate_from_active(df, i, active, structure, entry_mode)
                if cand is None:
                    continue
                key = (structure, entry_mode, cand["direction"], cand["signal_i"], cand["pivots"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(cand)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("signal_i").reset_index(drop=True)


def direction_cost_r(direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - SLIP_PRICE) - (entry + SPREAD_PRICE / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return clean / risk, after / risk


def passes_filter(cand: pd.Series, spec: dict) -> bool:
    abs_slope = abs(float(cand["trendline_slope_atr"]))
    if not (spec["retrace_min"] <= float(cand["retrace"]) <= spec["retrace_max"]):
        return False
    if float(cand["adjust_ratio"]) < spec["min_adjust_ratio"]:
        return False
    if float(cand["signal_body_ratio"]) < spec["min_body"]:
        return False
    if int(cand["upper_align"]) < spec["min_align"]:
        return False
    if int(cand["upper_oppose"]) > spec["max_oppose"]:
        return False
    if spec["require_right_shoulder"] and not bool(cand["right_shoulder_ok"]):
        return False
    if spec["require_momentum"] and not bool(cand["momentum_ok"]):
        return False
    if spec["require_diag_now"] and not bool(cand["diag_now"]):
        return False
    if float(cand["chase_atr"]) < 0 or float(cand["chase_atr"]) > spec["max_chase_atr"]:
        return False
    if abs_slope < spec["min_abs_tl_slope_atr"] or abs_slope > spec["max_abs_tl_slope_atr"]:
        return False
    return True


def simulate_trade(df: pd.DataFrame, cand: pd.Series, target_model: str, max_hold_bars: int, min_planned_rr: float) -> dict | None:
    signal_i = int(cand["signal_i"])
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None

    direction = str(cand["direction"])
    entry = float(df["open"].iloc[entry_i])
    stop = float(cand["stop"])

    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        if target_model == "half_wave":
            target = float(cand["target_half"])
        elif target_model == "fixed_1_5R":
            target = entry + risk * 1.5
        else:
            target = entry + risk * 2.0
        reward = target - entry
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        if target_model == "half_wave":
            target = float(cand["target_half"])
        elif target_model == "fixed_1_5R":
            target = entry - risk * 1.5
        else:
            target = entry - risk * 2.0
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
        "stop": stop,
        "target": target,
        "target_model": target_model,
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


def run_timeframe(df: pd.DataFrame, tf_label: str, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = collect_candidates(df, config)
    if candidates.empty:
        return candidates, pd.DataFrame()

    all_trades = []
    for spec in FILTER_SPECS:
        spec_candidates = candidates[candidates.apply(lambda row: passes_filter(row, spec), axis=1)]
        if spec_candidates.empty:
            continue
        for target_model in TARGET_MODELS:
            in_pos_until = -1
            for _, cand in spec_candidates.iterrows():
                signal_i = int(cand["signal_i"])
                if signal_i <= in_pos_until:
                    continue
                trade = simulate_trade(df, cand, target_model, config["max_hold"], spec["min_planned_rr"])
                if trade is None:
                    continue
                all_trades.append(
                    {
                        "symbol": "USDJPY",
                        "timeframe": tf_label,
                        "filter": spec["filter"],
                        "filter_description": spec["description"],
                        **cand.drop(labels=["signal_i"]).to_dict(),
                        **trade,
                    }
                )
                in_pos_until = int(trade["exit_i"])

    trades = pd.DataFrame(all_trades)
    return candidates, trades


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
                "median_planned_rr": float(group["planned_rr"].median()),
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
        ("retrace", pd.cut(trades["retrace"], [0, 0.382, 0.50, 0.618, 0.764, 0.886, 1.05, 2], include_lowest=True)),
        ("planned_rr", pd.cut(trades["planned_rr"], [0, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 99], include_lowest=True)),
        ("adjust_ratio", pd.cut(trades["adjust_ratio"], [0, 0.25, 0.5, 1.0, 2.0, 99], include_lowest=True)),
        ("chase_atr", pd.cut(trades["chase_atr"], [-99, 0, 0.5, 1.0, 1.5, 2.0, 3.0, 999], include_lowest=True)),
        ("mid_recovery", pd.cut(trades["mid_recovery"], [-99, 0.25, 0.5, 0.75, 1.0, 1.5, 999], include_lowest=True)),
        (
            "trendline_slope_atr_abs",
            pd.cut(trades["trendline_slope_atr"].abs(), [0, 0.03, 0.05, 0.12, 0.25, 0.50, 1.0, 99], include_lowest=True),
        ),
        ("body_ratio", pd.cut(trades["signal_body_ratio"], [0, 0.25, 0.35, 0.45, 0.65, 1.0], include_lowest=True)),
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


def candidate_summary(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()
    rows = []
    for key, group in candidates.groupby(["timeframe", "structure", "entry_mode"], dropna=False):
        rows.append(
            {
                "timeframe": key[0],
                "structure": key[1],
                "entry_mode": key[2],
                "raw_candidates": len(group),
                "avg_retrace": float(group["retrace"].mean()),
                "avg_chase_atr": float(group["chase_atr"].mean()),
                "diag_now_rate": float(group["diag_now"].mean() * 100),
                "upper_align_avg": float(group["upper_align"].mean()),
                "upper_oppose_avg": float(group["upper_oppose"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("raw_candidates", ascending=False)


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
    cand_sum: pd.DataFrame,
    overall: pd.DataFrame,
    by_filter_target: pd.DataFrame,
    by_tf_filter: pd.DataFrame,
    by_structure: pd.DataFrame,
    by_entry: pd.DataFrame,
    by_oos: pd.DataFrame,
    diag: pd.DataFrame,
) -> None:
    lines = [
        "# Synapse 定義グリッド検証 v0.1",
        "",
        "## 目的",
        "",
        "Synapse手法の再定義に合わせ、Pine実装前に複数のA/B解釈とフィルタ強度を比較する。",
        "今回は勝率だけでなく、予定RR、平均R、PF、最大DD、OOS 2025-2026を同時に見る。",
        "",
        "## 比較した構造",
        "",
        "- `classic_6pivot`: 既存検証に近い6pivot型。ロングは `L-H-L-H-L-H`、A=中間戻り高値、B=右端確認高値。",
        "- `ihs_5pivot`: 小波の逆三尊/三尊を優先する5pivot型。ロングは `L-H-L-H-L`、A=ヘッド前高値、B=ヘッド後高値。",
        "- `role_ab_5pivot`: A/B役割線を優先する5pivot型。ロングは `H-L-H-L-H`、A=最後の売り波起点、B=ヘッド後確認高値。",
        "",
        "## 比較した出口",
        "",
        "- `half_wave`: 中波1波値幅の半値目標",
        "- `fixed_1_5R`: 固定1.5R",
        "- `fixed_2R`: 固定2R",
        "",
        "## データ品質",
        "",
        markdown_table(coverage, 40),
        "",
        "## Raw候補数",
        "",
        markdown_table(cand_sum, 80),
        "",
        "## 全体",
        "",
        markdown_table(overall, 30),
        "",
        "## フィルタ x TP",
        "",
        markdown_table(by_filter_target, 80),
        "",
        "## 時間足 x フィルタ",
        "",
        markdown_table(by_tf_filter, 100),
        "",
        "## A/B構造別",
        "",
        markdown_table(by_structure, 80),
        "",
        "## エントリー方式別",
        "",
        markdown_table(by_entry, 80),
        "",
        "## OOS 2025-2026",
        "",
        markdown_table(by_oos, 120),
        "",
        "## 条件診断",
        "",
        markdown_table(diag.sort_values(["feature", "total_r"], ascending=[True, False]), 140),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `raw_candidates.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_filter_target.csv`",
        "- `summary_by_timeframe_filter.csv`",
        "- `summary_by_structure.csv`",
        "- `summary_by_entry.csv`",
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

    all_candidates = []
    all_trades = []
    for label, config in TIMEFRAME_CONFIGS.items():
        candidates, trades = run_timeframe(datasets[label], label, config)
        if not candidates.empty:
            candidates.insert(0, "timeframe", label)
            all_candidates.append(candidates)
        if not trades.empty:
            all_trades.append(trades)

    if all_candidates:
        candidates_df = pd.concat(all_candidates, ignore_index=True)
    else:
        candidates_df = pd.DataFrame()
    candidates_df.to_csv(OUT_DIR / "raw_candidates.csv", index=False)

    if not all_trades:
        (OUT_DIR / "report_ja.md").write_text("# Synapse 定義グリッド検証 v0.1\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades = pd.concat(all_trades, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col])
    trades["sample"] = np.where(trades["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    trades = trades.sort_values(["entry_time", "timeframe", "filter", "structure", "target_model"]).reset_index(drop=True)
    trades.to_csv(OUT_DIR / "trades.csv", index=False)

    cand_sum = candidate_summary(candidates_df)
    overall = summarize(trades, ["symbol"])
    by_filter_target = summarize(trades, ["filter", "target_model"])
    by_tf_filter = summarize(trades, ["timeframe", "filter"])
    by_structure = summarize(trades, ["structure", "filter", "target_model"])
    by_entry = summarize(trades, ["entry_mode", "filter", "target_model"])
    by_oos = summarize(trades, ["sample", "timeframe", "filter", "target_model"])
    diag = diagnostics(trades)

    cand_sum.to_csv(OUT_DIR / "summary_raw_candidates.csv", index=False)
    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_filter_target.to_csv(OUT_DIR / "summary_by_filter_target.csv", index=False)
    by_tf_filter.to_csv(OUT_DIR / "summary_by_timeframe_filter.csv", index=False)
    by_structure.to_csv(OUT_DIR / "summary_by_structure.csv", index=False)
    by_entry.to_csv(OUT_DIR / "summary_by_entry.csv", index=False)
    by_oos.to_csv(OUT_DIR / "summary_oos.csv", index=False)
    diag.to_csv(OUT_DIR / "diagnostics.csv", index=False)

    write_report(coverage, cand_sum, overall, by_filter_target, by_tf_filter, by_structure, by_entry, by_oos, diag)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nOverall")
    print(overall.to_string(index=False))
    print("\nFilter x target")
    print(by_filter_target.head(30).to_string(index=False))
    print("\nOOS")
    print(by_oos.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

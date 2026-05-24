#!/usr/bin/env python3
"""
Mechanical Elliott/Fibonacci study for the local FX data.

This script deliberately turns discretionary ideas into reproducible rules:
- V-shape Fibonacci recovery: enter when price recovers a chosen Fibonacci
  ratio of a sharp swing.
- Elliott wave-5 proxy: use confirmed alternating pivots and enter on the
  wave-3 extreme breakout after a valid wave-4 retracement.

The goal is research and scanner design, not a guarantee of live performance.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "results_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))

from sai_backtest import INSTRUMENTS, atr, load_instrument  # noqa: E402


SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
TIMEFRAMES = ["H1", "H4", "D1"]
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2024-12-31 23:59:59")
ATR_PERIOD = 14

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}


@dataclass(frozen=True)
class Pivot:
    pivot_i: int
    confirm_i: int
    kind: str
    price: float
    atr: float


@dataclass(frozen=True)
class StrategySpec:
    name: str
    family: str
    fib: float = 0.786
    rr: float = 2.0
    extension: float | None = None
    strict: bool = False
    body_min: float = 0.0
    early_exit_bars: int = 0
    direction_filter: str = "both"
    min_v_move_atr: float | None = None
    min_v_move_bars: int | None = None
    max_v_move_bars: int | None = None
    max_recovery_bars: int | None = None
    max_recovery_to_drop: float | None = None
    min_drop_speed: float | None = None
    min_recovery_speed: float | None = None
    min_recovery_vs_drop_speed: float | None = None


SPECS: list[StrategySpec] = [
    StrategySpec("VFIB_618_RR2", "V字フィボ", fib=0.618, rr=2.0),
    StrategySpec("VFIB_618_BODY50_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.50),
    StrategySpec("VFIB_618_BODY60_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60),
    StrategySpec("VFIB_618_EARLY1_RR2", "V字フィボ", fib=0.618, rr=2.0, early_exit_bars=1),
    StrategySpec("VFIB_618_EARLY3_RR2", "V字フィボ", fib=0.618, rr=2.0, early_exit_bars=3),
    StrategySpec("VFIB_618_BODY50_EARLY1_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.50, early_exit_bars=1),
    StrategySpec("VFIB_618_BODY60_LONG_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60, direction_filter="long"),
    StrategySpec("VFIB_618_BODY60_LONG_REC1_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60, direction_filter="long", max_recovery_to_drop=1.0),
    StrategySpec("VFIB_618_BODY60_LONG_SPEED030_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60, direction_filter="long", min_drop_speed=0.30),
    StrategySpec("VFIB_618_BODY60_LONG_REC1_SPEED030_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60, direction_filter="long", max_recovery_to_drop=1.0, min_drop_speed=0.30),
    StrategySpec("VFIB_618_BODY60_LONG_ATR4_SPEED060_RR2", "V字フィボ", fib=0.618, rr=2.0, body_min=0.60, direction_filter="long", min_v_move_atr=4.0, min_drop_speed=0.60),
    StrategySpec("VFIB_786_RR2", "V字フィボ", fib=0.786, rr=2.0),
    StrategySpec("VFIB_786_EARLY1_RR2", "V字フィボ", fib=0.786, rr=2.0, early_exit_bars=1),
    StrategySpec("VFIB_100_RR2", "V字フィボ", fib=1.000, rr=2.0),
    StrategySpec(
        "VFIB_100_BODY60_LONG_STRICTV_RR2",
        "V字フィボ",
        fib=1.000,
        rr=2.0,
        body_min=0.60,
        direction_filter="long",
        min_v_move_atr=3.5,
        min_v_move_bars=2,
        max_v_move_bars=18,
        max_recovery_bars=18,
        max_recovery_to_drop=1.0,
        min_drop_speed=0.35,
        min_recovery_speed=0.25,
        min_recovery_vs_drop_speed=1.0,
    ),
    StrategySpec("VFIB_786_RR3", "V字フィボ", fib=0.786, rr=3.0),
    StrategySpec("VFIB_786_EXT127", "V字フィボ", fib=0.786, extension=1.272),
    StrategySpec("VFIB_100_EXT161", "V字フィボ", fib=1.000, extension=1.618),
    StrategySpec("VFIB_786_BODY60_RR2", "V字フィボ", fib=0.786, rr=2.0, body_min=0.60),
    StrategySpec("ELLIOTT_W5_RR2_LOOSE", "エリオット風5波目", rr=2.0, strict=False),
    StrategySpec("ELLIOTT_W5_RR3_LOOSE", "エリオット風5波目", rr=3.0, strict=False),
    StrategySpec("ELLIOTT_W5_RR2_STRICT", "エリオット風5波目", rr=2.0, strict=True),
    StrategySpec("ELLIOTT_W5_RR3_STRICT", "エリオット風5波目", rr=3.0, strict=True),
]


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "H1":
        return df.copy()
    rule = {"H4": "4h", "D1": "1D"}[timeframe]
    return (
        df.resample(rule, label="left", closed="left")
        .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .dropna()
    )


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"], ATR_PERIOD)
    body = (out["close"] - out["open"]).abs()
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_ratio"] = (body / rng).fillna(0.0)
    return out


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def timeframe_settings(timeframe: str) -> dict:
    if timeframe == "D1":
        return dict(pivot_width=2, min_swing_atr=1.5, max_hold_bars=60, v_lookback=60, min_v_atr=3.0, break_buffer_atr=0.05)
    if timeframe == "H4":
        return dict(pivot_width=3, min_swing_atr=2.0, max_hold_bars=180, v_lookback=90, min_v_atr=3.5, break_buffer_atr=0.06)
    return dict(pivot_width=4, min_swing_atr=2.5, max_hold_bars=24 * 60, v_lookback=120, min_v_atr=4.0, break_buffer_atr=0.08)


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
        pointer += 1
    return pointer


def direction_cost_r(symbol: str, direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    costs = COST_TABLE[symbol]
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - costs["slip_price"]) - (entry + costs["spread_price"] / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - costs["spread_price"] / 2.0) - (exit_price + costs["slip_price"])
    return clean / risk, after / risk


def simulate_trade(
    df: pd.DataFrame,
    symbol: str,
    direction: str,
    signal_i: int,
    stop: float,
    target: float,
    max_hold_bars: int,
    invalidation_level: float | None = None,
    early_exit_bars: int = 0,
) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
    else:
        risk = stop - entry
        if risk <= 0:
            return None

    exit_i = min(len(df) - 1, entry_i + max_hold_bars)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "max_hold"
    for j in range(entry_i, min(len(df), entry_i + max_hold_bars + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        close = float(df["close"].iloc[j])
        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = hi >= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break
            if early_exit_bars > 0 and invalidation_level is not None and (j - entry_i + 1) <= early_exit_bars and close < invalidation_level:
                exit_i = min(j + 1, len(df) - 1)
                exit_price = float(df["open"].iloc[exit_i])
                reason = "early_back_inside"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break
            if early_exit_bars > 0 and invalidation_level is not None and (j - entry_i + 1) <= early_exit_bars and close > invalidation_level:
                exit_i = min(j + 1, len(df) - 1)
                exit_price = float(df["open"].iloc[exit_i])
                reason = "early_back_inside"
                break
    r_clean, r_after = direction_cost_r(symbol, direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after,
    }


def v_fib_signal(df: pd.DataFrame, i: int, active: list[Pivot], spec: StrategySpec, settings: dict) -> dict | None:
    if len(active) < 2:
        return None
    p0, p1 = active[-2], active[-1]
    if i - p1.pivot_i > settings["v_lookback"]:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None
    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    buffer = atr_i * settings["break_buffer_atr"]

    if p0.kind == "H" and p1.kind == "L":
        if spec.direction_filter == "short":
            return None
        drop = p0.price - p1.price
        min_v_atr = spec.min_v_move_atr if spec.min_v_move_atr is not None else settings["min_v_atr"]
        if drop < atr_i * min_v_atr:
            return None
        ratio = (close - p1.price) / drop
        prev_ratio = (prev_close - p1.price) / drop
        if prev_ratio < spec.fib <= ratio and close > p1.price + drop * spec.fib + buffer:
            stop = p1.price - atr_i * 0.25
            if spec.extension is None:
                target = close + (close - stop) * spec.rr
            else:
                target = p1.price + drop * spec.extension
            if target <= close:
                return None
            drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
            recovery_bars = max(i - p1.pivot_i, 1)
            recovery = close - p1.price
            recovery_to_drop = recovery_bars / drop_bars
            drop_speed = drop / drop_bars / atr_i
            recovery_speed = recovery / recovery_bars / atr_i
            if spec.min_v_move_bars is not None and drop_bars < spec.min_v_move_bars:
                return None
            if spec.max_v_move_bars is not None and drop_bars > spec.max_v_move_bars:
                return None
            if spec.max_recovery_bars is not None and recovery_bars > spec.max_recovery_bars:
                return None
            if spec.max_recovery_to_drop is not None and recovery_to_drop > spec.max_recovery_to_drop:
                return None
            if spec.min_drop_speed is not None and drop_speed < spec.min_drop_speed:
                return None
            if spec.min_recovery_speed is not None and recovery_speed < spec.min_recovery_speed:
                return None
            if spec.min_recovery_vs_drop_speed is not None and recovery_speed < drop_speed * spec.min_recovery_vs_drop_speed:
                return None
            return {
                "direction": "long",
                "v_start_i": p0.pivot_i,
                "v_extreme_i": p1.pivot_i,
                "v_start": p0.price,
                "v_extreme": p1.price,
                "v_move_atr": drop / atr_i,
                "v_move_bars": drop_bars,
                "v_recovery_bars": recovery_bars,
                "v_recovery_to_drop_bars": recovery_to_drop,
                "v_drop_speed_atr_per_bar": drop_speed,
                "v_recovery_speed_atr_per_bar": recovery_speed,
                "fib_ratio": ratio,
                "trigger_level": p1.price + drop * spec.fib,
                "stop": stop,
                "target": target,
            }

    if p0.kind == "L" and p1.kind == "H":
        if spec.direction_filter == "long":
            return None
        rally = p1.price - p0.price
        min_v_atr = spec.min_v_move_atr if spec.min_v_move_atr is not None else settings["min_v_atr"]
        if rally < atr_i * min_v_atr:
            return None
        ratio = (p1.price - close) / rally
        prev_ratio = (p1.price - prev_close) / rally
        if prev_ratio < spec.fib <= ratio and close < p1.price - rally * spec.fib - buffer:
            stop = p1.price + atr_i * 0.25
            if spec.extension is None:
                target = close - (stop - close) * spec.rr
            else:
                target = p1.price - rally * spec.extension
            if target >= close:
                return None
            rally_bars = max(p1.pivot_i - p0.pivot_i, 1)
            recovery_bars = max(i - p1.pivot_i, 1)
            recovery = p1.price - close
            recovery_to_rally = recovery_bars / rally_bars
            rally_speed = rally / rally_bars / atr_i
            recovery_speed = recovery / recovery_bars / atr_i
            if spec.min_v_move_bars is not None and rally_bars < spec.min_v_move_bars:
                return None
            if spec.max_v_move_bars is not None and rally_bars > spec.max_v_move_bars:
                return None
            if spec.max_recovery_bars is not None and recovery_bars > spec.max_recovery_bars:
                return None
            if spec.max_recovery_to_drop is not None and recovery_to_rally > spec.max_recovery_to_drop:
                return None
            if spec.min_drop_speed is not None and rally_speed < spec.min_drop_speed:
                return None
            if spec.min_recovery_speed is not None and recovery_speed < spec.min_recovery_speed:
                return None
            if spec.min_recovery_vs_drop_speed is not None and recovery_speed < rally_speed * spec.min_recovery_vs_drop_speed:
                return None
            return {
                "direction": "short",
                "v_start_i": p0.pivot_i,
                "v_extreme_i": p1.pivot_i,
                "v_start": p0.price,
                "v_extreme": p1.price,
                "v_move_atr": rally / atr_i,
                "v_move_bars": rally_bars,
                "v_recovery_bars": recovery_bars,
                "v_recovery_to_drop_bars": recovery_to_rally,
                "v_drop_speed_atr_per_bar": rally_speed,
                "v_recovery_speed_atr_per_bar": recovery_speed,
                "fib_ratio": ratio,
                "trigger_level": p1.price - rally * spec.fib,
                "stop": stop,
                "target": target,
            }
    return None


def elliott_signal(df: pd.DataFrame, i: int, active: list[Pivot], spec: StrategySpec, settings: dict) -> dict | None:
    if len(active) < 5:
        return None
    p = active[-5:]
    kinds = "".join(x.kind for x in p)
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    buffer = atr_i * settings["break_buffer_atr"]

    if kinds == "LHLHL":
        l0, h1, l2, h3, l4 = p
        wave1 = h1.price - l0.price
        wave3 = h3.price - l2.price
        if wave1 <= 0 or wave3 <= 0:
            return None
        wave2_retrace = (h1.price - l2.price) / wave1
        wave4_retrace = (h3.price - l4.price) / wave3
        structure_ok = h3.price > h1.price and l2.price > l0.price and l4.price > l2.price
        retrace_ok = 0.236 <= wave2_retrace <= 0.786 and 0.236 <= wave4_retrace <= 0.618
        strength_ok = wave3 >= wave1 * (1.0 if spec.strict else 0.8)
        strict_ok = not spec.strict or wave4_retrace <= 0.50
        if structure_ok and retrace_ok and strength_ok and strict_ok and prev_close <= h3.price and close > h3.price + buffer:
            stop = l4.price - atr_i * 0.25
            target = close + (close - stop) * spec.rr
            return {
                "direction": "long",
                "wave1": wave1,
                "wave3": wave3,
                "wave2_retrace": wave2_retrace,
                "wave4_retrace": wave4_retrace,
                "trigger_level": h3.price,
                "stop": stop,
                "target": target,
            }

    if kinds == "HLHLH":
        h0, l1, h2, l3, h4 = p
        wave1 = h0.price - l1.price
        wave3 = h2.price - l3.price
        if wave1 <= 0 or wave3 <= 0:
            return None
        wave2_retrace = (h2.price - l1.price) / wave1
        wave4_retrace = (h4.price - l3.price) / wave3
        structure_ok = l3.price < l1.price and h2.price < h0.price and h4.price < h2.price
        retrace_ok = 0.236 <= wave2_retrace <= 0.786 and 0.236 <= wave4_retrace <= 0.618
        strength_ok = wave3 >= wave1 * (1.0 if spec.strict else 0.8)
        strict_ok = not spec.strict or wave4_retrace <= 0.50
        if structure_ok and retrace_ok and strength_ok and strict_ok and prev_close >= l3.price and close < l3.price - buffer:
            stop = h4.price + atr_i * 0.25
            target = close - (stop - close) * spec.rr
            return {
                "direction": "short",
                "wave1": wave1,
                "wave3": wave3,
                "wave2_retrace": wave2_retrace,
                "wave4_retrace": wave4_retrace,
                "trigger_level": l3.price,
                "stop": stop,
                "target": target,
            }
    return None


def run_spec(df: pd.DataFrame, symbol: str, timeframe: str, spec: StrategySpec) -> pd.DataFrame:
    settings = timeframe_settings(timeframe)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < START or ts > END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        sig = v_fib_signal(df, i, active, spec, settings) if spec.family == "V字フィボ" else elliott_signal(df, i, active, spec, settings)
        if sig is None:
            continue
        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=sig["direction"],
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
            invalidation_level=float(sig["trigger_level"]) if "trigger_level" in sig else None,
            early_exit_bars=spec.early_exit_bars,
        )
        if trade is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": spec.name,
                "family": spec.family,
                "signal_time": ts,
                "direction": sig["direction"],
                **{k: v for k, v in sig.items() if k not in {"direction", "stop", "target"}},
                **trade,
            }
        )
        exit_pos = df.index.get_loc(trade["exit_time"])
        in_pos_until = int(exit_pos)
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


def summarize(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = group["r_after_cost"]
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": int(len(group)),
                "win_rate": float((r > 0).mean() * 100),
                "total_r_after_cost": float(r.sum()),
                "avg_r_after_cost": float(r.mean()),
                "pf_after_cost": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "avg_hold_bars": float(group["bars_held"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])


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


def write_report(trades: pd.DataFrame, overall: pd.DataFrame, by_symbol: pd.DataFrame, by_year: pd.DataFrame) -> None:
    lines = [
        "# Elliott / V-Fibonacci Mechanical Study 2015-2024",
        "",
        "## Tested definitions",
        "",
        "- V字フィボ: confirmed pivot high/low pair after a sharp move, then entry when close recovers 61.8/78.6/100% of that swing.",
        "- エリオット風5波目: confirmed pivot sequence L-H-L-H-L or H-L-H-L-H, wave-2 and wave-4 retrace 23.6-78.6% / 23.6-61.8%, then enter on wave-3 extreme breakout.",
        "- Entries use next bar open. SL is behind the V extreme or wave-4 pivot. TP is fixed RR or Fib extension depending on the variant.",
        "- Costs are approximated with the same spread/slippage table used in the TrendBreak fakeout studies.",
        "- Dec 15 to Jan 10 is skipped.",
        "",
        "## Overall Top",
        "",
        markdown_table(overall, 40),
        "",
        "## Symbol Breakdown Top",
        "",
        markdown_table(by_symbol, 80),
        "",
        "## Yearly Top",
        "",
        markdown_table(by_year, 80),
        "",
        "## Output Files",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_year.csv`",
        "- `report_ja.md`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_rows = []
    coverage_rows = []
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        for timeframe in TIMEFRAMES:
            df = add_indicators(resample_ohlc(raw, timeframe))
            for spec in SPECS:
                trades = run_spec(df, symbol, timeframe, spec)
                if not trades.empty:
                    all_rows.append(trades)

    if all_rows:
        trades_df = pd.concat(all_rows, ignore_index=True)
        trades_df["signal_time"] = pd.to_datetime(trades_df["signal_time"])
        trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"])
        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])
        trades_df["year"] = trades_df["entry_time"].dt.year.astype(str)
        trades_df = trades_df.sort_values(["timeframe", "strategy", "entry_time", "symbol"]).reset_index(drop=True)
    else:
        trades_df = pd.DataFrame()

    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if trades_df.empty:
        (OUT_DIR / "report_ja.md").write_text("# Elliott / V-Fibonacci Study\n\nNo trades.", encoding="utf-8")
        print(f"No trades. Report: {OUT_DIR / 'report_ja.md'}")
        return

    overall = summarize(trades_df, ["timeframe", "family", "strategy"])
    by_symbol = summarize(trades_df, ["timeframe", "family", "strategy", "symbol"])
    by_year = summarize(trades_df, ["timeframe", "family", "strategy", "year"])
    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_year.to_csv(OUT_DIR / "summary_by_year.csv", index=False)
    write_report(trades_df, overall, by_symbol, by_year)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(overall.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

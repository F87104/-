#!/usr/bin/env python3
"""
Sai H1 price-action backtester.

This script tests a mechanical approximation of the Sai method from the
local rule spec. It is deliberately conservative: signals are generated at
the close of a 1H candle and entered at the next 1H open.

Outputs:
  - trades.csv
  - summary_by_symbol.csv
  - summary_by_method.csv
  - summary_by_method_symbol.csv
  - summary_by_setup.csv
  - report.md

The result is a research baseline, not financial advice and not a guarantee
that the discretionary method has been fully reproduced.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class Config:
    start: str = "2015-01-01"
    end: str = "2024-12-31 23:59:59"
    atr_period: int = 14
    medium_lookback: int = 520
    short_lookback: int = 72
    recent_lookback: int = 8
    trend_min_atr: float = 2.0
    momentum_lookback: int = 12
    momentum_min_atr: float = 1.0
    body_ratio_min: float = 0.50
    stagnation_min_bars: int = 7
    stagnation_max_bars: int = 24
    stagnation_max_atr: float = 1.20
    wide_stagnation_max_atr: float = 2.50
    breakout_buffer_atr: float = 0.10
    key_level_lookback: int = 720
    key_level_near_atr: float = 1.25
    range_min_bars: int = 480
    range_max_atr: float = 10.0
    range_touch_atr: float = 0.75
    range_min_touches: int = 2
    second_break_lookback: int = 160
    vshape_lookback: int = 96
    vshape_min_move_atr: float = 3.0
    vshape_recovery_ratio: float = 0.80
    min_stop_atr: float = 0.50
    max_hold_days: int = 60
    bonus_time_days: int = 21
    swing_pivot_width: int = 2
    consolidation_bars: int = 48
    consolidation_max_atr: float = 3.0
    counter_move_lookback: int = 12
    counter_move_atr: float = 1.5
    skip_usdjpy: bool = True
    skip_holiday_market: bool = True


@dataclass
class Zone:
    valid: bool
    high: float = 0.0
    low: float = 0.0
    bars: int = 0
    wide: bool = False


@dataclass
class Signal:
    symbol: str
    signal_time: pd.Timestamp
    direction: str
    setup: str
    entry_signal_price: float
    stop_signal_price: float
    zone_high: float
    zone_low: float
    key_level: Optional[float]
    score: float
    reason: str


def normalize_symbol(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", symbol).upper()


def read_symbol_csvs(data_root: Path, symbol: str) -> pd.DataFrame:
    files = sorted(data_root.rglob(f"*{symbol}*H1*.csv"))
    if symbol == "GBPJPY":
        files += sorted(data_root.rglob("*GBY*JPY*H1*.csv"))
    if symbol == "XAGUSD":
        files += sorted(data_root.rglob("*SILVER*H1*.csv"))
    frames: list[pd.DataFrame] = []

    for file in files:
        df = pd.read_csv(file)
        df.columns = [c.strip("<>").lower() for c in df.columns]
        if "ticker" not in df.columns:
            continue
        ticker = normalize_symbol(str(df["ticker"].iloc[0]))
        if ticker != symbol:
            continue
        time_text = df["time"].astype(str).str.zfill(4)
        dt_text = df["dtyyyymmdd"].astype(str) + time_text
        df["datetime"] = pd.to_datetime(dt_text, format="%Y%m%d%H%M", errors="coerce")
        df = df.rename(
            columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
            }
        )
        frames.append(df[["datetime", "open", "high", "low", "close", "volume"]])

    if not frames:
        raise FileNotFoundError(f"No CSV files found for {symbol} under {data_root}")

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["datetime"])
    out = out.drop_duplicates(subset=["datetime"], keep="last")
    out = out.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"])
    out["datetime"] = out["datetime"].dt.floor("h")
    out = (
        out.groupby("datetime", as_index=False)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .sort_values("datetime")
        .reset_index(drop=True)
    )
    return out.reset_index(drop=True)


def available_symbols(data_root: Path) -> list[str]:
    symbols = set()
    for file in data_root.rglob("*.csv"):
        try:
            sample = pd.read_csv(file, nrows=1)
        except Exception:
            continue
        sample.columns = [c.strip("<>").lower() for c in sample.columns]
        if "ticker" not in sample.columns or sample.empty:
            continue
        symbol = normalize_symbol(str(sample["ticker"].iloc[0]))
        if symbol:
            symbols.add(symbol)
    return sorted(symbols)


def add_indicators(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    df = df.copy()
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr"] = tr.rolling(cfg.atr_period).mean()
    return df


def direction_by_window(close: pd.Series, atr: float, end: int, lookback: int, cfg: Config) -> str:
    if end - lookback + 1 < 0 or not math.isfinite(atr) or atr <= 0:
        return "none"
    start = end - lookback + 1
    segment = max(5, lookback // 5)
    first = close.iloc[start : start + segment].mean()
    last = close.iloc[end - segment + 1 : end + 1].mean()
    delta = last - first
    if delta > atr * cfg.trend_min_atr:
        return "long"
    if delta < -atr * cfg.trend_min_atr:
        return "short"
    return "none"


def recent_direction(close: pd.Series, atr: float, end: int, cfg: Config) -> str:
    if end - cfg.recent_lookback < 0 or not math.isfinite(atr) or atr <= 0:
        return "none"
    delta = close.iloc[end] - close.iloc[end - cfg.recent_lookback]
    if delta > atr * 0.35:
        return "long"
    if delta < -atr * 0.35:
        return "short"
    return "none"


def has_momentum(df: pd.DataFrame, end: int, direction: str, atr: float, cfg: Config) -> bool:
    if direction == "none" or end - cfg.momentum_lookback + 1 < 0:
        return False
    start = end - cfg.momentum_lookback + 1
    net = df["close"].iloc[end] - df["open"].iloc[start]
    if direction == "long" and net <= atr * cfg.momentum_min_atr:
        return False
    if direction == "short" and net >= -atr * cfg.momentum_min_atr:
        return False
    bodies = df["close"].iloc[start : end + 1] - df["open"].iloc[start : end + 1]
    if direction == "long":
        ratio = (bodies > 0).mean()
    else:
        ratio = (bodies < 0).mean()
    return bool(ratio >= cfg.body_ratio_min)


def find_stagnation(df: pd.DataFrame, trigger_index: int, atr: float, cfg: Config, max_atr: float) -> Zone:
    best = Zone(valid=False)
    end = trigger_index
    max_bars = min(cfg.stagnation_max_bars, end)
    for bars in range(cfg.stagnation_min_bars, max_bars + 1):
        start = end - bars
        high = float(df["high"].iloc[start:end].max())
        low = float(df["low"].iloc[start:end].min())
        if high - low <= atr * max_atr:
            best = Zone(valid=True, high=high, low=low, bars=bars, wide=max_atr > cfg.stagnation_max_atr)
    return best


def detect_range(df: pd.DataFrame, end: int, atr: float, cfg: Config) -> tuple[bool, float, float]:
    if end - cfg.range_min_bars + 1 < 0:
        return False, 0.0, 0.0
    start = end - cfg.range_min_bars + 1
    window = df.iloc[start : end + 1]
    high = float(window["high"].max())
    low = float(window["low"].min())
    if high - low > atr * cfg.range_max_atr:
        return False, high, low
    tolerance = atr * cfg.range_touch_atr
    high_touches = int((window["high"] >= high - tolerance).sum())
    low_touches = int((window["low"] <= low + tolerance).sum())
    return high_touches >= cfg.range_min_touches and low_touches >= cfg.range_min_touches, high, low


def near_key_level(df: pd.DataFrame, end: int, direction: str, zone: Zone, atr: float, cfg: Config) -> tuple[bool, Optional[float]]:
    if end - cfg.key_level_lookback + 1 < 0:
        return False, None
    start = end - cfg.key_level_lookback + 1
    window = df.iloc[start : end + 1]
    tolerance = atr * cfg.key_level_near_atr
    if direction == "long":
        level = float(window["high"].max())
        return abs(zone.high - level) <= tolerance or zone.high >= level - tolerance, level
    level = float(window["low"].min())
    return abs(zone.low - level) <= tolerance or zone.low <= level + tolerance, level


def second_range_breakout(df: pd.DataFrame, i: int, direction: str, atr: float, cfg: Config) -> tuple[bool, Optional[float]]:
    prior_end = i - cfg.second_break_lookback
    if prior_end <= cfg.range_min_bars:
        return False, None
    range_start = prior_end - cfg.range_min_bars
    range_window = df.iloc[range_start:prior_end]
    range_high = float(range_window["high"].max())
    range_low = float(range_window["low"].min())
    if range_high - range_low > atr * cfg.range_max_atr:
        return False, None

    scan = df.iloc[prior_end:i]
    buffer = atr * cfg.breakout_buffer_atr
    first_break = False
    returned_inside = False
    if direction == "long":
        first_extreme = -math.inf
        for _, row in scan.iterrows():
            if row["high"] > range_high + buffer:
                first_break = True
                first_extreme = max(first_extreme, float(row["high"]))
            if first_break and row["close"] < range_high:
                returned_inside = True
        return first_break and returned_inside and df["close"].iloc[i] > first_extreme + buffer, first_extreme

    first_extreme = math.inf
    for _, row in scan.iterrows():
        if row["low"] < range_low - buffer:
            first_break = True
            first_extreme = min(first_extreme, float(row["low"]))
        if first_break and row["close"] > range_low:
            returned_inside = True
    return first_break and returned_inside and df["close"].iloc[i] < first_extreme - buffer, first_extreme


def vshape_context(df: pd.DataFrame, end: int, direction: str, atr: float, cfg: Config) -> bool:
    if end - cfg.vshape_lookback + 1 < 0:
        return False
    start = end - cfg.vshape_lookback + 1
    window = df.iloc[start : end + 1]
    if direction == "long":
        valley_pos = int(window["low"].values.argmin())
        if valley_pos <= 2 or valley_pos >= len(window) - 3:
            return False
        pre_high = float(window["high"].iloc[:valley_pos].max())
        valley = float(window["low"].iloc[valley_pos])
        drop = pre_high - valley
        recovery = float(window["close"].iloc[-1]) - valley
        return drop >= atr * cfg.vshape_min_move_atr and recovery >= drop * cfg.vshape_recovery_ratio

    peak_pos = int(window["high"].values.argmax())
    if peak_pos <= 2 or peak_pos >= len(window) - 3:
        return False
    pre_low = float(window["low"].iloc[:peak_pos].min())
    peak = float(window["high"].iloc[peak_pos])
    rally = peak - pre_low
    recovery = peak - float(window["close"].iloc[-1])
    return rally >= atr * cfg.vshape_min_move_atr and recovery >= rally * cfg.vshape_recovery_ratio


def holiday_market(ts: pd.Timestamp, cfg: Config) -> bool:
    if not cfg.skip_holiday_market:
        return False
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def direction_ja(direction: str) -> str:
    if direction == "long":
        return "買い"
    if direction == "short":
        return "売り"
    return "なし"


def method_name_ja(setup: str, direction: str) -> str:
    high_low = "高値" if direction == "long" else "安値"
    resistance_support = "抵抗線" if direction == "long" else "支持線"
    v_word = "V字" if direction == "long" else "逆V字"

    if setup == "SimpleStagnation":
        return f"{high_low}停滞"
    if setup == "KeyLevelStagnation":
        return f"{resistance_support}付近の{high_low}停滞"
    if setup == "PostBreakoutStagnation":
        return f"ブレイク後の{high_low}停滞"
    if setup == "WideStagnation":
        return f"値幅広めの{high_low}停滞"
    if setup == "VShapeStagnation":
        return f"{v_word}＋{high_low}停滞"
    if setup == "SuddenReversalStagnation":
        return f"急な揺り戻し＋{high_low}停滞"
    if setup == "SecondRangeBreakout":
        return "レンジ抜け2回目以降のブレイクアウト"
    return setup


def method_family_ja(setup: str) -> str:
    if setup in {"SimpleStagnation", "KeyLevelStagnation", "PostBreakoutStagnation", "WideStagnation"}:
        return "高安値停滞"
    if setup in {"VShapeStagnation", "SuddenReversalStagnation"}:
        return "V字/急な揺り戻し＋停滞"
    if setup == "SecondRangeBreakout":
        return "レンジ抜け2回目以降"
    return setup


def generate_signal(df: pd.DataFrame, symbol: str, i: int, cfg: Config) -> Optional[Signal]:
    ts = df["datetime"].iloc[i]
    if cfg.skip_usdjpy and symbol == "USDJPY":
        return None
    if holiday_market(ts, cfg):
        return None

    atr = float(df["atr"].iloc[i - 1])
    if not math.isfinite(atr) or atr <= 0:
        return None

    tight = find_stagnation(df, i, atr, cfg, cfg.stagnation_max_atr)
    wide = find_stagnation(df, i, atr, cfg, cfg.wide_stagnation_max_atr)
    zone = tight if tight.valid else wide

    close = df["close"].iloc[i]
    buffer = atr * cfg.breakout_buffer_atr

    directions: list[str] = []
    if zone.valid and close > zone.high + buffer:
        directions.append("long")
    if zone.valid and close < zone.low - buffer:
        directions.append("short")

    for direction in ["long", "short"]:
        ok_second, second_level = second_range_breakout(df, i, direction, atr, cfg)
        if ok_second:
            directions.append(direction)

    for direction in directions:
        medium = direction_by_window(df["close"], atr, i - 1, cfg.medium_lookback, cfg)
        short = recent_direction(df["close"], atr, i, cfg)
        if short == "none":
            short = direction_by_window(df["close"], atr, i, cfg.short_lookback, cfg)
        if medium != direction or short != direction:
            continue

        pre_zone_end = max(0, i - (zone.bars if zone.valid else 1) - 1)
        momentum = has_momentum(df, pre_zone_end, direction, atr, cfg) or has_momentum(df, i, direction, atr, cfg)
        if not momentum:
            continue

        range_like, range_high, range_low = detect_range(df, i - 1, atr, cfg)
        ok_second, second_level = second_range_breakout(df, i, direction, atr, cfg)
        if range_like:
            if direction == "long" and close <= range_high + buffer:
                continue
            if direction == "short" and close >= range_low - buffer:
                continue
            if not ok_second and not zone.valid:
                continue

        if ok_second and second_level is not None:
            stop = second_level - atr if direction == "long" else second_level + atr
            return Signal(
                symbol=symbol,
                signal_time=ts,
                direction=direction,
                setup="SecondRangeBreakout",
                entry_signal_price=float(close),
                stop_signal_price=float(stop),
                zone_high=range_high,
                zone_low=range_low,
                key_level=second_level,
                score=0.85,
                reason="range first breakout failed, second breakout triggered",
            )

        if not zone.valid:
            continue

        near_key, key = near_key_level(df, i - 1, direction, zone, atr, cfg)
        vshape = vshape_context(df, i - 1, direction, atr, cfg)

        setup = "SimpleStagnation"
        score = 0.65
        if vshape and near_key:
            setup = "VShapeStagnation"
            score = 0.90
        elif vshape:
            setup = "SuddenReversalStagnation"
            score = 0.78
        elif near_key and zone.wide:
            setup = "WideStagnation"
            score = 0.76
        elif near_key:
            setup = "KeyLevelStagnation"
            score = 0.82
        elif zone.wide:
            setup = "WideStagnation"
            score = 0.68

        stop = zone.low - atr * 0.25 if direction == "long" else zone.high + atr * 0.25
        return Signal(
            symbol=symbol,
            signal_time=ts,
            direction=direction,
            setup=setup,
            entry_signal_price=float(close),
            stop_signal_price=float(stop),
            zone_high=zone.high,
            zone_low=zone.low,
            key_level=key,
            score=score,
            reason=f"{setup} with short-mid alignment and momentum",
        )

    return None


def latest_pivot_level(df: pd.DataFrame, start: int, end: int, direction: str, width: int) -> Optional[float]:
    if end - start < width * 2 + 1:
        return None
    level = None
    for i in range(start + width, end - width + 1):
        lows = df["low"].iloc[i - width : i + width + 1]
        highs = df["high"].iloc[i - width : i + width + 1]
        if direction == "long" and df["low"].iloc[i] == lows.min():
            level = float(df["low"].iloc[i])
        elif direction == "short" and df["high"].iloc[i] == highs.max():
            level = float(df["high"].iloc[i])
    return level


def manage_trade(df: pd.DataFrame, entry_i: int, signal: Signal, cfg: Config) -> dict:
    direction = signal.direction
    entry_time = df["datetime"].iloc[entry_i]
    entry = float(df["open"].iloc[entry_i])
    atr = float(df["atr"].iloc[entry_i - 1])
    stop = signal.stop_signal_price
    if direction == "long":
        stop = min(stop, entry - atr * cfg.min_stop_atr)
        risk = entry - stop
    else:
        stop = max(stop, entry + atr * cfg.min_stop_atr)
        risk = stop - entry
    if risk <= 0 or not math.isfinite(risk):
        risk = atr * cfg.min_stop_atr
        stop = entry - risk if direction == "long" else entry + risk

    exit_i = entry_i
    exit_price = entry
    exit_reason = "end_of_data"
    max_favorable_r = 0.0
    max_adverse_r = 0.0

    max_hold_time = entry_time + pd.Timedelta(days=cfg.max_hold_days)

    for j in range(entry_i, len(df)):
        row = df.iloc[j]
        now = row["datetime"]

        if direction == "long":
            max_favorable_r = max(max_favorable_r, (float(row["high"]) - entry) / risk)
            max_adverse_r = min(max_adverse_r, (float(row["low"]) - entry) / risk)
            if float(row["low"]) <= stop:
                exit_i = j
                exit_price = stop
                exit_reason = "initial_stop"
                break
        else:
            max_favorable_r = max(max_favorable_r, (entry - float(row["low"])) / risk)
            max_adverse_r = min(max_adverse_r, (entry - float(row["high"])) / risk)
            if float(row["high"]) >= stop:
                exit_i = j
                exit_price = stop
                exit_reason = "initial_stop"
                break

        open_profit = (float(row["close"]) - entry) if direction == "long" else (entry - float(row["close"]))
        if open_profit > risk * 0.25:
            pivot = latest_pivot_level(df, entry_i, j, direction, cfg.swing_pivot_width)
            if pivot is not None:
                if direction == "long" and float(row["close"]) < pivot:
                    exit_i = j
                    exit_price = float(row["close"])
                    exit_reason = "one_swing_break"
                    break
                if direction == "short" and float(row["close"]) > pivot:
                    exit_i = j
                    exit_price = float(row["close"])
                    exit_reason = "one_swing_break"
                    break

            if j - entry_i >= cfg.consolidation_bars:
                cons = df.iloc[j - cfg.consolidation_bars + 1 : j + 1]
                cons_atr = float(df["atr"].iloc[j])
                if math.isfinite(cons_atr) and cons_atr > 0:
                    cons_high = float(cons["high"].max())
                    cons_low = float(cons["low"].min())
                    if cons_high - cons_low <= cons_atr * cfg.consolidation_max_atr:
                        if direction == "long" and float(row["close"]) < cons_low:
                            exit_i = j
                            exit_price = float(row["close"])
                            exit_reason = "consolidation_neckline_break"
                            break
                        if direction == "short" and float(row["close"]) > cons_high:
                            exit_i = j
                            exit_price = float(row["close"])
                            exit_reason = "consolidation_neckline_break"
                            break

        if now > entry_time + pd.Timedelta(days=cfg.bonus_time_days):
            lookback_start = max(entry_i, j - cfg.counter_move_lookback + 1)
            recent = df.iloc[lookback_start : j + 1]
            current_atr = float(df["atr"].iloc[j])
            if math.isfinite(current_atr) and current_atr > 0:
                if direction == "long":
                    counter = float(recent["high"].max()) - float(row["close"])
                    if counter >= current_atr * cfg.counter_move_atr and open_profit > 0:
                        exit_i = j
                        exit_price = float(row["close"])
                        exit_reason = "post_bonus_counter_move"
                        break
                else:
                    counter = float(row["close"]) - float(recent["low"].min())
                    if counter >= current_atr * cfg.counter_move_atr and open_profit > 0:
                        exit_i = j
                        exit_price = float(row["close"])
                        exit_reason = "post_bonus_counter_move"
                        break

        if now >= max_hold_time:
            exit_i = j
            exit_price = float(row["close"])
            exit_reason = "max_hold"
            break

    pnl = (exit_price - entry) if direction == "long" else (entry - exit_price)
    r = pnl / risk
    return {
        "symbol": signal.symbol,
        "setup": signal.setup,
        "method": method_name_ja(signal.setup, direction),
        "method_family": method_family_ja(signal.setup),
        "direction": direction,
        "direction_ja": direction_ja(direction),
        "signal_time": signal.signal_time,
        "entry_time": entry_time,
        "entry": entry,
        "stop": stop,
        "exit_time": df["datetime"].iloc[exit_i],
        "exit": exit_price,
        "exit_reason": exit_reason,
        "risk": risk,
        "r": r,
        "max_favorable_r": max_favorable_r,
        "max_adverse_r": max_adverse_r,
        "hold_days": (df["datetime"].iloc[exit_i] - entry_time).total_seconds() / 86400.0,
        "score": signal.score,
        "reason": signal.reason,
    }


def backtest_symbol(df: pd.DataFrame, symbol: str, cfg: Config) -> pd.DataFrame:
    df = add_indicators(df, cfg)
    start_ts = pd.Timestamp(cfg.start)
    end_ts = pd.Timestamp(cfg.end)
    trades: list[dict] = []

    min_bars = max(
        cfg.medium_lookback,
        cfg.key_level_lookback,
        cfg.range_min_bars + cfg.second_break_lookback,
        cfg.vshape_lookback,
    ) + 5
    i = min_bars
    while i < len(df) - 1:
        ts = df["datetime"].iloc[i]
        if ts < start_ts:
            i += 1
            continue
        if ts > end_ts:
            break
        sig = generate_signal(df, symbol, i, cfg)
        if sig is None:
            i += 1
            continue
        trade = manage_trade(df, i + 1, sig, cfg)
        trades.append(trade)
        exit_time = trade["exit_time"]
        exit_candidates = df.index[df["datetime"] >= exit_time]
        i = int(exit_candidates[0]) + 1 if len(exit_candidates) else len(df)

    return pd.DataFrame(trades)


def summarize(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()

    def max_drawdown(values: pd.Series) -> float:
        curve = values.cumsum()
        dd = curve - curve.cummax()
        return float(dd.min()) if len(dd) else 0.0

    rows = []
    for key, g in trades.groupby(group_cols, dropna=False):
        if len(group_cols) == 1 and isinstance(key, tuple):
            key = key[0]
        wins = g[g["r"] > 0]
        losses = g[g["r"] <= 0]
        gross_win = wins["r"].sum()
        gross_loss = -losses["r"].sum()
        rows.append(
            {
                **(
                    {group_cols[0]: key}
                    if len(group_cols) == 1
                    else {col: value for col, value in zip(group_cols, key)}
                ),
                "trades": int(len(g)),
                "win_rate": float((g["r"] > 0).mean()),
                "total_r": float(g["r"].sum()),
                "avg_r": float(g["r"].mean()),
                "median_r": float(g["r"].median()),
                "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else math.inf,
                "max_drawdown_r": max_drawdown(g["r"]),
                "avg_hold_days": float(g["hold_days"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("total_r", ascending=False)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    display = df.copy()
    for col in display.columns:
        if pd.api.types.is_float_dtype(display[col]):
            display[col] = display[col].map(lambda x: f"{x:.3f}" if math.isfinite(float(x)) else str(x))
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def write_report(
    out_dir: Path,
    trades: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_method: pd.DataFrame,
    by_method_symbol: pd.DataFrame,
    by_setup: pd.DataFrame,
    cfg: Config,
) -> None:
    if trades.empty:
        text = "# Sai H1 Backtest Report\n\nNo trades were generated.\n"
        (out_dir / "report.md").write_text(text, encoding="utf-8")
        return

    total_wins = trades[trades["r"] > 0]["r"].sum()
    total_losses = -trades[trades["r"] <= 0]["r"].sum()
    pf = total_wins / total_losses if total_losses > 0 else math.inf
    curve = trades["r"].cumsum()
    dd = curve - curve.cummax()
    text = f"""# Sai H1 Backtest Report

Period: `{cfg.start}` to `{cfg.end}`

This is a mechanical baseline of the Sai conditions. It uses next-candle entry after a signal and R-multiple scoring.

## Overall

- Trades: {len(trades)}
- Win rate: {(trades["r"] > 0).mean():.2%}
- Total R: {trades["r"].sum():.2f}
- Average R: {trades["r"].mean():.3f}
- Median R: {trades["r"].median():.3f}
- Profit factor: {pf:.2f}
- Max drawdown: {dd.min():.2f} R
- Average hold days: {trades["hold_days"].mean():.2f}

## By Symbol

{markdown_table(by_symbol)}

## By Method

{markdown_table(by_method)}

## By Method And Symbol

{markdown_table(by_method_symbol)}

## By Internal Setup

{markdown_table(by_setup)}

## Notes

- USDJPY is skipped by default because the transcript says Sai's method is less compatible with USDJPY.
- Mid-December through January 10 is skipped by default.
- The result should be treated as a first scanner/backtest baseline, not as final EA logic.
- Next useful step: inspect losing clusters and false positives by chart screenshot.
"""
    (out_dir / "report.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("../fx-test-data"))
    parser.add_argument("--out-dir", type=Path, default=Path("backtests/sai_h1/results_2015_2024"))
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31 23:59:59")
    parser.add_argument("--symbols", nargs="*", default=None)
    parser.add_argument("--include-usdjpy", action="store_true")
    parser.add_argument("--include-holiday-market", action="store_true")
    args = parser.parse_args()

    cfg = Config(
        start=args.start,
        end=args.end,
        skip_usdjpy=not args.include_usdjpy,
        skip_holiday_market=not args.include_holiday_market,
    )
    data_root = args.data_root.resolve()
    symbols = args.symbols or available_symbols(data_root)
    symbols = [normalize_symbol(s) for s in symbols]

    all_trades: list[pd.DataFrame] = []
    coverage_rows = []
    for symbol in symbols:
        try:
            df = read_symbol_csvs(data_root, symbol)
        except FileNotFoundError:
            continue
        coverage_rows.append(
            {
                "symbol": symbol,
                "rows": len(df),
                "first": df["datetime"].min(),
                "last": df["datetime"].max(),
            }
        )
        trades = backtest_symbol(df, symbol, cfg)
        if not trades.empty:
            all_trades.append(trades)

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(coverage_rows).to_csv(out_dir / "data_coverage.csv", index=False)

    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    if not trades.empty:
        trades = trades.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    trades.to_csv(out_dir / "trades.csv", index=False)

    by_symbol = summarize(trades, ["symbol"])
    by_method = summarize(trades, ["method"])
    by_method_symbol = summarize(trades, ["method", "symbol"])
    by_setup = summarize(trades, ["setup"])
    by_symbol.to_csv(out_dir / "summary_by_symbol.csv", index=False)
    by_method.to_csv(out_dir / "summary_by_method.csv", index=False)
    by_method_symbol.to_csv(out_dir / "summary_by_method_symbol.csv", index=False)
    by_setup.to_csv(out_dir / "summary_by_setup.csv", index=False)
    write_report(out_dir, trades, by_symbol, by_method, by_method_symbol, by_setup, cfg)

    print(f"Wrote results to {out_dir}")
    if trades.empty:
        print("No trades generated.")
    else:
        print(f"Trades: {len(trades)}")
        print(f"Total R: {trades['r'].sum():.2f}")
        print(f"Win rate: {(trades['r'] > 0).mean():.2%}")


if __name__ == "__main__":
    main()

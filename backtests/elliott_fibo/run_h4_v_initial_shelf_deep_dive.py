#!/usr/bin/env python3
"""
Deep validation for H4 V Initial Shelf Breakout.

This script treats the 36d90e6 study as the baseline and audits whether the
method is robust enough to keep as a live candidate. It deliberately avoids
choosing the highest-PF tiny cell. Instead it runs controlled sensitivity
blocks around the current rule and reports structural reasons.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

import run_h4_v_kickoff_catalyst_study as kickoff
from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    build_confirmed_pivots,
    direction_cost_r,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    timeframe_settings,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_30" / "h4_v_initial_shelf_deep_dive"
SOURCE_OUT_DIR = THIS_DIR / "results_2026_05_30" / "h4_v_kickoff_catalyst"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
SELECTED_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
EXCLUDED_FOR_CURRENT = ["XAUUSD", "CHFJPY", "SILVER"]


@dataclass(frozen=True)
class DeepSpec:
    name: str
    family: str = "current"
    min_drop_atr: float = 2.8
    min_drop_speed: float = 0.25
    min_speed_ratio: float = 1.0
    min_recovery_ratio: float = 0.65
    max_recovery_ratio: float = 1.25
    min_drop_bars: int = 2
    max_drop_bars: int = 30
    max_recovery_bars: int = 36
    shelf_bars: int = 6
    max_shelf_range_atr: float = 1.8
    shelf_hold_ratio: float = 0.50
    breakout_buffer_atr: float = 0.05
    min_body_ratio: float = 0.40
    min_close_location: float = 0.60
    max_risk_atr: float = 2.2
    rr: float = 1.5
    stop_buffer_atr: float = 0.25
    max_hold_bars: int = 120
    max_context_bars: int = 36
    require_pre_calm: bool = True
    adx_max: float = 26.0
    range60_max_atr: float = 16.0
    ema_slope_mode: str = "standard"
    entry_mode: str = "next_open"  # next_open or signal_close
    target_basis: str = "signal"  # signal reproduces 36d90e6, entry is cleaner live logic


CURRENT_SPEC = DeepSpec("CURRENT_PRECALM_SHELF6_RR15")


def slope_limits(mode: str) -> tuple[float, float]:
    if mode == "none":
        return math.inf, math.inf
    if mode == "weak":
        return 1.6, 3.5
    if mode == "standard":
        return 1.2, 3.0
    if mode == "strict":
        return 0.8, 2.5
    raise ValueError(f"unknown ema_slope_mode: {mode}")


def finite(v: float) -> bool:
    return math.isfinite(float(v))


def load_h4_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        data[symbol] = kickoff.add_features(resample_ohlc(raw, TIMEFRAME))
    return data


def pre_calm_ok(df: pd.DataFrame, start_i: int, spec: DeepSpec) -> bool:
    if start_i < 80:
        return False
    adx_v = float(df["adx14"].iloc[start_i])
    slope = float(df["ema50_slope_20_atr"].iloc[start_i])
    stretch = float(df["close_ema50_stretch_atr"].iloc[start_i])
    range60 = float(df["range60_atr"].iloc[start_i])
    if not all(finite(x) for x in [adx_v, slope, stretch, range60]):
        return False
    slope_max, stretch_max = slope_limits(spec.ema_slope_mode)
    return adx_v <= spec.adx_max and range60 <= spec.range60_max_atr and slope <= slope_max and stretch <= stretch_max


def find_v_context(
    df: pd.DataFrame,
    i: int,
    active: list,
    spec: DeepSpec,
    used_pairs: set[str],
) -> dict | None:
    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not finite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    pairs_scanned = 0
    idx = len(active) - 2
    while idx >= 0 and pairs_scanned < 12:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        pairs_scanned += 1
        if p0.kind != "H" or p1.kind != "L":
            continue
        pair_key = f"{p0.pivot_i}-{p1.pivot_i}"
        if pair_key in used_pairs:
            continue
        drop = p0.price - p1.price
        if drop <= 0:
            continue
        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        recovery_bars = max(i - p1.pivot_i, 1)
        if drop_bars < spec.min_drop_bars or drop_bars > spec.max_drop_bars:
            continue
        if recovery_bars > spec.max_recovery_bars:
            continue
        drop_atr = drop / atr_i
        drop_speed = drop / drop_bars / atr_i
        recovery = close - p1.price
        recovery_ratio = recovery / drop
        recovery_speed = recovery / recovery_bars / atr_i
        speed_ratio = recovery_speed / drop_speed if drop_speed > 0 else math.nan
        if drop_atr < spec.min_drop_atr or drop_speed < spec.min_drop_speed:
            continue
        if not finite(speed_ratio) or speed_ratio < spec.min_speed_ratio:
            continue
        if recovery_ratio < spec.min_recovery_ratio or recovery_ratio > spec.max_recovery_ratio:
            continue
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue
        return {
            "pair_key": pair_key,
            "v_start_i": p0.pivot_i,
            "v_low_i": p1.pivot_i,
            "v_start_time": df.index[p0.pivot_i],
            "v_low_time": df.index[p1.pivot_i],
            "v_start_confirm_time": df.index[p0.confirm_i],
            "v_low_confirm_time": df.index[p1.confirm_i],
            "v_start": p0.price,
            "v_low": p1.price,
            "drop": drop,
            "drop_atr": drop_atr,
            "drop_bars": drop_bars,
            "context_i": i,
            "context_time": df.index[i],
            "context_recovery_bars": recovery_bars,
            "context_recovery_ratio": recovery_ratio,
            "drop_speed": drop_speed,
            "context_recovery_speed": recovery_speed,
            "context_speed_ratio": speed_ratio,
            "pre_adx14": float(df["adx14"].iloc[p0.pivot_i]),
            "pre_ema50_slope_20_atr": float(df["ema50_slope_20_atr"].iloc[p0.pivot_i]),
            "pre_close_ema50_stretch_atr": float(df["close_ema50_stretch_atr"].iloc[p0.pivot_i]),
            "pre_range60_atr": float(df["range60_atr"].iloc[p0.pivot_i]),
        }
    return None


def shelf_signal(df: pd.DataFrame, i: int, ctx: dict, spec: DeepSpec) -> dict | None:
    atr_i = float(df["atr"].iloc[i])
    if not finite(atr_i) or atr_i <= 0:
        return None
    if i - int(ctx["context_i"]) > spec.max_context_bars:
        return {"expired": True}
    if i - int(ctx["context_i"]) < spec.shelf_bars:
        return None
    if i - spec.shelf_bars < int(ctx["context_i"]):
        return None
    if float(df["body_ratio"].iloc[i]) < spec.min_body_ratio:
        return None
    if float(df["close_location"].iloc[i]) < spec.min_close_location:
        return None
    if spec.require_pre_calm and not pre_calm_ok(df, int(ctx["v_start_i"]), spec):
        return None

    shelf = df.iloc[i - spec.shelf_bars : i]
    shelf_high = float(shelf["high"].max())
    shelf_low = float(shelf["low"].min())
    shelf_range_atr = (shelf_high - shelf_low) / atr_i
    shelf_hold_level = float(ctx["v_low"]) + float(ctx["drop"]) * spec.shelf_hold_ratio
    shelf_hold_actual = (shelf_low - float(ctx["v_low"])) / float(ctx["drop"])
    close = float(df["close"].iloc[i])
    breakout_atr = (close - shelf_high) / atr_i
    if shelf_range_atr > spec.max_shelf_range_atr:
        return None
    if shelf_low < shelf_hold_level - atr_i * 0.05:
        return None
    if breakout_atr <= spec.breakout_buffer_atr:
        return None

    stop = shelf_low - atr_i * spec.stop_buffer_atr
    signal_risk_atr = (close - stop) / atr_i
    if stop >= close or signal_risk_atr <= 0 or signal_risk_atr > spec.max_risk_atr:
        return None

    recovery_bars_signal = max(i - int(ctx["v_low_i"]), 1)
    recovery_ratio_signal = (close - float(ctx["v_low"])) / float(ctx["drop"])
    recovery_speed_signal = (close - float(ctx["v_low"])) / recovery_bars_signal / atr_i
    signal = {
        "signal_i": i,
        "signal_time": df.index[i],
        "atr_signal": atr_i,
        "shelf_high": shelf_high,
        "shelf_low": shelf_low,
        "shelf_bars": spec.shelf_bars,
        "shelf_range_atr": shelf_range_atr,
        "shelf_hold_level": shelf_hold_level,
        "shelf_hold_actual": shelf_hold_actual,
        "breakout_atr": breakout_atr,
        "signal_close": close,
        "stop": stop,
        "signal_risk_atr": signal_risk_atr,
        "body_ratio": float(df["body_ratio"].iloc[i]),
        "close_location": float(df["close_location"].iloc[i]),
        "signal_adx14": float(df["adx14"].iloc[i]),
        "signal_ema50_slope_20_atr": float(df["ema50_slope_20_atr"].iloc[i]),
        "signal_range60_atr": float(df["range60_atr"].iloc[i]),
        "recovery_bars_signal": recovery_bars_signal,
        "recovery_ratio_signal": recovery_ratio_signal,
        "recovery_speed_signal": recovery_speed_signal,
        "speed_ratio_signal": recovery_speed_signal / float(ctx["drop_speed"]) if float(ctx["drop_speed"]) > 0 else math.nan,
    }
    return signal


def simulate_trade_deep(df: pd.DataFrame, symbol: str, signal_i: int, signal: dict, spec: DeepSpec) -> dict | None:
    if spec.entry_mode == "next_open":
        entry_i = signal_i + 1
        first_exit_i = entry_i
        if entry_i >= len(df):
            return None
        entry = float(df["open"].iloc[entry_i])
        entry_time = df.index[entry_i]
    elif spec.entry_mode == "signal_close":
        entry_i = signal_i
        first_exit_i = signal_i + 1
        if first_exit_i >= len(df):
            return None
        entry = float(df["close"].iloc[signal_i])
        entry_time = df.index[signal_i]
    else:
        raise ValueError(f"unknown entry_mode: {spec.entry_mode}")

    stop = float(signal["stop"])
    risk = entry - stop
    if risk <= 0:
        return None
    if spec.target_basis == "entry":
        target = entry + risk * spec.rr
    elif spec.target_basis == "signal":
        signal_close = float(signal["signal_close"])
        target = signal_close + (signal_close - stop) * spec.rr
    else:
        raise ValueError(f"unknown target_basis: {spec.target_basis}")

    exit_i = min(len(df) - 1, entry_i + spec.max_hold_bars)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "max_hold"
    scan_end = min(len(df), first_exit_i + spec.max_hold_bars + 1)
    for j in range(first_exit_i, scan_end):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        hit_sl = lo <= stop
        hit_tp = hi >= target
        if hit_sl or hit_tp:
            exit_i = j
            exit_price = stop if hit_sl else target
            reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
            break

    hold_win = df.iloc[first_exit_i : exit_i + 1]
    if hold_win.empty:
        mfe_r = 0.0
        mae_r = 0.0
        mfe_atr = 0.0
        mae_atr = 0.0
    else:
        atr_signal = float(signal["atr_signal"])
        mfe_price = float(hold_win["high"].max()) - entry
        mae_price = entry - float(hold_win["low"].min())
        mfe_r = mfe_price / risk
        mae_r = mae_price / risk
        mfe_atr = mfe_price / atr_signal if atr_signal > 0 else math.nan
        mae_atr = mae_price / atr_signal if atr_signal > 0 else math.nan
    r_clean, r_after = direction_cost_r(symbol, "long", entry, exit_price, risk)
    return {
        "entry_time": entry_time,
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "risk_atr_entry": risk / float(signal["atr_signal"]),
        "r_clean": r_clean,
        "r_after_cost": r_after,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "mfe_atr_trade": mfe_atr,
        "mae_atr_trade": mae_atr,
    }


def forward_expansion(df: pd.DataFrame, signal_i: int, atr_i: float) -> dict:
    close = float(df["close"].iloc[signal_i])
    out: dict[str, float] = {}
    for h in [12, 24, 48, 72]:
        end = min(len(df) - 1, signal_i + h)
        if end <= signal_i:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"mae_{h}_atr"] = math.nan
            out[f"fwd_{h}_atr"] = math.nan
            continue
        win = df.iloc[signal_i + 1 : end + 1]
        out[f"mfe_{h}_atr"] = (float(win["high"].max()) - close) / atr_i
        out[f"mae_{h}_atr"] = (close - float(win["low"].min())) / atr_i
        out[f"fwd_{h}_atr"] = (float(df["close"].iloc[end]) - close) / atr_i
    return out


def run_spec_for_symbol(df: pd.DataFrame, pivots: list, symbol: str, spec: DeepSpec) -> pd.DataFrame:
    active: list = []
    pointer = 0
    used_pairs: set[str] = set()
    in_pos_until = -1
    context: dict | None = None
    rows: list[dict] = []

    for i in range(100, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        if context is None:
            context = find_v_context(df, i, active, spec, used_pairs)
            if context is None:
                continue

        signal = shelf_signal(df, i, context, spec)
        if signal is None:
            continue
        if signal.get("expired"):
            context = None
            continue

        trade = simulate_trade_deep(df, symbol, i, signal, spec)
        if trade is None:
            context = None
            continue

        used_pairs.add(str(context["pair_key"]))
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "family": spec.family,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                "month": pd.Timestamp(trade["entry_time"]).strftime("%Y-%m"),
                **context,
                **signal,
                **forward_expansion(df, i, float(signal["atr_signal"])),
                **trade,
                "param_shelf_bars": spec.shelf_bars,
                "param_shelf_range": spec.max_shelf_range_atr,
                "param_shelf_hold": spec.shelf_hold_ratio,
                "param_breakout_buffer": spec.breakout_buffer_atr,
                "param_body": spec.min_body_ratio,
                "param_close_location": spec.min_close_location,
                "param_adx_max": spec.adx_max,
                "param_range60_max": spec.range60_max_atr,
                "param_ema_slope_mode": spec.ema_slope_mode,
                "param_rr": spec.rr,
                "param_stop_buffer": spec.stop_buffer_atr,
                "param_max_hold": spec.max_hold_bars,
                "param_entry_mode": spec.entry_mode,
                "param_target_basis": spec.target_basis,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
        context = None

    return pd.DataFrame(rows)


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "Research_2015_2024"
    return "OOS_2025_2026"


def prepare_data() -> tuple[dict[str, pd.DataFrame], dict[str, list]]:
    data = load_h4_data()
    settings = timeframe_settings(TIMEFRAME)
    pivots = {
        symbol: build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
        for symbol, df in data.items()
    }
    return data, pivots


def run_spec(data: dict[str, pd.DataFrame], pivots: dict[str, list], spec: DeepSpec, symbols: Iterable[str]) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        if symbol not in data:
            continue
        trades = run_spec_for_symbol(data[symbol], pivots[symbol], symbol, spec)
        if not trades.empty:
            rows.append(trades)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def max_losing_streak(series: pd.Series) -> int:
    streak = 0
    best = 0
    for value in series:
        if value < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def summarize_trades(trades: pd.DataFrame, label: str | None = None) -> dict:
    if trades.empty:
        return {
            "label": label or "",
            "trades": 0,
            "win_rate": 0.0,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": 0.0,
            "median_r_after_cost": math.nan,
            "pf_after_cost": math.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "avg_mfe_r": math.nan,
            "avg_mae_r": math.nan,
            "avg_bars_held": math.nan,
            "oos_trades": 0,
            "oos_total_r": 0.0,
        }
    ordered = trades.sort_values("entry_time")
    r = ordered["r_after_cost"]
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    equity = r.cumsum()
    dd = (equity.cummax() - equity).max()
    oos = ordered[ordered["period"] == "OOS_2025_2026"]
    return {
        "label": label or str(ordered["strategy"].iloc[0]),
        "trades": int(len(ordered)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r_after_cost": float(r.sum()),
        "avg_r_after_cost": float(r.mean()),
        "median_r_after_cost": float(r.median()),
        "pf_after_cost": float(wins / losses) if losses > 0 else math.inf,
        "max_dd_r": float(dd),
        "max_losing_streak": int(max_losing_streak(r)),
        "avg_mfe_r": float(ordered["mfe_r"].mean()),
        "avg_mae_r": float(ordered["mae_r"].mean()),
        "avg_bars_held": float(ordered["bars_held"].mean()),
        "oos_trades": int(len(oos)),
        "oos_total_r": float(oos["r_after_cost"].sum()) if not oos.empty else 0.0,
    }


def summarize_by(trades: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    if trades.empty:
        return pd.DataFrame()
    for key, group in trades.groupby(cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(cols, key_tuple))
        row.update(summarize_trades(group, ""))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_r_after_cost", "trades"], ascending=[False, False])


def feature_detail_columns() -> list[str]:
    return [
        "symbol",
        "entry_time",
        "signal_time",
        "v_start_time",
        "v_low_time",
        "context_time",
        "drop_bars",
        "recovery_bars_signal",
        "drop_atr",
        "drop_speed",
        "recovery_speed_signal",
        "speed_ratio_signal",
        "shelf_bars",
        "shelf_range_atr",
        "shelf_hold_actual",
        "breakout_atr",
        "body_ratio",
        "close_location",
        "pre_adx14",
        "pre_ema50_slope_20_atr",
        "pre_close_ema50_stretch_atr",
        "pre_range60_atr",
        "signal_adx14",
        "signal_ema50_slope_20_atr",
        "signal_range60_atr",
        "entry",
        "stop",
        "target",
        "risk",
        "risk_atr_entry",
        "r_after_cost",
        "mfe_r",
        "mae_r",
        "mfe_atr_trade",
        "mae_atr_trade",
        "bars_held",
        "exit_time",
        "exit_reason",
    ]


def win_loss_compare(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = [
        "shelf_range_atr",
        "shelf_bars",
        "shelf_hold_actual",
        "breakout_atr",
        "body_ratio",
        "close_location",
        "pre_adx14",
        "pre_ema50_slope_20_atr",
        "pre_range60_atr",
        "drop_atr",
        "drop_speed",
        "recovery_speed_signal",
        "speed_ratio_signal",
        "mfe_r",
        "mae_r",
        "mfe_atr_trade",
        "mae_atr_trade",
        "bars_held",
        "risk_atr_entry",
    ]
    rows = []
    dist_rows = []
    work = trades.copy()
    work["side"] = np.where(work["r_after_cost"] > 0, "win", "loss")
    for feature in features:
        win = work.loc[work["side"] == "win", feature].dropna()
        loss = work.loc[work["side"] == "loss", feature].dropna()
        rows.append(
            {
                "feature": feature,
                "win_count": int(len(win)),
                "loss_count": int(len(loss)),
                "win_mean": float(win.mean()) if len(win) else math.nan,
                "loss_mean": float(loss.mean()) if len(loss) else math.nan,
                "win_median": float(win.median()) if len(win) else math.nan,
                "loss_median": float(loss.median()) if len(loss) else math.nan,
                "win_p25": float(win.quantile(0.25)) if len(win) else math.nan,
                "loss_p25": float(loss.quantile(0.25)) if len(loss) else math.nan,
                "win_p75": float(win.quantile(0.75)) if len(win) else math.nan,
                "loss_p75": float(loss.quantile(0.75)) if len(loss) else math.nan,
                "mean_diff_win_minus_loss": float(win.mean() - loss.mean()) if len(win) and len(loss) else math.nan,
            }
        )
        values = work[feature].dropna()
        if len(values) < 5:
            continue
        bins = np.unique(np.nanquantile(values, [0, 0.25, 0.5, 0.75, 1.0]))
        if len(bins) < 3:
            continue
        cut = pd.cut(work[feature], bins=bins, include_lowest=True, duplicates="drop")
        for bucket, group in work.groupby(cut, observed=True):
            dist_rows.append(
                {
                    "feature": feature,
                    "bucket": str(bucket),
                    **summarize_trades(group, ""),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(dist_rows)


def sensitivity_specs() -> list[DeepSpec]:
    specs: list[DeepSpec] = []
    for shelf_bars in [4, 5, 6, 7, 8]:
        for shelf_range in [1.2, 1.5, 1.8, 2.1, 2.4]:
            for hold in [0.4, 0.5, 0.6]:
                specs.append(
                    replace(
                        CURRENT_SPEC,
                        name=f"SHELFGRID_B{shelf_bars}_R{shelf_range}_H{hold}",
                        family="entry_shelf",
                        shelf_bars=shelf_bars,
                        max_shelf_range_atr=shelf_range,
                        shelf_hold_ratio=hold,
                    )
                )
    for buffer in [0.0, 0.03, 0.05, 0.08, 0.10]:
        for body in [0.30, 0.40, 0.50, 0.60]:
            for close_loc in [0.50, 0.60, 0.70]:
                specs.append(
                    replace(
                        CURRENT_SPEC,
                        name=f"BREAKGRID_BUF{buffer}_BODY{body}_CL{close_loc}",
                        family="breakout_quality",
                        breakout_buffer_atr=buffer,
                        min_body_ratio=body,
                        min_close_location=close_loc,
                    )
                )
    for adx_max in [22, 24, 26, 28, 30]:
        for range60 in [12, 14, 16, 18, 20]:
            for mode in ["none", "weak", "standard", "strict"]:
                specs.append(
                    replace(
                        CURRENT_SPEC,
                        name=f"ENVGRID_ADX{adx_max}_R{range60}_{mode}",
                        family="environment",
                        adx_max=adx_max,
                        range60_max_atr=range60,
                        ema_slope_mode=mode,
                    )
                )
    for rr in [1.2, 1.5, 1.8, 2.0, 2.5]:
        for stop_buffer in [0.10, 0.25, 0.40, 0.50]:
            for max_hold in [12, 18, 24, 36, 48]:
                specs.append(
                    replace(
                        CURRENT_SPEC,
                        name=f"EXITGRID_RR{rr}_SL{stop_buffer}_H{max_hold}",
                        family="exit",
                        rr=rr,
                        stop_buffer_atr=stop_buffer,
                        max_hold_bars=max_hold,
                    )
                )
    for entry_mode in ["next_open", "signal_close"]:
        for target_basis in ["signal", "entry"]:
            specs.append(
                replace(
                    CURRENT_SPEC,
                    name=f"ENTRYMODE_{entry_mode}_{target_basis}",
                    family="entry_mode",
                    entry_mode=entry_mode,
                    target_basis=target_basis,
                )
            )
    return specs


def run_sensitivity(data: dict[str, pd.DataFrame], pivots: dict[str, list]) -> pd.DataFrame:
    rows = []
    specs = sensitivity_specs()
    for n, spec in enumerate(specs, 1):
        trades = run_spec(data, pivots, spec, SELECTED_SYMBOLS)
        summary = summarize_trades(trades, spec.name)
        summary.update(
            {
                "family": spec.family,
                "shelf_bars": spec.shelf_bars,
                "shelf_range": spec.max_shelf_range_atr,
                "shelf_hold": spec.shelf_hold_ratio,
                "breakout_buffer": spec.breakout_buffer_atr,
                "body": spec.min_body_ratio,
                "close_location": spec.min_close_location,
                "adx_max": spec.adx_max,
                "range60_max": spec.range60_max_atr,
                "ema_slope_mode": spec.ema_slope_mode,
                "rr": spec.rr,
                "stop_buffer": spec.stop_buffer_atr,
                "max_hold": spec.max_hold_bars,
                "entry_mode": spec.entry_mode,
                "target_basis": spec.target_basis,
                "robust_min_trades": bool(summary["trades"] >= 20),
            }
        )
        rows.append(summary)
        if n % 50 == 0:
            print(f"sensitivity {n}/{len(specs)}")
    return pd.DataFrame(rows)


def add_regime_bins(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    out["adx_band"] = pd.cut(out["pre_adx14"], bins=[-math.inf, 18, 22, 26, 30, math.inf], labels=["<=18", "18-22", "22-26", "26-30", ">30"])
    out["drop_atr_band"] = pd.cut(out["drop_atr"], bins=[-math.inf, 3, 4, 5, 7, math.inf], labels=["<=3", "3-4", "4-5", "5-7", ">7"])
    out["shelf_range_band"] = pd.cut(out["shelf_range_atr"], bins=[-math.inf, 1.2, 1.5, 1.8, 2.1, math.inf], labels=["<=1.2", "1.2-1.5", "1.5-1.8", "1.8-2.1", ">2.1"])
    out["volatility_band"] = pd.cut(out["pre_range60_atr"], bins=[-math.inf, 10, 12, 14, 16, math.inf], labels=["<=10", "10-12", "12-14", "14-16", ">16"])
    out["speed_ratio_band"] = pd.cut(out["speed_ratio_signal"], bins=[-math.inf, 1.0, 1.2, 1.5, 2.0, math.inf], labels=["<=1.0", "1.0-1.2", "1.2-1.5", "1.5-2.0", ">2.0"])
    return out


def split_period(ts: pd.Timestamp) -> str:
    if pd.Timestamp("2018-01-01") <= ts <= pd.Timestamp("2021-12-31 23:59:59"):
        return "DEV_2018_2021"
    if pd.Timestamp("2022-01-01") <= ts <= pd.Timestamp("2023-12-31 23:59:59"):
        return "VALID_2022_2023"
    if pd.Timestamp("2024-01-01") <= ts <= pd.Timestamp("2026-12-31 23:59:59"):
        return "OOS_2024_2026"
    return "EARLY_2015_2017"


def fixed_walk_forward(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    years = sorted(trades["year"].dropna().astype(int).unique())
    for year in years:
        train = trades[(trades["year"] >= year - 3) & (trades["year"] <= year - 1)]
        test = trades[trades["year"] == year]
        row = {"test_year": year}
        row.update({f"train_{k}": v for k, v in summarize_trades(train, "").items() if k != "label"})
        row.update({f"test_{k}": v for k, v in summarize_trades(test, "").items() if k != "label"})
        rows.append(row)
    return pd.DataFrame(rows)


def parity_audit(reproduced: pd.DataFrame) -> pd.DataFrame:
    source = pd.read_csv(SOURCE_OUT_DIR / "trades.csv")
    source = source[
        (source["strategy"] == "SHELF6_PRECALM_BREAK_RR15")
        & (~source["symbol"].isin(EXCLUDED_FOR_CURRENT))
    ].copy()
    for col in ["entry_time", "signal_time", "exit_time"]:
        source[col] = pd.to_datetime(source[col])
        reproduced[col] = pd.to_datetime(reproduced[col])
    left_cols = ["symbol", "entry_time", "signal_time", "entry", "stop", "target", "r_after_cost"]
    merged = source[left_cols].merge(
        reproduced[left_cols],
        on=["symbol", "entry_time"],
        how="outer",
        suffixes=("_source", "_reproduced"),
        indicator=True,
    )
    rows = [
        {"check": "source_trades", "value": len(source)},
        {"check": "reproduced_trades", "value": len(reproduced)},
        {"check": "matched_entry_times", "value": int((merged["_merge"] == "both").sum())},
        {"check": "source_only", "value": int((merged["_merge"] == "left_only").sum())},
        {"check": "reproduced_only", "value": int((merged["_merge"] == "right_only").sum())},
    ]
    both = merged[merged["_merge"] == "both"].copy()
    if not both.empty:
        for col in ["entry", "stop", "target", "r_after_cost"]:
            rows.append(
                {
                    "check": f"max_abs_diff_{col}",
                    "value": float((both[f"{col}_source"] - both[f"{col}_reproduced"]).abs().max()),
                }
            )
    return pd.DataFrame(rows)


def write_markdown_outputs(
    current_all: pd.DataFrame,
    current_selected: pd.DataFrame,
    sensitivity: pd.DataFrame,
    compare: pd.DataFrame,
    robustness: dict[str, pd.DataFrame],
    parity: pd.DataFrame,
) -> None:
    selected_summary = pd.DataFrame([summarize_trades(current_selected, "Current selected")])
    all_summary = pd.DataFrame([summarize_trades(current_all, "Current all symbols")])
    sens_robust = sensitivity[sensitivity["trades"] >= 20].copy()
    top_by_family = (
        sens_robust.sort_values(["family", "pf_after_cost", "total_r_after_cost"], ascending=[True, False, False])
        .groupby("family")
        .head(8)
        .reset_index(drop=True)
    )
    report = [
        "# H4 V Initial Shelf Breakout 深掘り検証",
        "",
        "作成日: 2026-05-30",
        "",
        "## 結論",
        "",
        "現時点では **採用候補だが、本番ロット投入は保留**。",
        "",
        "理由は、構造は良いが、現行の初動寄りルールは 34 trades とまだ少なく、Research 期間より OOS に成績が寄っているため。過剰最適化というより、まだ標本数不足のリスクが大きい。",
        "",
        "ただし、Vを直接買うより、売り失敗後に上側で棚を作って再点火する局面を買う、という本質は検証上も残っている。",
        "",
        "## 再現確認",
        "",
        markdown_table(parity, 20),
        "",
        "## 現行成績",
        "",
        markdown_table(pd.concat([selected_summary, all_summary], ignore_index=True), 20),
        "",
        "## 監査メモ",
        "",
        "- confirmed pivot は `confirm_i <= signal_i` のものだけを active に入れており、pivot確定前の未来情報は使っていない。",
        "- 棚6本は `signal_i - shelf_bars : signal_i` で、シグナル足を含まない過去6本のみ。",
        "- Entryは次足始値。ただし36d90e6版はTPをシグナル終値基準で計算しており、次足始値にギャップがあると厳密な1.5Rではない。Pine本番版ではEntry基準TPを推奨。",
        "- PRECALMはV左肩起点時点のADX/EMA50傾き/EMA乖離/60本レンジ幅を見ている。これは過去情報でありlookaheadではない。",
        "- 仕様書のベースV条件は3.5ATR完全回復だが、現行コードの本命は2.8ATRかつ65%-125%回復のV候補。初動狙いとしては合理的だが、仕様書では明確に分けるべき。",
        "",
        "## 勝ち負け比較 上位差分",
        "",
        markdown_table(compare.sort_values("mean_diff_win_minus_loss", ascending=False).head(12), 20),
        "",
        "## パラメータ感度 上位候補",
        "",
        markdown_table(top_by_family, 40),
        "",
        "## ロバスト性",
        "",
        "### 通貨別",
        "",
        markdown_table(robustness["by_symbol"], 40),
        "",
        "### 開発/検証/OOS",
        "",
        markdown_table(robustness["by_split"], 20),
        "",
        "### 年別",
        "",
        markdown_table(robustness["by_year"], 40),
        "",
        "### ADX帯",
        "",
        markdown_table(robustness["by_adx"], 20),
        "",
        "### 棚幅帯",
        "",
        markdown_table(robustness["by_shelf_range"], 20),
        "",
        "## 本番判断",
        "",
        "採用区分: **保留寄りの採用候補**。",
        "",
        "運用するなら、通常リスクではなく 0.25R からフォワード記録。最低30件、できれば50件までTradingView/Python時刻一致を確認してから判断する。",
        "",
        "残す条件:",
        "",
        "- V後に棚を作る",
        "- 棚高値を終値で抜く",
        "- 棚安値がVの50%前後を維持",
        "- PRECALMで既存トレンド途中乗りを抑える",
        "",
        "削る/保留する条件:",
        "",
        "- 自作休眠ラインの同時ブレイクは件数不足",
        "- Donchian55は大きく伸びる前兆だがOOS件数不足",
        "- 過度に厳しい棚幅・終値位置条件は件数が細りすぎる",
        "",
        "追加すべき検証:",
        "",
        "- Entry基準TPでPine/Pythonを統一",
        "- 固定1.5Rと半分利確+トレーリングの比較",
        "- 2026年以降のフォワード記録",
        "- TradingViewのシグナル時刻とPython `current_trades_detail.csv` の一致確認",
        "",
    ]
    (OUT_DIR / "deep_dive_report_ja.md").write_text("\n".join(report), encoding="utf-8")

    final_spec = [
        "# H4 V Initial Shelf Breakout 最終仕様書",
        "",
        "## 判定",
        "",
        "本番運用候補。ただし通常ロットはまだ早い。Pine照合後、0.25Rからフォワード検証。",
        "",
        "## 推奨仕様",
        "",
        "- 時間足: H4",
        "- 対象: USDJPY, EURJPY, GBPJPY, AUDJPY",
        "- 除外: XAUUSD, CHFJPY, SILVER",
        "- 方向: ロングのみ",
        "- V条件: confirmed pivot high -> confirmed pivot low",
        "- pivot width: 3",
        "- 下落幅 >= 2.8ATR",
        "- 下落速度 >= 0.25ATR/本",
        "- 回復率: 65%から125%",
        "- 回復速度 >= 下落速度",
        "- V谷後、V谷 - 0.10ATRを下抜けない",
        "- V前環境: ADX14 <= 26, EMA50傾き <= 1.2ATR/20本, Close-EMA50 <= 3ATR, 60本レンジ幅 <= 16ATR",
        "- 棚: V候補成立後36本以内、直近6本",
        "- 棚幅 <= 1.8ATR",
        "- 棚安値 >= V谷 + 下落幅 x 0.50 - 0.05ATR",
        "- Entry signal: close > 棚高値 + 0.05ATR, 実体 >= 40%, 終値位置 >= 60%",
        "- Entry: 次足始値",
        "- SL: 棚安値 - 0.25ATR",
        "- TP: Entry基準 1.5R を推奨。36d90e6再現ではSignal close基準。",
        "- 最大保有: 120本を基準。短期最大保有は別途exit研究。",
        "- 同一通貨で1ポジションのみ",
        "",
        "## Pine実装注意",
        "",
        "- pivotはconfirmedのみ。`ta.pivothigh/low(left, right)` の検出足は `bar_index - right`、利用可能になるのは現在足。",
        "- 棚はシグナル足を含めず `high[1]` から過去6本で計算。",
        "- strategy entryはシグナル足で注文、約定は次足始値想定。",
        "- TPはEntry約定価格が確定してから計算する。",
        "- Python照合用に signal_time, v_start_time, v_low_time, shelf_high, shelf_low, stop をラベル/テーブル表示する。",
    ]
    (OUT_DIR / "final_spec_ja.md").write_text("\n".join(final_spec), encoding="utf-8")

    checklist = [
        "# TradingView 照合チェックリスト",
        "",
        "1. H4チャートで実行する。",
        "2. Pineの対象通貨をPythonの `current_trades_detail.csv` と同じにする。",
        "3. 年末年始除外をPythonと同じにする。",
        "4. まずstrategy成績ではなく、signal_time一致だけを見る。",
        "5. `current_trades_detail.csv` の各行について、symbol / signal_time / entry_timeを照合する。",
        "6. 一致後、shelf_high / shelf_low / stop / target / entry を照合する。",
        "7. targetはPython再現用ならsignal close基準、本番用ならentry基準。どちらで比較しているか明記する。",
        "8. TradingViewのデータ提供元差で1-2本ずれる場合は、その通貨を別管理にする。",
        "9. シグナル一致率が100%になるまでPFや勝率は採用判断に使わない。",
    ]
    (OUT_DIR / "tradingview_parity_checklist.md").write_text("\n".join(checklist), encoding="utf-8")

    logic = [
        "# Pine Strategy化用 完全ロジック仕様",
        "",
        "## State",
        "",
        "- `active`: V候補監視中",
        "- `vStartPrice`, `vLowPrice`, `vStartBar`, `vLowBar`",
        "- `contextBar`: 回復率条件が最初に成立した足",
        "- `usedPair`: 同じVペアの重複使用を禁止",
        "- `inTrade`: `strategy.position_size != 0`",
        "",
        "## Signal Flow",
        "",
        "1. confirmed pivot high/lowを交互に管理する。",
        "2. H -> L のペアで急落条件を満たすか見る。",
        "3. 回復率65%-125%、速度条件、V谷再更新なしを確認する。",
        "4. V左肩時点のPRECALM条件を確認する。",
        "5. context成立後、最大36本だけ棚ブレイクを待つ。",
        "6. 直近6本の棚を、シグナル足を含めず計算する。",
        "7. closeが棚高値+0.05ATRを上抜け、実体/終値位置条件を満たしたらロング。",
        "8. SLは棚安値-0.25ATR。",
        "9. TPは約定後にEntry基準1.5Rで設定。",
        "10. ポジション保有中は新しいV候補もシグナルも無視する。",
    ]
    (OUT_DIR / "pine_strategy_logic_spec.md").write_text("\n".join(logic), encoding="utf-8")


def main() -> None:
    data, pivots = prepare_data()

    current_all = run_spec(data, pivots, CURRENT_SPEC, SYMBOLS)
    current_selected = current_all[~current_all["symbol"].isin(EXCLUDED_FOR_CURRENT)].copy()
    current_selected = current_selected.sort_values(["entry_time", "symbol"]).reset_index(drop=True)

    parity = parity_audit(current_selected.copy())
    current_all.to_csv(OUT_DIR / "current_trades_all_symbols.csv", index=False)
    current_selected[feature_detail_columns()].to_csv(OUT_DIR / "current_trades_detail.csv", index=False)
    parity.to_csv(OUT_DIR / "reproduction_audit.csv", index=False)

    compare, distribution = win_loss_compare(current_selected)
    compare.to_csv(OUT_DIR / "win_loss_compare.csv", index=False)
    distribution.to_csv(OUT_DIR / "win_loss_distribution_bins.csv", index=False)

    print("running sensitivity blocks...")
    sensitivity = run_sensitivity(data, pivots)
    sensitivity.to_csv(OUT_DIR / "parameter_sensitivity_all.csv", index=False)
    for family, group in sensitivity.groupby("family"):
        group.to_csv(OUT_DIR / f"parameter_sensitivity_{family}.csv", index=False)

    reg = add_regime_bins(current_selected)
    reg["split"] = reg["entry_time"].apply(lambda x: split_period(pd.Timestamp(x)))
    robustness = {
        "by_symbol": summarize_by(reg, ["symbol"]),
        "by_year": summarize_by(reg, ["year"]),
        "by_month": summarize_by(reg, ["month"]),
        "by_split": summarize_by(reg, ["split"]),
        "by_adx": summarize_by(reg, ["adx_band"]),
        "by_volatility": summarize_by(reg, ["volatility_band"]),
        "by_drop_atr": summarize_by(reg, ["drop_atr_band"]),
        "by_shelf_range": summarize_by(reg, ["shelf_range_band"]),
        "by_speed_ratio": summarize_by(reg, ["speed_ratio_band"]),
    }
    for name, table in robustness.items():
        table.to_csv(OUT_DIR / f"robustness_{name}.csv", index=False)
    fixed_walk_forward(reg).to_csv(OUT_DIR / "walk_forward_fixed_rule.csv", index=False)

    candidate_summary = pd.DataFrame(
        [
            summarize_trades(current_selected, "current_selected"),
            summarize_trades(current_all, "current_all_symbols"),
        ]
    )
    candidate_summary.to_csv(OUT_DIR / "candidate_summary.csv", index=False)

    write_markdown_outputs(current_all, current_selected, sensitivity, compare, robustness, parity)
    print(f"Report: {OUT_DIR / 'deep_dive_report_ja.md'}")
    print(candidate_summary.to_string(index=False))


if __name__ == "__main__":
    main()

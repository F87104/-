#!/usr/bin/env python3
"""
H4 low-break lookback and exit study.

Research questions:
- Is a longer low-break lookback, such as 3 months or 6 months, stronger
  than the current 1 month definition?
- If price often moves in favor and then returns, which practical take-profit
  or protection rule captures the move better than a fixed 2R target?
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    add_indicators,
    direction_cost_r,
    holiday_market,
    load_instrument,
    markdown_table,
    resample_ohlc,
)
from run_indicator_compatibility_search import add_extended_features
from run_monthly_low_rebreak_short import LowBreakSpec, first_low_breaks, low_break_signal


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_28" / "low_break_lookback_exit_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
MAX_HOLD_BARS = 180
H4_BARS_PER_MONTH = 120


@dataclass(frozen=True)
class ExitSpec:
    name: str
    target_rr: float = 2.0
    partial_1r: bool = False
    be_after_1r: bool = False
    trail_atr_after_1r: float | None = None
    no_progress_bars: int | None = None
    max_hold_bars: int = MAX_HOLD_BARS


@dataclass(frozen=True)
class FilterSpec:
    name: str
    notes: str
    fn: Callable[[pd.DataFrame], pd.Series]


LOOKBACK_BARS = [60, 90, 120, 180, 240, 360, 480, 720]
TRIGGER_MODES = ["stagnation", "rebreak", "either"]

EXIT_SPECS = [
    ExitSpec("fixed_1R", target_rr=1.0),
    ExitSpec("fixed_1_25R", target_rr=1.25),
    ExitSpec("fixed_1_5R", target_rr=1.5),
    ExitSpec("fixed_2R", target_rr=2.0),
    ExitSpec("BE_after_1R_to_2R", target_rr=2.0, be_after_1r=True),
    ExitSpec("half_1R_BE_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True),
    ExitSpec("half_1R_trail1ATR_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True, trail_atr_after_1r=1.0),
    ExitSpec("fixed_1_5R_no_progress12", target_rr=1.5, no_progress_bars=12),
    ExitSpec("fixed_2R_no_progress12", target_rr=2.0, no_progress_bars=12),
    ExitSpec("fixed_2R_max48", target_rr=2.0, max_hold_bars=48),
]


def lookback_label(bars: int) -> str:
    months = bars / H4_BARS_PER_MONTH
    if months.is_integer():
        return f"{int(months)}m"
    return f"{months:.2g}m"


def make_spec(bars: int, trigger_mode: str) -> LowBreakSpec:
    suffix = {"stagnation": "STAG", "rebreak": "REBREAK", "either": "EITHER"}[trigger_mode]
    return LowBreakSpec(
        name=f"L{bars:03d}_{suffix}",
        lookback_bars=bars,
        trigger_mode=trigger_mode,
        pullback_min_atr=0.75,
    )


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    curve = r.astype(float).cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(r: pd.Series) -> int:
    cur = 0
    best = 0
    for value in r.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def metrics(df: pd.DataFrame, r_col: str) -> dict[str, float | int]:
    r = df[r_col].astype(float) if not df.empty and r_col in df.columns else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def classify_period(ts: pd.Timestamp) -> str:
    if ts.year <= 2020:
        return "train_2015_2020"
    if ts.year <= 2024:
        return "test_2021_2024"
    return "oos_2025_2026"


def add_period_metrics(row: dict, prefix: str, sample: pd.DataFrame, r_col: str) -> None:
    row.update({f"{prefix}_{key}": value for key, value in metrics(sample, r_col).items()})


def excursion_metrics(df: pd.DataFrame, r_col: str) -> dict[str, float]:
    if df.empty or "mfe_r_model" not in df.columns:
        return {
            "avg_mfe_r": 0.0,
            "hit_1r_rate": 0.0,
            "hit_1_5r_rate": 0.0,
            "hit_2r_rate": 0.0,
            "giveback_1r_to_loss_rate": 0.0,
            "giveback_1_5r_to_loss_rate": 0.0,
        }
    mfe = df["mfe_r_model"].astype(float)
    r = df[r_col].astype(float)
    hit_1 = mfe.ge(1.0)
    hit_15 = mfe.ge(1.5)
    return {
        "avg_mfe_r": float(mfe.mean()) if len(mfe) else 0.0,
        "hit_1r_rate": float(hit_1.mean() * 100) if len(mfe) else 0.0,
        "hit_1_5r_rate": float(hit_15.mean() * 100) if len(mfe) else 0.0,
        "hit_2r_rate": float(mfe.ge(2.0).mean() * 100) if len(mfe) else 0.0,
        "giveback_1r_to_loss_rate": float((hit_1 & r.le(0)).mean() * 100) if len(mfe) else 0.0,
        "giveback_1_5r_to_loss_rate": float((hit_15 & r.le(0)).mean() * 100) if len(mfe) else 0.0,
    }


def count_touch_clusters(local_indices: np.ndarray, min_gap: int = 3) -> int:
    if len(local_indices) == 0:
        return 0
    clusters = 1
    prev = int(local_indices[0])
    for idx in local_indices[1:]:
        cur = int(idx)
        if cur - prev > min_gap:
            clusters += 1
        prev = cur
    return clusters


def support_age_bucket(age_bars: int) -> str:
    if age_bars <= 24:
        return "00_<=24bars"
    if age_bars <= 59:
        return "01_25-59bars"
    if age_bars <= 119:
        return "02_60-119bars"
    if age_bars <= 239:
        return "03_120-239bars"
    return "04_>=240bars"


def pre_break_context(df: pd.DataFrame, break_i: int, lookback_bars: int, prior_low: float) -> dict[str, float | int | str]:
    atr_break = float(df["atr"].iloc[break_i])
    if not math.isfinite(atr_break) or atr_break <= 0:
        atr_break = np.nan

    start_i = max(0, break_i - lookback_bars)
    win = df.iloc[start_i:break_i]
    if win.empty or not math.isfinite(atr_break):
        return {
            "support_age_bars": 0,
            "support_age_months": 0.0,
            "support_age_ratio": 0.0,
            "support_touch_bars_0_5atr": 0,
            "support_touch_clusters_0_5atr": 0,
            "pre_break_range_width_atr": np.nan,
            "pre_break_net_move_atr": np.nan,
            "pre_break_efficiency": np.nan,
            "pre_break_slope_atr_per_100": np.nan,
            "pre_break_regime": "unknown",
            "support_age_bucket": "unknown",
        }

    lows = win["low"].to_numpy(dtype=float)
    if np.all(np.isnan(lows)):
        low_local_i = 0
    else:
        low_local_i = int(np.nanargmin(lows))
    low_global_i = start_i + low_local_i
    age = int(break_i - low_global_i)
    age_ratio = age / lookback_bars if lookback_bars > 0 else 0.0

    near_support = (win["low"] <= prior_low + atr_break * 0.5).fillna(False).to_numpy()
    near_indices = np.flatnonzero(near_support)
    touch_clusters = count_touch_clusters(near_indices)

    closes = win["close"].astype(float)
    pre_range_width_atr = float((win["high"].max() - win["low"].min()) / atr_break)
    pre_net_move_atr = float((closes.iloc[-1] - closes.iloc[0]) / atr_break) if len(closes) >= 2 else 0.0
    total_path = float(closes.diff().abs().sum())
    net_abs = float(abs(closes.iloc[-1] - closes.iloc[0])) if len(closes) >= 2 else 0.0
    efficiency = net_abs / total_path if total_path > 0 else 0.0
    if len(closes) >= 8:
        x = np.arange(len(closes), dtype=float)
        slope = float(np.polyfit(x, closes.to_numpy(dtype=float), 1)[0])
        slope_atr_per_100 = slope * 100.0 / atr_break
    else:
        slope_atr_per_100 = 0.0

    long_support = age >= max(30, int(lookback_bars * 0.35))
    enough_touches = touch_clusters >= 2
    sideways = efficiency <= 0.35 and abs(slope_atr_per_100) <= 1.5
    trending_down = slope_atr_per_100 <= -1.5 and efficiency >= 0.30
    fresh_low = age <= min(24, max(8, int(lookback_bars * 0.20)))

    if long_support and enough_touches and sideways:
        regime = "range_support_break"
    elif fresh_low or trending_down:
        regime = "trend_continuation_break"
    else:
        regime = "mixed_or_wide_range"

    return {
        "support_age_bars": age,
        "support_age_months": age / H4_BARS_PER_MONTH,
        "support_age_ratio": age_ratio,
        "support_touch_bars_0_5atr": int(near_support.sum()),
        "support_touch_clusters_0_5atr": int(touch_clusters),
        "pre_break_range_width_atr": pre_range_width_atr,
        "pre_break_net_move_atr": pre_net_move_atr,
        "pre_break_efficiency": float(efficiency),
        "pre_break_slope_atr_per_100": float(slope_atr_per_100),
        "pre_break_regime": regime,
        "support_age_bucket": support_age_bucket(age),
    }


def filter_specs() -> list[FilterSpec]:
    return [
        FilterSpec("ALL", "全候補", lambda d: pd.Series(True, index=d.index)),
        FilterSpec(
            "ADX30_RISK_LE1_5_BBW3_8",
            "ADX>=30 + risk<=1.5ATR + BB幅3-8ATR",
            lambda d: d["adx14"].ge(30) & d["risk_atr_at_signal"].le(1.5) & d["bb_width_atr"].between(3.0, 8.0),
        ),
        FilterSpec(
            "ADX30_RISK_LE2_BBW3_8",
            "ADX>=30 + risk<=2ATR + BB幅3-8ATR",
            lambda d: d["adx14"].ge(30) & d["risk_atr_at_signal"].le(2.0) & d["bb_width_atr"].between(3.0, 8.0),
        ),
        FilterSpec(
            "GBP_ADX25_RISK_LE2_5_BBW3_8",
            "GBPJPY + ADX>=25 + risk<=2.5ATR + BB幅3-8ATR",
            lambda d: d["symbol"].eq("GBPJPY") & d["adx14"].ge(25) & d["risk_atr_at_signal"].le(2.5) & d["bb_width_atr"].between(3.0, 8.0),
        ),
        FilterSpec(
            "NO_XAU_ADX30_RISK_LE1_5_BBW3_8",
            "XAUUSD除外 + ADX>=30 + risk<=1.5ATR + BB幅3-8ATR",
            lambda d: d["symbol"].ne("XAUUSD") & d["adx14"].ge(30) & d["risk_atr_at_signal"].le(1.5) & d["bb_width_atr"].between(3.0, 8.0),
        ),
    ]


def _weighted_r(symbol: str, entry: float, exit_price: float, risk: float, weight: float) -> tuple[float, float]:
    clean, after = direction_cost_r(symbol, "short", entry, exit_price, risk)
    return clean * weight, after * weight


def simulate_exit(df: pd.DataFrame, symbol: str, entry_i: int, stop: float, spec: ExitSpec) -> dict | None:
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    risk = stop - entry
    if risk <= 0:
        return None

    target = entry - risk * spec.target_rr
    tp1 = entry - risk
    max_i = min(len(df) - 1, entry_i + spec.max_hold_bars)

    realized_clean = 0.0
    realized_after = 0.0
    remaining = 1.0
    current_stop = stop
    tp1_hit = False
    tp1_bar: int | None = None
    mfe = 0.0
    mae = 0.0
    exit_i = max_i
    exit_price = float(df["close"].iloc[max_i])
    reason = "max_hold"

    for j in range(entry_i, max_i + 1):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        close = float(df["close"].iloc[j])
        mfe = max(mfe, (entry - lo) / risk)
        mae = max(mae, (hi - entry) / risk)

        if tp1_hit and spec.trail_atr_after_1r is not None and j > (tp1_bar or entry_i):
            prev = df.iloc[j - 1]
            prev_atr = float(prev["atr"])
            if math.isfinite(prev_atr) and prev_atr > 0:
                trail_stop = float(prev["high"]) + prev_atr * spec.trail_atr_after_1r
                current_stop = min(current_stop, trail_stop)

        hit_sl = hi >= current_stop
        hit_tp = lo <= target

        if hit_sl:
            clean, after = _weighted_r(symbol, entry, current_stop, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = current_stop
            reason = "SL_or_BE" if current_stop <= entry else "SL"
            remaining = 0.0
            break

        if hit_tp:
            if spec.partial_1r and not tp1_hit:
                clean, after = _weighted_r(symbol, entry, tp1, risk, 0.5)
                realized_clean += clean
                realized_after += after
                remaining = 0.5
            clean, after = _weighted_r(symbol, entry, target, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = target
            reason = "TP"
            remaining = 0.0
            break

        if not tp1_hit and lo <= tp1:
            tp1_hit = True
            tp1_bar = j
            if spec.partial_1r:
                clean, after = _weighted_r(symbol, entry, tp1, risk, 0.5)
                realized_clean += clean
                realized_after += after
                remaining = 0.5
            if spec.be_after_1r:
                current_stop = min(current_stop, entry)
                if hi >= current_stop:
                    clean, after = _weighted_r(symbol, entry, current_stop, risk, remaining)
                    realized_clean += clean
                    realized_after += after
                    exit_i = j
                    exit_price = current_stop
                    reason = "TP1_then_BE_same_bar"
                    remaining = 0.0
                    break

        if spec.no_progress_bars is not None and not tp1_hit and (j - entry_i + 1) >= spec.no_progress_bars:
            clean, after = _weighted_r(symbol, entry, close, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = close
            reason = "no_progress_exit"
            remaining = 0.0
            break

    if remaining > 0:
        clean, after = _weighted_r(symbol, entry, exit_price, risk, remaining)
        realized_clean += clean
        realized_after += after

    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target_model": target,
        "exit_time_model": df.index[exit_i],
        "exit_model": exit_price,
        "exit_reason_model": reason,
        "bars_held_model": int(exit_i - entry_i),
        "risk": risk,
        "r_clean_model": realized_clean,
        "r_after_cost_model": realized_after,
        "mfe_r_model": float(mfe),
        "mae_r_model": float(mae),
    }


def extract_signals(df: pd.DataFrame, symbol: str, spec: LowBreakSpec) -> pd.DataFrame:
    breaks = first_low_breaks(df, spec)
    rows: list[dict] = []
    in_pos_until = -1
    used_breaks: set[str] = set()

    for break_i in np.flatnonzero(breaks.to_numpy()):
        if break_i <= in_pos_until or break_i >= len(df) - 2:
            continue
        ts = df.index[int(break_i)]
        if ts < START or ts > END or holiday_market(ts):
            continue

        sig = low_break_signal(df, int(break_i), spec)
        if sig is None or sig["break_key"] in used_breaks:
            continue

        entry_i = int(sig["trigger_i"]) + 1
        base_exit = simulate_exit(df, symbol, entry_i, float(sig["stop"]), ExitSpec("fixed_2R", target_rr=2.0))
        if base_exit is None:
            continue

        feature_cols = [
            "open",
            "high",
            "low",
            "close",
            "atr",
            "body_ratio",
            "ema20",
            "ema50",
            "ema200",
            "ema20_slope_10_atr",
            "rsi14",
            "adx14",
            "bb_width_atr",
            "bb_pos",
            "atr_ratio_50",
            "atr_pctile_252",
            "close_location",
            "range5_atr",
            "macd",
            "macd_signal",
            "macd_hist",
            "macd_hist_slope3",
        ]
        features = {col: df[col].iloc[int(sig["trigger_i"])] for col in feature_cols if col in df.columns}
        used_breaks.add(sig["break_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "trigger_mode": spec.trigger_mode,
                "lookback_bars": spec.lookback_bars,
                "lookback_months": spec.lookback_bars / H4_BARS_PER_MONTH,
                "lookback_label": lookback_label(spec.lookback_bars),
                "signal_time": df.index[int(sig["trigger_i"])],
                "entry_i": entry_i,
                **pre_break_context(df, int(break_i), spec.lookback_bars, float(sig["prior_low"])),
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "break_key", "lookback_bars"}},
                **features,
                "entry_time": base_exit["entry_time"],
                "entry": base_exit["entry"],
                "stop": base_exit["stop"],
                "base_target_2r": base_exit["target_model"],
                "base_exit_time": base_exit["exit_time_model"],
                "base_exit": base_exit["exit_model"],
                "base_exit_reason": base_exit["exit_reason_model"],
                "base_bars_held": base_exit["bars_held_model"],
                "risk": base_exit["risk"],
                "base_r_clean": base_exit["r_clean_model"],
                "base_r_after_cost": base_exit["r_after_cost_model"],
                "base_mfe_r": base_exit["mfe_r_model"],
                "base_mae_r": base_exit["mae_r_model"],
            }
        )
        in_pos_until = int(df.index.get_loc(base_exit["exit_time_model"]))

    return pd.DataFrame(rows)


def build_signals() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    coverage = []
    rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        frames[symbol] = df
        for bars in LOOKBACK_BARS:
            for trigger_mode in TRIGGER_MODES:
                sample = extract_signals(df, symbol, make_spec(bars, trigger_mode))
                if not sample.empty:
                    rows.append(sample)

    signals = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not signals.empty:
        for col in ["signal_time", "entry_time", "base_exit_time"]:
            signals[col] = pd.to_datetime(signals[col])
        signals["period"] = signals["entry_time"].map(classify_period)
        signals["year"] = signals["entry_time"].dt.year.astype(str)
        signals = signals.sort_values(["entry_time", "symbol", "strategy"]).reset_index(drop=True)
    return signals, frames, pd.DataFrame(coverage)


def build_exit_models(signals: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for _, row in signals.iterrows():
        symbol = str(row["symbol"])
        df = frames[symbol]
        entry_i = int(row["entry_i"])
        stop = float(row["stop"])
        base = row.to_dict()
        for spec in EXIT_SPECS:
            out = simulate_exit(df, symbol, entry_i, stop, spec)
            if out is None:
                continue
            rows.append({**base, "exit_variant": spec.name, **out})
    exits = pd.DataFrame(rows)
    if not exits.empty:
        for col in ["signal_time", "entry_time", "base_exit_time", "exit_time_model"]:
            exits[col] = pd.to_datetime(exits[col])
        exits["period"] = exits["entry_time"].map(classify_period)
        exits["year"] = exits["entry_time"].dt.year.astype(str)
    return exits


def summarize_groups(df: pd.DataFrame, r_col: str, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    filters = filter_specs()
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_cols, keys))
        for filt in filters:
            mask = filt.fn(group).fillna(False)
            sample = group[mask].copy()
            row = {**base, "filter": filt.name, "filter_notes": filt.notes}
            add_period_metrics(row, "all", sample, r_col)
            add_period_metrics(row, "train", sample[sample["period"].eq("train_2015_2020")], r_col)
            add_period_metrics(row, "test", sample[sample["period"].eq("test_2021_2024")], r_col)
            add_period_metrics(row, "oos", sample[sample["period"].eq("oos_2025_2026")], r_col)
            row.update(excursion_metrics(sample, r_col))
            row["score"] = (
                row["all_total_r"]
                + row["test_total_r"] * 1.2
                + row["all_avg_r"] * 4
                + min(row["all_pf"] if math.isfinite(row["all_pf"]) else 5, 5)
                - row["all_max_dd_r"] * 0.25
                - (3.0 if row["all_trades"] < 15 else 0.0)
                - (2.0 if row["test_total_r"] < 0 else 0.0)
                - (1.0 if row["oos_total_r"] < 0 else 0.0)
            )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["score", "all_total_r"], ascending=False).reset_index(drop=True)


def lookback_pivot_tables(exits: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fixed = exits[exits["exit_variant"].eq("fixed_2R")].copy()
    strength = summarize_groups(fixed, "r_after_cost_model", ["lookback_bars", "lookback_label", "trigger_mode"])
    exit_summary = summarize_groups(exits, "r_after_cost_model", ["lookback_bars", "lookback_label", "trigger_mode", "exit_variant"])
    regime_summary = summarize_groups(fixed, "r_after_cost_model", ["pre_break_regime", "trigger_mode"])
    support_age_summary = summarize_groups(fixed, "r_after_cost_model", ["support_age_bucket", "trigger_mode"])
    return fixed, strength, exit_summary, regime_summary, support_age_summary


def write_report(
    coverage: pd.DataFrame,
    signals: pd.DataFrame,
    strength: pd.DataFrame,
    exit_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
    support_age_summary: pd.DataFrame,
) -> None:
    primary_filter = "ADX30_RISK_LE1_5_BBW3_8"
    primary_strength = strength[
        strength["filter"].eq(primary_filter) & strength["trigger_mode"].eq("stagnation")
    ].sort_values("lookback_bars")

    broad_strength = strength[
        strength["filter"].eq("ALL") & strength["trigger_mode"].eq("stagnation")
    ].sort_values("lookback_bars")

    primary_exit = exit_summary[
        exit_summary["filter"].eq(primary_filter) & exit_summary["trigger_mode"].eq("stagnation")
    ].sort_values(["score", "all_total_r"], ascending=False)

    top_exit_by_lookback = (
        primary_exit.sort_values(["lookback_bars", "score"], ascending=[True, False])
        .groupby("lookback_bars", as_index=False)
        .head(3)
        .sort_values(["lookback_bars", "score"], ascending=[True, False])
    )
    primary_regime = regime_summary[
        regime_summary["filter"].eq(primary_filter) & regime_summary["trigger_mode"].eq("stagnation")
    ].sort_values(["score", "all_total_r"], ascending=False)
    primary_support_age = support_age_summary[
        support_age_summary["filter"].eq(primary_filter) & support_age_summary["trigger_mode"].eq("stagnation")
    ].sort_values("support_age_bucket")

    strength_cols = [
        "lookback_label",
        "lookback_bars",
        "trigger_mode",
        "filter",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_total_r",
        "oos_total_r",
        "avg_mfe_r",
        "hit_1r_rate",
        "hit_1_5r_rate",
        "hit_2r_rate",
        "giveback_1r_to_loss_rate",
    ]
    exit_cols = [
        "lookback_label",
        "lookback_bars",
        "exit_variant",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_total_r",
        "oos_total_r",
        "score",
    ]

    lines = [
        "# H4 安値更新期間と利益確定基準の研究",
        "",
        "Status: 検証途中。ショート側手法の本番採用前リサーチ。",
        "",
        "## 検証した問い",
        "",
        "- 1ヶ月安値更新だけでなく、2ヶ月、3ヶ月、4ヶ月、6ヶ月の安値更新はどの程度強いか。",
        "- 長い安値更新が、トレンド継続なのか、長いレンジのサポート割れなのかを分ける。",
        "- 安値更新後に一度伸びても戻ってしまう問題に対して、固定2R以外の利確・保護ルールが有効か。",
        "",
        "## 検証定義",
        "",
        "- 時間足: H4",
        "- lookback: 60/90/120/180/240/360/480/720本。約0.5ヶ月から6ヶ月。",
        "- トリガー: 安値停滞下抜け、戻り後の再下落、またはどちらか。",
        "- レンジ判定: サポート安値の保持期間、0.5ATR以内の接触回数、事前値動きの効率性、傾きで分類。",
        "- `range_support_break`: 長く保持された安値に複数回接触し、事前の方向効率と傾きが低いもの。",
        "- `trend_continuation_break`: 直近で新安値を更新し続けている、または事前の下向き傾きと方向効率が強いもの。",
        "- 主フィルタ: `ADX>=30 + risk<=1.5ATR + BB幅3-8ATR`。",
        "- ベース出口: 固定2R。追加で1R/1.25R/1.5R/建値/半分利確/トレール/時間撤退を比較。",
        "",
        "## データ範囲",
        "",
        markdown_table(coverage, 20),
        "",
        "## 主フィルタ + 安値停滞下抜け: lookback別",
        "",
        markdown_table(primary_strength[strength_cols], 80) if not primary_strength.empty else "_No rows._",
        "",
        "## 全候補 + 安値停滞下抜け: lookback別",
        "",
        markdown_table(broad_strength[strength_cols], 80) if not broad_strength.empty else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: 事前状態別",
        "",
        markdown_table(primary_regime[[c for c in ["pre_break_regime", *strength_cols[3:], "score"] if c in primary_regime.columns]], 60)
        if not primary_regime.empty
        else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: サポート保持期間別",
        "",
        markdown_table(primary_support_age[[c for c in ["support_age_bucket", *strength_cols[3:], "score"] if c in primary_support_age.columns]], 60)
        if not primary_support_age.empty
        else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: 利確/撤退 上位",
        "",
        markdown_table(primary_exit[exit_cols].head(40), 60) if not primary_exit.empty else "_No rows._",
        "",
        "## lookback別 利確/撤退 上位3",
        "",
        markdown_table(top_exit_by_lookback[exit_cols], 80) if not top_exit_by_lookback.empty else "_No rows._",
        "",
        "## 全体上位",
        "",
        markdown_table(strength[strength_cols + ["score"]].head(50), 80) if not strength.empty else "_No rows._",
        "",
        "## 暫定メモ",
        "",
        "- `hit_1r_rate` や `giveback_1r_to_loss_rate` は、伸びたのに戻る問題を見るための列。",
        "- 期間が長いほど強いとは限らない。長い期間には、下落トレンド継続とレンジサポート割れが混ざる。",
        "- lookbackの長さだけでなく、サポート保持期間と接触回数を必ず見る。",
        "- まずは安値停滞下抜けを中心に、1Rから1.5Rで守る出口と固定2Rを比較する。",
        "",
        "## 出力CSV",
        "",
        "- `signals.csv`",
        "- `exit_model_trades.csv`",
        "- `lookback_strength.csv`",
        "- `exit_summary.csv`",
        "- `regime_summary.csv`",
        "- `support_age_summary.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    signals, frames, coverage = build_signals()
    signals.to_csv(OUT_DIR / "signals.csv", index=False)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if signals.empty:
        (OUT_DIR / "report_ja.md").write_text("# H4 安値更新期間と利益確定基準の研究\n\nNo signals.", encoding="utf-8")
        print("No signals")
        return

    exits = build_exit_models(signals, frames)
    exits.to_csv(OUT_DIR / "exit_model_trades.csv", index=False)

    _, strength, exit_summary, regime_summary, support_age_summary = lookback_pivot_tables(exits)
    strength.to_csv(OUT_DIR / "lookback_strength.csv", index=False)
    exit_summary.to_csv(OUT_DIR / "exit_summary.csv", index=False)
    regime_summary.to_csv(OUT_DIR / "regime_summary.csv", index=False)
    support_age_summary.to_csv(OUT_DIR / "support_age_summary.csv", index=False)

    write_report(coverage, signals, strength, exit_summary, regime_summary, support_age_summary)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(
        strength[
            strength["filter"].eq("ADX30_RISK_LE1_5_BBW3_8")
            & strength["trigger_mode"].eq("stagnation")
        ][
            [
                "lookback_label",
                "lookback_bars",
                "all_trades",
                "all_total_r",
                "all_avg_r",
                "all_pf",
                "test_total_r",
                "oos_total_r",
                "hit_1r_rate",
                "giveback_1r_to_loss_rate",
            ]
        ]
        .sort_values("lookback_bars")
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Study: H4 V as a catalyst, not as the entry itself.

The current Clean H4 V Reclaim buys the V reclaim directly. The user's chart
review suggests that this is not always the "strong" place. This study tests a
different idea:

    A sharp H4 V is only context. Entry happens later, when price stays in the
    upper side after the V and breaks a tight shelf / range high.

The goal is to find V patterns that precede expansion or trend kickoff.
"""

from __future__ import annotations

import math
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    Pivot,
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    simulate_trade,
    summarize,
    timeframe_settings,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_30" / "h4_v_kickoff_catalyst"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
TIMEFRAME = "H4"


@dataclass(frozen=True)
class KickoffSpec:
    name: str
    note: str
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
    max_context_bars: int = 36
    require_donchian_break: int | None = None
    require_dormant_break: str | None = None
    require_recent_dormant_break_bars: int | None = None
    min_overhead_room_atr: float | None = None
    require_pre_calm: bool = False
    require_ema20_gt_50: bool = False
    stop_mode: str = "shelf"


SPECS: list[KickoffSpec] = [
    KickoffSpec(
        "V_CONTEXT_RECLAIM_RR15",
        "比較用: V上側回復後の直接リクレイム。棚は使わない。",
        min_speed_ratio=1.2,
        min_recovery_ratio=1.0,
        max_recovery_ratio=1.60,
        shelf_bars=1,
        max_shelf_range_atr=99.0,
        shelf_hold_ratio=0.0,
        max_risk_atr=9.0,
        stop_mode="v_low",
    ),
    KickoffSpec(
        "SHELF6_BREAK_RR15",
        "V後、上側で6本棚を作り、その棚高値を終値ブレイク。",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF8_TIGHT_BREAK_RR15",
        "V後、8本の狭い棚をブレイク。",
        shelf_bars=8,
        max_shelf_range_atr=1.5,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DON20_BREAK_RR15",
        "棚ブレイクと同時にH4 Donchian20高値も更新。",
        require_donchian_break=20,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DON55_BREAK_RR15",
        "棚ブレイクと同時にH4 Donchian55高値も更新。初動寄り。",
        require_donchian_break=55,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DORMANT120_BREAK_RR15",
        "自作ライン応用: 直近30本を除いた過去120本の休眠高値を棚ブレイクで更新。",
        require_dormant_break="dormant120",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DORMANT360_BREAK_RR15",
        "自作ライン応用: 直近90本を除いた過去360本の休眠高値を棚ブレイクで更新。",
        require_dormant_break="dormant360",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DORMANT1250_BREAK_RR15",
        "自作ライン応用: 直近190本を除いた過去1250本の休眠高値を棚ブレイクで更新。",
        require_dormant_break="dormant1250",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DORMANT_ANY_RR15",
        "自作ライン応用: 120/360/1250本のどれかの休眠高値を棚ブレイクで更新。",
        require_dormant_break="any",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_AFTER_DORMANT60_RR15",
        "自作ライン応用: 休眠高値更新から60本以内のV後棚ブレイク。",
        require_recent_dormant_break_bars=60,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_AFTER_DORMANT120_RR15",
        "自作ライン応用: 休眠高値更新から120本以内のV後棚ブレイク。",
        require_recent_dormant_break_bars=120,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_OVERHEAD_ROOM_RR15",
        "自作ライン応用: 近すぎる休眠高値が頭上にある場所を除外。",
        min_overhead_room_atr=1.0,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_EMA_UP_RR15",
        "棚ブレイク時にEMA20>EMA50。",
        require_ema20_gt_50=True,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_PRECALM_BREAK_RR15",
        "V前が過熱トレンドではない状態から棚ブレイク。",
        require_pre_calm=True,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_PRECALM_DORMANT_ANY_RR15",
        "V前過熱なし + 自作ライン休眠高値更新。",
        require_pre_calm=True,
        require_dormant_break="any",
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_PRECALM_AFTER_DORMANT60_RR15",
        "V前過熱なし + 休眠高値更新から60本以内のV後棚ブレイク。",
        require_pre_calm=True,
        require_recent_dormant_break_bars=60,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_PRECALM_OVERHEAD_ROOM_RR15",
        "V前過熱なし + 近すぎる休眠高値を避ける。",
        require_pre_calm=True,
        min_overhead_room_atr=1.0,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DON20_PRECALM_RR15",
        "V前過熱なし + Donchian20更新。",
        require_donchian_break=20,
        require_pre_calm=True,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_DON20_EMA_RR15",
        "Donchian20更新 + EMA20>EMA50。",
        require_donchian_break=20,
        require_ema20_gt_50=True,
        rr=1.5,
    ),
    KickoffSpec(
        "SHELF6_BREAK_RR2",
        "棚ブレイク、TPを2Rへ伸ばす。",
        rr=2.0,
    ),
]


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def adx(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_w = tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr_w
    minus_di = 100 * minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr_w
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)) * 100
    return dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean().fillna(0.0)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["ema20_slope_20_atr"] = (out["ema20"] - out["ema20"].shift(20)) / out["atr"].replace(0.0, np.nan)
    out["ema50_slope_20_atr"] = (out["ema50"] - out["ema50"].shift(20)) / out["atr"].replace(0.0, np.nan)
    out["adx14"] = adx(out, 14)
    out["rsi14"] = rsi(out["close"], 14)
    rng = (out["high"] - out["low"]).replace(0.0, np.nan)
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.5)
    out["don20_high_prev"] = out["high"].rolling(20, min_periods=20).max().shift(1)
    out["don55_high_prev"] = out["high"].rolling(55, min_periods=55).max().shift(1)
    # User's "large trend break" lines, made non-repainting:
    # use only older bars and exclude the recent zone from level discovery.
    dormant_windows = {
        "dormant120": (120, 30),
        "dormant360": (360, 90),
        "dormant1250": (1250, 190),
    }
    for name, (lookback, exclude_recent) in dormant_windows.items():
        width = lookback - exclude_recent
        old_high = out["high"].shift(exclude_recent + 1).rolling(width, min_periods=width).max()
        old_low = out["low"].shift(exclude_recent + 1).rolling(width, min_periods=width).min()
        recent_high = out["high"].shift(1).rolling(exclude_recent, min_periods=exclude_recent).max()
        recent_low = out["low"].shift(1).rolling(exclude_recent, min_periods=exclude_recent).min()
        out[f"{name}_high_prev"] = old_high
        out[f"{name}_low_prev"] = old_low
        out[f"{name}_high_dormant"] = recent_high < old_high
        out[f"{name}_low_dormant"] = recent_low > old_low
    out["range60_atr"] = (out["high"].rolling(60, min_periods=60).max() - out["low"].rolling(60, min_periods=60).min()) / out["atr"].replace(0.0, np.nan)
    out["close_ema50_stretch_atr"] = (out["close"] - out["ema50"]) / out["atr"].replace(0.0, np.nan)
    return out


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "Research_2015_2024"
    return "OOS_2025_2026"


def pre_calm_ok(df: pd.DataFrame, start_i: int) -> bool:
    if start_i < 80:
        return False
    adx_v = float(df["adx14"].iloc[start_i])
    slope = float(df["ema50_slope_20_atr"].iloc[start_i])
    stretch = float(df["close_ema50_stretch_atr"].iloc[start_i])
    range60 = float(df["range60_atr"].iloc[start_i])
    if not all(math.isfinite(x) for x in [adx_v, slope, stretch, range60]):
        return False
    return adx_v <= 26 and slope <= 1.2 and stretch <= 3.0 and range60 <= 16.0


def recent_high_break_ok(df: pd.DataFrame, i: int, length: int | None, atr_i: float, buffer_atr: float) -> bool:
    if length is None:
        return True
    col = f"don{length}_high_prev"
    level = float(df[col].iloc[i])
    return math.isfinite(level) and float(df["close"].iloc[i]) > level + atr_i * buffer_atr


def dormant_high_break_detail(df: pd.DataFrame, i: int, key: str, atr_i: float, buffer_atr: float) -> dict | None:
    level = float(df[f"{key}_high_prev"].iloc[i])
    dormant = bool(df[f"{key}_high_dormant"].iloc[i])
    if not math.isfinite(level) or not dormant:
        return None
    close = float(df["close"].iloc[i])
    if close <= level + atr_i * buffer_atr:
        return None
    return {
        "dormant_break_key": key,
        "dormant_high_level": level,
        "dormant_break_atr": (close - level) / atr_i,
    }


def dormant_high_break_ok(df: pd.DataFrame, i: int, mode: str | None, atr_i: float, buffer_atr: float) -> dict | None:
    if mode is None:
        return {
            "dormant_break_key": "NONE",
            "dormant_high_level": math.nan,
            "dormant_break_atr": math.nan,
        }
    keys = ["dormant120", "dormant360", "dormant1250"] if mode == "any" else [mode]
    hits = []
    for key in keys:
        hit = dormant_high_break_detail(df, i, key, atr_i, buffer_atr)
        if hit is not None:
            hits.append(hit)
    if not hits:
        return None
    # Prefer the longest dormant level when several break on the same bar.
    order = {"dormant120": 1, "dormant360": 2, "dormant1250": 3}
    return sorted(hits, key=lambda x: order.get(str(x["dormant_break_key"]), 0), reverse=True)[0]


def recent_dormant_high_break(df: pd.DataFrame, i: int, bars: int | None, buffer_atr: float) -> dict | None:
    if bars is None:
        return {
            "recent_dormant_break_key": "NONE",
            "bars_since_dormant_break": math.nan,
            "recent_dormant_high_level": math.nan,
        }
    keys = ["dormant120", "dormant360", "dormant1250"]
    start = max(0, i - bars + 1)
    best: dict | None = None
    for j in range(i, start - 1, -1):
        atr_j = float(df["atr"].iloc[j])
        if not math.isfinite(atr_j) or atr_j <= 0:
            continue
        hits = [dormant_high_break_detail(df, j, key, atr_j, buffer_atr) for key in keys]
        hits = [hit for hit in hits if hit is not None]
        if not hits:
            continue
        order = {"dormant120": 1, "dormant360": 2, "dormant1250": 3}
        hit = sorted(hits, key=lambda x: order.get(str(x["dormant_break_key"]), 0), reverse=True)[0]
        best = {
            "recent_dormant_break_key": hit["dormant_break_key"],
            "bars_since_dormant_break": i - j,
            "recent_dormant_high_level": hit["dormant_high_level"],
        }
        break
    return best


def overhead_room_ok(df: pd.DataFrame, i: int, min_room_atr: float | None, atr_i: float) -> dict | None:
    if min_room_atr is None:
        return {
            "nearest_overhead_key": "NONE",
            "nearest_overhead_level": math.nan,
            "nearest_overhead_room_atr": math.nan,
        }
    close = float(df["close"].iloc[i])
    candidates = []
    for key in ["dormant120", "dormant360", "dormant1250"]:
        level = float(df[f"{key}_high_prev"].iloc[i])
        dormant = bool(df[f"{key}_high_dormant"].iloc[i])
        if not dormant or not math.isfinite(level) or level <= close:
            continue
        room_atr = (level - close) / atr_i
        candidates.append((room_atr, key, level))
    if not candidates:
        return {
            "nearest_overhead_key": "NONE",
            "nearest_overhead_level": math.nan,
            "nearest_overhead_room_atr": math.inf,
        }
    room_atr, key, level = sorted(candidates)[0]
    if room_atr < min_room_atr:
        return None
    return {
        "nearest_overhead_key": key,
        "nearest_overhead_level": level,
        "nearest_overhead_room_atr": room_atr,
    }


def find_v_context(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: KickoffSpec,
    used_pairs: set[str],
) -> dict | None:
    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
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
        if not math.isfinite(speed_ratio) or speed_ratio < spec.min_speed_ratio:
            continue
        if recovery_ratio < spec.min_recovery_ratio or recovery_ratio > spec.max_recovery_ratio:
            continue
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue
        return {
            "pair_key": pair_key,
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "drop": drop,
            "drop_atr": drop_atr,
            "drop_bars": drop_bars,
            "recovery_bars_at_context": recovery_bars,
            "recovery_ratio_at_context": recovery_ratio,
            "drop_speed": drop_speed,
            "recovery_speed_at_context": recovery_speed,
            "speed_ratio_at_context": speed_ratio,
            "context_i": i,
        }
    return None


def shelf_signal(df: pd.DataFrame, i: int, ctx: dict, spec: KickoffSpec) -> dict | None:
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
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
    if spec.require_ema20_gt_50 and not (float(df["ema20"].iloc[i]) > float(df["ema50"].iloc[i])):
        return None
    if spec.require_pre_calm and not pre_calm_ok(df, int(ctx["v_start_i"])):
        return None
    if not recent_high_break_ok(df, i, spec.require_donchian_break, atr_i, spec.breakout_buffer_atr):
        return None
    dormant_break = dormant_high_break_ok(df, i, spec.require_dormant_break, atr_i, spec.breakout_buffer_atr)
    if dormant_break is None:
        return None
    recent_dormant = recent_dormant_high_break(df, i, spec.require_recent_dormant_break_bars, spec.breakout_buffer_atr)
    if recent_dormant is None:
        return None
    overhead_room = overhead_room_ok(df, i, spec.min_overhead_room_atr, atr_i)
    if overhead_room is None:
        return None

    shelf = df.iloc[i - spec.shelf_bars : i]
    shelf_high = float(shelf["high"].max())
    shelf_low = float(shelf["low"].min())
    shelf_range_atr = (shelf_high - shelf_low) / atr_i
    hold_level = float(ctx["v_extreme"]) + float(ctx["drop"]) * spec.shelf_hold_ratio
    broke_shelf = float(df["close"].iloc[i]) > shelf_high + atr_i * spec.breakout_buffer_atr
    shelf_tight = shelf_range_atr <= spec.max_shelf_range_atr
    shelf_hold = shelf_low >= hold_level - atr_i * 0.05
    if not (broke_shelf and shelf_tight and shelf_hold):
        return None

    stop = shelf_low - atr_i * 0.25 if spec.stop_mode == "shelf" else float(ctx["v_extreme"]) - atr_i * 0.25
    close = float(df["close"].iloc[i])
    risk_atr = (close - stop) / atr_i
    if stop >= close or risk_atr <= 0 or risk_atr > spec.max_risk_atr:
        return None
    target = close + (close - stop) * spec.rr
    return {
        "stop": stop,
        "target": target,
        "shelf_high": shelf_high,
        "shelf_low": shelf_low,
        "shelf_range_atr": shelf_range_atr,
        "shelf_hold_level": hold_level,
        "risk_atr": risk_atr,
        "entry_close": close,
        "body_ratio": float(df["body_ratio"].iloc[i]),
        "close_location": float(df["close_location"].iloc[i]),
        "ema20_gt_50": bool(float(df["ema20"].iloc[i]) > float(df["ema50"].iloc[i])),
        "don20_break": bool(float(df["close"].iloc[i]) > float(df["don20_high_prev"].iloc[i]) if pd.notna(df["don20_high_prev"].iloc[i]) else False),
        "don55_break": bool(float(df["close"].iloc[i]) > float(df["don55_high_prev"].iloc[i]) if pd.notna(df["don55_high_prev"].iloc[i]) else False),
        "dormant120_break": bool(dormant_high_break_detail(df, i, "dormant120", atr_i, spec.breakout_buffer_atr) is not None),
        "dormant360_break": bool(dormant_high_break_detail(df, i, "dormant360", atr_i, spec.breakout_buffer_atr) is not None),
        "dormant1250_break": bool(dormant_high_break_detail(df, i, "dormant1250", atr_i, spec.breakout_buffer_atr) is not None),
        **dormant_break,
        **recent_dormant,
        **overhead_room,
        "pre_calm": pre_calm_ok(df, int(ctx["v_start_i"])),
    }


def forward_expansion(df: pd.DataFrame, i: int, atr_i: float) -> dict:
    close = float(df["close"].iloc[i])
    out: dict[str, float] = {}
    for h in [12, 24, 48, 72]:
        end = min(len(df) - 1, i + h)
        if end <= i:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"fwd_{h}_atr"] = math.nan
            continue
        win = df.iloc[i + 1 : end + 1]
        out[f"mfe_{h}_atr"] = (float(win["high"].max()) - close) / atr_i
        out[f"mae_{h}_atr"] = (close - float(win["low"].min())) / atr_i
        out[f"fwd_{h}_atr"] = (float(df["close"].iloc[end]) - close) / atr_i
    return out


def run_spec(df: pd.DataFrame, symbol: str, spec: KickoffSpec) -> pd.DataFrame:
    settings = timeframe_settings(TIMEFRAME)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    used_pairs: set[str] = set()
    in_pos_until = -1
    context: dict | None = None

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

        sig = shelf_signal(df, i, context, spec)
        if sig is None:
            continue
        if sig.get("expired"):
            context = None
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction="long",
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=120,
        )
        if trade is None:
            context = None
            continue

        atr_i = float(df["atr"].iloc[i])
        used_pairs.add(str(context["pair_key"]))
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "note": spec.note,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                **context,
                **{k: v for k, v in sig.items() if k not in {"stop", "target"}},
                **forward_expansion(df, i, atr_i),
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
        context = None

    return pd.DataFrame(rows)


def summarize_expansion(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=group_cols)
    base = summarize(trades, group_cols)
    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple))
        for col in ["mfe_24_atr", "mfe_48_atr", "mfe_72_atr", "mae_24_atr", "fwd_48_atr"]:
            row[f"avg_{col}"] = float(group[col].mean())
        row["hit_mfe3atr_48_pct"] = float((group["mfe_48_atr"] >= 3.0).mean() * 100)
        row["hit_mfe5atr_72_pct"] = float((group["mfe_72_atr"] >= 5.0).mean() * 100)
        rows.append(row)
    return base.merge(pd.DataFrame(rows), on=group_cols, how="left")


def summarize_subset(trades: pd.DataFrame, label: str, excluded_symbols: tuple[str, ...]) -> dict:
    if trades.empty:
        return {
            "strategy": label,
            "excluded_symbols": ",".join(excluded_symbols) if excluded_symbols else "NONE",
            "trades": 0,
            "win_rate": 0.0,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": 0.0,
            "pf_after_cost": math.nan,
            "max_dd_r": 0.0,
            "research_trades": 0,
            "research_total_r": 0.0,
            "oos_trades": 0,
            "oos_total_r": 0.0,
        }
    wins = trades.loc[trades["r_after_cost"] > 0, "r_after_cost"].sum()
    losses = -trades.loc[trades["r_after_cost"] < 0, "r_after_cost"].sum()
    equity = trades["r_after_cost"].cumsum()
    dd = (equity.cummax() - equity).max()
    research = trades[trades["period"] == "Research_2015_2024"]
    oos = trades[trades["period"] == "OOS_2025_2026"]
    return {
        "strategy": label,
        "excluded_symbols": ",".join(excluded_symbols) if excluded_symbols else "NONE",
        "trades": int(len(trades)),
        "win_rate": float((trades["r_after_cost"] > 0).mean() * 100),
        "total_r_after_cost": float(trades["r_after_cost"].sum()),
        "avg_r_after_cost": float(trades["r_after_cost"].mean()),
        "pf_after_cost": float(wins / losses) if losses > 0 else math.inf,
        "max_dd_r": float(dd),
        "research_trades": int(len(research)),
        "research_total_r": float(research["r_after_cost"].sum()),
        "oos_trades": int(len(oos)),
        "oos_total_r": float(oos["r_after_cost"].sum()),
    }


def symbol_exclusion_sweep(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    symbols = sorted(trades["symbol"].dropna().unique())
    for strategy, group in trades.groupby("strategy"):
        for r in range(0, min(3, len(symbols)) + 1):
            for excluded in combinations(symbols, r):
                subset = group[~group["symbol"].isin(excluded)].copy()
                if len(subset) < 15:
                    continue
                rows.append(summarize_subset(subset.sort_values("entry_time"), strategy, excluded))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["pf_after_cost", "total_r_after_cost"], ascending=[False, False]).reset_index(drop=True)


def write_report(
    trades: pd.DataFrame,
    overall: pd.DataFrame,
    ex_xau: pd.DataFrame,
    by_period: pd.DataFrame,
    by_symbol: pd.DataFrame,
) -> None:
    lines = [
        "# H4 V Kickoff Catalyst 検証 2026-05-30",
        "",
        "## 目的",
        "",
        "Vをそのまま買うのではなく、Vを相場のスイッチ候補として扱い、V後に上側で棚を作ってブレイクした時だけ買う形を検証した。",
        "",
        "## 発想",
        "",
        "- Vの底や単純リクレイムは、強い場所ではなく中途半端な戻りになることがある。",
        "- 強いのは、急落が否定された後、価格が上側で崩れずに滞在し、その棚高値を抜ける場面ではないか。",
        "- これは逆張りVではなく、売り失敗後の初動・拡大確認として扱う。",
        "",
        "## ルール群",
        "",
        "- 比較用: `V_CONTEXT_RECLAIM_RR15`",
        "- 本命: `SHELF6_BREAK_RR15`, `SHELF6_DON20_BREAK_RR15`, `SHELF6_DON55_BREAK_RR15`",
        "- 自作ライン応用: `SHELF6_DORMANT120_BREAK_RR15`, `SHELF6_DORMANT360_BREAK_RR15`, `SHELF6_DORMANT1250_BREAK_RR15`, `SHELF6_DORMANT_ANY_RR15`",
        "- Entry: H4棚高値を終値で上抜け、次足始値",
        "- SL: 棚安値 - 0.25ATR",
        "- TP: 1.5R または 2R",
        "- 最大保有: H4 120本",
        "",
        "## 全体結果",
        "",
        markdown_table(overall, 80),
        "",
        "## 実戦候補 XAUUSD除外",
        "",
        markdown_table(ex_xau, 80),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 120),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 140),
        "",
        "## 補足",
        "",
        "- 通貨除外の影響は `symbol_exclusion_sweep.csv` に出力した。",
        "- これは過剰最適化の危険があるため、採用候補は XAUUSD 以外に 1-2通貨までの除外を優先する。",
        "",
        "## 出力",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_ex_xau.csv`",
        "- `summary_by_period.csv`",
        "- `summary_by_symbol.csv`",
        "- `symbol_exclusion_sweep.csv`",
        "- `data_coverage.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_trades: list[pd.DataFrame] = []
    coverage_rows: list[dict] = []

    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        df = add_features(resample_ohlc(raw, TIMEFRAME))
        for spec in SPECS:
            trades = run_spec(df, symbol, spec)
            if not trades.empty:
                all_trades.append(trades)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)
    if not all_trades:
        (OUT_DIR / "report_ja.md").write_text("# H4 V Kickoff Catalyst\n\nNo trades.", encoding="utf-8")
        print(f"No trades. Report: {OUT_DIR / 'report_ja.md'}")
        return

    trades_df = pd.concat(all_trades, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades_df[col] = pd.to_datetime(trades_df[col])
    trades_df = trades_df.sort_values(["strategy", "entry_time", "symbol"]).reset_index(drop=True)
    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize_expansion(trades_df, ["strategy"])
    ex_xau_trades = trades_df[trades_df["symbol"] != "XAUUSD"].copy()
    ex_xau = summarize_expansion(ex_xau_trades, ["strategy"])
    by_period = summarize_expansion(trades_df, ["strategy", "period"])
    by_symbol = summarize_expansion(trades_df, ["strategy", "symbol"])
    exclusion_sweep = symbol_exclusion_sweep(trades_df)

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    ex_xau.to_csv(OUT_DIR / "summary_ex_xau.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    exclusion_sweep.to_csv(OUT_DIR / "symbol_exclusion_sweep.csv", index=False)

    write_report(trades_df, overall, ex_xau, by_period, by_symbol)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(ex_xau.to_string(index=False))


if __name__ == "__main__":
    main()

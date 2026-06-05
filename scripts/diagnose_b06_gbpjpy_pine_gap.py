#!/usr/bin/env python3
"""Diagnose GBPJPY B06 Python-only signals vs Pine-equivalent gates."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
sys.path.insert(0, str(ELLIOTT))

from run_elliott_fibo_study import (  # noqa: E402
    build_confirmed_pivots,
    holiday_market,
    pivots_until,
    timeframe_settings,
)
from run_h4_v_initial_shelf_deep_dive import (  # noqa: E402
    CURRENT_SPEC,
    find_v_context,
    prepare_data,
    pre_calm_ok,
    run_spec_for_symbol,
    shelf_signal,
)

SPEC = CURRENT_SPEC
SETTINGS = timeframe_settings("H4")
PINE_AUTH = OUT / "python_expected_b06_tv_oanda_gbpjpy_pine_authoritative.csv"
PY_ONLY = OUT / "python_expected_b06_tv_oanda_gbpjpy_python_only.csv"


@dataclass
class PineCtx:
    pair_key: str
    ctx_bar: int
    v_start_i: int
    v_low_i: int
    v_start: float
    v_low: float
    drop: float
    drop_speed: float
    pre_adx: float
    pre_slope: float
    pre_stretch: float
    pre_range60: float


def pine_post_low(df: pd.DataFrame, i: int, low_i: int) -> float:
    recovery_bars = max(i - low_i, 1)
    post = float(df["low"].iloc[i])
    for m in range(1, min(recovery_bars, SPEC.max_recovery_bars)):
        if low_i + m <= i:
            post = min(post, float(df["low"].iloc[i - m]))
    return post


def pine_low_held(df: pd.DataFrame, i: int, low_i: int, low_price: float) -> tuple[bool, float]:
    atr_i = float(df["atr"].iloc[i])
    post = pine_post_low(df, i, low_i)
    ok = post >= low_price - atr_i * 0.10
    return ok, post


def pine_shelf_gates(df: pd.DataFrame, i: int, ctx: PineCtx) -> dict:
    atr_i = float(df["atr"].iloc[i])
    context_age = i - ctx.ctx_bar
    shelf = df.iloc[i - SPEC.shelf_bars : i]
    shelf_high = float(shelf["high"].max())
    shelf_low = float(shelf["low"].min())
    shelf_range_atr = (shelf_high - shelf_low) / atr_i
    hold_line = ctx.v_low + ctx.drop * SPEC.shelf_hold_ratio
    close = float(df["close"].iloc[i])
    body_ratio = float(df["body_ratio"].iloc[i])
    close_location = float(df["close_location"].iloc[i])
    broke = close > shelf_high + atr_i * SPEC.breakout_buffer_atr
    stop = shelf_low - atr_i * SPEC.stop_buffer_atr
    risk_dist = close - stop
    risk_atr = risk_dist / atr_i if atr_i > 0 else math.nan

    pre_calm = (
        ctx.pre_adx <= SPEC.adx_max
        and ctx.pre_slope <= 1.2
        and ctx.pre_stretch <= 3.0
        and ctx.pre_range60 <= SPEC.range60_max_atr
    )
    expired = context_age > SPEC.max_context_bars
    enough_shelf = context_age >= SPEC.shelf_bars and i - SPEC.shelf_bars >= ctx.ctx_bar
    shelf_tight = shelf_range_atr <= SPEC.max_shelf_range_atr
    shelf_holds = shelf_low >= hold_line - atr_i * 0.05
    quality = body_ratio >= SPEC.min_body_ratio and close_location >= SPEC.min_close_location
    risk_ok = risk_dist > 0 and risk_atr <= SPEC.max_risk_atr

    skip = 0
    if expired:
        skip = 11
    elif SPEC.require_pre_calm and not pre_calm:
        skip = 6
    elif not shelf_tight:
        skip = 7
    elif not shelf_holds:
        skip = 8
    elif not quality:
        skip = 9
    elif not risk_ok:
        skip = 10

    return {
        "context_age": context_age,
        "enough_shelf": enough_shelf,
        "broke_shelf": broke,
        "skip_code": skip if broke and enough_shelf else 0,
        "raw_signal": broke and enough_shelf and skip == 0,
        "shelf_high": shelf_high,
        "shelf_low": shelf_low,
        "shelf_range_atr": shelf_range_atr,
        "hold_line": hold_line,
        "breakout_atr": (close - shelf_high) / atr_i,
        "body_ratio": body_ratio,
        "close_location": close_location,
        "risk_atr": risk_atr,
        "pre_adx": ctx.pre_adx,
        "pre_slope": ctx.pre_slope,
        "pre_stretch": ctx.pre_stretch,
        "pre_range60": ctx.pre_range60,
        "pre_calm_ok": pre_calm,
    }


def find_pine_style_context(
    df: pd.DataFrame,
    i: int,
    pivots: list,
    used_pairs: set[str],
    flat: bool,
) -> PineCtx | None:
    if not flat or len(pivots) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    n = len(pivots)
    max_scan = min(12, n - 1)
    for scan in range(max_scan):
        j = n - 2 - scan
        p0, p1 = pivots[j], pivots[j + 1]
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
        if drop_bars < SPEC.min_drop_bars or drop_bars > SPEC.max_drop_bars:
            continue
        if recovery_bars > SPEC.max_recovery_bars:
            continue
        drop_atr = drop / atr_i
        drop_speed = drop / drop_bars / atr_i
        recovery = close - p1.price
        recovery_ratio = recovery / drop
        recovery_speed = recovery / recovery_bars / atr_i
        speed_ratio = recovery_speed / drop_speed if drop_speed > 0 else math.nan
        if drop_atr < SPEC.min_drop_atr or drop_speed < SPEC.min_drop_speed:
            continue
        if not math.isfinite(speed_ratio) or speed_ratio < SPEC.min_speed_ratio:
            continue
        if recovery_ratio < SPEC.min_recovery_ratio or recovery_ratio > SPEC.max_recovery_ratio:
            continue
        low_held, post_low = pine_low_held(df, i, p1.pivot_i, p1.price)
        if not low_held:
            continue
        return PineCtx(
            pair_key=pair_key,
            ctx_bar=i,
            v_start_i=p0.pivot_i,
            v_low_i=p1.pivot_i,
            v_start=p0.price,
            v_low=p1.price,
            drop=drop,
            drop_speed=drop_speed,
            pre_adx=float(df["adx14"].iloc[p0.pivot_i]),
            pre_slope=float(df["ema50_slope_20_atr"].iloc[p0.pivot_i]),
            pre_stretch=float(df["close_ema50_stretch_atr"].iloc[p0.pivot_i]),
            pre_range60=float(df["range60_atr"].iloc[p0.pivot_i]),
        )
    return None


def simulate_pine_state_machine(df: pd.DataFrame, pivots: list, pine_only_times: set[pd.Timestamp]) -> pd.DataFrame:
    pointer = 0
    used_pairs: set[str] = set()
    ctx: PineCtx | None = None
    in_pos_until = -1
    pending_until = -1
    last_exit = -1
    rows: list[dict] = []

    for i in range(100, len(df) - 1):
        confirmed = [p for p in pivots if p.confirm_i <= i]
        ts = df.index[i]
        if ts < pd.Timestamp("2015-01-01") or ts > pd.Timestamp("2026-12-31 23:59:59") or holiday_market(ts):
            continue

        flat = i > in_pos_until and i > pending_until and (last_exit < 0 or i > last_exit)

        if ctx is None and flat:
            ctx = find_pine_style_context(df, i, confirmed, used_pairs, flat=True)

        if ctx is not None:
            gates = pine_shelf_gates(df, i, ctx)
            if gates["context_age"] > SPEC.max_context_bars:
                ctx = None
                continue
            if gates["raw_signal"]:
                used_pairs.add(ctx.pair_key)
                in_pos_until = i + 1 + SPEC.max_hold_bars
                pending_until = i + 2
                last_exit = in_pos_until
                rows.append({"signal_time": ts, "pair_key": ctx.pair_key, "source": "pine_sim", **gates})
                ctx = None
            elif gates["broke_shelf"] and gates["enough_shelf"] and ts in pine_only_times:
                rows.append(
                    {
                        "signal_time": ts,
                        "pair_key": ctx.pair_key,
                        "source": "pine_skip",
                        "skip_code": gates["skip_code"],
                        **gates,
                    }
                )

    return pd.DataFrame(rows)


def diagnose_signal(df: pd.DataFrame, pivots: list, signal_time: pd.Timestamp, pair_key: str) -> dict:
    i = int(df.index.get_loc(signal_time))
    active: list = []
    pointer = 0
    pivots_until(pivots, pointer, i, active)

    ctx_py = find_v_context(df, i, active, SPEC, set())
    sig_py = shelf_signal(df, i, ctx_py, SPEC) if ctx_py else None

    # Pine lowHeld vs Python post_low at context bar (use v_low from pair)
    parts = pair_key.split("-")
    v_start_i, v_low_i = int(parts[0]), int(parts[1])
    py_post = float(df["low"].iloc[v_low_i + 1 : i + 1].min())
    py_low_held = py_post >= float(df["low"].iloc[v_low_i]) - float(df["atr"].iloc[i]) * 0.10
    pine_held, pine_post = pine_low_held(df, i, v_low_i, float(df["low"].iloc[v_low_i]))

    ctx_pine = PineCtx(
        pair_key=pair_key,
        ctx_bar=i,
        v_start_i=v_start_i,
        v_low_i=v_low_i,
        v_start=float(df["high"].iloc[v_start_i]),
        v_low=float(df["low"].iloc[v_low_i]),
        drop=float(df["high"].iloc[v_start_i]) - float(df["low"].iloc[v_low_i]),
        drop_speed=0.0,
        pre_adx=float(df["adx14"].iloc[v_start_i]),
        pre_slope=float(df["ema50_slope_20_atr"].iloc[v_start_i]),
        pre_stretch=float(df["close_ema50_stretch_atr"].iloc[v_start_i]),
        pre_range60=float(df["range60_atr"].iloc[v_start_i]),
    )
    gates = pine_shelf_gates(df, i, ctx_pine)

    # Would Pine pick this pair at context-establishment bar?
    # Walk back to find when Python context_i was set
    ctx_i = int(ctx_py["context_i"]) if ctx_py else i
    confirmed = [p for p in pivots if p.confirm_i <= ctx_i]
    pine_at_ctx = find_pine_style_context(df, ctx_i, confirmed, used_pairs=set(), flat=True)

    return {
        "signal_time": signal_time,
        "bar_i": i,
        "pair_key": pair_key,
        "py_context_i": ctx_py["context_i"] if ctx_py else None,
        "py_context_pair": ctx_py["pair_key"] if ctx_py else None,
        "py_shelf_ok": sig_py is not None and not sig_py.get("expired"),
        "py_post_low": py_post,
        "py_low_held": py_low_held,
        "pine_post_low": pine_post,
        "pine_low_held": pine_held,
        "pine_at_ctx_pair": pine_at_ctx.pair_key if pine_at_ctx else None,
        "pine_gates": gates,
        "pre_calm_py_at_vstart": pre_calm_ok(df, v_start_i, SPEC),
    }


def main() -> None:
    data, pivots_map = prepare_data("tv_oanda", OUT, ["GBPJPY"])
    df = data["GBPJPY"]
    pivots = pivots_map["GBPJPY"]

    py_trades = run_spec_for_symbol(df, pivots, "GBPJPY", SPEC)
    pine_auth = pd.read_csv(PINE_AUTH, parse_dates=["signal_time"])
    py_only = pd.read_csv(PY_ONLY, parse_dates=["signal_time"])
    pine_times = set(py_only["signal_time"])

    sim = simulate_pine_state_machine(df, pivots, pine_times)
    print("=== Pine-style state machine signals ===")
    print(sim[sim["source"] == "pine_sim"][["signal_time", "pair_key"]].to_string(index=False))
    print("\n=== Pine skips on Python-only bars ===")
    skips = sim[sim["source"] == "pine_skip"]
    if skips.empty:
        print("(none — context never reached breakout on those bars in sim)")
    else:
        print(skips[["signal_time", "pair_key", "skip_code", "shelf_range_atr", "pre_calm_ok", "risk_atr"]].to_string(index=False))

    print("\n=== Per-signal deep dive ===")
    for _, row in py_only.iterrows():
        d = diagnose_signal(df, pivots, row["signal_time"], row["pair_key"])
        g = d["pine_gates"]
        print(f"\n--- {row['signal_time_tv']} pair={row['pair_key']} ---")
        print(f"  Python context bar: {d['py_context_i']} pair={d['py_context_pair']}")
        print(f"  Pine would pick at ctx bar: {d['pine_at_ctx_pair']}")
        print(f"  lowHeld: py={d['py_low_held']} post={d['py_post_low']:.3f} | pine={d['pine_low_held']} post={d['pine_post_low']:.3f}")
        print(f"  PRECALM py@Vstart: {d['pre_calm_py_at_vstart']}")
        print(
            f"  Shelf gates @signal: broke={g['broke_shelf']} range={g['shelf_range_atr']:.3f} "
            f"holds={g['shelf_low'] >= g['hold_line'] - float(df['atr'].iloc[d['bar_i']])*0.05} "
            f"body={g['body_ratio']:.2f} close_loc={g['close_location']:.2f} risk_atr={g['risk_atr']:.2f}"
        )
        print(f"  pre: adx={g['pre_adx']:.2f} slope={g['pre_slope']:.2f} stretch={g['pre_stretch']:.2f} range60={g['pre_range60']:.2f}")
        print(f"  pine skip_code if breakout: {g['skip_code']} raw={g['raw_signal']}")

    # Compare pivot at v_low for each false signal
    print("\n=== Pivot neighborhood (confirmed) ===")
    for _, row in py_only.iterrows():
        parts = row["pair_key"].split("-")
        vs, vl = int(parts[0]), int(parts[1])
        sig_i = int(df.index.get_loc(row["signal_time"]))
        near = [p for p in pivots if vs - 5 <= p.pivot_i <= vl + 5]
        print(f"\n{row['signal_time_tv']}:")
        for p in near:
            print(f"  {p.kind} i={p.pivot_i} t={df.index[p.pivot_i]} price={p.price:.3f} confirm={df.index[p.confirm_i]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Loser-cohort event scanner — no entries, no parameter optimization.

Detects moments when specific trader cohorts likely admit defeat (stops / covers),
then measures forward MFE/MAE/fwd in ATR at 12/24/48/72 bars.

Events:
  E1  short_squeeze_cascade   — shorts trapped after drop -> shelf break (SQZ family)
  E2  v_reaccel              — V context + shelf break (re-acceleration after V denial)
  E3  break_fail_long_trap   — H4 Don120 close-fail after high break (longs trapped)
  E3b break_fail_d1_long     — D1 Don120 close-fail (context event)
  E4  range_break_up         — compressed range then upside break (range losers exit)
  E4s range_break_down       — compressed range then downside break

Also logs a matched random baseline per symbol for forward-up comparison.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    timeframe_settings,
)
from run_h4_v_kickoff_catalyst_study import (
    KickoffSpec,
    add_features as add_v_features,
    find_v_context,
    forward_expansion,
    pre_calm_ok,
    shelf_signal,
)
from run_market_psychology_strategy_tv_check import (
    PsySpec,
    add_features as add_sqz_features,
    squeeze_signal,
)
from run_trap_false_break_reaction_study import (
    TrapSpec,
    add_trap_indicators,
    base_event_fields,
    quality_ok,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_06_01" / "loser_cohort_event_scanner"
DOCS_OUT = THIS_DIR.parents[1] / "docs" / "research" / "loser_cohort_event_scanner_2026-06-01"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_OUT.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")
H4 = "H4"
HORIZONS = (12, 24, 48, 72)
RNG_SEED = 42

SQZ_DEFAULT = PsySpec("E1_SQZ_DEFAULT", "short_squeeze")
SQZ_STRICT = PsySpec("E1_SQZ_STRICT", "short_squeeze", shelf_atr=2.0, move_atr=3.5)

V_SHELF_SPEC = KickoffSpec(
    "E2_V_SHELF6",
    "V後棚ブレイク（敗者=売り残り）",
    min_drop_atr=2.8,
    min_drop_speed=0.25,
    min_speed_ratio=1.0,
    min_recovery_ratio=0.65,
    max_recovery_ratio=1.25,
    shelf_bars=6,
    max_shelf_range_atr=1.8,
    shelf_hold_ratio=0.50,
    breakout_buffer_atr=0.05,
    min_body_ratio=0.40,
    min_close_location=0.60,
    max_risk_atr=9.0,
    rr=1.5,
    max_context_bars=36,
)

TRAP_BODY = TrapSpec(
    "SCANNER_CLOSEFAIL_BODY",
    "close_fail",
    120,
    fail_window=6,
    quality="body_close",
)


def period_name(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts <= RESEARCH_END else "OOS_2025_2026"


def forward_path(df: pd.DataFrame, signal_i: int, cascade: str, atr_i: float) -> dict:
    """cascade: 'up' | 'down' — direction losers are forced to cover / stop."""
    sign = 1.0 if cascade == "up" else -1.0
    close_i = float(df["close"].iloc[signal_i])
    out: dict[str, float | bool] = {}
    for h in HORIZONS:
        end = min(len(df) - 1, signal_i + h)
        if end <= signal_i:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"mae_{h}_atr"] = math.nan
            out[f"fwd_{h}_atr"] = math.nan
            out[f"hit_3atr_{h}"] = False
            continue
        window = df.iloc[signal_i + 1 : end + 1]
        if cascade == "up":
            mfe = (float(window["high"].max()) - close_i) / atr_i
            mae = (close_i - float(window["low"].min())) / atr_i
        else:
            mfe = (close_i - float(window["low"].min())) / atr_i
            mae = (float(window["high"].max()) - close_i) / atr_i
        out[f"mfe_{h}_atr"] = mfe
        out[f"mae_{h}_atr"] = mae
        out[f"fwd_{h}_atr"] = sign * (float(df["close"].iloc[end]) - close_i) / atr_i
        out[f"hit_3atr_{h}"] = bool(mfe >= 3.0)

        hit_first = False
        decided = False
        for _, row in window.iterrows():
            if cascade == "up":
                hit_fav = float(row["high"]) >= close_i + atr_i
                hit_bad = float(row["low"]) <= close_i - atr_i
            else:
                hit_fav = float(row["low"]) <= close_i - atr_i
                hit_bad = float(row["high"]) >= close_i + atr_i
            if hit_fav or hit_bad:
                hit_first = hit_fav and not hit_bad
                decided = True
                break
        out[f"hit_1atr_first_{h}"] = bool(hit_first and decided)
    return out


def event_row(
    symbol: str,
    timeframe: str,
    event_type: str,
    loser_cohort: str,
    cascade_direction: str,
    signal_time: pd.Timestamp,
    signal_i: int,
    df: pd.DataFrame,
    extra: dict,
) -> dict:
    atr_i = float(df["atr"].iloc[signal_i])
    ts = df.index[signal_i]
    row = {
        "symbol": symbol,
        "timeframe": timeframe,
        "event_type": event_type,
        "loser_cohort": loser_cohort,
        "cascade_direction": cascade_direction,
        "signal_time": ts,
        "period": period_name(ts),
        "year": int(ts.year),
        "atr_signal": atr_i,
        **extra,
        **forward_path(df, signal_i, cascade_direction, atr_i),
    }
    return row


def scan_e1(df: pd.DataFrame, symbol: str, spec: PsySpec) -> list[dict]:
    rows: list[dict] = []
    last_i = -999
    for i in range(80, len(df) - max(HORIZONS) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        sig = squeeze_signal(df, i, spec)
        if sig is None:
            continue
        if i - last_i < 6:
            continue
        last_i = i
        extra = {k: v for k, v in sig.items() if k != "stop"}
        extra["sqz_variant"] = spec.name
        rows.append(
            event_row(
                symbol,
                H4,
                "E1_short_squeeze_cascade",
                "shorts_and_late_sellers",
                "up",
                ts,
                i,
                df,
                extra,
            )
        )
        # Second-wave tag: another shelf break within 48 bars
        for j in range(i + 1, min(len(df) - 1, i + 48)):
            sig2 = squeeze_signal(df, j, spec)
            if sig2 is not None:
                rows.append(
                    event_row(
                        symbol,
                        H4,
                        "E1_chain_second_shelf",
                        "shorts_still_trapped",
                        "up",
                        df.index[j],
                        j,
                        df,
                        {"parent_event": str(ts), "sqz_variant": spec.name},
                    )
                )
                break
    return rows


def scan_e2(df: pd.DataFrame, symbol: str) -> list[dict]:
    settings = timeframe_settings(H4)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list = []
    pointer = 0
    rows: list[dict] = []
    used_pairs: set[str] = set()
    context: dict | None = None
    last_i = -999

    for i in range(100, len(df) - max(HORIZONS) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if i - last_i < 6:
            continue

        if context is None:
            context = find_v_context(df, i, active, V_SHELF_SPEC, used_pairs)
            if context is None:
                continue

        sig = shelf_signal(df, i, context, V_SHELF_SPEC)
        if sig is None:
            continue
        if sig.get("expired"):
            context = None
            continue

        used_pairs.add(str(context["pair_key"]))
        last_i = i
        extra = {
            k: v
            for k, v in {**context, **sig}.items()
            if k not in {"stop", "target", "expired"}
        }
        extra["pre_calm"] = pre_calm_ok(df, int(context["v_start_i"]))
        rows.append(
            event_row(
                symbol,
                H4,
                "E2_v_reaccel",
                "v_deniers_and_range_shorts",
                "up",
                ts,
                i,
                df,
                extra,
            )
        )
        context = None
    return rows


def scan_trap_close_fail(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    lookback: int,
    fail_window: int,
) -> list[dict]:
    rows: list[dict] = []
    high_col = f"donchian{lookback}_high"
    low_col = f"donchian{lookback}_low"
    spec = TRAP_BODY
    pending_high: dict | None = None
    last_i = -999

    for i in range(lookback + 30, len(df) - max(HORIZONS) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        high_level = float(df[high_col].iloc[i])
        if not math.isfinite(high_level):
            continue
        close = float(df["close"].iloc[i])

        if pending_high is not None and i - int(pending_high["i"]) > fail_window:
            pending_high = None

        if pending_high is not None and i > int(pending_high["i"]):
            level = float(pending_high["level"])
            if close < level - atr_i * spec.reclaim_buffer_atr:
                direction = "short"
                if quality_ok(df, i, direction, spec):
                    b_i = int(pending_high["i"])
                    extreme = float(df["high"].iloc[b_i : i + 1].max())
                    if i - last_i >= 6:
                        last_i = i
                        evt = "E3_break_fail_long_trap" if timeframe == H4 else "E3b_d1_break_fail_long"
                        rows.append(
                            event_row(
                                symbol,
                                timeframe,
                                evt,
                                "breakout_chasers_long",
                                "down",
                                ts,
                                i,
                                df,
                                {
                                    **base_event_fields(df, i, "long", level, b_i, extreme),
                                    "don_lookback": lookback,
                                    "fail_window": fail_window,
                                },
                            )
                        )
                pending_high = None

        if close > high_level + atr_i * spec.break_buffer_atr:
            pending_high = {"i": i, "level": high_level}

    return rows


def range_regime_ok(df: pd.DataFrame, i: int) -> bool:
    adx = float(df["adx14"].iloc[i])
    r60 = float(df["range60_atr"].iloc[i])
    if not math.isfinite(adx) or not math.isfinite(r60):
        return False
    return adx <= 26.0 and r60 <= 16.0


def scan_e4(df: pd.DataFrame, symbol: str) -> list[dict]:
    rows: list[dict] = []
    n = 20
    last_up = -999
    last_dn = -999
    for i in range(80, len(df) - max(HORIZONS) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if not range_regime_ok(df, i):
            continue
        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        box = df.iloc[i - n : i]
        box_high = float(box["high"].max())
        box_low = float(box["low"].min())
        touches_hi = int((box["high"] >= box_high - 0.15 * atr_i).sum())
        touches_lo = int((box["low"] <= box_low + 0.15 * atr_i).sum())
        if touches_hi < 2 or touches_lo < 2:
            continue
        close = float(df["close"].iloc[i])
        prev_close = float(df["close"].iloc[i - 1])
        buf = 0.05 * atr_i

        if prev_close <= box_high and close > box_high + buf and i - last_up >= 12:
            last_up = i
            rows.append(
                event_row(
                    symbol,
                    H4,
                    "E4_range_break_up",
                    "range_shorts_and_late_sellers",
                    "up",
                    ts,
                    i,
                    df,
                    {
                        "range60_atr": float(df["range60_atr"].iloc[i]),
                        "adx14": float(df["adx14"].iloc[i]),
                        "box_range_atr": (box_high - box_low) / atr_i,
                        "touches_high": touches_hi,
                        "touches_low": touches_lo,
                    },
                )
            )
        if prev_close >= box_low and close < box_low - buf and i - last_dn >= 12:
            last_dn = i
            rows.append(
                event_row(
                    symbol,
                    H4,
                    "E4_range_break_down",
                    "range_longs_and_early_buyers",
                    "down",
                    ts,
                    i,
                    df,
                    {
                        "range60_atr": float(df["range60_atr"].iloc[i]),
                        "adx14": float(df["adx14"].iloc[i]),
                        "box_range_atr": (box_high - box_low) / atr_i,
                        "touches_high": touches_hi,
                        "touches_low": touches_lo,
                    },
                )
            )
    return rows


def scan_random_baseline(df: pd.DataFrame, symbol: str, n_target: int) -> list[dict]:
    rng = random.Random(RNG_SEED + hash(symbol) % 10000)
    candidates = []
    for i in range(80, len(df) - max(HORIZONS) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        candidates.append(i)
    if not candidates or n_target <= 0:
        return []
    pick = rng.sample(candidates, min(n_target, len(candidates)))
    rows = []
    for i in sorted(pick):
        ts = df.index[i]
        rows.append(
            event_row(
                symbol,
                H4,
                "RANDOM_H4_BAR",
                "none",
                "up",
                ts,
                i,
                df,
                {},
            )
        )
    return rows


def summarize_events(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    rows = []
    for key, g in events.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        mfe48 = g["mfe_48_atr"].astype(float)
        mae48 = g["mae_48_atr"].astype(float)
        fwd48 = g["fwd_48_atr"].astype(float)
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "events": len(g),
                "median_mfe_48_atr": round(float(mfe48.median()), 2),
                "median_mae_48_atr": round(float(mae48.median()), 2),
                "median_fwd_48_atr": round(float(fwd48.median()), 2),
                "pct_mfe48_ge_3": round(float((mfe48 >= 3).mean() * 100), 1),
                "pct_hit_1atr_first_24": round(float(g["hit_1atr_first_24"].astype(bool).mean() * 100), 1),
                "pct_mae48_ge_2": round(float((mae48 >= 2).mean() * 100), 1),
            }
        )
    return pd.DataFrame(rows).sort_values(["events", "median_mfe_48_atr"], ascending=[False, False])


def main() -> None:
    all_events: list[dict] = []
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        h4_sqz = add_sqz_features(raw)
        h4_v = add_v_features(resample_ohlc(raw, H4))
        h4_trap = add_trap_indicators(resample_ohlc(raw, H4))
        d1_trap = add_trap_indicators(resample_ohlc(raw, "D1"))

        sym_events: list[dict] = []
        sym_events.extend(scan_e1(h4_sqz, symbol, SQZ_DEFAULT))
        sym_events.extend(scan_e1(h4_sqz, symbol, SQZ_STRICT))
        sym_events.extend(scan_e2(h4_v, symbol))
        sym_events.extend(scan_trap_close_fail(h4_trap, symbol, H4, 120, 6))
        sym_events.extend(scan_trap_close_fail(d1_trap, symbol, "D1", 120, 6))
        sym_events.extend(scan_e4(h4_v, symbol))
        sym_events.extend(scan_random_baseline(h4_v, symbol, max(20, len(sym_events) // 5)))
        all_events.extend(sym_events)

    events = pd.DataFrame(all_events)
    events.to_csv(OUT_DIR / "events_all.csv", index=False)
    events.to_csv(DOCS_OUT / "events_all.csv", index=False)

    by_type = summarize_events(events, ["event_type", "cascade_direction"])
    by_type.to_csv(OUT_DIR / "summary_by_event_type.csv", index=False)
    by_type.to_csv(DOCS_OUT / "summary_by_event_type.csv", index=False)

    if "sqz_variant" in events.columns:
        sqz = summarize_events(
            events[events["event_type"].str.startswith("E1_")],
            ["sqz_variant", "period"],
        )
        sqz.to_csv(OUT_DIR / "summary_e1_sqz_variant.csv", index=False)
        sqz.to_csv(DOCS_OUT / "summary_e1_sqz_variant.csv", index=False)

    by_sym = summarize_events(events, ["symbol", "event_type"])
    by_sym.to_csv(OUT_DIR / "summary_by_symbol_event.csv", index=False)

    by_period = summarize_events(events, ["period", "event_type"])
    by_period.to_csv(OUT_DIR / "summary_by_period_event.csv", index=False)

    by_year = summarize_events(events, ["year", "event_type"])
    by_year.to_csv(OUT_DIR / "summary_by_year_event.csv", index=False)

    lines = [
        "# 敗者コホート・イベントスキャナー（2026-06-01）",
        "",
        "エントリーなし。各イベント後 **12/24/48/72 H4本** の MFE/MAE/fwd（ATR単位）のみ記録。",
        "",
        "## 設計原則",
        "",
        "- 最適化しない（SQZ/T5/Trap は既存固定パラメータ）",
        "- 勝率ではなく **cascade方向への median MFE** と **P(MFE48≥3ATR)**",
        "- `RANDOM_H4_BAR` は同数サンプルの対照",
        "",
        "## イベント別サマリー（全期間）",
        "",
        markdown_table(by_type.head(20)),
        "",
        "## 期間別（Research vs OOS）",
        "",
        markdown_table(by_period.head(24)),
        "",
        "## 解釈ガイド",
        "",
        "| event_type | 主な敗者 | cascade |",
        "|---|---|---|",
        "| E1_short_squeeze_cascade | ショート・戻り売り | up |",
        "| E2_v_reaccel | V否定後の売り残り | up |",
        "| E3_break_fail_long_trap | 高値ブレイク買い | down |",
        "| E4_range_break_* | レンジ両建て | up/down |",
        "",
        "## 再現",
        "",
        "```bash",
        "python3 backtests/elliott_fibo/run_loser_cohort_event_scanner.py",
        "```",
        "",
        f"全イベント件数: **{len(events)}**",
    ]
    report = "\n".join(lines)
    (OUT_DIR / "REPORT_ja.md").write_text(report, encoding="utf-8")
    (DOCS_OUT / "REPORT_ja.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

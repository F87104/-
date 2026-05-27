#!/usr/bin/env python3
"""
USDJPY M5 Synapse recheck.

The goal is not to claim a perfect reproduction of Tobi/Synapse discretion.
This script turns the latest chat transcript into a testable mechanical draft:

- Trade the turn from wave 2 into wave 3.
- Use one diagonal trendline and two horizontal levels, A and B.
- Prefer half-value targets over full N targets.
- Separate wave recognition from trade permission:
  upper-timeframe context, retrace quality, break quality, and RR decide whether
  a recognized pattern is actually tradable.

Input data:
  F87104_test/**/USDJPY_M5_*.csv
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
OUT_DIR = THIS_DIR / "results_usdjpy_m5_synapse_recheck_2026_05_24"
OUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")

ATR_PERIOD = 14
BREAK_BUFFER_ATR = 0.05
STOP_BUFFER_ATR = 0.20
MIN_WAVE1_ATR = 1.5
MAX_RETRACE = 0.95

SPREAD_PRICE = 0.010
SLIP_PRICE = 0.005

TIMEFRAME_CONFIGS = {
    "M5": {"rule": "5min", "pivot_width": 8, "min_swing_atr": 1.6, "max_hold": 144},
    "M15": {"rule": "15min", "pivot_width": 5, "min_swing_atr": 1.45, "max_hold": 120},
    "M30": {"rule": "30min", "pivot_width": 4, "min_swing_atr": 1.30, "max_hold": 96},
    "H1": {"rule": "1h", "pivot_width": 3, "min_swing_atr": 1.20, "max_hold": 96},
    "H4": {"rule": "4h", "pivot_width": 2, "min_swing_atr": 1.10, "max_hold": 60},
}

VARIANTS = ["v1_mechanical", "v2_relaxed", "v2_context"]
ENTRY_MODES = ["B_confirmed", "A_early"]


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
    return tr.rolling(period, min_periods=period).mean()


def discover_m5_files() -> list[Path]:
    files = sorted(DATA_ROOT.rglob("USDJPY_M5_*.csv"))
    return [p for p in files if p.is_file()]


def load_m5() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    coverage = []
    for path in discover_m5_files():
        frame = pd.read_csv(path)
        frame.columns = [c.strip().strip("<>").lower() for c in frame.columns]
        required = {"dtyyyymmdd", "time", "open", "high", "low", "close"}
        if not required.issubset(frame.columns):
            raise ValueError(f"Unsupported CSV format: {path}")

        date_s = frame["dtyyyymmdd"].astype(str)
        time_s = frame["time"].astype(str).str.zfill(4)
        dt = pd.to_datetime(date_s + time_s, format="%Y%m%d%H%M", errors="coerce")
        frame = frame.assign(timestamp=dt)
        frame = frame.dropna(subset=["timestamp"])
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


def timeframe_minutes(label: str) -> int:
    return {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}[label]


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
    if tf_label in {"M5", "M15", "M30"}:
        labels = ["H1", "H4"]
    elif tf_label == "H1":
        labels = ["H4"]
    else:
        labels = ["D1"]

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
        pointer += 1
    return pointer


def line_value(p0: Pivot, p1: Pivot, at_i: int) -> tuple[float, float]:
    bars = max(p1.pivot_i - p0.pivot_i, 1)
    slope = (p1.price - p0.price) / bars
    return p1.price + slope * (at_i - p1.pivot_i), slope


def direction_cost_r(direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - SLIP_PRICE) - (entry + SPREAD_PRICE / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return clean / risk, after / risk


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


def retrace_quality(retrace: float, wave1_bars: int, adjust_bars: int, variant: str) -> tuple[bool, float, str]:
    if not math.isfinite(retrace) or retrace <= 0 or retrace > MAX_RETRACE:
        return False, -2.0, "戻し過不足"
    if variant == "v1_mechanical":
        if 0.50 <= retrace <= 0.886:
            return True, 2.0, "半値以上"
        if 0.382 <= retrace < 0.50:
            return True, 0.5, "浅い戻し"
        return False, -2.0, "戻し不足"

    if 0.618 <= retrace <= 0.886:
        return True, 2.5, "61.8%以上"
    if 0.50 <= retrace < 0.618 and adjust_bars >= max(3, wave1_bars):
        return True, 1.2, "半値+横軸"
    return False, -1.5, "戻し不足/横軸不足"


def signal_from_pivots(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    entry_mode: str,
    variant: str,
) -> dict | None:
    if len(active) < 6:
        return None

    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    body = float(df["body_ratio"].iloc[i])
    buffer = atr_i * BREAK_BUFFER_ATR
    ema_slope = float(df["ema100_slope"].iloc[i])
    p = active[-6:]
    kinds = "".join(x.kind for x in p)

    if kinds == "LHLHLH":
        direction = "long"
        l0, h1, l2, h3, l4, h5 = p
        wave1 = h1.price - l0.price
        if wave1 <= atr_i * MIN_WAVE1_ATR:
            return None
        tl_now, tl_slope = line_value(h1, h3, i)
        line_break = close > tl_now + buffer and prev_close <= tl_now + atr_i * 0.20
        a_level = h3.price
        b_level = h5.price
        a_break = close > a_level + buffer
        b_break = close > b_level + buffer and prev_close <= b_level + buffer
        retrace = (h1.price - l4.price) / wave1
        wave1_bars = max(h1.pivot_i - l0.pivot_i, 1)
        adjust_bars = max(l4.pivot_i - h1.pivot_i, 1)
        right_shoulder_ok = l4.price >= l2.price - atr_i * 0.75
        target = l4.price + wave1 * 0.50
        stop = l4.price - atr_i * STOP_BUFFER_ATR
        trigger = b_level if entry_mode == "B_confirmed" else max(a_level, tl_now)
        trigger_ok = b_break if entry_mode == "B_confirmed" else line_break and a_break
        momentum_ok = h5.price > h3.price
        structure_note = f"{l0.pivot_i}-{h1.pivot_i}-{l2.pivot_i}-{h3.pivot_i}-{l4.pivot_i}-{h5.pivot_i}"
    elif kinds == "HLHLHL":
        direction = "short"
        h0, l1, h2, l3, h4, l5 = p
        wave1 = h0.price - l1.price
        if wave1 <= atr_i * MIN_WAVE1_ATR:
            return None
        tl_now, tl_slope = line_value(l1, l3, i)
        line_break = close < tl_now - buffer and prev_close >= tl_now - atr_i * 0.20
        a_level = l3.price
        b_level = l5.price
        a_break = close < a_level - buffer
        b_break = close < b_level - buffer and prev_close >= b_level - buffer
        retrace = (h4.price - l1.price) / wave1
        wave1_bars = max(l1.pivot_i - h0.pivot_i, 1)
        adjust_bars = max(h4.pivot_i - l1.pivot_i, 1)
        right_shoulder_ok = h4.price <= h2.price + atr_i * 0.75
        target = h4.price - wave1 * 0.50
        stop = h4.price + atr_i * STOP_BUFFER_ATR
        trigger = b_level if entry_mode == "B_confirmed" else min(a_level, tl_now)
        trigger_ok = b_break if entry_mode == "B_confirmed" else line_break and a_break
        momentum_ok = l5.price < l3.price
        structure_note = f"{h0.pivot_i}-{l1.pivot_i}-{h2.pivot_i}-{l3.pivot_i}-{h4.pivot_i}-{l5.pivot_i}"
    else:
        return None

    if not trigger_ok:
        return None
    if direction == "long" and (close <= stop or target <= close):
        return None
    if direction == "short" and (close >= stop or target >= close):
        return None

    retrace_ok, retrace_score, retrace_note = retrace_quality(retrace, wave1_bars, adjust_bars, variant)
    if not retrace_ok:
        return None

    align, oppose, upper_notes = upper_context(df, i, direction)
    if variant == "v2_context" and (align < 1 or oppose > 0):
        return None

    score = 0.0
    reasons: list[str] = []
    if line_break:
        score += 2
        reasons.append("斜め抜け")
    if a_break:
        score += 2
        reasons.append("A抜け")
    if b_break:
        score += 2
        reasons.append("B抜け")
    score += retrace_score
    reasons.append(retrace_note)
    if right_shoulder_ok:
        score += 1
        reasons.append("右肩維持")
    if body >= (0.40 if variant != "v1_mechanical" else 0.45):
        score += 1
        reasons.append("実体ブレイク")
    if (direction == "long" and ema_slope > 0) or (direction == "short" and ema_slope < 0):
        score += 0.5
        reasons.append("EMA100順")
    if momentum_ok:
        score += 1
        reasons.append("右側の波更新")
    if align:
        score += min(2, align)
        reasons.append(f"上位足{align}順")
    if oppose:
        score -= oppose
        reasons.append(f"上位足{oppose}逆")

    minimum = 5.0 if variant == "v1_mechanical" else 7.0 if variant == "v2_relaxed" else 8.0
    if score < minimum:
        return None

    grade = "normal" if score >= minimum + 1.5 else "half"
    risk_weight = 1.0 if grade == "normal" else 0.5
    return {
        "variant": variant,
        "entry_mode": entry_mode,
        "direction": direction,
        "grade": grade,
        "risk_weight": risk_weight,
        "score": score,
        "reasons": ",".join(reasons),
        "upper_context": upper_notes,
        "trigger_level": trigger,
        "a_level": a_level,
        "b_level": b_level,
        "trendline": tl_now,
        "trendline_slope_atr": tl_slope / atr_i,
        "retrace": retrace,
        "wave1_bars": wave1_bars,
        "adjust_bars": adjust_bars,
        "stop": stop,
        "target_half": target,
        "signal_body_ratio": body,
        "pivots": structure_note,
    }


def simulate_trade(df: pd.DataFrame, sig: dict, signal_i: int, max_hold_bars: int) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    target = float(sig["target_half"])
    if direction == "long":
        risk = entry - stop
        reward = target - entry
    else:
        risk = stop - entry
        reward = entry - target
    if risk <= 0 or reward <= 0 or reward / risk < 1.0:
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
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break
    r_clean, r_cost = direction_cost_r(direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "planned_rr": reward / risk,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_cost,
        "weighted_r_after_cost": r_cost * float(sig["risk_weight"]),
    }


def run_timeframe(df: pd.DataFrame, tf_label: str, config: dict) -> pd.DataFrame:
    pivots = build_confirmed_pivots(df, config["pivot_width"], config["min_swing_atr"])
    rows: list[dict] = []
    for variant in VARIANTS:
        for entry_mode in ENTRY_MODES:
            active: list[Pivot] = []
            pointer = 0
            in_pos_until = -1
            for i in range(2, len(df) - 1):
                pointer = pivots_until(pivots, pointer, i, active)
                ts = df.index[i]
                if ts < START or ts > END or holiday_market(ts) or i <= in_pos_until:
                    continue
                sig = signal_from_pivots(df, i, active, entry_mode, variant)
                if sig is None:
                    continue
                trade = simulate_trade(df, sig, i, config["max_hold"])
                if trade is None:
                    continue
                rows.append({"symbol": "USDJPY", "timeframe": tf_label, "signal_time": ts, **sig, **trade})
                in_pos_until = int(df.index.get_loc(trade["exit_time"]))
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
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


def diagnostics(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    specs = [
        ("retrace", pd.cut(trades["retrace"], [0, 0.5, 0.618, 0.764, 0.886, 0.95, 2], include_lowest=True)),
        ("planned_rr", pd.cut(trades["planned_rr"], [0, 1.2, 1.6, 2.2, 3.5, 99], include_lowest=True)),
        ("adjust_bars", pd.cut(trades["adjust_bars"], [0, 5, 12, 24, 48, 9999], include_lowest=True)),
        (
            "trendline_slope_atr",
            pd.cut(trades["trendline_slope_atr"].abs(), [0, 0.05, 0.12, 0.25, 0.50, 99], include_lowest=True),
        ),
        ("body_ratio", pd.cut(trades["signal_body_ratio"], [0, 0.25, 0.45, 0.65, 1.0], include_lowest=True)),
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
    trades: pd.DataFrame,
    coverage: pd.DataFrame,
    overall: pd.DataFrame,
    by_tf_variant: pd.DataFrame,
    by_variant_mode: pd.DataFrame,
    oos: pd.DataFrame,
    diag: pd.DataFrame,
) -> None:
    lines = [
        "# USDJPY 5分足 Synapse 手法 再検証",
        "",
        "## 今回の機械定義",
        "",
        "- 目的: 2波から3波への転換を取る",
        "- 転換確認: 斜め1本 + 水平A + 水平B",
        "- A: 調整中の戻り高値/押し安値",
        "- B: 右肩後の戻り高値/押し安値",
        "- `B_confirmed`: B抜けで次足エントリー",
        "- `A_early`: 斜め抜け + A抜けで次足エントリー",
        "- TP: 1波値幅の半値",
        "- SL: 右肩外側 + 0.2ATR",
        "- v2では、半値以上の戻し、横軸、上位足方向、実体ブレイク、RRを重視",
        "",
        "## 定義の限界",
        "",
        "チャット履歴の裁量要素である、斜め半値、NV、チャネル乖離、最大調整波の階層判断、",
        "見た目123の達成感までは完全には再現していません。今回の結果は“検証可能な土台”です。",
        "",
        "## データ品質",
        "",
        markdown_table(coverage, 30),
        "",
        "## 全体",
        "",
        markdown_table(overall, 30),
        "",
        "## 時間足 x 定義",
        "",
        markdown_table(by_tf_variant, 100),
        "",
        "## 定義 x エントリー方式",
        "",
        markdown_table(by_variant_mode, 80),
        "",
        "## OOS 2025-2026",
        "",
        markdown_table(oos, 100),
        "",
        "## 条件診断",
        "",
        markdown_table(diag.sort_values(["feature", "total_r"], ascending=[True, False]), 120),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_timeframe_variant.csv`",
        "- `summary_by_variant_mode.csv`",
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

    coverage_rows = [coverage]
    tf_rows = []
    for label, frame in datasets.items():
        if label == "D1":
            continue
        tf_rows.append({"file": f"RESAMPLED_{label}", "rows_raw": len(frame), "first": frame.index.min(), "last": frame.index.max()})
    coverage_rows.append(pd.DataFrame(tf_rows))
    coverage = pd.concat(coverage_rows, ignore_index=True)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    all_rows = []
    for label, config in TIMEFRAME_CONFIGS.items():
        rows = run_timeframe(datasets[label], label, config)
        if not rows.empty:
            all_rows.append(rows)

    if not all_rows:
        (OUT_DIR / "report_ja.md").write_text("# USDJPY 5分足 Synapse 手法 再検証\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades = pd.concat(all_rows, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col])
    trades["sample"] = np.where(trades["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    trades = trades.sort_values(["entry_time", "timeframe", "variant", "entry_mode"]).reset_index(drop=True)
    trades.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades, ["symbol"])
    weighted = summarize(trades, ["symbol"], "weighted_r_after_cost")
    overall.insert(1, "risk_model", "all=1R")
    weighted.insert(1, "risk_model", "normal=1R half=0.5R")
    overall = pd.concat([overall, weighted], ignore_index=True)
    by_tf_variant = summarize(trades, ["timeframe", "variant"])
    by_variant_mode = summarize(trades, ["variant", "entry_mode"])
    oos = summarize(trades, ["sample", "timeframe", "variant"])
    diag = diagnostics(trades)

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_tf_variant.to_csv(OUT_DIR / "summary_by_timeframe_variant.csv", index=False)
    by_variant_mode.to_csv(OUT_DIR / "summary_by_variant_mode.csv", index=False)
    oos.to_csv(OUT_DIR / "summary_oos.csv", index=False)
    diag.to_csv(OUT_DIR / "diagnostics.csv", index=False)
    write_report(trades, coverage, overall, by_tf_variant, by_variant_mode, oos, diag)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nOverall")
    print(overall.to_string(index=False))
    print("\nBy timeframe x variant")
    print(by_tf_variant.to_string(index=False))
    print("\nOOS")
    print(oos.to_string(index=False))


if __name__ == "__main__":
    main()

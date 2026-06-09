#!/usr/bin/env python3
"""
MTF pullback -> lower timeframe reversal validation.

Research question:
Does waiting for a lower-timeframe reversal inside a higher-timeframe pullback
produce shallower MAE and larger MFE than entering the pullback without that
reversal confirmation?

This is intentionally mechanical. It does not decide GO/NO-GO by visual feel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import add_indicators, load_instrument, markdown_table, resample_ohlc


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "mtf_pullback_lower_tf_reversal_2026-06-09"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["USDJPY", "GBPJPY", "XAUUSD"]
START = pd.Timestamp("2020-01-01")
END = pd.Timestamp("2026-06-08 23:59:59")

# Local source data is H1. H4/D1 are resampled from it.
MTF_PAIRS = [
    {"htf": "D1", "mid": "H4", "ltf": "H1"},
    {"htf": "H4", "mid": "H1", "ltf": "H1"},
]

TF_DELTA = {
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    "D1": pd.Timedelta(days=1),
}

HTF_PIVOT_WIDTH = {"D1": 2, "H4": 3}
LTF_PIVOT_WIDTH = {"H1": 3}
HTF_MIN_SWING_ATR = {"D1": 0.45, "H4": 0.55}
LTF_MIN_SWING_ATR = {"H1": 0.35}

PULLBACK_ATR_MULT = 1.5
LEVEL_TOUCH_ATR_MULT = 0.5
SL_BUFFER_ATR = 0.25
RR = 2.0
FORWARD_BARS = [24, 48, 120]
REVERSAL_LOOKAHEAD_BARS = {"D1": 240, "H4": 120}


@dataclass(frozen=True)
class Pivot:
    pivot_i: int
    confirm_i: int
    kind: str
    price: float
    atr: float
    pivot_time: pd.Timestamp
    confirm_time: pd.Timestamp


def finite_price(value: float) -> bool:
    return math.isfinite(float(value))


def build_pivots(df: pd.DataFrame, timeframe: str, width: int, min_swing_atr: float) -> list[Pivot]:
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    atrs = df["atr"].to_numpy(dtype=float)
    idx = list(df.index)
    raw: list[Pivot] = []

    for i in range(width, len(df) - width):
        if not finite_price(atrs[i]) or atrs[i] <= 0:
            continue
        hwin = highs[i - width : i + width + 1]
        lwin = lows[i - width : i + width + 1]
        is_high = highs[i] >= np.nanmax(hwin)
        is_low = lows[i] <= np.nanmin(lwin)
        confirm_i = i + width
        if confirm_i >= len(df):
            continue
        confirm_time = idx[confirm_i] + TF_DELTA[timeframe]
        if is_high and not is_low:
            raw.append(Pivot(i, confirm_i, "H", float(highs[i]), float(atrs[i]), idx[i], confirm_time))
        elif is_low and not is_high:
            raw.append(Pivot(i, confirm_i, "L", float(lows[i]), float(atrs[i]), idx[i], confirm_time))

    raw.sort(key=lambda p: (p.pivot_i, p.confirm_i))
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
        threshold = max(p.atr, last.atr) * min_swing_atr
        if abs(p.price - last.price) >= threshold:
            pivots.append(p)
    return pivots


def has_higher_high(pivots: list[Pivot], current_i: int, lookback: int = 20) -> bool:
    highs = [p for p in pivots if p.kind == "H" and p.confirm_i <= current_i and p.pivot_i >= current_i - lookback]
    return any(b.price > a.price for a, b in zip(highs, highs[1:]))


def has_lower_low(pivots: list[Pivot], current_i: int, lookback: int = 20) -> bool:
    lows = [p for p in pivots if p.kind == "L" and p.confirm_i <= current_i and p.pivot_i >= current_i - lookback]
    return any(b.price < a.price for a, b in zip(lows, lows[1:]))


def trend_ok(df: pd.DataFrame, pivots: list[Pivot], direction: str, confirm_i: int) -> tuple[bool, str]:
    if confirm_i < 20 or confirm_i >= len(df):
        return False, "insufficient_sma20"
    close = float(df["close"].iloc[confirm_i])
    sma20 = float(df["sma20"].iloc[confirm_i])
    if not finite_price(sma20):
        return False, "sma20_nan"
    if direction == "long":
        hh = has_higher_high(pivots, confirm_i)
        return bool(close > sma20 and hh), f"close_gt_sma20={close > sma20};hh20={hh}"
    ll = has_lower_low(pivots, confirm_i)
    return bool(close < sma20 and ll), f"close_lt_sma20={close < sma20};ll20={ll}"


def previous_same_kind_level(pivots: list[Pivot], before_i: int, kind: str) -> float | None:
    prev = [p for p in pivots if p.kind == kind and p.pivot_i < before_i]
    if not prev:
        return None
    return float(prev[-1].price)


def pullback_b_ok(
    df: pd.DataFrame,
    pivots: list[Pivot],
    start: Pivot,
    end: Pivot,
    direction: str,
) -> tuple[bool, str, float]:
    atr_value = float(df["atr"].iloc[end.confirm_i])
    if not finite_price(atr_value) or atr_value <= 0:
        return False, "atr_nan", math.nan

    if direction == "long":
        move = start.price - end.price
        prev_level = previous_same_kind_level(pivots, start.pivot_i, "L")
        current_extreme = end.price
    else:
        move = end.price - start.price
        prev_level = previous_same_kind_level(pivots, start.pivot_i, "H")
        current_extreme = end.price

    reasons = []
    if move >= atr_value * PULLBACK_ATR_MULT:
        reasons.append(f"leg_ge_{PULLBACK_ATR_MULT}atr")
    if prev_level is not None and abs(current_extreme - prev_level) <= atr_value * LEVEL_TOUCH_ATR_MULT:
        reasons.append(f"horizontal_touch_le_{LEVEL_TOUCH_ATR_MULT}atr")
    sma20 = float(df["sma20"].iloc[end.confirm_i])
    if finite_price(sma20) and abs(current_extreme - sma20) <= atr_value * LEVEL_TOUCH_ATR_MULT:
        reasons.append(f"sma20_touch_le_{LEVEL_TOUCH_ATR_MULT}atr")

    return bool(reasons), "+".join(reasons) if reasons else "no_b_rule", move / atr_value


def first_bar_at_or_after(df: pd.DataFrame, ts: pd.Timestamp) -> int | None:
    pos = int(df.index.searchsorted(ts, side="left"))
    if pos >= len(df):
        return None
    return pos


def max_time_from_bars(df: pd.DataFrame, start_time: pd.Timestamp, bars: int) -> pd.Timestamp:
    pos = first_bar_at_or_after(df, start_time)
    if pos is None:
        return start_time
    end_i = min(len(df) - 1, pos + bars)
    return pd.Timestamp(df.index[end_i])


def count_decreasing_steps(highs: list[Pivot]) -> int:
    return sum(1 for a, b in zip(highs, highs[1:]) if b.price < a.price)


def count_increasing_steps(lows: list[Pivot]) -> int:
    return sum(1 for a, b in zip(lows, lows[1:]) if b.price > a.price)


def find_ltf_reversal(
    ltf: pd.DataFrame,
    ltf_pivots: list[Pivot],
    direction: str,
    window_start: pd.Timestamp,
    extreme_time: pd.Timestamp,
    deadline: pd.Timestamp,
) -> dict | None:
    start_i = first_bar_at_or_after(ltf, window_start)
    deadline_i = first_bar_at_or_after(ltf, deadline)
    if start_i is None or deadline_i is None or deadline_i <= start_i:
        return None

    close = ltf["close"].to_numpy(dtype=float)
    highs = [p for p in ltf_pivots if p.kind == "H" and window_start <= p.pivot_time <= deadline]
    lows = [p for p in ltf_pivots if p.kind == "L" and window_start <= p.pivot_time <= deadline]

    if direction == "long":
        for h_idx in range(2, len(highs)):
            seq = highs[: h_idx + 1]
            latest3 = seq[-3:]
            if count_decreasing_steps(latest3) < 2:
                continue
            lh = latest3[-1]
            swing_lows = [p for p in lows if p.confirm_time >= lh.confirm_time and p.confirm_time >= extreme_time]
            if not swing_lows:
                continue
            swing = swing_lows[0]
            scan_start = first_bar_at_or_after(ltf, swing.confirm_time)
            if scan_start is None:
                continue
            for i in range(scan_start, deadline_i + 1):
                if close[i] > lh.price:
                    return {
                        "trigger_i": i,
                        "trigger_time": pd.Timestamp(ltf.index[i]) + TF_DELTA["H1"],
                        "trigger_level": lh.price,
                        "reversal_swing_price": swing.price,
                        "reversal_swing_time": swing.pivot_time,
                        "zigzag_count": count_decreasing_steps(latest3),
                        "reversal_note": "2step_lower_high_close_break",
                    }
    else:
        for l_idx in range(2, len(lows)):
            seq = lows[: l_idx + 1]
            latest3 = seq[-3:]
            if count_increasing_steps(latest3) < 2:
                continue
            hl = latest3[-1]
            swing_highs = [p for p in highs if p.confirm_time >= hl.confirm_time and p.confirm_time >= extreme_time]
            if not swing_highs:
                continue
            swing = swing_highs[0]
            scan_start = first_bar_at_or_after(ltf, swing.confirm_time)
            if scan_start is None:
                continue
            for i in range(scan_start, deadline_i + 1):
                if close[i] < hl.price:
                    return {
                        "trigger_i": i,
                        "trigger_time": pd.Timestamp(ltf.index[i]) + TF_DELTA["H1"],
                        "trigger_level": hl.price,
                        "reversal_swing_price": swing.price,
                        "reversal_swing_time": swing.pivot_time,
                        "zigzag_count": count_increasing_steps(latest3),
                        "reversal_note": "2step_higher_low_close_break",
                    }
    return None


def simulate_event(
    ltf: pd.DataFrame,
    direction: str,
    entry_time: pd.Timestamp,
    entry_anchor_price: float,
    sl_anchor_price: float,
    sl_buffer_atr_source_i: int,
    group: str,
) -> dict | None:
    entry_i = first_bar_at_or_after(ltf, entry_time)
    if entry_i is None or entry_i >= len(ltf) - 2:
        return None

    entry_price = float(ltf["open"].iloc[entry_i])
    atr_i = min(max(sl_buffer_atr_source_i, 0), len(ltf) - 1)
    atr_value = float(ltf["atr"].iloc[atr_i])
    if not finite_price(atr_value) or atr_value <= 0:
        atr_value = float(ltf["atr"].iloc[entry_i])
    if not finite_price(atr_value) or atr_value <= 0:
        return None

    if direction == "long":
        sl_price = sl_anchor_price - atr_value * SL_BUFFER_ATR
        risk = entry_price - sl_price
        if risk <= 0:
            return None
        tp_price = entry_price + risk * RR
    else:
        sl_price = sl_anchor_price + atr_value * SL_BUFFER_ATR
        risk = sl_price - entry_price
        if risk <= 0:
            return None
        tp_price = entry_price - risk * RR

    out: dict[str, float | int | str | pd.Timestamp] = {
        "entry_i": entry_i,
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "risk_price": risk,
        "entry_anchor_price": entry_anchor_price,
    }

    for bars in FORWARD_BARS:
        end_i = min(len(ltf), entry_i + bars)
        window = ltf.iloc[entry_i:end_i]
        if window.empty:
            out[f"mfe_{bars}h"] = math.nan
            out[f"mae_{bars}h"] = math.nan
            continue
        if direction == "long":
            out[f"mfe_{bars}h"] = (float(window["high"].max()) - entry_price) / risk
            out[f"mae_{bars}h"] = (entry_price - float(window["low"].min())) / risk
        else:
            out[f"mfe_{bars}h"] = (entry_price - float(window["low"].min())) / risk
            out[f"mae_{bars}h"] = (float(window["high"].max()) - entry_price) / risk

    outcome = 0
    exit_reason = "not_reached_120h"
    exit_i = min(len(ltf) - 1, entry_i + 120)
    exit_price = float(ltf["close"].iloc[exit_i])
    r_result = (exit_price - entry_price) / risk if direction == "long" else (entry_price - exit_price) / risk

    for i in range(entry_i, min(len(ltf), entry_i + 120)):
        hi = float(ltf["high"].iloc[i])
        lo = float(ltf["low"].iloc[i])
        if direction == "long":
            hit_sl = lo <= sl_price
            hit_tp = hi >= tp_price
        else:
            hit_sl = hi >= sl_price
            hit_tp = lo <= tp_price
        if hit_sl or hit_tp:
            exit_i = i
            if hit_sl:
                outcome = -1
                exit_reason = "SL_first_same_bar" if hit_tp else "SL"
                exit_price = sl_price
                r_result = -1.0
            else:
                outcome = 1
                exit_reason = "TP_2R"
                exit_price = tp_price
                r_result = RR
            break

    out.update(
        {
            "outcome": outcome,
            "r_result": r_result,
            "exit_reason": exit_reason,
            "exit_time": pd.Timestamp(ltf.index[exit_i]) + TF_DELTA["H1"],
            "exit_price": exit_price,
            "group": group,
        }
    )
    return out


def build_symbol_events(symbol: str) -> tuple[list[dict], dict]:
    raw = load_instrument(symbol)
    raw = raw[(raw.index >= START - pd.Timedelta(days=400)) & (raw.index <= END)]
    ltf = add_indicators(resample_ohlc(raw, "H1"))
    ltf["sma20"] = ltf["close"].rolling(20).mean()
    ltf_pivots = build_pivots(ltf, "H1", LTF_PIVOT_WIDTH["H1"], LTF_MIN_SWING_ATR["H1"])

    rows: list[dict] = []
    coverage = {
        "symbol": symbol,
        "h1_start": str(ltf.index.min()),
        "h1_end": str(ltf.index.max()),
        "h1_bars": len(ltf),
    }

    for pair in MTF_PAIRS:
        htf_name = pair["htf"]
        htf = add_indicators(resample_ohlc(raw, htf_name))
        htf["sma20"] = htf["close"].rolling(20).mean()
        htf_pivots = build_pivots(
            htf,
            htf_name,
            HTF_PIVOT_WIDTH[htf_name],
            HTF_MIN_SWING_ATR[htf_name],
        )
        idx = list(htf.index)
        for p_i in range(len(htf_pivots) - 1):
            start_p = htf_pivots[p_i]
            end_p = htf_pivots[p_i + 1]
            next_p = htf_pivots[p_i + 2] if p_i + 2 < len(htf_pivots) else None
            direction = ""
            if start_p.kind == "H" and end_p.kind == "L":
                direction = "long"
            elif start_p.kind == "L" and end_p.kind == "H":
                direction = "short"
            else:
                continue

            event_time = end_p.confirm_time
            if event_time < START or event_time > END:
                continue

            ok_trend, trend_note = trend_ok(htf, htf_pivots, direction, end_p.confirm_i)
            if not ok_trend:
                continue
            ok_b, b_note, pullback_atr = pullback_b_ok(htf, htf_pivots, start_p, end_p, direction)
            if not ok_b:
                continue

            deadline = max_time_from_bars(ltf, end_p.confirm_time, REVERSAL_LOOKAHEAD_BARS[htf_name])
            if next_p is not None:
                deadline = min(deadline, next_p.confirm_time)
            reversal = find_ltf_reversal(
                ltf,
                ltf_pivots,
                direction,
                start_p.pivot_time,
                end_p.confirm_time,
                deadline,
            )

            if reversal is not None:
                entry_time = reversal["trigger_time"]
                anchor_i = first_bar_at_or_after(ltf, reversal["reversal_swing_time"])
                if anchor_i is None:
                    continue
                trade = simulate_event(
                    ltf,
                    direction,
                    entry_time,
                    float(reversal["trigger_level"]),
                    float(reversal["reversal_swing_price"]),
                    anchor_i,
                    "GO",
                )
                if trade is None:
                    continue
                reversal_trigger_date_ltf = reversal["trigger_time"]
                reversal_note = reversal["reversal_note"]
                zigzag_count = reversal["zigzag_count"]
                sl_anchor = reversal["reversal_swing_price"]
            else:
                entry_time = end_p.confirm_time
                anchor_i = first_bar_at_or_after(ltf, entry_time)
                if anchor_i is None:
                    continue
                trade = simulate_event(
                    ltf,
                    direction,
                    entry_time,
                    end_p.price,
                    end_p.price,
                    anchor_i,
                    "NO-GO",
                )
                if trade is None:
                    continue
                reversal_trigger_date_ltf = pd.NaT
                reversal_note = "no_ltf_reversal_before_deadline"
                zigzag_count = 0
                sl_anchor = end_p.price

            rows.append(
                {
                    "symbol": symbol,
                    "htf": htf_name,
                    "mid": pair["mid"],
                    "ltf": pair["ltf"],
                    "direction": direction,
                    "group": trade["group"],
                    "event_date_htf": event_time,
                    "pullback_start": start_p.pivot_time,
                    "pullback_low/high": end_p.price,
                    "pullback_extreme_time": end_p.pivot_time,
                    "reversal_trigger_date_ltf": reversal_trigger_date_ltf,
                    "entry_time": pd.Timestamp(ltf.index[int(trade["entry_i"])]) + TF_DELTA["H1"],
                    "entry_price": trade["entry_price"],
                    "sl_price": trade["sl_price"],
                    "tp_price": trade["tp_price"],
                    "mfe_24h": trade["mfe_24h"],
                    "mfe_48h": trade["mfe_48h"],
                    "mfe_120h": trade["mfe_120h"],
                    "mae_24h": trade["mae_24h"],
                    "mae_48h": trade["mae_48h"],
                    "mae_120h": trade["mae_120h"],
                    "outcome": trade["outcome"],
                    "r_result": trade["r_result"],
                    "exit_time": trade["exit_time"],
                    "exit_reason": trade["exit_reason"],
                    "risk_price": trade["risk_price"],
                    "pullback_atr": pullback_atr,
                    "zigzag_count": zigzag_count,
                    "sl_anchor_price": sl_anchor,
                    "notes": f"{b_note};{trend_note};{reversal_note};deadline={deadline}",
                }
            )

    return rows, coverage


def evenly_sample(group: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    group = group.sort_values(["event_date_htf", "entry_time"]).reset_index(drop=True)
    if len(group) <= n:
        return group
    positions = np.linspace(0, len(group) - 1, n).round().astype(int)
    return group.iloc[sorted(set(positions))].head(n)


def sample_events(all_events: pd.DataFrame) -> pd.DataFrame:
    sampled = []
    for symbol in SYMBOLS:
        for group_name in ["GO", "NO-GO"]:
            subset = all_events[(all_events["symbol"].eq(symbol)) & (all_events["group"].eq(group_name))]
            if subset.empty:
                continue
            sampled.append(evenly_sample(subset, 10))
    if not sampled:
        return pd.DataFrame()
    return pd.concat(sampled, ignore_index=True).sort_values(["symbol", "group", "event_date_htf"])


def profit_factor(r: pd.Series) -> float:
    positive = float(r[r > 0].sum())
    negative = float(r[r < 0].sum())
    if negative == 0:
        return math.inf if positive > 0 else math.nan
    return positive / abs(negative)


def summarize_group(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame()
    for keys, g in df.groupby(cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        r = g["r_result"].astype(float)
        row = dict(zip(cols, keys))
        row.update(
            {
                "n": len(g),
                "avg_mae_24h": float(g["mae_24h"].mean()),
                "avg_mae_48h": float(g["mae_48h"].mean()),
                "avg_mae_120h": float(g["mae_120h"].mean()),
                "avg_mfe_24h": float(g["mfe_24h"].mean()),
                "avg_mfe_48h": float(g["mfe_48h"].mean()),
                "avg_mfe_120h": float(g["mfe_120h"].mean()),
                "win_rate_2r": float((g["outcome"].astype(int) == 1).mean() * 100),
                "sl_rate": float((g["outcome"].astype(int) == -1).mean() * 100),
                "pf": profit_factor(r),
                "avg_r": float(r.mean()),
                "total_r": float(r.sum()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def comparison_table(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    overall = summary.set_index("group")
    metrics = [
        ("n", "サンプル数"),
        ("avg_mae_24h", "平均MAE 24h"),
        ("avg_mae_48h", "平均MAE 48h"),
        ("avg_mae_120h", "平均MAE 120h"),
        ("avg_mfe_24h", "平均MFE 24h"),
        ("avg_mfe_48h", "平均MFE 48h"),
        ("avg_mfe_120h", "平均MFE 120h"),
        ("win_rate_2r", "2R到達率"),
        ("sl_rate", "SL到達率"),
        ("pf", "PF"),
        ("avg_r", "平均R"),
    ]
    rows = []
    for key, label in metrics:
        rows.append(
            {
                "指標": label,
                "GO": overall.loc["GO", key] if "GO" in overall.index else math.nan,
                "NO-GO": overall.loc["NO-GO", key] if "NO-GO" in overall.index else math.nan,
            }
        )
    return pd.DataFrame(rows)


def judge(summary: pd.DataFrame) -> str:
    if summary.empty or set(summary["group"]) != {"GO", "NO-GO"}:
        return "判定不能"
    s = summary.set_index("group")
    mae_ok = float(s.loc["GO", "avg_mae_120h"]) < float(s.loc["NO-GO", "avg_mae_120h"])
    mfe_ok = float(s.loc["GO", "avg_mfe_120h"]) >= float(s.loc["NO-GO", "avg_mfe_120h"])
    win_ok = float(s.loc["GO", "win_rate_2r"]) > float(s.loc["NO-GO", "win_rate_2r"])
    score = sum([mae_ok, mfe_ok, win_ok])
    if score == 3:
        return "支持"
    if score >= 1:
        return "部分支持"
    return "棄却"


def format_float_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else "inf" if math.isinf(float(x)) else round(float(x), 3))
    return out


def build_report(
    sampled: pd.DataFrame,
    all_events: pd.DataFrame,
    coverage: pd.DataFrame,
    summary: pd.DataFrame,
    by_symbol: pd.DataFrame,
) -> str:
    verdict = judge(summary)
    verdict_note = "GO/NO-GOの両群が揃わず、判定保留。"
    if not summary.empty and set(summary["group"]) == {"GO", "NO-GO"}:
        s_for_note = summary.set_index("group")
        pf_weaker = float(s_for_note.loc["GO", "pf"]) < float(s_for_note.loc["NO-GO", "pf"])
        avg_r_weaker = float(s_for_note.loc["GO", "avg_r"]) < float(s_for_note.loc["NO-GO", "avg_r"])
        avg_r_negative = float(s_for_note.loc["GO", "avg_r"]) < 0
        if verdict == "支持" and (pf_weaker or avg_r_weaker or avg_r_negative):
            verdict_note = (
                "主仮説の3条件（MAE低下、MFE増加、2R到達率改善）は満たした。"
                "ただしPF/平均Rは未改善なので、売買ルールとしてはまだ未採用。"
            )
        elif verdict == "支持":
            verdict_note = "主仮説と売買成績の両方が改善。Pine Event scanner化へ進める候補。"
        elif verdict == "部分支持":
            verdict_note = "一部の方向だけ改善。銘柄別・時間足別に分けて再検証が必要。"
        else:
            verdict_note = "今回の操作定義では主仮説を支持できない。条件定義から戻す。"
    comp = comparison_table(summary)
    counts = sampled.groupby(["symbol", "group"]).size().reset_index(name="n") if not sampled.empty else pd.DataFrame()
    missing_refs = [
        "docs/research/higher_tf_pullback_lower_tf_reversal_2026-06-08.md",
        "docs/trade_diary/practice/entries/2026-06-04_gbpjpy_nagekiri_signal_buy.md",
        "docs/trade_diary/reference/signal_review_protocol.md",
        "docs/research/市場心理図鑑/README.md",
    ]
    missing_existing = [p for p in missing_refs if not (REPO_ROOT / p).exists()]
    total_all = len(all_events)
    total_sampled = len(sampled)

    if verdict == "支持":
        rule_sentence = (
            "HTFの押し目legだけで入らず、LTFで2段階以上の逆方向zigzagが止まり、直近LH/HLを終値で抜けた次足だけを候補にする。"
            "NO-GO型はE01として見送り、Signal Reviewでは「転換確認あり」になるまでENTRYへ進めない。"
        )
    elif verdict == "部分支持":
        rule_sentence = (
            "HTFの押し目legはENTRYではなく観察開始条件に止める。LTFの2段階zigzag停止と直近LH/HL終値ブレイクが出た場合のみCHECKへ進め、"
            "銘柄別にMAE/MFEが改善する方向を確認してからPine化する。"
        )
    else:
        rule_sentence = (
            "今回の定義だけでは転換確認の優位性は不足。HTF押し目legを売買ルール化せず、zigzag本数、ATR倍率、水平線接触条件を再定義する。"
        )

    lines = [
        "## MTF 押し目×転換 検証結果 v0.1",
        "",
        f"### 判定: {verdict}",
        "",
        f"**判定補足:** {verdict_note}",
        "",
        "### 研究の問い",
        "",
        "上位足の押し目legの内部で下位足転換を待つと、転換未確認で飛び乗るよりMAEが浅くMFEが大きくなるか。",
        "",
        "### サンプル数と銘柄内訳",
        "",
        f"- 期間指定: 2020-01-01 から 2026-06-08。ただしローカルOHLCの実データ終端は銘柄により2026-05-19から2026-05-22。",
        f"- 抽出候補: {total_all}件。固定サンプル: {total_sampled}件。",
        "- 固定ペア: D1->H1, H4->H1。M15/M5はこのリポジトリの現在のOHLCソースがH1のため未検証。",
        "- B条件は 1.5ATR以上の押し目leg、または直前水平節目/SMA20から0.5ATR以内の反発で機械判定。",
        "- 同一バーでTP/SL両方に触れた場合は保守的にSL優先。",
        "",
        markdown_table(counts, 20) if not counts.empty else "_No sampled rows._",
        "",
        "### 比較表",
        "",
        markdown_table(format_float_columns(comp), 30) if not comp.empty else "_No summary rows._",
        "",
        "### 銘柄別",
        "",
        markdown_table(format_float_columns(by_symbol), 80) if not by_symbol.empty else "_No rows._",
        "",
        "### 支持条件チェック",
        "",
    ]

    if not summary.empty and set(summary["group"]) == {"GO", "NO-GO"}:
        s = summary.set_index("group")
        lines.extend(
            [
                f"- MAE: GO 120h {s.loc['GO', 'avg_mae_120h']:.3f} vs NO-GO {s.loc['NO-GO', 'avg_mae_120h']:.3f}",
                f"- MFE: GO 120h {s.loc['GO', 'avg_mfe_120h']:.3f} vs NO-GO {s.loc['NO-GO', 'avg_mfe_120h']:.3f}",
                f"- 2R到達率: GO {s.loc['GO', 'win_rate_2r']:.1f}% vs NO-GO {s.loc['NO-GO', 'win_rate_2r']:.1f}%",
                f"- 実運用注意: PF GO {s.loc['GO', 'pf']:.3f} vs NO-GO {s.loc['NO-GO', 'pf']:.3f}、平均R GO {s.loc['GO', 'avg_r']:.3f} vs NO-GO {s.loc['NO-GO', 'avg_r']:.3f}",
            ]
        )
    else:
        lines.append("- GO/NO-GOの両群が揃わず判定不能。")

    lines.extend(
        [
            "",
            "### 操作定義の修正案",
            "",
            "- LTF転換のzigzagは、現行の「3つの高値/安値で2段階」を基本にする。ただし候補不足の銘柄は「2つの高値/安値で1段階」も感度分析する。",
            "- HTF押し目幅 1.5ATR はやや広め。XAUUSDは2.0ATR、JPYクロスは1.2ATRも比較する。",
            "- 水平節目反発は直前pivot同種のみで判定した。次はA/B水平線、SMA20、直近レンジ高安を別列で分ける。",
            "- D1->H1 と H4->H1 は混ぜず、Pine化前に時間足ペアごとの支持/不支持を分ける。",
            "",
            "### 実運用ルール案",
            "",
            rule_sentence,
            "",
            "### Pine 化の可否",
            "",
            "段階4へ進むなら、まずは売買ストラテジーではなく Event scanner としてPine化する。表示は HTF押し目候補、LTF転換確認、NO-GO警告の3種類に分ける。",
            "",
            "### 注意",
            "",
            "- これはローカルOHLCでの機械検証であり、TradingViewの実ブローカー足との完全一致は未確認。",
            "- 参照画像はAI再生成していない。TradingView実スクショだけを使う方針を維持。",
            f"- 参照ドキュメント未配置: {', '.join(missing_existing) if missing_existing else 'なし'}",
            "",
            "### 次のアクション",
            "",
            "1. GO/NO-GOのサンプルCSVをTradingViewで20件だけ目視照合する。",
            "2. M15/M5の実OHLCを追加できるなら、H4->M15/M5で同じ定義を再実行する。",
            "3. GOが支持された銘柄・方向だけ、PineのEvent scannerへ落とす。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    all_rows: list[dict] = []
    coverage_rows: list[dict] = []
    for symbol in SYMBOLS:
        rows, coverage = build_symbol_events(symbol)
        all_rows.extend(rows)
        coverage_rows.append(coverage)

    all_events = pd.DataFrame(all_rows)
    coverage = pd.DataFrame(coverage_rows)
    if all_events.empty:
        raise RuntimeError("No events detected. Check data coverage or scanner thresholds.")

    sampled = sample_events(all_events)
    summary = summarize_group(sampled, ["group"])
    by_symbol = summarize_group(sampled, ["symbol", "group"])
    by_pair = summarize_group(sampled, ["htf", "ltf", "group"])

    date_cols = [
        "event_date_htf",
        "pullback_start",
        "pullback_extreme_time",
        "reversal_trigger_date_ltf",
        "entry_time",
        "exit_time",
    ]
    for frame in [all_events, sampled]:
        for col in date_cols:
            if col in frame.columns:
                frame[col] = pd.to_datetime(frame[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")

    all_events.to_csv(OUT_DIR / "events_all.csv", index=False)
    sampled.to_csv(OUT_DIR / "validation_results_template.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_go_vs_nogo.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_pair.to_csv(OUT_DIR / "summary_by_mtf_pair.csv", index=False)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    report = build_report(sampled, all_events, coverage, summary, by_symbol)
    (OUT_DIR / "REPORT_ja.md").write_text(report, encoding="utf-8")

    print(f"events_all={len(all_events)} sampled={len(sampled)}")
    print(summary.round(3).to_string(index=False))
    print(f"wrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

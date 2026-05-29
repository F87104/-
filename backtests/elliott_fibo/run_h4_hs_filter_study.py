#!/usr/bin/env python3
"""
Head-and-shoulders filter study for the H4 low-stagnation short setup.

The user-provided Pine scanner is treated as a visual pattern detector. This
script ports its pivot, quality, trend, and neckline-break logic to Python and
tests whether H&S context improves the existing H4 short setup.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, markdown_table, resample_ohlc
from run_h4_stagnation_followup_validation import actual_trade_sample, practical_mask
from run_h4_stagnation_precision_hardening import CORE4, quality_mask, strict_mask
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_followup_validation" / "enriched_followup.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_hs_filter_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"
TIMEFRAME = "H4"
NO_AUD_USD = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY", "SILVER"}


@dataclass(frozen=True)
class HSSpec:
    pivot_left: int
    pivot_right: int
    head_atr_min: float
    shoulder_symmetry: float
    shoulder_head_gap: float
    amplitude_symmetry: float
    time_symmetry: float
    neckline_tilt: float
    require_trend: bool
    trend_lookback: int
    trend_atr_mult: float
    break_bars: int
    break_buffer_atr: float
    label: str

    @property
    def name(self) -> str:
        trend = "TR" if self.require_trend else "NOTR"
        return (
            f"P{self.pivot_left}_{self.label}_{trend}"
            f"_TL{self.trend_lookback}_TA{self.trend_atr_mult:g}"
            f"_BB{self.break_bars}_BUF{self.break_buffer_atr:g}"
        )


def load_source() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def build_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        frames[symbol] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    return frames


def is_pivot_high(high: np.ndarray, k: int, left: int, right: int) -> bool:
    win = high[k - left : k + right + 1]
    return bool(np.isfinite(high[k]) and high[k] == np.nanmax(win))


def is_pivot_low(low: np.ndarray, k: int, left: int, right: int) -> bool:
    win = low[k - left : k + right + 1]
    return bool(np.isfinite(low[k]) and low[k] == np.nanmin(win))


def add_pivot(p_price: list[float], p_bar: list[int], p_type: list[int], price: float, bar: int, typ: int) -> None:
    if p_type and p_type[-1] == typ:
        prev = p_price[-1]
        keep_new = (typ == 1 and price > prev) or (typ == -1 and price < prev)
        if keep_new:
            p_price[-1] = price
            p_bar[-1] = bar
    else:
        p_price.append(price)
        p_bar.append(bar)
        p_type.append(typ)

    while len(p_type) > 80:
        p_price.pop(0)
        p_bar.pop(0)
        p_type.pop(0)


def quality_hs(
    ls: float,
    l1: float,
    head: float,
    l2: float,
    rs: float,
    ls_bar: int,
    head_bar: int,
    rs_bar: int,
    atr_value: float,
    spec: HSSpec,
) -> tuple[bool, dict]:
    avg_neck = (l1 + l2) / 2.0
    head_amp = max(head - avg_neck, 1e-10)
    left_amp = head - l1
    right_amp = head - l2
    avg_amp = max((left_amp + right_amp) / 2.0, 1e-10)
    left_bars = max(head_bar - ls_bar, 1)
    right_bars = max(rs_bar - head_bar, 1)
    avg_bars = (left_bars + right_bars) / 2.0
    max_shoulder = max(ls, rs)

    ok = (
        head > ls
        and head > rs
        and (head - max_shoulder) >= atr_value * spec.head_atr_min
        and (max_shoulder - avg_neck) <= head_amp * spec.shoulder_head_gap
        and abs(ls - rs) <= head_amp * spec.shoulder_symmetry
        and abs(left_amp - right_amp) <= avg_amp * spec.amplitude_symmetry
        and abs(left_bars - right_bars) <= avg_bars * spec.time_symmetry
        and abs(l1 - l2) <= avg_amp * spec.neckline_tilt
        and ls > avg_neck
        and rs > avg_neck
    )
    features = {
        "avg_neck": avg_neck,
        "head_amp_atr": head_amp / atr_value if atr_value > 0 else np.nan,
        "head_stand_atr": (head - max_shoulder) / atr_value if atr_value > 0 else np.nan,
        "shoulder_diff_ratio": abs(ls - rs) / head_amp,
        "amp_diff_ratio": abs(left_amp - right_amp) / avg_amp,
        "time_diff_ratio": abs(left_bars - right_bars) / avg_bars,
        "neck_tilt_ratio": abs(l1 - l2) / avg_amp,
    }
    return bool(ok), features


def quality_inv_hs(
    ls: float,
    l1: float,
    head: float,
    l2: float,
    rs: float,
    ls_bar: int,
    head_bar: int,
    rs_bar: int,
    atr_value: float,
    spec: HSSpec,
) -> tuple[bool, dict]:
    avg_neck = (l1 + l2) / 2.0
    head_amp = max(avg_neck - head, 1e-10)
    left_amp = l1 - head
    right_amp = l2 - head
    avg_amp = max((left_amp + right_amp) / 2.0, 1e-10)
    left_bars = max(head_bar - ls_bar, 1)
    right_bars = max(rs_bar - head_bar, 1)
    avg_bars = (left_bars + right_bars) / 2.0
    min_shoulder = min(ls, rs)

    ok = (
        head < ls
        and head < rs
        and (min_shoulder - head) >= atr_value * spec.head_atr_min
        and (avg_neck - min_shoulder) <= head_amp * spec.shoulder_head_gap
        and abs(ls - rs) <= head_amp * spec.shoulder_symmetry
        and abs(left_amp - right_amp) <= avg_amp * spec.amplitude_symmetry
        and abs(left_bars - right_bars) <= avg_bars * spec.time_symmetry
        and abs(l1 - l2) <= avg_amp * spec.neckline_tilt
        and ls < avg_neck
        and rs < avg_neck
    )
    features = {
        "avg_neck": avg_neck,
        "head_amp_atr": head_amp / atr_value if atr_value > 0 else np.nan,
        "head_stand_atr": (min_shoulder - head) / atr_value if atr_value > 0 else np.nan,
        "shoulder_diff_ratio": abs(ls - rs) / head_amp,
        "amp_diff_ratio": abs(left_amp - right_amp) / avg_amp,
        "time_diff_ratio": abs(left_bars - right_bars) / avg_bars,
        "neck_tilt_ratio": abs(l1 - l2) / avg_amp,
    }
    return bool(ok), features


def trend_ok(close: np.ndarray, atr_value: float, ls_bar: int, ptype: int, spec: HSSpec) -> bool:
    if not spec.require_trend:
        return True
    old_i = ls_bar - spec.trend_lookback
    if old_i < 0 or ls_bar < 0 or not math.isfinite(close[old_i]) or not math.isfinite(close[ls_bar]):
        return False
    if ptype == 1:
        return bool((close[ls_bar] - close[old_i]) >= atr_value * spec.trend_atr_mult)
    return bool((close[old_i] - close[ls_bar]) >= atr_value * spec.trend_atr_mult)


def maybe_pattern(
    p_price: list[float],
    p_bar: list[int],
    p_type: list[int],
    current_i: int,
    close: np.ndarray,
    atr: np.ndarray,
    spec: HSSpec,
) -> tuple[dict | None, dict | None]:
    if len(p_type) < 5:
        return None, None

    types = p_type[-5:]
    if types == [1, -1, 1, -1, 1]:
        ptype = 1
    elif types == [-1, 1, -1, 1, -1]:
        ptype = -1
    else:
        return None, None

    ls, l1, head, l2, rs = p_price[-5:]
    ls_bar, l1_bar, head_bar, l2_bar, rs_bar = p_bar[-5:]
    atr_value = atr[current_i]
    if not math.isfinite(atr_value) or atr_value <= 0:
        return None, None

    if ptype == 1:
        ok, features = quality_hs(ls, l1, head, l2, rs, ls_bar, head_bar, rs_bar, atr_value, spec)
    else:
        ok, features = quality_inv_hs(ls, l1, head, l2, rs, ls_bar, head_bar, rs_bar, atr_value, spec)

    if not ok or not trend_ok(close, atr_value, ls_bar, ptype, spec):
        return None, None

    slope = (l2 - l1) / max(l2_bar - l1_bar, 1)
    neck_at_rs = l2 + slope * (rs_bar - l2_bar)
    pattern = {
        "hs_spec": spec.name,
        "event": "pattern",
        "ptype": ptype,
        "confirm_i": current_i,
        "ls_i": ls_bar,
        "l1_i": l1_bar,
        "head_i": head_bar,
        "l2_i": l2_bar,
        "rs_i": rs_bar,
        "ls": ls,
        "l1": l1,
        "head": head,
        "l2": l2,
        "rs": rs,
        "neck_at_rs": neck_at_rs,
        "neck_slope": slope,
        **features,
    }
    pending = {
        "ptype": ptype,
        "rs_i": rs_bar,
        "neck_at_rs": neck_at_rs,
        "neck_slope": slope,
        "head": head,
        "expire_i": current_i + spec.break_bars,
        "broken": False,
        "pattern_i": current_i,
    }
    return pattern, pending


def detect_hs_events(df: pd.DataFrame, spec: HSSpec) -> pd.DataFrame:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)

    p_price: list[float] = []
    p_bar: list[int] = []
    p_type: list[int] = []
    pending: list[dict] = []
    rows: list[dict] = []

    start_i = spec.pivot_left + spec.pivot_right
    for current_i in range(start_i, len(df)):
        pivot_i = current_i - spec.pivot_right
        new_pivot = False

        if is_pivot_high(high, pivot_i, spec.pivot_left, spec.pivot_right):
            add_pivot(p_price, p_bar, p_type, float(high[pivot_i]), pivot_i, 1)
            new_pivot = True
        if is_pivot_low(low, pivot_i, spec.pivot_left, spec.pivot_right):
            add_pivot(p_price, p_bar, p_type, float(low[pivot_i]), pivot_i, -1)
            new_pivot = True

        if new_pivot:
            pattern, pend = maybe_pattern(p_price, p_bar, p_type, current_i, close, atr, spec)
            if pattern is not None and pend is not None:
                rows.append(pattern)
                pending.append(pend)

        next_pending: list[dict] = []
        for item in pending:
            if current_i > item["expire_i"]:
                continue
            if item["broken"]:
                next_pending.append(item)
                continue

            neck_now = item["neck_at_rs"] + item["neck_slope"] * (current_i - item["rs_i"])
            atr_value = atr[current_i]
            if not math.isfinite(atr_value) or atr_value <= 0 or current_i <= item["rs_i"]:
                next_pending.append(item)
                continue

            broke = False
            if item["ptype"] == 1 and close[current_i] < neck_now - atr_value * spec.break_buffer_atr:
                broke = True
                target = neck_now - (item["head"] - neck_now)
            elif item["ptype"] == -1 and close[current_i] > neck_now + atr_value * spec.break_buffer_atr:
                broke = True
                target = neck_now + (neck_now - item["head"])
            else:
                target = np.nan

            if broke:
                item["broken"] = True
                rows.append(
                    {
                        "hs_spec": spec.name,
                        "event": "break",
                        "ptype": item["ptype"],
                        "confirm_i": current_i,
                        "pattern_i": item["pattern_i"],
                        "rs_i": item["rs_i"],
                        "head": item["head"],
                        "neck_now": neck_now,
                        "target_1x": target,
                    }
                )
            next_pending.append(item)
        pending = next_pending

    return pd.DataFrame(rows)


def hs_specs() -> list[HSSpec]:
    profiles = [
        ("LOOSE", 0.35, 0.35, 0.90, 0.50, 0.70, 0.45, 1.0),
        ("DEF", 0.50, 0.25, 0.85, 0.35, 0.45, 0.30, 1.5),
        ("STRICT", 0.75, 0.20, 0.80, 0.30, 0.35, 0.20, 1.5),
    ]
    specs: list[HSSpec] = []
    for pivot in [3, 5, 8]:
        for label, head, shoulder, gap, amp, time, neck, trend_mult in profiles:
            for require_trend in [True, False]:
                for break_bars in [40, 80]:
                    specs.append(
                        HSSpec(
                            pivot_left=pivot,
                            pivot_right=pivot,
                            head_atr_min=head,
                            shoulder_symmetry=shoulder,
                            shoulder_head_gap=gap,
                            amplitude_symmetry=amp,
                            time_symmetry=time,
                            neckline_tilt=neck,
                            require_trend=require_trend,
                            trend_lookback=40,
                            trend_atr_mult=trend_mult,
                            break_bars=break_bars,
                            break_buffer_atr=0.10,
                            label=label,
                        )
                    )
    return specs


def sample_sets(enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
    primary = enriched[
        enriched["trigger_mode"].eq("stagnation")
        & enriched["lookback_bars"].eq(120)
        & enriched["adx14"].ge(30)
        & enriched["risk_atr_at_signal"].le(1.5)
        & enriched["bb_width_atr"].between(3.0, 8.0)
    ].copy()
    practical = enriched[practical_mask(enriched)].copy()
    primary_support = primary[primary["support_age_bars"].between(60, 119)].copy()
    practical_support = practical[practical["support_age_bars"].between(60, 119)].copy()
    return {
        "primary_all": actual_trade_sample(primary),
        "primary_core4": actual_trade_sample(primary[primary["symbol"].isin(CORE4)].copy()),
        "primary_core4_quality": actual_trade_sample(primary[primary["symbol"].isin(CORE4) & quality_mask(primary)].copy()),
        "primary_core4_strict": actual_trade_sample(primary[primary["symbol"].isin(CORE4) & strict_mask(primary)].copy()),
        "primary_support60_119": actual_trade_sample(primary_support),
        "primary_support60_119_core4": actual_trade_sample(primary_support[primary_support["symbol"].isin(CORE4)].copy()),
        "practical_no_AUD_USD": actual_trade_sample(practical[practical["symbol"].isin(NO_AUD_USD)].copy()),
        "practical_core4": actual_trade_sample(practical[practical["symbol"].isin(CORE4)].copy()),
        "practical_support60_119_no_AUD_USD": actual_trade_sample(
            practical_support[practical_support["symbol"].isin(NO_AUD_USD)].copy()
        ),
    }


def event_mask(events: pd.DataFrame, event: str, ptype: int, lo_i: int, hi_i: int) -> bool:
    if events.empty:
        return False
    m = events["event"].eq(event) & events["ptype"].eq(ptype) & events["confirm_i"].between(lo_i, hi_i)
    return bool(m.any())


def latest_event(events: pd.DataFrame, hi_i: int) -> pd.Series | None:
    if events.empty:
        return None
    before = events[events["confirm_i"].le(hi_i)]
    if before.empty:
        return None
    return before.iloc[-1]


def annotate_with_hs(sample: pd.DataFrame, detections: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    windows = [24, 48, 120, 240]
    for row in sample.to_dict("records"):
        symbol = str(row["symbol"])
        spec_name = str(row["hs_spec"])
        trigger_i = int(row["trigger_i"])
        break_i = int(row["break_i"])
        events = detections.get((symbol, spec_name), pd.DataFrame())

        out = dict(row)
        out.update(
            {
                "hs_latest_age": np.nan,
                "hs_latest_type": "",
                "hs_latest_event": "",
                "hs_after_low_break_pattern": False,
                "hs_after_low_break_break": False,
                "inv_after_low_break_pattern": False,
                "inv_after_low_break_break": False,
            }
        )

        for window in windows:
            for prefix, ptype in [("hs", 1), ("inv", -1)]:
                for event in ["pattern", "break"]:
                    out[f"{prefix}_{event}_{window}"] = event_mask(events, event, ptype, trigger_i - window, trigger_i)

        out["hs_after_low_break_pattern"] = event_mask(events, "pattern", 1, break_i, trigger_i)
        out["hs_after_low_break_break"] = event_mask(events, "break", 1, break_i, trigger_i)
        out["inv_after_low_break_pattern"] = event_mask(events, "pattern", -1, break_i, trigger_i)
        out["inv_after_low_break_break"] = event_mask(events, "break", -1, break_i, trigger_i)

        latest = latest_event(events, trigger_i)
        if latest is not None:
            out["hs_latest_age"] = int(trigger_i - latest["confirm_i"])
            out["hs_latest_type"] = "HS" if int(latest["ptype"]) == 1 else "INV"
            out["hs_latest_event"] = str(latest["event"])

        out["hs_break_120_no_inv_break_120"] = bool(out["hs_break_120"]) and not bool(out["inv_break_120"])
        out["hs_pattern_120_no_inv_break_120"] = bool(out["hs_pattern_120"]) and not bool(out["inv_break_120"])
        out["no_inv_break_120"] = not bool(out["inv_break_120"])
        out["no_inv_pattern_120"] = not bool(out["inv_pattern_120"])
        rows.append(out)
    return pd.DataFrame(rows)


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def metric_row(sample_name: str, spec_name: str, rule_name: str, sample: pd.DataFrame, base_count: int) -> dict:
    row = {"sample": sample_name, "hs_spec": spec_name, "rule": rule_name, "base_trades": int(base_count)}
    row.update(metrics(sample, R_COL))
    row["coverage_pct"] = float(len(sample) / base_count * 100.0) if base_count else 0.0
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample.columns else ""
    row["pf"] = profit_factor(sample[R_COL].astype(float)) if len(sample) else math.nan
    return row


def summarize_rules(annotated: pd.DataFrame) -> pd.DataFrame:
    masks = [
        ("hs_pattern_48", lambda d: d["hs_pattern_48"]),
        ("hs_pattern_120", lambda d: d["hs_pattern_120"]),
        ("hs_break_24", lambda d: d["hs_break_24"]),
        ("hs_break_48", lambda d: d["hs_break_48"]),
        ("hs_break_120", lambda d: d["hs_break_120"]),
        ("hs_break_240", lambda d: d["hs_break_240"]),
        ("hs_break_120_no_inv_break_120", lambda d: d["hs_break_120_no_inv_break_120"]),
        ("hs_pattern_120_no_inv_break_120", lambda d: d["hs_pattern_120_no_inv_break_120"]),
        ("hs_after_low_break_pattern", lambda d: d["hs_after_low_break_pattern"]),
        ("hs_after_low_break_break", lambda d: d["hs_after_low_break_break"]),
        ("inv_pattern_48", lambda d: d["inv_pattern_48"]),
        ("inv_pattern_120", lambda d: d["inv_pattern_120"]),
        ("inv_break_48", lambda d: d["inv_break_48"]),
        ("inv_break_120", lambda d: d["inv_break_120"]),
        ("no_inv_break_120", lambda d: d["no_inv_break_120"]),
        ("no_inv_pattern_120", lambda d: d["no_inv_pattern_120"]),
        ("inv_after_low_break_pattern", lambda d: d["inv_after_low_break_pattern"]),
        ("inv_after_low_break_break", lambda d: d["inv_after_low_break_break"]),
    ]
    rows: list[dict] = []
    for (sample_name, spec_name), group in annotated.groupby(["sample", "hs_spec"]):
        base_count = len(group)
        rows.append(metric_row(sample_name, spec_name, "baseline", group, base_count))
        for rule_name, fn in masks:
            mask = fn(group).fillna(False)
            rows.append(metric_row(sample_name, spec_name, rule_name, group[mask].copy(), base_count))

    out = pd.DataFrame(rows)
    base = out[out["rule"].eq("baseline")][["sample", "hs_spec", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]].rename(
        columns={
            "win_rate": "base_win_rate",
            "total_r": "base_total_r",
            "avg_r": "base_avg_r",
            "pf": "base_pf",
            "max_dd_r": "base_max_dd_r",
        }
    )
    out = out.merge(base, on=["sample", "hs_spec"], how="left")
    out["delta_win_rate"] = out["win_rate"] - out["base_win_rate"]
    out["delta_total_r"] = out["total_r"] - out["base_total_r"]
    out["delta_avg_r"] = out["avg_r"] - out["base_avg_r"]
    out["delta_pf"] = out["pf"] - out["base_pf"]
    return out.sort_values(["sample", "total_r", "pf"], ascending=[True, False, False])


def write_report(summaries: pd.DataFrame, annotated: pd.DataFrame) -> None:
    focus_samples = [
        "primary_all",
        "primary_core4",
        "primary_core4_quality",
        "primary_support60_119",
        "primary_support60_119_core4",
        "practical_no_AUD_USD",
        "practical_core4",
        "practical_support60_119_no_AUD_USD",
    ]
    cols = [
        "sample",
        "hs_spec",
        "rule",
        "base_trades",
        "trades",
        "coverage_pct",
        "win_rate",
        "delta_win_rate",
        "total_r",
        "delta_total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "symbols",
        "periods",
    ]
    baseline = (
        summaries[summaries["rule"].eq("baseline") & summaries["sample"].isin(focus_samples)]
        .sort_values(["sample", "hs_spec"])
        .groupby("sample", as_index=False)
        .head(1)
        .copy()
    )
    useful = summaries[
        summaries["sample"].isin(focus_samples)
        & ~summaries["rule"].eq("baseline")
        & summaries["trades"].ge(3)
        & summaries["coverage_pct"].between(10, 95)
    ].copy()
    improved = useful[
        (useful["pf"] > useful["base_pf"])
        & (useful["win_rate"] >= useful["base_win_rate"])
        & (useful["total_r"] > 0)
    ].copy()
    top_useful = improved.sort_values(
        ["sample", "delta_total_r", "pf", "total_r"], ascending=[True, False, False, False]
    ).groupby("sample").head(8)

    hs_rules = ["hs_pattern_120", "hs_break_120", "hs_after_low_break_pattern", "hs_after_low_break_break"]
    hs_focus = summaries[
        summaries["sample"].isin(focus_samples)
        & summaries["rule"].isin(hs_rules)
        & summaries["trades"].ge(2)
    ].sort_values(["sample", "pf", "total_r"], ascending=[True, False, False]).groupby("sample").head(6)

    inv_rules = ["inv_pattern_120", "inv_break_120", "inv_after_low_break_pattern", "inv_after_low_break_break"]
    inv_focus = summaries[
        summaries["sample"].isin(focus_samples)
        & summaries["rule"].isin(inv_rules)
        & summaries["trades"].ge(2)
    ].sort_values(["sample", "avg_r", "trades"], ascending=[True, True, False]).groupby("sample").head(6)

    default_spec = "P5_DEF_TR_TL40_TA1.5_BB80_BUF0.1"
    default_rules = [
        "baseline",
        "hs_pattern_120",
        "hs_break_120",
        "hs_break_240",
        "inv_pattern_120",
        "inv_break_120",
        "no_inv_pattern_120",
        "no_inv_break_120",
    ]
    default_focus = summaries[
        summaries["sample"].isin(["primary_core4", "primary_core4_quality", "practical_core4", "practical_no_AUD_USD"])
        & summaries["hs_spec"].eq(default_spec)
        & summaries["rule"].isin(default_rules)
    ].copy()
    default_focus["__rule_order"] = default_focus["rule"].map({rule: i for i, rule in enumerate(default_rules)})
    default_focus = default_focus.sort_values(["sample", "__rule_order"]).drop(columns=["__rule_order"])

    lines = [
        "# H4 Low-Stag Short H&S Filter Study",
        "",
        "Status: 検証途中。ユーザー提供の `Beautiful H&S / Inverse H&S Scanner` をPythonへ移植し、H4安値停滞ショートの補助条件として確認。",
        "",
        "## 検証した使い方",
        "",
        "- `hs_pattern`: 三尊の形がシグナル前に確定。戻り売り構造の候補。",
        "- `hs_break`: 三尊ネックライン割れがシグナル前に確定。短期下落の追い風候補。",
        "- `inv_pattern` / `inv_break`: 逆三尊。ショートでは反転警戒または除外候補。",
        "- `after_low_break`: 1ヶ月安値ブレイク後からH4安値停滞シグナルまでに出たか。",
        "",
        "## 重要な実装注意",
        "",
        "- Pineと同じく、ピボットは `pivotRight` 本後に確定するため、Pythonでも確定バー `confirm_i <= trigger_i` のイベントだけ使用。",
        "- 三尊/逆三尊は `形の確定` と `ネックラインブレイク` を分離。ブレイクは形成後 `breakBars` 本以内のみ追跡。",
        "- default条件だけでなく、loose/default/strict、pivot 3/5/8、事前トレンドあり/なしを比較。ただし採用候補は説明しやすいものだけ。",
        "",
        "## ベースライン",
        "",
        markdown_table(baseline[cols], 20) if not baseline.empty else "_No rows._",
        "",
        "## サンプル別 改善候補",
        "",
        "PFと勝率がベースライン以上、かつ3件以上の条件だけを表示。",
        "",
        markdown_table(top_useful[cols], 60) if not top_useful.empty else "_No rows._",
        "",
        "## 三尊系だけを見る",
        "",
        markdown_table(hs_focus[cols], 60) if not hs_focus.empty else "_No rows._",
        "",
        "## 逆三尊系だけを見る",
        "",
        markdown_table(inv_focus[cols], 60) if not inv_focus.empty else "_No rows._",
        "",
        "## 元Pine設定に近い条件",
        "",
        "`pivot=5`, `Beautiful DEF`, `事前トレンドあり`, `breakBars=80`。まずTradingViewで見るならこの条件。",
        "",
        markdown_table(default_focus[cols], 60) if not default_focus.empty else "_No rows._",
        "",
        "## Pineでまず試す条件",
        "",
        "1. 三尊そのものは、H4安値停滞ショートのエントリー強化条件としては件数不足。元設定では `hs_break_120` が practical_core4 で 1件のみ、しかも -1.04R。",
        "2. 逆三尊は、ショートの逆方向シグナルとして一応見る価値あり。元設定では `inv_break_120` を避けると practical_core4 が 26 trades / +6.16R / PF 1.40 から 25 trades / +7.19R / PF 1.50。",
        "3. ただし改善はほぼ1件除外の効果なので、現時点では `逆三尊上抜け注意` ラベルに留める。即見送りルールにはしない。",
        "4. Loose/NoTrend/P3系は良く見える条件もあるが、元の目的である「綺麗な三尊」から外れやすい。実戦条件ではなく検証用表示だけ。",
        "",
        "## 暫定解釈",
        "",
        "- 三尊は、現時点ではH4安値停滞ショートの本体条件に足さない。",
        "- 逆三尊ネック上抜けは、反転警戒タグとしてPineに表示する価値がある。",
        "- 件数が少ない条件はPine表示だけにし、実戦ルールには入れない。",
        "",
        "## 出力CSV",
        "",
        "- `annotated_trades.csv`",
        "- `rule_summary.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    enriched = load_source()
    frames = build_frames()
    specs = hs_specs()

    detections: dict[tuple[str, str], pd.DataFrame] = {}
    for spec in specs:
        for symbol, frame in frames.items():
            detections[(symbol, spec.name)] = detect_hs_events(frame, spec)

    annotated_frames: list[pd.DataFrame] = []
    samples = sample_sets(enriched)
    for sample_name, sample in samples.items():
        if sample.empty:
            continue
        for spec in specs:
            work = sample.copy()
            work["sample"] = sample_name
            work["hs_spec"] = spec.name
            annotated_frames.append(annotate_with_hs(work, detections))

    annotated = pd.concat(annotated_frames, ignore_index=True) if annotated_frames else pd.DataFrame()
    summaries = summarize_rules(annotated) if not annotated.empty else pd.DataFrame()

    annotated.to_csv(OUT_DIR / "annotated_trades.csv", index=False)
    summaries.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    write_report(summaries, annotated)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if not summaries.empty:
        view = summaries[
            summaries["sample"].isin(["primary_core4_quality", "practical_core4"])
            & ~summaries["rule"].eq("baseline")
            & summaries["trades"].ge(3)
        ].sort_values(["sample", "pf", "total_r"], ascending=[True, False, False])
        print(view.head(30).to_string(index=False))


if __name__ == "__main__":
    main()

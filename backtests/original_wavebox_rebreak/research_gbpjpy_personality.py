#!/usr/bin/env python3
"""
GBPJPY personality research for WaveBox-style H1 rebreaks.

This is intentionally not a direct USDJPY preset copy.  The first hypothesis is
that GBPJPY should be treated as a long-only, momentum-continuation market where
weak/wicky rebreaks and wide boxes are rejected.
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "results_2026_05_26" / "gbpjpy_personality"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))
sys.path.insert(0, str(THIS_DIR))

from sai_backtest import load_instrument  # noqa: E402
import run_wavebox_rebreak as wb  # noqa: E402


SYMBOL = "GBPJPY"
START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")
MAX_HOLD = 72

SPREAD_PRICE = 0.020
SLIP_PRICE = 0.010

BOX_BARS_LIST = [6, 8, 10]
BOX_ATR_LIST = [1.2, 1.4, 1.6, 1.8, 2.0]
RR_LIST = [1.2, 1.5, 1.8]

LENIENT_SIGNAL_SPEC = {
    "filter": "gbpjpy_lenient_source",
    "description": "GBPJPY source candidates before personality filters",
    "retrace_min": 0.50,
    "retrace_max": 0.886,
    "min_adjust_ratio": 0.30,
    "max_recovery": 0.95,
    "min_body": 0.20,
    "min_align": 0,
    "max_oppose": 99,
    "require_ema_flip": True,
    "max_chase_atr": 0.80,
    "min_planned_rr": 1.10,
}

RETRACE_FILTERS = {
    "50_618": (0.50, 0.618),
    "50_70": (0.50, 0.700),
    "50_786": (0.50, 0.786),
}

RECOVERY_FILTERS = {
    "any": None,
    "25_85": (0.25, 0.85),
    "50_80": (0.50, 0.80),
}

BODY_FILTERS = {
    "any": None,
    "ge45": 0.45,
    "ge65": 0.65,
}

H4_FILTERS = {
    "any": "any",
    "not_oppose": "not_oppose",
    "align": "align",
}

HOUR_FILTERS = {
    "none": None,
    "ex14": {"exclude": {14}},
    "active_1_6_8_22": {"include": {1, 6, 8, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21, 22}},
}

SETUP_AGE_FILTERS = {
    "any": None,
    "le2": 2,
    "le5": 5,
}

BOX_WIDTH_FILTERS = {
    "any": None,
    "le17": 1.70,
    "le14": 1.40,
}

CHASE_FILTERS = {
    "any": None,
    "le35": 0.35,
    "le50": 0.50,
}

REFERENCE_DIRECTIONS = ["long", "short"]
SEARCH_DIRECTIONS = ["long"]


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


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


def direction_cost_r(direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - SLIP_PRICE) - (entry + SPREAD_PRICE / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - SPREAD_PRICE / 2.0) - (exit_price + SLIP_PRICE)
    return clean / risk, after / risk


def prepare_h1() -> pd.DataFrame:
    raw = load_instrument(SYMBOL).loc[START:END].copy()
    raw["volume"] = 0.0
    wb.BOX_BARS_LIST = sorted(set(BOX_BARS_LIST))
    h1 = wb.add_indicators(raw, "H1")
    h4 = wb.add_indicators(wb.resample_ohlc(raw, "4h"), "H4")
    d1 = wb.add_indicators(wb.resample_ohlc(raw, "1D"), "D1")
    return wb.attach_upper_context(h1, {"H4": h4, "D1": d1}, "H1")


def generate_candidates(h1: pd.DataFrame) -> pd.DataFrame:
    pivots = wb.build_confirmed_pivots(h1, 3, 1.15)
    rows: list[dict] = []
    for box_bars, box_atr in itertools.product(BOX_BARS_LIST, BOX_ATR_LIST):
        active: list[wb.Pivot] = []
        pointer = 0
        seen_setup: set[tuple] = set()
        for i in range(2, len(h1) - 1):
            pointer = wb.pivots_until(pivots, pointer, i, active)
            ts = h1.index[i]
            if ts < START or ts > END or holiday_market(ts):
                continue
            sig = wb.signal_from_wavebox(h1, i, active, "H1", box_bars, box_atr, LENIENT_SIGNAL_SPEC)
            if sig is None:
                continue
            setup_key = (sig["direction"], sig["pivots"], box_bars, box_atr)
            if setup_key in seen_setup:
                continue
            sig = {**sig, "symbol": SYMBOL, "entry_hour": int(h1.index[int(sig["signal_i"]) + 1].hour)}
            rows.append(sig)
            seen_setup.add(setup_key)
    if not rows:
        return pd.DataFrame()
    candidates = pd.DataFrame(rows)
    candidates["signal_time"] = pd.to_datetime(candidates["signal_time"])
    return candidates.sort_values(["box_bars", "box_atr", "signal_i"]).reset_index(drop=True)


def simulate_trade(h1: pd.DataFrame, sig: dict, rr: float) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(h1):
        return None

    direction = str(sig["direction"])
    entry = float(h1["open"].iloc[entry_i])
    stop = float(sig["stop"])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * rr
        reward = target - entry
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * rr
        reward = entry - target

    exit_i = min(len(h1) - 1, entry_i + MAX_HOLD)
    exit_price = float(h1["close"].iloc[exit_i])
    reason = "time_exit"
    for j in range(entry_i, min(len(h1), entry_i + MAX_HOLD + 1)):
        hi = float(h1["high"].iloc[j])
        lo = float(h1["low"].iloc[j])
        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = hi >= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break

    r_clean, r_after_cost = direction_cost_r(direction, entry, exit_price, risk)
    return {
        "entry_i": entry_i,
        "entry_time": h1.index[entry_i],
        "entry": entry,
        "rr": rr,
        "target": target,
        "planned_rr": reward / risk,
        "exit_i": exit_i,
        "exit_time": h1.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after_cost,
    }


def apply_filter(candidates: pd.DataFrame, spec: dict) -> pd.DataFrame:
    out = candidates
    out = out[out["direction"] == spec["direction"]]

    lo, hi = RETRACE_FILTERS[spec["retrace"]]
    out = out[out["retrace"].between(lo, hi, inclusive="both")]

    recovery = RECOVERY_FILTERS[spec["recovery"]]
    if recovery is not None:
        out = out[out["recovery"].between(recovery[0], recovery[1], inclusive="both")]

    body = BODY_FILTERS[spec["body"]]
    if body is not None:
        out = out[out["signal_body_ratio"] >= body]

    h4 = H4_FILTERS[spec["h4"]]
    if h4 == "not_oppose":
        out = out[out["upper_oppose"] == 0]
    elif h4 == "align":
        out = out[(out["upper_oppose"] == 0) & (out["upper_align"] >= 1)]

    hour = HOUR_FILTERS[spec["hours"]]
    if hour is not None:
        if "exclude" in hour:
            out = out[~out["entry_hour"].isin(hour["exclude"])]
        if "include" in hour:
            out = out[out["entry_hour"].isin(hour["include"])]

    setup_age = SETUP_AGE_FILTERS[spec["setup_age"]]
    if setup_age is not None:
        out = out[out["setup_age"] <= setup_age]

    box_width = BOX_WIDTH_FILTERS[spec["box_width"]]
    if box_width is not None:
        out = out[out["box_width_atr"] <= box_width]

    chase = CHASE_FILTERS[spec["chase"]]
    if chase is not None:
        out = out[out["chase_atr"] <= chase]

    return out.sort_values("signal_i").copy()


def run_filtered_trades(h1: pd.DataFrame, candidates: pd.DataFrame, spec: dict, rr: float) -> pd.DataFrame:
    filtered = apply_filter(candidates, spec)
    if filtered.empty:
        return pd.DataFrame()
    rows: list[dict] = []
    in_pos_until = -1
    for row in filtered.itertuples(index=False):
        sig = row._asdict()
        if int(sig["signal_i"]) <= in_pos_until:
            continue
        trade = simulate_trade(h1, sig, rr)
        if trade is None:
            continue
        rows.append({**sig, **trade})
        in_pos_until = int(trade["exit_i"])
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    out["sample"] = np.where(out["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    out["year"] = out["entry_time"].dt.year
    return out


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "is_trades": 0,
            "is_r": 0.0,
            "oos_trades": 0,
            "oos_r": 0.0,
        }
    r = df["r_after_cost"]
    by_year = df.groupby("year")["r_after_cost"].sum()
    years = sorted(df["year"].unique())
    rolling_2y = []
    for start in years:
        sub = df[(df["year"] >= start) & (df["year"] <= start + 1)]
        if not sub.empty:
            rolling_2y.append(float(sub["r_after_cost"].sum()))
    is_df = df[df["entry_time"] < OOS_START]
    oos_df = df[df["entry_time"] >= OOS_START]
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "worst_year_r": float(by_year.min()) if len(by_year) else np.nan,
        "worst_2y_r": float(min(rolling_2y)) if rolling_2y else np.nan,
        "is_trades": int(len(is_df)),
        "is_r": float(is_df["r_after_cost"].sum()) if len(is_df) else 0.0,
        "oos_trades": int(len(oos_df)),
        "oos_r": float(oos_df["r_after_cost"].sum()) if len(oos_df) else 0.0,
    }


def score(row: dict) -> float:
    if row["trades"] < 18 or row["is_trades"] < 14 or row["oos_trades"] < 2:
        return -9999.0
    return (
        row["avg_r"] * 90.0
        + min(row["total_r"], 30.0) * 0.45
        + min(row["pf"], 5.0) * 5.0
        - row["max_dd_r"] * 0.75
        - max(row["max_losing_streak"] - 4, 0) * 1.20
        + min(row["worst_2y_r"], 0.0) * 2.0
        + min(row["oos_r"], 0.0) * 15.0
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
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


def axis_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    specs = [
        ("direction", trades["direction"].astype(str)),
        ("entry_hour", trades["entry_hour"].astype(str)),
        ("retrace", pd.cut(trades["retrace"], [0.5, 0.618, 0.70, 0.786, 0.886], include_lowest=True)),
        ("recovery", pd.cut(trades["recovery"], [0, 0.25, 0.5, 0.65, 0.80, 0.95], include_lowest=True)),
        ("body", pd.cut(trades["signal_body_ratio"], [0, 0.45, 0.65, 1.0], include_lowest=True)),
        ("box_width_atr", pd.cut(trades["box_width_atr"], [0, 1.2, 1.4, 1.7, 2.0], include_lowest=True)),
        ("setup_age", pd.cut(trades["setup_age"], [0, 2, 5, 12, 99], include_lowest=True)),
        ("chase_atr", pd.cut(trades["chase_atr"], [0, 0.35, 0.50, 0.80], include_lowest=True)),
    ]
    for feature, bins in specs:
        tmp = trades.copy()
        tmp["bin"] = bins.astype(str)
        for value, group in tmp.groupby("bin", dropna=False):
            row = summarize(group)
            rows.append({"feature": feature, "bin": str(value), **row})
    return pd.DataFrame(rows).sort_values(["feature", "total_r"], ascending=[True, False])


def write_report(
    candidates: pd.DataFrame,
    base_reference: pd.DataFrame,
    grid: pd.DataFrame,
    top: pd.DataFrame,
    chosen: pd.DataFrame,
) -> None:
    report_cols = [
        "score",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "worst_2y_r",
        "oos_trades",
        "oos_r",
        "box_bars",
        "box_atr",
        "rr",
        "direction",
        "retrace",
        "recovery",
        "body",
        "h4",
        "hours",
        "setup_age",
        "box_width",
        "chase",
    ]
    lines = [
        "# GBPJPY Personality Research",
        "",
        "## 目的",
        "",
        "USDJPY H1 WaveBox をそのまま移植せず、GBPJPYの負け方から専用ルールを探す。",
        "",
        "仮説:",
        "",
        "- GBPJPYはショートのだましが多いので、まずロング専用を本線にする",
        "- 広いBox、弱い実体、追いかけすぎのブレイクを捨てる",
        "- USDJPYの時間除外を固定で流用しない",
        "",
        "## 候補数",
        "",
        f"- source candidates: `{len(candidates)}`",
        "",
        "## USDJPY流用ベースの参考",
        "",
        markdown_table(base_reference, 30),
        "",
        "## Top Robust Candidates",
        "",
        markdown_table(top[report_cols], 30),
        "",
        "## Chosen Candidate Trades",
        "",
        markdown_table(
            chosen[
                [
                    "entry_time",
                    "direction",
                    "entry",
                    "exit_time",
                    "exit_reason",
                    "r_after_cost",
                    "retrace",
                    "recovery",
                    "signal_body_ratio",
                    "box_width_atr",
                    "chase_atr",
                    "entry_hour",
                    "upper_context",
                ]
            ],
            80,
        ),
        "",
        "## Notes",
        "",
        "- OOSが少ない候補は採用ではなく監視候補。",
        "- `active_1_6_8_22` はGBPJPYらしい時間仮説の検査用で、最終採用には追加監査が必要。",
        "- 最終ルールはTop表から数字だけで決めず、TradingView上で形が納得できるかを確認する。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    h1 = prepare_h1()
    candidates = generate_candidates(h1)
    candidates.to_csv(OUT_DIR / "gbpjpy_source_candidates.csv", index=False)
    if candidates.empty:
        (OUT_DIR / "report_ja.md").write_text("# GBPJPY Personality Research\n\nNo source candidates.", encoding="utf-8")
        print("No source candidates.")
        return

    base_rows = []
    for direction in REFERENCE_DIRECTIONS:
        base_spec = {
            "direction": direction,
            "retrace": "50_786",
            "recovery": "any",
            "body": "any",
            "h4": "any",
            "hours": "none",
            "setup_age": "any",
            "box_width": "any",
            "chase": "any",
        }
        subset = candidates[(candidates["box_bars"] == 8) & (candidates["box_atr"] == 2.0)]
        trades = run_filtered_trades(h1, subset, base_spec, 1.5)
        base_rows.append({"reference": f"box8_atr2_rr1.5_{direction}", **summarize(trades)})
    base_reference = pd.DataFrame(base_rows)
    base_reference.to_csv(OUT_DIR / "gbpjpy_base_reference.csv", index=False)

    keys = {
        "direction": SEARCH_DIRECTIONS,
        "retrace": list(RETRACE_FILTERS),
        "recovery": list(RECOVERY_FILTERS),
        "body": list(BODY_FILTERS),
        "h4": list(H4_FILTERS),
        "hours": list(HOUR_FILTERS),
        "setup_age": list(SETUP_AGE_FILTERS),
        "box_width": list(BOX_WIDTH_FILTERS),
        "chase": list(CHASE_FILTERS),
    }

    grid_rows = []
    chosen_trades: pd.DataFrame | None = None
    chosen_key: dict | None = None
    total_jobs = len(BOX_BARS_LIST) * len(BOX_ATR_LIST) * len(RR_LIST) * math.prod(len(v) for v in keys.values())
    done = 0
    for box_bars, box_atr, rr in itertools.product(BOX_BARS_LIST, BOX_ATR_LIST, RR_LIST):
        source = candidates[(candidates["box_bars"] == box_bars) & (candidates["box_atr"] == box_atr)]
        if source.empty:
            continue
        for combo in itertools.product(*keys.values()):
            spec = dict(zip(keys.keys(), combo))
            trades = run_filtered_trades(h1, source, spec, rr)
            summary = summarize(trades)
            row = {"box_bars": box_bars, "box_atr": box_atr, "rr": rr, **spec, **summary}
            row["score"] = score(row)
            grid_rows.append(row)
            if row["score"] > -9999.0 and (chosen_key is None or row["score"] > chosen_key["score"]):
                chosen_key = row
                chosen_trades = trades
            done += 1
            if done % 5000 == 0:
                print(f"progress {done}/{total_jobs}", flush=True)

    grid = pd.DataFrame(grid_rows).sort_values("score", ascending=False)
    grid.to_csv(OUT_DIR / "gbpjpy_grid.csv", index=False)
    top = grid[grid["score"] > -9999.0].head(50).copy()
    top.to_csv(OUT_DIR / "gbpjpy_top_candidates.csv", index=False)

    if chosen_trades is None:
        chosen_trades = pd.DataFrame()
    chosen_trades.to_csv(OUT_DIR / "gbpjpy_chosen_trades.csv", index=False)
    axis_summary(chosen_trades).to_csv(OUT_DIR / "gbpjpy_chosen_axis_summary.csv", index=False)

    write_report(candidates, base_reference, grid, top, chosen_trades)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Base reference")
    print(base_reference.to_string(index=False))
    print("Top candidates")
    print(top.head(12).to_string(index=False))


if __name__ == "__main__":
    main()

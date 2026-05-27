#!/usr/bin/env python3
"""
Cross-symbol validation for WaveBox H1 Rebreak.

Uses the best USDJPY first-pass variant:
  H1 / base / box 8 / 2.0 ATR / fixed 1.5R

Then evaluates the same mechanical rule on the available H1 instruments.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "results_2026_05_25" / "cross_symbol_h1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))
sys.path.insert(0, str(THIS_DIR))

from sai_backtest import INSTRUMENTS, load_instrument  # noqa: E402
import run_wavebox_rebreak as wb  # noqa: E402


START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")

BOX_BARS = 8
BOX_ATR = 2.0
TARGET_MODEL = "fixed_1_5R"
MAX_HOLD = 72

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}

BASE_SPEC = {
    "filter": "base",
    "description": "H1 WaveBox base cross-symbol",
    "retrace_min": 0.50,
    "retrace_max": 0.886,
    "min_adjust_ratio": 0.30,
    "max_recovery": 0.92,
    "min_body": 0.25,
    "min_align": 0,
    "max_oppose": 99,
    "require_ema_flip": True,
    "max_chase_atr": 0.80,
    "min_planned_rr": 1.20,
}


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def direction_cost_r(symbol: str, direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    costs = COST_TABLE[symbol]
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - costs["slip_price"]) - (entry + costs["spread_price"] / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - costs["spread_price"] / 2.0) - (exit_price + costs["slip_price"])
    return clean / risk, after / risk


def simulate_trade(symbol: str, df: pd.DataFrame, sig: dict) -> dict | None:
    entry_i = int(sig["signal_i"]) + 1
    if entry_i >= len(df):
        return None
    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * 1.5
        reward = target - entry
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * 1.5
        reward = entry - target
    if reward / risk < 1.2:
        return None

    exit_i = min(len(df) - 1, entry_i + MAX_HOLD)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "time_exit"
    for j in range(entry_i, min(len(df), entry_i + MAX_HOLD + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
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

    r_clean, r_after = direction_cost_r(symbol, direction, entry, exit_price, risk)
    return {
        "entry_i": entry_i,
        "entry_time": df.index[entry_i],
        "entry": entry,
        "target_model": TARGET_MODEL,
        "target": target,
        "planned_rr": reward / risk,
        "exit_i": exit_i,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after,
    }


def run_symbol(symbol: str) -> tuple[pd.DataFrame, dict]:
    raw = load_instrument(symbol).loc[START:END].copy()
    raw["volume"] = 0.0
    h1 = wb.add_indicators(raw, "H1")
    h4 = wb.add_indicators(wb.resample_ohlc(raw, "4h"), "H4")
    d1 = wb.add_indicators(wb.resample_ohlc(raw, "1D"), "D1")
    h1 = wb.attach_upper_context(h1, {"H4": h4, "D1": d1}, "H1")

    pivots = wb.build_confirmed_pivots(h1, 3, 1.15)
    active: list[wb.Pivot] = []
    pointer = 0
    in_pos_until = -1
    rows = []
    seen_setup: set[tuple] = set()
    for i in range(2, len(h1) - 1):
        pointer = wb.pivots_until(pivots, pointer, i, active)
        ts = h1.index[i]
        if ts < START or ts > END or holiday_market(ts) or i <= in_pos_until:
            continue
        sig = wb.signal_from_wavebox(h1, i, active, "H1", BOX_BARS, BOX_ATR, BASE_SPEC)
        if sig is None:
            continue
        setup_key = (sig["direction"], sig["pivots"], BOX_BARS, BOX_ATR)
        if setup_key in seen_setup:
            continue
        trade = simulate_trade(symbol, h1, sig)
        if trade is None:
            continue
        rows.append({**sig, "symbol": symbol, **trade})
        seen_setup.add(setup_key)
        in_pos_until = int(trade["exit_i"])
    coverage = {"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()}
    return pd.DataFrame(rows), coverage


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


def summarize(df: pd.DataFrame, group_cols: list[str], r_col: str = "r_after_cost") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for key, group in df.groupby(group_cols, dropna=False):
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
                "tp_rate": float((group["exit_reason"] == "TP").mean() * 100),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


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


def main() -> None:
    all_rows = []
    coverage = []
    for symbol in INSTRUMENTS:
        if symbol not in COST_TABLE:
            continue
        rows, cov = run_symbol(symbol)
        coverage.append(cov)
        if not rows.empty:
            all_rows.append(rows)

    coverage_df = pd.DataFrame(coverage)
    coverage_df.to_csv(OUT_DIR / "data_coverage.csv", index=False)
    if not all_rows:
        (OUT_DIR / "report_ja.md").write_text("# WaveBox H1 Cross Symbol\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades = pd.concat(all_rows, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col])
    trades["sample"] = np.where(trades["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2014_2024")
    trades["year"] = trades["entry_time"].dt.year
    trades.to_csv(OUT_DIR / "trades.csv", index=False)

    by_symbol = summarize(trades, ["symbol"])
    by_symbol_sample = summarize(trades, ["symbol", "sample"])
    by_symbol_direction = summarize(trades, ["symbol", "direction"])
    by_year = summarize(trades, ["year"])
    overall = summarize(trades.assign(all_symbols="ALL"), ["all_symbols"])
    jpy_only = trades[trades["symbol"].isin(["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY"])]
    jpy_overall = summarize(jpy_only.assign(group="JPY_FX"), ["group"])

    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_symbol_sample.to_csv(OUT_DIR / "summary_by_symbol_sample.csv", index=False)
    by_symbol_direction.to_csv(OUT_DIR / "summary_by_symbol_direction.csv", index=False)
    by_year.to_csv(OUT_DIR / "summary_by_year.csv", index=False)
    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    jpy_overall.to_csv(OUT_DIR / "summary_jpy_overall.csv", index=False)

    lines = [
        "# WaveBox H1 Rebreak クロスシンボル検証",
        "",
        "条件: `H1 / base / box 8本 / 2.0ATR / TP 1.5R`",
        "",
        "## 全体",
        "",
        markdown_table(overall, 10),
        "",
        "## JPY FXのみ",
        "",
        markdown_table(jpy_overall, 10),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 30),
        "",
        "## 通貨 x IS/OOS",
        "",
        markdown_table(by_symbol_sample.sort_values(["symbol", "sample"]), 80),
        "",
        "## 通貨 x 方向",
        "",
        markdown_table(by_symbol_direction.sort_values(["symbol", "direction"]), 80),
        "",
        "## 年別 全シンボル",
        "",
        markdown_table(by_year.sort_values("year"), 30),
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("\nOverall")
    print(overall.to_string(index=False))
    print("\nJPY")
    print(jpy_overall.to_string(index=False))
    print("\nBy symbol")
    print(by_symbol.to_string(index=False))


if __name__ == "__main__":
    main()

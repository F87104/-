#!/usr/bin/env python3
"""Sequential research pass requested on 2026-05-27.

Checks, in order:
1. CHFJPY two-bar exhaustion short confirmation.
2. CHFJPY strong-trend avoidance filter.
3. CHFJPY hour-filter robustness.
4. Stretch-reversal transfer to GBPJPY/AUDJPY.
5. Portfolio effect with USDJPY H1 WaveBox practical.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

import audit_wavebox_usdjpy_v1_practical as usd
import research_chfjpy_countertrend as ct
import research_chfjpy_personality as rp


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_27" / "sequence_countertrend_portfolio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL_COSTS = {
    "USDJPY": (0.010, 0.005),
    "CHFJPY": (0.020, 0.010),
    "GBPJPY": (0.030, 0.015),
    "AUDJPY": (0.020, 0.010),
}

BASE_STRETCH_SHORT = {
    "family": "stretch_reversal",
    "direction": "short",
    "lookback": "any",
    "move_bars": 6,
    "move_atr": 1.2,
    "trigger_atr": 1.0,
    "wick_ratio": 0.55,
    "close_location": 0.65,
    "bar_range_atr": 0.8,
    "body_max": 0.75,
    "range_width_max": 999.0,
    "bb_z": 2.1,
    "rsi_low": 25,
    "rsi_high": 75,
    "h4": "neutral",
    "hours": None,
    "rr": 0.8,
    "stop_buffer_atr": 0.15,
    "max_risk_atr": 2.0,
    "max_hold": 12,
}

STRETCH_LONG_ANY = {
    **BASE_STRETCH_SHORT,
    "direction": "long",
    "h4": "any",
    "rr": 1.0,
    "stop_buffer_atr": 0.25,
    "max_hold": 8,
}

HOUR_SETS = {
    "none": None,
    "exclude_0_only": [h for h in range(24) if h not in [0]],
    "exclude_bad_hours": [h for h in range(24) if h not in [0, 9, 11, 15, 19]],
    "tokyo_london_core": [8, 10, 12, 13, 14, 16, 17, 20],
    "no_very_late": [h for h in range(24) if h not in [0, 1, 19, 20, 21, 22, 23]],
}

_CACHE: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}


def set_symbol_cost(symbol: str) -> tuple[float, float]:
    old = (rp.SPREAD_PRICE, rp.SLIP_PRICE)
    spread, slip = SYMBOL_COSTS.get(symbol, (0.020, 0.010))
    rp.SPREAD_PRICE = spread
    rp.SLIP_PRICE = slip
    return old


def restore_cost(old: tuple[float, float]) -> None:
    rp.SPREAD_PRICE, rp.SLIP_PRICE = old


def get_symbol_data(symbol: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if symbol in _CACHE:
        return _CACHE[symbol]
    old_symbol = rp.SYMBOL
    old_cost = set_symbol_cost(symbol)
    try:
        rp.SYMBOL = symbol
        h1 = ct.add_countertrend_features(rp.prepare_h1())
        source = ct.build_source(h1)
    finally:
        rp.SYMBOL = old_symbol
        restore_cost(old_cost)
    _CACHE[symbol] = (h1, source)
    return h1, source


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def max_drawdown(values: pd.Series | np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def summarize_trades(label: str, trades: pd.DataFrame, symbol: str = "") -> dict:
    if trades.empty:
        return {
            "label": label,
            "symbol": symbol,
            "trades": 0,
            "win_rate": np.nan,
            "total_r": 0.0,
            "avg_r": np.nan,
            "pf": np.nan,
            "max_dd_r": 0.0,
            "worst_year_r": np.nan,
            "worst_2y_r": np.nan,
            "oos_trades": 0,
            "oos_r": 0.0,
        }
    df = trades.sort_values("entry_time").copy()
    r = df["r_after_cost"]
    df["year"] = df["entry_time"].dt.year
    by_year = df.groupby("year")["r_after_cost"].sum()
    rolling_2y = []
    for year in sorted(df["year"].unique()):
        rolling_2y.append(float(df[df["year"].between(year, year + 1)]["r_after_cost"].sum()))
    oos = df[df["entry_time"] >= rp.OOS_START]
    return {
        "label": label,
        "symbol": symbol,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "worst_year_r": float(by_year.min()) if len(by_year) else np.nan,
        "worst_2y_r": float(min(rolling_2y)) if rolling_2y else np.nan,
        "oos_trades": int(len(oos)),
        "oos_r": float(oos["r_after_cost"].sum()) if len(oos) else 0.0,
    }


def run_spec(symbol: str, spec: dict) -> pd.DataFrame:
    h1, source = get_symbol_data(symbol)
    old_cost = set_symbol_cost(symbol)
    try:
        trades = ct.run_trades(h1, source, spec)
    finally:
        restore_cost(old_cost)
    return trades


def simulate_second_bar_short(h1: pd.DataFrame, sig: dict, spec: dict, confirm_mode: str) -> dict | None:
    signal_i = int(sig["signal_i"])
    confirm_i = signal_i + 1
    entry_i = signal_i + 2
    if entry_i >= len(h1):
        return None

    signal_high = float(h1["high"].iloc[signal_i])
    signal_close = float(h1["close"].iloc[signal_i])
    confirm_open = float(h1["open"].iloc[confirm_i])
    confirm_high = float(h1["high"].iloc[confirm_i])
    confirm_close = float(h1["close"].iloc[confirm_i])
    lower_high = confirm_high <= signal_high
    bear = confirm_close < confirm_open
    close_down = confirm_close < signal_close

    if confirm_mode == "lower_high_or_bear" and not (lower_high or bear):
        return None
    if confirm_mode == "lower_high_and_bear" and not (lower_high and bear):
        return None
    if confirm_mode == "close_down" and not close_down:
        return None
    if confirm_mode == "lower_high_close_down" and not (lower_high and close_down):
        return None

    allowed_hours = spec.get("hours")
    if allowed_hours and h1.index[entry_i].hour not in allowed_hours:
        return None

    atr = float(sig["atr"])
    entry = float(h1["open"].iloc[entry_i])
    stop_anchor = max(signal_high, confirm_high)
    stop = stop_anchor + atr * spec["stop_buffer_atr"]
    risk = stop - entry
    if risk <= 0 or risk / atr > spec["max_risk_atr"]:
        return None
    target = entry - risk * spec["rr"]

    exit_i = min(len(h1) - 1, entry_i + spec["max_hold"])
    exit_price = float(h1["close"].iloc[exit_i])
    reason = "TIME"
    for j in range(entry_i, min(len(h1), entry_i + spec["max_hold"] + 1)):
        hi = float(h1["high"].iloc[j])
        lo = float(h1["low"].iloc[j])
        hit_sl = hi >= stop
        hit_tp = lo <= target
        if hit_sl or hit_tp:
            exit_i = j
            exit_price = stop if hit_sl else target
            reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
            break
    return {
        **sig,
        "confirm_mode": confirm_mode,
        "confirm_time": h1.index[confirm_i],
        "entry_i": entry_i,
        "entry_time": h1.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "risk_atr": risk / atr,
        "exit_i": exit_i,
        "exit_time": h1.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "r_after_cost": rp.direction_cost_r("short", entry, exit_price, risk),
    }


def run_second_bar(symbol: str, spec: dict, confirm_mode: str) -> pd.DataFrame:
    h1, source = get_symbol_data(symbol)
    base_spec = {**spec, "hours": None}
    old_cost = set_symbol_cost(symbol)
    rows = []
    in_pos_until = -1
    try:
        filtered = ct.apply_spec(source, base_spec)
        for row in filtered.itertuples(index=False):
            sig = row._asdict()
            if int(sig["signal_i"]) <= in_pos_until:
                continue
            trade = simulate_second_bar_short(h1, sig, spec, confirm_mode)
            if trade is None:
                continue
            rows.append(trade)
            in_pos_until = int(trade["exit_i"])
    finally:
        restore_cost(old_cost)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    for col in ["signal_time", "confirm_time", "entry_time", "exit_time"]:
        out[col] = pd.to_datetime(out[col])
    out["sample"] = np.where(out["entry_time"] >= rp.OOS_START, "OOS_2025_2026", "IS_2014_2024")
    out["year"] = out["entry_time"].dt.year
    return out


def write_csv(name: str, df: pd.DataFrame) -> None:
    df.to_csv(OUT_DIR / name, index=False)


def markdown_table(df: pd.DataFrame, max_rows: int = 60) -> str:
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


def usd_trades() -> pd.DataFrame:
    base = usd.load_base()
    trades = usd.apply_candidate(base, usd.CANDIDATES[usd.STANDARD_CANDIDATE]).copy()
    trades["strategy"] = "USDJPY WaveBox v1"
    trades["symbol"] = "USDJPY"
    return trades


def portfolio_summary() -> pd.DataFrame:
    usdjpy = usd_trades()
    chf_spec = {**BASE_STRETCH_SHORT, "hours": HOUR_SETS["exclude_0_only"]}
    chfjpy = run_spec("CHFJPY", chf_spec).copy()
    chfjpy["strategy"] = "CHFJPY stretch short ex0"
    chfjpy["symbol"] = "CHFJPY"
    combined = pd.concat(
        [
            usdjpy[["entry_time", "symbol", "strategy", "direction", "r_after_cost"]],
            chfjpy[["entry_time", "symbol", "strategy", "direction", "r_after_cost"]],
        ],
        ignore_index=True,
    ).sort_values("entry_time")
    write_csv("portfolio_combined_trades.csv", combined)
    rows = [
        summarize_trades("USDJPY only", usdjpy, "USDJPY"),
        summarize_trades("CHFJPY stretch short ex0", chfjpy, "CHFJPY"),
        summarize_trades("Combined equal-risk trades", combined, "PORTFOLIO"),
    ]
    return pd.DataFrame(rows)


def main() -> None:
    result_tables: dict[str, pd.DataFrame] = {}

    # 1. Two-bar confirmation.
    two_rows = []
    for confirm_mode in ["lower_high_or_bear", "lower_high_and_bear", "close_down", "lower_high_close_down"]:
        for rr in [0.8, 1.0]:
            for stop_buffer in [0.15, 0.25]:
                spec = {
                    **BASE_STRETCH_SHORT,
                    "rr": rr,
                    "stop_buffer_atr": stop_buffer,
                    "hours": HOUR_SETS["exclude_0_only"],
                }
                trades = run_second_bar("CHFJPY", spec, confirm_mode)
                label = f"{confirm_mode} rr{rr} stop{stop_buffer}"
                two_rows.append({**summarize_trades(label, trades, "CHFJPY"), "confirm_mode": confirm_mode, "rr": rr, "stop_buffer_atr": stop_buffer})
                if len(two_rows) <= 4:
                    write_csv(f"two_bar_{confirm_mode}_rr{rr}_stop{stop_buffer}.csv", trades)
    two_df = pd.DataFrame(two_rows).sort_values(["total_r", "avg_r"], ascending=False)
    write_csv("step1_two_bar_confirmation.csv", two_df)
    result_tables["Step 1 Two-Bar Confirmation"] = two_df

    # 2. Strong-trend avoidance.
    trend_rows = []
    for h4 in ["any", "not_oppose", "neutral"]:
        spec = {**BASE_STRETCH_SHORT, "h4": h4}
        trades = run_spec("CHFJPY", spec)
        trend_rows.append({**summarize_trades(f"h4_{h4}", trades, "CHFJPY"), "h4": h4})
    trend_df = pd.DataFrame(trend_rows).sort_values("total_r", ascending=False)
    write_csv("step2_h4_trend_filter.csv", trend_df)
    result_tables["Step 2 Strong-Trend Avoidance"] = trend_df

    # 3. Hour robustness.
    hour_rows = []
    for name, hours in HOUR_SETS.items():
        spec = {**BASE_STRETCH_SHORT, "hours": hours}
        trades = run_spec("CHFJPY", spec)
        hour_rows.append({**summarize_trades(name, trades, "CHFJPY"), "hour_set": name})
    hour_df = pd.DataFrame(hour_rows).sort_values("total_r", ascending=False)
    write_csv("step3_hour_filter.csv", hour_df)
    result_tables["Step 3 Hour Robustness"] = hour_df

    # 4. Cross-symbol stretch-reversal transfer.
    cross_rows = []
    for symbol in ["CHFJPY", "GBPJPY", "AUDJPY"]:
        for label, spec in {
            "short_neutral": BASE_STRETCH_SHORT,
            "short_neutral_ex0": {**BASE_STRETCH_SHORT, "hours": HOUR_SETS["exclude_0_only"]},
            "long_any": STRETCH_LONG_ANY,
            "both_neutral_1R": {**BASE_STRETCH_SHORT, "direction": "both", "rr": 1.0, "stop_buffer_atr": 0.25},
        }.items():
            try:
                trades = run_spec(symbol, spec)
                cross_rows.append({**summarize_trades(label, trades, symbol), "variant": label})
            except Exception as exc:  # Keep the sequence report alive if a symbol is missing.
                cross_rows.append({"symbol": symbol, "label": label, "variant": label, "error": str(exc)})
    cross_df = pd.DataFrame(cross_rows).sort_values(["symbol", "total_r"], ascending=[True, False])
    write_csv("step4_cross_symbol_stretch.csv", cross_df)
    result_tables["Step 4 Cross-Symbol Transfer"] = cross_df

    # 5. Portfolio.
    port_df = portfolio_summary().sort_values("total_r", ascending=False)
    write_csv("step5_portfolio_summary.csv", port_df)
    result_tables["Step 5 Portfolio"] = port_df

    cols = [
        "symbol",
        "label",
        "variant",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "worst_year_r",
        "worst_2y_r",
        "oos_trades",
        "oos_r",
    ]
    lines = [
        "# Sequential Countertrend / Portfolio Research 2026-05-27",
        "",
        "## Step 1: CHFJPY Two-Bar Exhaustion Short",
        "",
        markdown_table(two_df[[c for c in cols + ["confirm_mode", "rr", "stop_buffer_atr"] if c in two_df.columns]], 40),
        "",
        "## Step 2: CHFJPY Strong-Trend Avoidance",
        "",
        markdown_table(trend_df[[c for c in cols + ["h4"] if c in trend_df.columns]], 20),
        "",
        "## Step 3: CHFJPY Hour Robustness",
        "",
        markdown_table(hour_df[[c for c in cols + ["hour_set"] if c in hour_df.columns]], 20),
        "",
        "## Step 4: GBPJPY/AUDJPY Stretch Transfer",
        "",
        markdown_table(cross_df[[c for c in cols if c in cross_df.columns]], 40),
        "",
        "## Step 5: USDJPY + CHFJPY Portfolio",
        "",
        markdown_table(port_df[[c for c in cols if c in port_df.columns]], 20),
        "",
        "## Interpretation",
        "",
        "- This is a research pass, not final production approval.",
        "- The CHFJPY idea remains a short-side exhaustion setup, not a long-side falling-knife setup.",
        "- Two-bar confirmation is useful only if it improves robustness without killing the already-small sample.",
        "- Cross-symbol transfer is judged separately by symbol; no universal parameter should be assumed.",
    ]
    report_path = OUT_DIR / "report_ja.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {report_path}")
    for title, table in result_tables.items():
        print(f"\n== {title} ==")
        print(table[[c for c in cols if c in table.columns]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()

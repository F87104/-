#!/usr/bin/env python3
"""
H4 monthly/quarterly low-break continuation short study.

Hypothesis:
- A 1-3 month low update is more meaningful short context than an inverse-V.
- After the low update, wait for a pullback and another breakdown, or for
  tight stagnation near the low followed by a breakdown.

This script tests the idea mechanically on H4 data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    add_indicators,
    holiday_market,
    load_instrument,
    markdown_table,
    resample_ohlc,
    simulate_trade,
)
from run_indicator_compatibility_search import add_extended_features


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_28" / "monthly_low_rebreak_short"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
MAX_HOLD_BARS = 180


@dataclass(frozen=True)
class LowBreakSpec:
    name: str
    lookback_bars: int
    trigger_mode: str = "either"  # rebreak / stagnation / either
    max_after_break: int = 48
    min_wait_bars: int = 2
    pullback_min_atr: float = 0.75
    stag_bars: int = 3
    stag_range_atr: float = 1.0
    near_level_atr: float = 1.0
    break_buffer_atr: float = 0.06
    stop_buffer_atr: float = 0.25
    rr: float = 2.0


SPECS = [
    LowBreakSpec("L120_EITHER_PB075", 120, "either", pullback_min_atr=0.75),
    LowBreakSpec("L240_EITHER_PB075", 240, "either", pullback_min_atr=0.75),
    LowBreakSpec("L360_EITHER_PB075", 360, "either", pullback_min_atr=0.75),
    LowBreakSpec("L120_REBREAK_PB075", 120, "rebreak", pullback_min_atr=0.75),
    LowBreakSpec("L240_REBREAK_PB075", 240, "rebreak", pullback_min_atr=0.75),
    LowBreakSpec("L360_REBREAK_PB075", 360, "rebreak", pullback_min_atr=0.75),
    LowBreakSpec("L120_STAG_ONLY", 120, "stagnation", pullback_min_atr=0.75),
    LowBreakSpec("L240_STAG_ONLY", 240, "stagnation", pullback_min_atr=0.75),
    LowBreakSpec("L360_STAG_ONLY", 360, "stagnation", pullback_min_atr=0.75),
    LowBreakSpec("L240_EITHER_PB100", 240, "either", pullback_min_atr=1.00),
    LowBreakSpec("L360_EITHER_PB100", 360, "either", pullback_min_atr=1.00),
]


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


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict[str, float | int]:
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


def summary_row(name: str, sample: pd.DataFrame, notes: str = "") -> dict:
    train = sample[sample["period"].eq("train_2015_2020")] if not sample.empty else sample
    test = sample[sample["period"].eq("test_2021_2024")] if not sample.empty else sample
    oos = sample[sample["period"].eq("oos_2025_2026")] if not sample.empty else sample
    row = {"case": name, "notes": notes}
    row.update({f"all_{k}": v for k, v in metrics(sample).items()})
    row.update({f"train_{k}": v for k, v in metrics(train).items()})
    row.update({f"test_{k}": v for k, v in metrics(test).items()})
    row.update({f"oos_{k}": v for k, v in metrics(oos).items()})
    return row


def first_low_breaks(df: pd.DataFrame, spec: LowBreakSpec) -> pd.Series:
    prior_low = df["low"].shift(1).rolling(spec.lookback_bars, min_periods=spec.lookback_bars).min()
    prior_low_prev = prior_low.shift(1)
    buffer = df["atr"] * spec.break_buffer_atr
    break_now = df["close"] < prior_low - buffer
    was_broken = df["close"].shift(1) < prior_low_prev - buffer.shift(1)
    return (break_now & ~was_broken).fillna(False)


def low_break_signal(df: pd.DataFrame, break_i: int, spec: LowBreakSpec) -> dict | None:
    atr_break = float(df["atr"].iloc[break_i])
    if not math.isfinite(atr_break) or atr_break <= 0:
        return None

    prior_low = float(df["low"].shift(1).rolling(spec.lookback_bars).min().iloc[break_i])
    if not math.isfinite(prior_low):
        return None

    low_extreme = float(df["low"].iloc[break_i])
    extreme_i = break_i
    pullback_high = float(df["high"].iloc[break_i])
    pulled_back = False
    end_i = min(len(df) - 2, break_i + spec.max_after_break)

    for i in range(break_i + spec.min_wait_bars, end_i + 1):
        ts = df.index[i]
        if ts < START or ts > END or holiday_market(ts):
            continue
        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        close = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])
        low = float(df["low"].iloc[i])
        buffer = atr_i * spec.break_buffer_atr

        if not pulled_back:
            if low < low_extreme:
                low_extreme = low
                extreme_i = i
                pullback_high = high
            if high >= low_extreme + atr_i * spec.pullback_min_atr:
                pulled_back = True
                pullback_high = float(df["high"].iloc[extreme_i : i + 1].max())
        else:
            pullback_high = max(pullback_high, high)

        rebreak_ok = pulled_back and close < low_extreme - buffer

        stagnation_ok = False
        zone_high = np.nan
        zone_low = np.nan
        if i - break_i >= spec.stag_bars + 1:
            win = df.iloc[i - spec.stag_bars : i]
            zone_high = float(win["high"].max())
            zone_low = float(win["low"].min())
            zone_range = zone_high - zone_low
            tight = zone_range <= atr_i * spec.stag_range_atr
            near_broken_low = zone_high <= prior_low + atr_i * spec.near_level_atr
            touched_low_area = zone_low <= prior_low + atr_i * 0.30
            broke_zone_low = close < zone_low - buffer
            stagnation_ok = tight and near_broken_low and touched_low_area and broke_zone_low

        if spec.trigger_mode == "rebreak" and not rebreak_ok:
            continue
        if spec.trigger_mode == "stagnation" and not stagnation_ok:
            continue
        if spec.trigger_mode == "either" and not (rebreak_ok or stagnation_ok):
            continue

        if rebreak_ok and stagnation_ok:
            trigger_type = "rebreak+stagnation"
            stop_base = max(pullback_high, zone_high)
        elif rebreak_ok:
            trigger_type = "rebreak"
            stop_base = pullback_high
        else:
            trigger_type = "stagnation"
            stop_base = zone_high

        stop = stop_base + atr_i * spec.stop_buffer_atr
        target = close - (stop - close) * spec.rr
        if stop <= close or target >= close:
            continue

        return {
            "direction": "short",
            "trigger_type": trigger_type,
            "break_i": break_i,
            "trigger_i": i,
            "lookback_bars": spec.lookback_bars,
            "prior_low": prior_low,
            "break_low": float(df["low"].iloc[break_i]),
            "low_extreme": low_extreme,
            "pullback_high": pullback_high,
            "bars_after_break": i - break_i,
            "pullback_atr": (pullback_high - low_extreme) / atr_i,
            "break_depth_atr": (prior_low - float(df["close"].iloc[break_i])) / atr_break,
            "trigger_level": close,
            "stop": stop,
            "target": target,
            "risk_atr_at_signal": (stop - close) / atr_i,
            "break_key": f"{spec.lookback_bars}-{break_i}",
        }

    return None


def run_spec(df: pd.DataFrame, symbol: str, spec: LowBreakSpec) -> pd.DataFrame:
    breaks = first_low_breaks(df, spec)
    rows: list[dict] = []
    in_pos_until = -1
    used_breaks: set[str] = set()

    for break_i in np.flatnonzero(breaks.to_numpy()):
        if break_i <= in_pos_until or break_i >= len(df) - 2:
            continue
        ts = df.index[break_i]
        if ts < START or ts > END or holiday_market(ts):
            continue

        sig = low_break_signal(df, int(break_i), spec)
        if sig is None or sig["break_key"] in used_breaks:
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction="short",
            signal_i=int(sig["trigger_i"]),
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=MAX_HOLD_BARS,
        )
        if trade is None:
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
                "family": "monthly_low_rebreak_short",
                "signal_time": df.index[int(sig["trigger_i"])],
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "break_key"}},
                **features,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def build_trades() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    coverage = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        for spec in SPECS:
            trades = run_spec(df, symbol, spec)
            if not trades.empty:
                frames.append(trades)

    all_trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not all_trades.empty:
        for col in ["signal_time", "entry_time", "exit_time"]:
            all_trades[col] = pd.to_datetime(all_trades[col])
        all_trades["period"] = all_trades["entry_time"].map(classify_period)
        all_trades["year"] = all_trades["entry_time"].dt.year.astype(str)
        all_trades["month"] = all_trades["entry_time"].dt.to_period("M").astype(str)
        all_trades = all_trades.sort_values(["entry_time", "symbol", "strategy"]).reset_index(drop=True)
    return all_trades, pd.DataFrame(coverage)


def practical_masks(trades: pd.DataFrame) -> list[tuple[str, pd.Series, str]]:
    return [
        ("ALL", pd.Series(True, index=trades.index), "全候補"),
        ("ADX25", trades["adx14"].ge(25), "ADX>=25"),
        ("ADX25_RISK_LE3", trades["adx14"].ge(25) & trades["risk_atr_at_signal"].le(3.0), "ADX>=25 + risk<=3ATR"),
        ("GBP_AUD_ADX25", trades["symbol"].isin(["GBPJPY", "AUDJPY"]) & trades["adx14"].ge(25), "GBPJPY/AUDJPY + ADX>=25"),
        ("GBP_AUD_ADX25_RISK_LE3", trades["symbol"].isin(["GBPJPY", "AUDJPY"]) & trades["adx14"].ge(25) & trades["risk_atr_at_signal"].le(3.0), "GBPJPY/AUDJPY + ADX>=25 + risk<=3ATR"),
        ("REBREAK_ADX25", trades["trigger_type"].str.contains("rebreak") & trades["adx14"].ge(25), "rebreak系 + ADX>=25"),
        ("STAG_ADX25", trades["trigger_type"].str.contains("stagnation") & trades["adx14"].ge(25), "stagnation系 + ADX>=25"),
        ("LOW_BB_ADX25", trades["bb_pos"].le(0.25) & trades["adx14"].ge(25), "BB位置<=0.25 + ADX>=25"),
        ("MACD_TURN_ADX25", trades["macd_hist_slope3"].gt(0) & trades["adx14"].ge(25), "MACD slope3>0 + ADX>=25"),
        ("ADX30_RISK_LE2_BBW3_8", trades["adx14"].ge(30) & trades["risk_atr_at_signal"].le(2.0) & trades["bb_width_atr"].between(3.0, 8.0), "ADX>=30 + risk<=2ATR + BB幅3-8ATR"),
        ("ADX30_RISK_LE1_5_BBW3_8", trades["adx14"].ge(30) & trades["risk_atr_at_signal"].le(1.5) & trades["bb_width_atr"].between(3.0, 8.0), "ADX>=30 + risk<=1.5ATR + BB幅3-8ATR"),
        ("GBP_ADX25_RISK_LE2_5_BBW3_8", trades["symbol"].eq("GBPJPY") & trades["adx14"].ge(25) & trades["risk_atr_at_signal"].le(2.5) & trades["bb_width_atr"].between(3.0, 8.0), "GBPJPY + ADX>=25 + risk<=2.5ATR + BB幅3-8ATR"),
        ("GBP_ADX25_RISK_LE2_BARS_LE24", trades["symbol"].eq("GBPJPY") & trades["adx14"].ge(25) & trades["risk_atr_at_signal"].le(2.0) & trades["bars_after_break"].le(24), "GBPJPY + ADX>=25 + risk<=2ATR + 24本以内"),
    ]


def summarize(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    for spec, group in trades.groupby("strategy"):
        summary_rows.append(summary_row(spec, group, "base spec"))
        for name, mask, notes in practical_masks(group):
            if name == "ALL":
                continue
            summary_rows.append(summary_row(f"{spec}__{name}", group[mask.fillna(False)], notes))
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["score"] = (
            summary["all_total_r"]
            + summary["test_total_r"] * 1.5
            + summary["all_avg_r"] * 5
            + np.minimum(summary["all_pf"].replace(math.inf, 99), 5)
            - summary["all_max_dd_r"] * 0.25
            - np.where(summary["all_trades"] < 20, 2.0, 0.0)
            + np.where(summary["oos_total_r"] >= 0, 0.5, -1.0)
        )
        summary = summary.sort_values(["score", "all_total_r"], ascending=False).reset_index(drop=True)

    by_symbol_rows = []
    for (strategy, symbol), group in trades.groupby(["strategy", "symbol"]):
        row = {"strategy": strategy, "symbol": symbol}
        row.update(metrics(group))
        by_symbol_rows.append(row)
    by_symbol = pd.DataFrame(by_symbol_rows).sort_values("total_r", ascending=False) if by_symbol_rows else pd.DataFrame()

    by_trigger_rows = []
    for (strategy, trigger), group in trades.groupby(["strategy", "trigger_type"]):
        row = {"strategy": strategy, "trigger_type": trigger}
        row.update(metrics(group))
        by_trigger_rows.append(row)
    by_trigger = pd.DataFrame(by_trigger_rows).sort_values("total_r", ascending=False) if by_trigger_rows else pd.DataFrame()

    best_trades = pd.DataFrame()
    if not summary.empty:
        best_case = str(summary.iloc[0]["case"])
        if "__" in best_case:
            spec, mask_name = best_case.split("__", 1)
            group = trades[trades["strategy"].eq(spec)]
            masks = {name: mask for name, mask, _ in practical_masks(group)}
            best_trades = group[masks[mask_name].fillna(False)].copy()
        else:
            best_trades = trades[trades["strategy"].eq(best_case)].copy()
    return summary, by_symbol, by_trigger, best_trades


def write_report(
    coverage: pd.DataFrame,
    trades: pd.DataFrame,
    summary: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_trigger: pd.DataFrame,
    best_trades: pd.DataFrame,
) -> None:
    compact = [
        "case",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "train_trades",
        "train_total_r",
        "test_trades",
        "test_total_r",
        "oos_trades",
        "oos_total_r",
        "score",
        "notes",
    ]
    year_rows = []
    if not best_trades.empty:
        for year, group in best_trades.groupby("year"):
            row = {"year": year}
            row.update(metrics(group))
            year_rows.append(row)
    best_by_year = pd.DataFrame(year_rows).sort_values("year") if year_rows else pd.DataFrame()

    lines = [
        "# H4 1〜3ヶ月安値更新 戻り再下落ショート検証",
        "",
        "## 検証した考え方",
        "",
        "- H4で120/240/360本の過去安値を終値で更新したら、下落継続の環境認識にする。",
        "- 安値更新直後には売らず、戻り後の安値再ブレイク、または安値圏停滞からの下抜けを待つ。",
        "- エントリーは次足始値、SLは戻り高値または停滞レンジ高値の上、TPは2R。",
        "",
        "## データ範囲",
        "",
        markdown_table(coverage, 20),
        "",
        "## サマリー上位",
        "",
        markdown_table(summary[compact].head(60), 80) if not summary.empty else "_No rows._",
        "",
        "## 通貨別上位",
        "",
        markdown_table(by_symbol.head(80), 80) if not by_symbol.empty else "_No rows._",
        "",
        "## トリガー別上位",
        "",
        markdown_table(by_trigger.head(80), 80) if not by_trigger.empty else "_No rows._",
        "",
        "## 暫定ベスト 年別",
        "",
        markdown_table(best_by_year, 80) if not best_by_year.empty else "_No rows._",
        "",
        "## 実戦メモ",
        "",
        "- 1〜3ヶ月安値更新は、逆Vよりもショートの文脈として自然。",
        "- ただし、戻り高値をSLにするとリスク幅が広がりやすいため、risk<=3ATRなどの制限が重要。",
        "- rebreak型とstagnation型は別々に評価する。",
        "- OOSで崩れる候補は実戦採用しない。",
        "",
        "## 出力CSV",
        "",
        "- `trades.csv`",
        "- `summary.csv`",
        "- `by_symbol.csv`",
        "- `by_trigger.csv`",
        "- `best_trades.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    trades, coverage = build_trades()
    trades.to_csv(OUT_DIR / "trades.csv", index=False)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if trades.empty:
        (OUT_DIR / "report_ja.md").write_text("# H4 1〜3ヶ月安値更新 戻り再下落ショート検証\n\nNo trades.", encoding="utf-8")
        print("No trades")
        return

    summary, by_symbol, by_trigger, best_trades = summarize(trades)
    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "by_trigger.csv", index=False)
    best_trades.to_csv(OUT_DIR / "best_trades.csv", index=False)
    write_report(coverage, trades, summary, by_symbol, by_trigger, best_trades)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary[["case", "all_trades", "all_total_r", "all_avg_r", "all_pf", "test_trades", "test_total_r", "oos_trades", "oos_total_r", "score"]].head(30).to_string(index=False))


if __name__ == "__main__":
    main()

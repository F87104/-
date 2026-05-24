#!/usr/bin/env python3
"""
Study: non-Fibonacci filters for sharp-drop V recovery candidates.

The V context still uses the existing candidate engine, but this study does
not optimize Fibonacci levels. It asks a different question:

    After a V-recovery candidate and trigger appear, which non-Fib tools help
    distinguish better trades?

Tools tested:
- EMA regime and slope
- ADX trend strength
- RSI momentum zone
- Donchian breakout confirmation
- Bollinger width / volatility expansion
- ATR percentile / high-volatility avoidance
- Candle body and close location
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    add_indicators,
    load_instrument,
    markdown_table,
    resample_ohlc,
    summarize,
)
from run_v_recovery_trigger_study import TriggerSpec, run_spec as run_trigger_spec


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2015_2024" / "v_recovery_non_fibo_tools"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"

# Use the two practical trigger variants found in the prior study.
BASE_SPECS = [
    TriggerSpec("T4_REBREAK_ONLY", trigger_mode="rebreak"),
    TriggerSpec("T5_STAG_OR_REBREAK", trigger_mode="either"),
]


@dataclass(frozen=True)
class ToolFilter:
    name: str
    family: str
    description: str
    fn: Callable[[pd.DataFrame], pd.Series]


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


def rolling_percentile_last(series: pd.Series, length: int) -> pd.Series:
    def pct(values: np.ndarray) -> float:
        last = values[-1]
        if not np.isfinite(last):
            return np.nan
        return float((values <= last).mean() * 100)

    return series.rolling(length, min_periods=length).apply(pct, raw=True)


def add_tool_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["ema20_slope_10_atr"] = (out["ema20"] - out["ema20"].shift(10)) / out["atr"].replace(0.0, np.nan)
    out["rsi14"] = rsi(out["close"], 14)
    out["adx14"] = adx(out, 14)

    basis = out["close"].rolling(20, min_periods=20).mean()
    stdev = out["close"].rolling(20, min_periods=20).std()
    upper = basis + stdev * 2
    lower = basis - stdev * 2
    out["bb_width_atr"] = (upper - lower) / out["atr"].replace(0.0, np.nan)
    out["bb_pos"] = (out["close"] - lower) / (upper - lower).replace(0.0, np.nan)

    out["donchian20_high_prev"] = out["high"].rolling(20, min_periods=20).max().shift(1)
    out["donchian55_high_prev"] = out["high"].rolling(55, min_periods=55).max().shift(1)
    out["donchian20_break"] = out["close"] > out["donchian20_high_prev"]
    out["donchian55_break"] = out["close"] > out["donchian55_high_prev"]

    out["atr50"] = out["atr"].rolling(50, min_periods=50).mean()
    out["atr_ratio_50"] = out["atr"] / out["atr50"].replace(0.0, np.nan)
    out["atr_pctile_252"] = rolling_percentile_last(out["atr"], 252)

    bar_range = (out["high"] - out["low"]).replace(0.0, np.nan)
    out["close_location"] = ((out["close"] - out["low"]) / bar_range).fillna(0.5)
    out["range5_atr"] = (out["high"].rolling(5).max() - out["low"].rolling(5).min()) / out["atr"].replace(0.0, np.nan)
    return out


def build_filters() -> list[ToolFilter]:
    return [
        ToolFilter("ALL_BASELINE", "baseline", "フィルターなし", lambda x: pd.Series(True, index=x.index)),
        ToolFilter("EMA_close_gt_50", "EMA", "終値がEMA50より上", lambda x: x["close"] > x["ema50"]),
        ToolFilter("EMA_close_gt_200", "EMA", "終値がEMA200より上", lambda x: x["close"] > x["ema200"]),
        ToolFilter("EMA_20_gt_50", "EMA", "EMA20がEMA50より上", lambda x: x["ema20"] > x["ema50"]),
        ToolFilter("EMA_stack_20_50_200", "EMA", "EMA20 > EMA50 > EMA200", lambda x: (x["ema20"] > x["ema50"]) & (x["ema50"] > x["ema200"])),
        ToolFilter("EMA20_slope_pos", "EMA", "EMA20の10本傾きがプラス", lambda x: x["ema20_slope_10_atr"] > 0),
        ToolFilter("ADX_ge_18", "ADX", "ADX14 >= 18", lambda x: x["adx14"] >= 18),
        ToolFilter("ADX_ge_22", "ADX", "ADX14 >= 22", lambda x: x["adx14"] >= 22),
        ToolFilter("ADX_ge_25", "ADX", "ADX14 >= 25", lambda x: x["adx14"] >= 25),
        ToolFilter("RSI_45_75", "RSI", "RSI14が45〜75", lambda x: x["rsi14"].between(45, 75)),
        ToolFilter("RSI_50_75", "RSI", "RSI14が50〜75", lambda x: x["rsi14"].between(50, 75)),
        ToolFilter("RSI_gt_50", "RSI", "RSI14 > 50", lambda x: x["rsi14"] > 50),
        ToolFilter("RSI_lt_75", "RSI", "RSI14 < 75で過熱回避", lambda x: x["rsi14"] < 75),
        ToolFilter("Donchian20_break", "Donchian", "20本高値を終値で更新", lambda x: x["donchian20_break"]),
        ToolFilter("Donchian55_break", "Donchian", "55本高値を終値で更新", lambda x: x["donchian55_break"]),
        ToolFilter("BB_pos_60_110", "Bollinger", "BB内位置が上側60%〜軽い上抜け", lambda x: x["bb_pos"].between(0.60, 1.10)),
        ToolFilter("BB_width_ge_3ATR", "Bollinger", "BB幅が3ATR以上", lambda x: x["bb_width_atr"] >= 3.0),
        ToolFilter("BB_width_ge_4ATR", "Bollinger", "BB幅が4ATR以上", lambda x: x["bb_width_atr"] >= 4.0),
        ToolFilter("ATR_pctile_20_90", "ATR", "ATRが過小/過大すぎない 20〜90%", lambda x: x["atr_pctile_252"].between(20, 90)),
        ToolFilter("ATR_pctile_lt_85", "ATR", "ATR上位15%の荒れ相場を除外", lambda x: x["atr_pctile_252"] < 85),
        ToolFilter("ATR_ratio_lt_1_5", "ATR", "ATR14がATR50の1.5倍未満", lambda x: x["atr_ratio_50"] < 1.5),
        ToolFilter("Body_ge_60", "Candle", "実体比率60%以上", lambda x: x["body_ratio"] >= 0.60),
        ToolFilter("CloseLoc_ge_65", "Candle", "終値が足の上側35%以内", lambda x: x["close_location"] >= 0.65),
        ToolFilter("Range5_le_6ATR", "Compression", "直近5本レンジが6ATR以下", lambda x: x["range5_atr"] <= 6.0),
        ToolFilter("EMA_RSI_ATR", "Combo", "EMA20>50、RSI50〜75、ATR過大除外", lambda x: (x["ema20"] > x["ema50"]) & x["rsi14"].between(50, 75) & (x["atr_pctile_252"] < 85)),
        ToolFilter("ADX_Donchian_Body", "Combo", "ADX>=18、20本高値更新、実体60%以上", lambda x: (x["adx14"] >= 18) & x["donchian20_break"] & (x["body_ratio"] >= 0.60)),
        ToolFilter("Trend_Momentum_Close", "Combo", "EMA20>50、RSI>50、終値位置65%以上", lambda x: (x["ema20"] > x["ema50"]) & (x["rsi14"] > 50) & (x["close_location"] >= 0.65)),
    ]


def enrich_trades(trades: pd.DataFrame, feature_frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    if trades.empty:
        return trades

    rows: list[dict] = []
    feature_cols = [
        "close",
        "ema20",
        "ema50",
        "ema200",
        "ema20_slope_10_atr",
        "rsi14",
        "adx14",
        "bb_width_atr",
        "bb_pos",
        "donchian20_high_prev",
        "donchian55_high_prev",
        "donchian20_break",
        "donchian55_break",
        "atr_ratio_50",
        "atr_pctile_252",
        "body_ratio",
        "close_location",
        "range5_atr",
    ]
    for row in trades.to_dict("records"):
        key = (row["symbol"], row["timeframe"])
        df = feature_frames[key]
        ts = pd.Timestamp(row["signal_time"])
        if ts not in df.index:
            continue
        feat = df.loc[ts, feature_cols].to_dict()
        rows.append({**row, **feat})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["signal_time"] = pd.to_datetime(out["signal_time"])
        out = out.sort_values(["signal_time", "symbol"]).reset_index(drop=True)
    return out


def summarize_filter(filtered: pd.DataFrame, filt: ToolFilter, base_name: str) -> dict:
    if filtered.empty:
        return {
            "base_strategy": base_name,
            "filter": filt.name,
            "family": filt.family,
            "description": filt.description,
            "trades": 0,
            "win_rate": 0.0,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": 0.0,
            "pf_after_cost": np.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "avg_hold_bars": np.nan,
        }
    tmp = filtered.copy()
    tmp["filter"] = filt.name
    summary = summarize(tmp, ["filter"]).iloc[0].to_dict()
    return {
        "base_strategy": base_name,
        "filter": filt.name,
        "family": filt.family,
        "description": filt.description,
        **{k: summary[k] for k in summary if k != "filter"},
    }


def run() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    base_rows: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        df = add_tool_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        feature_frames[(symbol, TIMEFRAME)] = df
        for spec in BASE_SPECS:
            trades = run_trigger_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                base_rows.append(trades)

    base_trades = pd.concat(base_rows, ignore_index=True) if base_rows else pd.DataFrame()
    enriched = enrich_trades(base_trades, feature_frames)
    filters = build_filters()

    summary_rows: list[dict] = []
    by_symbol_rows: list[pd.DataFrame] = []
    for base_name, group in enriched.groupby("strategy"):
        for filt in filters:
            mask = filt.fn(group).fillna(False)
            filtered = group[mask].copy().sort_values(["signal_time", "symbol"])
            summary_rows.append(summarize_filter(filtered, filt, base_name))
            if not filtered.empty:
                tmp = filtered.copy()
                tmp["filter"] = filt.name
                sym_summary = summarize(tmp, ["strategy", "filter", "symbol"])
                sym_summary["family"] = filt.family
                by_symbol_rows.append(sym_summary)

    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary = summary.sort_values(["base_strategy", "total_r_after_cost", "pf_after_cost"], ascending=[True, False, False])
    by_symbol = pd.concat(by_symbol_rows, ignore_index=True) if by_symbol_rows else pd.DataFrame()
    return enriched, summary, by_symbol


def write_report(enriched: pd.DataFrame, summary: pd.DataFrame, by_symbol: pd.DataFrame) -> None:
    enriched.to_csv(OUT_DIR / "trades_enriched.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_filters.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)

    lines = [
        "# H4 V候補後トリガー 非フィボツール研究 2015-2024",
        "",
        "## 目的",
        "",
        "フィボナッチ水準だけに頼らず、EMA/ADX/RSI/ボリンジャー/ドンチャン/ATR/ローソク足の視点で、V候補後トリガーの質を判定する。",
        "",
        "## 使ったベース",
        "",
        "- H4のみ。",
        "- 買いのみ。",
        "- 既存のV候補後トリガーから、`T4_REBREAK_ONLY` と `T5_STAG_OR_REBREAK` をベースにした。",
        "- 各フィルターは、シグナル足の状態だけで判定。",
        "",
        "## フィルター別 結果",
        "",
        markdown_table(summary, 80),
        "",
        "## 通貨別 結果",
        "",
        markdown_table(by_symbol, 120),
        "",
        "## 出力",
        "",
        "- `trades_enriched.csv`",
        "- `summary_filters.csv`",
        "- `summary_by_symbol.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    enriched, summary, by_symbol = run()
    write_report(enriched, summary, by_symbol)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

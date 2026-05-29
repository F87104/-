#!/usr/bin/env python3
"""
Study: market reaction after common indicator signals are denied.

The goal is not to prove a ready-to-trade system immediately. It is to turn
"indicator denial" into numeric evidence that can feed future setup design.

Definitions tested:
- Bollinger outer-band breakout returns inside.
- RSI 70/30 momentum/extreme signal reverses back through the threshold.
- EMA50/EMA200 close cross fails back through the average.
- MACD signal-line cross fails back the other way.
- Donchian breakout fails back inside the breakout level.

Each denial enters in the opposite direction on the next bar open, with
1 ATR stop, 1.5R target, and short maximum holding periods.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    add_indicators,
    holiday_market,
    load_instrument,
    markdown_table,
    resample_ohlc,
    simulate_trade,
    summarize,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_29" / "indicator_denial_reaction"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RUN_TIMEFRAMES = ["H4", "D1"]
MAX_HOLD = {"H4": 24, "D1": 20}


@dataclass(frozen=True)
class DenialSpec:
    name: str
    family: str
    fail_window: int
    quality: bool = False
    donchian_len: int = 20
    rr: float = 1.5
    stop_atr: float = 1.0
    body_min: float = 0.40
    close_location_min: float = 0.60


SPECS: list[DenialSpec] = [
    DenialSpec("BB_OUTER_REJECT_3", "Bollinger外側否定", 3),
    DenialSpec("BB_OUTER_REJECT_6", "Bollinger外側否定", 6),
    DenialSpec("BB_OUTER_REJECT_12", "Bollinger外側否定", 12),
    DenialSpec("BB_OUTER_REJECT_6_Q", "Bollinger外側否定", 6, quality=True),
    DenialSpec("RSI_70_30_REJECT_6", "RSI 70/30否定", 6),
    DenialSpec("RSI_70_30_REJECT_6_Q", "RSI 70/30否定", 6, quality=True),
    DenialSpec("EMA50_CROSS_FAIL_6", "EMA50クロス否定", 6),
    DenialSpec("EMA50_CROSS_FAIL_6_Q", "EMA50クロス否定", 6, quality=True),
    DenialSpec("EMA200_CROSS_FAIL_6", "EMA200クロス否定", 6),
    DenialSpec("EMA200_CROSS_FAIL_6_Q", "EMA200クロス否定", 6, quality=True),
    DenialSpec("MACD_SIGNAL_CROSS_FAIL_6", "MACDクロス否定", 6),
    DenialSpec("MACD_SIGNAL_CROSS_FAIL_6_Q", "MACDクロス否定", 6, quality=True),
    DenialSpec("DONCHIAN20_FALSE_BREAK_6", "Donchian高安値更新否定", 6, donchian_len=20),
    DenialSpec("DONCHIAN20_FALSE_BREAK_6_Q", "Donchian高安値更新否定", 6, quality=True, donchian_len=20),
    DenialSpec("DONCHIAN55_FALSE_BREAK_6", "Donchian高安値更新否定", 6, donchian_len=55),
    DenialSpec("DONCHIAN55_FALSE_BREAK_6_Q", "Donchian高安値更新否定", 6, quality=True, donchian_len=55),
]


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100 - 100 / (1 + rs)


def add_denial_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["sma20"] = out["close"].rolling(20).mean()
    out["std20"] = out["close"].rolling(20).std(ddof=0)
    out["bb_upper"] = out["sma20"] + out["std20"] * 2.0
    out["bb_lower"] = out["sma20"] - out["std20"] * 2.0
    out["bb_width_atr"] = (out["bb_upper"] - out["bb_lower"]) / out["atr"]
    out["rsi14"] = rsi(out["close"], 14)
    macd = out["close"].ewm(span=12, adjust=False).mean() - out["close"].ewm(span=26, adjust=False).mean()
    out["macd"] = macd
    out["macd_signal"] = macd.ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    out["donchian20_high"] = out["high"].rolling(20).max().shift(1)
    out["donchian20_low"] = out["low"].rolling(20).min().shift(1)
    out["donchian55_high"] = out["high"].rolling(55).max().shift(1)
    out["donchian55_low"] = out["low"].rolling(55).min().shift(1)
    rng = (out["high"] - out["low"]).replace(0.0, np.nan)
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.5)
    return out


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "Research_2015_2024"
    return "OOS_2025_2026"


def quality_ok(df: pd.DataFrame, i: int, direction: str, spec: DenialSpec) -> bool:
    if not spec.quality:
        return True
    body = float(df["body_ratio"].iloc[i])
    close_loc = float(df["close_location"].iloc[i])
    if body < spec.body_min:
        return False
    if direction == "long":
        return close_loc >= spec.close_location_min
    return close_loc <= 1.0 - spec.close_location_min


def crossed_above(a: pd.Series, b: pd.Series, i: int) -> bool:
    return float(a.iloc[i - 1]) <= float(b.iloc[i - 1]) and float(a.iloc[i]) > float(b.iloc[i])


def crossed_below(a: pd.Series, b: pd.Series, i: int) -> bool:
    return float(a.iloc[i - 1]) >= float(b.iloc[i - 1]) and float(a.iloc[i]) < float(b.iloc[i])


def pending_signals(df: pd.DataFrame, i: int, spec: DenialSpec) -> tuple[bool, bool, float | None, float | None]:
    """Return new bullish/bearish indicator signals and their failure levels."""
    close = df["close"]
    if spec.name.startswith("BB_"):
        bull = float(close.iloc[i]) > float(df["bb_upper"].iloc[i])
        bear = float(close.iloc[i]) < float(df["bb_lower"].iloc[i])
        return bull, bear, float(df["bb_upper"].iloc[i]), float(df["bb_lower"].iloc[i])
    if spec.name.startswith("RSI_"):
        r = df["rsi14"]
        bull = float(r.iloc[i - 1]) <= 70.0 and float(r.iloc[i]) > 70.0
        bear = float(r.iloc[i - 1]) >= 30.0 and float(r.iloc[i]) < 30.0
        return bull, bear, 70.0, 30.0
    if spec.name.startswith("EMA50_"):
        bull = crossed_above(close, df["ema50"], i)
        bear = crossed_below(close, df["ema50"], i)
        return bull, bear, float(df["ema50"].iloc[i]), float(df["ema50"].iloc[i])
    if spec.name.startswith("EMA200_"):
        bull = crossed_above(close, df["ema200"], i)
        bear = crossed_below(close, df["ema200"], i)
        return bull, bear, float(df["ema200"].iloc[i]), float(df["ema200"].iloc[i])
    if spec.name.startswith("MACD_"):
        bull = crossed_above(df["macd"], df["macd_signal"], i)
        bear = crossed_below(df["macd"], df["macd_signal"], i)
        return bull, bear, float(df["macd_signal"].iloc[i]), float(df["macd_signal"].iloc[i])
    if spec.name.startswith("DONCHIAN"):
        high_col = f"donchian{spec.donchian_len}_high"
        low_col = f"donchian{spec.donchian_len}_low"
        high_level = float(df[high_col].iloc[i])
        low_level = float(df[low_col].iloc[i])
        bull = math.isfinite(high_level) and float(close.iloc[i]) > high_level
        bear = math.isfinite(low_level) and float(close.iloc[i]) < low_level
        return bull, bear, high_level, low_level
    return False, False, None, None


def is_denial(df: pd.DataFrame, i: int, spec: DenialSpec, pending_side: str, level: float | None) -> bool:
    close = float(df["close"].iloc[i])
    if level is None or not math.isfinite(level):
        return False
    if spec.name.startswith("BB_"):
        return close < float(df["bb_upper"].iloc[i]) if pending_side == "bull" else close > float(df["bb_lower"].iloc[i])
    if spec.name.startswith("RSI_"):
        val = float(df["rsi14"].iloc[i])
        prev = float(df["rsi14"].iloc[i - 1])
        return (prev >= 70.0 and val < 70.0) if pending_side == "bull" else (prev <= 30.0 and val > 30.0)
    if spec.name.startswith("EMA50_"):
        ema = float(df["ema50"].iloc[i])
        return close < ema if pending_side == "bull" else close > ema
    if spec.name.startswith("EMA200_"):
        ema = float(df["ema200"].iloc[i])
        return close < ema if pending_side == "bull" else close > ema
    if spec.name.startswith("MACD_"):
        macd = float(df["macd"].iloc[i])
        signal = float(df["macd_signal"].iloc[i])
        prev_macd = float(df["macd"].iloc[i - 1])
        prev_signal = float(df["macd_signal"].iloc[i - 1])
        return (prev_macd >= prev_signal and macd < signal) if pending_side == "bull" else (prev_macd <= prev_signal and macd > signal)
    if spec.name.startswith("DONCHIAN"):
        return close < level if pending_side == "bull" else close > level
    return False


def forward_reaction(df: pd.DataFrame, i: int, direction: str, atr_i: float) -> dict:
    sign = 1.0 if direction == "long" else -1.0
    close_i = float(df["close"].iloc[i])
    out: dict[str, float | bool] = {}
    for h in [4, 8, 16, 24]:
        if i + h < len(df):
            out[f"fwd_{h}_atr"] = sign * (float(df["close"].iloc[i + h]) - close_i) / atr_i
        else:
            out[f"fwd_{h}_atr"] = math.nan
    for h in [8, 16, 24]:
        end = min(len(df) - 1, i + h)
        if end <= i:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"mae_{h}_atr"] = math.nan
            out[f"hit_1atr_before_minus1atr_{h}"] = False
            continue
        window = df.iloc[i + 1 : end + 1]
        if direction == "long":
            mfe = (float(window["high"].max()) - close_i) / atr_i
            mae = (float(window["low"].min()) - close_i) / atr_i
        else:
            mfe = (close_i - float(window["low"].min())) / atr_i
            mae = (close_i - float(window["high"].max())) / atr_i
        out[f"mfe_{h}_atr"] = mfe
        out[f"mae_{h}_atr"] = mae

        hit = False
        decided = False
        for _, row in window.iterrows():
            if direction == "long":
                hit_fav = float(row["high"]) >= close_i + atr_i
                hit_bad = float(row["low"]) <= close_i - atr_i
            else:
                hit_fav = float(row["low"]) <= close_i - atr_i
                hit_bad = float(row["high"]) >= close_i + atr_i
            if hit_fav or hit_bad:
                hit = hit_fav and not hit_bad
                decided = True
                break
        out[f"hit_1atr_before_minus1atr_{h}"] = bool(hit and decided)
    return out


def run_spec(df: pd.DataFrame, symbol: str, timeframe: str, spec: DenialSpec) -> pd.DataFrame:
    rows: list[dict] = []
    pending_bull_i: int | None = None
    pending_bear_i: int | None = None
    pending_bull_level: float | None = None
    pending_bear_level: float | None = None
    in_pos_until = -1

    for i in range(2, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue

        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue

        bull_signal, bear_signal, bull_level, bear_level = pending_signals(df, i, spec)
        if bull_signal:
            pending_bull_i = i
            pending_bull_level = bull_level
        if bear_signal:
            pending_bear_i = i
            pending_bear_level = bear_level

        if pending_bull_i is not None and i - pending_bull_i > spec.fail_window:
            pending_bull_i = None
            pending_bull_level = None
        if pending_bear_i is not None and i - pending_bear_i > spec.fail_window:
            pending_bear_i = None
            pending_bear_level = None

        if i <= in_pos_until:
            continue

        event: dict | None = None
        if pending_bull_i is not None and i > pending_bull_i and is_denial(df, i, spec, "bull", pending_bull_level):
            direction = "short"
            if quality_ok(df, i, direction, spec):
                event = {
                    "denied_side": "bullish",
                    "direction": direction,
                    "base_signal_i": pending_bull_i,
                    "fail_bars": i - pending_bull_i,
                    "denial_level": pending_bull_level,
                }
            pending_bull_i = None
            pending_bull_level = None
        elif pending_bear_i is not None and i > pending_bear_i and is_denial(df, i, spec, "bear", pending_bear_level):
            direction = "long"
            if quality_ok(df, i, direction, spec):
                event = {
                    "denied_side": "bearish",
                    "direction": direction,
                    "base_signal_i": pending_bear_i,
                    "fail_bars": i - pending_bear_i,
                    "denial_level": pending_bear_level,
                }
            pending_bear_i = None
            pending_bear_level = None

        if event is None:
            continue

        close = float(df["close"].iloc[i])
        if event["direction"] == "long":
            stop = close - atr_i * spec.stop_atr
            target = close + (close - stop) * spec.rr
        else:
            stop = close + atr_i * spec.stop_atr
            target = close - (stop - close) * spec.rr

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=event["direction"],
            signal_i=i,
            stop=stop,
            target=target,
            max_hold_bars=MAX_HOLD[timeframe],
        )
        if trade is None:
            continue

        reaction = forward_reaction(df, i, event["direction"], atr_i)
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": spec.name,
                "family": spec.family,
                "quality_filter": spec.quality,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                "atr": atr_i,
                "body_ratio": float(df["body_ratio"].iloc[i]),
                "close_location": float(df["close_location"].iloc[i]),
                "rsi14": float(df["rsi14"].iloc[i]) if pd.notna(df["rsi14"].iloc[i]) else math.nan,
                "bb_width_atr": float(df["bb_width_atr"].iloc[i]) if pd.notna(df["bb_width_atr"].iloc[i]) else math.nan,
                **event,
                **reaction,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def summarize_reaction(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    base = summarize(events, group_cols)
    rows = []
    for key, group in events.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple))
        for col in ["fwd_4_atr", "fwd_8_atr", "fwd_16_atr", "fwd_24_atr", "mfe_16_atr", "mae_16_atr"]:
            row[f"avg_{col}"] = float(group[col].mean())
        row["hit_1atr_first_16"] = float(group["hit_1atr_before_minus1atr_16"].mean() * 100)
        rows.append(row)
    reaction = pd.DataFrame(rows)
    return base.merge(reaction, on=group_cols, how="left").sort_values(
        ["total_r_after_cost", "pf_after_cost"], ascending=[False, False]
    )


def write_report(
    events: pd.DataFrame,
    overall: pd.DataFrame,
    h4_overall: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_period: pd.DataFrame,
    by_direction: pd.DataFrame,
    candidate_direction: pd.DataFrame,
    candidate_period_direction: pd.DataFrame,
    candidate_symbol: pd.DataFrame,
) -> None:
    lines = [
        "# 一般インジケータ否定後の相場反応 検証 2026-05-29",
        "",
        "## 目的",
        "",
        "一般的に見られるインジケータのシグナルが短時間で否定された後、相場が逆方向へ反応しやすいかを数値化する。",
        "",
        "## 否定の定義",
        "",
        "- BB外側否定: 終値がBB外側へ出た後、指定本数以内にバンド内へ戻る。",
        "- RSI否定: RSIが70上抜け後に70割れ、または30割れ後に30上抜け。",
        "- EMA否定: 終値のEMA50/EMA200上抜け・下抜けが指定本数以内に逆側へ戻る。",
        "- MACD否定: MACDのシグナル線クロスが指定本数以内に逆クロスする。",
        "- Donchian否定: 20/55本高安値更新が指定本数以内にブレイク水準内へ戻る。",
        "",
        "## 共通売買モデル",
        "",
        "- 否定方向へ次足始値でEntry。",
        "- SL: 1ATR。",
        "- TP: 1.5R。",
        "- 最大保有: H4は24本、D1は20本。",
        "- 2015-2024をResearch、2025-2026をOOS。",
        "",
        "## 全体上位",
        "",
        markdown_table(overall, 40),
        "",
        "## H4上位",
        "",
        markdown_table(h4_overall, 40),
        "",
        "## 実戦候補: D1否定ロング方向",
        "",
        "単純なH4逆張りではなく、D1の一般インジケータ否定を上位環境として使う候補。",
        "",
        markdown_table(candidate_direction, 20),
        "",
        "## 実戦候補 期間・方向別",
        "",
        markdown_table(candidate_period_direction, 40),
        "",
        "## 実戦候補 通貨別",
        "",
        markdown_table(candidate_symbol, 60),
        "",
        "## 方向別",
        "",
        markdown_table(by_direction, 80),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 80),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 120),
        "",
        "## 出力",
        "",
        "- `events.csv`",
        "- `summary_overall.csv`",
        "- `summary_h4_overall.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_period.csv`",
        "- `summary_by_direction.csv`",
        "- `summary_candidate_direction.csv`",
        "- `summary_candidate_period_direction.csv`",
        "- `summary_candidate_symbol.csv`",
        "- `data_coverage.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_events: list[pd.DataFrame] = []
    coverage_rows: list[dict] = []

    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        for timeframe in RUN_TIMEFRAMES:
            df = add_denial_indicators(resample_ohlc(raw, timeframe))
            for spec in SPECS:
                events = run_spec(df, symbol, timeframe, spec)
                if not events.empty:
                    all_events.append(events)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if not all_events:
        (OUT_DIR / "report_ja.md").write_text("# Indicator denial reaction\n\nNo events.", encoding="utf-8")
        print(f"No events. Report: {OUT_DIR / 'report_ja.md'}")
        return

    events_df = pd.concat(all_events, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        events_df[col] = pd.to_datetime(events_df[col])
    events_df = events_df.sort_values(["timeframe", "strategy", "entry_time", "symbol"]).reset_index(drop=True)
    events_df.to_csv(OUT_DIR / "events.csv", index=False)

    overall = summarize_reaction(events_df, ["timeframe", "family", "strategy"])
    h4_overall = overall[overall["timeframe"] == "H4"].copy()
    by_symbol = summarize_reaction(events_df, ["timeframe", "family", "strategy", "symbol"])
    by_period = summarize_reaction(events_df, ["timeframe", "family", "strategy", "period"])
    by_direction = summarize_reaction(events_df, ["timeframe", "family", "strategy", "direction"])
    candidate_keys = [
        "DONCHIAN20_FALSE_BREAK_6_Q",
        "DONCHIAN55_FALSE_BREAK_6_Q",
        "RSI_70_30_REJECT_6_Q",
    ]
    candidate = events_df[
        (events_df["timeframe"] == "D1")
        & (events_df["strategy"].isin(candidate_keys))
    ].copy()
    candidate_direction = summarize_reaction(candidate, ["strategy", "direction"])
    candidate_period_direction = summarize_reaction(candidate, ["strategy", "period", "direction"])
    candidate_symbol = summarize_reaction(candidate, ["strategy", "symbol"])

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    h4_overall.to_csv(OUT_DIR / "summary_h4_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    by_direction.to_csv(OUT_DIR / "summary_by_direction.csv", index=False)
    candidate_direction.to_csv(OUT_DIR / "summary_candidate_direction.csv", index=False)
    candidate_period_direction.to_csv(OUT_DIR / "summary_candidate_period_direction.csv", index=False)
    candidate_symbol.to_csv(OUT_DIR / "summary_candidate_symbol.csv", index=False)
    write_report(
        events_df,
        overall,
        h4_overall,
        by_symbol,
        by_period,
        by_direction,
        candidate_direction,
        candidate_period_direction,
        candidate_symbol,
    )

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(h4_overall.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Study: Trap / false-break reaction.

Market psychology hypothesis:
    Breakout traders are trapped when price updates a visible high/low but
    quickly closes back inside. The forced unwind should create an opposite
    directional reaction.

This script tests two mechanical trap definitions:
    1. wick_trap: intrabar high/low updates the prior Donchian level, but the
       same candle closes back inside.
    2. close_fail: candle closes outside the prior Donchian level, then closes
       back inside within N bars.

Entries are intentionally simple: next bar open in the denial direction.
Stops use the trap extreme plus an ATR buffer. Targets use fixed R.
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
    direction_cost_r,
    holiday_market,
    load_instrument,
    markdown_table,
    resample_ohlc,
    summarize,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_30" / "trap_false_break_reaction"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RUN_TIMEFRAMES = ["H4", "D1"]
MAX_HOLD = {"H4": 36, "D1": 20}


@dataclass(frozen=True)
class TrapSpec:
    name: str
    trap_kind: str  # wick or close_fail
    lookback: int
    fail_window: int = 6
    break_buffer_atr: float = 0.05
    reclaim_buffer_atr: float = 0.00
    quality: str = "none"  # none, body_close, wick_activity, strict
    rr: float = 1.5
    stop_buffer_atr: float = 0.25
    max_risk_atr: float = 3.0


SPECS: list[TrapSpec] = []
for lb in [20, 55, 120]:
    SPECS.extend(
        [
            TrapSpec(f"WICK_L{lb}_RAW_RR15", "wick", lb, quality="none"),
            TrapSpec(f"WICK_L{lb}_BODY_RR15", "wick", lb, quality="body_close"),
            TrapSpec(f"WICK_L{lb}_ACTIVITY_RR15", "wick", lb, quality="wick_activity"),
            TrapSpec(f"WICK_L{lb}_STRICT_RR15", "wick", lb, quality="strict"),
            TrapSpec(f"CLOSEFAIL_L{lb}_W6_BODY_RR15", "close_fail", lb, fail_window=6, quality="body_close"),
            TrapSpec(f"CLOSEFAIL_L{lb}_W6_ACTIVITY_RR15", "close_fail", lb, fail_window=6, quality="wick_activity"),
            TrapSpec(f"CLOSEFAIL_L{lb}_W8_STRICT_RR15", "close_fail", lb, fail_window=8, quality="strict"),
        ]
    )


def add_trap_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["tr"] = tr
    out["tr_avg30"] = tr.rolling(30, min_periods=30).mean()
    out["range_atr"] = tr / out["atr"].replace(0.0, np.nan)
    out["activity_ratio"] = tr / out["tr_avg30"].replace(0.0, np.nan)
    out["atr_expansion_20"] = out["atr"] / out["atr"].shift(20).replace(0.0, np.nan)
    rng = (out["high"] - out["low"]).replace(0.0, np.nan)
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.5)
    out["lower_wick_atr"] = (np.minimum(out["open"], out["close"]) - out["low"]) / out["atr"].replace(0.0, np.nan)
    out["upper_wick_atr"] = (out["high"] - np.maximum(out["open"], out["close"])) / out["atr"].replace(0.0, np.nan)
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema50_slope_20_atr"] = (out["ema50"] - out["ema50"].shift(20)).abs() / out["atr"].replace(0.0, np.nan)
    out["range60_atr"] = (out["high"].rolling(60).max() - out["low"].rolling(60).min()) / out["atr"].replace(0.0, np.nan)
    for lb in [20, 55, 120]:
        out[f"donchian{lb}_high"] = out["high"].rolling(lb, min_periods=lb).max().shift(1)
        out[f"donchian{lb}_low"] = out["low"].rolling(lb, min_periods=lb).min().shift(1)
    return out


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "Research_2015_2024"
    return "OOS_2025_2026"


def quality_ok(df: pd.DataFrame, i: int, direction: str, spec: TrapSpec) -> bool:
    if spec.quality == "none":
        return True

    body = float(df["body_ratio"].iloc[i])
    close_loc = float(df["close_location"].iloc[i])
    range_atr = float(df["range_atr"].iloc[i])
    activity = float(df["activity_ratio"].iloc[i])
    atr_expansion = float(df["atr_expansion_20"].iloc[i])
    wick_atr = float(df["lower_wick_atr"].iloc[i]) if direction == "long" else float(df["upper_wick_atr"].iloc[i])

    directional_close = close_loc >= 0.60 if direction == "long" else close_loc <= 0.40
    if spec.quality == "body_close":
        return body >= 0.35 and directional_close

    if spec.quality == "wick_activity":
        return body >= 0.35 and directional_close and wick_atr >= 0.20 and range_atr >= 0.70 and activity >= 1.05

    if spec.quality == "strict":
        strict_close = close_loc >= 0.65 if direction == "long" else close_loc <= 0.35
        return (
            body >= 0.45
            and strict_close
            and wick_atr >= 0.25
            and range_atr >= 0.85
            and activity >= 1.10
            and atr_expansion >= 0.95
        )

    raise ValueError(f"unknown quality: {spec.quality}")


def forward_reaction(df: pd.DataFrame, signal_i: int, direction: str, atr_i: float) -> dict:
    sign = 1.0 if direction == "long" else -1.0
    close_i = float(df["close"].iloc[signal_i])
    out: dict[str, float | bool] = {}
    for h in [4, 8, 16, 24, 36]:
        if signal_i + h < len(df):
            out[f"fwd_{h}_atr"] = sign * (float(df["close"].iloc[signal_i + h]) - close_i) / atr_i
        else:
            out[f"fwd_{h}_atr"] = math.nan
    for h in [8, 16, 24, 36]:
        end = min(len(df) - 1, signal_i + h)
        if end <= signal_i:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"mae_{h}_atr"] = math.nan
            out[f"hit_1atr_first_{h}"] = False
            continue
        window = df.iloc[signal_i + 1 : end + 1]
        if direction == "long":
            mfe = (float(window["high"].max()) - close_i) / atr_i
            mae = (close_i - float(window["low"].min())) / atr_i
        else:
            mfe = (close_i - float(window["low"].min())) / atr_i
            mae = (float(window["high"].max()) - close_i) / atr_i
        out[f"mfe_{h}_atr"] = mfe
        out[f"mae_{h}_atr"] = mae

        hit_first = False
        decided = False
        for _, row in window.iterrows():
            if direction == "long":
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


def simulate_rr(
    df: pd.DataFrame,
    symbol: str,
    direction: str,
    signal_i: int,
    stop: float,
    rr: float,
    max_hold_bars: int,
    max_risk_atr: float,
) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    atr_i = float(df["atr"].iloc[signal_i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    entry = float(df["open"].iloc[entry_i])
    if direction == "long":
        risk = entry - stop
        target = entry + risk * rr
    else:
        risk = stop - entry
        target = entry - risk * rr
    if not math.isfinite(risk) or risk <= 0 or risk / atr_i > max_risk_atr:
        return None

    end_i = min(len(df) - 1, entry_i + max_hold_bars)
    exit_i = end_i
    exit_price = float(df["close"].iloc[end_i])
    reason = "max_hold"
    mfe_r = 0.0
    mae_r = 0.0

    for j in range(entry_i, end_i + 1):
        high = float(df["high"].iloc[j])
        low = float(df["low"].iloc[j])
        if direction == "long":
            mfe_r = max(mfe_r, (high - entry) / risk)
            mae_r = max(mae_r, (entry - low) / risk)
            hit_stop = low <= stop
            hit_target = high >= target
        else:
            mfe_r = max(mfe_r, (entry - low) / risk)
            mae_r = max(mae_r, (high - entry) / risk)
            hit_stop = high >= stop
            hit_target = low <= target
        if hit_stop or hit_target:
            exit_i = j
            exit_price = stop if hit_stop else target
            reason = "SL_first_same_bar" if hit_stop and hit_target else "SL" if hit_stop else "TP"
            break

    r_clean, r_after = direction_cost_r(symbol, direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "risk_atr": risk / atr_i,
        "r_clean": r_clean,
        "r_after_cost": r_after,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
    }


def base_event_fields(df: pd.DataFrame, i: int, direction: str, level: float, break_i: int, break_extreme: float) -> dict:
    atr_i = float(df["atr"].iloc[i])
    close = float(df["close"].iloc[i])
    if direction == "long":
        break_depth_atr = (level - break_extreme) / atr_i
        reclaim_atr = (close - level) / atr_i
    else:
        break_depth_atr = (break_extreme - level) / atr_i
        reclaim_atr = (level - close) / atr_i
    return {
        "trap_level": level,
        "break_time": df.index[break_i],
        "break_extreme": break_extreme,
        "fail_bars": i - break_i,
        "break_depth_atr": break_depth_atr,
        "reclaim_atr": reclaim_atr,
        "body_ratio": float(df["body_ratio"].iloc[i]),
        "close_location": float(df["close_location"].iloc[i]),
        "range_atr": float(df["range_atr"].iloc[i]),
        "activity_ratio": float(df["activity_ratio"].iloc[i]),
        "atr_expansion_20": float(df["atr_expansion_20"].iloc[i]),
        "lower_wick_atr": float(df["lower_wick_atr"].iloc[i]),
        "upper_wick_atr": float(df["upper_wick_atr"].iloc[i]),
        "ema50_slope_20_atr": float(df["ema50_slope_20_atr"].iloc[i]),
        "range60_atr": float(df["range60_atr"].iloc[i]),
    }


def run_spec(df: pd.DataFrame, symbol: str, timeframe: str, spec: TrapSpec) -> pd.DataFrame:
    rows: list[dict] = []
    in_pos_until = -1
    pending_low_break: dict | None = None
    pending_high_break: dict | None = None
    low_col = f"donchian{spec.lookback}_low"
    high_col = f"donchian{spec.lookback}_high"

    for i in range(spec.lookback + 30, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue

        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        low_level = float(df[low_col].iloc[i])
        high_level = float(df[high_col].iloc[i])
        if not math.isfinite(low_level) or not math.isfinite(high_level):
            continue

        close = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])
        low = float(df["low"].iloc[i])

        event: dict | None = None
        direction: str | None = None
        stop: float | None = None

        if spec.trap_kind == "wick":
            broke_low = low < low_level - atr_i * spec.break_buffer_atr
            reclaimed_low = close > low_level + atr_i * spec.reclaim_buffer_atr
            broke_high = high > high_level + atr_i * spec.break_buffer_atr
            reclaimed_high = close < high_level - atr_i * spec.reclaim_buffer_atr

            if broke_low and reclaimed_low:
                direction = "long"
                if quality_ok(df, i, direction, spec):
                    event = base_event_fields(df, i, direction, low_level, i, low)
                    stop = low - atr_i * spec.stop_buffer_atr
            elif broke_high and reclaimed_high:
                direction = "short"
                if quality_ok(df, i, direction, spec):
                    event = base_event_fields(df, i, direction, high_level, i, high)
                    stop = high + atr_i * spec.stop_buffer_atr

        elif spec.trap_kind == "close_fail":
            if pending_low_break is not None and i - int(pending_low_break["i"]) > spec.fail_window:
                pending_low_break = None
            if pending_high_break is not None and i - int(pending_high_break["i"]) > spec.fail_window:
                pending_high_break = None

            if pending_low_break is not None and i > int(pending_low_break["i"]):
                level = float(pending_low_break["level"])
                if close > level + atr_i * spec.reclaim_buffer_atr:
                    direction = "long"
                    if quality_ok(df, i, direction, spec):
                        b_i = int(pending_low_break["i"])
                        extreme = float(df["low"].iloc[b_i : i + 1].min())
                        event = base_event_fields(df, i, direction, level, b_i, extreme)
                        stop = extreme - atr_i * spec.stop_buffer_atr
                    pending_low_break = None

            if event is None and pending_high_break is not None and i > int(pending_high_break["i"]):
                level = float(pending_high_break["level"])
                if close < level - atr_i * spec.reclaim_buffer_atr:
                    direction = "short"
                    if quality_ok(df, i, direction, spec):
                        b_i = int(pending_high_break["i"])
                        extreme = float(df["high"].iloc[b_i : i + 1].max())
                        event = base_event_fields(df, i, direction, level, b_i, extreme)
                        stop = extreme + atr_i * spec.stop_buffer_atr
                    pending_high_break = None

            if close < low_level - atr_i * spec.break_buffer_atr:
                pending_low_break = {"i": i, "level": low_level}
            if close > high_level + atr_i * spec.break_buffer_atr:
                pending_high_break = {"i": i, "level": high_level}

        else:
            raise ValueError(f"unknown trap_kind: {spec.trap_kind}")

        if event is None or direction is None or stop is None:
            continue
        if i <= in_pos_until:
            continue

        trade = simulate_rr(
            df=df,
            symbol=symbol,
            direction=direction,
            signal_i=i,
            stop=stop,
            rr=spec.rr,
            max_hold_bars=MAX_HOLD[timeframe],
            max_risk_atr=spec.max_risk_atr,
        )
        if trade is None:
            continue

        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": spec.name,
                "trap_kind": spec.trap_kind,
                "lookback": spec.lookback,
                "quality": spec.quality,
                "rr": spec.rr,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                "month": pd.Timestamp(trade["entry_time"]).strftime("%Y-%m"),
                "direction": direction,
                **event,
                **forward_reaction(df, i, direction, atr_i),
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def summarize_with_reaction(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    base = summarize(events, group_cols)
    rows = []
    for key, group in events.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple))
        for col in [
            "break_depth_atr",
            "reclaim_atr",
            "range_atr",
            "activity_ratio",
            "mfe_16_atr",
            "mae_16_atr",
            "mfe_r",
            "mae_r",
        ]:
            row[f"avg_{col}"] = float(group[col].mean())
        row["hit_1atr_first_16"] = float(group["hit_1atr_first_16"].mean() * 100)
        rows.append(row)
    reaction = pd.DataFrame(rows)
    return base.merge(reaction, on=group_cols, how="left").sort_values(
        ["total_r_after_cost", "pf_after_cost"], ascending=[False, False]
    )


def write_report(
    events: pd.DataFrame,
    overall: pd.DataFrame,
    h4_overall: pd.DataFrame,
    practical: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_period: pd.DataFrame,
    by_direction: pd.DataFrame,
) -> None:
    lines = [
        "# Trap / False Break Reaction Study",
        "",
        "作成日: 2026-05-30",
        "",
        "## 目的",
        "",
        "Market Psychology Pattern Library の `Trap` を数値化する。高値/安値更新に飛び乗った参加者が、短時間で否定されたあとに逆方向へ走りやすいかを検証する。",
        "",
        "## 定義",
        "",
        "- `wick`: prior Donchian 高値/安値をヒゲで更新し、同じ足の終値で内側へ戻る。",
        "- `close_fail`: prior Donchian 高値/安値を終値で更新し、6-8本以内に終値で内側へ戻る。",
        "- Entry: 否定成立足の次足始値。",
        "- SL: Trap極値 ± 0.25ATR。",
        "- TP: 1.5R。",
        "- 最大保有: H4は36本、D1は20本。",
        "- volume列がないため、出来高増加は True Range / 直近30本TR平均 の活動量代理で見る。",
        "",
        "## 重要メモ",
        "",
        "この検証は、単純なPF最大化ではなく、Trapが単独エントリーに耐えるのか、またはV/棚/節目ブレイクの環境認識として使うべきかを見るための一次検証。",
        "",
        "## 全体上位",
        "",
        markdown_table(overall, 40),
        "",
        "## H4上位",
        "",
        markdown_table(h4_overall, 40),
        "",
        "## 実戦候補フィルタ",
        "",
        "条件: 20 trades以上、Total R > 0、PF > 1.25。",
        "",
        markdown_table(practical, 40),
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
        "## 初期解釈",
        "",
    ]
    if practical.empty:
        lines.extend(
            [
                "現時点で、単独売買として強く採用できるTrap条件は限定的。Trapはエントリーそのものより、V字回復・棚ブレイク・Dormant Breakoutの文脈フィルターとして使う方が自然。",
            ]
        )
    else:
        top = practical.iloc[0]
        lines.extend(
            [
                f"最初に見るべき候補は `{top['strategy']}`。ただし、通貨別/期間別に偏りがないかを次に確認する必要がある。",
            ]
        )
    lines.extend(
        [
            "",
            "## 出力",
            "",
            "- `events.csv`",
            "- `summary_overall.csv`",
            "- `summary_h4_overall.csv`",
            "- `summary_practical.csv`",
            "- `summary_by_symbol.csv`",
            "- `summary_by_period.csv`",
            "- `summary_by_direction.csv`",
            "- `data_coverage.csv`",
        ]
    )
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
            df = add_trap_indicators(resample_ohlc(raw, timeframe))
            for spec in SPECS:
                events = run_spec(df, symbol, timeframe, spec)
                if not events.empty:
                    all_events.append(events)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if not all_events:
        (OUT_DIR / "report_ja.md").write_text("# Trap / False Break Reaction Study\n\nNo events.", encoding="utf-8")
        print(f"No events. Report: {OUT_DIR / 'report_ja.md'}")
        return

    events_df = pd.concat(all_events, ignore_index=True)
    for col in ["signal_time", "break_time", "entry_time", "exit_time"]:
        events_df[col] = pd.to_datetime(events_df[col])
    events_df = events_df.sort_values(["timeframe", "strategy", "entry_time", "symbol"]).reset_index(drop=True)
    events_df.to_csv(OUT_DIR / "events.csv", index=False)

    overall = summarize_with_reaction(events_df, ["timeframe", "trap_kind", "strategy"])
    h4_overall = overall[overall["timeframe"] == "H4"].copy()
    practical = overall[
        (overall["trades"] >= 20)
        & (overall["total_r_after_cost"] > 0)
        & (overall["pf_after_cost"] > 1.25)
    ].copy()
    by_symbol = summarize_with_reaction(events_df, ["timeframe", "strategy", "symbol"])
    by_period = summarize_with_reaction(events_df, ["timeframe", "strategy", "period"])
    by_direction = summarize_with_reaction(events_df, ["timeframe", "strategy", "direction"])

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    h4_overall.to_csv(OUT_DIR / "summary_h4_overall.csv", index=False)
    practical.to_csv(OUT_DIR / "summary_practical.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    by_direction.to_csv(OUT_DIR / "summary_by_direction.csv", index=False)

    write_report(events_df, overall, h4_overall, practical, by_symbol, by_period, by_direction)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(h4_overall.head(30).to_string(index=False))
    if not practical.empty:
        print("\nPractical candidates:")
        print(practical.head(20).to_string(index=False))


if __name__ == "__main__":
    main()

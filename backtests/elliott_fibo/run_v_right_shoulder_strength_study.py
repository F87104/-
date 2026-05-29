#!/usr/bin/env python3
"""
Study: V recovery where the right shoulder is stronger than the left shoulder.

User hypothesis:
- The recovery leg should be steeper than the drop leg.
- The right shoulder should reclaim the V left-shoulder starting point.

This script tests that idea as a standalone long entry, using the same pivot,
next-bar-open execution, cost table, and SL/TP simulation used by the existing
Elliott/V studies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    Pivot,
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    simulate_trade,
    summarize,
    timeframe_settings,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_29" / "v_right_shoulder_strength"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RUN_TIMEFRAMES = ["H4", "D1"]


@dataclass(frozen=True)
class RightShoulderSpec:
    name: str
    note: str
    rr: float = 2.0
    min_drop_atr: float = 3.2
    min_drop_speed: float = 0.25
    min_speed_ratio: float = 1.0
    body_min: float = 0.0
    close_location_min: float = 0.0
    min_drop_bars: int = 2
    max_drop_bars: int = 30
    max_recovery_bars: int = 30
    cross_buffer_atr: float = 0.05
    stop_buffer_atr: float = 0.25
    require_up_regime: bool = False
    max_ema_stretch_atr: float | None = None


SPECS: list[RightShoulderSpec] = [
    RightShoulderSpec(
        "RS100_RECLAIM_RR1",
        "右肩速度 >= 左肩速度、終値が左肩起点を上抜け、RR1.0",
        rr=1.0,
    ),
    RightShoulderSpec(
        "RS100_RECLAIM_RR15",
        "右肩速度 >= 左肩速度、終値が左肩起点を上抜け、RR1.5",
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS100_RECLAIM_RR2",
        "右肩速度 >= 左肩速度、終値が左肩起点を上抜け、RR2.0",
        rr=2.0,
    ),
    RightShoulderSpec(
        "RS120_RECLAIM_RR1",
        "右肩速度 >= 左肩速度x1.2、終値が左肩起点を上抜け、RR1.0",
        min_speed_ratio=1.2,
        rr=1.0,
    ),
    RightShoulderSpec(
        "RS120_RECLAIM_RR15",
        "右肩速度 >= 左肩速度x1.2、終値が左肩起点を上抜け、RR1.5",
        min_speed_ratio=1.2,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS120_RECLAIM_RR2",
        "右肩速度 >= 左肩速度x1.2、終値が左肩起点を上抜け、RR2.0",
        min_speed_ratio=1.2,
        rr=2.0,
    ),
    RightShoulderSpec(
        "RS100_BODY45_CLOSE60_RR15",
        "RS100に実体45%以上、終値位置60%以上を追加、RR1.5",
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS120_BODY45_CLOSE60_RR15",
        "RS120に実体45%以上、終値位置60%以上を追加、RR1.5",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS120_BODY45_CLOSE60_RR2",
        "RS120に実体45%以上、終値位置60%以上を追加、RR2.0",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=2.0,
    ),
    RightShoulderSpec(
        "RS120_UPREG_BODY45_CLOSE60_RR15",
        "RS120 + H4/D1上向きEMA環境 + 実体45%以上、RR1.5",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
        require_up_regime=True,
    ),
    RightShoulderSpec(
        "RS120_UPREG_BODY45_CLOSE60_STRETCH35_RR15",
        "RS120 + 上向きEMA環境 + EMA乖離3.5ATR以内、RR1.5",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
        require_up_regime=True,
        max_ema_stretch_atr=3.5,
    ),
    RightShoulderSpec(
        "RS150_UPREG_BODY45_CLOSE60_STRETCH35_RR15",
        "右肩速度 >= 左肩速度x1.5 + 上向きEMA環境 + 乖離3.5ATR以内、RR1.5",
        min_speed_ratio=1.5,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
        require_up_regime=True,
        max_ema_stretch_atr=3.5,
    ),
]


def add_regime_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["ema50_slope_20"] = out["ema50"] - out["ema50"].shift(20)
    rng = (out["high"] - out["low"]).replace(0, float("nan"))
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.0)
    return out


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "Research_2015_2024"
    return "OOS_2025_2026"


def up_regime_ok(df: pd.DataFrame, i: int, spec: RightShoulderSpec, atr_i: float) -> bool:
    if not spec.require_up_regime and spec.max_ema_stretch_atr is None:
        return True
    close = float(df["close"].iloc[i])
    ema50 = float(df["ema50"].iloc[i])
    ema200 = float(df["ema200"].iloc[i])
    slope = float(df["ema50_slope_20"].iloc[i])
    if spec.require_up_regime:
        if not (math.isfinite(ema50) and math.isfinite(ema200) and close > ema50 and ema50 > ema200 and slope > 0):
            return False
    if spec.max_ema_stretch_atr is not None:
        stretch = abs(close - ema50) / atr_i
        if stretch > spec.max_ema_stretch_atr:
            return False
    return True


def right_shoulder_signal(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: RightShoulderSpec,
    settings: dict,
    used_pairs: set[str],
) -> dict | None:
    if len(active) < 2:
        return None

    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None
    if float(df["close_location"].iloc[i]) < spec.close_location_min:
        return None
    if not up_regime_ok(df, i, spec, atr_i):
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    buffer = atr_i * spec.cross_buffer_atr

    # Use recent confirmed High->Low V pairs only. This keeps the study close
    # to a live Pine scanner and avoids reusing stale V structures.
    pairs_scanned = 0
    idx = len(active) - 2
    while idx >= 0 and pairs_scanned < 12:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        pairs_scanned += 1
        if p0.kind != "H" or p1.kind != "L":
            continue

        pair_key = f"{p0.pivot_i}-{p1.pivot_i}"
        if pair_key in used_pairs:
            continue

        drop = p0.price - p1.price
        if drop <= 0:
            continue

        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        recovery_bars = max(i - p1.pivot_i, 1)
        if drop_bars < spec.min_drop_bars or drop_bars > spec.max_drop_bars:
            continue
        if recovery_bars > spec.max_recovery_bars:
            continue
        if drop < atr_i * spec.min_drop_atr:
            continue

        # A fresh lower low after the V bottom means the V was not actually
        # accepted by the market yet.
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue

        trigger = p0.price
        crossed_start = prev_close <= trigger + buffer and close > trigger + buffer
        if not crossed_start:
            continue

        recovery = close - p1.price
        drop_speed = drop / drop_bars / atr_i
        recovery_speed = recovery / recovery_bars / atr_i
        speed_ratio = recovery_speed / drop_speed if drop_speed > 0 else math.nan
        if drop_speed < spec.min_drop_speed:
            continue
        if not math.isfinite(speed_ratio) or speed_ratio < spec.min_speed_ratio:
            continue

        stop = p1.price - atr_i * spec.stop_buffer_atr
        target = close + (close - stop) * spec.rr
        if stop >= close or target <= close:
            continue

        return {
            "direction": "long",
            "pair_key": pair_key,
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "trigger_level": trigger,
            "v_move_atr": drop / atr_i,
            "v_move_bars": drop_bars,
            "v_recovery_bars": recovery_bars,
            "drop_speed_atr_per_bar": drop_speed,
            "recovery_speed_atr_per_bar": recovery_speed,
            "right_left_speed_ratio": speed_ratio,
            "fib_ratio_at_signal": recovery / drop,
            "close_location": float(df["close_location"].iloc[i]),
            "body_ratio": float(df["body_ratio"].iloc[i]),
            "ema50_stretch_atr": abs(close - float(df["ema50"].iloc[i])) / atr_i,
            "stop": stop,
            "target": target,
        }

    return None


def run_spec(df: pd.DataFrame, symbol: str, timeframe: str, spec: RightShoulderSpec) -> pd.DataFrame:
    settings = timeframe_settings(timeframe)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    used_pairs: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        sig = right_shoulder_signal(df, i, active, spec, settings, used_pairs)
        if sig is None:
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction="long",
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
        )
        if trade is None:
            continue

        used_pairs.add(str(sig["pair_key"]))
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": spec.name,
                "note": spec.note,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                **{k: v for k, v in sig.items() if k not in {"direction", "stop", "target"}},
                **trade,
            }
        )
        exit_pos = df.index.get_loc(trade["exit_time"])
        in_pos_until = int(exit_pos)

    return pd.DataFrame(rows)


def write_report(
    trades: pd.DataFrame,
    overall: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_period: pd.DataFrame,
    h4_top: pd.DataFrame,
    practical_ex_xau: pd.DataFrame,
    practical_ex_xau_period: pd.DataFrame,
) -> None:
    lines = [
        "# V右肩優位・左肩起点超え 検証 2026-05-29",
        "",
        "## 検証した仮説",
        "",
        "- ロングのみ。",
        "- confirmed pivot high から confirmed pivot low への急落を左肩とする。",
        "- 右肩は、その安値からの回復。",
        "- 右肩の角度 = 回復速度 ATR/本。",
        "- 左肩の角度 = 下落速度 ATR/本。",
        "- 条件: 右肩速度が左肩速度以上、または1.2倍/1.5倍以上。",
        "- 条件: 右肩の終値が左肩の起点、つまり急落前pivot highをATR余白付きで上抜ける。",
        "- Entryはシグナル次足始値、SLはV安値 - 0.25ATR、TPは固定RR。",
        "- 2015-2024をResearch、2025-2026をOOSとして分けた。",
        "",
        "## 全体結果 上位",
        "",
        markdown_table(overall, 40),
        "",
        "## H4上位",
        "",
        markdown_table(h4_top, 40),
        "",
        "## 実戦候補: H4 RS120 BODY45 CLOSE60 RR1.5 / XAUUSD除外",
        "",
        markdown_table(practical_ex_xau, 10),
        "",
        "## 実戦候補 期間別",
        "",
        markdown_table(practical_ex_xau_period, 10),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 80),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 100),
        "",
        "## 出力",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_h4_top.csv`",
        "- `summary_practical_ex_xau.csv`",
        "- `summary_practical_ex_xau_by_period.csv`",
        "- `summary_by_period.csv`",
        "- `summary_by_symbol.csv`",
        "- `data_coverage.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_trades: list[pd.DataFrame] = []
    coverage_rows: list[dict] = []

    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        coverage_rows.append(
            {
                "symbol": symbol,
                "rows_h1": len(raw),
                "first": raw.index.min(),
                "last": raw.index.max(),
            }
        )
        for timeframe in RUN_TIMEFRAMES:
            df = add_regime_indicators(resample_ohlc(raw, timeframe))
            for spec in SPECS:
                trades = run_spec(df, symbol, timeframe, spec)
                if not trades.empty:
                    all_trades.append(trades)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if not all_trades:
        (OUT_DIR / "report_ja.md").write_text("# V右肩優位・左肩起点超え 検証\n\nNo trades.", encoding="utf-8")
        print(f"No trades. Report: {OUT_DIR / 'report_ja.md'}")
        return

    trades_df = pd.concat(all_trades, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades_df[col] = pd.to_datetime(trades_df[col])
    trades_df["year"] = trades_df["entry_time"].dt.year.astype(str)
    trades_df = trades_df.sort_values(["timeframe", "strategy", "entry_time", "symbol"]).reset_index(drop=True)
    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades_df, ["timeframe", "strategy"])
    by_symbol = summarize(trades_df, ["timeframe", "strategy", "symbol"])
    by_period = summarize(trades_df, ["timeframe", "strategy", "period"])
    h4_top = overall[overall["timeframe"] == "H4"].copy()
    practical = trades_df[
        (trades_df["timeframe"] == "H4")
        & (trades_df["strategy"] == "RS120_BODY45_CLOSE60_RR15")
        & (trades_df["symbol"] != "XAUUSD")
    ].copy()
    practical_ex_xau = summarize(practical, ["timeframe", "strategy"])
    practical_ex_xau_period = summarize(practical, ["period"])

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    h4_top.to_csv(OUT_DIR / "summary_h4_top.csv", index=False)
    practical_ex_xau.to_csv(OUT_DIR / "summary_practical_ex_xau.csv", index=False)
    practical_ex_xau_period.to_csv(OUT_DIR / "summary_practical_ex_xau_by_period.csv", index=False)

    write_report(trades_df, overall, by_symbol, by_period, h4_top, practical_ex_xau, practical_ex_xau_period)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(h4_top.head(30).to_string(index=False))


if __name__ == "__main__":
    main()

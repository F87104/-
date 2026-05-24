#!/usr/bin/env python3
"""
Study: sharp-drop V recovery as context, then enter only after a trigger.

Definition tested here:
- Context: a confirmed pivot High -> pivot Low sharp drop.
- Candidate: close recovers 61.8% to 80.0% of the drop.
- Entry trigger after the candidate:
  1) high stagnation breakout: several tight bars near the recovered zone,
     followed by a close above that small range.
  2) re-break: price makes a recovery high, pulls back, then closes above
     that recovery high again.

This keeps the V shape as a setup/context instead of entering immediately at
the Fibonacci recovery level.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    END,
    START,
    SYMBOLS,
    TIMEFRAMES,
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
OUT_DIR = THIS_DIR / "results_2015_2024" / "v_recovery_trigger"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# The H1 pass is much heavier because every bar must inspect V context and
# follow-up triggers. Start with the practical higher-timeframe study requested
# for this setup; H1 can be run later with a narrower symbol/spec set.
RUN_TIMEFRAMES = ["H4", "D1"]


@dataclass(frozen=True)
class TriggerSpec:
    name: str
    fib_min: float = 0.618
    fib_max: float = 0.800
    rr: float = 2.0
    body_min: float = 0.60
    min_move_atr: float = 3.5
    min_drop_speed: float = 0.30
    max_recovery_to_drop: float = 1.5
    trigger_mode: str = "either"  # stagnation / rebreak / either
    stag_range_atr: float = 1.0
    pullback_atr: float = 0.75
    max_bars_after_candidate: int | None = None


SPECS = [
    TriggerSpec("VCTX_618_800_STAG_OR_REBREAK_RR2"),
    TriggerSpec("VCTX_618_800_STAG_ONLY_RR2", trigger_mode="stagnation"),
    TriggerSpec("VCTX_618_800_REBREAK_ONLY_RR2", trigger_mode="rebreak"),
    TriggerSpec("VCTX_618_786_STAG_OR_REBREAK_RR2", fib_max=0.786),
    TriggerSpec("VCTX_618_800_FAST_STAG_OR_REBREAK_RR2", min_drop_speed=0.60),
    TriggerSpec("VCTX_618_800_BIGDROP_STAG_OR_REBREAK_RR2", min_move_atr=4.0),
    TriggerSpec("VCTX_618_800_FAST_BIGDROP_STAG_OR_REBREAK_RR2", min_move_atr=4.0, min_drop_speed=0.60),
    TriggerSpec("VCTX_618_800_REC1_STAG_OR_REBREAK_RR2", max_recovery_to_drop=1.0),
]


def trigger_settings(timeframe: str) -> dict:
    if timeframe == "H1":
        return dict(stag_bars=7, min_wait_bars=2, max_after=48)
    if timeframe == "H4":
        return dict(stag_bars=3, min_wait_bars=1, max_after=24)
    return dict(stag_bars=2, min_wait_bars=1, max_after=12)


def _candidate_first_index(
    df: pd.DataFrame,
    start_i: int,
    end_i: int,
    low_price: float,
    drop: float,
    fib_min: float,
    fib_max: float,
) -> int | None:
    if end_i < start_i:
        return None
    closes = df["close"].to_numpy()
    for idx in range(start_i, end_i + 1):
        ratio = (float(closes[idx]) - low_price) / drop
        if fib_min <= ratio <= fib_max:
            return idx
        # If the market jumps straight past the candidate zone, it is not the
        # "61.8-80% candidate, then trigger" structure we want to test.
        if ratio > fib_max:
            return None
    return None


def v_context_trigger_signal(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: TriggerSpec,
    settings: dict,
) -> dict | None:
    if len(active) < 2:
        return None

    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None

    tf_trig = trigger_settings(settings["timeframe"])
    stag_bars = int(tf_trig["stag_bars"])
    min_wait_bars = int(tf_trig["min_wait_bars"])
    max_after = spec.max_bars_after_candidate or int(tf_trig["max_after"])
    buffer = atr_i * settings["break_buffer_atr"]

    # Scan only recent confirmed H-L pivot pairs. Looking through the full
    # pivot history on every bar is slow and also not useful for a live scanner:
    # old V structures should have expired by the time a fresh setup appears.
    pairs_scanned = 0
    idx = len(active) - 2
    while idx >= 0 and pairs_scanned < 10:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        pairs_scanned += 1
        if p0.kind != "H" or p1.kind != "L":
            continue
        if i <= p1.pivot_i + min_wait_bars:
            continue

        drop = p0.price - p1.price
        if drop <= 0 or drop < atr_i * spec.min_move_atr:
            continue

        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        drop_speed = drop / drop_bars / atr_i
        if drop_speed < spec.min_drop_speed:
            continue

        # If a lower low was made after the V extreme, invalidate this setup.
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue

        candidate_i = _candidate_first_index(
            df,
            p1.pivot_i + 1,
            i - min_wait_bars,
            p1.price,
            drop,
            spec.fib_min,
            spec.fib_max,
        )
        if candidate_i is None:
            continue

        if i - candidate_i > max_after:
            continue

        recovery_bars = max(candidate_i - p1.pivot_i, 1)
        recovery_to_drop = recovery_bars / drop_bars
        if recovery_to_drop > spec.max_recovery_to_drop:
            continue

        fib_min_level = p1.price + drop * spec.fib_min
        stop = p1.price - atr_i * 0.25
        target = close + (close - stop) * spec.rr
        if target <= close or stop >= close:
            continue

        # Trigger 1: high stagnation breakout after the candidate.
        stagnation_ok = False
        if i - candidate_i >= stag_bars + 1:
            win = df.iloc[i - stag_bars : i]
            win_high = float(win["high"].max())
            win_low = float(win["low"].min())
            win_range = win_high - win_low
            held_zone = win_low >= fib_min_level - atr_i * 0.50
            tight_enough = win_range <= atr_i * spec.stag_range_atr
            broke_tight_high = close > win_high + buffer
            stagnation_ok = held_zone and tight_enough and broke_tight_high

        # Trigger 2: recovery high re-break after one pullback.
        rebreak_ok = False
        pre = df.iloc[candidate_i:i]
        if len(pre) >= 3:
            highs = pre["high"].to_numpy(dtype=float)
            high_pos = int(np.nanargmax(highs))
            high_i = candidate_i + high_pos
            recovery_high = float(highs[high_pos])
            if high_i <= i - 2:
                pullback_low = float(df["low"].iloc[high_i + 1 : i].min())
                had_pullback = pullback_low <= recovery_high - atr_i * spec.pullback_atr
                rebreak_ok = had_pullback and close > recovery_high + buffer

        if spec.trigger_mode == "stagnation" and not stagnation_ok:
            continue
        if spec.trigger_mode == "rebreak" and not rebreak_ok:
            continue
        if spec.trigger_mode == "either" and not (stagnation_ok or rebreak_ok):
            continue

        trigger_type = "stagnation" if stagnation_ok else "rebreak"
        if stagnation_ok and rebreak_ok:
            trigger_type = "stagnation+rebreak"

        recovery_at_signal = close - p1.price
        return {
            "direction": "long",
            "trigger_type": trigger_type,
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "candidate_i": candidate_i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "v_move_atr": drop / atr_i,
            "v_move_bars": drop_bars,
            "v_drop_speed_atr_per_bar": drop_speed,
            "candidate_recovery_bars": recovery_bars,
            "candidate_recovery_to_drop_bars": recovery_to_drop,
            "signal_recovery_bars": i - p1.pivot_i,
            "signal_fib_ratio": recovery_at_signal / drop,
            "candidate_fib_min": spec.fib_min,
            "candidate_fib_max": spec.fib_max,
            "trigger_level": close,
            "stop": stop,
            "target": target,
            "candidate_key": f"{p0.pivot_i}-{p1.pivot_i}",
        }

    return None


def run_spec(df: pd.DataFrame, symbol: str, timeframe: str, spec: TriggerSpec) -> pd.DataFrame:
    settings = timeframe_settings(timeframe)
    settings["timeframe"] = timeframe
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    used_candidates: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < START or ts > END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        sig = v_context_trigger_signal(df, i, active, spec, settings)
        if sig is None:
            continue
        if sig["candidate_key"] in used_candidates:
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=sig["direction"],
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
            invalidation_level=None,
            early_exit_bars=0,
        )
        if trade is None:
            continue

        used_candidates.add(sig["candidate_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": spec.name,
                "family": "V候補後トリガー",
                "signal_time": ts,
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "candidate_key"}},
                **trade,
            }
        )
        exit_pos = df.index.get_loc(trade["exit_time"])
        in_pos_until = int(exit_pos)

    return pd.DataFrame(rows)


def write_report(trades: pd.DataFrame) -> None:
    if trades.empty:
        (OUT_DIR / "report_ja.md").write_text("# V候補後トリガー検証\n\nNo trades.", encoding="utf-8")
        return

    overall = summarize(trades, ["timeframe", "strategy"])
    by_symbol = summarize(trades, ["timeframe", "strategy", "symbol"])
    by_trigger = summarize(trades, ["timeframe", "strategy", "trigger_type"])
    by_year = summarize(trades, ["timeframe", "strategy", "year"])

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "summary_by_trigger.csv", index=False)
    by_year.to_csv(OUT_DIR / "summary_by_year.csv", index=False)

    h4 = overall[overall["timeframe"] == "H4"].copy()
    h4_symbol = by_symbol[by_symbol["timeframe"] == "H4"].copy()
    h4_trigger = by_trigger[by_trigger["timeframe"] == "H4"].copy()

    lines = [
        "# V候補後トリガー検証 2015-2024",
        "",
        "## 検証した考え方",
        "",
        "- 急落後V字を即エントリー条件にせず、まず候補として扱う。",
        "- 候補: 確定スイング高値から安値への急落後、終値が下落幅の61.8%〜80.0%まで戻す。",
        "- エントリー: 候補発生後に、狭い高値停滞を上抜ける、または一度押してから戻り高値を再ブレイクする。",
        "- 買いのみ。売りの逆V字は今回含めていません。",
        "- エントリーはシグナル次足の始値、コスト込みRで集計。",
        "",
        "## 全体結果",
        "",
        markdown_table(overall, 80),
        "",
        "## H4結果",
        "",
        markdown_table(h4, 80),
        "",
        "## H4 通貨別",
        "",
        markdown_table(h4_symbol, 120),
        "",
        "## H4 トリガー別",
        "",
        markdown_table(h4_trigger, 80),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_trigger.csv`",
        "- `summary_by_year.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_rows = []
    coverage_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        for timeframe in RUN_TIMEFRAMES:
            df = add_indicators(resample_ohlc(raw, timeframe))
            for spec in SPECS:
                trades = run_spec(df, symbol, timeframe, spec)
                if not trades.empty:
                    all_rows.append(trades)

    if all_rows:
        trades = pd.concat(all_rows, ignore_index=True)
        trades["signal_time"] = pd.to_datetime(trades["signal_time"])
        trades["entry_time"] = pd.to_datetime(trades["entry_time"])
        trades["exit_time"] = pd.to_datetime(trades["exit_time"])
        trades["year"] = trades["entry_time"].dt.year.astype(str)
        trades = trades.sort_values(["timeframe", "strategy", "entry_time", "symbol"]).reset_index(drop=True)
    else:
        trades = pd.DataFrame()

    trades.to_csv(OUT_DIR / "trades.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)
    write_report(trades)

    if trades.empty:
        print("No trades")
        return
    overall = summarize(trades, ["timeframe", "strategy"])
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(overall.head(60).to_string(index=False))


if __name__ == "__main__":
    main()

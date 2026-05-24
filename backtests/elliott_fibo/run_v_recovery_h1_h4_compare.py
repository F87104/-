#!/usr/bin/env python3
"""
Focused H1 vs H4 comparison for the V-context trigger idea.

Compared patterns:
1. V candidate -> one pullback -> recovery high re-break.
2. V candidate -> high stagnation and re-break overlap.

The full trigger study intentionally starts with H4/D1 because H1 is heavier.
This script narrows the spec set so H1/H4 can be compared directly.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import (
    END,
    START,
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
from run_v_recovery_trigger_study import TriggerSpec, v_context_trigger_signal


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2015_2024" / "v_recovery_h1_h4_compare"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAMES = ["H1", "H4"]
SPECS = [
    TriggerSpec("VCTX_618_800_REBREAK_ONLY_RR2", trigger_mode="rebreak"),
    TriggerSpec("VCTX_618_800_FAST_REBREAK_ONLY_RR2", trigger_mode="rebreak", min_drop_speed=0.60),
    TriggerSpec("VCTX_618_800_STAG_OR_REBREAK_RR2", trigger_mode="either"),
    TriggerSpec("VCTX_618_800_FAST_STAG_OR_REBREAK_RR2", trigger_mode="either", min_drop_speed=0.60),
]


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
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def pf(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def summarize_subset(df: pd.DataFrame, label: str) -> dict:
    r = df["r_after_cost"]
    return {
        "pattern": label,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100) if len(df) else math.nan,
        "total_r_after_cost": float(r.sum()) if len(df) else 0.0,
        "avg_r_after_cost": float(r.mean()) if len(df) else math.nan,
        "pf_after_cost": pf(r) if len(df) else math.nan,
        "max_dd_r": float((r.cumsum().cummax() - r.cumsum()).max()) if len(df) else 0.0,
    }


def comparison_tables(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for (timeframe, strategy), group in trades.groupby(["timeframe", "strategy"], sort=True):
        rows.append({"timeframe": timeframe, "strategy": strategy, **summarize_subset(group, "all accepted")})
        overlap = group[group["trigger_type"].eq("stagnation+rebreak")]
        if not overlap.empty:
            rows.append({"timeframe": timeframe, "strategy": strategy, **summarize_subset(overlap, "stagnation+rebreak only")})
        rebreak = group[group["trigger_type"].isin(["rebreak", "stagnation+rebreak"])]
        if not rebreak.empty:
            rows.append({"timeframe": timeframe, "strategy": strategy, **summarize_subset(rebreak, "rebreak including overlap")})

    compare = pd.DataFrame(rows).sort_values(["pattern", "strategy", "timeframe"])

    base_rebreak = trades[trades["strategy"].eq("VCTX_618_800_REBREAK_ONLY_RR2")]
    by_symbol_rebreak = summarize(base_rebreak, ["timeframe", "strategy", "symbol"]) if not base_rebreak.empty else pd.DataFrame()

    base_overlap = trades[
        trades["strategy"].eq("VCTX_618_800_STAG_OR_REBREAK_RR2")
        & trades["trigger_type"].eq("stagnation+rebreak")
    ]
    by_symbol_overlap = summarize(base_overlap, ["timeframe", "strategy", "symbol"]) if not base_overlap.empty else pd.DataFrame()

    return compare, by_symbol_rebreak, by_symbol_overlap


def write_report(trades: pd.DataFrame) -> None:
    if trades.empty:
        (OUT_DIR / "report_ja.md").write_text("# H1 vs H4 V候補後トリガー比較\n\nNo trades.", encoding="utf-8")
        return

    compare, by_symbol_rebreak, by_symbol_overlap = comparison_tables(trades)
    compare.to_csv(OUT_DIR / "compare_patterns.csv", index=False)
    by_symbol_rebreak.to_csv(OUT_DIR / "rebreak_by_symbol.csv", index=False)
    by_symbol_overlap.to_csv(OUT_DIR / "stagnation_rebreak_overlap_by_symbol.csv", index=False)

    lines = [
        "# H1 vs H4 V候補後トリガー比較 2015-2024",
        "",
        "## 比較対象",
        "",
        "- 再ブレイク型: 61.8〜80%回復後、一度押してから戻り高値を再ブレイク。",
        "- 高値停滞+再ブレイク型: 高値停滞と再ブレイクが同時に重なるものだけ。",
        "- 買いのみ、コスト込みR、シグナル次足始値エントリー。",
        "",
        "## H1/H4 比較",
        "",
        markdown_table(compare, 80),
        "",
        "## 再ブレイク型 通貨別",
        "",
        markdown_table(by_symbol_rebreak, 80),
        "",
        "## 高値停滞+再ブレイク型 通貨別",
        "",
        markdown_table(by_symbol_overlap, 80),
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        for timeframe in TIMEFRAMES:
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
    write_report(trades)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if not trades.empty:
        compare, _, _ = comparison_tables(trades)
        print(compare.to_string(index=False))


if __name__ == "__main__":
    main()

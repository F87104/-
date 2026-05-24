#!/usr/bin/env python3
"""
Validate T5 + MACD + BB with two V-shape speed definitions.

This compares the original research setting (recovery bars / drop bars <= 1.5)
with the stricter discretionary definition (<= 1.0: recover within the same
number of bars as the drop).
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, markdown_table, resample_ohlc
from run_indicator_compatibility_search import add_extended_features, enrich_trades
from run_v_recovery_trigger_study import TriggerSpec, run_spec
import run_v_recovery_trigger_study as trigger_mod


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2015_2024" / "t5_macd_bb_vshape_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2024-12-31 23:59:59")

SPECS = [
    TriggerSpec("REC15_T5_STAG_OR_REBREAK", trigger_mode="either", max_recovery_to_drop=1.5),
    TriggerSpec("REC10_T5_STAG_OR_REBREAK", trigger_mode="either", max_recovery_to_drop=1.0),
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


def metrics(df: pd.DataFrame) -> dict[str, float | int]:
    r = df["r_after_cost"].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def candidate_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    macd = df["macd_hist_slope3"] > 0
    return {
        "Current_060_110": macd & df["bb_pos"].between(0.60, 1.10),
        "Robust_075_105_width7": macd & df["bb_pos"].between(0.75, 1.05) & (df["bb_width_atr"] <= 7.0),
        "Strict_075_100_width7": macd & df["bb_pos"].between(0.75, 1.00) & (df["bb_width_atr"] <= 7.0),
    }


def summarize_group(df: pd.DataFrame, group_col: str, spec_name: str, candidate: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for key, frame in df.groupby(group_col):
        rows.append({"spec": spec_name, "candidate": candidate, group_col: key, **metrics(frame)})
    return pd.DataFrame(rows)


def main() -> None:
    trigger_mod.START = START
    trigger_mod.END = END

    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    trade_frames: list[pd.DataFrame] = []

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        feature_frames[(symbol, TIMEFRAME)] = df
        for spec in SPECS:
            trades = run_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                trade_frames.append(trades)

    trades = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    if not trades.empty:
        enriched = enrich_trades(trades, feature_frames)
        for col in ["signal_time", "entry_time", "exit_time"]:
            enriched[col] = pd.to_datetime(enriched[col])
        enriched["year"] = enriched["entry_time"].dt.year
        enriched = enriched.sort_values(["strategy", "entry_time", "symbol"]).reset_index(drop=True)
    else:
        enriched = pd.DataFrame()

    enriched.to_csv(OUT_DIR / "trades_enriched.csv", index=False)

    summary_rows = []
    by_symbol_frames = []
    by_trigger_frames = []

    for spec_name, spec_group in enriched.groupby("strategy") if not enriched.empty else []:
        masks = candidate_masks(spec_group)
        for cand_name, mask in masks.items():
            sample = spec_group[mask.fillna(False)].copy().sort_values(["entry_time", "symbol"])
            summary_rows.append({"spec": spec_name, "candidate": cand_name, **metrics(sample)})
            by_symbol_frames.append(summarize_group(sample, "symbol", spec_name, cand_name))
            by_trigger_frames.append(summarize_group(sample, "trigger_type", spec_name, cand_name))

    summary = pd.DataFrame(summary_rows)
    by_symbol = pd.concat(by_symbol_frames, ignore_index=True) if by_symbol_frames else pd.DataFrame()
    by_trigger = pd.concat(by_trigger_frames, ignore_index=True) if by_trigger_frames else pd.DataFrame()

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "by_trigger.csv", index=False)

    lines = [
        "# T5 + MACD + BB V字速度定義 比較検証",
        "",
        "## 比較した定義",
        "",
        "- `REC15`: 回復本数 / 下落本数 <= 1.5。過去の探索に近い定義。",
        "- `REC10`: 回復本数 / 下落本数 <= 1.0。左肩と同じ本数以内で戻す、より厳格なV字定義。",
        "",
        "## サマリー",
        "",
        markdown_table(summary, 80) if not summary.empty else "No trades.",
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 120) if not by_symbol.empty else "No trades.",
        "",
        "## トリガー別",
        "",
        markdown_table(by_trigger, 80) if not by_trigger.empty else "No trades.",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary.to_string(index=False) if not summary.empty else "No trades")


if __name__ == "__main__":
    main()

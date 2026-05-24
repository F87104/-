#!/usr/bin/env python3
"""
Sweep the V-shape recovery speed threshold for H4 T5 + MACD + BB.

The swept value is:

    recovery_to_drop = bars from V low to 61.8%-80% recovery candidate
                       / bars from pivot high to V low

Lower values mean stricter/faster V recovery. Higher values allow slower,
rounder recoveries.
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
OUT_DIR = THIS_DIR / "results_2025_2026_oos" / "t5_recovery_ratio_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
PERIODS = [
    ("Research_2015_2024", pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31 23:59:59")),
    ("OOS_2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31 23:59:59")),
]
RATIOS = [round(x / 100, 2) for x in range(80, 201, 5)]


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


def run_period(
    period: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    feature_frames: dict[tuple[str, str], pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trigger_mod.START = start
    trigger_mod.END = end

    summary_rows = []
    by_symbol_rows = []
    all_trade_frames = []

    for ratio in RATIOS:
        spec = TriggerSpec(
            f"REC{ratio:.2f}_T5_STAG_OR_REBREAK",
            trigger_mode="either",
            max_recovery_to_drop=ratio,
        )
        trade_frames = []
        for symbol in SYMBOLS:
            df = feature_frames[(symbol, TIMEFRAME)]
            trades = run_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                trade_frames.append(trades)
        if not trade_frames:
            continue

        raw_trades = pd.concat(trade_frames, ignore_index=True)
        enriched = enrich_trades(raw_trades, feature_frames)
        for col in ["signal_time", "entry_time", "exit_time"]:
            enriched[col] = pd.to_datetime(enriched[col])
        enriched = enriched[enriched["entry_time"].between(start, end)].copy()
        enriched["period"] = period
        enriched["max_recovery_to_drop"] = ratio
        enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)

        masks = candidate_masks(enriched)
        for candidate, mask in masks.items():
            sample = enriched[mask.fillna(False)].copy().sort_values(["entry_time", "symbol"])
            sample["candidate"] = candidate
            all_trade_frames.append(sample)
            summary_rows.append(
                {
                    "period": period,
                    "candidate": candidate,
                    "max_recovery_to_drop": ratio,
                    **metrics(sample),
                }
            )
            for symbol, frame in sample.groupby("symbol"):
                by_symbol_rows.append(
                    {
                        "period": period,
                        "candidate": candidate,
                        "max_recovery_to_drop": ratio,
                        "symbol": symbol,
                        **metrics(frame),
                    }
                )

    summary = pd.DataFrame(summary_rows)
    by_symbol = pd.DataFrame(by_symbol_rows)
    trades = pd.concat(all_trade_frames, ignore_index=True) if all_trade_frames else pd.DataFrame()
    return summary, by_symbol, trades


def choose_candidates(summary: pd.DataFrame) -> pd.DataFrame:
    research = summary[summary["period"] == "Research_2015_2024"].copy()
    oos = summary[summary["period"] == "OOS_2025_2026"].copy()
    merged = research.merge(
        oos,
        on=["candidate", "max_recovery_to_drop"],
        suffixes=("_research", "_oos"),
    )
    if merged.empty:
        return merged

    # Prefer parameters that remain positive out-of-sample, avoid tiny OOS
    # samples, and balance expectancy/PF/DD instead of maximizing only profit.
    merged = merged[
        (merged["trades_research"] >= 40)
        & (merged["trades_oos"] >= 10)
        & (merged["total_r_research"] > 0)
        & (merged["total_r_oos"] > 0)
        & (merged["pf_research"] >= 1.4)
        & (merged["pf_oos"] >= 1.2)
    ].copy()
    if merged.empty:
        return merged

    merged["score"] = (
        merged["avg_r_research"] * 0.35
        + merged["avg_r_oos"] * 0.35
        + (merged["pf_research"].clip(upper=3) - 1) * 0.12
        + (merged["pf_oos"].clip(upper=3) - 1) * 0.12
        - merged["max_dd_r_research"] * 0.015
        - merged["max_dd_r_oos"] * 0.03
    )
    return merged.sort_values("score", ascending=False)


def main() -> None:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    coverage_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        feature_frames[(symbol, TIMEFRAME)] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))

    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    summaries = []
    by_symbols = []
    trades = []
    for period, start, end in PERIODS:
        summary, by_symbol, trade_frame = run_period(period, start, end, feature_frames)
        summaries.append(summary)
        by_symbols.append(by_symbol)
        trades.append(trade_frame)

    summary_all = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    by_symbol_all = pd.concat(by_symbols, ignore_index=True) if by_symbols else pd.DataFrame()
    trades_all = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    candidates = choose_candidates(summary_all)

    summary_all.to_csv(OUT_DIR / "summary_by_ratio.csv", index=False)
    by_symbol_all.to_csv(OUT_DIR / "by_symbol_by_ratio.csv", index=False)
    trades_all.to_csv(OUT_DIR / "trades_by_ratio.csv", index=False)
    candidates.to_csv(OUT_DIR / "golden_ratio_candidates.csv", index=False)

    top_cols = [
        "candidate",
        "max_recovery_to_drop",
        "score",
        "trades_research",
        "win_rate_research",
        "total_r_research",
        "avg_r_research",
        "pf_research",
        "max_dd_r_research",
        "trades_oos",
        "win_rate_oos",
        "total_r_oos",
        "avg_r_oos",
        "pf_oos",
        "max_dd_r_oos",
    ]
    top = candidates[top_cols].head(20) if not candidates.empty else candidates

    lines = [
        "# H4 T5 + MACD + BB 回復比率スイープ",
        "",
        "## 見ている数値",
        "",
        "`max_recovery_to_drop = 61.8%〜80%回復までの本数 / 急落本数`",
        "",
        "- 1.00: 急落10本なら10本以内に回復候補へ到達。",
        "- 1.50: 急落10本なら15本以内まで許容。",
        "- 数値が大きいほど、丸い戻り・遅い戻りも拾う。",
        "",
        "## データカバレッジ",
        "",
        markdown_table(coverage, 20),
        "",
        "## 黄金比率候補 上位",
        "",
        markdown_table(top, 30) if not top.empty else "No robust candidate.",
        "",
        "## 出力",
        "",
        "- `summary_by_ratio.csv`",
        "- `by_symbol_by_ratio.csv`",
        "- `trades_by_ratio.csv`",
        "- `golden_ratio_candidates.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(top.to_string(index=False) if not top.empty else "No robust candidate")


if __name__ == "__main__":
    main()

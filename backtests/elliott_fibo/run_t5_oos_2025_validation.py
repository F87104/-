#!/usr/bin/env python3
"""
Out-of-sample validation for the already-selected T5 + MACD + BB candidates.

The 2015-2024 period was used for research/selection.  This script freezes the
rules and evaluates only data from 2025 onward, while still allowing indicators
and confirmed pivots to warm up on pre-2025 history.
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
OUT_DIR = THIS_DIR / "results_2025_2026_oos" / "t5_macd_bb"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
OOS_START = pd.Timestamp("2025-01-01")
OOS_END = pd.Timestamp("2026-12-31 23:59:59")
SPEC = TriggerSpec("T5_STAG_OR_REBREAK", trigger_mode="either")


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
        "T5_base_no_indicator_filter": pd.Series(True, index=df.index),
        "Current_060_110": macd & df["bb_pos"].between(0.60, 1.10),
        "Robust_075_105_width7": macd & df["bb_pos"].between(0.75, 1.05) & (df["bb_width_atr"] <= 7.0),
        "Strict_075_100_width7": macd & df["bb_pos"].between(0.75, 1.00) & (df["bb_width_atr"] <= 7.0),
    }


def summarize_group(df: pd.DataFrame, group_col: str, candidate: str) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame()
    for key, frame in df.groupby(group_col):
        rows.append({"candidate": candidate, group_col: key, **metrics(frame)})
    return pd.DataFrame(rows)


def main() -> None:
    # Freeze OOS period.  run_spec still iterates over full history so pivots
    # and indicators have pre-2025 warm-up, but entries before OOS_START are skipped.
    trigger_mod.START = OOS_START
    trigger_mod.END = OOS_END

    coverage_rows = []
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    base_rows = []

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append(
            {
                "symbol": symbol,
                "rows_h1": len(raw),
                "first": raw.index.min(),
                "last": raw.index.max(),
                "has_2025_plus": raw.index.max() >= OOS_START,
            }
        )
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        feature_frames[(symbol, TIMEFRAME)] = df
        trades = run_spec(df, symbol, TIMEFRAME, SPEC)
        if not trades.empty:
            base_rows.append(trades)

    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if base_rows:
        base = pd.concat(base_rows, ignore_index=True)
        enriched = enrich_trades(base, feature_frames)
        for col in ["signal_time", "entry_time", "exit_time"]:
            enriched[col] = pd.to_datetime(enriched[col])
        enriched = enriched[enriched["entry_time"] >= OOS_START].copy()
        enriched["year"] = enriched["entry_time"].dt.year
        enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)
        enriched = enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    else:
        enriched = pd.DataFrame()

    enriched.to_csv(OUT_DIR / "trades_enriched_oos.csv", index=False)

    summary_rows = []
    symbol_rows = []
    month_rows = []
    trigger_rows = []
    candidate_trades = []

    if not enriched.empty:
        masks = candidate_masks(enriched)
        for name, mask in masks.items():
            sample = enriched[mask.fillna(False)].copy().sort_values(["entry_time", "symbol"]).reset_index(drop=True)
            sample["candidate"] = name
            candidate_trades.append(sample)
            summary_rows.append({"candidate": name, **metrics(sample)})
            symbol_rows.append(summarize_group(sample, "symbol", name))
            month_rows.append(summarize_group(sample, "month", name))
            trigger_rows.append(summarize_group(sample, "trigger_type", name))

    summary = pd.DataFrame(summary_rows)
    by_symbol = pd.concat(symbol_rows, ignore_index=True) if symbol_rows else pd.DataFrame()
    by_month = pd.concat(month_rows, ignore_index=True) if month_rows else pd.DataFrame()
    by_trigger = pd.concat(trigger_rows, ignore_index=True) if trigger_rows else pd.DataFrame()
    all_candidate_trades = pd.concat(candidate_trades, ignore_index=True) if candidate_trades else pd.DataFrame()

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol.csv", index=False)
    by_month.to_csv(OUT_DIR / "by_month.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "by_trigger.csv", index=False)
    all_candidate_trades.to_csv(OUT_DIR / "candidate_trades_oos.csv", index=False)

    data_end = coverage["last"].max() if not coverage.empty else pd.NaT
    available = coverage[coverage["has_2025_plus"]]
    unavailable = coverage[~coverage["has_2025_plus"]]

    lines = [
        "# T5 + MACD + BB 2025-2026 未使用データ検証",
        "",
        "## 注意",
        "",
        f"- 希望期間: {OOS_START.date()}〜{OOS_END.date()}",
        f"- ローカルデータ上の最終日時: {data_end}",
        "- 2026年データはローカルに存在しません。",
        "- 2025年データがある通貨のみ、未使用データとして検証しています。",
        "- ルールは2015-2024で選んだものを固定し、ここでは再最適化していません。",
        "",
        "## データカバレッジ",
        "",
        markdown_table(coverage, 40),
        "",
        "## 2025以降データあり",
        "",
        markdown_table(available, 20),
        "",
        "## 2025以降データなし",
        "",
        markdown_table(unavailable, 20),
        "",
        "## OOS結果サマリー",
        "",
        markdown_table(summary, 20) if not summary.empty else "No trades.",
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 60) if not by_symbol.empty else "No trades.",
        "",
        "## 月別",
        "",
        markdown_table(by_month, 80) if not by_month.empty else "No trades.",
        "",
        "## トリガー別",
        "",
        markdown_table(by_trigger, 40) if not by_trigger.empty else "No trades.",
        "",
        "## 出力",
        "",
        "- `data_coverage.csv`",
        "- `trades_enriched_oos.csv`",
        "- `summary.csv`",
        "- `by_symbol.csv`",
        "- `by_month.csv`",
        "- `by_trigger.csv`",
        "- `candidate_trades_oos.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if summary.empty:
        print("No OOS trades.")
    else:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

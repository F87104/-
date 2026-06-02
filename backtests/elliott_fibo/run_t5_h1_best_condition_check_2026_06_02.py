#!/usr/bin/env python3
"""
H1 check for the T5 best H4 condition.

The H4 candidate was:
    BB 0.75-1.00 / signal_recovery_bars<=16 / MACD slope3>0.03 / BB width<=4ATR

On H1, recovery<=16 means 16 hours, while on H4 it meant 64 hours.  This script
therefore checks both:
    1. H1 literal: recovery<=16 H1 bars
    2. H1 time-equivalent: recovery<=64 H1 bars
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, holiday_market, load_instrument, resample_ohlc
from run_indicator_compatibility_search import add_extended_features, enrich_trades
from run_v_recovery_trigger_study import TriggerSpec, run_spec
import run_v_recovery_trigger_study as trigger_mod


THIS_DIR = Path(__file__).resolve().parent
OUT = THIS_DIR / "results_2026_06_02" / "t5_h1_best_condition_check"
OUT.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H1"
PERIODS = [
    ("Research_2015_2024", pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31 23:59:59")),
    ("OOS_2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31 23:59:59")),
]

BASE_SPEC = TriggerSpec(
    "REC1.20_T5_STAG_OR_REBREAK_BROAD_H1",
    trigger_mode="either",
    max_recovery_to_drop=1.20,
)


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


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows_"
    headers = list(df.columns)
    rows = [[fmt(value) for value in row] for row in df.itertuples(index=False, name=None)]
    widths = [len(str(h)) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    out = []
    out.append("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    out.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows:
        out.append("| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |")
    return "\n".join(out)


def classify_period(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts.year <= 2024 else "OOS_2025_2026"


def run_t5_h1_broad(feature_frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for period, start, end in PERIODS:
        trigger_mod.START = start
        trigger_mod.END = end
        for symbol in SYMBOLS:
            trades = run_spec(feature_frames[(symbol, TIMEFRAME)], symbol, TIMEFRAME, BASE_SPEC)
            if not trades.empty:
                trades["period"] = period
                frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    enriched["period"] = enriched["entry_time"].map(classify_period)
    enriched["year"] = enriched["entry_time"].dt.year.astype(int)
    enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def best_condition(df: pd.DataFrame, recovery_max: int) -> pd.Series:
    return (
        df["bb_pos"].between(0.75, 1.00)
        & df["signal_recovery_bars"].le(recovery_max)
        & df["macd_hist_slope3"].gt(0.03)
        & df["bb_width_atr"].le(4.0)
    ).fillna(False)


def summarize_sample(df: pd.DataFrame, name: str, notes: str) -> dict[str, object]:
    research = df[df["period"].eq("Research_2015_2024")]
    oos = df[df["period"].eq("OOS_2025_2026")]
    row: dict[str, object] = {"case": name, "notes": notes}
    for prefix, sample in [("all", df), ("research", research), ("oos", oos)]:
        row.update({f"{prefix}_{k}": v for k, v in metrics(sample).items()})
    return row


def grouped(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(keys):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(keys, key))
        row.update(metrics(g))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(keys) if rows else pd.DataFrame()


def main() -> None:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    coverage_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append(
            {"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)}
        )
        feature_frames[(symbol, TIMEFRAME)] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    pd.DataFrame(coverage_rows).to_csv(OUT / "data_coverage.csv", index=False)

    broad_path = OUT / "t5_h1_broad_trades_2015_2026.csv"
    if broad_path.exists():
        trades = pd.read_csv(broad_path, parse_dates=["signal_time", "entry_time", "exit_time"])
    else:
        trades = run_t5_h1_broad(feature_frames)
        trades.to_csv(broad_path, index=False)

    cases = []
    outputs = {
        "H1_LITERAL_RECOVERY16": (
            best_condition(trades, 16),
            "H4上位条件を数値そのままH1へ適用。回復<=16時間。",
        ),
        "H1_TIME_EQUIV_RECOVERY64": (
            best_condition(trades, 64),
            "H4の回復<=16本を時間換算。H1では回復<=64時間。",
        ),
    }
    for name, (mask, notes) in outputs.items():
        sample = trades[mask].copy()
        sample.to_csv(OUT / f"{name.lower()}_trades.csv", index=False)
        cases.append(summarize_sample(sample, name, notes))
        grouped(sample, ["symbol"]).to_csv(OUT / f"{name.lower()}_by_symbol.csv", index=False)
        grouped(sample, ["year"]).to_csv(OUT / f"{name.lower()}_by_year.csv", index=False)
        grouped(sample, ["trigger_type"]).to_csv(OUT / f"{name.lower()}_by_trigger.csv", index=False)

    summary = pd.DataFrame(cases)
    summary.to_csv(OUT / "summary.csv", index=False)

    lines = [
        "# T5 H1 Best Condition Check 2026-06-02",
        "",
        "## 目的",
        "",
        "H4で強かった `BB 0.75-1.00 / 回復<=16 / MACD>0.03 / BB幅<=4ATR` をH1で検証した。",
        "",
        "H4の16本は64時間に相当するため、H1では数値そのままの16本版と、時間換算の64本版を両方確認した。",
        "",
        "## サマリー",
        "",
        md_table(summary),
        "",
        "## 解釈メモ",
        "",
        "- `H1_LITERAL_RECOVERY16`: H1で16時間以内のかなり速い回復だけを見る。",
        "- `H1_TIME_EQUIV_RECOVERY64`: H4条件と時間感覚を合わせた確認。",
        "- H1はノイズが増えるため、H4と同じPF/勝率を期待するより、先行察知や補助確認として残るかを見る。",
        "",
        "## 出力",
        "",
        "- `t5_h1_broad_trades_2015_2026.csv`",
        "- `summary.csv`",
        "- `h1_literal_recovery16_trades.csv`",
        "- `h1_time_equiv_recovery64_trades.csv`",
        "- `*_by_symbol.csv`, `*_by_year.csv`, `*_by_trigger.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {OUT / 'report_ja.md'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

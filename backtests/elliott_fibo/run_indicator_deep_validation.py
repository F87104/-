#!/usr/bin/env python3
"""
Deep validation for the strongest H4 V-candidate indicator filters.

The earlier compatibility search answered "which indicator families look good?"
This script is stricter.  It checks each practical candidate through:

- full period and 2021+ out-of-sample style metrics
- year-by-year stability
- symbol-by-symbol stability
- two-year rolling windows
- threshold sensitivity around the promising indicator families

It uses the already-enriched trade file from run_indicator_compatibility_search.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
INPUT_DIR = THIS_DIR / "results_2015_2024" / "indicator_compatibility_search"
TRADES_CSV = INPUT_DIR / "trades_enriched.csv"
OUT_DIR = THIS_DIR / "results_2015_2024" / "indicator_deep_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SPLIT_DATE = pd.Timestamp("2021-01-01")
YEARS = list(range(2015, 2025))
TWO_YEAR_WINDOWS = [
    (2015, 2016),
    (2017, 2018),
    (2019, 2020),
    (2021, 2022),
    (2023, 2024),
]


@dataclass(frozen=True)
class Candidate:
    name: str
    base_strategy: str
    family: str
    description: str
    fn: Callable[[pd.DataFrame], pd.Series]


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
    dd = curve.cummax() - curve
    return float(dd.max())


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


def metrics(df: pd.DataFrame, prefix: str) -> dict[str, float | int]:
    r = df["r_after_cost"].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        f"{prefix}_trades": int(len(df)),
        f"{prefix}_win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        f"{prefix}_total_r": float(r.sum()) if len(r) else 0.0,
        f"{prefix}_avg_r": float(r.mean()) if len(r) else 0.0,
        f"{prefix}_pf": profit_factor(r) if len(r) else math.nan,
        f"{prefix}_max_dd_r": max_drawdown(r),
        f"{prefix}_max_ls": max_losing_streak(r),
    }


def load_trades() -> pd.DataFrame:
    if not TRADES_CSV.exists():
        raise SystemExit(f"Missing input: {TRADES_CSV}. Run run_indicator_compatibility_search.py first.")
    trades = pd.read_csv(TRADES_CSV)
    trades["signal_time"] = pd.to_datetime(trades["signal_time"])
    trades["year"] = trades["signal_time"].dt.year
    trades = trades.sort_values(["signal_time", "symbol", "strategy"]).reset_index(drop=True)
    return trades


def build_candidates() -> list[Candidate]:
    return [
        Candidate(
            "BASELINE",
            "T4_REBREAK_ONLY",
            "baseline",
            "フィルターなし",
            lambda x: pd.Series(True, index=x.index),
        ),
        Candidate(
            "T4_BB_CLOSELOC_BALANCED",
            "T4_REBREAK_ONLY",
            "BB+終値位置",
            "BB位置0.60〜1.10 + 終値位置65%以上",
            lambda x: x["bb_pos"].between(0.60, 1.10) & (x["close_location"] >= 0.65),
        ),
        Candidate(
            "T4_BB_ONLY",
            "T4_REBREAK_ONLY",
            "BB",
            "BB位置0.60〜1.10",
            lambda x: x["bb_pos"].between(0.60, 1.10),
        ),
        Candidate(
            "T4_BB_STRICT",
            "T4_REBREAK_ONLY",
            "BB",
            "BB位置0.50〜1.00",
            lambda x: x["bb_pos"].between(0.50, 1.00),
        ),
        Candidate(
            "T4_CHOP_BB",
            "T4_REBREAK_ONLY",
            "CHOP+BB",
            "CHOP<50 + BB位置0.60〜1.10",
            lambda x: (x["chop14"] < 50) & x["bb_pos"].between(0.60, 1.10),
        ),
        Candidate(
            "T4_CCI_RANGE",
            "T4_REBREAK_ONLY",
            "CCI",
            "CCI20 -50〜150",
            lambda x: x["cci20"].between(-50, 150),
        ),
        Candidate(
            "T4_ADX_CAP",
            "T4_REBREAK_ONLY",
            "ADX",
            "ADX14<25",
            lambda x: x["adx14"] < 25,
        ),
        Candidate(
            "T4_MACD_RISING",
            "T4_REBREAK_ONLY",
            "MACD",
            "MACDヒストグラムが3本前より上昇",
            lambda x: x["macd_hist_slope3"] > 0,
        ),
        Candidate(
            "T4_EMA_BB_CONSERVATIVE",
            "T4_REBREAK_ONLY",
            "EMA+BB",
            "EMA20>EMA50 + BB位置0.60〜1.10",
            lambda x: (x["ema20"] > x["ema50"]) & x["bb_pos"].between(0.60, 1.10),
        ),
        Candidate(
            "BASELINE",
            "T5_STAG_OR_REBREAK",
            "baseline",
            "フィルターなし",
            lambda x: pd.Series(True, index=x.index),
        ),
        Candidate(
            "T5_MACD_RISING_AGGRESSIVE",
            "T5_STAG_OR_REBREAK",
            "MACD",
            "MACDヒストグラムが3本前より上昇",
            lambda x: x["macd_hist_slope3"] > 0,
        ),
        Candidate(
            "T5_BB_WIDTH",
            "T5_STAG_OR_REBREAK",
            "BB幅",
            "BB幅2〜6ATR",
            lambda x: x["bb_width_atr"].between(2.0, 6.0),
        ),
        Candidate(
            "T5_BB_CLOSELOC_BALANCED",
            "T5_STAG_OR_REBREAK",
            "BB+終値位置",
            "BB位置0.60〜1.10 + 終値位置65%以上",
            lambda x: x["bb_pos"].between(0.60, 1.10) & (x["close_location"] >= 0.65),
        ),
        Candidate(
            "T5_CLOSELOC75",
            "T5_STAG_OR_REBREAK",
            "終値位置",
            "終値位置75%以上",
            lambda x: x["close_location"] >= 0.75,
        ),
        Candidate(
            "T5_CCI_RANGE",
            "T5_STAG_OR_REBREAK",
            "CCI",
            "CCI20 -50〜150",
            lambda x: x["cci20"].between(-50, 150),
        ),
        Candidate(
            "T5_ADX_CAP",
            "T5_STAG_OR_REBREAK",
            "ADX",
            "ADX14<25",
            lambda x: x["adx14"] < 25,
        ),
        Candidate(
            "T5_CHOP_CAP",
            "T5_STAG_OR_REBREAK",
            "CHOP",
            "CHOP<50",
            lambda x: x["chop14"] < 50,
        ),
        Candidate(
            "T5_EMA_BB_CONSERVATIVE",
            "T5_STAG_OR_REBREAK",
            "EMA+BB",
            "EMA20>EMA50 + BB位置0.60〜1.10",
            lambda x: (x["ema20"] > x["ema50"]) & x["bb_pos"].between(0.60, 1.10),
        ),
        Candidate(
            "T5_EMA_RSI_ATR_CONSERVATIVE",
            "T5_STAG_OR_REBREAK",
            "EMA+RSI+ATR",
            "EMA20>EMA50 + RSI50〜75 + ATR上位15%除外",
            lambda x: (x["ema20"] > x["ema50"]) & x["rsi14"].between(50, 75) & (x["atr_pctile_252"] < 85),
        ),
    ]


def candidate_sample(trades: pd.DataFrame, candidate: Candidate) -> pd.DataFrame:
    group = trades[trades["strategy"] == candidate.base_strategy].copy()
    mask = candidate.fn(group).fillna(False)
    return group[mask].sort_values(["signal_time", "symbol"]).reset_index(drop=True)


def stability_rows(sample: pd.DataFrame, candidate: Candidate, group_col: str) -> list[dict]:
    rows: list[dict] = []
    for key, group in sample.groupby(group_col):
        row = {
            "candidate": candidate.name,
            "base_strategy": candidate.base_strategy,
            group_col: key,
        }
        row.update(metrics(group, "m"))
        rows.append(row)
    return rows


def two_year_rows(sample: pd.DataFrame, candidate: Candidate) -> list[dict]:
    rows: list[dict] = []
    for start, end in TWO_YEAR_WINDOWS:
        part = sample[(sample["year"] >= start) & (sample["year"] <= end)]
        row = {
            "candidate": candidate.name,
            "base_strategy": candidate.base_strategy,
            "window": f"{start}-{end}",
        }
        row.update(metrics(part, "m"))
        rows.append(row)
    return rows


def summarize_candidate(trades: pd.DataFrame, candidate: Candidate, baselines: dict[str, dict]) -> dict:
    sample = candidate_sample(trades, candidate)
    train = sample[sample["signal_time"] < SPLIT_DATE]
    test = sample[sample["signal_time"] >= SPLIT_DATE]

    by_year = sample.groupby("year")["r_after_cost"].sum()
    by_symbol = sample.groupby("symbol")["r_after_cost"].sum()
    by_window = []
    for start, end in TWO_YEAR_WINDOWS:
        part = sample[(sample["year"] >= start) & (sample["year"] <= end)]
        by_window.append(float(part["r_after_cost"].sum()) if not part.empty else 0.0)

    row: dict = {
        "candidate": candidate.name,
        "base_strategy": candidate.base_strategy,
        "family": candidate.family,
        "description": candidate.description,
        "positive_years": int((by_year > 0).sum()),
        "tested_years": int(by_year.size),
        "positive_symbols": int((by_symbol > 0).sum()),
        "tested_symbols": int(by_symbol.size),
        "positive_2y_windows": int(sum(value > 0 for value in by_window)),
        "tested_2y_windows": len(by_window),
        "worst_year_r": float(by_year.min()) if by_year.size else 0.0,
        "worst_symbol_r": float(by_symbol.min()) if by_symbol.size else 0.0,
        "worst_2y_window_r": float(min(by_window)) if by_window else 0.0,
    }
    row.update(metrics(sample, "all"))
    row.update(metrics(train, "train"))
    row.update(metrics(test, "test"))

    base = baselines[candidate.base_strategy]
    row["all_total_delta"] = row["all_total_r"] - base["all_total_r"]
    row["test_total_delta"] = row["test_total_r"] - base["test_total_r"]
    row["all_avg_delta"] = row["all_avg_r"] - base["all_avg_r"]
    row["test_avg_delta"] = row["test_avg_r"] - base["test_avg_r"]
    row["all_dd_delta"] = row["all_max_dd_r"] - base["all_max_dd_r"]
    row["test_dd_delta"] = row["test_max_dd_r"] - base["test_max_dd_r"]

    year_ratio = row["positive_years"] / row["tested_years"] if row["tested_years"] else 0.0
    symbol_ratio = row["positive_symbols"] / row["tested_symbols"] if row["tested_symbols"] else 0.0
    window_ratio = row["positive_2y_windows"] / row["tested_2y_windows"] if row["tested_2y_windows"] else 0.0
    trade_penalty = max(0, 80 - row["all_trades"]) * 0.10 + max(0, 35 - row["test_trades"]) * 0.20
    row["stability_score"] = (
        row["test_total_r"]
        + row["test_avg_delta"] * 60
        - row["test_max_dd_r"] * 0.80
        + year_ratio * 10
        + symbol_ratio * 10
        + window_ratio * 10
        - max(0, -row["worst_symbol_r"]) * 0.30
        - max(0, -row["worst_year_r"]) * 0.20
        - trade_penalty
    )
    return row


def run_candidate_validation(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidates = build_candidates()
    baselines = {}
    for candidate in candidates:
        if candidate.name == "BASELINE":
            sample = candidate_sample(trades, candidate)
            test = sample[sample["signal_time"] >= SPLIT_DATE]
            base_metrics = {}
            base_metrics.update(metrics(sample, "all"))
            base_metrics.update(metrics(test, "test"))
            baselines[candidate.base_strategy] = base_metrics

    summary_rows = []
    symbol_rows = []
    year_rows = []
    window_rows = []
    for candidate in candidates:
        summary_rows.append(summarize_candidate(trades, candidate, baselines))
        sample = candidate_sample(trades, candidate)
        symbol_rows.extend(stability_rows(sample, candidate, "symbol"))
        year_rows.extend(stability_rows(sample, candidate, "year"))
        window_rows.extend(two_year_rows(sample, candidate))

    summary = pd.DataFrame(summary_rows).sort_values(["base_strategy", "stability_score"], ascending=[True, False])
    by_symbol = pd.DataFrame(symbol_rows).sort_values(["candidate", "symbol"])
    by_year = pd.DataFrame(year_rows).sort_values(["candidate", "year"])
    by_window = pd.DataFrame(window_rows).sort_values(["candidate", "window"])
    return summary, by_symbol, by_year, by_window


def add_sensitivity_row(rows: list[dict], trades: pd.DataFrame, strategy: str, name: str, desc: str, mask: pd.Series) -> None:
    group = trades[trades["strategy"] == strategy].copy()
    sample = group[mask.reindex(group.index).fillna(False)]
    test = sample[sample["signal_time"] >= SPLIT_DATE]
    by_year = sample.groupby("year")["r_after_cost"].sum()
    by_symbol = sample.groupby("symbol")["r_after_cost"].sum()
    row = {
        "base_strategy": strategy,
        "sweep": name,
        "description": desc,
        "positive_years": int((by_year > 0).sum()),
        "tested_years": int(by_year.size),
        "positive_symbols": int((by_symbol > 0).sum()),
        "tested_symbols": int(by_symbol.size),
        "worst_year_r": float(by_year.min()) if by_year.size else 0.0,
        "worst_symbol_r": float(by_symbol.min()) if by_symbol.size else 0.0,
    }
    row.update(metrics(sample, "all"))
    row.update(metrics(test, "test"))
    rows.append(row)


def run_sensitivity(trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for strategy in ["T4_REBREAK_ONLY", "T5_STAG_OR_REBREAK"]:
        group = trades[trades["strategy"] == strategy]

        for lo in [0.50, 0.55, 0.60, 0.65]:
            for hi in [1.00, 1.10, 1.20]:
                if hi <= lo:
                    continue
                mask = group["bb_pos"].between(lo, hi)
                add_sensitivity_row(rows, trades, strategy, "BB_POS", f"bb_pos {lo:.2f}-{hi:.2f}", mask)

        for close_loc in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
            mask = group["close_location"] >= close_loc
            add_sensitivity_row(rows, trades, strategy, "CLOSE_LOC", f"close_location >= {close_loc:.2f}", mask)

        for close_loc in [0.60, 0.65, 0.70, 0.75]:
            mask = group["bb_pos"].between(0.60, 1.10) & (group["close_location"] >= close_loc)
            add_sensitivity_row(rows, trades, strategy, "BB_CLOSELOC", f"bb_pos 0.60-1.10 + close_location >= {close_loc:.2f}", mask)

        for chop in [45, 50, 55, 60]:
            mask = group["chop14"] < chop
            add_sensitivity_row(rows, trades, strategy, "CHOP_CAP", f"chop14 < {chop}", mask)

        for adx in [20, 25, 30]:
            mask = group["adx14"] < adx
            add_sensitivity_row(rows, trades, strategy, "ADX_CAP", f"adx14 < {adx}", mask)

        for lo, hi in [(-100, 100), (-50, 150), (0, 150), (-50, 200), (0, 200)]:
            mask = group["cci20"].between(lo, hi)
            add_sensitivity_row(rows, trades, strategy, "CCI_RANGE", f"cci20 {lo}..{hi}", mask)

        for lo, hi in [(1.5, 5.0), (2.0, 5.0), (2.0, 6.0), (2.5, 6.0), (3.0, 7.0)]:
            mask = group["bb_width_atr"].between(lo, hi)
            add_sensitivity_row(rows, trades, strategy, "BB_WIDTH", f"bb_width_atr {lo:.1f}-{hi:.1f}", mask)

        mask = group["macd_hist_slope3"] > 0
        add_sensitivity_row(rows, trades, strategy, "MACD_RISING", "macd_hist_slope3 > 0", mask)
        mask = (group["macd_hist_slope3"] > 0) & (group["close_location"] >= 0.65)
        add_sensitivity_row(rows, trades, strategy, "MACD_CLOSELOC", "macd_hist_slope3 > 0 + close_location >= 0.65", mask)
        mask = (group["macd_hist_slope3"] > 0) & group["bb_pos"].between(0.60, 1.10)
        add_sensitivity_row(rows, trades, strategy, "MACD_BB", "macd_hist_slope3 > 0 + bb_pos 0.60-1.10", mask)
        mask = (group["macd_hist_slope3"] > 0) & (group["chop14"] < 50)
        add_sensitivity_row(rows, trades, strategy, "MACD_CHOP", "macd_hist_slope3 > 0 + chop14 < 50", mask)

    out = pd.DataFrame(rows)
    out["score"] = (
        out["test_total_r"]
        + out["test_avg_r"] * 40
        - out["test_max_dd_r"] * 0.8
        + (out["positive_years"] / out["tested_years"].replace(0, np.nan)).fillna(0) * 8
        + (out["positive_symbols"] / out["tested_symbols"].replace(0, np.nan)).fillna(0) * 8
        - np.maximum(0, -out["worst_symbol_r"]) * 0.25
    )
    return out.sort_values(["base_strategy", "score"], ascending=[True, False])


def write_report(summary: pd.DataFrame, by_symbol: pd.DataFrame, by_year: pd.DataFrame, by_window: pd.DataFrame, sensitivity: pd.DataFrame) -> None:
    compact_cols = [
        "candidate",
        "family",
        "description",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_trades",
        "test_win_rate",
        "test_total_r",
        "test_avg_r",
        "test_pf",
        "test_max_dd_r",
        "positive_years",
        "tested_years",
        "positive_symbols",
        "tested_symbols",
        "positive_2y_windows",
        "tested_2y_windows",
        "worst_year_r",
        "worst_symbol_r",
        "stability_score",
    ]
    sens_cols = [
        "base_strategy",
        "sweep",
        "description",
        "all_trades",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_trades",
        "test_total_r",
        "test_avg_r",
        "test_pf",
        "test_max_dd_r",
        "positive_years",
        "positive_symbols",
        "worst_symbol_r",
        "score",
    ]
    top_sensitivity = sensitivity[
        (sensitivity["all_trades"] >= 80)
        & (sensitivity["test_trades"] >= 30)
        & (sensitivity["test_total_r"] > 0)
    ].head(60)

    lines = [
        "# 有力インジケータ 本格検証",
        "",
        "## 結論サマリー",
        "",
        "- `T5 + MACDヒストグラム上昇` は利益の上積みが最も大きい攻め候補。",
        "- `T4 + BB位置 + 終値位置` はバランス型。通貨別・後半期間の安定性が良い。",
        "- `ADXは高いほど良い` ではなく、今回の構造では `ADX<25` のような上限フィルタが有効。",
        "- `BB位置` と `終値位置` は閾値を少し動かしても大崩れしづらく、Pine化の優先度が高い。",
        "",
        "## 候補別ディープ検証",
        "",
        markdown_table(summary[compact_cols], 80),
        "",
        "## 閾値感度 上位",
        "",
        markdown_table(top_sensitivity[sens_cols], 80),
        "",
        "## 出力ファイル",
        "",
        "- `deep_validation_summary.csv`",
        "- `deep_validation_by_symbol.csv`",
        "- `deep_validation_by_year.csv`",
        "- `deep_validation_2y_windows.csv`",
        "- `threshold_sensitivity.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    trades = load_trades()
    summary, by_symbol, by_year, by_window = run_candidate_validation(trades)
    sensitivity = run_sensitivity(trades)

    summary.to_csv(OUT_DIR / "deep_validation_summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "deep_validation_by_symbol.csv", index=False)
    by_year.to_csv(OUT_DIR / "deep_validation_by_year.csv", index=False)
    by_window.to_csv(OUT_DIR / "deep_validation_2y_windows.csv", index=False)
    sensitivity.to_csv(OUT_DIR / "threshold_sensitivity.csv", index=False)
    write_report(summary, by_symbol, by_year, by_window, sensitivity)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Top candidates:")
    show_cols = [
        "candidate",
        "base_strategy",
        "all_trades",
        "all_total_r",
        "all_pf",
        "all_max_dd_r",
        "test_trades",
        "test_total_r",
        "test_pf",
        "test_max_dd_r",
        "positive_years",
        "positive_symbols",
        "positive_2y_windows",
        "stability_score",
    ]
    print(summary[show_cols].to_string(index=False))


if __name__ == "__main__":
    main()

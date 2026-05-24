#!/usr/bin/env python3
"""
Skeptic audit for the T5 + MACD + BB candidate.

This is intentionally conservative.  It does not search for better settings;
it checks whether the attractive candidate survives harsher assumptions:

- additional R cost per trade
- multiplied original cost
- one global position at a time
- one entry per day/week
- out-of-sample and two-year windows
- duplicate/candidate reuse checks
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
INPUT = THIS_DIR / "results_2015_2024" / "indicator_compatibility_search" / "trades_enriched.csv"
OUT_DIR = THIS_DIR / "results_2015_2024" / "t5_skeptic_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_STRATEGY = "T5_STAG_OR_REBREAK"
SPLIT_DATE = pd.Timestamp("2021-01-01")


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


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict[str, float | int]:
    r = df[r_col].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def load_base() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    for col in ["signal_time", "entry_time", "exit_time"]:
        df[col] = pd.to_datetime(df[col])
    df["year"] = df["entry_time"].dt.year
    df["date"] = df["entry_time"].dt.date.astype(str)
    df["week"] = df["entry_time"].dt.to_period("W").astype(str)
    df["candidate_key_full"] = (
        df["symbol"].astype(str)
        + ":"
        + df["timeframe"].astype(str)
        + ":"
        + df["v_start_i"].astype(str)
        + "-"
        + df["v_extreme_i"].astype(str)
    )
    df["cost_r"] = df["r_clean"].astype(float) - df["r_after_cost"].astype(float)
    base = df[df["strategy"].eq(BASE_STRATEGY)].copy()
    return base.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def candidate_masks(base: pd.DataFrame) -> dict[str, pd.Series]:
    macd = base["macd_hist_slope3"] > 0
    return {
        "Current_060_110": macd & base["bb_pos"].between(0.60, 1.10),
        "Robust_075_105_width7": macd & base["bb_pos"].between(0.75, 1.05) & (base["bb_width_atr"] <= 7.0),
        "Strict_075_100_width7": macd & base["bb_pos"].between(0.75, 1.00) & (base["bb_width_atr"] <= 7.0),
    }


def keep_one_global_position(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    busy_until = pd.Timestamp.min
    for row in df.sort_values(["entry_time", "symbol"]).to_dict("records"):
        if pd.Timestamp(row["entry_time"]) >= busy_until:
            rows.append(row)
            busy_until = pd.Timestamp(row["exit_time"])
    return pd.DataFrame(rows)


def keep_one_symbol_position(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    busy: dict[str, pd.Timestamp] = {}
    for row in df.sort_values(["entry_time", "symbol"]).to_dict("records"):
        symbol = str(row["symbol"])
        until = busy.get(symbol, pd.Timestamp.min)
        if pd.Timestamp(row["entry_time"]) >= until:
            rows.append(row)
            busy[symbol] = pd.Timestamp(row["exit_time"])
    return pd.DataFrame(rows)


def variant_rows(name: str, sample: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []

    def add(label: str, frame: pd.DataFrame, r_col: str = "r_after_cost") -> None:
        rows.append({"candidate": name, "stress": label, **metrics(frame, r_col)})

    add("normal", sample)

    for extra in [0.05, 0.10, 0.20]:
        frame = sample.copy()
        frame[f"r_minus_{extra}"] = frame["r_after_cost"] - extra
        add(f"extra_cost_{extra:.2f}R_each", frame, f"r_minus_{extra}")

    for mult in [2, 3, 5]:
        frame = sample.copy()
        frame[f"r_cost_x{mult}"] = frame["r_clean"] - frame["cost_r"] * mult
        add(f"original_cost_x{mult}", frame, f"r_cost_x{mult}")

    add("one_global_position", keep_one_global_position(sample))
    add("one_symbol_position", keep_one_symbol_position(sample))
    add("first_signal_per_day", sample.sort_values(["entry_time", "symbol"]).drop_duplicates(["date"]))
    add("first_signal_per_week", sample.sort_values(["entry_time", "symbol"]).drop_duplicates(["week"]))
    add("exclude_silver", sample[sample["symbol"].ne("SILVER")])
    add("2021_2024_only", sample[sample["entry_time"] >= SPLIT_DATE])
    add("2023_2024_only", sample[sample["year"].between(2023, 2024)])
    return rows


def split_rows(name: str, sample: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    periods = [
        ("2015-2016", 2015, 2016),
        ("2017-2018", 2017, 2018),
        ("2019-2020", 2019, 2020),
        ("2021-2022", 2021, 2022),
        ("2023-2024", 2023, 2024),
    ]
    for label, start, end in periods:
        frame = sample[sample["year"].between(start, end)]
        rows.append({"candidate": name, "period": label, **metrics(frame)})
    return rows


def duplicate_rows(name: str, sample: pd.DataFrame) -> dict[str, int | float]:
    exact_dups = int(sample.duplicated(["symbol", "signal_time", "entry_time", "exit_time"]).sum())
    candidate_reuse = int(sample.duplicated(["candidate_key_full"]).sum())
    concurrent = len(sample) - len(keep_one_global_position(sample))
    same_symbol_overlap = len(sample) - len(keep_one_symbol_position(sample))
    return {
        "candidate": name,
        "trades": int(len(sample)),
        "exact_duplicate_rows": exact_dups,
        "same_v_candidate_reuse": candidate_reuse,
        "removed_by_one_global_position": int(concurrent),
        "removed_by_one_symbol_position": int(same_symbol_overlap),
    }


def by_group(name: str, sample: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows = []
    for key, frame in sample.groupby(group_col):
        rows.append({"candidate": name, group_col: key, **metrics(frame)})
    return pd.DataFrame(rows)


def main() -> None:
    base = load_base()
    masks = candidate_masks(base)

    summary_rows = []
    stress_rows = []
    split_rows_all = []
    duplicate_checks = []
    symbol_rows = []
    trigger_rows = []

    for name, mask in masks.items():
        sample = base[mask.fillna(False)].copy().sort_values(["entry_time", "symbol"]).reset_index(drop=True)
        summary_rows.append({"candidate": name, **metrics(sample)})
        stress_rows.extend(variant_rows(name, sample))
        split_rows_all.extend(split_rows(name, sample))
        duplicate_checks.append(duplicate_rows(name, sample))
        symbol_rows.append(by_group(name, sample, "symbol"))
        trigger_rows.append(by_group(name, sample, "trigger_type"))

    summary = pd.DataFrame(summary_rows)
    stress = pd.DataFrame(stress_rows)
    splits = pd.DataFrame(split_rows_all)
    duplicates = pd.DataFrame(duplicate_checks)
    by_symbol = pd.concat(symbol_rows, ignore_index=True) if symbol_rows else pd.DataFrame()
    by_trigger = pd.concat(trigger_rows, ignore_index=True) if trigger_rows else pd.DataFrame()

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    stress.to_csv(OUT_DIR / "stress_tests.csv", index=False)
    splits.to_csv(OUT_DIR / "two_year_windows.csv", index=False)
    duplicates.to_csv(OUT_DIR / "duplicate_and_overlap_checks.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "by_trigger.csv", index=False)

    lines = [
        "# T5 + MACD + BB 懐疑監査",
        "",
        "## 目的",
        "",
        "結果が良すぎる候補について、未来参照ではなくても起こりうる「最適化しすぎ」「重複カウント」「約定/コストの甘さ」をチェックする。",
        "",
        "## 重要なコード確認",
        "",
        "- V候補のピボットは `confirm_i <= 現在バー` になってからだけ active に入るため、ピボット確定前の未来情報は使っていない。",
        "- エントリーはシグナル足ではなく、シグナル次足の始値。",
        "- MACD/BB等のフィルタは `signal_time` の足で付与しており、次足エントリー前に確定している情報だけを見る設計。",
        "- SL/TP同時到達時は SL 優先で処理しているため、同一足内の約定判定は保守的。",
        "",
        "## 候補別サマリー",
        "",
        markdown_table(summary, 20),
        "",
        "## 重複・同時保有チェック",
        "",
        markdown_table(duplicates, 20),
        "",
        "## ストレステスト",
        "",
        markdown_table(stress, 80),
        "",
        "## 2年ごとの成績",
        "",
        markdown_table(splits, 80),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 80),
        "",
        "## トリガー別",
        "",
        markdown_table(by_trigger, 40),
        "",
        "## 出力",
        "",
        "- `summary.csv`",
        "- `stress_tests.csv`",
        "- `two_year_windows.csv`",
        "- `duplicate_and_overlap_checks.csv`",
        "- `by_symbol.csv`",
        "- `by_trigger.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary.to_string(index=False))
    print()
    print(duplicates.to_string(index=False))


if __name__ == "__main__":
    main()

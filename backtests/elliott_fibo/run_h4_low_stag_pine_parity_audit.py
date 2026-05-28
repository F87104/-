#!/usr/bin/env python3
"""
Pine parity audit for the H4 low-stagnation short setup.

The Python backtest is treated as the source of truth. This script exports the
exact expected trade ledger that the Pine strategy must reproduce before any
TradingView strategy-tester metrics are trusted.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import markdown_table
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_precision_hardening" / "primary_trades.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_low_stag_pine_parity_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"
CORE4 = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY"}


def load_primary() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def quality_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_depth_atr"].ge(0.10) & df["break_close_location"].le(0.50)


def strict_mask(df: pd.DataFrame) -> pd.Series:
    return quality_mask(df) & (df["support_age_bars"].gt(10) | df["break_depth_atr"].ge(0.20))


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def metric_row(name: str, sample: pd.DataFrame) -> dict:
    row = {"case": name}
    row.update(metrics(sample, R_COL))
    row["pf"] = profit_factor(sample[R_COL].astype(float)) if len(sample) else math.nan
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    return row


def slim_trades(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "symbol",
        "signal_time",
        "entry_time",
        "base_exit_time",
        "base_exit_reason",
        "trigger_type",
        "lookback_bars",
        "support_age_bars",
        "prior_low",
        "zone_low",
        "zone_high",
        "break_depth_atr",
        "break_close_location",
        "risk_atr_at_signal",
        "base_entry",
        "base_stop",
        "base_target_2r",
        R_COL,
    ]
    cols = [c for c in cols if c in df.columns]
    return df[cols].sort_values(["symbol", "entry_time"]).reset_index(drop=True)


def write_report(primary: pd.DataFrame, summaries: pd.DataFrame, expected: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# H4 Low-Stagnation Short Pine Parity Audit",
        "",
        "Status: Pine変換監査用。Python検証を正として、TradingView Pine strategyが同じシグナルを出すか確認する。",
        "",
        "## 重要結論",
        "",
        "- Pineのストラテジーテスター成績は、Pythonの期待シグナルと一致するまで採用判断に使わない。",
        "- TradingView側はデータ提供元、タイムゾーン、過去データ開始日、年末年始除外、コスト処理がPythonと違う可能性がある。",
        "- まずは単体通貨で `entry_time` と件数が一致するかだけを見る。PFや勝率はその後。",
        "",
        "## Pine設定",
        "",
        "- チャート: H4",
        "- 検証開始: 2015-01-01",
        "- 検証終了: 2026-12-31",
        "- 12/15-1/10除外: ON",
        "- core4のみ: ON",
        "- entryMode: `実戦候補` または `厳選候補`",
        "- default quantityは成績比較用ではなく、まずシグナル一致確認用。",
        "",
        "## 期待サマリー",
        "",
        markdown_table(summaries, 80),
        "",
        "## GBPJPY 期待シグナル",
        "",
        "TradingViewのGBPJPY H4で、まずこの4件に近い場所だけが出るか確認する。",
        "時刻はPythonデータのindexで、TradingView表示タイムゾーンとはずれる場合がある。",
        "",
        markdown_table(expected["gbpjpy_practical"], 80),
        "",
        "## 通貨別 実戦候補 件数",
        "",
        markdown_table(
            expected["core4_practical"]
            .groupby("symbol", as_index=False)
            .agg(trades=("symbol", "size"), total_r=(R_COL, "sum")),
            20,
        ),
        "",
        "## 出力CSV",
        "",
        "- `expected_primary_all.csv`",
        "- `expected_core4_candidate.csv`",
        "- `expected_core4_practical.csv`",
        "- `expected_core4_strict.csv`",
        "- `expected_gbpjpy_practical.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    primary = load_primary()
    core4 = primary[primary["symbol"].isin(CORE4)].copy()
    core4_practical = core4[quality_mask(core4)].copy()
    core4_strict = core4[strict_mask(core4)].copy()
    gbpjpy_practical = primary[primary["symbol"].eq("GBPJPY") & quality_mask(primary)].copy()

    expected = {
        "primary_all": slim_trades(primary),
        "core4_candidate": slim_trades(core4),
        "core4_practical": slim_trades(core4_practical),
        "core4_strict": slim_trades(core4_strict),
        "gbpjpy_practical": slim_trades(gbpjpy_practical),
    }

    for name, sample in expected.items():
        sample.to_csv(OUT_DIR / f"expected_{name}.csv", index=False)

    summaries = pd.DataFrame(
        [
            metric_row("Primary all", primary),
            metric_row("Primary core4 candidate", core4),
            metric_row("Primary core4 practical", core4_practical),
            metric_row("Primary core4 strict", core4_strict),
            metric_row("GBPJPY practical", gbpjpy_practical),
        ]
    )
    summaries.to_csv(OUT_DIR / "summary.csv", index=False)
    write_report(primary, summaries, expected)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summaries.to_string(index=False))


if __name__ == "__main__":
    main()

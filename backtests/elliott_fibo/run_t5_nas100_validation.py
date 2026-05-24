#!/usr/bin/env python3
"""
NAS100 / US100 validation for the H4 T5 + MACD + BB idea.

The local data uses NAS100 filenames.  This script treats that dataset as the
US100/NAS100 proxy and keeps the existing T5 research code untouched.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

import run_elliott_fibo_study as base
import run_t5_practical_robustness_audit as audit
from run_indicator_compatibility_search import add_extended_features
from run_elliott_fibo_study import add_indicators, markdown_table, resample_ohlc


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
DATA_DIR = REPO_ROOT / "F87104_test"
OUT_DIR = THIS_DIR / "results_2026_05_24" / "nas100_us100_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL = "NAS100"
TIMEFRAME = "H4"

# Conservative point-cost assumption for index CFD style data.
# Exact live spread/slippage depends on the broker, so the report also includes
# cost stress tests.
BASE_COST = {"spread_price": 2.0, "slip_price": 1.0}


def load_nas100() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("NAS100_H1_*.csv"))
    if not files:
        raise FileNotFoundError("NAS100_H1_*.csv was not found under F87104_test")
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_csv(path)
        df.columns = [c.strip("<>").lower() for c in df.columns]
        dt = pd.to_datetime(
            df["dtyyyymmdd"].astype(str) + df["time"].astype(str).str.zfill(4),
            format="%Y%m%d%H%M",
        )
        df["datetime"] = dt
        frames.append(df.set_index("datetime")[["open", "high", "low", "close"]].astype(float))
    out = pd.concat(frames).sort_index()
    return out[~out.index.duplicated(keep="first")]


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
    r = df[r_col].astype(float) if not df.empty and r_col in df.columns else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def period_of(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts.year <= 2024 else "OOS_2025_2026"


def summary_row(name: str, df: pd.DataFrame, notes: str = "", r_col: str = "r_after_cost") -> dict:
    research = df[df["period"].eq("Research_2015_2024")] if not df.empty else df
    oos = df[df["period"].eq("OOS_2025_2026")] if not df.empty else df
    row = {"case": name, "notes": notes}
    row.update({f"all_{k}": v for k, v in metrics(df, r_col).items()})
    row.update({f"research_{k}": v for k, v in metrics(research, r_col).items()})
    row.update({f"oos_{k}": v for k, v in metrics(oos, r_col).items()})
    return row


def pine_default_mask(trades: pd.DataFrame) -> pd.Series:
    """Approximate the current live-ready Pine defaults.

    Defaults in pine/h4_t5_macd_bb_live_ready.pine:
    - BB preset: 0.75 to 1.00 with width<=7ATR
    - guard BB upper: <=0.95
    - candidate age: <=16 H4 bars
    - MACD slope3: >0
    - weak single rebreak guard
    """
    return (
        trades["bb_pos"].between(0.75, 0.95)
        & trades["signal_recovery_bars"].le(16)
        & trades["macd_hist_slope3"].gt(0)
        & trades["bb_width_atr"].le(7.0)
        & audit.not_single_weak_rebreak(trades, macd_weak=0.03)
    ).fillna(False)


def apply_operation_r(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    bb_width = out["bb_width_atr"]
    macd = out["macd_hist_slope3"]
    skip = bb_width.isna() | bb_width.gt(5.0)
    half = (~skip) & (bb_width.gt(4.0) | macd.le(0.02))
    out["operation"] = np.where(skip, "SKIP", np.where(half, "HALF", "FULL"))
    out["lot_mult"] = np.where(skip, 0.0, np.where(half, 0.5, 1.0))
    out["account_r"] = out["r_after_cost"] * out["lot_mult"]
    out["operation_reason"] = np.select(
        [
            bb_width.isna(),
            bb_width.gt(5.0),
            bb_width.gt(4.0) & macd.le(0.02),
            bb_width.gt(4.0),
            macd.le(0.02),
        ],
        [
            "BB width missing",
            "BB width > 5ATR",
            "BB width 4-5ATR + weak MACD",
            "BB width 4-5ATR",
            "MACD slope3 <= 0.02",
        ],
        default="clean",
    )
    return out


def cost_stress_rows(sample: pd.DataFrame) -> list[dict]:
    if sample.empty:
        return []
    cost_r = sample["r_clean"] - sample["r_after_cost"]
    rows = []
    for name, r in [
        ("Pine default cost x1", sample["r_after_cost"]),
        ("Pine default cost x2", sample["r_clean"] - cost_r * 2.0),
        ("Pine default cost x3", sample["r_clean"] - cost_r * 3.0),
        ("Pine default extra -0.10R", sample["r_after_cost"] - 0.10),
        ("Pine default extra -0.20R", sample["r_after_cost"] - 0.20),
    ]:
        frame = sample.copy()
        frame["stress_r"] = r
        rows.append(summary_row(name, frame, "same trades, stressed execution", "stress_r"))
    return rows


def main() -> None:
    # Make the existing simulator accept NAS100 without modifying global source.
    base.COST_TABLE[SYMBOL] = BASE_COST
    audit.SYMBOLS = [SYMBOL]

    raw = load_nas100()
    h4 = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    feature_frames = {(SYMBOL, TIMEFRAME): h4}

    trades = audit.run_t5_broad(feature_frames)
    if trades.empty:
        raise RuntimeError("No NAS100 trades were generated.")

    trades["period"] = pd.to_datetime(trades["entry_time"]).map(period_of)
    trades["year"] = pd.to_datetime(trades["entry_time"]).dt.year
    trades = trades.sort_values(["entry_time"]).reset_index(drop=True)
    trades.to_csv(OUT_DIR / "nas100_t5_broad_trades.csv", index=False)

    practical_mask = audit.practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0)
    pine_mask = pine_default_mask(trades)
    pine_trades = apply_operation_r(trades[pine_mask])
    pine_taken = pine_trades[pine_trades["lot_mult"] > 0].copy()
    pine_taken.to_csv(OUT_DIR / "nas100_pine_default_taken_trades.csv", index=False)

    cases = [
        ("00 Broad T5 universe", trades, "V候補後にstagnation/rebreak。追加フィルタなし", "r_after_cost"),
        ("01 Research practical strict", trades[practical_mask], "BB0.60-0.95, recovery<=16, MACD>0, BB幅<=4ATR", "r_after_cost"),
        ("02 Pine default signal set", trades[pine_mask], "Pine現行デフォルトに近い候補。FULL/HALF/SKIP前", "r_after_cost"),
        ("03 Pine default operation weighted", pine_taken, "FULL=1R, HALF=0.5Rとして口座R換算", "account_r"),
    ]
    rows = [summary_row(name, frame, notes, r_col) for name, frame, notes, r_col in cases]
    rows.extend(cost_stress_rows(pine_taken))
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / "nas100_summary.csv", index=False)

    by_year_rows = []
    for year, group in pine_taken.groupby("year"):
        row = {"year": int(year)}
        row.update(metrics(group, "account_r"))
        by_year_rows.append(row)
    by_year = pd.DataFrame(by_year_rows)
    by_year.to_csv(OUT_DIR / "nas100_pine_default_by_year.csv", index=False)

    op_table = (
        pine_trades.groupby("operation", dropna=False)
        .agg(
            trades=("operation", "size"),
            win_rate=("r_after_cost", lambda s: float((s > 0).mean() * 100)),
            raw_total_r=("r_after_cost", "sum"),
            account_total_r=("account_r", "sum"),
            avg_raw_r=("r_after_cost", "mean"),
        )
        .reset_index()
    )
    op_table.to_csv(OUT_DIR / "nas100_operation_breakdown.csv", index=False)

    report = [
        "# NAS100 / US100 H4 T5 検証",
        "",
        f"- データ: `{DATA_DIR}` の `NAS100_H1_2014.csv` 〜 `NAS100_H1_2026.csv`",
        f"- H1行数: {len(raw):,}",
        f"- H4行数: {len(h4):,}",
        f"- 期間: {raw.index.min()} 〜 {raw.index.max()}",
        f"- コスト仮定: spread={BASE_COST['spread_price']}pt, slippage={BASE_COST['slip_price']}pt",
        "- Research: 2015-2024 / OOS: 2025-2026",
        "",
        "## Summary",
        "",
        markdown_table(
            summary[
                [
                    "case",
                    "all_trades",
                    "all_win_rate",
                    "all_total_r",
                    "all_avg_r",
                    "all_pf",
                    "all_max_dd_r",
                    "oos_trades",
                    "oos_total_r",
                    "oos_avg_r",
                    "oos_pf",
                    "notes",
                ]
            ],
            20,
        ),
        "",
        "## Pine default operation breakdown",
        "",
        markdown_table(op_table, 10),
        "",
        "## Pine default by year",
        "",
        markdown_table(by_year, 20),
        "",
        "## Interpretation",
        "",
        "- US100/NAS100は値幅が大きいため、H4 T5の形は出るが、通貨ペアとは別枠で評価する必要がある。",
        "- `03 Pine default operation weighted` が、通常ロット/半ロット運用まで含めた実戦寄りの見方。",
        "- OOSの取引数が少ない場合は、結論を急がずフォワード観察対象にする。",
        "- 実コストはブローカー差が大きいため、x2/x3ストレスでも崩れないかを必ず確認する。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(
        summary[
            [
                "case",
                "all_trades",
                "all_total_r",
                "all_avg_r",
                "all_pf",
                "all_max_dd_r",
                "oos_trades",
                "oos_total_r",
                "oos_avg_r",
                "oos_pf",
            ]
        ].to_string(index=False)
    )
    print(op_table.to_string(index=False))


if __name__ == "__main__":
    main()

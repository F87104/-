#!/usr/bin/env python3
"""
USDJPY M1 import and timeframe test.

Purpose:
- Load USDJPY 1-minute CSV files copied into data/raw/usdjpy_m1.
- Resample them into multiple timeframes.
- Run the existing Synapse entry-point v1 logic on each timeframe.

This is an import/pipeline test first.  It intentionally keeps the same
signal definition used in run_synapse_entry_point_v1.py so the only thing
being changed is the source timeframe.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "usdjpy_m1"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "usdjpy_timeframes"
OUT_DIR = THIS_DIR / "results_usdjpy_m1_timeframes_2026_05_24"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(THIS_DIR))

from run_synapse_entry_point_v1 import (  # noqa: E402
    MIN_SWING_ATR,
    OOS_START,
    PIVOT_WIDTH,
    START,
    add_indicators,
    build_confirmed_pivots,
    diagnostics,
    direction_cost_r,
    holiday_market,
    markdown_table,
    pivots_until,
    profit_factor,
    signal_from_pivots,
    summarize,
)


SYMBOL = "USDJPY"
TIMEFRAMES = {
    "M5": "5min",
    "M15": "15min",
    "M30": "30min",
    "H1": "1h",
    "H2": "2h",
    "H4": "4h",
    "D1": "1D",
}
TF_HOURS = {
    "M5": 5 / 60,
    "M15": 15 / 60,
    "M30": 30 / 60,
    "H1": 1,
    "H2": 2,
    "H4": 4,
    "D1": 24,
}
MAX_HOLD_HOURS = 96


def load_m1_csvs(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_csv(path)
        df.columns = [c.strip().strip("<>").lower() for c in df.columns]
        required = {"dtyyyymmdd", "time", "open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")

        date_part = df["dtyyyymmdd"].astype(str).str.replace(r"\.0$", "", regex=True)
        time_part = df["time"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
        dt = pd.to_datetime(date_part + time_part, format="%Y%m%d%H%M", errors="coerce")
        out = pd.DataFrame(
            {
                "open": pd.to_numeric(df["open"], errors="coerce").to_numpy(),
                "high": pd.to_numeric(df["high"], errors="coerce").to_numpy(),
                "low": pd.to_numeric(df["low"], errors="coerce").to_numpy(),
                "close": pd.to_numeric(df["close"], errors="coerce").to_numpy(),
                "volume": pd.to_numeric(df.get("vol", 0), errors="coerce").fillna(0).to_numpy(),
            },
            index=dt,
        )
        out = out[~out.index.isna()]
        frames.append(out)

    combined = pd.concat(frames).sort_index()
    combined = combined[~combined.index.duplicated(keep="last")]
    return combined.dropna(subset=["open", "high", "low", "close"])


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    out = df.resample(rule, label="right", closed="right").agg(agg)
    return out.dropna(subset=["open", "high", "low", "close"])


def max_hold_bars(tf: str) -> int:
    return max(1, int(round(MAX_HOLD_HOURS / TF_HOURS[tf])))


def simulate_trade_tf(df: pd.DataFrame, sig: dict, signal_i: int, max_hold: int) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None

    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    target = float(sig["target_half"])
    if direction == "long":
        risk = entry - stop
        reward = target - entry
        if risk <= 0 or reward <= 0 or reward / risk < 0.80:
            return None
    else:
        risk = stop - entry
        reward = entry - target
        if risk <= 0 or reward <= 0 or reward / risk < 0.80:
            return None

    exit_i = min(len(df) - 1, entry_i + max_hold)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "time_exit"

    for j in range(entry_i, min(len(df), entry_i + max_hold + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = hi >= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break

    r_clean, r_after = direction_cost_r(SYMBOL, direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "planned_rr": reward / risk,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after,
        "weighted_r_after_cost": r_after * float(sig["risk_weight"]),
    }


def run_timeframe(df: pd.DataFrame, tf: str, entry_mode: str) -> pd.DataFrame:
    work = add_indicators(df)
    pivots = build_confirmed_pivots(work, PIVOT_WIDTH, MIN_SWING_ATR)
    active = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    max_hold = max_hold_bars(tf)

    for i in range(2, len(work) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = work.index[i]
        if ts < START or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue
        sig = signal_from_pivots(work, i, active, entry_mode)
        if sig is None:
            continue
        trade = simulate_trade_tf(work, sig, i, max_hold)
        if trade is None:
            continue
        rows.append({"symbol": SYMBOL, "timeframe": tf, "signal_time": ts, **sig, **trade})
        in_pos_until = int(work.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def write_report(coverage: pd.DataFrame, trades: pd.DataFrame, summary: pd.DataFrame) -> None:
    lines = [
        "# USDJPY M1 インポート時間足テスト",
        "",
        "## 目的",
        "",
        "- Google Drive由来のUSDJPY 1分足CSVを読み込めるか確認",
        "- M1から複数時間足へリサンプル",
        "- 既存のSynapse Entry Point v1を、時間足だけ変えて試す",
        "",
        "## データ範囲",
        "",
        markdown_table(coverage, 20),
        "",
        "## 時間足別サマリー",
        "",
        markdown_table(summary, 80),
        "",
        "## 注意",
        "",
        "現時点では取り込み済みCSVだけのテストです。全期間CSVを同じフォルダへ追加すれば同じ処理で再集計できます。",
        "M1から生成した時間足なので、H1/H4/D1のOHLCは同じ元データから一貫して作られています。",
        "",
        "## 出力",
        "",
        "- `trades.csv`",
        "- `summary_by_timeframe_mode.csv`",
        "- `summary_by_timeframe.csv`",
        "- `data_coverage.csv`",
        f"- リサンプル済みCSV: `{PROCESSED_DIR}`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    m1 = load_m1_csvs(RAW_DIR)
    coverage_rows = [
        {
            "source": "M1 combined",
            "rows": len(m1),
            "first": m1.index.min(),
            "last": m1.index.max(),
        }
    ]
    all_trades: list[pd.DataFrame] = []

    for tf, rule in TIMEFRAMES.items():
        tf_df = resample_ohlc(m1, rule)
        tf_df.to_csv(PROCESSED_DIR / f"USDJPY_{tf}_from_m1.csv", index_label="datetime")
        coverage_rows.append(
            {
                "source": tf,
                "rows": len(tf_df),
                "first": tf_df.index.min(),
                "last": tf_df.index.max(),
            }
        )
        for entry_mode in ["B_confirmed", "A_early"]:
            trades = run_timeframe(tf_df, tf, entry_mode)
            if not trades.empty:
                all_trades.append(trades)

    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if all_trades:
        trades_all = pd.concat(all_trades, ignore_index=True).sort_values(["entry_time", "timeframe", "entry_mode"])
        for col in ["signal_time", "entry_time", "exit_time"]:
            trades_all[col] = pd.to_datetime(trades_all[col])
        trades_all["sample"] = np.where(trades_all["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_before_2025")
        trades_all.to_csv(OUT_DIR / "trades.csv", index=False)
        by_tf = summarize(trades_all, ["symbol", "timeframe"])
        by_tf_mode = summarize(trades_all, ["symbol", "timeframe", "entry_mode"])
        by_tf.to_csv(OUT_DIR / "summary_by_timeframe.csv", index=False)
        by_tf_mode.to_csv(OUT_DIR / "summary_by_timeframe_mode.csv", index=False)
        diagnostics(trades_all).to_csv(OUT_DIR / "diagnostics.csv", index=False)
        summary = by_tf_mode
    else:
        trades_all = pd.DataFrame()
        summary = pd.DataFrame()
        (OUT_DIR / "trades.csv").write_text("", encoding="utf-8")
        (OUT_DIR / "summary_by_timeframe.csv").write_text("", encoding="utf-8")
        (OUT_DIR / "summary_by_timeframe_mode.csv").write_text("", encoding="utf-8")

    write_report(coverage, trades_all, summary)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Coverage")
    print(coverage.to_string(index=False))
    print("\nSummary")
    print(summary.to_string(index=False) if not summary.empty else "No trades")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Python parity check for stumble_chase_suppression_experiment_v0_1.pine (v0.1.1).

Compare filter OFF vs ON (all filters) vs F1-only on GBPJPY 1H TradingView/OANDA CSV.
This is a research approximation; final numbers should still be checked in TV Strategy Tester.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from load_tv_oanda_csv import default_gbpjpy_h1_path, load_tv_oanda_csv


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = THIS_DIR / "results_gbpjpy_h1_tv_validation"


@dataclass(frozen=True)
class FilterConfig:
    filter_on: bool = True
    use_f1: bool = True
    use_f2: bool = True
    use_f3: bool = True


@dataclass
class Trade:
    direction: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    pnl: float
    exit_reason: str


def profit_factor(pnl: pd.Series) -> float:
    wins = float(pnl[pnl > 0].sum())
    losses = float(pnl[pnl <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    equity = pnl.cumsum()
    peak = equity.cummax()
    return float((peak - equity).max())


def add_signals(df: pd.DataFrame, cfg: FilterConfig) -> pd.DataFrame:
    out = df.copy()
    out["body"] = (out["close"] - out["open"]).abs()
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr"] = tr.rolling(14, min_periods=14).mean()
    out["ema"] = out["close"].ewm(span=50, adjust=False).mean()

    nearest_yen = out["close"].round()
    nearest_half = (out["close"] * 2.0).round() / 2.0
    dist_yen = (out["close"] - nearest_yen).abs()
    dist_half = (out["close"] - nearest_half).abs()
    out["near_round"] = (dist_yen <= 0.25) | (dist_half <= 0.15)

    out["hi_ext"] = out["high"].rolling(20, min_periods=20).max()
    out["lo_ext"] = out["low"].rolling(20, min_periods=20).min()
    out["near_high"] = out["hi_ext"] - out["close"] <= out["atr"] * 0.80
    out["near_low"] = out["close"] - out["lo_ext"] <= out["atr"] * 0.80

    out["brk_hi"] = out["high"].shift(1).rolling(12, min_periods=12).max()
    out["brk_lo"] = out["low"].shift(1).rolling(12, min_periods=12).min()

    cross_up = (out["close"] > out["brk_hi"]) & (out["close"].shift(1) <= out["brk_hi"].shift(1))
    cross_dn = (out["close"] < out["brk_lo"]) & (out["close"].shift(1) >= out["brk_lo"].shift(1))
    out["long_raw"] = (out["close"] > out["ema"]) & cross_up
    out["short_raw"] = (out["close"] < out["ema"]) & cross_dn

    big_bull = (out["close"] > out["open"]) & (out["body"] >= out["atr"] * 1.10)
    big_bear = (out["close"] < out["open"]) & (out["body"] >= out["atr"] * 1.10)
    impulse_bull = big_bull.shift(1).fillna(False)
    for lag in range(2, 3):
        impulse_bull = impulse_bull | big_bull.shift(lag).fillna(False)
    impulse_bear = big_bear.shift(1).fillna(False)
    for lag in range(2, 3):
        impulse_bear = impulse_bear | big_bear.shift(lag).fillna(False)

    out["first_break_long"] = out["long_raw"] & (out["close"].shift(1) <= out["brk_hi"])
    out["first_break_short"] = out["short_raw"] & (out["close"].shift(1) >= out["brk_lo"])

    f1_block_long = cfg.use_f1 & out["near_round"] & out["near_high"] & (out["close"] > out["open"]) & out["long_raw"]
    f1_block_short = cfg.use_f1 & out["near_round"] & out["near_low"] & (out["close"] < out["open"]) & out["short_raw"]
    f2_block_long = cfg.use_f2 & impulse_bull & out["long_raw"]
    f2_block_short = cfg.use_f2 & impulse_bear & out["short_raw"]
    f3_block_long = (
        cfg.use_f3
        & out["long_raw"]
        & ~out["first_break_long"]
        & (out["close"].shift(1) > out["brk_hi"].shift(1))
        & out["near_high"]
    )
    f3_block_short = (
        cfg.use_f3
        & out["short_raw"]
        & ~out["first_break_short"]
        & (out["close"].shift(1) < out["brk_lo"].shift(1))
        & out["near_low"]
    )

    block_long = cfg.filter_on & out["long_raw"] & (f1_block_long | f2_block_long | f3_block_long)
    block_short = cfg.filter_on & out["short_raw"] & (f1_block_short | f2_block_short | f3_block_short)
    out["long_sig"] = out["long_raw"] & ~block_long
    out["short_sig"] = out["short_raw"] & ~block_short
    return out


def run_backtest(df: pd.DataFrame, cfg: FilterConfig) -> list[Trade]:
    sig = add_signals(df, cfg)
    trades: list[Trade] = []
    position = 0
    entry_price = 0.0
    entry_time = pd.Timestamp.min
    stop = 0.0
    target = 0.0

    for row in sig.itertuples(index=False):
        if pd.isna(row.atr):
            continue

        if position != 0:
            if position > 0:
                stop_hit = row.low <= stop
                target_hit = row.high >= target
                if stop_hit or target_hit:
                    if stop_hit and target_hit:
                        exit_price = stop
                        reason = "stop"
                    elif stop_hit:
                        exit_price = stop
                        reason = "stop"
                    else:
                        exit_price = target
                        reason = "target"
                    trades.append(
                        Trade("long", entry_time, row.datetime, entry_price, exit_price, exit_price - entry_price, reason)
                    )
                    position = 0
            else:
                stop_hit = row.high >= stop
                target_hit = row.low <= target
                if stop_hit or target_hit:
                    if stop_hit and target_hit:
                        exit_price = stop
                        reason = "stop"
                    elif stop_hit:
                        exit_price = stop
                        reason = "stop"
                    else:
                        exit_price = target
                        reason = "target"
                    trades.append(
                        Trade(
                            "short",
                            entry_time,
                            row.datetime,
                            entry_price,
                            exit_price,
                            entry_price - exit_price,
                            reason,
                        )
                    )
                    position = 0

        if row.long_sig and position <= 0:
            if position < 0 and trades:
                last = trades[-1]
                if last.exit_time == row.datetime:
                    pass
            position = 1
            entry_price = float(row.close)
            entry_time = row.datetime
            stop = entry_price - row.atr * 1.5
            target = entry_price + row.atr * 2.5
        elif row.short_sig and position >= 0:
            position = -1
            entry_price = float(row.close)
            entry_time = row.datetime
            stop = entry_price + row.atr * 1.5
            target = entry_price - row.atr * 2.5

    return trades


def summarize_case(name: str, trades: list[Trade]) -> dict:
    if not trades:
        return {
            "case": name,
            "trades": 0,
            "net_pnl": 0.0,
            "pf": math.nan,
            "max_dd": 0.0,
            "win_rate": math.nan,
        }
    pnl = pd.Series([t.pnl for t in trades], dtype=float)
    return {
        "case": name,
        "trades": len(trades),
        "net_pnl": round(float(pnl.sum()), 2),
        "pf": round(profit_factor(pnl), 3),
        "max_dd": round(max_drawdown(pnl), 2),
        "win_rate": round(float((pnl > 0).mean()) * 100.0, 2),
    }


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join([header, sep, *body])


def main() -> None:
    parser = argparse.ArgumentParser(description="GBPJPY 1H F1 filter validation (Python/TV parity)")
    parser.add_argument("--csv", type=Path, default=None, help="TradingView/OANDA OHLC CSV path")
    parser.add_argument("--start", default="2015-01-01", help="Inclusive start date")
    parser.add_argument("--end", default=None, help="Inclusive end date")
    args = parser.parse_args()

    csv_path = args.csv or default_gbpjpy_h1_path(REPO_ROOT)
    if not csv_path.exists():
        raise SystemExit(
            "CSV not found.\n"
            f"Expected: {csv_path}\n"
            "Copy your TradingView export to:\n"
            f"  {REPO_ROOT / 'data' / 'raw' / 'tv_oanda' / 'GBPJPY_H1.csv'}\n"
            "Example source file:\n"
            "  /Users/asamifujita/Downloads/OANDA_GBPJPY, 60_87a90.csv"
        )

    df = load_tv_oanda_csv(csv_path)
    df = df[df["datetime"] >= pd.Timestamp(args.start)]
    if args.end:
        df = df[df["datetime"] <= pd.Timestamp(args.end)]

    cases = [
        ("filter_off", FilterConfig(filter_on=False)),
        ("filter_on_all", FilterConfig(filter_on=True, use_f1=True, use_f2=True, use_f3=True)),
        ("filter_on_f1_only", FilterConfig(filter_on=True, use_f1=True, use_f2=False, use_f3=False)),
        ("stumble_2024_10", FilterConfig(filter_on=True, use_f1=True, use_f2=False, use_f3=False)),
    ]

    summaries: list[dict] = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, cfg in cases:
        sample = df
        if name == "stumble_2024_10":
            sample = df[(df["datetime"] >= "2024-10-01") & (df["datetime"] < "2024-11-01")]
        trades = run_backtest(sample, cfg)
        summaries.append(summarize_case(name, trades))
        trade_rows = pd.DataFrame([t.__dict__ for t in trades])
        trade_rows.to_csv(OUT_DIR / f"{name}_trades.csv", index=False)

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(OUT_DIR / "summary.csv", index=False)

    report = [
        "# GBPJPY 1H F1 validation (Python)",
        "",
        f"- Source CSV: `{csv_path}`",
        f"- Bars: {len(df):,}",
        f"- Range: {df['datetime'].min()} → {df['datetime'].max()}",
        "",
        "## Summary",
        "",
        markdown_table(summaries, ["case", "trades", "net_pnl", "pf", "max_dd", "win_rate"]),
        "",
        "## TV reference (GBPJPY 1H, all filters ON/OFF, full period)",
        "",
        "| case | trades | net_pnl | pf | max_dd |",
        "| --- | ---: | ---: | ---: | ---: |",
        "| filter_off | 1279 | -34.61 | 0.906 | 42.85 |",
        "| filter_on_all | 473 | -25.51 | 0.78 | 30.56 |",
        "",
        "Compare `filter_off` / `filter_on_all` counts first. Then adopt `filter_on_f1_only` for v2.x.",
    ]
    (OUT_DIR / "report.md").write_text("\n".join(report), encoding="utf-8")

    print(summary_df.to_string(index=False))
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

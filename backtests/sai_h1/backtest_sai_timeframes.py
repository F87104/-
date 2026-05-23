#!/usr/bin/env python3
"""
H1/H4/D1 comparison runner for the Sai-style mechanical backtest.

The original backtester is an H1 approximation. This runner keeps the
underlying signal logic intact, resamples the same H1 source data to higher
timeframes, and scales broad lookback windows so the comparison is based on
roughly similar calendar durations.
"""

from __future__ import annotations

import argparse
import dataclasses
import math
from pathlib import Path
from typing import Iterable

import pandas as pd

from backtest_sai_h1 import (
    Config,
    available_symbols,
    backtest_symbol,
    normalize_symbol,
)


TIMEFRAME_RULES = {
    "M5": None,
    "M15": None,
    "H1": None,
    "H4": "4h",
    "D1": "1D",
}

TIMEFRAME_FACTORS = {
    "M5": 1 / 12,
    "M15": 1 / 4,
    "H1": 1,
    "H4": 4,
    "D1": 24,
}

SOURCE_TIMEFRAME = {
    "M5": "M5",
    "M15": "M15",
    "H1": "H1",
    "H4": "H1",
    "D1": "H1",
}

TIMEFRAME_FILE_TOKENS = {
    "M5": ("M5", "5M", "5MIN", "5_MIN", "5分"),
    "M15": ("M15", "15M", "15MIN", "15_MIN", "15分"),
    "H1": ("H1", "1H", "60MIN", "60_MIN", "1時間"),
}

BROAD_WINDOW_FIELDS = (
    "medium_lookback",
    "short_lookback",
    "recent_lookback",
    "momentum_lookback",
    "key_level_lookback",
    "range_min_bars",
    "second_break_lookback",
    "vshape_lookback",
    "consolidation_bars",
    "counter_move_lookback",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Sai-style backtest results across H1/H4/D1."
    )
    parser.add_argument("--data-root", type=Path, default=Path("F87104_test"))
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("backtests/sai_h1/timeframe_comparison_2015_2024"),
    )
    parser.add_argument("--start", type=str, default="2015-01-01")
    parser.add_argument("--end", type=str, default="2024-12-31")
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=["H1", "H4", "D1"],
        choices=sorted(TIMEFRAME_RULES.keys()),
    )
    parser.add_argument(
        "--include-usdjpy",
        action="store_true",
        help="Include USDJPY. Default follows Sai notes and skips USDJPY.",
    )
    parser.add_argument(
        "--include-holidays",
        action="store_true",
        help="Include Dec 15-Jan 10. Default skips thin holiday market.",
    )
    parser.add_argument(
        "--cost-mult",
        type=float,
        default=1.0,
        help="Multiplier for built-in spread/slippage cost table.",
    )
    return parser.parse_args()


def read_symbol_timeframe_csvs(data_root: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    tokens = TIMEFRAME_FILE_TOKENS[timeframe]
    files = []
    for file in data_root.rglob("*.csv"):
        name = file.name.upper()
        if not any(token.upper() in name for token in tokens):
            continue
        path_text = str(file).upper()
        if symbol == "GBPJPY":
            if "GBPJPY" not in path_text and "GBYJPY" not in path_text and "GBY JPY" not in path_text:
                continue
        elif symbol == "XAGUSD":
            if "XAGUSD" not in path_text and "SILVER" not in path_text:
                continue
        elif symbol not in path_text:
            continue
        files.append(file)

    frames: list[pd.DataFrame] = []
    for file in sorted(files):
        df = pd.read_csv(file)
        df.columns = [c.strip("<>").lower() for c in df.columns]
        if "ticker" not in df.columns:
            continue
        ticker = normalize_symbol(str(df["ticker"].iloc[0]))
        if symbol == "XAGUSD":
            ticker_ok = ticker in {"XAGUSD", "SILVER"}
        elif symbol == "GBPJPY":
            ticker_ok = ticker in {"GBPJPY", "GBYJPY"}
        else:
            ticker_ok = ticker == symbol
        if not ticker_ok:
            continue
        time_text = df["time"].astype(str).str.zfill(4)
        dt_text = df["dtyyyymmdd"].astype(str) + time_text
        df["datetime"] = pd.to_datetime(dt_text, format="%Y%m%d%H%M", errors="coerce")
        df = df.rename(
            columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
            }
        )
        frames.append(df[["datetime", "open", "high", "low", "close", "volume"]])

    if not frames:
        raise FileNotFoundError(f"No {timeframe} CSV files found for {symbol} under {data_root}")

    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["datetime"])
    out = out.drop_duplicates(subset=["datetime"], keep="last")
    out = out.sort_values("datetime").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"])
    return (
        out.groupby("datetime", as_index=False)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .sort_values("datetime")
        .reset_index(drop=True)
    )


def scaled_int(value: int, factor: float, minimum: int = 1) -> int:
    return max(minimum, int(math.ceil(value / factor)))


def config_for_timeframe(base: Config, timeframe: str) -> Config:
    """Return a config adjusted for the target timeframe.

    Broad context windows are scaled by calendar duration. Pattern windows such
    as stagnation are also scaled but clamped to at least two candles so a
    higher-timeframe "停滞" still means multiple bars.
    """
    factor = TIMEFRAME_FACTORS[timeframe]
    cfg = dataclasses.replace(base)

    if factor == 1:
        return cfg

    for field_name in BROAD_WINDOW_FIELDS:
        current = getattr(cfg, field_name)
        minimum = 1 if field_name == "swing_pivot_width" else 2
        setattr(cfg, field_name, scaled_int(current, factor, minimum=minimum))

    cfg.stagnation_min_bars = scaled_int(base.stagnation_min_bars, factor, minimum=2)
    cfg.stagnation_max_bars = max(
        cfg.stagnation_min_bars + 1,
        scaled_int(base.stagnation_max_bars, factor, minimum=3),
    )
    cfg.swing_pivot_width = scaled_int(base.swing_pivot_width, factor, minimum=1)
    return cfg


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    rule = TIMEFRAME_RULES[timeframe]
    if rule is None:
        return df.copy()

    resampled = (
        df.set_index("datetime")
        .resample(rule, label="left", closed="left")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return resampled


def max_losing_streak(values: Iterable[float]) -> int:
    current = 0
    longest = 0
    for value in values:
        if value <= 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def summarize_extended(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()

    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        total_r = float(group["r"].sum())
        trades_count = int(len(group))
        wins = int((group["r"] > 0).sum())
        losses = int((group["r"] <= 0).sum())
        avg_r = float(group["r"].mean()) if trades_count else 0.0
        median_r = float(group["r"].median()) if trades_count else 0.0
        gross_win = float(group.loc[group["r"] > 0, "r"].sum())
        gross_loss = abs(float(group.loc[group["r"] <= 0, "r"].sum()))
        profit_factor = gross_win / gross_loss if gross_loss > 0 else math.nan
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": trades_count,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / trades_count * 100 if trades_count else 0.0,
                "total_r": total_r,
                "avg_r": avg_r,
                "median_r": median_r,
                "profit_factor": profit_factor,
                "max_losing_streak": max_losing_streak(group["r"].tolist()),
                "avg_hold_days": float(group["hold_days"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("total_r", ascending=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    view = view.astype(str)
    headers = [str(col).replace("|", "\\|") for col in view.columns]
    rows = [
        [str(value).replace("|", "\\|") for value in row]
        for row in view.itertuples(index=False, name=None)
    ]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    header_line = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
    sep_line = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    row_lines = [
        "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line, *row_lines])


def write_report(
    out_dir: Path,
    trades: pd.DataFrame,
    overall: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_method: pd.DataFrame,
    yearly: pd.DataFrame,
    monthly: pd.DataFrame,
    symbols: list[str],
    missing_data: list[tuple[str, str, str]],
    args: argparse.Namespace,
) -> None:
    best_total = overall.sort_values("total_r", ascending=False).head(1)
    best_wr = overall[overall["trades"] >= 20].sort_values("win_rate", ascending=False).head(1)
    best_pf = overall[overall["trades"] >= 20].sort_values("profit_factor", ascending=False).head(1)

    lines = [
        "# Sai Timeframe Comparison",
        "",
        f"- Data root: `{args.data_root}`",
        f"- Period: `{args.start}` to `{args.end}`",
        f"- Timeframes: `{', '.join(args.timeframes)}`",
        f"- Symbols: `{', '.join(symbols)}`",
        f"- USDJPY: `{'included' if args.include_usdjpy else 'skipped'}`",
        f"- Holiday market Dec 15-Jan 10: `{'included' if args.include_holidays else 'skipped'}`",
        f"- Cost multiplier: `{args.cost_mult}`",
        "",
        "## Method",
        "",
        "H4/D1 are generated from the same H1 OHLC data. Broad lookback windows are scaled",
        "by approximate calendar duration. Stagnation windows are clamped to at least two",
        "candles, so higher-timeframe stagnation still requires multiple bars.",
        "",
    ]

    if missing_data:
        lines.extend(
            [
                "## Missing Data",
                "",
                "The following timeframe/symbol combinations were skipped because matching CSV data was not found.",
                "",
                "| timeframe | symbol | source_timeframe |",
                "| --- | --- | --- |",
            ]
        )
        for timeframe, symbol, source_tf in missing_data:
            lines.append(f"| {timeframe} | {symbol} | {source_tf} |")
        lines.append("")

    lines.extend(
        [
            "## Top-Level Result",
            "",
            markdown_table(overall),
            "",
        ]
    )

    if not best_total.empty:
        r = best_total.iloc[0]
        lines.append(
            f"**Total R best:** `{r['timeframe']}` with `{r['total_r']:.2f}R`, "
            f"`{r['win_rate']:.2f}%` win rate, `{r['trades']}` trades."
        )
    if not best_wr.empty:
        r = best_wr.iloc[0]
        lines.append(
            f"**Win rate best (20+ trades):** `{r['timeframe']}` with `{r['win_rate']:.2f}%`."
        )
    if not best_pf.empty:
        r = best_pf.iloc[0]
        pf = "N/A" if pd.isna(r["profit_factor"]) else f"{r['profit_factor']:.2f}"
        lines.append(f"**Profit factor best (20+ trades):** `{r['timeframe']}` with `{pf}`.")

    lines.extend(
        [
            "",
            "## Timeframe x Symbol",
            "",
            markdown_table(by_symbol, max_rows=60),
            "",
            "## Timeframe x Method",
            "",
            markdown_table(by_method, max_rows=80),
            "",
            "## Yearly",
            "",
            markdown_table(yearly, max_rows=80),
            "",
            "## Monthly",
            "",
            markdown_table(monthly, max_rows=120),
            "",
            "## Output Files",
            "",
            "- `trades_all.csv`: all trades",
            "- `summary_by_timeframe.csv`: timeframe totals",
            "- `summary_by_timeframe_symbol.csv`: symbol breakdown",
            "- `summary_by_timeframe_method.csv`: method breakdown",
            "- `summary_by_timeframe_year.csv`: yearly breakdown",
            "- `summary_by_timeframe_month.csv`: monthly breakdown",
        ]
    )
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    symbols = available_symbols(args.data_root)
    if not args.include_usdjpy:
        symbols = [symbol for symbol in symbols if normalize_symbol(symbol) != "USDJPY"]

    base_cfg = Config(
        start=args.start,
        end=args.end,
        skip_usdjpy=not args.include_usdjpy,
        skip_holiday_market=not args.include_holidays,
    )

    all_trades = []
    for timeframe in args.timeframes:
        cfg = config_for_timeframe(base_cfg, timeframe)
        for symbol in symbols:
            raw = read_symbol_csvs(args.data_root, symbol)
            data = resample_ohlc(raw, timeframe)
            trades = backtest_symbol(data, symbol, cfg)
            if not trades.empty:
                tf_df = trades.copy()
                tf_df.insert(0, "timeframe", timeframe)
                all_trades.append(tf_df)

    if all_trades:
        trades_df = pd.concat(all_trades, ignore_index=True)
        trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"])
        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])
        trades_df = trades_df.sort_values(["timeframe", "entry_time", "symbol"]).reset_index(drop=True)
    else:
        trades_df = pd.DataFrame()

    if trades_df.empty:
        write_csv(trades_df, args.out_dir / "trades_all.csv")
        (args.out_dir / "report.md").write_text("# Sai Timeframe Comparison\n\nNo trades.", encoding="utf-8")
        print(f"No trades. Report: {args.out_dir / 'report.md'}")
        return

    trades_df["year"] = trades_df["entry_time"].dt.year.astype(str)
    trades_df["month"] = trades_df["entry_time"].dt.to_period("M").astype(str)

    overall = summarize_extended(trades_df, ["timeframe"])
    by_symbol = summarize_extended(trades_df, ["timeframe", "symbol"])
    by_method = summarize_extended(trades_df, ["timeframe", "method"])
    yearly = summarize_extended(trades_df, ["timeframe", "year"])
    monthly = summarize_extended(trades_df, ["timeframe", "month"])

    write_csv(trades_df, args.out_dir / "trades_all.csv")
    write_csv(overall, args.out_dir / "summary_by_timeframe.csv")
    write_csv(by_symbol, args.out_dir / "summary_by_timeframe_symbol.csv")
    write_csv(by_method, args.out_dir / "summary_by_timeframe_method.csv")
    write_csv(yearly, args.out_dir / "summary_by_timeframe_year.csv")
    write_csv(monthly, args.out_dir / "summary_by_timeframe_month.csv")

    write_report(
        args.out_dir,
        trades_df,
        overall,
        by_symbol,
        by_method,
        yearly,
        monthly,
        symbols,
        args,
    )

    print(f"Report: {args.out_dir / 'report.md'}")
    print(overall.to_string(index=False))


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
Step 0 for H4 Double V / D1 V Context research:
validate TradingView-exported OHLC before Strategy Tester parity work.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from load_tv_ohlc import default_h4_path, infer_timeframe_minutes, load_tv_ohlc


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = THIS_DIR / "results_tv_data_coverage"

# Same universe as production ensemble (AUDJPY optional for some studies)
DEFAULT_SYMBOLS = ["GBPJPY", "USDJPY", "EURJPY", "CHFJPY", "AUDJPY", "XAUUSD"]
RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")


def discover_csv(symbol: str, csv_dir: Path | None, explicit: Path | None) -> Path | None:
    if explicit and explicit.exists():
        return explicit
    if csv_dir:
        patterns = [
            f"*{symbol}*240*.csv",
            f"*{symbol}*H4*.csv",
            f"OANDA_{symbol}*.csv",
            f"FX_{symbol}*.csv",
        ]
        for pattern in patterns:
            matches = sorted(csv_dir.glob(pattern))
            if matches:
                return matches[0]
    default = default_h4_path(REPO_ROOT, symbol)
    return default if default.exists() else None


def coverage_row(symbol: str, path: Path | None) -> dict:
    if path is None or not path.exists():
        return {
            "symbol": symbol,
            "status": "missing",
            "path": "",
            "rows": 0,
            "start": "",
            "end": "",
            "median_minutes": "",
            "bars_2015_2026": 0,
        }

    df = load_tv_ohlc(path)
    sample = df[(df["datetime"] >= RUN_START) & (df["datetime"] <= RUN_END)]
    minutes = infer_timeframe_minutes(df)
    status = "ok"
    if minutes is not None and abs(minutes - 240) > 30:
        status = f"warn_tf_{int(minutes)}m"

    return {
        "symbol": symbol,
        "status": status,
        "path": str(path),
        "rows": len(df),
        "start": str(df["datetime"].min()),
        "end": str(df["datetime"].max()),
        "median_minutes": round(minutes, 1) if minutes is not None else "",
        "bars_2015_2026": len(sample),
    }


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def main() -> None:
    parser = argparse.ArgumentParser(description="Check TradingView H4 OHLC coverage")
    parser.add_argument("--csv-dir", type=Path, default=REPO_ROOT / "data" / "raw" / "tv_oanda" / "h4")
    parser.add_argument("--csv", type=Path, default=None, help="Single CSV (with --symbol)")
    parser.add_argument("--symbol", default="GBPJPY")
    parser.add_argument("--symbols", nargs="*", default=DEFAULT_SYMBOLS)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    if args.csv:
        rows.append(coverage_row(args.symbol.upper(), args.csv))
    else:
        for symbol in args.symbols:
            path = discover_csv(symbol.upper(), args.csv_dir if args.csv_dir.exists() else None, None)
            rows.append(coverage_row(symbol.upper(), path))

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / "coverage.csv", index=False)

    missing = [r["symbol"] for r in rows if r["status"] == "missing"]
    report = [
        "# H4 Double V — TradingView OHLC coverage",
        "",
        f"- Checked: `{args.csv_dir}`",
        f"- Period filter for count: {RUN_START.date()} → {RUN_END.date()}",
        "",
        markdown_table(rows, ["symbol", "status", "rows", "bars_2015_2026", "median_minutes", "start", "end"]),
        "",
        "## Missing symbols" if missing else "## All requested symbols found",
    ]
    if missing:
        report.extend(
            [
                "",
                "Export from TradingView (OANDA, **H4**, same date range as Strategy Tester):",
                "",
                "```",
                "Chart → Export chart data → time,open,high,low,close",
                "```",
                "",
                "Place files under:",
                "",
                "```",
                "data/raw/tv_oanda/h4/GBPJPY_H4.csv",
                "data/raw/tv_oanda/h4/USDJPY_H4.csv",
                "...",
                "```",
                "",
                "Or upload to repo root as `OANDA_GBPJPY, 240_xxxx.csv` and rerun.",
            ]
        )
    else:
        report.append("")
        report.append("Next: run Strategy Tester on `d1_v_context_h4_strategy.pine` and save the trade list CSV.")

    (OUT_DIR / "report.md").write_text("\n".join(report), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"\nWrote: {OUT_DIR}")
    if missing:
        raise SystemExit(f"Missing TV CSV for: {', '.join(missing)}")


if __name__ == "__main__":
    main()

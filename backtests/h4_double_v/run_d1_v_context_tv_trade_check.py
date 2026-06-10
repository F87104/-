#!/usr/bin/env python3
"""
Check D1 V Context -> H4 Confirm Strategy against TradingView exports.

Inputs:
  1) TV H4 OHLC CSV (may include chart columns like `H4 Confirm Entry`)
  2) TV Strategy Tester trade-list CSV (Japanese export)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from load_tv_ohlc import load_tv_ohlc
from parse_tv_trades import parse_tv_trade_csv, summarize_trades


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = THIS_DIR / "results_d1_v_context_gbpjpy_tv"


def discover_trade_csv(repo_root: Path) -> Path | None:
    patterns = [
        "*D1_V_Context*GBPJPY*.csv",
        "*d1_v_context*gbpjpy*.csv",
        "*73de9*.csv",
    ]
    for pattern in patterns:
        matches = sorted(repo_root.glob(pattern))
        if matches:
            return matches[0]
    return None


def chart_confirm_entries(ohlc_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(ohlc_path)
    if "H4 Confirm Entry" not in raw.columns:
        return pd.DataFrame(columns=["entry_time", "close"])

    raw["entry_time"] = pd.to_datetime(raw["time"], unit="s", utc=True).dt.tz_convert("Asia/Tokyo").dt.tz_localize(None)
    out = raw[raw["H4 Confirm Entry"].fillna(0) != 0][["entry_time", "close", "Trade SL", "Trade TP"]].copy()
    return out.reset_index(drop=True)


def compare_entries(tv_trades: pd.DataFrame, chart_entries: pd.DataFrame, tolerance_hours: int = 4) -> pd.DataFrame:
    rows: list[dict] = []
    chart_times = chart_entries["entry_time"].tolist() if len(chart_entries) else []

    for _, trade in tv_trades.iterrows():
        entry = pd.Timestamp(trade["entry_time"])
        matched = None
        delta_h = None
        for ct in chart_times:
            diff = abs((entry - pd.Timestamp(ct)).total_seconds()) / 3600.0
            if diff <= tolerance_hours and (delta_h is None or diff < delta_h):
                matched = pd.Timestamp(ct)
                delta_h = diff
        rows.append(
            {
                "trade_no": trade["trade_no"],
                "tv_entry_time": entry,
                "chart_entry_time": matched,
                "delta_hours": round(delta_h, 2) if delta_h is not None else "",
                "match": matched is not None,
                "pnl": trade["pnl"],
            }
        )

    unmatched_chart = []
    matched_chart = {pd.Timestamp(r["chart_entry_time"]) for r in rows if r["match"]}
    for ct in chart_times:
        ct = pd.Timestamp(ct)
        if ct not in matched_chart:
            unmatched_chart.append(ct)

    comp = pd.DataFrame(rows)
    comp.attrs["unmatched_chart_entries"] = unmatched_chart
    return comp


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def main() -> None:
    parser = argparse.ArgumentParser(description="D1 V Context TV trade / OHLC check")
    parser.add_argument("--ohlc", type=Path, default=REPO_ROOT / "OANDA_GBPJPY, 240_7a999.csv")
    parser.add_argument("--trades", type=Path, default=None)
    parser.add_argument("--tolerance-hours", type=int, default=4)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.ohlc.exists():
        raise SystemExit(f"OHLC not found: {args.ohlc}")

    ohlc = load_tv_ohlc(args.ohlc)
    chart_entries = chart_confirm_entries(args.ohlc)
    chart_entries.to_csv(OUT_DIR / "chart_h4_confirm_entries.csv", index=False)

    trades_path = args.trades or discover_trade_csv(REPO_ROOT)
    report_lines = [
        "# D1 V Context -> H4 Confirm — TV check (GBPJPY)",
        "",
        f"- OHLC: `{args.ohlc}`",
        f"- OHLC bars: {len(ohlc):,} ({ohlc['datetime'].min()} → {ohlc['datetime'].max()})",
        f"- Chart `H4 Confirm Entry` bars: **{len(chart_entries)}**",
        "",
    ]

    if chart_entries.empty:
        report_lines.append("Chart export has no `H4 Confirm Entry` column.")
    else:
        report_lines.extend(
            [
                "## Chart export entries",
                "",
                markdown_table(
                    chart_entries.assign(entry_time=chart_entries["entry_time"].astype(str)).to_dict("records"),
                    ["entry_time", "close"],
                ),
                "",
            ]
        )

    if trades_path is None or not trades_path.exists():
        report_lines.extend(
            [
                "## Strategy Tester trade list",
                "",
                "**Not found in repo yet.**",
                "",
                "Latest Git upload commit was empty. Re-upload the file, e.g.:",
                "",
                "`D1_V_Context_GBPJPY_trades_73de9.csv`",
                "",
                "Then rerun:",
                "",
                "```bash",
                "python3 backtests/h4_double_v/run_d1_v_context_tv_trade_check.py \\",
                "  --trades D1_V_Context_GBPJPY_trades_73de9.csv",
                "```",
            ]
        )
        (OUT_DIR / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
        print("\n".join(report_lines))
        raise SystemExit("Trade-list CSV not found")

    tv_trades = parse_tv_trade_csv(trades_path)
    tv_trades.to_csv(OUT_DIR / "tv_trades_normalized.csv", index=False)
    summary = summarize_trades(tv_trades)
    comparison = compare_entries(tv_trades, chart_entries, tolerance_hours=args.tolerance_hours)
    comparison.to_csv(OUT_DIR / "entry_time_comparison.csv", index=False)

    matched = int(comparison["match"].sum()) if len(comparison) else 0
    report_lines.extend(
        [
            f"- Trades CSV: `{trades_path}`",
            "",
            "## Strategy Tester summary",
            "",
            markdown_table([summary], list(summary.keys())),
            "",
            "## Entry time parity (TV trades vs chart export)",
            "",
            f"- TV trades: **{len(tv_trades)}**",
            f"- Matched within {args.tolerance_hours}h: **{matched}/{len(tv_trades)}**",
            "",
        ]
    )

    unmatched_chart = comparison.attrs.get("unmatched_chart_entries", [])
    if unmatched_chart:
        report_lines.append(f"- Chart-only entries (no TV trade within {args.tolerance_hours}h): **{len(unmatched_chart)}**")

    if len(comparison):
        report_lines.extend(["", markdown_table(comparison.to_dict("records"), ["trade_no", "tv_entry_time", "chart_entry_time", "delta_hours", "match", "pnl"])])

    (OUT_DIR / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

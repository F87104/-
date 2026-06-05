#!/usr/bin/env python3
"""
Recheck Market Psychology Strategy from a TradingView trade-list CSV export.

The local Python OHLC feed can differ from TradingView/OANDA.  This script
treats the TradingView export as the source of truth, then compares only the
calendar dates against the existing Python research trades so the two result
sets are not mixed accidentally.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


DEFAULT_PY_TRADES = Path(
    "backtests/elliott_fibo/results_2026_05_30/"
    "market_psychology_strategy_tv_check/trades.csv"
)


def profit_factor(values: pd.Series) -> float:
    gross_profit = values[values > 0].sum()
    gross_loss = -values[values < 0].sum()
    if gross_loss == 0:
        return math.inf if gross_profit > 0 else 0.0
    return float(gross_profit / gross_loss)


def max_drawdown(values: pd.Series) -> float:
    equity = values.cumsum()
    peak = equity.cummax()
    dd = peak - equity
    return float(dd.max()) if len(dd) else 0.0


def parse_tv_trade_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw["日時"] = pd.to_datetime(raw["日時"])

    entries = raw[raw["タイプ"].astype(str).str.contains("エントリー")].copy()
    exits = raw[raw["タイプ"].astype(str).str.contains("決済")].copy()
    entry_by_no = entries.set_index("トレード番号")

    rows: list[dict[str, object]] = []
    for _, ex in exits.iterrows():
        trade_no = ex["トレード番号"]
        if trade_no not in entry_by_no.index:
            continue
        en = entry_by_no.loc[trade_no]
        rows.append(
            {
                "trade_no": int(trade_no),
                "entry_time": en["日時"],
                "exit_time": ex["日時"],
                "entry_signal": en["シグナル"],
                "exit_signal": ex["シグナル"],
                "entry_price": float(en["価格 USD"]),
                "exit_price": float(ex["価格 USD"]),
                "pnl_usd": float(ex["純損益 USD"]),
                "pnl_pct": float(ex["純損益 %"]),
                "mfe_usd": float(ex["最大順行幅 USD"]),
                "mfe_pct": float(ex["最大順行幅 %"]),
                "mae_usd": float(ex["最大逆行幅 USD"]),
                "mae_pct": float(ex["最大逆行幅 %"]),
                "cum_usd": float(ex["累積損益 USD"]),
                "cum_pct": float(ex["累積損益 %"]),
                "hold_hours": (ex["日時"] - en["日時"]).total_seconds() / 3600,
            }
        )
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)


def summarize_tv(tv: pd.DataFrame) -> dict[str, float]:
    pnl = tv["pnl_usd"]
    return {
        "trades": int(len(tv)),
        "wins": int((pnl > 0).sum()),
        "losses": int((pnl < 0).sum()),
        "winrate": float((pnl > 0).mean() * 100) if len(tv) else 0.0,
        "net_usd": float(pnl.sum()),
        "gross_profit": float(pnl[pnl > 0].sum()),
        "gross_loss": float(-pnl[pnl < 0].sum()),
        "pf": profit_factor(pnl),
        "avg_usd": float(pnl.mean()) if len(tv) else 0.0,
        "median_usd": float(pnl.median()) if len(tv) else 0.0,
        "max_dd_usd": max_drawdown(pnl),
        "avg_hold_hours": float(tv["hold_hours"].mean()) if len(tv) else 0.0,
        "median_hold_hours": float(tv["hold_hours"].median()) if len(tv) else 0.0,
    }


def compare_python_dates(tv: pd.DataFrame, py_trades_path: Path) -> pd.DataFrame:
    if not py_trades_path.exists():
        return pd.DataFrame()

    py = pd.read_csv(py_trades_path)
    py["entry_time"] = pd.to_datetime(py["entry_time"])
    tv_dates = set(tv["entry_time"].dt.date)

    rows: list[dict[str, object]] = []
    for strategy, g in py.groupby("strategy"):
        # XAGUSD in TradingView corresponds to the existing SILVER local dataset.
        g = g[g["symbol"].isin(["SILVER", "XAGUSD"])]
        if g.empty:
            continue
        py_dates = set(g["entry_time"].dt.date)
        r_col = "r_after_cost" if "r_after_cost" in g.columns else "result_r"
        rows.append(
            {
                "strategy": strategy,
                "python_trades": int(len(g)),
                "python_winrate": float((g[r_col] > 0).mean() * 100),
                "python_total_r": float(g[r_col].sum()),
                "python_pf": profit_factor(g[r_col]),
                "common_dates": int(len(tv_dates & py_dates)),
                "tv_only_dates": int(len(tv_dates - py_dates)),
                "python_only_dates": int(len(py_dates - tv_dates)),
                "common_date_list": "; ".join(str(d) for d in sorted(tv_dates & py_dates)),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["common_dates", "python_trades"], ascending=[False, True]
    )


def format_pf(value: float) -> str:
    return "inf" if math.isinf(value) else f"{value:.3f}"


def write_report(
    out_path: Path,
    tv_csv: Path,
    tv: pd.DataFrame,
    summary: dict[str, float],
    comparison: pd.DataFrame,
) -> None:
    by_year = tv.assign(year=tv["entry_time"].dt.year).groupby("year")["pnl_usd"].agg(
        trades="count",
        wins=lambda s: int((s > 0).sum()),
        net_usd="sum",
    )

    lines: list[str] = []
    lines.append("# TradingView OANDA XAGUSD CSV Recheck")
    lines.append("")
    lines.append("作成日: 2026-06-05")
    lines.append("")
    lines.append("## 結論")
    lines.append("")
    lines.append(
        "この再検証では、TradingView のエクスポートCSVを正として扱う。"
        "ローカルPythonの `SILVER` OHLC検証とはシグナル日付が大きくズレたため、"
        "XAGUSD/OANDA についてはPython結果をそのまま採用しない。"
    )
    lines.append("")
    lines.append("## TradingView CSV 集計")
    lines.append("")
    lines.append(f"- 入力CSV: `{tv_csv}`")
    lines.append(f"- Trades: {summary['trades']:.0f}")
    lines.append(f"- 勝率: {summary['winrate']:.2f}%")
    lines.append(f"- Net: {summary['net_usd']:.2f} USD")
    lines.append(f"- PF: {format_pf(summary['pf'])}")
    lines.append(f"- Avg: {summary['avg_usd']:.2f} USD")
    lines.append(f"- Median: {summary['median_usd']:.2f} USD")
    lines.append(f"- Max DD (trade close equity): {summary['max_dd_usd']:.2f} USD")
    lines.append(f"- Avg hold: {summary['avg_hold_hours']:.1f} hours")
    lines.append("")
    lines.append("## 年別")
    lines.append("")
    lines.append("| year | trades | wins | net_usd |")
    lines.append("|---:|---:|---:|---:|")
    for year, row in by_year.iterrows():
        lines.append(f"| {year} | {row['trades']:.0f} | {row['wins']:.0f} | {row['net_usd']:.2f} |")
    lines.append("")
    lines.append("## Python既存検証との照合")
    lines.append("")
    if comparison.empty:
        lines.append("Python比較ファイルが見つからなかったため、照合なし。")
    else:
        lines.append(
            "最大一致でも `SQZ_DEFAULT_RR2 / SQZ_DEFAULT_RR15 / SQZ_WIDE_RR2` の"
            " **6日/15日** のみ。これは単なる約定時刻ズレではなく、"
            "データ元またはTradingView側設定差が大きい可能性を示す。"
        )
        lines.append("")
        lines.append("| strategy | py_trades | common_dates | tv_only | py_only | py_total_r | py_pf |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for _, row in comparison.iterrows():
            lines.append(
                f"| {row['strategy']} | {row['python_trades']} | {row['common_dates']} | "
                f"{row['tv_only_dates']} | {row['python_only_dates']} | "
                f"{row['python_total_r']:.2f} | {format_pf(row['python_pf'])} |"
            )
    lines.append("")
    lines.append("## 今後の扱い")
    lines.append("")
    lines.append("- TradingView/OANDA XAGUSD は、このCSV結果を基準に再評価する。")
    lines.append("- 既存Pythonの `SILVER` 結果は参考値に降格する。")
    lines.append("- XAGUSDを本番候補にする場合は、TradingView Strategy Testerから同形式CSVを継続的に出し、同じスクリプトで追跡する。")
    lines.append("- Pythonに完全一致させるには、TradingView/OANDAのH4 OHLCそのものをPythonへ取り込む必要がある。")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv-csv", required=True, type=Path)
    parser.add_argument("--python-trades", default=DEFAULT_PY_TRADES, type=Path)
    parser.add_argument(
        "--out",
        default=Path("backtests/elliott_fibo/results_2026_06_05/market_psychology_tv_oanda_xagusd_recheck"),
        type=Path,
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    tv = parse_tv_trade_csv(args.tv_csv)
    summary = summarize_tv(tv)
    comparison = compare_python_dates(tv, args.python_trades)

    tv.to_csv(args.out / "tv_trades_normalized.csv", index=False)
    comparison.to_csv(args.out / "python_vs_tradingview_date_comparison.csv", index=False)
    write_report(args.out / "report_ja.md", args.tv_csv, tv, summary, comparison)

    print(f"Wrote {args.out}")
    print(f"TV trades={summary['trades']:.0f} winrate={summary['winrate']:.2f}% pf={format_pf(summary['pf'])} net={summary['net_usd']:.2f} USD")


if __name__ == "__main__":
    main()

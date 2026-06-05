#!/usr/bin/env python3
"""Step 0: Where does TrendBreak baseline R come from? (original research)"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRADES = REPO / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
OUT = REPO / "docs/research/original_tb_attribution_2026-06-01.csv"
OUT_MD = REPO / "docs/research/original_tb_attribution_2026-06-01.md"


def pf(series: pd.Series) -> float:
    w = series[series > 0].sum()
    l = -series[series <= 0].sum()
    return w / l if l > 0 else float("inf")


def main() -> None:
    df = pd.read_csv(TRADES)
    df = df[df["rule_name"].eq("baseline")].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["year"] = df["entry_time"].dt.year
    df["r"] = df["pnl_r_after_cost"]

    rows = []
    for keys, g in df.groupby(["symbol", "year", "direction"]):
        sym, year, direc = keys
        rows.append(
            dict(
                symbol=sym,
                year=int(year),
                direction=direc,
                trades=len(g),
                total_r=float(g["r"].sum()),
                pf=pf(g["r"]),
                win_rate=float((g["r"] > 0).mean()),
            )
        )
    by_sym = df.groupby("symbol").agg(trades=("r", "count"), total_r=("r", "sum")).reset_index()
    by_sym["pf"] = by_sym["symbol"].map(lambda s: pf(df.loc[df["symbol"] == s, "r"]))

    detail = pd.DataFrame(rows).sort_values("total_r", ascending=False)
    detail.to_csv(OUT, index=False)

    top = detail.nlargest(8, "total_r")
    bot = detail.nsmallest(5, "total_r")
    lines = [
        "# TB baseline 損益分解（Original Step 0）",
        "",
        f"母数: **{len(df)} trades** / **{df['r'].sum():+.1f}R** / PF **{pf(df['r']):.2f}**",
        "",
        "## 通貨別",
        "",
        "| symbol | trades | total_r | PF |",
        "|---|---:|---:|---:|",
    ]
    for _, r in by_sym.sort_values("total_r", ascending=False).iterrows():
        p = pf(df.loc[df["symbol"] == r["symbol"], "r"])
        lines.append(f"| {r['symbol']} | {int(r['trades'])} | {r['total_r']:+.1f} | {p:.2f} |")

    lines += ["", "## 寄与 TOP8（通貨×年×方向）", "", "| symbol | year | dir | trades | total_r | PF |", "|---|---:|---|---:|---:|---:|"]
    for _, r in top.iterrows():
        lines.append(
            f"| {r['symbol']} | {int(r['year'])} | {r['direction']} | {int(r['trades'])} | {r['total_r']:+.1f} | {r['pf']:.2f} |"
        )
    lines += ["", "## ドレイン BOTTOM5", "", "| symbol | year | dir | trades | total_r |", "|---|---:|---|---:|---:|"]
    for _, r in bot.iterrows():
        lines.append(f"| {r['symbol']} | {int(r['year'])} | {r['direction']} | {int(r['trades'])} | {r['total_r']:+.1f} |")
    lines += ["", f"CSV: `{OUT.name}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(detail)} rows)")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

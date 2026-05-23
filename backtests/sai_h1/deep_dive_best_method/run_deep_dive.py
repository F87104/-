"""
Sai H1 "急な揺り戻し＋高値停滞" メソッド 深掘りレポート

このメソッドはSai H1全体の+99.91Rの利益のうち+98.84Rを占める「主力」。
それだけに絞って、年別/月別/連負分布/通貨別を詳細分析する。
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", "..", ".."))
SAI_TRADES = os.path.join(REPO_ROOT, "backtests", "sai_h1",
                          "results_2015_2024", "trades.csv")
OUT_DIR = THIS_DIR
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_METHOD = "急な揺り戻し＋高値停滞"


def load_trades() -> pd.DataFrame:
    df = pd.read_csv(SAI_TRADES, parse_dates=["signal_time", "entry_time", "exit_time"])
    df = df[df["method"] == TARGET_METHOD].copy()
    df["year"] = df["entry_time"].dt.year
    df["month"] = df["entry_time"].dt.month
    df["yearmonth"] = df["entry_time"].dt.to_period("M").astype(str)
    return df.sort_values("entry_time").reset_index(drop=True)


def agg(group: pd.DataFrame) -> pd.Series:
    n = len(group)
    if n == 0:
        return pd.Series({})
    wins = int((group["r"] > 0).sum())
    gp = group.loc[group["r"] > 0, "r"].sum()
    gl = group.loc[group["r"] <= 0, "r"].sum()
    pf = gp / abs(gl) if gl < 0 else np.inf
    eq = group["r"].cumsum().reset_index(drop=True)
    dd = float((eq.cummax() - eq).max()) if not eq.empty else 0.0
    return pd.Series({
        "trades": n,
        "wins": wins,
        "losses": n - wins,
        "win_rate": round(wins / n * 100, 2),
        "total_r": round(group["r"].sum(), 3),
        "avg_r": round(group["r"].mean(), 4),
        "median_r": round(group["r"].median(), 3),
        "profit_factor": round(pf, 3) if np.isfinite(pf) else np.inf,
        "max_drawdown_r": round(dd, 3),
        "avg_hold_days": round(group["hold_days"].mean(), 3),
    })


def consecutive_streaks(r: pd.Series) -> dict:
    signs = np.where(r > 0, 1, -1)
    if len(signs) == 0:
        return {"max_winning_streak": 0, "max_losing_streak": 0}
    max_win, max_lose, cur_win, cur_lose = 0, 0, 0, 0
    for s in signs:
        if s == 1:
            cur_win += 1
            cur_lose = 0
        else:
            cur_lose += 1
            cur_win = 0
        max_win = max(max_win, cur_win)
        max_lose = max(max_lose, cur_lose)
    return {"max_winning_streak": max_win, "max_losing_streak": max_lose}


def main() -> None:
    df = load_trades()
    print(f"Loaded {len(df)} trades for method '{TARGET_METHOD}'")

    overall = agg(df)
    streaks = consecutive_streaks(df["r"])
    overall["max_winning_streak"] = streaks["max_winning_streak"]
    overall["max_losing_streak"] = streaks["max_losing_streak"]

    by_year = df.groupby("year").apply(agg).reset_index()
    by_symbol = df.groupby("symbol").apply(agg).reset_index()
    by_direction = df.groupby("direction_ja").apply(agg).reset_index()
    by_yearmonth = df.groupby("yearmonth").apply(agg).reset_index()
    by_month = df.groupby("month").apply(agg).reset_index()

    streaks_by_year = (df.groupby("year")["r"]
                         .apply(lambda r: pd.Series(consecutive_streaks(r)))
                         .unstack().reset_index())

    by_year.to_csv(os.path.join(OUT_DIR, "by_year.csv"), index=False)
    by_symbol.to_csv(os.path.join(OUT_DIR, "by_symbol.csv"), index=False)
    by_direction.to_csv(os.path.join(OUT_DIR, "by_direction.csv"), index=False)
    by_yearmonth.to_csv(os.path.join(OUT_DIR, "by_yearmonth.csv"), index=False)
    by_month.to_csv(os.path.join(OUT_DIR, "by_month.csv"), index=False)
    streaks_by_year.to_csv(os.path.join(OUT_DIR, "streaks_by_year.csv"), index=False)
    overall.to_frame().T.to_csv(os.path.join(OUT_DIR, "overall.csv"), index=False)
    df.to_csv(os.path.join(OUT_DIR, "trades_filtered.csv"), index=False)

    md = []
    md.append(f"# Sai H1 深掘りレポート: 「{TARGET_METHOD}」")
    md.append("")
    md.append(f"Period: 2015-01-01 to 2024-12-31")
    md.append(f"Trades: {len(df)}")
    md.append("")
    md.append("## なぜこのメソッドだけを見るのか")
    md.append("")
    md.append("Sai H1 全体は +99.91R / PF 1.05 だが、内訳は破綻したメソッドが多く、")
    md.append("実利益の **+98.84R が「急な揺り戻し+高値停滞」1つに集中**している。")
    md.append("→ このメソッドだけを取り出した場合、Sai H1の真の実力を測れる。")
    md.append("")
    md.append("## Overall")
    md.append("")
    for k, v in overall.items():
        md.append(f"- {k}: {v}")
    md.append("")

    def tbl(d: pd.DataFrame, title: str) -> None:
        if d.empty:
            return
        md.append(f"## {title}")
        md.append("")
        cols = d.columns.tolist()
        md.append("| " + " | ".join(cols) + " |")
        md.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in d.iterrows():
            md.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        md.append("")

    tbl(by_year, "By Year")
    tbl(by_symbol.sort_values("total_r", ascending=False), "By Symbol (best→worst)")
    tbl(by_direction, "By Direction (Long/Short)")
    tbl(by_month, "By Month (1-12)")
    tbl(streaks_by_year, "Streaks By Year (Max Winning / Max Losing)")

    md.append("## Worst Months (Top10 negative)")
    md.append("")
    worst = by_yearmonth.sort_values("total_r").head(10)
    tbl(worst, "")

    md.append("## Best Months (Top10 positive)")
    md.append("")
    best = by_yearmonth.sort_values("total_r", ascending=False).head(10)
    tbl(best, "")

    with open(os.path.join(OUT_DIR, "report.md"), "w") as f:
        f.write("\n".join(md))

    print("\nOUTPUT FILES")
    for fn in sorted(os.listdir(OUT_DIR)):
        if fn.endswith((".csv", ".md")):
            sz = os.path.getsize(os.path.join(OUT_DIR, fn))
            print(f"  {fn:30} {sz:>10} bytes")


if __name__ == "__main__":
    main()

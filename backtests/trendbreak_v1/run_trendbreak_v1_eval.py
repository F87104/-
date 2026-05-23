"""
TrendBreakV1 評価ランナー (Sai H1 と同じ形式で結果を保存)

期間: 2015-2024
全通貨ペア x [Conservative / Relaxed] の2モード
出力:
  - trades.csv              (個別トレード)
  - summary_by_symbol.csv   (通貨ペア別)
  - summary_by_mode.csv     (モード別: Conservative / Relaxed)
  - summary_by_symbol_mode.csv (通貨ペアxモード別)
  - summary_by_year.csv     (年別)
  - report.md               (人間向け要約)
"""
from __future__ import annotations

import os
import sys
import pandas as pd
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
BACKTEST_DIR = os.path.join(REPO_ROOT, "backtest")
OUT_DIR = os.path.join(THIS_DIR, "results_2015_2024")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, BACKTEST_DIR)

from trendbreak_backtest import (
    PRESETS_CONSERVATIVE, PRESETS_RELAXED,
    compute_signals, simulate,
)
from sai_backtest import load_instrument

INSTRUMENTS_ALL = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
YEAR_FROM = 2015
YEAR_TO = 2024


def run_combo(symbol: str, mode: str) -> tuple[pd.DataFrame, dict]:
    presets = PRESETS_RELAXED if mode == "relaxed" else PRESETS_CONSERVATIVE
    if symbol not in presets:
        return pd.DataFrame(), {}
    cfg = presets[symbol]
    try:
        df = load_instrument(symbol)
    except Exception as e:
        print(f"[SKIP] {symbol}: {e}")
        return pd.DataFrame(), {}
    df = df[(df.index.year >= YEAR_FROM) & (df.index.year <= YEAR_TO)]
    if df.empty:
        return pd.DataFrame(), {}
    sig = compute_signals(df, cfg)
    trades = simulate(sig, cfg)
    if not trades:
        return pd.DataFrame(), {}
    tdf = pd.DataFrame([t.__dict__ for t in trades])
    tdf["symbol"] = symbol
    tdf["mode"] = mode
    tdf["year"] = tdf["entry_time"].dt.year
    return tdf, cfg


def summarize(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    def agg(group: pd.DataFrame) -> pd.Series:
        n = len(group)
        wins = int((group["pnl_r"] > 0).sum())
        losses = int((group["pnl_r"] <= 0).sum())
        gp = group.loc[group["pnl_r"] > 0, "pnl_r"].sum()
        gl = group.loc[group["pnl_r"] <= 0, "pnl_r"].sum()
        pf = gp / abs(gl) if gl < 0 else np.inf
        equity = group["pnl_r"].cumsum().reset_index(drop=True)
        dd = float((equity.cummax() - equity).max()) if not equity.empty else 0.0
        median_r = float(group["pnl_r"].median())
        avg_hold = float(group["bars_held"].mean()) / 24.0  # H1足→日数
        return pd.Series({
            "trades": n, "wins": wins, "losses": losses,
            "win_rate": round(wins / n * 100, 2) if n else 0,
            "total_r": round(group["pnl_r"].sum(), 3),
            "avg_r": round(group["pnl_r"].mean(), 4),
            "median_r": round(median_r, 3),
            "profit_factor": round(pf, 3) if np.isfinite(pf) else np.inf,
            "max_drawdown_r": round(dd, 3),
            "avg_hold_days": round(avg_hold, 3),
        })
    if not group_cols:
        return agg(df).to_frame().T
    return df.groupby(group_cols).apply(agg).reset_index()


def main() -> None:
    print("=" * 70)
    print(f"TrendBreakV1 Evaluation  Period={YEAR_FROM}-{YEAR_TO}")
    print("=" * 70)
    all_trades = []
    summary_rows = []
    for mode in ("conservative", "relaxed"):
        print(f"\n--- Mode: {mode} ---")
        for symbol in INSTRUMENTS_ALL:
            tdf, cfg = run_combo(symbol, mode)
            if tdf.empty:
                print(f"  [{mode:11}] {symbol:7}  (no trades)")
                continue
            all_trades.append(tdf)
            n = len(tdf)
            wr = (tdf["pnl_r"] > 0).mean() * 100
            net = tdf["pnl_r"].sum()
            gp = tdf.loc[tdf["pnl_r"] > 0, "pnl_r"].sum()
            gl = tdf.loc[tdf["pnl_r"] <= 0, "pnl_r"].sum()
            pf = gp / abs(gl) if gl < 0 else float("inf")
            print(f"  [{mode:11}] {symbol:7}  Trades:{n:4}  WR:{wr:5.1f}%  PF:{pf:5.2f}  Net:{net:+7.1f}R")
            summary_rows.append({
                "symbol": symbol, "mode": mode, "trades": n,
                "win_rate": wr, "pf": pf, "net_r": net,
            })

    if not all_trades:
        print("ERROR: No trades generated.")
        return

    trades_all = pd.concat(all_trades, ignore_index=True)
    trades_all = trades_all[[
        "symbol", "mode", "year", "entry_time", "exit_time", "direction",
        "entry", "sl", "tp", "exit_price", "pnl", "pnl_r", "bars_held",
    ]]
    trades_all.to_csv(os.path.join(OUT_DIR, "trades.csv"), index=False)

    sum_overall = summarize(trades_all)
    sum_overall.to_csv(os.path.join(OUT_DIR, "summary_overall.csv"), index=False)

    sum_mode = summarize(trades_all, ["mode"])
    sum_mode.to_csv(os.path.join(OUT_DIR, "summary_by_mode.csv"), index=False)

    sum_symbol = summarize(trades_all, ["symbol"])
    sum_symbol.to_csv(os.path.join(OUT_DIR, "summary_by_symbol.csv"), index=False)

    sum_symbol_mode = summarize(trades_all, ["symbol", "mode"])
    sum_symbol_mode.to_csv(os.path.join(OUT_DIR, "summary_by_symbol_mode.csv"), index=False)

    sum_year = summarize(trades_all, ["year"])
    sum_year.to_csv(os.path.join(OUT_DIR, "summary_by_year.csv"), index=False)

    sum_year_mode = summarize(trades_all, ["mode", "year"])
    sum_year_mode.to_csv(os.path.join(OUT_DIR, "summary_by_mode_year.csv"), index=False)

    md = []
    md.append("# TrendBreakV1 Backtest Report")
    md.append("")
    md.append(f"Period: `{YEAR_FROM}-01-01` to `{YEAR_TO}-12-31`")
    md.append("")
    md.append("Data source: `F87104_test` (resampled to H1)")
    md.append("")
    md.append("## Overall")
    md.append("")
    r = sum_overall.iloc[0]
    md.append(f"- Trades: {int(r['trades'])}")
    md.append(f"- Win rate: {r['win_rate']:.2f}%")
    md.append(f"- Total R: {r['total_r']:.2f}")
    md.append(f"- Average R: {r['avg_r']:.3f}")
    md.append(f"- Median R: {r['median_r']:.3f}")
    md.append(f"- Profit factor: {r['profit_factor']:.2f}")
    md.append(f"- Max drawdown: {r['max_drawdown_r']:.2f} R")
    md.append(f"- Average hold days: {r['avg_hold_days']:.2f}")
    md.append("")

    def tbl(df: pd.DataFrame, title: str) -> None:
        if df.empty:
            return
        md.append(f"## {title}")
        md.append("")
        cols = df.columns.tolist()
        md.append("| " + " | ".join(cols) + " |")
        md.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in df.iterrows():
            md.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        md.append("")

    tbl(sum_mode, "By Mode")
    tbl(sum_symbol.sort_values("total_r", ascending=False), "By Symbol")
    tbl(sum_symbol_mode.sort_values("total_r", ascending=False), "By Symbol x Mode")
    tbl(sum_year, "By Year")
    tbl(sum_year_mode, "By Mode x Year")

    with open(os.path.join(OUT_DIR, "report.md"), "w") as f:
        f.write("\n".join(md))

    print("\n" + "=" * 70)
    print("OUTPUT FILES")
    print("=" * 70)
    for fn in sorted(os.listdir(OUT_DIR)):
        sz = os.path.getsize(os.path.join(OUT_DIR, fn))
        print(f"  {fn:35} {sz:>10} bytes")


if __name__ == "__main__":
    main()

"""
TrendBreakV1 vs Sai (Best Method) 同一期間厳密比較レポート

両者ともに:
- 2015-2024
- H1 timeframe
- F87104_test を起源とする同一データ
- R-multiple ベースの収益測定

比較:
- TrendBreakV1 (Conservative / Relaxed / Combined)
- Sai best method: 「急な揺り戻し＋高値停滞」(Long-only / 全通貨)
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
TB_TRADES = os.path.join(REPO_ROOT, "backtests", "trendbreak_v1",
                         "results_2015_2024", "trades.csv")
SAI_TRADES = os.path.join(REPO_ROOT, "backtests", "sai_h1",
                          "deep_dive_best_method", "trades_filtered.csv")
OUT_DIR = THIS_DIR
os.makedirs(OUT_DIR, exist_ok=True)


def load_tb() -> pd.DataFrame:
    df = pd.read_csv(TB_TRADES, parse_dates=["entry_time", "exit_time"])
    df["year"] = df["entry_time"].dt.year
    df.rename(columns={"pnl_r": "r"}, inplace=True)
    df["hold_days"] = df["bars_held"] / 24.0
    return df


def load_sai() -> pd.DataFrame:
    df = pd.read_csv(SAI_TRADES, parse_dates=["entry_time", "exit_time"])
    df["year"] = df["entry_time"].dt.year
    return df


def metrics(df: pd.DataFrame, label: str) -> dict:
    if df.empty:
        return {"label": label, "trades": 0}
    n = len(df)
    wins = int((df["r"] > 0).sum())
    losses = n - wins
    gp = df.loc[df["r"] > 0, "r"].sum()
    gl = df.loc[df["r"] <= 0, "r"].sum()
    pf = gp / abs(gl) if gl < 0 else float("inf")
    eq = df.sort_values("entry_time")["r"].cumsum().reset_index(drop=True)
    dd = float((eq.cummax() - eq).max())
    return {
        "label": label,
        "trades": n,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / n * 100, 2),
        "total_r": round(df["r"].sum(), 2),
        "avg_r": round(df["r"].mean(), 3),
        "median_r": round(df["r"].median(), 3),
        "profit_factor": round(pf, 2) if np.isfinite(pf) else float("inf"),
        "max_dd_r": round(dd, 2),
        "expectancy_per_trade_r": round(df["r"].mean(), 3),
        "avg_hold_days": round(df["hold_days"].mean(), 2),
        "trades_per_year": round(n / 10, 1),
        "calmar_proxy": round(df["r"].sum() / dd, 2) if dd > 0 else float("inf"),
    }


def year_series(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("year").agg(
        trades=("r", "count"),
        wr=("r", lambda s: (s > 0).mean() * 100),
        total_r=("r", "sum"),
        max_dd=("r", lambda s: (s.cumsum().cummax() - s.cumsum()).max()),
    ).round(2).reset_index()
    return g


def main() -> None:
    tb = load_tb()
    sai = load_sai()

    rows = []
    rows.append(metrics(tb, "TrendBreakV1 [Combined]"))
    rows.append(metrics(tb[tb["mode"] == "conservative"], "TrendBreakV1 [Conservative]"))
    rows.append(metrics(tb[tb["mode"] == "relaxed"], "TrendBreakV1 [Relaxed]"))
    rows.append(metrics(sai, "Sai H1 [BestMethod=急な揺り戻し+高値停滞]"))

    main_table = pd.DataFrame(rows)
    main_table.to_csv(os.path.join(OUT_DIR, "comparison_main.csv"), index=False)
    print(main_table.to_string(index=False))

    tb_year_combined = year_series(tb).assign(strategy="TrendBreakV1_Combined")
    tb_year_conserv = year_series(tb[tb["mode"] == "conservative"]).assign(strategy="TrendBreakV1_Conservative")
    tb_year_relaxed = year_series(tb[tb["mode"] == "relaxed"]).assign(strategy="TrendBreakV1_Relaxed")
    sai_year = year_series(sai).assign(strategy="Sai_BestMethod")
    year_all = pd.concat([tb_year_combined, tb_year_conserv, tb_year_relaxed, sai_year], ignore_index=True)
    year_all = year_all[["strategy", "year", "trades", "wr", "total_r", "max_dd"]]
    year_all.to_csv(os.path.join(OUT_DIR, "comparison_by_year.csv"), index=False)

    tb_sym = (tb.groupby("symbol")
                .agg(trades=("r", "count"),
                     wr=("r", lambda s: round((s > 0).mean() * 100, 2)),
                     total_r=("r", lambda s: round(s.sum(), 2)),
                     pf=("r", lambda s: round(s[s > 0].sum() / abs(s[s <= 0].sum()), 2)
                         if s[s <= 0].sum() < 0 else float("inf")))
                .reset_index().sort_values("total_r", ascending=False))
    tb_sym["strategy"] = "TrendBreakV1"

    sai_sym = (sai.groupby("symbol")
                  .agg(trades=("r", "count"),
                       wr=("r", lambda s: round((s > 0).mean() * 100, 2)),
                       total_r=("r", lambda s: round(s.sum(), 2)),
                       pf=("r", lambda s: round(s[s > 0].sum() / abs(s[s <= 0].sum()), 2)
                           if s[s <= 0].sum() < 0 else float("inf")))
                  .reset_index().sort_values("total_r", ascending=False))
    sai_sym["strategy"] = "Sai_BestMethod"

    sym_all = pd.concat([tb_sym, sai_sym], ignore_index=True)[["strategy", "symbol", "trades", "wr", "total_r", "pf"]]
    sym_all.to_csv(os.path.join(OUT_DIR, "comparison_by_symbol.csv"), index=False)

    md = []
    md.append("# TrendBreakV1 vs Sai (Best Method) 同一期間厳密比較")
    md.append("")
    md.append("- Period: 2015-01-01 to 2024-12-31")
    md.append("- Timeframe: H1")
    md.append("- Metric: R-multiple")
    md.append("- Data source: F87104_test (両戦略とも同じ)")
    md.append("")
    md.append("## ⭐ Main Comparison")
    md.append("")
    cols = list(main_table.columns)
    md.append("| " + " | ".join(cols) + " |")
    md.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, r in main_table.iterrows():
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    md.append("")

    md.append("## Key Findings")
    md.append("")
    tb_c = main_table.iloc[0]
    sai_r = main_table.iloc[3]
    md.append(f"### 1. 純利益 (Total R)")
    md.append(f"- TrendBreakV1 Combined: **+{tb_c['total_r']}R**")
    md.append(f"- Sai Best Method:        **+{sai_r['total_r']}R**")
    md.append(f"- **倍率: {round(tb_c['total_r'] / sai_r['total_r'], 2)}x** (TrendBreakが Sai best の何倍稼いだか)")
    md.append("")
    md.append(f"### 2. プロフィットファクター")
    md.append(f"- TrendBreakV1 Combined: **{tb_c['profit_factor']}**")
    md.append(f"- Sai Best Method:        **{sai_r['profit_factor']}**")
    md.append("")
    md.append(f"### 3. リスク調整リターン (Calmar Proxy = Total R / MaxDD R)")
    md.append(f"- TrendBreakV1 Combined: **{tb_c['calmar_proxy']}**")
    md.append(f"- Sai Best Method:        **{sai_r['calmar_proxy']}**")
    md.append("")
    md.append(f"### 4. 1トレード当たり期待値 (Avg R)")
    md.append(f"- TrendBreakV1 Combined: **{tb_c['avg_r']}R**")
    md.append(f"- Sai Best Method:        **{sai_r['avg_r']}R**")
    md.append("")
    md.append(f"### 5. 年間取引機会")
    md.append(f"- TrendBreakV1 Combined: **{tb_c['trades_per_year']} trades/年**")
    md.append(f"- Sai Best Method:        **{sai_r['trades_per_year']} trades/年**")
    md.append("")
    md.append(f"### 6. 平均保有期間")
    md.append(f"- TrendBreakV1 Combined: **{tb_c['avg_hold_days']} 日**")
    md.append(f"- Sai Best Method:        **{sai_r['avg_hold_days']} 日**")
    md.append("")

    def tbl(d: pd.DataFrame, title: str) -> None:
        if d.empty:
            return
        md.append(f"## {title}")
        md.append("")
        c = d.columns.tolist()
        md.append("| " + " | ".join(c) + " |")
        md.append("| " + " | ".join(["---"] * len(c)) + " |")
        for _, row in d.iterrows():
            md.append("| " + " | ".join(str(row[col]) for col in c) + " |")
        md.append("")

    tbl(year_all, "Year-by-Year (4 strategies side by side)")
    tbl(sym_all, "Symbol-by-Symbol")

    md.append("## 結論")
    md.append("")
    md.append("### 🏆 総合勝者: **TrendBreakV1 (Combined)**")
    md.append("")
    md.append(f"- 純利益で Sai best の **{round(tb_c['total_r'] / sai_r['total_r'], 2)}倍**")
    md.append(f"- PF: TrendBreak {tb_c['profit_factor']} vs Sai {sai_r['profit_factor']}")
    md.append(f"- 年間取引機会: TrendBreak {tb_c['trades_per_year']} vs Sai {sai_r['trades_per_year']}")
    md.append(f"- リスク調整リターン (Calmar): TrendBreak {tb_c['calmar_proxy']} vs Sai {sai_r['calmar_proxy']}")
    md.append("")
    md.append("### Sai best method の唯一の優位点")
    md.append(f"- **勝率**: Sai {sai_r['win_rate_pct']}% vs TrendBreak {tb_c['win_rate_pct']}%")
    md.append(f"  → ただし、利益は TrendBreak が圧勝。勝率は本質的指標ではない。")
    md.append(f"  → Sai は Long-only (買いのみ) なので、市場の長期上昇バイアスを利用している面もある。")
    md.append("")
    md.append("### 結論")
    md.append("- **本番戦略は TrendBreakV1_Final.pine で決まり**")
    md.append("- Sai の best method ロジック (急な揺り戻し+高値停滞 = 上昇トレンド中の押し目) を")
    md.append("  TrendBreak に組み込む案は、過剰最適化リスクが高いため非推奨")
    md.append("- Sai 系のスクリプトは引き続き **裁量補助の可視化ツール** として活用")

    with open(os.path.join(OUT_DIR, "comparison_report.md"), "w") as f:
        f.write("\n".join(md))

    print("\nOUTPUT FILES")
    for fn in sorted(os.listdir(OUT_DIR)):
        if fn.endswith((".csv", ".md")):
            sz = os.path.getsize(os.path.join(OUT_DIR, fn))
            print(f"  {fn:35} {sz:>10} bytes")


if __name__ == "__main__":
    main()

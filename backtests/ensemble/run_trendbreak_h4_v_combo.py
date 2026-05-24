#!/usr/bin/env python3
"""
Combine TrendBreakV1 FINAL baseline trades with the H4 sharp-drop V recovery
visual trade set.

The goal is not to create a new entry rule here, but to answer:

- What happens if both scripts are traded together?
- How many trades are added?
- Does win rate / PF / drawdown / equity growth improve?

Three portfolio assumptions are compared:

1. all_trades:
   Take every trade from both scripts.
2. trendbreak_priority_add_h4_when_free:
   Keep all TrendBreakV1 trades, and add H4 V trades only when they do not
   overlap an accepted trade on the same symbol.
3. same_symbol_first_wins:
   One active trade per symbol. The earliest entry wins. If two trades have
   the exact same entry time, TrendBreakV1 is preferred.

All R values are after costs where available. Equity growth assumes a fixed
fractional 1% account risk per trade unless changed below.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = THIS_DIR / "trendbreak_h4_v_combo_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TREND_BREAK_TRADES = (
    REPO_ROOT
    / "backtests"
    / "trendbreak_v1"
    / "fakeout_before_after_2015_2024"
    / "trades.csv"
)
H4_V_TRADES = (
    REPO_ROOT
    / "backtests"
    / "elliott_fibo"
    / "results_2015_2024"
    / "strict_v_recovery"
    / "strict_v_trades_h4.csv"
)

INITIAL_CAPITAL_JPY = 1_000_000.0
RISK_PCT = 1.0
RECOMMENDED_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]


def fmt_num(value: float, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"{value:,.{digits}f}"


def fmt_pct(value: float, digits: int = 2) -> str:
    return f"{fmt_num(value, digits)}%"


def fmt_jpy(value: float) -> str:
    return f"{value:,.0f}円"


def read_trendbreak() -> pd.DataFrame:
    df = pd.read_csv(TREND_BREAK_TRADES)
    df = df[df["rule_name"].eq("baseline")].copy()
    out = pd.DataFrame(
        {
            "strategy": "TrendBreakV1",
            "symbol": df["symbol"],
            "direction": df["direction"],
            "signal_time": pd.to_datetime(df["signal_time"]),
            "entry_time": pd.to_datetime(df["entry_time"]),
            "exit_time": pd.to_datetime(df["exit_time"]),
            "entry": df["entry"],
            "exit": df["exit_price"],
            "r": df["pnl_r_after_cost"],
            "exit_reason": df["exit_reason"],
        }
    )
    return out


def read_h4_v() -> pd.DataFrame:
    df = pd.read_csv(H4_V_TRADES)
    out = pd.DataFrame(
        {
            "strategy": "H4 Sharp Drop V",
            "symbol": df["symbol"],
            "direction": df["direction"],
            "signal_time": pd.to_datetime(df["signal_time"], errors="coerce"),
            "entry_time": pd.to_datetime(df["entry_time"]),
            "exit_time": pd.to_datetime(df["exit_time"]),
            "entry": df["entry"],
            "exit": df["exit"],
            "r": df["r_after_cost"],
            "exit_reason": df["exit_reason"],
        }
    )
    out["signal_time"] = out["signal_time"].fillna(out["entry_time"])
    return out


def overlaps(a_start: pd.Timestamp, a_end: pd.Timestamp, b_start: pd.Timestamp, b_end: pd.Timestamp) -> bool:
    return a_start < b_end and b_start < a_end


def scenario_all_trades(trendbreak: pd.DataFrame, h4_v: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat([trendbreak, h4_v], ignore_index=True)
    return df.sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)


def scenario_trendbreak_priority(trendbreak: pd.DataFrame, h4_v: pd.DataFrame) -> pd.DataFrame:
    accepted = trendbreak.sort_values(["entry_time", "symbol"]).to_dict("records")
    accepted_by_symbol: dict[str, list[dict]] = {}
    for trade in accepted:
        accepted_by_symbol.setdefault(trade["symbol"], []).append(trade)

    h4_added = []
    for trade in h4_v.sort_values(["entry_time", "symbol"]).to_dict("records"):
        symbol_trades = accepted_by_symbol.setdefault(trade["symbol"], [])
        has_overlap = any(
            overlaps(trade["entry_time"], trade["exit_time"], t["entry_time"], t["exit_time"])
            for t in symbol_trades
        )
        if has_overlap:
            continue
        h4_added.append(trade)
        symbol_trades.append(trade)
        symbol_trades.sort(key=lambda x: (x["entry_time"], x["exit_time"]))

    df = pd.DataFrame(accepted + h4_added)
    return df.sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)


def scenario_first_wins(trendbreak: pd.DataFrame, h4_v: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat([trendbreak, h4_v], ignore_index=True)
    # On exact ties, prefer TrendBreakV1 because it is the current core system.
    priority = {"TrendBreakV1": 0, "H4 Sharp Drop V": 1}
    df["priority"] = df["strategy"].map(priority).fillna(9)
    df = df.sort_values(["entry_time", "priority", "symbol"]).reset_index(drop=True)

    accepted: list[dict] = []
    by_symbol: dict[str, list[dict]] = {}
    for trade in df.to_dict("records"):
        symbol_trades = by_symbol.setdefault(trade["symbol"], [])
        has_overlap = any(
            overlaps(trade["entry_time"], trade["exit_time"], t["entry_time"], t["exit_time"])
            for t in symbol_trades
        )
        if has_overlap:
            continue
        accepted.append(trade)
        symbol_trades.append(trade)
        symbol_trades.sort(key=lambda x: (x["entry_time"], x["exit_time"]))

    out = pd.DataFrame(accepted).drop(columns=["priority"], errors="ignore")
    return out.sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)


def max_streak(values: pd.Series, wins: bool) -> int:
    best = 0
    current = 0
    for value in values:
        ok = value > 0 if wins else value <= 0
        if ok:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def equity_curve(trades: pd.DataFrame, risk_pct: float = RISK_PCT, initial: float = INITIAL_CAPITAL_JPY) -> pd.DataFrame:
    ordered = trades.sort_values(["exit_time", "entry_time", "strategy", "symbol"]).reset_index(drop=True)
    equity = initial
    peak = initial
    rows = []
    for _, trade in ordered.iterrows():
        equity *= 1.0 + float(trade["r"]) * risk_pct / 100.0
        peak = max(peak, equity)
        dd_pct = (peak - equity) / peak * 100.0 if peak > 0 else 0.0
        rows.append(
            {
                "exit_time": trade["exit_time"],
                "strategy": trade["strategy"],
                "symbol": trade["symbol"],
                "r": trade["r"],
                "equity": equity,
                "drawdown_pct": dd_pct,
            }
        )
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, scenario: str, symbol_filter: str = "all") -> dict:
    ordered = trades.sort_values(["exit_time", "entry_time", "strategy", "symbol"]).reset_index(drop=True)
    r = ordered["r"].astype(float)
    wins = r[r > 0]
    losses = r[r <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() < 0 else math.inf
    r_curve = r.cumsum()
    max_dd_r = float((r_curve.cummax() - r_curve).max()) if len(r_curve) else 0.0
    eq = equity_curve(trades)
    final_equity = float(eq["equity"].iloc[-1]) if not eq.empty else INITIAL_CAPITAL_JPY
    max_dd_pct = float(eq["drawdown_pct"].max()) if not eq.empty else 0.0
    linear_equity = INITIAL_CAPITAL_JPY * (1.0 + float(r.sum()) * RISK_PCT / 100.0)
    return {
        "scenario": scenario,
        "symbol_filter": symbol_filter,
        "trades": int(len(trades)),
        "win_rate": float((r > 0).mean() * 100.0) if len(r) else math.nan,
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()) if len(r) else math.nan,
        "pf": pf,
        "max_dd_r": max_dd_r,
        "max_dd_pct_compounded": max_dd_pct,
        "max_loss_streak": max_streak(r, wins=False),
        "max_win_streak": max_streak(r, wins=True),
        "linear_final_jpy_1pct": linear_equity,
        "compound_final_jpy_1pct": final_equity,
    }


def grouped_summary(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple))
        row.update(summarize(group.sort_values(["exit_time"]), scenario="group"))
        rows.append(row)
    drop_cols = ["scenario", "symbol_filter", "linear_final_jpy_1pct", "compound_final_jpy_1pct"]
    return pd.DataFrame(rows).drop(columns=drop_cols, errors="ignore")


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    headers = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in headers) + " |")
    return "\n".join(lines)


def view_overall(summary: pd.DataFrame) -> pd.DataFrame:
    view = summary.copy()
    view["win_rate"] = view["win_rate"].map(lambda x: fmt_pct(x))
    view["total_r"] = view["total_r"].map(lambda x: fmt_num(x) + "R")
    view["avg_r"] = view["avg_r"].map(lambda x: fmt_num(x, 3) + "R")
    view["pf"] = view["pf"].map(lambda x: "inf" if math.isinf(x) else fmt_num(x, 3))
    view["max_dd_r"] = view["max_dd_r"].map(lambda x: fmt_num(x) + "R")
    view["max_dd_pct_compounded"] = view["max_dd_pct_compounded"].map(lambda x: fmt_pct(x))
    view["linear_final_jpy_1pct"] = view["linear_final_jpy_1pct"].map(fmt_jpy)
    view["compound_final_jpy_1pct"] = view["compound_final_jpy_1pct"].map(fmt_jpy)
    return view


def view_group(df: pd.DataFrame) -> pd.DataFrame:
    view = df.copy()
    for col in ["win_rate", "max_dd_pct_compounded"]:
        if col in view:
            view[col] = view[col].map(lambda x: fmt_pct(float(x)))
    for col in ["total_r", "avg_r", "max_dd_r"]:
        if col in view:
            digits = 3 if col == "avg_r" else 2
            view[col] = view[col].map(lambda x: fmt_num(float(x), digits) + "R")
    if "pf" in view:
        view["pf"] = view["pf"].map(lambda x: "inf" if math.isinf(float(x)) else fmt_num(float(x), 3))
    return view


def main() -> None:
    trendbreak = read_trendbreak()
    h4_v = read_h4_v()

    scenarios = {
        "trendbreak_only": trendbreak,
        "h4_v_only": h4_v,
        "all_trades": scenario_all_trades(trendbreak, h4_v),
        "trendbreak_priority_add_h4_when_free": scenario_trendbreak_priority(trendbreak, h4_v),
        "same_symbol_first_wins": scenario_first_wins(trendbreak, h4_v),
    }

    overall_rows = []
    recommended_rows = []
    for name, trades in scenarios.items():
        out = trades.sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)
        out.to_csv(OUT_DIR / f"{name}_trades.csv", index=False)
        equity_curve(out).to_csv(OUT_DIR / f"{name}_equity_curve.csv", index=False)
        overall_rows.append(summarize(out, scenario=name, symbol_filter="all"))

        recommended = out[out["symbol"].isin(RECOMMENDED_SYMBOLS)].copy()
        recommended_rows.append(summarize(recommended, scenario=name, symbol_filter="recommended_ex_audjpy"))

    overall = pd.DataFrame(overall_rows)
    recommended = pd.DataFrame(recommended_rows)
    overall.to_csv(OUT_DIR / "overall_all_symbols.csv", index=False)
    recommended.to_csv(OUT_DIR / "overall_recommended_ex_audjpy.csv", index=False)

    main_combo = scenarios["trendbreak_priority_add_h4_when_free"]
    by_strategy = grouped_summary(main_combo, ["strategy"]).sort_values("strategy")
    by_symbol = grouped_summary(main_combo, ["symbol"]).sort_values("total_r", ascending=False)
    by_year = grouped_summary(
        main_combo.assign(year=main_combo["exit_time"].dt.year.astype(str)),
        ["year"],
    ).sort_values("year")
    by_strategy.to_csv(OUT_DIR / "trendbreak_priority_by_strategy.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "trendbreak_priority_by_symbol.csv", index=False)
    by_year.to_csv(OUT_DIR / "trendbreak_priority_by_year.csv", index=False)

    lines = [
        "# TrendBreakV1 + H4急落後V字回復 組み合わせ分析 2015-2024",
        "",
        "## 前提",
        "",
        "- TrendBreakV1: `fakeout_before_after_2015_2024/trades.csv` の `baseline`。現行HYBRID、騙し回避フィルタOFF、同方向最大保有数は初期値1の想定。",
        "- H4急落後V字回復: `strict_v_recovery/strict_v_trades_h4.csv`。現在の `h4_sharp_drop_v_recovery_visual.pine` に近い、完全回復・回復速度重視の厳格V字。",
        "- Rはコスト込み。資産推定は `100万円スタート / 1トレード1%リスク`。",
        "",
        "## 全通貨の比較",
        "",
        markdown_table(
            view_overall(
                overall[
                    [
                        "scenario",
                        "trades",
                        "win_rate",
                        "total_r",
                        "avg_r",
                        "pf",
                        "max_dd_r",
                        "max_dd_pct_compounded",
                        "max_loss_streak",
                        "linear_final_jpy_1pct",
                        "compound_final_jpy_1pct",
                    ]
                ]
            )
        ),
        "",
        "## 推奨6通貨のみ（AUDJPY除外）",
        "",
        markdown_table(
            view_overall(
                recommended[
                    [
                        "scenario",
                        "trades",
                        "win_rate",
                        "total_r",
                        "avg_r",
                        "pf",
                        "max_dd_r",
                        "max_dd_pct_compounded",
                        "max_loss_streak",
                        "linear_final_jpy_1pct",
                        "compound_final_jpy_1pct",
                    ]
                ]
            )
        ),
        "",
        "## 実運用寄りの採用案",
        "",
        "`trendbreak_priority_add_h4_when_free` は、TrendBreakV1を主軸として全て採用し、H4 Vは同一通貨でポジションが空いている時だけ追加する案です。",
        "",
        "### 戦略別",
        "",
        markdown_table(
            view_group(
                by_strategy[
                    [
                        "strategy",
                        "trades",
                        "win_rate",
                        "total_r",
                        "avg_r",
                        "pf",
                        "max_dd_r",
                        "max_loss_streak",
                    ]
                ]
            )
        ),
        "",
        "### 通貨別",
        "",
        markdown_table(
            view_group(
                by_symbol[
                    [
                        "symbol",
                        "trades",
                        "win_rate",
                        "total_r",
                        "avg_r",
                        "pf",
                        "max_dd_r",
                        "max_loss_streak",
                    ]
                ]
            )
        ),
        "",
        "### 年別",
        "",
        markdown_table(
            view_group(
                by_year[
                    [
                        "year",
                        "trades",
                        "win_rate",
                        "total_r",
                        "avg_r",
                        "pf",
                        "max_dd_r",
                        "max_loss_streak",
                    ]
                ]
            )
        ),
        "",
        "## 読み取り",
        "",
        "- H4急落後V字回復は単体では成績が弱いため、今の厳格V字をそのまま売買システムとして足す価値は低いです。",
        "- TrendBreakV1を主軸にして、H4 Vを同一通貨が空いている時だけ追加しても、改善幅は限定的か、悪化する可能性があります。",
        "- H4 Vは売買トリガーではなく、以前の結論どおり「環境認識・候補抽出」として使い、高値停滞/再ブレイク/MACD/BBなどの追加条件で絞る方が自然です。",
        "",
        "## 出力ファイル",
        "",
        "- `overall_all_symbols.csv`",
        "- `overall_recommended_ex_audjpy.csv`",
        "- `trendbreak_priority_add_h4_when_free_trades.csv`",
        "- `trendbreak_priority_by_strategy.csv`",
        "- `trendbreak_priority_by_symbol.csv`",
        "- `trendbreak_priority_by_year.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_DIR}")
    print("\nAll symbols:")
    print(
        overall[
            [
                "scenario",
                "trades",
                "win_rate",
                "total_r",
                "pf",
                "max_dd_r",
                "compound_final_jpy_1pct",
            ]
        ].to_string(index=False)
    )
    print("\nRecommended ex AUDJPY:")
    print(
        recommended[
            [
                "scenario",
                "trades",
                "win_rate",
                "total_r",
                "pf",
                "max_dd_r",
                "compound_final_jpy_1pct",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

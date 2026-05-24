#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = THIS_DIR / "trendbreak_t5_practical_combo_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TREND_BREAK_TRADES = REPO_ROOT / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
T5_TRADES = REPO_ROOT / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"

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
    return pd.DataFrame(
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


def read_t5_practical() -> pd.DataFrame:
    df = pd.read_csv(T5_TRADES)
    df = df[df["period"].eq("Research_2015_2024")].copy()
    # Practical C125: BB高すぎを避け、候補から16本以内、弱い単独rebreakを除外。
    df = df[
        (df["bb_pos"] <= 0.95)
        & (df["signal_recovery_bars"] <= 16)
        & ~(
            (df["trigger_type"] == "rebreak")
            & ((df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03))
        )
    ].copy()
    return pd.DataFrame(
        {
            "strategy": "H4 T5 MACD BB",
            "symbol": df["symbol"],
            "direction": df["direction"],
            "signal_time": pd.to_datetime(df["signal_time"]),
            "entry_time": pd.to_datetime(df["entry_time"]),
            "exit_time": pd.to_datetime(df["exit_time"]),
            "entry": df["entry"],
            "exit": df["exit"],
            "r": df["r_after_cost"],
            "exit_reason": df["exit_reason"],
            "trigger_type": df["trigger_type"],
        }
    )


def overlaps(a_start: pd.Timestamp, a_end: pd.Timestamp, b_start: pd.Timestamp, b_end: pd.Timestamp) -> bool:
    return a_start < b_end and b_start < a_end


def scenario_all(trendbreak: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([trendbreak, t5], ignore_index=True).sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)


def scenario_trendbreak_priority(trendbreak: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    accepted = trendbreak.sort_values(["entry_time", "symbol"]).to_dict("records")
    by_symbol: dict[str, list[dict]] = {}
    for trade in accepted:
        by_symbol.setdefault(trade["symbol"], []).append(trade)

    added = []
    for trade in t5.sort_values(["entry_time", "symbol"]).to_dict("records"):
        symbol_trades = by_symbol.setdefault(trade["symbol"], [])
        if any(overlaps(trade["entry_time"], trade["exit_time"], t["entry_time"], t["exit_time"]) for t in symbol_trades):
            continue
        added.append(trade)
        symbol_trades.append(trade)
        symbol_trades.sort(key=lambda x: (x["entry_time"], x["exit_time"]))
    return pd.DataFrame(accepted + added).sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)


def scenario_first_wins(trendbreak: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    df = pd.concat([trendbreak, t5], ignore_index=True)
    priority = {"TrendBreakV1": 0, "H4 T5 MACD BB": 1}
    df["priority"] = df["strategy"].map(priority).fillna(9)
    df = df.sort_values(["entry_time", "priority", "symbol"]).reset_index(drop=True)
    accepted: list[dict] = []
    by_symbol: dict[str, list[dict]] = {}
    for trade in df.to_dict("records"):
        symbol_trades = by_symbol.setdefault(trade["symbol"], [])
        if any(overlaps(trade["entry_time"], trade["exit_time"], t["entry_time"], t["exit_time"]) for t in symbol_trades):
            continue
        accepted.append(trade)
        symbol_trades.append(trade)
        symbol_trades.sort(key=lambda x: (x["entry_time"], x["exit_time"]))
    return pd.DataFrame(accepted).drop(columns=["priority"], errors="ignore")


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


def equity_curve(trades: pd.DataFrame) -> pd.DataFrame:
    ordered = trades.sort_values(["exit_time", "entry_time", "strategy", "symbol"]).reset_index(drop=True)
    equity = INITIAL_CAPITAL_JPY
    peak = equity
    rows = []
    for _, trade in ordered.iterrows():
        equity *= 1.0 + float(trade["r"]) * RISK_PCT / 100.0
        peak = max(peak, equity)
        rows.append(
            {
                "exit_time": trade["exit_time"],
                "strategy": trade["strategy"],
                "symbol": trade["symbol"],
                "r": trade["r"],
                "equity": equity,
                "drawdown_pct": (peak - equity) / peak * 100.0,
            }
        )
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, scenario: str) -> dict:
    ordered = trades.sort_values(["exit_time", "entry_time", "strategy", "symbol"]).reset_index(drop=True)
    r = ordered["r"].astype(float)
    wins = r[r > 0]
    losses = r[r <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() < 0 else math.inf
    r_curve = r.cumsum()
    eq = equity_curve(ordered)
    final_equity = float(eq["equity"].iloc[-1]) if not eq.empty else INITIAL_CAPITAL_JPY
    max_dd_pct = float(eq["drawdown_pct"].max()) if not eq.empty else 0.0
    return {
        "scenario": scenario,
        "trades": int(len(ordered)),
        "win_rate": float((r > 0).mean() * 100.0) if len(r) else math.nan,
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()) if len(r) else math.nan,
        "pf": pf,
        "max_dd_r": float((r_curve.cummax() - r_curve).max()) if len(r_curve) else 0.0,
        "max_dd_pct_compounded": max_dd_pct,
        "max_loss_streak": max_streak(r, wins=False),
        "linear_final_jpy_1pct": INITIAL_CAPITAL_JPY * (1.0 + float(r.sum()) * RISK_PCT / 100.0),
        "compound_final_jpy_1pct": final_equity,
    }


def grouped_summary(trades: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows = []
    for key, group in trades.groupby(group_col, dropna=False):
        row = {group_col: key}
        row.update(summarize(group, "group"))
        rows.append(row)
    return pd.DataFrame(rows).drop(columns=["scenario", "linear_final_jpy_1pct", "compound_final_jpy_1pct"], errors="ignore")


def md(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    headers = list(df.columns)
    rows = []
    for _, row in df.iterrows():
        out = []
        for col in headers:
            val = row[col]
            if col in {"win_rate", "max_dd_pct_compounded"}:
                out.append(fmt_pct(float(val)))
            elif col in {"total_r", "avg_r", "max_dd_r"}:
                out.append(fmt_num(float(val), 3 if col == "avg_r" else 2) + "R")
            elif col == "pf":
                out.append("inf" if math.isinf(float(val)) else fmt_num(float(val), 3))
            elif col.endswith("jpy_1pct"):
                out.append(fmt_jpy(float(val)))
            else:
                out.append(str(val))
        rows.append(out)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def main() -> None:
    trendbreak = read_trendbreak()
    t5 = read_t5_practical()
    scenarios = {
        "trendbreak_only": trendbreak,
        "t5_practical_only": t5,
        "all_trades": scenario_all(trendbreak, t5),
        "trendbreak_priority_add_t5_when_free": scenario_trendbreak_priority(trendbreak, t5),
        "same_symbol_first_wins": scenario_first_wins(trendbreak, t5),
    }

    overall_rows = []
    recommended_rows = []
    for name, trades in scenarios.items():
        out = trades.sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)
        out.to_csv(OUT_DIR / f"{name}_trades.csv", index=False)
        equity_curve(out).to_csv(OUT_DIR / f"{name}_equity_curve.csv", index=False)
        overall_rows.append(summarize(out, name))
        recommended_rows.append(summarize(out[out["symbol"].isin(RECOMMENDED_SYMBOLS)].copy(), name))

    overall = pd.DataFrame(overall_rows)
    recommended = pd.DataFrame(recommended_rows)
    overall.to_csv(OUT_DIR / "overall_all_symbols.csv", index=False)
    recommended.to_csv(OUT_DIR / "overall_recommended_ex_audjpy.csv", index=False)

    combo = scenarios["trendbreak_priority_add_t5_when_free"]
    by_strategy = grouped_summary(combo, "strategy").sort_values("total_r", ascending=False)
    by_symbol = grouped_summary(combo, "symbol").sort_values("total_r", ascending=False)
    by_trigger = grouped_summary(t5, "trigger_type").sort_values("total_r", ascending=False)
    by_strategy.to_csv(OUT_DIR / "trendbreak_priority_by_strategy.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "trendbreak_priority_by_symbol.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "t5_practical_by_trigger.csv", index=False)

    report = [
        "# TrendBreakV1 + H4 T5 MACD BB 実戦用フィルタ 組み合わせ分析 2015-2024",
        "",
        "## 前提",
        "",
        "- TrendBreakV1: `fakeout_before_after_2015_2024/trades.csv` の baseline。",
        "- H4 T5 MACD BB: V候補を環境認識にし、BB<=0.95、V候補から16本以内、弱い単独rebreak除外の実戦用フィルタ。",
        "- Rはコスト込み。資産推定は100万円スタート、1トレード1%リスク。",
        "",
        "## 全通貨",
        "",
        md(overall[["scenario", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_dd_pct_compounded", "max_loss_streak", "linear_final_jpy_1pct", "compound_final_jpy_1pct"]]),
        "",
        "## 推奨6通貨のみ（AUDJPY除外）",
        "",
        md(recommended[["scenario", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_dd_pct_compounded", "max_loss_streak", "linear_final_jpy_1pct", "compound_final_jpy_1pct"]]),
        "",
        "## TrendBreak優先 + T5追加時の内訳",
        "",
        "### 戦略別",
        "",
        md(by_strategy[["strategy", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_loss_streak"]]),
        "",
        "### 通貨別",
        "",
        md(by_symbol[["symbol", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_loss_streak"]]),
        "",
        "### T5トリガー別",
        "",
        md(by_trigger[["trigger_type", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_loss_streak"]]),
        "",
        "## 読み取り",
        "",
        "- 厳格V字をそのまま足した旧分析とは違い、T5/MACD/BBで絞ったV候補手法は単体でプラス。",
        "- ただし取引回数は少ないため、TrendBreakを主軸、T5を補助にするのが自然。",
        "- 同一通貨でポジションが空いている時だけT5を追加する案では、総RはTrendBreak単体より上がるが、DDもやや増える可能性がある。",
        "- 実運用ではT5を0.25Rから0.5Rで始め、フォワード30から50回で安定確認してから通常リスク化するのが現実的。",
        "",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()

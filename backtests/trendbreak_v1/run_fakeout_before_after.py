#!/usr/bin/env python3
"""
TrendBreakV1 fakeout filter before/after validation.

This runner re-simulates the entry logic, rather than only subsetting already
entered trades. It compares the current HYBRID baseline with practical fakeout
mitigation rules:

1. baseline: current TrendBreakV1 HYBRID logic.
2. body60_filter: only enter if the signal candle body is >= 60% of its range.
3. early_back_inside_1: enter normally, but exit if the first bar after entry
   closes back inside the broken level.
4. body60_plus_early1: apply both rules.

All values are R after approximate spread/slippage costs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import run_fakeout_rule_matrix as matrix
import run_fakeout_feature_study as study


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "fakeout_before_after_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)


RULES = [
    ("baseline", "現行HYBRID。追加の騙し回避なし", None, 0),
    ("body60_filter", "シグナル足の実体がローソク足全体の60%以上の時だけ入る", lambda f: f["body_ratio"] >= 0.60, 0),
    ("early_back_inside_1", "通常通り入る。エントリー後1本以内に終値がブレイク水準内へ戻れば次足始値で撤退", None, 1),
    (
        "body60_plus_early1",
        "実体60%以上で入る。さらに1本以内にブレイク水準内へ戻れば撤退",
        lambda f: f["body_ratio"] >= 0.60,
        1,
    ),
]


def pct(value: float) -> str:
    return f"{value:.2f}%"


def num(value: float) -> str:
    return f"{value:.2f}"


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


def main() -> None:
    contexts: dict[str, pd.DataFrame] = {}
    configs: dict[str, dict] = {}
    for symbol in study.SYMBOLS:
        cfg = study.hybrid_cfg(symbol)
        df = study.load_instrument(symbol)
        df = df[(df.index.year >= study.YEAR_FROM) & (df.index.year <= study.YEAR_TO)]
        configs[symbol] = cfg
        contexts[symbol] = study.prepare_context(df, cfg)

    all_trade_parts = []
    summary_rows = []
    for rule_name, rule_desc, filter_func, early_bars in RULES:
        print(f"Rule={rule_name}")
        symbol_parts = []
        for symbol in study.SYMBOLS:
            trades = matrix.simulate_rule(
                symbol=symbol,
                ctx=contexts[symbol],
                cfg=configs[symbol],
                rule_name=rule_name,
                rule_desc=rule_desc,
                filter_func=filter_func,
                early_bars=early_bars,
            )
            symbol_parts.append(trades)
            row = matrix.summarize(trades)
            row.update({"symbol": symbol, "rule_name": rule_name, "rule_desc": rule_desc})
            summary_rows.append(row)
        combined = pd.concat(symbol_parts, ignore_index=True) if symbol_parts else pd.DataFrame()
        all_trade_parts.append(combined)
        row = matrix.summarize(combined)
        row.update({"symbol": "ALL", "rule_name": rule_name, "rule_desc": rule_desc})
        summary_rows.append(row)

    trades_all = pd.concat(all_trade_parts, ignore_index=True) if all_trade_parts else pd.DataFrame()
    summary = pd.DataFrame(summary_rows)

    all_summary = summary[summary["symbol"] == "ALL"].copy()
    base = all_summary[all_summary["rule_name"] == "baseline"].iloc[0]
    for col in ["trades", "win_rate", "total_r_after_cost", "avg_r_after_cost", "pf_after_cost", "max_dd_after_cost_r"]:
        all_summary[f"delta_{col}"] = all_summary[col] - float(base[col])

    summary.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    all_summary.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    trades_all.to_csv(OUT_DIR / "trades.csv", index=False)

    view = all_summary[
        [
            "rule_name",
            "trades",
            "win_rate",
            "total_r_after_cost",
            "avg_r_after_cost",
            "pf_after_cost",
            "max_dd_after_cost_r",
            "early_exit_rate",
            "delta_total_r_after_cost",
            "delta_win_rate",
            "delta_max_dd_after_cost_r",
        ]
    ].copy()
    for c in [
        "win_rate",
        "total_r_after_cost",
        "avg_r_after_cost",
        "pf_after_cost",
        "max_dd_after_cost_r",
        "early_exit_rate",
        "delta_total_r_after_cost",
        "delta_win_rate",
        "delta_max_dd_after_cost_r",
    ]:
        view[c] = view[c].map(num)

    by_symbol_view = summary[summary["symbol"] != "ALL"][
        [
            "symbol",
            "rule_name",
            "trades",
            "win_rate",
            "total_r_after_cost",
            "pf_after_cost",
            "max_dd_after_cost_r",
            "early_exit_rate",
        ]
    ].copy()
    for c in ["win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "early_exit_rate"]:
        by_symbol_view[c] = by_symbol_view[c].map(num)

    best_profit = all_summary.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False]).iloc[0]
    best_pf = all_summary[all_summary["trades"] >= 150].sort_values(["pf_after_cost", "total_r_after_cost"], ascending=[False, False]).iloc[0]
    best_dd = all_summary[all_summary["trades"] >= 150].sort_values(["max_dd_after_cost_r", "total_r_after_cost"], ascending=[True, False]).iloc[0]

    lines = [
        "# TrendBreakV1 騙し回避フィルタ 前後比較 2015-2024",
        "",
        "## 結論",
        "",
        f"- 総利益最大: `{best_profit['rule_name']}` / {best_profit['total_r_after_cost']:.2f}R / 勝率 {best_profit['win_rate']:.2f}% / PF {best_profit['pf_after_cost']:.3f}",
        f"- PF最大: `{best_pf['rule_name']}` / PF {best_pf['pf_after_cost']:.3f} / {best_pf['total_r_after_cost']:.2f}R",
        f"- DD最小: `{best_dd['rule_name']}` / Max DD {best_dd['max_dd_after_cost_r']:.2f}R / {best_dd['total_r_after_cost']:.2f}R",
        "",
        "## 全体比較",
        "",
        markdown_table(view),
        "",
        "## 通貨別比較",
        "",
        markdown_table(by_symbol_view),
        "",
        "## ルール定義",
        "",
        "- `baseline`: 現行TrendBreakV1 HYBRID。",
        "- `body60_filter`: シグナル足の実体が足全体の60%以上のときだけ入る。",
        "- `early_back_inside_1`: 通常通り入るが、エントリー後1本以内に終値がブレイク水準内へ戻ったら次足始値で撤退。",
        "- `body60_plus_early1`: 上記2つを同時に適用。",
        "",
        "## 注意",
        "",
        "この検証はPython上の再現バックテストです。TradingView/Pineの約定モデルやブローカー実約定とは完全一致しません。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")

    print("\nOverall:")
    print(
        all_summary[
            [
                "rule_name",
                "trades",
                "win_rate",
                "total_r_after_cost",
                "avg_r_after_cost",
                "pf_after_cost",
                "max_dd_after_cost_r",
                "early_exit_rate",
            ]
        ].to_string(index=False)
    )
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

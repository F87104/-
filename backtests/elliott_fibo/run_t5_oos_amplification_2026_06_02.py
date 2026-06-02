#!/usr/bin/env python3
"""
OOS amplification check for H4 T5 + MACD + BB.

True OOS cannot be increased without waiting for more future data.  This script
therefore keeps the rule definitions fixed and treats each historical year as a
pseudo-OOS slice.  The purpose is to check whether a T5 condition only works in
one lucky pocket, or whether it survives multiple unseen-like annual regimes.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv"
)
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_oos_amplification"
OUT.mkdir(parents=True, exist_ok=True)


MaskFn = Callable[[pd.DataFrame], pd.Series]


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    curve = r.astype(float).cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(r: pd.Series) -> int:
    cur = 0
    best = 0
    for value in r.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def metrics(df: pd.DataFrame) -> dict[str, float | int]:
    r = df["r_after_cost"].astype(float) if not df.empty else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def not_single_weak_rebreak(df: pd.DataFrame, macd_weak: float = 0.03) -> pd.Series:
    trigger = df["trigger_type"].astype(str)
    single_rebreak = trigger.eq("rebreak")
    weak = df["bb_pos"].gt(0.95) | df["macd_hist_slope3"].le(macd_weak)
    return ~(single_rebreak & weak)


def mask_rule(
    df: pd.DataFrame,
    *,
    bb_lo: float,
    bb_hi: float,
    recovery_max: int,
    macd_min: float,
    bb_width_max: float,
    guard: bool,
    adx_max: float | None = None,
) -> pd.Series:
    mask = (
        df["bb_pos"].between(bb_lo, bb_hi)
        & df["signal_recovery_bars"].le(recovery_max)
        & df["macd_hist_slope3"].gt(macd_min)
        & df["bb_width_atr"].le(bb_width_max)
    )
    if guard:
        mask &= not_single_weak_rebreak(df)
    if adx_max is not None:
        mask &= df["adx14"].le(adx_max)
    return mask.fillna(False)


RULES: dict[str, tuple[str, MaskFn]] = {
    "T5_CORE_STRICT_BEST": (
        "BB 0.75-1.00 / recovery<=16 / MACD>0.03 / BB width<=4ATR / all triggers",
        lambda df: mask_rule(
            df,
            bb_lo=0.75,
            bb_hi=1.00,
            recovery_max=16,
            macd_min=0.03,
            bb_width_max=4.0,
            guard=False,
        ),
    ),
    "T5_SAFE_LIVE_GUARD": (
        "BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard",
        lambda df: mask_rule(
            df,
            bb_lo=0.75,
            bb_hi=0.95,
            recovery_max=16,
            macd_min=0.0,
            bb_width_max=4.0,
            guard=True,
        ),
    ),
    "T5_CURRENT_STRICT_PRACTICAL": (
        "BB 0.60-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard",
        lambda df: mask_rule(
            df,
            bb_lo=0.60,
            bb_hi=0.95,
            recovery_max=16,
            macd_min=0.0,
            bb_width_max=4.0,
            guard=True,
        ),
    ),
    "T5_MORE_TRADES_ADX30": (
        "BB 0.75-1.00 / recovery<=16 / MACD>0 / BB width<=4ATR / ADX<=30 / all triggers",
        lambda df: mask_rule(
            df,
            bb_lo=0.75,
            bb_hi=1.00,
            recovery_max=16,
            macd_min=0.0,
            bb_width_max=4.0,
            guard=False,
            adx_max=30.0,
        ),
    ),
    "T5_WIDTH5_GUARD": (
        "BB 0.75-0.95 / recovery<=20 / MACD>0 / BB width<=5ATR / weak rebreak guard",
        lambda df: mask_rule(
            df,
            bb_lo=0.75,
            bb_hi=0.95,
            recovery_max=20,
            macd_min=0.0,
            bb_width_max=5.0,
            guard=True,
        ),
    ),
}


def fmt(value: object) -> str:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        if math.isnan(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_No rows_"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    headers = list(view.columns)
    rows = [[fmt(value) for value in row] for row in view.itertuples(index=False, name=None)]
    widths = [len(str(h)) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    out = []
    out.append("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    out.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows:
        out.append("| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |")
    return "\n".join(out)


def main() -> None:
    trades = pd.read_csv(SRC, parse_dates=["entry_time", "signal_time", "exit_time"])
    trades = trades.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    trades["entry_year"] = trades["entry_time"].dt.year.astype(int)

    summary_rows: list[dict] = []
    by_year_rows: list[dict] = []

    for rule_name, (rule_desc, mask_fn) in RULES.items():
        sample = trades[mask_fn(trades)].copy()
        sample["rule_name"] = rule_name
        sample.to_csv(OUT / f"{rule_name.lower()}_trades.csv", index=False)

        all_m = metrics(sample)
        true_oos = sample[sample["entry_year"].between(2025, 2026)]
        true_oos_m = metrics(true_oos)
        pseudo = sample[sample["entry_year"].between(2018, 2024)]
        pseudo_m = metrics(pseudo)

        active_years = 0
        positive_years = 0
        worst_year = 0.0
        for year, g in sample.groupby("entry_year"):
            ym = metrics(g)
            active_years += 1
            positive_years += int(ym["total_r"] > 0)
            worst_year = min(worst_year, float(ym["total_r"]))
            by_year_rows.append(
                {
                    "rule_name": rule_name,
                    "year": int(year),
                    **ym,
                }
            )

        summary_rows.append(
            {
                "rule_name": rule_name,
                "rule_desc": rule_desc,
                "all_trades": all_m["trades"],
                "all_win_rate": all_m["win_rate"],
                "all_total_r": all_m["total_r"],
                "all_avg_r": all_m["avg_r"],
                "all_pf": all_m["pf"],
                "all_max_dd_r": all_m["max_dd_r"],
                "pseudo_2018_2024_trades": pseudo_m["trades"],
                "pseudo_2018_2024_total_r": pseudo_m["total_r"],
                "pseudo_2018_2024_pf": pseudo_m["pf"],
                "true_oos_2025_2026_trades": true_oos_m["trades"],
                "true_oos_2025_2026_total_r": true_oos_m["total_r"],
                "active_years": active_years,
                "positive_years": positive_years,
                "positive_year_rate": positive_years / active_years * 100 if active_years else 0.0,
                "worst_year_total_r": worst_year,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values(
        ["positive_year_rate", "all_avg_r", "all_trades"], ascending=[False, False, False]
    )
    by_year = pd.DataFrame(by_year_rows).sort_values(["rule_name", "year"])

    summary.to_csv(OUT / "fixed_rules_summary.csv", index=False)
    by_year.to_csv(OUT / "fixed_rules_by_year.csv", index=False)

    best_rule = str(summary.iloc[0]["rule_name"]) if not summary.empty else ""
    best_by_year = by_year[by_year["rule_name"].eq(best_rule)].copy()

    report = [
        "# T5 OOS Amplification Check 2026-06-02",
        "",
        "## 目的",
        "",
        "2025-2026の真のOOSが4件しかない問題に対して、過去各年を疑似OOSとして扱い、固定ルールが複数年で崩れないかを確認した。",
        "",
        "重要: これは未来データを増やす検証ではない。真のOOS不足を補助するための年別ロバスト性チェック。",
        "",
        "## 固定ルール別サマリー",
        "",
        md_table(summary),
        "",
        "## 最上位ルールの年別成績",
        "",
        f"- Rule: `{best_rule}`",
        "",
        md_table(best_by_year),
        "",
        "## 読み方",
        "",
        "- `true_oos_2025_2026_trades` は本当の未来扱い。ここは時間が進まない限り自然には増えない。",
        "- `pseudo_2018_2024_trades` は固定条件を過去の各年へ当てた疑似OOS件数。",
        "- `positive_year_rate` が高いほど、一部の年だけに依存していない可能性が高い。",
        "- それでも最終判断にはTradingView照合とフォワード記録が必要。",
        "",
        "## 出力",
        "",
        "- `fixed_rules_summary.csv`",
        "- `fixed_rules_by_year.csv`",
        "- `<rule_name>_trades.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT / 'report_ja.md'}")
    print(summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

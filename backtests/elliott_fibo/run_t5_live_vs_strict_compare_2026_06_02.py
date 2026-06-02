#!/usr/bin/env python3
"""
Direct comparison for two practical H4 T5 rule candidates.

Normal live:
    BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR
    / weak single-rebreak guard

Strict:
    BB 0.85-0.95 / recovery<=16 / MACD>0.02 / BB width<=4ATR
    / weak single-rebreak guard

The goal is to decide whether the strict rule is a better live default, or only
an "A+ priority" tag inside the normal live rule.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "backtests/elliott_fibo/results_2026_05_24/t5_practical_robustness_audit/t5_broad_trades_2015_2026.csv"
)
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_live_vs_strict_compare"
OUT.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Rule:
    name: str
    label: str
    bb_lo: float
    bb_hi: float
    recovery_max: int
    macd_min: float
    bb_width_max: float
    guard_bb_hi: float = 0.95
    guard_macd_weak: float = 0.03


RULES = [
    Rule(
        name="NORMAL_LIVE",
        label="BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard",
        bb_lo=0.75,
        bb_hi=0.95,
        recovery_max=16,
        macd_min=0.0,
        bb_width_max=4.0,
    ),
    Rule(
        name="STRICT_A_PLUS",
        label="BB 0.85-0.95 / recovery<=16 / MACD>0.02 / BB width<=4ATR / weak rebreak guard",
        bb_lo=0.85,
        bb_hi=0.95,
        recovery_max=16,
        macd_min=0.02,
        bb_width_max=4.0,
    ),
]


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


def weak_rebreak_guard(df: pd.DataFrame, rule: Rule) -> pd.Series:
    trigger = df["trigger_type"].astype(str)
    weak = trigger.eq("rebreak") & (
        (df["bb_pos"] > rule.guard_bb_hi) | (df["macd_hist_slope3"] <= rule.guard_macd_weak)
    )
    return ~weak


def mask_for(df: pd.DataFrame, rule: Rule) -> pd.Series:
    mask = (
        df["bb_pos"].between(rule.bb_lo, rule.bb_hi)
        & df["signal_recovery_bars"].le(rule.recovery_max)
        & df["macd_hist_slope3"].gt(rule.macd_min)
        & df["bb_width_atr"].le(rule.bb_width_max)
        & weak_rebreak_guard(df, rule)
    )
    return mask.fillna(False)


def summarize(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(keys, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(keys, key))
        row.update(metrics(g))
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(keys)


def prefixed(sample: pd.DataFrame, prefix: str) -> dict[str, float | int]:
    return {f"{prefix}_{key}": value for key, value in metrics(sample).items()}


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
    lines = []
    lines.append("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    lines.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows:
        lines.append("| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |")
    return "\n".join(lines)


def add_trade_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["trade_id"] = (
        out["symbol"].astype(str)
        + "|"
        + out["entry_time"].astype(str)
        + "|"
        + out["trigger_type"].astype(str)
        + "|"
        + out["v_start_i"].astype(str)
        + "-"
        + out["v_extreme_i"].astype(str)
    )
    return out


def main() -> None:
    trades = pd.read_csv(SRC, parse_dates=["signal_time", "entry_time", "exit_time"])
    trades = add_trade_id(trades.sort_values(["entry_time", "symbol"]).reset_index(drop=True))

    summary_rows: list[dict] = []
    samples: dict[str, pd.DataFrame] = {}
    for rule in RULES:
        sample = trades[mask_for(trades, rule)].copy()
        sample["rule_name"] = rule.name
        sample["rule_label"] = rule.label
        samples[rule.name] = sample
        sample.to_csv(OUT / f"{rule.name.lower()}_trades.csv", index=False)
        summarize(sample, ["symbol"]).to_csv(OUT / f"{rule.name.lower()}_by_symbol.csv", index=False)
        summarize(sample, ["year"]).to_csv(OUT / f"{rule.name.lower()}_by_year.csv", index=False)
        summarize(sample, ["trigger_type"]).to_csv(OUT / f"{rule.name.lower()}_by_trigger.csv", index=False)
        summarize(sample, ["period"]).to_csv(OUT / f"{rule.name.lower()}_by_period.csv", index=False)

        research = sample[sample["period"].eq("Research_2015_2024")]
        oos = sample[sample["period"].eq("OOS_2025_2026")]
        row: dict[str, object] = {"rule_name": rule.name, "rule_label": rule.label}
        row.update(prefixed(sample, "all"))
        row.update(prefixed(research, "research"))
        row.update(prefixed(oos, "oos"))
        summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "summary.csv", index=False)

    normal = samples["NORMAL_LIVE"]
    strict = samples["STRICT_A_PLUS"]
    strict_ids = set(strict["trade_id"])
    normal_ids = set(normal["trade_id"])

    common = normal[normal["trade_id"].isin(strict_ids)].copy()
    normal_only = normal[~normal["trade_id"].isin(strict_ids)].copy()
    strict_only = strict[~strict["trade_id"].isin(normal_ids)].copy()
    removed_losers = normal_only[normal_only["r_after_cost"] <= 0].copy()
    removed_winners = normal_only[normal_only["r_after_cost"] > 0].copy()

    common.to_csv(OUT / "common_trades.csv", index=False)
    normal_only.to_csv(OUT / "normal_only_removed_by_strict.csv", index=False)
    strict_only.to_csv(OUT / "strict_only.csv", index=False)
    removed_losers.to_csv(OUT / "removed_losers.csv", index=False)
    removed_winners.to_csv(OUT / "removed_winners.csv", index=False)

    diff_summary = pd.DataFrame(
        [
            {"bucket": "common_kept_by_strict", **metrics(common)},
            {"bucket": "normal_only_removed_by_strict", **metrics(normal_only)},
            {"bucket": "removed_losers", **metrics(removed_losers)},
            {"bucket": "removed_winners", **metrics(removed_winners)},
            {"bucket": "strict_only", **metrics(strict_only)},
        ]
    )
    diff_summary.to_csv(OUT / "normal_vs_strict_diff_summary.csv", index=False)

    strict_by_symbol = summarize(strict, ["symbol"]).sort_values(["total_r", "avg_r"], ascending=False)
    strict_by_year = summarize(strict, ["year"]).sort_values(["year"])
    normal_by_symbol = summarize(normal, ["symbol"]).sort_values(["total_r", "avg_r"], ascending=False)
    normal_by_year = summarize(normal, ["year"]).sort_values(["year"])

    report = [
        "# T5 Live vs Strict Compare 2026-06-02",
        "",
        "## 比較した条件",
        "",
        "- `NORMAL_LIVE`: BB 0.75-0.95 / recovery<=16 / MACD>0 / BB width<=4ATR / weak rebreak guard",
        "- `STRICT_A_PLUS`: BB 0.85-0.95 / recovery<=16 / MACD>0.02 / BB width<=4ATR / weak rebreak guard",
        "",
        "## 全体比較",
        "",
        md_table(summary),
        "",
        "## Strictで何が削られたか",
        "",
        md_table(diff_summary),
        "",
        "## NORMAL 通貨別",
        "",
        md_table(normal_by_symbol),
        "",
        "## STRICT 通貨別",
        "",
        md_table(strict_by_symbol),
        "",
        "## NORMAL 年別",
        "",
        md_table(normal_by_year),
        "",
        "## STRICT 年別",
        "",
        md_table(strict_by_year),
        "",
        "## 暫定結論",
        "",
        "- Strictは平均RとPFを上げるが、件数とOOS件数を削る。",
        "- NORMALは実戦監視の本線、STRICTはA+優先タグとして扱うのが自然。",
        "- Strict単独を本番ルールにすると、OOS確認件数が薄くなるため過剰厳選リスクが残る。",
        "",
        "## 出力",
        "",
        "- `summary.csv`",
        "- `normal_live_trades.csv`",
        "- `strict_a_plus_trades.csv`",
        "- `normal_vs_strict_diff_summary.csv`",
        "- `normal_only_removed_by_strict.csv`",
        "- `removed_losers.csv`, `removed_winners.csv`",
        "- `*_by_symbol.csv`, `*_by_year.csv`, `*_by_trigger.csv`, `*_by_period.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT / 'report_ja.md'}")
    print(summary.to_string(index=False))
    print()
    print(diff_summary.to_string(index=False))


if __name__ == "__main__":
    main()

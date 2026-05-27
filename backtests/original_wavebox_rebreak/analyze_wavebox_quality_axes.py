#!/usr/bin/env python3
"""
Quality-axis audit for USDJPY H1 WaveBox Rebreak.

This script does not search new parameters. It classifies A/A+ trades by the
practical quality axes used for discretionary execution:

- retrace depth
- box position near P2
- H4 state
- breakout candle quality
- recent phase / not chasing a spent move
"""

from __future__ import annotations

import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_wavebox_rebreak as wb


THIS_DIR = Path(__file__).resolve().parent
BASE_DIR = THIS_DIR / "results_2026_05_25"
AUDIT_DIR = BASE_DIR / "usdjpy_v1_practical_audit"
OUT_DIR = BASE_DIR / "quality_axes_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODE_FILES = {
    "Strict": "trades_standard_v1_wave1_quality.csv",
    "Balanced": "trades_standard_v1_wave1_balanced.csv",
    "Expansion88": "trades_expanded_v1_082_ex16_wave1_balanced.csv",
}


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(values[values <= 0].sum())
    if gross_loss < 0:
        return gross_profit / abs(gross_loss)
    return math.inf if gross_profit > 0 else math.nan


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    curve = values.cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(values: pd.Series) -> int:
    cur = 0
    best = 0
    for value in values:
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def summarize(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    if group_cols is None:
        groups = [("ALL", df)]
        group_cols = ["group"]
    else:
        groups = list(df.groupby(group_cols, dropna=False, observed=False))

    rows = []
    for key, group in groups:
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = group["r_after_cost"]
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": int(len(group)),
                "win_rate": float((r > 0).mean() * 100),
                "total_r": float(r.sum()),
                "avg_r": float(r.mean()),
                "pf": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "tp_rate": float((group["exit_reason"] == "TP").mean() * 100),
            }
        )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.itertuples(index=False, name=None)]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]
    )


def load_h1() -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        m5, _coverage = wb.load_m5()
    return wb.add_indicators(wb.resample_ohlc(m5, "1h"), "H1")


def load_mode(mode: str, filename: str) -> pd.DataFrame:
    path = AUDIT_DIR / filename
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    df["mode"] = mode
    return df


def enrich_quality_axes(df: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for trade in df.itertuples(index=False):
        bar = h1.iloc[int(trade.signal_i)]
        bar_range = float(bar.high - bar.low)
        atr_est = (trade.box_high - trade.box_low) / trade.box_width_atr if trade.box_width_atr else math.nan
        move2 = abs(trade.p1 - trade.p2)
        box_mid = (trade.box_high + trade.box_low) / 2.0

        if trade.direction == "long":
            box_mid_recovery = (box_mid - trade.p2) / move2 if move2 else math.nan
            close_location = (bar.close - bar.low) / bar_range if bar_range else math.nan
            wick_against = (bar.high - bar.close) / bar_range if bar_range else math.nan
            break_margin_atr = (bar.close - (trade.box_high + 0.05 * atr_est)) / atr_est if atr_est else math.nan
        else:
            box_mid_recovery = (trade.p2 - box_mid) / move2 if move2 else math.nan
            close_location = (bar.high - bar.close) / bar_range if bar_range else math.nan
            wick_against = (bar.close - bar.low) / bar_range if bar_range else math.nan
            break_margin_atr = ((trade.box_low - 0.05 * atr_est) - bar.close) / atr_est if atr_est else math.nan

        rows.append(
            {
                "sig_open": float(bar.open),
                "sig_high": float(bar.high),
                "sig_low": float(bar.low),
                "sig_close": float(bar.close),
                "sig_range": bar_range,
                "atr_est": atr_est,
                "box_mid_recovery": box_mid_recovery,
                "close_location": close_location,
                "wick_against": wick_against,
                "break_margin_atr": break_margin_atr,
            }
        )

    out = pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)

    out["rank"] = "B"
    out.loc[out["upper_oppose"] == 0, "rank"] = "A"
    out.loc[out["retrace"] <= 0.618, "rank"] = "A+"

    out["retrace_bin"] = pd.cut(
        out["retrace"],
        [0.499, 0.618, 0.700, 0.786, 0.820, 0.886],
        labels=["50-61.8", "61.8-70", "70-78.6", "78.6-82", "82-88.6"],
        include_lowest=True,
    )
    out["box_position"] = pd.cut(
        out["box_mid_recovery"],
        [-99, 0.35, 0.50, 0.65, 99],
        labels=["bottom", "low-mid", "mid-high", "late"],
        include_lowest=True,
    )
    out["h4_state"] = np.where(out["upper_align"] > 0, "align", np.where(out["upper_oppose"] > 0, "oppose", "neutral"))
    out["break_quality"] = np.select(
        [
            (out["signal_body_ratio"] >= 0.65) & (out["close_location"] >= 0.70),
            (out["signal_body_ratio"] >= 0.45) & (out["close_location"] >= 0.60),
        ],
        ["strong_close", "ok_close"],
        default="weak_or_wick",
    )
    out["recent_phase"] = np.select(
        [
            (out["recovery"] <= 0.65) & (out["chase_atr"] <= 0.40),
            (out["recovery"] <= 0.80) & (out["chase_atr"] <= 0.60),
        ],
        ["early", "normal"],
        default="late_or_chase",
    )

    out["clean_a"] = (
        out["rank"].eq("A")
        & out["box_position"].isin(["bottom", "low-mid", "mid-high"])
        & out["break_quality"].isin(["strong_close", "ok_close"])
        & out["recent_phase"].isin(["early", "normal"])
    )
    out["action_class"] = np.select(
        [
            out["rank"].eq("A+"),
            out["clean_a"],
            out["rank"].eq("A"),
            out["rank"].eq("B") & out["mode"].eq("Strict"),
        ],
        ["GO_A_PLUS", "GO_CLEAN_A", "SELECTIVE_A", "OBSERVE_STRICT_B"],
        default="SKIP",
    )
    return out


def clean_rule_table(all_trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mode, df in all_trades.groupby("mode", observed=False):
        candidates = {
            "A+ only": df["rank"].eq("A+"),
            "A/A+ all": df["rank"].isin(["A", "A+"]),
            "A/A+ strong_or_ok_break": df["rank"].isin(["A", "A+"]) & df["break_quality"].isin(["strong_close", "ok_close"]),
            "A/A+ early_or_normal": df["rank"].isin(["A", "A+"]) & df["recent_phase"].isin(["early", "normal"]),
            "A/A+ clean_all": df["rank"].isin(["A", "A+"])
            & df["box_position"].isin(["bottom", "low-mid", "mid-high"])
            & df["break_quality"].isin(["strong_close", "ok_close"])
            & df["recent_phase"].isin(["early", "normal"]),
            "A+ or clean A": df["rank"].eq("A+") | df["clean_a"],
            "B only": df["rank"].eq("B"),
        }
        for rule, mask in candidates.items():
            summary = summarize(df[mask]).iloc[0].to_dict() if mask.any() else {"trades": 0}
            summary["mode"] = mode
            summary["rule"] = rule
            rows.append(summary)
    return pd.DataFrame(rows)


def axis_table(all_trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    focus = all_trades[all_trades["rank"].isin(["A", "A+"])]
    for mode, mode_df in focus.groupby("mode", observed=False):
        for axis in ["retrace_bin", "box_position", "h4_state", "break_quality", "recent_phase", "action_class"]:
            summary = summarize(mode_df, [axis])
            if summary.empty:
                continue
            summary.insert(0, "axis", axis)
            summary.insert(0, "mode", mode)
            summary = summary.rename(columns={axis: "bucket"})
            rows.append(summary)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def write_report(mode_summary: pd.DataFrame, rank_summary: pd.DataFrame, axis_summary: pd.DataFrame, clean_summary: pd.DataFrame) -> None:
    lines = [
        "# USDJPY H1 WaveBox Quality Axes Audit",
        "",
        "## 結論",
        "",
        "- A+は最優先で打つ候補。",
        "- Aは無条件ではなく、Box位置・ブレイク足・直近フェーズがきれいなものを優先する。",
        "- StrictのBは観察または小ロット。ExpansionのBは捨てる。",
        "- 1波をBalancedへ緩めるのは許容範囲。戻し上限を82%へ広げるとBが弱くなる。",
        "",
        "## Mode Summary",
        "",
        markdown_table(mode_summary, 20),
        "",
        "## Rank Summary",
        "",
        markdown_table(rank_summary, 40),
        "",
        "## Quality Axis Summary",
        "",
        markdown_table(axis_summary.sort_values(["mode", "axis", "bucket"]), 160),
        "",
        "## Clean Rule Candidates",
        "",
        markdown_table(clean_summary.sort_values(["mode", "total_r"], ascending=[True, False]), 120),
        "",
        "## 実戦ルール案",
        "",
        "- `GO_A_PLUS`: A+。通常の実戦候補。",
        "- `GO_CLEAN_A`: Aかつ、Box位置が遅くなく、ブレイク足がstrong/ok、直近がearly/normal。",
        "- `SELECTIVE_A`: Aだが何かが弱い。裁量確認。",
        "- `OBSERVE_STRICT_B`: StrictモードのBのみ。小ロットまたは記録。",
        "- `SKIP`: Expansion B、弱いA、条件緩和で出た低品質候補。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    h1 = load_h1()
    frames = []
    for mode, filename in MODE_FILES.items():
        enriched = enrich_quality_axes(load_mode(mode, filename), h1)
        enriched.to_csv(OUT_DIR / f"trades_{mode.lower()}_quality_axes.csv", index=False)
        frames.append(enriched)
    all_trades = pd.concat(frames, ignore_index=True)

    mode_summary = summarize(all_trades, ["mode"]).sort_values("total_r", ascending=False)
    rank_summary = summarize(all_trades, ["mode", "rank"]).sort_values(["mode", "rank"])
    axis_summary = axis_table(all_trades)
    clean_summary = clean_rule_table(all_trades)

    mode_summary.to_csv(OUT_DIR / "mode_summary.csv", index=False)
    rank_summary.to_csv(OUT_DIR / "rank_summary.csv", index=False)
    axis_summary.to_csv(OUT_DIR / "axis_summary.csv", index=False)
    clean_summary.to_csv(OUT_DIR / "clean_rule_candidates.csv", index=False)
    write_report(mode_summary, rank_summary, axis_summary, clean_summary)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(mode_summary.to_string(index=False))
    print(clean_summary.sort_values(["mode", "total_r"], ascending=[True, False]).head(30).to_string(index=False))


if __name__ == "__main__":
    main()

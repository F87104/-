#!/usr/bin/env python3
"""
Entry slimming study for the H4 low-stagnation short setup.

The goal is not to add more trades.  It starts from the current practical
entry line and looks for simple rules that remove weak entries while staying
easy to implement in Pine.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import markdown_table
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_d1_regime_filter_study" / "enriched_with_prev_d1.csv"
OUT_DIR = THIS_DIR / "results_2026_05_29" / "h4_low_stag_entry_slimming"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"
CORE4 = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY"}
NO_AUD_USD = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY", "SILVER"}
LOOKBACK_PRIORITY = {120: 0, 90: 1, 180: 2, 240: 3, 60: 4, 360: 5, 480: 6, 720: 7}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time", "prev_d1_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def actual_trade_sample(sample: pd.DataFrame) -> pd.DataFrame:
    if sample.empty:
        return sample.copy()
    out = sample[sample["trigger_mode"].eq("stagnation")].copy()
    if out.empty:
        return out
    out["__lookback_priority"] = out["lookback_bars"].map(LOOKBACK_PRIORITY).fillna(99)
    out = out.sort_values(["symbol", "entry_time", "__lookback_priority", "lookback_bars"])
    out = out.drop_duplicates(["symbol", "entry_time"], keep="first")
    return out.drop(columns=["__lookback_priority"])


def practical_mask(df: pd.DataFrame) -> pd.Series:
    return df["adx14"].ge(30) & df["risk_atr_at_signal"].le(1.5) & df["bb_width_atr"].between(3.0, 8.0)


def quality_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_depth_atr"].ge(0.10) & df["break_close_location"].le(0.50)


def strict_mask(df: pd.DataFrame) -> pd.Series:
    return quality_mask(df) & (df["support_age_bars"].gt(10) | df["break_depth_atr"].ge(0.20))


def d1_rsi_mask(df: pd.DataFrame) -> pd.Series:
    return df["prev_d1_rsi14"].between(35, 55)


def l60_guard(df: pd.DataFrame, max_age: int = 24, min_depth: float = 0.25) -> pd.Series:
    short_lb = df["lookback_bars"].eq(60)
    strong_short = df["support_age_bars"].le(max_age) & df["break_depth_atr"].ge(min_depth)
    return ~short_lb | strong_short


def score(row: dict) -> dict:
    trades = int(row.get("trades", 0))
    total_r = float(row.get("total_r", 0.0))
    avg_r = float(row.get("avg_r", 0.0))
    pf_val = float(row.get("pf", 0.0))
    pf = 12.0 if math.isinf(pf_val) else pf_val
    dd = float(row.get("max_dd_r", 0.0))
    row["score"] = total_r + avg_r * 6.0 + min(pf, 12.0) * 1.25 - dd * 1.0 + min(trades, 18) * 0.08
    return row


def metric_row(sample_name: str, rule: str, sample: pd.DataFrame) -> dict:
    row = {"sample": sample_name, "rule": rule}
    row.update(metrics(sample, R_COL))
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample.columns else ""
    return score(row)


def build_samples(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    practical = df[practical_mask(df)].copy()
    return {
        "practical_no_AUD_USD": actual_trade_sample(practical[practical["symbol"].isin(NO_AUD_USD)].copy()),
        "practical_core4": actual_trade_sample(practical[practical["symbol"].isin(CORE4)].copy()),
    }


def rule_summary(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sample_name, sample in samples.items():
        rules = {
            "baseline": pd.Series(True, index=sample.index),
            "D1_RSI35_55_quality": d1_rsi_mask(sample) & quality_mask(sample),
            "D1_RSI35_55_strict_current": d1_rsi_mask(sample) & strict_mask(sample),
            "D1_RSI35_55_strict_no_L60": d1_rsi_mask(sample) & strict_mask(sample) & sample["lookback_bars"].ne(60),
            "D1_RSI35_55_strict_L60_guard_age24_depth0.25": d1_rsi_mask(sample)
            & strict_mask(sample)
            & l60_guard(sample, 24, 0.25),
            "D1_RSI35_55_strict_L60_guard_age24_depth0.20": d1_rsi_mask(sample)
            & strict_mask(sample)
            & l60_guard(sample, 24, 0.20),
            "D1_RSI35_55_strict_L60_guard_age24_depth0.30": d1_rsi_mask(sample)
            & strict_mask(sample)
            & l60_guard(sample, 24, 0.30),
        }
        for rule, mask in rules.items():
            rows.append(metric_row(sample_name, rule, sample[mask].copy()))
    return pd.DataFrame(rows).sort_values(["score", "total_r"], ascending=False)


def l60_sweep(sample: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base = sample[d1_rsi_mask(sample) & strict_mask(sample)].copy()
    for max_age in [12, 18, 24, 30, 36, 48, 60]:
        for min_depth in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
            picked = base[l60_guard(base, max_age, min_depth)].copy()
            row = {"max_l60_age": max_age, "min_l60_depth_atr": min_depth}
            row.update(metrics(picked, R_COL))
            rows.append(score(row))
    out = pd.DataFrame(rows)
    return out.sort_values(["score", "trades"], ascending=False)


def failure_audit(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sample = samples["practical_no_AUD_USD"].copy()
    current = sample[d1_rsi_mask(sample) & strict_mask(sample)].copy()
    current["keep_with_l60_guard"] = l60_guard(current, 24, 0.25)
    current["outcome"] = current[R_COL].apply(lambda v: "loss" if v <= 0 else "win")
    cols = [
        "outcome",
        "keep_with_l60_guard",
        "symbol",
        "entry_time",
        "period",
        R_COL,
        "lookback_bars",
        "support_age_bars",
        "break_depth_atr",
        "break_close_location",
        "risk_atr_at_signal",
        "adx14",
        "bb_width_atr",
        "bb_pos",
        "prev_d1_rsi14",
        "prev_d1_adx14",
        "prev_d1_bb_pos",
        "prev_d1_close_location",
        "base_exit_reason",
    ]
    return current[cols].sort_values(["outcome", "entry_time"])


def period_symbol_breakdown(sample: pd.DataFrame) -> pd.DataFrame:
    picked = sample[d1_rsi_mask(sample) & strict_mask(sample) & l60_guard(sample, 24, 0.25)].copy()
    rows = []
    for key in ["period", "symbol", "lookback_bars"]:
        for value, group in picked.groupby(key):
            row = {"group": key, "value": value}
            row.update(metrics(group, R_COL))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["group", "total_r"], ascending=[True, False])


def write_report(summary: pd.DataFrame, sweep: pd.DataFrame, audit: pd.DataFrame, breakdown: pd.DataFrame) -> None:
    summary_cols = [
        "sample",
        "rule",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "max_losing_streak",
        "symbols",
    ]
    sweep_cols = ["max_l60_age", "min_l60_depth_atr", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    audit_cols = [
        "outcome",
        "keep_with_l60_guard",
        "symbol",
        "entry_time",
        R_COL,
        "lookback_bars",
        "support_age_bars",
        "break_depth_atr",
        "break_close_location",
        "prev_d1_rsi14",
    ]
    breakdown_cols = ["group", "value", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]

    report = [
        "# H4 Low Stag Entry Slimming Study",
        "",
        "Status: 検証途中。エントリー精度を上げるため、余計な短期lookback候補を削る研究。",
        "",
        "## 結論",
        "",
        "- 現行の `D1 RSI35-55 + H4厳選` の負け3件は、すべて `lookback=60` に集中していた。",
        "- 90本以上のlookbackは今回の実戦本線サンプルでは負けが出ていない。",
        "- ただし60本を全除外すると勝ちも2件落とすため、60本だけ条件を強くするのがよい。",
        "- 推奨追加条件: `lookback != 60 or (support_age <= 24 and break_depth_atr >= 0.25)`。",
        "",
        "## ルール比較",
        "",
        markdown_table(summary[summary_cols], 80),
        "",
        "## 60本lookback条件スイープ",
        "",
        markdown_table(sweep[sweep_cols].head(20), 40),
        "",
        "## 現行D1厳選の勝敗監査",
        "",
        markdown_table(audit[audit_cols], 80),
        "",
        "## 推奨ルールの内訳",
        "",
        markdown_table(breakdown[breakdown_cols], 80),
        "",
        "## 実装案",
        "",
        "1. H4安値停滞の基本条件、ADX、risk、BB幅、H4品質、前日D1 RSI 35-55 は維持。",
        "2. `lookback=60` だけは、`support_age <= 24` かつ `break_depth_atr >= 0.25` を追加。",
        "3. これにより、短期の浅いだまし割れや、60本に見えるだけの中途半端な戻り売りを削る。",
        "4. 90本以上は現在の本線では残す。ここをさらに削ると件数が少なすぎる。",
        "",
        "## 注意",
        "",
        "- 11件・全勝は強すぎる数字なので、過信しない。これは本番化ではなく、Pine照合とフォワード監視用の厳選案。",
        "- 60本lookbackは短期の支持線割れなので、長いレンジ割れよりもだましが増えやすい、という解釈が自然。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    df = load_data()
    samples = build_samples(df)
    summary = rule_summary(samples)
    sweep = l60_sweep(samples["practical_no_AUD_USD"])
    audit = failure_audit(samples)
    breakdown = period_symbol_breakdown(samples["practical_no_AUD_USD"])

    summary.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    sweep.to_csv(OUT_DIR / "l60_guard_sweep.csv", index=False)
    audit.to_csv(OUT_DIR / "current_d1_strict_failure_audit.csv", index=False)
    breakdown.to_csv(OUT_DIR / "recommended_breakdown.csv", index=False)
    write_report(summary, sweep, audit, breakdown)

    print(f"Wrote {OUT_DIR}")
    print(summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Precision hardening for the H4 low-stagnation short setup.

This is the implementation-readiness pass. It uses the deduplicated practical
entry view and checks whether additional price-action filters improve precision
without creating a rule that is impossible to explain in Pine.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import markdown_table
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_followup_validation" / "enriched_followup.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_stagnation_precision_hardening"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_R = "base_r_after_cost"
CORE4 = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY"}
NO_AUD_USD = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY", "SILVER"}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def actual_trade_sample(sample: pd.DataFrame) -> pd.DataFrame:
    if sample.empty:
        return sample.copy()
    out = sample[sample["trigger_mode"].eq("stagnation")].copy()
    if out.empty:
        return out
    priority = {120: 0, 90: 1, 180: 2, 240: 3, 60: 4, 360: 5, 480: 6, 720: 7}
    out["__lookback_priority"] = out["lookback_bars"].map(priority).fillna(99)
    out = out.sort_values(["symbol", "entry_time", "__lookback_priority", "lookback_bars"])
    out = out.drop_duplicates(["symbol", "entry_time"], keep="first")
    return out.drop(columns=["__lookback_priority"])


def base_primary(df: pd.DataFrame) -> pd.DataFrame:
    mask = (
        df["trigger_mode"].eq("stagnation")
        & df["lookback_bars"].eq(120)
        & df["adx14"].ge(30)
        & df["risk_atr_at_signal"].le(1.5)
        & df["bb_width_atr"].between(3.0, 8.0)
    )
    return actual_trade_sample(df[mask].copy())


def quality_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_depth_atr"].ge(0.10) & df["break_close_location"].le(0.50)


def fresh_support_mask(df: pd.DataFrame) -> pd.Series:
    # When the broken low was made very recently, require a more decisive break.
    return df["support_age_bars"].gt(10) | df["break_depth_atr"].ge(0.20)


def strict_mask(df: pd.DataFrame) -> pd.Series:
    return quality_mask(df) & fresh_support_mask(df)


def age_observation_mask(df: pd.DataFrame) -> pd.Series:
    return df["support_age_bars"].between(30, 119)


def add_score(row: dict) -> dict:
    trades = int(row.get("trades", 0))
    total_r = float(row.get("total_r", 0.0))
    avg_r = float(row.get("avg_r", 0.0))
    pf = float(row.get("pf", 0.0)) if math.isfinite(float(row.get("pf", 0.0))) else 8.0
    dd = float(row.get("max_dd_r", 0.0))
    row["score"] = total_r + avg_r * 8.0 + min(pf, 8.0) * 1.5 - dd * 0.8 + min(trades, 20) * 0.1
    return row


def rule_samples(primary: pd.DataFrame) -> list[tuple[str, str, pd.DataFrame]]:
    samples = [
        ("base_all", "全通貨のPrimary L120", primary),
        ("base_no_AUD_USD", "AUDJPY/USDJPYを除外", primary[primary["symbol"].isin(NO_AUD_USD)].copy()),
        ("base_core4", "core4のみ", primary[primary["symbol"].isin(CORE4)].copy()),
    ]

    rows: list[tuple[str, str, pd.DataFrame]] = []
    for base_name, label, sample in samples:
        rows.append((base_name, label, sample))
        rows.append((f"{base_name}_quality", f"{label} + 品質フィルタ", sample[quality_mask(sample)].copy()))
        rows.append((f"{base_name}_strict", f"{label} + 厳選フィルタ", sample[strict_mask(sample)].copy()))
        rows.append((f"{base_name}_age30_119", f"{label} + support age 30-119", sample[age_observation_mask(sample)].copy()))
    return rows


def summarize_rules(primary: pd.DataFrame) -> pd.DataFrame:
    exit_cols = [
        ("fixed_2R", BASE_R),
        ("fixed_1_5R", "mgmt_fixed_1_5R_r_after_cost"),
        ("no_1R_by_12bars", "mgmt_fixed_2R_no_1R_by_12bars_r_after_cost"),
        ("half_1R_BE_rest_2R", "mgmt_half_1R_BE_rest_2R_r_after_cost"),
        ("mid6_exit", "mid_retest_exit_r_after_cost"),
    ]
    rows = []
    for rule, label, sample in rule_samples(primary):
        for exit_name, r_col in exit_cols:
            row = {"rule": rule, "label": label, "exit_model": exit_name}
            row.update(metrics(sample, r_col))
            row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
            row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) else ""
            rows.append(add_score(row))
    return pd.DataFrame(rows).sort_values(["score", "total_r"], ascending=False)


def summarize_periods(primary: pd.DataFrame) -> pd.DataFrame:
    chosen = {
        "base_core4": primary[primary["symbol"].isin(CORE4)].copy(),
        "core4_quality": primary[primary["symbol"].isin(CORE4) & quality_mask(primary)].copy(),
        "core4_strict": primary[primary["symbol"].isin(CORE4) & strict_mask(primary)].copy(),
        "no_AUD_USD_strict": primary[primary["symbol"].isin(NO_AUD_USD) & strict_mask(primary)].copy(),
    }
    rows = []
    for rule, sample in chosen.items():
        for period, group in sample.groupby("period"):
            row = {"rule": rule, "period": period}
            row.update(metrics(group, BASE_R))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["rule", "period"])


def summarize_symbols(primary: pd.DataFrame) -> pd.DataFrame:
    chosen = {
        "base_core4": primary[primary["symbol"].isin(CORE4)].copy(),
        "core4_quality": primary[primary["symbol"].isin(CORE4) & quality_mask(primary)].copy(),
        "core4_strict": primary[primary["symbol"].isin(CORE4) & strict_mask(primary)].copy(),
        "no_AUD_USD_strict": primary[primary["symbol"].isin(NO_AUD_USD) & strict_mask(primary)].copy(),
    }
    rows = []
    for rule, sample in chosen.items():
        for symbol, group in sample.groupby("symbol"):
            row = {"rule": rule, "symbol": symbol}
            row.update(metrics(group, BASE_R))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["rule", "total_r"], ascending=[True, False])


def failure_audit(primary: pd.DataFrame) -> pd.DataFrame:
    core = primary[primary["symbol"].isin(CORE4)].copy()
    core["passes_quality"] = quality_mask(core)
    core["passes_fresh_support"] = fresh_support_mask(core)
    core["passes_strict"] = strict_mask(core)
    core["audit"] = np.where(
        core[BASE_R].le(0),
        "loss",
        np.where(core["passes_strict"], "kept_winner", "dropped_winner"),
    )
    cols = [
        "audit",
        "symbol",
        "entry_time",
        "period",
        BASE_R,
        "support_age_bars",
        "break_depth_atr",
        "break_close_location",
        "break_body_ratio",
        "pre_break_regime",
        "passes_quality",
        "passes_fresh_support",
        "passes_strict",
    ]
    return core[cols].sort_values(["audit", "entry_time"])


def threshold_sweep(primary: pd.DataFrame) -> pd.DataFrame:
    core = primary[primary["symbol"].isin(CORE4)].copy()
    rows = []
    for depth in [0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20, 0.25]:
        for fresh_depth in [0.15, 0.175, 0.20, 0.225, 0.25]:
            sample = core[
                core["break_depth_atr"].ge(depth)
                & core["break_close_location"].le(0.50)
                & (core["support_age_bars"].gt(10) | core["break_depth_atr"].ge(fresh_depth))
            ].copy()
            row = {"depth_min": depth, "fresh_depth_min": fresh_depth}
            row.update(metrics(sample, BASE_R))
            rows.append(add_score(row))
    return pd.DataFrame(rows).sort_values(["score", "trades"], ascending=False)


def write_report(
    primary: pd.DataFrame,
    rule_summary: pd.DataFrame,
    period_summary: pd.DataFrame,
    symbol_summary: pd.DataFrame,
    audit: pd.DataFrame,
    sweep: pd.DataFrame,
) -> None:
    rule_cols = ["rule", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak", "symbols"]
    period_cols = ["rule", "period", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    symbol_cols = ["rule", "symbol", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    audit_cols = [
        "audit",
        "symbol",
        "entry_time",
        "period",
        BASE_R,
        "support_age_bars",
        "break_depth_atr",
        "break_close_location",
        "pre_break_regime",
        "passes_strict",
    ]
    sweep_cols = ["depth_min", "fresh_depth_min", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]

    important = rule_summary[
        rule_summary["rule"].isin(
            [
                "base_all",
                "base_core4",
                "base_core4_quality",
                "base_core4_strict",
                "base_core4_age30_119",
                "base_no_AUD_USD_strict",
            ]
        )
        & rule_summary["exit_model"].isin(["fixed_2R", "fixed_1_5R", "no_1R_by_12bars"])
    ].copy()
    top_rules = rule_summary[rule_summary["trades"].ge(5)].head(24).copy()
    top_sweep = sweep[sweep["trades"].ge(6)].head(20).copy()

    lines = [
        "# H4 安値停滞 精度向上検証",
        "",
        "Status: 検証途中。Pine実装に向けて、説明しやすい品質フィルタだけで精度を上げられるかを確認。",
        "",
        "## 母集団",
        "",
        "- Primary L120: H4で過去120本安値更新後の安値停滞下抜け。",
        "- 共通フィルタ: ADX>=30、risk<=1.5ATR、BB幅3-8ATR。",
        "- 同一通貨・同一エントリー時刻は1回に重複除去。",
        "",
        "## 追加した品質フィルタ",
        "",
        "- 品質フィルタ: 下抜け深さ `>=0.10ATR`、かつ下抜け足の終値位置 `<=0.50`。",
        "- 厳選フィルタ: 品質フィルタに加えて、support age が10本以内なら下抜け深さ `>=0.20ATR` を要求。",
        "- 目的: 浅い下抜けや、新しい安値を弱く割っただけの形を避ける。",
        "",
        "## 重要ルール比較",
        "",
        markdown_table(important[rule_cols], 80),
        "",
        "## スコア上位",
        "",
        markdown_table(top_rules[rule_cols], 80),
        "",
        "## 期間別",
        "",
        markdown_table(period_summary[period_cols], 80) if not period_summary.empty else "_No rows._",
        "",
        "## 通貨別",
        "",
        markdown_table(symbol_summary[symbol_cols], 80) if not symbol_summary.empty else "_No rows._",
        "",
        "## 負け・除外監査",
        "",
        markdown_table(audit[audit_cols], 80) if not audit.empty else "_No rows._",
        "",
        "## 閾値感度",
        "",
        markdown_table(top_sweep[sweep_cols], 80) if not top_sweep.empty else "_No rows._",
        "",
        "## 暫定解釈",
        "",
        "- `Primary L120 core4` はそのままでも良いが、浅い下抜けを避けると精度が上がる。",
        "- `break_depth>=0.10ATR` は、core4の負け3件中2件を落とし、勝ちを落とさなかった。",
        "- `support age<=10ならbreak_depth>=0.20ATR` は、残った弱いfresh support負けを落とし、OOSのGBPJPY勝ちを残した。",
        "- 厳選フィルタ後のcore4は8件全勝だが、件数が少ない。これは本番ロットではなく、Pineの `実戦用シグナル` 候補。",
        "- SILVERを戻すと件数と総Rは増えるが、SILVERの急落継続失敗を1件拾う。精度重視ならcore4維持。",
        "- 出口は固定2Rがまだ最も素直。12本撤退はPrimary L120では改善が小さく、広いPractical条件用の補助案。",
        "",
        "## 実装候補",
        "",
        "1. 候補ラベル: Primary L120 core4。",
        "2. 実戦候補ラベル: 候補 + `break_depth>=0.10ATR` + `break_close_location<=0.50`。",
        "3. 厳選ラベル: 実戦候補 + `support_age>10 or break_depth>=0.20ATR`。",
        "4. support60-119はエントリー条件ではなく、強い観察タグとして表示。",
        "",
        "## 出力CSV",
        "",
        "- `rule_summary.csv`",
        "- `period_summary.csv`",
        "- `symbol_summary.csv`",
        "- `failure_audit.csv`",
        "- `threshold_sweep.csv`",
        "- `primary_trades.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_data()
    primary = base_primary(df)
    primary.to_csv(OUT_DIR / "primary_trades.csv", index=False)
    rule_summary = summarize_rules(primary)
    period_summary = summarize_periods(primary)
    symbol_summary = summarize_symbols(primary)
    audit = failure_audit(primary)
    sweep = threshold_sweep(primary)
    rule_summary.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    period_summary.to_csv(OUT_DIR / "period_summary.csv", index=False)
    symbol_summary.to_csv(OUT_DIR / "symbol_summary.csv", index=False)
    audit.to_csv(OUT_DIR / "failure_audit.csv", index=False)
    sweep.to_csv(OUT_DIR / "threshold_sweep.csv", index=False)
    write_report(primary, rule_summary, period_summary, symbol_summary, audit, sweep)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(rule_summary[rule_summary["trades"].ge(5)].head(20).to_string(index=False))


if __name__ == "__main__":
    main()

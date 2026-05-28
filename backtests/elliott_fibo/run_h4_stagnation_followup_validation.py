#!/usr/bin/env python3
"""
Follow-up validation for the H4 low-stagnation breakdown idea.

This script starts from the enriched stagnation dataset and checks whether the
strong observations are usable rules:
- support age around 60-119 H4 bars
- symbol concentration, especially GBPJPY vs weak symbols
- fixed 2R vs a 12-bar no-progress exit
- whether mid-range retests are better used as a warning than as an exit
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, markdown_table, resample_ohlc
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import ExitSpec, metrics, simulate_exit


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_deep_dive" / "enriched_stagnation.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_stagnation_followup_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
BASE_R = "base_r_after_cost"
NO12_R = "mgmt_fixed_2R_no_1R_by_12bars_r_after_cost"
MID_EXIT_R = "mid_retest_exit_r_after_cost"

BAD_SYMBOLS = {"AUDJPY", "USDJPY"}
CORE_SYMBOLS = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY"}


def load_enriched() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    df["hit_1r_by_12"] = df["hit_1r_bar_48"].between(0, 12)
    df["r_mid6_then_no12"] = np.where(
        df["retest_zone_mid_6"].astype(bool) & ~df["hit_1r_by_12"].astype(bool),
        df[NO12_R],
        df[BASE_R],
    )
    df["r_no12_if_mid_retest"] = np.where(
        df["retest_zone_mid_6"].astype(bool) & ~df["hit_1r_by_12"].astype(bool),
        df[NO12_R],
        df[BASE_R],
    )
    return df


def practical_mask(df: pd.DataFrame) -> pd.Series:
    return df["adx14"].ge(30) & df["risk_atr_at_signal"].le(1.5) & df["bb_width_atr"].between(3.0, 8.0)


def primary_mask(df: pd.DataFrame) -> pd.Series:
    return practical_mask(df) & df["trigger_mode"].eq("stagnation") & df["lookback_bars"].eq(120)


def support60_119_mask(df: pd.DataFrame) -> pd.Series:
    return practical_mask(df) & df["support_age_bars"].between(60, 119)


def clean_depth_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_depth_atr"].between(0.05, 0.40)


def close_near_low_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_close_location"].le(0.25)


def large_body_mask(df: pd.DataFrame) -> pd.Series:
    return df["break_body_ratio"].ge(0.60)


def no_bad_symbols_mask(df: pd.DataFrame) -> pd.Series:
    return ~df["symbol"].isin(BAD_SYMBOLS)


def core_symbols_mask(df: pd.DataFrame) -> pd.Series:
    return df["symbol"].isin(CORE_SYMBOLS)


def actual_trade_sample(sample: pd.DataFrame) -> pd.DataFrame:
    """Convert a research grid sample into one practical entry per symbol/time."""
    if sample.empty:
        return sample.copy()
    out = sample[sample["trigger_mode"].eq("stagnation")].copy()
    if out.empty:
        return out
    lookback_priority = {120: 0, 90: 1, 180: 2, 240: 3, 60: 4, 360: 5, 480: 6, 720: 7}
    out["__lookback_priority"] = out["lookback_bars"].map(lookback_priority).fillna(99)
    out = out.sort_values(["symbol", "entry_time", "__lookback_priority", "lookback_bars"])
    out = out.drop_duplicates(["symbol", "entry_time"], keep="first")
    return out.drop(columns=["__lookback_priority"])


def rule_masks(df: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    practical = practical_mask(df)
    support60 = support60_119_mask(df)
    no_bad = no_bad_symbols_mask(df)
    core = core_symbols_mask(df)
    clean_depth = clean_depth_mask(df)
    close_near = close_near_low_mask(df)
    large_body = large_body_mask(df)
    gbpjpy = df["symbol"].eq("GBPJPY")
    return [
        ("primary_L120_all", primary_mask(df)),
        ("primary_L120_no_AUD_USD", primary_mask(df) & no_bad),
        ("primary_L120_core4", primary_mask(df) & core),
        ("primary_L120_GBPJPY", primary_mask(df) & gbpjpy),
        ("practical_all_lookbacks", practical),
        ("practical_no_AUD_USD", practical & no_bad),
        ("practical_core4", practical & core),
        ("practical_GBPJPY", practical & gbpjpy),
        ("support60_119_all", support60),
        ("support60_119_no_AUD_USD", support60 & no_bad),
        ("support60_119_core4", support60 & core),
        ("support60_119_GBPJPY", support60 & gbpjpy),
        ("support60_119_clean_depth", support60 & clean_depth),
        ("support60_119_close_near_low", support60 & close_near),
        ("support60_119_depth_close", support60 & clean_depth & close_near),
        ("support60_119_close_large_body", support60 & close_near & large_body),
        ("no_bad_clean_depth_close", practical & no_bad & clean_depth & close_near),
        ("core4_clean_depth_close", practical & core & clean_depth & close_near),
    ]


def add_score(row: dict) -> dict:
    trades = row.get("trades", 0)
    total_r = row.get("total_r", 0.0)
    avg_r = row.get("avg_r", 0.0)
    pf = row.get("pf", 0.0)
    dd = row.get("max_dd_r", 0.0)
    if not math.isfinite(float(pf)):
        pf = 5.0
    row["score"] = float(total_r) + float(avg_r) * 10.0 + min(float(pf), 5.0) * 2.0 - float(dd) * 0.5 + min(int(trades), 50) * 0.05
    return row


def summarize_rule_exits(df: pd.DataFrame) -> pd.DataFrame:
    exit_cols = [
        ("fixed_2R", BASE_R),
        ("fixed_2R_no_1R_by_12bars", NO12_R),
        ("mid6_exit", MID_EXIT_R),
        ("mid6_then_no12_only", "r_mid6_then_no12"),
        ("fixed_1_5R", "mgmt_fixed_1_5R_r_after_cost"),
        ("half_1R_BE_rest_2R", "mgmt_half_1R_BE_rest_2R_r_after_cost"),
    ]
    rows = []
    for rule_name, mask in rule_masks(df):
        sample = actual_trade_sample(df[mask.fillna(False)].copy())
        for exit_name, r_col in exit_cols:
            row = {"rule": rule_name, "exit_model": exit_name}
            row.update(metrics(sample, r_col))
            row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
            row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample else ""
            rows.append(add_score(row))
    out = pd.DataFrame(rows)
    return out.sort_values(["score", "total_r"], ascending=False)


def summarize_periods(df: pd.DataFrame) -> pd.DataFrame:
    selected = {
        "primary_L120_all": primary_mask(df),
        "primary_L120_no_AUD_USD": primary_mask(df) & no_bad_symbols_mask(df),
        "support60_119_all": support60_119_mask(df),
        "support60_119_no_AUD_USD": support60_119_mask(df) & no_bad_symbols_mask(df),
        "practical_no_AUD_USD": practical_mask(df) & no_bad_symbols_mask(df),
        "practical_GBPJPY": practical_mask(df) & df["symbol"].eq("GBPJPY"),
    }
    rows = []
    for name, mask in selected.items():
        sample = actual_trade_sample(df[mask.fillna(False)].copy())
        for exit_name, r_col in [("fixed_2R", BASE_R), ("fixed_2R_no_1R_by_12bars", NO12_R)]:
            for period, group in sample.groupby("period"):
                row = {"rule": name, "exit_model": exit_name, "period": period}
                row.update(metrics(group, r_col))
                rows.append(row)
    return pd.DataFrame(rows).sort_values(["rule", "exit_model", "period"])


def summarize_support_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    sample = actual_trade_sample(df[support60_119_mask(df)].copy())
    rows = []
    for symbol, group in sample.groupby("symbol"):
        for exit_name, r_col in [("fixed_2R", BASE_R), ("fixed_2R_no_1R_by_12bars", NO12_R)]:
            row = {"symbol": symbol, "exit_model": exit_name}
            row.update(metrics(group, r_col))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["exit_model", "total_r"], ascending=[True, False])


def summarize_lookback_inside_support(df: pd.DataFrame) -> pd.DataFrame:
    sample = actual_trade_sample(df[support60_119_mask(df)].copy())
    rows = []
    for (lookback, label), group in sample.groupby(["lookback_bars", "lookback_label"]):
        for exit_name, r_col in [("fixed_2R", BASE_R), ("fixed_2R_no_1R_by_12bars", NO12_R)]:
            row = {"lookback_bars": int(lookback), "lookback_label": label, "exit_model": exit_name}
            row.update(metrics(group, r_col))
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["exit_model", "lookback_bars"])


def support_age_window_sweep(df: pd.DataFrame) -> pd.DataFrame:
    base = df[practical_mask(df)].copy()
    windows = [
        (24, 59),
        (40, 89),
        (50, 99),
        (60, 119),
        (70, 139),
        (80, 159),
        (100, 199),
        (120, 239),
    ]
    symbol_scopes = [
        ("all_symbols", pd.Series(True, index=base.index)),
        ("no_AUD_USD", no_bad_symbols_mask(base)),
        ("core4", core_symbols_mask(base)),
        ("GBPJPY", base["symbol"].eq("GBPJPY")),
    ]
    rows = []
    for scope_name, scope_mask in symbol_scopes:
        for lo, hi in windows:
            sample = actual_trade_sample(base[scope_mask.fillna(False) & base["support_age_bars"].between(lo, hi)].copy())
            for exit_name, r_col in [("fixed_2R", BASE_R), ("fixed_2R_no_1R_by_12bars", NO12_R)]:
                row = {"scope": scope_name, "age_window": f"{lo}-{hi}", "exit_model": exit_name}
                row.update(metrics(sample, r_col))
                rows.append(add_score(row))
    return pd.DataFrame(rows).sort_values(["scope", "exit_model", "score"], ascending=[True, True, False])


def load_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for symbol in SYMBOLS:
        frames[symbol] = add_extended_features(add_indicators(resample_ohlc(load_instrument(symbol), TIMEFRAME)))
    return frames


def add_time_stop_columns(df: pd.DataFrame, bars_list: list[int]) -> pd.DataFrame:
    frames = load_frames()
    out = df.copy()
    practical_indices = out[practical_mask(out)].index
    for bars in bars_list:
        col = f"r_no_1r_by_{bars}bars"
        values: dict[int, float] = {}
        spec = ExitSpec(f"fixed_2R_no_1R_by_{bars}bars", target_rr=2.0, no_progress_bars=bars + 1)
        for idx, row in out.loc[practical_indices].iterrows():
            result = simulate_exit(
                frames[str(row["symbol"])],
                str(row["symbol"]),
                int(row["entry_i"]),
                float(row["stop"]),
                spec,
            )
            values[int(idx)] = float(result["r_after_cost_model"]) if result is not None else np.nan
        out[col] = np.nan
        for idx, value in values.items():
            out.at[idx, col] = value
    return out


def time_stop_sweep(df: pd.DataFrame, bars_list: list[int]) -> pd.DataFrame:
    samples = {
        "primary_L120_all": primary_mask(df),
        "practical_all": practical_mask(df),
        "practical_no_AUD_USD": practical_mask(df) & no_bad_symbols_mask(df),
        "practical_GBPJPY": practical_mask(df) & df["symbol"].eq("GBPJPY"),
        "support60_119_all": support60_119_mask(df),
        "support60_119_no_AUD_USD": support60_119_mask(df) & no_bad_symbols_mask(df),
        "support60_119_GBPJPY": support60_119_mask(df) & df["symbol"].eq("GBPJPY"),
    }
    rows = []
    for sample_name, mask in samples.items():
        sample = actual_trade_sample(df[mask.fillna(False)].copy())
        base_row = {"sample": sample_name, "exit_model": "fixed_2R", "bars": 0}
        base_row.update(metrics(sample, BASE_R))
        rows.append(add_score(base_row))
        for bars in bars_list:
            r_col = f"r_no_1r_by_{bars}bars"
            row = {"sample": sample_name, "exit_model": f"no_1R_by_{bars}bars", "bars": bars}
            row.update(metrics(sample, r_col))
            rows.append(add_score(row))
    return pd.DataFrame(rows).sort_values(["sample", "score"], ascending=[True, False])


def symbol_exclusion_sweep(df: pd.DataFrame) -> pd.DataFrame:
    practical = df[practical_mask(df)].copy()
    scopes = [
        ("all_symbols", practical.index),
        ("exclude_AUDJPY", practical[~practical["symbol"].eq("AUDJPY")].index),
        ("exclude_USDJPY", practical[~practical["symbol"].eq("USDJPY")].index),
        ("exclude_AUDJPY_USDJPY", practical[~practical["symbol"].isin(BAD_SYMBOLS)].index),
        ("core4_only", practical[practical["symbol"].isin(CORE_SYMBOLS)].index),
        ("GBPJPY_only", practical[practical["symbol"].eq("GBPJPY")].index),
    ]
    rows = []
    for scope_name, idx in scopes:
        sample = actual_trade_sample(practical.loc[idx].copy())
        support_sample = actual_trade_sample(sample[sample["support_age_bars"].between(60, 119)].copy())
        for sample_name, group in [("practical", sample), ("support60_119", support_sample)]:
            for exit_name, r_col in [("fixed_2R", BASE_R), ("fixed_2R_no_1R_by_12bars", NO12_R)]:
                row = {"scope": scope_name, "sample": sample_name, "exit_model": exit_name}
                row.update(metrics(group, r_col))
                rows.append(add_score(row))
    return pd.DataFrame(rows).sort_values(["sample", "exit_model", "score"], ascending=[True, True, False])


def write_report(
    rule_summary: pd.DataFrame,
    period_summary: pd.DataFrame,
    support_by_symbol: pd.DataFrame,
    support_lookback: pd.DataFrame,
    age_sweep: pd.DataFrame,
    time_sweep: pd.DataFrame,
    exclusion_sweep: pd.DataFrame,
) -> None:
    rule_cols = ["rule", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak", "symbols"]
    period_cols = ["rule", "exit_model", "period", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    basic_cols = ["symbol", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    lookback_cols = ["lookback_label", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    age_cols = ["scope", "age_window", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    time_cols = ["sample", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]
    exclusion_cols = ["scope", "sample", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]

    important_rules = rule_summary[
        rule_summary["rule"].isin(
            [
                "primary_L120_all",
                "primary_L120_no_AUD_USD",
                "practical_no_AUD_USD",
                "practical_GBPJPY",
                "support60_119_all",
                "support60_119_no_AUD_USD",
                "support60_119_core4",
                "support60_119_GBPJPY",
                "support60_119_depth_close",
            ]
        )
        & rule_summary["exit_model"].isin(["fixed_2R", "fixed_2R_no_1R_by_12bars", "mid6_then_no12_only"])
    ].copy()
    best_rules = rule_summary[rule_summary["trades"].ge(10)].head(20).copy()
    best_age = age_sweep[age_sweep["trades"].ge(5)].head(32).copy()
    best_time = time_sweep[time_sweep["trades"].ge(10)].copy()

    lines = [
        "# H4 安値停滞 追加検証",
        "",
        "Status: 検証途中。前回の発見を、入口ルールと出口管理に分けて再検証。",
        "",
        "注: 実戦想定に近づけるため、`trigger_mode=stagnation` を基準にし、同じ通貨・同じエントリー時刻は1回だけに重複除去して集計。",
        "",
        "## 検証した仮説",
        "",
        "- `サポート保持60-119本` は本当に強いのか。",
        "- `GBPJPY寄せ` と `AUDJPY/USDJPY除外` は有効か。",
        "- `6本以内に戻る` は即撤退ではなく、12本時間切れと組み合わせるべきか。",
        "- `12本以内に1R未達なら撤退` は、特定サンプルだけの偶然か。",
        "",
        "## 重要ルール比較",
        "",
        markdown_table(important_rules[rule_cols], 80),
        "",
        "## スコア上位ルール",
        "",
        markdown_table(best_rules[rule_cols], 80),
        "",
        "## サポート60-119本: 通貨別",
        "",
        markdown_table(support_by_symbol[basic_cols], 80) if not support_by_symbol.empty else "_No rows._",
        "",
        "## サポート60-119本: lookback別",
        "",
        markdown_table(support_lookback[lookback_cols], 80) if not support_lookback.empty else "_No rows._",
        "",
        "## サポート保持期間の近傍スイープ",
        "",
        markdown_table(best_age[age_cols], 80) if not best_age.empty else "_No rows._",
        "",
        "## 時間切れ撤退スイープ",
        "",
        markdown_table(best_time[time_cols], 120) if not best_time.empty else "_No rows._",
        "",
        "## 通貨除外スイープ",
        "",
        markdown_table(exclusion_sweep[exclusion_cols], 120) if not exclusion_sweep.empty else "_No rows._",
        "",
        "## 期間別チェック",
        "",
        markdown_table(period_summary[period_cols], 120) if not period_summary.empty else "_No rows._",
        "",
        "## 暫定解釈",
        "",
        "- 重複除去後、`サポート保持60-119本` は 26件ではなく実質8件。優秀だが件数不足なので、採用条件ではなく強い観察タグとして扱う。",
        "- 実戦候補として一番きれいに残ったのは `Primary L120 + core4`。core4は GBPJPY/CHFJPY/XAUUSD/EURJPY で、SILVER/AUDJPY/USDJPYを外す形。",
        "- AUDJPY/USDJPY除外は、広いPracticalでもPrimaryでも改善方向。特にAUDJPYはサポート60-119本の負けを作っていた。",
        "- GBPJPY単独は強いが、重複除去後は11件だけ。汎用ルールというより、優先監視通貨として扱う。",
        "- 12本以内1R未達撤退は、Primary L120ではほぼ効果なし。広いPracticalやsupport60-119では改善するが、これは補助管理案。",
        "- 6本撤退はやはり早すぎる。10-12本が候補で、16-20本も大きく崩れない。24本は固定2Rとほぼ同じ。",
        "- 6本以内の停滞レンジ中央戻りは、入口では使えない。即撤退より、10-12本以内1R未達の時間切れ管理で吸収する方が自然。",
        "",
        "## 出力CSV",
        "",
        "- `rule_exit_summary.csv`",
        "- `period_summary.csv`",
        "- `support60_119_by_symbol.csv`",
        "- `support60_119_by_lookback.csv`",
        "- `support_age_window_sweep.csv`",
        "- `time_stop_sweep.csv`",
        "- `symbol_exclusion_sweep.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_enriched()
    bars_list = [4, 6, 8, 10, 12, 16, 20, 24]
    df_with_time = add_time_stop_columns(df, bars_list)
    df_with_time.to_csv(OUT_DIR / "enriched_followup.csv", index=False)

    rule_summary = summarize_rule_exits(df_with_time)
    period_summary = summarize_periods(df_with_time)
    support_by_symbol = summarize_support_by_symbol(df_with_time)
    support_lookback = summarize_lookback_inside_support(df_with_time)
    age_sweep = support_age_window_sweep(df_with_time)
    time_sweep = time_stop_sweep(df_with_time, bars_list)
    exclusion_sweep = symbol_exclusion_sweep(df_with_time)

    rule_summary.to_csv(OUT_DIR / "rule_exit_summary.csv", index=False)
    period_summary.to_csv(OUT_DIR / "period_summary.csv", index=False)
    support_by_symbol.to_csv(OUT_DIR / "support60_119_by_symbol.csv", index=False)
    support_lookback.to_csv(OUT_DIR / "support60_119_by_lookback.csv", index=False)
    age_sweep.to_csv(OUT_DIR / "support_age_window_sweep.csv", index=False)
    time_sweep.to_csv(OUT_DIR / "time_stop_sweep.csv", index=False)
    exclusion_sweep.to_csv(OUT_DIR / "symbol_exclusion_sweep.csv", index=False)
    write_report(rule_summary, period_summary, support_by_symbol, support_lookback, age_sweep, time_sweep, exclusion_sweep)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(rule_summary[rule_summary["trades"].ge(10)].head(20).to_string(index=False))


if __name__ == "__main__":
    main()

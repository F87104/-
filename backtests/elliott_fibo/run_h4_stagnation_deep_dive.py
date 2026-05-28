#!/usr/bin/env python3
"""
H4 low-stagnation breakdown deep dive.

This script analyzes the H4 low-break stagnation trigger from angles that are
not covered by simple lookback length:
- quality of the stagnation range
- strength of the breakdown candle
- whether the breakdown immediately follows through
- whether price retests the broken range before reaching profit
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, direction_cost_r, load_instrument, markdown_table, resample_ohlc
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import ExitSpec, classify_period, metrics, simulate_exit


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "low_break_lookback_exit_study" / "signals.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_stagnation_deep_dive"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
R_COL = "base_r_after_cost"

MANAGEMENT_SPECS = [
    ExitSpec("fixed_1_5R", target_rr=1.5),
    ExitSpec("fixed_2R_no_1R_by_6bars", target_rr=2.0, no_progress_bars=7),
    ExitSpec("fixed_2R_no_1R_by_12bars", target_rr=2.0, no_progress_bars=13),
    ExitSpec("BE_after_1R_to_2R", target_rr=2.0, be_after_1r=True),
    ExitSpec("half_1R_BE_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True),
    ExitSpec("half_1R_trail1ATR_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True, trail_atr_after_1r=1.0),
]


def bucketize(value: float, cuts: list[float], labels: list[str]) -> str:
    if not math.isfinite(value):
        return "unknown"
    for cut, label in zip(cuts, labels):
        if value <= cut:
            return label
    return labels[-1]


def load_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for symbol in SYMBOLS:
        frames[symbol] = add_extended_features(add_indicators(resample_ohlc(load_instrument(symbol), TIMEFRAME)))
    return frames


def first_hit_bar_short(df: pd.DataFrame, entry_i: int, level: float, max_bars: int) -> int | None:
    end_i = min(len(df) - 1, entry_i + max_bars)
    for j in range(entry_i, end_i + 1):
        if float(df["low"].iloc[j]) <= level:
            return j - entry_i
    return None


def simulate_mid_retest_exit(
    df: pd.DataFrame,
    symbol: str,
    entry_i: int,
    entry: float,
    stop: float,
    target: float,
    risk: float,
    zone_mid: float,
    retest_bars: int = 6,
    max_hold_bars: int = 180,
) -> dict:
    exit_i = min(len(df) - 1, entry_i + max_hold_bars)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "max_hold"
    for j in range(entry_i, min(len(df), entry_i + max_hold_bars + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        if (j - entry_i) <= retest_bars and hi >= zone_mid:
            exit_i = j
            exit_price = zone_mid
            reason = "mid_retest_exit_6"
            break
        if hi >= stop:
            exit_i = j
            exit_price = stop
            reason = "SL"
            break
        if lo <= target:
            exit_i = j
            exit_price = target
            reason = "TP"
            break
    clean, after = direction_cost_r(symbol, "short", entry, exit_price, risk)
    return {
        "mid_retest_exit_time": df.index[exit_i],
        "mid_retest_exit_price": exit_price,
        "mid_retest_exit_reason": reason,
        "mid_retest_exit_r_clean": clean,
        "mid_retest_exit_r_after_cost": after,
    }


def add_stagnation_features(signals: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for row in signals.to_dict("records"):
        if "stagnation" not in str(row["trigger_type"]):
            continue

        symbol = str(row["symbol"])
        df = frames[symbol]
        trigger_i = int(row["trigger_i"])
        entry_i = int(row["entry_i"])
        if trigger_i < 4 or entry_i >= len(df):
            continue

        atr_i = float(df["atr"].iloc[trigger_i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue

        zone = df.iloc[trigger_i - 3 : trigger_i]
        sig_bar = df.iloc[trigger_i]
        zone_high = float(zone["high"].max())
        zone_low = float(zone["low"].min())
        zone_mid = (zone_high + zone_low) / 2.0
        zone_range = zone_high - zone_low
        zone_range_atr = zone_range / atr_i
        zone_body_avg = float(((zone["close"] - zone["open"]).abs() / atr_i).mean())
        zone_close_drift_atr = float((zone["close"].iloc[-1] - zone["close"].iloc[0]) / atr_i)
        zone_high_drift_atr = float((zone["high"].iloc[-1] - zone["high"].iloc[0]) / atr_i)
        zone_low_drift_atr = float((zone["low"].iloc[-1] - zone["low"].iloc[0]) / atr_i)
        zone_closes_below_mid = int((zone["close"] <= zone_mid).sum())

        sig_open = float(sig_bar["open"])
        sig_high = float(sig_bar["high"])
        sig_low = float(sig_bar["low"])
        sig_close = float(sig_bar["close"])
        sig_range = max(sig_high - sig_low, np.nan)
        break_depth_atr = (zone_low - sig_close) / atr_i
        break_body_atr = abs(sig_close - sig_open) / atr_i
        break_body_ratio = abs(sig_close - sig_open) / sig_range if sig_range and sig_range > 0 else np.nan
        break_close_location = (sig_close - sig_low) / sig_range if sig_range and sig_range > 0 else np.nan
        broke_prior_low_atr = (float(row["prior_low"]) - sig_close) / atr_i
        zone_high_vs_prior_low_atr = (zone_high - float(row["prior_low"])) / atr_i
        zone_low_vs_prior_low_atr = (zone_low - float(row["prior_low"])) / atr_i

        entry = float(row["entry"])
        risk = float(row["risk"])
        stop = float(row["stop"])
        max_i = min(len(df) - 1, entry_i + 48)
        after = df.iloc[entry_i : max_i + 1]
        low_3 = float(after.iloc[: min(len(after), 3)]["low"].min()) if len(after) else np.nan
        low_6 = float(after.iloc[: min(len(after), 6)]["low"].min()) if len(after) else np.nan
        high_3 = float(after.iloc[: min(len(after), 3)]["high"].max()) if len(after) else np.nan
        high_6 = float(after.iloc[: min(len(after), 6)]["high"].max()) if len(after) else np.nan
        mfe_3bar_r = (entry - low_3) / risk if risk > 0 and math.isfinite(low_3) else np.nan
        mfe_6bar_r = (entry - low_6) / risk if risk > 0 and math.isfinite(low_6) else np.nan
        mae_3bar_r = (high_3 - entry) / risk if risk > 0 and math.isfinite(high_3) else np.nan
        mae_6bar_r = (high_6 - entry) / risk if risk > 0 and math.isfinite(high_6) else np.nan
        hit_1r_bar = first_hit_bar_short(df, entry_i, entry - risk, 48) if risk > 0 else None
        mid_exit = simulate_mid_retest_exit(
            df=df,
            symbol=symbol,
            entry_i=entry_i,
            entry=entry,
            stop=stop,
            target=float(row["base_target_2r"]),
            risk=risk,
            zone_mid=zone_mid,
        )
        management_exits = {}
        for spec in MANAGEMENT_SPECS:
            exit_out = simulate_exit(df, symbol, entry_i, stop, spec)
            if exit_out is None:
                continue
            prefix = f"mgmt_{spec.name}"
            management_exits[f"{prefix}_r_after_cost"] = exit_out["r_after_cost_model"]
            management_exits[f"{prefix}_reason"] = exit_out["exit_reason_model"]
            management_exits[f"{prefix}_bars_held"] = exit_out["bars_held_model"]

        retest_zone_low_3 = bool(math.isfinite(high_3) and high_3 >= zone_low)
        retest_zone_mid_6 = bool(math.isfinite(high_6) and high_6 >= zone_mid)
        retest_zone_high_6 = bool(math.isfinite(high_6) and high_6 >= zone_high)
        stopped_within_6 = bool(math.isfinite(high_6) and high_6 >= stop)

        out = {
            **row,
            "zone_high": zone_high,
            "zone_low": zone_low,
            "zone_mid": zone_mid,
            "zone_range_atr": zone_range_atr,
            "zone_body_avg_atr": zone_body_avg,
            "zone_close_drift_atr": zone_close_drift_atr,
            "zone_high_drift_atr": zone_high_drift_atr,
            "zone_low_drift_atr": zone_low_drift_atr,
            "zone_closes_below_mid": zone_closes_below_mid,
            "break_depth_atr": break_depth_atr,
            "break_body_atr": break_body_atr,
            "break_body_ratio": break_body_ratio,
            "break_close_location": break_close_location,
            "broke_prior_low_atr": broke_prior_low_atr,
            "zone_high_vs_prior_low_atr": zone_high_vs_prior_low_atr,
            "zone_low_vs_prior_low_atr": zone_low_vs_prior_low_atr,
            "mfe_3bar_r": mfe_3bar_r,
            "mfe_6bar_r": mfe_6bar_r,
            "mae_3bar_r": mae_3bar_r,
            "mae_6bar_r": mae_6bar_r,
            "hit_1r_bar_48": -1 if hit_1r_bar is None else int(hit_1r_bar),
            "hit_1r_within_3": bool(hit_1r_bar is not None and hit_1r_bar <= 3),
            "hit_1r_within_6": bool(hit_1r_bar is not None and hit_1r_bar <= 6),
            "retest_zone_low_3": retest_zone_low_3,
            "retest_zone_mid_6": retest_zone_mid_6,
            "retest_zone_high_6": retest_zone_high_6,
            "stopped_within_6": stopped_within_6,
            **mid_exit,
            **management_exits,
        }

        out["zone_range_bucket"] = bucketize(zone_range_atr, [0.40, 0.70, 1.00], ["00_tight_<=0.40", "01_mid_0.40-0.70", "02_wide_0.70-1.00", "03_very_wide_>1.00"])
        out["break_depth_bucket"] = bucketize(break_depth_atr, [0.05, 0.20, 0.40], ["00_shallow_<=0.05", "01_clean_0.05-0.20", "02_strong_0.20-0.40", "03_too_deep_>0.40"])
        out["break_close_location_bucket"] = bucketize(break_close_location, [0.25, 0.50, 0.75], ["00_close_near_low", "01_lower_mid", "02_upper_mid", "03_close_high"])
        out["break_body_bucket"] = bucketize(break_body_ratio, [0.35, 0.60], ["00_small_body", "01_medium_body", "02_large_body"])
        out["zone_drift_bucket"] = bucketize(zone_close_drift_atr, [-0.20, 0.20], ["00_drifting_down", "01_flat", "02_drifting_up"])
        out["risk_bucket"] = bucketize(float(row["risk_atr_at_signal"]), [1.0, 1.5, 2.0], ["00_<=1ATR", "01_1-1.5ATR", "02_1.5-2ATR", "03_>2ATR"])
        out["bb_width_bucket"] = bucketize(float(row["bb_width_atr"]), [3.0, 5.0, 8.0], ["00_<=3ATR", "01_3-5ATR", "02_5-8ATR", "03_>8ATR"])
        out["bb_pos_bucket"] = bucketize(float(row["bb_pos"]), [0.0, 0.25, 0.50], ["00_below_lower", "01_0-0.25", "02_0.25-0.50", "03_>0.50"])
        out["bars_after_break_bucket"] = bucketize(float(row["bars_after_break"]), [12, 24, 36], ["00_<=12", "01_13-24", "02_25-36", "03_37-48"])
        out["followthrough_bucket"] = "00_hit_1r_<=3" if out["hit_1r_within_3"] else "01_hit_1r_<=6" if out["hit_1r_within_6"] else "02_no_fast_1r"
        out["retest_bucket"] = "00_no_mid_retest_6" if not retest_zone_mid_6 else "01_mid_retest_6"
        rows.append(out)

    enriched = pd.DataFrame(rows)
    if not enriched.empty:
        for col in ["signal_time", "entry_time", "base_exit_time"]:
            if col in enriched.columns:
                enriched[col] = pd.to_datetime(enriched[col], format="mixed", errors="coerce")
        enriched["period"] = enriched["entry_time"].map(classify_period)
    return enriched


def primary_mask(df: pd.DataFrame) -> pd.Series:
    return (
        df["trigger_mode"].eq("stagnation")
        & df["lookback_bars"].eq(120)
        & df["adx14"].ge(30)
        & df["risk_atr_at_signal"].le(1.5)
        & df["bb_width_atr"].between(3.0, 8.0)
    )


def practical_mask(df: pd.DataFrame) -> pd.Series:
    return df["adx14"].ge(30) & df["risk_atr_at_signal"].le(1.5) & df["bb_width_atr"].between(3.0, 8.0)


def summarize_by(df: pd.DataFrame, group_col: str, sample_name: str) -> pd.DataFrame:
    rows = []
    for key, group in df.groupby(group_col, dropna=False):
        row = {"sample": sample_name, "group": group_col, "bucket": key}
        row.update(metrics(group, R_COL))
        row["avg_mfe_r"] = float(group["base_mfe_r"].mean()) if len(group) else 0.0
        row["hit_1r_within_3_rate"] = float(group["hit_1r_within_3"].mean() * 100) if len(group) else 0.0
        row["hit_1r_within_6_rate"] = float(group["hit_1r_within_6"].mean() * 100) if len(group) else 0.0
        row["retest_mid_6_rate"] = float(group["retest_zone_mid_6"].mean() * 100) if len(group) else 0.0
        row["giveback_1r_to_loss_rate"] = float((group["base_mfe_r"].ge(1.0) & group[R_COL].le(0)).mean() * 100) if len(group) else 0.0
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_r", "avg_r"], ascending=False)


def all_summaries(enriched: pd.DataFrame) -> pd.DataFrame:
    samples = {
        "primary_L120_ADX30_RISK1_5_BBW3_8": enriched[primary_mask(enriched)].copy(),
        "practical_all_lookbacks": enriched[practical_mask(enriched)].copy(),
        "all_stagnation": enriched[enriched["trigger_mode"].eq("stagnation")].copy(),
    }
    group_cols = [
        "symbol",
        "period",
        "zone_range_bucket",
        "break_depth_bucket",
        "break_close_location_bucket",
        "break_body_bucket",
        "zone_drift_bucket",
        "risk_bucket",
        "bb_width_bucket",
        "bb_pos_bucket",
        "bars_after_break_bucket",
        "support_age_bucket",
        "pre_break_regime",
        "followthrough_bucket",
        "retest_bucket",
    ]
    frames = []
    for sample_name, sample in samples.items():
        for col in group_cols:
            frames.append(summarize_by(sample, col, sample_name))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def combo_summaries(enriched: pd.DataFrame) -> pd.DataFrame:
    sample = enriched[practical_mask(enriched)].copy()
    combos = [
        (
            "tight_or_mid_zone_clean_break_no_mid_retest",
            sample["zone_range_atr"].le(0.70) & sample["break_depth_atr"].between(0.05, 0.40) & ~sample["retest_zone_mid_6"],
        ),
        (
            "support_age_60_119_clean_break",
            sample["support_age_bucket"].eq("02_60-119bars") & sample["break_depth_atr"].between(0.05, 0.40),
        ),
        (
            "close_near_low_large_body",
            sample["break_close_location"].le(0.25) & sample["break_body_ratio"].ge(0.60),
        ),
        (
            "fast_followthrough_1r_6bars",
            sample["hit_1r_within_6"],
        ),
        (
            "danger_mid_retest_6",
            sample["retest_zone_mid_6"],
        ),
        (
            "danger_wide_zone_or_big_risk",
            sample["zone_range_atr"].gt(0.70) | sample["risk_atr_at_signal"].gt(1.5),
        ),
    ]
    rows = []
    for name, mask in combos:
        group = sample[mask.fillna(False)]
        row = {"combo": name}
        row.update(metrics(group, R_COL))
        row["avg_mfe_r"] = float(group["base_mfe_r"].mean()) if len(group) else 0.0
        row["hit_1r_within_6_rate"] = float(group["hit_1r_within_6"].mean() * 100) if len(group) else 0.0
        row["retest_mid_6_rate"] = float(group["retest_zone_mid_6"].mean() * 100) if len(group) else 0.0
        rows.append(row)
    return pd.DataFrame(rows).sort_values("total_r", ascending=False)


def management_summaries(enriched: pd.DataFrame) -> pd.DataFrame:
    samples = {
        "primary_L120_ADX30_RISK1_5_BBW3_8": enriched[primary_mask(enriched)].copy(),
        "practical_all_lookbacks": enriched[practical_mask(enriched)].copy(),
        "support_age_60_119_practical": enriched[practical_mask(enriched) & enriched["support_age_bucket"].eq("02_60-119bars")].copy(),
    }
    r_cols = [
        ("base_fixed_2R", R_COL),
        ("fixed_1_5R", "mgmt_fixed_1_5R_r_after_cost"),
        ("fixed_2R_no_1R_by_6bars", "mgmt_fixed_2R_no_1R_by_6bars_r_after_cost"),
        ("fixed_2R_no_1R_by_12bars", "mgmt_fixed_2R_no_1R_by_12bars_r_after_cost"),
        ("BE_after_1R_to_2R", "mgmt_BE_after_1R_to_2R_r_after_cost"),
        ("half_1R_BE_rest_2R", "mgmt_half_1R_BE_rest_2R_r_after_cost"),
        ("half_1R_trail1ATR_rest_2R", "mgmt_half_1R_trail1ATR_rest_2R_r_after_cost"),
        ("exit_if_mid_retest_within_6", "mid_retest_exit_r_after_cost"),
    ]
    rows = []
    for sample_name, sample in samples.items():
        for exit_name, r_col in r_cols:
            row = {"sample": sample_name, "exit_model": exit_name}
            row.update(metrics(sample, r_col))
            rows.append(row)
    return pd.DataFrame(rows)


def write_report(enriched: pd.DataFrame, summaries: pd.DataFrame, combos: pd.DataFrame, management: pd.DataFrame) -> None:
    primary = enriched[primary_mask(enriched)].copy()
    practical = enriched[practical_mask(enriched)].copy()

    def pick(sample: str, group: str) -> pd.DataFrame:
        return summaries[summaries["sample"].eq(sample) & summaries["group"].eq(group)].copy()

    cols = [
        "bucket",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "avg_mfe_r",
        "hit_1r_within_6_rate",
        "retest_mid_6_rate",
        "giveback_1r_to_loss_rate",
    ]
    combo_cols = [
        "combo",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "avg_mfe_r",
        "hit_1r_within_6_rate",
        "retest_mid_6_rate",
    ]
    mgmt_cols = ["sample", "exit_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]
    lines = [
        "# H4 安値停滞ブレイク 深掘り分析",
        "",
        "Status: 検証途中。H4 1ヶ月安値更新後の安値停滞ブレイクを、停滞レンジ品質とブレイク後の動きで再分析。",
        "",
        "## 見た角度",
        "",
        "- 停滞レンジの狭さ: シグナル前3本の高安幅をATR換算。",
        "- 下抜け足の強さ: 停滞レンジ安値からどれだけ終値で下に抜けたか、足の実体、終値位置。",
        "- サポートの見え方: 安値保持期間、接触回数、レンジ割れ/トレンド継続の分類。",
        "- 直後フォロースルー: エントリー後3〜6本で1Rに届くか。",
        "- 戻りやすさ: エントリー後6本以内に停滞レンジ中央へ戻るか。",
        "",
        "## ベースサンプル",
        "",
        "| sample | trades | total_r | avg_r | PF | maxDD |",
        "|---|---:|---:|---:|---:|---:|",
        f"| primary L120 + ADX30 + risk<=1.5 + BB幅3-8 | {len(primary)} | {metrics(primary, R_COL)['total_r']:.2f} | {metrics(primary, R_COL)['avg_r']:.2f} | {metrics(primary, R_COL)['pf']:.2f} | {metrics(primary, R_COL)['max_dd_r']:.2f} |",
        f"| practical all lookbacks | {len(practical)} | {metrics(practical, R_COL)['total_r']:.2f} | {metrics(practical, R_COL)['avg_r']:.2f} | {metrics(practical, R_COL)['pf']:.2f} | {metrics(practical, R_COL)['max_dd_r']:.2f} |",
        "",
        "## Primary: 通貨別",
        "",
        markdown_table(pick("primary_L120_ADX30_RISK1_5_BBW3_8", "symbol")[cols], 40),
        "",
        "## Primary: 期間別",
        "",
        markdown_table(pick("primary_L120_ADX30_RISK1_5_BBW3_8", "period")[cols], 40),
        "",
        "## Primary: 停滞レンジ幅別",
        "",
        markdown_table(pick("primary_L120_ADX30_RISK1_5_BBW3_8", "zone_range_bucket")[cols], 40),
        "",
        "## Primary: 下抜け深さ別",
        "",
        markdown_table(pick("primary_L120_ADX30_RISK1_5_BBW3_8", "break_depth_bucket")[cols], 40),
        "",
        "## Primary: 下抜け足の終値位置",
        "",
        markdown_table(pick("primary_L120_ADX30_RISK1_5_BBW3_8", "break_close_location_bucket")[cols], 40),
        "",
        "## Practical All: サポート保持期間別",
        "",
        markdown_table(pick("practical_all_lookbacks", "support_age_bucket")[cols], 60),
        "",
        "## Practical All: 通貨別",
        "",
        markdown_table(pick("practical_all_lookbacks", "symbol")[cols], 60),
        "",
        "## Practical All: 期間別",
        "",
        markdown_table(pick("practical_all_lookbacks", "period")[cols], 60),
        "",
        "## Practical All: 事前状態別",
        "",
        markdown_table(pick("practical_all_lookbacks", "pre_break_regime")[cols], 60),
        "",
        "## Practical All: 直後フォロースルー別",
        "",
        markdown_table(pick("practical_all_lookbacks", "followthrough_bucket")[cols], 60),
        "",
        "## Practical All: 6本以内の戻り別",
        "",
        markdown_table(pick("practical_all_lookbacks", "retest_bucket")[cols], 60),
        "",
        "## 複合条件チェック",
        "",
        markdown_table(combos[combo_cols], 60) if not combos.empty else "_No rows._",
        "",
        "## 出口管理比較",
        "",
        markdown_table(management[mgmt_cols], 80) if not management.empty else "_No rows._",
        "",
        "## 暫定解釈",
        "",
        "- 安値停滞は、単にレンジが狭ければ良いわけではない。今回の主軸は `サポート保持期間`、`下抜け足の終値位置`、`抜けた後の反応速度`。",
        "- Practical Allでは、GBPJPYが大きく寄与し、AUDJPYとUSDJPYは弱い。全通貨へ広げるより、通貨別に採否を分ける必要がある。",
        "- 6本以内に停滞レンジ中央へ戻るものは、ショートの勢いが弱い疑いがある。ただし、そこで機械的に全撤退すると期待値も削られた。",
        "- `6本以内に1R未達なら撤退` は早すぎて悪化。`12本以内に1R未達なら撤退` はPractical Allとサポート60-119本で改善したため、次の管理ルール候補。",
        "- Primary 1ヶ月安値停滞は、サンプル18件では固定2Rがまだ最も素直。サポート60-119本は強いが、2025-2026のOOSが未発生のため過信しない。",
        "- 直後フォロースルーや中央戻りは、エントリー前には分からないため入口フィルタではなく、建玉後の観察・撤退判断として扱う。",
        "",
        "## 出力CSV",
        "",
        "- `enriched_stagnation.csv`",
        "- `stagnation_feature_summary.csv`",
        "- `stagnation_combo_summary.csv`",
        "- `stagnation_management_summary.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    signals = pd.read_csv(SOURCE)
    frames = load_frames()
    enriched = add_stagnation_features(signals, frames)
    enriched.to_csv(OUT_DIR / "enriched_stagnation.csv", index=False)
    summaries = all_summaries(enriched)
    combos = combo_summaries(enriched)
    management = management_summaries(enriched)
    summaries.to_csv(OUT_DIR / "stagnation_feature_summary.csv", index=False)
    combos.to_csv(OUT_DIR / "stagnation_combo_summary.csv", index=False)
    management.to_csv(OUT_DIR / "stagnation_management_summary.csv", index=False)
    write_report(enriched, summaries, combos, management)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(combos.to_string(index=False))


if __name__ == "__main__":
    main()

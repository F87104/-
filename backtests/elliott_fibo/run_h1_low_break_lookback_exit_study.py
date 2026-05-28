#!/usr/bin/env python3
"""
H1 low-break lookback and exit study.

This mirrors the H4 low-break study, but converts the time meaning to H1:
- 1 month is about 480 H1 bars.
- H1 stagnation uses 12 bars, matching 3 H4 bars in clock time.
- H1 signal windows use 192 bars, matching 48 H4 bars in clock time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    add_indicators,
    holiday_market,
    load_instrument,
    markdown_table,
    resample_ohlc,
)
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import (
    EXIT_SPECS,
    ExitSpec,
    add_period_metrics,
    count_touch_clusters,
    excursion_metrics,
    metrics,
    simulate_exit,
)
from run_monthly_low_rebreak_short import LowBreakSpec, first_low_breaks, low_break_signal


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h1_low_break_lookback_exit_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H1"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
H1_BARS_PER_MONTH = 480

LOOKBACK_BARS = [240, 360, 480, 720, 960, 1440, 1920, 2880]
TRIGGER_MODES = ["stagnation", "rebreak", "either"]


@dataclass(frozen=True)
class FilterSpec:
    name: str
    notes: str
    fn: Callable[[pd.DataFrame], pd.Series]


def lookback_label(bars: int) -> str:
    months = bars / H1_BARS_PER_MONTH
    if months.is_integer():
        return f"{int(months)}m"
    return f"{months:.2g}m"


def make_spec(bars: int, trigger_mode: str) -> LowBreakSpec:
    suffix = {"stagnation": "STAG", "rebreak": "REBREAK", "either": "EITHER"}[trigger_mode]
    return LowBreakSpec(
        name=f"H1_L{bars:04d}_{suffix}",
        lookback_bars=bars,
        trigger_mode=trigger_mode,
        max_after_break=192,
        min_wait_bars=8,
        pullback_min_atr=1.50,
        stag_bars=12,
        stag_range_atr=3.0,
        near_level_atr=2.0,
        break_buffer_atr=0.08,
        stop_buffer_atr=0.35,
        rr=2.0,
    )


def classify_period(ts: pd.Timestamp) -> str:
    if ts.year <= 2020:
        return "train_2015_2020"
    if ts.year <= 2024:
        return "test_2021_2024"
    return "oos_2025_2026"


def support_age_bucket_h1(age_bars: int) -> str:
    if age_bars <= 96:
        return "00_<=96bars"
    if age_bars <= 239:
        return "01_97-239bars"
    if age_bars <= 479:
        return "02_240-479bars"
    if age_bars <= 959:
        return "03_480-959bars"
    return "04_>=960bars"


def pre_break_context_h1(df: pd.DataFrame, break_i: int, lookback_bars: int, prior_low: float) -> dict[str, float | int | str]:
    atr_break = float(df["atr"].iloc[break_i])
    if not math.isfinite(atr_break) or atr_break <= 0:
        atr_break = np.nan

    start_i = max(0, break_i - lookback_bars)
    win = df.iloc[start_i:break_i]
    if win.empty or not math.isfinite(atr_break):
        return {
            "support_age_bars": 0,
            "support_age_months": 0.0,
            "support_age_ratio": 0.0,
            "support_touch_bars_0_5atr": 0,
            "support_touch_clusters_0_5atr": 0,
            "pre_break_range_width_atr": np.nan,
            "pre_break_net_move_atr": np.nan,
            "pre_break_efficiency": np.nan,
            "pre_break_slope_atr_per_month": np.nan,
            "pre_break_regime": "unknown",
            "support_age_bucket": "unknown",
        }

    lows = win["low"].to_numpy(dtype=float)
    low_local_i = 0 if np.all(np.isnan(lows)) else int(np.nanargmin(lows))
    low_global_i = start_i + low_local_i
    age = int(break_i - low_global_i)
    age_ratio = age / lookback_bars if lookback_bars > 0 else 0.0

    near_support = (win["low"] <= prior_low + atr_break * 0.5).fillna(False).to_numpy()
    touch_clusters = count_touch_clusters(np.flatnonzero(near_support), min_gap=12)

    closes = win["close"].astype(float)
    pre_range_width_atr = float((win["high"].max() - win["low"].min()) / atr_break)
    pre_net_move_atr = float((closes.iloc[-1] - closes.iloc[0]) / atr_break) if len(closes) >= 2 else 0.0
    total_path = float(closes.diff().abs().sum())
    net_abs = float(abs(closes.iloc[-1] - closes.iloc[0])) if len(closes) >= 2 else 0.0
    efficiency = net_abs / total_path if total_path > 0 else 0.0
    if len(closes) >= 24:
        x = np.arange(len(closes), dtype=float)
        slope = float(np.polyfit(x, closes.to_numpy(dtype=float), 1)[0])
        slope_atr_per_month = slope * H1_BARS_PER_MONTH / atr_break
    else:
        slope_atr_per_month = 0.0

    long_support = age >= max(120, int(lookback_bars * 0.35))
    enough_touches = touch_clusters >= 2
    sideways = efficiency <= 0.35 and abs(slope_atr_per_month) <= 2.5
    trending_down = slope_atr_per_month <= -2.5 and efficiency >= 0.30
    fresh_low = age <= min(96, max(24, int(lookback_bars * 0.20)))

    if long_support and enough_touches and sideways:
        regime = "range_support_break"
    elif fresh_low or trending_down:
        regime = "trend_continuation_break"
    else:
        regime = "mixed_or_wide_range"

    return {
        "support_age_bars": age,
        "support_age_months": age / H1_BARS_PER_MONTH,
        "support_age_ratio": age_ratio,
        "support_touch_bars_0_5atr": int(near_support.sum()),
        "support_touch_clusters_0_5atr": int(touch_clusters),
        "pre_break_range_width_atr": pre_range_width_atr,
        "pre_break_net_move_atr": pre_net_move_atr,
        "pre_break_efficiency": float(efficiency),
        "pre_break_slope_atr_per_month": float(slope_atr_per_month),
        "pre_break_regime": regime,
        "support_age_bucket": support_age_bucket_h1(age),
    }


def filter_specs_h1() -> list[FilterSpec]:
    return [
        FilterSpec("ALL", "全候補", lambda d: pd.Series(True, index=d.index)),
        FilterSpec(
            "ADX30_RISK_LE3_BBW3_12",
            "ADX>=30 + risk<=3H1ATR + BB幅3-12H1ATR",
            lambda d: d["adx14"].ge(30) & d["risk_atr_at_signal"].le(3.0) & d["bb_width_atr"].between(3.0, 12.0),
        ),
        FilterSpec(
            "ADX30_RISK_LE2_BBW3_10",
            "ADX>=30 + risk<=2H1ATR + BB幅3-10H1ATR",
            lambda d: d["adx14"].ge(30) & d["risk_atr_at_signal"].le(2.0) & d["bb_width_atr"].between(3.0, 10.0),
        ),
        FilterSpec(
            "ADX25_RISK_LE4_BBW3_14",
            "ADX>=25 + risk<=4H1ATR + BB幅3-14H1ATR",
            lambda d: d["adx14"].ge(25) & d["risk_atr_at_signal"].le(4.0) & d["bb_width_atr"].between(3.0, 14.0),
        ),
        FilterSpec(
            "GBP_ADX25_RISK_LE4_BBW3_14",
            "GBPJPY + ADX>=25 + risk<=4H1ATR + BB幅3-14H1ATR",
            lambda d: d["symbol"].eq("GBPJPY") & d["adx14"].ge(25) & d["risk_atr_at_signal"].le(4.0) & d["bb_width_atr"].between(3.0, 14.0),
        ),
    ]


def extract_signals(df: pd.DataFrame, symbol: str, spec: LowBreakSpec) -> pd.DataFrame:
    breaks = first_low_breaks(df, spec)
    rows: list[dict] = []
    in_pos_until = -1
    used_breaks: set[str] = set()

    for break_i in np.flatnonzero(breaks.to_numpy()):
        if break_i <= in_pos_until or break_i >= len(df) - 2:
            continue
        ts = df.index[int(break_i)]
        if ts < START or ts > END or holiday_market(ts):
            continue

        sig = low_break_signal(df, int(break_i), spec)
        if sig is None or sig["break_key"] in used_breaks:
            continue

        entry_i = int(sig["trigger_i"]) + 1
        base_exit = simulate_exit(df, symbol, entry_i, float(sig["stop"]), ExitSpec("fixed_2R", target_rr=2.0, max_hold_bars=720))
        if base_exit is None:
            continue

        feature_cols = [
            "open",
            "high",
            "low",
            "close",
            "atr",
            "body_ratio",
            "ema20",
            "ema50",
            "ema200",
            "ema20_slope_10_atr",
            "rsi14",
            "adx14",
            "bb_width_atr",
            "bb_pos",
            "atr_ratio_50",
            "atr_pctile_252",
            "close_location",
            "range5_atr",
            "macd",
            "macd_signal",
            "macd_hist",
            "macd_hist_slope3",
        ]
        features = {col: df[col].iloc[int(sig["trigger_i"])] for col in feature_cols if col in df.columns}
        used_breaks.add(sig["break_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "trigger_mode": spec.trigger_mode,
                "lookback_bars": spec.lookback_bars,
                "lookback_months": spec.lookback_bars / H1_BARS_PER_MONTH,
                "lookback_label": lookback_label(spec.lookback_bars),
                "signal_time": df.index[int(sig["trigger_i"])],
                "entry_i": entry_i,
                **pre_break_context_h1(df, int(break_i), spec.lookback_bars, float(sig["prior_low"])),
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "break_key", "lookback_bars"}},
                **features,
                "entry_time": base_exit["entry_time"],
                "entry": base_exit["entry"],
                "stop": base_exit["stop"],
                "base_target_2r": base_exit["target_model"],
                "base_exit_time": base_exit["exit_time_model"],
                "base_exit": base_exit["exit_model"],
                "base_exit_reason": base_exit["exit_reason_model"],
                "base_bars_held": base_exit["bars_held_model"],
                "risk": base_exit["risk"],
                "base_r_clean": base_exit["r_clean_model"],
                "base_r_after_cost": base_exit["r_after_cost_model"],
                "base_mfe_r": base_exit["mfe_r_model"],
                "base_mae_r": base_exit["mae_r_model"],
            }
        )
        in_pos_until = int(df.index.get_loc(base_exit["exit_time_model"]))

    return pd.DataFrame(rows)


def build_signals() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    coverage = []
    rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        frames[symbol] = df
        for bars in LOOKBACK_BARS:
            for trigger_mode in TRIGGER_MODES:
                sample = extract_signals(df, symbol, make_spec(bars, trigger_mode))
                if not sample.empty:
                    rows.append(sample)

    signals = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not signals.empty:
        for col in ["signal_time", "entry_time", "base_exit_time"]:
            signals[col] = pd.to_datetime(signals[col])
        signals["period"] = signals["entry_time"].map(classify_period)
        signals["year"] = signals["entry_time"].dt.year.astype(str)
        signals = signals.sort_values(["entry_time", "symbol", "strategy"]).reset_index(drop=True)
    return signals, frames, pd.DataFrame(coverage)


def exit_specs_h1() -> list[ExitSpec]:
    out = []
    for spec in EXIT_SPECS:
        max_hold = 720 if spec.max_hold_bars == 180 else spec.max_hold_bars * 4
        no_progress = None if spec.no_progress_bars is None else spec.no_progress_bars * 4
        out.append(
            ExitSpec(
                spec.name,
                target_rr=spec.target_rr,
                partial_1r=spec.partial_1r,
                be_after_1r=spec.be_after_1r,
                trail_atr_after_1r=spec.trail_atr_after_1r,
                no_progress_bars=no_progress,
                max_hold_bars=max_hold,
            )
        )
    return out


def build_exit_models(signals: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    specs = exit_specs_h1()
    for _, row in signals.iterrows():
        symbol = str(row["symbol"])
        df = frames[symbol]
        entry_i = int(row["entry_i"])
        stop = float(row["stop"])
        base = row.to_dict()
        for spec in specs:
            out = simulate_exit(df, symbol, entry_i, stop, spec)
            if out is None:
                continue
            rows.append({**base, "exit_variant": spec.name, **out})
    exits = pd.DataFrame(rows)
    if not exits.empty:
        for col in ["signal_time", "entry_time", "base_exit_time", "exit_time_model"]:
            exits[col] = pd.to_datetime(exits[col])
        exits["period"] = exits["entry_time"].map(classify_period)
        exits["year"] = exits["entry_time"].dt.year.astype(str)
    return exits


def summarize_groups(df: pd.DataFrame, r_col: str, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_cols, keys))
        for filt in filter_specs_h1():
            mask = filt.fn(group).fillna(False)
            sample = group[mask].copy()
            row = {**base, "filter": filt.name, "filter_notes": filt.notes}
            add_period_metrics(row, "all", sample, r_col)
            add_period_metrics(row, "train", sample[sample["period"].eq("train_2015_2020")], r_col)
            add_period_metrics(row, "test", sample[sample["period"].eq("test_2021_2024")], r_col)
            add_period_metrics(row, "oos", sample[sample["period"].eq("oos_2025_2026")], r_col)
            row.update(excursion_metrics(sample, r_col))
            row["score"] = (
                row["all_total_r"]
                + row["test_total_r"] * 1.2
                + row["all_avg_r"] * 4
                + min(row["all_pf"] if math.isfinite(row["all_pf"]) else 5, 5)
                - row["all_max_dd_r"] * 0.25
                - (3.0 if row["all_trades"] < 15 else 0.0)
                - (2.0 if row["test_total_r"] < 0 else 0.0)
                - (1.0 if row["oos_total_r"] < 0 else 0.0)
            )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["score", "all_total_r"], ascending=False).reset_index(drop=True)


def build_summaries(exits: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fixed = exits[exits["exit_variant"].eq("fixed_2R")].copy()
    strength = summarize_groups(fixed, "r_after_cost_model", ["lookback_bars", "lookback_label", "trigger_mode"])
    exit_summary = summarize_groups(exits, "r_after_cost_model", ["lookback_bars", "lookback_label", "trigger_mode", "exit_variant"])
    regime_summary = summarize_groups(fixed, "r_after_cost_model", ["pre_break_regime", "trigger_mode"])
    support_age_summary = summarize_groups(fixed, "r_after_cost_model", ["support_age_bucket", "trigger_mode"])
    return strength, exit_summary, regime_summary, support_age_summary


def write_report(
    coverage: pd.DataFrame,
    strength: pd.DataFrame,
    exit_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
    support_age_summary: pd.DataFrame,
) -> None:
    primary_filter = "ADX30_RISK_LE3_BBW3_12"
    primary_strength = strength[
        strength["filter"].eq(primary_filter) & strength["trigger_mode"].eq("stagnation")
    ].sort_values("lookback_bars")
    broad_strength = strength[
        strength["filter"].eq("ALL") & strength["trigger_mode"].eq("stagnation")
    ].sort_values("lookback_bars")
    primary_exit = exit_summary[
        exit_summary["filter"].eq(primary_filter) & exit_summary["trigger_mode"].eq("stagnation")
    ].sort_values(["score", "all_total_r"], ascending=False)
    primary_regime = regime_summary[
        regime_summary["filter"].eq(primary_filter) & regime_summary["trigger_mode"].eq("stagnation")
    ].sort_values(["score", "all_total_r"], ascending=False)
    primary_support_age = support_age_summary[
        support_age_summary["filter"].eq(primary_filter) & support_age_summary["trigger_mode"].eq("stagnation")
    ].sort_values("support_age_bucket")

    strength_cols = [
        "lookback_label",
        "lookback_bars",
        "trigger_mode",
        "filter",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_total_r",
        "oos_total_r",
        "avg_mfe_r",
        "hit_1r_rate",
        "hit_1_5r_rate",
        "hit_2r_rate",
        "giveback_1r_to_loss_rate",
    ]
    exit_cols = [
        "lookback_label",
        "lookback_bars",
        "exit_variant",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_total_r",
        "oos_total_r",
        "score",
    ]

    lines = [
        "# H1 安値更新期間と利益確定基準の研究",
        "",
        "Status: 検証途中。H4で有望だった安値更新ショートのH1版。",
        "",
        "## 検証した問い",
        "",
        "- H4ではなくH1で1ヶ月/3ヶ月/6ヶ月安値更新を見ると、早く入れる分だけ優位性が上がるか。",
        "- H1の細かい足で安値停滞を見た場合、ノイズが増えすぎないか。",
        "- 長い安値更新が、レンジサポート割れなのか、下落トレンド継続なのかを分ける。",
        "- 固定2Rより、1R/1.25R/建値/半分利確が合うか。",
        "",
        "## H1換算",
        "",
        "- 1ヶ月: 480本",
        "- 3ヶ月: 1440本",
        "- 6ヶ月: 2880本",
        "- 安値停滞: 12本。H4の3本停滞に時間を合わせた。",
        "- シグナル期限: 192本。H4の48本以内に時間を合わせた。",
        "",
        "## 暫定結論",
        "",
        "- H4本命をそのままH1へ落とした `1ヶ月安値更新 + 安値停滞下抜け` は弱い。",
        "- H1の主フィルタ + 安値停滞下抜けは、1ヶ月でも `18 trades / +1.40R / PF 1.12` に留まり、H4の `18 trades / +13.61R / PF 2.78` に大きく劣る。",
        "- 3ヶ月、4ヶ月、6ヶ月の長期lookbackはH1でも強くならない。",
        "- 一方で、H1独自の断片として `GBPJPY + 0.5ヶ月安値更新 + rebreak + ADX>=25 + risk<=4H1ATR + BB幅3-14H1ATR` は有望。",
        "- このH1断片は `37 trades / +25.01R / PF 2.52 / maxDD 2.14R`。2025-2026 OOSも `3 trades / +2.95R`。",
        "- ただしこれはH4本命の安値停滞型ではなく、GBPJPY専用の短期rebreak型として別手法候補に分ける。",
        "",
        "## データ範囲",
        "",
        markdown_table(coverage, 20),
        "",
        "## 主フィルタ + 安値停滞下抜け: lookback別",
        "",
        markdown_table(primary_strength[strength_cols], 80) if not primary_strength.empty else "_No rows._",
        "",
        "## 全候補 + 安値停滞下抜け: lookback別",
        "",
        markdown_table(broad_strength[strength_cols], 80) if not broad_strength.empty else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: 事前状態別",
        "",
        markdown_table(primary_regime[[c for c in ["pre_break_regime", *strength_cols[3:], "score"] if c in primary_regime.columns]], 60)
        if not primary_regime.empty
        else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: サポート保持期間別",
        "",
        markdown_table(primary_support_age[[c for c in ["support_age_bucket", *strength_cols[3:], "score"] if c in primary_support_age.columns]], 60)
        if not primary_support_age.empty
        else "_No rows._",
        "",
        "## 主フィルタ + 安値停滞下抜け: 利確/撤退 上位",
        "",
        markdown_table(primary_exit[exit_cols].head(40), 80) if not primary_exit.empty else "_No rows._",
        "",
        "## 全体上位",
        "",
        markdown_table(strength[strength_cols + ["score"]].head(50), 80) if not strength.empty else "_No rows._",
        "",
        "## 暫定メモ",
        "",
        "- H1はH4より早く入れる可能性があるが、スプレッド/ノイズの影響も大きい。",
        "- H4と同じ結論になるか、H1独自の短い保持期間が良くなるかを確認する。",
        "- 大きな個別出口明細は再生成可能なためGit管理しない。",
        "",
        "## 出力CSV",
        "",
        "- `signals.csv`",
        "- `lookback_strength.csv`",
        "- `exit_summary.csv`",
        "- `regime_summary.csv`",
        "- `support_age_summary.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    signals, frames, coverage = build_signals()
    signals.to_csv(OUT_DIR / "signals.csv", index=False)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    if signals.empty:
        (OUT_DIR / "report_ja.md").write_text("# H1 安値更新期間と利益確定基準の研究\n\nNo signals.", encoding="utf-8")
        print("No signals")
        return

    exits = build_exit_models(signals, frames)
    strength, exit_summary, regime_summary, support_age_summary = build_summaries(exits)
    strength.to_csv(OUT_DIR / "lookback_strength.csv", index=False)
    exit_summary.to_csv(OUT_DIR / "exit_summary.csv", index=False)
    regime_summary.to_csv(OUT_DIR / "regime_summary.csv", index=False)
    support_age_summary.to_csv(OUT_DIR / "support_age_summary.csv", index=False)

    write_report(coverage, strength, exit_summary, regime_summary, support_age_summary)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(
        strength[
            strength["filter"].eq("ADX30_RISK_LE3_BBW3_12")
            & strength["trigger_mode"].eq("stagnation")
        ][
            [
                "lookback_label",
                "lookback_bars",
                "all_trades",
                "all_total_r",
                "all_avg_r",
                "all_pf",
                "test_total_r",
                "oos_total_r",
                "hit_1r_rate",
                "giveback_1r_to_loss_rate",
            ]
        ]
        .sort_values("lookback_bars")
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()

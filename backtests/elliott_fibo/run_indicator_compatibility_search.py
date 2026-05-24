#!/usr/bin/env python3
"""
Indicator compatibility search for H4 V-recovery trigger strategies.

This script searches indicators that pair well with the current H4
V-candidate -> trigger idea.  To reduce overfitting, it reports both:

- train period: 2015-2020
- test period:  2021-2024

The search is not meant to produce a final optimized system.  It is a research
map: which indicator families improve quality, and which ones are probably
dead ends.
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
    load_instrument,
    markdown_table,
    resample_ohlc,
)
from run_v_recovery_non_fibo_tool_study import add_tool_features
from run_v_recovery_trigger_study import TriggerSpec, run_spec as run_trigger_spec


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2015_2024" / "indicator_compatibility_search"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
SPLIT_DATE = pd.Timestamp("2021-01-01")

BASE_SPECS = [
    TriggerSpec("T4_REBREAK_ONLY", trigger_mode="rebreak"),
    TriggerSpec("T5_STAG_OR_REBREAK", trigger_mode="either"),
]


@dataclass(frozen=True)
class IndicatorFilter:
    name: str
    family: str
    description: str
    fn: Callable[[pd.DataFrame], pd.Series]


def true_range(df: pd.DataFrame) -> pd.Series:
    return pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)


def stochastic_k(df: pd.DataFrame, length: int = 14) -> pd.Series:
    ll = df["low"].rolling(length, min_periods=length).min()
    hh = df["high"].rolling(length, min_periods=length).max()
    return 100 * (df["close"] - ll) / (hh - ll).replace(0.0, np.nan)


def cci(df: pd.DataFrame, length: int = 20) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    ma = tp.rolling(length, min_periods=length).mean()
    md = (tp - ma).abs().rolling(length, min_periods=length).mean()
    return (tp - ma) / (0.015 * md.replace(0.0, np.nan))


def choppiness(df: pd.DataFrame, length: int = 14) -> pd.Series:
    tr_sum = true_range(df).rolling(length, min_periods=length).sum()
    span = df["high"].rolling(length, min_periods=length).max() - df["low"].rolling(length, min_periods=length).min()
    return 100 * np.log10(tr_sum / span.replace(0.0, np.nan)) / math.log10(length)


def aroon(series: pd.Series, length: int, kind: str) -> pd.Series:
    def calc(values: np.ndarray) -> float:
        if kind == "up":
            idx = int(np.nanargmax(values))
        else:
            idx = int(np.nanargmin(values))
        return 100.0 * (idx + 1) / len(values)

    return series.rolling(length, min_periods=length).apply(calc, raw=True)


def add_extended_features(df: pd.DataFrame) -> pd.DataFrame:
    out = add_tool_features(df)

    ema12 = out["close"].ewm(span=12, adjust=False).mean()
    ema26 = out["close"].ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    out["macd_hist_slope3"] = out["macd_hist"] - out["macd_hist"].shift(3)

    out["stoch_k14"] = stochastic_k(out, 14)
    out["stoch_d3"] = out["stoch_k14"].rolling(3, min_periods=3).mean()
    out["cci20"] = cci(out, 20)
    out["roc10"] = out["close"].pct_change(10) * 100

    hh14 = out["high"].rolling(14, min_periods=14).max()
    ll14 = out["low"].rolling(14, min_periods=14).min()
    out["williams_r14"] = -100 * (hh14 - out["close"]) / (hh14 - ll14).replace(0.0, np.nan)

    out["chop14"] = choppiness(out, 14)
    out["aroon_up25"] = aroon(out["high"], 25, "up")
    out["aroon_down25"] = aroon(out["low"], 25, "down")

    tenkan = (out["high"].rolling(9, min_periods=9).max() + out["low"].rolling(9, min_periods=9).min()) / 2
    kijun = (out["high"].rolling(26, min_periods=26).max() + out["low"].rolling(26, min_periods=26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (out["high"].rolling(52, min_periods=52).max() + out["low"].rolling(52, min_periods=52).min()) / 2
    out["ichi_tenkan"] = tenkan
    out["ichi_kijun"] = kijun
    out["ichi_cloud_top"] = pd.concat([span_a, span_b], axis=1).max(axis=1)
    out["ichi_cloud_bottom"] = pd.concat([span_a, span_b], axis=1).min(axis=1)

    kc_mid = out["close"].ewm(span=20, adjust=False).mean()
    kc_upper = kc_mid + out["atr"] * 2
    kc_lower = kc_mid - out["atr"] * 2
    out["kc_mid"] = kc_mid
    out["kc_pos"] = (out["close"] - kc_lower) / (kc_upper - kc_lower).replace(0.0, np.nan)
    out["bb_kc_width_ratio"] = out["bb_width_atr"] / 4.0
    return out


def enrich_trades(trades: pd.DataFrame, feature_frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for row in trades.to_dict("records"):
        key = (row["symbol"], row["timeframe"])
        df = feature_frames[key]
        ts = pd.Timestamp(row["signal_time"])
        if ts not in df.index:
            continue
        features = df.loc[ts].to_dict()
        rows.append({**row, **features})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["signal_time"] = pd.to_datetime(out["signal_time"])
        out = out.sort_values(["signal_time", "symbol"]).reset_index(drop=True)
    return out


def max_drawdown(values: pd.Series) -> float:
    arr = values.astype(float).to_numpy()
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def max_losing_streak(values: pd.Series) -> int:
    cur = 0
    best = 0
    for value in values.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def profit_factor(values: pd.Series) -> float:
    gp = float(values[values > 0].sum())
    gl = float(values[values <= 0].sum())
    if gl < 0:
        return gp / abs(gl)
    return math.inf if gp > 0 else math.nan


def metrics(df: pd.DataFrame, prefix: str) -> dict:
    r = df["r_after_cost"] if not df.empty else pd.Series(dtype=float)
    return {
        f"{prefix}_trades": int(len(df)),
        f"{prefix}_win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        f"{prefix}_total_r": float(r.sum()) if len(r) else 0.0,
        f"{prefix}_avg_r": float(r.mean()) if len(r) else 0.0,
        f"{prefix}_pf": profit_factor(r) if len(r) else math.nan,
        f"{prefix}_max_dd_r": max_drawdown(r),
        f"{prefix}_max_ls": max_losing_streak(r),
    }


def build_filters() -> list[IndicatorFilter]:
    return [
        IndicatorFilter("ALL_BASELINE", "baseline", "フィルターなし", lambda x: pd.Series(True, index=x.index)),
        IndicatorFilter("Candle_CloseLoc65", "Candle", "終値が足の上側35%以内", lambda x: x["close_location"] >= 0.65),
        IndicatorFilter("Candle_CloseLoc75", "Candle", "終値が足の上側25%以内", lambda x: x["close_location"] >= 0.75),
        IndicatorFilter("Candle_Body50", "Candle", "実体比率50%以上", lambda x: x["body_ratio"] >= 0.50),
        IndicatorFilter("Candle_Body70", "Candle", "実体比率70%以上", lambda x: x["body_ratio"] >= 0.70),
        IndicatorFilter("RSI_45_75", "RSI", "RSI14が45〜75", lambda x: x["rsi14"].between(45, 75)),
        IndicatorFilter("RSI_50_70", "RSI", "RSI14が50〜70", lambda x: x["rsi14"].between(50, 70)),
        IndicatorFilter("RSI_55_75", "RSI", "RSI14が55〜75", lambda x: x["rsi14"].between(55, 75)),
        IndicatorFilter("Stoch_20_85", "Stochastic", "Stoch Kが20〜85", lambda x: x["stoch_k14"].between(20, 85)),
        IndicatorFilter("Stoch_K_gt_D", "Stochastic", "Stoch K > D", lambda x: x["stoch_k14"] > x["stoch_d3"]),
        IndicatorFilter("Williams_gt_-50", "WilliamsR", "Williams %R > -50", lambda x: x["williams_r14"] > -50),
        IndicatorFilter("CCI_-50_150", "CCI", "CCI20が-50〜150", lambda x: x["cci20"].between(-50, 150)),
        IndicatorFilter("CCI_gt_0", "CCI", "CCI20 > 0", lambda x: x["cci20"] > 0),
        IndicatorFilter("MACD_hist_gt_0", "MACD", "MACDヒストグラム > 0", lambda x: x["macd_hist"] > 0),
        IndicatorFilter("MACD_hist_rising", "MACD", "MACDヒストグラムが3本前より上", lambda x: x["macd_hist_slope3"] > 0),
        IndicatorFilter("ROC10_gt_0", "ROC", "10本ROC > 0", lambda x: x["roc10"] > 0),
        IndicatorFilter("EMA20_gt_50", "EMA", "EMA20 > EMA50", lambda x: x["ema20"] > x["ema50"]),
        IndicatorFilter("EMA_close_gt_200", "EMA", "終値 > EMA200", lambda x: x["close"] > x["ema200"]),
        IndicatorFilter("EMA_stack", "EMA", "EMA20 > EMA50 > EMA200", lambda x: (x["ema20"] > x["ema50"]) & (x["ema50"] > x["ema200"])),
        IndicatorFilter("EMA20_slope_pos", "EMA", "EMA20の傾きがプラス", lambda x: x["ema20_slope_10_atr"] > 0),
        IndicatorFilter("ADX_lt_25", "ADX", "ADX14 < 25", lambda x: x["adx14"] < 25),
        IndicatorFilter("ADX_12_28", "ADX", "ADX14が12〜28", lambda x: x["adx14"].between(12, 28)),
        IndicatorFilter("ADX_ge_18", "ADX", "ADX14 >= 18", lambda x: x["adx14"] >= 18),
        IndicatorFilter("CHOP_lt_50", "Choppiness", "Choppiness < 50", lambda x: x["chop14"] < 50),
        IndicatorFilter("CHOP_35_60", "Choppiness", "Choppinessが35〜60", lambda x: x["chop14"].between(35, 60)),
        IndicatorFilter("AroonUp_gt_Down", "Aroon", "Aroon Up > Down", lambda x: x["aroon_up25"] > x["aroon_down25"]),
        IndicatorFilter("AroonUp_gt_70", "Aroon", "Aroon Up > 70", lambda x: x["aroon_up25"] > 70),
        IndicatorFilter("BB_pos_60_110", "Bollinger", "BB位置が0.60〜1.10", lambda x: x["bb_pos"].between(0.60, 1.10)),
        IndicatorFilter("BB_pos_50_100", "Bollinger", "BB位置が0.50〜1.00", lambda x: x["bb_pos"].between(0.50, 1.00)),
        IndicatorFilter("BB_width_2_6ATR", "Bollinger", "BB幅が2〜6ATR", lambda x: x["bb_width_atr"].between(2.0, 6.0)),
        IndicatorFilter("BB_width_ge_3ATR", "Bollinger", "BB幅 >= 3ATR", lambda x: x["bb_width_atr"] >= 3.0),
        IndicatorFilter("KC_pos_55_110", "Keltner", "KC位置が0.55〜1.10", lambda x: x["kc_pos"].between(0.55, 1.10)),
        IndicatorFilter("KC_close_gt_mid", "Keltner", "終値 > Keltner中心線", lambda x: x["close"] > x["kc_mid"]),
        IndicatorFilter("Ichimoku_close_gt_kijun", "Ichimoku", "終値 > 基準線", lambda x: x["close"] > x["ichi_kijun"]),
        IndicatorFilter("Ichimoku_tenkan_gt_kijun", "Ichimoku", "転換線 > 基準線", lambda x: x["ichi_tenkan"] > x["ichi_kijun"]),
        IndicatorFilter("Ichimoku_above_cloud", "Ichimoku", "終値 > 雲上限", lambda x: x["close"] > x["ichi_cloud_top"]),
        IndicatorFilter("ATR_pctile_lt_85", "ATR", "ATR上位15%を除外", lambda x: x["atr_pctile_252"] < 85),
        IndicatorFilter("ATR_pctile_20_90", "ATR", "ATRが20〜90パーセンタイル", lambda x: x["atr_pctile_252"].between(20, 90)),
        IndicatorFilter("ATR_ratio_lt_1_5", "ATR", "ATR14 < ATR50 x 1.5", lambda x: x["atr_ratio_50"] < 1.5),
        IndicatorFilter("Range5_le_6ATR", "Compression", "直近5本レンジ <= 6ATR", lambda x: x["range5_atr"] <= 6.0),
        IndicatorFilter("Combo_BB_CloseLoc", "Combo", "BB位置0.60〜1.10 + 終値位置65%以上", lambda x: x["bb_pos"].between(0.60, 1.10) & (x["close_location"] >= 0.65)),
        IndicatorFilter("Combo_EMA_RSI_ATR", "Combo", "EMA20>50 + RSI50〜75 + ATR過大除外", lambda x: (x["ema20"] > x["ema50"]) & x["rsi14"].between(50, 75) & (x["atr_pctile_252"] < 85)),
        IndicatorFilter("Combo_EMA_BB", "Combo", "EMA20>50 + BB位置0.60〜1.10", lambda x: (x["ema20"] > x["ema50"]) & x["bb_pos"].between(0.60, 1.10)),
        IndicatorFilter("Combo_EMA_CloseLoc", "Combo", "EMA20>50 + 終値位置65%以上", lambda x: (x["ema20"] > x["ema50"]) & (x["close_location"] >= 0.65)),
        IndicatorFilter("Combo_MACD_CloseLoc", "Combo", "MACDヒストグラム>0 + 終値位置65%以上", lambda x: (x["macd_hist"] > 0) & (x["close_location"] >= 0.65)),
        IndicatorFilter("Combo_Ichi_RSI", "Combo", "終値>基準線 + RSI45〜75", lambda x: (x["close"] > x["ichi_kijun"]) & x["rsi14"].between(45, 75)),
        IndicatorFilter("Combo_CHOP_BB", "Combo", "CHOP<50 + BB位置0.60〜1.10", lambda x: (x["chop14"] < 50) & x["bb_pos"].between(0.60, 1.10)),
    ]


def run_base_trades() -> pd.DataFrame:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    base_rows: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        df = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
        feature_frames[(symbol, TIMEFRAME)] = df
        for spec in BASE_SPECS:
            trades = run_trigger_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                base_rows.append(trades)
    base = pd.concat(base_rows, ignore_index=True) if base_rows else pd.DataFrame()
    return enrich_trades(base, feature_frames) if not base.empty else base


def evaluate_filter(group: pd.DataFrame, filt: IndicatorFilter) -> dict:
    mask = filt.fn(group).fillna(False)
    sample = group[mask].copy().sort_values(["signal_time", "symbol"])
    train = sample[sample["signal_time"] < SPLIT_DATE]
    test = sample[sample["signal_time"] >= SPLIT_DATE]
    out = {
        "base_strategy": group["strategy"].iloc[0],
        "filter": filt.name,
        "family": filt.family,
        "description": filt.description,
        "pass_rate": float(len(sample) / len(group) * 100) if len(group) else 0.0,
    }
    out.update(metrics(sample, "all"))
    out.update(metrics(train, "train"))
    out.update(metrics(test, "test"))
    return out


def run_search() -> tuple[pd.DataFrame, pd.DataFrame]:
    trades = run_base_trades()
    trades.to_csv(OUT_DIR / "trades_enriched.csv", index=False)

    filters = build_filters()
    rows: list[dict] = []
    for _, group in trades.groupby("strategy"):
        for filt in filters:
            rows.append(evaluate_filter(group, filt))

    summary = pd.DataFrame(rows)
    baseline = summary[summary["filter"] == "ALL_BASELINE"][
        ["base_strategy", "all_avg_r", "test_avg_r", "all_total_r", "test_total_r", "all_max_dd_r", "test_max_dd_r"]
    ].rename(
        columns={
            "all_avg_r": "base_all_avg_r",
            "test_avg_r": "base_test_avg_r",
            "all_total_r": "base_all_total_r",
            "test_total_r": "base_test_total_r",
            "all_max_dd_r": "base_all_max_dd_r",
            "test_max_dd_r": "base_test_max_dd_r",
        }
    )
    summary = summary.merge(baseline, on="base_strategy", how="left")
    summary["all_avg_r_delta"] = summary["all_avg_r"] - summary["base_all_avg_r"]
    summary["test_avg_r_delta"] = summary["test_avg_r"] - summary["base_test_avg_r"]
    summary["all_dd_delta"] = summary["all_max_dd_r"] - summary["base_all_max_dd_r"]
    summary["test_dd_delta"] = summary["test_max_dd_r"] - summary["base_test_max_dd_r"]

    # Robust rank: keep enough test trades, improve test avg R or DD, and avoid
    # selecting tiny-sample outliers.
    summary["robust_score"] = (
        summary["test_total_r"]
        + summary["test_avg_r_delta"] * 50
        - summary["test_max_dd_r"] * 0.75
        + np.minimum(summary["test_trades"], 60) * 0.05
    )
    summary = summary.sort_values(["base_strategy", "robust_score"], ascending=[True, False])
    summary.to_csv(OUT_DIR / "indicator_search_summary.csv", index=False)

    recommended = summary[
        (summary["filter"] != "ALL_BASELINE")
        & (summary["test_trades"] >= 25)
        & (summary["all_trades"] >= 60)
        & ((summary["test_avg_r_delta"] > 0) | (summary["test_dd_delta"] < -1.0))
    ].copy()
    recommended = recommended.sort_values(["base_strategy", "robust_score"], ascending=[True, False])
    recommended.to_csv(OUT_DIR / "recommended_candidates.csv", index=False)
    return summary, recommended


def write_report(summary: pd.DataFrame, recommended: pd.DataFrame) -> None:
    compact_cols = [
        "base_strategy",
        "filter",
        "family",
        "description",
        "pass_rate",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "test_trades",
        "test_win_rate",
        "test_total_r",
        "test_avg_r",
        "test_pf",
        "test_max_dd_r",
        "test_avg_r_delta",
        "test_dd_delta",
        "robust_score",
    ]
    lines = [
        "# H4 V候補後トリガー 相性インジケータ探索",
        "",
        "## 見方",
        "",
        "- `all`: 2015-2024全期間。",
        "- `test`: 2021-2024後半期間。ここでも良いものを重視。",
        "- `test_avg_r_delta`: ベースラインより1トレード平均Rがどれだけ改善したか。",
        "- `test_dd_delta`: ベースラインよりDDがどれだけ増減したか。マイナスならDD改善。",
        "",
        "## 推奨候補",
        "",
        markdown_table(recommended[compact_cols], 80),
        "",
        "## 全探索結果",
        "",
        markdown_table(summary[compact_cols], 120),
        "",
        "## 出力",
        "",
        "- `indicator_search_summary.csv`",
        "- `recommended_candidates.csv`",
        "- `trades_enriched.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    summary, recommended = run_search()
    write_report(summary, recommended)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Recommended:")
    print(recommended.to_string(index=False))


if __name__ == "__main__":
    main()

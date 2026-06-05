#!/usr/bin/env python3
"""Compare T5 / V-entry tiers at fixed 2.0R vs 2.5R take-profit."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, resample_ohlc
from run_indicator_compatibility_search import add_extended_features, enrich_trades
from run_t5_practical_robustness_audit import (
    BASE_SPEC,
    PERIODS,
    TIMEFRAME,
    not_single_weak_rebreak,
)
from run_elliott_fibo_study import run_spec as run_immediate_spec
from run_v_recovery_relaxation_ladder import IMMEDIATE_STAGES, TRIGGER_STAGES
from run_v_recovery_trigger_study import TriggerSpec, run_spec
import run_v_recovery_trigger_study as trigger_mod


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_06_01" / "t5_rr_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_SYMBOLS = {"AUDJPY"}
RESEARCH_START = pd.Timestamp("2015-01-01")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def row_metrics(df: pd.DataFrame) -> dict:
    r = df["r_after_cost"].astype(float)
    return {
        "trades": int(len(r)),
        "win_rate": round(float((r > 0).mean() * 100), 1) if len(r) else 0.0,
        "total_r": round(float(r.sum()), 2) if len(r) else 0.0,
        "avg_r": round(float(r.mean()), 3) if len(r) else 0.0,
        "pf": round(profit_factor(r), 2) if len(r) else math.nan,
        "tp_rate": round(float((df["exit_reason"] == "TP").mean() * 100), 1) if len(r) and "exit_reason" in df.columns else 0.0,
    }


def load_feature_frames() -> dict[tuple[str, str], pd.DataFrame]:
    frames: dict[tuple[str, str], pd.DataFrame] = {}
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        h4 = add_indicators(resample_ohlc(raw, TIMEFRAME))
        frames[(symbol, TIMEFRAME)] = add_extended_features(h4)
    return frames


def research_only(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    return out[(out["entry_time"] >= RESEARCH_START) & (out["entry_time"] <= RESEARCH_END)].copy()


def ex_audjpy(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["symbol"].isin(EXCLUDE_SYMBOLS)].copy()


def strict_mask(df: pd.DataFrame) -> pd.Series:
    return df["bb_pos"].between(0.75, 1.0) & (df["macd_hist_slope3"] > 0)


def c125_mask(df: pd.DataFrame) -> pd.Series:
    return (
        strict_mask(df)
        & (df["bb_pos"] <= 0.95)
        & (df["signal_recovery_bars"] <= 16)
        & (df["bb_width_atr"] <= 4.0)
        & not_single_weak_rebreak(df)
    )


def structure_key(df: pd.DataFrame) -> pd.Series:
    return df["symbol"].astype(str) + ":" + df["v_start_i"].astype(str) + "-" + df["v_extreme_i"].astype(str)


def run_ladder_rr(rr: float, h4_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    key_immediate = {"I4 61.8%回復", "I5 急落条件を緩和"}
    key_trigger = {"T5 停滞または再ブレイク"}

    for stage in IMMEDIATE_STAGES:
        if stage.stage not in key_immediate:
            continue
        spec = replace(stage.spec, rr=rr)
        parts = []
        for symbol, df in h4_data.items():
            trades = run_immediate_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                parts.append(trades)
        stage_trades = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        m = row_metrics(ex_audjpy(research_only(stage_trades)))
        rows.append({"stage": stage.stage, "rr": rr, **m})

    for stage in TRIGGER_STAGES:
        if stage.stage not in key_trigger:
            continue
        spec = replace(stage.spec, rr=rr)
        parts = []
        for symbol, df in h4_data.items():
            trigger_mod.START = RESEARCH_START
            trigger_mod.END = RESEARCH_END
            trades = run_spec(df, symbol, TIMEFRAME, spec)
            if stage.overlap_only and not trades.empty:
                trades = trades[trades["trigger_type"].eq("stagnation+rebreak")]
            if not trades.empty:
                parts.append(trades)
        stage_trades = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        m = row_metrics(ex_audjpy(research_only(stage_trades)))
        rows.append({"stage": stage.stage, "rr": rr, **m})
    return pd.DataFrame(rows)


def tier_table(broad: pd.DataFrame, v_only: pd.DataFrame, rr: float) -> list[dict]:
    b = ex_audjpy(research_only(broad))
    v = ex_audjpy(research_only(v_only))
    v["ck"] = structure_key(v)
    b["ck"] = structure_key(b)
    never = v[~v["ck"].isin(set(b["ck"]))]
    later = v[v["ck"].isin(set(b["ck"]))]
    strict = b[strict_mask(b)]
    c125 = b[c125_mask(b)]
    return [
        {"rr": rr, "tier": "V候補即入（全部）", **row_metrics(v)},
        {"rr": rr, "tier": "　うちT5未成立", **row_metrics(never)},
        {"rr": rr, "tier": "　うちのちT5成立", **row_metrics(later)},
        {"rr": rr, "tier": "T5トリガー（MACD/BBなし）", **row_metrics(b)},
        {"rr": rr, "tier": "T5 + Strict MACD/BB", **row_metrics(strict)},
        {"rr": rr, "tier": "本番C125相当", **row_metrics(c125)},
    ]


def main() -> None:
    feature_frames = load_feature_frames()
    h4_data = {symbol: feature_frames[(symbol, TIMEFRAME)] for symbol in SYMBOLS}

    tier_rows: list[dict] = []
    for rr in (2.0, 2.5):
        spec = replace(BASE_SPEC, rr=rr)
        broad = run_t5_broad_with_spec(feature_frames, spec)
        v_only = run_v_candidate_only_with_spec(feature_frames, spec)
        tier_rows.extend(tier_table(broad, v_only, rr))

    tiers = pd.DataFrame(tier_rows)
    tiers.to_csv(OUT_DIR / "tier_comparison_2r_vs_25r.csv", index=False)

    ladder_rows = []
    ladder_rows.append(run_ladder_rr(2.0, h4_data))
    ladder_rows.append(run_ladder_rr(2.5, h4_data))
    ladder = pd.concat(ladder_rows, ignore_index=True)
    ladder.to_csv(OUT_DIR / "ladder_key_stages.csv", index=False)

    from run_elliott_fibo_study import markdown_table

    lines = [
        "# T5 / V-entry: 2.0R vs 2.5R 比較",
        "",
        "- 期間: 2015-2024（研究期）",
        "- 通貨: 7通貨のうち **AUDJPY除外**（6通貨相当）",
        "- SL: V安値 - 0.25 ATR（変更なし）",
        "- エントリー: シグナル次足始値",
        "- R: コスト込み `r_after_cost`",
        "",
        "## 段階別",
        "",
        markdown_table(tiers),
        "",
        "## ラダー主要ステージ",
        "",
        markdown_table(ladder),
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT_DIR / "report_ja.md").read_text(encoding="utf-8"))


def run_t5_broad_with_spec(feature_frames: dict[tuple[str, str], pd.DataFrame], spec: TriggerSpec) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for period, start, end in PERIODS:
        if period != "Research_2015_2024":
            continue
        trigger_mod.START = start
        trigger_mod.END = end
        for symbol in SYMBOLS:
            df = feature_frames[(symbol, TIMEFRAME)]
            trades = run_spec(df, symbol, TIMEFRAME, spec)
            if not trades.empty:
                trades["period"] = period
                frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def run_v_candidate_only_with_spec(
    feature_frames: dict[tuple[str, str], pd.DataFrame], spec: TriggerSpec
) -> pd.DataFrame:
    from run_t5_practical_robustness_audit import run_v_candidate_only_for_period, classify_period

    frames: list[pd.DataFrame] = []
    for symbol in SYMBOLS:
        df = feature_frames[(symbol, TIMEFRAME)]
        trades = run_v_candidate_only_for_period(df, symbol, RESEARCH_START, RESEARCH_END, spec)
        if not trades.empty:
            trades["period"] = "Research_2015_2024"
            frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    enriched["period"] = enriched["entry_time"].map(classify_period)
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


if __name__ == "__main__":
    main()

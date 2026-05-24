#!/usr/bin/env python3
"""
Robustness audit for the H4 V-candidate T5 + MACD + BB idea.

This is intentionally not an optimizer.  It generates the broad H4 T5
candidate universe first, then removes/adds conditions to see which pieces
actually carry edge and which pieces look fragile.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    Pivot,
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    simulate_trade,
    timeframe_settings,
)
from run_indicator_compatibility_search import add_extended_features, enrich_trades
from run_v_recovery_trigger_study import TriggerSpec, run_spec
import run_v_recovery_trigger_study as trigger_mod


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_24" / "t5_practical_robustness_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
PERIODS = [
    ("Research_2015_2024", pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31 23:59:59")),
    ("OOS_2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31 23:59:59")),
]

REC_RATIO = 1.20
BASE_SPEC = TriggerSpec(
    "REC1.20_T5_STAG_OR_REBREAK_BROAD",
    trigger_mode="either",
    max_recovery_to_drop=REC_RATIO,
)


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


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict[str, float | int]:
    r = df[r_col].astype(float) if not df.empty and r_col in df.columns else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def summary_row(name: str, df: pd.DataFrame, notes: str = "", r_col: str = "r_after_cost") -> dict:
    research = df[df["period"] == "Research_2015_2024"] if not df.empty else df
    oos = df[df["period"] == "OOS_2025_2026"] if not df.empty else df
    out = {"case": name, "notes": notes}
    all_m = metrics(df, r_col)
    res_m = metrics(research, r_col)
    oos_m = metrics(oos, r_col)
    out.update({f"all_{k}": v for k, v in all_m.items()})
    out.update({f"research_{k}": v for k, v in res_m.items()})
    out.update({f"oos_{k}": v for k, v in oos_m.items()})
    out["oos_positive"] = bool(oos_m["total_r"] > 0 and oos_m["avg_r"] > 0)
    out["oos_avg_retention"] = (
        float(oos_m["avg_r"] / res_m["avg_r"]) if res_m["avg_r"] not in (0, math.nan) and res_m["avg_r"] != 0 else math.nan
    )
    return out


def summarize_cases(cases: list[tuple[str, pd.DataFrame, str]]) -> pd.DataFrame:
    return pd.DataFrame([summary_row(name, sample, notes) for name, sample, notes in cases])


def true_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series(True, index=df.index)


def not_single_weak_rebreak(df: pd.DataFrame, macd_weak: float = 0.03) -> pd.Series:
    single_rebreak = df["trigger_type"].eq("rebreak")
    weak = df["bb_pos"].gt(0.95) | df["macd_hist_slope3"].le(macd_weak)
    return ~(single_rebreak & weak)


def practical_mask(
    df: pd.DataFrame,
    bb_upper: float = 0.95,
    recovery_max: int = 16,
    macd_min: float = 0.0,
    bb_width_max: float | None = None,
    use_rebreak_guard: bool = True,
) -> pd.Series:
    mask = (
        df["bb_pos"].ge(0.60)
        & df["bb_pos"].le(bb_upper)
        & df["signal_recovery_bars"].le(recovery_max)
        & df["macd_hist_slope3"].gt(macd_min)
    )
    if bb_width_max is not None:
        mask &= df["bb_width_atr"].le(bb_width_max)
    if use_rebreak_guard:
        mask &= not_single_weak_rebreak(df)
    return mask.fillna(False)


def classify_period(ts: pd.Timestamp) -> str:
    y = ts.year
    if y <= 2024:
        return "Research_2015_2024"
    return "OOS_2025_2026"


def run_t5_broad(feature_frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for period, start, end in PERIODS:
        trigger_mod.START = start
        trigger_mod.END = end
        for symbol in SYMBOLS:
            df = feature_frames[(symbol, TIMEFRAME)]
            trades = run_spec(df, symbol, TIMEFRAME, BASE_SPEC)
            if not trades.empty:
                trades["period"] = period
                frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    enriched["period"] = enriched["entry_time"].map(classify_period)
    enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)
    enriched["year"] = enriched["entry_time"].dt.year.astype(str)
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def v_candidate_only_signal(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: TriggerSpec,
    settings: dict,
) -> dict | None:
    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None

    for p0, p1 in zip(reversed(active[:-1]), reversed(active[1:])):
        if p0.kind != "H" or p1.kind != "L":
            continue
        if i <= p1.pivot_i:
            continue
        drop = p0.price - p1.price
        if drop <= 0 or drop < atr_i * spec.min_move_atr:
            continue
        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        drop_speed = drop / drop_bars / atr_i
        if drop_speed < spec.min_drop_speed:
            continue
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue
        ratio = (close - p1.price) / drop
        prev_ratio = (prev_close - p1.price) / drop
        if not (prev_ratio < spec.fib_min <= ratio <= spec.fib_max):
            continue
        recovery_bars = max(i - p1.pivot_i, 1)
        recovery_to_drop = recovery_bars / drop_bars
        if recovery_to_drop > spec.max_recovery_to_drop:
            continue
        stop = p1.price - atr_i * 0.25
        target = close + (close - stop) * spec.rr
        if target <= close or stop >= close:
            continue
        return {
            "direction": "long",
            "trigger_type": "v_candidate_only",
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "candidate_i": i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "v_move_atr": drop / atr_i,
            "v_move_bars": drop_bars,
            "v_drop_speed_atr_per_bar": drop_speed,
            "candidate_recovery_bars": recovery_bars,
            "candidate_recovery_to_drop_bars": recovery_to_drop,
            "signal_recovery_bars": recovery_bars,
            "signal_fib_ratio": ratio,
            "candidate_fib_min": spec.fib_min,
            "candidate_fib_max": spec.fib_max,
            "trigger_level": close,
            "stop": stop,
            "target": target,
            "candidate_key": f"{p0.pivot_i}-{p1.pivot_i}",
        }
    return None


def run_v_candidate_only_for_period(
    df: pd.DataFrame,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    spec: TriggerSpec,
) -> pd.DataFrame:
    settings = timeframe_settings(TIMEFRAME)
    settings["timeframe"] = TIMEFRAME
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    used_candidates: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < start or ts > end or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue
        sig = v_candidate_only_signal(df, i, active, spec, settings)
        if sig is None or sig["candidate_key"] in used_candidates:
            continue
        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=sig["direction"],
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
        )
        if trade is None:
            continue
        used_candidates.add(sig["candidate_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": "REC1.20_V_CANDIDATE_ONLY",
                "family": "V候補のみ",
                "signal_time": ts,
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "candidate_key"}},
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def run_v_candidate_only(feature_frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for period, start, end in PERIODS:
        for symbol in SYMBOLS:
            df = feature_frames[(symbol, TIMEFRAME)]
            trades = run_v_candidate_only_for_period(df, symbol, start, end, BASE_SPEC)
            if not trades.empty:
                trades["period"] = period
                frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    enriched["period"] = enriched["entry_time"].map(classify_period)
    enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)
    enriched["year"] = enriched["entry_time"].dt.year.astype(str)
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def condition_contribution(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    full = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0, use_rebreak_guard=True)
    cases = [
        ("00 Broad T5 universe", trades, "V候補後にstagnation/rebreak。追加フィルタなし"),
        ("01 Full strict practical", trades[full], "BB<=0.95, recovery<=16, MACD>0, BB幅<=4ATR, 弱い単独rebreak除外"),
        (
            "LOO remove BB<=0.95",
            trades[
                trades["bb_pos"].ge(0.60)
                & trades["signal_recovery_bars"].le(16)
                & trades["macd_hist_slope3"].gt(0)
                & trades["bb_width_atr"].le(4.0)
                & not_single_weak_rebreak(trades)
            ],
            "BB上限だけ外す",
        ),
        (
            "LOO remove recovery<=16",
            trades[
                trades["bb_pos"].between(0.60, 0.95)
                & trades["macd_hist_slope3"].gt(0)
                & trades["bb_width_atr"].le(4.0)
                & not_single_weak_rebreak(trades)
            ],
            "回復本数上限だけ外す",
        ),
        (
            "LOO remove MACD>0",
            trades[
                trades["bb_pos"].between(0.60, 0.95)
                & trades["signal_recovery_bars"].le(16)
                & trades["bb_width_atr"].le(4.0)
                & not_single_weak_rebreak(trades)
            ],
            "MACD slope3プラスだけ外す",
        ),
        (
            "LOO remove BB幅<=4ATR",
            trades[
                trades["bb_pos"].between(0.60, 0.95)
                & trades["signal_recovery_bars"].le(16)
                & trades["macd_hist_slope3"].gt(0)
                & not_single_weak_rebreak(trades)
            ],
            "BB幅上限だけ外す",
        ),
        (
            "LOO remove weak rebreak guard",
            trades[
                trades["bb_pos"].between(0.60, 0.95)
                & trades["signal_recovery_bars"].le(16)
                & trades["macd_hist_slope3"].gt(0)
                & trades["bb_width_atr"].le(4.0)
            ],
            "弱い単独rebreak除外だけ外す",
        ),
        ("Only stagnation", trades[full & trades["trigger_type"].eq("stagnation")], "Full条件 + stagnation単独"),
        ("Only rebreak", trades[full & trades["trigger_type"].eq("rebreak")], "Full条件 + rebreak単独"),
        ("Only stagnation+rebreak", trades[full & trades["trigger_type"].eq("stagnation+rebreak")], "Full条件 + 両方重なる"),
    ]
    table = summarize_cases(cases)

    full_metrics = table[table["case"].eq("01 Full strict practical")].iloc[0].to_dict()
    loo = table[table["case"].str.startswith("LOO")].copy()
    loo["pf_change_vs_full"] = loo["all_pf"] - full_metrics["all_pf"]
    loo["dd_change_vs_full"] = loo["all_max_dd_r"] - full_metrics["all_max_dd_r"]
    loo["avg_r_change_vs_full"] = loo["all_avg_r"] - full_metrics["all_avg_r"]
    loo["fragility_flag"] = np.where(
        (loo["all_pf"] < full_metrics["all_pf"] * 0.75)
        | (loo["all_max_dd_r"] > full_metrics["all_max_dd_r"] * 1.5)
        | (loo["all_avg_r"] < full_metrics["all_avg_r"] * 0.5),
        "外すと悪化が大きい",
        "外しても致命傷ではない",
    )
    return table, loo


def threshold_sweeps(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    sweeps: dict[str, pd.DataFrame] = {}

    bb_rows = []
    for value in [0.85, 0.90, 0.95, 1.00]:
        mask = practical_mask(trades, bb_upper=value, recovery_max=16, macd_min=0.0, bb_width_max=4.0)
        bb_rows.append(summary_row(f"BB<={value:.2f}", trades[mask], "lower BB fixed at 0.60"))
    sweeps["bb_position"] = pd.DataFrame(bb_rows)

    rec_rows = []
    for value in [8, 12, 16, 20, 24]:
        mask = practical_mask(trades, bb_upper=0.95, recovery_max=value, macd_min=0.0, bb_width_max=4.0)
        rec_rows.append(summary_row(f"Recovery<={value}", trades[mask], "BB<=0.95, MACD>0, BB幅<=4ATR"))
    sweeps["recovery_bars"] = pd.DataFrame(rec_rows)

    macd_rows = []
    for value in [0.00, 0.01, 0.02, 0.03, 0.05]:
        mask = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=value, bb_width_max=4.0)
        macd_rows.append(summary_row(f"MACD slope3>{value:.2f}", trades[mask], "BB<=0.95, recovery<=16, BB幅<=4ATR"))
    sweeps["macd_slope3"] = pd.DataFrame(macd_rows)

    bbw_rows = []
    for value in [2.0, 4.0, 5.0, 7.0]:
        mask = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=value)
        bbw_rows.append(summary_row(f"BB幅<={value:.0f}ATR", trades[mask], "BB<=0.95, recovery<=16, MACD>0"))
    sweeps["bb_width"] = pd.DataFrame(bbw_rows)

    return sweeps


def structure_analysis(t5_trades: pd.DataFrame, candidate_only: pd.DataFrame) -> pd.DataFrame:
    base_filter = (
        t5_trades["bb_pos"].between(0.60, 0.95)
        & t5_trades["signal_recovery_bars"].le(16)
        & t5_trades["macd_hist_slope3"].gt(0)
    ).fillna(False)
    cases = [
        ("A V candidate only", candidate_only, "61.8-80%回復候補で即エントリー"),
        ("B V + stagnation", t5_trades[base_filter & t5_trades["trigger_type"].eq("stagnation")], "V候補後の高値停滞のみ"),
        ("C V + rebreak", t5_trades[base_filter & t5_trades["trigger_type"].eq("rebreak")], "V候補後の再ブレイクのみ"),
        (
            "D V + stagnation+rebreak",
            t5_trades[base_filter & t5_trades["trigger_type"].eq("stagnation+rebreak")],
            "高値停滞と再ブレイクが同時に成立",
        ),
        ("T5 either broad", t5_trades, "V候補後にどちらかのT5トリガー"),
        ("T5 either practical", t5_trades[base_filter & not_single_weak_rebreak(t5_trades)], "T5 + BB<=0.95 + recovery<=16 + MACD>0"),
    ]
    return summarize_cases(cases)


def symbol_comparison(trades: pd.DataFrame) -> pd.DataFrame:
    mask = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0)
    rows = []
    for symbol, group in trades[mask].groupby("symbol"):
        row = {"symbol": symbol}
        row.update(metrics(group))
        row.update({f"oos_{k}": v for k, v in metrics(group[group["period"].eq("OOS_2025_2026")]).items()})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("total_r", ascending=False) if rows else pd.DataFrame()


def market_environment_analysis(trades: pd.DataFrame) -> pd.DataFrame:
    mask = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0)
    sample = trades[mask].copy()
    if sample.empty:
        return pd.DataFrame()

    entry = pd.to_datetime(sample["entry_time"])
    crisis = (
        entry.between(pd.Timestamp("2015-08-20"), pd.Timestamp("2015-09-30"))
        | entry.between(pd.Timestamp("2016-06-20"), pd.Timestamp("2016-07-15"))
        | entry.between(pd.Timestamp("2020-02-20"), pd.Timestamp("2020-04-30"))
        | entry.between(pd.Timestamp("2022-02-24"), pd.Timestamp("2022-04-30"))
        | entry.between(pd.Timestamp("2022-09-01"), pd.Timestamp("2022-11-15"))
        | entry.between(pd.Timestamp("2023-03-08"), pd.Timestamp("2023-04-15"))
    )
    env_masks = {
        "Trend up": (sample["ema20"] > sample["ema50"]) & (sample["ema20_slope_10_atr"] > 0) & (sample["adx14"] >= 18),
        "Range/choppy": (sample["chop14"] >= 55) | (sample["adx14"] < 15),
        "Vol spike": (sample["atr_ratio_50"] >= 1.5) | (sample["bb_width_atr"] > 7),
        "High ATR percentile": sample["atr_pctile_252"] >= 80,
        "Normal ATR": sample["atr_pctile_252"].between(20, 80),
        "Crisis windows": crisis,
        "Rate/news proxy": (sample["atr_ratio_50"] >= 1.2) & (sample["range5_atr"] >= 4),
        "Gold Monday proxy": sample["symbol"].eq("XAUUSD") & (entry.dt.dayofweek == 0),
    }
    rows = []
    for name, env_mask in env_masks.items():
        frame = sample[env_mask.fillna(False)].copy()
        row = {"environment": name}
        row.update(metrics(frame))
        row.update({f"oos_{k}": v for k, v in metrics(frame[frame["period"].eq("OOS_2025_2026")]).items()})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("avg_r", ascending=False)


def practical_execution_stress(trades: pd.DataFrame) -> pd.DataFrame:
    mask = practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0)
    sample = trades[mask].copy()
    if sample.empty:
        return pd.DataFrame()
    cost_r = sample["r_clean"] - sample["r_after_cost"]
    rows = []
    for name, r in [
        ("Base current cost", sample["r_after_cost"]),
        ("Spread/slippage x1.5", sample["r_clean"] - cost_r * 1.5),
        ("Spread/slippage x2.0", sample["r_clean"] - cost_r * 2.0),
        ("Spread/slippage x3.0", sample["r_clean"] - cost_r * 3.0),
        ("Extra execution -0.10R", sample["r_after_cost"] - 0.10),
        ("Extra execution -0.20R", sample["r_after_cost"] - 0.20),
    ]:
        frame = sample.copy()
        frame["stress_r"] = r
        row = {"case": name, "notes": "same trades, stressed R"}
        row.update({f"all_{k}": v for k, v in metrics(frame, "stress_r").items()})
        row.update({f"oos_{k}": v for k, v in metrics(frame[frame["period"].eq("OOS_2025_2026")], "stress_r").items()})
        rows.append(row)

    filters = [
        ("Exclude ATR ratio>=1.5", sample[sample["atr_ratio_50"] < 1.5], "高ボラ急増を除外"),
        ("Exclude ATR pctile>=80", sample[sample["atr_pctile_252"] < 80], "ATR上位20%を除外"),
        (
            "Exclude XAU Monday proxy",
            sample[~(sample["symbol"].eq("XAUUSD") & (pd.to_datetime(sample["entry_time"]).dt.dayofweek == 0))],
            "ゴールド週明けギャップ代理条件を除外",
        ),
    ]
    for name, frame, notes in filters:
        rows.append(summary_row(name, frame, notes))
    return pd.DataFrame(rows)


def overlap_with_trendbreak() -> pd.DataFrame:
    root = THIS_DIR.parents[1]
    combo_dir = root / "backtests" / "ensemble" / "trendbreak_t5_practical_combo_2015_2024"
    trend_path = combo_dir / "trendbreak_only_trades.csv"
    t5_path = combo_dir / "t5_practical_only_trades.csv"
    if not trend_path.exists() or not t5_path.exists():
        return pd.DataFrame()
    trend = pd.read_csv(trend_path, parse_dates=["entry_time", "exit_time"])
    t5 = pd.read_csv(t5_path, parse_dates=["entry_time", "exit_time"])
    rows = []
    for _, row in t5.iterrows():
        same = trend[trend["symbol"].eq(row["symbol"])]
        overlaps = same[(same["entry_time"] <= row["exit_time"]) & (same["exit_time"] >= row["entry_time"])]
        out = row.to_dict()
        out["overlaps_trendbreak_same_symbol"] = len(overlaps) > 0
        out["overlap_count"] = int(len(overlaps))
        rows.append(out)
    enriched = pd.DataFrame(rows)
    if not enriched.empty and "r_after_cost" not in enriched.columns and "r" in enriched.columns:
        enriched["r_after_cost"] = enriched["r"]
    if not enriched.empty and "period" not in enriched.columns:
        enriched["period"] = pd.to_datetime(enriched["entry_time"]).map(classify_period)
    cases = [
        ("T5 all 2015-2024", enriched, ""),
        ("T5 overlaps TrendBreak", enriched[enriched["overlaps_trendbreak_same_symbol"]], "同通貨で保有期間が重なる"),
        ("T5 independent from TrendBreak", enriched[~enriched["overlaps_trendbreak_same_symbol"]], "同通貨の保有期間重複なし"),
    ]
    return summarize_cases(cases)


def sensitivity_warnings(sweeps: dict[str, pd.DataFrame]) -> list[str]:
    warnings: list[str] = []
    for name, table in sweeps.items():
        if table.empty or len(table) < 3:
            continue
        best_i = int(table["all_avg_r"].idxmax())
        best = table.loc[best_i]
        avg = float(table["all_avg_r"].mean())
        if float(best["all_avg_r"]) > avg * 1.8 and int(best["all_trades"]) < 15:
            warnings.append(f"{name}: 1点だけ平均Rが突出し、取引数も少ないため過去最適化疑い。")
        positives = int((table["all_avg_r"] > 0).sum())
        if positives <= max(1, len(table) // 2):
            warnings.append(f"{name}: 近い閾値で優位性が残りにくく、条件が不安定。")
    return warnings


def write_report(
    trades: pd.DataFrame,
    candidate_only: pd.DataFrame,
    contribution: pd.DataFrame,
    loo: pd.DataFrame,
    sweeps: dict[str, pd.DataFrame],
    structure: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_env: pd.DataFrame,
    stress: pd.DataFrame,
    overlap: pd.DataFrame,
) -> None:
    compact = [
        "case",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "oos_trades",
        "oos_win_rate",
        "oos_total_r",
        "oos_avg_r",
        "oos_pf",
        "oos_max_dd_r",
        "notes",
    ]
    warnings = sensitivity_warnings(sweeps)
    keep = [
        "BB位置上限は残す。ただし0.90〜1.00付近で滑らかに残るかを見る。",
        "V候補からシグナルまでの時間制限は残す。遅い戻りはV字の本質から外れやすい。",
        "MACD slope3は単独rebreakの弱さを避ける目的で残す。",
        "BB幅<=4ATRはDD抑制条件として残す。取引数を増やす場合でも5ATRまでを上限候補にする。",
        "stagnation / rebreak はエントリー条件。V候補だけで入らない。",
    ]
    removable = [
        "weak rebreak guardはBB位置/MACD条件と重複しやすいので、必須条件ではなく警告・補助条件へ降格可能。",
        "stagnation+rebreakだけに限定すると強いが、取引数が少なすぎる場合は候補として残すだけにする。",
    ]
    lines = [
        "# H4 V候補 T5 + MACD + BB ロバスト性監査",
        "",
        "## 前提",
        "",
        "- 研究期間: 2015-2024。",
        "- OOS/未使用期間: 2025-2026。追加ファイルがある範囲まで使用。",
        "- 母集団: H4で急落後61.8%〜80%回復候補を作り、その後 `stagnation` または `rebreak` が出たT5。",
        "- V候補は環境認識。実際のエントリーはT5トリガー後。",
        "- Rはコスト込み `r_after_cost`。",
        "",
        "## データ件数",
        "",
        f"- T5 broad trades: {len(trades)}",
        f"- V candidate only trades: {len(candidate_only)}",
        "",
        "## 1. 条件寄与率分析",
        "",
        markdown_table(contribution[compact], 80),
        "",
        "### Leave-one-out 判定",
        "",
        markdown_table(
            loo[
                [
                    "case",
                    "all_trades",
                    "all_total_r",
                    "all_avg_r",
                    "all_pf",
                    "all_max_dd_r",
                    "pf_change_vs_full",
                    "dd_change_vs_full",
                    "avg_r_change_vs_full",
                    "fragility_flag",
                ]
            ],
            40,
        ),
        "",
        "## 2. 閾値感度分析",
        "",
    ]
    for name, table in sweeps.items():
        lines.extend([f"### {name}", "", markdown_table(table[compact], 50), ""])
    lines.extend(
        [
            "### 感度分析の警告",
            "",
            "\n".join(f"- {w}" for w in warnings) if warnings else "- 大きな一点突出は検出されませんでした。ただしOOS取引数が少ない箇所は保守的に見るべきです。",
            "",
            "## 3. 構造分析",
            "",
            markdown_table(structure[compact], 50),
            "",
            "## 4. 通貨別比較",
            "",
            markdown_table(by_symbol, 80),
            "",
            "## 5. 市場環境別比較",
            "",
            markdown_table(by_env, 80),
            "",
            "## 6. TrendBreakV1 との重複リスク",
            "",
            markdown_table(overlap[compact], 20) if not overlap.empty else "_重複分析用CSVが見つかりませんでした._",
            "",
            "## 7. 実戦性ストレス",
            "",
            markdown_table(stress, 80),
            "",
            "## 崩れやすい条件",
            "",
            "- OOS取引数が少ないため、PFだけで判断すると危険。",
            "- `V candidate only` が弱い場合、V字そのものではなく、その後の再加速構造が本体。",
            "- `rebreak` 単独はMACDが弱い時に崩れやすい。単独rebreakは選別が必要。",
            "- ボラ急増・ATR上位・BB幅過大は、方向が合ってもSLに触れやすい。",
            "",
            "## 実戦で残すべき条件",
            "",
            "\n".join(f"- {x}" for x in keep),
            "",
            "## 削除または降格してもよい条件",
            "",
            "\n".join(f"- {x}" for x in removable),
            "",
            "## 実戦で最も壊れにくい最小構成案",
            "",
            "1. H4で急落後V候補を作る。V候補だけでは入らない。",
            "2. 回復候補は急落の61.8%〜80%。回復は急落本数の1.20倍以内を基本にする。",
            "3. T5トリガーは `stagnation` または `rebreak`。両方重なる場合は最優先。",
            "4. BB位置は0.60〜0.95を基本。0.95超は見送り。",
            "5. MACD slope3はプラスを要求。単独rebreakは0.03以下なら見送り。",
            "6. BB幅<=4ATRを標準にする。取引数を増やす検証では5ATRまで緩和し、それ以上は過熱扱い。",
            "7. TrendBreakV1と同通貨で同時期に重なる場合は、同じ相場リスクとみなし合計リスクを下げる。",
            "",
            "## 出力CSV",
            "",
            "- `t5_broad_trades_2015_2026.csv`",
            "- `v_candidate_only_trades_2015_2026.csv`",
            "- `condition_contribution.csv`",
            "- `leave_one_out_fragility.csv`",
            "- `sweep_*.csv`",
            "- `structure_analysis.csv`",
            "- `by_symbol_practical.csv`",
            "- `market_environment.csv`",
            "- `execution_stress.csv`",
            "- `trendbreak_overlap.csv`",
        ]
    )
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    coverage_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        feature_frames[(symbol, TIMEFRAME)] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    t5_trades = run_t5_broad(feature_frames)
    candidate_only = run_v_candidate_only(feature_frames)
    t5_trades.to_csv(OUT_DIR / "t5_broad_trades_2015_2026.csv", index=False)
    candidate_only.to_csv(OUT_DIR / "v_candidate_only_trades_2015_2026.csv", index=False)

    contribution, loo = condition_contribution(t5_trades)
    sweeps = threshold_sweeps(t5_trades)
    structure = structure_analysis(t5_trades, candidate_only)
    by_symbol = symbol_comparison(t5_trades)
    by_env = market_environment_analysis(t5_trades)
    stress = practical_execution_stress(t5_trades)
    overlap = overlap_with_trendbreak()

    contribution.to_csv(OUT_DIR / "condition_contribution.csv", index=False)
    loo.to_csv(OUT_DIR / "leave_one_out_fragility.csv", index=False)
    for name, table in sweeps.items():
        table.to_csv(OUT_DIR / f"sweep_{name}.csv", index=False)
    structure.to_csv(OUT_DIR / "structure_analysis.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol_practical.csv", index=False)
    by_env.to_csv(OUT_DIR / "market_environment.csv", index=False)
    stress.to_csv(OUT_DIR / "execution_stress.csv", index=False)
    overlap.to_csv(OUT_DIR / "trendbreak_overlap.csv", index=False)

    write_report(
        t5_trades,
        candidate_only,
        contribution,
        loo,
        sweeps,
        structure,
        by_symbol,
        by_env,
        stress,
        overlap,
    )
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(contribution[["case", "all_trades", "all_total_r", "all_avg_r", "all_pf", "all_max_dd_r", "oos_trades", "oos_total_r"]].to_string(index=False))


if __name__ == "__main__":
    main()

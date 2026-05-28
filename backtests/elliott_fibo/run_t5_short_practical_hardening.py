#!/usr/bin/env python3
"""
Practical hardening for the H4 high-volatility short-continuation idea.

This script takes the inverse-V/T5 short universe, then tests whether the
promising high-volatility fragments survive practical changes:

- shorter fixed targets
- 1R partial take-profit
- break-even after 1R
- simple trailing stop after 1R
- no-progress time exits
- train/test/OOS and cost stress checks
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
    direction_cost_r,
    load_instrument,
    markdown_table,
    resample_ohlc,
)


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "t5_short_mirror_validation" / "short_t5_broad_trades_2015_2026.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "t5_short_practical_hardening"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
MAX_HOLD_BARS = 180


@dataclass(frozen=True)
class ExitSpec:
    name: str
    target_rr: float = 2.0
    partial_1r: bool = False
    be_after_1r: bool = False
    trail_atr_after_1r: float | None = None
    no_progress_bars: int | None = None
    max_hold_bars: int = MAX_HOLD_BARS


@dataclass(frozen=True)
class RuleSpec:
    name: str
    notes: str
    fn: Callable[[pd.DataFrame], pd.Series]


EXIT_SPECS = [
    ExitSpec("fixed_2R", target_rr=2.0),
    ExitSpec("fixed_1_5R", target_rr=1.5),
    ExitSpec("fixed_1R", target_rr=1.0),
    ExitSpec("BE_after_1R_to_2R", target_rr=2.0, be_after_1r=True),
    ExitSpec("half_1R_BE_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True),
    ExitSpec("half_1R_BE_rest_2R_time12", target_rr=2.0, partial_1r=True, be_after_1r=True, no_progress_bars=12),
    ExitSpec("half_1R_trail1ATR_rest_2R", target_rr=2.0, partial_1r=True, be_after_1r=True, trail_atr_after_1r=1.0),
    ExitSpec("fixed_2R_no_progress12", target_rr=2.0, no_progress_bars=12),
    ExitSpec("fixed_2R_max48", target_rr=2.0, max_hold_bars=48),
]


def rule_specs() -> list[RuleSpec]:
    return [
        RuleSpec(
            "R0_broad_short_t5",
            "逆V候補後T5ショート全体。比較用。",
            lambda d: pd.Series(True, index=d.index),
        ),
        RuleSpec(
            "R1_hv_core",
            "rebreak + ADX>=25 + BB幅7-10ATR + BB位置0-0.25。",
            lambda d: d["trigger_type"].eq("rebreak")
            & d["adx14"].ge(25)
            & d["bb_width_atr"].between(7, 10)
            & d["bb_pos"].between(0, 0.25),
        ),
        RuleSpec(
            "R2_hv_adx_width",
            "ADX>=25 + BB幅7-10ATR。rebreak限定なし。",
            lambda d: d["adx14"].ge(25) & d["bb_width_atr"].between(7, 10),
        ),
        RuleSpec(
            "R3_gbp_aud_adx",
            "GBPJPY/AUDJPY + ADX>=25。",
            lambda d: d["symbol"].isin(["GBPJPY", "AUDJPY"]) & d["adx14"].ge(25),
        ),
        RuleSpec(
            "R4_gbp_aud_adx_rebreak",
            "GBPJPY/AUDJPY + ADX>=25 + rebreak。",
            lambda d: d["symbol"].isin(["GBPJPY", "AUDJPY"]) & d["adx14"].ge(25) & d["trigger_type"].eq("rebreak"),
        ),
        RuleSpec(
            "R5_gbp_aud_atr80_rebreak",
            "GBPJPY/AUDJPY + ATR percentile>=80 + rebreak。",
            lambda d: d["symbol"].isin(["GBPJPY", "AUDJPY"]) & d["atr_pctile_252"].ge(80) & d["trigger_type"].eq("rebreak"),
        ),
        RuleSpec(
            "R6_macd_turn_rebreak",
            "rebreak + MACD slope3>0。売り遅れを避ける仮説。",
            lambda d: d["trigger_type"].eq("rebreak") & d["macd_hist_slope3"].gt(0),
        ),
        RuleSpec(
            "R7_gbp_only_adx",
            "GBPJPY専用 + ADX>=25。",
            lambda d: d["symbol"].eq("GBPJPY") & d["adx14"].ge(25),
        ),
        RuleSpec(
            "R8_gbp_only_slow",
            "GBPJPY専用 + signal_recovery_bars>16。",
            lambda d: d["symbol"].eq("GBPJPY") & d["signal_recovery_bars"].gt(16),
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


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost_model") -> dict[str, float | int]:
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


def classify_window(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2021-01-01"):
        return "train_2015_2020"
    if ts <= pd.Timestamp("2024-12-31 23:59:59"):
        return "test_2021_2024"
    return "oos_2025_2026"


def add_prefix(prefix: str, values: dict[str, float | int]) -> dict[str, float | int]:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def summary_row(rule: str, exit_name: str, sample: pd.DataFrame, notes: str = "") -> dict:
    train = sample[sample["wf_window"].eq("train_2015_2020")] if not sample.empty else sample
    test = sample[sample["wf_window"].eq("test_2021_2024")] if not sample.empty else sample
    oos = sample[sample["wf_window"].eq("oos_2025_2026")] if not sample.empty else sample
    row = {"rule": rule, "exit": exit_name, "notes": notes}
    row.update(add_prefix("all", metrics(sample)))
    row.update(add_prefix("train", metrics(train)))
    row.update(add_prefix("test", metrics(test)))
    row.update(add_prefix("oos", metrics(oos)))
    row["test_positive"] = bool(row["test_total_r"] > 0 and row["test_avg_r"] > 0)
    row["oos_nonnegative"] = bool(row["oos_total_r"] >= 0)
    return row


def load_h4_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for symbol in SYMBOLS:
        frames[symbol] = add_indicators(resample_ohlc(load_instrument(symbol), TIMEFRAME))
    return frames


def _weighted_r(symbol: str, entry: float, exit_price: float, risk: float, weight: float) -> tuple[float, float]:
    clean, after = direction_cost_r(symbol, "short", entry, exit_price, risk)
    return clean * weight, after * weight


def simulate_exit(row: pd.Series, df: pd.DataFrame, spec: ExitSpec) -> dict:
    symbol = str(row["symbol"])
    entry_time = pd.Timestamp(row["entry_time"])
    if entry_time not in df.index:
        raise KeyError(f"entry_time not found in {symbol}: {entry_time}")

    entry_i = int(df.index.get_loc(entry_time))
    entry = float(row["entry"])
    stop = float(row["stop"])
    risk = stop - entry
    if risk <= 0:
        return {"exit_time_model": entry_time, "exit_model": entry, "exit_reason_model": "bad_risk", "r_clean_model": 0.0, "r_after_cost_model": 0.0, "bars_held_model": 0}

    target = entry - risk * spec.target_rr
    tp1 = entry - risk
    max_i = min(len(df) - 1, entry_i + spec.max_hold_bars)

    realized_clean = 0.0
    realized_after = 0.0
    remaining = 1.0
    current_stop = stop
    tp1_hit = False
    tp1_bar: int | None = None
    mfe = 0.0
    exit_i = max_i
    exit_price = float(df["close"].iloc[max_i])
    reason = "max_hold"

    for j in range(entry_i, max_i + 1):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        close = float(df["close"].iloc[j])
        mfe = max(mfe, (entry - lo) / risk)

        if tp1_hit and spec.trail_atr_after_1r is not None and j > (tp1_bar or entry_i):
            prev = df.iloc[j - 1]
            prev_atr = float(prev["atr"])
            if math.isfinite(prev_atr) and prev_atr > 0:
                trail_stop = float(prev["high"]) + prev_atr * spec.trail_atr_after_1r
                current_stop = min(current_stop, trail_stop)

        hit_sl = hi >= current_stop
        hit_tp = lo <= target

        if hit_sl:
            clean, after = _weighted_r(symbol, entry, current_stop, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = current_stop
            reason = "SL_or_BE" if current_stop <= entry else "SL"
            remaining = 0.0
            break

        if hit_tp:
            if spec.partial_1r and not tp1_hit:
                clean, after = _weighted_r(symbol, entry, tp1, risk, 0.5)
                realized_clean += clean
                realized_after += after
                remaining = 0.5
            clean, after = _weighted_r(symbol, entry, target, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = target
            reason = "TP"
            remaining = 0.0
            break

        if not tp1_hit and lo <= tp1:
            tp1_hit = True
            tp1_bar = j
            if spec.partial_1r:
                clean, after = _weighted_r(symbol, entry, tp1, risk, 0.5)
                realized_clean += clean
                realized_after += after
                remaining = 0.5
            if spec.be_after_1r:
                current_stop = min(current_stop, entry)
                if hi >= current_stop:
                    clean, after = _weighted_r(symbol, entry, current_stop, risk, remaining)
                    realized_clean += clean
                    realized_after += after
                    exit_i = j
                    exit_price = current_stop
                    reason = "TP1_then_BE_same_bar"
                    remaining = 0.0
                    break

        if spec.no_progress_bars is not None and not tp1_hit and (j - entry_i + 1) >= spec.no_progress_bars:
            clean, after = _weighted_r(symbol, entry, close, risk, remaining)
            realized_clean += clean
            realized_after += after
            exit_i = j
            exit_price = close
            reason = "no_progress_exit"
            remaining = 0.0
            break

    if remaining > 0:
        clean, after = _weighted_r(symbol, entry, exit_price, risk, remaining)
        realized_clean += clean
        realized_after += after

    return {
        "exit_time_model": df.index[exit_i],
        "exit_model": exit_price,
        "exit_reason_model": reason,
        "r_clean_model": realized_clean,
        "r_after_cost_model": realized_after,
        "bars_held_model": int(exit_i - entry_i),
        "mfe_r_model": float(mfe),
    }


def build_exit_models(source: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        df = frames[str(row["symbol"])]
        base = row.to_dict()
        for spec in EXIT_SPECS:
            if spec.name == "fixed_2R":
                out = {
                    "exit_time_model": row["exit_time"],
                    "exit_model": row["exit"],
                    "exit_reason_model": row["exit_reason"],
                    "r_clean_model": float(row["r_clean"]),
                    "r_after_cost_model": float(row["r_after_cost"]),
                    "bars_held_model": int(row["bars_held"]),
                    "mfe_r_model": np.nan,
                }
            else:
                out = simulate_exit(row, df, spec)
            rows.append({**base, "exit_variant": spec.name, **out})
    model = pd.DataFrame(rows)
    model["entry_time"] = pd.to_datetime(model["entry_time"])
    model["exit_time_model"] = pd.to_datetime(model["exit_time_model"])
    model["wf_window"] = model["entry_time"].map(classify_window)
    return model.sort_values(["exit_variant", "entry_time", "symbol"]).reset_index(drop=True)


def evaluate_rules(model: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    selected_trades = []
    for rule in rule_specs():
        base_mask = rule.fn(model)
        for exit_name, group in model[base_mask.fillna(False)].groupby("exit_variant"):
            rows.append(summary_row(rule.name, exit_name, group, rule.notes))
            selected = group.copy()
            selected["rule"] = rule.name
            selected_trades.append(selected)
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary["score"] = (
            summary["all_total_r"]
            + summary["test_total_r"] * 1.5
            + summary["all_avg_r"] * 5
            + np.minimum(summary["all_pf"].replace(math.inf, 99), 5)
            - summary["all_max_dd_r"] * 0.35
            - np.where(summary["all_trades"] < 12, 2.0, 0.0)
            - np.where(summary["oos_trades"].eq(0), 1.5, 0.0)
            + np.where(summary["oos_total_r"].ge(0), 0.5, -1.0)
        )
        summary = summary.sort_values(["score", "all_total_r"], ascending=False).reset_index(drop=True)

    trades = pd.concat(selected_trades, ignore_index=True) if selected_trades else pd.DataFrame()

    best = summary[summary["rule"].ne("R0_broad_short_t5")].head(1)
    if best.empty:
        return summary, trades, pd.DataFrame(), pd.DataFrame()
    best_rule = str(best.iloc[0]["rule"])
    best_exit = str(best.iloc[0]["exit"])
    best_trades = trades[trades["rule"].eq(best_rule) & trades["exit_variant"].eq(best_exit)].copy()

    year_rows = []
    for year, group in best_trades.groupby("year"):
        row = {"year": year}
        row.update(metrics(group))
        year_rows.append(row)
    by_year = pd.DataFrame(year_rows).sort_values("year") if year_rows else pd.DataFrame()

    stress_rows = []
    if not best_trades.empty:
        cost_r = best_trades["r_clean_model"].astype(float) - best_trades["r_after_cost_model"].astype(float)
        stress_defs = {
            "base": best_trades["r_after_cost_model"],
            "cost_x1_5": best_trades["r_clean_model"] - cost_r * 1.5,
            "cost_x2": best_trades["r_clean_model"] - cost_r * 2.0,
            "extra_-0_10R": best_trades["r_after_cost_model"] - 0.10,
            "extra_-0_20R": best_trades["r_after_cost_model"] - 0.20,
        }
        for name, values in stress_defs.items():
            temp = best_trades.copy()
            temp["stress_r"] = values
            row = {"stress": name}
            row.update(metrics(temp, "stress_r"))
            row.update(add_prefix("oos", metrics(temp[temp["wf_window"].eq("oos_2025_2026")], "stress_r")))
            stress_rows.append(row)
    stress = pd.DataFrame(stress_rows)
    return summary, trades, by_year, stress


def write_report(summary: pd.DataFrame, by_year: pd.DataFrame, stress: pd.DataFrame) -> None:
    compact = [
        "rule",
        "exit",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "train_trades",
        "train_total_r",
        "test_trades",
        "test_total_r",
        "oos_trades",
        "oos_total_r",
        "score",
    ]
    top = summary[summary["rule"].ne("R0_broad_short_t5")].head(30) if not summary.empty else summary
    lines = [
        "# H4 高ボラ下落継続ショート 実戦化監査",
        "",
        "## 結論",
        "",
        "- 入口だけならプラス断片はあるが、出口を変えてもOOSは強くならない。",
        "- 2025-2026の発生数が少なく、発生した候補も小幅マイナスになりやすい。",
        "- 現時点では本番採用不可。使うならフォワード観察専用。",
        "- 実戦化するなら、`GBPJPY/AUDJPY + ADX>=25` を監視対象にし、固定2Rより部分利確/建値移動を優先して検証継続。",
        "",
        "## 上位候補",
        "",
        markdown_table(top[compact], 40) if not top.empty else "_No rows._",
        "",
        "## 暫定ベスト候補 年別",
        "",
        markdown_table(by_year, 80) if not by_year.empty else "_No rows._",
        "",
        "## 暫定ベスト候補 コストストレス",
        "",
        markdown_table(stress, 20) if not stress.empty else "_No rows._",
        "",
        "## 実戦判断",
        "",
        "- 最小ルール候補: `GBPJPY/AUDJPY + ADX>=25` または `rebreak + ADX>=25 + BB幅7〜10ATR`。",
        "- ただし、どちらもOOSで十分なプラス確認がない。",
        "- ロット投入ではなく、アラートだけ出して30〜50件のフォワード記録を取る段階。",
        "- 見送り条件: `BB幅<=4ATR`, `MACD slope3<0` を根拠にした売り, `ADX<25`, 低ボラの安値割れ。",
        "",
        "## 出力CSV",
        "",
        "- `exit_model_trades.csv`",
        "- `rule_exit_summary.csv`",
        "- `selected_rule_trades.csv`",
        "- `selected_by_year.csv`",
        "- `selected_cost_stress.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Run run_t5_short_mirror_validation.py first: {SOURCE}")

    source = pd.read_csv(SOURCE, parse_dates=["signal_time", "entry_time", "exit_time"])
    frames = load_h4_frames()
    model = build_exit_models(source, frames)
    summary, trades, by_year, stress = evaluate_rules(model)

    model.to_csv(OUT_DIR / "exit_model_trades.csv", index=False)
    summary.to_csv(OUT_DIR / "rule_exit_summary.csv", index=False)
    by_year.to_csv(OUT_DIR / "selected_by_year.csv", index=False)
    stress.to_csv(OUT_DIR / "selected_cost_stress.csv", index=False)
    if not summary.empty:
        best = summary[summary["rule"].ne("R0_broad_short_t5")].head(1)
        if not best.empty and not trades.empty:
            best_rule = str(best.iloc[0]["rule"])
            best_exit = str(best.iloc[0]["exit"])
            trades[trades["rule"].eq(best_rule) & trades["exit_variant"].eq(best_exit)].to_csv(OUT_DIR / "selected_rule_trades.csv", index=False)

    write_report(summary, by_year, stress)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if not summary.empty:
        cols = [
            "rule",
            "exit",
            "all_trades",
            "all_total_r",
            "all_avg_r",
            "all_pf",
            "test_trades",
            "test_total_r",
            "oos_trades",
            "oos_total_r",
            "score",
        ]
        print(summary[summary["rule"].ne("R0_broad_short_t5")][cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Synapse/Tobi-style discretionary wave idea, converted to a first mechanical
research model.

This is intentionally a v0 approximation, not a claim that the discretionary
method has been fully reproduced.  The purpose is to make the ideas testable:

- A/B break: wave-3 extreme breaks the prior wave-1 extreme.
- B entry: enter on the break of the wave-3 extreme after a wave-4 pullback.
- Wall reaction: the pullback reaches half / fib retracement zones.
- Diagonal return: the pullback returns to a projected channel line.
- Trade judgement: normal lot / half lot / skip, based on a score.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "results_2026_05_24"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))

from sai_backtest import INSTRUMENTS, atr, load_instrument  # noqa: E402


SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
TIMEFRAME = "H4"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")
ATR_PERIOD = 14
RR = 3.0
MAX_HOLD_BARS = 120

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}

FIB_WALLS = [0.50, 0.618, 0.736, 0.764]


@dataclass(frozen=True)
class Pivot:
    pivot_i: int
    confirm_i: int
    kind: str
    price: float
    atr: float


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "H1":
        return df.copy()
    rule = {"H4": "4h", "D1": "1D"}[timeframe]
    return (
        df.resample(rule, label="left", closed="left")
        .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .dropna()
    )


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"], ATR_PERIOD)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_ratio"] = ((out["close"] - out["open"]).abs() / rng).fillna(0.0)
    return out


def holiday_market(ts: pd.Timestamp) -> bool:
    return (ts.month == 12 and ts.day >= 15) or (ts.month == 1 and ts.day <= 10)


def build_confirmed_pivots(df: pd.DataFrame, width: int, min_swing_atr: float) -> list[Pivot]:
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    atrs = df["atr"].to_numpy()
    raw: list[Pivot] = []
    for i in range(width, len(df) - width):
        if not math.isfinite(atrs[i]) or atrs[i] <= 0:
            continue
        hwin = highs[i - width : i + width + 1]
        lwin = lows[i - width : i + width + 1]
        is_high = highs[i] >= np.nanmax(hwin)
        is_low = lows[i] <= np.nanmin(lwin)
        if is_high and not is_low:
            raw.append(Pivot(i, i + width, "H", float(highs[i]), float(atrs[i])))
        elif is_low and not is_high:
            raw.append(Pivot(i, i + width, "L", float(lows[i]), float(atrs[i])))

    raw.sort(key=lambda p: (p.confirm_i, p.pivot_i))
    pivots: list[Pivot] = []
    for p in raw:
        if not pivots:
            pivots.append(p)
            continue
        last = pivots[-1]
        if p.kind == last.kind:
            if (p.kind == "H" and p.price > last.price) or (p.kind == "L" and p.price < last.price):
                pivots[-1] = p
            continue
        swing = abs(p.price - last.price)
        threshold = max(p.atr, last.atr) * min_swing_atr
        if swing >= threshold:
            pivots.append(p)
    return pivots


def pivots_until(pivots: list[Pivot], pointer: int, bar_i: int, active: list[Pivot]) -> int:
    while pointer < len(pivots) and pivots[pointer].confirm_i <= bar_i:
        active.append(pivots[pointer])
        pointer += 1
    return pointer


def nearest_wall(price: float, start: float, end: float, direction: str, atr_value: float) -> tuple[float, float, float]:
    move = abs(end - start)
    if move <= 0 or atr_value <= 0:
        return math.nan, math.nan, math.nan
    if direction == "long":
        levels = [(ratio, end - move * ratio) for ratio in FIB_WALLS]
    else:
        levels = [(ratio, end + move * ratio) for ratio in FIB_WALLS]
    ratio, level = min(levels, key=lambda item: abs(price - item[1]))
    return ratio, level, abs(price - level) / atr_value


def channel_projection(p0: Pivot, p1: Pivot, at_i: int) -> tuple[float, float]:
    bars = max(p1.pivot_i - p0.pivot_i, 1)
    slope = (p1.price - p0.price) / bars
    projected = p1.price + slope * (at_i - p1.pivot_i)
    return projected, slope


def score_candidate(
    direction: str,
    a_break: bool,
    retrace: float,
    wall_dist_atr: float,
    channel_dist_atr: float,
    slope_atr_per_bar: float,
    time_ratio: float,
    body_ratio: float,
    wave3_vs_wave1: float,
) -> tuple[float, str, float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    if a_break:
        score += 2.0
        reasons.append("A-break")
    else:
        score -= 2.0
        reasons.append("no-A-break")

    if 0.618 <= retrace <= 0.886:
        score += 2.0
        reasons.append("deep-retrace")
    elif 0.50 <= retrace < 0.618:
        score += 1.0
        reasons.append("half-retrace")
    else:
        score -= 3.0
        reasons.append("bad-retrace")

    if wall_dist_atr <= 0.35:
        score += 2.0
        reasons.append("wall-reaction")
    elif wall_dist_atr <= 0.60:
        score += 1.0
        reasons.append("near-wall")

    if channel_dist_atr <= 0.50:
        score += 2.0
        reasons.append("diagonal-return")
    elif channel_dist_atr <= 0.85:
        score += 1.0
        reasons.append("near-diagonal")
    elif channel_dist_atr > 1.50:
        score -= 1.0
        reasons.append("channel-kairi")

    if abs(slope_atr_per_bar) <= 0.12:
        score += 1.0
        reasons.append("gentle-channel")
    elif abs(slope_atr_per_bar) > 0.30:
        score -= 1.0
        reasons.append("steep-channel")

    if 0.45 <= time_ratio <= 1.80:
        score += 1.0
        reasons.append("time-balanced")
    elif time_ratio < 0.25:
        score -= 1.0
        reasons.append("too-fast-pullback")

    if body_ratio >= 0.45:
        score += 1.0
        reasons.append("break-candle")

    if wave3_vs_wave1 >= 0.80:
        score += 1.0
        reasons.append("wave3-strength")

    grade = "skip"
    risk_weight = 0.0
    if score >= 8.0 and a_break and wall_dist_atr <= 0.60 and channel_dist_atr <= 0.85:
        grade = "normal"
        risk_weight = 1.0
    elif score >= 6.0 and a_break and (wall_dist_atr <= 0.60 or channel_dist_atr <= 0.85):
        grade = "half"
        risk_weight = 0.5

    return score, grade, risk_weight, reasons


def synapse_signal(df: pd.DataFrame, i: int, active: list[Pivot]) -> dict | None:
    if len(active) < 5:
        return None

    p = active[-5:]
    kinds = "".join(x.kind for x in p)
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    body_ratio = float(df["body_ratio"].iloc[i])
    buffer = atr_i * 0.05

    if kinds == "LHLHL":
        l0, h1, l2, h3, l4 = p
        wave1 = h1.price - l0.price
        wave3 = h3.price - l2.price
        if wave1 <= 0 or wave3 <= 0:
            return None
        structure_ok = h3.price > h1.price and l2.price > l0.price and l4.price > l2.price
        if not structure_ok:
            return None
        if not (prev_close <= h3.price and close > h3.price + buffer):
            return None
        retrace = (h3.price - l4.price) / wave3
        wall_ratio, wall_level, wall_dist = nearest_wall(l4.price, l2.price, h3.price, "long", l4.atr)
        channel_level, slope = channel_projection(l0, l2, l4.pivot_i)
        channel_dist = abs(l4.price - channel_level) / max(l4.atr, 1e-9)
        slope_atr = slope / max(l4.atr, 1e-9)
        time_ratio = (l4.pivot_i - h3.pivot_i) / max(h3.pivot_i - l2.pivot_i, 1)
        wave3_vs_wave1 = wave3 / wave1
        a_break = h3.price > h1.price
        score, grade, risk_weight, reasons = score_candidate(
            "long", a_break, retrace, wall_dist, channel_dist, slope_atr, time_ratio, body_ratio, wave3_vs_wave1
        )
        if grade == "skip":
            return None
        stop = l4.price - atr_i * 0.20
        if close <= stop:
            return None
        return {
            "direction": "long",
            "grade": grade,
            "risk_weight": risk_weight,
            "score": score,
            "reasons": ",".join(reasons),
            "trigger_level": h3.price,
            "stop": stop,
            "wall_ratio": wall_ratio,
            "wall_level": wall_level,
            "wall_dist_atr": wall_dist,
            "channel_level": channel_level,
            "channel_dist_atr": channel_dist,
            "slope_atr_per_bar": slope_atr,
            "retrace": retrace,
            "time_ratio": time_ratio,
            "wave3_vs_wave1": wave3_vs_wave1,
            "signal_body_ratio": body_ratio,
            "pivots": f"{l0.pivot_i}-{h1.pivot_i}-{l2.pivot_i}-{h3.pivot_i}-{l4.pivot_i}",
        }

    if kinds == "HLHLH":
        h0, l1, h2, l3, h4 = p
        wave1 = h0.price - l1.price
        wave3 = h2.price - l3.price
        if wave1 <= 0 or wave3 <= 0:
            return None
        structure_ok = l3.price < l1.price and h2.price < h0.price and h4.price < h2.price
        if not structure_ok:
            return None
        if not (prev_close >= l3.price and close < l3.price - buffer):
            return None
        retrace = (h4.price - l3.price) / wave3
        wall_ratio, wall_level, wall_dist = nearest_wall(h4.price, h2.price, l3.price, "short", h4.atr)
        channel_level, slope = channel_projection(h0, h2, h4.pivot_i)
        channel_dist = abs(h4.price - channel_level) / max(h4.atr, 1e-9)
        slope_atr = slope / max(h4.atr, 1e-9)
        time_ratio = (h4.pivot_i - l3.pivot_i) / max(l3.pivot_i - h2.pivot_i, 1)
        wave3_vs_wave1 = wave3 / wave1
        a_break = l3.price < l1.price
        score, grade, risk_weight, reasons = score_candidate(
            "short", a_break, retrace, wall_dist, channel_dist, slope_atr, time_ratio, body_ratio, wave3_vs_wave1
        )
        if grade == "skip":
            return None
        stop = h4.price + atr_i * 0.20
        if close >= stop:
            return None
        return {
            "direction": "short",
            "grade": grade,
            "risk_weight": risk_weight,
            "score": score,
            "reasons": ",".join(reasons),
            "trigger_level": l3.price,
            "stop": stop,
            "wall_ratio": wall_ratio,
            "wall_level": wall_level,
            "wall_dist_atr": wall_dist,
            "channel_level": channel_level,
            "channel_dist_atr": channel_dist,
            "slope_atr_per_bar": slope_atr,
            "retrace": retrace,
            "time_ratio": time_ratio,
            "wave3_vs_wave1": wave3_vs_wave1,
            "signal_body_ratio": body_ratio,
            "pivots": f"{h0.pivot_i}-{l1.pivot_i}-{h2.pivot_i}-{l3.pivot_i}-{h4.pivot_i}",
        }

    return None


def direction_cost_r(symbol: str, direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    costs = COST_TABLE[symbol]
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - costs["slip_price"]) - (entry + costs["spread_price"] / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - costs["spread_price"] / 2.0) - (exit_price + costs["slip_price"])
    return clean / risk, after / risk


def simulate_trade(df: pd.DataFrame, symbol: str, sig: dict, signal_i: int) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None

    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    if direction == "long":
        risk = entry - stop
        target = entry + risk * RR
        if risk <= 0:
            return None
    else:
        risk = stop - entry
        target = entry - risk * RR
        if risk <= 0:
            return None

    exit_i = min(len(df) - 1, entry_i + MAX_HOLD_BARS)
    exit_price = float(df["close"].iloc[exit_i])
    reason = "time_exit"

    for j in range(entry_i, min(len(df), entry_i + MAX_HOLD_BARS + 1)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = hi >= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                break

    r_clean, r_after = direction_cost_r(symbol, direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after,
        "weighted_r_after_cost": r_after * float(sig["risk_weight"]),
    }


def run_symbol(symbol: str) -> pd.DataFrame:
    raw = load_instrument(symbol)
    df = add_indicators(resample_ohlc(raw, TIMEFRAME))
    pivots = build_confirmed_pivots(df, width=3, min_swing_atr=1.5)
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < START or ts > END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue
        sig = synapse_signal(df, i, active)
        if sig is None:
            continue
        trade = simulate_trade(df, symbol, sig, i)
        if trade is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "signal_time": ts,
                **sig,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def max_drawdown(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return 0.0
    curve = np.cumsum(arr)
    return float((np.maximum.accumulate(curve) - curve).max())


def max_losing_streak(values: Iterable[float]) -> int:
    cur = 0
    best = 0
    for value in values:
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


def summarize(trades: pd.DataFrame, group_cols: list[str], r_col: str = "r_after_cost") -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = group[r_col]
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
                "avg_hold_bars": float(group["bars_held"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
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


def diagnostic_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    specs = [
        ("score", pd.cut(trades["score"], [5.5, 6, 7, 8, 9, 10, 20], include_lowest=True)),
        ("retrace", pd.cut(trades["retrace"], [0.49, 0.55, 0.618, 0.70, 0.80, 0.886], include_lowest=True)),
        ("wall_dist_atr", pd.cut(trades["wall_dist_atr"], [0, 0.15, 0.35, 0.60, 99], include_lowest=True)),
        ("channel_dist_atr", pd.cut(trades["channel_dist_atr"], [0, 0.25, 0.50, 0.85, 1.50, 99], include_lowest=True)),
        ("time_ratio", pd.cut(trades["time_ratio"], [0, 0.45, 0.80, 1.20, 1.80, 99], include_lowest=True)),
        ("signal_body_ratio", pd.cut(trades["signal_body_ratio"], [0, 0.25, 0.45, 0.65, 1.0], include_lowest=True)),
    ]
    for feature, bins in specs:
        tmp = trades.copy()
        tmp["bin"] = bins.astype(str)
        for key, group in tmp.groupby("bin", dropna=False):
            r = group["r_after_cost"]
            rows.append(
                {
                    "feature": feature,
                    "bin": str(key),
                    "trades": int(len(group)),
                    "win_rate": float((r > 0).mean() * 100),
                    "total_r": float(r.sum()),
                    "avg_r": float(r.mean()),
                    "pf": profit_factor(r),
                }
            )
    return pd.DataFrame(rows)


def write_report(
    trades: pd.DataFrame,
    overall: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_grade: pd.DataFrame,
    oos: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> None:
    lines = [
        "# Synapse_v0 機械検証",
        "",
        "## 目的",
        "",
        "Tobi/Synapse系の裁量説明を、まず検証できる最小ルールへ落とした初期版です。",
        "完全再現ではなく、以下の要素だけを機械化しています。",
        "",
        "- Aブレイク: 3波側の高値/安値が1波側を更新している",
        "- Bブレイク: 4波調整後、3波高値/安値を終値で再ブレイク",
        "- 半値/61.8/73.6/76.4付近の壁反応",
        "- 斜めの帰り: 1波/3波側の角度を平行移動したチャネルへの回帰",
        "- 時間軸: 推進波と調整波の横軸バランス",
        "- 通常ロット/半ロット/見送り: 点数で分類",
        "",
        "## 重要な注意",
        "",
        "- これは裁量の完全コピーではありません。",
        "- 半値は `0.50` として扱っています。",
        "- エントリーはシグナル足の次足始値、SLは4波の外側、TPは固定3Rです。",
        "- 12月15日から1月10日は除外しています。",
        "- コストは既存研究と同じスプレッド+スリッページ近似です。",
        "",
        "## 全体成績",
        "",
        markdown_table(overall, 20),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 80),
        "",
        "## ロット判定別",
        "",
        markdown_table(by_grade, 20),
        "",
        "## 2025-2026 OOS",
        "",
        markdown_table(oos, 40),
        "",
        "## 条件診断",
        "",
        markdown_table(diagnostics.sort_values(["feature", "total_r"], ascending=[True, False]), 80),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_grade.csv`",
        "- `summary_oos.csv`",
        "- `diagnostics.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_rows = []
    coverage_rows = []
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        trades = run_symbol(symbol)
        if not trades.empty:
            all_rows.append(trades)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)
    if not all_rows:
        (OUT_DIR / "report_ja.md").write_text("# Synapse_v0\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades_df = pd.concat(all_rows, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades_df[col] = pd.to_datetime(trades_df[col])
    trades_df["year"] = trades_df["entry_time"].dt.year.astype(str)
    trades_df["sample"] = np.where(trades_df["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2015_2024")
    trades_df = trades_df.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades_df, ["timeframe"])
    overall_weighted = summarize(trades_df, ["timeframe"], "weighted_r_after_cost")
    overall_weighted.insert(1, "risk_model", "normal=1R half=0.5R")
    overall.insert(1, "risk_model", "all=1R")
    overall = pd.concat([overall, overall_weighted], ignore_index=True)

    by_symbol = summarize(trades_df, ["symbol", "timeframe"])
    by_grade = summarize(trades_df, ["grade", "timeframe"])
    oos = summarize(trades_df, ["sample", "symbol", "timeframe"])
    diagnostics = diagnostic_summary(trades_df)

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_grade.to_csv(OUT_DIR / "summary_by_grade.csv", index=False)
    oos.to_csv(OUT_DIR / "summary_oos.csv", index=False)
    diagnostics.to_csv(OUT_DIR / "diagnostics.csv", index=False)
    write_report(trades_df, overall, by_symbol, by_grade, oos, diagnostics)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(overall.to_string(index=False))
    print("\nBy symbol")
    print(by_symbol.to_string(index=False))


if __name__ == "__main__":
    main()

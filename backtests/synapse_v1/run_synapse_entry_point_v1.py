#!/usr/bin/env python3
"""
Synapse entry-point v1.

This is a mechanical first pass for the transcript that describes:

- H1 as the main trading timeframe.
- Take the turn from wave 2 into wave 3.
- Confirm the turn with one diagonal line and two horizontal lines.
- Use half-value targets rather than full N targets.

It is intentionally conservative about look-ahead:

- Swing pivots are only usable after the right-side confirmation bars exist.
- Entry is placed at the next H1 open after a signal bar.
- If SL and TP are touched in the same bar, SL wins.
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
TIMEFRAME = "H1"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-12-31 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")
ATR_PERIOD = 14
PIVOT_WIDTH = 3
MIN_SWING_ATR = 1.2
MAX_HOLD_BARS = 96
BREAK_BUFFER_ATR = 0.05
STOP_BUFFER_ATR = 0.20
MIN_REWARD_R = 0.80

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}


@dataclass(frozen=True)
class Pivot:
    pivot_i: int
    confirm_i: int
    kind: str
    price: float
    atr: float


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"], ATR_PERIOD)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_ratio"] = ((out["close"] - out["open"]).abs() / rng).fillna(0.0)
    out["ema100"] = out["close"].ewm(span=100, adjust=False).mean()
    out["ema100_slope"] = out["ema100"] - out["ema100"].shift(24)
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


def line_value(p0: Pivot, p1: Pivot, at_i: int) -> tuple[float, float]:
    bars = max(p1.pivot_i - p0.pivot_i, 1)
    slope = (p1.price - p0.price) / bars
    return p1.price + slope * (at_i - p1.pivot_i), slope


def direction_cost_r(symbol: str, direction: str, entry: float, exit_price: float, risk: float) -> tuple[float, float]:
    costs = COST_TABLE[symbol]
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - costs["slip_price"]) - (entry + costs["spread_price"] / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - costs["spread_price"] / 2.0) - (exit_price + costs["slip_price"])
    return clean / risk, after / risk


def signal_from_pivots(df: pd.DataFrame, i: int, active: list[Pivot], entry_mode: str) -> dict | None:
    if len(active) < 6:
        return None

    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None

    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    body = float(df["body_ratio"].iloc[i])
    buffer = atr_i * BREAK_BUFFER_ATR
    ema_slope = float(df["ema100_slope"].iloc[i])

    p = active[-6:]
    kinds = "".join(x.kind for x in p)

    if kinds == "LHLHLH":
        l0, h1, l2, h3, l4, h5 = p
        wave1 = h1.price - l0.price
        if wave1 <= atr_i * 1.5:
            return None

        # 2波の斜め: 調整中の高値を結んだ下降トレンドライン。
        tl_now, tl_slope = line_value(h1, h3, i)
        line_break = close > tl_now + buffer and prev_close <= tl_now + atr_i * 0.20

        # A/B: Aは調整内部の戻り高値、Bは安値後の戻り高値。
        a_level = h3.price
        b_level = h5.price
        a_break = close > a_level + buffer
        b_break = close > b_level + buffer and prev_close <= b_level + buffer

        # 2波は半値以上戻しているほど「押し目として妥当」と見る。
        retrace = (h1.price - l4.price) / wave1
        right_shoulder_ok = l4.price >= l2.price - atr_i * 0.75
        half_target = l4.price + wave1 * 0.50

        if entry_mode == "B_confirmed":
            trigger_ok = b_break
            trigger = b_level
        else:
            trigger_ok = line_break and a_break
            trigger = max(a_level, tl_now)

        if not trigger_ok:
            return None

        stop = l4.price - atr_i * STOP_BUFFER_ATR
        if close <= stop or half_target <= close:
            return None

        score = 0.0
        reasons: list[str] = []
        if line_break:
            score += 2
            reasons.append("斜め抜け")
        if a_break:
            score += 2
            reasons.append("A抜け")
        if b_break:
            score += 2
            reasons.append("B抜け")
        if 0.50 <= retrace <= 0.886:
            score += 2
            reasons.append("半値以上の押し")
        elif 0.382 <= retrace < 0.50:
            score += 0.5
            reasons.append("浅い押し")
        else:
            score -= 2
            reasons.append("押し過不足")
        if right_shoulder_ok:
            score += 1
            reasons.append("右肩維持")
        if body >= 0.45:
            score += 1
            reasons.append("実体ブレイク")
        if ema_slope > 0:
            score += 0.5
            reasons.append("EMA100上向き")
        if h3.price < h1.price:
            score += 1
            reasons.append("調整高値切下げ")

        grade = "normal" if score >= 7 else "half" if score >= 5 else "skip"
        risk_weight = 1.0 if grade == "normal" else 0.5 if grade == "half" else 0.0
        if grade == "skip":
            return None

        return {
            "direction": "long",
            "entry_mode": entry_mode,
            "grade": grade,
            "risk_weight": risk_weight,
            "score": score,
            "reasons": ",".join(reasons),
            "trigger_level": trigger,
            "a_level": a_level,
            "b_level": b_level,
            "trendline": tl_now,
            "trendline_slope_atr": tl_slope / atr_i,
            "retrace": retrace,
            "stop": stop,
            "target_half": half_target,
            "signal_body_ratio": body,
            "pivots": f"{l0.pivot_i}-{h1.pivot_i}-{l2.pivot_i}-{h3.pivot_i}-{l4.pivot_i}-{h5.pivot_i}",
        }

    if kinds == "HLHLHL":
        h0, l1, h2, l3, h4, l5 = p
        wave1 = h0.price - l1.price
        if wave1 <= atr_i * 1.5:
            return None

        tl_now, tl_slope = line_value(l1, l3, i)
        line_break = close < tl_now - buffer and prev_close >= tl_now - atr_i * 0.20

        a_level = l3.price
        b_level = l5.price
        a_break = close < a_level - buffer
        b_break = close < b_level - buffer and prev_close >= b_level - buffer

        retrace = (h4.price - l1.price) / wave1
        right_shoulder_ok = h4.price <= h2.price + atr_i * 0.75
        half_target = h4.price - wave1 * 0.50

        if entry_mode == "B_confirmed":
            trigger_ok = b_break
            trigger = b_level
        else:
            trigger_ok = line_break and a_break
            trigger = min(a_level, tl_now)

        if not trigger_ok:
            return None

        stop = h4.price + atr_i * STOP_BUFFER_ATR
        if close >= stop or half_target >= close:
            return None

        score = 0.0
        reasons: list[str] = []
        if line_break:
            score += 2
            reasons.append("斜め抜け")
        if a_break:
            score += 2
            reasons.append("A抜け")
        if b_break:
            score += 2
            reasons.append("B抜け")
        if 0.50 <= retrace <= 0.886:
            score += 2
            reasons.append("半値以上の戻し")
        elif 0.382 <= retrace < 0.50:
            score += 0.5
            reasons.append("浅い戻し")
        else:
            score -= 2
            reasons.append("戻し過不足")
        if right_shoulder_ok:
            score += 1
            reasons.append("右肩維持")
        if body >= 0.45:
            score += 1
            reasons.append("実体ブレイク")
        if ema_slope < 0:
            score += 0.5
            reasons.append("EMA100下向き")
        if l3.price > l1.price:
            score += 1
            reasons.append("調整安値切上げ")

        grade = "normal" if score >= 7 else "half" if score >= 5 else "skip"
        risk_weight = 1.0 if grade == "normal" else 0.5 if grade == "half" else 0.0
        if grade == "skip":
            return None

        return {
            "direction": "short",
            "entry_mode": entry_mode,
            "grade": grade,
            "risk_weight": risk_weight,
            "score": score,
            "reasons": ",".join(reasons),
            "trigger_level": trigger,
            "a_level": a_level,
            "b_level": b_level,
            "trendline": tl_now,
            "trendline_slope_atr": tl_slope / atr_i,
            "retrace": retrace,
            "stop": stop,
            "target_half": half_target,
            "signal_body_ratio": body,
            "pivots": f"{h0.pivot_i}-{l1.pivot_i}-{h2.pivot_i}-{l3.pivot_i}-{h4.pivot_i}-{l5.pivot_i}",
        }

    return None


def simulate_trade(df: pd.DataFrame, symbol: str, sig: dict, signal_i: int) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None

    direction = sig["direction"]
    entry = float(df["open"].iloc[entry_i])
    stop = float(sig["stop"])
    target = float(sig["target_half"])
    if direction == "long":
        risk = entry - stop
        reward = target - entry
        if risk <= 0 or reward <= 0 or reward / risk < MIN_REWARD_R:
            return None
    else:
        risk = stop - entry
        reward = entry - target
        if risk <= 0 or reward <= 0 or reward / risk < MIN_REWARD_R:
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
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break
        else:
            hit_sl = hi >= stop
            hit_tp = lo <= target
            if hit_sl or hit_tp:
                exit_i = j
                exit_price = stop if hit_sl else target
                reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP_half"
                break

    r_clean, r_after = direction_cost_r(symbol, direction, entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "planned_rr": reward / risk,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after,
        "weighted_r_after_cost": r_after * float(sig["risk_weight"]),
    }


def run_symbol(symbol: str, entry_mode: str) -> pd.DataFrame:
    raw = load_instrument(symbol)
    df = add_indicators(raw)
    pivots = build_confirmed_pivots(df, PIVOT_WIDTH, MIN_SWING_ATR)
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
        sig = signal_from_pivots(df, i, active, entry_mode)
        if sig is None:
            continue
        trade = simulate_trade(df, symbol, sig, i)
        if trade is None:
            continue
        rows.append({"symbol": symbol, "timeframe": TIMEFRAME, "signal_time": ts, **sig, **trade})
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
                "avg_planned_rr": float(group["planned_rr"].mean()),
                "avg_hold_bars": float(group["bars_held"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r", "win_rate"], ascending=[False, False])


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
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


def diagnostics(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    specs = [
        ("retrace", pd.cut(trades["retrace"], [0, 0.382, 0.50, 0.618, 0.764, 0.886, 2], include_lowest=True)),
        ("score", pd.cut(trades["score"], [0, 5, 6, 7, 8, 10], include_lowest=True)),
        ("planned_rr", pd.cut(trades["planned_rr"], [0, 1, 1.5, 2, 3, 99], include_lowest=True)),
        (
            "trendline_slope_atr",
            pd.cut(trades["trendline_slope_atr"].abs(), [0, 0.05, 0.12, 0.25, 99], include_lowest=True),
        ),
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
    by_mode: pd.DataFrame,
    by_grade: pd.DataFrame,
    oos: pd.DataFrame,
    diag: pd.DataFrame,
) -> None:
    lines = [
        "# Synapse Entry Point v1 機械検証",
        "",
        "## 検証定義",
        "",
        "- H1ピボットで 1波→2波→3波候補を検出",
        "- ロングは `L-H-L-H-L-H`、ショートは `H-L-H-L-H-L` を基礎形にする",
        "- 斜め1本: 2波中の調整トレンドライン",
        "- 水平線A: 調整内の戻り高値/押し安値",
        "- 水平線B: 右肩後の戻り高値/押し安値",
        "- `B_confirmed`: B抜けで次足エントリー",
        "- `A_early`: 斜め抜け + A抜けで次足エントリー",
        "- TP: N値ではなく、1波値幅の半値目標",
        "- SL: 右肩の外側 + 0.2ATR",
        "- 最低予定RRは0.8R、12月15日から1月10日は除外",
        "",
        "## 注意",
        "",
        "これはTobi/Synapse裁量の完全再現ではなく、文字起こしから作った検証可能なv1です。",
        "とくに、上位足環境、値幅干渉、斜め半値、チャネル乖離の裁量評価はまだ簡略化しています。",
        "",
        "## 全体",
        "",
        markdown_table(overall, 20),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 80),
        "",
        "## エントリーモード別",
        "",
        markdown_table(by_mode, 20),
        "",
        "## ロット判定別",
        "",
        markdown_table(by_grade, 20),
        "",
        "## OOS 2025-2026",
        "",
        markdown_table(oos, 60),
        "",
        "## 条件診断",
        "",
        markdown_table(diag.sort_values(["feature", "total_r"], ascending=[True, False]), 100),
        "",
        "## 出力ファイル",
        "",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_mode.csv`",
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
        for entry_mode in ["B_confirmed", "A_early"]:
            rows = run_symbol(symbol, entry_mode)
            if not rows.empty:
                all_rows.append(rows)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)
    if not all_rows:
        (OUT_DIR / "report_ja.md").write_text("# Synapse Entry Point v1\n\nNo trades.", encoding="utf-8")
        print("No trades.")
        return

    trades = pd.concat(all_rows, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col])
    trades["sample"] = np.where(trades["entry_time"] >= OOS_START, "OOS_2025_2026", "IS_2015_2024")
    trades = trades.sort_values(["entry_time", "symbol", "entry_mode"]).reset_index(drop=True)
    trades.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades, ["timeframe"])
    weighted = summarize(trades, ["timeframe"], "weighted_r_after_cost")
    overall.insert(1, "risk_model", "all=1R")
    weighted.insert(1, "risk_model", "normal=1R half=0.5R")
    overall = pd.concat([overall, weighted], ignore_index=True)
    by_symbol = summarize(trades, ["symbol", "timeframe"])
    by_mode = summarize(trades, ["entry_mode", "timeframe"])
    by_grade = summarize(trades, ["grade", "timeframe"])
    oos = summarize(trades, ["sample", "symbol", "timeframe"])
    diag = diagnostics(trades)

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_mode.to_csv(OUT_DIR / "summary_by_mode.csv", index=False)
    by_grade.to_csv(OUT_DIR / "summary_by_grade.csv", index=False)
    oos.to_csv(OUT_DIR / "summary_oos.csv", index=False)
    diag.to_csv(OUT_DIR / "diagnostics.csv", index=False)
    write_report(trades, overall, by_symbol, by_mode, by_grade, oos, diag)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(overall.to_string(index=False))
    print("\nBy symbol")
    print(by_symbol.to_string(index=False))
    print("\nBy mode")
    print(by_mode.to_string(index=False))


if __name__ == "__main__":
    main()

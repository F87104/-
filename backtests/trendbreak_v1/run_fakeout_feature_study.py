#!/usr/bin/env python3
"""
TrendBreakV1 fakeout feature study.

Goal:
- Inspect the current high/low breakout entries in detail.
- Quantify patterns that tend to become fakeouts/losses.
- Test practical skip/confirmation filters against the 2015-2024 H1 data.

This is a research backtest, not a broker emulator clone.
"""

from __future__ import annotations

import copy
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "fakeout_feature_study_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))

from sai_backtest import atr, load_instrument, rolling_max, rolling_min  # noqa: E402
from trendbreak_backtest import (  # noqa: E402
    ATR_PERIOD,
    EXCLUDE_LONG,
    LOOKBACK_LONG,
    PRESETS_CONSERVATIVE,
    compute_signals,
)


SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
YEAR_FROM = 2015
YEAR_TO = 2024
RISK_PCT = 1.0
MAX_DD_PCT = 20.0

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}


def hybrid_cfg(symbol: str) -> dict:
    """Mirror the currently used TrendBreakV1 HYBRID preset."""
    cfg = copy.deepcopy(PRESETS_CONSERVATIVE[symbol])
    if symbol in {"USDJPY", "GBPJPY", "SILVER"}:
        cfg["level_kind"] = "any"
        cfg["session"] = False
    elif symbol == "CHFJPY":
        cfg["level_kind"] = "any"
    elif symbol == "XAUUSD":
        cfg["session"] = False
    return cfg


def max_drawdown_r(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    curve = np.cumsum(values)
    return float((np.maximum.accumulate(curve) - curve).max())


def profit_factor(values: np.ndarray) -> float:
    gp = values[values > 0].sum()
    gl = values[values <= 0].sum()
    if gl < 0:
        return float(gp / abs(gl))
    return math.inf if gp > 0 else math.nan


def summarize_trades(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": 0.0,
            "pf_after_cost": math.nan,
            "max_dd_after_cost_r": 0.0,
            "quick_back_inside_3_rate": 0.0,
        }
    r = df["pnl_r_after_cost"].to_numpy()
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r_after_cost": float(r.sum()),
        "avg_r_after_cost": float(r.mean()),
        "pf_after_cost": profit_factor(r),
        "max_dd_after_cost_r": max_drawdown_r(r),
        "quick_back_inside_3_rate": float(df["quick_back_inside_3"].mean() * 100),
    }


def prepare_context(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    sig = compute_signals(df, cfg)
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]
    a = atr(h, l, c, ATR_PERIOD)

    lb3 = cfg["lookback_3m"]
    ex3 = cfg["exclude"]
    high_3m = rolling_max(h.shift(1), lb3)
    low_3m = rolling_min(l.shift(1), lb3)
    high_long = rolling_max(h.shift(1), LOOKBACK_LONG)
    low_long = rolling_min(l.shift(1), LOOKBACK_LONG)

    recent_high_3m = rolling_max(h.shift(1), max(ex3, 1))
    recent_low_3m = rolling_min(l.shift(1), max(ex3, 1))
    recent_high_long = rolling_max(h.shift(1), EXCLUDE_LONG)
    recent_low_long = rolling_min(l.shift(1), EXCLUDE_LONG)

    no_touch_high_3m = recent_high_3m < high_3m
    no_touch_low_3m = recent_low_3m > low_3m
    no_touch_high_long = recent_high_long < high_long
    no_touch_low_long = recent_low_long > low_long

    raw_long_3m = (c > high_3m) & no_touch_high_3m
    raw_short_3m = (c < low_3m) & no_touch_low_3m
    raw_long_long = (c > high_long) & no_touch_high_long
    raw_short_long = (c < low_long) & no_touch_low_long

    warmup = max(lb3, ex3) + 5
    warm_ok = pd.Series(np.arange(len(df)) >= warmup, index=df.index)
    raw_long_3m = raw_long_3m & warm_ok
    raw_short_3m = raw_short_3m & warm_ok

    atr_avg = a.rolling(100).mean()
    high_vol = (a > atr_avg * 2.0).fillna(False)

    out = sig.copy()
    out["atr"] = a
    out["atr_avg"] = atr_avg
    out["high_vol"] = high_vol
    out["high_3m"] = high_3m
    out["low_3m"] = low_3m
    out["high_long"] = high_long
    out["low_long"] = low_long
    out["recent_high_3m"] = recent_high_3m
    out["recent_low_3m"] = recent_low_3m
    out["raw_long_3m"] = raw_long_3m.fillna(False)
    out["raw_short_3m"] = raw_short_3m.fillna(False)
    out["raw_long_long"] = raw_long_long.fillna(False)
    out["raw_short_long"] = raw_short_long.fillna(False)
    return out


def choose_signal(ctx: pd.DataFrame, i: int, cfg: dict) -> tuple[str | None, float, str]:
    row = ctx.iloc[i]
    if not bool(row["long_sig"]) and not bool(row["short_sig"]):
        return None, math.nan, ""

    direction = "long" if bool(row["long_sig"]) else "short"
    level_kind = "3m"
    level = math.nan

    if direction == "long":
        if cfg["level_kind"] == "long":
            level_kind = "long"
            level = row["high_long"]
        elif cfg["level_kind"] == "any":
            if bool(row["raw_long_3m"]):
                level_kind = "3m"
                level = row["high_3m"]
            else:
                level_kind = "long"
                level = row["high_long"]
        else:
            level_kind = "3m"
            level = row["high_3m"]
    else:
        if cfg["level_kind"] == "long":
            level_kind = "long"
            level = row["low_long"]
        elif cfg["level_kind"] == "any":
            if bool(row["raw_short_3m"]):
                level_kind = "3m"
                level = row["low_3m"]
            else:
                level_kind = "long"
                level = row["low_long"]
        else:
            level_kind = "3m"
            level = row["low_3m"]

    if pd.isna(level):
        return None, math.nan, ""
    return direction, float(level), level_kind


def safe_div(a: float, b: float) -> float:
    if b == 0 or pd.isna(a) or pd.isna(b):
        return math.nan
    return float(a / b)


def signal_features(ctx: pd.DataFrame, i: int, direction: str, level: float, level_kind: str) -> dict:
    row = ctx.iloc[i]
    sign = 1.0 if direction == "long" else -1.0
    o = float(row["open"])
    h = float(row["high"])
    l = float(row["low"])
    c = float(row["close"])
    a = float(row["atr"])
    bar_range = max(h - l, 0.0)
    body = abs(c - o)

    close_strength = safe_div(c - l, bar_range) if direction == "long" else safe_div(h - c, bar_range)
    adverse_wick = safe_div(h - c, bar_range) if direction == "long" else safe_div(c - l, bar_range)
    favorable_wick = safe_div(c - l, bar_range) if direction == "long" else safe_div(h - c, bar_range)
    break_atr = safe_div(sign * (c - level), a)

    features: dict[str, float | int | bool | str] = {
        "signal_time": ctx.index[i],
        "direction": direction,
        "level_kind": level_kind,
        "break_level": level,
        "signal_close": c,
        "atr": a,
        "break_atr": break_atr,
        "signal_range_atr": safe_div(bar_range, a),
        "signal_body_atr": safe_div(body, a),
        "body_ratio": safe_div(body, bar_range),
        "close_strength": close_strength,
        "adverse_wick_ratio": adverse_wick,
        "favorable_wick_ratio": favorable_wick,
        "atr_to_avg": safe_div(a, float(row["atr_avg"])),
    }

    for n in (3, 6, 12, 24):
        start = max(0, i - n)
        prior = ctx.iloc[start:i]
        if len(prior) == 0:
            features[f"pre_range_{n}_atr"] = math.nan
            features[f"pre_extension_{n}_atr"] = math.nan
            features[f"same_body_{n}_ratio"] = math.nan
            continue
        pre_high = float(prior["high"].max())
        pre_low = float(prior["low"].min())
        prior_close = float(ctx["close"].iloc[start])
        features[f"pre_range_{n}_atr"] = safe_div(pre_high - pre_low, a)
        features[f"pre_extension_{n}_atr"] = safe_div(sign * (c - prior_close), a)
        if direction == "long":
            features[f"same_body_{n}_ratio"] = float((prior["close"] > prior["open"]).mean())
        else:
            features[f"same_body_{n}_ratio"] = float((prior["close"] < prior["open"]).mean())

    for n in (1, 2, 3, 6):
        fut = ctx.iloc[i + 1 : min(len(ctx), i + 1 + n)]
        if len(fut) == 0:
            features[f"back_inside_close_{n}"] = False
            features[f"follow_through_close_{n}"] = False
            features[f"mae_{n}_atr"] = math.nan
            features[f"mfe_{n}_atr"] = math.nan
            continue
        if direction == "long":
            back_inside = bool((fut["close"] <= level).any())
            follow = bool(fut["close"].iloc[-1] > c)
            mae = safe_div(c - float(fut["low"].min()), a)
            mfe = safe_div(float(fut["high"].max()) - c, a)
        else:
            back_inside = bool((fut["close"] >= level).any())
            follow = bool(fut["close"].iloc[-1] < c)
            mae = safe_div(float(fut["high"].max()) - c, a)
            mfe = safe_div(c - float(fut["low"].min()), a)
        features[f"back_inside_close_{n}"] = back_inside
        features[f"follow_through_close_{n}"] = follow
        features[f"mae_{n}_atr"] = mae
        features[f"mfe_{n}_atr"] = mfe

    features["quick_back_inside_3"] = bool(features["back_inside_close_3"])
    return features


@dataclass
class SimTrade:
    symbol: str
    filter_name: str
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    level_kind: str
    break_level: float
    signal_close: float
    entry: float
    sl: float
    tp: float
    exit_price: float
    pnl_r_clean: float
    pnl_r_after_cost: float
    bars_held: int
    exit_reason: str
    features: dict


FilterFunc = Callable[[dict], bool]


def simulate_filtered(
    symbol: str,
    ctx: pd.DataFrame,
    cfg: dict,
    filter_name: str,
    filter_func: FilterFunc | None = None,
    confirm_bars: int = 0,
    confirm_follow: bool = False,
) -> list[SimTrade]:
    o = ctx["open"].to_numpy()
    h = ctx["high"].to_numpy()
    l = ctx["low"].to_numpy()
    c = ctx["close"].to_numpy()
    a = ctx["atr"].to_numpy()
    idx = ctx.index
    costs = COST_TABLE[symbol]
    trades: list[SimTrade] = []

    in_pos_until = -1
    cooldown_until = -1
    equity_pct = 100.0
    peak_equity_pct = 100.0

    for i in range(len(ctx) - 2):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        if bool(ctx["high_vol"].iloc[i]):
            continue
        if peak_equity_pct > 0 and (peak_equity_pct - equity_pct) / peak_equity_pct * 100 >= MAX_DD_PCT:
            continue

        direction, level, level_kind = choose_signal(ctx, i, cfg)
        if direction is None:
            continue
        features = signal_features(ctx, i, direction, level, level_kind)
        if filter_func is not None and not filter_func(features):
            continue

        confirm_i = i + confirm_bars
        entry_bar = confirm_i + 1
        if entry_bar >= len(ctx):
            break

        if confirm_bars > 0:
            future = ctx.iloc[i + 1 : confirm_i + 1]
            if len(future) < confirm_bars:
                continue
            if direction == "long":
                outside = bool((future["close"] > level).all())
                follow = bool(future["close"].iloc[-1] > features["signal_close"])
            else:
                outside = bool((future["close"] < level).all())
                follow = bool(future["close"].iloc[-1] < features["signal_close"])
            if not outside:
                continue
            if confirm_follow and not follow:
                continue

        sig_atr = a[confirm_i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue

        entry = float(o[entry_bar])
        sl_dist = float(sig_atr * cfg["sl_atr"])
        if sl_dist <= 0:
            continue
        if direction == "long":
            sl = entry - sl_dist
            tp = entry + sl_dist * cfg["tp_rr"]
        else:
            sl = entry + sl_dist
            tp = entry - sl_dist * cfg["tp_rr"]

        for j in range(entry_bar, len(ctx)):
            if direction == "long":
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
                if not (hit_sl or hit_tp):
                    continue
                exit_reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                exit_price = sl if hit_sl else tp
                pnl_clean = exit_price - entry
                pnl_after = (exit_price - costs["slip_price"]) - (entry + costs["spread_price"] / 2.0)
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp
                if not (hit_sl or hit_tp):
                    continue
                exit_reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                exit_price = sl if hit_sl else tp
                pnl_clean = entry - exit_price
                pnl_after = (entry - costs["spread_price"] / 2.0) - (exit_price + costs["slip_price"])

            pnl_r_clean = pnl_clean / sl_dist
            pnl_r_after = pnl_after / sl_dist
            equity_pct += pnl_r_after * RISK_PCT
            peak_equity_pct = max(peak_equity_pct, equity_pct)
            trades.append(
                SimTrade(
                    symbol=symbol,
                    filter_name=filter_name,
                    signal_time=idx[i],
                    entry_time=idx[entry_bar],
                    exit_time=idx[j],
                    direction=direction,
                    level_kind=level_kind,
                    break_level=level,
                    signal_close=float(c[i]),
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    exit_price=float(exit_price),
                    pnl_r_clean=float(pnl_r_clean),
                    pnl_r_after_cost=float(pnl_r_after),
                    bars_held=j - entry_bar,
                    exit_reason=exit_reason,
                    features=features,
                )
            )
            in_pos_until = j
            cooldown_until = j + int(cfg.get("cooldown", 0))
            break
    return trades


def flatten_trades(trades: list[SimTrade]) -> pd.DataFrame:
    rows = []
    for t in trades:
        row = {
            "symbol": t.symbol,
            "filter_name": t.filter_name,
            "signal_time": t.signal_time,
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "direction": t.direction,
            "level_kind": t.level_kind,
            "break_level": t.break_level,
            "signal_close": t.signal_close,
            "entry": t.entry,
            "sl": t.sl,
            "tp": t.tp,
            "exit_price": t.exit_price,
            "pnl_r_clean": t.pnl_r_clean,
            "pnl_r_after_cost": t.pnl_r_after_cost,
            "bars_held": t.bars_held,
            "exit_reason": t.exit_reason,
        }
        row.update(t.features)
        rows.append(row)
    return pd.DataFrame(rows)


def filter_definitions() -> list[tuple[str, str, FilterFunc]]:
    defs: list[tuple[str, str, FilterFunc]] = []
    for th in [0.05, 0.10, 0.20, 0.30, 0.50]:
        defs.append((f"break_atr_ge_{th}", "ブレイク余白", lambda f, th=th: f["break_atr"] >= th))
    for th in [0.30, 0.40, 0.50, 0.60]:
        defs.append((f"body_ratio_ge_{th}", "実体の強さ", lambda f, th=th: f["body_ratio"] >= th))
    for th in [0.55, 0.65, 0.75, 0.85]:
        defs.append((f"close_strength_ge_{th}", "終値位置", lambda f, th=th: f["close_strength"] >= th))
    for th in [0.20, 0.30, 0.40, 0.50]:
        defs.append((f"adverse_wick_le_{th}", "逆ヒゲ回避", lambda f, th=th: f["adverse_wick_ratio"] <= th))
    for th in [1.00, 1.50, 2.00, 2.50, 3.00]:
        defs.append((f"pre_range6_le_{th}", "直前6本の停滞", lambda f, th=th: f["pre_range_6_atr"] <= th))
    for th in [1.50, 2.00, 2.50, 3.00, 4.00]:
        defs.append((f"pre_extension6_le_{th}", "伸びすぎ回避", lambda f, th=th: f["pre_extension_6_atr"] <= th))
    for th in [1.00, 1.50, 2.00, 2.50]:
        defs.append((f"signal_range_le_{th}", "大陽線/大陰線飛び乗り回避", lambda f, th=th: f["signal_range_atr"] <= th))
    for th in [0.50, 0.67, 0.80]:
        defs.append((f"same_body6_ge_{th}", "直前同方向ローソク", lambda f, th=th: f["same_body_6_ratio"] >= th))
    return defs


def combo_definitions() -> list[tuple[str, str, FilterFunc]]:
    return [
        (
            "strong_close_no_big_wick",
            "終値が強く、逆ヒゲが小さい",
            lambda f: f["close_strength"] >= 0.65 and f["adverse_wick_ratio"] <= 0.35,
        ),
        (
            "not_overextended",
            "直前6本で伸びすぎていない",
            lambda f: f["pre_extension_6_atr"] <= 2.5,
        ),
        (
            "stagnation_then_break",
            "直前6本が比較的停滞してから抜ける",
            lambda f: f["pre_range_6_atr"] <= 2.5 and f["break_atr"] >= 0.05,
        ),
        (
            "balanced_fakeout_guard",
            "終値強め＋逆ヒゲ小さめ＋伸びすぎ回避",
            lambda f: (
                f["close_strength"] >= 0.60
                and f["adverse_wick_ratio"] <= 0.40
                and f["pre_extension_6_atr"] <= 3.0
            ),
        ),
        (
            "strict_fakeout_guard",
            "厳しめ: 終値強い＋逆ヒゲ小＋停滞＋伸びすぎ回避",
            lambda f: (
                f["close_strength"] >= 0.65
                and f["adverse_wick_ratio"] <= 0.35
                and f["pre_range_6_atr"] <= 2.5
                and f["pre_extension_6_atr"] <= 2.5
            ),
        ),
    ]


def run_all(filter_name: str, filter_func: FilterFunc | None = None, confirm_bars: int = 0, confirm_follow: bool = False) -> pd.DataFrame:
    all_trades: list[SimTrade] = []
    for symbol in SYMBOLS:
        cfg = hybrid_cfg(symbol)
        df = load_instrument(symbol)
        df = df[(df.index.year >= YEAR_FROM) & (df.index.year <= YEAR_TO)]
        ctx = prepare_context(df, cfg)
        all_trades.extend(
            simulate_filtered(
                symbol,
                ctx,
                cfg,
                filter_name=filter_name,
                filter_func=filter_func,
                confirm_bars=confirm_bars,
                confirm_follow=confirm_follow,
            )
        )
    return flatten_trades(all_trades)


def summarize_by_symbol(df: pd.DataFrame, name: str, category: str) -> list[dict]:
    rows = []
    for symbol, g in df.groupby("symbol", dropna=False):
        row = summarize_trades(g)
        row.update({"filter_name": name, "category": category, "symbol": symbol})
        rows.append(row)
    row = summarize_trades(df)
    row.update({"filter_name": name, "category": category, "symbol": "ALL"})
    rows.append(row)
    return rows


def feature_buckets(baseline: pd.DataFrame) -> pd.DataFrame:
    features = [
        "break_atr",
        "body_ratio",
        "close_strength",
        "adverse_wick_ratio",
        "signal_range_atr",
        "pre_range_6_atr",
        "pre_extension_6_atr",
        "same_body_6_ratio",
        "atr_to_avg",
        "mae_3_atr",
        "mfe_3_atr",
    ]
    rows = []
    for feature in features:
        s = baseline[feature].replace([np.inf, -np.inf], np.nan).dropna()
        if s.nunique() < 4:
            continue
        try:
            buckets = pd.qcut(baseline[feature], q=4, duplicates="drop")
        except ValueError:
            continue
        for bucket, g in baseline.groupby(buckets, observed=False):
            row = summarize_trades(g)
            row.update({"feature": feature, "bucket": str(bucket)})
            rows.append(row)
    return pd.DataFrame(rows)


def write_report(
    baseline: pd.DataFrame,
    single: pd.DataFrame,
    combos: pd.DataFrame,
    confirms: pd.DataFrame,
    buckets: pd.DataFrame,
) -> None:
    base = summarize_trades(baseline)
    single_all = single[single["symbol"] == "ALL"].copy()
    combo_all = combos[combos["symbol"] == "ALL"].copy()
    confirm_all = confirms[confirms["symbol"] == "ALL"].copy()

    def sort_view(df: pd.DataFrame) -> pd.DataFrame:
        return df.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False]).head(10)

    lines = [
        "# TrendBreakV1 騙し特徴検証 2015-2024",
        "",
        "## 前提",
        "",
        "- データ: local `F87104_test` H1 OHLC",
        "- 対象: XAUUSD / USDJPY / EURJPY / GBPJPY / CHFJPY / AUDJPY / SILVER",
        "- 方式: HYBRID TrendBreakV1、シグナル足終値で判定、次足始値で約定",
        "- コスト: 既存監査と同じスプレッド + スリッページをRから控除",
        "- 高ボラ停止: ATR14 > ATR14の100本平均 x 2 は新規見送り",
        "- DD停止: 20%近似。今回の比較では大きな停止影響は出にくい想定",
        "",
        "## ベースライン",
        "",
        f"- Trades: {base['trades']}",
        f"- Total R after cost: {base['total_r_after_cost']:.2f}R",
        f"- Win rate: {base['win_rate']:.2f}%",
        f"- PF: {base['pf_after_cost']:.3f}",
        f"- Max DD: {base['max_dd_after_cost_r']:.2f}R",
        f"- 3本以内に終値がブレイク水準内へ戻った率: {base['quick_back_inside_3_rate']:.2f}%",
        "",
        "## 単独フィルタ Top 10（総利益順）",
        "",
        "| Filter | Category | Trades | WR | Total R | PF | Max DD | 3本以内戻り率 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in sort_view(single_all).iterrows():
        lines.append(
            f"| {row['filter_name']} | {row['category']} | {int(row['trades'])} | "
            f"{row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | "
            f"{row['pf_after_cost']:.3f} | {row['max_dd_after_cost_r']:.2f} | "
            f"{row['quick_back_inside_3_rate']:.2f}% |"
        )

    lines.extend([
        "",
        "## 複合フィルタ",
        "",
        "| Filter | Meaning | Trades | WR | Total R | PF | Max DD | 3本以内戻り率 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    meaning_by_name = {name: desc for name, desc, _ in combo_definitions()}
    for _, row in combo_all.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False]).iterrows():
        lines.append(
            f"| {row['filter_name']} | {meaning_by_name.get(row['filter_name'], '')} | "
            f"{int(row['trades'])} | {row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | "
            f"{row['pf_after_cost']:.3f} | {row['max_dd_after_cost_r']:.2f} | "
            f"{row['quick_back_inside_3_rate']:.2f}% |"
        )

    lines.extend([
        "",
        "## 確認型フィルタ（シグナル後に待つ）",
        "",
        "| Confirm | Trades | WR | Total R | PF | Max DD | 3本以内戻り率 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for _, row in confirm_all.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False]).iterrows():
        lines.append(
            f"| {row['filter_name']} | {int(row['trades'])} | {row['win_rate']:.2f}% | "
            f"{row['total_r_after_cost']:.2f} | {row['pf_after_cost']:.3f} | "
            f"{row['max_dd_after_cost_r']:.2f} | {row['quick_back_inside_3_rate']:.2f}% |"
        )

    lines.extend([
        "",
        "## 読み取り方",
        "",
        "- `break_atr`: ブレイク水準から終値がどれだけ抜けたか。小さすぎると浅い抜け。",
        "- `close_strength`: ロングなら足の上側で引けたか、ショートなら下側で引けたか。",
        "- `adverse_wick_ratio`: ロングなら上ヒゲ、ショートなら下ヒゲ。大きいほど押し戻されている。",
        "- `pre_extension_6_atr`: 直前6本でどれだけ同方向に伸びたか。大きすぎると飛び乗り感が強い。",
        "- `pre_range_6_atr`: 直前6本の値幅。小さいほど停滞後のブレイクに近い。",
        "- `quick_back_inside_3_rate`: シグナル後3本以内に終値が元の水準内へ戻った率。騙しの補助指標。",
        "",
        "## 出力ファイル",
        "",
        "- `baseline_trades_with_features.csv`",
        "- `single_filter_sweep.csv`",
        "- `combo_filter_results.csv`",
        "- `confirmation_filter_results.csv`",
        "- `feature_bucket_summary.csv`",
    ])

    if not buckets.empty:
        best_bucket = buckets.sort_values(["avg_r_after_cost", "trades"], ascending=[False, False]).head(8)
        lines.extend(["", "## 特徴量バケット参考（平均R上位）", "", "| Feature | Bucket | Trades | WR | Avg R | Total R |", "| --- | --- | ---: | ---: | ---: | ---: |"])
        for _, row in best_bucket.iterrows():
            lines.append(
                f"| {row['feature']} | {row['bucket']} | {int(row['trades'])} | "
                f"{row['win_rate']:.2f}% | {row['avg_r_after_cost']:.3f} | "
                f"{row['total_r_after_cost']:.2f} |"
            )

    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("Running baseline...")
    baseline = run_all("baseline")
    baseline.to_csv(OUT_DIR / "baseline_trades_with_features.csv", index=False)
    print(pd.Series(summarize_trades(baseline)).to_string())

    single_rows = []
    for name, category, func in filter_definitions():
        print(f"Single filter: {name}")
        df = run_all(name, func)
        single_rows.extend(summarize_by_symbol(df, name, category))
    single = pd.DataFrame(single_rows)
    single.to_csv(OUT_DIR / "single_filter_sweep.csv", index=False)

    combo_rows = []
    for name, category, func in combo_definitions():
        print(f"Combo filter: {name}")
        df = run_all(name, func)
        combo_rows.extend(summarize_by_symbol(df, name, category))
    combos = pd.DataFrame(combo_rows)
    combos.to_csv(OUT_DIR / "combo_filter_results.csv", index=False)

    confirm_specs = [
        ("confirm_1_close_outside", 1, False),
        ("confirm_1_close_outside_and_follow", 1, True),
        ("confirm_2_closes_outside", 2, False),
        ("confirm_2_closes_outside_and_follow", 2, True),
        ("confirm_3_closes_outside", 3, False),
    ]
    confirm_rows = []
    for name, bars, follow in confirm_specs:
        print(f"Confirmation: {name}")
        df = run_all(name, None, confirm_bars=bars, confirm_follow=follow)
        confirm_rows.extend(summarize_by_symbol(df, name, "確認型"))
    confirms = pd.DataFrame(confirm_rows)
    confirms.to_csv(OUT_DIR / "confirmation_filter_results.csv", index=False)

    buckets = feature_buckets(baseline)
    buckets.to_csv(OUT_DIR / "feature_bucket_summary.csv", index=False)
    write_report(baseline, single, combos, confirms, buckets)

    print("\nTop single filters (ALL):")
    print(
        single[single["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        .head(12)
        [["filter_name", "category", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print("\nCombo filters (ALL):")
    print(
        combos[combos["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        [["filter_name", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print("\nConfirmation filters (ALL):")
    print(
        confirms[confirms["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        [["filter_name", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

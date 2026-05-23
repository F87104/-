"""
TrendBreakV1 Strategy backtester
Pineスクリプト「Trend-Break Strategy (Python compatible)」をPythonで再現。
- 中期/長期の高値・安値レベルを計算
- 直近 exclude_recent 本以内に未接触 = noRecentTouch
- close でブレイク → 次バー始値で約定 (シグナル足のATRでSL/TP固定)
"""
from __future__ import annotations

import argparse
import glob
import os
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from sai_backtest import (
    atr, rolling_max, rolling_min, load_instrument, INSTRUMENTS, DATA_ROOT
)


# ============================================================
# Presets (Pine版と完全一致)
# ============================================================
PRESETS_CONSERVATIVE = {
    "XAUUSD": dict(lookback_3m=480, exclude=120, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "XAGUSD": dict(lookback_3m=360, exclude=180, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "GBPJPY": dict(lookback_3m=360, exclude=180, sl_atr=2.5, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "USDJPY": dict(lookback_3m=480, exclude=180, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "EURJPY": dict(lookback_3m=360, exclude=60,  sl_atr=2.5, tp_rr=3.0, level_kind="mid",
                   session=False, asia=True, eu=False, ny=True, margin=0.5, cooldown=0),
    "AUDJPY": dict(lookback_3m=480, exclude=120, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "CHFJPY": dict(lookback_3m=480, exclude=120, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "SILVER": dict(lookback_3m=360, exclude=180, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
}

PRESETS_RELAXED = {
    "XAUUSD": dict(lookback_3m=240, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "XAGUSD": dict(lookback_3m=360, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=24),
    "GBPJPY": dict(lookback_3m=180, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "USDJPY": dict(lookback_3m=180, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.3, cooldown=0),
    "EURJPY": dict(lookback_3m=180, exclude=30, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                   session=True, asia=True, eu=False, ny=True, margin=0.0, cooldown=24),
    "AUDJPY": dict(lookback_3m=480, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "CHFJPY": dict(lookback_3m=480, exclude=90, sl_atr=2.5, tp_rr=3.0, level_kind="any",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=0),
    "SILVER": dict(lookback_3m=360, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                   session=False, asia=True, eu=False, ny=True, margin=0.0, cooldown=24),
}

LOOKBACK_LONG = 5000
EXCLUDE_LONG = 760
ATR_PERIOD = 14


# ============================================================
# Signal calc
# ============================================================
def compute_signals(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    o = df["open"]; h = df["high"]; l = df["low"]; c = df["close"]
    a = atr(h, l, c, ATR_PERIOD)

    lb3 = cfg["lookback_3m"]
    ex3 = cfg["exclude"]

    high_3m = rolling_max(h.shift(1), lb3)
    low_3m  = rolling_min(l.shift(1), lb3)
    high_long = rolling_max(h.shift(1), LOOKBACK_LONG)
    low_long  = rolling_min(l.shift(1), LOOKBACK_LONG)

    recent_high_3m = rolling_max(h.shift(1), ex3)
    recent_low_3m  = rolling_min(l.shift(1), ex3)
    recent_high_long = rolling_max(h.shift(1), EXCLUDE_LONG)
    recent_low_long  = rolling_min(l.shift(1), EXCLUDE_LONG)

    no_touch_high_3m = recent_high_3m < high_3m
    no_touch_low_3m  = recent_low_3m  > low_3m
    no_touch_high_long = recent_high_long < high_long
    no_touch_low_long  = recent_low_long  > low_long

    long_3m  = (c > high_3m) & no_touch_high_3m
    short_3m = (c < low_3m)  & no_touch_low_3m
    long_long  = (c > high_long)  & no_touch_high_long
    short_long = (c < low_long)   & no_touch_low_long

    lk = cfg["level_kind"]
    if lk == "long":
        long_sig, short_sig = long_long, short_long
    elif lk == "any":
        long_sig = long_3m | long_long
        short_sig = short_3m | short_long
    elif lk == "confluence":
        long_sig = long_3m & long_long
        short_sig = short_3m & short_long
    else:  # "mid"
        long_sig, short_sig = long_3m, short_3m

    # warmup
    warmup = max(lb3, ex3) + 5
    idx_arr = np.arange(len(df))
    warm_ok = idx_arr >= warmup
    long_sig = long_sig & pd.Series(warm_ok, index=df.index)
    short_sig = short_sig & pd.Series(warm_ok, index=df.index)

    # session filter
    if cfg["session"]:
        h_utc = df.index.hour
        sess_asia = ((h_utc >= 0) & (h_utc < 7)) | ((h_utc >= 21) & (h_utc < 24))
        sess_eu = (h_utc >= 7) & (h_utc < 13)
        sess_ny = (h_utc >= 13) & (h_utc < 21)
        sess_pass = ((sess_asia & cfg["asia"]) | (sess_eu & cfg["eu"]) | (sess_ny & cfg["ny"]))
        sess_pass = pd.Series(sess_pass, index=df.index)
        long_sig = long_sig & sess_pass
        short_sig = short_sig & sess_pass

    # margin filter
    if cfg["margin"] > 0:
        margin_long = (c - high_3m) / a
        margin_short = (low_3m - c) / a
        long_sig = long_sig & (margin_long >= cfg["margin"])
        short_sig = short_sig & (margin_short >= cfg["margin"])

    return pd.DataFrame({
        "open": o, "high": h, "low": l, "close": c, "atr": a,
        "long_sig": long_sig.fillna(False), "short_sig": short_sig.fillna(False),
    }, index=df.index)


# ============================================================
# Trade simulation (TrendBreakV1: 次バー始値約定)
# ============================================================
@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    entry: float
    sl: float
    tp: float
    exit_price: float
    pnl: float
    pnl_r: float
    bars_held: int


def simulate(sig: pd.DataFrame, cfg: dict) -> list[Trade]:
    trades: list[Trade] = []
    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    long_sig = sig["long_sig"].to_numpy()
    short_sig = sig["short_sig"].to_numpy()
    idx = sig.index

    in_pos_until = -1
    cooldown_until = -1

    for i in range(len(sig) - 1):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        # シグナル足の close で発火 → i+1 のopen で約定
        if long_sig[i] or short_sig[i]:
            entry_bar = i + 1
            if entry_bar >= len(sig):
                break
            entry = o[entry_bar]
            sig_atr = a[i]
            if np.isnan(sig_atr) or sig_atr <= 0:
                continue
            sl_dist = sig_atr * cfg["sl_atr"]
            if long_sig[i]:
                direction = "long"
                sl = entry - sl_dist
                tp = entry + sl_dist * cfg["tp_rr"]
            else:
                direction = "short"
                sl = entry + sl_dist
                tp = entry - sl_dist * cfg["tp_rr"]

            for j in range(entry_bar, len(sig)):
                if direction == "long":
                    hit_sl = l[j] <= sl
                    hit_tp = h[j] >= tp
                    if hit_sl and hit_tp:
                        ex = sl; pnl = ex - entry
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
                    if hit_sl:
                        ex = sl; pnl = ex - entry
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
                    if hit_tp:
                        ex = tp; pnl = ex - entry
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
                else:
                    hit_sl = h[j] >= sl
                    hit_tp = l[j] <= tp
                    if hit_sl and hit_tp:
                        ex = sl; pnl = entry - ex
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
                    if hit_sl:
                        ex = sl; pnl = entry - ex
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
                    if hit_tp:
                        ex = tp; pnl = entry - ex
                        trades.append(Trade(idx[i], idx[j], direction, entry, sl, tp, ex, pnl, pnl/sl_dist, j-entry_bar))
                        in_pos_until = j
                        cooldown_until = j + cfg["cooldown"]
                        break
    return trades


def summarize(name: str, mode: str, trades: list[Trade]) -> dict:
    if not trades:
        return {"name": name, "mode": mode, "trades": 0, "wins": 0, "losses": 0,
                "win_rate": 0.0, "pf": np.nan, "expectancy_R": 0.0, "net_R": 0.0, "max_dd_R": 0.0}
    df = pd.DataFrame([t.__dict__ for t in trades])
    wins = int((df["pnl_r"] > 0).sum())
    losses = int((df["pnl_r"] <= 0).sum())
    gp = df.loc[df["pnl_r"] > 0, "pnl_r"].sum()
    gl = df.loc[df["pnl_r"] <= 0, "pnl_r"].sum()
    pf = gp / abs(gl) if gl < 0 else np.inf
    equity = df["pnl_r"].cumsum()
    dd = float((equity.cummax() - equity).max())
    return {"name": name, "mode": mode, "trades": len(df), "wins": wins, "losses": losses,
            "win_rate": wins/len(df)*100, "pf": pf, "expectancy_R": df["pnl_r"].mean(),
            "net_R": df["pnl_r"].sum(), "max_dd_R": dd}


def run(instruments: Iterable[str], mode: str, year_from=None, year_to=None) -> list[dict]:
    presets = PRESETS_RELAXED if mode == "relaxed" else PRESETS_CONSERVATIVE
    summaries = []
    for name in instruments:
        if name not in presets:
            print(f"[SKIP] {name}: no preset")
            continue
        try:
            df = load_instrument(name)
        except Exception as e:
            print(f"[SKIP] {name}: {e}")
            continue
        if year_from:
            df = df[df.index.year >= year_from]
        if year_to:
            df = df[df.index.year <= year_to]
        sig = compute_signals(df, presets[name])
        trades = simulate(sig, presets[name])
        s = summarize(name, mode, trades)
        summaries.append(s)
        print(f"  [{mode:11}] {name:7}  Trades:{s['trades']:4}  WR:{s['win_rate']:5.1f}%  "
              f"PF:{s['pf']:5.2f}  Net:{s['net_R']:+7.1f}R  "
              f"Expect:{s['expectancy_R']:+.3f}R  MaxDD:{s['max_dd_R']:5.1f}R")
    return summaries


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    ap.add_argument("--mode", choices=["conservative", "relaxed", "both"], default="both")
    ap.add_argument("--year-from", type=int, default=None)
    ap.add_argument("--year-to", type=int, default=None)
    args = ap.parse_args()

    modes = ["conservative", "relaxed"] if args.mode == "both" else [args.mode]
    all_rows = []
    for m in modes:
        print(f"\n========== TrendBreakV1 [{m}] ==========")
        rows = run(args.instruments, m, args.year_from, args.year_to)
        all_rows.extend(rows)
    if all_rows:
        df = pd.DataFrame(all_rows)
        print("\n========== Summary ==========")
        print(df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        for m in modes:
            sub = df[df["mode"] == m]
            t = sub["trades"].sum(); w = sub["wins"].sum(); n = sub["net_R"].sum()
            wr = w/t*100 if t else 0
            print(f"  [{m:11}] TOTAL  Trades:{t}  WR:{wr:.1f}%  Net:{n:+.1f}R")

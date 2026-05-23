"""
Sai H1 Strategy backtester
Pineスクリプトの「Sai H1 Strategy」と同等のロジックをPythonで再現し、
F87104/test の H1 OHLCデータでバックテストする。
"""
from __future__ import annotations

import argparse
import glob
import os
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd


# ============================================================
# Pine 風ヘルパー
# ============================================================
def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    # Pine ta.atr は RMA (Wilder's smoothing) を使う
    return tr.ewm(alpha=1.0 / length, adjust=False).mean()


def sma(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length).mean()


def rolling_max(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length).max()


def rolling_min(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length).min()


def highest_bars(s: pd.Series, length: int) -> pd.Series:
    """Pine ta.highestbars: 最高値があるバーまでのオフセット (0 = 現在のバー, -1 = 1本前 ...)"""
    return s.rolling(length).apply(lambda x: np.argmax(x) - (length - 1), raw=True)


def lowest_bars(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length).apply(lambda x: np.argmin(x) - (length - 1), raw=True)


def barssince(cond: pd.Series) -> pd.Series:
    """条件が最後にTrueだった時点からのバー数. 一度もTrueでなければ NaN."""
    n = len(cond)
    out = np.full(n, np.nan)
    last = -1
    arr = cond.to_numpy()
    for i in range(n):
        if arr[i]:
            last = i
        if last >= 0:
            out[i] = i - last
    return pd.Series(out, index=cond.index)


# ============================================================
# Strategy parameters
# ============================================================
@dataclass
class SaiParams:
    medium_lookback: int = 520
    short_lookback: int = 72
    recent_lookback: int = 8
    atr_len: int = 14
    trend_atr: float = 2.0
    momentum_len: int = 12
    momentum_atr: float = 1.0
    body_ratio_min: float = 0.50
    stag_bars: int = 8
    tight_atr: float = 1.20
    wide_atr: float = 2.50
    break_buffer_atr: float = 0.10
    key_lookback: int = 720
    key_near_atr: float = 1.25
    range_bars: int = 480
    range_max_atr: float = 10.0
    second_break_lookback: int = 160
    v_lookback: int = 96
    v_move_atr: float = 3.0
    v_recovery: float = 0.80
    cooldown_bars: int = 24
    sl_atr_mult: float = 1.5
    rr_ratio: float = 2.0
    skip_holiday: bool = True


# ============================================================
# Indicator pipeline (Pine 移植)
# ============================================================
def compute_signals(df: pd.DataFrame, p: SaiParams) -> pd.DataFrame:
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]

    a = atr(h, l, c, p.atr_len)

    # --- Trend ---
    segment = max(5, p.medium_lookback // 5)
    medium_sma = sma(c, segment)
    first_medium = medium_sma.shift(p.medium_lookback - segment)
    medium_delta = medium_sma - first_medium
    medium_long = medium_delta > a * p.trend_atr
    medium_short = medium_delta < -a * p.trend_atr

    short_segment = max(5, p.short_lookback // 5)
    short_sma = sma(c, short_segment)
    first_short = short_sma.shift(p.short_lookback - short_segment)
    short_delta = short_sma - first_short
    recent_delta = c - c.shift(p.recent_lookback)
    short_long = (recent_delta > a * 0.35) | (short_delta > a * p.trend_atr)
    short_short = (recent_delta < -a * 0.35) | (short_delta < -a * p.trend_atr)

    long_aligned = medium_long & short_long
    short_aligned = medium_short & short_short

    # --- Momentum ---
    net_move = c - o.shift(p.momentum_len - 1)
    bullish_body = (c > o).astype(float)
    bearish_body = (c < o).astype(float)
    long_bodies = bullish_body.rolling(p.momentum_len).sum() / p.momentum_len
    short_bodies = bearish_body.rolling(p.momentum_len).sum() / p.momentum_len
    long_momentum = (net_move > a * p.momentum_atr) & (long_bodies >= p.body_ratio_min)
    short_momentum = (net_move < -a * p.momentum_atr) & (short_bodies >= p.body_ratio_min)

    # --- Stagnation / Break ---
    zone_high = rolling_max(h.shift(1), p.stag_bars)
    zone_low = rolling_min(l.shift(1), p.stag_bars)
    zone_width = zone_high - zone_low
    tight_stag = zone_width <= a * p.tight_atr
    wide_stag = (~tight_stag) & (zone_width <= a * p.wide_atr)
    has_stag = tight_stag | wide_stag
    break_long = has_stag & (c > zone_high + a * p.break_buffer_atr)
    break_short = has_stag & (c < zone_low - a * p.break_buffer_atr)

    # --- Key Levels ---
    key_high = rolling_max(h.shift(1), p.key_lookback)
    key_low = rolling_min(l.shift(1), p.key_lookback)
    near_resistance = (
        ((zone_high - key_high).abs() <= a * p.key_near_atr)
        | (zone_high >= key_high - a * p.key_near_atr)
    )
    near_support = (
        ((zone_low - key_low).abs() <= a * p.key_near_atr)
        | (zone_low <= key_low + a * p.key_near_atr)
    )

    # --- Range / Second Break ---
    range_high = rolling_max(h.shift(p.second_break_lookback), p.range_bars)
    range_low = rolling_min(l.shift(p.second_break_lookback), p.range_bars)
    range_like = (range_high - range_low) <= a * p.range_max_atr

    first_break_high_bar = barssince(h > range_high + a * p.break_buffer_atr)
    first_break_low_bar = barssince(l < range_low - a * p.break_buffer_atr)

    valid_first_long = first_break_high_bar.between(1, p.second_break_lookback)
    valid_first_short = first_break_low_bar.between(1, p.second_break_lookback)

    # back inside check: 最初のブレイク以降の最安/最高を rolling で見る
    # 長さは可変なので、Pythonで明示ループする
    back_inside_long = pd.Series(False, index=df.index)
    back_inside_short = pd.Series(False, index=df.index)
    l_arr = l.to_numpy()
    h_arr = h.to_numpy()
    rh_arr = range_high.to_numpy()
    rl_arr = range_low.to_numpy()
    fbh_arr = first_break_high_bar.to_numpy()
    fbl_arr = first_break_low_bar.to_numpy()
    bil = np.zeros(len(df), dtype=bool)
    bis = np.zeros(len(df), dtype=bool)
    for i in range(len(df)):
        n = fbh_arr[i]
        if not np.isnan(n) and 1 <= n <= p.second_break_lookback:
            start = i - int(n) + 1
            if start < 0:
                start = 0
            if l_arr[start:i + 1].min() < rh_arr[i]:
                bil[i] = True
        m = fbl_arr[i]
        if not np.isnan(m) and 1 <= m <= p.second_break_lookback:
            start = i - int(m) + 1
            if start < 0:
                start = 0
            if h_arr[start:i + 1].max() > rl_arr[i]:
                bis[i] = True
    back_inside_long = pd.Series(bil, index=df.index)
    back_inside_short = pd.Series(bis, index=df.index)

    second_break_long = (
        range_like & valid_first_long & back_inside_long
        & (c > range_high + a * p.break_buffer_atr)
    )
    second_break_short = (
        range_like & valid_first_short & back_inside_short
        & (c < range_low - a * p.break_buffer_atr)
    )

    # --- V-reversal ---
    lowest_idx = lowest_bars(l, p.v_lookback)
    highest_idx = highest_bars(h, p.v_lookback)
    valley = rolling_min(l, p.v_lookback)
    peak = rolling_max(h, p.v_lookback)
    v_range = peak - valley
    long_v = (
        (highest_idx < lowest_idx)
        & (v_range >= a * p.v_move_atr)
        & ((c - valley) >= v_range * p.v_recovery)
    )
    short_v = (
        (lowest_idx < highest_idx)
        & (v_range >= a * p.v_move_atr)
        & ((peak - c) >= v_range * p.v_recovery)
    )

    # --- Holiday ---
    if p.skip_holiday:
        idx = df.index
        holiday = ((idx.month == 12) & (idx.day >= 15)) | ((idx.month == 1) & (idx.day <= 10))
        holiday = pd.Series(holiday, index=df.index)
    else:
        holiday = pd.Series(False, index=df.index)

    base_long = (~holiday) & long_aligned & long_momentum
    base_short = (~holiday) & short_aligned & short_momentum
    long_signal = base_long & (break_long | second_break_long | long_v) & (~near_resistance)
    short_signal = base_short & (break_short | second_break_short | short_v) & (~near_support)

    # Trigger = OFF→ON 変化 + cooldown
    long_raw = long_signal & (~long_signal.shift(1).fillna(False).astype(bool))
    short_raw = short_signal & (~short_signal.shift(1).fillna(False).astype(bool))

    out = pd.DataFrame({
        "open": o, "high": h, "low": l, "close": c, "atr": a,
        "long_signal": long_signal, "short_signal": short_signal,
        "long_raw": long_raw, "short_raw": short_raw,
        "break_long": break_long, "break_short": break_short,
        "second_break_long": second_break_long, "second_break_short": second_break_short,
        "long_v": long_v, "short_v": short_v,
    }, index=df.index)
    return out


# ============================================================
# Trade simulation
# ============================================================
@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str  # "long" or "short"
    entry: float
    sl: float
    tp: float
    exit_price: float
    pnl: float  # in price units
    pnl_r: float  # in R units (positive R = TP hit, -1R = SL hit)
    setup: str  # "Break" / "2nd" / "V"
    bars_held: int


def setup_label(row) -> str:
    if row["break_long"] or row["break_short"]:
        return "Break"
    if row["second_break_long"] or row["second_break_short"]:
        return "2nd"
    if row["long_v"] or row["short_v"]:
        return "V"
    return "?"


def simulate(sig: pd.DataFrame, p: SaiParams) -> list[Trade]:
    trades: list[Trade] = []
    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    c = sig["close"].to_numpy()
    a = sig["atr"].to_numpy()
    long_raw = sig["long_raw"].to_numpy()
    short_raw = sig["short_raw"].to_numpy()
    idx = sig.index

    in_pos = False
    cooldown_long_until = -1
    cooldown_short_until = -1

    for i in range(len(sig)):
        if in_pos:
            continue
        if long_raw[i] and i > cooldown_long_until:
            entry = c[i]
            sl_dist = a[i] * p.sl_atr_mult
            if np.isnan(sl_dist) or sl_dist <= 0:
                continue
            sl = entry - sl_dist
            tp = entry + sl_dist * p.rr_ratio
            # 次のバーから順に SL/TP のヒットを判定
            for j in range(i + 1, len(sig)):
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
                if hit_sl and hit_tp:
                    # 同一バーは保守的に SL 優先
                    exit_price = sl
                    pnl = exit_price - entry
                    trades.append(Trade(idx[i], idx[j], "long", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_long_until = i + p.cooldown_bars
                    break
                if hit_sl:
                    exit_price = sl
                    pnl = exit_price - entry
                    trades.append(Trade(idx[i], idx[j], "long", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_long_until = i + p.cooldown_bars
                    break
                if hit_tp:
                    exit_price = tp
                    pnl = exit_price - entry
                    trades.append(Trade(idx[i], idx[j], "long", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_long_until = i + p.cooldown_bars
                    break
        elif short_raw[i] and i > cooldown_short_until:
            entry = c[i]
            sl_dist = a[i] * p.sl_atr_mult
            if np.isnan(sl_dist) or sl_dist <= 0:
                continue
            sl = entry + sl_dist
            tp = entry - sl_dist * p.rr_ratio
            for j in range(i + 1, len(sig)):
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp
                if hit_sl and hit_tp:
                    exit_price = sl
                    pnl = entry - exit_price
                    trades.append(Trade(idx[i], idx[j], "short", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_short_until = i + p.cooldown_bars
                    break
                if hit_sl:
                    exit_price = sl
                    pnl = entry - exit_price
                    trades.append(Trade(idx[i], idx[j], "short", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_short_until = i + p.cooldown_bars
                    break
                if hit_tp:
                    exit_price = tp
                    pnl = entry - exit_price
                    trades.append(Trade(idx[i], idx[j], "short", entry, sl, tp,
                                        exit_price, pnl, pnl / sl_dist,
                                        setup_label(sig.iloc[i]), j - i))
                    cooldown_short_until = i + p.cooldown_bars
                    break
    return trades


# ============================================================
# Data loading
# ============================================================
DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "F87104_test")

INSTRUMENTS = {
    "EURJPY":  "EURJPY2014-2024/EURJPY_H1_*.csv",
    "USDJPY":  "USDJPY2014-2024/USDJPY_H1_*.csv",
    "AUDJPY":  "AUDJPY2014-2024/AUDJPY H1 *.csv",
    "CHFJPY":  "CHFJPY2014-2024/CHFJPY_H1_*.csv",
    "GBPJPY":  "GBYJPY2014-2024/GBYJPY H1/GBY JPY H1 *.csv",
    "XAUUSD":  "XAUUSD2014-2024/XAUUSD_H1_*.csv",
    "SILVER":  "SILVER2014-2024/*.csv",
}


def load_instrument(name: str) -> pd.DataFrame:
    pattern = os.path.join(DATA_ROOT, INSTRUMENTS[name])
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No data for {name}: {pattern}")
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = [c.strip("<>").lower() for c in df.columns]
        # 日付列の正規化
        if "dtyyyymmdd" in df.columns:
            dt = pd.to_datetime(df["dtyyyymmdd"].astype(str)
                                + df["time"].astype(str).str.zfill(4),
                                format="%Y%m%d%H%M")
        elif "date" in df.columns:
            dt = pd.to_datetime(df["date"] + " " + df["time"])
        else:
            raise ValueError(f"Unknown date format in {f}")
        df["datetime"] = dt
        df = df.set_index("datetime")[["open", "high", "low", "close"]].astype(float)
        dfs.append(df)
    out = pd.concat(dfs).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    # 全データをH1に統一 (M1/M5/M15混在対策)
    inferred_minutes = (out.index.to_series().diff().dt.total_seconds().dropna() / 60).median()
    if inferred_minutes < 50:
        out = out.resample("1h").agg({
            "open": "first", "high": "max", "low": "min", "close": "last"
        }).dropna()
    return out


# ============================================================
# Reporting
# ============================================================
def summarize(name: str, trades: list[Trade]) -> dict:
    if not trades:
        return {"instrument": name, "trades": 0, "win_rate": 0.0, "pf": np.nan,
                "expectancy_R": 0.0, "net_R": 0.0, "max_dd_R": 0.0}
    df = pd.DataFrame([t.__dict__ for t in trades])
    wins = (df["pnl_r"] > 0).sum()
    losses = (df["pnl_r"] <= 0).sum()
    gp = df.loc[df["pnl_r"] > 0, "pnl_r"].sum()
    gl = df.loc[df["pnl_r"] <= 0, "pnl_r"].sum()
    pf = gp / abs(gl) if gl < 0 else np.inf
    equity = df["pnl_r"].cumsum()
    dd = (equity.cummax() - equity).max()
    return {
        "instrument": name,
        "trades": len(df),
        "wins": int(wins),
        "losses": int(losses),
        "win_rate": wins / len(df) * 100,
        "pf": pf,
        "expectancy_R": df["pnl_r"].mean(),
        "net_R": df["pnl_r"].sum(),
        "max_dd_R": float(dd),
    }


def main(instruments: Iterable[str], year_from: int | None = None, year_to: int | None = None,
         show_trades: bool = False, by_setup: bool = False):
    params = SaiParams()
    all_summary = []
    all_trades: list[Trade] = []
    for name in instruments:
        try:
            df = load_instrument(name)
        except Exception as e:
            print(f"[SKIP] {name}: {e}")
            continue
        if year_from:
            df = df[df.index.year >= year_from]
        if year_to:
            df = df[df.index.year <= year_to]
        print(f"\n=== {name}  bars={len(df)}  {df.index.min()} ... {df.index.max()} ===")
        sig = compute_signals(df, params)
        trades = simulate(sig, params)
        all_trades.extend([(name, t) for t in trades])
        s = summarize(name, trades)
        all_summary.append(s)
        print(f"  Trades: {s['trades']}  WinRate: {s['win_rate']:.1f}%  "
              f"PF: {s['pf']:.2f}  Net: {s['net_R']:+.1f}R  "
              f"Expectancy: {s['expectancy_R']:+.3f}R  MaxDD: {s['max_dd_R']:.1f}R")

        if by_setup and trades:
            df_t = pd.DataFrame([t.__dict__ for t in trades])
            for setup, g in df_t.groupby("setup"):
                wr = (g["pnl_r"] > 0).mean() * 100
                pf_s = g.loc[g["pnl_r"] > 0, "pnl_r"].sum() / abs(g.loc[g["pnl_r"] <= 0, "pnl_r"].sum() or -1e-9)
                print(f"    [{setup:5}] n={len(g):3}  WR={wr:5.1f}%  PF={pf_s:5.2f}  Net={g['pnl_r'].sum():+.1f}R")

        if show_trades and trades:
            df_t = pd.DataFrame([t.__dict__ for t in trades])
            print(df_t[["entry_time", "exit_time", "direction", "setup",
                        "entry", "exit_price", "pnl_r", "bars_held"]]
                  .to_string(index=False))

    # 集計
    if all_summary:
        agg = pd.DataFrame(all_summary)
        total_trades = agg["trades"].sum()
        total_wins = agg["wins"].sum()
        total_net = agg["net_R"].sum()
        print("\n========== TOTAL ==========")
        print(agg.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        if total_trades > 0:
            print(f"\nOVERALL WinRate: {total_wins/total_trades*100:.1f}%  "
                  f"Trades: {total_trades}  NetR: {total_net:+.1f}R")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+", default=list(INSTRUMENTS.keys()))
    ap.add_argument("--year-from", type=int, default=None)
    ap.add_argument("--year-to", type=int, default=None)
    ap.add_argument("--show-trades", action="store_true")
    ap.add_argument("--by-setup", action="store_true")
    args = ap.parse_args()
    main(args.instruments, args.year_from, args.year_to, args.show_trades, args.by_setup)

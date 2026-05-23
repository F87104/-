"""
TrendBreakV1 Relaxed の精度向上のための多方面最適化テスト

Aブロック: パラメータ感度分析 (SL ATR, TP RR, lookback, exclude)
Bブロック: 決済戦略改良 (トレール / ブレイクイーブン / 部分利確)
Cブロック: 追加フィルター (大局トレンド / ボラ / 曜日)
Dブロック: 通貨別ベスト構成
"""
from __future__ import annotations

import argparse
import itertools
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd

from sai_backtest import atr, rolling_max, rolling_min, load_instrument


# ============================================================
# Config (TrendBreakV1 Relaxed base)
# ============================================================
@dataclass
class TBConfig:
    lookback_3m: int = 180
    exclude: int = 30
    sl_atr: float = 1.5
    tp_rr: float = 3.0
    level_kind: str = "mid"   # "mid"/"any"/"long"/"confluence"
    session: bool = False
    asia: bool = True
    eu: bool = False
    ny: bool = True
    margin: float = 0.0
    cooldown: int = 0
    # 改良パラメータ
    use_trail: bool = False           # 1R達成後にBEへトレール
    trail_at_R: float = 1.0           # 何Rで動かすか
    partial_at_R: float = 0.0         # >0なら部分利確 (1Rで50%手仕舞い等)
    partial_pct: float = 0.5
    require_close_in_top: float = 0.0 # 終値が足の上位X%にあること (0=無効, 0.7=上位30%)
    trend_filter_len: int = 0         # >0で長期SMA方向と一致のみエントリー
    atr_min_pct: float = 0.0          # ATR / close >= 閾値
    atr_max_pct: float = 999.0        # ATR / close <= 閾値
    weekday_mask: int = 0b1111111     # 月-日 ビットマスク (1=trade可)


# ============================================================
# Signal calc
# ============================================================
ATR_PERIOD = 14
LOOKBACK_LONG = 5000
EXCLUDE_LONG = 760


def compute_signals(df: pd.DataFrame, cfg: TBConfig) -> pd.DataFrame:
    o = df["open"]; h = df["high"]; l = df["low"]; c = df["close"]
    a = atr(h, l, c, ATR_PERIOD)

    high_3m = rolling_max(h.shift(1), cfg.lookback_3m)
    low_3m  = rolling_min(l.shift(1), cfg.lookback_3m)
    high_long = rolling_max(h.shift(1), LOOKBACK_LONG)
    low_long  = rolling_min(l.shift(1), LOOKBACK_LONG)

    recent_high_3m = rolling_max(h.shift(1), cfg.exclude)
    recent_low_3m  = rolling_min(l.shift(1), cfg.exclude)
    recent_high_long = rolling_max(h.shift(1), EXCLUDE_LONG)
    recent_low_long  = rolling_min(l.shift(1), EXCLUDE_LONG)

    long_3m  = (c > high_3m) & (recent_high_3m < high_3m)
    short_3m = (c < low_3m)  & (recent_low_3m  > low_3m)
    long_long  = (c > high_long)  & (recent_high_long < high_long)
    short_long = (c < low_long)   & (recent_low_long  > low_long)

    if cfg.level_kind == "long":
        long_sig, short_sig = long_long, short_long
    elif cfg.level_kind == "any":
        long_sig = long_3m | long_long; short_sig = short_3m | short_long
    elif cfg.level_kind == "confluence":
        long_sig = long_3m & long_long; short_sig = short_3m & short_long
    else:
        long_sig, short_sig = long_3m, short_3m

    warmup = max(cfg.lookback_3m, cfg.exclude) + 5
    warm_ok = np.arange(len(df)) >= warmup
    long_sig = long_sig & pd.Series(warm_ok, index=df.index)
    short_sig = short_sig & pd.Series(warm_ok, index=df.index)

    if cfg.session:
        h_utc = df.index.hour
        sess_asia = ((h_utc >= 0) & (h_utc < 7)) | ((h_utc >= 21) & (h_utc < 24))
        sess_eu = (h_utc >= 7) & (h_utc < 13)
        sess_ny = (h_utc >= 13) & (h_utc < 21)
        sess_pass = ((sess_asia & cfg.asia) | (sess_eu & cfg.eu) | (sess_ny & cfg.ny))
        long_sig = long_sig & pd.Series(sess_pass, index=df.index)
        short_sig = short_sig & pd.Series(sess_pass, index=df.index)

    if cfg.margin > 0:
        long_sig = long_sig & ((c - high_3m) / a >= cfg.margin)
        short_sig = short_sig & ((low_3m - c) / a >= cfg.margin)

    # --- 追加フィルター ---
    # 1) 大局トレンド SMA フィルター
    if cfg.trend_filter_len > 0:
        trend_sma = c.rolling(cfg.trend_filter_len).mean()
        long_sig = long_sig & (c > trend_sma)
        short_sig = short_sig & (c < trend_sma)

    # 2) ボラフィルター
    if cfg.atr_min_pct > 0 or cfg.atr_max_pct < 999:
        atr_pct = a / c * 100
        long_sig = long_sig & (atr_pct >= cfg.atr_min_pct) & (atr_pct <= cfg.atr_max_pct)
        short_sig = short_sig & (atr_pct >= cfg.atr_min_pct) & (atr_pct <= cfg.atr_max_pct)

    # 3) 終値の足内位置
    if cfg.require_close_in_top > 0:
        bar_range = h - l
        bar_pos = (c - l) / bar_range.replace(0, np.nan)
        long_sig = long_sig & (bar_pos >= cfg.require_close_in_top)
        short_sig = short_sig & ((1 - bar_pos) >= cfg.require_close_in_top)

    # 4) 曜日マスク
    if cfg.weekday_mask != 0b1111111:
        wd = df.index.dayofweek  # 0=Mon
        mask = np.array([bool((cfg.weekday_mask >> (6 - d)) & 1) for d in wd])
        long_sig = long_sig & pd.Series(mask, index=df.index)
        short_sig = short_sig & pd.Series(mask, index=df.index)

    return pd.DataFrame({
        "open": o, "high": h, "low": l, "close": c, "atr": a,
        "long_sig": long_sig.fillna(False), "short_sig": short_sig.fillna(False),
    }, index=df.index)


# ============================================================
# Trade simulation with improvements
# ============================================================
@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    entry: float
    initial_sl: float
    tp: float
    exit_price: float
    pnl_r: float
    bars_held: int


def simulate(sig: pd.DataFrame, cfg: TBConfig) -> list[Trade]:
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
        if not (long_sig[i] or short_sig[i]):
            continue
        entry_bar = i + 1
        if entry_bar >= len(sig):
            break
        entry = o[entry_bar]
        sig_atr = a[i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue
        sl_dist = sig_atr * cfg.sl_atr
        is_long = bool(long_sig[i])
        sl = entry - sl_dist if is_long else entry + sl_dist
        tp = entry + sl_dist * cfg.tp_rr if is_long else entry - sl_dist * cfg.tp_rr

        cur_sl = sl
        partial_done = False
        realized_partial_r = 0.0
        for j in range(entry_bar, len(sig)):
            # トレール: 1R達成後にSLをBEへ
            if cfg.use_trail and cur_sl == sl:
                if is_long and h[j] >= entry + sl_dist * cfg.trail_at_R:
                    cur_sl = entry
                elif (not is_long) and l[j] <= entry - sl_dist * cfg.trail_at_R:
                    cur_sl = entry

            # 部分利確
            if cfg.partial_at_R > 0 and not partial_done:
                trigger = entry + sl_dist * cfg.partial_at_R if is_long else entry - sl_dist * cfg.partial_at_R
                if (is_long and h[j] >= trigger) or ((not is_long) and l[j] <= trigger):
                    realized_partial_r = cfg.partial_at_R * cfg.partial_pct
                    partial_done = True
                    if cfg.use_trail:
                        cur_sl = entry

            if is_long:
                hit_sl = l[j] <= cur_sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= cur_sl
                hit_tp = l[j] <= tp

            if hit_sl and hit_tp:
                # 同一バーは保守: SL優先
                ex = cur_sl
                base_r = (ex - entry) / sl_dist if is_long else (entry - ex) / sl_dist
                final_r = realized_partial_r + base_r * (1 - cfg.partial_pct if partial_done else 1.0)
                trades.append(Trade(idx[i], idx[j], "long" if is_long else "short",
                                    entry, sl, tp, ex, final_r, j - entry_bar))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_sl:
                ex = cur_sl
                base_r = (ex - entry) / sl_dist if is_long else (entry - ex) / sl_dist
                final_r = realized_partial_r + base_r * (1 - cfg.partial_pct if partial_done else 1.0)
                trades.append(Trade(idx[i], idx[j], "long" if is_long else "short",
                                    entry, sl, tp, ex, final_r, j - entry_bar))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_tp:
                ex = tp
                base_r = cfg.tp_rr
                final_r = realized_partial_r + base_r * (1 - cfg.partial_pct if partial_done else 1.0)
                trades.append(Trade(idx[i], idx[j], "long" if is_long else "short",
                                    entry, sl, tp, ex, final_r, j - entry_bar))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    return trades


def stats(trades: list[Trade]) -> dict:
    if not trades:
        return {"n": 0, "wr": 0.0, "pf": np.nan, "exp": 0.0, "net": 0.0, "dd": 0.0}
    df = pd.DataFrame([t.__dict__ for t in trades])
    wins = (df["pnl_r"] > 0).sum()
    gp = df.loc[df["pnl_r"] > 0, "pnl_r"].sum()
    gl = df.loc[df["pnl_r"] <= 0, "pnl_r"].sum()
    eq = df["pnl_r"].cumsum()
    return {
        "n": len(df), "wr": wins/len(df)*100,
        "pf": gp/abs(gl) if gl < 0 else np.inf,
        "exp": df["pnl_r"].mean(), "net": df["pnl_r"].sum(),
        "dd": float((eq.cummax() - eq).max()),
    }


def evaluate(name: str, cfg: TBConfig, df: pd.DataFrame) -> dict:
    sig = compute_signals(df, cfg)
    trades = simulate(sig, cfg)
    s = stats(trades)
    s["name"] = name
    return s


# ============================================================
# Base presets (from Pine TrendBreakV1 Relaxed)
# ============================================================
BASE = {
    "XAUUSD": TBConfig(lookback_3m=240, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="mid",
                       session=True, asia=True, ny=True, cooldown=0),
    "USDJPY": TBConfig(lookback_3m=180, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="mid",
                       session=True, asia=True, ny=True, margin=0.3, cooldown=0),
    "EURJPY": TBConfig(lookback_3m=180, exclude=30, sl_atr=2.0, tp_rr=3.0, level_kind="mid",
                       session=True, asia=True, ny=True, cooldown=24),
    "GBPJPY": TBConfig(lookback_3m=180, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                       session=False, cooldown=0),
    "CHFJPY": TBConfig(lookback_3m=480, exclude=90, sl_atr=2.5, tp_rr=3.0, level_kind="any",
                       session=False, cooldown=0),
    "AUDJPY": TBConfig(lookback_3m=480, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                       session=False, cooldown=0),
    "SILVER": TBConfig(lookback_3m=360, exclude=30, sl_atr=1.5, tp_rr=3.0, level_kind="any",
                       session=False, cooldown=24),
}


# ============================================================
# Test blocks
# ============================================================
def block_a_sensitivity(instruments: list[str], data: dict[str, pd.DataFrame]):
    """Aブロック: パラメータ感度分析"""
    print("\n" + "=" * 80)
    print("【Aブロック】 パラメータ感度分析 (各通貨で1つずつ振る)")
    print("=" * 80)
    rows = []
    for name in instruments:
        base = BASE[name]
        df = data[name]
        # 1) SL ATR mult
        for sl in [1.0, 1.5, 2.0, 2.5, 3.0]:
            cfg = TBConfig(**{**base.__dict__, "sl_atr": sl})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "axis": "sl_atr", "val": sl, **s})
        # 2) TP RR
        for rr in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            cfg = TBConfig(**{**base.__dict__, "tp_rr": rr})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "axis": "tp_rr", "val": rr, **s})
        # 3) lookback
        for lb in [90, 120, 180, 240, 360, 480]:
            cfg = TBConfig(**{**base.__dict__, "lookback_3m": lb})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "axis": "lookback", "val": lb, **s})
        # 4) exclude
        for ex in [15, 30, 60, 90, 120]:
            cfg = TBConfig(**{**base.__dict__, "exclude": ex})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "axis": "exclude", "val": ex, **s})
    df_r = pd.DataFrame(rows)
    for ax in ["sl_atr", "tp_rr", "lookback", "exclude"]:
        sub = df_r[df_r["axis"] == ax]
        print(f"\n--- {ax} 感度 ---")
        for inst in instruments:
            best = sub[sub["inst"] == inst].sort_values("net", ascending=False).head(2)
            for _, r in best.iterrows():
                print(f"  {inst:7} {ax}={r['val']:>5}  n={r['n']:>4}  WR={r['wr']:5.1f}%  "
                      f"PF={r['pf']:5.2f}  Net={r['net']:+7.1f}R  DD={r['dd']:5.1f}R")
    return df_r


def block_b_exits(instruments: list[str], data: dict[str, pd.DataFrame]):
    """Bブロック: 決済戦略の比較"""
    print("\n" + "=" * 80)
    print("【Bブロック】 決済戦略の改良")
    print("=" * 80)
    variants = {
        "Base (固定 RR=3)": dict(),
        "BE@1R トレール":  dict(use_trail=True, trail_at_R=1.0),
        "BE@0.5R":         dict(use_trail=True, trail_at_R=0.5),
        "部分利確 1R/50%": dict(partial_at_R=1.0, partial_pct=0.5),
        "部分利確 +BE@1R": dict(use_trail=True, trail_at_R=1.0, partial_at_R=1.0, partial_pct=0.5),
        "RR=4 + BE@1R":    dict(use_trail=True, trail_at_R=1.0, tp_rr=4.0),
        "RR=5 + BE@1R":    dict(use_trail=True, trail_at_R=1.0, tp_rr=5.0),
        "RR=2 (高勝率狙)":  dict(tp_rr=2.0),
    }
    rows = []
    for name in instruments:
        df = data[name]
        for label, mod in variants.items():
            cfg = TBConfig(**{**BASE[name].__dict__, **mod})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "variant": label, **s})
    df_r = pd.DataFrame(rows)
    pvt = df_r.pivot(index="inst", columns="variant", values="net")
    print("\nNet R (各セルが純利益R)")
    print(pvt.to_string(float_format=lambda x: f"{x:+.1f}"))
    # ベスト分散
    print("\n各通貨のベスト決済戦略:")
    for inst in instruments:
        sub = df_r[df_r["inst"] == inst].sort_values("net", ascending=False)
        b = sub.iloc[0]
        print(f"  {inst:7} → [{b['variant']:18}]  n={b['n']:>4} WR={b['wr']:5.1f}%  "
              f"PF={b['pf']:5.2f}  Net={b['net']:+7.1f}R  DD={b['dd']:5.1f}R")
    return df_r


def block_c_filters(instruments: list[str], data: dict[str, pd.DataFrame]):
    """Cブロック: 追加フィルター効果"""
    print("\n" + "=" * 80)
    print("【Cブロック】 追加フィルター効果")
    print("=" * 80)
    variants = {
        "Base":                   dict(),
        "大局トレンドSMA200":      dict(trend_filter_len=200),
        "大局トレンドSMA500":      dict(trend_filter_len=500),
        "ボラ最低 ATR>=0.1%":      dict(atr_min_pct=0.1),
        "ボラ上限 ATR<=1.0%":      dict(atr_max_pct=1.0),
        "終値上位30%必須":          dict(require_close_in_top=0.7),
        "終値上位20%必須":          dict(require_close_in_top=0.8),
        "金曜オフ":                dict(weekday_mask=0b1111000),  # Mon-Thu
        "Trend+終値":              dict(trend_filter_len=200, require_close_in_top=0.7),
        "全部入り":                dict(trend_filter_len=200, require_close_in_top=0.7, atr_max_pct=1.0),
    }
    rows = []
    for name in instruments:
        df = data[name]
        for label, mod in variants.items():
            cfg = TBConfig(**{**BASE[name].__dict__, **mod})
            s = evaluate(name, cfg, df)
            rows.append({"inst": name, "variant": label, **s})
    df_r = pd.DataFrame(rows)
    pvt = df_r.pivot(index="inst", columns="variant", values="net")
    cols = list(variants.keys())
    pvt = pvt[cols]
    print("\nNet R (フィルター別)")
    print(pvt.to_string(float_format=lambda x: f"{x:+.1f}"))
    print("\n各通貨のベスト・フィルター構成:")
    for inst in instruments:
        sub = df_r[df_r["inst"] == inst].sort_values("net", ascending=False)
        b = sub.iloc[0]
        print(f"  {inst:7} → [{b['variant']:22}]  n={b['n']:>4} WR={b['wr']:5.1f}%  "
              f"PF={b['pf']:5.2f}  Net={b['net']:+7.1f}R  DD={b['dd']:5.1f}R")
    return df_r


def block_d_best_combo(instruments: list[str], data: dict[str, pd.DataFrame]):
    """Dブロック: 通貨別ベスト構成のフルグリッドサーチ"""
    print("\n" + "=" * 80)
    print("【Dブロック】 通貨別ベスト構成のフルグリッドサーチ")
    print("=" * 80)
    sl_grid = [1.0, 1.5, 2.0, 2.5, 3.0]
    rr_grid = [2.5, 3.0, 4.0, 5.0]
    lb_grid = [90, 120, 180, 240, 360, 480]
    ex_grid = [15, 30, 60, 90]
    trend_grid = [0, 200, 500]
    weekday_grid = [0b1111111, 0b1111000]  # 全曜日, 金曜オフ

    print(f"\nGrid size per inst: {len(sl_grid)*len(rr_grid)*len(lb_grid)*len(ex_grid)*len(trend_grid)*len(weekday_grid)}")

    best_each = {}
    for name in instruments:
        df = data[name]
        base = BASE[name].__dict__.copy()
        best = None
        for sl, rr, lb, ex, trend, wd in itertools.product(
                sl_grid, rr_grid, lb_grid, ex_grid, trend_grid, weekday_grid):
            if ex > lb:
                continue
            mod = {"sl_atr": sl, "tp_rr": rr,
                   "lookback_3m": lb, "exclude": ex,
                   "trend_filter_len": trend, "weekday_mask": wd}
            cfg = TBConfig(**{**base, **mod})
            s = evaluate(name, cfg, df)
            if s["n"] < 30:
                continue
            score = s["net"] - s["dd"] * 0.3
            if best is None or score > best["_score"]:
                best = {**s, "_score": score, "sl_atr": sl, "tp_rr": rr,
                        "lookback": lb, "exclude": ex, "trend": trend, "wd": wd}
        best_each[name] = best
        if best:
            wd_str = "Mon-Thu" if best['wd'] == 0b1111000 else "Mon-Sun"
            print(f"\n  {name}: sl={best['sl_atr']} rr={best['tp_rr']} "
                  f"lookback={best['lookback']} exclude={best['exclude']} "
                  f"trend_sma={best['trend']} weekday={wd_str}")
            print(f"    → n={best['n']}  WR={best['wr']:.1f}%  PF={best['pf']:.2f}  "
                  f"Net={best['net']:+.1f}R  DD={best['dd']:.1f}R  Exp={best['exp']:+.3f}R")
    total = sum(b["net"] for b in best_each.values() if b)
    n_total = sum(b["n"] for b in best_each.values() if b)
    print(f"\n  TOTAL: trades={n_total}  Net={total:+.1f}R")
    return best_each


# ============================================================
# Main
# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    ap.add_argument("--blocks", nargs="+", default=["a", "b", "c", "d"])
    args = ap.parse_args()

    data = {}
    for name in args.instruments:
        try:
            print(f"Loading {name}...")
            data[name] = load_instrument(name)
        except Exception as e:
            print(f"[SKIP] {name}: {e}")

    insts = list(data.keys())
    if "a" in args.blocks:
        block_a_sensitivity(insts, data)
    if "b" in args.blocks:
        block_b_exits(insts, data)
    if "c" in args.blocks:
        block_c_filters(insts, data)
    if "d" in args.blocks:
        block_d_best_combo(insts, data)


if __name__ == "__main__":
    main()

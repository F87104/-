#!/usr/bin/env python3
"""
B7棚 XAUUSD トレンドフィルター検証

ゴールドの精度向上のため、エントリー時のトレンド判定フィルターを網羅テスト。
レンジ相場でのダマシを排除する。
"""
from __future__ import annotations
import sys, math
from pathlib import Path
import numpy as np, pandas as pd

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))
from run_b7_shelf_tv import add_features, find_v_shocks, stats

REPO_ROOT = THIS_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "backtests" / "synapse_v2_definition_grid"))
import importlib.util
_s = importlib.util.spec_from_file_location("synapse_tv",
    REPO_ROOT / "backtests" / "synapse_v2_definition_grid" / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_s)
sys.modules["synapse_tv"] = tv
_s.loader.exec_module(tv)

RUN_START = pd.Timestamp("2015-01-01")


def add_trend_features(h4):
    """トレンド判定用の追加指標"""
    df = h4.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema100"] = df["close"].ewm(span=100, adjust=False).mean()

    # EMA傾き（過去N本での変化率）
    df["ema20_slope5"] = (df["ema20"] - df["ema20"].shift(5)) / df["atr"]
    df["ema50_slope10"] = (df["ema50"] - df["ema50"].shift(10)) / df["atr"]

    # ADX
    plus_dm = df["high"].diff().clip(lower=0)
    minus_dm = (-df["low"].diff()).clip(lower=0)
    tr = pd.concat([df["high"] - df["low"],
                     (df["high"] - df["close"].shift(1)).abs(),
                     (df["low"] - df["close"].shift(1)).abs()], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr14
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr14
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    df["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()
    df["plus_di"] = plus_di
    df["minus_di"] = minus_di

    # ATR変化率（ボラティリティ拡大判定）
    df["atr_ratio"] = df["atr"] / df["atr"].rolling(50).mean()

    # 直近高値からの距離（レンジ判定）
    df["dist_from_high20"] = (df["high"].rolling(20).max() - df["close"]) / df["atr"]

    return df


def sweep_with_filter(h4, filter_func, params):
    """フィルタ付きB7棚バックテスト"""
    idx = h4.index
    o, hi, lo, cl = h4["open"].to_numpy(), h4["high"].to_numpy(), h4["low"].to_numpy(), h4["close"].to_numpy()
    atrs, body, cloc = h4["atr"].to_numpy(), h4["body_ratio"].to_numpy(), h4["close_location"].to_numpy()
    n = len(h4)
    spread, slip = tv.COST_BY_SYMBOL.get("XAUUSD", (0.30, 0.15))
    shocks = find_v_shocks(h4)
    trades_r = []
    wins = 0
    losses = 0
    in_pos_until = -1

    for shock in shocks:
        lo_conf = shock["lo_conf"]
        hi_p, lo_p = shock["hi_p"], shock["lo_p"]
        drop = hi_p - lo_p
        a_shock = atrs[shock["lo_i"]]
        if a_shock > 0 and drop / a_shock < params["drop_atr_min"]:
            continue
        for ri in range(lo_conf, min(n, lo_conf + 60)):
            recovery = (cl[ri] - lo_p) / drop if drop > 0 else 0
            if recovery < 0.65 or recovery > 1.25:
                if recovery > 1.25:
                    break
                continue
            shelf_start = ri + 1
            shelf_end = shelf_start + params["shelf_bars"]
            if shelf_end >= n - 1:
                break
            a = atrs[shelf_end]
            if not math.isfinite(a) or a <= 0:
                continue
            shelf_hi = np.max(hi[shelf_start:shelf_end])
            shelf_lo = np.min(lo[shelf_start:shelf_end])
            if (shelf_hi - shelf_lo) / a > params["shelf_atr"]:
                continue
            if shelf_lo < lo_p + drop * 0.4:
                continue
            for bi in range(shelf_end, min(n - 1, shelf_end + 30)):
                if idx[bi] < RUN_START or bi <= in_pos_until:
                    continue
                a_b = atrs[bi]
                if not math.isfinite(a_b) or a_b <= 0:
                    continue
                if cl[bi - 1] > shelf_hi:
                    break
                if cl[bi] <= shelf_hi + 0.05 * a_b:
                    continue
                if body[bi] < 0.30 or cloc[bi] < 0.50:
                    continue

                if not filter_func(h4, bi):
                    continue

                stop = shelf_lo - params["stop_buf"] * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * params["rr"]
                if risk / a_b > 2.5:
                    break
                end_i = min(n - 1, entry_i + params["max_hold"])
                exit_i, exit_price = end_i, cl[end_i]
                for j in range(entry_i, end_i + 1):
                    if lo[j] <= stop:
                        exit_i, exit_price = j, stop
                        break
                    if hi[j] >= target:
                        exit_i, exit_price = j, target
                        break
                after = (exit_price - slip) - (entry + spread / 2.0)
                r = after / risk
                trades_r.append(r)
                if r > 0:
                    wins += 1
                else:
                    losses += 1
                in_pos_until = exit_i
                break
            break
    return trades_r


def main():
    gold_path = None
    for p in sorted((REPO_ROOT / "tv_data").glob("*.csv")):
        if tv.detect_symbol(p) == "XAUUSD":
            gold_path = p
            break
    if not gold_path:
        print("XAUUSD data not found")
        return

    raw = tv.load_tv_csv(gold_path)
    h4 = add_features(raw)
    h4 = add_trend_features(h4)
    print(f"XAUUSD H4: {len(h4)} bars\n")

    base = {"shelf_bars": 3, "shelf_atr": 2.0, "drop_atr_min": 4.0,
            "rr": 3.0, "max_hold": 80, "stop_buf": 0.50}

    # ベースライン（フィルタなし）
    no_filter = lambda h4, bi: True
    base_tr = sweep_with_filter(h4, no_filter, base)
    base_s = stats(pd.Series(base_tr))
    print(f"ベースライン(フィルタなし): {base_s['trades']}件 勝率{base_s['win_rate']:.1f}% PF{base_s['pf']:.2f} 合計{base_s['total_r']:.1f}R")
    print("=" * 80)

    ema20 = h4["ema20"].to_numpy()
    ema50 = h4["ema50"].to_numpy()
    ema100 = h4["ema100"].to_numpy()
    ema20_slope5 = h4["ema20_slope5"].to_numpy()
    ema50_slope10 = h4["ema50_slope10"].to_numpy()
    adx_arr = h4["adx"].to_numpy()
    plus_di_arr = h4["plus_di"].to_numpy()
    minus_di_arr = h4["minus_di"].to_numpy()
    atr_ratio = h4["atr_ratio"].to_numpy()
    cl_arr = h4["close"].to_numpy()
    dist_high = h4["dist_from_high20"].to_numpy()

    filters = {
        # EMAフィルタ
        "終値>EMA20": lambda h4, bi: cl_arr[bi] > ema20[bi],
        "終値>EMA50": lambda h4, bi: cl_arr[bi] > ema50[bi],
        "終値>EMA100": lambda h4, bi: cl_arr[bi] > ema100[bi],
        "EMA20>EMA50": lambda h4, bi: ema20[bi] > ema50[bi],
        "EMA20>EMA50>EMA100": lambda h4, bi: ema20[bi] > ema50[bi] > ema100[bi],

        # EMA傾きフィルタ
        "EMA20傾き>0": lambda h4, bi: math.isfinite(ema20_slope5[bi]) and ema20_slope5[bi] > 0,
        "EMA20傾き>0.5": lambda h4, bi: math.isfinite(ema20_slope5[bi]) and ema20_slope5[bi] > 0.5,
        "EMA50傾き>0": lambda h4, bi: math.isfinite(ema50_slope10[bi]) and ema50_slope10[bi] > 0,

        # ADXフィルタ
        "ADX>20": lambda h4, bi: math.isfinite(adx_arr[bi]) and adx_arr[bi] > 20,
        "ADX>25": lambda h4, bi: math.isfinite(adx_arr[bi]) and adx_arr[bi] > 25,
        "ADX>30": lambda h4, bi: math.isfinite(adx_arr[bi]) and adx_arr[bi] > 30,
        "ADX<25(レンジ除外)": lambda h4, bi: math.isfinite(adx_arr[bi]) and adx_arr[bi] < 25,
        "+DI>-DI": lambda h4, bi: math.isfinite(plus_di_arr[bi]) and plus_di_arr[bi] > minus_di_arr[bi],
        "+DI>-DI & ADX>20": lambda h4, bi: math.isfinite(adx_arr[bi]) and plus_di_arr[bi] > minus_di_arr[bi] and adx_arr[bi] > 20,

        # ボラティリティフィルタ
        "ATR比>1.0(ボラ拡大)": lambda h4, bi: math.isfinite(atr_ratio[bi]) and atr_ratio[bi] > 1.0,
        "ATR比>1.2(ボラ強拡大)": lambda h4, bi: math.isfinite(atr_ratio[bi]) and atr_ratio[bi] > 1.2,
        "ATR比<0.8(ボラ縮小除外)": lambda h4, bi: math.isfinite(atr_ratio[bi]) and atr_ratio[bi] >= 0.8,

        # 高値距離フィルタ
        "20本高値距離<2ATR": lambda h4, bi: math.isfinite(dist_high[bi]) and dist_high[bi] < 2.0,
        "20本高値距離<1ATR": lambda h4, bi: math.isfinite(dist_high[bi]) and dist_high[bi] < 1.0,

        # 組み合わせ
        "終値>EMA50 & EMA20傾き>0": lambda h4, bi: cl_arr[bi] > ema50[bi] and math.isfinite(ema20_slope5[bi]) and ema20_slope5[bi] > 0,
        "終値>EMA50 & +DI>-DI": lambda h4, bi: cl_arr[bi] > ema50[bi] and math.isfinite(plus_di_arr[bi]) and plus_di_arr[bi] > minus_di_arr[bi],
        "EMA20>EMA50 & ADX>20": lambda h4, bi: ema20[bi] > ema50[bi] and math.isfinite(adx_arr[bi]) and adx_arr[bi] > 20,
        "終値>EMA50 & ATR比>1.0": lambda h4, bi: cl_arr[bi] > ema50[bi] and math.isfinite(atr_ratio[bi]) and atr_ratio[bi] > 1.0,
        "EMA20傾き>0 & +DI>-DI": lambda h4, bi: math.isfinite(ema20_slope5[bi]) and ema20_slope5[bi] > 0 and math.isfinite(plus_di_arr[bi]) and plus_di_arr[bi] > minus_di_arr[bi],
        "全部盛り(>EMA50 & EMA20傾き>0 & +DI>-DI)": lambda h4, bi: cl_arr[bi] > ema50[bi] and math.isfinite(ema20_slope5[bi]) and ema20_slope5[bi] > 0 and math.isfinite(plus_di_arr[bi]) and plus_di_arr[bi] > minus_di_arr[bi],
    }

    print(f"\n{'フィルター':<40} {'件数':>4} {'勝率':>6} {'PF':>6} {'合計R':>7}")
    print("-" * 70)
    print(f"{'ベースライン(なし)':<40} {base_s['trades']:4} {base_s['win_rate']:5.1f}% {base_s['pf']:6.2f} {base_s['total_r']:7.2f}")
    print("-" * 70)

    results = []
    for name, func in filters.items():
        tr = sweep_with_filter(h4, func, base)
        s = stats(pd.Series(tr))
        better = s["pf"] > base_s["pf"] and s["trades"] >= 5
        mark = " ⭐" if better else ""
        print(f"{name:<40} {s['trades']:4} {s['win_rate']:5.1f}% {s['pf']:6.2f} {s['total_r']:7.2f}{mark}")
        results.append({"name": name, **s})

    # ベスト3
    df = pd.DataFrame(results)
    df = df[df["trades"] >= 5].sort_values("pf", ascending=False)
    print(f"\n{'='*70}")
    print("■ ベスト5フィルター")
    print(f"{'='*70}")
    for _, row in df.head(5).iterrows():
        print(f"  {row['name']:<40} {int(row['trades']):4}件 勝率{row['win_rate']:5.1f}% PF{row['pf']:6.2f} 合計{row['total_r']:7.2f}R")


if __name__ == "__main__":
    main()

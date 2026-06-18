#!/usr/bin/env python3
"""
B7棚 正直な条件での全銘柄再最適化

calc_on_order_fills=false 相当（決済後の同足再エントリーなし）の
honestなバックテストで、各銘柄の最適パラメータを再探索する。
Pythonのバックテストは元々same-bar再エントリーをしない設計なので、
TVのcalc_on_order_fills=falseに近い挙動。
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
SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "XAGUSD", "NAS100", "XAUUSD"]


def backtest(h4, symbol, p):
    idx = h4.index
    o, hi, lo, cl = h4["open"].to_numpy(), h4["high"].to_numpy(), h4["low"].to_numpy(), h4["close"].to_numpy()
    atrs, body, cloc = h4["atr"].to_numpy(), h4["body_ratio"].to_numpy(), h4["close_location"].to_numpy()
    n = len(h4)
    spread, slip = tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))
    shocks = find_v_shocks(h4)
    trades = []
    in_pos_until = -1
    for shock in shocks:
        lo_conf = shock["lo_conf"]
        hi_p, lo_p = shock["hi_p"], shock["lo_p"]
        drop = hi_p - lo_p
        a_shock = atrs[shock["lo_i"]]
        if a_shock > 0 and drop / a_shock < p["drop"]:
            continue
        for ri in range(lo_conf, min(n, lo_conf + 60)):
            recovery = (cl[ri] - lo_p) / drop if drop > 0 else 0
            if recovery < 0.65:
                continue
            if recovery > 1.25:
                break
            shelf_start = ri + 1
            shelf_end = shelf_start + p["bars"]
            if shelf_end >= n - 1:
                break
            a = atrs[shelf_end]
            if not math.isfinite(a) or a <= 0:
                continue
            shelf_hi = np.max(hi[shelf_start:shelf_end])
            shelf_lo = np.min(lo[shelf_start:shelf_end])
            if (shelf_hi - shelf_lo) / a > p["satr"]:
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
                stop = shelf_lo - p["sl"] * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * p["rr"]
                if risk / a_b > p["risk"]:
                    break
                end_i = min(n - 1, entry_i + p["hold"])
                exit_i, exit_price = end_i, cl[end_i]
                for j in range(entry_i, end_i + 1):
                    # SL優先（保守的）: 同足で両方ヒットならSL
                    if lo[j] <= stop:
                        exit_i, exit_price = j, stop
                        break
                    if hi[j] >= target:
                        exit_i, exit_price = j, target
                        break
                after = (exit_price - slip) - (entry + spread / 2.0)
                trades.append(after / risk)
                in_pos_until = exit_i
                break
            break
    return trades


def main():
    files = sorted((REPO_ROOT / "tv_data").glob("*.csv"))
    data = {}
    for path in files:
        sym = tv.detect_symbol(path)
        if sym in SYMBOLS:
            raw = tv.load_tv_csv(path)
            if len(raw) >= 500:
                data[sym] = add_features(raw)

    print("=" * 80)
    print("B7棚 正直な条件での再最適化（SL優先・同足再エントリーなし）")
    print("=" * 80)

    best = {}
    for symbol in SYMBOLS:
        if symbol not in data:
            continue
        h4 = data[symbol]
        results = []
        for bars in [3, 4, 5, 6, 7]:
            for drop in [2.8, 3.0, 3.5]:
                for satr in [1.8, 2.0, 2.5]:
                    for sl in [0.25, 0.5, 0.8]:
                        for rr in [1.5, 2.0, 2.5, 3.0]:
                            for hold in [60, 9999]:
                                p = {"bars": bars, "drop": drop, "satr": satr,
                                     "sl": sl, "rr": rr, "hold": hold, "risk": 2.5}
                                tr = backtest(h4, symbol, p)
                                s = stats(pd.Series(tr))
                                if s["trades"] >= 10:
                                    results.append({**p, **s})
        if not results:
            print(f"\n{symbol}: 該当なし")
            continue
        df = pd.DataFrame(results).sort_values("pf", ascending=False)
        print(f"\n■ {symbol} — TOP5")
        print(f"  {'棚':>2} {'急落':>4} {'棚幅':>4} {'SL':>4} {'RR':>4} {'TIME':>5} | {'件数':>4} {'勝率':>6} {'PF':>6} {'R':>6} {'DD':>5}")
        for _, r in df.head(5).iterrows():
            tstr = "OFF" if r["hold"] == 9999 else str(int(r["hold"]))
            print(f"  {int(r['bars']):2} {r['drop']:4.1f} {r['satr']:4.1f} {r['sl']:4.2f} {r['rr']:4.1f} {tstr:>5} | "
                  f"{int(r['trades']):4} {r['win_rate']:5.1f}% {r['pf']:6.2f} {r['total_r']:6.1f} {r['max_dd_r']:5.1f}")
        b = df.iloc[0]
        best[symbol] = b

    print("\n" + "=" * 80)
    print("■ 各銘柄ベスト（正直版）")
    print("=" * 80)
    print(f"{'銘柄':<8} {'棚':>2} {'急落':>4} {'棚幅':>4} {'SL':>4} {'RR':>4} {'TIME':>5} {'PF':>6} {'件数':>4}")
    for symbol in SYMBOLS:
        if symbol in best:
            b = best[symbol]
            tstr = "OFF" if b["hold"] == 9999 else str(int(b["hold"]))
            print(f"{symbol:<8} {int(b['bars']):2} {b['drop']:4.1f} {b['satr']:4.1f} {b['sl']:4.2f} {b['rr']:4.1f} {tstr:>5} {b['pf']:6.2f} {int(b['trades']):4}")


if __name__ == "__main__":
    main()

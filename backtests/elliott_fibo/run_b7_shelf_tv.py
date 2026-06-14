#!/usr/bin/env python3
"""
B7棚（H4 V Shelf Breakout）— TradingViewデータ検証

急落否定後の棚ブレイク手法を tv_data/ の H4 CSV で8銘柄検証。
仕様: docs/research/H4_V字棚ブレイクアウト手法_2026-05-29.md
最良パラメータ: 棚7本 / 棚幅1.8ATR / RR1.5 / 実体0.30 / 終値位置0.50

使い方:
  python3 backtests/elliott_fibo/run_b7_shelf_tv.py           # 全銘柄
  python3 backtests/elliott_fibo/run_b7_shelf_tv.py USDJPY    # 銘柄指定
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
SYN_DIR = REPO_ROOT / "backtests" / "synapse_v2_definition_grid"
OUT_DIR = THIS_DIR / "results_tv_b7_shelf"
REPORT = REPO_ROOT / "docs" / "research" / "B7棚_TV検証_2026-06-14.md"

_s = importlib.util.spec_from_file_location("synapse_tv", SYN_DIR / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_s)
sys.modules["synapse_tv"] = tv
_s.loader.exec_module(tv)

RUN_START = pd.Timestamp("2015-01-01")
OOS_START = pd.Timestamp("2025-01-01")
ATR_PERIOD = 14

# B7棚パラメータ（深掘り検証の最良候補）
SHELF_BARS = 7
SHELF_RANGE_ATR = 1.8
SHELF_HOLD = 0.4       # 棚安値がV回復ラインの40%以上を維持
BREAK_BUF_ATR = 0.05
MIN_BODY = 0.30
MIN_CLOSE_LOC = 0.50
DROP_ATR_MIN = 2.8      # V急落の最小幅
RECOVERY_MIN = 0.65     # V回復率下限
RECOVERY_MAX = 1.25     # V回復率上限
STOP_BUF_ATR = 0.25
MAX_HOLD = 60           # スイング前提
RR_LIST = [1.5, 2.0]    # 両方試す
ADX_MAX = 26.0
RANGE60_MAX = 16.0

SYMBOL_ORDER = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "XAUUSD", "XAGUSD", "NAS100"]


def atr(high, low, close, period=14):
    pc = close.shift(1)
    tr = pd.concat([high - low, (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def add_features(raw):
    h4 = raw.copy()
    h4["atr"] = atr(h4["high"], h4["low"], h4["close"], ATR_PERIOD)
    rng = (h4["high"] - h4["low"]).replace(0.0, np.nan)
    h4["body_ratio"] = ((h4["close"] - h4["open"]).abs() / rng).fillna(0.0)
    h4["close_location"] = ((h4["close"] - h4["low"]) / rng).fillna(0.5)
    h4["ema20"] = h4["close"].ewm(span=20, adjust=False).mean()
    h4["ema50"] = h4["close"].ewm(span=50, adjust=False).mean()
    return h4


def find_v_shocks(h4):
    """confirmed pivot high → pivot low で急落を検出（先読みなし）"""
    highs = h4["high"].to_numpy()
    lows = h4["low"].to_numpy()
    atrs = h4["atr"].to_numpy()
    n = len(h4)
    width = 3
    pivots = []
    for i in range(width, n - width):
        a = atrs[i]
        if not math.isfinite(a) or a <= 0:
            continue
        hwin = highs[i - width:i + width + 1]
        lwin = lows[i - width:i + width + 1]
        is_high = highs[i] >= np.nanmax(hwin)
        is_low = lows[i] <= np.nanmin(lwin)
        if is_high and not is_low:
            pivots.append(("H", i, i + width, highs[i]))
        elif is_low and not is_high:
            pivots.append(("L", i, i + width, lows[i]))

    # H→L のペアで急落を検出
    shocks = []
    for j in range(1, len(pivots)):
        if pivots[j - 1][0] == "H" and pivots[j][0] == "L":
            hi_i, hi_conf = pivots[j - 1][1], pivots[j - 1][2]
            lo_i, lo_conf = pivots[j][1], pivots[j][2]
            hi_p, lo_p = pivots[j - 1][3], pivots[j][3]
            drop_bars = lo_i - hi_i
            if drop_bars < 2 or drop_bars > 24:
                continue
            a = atrs[lo_i]
            drop_atr = (hi_p - lo_p) / a if a > 0 else 0
            if drop_atr < DROP_ATR_MIN:
                continue
            shocks.append({
                "hi_i": hi_i, "lo_i": lo_i, "lo_conf": lo_conf,
                "hi_p": hi_p, "lo_p": lo_p,
                "drop_atr": drop_atr, "drop_bars": drop_bars,
            })
    return shocks


def scan_shelf_breakout(h4, symbol, rr):
    idx = h4.index
    o = h4["open"].to_numpy()
    hi = h4["high"].to_numpy()
    lo = h4["low"].to_numpy()
    cl = h4["close"].to_numpy()
    atrs = h4["atr"].to_numpy()
    body = h4["body_ratio"].to_numpy()
    cloc = h4["close_location"].to_numpy()
    ema20 = h4["ema20"].to_numpy()
    ema50 = h4["ema50"].to_numpy()
    n = len(h4)

    shocks = find_v_shocks(h4)
    spread, slip = tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))

    trades = []
    in_pos_until = -1

    for shock in shocks:
        lo_conf = shock["lo_conf"]
        hi_p, lo_p = shock["hi_p"], shock["lo_p"]
        drop = hi_p - lo_p

        # V回復を探す: lo_conf以降で、回復率65-125%の足
        for ri in range(lo_conf, min(n, lo_conf + 60)):
            recovery = (cl[ri] - lo_p) / drop if drop > 0 else 0
            if recovery < RECOVERY_MIN:
                continue
            if recovery > RECOVERY_MAX:
                break

            # 棚の開始点 = ri+1 から SHELF_BARS 本
            shelf_start = ri + 1
            shelf_end = shelf_start + SHELF_BARS
            if shelf_end >= n - 1:
                break

            a = atrs[shelf_end]
            if not math.isfinite(a) or a <= 0:
                continue

            shelf_hi = np.max(hi[shelf_start:shelf_end])
            shelf_lo = np.min(lo[shelf_start:shelf_end])
            shelf_range = (shelf_hi - shelf_lo) / a

            if shelf_range > SHELF_RANGE_ATR:
                continue

            # 棚安値がV回復ラインの一定%以上を維持
            recovery_line = lo_p + drop * SHELF_HOLD
            if shelf_lo < recovery_line:
                continue

            # ブレイク足の検出: shelf_end 以降で棚高値を終値で上抜け
            for bi in range(shelf_end, min(n - 1, shelf_end + 30)):
                ts = idx[bi]
                if ts < RUN_START:
                    continue
                if bi <= in_pos_until:
                    continue

                a_b = atrs[bi]
                if not math.isfinite(a_b) or a_b <= 0:
                    continue

                # 前足は棚高値以下、今足は棚高値を上抜け
                if cl[bi - 1] > shelf_hi:
                    break  # もう抜けている
                if cl[bi] <= shelf_hi + BREAK_BUF_ATR * a_b:
                    continue

                # 実体・終値位置チェック
                if body[bi] < MIN_BODY or cloc[bi] < MIN_CLOSE_LOC:
                    continue

                # SL / TP
                stop = shelf_lo - STOP_BUF_ATR * a_b
                entry_i = bi + 1
                if entry_i >= n:
                    break
                entry = o[entry_i]
                risk = entry - stop
                if risk <= 0:
                    break
                target = entry + risk * rr

                # リスク幅チェック
                risk_atr = risk / a_b
                if risk_atr > 2.5:
                    break

                # シミュレーション
                end_i = min(n - 1, entry_i + MAX_HOLD)
                exit_i, exit_price, reason = end_i, cl[end_i], "time"
                for j in range(entry_i, end_i + 1):
                    if lo[j] <= stop:
                        exit_i, exit_price, reason = j, stop, "stop"
                        break
                    if hi[j] >= target:
                        exit_i, exit_price, reason = j, target, "target"
                        break

                after = (exit_price - slip) - (entry + spread / 2.0)
                r_after = after / risk

                trades.append({
                    "symbol": symbol,
                    "signal_time": idx[bi],
                    "entry_time": idx[entry_i],
                    "exit_time": idx[exit_i],
                    "entry": entry,
                    "stop": stop,
                    "target": target,
                    "exit": exit_price,
                    "exit_reason": reason,
                    "r_after_cost": r_after,
                    "rr": rr,
                    "shelf_bars": SHELF_BARS,
                    "shelf_range_atr": shelf_range,
                    "drop_atr": shock["drop_atr"],
                    "risk_atr": risk_atr,
                    "is_oos": idx[entry_i] >= OOS_START,
                })
                in_pos_until = exit_i
                break  # このV shockからは1トレードのみ
            break  # 最初の回復点のみ

    return pd.DataFrame(trades)


def stats(r):
    if len(r) == 0:
        return dict(trades=0, win_rate=0.0, total_r=0.0, pf=float("nan"), max_dd_r=0.0)
    cum = r.cumsum().values
    dd = float((np.maximum.accumulate(cum) - cum).max())
    w, l = r[r > 0].sum(), -r[r <= 0].sum()
    pf = w / l if l > 0 else float("inf")
    return dict(trades=int(len(r)), win_rate=float((r > 0).mean() * 100),
                total_r=float(r.sum()), pf=float(pf), max_dd_r=dd)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    args = [a.upper() for a in sys.argv[1:]]
    files = sorted(tv.TV_DATA.glob("*.csv"))
    if args:
        files = [p for p in files if tv.detect_symbol(p) in args]

    all_trades = []
    results = {}
    for path in files:
        symbol = tv.detect_symbol(path)
        try:
            raw = tv.load_tv_csv(path)
        except Exception as e:
            print(f"[error] {path.name}: {e}")
            continue
        if len(raw) < 500:
            continue
        h4 = add_features(raw)

        for rr in RR_LIST:
            tr = scan_shelf_breakout(h4, symbol, rr)
            if tr.empty:
                results[(symbol, rr)] = stats(pd.Series([], dtype=float))
                continue
            all_trades.append(tr)
            s = stats(tr["r_after_cost"])
            oos = tr[tr["is_oos"]]["r_after_cost"]
            s["oos_trades"] = int(len(oos))
            s["oos_total_r"] = float(oos.sum())
            results[(symbol, rr)] = s

    if all_trades:
        pd.concat(all_trades, ignore_index=True).to_csv(OUT_DIR / "trades.csv", index=False)

    # レポート
    lines = [
        "# B7棚（H4 V Shelf Breakout）— TradingView H4 検証（2026-06-14）",
        "",
        "> `run_b7_shelf_tv.py` の出力。急落否定後の棚ブレイク手法を tv_data/ の H4 CSV で検証。",
        f"> 棚{SHELF_BARS}本 / 棚幅{SHELF_RANGE_ATR}ATR / 急落{DROP_ATR_MIN}ATR / 回復{RECOVERY_MIN}-{RECOVERY_MAX}",
        f"> ブレイク実体≥{MIN_BODY} / 終値位置≥{MIN_CLOSE_LOC} / TIME{MAX_HOLD}本",
        "",
        "## 銘柄別結果",
        "",
        "| 銘柄 | RR | 件数 | 勝率 | 合計R | PF | DD | OOS件数 | OOS R |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for sym in SYMBOL_ORDER:
        for rr in RR_LIST:
            s = results.get((sym, rr))
            if not s or s["trades"] == 0:
                lines.append(f"| {sym} | {rr} | 0 | - | - | - | - | - | - |")
                continue
            lines.append(
                f"| {sym} | {rr} | {s['trades']} | {s['win_rate']:.1f} | {s['total_r']:.2f} | "
                f"{s['pf']:.2f} | {s['max_dd_r']:.2f} | {s.get('oos_trades', 0)} | {s.get('oos_total_r', 0):.2f} |"
            )

    lines += ["", "## 出力", "", f"- `{OUT_DIR / 'trades.csv'}`"]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    # コンソール出力
    print("=== B7棚 銘柄別結果 ===")
    for sym in SYMBOL_ORDER:
        for rr in RR_LIST:
            s = results.get((sym, rr))
            if not s or s["trades"] == 0:
                continue
            print(f"{sym:8} RR{rr}  {s['trades']:3}件  勝率{s['win_rate']:5.1f}%  "
                  f"合計{s['total_r']:7.2f}R  PF{s['pf']:.2f}  DD{s['max_dd_r']:.2f}  "
                  f"OOS{s.get('oos_trades', 0)}件/{s.get('oos_total_r', 0):.2f}R")
    print(f"\n書き出し: {REPORT}")


if __name__ == "__main__":
    main()

"""
時間足比較バックテスト: H1 / H4 / D1
=====================================================================
目的:
  TrendBreakV1 Relaxed (現行ロジック) をH1で運用しているが、
  H4/D1に変更すべきか? 期待値・DD・連敗・PFで総合判断する。

方針:
  - H1データを resample してH4/D1を生成 (look-ahead bias なし)
  - ロジック・パラメータは現行 (RELAXED) を一切変更しない
  - 同一の現実コスト (spread/slippage) を適用
  - IS (2014-2020) / OOS (2021-2025) で過学習を確認
=====================================================================
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sai_backtest import load_instrument, atr
from trendbreak_backtest import (
    PRESETS_RELAXED, compute_signals, simulate, Trade, LOOKBACK_LONG,
    EXCLUDE_LONG, ATR_PERIOD,
)
from audit import SPREAD, SLIPPAGE


INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "CHFJPY", "AUDJPY"]
TIMEFRAMES = ["H1", "H4", "D1"]


# =====================================================================
# OHLCリサンプリング (look-ahead 完全排除)
# =====================================================================
def resample_ohlc(df_h1: pd.DataFrame, tf: str) -> pd.DataFrame:
    """
    H1 → H4 / D1 リサンプリング
    closed="left", label="left" でバーの「開始時刻」をindex、
    バーの確定は後続のバー時刻まで持ち越されないため、look-ahead は起きない。
    """
    if tf == "H1":
        return df_h1.copy()

    rule = {"H4": "4h", "D1": "1D"}[tf]
    res = df_h1.resample(rule, closed="left", label="left").agg({
        "open": "first",
        "high": "max",
        "low":  "min",
        "close": "last",
    }).dropna()
    return res


# =====================================================================
# 現実コスト込み simulate (audit.py と同じ方式)
# =====================================================================
def simulate_with_costs(name: str, sig: pd.DataFrame, cfg: dict) -> list[dict]:
    spread = SPREAD.get(name, 0.0)
    slip   = SLIPPAGE.get(name, 0.0)
    cost_in  = spread / 2 + slip
    cost_out = spread / 2 + slip

    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    ls = sig["long_sig"].to_numpy()
    ss = sig["short_sig"].to_numpy()
    idx = sig.index
    n = len(sig)

    trades = []
    in_pos_until = -1
    cooldown_until = -1

    for i in range(n - 1):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        if not (ls[i] or ss[i]):
            continue
        sa = a[i]
        if np.isnan(sa) or sa <= 0:
            continue
        is_long = bool(ls[i])
        eb = i + 1
        if eb >= n:
            break
        entry = o[eb] + (cost_in if is_long else -cost_in)
        sd = sa * cfg["sl_atr"]
        sl = entry - sd if is_long else entry + sd
        tp = entry + sd * cfg["tp_rr"] if is_long else entry - sd * cfg["tp_rr"]

        for j in range(eb, n):
            if is_long:
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp
            if hit_sl or hit_tp:
                # 同バー両方ヒットは SL優先 (保守的)
                if hit_sl:
                    ex = sl - cost_out if is_long else sl + cost_out
                else:
                    ex = tp - cost_out if is_long else tp + cost_out
                pnl = (ex - entry) if is_long else (entry - ex)
                trades.append({
                    "inst": name,
                    "entry_time": idx[i],
                    "exit_time":  idx[j],
                    "direction": "long" if is_long else "short",
                    "pnl_r": pnl / sd,
                    "bars_held": j - eb,
                })
                in_pos_until = j
                cooldown_until = j + cfg["cooldown"]
                break
    return trades


# =====================================================================
# メトリクス計算
# =====================================================================
def calc_metrics(trades_df: pd.DataFrame, tf: str) -> dict:
    if trades_df.empty:
        return {
            "trades": 0, "wins": 0, "wr": 0.0, "pf": np.nan,
            "expectancy": 0.0, "net_r": 0.0, "max_dd": 0.0,
            "max_loss_streak": 0, "max_win_streak": 0,
            "avg_hold_hours": 0.0, "median_hold_hours": 0.0,
            "max_consec_neg_months": 0, "pos_months_pct": 0.0,
        }

    df = trades_df.copy()
    # H1=1, H4=4, D1=24 (時間/bar)
    tf_hours = {"H1": 1, "H4": 4, "D1": 24}[tf]
    df["hold_hours"] = df["bars_held"] * tf_hours

    pnl = df["pnl_r"].to_numpy()
    wins = int((pnl > 0).sum())
    losses = int((pnl <= 0).sum())
    gross_win = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl <= 0].sum()
    pf = gross_win / gross_loss if gross_loss > 0 else np.inf
    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity).max() if len(equity) > 0 else 0.0

    # 連勝・連敗
    sw, sl_, cw, cl = 0, 0, 0, 0
    for r in pnl:
        if r > 0:
            cw += 1
            if cl > 0:
                sl_ = max(sl_, cl); cl = 0
        else:
            cl += 1
            if cw > 0:
                sw = max(sw, cw); cw = 0
    sw = max(sw, cw); sl_ = max(sl_, cl)

    # 月次
    df["ym"] = pd.to_datetime(df["entry_time"]).dt.to_period("M")
    monthly = df.groupby("ym")["pnl_r"].sum().sort_index()
    if len(monthly) > 0:
        pos_months_pct = (monthly > 0).mean() * 100
        consec_neg = 0; max_consec_neg = 0
        for v in monthly.values:
            if v < 0:
                consec_neg += 1
                max_consec_neg = max(max_consec_neg, consec_neg)
            else:
                consec_neg = 0
    else:
        pos_months_pct = 0.0
        max_consec_neg = 0

    return {
        "trades": len(df),
        "wins": wins,
        "wr": wins / len(df) * 100,
        "pf": float(pf),
        "expectancy": float(pnl.mean()),
        "net_r": float(pnl.sum()),
        "max_dd": float(dd),
        "max_loss_streak": int(sl_),
        "max_win_streak": int(sw),
        "avg_hold_hours": float(df["hold_hours"].mean()),
        "median_hold_hours": float(df["hold_hours"].median()),
        "max_consec_neg_months": int(max_consec_neg),
        "pos_months_pct": float(pos_months_pct),
    }


# =====================================================================
# 1通貨1時間足で実行
# =====================================================================
def run_single(name: str, tf: str, df_h1: pd.DataFrame, cfg: dict,
               year_from: int | None = None, year_to: int | None = None
               ) -> tuple[pd.DataFrame, dict]:
    df_tf = resample_ohlc(df_h1, tf)
    if year_from:
        df_tf = df_tf[df_tf.index.year >= year_from]
    if year_to:
        df_tf = df_tf[df_tf.index.year <= year_to]
    if len(df_tf) < 200:
        return pd.DataFrame(), calc_metrics(pd.DataFrame(), tf)

    sig = compute_signals(df_tf, cfg)
    trades = simulate_with_costs(name, sig, cfg)
    tdf = pd.DataFrame(trades)
    m = calc_metrics(tdf, tf)
    return tdf, m


# =====================================================================
# Pretty print helpers
# =====================================================================
def print_metric_row(name: str, m: dict, tf: str):
    pf_str = f"{m['pf']:>5.2f}" if not np.isinf(m['pf']) and not np.isnan(m['pf']) else "  inf"
    print(f"  {name:<10}  {tf:>3}  "
          f"trades={m['trades']:>4}  WR={m['wr']:>5.1f}%  PF={pf_str}  "
          f"Exp={m['expectancy']:>+5.2f}R  Net={m['net_r']:>+7.1f}R  "
          f"DD={m['max_dd']:>5.1f}R  MaxL={m['max_loss_streak']:>3}  "
          f"Hold={m['avg_hold_hours']:>6.1f}h  "
          f"Pos月={m['pos_months_pct']:>5.1f}%  連赤月={m['max_consec_neg_months']:>2}")


# =====================================================================
# Main
# =====================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+", default=INSTRUMENTS)
    ap.add_argument("--year-from", type=int, default=2015)
    ap.add_argument("--year-to", type=int, default=2025)
    ap.add_argument("--no-oos", action="store_true",
                    help="IS/OOS分割せず通期で実行")
    args = ap.parse_args()

    print("=" * 130)
    print(f"【時間足比較バックテスト】 TrendBreakV1 Relaxed (ロジック・パラメータ固定)")
    print(f"  対象: {', '.join(args.instruments)}")
    print(f"  期間: {args.year_from}-{args.year_to}")
    print(f"  時間足: H1 / H4 / D1 (H1データから resample)")
    print(f"  現実コスト: spread+slippage 込み")
    print("=" * 130)

    # ロード
    h1_data = {}
    for name in args.instruments:
        try:
            h1_data[name] = load_instrument(name)
            print(f"  [OK]  {name}: {len(h1_data[name])} H1 bars")
        except Exception as e:
            print(f"  [SKIP] {name}: {e}")

    # =====================================================
    # PHASE 1: 通期 (全期間) ヘッドライン比較
    # =====================================================
    print("\n" + "=" * 130)
    print("【PHASE 1】 通期ヘッドライン (通貨×時間足 × 同一パラメータ)")
    print("=" * 130)

    all_results = {}  # (name, tf) -> metrics
    all_trades  = {}  # (name, tf) -> trades_df

    for tf in TIMEFRAMES:
        print(f"\n--- {tf} ---")
        for name in args.instruments:
            if name not in h1_data:
                continue
            cfg = PRESETS_RELAXED[name]
            tdf, m = run_single(name, tf, h1_data[name], cfg,
                                args.year_from, args.year_to)
            all_results[(name, tf)] = m
            all_trades[(name, tf)] = tdf
            print_metric_row(name, m, tf)

    # =====================================================
    # PHASE 2: 時間足ごとの合計 (通貨横断)
    # =====================================================
    print("\n" + "=" * 130)
    print("【PHASE 2】 時間足ごとの合計 (通貨横断)")
    print("=" * 130)
    print(f"  {'TF':<4}  {'trades':>6}  {'WR%':>5}  {'PF':>5}  {'Exp':>6}  {'Net R':>7}  {'DD':>5}  {'MaxL':>4}")
    tf_totals = {}
    for tf in TIMEFRAMES:
        rows = [v for (n, t), v in all_results.items() if t == tf]
        trades_all = pd.concat([all_trades[(n, tf)] for n in args.instruments
                                 if (n, tf) in all_trades and not all_trades[(n, tf)].empty],
                                ignore_index=True) if any(
            (n, tf) in all_trades and not all_trades[(n, tf)].empty
            for n in args.instruments
        ) else pd.DataFrame()
        m = calc_metrics(trades_all, tf)
        tf_totals[tf] = m
        pf_str = f"{m['pf']:>5.2f}" if not np.isinf(m['pf']) else "  inf"
        print(f"  {tf:<4}  {m['trades']:>6}  {m['wr']:>4.1f}%  {pf_str}  "
              f"{m['expectancy']:>+5.2f}  {m['net_r']:>+7.1f}  "
              f"{m['max_dd']:>5.1f}  {m['max_loss_streak']:>4}")

    # =====================================================
    # PHASE 3: 通貨別 「最良時間足」ランキング
    # =====================================================
    print("\n" + "=" * 130)
    print("【PHASE 3】 通貨別 最良時間足ランキング (期待値R / Net R で評価)")
    print("=" * 130)
    print(f"  {'通貨':<8}  {'勝者':<5}  {'Net比較 (H1 / H4 / D1)':<35}  {'Exp比較':<28}  {'DD比較':<28}")
    best_by_inst = {}
    for name in args.instruments:
        nets = {tf: all_results[(name, tf)]["net_r"] for tf in TIMEFRAMES if (name, tf) in all_results}
        if not nets:
            continue
        # 期待値とNet両方で評価。シグナル極端少 (<20) は除外
        valid = {tf: v for tf, v in nets.items() if all_results[(name, tf)]["trades"] >= 20}
        if not valid:
            best_tf = max(nets, key=nets.get)
        else:
            best_tf = max(valid, key=valid.get)
        best_by_inst[name] = best_tf

        nets_s = " / ".join(f"{tf}:{all_results[(name,tf)]['net_r']:+6.1f}R" for tf in TIMEFRAMES)
        exps_s = " / ".join(f"{tf}:{all_results[(name,tf)]['expectancy']:+.2f}" for tf in TIMEFRAMES)
        dds_s  = " / ".join(f"{tf}:{all_results[(name,tf)]['max_dd']:.1f}" for tf in TIMEFRAMES)
        print(f"  {name:<8}  {best_tf:<5}  {nets_s:<35}  {exps_s:<28}  {dds_s:<28}")

    print(f"\n  通貨別の最良: {best_by_inst}")

    # =====================================================
    # PHASE 4: IS / OOS 分割
    # =====================================================
    if not args.no_oos:
        print("\n" + "=" * 130)
        print("【PHASE 4】 IS (2015-2020) / OOS (2021-2025) 分割 (過学習チェック)")
        print("=" * 130)
        for tf in TIMEFRAMES:
            print(f"\n--- {tf} ---")
            print(f"  {'通貨':<8}  {'IS Net':>9}  {'IS WR':>6}  {'IS Exp':>7}  "
                  f"{'OOS Net':>9}  {'OOS WR':>7}  {'OOS Exp':>7}  {'判定':<10}")
            for name in args.instruments:
                if name not in h1_data:
                    continue
                cfg = PRESETS_RELAXED[name]
                _, mi = run_single(name, tf, h1_data[name], cfg, 2015, 2020)
                _, mo = run_single(name, tf, h1_data[name], cfg, 2021, 2025)
                ratio = mo["expectancy"] / mi["expectancy"] if mi["expectancy"] > 0.05 else 0
                if mi["trades"] < 10 or mo["trades"] < 5:
                    judge = "サンプル少"
                elif mi["expectancy"] > 0 and mo["expectancy"] > 0:
                    judge = "✅ 両期安定" if 0.5 <= ratio <= 2.0 else "△ ばらつき"
                elif mi["expectancy"] > 0 >= mo["expectancy"]:
                    judge = "⚠️ OOS劣化"
                elif mi["expectancy"] <= 0 < mo["expectancy"]:
                    judge = "△ ISは負け"
                else:
                    judge = "❌ 両期負け"
                print(f"  {name:<8}  {mi['net_r']:>+8.1f}R  {mi['wr']:>5.1f}%  "
                      f"{mi['expectancy']:>+6.2f}R  "
                      f"{mo['net_r']:>+8.1f}R  {mo['wr']:>6.1f}%  "
                      f"{mo['expectancy']:>+6.2f}R  {judge:<10}")

    # =====================================================
    # PHASE 5: 月次・年次成績 (採用候補のみ詳細出力)
    # =====================================================
    print("\n" + "=" * 130)
    print("【PHASE 5】 時間足合計の年次推移")
    print("=" * 130)
    for tf in TIMEFRAMES:
        print(f"\n--- {tf} ---")
        all_t = pd.concat([all_trades[(n, tf)] for n in args.instruments
                           if (n, tf) in all_trades and not all_trades[(n, tf)].empty],
                          ignore_index=True) if any(
            (n, tf) in all_trades and not all_trades[(n, tf)].empty
            for n in args.instruments
        ) else pd.DataFrame()
        if all_t.empty:
            print("  (no trades)")
            continue
        all_t["year"] = pd.to_datetime(all_t["entry_time"]).dt.year
        yearly = all_t.groupby("year").agg(
            n=("pnl_r", "count"),
            wr=("pnl_r", lambda s: (s > 0).mean() * 100),
            exp=("pnl_r", "mean"),
            net=("pnl_r", "sum"),
        )
        for y, row in yearly.iterrows():
            sig = "⚠️" if row["exp"] <= 0 else "  "
            print(f"  {y}  n={int(row['n']):>4}  WR={row['wr']:>5.1f}%  "
                  f"Exp={row['exp']:>+.3f}R  Net={row['net']:>+7.1f}R  {sig}")

    # =====================================================
    # PHASE 6: 結論
    # =====================================================
    print("\n" + "=" * 130)
    print("【結論】")
    print("=" * 130)
    h1m = tf_totals["H1"]; h4m = tf_totals["H4"]; d1m = tf_totals["D1"]
    print(f"  時間足   Trades  PF    Exp     Net R   DD")
    print(f"  H1     {h1m['trades']:>6}  {h1m['pf']:>4.2f}  {h1m['expectancy']:>+.2f}R  "
          f"{h1m['net_r']:>+6.1f}R  {h1m['max_dd']:>5.1f}R")
    print(f"  H4     {h4m['trades']:>6}  {h4m['pf']:>4.2f}  {h4m['expectancy']:>+.2f}R  "
          f"{h4m['net_r']:>+6.1f}R  {h4m['max_dd']:>5.1f}R")
    print(f"  D1     {d1m['trades']:>6}  {d1m['pf']:>4.2f}  {d1m['expectancy']:>+.2f}R  "
          f"{d1m['net_r']:>+6.1f}R  {d1m['max_dd']:>5.1f}R")

    # H1 vs H4/D1 のNet・期待値・DD比較
    print(f"\n  ヘッドライン:")
    winner_tf = max(["H1", "H4", "D1"], key=lambda t: tf_totals[t]["net_r"])
    winner_exp = max(["H1", "H4", "D1"], key=lambda t: tf_totals[t]["expectancy"])
    winner_dd  = min(["H1", "H4", "D1"], key=lambda t: tf_totals[t]["max_dd"])
    print(f"    総損益R最大: {winner_tf}")
    print(f"    期待値R最大: {winner_exp}")
    print(f"    最大DD最小 : {winner_dd}")


if __name__ == "__main__":
    main()

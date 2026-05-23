"""
時間足比較バックテスト (時間ベース等価lookback版)
=====================================================================
PHASE A の as-is 比較ではH4/D1のシグナル数が極端に減少していた。
本スクリプトは lookback / exclude を「時間ベースで同等」に
スケーリングし、フェアな比較を行う。

  H1: lookback=180   (=180時間=7.5日)
  H4: lookback=45    (=180時間=7.5日)
  D1: lookback=8     (=192時間=8日)
=====================================================================
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd

from sai_backtest import load_instrument
from trendbreak_backtest import PRESETS_RELAXED, compute_signals
from timeframe_compare import (
    INSTRUMENTS, TIMEFRAMES, resample_ohlc, simulate_with_costs,
    calc_metrics, print_metric_row,
)


def scale_cfg(cfg: dict, tf: str) -> dict:
    """lookback / exclude / cooldown を時間ベースで等価にスケール"""
    if tf == "H1":
        return cfg
    factor = {"H4": 4, "D1": 24}[tf]
    scaled = dict(cfg)
    scaled["lookback_3m"] = max(int(round(cfg["lookback_3m"] / factor)), 5)
    scaled["exclude"]     = max(int(round(cfg["exclude"]     / factor)), 1)
    scaled["cooldown"]    = max(int(round(cfg["cooldown"]    / factor)), 0)
    return scaled


def run_single(name: str, tf: str, df_h1: pd.DataFrame, cfg: dict,
               year_from=None, year_to=None):
    df_tf = resample_ohlc(df_h1, tf)
    if year_from: df_tf = df_tf[df_tf.index.year >= year_from]
    if year_to:   df_tf = df_tf[df_tf.index.year <= year_to]
    if len(df_tf) < 50:
        return pd.DataFrame(), calc_metrics(pd.DataFrame(), tf)
    sig = compute_signals(df_tf, cfg)
    trades = simulate_with_costs(name, sig, cfg)
    tdf = pd.DataFrame(trades)
    return tdf, calc_metrics(tdf, tf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year-from", type=int, default=2015)
    ap.add_argument("--year-to",   type=int, default=2025)
    args = ap.parse_args()

    print("=" * 130)
    print("【時間足比較 ADJUSTED】 H4/D1 は lookback を時間ベースで等価スケーリング")
    print(f"  期間: {args.year_from}-{args.year_to}")
    print("=" * 130)

    h1_data = {}
    for name in INSTRUMENTS:
        try:
            h1_data[name] = load_instrument(name)
        except Exception as e:
            print(f"  [SKIP] {name}: {e}")

    all_results = {}
    all_trades  = {}

    for tf in TIMEFRAMES:
        print(f"\n--- {tf} (時間等価スケーリング適用) ---")
        for name, df_h1 in h1_data.items():
            cfg = scale_cfg(PRESETS_RELAXED[name], tf)
            tdf, m = run_single(name, tf, df_h1, cfg, args.year_from, args.year_to)
            all_results[(name, tf)] = m
            all_trades[(name, tf)]  = tdf
            print_metric_row(name, m, tf)
            scaled_info = f"   [scaled: lb={cfg['lookback_3m']}, exc={cfg['exclude']}, cd={cfg['cooldown']}]"
            print(scaled_info)

    # 合計
    print("\n" + "=" * 130)
    print("【合計 (通貨横断)】 - 時間等価lookback版")
    print("=" * 130)
    print(f"  {'TF':<4}  {'trades':>6}  {'WR%':>5}  {'PF':>5}  {'Exp':>6}  {'Net R':>7}  {'DD':>5}  {'MaxL':>4}")
    tf_totals = {}
    for tf in TIMEFRAMES:
        trades_all = pd.concat([all_trades[(n, tf)] for n in INSTRUMENTS
                                if (n, tf) in all_trades and not all_trades[(n, tf)].empty],
                               ignore_index=True) if any(
            (n, tf) in all_trades and not all_trades[(n, tf)].empty for n in INSTRUMENTS
        ) else pd.DataFrame()
        m = calc_metrics(trades_all, tf)
        tf_totals[tf] = m
        pf_str = f"{m['pf']:>5.2f}" if not np.isinf(m['pf']) else "  inf"
        print(f"  {tf:<4}  {m['trades']:>6}  {m['wr']:>4.1f}%  {pf_str}  "
              f"{m['expectancy']:>+5.2f}  {m['net_r']:>+7.1f}  "
              f"{m['max_dd']:>5.1f}  {m['max_loss_streak']:>4}")

    # IS/OOS
    print("\n" + "=" * 130)
    print("【IS (2015-2020) / OOS (2021-2025) 分割 - 時間等価lookback版】")
    print("=" * 130)
    for tf in TIMEFRAMES:
        print(f"\n--- {tf} ---")
        print(f"  {'通貨':<8}  {'IS Net':>9}  {'IS WR':>6}  {'IS Exp':>7}  "
              f"{'OOS Net':>9}  {'OOS WR':>7}  {'OOS Exp':>7}  {'判定':<10}")
        for name, df_h1 in h1_data.items():
            cfg = scale_cfg(PRESETS_RELAXED[name], tf)
            _, mi = run_single(name, tf, df_h1, cfg, 2015, 2020)
            _, mo = run_single(name, tf, df_h1, cfg, 2021, 2025)
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


if __name__ == "__main__":
    main()

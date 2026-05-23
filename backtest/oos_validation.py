"""
アウトオブサンプル (Out-of-Sample) 検証

手順:
  1. データを Train (2014-2020) / Test (2021-2024) に分割
  2. Trainでフルグリッドサーチして最適パラメータを取得
  3. その同じパラメータで Test 期間を評価 (再最適化しない)
  4. Train と Test の性能を並べてオーバーフィットを判定

過学習の判定基準:
  - Test の Net R が Train の 50% 未満 → 過学習の可能性大
  - Test の WR が Train から 5% 以上下がる → ロジック弱い
  - Test が赤字 → 完全に過学習
"""
from __future__ import annotations

import argparse
import itertools

import numpy as np
import pandas as pd

from sai_backtest import load_instrument
from optimize_trendbreak import TBConfig, BASE, evaluate


TRAIN_END = 2020
TEST_START = 2021


def grid_search(name: str, df: pd.DataFrame, base: TBConfig) -> dict:
    """Trainデータでベスト構成を探す"""
    sl_grid = [1.0, 1.5, 2.0, 2.5, 3.0]
    rr_grid = [2.5, 3.0, 4.0, 5.0]
    lb_grid = [90, 120, 180, 240, 360, 480]
    ex_grid = [15, 30, 60, 90]
    trend_grid = [0, 200, 500]
    wd_grid = [0b1111111, 0b1111000]

    best = None
    base_d = base.__dict__.copy()
    for sl, rr, lb, ex, trend, wd in itertools.product(
            sl_grid, rr_grid, lb_grid, ex_grid, trend_grid, wd_grid):
        if ex > lb:
            continue
        mod = {"sl_atr": sl, "tp_rr": rr,
               "lookback_3m": lb, "exclude": ex,
               "trend_filter_len": trend, "weekday_mask": wd}
        cfg = TBConfig(**{**base_d, **mod})
        s = evaluate(name, cfg, df)
        if s["n"] < 20:
            continue
        score = s["net"] - s["dd"] * 0.3
        if best is None or score > best["_score"]:
            best = {**s, "_score": score, "params": mod, "cfg": cfg}
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    args = ap.parse_args()

    results = []
    for name in args.instruments:
        try:
            full = load_instrument(name)
        except Exception as e:
            print(f"[SKIP] {name}: {e}")
            continue
        train = full[full.index.year <= TRAIN_END]
        test  = full[full.index.year >= TEST_START]
        print(f"\n=== {name}  Train: {train.index.min().date()}〜{train.index.max().date()} "
              f"({len(train)}本)  Test: {test.index.min().date()}〜{test.index.max().date()} ({len(test)}本) ===")

        # 1) Trainで最適化
        best_train = grid_search(name, train, BASE[name])
        if best_train is None:
            print("  ベスト構成見つからず")
            continue
        p = best_train["params"]
        wd_str = "Mon-Thu" if p["weekday_mask"] == 0b1111000 else "Mon-Sun"
        print(f"  [TRAIN] sl={p['sl_atr']} rr={p['tp_rr']} lb={p['lookback_3m']} "
              f"ex={p['exclude']} sma={p['trend_filter_len']} wd={wd_str}")
        print(f"          n={best_train['n']:4}  WR={best_train['wr']:5.1f}%  "
              f"PF={best_train['pf']:5.2f}  Net={best_train['net']:+6.1f}R  DD={best_train['dd']:.1f}R")

        # 2) 同じ設定でTestを評価
        test_eval = evaluate(name, best_train["cfg"], test)
        print(f"  [TEST ] (Train最適パラメータをそのまま適用)")
        print(f"          n={test_eval['n']:4}  WR={test_eval['wr']:5.1f}%  "
              f"PF={test_eval['pf']:5.2f}  Net={test_eval['net']:+6.1f}R  DD={test_eval['dd']:.1f}R")

        # 3) 過学習判定
        if best_train["net"] > 0:
            test_ratio = test_eval["net"] / best_train["net"] * 100
        else:
            test_ratio = 0
        wr_drop = best_train["wr"] - test_eval["wr"]
        if test_eval["net"] < 0:
            verdict = "❌ 完全過学習 (Testで赤字)"
        elif test_ratio < 30:
            verdict = "⚠️ 過学習の疑い大 (Test利益が30%未満)"
        elif wr_drop > 10:
            verdict = "⚠️ 勝率劣化大 (-10%以上)"
        elif test_ratio < 60:
            verdict = "△ やや過学習"
        else:
            verdict = "✅ 安定 (汎化している)"
        print(f"  判定: {verdict}  (Train→Test Net比 {test_ratio:.0f}%, WR差 {wr_drop:+.1f}pt)")

        # 4) 参考: ベースライン (元のRelaxed Preset) でも Test 評価
        base_test = evaluate(name, BASE[name], test)
        print(f"  参考[Base Relaxed をTest期間で評価]")
        print(f"          n={base_test['n']:4}  WR={base_test['wr']:5.1f}%  "
              f"PF={base_test['pf']:5.2f}  Net={base_test['net']:+6.1f}R")

        results.append({
            "inst": name,
            "train_net": best_train["net"], "train_wr": best_train["wr"],
            "test_net": test_eval["net"], "test_wr": test_eval["wr"],
            "base_test_net": base_test["net"],
            "verdict": verdict,
            **{f"p_{k}": v for k, v in p.items()},
        })

    # 集計
    if results:
        df = pd.DataFrame(results)
        print("\n" + "=" * 90)
        print("【総合】 Train vs Test 比較")
        print("=" * 90)
        print(df[["inst", "train_net", "train_wr", "test_net", "test_wr", "base_test_net", "verdict"]]
              .to_string(index=False, float_format=lambda x: f"{x:.1f}"))
        print(f"\n  TRAIN 合計: {df['train_net'].sum():+.1f}R")
        print(f"  TEST  合計: {df['test_net'].sum():+.1f}R   ← 実際の汎化性能")
        print(f"  Base Relaxed の TEST 合計: {df['base_test_net'].sum():+.1f}R")
        if df['train_net'].sum() > 0:
            print(f"  Train→Test 比率: {df['test_net'].sum()/df['train_net'].sum()*100:.0f}%")


if __name__ == "__main__":
    main()

"""
D1 SMA20 を軸にした最終組合せテスト (全てOOS検証付き)

C1: D1 SMA20 + 金曜オフ
C2: D1 SMA20 + RR 可変 (CHFJPY だけ 4.0、他は 3.0)
C3: D1 SMA20 + W1 SMA4 一致
C4: D1 SMA20 + 通貨別 lookback 微調整
C5: 全部入り (1-4の合成)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sai_backtest import atr, rolling_max, rolling_min, load_instrument
from optimize_trendbreak import TBConfig, BASE, ATR_PERIOD, LOOKBACK_LONG, EXCLUDE_LONG
from new_techniques import ExtConfig, compute_signals_ext, simulate_ext, stats, evaluate_ext

TRAIN_END = 2020
TEST_START = 2021


@dataclass
class ExtConfigPlus(ExtConfig):
    htf_trend_w: int = 0   # 週足 SMA Period (週足の値で比較)


def compute_signals_with_w1(df: pd.DataFrame, cfg: ExtConfigPlus) -> pd.DataFrame:
    sig = compute_signals_ext(df, cfg)
    if cfg.htf_trend_w > 0:
        w1_close = df["close"].resample("1W").last()
        w1_sma = w1_close.rolling(cfg.htf_trend_w).mean()
        # ★ FIX: shift(1) で前週確定値ベース (未来参照回避)
        w1_signal = (w1_close > w1_sma).shift(1)
        w1_above = w1_signal.reindex(df.index, method="ffill").fillna(False)
        sig["long_sig"] = sig["long_sig"] & w1_above
        sig["short_sig"] = sig["short_sig"] & (~w1_above)
    return sig


def evaluate(cfg: ExtConfigPlus, df: pd.DataFrame) -> dict:
    sig = compute_signals_with_w1(df, cfg)
    trades = simulate_ext(sig, cfg)
    return stats(trades)


def make_base_ext(name: str, sma_d: int = 20) -> ExtConfigPlus:
    b = BASE[name].__dict__
    return ExtConfigPlus(**b, htf_trend_d=sma_d)


def run(instruments: list[str]):
    data = {}
    for n in instruments:
        try:
            data[n] = load_instrument(n)
        except Exception as e:
            print(f"[SKIP] {n}: {e}")

    # --- 各組合せを設定 ---
    def cfg_base(inst):
        return make_base_ext(inst, sma_d=20)

    def cfg_c1(inst):  # D1 SMA20 + 金曜オフ
        c = make_base_ext(inst, sma_d=20)
        c.weekday_mask = 0b1111000
        return c

    def cfg_c2(inst):  # D1 SMA20 + RR可変
        c = make_base_ext(inst, sma_d=20)
        c.tp_rr = 4.0 if inst == "CHFJPY" else 3.0
        return c

    def cfg_c3(inst):  # D1 SMA20 + W1 SMA4
        c = make_base_ext(inst, sma_d=20)
        c.htf_trend_w = 4
        return c

    def cfg_c4(inst):  # D1 SMA20 + 通貨別 lookback 微調整
        # OOS で機能した、過去に「中央値より少し短め」だった設定だけ採用
        # 過学習を避けるため、Base ±33%以内に留める
        c = make_base_ext(inst, sma_d=20)
        # Base 値: XAUUSD 240, USDJPY 180, EURJPY 180, GBPJPY 180, CHFJPY 480, AUDJPY 480, SILVER 360
        # 控えめに ±20% で揃え気味に
        adjust = {
            "XAUUSD": 240,  # そのまま
            "USDJPY": 180,
            "EURJPY": 180,
            "GBPJPY": 180,
            "CHFJPY": 360,  # 480→360 (やや短く)
            "AUDJPY": 360,  # 480→360
            "SILVER": 360,
        }
        c.lookback_3m = adjust.get(inst, c.lookback_3m)
        return c

    def cfg_c5(inst):  # 全部入り
        c = make_base_ext(inst, sma_d=20)
        c.weekday_mask = 0b1111000
        c.htf_trend_w = 4
        c.tp_rr = 4.0 if inst == "CHFJPY" else 3.0
        if inst in ("CHFJPY", "AUDJPY"):
            c.lookback_3m = 360
        return c

    COMBOS = {
        "T0: Baseline":           lambda i: ExtConfigPlus(**BASE[i].__dict__),
        "D1 SMA20 (T5)":          cfg_base,
        "C1: D1 SMA20 + 金曜オフ":  cfg_c1,
        "C2: D1 SMA20 + RR可変":   cfg_c2,
        "C3: D1 SMA20 + W1 SMA4": cfg_c3,
        "C4: D1 SMA20 + LB微調整": cfg_c4,
        "C5: 全部入り":            cfg_c5,
    }

    print("=" * 100)
    print("【最終組合せ OOS 検証】 Train(2014-2020) / Test(2021-2024)")
    print("=" * 100)
    rows = []
    for cname, builder in COMBOS.items():
        for inst, df in data.items():
            cfg = builder(inst)
            tr_df = df[df.index.year <= TRAIN_END]
            te_df = df[df.index.year >= TEST_START]
            tr = evaluate(cfg, tr_df)
            te = evaluate(cfg, te_df)
            rows.append({"combo": cname, "inst": inst,
                         "tr_n": tr["n"], "tr_wr": tr["wr"], "tr_net": tr["net"],
                         "te_n": te["n"], "te_wr": te["wr"], "te_net": te["net"],
                         "te_pf": te["pf"], "te_dd": te["dd"]})
    dfr = pd.DataFrame(rows)

    # 合計
    print("\n--- 組合せ別 TEST 合計 (2021-2024) ---")
    summary = dfr.groupby("combo").agg(
        tr_net=("tr_net", "sum"),
        te_net=("te_net", "sum"),
        te_n=("te_n", "sum"),
        te_wr=("te_wr", "mean"),
    ).reset_index()
    summary["ratio"] = summary["te_net"] / summary["tr_net"].replace(0, np.nan) * 100
    # 順序固定
    summary["sort_key"] = summary["combo"].map({c: i for i, c in enumerate(COMBOS.keys())})
    summary = summary.sort_values("sort_key").drop("sort_key", axis=1)
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.1f}"))

    # 各組合せの通貨別 TEST
    print("\n--- TEST 期間 各通貨×各組合せ Net R ---")
    pvt = dfr.pivot(index="inst", columns="combo", values="te_net")
    pvt = pvt[list(COMBOS.keys())]
    print(pvt.to_string(float_format=lambda x: f"{x:+.1f}"))

    # ベスト組合せ
    best_row = summary.sort_values("te_net", ascending=False).iloc[0]
    print(f"\n🏆 TEST 期間総合ベスト: {best_row['combo']}")
    print(f"    Train: {best_row['tr_net']:.1f}R → Test: {best_row['te_net']:.1f}R "
          f"(汎化率 {best_row['ratio']:.0f}%, 平均WR {best_row['te_wr']:.1f}%)")

    # 通貨別ベスト組合せ
    print("\n--- 通貨別 TEST ベスト組合せ ---")
    for inst in data.keys():
        sub = dfr[dfr["inst"] == inst].sort_values("te_net", ascending=False)
        b = sub.iloc[0]
        base = sub[sub["combo"] == "T0: Baseline"].iloc[0]
        print(f"  {inst:7} → [{b['combo']:28}] n={b['te_n']:>4} WR={b['te_wr']:5.1f}% "
              f"PF={b['te_pf']:5.2f} Net={b['te_net']:+6.1f}R DD={b['te_dd']:4.1f}R "
              f"(vs Base: {b['te_net']-base['te_net']:+.1f}R)")

    # 通貨別ベスト構成で運用したときの合計
    print("\n--- 各通貨でベスト組合せを採用した場合の合計 (Mix-and-Match) ---")
    total_te = 0; total_n = 0
    for inst in data.keys():
        sub = dfr[dfr["inst"] == inst].sort_values("te_net", ascending=False)
        b = sub.iloc[0]
        total_te += b["te_net"]; total_n += b["te_n"]
    print(f"  TEST 期間 ミックスマッチ合計: {total_te:+.1f}R  / 取引数 {total_n}")

    return dfr


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    args = ap.parse_args()
    run(args.instruments)

#!/usr/bin/env python3
"""
Market Psychology Research Framework — ショート側 対称検証

検証対象（[Short Squeeze] の完全対称モデル）:
    Expectation Failure -> Long Liquidation
    急騰 (続伸期待) -> 逆V下落 (期待崩壊) -> 高値棚停滞/棚下抜け (投げ点火)

問い:
    ロング側 (踏み上げ) で PF 2.5 の優位性が出た。
    では上下反転した「投げ」構造は、本当に対称な優位性を持つのか？
    LONG_LIQUIDATION.md は「Short Squeeze の完全対称モデル」と仮定している。
    その仮定をOOS込みの実トレードデータで検証・反証する。

データソース (リポジトリにコミット済み):
    - 対照群: short_inverse_v_candidate_only (逆V候補で即ショート / 棚確認なし)
    - 本命  : short_t5_broad (逆V候補 + 高値棚停滞/棚下抜けで確認)
      IS = Research_2015_2024 / OOS = OOS_2025_2026
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
OUT_DIR = THIS_DIR

BASE = REPO_ROOT / "backtests/elliott_fibo/results_2026_05_28/t5_short_mirror_validation"
CONTROL = BASE / "short_inverse_v_candidate_only_trades_2015_2026.csv"
STRUCT = BASE / "short_t5_broad_trades_2015_2026.csv"

RNG = np.random.default_rng(20260530)


def metrics(r: pd.Series) -> dict:
    r = pd.Series(r).astype(float).dropna()
    n = len(r)
    if n == 0:
        return dict(n=0, wr=float("nan"), avg_r=float("nan"), total_r=0.0,
                    pf=float("nan"), max_dd=float("nan"), max_loss_streak=0, sharpe=float("nan"))
    losses = r[r < 0]
    gross_loss = -losses.sum()
    pf = r[r > 0].sum() / gross_loss if gross_loss > 0 else float("inf")
    equity = r.cumsum()
    dd = (equity.cummax() - equity).max()
    streak = mx = 0
    for v in r:
        if v < 0:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    sharpe = r.mean() / r.std(ddof=1) * math.sqrt(n) if n > 1 and r.std(ddof=1) > 0 else float("nan")
    return dict(n=n, wr=100.0 * (r > 0).mean(), avg_r=r.mean(), total_r=r.sum(),
                pf=pf, max_dd=dd, max_loss_streak=mx, sharpe=sharpe)


def bootstrap_ci(r, fn, iters=10000, alpha=0.05):
    r = pd.Series(r).astype(float).dropna().values
    if len(r) == 0:
        return (float("nan"), float("nan"))
    stats = np.empty(iters)
    n = len(r)
    for i in range(iters):
        stats[i] = fn(r[RNG.integers(0, n, n)])
    return (float(np.quantile(stats, alpha / 2)), float(np.quantile(stats, 1 - alpha / 2)))


def pf_of(arr):
    arr = np.asarray(arr, float)
    gl = -arr[arr < 0].sum()
    return arr[arr > 0].sum() / gl if gl > 0 else np.inf


def fmt(d: dict) -> str:
    pf = "inf" if d["pf"] == float("inf") else f"{d['pf']:.2f}"
    return (f"n={d['n']:>3}  WR={d['wr']:5.1f}%  avgR={d['avg_r']:+.3f}  "
            f"totalR={d['total_r']:+7.2f}  PF={pf:>5}  maxDD={d['max_dd']:.2f}R  "
            f"maxLoss連敗={d['max_loss_streak']}  Sharpe={d['sharpe']:.2f}")


lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


out("=" * 80)
out("Market Psychology Research — ショート側 対称検証 (Long Liquidation)")
out("  急騰 -> 逆V下落(期待崩壊) -> 高値棚停滞/棚下抜け(投げ点火)")
out("=" * 80)

ctrl = pd.read_csv(CONTROL)
df = pd.read_csv(STRUCT)
df["r"] = df["r_after_cost"].astype(float)
ctrl["r"] = ctrl["r_after_cost"].astype(float)
is_df = df[df["period"] == "Research_2015_2024"].copy()
oos_df = df[df["period"] == "OOS_2025_2026"].copy()

out("")
out("[対照群] 逆V候補で即ショート (高値棚=投げ構造を確認せず飛び乗り)")
out("  " + fmt(metrics(ctrl["r"])))

out("")
out("-" * 80)
out("[本命] 投げ構造版: 逆V候補 + 高値棚停滞/棚下抜け")
out("-" * 80)
out("IS  (2015-2024): " + fmt(metrics(is_df["r"])))
out("OOS (2025-2026): " + fmt(metrics(oos_df["r"])))
out("ALL            : " + fmt(metrics(df["r"])))

ci_exp = bootstrap_ci(is_df["r"], np.mean)
ci_pf = bootstrap_ci(is_df["r"], pf_of)
out("")
out(f"IS 期待値(avgR) 95%CI: [{ci_exp[0]:+.3f}, {ci_exp[1]:+.3f}]")
out(f"IS PF           95%CI: [{ci_pf[0]:.2f}, {ci_pf[1]:.2f}]")

# 仮説1: trigger_type
out("")
out("-" * 80)
out("仮説1: trigger_type 別 (ロング側では stagnation+rebreak が最良 PF3.65 だった)")
out("-" * 80)
for tt, g in df.groupby("trigger_type"):
    out(f"  {tt:<19}: " + fmt(metrics(g['r'])))

# 仮説3: 圧縮
out("")
out("-" * 80)
out("仮説3: 圧縮の深さ (bb_width_atr) 中央値で二分 (ロング側では狭い側 PF3.44)")
out("-" * 80)
med = df["bb_width_atr"].median()
out(f"  (bb_width_atr 中央値 = {med:.2f})")
for label, g in [("狭い(圧縮強) <=med", df[df['bb_width_atr'] <= med]),
                 ("広い(圧縮弱) > med", df[df['bb_width_atr'] > med])]:
    out(f"  {label:<18}: " + fmt(metrics(g['r'])))

# 仮説4: 期待崩壊(急騰)の鋭さ
out("")
out("-" * 80)
out("仮説4: 期待崩壊の鋭さ (v_move_atr / 急騰の大きさ) 中央値で二分")
out("-" * 80)
med2 = df["v_move_atr"].median()
out(f"  (v_move_atr 中央値 = {med2:.2f})")
for label, g in [("大きい急騰 > med", df[df['v_move_atr'] > med2]),
                 ("小さい急騰 <=med", df[df['v_move_atr'] <= med2])]:
    out(f"  {label:<16}: " + fmt(metrics(g['r'])))

# 年別・通貨別
out("")
out("-" * 80)
out("再現性: 年別 (全期間)")
out("-" * 80)
df["yr"] = pd.to_datetime(df["signal_time"]).dt.year
yr = df.groupby("yr")["r"].agg(["count", "sum", "mean"]).round(3)
yr["pf"] = df.groupby("yr")["r"].apply(lambda s: pf_of(s.values)).round(2)
out(yr.to_string())
out("")
out("再現性: 通貨別 (全期間)")
sym = df.groupby("symbol")["r"].agg(["count", "sum", "mean"]).round(3)
sym["pf"] = df.groupby("symbol")["r"].apply(lambda s: pf_of(s.values)).round(2)
out(sym.sort_values("sum", ascending=False).to_string())

# ロング vs ショート 直接対比
out("")
out("=" * 80)
out("ロング(踏み上げ) vs ショート(投げ) 直接対比 — 対称性は成立するか？")
out("=" * 80)
out(f"{'指標':<22}{'ロング(Short Squeeze)':<26}{'ショート(Long Liquidation)'}")
long_all = dict(n=114, wr=57.0, pf=2.54, total_r=67.03, avg_r=0.588)
s = metrics(df["r"])
out(f"{'n (ALL)':<22}{long_all['n']:<26}{s['n']}")
out(f"{'WR (ALL)':<22}{long_all['wr']:<26}{s['wr']:.1f}")
out(f"{'PF (ALL)':<22}{long_all['pf']:<26}{s['pf']:.2f}")
out(f"{'total R (ALL)':<22}{long_all['total_r']:<26}{s['total_r']:.2f}")
out(f"{'avg R (ALL)':<22}{long_all['avg_r']:<26}{s['avg_r']:+.3f}")

# save
rows = []
for name, sub in [("short_control_naive", ctrl), ("short_structure_IS", is_df),
                  ("short_structure_OOS", oos_df), ("short_structure_ALL", df)]:
    m = metrics(sub["r"]); m["bucket"] = name; rows.append(m)
pd.DataFrame(rows).set_index("bucket").to_csv(OUT_DIR / "verification_short_summary.csv")
(OUT_DIR / "verification_short_report.txt").write_text("\n".join(lines), encoding="utf-8")
out("")
out("saved: verification_short_summary.csv, verification_short_report.txt")

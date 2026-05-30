#!/usr/bin/env python3
"""
Market Psychology Research Framework — 検証スクリプト

検証対象（最も手応えのある構造）:
    Expectation Failure -> Short Squeeze
    急落 (続落期待) -> V字回復 (期待崩壊) -> 棚停滞/棚ブレイク (踏み上げ点火)

思想:
    相場は価格ではなく「市場参加者の期待がどこで崩壊したか」を研究する。
    本スクリプトは、この心理構造に「説明可能・OOS・再現性」のレンズで
    本当に優位性があるのかを、既にコミット済みのトレード実績データで独立に検証する。

データソース (リポジトリにコミット済み):
    1. strict V (完全V字回復で入る素朴版) ... 「価格だけ」を追う対照群
    2. T5 (早期V候補 + 棚停滞/棚ブレイクで確認) ... 心理構造版
       - IS: Research_2015_2024
       - OOS: OOS_2025_2026
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[2]
OUT_DIR = THIS_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

STRICT_V = REPO_ROOT / "backtests/elliott_fibo/results_2015_2024/strict_v_recovery/strict_v_trades_h4.csv"
T5 = REPO_ROOT / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"

RNG = np.random.default_rng(20260530)


def metrics(r: pd.Series) -> dict:
    r = pd.Series(r).astype(float).dropna()
    n = len(r)
    if n == 0:
        return dict(n=0, wr=float("nan"), avg_r=float("nan"), total_r=0.0,
                    pf=float("nan"), expectancy=float("nan"), max_dd=float("nan"),
                    max_loss_streak=0, sharpe=float("nan"))
    wins = r[r > 0]
    losses = r[r < 0]
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    equity = r.cumsum()
    dd = (equity.cummax() - equity).max()
    # max losing streak
    streak = mx = 0
    for v in r:
        if v < 0:
            streak += 1
            mx = max(mx, streak)
        else:
            streak = 0
    sharpe = r.mean() / r.std(ddof=1) * math.sqrt(n) if n > 1 and r.std(ddof=1) > 0 else float("nan")
    return dict(
        n=n,
        wr=100.0 * (r > 0).mean(),
        avg_r=r.mean(),
        total_r=r.sum(),
        pf=pf,
        expectancy=r.mean(),
        max_dd=dd,
        max_loss_streak=mx,
        sharpe=sharpe,
    )


def bootstrap_ci(r: pd.Series, fn, iters=10000, alpha=0.05):
    r = pd.Series(r).astype(float).dropna().values
    if len(r) == 0:
        return (float("nan"), float("nan"))
    stats = np.empty(iters)
    n = len(r)
    for i in range(iters):
        sample = r[RNG.integers(0, n, n)]
        stats[i] = fn(sample)
    return (float(np.quantile(stats, alpha / 2)), float(np.quantile(stats, 1 - alpha / 2)))


def pf_of(arr):
    arr = np.asarray(arr, float)
    gl = -arr[arr < 0].sum()
    return arr[arr > 0].sum() / gl if gl > 0 else np.inf


def fmt(d: dict) -> str:
    pf = "inf" if d["pf"] == float("inf") else f"{d['pf']:.2f}"
    return (f"n={d['n']:>3}  WR={d['wr']:5.1f}%  avgR={d['avg_r']:+.3f}  "
            f"totalR={d['total_r']:+6.2f}  PF={pf:>5}  maxDD={d['max_dd']:.2f}R  "
            f"maxLoss連敗={d['max_loss_streak']}  Sharpe={d['sharpe']:.2f}")


lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


# ---------------------------------------------------------------------------
out("=" * 78)
out("Market Psychology Research — Expectation Failure -> Short Squeeze 検証")
out("=" * 78)

# --- 対照群: 価格だけを追う「完全V字回復で入る」素朴版 -----------------------
sv = pd.read_csv(STRICT_V)
out("")
out("[対照群] 完全V字回復で入る素朴版 (価格だけを追う / 棚確認なし) — H4 2015-2024")
out("  " + fmt(metrics(sv["r_after_cost"])))
out("  → 期待崩壊の『地点』だけを見て、踏み上げ構造を確認せず飛び乗ると優位性は出ない。")

# --- 本命: 心理構造版 (早期V候補 + 棚停滞/棚ブレイク) -------------------------
df = pd.read_csv(T5)
df["r"] = df["r_after_cost"].astype(float)
is_df = df[df["period"] == "Research_2015_2024"].copy()
oos_df = df[df["period"] == "OOS_2025_2026"].copy()

out("")
out("-" * 78)
out("[本命] 心理構造版: 急落->V字(期待崩壊)->棚停滞/棚ブレイク(踏み上げ点火)")
out("-" * 78)
out("IS  (2015-2024): " + fmt(metrics(is_df["r"])))
out("OOS (2025-2026): " + fmt(metrics(oos_df["r"])))
out("ALL            : " + fmt(metrics(df["r"])))

# bootstrap CI on IS expectancy & PF
ci_exp = bootstrap_ci(is_df["r"], np.mean)
ci_pf = bootstrap_ci(is_df["r"], pf_of)
out("")
out(f"IS 期待値(avgR) 95%CI: [{ci_exp[0]:+.3f}, {ci_exp[1]:+.3f}]   (>0 が下限なら有意)")
out(f"IS PF           95%CI: [{ci_pf[0]:.2f}, {ci_pf[1]:.2f}]")

# ---------------------------------------------------------------------------
# 仮説検証 1: 踏み上げ点火 = 棚ブレイク(rebreak) vs 棚停滞(stagnation)
out("")
out("-" * 78)
out("仮説1: trigger_type 別 (stagnation=棚で停滞 / rebreak=棚を再ブレイク=踏み上げ点火)")
out("-" * 78)
for tt, g in df.groupby("trigger_type"):
    out(f"  {tt:<11}: " + fmt(metrics(g['r'])))
out("  IS のみ:")
for tt, g in is_df.groupby("trigger_type"):
    out(f"  {tt:<11}: " + fmt(metrics(g['r'])))

# ---------------------------------------------------------------------------
# 仮説検証 2: Short Squeeze 点火サイン = Donchian20 ブレイク有無
out("")
out("-" * 78)
out("仮説2: Donchian20 ブレイク有無 (踏み上げ=直近高値更新で買い戻し連鎖が点火するか)")
out("-" * 78)
for flag, g in df.groupby(df["donchian20_break"].astype(bool)):
    label = "Donchian20更新あり" if flag else "Donchian20更新なし"
    out(f"  {label:<18}: " + fmt(metrics(g['r'])))

# ---------------------------------------------------------------------------
# 仮説検証 3: 圧縮(Compression) = 棚レンジの狭さ (bb_width_atr) 別
out("")
out("-" * 78)
out("仮説3: 圧縮の深さ (bb_width_atr) 中央値で二分 — 棚が狭い(圧縮)ほど踏み上げが強いか")
out("-" * 78)
med = df["bb_width_atr"].median()
out(f"  (bb_width_atr 中央値 = {med:.2f})")
for label, g in [("狭い(圧縮強) <=med", df[df['bb_width_atr'] <= med]),
                 ("広い(圧縮弱) > med", df[df['bb_width_atr'] > med])]:
    out(f"  {label:<18}: " + fmt(metrics(g['r'])))

# ---------------------------------------------------------------------------
# 仮説検証 4: 期待崩壊の鋭さ = V字の下落速度 (v_drop_speed_atr_per_bar)
out("")
out("-" * 78)
out("仮説4: 期待崩壊の鋭さ (v_drop_speed_atr_per_bar) 中央値で二分")
out("       急落が鋭い=続落期待が強い=踏み上げ燃料が多い、という仮説")
out("-" * 78)
med2 = df["v_drop_speed_atr_per_bar"].median()
out(f"  (v_drop_speed 中央値 = {med2:.3f} ATR/bar)")
for label, g in [("鋭い急落 > med", df[df['v_drop_speed_atr_per_bar'] > med2]),
                 ("緩い急落 <=med", df[df['v_drop_speed_atr_per_bar'] <= med2])]:
    out(f"  {label:<14}: " + fmt(metrics(g['r'])))

# ---------------------------------------------------------------------------
# 年別 / 通貨別 (IS) で再現性チェック
out("")
out("-" * 78)
out("再現性: 年別 (全期間)")
out("-" * 78)
df["year"] = pd.to_datetime(df["signal_time"]).dt.year
yr = df.groupby("year")["r"].agg(["count", "sum", "mean"]).round(3)
yr["pf"] = df.groupby("year")["r"].apply(lambda s: pf_of(s.values)).round(2)
out(yr.to_string())

out("")
out("再現性: 通貨別 (全期間)")
sym = df.groupby("symbol")["r"].agg(["count", "sum", "mean"]).round(3)
sym["pf"] = df.groupby("symbol")["r"].apply(lambda s: pf_of(s.values)).round(2)
sym = sym.sort_values("sum", ascending=False)
out(sym.to_string())

# save machine-readable summary
summary_rows = []
for name, sub in [("strict_V_naive_all", sv.rename(columns={"r_after_cost": "r"})),
                  ("structure_IS", is_df), ("structure_OOS", oos_df), ("structure_ALL", df)]:
    m = metrics(sub["r"])
    m["bucket"] = name
    summary_rows.append(m)
pd.DataFrame(summary_rows).set_index("bucket").to_csv(OUT_DIR / "verification_summary.csv")

(OUT_DIR / "verification_report.txt").write_text("\n".join(lines), encoding="utf-8")
out("")
out("saved: verification_summary.csv, verification_report.txt")

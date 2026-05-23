"""
TrendBreakV1 バックテスト精密監査

監査項目:
  D1: データ品質チェック (欠損・重複・異常値・カバレッジ)
  D2: OOS 分割テスト (2015-2019 学習 vs 2020-2024 検証)
  D3: 取引コスト込み再評価 (Spread + Commission + Slippage)
  D4: 連敗・DD ストレステスト (心理・経済的に耐えられるか)
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backtest"))

from trendbreak_backtest import (
    PRESETS_CONSERVATIVE, PRESETS_RELAXED,
    compute_signals, simulate,
)
from sai_backtest import load_instrument, DATA_ROOT, INSTRUMENTS

OUT_DIR = THIS_DIR
TRADES_CSV = os.path.join(REPO_ROOT, "backtests", "trendbreak_v1",
                          "results_2015_2024", "trades.csv")

# ==========================================================================
# 監査5: データ品質
# ==========================================================================

def audit_data_quality() -> dict:
    print("=" * 70)
    print("AUDIT D1: Data Quality Check")
    print("=" * 70)
    report = {}
    for sym in INSTRUMENTS.keys():
        try:
            df = load_instrument(sym)
        except Exception as e:
            print(f"  [{sym}] FAILED: {e}")
            report[sym] = {"error": str(e)}
            continue

        df = df[(df.index.year >= 2015) & (df.index.year <= 2024)]
        n_total = len(df)
        n_dup = int(df.index.duplicated().sum())

        diff_hours = df.index.to_series().diff().dt.total_seconds() / 3600
        median_gap = float(diff_hours.median())
        large_gaps = int((diff_hours > 72).sum())  # 3日以上の連続欠損
        max_gap_h = float(diff_hours.max())

        bad_ohlc = int(((df["high"] < df["low"]) | (df["high"] < df["open"]) |
                        (df["high"] < df["close"]) | (df["low"] > df["open"]) |
                        (df["low"] > df["close"])).sum())

        ret = (df["close"].pct_change().abs())
        outlier_pct = float((ret > 0.05).sum() / max(len(ret), 1) * 100)  # 1足5%超

        years_covered = sorted(df.index.year.unique().tolist())

        report[sym] = {
            "bars": n_total,
            "duplicates": n_dup,
            "median_gap_hours": round(median_gap, 2),
            "gaps_over_72h": large_gaps,
            "max_gap_hours": round(max_gap_h, 1),
            "ohlc_errors": bad_ohlc,
            "outlier_5pct_bars": round(outlier_pct, 3),
            "years_covered_count": len(years_covered),
            "first_year": years_covered[0] if years_covered else None,
            "last_year": years_covered[-1] if years_covered else None,
        }
        print(f"  [{sym:7}] bars={n_total:6}  dup={n_dup:3}  gap_med={median_gap:.2f}h"
              f"  >72h_gaps={large_gaps:3}  max_gap={max_gap_h:5.1f}h"
              f"  ohlc_err={bad_ohlc:2}  outliers={outlier_pct:.2f}%")
    pd.DataFrame(report).T.to_csv(os.path.join(OUT_DIR, "audit_data_quality.csv"))
    return report


# ==========================================================================
# 監査6: OOS (Out-of-Sample) 分割テスト
# ==========================================================================

def audit_oos_split() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("AUDIT D2: OOS Split Test  (2015-2019 vs 2020-2024)")
    print("=" * 70)
    rows = []
    for mode_name, presets in (("conservative", PRESETS_CONSERVATIVE),
                                ("relaxed", PRESETS_RELAXED)):
        for sym, cfg in presets.items():
            try:
                df = load_instrument(sym)
            except Exception:
                continue
            for label, yfrom, yto in (("IS_2015-2019", 2015, 2019),
                                       ("OOS_2020-2024", 2020, 2024)):
                sub = df[(df.index.year >= yfrom) & (df.index.year <= yto)]
                if sub.empty:
                    continue
                sig = compute_signals(sub, cfg)
                trades = simulate(sig, cfg)
                if not trades:
                    continue
                r = np.array([t.pnl_r for t in trades])
                wr = (r > 0).mean() * 100
                gp = r[r > 0].sum()
                gl = r[r <= 0].sum()
                pf = gp / abs(gl) if gl < 0 else np.inf
                eq = np.cumsum(r)
                dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0
                rows.append({
                    "mode": mode_name, "symbol": sym, "period": label,
                    "trades": len(trades),
                    "win_rate": round(wr, 2),
                    "total_r": round(r.sum(), 2),
                    "avg_r": round(r.mean(), 4),
                    "pf": round(pf, 3) if np.isfinite(pf) else np.inf,
                    "max_dd_r": round(dd, 2),
                })
    df = pd.DataFrame(rows)

    pivot = df.pivot_table(index=["mode", "symbol"], columns="period",
                            values=["total_r", "pf", "win_rate", "trades"],
                            aggfunc="first")
    pivot.to_csv(os.path.join(OUT_DIR, "audit_oos_split.csv"))

    print("\n--- Aggregated by mode ---")
    print(f"{'mode':12} {'period':14} {'trades':>7} {'WR':>7} {'TotalR':>9} {'PF':>6}")
    for mode_name in ("conservative", "relaxed"):
        for label in ("IS_2015-2019", "OOS_2020-2024"):
            sub = df[(df["mode"] == mode_name) & (df["period"] == label)]
            if sub.empty:
                continue
            t = sub["trades"].sum()
            r = sub["total_r"].sum()
            wr_avg = sub["win_rate"].mean()
            # 全データで一つの PF
            print(f"{mode_name:12} {label:14} {t:>7} {wr_avg:>6.1f}% {r:>+8.1f}R {sub['pf'].mean():>5.2f}")
    return df


# ==========================================================================
# 監査7: 取引コスト込み再評価
# ==========================================================================

# 通貨ペア別の実取引コスト推定 (pips換算)
#   - スプレッド: STP/ECN系ブローカーの一般的水準
#   - スリッページ: SL執行時の追加コスト (現実的な水準)
#   - 単位は「価格そのもの」(USD or JPY)
COST_TABLE = {
    "USDJPY": {"spread_price": 0.010,  "slip_price": 0.005},   # 1pip + 0.5pip
    "EURJPY": {"spread_price": 0.015,  "slip_price": 0.005},   # 1.5pip + 0.5pip
    "GBPJPY": {"spread_price": 0.020,  "slip_price": 0.010},   # 2pip + 1pip
    "AUDJPY": {"spread_price": 0.015,  "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020,  "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30,   "slip_price": 0.20},    # $0.30 + $0.20
    "SILVER": {"spread_price": 0.030,  "slip_price": 0.020},
}


def audit_cost_impact() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("AUDIT D3: Cost Impact (Spread + Slippage)")
    print("=" * 70)
    rows = []
    for mode_name, presets in (("conservative", PRESETS_CONSERVATIVE),
                                ("relaxed", PRESETS_RELAXED)):
        for sym, cfg in presets.items():
            if sym not in COST_TABLE:
                continue
            try:
                df = load_instrument(sym)
            except Exception:
                continue
            df = df[(df.index.year >= 2015) & (df.index.year <= 2024)]
            sig = compute_signals(df, cfg)
            trades = simulate(sig, cfg)
            if not trades:
                continue
            spread = COST_TABLE[sym]["spread_price"]
            slip = COST_TABLE[sym]["slip_price"]
            # Long 時:
            #   entry: スプレッドの半分悪化 → entry に + spread/2
            #   SL hit: 滑り → SL に - slip
            #   TP hit: スプレッド込みで TP に届くのが遅れる → -slip
            r_clean = np.array([t.pnl_r for t in trades])
            r_after_cost = []
            for t in trades:
                # entry / exit を悪化させて pnl を再計算
                ent = t.entry + spread / 2 if t.direction == "long" else t.entry - spread / 2
                ex = t.exit_price
                if t.exit_reason if hasattr(t, "exit_reason") else (ex == t.sl):
                    pass
                # exit_price が SL == 損切り
                if t.direction == "long":
                    if abs(ex - t.sl) < 1e-9:
                        ex = ex - slip
                    else:  # TP
                        ex = ex - slip
                else:
                    if abs(ex - t.sl) < 1e-9:
                        ex = ex + slip
                    else:
                        ex = ex + slip
                pnl = (ex - ent) if t.direction == "long" else (ent - ex)
                sl_dist = abs(t.entry - t.sl)
                r_after_cost.append(pnl / sl_dist if sl_dist > 0 else 0)
            r_after_cost = np.array(r_after_cost)
            wr_c = (r_clean > 0).mean() * 100
            wr_a = (r_after_cost > 0).mean() * 100
            net_c = r_clean.sum()
            net_a = r_after_cost.sum()
            pf_c = (r_clean[r_clean > 0].sum() / abs(r_clean[r_clean <= 0].sum())
                    if (r_clean <= 0).any() else np.inf)
            pf_a = (r_after_cost[r_after_cost > 0].sum() / abs(r_after_cost[r_after_cost <= 0].sum())
                    if (r_after_cost <= 0).any() else np.inf)
            rows.append({
                "mode": mode_name, "symbol": sym, "trades": len(trades),
                "wr_clean": round(wr_c, 2), "wr_after_cost": round(wr_a, 2),
                "totalR_clean": round(net_c, 2), "totalR_after_cost": round(net_a, 2),
                "pf_clean": round(pf_c, 3) if np.isfinite(pf_c) else np.inf,
                "pf_after_cost": round(pf_a, 3) if np.isfinite(pf_a) else np.inf,
                "R_lost_to_cost": round(net_c - net_a, 2),
                "R_per_trade_cost": round((net_c - net_a) / len(trades), 4),
            })
            print(f"  [{mode_name:11}] {sym:7}  "
                  f"Clean:{net_c:+7.1f}R  After:{net_a:+7.1f}R  "
                  f"Cost:{net_c - net_a:+6.1f}R  PF: {pf_c:.2f}→{pf_a:.2f}")
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT_DIR, "audit_cost_impact.csv"), index=False)
    if not out.empty:
        print("\n--- TOTAL across all symbols/modes ---")
        print(f"  Clean Total R:       {out['totalR_clean'].sum():+.2f}")
        print(f"  After-Cost Total R:  {out['totalR_after_cost'].sum():+.2f}")
        print(f"  Cost (lost R):       {(out['totalR_clean'].sum() - out['totalR_after_cost'].sum()):+.2f}")
        print(f"  Cost ratio:          {(1 - out['totalR_after_cost'].sum() / out['totalR_clean'].sum()) * 100:.1f}%")
    return out


# ==========================================================================
# 監査8: 連敗・DD ストレステスト
# ==========================================================================

def audit_streaks_dd() -> dict:
    print("\n" + "=" * 70)
    print("AUDIT D4: Streaks & DD Stress Test")
    print("=" * 70)
    df = pd.read_csv(TRADES_CSV, parse_dates=["entry_time", "exit_time"])
    df = df.sort_values("entry_time").reset_index(drop=True)

    out = {}
    for mode in ["conservative", "relaxed", "combined"]:
        sub = df if mode == "combined" else df[df["mode"] == mode]
        if sub.empty:
            continue
        r = sub["pnl_r"].to_numpy()
        signs = np.where(r > 0, 1, -1)
        max_win, max_lose, cur_win, cur_lose = 0, 0, 0, 0
        win_streaks = []
        lose_streaks = []
        for s in signs:
            if s == 1:
                cur_win += 1
                if cur_lose > 0:
                    lose_streaks.append(cur_lose)
                cur_lose = 0
            else:
                cur_lose += 1
                if cur_win > 0:
                    win_streaks.append(cur_win)
                cur_win = 0
            max_win = max(max_win, cur_win)
            max_lose = max(max_lose, cur_lose)
        if cur_win > 0:
            win_streaks.append(cur_win)
        if cur_lose > 0:
            lose_streaks.append(cur_lose)

        eq = np.cumsum(r)
        peak = np.maximum.accumulate(eq)
        dd = peak - eq

        # 最深DDからの回復までの所要バー数
        peak_idx = int(np.argmax(dd))
        recovered = False
        recovery_bars = -1
        for i in range(peak_idx + 1, len(eq)):
            if eq[i] >= peak[peak_idx]:
                recovery_bars = i - peak_idx
                recovered = True
                break

        # 月別R分布
        sub2 = sub.copy()
        sub2["year_month"] = sub2["entry_time"].dt.to_period("M").astype(str)
        monthly = sub2.groupby("year_month")["pnl_r"].sum()
        losing_months = int((monthly < 0).sum())
        worst_month = float(monthly.min())
        best_month = float(monthly.max())
        win_months = int((monthly > 0).sum())

        out[mode] = {
            "trades": len(sub),
            "max_winning_streak": int(max_win),
            "max_losing_streak": int(max_lose),
            "max_dd_r": round(float(dd.max()), 2),
            "max_dd_pct_of_total": round(float(dd.max() / max(eq[-1], 0.0001) * 100), 1),
            "recovery_trades": recovery_bars if recovered else "NOT_RECOVERED",
            "total_months": int(len(monthly)),
            "winning_months": win_months,
            "losing_months": losing_months,
            "best_month_r": round(best_month, 2),
            "worst_month_r": round(worst_month, 2),
        }
        print(f"\n  [{mode}]")
        for k, v in out[mode].items():
            print(f"    {k}: {v}")

    pd.DataFrame(out).T.to_csv(os.path.join(OUT_DIR, "audit_streaks_dd.csv"))
    return out


# ==========================================================================
# Main
# ==========================================================================

def main() -> None:
    d1 = audit_data_quality()
    d2 = audit_oos_split()
    d3 = audit_cost_impact()
    d4 = audit_streaks_dd()

    print("\n" + "=" * 70)
    print("AUDIT REPORTS")
    print("=" * 70)
    for fn in sorted(os.listdir(OUT_DIR)):
        if fn.endswith(".csv"):
            sz = os.path.getsize(os.path.join(OUT_DIR, fn))
            print(f"  {fn:40} {sz:>10} bytes")


if __name__ == "__main__":
    main()

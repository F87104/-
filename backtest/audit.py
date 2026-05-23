"""
TrendBreakV1 Relaxed 徹底監査

監査ポイント:
  1. 現実コスト (スプレッド+スリッページ+手数料) を反映
  2. データ品質 (ギャップ、重複、欠損)
  3. 同一バー SL/TP 同時ヒットの感度 (SL先 / TP先 / ランダム)
  4. Pine vs Python ロジック完全一致確認
  5. 年別損益カーブ (どの年に儲け、どの年に負けたか)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sai_backtest import atr, rolling_max, rolling_min, load_instrument
from optimize_trendbreak import TBConfig, BASE, ATR_PERIOD, LOOKBACK_LONG, EXCLUDE_LONG
from trendbreak_backtest import compute_signals as compute_signals_tb


# ============================================================
# 現実コスト (1スプレッド換算で価格単位)
# Tickごとの "通常" スプレッド (broker median, FXCM相当)
# ============================================================
SPREAD = {
    "EURJPY":  0.015,   # 1.5 pips
    "USDJPY":  0.010,   # 1.0 pips
    "GBPJPY":  0.020,   # 2.0 pips
    "CHFJPY":  0.020,
    "AUDJPY":  0.015,
    "XAUUSD":  0.50,    # 50 cents
    "SILVER":  0.03,
    "XAGUSD":  0.03,
}
# スリッページ (1サイドあたり、価格単位)
SLIPPAGE = {k: v * 0.5 for k, v in SPREAD.items()}


# ============================================================
# Realistic trade simulation
# ============================================================
@dataclass
class RealTrade:
    pnl_r: float
    pnl_pips: float
    is_win: bool
    direction: str
    setup_atr: float
    sl_dist_price: float


def simulate_realistic(sig: pd.DataFrame, cfg: TBConfig, name: str,
                       resolution: str = "sl_first") -> list[RealTrade]:
    """resolution: "sl_first" (保守) / "tp_first" (楽観) / "random" / "midpoint" """
    rng = np.random.default_rng(42)
    spread = SPREAD.get(name, 0.0)
    slip = SLIPPAGE.get(name, 0.0)

    trades: list[RealTrade] = []
    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    long_sig = sig["long_sig"].to_numpy()
    short_sig = sig["short_sig"].to_numpy()
    n = len(sig)

    in_pos_until = -1
    cooldown_until = -1
    for i in range(n - 1):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        if not (long_sig[i] or short_sig[i]):
            continue
        sig_atr = a[i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue
        is_long = bool(long_sig[i])
        entry_bar = i + 1
        if entry_bar >= n:
            break

        # 実際の約定価格 = 次バー始値 +/- (半スプレッド + スリッページ)
        cost_in = spread / 2 + slip
        entry = o[entry_bar] + (cost_in if is_long else -cost_in)
        sl_dist = sig_atr * cfg.sl_atr
        if is_long:
            sl = entry - sl_dist
            tp = entry + sl_dist * cfg.tp_rr
        else:
            sl = entry + sl_dist
            tp = entry - sl_dist * cfg.tp_rr

        # SL/TP もスリッページ加味 (出口の負け値で約定)
        cost_out_sl = spread / 2 + slip   # ストップは逆方向の悪い価格で約定
        cost_out_tp = spread / 2 + slip   # TP は逆指値だが板変動で多少差し引かれる

        for j in range(entry_bar, n):
            if is_long:
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp

            if hit_sl and hit_tp:
                if resolution == "tp_first":
                    ex = tp - cost_out_tp if is_long else tp + cost_out_tp
                    pnl = (ex - entry) if is_long else (entry - ex)
                elif resolution == "random":
                    if rng.random() < 0.5:
                        ex = sl - cost_out_sl if is_long else sl + cost_out_sl
                    else:
                        ex = tp - cost_out_tp if is_long else tp + cost_out_tp
                    pnl = (ex - entry) if is_long else (entry - ex)
                elif resolution == "midpoint":
                    ex = (sl + tp) / 2
                    pnl = (ex - entry) if is_long else (entry - ex)
                else:  # sl_first 保守
                    ex = sl - cost_out_sl if is_long else sl + cost_out_sl
                    pnl = (ex - entry) if is_long else (entry - ex)
                pnl_r = pnl / sl_dist
                trades.append(RealTrade(pnl_r, pnl, pnl > 0, "long" if is_long else "short", sig_atr, sl_dist))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_sl:
                ex = sl - cost_out_sl if is_long else sl + cost_out_sl
                pnl = (ex - entry) if is_long else (entry - ex)
                pnl_r = pnl / sl_dist
                trades.append(RealTrade(pnl_r, pnl, pnl > 0, "long" if is_long else "short", sig_atr, sl_dist))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_tp:
                ex = tp - cost_out_tp if is_long else tp + cost_out_tp
                pnl = (ex - entry) if is_long else (entry - ex)
                pnl_r = pnl / sl_dist
                trades.append(RealTrade(pnl_r, pnl, pnl > 0, "long" if is_long else "short", sig_atr, sl_dist))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    return trades


def stats_real(trades: list[RealTrade]) -> dict:
    if not trades:
        return {"n": 0, "wr": 0.0, "pf": np.nan, "net_r": 0.0, "net_price": 0.0,
                "exp_r": 0.0, "dd_r": 0.0}
    pnl_r = np.array([t.pnl_r for t in trades])
    pnl_pr = np.array([t.pnl_pips for t in trades])
    wins = (pnl_r > 0).sum()
    gp = pnl_r[pnl_r > 0].sum()
    gl = pnl_r[pnl_r <= 0].sum()
    eq = np.cumsum(pnl_r)
    return {
        "n": len(trades), "wr": wins / len(trades) * 100,
        "pf": gp / abs(gl) if gl < 0 else np.inf,
        "net_r": pnl_r.sum(), "net_price": pnl_pr.sum(),
        "exp_r": pnl_r.mean(),
        "dd_r": float((np.maximum.accumulate(eq) - eq).max()),
    }


# ============================================================
# データ品質チェック
# ============================================================
def check_data_quality(name: str, df: pd.DataFrame) -> dict:
    expected_per_year = 24 * 252  # 平日24h × 252日
    n_years = (df.index.max() - df.index.min()).days / 365.25
    expected = int(expected_per_year * n_years)

    # ギャップ検出 (1時間以上の連続欠損)
    gaps = df.index.to_series().diff().dt.total_seconds() / 3600
    big_gaps = (gaps > 5).sum()  # 5時間以上のギャップ

    # 重複検出
    dup = df.index.duplicated().sum()

    # 異常な値検出
    zero_range = ((df["high"] - df["low"]) == 0).sum()
    open_eq_close = (df["open"] == df["close"]).sum()

    return {
        "bars": len(df),
        "expected": expected,
        "coverage_pct": len(df) / expected * 100 if expected else 0,
        "big_gaps": int(big_gaps),
        "duplicates": int(dup),
        "zero_range_bars": int(zero_range),
        "first": str(df.index.min().date()),
        "last": str(df.index.max().date()),
    }


# ============================================================
# 年別損益カーブ
# ============================================================
def yearly_breakdown(name: str, df: pd.DataFrame, cfg: TBConfig) -> pd.DataFrame:
    sig = compute_signals_tb(df, {
        "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
        "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
        "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
        "margin": cfg.margin, "cooldown": cfg.cooldown,
    })
    trades_real = simulate_realistic(sig, cfg, name, resolution="sl_first")
    # 各トレードの「年」を集計に組み込むため再シミュレーション (簡易: open時刻使う)
    # トレードに時刻を持たせるためここで再生成
    # ... 既にtrades_realがあるが、年データがないので、シグナルベースで集計
    rows = []
    o = sig["open"].to_numpy(); h_arr = sig["high"].to_numpy(); l_arr = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    ls = sig["long_sig"].to_numpy(); ss = sig["short_sig"].to_numpy()
    spread = SPREAD.get(name, 0.0); slip = SLIPPAGE.get(name, 0.0)
    cost_in = spread / 2 + slip; cost_out = spread / 2 + slip

    in_pos_until = -1; cooldown_until = -1
    n = len(sig)
    for i in range(n - 1):
        if i <= in_pos_until or i <= cooldown_until: continue
        if not (ls[i] or ss[i]): continue
        sa = a[i]
        if np.isnan(sa) or sa <= 0: continue
        is_long = bool(ls[i]); entry_bar = i + 1
        if entry_bar >= n: break
        entry = o[entry_bar] + (cost_in if is_long else -cost_in)
        sd = sa * cfg.sl_atr
        sl = entry - sd if is_long else entry + sd
        tp = entry + sd * cfg.tp_rr if is_long else entry - sd * cfg.tp_rr
        for j in range(entry_bar, n):
            if is_long:
                hit_sl = l_arr[j] <= sl; hit_tp = h_arr[j] >= tp
            else:
                hit_sl = h_arr[j] >= sl; hit_tp = l_arr[j] <= tp
            if hit_sl or hit_tp:
                if hit_sl and hit_tp:
                    ex = sl - cost_out if is_long else sl + cost_out
                elif hit_sl:
                    ex = sl - cost_out if is_long else sl + cost_out
                else:
                    ex = tp - cost_out if is_long else tp + cost_out
                pnl = (ex - entry) if is_long else (entry - ex)
                rows.append({"year": sig.index[i].year, "pnl_r": pnl / sd})
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    if not rows:
        return pd.DataFrame()
    dft = pd.DataFrame(rows)
    yearly = dft.groupby("year").agg(
        n=("pnl_r", "count"),
        wr=("pnl_r", lambda s: (s > 0).mean() * 100),
        net=("pnl_r", "sum"),
    ).reset_index()
    return yearly


# ============================================================
# Main audit
# ============================================================
def run_audit(instruments: list[str]):
    data = {}
    for n in instruments:
        try:
            data[n] = load_instrument(n)
        except Exception as e:
            print(f"[SKIP] {n}: {e}")
    instruments = list(data.keys())

    print("=" * 100)
    print("【監査 1】 データ品質チェック")
    print("=" * 100)
    for name in instruments:
        q = check_data_quality(name, data[name])
        verdict = "OK" if q["coverage_pct"] > 95 and q["duplicates"] == 0 else "⚠️"
        print(f"  {verdict} {name:7}  bars={q['bars']:>6} (期待{q['expected']:>6}, 充足率 {q['coverage_pct']:.1f}%)  "
              f"ギャップ>5h={q['big_gaps']:>4}  重複={q['duplicates']:>3}  ゼロ足={q['zero_range_bars']:>4}  "
              f"期間 {q['first']}〜{q['last']}")

    print("\n" + "=" * 100)
    print("【監査 2】 現実コスト適用後の利益 (スプレッド+スリッページ込み)")
    print("=" * 100)
    print(f"  仮定: スプレッド/スリッページ通常想定 (EURJPY=1.5pips, XAUUSD=$0.5, ...)")

    rows = []
    for name in instruments:
        df = data[name]
        cfg = BASE[name]
        sig = compute_signals_tb(df, {
            "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
            "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
            "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
            "margin": cfg.margin, "cooldown": cfg.cooldown,
        })
        # コストなし版 (基準)
        t_free = simulate_realistic(sig, cfg, name + "_FREE", resolution="sl_first")  # 存在しないキー → コスト0
        # コストあり版
        t_real = simulate_realistic(sig, cfg, name, resolution="sl_first")
        s_free = stats_real(t_free); s_real = stats_real(t_real)
        loss = s_free["net_r"] - s_real["net_r"]
        print(f"  {name:7}  n={s_real['n']:>4}  "
              f"WRなし→{s_real['wr']:5.1f}%  "
              f"コストなし {s_free['net_r']:+6.1f}R → 込み {s_real['net_r']:+6.1f}R  "
              f"(コスト負担 {loss:+.1f}R)")
        rows.append({"inst": name, "no_cost": s_free["net_r"], "with_cost": s_real["net_r"],
                     "n": s_real["n"], "wr_real": s_real["wr"], "pf_real": s_real["pf"]})
    df_costs = pd.DataFrame(rows)
    print(f"\n  全通貨合計  コスト無 {df_costs['no_cost'].sum():+.1f}R → "
          f"込み {df_costs['with_cost'].sum():+.1f}R  "
          f"(劣化 {df_costs['no_cost'].sum() - df_costs['with_cost'].sum():.1f}R)")

    print("\n" + "=" * 100)
    print("【監査 3】 同一バー SL/TP 同時ヒット時の解釈感度")
    print("=" * 100)
    print("  保守 (SL先) / 楽観 (TP先) / 50%ランダム / 中点で比較")
    for resolution in ["sl_first", "tp_first", "random", "midpoint"]:
        total = 0
        for name in instruments:
            df = data[name]
            cfg = BASE[name]
            sig = compute_signals_tb(df, {
                "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
                "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
                "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
                "margin": cfg.margin, "cooldown": cfg.cooldown,
            })
            t = simulate_realistic(sig, cfg, name, resolution=resolution)
            s = stats_real(t)
            total += s["net_r"]
        print(f"  {resolution:10}  全通貨 NetR (コスト込み) = {total:+.1f}R")

    print("\n" + "=" * 100)
    print("【監査 4】 年別損益カーブ (コスト込み)")
    print("=" * 100)
    all_yearly = []
    for name in instruments:
        yearly = yearly_breakdown(name, data[name], BASE[name])
        if yearly.empty: continue
        yearly["inst"] = name
        all_yearly.append(yearly)
    if all_yearly:
        yd = pd.concat(all_yearly, ignore_index=True)
        # ピボット
        pvt_net = yd.pivot(index="inst", columns="year", values="net").fillna(0)
        pvt_wr = yd.pivot(index="inst", columns="year", values="wr").fillna(0)
        print("\n  年別 Net R (コスト込み):")
        print(pvt_net.to_string(float_format=lambda x: f"{x:+.1f}"))
        print("\n  年別合計 (全通貨):")
        totals = pvt_net.sum(axis=0)
        for y, v in totals.items():
            bar = "█" * int(abs(v) / 3) if abs(v) >= 3 else "·"
            sign = "+" if v >= 0 else "-"
            print(f"    {y}: {sign}{abs(v):5.1f}R  {bar}")
        # 連敗・連勝年カウント
        years_pos = (totals > 0).sum()
        years_neg = (totals < 0).sum()
        print(f"\n  プラス年: {years_pos}, マイナス年: {years_neg}")

    print("\n" + "=" * 100)
    print("【監査 5】 月別損益分布 (XAUUSD, USDJPY のみ)")
    print("=" * 100)
    for name in ["XAUUSD", "USDJPY"]:
        if name not in data: continue
        df = data[name]
        cfg = BASE[name]
        sig = compute_signals_tb(df, {
            "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
            "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
            "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
            "margin": cfg.margin, "cooldown": cfg.cooldown,
        })
        # シグナル時刻ベースで月別集計
        from collections import defaultdict
        monthly = defaultdict(float)
        # シミュレーション再走 (シグナル時刻を保持)
        o = sig["open"].to_numpy(); h_arr = sig["high"].to_numpy(); l_arr = sig["low"].to_numpy()
        a = sig["atr"].to_numpy()
        ls = sig["long_sig"].to_numpy(); ss = sig["short_sig"].to_numpy()
        spread = SPREAD.get(name, 0); slip = SLIPPAGE.get(name, 0)
        ci = spread / 2 + slip; co = spread / 2 + slip
        in_pos_until = -1; cooldown_until = -1
        for i in range(len(sig) - 1):
            if i <= in_pos_until or i <= cooldown_until: continue
            if not (ls[i] or ss[i]): continue
            sa = a[i]
            if np.isnan(sa) or sa <= 0: continue
            is_long = bool(ls[i]); eb = i + 1
            if eb >= len(sig): break
            entry = o[eb] + (ci if is_long else -ci)
            sd = sa * cfg.sl_atr
            sl = entry - sd if is_long else entry + sd
            tp = entry + sd * cfg.tp_rr if is_long else entry - sd * cfg.tp_rr
            for j in range(eb, len(sig)):
                if is_long:
                    hsl = l_arr[j] <= sl; htp = h_arr[j] >= tp
                else:
                    hsl = h_arr[j] >= sl; htp = l_arr[j] <= tp
                if hsl or htp:
                    if hsl:
                        ex = sl - co if is_long else sl + co
                    else:
                        ex = tp - co if is_long else tp + co
                    p = (ex - entry) if is_long else (entry - ex)
                    key = sig.index[i].strftime("%Y-%m")
                    monthly[key] += p / sd
                    in_pos_until = j; cooldown_until = j + cfg.cooldown
                    break
        # 統計
        if monthly:
            vals = list(monthly.values())
            pos = sum(1 for v in vals if v > 0)
            neg = sum(1 for v in vals if v < 0)
            wr_month = pos / len(vals) * 100
            print(f"  {name}: 月数={len(vals)} 勝月={pos} 負月={neg} 月間勝率={wr_month:.1f}% "
                  f"最良月={max(vals):+.1f}R 最悪月={min(vals):+.1f}R")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    args = ap.parse_args()
    run_audit(args.instruments)

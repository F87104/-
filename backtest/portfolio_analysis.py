"""
ポートフォリオ・運用面の最終検証

実施項目:
  1. 複利資金シミュレーション (実口座での月次推移)
  2. モンテカルロ連敗分析 (最大DDの確率分布、口座破綻確率)
  3. 5通貨相関測定 (同時保有の真の効果)
  4. ポジションサイジング3種比較
     - A) 固定 1% リスク
     - B) ボラ調整 (ATRが平均より高いときは縮小)
     - C) 連敗縮小 (3連敗で50%、5連敗で25%、4連勝で復元)

データ前提:
  - 5通貨: XAUUSD, USDJPY, GBPJPY, CHFJPY, AUDJPY (SILVER/EURJPY除外)
  - 現実コスト込み (スプレッド+スリッページ)
  - Pine TrendBreakV1 Relaxed プリセット
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from sai_backtest import load_instrument
from optimize_trendbreak import TBConfig, BASE
from trendbreak_backtest import compute_signals as compute_signals_tb
from audit import SPREAD, SLIPPAGE


# ============================================================
# トレード生成 (時刻+R+SL距離をきっちり保持)
# ============================================================
@dataclass
class Trade:
    inst: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    pnl_r: float                # SL距離正規化
    sl_dist_price: float        # 価格単位のSL距離
    atr_at_entry: float


def generate_trades(name: str, df: pd.DataFrame, cfg: TBConfig) -> list[Trade]:
    sig = compute_signals_tb(df, {
        "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
        "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
        "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
        "margin": cfg.margin, "cooldown": cfg.cooldown,
    })
    spread = SPREAD.get(name, 0.0)
    slip = SLIPPAGE.get(name, 0.0)
    ci = spread / 2 + slip
    co = spread / 2 + slip

    o = sig["open"].to_numpy(); h = sig["high"].to_numpy()
    l = sig["low"].to_numpy(); c = sig["close"].to_numpy()
    a = sig["atr"].to_numpy()
    ls = sig["long_sig"].to_numpy(); ss = sig["short_sig"].to_numpy()
    idx = sig.index
    n = len(sig)

    trades: list[Trade] = []
    in_pos_until = -1
    cooldown_until = -1
    for i in range(n - 1):
        if i <= in_pos_until or i <= cooldown_until: continue
        if not (ls[i] or ss[i]): continue
        sa = a[i]
        if np.isnan(sa) or sa <= 0: continue
        is_long = bool(ls[i])
        eb = i + 1
        if eb >= n: break
        entry = o[eb] + (ci if is_long else -ci)
        sd = sa * cfg.sl_atr
        sl = entry - sd if is_long else entry + sd
        tp = entry + sd * cfg.tp_rr if is_long else entry - sd * cfg.tp_rr
        for j in range(eb, n):
            if is_long:
                hsl = l[j] <= sl; htp = h[j] >= tp
            else:
                hsl = h[j] >= sl; htp = l[j] <= tp
            if hsl or htp:
                if hsl:
                    ex = sl - co if is_long else sl + co
                else:
                    ex = tp - co if is_long else tp + co
                pnl = (ex - entry) if is_long else (entry - ex)
                trades.append(Trade(name, idx[i], idx[j],
                                    "long" if is_long else "short",
                                    pnl / sd, sd, sa))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    return trades


# ============================================================
# 1. 複利資金シミュレーション
# ============================================================
def compound_sim(trades: list[Trade], initial: float, risk_pct: float,
                 sizing: str = "fixed",
                 atr_baseline: Optional[dict] = None) -> pd.DataFrame:
    """
    sizing: "fixed" / "vol_adjusted" / "drawdown_reduce"
    """
    rows = []
    equity = initial
    peak = initial
    consec_losses = 0
    consec_wins = 0
    size_multiplier = 1.0

    # トレードを時系列順に並べる
    sorted_trades = sorted(trades, key=lambda t: t.entry_time)

    for t in sorted_trades:
        # サイズ倍率の決定
        if sizing == "fixed":
            mult = 1.0
        elif sizing == "vol_adjusted":
            baseline = atr_baseline.get(t.inst, t.atr_at_entry) if atr_baseline else t.atr_at_entry
            ratio = baseline / t.atr_at_entry
            mult = float(np.clip(ratio, 0.3, 2.0))
        elif sizing == "drawdown_reduce":
            if consec_losses >= 5:
                mult = 0.25
            elif consec_losses >= 3:
                mult = 0.5
            else:
                mult = 1.0
            # 連勝後の復元はゆっくり
            if consec_wins >= 4 and mult < 1.0:
                mult = min(1.0, mult * 1.5)
        else:
            mult = 1.0

        risk_amount = equity * (risk_pct / 100) * mult
        pnl_dollar = t.pnl_r * risk_amount
        equity += pnl_dollar
        peak = max(peak, equity)
        dd_pct = (peak - equity) / peak * 100

        # 連勝/連敗カウント
        if t.pnl_r > 0:
            consec_wins += 1; consec_losses = 0
        else:
            consec_losses += 1; consec_wins = 0

        rows.append({"time": t.entry_time, "inst": t.inst, "pnl_r": t.pnl_r,
                     "mult": mult, "risk_amt": risk_amount, "pnl_dollar": pnl_dollar,
                     "equity": equity, "peak": peak, "dd_pct": dd_pct})
    return pd.DataFrame(rows)


# ============================================================
# 2. モンテカルロ分析
# ============================================================
def monte_carlo(pnl_r_list: np.ndarray, n_paths: int = 5000,
                risk_pct: float = 1.0, initial: float = 10000) -> dict:
    """ブートストラップ法: トレード結果を復元抽出して別ユニバースを生成"""
    rng = np.random.default_rng(42)
    final_returns = []
    max_dds = []
    losers = 0

    n_trades = len(pnl_r_list)
    for _ in range(n_paths):
        # 復元抽出 (新しい未来をN回サンプル)
        sample = rng.choice(pnl_r_list, size=n_trades, replace=True)
        eq = initial
        peak = initial
        max_dd = 0.0
        for r in sample:
            risk_amt = eq * (risk_pct / 100)
            eq += r * risk_amt
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100
            max_dd = max(max_dd, dd)
        final_returns.append((eq - initial) / initial * 100)
        max_dds.append(max_dd)
        if eq < initial:
            losers += 1

    final_returns = np.array(final_returns)
    max_dds = np.array(max_dds)
    return {
        "n_paths": n_paths,
        "n_trades": n_trades,
        "median_return_pct": float(np.median(final_returns)),
        "mean_return_pct": float(np.mean(final_returns)),
        "p5_return": float(np.percentile(final_returns, 5)),
        "p95_return": float(np.percentile(final_returns, 95)),
        "median_dd": float(np.median(max_dds)),
        "p95_dd": float(np.percentile(max_dds, 95)),
        "max_dd_seen": float(max_dds.max()),
        "loser_rate": losers / n_paths * 100,
    }


# ============================================================
# 3. 通貨間相関
# ============================================================
def correlation_analysis(trades_by_inst: dict[str, list[Trade]]) -> pd.DataFrame:
    """月次R合計の相関行列"""
    monthly = {}
    for inst, trades in trades_by_inst.items():
        if not trades:
            continue
        df = pd.DataFrame([{"t": t.entry_time, "r": t.pnl_r} for t in trades])
        df["ym"] = df["t"].dt.to_period("M")
        m = df.groupby("ym")["r"].sum()
        monthly[inst] = m
    if not monthly:
        return pd.DataFrame()
    full = pd.DataFrame(monthly).fillna(0)
    return full.corr()


# ============================================================
# Main
# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "GBPJPY", "CHFJPY", "AUDJPY"])
    ap.add_argument("--risk-pct", type=float, default=1.0)
    ap.add_argument("--initial", type=float, default=10000)
    args = ap.parse_args()

    print("=" * 100)
    print(f"【ポートフォリオ分析】 5通貨 / 初期資金 ${args.initial:,.0f} / リスク {args.risk_pct}% / コスト込み")
    print("=" * 100)

    # データロード + トレード生成
    print("\n[ステップ1] 全通貨のトレード生成 (10年分)")
    all_trades = []
    by_inst: dict[str, list[Trade]] = {}
    atr_baseline = {}
    for name in args.instruments:
        try:
            df = load_instrument(name)
        except Exception as e:
            print(f"  [SKIP] {name}: {e}")
            continue
        cfg = BASE[name]
        trs = generate_trades(name, df, cfg)
        by_inst[name] = trs
        all_trades.extend(trs)
        atr_baseline[name] = df["high"].sub(df["low"]).rolling(14).mean().mean()
        net_r = sum(t.pnl_r for t in trs)
        wr = sum(1 for t in trs if t.pnl_r > 0) / len(trs) * 100
        print(f"  {name:7}  n={len(trs):>4}  WR={wr:5.1f}%  Net={net_r:+6.1f}R")
    all_trades.sort(key=lambda t: t.entry_time)
    print(f"  合計: {len(all_trades)} トレード / Net = {sum(t.pnl_r for t in all_trades):+.1f}R")

    # =====================================================
    # 1. 複利資金シミュレーション
    # =====================================================
    print("\n" + "=" * 100)
    print("【分析1】 複利資金シミュレーション (3種類のサイジング比較)")
    print("=" * 100)

    sizings = ["fixed", "vol_adjusted", "drawdown_reduce"]
    sizing_labels = {"fixed": "A) 固定 1% リスク",
                     "vol_adjusted": "B) ボラ調整サイズ",
                     "drawdown_reduce": "C) 連敗縮小"}
    sims = {}
    for s in sizings:
        sim = compound_sim(all_trades, args.initial, args.risk_pct, s, atr_baseline)
        sims[s] = sim
        final = sim["equity"].iloc[-1]
        max_dd = sim["dd_pct"].max()
        ret_pct = (final - args.initial) / args.initial * 100
        years = (sim["time"].iloc[-1] - sim["time"].iloc[0]).days / 365.25
        cagr = ((final / args.initial) ** (1 / years) - 1) * 100 if years > 0 else 0
        n_trades = len(sim)
        wins = (sim["pnl_r"] > 0).sum()
        print(f"\n  [{sizing_labels[s]}]")
        print(f"    最終資金: ${final:,.0f} (+{ret_pct:.1f}%) / CAGR {cagr:.1f}%")
        print(f"    最大DD: {max_dd:.1f}%")
        print(f"    取引: {n_trades}  勝率: {wins/n_trades*100:.1f}%")
        print(f"    期間: {sim['time'].iloc[0].date()} ~ {sim['time'].iloc[-1].date()} ({years:.1f}年)")

    # 月次集計 (fixed のみ)
    print("\n  [年別収益 (固定1%リスク)]")
    sim_fix = sims["fixed"].copy()
    sim_fix["year"] = sim_fix["time"].dt.year
    yearly = sim_fix.groupby("year").agg(
        net_pct=("pnl_dollar", lambda x: x.sum() / args.initial * 100),
        n=("pnl_dollar", "count"),
        eq_end=("equity", "last"),
    ).reset_index()
    for _, r in yearly.iterrows():
        bar = "█" * max(int(abs(r["net_pct"]) / 2), 1)
        sign = "+" if r["net_pct"] >= 0 else ""
        print(f"    {int(r['year'])}: {sign}{r['net_pct']:6.1f}%  資金${r['eq_end']:>10,.0f}  取引{int(r['n']):>3}  {bar}")

    # =====================================================
    # 2. モンテカルロ分析
    # =====================================================
    print("\n" + "=" * 100)
    print("【分析2】 モンテカルロ連敗分析 (5000パス)")
    print("=" * 100)
    pnl_arr = np.array([t.pnl_r for t in all_trades])
    mc = monte_carlo(pnl_arr, n_paths=5000, risk_pct=args.risk_pct, initial=args.initial)
    print(f"\n  リターン分布 (10年運用後):")
    print(f"    中央値: {mc['median_return_pct']:+.1f}%")
    print(f"    平均:   {mc['mean_return_pct']:+.1f}%")
    print(f"    P5  (悪い5%): {mc['p5_return']:+.1f}%")
    print(f"    P95 (良い5%): {mc['p95_return']:+.1f}%")
    print(f"  最大ドローダウン分布:")
    print(f"    中央値: {mc['median_dd']:.1f}%")
    print(f"    P95 (悪い5%): {mc['p95_dd']:.1f}%")
    print(f"    最悪のパスで観測: {mc['max_dd_seen']:.1f}%")
    print(f"  元本割れで終わる確率: {mc['loser_rate']:.1f}% (10年で)")

    # 異なるリスク%での感度
    print("\n  [リスク%感度: 同じトレード列で異なるリスクサイズ]")
    print(f"  {'risk%':>6}  {'中央値Ret':>10}  {'P5 Ret':>10}  {'中央DD':>8}  {'P95 DD':>8}  {'元本割れ確率':>12}")
    for rp in [0.5, 1.0, 1.5, 2.0, 3.0]:
        m = monte_carlo(pnl_arr, n_paths=2000, risk_pct=rp, initial=args.initial)
        print(f"  {rp:>5.1f}%  {m['median_return_pct']:>+9.1f}%  {m['p5_return']:>+9.1f}%  "
              f"{m['median_dd']:>7.1f}%  {m['p95_dd']:>7.1f}%  {m['loser_rate']:>11.1f}%")

    # =====================================================
    # 3. 通貨間相関
    # =====================================================
    print("\n" + "=" * 100)
    print("【分析3】 5通貨の月次R相関")
    print("=" * 100)
    corr = correlation_analysis(by_inst)
    if not corr.empty:
        print(corr.to_string(float_format=lambda x: f"{x:+.2f}"))
        # 平均相関
        n = len(corr)
        sum_corr = (corr.sum().sum() - n) / (n * (n - 1))
        print(f"\n  平均ペア相関: {sum_corr:.2f}")
        if sum_corr < 0.3:
            verdict = "✅ 真の分散効果あり (低相関)"
        elif sum_corr < 0.5:
            verdict = "△ ある程度分散される (中相関)"
        else:
            verdict = "⚠️ 同時に動きやすい (高相関、分散効果薄い)"
        print(f"  判定: {verdict}")

    # 5通貨ポートフォリオの実効リスク
    # 同時保有が起きる頻度
    print("\n  [同時保有の頻度測定]")
    # 各トレードの保有期間中、他の通貨でいくつポジ取っていたか
    # 単純化: トレードの時刻を日次に丸めて、同日に何通貨でポジっていたか
    df_t = pd.DataFrame([{"date": t.entry_time.date(), "inst": t.inst} for t in all_trades])
    daily = df_t.groupby("date")["inst"].nunique()
    multi_pos_days = (daily >= 2).sum()
    print(f"    複数通貨ポジ日数: {multi_pos_days} / {len(daily)}日 ({multi_pos_days/len(daily)*100:.1f}%)")
    print(f"    最大同時通貨数: {daily.max()}")

    # =====================================================
    # 4. サイジング比較サマリー
    # =====================================================
    print("\n" + "=" * 100)
    print("【分析4】 サイジング 3 種類の最終比較")
    print("=" * 100)
    print(f"\n  {'方式':22}  {'最終資金':>13}  {'リターン':>10}  {'CAGR':>7}  {'最大DD':>7}")
    for s in sizings:
        sim = sims[s]
        final = sim["equity"].iloc[-1]
        ret = (final - args.initial) / args.initial * 100
        years = (sim["time"].iloc[-1] - sim["time"].iloc[0]).days / 365.25
        cagr = ((final / args.initial) ** (1 / years) - 1) * 100 if years > 0 else 0
        dd = sim["dd_pct"].max()
        print(f"  {sizing_labels[s]:22}  ${final:>12,.0f}  {ret:>+9.1f}%  {cagr:>6.1f}%  {dd:>6.1f}%")

    # =====================================================
    # 最終判断
    # =====================================================
    print("\n" + "=" * 100)
    print("【最終判断】")
    print("=" * 100)
    best_sim = max(sims.items(), key=lambda x: x[1]["equity"].iloc[-1])
    final = best_sim[1]["equity"].iloc[-1]
    ret = (final - args.initial) / args.initial * 100
    years = (best_sim[1]["time"].iloc[-1] - best_sim[1]["time"].iloc[0]).days / 365.25
    cagr = ((final / args.initial) ** (1 / years) - 1) * 100
    print(f"  ✅ ベスト・サイジング: {sizing_labels[best_sim[0]]}")
    print(f"  ✅ 10年間でリターン: +{ret:.1f}% (CAGR {cagr:.1f}%)")
    print(f"  ✅ 最大DD: {best_sim[1]['dd_pct'].max():.1f}%")
    print(f"\n  推奨リスク%: {args.risk_pct}%")
    print(f"  モンテカルロでの破綻確率: {mc['loser_rate']:.1f}%")
    print(f"  モンテカルロでのP5リターン (悪いケース): {mc['p5_return']:+.1f}%")


if __name__ == "__main__":
    main()

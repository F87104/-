"""
本番運用前の最終チェックリスト

実装前に確認すべき重要メトリクス:
  1. リスク調整リターン (Sharpe / Sortino / Calmar)
  2. 連敗統計 (最大連敗、連敗からの回復時間)
  3. ローリング6ヶ月の最悪パフォーマンス (実運用時のメンタル想定)
  4. 時間帯別パフォーマンス (どの時間に強い・弱い)
  5. 曜日別パフォーマンス (運用時間の最適化)
  6. ストラテジー劣化チェック (年代別の期待値推移)
  7. コスト・ストレステスト (スプレッド1.5x, 2x 想定)
  8. MAE/MFE分析 (含み損益の最大幅)
  9. 月別損益分布 (連敗月の頻度)
 10. 時間効率 (相場参加率、平均保有時間)
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np
import pandas as pd

from sai_backtest import load_instrument
from optimize_trendbreak import TBConfig, BASE
from trendbreak_backtest import compute_signals as compute_signals_tb
from audit import SPREAD, SLIPPAGE
from portfolio_analysis import Trade, generate_trades, compound_sim


# ============================================================
# 拡張トレード生成 (MAE/MFE と保有時間も計測)
# ============================================================
def generate_trades_with_mae(name: str, df: pd.DataFrame, cfg: TBConfig,
                              spread_mult: float = 1.0) -> list[dict]:
    sig = compute_signals_tb(df, {
        "lookback_3m": cfg.lookback_3m, "exclude": cfg.exclude,
        "sl_atr": cfg.sl_atr, "tp_rr": cfg.tp_rr, "level_kind": cfg.level_kind,
        "session": cfg.session, "asia": cfg.asia, "eu": cfg.eu, "ny": cfg.ny,
        "margin": cfg.margin, "cooldown": cfg.cooldown,
    })
    spread = SPREAD.get(name, 0.0) * spread_mult
    slip = SLIPPAGE.get(name, 0.0) * spread_mult
    ci = spread / 2 + slip
    co = spread / 2 + slip

    o = sig["open"].to_numpy(); h = sig["high"].to_numpy()
    l = sig["low"].to_numpy(); c = sig["close"].to_numpy()
    a = sig["atr"].to_numpy()
    ls = sig["long_sig"].to_numpy(); ss = sig["short_sig"].to_numpy()
    idx = sig.index
    n = len(sig)

    trades = []
    in_pos_until = -1; cooldown_until = -1
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

        mae = 0.0  # Maximum Adverse Excursion (最悪含み損 R単位)
        mfe = 0.0  # Maximum Favorable Excursion (最大含み益 R単位)
        for j in range(eb, n):
            cur_low = (l[j] - entry) / sd if is_long else (entry - h[j]) / sd
            cur_high = (h[j] - entry) / sd if is_long else (entry - l[j]) / sd
            mae = min(mae, cur_low)
            mfe = max(mfe, cur_high)
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
                trades.append({
                    "inst": name, "entry_time": idx[i], "exit_time": idx[j],
                    "direction": "long" if is_long else "short",
                    "pnl_r": pnl / sd, "mae": mae, "mfe": mfe,
                    "bars_held": j - eb, "hour": idx[i].hour,
                    "dow": idx[i].dayofweek, "year": idx[i].year,
                    "ym": idx[i].strftime("%Y-%m"),
                })
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    return trades


# ============================================================
# メトリクス計算
# ============================================================
def streak_stats(pnl_r: np.ndarray) -> dict:
    """連勝/連敗の統計"""
    streaks_win = []
    streaks_loss = []
    cur_win = 0; cur_loss = 0
    for r in pnl_r:
        if r > 0:
            cur_win += 1
            if cur_loss > 0: streaks_loss.append(cur_loss); cur_loss = 0
        else:
            cur_loss += 1
            if cur_win > 0: streaks_win.append(cur_win); cur_win = 0
    if cur_win > 0: streaks_win.append(cur_win)
    if cur_loss > 0: streaks_loss.append(cur_loss)
    return {
        "max_win_streak": max(streaks_win) if streaks_win else 0,
        "max_loss_streak": max(streaks_loss) if streaks_loss else 0,
        "avg_win_streak": float(np.mean(streaks_win)) if streaks_win else 0,
        "avg_loss_streak": float(np.mean(streaks_loss)) if streaks_loss else 0,
        "p95_loss_streak": float(np.percentile(streaks_loss, 95)) if streaks_loss else 0,
    }


def calc_ratios(equity_curve: np.ndarray, periods_per_year: int = 252) -> dict:
    """Sharpe / Sortino / Calmar"""
    returns = np.diff(equity_curve) / equity_curve[:-1]
    if len(returns) < 2:
        return {"sharpe": 0, "sortino": 0, "calmar": 0}
    mean_r = returns.mean()
    std_r = returns.std()
    sharpe = mean_r / std_r * np.sqrt(periods_per_year) if std_r > 0 else 0
    downside = returns[returns < 0]
    sortino = mean_r / downside.std() * np.sqrt(periods_per_year) if len(downside) > 1 else 0
    # Calmar: 年率/最大DD
    cagr = (equity_curve[-1] / equity_curve[0]) ** (periods_per_year / len(returns)) - 1
    peak = np.maximum.accumulate(equity_curve)
    dd = (peak - equity_curve) / peak
    max_dd = dd.max()
    calmar = cagr / max_dd if max_dd > 0 else 0
    return {"sharpe": float(sharpe), "sortino": float(sortino),
            "calmar": float(calmar), "cagr": float(cagr * 100)}


def rolling_dd_recovery(equity: pd.Series) -> dict:
    """ドローダウンからの回復時間"""
    peak = equity.cummax()
    in_dd = equity < peak
    # 連続DD期間
    blocks = []
    cur_start = None
    for i, (t, flag) in enumerate(in_dd.items()):
        if flag and cur_start is None:
            cur_start = i
        elif not flag and cur_start is not None:
            blocks.append((cur_start, i, i - cur_start))
            cur_start = None
    if cur_start is not None:
        blocks.append((cur_start, len(in_dd), len(in_dd) - cur_start))
    if not blocks:
        return {"longest_dd_trades": 0, "median_dd_trades": 0}
    durations = [b[2] for b in blocks]
    return {
        "longest_dd_trades": max(durations),
        "median_dd_trades": int(np.median(durations)),
        "avg_dd_trades": int(np.mean(durations)),
    }


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
    print("【本番運用 前 最終チェック】 10項目の重要メトリクス")
    print("=" * 100)

    # 全トレード生成 (MAE/MFE 込み)
    print("\n[ロード] 全トレード生成中...")
    all_trades_raw = []
    for name in args.instruments:
        try:
            df = load_instrument(name)
        except Exception as e:
            print(f"  [SKIP] {name}: {e}")
            continue
        cfg = BASE[name]
        ts = generate_trades_with_mae(name, df, cfg)
        all_trades_raw.extend(ts)
    df_all = pd.DataFrame(all_trades_raw).sort_values("entry_time").reset_index(drop=True)
    print(f"  全トレード: {len(df_all)}")

    pnl_r = df_all["pnl_r"].to_numpy()

    # 複利エクイティカーブ (固定1%)
    trades_obj = [Trade(t["inst"], pd.to_datetime(t["entry_time"]),
                        pd.to_datetime(t["exit_time"]), t["direction"],
                        t["pnl_r"], 0, 0) for t in all_trades_raw]
    trades_obj.sort(key=lambda t: t.entry_time)
    sim = compound_sim(trades_obj, args.initial, args.risk_pct, "fixed")
    equity = sim["equity"].to_numpy()

    # =====================================================
    # 1. リスク調整リターン
    # =====================================================
    print("\n" + "=" * 100)
    print("【1】 リスク調整リターン (Sharpe / Sortino / Calmar)")
    print("=" * 100)
    ratios = calc_ratios(equity, periods_per_year=int(len(equity) / 12.5))
    print(f"  Sharpe比率:  {ratios['sharpe']:.2f}  " + (
        "✅ 優秀 (>1.0)" if ratios['sharpe'] > 1.0 else
        "△ 平均的 (0.5-1.0)" if ratios['sharpe'] > 0.5 else
        "⚠️ 弱い (<0.5)"))
    print(f"  Sortino比率: {ratios['sortino']:.2f}  " + (
        "✅ 優秀 (>1.5)" if ratios['sortino'] > 1.5 else
        "△ 平均的"))
    print(f"  Calmar比率:  {ratios['calmar']:.2f}  " + (
        "✅ 優秀 (>0.5)" if ratios['calmar'] > 0.5 else
        "△ 平均的"))
    print(f"  CAGR: {ratios['cagr']:.1f}%")
    print(f"  参考: SP500 のSharpe ≈ 0.4, 機関ヘッジファンドで 1.0 が良い水準")

    # =====================================================
    # 2. 連勝/連敗統計
    # =====================================================
    print("\n" + "=" * 100)
    print("【2】 連勝/連敗統計 (最悪を覚悟するため)")
    print("=" * 100)
    st = streak_stats(pnl_r)
    print(f"  最大連勝: {st['max_win_streak']}回")
    print(f"  最大連敗: {st['max_loss_streak']}回  ⚠️ 心の準備をすべき数字")
    print(f"  平均連敗: {st['avg_loss_streak']:.1f}回")
    print(f"  P95 連敗 (悪い5%): {st['p95_loss_streak']:.1f}回")
    print(f"\n  → リスク1%なら、{st['max_loss_streak']}連敗で口座 {(1-0.01)**st['max_loss_streak']*100:.1f}% に下落")
    print(f"  → これは「絶対起きる」想定")

    # =====================================================
    # 3. ローリング6ヶ月最悪
    # =====================================================
    print("\n" + "=" * 100)
    print("【3】 最悪の連続6ヶ月パフォーマンス (実運用での精神的負荷)")
    print("=" * 100)
    df_all["ym"] = pd.to_datetime(df_all["entry_time"]).dt.to_period("M")
    monthly_r = df_all.groupby("ym")["pnl_r"].sum().sort_index()
    rolling_6m = monthly_r.rolling(6).sum()
    print(f"  最悪 6ヶ月: {rolling_6m.min():+.2f}R (期間 {rolling_6m.idxmin()})")
    print(f"  最良 6ヶ月: {rolling_6m.max():+.2f}R (期間 {rolling_6m.idxmax()})")
    print(f"  中央値 6ヶ月: {rolling_6m.median():+.2f}R")
    neg_6m = (rolling_6m < 0).sum()
    total_6m = rolling_6m.dropna().shape[0]
    print(f"  マイナス6ヶ月の回数: {neg_6m} / {total_6m} ({neg_6m/total_6m*100:.1f}%)")

    # =====================================================
    # 4. 時間帯別パフォーマンス
    # =====================================================
    print("\n" + "=" * 100)
    print("【4】 時間帯別パフォーマンス (UTC基準)")
    print("=" * 100)
    hourly = df_all.groupby("hour")["pnl_r"].agg(["count", "mean", "sum"])
    hourly["wr"] = df_all.groupby("hour")["pnl_r"].apply(lambda s: (s > 0).mean() * 100)
    print(f"  {'時刻(UTC)':>10}  {'取引':>4}  {'勝率':>6}  {'平均R':>7}  {'合計R':>7}  {'JST':>5}")
    for h, row in hourly.iterrows():
        jst = (h + 9) % 24
        bar = "+" * max(int(row["sum"]), 0) or "-" * max(int(-row["sum"]), 0)
        print(f"  {h:>9}h  {int(row['count']):>4}  {row['wr']:>5.1f}%  "
              f"{row['mean']:>+6.2f}R  {row['sum']:>+6.1f}R  {jst:>4}h  {bar[:30]}")

    # =====================================================
    # 5. 曜日別
    # =====================================================
    print("\n" + "=" * 100)
    print("【5】 曜日別 (0=月, 4=金)")
    print("=" * 100)
    dow_names = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 6: "日"}
    dow = df_all.groupby("dow")["pnl_r"].agg(["count", "mean", "sum"])
    dow["wr"] = df_all.groupby("dow")["pnl_r"].apply(lambda s: (s > 0).mean() * 100)
    for d, row in dow.iterrows():
        print(f"  {dow_names.get(d, str(d)):>3}  取引{int(row['count']):>4}  "
              f"勝率{row['wr']:>5.1f}%  平均{row['mean']:>+6.2f}R  合計{row['sum']:>+6.1f}R")

    # =====================================================
    # 6. ストラテジー劣化チェック (年代別期待値)
    # =====================================================
    print("\n" + "=" * 100)
    print("【6】 ストラテジー劣化チェック (年別期待値の推移)")
    print("=" * 100)
    yearly = df_all.groupby("year").agg(
        n=("pnl_r", "count"),
        wr=("pnl_r", lambda s: (s > 0).mean() * 100),
        exp=("pnl_r", "mean"),
        net=("pnl_r", "sum"),
    )
    for y, row in yearly.iterrows():
        sig = "" if row["exp"] > 0 else " ⚠️"
        print(f"  {y}  n={int(row['n']):>3}  WR={row['wr']:>5.1f}%  期待値={row['exp']:>+.3f}R  Net={row['net']:>+6.1f}R{sig}")
    # 線形回帰で劣化検出
    years = yearly.index.values.astype(float)
    exps = yearly["exp"].values
    if len(years) > 3:
        slope = np.polyfit(years, exps, 1)[0]
        verdict = "✅ 改善中" if slope > 0.005 else "✅ 安定" if abs(slope) < 0.005 else "⚠️ 劣化中"
        print(f"\n  期待値トレンド: 年あたり {slope:+.4f}R / 判定: {verdict}")

    # =====================================================
    # 7. コスト・ストレステスト
    # =====================================================
    print("\n" + "=" * 100)
    print("【7】 コスト・ストレステスト (スプレッド拡大時の生存性)")
    print("=" * 100)
    for sm in [1.0, 1.5, 2.0, 3.0]:
        all_t = []
        for name in args.instruments:
            try:
                df = load_instrument(name)
            except:
                continue
            cfg = BASE[name]
            ts = generate_trades_with_mae(name, df, cfg, spread_mult=sm)
            all_t.extend([t["pnl_r"] for t in ts])
        if all_t:
            net = sum(all_t)
            wins = sum(1 for r in all_t if r > 0)
            wr = wins / len(all_t) * 100
            print(f"  スプレッド×{sm:.1f}  Net={net:+6.1f}R  WR={wr:.1f}%  取引{len(all_t)}")

    # =====================================================
    # 8. MAE/MFE 分析
    # =====================================================
    print("\n" + "=" * 100)
    print("【8】 MAE/MFE 分析 (含み損益の最大幅 → SL/TP最適化のヒント)")
    print("=" * 100)
    print(f"  MAE (最大含み損 R単位):")
    print(f"    中央値: {df_all['mae'].median():.2f}R")
    print(f"    P95 (悪い5%): {df_all['mae'].quantile(0.05):.2f}R")
    print(f"    最悪: {df_all['mae'].min():.2f}R")
    print(f"  MFE (最大含み益 R単位):")
    print(f"    中央値: {df_all['mfe'].median():.2f}R")
    print(f"    P95 (良い5%): {df_all['mfe'].quantile(0.95):.2f}R")
    print(f"    最大: {df_all['mfe'].max():.2f}R")
    print(f"\n  示唆:")
    print(f"  - 勝ちトレードでMFE中央値が3.0R近ければ → 固定TP正解")
    print(f"  - 負けトレードのMAEで戻れた率があるなら → BEストップが効く可能性")
    wins_df = df_all[df_all["pnl_r"] > 0]
    losses_df = df_all[df_all["pnl_r"] <= 0]
    print(f"  勝ちのMFE中央値: {wins_df['mfe'].median():.2f}R  (TP=3.0が妥当か?)")
    print(f"  負けのMAE中央値: {losses_df['mae'].median():.2f}R")
    near_be = losses_df[(losses_df["mfe"] >= 0.5)]
    print(f"  負けトレードのうち、+0.5R以上に伸びたケース: {len(near_be)}/{len(losses_df)} ({len(near_be)/len(losses_df)*100:.1f}%)")
    near_be1 = losses_df[(losses_df["mfe"] >= 1.0)]
    print(f"  負けトレードのうち、+1.0R以上に伸びたケース: {len(near_be1)}/{len(losses_df)} ({len(near_be1)/len(losses_df)*100:.1f}%)")

    # =====================================================
    # 9. 月別損益分布
    # =====================================================
    print("\n" + "=" * 100)
    print("【9】 月別損益分布 (連敗月の頻度)")
    print("=" * 100)
    monthly = monthly_r.values
    n_pos = (monthly > 0).sum()
    n_neg = (monthly < 0).sum()
    n_zero = (monthly == 0).sum()
    total = len(monthly)
    print(f"  期間: {total}ヶ月")
    print(f"  プラス月: {n_pos} ({n_pos/total*100:.1f}%)")
    print(f"  マイナス月: {n_neg} ({n_neg/total*100:.1f}%)")
    print(f"  ゼロ月: {n_zero}")
    print(f"  最良月: {monthly.max():+.2f}R")
    print(f"  最悪月: {monthly.min():+.2f}R")
    # 連続マイナス月
    consec_neg = 0; max_consec_neg = 0
    for v in monthly:
        if v < 0:
            consec_neg += 1; max_consec_neg = max(max_consec_neg, consec_neg)
        else:
            consec_neg = 0
    print(f"  最大連続マイナス月: {max_consec_neg}ヶ月  (これだけは耐える覚悟)")

    # =====================================================
    # 10. 時間効率
    # =====================================================
    print("\n" + "=" * 100)
    print("【10】 時間効率 (相場参加率, 平均保有時間)")
    print("=" * 100)
    total_bars = df_all["bars_held"].sum()
    avg_bars = df_all["bars_held"].mean()
    median_bars = df_all["bars_held"].median()
    # 全H1足の年数: 12.5年 × 365.25 × 24 ≒ 109,500 本
    total_period_bars = 12.5 * 365.25 * 24
    exposure_pct = total_bars / total_period_bars * 100
    print(f"  平均保有時間: {avg_bars:.1f}バー ({avg_bars:.0f}時間 = {avg_bars/24:.1f}日)")
    print(f"  中央値保有時間: {median_bars:.0f}バー ({median_bars:.0f}時間)")
    print(f"  相場参加率 (5通貨合計): {exposure_pct:.1f}% (残り{100-exposure_pct:.1f}%は休み)")
    print(f"  → 過剰取引ではなく、間欠的にしか動かない健康な戦略")


if __name__ == "__main__":
    main()

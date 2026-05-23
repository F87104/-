"""ポジション保有期間の詳細分析"""
from __future__ import annotations
import numpy as np
import pandas as pd

from sai_backtest import load_instrument
from optimize_trendbreak import BASE
from deployment_check import generate_trades_with_mae


def main():
    instruments = ["XAUUSD", "USDJPY", "GBPJPY", "CHFJPY", "AUDJPY"]
    all_trades = []
    for name in instruments:
        try:
            df = load_instrument(name)
        except Exception as e:
            print(f"  [SKIP] {name}: {e}"); continue
        ts = generate_trades_with_mae(name, df, BASE[name])
        all_trades.extend(ts)
    df = pd.DataFrame(all_trades)

    # H1なのでbars=hours
    df["hours"] = df["bars_held"].astype(float)
    df["days"] = df["hours"] / 24.0
    df["is_win"] = df["pnl_r"] > 0
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    # 実時間 (週末ギャップ含む実カレンダー時間)
    df["calendar_hours"] = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 3600
    df["calendar_days"] = df["calendar_hours"] / 24.0

    print("=" * 90)
    print("【ポジション保有期間 詳細分析】 (全 {} トレード, 12.5年)".format(len(df)))
    print("=" * 90)

    # ==================================================
    # 1. 全体統計
    # ==================================================
    print("\n■ 全体統計 (H1足ベース = 市場時間)")
    print(f"  平均保有: {df['hours'].mean():>6.1f} 時間 ({df['days'].mean():>5.2f} 日)")
    print(f"  中央値  : {df['hours'].median():>6.1f} 時間 ({df['days'].median():>5.2f} 日)")
    print(f"  最短    : {df['hours'].min():>6.0f} 時間")
    print(f"  最長    : {df['hours'].max():>6.0f} 時間 ({df['hours'].max()/24:>5.1f} 日)")

    print("\n■ 全体統計 (カレンダー実時間 = 週末ギャップ含む)")
    print(f"  平均保有: {df['calendar_hours'].mean():>6.1f} 時間 ({df['calendar_days'].mean():>5.2f} 日)")
    print(f"  中央値  : {df['calendar_hours'].median():>6.1f} 時間 ({df['calendar_days'].median():>5.2f} 日)")
    print(f"  最長    : {df['calendar_hours'].max():>6.0f} 時間 ({df['calendar_days'].max():>5.1f} 日)")

    # ==================================================
    # 2. 勝ち vs 負けで分けて
    # ==================================================
    print("\n■ 勝ち / 負けで比較")
    wins = df[df["is_win"]]
    losses = df[~df["is_win"]]
    print(f"  勝ちトレード ({len(wins)}件):")
    print(f"    平均  : {wins['hours'].mean():>6.1f} 時間 ({wins['days'].mean():>5.2f} 日)")
    print(f"    中央値: {wins['hours'].median():>6.1f} 時間 ({wins['days'].median():>5.2f} 日)")
    print(f"  負けトレード ({len(losses)}件):")
    print(f"    平均  : {losses['hours'].mean():>6.1f} 時間 ({losses['days'].mean():>5.2f} 日)")
    print(f"    中央値: {losses['hours'].median():>6.1f} 時間 ({losses['days'].median():>5.2f} 日)")
    print(f"  → 勝ちトレードのほうが {wins['hours'].mean()/losses['hours'].mean():.1f}x 長く保有")

    # ==================================================
    # 3. 通貨ペア別
    # ==================================================
    print("\n■ 通貨ペア別")
    print(f"  {'通貨':<8}  {'件数':>4}  {'平均(h)':>7}  {'中央値(h)':>9}  {'平均(日)':>7}  {'最長(日)':>7}")
    for inst, sub in df.groupby("inst"):
        print(f"  {inst:<8}  {len(sub):>4}  {sub['hours'].mean():>6.1f}  {sub['hours'].median():>8.1f}  "
              f"{sub['days'].mean():>6.2f}  {sub['days'].max():>6.1f}")

    # ==================================================
    # 4. 分布
    # ==================================================
    print("\n■ 保有時間の分布")
    bins = [0, 1, 3, 6, 12, 24, 48, 72, 168, 336, 10000]
    labels = ["≤1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-2d", "2-3d", "3-7d", "7-14d", "14d+"]
    df["bucket"] = pd.cut(df["hours"], bins=bins, labels=labels, right=True)
    dist = df.groupby("bucket", observed=True).agg(
        n=("hours", "count"),
        wr=("is_win", lambda s: s.mean() * 100),
        avg_r=("pnl_r", "mean"),
    )
    total = len(df)
    print(f"  {'保有時間':<10}  {'件数':>4}  {'割合':>6}  {'勝率':>6}  {'平均R':>7}")
    for b, row in dist.iterrows():
        pct = row["n"] / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {str(b):<10}  {int(row['n']):>4}  {pct:>5.1f}%  {row['wr']:>5.1f}%  {row['avg_r']:>+6.2f}R  {bar}")

    # ==================================================
    # 5. パーセンタイル
    # ==================================================
    print("\n■ パーセンタイル (どこまで耐える必要があるか)")
    for p in [50, 70, 80, 90, 95, 99]:
        v = df["hours"].quantile(p / 100)
        print(f"  {p:>2}%タイル: {v:>5.1f} 時間 ({v/24:>4.1f} 日)")

    # ==================================================
    # 6. 週末持ち越し率
    # ==================================================
    print("\n■ 週末持ち越し率 (金曜エントリーで月曜まで持つ確率)")
    weekend = df["calendar_hours"] - df["hours"]
    n_weekend = (weekend >= 48).sum()  # 48時間以上のギャップ = 週末持ち越し
    print(f"  週末持ち越しトレード: {n_weekend} / {len(df)} ({n_weekend/len(df)*100:.1f}%)")

    # ==================================================
    # 7. 同時保有数
    # ==================================================
    print("\n■ 同時保有ポジション数 (運用負荷)")
    # 簡易: 各時点で「エントリ済 < 現在 < 決済」のトレード数を計算
    events = []
    for _, r in df.iterrows():
        events.append((r["entry_time"], 1))
        events.append((r["exit_time"], -1))
    events.sort()
    cur = 0; max_cur = 0; hist = []
    for t, d in events:
        cur += d
        max_cur = max(max_cur, cur)
        hist.append(cur)
    hist = np.array(hist)
    print(f"  最大同時保有: {max_cur} ポジション")
    print(f"  平均同時保有: {hist.mean():.2f} ポジション")
    print(f"  P95 (悪い5%) : {np.percentile(hist, 95):.0f} ポジション")

    # ==================================================
    # まとめ
    # ==================================================
    print("\n" + "=" * 90)
    print("【サマリー】")
    print("=" * 90)
    print(f"  ✅ 平均保有: 約 {df['days'].mean():.1f} 日 (中央値 {df['days'].median():.2f} 日)")
    print(f"  ✅ 大半 (70%) は {df['hours'].quantile(0.7):.0f} 時間以内に決着")
    print(f"  ✅ 最長でも {df['days'].max():.1f} 日 (TP届かない場合の Margin期限)")
    print(f"  → 「スイング寄りデイトレ」の挙動。デイトレほど忙しくなく、")
    print(f"     スイングほど長期間ポジションを抱えない")


if __name__ == "__main__":
    main()

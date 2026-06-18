#!/usr/bin/env python3
"""
Market Psychology Research Framework — 生OHLCからの再現性検証 (from scratch)

目的:
    事前計算済みトレードの分析ではなく、生のH1 OHLCから自前のエンジンで
    心理構造を検出・バックテストし、フレームワークの中心的発見を独立に再現する。

検証する構造 (上下対称に同一エンジンで実装):
    LONG  = Short Squeeze:  急落 -> 安値棚(圧縮) -> 棚を上抜け(踏み上げ点火)
    SHORT = Long Liquidation: 急騰 -> 高値棚(圧縮) -> 棚を下抜け(投げ点火)

設計方針 (フレームワーク思想に忠実):
    - PF最適化はしない。説明可能な丸めたデフォルト値のみ使用。
    - 先読みバイアス排除: シグナルは確定足のみ、エントリは次足始値、
      SL/TPは後続足の高安で判定 (同一足両ヒットは保守的にSL優先)。
    - ロングとショートは符号反転の同一ロジック (対称性を厳密に担保)。

データ:
    環境変数 MPR_DATA_DIR (既定 /tmp/f87104_data) 配下の MT形式 H1 CSV。
    列: <TICKER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>
"""
from __future__ import annotations

import os
import glob
import math
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(os.environ.get("MPR_DATA_DIR", "/tmp/f87104_data"))
OUT_DIR = Path(__file__).resolve().parent

FX_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER", "AUDJPY"]
INDEX_SYMBOLS = ["NAS100", "SPX500"]

# --- 構造パラメータ (丸めたデフォルト / 最適化なし) -------------------------
ATR_N = 14
SHELF_BARS = 6          # 棚(蓄積レンジ)の本数
DROP_WINDOW = 6         # 棚に入る直前の急変を測る窓
SHELF_ATR_MULT = 2.5    # 棚レンジ <= 2.5*ATR を「圧縮」とみなす
MOVE_ATR = 3.0          # 棚へ 3*ATR 以上の急変で入った
RR = 2.0                # 利益確定 = 2R
MAX_HOLD = 120          # 最大保有 H4本数
STOP_BUF_ATR = 0.25     # ストップのバッファ
COST_R = 0.04           # 概算コスト(往復) R。clean と after-cost 両方を報告

IS_END_YEAR = 2024      # IS: 2015-2024 / OOS: 2025-2026
OOS_START_YEAR = 2025


def load_h1() -> pd.DataFrame:
    """H1 CSV を全て読み、<TICKER>列でシンボルを割り当て、重複排除して返す。"""
    files = []
    for p in glob.glob(str(DATA_DIR / "**" / "*.csv"), recursive=True):
        name = os.path.basename(p).upper()
        if "M5" in name or "M15" in name or "M1_" in name:
            continue
        if "H1" not in name:
            continue
        files.append(p)
    frames = []
    for p in files:
        try:
            d = pd.read_csv(p)
        except Exception:
            continue
        d.columns = [c.strip("<>").upper() for c in d.columns]
        if not {"TICKER", "DTYYYYMMDD", "TIME", "OPEN", "HIGH", "LOW", "CLOSE"}.issubset(d.columns):
            continue
        d["dt"] = pd.to_datetime(
            d["DTYYYYMMDD"].astype(str) + d["TIME"].astype(str).str.zfill(4),
            format="%Y%m%d%H%M", errors="coerce",
        )
        d = d.dropna(subset=["dt"])
        d["symbol"] = d["TICKER"].astype(str).str.upper().str.replace("GBYJPY", "GBPJPY")
        frames.append(d[["symbol", "dt", "OPEN", "HIGH", "LOW", "CLOSE"]])
    if not frames:
        raise SystemExit(f"No H1 CSVs found under {DATA_DIR}")
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close"})
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["symbol", "dt"]).sort_values(["symbol", "dt"])
    return df


def resample_h4(h1: pd.DataFrame) -> pd.DataFrame:
    g = h1.set_index("dt")
    o = g["open"].resample("4h").first()
    h = g["high"].resample("4h").max()
    l = g["low"].resample("4h").min()
    c = g["close"].resample("4h").last()
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}).dropna()
    return out.reset_index()


def atr(df: pd.DataFrame, n: int) -> pd.Series:
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def backtest_symbol(df: pd.DataFrame, symbol: str, side: str) -> list[dict]:
    """side: 'long' (Short Squeeze) or 'short' (Long Liquidation). 完全対称。"""
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, ATR_N)
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    openp = df["open"].values
    atrv = df["atr"].values
    n = len(df)
    trades = []
    open_until = -1  # 重複ポジション防止 (このindexまでは新規シグナル禁止)

    start = SHELF_BARS + DROP_WINDOW + ATR_N + 2
    for t in range(start, n - 1):
        if t <= open_until:
            continue
        a = atrv[t]
        if not np.isfinite(a) or a <= 0:
            continue
        # 棚 = 直前 SHELF_BARS 本 [t-SHELF_BARS .. t-1]
        s0, s1 = t - SHELF_BARS, t - 1
        shelf_hi = high[s0:s1 + 1].max()
        shelf_lo = low[s0:s1 + 1].min()
        shelf_range = shelf_hi - shelf_lo
        if shelf_range > SHELF_ATR_MULT * a:
            continue  # 圧縮していない棚は対象外
        # 棚へ入る直前の急変 [t-SHELF_BARS-DROP_WINDOW .. t-SHELF_BARS-1]
        d0, d1 = t - SHELF_BARS - DROP_WINDOW, t - SHELF_BARS - 1
        if side == "long":
            prior_hi = high[d0:d1 + 1].max()
            sharp = (prior_hi - shelf_hi) >= MOVE_ATR * a  # 急落して棚へ
            fresh = close[t - 1] <= shelf_hi and close[t] > shelf_hi  # 棚を上抜け
        else:
            prior_lo = low[d0:d1 + 1].min()
            sharp = (shelf_lo - prior_lo) >= MOVE_ATR * a  # 急騰して棚へ
            fresh = close[t - 1] >= shelf_lo and close[t] < shelf_lo  # 棚を下抜け
        if not (sharp and fresh):
            continue
        # エントリは次足始値
        entry = openp[t + 1]
        if side == "long":
            stop = shelf_lo - STOP_BUF_ATR * a
            risk = entry - stop
            if risk <= 0:
                continue
            target = entry + RR * risk
        else:
            stop = shelf_hi + STOP_BUF_ATR * a
            risk = stop - entry
            if risk <= 0:
                continue
            target = entry - RR * risk
        # 後続足で決済 (同一足両ヒットは保守的にSL優先)
        r = None
        exit_reason = "timeout"
        end = min(t + 1 + MAX_HOLD, n)
        for k in range(t + 1, end):
            hi, lo = high[k], low[k]
            if side == "long":
                hit_sl = lo <= stop
                hit_tp = hi >= target
            else:
                hit_sl = hi >= stop
                hit_tp = lo <= target
            if hit_sl:
                r = -1.0
                exit_reason = "SL"
                open_until = k
                break
            if hit_tp:
                r = RR
                exit_reason = "TP"
                open_until = k
                break
        if r is None:
            # タイムアウト: 最終クローズでmark-to-R
            last = close[end - 1]
            r = ((last - entry) if side == "long" else (entry - last)) / risk
            open_until = end - 1
        trades.append(dict(
            symbol=symbol, side=side, signal_dt=df["dt"].iloc[t], entry=entry,
            r_clean=r, r_after_cost=r - COST_R, exit_reason=exit_reason,
            shelf_range_atr=shelf_range / a, year=df["dt"].iloc[t].year,
        ))
    return trades


def metrics(r: pd.Series) -> dict:
    r = pd.Series(r).astype(float).dropna()
    n = len(r)
    if n == 0:
        return dict(n=0, wr=float("nan"), avg_r=float("nan"), total_r=0.0, pf=float("nan"), max_dd=float("nan"))
    gl = -r[r < 0].sum()
    pf = r[r > 0].sum() / gl if gl > 0 else float("inf")
    eq = r.cumsum()
    dd = (eq.cummax() - eq).max()
    return dict(n=n, wr=100.0 * (r > 0).mean(), avg_r=r.mean(), total_r=r.sum(), pf=pf, max_dd=dd)


def fmt(d: dict) -> str:
    pf = "inf" if d["pf"] == float("inf") else f"{d['pf']:.2f}"
    return (f"n={d['n']:>4}  WR={d['wr']:5.1f}%  avgR={d['avg_r']:+.3f}  "
            f"totalR={d['total_r']:+8.2f}  PF={pf:>5}  maxDD={d['max_dd']:.1f}R")


lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


def main():
    out("=" * 84)
    out("Market Psychology Research — 生OHLCからの再現性検証 (from scratch / H4)")
    out("  LONG=Short Squeeze (急落->安値棚->上抜け) / SHORT=Long Liquidation (急騰->高値棚->下抜け)")
    out("=" * 84)
    out(f"params: shelf={SHELF_BARS} drop_win={DROP_WINDOW} shelf<= {SHELF_ATR_MULT}ATR "
        f"move>= {MOVE_ATR}ATR RR={RR} maxHold={MAX_HOLD} cost={COST_R}R")

    h1 = load_h1()
    syms = [s for s in FX_SYMBOLS + INDEX_SYMBOLS if s in set(h1["symbol"].unique())]
    out(f"loaded symbols: {syms}")
    cov = h1.groupby("symbol")["dt"].agg(["min", "max", "count"])
    out("data coverage (H1):")
    out(cov.loc[[s for s in syms]].to_string())

    all_trades = []
    for sym in syms:
        h4 = resample_h4(h1[h1["symbol"] == sym])
        for side in ("long", "short"):
            all_trades += backtest_symbol(h4, sym, side)
    td = pd.DataFrame(all_trades)
    td = td[(td["year"] >= 2015) & (td["year"] <= 2026)].copy()
    td["period"] = np.where(td["year"] <= IS_END_YEAR, "IS_2015_2024", "OOS_2025_2026")
    td["group"] = np.where(td["symbol"].isin(INDEX_SYMBOLS), "index", "fx")

    for grp_name, gmask in [("FX/メタル7銘柄", td["group"] == "fx"),
                            ("株価指数(NAS100/SPX500)", td["group"] == "index")]:
        sub = td[gmask]
        if sub.empty:
            continue
        out("")
        out("#" * 84)
        out(f"# {grp_name}")
        out("#" * 84)
        for side, jp in [("long", "LONG = Short Squeeze (踏み上げ)"),
                         ("short", "SHORT = Long Liquidation (投げ)")]:
            s = sub[sub["side"] == side]
            out("")
            out(f"--- {jp} ---")
            out("  IS  (2015-2024): " + fmt(metrics(s[s.period == 'IS_2015_2024']['r_after_cost'])))
            out("  OOS (2025-2026): " + fmt(metrics(s[s.period == 'OOS_2025_2026']['r_after_cost'])))
            out("  ALL after-cost : " + fmt(metrics(s['r_after_cost'])))
            out("  ALL clean      : " + fmt(metrics(s['r_clean'])))

    # 仮説: 圧縮(棚の狭さ) — FXロングで中央値二分
    fx_long = td[(td.group == "fx") & (td.side == "long")]
    if len(fx_long) > 10:
        med = fx_long["shelf_range_atr"].median()
        out("")
        out("=" * 84)
        out(f"仮説(圧縮): FX LONG 棚レンジ(ATR比) 中央値={med:.2f} で二分 — 狭いほど強いか")
        out("=" * 84)
        out("  狭い(圧縮強) <=med: " + fmt(metrics(fx_long[fx_long.shelf_range_atr <= med]['r_after_cost'])))
        out("  広い(圧縮弱) > med: " + fmt(metrics(fx_long[fx_long.shelf_range_atr > med]['r_after_cost'])))

    # 直接対比
    out("")
    out("=" * 84)
    out("対称性チェック: FX/メタル LONG vs SHORT (after-cost, ALL)")
    out("=" * 84)
    L = metrics(td[(td.group == 'fx') & (td.side == 'long')]['r_after_cost'])
    S = metrics(td[(td.group == 'fx') & (td.side == 'short')]['r_after_cost'])
    out(f"  LONG (踏み上げ): PF={L['pf']:.2f}  totalR={L['total_r']:+.1f}  WR={L['wr']:.1f}%  n={L['n']}")
    out(f"  SHORT(投げ)    : PF={S['pf']:.2f}  totalR={S['total_r']:+.1f}  WR={S['wr']:.1f}%  n={S['n']}")

    td.to_csv(OUT_DIR / "from_raw_trades.csv", index=False)
    # サマリーテーブル
    rows = []
    for grp in ["fx", "index"]:
        for side in ["long", "short"]:
            for per in ["IS_2015_2024", "OOS_2025_2026"]:
                m = metrics(td[(td.group == grp) & (td.side == side) & (td.period == per)]["r_after_cost"])
                m.update(group=grp, side=side, period=per)
                rows.append(m)
    pd.DataFrame(rows).to_csv(OUT_DIR / "from_raw_summary.csv", index=False)
    (OUT_DIR / "from_raw_report.txt").write_text("\n".join(lines), encoding="utf-8")
    out("")
    out("saved: from_raw_trades.csv, from_raw_summary.csv, from_raw_report.txt")


if __name__ == "__main__":
    main()

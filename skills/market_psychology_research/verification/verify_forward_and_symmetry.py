#!/usr/bin/env python3
"""
Market Psychology Research Framework — 前向き検証 & トレンド対称性

Part 1: 事前登録ルールの前向き検証 (後知恵バイアス排除)
    IS(2015-2024)だけで「モード」と「採用銘柄」を決め、そのルールを固定したまま
    OOS(2025-2026)で評価する。Capitulation 底買い反転が対象。

Part 2: 踏み上げ(Short Squeeze, ロング)に同じ日足トレンドフィルタを適用
    仮説: 継続構造(踏み上げ=上昇)は順張り一致(align)で改善し、
          反転構造(Capitulation=底)は逆張り(counter)で改善する、という対称性。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))
from verify_from_raw_ohlc import (  # noqa: E402
    load_h1, resample_h4, atr, metrics, fmt,
    FX_SYMBOLS, INDEX_SYMBOLS, ATR_N, IS_END_YEAR,
    SHELF_BARS, DROP_WINDOW, SHELF_ATR_MULT, MOVE_ATR, RR, MAX_HOLD, STOP_BUF_ATR, COST_R,
)
from verify_capitulation_trend_filter import daily_trend_map  # noqa: E402

lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


def pf_of(s):
    s = np.asarray(s, float)
    gl = -s[s < 0].sum()
    return s[s > 0].sum() / gl if gl > 0 else np.inf


# ====================================================================== Part 1
def part1_forward_test():
    out("=" * 84)
    out("Part 1: 事前登録ルールの前向き検証 (Capitulation 底買い反転)")
    out("  IS(2015-2024)だけでルールを決め、OOS(2025-2026)で固定評価")
    out("=" * 84)
    csv = THIS / "capitulation_trendfilter_trades.csv"
    if not csv.exists():
        out("  (capitulation_trendfilter_trades.csv が無い。先に trend_filter を実行)")
        return
    td = pd.read_csv(csv)
    isd = td[td.period == "IS_2015_2024"]
    oos = td[td.period == "OOS_2025_2026"]

    # 手順1: IS でモードを選ぶ (全銘柄集計の PF が最大のモード)
    out("\n[手順1] IS でモード選択 (全銘柄集計 PF):")
    mode_pf = {}
    for m in ["none", "align", "counter"]:
        r = isd[isd["mode"] == m]["r_after_cost"]
        mode_pf[m] = pf_of(r)
        out(f"    {m:<8}: IS PF={mode_pf[m]:.2f}  totalR={r.sum():+.1f}  n={len(r)}")
    best_mode = max(mode_pf, key=mode_pf.get)
    out(f"  => 採用モード = '{best_mode}'")

    # 手順2: 採用モード内で IS PF>=1.0 & n>=8 の銘柄だけ採用
    out(f"\n[手順2] '{best_mode}' で IS PF>=1.0 かつ IS n>=8 の銘柄を採用:")
    keep = []
    for sym, g in isd[isd["mode"] == best_mode].groupby("symbol"):
        r = g["r_after_cost"]
        p = pf_of(r)
        ok = (p >= 1.0) and (len(r) >= 8)
        out(f"    {sym:<7}: IS n={len(r):>2} PF={p:.2f} {'採用' if ok else '除外'}")
        if ok:
            keep.append(sym)
    out(f"  => 採用銘柄 = {keep}")

    # 手順3: ルール固定で OOS 評価
    out(f"\n[手順3] ルール固定で OOS(2025-2026) 前向き評価:")
    oos_rule = oos[(oos["mode"] == best_mode) & (oos["symbol"].isin(keep))]["r_after_cost"]
    out("  事前登録ルール (採用モード×採用銘柄):")
    out("    OOS : " + fmt(metrics(oos_rule)))
    out("  参考: 同モード・全銘柄 OOS:")
    out("    OOS : " + fmt(metrics(oos[oos["mode"] == best_mode]["r_after_cost"])))
    out("  参考: フィルタなし(none)・全銘柄 OOS:")
    out("    OOS : " + fmt(metrics(oos[oos["mode"] == "none"]["r_after_cost"])))
    # 念のため IS でのルール成績も
    is_rule = isd[(isd["mode"] == best_mode) & (isd["symbol"].isin(keep))]["r_after_cost"]
    out("  (参考) 同ルールの IS 成績:")
    out("    IS  : " + fmt(metrics(is_rule)))


# ====================================================================== Part 2
def run_squeeze_long(df: pd.DataFrame, symbol: str, tmap: dict, mode: str) -> list[dict]:
    """踏み上げ(ロング) + 日足トレンドゲート。verify_from_raw のロング検出と同義。"""
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, ATR_N)
    high, low, close, openp = (df[c].values for c in ("high", "low", "close", "open"))
    atrv = df["atr"].values
    dts = df["dt"].values
    n = len(df)
    trades = []
    open_until = -1
    start = SHELF_BARS + DROP_WINDOW + ATR_N + 2
    for t in range(start, n - 1):
        if t <= open_until:
            continue
        a = atrv[t]
        if not np.isfinite(a) or a <= 0:
            continue
        s0, s1 = t - SHELF_BARS, t - 1
        shelf_hi = high[s0:s1 + 1].max()
        shelf_lo = low[s0:s1 + 1].min()
        if (shelf_hi - shelf_lo) > SHELF_ATR_MULT * a:
            continue
        d0, d1 = t - SHELF_BARS - DROP_WINDOW, t - SHELF_BARS - 1
        prior_hi = high[d0:d1 + 1].max()
        sharp = (prior_hi - shelf_hi) >= MOVE_ATR * a
        fresh = close[t - 1] <= shelf_hi and close[t] > shelf_hi
        if not (sharp and fresh):
            continue
        if mode != "none":
            up = tmap.get(pd.Timestamp(dts[t]).normalize(), None)
            if up is None:
                continue
            if mode == "align" and not up:
                continue
            if mode == "counter" and up:
                continue
        entry = openp[t + 1]
        stop = shelf_lo - STOP_BUF_ATR * a
        risk = entry - stop
        if risk <= 0:
            continue
        target = entry + RR * risk
        r, reason = None, "timeout"
        end = min(t + 1 + MAX_HOLD, n)
        for k in range(t + 1, end):
            if low[k] <= stop:
                r, reason, open_until = -1.0, "SL", k
                break
            if high[k] >= target:
                r, reason, open_until = RR, "TP", k
                break
        if r is None:
            r = (close[end - 1] - entry) / risk
            open_until = end - 1
        trades.append(dict(symbol=symbol, mode=mode, r_after_cost=r - COST_R,
                           year=pd.Timestamp(dts[t]).year))
    return trades


def part2_squeeze_symmetry(h1: pd.DataFrame, syms: list[str]):
    out("")
    out("=" * 84)
    out("Part 2: 踏み上げ(Short Squeeze, ロング) × 日足トレンドフィルタ")
    out("  仮説: 継続構造の踏み上げは順張り一致(align)で改善するか")
    out("=" * 84)
    rows = []
    for sym in syms:
        sub = h1[h1["symbol"] == sym]
        h4 = resample_h4(sub)
        tmap = daily_trend_map(sub)
        for mode in ("none", "align", "counter"):
            rows += run_squeeze_long(h4, sym, tmap, mode)
    td = pd.DataFrame(rows)
    td = td[(td.year >= 2015) & (td.year <= 2026)].copy()
    td["period"] = np.where(td.year <= IS_END_YEAR, "IS_2015_2024", "OOS_2025_2026")
    td["group"] = np.where(td.symbol.isin(INDEX_SYMBOLS), "index", "fx")
    for grp, gmask in [("FX/メタル7銘柄", td.group == "fx"),
                       ("株価指数", td.group == "index"),
                       ("全銘柄", td.symbol.notna())]:
        out(f"\n### {grp} (踏み上げ ロング)")
        for mode, jp in [("none", "フィルタなし"),
                         ("align", "日足上昇一致(順張り)"),
                         ("counter", "日足下降中(逆張り)")]:
            s = td[gmask & (td["mode"] == mode)]
            out(f"  {jp:<18}: ALL " + fmt(metrics(s['r_after_cost'])))
    td.to_csv(THIS / "squeeze_trendfilter_trades.csv", index=False)

    out("")
    out("-" * 84)
    out("対称性まとめ (ALL after-cost PF): 継続(踏み上げ) vs 反転(Capitulation底買い)")
    out("-" * 84)
    cap = pd.read_csv(THIS / "capitulation_trendfilter_trades.csv")

    def allpf(df, mode):
        return pf_of(df[df["mode"] == mode]["r_after_cost"])
    out(f"  {'':<22}{'none':>8}{'align(順張り)':>16}{'counter(逆張り)':>18}")
    out(f"  {'踏み上げ(継続)':<20}{allpf(td,'none'):>8.2f}{allpf(td,'align'):>16.2f}{allpf(td,'counter'):>18.2f}")
    out(f"  {'Capit.底買い(反転)':<20}{allpf(cap,'none'):>8.2f}{allpf(cap,'align'):>16.2f}{allpf(cap,'counter'):>18.2f}")


def main():
    part1_forward_test()
    h1 = load_h1()
    syms = [s for s in FX_SYMBOLS + INDEX_SYMBOLS if s in set(h1["symbol"].unique())]
    part2_squeeze_symmetry(h1, syms)
    (THIS / "forward_symmetry_report.txt").write_text("\n".join(lines), encoding="utf-8")
    out("")
    out("saved: squeeze_trendfilter_trades.csv, forward_symmetry_report.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Market Psychology Research Framework —
Capitulation 底買い反転 × 上位足(日足)トレンド一致フィルタ 検証

問い:
    売りクライマックス反転(底買い)は資産依存のエッジで、GBPJPYなどで負けた。
    「上位足(日足)が上昇トレンドの中での押し目クライマックスだけ買う」と
    勝てない銘柄を除外でき、エッジが安定するか？

フィルタ条件 (先読みなし: その日の判定は前営業日までのデータで確定):
    - align    : 日足が上昇 (D1 close > D1 EMA50) のときだけ底買い
    - counter  : 日足が下降 のときだけ底買い (ナイフ掴み / 対照)
    - none     : フィルタなし (前回の基本ケース)

設計はフレームワーク思想に忠実 (最適化なし)。LONG(底買い)に集中。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_from_raw_ohlc import (  # noqa: E402
    load_h1, resample_h4, atr, metrics, fmt,
    FX_SYMBOLS, INDEX_SYMBOLS, ATR_N, IS_END_YEAR,
)
from verify_capitulation_reversal import (  # noqa: E402
    DECLINE_BARS, DROP_ATR, ATR_SPIKE, WICK_THR, CLOSE_LOC,
    STOP_BUF_ATR, COST_R, MAX_HOLD,
)

OUT_DIR = Path(__file__).resolve().parent
RR = 2.0
EMA_D = 50  # 日足トレンド判定 EMA


def daily_trend_map(h1_sym: pd.DataFrame) -> dict:
    """日付 -> 前営業日までで確定した日足上昇フラグ (先読みなし)。"""
    g = h1_sym.set_index("dt")
    d_close = g["close"].resample("1D").last().dropna()
    if len(d_close) < EMA_D + 2:
        return {}
    ema = d_close.ewm(span=EMA_D, adjust=False).mean()
    up = (d_close > ema)
    up_shift = up.shift(1)  # 前日までで確定したトレンド状態を当日に適用
    return {ts.normalize(): bool(v) for ts, v in up_shift.dropna().items()}


def run_long(df: pd.DataFrame, symbol: str, trend_map: dict, mode: str) -> list[dict]:
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, ATR_N)
    high, low, close, openp = (df[c].values for c in ("high", "low", "close", "open"))
    atrv = df["atr"].values
    dts = df["dt"].values
    n = len(df)
    trades = []
    open_until = -1
    start = DECLINE_BARS + ATR_N + 2
    for t in range(start, n - 1):
        if t <= open_until:
            continue
        a = atrv[t - 1]
        if not np.isfinite(a) or a <= 0:
            continue
        rng = high[t] - low[t]
        if rng <= 0:
            continue
        body_lo = min(openp[t], close[t])
        w0 = t - DECLINE_BARS
        is_extreme = low[t] <= np.min(low[w0:t + 1])
        prolonged = (np.max(high[w0:t]) - low[t]) >= DROP_ATR * a
        lower_wick = (body_lo - low[t]) / rng
        close_loc = (close[t] - low[t]) / rng
        climax = (rng >= ATR_SPIKE * a) and (lower_wick >= WICK_THR) and (close_loc >= CLOSE_LOC)
        if not (is_extreme and prolonged and climax):
            continue
        if mode != "none":
            day = pd.Timestamp(dts[t]).normalize()
            up = trend_map.get(day, None)
            if up is None:
                continue
            if mode == "align" and not up:
                continue
            if mode == "counter" and up:
                continue
        entry = openp[t + 1]
        stop = low[t] - STOP_BUF_ATR * a
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


lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


def main():
    out("=" * 84)
    out("Capitulation 底買い反転 × 日足トレンド一致フィルタ (H4, RR=2, from raw)")
    out(f"  filter: D1 close > D1 EMA{EMA_D} (先読みなし)  / LONG(底買い)のみ")
    out("=" * 84)

    h1 = load_h1()
    syms = [s for s in FX_SYMBOLS + INDEX_SYMBOLS if s in set(h1["symbol"].unique())]
    rows = []
    for sym in syms:
        sub = h1[h1["symbol"] == sym]
        h4 = resample_h4(sub)
        tmap = daily_trend_map(sub)
        for mode in ("none", "align", "counter"):
            rows += run_long(h4, sym, tmap, mode)
    td = pd.DataFrame(rows)
    td = td[(td.year >= 2015) & (td.year <= 2026)].copy()
    td["period"] = np.where(td.year <= IS_END_YEAR, "IS_2015_2024", "OOS_2025_2026")
    td["group"] = np.where(td.symbol.isin(INDEX_SYMBOLS), "index", "fx")

    for grp, gmask in [("FX/メタル7銘柄", td.group == "fx"),
                       ("株価指数(NAS100/SPX500)", td.group == "index"),
                       ("全銘柄", td.symbol.notna())]:
        out("")
        out("#" * 84)
        out(f"# {grp}")
        out("#" * 84)
        for mode, jp in [("none", "フィルタなし(基本)"),
                         ("align", "日足上昇トレンド一致(押し目だけ買う)"),
                         ("counter", "日足下降中(ナイフ掴み/対照)")]:
            s = td[(gmask) & (td["mode"] == mode)]
            out(f"  -- {jp} --")
            out("    IS  : " + fmt(metrics(s[s.period == 'IS_2015_2024']['r_after_cost'])))
            out("    OOS : " + fmt(metrics(s[s.period == 'OOS_2025_2026']['r_after_cost'])))
            out("    ALL : " + fmt(metrics(s['r_after_cost'])))

    out("")
    out("=" * 84)
    out("銘柄別: フィルタなし vs 日足一致 (ALL, after-cost)")
    out("=" * 84)

    def pf(s):
        s = np.asarray(s, float)
        gl = -s[s < 0].sum()
        return s[s > 0].sum() / gl if gl > 0 else np.inf
    for sym in syms:
        g = td[td.symbol == sym]
        none = g[g['mode'] == 'none']['r_after_cost']
        al = g[g['mode'] == 'align']['r_after_cost']
        out(f"  {sym:<7} none: n={len(none):>2} totalR={none.sum():+6.2f} PF={pf(none):.2f}"
            f"   -> align: n={len(al):>2} totalR={al.sum():+6.2f} PF={pf(al):.2f}")

    td.to_csv(OUT_DIR / "capitulation_trendfilter_trades.csv", index=False)
    (OUT_DIR / "capitulation_trendfilter_report.txt").write_text("\n".join(lines), encoding="utf-8")
    out("")
    out("saved: capitulation_trendfilter_trades.csv, capitulation_trendfilter_report.txt")


if __name__ == "__main__":
    main()

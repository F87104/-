#!/usr/bin/env python3
"""
Market Psychology Research Framework — Capitulation 型クライマックス反転 検証

背景:
    ショート側を「高値棚の下抜け継続（投げブレイク）」で獲ろうとすると負けた
    (VERIFICATION_LONG_LIQUIDATION_SHORT.md, PF 0.68-0.72)。
    そこで投げを「継続」ではなく [Capitulation](../CAPITULATION.md) の思想どおり
    「最後の投げ(クライマックス)→反転」= 逆張り反転で再定義して検証する。

検証する構造 (上下対称に同一エンジン):
    LONG  = 売りクライマックス反転:
        長期下落 -> 投げ切り(ATR急拡大+長い下ヒゲ+終値が上に戻す) -> 反転(買い)
    SHORT = 買いクライマックス反転 (対称):
        長期上昇 -> 買い尽くし(ATR急拡大+長い上ヒゲ+終値が下に戻す) -> 反転(売り)

設計 (フレームワーク思想に忠実 / 最適化なし):
    - 出来高は信頼性が低いため不使用。ATR急拡大+長いヒゲ+投げ切り戻しで代用。
    - 先読み排除: 確定足シグナル -> 次足始値エントリー -> 後続足でSL/TP判定(同足両ヒットはSL優先)。
    - LONG/SHORT は符号反転の同一ロジック。
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

OUT_DIR = Path(__file__).resolve().parent

# --- Capitulation パラメータ (丸めた既定値 / 最適化なし) ---------------------
DECLINE_BARS = 24       # 「長期間含み損」を測る窓 (H4で約4日)
DROP_ATR = 4.0          # その窓で 4*ATR 以上動いて極値を付けた = たまった含み損
ATR_SPIKE = 1.8         # クライマックス足の実体レンジ >= 1.8*ATR (ボラ急拡大)
WICK_THR = 0.50         # ヒゲ / レンジ >= 0.5 (長いヒゲ=投げ切りと即戻し)
CLOSE_LOC = 0.50        # 終値が反転方向に戻している (close location)
STOP_BUF_ATR = 0.25
COST_R = 0.04
MAX_HOLD = 120


def run(df: pd.DataFrame, symbol: str, side: str, rr: float, confirm: bool) -> list[dict]:
    """side: 'long' = 売りクライマックス反転 / 'short' = 買いクライマックス反転。"""
    df = df.reset_index(drop=True).copy()
    df["atr"] = atr(df, ATR_N)
    high, low, close, openp = (df[c].values for c in ("high", "low", "close", "open"))
    atrv = df["atr"].values
    n = len(df)
    trades = []
    open_until = -1
    start = DECLINE_BARS + ATR_N + 2

    for t in range(start, n - 2):
        if t <= open_until:
            continue
        a = atrv[t - 1]
        if not np.isfinite(a) or a <= 0:
            continue
        rng = high[t] - low[t]
        if rng <= 0:
            continue
        body_lo, body_hi = min(openp[t], close[t]), max(openp[t], close[t])
        w0, w1 = t - DECLINE_BARS, t

        if side == "long":
            # 長期下落の末に新安値クライマックス
            is_extreme = low[t] <= np.min(low[w0:w1 + 1])
            prior_high = np.max(high[w0:w1])
            prolonged = (prior_high - low[t]) >= DROP_ATR * a
            lower_wick = (body_lo - low[t]) / rng
            close_loc = (close[t] - low[t]) / rng
            climax = (rng >= ATR_SPIKE * a) and (lower_wick >= WICK_THR) and (close_loc >= CLOSE_LOC)
            ok = is_extreme and prolonged and climax
            if confirm:
                ok = ok and close[t + 1] > high[t]  # 反転確認足
        else:
            is_extreme = high[t] >= np.max(high[w0:w1 + 1])
            prior_low = np.min(low[w0:w1])
            prolonged = (high[t] - prior_low) >= DROP_ATR * a
            upper_wick = (high[t] - body_hi) / rng
            close_loc = (high[t] - close[t]) / rng
            climax = (rng >= ATR_SPIKE * a) and (upper_wick >= WICK_THR) and (close_loc >= CLOSE_LOC)
            ok = is_extreme and prolonged and climax
            if confirm:
                ok = ok and close[t + 1] < low[t]
        if not ok:
            continue

        ei = t + 2 if confirm else t + 1   # エントリ足index
        if ei >= n:
            continue
        entry = openp[ei]
        if side == "long":
            stop = low[t] - STOP_BUF_ATR * a
            risk = entry - stop
            if risk <= 0:
                continue
            target = entry + rr * risk
        else:
            stop = high[t] + STOP_BUF_ATR * a
            risk = stop - entry
            if risk <= 0:
                continue
            target = entry - rr * risk

        r, reason = None, "timeout"
        end = min(ei + MAX_HOLD, n)
        for k in range(ei, end):
            if side == "long":
                hit_sl, hit_tp = low[k] <= stop, high[k] >= target
            else:
                hit_sl, hit_tp = high[k] >= stop, low[k] <= target
            if hit_sl:
                r, reason, open_until = -1.0, "SL", k
                break
            if hit_tp:
                r, reason, open_until = rr, "TP", k
                break
        if r is None:
            last = close[end - 1]
            r = ((last - entry) if side == "long" else (entry - last)) / risk
            open_until = end - 1
        trades.append(dict(symbol=symbol, side=side, signal_dt=df["dt"].iloc[t],
                           r_clean=r, r_after_cost=r - COST_R, exit_reason=reason,
                           year=df["dt"].iloc[t].year))
    return trades


lines: list[str] = []


def out(s: str = ""):
    print(s)
    lines.append(s)


def summarize(td: pd.DataFrame, title: str):
    out("")
    out("#" * 84)
    out(f"# {title}")
    out("#" * 84)
    for grp, gmask in [("FX/メタル7銘柄", td.group == "fx"),
                       ("株価指数(NAS100/SPX500)", td.group == "index")]:
        sub = td[gmask]
        if sub.empty:
            continue
        out(f"\n=== {grp} ===")
        for side, jp in [("long", "LONG = 売りクライマックス反転(底で買い)"),
                         ("short", "SHORT = 買いクライマックス反転(天井で売り)")]:
            s = sub[sub.side == side]
            out(f"  -- {jp} --")
            out("    IS  : " + fmt(metrics(s[s.period == 'IS_2015_2024']['r_after_cost'])))
            out("    OOS : " + fmt(metrics(s[s.period == 'OOS_2025_2026']['r_after_cost'])))
            out("    ALL : " + fmt(metrics(s['r_after_cost'])))


def main():
    out("=" * 84)
    out("Market Psychology Research — Capitulation 型クライマックス反転 検証 (H4 / from raw)")
    out("=" * 84)
    out(f"params: declineWin={DECLINE_BARS} drop>= {DROP_ATR}ATR climaxRange>= {ATR_SPIKE}ATR "
        f"wick>= {WICK_THR} closeLoc>= {CLOSE_LOC} maxHold={MAX_HOLD} cost={COST_R}R")

    h1 = load_h1()
    syms = [s for s in FX_SYMBOLS + INDEX_SYMBOLS if s in set(h1["symbol"].unique())]
    h4_map = {sym: resample_h4(h1[h1["symbol"] == sym]) for sym in syms}

    # メイン: RR=2, 確認足なし
    for rr, confirm, tag in [(2.0, False, "RR=2.0 / 確認足なし (基本)"),
                             (2.0, True, "RR=2.0 / 反転確認足あり"),
                             (1.0, False, "RR=1.0 / 確認足なし (反転は早く利確)"),
                             (3.0, False, "RR=3.0 / 確認足なし")]:
        all_tr = []
        for sym in syms:
            for side in ("long", "short"):
                all_tr += run(h4_map[sym], sym, side, rr=rr, confirm=confirm)
        td = pd.DataFrame(all_tr)
        td = td[(td.year >= 2015) & (td.year <= 2026)].copy()
        td["period"] = np.where(td.year <= IS_END_YEAR, "IS_2015_2024", "OOS_2025_2026")
        td["group"] = np.where(td.symbol.isin(INDEX_SYMBOLS), "index", "fx")
        summarize(td, tag)
        if rr == 2.0 and not confirm:
            base = td.copy()

    # 銘柄別 (基本ケース, LONG=売りクライマックス反転)
    out("")
    out("=" * 84)
    out("銘柄別 (基本 RR=2 確認足なし, after-cost, ALL)")
    out("=" * 84)

    def pf(s):
        s = np.asarray(s, float)
        gl = -s[s < 0].sum()
        return s[s > 0].sum() / gl if gl > 0 else np.inf
    for sym, g in base.groupby("symbol"):
        L = g[g.side == "long"]["r_after_cost"]
        S = g[g.side == "short"]["r_after_cost"]
        out(f"  {sym:<7} 売りクライマックス反転(買): n={len(L):>2} totalR={L.sum():+6.2f} PF={pf(L):.2f}"
            f"  | 買いクライマックス反転(売): n={len(S):>2} totalR={S.sum():+6.2f} PF={pf(S):.2f}")

    base.to_csv(OUT_DIR / "capitulation_trades.csv", index=False)
    (OUT_DIR / "capitulation_report.txt").write_text("\n".join(lines), encoding="utf-8")
    out("")
    out("saved: capitulation_trades.csv, capitulation_report.txt")


if __name__ == "__main__":
    main()

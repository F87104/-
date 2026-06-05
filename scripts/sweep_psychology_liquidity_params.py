#!/usr/bin/env python3
"""
Parameter sweep: stop clusters, stop-hunt / cover, doten proxy, forward edge.

Hypothesis (user):
  損切誘発 → ショートカバー / 投げ切り → どテン集中 → その方向に短期優位

Outputs:
  docs/research/psychology_liquidity_param_sweep_2026-06-01.csv
  docs/research/psychology_liquidity_param_sweep_2026-06-01.md
"""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO / "F87104_test"
ENTRIES = REPO / "docs/research/student_entries_extracted.csv"
OUT_CSV = REPO / "docs/research/psychology_liquidity_param_sweep_2026-06-01.csv"
OUT_MD = REPO / "docs/research/psychology_liquidity_param_sweep_2026-06-01.md"


def parse_mt_h1(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    cols = {c.strip("<>").lower(): c for c in raw.columns}
    out = pd.DataFrame()
    out["time"] = pd.to_datetime(
        raw[cols["dtyyyymmdd"]].astype(str) + raw[cols["time"]].astype(str).str.zfill(4),
        format="%Y%m%d%H%M",
    )
    for k in ("open", "high", "low", "close"):
        out[k] = pd.to_numeric(raw[cols[k]], errors="coerce")
    return out.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)


def find_h1_files(symbol: str, years: list[int]) -> list[Path]:
    token = "GBY" if symbol == "GBPJPY" else symbol[:3]
    found: list[Path] = []
    for path in DATA_ROOT.rglob("*.csv"):
        if "H1" not in path.name.upper():
            continue
        if not any(str(y) in path.name for y in years):
            continue
        if token in path.name.replace(" ", "") or symbol in path.name:
            found.append(path)
    return found


def pip_size(symbol: str) -> float:
    return 0.1 if symbol == "XAUUSD" else 0.01


def load_ohlc(symbol: str, years: list[int]) -> pd.DataFrame:
    frames = [parse_mt_h1(p) for p in find_h1_files(symbol, years)]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates("time").sort_values("time")


def base_frame(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    tr = pd.concat(
        [d["high"] - d["low"], (d["high"] - d["close"].shift()).abs(), (d["low"] - d["close"].shift()).abs()],
        axis=1,
    ).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    d["body"] = (d["close"] - d["open"]).abs()
    d["body_ratio"] = d["body"] / (d["high"] - d["low"]).replace(0, np.nan)
    d["hi_ext"] = d["high"].rolling(20).max()
    d["lo_ext"] = d["low"].rolling(20).min()
    return d.dropna(subset=["atr"])


def forward_extreme(high: pd.Series, low: pd.Series, n: int) -> tuple[pd.Series, pd.Series]:
    fh = pd.concat([high.shift(-i) for i in range(1, n + 1)], axis=1).max(axis=1)
    fl = pd.concat([low.shift(-i) for i in range(1, n + 1)], axis=1).min(axis=1)
    return fh, fl


def round_cross(d: pd.DataFrame, symbol: str, prox_yen: float, prox_half: float) -> tuple[pd.Series, pd.Series]:
    if symbol == "XAUUSD":
        n10 = (d["close"] / 10).round() * 10
        n50 = (d["close"] / 50).round() * 50
        up = ((d["close"] > n10) & (d["close"].shift(1) <= n10.shift(1))) | (
            (d["close"] > n50) & (d["close"].shift(1) <= n50.shift(1))
        )
        dn = ((d["close"] < n10) & (d["close"].shift(1) >= n10.shift(1))) | (
            (d["close"] < n50) & (d["close"].shift(1) >= n50.shift(1))
        )
        near = ((d["close"] - n10).abs() <= prox_yen * 4) | ((d["close"] - n50).abs() <= prox_yen * 4)
    else:
        yen = d["close"].round()
        half = (d["close"] * 2).round() / 2
        up = ((d["close"] > yen) & (d["close"].shift(1) <= yen.shift(1))) | (
            (d["close"] > half) & (d["close"].shift(1) <= half.shift(1))
        )
        dn = ((d["close"] < yen) & (d["close"].shift(1) >= yen.shift(1))) | (
            (d["close"] < half) & (d["close"].shift(1) >= half.shift(1))
        )
        near = (d["close"] - yen).abs() <= prox_yen
        near = near | (d["close"] - half).abs() <= prox_half
    return up.fillna(False), dn.fillna(False), near.fillna(False)


def eval_combo_fast(
    d: pd.DataFrame,
    symbol: str,
    prox_yen: float,
    prox_half: float,
    ext_atr: float,
    swing_len: int,
    big_mult: float,
    fwd_bars: int,
    strict_f1: bool,
    wick_atr: float,
    sweep_lb: int,
    fwd_pair: tuple[pd.Series, pd.Series],
) -> dict:
    return eval_combo(
        d, symbol, prox_yen, prox_half, ext_atr, swing_len, big_mult,
        fwd_bars, strict_f1, wick_atr, sweep_lb, 72, fh=fwd_pair[0], fl=fwd_pair[1],
    )


def eval_combo(
    d: pd.DataFrame,
    symbol: str,
    prox_yen: float,
    prox_half: float,
    ext_atr: float,
    swing_len: int,
    big_mult: float,
    fwd_bars: int,
    strict_f1: bool,
    wick_atr: float,
    sweep_lb: int,
    revenge_bars: int,
    fh: pd.Series | None = None,
    fl: pd.Series | None = None,
) -> dict:
    ps = pip_size(symbol)
    cross_up, cross_dn, near = round_cross(d, symbol, prox_yen, prox_half)
    near_high = d["hi_ext"] - d["close"] <= d["atr"] * ext_atr
    near_low = d["lo_ext"] - d["close"] <= d["atr"] * ext_atr

    big = d["body"] >= d["atr"] * big_mult
    bull = d["close"] > d["open"]
    bear = d["close"] < d["open"]
    impulse_bull = big & bull
    impulse_bull_prev = impulse_bull.shift(1).fillna(False).astype(bool)
    impulse_bear = big & bear
    impulse_bear_prev = impulse_bear.shift(1).fillna(False).astype(bool)

    key_high = d["high"].shift(1).rolling(swing_len).max()
    key_low = d["low"].shift(1).rolling(swing_len).min()
    buf = d["atr"] * 0.08
    break_up = (d["close"] > key_high + buf) & (d["close"].shift(1) <= key_high.shift(1) + buf.shift(1))
    break_dn = (d["close"] < key_low - buf) & (d["close"].shift(1) >= key_low.shift(1) - buf.shift(1))
    strong_up = bull & (d["body_ratio"] >= 0.45)
    strong_dn = bear & (d["body_ratio"] >= 0.45)

    if strict_f1:
        f1l = near_high & bull & cross_up
        f1s = near_low & bear & cross_dn
    else:
        f1l = near_high & bull & near
        f1s = near_low & bear & near

    f2l = impulse_bull & ~impulse_bull_prev & bull
    f2s = impulse_bear & ~impulse_bear_prev & bear
    brkl = break_up & strong_up
    brks = break_dn & strong_dn
    stop_long = f1l | f2l | brkl
    stop_short = f1s | f2s | brks
    stop_any = stop_long | stop_short

    if fh is None or fl is None:
        fh, fl = forward_extreme(d["high"], d["low"], fwd_bars)
    fwd_up = (fh - d["close"]) / ps
    fwd_dn = (d["close"] - fl) / ps
    valid = fh.notna() & fl.notna()

    # 追い側逆行（買いSTOP後に下がる）
    adverse_long = valid & stop_long & (fwd_dn > fwd_up)
    adverse_short = valid & stop_short & (fwd_up > fwd_dn)
    adverse = pd.concat([adverse_long, adverse_short])
    n_stop = int(stop_any.sum())
    n_sl = int(stop_long.sum())
    n_ss = int(stop_short.sum())

    # ストップ狩り + 投げ切り proxy（下ヒゲ奪い→戻り）
    ref_low = d["low"].shift(1).rolling(sweep_lb).min()
    ref_high = d["high"].shift(1).rolling(sweep_lb).max()
    mid = (d["high"] + d["low"]) / 2
    sweep_down = (d["low"] < ref_low - d["atr"] * wick_atr) & (d["close"] > mid) & bull
    sweep_up = (d["high"] > ref_high + d["atr"] * wick_atr) & (d["close"] < mid) & bear

    edge_down_sweep = valid & sweep_down & (fwd_up > 20)  # 狩り後の上方向優位（pips閾値は相対）
    edge_up_sweep = valid & sweep_up & (fwd_dn > 20)
    sweep_dn_up = valid & sweep_down & (fwd_up > fwd_dn)
    sweep_up_dn = valid & sweep_up & (fwd_dn > fwd_up)

    def rate(mask: pd.Series, favor: pd.Series) -> float:
        m = mask & valid
        return float(favor[m].mean()) if m.any() else np.nan

    # どテン proxy（高速）: STOP後 revenge_bars 以内に再STOP
    rev_follow = stop_long.shift(1).rolling(revenge_bars).max().fillna(0).astype(bool) & stop_long
    revenge_hit = int(rev_follow.sum())
    rev_rate = rate(rev_follow, fwd_up > fwd_dn)

    # 連鎖: 買いSTOPの次1〜6本以内に下狩り→その足で上優位
    soon_sweep = pd.concat([sweep_down.shift(-k) for k in range(1, 7)], axis=1).max(axis=1).fillna(0).astype(bool)
    chain_mask = valid & stop_long & soon_sweep
    chain_n = int(chain_mask.sum())
    chain_pct = float((fwd_up > fwd_dn)[chain_mask].mean()) if chain_n else np.nan

    return {
        "prox_yen": prox_yen,
        "prox_half": prox_half,
        "ext_atr": ext_atr,
        "swing_len": swing_len,
        "big_mult": big_mult,
        "fwd_bars": fwd_bars,
        "strict_f1": strict_f1,
        "wick_atr": wick_atr,
        "sweep_lb": sweep_lb,
        "revenge_bars": revenge_bars,
        "stop_count": n_stop,
        "stop_long": n_sl,
        "stop_short": n_ss,
        "adverse_rate": float(adverse.mean()) if len(adverse) else np.nan,
        "sweep_down_n": int(sweep_down.sum()),
        "sweep_down_up_edge": rate(sweep_down, sweep_dn_up),
        "sweep_up_n": int(sweep_up.sum()),
        "sweep_up_dn_edge": rate(sweep_up, sweep_up_dn),
        "avg_fwd_up_after_sweep_dn": float(fwd_up[sweep_down & valid].mean()) if (sweep_down & valid).any() else np.nan,
        "avg_fwd_dn_after_sweep_up": float(fwd_dn[sweep_up & valid].mean()) if (sweep_up & valid).any() else np.nan,
        "revenge_after_stop_n": revenge_hit,
        "revenge_fwd_up_rate": rev_rate,
        "chain_stop_sweep_up": chain_pct,
        "chain_n": chain_n,
        "score_edge": np.nanmean([rate(sweep_down, sweep_dn_up), chain_pct]) if not np.isnan(chain_pct) else rate(sweep_down, sweep_dn_up),
    }


def student_loss_sweep(symbol: str, d: pd.DataFrame, tol_pips: float, fwd_bars: int) -> pd.DataFrame:
    """Loss exit price clusters → first breach → forward direction."""
    if not ENTRIES.exists():
        return pd.DataFrame()
    ps = pip_size(symbol)
    ent = pd.read_csv(ENTRIES, on_bad_lines="skip")
    loss = ent[(ent["currency"] == symbol) & (ent["result"] == "loss")].copy()
    loss["exit_dt"] = pd.to_datetime(loss["exit_datetime_jst"])
    if loss.empty:
        return pd.DataFrame()

    tol = tol_pips * ps
    loss["cluster"] = (loss["exit_price"].astype(float) / tol).round() * tol
    fh, fl = forward_extreme(d["high"], d["low"], fwd_bars)
    d = d.reset_index(drop=True)
    rows = []

    for price, g in loss.groupby("cluster"):
        if len(g) < 3:
            continue
        t0 = g["exit_dt"].min()
        t1 = g["exit_dt"].max() + pd.Timedelta(days=5)
        win = d[(d["time"] >= t0) & (d["time"] <= t1)]
        if len(win) < 10:
            continue
        zone_lo, zone_hi = float(price) - tol, float(price) + tol
        # 買い損切束の下抜け → 上優位（カバー+どテン買い）
        hit = win[win["low"] < zone_lo]
        if hit.empty:
            continue
        t = hit.iloc[0]["time"]
        idx = d.index[d["time"] == t]
        if len(idx) != 1:
            continue
        i = int(idx[0])
        if i >= len(d) - fwd_bars or not pd.notna(fh.iloc[i]):
            continue
        fu = (fh.iloc[i] - d["close"].iloc[i]) / ps
        fd = (d["close"].iloc[i] - fl.iloc[i]) / ps
        rows.append(
            {
                "cluster_price": float(price),
                "loss_n": len(g),
                "breach": "below_cluster",
                "fwd_up_pips": float(fu),
                "fwd_dn_pips": float(fd),
                "edge_hit": bool(fu > fd),
            }
        )
    return pd.DataFrame(rows)


def _mean_rate(mask: np.ndarray, favor: np.ndarray, valid: np.ndarray) -> float:
    m = mask & valid
    return float(favor[m].mean()) if m.any() else np.nan


def build_sweep_cache(d: pd.DataFrame, symbol: str) -> dict:
    """Precompute masks once; grid loop only ORs booleans + aggregates."""
    ps = pip_size(symbol)
    n = len(d)
    bull = (d["close"] > d["open"]).to_numpy()
    bear = (d["close"] < d["open"]).to_numpy()
    body_ratio = d["body_ratio"].to_numpy()
    strong_up = bull & (body_ratio >= 0.45)
    strong_dn = bear & (body_ratio >= 0.45)
    big_body = d["body"].to_numpy()
    atr = d["atr"].to_numpy()
    hi_ext = d["hi_ext"].to_numpy()
    lo_ext = d["lo_ext"].to_numpy()
    close = d["close"].to_numpy()
    high = d["high"].to_numpy()
    low = d["low"].to_numpy()

    prox_vals_y = [0.15, 0.25, 0.35]
    prox_vals_h = [0.10, 0.15, 0.20]
    round_cache: dict[tuple[float, float], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for py, ph in itertools.product(prox_vals_y, prox_vals_h):
        cu, cd, nr = round_cross(d, symbol, py, ph)
        round_cache[(py, ph)] = (cu.to_numpy(), cd.to_numpy(), nr.to_numpy())

    ext_cache: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for ext in [0.60, 0.85, 1.10]:
        ext_cache[ext] = (
            (hi_ext - close <= atr * ext),
            (close - lo_ext <= atr * ext),
        )

    f2_cache: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for bg in [0.95, 1.05, 1.20]:
        big = big_body >= atr * bg
        ib = big & bull
        ibp = np.roll(ib, 1)
        ibp[0] = False
        ie = big & bear
        iep = np.roll(ie, 1)
        iep[0] = False
        f2_cache[bg] = (ib & ~ibp & bull, ie & ~iep & bear)

    brk_cache: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    buf = atr * 0.08
    c1 = np.roll(close, 1)
    c1[0] = close[0]
    for sw in [36, 48, 72]:
        kh = pd.Series(high).shift(1).rolling(sw).max().to_numpy()
        kl = pd.Series(low).shift(1).rolling(sw).min().to_numpy()
        khb = np.roll(kh, 1)
        klb = np.roll(kl, 1)
        khb[0], klb[0] = kh[0], kl[0]
        bb = np.roll(buf, 1)
        bb[0] = buf[0]
        brk_cache[sw] = (
            (close > kh + buf) & (c1 <= khb + bb),
            (close < kl - buf) & (c1 >= klb - bb),
        )

    mid = (high + low) / 2
    sweep_dn_cache: dict[tuple[float, int], np.ndarray] = {}
    sweep_up_cache: dict[tuple[float, int], np.ndarray] = {}
    for wick, slb in itertools.product([0.25, 0.40, 0.55], [12, 20, 32]):
        rl = pd.Series(low).shift(1).rolling(slb).min().to_numpy()
        rh = pd.Series(high).shift(1).rolling(slb).max().to_numpy()
        sweep_dn_cache[(wick, slb)] = (low < rl - atr * wick) & (close > mid) & bull
        sweep_up_cache[(wick, slb)] = (high > rh + atr * wick) & (close < mid) & bear

    soon_cache: dict[tuple[float, int], np.ndarray] = {}
    for key, sd in sweep_dn_cache.items():
        parts = [np.roll(sd, -k) for k in range(1, 7)]
        for k in range(1, 7):
            parts[k - 1][-k:] = False
        soon_cache[key] = np.max(np.stack(parts), axis=0).astype(bool)

    fwd_cache: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for fb in [12, 24, 48, 72]:
        fh, fl = forward_extreme(d["high"], d["low"], fb)
        fu = ((fh - d["close"]) / ps).to_numpy()
        fd = ((d["close"] - fl) / ps).to_numpy()
        valid = (fh.notna() & fl.notna()).to_numpy()
        fwd_cache[fb] = (fu, fd, valid, (fu > fd))

    return {
        "round": round_cache,
        "ext": ext_cache,
        "f2": f2_cache,
        "brk": brk_cache,
        "sweep_dn": sweep_dn_cache,
        "sweep_up": sweep_up_cache,
        "soon": soon_cache,
        "fwd": fwd_cache,
        "strong_up": strong_up,
        "strong_dn": strong_dn,
        "bull": bull,
        "bear": bear,
        "revenge_bars": 72,
    }


def score_cached(
    cache: dict,
    prox_y: float,
    prox_h: float,
    ext_a: float,
    sw: int,
    bg: float,
    fwd: int,
    strict: bool,
    wick: float,
    slb: int,
) -> dict:
    cu, cd, nr = cache["round"][(prox_y, prox_h)]
    nh, nl = cache["ext"][ext_a]
    bull = cache["bull"]
    f2l, f2s = cache["f2"][bg]
    brkl, brks = cache["brk"][sw]
    bear = cache["bear"]
    if strict:
        f1l = nh & bull & cu
        f1s = nl & bear & cd
    else:
        f1l = nh & bull & nr
        f1s = nl & bear & nr
    stop_long = f1l | f2l | (brkl & cache["strong_up"])
    stop_short = f1s | f2s | (brks & cache["strong_dn"])
    stop_any = stop_long | stop_short

    fu, fd, valid, favor_up = cache["fwd"][fwd]
    sweep_down = cache["sweep_dn"][(wick, slb)]
    sweep_up = cache["sweep_up"][(wick, slb)]
    soon = cache["soon"][(wick, slb)]

    adverse_l = valid & stop_long & (fd > fu)
    adverse_s = valid & stop_short & (fu > fd)
    adverse = np.concatenate([adverse_l[valid & stop_long], adverse_s[valid & stop_short]])
    n_stop = int(stop_any.sum())

    sweep_dn_up = valid & sweep_down & (fu > fd)
    sweep_up_dn = valid & sweep_up & (fd > fu)
    rev_follow = (
        pd.Series(stop_long).shift(1).rolling(cache["revenge_bars"]).max().fillna(0).astype(bool).to_numpy()
        & stop_long
    )
    chain_mask = valid & stop_long & soon

    return {
        "prox_yen": prox_y,
        "prox_half": prox_h,
        "ext_atr": ext_a,
        "swing_len": sw,
        "big_mult": bg,
        "fwd_bars": fwd,
        "strict_f1": strict,
        "wick_atr": wick,
        "sweep_lb": slb,
        "revenge_bars": cache["revenge_bars"],
        "stop_count": n_stop,
        "stop_long": int(stop_long.sum()),
        "stop_short": int(stop_short.sum()),
        "adverse_rate": float(adverse.mean()) if len(adverse) else np.nan,
        "sweep_down_n": int(sweep_down.sum()),
        "sweep_down_up_edge": _mean_rate(sweep_down, sweep_dn_up, valid),
        "sweep_up_n": int(sweep_up.sum()),
        "sweep_up_dn_edge": _mean_rate(sweep_up, sweep_up_dn, valid),
        "avg_fwd_up_after_sweep_dn": float(fu[sweep_down & valid].mean()) if (sweep_down & valid).any() else np.nan,
        "avg_fwd_dn_after_sweep_up": float(fd[sweep_up & valid].mean()) if (sweep_up & valid).any() else np.nan,
        "revenge_after_stop_n": int(rev_follow.sum()),
        "revenge_fwd_up_rate": _mean_rate(rev_follow, favor_up, valid),
        "chain_stop_sweep_up": _mean_rate(chain_mask, favor_up, valid),
        "chain_n": int(chain_mask.sum()),
        "score_edge": float(
            np.nanmean(
                [
                    _mean_rate(sweep_down, sweep_dn_up, valid),
                    _mean_rate(chain_mask, favor_up, valid),
                ]
            )
        ),
    }


def run_sweep(symbol: str, years: list[int]) -> pd.DataFrame:
    raw = load_ohlc(symbol, years)
    if raw.empty:
        return pd.DataFrame()
    d = base_frame(raw)
    cache = build_sweep_cache(d, symbol)
    rows = []
    grid = itertools.product(
        [0.15, 0.25, 0.35],
        [0.10, 0.15, 0.20],
        [0.60, 0.85, 1.10],
        [36, 48, 72],
        [0.95, 1.05, 1.20],
        [12, 24, 48, 72],
        [True, False],
        [0.25, 0.40, 0.55],
        [12, 20, 32],
    )
    for prox_y, prox_h, ext_a, sw, bg, fwd, strict, wick, slb in grid:
        r = score_cached(cache, prox_y, prox_h, ext_a, sw, bg, fwd, strict, wick, slb)
        r["symbol"] = symbol
        rows.append(r)
    print(f"  {symbol}: {len(rows)} combos")
    return pd.DataFrame(rows)


def write_md(df: pd.DataFrame, student_parts: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# 損切・狩り・どテン — パラメータスイープ",
        "",
        "仮説: 損切誘発 → カバー/投げ切り → どテン集中 → **その方向に短期優位**",
        "",
        f"組み合わせ: **{len(df)}行**（通貨×パラメータグリッド）",
        "",
        "## 見る指標",
        "",
        "| 列 | 意味 |",
        "|---|---|",
        "| adverse_rate | 買いSTOP後に下優位・売りSTOP後に上優位（追い側が不利） |",
        "| sweep_down_up_edge | 安値狩り＋戻り足後、上方向に優位な割合 |",
        "| chain_stop_sweep_up | 買いSTOP→6本内に下狩り→上優位 |",
        "| revenge_fwd_up_rate | どテン(再STOP)後の上優位 |",
        "| score_edge | 狩り系スコアの平均 |",
        "",
    ]
    for sym in df["symbol"].unique():
        sub = df[df["symbol"] == sym].copy()
        sub = sub[sub["stop_count"] >= 50].sort_values("score_edge", ascending=False)
        lines += [f"## {sym} — score_edge TOP10", ""]
        lines += [
            "| prox | ext | swing | fwd | strict | wick | sweep_lb | stops | sweep_dn↑% | chain% | revenge↑% | adverse% |",
            "|---:|---:|---:|---:|:---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for _, r in sub.head(10).iterrows():
            def pct(v: float) -> str:
                return f"{v:.1%}" if pd.notna(v) else "—"

            lines.append(
                f"| {r['prox_yen']}/{r['prox_half']} | {r['ext_atr']} | {int(r['swing_len'])} | {int(r['fwd_bars'])} | "
                f"{'Y' if r['strict_f1'] else 'N'} | {r['wick_atr']} | {int(r['sweep_lb'])} | {int(r['stop_count'])} | "
                f"{pct(r['sweep_down_up_edge'])} | {pct(r['chain_stop_sweep_up'])} | {pct(r['revenge_fwd_up_rate'])} | {pct(r['adverse_rate'])} |"
            )
        lines.append("")

        best_adv = sub.sort_values("adverse_rate", ascending=False).head(5)
        lines += [f"### {sym} — 追い抑制（adverse_rate）TOP5", ""]
        for _, r in best_adv.iterrows():
            lines.append(
                f"- prox={r['prox_yen']}/{r['prox_half']} ext={r['ext_atr']} swing={int(r['swing_len'])} "
                f"fwd={int(r['fwd_bars'])} strict={r['strict_f1']} → adverse **{r['adverse_rate']:.1%}** (n={int(r['stop_count'])})"
            )
        lines.append("")

        st = student_parts.get(sym)
        if st is not None and not st.empty:
            hit = st["edge_hit"].mean()
            lines += [f"### {sym} — 受講生損切出口クラスタの狩り後", "", f"- イベント {len(st)}件 / 優位方向的中 **{hit:.1%}**", ""]

    lines += ["## 全データ", "", f"CSV: `{OUT_CSV.name}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    years = [2024, 2025]
    symbols = ["GBPJPY", "XAUUSD", "USDJPY"]
    all_rows = []
    student_parts = {}
    for sym in symbols:
        print(f"Sweep {sym}...")
        sdf = run_sweep(sym, years)
        all_rows.append(sdf)
        raw = load_ohlc(sym, years)
        if not raw.empty:
            student_parts[sym] = student_loss_sweep(sym, base_frame(raw), 20, 24)

    df = pd.concat(all_rows, ignore_index=True)
    df.to_csv(OUT_CSV, index=False)
    write_md(df, student_parts)
    print(f"Wrote {OUT_CSV} ({len(df)} rows)")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

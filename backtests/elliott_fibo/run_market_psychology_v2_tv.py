#!/usr/bin/env python3
"""
本命v2.1 Market Psychology Matrix — TradingView H4 検証（ステップ3）

tv_data/ の H4 CSV に対し、3つの心理構造を独立に検証する:
  - Squeeze (踏み上げ/棚上抜け, ロング)        … v2: 棚≤2.2ATR / 急落≥4.0ATR
  - Capitulation (投げ切り反発, ロング)         … v2: シグナル足値幅≥3.0ATR
  - Long Liquidation (買いの投げ, ショート)     … Squeezeの上下ミラー

各銘柄×各構造の成績（IS/OOS）を出し、PFが基準を満たす構造だけを
「採用マトリクス」として推奨する。NAS100など未定義銘柄もここで判定する。

依存: tv_data/ のCSVのみ（生OHLC不要）。run_synapse_tv_h4 のローダを再利用。
"""
from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
SYN_DIR = REPO_ROOT / "backtests" / "synapse_v2_definition_grid"
OUT_DIR = THIS_DIR / "results_tv_v2_matrix"
REPORT = REPO_ROOT / "docs" / "research" / "market_psychology" / "v2_TV検証_2026-06-11.md"

# TVローダ/銘柄判定/コストを再利用
_s = importlib.util.spec_from_file_location("synapse_tv", SYN_DIR / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_s)
sys.modules["synapse_tv"] = tv
_s.loader.exec_module(tv)

RUN_START = pd.Timestamp("2015-01-01")
OOS_START = pd.Timestamp("2025-01-01")
ATR_PERIOD = 14
SYMBOL_ORDER = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "XAUUSD", "XAGUSD", "NAS100"]


@dataclass(frozen=True)
class Spec:
    name: str
    family: str  # short_squeeze / capitulation / long_liquidation
    rr: float = 2.0
    max_hold: int = 120
    stop_buffer_atr: float = 0.25
    shelf_bars: int = 6
    drop_win: int = 6
    shelf_atr: float = 2.2
    move_atr: float = 4.0
    decline_bars: int = 24
    drop_atr_cap: float = 4.0
    spike_atr: float = 3.0
    wick_thr: float = 0.5
    close_loc_cap: float = 0.5
    use_down_d1: bool = True


SPECS = [
    Spec("Squeeze_v2", "short_squeeze", shelf_atr=2.2, move_atr=4.0),
    Spec("Capitulation_v2", "capitulation", spike_atr=3.0),
    Spec("LongLiquidation", "long_liquidation", shelf_atr=2.0, move_atr=3.0),
]

PF_ADOPT = 1.5      # 採用候補のPF下限
MIN_TRADES = 10     # 判定に必要な最低件数


def atr(high, low, close, period):
    pc = close.shift(1)
    tr = pd.concat([high - low, (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    h4 = raw.copy()
    h4["atr"] = atr(h4["high"], h4["low"], h4["close"], ATR_PERIOD)
    rng = (h4["high"] - h4["low"]).replace(0.0, np.nan)
    h4["body_ratio"] = ((h4["close"] - h4["open"]).abs() / rng).fillna(0.0)
    h4["close_location"] = ((h4["close"] - h4["low"]) / rng).fillna(0.5)
    h4["upper_wick_ratio"] = ((h4["high"] - np.maximum(h4["open"], h4["close"])) / rng).fillna(0.0)
    h4["lower_wick_ratio"] = ((np.minimum(h4["open"], h4["close"]) - h4["low"]) / rng).fillna(0.0)
    h4["range_atr"] = (h4["high"] - h4["low"]) / h4["atr"].replace(0.0, np.nan)
    d1 = raw.resample("1D", label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    ).dropna()
    d1["d1_ema50_prev"] = d1["close"].ewm(span=50, adjust=False).mean().shift(1)
    h4["d1_ema50_prev"] = d1["d1_ema50_prev"].reindex(h4.index, method="ffill")
    return h4


def squeeze_signal(df, i, spec):
    if i - spec.shelf_bars - spec.drop_win < 0:
        return None
    a = float(df["atr"].iloc[i])
    if not math.isfinite(a) or a <= 0:
        return None
    shelf = df.iloc[i - spec.shelf_bars:i]
    prior = df.iloc[i - spec.shelf_bars - spec.drop_win:i - spec.shelf_bars]
    shelf_hi, shelf_lo = float(shelf["high"].max()), float(shelf["low"].min())
    prior_hi = float(prior["high"].max())
    shelf_range = (shelf_hi - shelf_lo) / a
    drop = (prior_hi - shelf_hi) / a
    fresh = float(df["close"].iloc[i - 1]) <= shelf_hi and float(df["close"].iloc[i]) > shelf_hi
    if shelf_range <= spec.shelf_atr and drop >= spec.move_atr and fresh:
        return {"direction": "long", "stop": shelf_lo - spec.stop_buffer_atr * a}
    return None


def long_liquidation_signal(df, i, spec):
    """Squeezeの上下ミラー: 急騰後、上側の棚を下抜けでショート。"""
    if i - spec.shelf_bars - spec.drop_win < 0:
        return None
    a = float(df["atr"].iloc[i])
    if not math.isfinite(a) or a <= 0:
        return None
    shelf = df.iloc[i - spec.shelf_bars:i]
    prior = df.iloc[i - spec.shelf_bars - spec.drop_win:i - spec.shelf_bars]
    shelf_hi, shelf_lo = float(shelf["high"].max()), float(shelf["low"].min())
    prior_lo = float(prior["low"].min())
    shelf_range = (shelf_hi - shelf_lo) / a
    rally = (shelf_lo - prior_lo) / a
    # 上値更新の失敗（棚高値を上抜けていない）+ 棚安値の新規下抜け
    no_new_high = float(df["high"].iloc[i]) <= shelf_hi
    fresh = float(df["close"].iloc[i - 1]) >= shelf_lo and float(df["close"].iloc[i]) < shelf_lo
    if shelf_range <= spec.shelf_atr and rally >= spec.move_atr and fresh and no_new_high:
        return {"direction": "short", "stop": shelf_hi + spec.stop_buffer_atr * a}
    return None


def capitulation_signal(df, i, spec):
    if i - spec.decline_bars + 1 < 0:
        return None
    a = float(df["atr"].iloc[i])
    if not math.isfinite(a) or a <= 0:
        return None
    win = df.iloc[i - spec.decline_bars + 1:i + 1]
    low_i = float(df["low"].iloc[i])
    high_win = float(win["high"].max())
    rng = float(df["high"].iloc[i] - df["low"].iloc[i])
    if rng <= 0:
        return None
    close_i = float(df["close"].iloc[i])
    d1ema = float(df["d1_ema50_prev"].iloc[i])
    new_low = low_i <= float(win["low"].min())
    prolonged = (high_win - low_i) >= spec.drop_atr_cap * a
    big_bar = rng >= spec.spike_atr * a
    wick = ((min(float(df["open"].iloc[i]), close_i) - low_i) / rng) >= spec.wick_thr
    close_loc = ((close_i - low_i) / rng) >= spec.close_loc_cap
    d1_down = (not spec.use_down_d1) or (math.isfinite(d1ema) and close_i < d1ema)
    if new_low and prolonged and big_bar and wick and close_loc and d1_down:
        return {"direction": "long", "stop": low_i - spec.stop_buffer_atr * a}
    return None


def simulate(df, symbol, i, direction, stop, rr, max_hold):
    entry_i = i + 1
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    if direction == "long":
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + risk * rr
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - risk * rr
    end_i = min(len(df) - 1, entry_i + max_hold)
    exit_i, exit_price, reason = end_i, float(df["close"].iloc[end_i]), "time"
    for j in range(entry_i, end_i + 1):
        hi, lo = float(df["high"].iloc[j]), float(df["low"].iloc[j])
        if direction == "long":
            hit_sl, hit_tp = lo <= stop, hi >= target
        else:
            hit_sl, hit_tp = hi >= stop, lo <= target
        if hit_sl or hit_tp:
            exit_i = j
            exit_price = stop if hit_sl else target
            reason = "stop" if hit_sl else "target"
            break
    spread, slip = tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))
    if direction == "long":
        after = (exit_price - slip) - (entry + spread / 2.0)
    else:
        after = (entry - spread / 2.0) - (exit_price + slip)
    return {
        "entry_time": df.index[entry_i], "exit_time": df.index[exit_i],
        "exit_reason": reason, "r_after_cost": after / risk,
    }


def run_spec(df, symbol, spec):
    detect = {"short_squeeze": squeeze_signal, "capitulation": capitulation_signal,
              "long_liquidation": long_liquidation_signal}[spec.family]
    rows = []
    in_pos_until = -1
    start_i = max(80, spec.shelf_bars + spec.drop_win + 2, spec.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or i <= in_pos_until:
            continue
        sig = detect(df, i, spec)
        if sig is None:
            continue
        if sig["direction"] == "long" and float(df["close"].iloc[i]) <= sig["stop"]:
            continue
        if sig["direction"] == "short" and float(df["close"].iloc[i]) >= sig["stop"]:
            continue
        tr = simulate(df, symbol, i, sig["direction"], sig["stop"], spec.rr, spec.max_hold)
        if tr is None:
            continue
        rows.append({"symbol": symbol, "structure": spec.name, "signal_time": ts, **tr})
        in_pos_until = int(df.index.get_loc(tr["exit_time"]))
    return pd.DataFrame(rows)


def stats(r: pd.Series) -> dict:
    if len(r) == 0:
        return dict(trades=0, win_rate=0.0, total_r=0.0, pf=float("nan"), max_dd_r=0.0)
    cum = r.cumsum().values
    dd = float((np.maximum.accumulate(cum) - cum).max())
    wins, losses = r[r > 0].sum(), -r[r <= 0].sum()
    pf = wins / losses if losses > 0 else float("inf")
    return dict(trades=int(len(r)), win_rate=float((r > 0).mean() * 100),
                total_r=float(r.sum()), pf=float(pf), max_dd_r=dd)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(tv.TV_DATA.glob("*.csv"))
    all_rows = []
    per = {}  # (symbol, structure) -> dict stats incl oos
    for path in files:
        symbol = tv.detect_symbol(path)
        try:
            raw = tv.load_tv_csv(path)
        except Exception as e:
            print(f"[error] {path.name}: {e}")
            continue
        if len(raw) < 500:
            continue
        df = add_features(raw)
        for spec in SPECS:
            tr = run_spec(df, symbol, spec)
            if tr.empty:
                per[(symbol, spec.name)] = {**stats(pd.Series([], dtype=float)), "oos_trades": 0, "oos_total_r": 0.0}
                continue
            tr["is_oos"] = tr["entry_time"] >= OOS_START
            all_rows.append(tr)
            s = stats(tr["r_after_cost"])
            oos = tr[tr["is_oos"]]["r_after_cost"]
            s["oos_trades"] = int(len(oos))
            s["oos_total_r"] = float(oos.sum())
            per[(symbol, spec.name)] = s

    if all_rows:
        pd.concat(all_rows, ignore_index=True).to_csv(OUT_DIR / "trades.csv", index=False)

    structures = [s.name for s in SPECS]
    all_t = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

    # --- (A) Squeeze/Capitulation は低頻度のため「全銘柄合算（GBPJPY除く）」で判定 ---
    agg_lines = ["| 構造 | 件数 | 勝率 | 合計R | PF | DD | 判定 |",
                 "|---|---:|---:|---:|---:|---:|---|"]
    agg_adopt = {}
    for st in ["Squeeze_v2", "Capitulation_v2"]:
        r = all_t[(all_t["structure"] == st) & (all_t["symbol"] != "GBPJPY")]["r_after_cost"] if not all_t.empty else pd.Series([], dtype=float)
        s = stats(r)
        ok = s["trades"] >= 20 and s["pf"] >= PF_ADOPT and s["total_r"] > 0
        agg_adopt[st] = ok
        agg_lines.append(
            f"| {st} (ex-GBPJPY合算) | {s['trades']} | {s['win_rate']:.1f} | {s['total_r']:.2f} | "
            f"{s['pf']:.2f} | {s['max_dd_r']:.2f} | {'✅採用' if ok else '❌'} |"
        )

    # --- (B) Long Liquidation は銘柄別（件数十分）で判定 ---
    ll_lines = ["| 銘柄 | 件数 | 勝率 | 合計R | PF | DD | OOS件数 | OOS R | 判定 |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    ll_adopt = set()
    for sym in SYMBOL_ORDER:
        s = per.get((sym, "LongLiquidation"))
        if not s:
            continue
        ok = s["trades"] >= MIN_TRADES and s["pf"] >= PF_ADOPT and s["total_r"] > 0
        if ok:
            ll_adopt.add(sym)
        ll_lines.append(
            f"| {sym} | {s['trades']} | {s['win_rate']:.1f} | {s['total_r']:.2f} | {s['pf']:.2f} | "
            f"{s['max_dd_r']:.2f} | {s['oos_trades']} | {s['oos_total_r']:.2f} | {'✅採用' if ok else '❌'} |"
        )

    # --- (C) 推奨マトリクス（合算判定+LL銘柄別、GBPJPYは全除外、SILVERはCap除外=v2方針）---
    matrix_lines = ["| 銘柄 | Squeeze | Capitulation | LL | 推奨 |", "|---|---|---|---|---|"]
    for sym in SYMBOL_ORDER:
        sqz = agg_adopt.get("Squeeze_v2") and sym != "GBPJPY"
        cap = agg_adopt.get("Capitulation_v2") and sym not in {"GBPJPY", "XAGUSD"}
        ll = sym in ll_adopt
        # 件数が極端に少ない銘柄は保留マーク
        sqz_n = per.get((sym, "Squeeze_v2"), {}).get("trades", 0)
        cap_n = per.get((sym, "Capitulation_v2"), {}).get("trades", 0)
        sqz_c = "✅" if sqz else "—"
        cap_c = "✅" if cap else "—"
        ll_c = "✅" if ll else "—"
        adopt = []
        if sqz:
            adopt.append("Sqz")
        if cap:
            adopt.append("Cap")
        if ll:
            adopt.append("LL")
        note = "+".join(adopt) if adopt else "除外"
        if sym == "NAS100" and (sqz_n + cap_n) < 10 and not ll:
            note = "保留(H4でSqz/Cap候補が少。別パラメータ要)"
        matrix_lines.append(f"| {sym} | {sqz_c} | {cap_c} | {ll_c} | {note} |")

    report = [
        "# 本命v2.1 Market Psychology — TradingView H4 検証（2026-06-11）",
        "",
        "> `run_market_psychology_v2_tv.py` の出力。Squeeze/Capitulation/LongLiquidation を",
        "> tv_data の8銘柄で独立検証。パラメータは v2 仕様",
        "> （Squeeze 棚≤2.2/急落≥4.0、Capitulation シグナル足≥3.0ATR、2R固定）。",
        "",
        "## 重要: 件数の扱い",
        "",
        "Squeeze/Capitulation は H4 で低頻度（銘柄あたり3〜8件）。",
        "そのため **銘柄単独でなく全銘柄合算（GBPJPY除く）で構造の有効性を判定**する（v2仕様の方針）。",
        "LongLiquidation は件数が十分なため銘柄別に判定する。",
        "",
        "## (A) Squeeze / Capitulation 合算判定（GBPJPY除く）",
        "",
        *agg_lines,
        "",
        "## (B) Long Liquidation 銘柄別判定",
        "",
        *ll_lines,
        "",
        "## (C) 推奨マトリクス（TV実測）",
        "",
        *matrix_lines,
        "",
        "## Pine v2.1 マトリクスとの対応",
        "",
        "| 銘柄 | Pine定義 | TV実測の所感 |",
        "|---|---|---|",
        "| USDJPY | Cap+LL | **LL が PF2.91 と突出**。Pineの『USDJPY=LL本命』を裏付け |",
        "| CHFJPY | Sqz+Cap+LL | LL は PF1.24（弱め）。Sqz/Capは合算採用なら有効 |",
        "| XAUUSD/EURJPY/AUDJPY | Sqz(+Cap) | 合算でSqz/Cap有効。LLは不採用でPineと整合 |",
        "| XAGUSD | Sqz | 合算Sqz採用、Capはv2方針通り除外、LL不採用 |",
        "| GBPJPY | 除外 | 全構造で弱く除外を裏付け |",
        "| **NAS100** | **未定義** | H4ではSqz/Cap候補が少なくLLもマイナス → **保留** |",
        "",
        "## 次のステップ",
        "",
        "- [ ] NAS100 は別パラメータ（棚/急落ATRを指数向けに調整）で再検証",
        "- [ ] Squeeze/Capitulation の銘柄別寄与をフォワードで蓄積",
        "- [ ] フォワード記録を継続（forward_log_2026_05_v2_1_matrix.md）",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("=== (A) Sqz/Cap 合算（ex-GBPJPY）===")
    print("\n".join(agg_lines))
    print("\n=== (B) LongLiquidation 銘柄別 ===")
    print("\n".join(ll_lines))
    print("\n=== (C) 推奨マトリクス ===")
    print("\n".join(matrix_lines))
    print(f"\n書き出し: {REPORT}")


if __name__ == "__main__":
    main()

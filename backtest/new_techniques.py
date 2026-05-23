"""
新しい改善手法の発見テスト (OOS検証付き)

過学習を避けるため、各手法を以下で評価:
  1. Train (2014-2020) + Test (2021-2024) で同じパラメータを評価
  2. Test の Net R が Base Relaxed (Test) を上回り、かつ
     Train→Test 比率が 50% 以上 → 採用候補
  3. 全通貨平均で効くもののみ残す

テスト対象:
  T1. プルバック・エントリー: ブレイク後の押し目で約定
  T2. 確認バー (Sequential): 翌バーも同方向で確定したらエントリー
  T3. ATR 拡大フィルター: 直近 ATR > N本平均 ATR
  T4. 上位足トレンド: D1 終値が D1 SMA20 の上/下
  T5. 強体フィルター: 体/レンジ比 >= 閾値
  T6. 時間決済: 一定本数で未決済なら強制 close
  T7. ブレイクボリューム代用 (レンジ拡大): 当該バー range > ATR*N
  T8. 流動性スイープ: 高値抜けて押し戻された次バーでエントリー
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from sai_backtest import atr, rolling_max, rolling_min, load_instrument
from optimize_trendbreak import TBConfig, BASE, ATR_PERIOD, LOOKBACK_LONG, EXCLUDE_LONG

TRAIN_END = 2020
TEST_START = 2021


# ============================================================
# Signal generation (拡張版)
# ============================================================
@dataclass
class ExtConfig(TBConfig):
    # 新追加パラメータ
    pullback_atr: float = 0.0       # >0: ブレイク後 X*ATR 押し目まで待ってエントリー
    pullback_max_bars: int = 8       # 押し目を何バーまで待つか
    require_seq_confirm: bool = False  # 翌バーも同方向クロージング
    atr_expansion_ratio: float = 0.0   # ATR が直近平均の X 倍以上 (0=無効)
    atr_expansion_lookback: int = 50
    htf_trend_d: int = 0               # >0: D1 SMA X 方向と一致のみ
    body_ratio_min: float = 0.0        # 体/レンジ比 (0=無効)
    time_exit_bars: int = 0            # >0: N本経過したら強制クローズ
    range_atr_min: float = 0.0         # 当該バー range >= X*ATR
    sweep_mode: bool = False           # 流動性スイープモード (ブレイク失敗の反対方向)


def compute_signals_ext(df: pd.DataFrame, cfg: ExtConfig) -> pd.DataFrame:
    o = df["open"]; h = df["high"]; l = df["low"]; c = df["close"]
    a = atr(h, l, c, ATR_PERIOD)

    high_3m = rolling_max(h.shift(1), cfg.lookback_3m)
    low_3m  = rolling_min(l.shift(1), cfg.lookback_3m)
    recent_high_3m = rolling_max(h.shift(1), cfg.exclude)
    recent_low_3m  = rolling_min(l.shift(1), cfg.exclude)

    high_long = rolling_max(h.shift(1), LOOKBACK_LONG)
    low_long  = rolling_min(l.shift(1), LOOKBACK_LONG)
    recent_high_long = rolling_max(h.shift(1), EXCLUDE_LONG)
    recent_low_long  = rolling_min(l.shift(1), EXCLUDE_LONG)

    long_3m  = (c > high_3m) & (recent_high_3m < high_3m)
    short_3m = (c < low_3m)  & (recent_low_3m  > low_3m)
    long_long  = (c > high_long)  & (recent_high_long < high_long)
    short_long = (c < low_long)   & (recent_low_long  > low_long)

    if cfg.level_kind == "long":
        long_sig, short_sig = long_long, short_long
    elif cfg.level_kind == "any":
        long_sig = long_3m | long_long; short_sig = short_3m | short_long
    elif cfg.level_kind == "confluence":
        long_sig = long_3m & long_long; short_sig = short_3m & short_long
    else:
        long_sig, short_sig = long_3m, short_3m

    warmup = max(cfg.lookback_3m, cfg.exclude) + 5
    warm_ok = np.arange(len(df)) >= warmup
    long_sig = long_sig & pd.Series(warm_ok, index=df.index)
    short_sig = short_sig & pd.Series(warm_ok, index=df.index)

    if cfg.session:
        h_utc = df.index.hour
        sess_asia = ((h_utc >= 0) & (h_utc < 7)) | ((h_utc >= 21) & (h_utc < 24))
        sess_eu = (h_utc >= 7) & (h_utc < 13)
        sess_ny = (h_utc >= 13) & (h_utc < 21)
        sess_pass = ((sess_asia & cfg.asia) | (sess_eu & cfg.eu) | (sess_ny & cfg.ny))
        long_sig = long_sig & pd.Series(sess_pass, index=df.index)
        short_sig = short_sig & pd.Series(sess_pass, index=df.index)

    # --- 新フィルター ---
    # 確認バー: 翌バー(=次の足のi)で前バーも条件継続+方向同じ終値
    if cfg.require_seq_confirm:
        # 前バーがブレイク条件、当該バーが同方向の終値で前バー終値より上/下
        long_prev = long_sig.shift(1).fillna(False)
        short_prev = short_sig.shift(1).fillna(False)
        long_sig = long_prev & (c > c.shift(1))
        short_sig = short_prev & (c < c.shift(1))

    # ATR 拡大
    if cfg.atr_expansion_ratio > 0:
        atr_ma = a.rolling(cfg.atr_expansion_lookback).mean()
        expanded = a >= atr_ma * cfg.atr_expansion_ratio
        long_sig = long_sig & expanded
        short_sig = short_sig & expanded

    # 上位足トレンド (D1) - 前日終値ベース (未来参照回避)
    if cfg.htf_trend_d > 0:
        d1_close = c.resample("1D").last()
        d1_sma = d1_close.rolling(cfg.htf_trend_d).mean()
        # ★ FIX: shift(1) で前日の確定値のみ使う
        d1_signal = (d1_close > d1_sma).shift(1)
        d1_above = d1_signal.reindex(df.index, method="ffill").fillna(False)
        long_sig = long_sig & d1_above
        short_sig = short_sig & (~d1_above)

    # 体/レンジ比
    if cfg.body_ratio_min > 0:
        bar_range = (h - l).replace(0, np.nan)
        body_ratio = (c - o).abs() / bar_range
        long_sig = long_sig & (body_ratio >= cfg.body_ratio_min) & (c > o)
        short_sig = short_sig & (body_ratio >= cfg.body_ratio_min) & (c < o)

    # レンジATR 倍率 (ブレイクバーの大きさ)
    if cfg.range_atr_min > 0:
        big_bar = (h - l) >= a * cfg.range_atr_min
        long_sig = long_sig & big_bar
        short_sig = short_sig & big_bar

    # スイープモード: ヒゲがレベル抜け、終値が戻った → 反対方向で約定
    if cfg.sweep_mode:
        sweep_long_setup = (l < low_3m) & (c > low_3m) & (recent_low_3m > low_3m)
        sweep_short_setup = (h > high_3m) & (c < high_3m) & (recent_high_3m < high_3m)
        long_sig = sweep_long_setup
        short_sig = sweep_short_setup

    return pd.DataFrame({
        "open": o, "high": h, "low": l, "close": c, "atr": a,
        "high_3m": high_3m, "low_3m": low_3m,
        "long_sig": long_sig.fillna(False), "short_sig": short_sig.fillna(False),
    }, index=df.index)


# ============================================================
# Trade simulation (拡張版: プルバックエントリーと時間決済)
# ============================================================
@dataclass
class Trade:
    pnl_r: float
    bars_held: int
    is_win: bool
    direction: str


def simulate_ext(sig: pd.DataFrame, cfg: ExtConfig) -> list[Trade]:
    trades: list[Trade] = []
    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    high_3m = sig["high_3m"].to_numpy()
    low_3m = sig["low_3m"].to_numpy()
    long_sig = sig["long_sig"].to_numpy()
    short_sig = sig["short_sig"].to_numpy()

    in_pos_until = -1
    cooldown_until = -1
    n = len(sig)
    for i in range(n - 1):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        if not (long_sig[i] or short_sig[i]):
            continue
        sig_atr = a[i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue
        sl_dist = sig_atr * cfg.sl_atr
        is_long = bool(long_sig[i])

        # --- プルバックエントリー ---
        entry_bar = i + 1
        entry: float
        if cfg.pullback_atr > 0:
            level = high_3m[i] if is_long else low_3m[i]
            target = level + cfg.pullback_atr * sig_atr if not is_long else level - cfg.pullback_atr * sig_atr
            entry = np.nan
            for k in range(i + 1, min(i + 1 + cfg.pullback_max_bars, n)):
                if is_long and l[k] <= target:
                    entry = target
                    entry_bar = k
                    break
                if (not is_long) and h[k] >= target:
                    entry = target
                    entry_bar = k
                    break
            if np.isnan(entry):
                continue
        else:
            if entry_bar >= n:
                break
            entry = o[entry_bar]

        sl = entry - sl_dist if is_long else entry + sl_dist
        tp = entry + sl_dist * cfg.tp_rr if is_long else entry - sl_dist * cfg.tp_rr

        # --- 決済シミュレーション ---
        for j in range(entry_bar, n):
            if is_long:
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp

            time_out = cfg.time_exit_bars > 0 and (j - entry_bar) >= cfg.time_exit_bars

            if hit_sl and hit_tp:
                ex = sl
                pnl = (ex - entry) / sl_dist if is_long else (entry - ex) / sl_dist
                trades.append(Trade(pnl, j - entry_bar, pnl > 0, "long" if is_long else "short"))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_sl:
                ex = sl
                pnl = (ex - entry) / sl_dist if is_long else (entry - ex) / sl_dist
                trades.append(Trade(pnl, j - entry_bar, pnl > 0, "long" if is_long else "short"))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if hit_tp:
                ex = tp
                pnl = cfg.tp_rr
                trades.append(Trade(pnl, j - entry_bar, True, "long" if is_long else "short"))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
            if time_out:
                # 終値で決済 (ここでは現在のclose使えないので、当該バーのcloseで決済)
                c_arr = sig["close"].to_numpy()
                ex = c_arr[j]
                pnl = (ex - entry) / sl_dist if is_long else (entry - ex) / sl_dist
                trades.append(Trade(pnl, j - entry_bar, pnl > 0, "long" if is_long else "short"))
                in_pos_until = j; cooldown_until = j + cfg.cooldown
                break
    return trades


def stats(trades: list[Trade]) -> dict:
    if not trades:
        return {"n": 0, "wr": 0.0, "pf": np.nan, "exp": 0.0, "net": 0.0, "dd": 0.0}
    pnl = np.array([t.pnl_r for t in trades])
    wins = (pnl > 0).sum()
    gp = pnl[pnl > 0].sum()
    gl = pnl[pnl <= 0].sum()
    eq = np.cumsum(pnl)
    return {
        "n": len(trades), "wr": wins/len(trades)*100,
        "pf": gp/abs(gl) if gl < 0 else np.inf,
        "exp": pnl.mean(), "net": pnl.sum(),
        "dd": float((np.maximum.accumulate(eq) - eq).max()),
    }


def evaluate_ext(cfg: ExtConfig, df: pd.DataFrame) -> dict:
    sig = compute_signals_ext(df, cfg)
    trades = simulate_ext(sig, cfg)
    return stats(trades)


# ============================================================
# Test runner
# ============================================================
def make_base_ext(name: str) -> ExtConfig:
    """BASE Relaxed を ExtConfig に変換"""
    b = BASE[name].__dict__
    return ExtConfig(**b)


TECHNIQUES = {
    "T0: Baseline (Relaxed)":   dict(),
    "T1: プルバック 0.5*ATR":     dict(pullback_atr=0.5, pullback_max_bars=8),
    "T2: プルバック 1.0*ATR":     dict(pullback_atr=1.0, pullback_max_bars=12),
    "T3: 確認バー (Seq)":         dict(require_seq_confirm=True),
    "T4: ATR拡大 x1.2":          dict(atr_expansion_ratio=1.2),
    "T5: D1 SMA20 一致":         dict(htf_trend_d=20),
    "T6: D1 SMA50 一致":         dict(htf_trend_d=50),
    "T7: 体/レンジ 60%":          dict(body_ratio_min=0.6),
    "T8: 時間決済 48本":         dict(time_exit_bars=48),
    "T9: ブレイクバーRange>=2ATR": dict(range_atr_min=2.0),
    "T10: スイープ (逆張り)":      dict(sweep_mode=True),
    "T11: プルバック+D1SMA50":    dict(pullback_atr=0.5, pullback_max_bars=8, htf_trend_d=50),
    "T12: プルバック+体力60%":    dict(pullback_atr=0.5, pullback_max_bars=8, body_ratio_min=0.6),
}


def run_oos(instruments: list[str]):
    print("=" * 100)
    print("【新手法 OOS 検証】 Train(2014-2020) / Test(2021-2024) で同じ設定を評価")
    print("=" * 100)

    data = {}
    for name in instruments:
        try:
            data[name] = load_instrument(name)
        except Exception as e:
            print(f"[SKIP] {name}: {e}")

    # 各手法×通貨で Train/Test を評価
    rows = []
    for tname, mods in TECHNIQUES.items():
        for inst, df in data.items():
            base = make_base_ext(inst).__dict__.copy()
            cfg = ExtConfig(**{**base, **mods})
            train_df = df[df.index.year <= TRAIN_END]
            test_df  = df[df.index.year >= TEST_START]
            s_tr = evaluate_ext(cfg, train_df)
            s_te = evaluate_ext(cfg, test_df)
            rows.append({"tech": tname, "inst": inst,
                         "tr_n": s_tr["n"], "tr_wr": s_tr["wr"], "tr_net": s_tr["net"],
                         "te_n": s_te["n"], "te_wr": s_te["wr"], "te_net": s_te["net"],
                         "te_pf": s_te["pf"], "te_dd": s_te["dd"]})
    df_r = pd.DataFrame(rows)

    # 各手法の TEST 合計
    print("\n--- 手法別 TEST 期間 合計 (2021-2024) ---")
    summary = df_r.groupby("tech").agg(
        tr_net=("tr_net", "sum"),
        te_net=("te_net", "sum"),
        te_n=("te_n", "sum"),
        te_wr=("te_wr", "mean"),
    ).reset_index()
    summary["te_ratio"] = summary["te_net"] / summary["tr_net"].replace(0, np.nan) * 100
    summary = summary.sort_values("te_net", ascending=False)
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.1f}"))

    # 手法別×通貨の TEST 詳細 (ベースラインとの比較)
    base_te = df_r[df_r["tech"] == "T0: Baseline (Relaxed)"].set_index("inst")["te_net"]
    pvt = df_r.pivot(index="inst", columns="tech", values="te_net")
    pvt = pvt.loc[base_te.index]  # 並び固定
    diff = pvt.sub(base_te, axis=0)
    print("\n--- TEST 期間: 各手法のベースラインとの差 (+ベース対比) ---")
    print(diff.to_string(float_format=lambda x: f"{x:+.1f}"))

    # 通貨別ベスト手法
    print("\n--- 通貨別 TEST ベスト手法 ---")
    for inst in data.keys():
        sub = df_r[df_r["inst"] == inst].sort_values("te_net", ascending=False)
        b = sub.iloc[0]
        base_row = sub[sub["tech"] == "T0: Baseline (Relaxed)"].iloc[0]
        delta = b["te_net"] - base_row["te_net"]
        print(f"  {inst:7} → [{b['tech']:30}] TEST: n={b['te_n']:>4} WR={b['te_wr']:5.1f}% "
              f"PF={b['te_pf']:5.2f} Net={b['te_net']:+6.1f}R DD={b['te_dd']:.1f}R "
              f"(vs Base: {delta:+.1f}R)")

    return df_r, summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", nargs="+",
                    default=["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"])
    args = ap.parse_args()
    run_oos(args.instruments)

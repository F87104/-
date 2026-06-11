#!/usr/bin/env python3
"""
Synapse 精度向上フィルタ検証（ステップ1）

run_synapse_tv_h4.py と同じ土台（既存Synapseエンジン + TradingView H4）で、
ihs_5pivot の各銘柄ベスト構成に対し、以下の精度向上フィルタを重ねて
PF/DD が改善するかを総当たりで調べる。

  - ADX下限         : トレンド強度（弱い反転を除外）
  - 調整時間下限     : adjust_ratio（浅すぎる2波を除外）
  - 実体比率下限     : signal_body_ratio（ヒゲ主体の反転を除外）

ベース構成（ihs_5pivot のフィルタ/TP）は各銘柄の summary_by_structure.csv から
total_r 最良（trades>=20）を自動採用する。

出力:
  - results_tv_h4/<SYMBOL>/precision_sweep.csv
  - docs/research/Synapse_精度向上フィルタ_2026-06-11.md
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
TV_DATA = REPO_ROOT / "tv_data"
RES = THIS_DIR / "results_tv_h4"
REPORT = REPO_ROOT / "docs" / "research" / "Synapse_精度向上フィルタ_2026-06-11.md"

_spec = importlib.util.spec_from_file_location("synapse_engine", THIS_DIR / "run_synapse_definition_grid.py")
eng = importlib.util.module_from_spec(_spec)
sys.modules["synapse_engine"] = eng
_spec.loader.exec_module(eng)

# tvランナーの読み込み・銘柄判定・コストを再利用
_spec2 = importlib.util.spec_from_file_location("synapse_tv", THIS_DIR / "run_synapse_tv_h4.py")
tv = importlib.util.module_from_spec(_spec2)
sys.modules["synapse_tv"] = tv
_spec2.loader.exec_module(tv)

ADX_MINS = [0, 18, 22, 26]
ADJUST_MINS = [0.0, 0.5, 1.0]
BODY_MINS = [0.0, 0.35, 0.45]

SYMBOL_ORDER = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "XAUUSD", "XAGUSD", "NAS100"]


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    alpha = 1.0 / period
    atr_ = tr.ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=alpha, adjust=False).mean()


def best_base(symbol: str) -> tuple[str, str] | None:
    f = RES / symbol / "summary_by_structure.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    d = d[(d["structure"] == "ihs_5pivot") & (d["filter"].isin(["context", "diag_break"])) & (d["trades"] >= 20)]
    if d.empty:
        return None
    r = d.sort_values("total_r", ascending=False).iloc[0]
    return str(r["filter"]), str(r["target_model"])


def stats(r: pd.Series) -> dict:
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": eng.profit_factor(r),
        "max_dd_r": eng.max_drawdown(r),
    }


def build_trades(path: Path) -> tuple[str, pd.DataFrame] | None:
    symbol = tv.detect_symbol(path)
    raw = tv.load_tv_csv(path)
    if len(raw) < 500:
        return None
    spread, slip = tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))
    eng.SPREAD_PRICE, eng.SLIP_PRICE = spread, slip
    config = eng.TIMEFRAME_CONFIGS["H4"]
    h4 = eng.add_indicators(raw, "H4")
    h4["adx"] = adx(raw)
    d1 = eng.add_indicators(eng.resample_ohlc(raw, "1D"), "D1")
    h4 = eng.attach_upper_context(h4, {"D1": d1}, "H4")
    _, trades = eng.run_timeframe(h4, "H4", config)
    if trades.empty:
        return None
    adx_by_time = h4["adx"]
    trades["adx"] = trades["signal_time"].map(adx_by_time)
    trades["is_oos"] = trades["entry_time"] >= eng.OOS_START
    return symbol, trades


def sweep_symbol(symbol: str, trades: pd.DataFrame) -> tuple[pd.DataFrame, dict] | None:
    base = best_base(symbol)
    if base is None:
        return None
    filt, tp = base
    sub = trades[(trades["structure"] == "ihs_5pivot") & (trades["filter"] == filt) & (trades["target_model"] == tp)].copy()
    if len(sub) < 20:
        return None

    base_stats = stats(sub["r_after_cost"])
    base_stats.update({"adx_min": 0, "adjust_min": 0.0, "body_min": 0.0, "is_base": True})

    rows = [base_stats]
    for a in ADX_MINS:
        for adj in ADJUST_MINS:
            for b in BODY_MINS:
                if a == 0 and adj == 0.0 and b == 0.0:
                    continue
                m = sub[(sub["adx"].fillna(0) >= a) & (sub["adjust_ratio"] >= adj) & (sub["signal_body_ratio"] >= b)]
                if m.empty:
                    continue
                s = stats(m["r_after_cost"])
                s.update({"adx_min": a, "adjust_min": adj, "body_min": b, "is_base": False})
                rows.append(s)

    df = pd.DataFrame(rows)
    df.to_csv(RES / symbol / "precision_sweep.csv", index=False)

    # 採用候補: trades>=15 かつ PFがベース以上、PF優先・DD小優先
    cand = df[(~df["is_base"]) & (df["trades"] >= 15) & (df["pf"] >= base_stats["pf"])]
    best = None
    if not cand.empty:
        best = cand.sort_values(["pf", "total_r"], ascending=[False, False]).iloc[0].to_dict()
    return df, {"symbol": symbol, "filter": filt, "tp": tp, "base": base_stats, "best": best}


def fmt(x) -> str:
    if isinstance(x, float) and (x != x):
        return ""
    return f"{x:.2f}" if isinstance(x, float) else str(x)


def main() -> None:
    files = sorted(TV_DATA.glob("*.csv"))
    summaries = []
    for path in files:
        try:
            built = build_trades(path)
        except Exception as e:  # noqa: BLE001
            print(f"[error] {path.name}: {e}")
            continue
        if not built:
            continue
        symbol, trades = built
        res = sweep_symbol(symbol, trades)
        if res is None:
            print(f"[skip] {symbol}: ベース構成なし or トレード不足")
            continue
        _, summ = res
        summaries.append(summ)
        b = summ["base"]
        print(f"\n■ {symbol}  base={summ['filter']}+{summ['tp']}  "
              f"PF {b['pf']:.2f} / {b['trades']}件 / {b['total_r']:.1f}R / DD {b['max_dd_r']:.1f}R")
        if summ["best"]:
            x = summ["best"]
            print(f"   → 精度版 ADX≥{x['adx_min']} adj≥{x['adjust_min']} body≥{x['body_min']}: "
                  f"PF {x['pf']:.2f} / {x['trades']}件 / {x['total_r']:.1f}R / DD {x['max_dd_r']:.1f}R")
        else:
            print("   → ベース超えの精度版なし")

    order = {s: i for i, s in enumerate(SYMBOL_ORDER)}
    summaries.sort(key=lambda s: order.get(s["symbol"], 99))

    lines = [
        "# Synapse 精度向上フィルタ検証（2026-06-11）",
        "",
        "> `run_synapse_precision_filters.py` の出力。ihs_5pivot の各銘柄ベスト構成に",
        "> **ADX下限 / 調整時間下限(adjust_ratio) / 実体比率下限(body)** を重ねて総当たり。",
        "> 採用候補は trades≥15 かつ PF がベース以上のうち PF 最良。",
        "",
        "## ベース vs 精度版（ihs_5pivot）",
        "",
        "| 銘柄 | ベース構成 | ベースPF | ベース件数 | ベースDD | 精度フィルタ | 精度PF | 精度件数 | 精度DD |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for s in summaries:
        b = s["base"]
        if s["best"]:
            x = s["best"]
            pfilt = f"ADX≥{x['adx_min']} / adj≥{x['adjust_min']} / body≥{x['body_min']}"
            lines.append(
                f"| {s['symbol']} | {s['filter']}+{s['tp']} | {fmt(b['pf'])} | {b['trades']} | {fmt(b['max_dd_r'])} | "
                f"{pfilt} | {fmt(x['pf'])} | {x['trades']} | {fmt(x['max_dd_r'])} |"
            )
        else:
            lines.append(
                f"| {s['symbol']} | {s['filter']}+{s['tp']} | {fmt(b['pf'])} | {b['trades']} | {fmt(b['max_dd_r'])} | "
                f"（改善なし） | - | - | - |"
            )

    lines += [
        "",
        "## 読み方・注意",
        "",
        "- 精度フィルタは「件数を削ってPF/DDを改善」する方向。件数が減りすぎる版は過信しない。",
        "- ADX は H4 の Wilder ADX(14)。adjust_ratio は2波の時間/1波の時間。body は確定足の実体比率。",
        "- ここで有効だったフィルタを、次段で Pine（synapse_mtf_wave_reversal_v4）へ移植候補にする。",
        "",
        "## 次のステップ",
        "",
        "- [ ] 採用フィルタを各銘柄の推奨プリセットとして固定",
        "- [ ] TradingView でその条件の候補が人の目で納得できるか確認",
        "- [ ] H1 への展開可否を検証",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n書き出し: {REPORT}")


if __name__ == "__main__":
    main()

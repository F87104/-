#!/usr/bin/env python3
"""Compare Cap/Squeeze on H1 vs H4 (same Pine bar-count params)."""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_elliott_fibo_study import INSTRUMENTS, SYMBOLS, add_indicators, load_instrument, resample_ohlc
from run_market_psychology_strategy_tv_check import (
    PsySpec,
    add_features,
    capitulation_signal,
    period_name,
    simulate_long,
    squeeze_signal,
)

OUT = ROOT / "docs/research/cap_sqz_h1_vs_h4_2026-06-01"
OUT.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")

CORE4 = {"XAUUSD", "USDJPY", "CHFJPY", "SILVER"}
PROD5 = {"XAUUSD", "USDJPY", "EURJPY", "CHFJPY", "SILVER"}
EXCLUDE = {"GBPJPY", "AUDJPY"}

PINE_SQZ = PsySpec("SQZ_PINE", "short_squeeze")
SQZ_STRICT = replace(PINE_SQZ, name="SQZ_STRICT", shelf_atr=2.0, move_atr=3.5)
PINE_CAP = PsySpec("CAP_PINE", "capitulation")


def pf(r: pd.Series) -> float:
    w = float(r[r > 0].sum())
    l = float(r[r <= 0].sum())
    return w / abs(l) if l < 0 else (math.inf if w > 0 else math.nan)


def add_features_tf(raw: pd.DataFrame, tf: str) -> pd.DataFrame:
    h = add_indicators(resample_ohlc(raw, tf))
    import numpy as np

    rng = (h["high"] - h["low"]).replace(0.0, np.nan)
    h["close_location"] = ((h["close"] - h["low"]) / rng).fillna(0.5)
    h["lower_wick_ratio"] = ((np.minimum(h["open"], h["close"]) - h["low"]) / rng).fillna(0.0)
    h["range_atr"] = (h["high"] - h["low"]) / h["atr"].replace(0.0, np.nan)
    d1 = resample_ohlc(raw, "D1")
    d1["d1_ema50_prev"] = d1["close"].ewm(span=50, adjust=False).mean().shift(1)
    h["d1_ema50_prev"] = d1["d1_ema50_prev"].reindex(h.index, method="ffill")
    return h


def run_sqz(df: pd.DataFrame, symbol: str, spec: PsySpec, tf: str, max_hold: int) -> pd.DataFrame:
    rows = []
    in_pos = -1
    start_i = max(80, spec.shelf_bars + spec.drop_win + 2, spec.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or i <= in_pos:
            continue
        sig = squeeze_signal(df, i, spec)
        if sig is None or float(df["close"].iloc[i]) <= float(sig["stop"]):
            continue
        trade = simulate_long(df, symbol, i, float(sig["stop"]), spec.rr, max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "timeframe": tf,
                "symbol": symbol,
                "variant": spec.name,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                "max_hold": max_hold,
                **sig,
                **trade,
            }
        )
        in_pos = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def run_cap(df: pd.DataFrame, symbol: str, spec: PsySpec, tf: str, max_hold: int) -> pd.DataFrame:
    rows = []
    in_pos = -1
    start_i = max(80, spec.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or i <= in_pos:
            continue
        sig = capitulation_signal(df, i, spec)
        if sig is None or float(df["close"].iloc[i]) <= float(sig["stop"]):
            continue
        trade = simulate_long(df, symbol, i, float(sig["stop"]), spec.rr, max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "timeframe": tf,
                "symbol": symbol,
                "variant": "CAP_PINE",
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                "max_hold": max_hold,
                **sig,
                **trade,
            }
        )
        in_pos = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(trades=0, win_rate=0.0, total_r=0.0, avg_r=0.0, pf=math.nan, max_dd_r=0.0, tp_pct=0.0, trades_per_year=0.0)
    r = df["r_after_cost"].astype(float)
    curve = r.cumsum()
    yrs = max((df["entry_time"].max() - df["entry_time"].min()).days / 365.25, 1)
    return dict(
        trades=len(r),
        win_rate=round((r > 0).mean() * 100, 1),
        total_r=round(r.sum(), 2),
        avg_r=round(r.mean(), 3),
        pf=round(pf(r), 2),
        max_dd_r=round(float((curve.cummax() - curve).max()), 2),
        tp_pct=round((df["exit_reason"] == "target").mean() * 100, 1),
        trades_per_year=round(len(r) / yrs, 1),
    )


def filter_research(df: pd.DataFrame, symbols: set[str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out = out[(out["entry_time"] >= RUN_START) & (out["entry_time"] <= RESEARCH_END)]
    return out[out["symbol"].isin(symbols)]


def main() -> None:
    variants = [
        ("SQZ_PINE", replace(PINE_SQZ, rr=2.0), "sqz"),
        ("SQZ_STRICT", replace(SQZ_STRICT, rr=2.0), "sqz"),
        ("SQZ_PINE_25", replace(PINE_SQZ, rr=2.5), "sqz"),
        ("CAP_PINE", replace(PINE_CAP, rr=2.0), "cap"),
    ]
    hold_modes = [
        ("hold120", 120),
        ("hold480_H1_equiv_30d", 480),  # H1: ~30 calendar days like 120 H4 bars
    ]

    all_trades = []
    summary_rows = []

    for tf in ["H1", "H4"]:
        data = {}
        for symbol in SYMBOLS:
            if symbol not in INSTRUMENTS:
                continue
            data[symbol] = add_features_tf(load_instrument(symbol), tf)

        for vname, spec, kind in variants:
            for hold_label, max_hold in hold_modes:
                if tf == "H4" and hold_label == "hold480_H1_equiv_30d":
                    continue
                if tf == "H1" and hold_label == "hold120" and kind == "cap":
                    pass  # run both holds for cap on H1 too
                parts = []
                for symbol, df in data.items():
                    if kind == "sqz":
                        t = run_sqz(df, symbol, replace(spec, name=vname), tf, max_hold)
                    else:
                        t = run_cap(df, symbol, replace(PINE_CAP, rr=spec.rr), tf, max_hold)
                    if not t.empty:
                        parts.append(t)
                trades = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
                if not trades.empty:
                    trades["hold_mode"] = hold_label
                    all_trades.append(trades)

                for uni_label, symset in [("ALL7", set(SYMBOLS)), ("PROD5", PROD5), ("CORE4", CORE4)]:
                    sub = filter_research(trades, symset)
                    sub = sub[~sub["symbol"].isin(EXCLUDE)] if uni_label != "ALL7" else sub
                    m = metrics(sub)
                    summary_rows.append(
                        {
                            "timeframe": tf,
                            "variant": vname,
                            "hold_mode": hold_label,
                            "universe": uni_label,
                            **m,
                        }
                    )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "summary_h1_vs_h4.csv", index=False)

    if all_trades:
        full = pd.concat(all_trades, ignore_index=True)
        full.to_csv(OUT / "trades_all.csv", index=False)

    # pivot for report: CORE4 research SQZ strict hold120
    core = summary[
        (summary["universe"] == "CORE4")
        & (summary["variant"].isin(["SQZ_PINE", "SQZ_STRICT", "SQZ_PINE_25"]))
        & (summary["hold_mode"] == "hold120")
    ].sort_values(["variant", "timeframe"])

    lines = [
        "# 踏み上げ・投げ切り — H1 vs H4 検証",
        "",
        "## 前提",
        "",
        "- **同じ本数パラメータ**（PineをH1に貼ったときと同じ）",
        "  - 棚6本・急落窓6本・投げ切り窓24本 など",
        "- H1の6本 ≈ **6時間**、H4の6本 ≈ **24時間**（時間スケールは違う）",
        "- 出口: SL棚安-0.25ATR、TP=2R/2.5R、次足始値",
        "- 研究期: 2015-2024、コスト込みR",
        "",
        "## コア比較（CORE4・GBP/AUD除外・hold120本）",
        "",
        core.to_string(index=False),
        "",
        "## 読み方",
        "",
        "- **件数/年** が H1 >> H4 なら、同じパラメータでもH1の方がシグナルが多い",
        "- **PF・合計R** が H1 で上なら、あなたの「H1の方が良い」はデータでも支持",
        "- H1で max_hold=480 は「H4の120本と同じ約30日」を揃えた感度",
        "",
        "## ファイル",
        "",
        f"- `{OUT.relative_to(ROOT)}/summary_h1_vs_h4.csv`",
    ]
    (OUT / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(core.to_string(index=False))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

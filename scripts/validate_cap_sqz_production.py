#!/usr/bin/env python3
"""
Production validation for Pine visual scanner: Capitulation + Short Squeeze.

Matches user Pine defaults (踏み上げ投げ切り indicator).
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_market_psychology_strategy_tv_check import (  # noqa: E402
    PsySpec,
    add_features,
    capitulation_signal,
    load_data,
    period_name,
    simulate_long,
    squeeze_signal,
    summarize,
)
from run_elliott_fibo_study import INSTRUMENTS, SYMBOLS, load_instrument  # noqa: E402

OUT_DIR = ROOT / "docs" / "research" / "cap_sqz_production_validation_2026-06-01"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")
EXCLUDE = {"GBPJPY", "AUDJPY"}

# Pine visual scanner defaults
PINE_SQZ = PsySpec("SQZ_PINE", "short_squeeze")
PINE_CAP = PsySpec("CAP_PINE", "capitulation")
PINE_SQZ_STRICT = replace(PINE_SQZ, name="SQZ_STRICT", shelf_atr=2.0, move_atr=3.5)


def run_signals(
    df: pd.DataFrame,
    symbol: str,
    *,
    rr: float,
    max_hold: int,
    allow_cap: bool,
    allow_sqz: bool,
    prefer: str,
) -> pd.DataFrame:
    rows: list[dict] = []
    in_pos_until = -1
    start_i = max(80, PINE_SQZ.shelf_bars + PINE_SQZ.drop_win + 2, PINE_CAP.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < pd.Timestamp("2015-01-01") or ts > pd.Timestamp("2026-12-31 23:59:59"):
            continue
        if i <= in_pos_until:
            continue
        sqz = squeeze_signal(df, i, replace(PINE_SQZ, rr=rr, max_hold=max_hold)) if allow_sqz else None
        cap = capitulation_signal(df, i, replace(PINE_CAP, rr=rr, max_hold=max_hold)) if allow_cap else None
        if sqz is None and cap is None:
            continue
        if sqz is not None and cap is not None:
            if prefer == "sqz":
                signal, kind = sqz, "short_squeeze"
            elif prefer == "cap":
                signal, kind = cap, "capitulation"
            else:
                signal, kind = sqz, "short_squeeze+capitulation"
        else:
            signal = sqz if sqz is not None else cap
            kind = signal["signal_kind"]
        if float(df["close"].iloc[i]) <= float(signal["stop"]):
            continue
        trade = simulate_long(df, symbol, i, float(signal["stop"]), rr, max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "signal_kind": kind,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "rr": rr,
                **signal,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def filter_trades(trades: pd.DataFrame, *, research_only: bool, ex_symbols: set[str]) -> pd.DataFrame:
    if trades.empty:
        return trades
    out = trades.copy()
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    if research_only:
        out = out[out["entry_time"] <= RESEARCH_END]
    if ex_symbols:
        out = out[~out["symbol"].isin(ex_symbols)]
    return out


def overlap_tb(trades: pd.DataFrame) -> pd.DataFrame:
    tb_path = ROOT / "backtests" / "trendbreak_v1" / "fakeout_before_after_2015_2024" / "trades.csv"
    if not trades.empty and tb_path.exists():
        tb = pd.read_csv(tb_path, parse_dates=["entry_time", "exit_time"])
        tb = tb[tb["direction"].str.lower() == "long"]
        rows = []
        for _, t in trades.iterrows():
            sym = t["symbol"]
            overlap = tb[
                (tb["symbol"] == sym)
                & (tb["entry_time"] <= t["exit_time"])
                & (tb["exit_time"] >= t["entry_time"])
            ]
            rows.append(len(overlap) > 0)
        trades = trades.copy()
        trades["overlaps_tb"] = rows
    return trades


def main() -> None:
    data = load_data()
    cases = [
        ("SQZ_PINE_2R", dict(allow_cap=False, allow_sqz=True, prefer="sqz", rr=2.0)),
        ("SQZ_PINE_2.5R", dict(allow_cap=False, allow_sqz=True, prefer="sqz", rr=2.5)),
        ("SQZ_STRICT_2R", dict(allow_cap=False, allow_sqz=True, prefer="sqz", rr=2.0, sqz_spec=True)),
        ("CAP_PINE_2R", dict(allow_cap=True, allow_sqz=False, prefer="cap", rr=2.0)),
        ("CAP_PINE_2.5R", dict(allow_cap=True, allow_sqz=False, prefer="cap", rr=2.5)),
        ("BOTH_PINE_2R", dict(allow_cap=True, allow_sqz=True, prefer="sqz", rr=2.0)),
        ("BOTH_PINE_2.5R", dict(allow_cap=True, allow_sqz=True, prefer="sqz", rr=2.5)),
    ]
    all_frames: list[pd.DataFrame] = []
    summary_rows: list[dict] = []

    for name, cfg in cases:
        rr = cfg["rr"]
        max_hold = 120
        frames = []
        for symbol, df in data.items():
            if cfg.get("sqz_spec"):
                # strict squeeze only: patch via custom run
                spec = replace(PINE_SQZ_STRICT, rr=rr, max_hold=max_hold)
                rows = []
                in_pos_until = -1
                start_i = max(80, spec.shelf_bars + spec.drop_win + 2)
                for i in range(start_i, len(df) - 1):
                    ts = df.index[i]
                    if ts < pd.Timestamp("2015-01-01") or ts > pd.Timestamp("2026-12-31 23:59:59"):
                        continue
                    if i <= in_pos_until:
                        continue
                    sig = squeeze_signal(df, i, spec)
                    if sig is None or float(df["close"].iloc[i]) <= float(sig["stop"]):
                        continue
                    trade = simulate_long(df, symbol, i, float(sig["stop"]), rr, max_hold)
                    if trade is None:
                        continue
                    rows.append({"symbol": symbol, "signal_kind": "short_squeeze", "signal_time": ts, "period": period_name(pd.Timestamp(trade["entry_time"])), "rr": rr, **sig, **trade})
                    in_pos_until = int(df.index.get_loc(trade["exit_time"]))
                tdf = pd.DataFrame(rows)
            else:
                tdf = run_signals(
                    df,
                    symbol,
                    rr=rr,
                    max_hold=max_hold,
                    allow_cap=cfg["allow_cap"],
                    allow_sqz=cfg["allow_sqz"],
                    prefer=cfg["prefer"],
                )
            if not tdf.empty:
                tdf["case"] = name
                frames.append(tdf)
        trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if not trades.empty:
            trades = overlap_tb(trades)
            all_frames.append(trades)
        for label, subset in [
            (f"{name}_ALL", trades),
            (f"{name}_exGBPJPY", filter_trades(trades, research_only=False, ex_symbols={"GBPJPY"})),
            (f"{name}_exGBP_AUD_research", filter_trades(trades, research_only=True, ex_symbols=EXCLUDE)),
        ]:
            row = summarize(subset, label)
            row["case"] = name
            row["filter"] = label.split(name)[-1].strip("_") or "ALL"
            if not subset.empty and "overlaps_tb" in subset.columns:
                row["tb_overlap_pct"] = round(float(subset["overlaps_tb"].mean() * 100), 1)
            summary_rows.append(row)

    all_trades = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    summary = pd.DataFrame(summary_rows)
    all_trades.to_csv(OUT_DIR / "trades_all.csv", index=False)
    summary.to_csv(OUT_DIR / "summary.csv", index=False)

    lines = [
        "# 投げ切り・踏み上げ 本番導入検証",
        "",
        "Pine visual scanner（ユーザー提示デフォルト）と同義の Python 検証。",
        "",
        "## 出口",
        "- SL: 棚安値 or 投げ切り足安値 − 0.25 ATR",
        "- TP: 固定 R（2.0 / 2.5）",
        "- エントリー: シグナル次足始値",
        "- 最大保有: 120 H4本",
        "",
        "## サマリー",
        "",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"- **{r['label']}**: {int(r['trades'])}件 WR {r['win_rate']:.1f}% "
            f"PF {r['pf']:.2f} +{r['total_r']:.1f}R DD {r['max_dd_r']:.1f}R"
        )
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"\nWrote {OUT_DIR}")


if __name__ == "__main__":
    main()

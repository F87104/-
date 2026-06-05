#!/usr/bin/env python3
"""
B06 VIS PRECALM — rerun on TradingView OANDA H4 CSV and compare to F87104 + TV tester.

Goal: TV execution parity. Python on TV OHLC is the verification baseline for Pine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
TV_DIR = OUT
VIS_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]

sys.path.insert(0, str(ELLIOTT))

from run_h4_v_initial_shelf_deep_dive import (  # noqa: E402
    CURRENT_SPEC,
    prepare_data,
    run_spec,
)

F87104_USDJPY = OUT / "by_symbol/b06_usdjpy.csv"
TV_TESTER = OUT / "tv_strategy_trades_usdjpy.csv"
# TV chart UNIX = UTC bar open; UI (UTC+9) shows +9h — matches Strategy Tester list
TV_DISPLAY_OFFSET_HOURS = 9


def to_tv_display(ts: pd.Series) -> pd.Series:
    return pd.to_datetime(ts) + pd.Timedelta(hours=TV_DISPLAY_OFFSET_HOURS)


def signal_key(symbol: str, signal_time: pd.Timestamp) -> str:
    return f"{symbol}|{pd.Timestamp(signal_time).strftime('%Y-%m-%d %H:%M:%S')}"


def slim_trades(df: pd.DataFrame, data_source: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["data_source"] = data_source
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"]) if "exit_time" in out.columns else pd.NaT
    out["signal_time_tv"] = to_tv_display(out["signal_time"])
    out["entry_time_tv"] = to_tv_display(out["entry_time"])
    out["exit_time_tv"] = to_tv_display(out["exit_time"])
    cols = [
        "symbol",
        "data_source",
        "signal_time",
        "signal_time_tv",
        "entry_time",
        "entry_time_tv",
        "entry",
        "signal_close",
        "stop",
        "target",
        "shelf_high",
        "shelf_low",
        "exit_time",
        "exit_time_tv",
        "exit_reason",
        "r_after_cost",
        "pair_key",
        "v_low_time",
        "v_start_time",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols].sort_values(["symbol", "signal_time"]).reset_index(drop=True)


def compare_expected(f87104: pd.DataFrame, tv_oanda: pd.DataFrame) -> pd.DataFrame:
    rows = []
    f_keys = {signal_key(r.symbol, r.signal_time): r for _, r in f87104.iterrows()}
    t_keys = {signal_key(r.symbol, r.signal_time): r for _, r in tv_oanda.iterrows()}
    for k in sorted(set(f_keys) | set(t_keys)):
        in_f = k in f_keys
        in_t = k in t_keys
        row = {
            "key": k,
            "in_f87104": in_f,
            "in_tv_oanda_py": in_t,
            "match": in_f and in_t,
        }
        if in_f and in_t:
            fr, tr = f_keys[k], t_keys[k]
            row["entry_diff_pips"] = round((float(fr.entry) - float(tr.entry)) / 0.01, 2)
            row["stop_diff_pips"] = round((float(fr.stop) - float(tr.stop)) / 0.01, 2)
        rows.append(row)
    return pd.DataFrame(rows)


def match_tv_tester(tv_oanda: pd.DataFrame, tester: pd.DataFrame, tol_hours: float = 2.0) -> pd.DataFrame:
    rows = []
    tester = tester.copy()
    tester["entry_time"] = pd.to_datetime(tester["entry_time"])
    for _, py in tv_oanda.iterrows():
        ent_tv = pd.Timestamp(py["entry_time_tv"])
        tester["dist"] = (tester["entry_time"] - ent_tv).abs()
        near = tester.sort_values("dist")
        best = near.iloc[0] if not near.empty else None
        gap_h = best["dist"].total_seconds() / 3600 if best is not None else float("nan")
        rows.append(
            {
                "signal_time_utc": py["signal_time"],
                "signal_time_tv": py["signal_time_tv"],
                "entry_time_utc": py["entry_time"],
                "entry_time_tv": py["entry_time_tv"],
                "py_entry": py["entry"],
                "nearest_tv_entry_time": best["entry_time"] if best is not None else "",
                "nearest_tv_entry_price": best.get("entry_price", float("nan")) if best is not None else float("nan"),
                "hour_gap": round(gap_h, 2),
                "tv_match": "OK" if gap_h <= tol_hours else "MISS",
            }
        )
    return pd.DataFrame(rows)


def write_report(
    symbol: str,
    f87104: pd.DataFrame,
    tv_oanda: pd.DataFrame,
    cmp_df: pd.DataFrame,
    tester_match: pd.DataFrame,
) -> None:
    n_f = len(f87104)
    n_t = len(tv_oanda)
    n_match = int(cmp_df["match"].sum()) if not cmp_df.empty else 0
    ok = int((tester_match["tv_match"] == "OK").sum()) if not tester_match.empty else 0
    lines = [
        f"# B06 {symbol} — TV OANDA データでの Python 再実行",
        "",
        "## 目的",
        "",
        "TradingView で執行する前提で、**検証は TV OANDA H4 CSV 上の Python** を正とする。",
        "",
        "## 件数",
        "",
        f"| 系列 | 件数 |",
        f"|------|------|",
        f"| F87104 H1→H4（従来） | **{n_f}** |",
        f"| TV OANDA H4 CSV（今回） | **{n_t}** |",
        f"| 同一 signal_time | **{n_match}** |",
        f"| TVテスターと1日以内（TV-OHLC Python） | **{ok}/{n_t}** |",
        "",
        "## F87104 vs TV-OHLC Python",
        "",
    ]
    only_f = cmp_df[~cmp_df["in_tv_oanda_py"] & cmp_df["in_f87104"]] if not cmp_df.empty else pd.DataFrame()
    only_t = cmp_df[~cmp_df["in_f87104"] & cmp_df["in_tv_oanda_py"]] if not cmp_df.empty else pd.DataFrame()
    if not only_f.empty:
        lines.append("**F87104のみ:**")
        for k in only_f["key"]:
            lines.append(f"- {k}")
        lines.append("")
    if not only_t.empty:
        lines.append("**TV-OHLC Pythonのみ:**")
        for k in only_t["key"]:
            lines.append(f"- {k}")
        lines.append("")
    lines.extend(
        [
            "## 次の作業（Pine）",
            "",
            "1. TVチャートで `python_expected_b06_tv_oanda_<symbol>.csv` の signal_time にラベルがあるか",
            "2. 無い日は `showSkips=ON` で skipCode を記録",
            "3. Pine を直し、**TV-OHDC Python とラベル日時が一致**するまで繰り返す",
            "4. ストラテジーテスター件数も同じ signal に揃うか確認",
            "",
            "## ファイル",
            "",
            f"- `python_expected_b06_tv_oanda_{symbol.lower()}.csv`",
            f"- `b06_f87104_vs_tv_oanda_{symbol.lower()}.csv`",
            f"- `b06_tv_oanda_vs_tester_{symbol.lower()}.csv`",
            "",
            "再現: `python3 scripts/run_b06_tv_oanda_parity.py`",
        ]
    )
    (OUT / f"B06_TV_OANDA_RERUN_{symbol}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    symbols_with_csv = [s for s in VIS_SYMBOLS if (TV_DIR / f"tv_{s.lower()}_h4.csv").exists()]
    if not symbols_with_csv:
        print(f"No tv_*_h4.csv under {TV_DIR}")
        sys.exit(1)

    print(f"TV OANDA CSV symbols: {symbols_with_csv}")
    data, pivots = prepare_data(data_source="tv_oanda", tv_csv_dir=TV_DIR, symbols=symbols_with_csv)
    tv_trades = run_spec(data, pivots, CURRENT_SPEC, symbols_with_csv)

    for symbol in symbols_with_csv:
        sub = tv_trades[tv_trades["symbol"] == symbol] if not tv_trades.empty else pd.DataFrame()
        tv_slim = slim_trades(sub, "tv_oanda")
        tv_slim.to_csv(OUT / f"python_expected_b06_tv_oanda_{symbol.lower()}.csv", index=False)

        f_path = OUT / f"by_symbol/b06_{symbol.lower()}.csv"
        f87104 = pd.DataFrame()
        if f_path.exists():
            f87104 = pd.read_csv(f_path, parse_dates=["signal_time", "entry_time"])
            cmp_df = compare_expected(f87104, tv_slim)
            cmp_df.to_csv(OUT / f"b06_f87104_vs_tv_oanda_{symbol.lower()}.csv", index=False)
        else:
            cmp_df = pd.DataFrame()

        tester_match = pd.DataFrame()
        tester_path = OUT / f"tv_strategy_trades_{symbol.lower()}.csv"
        if tester_path.exists():
            tester = pd.read_csv(tester_path)
            tester_match = match_tv_tester(tv_slim, tester)
            tester_match.to_csv(OUT / f"b06_tv_oanda_vs_tester_{symbol.lower()}.csv", index=False)
        elif symbol == "USDJPY" and TV_TESTER.exists():
            tester = pd.read_csv(TV_TESTER)
            tester_match = match_tv_tester(tv_slim, tester)
            tester_match.to_csv(OUT / f"b06_tv_oanda_vs_tester_{symbol.lower()}.csv", index=False)

        write_report(symbol, f87104, tv_slim, cmp_df, tester_match)
        print(f"\n=== {symbol} ===")
        print(f"TV-OHLC Python signals: {len(tv_slim)}")
        if not cmp_df.empty:
            print(f"Same signal_time as F87104: {int(cmp_df['match'].sum())}/{len(cmp_df)}")
        if not tester_match.empty:
            print(f"TV tester OK (±2h vs entry_time_tv): {int((tester_match['tv_match']=='OK').sum())}/{len(tester_match)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
B06 VIS PRECALM — rerun on TradingView OANDA H4 CSV and compare to F87104 + TV tester.

Goal: TV execution parity. Python on TV OHLC is the verification baseline for Pine.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
TV_DIR = OUT
JPY4_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
TRIAL_SYMBOLS = ["XAUUSD", "CHFJPY", "SILVER"]
VIS_SYMBOLS = JPY4_SYMBOLS + TRIAL_SYMBOLS

sys.path.insert(0, str(ELLIOTT))

from run_h4_v_initial_shelf_deep_dive import (  # noqa: E402
    CURRENT_SPEC,
    prepare_data,
    run_spec,
)
from tv_oanda_h4_loader import default_tv_csv_path  # noqa: E402

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


def stats_row(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trades": 0, "win_rate": 0.0, "total_r": 0.0, "pf": float("nan")}
    r = df["r_after_cost"]
    wins = int((r > 0).sum())
    gp = float(r[r > 0].sum())
    gl = float(r[r <= 0].sum())
    pf = gp / abs(gl) if gl < 0 else (float("inf") if gp > 0 else float("nan"))
    return {
        "trades": len(df),
        "win_rate": round(100 * wins / len(df), 1),
        "total_r": round(float(r.sum()), 2),
        "pf": round(pf, 2) if pf != float("inf") else float("inf"),
    }


def symbols_with_tv_csv(symbols: list[str]) -> list[str]:
    return [s for s in symbols if default_tv_csv_path(s, TV_DIR).exists()]


def append_symbol_table(lines: list[str], all_tv: pd.DataFrame, symbols: list[str]) -> None:
    lines.extend(
        [
            "| 銘柄 | 件数 | 勝率 | 合計R | PF |",
            "|------|------|------|-------|-----|",
        ]
    )
    for sym in symbols:
        sub = all_tv[all_tv["symbol"] == sym] if not all_tv.empty else pd.DataFrame()
        s = stats_row(sub)
        lines.append(f"| {sym} | {s['trades']} | {s['win_rate']}% | {s['total_r']}R | {s['pf']} |")


def write_summary(
    all_tv: pd.DataFrame,
    symbols: list[str],
    confirmed_path: Path,
    *,
    jpy4_symbols: list[str],
    trial_symbols: list[str],
) -> None:
    jpy4_tv = all_tv[all_tv["symbol"].isin(jpy4_symbols)] if not all_tv.empty else pd.DataFrame()
    trial_tv = all_tv[all_tv["symbol"].isin(trial_symbols)] if not all_tv.empty else pd.DataFrame()
    total = stats_row(all_tv)
    jpy4_total = stats_row(jpy4_tv)
    trial_total = stats_row(trial_tv)
    lines = [
        "# B06 — TV OANDA H4 再検証サマリ",
        "",
        "再現: `python3 scripts/run_b06_tv_oanda_parity.py`",
        "",
        "## データ源",
        "",
        "- OHLC: `docs/research/system_b_pine_parity_2026-06-01/tv_{symbol}_h4.csv`（TradingView OANDA 4Hエクスポート）",
        "- SILVER は `tv_xagusd_h4.csv` を使用",
        "- CHFJPY は `tv_chfjpy_h4.csv` 未エクスポート時はスキップ",
        "- ロジック: `CURRENT_PRECALM_SHELF6_RR15`（`run_h4_v_initial_shelf_deep_dive.py`）",
        "- Pine: `pine/research/h4_v_initial_shelf_breakout_strategy.pine`",
        "",
        "## 件数・成績（TV-OHLC Python）",
        "",
        f"| 区分 | 件数 | 勝率 | 合計R | PF |",
        f"|------|------|------|-------|-----|",
        f"| **JPY4 本番** | **{jpy4_total['trades']}** | **{jpy4_total['win_rate']}%** | **{jpy4_total['total_r']}R** | **{jpy4_total['pf']}** |",
        f"| **試験3銘柄** | **{trial_total['trades']}** | **{trial_total['win_rate']}%** | **{trial_total['total_r']}R** | **{trial_total['pf']}** |",
        f"| 合計 | **{total['trades']}** | **{total['win_rate']}%** | **{total['total_r']}R** | **{total['pf']}** |",
        "",
        "### JPY4 銘柄別",
        "",
    ]
    append_symbol_table(lines, all_tv, jpy4_symbols)
    if trial_symbols:
        lines.extend(["", "### 試験3銘柄別（Pine照合前・0.25R試行）", ""])
        append_symbol_table(lines, all_tv, trial_symbols)
    lines.extend(
        [
            "",
            "## 執行の正",
            "",
            "- JPY4: `python_expected_b06_tv_oanda_{symbol}.csv`（GBPJPYは `*_pine_authoritative.csv`）",
            "- 試験: `python_expected_b06_tv_oanda_{symbol}.csv`（TVラベル照合後に執行正化）",
            "- 合算: `python_expected_b06_tv_oanda_all.csv` / 試験のみ `python_expected_b06_tv_oanda_trial_all.csv`",
            "",
            "## Pine照合チェック",
            "",
            "各 `signal_time_tv` でチャートに **棚B** ラベルがあるか確認。試験3銘柄は `symbolMode=試験3銘柄` で載せる。",
            "",
            "| # | symbol | signal_time_tv | entry | stop | target |",
            "|---|--------|----------------|-------|------|--------|",
        ]
    )
    if not all_tv.empty:
        for i, (_, r) in enumerate(all_tv.sort_values(["symbol", "signal_time"]).iterrows(), 1):
            lines.append(
                f"| {i} | {r['symbol']} | {r['signal_time_tv']} | {r['entry']:.3f} | {r['stop']:.3f} | {r['target']:.3f} |"
            )
    if confirmed_path.exists() and not jpy4_tv.empty:
        old = pd.read_csv(confirmed_path, parse_dates=["signal_time"])
        keys_old = {
            f"{row.symbol}|{pd.Timestamp(row.signal_time).strftime('%Y-%m-%d %H:%M:%S')}"
            for _, row in old.iterrows()
        }
        keys_new = {
            f"{row.symbol}|{pd.Timestamp(row.signal_time).strftime('%Y-%m-%d %H:%M:%S')}"
            for _, row in jpy4_tv.iterrows()
        }
        match = keys_old == keys_new
        lines.extend(
            [
                "",
                "## 前回照合ログとの一致（JPY4のみ）",
                "",
                f"- `parity_log_b06_tv_oanda_confirmed.csv` と signal_time キー一致: **{'OK' if match else 'DIFF'}**",
            ]
        )
    (OUT / "B06_TV_RERUN_SUMMARY_ja.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="B06 TV OANDA parity rerun")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--jpy4-only", action="store_true", help="JPY4 本番4通貨のみ")
    g.add_argument("--trial-only", action="store_true", help="試験3銘柄のみ (XAU/CHFJPY/SILVER)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.jpy4_only:
        target_symbols = JPY4_SYMBOLS
    elif args.trial_only:
        target_symbols = TRIAL_SYMBOLS
    else:
        target_symbols = VIS_SYMBOLS

    symbols_with_csv = symbols_with_tv_csv(target_symbols)
    missing = [s for s in target_symbols if s not in symbols_with_csv]
    if missing:
        print(f"Missing TV CSV (skipped): {missing}")
    if not symbols_with_csv:
        print(f"No tv_*_h4.csv under {TV_DIR} for {target_symbols}")
        sys.exit(1)

    print(f"TV OANDA CSV symbols: {symbols_with_csv}")
    data, pivots = prepare_data(data_source="tv_oanda", tv_csv_dir=TV_DIR, symbols=symbols_with_csv)
    tv_trades = run_spec(data, pivots, CURRENT_SPEC, symbols_with_csv)
    all_parts: list[pd.DataFrame] = []

    for symbol in symbols_with_csv:
        sub = tv_trades[tv_trades["symbol"] == symbol] if not tv_trades.empty else pd.DataFrame()
        tv_slim = slim_trades(sub, "tv_oanda")
        tv_slim.to_csv(OUT / f"python_expected_b06_tv_oanda_{symbol.lower()}.csv", index=False)
        if not tv_slim.empty:
            all_parts.append(tv_slim)

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

    all_tv = pd.concat(all_parts, ignore_index=True) if all_parts else pd.DataFrame()
    if not all_tv.empty:
        all_tv = all_tv.sort_values(["symbol", "signal_time"]).reset_index(drop=True)
        all_tv.to_csv(OUT / "python_expected_b06_tv_oanda_all.csv", index=False)
        trial_tv = all_tv[all_tv["symbol"].isin(TRIAL_SYMBOLS)]
        if not trial_tv.empty:
            trial_tv.to_csv(OUT / "python_expected_b06_tv_oanda_trial_all.csv", index=False)
    confirmed = OUT / "parity_log_b06_tv_oanda_confirmed.csv"
    jpy4_run = [s for s in symbols_with_csv if s in JPY4_SYMBOLS]
    trial_run = [s for s in symbols_with_csv if s in TRIAL_SYMBOLS]
    write_summary(
        all_tv,
        symbols_with_csv,
        confirmed,
        jpy4_symbols=jpy4_run or JPY4_SYMBOLS,
        trial_symbols=trial_run,
    )
    print(f"\n=== ALL ===")
    print(f"Total TV-OHLC Python signals: {len(all_tv)}")
    if not all_tv.empty:
        s = stats_row(all_tv)
        print(f"Win {s['win_rate']}% / Total {s['total_r']}R / PF {s['pf']}")
    print(f"Summary: {OUT / 'B06_TV_RERUN_SUMMARY_ja.md'}")


if __name__ == "__main__":
    main()

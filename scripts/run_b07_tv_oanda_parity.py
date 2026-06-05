#!/usr/bin/env python3
"""
B07 DTS (D1 Trap -> H4 Shelf) — rerun on TradingView OANDA H4 CSV vs F87104 export.

D1 trap contexts remain from F87104 trap study; H4 OHLC + pivots use TV CSV.
Execution truth for Pine: TV-OHLC Python on exported OANDA H4 files.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
TV_DIR = OUT
DTS_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
DTS_STRATEGY = "selected_CURRENT_A30_180_SIGADX30"
LANE_ID = "B07_DTS_TRAP_SHELF"

sys.path.insert(0, str(ELLIOTT))

from run_d1_trap_h4_shelf_integrated_study import (  # noqa: E402
    IntegratedSpec,
    load_d1_low_trap_contexts,
    run_integrated,
)
from run_h4_v_initial_shelf_deep_dive import CURRENT_SPEC, prepare_data  # noqa: E402

EXPORT_ALL = OUT / "python_expected_b07_dts_all.csv"
TV_DISPLAY_OFFSET_HOURS = 9

B07_SPEC = IntegratedSpec(
    DTS_STRATEGY,
    replace(CURRENT_SPEC, name="BASE", target_basis="entry", entry_mode="next_open"),
    30,
    180,
    universe="selected",
    signal_adx_max=30.0,
)


def to_tv_display(ts: pd.Series) -> pd.Series:
    return pd.to_datetime(ts) + pd.Timedelta(hours=TV_DISPLAY_OFFSET_HOURS)


def signal_key(symbol: str, signal_time: pd.Timestamp) -> str:
    return f"{symbol}|{pd.Timestamp(signal_time).strftime('%Y-%m-%d %H:%M:%S')}"


def slim_trades(df: pd.DataFrame, data_source: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["lane_id"] = LANE_ID
    out["data_source"] = data_source
    out["strategy"] = DTS_STRATEGY
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"]) if "exit_time" in out.columns else pd.NaT
    if "d1_low_trap_signal_time" in out.columns:
        out["d1_low_trap_signal_time"] = pd.to_datetime(out["d1_low_trap_signal_time"])
    out["signal_time_tv"] = to_tv_display(out["signal_time"])
    out["entry_time_tv"] = to_tv_display(out["entry_time"])
    out["exit_time_tv"] = to_tv_display(out["exit_time"])
    cols = [
        "lane_id",
        "symbol",
        "period",
        "strategy",
        "data_source",
        "d1_low_trap_source",
        "d1_low_trap_signal_time",
        "d1_low_trap_age_days",
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
        "param_target_basis",
        "pair_key",
        "v_low_time",
        "v_start_time",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols].sort_values(["symbol", "signal_time"]).reset_index(drop=True)


def compare_export_entry(f87104: pd.DataFrame, tv_oanda: pd.DataFrame, tol_hours: float = 4.0) -> pd.DataFrame:
    """Map legacy F87104 export rows to nearest TV-OHLC B07 by entry_time."""
    rows = []
    for _, ex in f87104.iterrows():
        sub = tv_oanda[tv_oanda["symbol"] == ex["symbol"]].copy()
        if sub.empty:
            rows.append(
                {
                    "export_signal_time": ex["signal_time"],
                    "export_entry_time": ex["entry_time"],
                    "symbol": ex["symbol"],
                    "tv_signal_time": pd.NaT,
                    "tv_entry_time": pd.NaT,
                    "entry_hour_gap": float("nan"),
                    "entry_match": False,
                }
            )
            continue
        sub["gap"] = (sub["entry_time"] - ex["entry_time"]).abs()
        best = sub.loc[sub["gap"].idxmin()]
        gap_h = best["gap"].total_seconds() / 3600
        rows.append(
            {
                "export_signal_time": ex["signal_time"],
                "export_entry_time": ex["entry_time"],
                "symbol": ex["symbol"],
                "tv_signal_time": best["signal_time"],
                "tv_entry_time": best["entry_time"],
                "entry_hour_gap": round(gap_h, 2),
                "entry_match": gap_h <= tol_hours,
            }
        )
    return pd.DataFrame(rows)


def compare_expected(f87104: pd.DataFrame, tv_oanda: pd.DataFrame) -> pd.DataFrame:
    rows = []
    f_keys = {signal_key(r.symbol, r.signal_time): r for _, r in f87104.iterrows()}
    t_keys = {signal_key(r.symbol, r.signal_time): r for _, r in tv_oanda.iterrows()}
    for k in sorted(set(f_keys) | set(t_keys)):
        in_f = k in f_keys
        in_t = k in t_keys
        row = {
            "key": k,
            "in_f87104_export": in_f,
            "in_tv_oanda_py": in_t,
            "match": in_f and in_t,
        }
        if in_f and in_t:
            fr, tr = f_keys[k], t_keys[k]
            row["entry_diff_pips"] = round((float(fr.entry) - float(tr.entry)) / 0.01, 2)
            row["stop_diff_pips"] = round((float(fr.stop) - float(tr.stop)) / 0.01, 2)
            row["target_diff_pips"] = round((float(fr.target) - float(tr.target)) / 0.01, 2)
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
        f"# B07 {symbol} — TV OANDA データでの Python 再実行",
        "",
        "## 目的",
        "",
        "B07 DTS: D1 Trap 文脈（F87104）+ **H4 は TV OANDA CSV** で再実行。Pine 照合の正は TV-OHLC Python。",
        "",
        "## Pine 必須",
        "",
        "- ファイル: `pine/research/d1_trap_h4_shelf_strict_strategy.pine`",
        f"- strategy: `{DTS_STRATEGY}`",
        "- tp_basis: Entry基準",
        "- trap_age: 30–180, signal_adx_max: 30",
        "",
        "## 件数",
        "",
        f"| 系列 | 件数 |",
        f"|------|------|",
        f"| F87104 export（従来） | **{n_f}** |",
        f"| TV OANDA H4 CSV（今回） | **{n_t}** |",
        f"| 同一 signal_time | **{n_match}** |",
        f"| TVテスターと±2h（entry_time_tv） | **{ok}/{n_t}** |",
        "",
        "## B06 との重複",
        "",
        "同一 `signal_time` の B06/B07 は **9件**（`overlap_b06_b07_signal_times.csv`）。",
        "本番・TV では **B06 優先**（portfolio_slots overlap_resolution）。",
        "",
    ]
    only_f = cmp_df[~cmp_df["in_tv_oanda_py"] & cmp_df["in_f87104_export"]] if not cmp_df.empty else pd.DataFrame()
    only_t = cmp_df[~cmp_df["in_f87104_export"] & cmp_df["in_tv_oanda_py"]] if not cmp_df.empty else pd.DataFrame()
    if not only_f.empty:
        lines.append("**F87104 export のみ:**")
        for k in only_f["key"]:
            lines.append(f"- {k}")
        lines.append("")
    if not only_t.empty:
        lines.append("**TV-OHLC Python のみ:**")
        for k in only_t["key"]:
            lines.append(f"- {k}")
        lines.append("")
    lines.extend(
        [
            "## 次の作業（Pine）",
            "",
            "1. `python_expected_b07_tv_oanda_<symbol>.csv` の `signal_time_tv` にラベル",
            "2. tp_basis=Entry基準、strategy 名を上記と一致",
            "3. B06 と同日のシグナルは B06 が先 — B07 ラベルは重複日を確認",
            "4. テスターは `entry_time_tv` と照合",
            "",
            "## ファイル",
            "",
            f"- `python_expected_b07_tv_oanda_{symbol.lower()}.csv`",
            f"- `b07_f87104_vs_tv_oanda_{symbol.lower()}.csv`",
            f"- `b07_tv_oanda_vs_tester_{symbol.lower()}.csv`（テスターCSVがある場合）",
            "",
            "再現: `python3 scripts/run_b07_tv_oanda_parity.py`",
        ]
    )
    (OUT / f"B07_TV_OANDA_RERUN_{symbol}.md").write_text("\n".join(lines), encoding="utf-8")


PINE_PRESET = {
    "file": "pine/research/d1_trap_h4_shelf_strict_strategy.pine",
    "chart": "H4",
    "strategy": DTS_STRATEGY,
    "tp_basis": "Entry基準",
    "trap_age_min": 30,
    "trap_age_max": 180,
    "signal_adx_max": 30,
}


def write_smoke(symbol: str, df: pd.DataFrame) -> None:
    sub = df[df["symbol"] == symbol].sort_values("signal_time")
    lines = [
        f"# B07 DTS — {symbol} TVスモーク（TV-OHLC Python）",
        "",
        f"件数: **{len(sub)}**",
        "",
        "## Pine 必須設定",
        "",
    ]
    for k, v in PINE_PRESET.items():
        if k != "file":
            lines.append(f"- **{k}:** `{v}`")
    lines.append(f"- **Pineファイル:** `{PINE_PRESET['file']}`")
    lines.extend(
        [
            "",
            "## 照合",
            "",
            "1. `signal_time_tv` / `entry_time_tv` を TV 表示（JST）と照合",
            "2. B06 と同日シグナルは **B06 優先**（`overlap_b06_b07_tv_signal_times.csv`）",
            "3. 旧 F87104 `python_expected_b07_dts_all.csv`（9件）は **signal_time 不一致** — 使わない",
            "",
            "| signal_time_tv | entry_time_tv | entry | stop | target | r |",
            "|----------------|---------------|-------|------|--------|---|",
        ]
    )
    for _, row in sub.iterrows():
        lines.append(
            f"| {row['signal_time_tv']} | {row['entry_time_tv']} | {row['entry']} | "
            f"{row['stop']} | {row['target']} | {row['r_after_cost']} |"
        )
    if len(sub) >= 1:
        first = sub.iloc[0]
        lines.extend(
            [
                "",
                "## TZ確認（1件目）",
                "",
                f"- signal_time (index): `{first['signal_time']}`",
                f"- signal_time_tv: `{first['signal_time_tv']}`",
            ]
        )
    (OUT / f"{symbol.lower()}_b07_tv_oanda_smoke.md").write_text("\n".join(lines), encoding="utf-8")


def write_overlap_tv(b06_tv: pd.DataFrame, b07_tv: pd.DataFrame) -> None:
    def keyed(df: pd.DataFrame) -> dict[str, pd.Series]:
        out: dict[str, pd.Series] = {}
        for _, r in df.iterrows():
            k = f"{r.symbol}|{pd.Timestamp(r.signal_time).strftime('%Y-%m-%d %H:%M:%S')}"
            out[k] = r
        return out

    b07_by_key = keyed(b07_tv)
    rows = []
    for k in sorted(keyed(b06_tv).keys() & b07_by_key.keys()):
        r = b07_by_key[k]
        rows.append(
            {
                "symbol": r["symbol"],
                "signal_time": r["signal_time"],
                "signal_time_tv": r["signal_time_tv"],
                "entry_time_tv": r["entry_time_tv"],
                "note": "B06優先（overlap_resolution）",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "overlap_b06_b07_tv_signal_times.csv", index=False)


def write_summary(
    all_tv: pd.DataFrame,
    cmp_all: pd.DataFrame,
    entry_map: pd.DataFrame,
    b06_tv: pd.DataFrame,
) -> None:
    n = len(all_tv)
    n_match = int(cmp_all["match"].sum()) if not cmp_all.empty else 0
    n_entry = int(entry_map["entry_match"].sum()) if not entry_map.empty else 0
    n_overlap = len(pd.read_csv(OUT / "overlap_b06_b07_tv_signal_times.csv")) if (OUT / "overlap_b06_b07_tv_signal_times.csv").exists() else 0
    by_sym = all_tv.groupby("symbol").size() if not all_tv.empty else pd.Series(dtype=int)
    lines = [
        "# B07 DTS — TV OANDA parity サマリ",
        "",
        "更新: 2026-05-31",
        "",
        "## 結論（現時点）",
        "",
        "**執行の正 = TV OANDA H4 CSV 上の Python（12件）**。Pine 照合はこれに対して行う。",
        "",
        f"- TV-OHLC Python: **{n}** 件",
        f"- 旧 F87104 export: 9 件（`signal_time` 一致 **{n_match}/9** — 参照用のみ）",
        f"- export `entry_time` ±4h で TV に寄る: **{n_entry}/9**",
        f"- B06 TV と同一 `signal_time`: **{n_overlap}** 件（本番は B06 優先）",
        "",
        "## 銘柄別（TV-OHLC）",
        "",
    ]
    for sym, cnt in by_sym.items():
        lines.append(f"- {sym}: {cnt}")
    lines.extend(
        [
            "",
            "## 使わないもの",
            "",
            "- `python_expected_b07_dts_all.csv`（F87104 H1→H4、9件）",
            "",
            "## 使うもの",
            "",
            "- `python_expected_b07_tv_oanda_all.csv` および `_*_{symbol}.csv`",
            "- `*_tv` 列 = TV チャート/テスター表示（UTC+9）",
            "- Pine: `d1_trap_h4_shelf_strict_strategy.pine`",
            "",
            "## 次",
            "",
            "1. 銘柄ごと Pine で 12 件のラベル照合",
            "2. **B07 専用**ストラテジーテスター CSV をエクスポートして `tv_strategy_trades_b07_{symbol}.csv` に保存",
            "3. `parity_log_b07_tv_oanda.csv` に OK/MISS を記録",
            "",
            "再現: `python3 scripts/run_b07_tv_oanda_parity.py`",
        ]
    )
    (OUT / "DECISION_b07_tv_oanda_parity.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    symbols_with_csv = [s for s in DTS_SYMBOLS if (TV_DIR / f"tv_{s.lower()}_h4.csv").exists()]
    if not symbols_with_csv:
        print(f"No tv_*_h4.csv under {TV_DIR}")
        sys.exit(1)

    print(f"TV OANDA CSV symbols: {symbols_with_csv}")
    data, pivots = prepare_data(data_source="tv_oanda", tv_csv_dir=TV_DIR, symbols=symbols_with_csv)
    contexts = load_d1_low_trap_contexts()
    tv_trades = run_integrated(data, pivots, contexts, B07_SPEC)
    tv_trades = tv_trades[tv_trades["strategy"] == DTS_STRATEGY] if not tv_trades.empty else tv_trades

    all_tv_slim = slim_trades(tv_trades, "tv_oanda")
    all_tv_slim.to_csv(OUT / "python_expected_b07_tv_oanda_all.csv", index=False)

    export_all = pd.DataFrame()
    if EXPORT_ALL.exists():
        export_all = pd.read_csv(EXPORT_ALL, parse_dates=["signal_time", "entry_time"])
        export_all = export_all[export_all["strategy"].eq(DTS_STRATEGY)]

    cmp_frames = []
    for symbol in symbols_with_csv:
        sub = tv_trades[tv_trades["symbol"] == symbol] if not tv_trades.empty else pd.DataFrame()
        tv_slim = slim_trades(sub, "tv_oanda")
        tv_slim.to_csv(OUT / f"python_expected_b07_tv_oanda_{symbol.lower()}.csv", index=False)

        f87104 = pd.DataFrame()
        f_path = OUT / f"by_symbol/b07_{symbol.lower()}.csv"
        if f_path.exists():
            f87104 = pd.read_csv(f_path, parse_dates=["signal_time", "entry_time"])
        elif not export_all.empty:
            f87104 = export_all[export_all["symbol"] == symbol].copy()

        cmp_df = compare_expected(f87104, tv_slim)
        cmp_df.to_csv(OUT / f"b07_f87104_vs_tv_oanda_{symbol.lower()}.csv", index=False)
        cmp_frames.append(cmp_df)

        tester_match = pd.DataFrame()
        tester_b07 = OUT / f"tv_strategy_trades_b07_{symbol.lower()}.csv"
        if tester_b07.exists():
            tester = pd.read_csv(tester_b07)
            tester_match = match_tv_tester(tv_slim, tester)
            tester_match.to_csv(OUT / f"b07_tv_oanda_vs_tester_{symbol.lower()}.csv", index=False)

        write_smoke(symbol, all_tv_slim)
        write_report(symbol, f87104, tv_slim, cmp_df, tester_match)
        print(f"\n=== {symbol} ===")
        print(f"TV-OHLC Python signals: {len(tv_slim)}")
        if not cmp_df.empty:
            print(f"Same signal_time as F87104 export: {int(cmp_df['match'].sum())}/{len(f87104)}")
        if not tester_match.empty:
            print(
                f"B07 tester OK (±2h vs entry_time_tv): "
                f"{int((tester_match['tv_match']=='OK').sum())}/{len(tester_match)}"
            )
        else:
            print("B07 tester CSV: not yet (export tv_strategy_trades_b07_*.csv from TV)")

    cmp_all = compare_expected(export_all, all_tv_slim) if not export_all.empty else pd.DataFrame()
    if not cmp_all.empty:
        cmp_all.to_csv(OUT / "b07_f87104_vs_tv_oanda_all.csv", index=False)
    entry_map = compare_export_entry(export_all, all_tv_slim) if not export_all.empty else pd.DataFrame()
    if not entry_map.empty:
        entry_map.to_csv(OUT / "b07_export_entry_vs_tv_oanda.csv", index=False)

    b06_frames = []
    for s in symbols_with_csv:
        p = OUT / f"python_expected_b06_tv_oanda_{s.lower()}.csv"
        if p.exists():
            b06_frames.append(pd.read_csv(p, parse_dates=["signal_time", "entry_time"]))
    b06_tv = pd.concat(b06_frames, ignore_index=True) if b06_frames else pd.DataFrame()
    if not b06_tv.empty and not all_tv_slim.empty:
        write_overlap_tv(b06_tv, all_tv_slim)

    parity_tpl = all_tv_slim.copy()
    parity_tpl["tv_match"] = "pending"
    parity_tpl["tv_notes"] = ""
    parity_tpl.to_csv(OUT / "parity_log_b07_tv_oanda_template.csv", index=False)

    write_summary(all_tv_slim, cmp_all, entry_map, b06_tv)

    print(f"\n=== TOTAL ===")
    print(f"TV-OHLC Python: {len(all_tv_slim)} (export expected: {len(export_all)})")
    if not cmp_all.empty:
        print(f"Matched export keys: {int(cmp_all['match'].sum())}/{len(export_all)}")


if __name__ == "__main__":
    main()

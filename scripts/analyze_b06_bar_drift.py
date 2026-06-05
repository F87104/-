#!/usr/bin/env python3
"""
Quantify Python (F87104 H1→H4) vs TradingView strategy-tester drift for B06 USDJPY.

Without TV-exported OHLC, compares:
- time offset (H4 bars) between TV entry and Python signal/entry
- entry price vs Python bar open/close at aligned timestamps
- optional: full OHLC diff if tv_usdjpy_h4.csv is provided

TV export format (optional): datetime,open,high,low,close  (UTC or JST — set TZ_OFFSET_HOURS)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
sys.path.insert(0, str(ROOT / "backtest"))
sys.path.insert(0, str(ELLIOTT))

from sai_backtest import load_instrument  # noqa: E402
from run_elliott_fibo_study import resample_ohlc  # noqa: E402

PY_TRADES = OUT / "by_symbol/b06_usdjpy.csv"
TV_TRADES = OUT / "tv_strategy_trades_usdjpy.csv"
TV_OHLC_OPTIONAL = OUT / "tv_usdjpy_h4.csv"  # user can add later

# TradingView UI was UTC+9 in screenshots; tester times may be chart/exchange time
TZ_SCENARIOS = {
    "as_utc": 0,
    "tv_ui_jst_to_utc": -9,  # subtract 9h from displayed JST to get UTC
}


def load_python_h4() -> pd.DataFrame:
    raw = load_instrument("USDJPY")
    return resample_ohlc(raw, "H4")


def bar_at(df: pd.DataFrame, ts: pd.Timestamp) -> tuple[pd.Timestamp, pd.Series, str]:
    if ts in df.index:
        return ts, df.loc[ts], "exact"
    idx = df.index.get_indexer([ts], method="nearest")[0]
    nt = df.index[idx]
    return nt, df.iloc[idx], f"nearest_{int((nt - ts).total_seconds() / 3600)}h"


def pip_diff(a: float, b: float) -> float:
    """USDJPY: 1 pip ≈ 0.01 yen."""
    return round((a - b) / 0.01, 1)


def analyze_tv_vs_python(py_h4: pd.DataFrame, py_tr: pd.DataFrame, tv_tr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, tv in tv_tr.iterrows():
        tv_entry = pd.Timestamp(tv["entry_time"])
        tv_price = float(tv["entry_price"])
        best_py = None
        best_days = 9999.0
        for _, py in py_tr.iterrows():
            py_sig = pd.Timestamp(py["signal_time"])
            py_ent = pd.Timestamp(py["entry_time"])
            d_sig = abs((tv_entry - py_sig).total_seconds()) / 86400
            d_ent = abs((tv_entry - py_ent).total_seconds()) / 86400
            d = min(d_sig, d_ent)
            if d < best_days:
                best_days = d
                best_py = py
        row = {
            "tv_trade_no": tv.get("trade_no", ""),
            "tv_entry_time": tv_entry,
            "tv_entry_price": tv_price,
            "nearest_py_trade_id": best_py["trade_id"] if best_py is not None else "",
            "nearest_py_signal_time": best_py["signal_time"] if best_py is not None else "",
            "nearest_py_entry_time": best_py["entry_time"] if best_py is not None else "",
            "nearest_py_entry_price": best_py["entry"] if best_py is not None else np.nan,
            "day_gap_to_py_signal": round(best_days, 2) if best_py is not None else np.nan,
        }
        for label, offset_h in TZ_SCENARIOS.items():
            adj = tv_entry + pd.Timedelta(hours=offset_h)
            bar_ts, bar, how = bar_at(py_h4, adj)
            row[f"{label}_bar_time"] = bar_ts
            row[f"{label}_bar_match"] = how
            row[f"{label}_open"] = bar["open"]
            row[f"{label}_close"] = bar["close"]
            row[f"{label}_entry_vs_open_pips"] = pip_diff(tv_price, float(bar["open"]))
            row[f"{label}_entry_vs_close_pips"] = pip_diff(tv_price, float(bar["close"]))
            if best_py is not None:
                row[f"{label}_entry_vs_py_entry_pips"] = pip_diff(tv_price, float(best_py["entry"]))
                py_ent = pd.Timestamp(best_py["entry_time"])
                row[f"{label}_h4_bars_tv_to_py_entry"] = int(
                    round((adj - py_ent).total_seconds() / (4 * 3600))
                )
        rows.append(row)
    return pd.DataFrame(rows)


def analyze_py_signals(py_h4: pd.DataFrame, py_tr: pd.DataFrame, tv_tr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, py in py_tr.iterrows():
        sig = pd.Timestamp(py["signal_time"])
        ent = pd.Timestamp(py["entry_time"])
        _, sig_bar, _ = bar_at(py_h4, sig)
        _, ent_bar, _ = bar_at(py_h4, ent)
        tv_match = tv_tr.copy()
        tv_match["dist"] = (pd.to_datetime(tv_match["entry_time"]) - sig).abs()
        nearest_tv = tv_match.sort_values("dist").iloc[0] if not tv_match.empty else None
        rows.append(
            {
                "trade_id": py["trade_id"],
                "signal_time": sig,
                "entry_time": ent,
                "py_entry": py["entry"],
                "signal_close": py["signal_close"],
                "signal_bar_o": sig_bar["open"],
                "signal_bar_h": sig_bar["high"],
                "signal_bar_l": sig_bar["low"],
                "signal_bar_c": sig_bar["close"],
                "entry_bar_open": ent_bar["open"],
                "entry_bar_close": ent_bar["close"],
                "entry_vs_signal_close_pips": pip_diff(float(py["entry"]), float(py["signal_close"])),
                "nearest_tv_entry_time": nearest_tv["entry_time"] if nearest_tv is not None else "",
                "nearest_tv_entry_price": nearest_tv["entry_price"] if nearest_tv is not None else np.nan,
                "tv_day_gap": round(nearest_tv["dist"].total_seconds() / 86400, 2) if nearest_tv is not None else np.nan,
                "tv_h4_bars_gap": int(round(nearest_tv["dist"].total_seconds() / (4 * 3600)))
                if nearest_tv is not None
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _parse_tv_timestamps(series: pd.Series) -> pd.DatetimeIndex:
    raw = series.dropna()
    if raw.empty:
        return pd.DatetimeIndex([])
    if pd.api.types.is_numeric_dtype(raw):
        v = float(raw.iloc[len(raw) // 2])
        unit = "ms" if v > 1e12 else "s"
        # TV UNIX = UTC epoch; keep naive for index join with Python H4
        return pd.DatetimeIndex(pd.to_datetime(raw.astype("int64"), unit=unit))
    parsed = pd.to_datetime(raw, utc=False, errors="coerce")
    if getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_localize(None)
    return pd.DatetimeIndex(parsed)


def _load_tv_ohlc_csv(path: Path) -> pd.DataFrame:
    tv = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in tv.columns}
    time_col = None
    for key in ("datetime", "time", "date", "timestamp"):
        if key in cols:
            time_col = cols[key]
            break
    if time_col is None and len(tv.columns) >= 5:
        # TradingView UNIX export sometimes labels the first column oddly
        first = tv.columns[0]
        if pd.api.types.is_numeric_dtype(tv[first]) or str(first).lower() in ("unix", "unixtime"):
            time_col = first
    if time_col is None:
        raise ValueError(f"{path.name}: need datetime/time/date column; got {list(tv.columns)}")
    rename = {time_col: "datetime"}
    for ohlc in ("open", "high", "low", "close"):
        if ohlc in cols:
            rename[cols[ohlc]] = ohlc
    tv = tv.rename(columns=rename)
    missing = [c for c in ("datetime", "open", "high", "low", "close") if c not in tv.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    out = tv[["datetime", "open", "high", "low", "close"]].copy()
    out.index = _parse_tv_timestamps(out["datetime"])
    out = out.loc[out.index.notna()].drop(columns=["datetime"])
    return out.sort_index()


def _ohlc_diff_summary(py_h4: pd.DataFrame, tv: pd.DataFrame, shift_h: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    if shift_h:
        tv = tv.copy()
        tv.index = tv.index + pd.Timedelta(hours=shift_h)
    common = py_h4.index.intersection(tv.index)
    if len(common) == 0:
        return pd.DataFrame(), pd.DataFrame(), 0
    a = py_h4.loc[common]
    b = tv.loc[common]
    diff = pd.DataFrame(
        {
            "open_pips": (a["open"] - b["open"]) / 0.01,
            "high_pips": (a["high"] - b["high"]) / 0.01,
            "low_pips": (a["low"] - b["low"]) / 0.01,
            "close_pips": (a["close"] - b["close"]) / 0.01,
        }
    )
    summary = {
        "tv_index_shift_hours": shift_h,
        "matched_bars": len(common),
        "open_pips_mean": round(diff["open_pips"].mean(), 2),
        "open_pips_max_abs": round(diff["open_pips"].abs().max(), 2),
        "high_pips_max_abs": round(diff["high_pips"].abs().max(), 2),
        "low_pips_max_abs": round(diff["low_pips"].abs().max(), 2),
        "close_pips_mean": round(diff["close_pips"].mean(), 2),
        "close_pips_max_abs": round(diff["close_pips"].abs().max(), 2),
    }
    return diff, pd.DataFrame([summary]), len(common)


def compare_tv_ohlc_optional(py_h4: pd.DataFrame) -> pd.DataFrame | None:
    if not TV_OHLC_OPTIONAL.exists():
        return None
    tv_raw = _load_tv_ohlc_csv(TV_OHLC_OPTIONAL)
    best_shift = 0
    best_n = 0
    best_med = float("inf")
    best_diff = pd.DataFrame()
    best_summary = pd.DataFrame()
    for shift_h in range(-12, 13):
        diff, summary, n = _ohlc_diff_summary(py_h4, tv_raw, shift_h)
        if n < 500 or summary.empty:
            continue
        med = float(diff["close_pips"].abs().median()) if not diff.empty else float("inf")
        if med < best_med or (med == best_med and n > best_n):
            best_med, best_n, best_shift, best_diff, best_summary = med, n, shift_h, diff, summary
    if best_n == 0:
        print(
            f"WARN: {TV_OHLC_OPTIONAL.name} loaded ({len(tv_raw)} bars) but no index overlap with Python H4. "
            "Check date range and chart timezone; see TV_H4_EXPORT_GUIDE_ja.md"
        )
        return None
    best_diff.to_csv(OUT / "ohlc_diff_per_bar.csv")
    if not best_summary.empty:
        close_abs = best_diff["close_pips"].abs()
        best_summary["close_pips_median_abs"] = round(close_abs.median(), 2)
        best_summary["close_within_1pip_pct"] = round((close_abs <= 1.0).mean() * 100, 2)
        best_summary["alignment_note"] = (
            f"tv index shifted {best_shift:+d}h (min median |close| pip among shifts with n>=500)"
        )
    return best_summary


def write_report(tv_py: pd.DataFrame, py_sig: pd.DataFrame, ohlc_sum: pd.DataFrame | None) -> None:
    ok = py_sig[py_sig["tv_day_gap"] <= 1.0]
    miss = py_sig[py_sig["tv_day_gap"] > 3.0]
    lines = [
        "# B06 USDJPY — ローソク足・時刻ずれ解析",
        "",
        "Python: F87104_test H1 → H4 (`label=left, closed=left`).",
        "TV: ストラテジーテスター約定時刻・価格（OANDA表示チャート）。",
        "",
        "## 1. サマリー",
        "",
        f"- Pythonシグナル: **{len(py_sig)}** 件",
        f"- TVテスター: **{len(tv_py)}** 件",
        f"- Python signal と TV entry が **1日以内**: **{len(ok)}** 件",
        f"- **3日超ずれ**: **{len(miss)}** 件（データ/ピボット差の疑い）",
        "",
        "## 2. 価格ずれ（TV約定 vs Python約定）",
        "",
        "一致ペア（1日以内）の entry 差:",
        "",
    ]
    if not ok.empty:
        diffs = ok.apply(lambda r: pip_diff(float(r["nearest_tv_entry_price"]), float(r["py_entry"])), axis=1)
        lines.append(f"- 平均 **{diffs.mean():.1f} pip** / 最大 **{diffs.abs().max():.1f} pip**")
    lines.extend(
        [
            "",
            "## 3. 時間ずれ（H4本数）",
            "",
        ]
    )
    if not ok.empty:
        bars = ok["tv_h4_bars_gap"].dropna()
        lines.append(f"- 1日以内ペアの TV entry と Py entry の差: 平均 **{bars.mean():.1f}** 本 / 最大 **{bars.max():.0f}** 本")
    lines.extend(
        [
            "",
            "3日超ずれの Python シグナル（TVに無い）:",
            "",
        ]
    )
    for _, r in miss.iterrows():
        lines.append(f"- id **{r['trade_id']}** signal `{r['signal_time']}` nearest TV `{r['nearest_tv_entry_time']}` gap **{r['tv_day_gap']}** 日")
    lines.extend(
        [
            "",
            "## 4. TV約定 vs Python同一時刻の足",
            "",
            "`drift_tv_vs_python.csv` の `as_utc_entry_vs_open_pips` / `tv_ui_jst_to_utc_*` を参照。",
            "JST表示をUTCに直すと open との差が縮むペアあり → **時刻解釈が主因**のことが多い。",
            "",
            "## 5. TV OHLCを入れた場合",
            "",
        ]
    )
    if ohlc_sum is not None and not ohlc_sum.empty:
        r = ohlc_sum.iloc[0]
        shift = int(r.get("tv_index_shift_hours", 0))
        note = r.get("alignment_note", "")
        med = r.get("close_pips_median_abs", "")
        pct1 = r.get("close_within_1pip_pct", "")
        lines.append(
            f"一致インデックス **{int(r['matched_bars'])}** 本（TVシフト **{shift:+d}h**）: "
            f"close中央値ずれ **{med}** pip / 平均 **{r['close_pips_mean']}** pip / 最大 **{r['close_pips_max_abs']}** pip"
        )
        if pct1 != "":
            lines.append(f"- close が **1 pip 以内** のバー: **{pct1}%**（同一インデックス照合）")
        if note:
            lines.append(f"- {note}")
        lines.append(
            "- 中央値が数 pip 超なら **H4足の区切り（open時刻）が Python と TV で一致していない** 可能性が高い"
        )
    else:
        lines.append(
            f"`{TV_OHLC_OPTIONAL.name}` を置くとバー単位OHLC差分を出力。"
            "手順: `TV_H4_EXPORT_GUIDE_ja.md`"
        )
    lines.extend(
        [
            "",
            "## 6. CSV",
            "",
            "- `drift_tv_vs_python.csv` — TV各トレードの時刻・価格ずれ",
            "- `drift_python_signals.csv` — Python各シグナルと最寄TV",
            "- `ohlc_diff_per_bar.csv` — TV OHLCあり時のみ",
            "",
            "再現: `python3 scripts/analyze_b06_bar_drift.py`",
        ]
    )
    (OUT / "BAR_DRIFT_REPORT_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    py_h4 = load_python_h4()
    py_tr = pd.read_csv(PY_TRADES, parse_dates=["signal_time", "entry_time", "exit_time"])
    tv_tr = pd.read_csv(TV_TRADES, parse_dates=["entry_time", "exit_time"])

    tv_py = analyze_tv_vs_python(py_h4, py_tr, tv_tr)
    py_sig = analyze_py_signals(py_h4, py_tr, tv_tr)
    ohlc_sum = compare_tv_ohlc_optional(py_h4)

    tv_py.to_csv(OUT / "drift_tv_vs_python.csv", index=False)
    py_sig.to_csv(OUT / "drift_python_signals.csv", index=False)
    if ohlc_sum is not None:
        ohlc_sum.to_csv(OUT / "ohlc_diff_summary.csv", index=False)

    write_report(tv_py, py_sig, ohlc_sum)
    if not TV_OHLC_OPTIONAL.exists():
        print(
            f"\n[INFO] TV H4 not found. Export chart data → save as:\n  {TV_OHLC_OPTIONAL}\n"
            f"  Guide: {OUT / 'TV_H4_EXPORT_GUIDE_ja.md'}\n"
        )
    print((OUT / "BAR_DRIFT_REPORT_ja.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

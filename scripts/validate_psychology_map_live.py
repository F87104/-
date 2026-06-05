#!/usr/bin/env python3
"""
Offline validation for Psychology Map Live rules (F1/F2/break STOP).

Compares:
  - STOP signal rate and forward returns (did price move against chasers?)
  - Overlap with student all-loss stumble windows (reference only)

Usage:
  python3 scripts/validate_psychology_map_live.py
  python3 scripts/validate_psychology_map_live.py --symbol GBPJPY --year 2024

Output:
  docs/research/psychology_map_live_validation_report.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO / "F87104_test"
STUMBLE = REPO / "docs/research/student_stumble_clusters_v0_3.csv"
OUT = REPO / "docs/research/psychology_map_live_validation_report.md"

FORWARD_BARS = 24  # 1H ≈ 1 day


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


def find_h1(symbol: str, year: int) -> Path | None:
    token = "GBY" if symbol == "GBPJPY" else symbol[:3]
    for path in DATA_ROOT.rglob("*.csv"):
        if "H1" not in path.name.upper() or str(year) not in path.name:
            continue
        if token in path.name.replace(" ", "") or symbol in path.name:
            return path
    return None


def pip_size(symbol: str) -> float:
    return 0.1 if symbol == "XAUUSD" else 0.01


def add_indicators(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    d = df.copy()
    tr = pd.concat(
        [
            d["high"] - d["low"],
            (d["high"] - d["close"].shift()).abs(),
            (d["low"] - d["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    d["ema"] = d["close"].ewm(span=50, adjust=False).mean()
    d["body"] = (d["close"] - d["open"]).abs()
    d["body_ratio"] = d["body"] / (d["high"] - d["low"]).replace(0, np.nan)

    ps = pip_size(symbol)
    if symbol == "XAUUSD":
        n10 = (d["close"] / 10).round() * 10
        n50 = (d["close"] / 50).round() * 50
        d["near_round"] = (d["close"] - n10).abs() <= 12.0
        d["near_round"] |= (d["close"] - n50).abs() <= 12.0
    else:
        yen = d["close"].round()
        half = (d["close"] * 2).round() / 2
        d["near_round"] = (d["close"] - yen).abs() <= 0.25
        d["near_round"] |= (d["close"] - half).abs() <= 0.15

    d["key_high"] = d["high"].shift(1).rolling(48).max()
    d["key_low"] = d["low"].shift(1).rolling(48).min()
    d["hi_ext"] = d["high"].rolling(20).max()
    d["lo_ext"] = d["low"].rolling(20).min()
    d["near_high"] = d["hi_ext"] - d["close"] <= d["atr"] * 0.85
    d["near_low"] = d["close"] - d["lo_ext"] <= d["atr"] * 0.85

    big = d["body"] >= d["atr"] * 1.05
    d["big_bull"] = (d["close"] > d["open"]) & big
    d["big_bear"] = (d["close"] < d["open"]) & big
    d["impulse_bull"] = d["big_bull"].rolling(2).max().fillna(0).astype(bool)
    d["impulse_bear"] = d["big_bear"].rolling(2).max().fillna(0).astype(bool)

    buf = d["atr"] * 0.08
    d["break_up"] = (d["close"] > d["key_high"] + buf) & (d["close"].shift(1) <= d["key_high"].shift(1) + buf.shift(1))
    d["break_dn"] = (d["close"] < d["key_low"] - buf) & (d["close"].shift(1) >= d["key_low"].shift(1) - buf.shift(1))
    strong_up = (d["close"] > d["open"]) & (d["body_ratio"] >= 0.45)
    strong_dn = (d["close"] < d["open"]) & (d["body_ratio"] >= 0.45)

    if symbol == "XAUUSD":
        n10 = (d["close"] / 10).round() * 10
        n50 = (d["close"] / 50).round() * 50
        cross_up = (d["close"] > n10) & (d["close"].shift(1) <= n10.shift(1))
        cross_up |= (d["close"] > n50) & (d["close"].shift(1) <= n50.shift(1))
        cross_dn = (d["close"] < n10) & (d["close"].shift(1) >= n10.shift(1))
        cross_dn |= (d["close"] < n50) & (d["close"].shift(1) >= n50.shift(1))
    else:
        yen = d["close"].round()
        half = (d["close"] * 2).round() / 2
        cross_up = (d["close"] > yen) & (d["close"].shift(1) <= yen.shift(1))
        cross_up |= (d["close"] > half) & (d["close"].shift(1) <= half.shift(1))
        cross_dn = (d["close"] < yen) & (d["close"].shift(1) >= yen.shift(1))
        cross_dn |= (d["close"] < half) & (d["close"].shift(1) >= half.shift(1))
    d["f1_stop_long"] = d["near_high"] & (d["close"] > d["open"]) & cross_up.fillna(False)
    d["f1_stop_short"] = d["near_low"] & (d["close"] < d["open"]) & cross_dn.fillna(False)
    d["impulse_bull_prev"] = d["impulse_bull"].shift(1).fillna(False)
    d["impulse_bear_prev"] = d["impulse_bear"].shift(1).fillna(False)
    d["f2_stop_long"] = d["impulse_bull"] & ~d["impulse_bull_prev"] & (d["close"] > d["open"])
    d["f2_stop_short"] = d["impulse_bear"] & ~d["impulse_bear_prev"] & (d["close"] < d["open"])
    d["brk_stop_long"] = d["break_up"] & strong_up
    d["brk_stop_short"] = d["break_dn"] & strong_dn

    d["stop_long"] = d["f1_stop_long"] | d["f2_stop_long"] | d["brk_stop_long"]
    d["stop_short"] = d["f1_stop_short"] | d["f2_stop_short"] | d["brk_stop_short"]
    d["stop_any"] = d["stop_long"] | d["stop_short"]

    # forward return for chasers (long stop -> hope price falls)
    d["fwd_close"] = d["close"].shift(-FORWARD_BARS)
    d["fwd_ret"] = (d["fwd_close"] - d["close"]) / ps
    d["stop_long_ok"] = d["stop_long"] & (d["fwd_ret"] < 0)
    d["stop_short_ok"] = d["stop_short"] & (d["fwd_ret"] > 0)
    return d


def stumble_overlap(d: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if not STUMBLE.exists():
        return pd.DataFrame()
    st = pd.read_csv(STUMBLE)
    st = st[(st["currency"] == symbol) & (st["loss_rate"] >= 1.0)].copy()
    st["start"] = pd.to_datetime(st["start"])
    st["end"] = pd.to_datetime(st["end"])
    rows = []
    for _, r in st.iterrows():
        win = d[(d["time"] >= r["start"]) & (d["time"] <= r["end"])]
        if win.empty:
            rows.append({**r.to_dict(), "stop_hits": 0, "bars": 0})
            continue
        hits = int(win["stop_any"].sum())
        rows.append(
            {
                "currency": r["currency"],
                "students": r["students"],
                "start": r["start"],
                "end": r["end"],
                "price_low": r["price_low"],
                "price_high": r["price_high"],
                "stop_hits": hits,
                "bars": len(win),
            }
        )
    return pd.DataFrame(rows)


def validate_symbol(symbol: str, years: list[int]) -> dict:
    frames = []
    for y in years:
        p = find_h1(symbol, y)
        if p:
            frames.append(parse_mt_h1(p))
    if not frames:
        return {"symbol": symbol, "error": "no OHLC"}
    d = add_indicators(pd.concat(frames, ignore_index=True).drop_duplicates("time"), symbol)
    d = d.dropna(subset=["atr", "fwd_close"])

    n_stop = int(d["stop_any"].sum())
    n_long = int(d["stop_long"].sum())
    n_short = int(d["stop_short"].sum())
    ok_long = d.loc[d["stop_long"], "stop_long_ok"].mean() if n_long else np.nan
    ok_short = d.loc[d["stop_short"], "stop_short_ok"].mean() if n_short else np.nan
    ok_any = pd.concat(
        [
            d.loc[d["stop_long"], "stop_long_ok"],
            d.loc[d["stop_short"], "stop_short_ok"],
        ]
    ).mean() if n_stop else np.nan

    overlap = stumble_overlap(d, symbol)
    hit_clusters = 0
    if not overlap.empty:
        hit_clusters = int((overlap["stop_hits"] > 0).sum())

    return {
        "symbol": symbol,
        "bars": len(d),
        "stop_any": n_stop,
        "stop_long": n_long,
        "stop_short": n_short,
        "fwd_ok_rate": ok_any,
        "fwd_ok_long": ok_long,
        "fwd_ok_short": ok_short,
        "clusters": len(overlap),
        "clusters_with_stop": hit_clusters,
        "overlap": overlap,
    }


def write_report(results: list[dict]) -> None:
    lines = [
        "# Psychology Map Live — オフライン検証レポート",
        "",
        f"Forward評価: STOP 後 **{FORWARD_BARS}本**（1H）の逆行率",
        "受講生クラスタは **参考一致率** のみ（未来判定には未使用）",
        "",
    ]
    for r in results:
        if r.get("error"):
            lines += [f"## {r['symbol']}", "", f"- エラー: {r['error']}", ""]
            continue
        lines += [
            f"## {r['symbol']}",
            "",
            f"| 指標 | 値 |",
            f"|------|-----|",
            f"| H1バー数 | {r['bars']} |",
            f"| STOP シグナル | {r['stop_any']} |",
            f"| 内訳 買抑制/売抑制 | {r['stop_long']} / {r['stop_short']} |",
            f"| {FORWARD_BARS}本後に逆行（買STOP） | {r['fwd_ok_long']:.1%} |" if r["stop_long"] else "| 買STOP | - |",
            f"| {FORWARD_BARS}本後に逆行（売STOP） | {r['fwd_ok_short']:.1%} |" if r["stop_short"] else "| 売STOP | - |",
            f"| 逆行率 合計 | {r['fwd_ok_rate']:.1%} |" if r["stop_any"] else "| 合計 | - |",
            f"| 受講生全敗帯（参考） | {r['clusters_with_stop']}/{r['clusters']} 件でSTOP≥1 |",
            "",
        ]
        ov = r.get("overlap")
        if ov is not None and not ov.empty:
            lines += ["### 受講生全敗帯との重なり", "", "| start | end | students | STOP本数 |", "|---|---|---:|---:|"]
            for _, row in ov.iterrows():
                lines.append(
                    f"| {row['start']} | {row['end']} | {int(row['students'])} | {int(row['stop_hits'])} |"
                )
            lines.append("")

    lines += [
        "## TradingView 検証",
        "",
        "1. `pine/research/psychology_map_live_validation_v0_1.pine` を 1H に貼る",
        "2. モード **比較** → `フィルタON` OFF でバックテスト → ON で再実行",
        "3. 右上テーブル: Trades / PF / STOP累計 / ブロック",
        "4. 受講生参考帯（灰破線）と STOP=S が近いか目視",
        "",
        "## 運用",
        "",
        "- 目視: `pine/visual/psychology_map_live.pine` v1.0.1",
        "- 抑制ロジック試験: 本 Strategy",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", action="append", default=["GBPJPY", "XAUUSD", "USDJPY"])
    ap.add_argument("--year", type=int, nargs="+", default=[2024, 2025])
    args = ap.parse_args()

    results = [validate_symbol(s, args.year) for s in args.symbol]
    write_report(results)
    print(f"Wrote {OUT}")
    for r in results:
        if r.get("error"):
            print(f"  {r['symbol']}: {r['error']}")
        else:
            print(
                f"  {r['symbol']}: STOP={r['stop_any']} "
                f"fwd_ok={r['fwd_ok_rate']:.1%} "
                f"cluster_hit={r['clusters_with_stop']}/{r['clusters']}"
            )


if __name__ == "__main__":
    main()

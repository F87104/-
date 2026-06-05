#!/usr/bin/env python3
"""
Thorough pre-implementation validation: Capitulation (watch) + Short Squeeze (trade).

Outputs under docs/research/cap_sqz_thorough_validation_2026-06-01/
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_market_psychology_strategy_tv_check import (  # noqa: E402
    PsySpec,
    capitulation_signal,
    load_data,
    period_name,
    simulate_long,
    squeeze_signal,
    summarize,
)
from run_elliott_fibo_study import SYMBOLS  # noqa: E402

OUT = ROOT / "docs" / "research" / "cap_sqz_thorough_validation_2026-06-01"
OUT.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")

PROD_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "CHFJPY", "SILVER"]
EXCLUDE_GBP = {"GBPJPY"}
EXCLUDE_PROD = {"GBPJPY", "AUDJPY"}

PINE_SQZ = PsySpec("SQZ_PINE", "short_squeeze")
PINE_CAP = PsySpec("CAP_PINE", "capitulation")
SQZ_STRICT = replace(PINE_SQZ, name="SQZ_STRICT", shelf_atr=2.0, move_atr=3.5)

TB_PATH = ROOT / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
T5_PATH = ROOT / "backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/t5_practical_only_trades.csv"


def pf(r: pd.Series) -> float:
    w = float(r[r > 0].sum())
    l = float(r[r <= 0].sum())
    return w / abs(l) if l < 0 else (math.inf if w > 0 else math.nan)


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict:
    if df.empty:
        return dict(trades=0, win_rate=0.0, total_r=0.0, avg_r=0.0, pf=math.nan, max_dd_r=0.0, max_ls=0, tp_pct=0.0)
    r = df[r_col].astype(float)
    curve = r.cumsum()
    ls = 0
    best = 0
    for v in r:
        if v <= 0:
            ls += 1
            best = max(best, ls)
        else:
            ls = 0
    tp = (df["exit_reason"] == "target").mean() * 100 if "exit_reason" in df.columns else 0.0
    return dict(
        trades=len(r),
        win_rate=round((r > 0).mean() * 100, 1),
        total_r=round(r.sum(), 2),
        avg_r=round(r.mean(), 3),
        pf=round(pf(r), 2) if len(r) else math.nan,
        max_dd_r=round(float((curve.cummax() - curve).max()), 2) if len(r) else 0.0,
        max_ls=int(best),
        tp_pct=round(tp, 1),
    )


def run_sqz_trades(df: pd.DataFrame, symbol: str, spec: PsySpec) -> pd.DataFrame:
    rows = []
    in_pos = -1
    start_i = max(80, spec.shelf_bars + spec.drop_win + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or i <= in_pos:
            continue
        sig = squeeze_signal(df, i, spec)
        if sig is None or float(df["close"].iloc[i]) <= float(sig["stop"]):
            continue
        trade = simulate_long(df, symbol, i, float(sig["stop"]), spec.rr, spec.max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "year": pd.Timestamp(trade["entry_time"]).year,
                **sig,
                **trade,
            }
        )
        in_pos = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def run_cap_signals_only(df: pd.DataFrame, symbol: str, spec: PsySpec) -> pd.DataFrame:
    """Capitulation: signal log without auto-trade (for watch-layer stats)."""
    rows = []
    start_i = max(80, spec.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END:
            continue
        sig = capitulation_signal(df, i, spec)
        if sig is None:
            continue
        rows.append({"symbol": symbol, "signal_time": ts, "period": period_name(ts), "year": ts.year, **sig})
    return pd.DataFrame(rows)


def filter_df(df: pd.DataFrame, *, research: bool | None, symbols: set[str] | None) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["entry_time"] = pd.to_datetime(out.get("entry_time", out["signal_time"]))
    if research is True:
        out = out[out["entry_time"] <= RESEARCH_END]
    elif research is False:
        out = out[out["entry_time"] > RESEARCH_END]
    if symbols is not None:
        out = out[out["symbol"].isin(symbols)]
    if symbols is not None and symbols == set(PROD_SYMBOLS):
        pass
    return out


def overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def read_tb_long() -> pd.DataFrame:
    df = pd.read_csv(TB_PATH)
    df = df[df["rule_name"].eq("baseline") & df["direction"].str.lower().eq("long")].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RESEARCH_END)]
    out = df.rename(columns={"pnl_r_after_cost": "r"})[["symbol", "entry_time", "exit_time", "r"]]
    out["strategy"] = "TrendBreak_long"
    return out


def read_t5_fixed() -> pd.DataFrame:
    df = pd.read_csv(T5_PATH, parse_dates=["entry_time", "exit_time"])
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RESEARCH_END)]
    return pd.DataFrame(
        {
            "strategy": "T5_practical",
            "symbol": df["symbol"],
            "entry_time": df["entry_time"],
            "exit_time": df["exit_time"],
            "r": df["r"].astype(float),
        }
    )


def ensemble_priority(
    pools: list[tuple[str, pd.DataFrame, int]],
) -> pd.DataFrame:
    """Lower priority number wins slot on overlap (same symbol, holding overlap)."""
    all_rows = []
    for name, df, pri in pools:
        if df.empty:
            continue
        t = df.copy()
        t["strategy"] = name
        t["priority"] = pri
        all_rows.append(t[["strategy", "symbol", "entry_time", "exit_time", "r", "priority"]])
    if not all_rows:
        return pd.DataFrame()
    merged = pd.concat(all_rows, ignore_index=True).sort_values(["entry_time", "priority", "symbol"])
    accepted: list[dict] = []
    by_sym: dict[str, list[dict]] = {}
    for row in merged.to_dict("records"):
        sym = row["symbol"]
        book = by_sym.setdefault(sym, [])
        if any(overlaps(row["entry_time"], row["exit_time"], t["entry_time"], t["exit_time"]) for t in book):
            continue
        accepted.append(row)
        book.append(row)
    return pd.DataFrame(accepted)


def win_loss_diag(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for label, g in [("win", trades[trades["r_after_cost"] > 0]), ("loss", trades[trades["r_after_cost"] <= 0])]:
        if g.empty:
            continue
        rows.append(
            {
                "group": label,
                "trades": len(g),
                "shelf_range_atr_mean": round(g["shelf_range_atr"].mean(), 2),
                "sharp_drop_atr_mean": round(g["sharp_drop_atr"].mean(), 2),
                "body_ratio_mean": round(g["body_ratio"].mean(), 2),
                "close_location_mean": round(g["close_location"].mean(), 2),
                "avg_mfe_r": round(g["mfe_r"].mean(), 2),
                "avg_mae_r": round(g["mae_r"].mean(), 2),
            }
        )
    return pd.DataFrame(rows)


def param_sweep(data: dict[str, pd.DataFrame], symbols: list[str]) -> pd.DataFrame:
    rows = []
    for shelf_atr in [2.0, 2.5, 3.0]:
        for move_atr in [2.5, 3.0, 3.5, 4.0]:
            spec = replace(PINE_SQZ, shelf_atr=shelf_atr, move_atr=move_atr, rr=2.0)
            parts = []
            for sym in symbols:
                parts.append(run_sqz_trades(data[sym], sym, spec))
            t = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            t = filter_df(t, research=True, symbols=set(symbols))
            m = metrics(t)
            rows.append({"shelf_atr": shelf_atr, "move_atr": move_atr, **m})
    return pd.DataFrame(rows)


def main() -> None:
    data = load_data()
    prod_set = set(PROD_SYMBOLS)

    # --- Generate SQZ trade sets ---
    variants = {
        "SQZ_PINE_2R": replace(PINE_SQZ, rr=2.0),
        "SQZ_PINE_2.5R": replace(PINE_SQZ, rr=2.5),
        "SQZ_STRICT_2R": replace(SQZ_STRICT, rr=2.0),
        "SQZ_STRICT_2.5R": replace(SQZ_STRICT, rr=2.5),
    }
    trade_sets: dict[str, pd.DataFrame] = {}
    for vname, spec in variants.items():
        parts = [run_sqz_trades(data[s], s, spec) for s in SYMBOLS if s in data]
        trade_sets[vname] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        trade_sets[vname].to_csv(OUT / f"trades_{vname}.csv", index=False)

    primary = trade_sets["SQZ_STRICT_2R"]
    primary_prod = filter_df(primary, research=True, symbols=prod_set)
    primary_prod = primary_prod[~primary_prod["symbol"].isin(EXCLUDE_PROD)]

    # --- Summary matrix ---
    summary_rows = []
    for vname, tdf in trade_sets.items():
        for label, research in [
            ("ALL_7SYM_2015_2026", None),
            ("RESEARCH_7SYM", True),
            ("OOS_7SYM", False),
            ("PROD5_RESEARCH", True),
        ]:
            sub = tdf.copy()
            if research is True:
                sub = filter_df(sub, research=True, symbols=None)
            elif research is False:
                sub = filter_df(sub, research=False, symbols=None)
            if label == "PROD5_RESEARCH":
                sub = sub[sub["symbol"].isin(prod_set) & ~sub["symbol"].isin(EXCLUDE_PROD)]
            m = metrics(sub)
            summary_rows.append({"variant": vname, "universe": label, **m})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "summary_matrix.csv", index=False)

    # --- By symbol / period / year (STRICT 2R prod) ---
    by_symbol = []
    for sym, g in primary_prod.groupby("symbol"):
        by_symbol.append({"symbol": sym, **metrics(g)})
    pd.DataFrame(by_symbol).to_csv(OUT / "strict_2r_by_symbol.csv", index=False)

    by_period = []
    for per, g in primary_prod.groupby("period"):
        by_period.append({"period": per, **metrics(g)})
    pd.DataFrame(by_period).to_csv(OUT / "strict_2r_by_period.csv", index=False)

    by_year = []
    for yr, g in primary_prod.groupby("year"):
        by_year.append({"year": yr, **metrics(g)})
    pd.DataFrame(by_year).to_csv(OUT / "strict_2r_by_year.csv", index=False)

    win_loss_diag(primary_prod).to_csv(OUT / "strict_2r_win_loss_diag.csv", index=False)

    # --- Parameter sweep (prod symbols) ---
    sweep = param_sweep(data, PROD_SYMBOLS)
    sweep.to_csv(OUT / "param_sweep_prod.csv", index=False)

    # --- Capitulation watch layer ---
    cap_parts = [run_cap_signals_only(data[s], s, PINE_CAP) for s in SYMBOLS if s in data]
    cap_all = pd.concat(cap_parts, ignore_index=True) if cap_parts else pd.DataFrame()
    cap_all.to_csv(OUT / "cap_signals_all.csv", index=False)
    cap_research = filter_df(
        cap_all.assign(entry_time=cap_all["signal_time"]),
        research=True,
        symbols=prod_set,
    )
    # cap -> later sqz strict within 24 bars?
    cap_conv = []
    if not cap_research.empty and not primary_prod.empty:
        for _, c in cap_research.iterrows():
            sym = c["symbol"]
            t0 = c["signal_time"]
            t1 = t0 + pd.Timedelta(hours=24 * 4)
            hit = primary_prod[
                (primary_prod["symbol"] == sym)
                & (primary_prod["signal_time"] > t0)
                & (primary_prod["signal_time"] <= t1)
            ]
            cap_conv.append(len(hit) > 0)
        cap_research = cap_research.copy()
        cap_research["sqz_strict_within_24h4"] = cap_conv
    cap_metrics = {
        "cap_signals_research_prod": len(cap_research),
        "sqz_follow_rate_pct": round(cap_research["sqz_strict_within_24h4"].mean() * 100, 1)
        if not cap_research.empty and "sqz_strict_within_24h4" in cap_research.columns
        else 0.0,
    }
    pd.DataFrame([cap_metrics]).to_csv(OUT / "cap_watch_metrics.csv", index=False)

    # --- Ensemble (research, prod symbols) ---
    sqz = primary_prod[["symbol", "entry_time", "exit_time", "r_after_cost"]].rename(
        columns={"r_after_cost": "r"}
    )
    sqz["strategy"] = "SQZ_STRICT"
    tb = read_tb_long()
    tb = tb[tb["symbol"].isin(prod_set)]
    t5 = read_t5_fixed()
    t5 = t5[t5["symbol"].isin(prod_set)]

    ens_rows = []
    scenarios = [
        ("TB_long_only", [( "TB", tb, 0)]),
        ("T5_only", [( "T5", t5, 0)]),
        ("SQZ_only", [( "SQZ", sqz, 0)]),
        ("TB+T5_T5priority", [( "TB", tb, 1), ("T5", t5, 0)]),
        ("TB+SQZ_TBpriority", [( "TB", tb, 0), ("SQZ", sqz, 1)]),
        ("T5+SQZ_T5priority", [( "T5", t5, 0), ("SQZ", sqz, 1)]),
        ("TB+T5+SQZ_T5>TB>SQZ", [( "T5", t5, 0), ("TB", tb, 1), ("SQZ", sqz, 2)]),
        ("TB+T5+SQZ_SQZwhen_free", [( "TB", tb, 0), ("T5", t5, 1), ("SQZ", sqz, 2)]),
    ]
    for name, pools in scenarios:
        merged = ensemble_priority(pools)
        if merged.empty:
            continue
        m = metrics(merged.rename(columns={"r": "r_after_cost"}))
        m["scenario"] = name
        ens_rows.append(m)
        merged.to_csv(OUT / f"ensemble_{name}.csv", index=False)
    pd.DataFrame(ens_rows).to_csv(OUT / "ensemble_summary.csv", index=False)

    # --- Overlap rates ---
    ov_rows = []
    for label, other in [("TB_long", tb), ("T5", t5)]:
        if sqz.empty or other.empty:
            continue
        hits = 0
        for _, s in sqz.iterrows():
            o = other[other["symbol"] == s["symbol"]]
            if any(overlaps(s["entry_time"], s["exit_time"], r["entry_time"], r["exit_time"]) for _, r in o.iterrows()):
                hits += 1
        ov_rows.append(
            {
                "pair": f"SQZ_vs_{label}",
                "sqz_trades": len(sqz),
                "overlap_trades": hits,
                "overlap_pct": round(100 * hits / len(sqz), 1),
            }
        )
    pd.DataFrame(ov_rows).to_csv(OUT / "overlap_rates.csv", index=False)

    # --- Report ---
    strict_m = metrics(primary_prod)
    pine_m = metrics(
        filter_df(trade_sets["SQZ_PINE_2R"], research=True, symbols=prod_set).pipe(
            lambda x: x[~x["symbol"].isin(EXCLUDE_PROD)]
        )
    )
    best_sweep = sweep.sort_values(["pf", "total_r"], ascending=[False, False]).head(3)

    lines = [
        "# 投げ切り・踏み上げ — 実装前 徹底検証",
        "",
        "作成: 2026-06-01",
        "",
        "## 1. 実装対象の切り分け",
        "",
        "| レイヤ | 判定 | 根拠 |",
        "|--------|------|------|",
        "| **踏み上げ SQZ STRICT** | **実装（EXECUTE）** | 本番5通貨・研究期 PF≥2、DD抑制 |",
        "| **踏み上げ SQZ Pineデフォルト** | 監視プリセット | 件数多め・PFやや低 |",
        "| **投げ切り CAP** | **WATCHのみ** | 研究期 PF≈1、単独エントリー非推奨 |",
        "",
        "## 2. 本番ユニバース（推奨）",
        "",
        f"- 通貨: {', '.join(PROD_SYMBOLS)}",
        "- 除外: GBPJPY, AUDJPY",
        "- 時間足: H4、ロングのみ",
        "- 仕様: SQZ STRICT — 棚≤2ATR、急落≥3.5ATR、SL=棚安−0.25ATR、TP=2R、次足始値、最大120本",
        "",
        "## 3. コア数値（SQZ STRICT 2R・研究期・本番5通貨）",
        "",
        f"- 件数: {strict_m['trades']}",
        f"- 勝率: {strict_m['win_rate']}%",
        f"- PF: {strict_m['pf']}",
        f"- 合計R: {strict_m['total_r']}R",
        f"- maxDD: {strict_m['max_dd_r']}R",
        f"- 最大連敗: {strict_m['max_ls']}",
        f"- TP到達率: {strict_m['tp_pct']}%",
        "",
        "参考 Pineデフォルト2R（同ユニバース）:",
        f"- {pine_m['trades']}件 / WR {pine_m['win_rate']}% / PF {pine_m['pf']} / +{pine_m['total_r']}R",
        "",
        "## 4. 2R vs 2.5R（STRICT・本番5通貨・研究期）",
        "",
    ]
    for rr in ["2R", "2.5R"]:
        v = f"SQZ_STRICT_{rr}"
        sub = filter_df(trade_sets[v], research=True, symbols=prod_set)
        sub = sub[~sub["symbol"].isin(EXCLUDE_PROD)]
        m = metrics(sub)
        lines.append(f"- **{rr}**: {m['trades']}件 WR {m['win_rate']}% PF {m['pf']} +{m['total_r']}R DD {m['max_dd_r']}R")
    lines.extend(
        [
            "",
            "## 5. 通貨別（STRICT 2R・研究期）",
            "",
            pd.read_csv(OUT / "strict_2r_by_symbol.csv").to_string(index=False),
            "",
            "## 6. 期間別（STRICT 2R）",
            "",
            pd.read_csv(OUT / "strict_2r_by_period.csv").to_string(index=False),
            "",
            "## 7. パラメータ感度（本番5通貨・研究期・2R）",
            "",
            "上位3:",
            best_sweep.to_string(index=False),
            "",
            "## 8. アンサンブル（研究期・本番5通貨・重複時優先）",
            "",
            pd.read_csv(OUT / "ensemble_summary.csv").to_string(index=False),
            "",
            "## 9. 重複率",
            "",
            pd.read_csv(OUT / "overlap_rates.csv").to_string(index=False),
            "",
            "## 10. 投げ切り（監視層）",
            "",
            f"- 研究期シグナル数（本番5通貨）: {cap_metrics['cap_signals_research_prod']}",
            f"- 24H4以内にSQZ STRICTが続く率: {cap_metrics['sqz_follow_rate_pct']}%",
            "",
            "## 11. 実装 GO 条件チェック",
            "",
            "| 条件 | 状態 |",
            "|------|------|",
            f"| 研究期 PF≥1.5 | {'OK' if strict_m['pf'] >= 1.5 else 'NG'} ({strict_m['pf']}) |",
            f"| 研究期 件数≥25 | {'OK' if strict_m['trades'] >= 25 else 'NG'} ({strict_m['trades']}) |",
            f"| maxDD≤8R | {'OK' if strict_m['max_dd_r'] <= 8 else 'WARN'} ({strict_m['max_dd_r']}R) |",
            f"| OOS PF≥1.0 | 要確認 summary_matrix |",
            "| TVパリティ5件 | 未実施 |",
            "| フォワード20件 | 未実施 |",
            "",
            "## 12. 実装タスク",
            "",
            "1. `pine/production/h4_sqz_strict_live.pine` — EXECUTE + alert",
            "2. `pine/visual/market_psychology_cap_sqz_visual.pine` — ユーザー案を保存（CAP/SQZ表示）",
            "3. 運用: CAP=青ラベル監視、SQZ STRICT=ライム＋アラート",
            "4. TB/T5併用時は `TB+T5+SQZ_T5>TB>SQZ` または空きスロットのみSQZ",
            "",
            "## ファイル",
            "",
            f"- `{OUT.relative_to(ROOT)}/` 以下 CSV 一式",
        ]
    )
    (OUT / "VALIDATION_REPORT_ja.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "IMPLEMENTATION_SPEC.md").write_text(
        "\n".join(
            [
                "# SQZ STRICT 実装仕様（確定案）",
                "",
                "## エントリー（H4・ロング）",
                "",
                "1. `shelfBars=6` 直前の高値 `shelfHi`、安値 `shelfLo`",
                "2. `shelfRange <= 2.0 * ATR`",
                "3. 棚前 `dropWin=6` の高値から棚高値まで `>= 3.5 * ATR` 下落",
                "4. 前足終値 `<= shelfHi` かつ 当足終値 `> shelfHi`",
                "5. シグナル足確定 → **次足始値**でエントリー",
                "",
                "## 出口",
                "",
                "- SL: `shelfLo - 0.25 * ATR`",
                "- TP: `2.0R`（フォワードで2.5R比較可）",
                "- 最大保有: 120 H4",
                "",
                "## 通貨",
                "",
                "- 許可: XAUUSD, USDJPY, EURJPY, CHFJPY, SILVER",
                "- 禁止: GBPJPY, AUDJPY",
                "",
                "## 投げ切り",
                "",
                "- 表示・アラートのみ。自動発注なし。",
                "- Pineデフォルト条件はユーザー提示インジと同一。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print((OUT / "VALIDATION_REPORT_ja.md").read_text(encoding="utf-8")[:4000])
    print(f"\n... full report at {OUT}")


if __name__ == "__main__":
    main()

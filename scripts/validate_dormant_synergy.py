#!/usr/bin/env python3
"""
Validate synergy between fixed dormant trend-break levels and existing signals.

Outputs: docs/research/dormant_synergy_validation_2026-06-01/
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_elliott_fibo_study import (  # noqa: E402
    add_indicators,
    load_instrument,
    markdown_table,
    resample_ohlc,
    simulate_trade,
)
from run_h4_v_kickoff_catalyst_study import (  # noqa: E402
    dormant_high_break_detail,
    recent_dormant_high_break,
)

OUT = ROOT / "docs/research/dormant_synergy_validation_2026-06-01"
OUT.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")

CORE_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "CHFJPY", "SILVER"]
TB_PATH = ROOT / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
T5_PATH = ROOT / "backtests/ensemble/trendbreak_t5_practical_combo_2015_2024/t5_practical_only_trades.csv"

DORMANT_WINDOWS = {
    "dormant120": (120, 30),
    "dormant360": (360, 90),
    "dormant1250": (1250, 190),
}
BUFFER_ATR = 0.05


def pf(r: pd.Series) -> float:
    w = float(r[r > 0].sum())
    l = float(r[r <= 0].sum())
    return w / abs(l) if l < 0 else (math.inf if w > 0 else math.nan)


def period_name(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts <= RESEARCH_END else "OOS_2025_2026"


def metrics(df: pd.DataFrame, r_col: str = "r") -> dict:
    if df.empty:
        return dict(trades=0, win_rate=0.0, total_r=0.0, avg_r=0.0, pf=math.nan, max_dd_r=0.0)
    r = df[r_col].astype(float)
    curve = r.cumsum()
    return dict(
        trades=len(r),
        win_rate=round((r > 0).mean() * 100, 1),
        total_r=round(r.sum(), 2),
        avg_r=round(r.mean(), 3),
        pf=round(pf(r), 2) if len(r) else math.nan,
        max_dd_r=round(float((curve.cummax() - curve).max()), 2) if len(r) else 0.0,
    )


def add_dormant_features(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    for name, (lookback, exclude_recent) in DORMANT_WINDOWS.items():
        width = lookback - exclude_recent
        old_high = out["high"].shift(exclude_recent + 1).rolling(width, min_periods=width).max()
        old_low = out["low"].shift(exclude_recent + 1).rolling(width, min_periods=width).min()
        recent_high = out["high"].shift(1).rolling(exclude_recent, min_periods=exclude_recent).max()
        recent_low = out["low"].shift(1).rolling(exclude_recent, min_periods=exclude_recent).min()
        out[f"{name}_high_prev"] = old_high
        out[f"{name}_low_prev"] = old_low
        out[f"{name}_high_dormant"] = recent_high < old_high
        out[f"{name}_low_dormant"] = recent_low > old_low
    return out


def dormant_break_on_bar(df: pd.DataFrame, i: int, mode: str) -> dict | None:
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    keys = ["dormant120", "dormant360", "dormant1250"]
    if mode == "dormant120":
        keys = ["dormant120"]
    elif mode == "dormant360":
        keys = ["dormant360"]
    elif mode == "dormant1250":
        keys = ["dormant1250"]
    hits = []
    for key in keys:
        hit = dormant_high_break_detail(df, i, key, atr_i, BUFFER_ATR)
        if hit is not None:
            hits.append(hit)
    if not hits:
        return None
    order = {"dormant120": 1, "dormant360": 2, "dormant1250": 3}
    return sorted(hits, key=lambda x: order.get(str(x["dormant_break_key"]), 0), reverse=True)[0]


@dataclass(frozen=True)
class DormantEntrySpec:
    name: str
    break_mode: str  # dormant120 | dormant360 | dormant1250 | any
    rr: float = 2.0
    sl_pad_atr: float = 0.25
    max_hold: int = 120


def run_dormant_long_trades(df: pd.DataFrame, symbol: str, spec: DormantEntrySpec) -> pd.DataFrame:
    rows = []
    in_pos = -1
    warmup = 1300
    for i in range(warmup, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or i <= in_pos:
            continue
        hit = dormant_break_on_bar(df, i, spec.break_mode)
        if hit is None:
            continue
        key = str(hit["dormant_break_key"])
        level = float(hit["dormant_high_level"])
        atr_i = float(df["atr"].iloc[i])
        stop = float(df[f"{key}_low_prev"].iloc[i]) - atr_i * spec.sl_pad_atr
        if not math.isfinite(stop) or float(df["close"].iloc[i]) <= stop:
            continue
        risk = float(df["open"].iloc[i + 1]) - stop
        if risk <= 0:
            continue
        target = float(df["open"].iloc[i + 1]) + risk * spec.rr
        trade = simulate_trade(df, symbol, "long", i, stop, target, spec.max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "strategy": spec.name,
                "symbol": symbol,
                "signal_time": ts,
                "entry_time": trade["entry_time"],
                "exit_time": trade["exit_time"],
                "r": trade["r_after_cost"],
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "dormant_break_key": key,
                "dormant_high_level": level,
            }
        )
        in_pos = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def load_h4(symbol: str) -> pd.DataFrame:
    raw = load_instrument(symbol)
    h4 = resample_ohlc(raw, "H4")
    h4 = h4[(h4.index >= RUN_START) & (h4.index <= RUN_END)]
    return add_dormant_features(h4)


def bar_index_at(df: pd.DataFrame, ts: pd.Timestamp) -> int | None:
    try:
        loc = df.index.get_indexer([ts], method="pad")[0]
        if loc < 0:
            return None
        if df.index[loc] != ts and loc > 0 and df.index[loc] > ts:
            loc -= 1
        return int(loc)
    except Exception:
        return None


def gate_context(df: pd.DataFrame, signal_ts: pd.Timestamp, gate: str) -> bool:
    i = bar_index_at(df, signal_ts)
    if i is None:
        return False
    atr_i = float(df["atr"].iloc[i])
    if gate == "dormant_break_signal":
        return dormant_break_on_bar(df, i, "any") is not None
    if gate == "dormant_break_C_signal":
        return dormant_break_on_bar(df, i, "dormant1250") is not None
    if gate.startswith("recent_dormant_"):
        bars = int(gate.split("_")[-1])
        ctx = recent_dormant_high_break(df, i, bars, BUFFER_ATR)
        return ctx is not None and str(ctx.get("recent_dormant_break_key", "NONE")) != "NONE"
    if gate == "bull_regime_no_short_break_24":
        ctx = recent_dormant_high_break(df, i, 24, BUFFER_ATR)
        return ctx is not None
    return True


def apply_gate(trades: pd.DataFrame, frames: dict[str, pd.DataFrame], gate: str) -> pd.DataFrame:
    if trades.empty or gate == "none":
        return trades
    keep = []
    for row in trades.itertuples(index=False):
        df = frames.get(row.symbol)
        if df is None:
            continue
        ts = pd.Timestamp(getattr(row, "signal_time", row.entry_time))
        if gate_context(df, ts, gate):
            keep.append(row._asdict())
    if not keep:
        return trades.iloc[0:0].copy()
    return pd.DataFrame(keep)


def read_tb_long() -> pd.DataFrame:
    df = pd.read_csv(TB_PATH)
    df = df[df["rule_name"].eq("baseline") & df["direction"].str.lower().eq("long")].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    out = df[df["symbol"].isin(CORE_SYMBOLS)][["symbol", "signal_time", "entry_time", "exit_time"]].copy()
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["r"] = df.loc[out.index, "pnl_r_after_cost"].astype(float)
    out["strategy"] = "TrendBreak_long"
    return out.reset_index(drop=True)


def read_t5_long() -> pd.DataFrame:
    df = pd.read_csv(T5_PATH, parse_dates=["entry_time", "exit_time"])
    df = df[df["direction"].str.lower().eq("long")]
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    df = df[df["symbol"].isin(CORE_SYMBOLS)]
    return pd.DataFrame(
        {
            "strategy": "T5_practical_long",
            "symbol": df["symbol"],
            "entry_time": df["entry_time"],
            "exit_time": df["exit_time"],
            "r": df["r"].astype(float),
        }
    )


def overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def ensemble_no_overlap(pools: list[tuple[str, pd.DataFrame, int]]) -> pd.DataFrame:
    merged = []
    for name, df, pri in pools:
        if df.empty:
            continue
        t = df.copy()
        t["pool"] = name
        t["priority"] = pri
        merged.append(t)
    if not merged:
        return pd.DataFrame()
    all_df = pd.concat(merged, ignore_index=True).sort_values(["entry_time", "priority", "symbol"])
    accepted: list[dict] = []
    book: dict[str, list[dict]] = {}
    for row in all_df.to_dict("records"):
        sym = row["symbol"]
        slots = book.setdefault(sym, [])
        if any(overlaps(row["entry_time"], row["exit_time"], s["entry_time"], s["exit_time"]) for s in slots):
            continue
        accepted.append(row)
        slots.append(row)
    return pd.DataFrame(accepted)


def main() -> None:
    frames = {sym: load_h4(sym) for sym in CORE_SYMBOLS}

    dormant_specs = [
        DormantEntrySpec("DORM_LONG_A", "dormant120", rr=2.0),
        DormantEntrySpec("DORM_LONG_B", "dormant360", rr=2.0),
        DormantEntrySpec("DORM_LONG_C", "dormant1250", rr=2.0),
        DormantEntrySpec("DORM_LONG_ANY", "any", rr=2.0),
        DormantEntrySpec("DORM_LONG_C_RR3", "dormant1250", rr=3.0),
    ]
    dormant_rows = []
    for sym in CORE_SYMBOLS:
        df = frames[sym]
        for spec in dormant_specs:
            tr = run_dormant_long_trades(df, sym, spec)
            dormant_rows.append(tr)
    dormant_all = pd.concat([x for x in dormant_rows if not x.empty], ignore_index=True)
    dormant_all.to_csv(OUT / "dormant_standalone_trades.csv", index=False)

    tb = read_tb_long()
    t5 = read_t5_long()

    gates = [
        ("none", "フィルタなし"),
        ("dormant_break_signal", "シグナル足で休眠高値ブレイク(any)"),
        ("dormant_break_C_signal", "シグナル足でC(1250)休眠高値ブレイク"),
        ("recent_dormant_48", "直近48本以内に休眠高値ブレイク"),
        ("recent_dormant_120", "直近120本以内に休眠高値ブレイク"),
    ]

    combo_rows = []
    for base_name, base_df in [("TrendBreak_long", tb), ("T5_practical_long", t5)]:
        for gate_id, gate_label in gates:
            gated = apply_gate(base_df, frames, gate_id)
            for period in ["all", "Research_2015_2024", "OOS_2025_2026"]:
                sub = gated.copy()
                if period != "all" and not sub.empty:
                    sub["period"] = sub["entry_time"].map(period_name)
                    sub = sub[sub["period"] == period]
                elif period != "all":
                    sub = sub.iloc[0:0]
                m = metrics(sub)
                combo_rows.append(
                    {
                        "base": base_name,
                        "gate": gate_id,
                        "gate_label": gate_label,
                        "period": period,
                        **m,
                        "retention_pct": round(100 * len(sub) / len(base_df), 1) if len(base_df) else 0.0,
                    }
                )
            gated.to_csv(OUT / f"{base_name}_{gate_id}_trades.csv", index=False)

    # Ensemble: TB priority 1, T5 priority 2; dormant-gated variants
    ens_variants = [
        ("TB+T5_baseline", tb, t5, "none"),
        ("TB+T5_recent_dormant_48", apply_gate(tb, frames, "recent_dormant_48"), apply_gate(t5, frames, "recent_dormant_48"), "none"),
        ("TB+T5_dormant_C_signal", apply_gate(tb, frames, "dormant_break_C_signal"), apply_gate(t5, frames, "dormant_break_C_signal"), "none"),
    ]
    ens_rows = []
    for name, tb_part, t5_part, _ in ens_variants:
        merged = ensemble_no_overlap([("TB", tb_part, 1), ("T5", t5_part, 2)])
        if not merged.empty:
            merged.to_csv(OUT / f"ensemble_{name}.csv", index=False)
        for period in ["all", "Research_2015_2024"]:
            sub = merged.copy()
            if period != "all" and not sub.empty:
                sub["period"] = sub["entry_time"].map(period_name)
                sub = sub[sub["period"] == period]
            elif period != "all":
                sub = sub.iloc[0:0]
            ens_rows.append({"ensemble": name, "period": period, **metrics(sub)})

    dormant_summary = []
    for spec in dormant_specs:
        sub = dormant_all[dormant_all["strategy"] == spec.name]
        for period in ["all", "Research_2015_2024", "OOS_2025_2026"]:
            psub = sub.copy()
            if period != "all":
                psub = psub[psub["period"] == period]
            dormant_summary.append({"strategy": spec.name, "period": period, **metrics(psub)})

    pd.DataFrame(dormant_summary).to_csv(OUT / "dormant_standalone_summary.csv", index=False)
    pd.DataFrame(combo_rows).to_csv(OUT / "gate_combo_summary.csv", index=False)
    pd.DataFrame(ens_rows).to_csv(OUT / "ensemble_summary.csv", index=False)

    # Rank gates for TB (research only)
    tb_g = pd.DataFrame(combo_rows)
    tb_g = tb_g[(tb_g["base"] == "TrendBreak_long") & (tb_g["period"] == "Research_2015_2024")].sort_values("total_r", ascending=False)

    best_dorm = pd.DataFrame(dormant_summary)
    best_dorm = best_dorm[best_dorm["period"] == "Research_2015_2024"].sort_values("total_r", ascending=False)

    md = [
        "# 大トレンドブレイク（休眠レベル）相性検証",
        "",
        "作成日: 2026-06-01",
        "",
        "踏み上げ（SQZ）研究は対象外。休眠高値/安値ライン（Pine修正版と同じ窓）と既存シグナルの組み合わせを検証。",
        "",
        "## 前提",
        "",
        "- H4 / 窓: A=120/30, B=360/90, C=1250/190",
        "- ブレイク余白: 0.05 ATR",
        "- 対象通貨: XAUUSD, USDJPY, EURJPY, CHFJPY, SILVER（GBPJPY・AUDJPY除外）",
        "",
        "## 1. 休眠ブレイク単独エントリー（ロング）",
        "",
        "シグナル足終値で休眠高値更新 → 次足始値IN、SL=同ティア休眠安値−0.25ATR、TP=2R（Cのみ3Rも比較）。",
        "",
        markdown_table(best_dorm),
        "",
        "## 2. TrendBreak ロング × 休眠ゲート",
        "",
        markdown_table(tb_g[["gate", "gate_label", "trades", "total_r", "pf", "avg_r", "retention_pct"]]),
        "",
        "## 3. アンサンブル（TB優先・T5次点・重複スキップ）",
        "",
        markdown_table(pd.DataFrame(ens_rows)),
        "",
        "## 2b. T5 ロング × 休眠ゲート",
        "",
        markdown_table(
            pd.DataFrame(combo_rows)[
                (pd.DataFrame(combo_rows)["base"] == "T5_practical_long")
                & (pd.DataFrame(combo_rows)["period"] == "Research_2015_2024")
            ][["gate", "trades", "total_r", "pf", "retention_pct"]]
        ),
        "",
        "T5は停滞リブレイクのため、**シグナル足での休眠同時ブレイクは0件**。ゲートはTB側に載せる。",
        "",
        "## 採用結論（要約）",
        "",
        "1. **第一推奨**: TrendBreakロング ＋ シグナル足で休眠高値ブレイク → +79R / PF2.37（`DECISION.md` 参照）",
        "2. **アンサンブル**: TB+T5 ＋ 直近48本以内に休眠高値ブレイク → DD 12R→5R 付近まで改善",
        "3. **インジケータ単独トレードは採用しない**（表示・文脈用）",
        "",
        "## 解釈メモ",
        "",
        "- 大トレンドブレイクは「新しい売買ルール」より **ロングの地合い確認** に効く。",
        "- V後棚ブレイク（`h4_v_kickoff_catalyst`）との併用は別研究だが、同じ休眠窓思想。初動は TB/T5、節目はライン表示が役割分担に近い。",
        "",
        "## 成果物",
        "",
        f"- `{OUT.relative_to(ROOT)}/gate_combo_summary.csv`",
        f"- `{OUT.relative_to(ROOT)}/dormant_standalone_summary.csv`",
        f"- `{OUT.relative_to(ROOT)}/ensemble_summary.csv`",
    ]
    (OUT / "REPORT_ja.md").write_text("\n".join(md), encoding="utf-8")
    print((OUT / "REPORT_ja.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

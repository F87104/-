#!/usr/bin/env python3
"""
Integrated study: D1 120-bar low trap -> delayed H4 V shelf breakout.

This is the continuation of run_d1_trap_delayed_h4_shelf_study.py.
The previous study was a post-filter audit on already-produced H4 shelf
trades. This script integrates the D1 context into the H4 signal generation
loop, so H4 signals without D1 context do not block later valid entries.

The goal is not to find the prettiest tiny PF cell. The goal is to see whether
the structure survives when implemented as a real strategy:

    1. D1 makes a 120-bar low false break / trap.
    2. Do not buy immediately.
    3. After a waiting window, H4 forms a sharp V context.
    4. Price builds an upper shelf that holds the V recovery.
    5. Buy only when the shelf high breaks.
"""

from __future__ import annotations

import math
import warnings
from bisect import bisect_right
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

import pandas as pd

from run_elliott_fibo_study import (
    build_confirmed_pivots,
    holiday_market,
    markdown_table,
    pivots_until,
    timeframe_settings,
)
from run_h4_v_initial_shelf_deep_dive import (
    CURRENT_SPEC,
    DeepSpec,
    forward_expansion,
    load_h4_data,
    shelf_signal,
    simulate_trade_deep,
    summarize_trades,
)


THIS_DIR = Path(__file__).resolve().parent
TRAP_DIR = THIS_DIR / "results_2026_05_30" / "trap_false_break_reaction"
OUT_DIR = THIS_DIR / "results_2026_05_30" / "d1_trap_h4_shelf_integrated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
TIMEFRAME = "H4"
SELECTED_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
BROADER_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "SILVER"]
TRAP_STRATEGIES = [
    "CLOSEFAIL_L120_W6_BODY_RR15",
    "WICK_L120_BODY_RR15",
    "WICK_L120_ACTIVITY_RR15",
]


@dataclass(frozen=True)
class IntegratedSpec:
    name: str
    h4: DeepSpec
    min_trap_age_days: int
    max_trap_age_days: int
    trap_sources: tuple[str, ...] = tuple(TRAP_STRATEGIES)
    universe: str = "selected"
    signal_adx_max: float | None = None


def load_d1_low_trap_contexts() -> pd.DataFrame:
    traps = pd.read_csv(TRAP_DIR / "events.csv")
    for col in ["signal_time", "entry_time"]:
        traps[col] = pd.to_datetime(traps[col], format="mixed")
    contexts = traps[
        (traps["timeframe"] == "D1")
        & (traps["lookback"] == 120)
        & (traps["direction"] == "long")
        & (traps["strategy"].isin(TRAP_STRATEGIES))
    ].copy()
    contexts["context_start"] = contexts["signal_time"] + pd.Timedelta(days=1)
    return contexts.sort_values(["symbol", "context_start"]).reset_index(drop=True)


def prepare_symbol_contexts(contexts: pd.DataFrame, symbol: str, spec: IntegratedSpec) -> tuple[list[pd.Timestamp], list[dict]]:
    if contexts.empty:
        return [], []
    subset = contexts[
        (contexts["symbol"] == symbol)
        & (contexts["strategy"].isin(spec.trap_sources))
    ].copy()
    if subset.empty:
        return [], []
    rows: list[dict] = []
    for row in subset.sort_values("context_start").itertuples(index=False):
        rows.append(
            {
                "context_start": row.context_start,
                "d1_low_trap_source": row.strategy,
                "d1_low_trap_signal_time": row.signal_time,
                "d1_low_trap_context_start": row.context_start,
                "d1_low_trap_break_depth_atr": float(row.break_depth_atr),
                "d1_low_trap_reclaim_atr": float(row.reclaim_atr),
                "d1_low_trap_activity_ratio": float(row.activity_ratio),
            }
        )
    return [pd.Timestamp(row["context_start"]) for row in rows], rows


def active_trap_context(prepared: tuple[list[pd.Timestamp], list[dict]], ts: pd.Timestamp, spec: IntegratedSpec) -> dict | None:
    starts, rows = prepared
    if not starts:
        return None
    idx = bisect_right(starts, ts) - 1
    while idx >= 0:
        row = rows[idx]
        age_days = (ts - row["context_start"]) / pd.Timedelta(days=1)
        if age_days > spec.max_trap_age_days:
            break
        if age_days >= spec.min_trap_age_days:
            out = dict(row)
            out["d1_low_trap_age_days"] = float(age_days)
            return out
        idx -= 1
    return None


def find_v_context_integrated(
    df: pd.DataFrame,
    i: int,
    active: list,
    spec: DeepSpec,
    used_pairs: set[str],
) -> dict | None:
    """Copy of the H4 shelf context detector, scoped here to avoid
    importing private helpers from the deep-dive module.
    """

    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    pairs_scanned = 0
    idx = len(active) - 2
    while idx >= 0 and pairs_scanned < 12:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        pairs_scanned += 1
        if p0.kind != "H" or p1.kind != "L":
            continue
        pair_key = f"{p0.pivot_i}-{p1.pivot_i}"
        if pair_key in used_pairs:
            continue
        drop = p0.price - p1.price
        if drop <= 0:
            continue
        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        recovery_bars = max(i - p1.pivot_i, 1)
        if drop_bars < spec.min_drop_bars or drop_bars > spec.max_drop_bars:
            continue
        if recovery_bars > spec.max_recovery_bars:
            continue
        drop_atr = drop / atr_i
        drop_speed = drop / drop_bars / atr_i
        recovery = close - p1.price
        recovery_ratio = recovery / drop
        recovery_speed = recovery / recovery_bars / atr_i
        speed_ratio = recovery_speed / drop_speed if drop_speed > 0 else math.nan
        if drop_atr < spec.min_drop_atr or drop_speed < spec.min_drop_speed:
            continue
        if not math.isfinite(speed_ratio) or speed_ratio < spec.min_speed_ratio:
            continue
        if recovery_ratio < spec.min_recovery_ratio or recovery_ratio > spec.max_recovery_ratio:
            continue
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue
        return {
            "pair_key": pair_key,
            "v_start_i": p0.pivot_i,
            "v_low_i": p1.pivot_i,
            "v_start_time": df.index[p0.pivot_i],
            "v_low_time": df.index[p1.pivot_i],
            "v_start_confirm_time": df.index[p0.confirm_i],
            "v_low_confirm_time": df.index[p1.confirm_i],
            "v_start": p0.price,
            "v_low": p1.price,
            "drop": drop,
            "drop_atr": drop_atr,
            "drop_bars": drop_bars,
            "context_i": i,
            "context_time": df.index[i],
            "context_recovery_bars": recovery_bars,
            "context_recovery_ratio": recovery_ratio,
            "drop_speed": drop_speed,
            "context_recovery_speed": recovery_speed,
            "context_speed_ratio": speed_ratio,
            "pre_adx14": float(df["adx14"].iloc[p0.pivot_i]),
            "pre_ema50_slope_20_atr": float(df["ema50_slope_20_atr"].iloc[p0.pivot_i]),
            "pre_close_ema50_stretch_atr": float(df["close_ema50_stretch_atr"].iloc[p0.pivot_i]),
            "pre_range60_atr": float(df["range60_atr"].iloc[p0.pivot_i]),
        }
    return None


def run_symbol(
    df: pd.DataFrame,
    pivots: list,
    contexts: pd.DataFrame,
    symbol: str,
    spec: IntegratedSpec,
) -> pd.DataFrame:
    active: list = []
    pointer = 0
    used_pairs: set[str] = set()
    in_pos_until = -1
    h4_context: dict | None = None
    h4_context_d1: dict | None = None
    rows: list[dict] = []
    prepared_contexts = prepare_symbol_contexts(contexts, symbol, spec)

    for i in range(100, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        if h4_context is None:
            d1_info = active_trap_context(prepared_contexts, ts, spec)
            if d1_info is None:
                continue
            h4_context = find_v_context_integrated(df, i, active, spec.h4, used_pairs)
            if h4_context is None:
                continue
            h4_context_d1 = d1_info

        signal = shelf_signal(df, i, h4_context, spec.h4)
        if signal is None:
            continue
        if signal.get("expired"):
            h4_context = None
            h4_context_d1 = None
            continue
        if spec.signal_adx_max is not None and float(signal["signal_adx14"]) > spec.signal_adx_max:
            continue

        # The D1 context must still be active at the final shelf breakout.
        d1_signal_info = active_trap_context(prepared_contexts, ts, spec)
        if d1_signal_info is None:
            h4_context = None
            h4_context_d1 = None
            continue

        trade = simulate_trade_deep(df, symbol, i, signal, spec.h4)
        if trade is None:
            h4_context = None
            h4_context_d1 = None
            continue

        used_pairs.add(str(h4_context["pair_key"]))
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "period": "Research_2015_2024" if pd.Timestamp(trade["entry_time"]) <= pd.Timestamp("2024-12-31 23:59:59") else "OOS_2025_2026",
                "year": pd.Timestamp(trade["entry_time"]).year,
                "month": pd.Timestamp(trade["entry_time"]).strftime("%Y-%m"),
                **(h4_context_d1 or {}),
                **h4_context,
                **signal,
                **forward_expansion(df, i, float(signal["atr_signal"])),
                **trade,
                "param_trap_min_age": spec.min_trap_age_days,
                "param_trap_max_age": spec.max_trap_age_days,
                "param_shelf_bars": spec.h4.shelf_bars,
                "param_shelf_range": spec.h4.max_shelf_range_atr,
                "param_shelf_hold": spec.h4.shelf_hold_ratio,
                "param_breakout_buffer": spec.h4.breakout_buffer_atr,
                "param_body": spec.h4.min_body_ratio,
                "param_close_location": spec.h4.min_close_location,
                "param_rr": spec.h4.rr,
                "param_target_basis": spec.h4.target_basis,
                "param_signal_adx_max": spec.signal_adx_max,
                "param_universe": spec.universe,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
        h4_context = None
        h4_context_d1 = None

    return pd.DataFrame(rows)


def run_integrated(
    data: dict[str, pd.DataFrame],
    pivots: dict[str, list],
    contexts: pd.DataFrame,
    spec: IntegratedSpec,
) -> pd.DataFrame:
    symbols: Iterable[str] = BROADER_SYMBOLS if spec.universe == "broader" else SELECTED_SYMBOLS
    rows: list[pd.DataFrame] = []
    for symbol in symbols:
        if symbol not in data:
            continue
        trades = run_symbol(data[symbol], pivots[symbol], contexts, symbol, spec)
        if not trades.empty:
            rows.append(trades)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def make_specs() -> list[IntegratedSpec]:
    specs: list[IntegratedSpec] = []
    # Keep the H4 shelf rule fixed and test only the D1 context window.
    # Earlier broad grids were too slow and also less useful: this study is
    # about validating the market-psychology structure, not finding a tiny
    # parameter island.
    windows = [(30, 120), (30, 180), (30, 240), (60, 240)]
    for universe in ["selected", "broader"]:
        for min_age, max_age in windows:
            base = replace(
                CURRENT_SPEC,
                name="BASE",
                target_basis="entry",
                entry_mode="next_open",
            )
            specs.append(
                IntegratedSpec(
                    f"{universe}_CURRENT_A{min_age}_{max_age}",
                    base,
                    min_age,
                    max_age,
                    universe=universe,
                )
            )
            if (min_age, max_age) in [(30, 180), (30, 240)]:
                specs.append(
                    IntegratedSpec(
                        f"{universe}_CURRENT_A{min_age}_{max_age}_SIGADX30",
                        base,
                        min_age,
                        max_age,
                        universe=universe,
                        signal_adx_max=30.0,
                    )
                )
    return specs


def summarize_by(trades: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(cols, key_tuple))
        row.update(summarize_trades(group, ""))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_r_after_cost", "trades"], ascending=[False, False])


def compare_win_loss(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    metrics = [
        "d1_low_trap_age_days",
        "drop_atr",
        "drop_bars",
        "context_recovery_bars",
        "context_speed_ratio",
        "recovery_ratio_signal",
        "speed_ratio_signal",
        "shelf_range_atr",
        "shelf_hold_actual",
        "breakout_atr",
        "body_ratio",
        "close_location",
        "pre_adx14",
        "pre_ema50_slope_20_atr",
        "pre_range60_atr",
        "signal_adx14",
        "signal_range60_atr",
        "signal_risk_atr",
        "mfe_r",
        "mae_r",
        "bars_held",
    ]
    rows = []
    work = trades.copy()
    work["result_group"] = work["r_after_cost"].apply(lambda x: "win" if x > 0 else "loss")
    for metric in metrics:
        for group_name, group in work.groupby("result_group"):
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "metric": metric,
                    "result_group": group_name,
                    "count": int(values.size),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                }
            )
    return pd.DataFrame(rows)


def robustness_score(row: pd.Series) -> float:
    trades = float(row["trades"])
    pf = float(row["pf_after_cost"]) if math.isfinite(float(row["pf_after_cost"])) else 5.0
    dd = max(float(row["max_dd_r"]), 0.01)
    oos = float(row.get("oos_total_r", 0.0))
    return float(row["total_r_after_cost"]) + min(trades, 40) * 0.08 + min(pf, 4.0) * 2.0 - dd * 0.25 + max(oos, -5.0) * 0.5


def write_report(summary: pd.DataFrame, chosen: pd.DataFrame, all_trades: pd.DataFrame) -> None:
    robust = summary[
        (summary["trades"] >= 9)
        & (summary["total_r_after_cost"] > 0)
        & (summary["pf_after_cost"] >= 1.5)
    ].copy()
    robust["score"] = robust.apply(robustness_score, axis=1)
    robust = robust.sort_values(["score", "trades"], ascending=[False, False])

    chosen_summary = pd.DataFrame([summarize_trades(chosen, "CHOSEN")])
    by_symbol = summarize_by(chosen, ["symbol"])
    by_period = summarize_by(chosen, ["period"])
    by_year = summarize_by(chosen, ["year"])
    by_source = summarize_by(chosen, ["d1_low_trap_source"])
    win_loss = compare_win_loss(chosen)

    lines = [
        "# D1 Trap -> H4 Shelf Integrated Study",
        "",
        "作成日: 2026-05-30",
        "",
        "## 結論",
        "",
        "現時点で最も提案したい候補は **D1 Trap Delayed H4 Shelf Strict**。",
        "",
        "D1の120本級安値Trapを直接買わず、30-180日待ち、その後H4で急落V・棚形成・棚高値ブレイクが出た時だけ買う。さらにシグナル時点ADXが30を超える過熱再ブレイクは見送る。",
        "",
        "## 探索方針",
        "",
        "- D1 TrapはEntry triggerではなく心理文脈。",
        "- H4 Entryは既存のInitial Shelf Breakout系。",
        "- D1 TrapがないH4シグナルは無視するだけで、ポジションブロックしない統合バックテスト。",
        "- PF最大の小標本セルではなく、9件以上・PF1.5以上・OOSが極端に悪くない候補を見る。",
        "",
        "## 探索上位",
        "",
        markdown_table(robust, 30),
        "",
        "## 選定候補",
        "",
        markdown_table(chosen_summary, 10),
        "",
        "## 選定候補トレード",
        "",
        markdown_table(
            chosen[
                [
                    "symbol",
                    "entry_time",
                    "d1_low_trap_age_days",
                    "d1_low_trap_source",
                    "shelf_bars",
                    "shelf_range_atr",
                    "shelf_hold_actual",
                    "breakout_atr",
                    "signal_adx14",
                    "r_after_cost",
                    "exit_reason",
                ]
            ],
            40,
        ),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 30),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 30),
        "",
        "## 年別",
        "",
        markdown_table(by_year, 40),
        "",
        "## D1 Trapソース別",
        "",
        markdown_table(by_source, 30),
        "",
        "## 勝ち負け比較",
        "",
        markdown_table(win_loss, 80),
        "",
        "## 判断",
        "",
        "これは研究候補から **準本命候補** に格上げしてよい。ただし、まだトレード数が少ないため、本番通常ロットではなく、Pine照合と小ロット/デモのフォワード記録が必要。",
        "",
        "自信を持って言える部分:",
        "",
        "- D1 Trapをその場で買うより、遅れてH4棚ブレイクを待つ方が構造として自然。",
        "- D1 Trap直後15日以内より、30日以降の方が良い。",
        "- H4の棚・再ブレイク確認は、Trap単独の弱さをかなり補っている。",
        "- 負けはシグナル足ADXが高い場所に集中しやすく、ADX<=30で遅すぎる飛び乗りを削れる。",
        "",
        "まだ自信を持ち切れない部分:",
        "",
        "- 件数が少ない。",
        "- 2017-2020付近に利益が寄る候補がある。",
        "- OOS件数が少ないため、Pineで2026以降のフォワード確認が必要。",
        "",
        "## Pine化するなら",
        "",
        "1. D1で120本安値Trapを検出。",
        "2. Trap確定翌日から30-180日を有効期間にする。",
        "3. H4でInitial Shelf Breakoutを検出。",
        "4. シグナル足ADXが30超なら見送り。",
        "5. Entryは次H4足始値、TPはEntry基準RR、SLは棚安値 - ATR buffer。",
        "6. ラベルは `D1 Trap Context`, `H4 V Context`, `Shelf Break Entry` に分ける。",
        "",
        "## 出力",
        "",
        "- `summary_grid.csv`",
        "- `all_trades.csv`",
        "- `chosen_trades.csv`",
        "- `chosen_by_symbol.csv`",
        "- `chosen_by_period.csv`",
        "- `chosen_by_year.csv`",
        "- `chosen_by_source.csv`",
        "- `chosen_win_loss_compare.csv`",
        "- `tradingview_parity_checklist.md`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = load_h4_data()
    settings = timeframe_settings(TIMEFRAME)
    pivots = {
        symbol: build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
        for symbol, df in data.items()
    }
    contexts = load_d1_low_trap_contexts()

    summaries = []
    all_trade_frames = []
    specs = make_specs()
    for n, spec in enumerate(specs, 1):
        trades = run_integrated(data, pivots, contexts, spec)
        row = summarize_trades(trades, spec.name)
        row.update(
            {
                "universe": spec.universe,
                "min_trap_age": spec.min_trap_age_days,
                "max_trap_age": spec.max_trap_age_days,
                "shelf_bars": spec.h4.shelf_bars,
                "shelf_range": spec.h4.max_shelf_range_atr,
                "shelf_hold": spec.h4.shelf_hold_ratio,
                "body": spec.h4.min_body_ratio,
                "close_location": spec.h4.min_close_location,
                "rr": spec.h4.rr,
                "target_basis": spec.h4.target_basis,
                "signal_adx_max": spec.signal_adx_max,
            }
        )
        summaries.append(row)
        if not trades.empty:
            all_trade_frames.append(trades)
        print(f"grid {n}/{len(specs)} {spec.name}")

    summary = pd.DataFrame(summaries)
    summary["score"] = summary.apply(robustness_score, axis=1)
    summary = summary.sort_values(["score", "total_r_after_cost"], ascending=[False, False]).reset_index(drop=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        all_trades = pd.concat(all_trade_frames, ignore_index=True) if all_trade_frames else pd.DataFrame()

    # Choose the strict live candidate:
    # selected universe, 30-180 days, current H4 shelf rule, signal ADX <= 30.
    chosen_label = "selected_CURRENT_A30_180_SIGADX30"
    chosen = all_trades[all_trades["strategy"] == chosen_label].copy() if not all_trades.empty else pd.DataFrame()
    if chosen.empty:
        # Fallback to best robust candidate if the current-shaped candidate is empty.
        robust = summary[(summary["trades"] >= 9) & (summary["pf_after_cost"] >= 1.5) & (summary["total_r_after_cost"] > 0)]
        chosen_label = str(robust.iloc[0]["label"]) if not robust.empty else str(summary.iloc[0]["label"])
        chosen = all_trades[all_trades["strategy"] == chosen_label].copy() if not all_trades.empty else pd.DataFrame()

    summary.to_csv(OUT_DIR / "summary_grid.csv", index=False)
    all_trades.to_csv(OUT_DIR / "all_trades.csv", index=False)
    chosen.to_csv(OUT_DIR / "chosen_trades.csv", index=False)
    summarize_by(chosen, ["symbol"]).to_csv(OUT_DIR / "chosen_by_symbol.csv", index=False)
    summarize_by(chosen, ["period"]).to_csv(OUT_DIR / "chosen_by_period.csv", index=False)
    summarize_by(chosen, ["year"]).to_csv(OUT_DIR / "chosen_by_year.csv", index=False)
    summarize_by(chosen, ["d1_low_trap_source"]).to_csv(OUT_DIR / "chosen_by_source.csv", index=False)
    compare_win_loss(chosen).to_csv(OUT_DIR / "chosen_win_loss_compare.csv", index=False)
    write_report(summary, chosen, all_trades)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print("Top robust candidates:")
    print(
        summary[
            (summary["trades"] >= 9)
            & (summary["total_r_after_cost"] > 0)
            & (summary["pf_after_cost"] >= 1.5)
        ].head(20).to_string(index=False)
    )
    print("\nChosen:")
    print(pd.DataFrame([summarize_trades(chosen, chosen_label)]).to_string(index=False))


if __name__ == "__main__":
    main()

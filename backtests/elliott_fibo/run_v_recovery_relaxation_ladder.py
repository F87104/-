#!/usr/bin/env python3
"""
Stepwise relaxation study for sharp-drop V recovery ideas.

Two ladders are compared on H4:
1. Immediate V recovery entry:
   strict complete V recovery -> progressively looser recovery/body/speed rules.
2. V context + trigger entry:
   strict high-stagnation + re-break overlap -> progressively looser trigger rules.

All results use next-bar-open entries and the existing spread/slippage cost table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    StrategySpec,
    add_indicators,
    load_instrument,
    markdown_table,
    resample_ohlc,
    run_spec as run_immediate_spec,
)
from run_v_recovery_trigger_study import (
    TriggerSpec,
    run_spec as run_trigger_spec,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2015_2024" / "v_recovery_relaxation_ladder"
OUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ImmediateStage:
    stage: str
    note: str
    spec: StrategySpec


@dataclass(frozen=True)
class TriggerStage:
    stage: str
    note: str
    spec: TriggerSpec
    overlap_only: bool = False


IMMEDIATE_STAGES = [
    ImmediateStage(
        "I0 厳格",
        "完全回復100%、実体60%、回復本数<=下落本数、回復速度>=下落速度",
        StrategySpec(
            "I0_STRICT_100_BODY60_REC1_SPEED1",
            "V字フィボ",
            fib=1.000,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.5,
            min_v_move_bars=2,
            max_v_move_bars=18,
            max_recovery_bars=18,
            max_recovery_to_drop=1.0,
            min_drop_speed=0.35,
            min_recovery_speed=0.25,
            min_recovery_vs_drop_speed=1.0,
        ),
    ),
    ImmediateStage(
        "I1 回復角度だけ緩和",
        "完全回復100%、回復速度>=下落速度x0.8",
        StrategySpec(
            "I1_100_BODY60_REC1_SPEED08",
            "V字フィボ",
            fib=1.000,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.5,
            min_v_move_bars=2,
            max_v_move_bars=18,
            max_recovery_bars=18,
            max_recovery_to_drop=1.0,
            min_drop_speed=0.35,
            min_recovery_speed=0.25,
            min_recovery_vs_drop_speed=0.8,
        ),
    ),
    ImmediateStage(
        "I2 回復時間を緩和",
        "完全回復100%、回復本数<=下落本数x1.25、最大24本",
        StrategySpec(
            "I2_100_BODY60_REC125_SPEED08",
            "V字フィボ",
            fib=1.000,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.5,
            min_v_move_bars=2,
            max_v_move_bars=18,
            max_recovery_bars=24,
            max_recovery_to_drop=1.25,
            min_drop_speed=0.35,
            min_recovery_speed=0.25,
            min_recovery_vs_drop_speed=0.8,
        ),
    ),
    ImmediateStage(
        "I3 80%回復",
        "完全回復を待たず、80%回復で入る",
        StrategySpec(
            "I3_800_BODY60_REC125_SPEED08",
            "V字フィボ",
            fib=0.800,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.5,
            min_v_move_bars=2,
            max_v_move_bars=18,
            max_recovery_bars=24,
            max_recovery_to_drop=1.25,
            min_drop_speed=0.35,
            min_recovery_speed=0.25,
            min_recovery_vs_drop_speed=0.8,
        ),
    ),
    ImmediateStage(
        "I4 61.8%回復",
        "61.8%回復で入る",
        StrategySpec(
            "I4_618_BODY60_REC125_SPEED08",
            "V字フィボ",
            fib=0.618,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.5,
            min_v_move_bars=2,
            max_v_move_bars=18,
            max_recovery_bars=24,
            max_recovery_to_drop=1.25,
            min_drop_speed=0.35,
            min_recovery_speed=0.25,
            min_recovery_vs_drop_speed=0.8,
        ),
    ),
    ImmediateStage(
        "I5 急落条件を緩和",
        "61.8%回復、下落幅3.0ATR、下落速度0.25ATR/本",
        StrategySpec(
            "I5_618_BODY60_DROP30_SPEED025",
            "V字フィボ",
            fib=0.618,
            rr=2.0,
            body_min=0.60,
            direction_filter="long",
            min_v_move_atr=3.0,
            min_v_move_bars=2,
            max_v_move_bars=24,
            max_recovery_bars=30,
            max_recovery_to_drop=1.5,
            min_drop_speed=0.25,
            min_recovery_speed=0.20,
            min_recovery_vs_drop_speed=0.6,
        ),
    ),
    ImmediateStage(
        "I6 実体50%",
        "I5から実体条件を50%へ緩和",
        StrategySpec(
            "I6_618_BODY50_DROP30_SPEED025",
            "V字フィボ",
            fib=0.618,
            rr=2.0,
            body_min=0.50,
            direction_filter="long",
            min_v_move_atr=3.0,
            min_v_move_bars=2,
            max_v_move_bars=24,
            max_recovery_bars=30,
            max_recovery_to_drop=1.5,
            min_drop_speed=0.25,
            min_recovery_speed=0.20,
            min_recovery_vs_drop_speed=0.6,
        ),
    ),
    ImmediateStage(
        "I7 実体条件なし",
        "I5から実体条件を撤廃",
        StrategySpec(
            "I7_618_NOBODY_DROP30_SPEED025",
            "V字フィボ",
            fib=0.618,
            rr=2.0,
            body_min=0.0,
            direction_filter="long",
            min_v_move_atr=3.0,
            min_v_move_bars=2,
            max_v_move_bars=24,
            max_recovery_bars=30,
            max_recovery_to_drop=1.5,
            min_drop_speed=0.25,
            min_recovery_speed=0.20,
            min_recovery_vs_drop_speed=0.6,
        ),
    ),
]


TRIGGER_STAGES = [
    TriggerStage(
        "T0 厳格重なり",
        "61.8-80%候補、下落4ATR、速度0.60、回復<=下落、停滞+再ブレイク重なりのみ",
        TriggerSpec(
            "T0_FAST_BIGDROP_REC1_OVERLAP",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=4.0,
            min_drop_speed=0.60,
            max_recovery_to_drop=1.0,
            trigger_mode="either",
        ),
        overlap_only=True,
    ),
    TriggerStage(
        "T1 下落幅だけ緩和",
        "下落幅3.5ATR、速度0.60、回復<=下落、停滞+再ブレイク重なりのみ",
        TriggerSpec(
            "T1_FAST_REC1_OVERLAP",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=3.5,
            min_drop_speed=0.60,
            max_recovery_to_drop=1.0,
            trigger_mode="either",
        ),
        overlap_only=True,
    ),
    TriggerStage(
        "T2 速度を緩和",
        "下落幅3.5ATR、速度0.30、回復<=下落、停滞+再ブレイク重なりのみ",
        TriggerSpec(
            "T2_BASE_REC1_OVERLAP",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=3.5,
            min_drop_speed=0.30,
            max_recovery_to_drop=1.0,
            trigger_mode="either",
        ),
        overlap_only=True,
    ),
    TriggerStage(
        "T3 回復時間を緩和",
        "回復<=下落x1.5、停滞+再ブレイク重なりのみ",
        TriggerSpec(
            "T3_BASE_REC15_OVERLAP",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=3.5,
            min_drop_speed=0.30,
            max_recovery_to_drop=1.5,
            trigger_mode="either",
        ),
        overlap_only=True,
    ),
    TriggerStage(
        "T4 再ブレイクのみ",
        "重なり条件を外し、再ブレイク単独も許可",
        TriggerSpec(
            "T4_REBREAK_ONLY",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=3.5,
            min_drop_speed=0.30,
            max_recovery_to_drop=1.5,
            trigger_mode="rebreak",
        ),
        overlap_only=False,
    ),
    TriggerStage(
        "T5 停滞または再ブレイク",
        "高値停滞か再ブレイクのどちらかで許可",
        TriggerSpec(
            "T5_STAG_OR_REBREAK",
            fib_min=0.618,
            fib_max=0.800,
            min_move_atr=3.5,
            min_drop_speed=0.30,
            max_recovery_to_drop=1.5,
            trigger_mode="either",
        ),
        overlap_only=False,
    ),
]


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(values[values <= 0].sum())
    if gross_loss < 0:
        return gross_profit / abs(gross_loss)
    return math.inf if gross_profit > 0 else math.nan


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    curve = values.cumsum()
    peak = curve.cummax()
    return float((peak - curve).max())


def max_losing_streak(values: pd.Series) -> int:
    cur = 0
    best = 0
    for value in values:
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def summarize_stage(df: pd.DataFrame, ladder: str, stage: str, note: str, trigger_type: str = "") -> dict:
    if df.empty:
        return {
            "ladder": ladder,
            "stage": stage,
            "note": note,
            "trigger_type": trigger_type,
            "trades": 0,
            "win_rate": math.nan,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": math.nan,
            "pf_after_cost": math.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "avg_hold_bars": math.nan,
        }
    r = df["r_after_cost"]
    return {
        "ladder": ladder,
        "stage": stage,
        "note": note,
        "trigger_type": trigger_type,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r_after_cost": float(r.sum()),
        "avg_r_after_cost": float(r.mean()),
        "pf_after_cost": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "avg_hold_bars": float(df["bars_held"].mean()),
    }


def run_h4_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        data[symbol] = add_indicators(resample_ohlc(raw, "H4"))
    return data


def main() -> None:
    h4_data = run_h4_data()
    all_trade_frames = []
    summary_rows = []

    for stage in IMMEDIATE_STAGES:
        stage_frames = []
        for symbol, df in h4_data.items():
            trades = run_immediate_spec(df, symbol, "H4", stage.spec)
            if not trades.empty:
                trades = trades.copy()
                trades["ladder"] = "Immediate V"
                trades["stage"] = stage.stage
                trades["note"] = stage.note
                stage_frames.append(trades)
        stage_trades = pd.concat(stage_frames, ignore_index=True) if stage_frames else pd.DataFrame()
        if not stage_trades.empty:
            all_trade_frames.append(stage_trades)
        summary_rows.append(summarize_stage(stage_trades, "Immediate V", stage.stage, stage.note))

    for stage in TRIGGER_STAGES:
        stage_frames = []
        for symbol, df in h4_data.items():
            trades = run_trigger_spec(df, symbol, "H4", stage.spec)
            if trades.empty:
                continue
            trades = trades.copy()
            if stage.overlap_only:
                trades = trades[trades["trigger_type"].eq("stagnation+rebreak")].copy()
            if not trades.empty:
                trades["ladder"] = "V Context + Trigger"
                trades["stage"] = stage.stage
                trades["note"] = stage.note
                stage_frames.append(trades)
        stage_trades = pd.concat(stage_frames, ignore_index=True) if stage_frames else pd.DataFrame()
        if not stage_trades.empty:
            all_trade_frames.append(stage_trades)
        summary_rows.append(
            summarize_stage(
                stage_trades,
                "V Context + Trigger",
                stage.stage,
                stage.note,
                "overlap only" if stage.overlap_only else "accepted triggers",
            )
        )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "summary_ladder.csv", index=False)

    if all_trade_frames:
        trades_all = pd.concat(all_trade_frames, ignore_index=True)
        for col in ["signal_time", "entry_time", "exit_time"]:
            if col in trades_all:
                trades_all[col] = pd.to_datetime(trades_all[col])
        trades_all = trades_all.sort_values(["ladder", "stage", "entry_time", "symbol"]).reset_index(drop=True)
    else:
        trades_all = pd.DataFrame()
    trades_all.to_csv(OUT_DIR / "trades_ladder.csv", index=False)

    by_symbol_rows = []
    if not trades_all.empty:
        for (ladder, stage, symbol), group in trades_all.groupby(["ladder", "stage", "symbol"], sort=False):
            note = str(group["note"].iloc[0]) if "note" in group else ""
            by_symbol_rows.append(summarize_stage(group, ladder, stage, note, symbol))
    by_symbol = pd.DataFrame(by_symbol_rows)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)

    report = [
        "# H4 急落後V字回復 条件緩和ラダー 2015-2024",
        "",
        "## 見方",
        "",
        "- `Immediate V`: V字回復そのもので即エントリーする検証。",
        "- `V Context + Trigger`: V字は候補抽出に使い、その後の高値停滞/再ブレイクで入る検証。",
        "- すべてH4、買いのみ、シグナル次足始値エントリー、コスト込みR。",
        "",
        "## ラダー結果",
        "",
        markdown_table(summary, 50),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 120),
        "",
        "## 出力",
        "",
        "- `summary_ladder.csv`",
        "- `summary_by_symbol.csv`",
        "- `trades_ladder.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

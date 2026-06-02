#!/usr/bin/env python3
"""
Market Psychology Squeeze exit refinement.

Purpose:
  The prior TV-check study showed that SQZ_STRICT_RR2 ex GBPJPY has positive
  expectancy, while losers tend to suffer deeper MAE early. This script tests
  simple, explainable early-failure exits without changing the entry idea.

Core entry:
  SQZ_STRICT_RR2 = sharp drop -> 6-bar shelf -> close breaks shelf high.

Exit variants:
  - BASE: original SL/TP/time exit.
  - RETURN_INSIDE_N: if price closes back inside the shelf within N bars, exit.
  - NO_PROGRESS_N: if after N bars the trade has not reached +0.5R MFE, exit.
  - COMBO: both checks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from run_market_psychology_strategy_tv_check import (
    PsySpec,
    RUN_END,
    RUN_START,
    load_data,
    period_name,
    squeeze_signal,
    summarize,
    summary_by,
)
from run_elliott_fibo_study import direction_cost_r, markdown_table


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_06_02" / "market_psychology_squeeze_exit_refinement"
OUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ExitVariant:
    name: str
    rr: float = 2.0
    max_hold: int = 120
    return_inside_bars: int = 0
    no_progress_bars: int = 0
    min_progress_r: float = 0.50


ENTRY_SPEC = PsySpec(
    "SQZ_STRICT_ENTRY",
    "short_squeeze",
    rr=2.0,
    shelf_atr=2.0,
    move_atr=3.5,
)

VARIANTS = [
    ExitVariant("BASE_RR2", rr=2.0),
    ExitVariant("BASE_RR15", rr=1.5),
    ExitVariant("BASE_RR25", rr=2.5),
    ExitVariant("RETURN_INSIDE_2_RR2", rr=2.0, return_inside_bars=2),
    ExitVariant("RETURN_INSIDE_3_RR2", rr=2.0, return_inside_bars=3),
    ExitVariant("NO_PROGRESS_6_05R_RR2", rr=2.0, no_progress_bars=6, min_progress_r=0.50),
    ExitVariant("NO_PROGRESS_8_05R_RR2", rr=2.0, no_progress_bars=8, min_progress_r=0.50),
    ExitVariant(
        "RETURN3_PLUS_NOPROG6_RR2",
        rr=2.0,
        return_inside_bars=3,
        no_progress_bars=6,
        min_progress_r=0.50,
    ),
]


def simulate_long_variant(
    df: pd.DataFrame,
    symbol: str,
    signal_i: int,
    signal: dict,
    variant: ExitVariant,
) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None

    entry = float(df["open"].iloc[entry_i])
    stop = float(signal["stop"])
    risk = entry - stop
    if not math.isfinite(risk) or risk <= 0:
        return None

    shelf_high = float(signal["shelf_high"])
    target = entry + risk * variant.rr
    end_i = min(len(df) - 1, entry_i + variant.max_hold)
    exit_i = end_i
    exit_price = float(df["close"].iloc[end_i])
    reason = "time"
    mfe = 0.0
    mae = 0.0

    for j in range(entry_i, end_i + 1):
        high = float(df["high"].iloc[j])
        low = float(df["low"].iloc[j])
        close = float(df["close"].iloc[j])
        bars_held = j - entry_i + 1

        mfe = max(mfe, (high - entry) / risk)
        mae = max(mae, (entry - low) / risk)

        hit_stop = low <= stop
        hit_target = high >= target
        if hit_stop or hit_target:
            exit_i = j
            exit_price = stop if hit_stop else target
            reason = "stop" if hit_stop else "target"
            break

        if variant.return_inside_bars > 0 and bars_held <= variant.return_inside_bars and close <= shelf_high:
            exit_i = j
            exit_price = close
            reason = "return_inside_shelf"
            break

        if (
            variant.no_progress_bars > 0
            and bars_held >= variant.no_progress_bars
            and mfe < variant.min_progress_r
        ):
            exit_i = j
            exit_price = close
            reason = "no_progress"
            break

    r_clean, r_after_cost = direction_cost_r(symbol, "long", entry, exit_price, risk)
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i + 1,
        "risk": risk,
        "r_clean": r_clean,
        "r_after_cost": r_after_cost,
        "mfe_r": mfe,
        "mae_r": mae,
    }


def run_variant(df: pd.DataFrame, symbol: str, variant: ExitVariant) -> pd.DataFrame:
    rows: list[dict] = []
    in_pos_until = -1
    start_i = max(80, ENTRY_SPEC.shelf_bars + ENTRY_SPEC.drop_win + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END:
            continue
        if i <= in_pos_until:
            continue

        signal = squeeze_signal(df, i, ENTRY_SPEC)
        if signal is None:
            continue
        if float(df["close"].iloc[i]) <= float(signal["stop"]):
            continue

        trade = simulate_long_variant(df, symbol, i, signal, variant)
        if trade is None:
            continue

        rows.append(
            {
                "symbol": symbol,
                "strategy": variant.name,
                "family": "short_squeeze_exit_refinement",
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "rr": variant.rr,
                "return_inside_bars": variant.return_inside_bars,
                "no_progress_bars": variant.no_progress_bars,
                "min_progress_r": variant.min_progress_r,
                **signal,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def win_loss_compare(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    features = [
        "shelf_range_atr",
        "sharp_drop_atr",
        "signal_range_atr",
        "body_ratio",
        "close_location",
        "mfe_r",
        "mae_r",
        "bars_held",
    ]
    rows = []
    for bucket, group in [("win", trades[trades["r_after_cost"] > 0]), ("loss", trades[trades["r_after_cost"] < 0])]:
        row = {"label": label, "bucket": bucket, "trades": len(group)}
        for col in features:
            row[f"{col}_avg"] = float(group[col].mean()) if not group.empty else math.nan
            row[f"{col}_median"] = float(group[col].median()) if not group.empty else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def write_report(all_trades: pd.DataFrame) -> None:
    summary = summary_by(all_trades, ["strategy"])
    ex_gbp = summary_by(all_trades[all_trades["symbol"] != "GBPJPY"].copy(), ["strategy"])
    by_symbol = summary_by(all_trades, ["strategy", "symbol"])
    by_period = summary_by(all_trades, ["strategy", "period"])
    ex_gbp_period = summary_by(all_trades[all_trades["symbol"] != "GBPJPY"].copy(), ["strategy", "period"])

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    ex_gbp.to_csv(OUT_DIR / "summary_ex_gbp.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    ex_gbp_period.to_csv(OUT_DIR / "summary_ex_gbp_by_period.csv", index=False)

    compares = []
    for strategy, group in all_trades.groupby("strategy"):
        compares.append(win_loss_compare(group, strategy))
        ex = group[group["symbol"] != "GBPJPY"].copy()
        if not ex.empty:
            compares.append(win_loss_compare(ex, f"{strategy}_EX_GBPJPY"))
    pd.concat(compares, ignore_index=True).to_csv(OUT_DIR / "win_loss_compare.csv", index=False)

    lines = [
        "# Market Psychology Squeeze Exit Refinement",
        "",
        "作成日: 2026-06-02",
        "",
        "## 目的",
        "",
        "`SQZ_STRICT_RR2` の入口を変えず、負けを早く切る出口だけで改善するかを確認した。",
        "",
        "## 全通貨サマリー",
        "",
        markdown_table(summary, 30),
        "",
        "## GBPJPY除外サマリー",
        "",
        markdown_table(ex_gbp, 30),
        "",
        "## GBPJPY除外 期間別",
        "",
        markdown_table(ex_gbp_period, 80),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 120),
        "",
        "## 暫定判断",
        "",
        "- 入口の本質は変えない。急落後の棚上抜けだけを見る。",
        "- `return_inside_shelf` は、踏み上げ失敗を早く認めるための自然な撤退候補。",
        "- `no_progress` はやや裁量的なので、PFだけ良くても過剰最適化疑いとして扱う。",
        "",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = load_data()
    frames = []
    for variant in VARIANTS:
        for symbol, df in data.items():
            trades = run_variant(df, symbol, variant)
            if not trades.empty:
                frames.append(trades)
    all_trades = pd.concat(frames, ignore_index=True).sort_values(["strategy", "signal_time", "symbol"]).reset_index(drop=True)
    all_trades.to_csv(OUT_DIR / "trades.csv", index=False)
    write_report(all_trades)
    print(f"Wrote {OUT_DIR}")
    print(summary_by(all_trades, ["strategy"]).to_string(index=False))
    print()
    print("EX GBPJPY")
    print(summary_by(all_trades[all_trades["symbol"] != "GBPJPY"], ["strategy"]).to_string(index=False))


if __name__ == "__main__":
    main()

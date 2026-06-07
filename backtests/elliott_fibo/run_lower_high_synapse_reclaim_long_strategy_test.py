#!/usr/bin/env python3
"""
Lower High 3 Touch red-line reclaim long strategy test.

This turns the observation event into a simple trade model:
- long at the confirmed close above the visible LH3 red line
- stop below the lowest low from H3 to the reclaim bar
- fixed targets at 1R / 1.5R / 2R
- max-hold exits at 48 / 120 bars

The goal is not optimization. It is a first win-rate / PF check for the exact
"enter when the red line is reclaimed" idea.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, direction_cost_r, load_instrument, resample_ohlc
from run_lower_high_synapse_reclaim_long_scanner import HORIZONS, SPECS, detect_events, markdown_table


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "lower_high_synapse_reclaim_long_strategy_2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RR_TARGETS = (1.0, 1.5, 2.0)
MAX_HOLD_BARS = (48, 120)
STOP_BUFFER_ATR = 0.20


def profit_factor(r: pd.Series) -> float:
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    return float(wins / losses) if losses > 0 else math.inf


def max_losing_streak(r: pd.Series) -> int:
    best = 0
    cur = 0
    for v in r:
        if float(v) <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    equity = r.cumsum()
    return float((equity.cummax() - equity).max())


def simulate_trade(
    df: pd.DataFrame,
    symbol: str,
    signal_i: int,
    h3_i: int,
    rr: float,
    max_hold: int,
) -> dict | None:
    entry = float(df["close"].iloc[signal_i])
    atr_entry = float(df["atr"].iloc[signal_i])
    if not math.isfinite(entry) or not math.isfinite(atr_entry) or atr_entry <= 0:
        return None

    structure_low = float(df["low"].iloc[h3_i : signal_i + 1].min())
    stop = structure_low - atr_entry * STOP_BUFFER_ATR
    risk = entry - stop
    if not math.isfinite(risk) or risk <= 0:
        return None

    target = entry + risk * rr
    end_i = min(len(df) - 1, signal_i + max_hold)
    if end_i <= signal_i:
        return None

    exit_i = end_i
    exit_price = float(df["close"].iloc[end_i])
    exit_reason = "time"

    for i in range(signal_i + 1, end_i + 1):
        low = float(df["low"].iloc[i])
        high = float(df["high"].iloc[i])
        hit_stop = low <= stop
        hit_target = high >= target
        if hit_stop and hit_target:
            exit_i = i
            exit_price = stop
            exit_reason = "stop_and_target_same_bar_stop_first"
            break
        if hit_stop:
            exit_i = i
            exit_price = stop
            exit_reason = "stop"
            break
        if hit_target:
            exit_i = i
            exit_price = target
            exit_reason = "target"
            break

    path = df.iloc[signal_i + 1 : exit_i + 1]
    mfe_r = (float(path["high"].max()) - entry) / risk if not path.empty else 0.0
    mae_r = (entry - float(path["low"].min())) / risk if not path.empty else 0.0
    r_clean, r_after = direction_cost_r(symbol, "long", entry, exit_price, risk)
    return {
        "rr": rr,
        "max_hold_bars": max_hold,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "exit_time": df.index[exit_i],
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "bars_held": exit_i - signal_i,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "r_clean": r_clean,
        "r_after_cost": r_after,
    }


def summarize_trades(trades: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    if trades.empty:
        return pd.DataFrame()
    for key, group in trades.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        ordered = group.sort_values("entry_time").reset_index(drop=True)
        r = ordered["r_after_cost"].astype(float)
        oos = ordered[ordered["period"] == "OOS_2025_2026"]
        rows.append(
            {
                **dict(zip(group_cols, key_tuple)),
                "trades": int(len(ordered)),
                "win_rate": float((r > 0).mean() * 100),
                "total_r_after_cost": float(r.sum()),
                "avg_r_after_cost": float(r.mean()),
                "median_r_after_cost": float(r.median()),
                "pf_after_cost": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "avg_mfe_r": float(ordered["mfe_r"].mean()),
                "avg_mae_r": float(ordered["mae_r"].mean()),
                "avg_bars_held": float(ordered["bars_held"].mean()),
                "target_hit_pct": float(ordered["exit_reason"].eq("target").mean() * 100),
                "stop_hit_pct": float(ordered["exit_reason"].str.startswith("stop").mean() * 100),
                "oos_trades": int(len(oos)),
                "oos_total_r": float(oos["r_after_cost"].sum()) if not oos.empty else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["total_r_after_cost", "pf_after_cost"], ascending=[False, False])


def build_report(summary: pd.DataFrame, by_symbol: pd.DataFrame) -> str:
    h4 = summary[summary["timeframe"].eq("H4")].copy()
    best_h4 = h4.iloc[0] if not h4.empty else None
    xau_h4 = by_symbol[
        by_symbol["symbol"].eq("XAUUSD") & by_symbol["timeframe"].eq("H4")
    ].copy()
    silver_h4 = by_symbol[
        by_symbol["symbol"].eq("SILVER") & by_symbol["timeframe"].eq("H4")
    ].copy()

    lines = [
        "# Lower High 3 Touch 赤LINE上抜けロング 勝率/PF検証 v0.1",
        "",
        "作成日: 2026-06-08",
        "",
        "赤いLH3下降LINEを終値で上抜けた足でロングする、というアイデアを初回検証した。",
        "",
        "## ルール",
        "",
        "- エントリー: 赤いLH3下降LINEを終値で上抜けた足の終値",
        f"- SL: H3後から上抜け足までの最安値 - {STOP_BUFFER_ATR:.2f}ATR",
        "- TP: 1R / 1.5R / 2R を比較",
        "- 時間切れ: 48本 / 120本で比較",
        "- 同一足でTP/SLが両方ついた場合は、保守的にSL先着扱い",
        "- R: 既存コスト表のspread/slippage込み `r_after_cost`",
        "",
        "## 全体サマリー",
        "",
        markdown_table(summary.round(2)),
        "",
        "## 通貨別サマリー",
        "",
        markdown_table(by_symbol.round(2)),
        "",
        "## 暫定判断",
        "",
    ]

    if best_h4 is not None:
        lines.append(
            f"- H4の最上位は RR{best_h4['rr']} / {int(best_h4['max_hold_bars'])}本。"
            f"勝率 {best_h4['win_rate']:.2f}%、PF {best_h4['pf_after_cost']:.2f}、"
            f"総R {best_h4['total_r_after_cost']:.2f}R。"
        )
    if not xau_h4.empty:
        r = xau_h4.iloc[0]
        lines.append(
            f"- XAUUSD H4の最上位は RR{r['rr']} / {int(r['max_hold_bars'])}本。"
            f"勝率 {r['win_rate']:.2f}%、PF {r['pf_after_cost']:.2f}、総R {r['total_r_after_cost']:.2f}R。"
        )
    if not silver_h4.empty:
        r = silver_h4.iloc[0]
        lines.append(
            f"- SILVER H4の最上位は RR{r['rr']} / {int(r['max_hold_bars'])}本。"
            f"勝率 {r['win_rate']:.2f}%、PF {r['pf_after_cost']:.2f}、総R {r['total_r_after_cost']:.2f}R。"
        )

    lines.extend(
        [
            "",
            "この段階では、赤LINE上抜けだけを本番化しない。",
            "理由は、件数が多く、上抜け直後に振らされるケースが残るため。",
            "次はB水平線上抜け、A水平線上抜け、上抜け後の浅い戻り確認で絞る。",
            "",
            "## 出力ファイル",
            "",
            "- [trades.csv](trades.csv)",
            "- [summary_by_rule.csv](summary_by_rule.csv)",
            "- [summary_by_symbol_rule.csv](summary_by_symbol_rule.csv)",
            "",
            "## 再現",
            "",
            "```bash",
            "python3 backtests/elliott_fibo/run_lower_high_synapse_reclaim_long_strategy_test.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    trades: list[dict] = []
    frames: dict[tuple[str, str], pd.DataFrame] = {}

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        for spec in SPECS:
            frame = add_indicators(resample_ohlc(raw, spec.timeframe))
            frames[(symbol, spec.timeframe)] = frame
            events = detect_events(frame, symbol, spec)
            if not events:
                continue
            for event in events:
                event_time = pd.Timestamp(event["event_time"])
                h3_time = pd.Timestamp(event["h3_time"])
                if event_time not in frame.index or h3_time not in frame.index:
                    continue
                signal_i = int(frame.index.get_loc(event_time))
                h3_i = int(frame.index.get_loc(h3_time))
                for rr in RR_TARGETS:
                    for max_hold in MAX_HOLD_BARS:
                        result = simulate_trade(frame, symbol, signal_i, h3_i, rr, max_hold)
                        if result is None:
                            continue
                        trades.append(
                            {
                                "symbol": symbol,
                                "timeframe": spec.timeframe,
                                "rule": f"{spec.timeframe}_red_line_reclaim_RR{rr:g}_H{max_hold}",
                                "period": event["period"],
                                "entry_time": event_time,
                                "h1_time": event["h1_time"],
                                "h2_time": event["h2_time"],
                                "h3_time": h3_time,
                                "bars_after_h3": event["bars_after_h3"],
                                "line_price": event["line_price"],
                                "line_reclaim_level": event["line_reclaim_level"],
                                **result,
                            }
                        )

    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df = trades_df.sort_values(["timeframe", "symbol", "entry_time", "rr", "max_hold_bars"]).reset_index(drop=True)
    summary = summarize_trades(trades_df, ["timeframe", "rr", "max_hold_bars"]) if not trades_df.empty else pd.DataFrame()
    by_symbol = (
        summarize_trades(trades_df, ["symbol", "timeframe", "rr", "max_hold_bars"])
        if not trades_df.empty
        else pd.DataFrame()
    )

    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_by_rule.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol_rule.csv", index=False)
    (OUT_DIR / "REPORT_ja.md").write_text(build_report(summary, by_symbol), encoding="utf-8")

    print(f"trades: {len(trades_df)}")
    print(f"wrote: {OUT_DIR}")
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

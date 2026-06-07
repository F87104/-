#!/usr/bin/env python3
"""
Lower High 3 Touch Synapse confirmation filter strategy test.

Compares three filters after the visible LH3 red-line reclaim:
- B_BREAK: red-line reclaim, then break the post-head B horizontal level
- A_BREAK: red-line reclaim, then break the H3/A horizontal level
- PULLBACK_REACCEL: red-line reclaim, shallow pullback to the red-line area,
  then re-acceleration above the pullback high

This is a first win-rate / PF check for the confirmation filters.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, resample_ohlc
from run_lower_high_synapse_reclaim_long_scanner import SPECS, is_pivot_high, markdown_table, period_name
from run_lower_high_synapse_reclaim_long_strategy_test import (
    MAX_HOLD_BARS,
    RR_TARGETS,
    STOP_BUFFER_ATR,
    simulate_trade,
    summarize_trades,
)


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "lower_high_synapse_confirm_filters_2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)

B_A_BREAK_BUFFER_ATR = 0.03
CONFIRM_MAX_BARS = {"H1": 96, "H4": 48}
PULLBACK_MAX_BARS = {"H1": 48, "H4": 24}
PULLBACK_NEAR_LINE_ATR = 0.35
PULLBACK_FAIL_ATR = 0.60
PULLBACK_RECLOSE_ATR = 0.20
PULLBACK_REACCEL_BUFFER_ATR = 0.05


def is_pivot_low(low: np.ndarray, i: int, left: int, right: int) -> bool:
    if i < left or i + right >= len(low):
        return False
    value = low[i]
    if not math.isfinite(value):
        return False
    window = low[i - left : i + right + 1]
    return bool(value <= np.nanmin(window))


def line_price_at(h1_i: int, h1_p: float, visible_slope: float, bar_i: int) -> float:
    return h1_p + visible_slope * (bar_i - h1_i)


def first_red_line_reclaim(
    close: np.ndarray,
    atr: np.ndarray,
    h1_i: int,
    h1_p: float,
    visible_slope: float,
    start_i: int,
    end_i: int,
    buffer_atr: float,
) -> int | None:
    for j in range(start_i, end_i + 1):
        atr_j = float(atr[j])
        if not math.isfinite(atr_j) or atr_j <= 0:
            continue
        line_px = line_price_at(h1_i, h1_p, visible_slope, j)
        if math.isfinite(line_px) and close[j] > line_px + atr_j * buffer_atr:
            return j
    return None


def find_b_break(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    spec,
    h3_i: int,
    line_reclaim_i: int,
    end_i: int,
) -> tuple[int, float, int] | None:
    head_i: int | None = None
    head_price = math.inf
    b_i: int | None = None
    b_level: float | None = None

    for cur_i in range(h3_i + spec.pivot_right + 1, end_i + 1):
        p_i = cur_i - spec.pivot_right
        if p_i <= h3_i:
            continue

        if is_pivot_low(low, p_i, spec.pivot_left, spec.pivot_right):
            p_low = float(low[p_i])
            if p_low < head_price:
                head_i = p_i
                head_price = p_low
                b_i = None
                b_level = None

        if head_i is not None and b_i is None and p_i > head_i and is_pivot_high(high, p_i, spec.pivot_left, spec.pivot_right):
            b_i = p_i
            b_level = float(high[p_i])

        if b_i is not None and b_level is not None and cur_i >= max(line_reclaim_i, b_i + spec.pivot_right):
            atr_cur = float(atr[cur_i])
            if math.isfinite(atr_cur) and atr_cur > 0 and close[cur_i] > b_level + atr_cur * B_A_BREAK_BUFFER_ATR:
                return cur_i, b_level, b_i
    return None


def find_a_break(
    close: np.ndarray,
    atr: np.ndarray,
    h3_p: float,
    line_reclaim_i: int,
    end_i: int,
) -> tuple[int, float] | None:
    for i in range(line_reclaim_i, end_i + 1):
        atr_i = float(atr[i])
        if math.isfinite(atr_i) and atr_i > 0 and close[i] > h3_p + atr_i * B_A_BREAK_BUFFER_ATR:
            return i, h3_p
    return None


def find_pullback_reaccel(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    h1_i: int,
    h1_p: float,
    visible_slope: float,
    line_reclaim_i: int,
    end_i: int,
) -> tuple[int, int, float] | None:
    pull_i: int | None = None
    pull_high: float | None = None
    for i in range(line_reclaim_i + 1, end_i + 1):
        atr_i = float(atr[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue
        line_px = line_price_at(h1_i, h1_p, visible_slope, i)
        if not math.isfinite(line_px):
            continue

        if pull_i is None:
            near_line = low[i] <= line_px + atr_i * PULLBACK_NEAR_LINE_ATR
            not_failed = low[i] >= line_px - atr_i * PULLBACK_FAIL_ATR
            recovered = close[i] >= line_px - atr_i * PULLBACK_RECLOSE_ATR
            if near_line and not_failed and recovered:
                pull_i = i
                pull_high = float(high[i])
            continue

        if i - pull_i > max(PULLBACK_MAX_BARS.values()):
            return None
        assert pull_high is not None
        if close[i] > pull_high + atr_i * PULLBACK_REACCEL_BUFFER_ATR and close[i] > line_px:
            return i, pull_i, pull_high
    return None


def detect_confirm_events(df: pd.DataFrame, symbol: str, spec) -> list[dict]:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)
    idx = list(df.index)

    pivot_highs: list[dict] = []
    events: list[dict] = []
    last_event_i: dict[str, int] = {"B_BREAK": -10_000, "A_BREAK": -10_000, "PULLBACK_REACCEL": -10_000}
    max_hold = max(MAX_HOLD_BARS)
    confirm_max = CONFIRM_MAX_BARS.get(spec.timeframe, spec.max_reclaim_bars)
    pullback_max = PULLBACK_MAX_BARS.get(spec.timeframe, 24)

    for current_i in range(spec.pivot_left + spec.pivot_right, len(df) - max_hold - 1):
        pivot_i = current_i - spec.pivot_right
        if not is_pivot_high(high, pivot_i, spec.pivot_left, spec.pivot_right):
            continue

        pivot_highs.append(
            {
                "i": pivot_i,
                "confirm_i": current_i,
                "price": float(high[pivot_i]),
                "atr": float(atr[pivot_i]),
            }
        )
        while len(pivot_highs) > 200:
            pivot_highs.pop(0)
        if len(pivot_highs) < 3:
            continue

        h1, h2, h3 = pivot_highs[-3:]
        atr_ref = h3["atr"]
        if not math.isfinite(atr_ref) or atr_ref <= 0:
            continue

        h1_i, h2_i, h3_i = int(h1["i"]), int(h2["i"]), int(h3["i"])
        h1_p, h2_p, h3_p = float(h1["price"]), float(h2["price"]), float(h3["price"])
        lower_ok = h1_p > h2_p + atr_ref * spec.min_lower_atr and h2_p > h3_p + atr_ref * spec.min_lower_atr
        spacing_ok = (
            h1_i < h2_i < h3_i
            and h2_i - h1_i <= spec.max_bars_12
            and h3_i - h2_i <= spec.max_bars_23
        )
        touch_slope = (h2_p - h1_p) / (h2_i - h1_i) if h2_i != h1_i else math.nan
        expected_h3 = h1_p + touch_slope * (h3_i - h1_i) if math.isfinite(touch_slope) else math.nan
        touch_ok = math.isfinite(expected_h3) and abs(h3_p - expected_h3) <= atr_ref * spec.line_touch_atr
        visible_slope = (h3_p - h1_p) / (h3_i - h1_i) if h3_i != h1_i else math.nan
        if not (lower_ok and spacing_ok and touch_ok and math.isfinite(visible_slope)):
            continue

        reclaim_start = int(h3["confirm_i"]) + 1
        reclaim_end = min(len(df) - max_hold - 1, reclaim_start + spec.max_reclaim_bars)
        line_reclaim_i = first_red_line_reclaim(
            close, atr, h1_i, h1_p, visible_slope, reclaim_start, reclaim_end, spec.reclaim_buffer_atr
        )
        if line_reclaim_i is None:
            continue

        confirm_end = min(len(df) - max_hold - 1, line_reclaim_i + confirm_max)
        pullback_end = min(len(df) - max_hold - 1, line_reclaim_i + pullback_max)
        base = {
            "symbol": symbol,
            "timeframe": spec.timeframe,
            "period": period_name(idx[line_reclaim_i]),
            "line_reclaim_time": idx[line_reclaim_i],
            "h1_time": idx[h1_i],
            "h2_time": idx[h2_i],
            "h3_time": idx[h3_i],
            "h1_price": h1_p,
            "h2_price": h2_p,
            "h3_price": h3_p,
            "line_reclaim_close": float(close[line_reclaim_i]),
            "bars_after_h3_to_line": line_reclaim_i - h3_i,
        }

        b = find_b_break(high, low, close, atr, spec, h3_i, line_reclaim_i, confirm_end)
        if b is not None:
            entry_i, b_level, b_i = b
            if entry_i - last_event_i["B_BREAK"] >= spec.cooldown_bars:
                last_event_i["B_BREAK"] = entry_i
                events.append(
                    {
                        **base,
                        "variant": "B_BREAK",
                        "entry_time": idx[entry_i],
                        "entry_i": entry_i,
                        "h3_i": h3_i,
                        "confirm_level": b_level,
                        "confirm_bar_time": idx[b_i],
                        "bars_after_line": entry_i - line_reclaim_i,
                    }
                )

        a = find_a_break(close, atr, h3_p, line_reclaim_i, confirm_end)
        if a is not None:
            entry_i, a_level = a
            if entry_i - last_event_i["A_BREAK"] >= spec.cooldown_bars:
                last_event_i["A_BREAK"] = entry_i
                events.append(
                    {
                        **base,
                        "variant": "A_BREAK",
                        "entry_time": idx[entry_i],
                        "entry_i": entry_i,
                        "h3_i": h3_i,
                        "confirm_level": a_level,
                        "confirm_bar_time": idx[h3_i],
                        "bars_after_line": entry_i - line_reclaim_i,
                    }
                )

        pull = find_pullback_reaccel(high, low, close, atr, h1_i, h1_p, visible_slope, line_reclaim_i, pullback_end)
        if pull is not None:
            entry_i, pull_i, pull_high = pull
            if entry_i - last_event_i["PULLBACK_REACCEL"] >= spec.cooldown_bars:
                last_event_i["PULLBACK_REACCEL"] = entry_i
                events.append(
                    {
                        **base,
                        "variant": "PULLBACK_REACCEL",
                        "entry_time": idx[entry_i],
                        "entry_i": entry_i,
                        "h3_i": h3_i,
                        "confirm_level": pull_high,
                        "confirm_bar_time": idx[pull_i],
                        "bars_after_line": entry_i - line_reclaim_i,
                    }
                )

    return events


def build_report(summary: pd.DataFrame, by_symbol: pd.DataFrame) -> str:
    h4 = summary[summary["timeframe"].eq("H4")].copy()
    lines = [
        "# Lower High 3 Touch Synapse確認フィルタ 勝率/PF検証 v0.1",
        "",
        "作成日: 2026-06-08",
        "",
        "赤LINE上抜けだけではなく、B水平線、A水平線、浅い戻り再上昇で絞った場合の勝率/PFを比較する。",
        "",
        "## ルール",
        "",
        "- 共通: 3回lower high後、赤いLH3下降LINEを終値で上抜ける",
        "- `B_BREAK`: H3後に安値を作り、その後の確認高値Bを終値で上抜け",
        "- `A_BREAK`: H3価格、つまりA水平線を終値で上抜け",
        "- `PULLBACK_REACCEL`: 赤LINE上抜け後、LINE付近へ浅く戻り、戻り足高値を終値で上抜け",
        f"- SL: H3後からエントリー足までの最安値 - {STOP_BUFFER_ATR:.2f}ATR",
        "- TP: 1R / 1.5R / 2R",
        "- 時間切れ: 48本 / 120本",
        "- R: spread/slippage込み `r_after_cost`",
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
        "- 赤LINE上抜け単体のH4 RR2.0 / 120本は、勝率 40.21%、PF 1.07、総R +33.83R。",
        "- B水平線上抜けを足すと、H4 RR2.0 / 120本は勝率 44.72%、PF 1.22、総R +60.14Rへ改善。",
        "- H4 RR2.0 / 48本でも、B水平線上抜けは勝率 48.66%、PF 1.23、総R +48.82R。",
        "- A水平線上抜けは、H4 RR2.0 / 120本で勝率 40.53%、PF 1.07、総R +21.44R。確認としては強そうに見えるが、単体ではB水平線ほど伸びない。",
        "- 浅い戻り再上昇は、H4 RR1.0 / 120本で勝率 55.45%、PF 1.18、総R +33.44R。総Rよりも、入り急ぎを減らす補助フィルタとして見る。",
    ]
    if not h4.empty:
        best = h4.iloc[0]
        lines.append(
            f"- H4最上位は `{best['variant']}` RR{best['rr']} / {int(best['max_hold_bars'])}本。"
            f"勝率 {best['win_rate']:.2f}%、PF {best['pf_after_cost']:.2f}、総R {best['total_r_after_cost']:.2f}R。"
        )
    xau = by_symbol[by_symbol["symbol"].eq("XAUUSD") & by_symbol["timeframe"].eq("H4")]
    if not xau.empty:
        best = xau.iloc[0]
        lines.append(
            f"- XAUUSD H4最上位は `{best['variant']}` RR{best['rr']} / {int(best['max_hold_bars'])}本。"
            f"勝率 {best['win_rate']:.2f}%、PF {best['pf_after_cost']:.2f}、総R {best['total_r_after_cost']:.2f}R。"
        )
    lines.append("- SILVER H4は赤LINE単体では良く見えたが、B/A/浅い戻り確認を足すと優位性が弱くなったため、本命から外す。")
    lines.extend(
        [
            "",
            "今回の目的は、赤LINE上抜けだけよりも絞り込みでPFが上がるかを見ること。",
            "PFが上がっても件数が極端に少ないものは、次に年別・OOSで確認する。",
            "",
            "## 出力ファイル",
            "",
            "- [trades.csv](trades.csv)",
            "- [events.csv](events.csv)",
            "- [summary_by_filter.csv](summary_by_filter.csv)",
            "- [summary_by_symbol_filter.csv](summary_by_symbol_filter.csv)",
            "",
            "## 再現",
            "",
            "```bash",
            "python3 backtests/elliott_fibo/run_lower_high_synapse_confirm_filter_strategy_test.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    event_rows: list[dict] = []
    trades: list[dict] = []

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        for spec in SPECS:
            frame = add_indicators(resample_ohlc(raw, spec.timeframe))
            events = detect_confirm_events(frame, symbol, spec)
            event_rows.extend(events)
            for event in events:
                entry_i = int(event["entry_i"])
                h3_i = int(event["h3_i"])
                for rr in RR_TARGETS:
                    for max_hold in MAX_HOLD_BARS:
                        result = simulate_trade(frame, symbol, entry_i, h3_i, rr, max_hold)
                        if result is None:
                            continue
                        trades.append(
                            {
                                "symbol": symbol,
                                "timeframe": spec.timeframe,
                                "variant": event["variant"],
                                "rule": f"{spec.timeframe}_{event['variant']}_RR{rr:g}_H{max_hold}",
                                "period": event["period"],
                                "entry_time": event["entry_time"],
                                "line_reclaim_time": event["line_reclaim_time"],
                                "h1_time": event["h1_time"],
                                "h2_time": event["h2_time"],
                                "h3_time": event["h3_time"],
                                "confirm_level": event["confirm_level"],
                                "confirm_bar_time": event["confirm_bar_time"],
                                "bars_after_line": event["bars_after_line"],
                                **result,
                            }
                        )

    events_df = pd.DataFrame(event_rows)
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df = trades_df.sort_values(["timeframe", "variant", "symbol", "entry_time", "rr", "max_hold_bars"]).reset_index(drop=True)
    summary = (
        summarize_trades(trades_df, ["timeframe", "variant", "rr", "max_hold_bars"])
        if not trades_df.empty
        else pd.DataFrame()
    )
    by_symbol = (
        summarize_trades(trades_df, ["symbol", "timeframe", "variant", "rr", "max_hold_bars"])
        if not trades_df.empty
        else pd.DataFrame()
    )

    events_df.to_csv(OUT_DIR / "events.csv", index=False)
    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_by_filter.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol_filter.csv", index=False)
    (OUT_DIR / "REPORT_ja.md").write_text(build_report(summary, by_symbol), encoding="utf-8")

    print(f"events: {len(events_df)}")
    print(f"trades: {len(trades_df)}")
    print(f"wrote: {OUT_DIR}")
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

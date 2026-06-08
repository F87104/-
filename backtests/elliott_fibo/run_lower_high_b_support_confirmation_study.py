#!/usr/bin/env python3
"""
Lower High 3 Touch B support confirmation study.

Compares three entry timings after the same LH3 red-line reclaim and B break:
- ENTRY_A_B_BREAK: enter at the B horizontal close break
- ENTRY_B_B_SUPPORT_REACCEL: wait for B to behave as support, then re-accelerate
- ENTRY_C_A_AFTER_B: wait for A/H3 horizontal reclaim after B break

The goal is to test whether waiting for "B becomes floor" improves win rate/PF.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, resample_ohlc
from run_lower_high_synapse_confirm_filter_strategy_test import B_A_BREAK_BUFFER_ATR, detect_confirm_events
from run_lower_high_synapse_reclaim_long_scanner import SPECS, markdown_table
from run_lower_high_synapse_reclaim_long_strategy_test import (
    MAX_HOLD_BARS,
    RR_TARGETS,
    STOP_BUFFER_ATR,
    simulate_trade,
    summarize_trades,
)


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "lower_high_b_support_confirmation_2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)

B_SUPPORT_RETEST_MAX_BARS = {"H1": 48, "H4": 24}
B_SUPPORT_REACCEL_MAX_BARS = {"H1": 24, "H4": 12}
A_AFTER_B_MAX_BARS = {"H1": 96, "H4": 48}

SUPPORT_NEAR_B_ATR = 0.35
SUPPORT_FAIL_ATR = 0.45
SUPPORT_CLOSE_TOLERANCE_ATR = 0.10
REACCEL_BUFFER_ATR = 0.05


def find_b_support_reaccel(
    df: pd.DataFrame,
    b_break_i: int,
    b_level: float,
    timeframe: str,
) -> tuple[int, int, float] | None:
    """Return entry_i, retest_i, retest_high when B acts as support."""
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)

    retest_i: int | None = None
    retest_high: float | None = None
    retest_end = min(len(df) - 1, b_break_i + B_SUPPORT_RETEST_MAX_BARS.get(timeframe, 24))
    reaccel_max = B_SUPPORT_REACCEL_MAX_BARS.get(timeframe, 12)

    for i in range(b_break_i + 1, retest_end + 1):
        atr_i = float(atr[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue

        # If B is clearly lost before a valid retest, this setup failed.
        if close[i] < b_level - atr_i * SUPPORT_FAIL_ATR:
            return None

        if retest_i is None:
            near_b = low[i] <= b_level + atr_i * SUPPORT_NEAR_B_ATR
            not_lost = low[i] >= b_level - atr_i * SUPPORT_FAIL_ATR
            close_recovered = close[i] >= b_level - atr_i * SUPPORT_CLOSE_TOLERANCE_ATR
            if near_b and not_lost and close_recovered:
                retest_i = i
                retest_high = float(high[i])
            continue

        if i - retest_i > reaccel_max:
            return None
        assert retest_high is not None
        retest_high = max(retest_high, float(high[i - 1]))
        reaccelerated = close[i] > retest_high + atr_i * REACCEL_BUFFER_ATR and close[i] > b_level
        if reaccelerated:
            return i, retest_i, retest_high

    return None


def find_a_after_b(
    df: pd.DataFrame,
    b_break_i: int,
    h3_price: float,
    timeframe: str,
) -> tuple[int, float] | None:
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)
    end_i = min(len(df) - 1, b_break_i + A_AFTER_B_MAX_BARS.get(timeframe, 48))
    for i in range(b_break_i, end_i + 1):
        atr_i = float(atr[i])
        if math.isfinite(atr_i) and atr_i > 0 and close[i] > h3_price + atr_i * B_A_BREAK_BUFFER_ATR:
            return i, h3_price
    return None


def build_entry_events(df: pd.DataFrame, symbol: str, spec) -> list[dict]:
    events = []
    b_events = [e for e in detect_confirm_events(df, symbol, spec) if e["variant"] == "B_BREAK"]
    idx = list(df.index)

    for event in b_events:
        b_break_i = int(event["entry_i"])
        h3_i = int(event["h3_i"])
        b_level = float(event["confirm_level"])
        h3_price = float(event["h3_price"])

        base = {
            **event,
            "b_break_time": event["entry_time"],
            "b_break_i": b_break_i,
            "b_level": b_level,
        }

        events.append(
            {
                **base,
                "variant": "ENTRY_A_B_BREAK",
                "entry_i": b_break_i,
                "entry_time": event["entry_time"],
                "confirm_level": b_level,
                "confirm_bar_time": event["confirm_bar_time"],
                "bars_after_b": 0,
            }
        )

        support = find_b_support_reaccel(df, b_break_i, b_level, spec.timeframe)
        if support is not None:
            entry_i, retest_i, retest_high = support
            events.append(
                {
                    **base,
                    "variant": "ENTRY_B_B_SUPPORT_REACCEL",
                    "entry_i": entry_i,
                    "entry_time": idx[entry_i],
                    "confirm_level": retest_high,
                    "confirm_bar_time": idx[retest_i],
                    "bars_after_b": entry_i - b_break_i,
                    "support_retest_time": idx[retest_i],
                }
            )

        a_after_b = find_a_after_b(df, b_break_i, h3_price, spec.timeframe)
        if a_after_b is not None:
            entry_i, a_level = a_after_b
            events.append(
                {
                    **base,
                    "variant": "ENTRY_C_A_AFTER_B",
                    "entry_i": entry_i,
                    "entry_time": idx[entry_i],
                    "confirm_level": a_level,
                    "confirm_bar_time": idx[h3_i],
                    "bars_after_b": entry_i - b_break_i,
                }
            )

    return events


def compact_best_rows(summary: pd.DataFrame, timeframe: str = "H4") -> pd.DataFrame:
    if summary.empty:
        return summary
    return summary[summary["timeframe"].eq(timeframe)].sort_values(
        ["total_r_after_cost", "pf_after_cost"], ascending=[False, False]
    )


def build_report(summary: pd.DataFrame, by_symbol: pd.DataFrame) -> str:
    h4 = compact_best_rows(summary, "H4")
    xau_h4 = by_symbol[by_symbol["symbol"].eq("XAUUSD") & by_symbol["timeframe"].eq("H4")]

    def pick(df: pd.DataFrame, timeframe: str, variant: str, rr: float, max_hold: int) -> pd.Series | None:
        subset = df[
            df["timeframe"].eq(timeframe)
            & df["variant"].eq(variant)
            & df["rr"].eq(rr)
            & df["max_hold_bars"].eq(max_hold)
        ]
        return None if subset.empty else subset.iloc[0]

    h4_a = pick(summary, "H4", "ENTRY_A_B_BREAK", 2.0, 120)
    h4_b = pick(summary, "H4", "ENTRY_B_B_SUPPORT_REACCEL", 2.0, 120)
    h1_a = pick(summary, "H1", "ENTRY_A_B_BREAK", 2.0, 120)
    h1_b = pick(summary, "H1", "ENTRY_B_B_SUPPORT_REACCEL", 1.5, 120)

    lines = [
        "# LH3 B抜け後サポート化確認 勝率/PF検証 v0.1",
        "",
        "作成日: 2026-06-08",
        "",
        "目的は、LH3 + 赤LINE上抜け + B水平線上抜けのあと、すぐ入るよりも、Bが床になったことを確認してから入る方が勝率/PFを上げられるかを見ること。",
        "",
        "## 比較した入口",
        "",
        "| variant | 入口 | 狙い |",
        "|---|---|---|",
        "| ENTRY_A_B_BREAK | B水平線を終値で上抜けた足 | 最速。取り逃しは少ないがダマシを受ける |",
        "| ENTRY_B_B_SUPPORT_REACCEL | B上抜け後、B付近へ浅く戻り、Bを割らずに再上昇 | Bが床になった確認。勝率改善狙い |",
        "| ENTRY_C_A_AFTER_B | B上抜け後、A/H3水平線も終値で上抜け | 強い確認。ただし遅れる可能性 |",
        "",
        "## ルール",
        "",
        "- 共通: 3回lower high後、赤いLH3下降LINEを終値で上抜け、その後B水平線を上抜ける",
        f"- Bサポート化: B上抜け後、lowがB + {SUPPORT_NEAR_B_ATR:.2f}ATR以内へ戻る",
        f"- B失敗: 終値がB - {SUPPORT_FAIL_ATR:.2f}ATRより下で失効",
        f"- 再上昇: 戻り足高値 + {REACCEL_BUFFER_ATR:.2f}ATRを終値で上抜け",
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
    ]

    if not h4.empty:
        for variant in ["ENTRY_A_B_BREAK", "ENTRY_B_B_SUPPORT_REACCEL", "ENTRY_C_A_AFTER_B"]:
            subset = h4[h4["variant"].eq(variant)]
            if subset.empty:
                continue
            row = subset.iloc[0]
            lines.append(
                f"- H4 {variant}: 最上位は RR{row['rr']} / {int(row['max_hold_bars'])}本。"
                f"勝率 {row['win_rate']:.2f}%、PF {row['pf_after_cost']:.2f}、総R {row['total_r_after_cost']:.2f}R、件数 {int(row['trades'])}。"
            )

    if not xau_h4.empty:
        best_xau = xau_h4.iloc[0]
        lines.append(
            f"- XAUUSD H4の最上位は {best_xau['variant']} RR{best_xau['rr']} / {int(best_xau['max_hold_bars'])}本。"
            f"勝率 {best_xau['win_rate']:.2f}%、PF {best_xau['pf_after_cost']:.2f}、総R {best_xau['total_r_after_cost']:.2f}R。"
        )

    lines.extend(["", "## 重要な気づき", ""])
    if h4_a is not None and h4_b is not None:
        lines.append(
            "- H4では、Bサポート化確認は「万能の勝率改善」ではなかった。"
            f"ENTRY_A_B_BREAK RR2.0/120本は勝率 {h4_a['win_rate']:.2f}%、PF {h4_a['pf_after_cost']:.2f}、総R {h4_a['total_r_after_cost']:.2f}R、最大DD {h4_a['max_dd_r']:.2f}R。"
            f"ENTRY_B_B_SUPPORT_REACCEL RR2.0/120本は勝率 {h4_b['win_rate']:.2f}%、PF {h4_b['pf_after_cost']:.2f}、総R {h4_b['total_r_after_cost']:.2f}R、最大DD {h4_b['max_dd_r']:.2f}R。"
        )
        lines.append(
            "- つまり、B床化は勝率を少し上げ、最大DDをかなり下げるが、件数と総Rを大きく減らす。"
            "H4では本線をB抜け即エントリー、B床化を危険回避・ロット調整の補助条件として扱う。"
        )
    if h1_a is not None and h1_b is not None:
        lines.append(
            "- H1ではB床化の価値が少し変わる。"
            f"ENTRY_A_B_BREAK RR2.0/120本はPF {h1_a['pf_after_cost']:.2f}、最大DD {h1_a['max_dd_r']:.2f}R。"
            f"ENTRY_B_B_SUPPORT_REACCEL RR1.5/120本はPF {h1_b['pf_after_cost']:.2f}、最大DD {h1_b['max_dd_r']:.2f}R。"
            "H1では利益最大化より、荒い振れを減らすフィルタとして研究価値がある。"
        )
    lines.extend(
        [
            "- 直感では「Bを抜けたあと、一度支えられてから入るほうが強い」と見える。"
            "ただし数字では、XAUUSD H4のようにB抜け即のほうが強いケースがある。",
            "- 次は、B床化そのものを入口にするより、B抜け即エントリーから除外すべき危険条件を探す。"
            "候補は、巨大陽線で損切りが遠い、A水平線まで距離がない、D1抵抗直下、上抜け後すぐ大陰線でBを割る場面。",
        ]
    )

    lines.extend(
        [
            "",
            "今回の読み方:",
            "",
            "- 勝率だけでなく、件数、総R、OOS、最大DDを一緒に見る。",
            "- Bサポート化で勝率が上がっても、件数が減りすぎる場合は実運用の候補ではなく補助条件にする。",
            "- B抜け即エントリーが総Rで勝ち、Bサポート化が勝率/DDで勝つなら、リアル運用ではロットを分ける余地がある。",
            "",
            "## 出力ファイル",
            "",
            "- [trades.csv](trades.csv)",
            "- [events.csv](events.csv)",
            "- [summary_by_entry.csv](summary_by_entry.csv)",
            "- [summary_by_symbol_entry.csv](summary_by_symbol_entry.csv)",
            "",
            "## 再現",
            "",
            "```bash",
            "python3 backtests/elliott_fibo/run_lower_high_b_support_confirmation_study.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    event_rows: list[dict] = []
    trade_rows: list[dict] = []

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        for spec in SPECS:
            frame = add_indicators(resample_ohlc(raw, spec.timeframe))
            events = build_entry_events(frame, symbol, spec)
            event_rows.extend(events)
            for event in events:
                entry_i = int(event["entry_i"])
                h3_i = int(event["h3_i"])
                for rr in RR_TARGETS:
                    for max_hold in MAX_HOLD_BARS:
                        result = simulate_trade(frame, symbol, entry_i, h3_i, rr, max_hold)
                        if result is None:
                            continue
                        trade_rows.append(
                            {
                                "symbol": symbol,
                                "timeframe": spec.timeframe,
                                "variant": event["variant"],
                                "rule": f"{spec.timeframe}_{event['variant']}_RR{rr:g}_H{max_hold}",
                                "period": event["period"],
                                "entry_time": event["entry_time"],
                                "line_reclaim_time": event["line_reclaim_time"],
                                "b_break_time": event["b_break_time"],
                                "h1_time": event["h1_time"],
                                "h2_time": event["h2_time"],
                                "h3_time": event["h3_time"],
                                "b_level": event["b_level"],
                                "confirm_level": event["confirm_level"],
                                "confirm_bar_time": event["confirm_bar_time"],
                                "bars_after_line": event["bars_after_line"],
                                "bars_after_b": event["bars_after_b"],
                                **result,
                            }
                        )

    events_df = pd.DataFrame(event_rows)
    trades = pd.DataFrame(trade_rows)
    if not trades.empty:
        trades = trades.sort_values(["timeframe", "variant", "symbol", "entry_time", "rr", "max_hold_bars"]).reset_index(drop=True)
    summary = summarize_trades(trades, ["timeframe", "variant", "rr", "max_hold_bars"]) if not trades.empty else pd.DataFrame()
    by_symbol = (
        summarize_trades(trades, ["symbol", "timeframe", "variant", "rr", "max_hold_bars"])
        if not trades.empty
        else pd.DataFrame()
    )

    events_df.to_csv(OUT_DIR / "events.csv", index=False)
    trades.to_csv(OUT_DIR / "trades.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_by_entry.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol_entry.csv", index=False)
    (OUT_DIR / "REPORT_ja.md").write_text(build_report(summary, by_symbol), encoding="utf-8")

    print(f"events: {len(events_df)}")
    print(f"trades: {len(trades)}")
    print(f"wrote: {OUT_DIR}")
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

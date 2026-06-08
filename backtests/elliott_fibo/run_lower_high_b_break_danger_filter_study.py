#!/usr/bin/env python3
"""
Lower High 3 Touch B-break danger filter study.

The previous study found that H4 B-break immediate entries stayed stronger than
waiting for B to become support, especially on XAUUSD H4. This script keeps the
B-break entry as the baseline and tests which danger conditions should be
excluded instead.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, resample_ohlc
from run_lower_high_synapse_confirm_filter_strategy_test import detect_confirm_events
from run_lower_high_synapse_reclaim_long_scanner import SPECS, markdown_table
from run_lower_high_synapse_reclaim_long_strategy_test import (
    MAX_HOLD_BARS,
    RR_TARGETS,
    simulate_trade,
    summarize_trades,
)


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "lower_high_b_break_danger_filters_2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def finite(value: float) -> bool:
    return math.isfinite(float(value))


def add_daily_context(d1: pd.DataFrame) -> pd.DataFrame:
    out = d1.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["prev60_high"] = out["high"].rolling(60, min_periods=20).max()
    out["prev20_high"] = out["high"].rolling(20, min_periods=10).max()
    return out


def daily_context_at(d1: pd.DataFrame, entry_time: pd.Timestamp) -> dict:
    prior = d1[d1.index < entry_time.normalize()]
    if prior.empty:
        return {
            "d1_prev60_high": math.nan,
            "d1_prev20_high": math.nan,
            "d1_close": math.nan,
            "d1_ema20": math.nan,
            "d1_ema50": math.nan,
        }
    row = prior.iloc[-1]
    return {
        "d1_prev60_high": float(row.get("prev60_high", math.nan)),
        "d1_prev20_high": float(row.get("prev20_high", math.nan)),
        "d1_close": float(row.get("close", math.nan)),
        "d1_ema20": float(row.get("ema20", math.nan)),
        "d1_ema50": float(row.get("ema50", math.nan)),
    }


def compute_features(frame: pd.DataFrame, d1: pd.DataFrame, event: dict, result: dict) -> dict:
    entry_i = int(event["entry_i"])
    bar = frame.iloc[entry_i]
    entry_time = pd.Timestamp(event["entry_time"])
    entry = float(result["entry"])
    risk = float(result["risk"])
    atr_entry = float(bar["atr"])
    rng = float(bar["high"] - bar["low"])
    body = abs(float(bar["close"] - bar["open"]))
    h3_price = float(event["h3_price"])
    b_level = float(event["confirm_level"])
    d1_ctx = daily_context_at(d1, entry_time)

    a_room_price = h3_price - entry
    a_room_r = a_room_price / risk if risk > 0 and a_room_price > 0 else math.inf
    a_room_atr = a_room_price / atr_entry if atr_entry > 0 else math.nan
    d1_prev60_room_atr = (
        (d1_ctx["d1_prev60_high"] - entry) / atr_entry
        if finite(d1_ctx["d1_prev60_high"]) and atr_entry > 0
        else math.nan
    )
    d1_prev20_room_atr = (
        (d1_ctx["d1_prev20_high"] - entry) / atr_entry
        if finite(d1_ctx["d1_prev20_high"]) and atr_entry > 0
        else math.nan
    )

    return {
        "atr_entry": atr_entry,
        "entry_range_atr": rng / atr_entry if atr_entry > 0 else math.nan,
        "entry_body_atr": body / atr_entry if atr_entry > 0 else math.nan,
        "entry_close_location": (float(bar["close"]) - float(bar["low"])) / rng if rng > 0 else math.nan,
        "break_extension_atr": (entry - b_level) / atr_entry if atr_entry > 0 else math.nan,
        "risk_atr": risk / atr_entry if atr_entry > 0 else math.nan,
        "a_room_r": a_room_r,
        "a_room_atr": a_room_atr,
        "a_already_cleared": bool(entry >= h3_price),
        "d1_prev60_room_atr": d1_prev60_room_atr,
        "d1_prev20_room_atr": d1_prev20_room_atr,
        "d1_close_above_ema20": bool(
            finite(d1_ctx["d1_close"]) and finite(d1_ctx["d1_ema20"]) and d1_ctx["d1_close"] > d1_ctx["d1_ema20"]
        ),
        "d1_close_above_ema50": bool(
            finite(d1_ctx["d1_close"]) and finite(d1_ctx["d1_ema50"]) and d1_ctx["d1_close"] > d1_ctx["d1_ema50"]
        ),
        **d1_ctx,
    }


def not_d1_resistance_near(series: pd.Series, threshold_atr: float) -> pd.Series:
    room = series["d1_prev60_room_atr"]
    return room.isna() | (room < 0) | (room >= threshold_atr)


def a_room_ok(series: pd.Series, min_room_r: float) -> pd.Series:
    return series["a_already_cleared"] | series["a_room_r"].ge(min_room_r)


FILTERS: list[tuple[str, str, Callable[[pd.DataFrame], pd.Series]]] = [
    ("BASELINE", "B抜け即。除外なし", lambda x: pd.Series(True, index=x.index)),
    ("RISK_LE_2_5ATR", "損切り幅が2.5ATR以内", lambda x: x["risk_atr"].le(2.5)),
    ("RISK_LE_3ATR", "損切り幅が3.0ATR以内", lambda x: x["risk_atr"].le(3.0)),
    ("RANGE_LE_2ATR", "エントリー足の高安が2.0ATR以内", lambda x: x["entry_range_atr"].le(2.0)),
    ("BODY_LE_1ATR", "エントリー足の実体が1.0ATR以内", lambda x: x["entry_body_atr"].le(1.0)),
    ("BREAK_EXT_LE_0_8ATR", "Bから0.8ATR以上伸びた飛び乗りを除外", lambda x: x["break_extension_atr"].le(0.8)),
    ("BREAK_EXT_LE_1_2ATR", "Bから1.2ATR以上伸びた飛び乗りを除外", lambda x: x["break_extension_atr"].le(1.2)),
    ("A_ROOM_GE_0_5R", "Aが上に残る場合、Aまで0.5R以上", lambda x: a_room_ok(x, 0.5)),
    ("A_ROOM_GE_1R", "Aが上に残る場合、Aまで1R以上", lambda x: a_room_ok(x, 1.0)),
    ("NO_D1_RESIST_1ATR", "D1過去60日高値が1ATR未満にある場所を除外", lambda x: not_d1_resistance_near(x, 1.0)),
    ("D1_CLOSE_GT_EMA20", "D1終値がEMA20より上", lambda x: x["d1_close_above_ema20"]),
    ("CLOSE_LOC_GE_60", "エントリー足の終値位置が上位60%以上", lambda x: x["entry_close_location"].ge(0.60)),
    (
        "COMBO_RISK_CHASE",
        "損切り3ATR以内 + Bから1.2ATR以内",
        lambda x: x["risk_atr"].le(3.0) & x["break_extension_atr"].le(1.2),
    ),
    (
        "COMBO_STRUCTURE",
        "損切り3ATR以内 + Bから1.2ATR以内 + Aまで0.5R以上",
        lambda x: x["risk_atr"].le(3.0) & x["break_extension_atr"].le(1.2) & a_room_ok(x, 0.5),
    ),
    (
        "COMBO_D1",
        "損切り3ATR以内 + Bから1.2ATR以内 + A余白 + D1抵抗近接なし",
        lambda x: x["risk_atr"].le(3.0)
        & x["break_extension_atr"].le(1.2)
        & a_room_ok(x, 0.5)
        & not_d1_resistance_near(x, 1.0),
    ),
]


def add_scope_rows(filtered: pd.DataFrame, filter_id: str, filter_desc: str) -> pd.DataFrame:
    rows = []
    h4 = filtered[filtered["timeframe"].eq("H4")].copy()
    if not h4.empty:
        h4["scope"] = "ALL_H4"
        rows.append(h4)
    xau_h4 = filtered[filtered["symbol"].eq("XAUUSD") & filtered["timeframe"].eq("H4")].copy()
    if not xau_h4.empty:
        xau_h4["scope"] = "XAUUSD_H4"
        rows.append(xau_h4)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["filter_id"] = filter_id
    out["filter_desc"] = filter_desc
    return out


def select_rule(summary: pd.DataFrame, scope: str, rr: float, max_hold: int) -> pd.DataFrame:
    return summary[
        summary["scope"].eq(scope)
        & summary["rr"].eq(rr)
        & summary["max_hold_bars"].eq(max_hold)
    ].copy()


def best_candidate(summary: pd.DataFrame, scope: str, rr: float, max_hold: int, min_trades: int) -> pd.Series | None:
    subset = select_rule(summary, scope, rr, max_hold)
    subset = subset[subset["trades"].ge(min_trades) & ~subset["filter_id"].eq("BASELINE")]
    if subset.empty:
        return None
    subset = subset.sort_values(["pf_after_cost", "total_r_after_cost"], ascending=[False, False])
    return subset.iloc[0]


def baseline_row(summary: pd.DataFrame, scope: str, rr: float, max_hold: int) -> pd.Series | None:
    subset = select_rule(summary, scope, rr, max_hold)
    subset = subset[subset["filter_id"].eq("BASELINE")]
    return None if subset.empty else subset.iloc[0]


def filter_row(summary: pd.DataFrame, scope: str, filter_id: str, rr: float, max_hold: int) -> pd.Series | None:
    subset = select_rule(summary, scope, rr, max_hold)
    subset = subset[subset["filter_id"].eq(filter_id)]
    return None if subset.empty else subset.iloc[0]


def line_for(row: pd.Series) -> str:
    return (
        f"{row['filter_id']}: {int(row['trades'])}件、勝率 {row['win_rate']:.2f}%、"
        f"PF {row['pf_after_cost']:.2f}、総R {row['total_r_after_cost']:.2f}R、"
        f"最大DD {row['max_dd_r']:.2f}R"
    )


def build_report(summary: pd.DataFrame, trades: pd.DataFrame) -> str:
    xau_base_48 = baseline_row(summary, "XAUUSD_H4", 2.0, 48)
    xau_base_120 = baseline_row(summary, "XAUUSD_H4", 2.0, 120)
    xau_best_48 = best_candidate(summary, "XAUUSD_H4", 2.0, 48, min_trades=30)
    xau_best_120 = best_candidate(summary, "XAUUSD_H4", 2.0, 120, min_trades=30)
    xau_aroom_48 = filter_row(summary, "XAUUSD_H4", "A_ROOM_GE_0_5R", 2.0, 48)
    xau_close_loc_48 = filter_row(summary, "XAUUSD_H4", "CLOSE_LOC_GE_60", 2.0, 48)
    xau_d1_ema_48 = filter_row(summary, "XAUUSD_H4", "D1_CLOSE_GT_EMA20", 2.0, 48)
    xau_d1_res_48 = filter_row(summary, "XAUUSD_H4", "NO_D1_RESIST_1ATR", 2.0, 48)
    xau_risk_48 = filter_row(summary, "XAUUSD_H4", "RISK_LE_3ATR", 2.0, 48)
    all_base_120 = baseline_row(summary, "ALL_H4", 2.0, 120)
    all_best_120 = best_candidate(summary, "ALL_H4", 2.0, 120, min_trades=200)

    xau_features = trades[
        trades["scope"].eq("XAUUSD_H4")
        & trades["filter_id"].eq("BASELINE")
        & trades["rr"].eq(2.0)
        & trades["max_hold_bars"].eq(48)
    ].copy()

    feature_notes: list[str] = []
    if not xau_features.empty:
        losing = xau_features[xau_features["r_after_cost"] <= 0]
        winning = xau_features[xau_features["r_after_cost"] > 0]
        for col, label in [
            ("risk_atr", "損切り幅ATR"),
            ("break_extension_atr", "B抜け時の伸びATR"),
            ("entry_range_atr", "エントリー足高安ATR"),
            ("a_room_r", "Aまでの余白R"),
            ("d1_prev60_room_atr", "D1過去60日高値までの距離ATR"),
        ]:
            feature_notes.append(
                f"- {label}: 勝ち中央値 {winning[col].median():.2f} / 負け中央値 {losing[col].median():.2f}"
            )

    lines = [
        "# LH3 B抜け即 危険除外フィルタ検証 v0.1",
        "",
        "作成日: 2026-06-08",
        "",
        "目的は、B抜け即エントリーを捨てずに、負けやすい形だけを除外できるかを調べること。",
        "前回のB床化検証では、B床化はH4で最大DDを下げる一方、総Rを大きく減らした。そこで今回は、B抜け即の中から危険条件を探す。",
        "",
        "## 比較した除外条件",
        "",
        "| filter | 意味 |",
        "|---|---|",
    ]
    for filter_id, filter_desc, _ in FILTERS:
        lines.append(f"| {filter_id} | {filter_desc} |")

    lines.extend(
        [
            "",
            "## 先に結論",
            "",
            "- XAUUSD H4では、B抜け即を完全に捨てるより、危険な形だけを除外するほうが自然。",
            "- 現時点の実用候補は `A_ROOM_GE_0_5R`。A水平線が上に残るなら、そこまで最低0.5Rの余白があるものだけをENTRY候補にする。",
            "- `D1_CLOSE_GT_EMA20` はPFが高いが件数が減るため、ENTRY条件ではなく「強い追い風」ラベル向き。",
            "- 巨大足、損切り幅、D1高値近接は、単体ではXAUUSD H4の勝ち負けをきれいに分けなかった。",
            "",
            "## XAUUSD H4の重要比較",
            "",
        ]
    )
    if xau_base_48 is not None:
        lines.append(f"- baseline RR2/48: {line_for(xau_base_48)}")
    if xau_best_48 is not None:
        lines.append(f"- RR2/48でPF最良候補: {line_for(xau_best_48)}")
    if xau_base_120 is not None:
        lines.append(f"- baseline RR2/120: {line_for(xau_base_120)}")
    if xau_best_120 is not None:
        lines.append(f"- RR2/120でPF最良候補: {line_for(xau_best_120)}")
    if all_base_120 is not None:
        lines.append("")
        lines.append(f"- ALL H4 baseline RR2/120: {line_for(all_base_120)}")
    if all_best_120 is not None:
        lines.append(f"- ALL H4 RR2/120でPF最良候補: {line_for(all_best_120)}")

    lines.extend(["", "## 実用候補", ""])
    if xau_aroom_48 is not None:
        lines.append(
            "- 実用候補 v1 は `A_ROOM_GE_0_5R`。"
            f"{line_for(xau_aroom_48)}。"
            " baselineより総Rは少し下がるが、勝率・PF・最大DDのバランスが一番よい。"
        )
    if xau_close_loc_48 is not None:
        lines.append(
            "- 軽い補助なら `CLOSE_LOC_GE_60`。"
            f"{line_for(xau_close_loc_48)}。"
            "件数をほぼ残しながら、PFとDDを少し改善する。"
        )
    if xau_d1_ema_48 is not None:
        lines.append(
            "- 高品質だが狭い条件は `D1_CLOSE_GT_EMA20`。"
            f"{line_for(xau_d1_ema_48)}。"
            "PFは最も高いが件数が32件まで減るため、本線ではなく強弱ラベル向き。"
        )
    if xau_d1_res_48 is not None:
        lines.append(
            "- `NO_D1_RESIST_1ATR` はXAUUSD H4では改善しない。"
            f"{line_for(xau_d1_res_48)}。"
            "今回の定義ではD1高値近接を単純に避けても良くならなかった。"
        )
    if xau_risk_48 is not None:
        lines.append(
            "- `RISK_LE_3ATR` は件数が少なすぎる。"
            f"{line_for(xau_risk_48)}。"
            "勝率は高く見えるが7件なので、採用判断には使わない。"
        )

    lines.extend(
        [
            "",
            "## 勝ち負けの特徴メモ（XAUUSD H4 RR2/48）",
            "",
            *feature_notes,
            "",
            "## 暫定判断",
            "",
            "- B抜け即の主役は、まだXAUUSD H4。",
            "- 次のTradingView表示では、`ENTRY`を出す条件に `A_ROOM_GE_0_5R` を足す案が最も自然。",
            "- `D1_CLOSE_GT_EMA20` はENTRY条件にすると件数が減りすぎるため、強い追い風ラベルとして表示する。",
            "- `CLOSE_LOC_GE_60` は軽い品質ラベルとして候補。終値が足の上側で終わっているかを見る。",
            "- 巨大足・損切り幅・D1高値近接は、単体では今回のXAUUSD H4をうまく分けなかった。",
            "- 件数が30件未満のXAUUSD H4フィルタは、現時点では参考値扱い。",
            "",
            "## 出力ファイル",
            "",
            "- [trades_with_features.csv](trades_with_features.csv)",
            "- [summary_by_filter.csv](summary_by_filter.csv)",
            "",
            "## 全サマリー",
            "",
            markdown_table(summary.round(2)),
            "",
            "## 再現",
            "",
            "```bash",
            "python3 backtests/elliott_fibo/run_lower_high_b_break_danger_filter_study.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    base_rows: list[dict] = []

    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        d1 = add_daily_context(add_indicators(resample_ohlc(raw, "D1")))
        for spec in SPECS:
            frame = add_indicators(resample_ohlc(raw, spec.timeframe))
            b_events = [e for e in detect_confirm_events(frame, symbol, spec) if e["variant"] == "B_BREAK"]
            for event in b_events:
                entry_i = int(event["entry_i"])
                h3_i = int(event["h3_i"])
                for rr in RR_TARGETS:
                    for max_hold in MAX_HOLD_BARS:
                        result = simulate_trade(frame, symbol, entry_i, h3_i, rr, max_hold)
                        if result is None:
                            continue
                        features = compute_features(frame, d1, event, result)
                        base_rows.append(
                            {
                                "symbol": symbol,
                                "timeframe": spec.timeframe,
                                "period": event["period"],
                                "entry_time": event["entry_time"],
                                "line_reclaim_time": event["line_reclaim_time"],
                                "h1_time": event["h1_time"],
                                "h2_time": event["h2_time"],
                                "h3_time": event["h3_time"],
                                "b_level": event["confirm_level"],
                                "h3_price": event["h3_price"],
                                "bars_after_line": event["bars_after_line"],
                                **result,
                                **features,
                            }
                        )

    base = pd.DataFrame(base_rows)
    scoped_rows: list[pd.DataFrame] = []
    if not base.empty:
        for filter_id, filter_desc, filter_fn in FILTERS:
            mask = filter_fn(base).fillna(False)
            scoped = add_scope_rows(base[mask].copy(), filter_id, filter_desc)
            if not scoped.empty:
                scoped_rows.append(scoped)

    trades = pd.concat(scoped_rows, ignore_index=True) if scoped_rows else pd.DataFrame()
    if not trades.empty:
        trades = trades.sort_values(["scope", "filter_id", "symbol", "timeframe", "entry_time", "rr", "max_hold_bars"])
    summary = (
        summarize_trades(trades, ["scope", "filter_id", "filter_desc", "rr", "max_hold_bars"])
        if not trades.empty
        else pd.DataFrame()
    )

    trades.to_csv(OUT_DIR / "trades_with_features.csv", index=False)
    summary.to_csv(OUT_DIR / "summary_by_filter.csv", index=False)
    (OUT_DIR / "REPORT_ja.md").write_text(build_report(summary, trades), encoding="utf-8")

    print(f"base trades: {len(base)}")
    print(f"scoped trades: {len(trades)}")
    print(f"wrote: {OUT_DIR}")
    if not summary.empty:
        focus = summary[
            summary["scope"].isin(["XAUUSD_H4", "ALL_H4"])
            & summary["rr"].eq(2.0)
            & summary["max_hold_bars"].isin([48, 120])
        ].copy()
        print(focus.to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Elliott wave-5 reproducibility study.

The point is not to draw a beautiful count after the fact. The point is to ask:
if an AI/code system must use Elliott wave, which objective definition can it
repeat, and does the wave-5 breakout actually extend better than similar
non-Elliott breakouts?
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    max_drawdown,
    max_losing_streak,
    profit_factor,
    resample_ohlc,
    timeframe_settings,
)


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "elliott_wave5_reproducibility_2026-06-09"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]
TIMEFRAMES = ["H1", "H4", "D1"]
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2026-06-08 23:59:59")
OOS_START = pd.Timestamp("2025-01-01")
FORWARD_BARS = [24, 48, 120]
RR_TARGETS = [1.0, 2.0, 3.0]
STOP_BUFFER_ATR = 0.25


def tf_delta(timeframe: str) -> pd.Timedelta:
    if timeframe == "D1":
        return pd.Timedelta(days=1)
    if timeframe == "H4":
        return pd.Timedelta(hours=4)
    return pd.Timedelta(hours=1)


def pivot_time(df: pd.DataFrame, pivot_i: int, timeframe: str) -> pd.Timestamp:
    return pd.Timestamp(df.index[pivot_i]) + tf_delta(timeframe)


def crossed(close: np.ndarray, level: float, i: int, direction: str, buffer: float) -> bool:
    if i <= 0:
        return False
    if direction == "long":
        return close[i - 1] <= level and close[i] > level + buffer
    return close[i - 1] >= level and close[i] < level - buffer


def wave_features(pivots: list, direction: str) -> dict | None:
    if len(pivots) < 5:
        return None
    p = pivots[-5:]
    kinds = "".join(x.kind for x in p)
    if direction == "long" and kinds != "LHLHL":
        return None
    if direction == "short" and kinds != "HLHLH":
        return None

    if direction == "long":
        l0, h1, l2, h3, l4 = p
        wave1 = h1.price - l0.price
        wave3 = h3.price - l2.price
        if wave1 <= 0 or wave3 <= 0:
            return None
        wave2_retrace = (h1.price - l2.price) / wave1
        wave4_retrace = (h3.price - l4.price) / wave3
        return {
            "direction": "long",
            "kind_sequence": kinds,
            "p0_i": l0.pivot_i,
            "p1_i": h1.pivot_i,
            "p2_i": l2.pivot_i,
            "p3_i": h3.pivot_i,
            "p4_i": l4.pivot_i,
            "p0_price": l0.price,
            "p1_price": h1.price,
            "p2_price": l2.price,
            "p3_price": h3.price,
            "p4_price": l4.price,
            "wave1": wave1,
            "wave3": wave3,
            "wave2_retrace": wave2_retrace,
            "wave4_retrace": wave4_retrace,
            "trigger_level": h3.price,
            "sl_anchor": l4.price,
            "structure_ok": h3.price > h1.price and l2.price > l0.price and l4.price > l2.price,
            "no_overlap": l4.price > h1.price,
        }

    h0, l1, h2, l3, h4 = p
    wave1 = h0.price - l1.price
    wave3 = h2.price - l3.price
    if wave1 <= 0 or wave3 <= 0:
        return None
    wave2_retrace = (h2.price - l1.price) / wave1
    wave4_retrace = (h4.price - l3.price) / wave3
    return {
        "direction": "short",
        "kind_sequence": kinds,
        "p0_i": h0.pivot_i,
        "p1_i": l1.pivot_i,
        "p2_i": h2.pivot_i,
        "p3_i": l3.pivot_i,
        "p4_i": h4.pivot_i,
        "p0_price": h0.price,
        "p1_price": l1.price,
        "p2_price": h2.price,
        "p3_price": l3.price,
        "p4_price": h4.price,
        "wave1": wave1,
        "wave3": wave3,
        "wave2_retrace": wave2_retrace,
        "wave4_retrace": wave4_retrace,
        "trigger_level": l3.price,
        "sl_anchor": h4.price,
        "structure_ok": l3.price < l1.price and h2.price < h0.price and h4.price < h2.price,
        "no_overlap": h4.price < l1.price,
    }


def classify_methods(features: dict, trend_ok: bool) -> list[str]:
    structure = bool(features["structure_ok"])
    retrace_ok = 0.236 <= features["wave2_retrace"] <= 0.786 and 0.236 <= features["wave4_retrace"] <= 0.618
    shallow_w4 = 0.236 <= features["wave4_retrace"] <= 0.50
    wave3_loose = features["wave3"] >= features["wave1"] * 0.8
    wave3_classic = features["wave3"] >= features["wave1"] * 1.0
    wave3_extended = features["wave3"] >= features["wave1"] * 1.272
    no_overlap = bool(features["no_overlap"])

    score = 0
    score += 2 if structure else 0
    score += 1 if retrace_ok else 0
    score += 1 if shallow_w4 else 0
    score += 1 if wave3_classic else 0
    score += 1 if wave3_extended else 0
    score += 1 if no_overlap else 0
    score += 1 if trend_ok else 0

    methods = ["ALL_PIVOT_BREAKOUT"]
    if structure and retrace_ok and wave3_loose:
        methods.append("W5_LOOSE")
    if structure and retrace_ok and wave3_classic:
        methods.append("W5_CLASSIC")
    if structure and retrace_ok and shallow_w4 and wave3_classic and no_overlap:
        methods.append("W5_STRICT_NO_OVERLAP")
    if score >= 5:
        methods.append("W5_AI_SCORE_5")
    if score >= 6:
        methods.append("W5_AI_SCORE_6")
    if methods == ["ALL_PIVOT_BREAKOUT"]:
        methods.append("CONTROL_NOT_W5")
    return methods


def simulate_forward(
    df: pd.DataFrame,
    timeframe: str,
    signal_i: int,
    direction: str,
    trigger_level: float,
    sl_anchor: float,
    wave1: float,
    wave3: float,
) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    atr_value = float(df["atr"].iloc[signal_i])
    if not math.isfinite(atr_value) or atr_value <= 0:
        return None

    if direction == "long":
        sl = sl_anchor - atr_value * STOP_BUFFER_ATR
        risk = entry - sl
        if risk <= 0:
            return None
    else:
        sl = sl_anchor + atr_value * STOP_BUFFER_ATR
        risk = sl - entry
        if risk <= 0:
            return None

    out: dict[str, float | int | str | pd.Timestamp] = {
        "signal_time": pd.Timestamp(df.index[signal_i]),
        "entry_time": pd.Timestamp(df.index[entry_i]),
        "entry_price": entry,
        "sl_price": sl,
        "risk_price": risk,
    }

    for bars in FORWARD_BARS:
        end_i = min(len(df), entry_i + bars)
        window = df.iloc[entry_i:end_i]
        if window.empty:
            out[f"mfe_{bars}"] = math.nan
            out[f"mae_{bars}"] = math.nan
            out[f"wave5_ext_wave1_{bars}"] = math.nan
            continue
        if direction == "long":
            max_high = float(window["high"].max())
            min_low = float(window["low"].min())
            out[f"mfe_{bars}"] = (max_high - entry) / risk
            out[f"mae_{bars}"] = (entry - min_low) / risk
            out[f"wave5_ext_wave1_{bars}"] = (max_high - sl_anchor) / wave1 if wave1 > 0 else math.nan
        else:
            max_high = float(window["high"].max())
            min_low = float(window["low"].min())
            out[f"mfe_{bars}"] = (entry - min_low) / risk
            out[f"mae_{bars}"] = (max_high - entry) / risk
            out[f"wave5_ext_wave1_{bars}"] = (sl_anchor - min_low) / wave1 if wave1 > 0 else math.nan

    for rr in RR_TARGETS:
        tp = entry + risk * rr if direction == "long" else entry - risk * rr
        hit = False
        for j in range(entry_i, min(len(df), entry_i + 120)):
            hi = float(df["high"].iloc[j])
            lo = float(df["low"].iloc[j])
            if direction == "long":
                hit_sl = lo <= sl
                hit_tp = hi >= tp
            else:
                hit_sl = hi >= sl
                hit_tp = lo <= tp
            if hit_sl:
                break
            if hit_tp:
                hit = True
                break
        out[f"tp{rr:g}_hit_120"] = int(hit)

    tp2 = entry + risk * 2.0 if direction == "long" else entry - risk * 2.0
    result_r = 0.0
    outcome = 0
    exit_reason = "not_reached_120"
    exit_i = min(len(df) - 1, entry_i + 120)
    exit_price = float(df["close"].iloc[exit_i])
    result_r = (exit_price - entry) / risk if direction == "long" else (entry - exit_price) / risk
    for j in range(entry_i, min(len(df), entry_i + 120)):
        hi = float(df["high"].iloc[j])
        lo = float(df["low"].iloc[j])
        if direction == "long":
            hit_sl = lo <= sl
            hit_tp = hi >= tp2
        else:
            hit_sl = hi >= sl
            hit_tp = lo <= tp2
        if hit_sl or hit_tp:
            exit_i = j
            if hit_sl:
                result_r = -1.0
                outcome = -1
                exit_reason = "SL_first_same_bar" if hit_tp else "SL"
                exit_price = sl
            else:
                result_r = 2.0
                outcome = 1
                exit_reason = "TP2"
                exit_price = tp2
            break

    out.update(
        {
            "exit_time": pd.Timestamp(df.index[exit_i]),
            "exit_price": exit_price,
            "outcome_2r": outcome,
            "r_result_2r": result_r,
            "exit_reason": exit_reason,
            "wave3_vs_wave1": wave3 / wave1 if wave1 > 0 else math.nan,
            "entry_over_wave3": abs(entry - trigger_level) / wave3 if wave3 > 0 else math.nan,
            "period": "OOS_2025_2026" if pd.Timestamp(df.index[signal_i]) >= OOS_START else "Research_2015_2024",
            "timeframe": timeframe,
        }
    )
    return out


def detect_events(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    settings = timeframe_settings(timeframe)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list = []
    pointer = 0
    rows: list[dict] = []
    used_keys: set[tuple] = set()

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)

    for i in range(2, len(df) - 1):
        while pointer < len(pivots) and pivots[pointer].confirm_i <= i:
            active.append(pivots[pointer])
            pointer += 1
        ts = pd.Timestamp(df.index[i])
        if ts < START or ts > END or holiday_market(ts):
            continue
        if len(active) < 5 or not math.isfinite(atr[i]) or atr[i] <= 0:
            continue

        for direction in ["long", "short"]:
            features = wave_features(active, direction)
            if features is None:
                continue
            buffer = float(atr[i]) * settings["break_buffer_atr"]
            if not crossed(close, float(features["trigger_level"]), i, direction, buffer):
                continue
            key = (direction, features["p0_i"], features["p1_i"], features["p2_i"], features["p3_i"], features["p4_i"])
            if key in used_keys:
                continue
            used_keys.add(key)

            if direction == "long":
                trend_ok = close[i] > float(df["close"].rolling(80).mean().iloc[i]) if i >= 80 else False
                pre_break_range_atr = (high[i] - low[int(features["p4_i"]) : i + 1].min()) / atr[i]
            else:
                trend_ok = close[i] < float(df["close"].rolling(80).mean().iloc[i]) if i >= 80 else False
                pre_break_range_atr = (high[int(features["p4_i"]) : i + 1].max() - low[i]) / atr[i]

            sim = simulate_forward(
                df,
                timeframe,
                i,
                direction,
                float(features["trigger_level"]),
                float(features["sl_anchor"]),
                float(features["wave1"]),
                float(features["wave3"]),
            )
            if sim is None:
                continue
            methods = classify_methods(features, trend_ok)
            base = {
                "symbol": symbol,
                "direction": direction,
                "kind_sequence": features["kind_sequence"],
                "p0_time": pivot_time(df, int(features["p0_i"]), timeframe),
                "p1_time": pivot_time(df, int(features["p1_i"]), timeframe),
                "p2_time": pivot_time(df, int(features["p2_i"]), timeframe),
                "p3_time": pivot_time(df, int(features["p3_i"]), timeframe),
                "p4_time": pivot_time(df, int(features["p4_i"]), timeframe),
                "p0_price": features["p0_price"],
                "p1_price": features["p1_price"],
                "p2_price": features["p2_price"],
                "p3_price": features["p3_price"],
                "p4_price": features["p4_price"],
                "wave1": features["wave1"],
                "wave3": features["wave3"],
                "wave2_retrace": features["wave2_retrace"],
                "wave4_retrace": features["wave4_retrace"],
                "structure_ok": int(bool(features["structure_ok"])),
                "no_overlap": int(bool(features["no_overlap"])),
                "trend_ok": int(bool(trend_ok)),
                "pre_break_range_atr": pre_break_range_atr,
                **sim,
            }
            for method in methods:
                rows.append({**base, "method": method})
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        r = group["r_result_2r"].astype(float)
        row = dict(zip(group_cols, keys))
        row.update(
            {
                "events": len(group),
                "win_rate_2r": float((group["outcome_2r"].astype(int) == 1).mean() * 100),
                "sl_rate": float((group["outcome_2r"].astype(int) == -1).mean() * 100),
                "avg_r_2r": float(r.mean()),
                "total_r_2r": float(r.sum()),
                "pf_2r": profit_factor(r),
                "max_dd_r": max_drawdown(r),
                "max_losing_streak": max_losing_streak(r),
                "avg_mfe_24": float(group["mfe_24"].mean()),
                "avg_mfe_48": float(group["mfe_48"].mean()),
                "avg_mfe_120": float(group["mfe_120"].mean()),
                "avg_mae_24": float(group["mae_24"].mean()),
                "avg_mae_48": float(group["mae_48"].mean()),
                "avg_mae_120": float(group["mae_120"].mean()),
                "tp1_rate_120": float(group["tp1_hit_120"].mean() * 100),
                "tp2_rate_120": float(group["tp2_hit_120"].mean() * 100),
                "tp3_rate_120": float(group["tp3_hit_120"].mean() * 100),
                "avg_wave5_ext_wave1_120": float(group["wave5_ext_wave1_120"].mean()),
                "median_wave5_ext_wave1_120": float(group["wave5_ext_wave1_120"].median()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["period"] + group_cols + ["total_r_2r"], ascending=[True] * (len(group_cols) + 1) + [False])


def compact_summary(summary: pd.DataFrame, period: str = "Research_2015_2024") -> pd.DataFrame:
    cols = [
        "method",
        "events",
        "win_rate_2r",
        "pf_2r",
        "avg_r_2r",
        "total_r_2r",
        "max_dd_r",
        "avg_mfe_120",
        "avg_mae_120",
        "tp2_rate_120",
        "avg_wave5_ext_wave1_120",
    ]
    if summary.empty:
        return summary
    out = summary[summary["period"].eq(period)]
    return out[cols].sort_values(["pf_2r", "avg_r_2r"], ascending=[False, False])


def verdict(summary: pd.DataFrame) -> tuple[str, str]:
    research = summary[summary["period"].eq("Research_2015_2024")].set_index("method")
    oos = summary[summary["period"].eq("OOS_2025_2026")].set_index("method")
    if "W5_CLASSIC" not in research.index or "CONTROL_NOT_W5" not in research.index:
        return "判定不能", "W5_CLASSICまたはCONTROL_NOT_W5が不足。"
    w5 = research.loc["W5_CLASSIC"]
    ctrl = research.loc["CONTROL_NOT_W5"]
    mfe_ok = float(w5["avg_mfe_120"]) > float(ctrl["avg_mfe_120"])
    win_ok = float(w5["win_rate_2r"]) > float(ctrl["win_rate_2r"])
    pf_ok = float(w5["pf_2r"]) > float(ctrl["pf_2r"])
    research_ok = mfe_ok and win_ok and pf_ok

    oos_ok = False
    if "W5_CLASSIC" in oos.index and "CONTROL_NOT_W5" in oos.index:
        oos_w5 = oos.loc["W5_CLASSIC"]
        oos_ctrl = oos.loc["CONTROL_NOT_W5"]
        oos_ok = (
            float(oos_w5["pf_2r"]) > 1.0
            and float(oos_w5["avg_r_2r"]) > 0
            and float(oos_w5["win_rate_2r"]) > float(oos_ctrl["win_rate_2r"])
        )

    if research_ok and oos_ok:
        return "支持", "Classic W5は研究期間とOOSの両方で、対照群より伸び・2R到達率・PFが良い。"
    if research_ok:
        return "部分支持", "Classic W5は研究期間では対照群より良いが、OOSでは崩れている。5波候補ラベルとしては有望、単独売買ルール化は未支持。"
    if mfe_ok and win_ok:
        return "部分支持", "Classic W5は伸びと到達率は良いが、PFまでは安定していない。"
    if mfe_ok:
        return "弱い部分支持", "Classic W5は伸びやすいが、売買成績としては弱い。"
    return "棄却", "Classic W5は対照群より明確に伸びるとは言えない。"


def build_report(events: pd.DataFrame, summary_method: pd.DataFrame, by_tf: pd.DataFrame, by_symbol: pd.DataFrame) -> str:
    judge, judge_note = verdict(summary_method)
    research_compact = compact_summary(summary_method, "Research_2015_2024")
    oos_compact = compact_summary(summary_method, "OOS_2025_2026")
    classic_symbol = by_symbol[(by_symbol["period"].eq("Research_2015_2024")) & (by_symbol["method"].eq("W5_CLASSIC"))]
    classic_tf = by_tf[(by_tf["period"].eq("Research_2015_2024")) & (by_tf["method"].eq("W5_CLASSIC"))]

    lines = [
        "# Elliott 5波狙い 再現性検証 v0.1",
        "",
        f"作成日: 2026-06-09",
        "",
        "## 研究の問い",
        "",
        "人間の目で数えたエリオット波動ではなく、AI/コードが同じ条件で検出できる5波候補は、普通のブレイクより本当に伸びやすいのか。",
        "",
        f"## 判定: {judge}",
        "",
        judge_note,
        "",
        "## AIがエリオット波動を使うなら",
        "",
        "| 方法 | 使い方 | 問題 |",
        "|---|---|---|",
        "| 1. Pivot/ZigZagルール | 確定pivotの L-H-L-H-L / H-L-H-L-H を数える | pivot幅とATR閾値で結果が変わる |",
        "| 2. 比率スコア | 2波/4波の戻し、3波の強さ、4波の浅さを点数化 | 後付け最適化しやすい |",
        "| 3. 画像AI | チャート画像から波を読む | 目視に近いが再現性・検証性が弱い |",
        "| 4. ラベル学習 | 過去の成功5波を教師データにする | まず正しいラベル作成が必要 |",
        "",
        "今回のv0.1では、再現性を優先して 1 と 2 だけを使った。",
        "",
        "## 操作定義",
        "",
        "- ALL_PIVOT_BREAKOUT: 5つの交互pivot後、3波高値/安値を終値で突破した全候補",
        "- CONTROL_NOT_W5: 上記のうち、エリオット条件を満たさない対照群",
        "- W5_LOOSE: 構造 + 2波/4波戻し + 3波 >= 0.8 x 1波",
        "- W5_CLASSIC: 構造 + 2波/4波戻し + 3波 >= 1.0 x 1波",
        "- W5_STRICT_NO_OVERLAP: Classic + 4波浅め + 4波が1波領域に重ならない",
        "- W5_AI_SCORE_5/6: 構造、戻し、3波、4波、トレンドを点数化したAI proxy",
        "",
        "## 全体比較 2015-2024",
        "",
        markdown_table(research_compact, 20),
        "",
        "## OOS 2025-2026",
        "",
        markdown_table(oos_compact, 20),
        "",
        "## Classic W5 時間足別",
        "",
        markdown_table(classic_tf, 20),
        "",
        "## Classic W5 銘柄別",
        "",
        markdown_table(classic_symbol, 80),
        "",
        "## 考察",
        "",
        "- エリオット5波は、機械化すると「どこをpivotにするか」が最重要になる。",
        "- Classic W5がControlより良ければ、5波そのものに意味がある可能性がある。",
        "- ただしOOSで崩れる場合、伸びやすさの仮説と売買ルールとしての採用は分ける。",
        "- Strict No Overlapは人間の教科書には近いが、FX/CFDでは候補が少なくなりやすい。",
        "- 5波狙いを本番化するなら、まずは売買ではなくEvent scannerで、波カウントと3波高値/安値ブレイクを可視化するのが安全。",
        "",
        "## 実運用への落とし込み",
        "",
        "現段階では、エリオット波動を単独の売買ルールにしない。使うなら「5波候補」ラベルとして、既存のT5/B06/LH3の方向確認や利確期待の補助にする。",
        "",
        "## 次のアクション",
        "",
        "1. W5_CLASSIC と CONTROL_NOT_W5 の代表20件をTradingViewで目視照合する。",
        "2. pivot幅/ATR閾値の感度分析を行い、結果が崩れないかを見る。",
        "3. 支持が残る場合のみ、Pine Event scannerを作る。",
        "",
        "## 出力",
        "",
        "- events_all.csv",
        "- summary_by_method.csv",
        "- summary_by_timeframe.csv",
        "- summary_by_symbol.csv",
        "- REPORT_ja.md",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    all_events: list[pd.DataFrame] = []
    coverage = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        raw = raw[(raw.index >= START - pd.Timedelta(days=400)) & (raw.index <= END)]
        coverage.append({"symbol": symbol, "h1_bars": len(raw), "first": raw.index.min(), "last": raw.index.max()})
        for timeframe in TIMEFRAMES:
            df = add_indicators(resample_ohlc(raw, timeframe))
            events = detect_events(df, symbol, timeframe)
            if not events.empty:
                all_events.append(events)

    if not all_events:
        raise RuntimeError("No Elliott W5 events detected.")

    events = pd.concat(all_events, ignore_index=True)
    summary_method = summarize(events, ["period", "method"])
    summary_tf = summarize(events, ["period", "timeframe", "method"])
    summary_symbol = summarize(events, ["period", "symbol", "method"])
    summary_direction = summarize(events, ["period", "direction", "method"])
    coverage_df = pd.DataFrame(coverage)

    date_cols = ["signal_time", "entry_time", "exit_time", "p0_time", "p1_time", "p2_time", "p3_time", "p4_time"]
    for col in date_cols:
        events[col] = pd.to_datetime(events[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")

    events.to_csv(OUT_DIR / "events_all.csv", index=False)
    summary_method.to_csv(OUT_DIR / "summary_by_method.csv", index=False)
    summary_tf.to_csv(OUT_DIR / "summary_by_timeframe.csv", index=False)
    summary_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    summary_direction.to_csv(OUT_DIR / "summary_by_direction.csv", index=False)
    coverage_df.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    report = build_report(events, summary_method, summary_tf, summary_symbol)
    (OUT_DIR / "REPORT_ja.md").write_text(report, encoding="utf-8")

    print(f"events={len(events)} unique_breakouts={events.drop_duplicates(['symbol','timeframe','signal_time','direction']).shape[0]}")
    print(compact_summary(summary_method, "Research_2015_2024").round(3).to_string(index=False))
    print(f"wrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

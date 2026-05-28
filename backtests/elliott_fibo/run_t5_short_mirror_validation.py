#!/usr/bin/env python3
"""
Mirror-short validation for the H4 V-candidate T5 + MACD + BB idea.

Long production logic uses a sharp drop as context, then waits for a
stagnation breakout or rebreak.  This script tests the true short mirror:

- Context: confirmed pivot Low -> pivot High sharp rally.
- Candidate: close falls 61.8% to 80.0% of that rally.
- Trigger: low stagnation breakdown, or bounce then recovery-low rebreak.
- Filters: MACD histogram falling, BB position in the lower mirror zone.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import (
    SYMBOLS,
    Pivot,
    add_indicators,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    simulate_trade,
    timeframe_settings,
)
from run_indicator_compatibility_search import add_extended_features, enrich_trades
from run_v_recovery_trigger_study import TriggerSpec, trigger_settings


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_28" / "t5_short_mirror_validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
PERIODS = [
    ("Research_2015_2024", pd.Timestamp("2015-01-01"), pd.Timestamp("2024-12-31 23:59:59")),
    ("OOS_2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31 23:59:59")),
]

BASE_SPEC = TriggerSpec(
    "SHORT_REC1.20_T5_STAG_OR_REBREAK_BROAD",
    trigger_mode="either",
    max_recovery_to_drop=1.20,
)


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    curve = r.astype(float).cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(r: pd.Series) -> int:
    cur = 0
    best = 0
    for value in r.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def metrics(df: pd.DataFrame, r_col: str = "r_after_cost") -> dict[str, float | int]:
    r = df[r_col].astype(float) if not df.empty and r_col in df.columns else pd.Series(dtype=float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def classify_period(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts.year <= 2024 else "OOS_2025_2026"


def summary_row(name: str, df: pd.DataFrame, notes: str = "", r_col: str = "r_after_cost") -> dict:
    research = df[df["period"].eq("Research_2015_2024")] if not df.empty else df
    oos = df[df["period"].eq("OOS_2025_2026")] if not df.empty else df
    out = {"case": name, "notes": notes}
    out.update({f"all_{k}": v for k, v in metrics(df, r_col).items()})
    out.update({f"research_{k}": v for k, v in metrics(research, r_col).items()})
    out.update({f"oos_{k}": v for k, v in metrics(oos, r_col).items()})
    return out


def summarize_cases(cases: list[tuple[str, pd.DataFrame, str]]) -> pd.DataFrame:
    return pd.DataFrame([summary_row(name, sample, notes) for name, sample, notes in cases])


def _candidate_first_index_short(
    df: pd.DataFrame,
    start_i: int,
    end_i: int,
    high_price: float,
    rally: float,
    fib_min: float,
    fib_max: float,
) -> int | None:
    if end_i < start_i:
        return None
    closes = df["close"].to_numpy()
    for idx in range(start_i, end_i + 1):
        ratio = (high_price - float(closes[idx])) / rally
        if fib_min <= ratio <= fib_max:
            return idx
        if ratio > fib_max:
            return None
    return None


def short_context_trigger_signal(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: TriggerSpec,
    settings: dict,
) -> dict | None:
    if len(active) < 2:
        return None

    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None

    tf_trig = trigger_settings(settings["timeframe"])
    stag_bars = int(tf_trig["stag_bars"])
    min_wait_bars = int(tf_trig["min_wait_bars"])
    max_after = spec.max_bars_after_candidate or int(tf_trig["max_after"])
    buffer = atr_i * settings["break_buffer_atr"]

    pairs_scanned = 0
    idx = len(active) - 2
    while idx >= 0 and pairs_scanned < 10:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        pairs_scanned += 1
        if p0.kind != "L" or p1.kind != "H":
            continue
        if i <= p1.pivot_i + min_wait_bars:
            continue

        rally = p1.price - p0.price
        if rally <= 0 or rally < atr_i * spec.min_move_atr:
            continue

        rally_bars = max(p1.pivot_i - p0.pivot_i, 1)
        rally_speed = rally / rally_bars / atr_i
        if rally_speed < spec.min_drop_speed:
            continue

        post_high = float(df["high"].iloc[p1.pivot_i + 1 : i + 1].max())
        if post_high > p1.price + atr_i * 0.10:
            continue

        candidate_i = _candidate_first_index_short(
            df,
            p1.pivot_i + 1,
            i - min_wait_bars,
            p1.price,
            rally,
            spec.fib_min,
            spec.fib_max,
        )
        if candidate_i is None:
            continue

        if i - candidate_i > max_after:
            continue

        recovery_bars = max(candidate_i - p1.pivot_i, 1)
        recovery_to_rally = recovery_bars / rally_bars
        if recovery_to_rally > spec.max_recovery_to_drop:
            continue

        fib_min_level = p1.price - rally * spec.fib_min
        stop = p1.price + atr_i * 0.25
        target = close - (stop - close) * spec.rr
        if target >= close or stop <= close:
            continue

        stagnation_ok = False
        if i - candidate_i >= stag_bars + 1:
            win = df.iloc[i - stag_bars : i]
            win_high = float(win["high"].max())
            win_low = float(win["low"].min())
            win_range = win_high - win_low
            held_zone = win_high <= fib_min_level + atr_i * 0.50
            tight_enough = win_range <= atr_i * spec.stag_range_atr
            broke_tight_low = close < win_low - buffer
            stagnation_ok = held_zone and tight_enough and broke_tight_low

        rebreak_ok = False
        pre = df.iloc[candidate_i:i]
        if len(pre) >= 3:
            lows = pre["low"].to_numpy(dtype=float)
            low_pos = int(pd.Series(lows).idxmin())
            low_i = candidate_i + low_pos
            recovery_low = float(lows[low_pos])
            if low_i <= i - 2:
                pullback_high = float(df["high"].iloc[low_i + 1 : i].max())
                had_pullback = pullback_high >= recovery_low + atr_i * spec.pullback_atr
                rebreak_ok = had_pullback and close < recovery_low - buffer

        if spec.trigger_mode == "stagnation" and not stagnation_ok:
            continue
        if spec.trigger_mode == "rebreak" and not rebreak_ok:
            continue
        if spec.trigger_mode == "either" and not (stagnation_ok or rebreak_ok):
            continue

        trigger_type = "stagnation" if stagnation_ok else "rebreak"
        if stagnation_ok and rebreak_ok:
            trigger_type = "stagnation+rebreak"

        decline_at_signal = p1.price - close
        return {
            "direction": "short",
            "trigger_type": trigger_type,
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "candidate_i": candidate_i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "v_move_atr": rally / atr_i,
            "v_move_bars": rally_bars,
            "v_drop_speed_atr_per_bar": rally_speed,
            "candidate_recovery_bars": recovery_bars,
            "candidate_recovery_to_drop_bars": recovery_to_rally,
            "signal_recovery_bars": i - p1.pivot_i,
            "signal_fib_ratio": decline_at_signal / rally,
            "candidate_fib_min": spec.fib_min,
            "candidate_fib_max": spec.fib_max,
            "trigger_level": close,
            "stop": stop,
            "target": target,
            "candidate_key": f"{p0.pivot_i}-{p1.pivot_i}",
        }

    return None


def run_short_spec_for_period(
    df: pd.DataFrame,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    spec: TriggerSpec,
) -> pd.DataFrame:
    settings = timeframe_settings(TIMEFRAME)
    settings["timeframe"] = TIMEFRAME
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    used_candidates: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < start or ts > end or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        sig = short_context_trigger_signal(df, i, active, spec, settings)
        if sig is None or sig["candidate_key"] in used_candidates:
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=sig["direction"],
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
            invalidation_level=None,
            early_exit_bars=0,
        )
        if trade is None:
            continue

        used_candidates.add(sig["candidate_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": spec.name,
                "family": "逆V候補後トリガー",
                "signal_time": ts,
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "candidate_key"}},
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def short_candidate_only_signal(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: TriggerSpec,
) -> dict | None:
    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    close = float(df["close"].iloc[i])
    prev_close = float(df["close"].iloc[i - 1])
    if float(df["body_ratio"].iloc[i]) < spec.body_min:
        return None

    for p0, p1 in zip(reversed(active[:-1]), reversed(active[1:])):
        if p0.kind != "L" or p1.kind != "H":
            continue
        if i <= p1.pivot_i:
            continue
        rally = p1.price - p0.price
        if rally <= 0 or rally < atr_i * spec.min_move_atr:
            continue
        rally_bars = max(p1.pivot_i - p0.pivot_i, 1)
        rally_speed = rally / rally_bars / atr_i
        if rally_speed < spec.min_drop_speed:
            continue
        post_high = float(df["high"].iloc[p1.pivot_i + 1 : i + 1].max())
        if post_high > p1.price + atr_i * 0.10:
            continue
        ratio = (p1.price - close) / rally
        prev_ratio = (p1.price - prev_close) / rally
        if not (prev_ratio < spec.fib_min <= ratio <= spec.fib_max):
            continue
        recovery_bars = max(i - p1.pivot_i, 1)
        recovery_to_rally = recovery_bars / rally_bars
        if recovery_to_rally > spec.max_recovery_to_drop:
            continue
        stop = p1.price + atr_i * 0.25
        target = close - (stop - close) * spec.rr
        if target >= close or stop <= close:
            continue
        return {
            "direction": "short",
            "trigger_type": "inverse_v_candidate_only",
            "v_start_i": p0.pivot_i,
            "v_extreme_i": p1.pivot_i,
            "candidate_i": i,
            "v_start": p0.price,
            "v_extreme": p1.price,
            "v_move_atr": rally / atr_i,
            "v_move_bars": rally_bars,
            "v_drop_speed_atr_per_bar": rally_speed,
            "candidate_recovery_bars": recovery_bars,
            "candidate_recovery_to_drop_bars": recovery_to_rally,
            "signal_recovery_bars": recovery_bars,
            "signal_fib_ratio": ratio,
            "candidate_fib_min": spec.fib_min,
            "candidate_fib_max": spec.fib_max,
            "trigger_level": close,
            "stop": stop,
            "target": target,
            "candidate_key": f"{p0.pivot_i}-{p1.pivot_i}",
        }
    return None


def run_short_candidate_only_for_period(
    df: pd.DataFrame,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    spec: TriggerSpec,
) -> pd.DataFrame:
    settings = timeframe_settings(TIMEFRAME)
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    in_pos_until = -1
    used_candidates: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < start or ts > end or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue
        sig = short_candidate_only_signal(df, i, active, spec)
        if sig is None or sig["candidate_key"] in used_candidates:
            continue
        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction=sig["direction"],
            signal_i=i,
            stop=float(sig["stop"]),
            target=float(sig["target"]),
            max_hold_bars=settings["max_hold_bars"],
        )
        if trade is None:
            continue
        used_candidates.add(sig["candidate_key"])
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "strategy": "SHORT_REC1.20_INVERSE_V_CANDIDATE_ONLY",
                "family": "逆V候補のみ",
                "signal_time": ts,
                **{k: v for k, v in sig.items() if k not in {"stop", "target", "candidate_key"}},
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def run_all(
    feature_frames: dict[tuple[str, str], pd.DataFrame],
    candidate_only: bool = False,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for period, start, end in PERIODS:
        for symbol in SYMBOLS:
            df = feature_frames[(symbol, TIMEFRAME)]
            if candidate_only:
                trades = run_short_candidate_only_for_period(df, symbol, start, end, BASE_SPEC)
            else:
                trades = run_short_spec_for_period(df, symbol, start, end, BASE_SPEC)
            if not trades.empty:
                trades["period"] = period
                frames.append(trades)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    enriched = enrich_trades(raw, feature_frames)
    for col in ["signal_time", "entry_time", "exit_time"]:
        enriched[col] = pd.to_datetime(enriched[col])
    enriched["period"] = enriched["entry_time"].map(classify_period)
    enriched["month"] = enriched["entry_time"].dt.to_period("M").astype(str)
    enriched["year"] = enriched["entry_time"].dt.year.astype(str)
    return enriched.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def not_single_weak_rebreak_short(df: pd.DataFrame, macd_weak: float = -0.03, bb_low: float = 0.05) -> pd.Series:
    single_rebreak = df["trigger_type"].eq("rebreak")
    weak = df["bb_pos"].lt(bb_low) | df["macd_hist_slope3"].ge(macd_weak)
    return ~(single_rebreak & weak)


def short_practical_mask(
    df: pd.DataFrame,
    bb_low: float = 0.05,
    bb_high: float = 0.40,
    recovery_max: int = 16,
    macd_max: float = 0.0,
    bb_width_max: float | None = None,
    use_rebreak_guard: bool = True,
) -> pd.Series:
    mask = (
        df["bb_pos"].ge(bb_low)
        & df["bb_pos"].le(bb_high)
        & df["signal_recovery_bars"].le(recovery_max)
        & df["macd_hist_slope3"].lt(macd_max)
    )
    if bb_width_max is not None:
        mask &= df["bb_width_atr"].le(bb_width_max)
    if use_rebreak_guard:
        mask &= not_single_weak_rebreak_short(df, bb_low=bb_low)
    return mask.fillna(False)


def build_summary(trades: pd.DataFrame, candidate_only: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    practical7 = short_practical_mask(trades, bb_width_max=7.0)
    strict4 = short_practical_mask(trades, bb_width_max=4.0)
    super_strict = short_practical_mask(trades, macd_max=-0.03, bb_width_max=4.0)
    no_guard = short_practical_mask(trades, bb_width_max=7.0, use_rebreak_guard=False)
    cases = [
        ("A inverse V candidate only", candidate_only, "急騰後61.8-80%下落候補で即ショート"),
        ("B short T5 broad", trades, "逆V候補後にstagnation/rebreak。追加フィルタなし"),
        ("C mirror practical width<=7", trades[practical7], "BB 0.05-0.40, recovery<=16, MACD<0, BB幅<=7ATR, 弱い単独rebreak除外"),
        ("D mirror strict width<=4", trades[strict4], "実戦用よりBB幅を4ATRまで厳格化"),
        ("E mirror super strict", trades[super_strict], "BB幅<=4ATR + MACD slope3<-0.03"),
        ("F practical no rebreak guard", trades[no_guard], "Cから弱い単独rebreak除外だけ外す"),
    ]
    summary = summarize_cases(cases)

    symbol_rows = []
    for symbol, group in trades[practical7].groupby("symbol"):
        row = {"symbol": symbol}
        row.update(metrics(group))
        row.update({f"oos_{k}": v for k, v in metrics(group[group["period"].eq("OOS_2025_2026")]).items()})
        symbol_rows.append(row)
    by_symbol = pd.DataFrame(symbol_rows).sort_values("total_r", ascending=False) if symbol_rows else pd.DataFrame()

    trigger_rows = []
    for trig, group in trades[practical7].groupby("trigger_type"):
        row = {"trigger_type": trig}
        row.update(metrics(group))
        trigger_rows.append(row)
    by_trigger = pd.DataFrame(trigger_rows).sort_values("total_r", ascending=False) if trigger_rows else pd.DataFrame()

    sweep_rows = []
    for low, high in [(0.00, 0.25), (0.00, 0.35), (0.05, 0.40), (0.10, 0.45), (0.00, 0.50)]:
        mask = short_practical_mask(trades, bb_low=low, bb_high=high, bb_width_max=7.0)
        sweep_rows.append(summary_row(f"BB {low:.2f}-{high:.2f}", trades[mask], "recovery<=16, MACD<0, BB幅<=7ATR"))
    for width in [4.0, 5.0, 7.0]:
        mask = short_practical_mask(trades, bb_width_max=width)
        sweep_rows.append(summary_row(f"BB幅<={width:.0f}ATR", trades[mask], "BB 0.05-0.40, recovery<=16, MACD<0"))
    for macd in [0.00, -0.01, -0.03, -0.05]:
        mask = short_practical_mask(trades, macd_max=macd, bb_width_max=7.0)
        sweep_rows.append(summary_row(f"MACD slope3<{macd:.2f}", trades[mask], "BB 0.05-0.40, recovery<=16, BB幅<=7ATR"))
    sweep = pd.DataFrame(sweep_rows)
    return summary, by_symbol, by_trigger, sweep


def write_report(
    coverage: pd.DataFrame,
    trades: pd.DataFrame,
    candidate_only: pd.DataFrame,
    summary: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_trigger: pd.DataFrame,
    sweep: pd.DataFrame,
) -> None:
    compact = [
        "case",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "research_trades",
        "research_total_r",
        "oos_trades",
        "oos_total_r",
        "notes",
    ]
    lines = [
        "# H4 T5 + MACD + BB ショート反転検証",
        "",
        "## 検証定義",
        "",
        "- ロング版の反転として、急騰後に上昇幅の61.8%〜80%まで下落した逆V候補を抽出。",
        "- 逆V候補だけでは入らず、安値停滞下抜けまたは戻り安値再ブレイクでエントリー。",
        "- 実戦用ミラー条件は `BB位置0.05〜0.40`, `signal_recovery_bars<=16`, `MACD slope3<0`, `BB幅<=7ATR`, 弱い単独rebreak除外。",
        "- Rは次足始値エントリー、SL/TP到達、コスト込み `r_after_cost`。",
        "",
        "## データ範囲",
        "",
        markdown_table(coverage, 20),
        "",
        "## サマリー",
        "",
        markdown_table(summary[compact], 40),
        "",
        "## 実戦用ミラー 通貨別",
        "",
        markdown_table(by_symbol, 80) if not by_symbol.empty else "_No rows._",
        "",
        "## 実戦用ミラー トリガー別",
        "",
        markdown_table(by_trigger, 40) if not by_trigger.empty else "_No rows._",
        "",
        "## 閾値感度",
        "",
        markdown_table(sweep[compact], 80),
        "",
        "## 出力CSV",
        "",
        "- `short_t5_broad_trades_2015_2026.csv`",
        "- `short_inverse_v_candidate_only_trades_2015_2026.csv`",
        "- `summary.csv`",
        "- `by_symbol_practical.csv`",
        "- `by_trigger_practical.csv`",
        "- `sweep_thresholds.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    feature_frames: dict[tuple[str, str], pd.DataFrame] = {}
    coverage_rows = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "first": raw.index.min(), "last": raw.index.max(), "rows_h1": len(raw)})
        feature_frames[(symbol, TIMEFRAME)] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(OUT_DIR / "data_coverage.csv", index=False)

    trades = run_all(feature_frames, candidate_only=False)
    candidate_only = run_all(feature_frames, candidate_only=True)
    trades.to_csv(OUT_DIR / "short_t5_broad_trades_2015_2026.csv", index=False)
    candidate_only.to_csv(OUT_DIR / "short_inverse_v_candidate_only_trades_2015_2026.csv", index=False)

    summary, by_symbol, by_trigger, sweep = build_summary(trades, candidate_only)
    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "by_symbol_practical.csv", index=False)
    by_trigger.to_csv(OUT_DIR / "by_trigger_practical.csv", index=False)
    sweep.to_csv(OUT_DIR / "sweep_thresholds.csv", index=False)
    write_report(coverage, trades, candidate_only, summary, by_symbol, by_trigger, sweep)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary[["case", "all_trades", "all_win_rate", "all_total_r", "all_avg_r", "all_pf", "all_max_dd_r", "oos_trades", "oos_total_r"]].to_string(index=False))


if __name__ == "__main__":
    main()

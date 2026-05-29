#!/usr/bin/env python3
"""
Study: D1 bearish-denial context + H4 right-shoulder V reclaim.

Core hypothesis:
- D1 bearish signals that are quickly denied create a long-side context.
- Inside that context, buy only when H4 forms a sharp-drop V whose right
  shoulder is faster than the left shoulder and reclaims the left-shoulder
  starting point.

This is an integrated backtest, not a post-filter of old trades. If a V signal
appears without the D1 context, it is skipped and does not block later trades.
The D1 signal is activated from the next D1 bar to avoid lookahead on H4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    Pivot,
    build_confirmed_pivots,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
    simulate_trade,
    summarize,
    timeframe_settings,
)
from run_indicator_denial_reaction_study import (
    DenialSpec,
    add_denial_indicators,
    is_denial,
    pending_signals,
    quality_ok,
)
from run_v_right_shoulder_strength_study import (
    RightShoulderSpec,
    add_regime_indicators,
    period_name,
    right_shoulder_signal,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_29" / "d1_bear_trap_h4_v_reclaim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")


DENIAL_SPECS: list[DenialSpec] = [
    DenialSpec("DONCHIAN20_FALSE_BREAK_6_Q", "Donchian20下抜け否定", 6, quality=True, donchian_len=20),
    DenialSpec("DONCHIAN55_FALSE_BREAK_6_Q", "Donchian55下抜け否定", 6, quality=True, donchian_len=55),
    DenialSpec("RSI_70_30_REJECT_6_Q", "RSI30割れ否定", 6, quality=True),
]

V_SPECS: list[RightShoulderSpec] = [
    RightShoulderSpec(
        "RS120_BODY45_CLOSE60_RR15",
        "右肩速度>=左肩x1.2 + 実体45%以上 + 終値位置60%以上 + 左肩起点超え",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS100_BODY45_CLOSE60_RR15",
        "右肩速度>=左肩x1.0 + 実体45%以上 + 終値位置60%以上 + 左肩起点超え",
        min_speed_ratio=1.0,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS120_RECLAIM_RR15",
        "右肩速度>=左肩x1.2 + 左肩起点超え",
        min_speed_ratio=1.2,
        rr=1.5,
    ),
    RightShoulderSpec(
        "RS120_UPREG_BODY45_CLOSE60_RR15",
        "RS120_BODY45_CLOSE60 + EMA上向き環境",
        min_speed_ratio=1.2,
        body_min=0.45,
        close_location_min=0.60,
        rr=1.5,
        require_up_regime=True,
    ),
]


@dataclass(frozen=True)
class ContextSpec:
    name: str
    denial_names: tuple[str, ...]
    active_days: int
    mode: str = "require"


CONTEXT_SPECS: list[ContextSpec | None] = [
    None,
    ContextSpec("D20Q_5D", ("DONCHIAN20_FALSE_BREAK_6_Q",), 5),
    ContextSpec("D20Q_10D", ("DONCHIAN20_FALSE_BREAK_6_Q",), 10),
    ContextSpec("D20Q_15D", ("DONCHIAN20_FALSE_BREAK_6_Q",), 15),
    ContextSpec("D20Q_20D", ("DONCHIAN20_FALSE_BREAK_6_Q",), 20),
    ContextSpec("RSIQ_5D", ("RSI_70_30_REJECT_6_Q",), 5),
    ContextSpec("RSIQ_10D", ("RSI_70_30_REJECT_6_Q",), 10),
    ContextSpec("RSIQ_15D", ("RSI_70_30_REJECT_6_Q",), 15),
    ContextSpec("D20_OR_RSI_5D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 5),
    ContextSpec("D20_OR_RSI_10D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 10),
    ContextSpec("D20_OR_RSI_15D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 15),
    ContextSpec(
        "D20_D55_OR_RSI_10D",
        ("DONCHIAN20_FALSE_BREAK_6_Q", "DONCHIAN55_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"),
        10,
    ),
    ContextSpec(
        "D20_D55_OR_RSI_15D",
        ("DONCHIAN20_FALSE_BREAK_6_Q", "DONCHIAN55_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"),
        15,
    ),
    ContextSpec("AVOID_D20_OR_RSI_5D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 5, mode="avoid"),
    ContextSpec("AVOID_D20_OR_RSI_10D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 10, mode="avoid"),
    ContextSpec("AVOID_D20_OR_RSI_15D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 15, mode="avoid"),
    ContextSpec("AVOID_D20_OR_RSI_20D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 20, mode="avoid"),
    ContextSpec("AVOID_D20_OR_RSI_30D", ("DONCHIAN20_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"), 30, mode="avoid"),
    ContextSpec(
        "AVOID_D20_D55_OR_RSI_20D",
        ("DONCHIAN20_FALSE_BREAK_6_Q", "DONCHIAN55_FALSE_BREAK_6_Q", "RSI_70_30_REJECT_6_Q"),
        20,
        mode="avoid",
    ),
]


def detect_d1_bearish_denials(df: pd.DataFrame, symbol: str, spec: DenialSpec) -> pd.DataFrame:
    """Detect D1 bearish signals that failed and therefore create long context.

    This detector intentionally does not simulate D1 trades or suppress events
    while a prior D1 context is active. It is meant to measure environment, not
    standalone D1 entries.
    """

    rows: list[dict] = []
    pending_bear_i: int | None = None
    pending_bear_level: float | None = None

    for i in range(2, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue

        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue

        _, bear_signal, _, bear_level = pending_signals(df, i, spec)
        if bear_signal:
            pending_bear_i = i
            pending_bear_level = bear_level

        if pending_bear_i is not None and i - pending_bear_i > spec.fail_window:
            pending_bear_i = None
            pending_bear_level = None

        if pending_bear_i is None or i <= pending_bear_i:
            continue

        if not is_denial(df, i, spec, "bear", pending_bear_level):
            continue

        if quality_ok(df, i, "long", spec):
            rows.append(
                {
                    "symbol": symbol,
                    "denial_name": spec.name,
                    "denial_family": spec.family,
                    "d1_signal_time": ts,
                    "context_start": ts + pd.Timedelta(days=1),
                    "fail_bars": i - pending_bear_i,
                    "denial_level": pending_bear_level,
                    "atr": atr_i,
                    "body_ratio": float(df["body_ratio"].iloc[i]),
                    "close_location": float(df["close_location"].iloc[i]),
                    "rsi14": float(df["rsi14"].iloc[i]) if pd.notna(df["rsi14"].iloc[i]) else math.nan,
                }
            )

        pending_bear_i = None
        pending_bear_level = None

    return pd.DataFrame(rows)


def context_match(
    contexts: pd.DataFrame,
    ts: pd.Timestamp,
    context_spec: ContextSpec | None,
) -> dict | None:
    if context_spec is None:
        return {
            "context_name": "BASELINE_NO_D1_CONTEXT",
            "d1_context_signal_time": pd.NaT,
            "d1_context_strategy": "NONE",
            "d1_context_age_days": math.nan,
            "d1_context_fail_bars": math.nan,
        }
    if contexts.empty:
        if context_spec.mode == "avoid":
            return {
                "context_name": context_spec.name,
                "d1_context_signal_time": pd.NaT,
                "d1_context_strategy": "NO_D1_CONTEXT_DATA",
                "d1_context_age_days": math.nan,
                "d1_context_fail_bars": math.nan,
            }
        return None
    subset = contexts[
        (contexts["denial_name"].isin(context_spec.denial_names))
        & (contexts["context_start"] <= ts)
        & (ts <= contexts["context_start"] + pd.Timedelta(days=context_spec.active_days))
    ]
    if context_spec.mode == "avoid":
        if subset.empty:
            return {
                "context_name": context_spec.name,
                "d1_context_signal_time": pd.NaT,
                "d1_context_strategy": "NO_RECENT_D1_BEAR_DENIAL",
                "d1_context_age_days": math.nan,
                "d1_context_fail_bars": math.nan,
            }
        return None
    if subset.empty:
        return None
    row = subset.sort_values("context_start").iloc[-1]
    age = (ts - row["context_start"]) / pd.Timedelta(days=1)
    return {
        "context_name": context_spec.name,
        "d1_context_signal_time": row["d1_signal_time"],
        "d1_context_strategy": row["denial_name"],
        "d1_context_age_days": float(age),
        "d1_context_fail_bars": int(row["fail_bars"]),
    }


def extract_h4_v_candidates(
    df: pd.DataFrame,
    symbol: str,
    v_spec: RightShoulderSpec,
) -> pd.DataFrame:
    """Extract all possible H4 V reclaim signals once.

    Pair de-duplication and position blocking are handled later per context
    specification. This keeps the grid fast while still letting skipped
    no-context signals leave room for later valid signals.
    """

    settings = timeframe_settings("H4")
    pivots = build_confirmed_pivots(df, settings["pivot_width"], settings["min_swing_atr"])
    active: list[Pivot] = []
    pointer = 0
    rows: list[dict] = []
    empty_used_pairs: set[str] = set()

    for i in range(2, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue

        sig = right_shoulder_signal(df, i, active, v_spec, settings, empty_used_pairs)
        if sig is None:
            continue

        rows.append(
            {
                "symbol": symbol,
                "signal_i": i,
                "signal_time": ts,
                "v_strategy": v_spec.name,
                **{k: v for k, v in sig.items() if k != "direction"},
            }
        )

    return pd.DataFrame(rows)


def run_h4_v_candidates_with_context(
    df: pd.DataFrame,
    symbol: str,
    v_spec: RightShoulderSpec,
    context_spec: ContextSpec | None,
    contexts: pd.DataFrame,
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []
    in_pos_until = -1
    used_pairs: set[str] = set()
    settings = timeframe_settings("H4")

    if candidates.empty:
        return pd.DataFrame()

    for _, candidate in candidates.sort_values(["signal_i", "signal_time"]).iterrows():
        i = int(candidate["signal_i"])
        ts = pd.Timestamp(candidate["signal_time"])
        pair_key = str(candidate["pair_key"])
        if pair_key in used_pairs:
            continue
        if i <= in_pos_until:
            continue

        context_info = context_match(contexts, ts, context_spec)
        if context_info is None:
            continue

        trade = simulate_trade(
            df=df,
            symbol=symbol,
            direction="long",
            signal_i=i,
            stop=float(candidate["stop"]),
            target=float(candidate["target"]),
            max_hold_bars=settings["max_hold_bars"],
        )
        if trade is None:
            continue

        used_pairs.add(pair_key)
        rows.append(
            {
                "symbol": symbol,
                "timeframe": "H4",
                "strategy": f"{context_info['context_name']}__{v_spec.name}",
                "context_name": context_info["context_name"],
                "v_strategy": v_spec.name,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                **context_info,
                **{
                    k: candidate[k]
                    for k in candidate.index
                    if k
                    not in {
                        "symbol",
                        "signal_i",
                        "signal_time",
                        "v_strategy",
                        "stop",
                        "target",
                    }
                },
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))

    return pd.DataFrame(rows)


def summarize_if_any(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_cols)
    return summarize(df, group_cols)


def context_count_table(contexts: pd.DataFrame) -> pd.DataFrame:
    if contexts.empty:
        return pd.DataFrame(columns=["denial_name", "events"])
    return (
        contexts.groupby("denial_name", dropna=False)
        .size()
        .reset_index(name="events")
        .sort_values("events", ascending=False)
    )


def write_report(
    trades: pd.DataFrame,
    contexts: pd.DataFrame,
    overall: pd.DataFrame,
    practical_ex_xau: pd.DataFrame,
    by_period: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_context_source: pd.DataFrame,
) -> None:
    lines = [
        "# D1売り否定 + H4 V右肩リクレイム 検証 2026-05-29",
        "",
        "## 仮説",
        "",
        "D1で売りシグナルが否定された直後だけ、H4の右肩優位V・左肩起点超えを買う仮説を検証する。",
        "",
        "追加で、逆発見を確認するため、直近D1売り否定がない場合だけ入る除外フィルタも検証する。",
        "",
        "## D1売り否定コンテキスト",
        "",
        "- D1 Donchian20下抜け否定_Q",
        "- D1 Donchian55下抜け否定_Q",
        "- D1 RSI30割れ否定_Q",
        "- D1の否定は日足確定後にしか分からないため、H4では翌日から有効にした。",
        "- `AVOID_...` は、直近指定日数内にD1売り否定がない時だけH4 Vを許可する。",
        "",
        "## H4エントリー",
        "",
        "- confirmed pivot high -> confirmed pivot low の急落V。",
        "- 右肩速度が左肩速度以上、主候補は1.2倍以上。",
        "- 終値が左肩起点を0.05ATR上抜け。",
        "- 主候補は実体45%以上、終値位置60%以上、RR1.5。",
        "- Entryは次H4足始値、SLはV安値 - 0.25ATR。",
        "",
        "## D1コンテキスト件数",
        "",
        markdown_table(context_count_table(contexts), 20),
        "",
        "## 全体結果",
        "",
        markdown_table(overall, 80),
        "",
        "## 実戦候補 XAUUSD除外",
        "",
        markdown_table(practical_ex_xau, 60),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 100),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 120),
        "",
        "## D1否定ソース別",
        "",
        markdown_table(by_context_source, 80),
        "",
        "## 出力",
        "",
        "- `contexts.csv`",
        "- `trades.csv`",
        "- `summary_overall.csv`",
        "- `summary_practical_ex_xau.csv`",
        "- `summary_by_period.csv`",
        "- `summary_by_symbol.csv`",
        "- `summary_by_context_source.csv`",
        "- `data_coverage.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_contexts: list[pd.DataFrame] = []
    all_trades: list[pd.DataFrame] = []
    coverage_rows: list[dict] = []

    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue

        raw = load_instrument(symbol)
        coverage_rows.append({"symbol": symbol, "rows_h1": len(raw), "first": raw.index.min(), "last": raw.index.max()})

        d1 = add_denial_indicators(resample_ohlc(raw, "D1"))
        symbol_contexts: list[pd.DataFrame] = []
        for denial_spec in DENIAL_SPECS:
            c = detect_d1_bearish_denials(d1, symbol, denial_spec)
            if not c.empty:
                symbol_contexts.append(c)
                all_contexts.append(c)
        contexts_df = pd.concat(symbol_contexts, ignore_index=True) if symbol_contexts else pd.DataFrame()
        if not contexts_df.empty:
            contexts_df["d1_signal_time"] = pd.to_datetime(contexts_df["d1_signal_time"])
            contexts_df["context_start"] = pd.to_datetime(contexts_df["context_start"])

        h4 = add_regime_indicators(resample_ohlc(raw, "H4"))
        for v_spec in V_SPECS:
            candidates = extract_h4_v_candidates(h4, symbol, v_spec)
            for context_spec in CONTEXT_SPECS:
                trades = run_h4_v_candidates_with_context(h4, symbol, v_spec, context_spec, contexts_df, candidates)
                if not trades.empty:
                    all_trades.append(trades)

    pd.DataFrame(coverage_rows).to_csv(OUT_DIR / "data_coverage.csv", index=False)

    contexts_out = pd.concat(all_contexts, ignore_index=True) if all_contexts else pd.DataFrame()
    if not contexts_out.empty:
        contexts_out = contexts_out.sort_values(["symbol", "d1_signal_time", "denial_name"]).reset_index(drop=True)
    contexts_out.to_csv(OUT_DIR / "contexts.csv", index=False)

    if not all_trades:
        (OUT_DIR / "report_ja.md").write_text("# D1売り否定 + H4 V右肩リクレイム\n\nNo trades.", encoding="utf-8")
        print(f"No trades. Report: {OUT_DIR / 'report_ja.md'}")
        return

    trades_df = pd.concat(all_trades, ignore_index=True)
    for col in ["signal_time", "entry_time", "exit_time", "d1_context_signal_time"]:
        trades_df[col] = pd.to_datetime(trades_df[col])
    trades_df = trades_df.sort_values(["strategy", "entry_time", "symbol"]).reset_index(drop=True)
    trades_df.to_csv(OUT_DIR / "trades.csv", index=False)

    overall = summarize(trades_df, ["context_name", "v_strategy", "strategy"])
    practical = trades_df[trades_df["symbol"] != "XAUUSD"].copy()
    practical_ex_xau = summarize_if_any(practical, ["context_name", "v_strategy"])
    by_period = summarize(trades_df, ["context_name", "v_strategy", "period"])
    by_symbol = summarize(trades_df, ["context_name", "v_strategy", "symbol"])
    by_context_source = summarize(
        trades_df[trades_df["context_name"] != "BASELINE_NO_D1_CONTEXT"].copy(),
        ["context_name", "v_strategy", "d1_context_strategy"],
    )

    overall.to_csv(OUT_DIR / "summary_overall.csv", index=False)
    practical_ex_xau.to_csv(OUT_DIR / "summary_practical_ex_xau.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_context_source.to_csv(OUT_DIR / "summary_by_context_source.csv", index=False)

    write_report(trades_df, contexts_out, overall, practical_ex_xau, by_period, by_symbol, by_context_source)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(practical_ex_xau.head(40).to_string(index=False))


if __name__ == "__main__":
    main()

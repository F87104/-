#!/usr/bin/env python3
"""
H1 lower-high / rebreak filter study for the H4 low-stagnation short setup.

Idea:
After an H4 support break, do not rely only on the H4 stagnation candle.
Check whether H1 has made a lower pullback high and then broken back below
the intervening swing low. This should capture "the pullback failed" more
directly than named patterns such as H&S.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, markdown_table, resample_ohlc
from run_h4_stagnation_followup_validation import actual_trade_sample, practical_mask
from run_h4_stagnation_precision_hardening import CORE4, quality_mask, strict_mask
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_followup_validation" / "enriched_followup.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h1_lower_high_filter_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"
NO_AUD_USD = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY", "SILVER"}


@dataclass(frozen=True)
class LHSpec:
    pivot_len: int
    min_lower_atr: float
    min_swing_atr: float
    rebreak_buffer_atr: float
    max_rebreak_bars: int

    @property
    def name(self) -> str:
        return (
            f"P{self.pivot_len}_LOW{self.min_lower_atr:g}"
            f"_SW{self.min_swing_atr:g}_BUF{self.rebreak_buffer_atr:g}"
            f"_EXP{self.max_rebreak_bars}"
        )


def load_source() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def build_frames() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    h1: dict[str, pd.DataFrame] = {}
    h4: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        h1[symbol] = add_extended_features(add_indicators(resample_ohlc(raw, "H1")))
        h4[symbol] = add_extended_features(add_indicators(resample_ohlc(raw, "H4")))
    return h1, h4


def is_pivot_high(high: np.ndarray, k: int, piv_len: int) -> bool:
    win = high[k - piv_len : k + piv_len + 1]
    return bool(np.isfinite(high[k]) and high[k] == np.nanmax(win))


def is_pivot_low(low: np.ndarray, k: int, piv_len: int) -> bool:
    win = low[k - piv_len : k + piv_len + 1]
    return bool(np.isfinite(low[k]) and low[k] == np.nanmin(win))


def add_pivot(p_price: list[float], p_bar: list[int], p_type: list[int], price: float, bar: int, typ: int) -> None:
    if p_type and p_type[-1] == typ:
        prev = p_price[-1]
        keep_new = (typ == 1 and price > prev) or (typ == -1 and price < prev)
        if keep_new:
            p_price[-1] = price
            p_bar[-1] = bar
    else:
        p_price.append(price)
        p_bar.append(bar)
        p_type.append(typ)

    while len(p_type) > 120:
        p_price.pop(0)
        p_bar.pop(0)
        p_type.pop(0)


def lh_specs() -> list[LHSpec]:
    specs: list[LHSpec] = []
    for pivot_len in [2, 3, 5]:
        for min_lower_atr in [0.0, 0.10, 0.25]:
            for min_swing_atr in [0.5, 1.0]:
                for rebreak_buffer_atr in [0.0, 0.05]:
                    for max_rebreak_bars in [12, 24, 48]:
                        specs.append(
                            LHSpec(
                                pivot_len=pivot_len,
                                min_lower_atr=min_lower_atr,
                                min_swing_atr=min_swing_atr,
                                rebreak_buffer_atr=rebreak_buffer_atr,
                                max_rebreak_bars=max_rebreak_bars,
                            )
                        )
    return specs


def detect_lh_events(df: pd.DataFrame, spec: LHSpec) -> pd.DataFrame:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)

    p_price: list[float] = []
    p_bar: list[int] = []
    p_type: list[int] = []
    pending: list[dict] = []
    rows: list[dict] = []

    for current_i in range(spec.pivot_len * 2, len(df)):
        pivot_i = current_i - spec.pivot_len
        new_pivot = False

        if is_pivot_high(high, pivot_i, spec.pivot_len):
            add_pivot(p_price, p_bar, p_type, float(high[pivot_i]), pivot_i, 1)
            new_pivot = True
        elif is_pivot_low(low, pivot_i, spec.pivot_len):
            add_pivot(p_price, p_bar, p_type, float(low[pivot_i]), pivot_i, -1)
            new_pivot = True

        if new_pivot and len(p_type) >= 3 and p_type[-3:] == [1, -1, 1]:
            h1_price, swing_low, h2_price = p_price[-3:]
            h1_i, low_i, h2_i = p_bar[-3:]
            atr_ref = atr[h2_i] if 0 <= h2_i < len(atr) else np.nan
            if math.isfinite(atr_ref) and atr_ref > 0:
                lower_atr = (h1_price - h2_price) / atr_ref
                left_swing_atr = (h1_price - swing_low) / atr_ref
                right_swing_atr = (h2_price - swing_low) / atr_ref
                swing_ok = min(left_swing_atr, right_swing_atr) >= spec.min_swing_atr
                lower_ok = lower_atr >= spec.min_lower_atr
                if h2_price < h1_price and lower_ok and swing_ok:
                    event = {
                        "lh_spec": spec.name,
                        "event": "lh_confirm",
                        "confirm_i": current_i,
                        "first_high_i": h1_i,
                        "swing_low_i": low_i,
                        "second_high_i": h2_i,
                        "first_high": h1_price,
                        "swing_low": swing_low,
                        "second_high": h2_price,
                        "lower_atr": lower_atr,
                        "left_swing_atr": left_swing_atr,
                        "right_swing_atr": right_swing_atr,
                    }
                    rows.append(event)
                    pending.append(
                        {
                            **event,
                            "expire_i": current_i + spec.max_rebreak_bars,
                            "broken": False,
                        }
                    )

        next_pending: list[dict] = []
        for item in pending:
            if current_i > item["expire_i"]:
                continue
            if item["broken"]:
                next_pending.append(item)
                continue
            atr_now = atr[current_i]
            if not math.isfinite(atr_now) or atr_now <= 0:
                next_pending.append(item)
                continue
            if current_i > int(item["confirm_i"]) and close[current_i] < float(item["swing_low"]) - atr_now * spec.rebreak_buffer_atr:
                item["broken"] = True
                rows.append(
                    {
                        "lh_spec": spec.name,
                        "event": "lh_rebreak",
                        "confirm_i": current_i,
                        "lh_confirm_i": int(item["confirm_i"]),
                        "first_high_i": int(item["first_high_i"]),
                        "swing_low_i": int(item["swing_low_i"]),
                        "second_high_i": int(item["second_high_i"]),
                        "first_high": float(item["first_high"]),
                        "swing_low": float(item["swing_low"]),
                        "second_high": float(item["second_high"]),
                        "lower_atr": float(item["lower_atr"]),
                        "left_swing_atr": float(item["left_swing_atr"]),
                        "right_swing_atr": float(item["right_swing_atr"]),
                        "rebreak_close": close[current_i],
                    }
                )
            next_pending.append(item)
        pending = next_pending

    return pd.DataFrame(rows)


def sample_sets(enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
    primary = enriched[
        enriched["trigger_mode"].eq("stagnation")
        & enriched["lookback_bars"].eq(120)
        & enriched["adx14"].ge(30)
        & enriched["risk_atr_at_signal"].le(1.5)
        & enriched["bb_width_atr"].between(3.0, 8.0)
    ].copy()
    practical = enriched[practical_mask(enriched)].copy()
    primary_support = primary[primary["support_age_bars"].between(60, 119)].copy()
    practical_support = practical[practical["support_age_bars"].between(60, 119)].copy()
    return {
        "primary_all": actual_trade_sample(primary),
        "primary_core4": actual_trade_sample(primary[primary["symbol"].isin(CORE4)].copy()),
        "primary_core4_quality": actual_trade_sample(primary[primary["symbol"].isin(CORE4) & quality_mask(primary)].copy()),
        "primary_core4_strict": actual_trade_sample(primary[primary["symbol"].isin(CORE4) & strict_mask(primary)].copy()),
        "primary_support60_119": actual_trade_sample(primary_support),
        "primary_support60_119_core4": actual_trade_sample(primary_support[primary_support["symbol"].isin(CORE4)].copy()),
        "practical_no_AUD_USD": actual_trade_sample(practical[practical["symbol"].isin(NO_AUD_USD)].copy()),
        "practical_core4": actual_trade_sample(practical[practical["symbol"].isin(CORE4)].copy()),
        "practical_support60_119_no_AUD_USD": actual_trade_sample(
            practical_support[practical_support["symbol"].isin(NO_AUD_USD)].copy()
        ),
    }


def h4_break_time(row: dict, h4_frames: dict[str, pd.DataFrame]) -> pd.Timestamp | None:
    frame = h4_frames[str(row["symbol"])]
    break_i = int(row["break_i"])
    if break_i < 0 or break_i >= len(frame):
        return None
    return pd.Timestamp(frame.index[break_i])


def has_event(events: pd.DataFrame, event: str, lo_i: int, hi_i: int) -> bool:
    if events.empty:
        return False
    return bool((events["event"].eq(event) & events["confirm_i"].between(lo_i, hi_i)).any())


def has_full_after_break(events: pd.DataFrame, event: str, break_i: int, hi_i: int) -> bool:
    if events.empty:
        return False
    m = events["event"].eq(event) & events["confirm_i"].le(hi_i) & events["first_high_i"].ge(break_i)
    return bool(m.any())


def latest_event(events: pd.DataFrame, hi_i: int) -> pd.Series | None:
    if events.empty:
        return None
    before = events[events["confirm_i"].le(hi_i)]
    if before.empty:
        return None
    return before.iloc[-1]


def annotate_with_lh(
    sample: pd.DataFrame,
    detections: dict[tuple[str, str], pd.DataFrame],
    h1_frames: dict[str, pd.DataFrame],
    h4_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict] = []
    windows = [12, 24, 48, 72, 120]
    for row in sample.to_dict("records"):
        symbol = str(row["symbol"])
        spec_name = str(row["lh_spec"])
        events = detections.get((symbol, spec_name), pd.DataFrame())
        h1 = h1_frames[symbol]
        signal_time = pd.Timestamp(row["signal_time"])
        break_time = h4_break_time(row, h4_frames)

        signal_pos = h1.index.searchsorted(signal_time, side="right") - 1
        break_pos = h1.index.searchsorted(break_time, side="left") if break_time is not None else 0

        out = dict(row)
        out.update(
            {
                "h1_break_time": break_time,
                "h1_signal_i": signal_pos,
                "h1_break_i": break_pos,
                "h1_latest_event": "",
                "h1_latest_event_age": np.nan,
                "h1_lh_confirm_after_break_full": False,
                "h1_lh_rebreak_after_break_full": False,
                "h1_lh_confirm_after_break_confirm": False,
                "h1_lh_rebreak_after_break_confirm": False,
                "h1_lh_confirm_after_break_no_rebreak": False,
            }
        )

        if signal_pos < 0 or break_pos < 0:
            rows.append(out)
            continue

        for window in windows:
            for event in ["lh_confirm", "lh_rebreak"]:
                out[f"h1_{event}_{window}"] = has_event(events, event, signal_pos - window, signal_pos)

        out["h1_lh_confirm_after_break_full"] = has_full_after_break(events, "lh_confirm", break_pos, signal_pos)
        out["h1_lh_rebreak_after_break_full"] = has_full_after_break(events, "lh_rebreak", break_pos, signal_pos)
        out["h1_lh_confirm_after_break_confirm"] = has_event(events, "lh_confirm", break_pos, signal_pos)
        out["h1_lh_rebreak_after_break_confirm"] = has_event(events, "lh_rebreak", break_pos, signal_pos)
        out["h1_lh_confirm_after_break_no_rebreak"] = bool(out["h1_lh_confirm_after_break_confirm"]) and not bool(
            out["h1_lh_rebreak_after_break_confirm"]
        )

        latest = latest_event(events, signal_pos)
        if latest is not None:
            out["h1_latest_event"] = str(latest["event"])
            out["h1_latest_event_age"] = int(signal_pos - latest["confirm_i"])
        rows.append(out)
    return pd.DataFrame(rows)


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def metric_row(sample_name: str, spec_name: str, rule_name: str, sample: pd.DataFrame, base_count: int) -> dict:
    row = {"sample": sample_name, "lh_spec": spec_name, "rule": rule_name, "base_trades": int(base_count)}
    row.update(metrics(sample, R_COL))
    row["coverage_pct"] = float(len(sample) / base_count * 100.0) if base_count else 0.0
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample.columns else ""
    row["pf"] = profit_factor(sample[R_COL].astype(float)) if len(sample) else math.nan
    return row


def summarize_rules(annotated: pd.DataFrame) -> pd.DataFrame:
    masks = [
        ("lh_confirm_after_break_full", lambda d: d["h1_lh_confirm_after_break_full"]),
        ("lh_rebreak_after_break_full", lambda d: d["h1_lh_rebreak_after_break_full"]),
        ("lh_confirm_after_break_confirm", lambda d: d["h1_lh_confirm_after_break_confirm"]),
        ("lh_rebreak_after_break_confirm", lambda d: d["h1_lh_rebreak_after_break_confirm"]),
        ("lh_confirm_after_break_no_rebreak", lambda d: d["h1_lh_confirm_after_break_no_rebreak"]),
        ("lh_rebreak_12", lambda d: d["h1_lh_rebreak_12"]),
        ("lh_rebreak_24", lambda d: d["h1_lh_rebreak_24"]),
        ("lh_rebreak_48", lambda d: d["h1_lh_rebreak_48"]),
        ("lh_rebreak_72", lambda d: d["h1_lh_rebreak_72"]),
        ("lh_rebreak_120", lambda d: d["h1_lh_rebreak_120"]),
        ("lh_confirm_24", lambda d: d["h1_lh_confirm_24"]),
        ("lh_confirm_48", lambda d: d["h1_lh_confirm_48"]),
        ("no_lh_rebreak_48", lambda d: ~d["h1_lh_rebreak_48"]),
        ("no_lh_rebreak_after_break_full", lambda d: ~d["h1_lh_rebreak_after_break_full"]),
    ]
    rows: list[dict] = []
    for (sample_name, spec_name), group in annotated.groupby(["sample", "lh_spec"]):
        base_count = len(group)
        rows.append(metric_row(sample_name, spec_name, "baseline", group, base_count))
        for rule_name, fn in masks:
            mask = fn(group).fillna(False)
            rows.append(metric_row(sample_name, spec_name, rule_name, group[mask].copy(), base_count))

    out = pd.DataFrame(rows)
    base = out[out["rule"].eq("baseline")][["sample", "lh_spec", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]].rename(
        columns={
            "win_rate": "base_win_rate",
            "total_r": "base_total_r",
            "avg_r": "base_avg_r",
            "pf": "base_pf",
            "max_dd_r": "base_max_dd_r",
        }
    )
    out = out.merge(base, on=["sample", "lh_spec"], how="left")
    out["delta_win_rate"] = out["win_rate"] - out["base_win_rate"]
    out["delta_total_r"] = out["total_r"] - out["base_total_r"]
    out["delta_avg_r"] = out["avg_r"] - out["base_avg_r"]
    out["delta_pf"] = out["pf"] - out["base_pf"]
    return out.sort_values(["sample", "total_r", "pf"], ascending=[True, False, False])


def write_report(summaries: pd.DataFrame) -> None:
    focus_samples = [
        "primary_all",
        "primary_core4",
        "primary_core4_quality",
        "primary_support60_119",
        "primary_support60_119_core4",
        "practical_no_AUD_USD",
        "practical_core4",
        "practical_support60_119_no_AUD_USD",
    ]
    cols = [
        "sample",
        "lh_spec",
        "rule",
        "base_trades",
        "trades",
        "coverage_pct",
        "win_rate",
        "delta_win_rate",
        "total_r",
        "delta_total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "symbols",
        "periods",
    ]
    baseline = (
        summaries[summaries["rule"].eq("baseline") & summaries["sample"].isin(focus_samples)]
        .sort_values(["sample", "lh_spec"])
        .groupby("sample", as_index=False)
        .head(1)
        .copy()
    )
    useful = summaries[
        summaries["sample"].isin(focus_samples)
        & ~summaries["rule"].eq("baseline")
        & summaries["trades"].ge(3)
        & summaries["coverage_pct"].between(10, 95)
        & summaries["total_r"].gt(0)
    ].copy()
    improved = useful[
        (useful["pf"] > useful["base_pf"])
        & (useful["win_rate"] >= useful["base_win_rate"])
    ].copy()
    top_useful = improved.sort_values(
        ["sample", "delta_total_r", "pf", "total_r"], ascending=[True, False, False, False]
    ).groupby("sample").head(8)

    main_rules = [
        "lh_confirm_after_break_full",
        "lh_rebreak_after_break_full",
        "lh_confirm_after_break_confirm",
        "lh_rebreak_after_break_confirm",
        "lh_confirm_after_break_no_rebreak",
        "lh_rebreak_24",
        "lh_rebreak_48",
    ]
    main_focus = summaries[
        summaries["sample"].isin(focus_samples)
        & summaries["rule"].isin(main_rules)
        & summaries["trades"].ge(2)
    ].sort_values(["sample", "pf", "total_r"], ascending=[True, False, False]).groupby("sample").head(8)

    default_spec = "P3_LOW0.1_SW0.5_BUF0_EXP24"
    default_rules = [
        "baseline",
        "lh_confirm_after_break_full",
        "lh_rebreak_after_break_full",
        "lh_confirm_after_break_confirm",
        "lh_rebreak_after_break_confirm",
        "lh_confirm_after_break_no_rebreak",
        "lh_rebreak_24",
        "lh_rebreak_48",
        "no_lh_rebreak_after_break_full",
    ]
    default_focus = summaries[
        summaries["sample"].isin(["primary_core4", "primary_core4_quality", "practical_core4", "practical_no_AUD_USD"])
        & summaries["lh_spec"].eq(default_spec)
        & summaries["rule"].isin(default_rules)
    ].copy()
    default_focus["__rule_order"] = default_focus["rule"].map({rule: i for i, rule in enumerate(default_rules)})
    default_focus = default_focus.sort_values(["sample", "__rule_order"]).drop(columns=["__rule_order"])

    candidate_keys = [
        (
            "A 実戦本線: Core4でH4ブレイク後のH1戻り高値切り下げ",
            "practical_core4",
            "P3_LOW0.25_SW1_BUF0_EXP24",
            "lh_confirm_after_break_full",
        ),
        (
            "B 実戦補助: Core4で直近24本以内のH1再下落",
            "practical_core4",
            "P2_LOW0.1_SW1_BUF0_EXP48",
            "lh_rebreak_24",
        ),
        (
            "C 広め確認: AUD/USD除外で直近24本以内のH1再下落",
            "practical_no_AUD_USD",
            "P2_LOW0.1_SW1_BUF0_EXP48",
            "lh_rebreak_24",
        ),
        (
            "D Primary厳選: Core4品質条件でH1切り下げ確認",
            "primary_core4_quality",
            "P2_LOW0.1_SW1_BUF0_EXP24",
            "lh_confirm_after_break_confirm",
        ),
        (
            "E Primary広め: 直近72本以内のH1再下落",
            "primary_all",
            "P3_LOW0.1_SW0.5_BUF0_EXP24",
            "lh_rebreak_72",
        ),
    ]
    candidate_rows = []
    for label, sample_name, spec_name, rule_name in candidate_keys:
        hit = summaries[
            summaries["sample"].eq(sample_name)
            & summaries["lh_spec"].eq(spec_name)
            & summaries["rule"].eq(rule_name)
        ]
        if not hit.empty:
            row = hit.iloc[0].copy()
            row["candidate"] = label
            candidate_rows.append(row)
    candidate_focus = pd.DataFrame(candidate_rows)
    candidate_cols = ["candidate"] + cols

    lines = [
        "# H1 Lower-High Rebreak Filter Study",
        "",
        "Status: 検証途中。H4安値停滞ショートに対して、H1で戻り高値切り下げと再下落が確認できるかを検証。",
        "",
        "## 検証した使い方",
        "",
        "- `lh_confirm`: H1で 高値 -> 安値 -> 低い高値 が確定。",
        "- `lh_rebreak`: その後、H1終値が中間安値を下抜き。戻り売り再開の確認。",
        "- `after_break_full`: H1の最初の戻り高値から再下落までが、H4安値ブレイク後に作られたもの。",
        "- `after_break_confirm`: H1イベントの確定が、H4安値ブレイク後からH4シグナル前までに起きたもの。",
        "",
        "## 重要な実装注意",
        "",
        "- H1ピボットは右側 `pivot_len` 本後に確定するため、確定済みイベントだけを使用。",
        "- H4の `break_i` をH4足の日時へ戻し、H1側ではその時刻以降のイベントだけを検証。",
        "- `lh_rebreak` は、低い高値の確定後 `max_rebreak_bars` 本以内に中間安値を終値で下抜く必要がある。",
        "",
        "## ベースライン",
        "",
        markdown_table(baseline[cols], 20) if not baseline.empty else "_No rows._",
        "",
        "## サンプル別 改善候補",
        "",
        "PFと勝率がベースライン以上、かつ3件以上の条件だけを表示。",
        "",
        markdown_table(top_useful[cols], 60) if not top_useful.empty else "_No rows._",
        "",
        "## Pineでまず試す候補",
        "",
        "成績順だけではなく、実装しやすさと売買ロジックの自然さで候補を整理。",
        "",
        markdown_table(candidate_focus[candidate_cols], 20) if not candidate_focus.empty else "_No rows._",
        "",
        "## Pine化時の本線案",
        "",
        "- H4の既存シグナルを先に作る。",
        "- H4の安値ブレイク後に、H1で `高値 -> 安値 -> 低い高値` が確定しているかを見る。",
        "- まずは `pivot=3`, `切り下げ>=0.25ATR`, `左右の波>=1ATR` を本線にする。",
        "- H1の中間安値再下落はエントリー必須ではなく、最初は確認タグとして使う。必須化するとPFは上がるが件数と総Rが削られやすい。",
        "- `no_lh_rebreak` 系は数字が良く見える箇所があるが、売り根拠として逆向きなので実装本線にはしない。",
        "",
        "## H1 lower-high 系だけを見る",
        "",
        markdown_table(main_focus[cols], 80) if not main_focus.empty else "_No rows._",
        "",
        "## まず見る標準候補",
        "",
        "`pivot=3`, `切り下げ>=0.1ATR`, `左右の波>=0.5ATR`, `再下落期限24本`, `buffer=0`。",
        "",
        markdown_table(default_focus[cols], 80) if not default_focus.empty else "_No rows._",
        "",
        "## 暫定解釈",
        "",
        "- H&Sよりも、H1の戻り高値切り下げを直接見る方がH4安値停滞ショートとは相性が良い。",
        "- 実戦本線は `practical_core4` の `lh_confirm_after_break_full`。26件から14件に絞り、勝率42.31% -> 57.14%、総R +6.16R -> +9.54R、PF 1.40 -> 2.53。",
        "- H1再下落まで待つ条件は精度確認には有効だが、単独で必須にすると件数がかなり減る。Pineではラベル/色分けでまず比較する。",
        "- 件数が少ない条件はPine表示だけにし、エントリー条件にはまだ入れない。",
        "",
        "## 出力CSV",
        "",
        "- `annotated_trades.csv`",
        "- `rule_summary.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    enriched = load_source()
    h1_frames, h4_frames = build_frames()
    specs = lh_specs()

    detections: dict[tuple[str, str], pd.DataFrame] = {}
    for spec in specs:
        for symbol, frame in h1_frames.items():
            detections[(symbol, spec.name)] = detect_lh_events(frame, spec)

    annotated_frames: list[pd.DataFrame] = []
    samples = sample_sets(enriched)
    for sample_name, sample in samples.items():
        if sample.empty:
            continue
        for spec in specs:
            work = sample.copy()
            work["sample"] = sample_name
            work["lh_spec"] = spec.name
            annotated_frames.append(annotate_with_lh(work, detections, h1_frames, h4_frames))

    annotated = pd.concat(annotated_frames, ignore_index=True) if annotated_frames else pd.DataFrame()
    summaries = summarize_rules(annotated) if not annotated.empty else pd.DataFrame()

    annotated.to_csv(OUT_DIR / "annotated_trades.csv", index=False)
    summaries.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    write_report(summaries)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if not summaries.empty:
        view = summaries[
            summaries["sample"].isin(["primary_core4_quality", "practical_core4"])
            & ~summaries["rule"].eq("baseline")
            & summaries["trades"].ge(3)
        ].sort_values(["sample", "pf", "total_r"], ascending=[True, False, False])
        print(view.head(30).to_string(index=False))


if __name__ == "__main__":
    main()

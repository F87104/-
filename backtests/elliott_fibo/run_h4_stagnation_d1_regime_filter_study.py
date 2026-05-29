#!/usr/bin/env python3
"""
Previous-day D1 regime filter study for the H4 low-stagnation short setup.

This pass deliberately avoids unfinished daily-bar leakage.  Every D1 feature
is taken from the previous completed daily candle relative to the H4 signal.
That makes the candidate directly portable to Pine with request.security(...)[1].
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, markdown_table, resample_ohlc
from run_h4_stagnation_followup_validation import actual_trade_sample, practical_mask
from run_h4_stagnation_precision_hardening import CORE4, NO_AUD_USD, quality_mask, strict_mask
from run_indicator_compatibility_search import add_extended_features
from run_low_break_lookback_exit_study import metrics


THIS_DIR = Path(__file__).resolve().parent
SOURCE = THIS_DIR / "results_2026_05_28" / "h4_stagnation_followup_validation" / "enriched_followup.csv"
H1_SOURCE = THIS_DIR / "results_2026_05_28" / "h1_lower_high_filter_study" / "annotated_trades.csv"
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_stagnation_d1_regime_filter_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def load_source() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def build_prev_d1_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        d1 = add_extended_features(add_indicators(resample_ohlc(load_instrument(symbol), "D1")))
        d1["close_below_ema20"] = d1["close"] < d1["ema20"]
        d1["close_below_ema50"] = d1["close"] < d1["ema50"]
        d1["ema20_below_ema50"] = d1["ema20"] < d1["ema50"]
        d1["stack_down"] = d1["close_below_ema20"] & d1["ema20_below_ema50"]
        d1["stack_strong_down"] = d1["stack_down"] & (d1["ema50"] < d1["ema200"])
        d1["macd_bear"] = d1["macd_hist"] < 0
        d1["macd_falling"] = d1["macd_hist_slope3"] < 0
        d1["rsi_lt50"] = d1["rsi14"] < 50
        d1["rsi_35_55"] = d1["rsi14"].between(35, 55)
        d1["adx_ge18"] = d1["adx14"] >= 18
        d1["adx_ge22"] = d1["adx14"] >= 22
        d1["bbpos_lt50"] = d1["bb_pos"] < 0.50
        d1["close_loc_lt50"] = d1["close_location"] < 0.50
        frames[symbol] = d1
    return frames


def add_prev_d1_features(df: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = [
        "close",
        "ema20",
        "ema50",
        "ema200",
        "ema20_slope_10_atr",
        "rsi14",
        "adx14",
        "bb_width_atr",
        "bb_pos",
        "macd_hist",
        "macd_hist_slope3",
        "atr_pctile_252",
        "close_location",
        "close_below_ema20",
        "close_below_ema50",
        "ema20_below_ema50",
        "stack_down",
        "stack_strong_down",
        "macd_bear",
        "macd_falling",
        "rsi_lt50",
        "rsi_35_55",
        "adx_ge18",
        "adx_ge22",
        "bbpos_lt50",
        "close_loc_lt50",
    ]
    rows: list[dict] = []
    for row in df.to_dict("records"):
        symbol = str(row["symbol"])
        ts = pd.Timestamp(row["signal_time"])
        d1 = frames[symbol]
        day_start = ts.normalize()
        pos = d1.index.searchsorted(day_start, side="left") - 1
        out = dict(row)
        if pos >= 0:
            d1_row = d1.iloc[pos]
            out["prev_d1_time"] = d1.index[pos]
            for col in cols:
                out[f"prev_d1_{col}"] = d1_row[col]
        else:
            out["prev_d1_time"] = pd.NaT
            for col in cols:
                out[f"prev_d1_{col}"] = np.nan
        rows.append(out)
    return pd.DataFrame(rows)


def add_h1_focus_flags(samples: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    if not H1_SOURCE.exists():
        return samples
    usecols = [
        "sample",
        "lh_spec",
        "symbol",
        "entry_time",
        "h1_lh_confirm_after_break_full",
        "h1_lh_rebreak_24",
    ]
    h1 = pd.read_csv(H1_SOURCE, usecols=usecols)
    h1["entry_time"] = pd.to_datetime(h1["entry_time"], format="mixed", errors="coerce")
    focus = h1[
        h1["sample"].eq("practical_core4")
        & h1["lh_spec"].eq("P3_LOW0.25_SW1_BUF0_EXP24")
    ].drop_duplicates(["symbol", "entry_time"])
    out: dict[str, pd.DataFrame] = {}
    for name, sample in samples.items():
        work = sample.merge(focus.drop(columns=["sample", "lh_spec"]), on=["symbol", "entry_time"], how="left")
        for col in ["h1_lh_confirm_after_break_full", "h1_lh_rebreak_24"]:
            if col in work.columns:
                work[col] = work[col].astype("boolean").fillna(False).astype(bool)
        out[name] = work
    return out


def sample_sets(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    primary = df[
        df["trigger_mode"].eq("stagnation")
        & df["lookback_bars"].eq(120)
        & df["adx14"].ge(30)
        & df["risk_atr_at_signal"].le(1.5)
        & df["bb_width_atr"].between(3.0, 8.0)
    ].copy()
    practical = df[practical_mask(df)].copy()
    samples = {
        "practical_no_AUD_USD": actual_trade_sample(practical[practical["symbol"].isin(NO_AUD_USD)].copy()),
        "practical_core4": actual_trade_sample(practical[practical["symbol"].isin(CORE4)].copy()),
        "primary_core4": actual_trade_sample(primary[primary["symbol"].isin(CORE4)].copy()),
        "primary_core4_quality": actual_trade_sample(
            primary[primary["symbol"].isin(CORE4) & quality_mask(primary)].copy()
        ),
    }
    return add_h1_focus_flags(samples)


def metric_row(sample_name: str, rule_name: str, sample: pd.DataFrame, base_count: int) -> dict:
    row = {"sample": sample_name, "rule": rule_name, "base_trades": int(base_count)}
    row.update(metrics(sample, R_COL))
    row["coverage_pct"] = float(len(sample) / base_count * 100.0) if base_count else 0.0
    row["pf"] = profit_factor(sample[R_COL].astype(float)) if len(sample) else math.nan
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample.columns else ""
    return row


def rule_masks(sample: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    d1_rsi_30_55 = sample["prev_d1_rsi14"].between(30, 55)
    d1_rsi_35_55 = sample["prev_d1_rsi14"].between(35, 55)
    d1_rsi_40_55 = sample["prev_d1_rsi14"].between(40, 55)
    quality = quality_mask(sample)
    strict = strict_mask(sample)
    h1_confirm = (
        sample["h1_lh_confirm_after_break_full"]
        if "h1_lh_confirm_after_break_full" in sample.columns
        else pd.Series(False, index=sample.index)
    )
    h1_rebreak = (
        sample["h1_lh_rebreak_24"]
        if "h1_lh_rebreak_24" in sample.columns
        else pd.Series(False, index=sample.index)
    )
    return [
        ("prevD1_RSI_30_55", d1_rsi_30_55),
        ("prevD1_RSI_35_55", d1_rsi_35_55),
        ("prevD1_RSI_40_55", d1_rsi_40_55),
        ("quality", quality),
        ("strict", strict),
        ("prevD1_RSI_35_55__quality", d1_rsi_35_55 & quality),
        ("prevD1_RSI_35_55__strict", d1_rsi_35_55 & strict),
        ("prevD1_RSI_35_55__break_depth_ge_0_15", d1_rsi_35_55 & sample["break_depth_atr"].ge(0.15)),
        ("prevD1_RSI_35_55__close_location_le_0_50", d1_rsi_35_55 & sample["break_close_location"].le(0.50)),
        ("prevD1_RSI_35_55__support60_119", d1_rsi_35_55 & sample["support_age_bars"].between(60, 119)),
        ("prevD1_close_below_EMA50", sample["prev_d1_close_below_ema50"].fillna(False).astype(bool)),
        ("prevD1_stack_down", sample["prev_d1_stack_down"].fillna(False).astype(bool)),
        ("prevD1_MACD_falling", sample["prev_d1_macd_falling"].fillna(False).astype(bool)),
        ("prevD1_close_location_lt_0_50", sample["prev_d1_close_loc_lt50"].fillna(False).astype(bool)),
        ("H1_LH_confirm", h1_confirm),
        ("H1_LH_confirm__prevD1_RSI_35_55", h1_confirm & d1_rsi_35_55),
        ("H1_LH_rebreak24__prevD1_RSI_35_55", h1_rebreak & d1_rsi_35_55),
    ]


def summarize_rules(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for sample_name, sample in samples.items():
        base_count = len(sample)
        rows.append(metric_row(sample_name, "baseline", sample, base_count))
        for rule_name, mask in rule_masks(sample):
            rows.append(metric_row(sample_name, rule_name, sample[mask.fillna(False)].copy(), base_count))
    summary = pd.DataFrame(rows)
    base = summary[summary["rule"].eq("baseline")][["sample", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]].rename(
        columns={
            "win_rate": "base_win_rate",
            "total_r": "base_total_r",
            "avg_r": "base_avg_r",
            "pf": "base_pf",
            "max_dd_r": "base_max_dd_r",
        }
    )
    summary = summary.merge(base, on="sample", how="left")
    summary["delta_win_rate"] = summary["win_rate"] - summary["base_win_rate"]
    summary["delta_total_r"] = summary["total_r"] - summary["base_total_r"]
    summary["delta_avg_r"] = summary["avg_r"] - summary["base_avg_r"]
    summary["delta_pf"] = summary["pf"] - summary["base_pf"]
    return summary.sort_values(["sample", "total_r", "pf"], ascending=[True, False, False])


def threshold_sweep(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for sample_name in ["practical_no_AUD_USD", "practical_core4"]:
        sample = samples[sample_name]
        for low in [25, 30, 35, 40]:
            for high in [50, 55, 60]:
                if low >= high:
                    continue
                for h4_filter_name, h4_mask in [
                    ("none", pd.Series(True, index=sample.index)),
                    ("quality", quality_mask(sample)),
                    ("strict", strict_mask(sample)),
                ]:
                    mask = sample["prev_d1_rsi14"].between(low, high) & h4_mask
                    row = {
                        "sample": sample_name,
                        "rsi_low": low,
                        "rsi_high": high,
                        "h4_filter": h4_filter_name,
                    }
                    row.update(metrics(sample[mask].copy(), R_COL))
                    row["pf"] = profit_factor(sample.loc[mask, R_COL].astype(float)) if bool(mask.any()) else math.nan
                    rows.append(row)
    return pd.DataFrame(rows).sort_values(["sample", "total_r", "pf"], ascending=[True, False, False])


def breakdown(sample: pd.DataFrame, rule_name: str, mask: pd.Series, by: str) -> pd.DataFrame:
    rows: list[dict] = []
    selected = sample[mask.fillna(False)].copy()
    for key, group in selected.groupby(by):
        row = {"rule": rule_name, by: key}
        row.update(metrics(group, R_COL))
        row["pf"] = profit_factor(group[R_COL].astype(float)) if len(group) else math.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["rule", "total_r"], ascending=[True, False])


def write_report(
    samples: dict[str, pd.DataFrame],
    summary: pd.DataFrame,
    sweep: pd.DataFrame,
    period_summary: pd.DataFrame,
    symbol_summary: pd.DataFrame,
    candidate_trades: pd.DataFrame,
) -> None:
    cols = [
        "sample",
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
    candidate_rules = [
        ("practical_no_AUD_USD", "baseline"),
        ("practical_no_AUD_USD", "prevD1_RSI_35_55"),
        ("practical_no_AUD_USD", "quality"),
        ("practical_no_AUD_USD", "strict"),
        ("practical_no_AUD_USD", "prevD1_RSI_35_55__quality"),
        ("practical_no_AUD_USD", "prevD1_RSI_35_55__strict"),
        ("practical_core4", "baseline"),
        ("practical_core4", "prevD1_RSI_35_55__strict"),
        ("practical_core4", "H1_LH_confirm"),
        ("practical_core4", "H1_LH_confirm__prevD1_RSI_35_55"),
        ("primary_core4_quality", "baseline"),
        ("primary_core4_quality", "prevD1_close_below_EMA50"),
    ]
    candidate_focus = []
    for sample_name, rule_name in candidate_rules:
        hit = summary[summary["sample"].eq(sample_name) & summary["rule"].eq(rule_name)]
        if not hit.empty:
            candidate_focus.append(hit.iloc[0])
    candidate_focus_df = pd.DataFrame(candidate_focus)

    useful = summary[
        ~summary["rule"].eq("baseline")
        & summary["trades"].ge(5)
        & summary["total_r"].gt(0)
        & summary["pf"].gt(summary["base_pf"])
        & summary["win_rate"].ge(summary["base_win_rate"])
    ].sort_values(["sample", "delta_total_r", "pf"], ascending=[True, False, False])

    period_cols = ["rule", "period", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    symbol_cols = ["rule", "symbol", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    sweep_cols = ["sample", "rsi_low", "rsi_high", "h4_filter", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    trade_cols = [
        "symbol",
        "entry_time",
        "period",
        R_COL,
        "prev_d1_rsi14",
        "support_age_bars",
        "break_depth_atr",
        "break_close_location",
        "lookback_bars",
        "pre_break_regime",
    ]

    lines = [
        "# H4 Low Stagnation Short: Previous D1 Regime Filter Study",
        "",
        "Status: 検証途中。H4安値停滞ショートに、前日確定の日足地合いを重ねる検証。",
        "",
        "## 結論候補",
        "",
        "- 最も実戦向きに見える追加条件は `前日D1 RSI 35-55`。",
        "- 意味: 日足は弱いが、まだ売られ過ぎすぎない状態だけを残す。",
        "- Pineでは未確定日足を使わず、`request.security(..., \"D\", ta.rsi(close, 14)[1])` の形にする。",
        "- H4側は既存の品質フィルタ `break_depth>=0.10ATR` と `break_close_location<=0.50` を重ねると強い。",
        "- さらに厳選するなら `support_age>10 or break_depth>=0.20ATR` を追加する。",
        "",
        "## 重要候補",
        "",
        markdown_table(candidate_focus_df[cols], 40) if not candidate_focus_df.empty else "_No rows._",
        "",
        "## 改善候補一覧",
        "",
        "ベースラインより勝率とPFが改善し、5件以上ある条件。",
        "",
        markdown_table(useful[cols], 80) if not useful.empty else "_No rows._",
        "",
        "## RSI閾値感度",
        "",
        markdown_table(sweep[sweep_cols].head(60), 80) if not sweep.empty else "_No rows._",
        "",
        "## 本線候補の期間別",
        "",
        markdown_table(period_summary[period_cols], 40) if not period_summary.empty else "_No rows._",
        "",
        "## 本線候補の通貨別",
        "",
        markdown_table(symbol_summary[symbol_cols], 40) if not symbol_summary.empty else "_No rows._",
        "",
        "## 本線候補のトレード一覧",
        "",
        markdown_table(candidate_trades[trade_cols], 40) if not candidate_trades.empty else "_No rows._",
        "",
        "## 暫定解釈",
        "",
        "- D1 RSI 35-55 は、日足が強すぎる局面と売られ過ぎの反発局面を同時に避けるフィルタとして働いている。",
        "- `practical_no_AUD_USD + D1 RSI35-55 + H4品質` は、37件から16件へ絞って、総R +8.36R -> +18.90R、PF 1.37 -> 5.56。",
        "- `strict` まで入れると、14件、勝率78.57%、PF 6.84。精度重視のPineラベル候補。",
        "- SILVERは過去の停滞型ショートでは弱かったが、この条件では3件全勝。最初はCore4版とSILVER込み版を別ラベルで比較するのが安全。",
        "- H1戻り高値切り下げとの重複は、精度タグとしては良いが7件まで減るため、最初から必須化しない。",
        "",
        "## 出力CSV",
        "",
        "- `enriched_with_prev_d1.csv`",
        "- `rule_summary.csv`",
        "- `threshold_sweep.csv`",
        "- `candidate_period_summary.csv`",
        "- `candidate_symbol_summary.csv`",
        "- `candidate_trades.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source = load_source()
    enriched = add_prev_d1_features(source, build_prev_d1_frames())
    samples = sample_sets(enriched)
    summary = summarize_rules(samples)
    sweep = threshold_sweep(samples)

    candidate_mask = (
        samples["practical_no_AUD_USD"]["prev_d1_rsi14"].between(35, 55)
        & strict_mask(samples["practical_no_AUD_USD"])
    )
    candidate_trades = samples["practical_no_AUD_USD"][candidate_mask].copy().sort_values("entry_time")
    period_summary = breakdown(samples["practical_no_AUD_USD"], "prevD1_RSI35_55__strict", candidate_mask, "period")
    symbol_summary = breakdown(samples["practical_no_AUD_USD"], "prevD1_RSI35_55__strict", candidate_mask, "symbol")

    enriched.to_csv(OUT_DIR / "enriched_with_prev_d1.csv", index=False)
    summary.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    sweep.to_csv(OUT_DIR / "threshold_sweep.csv", index=False)
    candidate_trades.to_csv(OUT_DIR / "candidate_trades.csv", index=False)
    period_summary.to_csv(OUT_DIR / "candidate_period_summary.csv", index=False)
    symbol_summary.to_csv(OUT_DIR / "candidate_symbol_summary.csv", index=False)
    write_report(samples, summary, sweep, period_summary, symbol_summary, candidate_trades)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    view = summary[
        summary["sample"].isin(["practical_no_AUD_USD", "practical_core4"])
        & summary["rule"].isin(
            [
                "baseline",
                "prevD1_RSI_35_55",
                "quality",
                "strict",
                "prevD1_RSI_35_55__quality",
                "prevD1_RSI_35_55__strict",
                "H1_LH_confirm",
                "H1_LH_confirm__prevD1_RSI_35_55",
            ]
        )
    ].copy()
    print(view[["sample", "rule", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]].to_string(index=False))


if __name__ == "__main__":
    main()

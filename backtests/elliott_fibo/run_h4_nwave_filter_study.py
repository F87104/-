#!/usr/bin/env python3
"""
Symmetric N-wave filter study for the H4 low-stagnation short setup.

The user-provided Pine indicator is treated as a shape detector. This script
ports the detector to Python, avoids lookahead by using the pivot confirmation
bar, and tests whether N-wave context improves the existing short setup.
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
OUT_DIR = THIS_DIR / "results_2026_05_28" / "h4_nwave_filter_study"
OUT_DIR.mkdir(parents=True, exist_ok=True)

R_COL = "base_r_after_cost"
TIMEFRAME = "H4"
NO_AUD_USD = {"GBPJPY", "CHFJPY", "XAUUSD", "EURJPY", "SILVER"}


@dataclass(frozen=True)
class NWaveSpec:
    piv_len: int
    n_waves: int
    amp_tol: float
    bar_tol: float
    min_bars: int = 3
    min_leg_atr: float = 0.0
    non_overlap: bool = True

    @property
    def name(self) -> str:
        overlap = "NOOV" if self.non_overlap else "OV"
        return (
            f"P{self.piv_len}_N{self.n_waves}_A{int(self.amp_tol)}"
            f"_B{int(self.bar_tol)}_ATR{self.min_leg_atr:g}_{overlap}"
        )


def load_source() -> pd.DataFrame:
    df = pd.read_csv(SOURCE)
    for col in ["signal_time", "entry_time", "base_exit_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def build_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        frames[symbol] = add_extended_features(add_indicators(resample_ohlc(raw, TIMEFRAME)))
    return frames


def is_pivot_high(high: np.ndarray, k: int, piv_len: int) -> bool:
    win = high[k - piv_len : k + piv_len + 1]
    return bool(np.isfinite(high[k]) and high[k] == np.nanmax(win))


def is_pivot_low(low: np.ndarray, k: int, piv_len: int) -> bool:
    win = low[k - piv_len : k + piv_len + 1]
    return bool(np.isfinite(low[k]) and low[k] == np.nanmin(win))


def detect_nwaves(df: pd.DataFrame, spec: NWaveSpec) -> pd.DataFrame:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)

    p_price: list[float] = []
    p_bar: list[int] = []
    p_high: list[bool] = []
    last_detect_end = -1
    rows: list[dict] = []

    for current_i in range(spec.piv_len * 2, len(df)):
        pivot_i = current_i - spec.piv_len
        npx = np.nan
        nhi: bool | None = None

        if is_pivot_high(high, pivot_i, spec.piv_len):
            npx = float(high[pivot_i])
            nhi = True
        elif is_pivot_low(low, pivot_i, spec.piv_len):
            npx = float(low[pivot_i])
            nhi = False

        if nhi is None or not math.isfinite(npx):
            continue

        if not p_price:
            p_price.append(npx)
            p_bar.append(pivot_i)
            p_high.append(nhi)
            continue

        last_high = p_high[-1]
        if nhi == last_high:
            last_p = p_price[-1]
            replace = npx > last_p if nhi else npx < last_p
            if replace:
                p_price[-1] = npx
                p_bar[-1] = pivot_i
            continue

        p_price.append(npx)
        p_bar.append(pivot_i)
        p_high.append(nhi)

        need = spec.n_waves + 1
        sz = len(p_price)
        if sz < need:
            continue

        base = sz - need
        if spec.non_overlap and base < last_detect_end:
            continue

        amps: list[float] = []
        bars: list[int] = []
        amp_atrs: list[float] = []
        for j in range(base, sz - 1):
            amp = abs(p_price[j + 1] - p_price[j])
            bar_span = p_bar[j + 1] - p_bar[j]
            amps.append(float(amp))
            bars.append(int(bar_span))
            atr_ref = atr[p_bar[j + 1]] if 0 <= p_bar[j + 1] < len(atr) else np.nan
            if math.isfinite(atr_ref) and atr_ref > 0:
                amp_atrs.append(float(amp / atr_ref))

        amp_min = min(amps) if amps else np.nan
        amp_max = max(amps) if amps else np.nan
        bar_min = min(bars) if bars else 0
        bar_max = max(bars) if bars else 0
        amp_ratio = amp_min / amp_max if amp_max and amp_max > 0 else 0.0
        bar_ratio = bar_min / bar_max if bar_max and bar_max > 0 else 0.0
        amp_min_atr = min(amp_atrs) if amp_atrs else np.nan

        amp_ok = amp_ratio >= 1.0 - spec.amp_tol / 100.0
        bar_ok = bar_ratio >= 1.0 - spec.bar_tol / 100.0
        size_ok = bar_min >= spec.min_bars and (spec.min_leg_atr <= 0 or (math.isfinite(amp_min_atr) and amp_min_atr >= spec.min_leg_atr))

        if amp_ok and bar_ok and size_ok:
            rows.append(
                {
                    "nwave_spec": spec.name,
                    "confirm_i": current_i,
                    "start_i": p_bar[base],
                    "end_i": p_bar[-1],
                    "ends_high": bool(p_high[-1]),
                    "amp_ratio": float(amp_ratio),
                    "bar_ratio": float(bar_ratio),
                    "amp_min_atr": float(amp_min_atr) if math.isfinite(amp_min_atr) else np.nan,
                    "total_bars": int(p_bar[-1] - p_bar[base]),
                    "end_price": float(p_price[-1]),
                }
            )
            last_detect_end = sz - 1

    return pd.DataFrame(rows)


def n_wave_specs() -> list[NWaveSpec]:
    specs: list[NWaveSpec] = []
    for piv_len in [3, 5, 8]:
        for n_waves in [3, 4]:
            for tol in [30.0, 45.0]:
                for min_leg_atr in [0.0, 0.5]:
                    for non_overlap in [True, False]:
                        specs.append(
                            NWaveSpec(
                                piv_len=piv_len,
                                n_waves=n_waves,
                                amp_tol=tol,
                                bar_tol=tol,
                                min_leg_atr=min_leg_atr,
                                non_overlap=non_overlap,
                            )
                        )
    return specs


def annotate_with_nwaves(sample: pd.DataFrame, detections: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for row in sample.to_dict("records"):
        symbol = str(row["symbol"])
        spec_name = str(row["nwave_spec"])
        d = detections.get((symbol, spec_name), pd.DataFrame())
        trigger_i = int(row["trigger_i"])
        break_i = int(row["break_i"])

        out = dict(row)
        out.update(
            {
                "nw_latest_age": np.nan,
                "nw_latest_ends_high": False,
                "nw_latest_high_age_le_120": False,
                "nw_latest_high_age_le_240": False,
                "nw_latest_high_age_le_480": False,
                "nw_latest_low_age_le_120": False,
                "nw_latest_low_age_le_240": False,
                "nw_latest_low_age_le_480": False,
                "nw_high_12": False,
                "nw_high_24": False,
                "nw_high_48": False,
                "nw_low_12": False,
                "nw_low_24": False,
                "nw_low_48": False,
                "nw_after_break_high": False,
                "nw_after_break_low": False,
                "nw_after_break_any": False,
                "nw_after_break_high_no_low": False,
                "nw_high_24_no_low_12": False,
                "nw_high_after_break_no_low_24": False,
            }
        )

        if d.empty:
            rows.append(out)
            continue

        before = d[d["confirm_i"].le(trigger_i)]
        if not before.empty:
            latest = before.iloc[-1]
            latest_age = int(trigger_i - latest["confirm_i"])
            latest_ends_high = bool(latest["ends_high"])
            out["nw_latest_age"] = latest_age
            out["nw_latest_ends_high"] = latest_ends_high
            for max_age in [120, 240, 480]:
                out[f"nw_latest_high_age_le_{max_age}"] = latest_ends_high and latest_age <= max_age
                out[f"nw_latest_low_age_le_{max_age}"] = (not latest_ends_high) and latest_age <= max_age

        for window in [12, 24, 48]:
            recent = before[before["confirm_i"].ge(trigger_i - window)] if not before.empty else before
            out[f"nw_high_{window}"] = bool(len(recent[recent["ends_high"]]) > 0)
            out[f"nw_low_{window}"] = bool(len(recent[~recent["ends_high"]]) > 0)

        after_break = d[d["confirm_i"].between(break_i, trigger_i)]
        high_after = bool(len(after_break[after_break["ends_high"]]) > 0)
        low_after = bool(len(after_break[~after_break["ends_high"]]) > 0)
        out["nw_after_break_high"] = high_after
        out["nw_after_break_low"] = low_after
        out["nw_after_break_any"] = bool(len(after_break) > 0)
        out["nw_after_break_high_no_low"] = high_after and not low_after
        out["nw_high_24_no_low_12"] = bool(out["nw_high_24"]) and not bool(out["nw_low_12"])
        out["nw_high_after_break_no_low_24"] = high_after and not bool(out["nw_low_24"])
        rows.append(out)

    return pd.DataFrame(rows)


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def metric_row(sample_name: str, spec_name: str, rule_name: str, sample: pd.DataFrame, base_count: int) -> dict:
    row = {"sample": sample_name, "nwave_spec": spec_name, "rule": rule_name, "base_trades": int(base_count)}
    row.update(metrics(sample, R_COL))
    row["coverage_pct"] = float(len(sample) / base_count * 100.0) if base_count else 0.0
    row["symbols"] = ",".join(sorted(sample["symbol"].unique())) if len(sample) else ""
    row["periods"] = ",".join(sorted(sample["period"].unique())) if len(sample) and "period" in sample.columns else ""
    row["pf"] = profit_factor(sample[R_COL].astype(float)) if len(sample) else math.nan
    return row


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


def summarize_rules(annotated: pd.DataFrame) -> pd.DataFrame:
    masks = [
        ("recent_high_12", lambda d: d["nw_high_12"]),
        ("recent_high_24", lambda d: d["nw_high_24"]),
        ("recent_high_48", lambda d: d["nw_high_48"]),
        ("recent_low_12", lambda d: d["nw_low_12"]),
        ("recent_low_24", lambda d: d["nw_low_24"]),
        ("no_recent_low_24", lambda d: ~d["nw_low_24"]),
        ("latest_high_age_le_120", lambda d: d["nw_latest_high_age_le_120"]),
        ("latest_high_age_le_240", lambda d: d["nw_latest_high_age_le_240"]),
        ("latest_high_age_le_480", lambda d: d["nw_latest_high_age_le_480"]),
        ("latest_low_age_le_120", lambda d: d["nw_latest_low_age_le_120"]),
        ("latest_low_age_le_240", lambda d: d["nw_latest_low_age_le_240"]),
        ("latest_low_age_le_480", lambda d: d["nw_latest_low_age_le_480"]),
        ("latest_low_age_25_240", lambda d: d["nw_latest_low_age_le_240"] & d["nw_latest_age"].gt(24)),
        ("latest_low_age_25_480", lambda d: d["nw_latest_low_age_le_480"] & d["nw_latest_age"].gt(24)),
        ("latest_low_age_49_240", lambda d: d["nw_latest_low_age_le_240"] & d["nw_latest_age"].gt(48)),
        ("latest_low_age_49_480", lambda d: d["nw_latest_low_age_le_480"] & d["nw_latest_age"].gt(48)),
        ("latest_high_240_no_low_24", lambda d: d["nw_latest_high_age_le_240"] & ~d["nw_low_24"]),
        ("latest_high_480_no_low_24", lambda d: d["nw_latest_high_age_le_480"] & ~d["nw_low_24"]),
        ("after_break_high", lambda d: d["nw_after_break_high"]),
        ("after_break_low", lambda d: d["nw_after_break_low"]),
        ("after_break_high_no_low", lambda d: d["nw_after_break_high_no_low"]),
        ("high_24_no_low_12", lambda d: d["nw_high_24_no_low_12"]),
        ("high_after_break_no_low_24", lambda d: d["nw_high_after_break_no_low_24"]),
        ("latest_is_high_unbounded", lambda d: d["nw_latest_ends_high"]),
    ]
    rows: list[dict] = []
    for (sample_name, spec_name), group in annotated.groupby(["sample", "nwave_spec"]):
        base_count = len(group)
        rows.append(metric_row(sample_name, spec_name, "baseline", group, base_count))
        for rule_name, fn in masks:
            mask = fn(group).fillna(False)
            rows.append(metric_row(sample_name, spec_name, rule_name, group[mask].copy(), base_count))
    out = pd.DataFrame(rows)
    base = out[out["rule"].eq("baseline")][["sample", "nwave_spec", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]].rename(
        columns={
            "win_rate": "base_win_rate",
            "total_r": "base_total_r",
            "avg_r": "base_avg_r",
            "pf": "base_pf",
            "max_dd_r": "base_max_dd_r",
        }
    )
    out = out.merge(base, on=["sample", "nwave_spec"], how="left")
    out["delta_win_rate"] = out["win_rate"] - out["base_win_rate"]
    out["delta_total_r"] = out["total_r"] - out["base_total_r"]
    out["delta_avg_r"] = out["avg_r"] - out["base_avg_r"]
    out["delta_pf"] = out["pf"] - out["base_pf"]
    return out.sort_values(["sample", "total_r", "pf"], ascending=[True, False, False])


def write_report(summaries: pd.DataFrame, annotated: pd.DataFrame) -> None:
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
        "nwave_spec",
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
        .sort_values(["sample", "nwave_spec"])
        .groupby("sample", as_index=False)
        .head(1)
        .copy()
    )
    useful = summaries[
        summaries["sample"].isin(focus_samples)
        & ~summaries["rule"].eq("baseline")
        & ~summaries["rule"].str.contains("unbounded")
        & summaries["trades"].ge(5)
        & summaries["total_r"].gt(0)
    ].copy()
    improved = useful[
        (useful["pf"] > useful["base_pf"])
        & (useful["win_rate"] >= useful["base_win_rate"])
        & (useful["coverage_pct"].between(20, 95))
    ].copy()
    top_useful = improved.sort_values(
        ["sample", "delta_total_r", "pf", "total_r"], ascending=[True, False, False, False]
    ).groupby("sample").head(8)

    primary_core4_quality = summaries[
        summaries["sample"].eq("primary_core4_quality")
        & ~summaries["rule"].eq("baseline")
        & ~summaries["rule"].str.contains("unbounded")
        & summaries["trades"].ge(3)
    ].sort_values(["pf", "total_r"], ascending=False).head(12)

    danger_rules = [
        "recent_low_12",
        "recent_low_24",
        "latest_low_age_le_120",
        "latest_low_age_le_240",
        "after_break_low",
    ]
    danger = summaries[
        summaries["sample"].isin(focus_samples)
        & summaries["rule"].isin(danger_rules)
        & summaries["trades"].between(2, 12)
    ].sort_values(["sample", "avg_r", "trades"], ascending=[True, True, False]).groupby("sample").head(8)

    stale_latest = summaries[
        summaries["sample"].isin(focus_samples)
        & summaries["rule"].eq("latest_is_high_unbounded")
        & summaries["trades"].ge(5)
        & summaries["pf"].gt(summaries["base_pf"])
    ].sort_values(["sample", "pf", "total_r"], ascending=[True, False, False]).groupby("sample").head(5)

    lines = [
        "# H4 Low-Stag Short N-Wave Filter Study",
        "",
        "Status: 検証途中。ユーザー提供の `Symmetric N-Wave Finder` をPythonへ移植し、H4安値停滞ショートの補助条件として使えるか確認。",
        "",
        "## 検証した使い方",
        "",
        "- `recent_high`: シグナル前に対称N波が高値で終わる。戻り売りの形が整った候補。",
        "- `recent_low`: シグナル前に対称N波が安値で終わる。下落が一度出尽くした可能性。",
        "- `latest_high_age_le_120/240/480`: 最新のN波が高値終了で、かつ検出から1から4か月相当以内。古すぎるN波を除外。",
        "- `after_break_high`: 1ヶ月安値ブレイク後からシグナル前までに、高値終了N波がある。",
        "- `high_after_break_no_low_24`: ブレイク後に高値終了N波があり、直近24本に安値終了N波がない。",
        "",
        "## 重要な実装注意",
        "",
        "- Pineのピボットは `pivLen` 本後に確定するため、Pythonでも `confirm_i <= trigger_i` のN波だけを使用。ラベル位置ではなく、確認バー基準でlookaheadを避けた。",
        "- `minAmp` は価格固定だと通貨間比較できないため、検証では `min_leg_atr` を追加してATR換算でも確認。",
        "- 表示用の `nonOverlap=true` は検出をかなり間引くため、戦略フィルタ用には `nonOverlap=false` も同時に検証した。",
        "- 件数が少ないため、N波は現時点では単独エントリー条件ではなく、まず観察タグ・警戒タグ候補。",
        "",
        "## ベースライン",
        "",
        markdown_table(baseline[cols], 20) if not baseline.empty else "_No rows._",
        "",
        "## サンプル別 改善候補",
        "",
        "PFと勝率がベースライン以上、かつカバー率20から95%の条件だけを表示。",
        "",
        markdown_table(top_useful[cols], 50) if not top_useful.empty else "_No rows._",
        "",
        "## 本命 primary_core4_quality の候補",
        "",
        markdown_table(primary_core4_quality[cols], 80) if not primary_core4_quality.empty else "_No rows._",
        "",
        "## 警戒タグ候補",
        "",
        "安値で終わるN波は、下落が一度出尽くした可能性として確認。件数が少ないものは即採用しない。",
        "",
        markdown_table(danger[cols], 50) if not danger.empty else "_No rows._",
        "",
        "## 古すぎる可能性がある条件",
        "",
        "`latest_is_high_unbounded` は見た目の成績が良くても、検出から数百から数千本後のトレードを含むため、実戦条件にはしない。",
        "",
        markdown_table(stale_latest[cols], 30) if not stale_latest.empty else "_No rows._",
        "",
        "## Pineでまず試す条件",
        "",
        "1. N波設定は `pivLen=3`, `nWaves=3`, `ampTol=45`, `barTol=45`, `minLegAtr=0.5`, `nonOverlap=true` を最初の本線にする。",
        "2. 強い観察タグは `latest_low_age_49_240`: 最新N波が安値終了で、検出から49から240本経過。広いPractical core4では 9 trades / 77.78% / +11.73R / PF 6.74。",
        "3. 注意タグは `recent_low_24`: 最新または直近の安値終了N波が24本以内。これは下落直後すぎて戻りリスクがあり、Practical core4では 3 trades / -0.13R / PF 0.94。",
        "4. `latest_high` 系は高値終了の戻り売りタグとして期待したが、年齢制限なしでは古すぎ、年齢制限ありでは件数不足または悪化。現段階では採用しない。",
        "5. `support_age 60-119` は単体で強く、N波でさらに良くなるというより、別々の強い観察タグとして並べて見る。",
        "",
        "## 暫定解釈",
        "",
        "- まず見るべきは、`primary_core4_quality` と `practical_core4` の両方で悪化しない条件。",
        "- `latest_is_high_unbounded` は古すぎる検出を含むため、採用するなら必ず年齢制限を付ける。",
        "- `recent_low` 系が弱ければ、エントリー除外ではなく半ロット・注意表示から試す。",
        "- `after_break_high` 系は件数が足りない場合、エントリー条件にせずPine表示だけに留める。",
        "",
        "## 出力CSV",
        "",
        "- `annotated_trades.csv`",
        "- `rule_summary.csv`",
        "- `../../../pine/visual/h4_nwave_filter_probe.pine`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    enriched = load_source()
    frames = build_frames()
    specs = n_wave_specs()

    detections: dict[tuple[str, str], pd.DataFrame] = {}
    for spec in specs:
        for symbol, frame in frames.items():
            detections[(symbol, spec.name)] = detect_nwaves(frame, spec)

    annotated_frames: list[pd.DataFrame] = []
    samples = sample_sets(enriched)
    for sample_name, sample in samples.items():
        if sample.empty:
            continue
        for spec in specs:
            work = sample.copy()
            work["sample"] = sample_name
            work["nwave_spec"] = spec.name
            annotated_frames.append(annotate_with_nwaves(work, detections))

    annotated = pd.concat(annotated_frames, ignore_index=True) if annotated_frames else pd.DataFrame()
    summaries = summarize_rules(annotated) if not annotated.empty else pd.DataFrame()

    annotated.to_csv(OUT_DIR / "annotated_trades.csv", index=False)
    summaries.to_csv(OUT_DIR / "rule_summary.csv", index=False)
    write_report(summaries, annotated)
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    if not summaries.empty:
        print(summaries[summaries["sample"].eq("primary_core4_quality")].head(20).to_string(index=False))


if __name__ == "__main__":
    main()

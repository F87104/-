#!/usr/bin/env python3
"""
Elliott wave-5 filter improvement study.

This script starts from the reproducible W5_CLASSIC event set and tests
filters that should remove exhausted wave-5 candidates. It intentionally keeps
the study separate from the detector so that filter performance can be audited
without changing the event definition.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_EVENTS = REPO_ROOT / "docs" / "research" / "elliott_wave5_reproducibility_2026-06-09" / "events_all.csv"
OUT_DIR = REPO_ROOT / "docs" / "research" / "elliott_wave5_filter_improvement_2026-06-09"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESEARCH = "Research_2015_2024"
OOS = "OOS_2025_2026"


def profit_factor(r_values: pd.Series) -> float:
    gains = float(r_values[r_values > 0].sum())
    losses = float(-r_values[r_values < 0].sum())
    if losses == 0:
        return math.inf if gains > 0 else 0.0
    return gains / losses


def max_drawdown(r_values: pd.Series) -> float:
    equity = r_values.cumsum()
    peak = equity.cummax()
    return float((peak - equity).max()) if len(r_values) else 0.0


def max_losing_streak(r_values: pd.Series) -> int:
    streak = 0
    max_streak = 0
    for value in r_values:
        if value < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def summarize(df: pd.DataFrame, variant: str, period: str) -> dict:
    x = df[df["period"].eq(period)].sort_values("entry_time")
    r = x["r_result_2r"]
    return {
        "variant": variant,
        "period": period,
        "events": int(len(x)),
        "win_rate_2r": float((x["outcome_2r"].eq(1).mean() * 100) if len(x) else 0),
        "sl_rate": float((x["exit_reason"].eq("SL").mean() * 100) if len(x) else 0),
        "pf_2r": profit_factor(r),
        "avg_r_2r": float(r.mean()) if len(x) else 0,
        "total_r_2r": float(r.sum()) if len(x) else 0,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "avg_mfe_120": float(x["mfe_120"].mean()) if len(x) else 0,
        "avg_mae_120": float(x["mae_120"].mean()) if len(x) else 0,
        "median_wave3_vs_wave1": float(x["wave3_vs_wave1"].median()) if len(x) else 0,
        "median_wave2_retrace": float(x["wave2_retrace"].median()) if len(x) else 0,
        "median_entry_over_wave3": float(x["entry_over_wave3"].median()) if len(x) else 0,
    }


def pivot_summary(summary: pd.DataFrame) -> pd.DataFrame:
    cols = ["events", "win_rate_2r", "pf_2r", "avg_r_2r", "total_r_2r", "max_dd_r", "avg_mfe_120", "avg_mae_120"]
    pivot = summary.pivot(index="variant", columns="period", values=cols)
    pivot.columns = [f"{period}_{metric}" for metric, period in pivot.columns]
    return pivot.reset_index()


def fmt(value: float) -> str:
    if isinstance(value, float) and math.isinf(value):
        return "inf"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "(none)"
    show = df.head(max_rows).copy()
    headers = list(show.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(fmt(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def add_variant(variants: list[tuple[str, str, pd.Series]], name: str, note: str, mask: pd.Series) -> None:
    variants.append((name, note, mask))


def build_variants(df: pd.DataFrame) -> list[tuple[str, str, pd.Series]]:
    variants: list[tuple[str, str, pd.Series]] = []
    all_mask = pd.Series(True, index=df.index)
    add_variant(variants, "BASE_W5_CLASSIC", "Classic W5全体。改善前の比較基準。", all_mask)
    add_variant(variants, "LONG_ONLY", "ショートを除外。5波ロングだけを見る。", df["direction"].eq("long"))
    add_variant(variants, "W3_CAP_1_2", "3波伸び切り除外。wave3/wave1 <= 1.2。", df["wave3_vs_wave1"].le(1.2))
    add_variant(variants, "W3_CAP_1_3", "やや緩い3波伸び切り除外。wave3/wave1 <= 1.3。", df["wave3_vs_wave1"].le(1.3))
    add_variant(variants, "W2_SHALLOW_0382", "2波が浅い候補だけ。wave2 <= 0.382。", df["wave2_retrace"].le(0.382))
    add_variant(variants, "W2_MODERATE_0618", "2波が深すぎない候補。wave2 <= 0.618。", df["wave2_retrace"].le(0.618))
    add_variant(variants, "EARLY_BREAK_005", "3波高値/安値を大きく抜けた後を追わない。entry_over_wave3 <= 0.05。", df["entry_over_wave3"].le(0.05))
    add_variant(variants, "LONG_W3_CAP_1_2", "ロング + 3波伸び切り除外。", df["direction"].eq("long") & df["wave3_vs_wave1"].le(1.2))
    add_variant(
        variants,
        "LONG_W3_CAP_W2_MOD",
        "ロング + 3波伸び切り除外 + 2波深戻し除外。",
        df["direction"].eq("long") & df["wave3_vs_wave1"].le(1.2) & df["wave2_retrace"].le(0.618),
    )
    add_variant(
        variants,
        "LONG_W3_CAP_W2_MOD_EARLY",
        "厳しすぎる比較用。ロング + 3波<=1.2 + 2波<=0.618 + 早いブレイクだけ。",
        df["direction"].eq("long")
        & df["wave3_vs_wave1"].le(1.2)
        & df["wave2_retrace"].le(0.618)
        & df["entry_over_wave3"].le(0.05),
    )
    add_variant(
        variants,
        "H4_XAU_EUR_USD_W2_MOD_PREATR3",
        "OOSが崩れにくかった狭い候補。H4 + XAU/EUR/USD + wave2<=0.618 + preBreak>=3ATR。",
        df["timeframe"].eq("H4")
        & df["symbol"].isin(["XAUUSD", "EURJPY", "USDJPY"])
        & df["wave2_retrace"].le(0.618)
        & df["pre_break_range_atr"].ge(3),
    )
    add_variant(
        variants,
        "XAU_W3_CAP_1_3",
        "XAUUSD限定 + 3波伸び切り除外。件数は少ないがOOSで崩れにくい。",
        df["symbol"].eq("XAUUSD") & df["wave3_vs_wave1"].le(1.3),
    )
    add_variant(
        variants,
        "H1_STRONG_SYMBOLS",
        "過去は強いがOOSで崩れる疑いの比較用。H1 + EURJPY/USDJPY/SILVER。",
        df["timeframe"].eq("H1") & df["symbol"].isin(["EURJPY", "USDJPY", "SILVER"]),
    )
    return variants


def search_filters(df: pd.DataFrame) -> pd.DataFrame:
    atomics: list[tuple[str, pd.Series]] = [
        ("tf=H4", df["timeframe"].eq("H4")),
        ("tf=H1", df["timeframe"].eq("H1")),
        ("long", df["direction"].eq("long")),
        ("sym=XAU/EUR/USD", df["symbol"].isin(["XAUUSD", "EURJPY", "USDJPY"])),
        ("sym=XAU", df["symbol"].eq("XAUUSD")),
        ("w3<=1.2", df["wave3_vs_wave1"].le(1.2)),
        ("w3<=1.3", df["wave3_vs_wave1"].le(1.3)),
        ("w2<=0.382", df["wave2_retrace"].le(0.382)),
        ("w2<=0.618", df["wave2_retrace"].le(0.618)),
        ("w4<=0.5", df["wave4_retrace"].le(0.5)),
        ("early<=0.05", df["entry_over_wave3"].le(0.05)),
        ("preATR>=3", df["pre_break_range_atr"].ge(3)),
        ("preATR<=5", df["pre_break_range_atr"].le(5)),
    ]
    rows: list[dict] = []
    n = len(atomics)
    for bits in range(1, 1 << n):
        if bin(bits).count("1") > 4:
            continue
        mask = pd.Series(True, index=df.index)
        names = []
        for i in range(n):
            if bits & (1 << i):
                names.append(atomics[i][0])
                mask &= atomics[i][1]
        x = df[mask]
        r = x[x["period"].eq(RESEARCH)]
        o = x[x["period"].eq(OOS)]
        if len(r) < 20 or len(o) < 5:
            continue
        r_stats = summarize(x, "x", RESEARCH)
        o_stats = summarize(x, "x", OOS)
        if r_stats["pf_2r"] <= 1.0:
            continue
        rows.append({
            "filter": " + ".join(names),
            "research_events": r_stats["events"],
            "research_wr": r_stats["win_rate_2r"],
            "research_pf": r_stats["pf_2r"],
            "research_avg_r": r_stats["avg_r_2r"],
            "research_total_r": r_stats["total_r_2r"],
            "oos_events": o_stats["events"],
            "oos_wr": o_stats["win_rate_2r"],
            "oos_pf": o_stats["pf_2r"],
            "oos_avg_r": o_stats["avg_r_2r"],
            "oos_total_r": o_stats["total_r_2r"],
            "score": min(r_stats["pf_2r"], 3.0) + min(o_stats["pf_2r"], 3.0) + r_stats["avg_r_2r"] + o_stats["avg_r_2r"],
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["oos_pf", "research_pf", "oos_avg_r"], ascending=False)


def build_report(summary: pd.DataFrame, pivot: pd.DataFrame, search: pd.DataFrame, notes: dict[str, str]) -> str:
    cols = [
        "variant",
        f"{RESEARCH}_events",
        f"{RESEARCH}_win_rate_2r",
        f"{RESEARCH}_pf_2r",
        f"{RESEARCH}_avg_r_2r",
        f"{OOS}_events",
        f"{OOS}_win_rate_2r",
        f"{OOS}_pf_2r",
        f"{OOS}_avg_r_2r",
    ]
    compact = pivot[cols].copy()
    compact["note"] = compact["variant"].map(notes)
    compact = compact.sort_values([f"{OOS}_pf_2r", f"{RESEARCH}_pf_2r"], ascending=False)

    lines = [
        "# Elliott 5波 フィルター改善検証 v0.2",
        "",
        "作成日: 2026-06-09",
        "",
        "## 研究の問い",
        "",
        "Classic W5の勝率/PFが悪すぎるため、伸び切った5波候補を捨てるフィルターで改善できるか。",
        "",
        "## 結論",
        "",
        "- ベースのClassic W5は、OOSで勝率12.00%、PF0.48まで崩れる。",
        "- 最重要フィルターは `wave3 / wave1 <= 1.2`。3波が強すぎるほど5波余地が残らない可能性がある。",
        "- 本線候補は `LONG_W3_CAP_W2_MOD`: 研究期間46件、勝率39.13%、PF1.97。OOS8件、勝率37.50%、PF1.20。",
        "- `wave2 <= 0.382` は研究期間PF2.02だが、OOS件数が3件で不足。",
        "- `entry_over_wave3 <= 0.05` は単独の注意ラベルとして使う。必須にすると件数が減り、OOSが弱い。",
        "- H4 + XAU/EUR/USD + `wave2 <= 0.618` + `preBreak >= 3ATR` はOOSが良いが、OOS6件しかないため本番採用しない。",
        "- v0.2は売買ルールではなく、TradingViewで目視照合するEvent scanner候補に留める。",
        "",
        "## 主要フィルター比較",
        "",
        markdown_table(compact, 40),
        "",
        "## 自動探索 上位候補",
        "",
        markdown_table(search[[
            "filter",
            "research_events",
            "research_wr",
            "research_pf",
            "research_avg_r",
            "oos_events",
            "oos_wr",
            "oos_pf",
            "oos_avg_r",
        ]], 30),
        "",
        "## 採用しない条件",
        "",
        "- `H1_STRONG_SYMBOLS`: 研究期間はPFが高いが、OOSで崩れるため過去最適化疑い。",
        "- `wave3 / wave1 >= 1.5` のような3波強すぎ条件: 5波狙いではなく、すでに伸び切った場所を追いやすい。",
        "- ショート5波: 研究期間/OOSともに弱く、現段階では除外。",
        "",
        "## v0.2 仮ルール案",
        "",
        "```text",
        "Elliott W5 v0.2 Event scanner",
        "",
        "必須:",
        "- Classic W5",
        "- long only",
        "- wave3 / wave1 <= 1.2",
        "- wave2 retrace <= 0.618",
        "",
        "注意ラベル:",
        "- wave2 <= 0.382 は強候補。ただし件数不足",
        "- entry_over_wave3 <= 0.05 は飛び乗り抑制",
        "- H4 XAUUSD/EURJPY/USDJPY は優先観察",
        "",
        "禁止:",
        "- 3波が伸び切った後の5波追い",
        "- H1過去成績だけを根拠にした本番化",
        "- ショート5波の単独採用",
        "```",
        "",
        "## 次のアクション",
        "",
        "1. `W3_CAP_1_2` と `LONG_W3_CAP_W2_MOD` の代表20件をTradingViewで目視照合する。",
        "2. H4 XAU/EUR/USD候補は件数が少ないため、候補位置だけをスクショで確認する。",
        "3. Pine化する場合はENTRYではなく、`W5候補`, `3波伸び切り注意`, `2波浅い強候補` の3ラベルに分ける。",
        "",
        "## 出力",
        "",
        "- variant_summary.csv",
        "- variant_pivot.csv",
        "- top_filter_search.csv",
        "- v0_2_candidate_events.csv",
        "- REPORT_ja.md",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    events = pd.read_csv(INPUT_EVENTS)
    events = events[events["method"].eq("W5_CLASSIC")].copy()
    events["entry_time"] = pd.to_datetime(events["entry_time"], errors="coerce")
    variants = build_variants(events)

    summary_rows = []
    notes = {}
    candidate_events = []
    for name, note, mask in variants:
        notes[name] = note
        x = events[mask].copy()
        x["variant"] = name
        summary_rows.append(summarize(x, name, RESEARCH))
        summary_rows.append(summarize(x, name, OOS))
        if name in {"W3_CAP_1_2", "LONG_W3_CAP_W2_MOD", "H4_XAU_EUR_USD_W2_MOD_PREATR3", "XAU_W3_CAP_1_3"}:
            candidate_events.append(x)

    summary = pd.DataFrame(summary_rows)
    pivot = pivot_summary(summary)
    search = search_filters(events)
    candidates = pd.concat(candidate_events, ignore_index=True).drop_duplicates(
        ["variant", "symbol", "timeframe", "direction", "entry_time"]
    )

    summary.to_csv(OUT_DIR / "variant_summary.csv", index=False)
    pivot.to_csv(OUT_DIR / "variant_pivot.csv", index=False)
    search.to_csv(OUT_DIR / "top_filter_search.csv", index=False)
    candidates.to_csv(OUT_DIR / "v0_2_candidate_events.csv", index=False)
    report = build_report(summary, pivot, search, notes)
    (OUT_DIR / "REPORT_ja.md").write_text(report, encoding="utf-8")

    print(markdown_table(
        pivot[[
            "variant",
            f"{RESEARCH}_events",
            f"{RESEARCH}_win_rate_2r",
            f"{RESEARCH}_pf_2r",
            f"{OOS}_events",
            f"{OOS}_win_rate_2r",
            f"{OOS}_pf_2r",
        ]].sort_values([f"{OOS}_pf_2r", f"{RESEARCH}_pf_2r"], ascending=False),
        20,
    ))
    print(f"wrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

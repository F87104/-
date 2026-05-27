#!/usr/bin/env python3
"""
Red-team audit for USDJPY H1 WaveBox Rebreak.

The goal is not to improve the strategy. It looks for reasons the result may be
too good: lookahead-like defects, fragile filters, small samples, and period
dependence.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BASE_DIR = THIS_DIR / "results_2026_05_25"
PRACTICAL_DIR = BASE_DIR / "usdjpy_v1_practical_audit"
QUALITY_DIR = BASE_DIR / "quality_axes_audit"
OUT_DOC = REPO_ROOT / "docs" / "wavebox_red_team_audit_2026-05-26.md"
OUT_CSV = REPO_ROOT / "outputs" / "wavebox_forward_validation" / "wavebox_red_team_audit_summary.csv"

sys.path.insert(0, str(THIS_DIR))
import audit_wavebox_usdjpy_v1_practical as practical  # noqa: E402


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(values[values <= 0].sum())
    if gross_loss < 0:
        return gross_profit / abs(gross_loss)
    return math.inf if gross_profit > 0 else math.nan


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    curve = values.cumsum()
    return float((curve.cummax() - curve).max())


def summarize(label: str, df: pd.DataFrame) -> dict:
    r = df["r_after_cost"] if "r_after_cost" in df.columns else pd.Series(dtype=float)
    return {
        "label": label,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else math.nan,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else math.nan,
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
    }


def wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    phat = wins / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half) * 100.0, min(1.0, center + half) * 100.0


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.itertuples(index=False, name=None)]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]
    )


def integrity_checks(strict: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rows.append({"check": "entry_i == signal_i + 1", "bad_count": int((strict["entry_i"] != strict["signal_i"] + 1).sum())})
    rows.append({"check": "setup_age >= 0", "bad_count": int((strict["setup_age"] < 0).sum())})
    rows.append({"check": "risk > 0", "bad_count": int((strict["risk"] <= 0).sum())})

    long_bad = (strict["direction"].eq("long") & (strict["stop"] >= strict["entry"])).sum()
    short_bad = (strict["direction"].eq("short") & (strict["stop"] <= strict["entry"])).sum()
    rows.append({"check": "stop is on correct side", "bad_count": int(long_bad + short_bad)})

    target_expected = np.where(
        strict["direction"].eq("long"),
        strict["entry"] + strict["risk"] * 1.5,
        strict["entry"] - strict["risk"] * 1.5,
    )
    target_error = np.abs(strict["target"].to_numpy(dtype=float) - target_expected)
    rows.append({"check": "target equals 1.5R from next open", "bad_count": int((target_error > 1e-9).sum())})

    sorted_trades = strict.sort_values("entry_i")
    overlap = 0
    last_exit = -1
    for trade in sorted_trades.itertuples(index=False):
        if int(trade.entry_i) <= last_exit:
            overlap += 1
        last_exit = max(last_exit, int(trade.exit_i))
    rows.append({"check": "no overlapping strict trades", "bad_count": overlap})
    rows.append({"check": "same-bar TP/SL counted as SL", "bad_count": int(strict["exit_reason"].eq("SL_first_same_bar").sum())})
    return pd.DataFrame(rows)


def main() -> None:
    strict = pd.read_csv(PRACTICAL_DIR / "trades_standard_v1_wave1_quality.csv", parse_dates=["entry_time"])
    quality = pd.read_csv(QUALITY_DIR / "trades_strict_quality_axes.csv", parse_dates=["entry_time"])
    base = practical.load_base()

    variants = {
        "Strict no hour filter": {"retrace": (0.50, 0.786), "exclude_hours": [], "h4": "any", "direction": "both", "wave1_quality": True},
        "Strict exclude 1": {"retrace": (0.50, 0.786), "exclude_hours": [1], "h4": "any", "direction": "both", "wave1_quality": True},
        "Strict exclude 1/6": {"retrace": (0.50, 0.786), "exclude_hours": [1, 6], "h4": "any", "direction": "both", "wave1_quality": True},
        "Strict exclude 1/6/14": {"retrace": (0.50, 0.786), "exclude_hours": [1, 6, 14], "h4": "any", "direction": "both", "wave1_quality": True},
    }
    variant_summary = pd.DataFrame([summarize(name, practical.apply_candidate(base, spec)) for name, spec in variants.items()])

    go = quality[quality["action_class"].isin(["GO_A_PLUS", "GO_CLEAN_A"])].copy()
    period_summary = pd.DataFrame(
        [
            summarize("Strict all", strict),
            summarize("Strict 2014-2022", strict[strict["entry_time"] < pd.Timestamp("2023-01-01")]),
            summarize("Strict 2023+", strict[strict["entry_time"] >= pd.Timestamp("2023-01-01")]),
            summarize("GO A+ or clean A", go),
            summarize("GO only pre-2023", go[go["entry_time"] < pd.Timestamp("2023-01-01")]),
            summarize("GO only 2023+", go[go["entry_time"] >= pd.Timestamp("2023-01-01")]),
        ]
    )

    ci_rows = []
    for label, df in [
        ("Strict all", strict),
        ("GO A+ or clean A", go),
        ("GO only pre-2023", go[go["entry_time"] < pd.Timestamp("2023-01-01")]),
        ("Strict OOS 2025-2026", strict[strict["entry_time"] >= pd.Timestamp("2025-01-01")]),
    ]:
        wins = int((df["r_after_cost"] > 0).sum())
        n = int(len(df))
        lo, hi = wilson_interval(wins, n)
        ci_rows.append({"label": label, "wins": wins, "trades": n, "win_rate": (wins / n * 100.0) if n else math.nan, "wilson_95_low": lo, "wilson_95_high": hi})
    ci = pd.DataFrame(ci_rows)

    exit_counts = strict["exit_reason"].value_counts().rename_axis("exit_reason").reset_index(name="trades")
    checks = integrity_checks(strict)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(
        [
            variant_summary.assign(section="hour_filter"),
            period_summary.assign(section="period"),
        ],
        ignore_index=True,
    ).to_csv(OUT_CSV, index=False)

    lines = [
        "# WaveBox Red-Team Audit 2026-05-26",
        "",
        "## 結論",
        "",
        "結果は良いが、そのまま実力値として信じない。",
        "",
        "コード上の明確な未来参照・同足ENTRY・TP優先の過大評価は見つからない。一方で、成績は時間フィルターと近年相場に強く支えられている。特にOOS 2025-2026は6件だけで、全勝しているため統計的な証拠としては弱い。",
        "",
        "## Passed Integrity Checks",
        "",
        markdown_table(checks),
        "",
        "## Hour Filter Dependence",
        "",
        markdown_table(variant_summary),
        "",
        "## Period Dependence",
        "",
        markdown_table(period_summary),
        "",
        "## Win-Rate Confidence",
        "",
        markdown_table(ci),
        "",
        "## Exit Count",
        "",
        markdown_table(exit_counts),
        "",
        "## Red Flags",
        "",
        "- 時間フィルターなしでは `Strict` はPF1.50まで落ちる。つまり1時/6時/14時除外の寄与が大きい。",
        "- 2023年以降がかなり良すぎる。近年のUSDJPYトレンド環境に適合している可能性がある。",
        "- `GO A+ or clean A` は38件しかなく、95%信頼区間は広い。",
        "- 2025-2026のOOSは6件全勝だが、件数が少なく、実戦証拠にはならない。",
        "- この手法は作成過程で複数条件を見ているため、厳密な未使用OOSではない。",
        "",
        "## Practical Verdict",
        "",
        "- 実装ミスで勝っている疑いは低め。",
        "- ただし結果は過信禁止。実力値はPF3ではなく、まずPF1.5-2.0程度に割り引いて見る。",
        "- 実弾は `GO A+ / GO A` の20-30件フォワードが取れるまで小ロット。",
        "- 20件まではパラメータ変更禁止。変更すると検証がまた最初からになる。",
    ]
    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {OUT_DOC}")
    print(checks.to_string(index=False))
    print(variant_summary.to_string(index=False))
    print(period_summary.to_string(index=False))
    print(ci.to_string(index=False))


if __name__ == "__main__":
    main()

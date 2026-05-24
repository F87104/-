#!/usr/bin/env python3
"""
Fast fakeout study runner.

Pre-entry filters are evaluated as a baseline-trade subset analysis, which is
useful for discovering fakeout-prone shapes quickly. Confirmation filters are
still re-simulated because their entry timing changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "fakeout_feature_study_fast_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(THIS_DIR))

import run_fakeout_feature_study as study  # noqa: E402

study.OUT_DIR = OUT_DIR


def subset_by_filter(baseline: pd.DataFrame, func) -> pd.DataFrame:
    if baseline.empty:
        return baseline.copy()
    mask = baseline.apply(lambda row: bool(func(row)), axis=1)
    return baseline[mask].copy()


def main() -> None:
    print("Running baseline feature extraction...")
    baseline = study.run_all("baseline")
    baseline.to_csv(OUT_DIR / "baseline_trades_with_features.csv", index=False)
    print(pd.Series(study.summarize_trades(baseline)).to_string())

    single_rows = []
    for name, category, func in study.filter_definitions():
        print(f"Subset filter: {name}")
        df = subset_by_filter(baseline, func)
        df = df.copy()
        df["filter_name"] = name
        single_rows.extend(study.summarize_by_symbol(df, name, category))
    single = pd.DataFrame(single_rows)
    single.to_csv(OUT_DIR / "single_filter_sweep.csv", index=False)

    combo_rows = []
    for name, category, func in study.combo_definitions():
        print(f"Subset combo: {name}")
        df = subset_by_filter(baseline, func)
        df = df.copy()
        df["filter_name"] = name
        combo_rows.extend(study.summarize_by_symbol(df, name, category))
    combos = pd.DataFrame(combo_rows)
    combos.to_csv(OUT_DIR / "combo_filter_results.csv", index=False)

    confirm_specs = [
        ("confirm_1_close_outside", 1, False),
        ("confirm_1_close_outside_and_follow", 1, True),
        ("confirm_2_closes_outside", 2, False),
        ("confirm_2_closes_outside_and_follow", 2, True),
        ("confirm_3_closes_outside", 3, False),
    ]
    confirm_rows = []
    for name, bars, follow in confirm_specs:
        print(f"Re-sim confirmation: {name}")
        df = study.run_all(name, None, confirm_bars=bars, confirm_follow=follow)
        confirm_rows.extend(study.summarize_by_symbol(df, name, "確認型"))
    confirms = pd.DataFrame(confirm_rows)
    confirms.to_csv(OUT_DIR / "confirmation_filter_results.csv", index=False)

    buckets = study.feature_buckets(baseline)
    buckets.to_csv(OUT_DIR / "feature_bucket_summary.csv", index=False)
    study.write_report(baseline, single, combos, confirms, buckets)

    with (OUT_DIR / "report_ja.md").open("a", encoding="utf-8") as f:
        f.write(
            "\n\n## 高速版の注意\n\n"
            "- 単独フィルタと複合フィルタは、ベースラインで実際に入ったトレードを特徴量で分類した一次評価です。\n"
            "- つまり、フィルタで見送ったあとに後続シグナルへ入り直す効果はここには含めていません。\n"
            "- 確認型フィルタだけは、待機後の次足始値で入り直す形で再シミュレーションしています。\n"
        )

    print("\nTop single subset filters (ALL):")
    print(
        single[single["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        .head(12)
        [["filter_name", "category", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print("\nCombo subset filters (ALL):")
    print(
        combos[combos["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        [["filter_name", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print("\nConfirmation filters (ALL):")
    print(
        confirms[confirms["symbol"] == "ALL"]
        .sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        [["filter_name", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "quick_back_inside_3_rate"]]
        .to_string(index=False)
    )
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

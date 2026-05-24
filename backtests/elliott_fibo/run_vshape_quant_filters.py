#!/usr/bin/env python3
"""
Post-study quantification for sharp-drop V recoveries.

This reads results_2015_2024/trades.csv produced by run_elliott_fibo_study.py
and summarizes which measurable V-shape features are useful.

Important: this is a feature study on already generated trades. It is useful
for defining the next scanner rules, but final production numbers should be
confirmed by adding the chosen filters to the entry logic and rerunning.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
IN_PATH = THIS_DIR / "results_2015_2024" / "trades.csv"
OUT_DIR = THIS_DIR / "results_2015_2024" / "vshape_quant"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    curve = values.cumsum()
    peak = curve.cummax()
    return float((peak - curve).max())


def profit_factor(values: pd.Series) -> float:
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(values[values <= 0].sum())
    if gross_loss < 0:
        return gross_profit / abs(gross_loss)
    return math.inf if gross_profit > 0 else math.nan


def summarize(group: pd.DataFrame, label: str) -> dict:
    r = group["r_after_cost"]
    return {
        "filter": label,
        "trades": int(len(group)),
        "win_rate": float((r > 0).mean() * 100) if len(group) else math.nan,
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()) if len(group) else math.nan,
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
    }


def fmt(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.2f}"


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(fmt)
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.itertuples(index=False, name=None)]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(row) + " |" for row in rows],
        ]
    )


def main() -> None:
    trades = pd.read_csv(IN_PATH, parse_dates=["entry_time"])
    vtrades = trades[trades["family"] == "V字フィボ"].copy()
    vtrades = vtrades.sort_values("entry_time")

    focus = vtrades[
        (vtrades["timeframe"].isin(["H1", "H4", "D1"]))
        & (vtrades["strategy"].isin(["VFIB_618_RR2", "VFIB_618_BODY50_RR2", "VFIB_618_BODY60_RR2"]))
    ].copy()

    fixed_filters = [
        ("全V字", lambda x: pd.Series(True, index=x.index)),
        ("買いのみ: 急落後V字", lambda x: x["direction"].eq("long")),
        ("買いのみ + 実体50%以上", lambda x: x["direction"].eq("long") & x["strategy"].eq("VFIB_618_BODY50_RR2")),
        ("買いのみ + 実体60%以上", lambda x: x["direction"].eq("long") & x["strategy"].eq("VFIB_618_BODY60_RR2")),
        ("買いのみ + 回復本数 <= 下落本数", lambda x: x["direction"].eq("long") & (x["v_recovery_to_drop_bars"] <= 1.0)),
        ("買いのみ + 回復本数 <= 下落本数 x1.5", lambda x: x["direction"].eq("long") & (x["v_recovery_to_drop_bars"] <= 1.5)),
        ("買いのみ + 急落速度 >=0.30ATR/本", lambda x: x["direction"].eq("long") & (x["v_drop_speed_atr_per_bar"] >= 0.30)),
        ("買いのみ + 下落幅 >=4ATR", lambda x: x["direction"].eq("long") & (x["v_move_atr"] >= 4.0)),
        (
            "買いのみ + 実体60%以上 + 回復<=下落本数",
            lambda x: x["direction"].eq("long")
            & x["strategy"].eq("VFIB_618_BODY60_RR2")
            & (x["v_recovery_to_drop_bars"] <= 1.0),
        ),
        (
            "買いのみ + 実体60%以上 + 速度>=0.30 + 回復<=下落本数",
            lambda x: x["direction"].eq("long")
            & x["strategy"].eq("VFIB_618_BODY60_RR2")
            & (x["v_drop_speed_atr_per_bar"] >= 0.30)
            & (x["v_recovery_to_drop_bars"] <= 1.0),
        ),
    ]

    rows = []
    for (timeframe, strategy), group in focus.groupby(["timeframe", "strategy"], sort=True):
        for label, filter_fn in fixed_filters:
            mask = filter_fn(group)
            selected = group[mask]
            if len(selected) < 20:
                continue
            rows.append({"timeframe": timeframe, "strategy": strategy, **summarize(selected, label)})

    fixed = pd.DataFrame(rows).sort_values(["timeframe", "total_r", "avg_r"], ascending=[True, False, False])
    fixed.to_csv(OUT_DIR / "fixed_filters.csv", index=False)

    sweep_rows = []
    h4 = focus[(focus["timeframe"] == "H4") & (focus["strategy"] == "VFIB_618_BODY60_RR2") & (focus["direction"] == "long")].copy()
    for min_atr in [3.0, 3.5, 4.0, 5.0, 6.0]:
        for max_recovery_ratio in [0.75, 1.0, 1.5, 2.0, 999.0]:
            for min_speed in [0.0, 0.2, 0.3, 0.4, 0.6]:
                selected = h4[
                    (h4["v_move_atr"] >= min_atr)
                    & (h4["v_recovery_to_drop_bars"] <= max_recovery_ratio)
                    & (h4["v_drop_speed_atr_per_bar"] >= min_speed)
                ]
                if len(selected) < 50:
                    continue
                sweep_rows.append(
                    {
                        "min_drop_atr": min_atr,
                        "max_recovery_to_drop_bars": max_recovery_ratio,
                        "min_drop_speed_atr_per_bar": min_speed,
                        **summarize(selected, "H4 BODY60 long sweep"),
                    }
                )

    sweep = pd.DataFrame(sweep_rows)
    if not sweep.empty:
        sweep = sweep.sort_values(["avg_r", "total_r"], ascending=[False, False])
    sweep.to_csv(OUT_DIR / "h4_body60_long_sweep.csv", index=False)

    report = [
        "# 急落後V字回復 定量化レポート",
        "",
        "## 定義",
        "",
        "- 急落: 確定スイング高値から確定スイング安値まで、一定ATR以上の下落があること。",
        "- V字回復: 急落幅に対して終値が61.8%以上戻すこと。",
        "- 実体条件: シグナル足の実体がローソク足全体の50%または60%以上。",
        "- 回復速度: `回復にかかった本数 / 下落にかかった本数`。1.0以下なら下落と同等以上の速度で戻した形。",
        "- 急落速度: `下落幅ATR / 下落本数`。数値が大きいほど短時間で強く落ちた形。",
        "",
        "## 固定フィルタ比較",
        "",
        markdown_table(fixed.head(60)),
        "",
        "## H4 実体60%以上・買いのみ スイープ上位",
        "",
        markdown_table(sweep.head(30)),
        "",
        "## 注意",
        "",
        "この集計は既存トレードへの後付けフィルタです。最終採用前に、選んだ条件をエントリーロジックへ組み込んで再バックテストしてください。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(fixed.head(30).to_string(index=False))
    print()
    print(sweep.head(20).to_string(index=False))


if __name__ == "__main__":
    main()

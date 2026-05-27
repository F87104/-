#!/usr/bin/env python3
"""Small CHFJPY personality probe.

This keeps the tested ideas narrow so we can quickly see whether CHFJPY favors
failed-sweep reversal or breakout continuation.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

import research_chfjpy_personality as rp


OUT_DIR = Path(__file__).resolve().parent / "results_2026_05_27" / "chfjpy_personality_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_family(h1: pd.DataFrame, source: pd.DataFrame, family: str, config: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    best: tuple[dict, pd.DataFrame] | None = None
    total = 0
    for combo in itertools.product(*config.values()):
        spec = {"family": family, **dict(zip(config.keys(), combo))}
        trades = rp.run_filtered_trades(h1, source, spec)
        row = {**spec, **rp.summarize(trades)}
        row["score"] = rp.score(row)
        rows.append(row)
        total += 1
        if row["score"] > -9999 and (best is None or row["score"] > best[0]["score"]):
            best = (row, trades)
    grid = pd.DataFrame(rows).sort_values("score", ascending=False)
    if best is not None:
        best[1].to_csv(OUT_DIR / f"{family}_best_trades.csv", index=False)
    return grid, best[0] if best is not None else {}


def main() -> None:
    h1 = rp.prepare_h1()
    wick_source = rp.generate_wick_source(h1)
    breakout_source = rp.generate_breakout_source(h1)

    families = [
        (
            "wick_sweep",
            wick_source,
            {
                "direction": ["long", "short", "both"],
                "lookback": [24, 48],
                "pre_bars": [6, 12],
                "trigger_atr": [0.05],
                "move_atr": [0.8, 1.2],
                "wick_ratio": [0.55, 0.65],
                "wick_max": [1.0],
                "close_location": [0.65, 0.75],
                "range_atr": [1.0],
                "body_min": [0.0],
                "body_max": [0.65],
                "h4": ["any", "not_oppose", "align"],
                "rr": [1.0, 1.2],
                "max_hold": [12, 24],
            },
        ),
        (
            "breakout",
            breakout_source,
            {
                "direction": ["long", "short", "both"],
                "lookback": [24, 48],
                "pre_bars": [6, 12],
                "trigger_atr": [0.05],
                "move_atr": [0.8, 1.2],
                "wick_ratio": [0.0],
                "wick_max": [0.45, 0.60],
                "close_location": [0.60, 0.70],
                "range_atr": [0.8],
                "body_min": [0.35, 0.50],
                "body_max": [1.0],
                "h4": ["any", "not_oppose", "align"],
                "rr": [1.0, 1.2, 1.5],
                "max_hold": [12, 24],
            },
        ),
    ]

    grids = []
    best_rows = []
    for family, source, config in families:
        grid, best = run_family(h1, source, family, config)
        grids.append(grid)
        if best:
            best_rows.append(best)

    all_grid = pd.concat(grids, ignore_index=True).sort_values("score", ascending=False)
    valid = all_grid[all_grid["score"] > -9999].copy()
    all_grid.to_csv(OUT_DIR / "probe_grid.csv", index=False)
    valid.head(50).to_csv(OUT_DIR / "probe_top.csv", index=False)

    cols = [
        "family",
        "score",
        "trades",
        "win_rate",
        "total_r",
        "avg_r",
        "pf",
        "max_dd_r",
        "worst_year_r",
        "worst_2y_r",
        "oos_trades",
        "oos_r",
        "direction",
        "lookback",
        "pre_bars",
        "trigger_atr",
        "move_atr",
        "wick_ratio",
        "wick_max",
        "close_location",
        "range_atr",
        "body_min",
        "body_max",
        "h4",
        "rr",
        "max_hold",
    ]
    print(valid.head(20)[cols].to_string(index=False))
    print(f"OUT_DIR={OUT_DIR}")


if __name__ == "__main__":
    main()

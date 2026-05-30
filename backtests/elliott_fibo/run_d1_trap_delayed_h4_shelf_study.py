#!/usr/bin/env python3
"""
Study: D1 120-bar low trap as a delayed context for H4 V Initial Shelf.

This is a secondary context study. It does not invent a new H4 entry yet.
Instead, it audits whether the already validated H4 V Initial Shelf Breakout
improves when the market recently printed a large D1 low false-break trap.

Hypothesis:
    A D1 120-bar low trap is not a direct buy trigger. It may be an
    accumulation / trapped-seller context. The cleaner entry appears later,
    when H4 forms a V context, holds an upper shelf, and breaks out.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
SHELF_DIR = THIS_DIR / "results_2026_05_30" / "h4_v_initial_shelf_deep_dive"
TRAP_DIR = THIS_DIR / "results_2026_05_30" / "trap_false_break_reaction"
OUT_DIR = THIS_DIR / "results_2026_05_30" / "d1_trap_delayed_h4_shelf"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDED_FOR_CURRENT = ["XAUUSD", "CHFJPY", "SILVER"]

TRAP_STRATEGIES = [
    "CLOSEFAIL_L120_W6_BODY_RR15",
    "WICK_L120_BODY_RR15",
    "WICK_L120_ACTIVITY_RR15",
]


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    equity = r.cumsum()
    return float((equity.cummax() - equity).max())


def max_losing_streak(r: pd.Series) -> int:
    streak = 0
    best = 0
    for value in r:
        if value < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def profit_factor(r: pd.Series) -> float:
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    return float(wins / losses) if losses > 0 else math.inf


def summarize(trades: pd.DataFrame, label: str) -> dict:
    if trades.empty:
        return {
            "label": label,
            "trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "avg_r": math.nan,
            "pf": math.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
            "oos_trades": 0,
            "oos_total_r": 0.0,
        }
    ordered = trades.sort_values("entry_time").copy()
    r = ordered["r_after_cost"].astype(float)
    oos = ordered[ordered["period"] == "OOS_2025_2026"]
    return {
        "label": label,
        "trades": int(len(ordered)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": profit_factor(r),
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
        "avg_mfe_r": float(ordered["mfe_r"].mean()) if "mfe_r" in ordered else math.nan,
        "avg_mae_r": float(ordered["mae_r"].mean()) if "mae_r" in ordered else math.nan,
        "oos_trades": int(len(oos)),
        "oos_total_r": float(oos["r_after_cost"].sum()) if not oos.empty else 0.0,
    }


def summarize_by(trades: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(cols, key_tuple))
        row.update(summarize(group, ""))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_r", "trades"], ascending=[False, False])


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    trades = pd.read_csv(SHELF_DIR / "current_trades_all_symbols.csv")
    traps = pd.read_csv(TRAP_DIR / "events.csv")
    for col in ["entry_time", "signal_time", "exit_time"]:
        trades[col] = pd.to_datetime(trades[col], format="mixed")
    for col in ["signal_time", "entry_time"]:
        traps[col] = pd.to_datetime(traps[col], format="mixed")
    return trades, traps


def build_low_trap_contexts(traps: pd.DataFrame) -> pd.DataFrame:
    contexts = traps[
        (traps["timeframe"] == "D1")
        & (traps["lookback"] == 120)
        & (traps["direction"] == "long")
        & (traps["strategy"].isin(TRAP_STRATEGIES))
    ].copy()
    contexts["context_start"] = contexts["signal_time"] + pd.Timedelta(days=1)
    contexts = contexts.sort_values(["symbol", "context_start", "strategy"]).reset_index(drop=True)
    return contexts


def annotate_trades(trades: pd.DataFrame, contexts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, trade in trades.sort_values(["entry_time", "symbol"]).iterrows():
        prior = contexts[
            (contexts["symbol"] == trade["symbol"])
            & (contexts["context_start"] <= trade["entry_time"])
        ].copy()
        row = trade.to_dict()
        if prior.empty:
            row.update(
                {
                    "d1_low_trap_age_days": math.nan,
                    "d1_low_trap_source": "NONE",
                    "d1_low_trap_signal_time": pd.NaT,
                    "d1_low_trap_context_start": pd.NaT,
                    "d1_low_trap_break_depth_atr": math.nan,
                    "d1_low_trap_reclaim_atr": math.nan,
                    "d1_low_trap_activity_ratio": math.nan,
                }
            )
        else:
            latest = prior.iloc[-1]
            row.update(
                {
                    "d1_low_trap_age_days": float((trade["entry_time"] - latest["context_start"]) / pd.Timedelta(days=1)),
                    "d1_low_trap_source": latest["strategy"],
                    "d1_low_trap_signal_time": latest["signal_time"],
                    "d1_low_trap_context_start": latest["context_start"],
                    "d1_low_trap_break_depth_atr": latest["break_depth_atr"],
                    "d1_low_trap_reclaim_atr": latest["reclaim_atr"],
                    "d1_low_trap_activity_ratio": latest["activity_ratio"],
                }
            )
        rows.append(row)
    out = pd.DataFrame(rows)
    out["selected_universe"] = ~out["symbol"].isin(EXCLUDED_FOR_CURRENT)
    out["d1_low_trap_age_band"] = pd.cut(
        out["d1_low_trap_age_days"],
        bins=[-math.inf, 7, 15, 30, 60, 120, 240, math.inf],
        labels=["<=7d", "7-15d", "15-30d", "30-60d", "60-120d", "120-240d", ">240d"],
    )
    return out


def context_filter_summary(annotated: pd.DataFrame) -> pd.DataFrame:
    rows = []
    universes = {
        "all_symbols": annotated,
        "selected_ex_xau_chf_silver": annotated[annotated["selected_universe"]].copy(),
    }
    for universe_name, data in universes.items():
        rows.append({"universe": universe_name, **summarize(data, "BASELINE")})
        for days in [7, 15, 30, 60, 120, 240]:
            req = data[data["d1_low_trap_age_days"] <= days].copy()
            rows.append({"universe": universe_name, **summarize(req, f"REQUIRE_D1_LOW_TRAP_WITHIN_{days}D")})
        for lo, hi in [(3, 15), (7, 30), (15, 60), (30, 120), (60, 240), (120, 9999)]:
            band = data[
                (data["d1_low_trap_age_days"] >= lo)
                & (data["d1_low_trap_age_days"] <= hi)
            ].copy()
            rows.append({"universe": universe_name, **summarize(band, f"D1_LOW_TRAP_AGE_{lo}_{hi}D")})
        for days in [7, 15, 30, 60, 120, 240]:
            avoid = data[
                data["d1_low_trap_age_days"].isna()
                | (data["d1_low_trap_age_days"] > days)
            ].copy()
            rows.append({"universe": universe_name, **summarize(avoid, f"AVOID_D1_LOW_TRAP_WITHIN_{days}D")})
    return pd.DataFrame(rows)


def write_report(annotated: pd.DataFrame, summary: pd.DataFrame, candidate: pd.DataFrame) -> None:
    selected = annotated[annotated["selected_universe"]].copy()
    candidate_summary = pd.DataFrame(
        [
            summarize(selected, "Baseline selected"),
            summarize(candidate, "D1 low trap age 30-120d + H4 Initial Shelf"),
        ]
    )
    by_symbol = summarize_by(candidate, ["symbol"])
    by_period = summarize_by(candidate, ["period"])
    by_source = summarize_by(candidate, ["d1_low_trap_source"])
    best_rows = summary[
        (summary["universe"] == "selected_ex_xau_chf_silver")
        & (summary["trades"] >= 5)
        & (summary["total_r"] > 0)
    ].sort_values(["pf", "total_r"], ascending=[False, False])

    lines = [
        "# D1 Trap Delayed H4 Shelf Study",
        "",
        "作成日: 2026-05-30",
        "",
        "## 仮説",
        "",
        "D1 120本級の安値更新否定は、その場で買うより、少し時間が経ってからH4でV棚ブレイクが出た時に効くのではないか。",
        "",
        "心理構造:",
        "",
        "1. D1で長期安値を割る",
        "2. 下方向ブレイクが否定される",
        "3. 売り方が完全には崩れず、しばらく揉む",
        "4. 後日H4で急落Vから上側の棚を作る",
        "5. 棚高値を抜けると、売り方の買い戻しと遅れた買いが重なる",
        "",
        "## 検証方法",
        "",
        "- H4側は既存の `H4 V Initial Shelf Breakout` 現行トレードを使用。",
        "- D1側は `D1 120本 安値Trap` のみを見る。",
        "- D1 Trapは日足確定後の翌日から有効。",
        "- これはポストフィルタ検証。実装候補になった場合は、次に統合バックテストで確認する。",
        "",
        "## 結果",
        "",
        markdown_table(candidate_summary, 10),
        "",
        "## 条件別サマリー 上位",
        "",
        markdown_table(best_rows, 40),
        "",
        "## 候補トレード",
        "",
        markdown_table(
            candidate[
                [
                    "symbol",
                    "entry_time",
                    "d1_low_trap_age_days",
                    "d1_low_trap_source",
                    "shelf_range_atr",
                    "shelf_hold_actual",
                    "breakout_atr",
                    "r_after_cost",
                    "exit_reason",
                ]
            ],
            30,
        ),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 30),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 30),
        "",
        "## D1 Trapソース別",
        "",
        markdown_table(by_source, 30),
        "",
        "## 初期判断",
        "",
        "これは面白い。D1 Trap直後ではなく、**30-120日後** が良いという形が出た。",
        "",
        "ただし候補は selected universe で8件。PFは高いが、まだ本番候補ではなく、次は統合バックテストと条件緩和が必要。",
        "",
        "現時点では、`D1 Trap Delayed H4 Shelf` は新しい研究テーマとして継続価値あり。",
        "",
        "## 次にやること",
        "",
        "1. 統合バックテスト化して、contextなしシグナルでポジションブロックされないようにする。",
        "2. D1 Trapの有効期間を 30-180日 まで滑らかに確認する。",
        "3. H4側を Shelf6 固定ではなく Shelf4-8 / RR1.2-2.0 で再確認する。",
        "4. D1 Trap後すぐの15日以内が弱い理由を負けトレードで見る。",
        "",
        "## 出力",
        "",
        "- `annotated_h4_shelf_trades.csv`",
        "- `context_filter_summary.csv`",
        "- `candidate_trades_30_120d_selected.csv`",
        "- `summary_candidate_by_symbol.csv`",
        "- `summary_candidate_by_period.csv`",
        "- `summary_candidate_by_source.csv`",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    trades, traps = load_inputs()
    contexts = build_low_trap_contexts(traps)
    annotated = annotate_trades(trades, contexts)
    summary = context_filter_summary(annotated)
    candidate = annotated[
        annotated["selected_universe"]
        & (annotated["d1_low_trap_age_days"] >= 30)
        & (annotated["d1_low_trap_age_days"] <= 120)
    ].copy()

    annotated.to_csv(OUT_DIR / "annotated_h4_shelf_trades.csv", index=False)
    contexts.to_csv(OUT_DIR / "d1_low_trap_contexts.csv", index=False)
    summary.to_csv(OUT_DIR / "context_filter_summary.csv", index=False)
    candidate.to_csv(OUT_DIR / "candidate_trades_30_120d_selected.csv", index=False)
    summarize_by(candidate, ["symbol"]).to_csv(OUT_DIR / "summary_candidate_by_symbol.csv", index=False)
    summarize_by(candidate, ["period"]).to_csv(OUT_DIR / "summary_candidate_by_period.csv", index=False)
    summarize_by(candidate, ["d1_low_trap_source"]).to_csv(OUT_DIR / "summary_candidate_by_source.csv", index=False)
    write_report(annotated, summary, candidate)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(summary[summary["universe"] == "selected_ex_xau_chf_silver"].to_string(index=False))


if __name__ == "__main__":
    main()

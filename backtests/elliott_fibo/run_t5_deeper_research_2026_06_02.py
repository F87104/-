#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"
OUT = ROOT / "backtests/elliott_fibo/results_2026_06_02/t5_deeper_research"
OUT.mkdir(parents=True, exist_ok=True)

RECOMMENDED_6 = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]
EX_AUD_XAU = ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]


def summarize(df: pd.DataFrame, label: str) -> dict:
    if df.empty:
        return {
            "scenario": label,
            "trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "avg_r": math.nan,
            "pf": math.nan,
            "max_dd_r": 0.0,
            "max_loss_streak": 0,
        }
    d = df.sort_values(["exit_time", "entry_time", "symbol"]).reset_index(drop=True)
    r = d["r_after_cost"].astype(float)
    wins = r[r > 0]
    losses = r[r <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() < 0 else math.inf
    curve = r.cumsum()
    dd = curve.cummax() - curve
    streak = 0
    max_streak = 0
    for value in r:
        if value <= 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return {
        "scenario": label,
        "trades": int(len(d)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": pf,
        "max_dd_r": float(dd.max()) if len(dd) else 0.0,
        "max_loss_streak": int(max_streak),
    }


def grouped(df: pd.DataFrame, cols: list[str], prefix: str) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(cols, dropna=False, observed=False):
        key_tuple = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(cols, key_tuple))
        row.update(summarize(group, prefix + "_" + "_".join(str(x) for x in key_tuple)))
        rows.append(row)
    return pd.DataFrame(rows)


def practical_mask(df: pd.DataFrame) -> pd.Series:
    weak_single_rebreak = (
        df["trigger_type"].eq("rebreak")
        & ((df["bb_pos"].gt(0.95)) | (df["macd_hist_slope3"].le(0.03)))
    )
    return df["bb_pos"].le(0.95) & df["signal_recovery_bars"].le(16) & (~weak_single_rebreak)


def add_buckets(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["result"] = d["r_after_cost"].gt(0).map({True: "win", False: "loss"})
    d["bb_pos_bucket"] = pd.cut(
        d["bb_pos"],
        bins=[-math.inf, 0.85, 0.90, 0.95, math.inf],
        labels=["<=0.85", "0.85-0.90", "0.90-0.95", ">0.95"],
    )
    d["bb_width_bucket"] = pd.cut(
        d["bb_width_atr"],
        bins=[-math.inf, 4.0, 5.5, 7.0, math.inf],
        labels=["<=4", "4-5.5", "5.5-7", ">7"],
    )
    d["macd_slope_bucket"] = pd.cut(
        d["macd_hist_slope3"],
        bins=[-math.inf, 0.03, 0.06, 0.10, math.inf],
        labels=["<=0.03", "0.03-0.06", "0.06-0.10", ">0.10"],
    )
    d["recovery_bars_bucket"] = pd.cut(
        d["signal_recovery_bars"],
        bins=[-math.inf, 8, 12, 16, math.inf],
        labels=["<=8", "9-12", "13-16", ">16"],
    )
    d["fib_bucket"] = pd.cut(
        d["signal_fib_ratio"],
        bins=[-math.inf, 0.85, 0.92, 1.00, math.inf],
        labels=["<=0.85", "0.85-0.92", "0.92-1.00", ">1.00"],
    )
    d["adx_bucket"] = pd.cut(
        d["adx14"],
        bins=[-math.inf, 18, 25, 32, math.inf],
        labels=["<=18", "18-25", "25-32", ">32"],
    )
    d["close_loc_bucket"] = pd.cut(
        d["close_location"],
        bins=[-math.inf, 0.55, 0.70, 0.85, math.inf],
        labels=["<=0.55", "0.55-0.70", "0.70-0.85", ">0.85"],
    )
    return d


def feature_compare(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    for col in features:
        wins = df[df["r_after_cost"].gt(0)][col].dropna()
        losses = df[df["r_after_cost"].le(0)][col].dropna()
        rows.append(
            {
                "feature": col,
                "win_mean": float(wins.mean()) if len(wins) else math.nan,
                "loss_mean": float(losses.mean()) if len(losses) else math.nan,
                "win_median": float(wins.median()) if len(wins) else math.nan,
                "loss_median": float(losses.median()) if len(losses) else math.nan,
                "win_q25": float(wins.quantile(0.25)) if len(wins) else math.nan,
                "loss_q25": float(losses.quantile(0.25)) if len(losses) else math.nan,
                "win_q75": float(wins.quantile(0.75)) if len(wins) else math.nan,
                "loss_q75": float(losses.quantile(0.75)) if len(losses) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def apply_filter_grid(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs: list[tuple[str, Callable[[pd.DataFrame], pd.Series], str]] = [
        ("C125_current", lambda d: practical_mask(d), "現行C125"),
        ("C125_ex_xau", lambda d: practical_mask(d) & d["symbol"].isin(EX_AUD_XAU), "現行C125からXAUUSDも除外"),
        ("no_single_rebreak", lambda d: practical_mask(d) & ~d["trigger_type"].eq("rebreak"), "単独rebreak除外"),
        ("stag_or_combo_only", lambda d: practical_mask(d) & d["trigger_type"].isin(["stagnation", "stagnation+rebreak"]), "stagnation系のみ"),
        ("combo_only", lambda d: practical_mask(d) & d["trigger_type"].eq("stagnation+rebreak"), "stagnation+rebreakのみ"),
        (
            "exclude_gbpjpy_rebreak",
            lambda d: practical_mask(d)
            & d["symbol"].isin(RECOMMENDED_6)
            & ~(d["symbol"].eq("GBPJPY") & d["trigger_type"].eq("rebreak")),
            "推奨6 + GBPJPY単独rebreak除外",
        ),
        ("bb_le_090", lambda d: practical_mask(d) & d["bb_pos"].le(0.90), "BB位置<=0.90"),
        ("bb_085_095", lambda d: practical_mask(d) & d["bb_pos"].between(0.85, 0.95), "BB位置0.85-0.95"),
        ("bb_width_le4", lambda d: practical_mask(d) & d["bb_width_atr"].le(4.0), "BB幅<=4ATR"),
        ("macd_gt006", lambda d: practical_mask(d) & d["macd_hist_slope3"].gt(0.06), "MACD slope3>0.06"),
        ("rec_bars_le12", lambda d: practical_mask(d) & d["signal_recovery_bars"].le(12), "signal recovery<=12"),
        ("close_loc_ge070", lambda d: practical_mask(d) & d["close_location"].ge(0.70), "終値位置>=0.70"),
        ("body_ge060", lambda d: practical_mask(d) & d["body_ratio"].ge(0.60), "実体比率>=0.60"),
        (
            "lean_candidate",
            lambda d: practical_mask(d)
            & d["trigger_type"].isin(["stagnation", "stagnation+rebreak"])
            & d["symbol"].isin(EX_AUD_XAU),
            "実戦候補: XAU/AUD除外 + stagnation系",
        ),
        (
            "quality_candidate",
            lambda d: practical_mask(d)
            & d["symbol"].isin(EX_AUD_XAU)
            & d["trigger_type"].isin(["stagnation", "stagnation+rebreak"])
            & d["bb_width_atr"].le(5.5),
            "品質候補: 実戦候補 + BB幅<=5.5",
        ),
        (
            "balanced_candidate",
            lambda d: practical_mask(d)
            & d["symbol"].isin(RECOMMENDED_6)
            & ~(d["symbol"].eq("GBPJPY") & d["trigger_type"].eq("rebreak"))
            & (d["bb_width_atr"].le(5.5)),
            "バランス候補: 推奨6 + GBPJPY単独rebreak除外 + BB幅<=5.5",
        ),
        (
            "bb_or_width_candidate",
            lambda d: practical_mask(d)
            & d["symbol"].isin(RECOMMENDED_6)
            & (d["bb_pos"].between(0.85, 0.95) | d["bb_width_atr"].le(4.0)),
            "勢い候補: BB位置0.85-0.95 または BB幅<=4",
        ),
    ]
    for name, fn, note in specs:
        mask = fn(base)
        row = summarize(base[mask], name)
        row["note"] = note
        rows.append(row)
        for period, group in base[mask].groupby("period"):
            prow = summarize(group, name + "_" + str(period))
            prow["note"] = note
            rows.append(prow)
    return pd.DataFrame(rows)


def md(df: pd.DataFrame, digits: int = 2) -> str:
    if df.empty:
        return "_No rows._"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = []
        for col in headers:
            value = row[col]
            if isinstance(value, float):
                if math.isinf(value):
                    values.append("inf")
                elif math.isnan(value):
                    values.append("nan")
                elif col == "avg_r":
                    values.append(f"{value:.3f}")
                elif col == "win_rate":
                    values.append(f"{value:.2f}%")
                else:
                    values.append(f"{value:.{digits}f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    raw = pd.read_csv(SRC, parse_dates=["signal_time", "entry_time", "exit_time"])
    raw = add_buckets(raw)
    practical_all = raw[practical_mask(raw)].copy()
    practical_6 = practical_all[practical_all["symbol"].isin(RECOMMENDED_6)].copy()

    raw.to_csv(OUT / "source_with_buckets.csv", index=False)
    practical_all.to_csv(OUT / "t5_practical_all_symbols.csv", index=False)
    practical_6.to_csv(OUT / "t5_practical_recommended6.csv", index=False)

    overview = pd.DataFrame(
        [
            summarize(raw, "source_all_114"),
            summarize(practical_all, "practical_c125_all_symbols"),
            summarize(practical_6, "practical_c125_recommended6"),
        ]
    )
    overview.to_csv(OUT / "overview.csv", index=False)

    filter_grid = apply_filter_grid(raw)
    filter_grid.to_csv(OUT / "filter_grid.csv", index=False)

    practical_group_specs = {
        "by_period": ["period"],
        "by_symbol": ["symbol"],
        "by_trigger": ["trigger_type"],
        "by_symbol_trigger": ["symbol", "trigger_type"],
        "by_bb_pos_bucket": ["bb_pos_bucket"],
        "by_bb_width_bucket": ["bb_width_bucket"],
        "by_macd_slope_bucket": ["macd_slope_bucket"],
        "by_recovery_bars_bucket": ["recovery_bars_bucket"],
        "by_fib_bucket": ["fib_bucket"],
        "by_adx_bucket": ["adx_bucket"],
        "by_close_loc_bucket": ["close_loc_bucket"],
    }
    for name, cols in practical_group_specs.items():
        grouped(practical_6, cols, name).to_csv(OUT / f"{name}.csv", index=False)

    features = [
        "bb_pos",
        "bb_width_atr",
        "macd_hist_slope3",
        "signal_recovery_bars",
        "signal_fib_ratio",
        "v_move_atr",
        "v_move_bars",
        "v_drop_speed_atr_per_bar",
        "body_ratio",
        "close_location",
        "adx14",
        "ema20_slope_10_atr",
        "atr_ratio_50",
        "range5_atr",
        "chop14",
    ]
    fc = feature_compare(practical_6, features)
    fc.to_csv(OUT / "winner_loser_feature_compare.csv", index=False)

    report = [
        "# T5 Deeper Research",
        "",
        "作成日: 2026-06-02",
        "",
        "## 目的",
        "",
        "H4 T5 + MACD + BBを、単なる補助手法から実戦運用ルールへ近づけるため、勝ち負けの特徴・削る条件・残す条件を再点検した。",
        "",
        "## 全体",
        "",
        md(overview),
        "",
        "## フィルタ候補",
        "",
        md(filter_grid[filter_grid["scenario"].isin([
            "C125_current",
            "C125_ex_xau",
            "no_single_rebreak",
            "stag_or_combo_only",
            "combo_only",
            "bb_le_090",
            "bb_085_095",
            "bb_width_le4",
            "macd_gt006",
            "rec_bars_le12",
            "close_loc_ge070",
            "body_ge060",
            "exclude_gbpjpy_rebreak",
            "lean_candidate",
            "quality_candidate",
            "balanced_candidate",
            "bb_or_width_candidate",
        ])]),
        "",
        "## Practical C125 推奨6 通貨別",
        "",
        md(pd.read_csv(OUT / "by_symbol.csv")),
        "",
        "## Practical C125 推奨6 トリガー別",
        "",
        md(pd.read_csv(OUT / "by_trigger.csv")),
        "",
        "## Practical C125 推奨6 BB位置",
        "",
        md(pd.read_csv(OUT / "by_bb_pos_bucket.csv")),
        "",
        "## Practical C125 推奨6 MACD slope",
        "",
        md(pd.read_csv(OUT / "by_macd_slope_bucket.csv")),
        "",
        "## Practical C125 推奨6 回復本数",
        "",
        md(pd.read_csv(OUT / "by_recovery_bars_bucket.csv")),
        "",
        "## 勝ち負け特徴量比較",
        "",
        md(fc, digits=3),
        "",
        "## 暫定結論",
        "",
        "- 現行C125は全期間・全7通貨で39件 +35.90R / PF 4.14、推奨6通貨では35件 +32.04R / PF 4.07。まだかなり強い。",
        "- 2015-2024だけで見ると現行C125は34件 +29.20R / PF 3.55、OOS 2025-2026は5件 +6.71R。OOS件数は少ないが崩れてはいない。",
        "- XAUUSDはT5単体では悪くないが、別研究でボラや重複リスクが大きいため、運用上は除外候補として別枠管理が妥当。",
        "- 単独rebreakを丸ごと除外すると件数は減る。通貨別に見ると、弱いのは特にGBPJPY単独rebreakで、CHFJPY/XAUUSDなどのrebreakは残す余地がある。",
        "- 推奨6からGBPJPY単独rebreakだけを除外すると30件 +32.50R / PF 5.39。構造説明と件数のバランスが良い改善候補。",
        "- BB幅<=4ATRは過去研究では超厳選寄り。今回も件数が減りやすいので、通常ロット条件ではなくロット増減条件として扱う方が自然。",
        "- T5の本質は、急落後のV候補を直接買うことではなく、売り失敗後に上側で崩れず再点火する場所だけを買うこと。",
        "",
        "## 実戦向け次案",
        "",
        "1. C125を基本にする。",
        "2. 通常監視は推奨6、ただしXAUUSDは小ロットまたは別集計。",
        "3. trigger_typeはstagnation+rebreakを最優先、stagnationを通常、単独rebreakは0.25RまたはMACD強い時だけ。",
        "4. GBPJPYの単独rebreakは見送り候補。GBPJPYはstagnation系だけを使う。",
        "5. BB幅<=4ATRはロット通常、4-7ATRは半分、7ATR超は見送り。",
        "6. T5後にTBが同方向で出ても早利確しない。保有継続または小さな追加候補にする。",
        "",
    ]
    (OUT / "report_ja.md").write_text("\n".join(report), encoding="utf-8")
    print(OUT)
    print(overview.to_string(index=False))
    print(filter_grid[filter_grid["scenario"].isin(["C125_current", "lean_candidate", "quality_candidate"])].to_string(index=False))


if __name__ == "__main__":
    main()

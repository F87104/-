#!/usr/bin/env python3
"""
Rule matrix for TrendBreakV1 fakeout mitigation.

Combines:
- pre-entry filters discovered in the fakeout feature study
- early back-inside exits after entry

The purpose is to find practical rule sets, not only descriptive features.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "fakeout_rule_matrix_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(THIS_DIR))

import run_fakeout_feature_study as study  # noqa: E402


FilterFunc = Callable[[dict], bool]


FILTERS: list[tuple[str, str, FilterFunc | None]] = [
    ("baseline", "追加フィルタなし", None),
    ("body50", "実体が足全体の50%以上", lambda f: f["body_ratio"] >= 0.50),
    ("body60", "実体が足全体の60%以上", lambda f: f["body_ratio"] >= 0.60),
    ("break005", "終値の抜け幅がATR0.05以上", lambda f: f["break_atr"] >= 0.05),
    ("break010", "終値の抜け幅がATR0.10以上", lambda f: f["break_atr"] >= 0.10),
    ("pre_range20", "直前6本値幅がATR2.0以内", lambda f: f["pre_range_6_atr"] <= 2.0),
    ("pre_range25", "直前6本値幅がATR2.5以内", lambda f: f["pre_range_6_atr"] <= 2.5),
    ("stagnation_break", "直前6本停滞 + ATR0.05以上ブレイク", lambda f: f["pre_range_6_atr"] <= 2.5 and f["break_atr"] >= 0.05),
    ("stagnation_body60", "停滞 + 実体60%以上", lambda f: f["pre_range_6_atr"] <= 2.5 and f["body_ratio"] >= 0.60),
    ("stagnation_break_body60", "停滞 + ATR0.05以上ブレイク + 実体60%以上", lambda f: f["pre_range_6_atr"] <= 2.5 and f["break_atr"] >= 0.05 and f["body_ratio"] >= 0.60),
    ("strong_close_wick", "終値位置65%以上 + 逆ヒゲ35%以下", lambda f: f["close_strength"] >= 0.65 and f["adverse_wick_ratio"] <= 0.35),
    ("not_overextended3", "直前6本の伸びがATR3.0以内", lambda f: f["pre_extension_6_atr"] <= 3.0),
    ("balanced_guard", "終値強め + 逆ヒゲ小 + 伸びすぎ回避", lambda f: f["close_strength"] >= 0.60 and f["adverse_wick_ratio"] <= 0.40 and f["pre_extension_6_atr"] <= 3.0),
]

EARLY_EXIT_BARS = [0, 1, 3, 6]


def close_r(direction: str, entry: float, exit_price: float, sl_dist: float, spread: float, slip: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - slip) - (entry + spread / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - spread / 2.0) - (exit_price + slip)
    return clean / sl_dist, after / sl_dist


def simulate_rule(symbol: str, ctx: pd.DataFrame, cfg: dict, rule_name: str, rule_desc: str, filter_func: FilterFunc | None, early_bars: int) -> pd.DataFrame:
    o = ctx["open"].to_numpy()
    h = ctx["high"].to_numpy()
    l = ctx["low"].to_numpy()
    c = ctx["close"].to_numpy()
    a = ctx["atr"].to_numpy()
    idx = ctx.index
    costs = study.COST_TABLE[symbol]
    rows = []
    in_pos_until = -1
    cooldown_until = -1
    equity_pct = 100.0
    peak_equity_pct = 100.0

    for i in range(len(ctx) - 2):
        if i <= in_pos_until or i <= cooldown_until:
            continue
        if bool(ctx["high_vol"].iloc[i]):
            continue
        if peak_equity_pct > 0 and (peak_equity_pct - equity_pct) / peak_equity_pct * 100 >= study.MAX_DD_PCT:
            continue

        direction, level, level_kind = study.choose_signal(ctx, i, cfg)
        if direction is None:
            continue
        features = study.signal_features(ctx, i, direction, level, level_kind)
        if filter_func is not None and not filter_func(features):
            continue

        sig_atr = a[i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue
        entry_bar = i + 1
        entry = float(o[entry_bar])
        sl_dist = float(sig_atr * cfg["sl_atr"])
        if direction == "long":
            sl = entry - sl_dist
            tp = entry + sl_dist * cfg["tp_rr"]
        else:
            sl = entry + sl_dist
            tp = entry - sl_dist * cfg["tp_rr"]

        for j in range(entry_bar, len(ctx) - 1):
            if direction == "long":
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
                if hit_sl or hit_tp:
                    reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                    exit_bar = j
                    exit_price = sl if hit_sl else tp
                elif early_bars > 0 and (j - entry_bar + 1) <= early_bars and c[j] <= level:
                    reason = "early_back_inside"
                    exit_bar = j + 1
                    exit_price = float(o[exit_bar])
                else:
                    continue
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp
                if hit_sl or hit_tp:
                    reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                    exit_bar = j
                    exit_price = sl if hit_sl else tp
                elif early_bars > 0 and (j - entry_bar + 1) <= early_bars and c[j] >= level:
                    reason = "early_back_inside"
                    exit_bar = j + 1
                    exit_price = float(o[exit_bar])
                else:
                    continue

            r_clean, r_after = close_r(direction, entry, exit_price, sl_dist, costs["spread_price"], costs["slip_price"])
            equity_pct += r_after * study.RISK_PCT
            peak_equity_pct = max(peak_equity_pct, equity_pct)
            row = {
                "symbol": symbol,
                "rule_name": rule_name,
                "rule_desc": rule_desc,
                "early_exit_bars": early_bars,
                "signal_time": idx[i],
                "entry_time": idx[entry_bar],
                "exit_time": idx[exit_bar],
                "direction": direction,
                "level_kind": level_kind,
                "break_level": level,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "exit_price": exit_price,
                "pnl_r_clean": r_clean,
                "pnl_r_after_cost": r_after,
                "bars_held": exit_bar - entry_bar,
                "exit_reason": reason,
            }
            row.update(features)
            rows.append(row)
            in_pos_until = exit_bar
            cooldown_until = exit_bar + int(cfg.get("cooldown", 0))
            break
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "total_r_after_cost": 0.0,
            "avg_r_after_cost": 0.0,
            "pf_after_cost": math.nan,
            "max_dd_after_cost_r": 0.0,
            "early_exit_rate": 0.0,
        }
    r = df["pnl_r_after_cost"].to_numpy()
    return {
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r_after_cost": float(r.sum()),
        "avg_r_after_cost": float(r.mean()),
        "pf_after_cost": study.profit_factor(r),
        "max_dd_after_cost_r": study.max_drawdown_r(r),
        "early_exit_rate": float((df["exit_reason"] == "early_back_inside").mean() * 100),
    }


def write_report(summary: pd.DataFrame) -> None:
    all_rows = summary[summary["symbol"] == "ALL"].copy()
    lines = [
        "# TrendBreakV1 騙し回避ルール行列 2015-2024",
        "",
        "## 見方",
        "",
        "- `early_exit_bars=0` は早期撤退なし。",
        "- `early_exit_bars=1/3/6` は、その本数以内に終値がブレイク水準内へ戻ったら次足始値で撤退。",
        "- Total R はコスト込み。",
        "",
        "## 総利益順 Top 15",
        "",
        "| Rule | Early Exit | Trades | WR | Total R | PF | Max DD | Early Exit Rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in all_rows.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False]).head(15).iterrows():
        lines.append(
            f"| {row['rule_name']} | {int(row['early_exit_bars'])} | {int(row['trades'])} | "
            f"{row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | {row['pf_after_cost']:.3f} | "
            f"{row['max_dd_after_cost_r']:.2f} | {row['early_exit_rate']:.2f}% |"
        )

    lines.extend([
        "",
        "## PF順 Top 15（最低150トレード）",
        "",
        "| Rule | Early Exit | Trades | WR | Total R | PF | Max DD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    pf_view = all_rows[all_rows["trades"] >= 150].sort_values(["pf_after_cost", "total_r_after_cost"], ascending=[False, False]).head(15)
    for _, row in pf_view.iterrows():
        lines.append(
            f"| {row['rule_name']} | {int(row['early_exit_bars'])} | {int(row['trades'])} | "
            f"{row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | {row['pf_after_cost']:.3f} | "
            f"{row['max_dd_after_cost_r']:.2f} |"
        )

    lines.extend([
        "",
        "## DD順 Top 15（最低150トレード）",
        "",
        "| Rule | Early Exit | Trades | WR | Total R | PF | Max DD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    dd_view = all_rows[all_rows["trades"] >= 150].sort_values(["max_dd_after_cost_r", "total_r_after_cost"], ascending=[True, False]).head(15)
    for _, row in dd_view.iterrows():
        lines.append(
            f"| {row['rule_name']} | {int(row['early_exit_bars'])} | {int(row['trades'])} | "
            f"{row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | {row['pf_after_cost']:.3f} | "
            f"{row['max_dd_after_cost_r']:.2f} |"
        )
    (OUT_DIR / "rule_matrix_report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    contexts = {}
    configs = {}
    for symbol in study.SYMBOLS:
        cfg = study.hybrid_cfg(symbol)
        df = study.load_instrument(symbol)
        df = df[(df.index.year >= study.YEAR_FROM) & (df.index.year <= study.YEAR_TO)]
        configs[symbol] = cfg
        contexts[symbol] = study.prepare_context(df, cfg)

    all_trades = []
    summary_rows = []
    for rule_name, rule_desc, filter_func in FILTERS:
        for early_bars in EARLY_EXIT_BARS:
            print(f"Rule={rule_name} early={early_bars}")
            parts = []
            for symbol in study.SYMBOLS:
                df = simulate_rule(symbol, contexts[symbol], configs[symbol], rule_name, rule_desc, filter_func, early_bars)
                parts.append(df)
                row = summarize(df)
                row.update({"symbol": symbol, "rule_name": rule_name, "rule_desc": rule_desc, "early_exit_bars": early_bars})
                summary_rows.append(row)
            combined = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            all_trades.append(combined)
            row = summarize(combined)
            row.update({"symbol": "ALL", "rule_name": rule_name, "rule_desc": rule_desc, "early_exit_bars": early_bars})
            summary_rows.append(row)

    trades = pd.concat(all_trades, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    trades.to_csv(OUT_DIR / "rule_matrix_trades.csv", index=False)
    summary.to_csv(OUT_DIR / "rule_matrix_summary.csv", index=False)
    write_report(summary)

    all_summary = summary[summary["symbol"] == "ALL"]
    print("\nTop by total R:")
    print(
        all_summary.sort_values(["total_r_after_cost", "win_rate"], ascending=[False, False])
        .head(15)
        [["rule_name", "early_exit_bars", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "early_exit_rate"]]
        .to_string(index=False)
    )
    print("\nTop by PF with >=150 trades:")
    print(
        all_summary[all_summary["trades"] >= 150]
        .sort_values(["pf_after_cost", "total_r_after_cost"], ascending=[False, False])
        .head(15)
        [["rule_name", "early_exit_bars", "trades", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r", "early_exit_rate"]]
        .to_string(index=False)
    )
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

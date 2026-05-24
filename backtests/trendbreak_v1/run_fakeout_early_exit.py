#!/usr/bin/env python3
"""
Test an actionable fakeout escape:
after entry, if price closes back inside the broken level within N bars,
exit at the next bar open.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "fakeout_feature_study_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(THIS_DIR))

import run_fakeout_feature_study as study  # noqa: E402


def close_r(direction: str, entry: float, exit_price: float, sl_dist: float, spread: float, slip: float) -> tuple[float, float]:
    if direction == "long":
        clean = exit_price - entry
        after = (exit_price - slip) - (entry + spread / 2.0)
    else:
        clean = entry - exit_price
        after = (entry - spread / 2.0) - (exit_price + slip)
    return clean / sl_dist, after / sl_dist


def simulate_early_exit(symbol: str, ctx: pd.DataFrame, cfg: dict, back_inside_bars: int) -> pd.DataFrame:
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
                    exit_price = sl if hit_sl else tp
                    r_clean, r_after = close_r(direction, entry, exit_price, sl_dist, costs["spread_price"], costs["slip_price"])
                    exit_bar = j
                elif (j - entry_bar + 1) <= back_inside_bars and c[j] <= level:
                    reason = "early_back_inside"
                    exit_bar = j + 1
                    exit_price = float(o[exit_bar])
                    r_clean, r_after = close_r(direction, entry, exit_price, sl_dist, costs["spread_price"], costs["slip_price"])
                else:
                    continue
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp
                if hit_sl or hit_tp:
                    reason = "SL_first_same_bar" if hit_sl and hit_tp else "SL" if hit_sl else "TP"
                    exit_price = sl if hit_sl else tp
                    r_clean, r_after = close_r(direction, entry, exit_price, sl_dist, costs["spread_price"], costs["slip_price"])
                    exit_bar = j
                elif (j - entry_bar + 1) <= back_inside_bars and c[j] >= level:
                    reason = "early_back_inside"
                    exit_bar = j + 1
                    exit_price = float(o[exit_bar])
                    r_clean, r_after = close_r(direction, entry, exit_price, sl_dist, costs["spread_price"], costs["slip_price"])
                else:
                    continue

            equity_pct += r_after * study.RISK_PCT
            peak_equity_pct = max(peak_equity_pct, equity_pct)
            rows.append(
                {
                    "symbol": symbol,
                    "back_inside_bars": back_inside_bars,
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
            )
            in_pos_until = exit_bar
            cooldown_until = exit_bar + int(cfg.get("cooldown", 0))
            break
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trades": 0, "win_rate": 0.0, "total_r_after_cost": 0.0, "avg_r_after_cost": 0.0, "pf_after_cost": math.nan, "max_dd_after_cost_r": 0.0, "early_exit_rate": 0.0}
    r = df["pnl_r_after_cost"].to_numpy()
    return {
        "trades": len(df),
        "win_rate": float((r > 0).mean() * 100),
        "total_r_after_cost": float(r.sum()),
        "avg_r_after_cost": float(r.mean()),
        "pf_after_cost": study.profit_factor(r),
        "max_dd_after_cost_r": study.max_drawdown_r(r),
        "early_exit_rate": float((df["exit_reason"] == "early_back_inside").mean() * 100),
    }


def main() -> None:
    all_rows = []
    for n in [1, 2, 3, 6]:
        print(f"Early exit back-inside within {n} bars")
        for symbol in study.SYMBOLS:
            cfg = study.hybrid_cfg(symbol)
            df = study.load_instrument(symbol)
            df = df[(df.index.year >= study.YEAR_FROM) & (df.index.year <= study.YEAR_TO)]
            ctx = study.prepare_context(df, cfg)
            res = simulate_early_exit(symbol, ctx, cfg, n)
            all_rows.append(res)
    trades = pd.concat(all_rows, ignore_index=True)
    trades.to_csv(OUT_DIR / "early_back_inside_exit_trades.csv", index=False)

    rows = []
    for (n, symbol), g in trades.groupby(["back_inside_bars", "symbol"]):
        row = summarize(g)
        row.update({"back_inside_bars": n, "symbol": symbol})
        rows.append(row)
    for n, g in trades.groupby("back_inside_bars"):
        row = summarize(g)
        row.update({"back_inside_bars": n, "symbol": "ALL"})
        rows.append(row)
    summary = pd.DataFrame(rows).sort_values(["back_inside_bars", "symbol"])
    summary.to_csv(OUT_DIR / "early_back_inside_exit_summary.csv", index=False)
    print(summary[summary["symbol"] == "ALL"].to_string(index=False))
    print(f"Wrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

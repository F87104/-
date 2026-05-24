#!/usr/bin/env python3
"""
Sweep TrendBreakV1 HYBRID same-direction pyramiding from 1 to 5.

This is a Python approximation of the Pine strategy behavior after adding
`maxEntriesPerDirection`. It keeps opposite-direction hedging disabled and
allows only same-direction add-on entries. Each add-on recalculates the basket
SL/TP from the current average entry and the latest signal ATR, which mirrors
the current Pine implementation.
"""

from __future__ import annotations

import copy
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
BACKTEST_DIR = REPO_ROOT / "backtest"
OUT_DIR = THIS_DIR / "pyramiding_sweep_2015_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKTEST_DIR))

from sai_backtest import load_instrument  # noqa: E402
from trendbreak_backtest import PRESETS_CONSERVATIVE, compute_signals  # noqa: E402


SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
YEAR_FROM = 2015
YEAR_TO = 2024
RISK_PCT = 1.0
MAX_DD_PCT = 20.0

COST_TABLE = {
    "USDJPY": {"spread_price": 0.010, "slip_price": 0.005},
    "EURJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "GBPJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "AUDJPY": {"spread_price": 0.015, "slip_price": 0.005},
    "CHFJPY": {"spread_price": 0.020, "slip_price": 0.010},
    "XAUUSD": {"spread_price": 0.30, "slip_price": 0.20},
    "SILVER": {"spread_price": 0.030, "slip_price": 0.020},
}


def hybrid_cfg(symbol: str) -> dict:
    cfg = copy.deepcopy(PRESETS_CONSERVATIVE[symbol])
    if symbol in {"USDJPY", "GBPJPY", "SILVER"}:
        cfg["level_kind"] = "any"
        cfg["session"] = False
    elif symbol == "CHFJPY":
        cfg["level_kind"] = "any"
    elif symbol == "XAUUSD":
        cfg["session"] = False
    # EURJPY and AUDJPY keep BASE conservative settings.
    return cfg


@dataclass
class Leg:
    basket_id: int
    leg_no: int
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    direction: str
    entry: float
    sl_dist: float


@dataclass
class ClosedLeg:
    symbol: str
    max_entries: int
    basket_id: int
    leg_no: int
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    entry: float
    exit_price: float
    basket_sl: float
    basket_tp: float
    sl_dist: float
    pnl_r_clean: float
    pnl_r_after_cost: float
    bars_held: int
    exit_reason: str


def close_leg_r(leg: Leg, exit_price: float, spread: float, slip: float) -> tuple[float, float]:
    if leg.direction == "long":
        pnl_clean = exit_price - leg.entry
        entry_after_cost = leg.entry + spread / 2.0
        exit_after_cost = exit_price - slip
        pnl_after_cost = exit_after_cost - entry_after_cost
    else:
        pnl_clean = leg.entry - exit_price
        entry_after_cost = leg.entry - spread / 2.0
        exit_after_cost = exit_price + slip
        pnl_after_cost = entry_after_cost - exit_after_cost
    return pnl_clean / leg.sl_dist, pnl_after_cost / leg.sl_dist


def current_dd_pct(equity_pct: float, peak_equity_pct: float) -> float:
    if peak_equity_pct <= 0:
        return 0.0
    return (peak_equity_pct - equity_pct) / peak_equity_pct * 100.0


def simulate_pyramiding(symbol: str, sig: pd.DataFrame, cfg: dict, max_entries: int) -> list[ClosedLeg]:
    o = sig["open"].to_numpy()
    h = sig["high"].to_numpy()
    l = sig["low"].to_numpy()
    a = sig["atr"].to_numpy()
    long_sig = sig["long_sig"].to_numpy()
    short_sig = sig["short_sig"].to_numpy()
    idx = sig.index

    atr_avg = sig["atr"].rolling(100).mean().to_numpy()
    high_vol = (sig["atr"].to_numpy() > atr_avg * 2.0)
    high_vol = np.nan_to_num(high_vol, nan=False).astype(bool)

    costs = COST_TABLE[symbol]
    open_legs: list[Leg] = []
    closed: list[ClosedLeg] = []
    side: str | None = None
    basket_id = 0
    basket_sl = np.nan
    basket_tp = np.nan
    cooldown_until = -1
    last_exit_bar = -1
    equity_pct = 100.0
    peak_equity_pct = 100.0

    def mark_exit(bar: int, exit_price: float, reason: str) -> None:
        nonlocal open_legs, side, basket_sl, basket_tp, last_exit_bar, cooldown_until
        nonlocal equity_pct, peak_equity_pct
        for leg in open_legs:
            r_clean, r_after = close_leg_r(
                leg, exit_price, costs["spread_price"], costs["slip_price"]
            )
            equity_pct += r_after * RISK_PCT
            peak_equity_pct = max(peak_equity_pct, equity_pct)
            closed.append(
                ClosedLeg(
                    symbol=symbol,
                    max_entries=max_entries,
                    basket_id=leg.basket_id,
                    leg_no=leg.leg_no,
                    signal_time=leg.signal_time,
                    entry_time=leg.entry_time,
                    exit_time=idx[bar],
                    direction=leg.direction,
                    entry=leg.entry,
                    exit_price=exit_price,
                    basket_sl=basket_sl,
                    basket_tp=basket_tp,
                    sl_dist=leg.sl_dist,
                    pnl_r_clean=r_clean,
                    pnl_r_after_cost=r_after,
                    bars_held=bar - int(sig.index.get_loc(leg.entry_time)),
                    exit_reason=reason,
                )
            )
        open_legs = []
        side = None
        basket_sl = np.nan
        basket_tp = np.nan
        last_exit_bar = bar
        cooldown_until = bar + int(cfg.get("cooldown", 0))

    for i in range(len(sig) - 1):
        # Existing basket exits are checked first on each bar.
        if open_legs and side == "long":
            hit_sl = l[i] <= basket_sl
            hit_tp = h[i] >= basket_tp
            if hit_sl and hit_tp:
                mark_exit(i, basket_sl, "SL_first_same_bar")
                continue
            if hit_sl:
                mark_exit(i, basket_sl, "SL")
                continue
            if hit_tp:
                mark_exit(i, basket_tp, "TP")
                continue
        elif open_legs and side == "short":
            hit_sl = h[i] >= basket_sl
            hit_tp = l[i] <= basket_tp
            if hit_sl and hit_tp:
                mark_exit(i, basket_sl, "SL_first_same_bar")
                continue
            if hit_sl:
                mark_exit(i, basket_sl, "SL")
                continue
            if hit_tp:
                mark_exit(i, basket_tp, "TP")
                continue

        if i == last_exit_bar or i <= cooldown_until or high_vol[i]:
            continue

        if current_dd_pct(equity_pct, peak_equity_pct) >= MAX_DD_PCT:
            continue

        wants_long = bool(long_sig[i])
        wants_short = bool(short_sig[i])
        if not wants_long and not wants_short:
            continue

        # Match the Pine/code convention: if both are true, long has priority.
        entry_direction = "long" if wants_long else "short"
        if side is not None and entry_direction != side:
            continue
        if len(open_legs) >= max_entries:
            continue

        entry_bar = i + 1
        sig_atr = a[i]
        if np.isnan(sig_atr) or sig_atr <= 0:
            continue

        if not open_legs:
            basket_id += 1
            side = entry_direction

        leg_no = len(open_legs) + 1
        sl_dist = sig_atr * cfg["sl_atr"]
        open_legs.append(
            Leg(
                basket_id=basket_id,
                leg_no=leg_no,
                signal_time=idx[i],
                entry_time=idx[entry_bar],
                direction=entry_direction,
                entry=float(o[entry_bar]),
                sl_dist=float(sl_dist),
            )
        )

        avg_entry = float(np.mean([leg.entry for leg in open_legs]))
        if side == "long":
            basket_sl = avg_entry - sl_dist
            basket_tp = avg_entry + sl_dist * cfg["tp_rr"]
        else:
            basket_sl = avg_entry + sl_dist
            basket_tp = avg_entry - sl_dist * cfg["tp_rr"]

    return closed


def max_streak(values: np.ndarray, winning: bool) -> int:
    current = 0
    longest = 0
    for value in values:
        good = value > 0 if winning else value <= 0
        if good:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def summarize_legs(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(group_cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        r = g["pnl_r_after_cost"].to_numpy()
        r_clean = g["pnl_r_clean"].to_numpy()
        gp = r[r > 0].sum()
        gl = r[r <= 0].sum()
        curve = np.cumsum(r)
        dd = float((np.maximum.accumulate(curve) - curve).max()) if len(curve) else 0.0
        row = dict(zip(group_cols, key_tuple))
        row.update(
            entries=len(g),
            baskets=int(g["basket_key"].nunique()),
            win_rate=round(float((r > 0).mean() * 100), 2) if len(r) else 0.0,
            total_r_after_cost=round(float(r.sum()), 2),
            total_r_clean=round(float(r_clean.sum()), 2),
            avg_r_after_cost=round(float(r.mean()), 4) if len(r) else 0.0,
            pf_after_cost=round(float(gp / abs(gl)), 3) if gl < 0 else np.inf,
            max_dd_after_cost_r=round(dd, 2),
            max_losing_streak=max_streak(r, winning=False),
            max_winning_streak=max_streak(r, winning=True),
        )
        rows.append(row)
    return pd.DataFrame(rows)


def write_report(
    all_summary: pd.DataFrame,
    best_profit: pd.DataFrame,
    best_wr: pd.DataFrame,
    overall: pd.DataFrame,
) -> None:
    lines = [
        "# TrendBreakV1 HYBRID Same-Direction Pyramiding Sweep",
        "",
        f"- Period: `{YEAR_FROM}-01-01` to `{YEAR_TO}-12-31`",
        "- Data: local `F87104_test` H1 OHLC",
        "- Cost: spread + slippage table used in prior audit scripts",
        "- Entry: next bar open after confirmed signal close",
        "- Add-on rule: same direction only, opposite direction blocked",
        "- Basket SL/TP: recalculated from average entry after each add-on",
        "- High-vol filter: ATR14 > SMA(ATR14,100) x 2 blocks new entries",
        "- DD stop approximation: 20% with 1R ~= 1%",
        "",
        "## Best By Symbol",
        "",
        "| Symbol | Best Profit Max Entries | Profit R | WR | Entries | Baskets | Best WR Max Entries | Best WR | WR Profit R |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol in SYMBOLS:
        bp = best_profit[best_profit["symbol"] == symbol].iloc[0]
        bw = best_wr[best_wr["symbol"] == symbol].iloc[0]
        lines.append(
            f"| {symbol} | {int(bp['max_entries'])} | {bp['total_r_after_cost']:.2f} | "
            f"{bp['win_rate']:.2f}% | {int(bp['entries'])} | {int(bp['baskets'])} | "
            f"{int(bw['max_entries'])} | {bw['win_rate']:.2f}% | {bw['total_r_after_cost']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Overall By Max Entries",
            "",
            "| Max Entries | Entries | Baskets | WR | Profit R | PF | Max DD R |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in overall.sort_values("max_entries").iterrows():
        lines.append(
            f"| {int(row['max_entries'])} | {int(row['entries'])} | {int(row['baskets'])} | "
            f"{row['win_rate']:.2f}% | {row['total_r_after_cost']:.2f} | "
            f"{row['pf_after_cost']:.3f} | {row['max_dd_after_cost_r']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `entries` counts each add-on entry as one closed leg.",
            "- `baskets` counts one campaign from first entry until aggregate SL/TP exit.",
            "- The result is a research approximation, not a TradingView broker emulator clone.",
            "",
            "## Output Files",
            "",
            "- `pyramiding_trades.csv`",
            "- `summary_by_symbol_entries.csv`",
            "- `best_by_profit.csv`",
            "- `best_by_win_rate.csv`",
            "- `overall_by_entries.csv`",
        ]
    )
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    all_closed: list[ClosedLeg] = []
    for symbol in SYMBOLS:
        cfg = hybrid_cfg(symbol)
        df = load_instrument(symbol)
        df = df[(df.index.year >= YEAR_FROM) & (df.index.year <= YEAR_TO)]
        sig = compute_signals(df, cfg)
        for max_entries in range(1, 6):
            closed = simulate_pyramiding(symbol, sig, cfg, max_entries)
            all_closed.extend(closed)
            print(
                f"{symbol:7} max_entries={max_entries} "
                f"entries={len(closed):4} baskets={len(set(t.basket_id for t in closed)):4}"
            )

    trades_df = pd.DataFrame([t.__dict__ for t in all_closed])
    trades_df["basket_key"] = trades_df["symbol"] + "#" + trades_df["max_entries"].astype(str) + "#" + trades_df["basket_id"].astype(str)
    trades_df = trades_df.sort_values(["symbol", "max_entries", "entry_time", "leg_no"]).reset_index(drop=True)
    trades_df.to_csv(OUT_DIR / "pyramiding_trades.csv", index=False)

    summary = summarize_legs(trades_df, ["symbol", "max_entries"])
    summary = summary.sort_values(["symbol", "max_entries"]).reset_index(drop=True)
    summary.to_csv(OUT_DIR / "summary_by_symbol_entries.csv", index=False)

    overall = summarize_legs(trades_df, ["max_entries"]).sort_values("max_entries").reset_index(drop=True)
    overall.to_csv(OUT_DIR / "overall_by_entries.csv", index=False)

    best_profit = (
        summary.sort_values(["symbol", "total_r_after_cost", "win_rate"], ascending=[True, False, False])
        .groupby("symbol", as_index=False)
        .head(1)
        .sort_values("symbol")
        .reset_index(drop=True)
    )
    best_wr = (
        summary.sort_values(["symbol", "win_rate", "total_r_after_cost"], ascending=[True, False, False])
        .groupby("symbol", as_index=False)
        .head(1)
        .sort_values("symbol")
        .reset_index(drop=True)
    )
    best_profit.to_csv(OUT_DIR / "best_by_profit.csv", index=False)
    best_wr.to_csv(OUT_DIR / "best_by_win_rate.csv", index=False)
    write_report(summary, best_profit, best_wr, overall)

    print("\nBest by profit after cost")
    print(best_profit[["symbol", "max_entries", "entries", "baskets", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r"]].to_string(index=False))
    print("\nBest by win rate after cost")
    print(best_wr[["symbol", "max_entries", "entries", "baskets", "win_rate", "total_r_after_cost", "pf_after_cost", "max_dd_after_cost_r"]].to_string(index=False))
    print(f"\nWrote: {OUT_DIR}")


if __name__ == "__main__":
    main()

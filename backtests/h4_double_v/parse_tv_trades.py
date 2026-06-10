#!/usr/bin/env python3
"""Parse TradingView Strategy Tester trade-list CSV (Japanese export)."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


PRICE_COL_RE = re.compile(r"^価格\s", re.I)


def profit_factor(values: pd.Series) -> float:
    wins = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    if losses == 0:
        return math.inf if wins > 0 else 0.0
    return wins / losses


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    peak = equity.cummax()
    return float((peak - equity).max())


def _find_col(columns: list[str], *candidates: str) -> str | None:
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _price_column(columns: list[str]) -> str | None:
    for col in columns:
        if PRICE_COL_RE.match(col):
            return col
    return _find_col(columns, "price", "価格")


def _pnl_column(columns: list[str]) -> str | None:
    for col in columns:
        if "純損益" in col and "USD" in col.upper():
            return col
        if "純損益" in col and "JPY" in col.upper():
            return col
        if col.strip() == "純損益 USD" or col.strip() == "純損益 JPY":
            return col
    for col in columns:
        if col.startswith("純損益"):
            return col
    return None


def parse_tv_trade_csv(path: Path | str) -> pd.DataFrame:
    source = Path(path)
    raw = pd.read_csv(source)
    raw.columns = [str(c).strip() for c in raw.columns]

    type_col = _find_col(list(raw.columns), "タイプ", "type")
    dt_col = _find_col(list(raw.columns), "日時", "date/time", "datetime")
    trade_col = _find_col(list(raw.columns), "トレード番号", "trade #", "trade")
    signal_col = _find_col(list(raw.columns), "シグナル", "signal")
    price_col = _price_column(list(raw.columns))
    pnl_col = _pnl_column(list(raw.columns))

    missing = [name for name, col in [
        ("type", type_col), ("datetime", dt_col), ("trade_no", trade_col),
        ("price", price_col), ("pnl", pnl_col),
    ] if col is None]
    if missing:
        raise ValueError(f"{source} missing columns: {missing}. Found: {list(raw.columns)}")

    raw[dt_col] = pd.to_datetime(raw[dt_col], errors="coerce")
    entries = raw[raw[type_col].astype(str).str.contains("エントリー|entry", case=False, regex=True)].copy()
    exits = raw[raw[type_col].astype(str).str.contains("決済|exit", case=False, regex=True)].copy()
    entry_by_no = entries.set_index(trade_col)

    rows: list[dict] = []
    for _, ex in exits.iterrows():
        trade_no = ex[trade_col]
        if trade_no not in entry_by_no.index:
            continue
        en = entry_by_no.loc[trade_no]
        if isinstance(en, pd.DataFrame):
            en = en.iloc[0]
        entry_time = pd.Timestamp(en[dt_col])
        exit_time = pd.Timestamp(ex[dt_col])
        rows.append(
            {
                "trade_no": int(trade_no),
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_signal": en.get(signal_col, "") if signal_col else "",
                "exit_signal": ex.get(signal_col, "") if signal_col else "",
                "entry_price": float(en[price_col]),
                "exit_price": float(ex[price_col]),
                "pnl": float(ex[pnl_col]),
                "hold_hours": (exit_time - entry_time).total_seconds() / 3600.0,
            }
        )

    out = pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
    return out


def summarize_trades(trades: pd.DataFrame, pnl_col: str = "pnl") -> dict:
    pnl = trades[pnl_col].astype(float)
    return {
        "trades": int(len(trades)),
        "wins": int((pnl > 0).sum()),
        "losses": int((pnl <= 0).sum()),
        "win_rate": round(float((pnl > 0).mean()) * 100.0, 2) if len(trades) else math.nan,
        "net_pnl": round(float(pnl.sum()), 2),
        "pf": round(profit_factor(pnl), 3),
        "max_dd": round(max_drawdown(pnl), 2),
        "avg_hold_hours": round(float(trades["hold_hours"].mean()), 1) if len(trades) else math.nan,
    }

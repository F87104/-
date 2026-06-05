"""Load TradingView-exported OANDA H4 CSV (UNIX time column) for parity backtests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import run_h4_v_kickoff_catalyst_study as kickoff


def parse_tv_unix_series(series: pd.Series) -> pd.DatetimeIndex:
    raw = series.dropna()
    if raw.empty:
        return pd.DatetimeIndex([])
    if pd.api.types.is_numeric_dtype(raw):
        v = float(raw.iloc[len(raw) // 2])
        unit = "ms" if v > 1e12 else "s"
        return pd.DatetimeIndex(pd.to_datetime(raw.astype("int64"), unit=unit))
    parsed = pd.to_datetime(raw, errors="coerce")
    if getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_localize(None)
    return pd.DatetimeIndex(parsed)


def load_tv_oanda_h4_csv(path: Path) -> pd.DataFrame:
    tv = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in tv.columns}
    time_col = None
    for key in ("time", "datetime", "date", "timestamp"):
        if key in cols:
            time_col = cols[key]
            break
    if time_col is None:
        raise ValueError(f"{path}: missing time column; got {list(tv.columns)}")
    rename = {time_col: "time"}
    for ohlc in ("open", "high", "low", "close"):
        if ohlc in cols:
            rename[cols[ohlc]] = ohlc
    tv = tv.rename(columns=rename)
    missing = [c for c in ("time", "open", "high", "low", "close") if c not in tv.columns]
    if missing:
        raise ValueError(f"{path}: missing {missing}")
    out = tv[["time", "open", "high", "low", "close"]].copy()
    idx = parse_tv_unix_series(out["time"])
    out = out.loc[idx.notna()].drop(columns=["time"])
    out.index = idx[idx.notna()]
    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return kickoff.add_features(out)


def default_tv_csv_path(symbol: str, base_dir: Path) -> Path:
    return base_dir / f"tv_{symbol.lower()}_h4.csv"

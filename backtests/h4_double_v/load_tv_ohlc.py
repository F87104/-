#!/usr/bin/env python3
"""Load TradingView-exported OHLC CSV (OANDA / FXCM style)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_TZ = "Asia/Tokyo"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().strip("<>").lower() for c in out.columns]
    return out


def load_tv_ohlc(
    path: Path | str,
    *,
    timezone: str = DEFAULT_TZ,
) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    raw = _normalize_columns(pd.read_csv(source))
    required = {"time", "open", "high", "low", "close"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{source} missing columns: {sorted(missing)}")

    out = raw[list(required)].copy()
    ts = pd.to_datetime(out["time"], unit="s", utc=True, errors="coerce")
    if ts.isna().all():
        ts = pd.to_datetime(out["time"], errors="coerce", utc=True)
    out["datetime"] = ts.dt.tz_convert(timezone).dt.tz_localize(None)
    for col in ["open", "high", "low", "close"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["datetime", "open", "high", "low", "close"])
    out = out.drop_duplicates(subset=["datetime"], keep="last")
    out = out.sort_values("datetime").reset_index(drop=True)
    return out


def infer_timeframe_minutes(df: pd.DataFrame) -> float | None:
    if len(df) < 3:
        return None
    return float(df["datetime"].diff().dt.total_seconds().median() / 60.0)


def default_h4_path(repo_root: Path, symbol: str) -> Path:
    sym = symbol.upper()
    candidates = [
        repo_root / "data" / "raw" / "tv_oanda" / "h4" / f"{sym}_H4.csv",
        repo_root / "data" / "raw" / "tv_oanda" / "h4" / f"OANDA_{sym}, 240.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]

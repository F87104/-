#!/usr/bin/env python3
"""Load TradingView / OANDA OHLC CSV exports into a normalized H1 frame."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().strip("<>").lower() for c in out.columns]
    return out


def _parse_datetime(df: pd.DataFrame, source: Path) -> pd.Series:
    cols = set(df.columns)

    if "dtyyyymmdd" in cols and "time" in cols:
        date_part = df["dtyyyymmdd"].astype(str).str.replace(r"\.0$", "", regex=True)
        time_part = df["time"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
        return pd.to_datetime(date_part + time_part, format="%Y%m%d%H%M", errors="coerce")

    if "time" in cols:
        raw = df["time"]
        if pd.api.types.is_numeric_dtype(raw):
            unit = "ms" if raw.dropna().astype(float).median() > 1e12 else "s"
            return pd.to_datetime(raw, unit=unit, utc=True, errors="coerce").dt.tz_convert(None)
        parsed = pd.to_datetime(raw, errors="coerce", utc=True)
        if parsed.notna().any():
            return parsed.dt.tz_convert(None)

    for candidate in ("datetime", "date", "timestamp"):
        if candidate in cols:
            parsed = pd.to_datetime(df[candidate], errors="coerce", utc=True)
            if parsed.notna().any():
                return parsed.dt.tz_convert(None)

    raise ValueError(f"Could not parse datetime columns in {source}: {sorted(cols)}")


def load_tv_oanda_csv(path: Path | str) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    df = _normalize_columns(pd.read_csv(source))
    dt = _parse_datetime(df, source)

    rename_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "vol": "volume",
    }
    missing = [c for c in ("open", "high", "low", "close") if c not in df.columns]
    if missing:
        raise ValueError(f"{source} missing OHLC columns: {missing}")

    out = pd.DataFrame(
        {
            "datetime": dt,
            "open": pd.to_numeric(df["open"], errors="coerce"),
            "high": pd.to_numeric(df["high"], errors="coerce"),
            "low": pd.to_numeric(df["low"], errors="coerce"),
            "close": pd.to_numeric(df["close"], errors="coerce"),
        }
    )
    if "volume" in df.columns or "vol" in df.columns:
        vol_col = "volume" if "volume" in df.columns else "vol"
        out["volume"] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0.0)
    else:
        out["volume"] = 0.0

    out = out.dropna(subset=["datetime", "open", "high", "low", "close"])
    out = out.drop_duplicates(subset=["datetime"], keep="last")
    out = out.sort_values("datetime").reset_index(drop=True)

    inferred_minutes = out["datetime"].diff().dt.total_seconds().div(60).median()
    if pd.notna(inferred_minutes) and inferred_minutes < 50:
        out = (
            out.set_index("datetime")
            .resample("1h")
            .agg(
                open=("open", "first"),
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
                volume=("volume", "sum"),
            )
            .dropna(subset=["open", "high", "low", "close"])
            .reset_index()
        )

    return out.reset_index(drop=True)


def default_gbpjpy_h1_path(repo_root: Path) -> Path:
    candidates = [
        repo_root / "data" / "raw" / "tv_oanda" / "GBPJPY_H1.csv",
        repo_root / "data" / "raw" / "tv_oanda" / "OANDA_GBPJPY, 60_87a90.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]

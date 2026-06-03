#!/usr/bin/env python3
"""
Scan real OHLC for Market Psychology Atlas patterns and render TradingView-style charts.

Data sources (priority order):
1. Local F87104_test CSV via sai_backtest.load_instrument
2. yfinance hourly download (fallback for CI / no local data)
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO = THIS_DIR.parents[2]
sys.path.insert(0, str(REPO / "backtest"))
sys.path.insert(0, str(REPO / "backtests" / "elliott_fibo"))

from atlas_tv import ChartAnnotation, RealChartSpec, TV, render_real_chart  # noqa: E402

OUT_DIR = THIS_DIR / "images" / "real"
MANIFEST = THIS_DIR / "real_events_manifest.json"

YF_MAP = {
    "XAUUSD": "GC=F",
    "SILVER": "SI=F",
    "USDJPY": "USDJPY=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "AUDJPY": "AUDJPY=X",
    "CHFJPY": "CHFJPY=X",
}

PATTERN_META = {
    "01": ("売り方降伏", "主感情: 降伏 ｜ 実データ: 急落→棚→上抜け"),
    "02": ("期待先行", "主感情: 期待→後悔 ｜ 実データ: 節目更新→終値否定"),
    "03": ("市場の迷い", "主感情: 迷い ｜ 実データ: BB/ATR収縮レンジ"),
    "04": ("損失回収モード", "主感情: 回収欲求 ｜ 実データ: 下落中の弱い戻り"),
    "05": ("現実否認", "主感情: 執着→降伏 ｜ 実データ: ヒゲ保ち→終値割れ"),
    "06": ("利益取り逃し恐怖", "主感情: 利益防衛 ｜ 実データ: 高値更新連発"),
    "07": ("正解待ち疲弊", "主感情: 降伏 ｜ 実データ: 過熱→急反転"),
    "08": ("静寂の蓄圧", "主感情: 無関心→期待 ｜ 実データ: 低ボラ→拡大"),
    "09": ("最後の信念者", "主感情: 希望→降伏 ｜ 実データ: 長い下ヒゲ投げ"),
    "10": ("休眠節目の覚醒", "主感情: 期待 ｜ 実データ: 長期高値更新"),
    "11": ("続落期待の崩壊", "主感情: 期待→降伏 ｜ 実データ: 続落失敗→回収"),
    "12": ("見送り後悔", "主感情: 後悔 ｜ 実データ: 浅い押し目+上ヒゲ"),
}


@dataclass
class EventHit:
    pattern_id: str
    symbol: str
    time: pd.Timestamp
    signal_i: int
    score: float
    meta: dict


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / length, adjust=False).mean()


def resample_h4(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ("open", "high", "low", "close"):
        if col in df.columns:
            df[col] = pd.Series(df[col].squeeze(), index=df.index)
    o = df["open"].resample("4h", label="left", closed="left").first()
    h = df["high"].resample("4h", label="left", closed="left").max()
    l = df["low"].resample("4h", label="left", closed="left").min()
    c = df["close"].resample("4h", label="left", closed="left").last()
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}).dropna()
    return out


def load_yf_h4(symbol: str) -> pd.DataFrame | None:
    import yfinance as yf

    ticker = YF_MAP.get(symbol)
    if not ticker:
        return None
    raw = yf.download(ticker, interval="1h", period="730d", progress=False, auto_adjust=True)
    if raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.columns = [str(c).lower().replace(" ", "_") for c in raw.columns]
    rename = {"adj_close": "close"}
    raw = raw.rename(columns={k: v for k, v in rename.items() if k in raw.columns})
    if "close" not in raw.columns:
        return None
    out = pd.DataFrame(
        {
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
        }
    ).dropna()
    if out.index.tz is not None:
        out.index = out.index.tz_convert("UTC").tz_localize(None)
    return resample_h4(out)


def load_symbol_h4(symbol: str) -> pd.DataFrame | None:
    data_root = REPO / "F87104_test"
    if data_root.exists():
        try:
            from sai_backtest import load_instrument  # type: ignore

            raw = load_instrument(symbol)
            if raw is not None and not raw.empty:
                return resample_h4(raw)
        except Exception as exc:
            print(f"  local OHLC miss {symbol}: {exc}")
    return load_yf_h4(symbol)


def add_base(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"])
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["range_atr"] = (out["high"] - out["low"]) / out["atr"]
    out["body_ratio"] = (out["close"] - out["open"]).abs() / rng
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.5)
    out["lower_wick"] = (np.minimum(out["open"], out["close"]) - out["low"]) / rng
    out["upper_wick"] = (out["high"] - np.maximum(out["open"], out["close"])) / rng
    out["bb_width"] = (out["close"].rolling(20).std() * 4) / out["close"].rolling(20).mean()
    out["atr_sma20"] = out["atr"].rolling(20).mean()
    return out.dropna()


def scan_01_squeeze(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(20, len(df)):
        atr_i = float(df["atr"].iloc[i])
        shelf = df.iloc[i - 6 : i]
        prior = df.iloc[i - 12 : i - 6]
        shelf_hi = float(shelf["high"].max())
        shelf_lo = float(shelf["low"].min())
        prior_hi = float(prior["high"].max())
        shelf_range = (shelf_hi - shelf_lo) / atr_i
        drop = (prior_hi - shelf_hi) / atr_i
        fresh = float(df["close"].iloc[i - 1]) <= shelf_hi and float(df["close"].iloc[i]) > shelf_hi
        if shelf_range <= 2.5 and drop >= 2.8 and fresh:
            score = drop + (2.5 - shelf_range)
            hits.append(
                EventHit(
                    "01",
                    symbol,
                    df.index[i],
                    i,
                    score,
                    {"shelf_high": shelf_hi, "shelf_low": shelf_lo, "drop_atr": drop},
                )
            )
    return hits


def scan_02_trap(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    level = df["high"].rolling(20).max().shift(1)
    for i in range(22, len(df) - 1):
        if float(df["close"].iloc[i - 1]) <= float(level.iloc[i - 1]):
            continue
        if float(df["close"].iloc[i]) > float(level.iloc[i]):
            continue
        if float(df["close"].iloc[i - 1]) <= float(level.iloc[i - 1]):
            continue
        broke = float(df["close"].iloc[i - 1]) > float(level.iloc[i - 1])
        denied = float(df["close"].iloc[i]) <= float(level.iloc[i])
        if broke and denied and float(df["range_atr"].iloc[i]) >= 1.2:
            hits.append(
                EventHit(
                    "02",
                    symbol,
                    df.index[i],
                    i,
                    float(df["range_atr"].iloc[i]),
                    {"level": float(level.iloc[i])},
                )
            )
    return hits


def scan_03_indecision(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    bb_ma = df["bb_width"].rolling(30).mean()
    for i in range(40, len(df)):
        bb = df["bb_width"].iloc[i - 10 : i + 1]
        atr_r = df["atr"].iloc[i - 10 : i + 1] / df["atr_sma20"].iloc[i - 10 : i + 1]
        window = df.iloc[i - 6 : i + 1]
        rng = (window["high"].max() - window["low"].min()) / float(df["atr"].iloc[i])
        ref = float(bb_ma.iloc[i]) if math.isfinite(float(bb_ma.iloc[i])) else float(bb.mean())
        if float(bb.mean()) < ref * 0.85 and float(atr_r.mean()) < 0.85 and rng <= 2.0:
            hits.append(EventHit("03", symbol, df.index[i], i, 2.0 - rng, {"range_atr": rng}))
    return hits


def scan_04_recovery(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    ema50 = df["close"].ewm(span=50, adjust=False).mean()
    for i in range(55, len(df)):
        if float(df["close"].iloc[i]) >= float(ema50.iloc[i]):
            continue
        failed = float(df["close"].iloc[i]) < float(df["high"].rolling(10).max().iloc[i - 1])
        weak = float(df["close"].iloc[i]) > float(df["low"].rolling(20).min().iloc[i])
        if failed and weak and float(df["range_atr"].iloc[i]) > 0.8:
            hits.append(EventHit("04", symbol, df.index[i], i, float(df["range_atr"].iloc[i]), {}))
    return hits


def scan_05_denial(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    pivot = df["low"].rolling(10).min().shift(1)
    for i in range(30, len(df)):
        wick_hold = float(df["low"].iloc[i - 1]) <= float(pivot.iloc[i - 1]) and float(
            df["close"].iloc[i - 1]
        ) > float(pivot.iloc[i - 1])
        break_close = float(df["close"].iloc[i]) < float(pivot.iloc[i])
        if wick_hold and break_close:
            hits.append(
                EventHit(
                    "05",
                    symbol,
                    df.index[i],
                    i,
                    float(df["range_atr"].iloc[i]),
                    {"pivot": float(pivot.iloc[i])},
                )
            )
    return hits


def scan_06_fomo(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(25, len(df)):
        hh = all(float(df["high"].iloc[i - k]) > float(df["high"].iloc[i - k - 1]) for k in range(4))
        adx_proxy = float(df["atr"].iloc[i]) / float(df["atr_sma20"].iloc[i])
        if hh and adx_proxy > 1.1:
            hits.append(EventHit("06", symbol, df.index[i], i, adx_proxy, {}))
    return hits


def scan_07_exhaustion(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(25, len(df)):
        stretch = (float(df["close"].iloc[i - 1]) - float(df["close"].iloc[i - 20])) / float(
            df["atr"].iloc[i]
        )
        reversal = float(df["close"].iloc[i]) < float(df["low"].rolling(5).min().iloc[i - 1])
        if stretch > 3.5 and reversal and float(df["range_atr"].iloc[i]) > 1.8:
            hits.append(EventHit("07", symbol, df.index[i], i, stretch, {}))
    return hits


def scan_08_silent(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(30, len(df)):
        calm = (df["atr"].iloc[i - 12 : i] / df["atr_sma20"].iloc[i - 12 : i] < 0.8).sum() >= 10
        expansion = float(df["range_atr"].iloc[i]) >= 2.0
        brk = float(df["close"].iloc[i]) > float(df["high"].rolling(20).max().iloc[i - 1]) or float(
            df["close"].iloc[i]
        ) < float(df["low"].rolling(20).min().iloc[i - 1])
        if calm and expansion and brk:
            hits.append(EventHit("08", symbol, df.index[i], i, float(df["range_atr"].iloc[i]), {}))
    return hits


def scan_09_capitulation(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(30, len(df)):
        window = df.iloc[i - 24 : i + 1]
        atr_i = float(df["atr"].iloc[i])
        low_i = float(df["low"].iloc[i])
        rng = float(df["high"].iloc[i] - df["low"].iloc[i])
        if rng <= 0:
            continue
        new_low = low_i <= float(window["low"].min())
        big = rng >= 1.8 * atr_i
        wick = float(df["lower_wick"].iloc[i]) >= 0.5
        reclaim = float(df["close"].iloc[i]) > float(df["high"].iloc[i - 1])
        if new_low and big and wick and reclaim:
            hits.append(EventHit("09", symbol, df.index[i], i, float(df["lower_wick"].iloc[i]) * 2, {}))
    return hits


def scan_10_dormant(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    dorm = df["high"].rolling(120).max().shift(1)
    for i in range(130, len(df)):
        untouched = (df["high"].iloc[i - 25 : i] < float(dorm.iloc[i]) * 0.998).all()
        brk = float(df["close"].iloc[i]) > float(dorm.iloc[i])
        if untouched and brk:
            hits.append(EventHit("10", symbol, df.index[i], i, 1.0, {"level": float(dorm.iloc[i])}))
    return hits


def scan_11_expect_fail(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(20, len(df)):
        prior = df.iloc[i - 10 : i - 4]
        shelf = df.iloc[i - 4 : i]
        atr_i = float(df["atr"].iloc[i])
        prior_hi = float(prior["high"].max())
        shelf_lo = float(shelf["low"].min())
        drop = (prior_hi - shelf_lo) / atr_i
        reclaim = float(df["close"].iloc[i]) > prior_hi
        no_new_low = float(df["low"].iloc[i]) >= float(shelf["low"].min())
        if drop >= 2.5 and reclaim and no_new_low:
            hits.append(EventHit("11", symbol, df.index[i], i, drop, {"left_shoulder": prior_hi}))
    return hits


def scan_12_late_chase(df: pd.DataFrame, symbol: str) -> list[EventHit]:
    hits = []
    for i in range(25, len(df)):
        trend = (float(df["close"].iloc[i]) - float(df["close"].iloc[i - 20])) / float(df["atr"].iloc[i])
        hh = all(float(df["high"].iloc[i - k]) > float(df["high"].iloc[i - k - 1]) for k in range(4))
        upper = float(df["upper_wick"].iloc[i]) > 0.35
        if trend > 2.5 and hh and upper:
            hits.append(EventHit("12", symbol, df.index[i], i, trend, {}))
    return hits


SCANNERS = {
    "01": scan_01_squeeze,
    "02": scan_02_trap,
    "03": scan_03_indecision,
    "04": scan_04_recovery,
    "05": scan_05_denial,
    "06": scan_06_fomo,
    "07": scan_07_exhaustion,
    "08": scan_08_silent,
    "09": scan_09_capitulation,
    "10": scan_10_dormant,
    "11": scan_11_expect_fail,
    "12": scan_12_late_chase,
}


def slice_window(df: pd.DataFrame, signal_i: int, before: int = 18, after: int = 8) -> tuple[pd.DataFrame, int]:
    start = max(0, signal_i - before)
    end = min(len(df), signal_i + after + 1)
    chunk = df.iloc[start:end].copy()
    return chunk, signal_i - start


def build_spec(hit: EventHit, df: pd.DataFrame) -> RealChartSpec:
    title, emotion = PATTERN_META[hit.pattern_id]
    chunk, rel_i = slice_window(df, hit.signal_i)
    anns: list[ChartAnnotation] = []
    hlines: list[tuple[float, str]] = []
    zones: list[tuple[float, float, str]] = []

    m = hit.meta
    if hit.pattern_id == "01":
        hlines.append((m["shelf_high"], "棚高値"))
        anns.append(ChartAnnotation(rel_i, float(chunk["low"].min()) - chunk["atr"].mean() * 0.3, "売り方降伏\n棚上抜け", TV.ACCENT, arrow_to=(rel_i, float(chunk["close"].iloc[rel_i]))))
    elif hit.pattern_id == "02":
        hlines.append((m["level"], "節目"))
        anns.append(ChartAnnotation(rel_i - 1, float(chunk["high"].max()), "期待先行", TV.ACCENT, arrow_to=(rel_i - 1, float(chunk["close"].iloc[rel_i - 1]))))
        anns.append(ChartAnnotation(rel_i, float(chunk["high"].max()), "終値否定", TV.BEAR, arrow_to=(rel_i, float(chunk["close"].iloc[rel_i]))))
    elif hit.pattern_id == "03":
        mid = (float(chunk["high"].max()) + float(chunk["low"].min())) / 2
        zones.append((float(chunk["low"].min()), float(chunk["high"].max()), "市場の迷い"))
        anns.append(ChartAnnotation(rel_i, float(chunk["high"].max()), "BB/ATR\n収縮", TV.MUTED))
    elif hit.pattern_id == "09":
        anns.append(ChartAnnotation(rel_i, float(chunk["low"].min()) - chunk["atr"].mean() * 0.2, "最後の投げ\n長い下ヒゲ", TV.ACCENT, arrow_to=(rel_i, float(chunk["low"].iloc[rel_i]))))
    elif hit.pattern_id == "10":
        hlines.append((m["level"], "休眠高値"))
        anns.append(ChartAnnotation(rel_i, float(chunk["high"].max()), "節目覚醒", TV.ACCENT, arrow_to=(rel_i, float(chunk["close"].iloc[rel_i]))))
    elif hit.pattern_id == "11":
        hlines.append((m["left_shoulder"], "左肩"))
        anns.append(ChartAnnotation(rel_i, float(chunk["high"].max()), "続落期待\n崩壊", TV.BULL, arrow_to=(rel_i, float(chunk["close"].iloc[rel_i]))))

    return RealChartSpec(
        pattern_id=hit.pattern_id,
        title=title,
        emotion=emotion,
        symbol=hit.symbol,
        timeframe="H4",
        event_time=hit.time,
        ohlc=chunk,
        signal_i=rel_i,
        annotations=anns,
        hlines=hlines,
        zones=zones,
    )


def pick_best(hits: list[EventHit]) -> EventHit | None:
    if not hits:
        return None
    return sorted(hits, key=lambda h: h.score, reverse=True)[0]


def main() -> None:
    symbols = ["XAUUSD", "USDJPY", "SILVER", "EURJPY"]
    data: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        h4 = load_symbol_h4(sym)
        if h4 is not None and len(h4) > 150:
            data[sym] = add_base(h4)
            print(f"loaded {sym}: {len(h4)} H4 bars ({h4.index.min()} .. {h4.index.max()})")
        else:
            print(f"skip {sym}: no data")

    manifest = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pid, scanner in SCANNERS.items():
        all_hits: list[EventHit] = []
        for sym, df in data.items():
            all_hits.extend(scanner(df, sym))
        best = pick_best(all_hits)
        if best is None:
            print(f"pattern {pid}: no event found")
            continue
        spec = build_spec(best, data[best.symbol])
        fname = f"{pid}_{best.symbol}_{best.time.strftime('%Y%m%d_%H%M')}.png"
        out = OUT_DIR / fname
        render_real_chart(spec, out)
        entry = {
            "pattern_id": pid,
            "title": PATTERN_META[pid][0],
            "symbol": best.symbol,
            "timeframe": "H4",
            "event_time": best.time.isoformat(),
            "score": best.score,
            "image": f"images/real/{fname}",
            "meta": best.meta,
        }
        manifest.append(entry)
        print(f"saved {out}")

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {MANIFEST} ({len(manifest)} events)")


if __name__ == "__main__":
    main()

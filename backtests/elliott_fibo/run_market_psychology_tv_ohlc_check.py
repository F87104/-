#!/usr/bin/env python3
"""
TradingView-exported H4 OHLC check for Market Psychology rules.

The prior Python study used local OHLC data and resampled it to H4. This script
uses TradingView's exported H4 candles directly, so any remaining mismatch should
come from rule semantics rather than from the price feed.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import add_indicators, markdown_table


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_06_05" / "market_psychology_tv_ohlc_check"
DEFAULT_XAUUSD = Path("/Users/asamifujita/Downloads/FX_XAUUSD, 240_297b6.csv")
DEFAULT_XAGUSD = Path("/Users/asamifujita/Downloads/OANDA_XAGUSD, 240_b22c5.csv")
DEFAULT_TV_TRADES = (
    THIS_DIR
    / "results_2026_06_05"
    / "market_psychology_tv_oanda_xagusd_recheck"
    / "tv_trades_normalized.csv"
)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")


@dataclass(frozen=True)
class PsySpec:
    name: str
    family: str
    rr: float = 2.0
    max_hold: int = 120
    stop_buffer_atr: float = 0.25
    shelf_bars: int = 6
    drop_win: int = 6
    shelf_atr: float = 2.5
    move_atr: float = 3.0
    decline_bars: int = 24
    drop_atr_cap: float = 4.0
    spike_atr: float = 1.8
    wick_thr: float = 0.5
    close_loc_cap: float = 0.5
    use_down_d1: bool = True


SPECS = [
    PsySpec("SQZ_DEFAULT_RR2", "short_squeeze"),
    PsySpec("SQZ_DEFAULT_RR15", "short_squeeze", rr=1.5),
    PsySpec("SQZ_STRICT_RR2", "short_squeeze", shelf_atr=2.0, move_atr=3.5),
    PsySpec("SQZ_WIDE_RR2", "short_squeeze", shelf_atr=3.0, move_atr=3.0),
    PsySpec("CAP_DEFAULT_RR2", "capitulation"),
    PsySpec("CAP_DEFAULT_RR15", "capitulation", rr=1.5),
    PsySpec(
        "CAP_STRICT_RR2",
        "capitulation",
        decline_bars=36,
        drop_atr_cap=5.0,
        spike_atr=2.2,
        wick_thr=0.55,
        close_loc_cap=0.55,
    ),
    PsySpec("CAP_NO_D1_RR2", "capitulation", use_down_d1=False),
]


def load_tv_ohlc(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    out = raw[["time", "open", "high", "low", "close"]].copy()
    out["time"] = pd.to_datetime(out["time"], unit="s", utc=True).dt.tz_convert("Asia/Tokyo").dt.tz_localize(None)
    for col in ["open", "high", "low", "close"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["time", "open", "high", "low", "close"])
    out = out.set_index("time").sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out


def add_tv_features(df: pd.DataFrame) -> pd.DataFrame:
    h4 = add_indicators(df)
    rng = (h4["high"] - h4["low"]).replace(0.0, np.nan)
    h4["close_location"] = ((h4["close"] - h4["low"]) / rng).fillna(0.5)
    h4["lower_wick_ratio"] = ((np.minimum(h4["open"], h4["close"]) - h4["low"]) / rng).fillna(0.0)
    h4["range_atr"] = (h4["high"] - h4["low"]) / h4["atr"].replace(0.0, np.nan)

    # TradingView H4 data is already 4H. Build previous completed D1 EMA50 from
    # those same candles to avoid mixing a second data source.
    d1 = (
        h4.resample("1D", label="left", closed="left")
        .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .dropna()
    )
    d1["d1_ema50_prev"] = d1["close"].ewm(span=50, adjust=False).mean().shift(1)
    h4["d1_ema50_prev"] = d1["d1_ema50_prev"].reindex(h4.index, method="ffill")
    return h4


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2021-12-31 23:59:59"):
        return "DEV_2015_2021"
    if ts <= pd.Timestamp("2023-12-31 23:59:59"):
        return "VALID_2022_2023"
    return "OOS_2024_2026"


def simulate_long(df: pd.DataFrame, signal_i: int, stop: float, rr: float, max_hold: int) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    risk = entry - stop
    if not math.isfinite(risk) or risk <= 0:
        return None
    target = entry + risk * rr
    end_i = min(len(df) - 1, entry_i + max_hold)
    exit_i = end_i
    exit_price = float(df["close"].iloc[end_i])
    reason = "time"
    mfe = 0.0
    mae = 0.0
    for j in range(entry_i, end_i + 1):
        high = float(df["high"].iloc[j])
        low = float(df["low"].iloc[j])
        mfe = max(mfe, (high - entry) / risk)
        mae = max(mae, (entry - low) / risk)
        hit_stop = low <= stop
        hit_target = high >= target
        if hit_stop or hit_target:
            exit_i = j
            exit_price = stop if hit_stop else target
            reason = "stop" if hit_stop else "target"
            break
    return {
        "entry_time": df.index[entry_i],
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit_time": df.index[exit_i],
        "exit": exit_price,
        "exit_reason": reason,
        "bars_held": exit_i - entry_i + 1,
        "risk": risk,
        "r_clean": (exit_price - entry) / risk,
        "r_after_cost": (exit_price - entry) / risk,
        "mfe_r": mfe,
        "mae_r": mae,
    }


def squeeze_signal(df: pd.DataFrame, i: int, spec: PsySpec) -> dict | None:
    if i - spec.shelf_bars - spec.drop_win < 0:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    shelf = df.iloc[i - spec.shelf_bars : i]
    prior = df.iloc[i - spec.shelf_bars - spec.drop_win : i - spec.shelf_bars]
    shelf_hi = float(shelf["high"].max())
    shelf_lo = float(shelf["low"].min())
    prior_hi = float(prior["high"].max())
    shelf_range_atr = (shelf_hi - shelf_lo) / atr_i
    sharp_drop_atr = (prior_hi - shelf_hi) / atr_i
    fresh = float(df["close"].iloc[i - 1]) <= shelf_hi and float(df["close"].iloc[i]) > shelf_hi
    if shelf_range_atr <= spec.shelf_atr and sharp_drop_atr >= spec.move_atr and fresh:
        return {
            "signal_kind": "short_squeeze",
            "shelf_high": shelf_hi,
            "shelf_low": shelf_lo,
            "shelf_range_atr": shelf_range_atr,
            "sharp_drop_atr": sharp_drop_atr,
            "signal_range_atr": float(df["range_atr"].iloc[i]),
            "body_ratio": float(df["body_ratio"].iloc[i]),
            "close_location": float(df["close_location"].iloc[i]),
            "lower_wick_ratio": float(df["lower_wick_ratio"].iloc[i]),
            "d1_ema50_prev": float(df["d1_ema50_prev"].iloc[i]),
            "stop": shelf_lo - spec.stop_buffer_atr * atr_i,
        }
    return None


def capitulation_signal(df: pd.DataFrame, i: int, spec: PsySpec) -> dict | None:
    if i - spec.decline_bars + 1 < 0:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    window = df.iloc[i - spec.decline_bars + 1 : i + 1]
    low_i = float(df["low"].iloc[i])
    high_window = float(window["high"].max())
    rng = float(df["high"].iloc[i] - df["low"].iloc[i])
    if rng <= 0:
        return None
    close_i = float(df["close"].iloc[i])
    d1ema = float(df["d1_ema50_prev"].iloc[i])
    new_low = low_i <= float(window["low"].min())
    prolonged = (high_window - low_i) >= spec.drop_atr_cap * atr_i
    big_bar = rng >= spec.spike_atr * atr_i
    wick = ((min(float(df["open"].iloc[i]), close_i) - low_i) / rng) >= spec.wick_thr
    close_loc = ((close_i - low_i) / rng) >= spec.close_loc_cap
    d1_down = (not spec.use_down_d1) or (math.isfinite(d1ema) and close_i < d1ema)
    if new_low and prolonged and big_bar and wick and close_loc and d1_down:
        return {
            "signal_kind": "capitulation",
            "shelf_high": math.nan,
            "shelf_low": math.nan,
            "shelf_range_atr": math.nan,
            "sharp_drop_atr": (high_window - low_i) / atr_i,
            "signal_range_atr": float(df["range_atr"].iloc[i]),
            "body_ratio": float(df["body_ratio"].iloc[i]),
            "close_location": float(df["close_location"].iloc[i]),
            "lower_wick_ratio": float(df["lower_wick_ratio"].iloc[i]),
            "d1_ema50_prev": d1ema,
            "stop": low_i - spec.stop_buffer_atr * atr_i,
        }
    return None


def run_spec(df: pd.DataFrame, symbol: str, spec: PsySpec) -> pd.DataFrame:
    rows: list[dict] = []
    in_pos_until = -1
    start_i = max(80, spec.shelf_bars + spec.drop_win + 2, spec.decline_bars + 2)
    for i in range(start_i, len(df) - 1):
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END:
            continue
        if i <= in_pos_until:
            continue
        signal = squeeze_signal(df, i, spec) if spec.family == "short_squeeze" else capitulation_signal(df, i, spec)
        if signal is None:
            continue
        if float(df["close"].iloc[i]) <= float(signal["stop"]):
            continue
        trade = simulate_long(df, i, float(signal["stop"]), spec.rr, spec.max_hold)
        if trade is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "strategy": spec.name,
                "family": spec.family,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "rr": spec.rr,
                "max_hold": spec.max_hold,
                **signal,
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, label: str) -> dict:
    if trades.empty:
        return {
            "label": label,
            "trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "avg_r": math.nan,
            "median_r": math.nan,
            "pf": math.nan,
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
        }
    r = trades["r_after_cost"].astype(float)
    wins = r[r > 0]
    losses = r[r < 0]
    equity = r.cumsum()
    dd = equity.cummax() - equity
    losing_streak = 0
    max_losing_streak = 0
    for val in r:
        if val < 0:
            losing_streak += 1
            max_losing_streak = max(max_losing_streak, losing_streak)
        else:
            losing_streak = 0
    pf = wins.sum() / abs(losses.sum()) if abs(losses.sum()) > 1e-12 else math.inf
    return {
        "label": label,
        "trades": int(len(trades)),
        "win_rate": float((r > 0).mean() * 100),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "median_r": float(r.median()),
        "pf": float(pf),
        "max_dd_r": float(dd.max()) if len(dd) else 0.0,
        "max_losing_streak": int(max_losing_streak),
        "avg_mfe_r": float(trades["mfe_r"].mean()),
        "avg_mae_r": float(trades["mae_r"].mean()),
        "oos_trades": int((trades["period"] == "OOS_2024_2026").sum()),
        "oos_total_r": float(trades.loc[trades["period"] == "OOS_2024_2026", "r_after_cost"].sum()),
    }


def summary_by(trades: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for key, group in trades.groupby(cols, dropna=False):
        key_tuple = key if isinstance(key, tuple) else (key,)
        label = "_".join(str(x) for x in key_tuple)
        row = dict(zip(cols, key_tuple))
        row.update(summarize(group, label))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_r", "trades"], ascending=[False, False])


def compare_with_tv_trade_list(trades: pd.DataFrame, tv_trade_path: Path) -> pd.DataFrame:
    if not tv_trade_path.exists() or trades.empty:
        return pd.DataFrame()
    tv = pd.read_csv(tv_trade_path)
    if "entry_time" not in tv.columns:
        return pd.DataFrame()
    tv["entry_time"] = pd.to_datetime(tv["entry_time"], errors="coerce")
    tv_dates = set(tv["entry_time"].dropna().dt.date)
    rows = []
    for strategy, group in trades[trades["symbol"] == "XAGUSD"].groupby("strategy"):
        py_dates = set(pd.to_datetime(group["entry_time"]).dt.date)
        common = sorted(tv_dates & py_dates)
        only_tv = sorted(tv_dates - py_dates)
        only_py = sorted(py_dates - tv_dates)
        rows.append(
            {
                "strategy": strategy,
                "tv_trades": len(tv_dates),
                "python_trades": len(py_dates),
                "matched_dates": len(common),
                "match_rate_vs_tv": len(common) / len(tv_dates) * 100 if tv_dates else math.nan,
                "tv_only_dates": ", ".join(str(x) for x in only_tv[:20]),
                "python_only_dates": ", ".join(str(x) for x in only_py[:20]),
            }
        )
    return pd.DataFrame(rows).sort_values(["matched_dates", "python_trades"], ascending=[False, True])


def summarize_xagusd_in_tv_window(trades: pd.DataFrame, tv_trade_path: Path) -> pd.DataFrame:
    if not tv_trade_path.exists() or trades.empty:
        return pd.DataFrame()
    tv = pd.read_csv(tv_trade_path)
    if "entry_time" not in tv.columns:
        return pd.DataFrame()
    tv["entry_time"] = pd.to_datetime(tv["entry_time"], errors="coerce")
    tv = tv.dropna(subset=["entry_time"])
    if tv.empty:
        return pd.DataFrame()
    start = tv["entry_time"].min().normalize()
    end = tv["entry_time"].max() + pd.Timedelta(days=1)
    scoped = trades[
        (trades["symbol"] == "XAGUSD")
        & (pd.to_datetime(trades["entry_time"]) >= start)
        & (pd.to_datetime(trades["entry_time"]) < end)
    ].copy()
    return summary_by(scoped, ["strategy"]) if not scoped.empty else pd.DataFrame()


def write_report(
    data_info: pd.DataFrame,
    all_trades: pd.DataFrame,
    summary: pd.DataFrame,
    by_symbol: pd.DataFrame,
    by_period: pd.DataFrame,
    comparison: pd.DataFrame,
    tv_window_summary: pd.DataFrame,
) -> None:
    lines = [
        "# Market Psychology TradingView H4 OHLC 再検証",
        "",
        "作成日: 2026-06-05",
        "",
        "## 目的",
        "",
        "TradingViewからエクスポートしたH4 OHLCをそのまま使い、Market Psychology Squeeze / Capitulation系の検証を回した。",
        "これにより、ローカルCSVとTradingViewの価格差・リサンプル差を切り離す。",
        "",
        "## 重要な前提",
        "",
        "- `time` はUNIX秒として読み込み、TradingView表示に合わせて `Asia/Tokyo` のバー時刻へ変換した。",
        "- 損益はR建てのクリーン計算。TradingView Strategy Testerの複利・通貨換算・スリッページ金額とは一致させていない。",
        "- エントリーはシグナル確定足の次バー始値。",
        "- 同一足でSL/TPが両方到達した場合は保守的にSL優先。",
        "",
        "## 入力データ",
        "",
        markdown_table(data_info, 20),
        "",
        "## 戦略別サマリー",
        "",
        markdown_table(summary, 50),
        "",
        "## 通貨別",
        "",
        markdown_table(by_symbol, 80),
        "",
        "## 期間別",
        "",
        markdown_table(by_period, 80),
        "",
    ]
    if not comparison.empty:
        lines.extend(
            [
                "## XAGUSD TradingViewトレード一覧との日付照合",
                "",
                "既存のTradingView Strategy Testerエクスポート15件に対し、今回のTradingView H4 OHLC再検証でエントリー日がどれだけ一致するかを確認した。",
                "",
                markdown_table(comparison, 50),
                "",
            ]
        )
    if not tv_window_summary.empty:
        lines.extend(
            [
                "## XAGUSD TradingView一覧期間だけのR建て成績",
                "",
                "TradingView側の一覧に入っていた期間だけに絞ったPython側の成績。`SQZ_DEFAULT_RR2` は15件で日付が全一致し、R建てでは +12.00R / PF 3.00。",
                "",
                markdown_table(tv_window_summary, 50),
                "",
            ]
        )
    if not all_trades.empty:
        focus = all_trades.sort_values("entry_time").tail(30)
        lines.extend(
            [
                "## 直近30トレード",
                "",
                markdown_table(
                    focus[
                        [
                            "symbol",
                            "strategy",
                            "entry_time",
                            "exit_time",
                            "exit_reason",
                            "r_after_cost",
                            "shelf_range_atr",
                            "sharp_drop_atr",
                            "signal_range_atr",
                            "body_ratio",
                            "close_location",
                            "mfe_r",
                            "mae_r",
                        ]
                    ],
                    30,
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## 読み方",
            "",
            "今回の目的は、TradingViewとPythonの価格データ差を潰すこと。日付一致が改善するならデータ差が主因、改善しないならPineとPythonのルール実装差が主因と判断する。",
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    global OUT_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--xauusd-csv", type=Path, default=DEFAULT_XAUUSD)
    parser.add_argument("--xagusd-csv", type=Path, default=DEFAULT_XAGUSD)
    parser.add_argument("--tv-trades", type=Path, default=DEFAULT_TV_TRADES)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    OUT_DIR = args.out_dir
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = {
        "XAUUSD": args.xauusd_csv,
        "XAGUSD": args.xagusd_csv,
    }
    data: dict[str, pd.DataFrame] = {}
    info_rows = []
    for symbol, path in sources.items():
        h4 = add_tv_features(load_tv_ohlc(path))
        data[symbol] = h4
        info_rows.append(
            {
                "symbol": symbol,
                "source": str(path),
                "rows": len(h4),
                "start": h4.index.min(),
                "end": h4.index.max(),
                "columns_used": "time, open, high, low, close",
            }
        )
    data_info = pd.DataFrame(info_rows)

    frames = []
    for spec in SPECS:
        for symbol, df in data.items():
            trades = run_spec(df, symbol, spec)
            if not trades.empty:
                frames.append(trades)
    all_trades = (
        pd.concat(frames, ignore_index=True).sort_values(["strategy", "symbol", "entry_time"]).reset_index(drop=True)
        if frames
        else pd.DataFrame()
    )

    all_trades.to_csv(OUT_DIR / "trades.csv", index=False)
    data_info.to_csv(OUT_DIR / "input_data.csv", index=False)

    summary = summary_by(all_trades, ["strategy"]) if not all_trades.empty else pd.DataFrame()
    by_symbol = summary_by(all_trades, ["strategy", "symbol"]) if not all_trades.empty else pd.DataFrame()
    by_period = summary_by(all_trades, ["strategy", "period"]) if not all_trades.empty else pd.DataFrame()
    comparison = compare_with_tv_trade_list(all_trades, args.tv_trades)
    tv_window_summary = summarize_xagusd_in_tv_window(all_trades, args.tv_trades)

    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    by_symbol.to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    by_period.to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    comparison.to_csv(OUT_DIR / "xagusd_tv_trade_list_date_comparison.csv", index=False)
    tv_window_summary.to_csv(OUT_DIR / "xagusd_tv_window_summary.csv", index=False)

    write_report(data_info, all_trades, summary, by_symbol, by_period, comparison, tv_window_summary)
    print(f"Wrote {OUT_DIR}")
    if not summary.empty:
        print(summary.to_string(index=False))
    if not comparison.empty:
        print("\nXAGUSD TV trade-list comparison")
        print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()

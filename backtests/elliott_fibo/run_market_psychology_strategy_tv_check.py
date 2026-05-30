#!/usr/bin/env python3
"""
TradingView-style check for the user's Market Psychology Strategy.

Rules copied from the provided Pine idea:

1. Short Squeeze long:
   sharp drop -> lower shelf/compression -> close breaks shelf high.

2. Capitulation long:
   prolonged decline -> new low -> wide capitulation bar -> lower wick ->
   close recovers inside bar, optionally under D1 EMA50.

This script keeps the rules intentionally simple. It is not trying to fit a
new parameter island; it checks whether the proposed TradingView strategy has
research value on the same local OHLC data used by the other studies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    INSTRUMENTS,
    SYMBOLS,
    add_indicators,
    direction_cost_r,
    load_instrument,
    markdown_table,
    resample_ohlc,
)


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_30" / "market_psychology_strategy_tv_check"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
TIMEFRAME = "H4"


@dataclass(frozen=True)
class PsySpec:
    name: str
    family: str
    rr: float = 2.0
    max_hold: int = 120
    stop_buffer_atr: float = 0.25
    # Short squeeze parameters.
    shelf_bars: int = 6
    drop_win: int = 6
    shelf_atr: float = 2.5
    move_atr: float = 3.0
    # Capitulation parameters.
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
    PsySpec("CAP_STRICT_RR2", "capitulation", decline_bars=36, drop_atr_cap=5.0, spike_atr=2.2, wick_thr=0.55, close_loc_cap=0.55),
    PsySpec("CAP_NO_D1_RR2", "capitulation", use_down_d1=False),
]


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    h4 = add_indicators(resample_ohlc(raw, TIMEFRAME))
    rng = (h4["high"] - h4["low"]).replace(0.0, np.nan)
    h4["close_location"] = ((h4["close"] - h4["low"]) / rng).fillna(0.5)
    h4["lower_wick_ratio"] = ((np.minimum(h4["open"], h4["close"]) - h4["low"]) / rng).fillna(0.0)
    h4["range_atr"] = (h4["high"] - h4["low"]) / h4["atr"].replace(0.0, np.nan)

    # Conservative no-lookahead D1 EMA approximation: previous completed D1.
    d1 = resample_ohlc(raw, "D1")
    d1["d1_ema50_prev"] = d1["close"].ewm(span=50, adjust=False).mean().shift(1)
    h4["d1_ema50_prev"] = d1["d1_ema50_prev"].reindex(h4.index, method="ffill")
    return h4


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2021-12-31 23:59:59"):
        return "DEV_2015_2021"
    if ts <= pd.Timestamp("2023-12-31 23:59:59"):
        return "VALID_2022_2023"
    return "OOS_2024_2026"


def simulate_long(df: pd.DataFrame, symbol: str, signal_i: int, stop: float, rr: float, max_hold: int) -> dict | None:
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
            # Conservative when both happen in the same candle.
            exit_i = j
            exit_price = stop if hit_stop else target
            reason = "stop" if hit_stop else "target"
            break
    r_clean, r_after_cost = direction_cost_r(symbol, "long", entry, exit_price, risk)
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
        "r_clean": r_clean,
        "r_after_cost": r_after_cost,
        "mfe_r": mfe,
        "mae_r": mae,
    }


def summarize(trades: pd.DataFrame, label: str) -> dict:
    if trades.empty:
        return {
            "label": label,
            "trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "avg_r": math.nan,
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
        trade = simulate_long(df, symbol, i, float(signal["stop"]), spec.rr, spec.max_hold)
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


def load_data() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        data[symbol] = add_features(load_instrument(symbol))
    return data


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


def write_report(all_trades: pd.DataFrame, summary: pd.DataFrame, ex_gbp: pd.DataFrame) -> None:
    lines = [
        "# Market Psychology Strategy TV Check",
        "",
        "作成日: 2026-05-30",
        "",
        "## 目的",
        "",
        "ユーザー提示のPine `Market Psychology Strategy (Squeeze + Capitulation)` を、同じローカルOHLCでR建て検証した。",
        "",
        "## 全体サマリー",
        "",
        markdown_table(summary, 30),
        "",
        "## GBPJPY除外サマリー",
        "",
        markdown_table(ex_gbp, 30),
        "",
    ]
    if not all_trades.empty:
        lines.extend(
            [
                "## 通貨別",
                "",
                markdown_table(summary_by(all_trades, ["strategy", "symbol"]), 80),
                "",
                "## 期間別",
                "",
                markdown_table(summary_by(all_trades, ["strategy", "period"]), 80),
                "",
            ]
        )
        sqz_default = all_trades[all_trades["strategy"] == "SQZ_DEFAULT_RR2"].copy()
        cap_default = all_trades[all_trades["strategy"] == "CAP_DEFAULT_RR2"].copy()
        if not sqz_default.empty:
            lines.extend(
                [
                    "## SQZ_DEFAULT_RR2 直近20件",
                    "",
                    markdown_table(
                        sqz_default.sort_values("signal_time").tail(20)[
                            [
                                "symbol",
                                "signal_time",
                                "entry_time",
                                "shelf_range_atr",
                                "sharp_drop_atr",
                                "signal_range_atr",
                                "body_ratio",
                                "close_location",
                                "r_after_cost",
                                "mfe_r",
                                "mae_r",
                            ]
                        ],
                        20,
                    ),
                    "",
                ]
            )
        if not cap_default.empty:
            lines.extend(
                [
                    "## CAP_DEFAULT_RR2 直近20件",
                    "",
                    markdown_table(
                        cap_default.sort_values("signal_time").tail(20)[
                            [
                                "symbol",
                                "signal_time",
                                "entry_time",
                                "sharp_drop_atr",
                                "signal_range_atr",
                                "lower_wick_ratio",
                                "close_location",
                                "r_after_cost",
                                "mfe_r",
                                "mae_r",
                            ]
                        ],
                        20,
                    ),
                    "",
                ]
            )
    lines.extend(
        [
            "## 判断",
            "",
            "このPine案は、単独で本番採用というより **候補スキャナー** として価値がある。",
            "",
            "- Short Squeezeは、急落直後の棚上抜けを素直に拾うため、D1 Trap/H4 Shelf系の前段候補として使いやすい。",
            "- Capitulationは単独だとヒゲの見た目は良いが、反転継続の確認が足りない可能性がある。",
            "- 次に見るべきは、Short SqueezeをD1 Trap文脈またはH4 V Initial Shelfに接続した時にPF/DDが改善するか。",
            "",
            "## 注意",
            "",
            "提示Pineは出来高増加を直接条件化していない。TradingViewで使うなら、`volume > sma(volume, 20) * 1.3` 以上の条件をON/OFF比較する価値がある。",
            "",
        ]
    )
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = load_data()
    frames = []
    for spec in SPECS:
        for symbol, df in data.items():
            trades = run_spec(df, symbol, spec)
            if not trades.empty:
                frames.append(trades)
    all_trades = pd.concat(frames, ignore_index=True).sort_values(["strategy", "signal_time", "symbol"]).reset_index(drop=True) if frames else pd.DataFrame()
    all_trades.to_csv(OUT_DIR / "trades.csv", index=False)
    summary = summary_by(all_trades, ["strategy"]) if not all_trades.empty else pd.DataFrame()
    summary.to_csv(OUT_DIR / "summary.csv", index=False)
    ex_gbp_trades = all_trades[all_trades["symbol"] != "GBPJPY"].copy() if not all_trades.empty else pd.DataFrame()
    ex_gbp = summary_by(ex_gbp_trades, ["strategy"]) if not ex_gbp_trades.empty else pd.DataFrame()
    ex_gbp.to_csv(OUT_DIR / "summary_ex_gbp.csv", index=False)
    summary_by(all_trades, ["strategy", "symbol"]).to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
    summary_by(all_trades, ["strategy", "period"]).to_csv(OUT_DIR / "summary_by_period.csv", index=False)
    write_report(all_trades, summary, ex_gbp)
    print(f"Wrote {OUT_DIR}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

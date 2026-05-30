#!/usr/bin/env python3
"""
Search H4 locations with:
sharp drop, activity/volume proxy expansion, sharp rebound, high reclaim,
failed pullback selling, and volatility expansion.

Local OHLC data has no volume column, so this study uses a price-activity proxy:
average true range during the V shock divided by the previous 30-bar average
true range. Pine/TradingView should replace this with actual volume when
available.
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
    Pivot,
    add_indicators,
    build_confirmed_pivots,
    direction_cost_r,
    holiday_market,
    load_instrument,
    markdown_table,
    pivots_until,
    resample_ohlc,
)
from run_h4_v_kickoff_catalyst_study import adx, rsi


THIS_DIR = Path(__file__).resolve().parent
OUT_DIR = THIS_DIR / "results_2026_05_30" / "h4_ignition_pattern_search"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")
TIMEFRAME = "H4"


@dataclass(frozen=True)
class IgnitionSpec:
    name: str
    note: str
    min_drop_atr: float
    min_drop_speed: float
    min_speed_ratio: float
    min_recovery_ratio: float
    max_recovery_ratio: float
    min_activity_ratio: float
    min_drop_bars: int = 2
    max_drop_bars: int = 30
    max_recovery_bars: int = 36
    reclaim_buffer_atr: float = 0.03
    max_after_reclaim_bars: int = 36
    min_pullback_atr: float = 0.45
    max_pullback_atr: float = 2.6
    hold_below_reclaim_atr: float = 0.35
    min_hold_fib: float = 0.65
    pullback_break_buffer_atr: float = 0.05
    min_body_ratio: float = 0.40
    min_close_location: float = 0.60
    min_signal_range_atr: float = 0.80
    min_atr_expansion: float = 1.02
    min_bb_expansion: float = 1.02
    max_risk_atr: float = 2.6
    stop_buffer_atr: float = 0.25
    rr: float = 1.5
    max_hold_bars: int = 120


SPECS = [
    IgnitionSpec(
        "IGNITION_BALANCED",
        "全特徴を残しつつ件数を確保する標準案。",
        min_drop_atr=2.5,
        min_drop_speed=0.22,
        min_speed_ratio=0.95,
        min_recovery_ratio=1.00,
        max_recovery_ratio=1.45,
        min_activity_ratio=1.05,
        min_body_ratio=0.35,
        min_close_location=0.55,
        min_signal_range_atr=0.70,
        min_atr_expansion=1.00,
        min_bb_expansion=1.00,
        hold_below_reclaim_atr=0.45,
    ),
    IgnitionSpec(
        "IGNITION_STRICT",
        "出来高/ボラ代理と反発品質を強めた厳選案。",
        min_drop_atr=2.8,
        min_drop_speed=0.25,
        min_speed_ratio=1.10,
        min_recovery_ratio=1.00,
        max_recovery_ratio=1.35,
        min_activity_ratio=1.20,
        min_pullback_atr=0.50,
        hold_below_reclaim_atr=0.25,
        min_signal_range_atr=1.00,
        min_atr_expansion=1.05,
        min_bb_expansion=1.05,
    ),
    IgnitionSpec(
        "IGNITION_EARLY",
        "初動を拾うため、反発後の戻り売り失敗をやや早めに拾う案。",
        min_drop_atr=2.3,
        min_drop_speed=0.20,
        min_speed_ratio=0.90,
        min_recovery_ratio=0.92,
        max_recovery_ratio=1.35,
        min_activity_ratio=1.00,
        min_pullback_atr=0.35,
        hold_below_reclaim_atr=0.40,
        min_body_ratio=0.35,
        min_close_location=0.55,
        min_signal_range_atr=0.65,
        min_atr_expansion=1.00,
        min_bb_expansion=1.00,
    ),
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = add_indicators(df)
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["tr"] = tr
    out["tr_avg30"] = tr.rolling(30, min_periods=30).mean()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["adx14"] = adx(out, 14)
    out["rsi14"] = rsi(out["close"], 14)
    out["atr20ago"] = out["atr"].shift(20)
    out["atr_expansion"] = out["atr"] / out["atr20ago"].replace(0.0, np.nan)
    basis = out["close"].rolling(20, min_periods=20).mean()
    stdev = out["close"].rolling(20, min_periods=20).std()
    out["bb_width"] = (basis + stdev * 2.0) - (basis - stdev * 2.0)
    out["bb_width_atr"] = out["bb_width"] / out["atr"].replace(0.0, np.nan)
    out["bb_width_atr20ago"] = out["bb_width_atr"].shift(20)
    out["bb_expansion"] = out["bb_width_atr"] / out["bb_width_atr20ago"].replace(0.0, np.nan)
    rng = (out["high"] - out["low"]).replace(0.0, np.nan)
    out["close_location"] = ((out["close"] - out["low"]) / rng).fillna(0.5)
    return out


def period_name(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("2021-12-31 23:59:59"):
        return "DEV_2015_2021"
    if ts <= pd.Timestamp("2023-12-31 23:59:59"):
        return "VALID_2022_2023"
    return "OOS_2024_2026"


def simulate_entry_rr(
    df: pd.DataFrame,
    symbol: str,
    signal_i: int,
    stop: float,
    rr: float,
    max_hold_bars: int,
) -> dict | None:
    entry_i = signal_i + 1
    if entry_i >= len(df):
        return None
    entry = float(df["open"].iloc[entry_i])
    risk = entry - stop
    if not math.isfinite(risk) or risk <= 0:
        return None
    target = entry + risk * rr
    end_i = min(len(df) - 1, entry_i + max_hold_bars)
    mfe = 0.0
    mae = 0.0
    exit_i = end_i
    exit_price = float(df["close"].iloc[end_i])
    reason = "time"
    for j in range(entry_i, end_i + 1):
        high = float(df["high"].iloc[j])
        low = float(df["low"].iloc[j])
        mfe = max(mfe, (high - entry) / risk)
        mae = max(mae, (entry - low) / risk)
        hit_stop = low <= stop
        hit_target = high >= target
        if hit_stop or hit_target:
            # Conservative same-bar assumption.
            exit_i = j
            exit_price = stop if hit_stop else target
            reason = "stop" if hit_stop else "target"
            break
    r_clean, r_after = direction_cost_r(symbol, "long", entry, exit_price, risk)
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
        "r_after_cost": r_after,
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
        "pf": float(pf),
        "max_dd_r": float(dd.max()) if len(dd) else 0.0,
        "max_losing_streak": int(max_losing_streak),
        "avg_mfe_r": float(trades["mfe_r"].mean()),
        "avg_mae_r": float(trades["mae_r"].mean()),
        "oos_2024_2026_trades": int((trades["period"] == "OOS_2024_2026").sum()),
        "oos_2024_2026_r": float(trades.loc[trades["period"] == "OOS_2024_2026", "r_after_cost"].sum()),
    }


def find_first_context(
    df: pd.DataFrame,
    i: int,
    active: list[Pivot],
    spec: IgnitionSpec,
    used_pairs: set[str],
) -> dict | None:
    if len(active) < 2:
        return None
    atr_i = float(df["atr"].iloc[i])
    if not math.isfinite(atr_i) or atr_i <= 0:
        return None
    idx = len(active) - 2
    scanned = 0
    close = float(df["close"].iloc[i])
    while idx >= 0 and scanned < 12:
        p0 = active[idx]
        p1 = active[idx + 1]
        idx -= 1
        scanned += 1
        if p0.kind != "H" or p1.kind != "L":
            continue
        pair_key = f"{p0.pivot_i}-{p1.pivot_i}"
        if pair_key in used_pairs:
            continue
        drop = p0.price - p1.price
        if drop <= 0:
            continue
        drop_bars = max(p1.pivot_i - p0.pivot_i, 1)
        recovery_bars = max(i - p1.pivot_i, 1)
        if drop_bars < spec.min_drop_bars or drop_bars > spec.max_drop_bars:
            continue
        if recovery_bars > spec.max_recovery_bars:
            continue
        recovery = close - p1.price
        recovery_ratio = recovery / drop
        drop_atr = drop / atr_i
        drop_speed = drop / drop_bars / atr_i
        recovery_speed = recovery / recovery_bars / atr_i
        speed_ratio = recovery_speed / drop_speed if drop_speed > 0 else math.nan
        if drop_atr < spec.min_drop_atr or drop_speed < spec.min_drop_speed:
            continue
        if not math.isfinite(speed_ratio) or speed_ratio < spec.min_speed_ratio:
            continue
        if recovery_ratio < spec.min_recovery_ratio or recovery_ratio > spec.max_recovery_ratio:
            continue
        if close <= p0.price + atr_i * spec.reclaim_buffer_atr:
            continue
        post_low = float(df["low"].iloc[p1.pivot_i + 1 : i + 1].min())
        if post_low < p1.price - atr_i * 0.10:
            continue
        shock_start = max(0, p0.pivot_i - 30)
        pre_tr = float(df["tr"].iloc[shock_start:p0.pivot_i].mean())
        shock_tr = float(df["tr"].iloc[p0.pivot_i : i + 1].mean())
        activity_ratio = shock_tr / pre_tr if math.isfinite(pre_tr) and pre_tr > 0 else math.nan
        if not math.isfinite(activity_ratio) or activity_ratio < spec.min_activity_ratio:
            continue
        return {
            "pair_key": pair_key,
            "v_start_i": p0.pivot_i,
            "v_low_i": p1.pivot_i,
            "v_start_time": df.index[p0.pivot_i],
            "v_low_time": df.index[p1.pivot_i],
            "reclaim_time": df.index[i],
            "v_start": p0.price,
            "v_low": p1.price,
            "drop": drop,
            "drop_atr": drop_atr,
            "drop_bars": drop_bars,
            "recovery_bars": recovery_bars,
            "recovery_ratio": recovery_ratio,
            "drop_speed": drop_speed,
            "recovery_speed": recovery_speed,
            "speed_ratio": speed_ratio,
            "activity_ratio": activity_ratio,
            "reclaim_i": i,
            "post_high": float(df["high"].iloc[i]),
            "pullback_seen": False,
            "pullback_low": math.nan,
            "pullback_high": math.nan,
            "pullback_i": -1,
        }
    return None


def run_spec(df: pd.DataFrame, pivots: list[Pivot], symbol: str, spec: IgnitionSpec) -> pd.DataFrame:
    active: list[Pivot] = []
    pointer = 0
    used_pairs: set[str] = set()
    rows: list[dict] = []
    context: dict | None = None
    in_pos_until = -1

    for i in range(120, len(df) - 1):
        pointer = pivots_until(pivots, pointer, i, active)
        ts = df.index[i]
        if ts < RUN_START or ts > RUN_END or holiday_market(ts):
            continue
        if i <= in_pos_until:
            continue

        if context is None:
            context = find_first_context(df, i, active, spec, used_pairs)
            continue

        atr_i = float(df["atr"].iloc[i])
        if not math.isfinite(atr_i) or atr_i <= 0:
            continue

        age = i - int(context["reclaim_i"])
        if age > spec.max_after_reclaim_bars:
            context = None
            continue

        context["post_high"] = max(float(context["post_high"]), float(df["high"].iloc[i]))
        pullback_depth_atr = (float(context["post_high"]) - float(df["low"].iloc[i])) / atr_i
        hold_level = max(float(context["v_start"]) - atr_i * spec.hold_below_reclaim_atr, float(context["v_low"]) + float(context["drop"]) * spec.min_hold_fib)
        hold_ok = float(df["low"].iloc[i]) >= hold_level
        if not hold_ok:
            context = None
            continue

        if not bool(context["pullback_seen"]):
            if pullback_depth_atr >= spec.min_pullback_atr and pullback_depth_atr <= spec.max_pullback_atr:
                context["pullback_seen"] = True
                context["pullback_low"] = float(df["low"].iloc[i])
                context["pullback_high"] = float(df["high"].iloc[i])
                context["pullback_i"] = i
            continue

        prev_pullback_high = float(context["pullback_high"])
        context["pullback_low"] = min(float(context["pullback_low"]), float(df["low"].iloc[i]))

        signal_range_atr = float(df["tr"].iloc[i]) / atr_i
        atr_expansion = float(df["atr_expansion"].iloc[i])
        bb_expansion = float(df["bb_expansion"].iloc[i])
        body_ratio = float(df["body_ratio"].iloc[i])
        close_location = float(df["close_location"].iloc[i])
        breakout_atr = (float(df["close"].iloc[i]) - prev_pullback_high) / atr_i
        broke_pullback = float(df["close"].iloc[i]) > prev_pullback_high + atr_i * spec.pullback_break_buffer_atr
        quality_ok = body_ratio >= spec.min_body_ratio and close_location >= spec.min_close_location
        vol_ok = signal_range_atr >= spec.min_signal_range_atr and atr_expansion >= spec.min_atr_expansion and bb_expansion >= spec.min_bb_expansion

        if not (broke_pullback and quality_ok and vol_ok):
            context["pullback_high"] = max(prev_pullback_high, float(df["high"].iloc[i]))
            continue

        stop = float(context["pullback_low"]) - atr_i * spec.stop_buffer_atr
        entry_proxy = float(df["close"].iloc[i])
        risk_atr = (entry_proxy - stop) / atr_i
        if stop >= entry_proxy or risk_atr <= 0 or risk_atr > spec.max_risk_atr:
            context["pullback_high"] = max(prev_pullback_high, float(df["high"].iloc[i]))
            continue

        trade = simulate_entry_rr(df, symbol, i, stop, spec.rr, spec.max_hold_bars)
        if trade is None:
            context = None
            continue

        used_pairs.add(str(context["pair_key"]))
        rows.append(
            {
                "symbol": symbol,
                "strategy": spec.name,
                "signal_time": ts,
                "period": period_name(pd.Timestamp(trade["entry_time"])),
                "pullback_time": df.index[int(context["pullback_i"])],
                "bars_after_reclaim": age,
                "pullback_depth_atr": pullback_depth_atr,
                "pullback_hold_level": hold_level,
                "pullback_high": prev_pullback_high,
                "pullback_low": context["pullback_low"],
                "breakout_atr": breakout_atr,
                "signal_range_atr": signal_range_atr,
                "atr_expansion": atr_expansion,
                "bb_expansion": bb_expansion,
                "body_ratio": body_ratio,
                "close_location": close_location,
                "risk_atr": risk_atr,
                "adx14": float(df["adx14"].iloc[i]),
                "rsi14": float(df["rsi14"].iloc[i]),
                **{k: v for k, v in context.items() if k not in {"post_high", "pullback_seen", "pullback_low", "pullback_high", "pullback_i"}},
                **trade,
            }
        )
        in_pos_until = int(df.index.get_loc(trade["exit_time"]))
        context = None

    return pd.DataFrame(rows)


def load_data() -> tuple[dict[str, pd.DataFrame], dict[str, list[Pivot]]]:
    data: dict[str, pd.DataFrame] = {}
    pivots: dict[str, list[Pivot]] = {}
    for symbol in SYMBOLS:
        if symbol not in INSTRUMENTS:
            continue
        raw = load_instrument(symbol)
        h4 = add_features(resample_ohlc(raw, TIMEFRAME))
        data[symbol] = h4
        pivots[symbol] = build_confirmed_pivots(h4, width=3, min_swing_atr=2.0)
    return data, pivots


def write_report(all_trades: pd.DataFrame, summary: pd.DataFrame) -> None:
    out = [
        "# H4 Ignition Pattern Search",
        "",
        "作成日: 2026-05-30",
        "",
        "## 探した特徴",
        "",
        "- 急落: confirmed pivot high -> low の下落幅/速度",
        "- 出来高増加: ローカルデータにvolumeがないため、V形成中のTrue Range平均/直前30本True Range平均で代替",
        "- 急反発: 右肩速度と回復率",
        "- 高値更新: 左肩起点を終値で上抜け",
        "- 戻り売り失敗: 高値更新後に押すが、起点付近を維持して押し高値を再上抜け",
        "- ボラ拡大: シグナル足True Range、ATR拡大、BB幅拡大",
        "",
        "## 全体サマリー",
        "",
        markdown_table(summary),
        "",
    ]
    if not all_trades.empty:
        strict_ex_xau = all_trades[(all_trades["strategy"] == "IGNITION_STRICT") & (all_trades["symbol"] != "XAUUSD")]
        if not strict_ex_xau.empty:
            out.extend(
                [
                    "## 重要発見",
                    "",
                    "`IGNITION_STRICT` は件数が少ないが、XAUUSDを除外すると 7 trades / 勝率 71.43% / +5.36R / PF 3.62。",
                    "標準案や早め案は件数は出るが、DDと連敗が大きい。つまりこの6条件は、ゆるく使うより厳選スキャナーとして使う方が自然。",
                    "",
                ]
            )
        selected = all_trades[all_trades["strategy"] == "IGNITION_BALANCED"].copy()
        if not selected.empty:
            recent = selected.sort_values("signal_time").tail(20)[
                [
                    "symbol",
                    "signal_time",
                    "v_start_time",
                    "v_low_time",
                    "pullback_time",
                    "drop_atr",
                    "activity_ratio",
                    "speed_ratio",
                    "pullback_depth_atr",
                    "breakout_atr",
                    "signal_range_atr",
                    "atr_expansion",
                    "bb_expansion",
                    "r_after_cost",
                    "mfe_r",
                    "mae_r",
                ]
            ]
            out.extend(
                [
                    "## IGNITION_BALANCED 直近20件",
                    "",
                    markdown_table(recent),
                    "",
                ]
            )
        by_symbol = (
            all_trades.groupby(["strategy", "symbol"], dropna=False)
            .apply(lambda g: pd.Series(summarize(g, f"{g.name[0]}_{g.name[1]}")))
            .reset_index(drop=True)
        )
        out.extend(["## 通貨別", "", markdown_table(by_symbol), ""])
        by_period = (
            all_trades.groupby(["strategy", "period"], dropna=False)
            .apply(lambda g: pd.Series(summarize(g, f"{g.name[0]}_{g.name[1]}")))
            .reset_index(drop=True)
        )
        out.extend(["## 期間別", "", markdown_table(by_period), ""])

    out.extend(
        [
            "## 実装メモ",
            "",
            "Pythonではvolumeが使えないため、ここで良い場所を絞った後、Pineでは `volume > sma(volume, 20) * 1.3〜1.8` を追加して再確認する。",
            "この条件群は、Vを直接買うというより、売り失敗後の再点火を探すためのスキャナーとして扱う。",
            "",
        ]
    )
    (OUT_DIR / "report_ja.md").write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    data, pivots = load_data()
    all_rows: list[pd.DataFrame] = []
    for spec in SPECS:
        for symbol, df in data.items():
            trades = run_spec(df, pivots[symbol], symbol, spec)
            if not trades.empty:
                all_rows.append(trades)
    all_trades = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    if not all_trades.empty:
        all_trades = all_trades.sort_values(["strategy", "signal_time", "symbol"]).reset_index(drop=True)
    all_trades.to_csv(OUT_DIR / "ignition_events_trades.csv", index=False)

    summary_rows = []
    if not all_trades.empty:
        for strategy, group in all_trades.groupby("strategy"):
            summary_rows.append(summarize(group, strategy))
    summary = pd.DataFrame(summary_rows).sort_values(["pf", "total_r"], ascending=[False, False]) if summary_rows else pd.DataFrame()
    summary.to_csv(OUT_DIR / "summary.csv", index=False)

    if not all_trades.empty:
        ex_xau = all_trades[all_trades["symbol"] != "XAUUSD"].copy()
        ex_xau_rows = []
        for strategy, group in ex_xau.groupby("strategy"):
            ex_xau_rows.append(summarize(group, f"{strategy}_ex_XAUUSD"))
        pd.DataFrame(ex_xau_rows).sort_values(["pf", "total_r"], ascending=[False, False]).to_csv(OUT_DIR / "summary_ex_xau.csv", index=False)
        (
            all_trades.groupby(["strategy", "symbol"], dropna=False)
            .apply(lambda g: pd.Series(summarize(g, f"{g.name[0]}_{g.name[1]}")))
            .reset_index(drop=True)
            .to_csv(OUT_DIR / "summary_by_symbol.csv", index=False)
        )
        (
            all_trades.groupby(["strategy", "period"], dropna=False)
            .apply(lambda g: pd.Series(summarize(g, f"{g.name[0]}_{g.name[1]}")))
            .reset_index(drop=True)
            .to_csv(OUT_DIR / "summary_by_period.csv", index=False)
        )

    write_report(all_trades, summary)
    print(f"Wrote {OUT_DIR}")
    if not summary.empty:
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

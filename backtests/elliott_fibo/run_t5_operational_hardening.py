#!/usr/bin/env python3
"""
Operational hardening study for H4 V-candidate T5 + MACD + BB.

This script treats the current idea as a promising signal and asks a more
practical question: how should it be operated so it is harder to break?

It studies:
- environment on/off and half-risk controls,
- exit variants,
- loss taxonomy,
- overlap/correlation with TrendBreakV1.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import (
    COST_TABLE,
    SYMBOLS,
    add_indicators,
    direction_cost_r,
    load_instrument,
    markdown_table,
    resample_ohlc,
)
from run_indicator_compatibility_search import add_extended_features
from run_t5_practical_robustness_audit import metrics, practical_mask


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
ROBUST_DIR = THIS_DIR / "results_2026_05_24" / "t5_practical_robustness_audit"
OUT_DIR = THIS_DIR / "results_2026_05_24" / "t5_operational_hardening"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "H4"
MAX_HOLD_BARS = 180


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def max_drawdown(r: pd.Series) -> float:
    if r.empty:
        return 0.0
    curve = r.astype(float).cumsum()
    return float((curve.cummax() - curve).max())


def max_losing_streak(r: pd.Series) -> int:
    cur = 0
    best = 0
    for value in r.astype(float):
        if value <= 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def metric_from_r(values: pd.Series) -> dict:
    r = values.dropna().astype(float)
    return {
        "trades": int(len(r)),
        "win_rate": float((r > 0).mean() * 100) if len(r) else 0.0,
        "total_r": float(r.sum()) if len(r) else 0.0,
        "avg_r": float(r.mean()) if len(r) else 0.0,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": max_drawdown(r),
        "max_losing_streak": max_losing_streak(r),
    }


def period_of(ts: pd.Timestamp) -> str:
    return "OOS_2025_2026" if ts.year >= 2025 else "Research_2015_2024"


def add_period(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    if "period" not in out.columns:
        out["period"] = out["entry_time"].map(period_of)
    return out


def summary_row(name: str, df: pd.DataFrame, r_col: str = "r_after_cost", notes: str = "") -> dict:
    out = {"case": name, "notes": notes}
    out.update({f"all_{k}": v for k, v in metric_from_r(df[r_col] if r_col in df.columns else pd.Series(dtype=float)).items()})
    for period in ["Research_2015_2024", "OOS_2025_2026"]:
        sub = df[df["period"].eq(period)] if not df.empty and "period" in df.columns else df.iloc[0:0]
        prefix = "oos" if period.startswith("OOS") else "research"
        out.update({f"{prefix}_{k}": v for k, v in metric_from_r(sub[r_col] if r_col in sub.columns else pd.Series(dtype=float)).items()})
    return out


def load_t5_trades() -> pd.DataFrame:
    path = ROBUST_DIR / "t5_broad_trades_2015_2026.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run robustness audit first: {path}")
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    return add_period(df)


def t5_operational_sets(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = trades[
        practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=None, use_rebreak_guard=True)
    ].copy()
    strict = trades[
        practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=4.0, use_rebreak_guard=True)
    ].copy()
    quality_5atr = trades[
        practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.0, bb_width_max=5.0, use_rebreak_guard=True)
    ].copy()
    macd_002 = trades[
        practical_mask(trades, bb_upper=0.95, recovery_max=16, macd_min=0.02, bb_width_max=4.0, use_rebreak_guard=True)
    ].copy()
    return {
        "BASE operational no BB width cap": base,
        "STRICT BB width<=4ATR": strict,
        "RELAX BB width<=5ATR": quality_5atr,
        "STRICT + MACD slope3>0.02": macd_002,
    }


def environment_controls(sample: pd.DataFrame) -> pd.DataFrame:
    rows = [summary_row("Baseline", sample, notes="BB<=0.95, recovery<=16, MACD>0")]

    controls: list[tuple[str, pd.Series, str]] = [
        ("Stop ATR pctile>=80", sample["atr_pctile_252"] < 80, "ATR上位20%は停止"),
        ("Half ATR pctile>=80", pd.Series(True, index=sample.index), "ATR上位20%はロット半減"),
        ("Stop BB width>4ATR", sample["bb_width_atr"] <= 4.0, "BB幅過大は停止"),
        ("Half BB width>4ATR", pd.Series(True, index=sample.index), "BB幅過大はロット半減"),
        ("Stop EMA flat/against", sample["ema20_slope_10_atr"] > 0.0, "H4 EMA20傾きが上向きのみ"),
        ("Stop ADX<15", sample["adx14"] >= 15, "弱すぎるトレンドを停止"),
        ("Stop chop>=55", sample["chop14"] < 55, "レンジ・乱高下寄りを停止"),
        ("Stop MACD<=0.02", sample["macd_hist_slope3"] > 0.02, "MACD上昇を強める"),
        ("Stop single rebreak weak", ~((sample["trigger_type"].eq("rebreak")) & (sample["macd_hist_slope3"] <= 0.03)), "単独rebreakでMACD弱い時だけ停止"),
    ]

    for name, mask, notes in controls:
        frame = sample.copy()
        if name.startswith("Half ATR"):
            frame["controlled_r"] = np.where(frame["atr_pctile_252"] >= 80, frame["r_after_cost"] * 0.5, frame["r_after_cost"])
            rows.append(summary_row(name, frame, "controlled_r", notes))
        elif name.startswith("Half BB"):
            frame["controlled_r"] = np.where(frame["bb_width_atr"] > 4.0, frame["r_after_cost"] * 0.5, frame["r_after_cost"])
            rows.append(summary_row(name, frame, "controlled_r", notes))
        else:
            rows.append(summary_row(name, frame[mask.fillna(False)].copy(), notes=notes))
    return pd.DataFrame(rows)


def build_feature_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for symbol in SYMBOLS:
        frames[symbol] = add_extended_features(add_indicators(resample_ohlc(load_instrument(symbol), TIMEFRAME)))
    return frames


def exit_variant_r(
    df: pd.DataFrame,
    trade: pd.Series,
    variant: str,
    rr: float = 2.0,
    trail_atr: float = 3.0,
    swing_len: int = 5,
    time_bars: int = 40,
) -> tuple[float | None, str, pd.Timestamp | None]:
    entry_time = pd.Timestamp(trade["entry_time"])
    if entry_time not in df.index:
        return None, "missing_entry", None
    entry_i = int(df.index.get_loc(entry_time))
    entry = float(trade["entry"])
    stop0 = float(trade["stop"])
    direction = str(trade["direction"])
    risk = abs(entry - stop0)
    if risk <= 0:
        return None, "bad_risk", None

    stop = stop0
    target = None
    partial_done = False
    partial_r = 0.0

    if variant.startswith("fixed"):
        target = entry + risk * rr if direction == "long" else entry - risk * rr
    elif variant == "be_after_2r_target_3r":
        target = entry + risk * 3.0 if direction == "long" else entry - risk * 3.0
    elif variant == "partial_1r_half_rest_3r":
        target = entry + risk * 3.0 if direction == "long" else entry - risk * 3.0

    end_i = min(len(df) - 1, entry_i + MAX_HOLD_BARS)
    for j in range(entry_i, end_i + 1):
        row = df.iloc[j]
        hi = float(row["high"])
        lo = float(row["low"])
        close = float(row["close"])
        atr = float(row["atr"]) if math.isfinite(float(row["atr"])) else risk

        # Update trailing stop from information available before the current
        # bar close. This is intentionally conservative.
        if j > entry_i:
            prev = df.iloc[j - 1]
            if variant == "atr_trail_3atr":
                stop = max(stop, float(prev["close"]) - atr * trail_atr) if direction == "long" else min(stop, float(prev["close"]) + atr * trail_atr)
            elif variant == "swing_trail_5":
                start = max(entry_i, j - swing_len)
                if direction == "long":
                    swing_stop = float(df["low"].iloc[start:j].min()) - atr * 0.10
                    stop = max(stop, swing_stop)
                else:
                    swing_stop = float(df["high"].iloc[start:j].max()) + atr * 0.10
                    stop = min(stop, swing_stop)

        if variant == "be_after_2r_target_3r":
            if direction == "long" and hi >= entry + risk * 2.0:
                stop = max(stop, entry)
            if direction == "short" and lo <= entry - risk * 2.0:
                stop = min(stop, entry)

        if variant == "partial_1r_half_rest_3r" and not partial_done:
            if direction == "long" and hi >= entry + risk:
                partial_done = True
                partial_r = 0.5 * 1.0
                stop = max(stop, entry)
            elif direction == "short" and lo <= entry - risk:
                partial_done = True
                partial_r = 0.5 * 1.0
                stop = min(stop, entry)

        if direction == "long":
            hit_sl = lo <= stop
            hit_tp = target is not None and hi >= target
            if hit_sl or hit_tp:
                exit_px = stop if hit_sl else float(target)
                r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, exit_px, risk)
                if variant == "partial_1r_half_rest_3r" and partial_done:
                    r_after = partial_r + 0.5 * r_after
                return r_after, "SL" if hit_sl else "TP", df.index[j]
            if variant == "bb_mid_reversal" and j > entry_i and close < float(row["kc_mid"]):
                r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, close, risk)
                return r_after, "bb_mid_reversal", df.index[j]
            if variant == "h4_low_break_5" and j - entry_i >= 5:
                prev_low = float(df["low"].iloc[j - 5 : j].min())
                if close < prev_low:
                    r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, close, risk)
                    return r_after, "h4_low_break", df.index[j]
        else:
            hit_sl = hi >= stop
            hit_tp = target is not None and lo <= target
            if hit_sl or hit_tp:
                exit_px = stop if hit_sl else float(target)
                r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, exit_px, risk)
                if variant == "partial_1r_half_rest_3r" and partial_done:
                    r_after = partial_r + 0.5 * r_after
                return r_after, "SL" if hit_sl else "TP", df.index[j]
            if variant == "bb_mid_reversal" and j > entry_i and close > float(row["kc_mid"]):
                r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, close, risk)
                return r_after, "bb_mid_reversal", df.index[j]
            if variant == "h4_low_break_5" and j - entry_i >= 5:
                prev_high = float(df["high"].iloc[j - 5 : j].max())
                if close > prev_high:
                    r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, close, risk)
                    return r_after, "h4_high_break", df.index[j]

        if variant == "time_exit_40" and j - entry_i >= time_bars:
            r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, close, risk)
            return r_after, "time_exit", df.index[j]

    exit_px = float(df["close"].iloc[end_i])
    r_clean, r_after = direction_cost_r(str(trade["symbol"]), direction, entry, exit_px, risk)
    if variant == "partial_1r_half_rest_3r" and partial_done:
        r_after = partial_r + 0.5 * r_after
    return r_after, "max_hold", df.index[end_i]


def exit_research(sample: pd.DataFrame, feature_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    variants = [
        ("fixed_1_5r", dict(variant="fixed", rr=1.5), "固定TP 1.5R"),
        ("fixed_2r_current", dict(variant="fixed", rr=2.0), "現行に近い固定TP 2R"),
        ("fixed_3r", dict(variant="fixed", rr=3.0), "固定TP 3R"),
        ("be_after_2r_target_3r", dict(variant="be_after_2r_target_3r"), "2R到達後建値、3R目標"),
        ("partial_1r_half_rest_3r", dict(variant="partial_1r_half_rest_3r"), "1Rで半分利確、残り3R"),
        ("atr_trail_3atr", dict(variant="atr_trail_3atr"), "ATR 3本分トレール"),
        ("swing_trail_5", dict(variant="swing_trail_5"), "直近5本安値トレール"),
        ("bb_mid_reversal", dict(variant="bb_mid_reversal"), "ミドル割れ撤退"),
        ("h4_low_break_5", dict(variant="h4_low_break_5"), "直近5本安値割れ撤退"),
        ("time_exit_40", dict(variant="time_exit_40"), "40本時間切れ"),
    ]
    rows = []
    detail_rows = []
    for name, kwargs, notes in variants:
        values = []
        for _, trade in sample.iterrows():
            r, reason, exit_time = exit_variant_r(feature_frames[str(trade["symbol"])], trade, **kwargs)
            values.append(r if r is not None else np.nan)
            detail_rows.append(
                {
                    "variant": name,
                    "symbol": trade["symbol"],
                    "entry_time": trade["entry_time"],
                    "r": r,
                    "reason": reason,
                    "exit_time": exit_time,
                    "period": trade["period"],
                }
            )
        frame = sample.copy()
        frame["exit_variant_r"] = values
        rows.append(summary_row(name, frame.dropna(subset=["exit_variant_r"]), "exit_variant_r", notes))
    pd.DataFrame(detail_rows).to_csv(OUT_DIR / "exit_variant_trades.csv", index=False)
    return pd.DataFrame(rows)


def loss_taxonomy(sample: pd.DataFrame) -> pd.DataFrame:
    losses = sample[sample["r_after_cost"] <= 0].copy()
    checks: list[tuple[str, pd.Series, str]] = [
        ("BB位置が高すぎる", sample["bb_pos"] > 0.95, "過熱域での買い"),
        ("BB幅が4ATR超", sample["bb_width_atr"] > 4.0, "ボラ拡大後"),
        ("BB幅が5ATR超", sample["bb_width_atr"] > 5.0, "かなり過熱"),
        ("MACD slope3<=0.03", sample["macd_hist_slope3"] <= 0.03, "再加速が弱い"),
        ("ATR percentile>=80", sample["atr_pctile_252"] >= 80, "高ボラ環境"),
        ("EMA20傾き<=0", sample["ema20_slope_10_atr"] <= 0, "H4方向が逆/停滞"),
        ("ADX<15", sample["adx14"] < 15, "トレンド弱い"),
        ("Chop>=55", sample["chop14"] >= 55, "レンジ・乱高下"),
        ("単独rebreak", sample["trigger_type"].eq("rebreak"), "停滞なし再ブレイク"),
        ("stagnation+rebreak", sample["trigger_type"].eq("stagnation+rebreak"), "両方成立"),
    ]
    rows = []
    for name, mask, note in checks:
        all_count = int(mask.fillna(False).sum())
        loss_count = int((losses.index.to_series().isin(sample[mask.fillna(False)].index)).sum())
        subset = sample[mask.fillna(False)]
        rows.append(
            {
                "pattern": name,
                "note": note,
                "all_count": all_count,
                "loss_count": loss_count,
                "loss_share_pct": loss_count / len(losses) * 100 if len(losses) else 0,
                "pattern_win_rate": float((subset["r_after_cost"] > 0).mean() * 100) if len(subset) else 0,
                "pattern_avg_r": float(subset["r_after_cost"].mean()) if len(subset) else 0,
                "pattern_total_r": float(subset["r_after_cost"].sum()) if len(subset) else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["loss_count", "pattern_avg_r"], ascending=[False, True])


def load_combo_trades() -> pd.DataFrame:
    combo_dir = REPO_ROOT / "backtests" / "ensemble" / "trendbreak_t5_practical_combo_2015_2024"
    frames = []
    for path in [combo_dir / "trendbreak_only_trades.csv", combo_dir / "t5_practical_only_trades.csv"]:
        if path.exists():
            frame = pd.read_csv(path, parse_dates=["entry_time", "exit_time"])
            if "r_after_cost" not in frame.columns and "r" in frame.columns:
                frame["r_after_cost"] = frame["r"]
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).sort_values(["entry_time", "strategy", "symbol"]).reset_index(drop=True)
    return add_period(df)


def risk_group(symbol: str) -> str:
    if symbol in {"XAUUSD", "SILVER"}:
        return "METAL"
    if symbol.endswith("JPY"):
        return "JPY"
    return symbol


def correlation_controls(combo: pd.DataFrame) -> pd.DataFrame:
    if combo.empty:
        return pd.DataFrame()
    rows = [summary_row("No correlation control", combo, notes="TrendBreak + T5単純合算")]

    detail = combo.copy()
    scaled_same_group = []
    scaled_skip_same_symbol = []
    scaled_group_cap = []
    for _, trade in detail.iterrows():
        active = detail[
            (detail["entry_time"] < trade["entry_time"])
            & (detail["exit_time"] > trade["entry_time"])
        ]
        same_symbol_active = active["symbol"].eq(trade["symbol"]).any()
        same_group_active = active["symbol"].map(risk_group).eq(risk_group(str(trade["symbol"]))).any()
        scaled_same_group.append(float(trade["r_after_cost"]) * (0.5 if same_group_active else 1.0))
        scaled_skip_same_symbol.append(0.0 if same_symbol_active and trade["strategy"] != "trendbreak_only" else float(trade["r_after_cost"]))
        scaled_group_cap.append(0.0 if same_group_active and trade["strategy"] != "trendbreak_only" else float(trade["r_after_cost"]))

    for name, values, notes in [
        ("Half risk when same group active", scaled_same_group, "JPY/METALの同時リスクは後続を半分"),
        ("Skip T5 when same symbol active", scaled_skip_same_symbol, "同一通貨でTrendBreak等が保有中ならT5を見送り"),
        ("Group cap priority TrendBreak", scaled_group_cap, "JPY/METALのグループ内でTrendBreak優先"),
    ]:
        frame = detail.copy()
        frame["controlled_r"] = values
        rows.append(summary_row(name, frame, "controlled_r", notes))
    return pd.DataFrame(rows)


def write_report(
    set_table: pd.DataFrame,
    env_table: pd.DataFrame,
    exit_table: pd.DataFrame,
    loss_table: pd.DataFrame,
    corr_table: pd.DataFrame,
) -> None:
    compact = [
        "case",
        "all_trades",
        "all_win_rate",
        "all_total_r",
        "all_avg_r",
        "all_pf",
        "all_max_dd_r",
        "oos_trades",
        "oos_win_rate",
        "oos_total_r",
        "oos_avg_r",
        "oos_pf",
        "notes",
    ]
    lines = [
        "# H4 V候補 T5 + MACD + BB 本番運用監査",
        "",
        "## 目的",
        "",
        "PFをさらに上げるのではなく、壊れにくい運用ルールを作るための監査。",
        "シグナル研究ではなく、見送り・停止・ロット調整・出口・相関を確認する。",
        "",
        "## 1. 運用候補セット",
        "",
        markdown_table(set_table[compact], 40),
        "",
        "## 2. 市場環境フィルタ / ロット調整",
        "",
        markdown_table(env_table[compact], 80),
        "",
        "## 3. EXIT研究",
        "",
        markdown_table(exit_table[compact], 80),
        "",
        "## 4. 負け方の分類",
        "",
        markdown_table(loss_table, 80),
        "",
        "## 5. TrendBreakV1との相関制御",
        "",
        markdown_table(corr_table[compact], 40) if not corr_table.empty else "_TrendBreak/T5 combo trades not found._",
        "",
        "## 暫定結論",
        "",
        "- 今の手法は、エントリー条件よりもBB幅・MACD・同時保有制御で壊れにくさが大きく変わる。",
        "- `BB幅<=4ATR` は利益最大化ではなくDD抑制装置。5ATR緩和は候補だが、4ATRを標準にする方が本番向き。",
        "- `MACD slope3>0.02` は取引数を減らすが、DDをかなり抑える候補。",
        "- EXITは固定TPだけでなく、2R到達後建値/3R目標、分割利確、トレールを比較対象にする価値がある。",
        "- TrendBreakと同時に出る時は分散ではなく同じ相場を取りにいく可能性が高い。グループ単位の上限が必要。",
        "",
        "## 本番前チェックリスト",
        "",
        "1. フォワードで最低30 trades、理想50〜100 tradesを記録。",
        "2. シグナル、見送り、感情、ニュース有無、スクショを全部残す。",
        "3. JPYグループとMETALグループの同時リスク上限を決める。",
        "4. ATR上位20%、BB幅>4ATR、EMA逆向きの時の停止/半減ルールを固定する。",
        "5. EXITは固定2Rだけでなく、2R後建値・分割利確・スイングトレールをフォワードで比較する。",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    trades = load_t5_trades()
    sets = t5_operational_sets(trades)
    set_rows = [summary_row(name, frame, notes="T5 operational candidate") for name, frame in sets.items()]
    set_table = pd.DataFrame(set_rows)

    base_sample = sets["BASE operational no BB width cap"]
    strict_sample = sets["STRICT BB width<=4ATR"]

    env_table = environment_controls(base_sample)
    feature_frames = build_feature_frames()
    exit_table = exit_research(strict_sample, feature_frames)
    loss_table = loss_taxonomy(base_sample)
    combo = load_combo_trades()
    corr_table = correlation_controls(combo)

    set_table.to_csv(OUT_DIR / "operational_sets.csv", index=False)
    env_table.to_csv(OUT_DIR / "environment_controls.csv", index=False)
    exit_table.to_csv(OUT_DIR / "exit_research.csv", index=False)
    loss_table.to_csv(OUT_DIR / "loss_taxonomy.csv", index=False)
    corr_table.to_csv(OUT_DIR / "correlation_controls.csv", index=False)
    write_report(set_table, env_table, exit_table, loss_table, corr_table)

    print(f"Report: {OUT_DIR / 'report_ja.md'}")
    print(set_table[["case", "all_trades", "all_total_r", "all_avg_r", "all_pf", "all_max_dd_r", "oos_trades", "oos_total_r"]].to_string(index=False))
    print(env_table[["case", "all_trades", "all_total_r", "all_avg_r", "all_pf", "all_max_dd_r"]].to_string(index=False))


if __name__ == "__main__":
    main()

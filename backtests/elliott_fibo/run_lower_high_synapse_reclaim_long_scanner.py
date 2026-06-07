#!/usr/bin/env python3
"""
Lower High 3 Touch line reclaim long event scanner.

No entries, no parameter optimization. Detects a three-lower-high structure,
then treats the first confirmed close above the descending LH3 line as a
long-direction observation event. Measures long-direction MFE/MAE over
24/48/120 bars. This is a hypothesis test, not a trading strategy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from run_elliott_fibo_study import SYMBOLS, add_indicators, load_instrument, resample_ohlc


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
OUT_DIR = REPO_ROOT / "docs" / "research" / "lower_high_synapse_reclaim_long_2026-06-08"
OUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2015-01-01")
RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")
END = pd.Timestamp("2026-12-31 23:59:59")
HORIZONS = (24, 48, 120)


@dataclass(frozen=True)
class ScanSpec:
    timeframe: str
    pivot_left: int
    pivot_right: int
    min_lower_atr: float
    line_touch_atr: float
    max_bars_12: int
    max_bars_23: int
    reclaim_buffer_atr: float
    max_reclaim_bars: int
    cooldown_bars: int

    @property
    def name(self) -> str:
        return (
            f"{self.timeframe}_P{self.pivot_left}R{self.pivot_right}"
            f"_LOW{self.min_lower_atr:g}_TOUCH{self.line_touch_atr:g}"
            f"_RECLAIMBUF{self.reclaim_buffer_atr:g}"
        )


SPECS = [
    ScanSpec("H1", 5, 5, 0.20, 0.55, 160, 160, 0.05, 240, 48),
    ScanSpec("H4", 3, 3, 0.20, 0.55, 80, 80, 0.05, 120, 24),
]


def period_name(ts: pd.Timestamp) -> str:
    return "Research_2015_2024" if ts <= RESEARCH_END else "OOS_2025_2026"


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append("" if math.isnan(v) else f"{v:.2f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def is_pivot_high(high: np.ndarray, i: int, left: int, right: int) -> bool:
    if i < left or i + right >= len(high):
        return False
    value = high[i]
    if not math.isfinite(value):
        return False
    window = high[i - left : i + right + 1]
    return bool(value >= np.nanmax(window))


def forward_path_long(df: pd.DataFrame, signal_i: int, atr_i: float) -> dict:
    entry = float(df["close"].iloc[signal_i])
    out: dict[str, float | bool] = {}
    for h in HORIZONS:
        end = min(len(df) - 1, signal_i + h)
        if end <= signal_i or not math.isfinite(atr_i) or atr_i <= 0:
            out[f"mfe_{h}_atr"] = math.nan
            out[f"mae_{h}_atr"] = math.nan
            out[f"fwd_{h}_atr"] = math.nan
            out[f"hit_1atr_first_{h}"] = False
            out[f"hit_3atr_{h}"] = False
            continue

        window = df.iloc[signal_i + 1 : end + 1]
        mfe = (float(window["high"].max()) - entry) / atr_i
        mae = (entry - float(window["low"].min())) / atr_i
        fwd = (float(df["close"].iloc[end]) - entry) / atr_i
        out[f"mfe_{h}_atr"] = mfe
        out[f"mae_{h}_atr"] = mae
        out[f"fwd_{h}_atr"] = fwd
        out[f"hit_3atr_{h}"] = bool(mfe >= 3.0)

        hit_first = False
        decided = False
        for _, r in window.iterrows():
            hit_fav = float(r["high"]) >= entry + atr_i
            hit_bad = float(r["low"]) <= entry - atr_i
            if hit_fav or hit_bad:
                hit_first = hit_fav and not hit_bad
                decided = True
                break
        out[f"hit_1atr_first_{h}"] = bool(hit_first and decided)
    return out


def detect_events(df: pd.DataFrame, symbol: str, spec: ScanSpec) -> list[dict]:
    df = df[(df.index >= START) & (df.index <= END)].copy()
    if df.empty:
        return []

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = df["atr"].to_numpy(dtype=float)
    idx = list(df.index)

    pivot_highs: list[dict] = []
    events: list[dict] = []
    last_event_i = -10_000

    for current_i in range(spec.pivot_left + spec.pivot_right, len(df) - max(HORIZONS) - 1):
        pivot_i = current_i - spec.pivot_right
        if not is_pivot_high(high, pivot_i, spec.pivot_left, spec.pivot_right):
            continue

        pivot_highs.append(
            {
                "i": pivot_i,
                "confirm_i": current_i,
                "price": float(high[pivot_i]),
                "atr": float(atr[pivot_i]),
            }
        )
        while len(pivot_highs) > 200:
            pivot_highs.pop(0)

        if len(pivot_highs) < 3:
            continue

        h1, h2, h3 = pivot_highs[-3:]
        atr_ref = h3["atr"]
        if not math.isfinite(atr_ref) or atr_ref <= 0:
            continue

        h1_i, h2_i, h3_i = int(h1["i"]), int(h2["i"]), int(h3["i"])
        h1_p, h2_p, h3_p = float(h1["price"]), float(h2["price"]), float(h3["price"])
        lower_ok = h1_p > h2_p + atr_ref * spec.min_lower_atr and h2_p > h3_p + atr_ref * spec.min_lower_atr
        spacing_ok = (
            h1_i < h2_i < h3_i
            and h2_i - h1_i <= spec.max_bars_12
            and h3_i - h2_i <= spec.max_bars_23
        )
        touch_slope = (h2_p - h1_p) / (h2_i - h1_i) if h2_i != h1_i else math.nan
        expected_h3 = h1_p + touch_slope * (h3_i - h1_i) if math.isfinite(touch_slope) else math.nan
        touch_ok = math.isfinite(expected_h3) and abs(h3_p - expected_h3) <= atr_ref * spec.line_touch_atr
        if not (lower_ok and spacing_ok and touch_ok):
            continue

        # Match the visible red line in the Pine scanner:
        # line.new(h1Bar, h1, h3Bar, h3, extend=extend.right)
        visible_slope = (h3_p - h1_p) / (h3_i - h1_i) if h3_i != h1_i else math.nan
        if not math.isfinite(visible_slope):
            continue

        search_start = int(h3["confirm_i"]) + 1
        search_end = min(len(df) - max(HORIZONS) - 1, search_start + spec.max_reclaim_bars)
        if search_end <= search_start:
            continue

        leg1_low = float(np.nanmin(low[h1_i : h2_i + 1]))
        leg2_low = float(np.nanmin(low[h2_i : h3_i + 1]))
        leg1_atr = (h1_p - leg1_low) / atr_ref
        leg2_atr = (h2_p - leg2_low) / atr_ref
        prev_leg_avg_atr = float(np.nanmean([leg1_atr, leg2_atr]))

        for j in range(search_start, search_end + 1):
            atr_j = float(atr[j])
            if not math.isfinite(atr_j) or atr_j <= 0:
                continue
            line_price = h1_p + visible_slope * (j - h1_i)
            if not math.isfinite(line_price):
                continue
            reclaim_level = line_price + atr_j * spec.reclaim_buffer_atr
            if close[j] > reclaim_level and j - last_event_i >= spec.cooldown_bars:
                last_event_i = j
                path = forward_path_long(df, j, atr_j)
                row = {
                    "symbol": symbol,
                    "timeframe": spec.timeframe,
                    "spec": spec.name,
                    "period": period_name(idx[j]),
                    "event_time": idx[j],
                    "h1_time": idx[h1_i],
                    "h2_time": idx[h2_i],
                    "h3_time": idx[h3_i],
                    "entry_close": float(close[j]),
                    "line_reclaim_level": reclaim_level,
                    "line_price": line_price,
                    "h1_price": h1_p,
                    "h2_price": h2_p,
                    "h3_price": h3_p,
                    "bars_after_h3": j - h3_i,
                    "h12_drop_atr": (h1_p - h2_p) / atr_ref,
                    "h23_drop_atr": (h2_p - h3_p) / atr_ref,
                    "line_touch_error_atr": abs(h3_p - expected_h3) / atr_ref,
                    "leg1_drop_atr": leg1_atr,
                    "leg2_drop_atr": leg2_atr,
                    "prev_leg_avg_atr": prev_leg_avg_atr,
                    **path,
                }
                for h in HORIZONS:
                    row[f"mfe{h}_vs_prev_leg_avg"] = (
                        row[f"mfe_{h}_atr"] / prev_leg_avg_atr if prev_leg_avg_atr and prev_leg_avg_atr > 0 else math.nan
                    )
                events.append(row)
                break
    return events


def summarize(events: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()

    rows = []
    for keys, g in events.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["events"] = len(g)
        row["median_bars_after_h3"] = g["bars_after_h3"].median()
        for h in HORIZONS:
            row[f"median_mfe_{h}"] = g[f"mfe_{h}_atr"].median()
            row[f"median_mae_{h}"] = g[f"mae_{h}_atr"].median()
            row[f"median_fwd_{h}"] = g[f"fwd_{h}_atr"].median()
            row[f"pct_mfe{h}_ge_3"] = g[f"hit_3atr_{h}"].mean() * 100.0
            row[f"pct_hit1_first_{h}"] = g[f"hit_1atr_first_{h}"].mean() * 100.0
            row[f"median_mfe{h}_vs_prev_leg"] = g[f"mfe{h}_vs_prev_leg_avg"].median()
        row["median_prev_leg_avg_atr"] = g["prev_leg_avg_atr"].median()
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["timeframe", "events"], ascending=[True, False])


def build_report(events: pd.DataFrame, summary_tf: pd.DataFrame, summary_sym_tf: pd.DataFrame) -> str:
    lines = [
        "# Lower High 3 Touch 上抜けロング実測 v0.1",
        "",
        "作成日: 2026-06-08",
        "",
        "TP/SLを置いた売買バックテストではない。3回の戻り高値切り下げ後、赤いLH3下降LINEを終値で上抜けた最初の足をロング仮エントリーとして抽出し、その後の MFE/MAE を測定。",
        "",
        "## データ",
        "",
        f"- 期間: 2015-01-01 〜 {events['event_time'].max() if not events.empty else 'N/A'}",
        "- 通貨: XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, AUDJPY, SILVER",
        "- 時間足: H1 / H4",
        "- Pivot: confirmed pivot high のみ",
        "- 仮エントリー: 赤いLH3下降LINE上抜け足の終値。",
        "",
        "## 全体サマリー",
        "",
        markdown_table(summary_tf.round(2)),
        "",
        "## 通貨別サマリー",
        "",
        markdown_table(summary_sym_tf.round(2)),
        "",
        "## 読み方",
        "",
        "- `median_mfe_*`: 上方向へどれだけ伸びたか。ATR単位。",
        "- `median_mae_*`: 逆行幅。ATR単位。",
        "- `median_fwd_*`: 指定本数後の終値ベース上昇幅。プラスなら上方向に進んだ。",
        "- `median_mfe*_vs_prev_leg`: 上抜け後のMFEが、直前1〜2段目の平均下落legの何倍か。",
        "- `pct_mfe*_ge_3`: 指定本数内に3ATR以上の上昇余地が出た割合。",
        "- `median_bars_after_h3`: 3つ目のlower highから上抜けまでの中央値。",
        "",
        "## 暫定判断",
        "",
    ]

    if events.empty:
        lines.append("イベントが検出されなかったため、条件を緩める必要がある。")
    else:
        for label in ("H1", "H4"):
            frame = summary_tf[summary_tf["timeframe"].eq(label)]
            if frame.empty:
                continue
            r = frame.iloc[0]
            lines.append(
                f"- {label}: {int(r['events'])}件。MFE48中央値 {r['median_mfe_48']:.2f}ATR、"
                f"MAE48中央値 {r['median_mae_48']:.2f}ATR、fwd48中央値 {r['median_fwd_48']:.2f}ATR。"
            )
        lines.extend(
            [
                "",
                "この検証は「LH3ライン上抜けだけ」で測っている。",
                "H1はMFEとMAEがほぼ同じで、上抜け直後に振らされやすい。",
                "H4はMFE48がMAE48を上回り、fwd48/fwd120もプラス。LH3上抜けロングはH4のほうが研究価値が高い。",
                "ただし、1ATR順行が先に来る割合はH4でも50%前後なので、赤LINE上抜けだけで即エントリーするにはまだ弱い。",
                "Synapseとして使う場合は、次に B水平線上抜け、A水平線上抜け、Bから離れすぎない条件で分ける。",
            ]
        )

        xau_h4 = summary_sym_tf[
            summary_sym_tf["symbol"].eq("XAUUSD") & summary_sym_tf["timeframe"].eq("H4")
        ]
        silver_h4 = summary_sym_tf[
            summary_sym_tf["symbol"].eq("SILVER") & summary_sym_tf["timeframe"].eq("H4")
        ]
        if not xau_h4.empty or not silver_h4.empty:
            lines.extend(["", "## 通貨別の気づき", ""])
            if not xau_h4.empty:
                r = xau_h4.iloc[0]
                lines.append(
                    f"- XAUUSD H4: MFE48中央値 {r['median_mfe_48']:.2f}ATR、"
                    f"MAE48中央値 {r['median_mae_48']:.2f}ATR、fwd48中央値 {r['median_fwd_48']:.2f}ATR。"
                    "今回の定義では最も見たい候補。"
                )
            if not silver_h4.empty:
                r = silver_h4.iloc[0]
                lines.append(
                    f"- SILVER H4: MFE48中央値 {r['median_mfe_48']:.2f}ATR、"
                    f"MAE48中央値 {r['median_mae_48']:.2f}ATR、fwd48中央値 {r['median_fwd_48']:.2f}ATR。"
                    "XAUUSDに次いで転換側の観察価値が高い。"
                )

    lines.extend(
        [
            "",
            "## 出力ファイル",
            "",
            "- [events_all.csv](events_all.csv)",
            "- [summary_by_timeframe.csv](summary_by_timeframe.csv)",
            "- [summary_by_symbol_timeframe.csv](summary_by_symbol_timeframe.csv)",
            "",
            "## 再現",
            "",
            "```bash",
            "python3 backtests/elliott_fibo/run_lower_high_synapse_reclaim_long_scanner.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    all_events: list[dict] = []
    for symbol in SYMBOLS:
        raw = load_instrument(symbol)
        for spec in SPECS:
            frame = add_indicators(resample_ohlc(raw, spec.timeframe))
            all_events.extend(detect_events(frame, symbol, spec))

    events = pd.DataFrame(all_events)
    if not events.empty:
        events = events.sort_values(["timeframe", "symbol", "event_time"]).reset_index(drop=True)
    summary_tf = summarize(events, ["timeframe"]) if not events.empty else pd.DataFrame()
    summary_sym_tf = summarize(events, ["symbol", "timeframe"]) if not events.empty else pd.DataFrame()

    events.to_csv(OUT_DIR / "events_all.csv", index=False)
    summary_tf.to_csv(OUT_DIR / "summary_by_timeframe.csv", index=False)
    summary_sym_tf.to_csv(OUT_DIR / "summary_by_symbol_timeframe.csv", index=False)
    (OUT_DIR / "REPORT_ja.md").write_text(build_report(events, summary_tf, summary_sym_tf), encoding="utf-8")

    print(f"events: {len(events)}")
    print(f"wrote: {OUT_DIR}")
    if not summary_tf.empty:
        print(summary_tf.to_string(index=False))


if __name__ == "__main__":
    main()

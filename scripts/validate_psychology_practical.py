#!/usr/bin/env python3
"""
Practical psychology-map validation for live trading.

1) TrendBreak / T5 trades × H1 STOP / stagnation (CHECK) gates
2) STOP component breakdown (F1 / F2 / break)
3) Student wait-zone hit rates
4) Per-symbol Pine preset recommendations

Outputs:
  docs/research/psychology_practical_gate_results_2026-06-01.csv
  docs/research/psychology_practical_presets_2026-06-01.json
  docs/research/psychology_practical_validation_2026-06-01.md
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO / "F87104_test"
TB_TRADES = REPO / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
T5_TRADES = (
    REPO / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"
)
WAIT_ZONES = REPO / "docs/research/student_stumble_wait_zones_v0_2.csv"
OUT_CSV = REPO / "docs/research/psychology_practical_gate_results_2026-06-01.csv"
OUT_JSON = REPO / "docs/research/psychology_practical_presets_2026-06-01.json"
OUT_MD = REPO / "docs/research/psychology_practical_validation_2026-06-01.md"

# Import shared OHLC / signal helpers
import sys

sys.path.insert(0, str(REPO / "scripts"))
from sweep_psychology_liquidity_params import (  # noqa: E402
    base_frame,
    build_sweep_cache,
    load_ohlc,
    pip_size,
)

REC_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]
YEARS = list(range(2015, 2025))
LOOKBACK_BARS = 24
LOOKBACK_SHORT = 6
STAG_ATR_MAX = 2.5

# Practical defaults (from sweep + prior analysis)
PRESETS = {
    "GBPJPY": dict(prox_yen=0.25, prox_half=0.15, ext_atr=0.60, swing_len=48, big_mult=1.05, strict_f1=True, wick_atr=0.40, sweep_lb=20, fwd_bars=72),
    "XAUUSD": dict(prox_yen=0.25, prox_half=0.15, ext_atr=0.85, swing_len=48, big_mult=1.05, strict_f1=False, wick_atr=0.40, sweep_lb=20, fwd_bars=48),
    "USDJPY": dict(prox_yen=0.25, prox_half=0.15, ext_atr=0.60, swing_len=48, big_mult=1.05, strict_f1=True, wick_atr=0.40, sweep_lb=20, fwd_bars=12),
    "DEFAULT": dict(prox_yen=0.25, prox_half=0.15, ext_atr=0.85, swing_len=48, big_mult=1.05, strict_f1=True, wick_atr=0.40, sweep_lb=20, fwd_bars=24),
}


def preset_for(symbol: str) -> dict:
    return PRESETS.get(symbol, PRESETS["DEFAULT"]).copy()


def build_signal_frame(d: pd.DataFrame, symbol: str, p: dict) -> pd.DataFrame:
    cache = build_sweep_cache(d, symbol)
    cu, cd, nr = cache["round"][(p["prox_yen"], p["prox_half"])]
    nh, nl = cache["ext"][p["ext_atr"]]
    bull = cache["bull"]
    bear = cache["bear"]
    f2l, f2s = cache["f2"][p["big_mult"]]
    brkl, brks = cache["brk"][p["swing_len"]]
    su = cache["strong_up"]
    sd = cache["strong_dn"]
    if p["strict_f1"]:
        f1l = nh & bull & cu
        f1s = nl & bear & cd
    else:
        f1l = nh & bull & nr
        f1s = nl & bear & nr
    stop_long = f1l | f2l | (brkl & su)
    stop_short = f1s | f2s | (brks & sd)
    wkey = (p["wick_atr"], p["sweep_lb"])
    sweep_dn = cache["sweep_dn"][wkey]
    sweep_up = cache["sweep_up"][wkey]

    high = d["high"].to_numpy()
    low = d["low"].to_numpy()
    atr = d["atr"].to_numpy()
    n = len(d)
    stag = np.zeros(n, dtype=bool)
    for i in range(6, n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        rng = high[i - 6 : i].max() - low[i - 6 : i].min()
        stag[i] = rng / atr[i] <= STAG_ATR_MAX

    out = d[["time"]].copy()
    out["f1_long"] = f1l
    out["f2_long"] = f2l
    out["brk_long"] = brkl & su
    out["f1_short"] = f1s
    out["f2_short"] = f2s
    out["brk_short"] = brks & sd
    out["stop_long"] = stop_long
    out["stop_short"] = stop_short
    out["stop_any"] = stop_long | stop_short
    out["sweep_down"] = sweep_dn
    out["sweep_up"] = sweep_up
    out["stagnation_h1"] = stag
    return out


def load_h1_signals(symbol: str) -> pd.DataFrame | None:
    raw = load_ohlc(symbol, YEARS)
    if raw.empty:
        return None
    d = base_frame(raw)
    return build_signal_frame(d, symbol, preset_for(symbol))


def window_flag(sig: pd.DataFrame, entry_time: pd.Timestamp, col: str, lookback: int = LOOKBACK_BARS) -> bool:
    t0 = entry_time - pd.Timedelta(hours=lookback)
    sub = sig[(sig["time"] > t0) & (sig["time"] <= entry_time)]
    if sub.empty:
        return False
    return bool(sub[col].any())


def window_flag_at_entry(sig: pd.DataFrame, entry_time: pd.Timestamp, col: str) -> bool:
    row = sig[sig["time"] == entry_time]
    if row.empty:
        idx = sig["time"].searchsorted(entry_time, side="right") - 1
        if idx < 0:
            return False
        row = sig.iloc[[idx]]
    return bool(row[col].iloc[0])


def summarize_trades(df: pd.DataFrame, label: str, strategy: str) -> dict:
    if df.empty:
        return dict(gate=label, strategy=strategy, trades=0, total_r=0.0, pf=np.nan, win_rate=np.nan, avg_r=np.nan)
    wins = df[df["r"] > 0]["r"].sum()
    losses = -df[df["r"] <= 0]["r"].sum()
    pf = wins / losses if losses > 0 else np.inf
    return dict(
        gate=label,
        strategy=strategy,
        trades=len(df),
        total_r=float(df["r"].sum()),
        pf=float(pf),
        win_rate=float((df["r"] > 0).mean()),
        avg_r=float(df["r"].mean()),
    )


def read_tb() -> pd.DataFrame:
    df = pd.read_csv(TB_TRADES)
    df = df[df["rule_name"].eq("baseline")].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["signal_time"] = pd.to_datetime(df["signal_time"])
    return df[
        [
            "symbol",
            "direction",
            "entry_time",
            "signal_time",
            "pnl_r_after_cost",
            "pre_range_6_atr",
            "exit_reason",
        ]
    ].rename(columns={"pnl_r_after_cost": "r"})


def read_t5() -> pd.DataFrame:
    df = pd.read_csv(T5_TRADES)
    df = df[df["period"].eq("Research_2015_2024")].copy()
    df = df[
        (df["bb_pos"] <= 0.95)
        & (df["signal_recovery_bars"] <= 16)
        & ~(
            (df["trigger_type"] == "rebreak")
            & ((df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03))
        )
    ]
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    return df[["symbol", "direction", "entry_time", "r_after_cost", "trigger_type"]].rename(
        columns={"r_after_cost": "r"}
    )


def attach_psychology(trades: pd.DataFrame, signals: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for _, t in trades.iterrows():
        sym = t["symbol"]
        sig = signals.get(sym)
        if sig is None:
            continue
        et = t["entry_time"]
        d = t["direction"]
        sl = window_flag(sig, et, "stop_long")
        ss = window_flag(sig, et, "stop_short")
        sany = window_flag(sig, et, "stop_any")
        sd = window_flag(sig, et, "sweep_down")
        su = window_flag(sig, et, "sweep_up")
        if "pre_range_6_atr" in t and pd.notna(t["pre_range_6_atr"]):
            stag_tb = float(t["pre_range_6_atr"]) <= STAG_ATR_MAX
        else:
            stag_tb = window_flag_at_entry(sig, et, "stagnation_h1")
        stag_h1 = window_flag_at_entry(sig, et, "stagnation_h1")
        f1 = window_flag(sig, et, "f1_long" if d == "long" else "f1_short")
        f2 = window_flag(sig, et, "f2_long" if d == "long" else "f2_short")
        brk = window_flag(sig, et, "brk_long" if d == "long" else "brk_short")
        same_dir_stop = sl if d == "long" else ss
        sl6 = window_flag(sig, et, "stop_long", LOOKBACK_SHORT)
        ss6 = window_flag(sig, et, "stop_short", LOOKBACK_SHORT)
        same_dir_stop_6 = sl6 if d == "long" else ss6
        stop_entry = window_flag_at_entry(sig, et, "stop_long" if d == "long" else "stop_short")
        f1_6 = window_flag(sig, et, "f1_long" if d == "long" else "f1_short", LOOKBACK_SHORT)
        f1_entry = window_flag_at_entry(sig, et, "f1_long" if d == "long" else "f1_short")
        rows.append(
            {
                **t.to_dict(),
                "stop_long_win": sl,
                "stop_short_win": ss,
                "stop_any_win": sany,
                "same_dir_stop": same_dir_stop,
                "same_dir_stop_6": same_dir_stop_6,
                "stop_on_entry": stop_entry,
                "f1_6h": f1_6,
                "f1_on_entry": f1_entry,
                "sweep_down_win": sd,
                "sweep_up_win": su,
                "stagnation_tb": stag_tb,
                "stagnation_h1": stag_h1,
                "f1_win": f1,
                "f2_win": f2,
                "brk_win": brk,
                "check_ok": same_dir_stop and (stag_tb or stag_h1),
            }
        )
    return pd.DataFrame(rows)


def apply_gates(tb: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    g = []
    g.append(("baseline_all", pd.Series(True, index=tb.index)))
    g.append(("block_stop_on_entry_bar", ~tb["stop_on_entry"]))
    g.append(("block_f1_on_entry_bar", ~tb["f1_on_entry"]))
    g.append(("block_same_dir_stop_6h", ~tb["same_dir_stop_6"]))
    g.append(("block_f1_6h", ~tb["f1_6h"]))
    g.append(("block_same_dir_stop_24h", ~tb["same_dir_stop"]))
    g.append(("block_stop_any_24h", ~tb["stop_any_win"]))
    g.append(("block_f1_only_24h", ~tb["f1_win"]))
    g.append(
        (
            "block_same_dir_unless_check",
            ~tb["same_dir_stop"] | tb["stagnation_tb"] | tb["stagnation_h1"],
        )
    )
    g.append(
        (
            "block_same_dir_unless_check_h1only",
            ~tb["same_dir_stop"] | tb["stagnation_h1"],
        )
    )
    # Per-symbol asymmetric (data-driven)
    asym = []
    for i, row in tb.iterrows():
        sym = row["symbol"]
        if sym == "XAUUSD" and row["direction"] == "short":
            asym.append(not row["stop_short_win"])
        elif sym == "GBPJPY" and row["direction"] == "long":
            asym.append(not row["stop_long_win"])
        else:
            asym.append(True)
    g.append(("asym_xau_sell_gbp_buy_stop", pd.Series(asym, index=tb.index)))
    asym_s = pd.Series(asym, index=tb.index)
    g.append(
        (
            "asym_plus_check",
            asym_s & (~tb["same_dir_stop"] | tb["stagnation_tb"] | tb["stagnation_h1"]),
        )
    )
    g.append(("favor_sweep_down_long_only", ~(tb["direction"].eq("long") & tb["sweep_down_win"])))
    return g


def eval_wait_zones() -> pd.DataFrame:
    if not WAIT_ZONES.exists():
        return pd.DataFrame()
    wz = pd.read_csv(WAIT_ZONES)
    rows = []
    for _, z in wz.iterrows():
        sym = z["currency"]
        raw = load_ohlc(sym, [2024, 2025, 2026])
        if raw.empty:
            continue
        d = raw.copy()
        t0 = pd.to_datetime(z["wait_start"])
        t1 = pd.to_datetime(z["wait_end"])
        win = d[(d["time"] >= t0) & (d["time"] <= t1)]
        if win.empty:
            continue
        lo, hi = float(z["wait_lo"]), float(z["wait_hi"])
        touch = ((win["low"] <= hi) & (win["high"] >= lo)).any()
        rows.append(
            dict(
                currency=sym,
                rank=int(z["rank"]),
                rule=z["rule"],
                students=int(z["students"]),
                wait_lo=lo,
                wait_hi=hi,
                touched=bool(touch),
                note=z.get("note", ""),
            )
        )
    return pd.DataFrame(rows)


def component_report(signals: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sym, sig in signals.items():
        n = len(sig)
        for col, label in [
            ("f1_long", "f1_long"),
            ("f2_long", "f2_long"),
            ("brk_long", "brk_long"),
            ("f1_short", "f1_short"),
            ("f2_short", "f2_short"),
            ("brk_short", "brk_short"),
            ("stop_long", "stop_long"),
            ("stop_short", "stop_short"),
            ("sweep_down", "sweep_down"),
        ]:
            rows.append(dict(symbol=sym, component=label, count=int(sig[col].sum()), rate=float(sig[col].mean())))
    return pd.DataFrame(rows)


def blocked_trade_quality(tb: pd.DataFrame, mask: pd.Series) -> dict:
    blocked = tb[~mask]
    kept = tb[mask]
    if blocked.empty or kept.empty:
        return {}
    return dict(
        blocked_n=len(blocked),
        blocked_avg_r=float(blocked["r"].mean()),
        blocked_wr=float((blocked["r"] > 0).mean()),
        kept_avg_r=float(kept["r"].mean()),
        kept_wr=float((kept["r"] > 0).mean()),
    )


def write_md(
    gate_df: pd.DataFrame,
    best_gate: str,
    tb_enriched: pd.DataFrame,
    wait_df: pd.DataFrame,
    comp_df: pd.DataFrame,
    coverage: dict,
) -> None:
    lines = [
        "# 心理マップ — 実践検証（2026-06-01）",
        "",
        "目的: **TrendBreak / T5 の実トレード**に H1 STOP・停滞(CHECK) を重ね、採用できるゲートだけ残す。",
        "",
        "## 運用ルール（採用案）",
        "",
        "| 優先 | ルール | 内容 |",
        "|---:|---|---|",
        "| 1 | **エントリー足の S** | 24h ではなく **その足に S** が付いた TB だけ見送り（過剰ブロックを避ける） |",
        "| 2 | **CHECK** | 同方向 STOP でも `pre_range_6 ≤ 2.5 ATR` なら TB 可（停滞→再ブレイク） |",
        "| 3 | **方向別（任意）** | XAU 売り / GBP 買いで 6h 内 STOP → 慎重（PF↑・件数↓） |",
        "| 4 | **T5は止めない** | H4 T5 は心理ゲート非適用 |",
        "| 5 | **マップ** | 赤＝追い確認。全面禁止にしない |",
        "",
        "## TB と心理フラグの重なり",
        "",
        f"- エントリー足に同方向 STOP: **{coverage.get('stop_entry_pct', 0):.1%}**",
        f"- 6本以内に同方向 STOP: **{coverage.get('stop_6_pct', 0):.1%}**",
        f"- 24本以内に同方向 STOP: **{coverage.get('stop_24_pct', 0):.1%}**（広すぎ・自動ブロック非推奨）",
        "",
        "## TrendBreak ゲート比較（2015–2024 baseline）",
        "",
        "| gate | trades | total_r | PF | win_rate | avg_r |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    sub = gate_df[gate_df["strategy"] == "TrendBreakV1"].sort_values("total_r", ascending=False)
    for _, r in sub.iterrows():
        pf = f"{r['pf']:.2f}" if np.isfinite(r["pf"]) else "inf"
        lines.append(
            f"| {r['gate']} | {int(r['trades'])} | {r['total_r']:+.1f} | {pf} | {r['win_rate']:.1%} | {r['avg_r']:+.3f} |"
        )
    lines += ["", f"**推奨ゲート:** `{best_gate}`（total_r 最大・件数過少なし）", ""]

    q = blocked_trade_quality(
        tb_enriched,
        tb_enriched["_best_mask"] if "_best_mask" in tb_enriched.columns else pd.Series(True, index=tb_enriched.index),
    )
    if q:
        lines += [
            "### ブロックされた TB の質",
            "",
            f"- ブロック件数: {q['blocked_n']} / 平均R {q['blocked_avg_r']:+.3f} / 勝率 {q['blocked_wr']:.1%}",
            f"- 残した件数の質: 平均R {q['kept_avg_r']:+.3f} / 勝率 {q['kept_wr']:.1%}",
            "",
        ]

    lines += ["## 通貨別 Pine プリセット", "", "```json", json.dumps(PRESETS, indent=2, ensure_ascii=False), "```", ""]

    if not comp_df.empty:
        lines += ["## STOP 成分（H1本数ベース）", ""]
        for sym in comp_df["symbol"].unique():
            c = comp_df[comp_df["symbol"] == sym]
            lines.append(f"### {sym}")
            for _, r in c.iterrows():
                lines.append(f"- {r['component']}: {int(r['count'])}本 ({r['rate']:.2%})")
            lines.append("")

    if not wait_df.empty:
        hit = wait_df["touched"].mean()
        lines += [
            "## 青帯（待つ場所）到達率",
            "",
            f"- ゾーン数 {len(wait_df)} / 期間内に帯タッチ **{hit:.1%}**",
            "",
            "| rank | currency | rule | touched |",
            "|---:|---|---|---|",
        ]
        for _, r in wait_df.iterrows():
            lines.append(f"| {int(r['rank'])} | {r['currency']} | {r['rule']} | {'✓' if r['touched'] else '—'} |")
        lines.append("")

    lines += [
        "## 結論（実践）",
        "",
        "1. **TBを心理マップで自動全停止しない** — 6h/24h 内 STOP は TB の ~99% と重なるため。",
        "2. **手動の見送りは「エントリー足に S」**（約13%）— `block_stop_on_entry_bar` でも総Rは +194→+151 と減るため、",
        "   エンジン組み込みより **最終チェック** 向き。",
        "3. **CHECK** — 同方向 STOP でも TB の `pre_range_6_atr ≤ 2.5` なら見送り不要（PF 2.08・件数半減のトレードオフ）。",
        "4. **狩り後ロング** — `favor_sweep_down_long_only` は総Rほぼ維持（+184.5）→ 下狩り直後の追い買いだけ注意。",
        "5. **T5** — 心理ゲート不要（30件・PF3.4）。",
        "6. **青帯** — 待ちゾーンは期間内タッチ率高い → 飛び乗り禁止・押し/戻り待ちの教材と一致。",
        "",
        "### エントリー前チェックリスト（TB）",
        "",
        "- [ ] エントリー足に **S** が無い（あれば見送り or ロット半減）",
        "- [ ] S が出ていても **直前6本が停滞**（レンジ/ATR≤2.5）なら CHECK → TB可",
        "- [ ] XAU 売り / GBP 買いで節目追いなら **赤帯・整数** を確認",
        "- [ ] 直近に **安値狩り＋陽線** なら追い買い慎重",
        "- [ ] T5 シグナルは心理マップと独立に優先",
        "",
        "## ファイル",
        "",
        f"- `{OUT_CSV.name}` — ゲート一覧",
        f"- `{OUT_JSON.name}` — Pine 入力用プリセット",
        f"- `psychology_liquidity_param_sweep_2026-06-01.md` — パラメータスイープ",
        "",
        "## TradingView",
        "",
        "- 目視: `pine/visual/psychology_map_live.pine`（プリセットを通貨で切替）",
        "- TB 試験: エントリー前24本に S が出たら手動見送り（CHECK は停滞足ありなら可）",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("Loading H1 signals...")
    signals: dict[str, pd.DataFrame] = {}
    for sym in REC_SYMBOLS:
        sf = load_h1_signals(sym)
        if sf is not None:
            signals[sym] = sf
            print(f"  {sym}: {len(sf)} bars")

    comp_df = component_report(signals)
    wait_df = eval_wait_zones()

    tb_raw = read_tb()
    tb = attach_psychology(tb_raw, signals)
    t5_raw = read_t5()
    t5 = attach_psychology(t5_raw, signals)

    gate_rows = []
    gates = apply_gates(tb)
    best_name = "baseline_all"
    best_r = -1e9
    best_mask = pd.Series(True, index=tb.index)

    for name, mask in gates:
        filt = tb[mask]
        gate_rows.append(summarize_trades(filt, name, "TrendBreakV1"))
        if name != "baseline_all":
            tr = float(filt["r"].sum())
            if tr > best_r and len(filt) >= len(tb) * 0.70:
                best_r = tr
                best_name = name
                best_mask = mask

    # Also evaluate: if best is worse than baseline, keep baseline
    base_r = float(tb["r"].sum())
    if best_r < base_r:
        best_name = "baseline_all (no gate beat baseline)"
        best_mask = pd.Series(True, index=tb.index)

    tb["_best_mask"] = best_mask
    gate_rows.append(summarize_trades(t5, "t5_no_gate", "H4_T5_practical"))
    gate_rows.append(summarize_trades(t5[~t5["same_dir_stop"]], "t5_block_same_dir_stop", "H4_T5_practical"))

    gate_df = pd.DataFrame(gate_rows)
    gate_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(PRESETS, indent=2, ensure_ascii=False), encoding="utf-8")
    coverage = dict(
        stop_entry_pct=float(tb["stop_on_entry"].mean()),
        stop_6_pct=float(tb["same_dir_stop_6"].mean()),
        stop_24_pct=float(tb["same_dir_stop"].mean()),
    )
    write_md(gate_df, best_name, tb, wait_df, comp_df, coverage)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"Best TB gate: {best_name} total_r={best_r:.1f} (baseline {base_r:.1f})")


if __name__ == "__main__":
    main()

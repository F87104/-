#!/usr/bin/env python3
"""Market Psychology V2 Deep Research.

Post-hoc analysis on the existing market_psychology_strategy_tv_check trades.csv
(1238 trades across SQZ/CAP variants and 7 symbols).

Covers the 10 research questions:
    #2  Early exit rule (approximate, using mfe_r + mae_r + bars_held)
    #3  Shelf parameter sensitivity heat-map
    #4  Shelf quality (body_ratio, close_location, lower_wick_ratio)
    #5  Long Liquidation (documented; OHLC scan deferred)
    #6  Dormant Breakout (documented; OHLC scan deferred)
    #7  Duplicate signal overlap with other strategies
    #8  Session / day-of-week bias
    #9  Currency microstructure (shelf width vs drop magnitude correlation)
    #10 Capitulation context filters

Outputs everything under
    backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research/
as CSVs that can be inspected directly, plus a console summary.

This script needs only pandas and the existing trades.csv. No raw OHLC required.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1].parents[0]
SRC = ROOT / "backtests/elliott_fibo/results_2026_05_30/market_psychology_strategy_tv_check/trades.csv"
OUT = ROOT / "backtests/elliott_fibo/results_2026_05_30/market_psychology_v2_deep_research"
OUT.mkdir(parents=True, exist_ok=True)

trades = pd.read_csv(SRC, parse_dates=["signal_time", "entry_time", "exit_time"])
trades["hour"] = trades["entry_time"].dt.hour
trades["dow"] = trades["entry_time"].dt.dayofweek
trades["year"] = trades["entry_time"].dt.year
trades["is_win"] = trades["r_after_cost"] > 0
trades["is_loss"] = trades["r_after_cost"] <= 0

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def summarize(df: pd.DataFrame, label: str = "") -> dict:
    if len(df) == 0:
        return dict(label=label, trades=0, wr=np.nan, total_r=0.0, avg_r=np.nan,
                    pf=np.nan, dd=0.0, max_streak=0)
    wins = df[df["r_after_cost"] > 0]["r_after_cost"].sum()
    losses = -df[df["r_after_cost"] <= 0]["r_after_cost"].sum()
    pf = wins / losses if losses > 0 else np.inf
    cumr = df["r_after_cost"].cumsum().values
    peak = np.maximum.accumulate(cumr)
    dd = float(np.max(peak - cumr)) if len(cumr) else 0.0
    streak = 0
    max_streak = 0
    for r in df["r_after_cost"]:
        if r <= 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return dict(
        label=label,
        trades=len(df),
        wr=float((df["r_after_cost"] > 0).mean() * 100.0),
        total_r=float(df["r_after_cost"].sum()),
        avg_r=float(df["r_after_cost"].mean()),
        pf=float(pf),
        dd=dd,
        max_streak=int(max_streak),
    )


BASE_STRAT = "SQZ_STRICT_RR2"
base = trades[trades["strategy"] == BASE_STRAT].copy()
base_ex_gbp = base[base["symbol"] != "GBPJPY"].copy()


def write(df: pd.DataFrame, name: str) -> None:
    path = OUT / name
    df.to_csv(path, index=False)


print(f"Trades total: {len(trades)} / SQZ_STRICT_RR2: {len(base)} / ex GBPJPY: {len(base_ex_gbp)}")

# ===========================================================================
# #2  Early-exit rule simulation
# ===========================================================================
# Approximate model:
#   If a trade ultimately lost (r_after_cost <= 0) AND its mfe_r < THR_MFE
#   within first BARS bars (bars_held >= BARS), assume an early-exit rule
#   would have closed it at -EARLY_LOSS (instead of -1R).
#
# We sweep THR_MFE x BARS, applying the substitution to ex-GBPJPY SQZ_STRICT_RR2.
# This gives an *upper bound* on benefit since we cannot replay the path bar by
# bar from this CSV.  We also model a more conservative version where any saved
# loser also implies some wins that would have been clipped (false positives).
# ===========================================================================
print("\n[#2] Early-exit rule sweep...")

def apply_early_exit(df: pd.DataFrame, thr_mfe: float, bars_min: int,
                     early_loss: float = -0.35, win_clip_rate: float = 0.0,
                     win_clip_r: float = 0.5) -> pd.DataFrame:
    out = df.copy()
    # candidates for early exit: lost AND low mfe_r AND held long enough
    cond_loss = (out["r_after_cost"] <= 0) & (out["mfe_r"] < thr_mfe) & (out["bars_held"] >= bars_min)
    out.loc[cond_loss, "r_after_cost"] = early_loss
    # false positives: a fraction of wins that *might* have triggered the same
    # early-exit (low mfe in the first BARS but recovered).  We do not have
    # bar-by-bar so we model by clipping `win_clip_rate` of small wins to
    # win_clip_r.  By default 0.0 = ignore false positives.
    if win_clip_rate > 0:
        wins = out[(out["r_after_cost"] > 0) & (out["mfe_r"] < thr_mfe + 0.2)]
        clip_n = int(len(wins) * win_clip_rate)
        if clip_n > 0:
            clip_idx = wins.sample(n=clip_n, random_state=42).index
            out.loc[clip_idx, "r_after_cost"] = win_clip_r
    return out


rows = []
for thr in [0.3, 0.4, 0.5, 0.6, 0.7]:
    for bars in [4, 8, 12, 16, 24]:
        for early in [-0.25, -0.35, -0.5]:
            mod = apply_early_exit(base_ex_gbp, thr, bars, early_loss=early)
            s = summarize(mod, f"thr{thr}_bars{bars}_loss{early}")
            s.update(dict(thr_mfe=thr, bars_min=bars, early_loss=early))
            rows.append(s)

baseline_s = summarize(base_ex_gbp, "baseline SQZ_STRICT_RR2 ex GBPJPY")
print(f"  baseline: {baseline_s}")
df_r2 = pd.DataFrame(rows).sort_values("total_r", ascending=False)
write(df_r2, "r2_early_exit_sweep.csv")
print(df_r2.head(5).to_string(index=False))

# also compute candidates / sensitivity at chosen point
chosen = apply_early_exit(base_ex_gbp, 0.5, 12, early_loss=-0.35)
chosen_s = summarize(chosen, "EARLY_EXIT thr0.5 bars12 loss-0.35")
print(f"  chosen point: {chosen_s}")
write(pd.DataFrame([baseline_s, chosen_s]), "r2_baseline_vs_chosen.csv")

# ===========================================================================
# #3  Shelf parameter sensitivity (post-hoc)
# ===========================================================================
# Each SQZ trade already has shelf_range_atr and sharp_drop_atr.  We filter
# the SQZ_DEFAULT_RR2 super-set (135 trades) by a 6x6 grid of (shelf_atr,
# drop_atr) thresholds and report the aggregate stats per cell.
# ===========================================================================
print("\n[#3] Shelf x drop heat-map...")
src = trades[trades["strategy"] == "SQZ_DEFAULT_RR2"].copy()
src_ex_gbp = src[src["symbol"] != "GBPJPY"].copy()

shelf_grid = [1.5, 1.8, 2.0, 2.2, 2.5, 3.0]
drop_grid = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
rows = []
for s in shelf_grid:
    for d in drop_grid:
        sub = src_ex_gbp[(src_ex_gbp["shelf_range_atr"] <= s) & (src_ex_gbp["sharp_drop_atr"] >= d)]
        stat = summarize(sub, f"shelf<={s} drop>={d}")
        stat.update(dict(shelf_atr_max=s, drop_atr_min=d))
        rows.append(stat)
df_r3 = pd.DataFrame(rows)
write(df_r3, "r3_shelf_drop_heatmap.csv")

# pivot for PF / total R views
piv_pf = df_r3.pivot(index="shelf_atr_max", columns="drop_atr_min", values="pf")
piv_r = df_r3.pivot(index="shelf_atr_max", columns="drop_atr_min", values="total_r")
piv_t = df_r3.pivot(index="shelf_atr_max", columns="drop_atr_min", values="trades")
write(piv_pf.reset_index(), "r3_heatmap_pf.csv")
write(piv_r.reset_index(), "r3_heatmap_total_r.csv")
write(piv_t.reset_index(), "r3_heatmap_trades.csv")
print("  PF heatmap:\n", piv_pf.round(2).to_string())
print("  Total R heatmap:\n", piv_r.round(2).to_string())

best_cell = df_r3[df_r3["trades"] >= 20].sort_values("pf", ascending=False).head(5)
print("  Top cells (trades>=20):")
print(best_cell[["shelf_atr_max", "drop_atr_min", "trades", "total_r", "pf", "dd"]].to_string(index=False))

# ===========================================================================
# #4  Shelf candle quality (body / close_loc / wick)
# ===========================================================================
print("\n[#4] Shelf candle quality...")
df = src_ex_gbp.copy()
rows = []
for thr_body in [0.0, 0.3, 0.5, 0.7]:
    for thr_close in [0.0, 0.5, 0.7]:
        sub = df[(df["body_ratio"] >= thr_body) & (df["close_location"] >= thr_close)]
        s = summarize(sub, f"body>={thr_body} close_loc>={thr_close}")
        s.update(dict(body_min=thr_body, close_loc_min=thr_close))
        rows.append(s)
df_r4 = pd.DataFrame(rows)
write(df_r4, "r4_candle_quality.csv")
print(df_r4.to_string(index=False))

# ===========================================================================
# #5  Long Liquidation (planning + light analysis)
# ===========================================================================
# Without bar-by-bar OHLC we cannot scan for the short-direction mirror.
# But we can document the design and produce a checklist for a follow-up scan.
# ===========================================================================
plan_r5 = """\
Long Liquidation (short side, mirror of Short Squeeze)

Goal: detect 'buyers giving up' after a rally.
Signal definition (proposed):
  1. Sharp rally:    last 6 bars high - last 12 bars low >= 3 * ATR
  2. Failure to make new high after the rally (within 6 bars)
  3. Upper shelf:   6-bar range <= 2.0 * ATR formed at the rally top
  4. Break:         close < shelfLow

Entry: next bar open, short
SL: shelfHigh + 0.25 * ATR
TP: 2R
Max hold: 120 bars
Currency filter:  exclude GBPJPY (likely mirror imbalance)

Why mirror of SHORT_SQUEEZE failed in earlier studies:
  - In long-direction crashes the new short positions trapped at the bottom
    are forced to cover.  At the top the new long positions trapped at the top
    are NOT forced (they can hold, set wider stops, etc.).
  - That is why we need 'failure to make new high' + 'volume divergence'
    (TV-only) as additional rigor on the short side.

Requires OHLC scan; not feasible in this post-hoc analysis.  See Pine sketch
in pine/research/market_psychology_long_liquidation_strategy.pine (future).
"""
(OUT / "r5_long_liquidation_plan.md").write_text(plan_r5)

# ===========================================================================
# #6  Dormant Breakout (planning)
# ===========================================================================
plan_r6 = """\
Dormant Breakout (Pattern 10)

Goal: catch breakouts of long-untouched levels.

Signal definition (proposed):
  1. Donchian-N high or low untouched for N bars (N in [120, 360, 1250])
  2. Close breaks the level (no wick-only)
  3. After break, 5-bar pullback that holds above the level (long) / below (short)
  4. Re-break of the prior 5-bar high / low

Entry: next bar open after re-break
SL: opposite side of the 5-bar pullback - 0.25 * ATR
TP: 2R
Max hold: 240 bars

Why dormant?  Long-untouched levels accumulate stop orders (sell stops below
multi-year low, buy stops above multi-year high).  Breaking them releases
liquidity and accelerates the move.

Requires OHLC scan and Donchian computation; not feasible here.  Sketch a
Pine implementation in pine/research/market_psychology_dormant_breakout_strategy.pine
(future).
"""
(OUT / "r6_dormant_breakout_plan.md").write_text(plan_r6)

# ===========================================================================
# #7  Duplicate signal overlap with other strategies
# ===========================================================================
# Cross-check signal_time of our SQZ_STRICT_RR2 ex GBPJPY against trade
# entry_times of other strategies' CSVs.  If on the same bar/symbol there is
# another strategy's entry, mark it.  Then summarize how often duplicates win.
# ===========================================================================
print("\n[#7] Duplicate signal overlap...")
others = {
    "TrendBreakV1": "backtests/trendbreak_v1/results_2015_2024/trades.csv",
    "H4VKickoff":   "backtests/elliott_fibo/results_2026_05_30/h4_v_kickoff_catalyst/trades.csv",
    "D1BearTrap":   "backtests/elliott_fibo/results_2026_05_29/d1_bear_trap_h4_v_reclaim/trades.csv",
}

base_keys = base_ex_gbp.copy()
base_keys["key_day"] = base_keys["entry_time"].dt.normalize()  # group by day
overlap_rows = []
for name, rel in others.items():
    p = ROOT / rel
    if not p.exists():
        continue
    other = pd.read_csv(p, parse_dates=["entry_time"], dayfirst=False, low_memory=False, on_bad_lines="skip")
    if "entry_time" not in other.columns or "symbol" not in other.columns:
        continue
    other["key_day"] = other["entry_time"].dt.normalize()
    merged = base_keys.merge(other[["symbol", "key_day"]].drop_duplicates(),
                             on=["symbol", "key_day"], how="left", indicator=True)
    n_dup = (merged["_merge"] == "both").sum()
    overlap_rows.append(dict(other_strategy=name, sqz_trades=len(base_keys), overlap=int(n_dup),
                             overlap_pct=round(100 * n_dup / max(1, len(base_keys)), 1)))
    base_keys[f"dup_{name}"] = (merged["_merge"] == "both").values

df_r7 = pd.DataFrame(overlap_rows)
write(df_r7, "r7_duplicate_overlap_summary.csv")
print(df_r7.to_string(index=False))

# per-trade impact: are duplicates more/less profitable?
dup_cols = [c for c in base_keys.columns if c.startswith("dup_")]
if dup_cols:
    rows = []
    for c in dup_cols:
        dup_pos = base_keys[base_keys[c]]
        dup_neg = base_keys[~base_keys[c]]
        rows.append({"flag": c, "n_dup": len(dup_pos), "n_not": len(dup_neg),
                     "r_dup": dup_pos["r_after_cost"].mean() if len(dup_pos) else np.nan,
                     "r_not": dup_neg["r_after_cost"].mean() if len(dup_neg) else np.nan,
                     "pf_dup": (dup_pos["r_after_cost"].clip(lower=0).sum() /
                                max(1e-9, -dup_pos["r_after_cost"].clip(upper=0).sum())) if len(dup_pos) else np.nan,
                     "pf_not": (dup_neg["r_after_cost"].clip(lower=0).sum() /
                                max(1e-9, -dup_neg["r_after_cost"].clip(upper=0).sum())) if len(dup_neg) else np.nan})
    df_r7_dup = pd.DataFrame(rows)
    write(df_r7_dup, "r7_duplicate_impact.csv")
    print(df_r7_dup.to_string(index=False))

# ===========================================================================
# #8  Session / day-of-week bias
# ===========================================================================
print("\n[#8] Session / DOW bias...")
df = base_ex_gbp.copy()
by_hour = df.groupby("hour").apply(lambda d: pd.Series(summarize(d))).reset_index()
by_dow = df.groupby("dow").apply(lambda d: pd.Series(summarize(d))).reset_index()
write(by_hour, "r8_by_hour.csv")
write(by_dow, "r8_by_dow.csv")
print("  By hour (UTC):")
print(by_hour[["hour", "trades", "wr", "total_r", "pf", "dd"]].to_string(index=False))
print("  By DOW (Mon=0):")
print(by_dow[["dow", "trades", "wr", "total_r", "pf", "dd"]].to_string(index=False))

# ===========================================================================
# #9  Currency microstructure
# ===========================================================================
print("\n[#9] Currency microstructure...")
sqz_all = trades[trades["family"] == "short_squeeze"].copy()
cap_all = trades[trades["family"] == "capitulation"].copy()

def microsig(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sym, sub in df.groupby("symbol"):
        rows.append(dict(
            symbol=sym, trades=len(sub),
            mean_shelf_atr=sub["shelf_range_atr"].mean() if "shelf_range_atr" in sub else np.nan,
            mean_drop_atr=sub["sharp_drop_atr"].mean() if "sharp_drop_atr" in sub else np.nan,
            mean_signal_range=sub["signal_range_atr"].mean(),
            mean_close_loc=sub["close_location"].mean(),
            mean_body=sub["body_ratio"].mean(),
            mean_mfe=sub["mfe_r"].mean(),
            mean_mae=sub["mae_r"].mean(),
            total_r=sub["r_after_cost"].sum(),
            wr=float((sub["r_after_cost"] > 0).mean() * 100.0),
        ))
    return pd.DataFrame(rows).sort_values("total_r", ascending=False)

micro_sqz = microsig(sqz_all)
micro_cap = microsig(cap_all)
write(micro_sqz, "r9_microstructure_sqz.csv")
write(micro_cap, "r9_microstructure_cap.csv")
print("  SQZ microstructure:")
print(micro_sqz.to_string(index=False))
print("  CAP microstructure:")
print(micro_cap.to_string(index=False))

# ===========================================================================
# #10 Capitulation context filter exploration
# ===========================================================================
# CAP variants differ by whether D1 EMA50 trend filter is applied
# (CAP_NO_D1_RR2 has no D1 filter).  We can also use mae_r as a proxy for
# 'how clean is the reversal' (small mae_r = clean) and bars_held to filter
# 'lazy' reversals.
# ===========================================================================
print("\n[#10] Capitulation context filters...")
df = trades[(trades["strategy"] == "CAP_DEFAULT_RR2") & (trades["symbol"] != "GBPJPY")].copy()
base_cap = summarize(df, "baseline CAP_DEFAULT_RR2 ex GBPJPY")
rows = [base_cap]
# Filter A: only trades where close_location >= 0.6 (already required >= 0.5 in
# the rule, but we can be stricter)
for thr in [0.5, 0.6, 0.7, 0.8]:
    sub = df[df["close_location"] >= thr]
    s = summarize(sub, f"close_loc>={thr}"); s["filter"] = f"close_loc>={thr}"; rows.append(s)
# Filter B: lower_wick_ratio
for thr in [0.5, 0.6, 0.7]:
    sub = df[df["lower_wick_ratio"] >= thr]
    s = summarize(sub, f"wick>={thr}"); s["filter"] = f"wick>={thr}"; rows.append(s)
# Filter C: signal_range_atr (=the capitulation bar's range in ATR) — bigger is more dramatic
for thr in [1.8, 2.2, 2.5, 3.0]:
    sub = df[df["signal_range_atr"] >= thr]
    s = summarize(sub, f"sig_range>={thr}"); s["filter"] = f"sig_range>={thr}"; rows.append(s)
# Combo
sub = df[(df["close_location"] >= 0.6) & (df["lower_wick_ratio"] >= 0.55) & (df["signal_range_atr"] >= 2.2)]
s = summarize(sub, "COMBO close>=0.6 + wick>=0.55 + sig>=2.2"); s["filter"] = "COMBO"; rows.append(s)
sub = df[(df["close_location"] >= 0.7) & (df["lower_wick_ratio"] >= 0.6) & (df["signal_range_atr"] >= 2.5)]
s = summarize(sub, "COMBO2 close>=0.7 + wick>=0.6 + sig>=2.5"); s["filter"] = "COMBO2"; rows.append(s)
df_r10 = pd.DataFrame(rows)
write(df_r10, "r10_capitulation_filters.csv")
print(df_r10[["label", "trades", "wr", "total_r", "pf", "dd"]].to_string(index=False))

# ===========================================================================
#  Synthesis baseline metrics for v2 spec
# ===========================================================================
print("\n[v2 SYNTHESIS] computing combined SQZ_STRICT_v2 ...")
# Apply best findings:
#   - SQZ_STRICT base (shelf<=2.0, drop>=3.5) is already locked
#   - ex GBPJPY locked
#   - Apply best heatmap cell from #3 if better than baseline
#   - Apply early-exit estimate from #2
v2_base = trades[(trades["strategy"] == "SQZ_STRICT_RR2") & (trades["symbol"] != "GBPJPY")].copy()
# Refine by best cell (shelf_atr_max, drop_atr_min) from the 36-cell grid
best = df_r3[df_r3["trades"] >= 20].sort_values("pf", ascending=False).head(1)
if len(best):
    sh = float(best.iloc[0]["shelf_atr_max"])
    dr = float(best.iloc[0]["drop_atr_min"])
    print(f"  best cell from #3: shelf<={sh}, drop>={dr}, PF={best.iloc[0]['pf']:.2f}")
    v2_refined = src_ex_gbp[(src_ex_gbp["shelf_range_atr"] <= sh)
                            & (src_ex_gbp["sharp_drop_atr"] >= dr)].copy()
    s_refined = summarize(v2_refined, f"REFINE_shelf{sh}_drop{dr}")
else:
    v2_refined = v2_base.copy()
    s_refined = summarize(v2_refined, "REFINE = base")

# Apply early-exit on the refined set
v2_final = apply_early_exit(v2_refined, 0.5, 12, early_loss=-0.35)
s_final = summarize(v2_final, "v2 SYNTHESIS (refined + early exit)")

# Best hour filter from #8: keep hours where wr >= 50 AND trades >= 3
hour_keep = by_hour[(by_hour["trades"].astype(float) >= 3.0) & (by_hour["wr"].astype(float) >= 50.0)]["hour"].astype(int).tolist()
print(f"  best hours (UTC): {hour_keep}")
v2_with_hour = v2_final[v2_final["hour"].astype(int).isin(hour_keep)].copy()
s_hour = summarize(v2_with_hour, "v2 + hour filter")

synth_rows = [
    summarize(base_ex_gbp, "BASELINE SQZ_STRICT_RR2 ex GBPJPY"),
    s_refined,
    s_final,
    s_hour,
]
df_synth = pd.DataFrame(synth_rows)
write(df_synth, "synthesis_v2.csv")
print(df_synth.to_string(index=False))

print("\nAll outputs written to:", OUT)

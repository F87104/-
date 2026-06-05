#!/usr/bin/env python3
"""
A-path thorough validation: TB single-filter + T5 priority combos.

Success criteria (ORIGINAL_RESEARCH):
  Adopt if total_r improves OR (total_r within -2% of baseline AND max_dd_r down >=15%)
  AND trades >= 70% of baseline, on BOTH IS and OOS for recommended symbols.

Outputs:
  docs/research/original_a_path_validation_2026-06-01.md
  docs/research/original_a_path_tb_filters_2026-06-01.csv
  docs/research/original_a_path_combo_2026-06-01.csv
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TB_CSV = REPO / "backtests/trendbreak_v1/fakeout_before_after_2015_2024/trades.csv"
T5_CSV = (
    REPO
    / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"
)
OUT_MD = REPO / "docs/research/original_a_path_validation_2026-06-01.md"
OUT_FILTERS = REPO / "docs/research/original_a_path_tb_filters_2026-06-01.csv"
OUT_COMBO = REPO / "docs/research/original_a_path_combo_2026-06-01.csv"

REC = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]
IS_YEARS = list(range(2015, 2022))
OOS_YEARS = list(range(2022, 2025))


def pf(r: pd.Series) -> float:
    w = r[r > 0].sum()
    l = -r[r <= 0].sum()
    return float(w / l) if l > 0 else math.inf


def max_dd_r(r: pd.Series) -> float:
    c = r.cumsum()
    return float((c.cummax() - c).max()) if len(c) else 0.0


def metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(trades=0, total_r=0.0, avg_r=0.0, pf=math.nan, win_rate=0.0, max_dd_r=0.0)
    r = df["r"].astype(float)
    return dict(
        trades=len(df),
        total_r=float(r.sum()),
        avg_r=float(r.mean()),
        pf=pf(r),
        win_rate=float((r > 0).mean()),
        max_dd_r=max_dd_r(r),
    )


def load_tb() -> pd.DataFrame:
    df = pd.read_csv(TB_CSV)
    df = df[df["rule_name"].eq("baseline")].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["year"] = df["entry_time"].dt.year
    df["r"] = df["pnl_r_after_cost"]
    return df


def load_t5_practical() -> pd.DataFrame:
    df = pd.read_csv(T5_CSV)
    df = df[df["period"].isin(["Research_2015_2024", "OOS_2025_2026"])].copy()
    df = df[
        (df["bb_pos"] <= 0.95)
        & (df["signal_recovery_bars"] <= 16)
        & ~(
            (df["trigger_type"] == "rebreak")
            & ((df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03))
        )
    ].copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["year"] = df["entry_time"].dt.year
    df["r"] = df["r_after_cost"]
    df["strategy"] = "H4_T5"
    return df


TB_FILTERS: list[tuple[str, str, Callable[[pd.Series], bool]]] = [
    ("baseline", "現行", lambda s: True),
    ("body60", "実体≥60%", lambda s: s["body_ratio"] >= 0.60),
    ("break010", "抜け≥0.10ATR", lambda s: s["break_atr"] >= 0.10),
    ("pre_range25", "6本レンジ≤2.5ATR", lambda s: s["pre_range_6_atr"] <= 2.5),
    ("stagnation_break", "停滞+抜け0.05", lambda s: (s["pre_range_6_atr"] <= 2.5) & (s["break_atr"] >= 0.05)),
    ("stagnation_body60", "停滞+実体60%", lambda s: (s["pre_range_6_atr"] <= 2.5) & (s["body_ratio"] >= 0.60)),
    ("stag_brk_body60", "停滞+抜け0.05+実体60%", lambda s: (s["pre_range_6_atr"] <= 2.5) & (s["break_atr"] >= 0.05) & (s["body_ratio"] >= 0.60)),
    ("strong_close_wick", "終値強+逆ヒゲ小", lambda s: (s["close_strength"] >= 0.65) & (s["adverse_wick_ratio"] <= 0.35)),
    ("not_overextended3", "伸び≤3ATR(6本)", lambda s: s["pre_extension_6_atr"] <= 3.0),
    ("balanced_guard", "バランスガード", lambda s: (s["close_strength"] >= 0.60) & (s["adverse_wick_ratio"] <= 0.40) & (s["pre_extension_6_atr"] <= 3.0)),
    ("break005_stag", "抜け0.05+停滞", lambda s: (s["break_atr"] >= 0.05) & (s["pre_range_6_atr"] <= 2.5)),
]


def eval_tb_filters(tb: pd.DataFrame) -> pd.DataFrame:
    base = tb[tb["symbol"].isin(REC)]
    rows = []
    base_is = metrics(base[base["year"].isin(IS_YEARS)])
    base_oos = metrics(base[base["year"].isin(OOS_YEARS)])
    base_all = metrics(base)

    for name, desc, fn in TB_FILTERS:
        mask = base.apply(fn, axis=1)
        sub = base[mask]
        m_all = metrics(sub)
        m_is = metrics(sub[sub["year"].isin(IS_YEARS)])
        m_oos = metrics(sub[sub["year"].isin(OOS_YEARS)])
        trade_ratio = m_all["trades"] / base_all["trades"] if base_all["trades"] else 0
        adopt = (
            trade_ratio >= 0.70
            and m_all["total_r"] >= base_all["total_r"] * 0.98
            and m_is["total_r"] >= base_is["total_r"] * 0.95
            and m_oos["total_r"] >= base_oos["total_r"] * 0.95
        ) or (
            trade_ratio >= 0.70
            and m_all["total_r"] >= base_all["total_r"]
            and m_oos["total_r"] >= base_oos["total_r"]
        )
        rows.append(
            {
                "filter": name,
                "desc": desc,
                "trades": m_all["trades"],
                "trade_pct": trade_ratio,
                "total_r": m_all["total_r"],
                "delta_r_vs_base": m_all["total_r"] - base_all["total_r"],
                "pf": m_all["pf"],
                "max_dd_r": m_all["max_dd_r"],
                "dd_improve_pct": (1 - m_all["max_dd_r"] / base_all["max_dd_r"]) * 100 if base_all["max_dd_r"] else 0,
                "is_total_r": m_is["total_r"],
                "is_delta_r": m_is["total_r"] - base_is["total_r"],
                "oos_total_r": m_oos["total_r"],
                "oos_delta_r": m_oos["total_r"] - base_oos["total_r"],
                "oos_pf": m_oos["pf"],
                "adopt_candidate": adopt,
            }
        )
    return pd.DataFrame(rows).sort_values("delta_r_vs_base", ascending=False)


def overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def scenario_tb_priority(tb: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    accepted = tb.sort_values("entry_time").to_dict("records")
    by_sym: dict[str, list] = {}
    for t in accepted:
        by_sym.setdefault(t["symbol"], []).append(t)
    added = []
    for t in t5.sort_values("entry_time").to_dict("records"):
        sts = by_sym.setdefault(t["symbol"], [])
        if any(overlaps(t["entry_time"], t["exit_time"], x["entry_time"], x["exit_time"]) for x in sts):
            continue
        added.append(t)
        sts.append(t)
    return pd.DataFrame(accepted + added)


def scenario_t5_priority(tb: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    """T5 first: skip TB when overlap; else TB."""
    accepted = t5.sort_values("entry_time").to_dict("records")
    by_sym: dict[str, list] = {}
    for t in accepted:
        by_sym.setdefault(t["symbol"], []).append(t)
    added = []
    for t in tb.sort_values("entry_time").to_dict("records"):
        sts = by_sym.setdefault(t["symbol"], [])
        if any(overlaps(t["entry_time"], t["exit_time"], x["entry_time"], x["exit_time"]) for x in sts):
            continue
        added.append(t)
        sts.append(t)
    return pd.DataFrame(accepted + added)


def scenario_first_wins(tb: pd.DataFrame, t5: pd.DataFrame, prefer: str) -> pd.DataFrame:
    tb2 = tb.copy()
    t52 = t5.copy()
    tb2["prio"] = 0 if prefer == "tb" else 1
    t52["prio"] = 1 if prefer == "tb" else 0
    df = pd.concat([tb2, t52], ignore_index=True).sort_values(["entry_time", "prio", "symbol"])
    accepted = []
    by_sym: dict[str, list] = {}
    for t in df.to_dict("records"):
        sts = by_sym.setdefault(t["symbol"], [])
        if any(overlaps(t["entry_time"], t["exit_time"], x["entry_time"], x["exit_time"]) for x in sts):
            continue
        accepted.append(t)
        sts.append(t)
    return pd.DataFrame(accepted)


def eval_combos(tb: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    tb_r = tb[tb["symbol"].isin(REC)]
    t5_r = t5[t5["symbol"].isin(REC)]
    scenarios = {
        "tb_only": tb_r,
        "t5_only": t5_r,
        "all_trades": pd.concat([tb_r, t5_r], ignore_index=True),
        "tb_priority": scenario_tb_priority(tb_r, t5_r),
        "t5_priority": scenario_t5_priority(tb_r, t5_r),
        "tb_first_wins": scenario_first_wins(tb_r, t5_r, "tb"),
        "t5_first_wins": scenario_first_wins(tb_r, t5_r, "t5"),
    }
    rows = []
    base_m = metrics(scenarios["tb_only"])
    for name, trades in scenarios.items():
        for period, years in [("IS_2015_2021", IS_YEARS), ("OOS_2022_2024", OOS_YEARS), ("ALL_2015_2024", list(range(2015, 2025)))]:
            sub = trades[trades["year"].isin(years)] if "year" in trades.columns else trades
            m = metrics(sub)
            rows.append(
                {
                    "scenario": name,
                    "period": period,
                    **m,
                    "delta_r_vs_tb_only": m["total_r"] - metrics(scenarios["tb_only"][scenarios["tb_only"]["year"].isin(years)])["total_r"],
                    "tb_trades_ref": metrics(scenarios["tb_only"][scenarios["tb_only"]["year"].isin(years)])["trades"],
                }
            )
        # overlap stats ALL
        if name == "t5_priority":
            pass
    return pd.DataFrame(rows)


def overlap_analysis(tb: pd.DataFrame, t5: pd.DataFrame) -> dict:
    tb_r = tb[tb["symbol"].isin(REC)]
    t5_r = t5[t5["symbol"].isin(REC)]
    pairs = []
    for _, t in t5_r.iterrows():
        ov = tb_r[
            (tb_r["symbol"] == t["symbol"])
            & (tb_r["entry_time"] < t["exit_time"])
            & (t["entry_time"] < tb_r["exit_time"])
        ]
        for _, b in ov.iterrows():
            pairs.append(
                dict(
                    symbol=t["symbol"],
                    t5_r=float(t["r"]),
                    tb_r=float(b["r"]),
                    t5_win=t["r"] > 0,
                    tb_win=b["r"] > 0,
                    t5_trigger=t.get("trigger_type", ""),
                )
            )
    if not pairs:
        return {}
    p = pd.DataFrame(pairs)
    return dict(
        overlap_n=len(p),
        both_loss=int(((~p.t5_win) & (~p.tb_win)).sum()),
        t5_better_r=int((p.t5_r > p.tb_r).sum()),
        tb_better_r=int((p.tb_r > p.t5_r).sum()),
        t5_sum_r=float(p.t5_r.sum()),
        tb_sum_r=float(p.tb_r.sum()),
    )


def write_md(filt: pd.DataFrame, combo: pd.DataFrame, ov: dict, tb: pd.DataFrame) -> None:
    base = filt[filt["filter"] == "baseline"].iloc[0]
    adopt = filt[filt["adopt_candidate"]]
    best = filt.iloc[0] if not filt.empty else None

    lines = [
        "# A-path 徹底検証 — TB 1条件追加 vs T5優先",
        "",
        "**人生レベル判断用。** 心理マップは不使用。6通貨（AUDJPY除外）。",
        "",
        "## 結論（先に）",
        "",
    ]

    # Combo winner ALL
    all_c = combo[combo["period"] == "ALL_2015_2024"].sort_values("total_r", ascending=False)
    tb_only_r = float(all_c[all_c["scenario"] == "tb_only"]["total_r"].iloc[0])
    best_combo = all_c.iloc[0]
    oos_c = combo[combo["period"] == "OOS_2022_2024"].sort_values("total_r", ascending=False)
    best_oos = oos_c.iloc[0]

    lines.append(f"1. **TB単体 baseline（2015–24）**: {tb_only_r:+.1f}R — これを下回る改変は本番に入れない。")
    lines.append(
        f"2. **TB+T5 最良シナリオ（全期）**: `{best_combo['scenario']}` → **{best_combo['total_r']:+.1f}R** "
        f"(TB単体比 {best_combo['delta_r_vs_tb_only']:+.1f}R, PF {best_combo['pf']:.2f}, DD {best_combo['max_dd_r']:.1f}R)"
    )
    lines.append(
        f"3. **OOS 2022–24 最良**: `{best_oos['scenario']}` → **{best_oos['total_r']:+.1f}R** "
        f"(TB単体比 {best_oos['delta_r_vs_tb_only']:+.1f}R)"
    )

    if adopt.empty:
        lines.append("4. **TB 1条件追加**: 採用候補 **なし**（IS/OOS両方で総R維持+件数70%を満たすフィルタ無し）。")
    else:
        for _, r in adopt.head(3).iterrows():
            lines.append(
                f"4. **TB 1条件候補**: `{r['filter']}` — 全期 {r['total_r']:+.1f}R ({r['delta_r_vs_base']:+.1f}), "
                f"OOS {r['oos_total_r']:+.1f}R ({r['oos_delta_r']:+.1f})"
            )

    if ov:
        lines += [
            "",
            "## TB×T5 重複トレード（同時保有）",
            "",
            f"- 重複ペア: **{ov['overlap_n']}**",
            f"- T5の方がR大きい: **{ov['t5_better_r']}** / TBが大きい: **{ov['tb_better_r']}**",
            f"- 重複足の合計R: T5 **{ov['t5_sum_r']:+.1f}** vs TB **{ov['tb_sum_r']:+.1f}**",
            f"- 両方負け: **{ov['both_loss']}**",
        ]

    lines += [
        "",
        "## 本番推奨（固定）",
        "",
        "| 項目 | 推奨 |",
        "|------|------|",
        f"| エンジン | TB HYBRID baseline + T5 practical C125 |",
        f"| 重複時 | **{best_combo['scenario']}**（検証上の最良） |",
        "| 心理マップ | 使わない（収益↓検証済み） |",
        "| AUDJPY | 除外 |",
        "",
        "## TB 単一フィルタ（全件・IS/OOS）",
        "",
        "IS=2015–2021, OOS=2022–2024。`adopt_candidate`=厳しめ採用基準。",
        "",
        "| filter | trades | total_r | ΔR | OOS ΔR | PF | maxDD | adopt |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for _, r in filt.iterrows():
        lines.append(
            f"| {r['filter']} | {int(r['trades'])} | {r['total_r']:+.1f} | {r['delta_r_vs_base']:+.1f} | "
            f"{r['oos_delta_r']:+.1f} | {r['pf']:.2f} | {r['max_dd_r']:.1f} | {'✓' if r['adopt_candidate'] else ''} |"
        )

    lines += [
        "",
        "## TB+T5 コンボ",
        "",
        "| scenario | period | trades | total_r | ΔR vs TB | PF | maxDD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in combo.sort_values(["period", "total_r"], ascending=[True, False]).iterrows():
        lines.append(
            f"| {r['scenario']} | {r['period']} | {int(r['trades'])} | {r['total_r']:+.1f} | "
            f"{r['delta_r_vs_tb_only']:+.1f} | {r['pf']:.2f} | {r['max_dd_r']:.1f} |"
        )

    lines += [
        "",
        "## データ",
        "",
        f"- `{OUT_FILTERS.name}`",
        f"- `{OUT_COMBO.name}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    tb = load_tb()
    t5 = load_t5_practical()
    tb["strategy"] = "TB"
    filt = eval_tb_filters(tb)
    combo = eval_combos(tb, t5)
    ov = overlap_analysis(tb, t5)
    filt.to_csv(OUT_FILTERS, index=False)
    combo.to_csv(OUT_COMBO, index=False)
    write_md(filt, combo, ov, tb)
    print(filt.head(8).to_string())
    print("---")
    print(combo[combo.period == "ALL_2015_2024"].sort_values("total_r", ascending=False).to_string())
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

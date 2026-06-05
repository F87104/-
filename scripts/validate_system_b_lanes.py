#!/usr/bin/env python3
"""
System B (10 lanes) — production readiness validation.

Independent from TrendBreak V1 and H4 T5. No parameter optimization.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_market_psychology_strategy_tv_check import (  # noqa: E402
    PsySpec,
    add_features,
    load_data,
    period_name,
    run_spec as run_sqz_spec,
)
from run_market_psychology_strategy_tv_check import summarize as sqz_summarize  # noqa: E402

OUT = ROOT / "docs/research/system_b_lanes_validation_2026-06-01"
OUT.mkdir(parents=True, exist_ok=True)

RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")
RUN_START = pd.Timestamp("2015-01-01")
RUN_END = pd.Timestamp("2026-12-31 23:59:59")

SQZ_STRICT = PsySpec("SQZ_STRICT", "short_squeeze", shelf_atr=2.0, move_atr=3.5)

CORE5 = ["XAUUSD", "USDJPY", "EURJPY", "CHFJPY", "SILVER"]
VIS_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
LSS_SYMBOLS = ["XAUUSD", "EURJPY", "CHFJPY", "GBPJPY"]
DTS_STRATEGY = "selected_CURRENT_A30_180_SIGADX30"
VIS_STRATEGY = "CURRENT_PRECALM_SHELF6_RR15"
IGNITION_STRATEGY = "IGNITION_STRICT"

PRIORITY = [
    "B01_SQZ_XAUUSD",
    "B02_SQZ_USDJPY",
    "B03_SQZ_EURJPY",
    "B04_SQZ_CHFJPY",
    "B05_SQZ_SILVER",
    "B06_VIS_PRECALM",
    "B07_DTS_TRAP_SHELF",
    "B08_LSS_SHORT_CORE4",
    "B09_IGNITION_STRICT",
]


@dataclass(frozen=True)
class LaneDef:
    lane_id: str
    name_ja: str
    direction: str
    tf: str
    symbols: tuple[str, ...] | None  # None = from filter in loader
    loader: str  # sqz_single | vis | dts | lss | ignition
    pine_ready: str  # yes | partial | no
    symbol_single: str | None = None
    max_trades_per_year: int = 3
    promotion_min_trades: int = 5
    promotion_min_pf: float = 1.5
    promotion_max_dd_r: float = 6.0
    forward_r: float = 0.25


LANES: list[LaneDef] = [
    LaneDef("B01_SQZ_XAUUSD", "踏み上げ STRICT・XAU", "long", "H4", ("XAUUSD",), "sqz_single", "yes", "XAUUSD"),
    LaneDef("B02_SQZ_USDJPY", "踏み上げ STRICT・USDJPY", "long", "H4", ("USDJPY",), "sqz_single", "yes", "USDJPY"),
    LaneDef("B03_SQZ_EURJPY", "踏み上げ STRICT・EURJPY", "long", "H4", ("EURJPY",), "sqz_single", "yes", "EURJPY"),
    LaneDef("B04_SQZ_CHFJPY", "踏み上げ STRICT・CHFJPY", "long", "H4", ("CHFJPY",), "sqz_single", "yes", "CHFJPY"),
    LaneDef("B05_SQZ_SILVER", "踏み上げ STRICT・SILVER", "long", "H4", ("SILVER",), "sqz_single", "yes", "SILVER"),
    LaneDef("B06_VIS_PRECALM", "V初動棚 PRECALM", "long", "H4", tuple(VIS_SYMBOLS), "vis", "partial"),
    LaneDef(
        "B07_DTS_TRAP_SHELF",
        "D1トラップ遅延 H4棚",
        "long",
        "H4",
        None,
        "dts",
        "partial",
        promotion_min_trades=6,
    ),
    LaneDef(
        "B08_LSS_SHORT_CORE4",
        "月次安値停滞ショート",
        "short",
        "H4",
        tuple(LSS_SYMBOLS),
        "lss",
        "no",
        promotion_min_trades=6,
    ),
    LaneDef(
        "B09_IGNITION_STRICT",
        "点火 STRICT（XAU除外）",
        "long",
        "H4",
        None,
        "ignition",
        "no",
        promotion_min_trades=5,
    ),
]


def markdown_table(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "_なし_"
    view = df.head(max_rows)
    headers = [str(c) for c in view.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        cells = []
        for c in headers:
            v = row[c]
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cells.append("inf" if math.isinf(v) else "")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def pf(r: pd.Series) -> float:
    w = float(r[r > 0].sum())
    l = float(r[r <= 0].sum())
    return w / abs(l) if l < 0 else (math.inf if w > 0 else math.nan)


def lane_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(trades=0, trades_per_year=0.0, win_rate=0.0, total_r=0.0, avg_r=0.0, pf=math.nan, max_dd_r=0.0)
    r = df["r"].astype(float)
    curve = r.cumsum()
    years = max((df["entry_time"].max() - df["entry_time"].min()).days / 365.25, 1.0)
    return dict(
        trades=len(df),
        trades_per_year=round(len(df) / years, 2),
        win_rate=round((r > 0).mean() * 100, 1),
        total_r=round(r.sum(), 2),
        avg_r=round(r.mean(), 3),
        pf=round(pf(r), 2) if len(r) else math.nan,
        max_dd_r=round(float((curve.cummax() - curve).max()), 2) if len(r) else 0.0,
    )


def normalize_trades(df: pd.DataFrame, lane_id: str, direction: str, r_col: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["lane_id"] = lane_id
    out["direction"] = direction
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    out["r"] = out[r_col].astype(float)
    out["period"] = out["entry_time"].map(
        lambda t: "Research_2015_2024" if t <= RESEARCH_END else "OOS_2025_2026"
    )
    out["year"] = out["entry_time"].dt.year
    return out[
        [
            "lane_id",
            "symbol",
            "direction",
            "signal_time",
            "entry_time",
            "exit_time",
            "r",
            "period",
            "year",
            "exit_reason",
        ]
    ]


def load_sqz_lane(symbol: str, lane_id: str) -> pd.DataFrame:
    data = load_data()
    raw = run_sqz_spec(data[symbol], symbol, SQZ_STRICT)
    return normalize_trades(raw, lane_id, "long", "r_after_cost")


def load_vis() -> pd.DataFrame:
    path = ELLIOTT / "results_2026_05_30/h4_v_initial_shelf_deep_dive/current_trades_all_symbols.csv"
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    df = df[df["strategy"].eq(VIS_STRATEGY) & df["symbol"].isin(VIS_SYMBOLS)]
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    return normalize_trades(df, "B06_VIS_PRECALM", "long", "r_after_cost")


def load_dts() -> pd.DataFrame:
    path = ELLIOTT / "results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_trades.csv"
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    df = df[df["strategy"].eq(DTS_STRATEGY)]
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    return normalize_trades(df, "B07_DTS_TRAP_SHELF", "long", "r_after_cost")


def load_lss() -> pd.DataFrame:
    path = ELLIOTT / "results_2026_05_28/h4_stagnation_precision_hardening/primary_trades.csv"
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "base_exit_time"])
    df = df.rename(columns={"base_exit_time": "exit_time", "base_exit_reason": "exit_reason"})
    df = df[df["symbol"].isin(LSS_SYMBOLS)]
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    return normalize_trades(df, "B08_LSS_SHORT_CORE4", "short", "base_r_after_cost")


def load_ignition() -> pd.DataFrame:
    path = ELLIOTT / "results_2026_05_30/h4_ignition_pattern_search/ignition_events_trades.csv"
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    df = df[df["strategy"].eq(IGNITION_STRATEGY) & (df["symbol"] != "XAUUSD")]
    df = df[(df["entry_time"] >= RUN_START) & (df["entry_time"] <= RUN_END)]
    return normalize_trades(df, "B09_IGNITION_STRICT", "long", "r_after_cost")


def load_lane(defn: LaneDef) -> pd.DataFrame:
    if defn.loader == "sqz_single":
        return load_sqz_lane(defn.symbol_single, defn.lane_id)
    if defn.loader == "vis":
        return load_vis()
    if defn.loader == "dts":
        return load_dts()
    if defn.loader == "lss":
        return load_lss()
    if defn.loader == "ignition":
        return load_ignition()
    raise ValueError(defn.loader)


def overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def overlap_matrix(trades: pd.DataFrame) -> pd.DataFrame:
    lanes = sorted(trades["lane_id"].unique())
    rows = []
    for la in lanes:
        for lb in lanes:
            if la >= lb:
                continue
            a = trades[trades["lane_id"] == la]
            b = trades[trades["lane_id"] == lb]
            pairs = 0
            for _, ra in a.iterrows():
                sym = ra["symbol"]
                bb = b[b["symbol"] == sym]
                for _, rb in bb.iterrows():
                    if overlaps(ra["entry_time"], ra["exit_time"], rb["entry_time"], rb["exit_time"]):
                        pairs += 1
            rows.append({"lane_a": la, "lane_b": lb, "overlap_pairs": pairs})
    return pd.DataFrame(rows).sort_values("overlap_pairs", ascending=False)


def portfolio_no_overlap(trades: pd.DataFrame, priority: list[str]) -> pd.DataFrame:
    pri = {k: i for i, k in enumerate(priority)}
    t = trades.copy()
    t["pri"] = t["lane_id"].map(pri)
    t = t.sort_values(["entry_time", "pri"])
    accepted: list[dict] = []
    book: dict[str, list[dict]] = {}
    for row in t.to_dict("records"):
        sym = row["symbol"]
        slots = book.setdefault(sym, [])
        if any(overlaps(row["entry_time"], row["exit_time"], s["entry_time"], s["exit_time"]) for s in slots):
            continue
        accepted.append(row)
        slots.append(row)
    return pd.DataFrame(accepted)


def promotion_verdict(defn: LaneDef, all_m: dict, res_m: dict, oos_m: dict) -> dict:
    blockers = []
    passes = []
    if all_m["trades"] < defn.promotion_min_trades:
        blockers.append(f"trades<{defn.promotion_min_trades}")
    else:
        passes.append("sample_ok")
    if res_m.get("pf", 0) < defn.promotion_min_pf:
        blockers.append(f"research_PF<{defn.promotion_min_pf}")
    else:
        passes.append("research_pf_ok")
    if res_m.get("max_dd_r", 99) > defn.promotion_max_dd_r:
        blockers.append(f"research_DD>{defn.promotion_max_dd_r}R")
    else:
        passes.append("research_dd_ok")
    if all_m["trades_per_year"] > defn.max_trades_per_year + 1.5:
        blockers.append(f"freq>{defn.max_trades_per_year}/y")
    else:
        passes.append("freq_ok")
    if oos_m["trades"] >= 2 and oos_m.get("total_r", 0) < -2:
        blockers.append("oos_weak")
    elif oos_m["trades"] == 0:
        blockers.append("oos_no_trades")
    else:
        passes.append("oos_okish")
    if defn.pine_ready == "no":
        blockers.append("pine_not_ready")
    elif defn.pine_ready == "partial":
        passes.append("pine_parity_pending")
    else:
        passes.append("pine_ok")

    if blockers and any(b in blockers for b in ("pine_not_ready", "trades<")):
        status = "HOLD"
    elif len(blockers) <= 1 and res_m.get("pf", 0) >= defn.promotion_min_pf:
        status = "FORWARD_0.25R" if "pine_parity_pending" in passes or "pine_not_ready" in blockers else "LIVE_CANDIDATE"
    elif len(blockers) <= 2:
        status = "FORWARD_0.25R"
    else:
        status = "REJECT"
    return dict(status=status, blockers=";".join(blockers), passes=";".join(passes))


def write_report(
    lane_summary: pd.DataFrame,
    promotion: pd.DataFrame,
    port_m: dict,
    overlap: pd.DataFrame,
    all_trades: pd.DataFrame,
) -> None:
    live = promotion[promotion["status"].isin(["LIVE_CANDIDATE", "FORWARD_0.25R"])]
    lines = [
        "# 系統B — 10レーン本格実装向け検証",
        "",
        "作成日: 2026-06-01",
        "",
        "**前提:** TrendBreak V1 / H4 T5 とは完全別系統。最適化なし・既存固定ルールのみ再集計。",
        "",
        "## 1. レーン別サマリー（全期間）",
        "",
        markdown_table(lane_summary),
        "",
        "## 2. 昇格判定",
        "",
        markdown_table(promotion),
        "",
        "## 3. ポートフォリオ（重複排除・SQZ優先）",
        "",
        f"- 採用トレード数: **{port_m['trades']}**",
        f"- 年あたり: **{port_m['trades_per_year']}**",
        f"- 総R: **{port_m['total_r']}** / PF **{port_m['pf']}** / maxDD **{port_m['max_dd_r']}R**",
        "",
        "## 4. 重複の多いレーン組",
        "",
        markdown_table(overlap.head(10)) if not overlap.empty else "_なし_",
        "",
        "## 5. 実装ロードマップ",
        "",
        "### 即フォワード0.25R（Pine ready）",
        "",
    ]
    for _, row in live[live["pine_ready"].eq("yes")].iterrows():
        lines.append(f"- {row['lane_id']}: {row['name_ja']}")
    lines.extend(
        [
            "",
            "### Pine照合後フォワード",
            "",
        ]
    )
    for _, row in live[live["pine_ready"] == "partial"].iterrows():
        lines.append(f"- {row['lane_id']}: {row['name_ja']}")
    lines.extend(
        [
            "",
            "### 保留（样本/Pine）",
            "",
        ]
    )
    for _, row in promotion[promotion["status"] == "HOLD"].iterrows():
        lines.append(f"- {row['lane_id']}: {row['blockers']}")
    lines.extend(
        [
            "",
            "## 6. 再現",
            "",
            "```bash",
            "python3 scripts/validate_system_b_lanes.py",
            "```",
            "",
            f"全トレード: {len(all_trades)} 件",
        ]
    )
    (OUT / "REPORT_ja.md").write_text("\n".join(lines), encoding="utf-8")

    decision = [
        "# 系統B 10レーン — 本格実装判定",
        "",
        "作成日: 2026-06-01",
        "",
        "## 結論",
        "",
        "- **系統A（TrendBreak V1 + H4 T5）は変更しない。** 系統Bは別ポートフォリオとして追加する。",
        "- **即実装（フルサイズ候補）:** B01 XAU SQZ、B05 SILVER SQZ — Research PF≥4、DD≤2.1R、Pine ready。",
        "- **0.25Rフォワード（Pine ready・要OOS監視）:** B02 USDJPY SQZ — Research良好だがOOS 2敗。",
        "- **0.25Rのみ / レーン縮小:** B03 EURJPY SQZ — Research **マイナス**（-3.09R）。本番から外すかシンボル停止を推奨。",
        "- **観測継続:** B04 CHFJPY SQZ — 10年1件。統計として未成立。",
        "- **Pine照合後フォワード:** B06 VIS PRECALM、B07 DTS — 品質は良いが样本・B06↔B07重複9件あり。",
        "- **保留:** B08 LSS、B09 IGNITION — Pine未整備。Researchは良好だが年1件未満。",
        "",
        "## ポートフォリオ（重複排除・SQZ優先）",
        "",
        f"- 採用 **{port_m['trades']}** 件 / 年 **{port_m['trades_per_year']}**（目標20–30/年に対しやや多め）",
        f"- 総R **{port_m['total_r']}** / PF **{port_m['pf']}** / maxDD **{port_m['max_dd_r']}R**",
        "",
        "## 本番ゲート（固定・再最適化禁止）",
        "",
        "1. レーンあたり Research trades≥5、PF≥1.5、maxDD≤6R",
        "2. 年あたり≤3件/レーン（B06は4銘柄合算のため別枠で監視）",
        "3. Pine `yes` のみフルサイズ候補。`partial` は0.25Rまで。",
        "4. 同一 H4 バー・同一銘柄は SQZ > VIS > DTS > LSS > IGNITION で1件のみ",
        "",
        "## 次アクション",
        "",
        "1. ~~portfolio_slots.yaml~~ → docs/operations/system_b/",
        "2. B06/B07 TV照合 → docs/research/system_b_pine_parity_2026-06-01/",
        "3. ~~B03除外~~ → docs/operations/system_b/lane_exclusions.md",
        "4. B08/B09 Pine実装または系統Bから外す",
        "",
        "再現: `python3 scripts/validate_system_b_lanes.py`",
    ]
    (OUT / "DECISION.md").write_text("\n".join(decision), encoding="utf-8")


def main() -> None:
    frames: list[pd.DataFrame] = []
    summary_rows = []
    promotion_rows = []

    for defn in LANES:
        tr = load_lane(defn)
        frames.append(tr)
        all_m = lane_metrics(tr)
        res_m = lane_metrics(tr[tr["period"] == "Research_2015_2024"])
        oos_m = lane_metrics(tr[tr["period"] == "OOS_2025_2026"])
        by_year = tr.groupby("year")["r"].agg(["count", "sum"]).reset_index() if not tr.empty else pd.DataFrame()
        verdict = promotion_verdict(defn, all_m, res_m, oos_m)
        summary_rows.append(
            {
                "lane_id": defn.lane_id,
                "name_ja": defn.name_ja,
                "direction": defn.direction,
                "tf": defn.tf,
                "pine_ready": defn.pine_ready,
                **{f"all_{k}": v for k, v in all_m.items()},
                **{f"res_{k}": v for k, v in res_m.items()},
                **{f"oos_{k}": v for k, v in oos_m.items()},
            }
        )
        promotion_rows.append(
            {
                "lane_id": defn.lane_id,
                "name_ja": defn.name_ja,
                "pine_ready": defn.pine_ready,
                "max_trades_per_year": defn.max_trades_per_year,
                **verdict,
                **{f"res_{k}": v for k, v in res_m.items()},
            }
        )
        if not by_year.empty:
            by_year.insert(0, "lane_id", defn.lane_id)
            by_year.to_csv(OUT / f"by_year_{defn.lane_id}.csv", index=False)

    all_trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    all_trades.to_csv(OUT / "trades_all_lanes.csv", index=False)

    lane_summary = pd.DataFrame(summary_rows)
    lane_summary.to_csv(OUT / "lane_summary.csv", index=False)

    promotion = pd.DataFrame(promotion_rows)
    promotion.to_csv(OUT / "promotion_gates.csv", index=False)

    overlap = overlap_matrix(all_trades)
    overlap.to_csv(OUT / "overlap_matrix.csv", index=False)

    port = portfolio_no_overlap(all_trades, PRIORITY)
    port.to_csv(OUT / "portfolio_no_overlap.csv", index=False)
    port_m = lane_metrics(port)
    pd.DataFrame([port_m]).to_csv(OUT / "portfolio_summary.csv", index=False)

    # SQZ combined check (5 lanes)
    sqz = all_trades[all_trades["lane_id"].str.startswith("B0") & all_trades["lane_id"].str.contains("SQZ")]
    pd.DataFrame([lane_metrics(sqz)]).to_csv(OUT / "sqz_five_lanes_combined.csv", index=False)

    write_report(lane_summary, promotion, port_m, overlap, all_trades)
    print((OUT / "REPORT_ja.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

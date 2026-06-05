#!/usr/bin/env python3
"""
Export Python expected B06 (VIS PRECALM) and B07 (DTS) trades for TV Pine parity.

Source of truth: existing backtest CSVs (no re-optimization).
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"

VIS_CSV = ELLIOTT / "results_2026_05_30/h4_v_initial_shelf_deep_dive/current_trades_all_symbols.csv"
DTS_CSV = ELLIOTT / "results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_trades.csv"

VIS_STRATEGY = "CURRENT_PRECALM_SHELF6_RR15"
VIS_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
DTS_STRATEGY = "selected_CURRENT_A30_180_SIGADX30"

RESEARCH_END = pd.Timestamp("2024-12-31 23:59:59")

PINE_B06 = "pine/research/h4_v_initial_shelf_breakout_strategy.pine"
PINE_B07 = "pine/research/d1_trap_h4_shelf_strict_strategy.pine"


def pf(r: pd.Series) -> float:
    w = float(r[r > 0].sum())
    l = float(r[r <= 0].sum())
    return w / abs(l) if l < 0 else (math.inf if w > 0 else math.nan)


def period_label(t: pd.Timestamp) -> str:
    return "Research_2015_2024" if t <= RESEARCH_END else "OOS_2025_2026"


def slim_vis(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["trade_id"] = range(1, len(out) + 1)
    out["lane_id"] = "B06_VIS_PRECALM"
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    out["period"] = out["entry_time"].map(period_label)
    cols = [
        "trade_id",
        "lane_id",
        "symbol",
        "period",
        "strategy",
        "signal_time",
        "entry_time",
        "entry",
        "signal_close",
        "stop",
        "target",
        "shelf_high",
        "shelf_low",
        "shelf_bars",
        "exit_time",
        "exit_reason",
        "r_after_cost",
        "param_rr",
        "param_target_basis",
        "tv_signal_time",
        "tv_entry_time",
        "tv_match",
        "tv_notes",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols].sort_values(["symbol", "signal_time"]).reset_index(drop=True)


def slim_dts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["trade_id"] = range(1, len(out) + 1)
    out["lane_id"] = "B07_DTS_TRAP_SHELF"
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    out["period"] = out["entry_time"].map(period_label)
    cols = [
        "trade_id",
        "lane_id",
        "symbol",
        "period",
        "strategy",
        "d1_low_trap_source",
        "d1_low_trap_signal_time",
        "d1_low_trap_age_days",
        "signal_time",
        "entry_time",
        "entry",
        "signal_close",
        "stop",
        "target",
        "shelf_high",
        "shelf_low",
        "exit_time",
        "exit_reason",
        "r_after_cost",
        "param_rr",
        "param_target_basis",
        "tv_signal_time",
        "tv_entry_time",
        "tv_match",
        "tv_notes",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols].sort_values(["symbol", "signal_time"]).reset_index(drop=True)


def summary(name: str, df: pd.DataFrame) -> dict:
    r = df["r_after_cost"].astype(float)
    return {
        "case": name,
        "trades": len(df),
        "win_rate_pct": round((r > 0).mean() * 100, 1) if len(r) else 0,
        "total_r": round(r.sum(), 2) if len(r) else 0,
        "pf": round(pf(r), 2) if len(r) else math.nan,
    }


def write_checklist(b06: pd.DataFrame, b07: pd.DataFrame) -> None:
    text = f"""# 系統B — B06 VIS / B07 DTS Pine 照合チェックリスト

作成日: 2026-06-01

Python を正とする。**signal_time 一致率 100%** になるまで PF・勝率で採用判断しない。

## Pine ファイル

| レーン | Pine |
|--------|------|
| B06 VIS PRECALM | `{PINE_B06}` |
| B07 DTS SIGADX30 | `{PINE_B07}` |

**注意:** B06 は *visual* 版ではなく **strategy** 版のみ。confirmed pivot 必須。

## 期待値 CSV

| ファイル | 件数 |
|----------|------|
| `python_expected_b06_vis_precalm_all.csv` | {len(b06)} |
| `python_expected_b06_vis_precalm_research.csv` | {len(b06[b06['period']=='Research_2015_2024'])} |
| `python_expected_b06_vis_precalm_oos.csv` | {len(b06[b06['period']=='OOS_2025_2026'])} |
| `python_expected_b07_dts_all.csv` | {len(b07)} |
| `python_expected_b07_dts_research.csv` | {len(b07[b07['period']=='Research_2015_2024'])} |
| `python_expected_b07_dts_oos.csv` | {len(b07[b07['period']=='OOS_2025_2026'])} |

## 手順

### Step 0 — タイムゾーン

1. Python `signal_time` は CSV の **UTC 相当**（indexそのまま）。
2. TV 表示が JST なら **+9h** を1件で確認してから全件照合。

### Step 1 — B06 スモーク（USDJPY）

1. USDJPY H4 に B06 Pine を貼る。
2. 戦略名 **CURRENT_PRECALM_SHELF6_RR15** 相当の設定にする。
3. `by_symbol/b06_usdjpy.csv` の **signal_time** をすべて目視一致。
4. 一致後 `stop` / `target`（signal close 基準 RR1.5）を確認。

### Step 2 — B06 全銘柄（{len(b06)}件）

1. USDJPY / EURJPY / GBPJPY / AUDJPY（XAU・CHF・SIL は系統B対象外）
2. `parity_log_b06_filled.csv` に `tv_match` = OK / MISS / OFFSET / DATA

### Step 3 — B07（{len(b07)}件）

1. `selected_CURRENT_A30_180_SIGADX30` 設定（trap age 30–180、SIG ADX≤30）
2. `by_symbol/b07_*.csv` と照合
3. B06 と **同一 signal_time** の行は、運用上 B06 優先（B07は見送り可）

## 一致判定

| 項目 | 許容 |
|------|------|
| signal_time | **完全一致**（TZ補正後） |
| entry_time | signal の **次の H4 足**（next_open） |
| stop / target | ±0.5 pip または ±0.01% |
| 件数 | B06={len(b06)} / B07={len(b07)} |

## 採用ゲート

- B06: **{len(b06)}/{len(b06)}** signal match → 0.25R フォワード 30件
- B07: **{len(b07)}/{len(b07)}** signal match → 同上
- 両方完了後に `portfolio_slots.yaml` の `pine_ready` を `yes` に更新（手動）

## 再現

```bash
python3 scripts/export_system_b_pine_parity.py
```
"""
    (OUT / "tradingview_parity_checklist.md").write_text(text, encoding="utf-8")


def write_report(b06: pd.DataFrame, b07: pd.DataFrame, summaries: pd.DataFrame) -> None:
    overlap = 0
    for _, r6 in b06.iterrows():
        m = (b07["symbol"] == r6["symbol"]) & (b07["signal_time"] == r6["signal_time"])
        overlap += int(m.sum())

    lines = [
        "# 系統B B06/B07 Pine parity エクスポート",
        "",
        "作成日: 2026-06-01",
        "",
        "## サマリー",
        "",
        "| case | trades | win_rate% | total_r | pf |",
        "|------|--------|-----------|---------|-----|",
    ]
    for _, row in summaries.iterrows():
        lines.append(
            f"| {row['case']} | {row['trades']} | {row['win_rate_pct']} | {row['total_r']} | {row['pf']} |"
        )
    lines.extend(
        [
            "",
            f"- B06↔B07 同一 signal_time ペア: **{overlap}**（運用では B06 優先）",
            "",
            "## 運用",
            "",
            "- 照合完了まで `risk_r=0.25` のみ",
            "- 台帳: `docs/operations/system_b/system_b_forward_trade_log.csv`",
            "",
        ]
    )
    (OUT / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "by_symbol").mkdir(exist_ok=True)

    vis = pd.read_csv(VIS_CSV, parse_dates=["signal_time", "entry_time", "exit_time"])
    vis = vis[vis["strategy"].eq(VIS_STRATEGY) & vis["symbol"].isin(VIS_SYMBOLS)]
    b06 = slim_vis(vis)

    dts = pd.read_csv(DTS_CSV, parse_dates=["signal_time", "entry_time", "exit_time"])
    dts = dts[dts["strategy"].eq(DTS_STRATEGY)]
    b07 = slim_dts(dts)

    b06.to_csv(OUT / "python_expected_b06_vis_precalm_all.csv", index=False)
    b06[b06["period"] == "Research_2015_2024"].to_csv(
        OUT / "python_expected_b06_vis_precalm_research.csv", index=False
    )
    b06[b06["period"] == "OOS_2025_2026"].to_csv(
        OUT / "python_expected_b06_vis_precalm_oos.csv", index=False
    )

    b07.to_csv(OUT / "python_expected_b07_dts_all.csv", index=False)
    b07[b07["period"] == "Research_2015_2024"].to_csv(
        OUT / "python_expected_b07_dts_research.csv", index=False
    )
    b07[b07["period"] == "OOS_2025_2026"].to_csv(
        OUT / "python_expected_b07_dts_oos.csv", index=False
    )

    for sym in sorted(b06["symbol"].unique()):
        b06[b06["symbol"] == sym].to_csv(OUT / f"by_symbol/b06_{sym.lower()}.csv", index=False)
    for sym in sorted(b07["symbol"].unique()):
        b07[b07["symbol"] == sym].to_csv(OUT / f"by_symbol/b07_{sym.lower()}.csv", index=False)

    b06.to_csv(OUT / "parity_log_b06_template.csv", index=False)
    b07.to_csv(OUT / "parity_log_b07_template.csv", index=False)

    rows = [
        summary("B06_all", b06),
        summary("B06_research", b06[b06["period"] == "Research_2015_2024"]),
        summary("B06_oos", b06[b06["period"] == "OOS_2025_2026"]),
        summary("B07_all", b07),
        summary("B07_research", b07[b07["period"] == "Research_2015_2024"]),
        summary("B07_oos", b07[b07["period"] == "OOS_2025_2026"]),
    ]
    summaries = pd.DataFrame(rows)
    summaries.to_csv(OUT / "export_summary.csv", index=False)

    write_checklist(b06, b07)
    write_report(b06, b07, summaries)
    print(f"Wrote {OUT}")
    print(summaries.to_string(index=False))


if __name__ == "__main__":
    main()

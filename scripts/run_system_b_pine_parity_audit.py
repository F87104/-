#!/usr/bin/env python3
"""
Re-run Python B06/B07 specs and verify parity export CSVs.
Writes TV smoke guides and pre-filled parity logs (tv_match=pending).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELLIOTT = ROOT / "backtests" / "elliott_fibo"
sys.path.insert(0, str(ELLIOTT))

from run_h4_v_initial_shelf_deep_dive import (  # noqa: E402
    CURRENT_SPEC,
    prepare_data,
    run_spec,
)

CHOSEN_DTS = (
    ELLIOTT / "results_2026_05_30/d1_trap_h4_shelf_integrated/chosen_trades.csv"
)

OUT = ROOT / "docs/research/system_b_pine_parity_2026-06-01"
EXPORT_VIS = OUT / "python_expected_b06_vis_precalm_all.csv"
EXPORT_DTS = OUT / "python_expected_b07_dts_all.csv"

VIS_SYMBOLS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
DTS_STRATEGY = "selected_CURRENT_A30_180_SIGADX30"

PINE_PRESET = {
    "B06": {
        "file": "pine/research/h4_v_initial_shelf_breakout_strategy.pine",
        "chart": "H4",
        "symbol_filter": "4通貨のみ",
        "tp_basis": "Signal基準(36d90e6再現)",
        "require_h4": True,
        "date_filter": True,
        "skip_holiday": True,
        "rr": 1.5,
        "shelf_bars": 6,
        "use_pre_calm": True,
    },
    "B07": {
        "file": "pine/research/d1_trap_h4_shelf_strict_strategy.pine",
        "chart": "H4",
        "strategy": DTS_STRATEGY,
        "tp_basis": "Entry基準",
        "trap_age_min": 30,
        "trap_age_max": 180,
        "signal_adx_max": 30,
    },
}


def load_export(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["signal_time", "entry_time", "exit_time"])
    return df


def rerun_b06() -> pd.DataFrame:
    data, pivots = prepare_data()
    return run_spec(data, pivots, CURRENT_SPEC, VIS_SYMBOLS)


def source_b07() -> pd.DataFrame:
    df = pd.read_csv(CHOSEN_DTS, parse_dates=["signal_time", "entry_time", "exit_time"])
    return df[df["strategy"].eq(DTS_STRATEGY)].copy()


def compare_keys(expected: pd.DataFrame, fresh: pd.DataFrame, strategy_col: str) -> pd.DataFrame:
    e = expected.copy()
    f = fresh.copy()
    e["key"] = e["symbol"].astype(str) + "|" + pd.to_datetime(e["signal_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    f["key"] = f["symbol"].astype(str) + "|" + pd.to_datetime(f["signal_time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    e_keys = set(e["key"])
    f_keys = set(f["key"])
    rows = []
    for k in sorted(e_keys | f_keys):
        rows.append(
            {
                "key": k,
                "in_export": k in e_keys,
                "in_rerun": k in f_keys,
                "match": k in e_keys and k in f_keys,
            }
        )
    return pd.DataFrame(rows)


def smoke_md(lane: str, sym: str, df: pd.DataFrame, preset: dict) -> str:
    sub = df[df["symbol"] == sym].sort_values("signal_time")
    lines = [
        f"# {lane} — {sym} TVスモーク照合",
        "",
        f"件数: **{len(sub)}**（Python期待値）",
        "",
        "## Pine 必須設定",
        "",
    ]
    for k, v in preset.items():
        if k != "file":
            lines.append(f"- **{k}:** `{v}`")
    lines.append(f"- **Pineファイル:** `{preset['file']}`")
    lines.extend(
        [
            "",
            "## 照合手順",
            "",
            "1. TVで H4・シンボルを合わせる",
            "2. 下表の `signal_time`（UTC相当）にラベル「棚B」があるか",
            "3. JST表示なら +9h で同じバーを指すか1件目で確認",
            "4. 一致したら `stop` / `target` をラベル表示値と比較",
            "5. `parity_log_*_filled.csv` の `tv_match` を OK / MISS / OFFSET / DATA に更新",
            "",
            "## 期待シグナル一覧",
            "",
            "| # | period | signal_time (UTC) | entry_time | signal_close | stop | target | r |",
            "|---|--------|-------------------|------------|--------------|------|--------|---|",
        ]
    )
    for i, row in sub.iterrows():
        lines.append(
            f"| {row.get('trade_id', i)} | {row['period']} | {row['signal_time']} | "
            f"{row['entry_time']} | {row['signal_close']} | {row['stop']} | {row['target']} | "
            f"{row['r_after_cost']} |"
        )
    if len(sub) >= 1:
        first = sub.iloc[0]
        lines.extend(
            [
                "",
                "## 最初の1件（TZ確認用）",
                "",
                f"- signal_time: `{first['signal_time']}`",
                f"- TVがJSTなら表示目安: `{pd.Timestamp(first['signal_time']) + pd.Timedelta(hours=9)}`（要1件目視確認）",
                f"- entry_time: `{first['entry_time']}`（次のH4始値）",
            ]
        )
    return "\n".join(lines)


def init_parity_log(expected: pd.DataFrame, lane: str) -> pd.DataFrame:
    out = expected.copy()
    out["tv_match"] = "pending"
    out["tv_notes"] = "TV照合待ち — scripts/run_system_b_pine_parity_audit.py"
    out["pine_preset"] = lane
    return out


def write_pine_settings() -> None:
    lines = [
        "# 系統B Pine 照合 — 必須プリセット",
        "",
        "Python CSV を正とする。**件数・signal_time が一致するまでストラテジー成績は使わない。**",
        "",
        "## B06 VIS PRECALM",
        "",
        "| 入力 | 値 |",
        "|------|-----|",
        "| チャート | H4 |",
        "| 銘柄フィルタ | 4通貨のみ |",
        "| H4のみ | ON |",
        "| 2015〜2026 | ON |",
        "| 12/15〜1/10停止 | ON |",
        "| **TP計算** | **Signal基準(36d90e6再現)** ← CSVのtargetと一致 |",
        "| TP RR | 1.5 |",
        "| 棚の本数 | 6 |",
        "| V前PRECALM | ON |",
        "",
        "## B07 DTS SIGADX30",
        "",
        "| 入力 | 値 |",
        "|------|-----|",
        "| チャート | H4 |",
        "| 戦略 | selected_CURRENT_A30_180_SIGADX30 相当 |",
        "| Trap age | 30–180 日 |",
        "| Signal ADX max | 30 |",
        "| **TP計算** | **Entry基準** ← chosen_trades の target |",
        "| TP RR | 1.5 |",
        "",
        "## B06↔B07 重複",
        "",
        "同一 signal_time が9ペア。運用では B06 優先（B07はログで suppressed 可）。",
    ]
    (OUT / "pine_required_settings.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    exp_b06 = load_export(EXPORT_VIS)
    exp_b07 = load_export(EXPORT_DTS)

    print("Re-running B06 Python spec...")
    fresh_b06 = rerun_b06()
    fresh_b06 = fresh_b06[fresh_b06["strategy"].eq(CURRENT_SPEC.name)]
    cmp_b06 = compare_keys(exp_b06, fresh_b06, "strategy")
    cmp_b06.to_csv(OUT / "python_rerun_diff_b06.csv", index=False)

    print("Loading B07 chosen_trades source...")
    fresh_b07 = source_b07()
    cmp_b07 = compare_keys(exp_b07, fresh_b07, "strategy")
    cmp_b07.to_csv(OUT / "python_rerun_diff_b07.csv", index=False)

    b06_ok = cmp_b06["match"].all() and len(cmp_b06) == len(exp_b06)
    b07_ok = cmp_b07["match"].all() and len(cmp_b07) == len(exp_b07)

    overlap = exp_b06.merge(
        exp_b07,
        on=["symbol", "signal_time"],
        how="inner",
        suffixes=("_b06", "_b07"),
    )
    overlap.to_csv(OUT / "overlap_b06_b07_signal_times.csv", index=False)

    init_parity_log(exp_b06, "B06").to_csv(OUT / "parity_log_b06_filled.csv", index=False)
    init_parity_log(exp_b07, "B07").to_csv(OUT / "parity_log_b07_filled.csv", index=False)

    exp_b06[exp_b06["symbol"] == "USDJPY"].head(3).to_csv(OUT / "usdjpy_b06_first3.csv", index=False)

    (OUT / "usdjpy_b06_smoke.md").write_text(
        smoke_md("B06 VIS", "USDJPY", exp_b06, PINE_PRESET["B06"]),
        encoding="utf-8",
    )
    (OUT / "usdjpy_b07_smoke.md").write_text(
        smoke_md("B07 DTS", "USDJPY", exp_b07, PINE_PRESET["B07"]),
        encoding="utf-8",
    )
    write_pine_settings()

    report = [
        "# 系統B Pine parity 監査（Python再実行）",
        "",
        f"- B06 export vs rerun: **{'OK' if b06_ok else 'MISMATCH'}** ({len(exp_b06)} vs {len(fresh_b06)} keys)",
        f"- B07 export vs rerun: **{'OK' if b07_ok else 'MISMATCH'}** ({len(exp_b07)} vs {len(fresh_b07)} keys)",
        f"- B06↔B07 同一 signal_time: **{len(overlap)}**",
        "",
        "## 次（TradingView）",
        "",
        "1. [pine_required_settings.md](pine_required_settings.md) の TP設定を必ず適用",
        "2. [usdjpy_b06_smoke.md](usdjpy_b06_smoke.md) — 13件",
        "3. [usdjpy_b07_smoke.md](usdjpy_b07_smoke.md) — 2件（B06と重複するOOSのみ）",
        "4. 全件完了後 `parity_log_b06_filled.csv` の tv_match を更新",
        "",
    ]
    if not b06_ok:
        miss = cmp_b06[~cmp_b06["match"]]
        report.append("### B06 diff keys")
        report.append("```")
        report.append(miss.to_string(index=False))
        report.append("```")
    (OUT / "audit_report_ja.md").write_text("\n".join(report), encoding="utf-8")

    print(report[2])
    print(report[3])
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

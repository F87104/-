#!/usr/bin/env python3
"""
results_tv_h4/<SYMBOL>/ の各サマリーから、銘柄横断の比較表を生成する。
出力: docs/research/Synapse_TV_H4検証_横断比較.md
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
RES = THIS_DIR / "results_tv_h4"
OUT = REPO_ROOT / "docs" / "research" / "Synapse_TV_H4検証_横断比較.md"

SYMBOL_ORDER = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "XAUUSD", "XAGUSD", "NAS100"]


def fmt(x) -> str:
    return "" if pd.isna(x) else f"{x:.2f}"


def best_ihs(symbol: str) -> dict | None:
    f = RES / symbol / "summary_by_structure.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    d = d[(d["structure"] == "ihs_5pivot") & (d["filter"].isin(["context", "diag_break"]))]
    d = d[d["trades"] >= 20]
    if d.empty:
        return None
    row = d.sort_values("total_r", ascending=False).iloc[0]
    return row.to_dict()


def oos_row(symbol: str, filt: str, tp: str) -> dict | None:
    f = RES / symbol / "summary_by_oos.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    d = d[(d["filter"] == filt) & (d["target_model"] == tp)]
    out = {}
    for _, r in d.iterrows():
        key = "oos" if bool(r["is_oos"]) else "is"
        out[key] = r.to_dict()
    return out or None


def main() -> None:
    best_rows = []
    oos_rows = []
    for sym in SYMBOL_ORDER:
        b = best_ihs(sym)
        if not b:
            continue
        best_rows.append(
            f"| {sym} | {b['filter']} | {b['target_model']} | {int(b['trades'])} | "
            f"{fmt(b['win_rate'])} | {fmt(b['total_r'])} | {fmt(b['pf'])} | {fmt(b['max_dd_r'])} |"
        )
        oo = oos_row(sym, b["filter"], b["target_model"])
        if oo:
            isr = oo.get("is", {})
            osr = oo.get("oos", {})
            oos_rows.append(
                f"| {sym} | {b['filter']}+{b['target_model']} | "
                f"{int(isr.get('trades', 0))} | {fmt(isr.get('pf'))} | {fmt(isr.get('total_r'))} | "
                f"{int(osr.get('trades', 0))} | {fmt(osr.get('pf'))} | {fmt(osr.get('total_r'))} |"
            )

    lines = [
        "# Synapse TradingView H4 検証 — 銘柄横断比較",
        "",
        "> `run_synapse_tv_h4.py` の出力（`results_tv_h4/`）から自動生成。",
        "> 構造は **ihs_5pivot**（最良構造）に固定し、フィルタは context / diag_break のうち",
        "> total_r 最良（trades ≥ 20）を採用。コストは銘柄別に概算設定済み。",
        "",
        "## 1. 銘柄ごとの最良構成（ihs_5pivot）",
        "",
        "| 銘柄 | フィルタ | TP | 件数 | 勝率 | 合計R | PF | 最大DD |",
        "|---|---|---|---:|---:|---:|---:|---:|",
        *best_rows,
        "",
        "## 2. IS（2014-2024）vs OOS（2025-）",
        "",
        "| 銘柄 | 構成 | IS件数 | IS PF | IS R | OOS件数 | OOS PF | OOS R |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        *oos_rows,
        "",
        "## 3. 所感（8銘柄検証時点）",
        "",
        "- 通貨ごとに最適フィルタ/TPが異なる（v2.1マトリクスと同じく**銘柄別最適化**が必要）。",
        "- **採用候補（ihs_5pivot でプラス）**: GBPJPY(PF2.08) / NAS100(PF1.48) / EURJPY(PF1.28) /",
        "  AUDJPY(PF1.20) / USDJPY(PF1.19) / XAUUSD(PF1.17) / CHFJPY(PF1.15)。",
        "- **NAS100 は Synapse と好相性**（diag_break 1.5R で PF1.48・勝率55%・DD3.7Rと優秀）。",
        "- **XAGUSD は ihs_5pivot ではマイナス**（PF0.93）。銀はこの構造を使わない、",
        "  または別構造（all構造では context 2R が PF1.23）で再検討する。",
        "- フィルタ傾向: GBPJPY/EURJPY/NAS100/XAUUSD/CHFJPY は **diag_break**、",
        "  USDJPY/AUDJPY は **context** が良い。",
        "- 貴金属（XAUUSD）は total_r は出るが DD が大きい（21R）→ ロット調整前提。",
        "",
        "## 4. 残タスク",
        "",
        "- [ ] XAGUSD の別構造（classic_6pivot / role_ab_5pivot）での再検証",
        "- [ ] 精度向上フィルタ（ADX下限 / 調整時間 / 実体比率）のグリッド追加",
        "- [ ] 採用候補のTradingView目視確認（人が見て納得できる位置に出るか）",
        "- [ ] H4で機能した銘柄をH1へ落とせるか検証",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"書き出し: {OUT}")
    print("\n".join(best_rows))


if __name__ == "__main__":
    main()

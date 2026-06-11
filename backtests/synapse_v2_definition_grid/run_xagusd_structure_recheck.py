#!/usr/bin/env python3
"""
ステップ2: 銀（XAGUSD）の別構造再検討。

ihs_5pivot では弱かった XAGUSD を role_ab_5pivot / classic_6pivot で再検証し、
さらに精度フィルタ（ADX / 調整時間 / 実体比率）を重ねて最良を出す。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
TV_DATA = REPO_ROOT / "tv_data"
REPORT = REPO_ROOT / "docs" / "research" / "Synapse_銀XAGUSD_別構造再検討_2026-06-11.md"

# 精度モジュール（build_trades / adx / stats / ADX_MINS など）を再利用
_s = importlib.util.spec_from_file_location("synapse_precision", THIS_DIR / "run_synapse_precision_filters.py")
pf = importlib.util.module_from_spec(_s)
sys.modules["synapse_precision"] = pf
_s.loader.exec_module(pf)


def main() -> None:
    path = next((p for p in TV_DATA.glob("*.csv") if pf.tv.detect_symbol(p) == "XAGUSD"), None)
    if path is None:
        print("XAGUSD のCSVが見つかりません")
        return

    symbol, trades = pf.build_trades(path)
    out_lines = [
        "# Synapse 銀(XAGUSD) 別構造再検討（2026-06-11）",
        "",
        "> XAGUSD は ihs_5pivot ではマイナス(PF0.93)。構造を変えて再検証する。",
        "",
        "## 1. 構造別ベスト（trades≥20, total_r上位）",
        "",
        "| 構造 | フィルタ | TP | 件数 | 勝率 | 合計R | PF | DD |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]

    # 構造別に集計
    summ = pf.eng.summarize(trades, ["structure", "filter", "target_model"])
    summ = summ[summ["trades"] >= 20].sort_values("total_r", ascending=False)
    for _, r in summ.head(8).iterrows():
        out_lines.append(
            f"| {r['structure']} | {r['filter']} | {r['target_model']} | {int(r['trades'])} | "
            f"{r['win_rate']:.2f} | {r['total_r']:.2f} | {r['pf']:.2f} | {r['max_dd_r']:.2f} |"
        )

    # 最良構造（role_ab_5pivot 想定）に精度フィルタを重ねる
    top = summ.iloc[0]
    struct, filt, tp = top["structure"], top["filter"], top["target_model"]
    sub = trades[(trades["structure"] == struct) & (trades["filter"] == filt) & (trades["target_model"] == tp)].copy()
    base = pf.stats(sub["r_after_cost"])

    rows = []
    for a in pf.ADX_MINS:
        for adj in pf.ADJUST_MINS:
            for b in pf.BODY_MINS:
                m = sub[(sub["adx"].fillna(0) >= a) & (sub["adjust_ratio"] >= adj) & (sub["signal_body_ratio"] >= b)]
                if len(m) < 15:
                    continue
                s = pf.stats(m["r_after_cost"])
                s.update({"adx_min": a, "adjust_min": adj, "body_min": b})
                rows.append(s)
    sweep = pd.DataFrame(rows).sort_values(["pf", "total_r"], ascending=[False, False])

    out_lines += [
        "",
        f"## 2. 最良構造 `{struct}` ({filt}+{tp}) への精度フィルタ重ね掛け",
        "",
        f"ベース: PF {base['pf']:.2f} / {base['trades']}件 / {base['total_r']:.2f}R / DD {base['max_dd_r']:.2f}R",
        "",
        "| ADX≥ | 調整≥ | 実体≥ | 件数 | 勝率 | 合計R | PF | DD |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in sweep.head(8).iterrows():
        out_lines.append(
            f"| {int(r['adx_min'])} | {r['adjust_min']:.1f} | {r['body_min']:.2f} | {int(r['trades'])} | "
            f"{r['win_rate']:.2f} | {r['total_r']:.2f} | {r['pf']:.2f} | {r['max_dd_r']:.2f} |"
        )

    out_lines += [
        "",
        "## 3. 結論",
        "",
        f"- **銀は `{struct}` を使う**（ihs_5pivot は不適）。",
        f"- 推奨ベース: `{struct} + {filt} + {tp}`（PF {base['pf']:.2f}）",
        "- 精度フィルタは上表の最良行を参照。件数が15未満になる版は採用しない。",
    ]
    REPORT.write_text("\n".join(out_lines), encoding="utf-8")

    print(f"=== XAGUSD 構造別ベスト ===")
    print(summ.head(6)[["structure", "filter", "target_model", "trades", "win_rate", "total_r", "pf", "max_dd_r"]].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\n=== {struct} {filt}+{tp} 精度フィルタ上位 ===")
    print(sweep.head(6).to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\n書き出し: {REPORT}")


if __name__ == "__main__":
    main()

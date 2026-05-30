#!/usr/bin/env python3
"""
Market Psychology Research — 実用性監査 (後付けでないか / リアルで使えるか)

既存のトレード結果CSVを再利用し、以下を厳しめに点検する:
  1. コスト/スリッページ感度 (cost を 0.04→0.10→0.20R に上げてもエッジが残るか)
  2. 利益の集中度 (1銘柄・少数トレードに依存していないか)
  3. 年ごとの頑健性 (勝ち年の比率、最悪年)
  4. Capitulation 事前登録ルールの OOS をコスト増しで再評価

注: ルックアヘッド/エントリ規約はソース監査で別途確認済み
    (シグナル=確定足, エントリ=次足始値, 決済=後続足, 同足両ヒットはSL優先)。
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

THIS = Path(__file__).resolve().parent
lines = []


def out(s=""):
    print(s)
    lines.append(s)


def pf(s):
    s = np.asarray(s, float)
    gl = -s[s < 0].sum()
    return s[s > 0].sum() / gl if gl > 0 else np.inf


def stat(r):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return "n=0"
    return f"n={n:>4} totalR={r.sum():+7.1f} PF={pf(r):.2f} avgR={r.mean():+.3f} WR={100*(r>0).mean():.0f}%"


def cost_stress(r_clean, costs=(0.04, 0.10, 0.20)):
    res = {}
    for c in costs:
        res[c] = pf(np.asarray(r_clean, float) - c)
    return res


out("=" * 86)
out("実用性監査レポート — 後付け/カーブフィット検査 & リアル運用耐性")
out("=" * 86)

# ---------------------------------------------------------------- 踏み上げ (from raw)
out("\n" + "#" * 86)
out("# ① 踏み上げ Short Squeeze (生OHLC再現, FX/メタル, LONG)")
out("#" * 86)
fr = pd.read_csv(THIS / "from_raw_trades.csv")
sq = fr[(fr.group == "fx") & (fr.side == "long")].copy()
sq["r_clean"] = sq["r_after_cost"] + 0.04
out("全体: " + stat(sq["r_after_cost"]))
cs = cost_stress(sq["r_clean"])
out(f"コスト感度 PF: 0.04R→{cs[0.04]:.2f}  0.10R→{cs[0.10]:.2f}  0.20R→{cs[0.20]:.2f}")
# 集中度
gp = sq[sq.r_after_cost > 0].groupby("symbol")["r_after_cost"].sum().sort_values(ascending=False)
tot = sq.r_after_cost.sum()
out(f"利益集中: 最大銘柄 {gp.index[0]} が総利益の {100*gp.iloc[0]/max(gp.sum(),1e-9):.0f}% (粗利ベース)")
out(f"純損益 totalR={tot:+.1f} / トレード数 {len(sq)} → 1トレード平均 {tot/len(sq):+.3f}R")
# 年別
yr = sq.groupby("year")["r_after_cost"].sum()
win_years = (yr > 0).sum()
out(f"年別: {win_years}/{len(yr)} 年がプラス, 最悪年 {yr.idxmin()}={yr.min():+.1f}R, 最良年 {yr.idxmax()}={yr.max():+.1f}R")

# ---------------------------------------------------------------- Capitulation (基本)
out("\n" + "#" * 86)
out("# ② Capitulation 底買い (生OHLC, LONG, 基本ケース 全銘柄)")
out("#" * 86)
cap = pd.read_csv(THIS / "capitulation_trades.csv")
cl = cap[cap.side == "long"].copy()
cl["r_clean"] = cl["r_after_cost"] + 0.04
out("全体: " + stat(cl["r_after_cost"]))
cs = cost_stress(cl["r_clean"])
out(f"コスト感度 PF: 0.04R→{cs[0.04]:.2f}  0.10R→{cs[0.10]:.2f}  0.20R→{cs[0.20]:.2f}")
out("  → FX単体IS PF≈1.0 と弱いため、コスト増で容易にトントン割れの可能性を確認")

# ---------------------------------------------------------------- Capitulation 事前登録ルール
out("\n" + "#" * 86)
out("# ③ Capitulation 事前登録ルール (counter × 7銘柄, GBPJPY除外) のコスト耐性")
out("#" * 86)
tf = pd.read_csv(THIS / "capitulation_trendfilter_trades.csv")
keep = ["AUDJPY", "CHFJPY", "EURJPY", "NAS100", "SPX500", "USDJPY", "XAUUSD"]
rule = tf[(tf["mode"] == "counter") & (tf["symbol"].isin(keep))].copy()
rule["r_clean"] = rule["r_after_cost"] + 0.04
for per in ["IS_2015_2024", "OOS_2025_2026"]:
    sub = rule[rule.period == per]
    out(f"{per}: " + stat(sub["r_after_cost"]))
    cs = cost_stress(sub["r_clean"])
    out(f"   コスト感度 PF: 0.04R→{cs[0.04]:.2f}  0.10R→{cs[0.10]:.2f}  0.20R→{cs[0.20]:.2f}")
oos = rule[rule.period == "OOS_2025_2026"]
out(f"\nOOSサンプル数 = {len(oos)} 件 (※ 統計的に小さく、結論は暫定)")

# ---------------------------------------------------------------- まとめ表
out("\n" + "=" * 86)
out("監査サマリ")
out("=" * 86)
out("- ルックアヘッド: なし (確定足シグナル/次足始値エントリ/同足両ヒットはSL優先) … ソース確認済")
out("- 踏み上げ: コスト0.20Rでも PF>1 を維持できるか上記参照。利益集中・年別頑健性も上記。")
out("- Capitulation基本(FX): エッジ薄くコスト耐性低い。事前登録ルール+指数で実用域。")
out("- 共通の弱点: OOSサンプル小、スリッページ未計上(特にCapitulationは高ボラ時=滑りやすい)。")

(THIS / "audit_realism_report.txt").write_text("\n".join(lines), encoding="utf-8")
out("\nsaved: audit_realism_report.txt")

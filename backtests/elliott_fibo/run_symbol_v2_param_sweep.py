#!/usr/bin/env python3
"""
任意銘柄の v2 パラメータスイープ（汎用版）

NAS100スイープ(run_nas100_v2_param_sweep.py)の高速ベクトル化ロジックを再利用し、
コマンドラインで指定した銘柄に対して Squeeze/Capitulation/LL のパラメータを総当たり。

使い方:
  python3 backtests/elliott_fibo/run_symbol_v2_param_sweep.py XAUUSD
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]

_s = importlib.util.spec_from_file_location("nas_sweep", THIS_DIR / "run_nas100_v2_param_sweep.py")
nas = importlib.util.module_from_spec(_s)
sys.modules["nas_sweep"] = nas
_s.loader.exec_module(nas)

MIN_TRADES = nas.MIN_TRADES
PF_SHOW = nas.PF_SHOW


def main():
    if len(sys.argv) < 2:
        print("使い方: run_symbol_v2_param_sweep.py <SYMBOL>")
        return
    symbol = sys.argv[1].upper()
    path = next((p for p in nas.v2.tv.TV_DATA.glob("*.csv") if nas.v2.tv.detect_symbol(p) == symbol), None)
    if path is None:
        print(f"{symbol} のCSVが tv_data に見つかりません")
        return

    # 銘柄別コストに切替（simulate_all はモジュールの COST を参照）
    nas.COST = nas.v2.tv.COST_BY_SYMBOL.get(symbol, (0.010, 0.005))

    out = THIS_DIR / "results_tv_v2_matrix" / f"{symbol.lower()}_param_sweep"
    out.mkdir(parents=True, exist_ok=True)
    report = REPO_ROOT / "docs" / "research" / "market_psychology" / f"v2_{symbol}_別パラメータ_2026-06-11.md"

    df = nas.v2.add_features(nas.v2.tv.load_tv_csv(path))
    P = nas.prep(df)
    print(f"{symbol} H4: {len(df)}本  {df.index.min().date()} 〜 {df.index.max().date()}  コスト={nas.COST}")

    sqz = nas.sweep_squeeze(df, P)
    cap = nas.sweep_capitulation(df, P)
    ll = nas.sweep_ll(df, P)
    sqz.to_csv(out / "squeeze_sweep.csv", index=False)
    cap.to_csv(out / "capitulation_sweep.csv", index=False)
    ll.to_csv(out / "ll_sweep.csv", index=False)

    lines = [
        f"# {symbol} v2 別パラメータ検証（2026-06-11）",
        "",
        f"> {symbol} を v2 標準パラメータで動かすとシグナルが少ないため、専用に総当たり。",
        f"> `run_symbol_v2_param_sweep.py {symbol}` の出力。表示は 件数≥{MIN_TRADES} & PF≥{PF_SHOW} 優先。",
        "",
        f"対象: {symbol} H4 {len(df)}本（{df.index.min().date()} 〜 {df.index.max().date()}）",
        "",
        "## Squeeze（ロング）上位",
        "",
        *nas.top_table(sqz, ["shelf_bars", "drop_win", "shelf_atr", "move_atr", "rr"]),
        "## Capitulation（ロング）上位",
        "",
        *nas.top_table(cap, ["decline_bars", "drop_atr_cap", "spike_atr", "use_down_d1", "rr"]),
        "## Long Liquidation（ショート）上位",
        "",
        *nas.top_table(ll, ["shelf_bars", "drop_win", "shelf_atr", "move_atr", "rr"]),
    ]
    report.write_text("\n".join(lines), encoding="utf-8")

    for name, d, cols in [
        ("Squeeze", sqz, ["shelf_bars", "drop_win", "shelf_atr", "move_atr", "rr"]),
        ("Capitulation", cap, ["decline_bars", "drop_atr_cap", "spike_atr", "use_down_d1", "rr"]),
        ("LongLiquidation", ll, ["shelf_bars", "drop_win", "shelf_atr", "move_atr", "rr"]),
    ]:
        print(f"\n=== {name} （件数≥{MIN_TRADES}, PF順）===")
        if d.empty:
            print("  候補なし")
            continue
        dd = d[d["trades"] >= MIN_TRADES].sort_values("pf", ascending=False)
        if dd.empty:
            print(f"  件数≥{MIN_TRADES} なし（最大 {int(d['trades'].max())}件）")
            continue
        print(dd.head(6)[cols + ["trades", "win_rate", "total_r", "pf", "max_dd_r"]].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\n書き出し: {report}")


if __name__ == "__main__":
    main()

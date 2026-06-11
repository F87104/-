#!/usr/bin/env python3
"""
Synapse H4 verification on TradingView data.

既存の run_synapse_definition_grid.py のSynapseエンジン（pivot検出 / A/B構造 /
フィルタ / バックテスト）をそのまま再利用し、データソースだけを
tv_data/ に置いた TradingView H4 CSV に差し替えて検証する。

- 対象: tv_data/*.csv （H4。time,open,high,low,close 形式）
- 上位足コンテキスト: H4から日足(D1)を自動生成して付与（精度向上フィルタ）
- 出力: results_tv_h4/<SYMBOL>/ に trades.csv と各サマリーCSV、stdoutに要約

使い方:
  python3 backtests/synapse_v2_definition_grid/run_synapse_tv_h4.py            # tv_data内の全銘柄
  python3 backtests/synapse_v2_definition_grid/run_synapse_tv_h4.py USDJPY     # 銘柄指定
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
TV_DATA = REPO_ROOT / "tv_data"
OUT_ROOT = THIS_DIR / "results_tv_h4"

# --- 既存Synapseエンジンを動的import（ファイル名にスペースが無いので安全） ---
_spec = importlib.util.spec_from_file_location(
    "synapse_engine", THIS_DIR / "run_synapse_definition_grid.py"
)
eng = importlib.util.module_from_spec(_spec)
sys.modules["synapse_engine"] = eng
_spec.loader.exec_module(eng)

KNOWN_SYMBOLS = [
    "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY",
    "XAUUSD", "XAGUSD", "NAS100", "US100", "NDX",
]

# 銘柄ごとの概算コスト（スプレッド/スリッページ、価格絶対値）
# JPYクロスは約1pip、貴金属/指数は価格スケールに合わせて調整。
COST_BY_SYMBOL = {
    "USDJPY": (0.010, 0.005),
    "EURJPY": (0.012, 0.006),
    "GBPJPY": (0.016, 0.008),
    "AUDJPY": (0.012, 0.006),
    "CHFJPY": (0.014, 0.007),
    "XAUUSD": (0.30, 0.15),
    "XAGUSD": (0.020, 0.010),
    "NAS100": (2.0, 1.0),
    "US100": (2.0, 1.0),
    "NDX": (2.0, 1.0),
}


def detect_symbol(path: Path) -> str:
    name = path.stem.upper()
    for sym in KNOWN_SYMBOLS:
        if sym in name:
            return "NAS100" if sym in {"US100", "NDX"} else sym
    return path.stem


def load_tv_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"{path.name}: 必須列 {required} が見つかりません（列: {list(df.columns)}）")

    time_col = df["time"]
    if pd.api.types.is_numeric_dtype(time_col):
        ts = pd.to_datetime(time_col, unit="s", utc=True).dt.tz_localize(None)
    else:
        ts = pd.to_datetime(time_col, utc=True, errors="coerce").dt.tz_localize(None)

    df = df.assign(timestamp=ts).dropna(subset=["timestamp"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["volume"] = 0.0
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    df = df.set_index("timestamp").sort_index()
    df = df.loc[(df.index >= eng.START) & (df.index <= eng.END)]
    return df


def run_symbol(path: Path) -> dict | None:
    symbol = detect_symbol(path)
    raw = load_tv_csv(path)
    if len(raw) < 500:
        print(f"  [skip] {symbol}: データが少なすぎます（{len(raw)}本）")
        return None

    # コスト設定（銘柄別）
    spread, slip = COST_BY_SYMBOL.get(symbol, (0.010, 0.005))
    eng.SPREAD_PRICE = spread
    eng.SLIP_PRICE = slip

    config = eng.TIMEFRAME_CONFIGS["H4"]

    # H4本体に指標付与
    h4 = eng.add_indicators(raw, "H4")

    # 日足コンテキスト（H4 -> D1 リサンプル）を上位足として付与
    d1 = eng.resample_ohlc(raw, "1D")
    d1 = eng.add_indicators(d1, "D1")
    h4 = eng.attach_upper_context(h4, {"D1": d1}, "H4")

    candidates, trades = eng.run_timeframe(h4, "H4", config)
    if trades.empty:
        print(f"  [warn] {symbol}: トレードが生成されませんでした（候補 {len(candidates)} 件）")
        return None

    trades["symbol"] = symbol
    trades["is_oos"] = trades["entry_time"] >= eng.OOS_START

    out_dir = OUT_ROOT / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out_dir / "trades.csv", index=False)

    by_ft = eng.summarize(trades, ["filter", "target_model"])
    by_struct = eng.summarize(trades, ["structure", "filter", "target_model"])
    by_oos = eng.summarize(trades, ["is_oos", "filter", "target_model"])
    overall = eng.summarize(trades, ["symbol"])

    by_ft.to_csv(out_dir / "summary_by_filter_target.csv", index=False)
    by_struct.to_csv(out_dir / "summary_by_structure.csv", index=False)
    by_oos.to_csv(out_dir / "summary_by_oos.csv", index=False)
    overall.to_csv(out_dir / "summary_overall.csv", index=False)

    return {
        "symbol": symbol,
        "bars": len(raw),
        "first": raw.index.min(),
        "last": raw.index.max(),
        "candidates": len(candidates),
        "trades": len(trades),
        "by_ft": by_ft,
        "by_struct": by_struct,
        "by_oos": by_oos,
    }


def print_summary(res: dict) -> None:
    sym = res["symbol"]
    print(f"\n{'='*70}")
    print(f"■ {sym}  期間 {res['first'].date()} 〜 {res['last'].date()}  "
          f"H4 {res['bars']}本 / 候補 {res['candidates']} / トレード {res['trades']}")
    print(f"{'='*70}")

    print("\n【フィルタ × TP】上位（total_r順）")
    cols = ["filter", "target_model", "trades", "win_rate", "total_r", "avg_r", "pf", "max_dd_r"]
    top = res["by_ft"].head(8)[cols]
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(top.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    print("\n【ihs_5pivot 構造の context/diag_break】（本命構成の確認）")
    bs = res["by_struct"]
    focus = bs[(bs["structure"] == "ihs_5pivot")
               & (bs["filter"].isin(["context", "diag_break"]))]
    if not focus.empty:
        fcols = ["structure", "filter", "target_model", "trades", "win_rate", "total_r", "pf", "max_dd_r"]
        print(focus.head(6)[fcols].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    else:
        print("  （該当なし）")

    print("\n【IS vs OOS】context + fixed_2R")
    bo = res["by_oos"]
    sel = bo[(bo["filter"] == "context") & (bo["target_model"] == "fixed_2R")]
    if not sel.empty:
        ocols = ["is_oos", "trades", "win_rate", "total_r", "pf", "max_dd_r"]
        print(sel[ocols].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    else:
        print("  （該当なし）")


def main() -> None:
    args = [a.upper() for a in sys.argv[1:]]
    if not TV_DATA.exists():
        print(f"tv_data フォルダがありません: {TV_DATA}")
        return

    files = sorted(p for p in TV_DATA.glob("*.csv"))
    if args:
        files = [p for p in files if detect_symbol(p) in args]
    if not files:
        print("対象CSVが見つかりません。tv_data/ にH4 CSVを置いてください。")
        return

    print(f"対象ファイル: {[p.name for p in files]}")
    results = []
    for path in files:
        print(f"\n>> 実行中: {path.name}")
        try:
            res = run_symbol(path)
        except Exception as e:  # noqa: BLE001
            print(f"  [error] {path.name}: {e}")
            continue
        if res:
            results.append(res)

    for res in results:
        print_summary(res)

    print(f"\n出力先: {OUT_ROOT}")


if __name__ == "__main__":
    main()

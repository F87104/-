#!/usr/bin/env python3
"""
Export Python expected T5 trades for TradingView Pine parity checks.

Source of truth:
  backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/
  baseline_final_trades_rec120_strict.csv

Two parity phases are exported:
  Phase A (99 / 15): Strict REC1.2 + MACD/BB, guards OFF  -> matches filter_summary BASE
  Phase B (34 / 5):  Practical C125 guards ON             -> matches live Pine defaults
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from run_elliott_fibo_study import markdown_table


THIS_DIR = Path(__file__).resolve().parent
SOURCE = (
    THIS_DIR
    / "results_2025_2026_oos"
    / "t5_failure_filter_validation"
    / "baseline_final_trades_rec120_strict.csv"
)
OUT_DIR = THIS_DIR / "results_2026_06_01" / "t5_pine_parity"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "SILVER"]
RECOMMENDED_6 = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]


def profit_factor(r: pd.Series) -> float:
    wins = float(r[r > 0].sum())
    losses = float(r[r <= 0].sum())
    if losses < 0:
        return wins / abs(losses)
    return math.inf if wins > 0 else math.nan


def practical_guard_mask(df: pd.DataFrame) -> pd.Series:
    weak_rebreak = (df["trigger_type"] == "rebreak") & (
        (df["bb_pos"] > 0.95) | (df["macd_hist_slope3"] <= 0.03)
    )
    return (df["bb_pos"] <= 0.95) & (df["signal_recovery_bars"] <= 16) & ~weak_rebreak


def slim_trades(df: pd.DataFrame, phase: str) -> pd.DataFrame:
    out = df.copy()
    out["trade_id"] = range(1, len(out) + 1)
    out["phase"] = phase
    out["signal_time"] = pd.to_datetime(out["signal_time"])
    out["entry_time"] = pd.to_datetime(out["entry_time"])
    out["exit_time"] = pd.to_datetime(out["exit_time"])
    cols = [
        "trade_id",
        "phase",
        "symbol",
        "period",
        "signal_time",
        "entry_time",
        "trigger_type",
        "signal_close",
        "entry",
        "stop",
        "target",
        "exit_time",
        "exit_reason",
        "r_after_cost",
        "bb_pos",
        "bb_width_atr",
        "macd_hist_slope3",
        "signal_recovery_bars",
        "v_move_atr",
        "v_drop_speed_atr_per_bar",
        "max_recovery_to_drop",
        "candidate",
        "tv_signal_time",
        "tv_entry_time",
        "tv_match",
        "tv_notes",
    ]
    out = out.rename(columns={"close": "signal_close"})
    if "signal_close" not in out.columns:
        out["signal_close"] = out.get("trigger_level", pd.NA)
    for col in cols:
        if col not in out.columns:
            out[col] = pd.NA
    return out[cols].sort_values(["symbol", "signal_time"]).reset_index(drop=True)


def summary_row(name: str, df: pd.DataFrame) -> dict:
    r = df["r_after_cost"].astype(float)
    return {
        "case": name,
        "trades": int(len(df)),
        "win_rate": float((r > 0).mean() * 100.0) if len(r) else math.nan,
        "total_r": float(r.sum()) if len(r) else math.nan,
        "avg_r": float(r.mean()) if len(r) else math.nan,
        "pf": profit_factor(r) if len(r) else math.nan,
        "max_dd_r": float((r.cumsum().cummax() - r.cumsum()).max()) if len(r) else math.nan,
    }


def write_checklist() -> None:
    text = """# H4 T5 + MACD + BB — TradingView Pine Parity Checklist

Python を正とする。TradingView の strategy 成績（PF/勝率）は、**signal_time 一致率 100%** になるまで採用判断に使わない。

## Pine ファイル

- `pine/production/h4_t5_macd_bb_live_ready.pine`

## 照合の2フェーズ

| Phase | Python CSV | 件数 (IS/OOS) | Pine 設定 |
|---|---|---:|---|
| **A: BASE** | `python_expected_base_research_99.csv` | 99 / 15 | `騙し回避フィルタ` = **OFF** |
| **B: LIVE** | `python_expected_practical_research_34.csv` | 34 / 5 | `騙し回避フィルタ` = **ON**（デフォルト） |

共通設定（両フェーズ）:

1. チャート時間足: **H4**
2. `判定時間足`: 240
3. `判定時間足チャートでのみ売買する`: **ON**
4. `MACD + BBプリセット`: **Strict 0.75-1.00 + width<=7**
5. `V字速度プリセット`: **Balanced REC1.2**
6. `12/15〜1/10は新規停止`: **ON**
7. `運用判定 (FULL/HALF/SKIP)`: **OFF**（シグナル件数照合時）
8. `固定数量を使う`: **ON** でも可（件数照合のみなら数量は不問）

## 手順（推奨順）

### Step 0: タイムゾーン合わせ

1. Python の `signal_time` は **CSV index そのまま（UTC 相当）**。
2. TradingView 表示が JST 等なら **+9h 等の固定オフセット** を1件で確認してから全件照合する。
3. 最初の確認用: **USDJPY 2015-03-31** `signal_time=2015-03-31 00:00:00`（`expected_usdjpy_first5.csv` 参照）。

### Step 1: 単通貨スモーク（USDJPY）

1. USDJPY H4 に Pine を貼る。
2. Phase A 設定（ guards OFF ）で 2015–2024 を表示。
3. `expected_usdjpy_all.csv` の **16件** すべてで `signal_time` が一致するか目視。
4. 一致したら `signal_close` / `stop` / `target` を ±数 pip 以内で確認。

### Step 2: 全通貨 Phase A（99件）

1. 7通貨それぞれで `by_symbol/*_base.csv` と照合。
2. 結果を `parity_log_filled.csv` に記録（`tv_match` = OK / MISS / OFFSET / DATA）。

### Step 3: Phase B（live 34件）

1. `騙し回避フィルタ` = ON に戻す。
2. `python_expected_practical_research_34.csv` と照合。
3. ここまで一致すれば live ペーパー開始可。

## 一致判定ルール

| 項目 | 許容 |
|---|---|
| `signal_time` | **完全一致**（TZ 補正後） |
| `entry_time` | signal の **次の H4 足**（Python は次足始値） |
| `trigger_type` | stagnation / rebreak / stagnation+rebreak 一致 |
| `stop` | ±0.5 pip または ±0.01% |
| `target` | シグナル終値基準 RR2.0（Python/Pine 同じ定義） |
| 件数 | Phase A=99, Phase B=34（Research） |

## よくある不一致原因

1. **データ提供元差** — TV と F87104_test の H/L/C 差
2. **Pivot 確定タイミング** — pivotWidth=3 の確定本数
3. **年末年始除外** — 12/15–1/10
4. **Guard ON/OFF 取り違え** — 99件 vs 34件
5. **運用判定 ON** — SKIP/HALF で件数が減る
6. **REC プリセット** — REC1.2 以外を選んでいる

## 出力ファイル

| ファイル | 内容 |
|---|---|
| `python_expected_base_research_99.csv` | Phase A IS 99件 |
| `python_expected_base_oos_15.csv` | Phase A OOS 15件 |
| `python_expected_practical_research_34.csv` | Phase B IS 34件 |
| `parity_log_template.csv` | TV 記入用テンプレ |
| `by_symbol/*.csv` | 通貨別 |
| `report_ja.md` | サマリー |

## 採用ゲート

- Phase A: **99/99 signal match**（DATA差除く）
- Phase B: **34/34 signal match**
- その後: 0.25R フォワード 30件
"""
    (OUT_DIR / "tradingview_parity_checklist.md").write_text(text, encoding="utf-8")


def write_report(
    summaries: pd.DataFrame,
    base_research: pd.DataFrame,
    usdjpy: pd.DataFrame,
) -> None:
    by_symbol = (
        base_research.groupby("symbol", as_index=False)
        .agg(trades=("symbol", "size"), total_r=("r_after_cost", "sum"))
        .sort_values("trades", ascending=False)
    )
    lines = [
        "# H4 T5 Pine Parity Export",
        "",
        "Status: **TradingView 照合待ち**（Python 期待値エクスポート済み）",
        "",
        "## 目的",
        "",
        "Strict REC1.2 + MACD/BB の Python 99件（Research 2015–2024）と、",
        "`h4_t5_macd_bb_live_ready.pine` の **signal_time / entry_time** が一致するか確認する。",
        "",
        "## Python ソース",
        "",
        f"- `{SOURCE.relative_to(THIS_DIR.parents[1])}`",
        "- 設定: Strict_075_100_width7 + max_recovery_to_drop=1.20",
        "",
        "## 期待サマリー",
        "",
        markdown_table(summaries, 20),
        "",
        "## Phase A: BASE 99件 — 通貨別",
        "",
        markdown_table(by_symbol, 20),
        "",
        "## 最初に見る USDJPY（16件）",
        "",
        "件数が中程度で OOS も良好。最初のスモークテスト用。",
        "",
        markdown_table(
            usdjpy[
                [
                    "trade_id",
                    "signal_time",
                    "entry_time",
                    "trigger_type",
                    "signal_close",
                    "stop",
                    "target",
                    "r_after_cost",
                ]
            ].head(8),
            20,
        ),
        "",
        "## Pine 設定（Phase A）",
        "",
        "| 項目 | 値 |",
        "|---|---|",
        "| プリセット Strict + REC1.2 | ON |",
        "| 騙し回避フィルタ | **OFF** |",
        "| 運用判定 FULL/HALF/SKIP | **OFF** |",
        "| 年末年始除外 | ON |",
        "",
        "## 次のアクション",
        "",
        "1. `tradingview_parity_checklist.md` に従い USDJPY から照合",
        "2. `parity_log_template.csv` に TV 結果を記入",
        "3. Phase A 100% 一致 → Phase B（guards ON, 34件）",
        "4. 一致後 `near_main_forward_validation_log.csv` で 0.25R 開始",
        "",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    raw = pd.read_csv(SOURCE)
    raw["signal_time"] = pd.to_datetime(raw["signal_time"])
    raw["entry_time"] = pd.to_datetime(raw["entry_time"])
    raw["exit_time"] = pd.to_datetime(raw["exit_time"])

    research = raw[raw["period"].eq("Research_2015_2024")].copy()
    oos = raw[raw["period"].eq("OOS_2025_2026")].copy()
    practical_research = research[practical_guard_mask(research)].copy()
    practical_oos = oos[practical_guard_mask(oos)].copy()

    exports = {
        "python_expected_base_research_99": slim_trades(research, "A_BASE"),
        "python_expected_base_oos_15": slim_trades(oos, "A_BASE"),
        "python_expected_base_all_114": slim_trades(raw, "A_BASE"),
        "python_expected_practical_research_34": slim_trades(practical_research, "B_LIVE"),
        "python_expected_practical_oos_5": slim_trades(practical_oos, "B_LIVE"),
        "python_expected_practical_research_ex_audjpy_30": slim_trades(
            practical_research[practical_research["symbol"].isin(RECOMMENDED_6)].copy(),
            "B_LIVE_6SYM",
        ),
    }

    for name, df in exports.items():
        df.to_csv(OUT_DIR / f"{name}.csv", index=False)

    by_symbol_dir = OUT_DIR / "by_symbol"
    by_symbol_dir.mkdir(exist_ok=True)
    for symbol in SYMBOLS:
        sub = exports["python_expected_base_research_99"]
        sym_base = sub[sub["symbol"].eq(symbol)].copy()
        sym_base.to_csv(by_symbol_dir / f"{symbol.lower()}_base.csv", index=False)
        sym_prac = exports["python_expected_practical_research_34"]
        sym_prac[sym_prac["symbol"].eq(symbol)].to_csv(
            by_symbol_dir / f"{symbol.lower()}_practical.csv", index=False
        )

    usdjpy_all = exports["python_expected_base_research_99"][
        exports["python_expected_base_research_99"]["symbol"].eq("USDJPY")
    ].copy()
    usdjpy_all.to_csv(OUT_DIR / "expected_usdjpy_all.csv", index=False)
    usdjpy_all.head(5).to_csv(OUT_DIR / "expected_usdjpy_first5.csv", index=False)

    template = exports["python_expected_base_research_99"].copy()
    template["tv_signal_time"] = ""
    template["tv_entry_time"] = ""
    template["tv_match"] = ""
    template["tv_notes"] = ""
    template.to_csv(OUT_DIR / "parity_log_template.csv", index=False)

    summaries = pd.DataFrame(
        [
            summary_row("BASE Research 2015-2024", research),
            summary_row("BASE OOS 2025-2026", oos),
            summary_row("BASE ALL", raw),
            summary_row("Practical Research", practical_research),
            summary_row("Practical OOS", practical_oos),
            summary_row(
                "Practical Research ex-AUDJPY",
                practical_research[practical_research["symbol"].isin(RECOMMENDED_6)],
            ),
        ]
    )
    summaries.to_csv(OUT_DIR / "summary.csv", index=False)

    write_checklist()
    write_report(summaries, exports["python_expected_base_research_99"], usdjpy_all)

    print(f"Output: {OUT_DIR}")
    print(summaries.to_string(index=False))


if __name__ == "__main__":
    main()

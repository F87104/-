"""
TrendBreakV1 + Sai Best Method アンサンブル運用シミュレータ
============================================================

入力:
  - backtests/trendbreak_v1/results_2015_2024/trades.csv (TrendBreakV1)
  - backtests/sai_h1/deep_dive_best_method/trades_filtered.csv (Sai 急な揺り戻し+高値停滞)

運用前提:
  - 同一通貨ペア内では「先発ポジションが exit するまで新規不可」(現実的)
  - 異なる通貨ペアは独立 (リスク分散)
  - 各トレードのリスクは 1R 固定で正規化済み (両CSVとも r 列が R-multiple)
  - TrendBreakV1 は 4モード (conservative/aggressive/looser/combined) のうち
    本検証では "conservative" のみ採用 (堅実運用想定)
    → comparison でも conservative ベースのため一貫性

出力:
  - ensemble_trades.csv : 採用された全トレード (時系列)
  - ensemble_metrics.csv : 統合メトリクス
  - ensemble_by_symbol.csv : 通貨別
  - ensemble_by_year.csv : 年別
  - ensemble_by_month.csv : 月別 (equity curve データ)
  - ensemble_by_strategy.csv : 戦略別寄与
  - ensemble_report.md : マークダウンレポート
  - ensemble_equity_curve.csv : equity curve データ
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TB_TRADES = ROOT / "backtests/trendbreak_v1/results_2015_2024/trades.csv"
SAI_TRADES = ROOT / "backtests/sai_h1/deep_dive_best_method/trades_filtered.csv"

OUT_DIR = ROOT / "backtests/ensemble"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# 1. データロード
# -------------------------------------------------------------------
def load_trendbreak(mode: str = "conservative") -> pd.DataFrame:
    df = pd.read_csv(TB_TRADES, parse_dates=["entry_time", "exit_time"])
    df = df[df["mode"] == mode].copy()
    df["strategy"] = "TrendBreakV1"
    df["r"] = df["pnl_r"].astype(float)
    df = df.rename(columns={"direction": "side"})
    keep = ["symbol", "strategy", "side", "entry_time", "exit_time", "entry", "exit_price", "r"]
    return df[keep].copy()


def load_sai_best() -> pd.DataFrame:
    df = pd.read_csv(SAI_TRADES, parse_dates=["entry_time", "exit_time"])
    df["strategy"] = "SaiBest"
    df["r"] = df["r"].astype(float)
    df = df.rename(columns={"direction": "side", "entry": "entry", "exit": "exit_price"})
    keep = ["symbol", "strategy", "side", "entry_time", "exit_time", "entry", "exit_price", "r"]
    return df[keep].copy()


# -------------------------------------------------------------------
# 2. アンサンブル運用シミュレーション
# -------------------------------------------------------------------
@dataclass
class HeldPosition:
    strategy: str
    side: str
    exit_time: pd.Timestamp


def simulate_ensemble(trades: pd.DataFrame, allow_same_symbol_overlap: bool = False) -> pd.DataFrame:
    """通貨ペアごとに「保有中なら新規エントリー不可」のルールで採用判定。"""
    trades = trades.sort_values(["entry_time", "strategy"]).reset_index(drop=True)
    accepted: list[bool] = []
    open_positions: dict[str, HeldPosition] = {}

    for _, row in trades.iterrows():
        sym = row["symbol"]
        held = open_positions.get(sym)
        if held is not None and row["entry_time"] < held.exit_time and not allow_same_symbol_overlap:
            accepted.append(False)
            continue
        # accept
        accepted.append(True)
        open_positions[sym] = HeldPosition(
            strategy=row["strategy"],
            side=row["side"],
            exit_time=row["exit_time"],
        )
    trades["accepted"] = accepted
    return trades


# -------------------------------------------------------------------
# 3. メトリクス計算
# -------------------------------------------------------------------
def compute_metrics(df: pd.DataFrame, name: str) -> dict:
    n = len(df)
    if n == 0:
        return {"name": name, "trades": 0}
    wins = df[df["r"] > 0]
    losses = df[df["r"] <= 0]
    gross_w = wins["r"].sum()
    gross_l = losses["r"].sum()
    pf = gross_w / abs(gross_l) if abs(gross_l) > 0 else float("inf")
    win_rate = len(wins) / n * 100 if n > 0 else 0.0
    avg_r = df["r"].mean()
    total_r = df["r"].sum()
    avg_win = wins["r"].mean() if len(wins) else 0.0
    avg_loss = losses["r"].mean() if len(losses) else 0.0

    # 連敗・連勝 (時系列順)
    df_sorted = df.sort_values("entry_time").reset_index(drop=True)
    streak_win = streak_loss = max_streak_win = max_streak_loss = 0
    for r in df_sorted["r"]:
        if r > 0:
            streak_win += 1
            streak_loss = 0
        else:
            streak_loss += 1
            streak_win = 0
        max_streak_win = max(max_streak_win, streak_win)
        max_streak_loss = max(max_streak_loss, streak_loss)

    # MaxDD (累積R)
    cum = df_sorted["r"].cumsum()
    peak = cum.cummax()
    dd = peak - cum
    max_dd = dd.max()

    span_days = (df_sorted["entry_time"].iloc[-1] - df_sorted["entry_time"].iloc[0]).days
    trades_per_year = n / (span_days / 365.25) if span_days > 0 else 0

    return {
        "name": name,
        "trades": n,
        "win_rate_%": round(win_rate, 2),
        "PF": round(pf, 3) if math.isfinite(pf) else "inf",
        "avg_R": round(avg_r, 3),
        "avg_win_R": round(avg_win, 3),
        "avg_loss_R": round(avg_loss, 3),
        "total_R": round(total_r, 2),
        "max_DD_R": round(max_dd, 2),
        "calmar_R": round(total_r / max_dd, 3) if max_dd > 0 else float("inf"),
        "max_consec_wins": max_streak_win,
        "max_consec_losses": max_streak_loss,
        "trades_per_year": round(trades_per_year, 1),
    }


# -------------------------------------------------------------------
# 4. メイン
# -------------------------------------------------------------------
def main() -> None:
    print("=" * 72)
    print("Ensemble Simulator: TrendBreakV1 (conservative) + Sai Best Method")
    print("=" * 72)

    tb = load_trendbreak("conservative")
    sai = load_sai_best()
    print(f"Loaded: TrendBreakV1 trades = {len(tb)}, Sai Best trades = {len(sai)}")

    combined = pd.concat([tb, sai], ignore_index=True)
    combined = simulate_ensemble(combined)

    accepted = combined[combined["accepted"]].copy()
    rejected = combined[~combined["accepted"]].copy()
    rejected_by_strategy = rejected.groupby("strategy").size().to_dict()

    print(f"\nAcceptance:")
    print(f"  Total signals = {len(combined)}")
    print(f"  Accepted      = {len(accepted)}")
    print(f"  Rejected (重複) = {len(rejected)}  detail: {rejected_by_strategy}")

    # 全体メトリクス
    metrics_rows: list[dict] = []
    metrics_rows.append(compute_metrics(tb, "TrendBreakV1 (solo)"))
    metrics_rows.append(compute_metrics(sai, "SaiBest (solo)"))
    metrics_rows.append(compute_metrics(accepted, "Ensemble (accepted)"))
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(OUT_DIR / "ensemble_metrics.csv", index=False)
    print("\n--- Overall Metrics ---")
    print(metrics_df.to_string(index=False))

    # シンボル別
    sym_rows = [compute_metrics(accepted[accepted["symbol"] == s], s) for s in sorted(accepted["symbol"].unique())]
    sym_df = pd.DataFrame(sym_rows).sort_values("total_R", ascending=False)
    sym_df.to_csv(OUT_DIR / "ensemble_by_symbol.csv", index=False)
    print("\n--- By Symbol ---")
    print(sym_df.to_string(index=False))

    # 年別
    accepted["year"] = accepted["entry_time"].dt.year
    year_rows = [compute_metrics(accepted[accepted["year"] == y], str(y)) for y in sorted(accepted["year"].unique())]
    year_df = pd.DataFrame(year_rows)
    year_df.to_csv(OUT_DIR / "ensemble_by_year.csv", index=False)
    print("\n--- By Year ---")
    print(year_df.to_string(index=False))

    # 戦略別寄与
    strat_rows = [compute_metrics(accepted[accepted["strategy"] == s], s) for s in sorted(accepted["strategy"].unique())]
    strat_df = pd.DataFrame(strat_rows)
    strat_df.to_csv(OUT_DIR / "ensemble_by_strategy.csv", index=False)
    print("\n--- By Strategy (Ensemble Contribution) ---")
    print(strat_df.to_string(index=False))

    # 月別 equity curve
    accepted["month"] = accepted["entry_time"].dt.to_period("M").astype(str)
    monthly = accepted.groupby("month")["r"].agg(["count", "sum"]).reset_index()
    monthly.columns = ["month", "trades", "monthly_R"]
    monthly["cum_R"] = monthly["monthly_R"].cumsum()
    monthly["peak"] = monthly["cum_R"].cummax()
    monthly["dd_R"] = monthly["peak"] - monthly["cum_R"]
    monthly.to_csv(OUT_DIR / "ensemble_by_month.csv", index=False)

    # 全トレード保存
    accepted_out = accepted.sort_values("entry_time").reset_index(drop=True)
    accepted_out["cum_R"] = accepted_out["r"].cumsum()
    accepted_out.to_csv(OUT_DIR / "ensemble_trades.csv", index=False)
    accepted_out[["entry_time", "strategy", "symbol", "side", "r", "cum_R"]].to_csv(
        OUT_DIR / "ensemble_equity_curve.csv", index=False
    )

    # レポート markdown
    write_report(metrics_df, sym_df, year_df, strat_df, monthly, accepted_out, rejected_by_strategy)
    print(f"\n✅ Output saved to: {OUT_DIR}")


def df_to_md(df: pd.DataFrame) -> str:
    """tabulate を使わない簡易 markdown テーブル生成。"""
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(str(c) for c in cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                if math.isfinite(v):
                    cells.append(f"{v:.3f}" if abs(v) < 100 else f"{v:.2f}")
                else:
                    cells.append("inf")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(metrics_df, sym_df, year_df, strat_df, monthly_df, trades_df, rejected_by_strategy):
    lines = []
    lines.append("# Ensemble Backtest Report — TrendBreakV1 + Sai Best Method")
    lines.append("")
    lines.append(f"_Generated by `backtests/ensemble/run_ensemble.py`_")
    lines.append("")
    lines.append("## 目的")
    lines.append("")
    lines.append("- **TrendBreakV1** (conservative): 高EV・低頻度のブレイクアウト戦略")
    lines.append("- **Sai Best Method**: 急な揺り戻し+高値停滞 (V字+停滞ブレイク)")
    lines.append("")
    lines.append("両者を同一口座で同時運用したときのパフォーマンスを検証。")
    lines.append("**ルール**: 同一通貨ペアで保有中なら新規不可。異なる通貨は独立。")
    lines.append("")
    lines.append("## 全体サマリー")
    lines.append("")
    lines.append(df_to_md(metrics_df))
    lines.append("")
    lines.append(f"- 重複却下: {rejected_by_strategy}")
    lines.append("")

    ens_row = metrics_df[metrics_df["name"] == "Ensemble (accepted)"].iloc[0]
    tb_row = metrics_df[metrics_df["name"] == "TrendBreakV1 (solo)"].iloc[0]
    sai_row = metrics_df[metrics_df["name"] == "SaiBest (solo)"].iloc[0]
    lines.append("### アンサンブル効果")
    lines.append("")
    lines.append(f"- 単独運用 TrendBreakV1: {tb_row['trades']} trades / +{tb_row['total_R']}R / PF {tb_row['PF']}")
    lines.append(f"- 単独運用 Sai Best:     {sai_row['trades']} trades / +{sai_row['total_R']}R / PF {sai_row['PF']}")
    lines.append(f"- **アンサンブル運用**:   {ens_row['trades']} trades / +{ens_row['total_R']}R / PF {ens_row['PF']}")
    expected_naive = float(tb_row["total_R"]) + float(sai_row["total_R"])
    delta = float(ens_row["total_R"]) - expected_naive
    lines.append(f"- 単純合算 (重複考慮なし): {expected_naive:.1f}R → 実効差分: {delta:+.1f}R")
    lines.append(f"- アンサンブルの年間トレード数: **{ens_row['trades_per_year']} trades/year**")
    lines.append(f"- 連敗最大: {ens_row['max_consec_losses']} (単独 TB={tb_row['max_consec_losses']}, Sai={sai_row['max_consec_losses']})")
    lines.append(f"- MaxDD: {ens_row['max_DD_R']}R (Calmar {ens_row['calmar_R']})")
    lines.append("")
    lines.append("## 戦略別寄与")
    lines.append("")
    lines.append(df_to_md(strat_df))
    lines.append("")
    lines.append("## 通貨別")
    lines.append("")
    lines.append(df_to_md(sym_df))
    lines.append("")
    lines.append("## 年別")
    lines.append("")
    lines.append(df_to_md(year_df))
    lines.append("")
    lines.append("## 月別 equity curve (累積R)")
    lines.append("")
    monthly_show = monthly_df.copy()
    monthly_show["monthly_R"] = monthly_show["monthly_R"].round(2)
    monthly_show["cum_R"] = monthly_show["cum_R"].round(2)
    monthly_show["dd_R"] = monthly_show["dd_R"].round(2)
    monthly_show = monthly_show[["month", "trades", "monthly_R", "cum_R", "dd_R"]]
    lines.append(df_to_md(monthly_show.tail(24)))
    lines.append("")
    lines.append("_(最新24ヶ月のみ表示。フル: `ensemble_by_month.csv`)_")
    lines.append("")
    lines.append("## 解釈ガイド")
    lines.append("")
    lines.append("- **アンサンブルが単独より優秀な場合**: 戦略の相補性が機能")
    lines.append("- **逆相関 / 連敗緩和**: TrendBreakV1 の連敗期に Sai がカバーしているか確認")
    lines.append("- **重複却下が極端に多い場合**: 戦略のシグナル特性が近く、分散効果薄")
    lines.append("")
    (OUT_DIR / "ensemble_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

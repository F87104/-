from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
V_TRADES = ROOT / "backtests/elliott_fibo/results_2025_2026_oos/t5_failure_filter_validation/baseline_final_trades_rec120_strict.csv"
TB_COMPARISON = ROOT / "backtests/relaxation/hybrid_comparison.csv"
TB_BY_SYMBOL = ROOT / "backtests/relaxation/hybrid_HYBRID_optimal_per_symbol.csv"
OUT = ROOT / "docs/two_method_practical_research_2026-05-24.md"


def max_drawdown_r(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    peak = equity.cummax()
    dd = peak - equity
    return float(dd.max())


def max_losing_streak(values: pd.Series) -> int:
    streak = 0
    best = 0
    for value in values:
        if value < 0:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return best


def stats(df: pd.DataFrame) -> dict[str, float | int | str]:
    if df.empty:
        return {
            "trades": 0,
            "winrate": 0.0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "pf": "N/A",
            "max_dd_r": 0.0,
            "max_losing_streak": 0,
        }

    r = df["r_after_cost"].astype(float)
    wins = r[r > 0]
    losses = r[r < 0]
    gross_win = float(wins.sum())
    gross_loss = float(abs(losses.sum()))
    pf: float | str = gross_win / gross_loss if gross_loss > 0 else "inf"
    return {
        "trades": int(len(df)),
        "winrate": float((r > 0).mean() * 100),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": pf,
        "max_dd_r": max_drawdown_r(r),
        "max_losing_streak": max_losing_streak(r),
    }


def fmt_num(value: float | int | str, digits: int = 2) -> str:
    if isinstance(value, str):
        return value
    return f"{value:.{digits}f}"


def stats_table(df: pd.DataFrame, group: str | None = None) -> pd.DataFrame:
    rows = []
    groups = [(None, df)] if group is None else list(df.groupby(group, dropna=False))
    for name, part in groups:
        row = stats(part)
        if group is not None:
            row[group] = name
        rows.append(row)
    out = pd.DataFrame(rows)
    if group is not None and not out.empty:
        cols = [group] + [c for c in out.columns if c != group]
        out = out[cols]
    return out


def md_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_no data_"
    render = df.loc[:, columns].copy()
    for col in render.columns:
        if col in {"winrate", "total_r", "avg_r", "max_dd_r"}:
            render[col] = render[col].map(lambda x: fmt_num(float(x), 2))
        elif col == "pf":
            render[col] = render[col].map(lambda x: fmt_num(x, 2) if not isinstance(x, str) else x)
    widths = []
    string_rows = []
    headers = list(render.columns)
    for _, row in render.iterrows():
        string_rows.append([str(row[col]) for col in headers])
    for idx, header in enumerate(headers):
        max_cell = max([len(r[idx]) for r in string_rows], default=0)
        widths.append(max(len(header), max_cell))

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(values)) + " |"

    lines = [fmt_row(headers), "| " + " | ".join("-" * w for w in widths) + " |"]
    lines.extend(fmt_row(row) for row in string_rows)
    return "\n".join(lines)


def main() -> None:
    v = pd.read_csv(V_TRADES)
    v["entry_time"] = pd.to_datetime(v["entry_time"])
    v = v.sort_values("entry_time").reset_index(drop=True)

    base = v.copy()
    practical = v[
        (v["bb_pos"] <= 0.95)
        & (v["signal_recovery_bars"] <= 16)
        & ~(
            (v["trigger_type"] == "rebreak")
            & ((v["bb_pos"] > 0.95) | (v["macd_hist_slope3"] <= 0.03))
        )
    ].copy()
    ultra = v[
        (v["bb_pos"] <= 0.95)
        & (v["signal_recovery_bars"] <= 16)
        & (v["macd_hist_slope3"] > 0.03)
        & (v["bb_width_atr"] <= 4.0)
        & ~(
            (v["trigger_type"] == "rebreak")
            & ((v["bb_pos"] > 0.95) | (v["macd_hist_slope3"] <= 0.03))
        )
    ].copy()

    tb_cmp = pd.read_csv(TB_COMPARISON)
    tb_sym = pd.read_csv(TB_BY_SYMBOL)
    hybrid = tb_cmp[tb_cmp["scenario"] == "HYBRID_optimal"].iloc[0]

    report: list[str] = []
    report.append("# 実戦向け 2本柱 研究ノート")
    report.append("")
    report.append("作成日: 2026-05-24")
    report.append("")
    report.append("## 結論")
    report.append("")
    report.append("実戦で使うなら、V字をそのままエントリー条件にせず、**V候補を環境認識として使い、その後に高値停滞・再ブレイク・MACD・BB位置が重なる場面だけ入る**のが現実的です。")
    report.append("")
    report.append("2つに絞るなら、以下の組み合わせが最も扱いやすいです。")
    report.append("")
    report.append("1. **TrendBreakV1 HYBRID**: 主力。高安値更新・節目ブレイク型。取引回数と総利益を取りに行く。")
    report.append("2. **H4 V候補 T5 + MACD + BB**: 補助。急落後のV回復候補から、高値停滞または再ブレイクで厳選して入る。勝率とPFを重視する。")
    report.append("")
    report.append("## 手法1: TrendBreakV1 HYBRID")
    report.append("")
    report.append("役割: 20日から数か月級の高安値更新を使い、伸びる相場を取りに行く主力手法。")
    report.append("")
    report.append("| 指標 | 値 |")
    report.append("|---|---:|")
    report.append(f"| 期間 | 2015-2024 |")
    report.append(f"| 取引回数 | {int(hybrid['total_trades'])} |")
    report.append(f"| 年間取引回数 | {float(hybrid['trades_per_year']):.1f} |")
    report.append(f"| 勝率 | {float(hybrid['win_rate']):.2f}% |")
    report.append(f"| 総R | {float(hybrid['total_r_after_cost']):.2f}R |")
    report.append(f"| 平均R | {float(hybrid['avg_r_after_cost']):.2f}R |")
    report.append(f"| PF | {float(hybrid['pf_after_cost']):.2f} |")
    report.append(f"| 最大連敗 | {int(hybrid['max_losing_streak'])} |")
    report.append(f"| 最大DD | {float(hybrid['max_dd_after_cost_r']):.2f}R |")
    report.append("")
    report.append("通貨別:")
    report.append("")
    tb_cols = ["symbol", "trades", "win_rate", "total_r_after_cost", "avg_r_after_cost", "pf_after_cost", "max_losing_streak"]
    tb_render = tb_sym[tb_cols].rename(
        columns={
            "win_rate": "winrate",
            "total_r_after_cost": "total_r",
            "avg_r_after_cost": "avg_r",
            "pf_after_cost": "pf",
        }
    )
    report.append(md_table(tb_render, ["symbol", "trades", "winrate", "total_r", "avg_r", "pf", "max_losing_streak"]))
    report.append("")
    report.append("## 手法2: H4 V候補 T5 + MACD + BB")
    report.append("")
    report.append("役割: 急落後のV回復を直接買うのではなく、**戻りの勢いが確認された後の候補だけを抽出**し、そこから高値停滞・再ブレイクで入る補助手法。")
    report.append("")
    report.append("### 共通条件")
    report.append("")
    report.append("- 時間足: H4")
    report.append("- 方向: 現在はロングのみ")
    report.append("- V候補: 急落後、下落幅の61.8%から80%まで回復")
    report.append("- 回復速度: 下落形成本数に対して回復本数が1.20倍以内。例: 下落10本なら回復12本以内")
    report.append("- BB位置: 0.75から1.00が基本。実戦フィルタでは0.95以下を優先")
    report.append("- MACD: ヒストグラムが3本前より上昇")
    report.append("- BB幅: 7ATR以内。4ATR超はロットを下げる候補")
    report.append("- エントリー: V候補後の高値停滞ブレイク、または一度押した後の戻り高値再ブレイク")
    report.append("")
    report.append("### 成績比較")
    report.append("")
    comp = pd.DataFrame(
        [
            {"rule": "標準: V候補 + T5 + MACD + BB", **stats(base)},
            {"rule": "実戦用: BB<=0.95 + 16本以内 + 弱い単独rebreak除外", **stats(practical)},
            {"rule": "超厳選: 実戦用 + MACD強 + BB幅<=4ATR", **stats(ultra)},
        ]
    )
    report.append(md_table(comp, ["rule", "trades", "winrate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]))
    report.append("")
    report.append("実戦では、超厳選は勝率が高いものの取引が少なすぎるため、最初は **実戦用ルール** を本線にするのが現実的です。")
    report.append("")
    report.append("### 実戦用ルールの期間別")
    report.append("")
    period_tbl = stats_table(practical, "period")
    report.append(md_table(period_tbl, ["period", "trades", "winrate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]))
    report.append("")
    report.append("### 実戦用ルールの通貨別")
    report.append("")
    symbol_tbl = stats_table(practical, "symbol").sort_values("total_r", ascending=False)
    report.append(md_table(symbol_tbl, ["symbol", "trades", "winrate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]))
    report.append("")
    report.append("### 実戦用ルールのトリガー別")
    report.append("")
    trigger_tbl = stats_table(practical, "trigger_type").sort_values("total_r", ascending=False)
    report.append(md_table(trigger_tbl, ["trigger_type", "trades", "winrate", "total_r", "avg_r", "pf", "max_dd_r", "max_losing_streak"]))
    report.append("")
    report.append("## 実戦ルール案")
    report.append("")
    report.append("### A. 主力: TrendBreakV1")
    report.append("")
    report.append("- 6通貨で監視: XAUUSD, USDJPY, EURJPY, GBPJPY, CHFJPY, SILVER")
    report.append("- AUDJPYは現段階では除外")
    report.append("- 1トレードのリスクは最大1R。資金100万円なら1R=1万円を上限にする")
    report.append("- 連敗13回程度は想定内。DD停止ラインを20%前後に置く")
    report.append("")
    report.append("### B. 補助: H4 V候補 T5 + MACD + BB")
    report.append("")
    report.append("- V候補だけでは入らない")
    report.append("- V候補後、H4で16本以内に高値停滞ブレイクまたは戻り高値再ブレイクが出た時だけ検討")
    report.append("- BB位置が0.95を超えたら原則見送り")
    report.append("- 単独rebreakでMACD slope3が0.03以下なら見送り")
    report.append("- BB幅が4ATR超なら半分ロット、7ATR超なら見送り")
    report.append("- まずは0.25Rから0.5Rでフォワード確認。30から50回分の実売買/デモ記録が安定してから通常リスクへ上げる")
    report.append("")
    report.append("## 使い分け")
    report.append("")
    report.append("| 状況 | 使う手法 | 判断 |")
    report.append("|---|---|---|")
    report.append("| 明確な高安値更新・節目突破 | TrendBreakV1 | 主力として入る |")
    report.append("| 急落後にV候補が出たが、まだ形が荒い | H4 V候補 | まだ入らない |")
    report.append("| V候補後に高値停滞または再ブレイク、MACD/BBも一致 | H4 V候補 T5 | 補助エントリー候補 |")
    report.append("| TrendBreakとV候補が同じ通貨で同時に近い位置に出る | 片方だけ | 重複リスクを避ける |")
    report.append("| BB位置が高すぎる、回復から時間が経ちすぎた | 見送り | 飛び乗りを避ける |")
    report.append("")
    report.append("## 次にやること")
    report.append("")
    report.append("1. Pine側でH4 V候補のラベルを「候補」「実戦用シグナル」「見送り理由」に分ける")
    report.append("2. TrendBreakV1とH4 V候補の同一通貨・同時期の重複を確認し、重複時はどちらを優先するか決める")
    report.append("3. H4 V候補は2026年以降もフォワードで最低30回、できれば50回まで記録してから本番ロットへ上げる")
    report.append("")
    report.append("## 注意")
    report.append("")
    report.append("この研究は過去データに基づく検証です。実運用ではスプレッド拡大、約定滑り、データ差、ニュース急変で結果が変わるため、最初は小さなリスクで検証してください。")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()

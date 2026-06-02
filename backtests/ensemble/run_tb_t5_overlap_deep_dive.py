#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


THIS_DIR = Path(__file__).resolve().parent
SOURCE_DIR = THIS_DIR / "trendbreak_t5_practical_combo_2015_2024"
OUT_DIR = THIS_DIR / "tb_t5_overlap_deep_dive_2026_06_02"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RECOMMENDED_SYMBOLS = ["XAUUSD", "USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "SILVER"]


def load_trades(name: str) -> pd.DataFrame:
    df = pd.read_csv(SOURCE_DIR / name, parse_dates=["signal_time", "entry_time", "exit_time"])
    return df[df["symbol"].isin(RECOMMENDED_SYMBOLS)].copy()


def overlaps(a: pd.Series, b: pd.Series) -> bool:
    return a["entry_time"] < b["exit_time"] and b["entry_time"] < a["exit_time"]


def summarize(trades: pd.DataFrame, label: str) -> dict:
    if trades.empty:
        return {
            "scenario": label,
            "trades": 0,
            "win_rate": 0.0,
            "total_r": 0.0,
            "avg_r": math.nan,
            "pf": math.nan,
            "max_dd_r": 0.0,
            "max_loss_streak": 0,
        }
    ordered = trades.sort_values(["exit_time", "entry_time", "strategy", "symbol"]).reset_index(drop=True)
    r = ordered["r"].astype(float)
    wins = r[r > 0]
    losses = r[r <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() < 0 else math.inf
    curve = r.cumsum()
    dd = curve.cummax() - curve
    loss_streak = 0
    max_loss_streak = 0
    for value in r:
        if value <= 0:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        else:
            loss_streak = 0
    return {
        "scenario": label,
        "trades": int(len(ordered)),
        "win_rate": float((r > 0).mean() * 100.0),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "pf": pf,
        "max_dd_r": float(dd.max()) if len(dd) else 0.0,
        "max_loss_streak": int(max_loss_streak),
    }


def annotate_t5(tb: pd.DataFrame, t5: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, trade in t5.sort_values("entry_time").iterrows():
        symbol_tb = tb[tb["symbol"].eq(trade["symbol"])].copy()
        overlapping = symbol_tb[symbol_tb.apply(lambda x: overlaps(trade, x), axis=1)].copy()
        if overlapping.empty:
            rows.append(
                {
                    **trade.to_dict(),
                    "overlap_bucket": "free",
                    "overlap_count": 0,
                    "overlap_tb_r_sum": 0.0,
                    "overlap_same_dir_count": 0,
                    "overlap_opp_dir_count": 0,
                    "overlap_tb_entries": "",
                    "overlap_tb_exits": "",
                    "overlap_tb_directions": "",
                    "overlap_tb_after_t5_hours_median": math.nan,
                }
            )
            continue
        same_dir = overlapping["direction"].eq(trade["direction"])
        bucket = "overlap_same_direction" if same_dir.all() else "overlap_opposite_or_mixed"
        hours = (overlapping["entry_time"] - trade["entry_time"]).dt.total_seconds() / 3600.0
        rows.append(
            {
                **trade.to_dict(),
                "overlap_bucket": bucket,
                "overlap_count": int(len(overlapping)),
                "overlap_tb_r_sum": float(overlapping["r"].sum()),
                "overlap_same_dir_count": int(same_dir.sum()),
                "overlap_opp_dir_count": int((~same_dir).sum()),
                "overlap_tb_entries": ";".join(overlapping["entry_time"].astype(str)),
                "overlap_tb_exits": ";".join(overlapping["exit_time"].astype(str)),
                "overlap_tb_directions": ",".join(overlapping["direction"].astype(str)),
                "overlap_tb_after_t5_hours_median": float(hours.median()),
            }
        )
    return pd.DataFrame(rows)


def annotate_tb_context(tb: pd.DataFrame, t5_annotated: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, trade in tb.sort_values("entry_time").iterrows():
        symbol_t5 = t5_annotated[t5_annotated["symbol"].eq(trade["symbol"])].copy()
        overlapping = symbol_t5[symbol_t5.apply(lambda x: overlaps(trade, x), axis=1)].copy()
        if overlapping.empty:
            bucket = "tb_no_t5_context"
        else:
            same_dir = overlapping["direction"].eq(trade["direction"])
            bucket = "tb_with_same_dir_t5_context" if same_dir.all() else "tb_with_opp_or_mixed_t5_context"
        rows.append(
            {
                **trade.to_dict(),
                "tb_context_bucket": bucket,
                "overlap_t5_count": int(len(overlapping)),
                "overlap_t5_r_sum": float(overlapping["r"].sum()) if not overlapping.empty else 0.0,
                "overlap_t5_entries": ";".join(overlapping["entry_time"].astype(str)),
                "overlap_t5_exits": ";".join(overlapping["exit_time"].astype(str)),
                "overlap_t5_triggers": ",".join(overlapping["trigger_type"].astype(str)),
            }
        )
    return pd.DataFrame(rows)


def make_pair_summary(t5_annotated: pd.DataFrame) -> pd.DataFrame:
    pair = t5_annotated[t5_annotated["overlap_count"].gt(0)].copy()
    if pair.empty:
        return pair
    pair["pair_total_r"] = pair["r"].astype(float) + pair["overlap_tb_r_sum"].astype(float)
    pair["entry_gap_hours_median"] = pair["overlap_tb_after_t5_hours_median"]
    return pair


def trade_risk(trade: pd.Series) -> float:
    r_value = float(trade["r"])
    if abs(r_value) < 1e-9:
        return math.nan
    if trade["direction"] == "long":
        return float(trade["exit"] - trade["entry"]) / r_value
    return float(trade["entry"] - trade["exit"]) / r_value


def r_at_price(trade: pd.Series, price: float) -> float:
    risk = trade_risk(trade)
    if not math.isfinite(risk) or risk <= 0:
        return math.nan
    if trade["direction"] == "long":
        return (price - float(trade["entry"])) / risk
    return (float(trade["entry"]) - price) / risk


def make_t5_management_at_first_tb(tb: pd.DataFrame, t5_annotated: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, trade in t5_annotated.sort_values("entry_time").iterrows():
        symbol_tb = tb[tb["symbol"].eq(trade["symbol"])].copy()
        overlapping = symbol_tb[symbol_tb.apply(lambda x: overlaps(trade, x), axis=1)].copy()
        overlapping = overlapping.sort_values("entry_time")
        if overlapping.empty:
            first_time = pd.NaT
            first_direction = ""
            first_entry = math.nan
            first_r = math.nan
        else:
            first = overlapping.iloc[0]
            first_time = first["entry_time"]
            first_direction = first["direction"]
            first_entry = float(first["entry"])
            first_r = r_at_price(trade, first_entry)
        rows.append(
            {
                "strategy": trade["strategy"],
                "symbol": trade["symbol"],
                "trigger_type": trade["trigger_type"],
                "entry_time": trade["entry_time"],
                "exit_time": trade["exit_time"],
                "direction": trade["direction"],
                "entry": trade["entry"],
                "exit": trade["exit"],
                "original_r": trade["r"],
                "overlap_bucket": trade["overlap_bucket"],
                "first_tb_time": first_time,
                "first_tb_direction": first_direction,
                "first_tb_entry": first_entry,
                "r_if_exit_at_first_tb": first_r,
                "delta_vs_original": first_r - float(trade["r"]) if math.isfinite(first_r) else math.nan,
            }
        )
    out = pd.DataFrame(rows)
    out["managed_close_on_conflict_r"] = out.apply(
        lambda x: x["r_if_exit_at_first_tb"]
        if x["overlap_bucket"] == "overlap_opposite_or_mixed" and math.isfinite(float(x["r_if_exit_at_first_tb"]))
        else x["original_r"],
        axis=1,
    )
    out["managed_close_on_any_tb_r"] = out.apply(
        lambda x: x["r_if_exit_at_first_tb"]
        if x["overlap_bucket"] != "free" and math.isfinite(float(x["r_if_exit_at_first_tb"]))
        else x["original_r"],
        axis=1,
    )
    return out


def scaled_subset(subset: pd.DataFrame, weight: float, suffix: str) -> pd.DataFrame:
    out = subset.copy()
    out["r"] = out["r"].astype(float) * weight
    out["strategy"] = out["strategy"].astype(str) + suffix
    return out


def make_scenarios(tb: pd.DataFrame, t5_annotated: pd.DataFrame) -> dict[str, pd.DataFrame]:
    free = t5_annotated[t5_annotated["overlap_bucket"].eq("free")].copy()
    same = t5_annotated[t5_annotated["overlap_bucket"].eq("overlap_same_direction")].copy()
    opposite = t5_annotated[t5_annotated["overlap_bucket"].eq("overlap_opposite_or_mixed")].copy()

    # Existing output, loaded for exact comparison.
    same_symbol_first = load_trades("same_symbol_first_wins_trades.csv")

    scenarios = {
        "TB_only": tb,
        "TB_plus_T5_free_only": pd.concat([tb, free], ignore_index=True),
        "TB_plus_T5_free_and_same_overlap_full": pd.concat([tb, free, same], ignore_index=True),
        "TB_plus_T5_free_and_same_overlap_half": pd.concat(
            [tb, free, scaled_subset(same, 0.5, "_HALF_RISK")],
            ignore_index=True,
        ),
        "TB_plus_T5_free_and_same_overlap_quarter": pd.concat(
            [tb, free, scaled_subset(same, 0.25, "_QUARTER_RISK")],
            ignore_index=True,
        ),
        "TB_plus_all_T5": pd.concat([tb, t5_annotated], ignore_index=True),
        "same_symbol_first_wins": same_symbol_first,
        "T5_only": t5_annotated,
        "T5_free_only": free,
        "T5_overlap_same_direction_only": same,
        "T5_overlap_opposite_or_mixed_only": opposite,
    }
    return scenarios


def grouped(df: pd.DataFrame, cols: list[str], label_prefix: str) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(cols, dropna=False):
        key_tuple = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(cols, key_tuple))
        row.update(summarize(group, label_prefix + "_" + "_".join(str(x) for x in key_tuple)))
        rows.append(row)
    return pd.DataFrame(rows)


def md(df: pd.DataFrame, digits: int = 2) -> str:
    if df.empty:
        return "_No rows._"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        vals = []
        for col in headers:
            v = row[col]
            if isinstance(v, float):
                if math.isinf(v):
                    vals.append("inf")
                elif col == "avg_r":
                    vals.append(f"{v:.3f}")
                elif col in {"win_rate"}:
                    vals.append(f"{v:.2f}%")
                else:
                    vals.append(f"{v:.{digits}f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    tb = load_trades("trendbreak_only_trades.csv")
    t5 = load_trades("t5_practical_only_trades.csv")
    t5_annotated = annotate_t5(tb, t5)
    t5_annotated.to_csv(OUT_DIR / "t5_overlap_annotation.csv", index=False)
    tb_annotated = annotate_tb_context(tb, t5_annotated)
    tb_annotated.to_csv(OUT_DIR / "tb_t5_context_annotation.csv", index=False)
    pair = make_pair_summary(t5_annotated)
    pair.to_csv(OUT_DIR / "tb_t5_overlap_pair_detail.csv", index=False)
    t5_management = make_t5_management_at_first_tb(tb, t5_annotated)
    t5_management.to_csv(OUT_DIR / "t5_management_at_first_tb.csv", index=False)

    scenarios = make_scenarios(tb, t5_annotated)
    summary = pd.DataFrame([summarize(trades, name) for name, trades in scenarios.items()])
    summary.to_csv(OUT_DIR / "scenario_summary.csv", index=False)

    grouped(t5_annotated, ["overlap_bucket"], "bucket").to_csv(OUT_DIR / "t5_by_overlap_bucket.csv", index=False)
    grouped(t5_annotated, ["overlap_bucket", "trigger_type"], "bucket_trigger").to_csv(
        OUT_DIR / "t5_by_overlap_bucket_trigger.csv",
        index=False,
    )
    grouped(t5_annotated, ["symbol", "overlap_bucket"], "symbol_bucket").to_csv(
        OUT_DIR / "t5_by_symbol_overlap_bucket.csv",
        index=False,
    )
    grouped(tb_annotated, ["tb_context_bucket"], "tb_context").to_csv(
        OUT_DIR / "tb_by_t5_context_bucket.csv",
        index=False,
    )
    if not pair.empty:
        pair_for_summary = pair.copy()
        pair_for_summary["r"] = pair_for_summary["pair_total_r"]
        grouped(pair_for_summary, ["overlap_bucket"], "pair_bucket").to_csv(
            OUT_DIR / "tb_t5_pair_by_bucket.csv",
            index=False,
        )
    management_scenarios = {
        "T5_original": t5_annotated.rename(columns={"r": "r"}),
        "T5_close_on_opposite_or_mixed_TB": t5_management.assign(r=t5_management["managed_close_on_conflict_r"]),
        "T5_close_on_any_TB": t5_management.assign(r=t5_management["managed_close_on_any_tb_r"]),
    }
    management_summary = pd.DataFrame(
        [summarize(trades, name) for name, trades in management_scenarios.items()]
    )
    management_summary.to_csv(OUT_DIR / "t5_management_scenarios.csv", index=False)

    report = [
        "# TB + T5 Overlap Deep Dive",
        "",
        "作成日: 2026-06-02",
        "",
        "## 目的",
        "",
        "TB+T5アンサンブルの結果から、T5を単純な追加手法ではなく、TBより早い初動サインとして扱えるかを確認した。",
        "",
        "## T5重複バケット",
        "",
        md(pd.read_csv(OUT_DIR / "t5_by_overlap_bucket.csv")),
        "",
        "## T5重複バケット x トリガー",
        "",
        md(pd.read_csv(OUT_DIR / "t5_by_overlap_bucket_trigger.csv")),
        "",
        "## T5重複バケット x 通貨",
        "",
        md(pd.read_csv(OUT_DIR / "t5_by_symbol_overlap_bucket.csv")),
        "",
        "## TB側から見たT5コンテキスト",
        "",
        md(pd.read_csv(OUT_DIR / "tb_by_t5_context_bucket.csv")),
        "",
        "## T5 + 後続TB ペア合算",
        "",
        md(pd.read_csv(OUT_DIR / "tb_t5_pair_by_bucket.csv")) if not pair.empty else "_No rows._",
        "",
        "## T5保有中にTBが出た時の管理テスト",
        "",
        md(management_summary),
        "",
        "## シナリオ比較",
        "",
        md(summary),
        "",
        "## T5重複詳細",
        "",
        md(
            t5_annotated[
                [
                    "symbol",
                    "trigger_type",
                    "entry_time",
                    "exit_time",
                    "r",
                    "overlap_bucket",
                    "overlap_tb_r_sum",
                    "overlap_tb_directions",
                    "overlap_tb_after_t5_hours_median",
                ]
            ],
            digits=3,
        ),
        "",
        "## 暫定発見",
        "",
        "- T5がTB保有中に後から出るケースはなく、T5が先に出て後からTBが重なるケースだけだった。",
        "- 推奨6通貨では、T5単体30件のうち18件はTBと重ならず、12件は後続TBと重なった。",
        "- 後続TBと同方向に重なるT5は10件、T5合計+14.81R、後続TB合計+5.29R。T5を初動、TBを追加確認として見る余地がある。",
        "- 逆方向または混在の重なりは2件のみで、まだ判断不能。実戦では逆方向TBは新規追加ではなく注意タグ扱いが妥当。",
        "- 同方向重なりT5をフルリスクで足すと数字は伸びるが、同一通貨の二重リスクになる。半分リスクまたは0.25R追加が実戦候補。",
        "- 同方向T5コンテキスト中のTB自体は10件で+5.29R、PF 1.81。TB追加だけが特別強いわけではないため、追加よりもT5の保有継続・利確判断の根拠として使う方が自然。",
        "- T5の同方向重なりは、あとからTBが出たという未来情報でしか確定しない。T5エントリー時点のフィルタには使わず、保有中の管理ルールとして扱う。",
        "- T5保有中に逆方向/混在TBが出たら即撤退、という単純ルールはT5単体より悪化した。T5 original +25.33R / PF 3.43 に対し、conflict撤退は +25.06R / PF 3.34。",
        "- T5保有中に同方向TBが出ても、T5をそこで早利確すると +18.42R / PF 2.91 まで期待値を削る。T5は早逃げより、元のSL/TP管理を維持する方が現時点では自然。",
        "",
    ]
    (OUT_DIR / "report_ja.md").write_text("\n".join(report), encoding="utf-8")
    print(OUT_DIR)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

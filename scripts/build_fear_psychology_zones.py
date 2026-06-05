#!/usr/bin/env python3
"""
Build fear / stop-loss / revenge-reentry zones from student chart entries.

Outputs:
  docs/research/fear_psychology_zones_v0_1.csv
  docs/research/fear_psychology_revenge_reentry_v0_1.csv
  docs/research/fear_psychology_chart_verification_2026-06-01.md

Zones:
  FEAR_STOP   — loss exit price clusters (where stops likely hit / pain)
  FEAR_ENTRY  — loss entry clusters (where people jumped in scared/wrong)
  REVENGE     — re-entry within 72h after loss, same direction (どテン候補)
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ENTRIES = REPO / "docs/research/student_entries_extracted.csv"
STUMBLE = REPO / "docs/research/student_stumble_clusters_v0_3.csv"
WAIT = REPO / "docs/research/student_stumble_wait_zones_v0_2.csv"
DATA_ROOT = REPO / "F87104_test"
OUT_ZONES = REPO / "docs/research/fear_psychology_zones_v0_1.csv"
OUT_REVENGE = REPO / "docs/research/fear_psychology_revenge_reentry_v0_1.csv"
OUT_REPORT = REPO / "docs/research/fear_psychology_chart_verification_2026-06-01.md"
OUT_PINE = REPO / "pine/visual/fear_psychology_zones_visual.pine"

# Key zones to verify on OHLC (from stumble + wait zones)
VERIFY_CASES = [
    {
        "id": "GBPJPY_199_all_loss",
        "currency": "GBPJPY",
        "folder": "GBYJPY",
        "start_jst": "2024-10-28 07:00:00",
        "end_jst": "2024-10-31 08:00:00",
        "zone_lo": 198.38,
        "zone_hi": 199.64,
        "side": "buy",
        "expect": "199円台追い買い→反落（7人中6敗クラスタ）。恐怖の節目追い。",
    },
    {
        "id": "GBPJPY_195_all_loss",
        "currency": "GBPJPY",
        "folder": "GBYJPY",
        "start_jst": "2024-10-14 18:00:00",
        "end_jst": "2024-10-15 12:00:00",
        "zone_lo": 195.35,
        "zone_hi": 195.69,
        "side": "buy",
        "expect": "195帯5人全敗。高値タッチ後の押し（赤帯v0.5）。",
    },
    {
        "id": "GBPJPY_194_fly",
        "currency": "GBPJPY",
        "folder": "GBYJPY",
        "start_jst": "2024-10-02 00:00:00",
        "end_jst": "2024-10-05 23:59:00",
        "zone_lo": 194.0,
        "zone_hi": 195.0,
        "side": "buy",
        "expect": "194飛び乗り→193押しが待つ場所（青帯）。",
    },
    {
        "id": "XAU_2950_all_loss",
        "currency": "XAUUSD",
        "folder": "XAUUSD",
        "start_jst": "2025-02-18 00:00:00",
        "end_jst": "2025-02-22 23:59:00",
        "zone_lo": 2934.0,
        "zone_hi": 2955.0,
        "side": "buy",
        "expect": "2950史上高値追い→6人全敗。恐怖の利確逃しと損切遅れ。",
    },
    {
        "id": "USDJPY_140_sell_panic",
        "currency": "USDJPY",
        "folder": "USDJPY",
        "start_jst": "2024-09-16 00:00:00",
        "end_jst": "2024-09-21 23:59:00",
        "zone_lo": 139.9,
        "zone_hi": 140.3,
        "side": "sell",
        "expect": "140割れ即売り→戻りで損切。4人全敗。",
    },
]


def load_entries() -> pd.DataFrame:
    df = pd.read_csv(ENTRIES, on_bad_lines="skip")
    df["entry_dt"] = pd.to_datetime(df["entry_datetime_jst"])
    df["exit_dt"] = pd.to_datetime(df["exit_datetime_jst"])
    return df


def pip_size(currency: str) -> float:
    if currency in {"XAUUSD", "SILVER"}:
        return 0.1
    return 0.01


def cluster_loss_exits(loss: pd.DataFrame, price_col: str, tol_pips: float = 15) -> pd.DataFrame:
    rows = []
    for currency, g in loss.groupby("currency"):
        ps = pip_size(currency)
        tol = tol_pips * ps
        g = g.sort_values(price_col)
        prices = g[price_col].astype(float).tolist()
        if not prices:
            continue
        buckets: list[list[float]] = [[prices[0]]]
        bucket_idx: list[list[int]] = [[0]]
        for i in range(1, len(prices)):
            if prices[i] - buckets[-1][-1] <= tol:
                buckets[-1].append(prices[i])
                bucket_idx[-1].append(i)
            else:
                buckets.append([prices[i]])
                bucket_idx.append([i])
        for b_prices, b_idx in zip(buckets, bucket_idx):
            sub = g.iloc[b_idx]
            rows.append(
                {
                    "zone_type": "FEAR_STOP" if price_col == "exit_price" else "FEAR_ENTRY",
                    "currency": currency,
                    "side_mode": sub["side"].mode().iloc[0] if len(sub) else "",
                    "price_lo": min(b_prices),
                    "price_hi": max(b_prices),
                    "price_mid": sum(b_prices) / len(b_prices),
                    "loss_count": len(sub),
                    "student_count": sub["anon_id"].nunique(),
                    "start_jst": sub["entry_dt"].min(),
                    "end_jst": sub["exit_dt"].max(),
                    "avg_loss_pips": sub["pips"].astype(float).mean(),
                    "psychology": "損切集中・恐怖の出口",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["currency", "loss_count"], ascending=[True, False]).reset_index(drop=True)


def find_revenge_reentries(df: pd.DataFrame, hours: int = 72) -> pd.DataFrame:
    rows = []
    for (anon, sym), g in df.sort_values("entry_dt").groupby(["anon_id", "currency"]):
        g = g.reset_index(drop=True)
        for i in range(1, len(g)):
            prev, cur = g.iloc[i - 1], g.iloc[i]
            if prev["result"] != "loss":
                continue
            delta_h = (cur["entry_dt"] - prev["exit_dt"]).total_seconds() / 3600
            if delta_h > hours or cur["side"] != prev["side"]:
                continue
            rows.append(
                {
                    "anon_id": anon,
                    "currency": sym,
                    "side": cur["side"],
                    "loss_exit_dt": prev["exit_dt"],
                    "loss_exit_price": prev["exit_price"],
                    "loss_pips": prev["pips"],
                    "reentry_dt": cur["entry_dt"],
                    "reentry_price": cur["entry_price"],
                    "hours_after_loss": round(delta_h, 1),
                    "reentry_result": cur["result"],
                    "zone_type": "REVENGE",
                    "psychology": "損切後の取り返し・どテン候補",
                }
            )
    return pd.DataFrame(rows)


def _parse_mt_h1(path: Path) -> pd.DataFrame | None:
    """Parse F87104 MetaTrader-style H1 CSV (<TICKER>,<DTYYYYMMDD>,<TIME>,...)."""
    try:
        raw = pd.read_csv(path)
    except Exception:
        return None
    if raw.empty:
        return None
    cols = {c.strip("<>").lower(): c for c in raw.columns}
    if "dtyyyymmdd" not in cols or "time" not in cols:
        return None
    out = pd.DataFrame()
    out["time"] = pd.to_datetime(
        raw[cols["dtyyyymmdd"]].astype(str) + raw[cols["time"]].astype(str).str.zfill(4),
        format="%Y%m%d%H%M",
        errors="coerce",
    )
    for key, dst in (("open", "open"), ("high", "high"), ("low", "low"), ("close", "close")):
        if key not in cols:
            return None
        out[dst] = pd.to_numeric(raw[cols[key]], errors="coerce")
    out = out.dropna(subset=["time", "close"])
    return out if not out.empty else None


def _h1_paths(symbol_folder: str, year: int) -> list[Path]:
    """Resolve H1 file paths (GBYJPY typo, nested folders, root flat files)."""
    sym = symbol_folder.upper()
    token = sym[:3]  # GBY / XAU / USD
    patterns = [
        f"*{token}*H1*{year}*.csv",
        f"*{sym}*H1*{year}*.csv",
        f"*{sym}_H1_{year}.csv",
    ]
    found: list[Path] = []
    for base in [DATA_ROOT, DATA_ROOT / f"{sym}2014-2024", DATA_ROOT / "AUDJPY2014-2024"]:
        if not base.exists():
            continue
        for pat in patterns:
            for path in base.glob(pat):
                if path not in found and "H1" in path.name.upper():
                    found.append(path)
        for path in base.rglob("*.csv"):
            if path in found:
                continue
            name = path.name.upper()
            if "H1" not in name or str(year) not in name:
                continue
            if token in name.replace(" ", "") or sym in name.replace(" ", ""):
                found.append(path)
    return found


def read_h1(symbol_folder: str, year: int) -> pd.DataFrame:
    """Load H1 OHLC from F87104_test (MT CSV; timestamps align with student JST)."""
    frames = []
    for path in _h1_paths(symbol_folder, year):
        chunk = _parse_mt_h1(path)
        if chunk is not None:
            frames.append(chunk)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).drop_duplicates("time").sort_values("time")
    return df


def verify_zone(case: dict) -> dict:
    start = pd.Timestamp(case["start_jst"])
    end = pd.Timestamp(case["end_jst"])
    year = start.year
    ohlc = read_h1(case["folder"], year)
    if ohlc.empty and year + 1 <= 2026:
        ohlc = pd.concat([read_h1(case["folder"], year), read_h1(case["folder"], year + 1)], ignore_index=True)
    if ohlc.empty:
        return {**case, "ohlc_status": "NO_DATA", "chart_note": "OHLC未検出"}
    data_end = ohlc["time"].max()
    data_start = ohlc["time"].min()
    gap_note = ""
    if end > data_end:
        gap_note += f" ※CSV最終バー {data_end} より後は欠損"
    if start < data_start:
        gap_note += f" ※CSV開始 {data_start} より前は欠損"
    sub = ohlc[(ohlc["time"] >= start) & (ohlc["time"] <= end)].copy()
    if sub.empty:
        return {
            **case,
            "ohlc_status": "DATA_GAP",
            "chart_note": f"期間にバーなし（{data_start}〜{data_end}）{gap_note}",
        }
    zone_hi = case["zone_hi"]
    zone_lo = case["zone_lo"]
    touched = ((sub["high"] >= zone_lo) & (sub["low"] <= zone_hi)).sum()
    peak = float(sub["high"].max())
    trough = float(sub["low"].min())
    close_end = float(sub["close"].iloc[-1])
    if case["side"] == "buy":
        spike_then_drop = peak >= zone_hi * 0.998 and close_end < zone_lo
        verdict = "一致: 高値タッチ後下落" if spike_then_drop else "要目視: パターン不明確"
    else:
        break_then_bounce = trough <= zone_lo * 1.002 and close_end > zone_hi
        verdict = "一致: 安値割れ後戻り" if break_then_bounce else "要目視: パターン不明確"
    return {
        **case,
        "ohlc_status": "OK",
        "bars": len(sub),
        "peak": peak,
        "trough": trough,
        "close_end": close_end,
        "zone_touches": int(touched),
        "chart_note": verdict + gap_note,
        "data_range": f"{data_start} — {data_end}",
    }


def merge_stumble_fear(stumble: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in stumble.iterrows():
        if r["losses"] < r["students"]:
            continue
        rows.append(
            {
                "zone_type": "FEAR_STUMBLE_ALL_LOSS",
                "currency": r["currency"],
                "side_mode": r["side"],
                "price_lo": r["price_low"],
                "price_hi": r["price_high"],
                "price_mid": (r["price_low"] + r["price_high"]) / 2,
                "loss_count": int(r["losses"]),
                "student_count": int(r["students"]),
                "start_jst": r["start"],
                "end_jst": r["end"],
                "avg_loss_pips": math.nan,
                "psychology": "全員負け=群衆恐怖ゾーン（赤帯）",
            }
        )
    return pd.DataFrame(rows)


def write_report(
    zones: pd.DataFrame,
    revenge: pd.DataFrame,
    verifications: list[dict],
    loss_n: int,
) -> None:
    top_stop = zones[zones["zone_type"] == "FEAR_STOP"].head(12)
    top_rev = revenge.head(12)
    lines = [
        "# 恐怖・損切集中・どテン候補 — チャート照合レポート",
        "",
        "作成日: 2026-06-01",
        "",
        "## 目的",
        "",
        "人間が**恐怖を感じやすい場所**を可視化する。",
        "",
        "- **赤（FEAR_STUMBLE）**: 複数人が同じ価格帯で全敗 = 群衆の恐怖",
        "- **FEAR_STOP**: 損切り（exit）価格が集中した帯",
        "- **FEAR_ENTRY**: 不安なまま入った入口の集中",
        "- **オレンジ（REVENGE）**: 損切後72h以内の同方向再エントリー = どテン候補",
        "",
        f"データ: 受講生チャート抽出 **{loss_n}件損失** / どテン候補 **{len(revenge)}件**",
        "",
        "## Pine で見る",
        "",
        "既存（推奨）:",
        "",
        "- `pine/research/student_stumble_zones_gbpjpy_v0_5.pine` — 赤=全敗 / 青=待つ / 三角=実エントリー",
        "- `pine/research/student_stumble_zones_xauusd_v0_5.pine`",
        "- `pine/research/student_stumble_zones_usdjpy_v0_5.pine`",
        "",
        "新規（恐怖レイヤー）:",
        "",
        "- `pine/visual/fear_psychology_zones_visual.pine` — 損切出口×マーク + どテン候補オレンジ帯",
        "",
        "## OHLC 照合（F87104_test H1）",
        "",
    ]
    for v in verifications:
        lines += [
            f"### {v['id']}",
            "",
            f"- 期間: {v['start_jst']} 〜 {v['end_jst']}",
            f"- ゾーン: {v['zone_lo']} — {v['zone_hi']} ({v['side']})",
            f"- 期待: {v['expect']}",
            f"- OHLC: {v.get('ohlc_status', 'N/A')} / bars={v.get('bars', 'N/A')}",
        ]
        if v.get("ohlc_status") == "OK":
            lines += [
                f"- peak={v.get('peak'):.3f} trough={v.get('trough'):.3f} close_end={v.get('close_end'):.3f}",
                f"- zone_touches={v.get('zone_touches')} / data={v.get('data_range', '')}",
                f"- 判定: **{v.get('chart_note')}**",
            ]
        elif v.get("ohlc_status") == "DATA_GAP":
            lines += [f"- 判定: **{v.get('chart_note')}**（TradingViewで要目視）"]
        lines.append("")

    lines += [
        "## 損切出口の集中 TOP（価格帯）",
        "",
        "| currency | lo | hi | losses | students |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in top_stop.iterrows():
        lines.append(
            f"| {r['currency']} | {r['price_lo']:.3f} | {r['price_hi']:.3f} | {int(r['loss_count'])} | {int(r['student_count'])} |"
        )

    lines += [
        "",
        "## どテン候補（損切後72h・同方向）",
        "",
        f"全 **{len(revenge)}件**（うち再損切 {int((revenge['reentry_result']=='loss').sum()) if len(revenge) else 0}件）",
        "",
        "| currency | hours_after | loss_exit | reentry | result |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in top_rev.iterrows():
        lines.append(
            f"| {r['currency']} | {r['hours_after_loss']} | {r['loss_exit_price']} | {r['reentry_price']} | {r['reentry_result']} |"
        )

    lines += [
        "",
        "## 850件テキストとの一致",
        "",
        "- 損切り判断の遅れ: 302件（損失の82%）→ FEAR_STOP は「遅れて切った価格」の地図",
        "- 恐怖・不安: 92件 / 焦り・FOMO: 65件 → 赤帯・節目手前のFEAR_ENTRY",
        "- 入り直し・取り返し: P06 → REVENGE ゾーン",
        "",
        "## 実戦ルール（可視化の読み方）",
        "",
        "1. **赤帯の中** → 新規エントリー禁止（STOP）",
        "2. **FEAR_STOP が厚い価格** → ここに損切を置くと群衆と一緒に狩られる",
        "3. **青帯（待つ場所）** → 恐怖の反対。ここまで引いてから",
        "4. **オレンジ（REVENGE）** → 損切直後の同方向はどテン禁止",
        "",
        "## 出力CSV",
        "",
        f"- `{OUT_ZONES.name}`",
        f"- `{OUT_REVENGE.name}`",
        "",
    ]
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def _pine_ts(dt: pd.Timestamp) -> str:
    t = pd.Timestamp(dt)
    return f'timestamp("GMT+9",{t.year},{t.month},{t.day},{t.hour},{t.minute})'


def write_pine_overlay(zones: pd.DataFrame, revenge: pd.DataFrame, currency: str = "GBPJPY") -> None:
    """Emit TradingView overlay: magenta=FEAR_STOP, orange=REVENGE re-entry."""
    stops = zones[(zones["zone_type"] == "FEAR_STOP") & (zones["currency"] == currency)].copy()
    stops["span_h"] = (pd.to_datetime(stops["end_jst"]) - pd.to_datetime(stops["start_jst"])).dt.total_seconds() / 3600
    stops = stops[stops["loss_count"] >= 3].sort_values("loss_count", ascending=False).head(8)
    rev = revenge[revenge["currency"] == currency].head(12)

    s_lo, s_hi, s_t1, s_t2, s_n = [], [], [], [], []
    for _, r in stops.iterrows():
        s_lo.append(round(float(r["price_lo"]), 3))
        s_hi.append(round(float(r["price_hi"]), 3))
        s_t1.append(_pine_ts(r["start_jst"]))
        t2 = pd.Timestamp(r["end_jst"])
        if (t2 - pd.Timestamp(r["start_jst"])).total_seconds() > 7 * 86400:
            t2 = pd.Timestamp(r["start_jst"]) + pd.Timedelta(days=5)
        s_t2.append(_pine_ts(t2))
        s_n.append(int(r["loss_count"]))

    r_ts, r_px, r_res = [], [], []
    for _, r in rev.iterrows():
        r_ts.append(_pine_ts(r["reentry_dt"]))
        r_px.append(round(float(r["reentry_price"]), 3))
        r_res.append(1 if r["reentry_result"] == "win" else 0)

    if not r_ts:
        r_ts = [_pine_ts("2020-01-01 00:00:00")]
        r_px = [0.0]
        r_res = [0]

    body = f"""//@version=5
indicator("Fear Psychology Zones - {currency} v0.1 [Research]", overlay=true, max_boxes_count=50, max_labels_count=200)

// マゼンタ = 損切出口の集中 (FEAR_STOP) / オレンジ◇ = 損切後72h同方向再エントリー (REVENGE)
// 赤・青の全敗/待つ帯は student_stumble_zones_{currency.lower()}_v0_5.pine と併用

pairOk = syminfo.basecurrency == "{'GBP' if currency == 'GBPJPY' else currency[:3]}" and syminfo.currency == "{'JPY' if currency == 'GBPJPY' else currency[3:]}"
showStop = input.bool(true, "FEAR_STOP (損切集中)")
showRev  = input.bool(true, "REVENGE (どテン候補)")

SLo = array.from({", ".join(str(x) for x in s_lo)})
SHi = array.from({", ".join(str(x) for x in s_hi)})
ST1 = array.from({", ".join(s_t1)})
ST2 = array.from({", ".join(s_t2)})
SN  = array.from({", ".join(str(x) for x in s_n)})

RTs = array.from({", ".join(r_ts)})
RPx = array.from({", ".join(str(x) for x in r_px)})
RWin = array.from({", ".join(str(x) for x in r_res)})

if barstate.islast and pairOk
    if showStop
        for i = 0 to array.size(SLo) - 1
            box.new(array.get(ST1, i), array.get(SHi, i), array.get(ST2, i), array.get(SLo, i), xloc=xloc.bar_time, bgcolor=color.new(color.fuchsia, 82), border_color=color.new(color.fuchsia, 30))
    if showRev
        for j = 0 to array.size(RTs) - 1
            col = array.get(RWin, j) == 1 ? color.new(color.orange, 40) : color.new(color.orange, 0)
            label.new(array.get(RTs, j), array.get(RPx, j), xloc=xloc.bar_time, yloc=yloc.price, style=label.style_diamond, color=col, size=size.small, text="REV")
"""
    OUT_PINE.parent.mkdir(parents=True, exist_ok=True)
    OUT_PINE.write_text(body, encoding="utf-8")


def main() -> None:
    df = load_entries()
    loss = df[df["result"] == "loss"].copy()
    stumble = pd.read_csv(STUMBLE)

    zones_stop = cluster_loss_exits(loss, "exit_price", tol_pips=20)
    zones_entry = cluster_loss_exits(loss, "entry_price", tol_pips=25)
    zones_stumble = merge_stumble_fear(stumble[stumble["loss_rate"] >= 1.0])
    zones = pd.concat([zones_stumble, zones_stop, zones_entry], ignore_index=True)
    zones.to_csv(OUT_ZONES, index=False)

    revenge = find_revenge_reentries(df, hours=72)
    revenge.to_csv(OUT_REVENGE, index=False)

    verifications = [verify_zone(c) for c in VERIFY_CASES]
    write_report(zones, revenge, verifications, len(loss))
    write_pine_overlay(zones, revenge, "GBPJPY")

    print(f"Zones: {OUT_ZONES} ({len(zones)} rows)")
    print(f"Pine: {OUT_PINE}")
    print(f"Revenge: {OUT_REVENGE} ({len(revenge)} rows)")
    print(f"Report: {OUT_REPORT}")
    for v in verifications:
        print(f"  {v['id']}: {v.get('ohlc_status')} — {v.get('chart_note', '')}")


if __name__ == "__main__":
    main()

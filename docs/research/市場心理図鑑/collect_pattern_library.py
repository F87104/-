#!/usr/bin/env python3
"""
Collect multiple real OHLC examples per psychology pattern into a pattern library.

Output:
  collection/manifest.json   — full metadata
  collection/events.csv      — spreadsheet-friendly index
  collection/index.md        — browsable gallery by pattern
  collection/images/{id}_{title}/{symbol}_{datetime}.png
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
COLLECTION_DIR = THIS_DIR / "collection"
IMAGES_DIR = COLLECTION_DIR / "images"

sys.path.insert(0, str(THIS_DIR))
from atlas_tv import render_real_chart  # noqa: E402
from render_real_events import (  # noqa: E402
    PATTERN_META,
    SCANNERS,
    EventHit,
    add_base,
    build_spec,
    load_symbol_h4,
)


def dedupe_hits(hits: list[EventHit], min_gap: int) -> list[EventHit]:
    """Keep highest-score events with minimum bar separation per symbol."""
    ordered = sorted(hits, key=lambda h: h.score, reverse=True)
    kept: list[EventHit] = []
    by_symbol: dict[str, list[int]] = defaultdict(list)
    for h in ordered:
        if any(abs(h.signal_i - prev) < min_gap for prev in by_symbol[h.symbol]):
            continue
        kept.append(h)
        by_symbol[h.symbol].append(h.signal_i)
    return kept


def select_for_pattern(
    hits: list[EventHit],
    max_per_symbol: int,
    max_per_pattern: int,
    min_gap: int,
) -> list[EventHit]:
    deduped = dedupe_hits(hits, min_gap)
    by_symbol: dict[str, list[EventHit]] = defaultdict(list)
    for h in deduped:
        if len(by_symbol[h.symbol]) < max_per_symbol:
            by_symbol[h.symbol].append(h)
    merged = [h for group in by_symbol.values() for h in group]
    merged.sort(key=lambda h: h.score, reverse=True)
    return merged[:max_per_pattern]


def pattern_dir_name(pattern_id: str) -> str:
    title = PATTERN_META[pattern_id][0]
    return f"{pattern_id}_{title}"


def write_index(events: list[dict]) -> None:
    by_pattern: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_pattern[e["pattern_id"]].append(e)

    lines = [
        "# パターンライブラリ — 収集一覧",
        "",
        "> [← 図鑑トップ](README.md) ／ [代表1枚ずつ](real_gallery.md) ／ [収集手順](SETUP_COLLECTION.md)",
        "",
        f"**収集件数:** {len(events)} イベント ／ **パターン数:** {len(by_pattern)}",
        "",
        "| パターン | 件数 |",
        "|---|---:|",
    ]
    for pid in sorted(by_pattern.keys()):
        title = PATTERN_META[pid][0]
        lines.append(f"| [{pid} {title}](#{pid}-{title}) | {len(by_pattern[pid])} |")

    lines.append("")
    for pid in sorted(by_pattern.keys()):
        title = PATTERN_META[pid][0]
        items = by_pattern[pid]
        lines += [
            f"## {pid} {title}",
            "",
            f"Vol.1: [詳細説明](vol01_core_patterns.md#{pid.zfill(2)}-{title})",
            "",
            "| 通貨 | 時刻 | スコア | チャート |",
            "|---|---|---:|---|",
        ]
        for e in items:
            rel = e["image"].replace("collection/", "")
            lines.append(
                f"| {e['symbol']} | {e['event_time'][:16]} | {e['score']:.2f} "
                f"| [📈]({rel}) |"
            )
        lines.append("")
        for e in items[:6]:
            rel = e["image"]
            lines.append(f"### {e['symbol']} · {e['event_time'][:16]}")
            lines.append("")
            lines.append(f"![{title}]({rel})")
            lines.append("")
        if len(items) > 6:
            lines.append(f"*…他 {len(items) - 6} 件は CSV / manifest を参照*")
            lines.append("")
        lines.append("---")
        lines.append("")

    (COLLECTION_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_csv(events: list[dict]) -> None:
    if not events:
        return
    fields = ["pattern_id", "title", "symbol", "timeframe", "event_time", "score", "image", "meta"]
    with (COLLECTION_DIR / "events.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in events:
            row = {k: e.get(k, "") for k in fields}
            row["meta"] = json.dumps(e.get("meta", {}), ensure_ascii=False)
            w.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect psychology pattern chart library")
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--require-local", action="store_true")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["XAUUSD", "USDJPY", "SILVER", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY"],
    )
    parser.add_argument("--patterns", nargs="+", default=None, help="Pattern IDs e.g. 01 02")
    parser.add_argument("--max-per-symbol", type=int, default=3)
    parser.add_argument("--max-per-pattern", type=int, default=10)
    parser.add_argument("--min-gap", type=int, default=36, help="Min H4 bars between events (same symbol)")
    parser.add_argument("--no-render", action="store_true", help="Catalog only, skip PNG generation")
    args = parser.parse_args()

    if args.data_root and args.data_root.exists():
        os.environ["F87104_DATA_ROOT"] = str(args.data_root.resolve())
        print(f"data root: {args.data_root.resolve()}")

    data: dict[str, pd.DataFrame] = {}
    data_sources: dict[str, dict] = {}
    for sym in args.symbols:
        h4, source = load_symbol_h4(sym)
        if h4 is not None and len(h4) > 150:
            data[sym] = add_base(h4)
            data_sources[sym] = {
                "source": source,
                "bars": len(h4),
                "from": h4.index.min().isoformat(),
                "to": h4.index.max().isoformat(),
            }
            print(f"loaded {sym}: {len(h4)} H4 bars [{source}]")
        else:
            print(f"skip {sym}")

    if args.require_local:
        bad = [s for s, m in data_sources.items() if not m["source"].startswith("F87104_test")]
        if bad or not data_sources:
            raise SystemExit(f"F87104_test required but missing for: {', '.join(bad or args.symbols)}")

    pattern_ids = args.patterns or sorted(SCANNERS.keys())
    COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    all_events: list[dict] = []
    stats: dict[str, dict] = {}

    for pid in pattern_ids:
        if pid not in SCANNERS:
            print(f"skip unknown pattern {pid}")
            continue
        scanner = SCANNERS[pid]
        raw_hits: list[EventHit] = []
        for sym, df in data.items():
            raw_hits.extend(scanner(df, sym))

        gap = args.min_gap * (2 if pid == "03" else 1)
        selected = select_for_pattern(raw_hits, args.max_per_symbol, args.max_per_pattern, gap)
        stats[pid] = {"raw": len(raw_hits), "selected": len(selected)}

        pdir = IMAGES_DIR / pattern_dir_name(pid)
        pdir.mkdir(parents=True, exist_ok=True)

        for hit in selected:
            fname = f"{hit.symbol}_{hit.time.strftime('%Y%m%d_%H%M')}.png"
            rel_image = f"collection/images/{pattern_dir_name(pid)}/{fname}"
            entry = {
                "pattern_id": pid,
                "title": PATTERN_META[pid][0],
                "symbol": hit.symbol,
                "timeframe": "H4",
                "event_time": hit.time.isoformat(),
                "score": hit.score,
                "image": rel_image,
                "meta": hit.meta,
            }
            if not args.no_render:
                spec = build_spec(hit, data[hit.symbol])
                render_real_chart(spec, pdir / fname)
            all_events.append(entry)

        print(f"pattern {pid} {PATTERN_META[pid][0]}: raw={len(raw_hits)} → kept={len(selected)}")

    manifest = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "settings": {
            "max_per_symbol": args.max_per_symbol,
            "max_per_pattern": args.max_per_pattern,
            "min_gap": args.min_gap,
            "symbols": list(data.keys()),
            "patterns": pattern_ids,
        },
        "data_sources": data_sources,
        "stats": stats,
        "total_events": len(all_events),
        "events": all_events,
    }
    (COLLECTION_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_csv(all_events)
    write_index(all_events)
    print(f"\ntotal: {len(all_events)} events")
    print(f"manifest: {COLLECTION_DIR / 'manifest.json'}")
    print(f"index:    {COLLECTION_DIR / 'index.md'}")
    print(f"csv:      {COLLECTION_DIR / 'events.csv'}")


if __name__ == "__main__":
    main()

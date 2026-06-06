#!/usr/bin/env python3
"""Post rotating trade-lesson reminders to Slack.

Reads lessons from docs/trade_diary/lessons/reminders.json and open-position
context from practice/index.csv. Intended for GitHub Actions cron or local cron.

Environment:
  SLACK_WEBHOOK_URL  — Slack Incoming Webhook URL (required unless --dry-run)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LESSONS_PATH = ROOT / "docs" / "trade_diary" / "lessons" / "reminders.json"
INDEX_PATH = ROOT / "docs" / "trade_diary" / "practice" / "index.csv"
PATTERN_LOG_PATH = ROOT / "docs" / "trade_diary" / "practice" / "early_stop_pattern_log.csv"
JST = ZoneInfo("Asia/Tokyo")

# Thursday=3, Friday=4 (Mon=0)
INDICATOR_WEEKDAYS = {3, 4}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_open_positions() -> list[dict[str, str]]:
    if not INDEX_PATH.exists():
        return []
    rows: list[dict[str, str]] = []
    with INDEX_PATH.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status", "").lower() == "open":
                rows.append(row)
    return rows


def load_pattern_notes() -> dict[str, str]:
    if not PATTERN_LOG_PATH.exists():
        return {}
    notes: dict[str, str] = {}
    with PATTERN_LOG_PATH.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            entry_id = row.get("entry_id", "")
            note = row.get("note", "")
            if entry_id and note:
                notes[entry_id] = note
    return notes


def pick_lesson(lessons: list[dict], now_jst: datetime, force_id: str | None) -> dict:
    if force_id:
        for lesson in lessons:
            if lesson["id"] == force_id:
                return lesson
        raise SystemExit(f"Unknown lesson id: {force_id}")

    # Thu/Fri: prioritize employment-stats rule (E05)
    if now_jst.weekday() in INDICATOR_WEEKDAYS:
        for lesson in lessons:
            if lesson.get("pattern") == "E05":
                return lesson

    # Rotate by calendar day so morning/evening on same day share one focus lesson
    index = now_jst.timetuple().tm_yday % len(lessons)
    return lessons[index]


def format_open_positions(
    positions: list[dict[str, str]], pattern_notes: dict[str, str]
) -> str | None:
    if not positions:
        return None
    lines = ["*建玉中（要監視）*"]
    for pos in positions:
        entry_id = pos.get("entry_id", "")
        symbol = pos.get("symbol", "")
        side = pos.get("side", "")
        pnl = pos.get("unrealized_pnl_jpy", "")
        note = pattern_notes.get(entry_id, pos.get("note", ""))
        pnl_str = f" 評価損益 {int(float(pnl)):+,}円" if pnl else ""
        lines.append(f"• {symbol} {side}{pnl_str}")
        if note:
            short = note if len(note) <= 80 else note[:77] + "..."
            lines.append(f"  _{short}_")
    return "\n".join(lines)


def build_message(
    lesson: dict,
    anchor: dict,
    open_block: str | None,
    now_jst: datetime,
) -> str:
    parts = [
        f"📋 *トレード反省リマインド*（{now_jst.strftime('%Y-%m-%d %H:%M')} JST）",
        "",
        f"*{lesson['id']} / {lesson.get('pattern', '')}: {lesson['title']}*",
        lesson["body"],
        "",
        f"→ *今日の行動:* {lesson['action']}",
        "",
        f"_アンカー: {anchor['date']} {anchor['symbol']} — {anchor['story']}_",
    ]
    if open_block:
        parts.extend(["", open_block])
    parts.extend(
        [
            "",
            f"<{anchor['diary_url']}|6/3 日誌> | "
            "<https://github.com/F87104/-/blob/main/docs/trade_diary/reference/signal_review_protocol.md|シグナル判断> | "
            "<https://github.com/F87104/-/blob/main/docs/research/early_stop_loss_patterns_2026-06-06.md|E01-E09 研究>",
        ]
    )
    return "\n".join(parts)


def post_slack(webhook_url: str, text: str) -> None:
    payload = json.dumps({"text": text, "mrkdwn": True}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        if body != "ok":
            raise RuntimeError(f"Unexpected Slack response: {body!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send trade lesson reminder to Slack")
    parser.add_argument("--dry-run", action="store_true", help="Print message, do not post")
    parser.add_argument("--lesson-id", help="Force a specific lesson id (e.g. R03)")
    parser.add_argument(
        "--webhook-url",
        default=os.environ.get("SLACK_WEBHOOK_URL", ""),
        help="Slack webhook URL (default: SLACK_WEBHOOK_URL env)",
    )
    args = parser.parse_args()

    data = load_json(LESSONS_PATH)
    lessons: list[dict] = data["lessons"]
    anchor: dict = data["anchor_case"]

    now_jst = datetime.now(JST)
    lesson = pick_lesson(lessons, now_jst, args.lesson_id)
    open_block = format_open_positions(load_open_positions(), load_pattern_notes())
    message = build_message(lesson, anchor, open_block, now_jst)

    if args.dry_run:
        print(message)
        return 0

    if not args.webhook_url:
        print("SLACK_WEBHOOK_URL is not set. Use --dry-run to preview.", file=sys.stderr)
        return 1

    try:
        post_slack(args.webhook_url, message)
    except urllib.error.URLError as exc:
        print(f"Failed to post to Slack: {exc}", file=sys.stderr)
        return 1

    print(f"Posted lesson {lesson['id']} at {now_jst.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

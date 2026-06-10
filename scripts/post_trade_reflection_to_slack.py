#!/usr/bin/env python3
"""Post trade-diary reflection points (反省点) to a Slack thread."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIARY_DIR = ROOT / "docs" / "trade_diary"
PRACTICE_DIR = DIARY_DIR / "practice"
INDEX_CSV = PRACTICE_DIR / "index.csv"
ENTRIES_DIR = PRACTICE_DIR / "entries"
CONFIG_PATH = ROOT / "config" / "slack_reflection.json"


@dataclass(frozen=True)
class DiaryEntry:
    entry_id: str
    symbol: str
    side: str
    status: str
    markdown_path: Path
    title: str


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def load_entries(*, status_filter: str | None = None) -> list[DiaryEntry]:
    entries: list[DiaryEntry] = []
    with INDEX_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if status_filter and row["status"] != status_filter:
                continue
            markdown_path = DIARY_DIR / row["markdown_path"]
            if not markdown_path.exists():
                continue
            title = markdown_path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            entries.append(
                DiaryEntry(
                    entry_id=row["entry_id"],
                    symbol=row["symbol"],
                    side=row["side"],
                    status=row["status"],
                    markdown_path=markdown_path,
                    title=title,
                )
            )
    return entries


def extract_reflection_section(markdown_text: str) -> str | None:
    match = re.search(r"^## 反省点\s*\n(.*?)(?=^## |\Z)", markdown_text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    body = match.group(1).strip()
    return body or None


def markdown_table_to_lines(table_text: str) -> list[str]:
    rows: list[list[str]] = []
    for line in table_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return []

    lines: list[str] = []
    for row in rows[1:] if len(rows) > 1 else rows:
        if len(row) >= 2:
            lines.append(f"• *{row[0]}*: {row[1]}")
        elif row:
            lines.append(f"• {row[0]}")
    return lines


def markdown_to_slack(section: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(part.strip() for part in paragraph).strip()
        if text:
            output.append(text)
        paragraph.clear()

    def flush_table() -> None:
        nonlocal table_lines
        if not table_lines:
            return
        output.extend(markdown_table_to_lines("\n".join(table_lines)))
        table_lines = []

    for raw_line in section.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            flush_table()
            if in_code:
                output.append("```\n" + "\n".join(code_lines) + "\n```")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("|"):
            flush_paragraph()
            table_lines.append(line)
            continue

        flush_table()

        if line.startswith("### "):
            flush_paragraph()
            output.append(f"\n*{line[4:].strip()}*")
            continue

        if line.startswith("> "):
            flush_paragraph()
            output.append(f"> {line[2:].strip()}")
            continue

        if line.startswith("- "):
            flush_paragraph()
            output.append(f"• {line[2:].strip()}")
            continue

        if not line.strip():
            flush_paragraph()
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_table()
    if in_code and code_lines:
        output.append("```\n" + "\n".join(code_lines) + "\n```")

    text = "\n".join(output)
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_message(entry: DiaryEntry, reflection: str) -> str:
    slack_body = markdown_to_slack(reflection)
    status_label = "建玉中" if entry.status == "open" else "決済済"
    header = (
        f"📓 *トレード反省リマインド* — `{entry.entry_id}`\n"
        f"*{entry.title}* ／ {entry.symbol} {entry.side} ／ {status_label}\n"
        f"---\n"
    )
    footer = (
        f"\n---\n"
        f"出典: `{entry.markdown_path.relative_to(DIARY_DIR)}`"
    )
    return header + slack_body + footer


def pick_entry(
    entries: list[DiaryEntry],
    *,
    entry_id: str | None,
    rotation: str,
    rotation_date: date,
) -> DiaryEntry | None:
    candidates: list[tuple[DiaryEntry, str]] = []
    for entry in entries:
        reflection = extract_reflection_section(entry.markdown_path.read_text(encoding="utf-8"))
        if reflection:
            candidates.append((entry, reflection))

    if not candidates:
        return None

    if entry_id:
        for entry, _ in candidates:
            if entry.entry_id == entry_id:
                return entry
        raise SystemExit(f"entry_id {entry_id} not found or has no 反省点 section")

    if len(candidates) == 1 or rotation == "all":
        return candidates[0][0]

    index = rotation_date.toordinal() % len(candidates)
    return candidates[index][0]


def post_to_slack(
    *,
    token: str,
    channel: str,
    text: str,
    thread_ts: str | None,
    dry_run: bool,
) -> dict:
    payload = {
        "channel": channel,
        "text": text,
        "mrkdwn": True,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return {"ok": True, "dry_run": True}

    request = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Slack HTTP error {exc.code}: {detail}") from exc

    if not body.get("ok"):
        raise SystemExit(f"Slack API error: {body.get('error', body)}")
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry-id", help="Post a specific entry_id (default: rotate among matches)")
    parser.add_argument(
        "--status",
        choices=("open", "closed", "all"),
        default=None,
        help="Filter entries by status (default: config entry_filter or open)",
    )
    parser.add_argument(
        "--rotation",
        choices=("daily", "all"),
        default=None,
        help="daily = one entry per day, all = first available entry",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload without posting")
    parser.add_argument("--list", action="store_true", help="List entries that have 反省点")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()

    status_filter = args.status or config.get("entry_filter", "open")
    if status_filter == "all":
        status_filter = None

    entries = load_entries(status_filter=status_filter)
    reflection_entries = []
    for entry in entries:
        reflection = extract_reflection_section(entry.markdown_path.read_text(encoding="utf-8"))
        if reflection:
            reflection_entries.append((entry, reflection))

    if args.list:
        for entry, _ in reflection_entries:
            print(f"{entry.entry_id}\t{entry.status}\t{entry.title}")
        return 0

    if not reflection_entries:
        print("No diary entries with 反省点 found.", file=sys.stderr)
        return 1

    rotation = args.rotation or config.get("rotation", "daily")
    selected = pick_entry(
        [entry for entry, _ in reflection_entries],
        entry_id=args.entry_id,
        rotation=rotation,
        rotation_date=date.today(),
    )
    assert selected is not None

    reflection = extract_reflection_section(selected.markdown_path.read_text(encoding="utf-8"))
    assert reflection is not None
    message = build_message(selected, reflection)

    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_ID") or config.get("channel_id")
    thread_ts = os.environ.get("SLACK_THREAD_TS") or config.get("thread_ts")

    if not args.dry_run and not token:
        raise SystemExit("SLACK_BOT_TOKEN is required (unless --dry-run)")
    if not args.dry_run and not channel:
        raise SystemExit("SLACK_CHANNEL_ID or config/slack_reflection.json channel_id is required")

    result = post_to_slack(
        token=token or "",
        channel=channel or "",
        text=message,
        thread_ts=thread_ts,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(f"\nWould post entry: {selected.entry_id}")
    else:
        print(f"Posted {selected.entry_id} to Slack (ts={result.get('ts')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

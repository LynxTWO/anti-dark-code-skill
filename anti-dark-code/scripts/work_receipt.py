#!/usr/bin/env python3
"""Deterministic per-session work measure from agent-session transcripts.

Sums model token usage, tool calls, and the covered time window from one or
more session transcript files and prints a compact WORK line suitable for a
pull-request body, plus a breakdown. Token counts are measured; any
human-equivalent effort figure a person adds alongside is an estimate and must
be labeled as one. Measured numbers and estimates never blend.

Supported input: Claude Code session transcripts (JSON Lines; one JSON object
per line; usage under message.usage, tool calls as message.content[] entries
with type "tool_use", timestamps as offset-aware ISO 8601 strings). Other
hosts can emit the same shape or extend this script; the output format is
host-neutral.

No network access, no repository access, no execution of transcript content.
Transcript text is untrusted data and is never printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_when(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def summarize(paths: list[Path], since: datetime | None, until: datetime | None) -> dict[str, object]:
    totals = {
        "messages": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "cache_write_tokens": 0,
        "cache_read_tokens": 0,
        "output_tokens": 0,
    }
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    malformed_lines = 0

    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    malformed_lines += 1
                    continue
                stamp_raw = row.get("timestamp")
                if not isinstance(stamp_raw, str):
                    continue
                try:
                    stamp = parse_when(stamp_raw)
                except ValueError:
                    malformed_lines += 1
                    continue
                if since is not None and stamp < since:
                    continue
                if until is not None and stamp > until:
                    continue
                if first_ts is None or stamp < first_ts:
                    first_ts = stamp
                if last_ts is None or stamp > last_ts:
                    last_ts = stamp
                message = row.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if isinstance(content, list):
                    totals["tool_calls"] += sum(
                        1 for item in content if isinstance(item, dict) and item.get("type") == "tool_use"
                    )
                usage = message.get("usage")
                if isinstance(usage, dict):
                    totals["messages"] += 1
                    totals["input_tokens"] += int(usage.get("input_tokens") or 0)
                    totals["cache_write_tokens"] += int(usage.get("cache_creation_input_tokens") or 0)
                    totals["cache_read_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
                    totals["output_tokens"] += int(usage.get("output_tokens") or 0)

    totals["billable_new_tokens"] = (
        int(totals["input_tokens"]) + int(totals["cache_write_tokens"]) + int(totals["output_tokens"])
    )
    totals["first_ts"] = first_ts.isoformat() if first_ts else None
    totals["last_ts"] = last_ts.isoformat() if last_ts else None
    totals["malformed_lines"] = malformed_lines
    return totals


def format_receipt(totals: dict[str, object]) -> str:
    work_line = (
        f"WORK: {totals['output_tokens']} output tokens, "
        f"{totals['billable_new_tokens']} new-context tokens, "
        f"{totals['tool_calls']} tool calls, "
        f"{totals['first_ts'] or 'no rows'} -> {totals['last_ts'] or 'no rows'}"
    )
    breakdown = (
        f"  breakdown: input={totals['input_tokens']} "
        f"cache_write={totals['cache_write_tokens']} "
        f"cache_read={totals['cache_read_tokens']} "
        f"output={totals['output_tokens']} "
        f"messages={totals['messages']}"
    )
    lines = [work_line, breakdown]
    if totals.get("malformed_lines"):
        lines.append(f"  note: {totals['malformed_lines']} malformed line(s) skipped")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a measured WORK receipt from agent-session transcripts."
    )
    parser.add_argument("transcripts", nargs="+", help="Session transcript .jsonl files")
    parser.add_argument("--since", help="Include rows at or after this ISO 8601 time")
    parser.add_argument("--until", help="Include rows at or before this ISO 8601 time")
    parser.add_argument("--json", action="store_true", help="Emit the totals as JSON instead of text")
    args = parser.parse_args(argv)

    paths = [Path(item) for item in args.transcripts]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        print("work_receipt: transcript not found: " + ", ".join(missing), file=sys.stderr)
        return 2

    since = parse_when(args.since) if args.since else None
    until = parse_when(args.until) if args.until else None
    totals = summarize(paths, since, until)
    if args.json:
        print(json.dumps(totals, sort_keys=True))
    else:
        print(format_receipt(totals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

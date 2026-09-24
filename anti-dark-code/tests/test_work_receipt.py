from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "work_receipt.py"
spec = importlib.util.spec_from_file_location("work_receipt", MODULE_PATH)
work_receipt = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(work_receipt)


def write_transcript(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def usage_row(stamp: str, output_tokens: int, tool_uses: int = 0) -> dict:
    content = [{"type": "tool_use", "name": "Bash"}] * tool_uses
    return {
        "timestamp": stamp,
        "message": {
            "content": content,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 1000,
                "output_tokens": output_tokens,
            },
        },
    }


def split_response_rows(message_id: str, stamp: str, output_tokens: int, tool_ids: list[str]) -> list[dict]:
    """One response written the way Claude Code writes it: a row per content
    block (thinking, text, each tool_use), each row repeating the full usage."""
    blocks = [{"type": "thinking", "thinking": "..."}, {"type": "text", "text": "..."}]
    blocks += [{"type": "tool_use", "id": tool_id, "name": "Bash"} for tool_id in tool_ids]
    return [
        {
            "timestamp": stamp,
            "uuid": f"{message_id}-row-{index}",
            "message": {
                "id": message_id,
                "content": [block],
                "usage": {
                    "input_tokens": 3,
                    "cache_creation_input_tokens": 40,
                    "cache_read_input_tokens": 500,
                    "output_tokens": output_tokens,
                },
            },
        }
        for index, block in enumerate(blocks)
    ]


class WorkReceiptTests(unittest.TestCase):
    def test_response_split_across_rows_counts_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            rows = split_response_rows("msg_1", "2026-09-24T10:00:00Z", 50, ["toolu_1", "toolu_2"])
            rows += split_response_rows("msg_2", "2026-09-24T10:01:00Z", 7, [])
            write_transcript(path, rows)
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["messages"], 2)
            self.assertEqual(totals["tool_calls"], 2)
            self.assertEqual(totals["output_tokens"], 57)
            self.assertEqual(totals["input_tokens"], 6)
            self.assertEqual(totals["cache_write_tokens"], 80)
            self.assertEqual(totals["cache_read_tokens"], 1000)
            self.assertEqual(totals["billable_new_tokens"], 6 + 80 + 57)
            self.assertEqual(totals["usage_rows"], 6)
            receipt = work_receipt.format_receipt(totals)
            self.assertIn("WORK: 57 output tokens, 143 new-context tokens, 2 tool calls", receipt)
            self.assertIn("messages=2 usage_rows=6", receipt)

    def test_largest_usage_snapshot_wins_for_one_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            first = split_response_rows("msg_1", "2026-09-24T10:00:00Z", 5, [])[0]
            later = split_response_rows("msg_1", "2026-09-24T10:00:02Z", 12, [])[1]
            write_transcript(path, [first, later])
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["messages"], 1)
            self.assertEqual(totals["output_tokens"], 12)

    def test_copied_transcript_counts_each_response_and_tool_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rows = split_response_rows("msg_1", "2026-09-24T10:00:00Z", 50, ["toolu_1"])
            original = Path(tmp) / "session.jsonl"
            copy = Path(tmp) / "session-copy.jsonl"
            write_transcript(original, rows)
            write_transcript(copy, rows)
            single = work_receipt.summarize([original], None, None)
            both = work_receipt.summarize([original, copy], None, None)
            for name in ("messages", "tool_calls", "output_tokens", "billable_new_tokens"):
                self.assertEqual(both[name], single[name], name)
            self.assertEqual(both["usage_rows"], 2 * single["usage_rows"])

    def test_rows_without_ids_count_individually(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            anonymous = usage_row("2026-09-24T10:00:00Z", 4, tool_uses=1)
            with_uuid = dict(usage_row("2026-09-24T10:00:01Z", 6), uuid="row-a")
            other_uuid = dict(usage_row("2026-09-24T10:00:01Z", 6), uuid="row-b")
            write_transcript(path, [anonymous, anonymous, with_uuid, other_uuid])
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["messages"], 4)
            self.assertEqual(totals["output_tokens"], 4 + 4 + 6 + 6)
            self.assertEqual(totals["tool_calls"], 2)

    def test_non_object_json_lines_are_malformed_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(
                "[1, 2]\n\"text\"\n" + json.dumps(usage_row("2026-08-20T10:00:00Z", 9)) + "\n",
                encoding="utf-8",
            )
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["malformed_lines"], 2)
            self.assertEqual(totals["output_tokens"], 9)

    def test_sums_usage_tool_calls_and_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_transcript(path, [
                usage_row("2026-08-20T10:00:00Z", 50, tool_uses=2),
                usage_row("2026-08-20T10:05:00Z", 70, tool_uses=1),
                {"timestamp": "2026-08-20T10:06:00Z", "type": "queue-operation"},
            ])
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["messages"], 2)
            self.assertEqual(totals["tool_calls"], 3)
            self.assertEqual(totals["output_tokens"], 120)
            self.assertEqual(totals["billable_new_tokens"], 10 * 2 + 100 * 2 + 120)
            self.assertEqual(totals["cache_read_tokens"], 2000)
            receipt = work_receipt.format_receipt(totals)
            self.assertIn("WORK: 120 output tokens", receipt)
            self.assertIn("3 tool calls", receipt)

    def test_window_filters_and_offset_equivalence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_transcript(path, [
                usage_row("2026-08-20T09:00:00Z", 5),
                usage_row("2026-08-20T06:30:00-04:00", 7),
                usage_row("2026-08-20T11:00:00Z", 11),
            ])
            totals = work_receipt.summarize(
                [path],
                work_receipt.parse_when("2026-08-20T10:00:00Z"),
                None,
            )
            self.assertEqual(totals["messages"], 2)
            self.assertEqual(totals["output_tokens"], 18)

    def test_malformed_lines_are_counted_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            path.write_text(
                "not json at all\n" + json.dumps(usage_row("2026-08-20T10:00:00Z", 9)) + "\n",
                encoding="utf-8",
            )
            totals = work_receipt.summarize([path], None, None)
            self.assertEqual(totals["malformed_lines"], 1)
            self.assertEqual(totals["output_tokens"], 9)
            self.assertIn("1 malformed line(s) skipped", work_receipt.format_receipt(totals))

    def test_missing_transcript_returns_error_exit(self) -> None:
        self.assertEqual(work_receipt.main(["/nonexistent/definitely-missing.jsonl"]), 2)


if __name__ == "__main__":
    unittest.main()

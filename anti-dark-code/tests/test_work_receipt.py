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


class WorkReceiptTests(unittest.TestCase):
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

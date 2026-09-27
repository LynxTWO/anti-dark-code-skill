"""Independent ledger examples: real work is observed once, never replayed."""
from __future__ import annotations

import importlib.util
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adc_usage.py"
STAMP = "2099-01-01T00:00:00Z"


def module():
    spec = importlib.util.spec_from_file_location("adc_usage", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def rows(response="answer-one", total=17, output=5):
    return [
        {"timestamp": STAMP, "type": "session_meta", "payload": {
            "id": "thread-one", "session_id": "session-one",
            "model_provider": "openai", "cli_version": "0.153.0",
            "cwd": "private-repo-name", "base_instructions": "private prompt"}},
        {"timestamp": STAMP, "type": "turn_context", "payload": {
            "turn_id": "turn-one", "root_turn_id": "root-one", "model": "test-standard", "effort": "high"}},
        {"timestamp": STAMP, "type": "token_usage_record", "payload": {
            "thread_id": "thread-one", "session_id": "session-one", "turn_id": "turn-one",
            "root_turn_id": "root-one", "response_id": response,
            "usage": {"input_tokens": 12, "cached_input_tokens": 3,
                      "cache_write_input_tokens": 2, "output_tokens": output,
                      "reasoning_output_tokens": 1, "total_tokens": total}}},
    ]


class UsageLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.directory = self.root / "private-ledger"

    def initialize(self, host="codex"):
        self.adc = module()
        return self.adc.init_ledger(self.directory, {host: self.source}, opt_in=True)

    def write(self, content=None, name="run.jsonl", mode="w"):
        with (self.source / name).open(mode, encoding="utf-8") as stream:
            for row in rows() if content is None else content:
                stream.write(json.dumps(row) + "\n")

    def test_requires_explicit_opt_in_and_never_overwrites_configuration(self):
        adc = module()
        with self.assertRaises(ValueError):
            adc.init_ledger(self.directory, {"codex": self.source}, opt_in=False)
        self.assertFalse(self.directory.exists())
        self.initialize()
        before = (self.directory / "config.json").read_bytes()
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertEqual(before, (self.directory / "config.json").read_bytes())

    def test_repeated_ticks_and_copied_transcripts_count_each_response_once(self):
        self.initialize()
        self.write()
        self.assertEqual(1, self.adc.collect(self.directory)["inserted"])
        self.assertEqual(0, self.adc.collect(self.directory)["inserted"])
        self.write(name="copied.jsonl")
        self.assertEqual(0, self.adc.collect(self.directory)["inserted"])
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["events"])
        usage = report["strata"][0]["usage"]
        self.assertEqual({"known_subtotal": 17, "missing_events": 0}, usage["provider_total_tokens"])
        self.assertEqual(12, usage["input_tokens"]["known_subtotal"])
        self.assertIsNone(report["savings"])
        self.assertIsNone(report["subscription_cost"])
        for private in ("private-repo-name", "private prompt", str(self.source), "thread-one"):
            self.assertNotIn(private, json.dumps(report))
            self.assertNotIn(private.encode(), (self.directory / "usage.sqlite3").read_bytes())

    def test_partial_line_waits_and_new_response_is_incremental(self):
        self.initialize()
        self.write()
        self.adc.collect(self.directory)
        text = json.dumps(rows(response="answer-two")[-1])
        with (self.source / "run.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(text[:50])
        self.assertEqual(0, self.adc.collect(self.directory)["inserted"])
        with (self.source / "run.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(text[50:] + "\n")
        self.assertEqual(1, self.adc.collect(self.directory)["inserted"])
        report = self.adc.summary(self.directory)
        self.assertEqual(34, report["strata"][0]["usage"]["provider_total_tokens"]["known_subtotal"])
        self.assertEqual(1, len(report["tasks"]))

    def test_pre_opt_in_usage_is_excluded_but_context_can_be_reused(self):
        self.initialize()
        old = rows()
        for row in old:
            row["timestamp"] = "2000-01-01T00:00:00Z"
        self.write(old + [rows(response="new-answer")[-1]])
        self.adc.collect(self.directory)
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["events"])
        self.assertEqual("test-standard", report["strata"][0]["model"])

    def test_conflicting_record_rolls_back_offsets_and_all_events(self):
        self.initialize()
        self.write()
        self.adc.collect(self.directory)
        self.write([rows("valid-new")[-1], rows(total=16, output=4)[-1]], mode="a")
        with self.assertRaises(ValueError):
            self.adc.collect(self.directory)
        self.assertEqual(1, self.adc.summary(self.directory)["events"])
        with self.assertRaises(ValueError):
            self.adc.collect(self.directory)

    def test_arithmetic_contradiction_and_unknown_are_distinct(self):
        self.initialize()
        self.write(rows(total=999))
        with self.assertRaises(ValueError):
            self.adc.collect(self.directory)
        self.assertEqual(0, self.adc.summary(self.directory)["events"])
        missing = rows()
        del missing[-1]["payload"]["usage"]["cached_input_tokens"]
        self.write(missing)
        self.adc.collect(self.directory)
        self.assertEqual({"known_subtotal": 0, "missing_events": 1},
                         self.adc.summary(self.directory)["strata"][0]["usage"]["cache_read_input_tokens"])

    def test_claude_stream_growth_updates_one_record_without_summing(self):
        self.initialize("claude")
        row = {"timestamp": STAMP, "type": "assistant", "sessionId": "session-a",
               "requestId": "request-a", "message": {"id": "message-a", "model": "test-model",
               "usage": {"input_tokens": 10, "cache_creation_input_tokens": 4,
                         "cache_read_input_tokens": 6, "output_tokens": 2}}}
        self.write([row])
        self.adc.collect(self.directory)
        row["message"]["usage"]["output_tokens"] = 7
        self.write([row], mode="a")
        result = self.adc.collect(self.directory)
        self.assertEqual(1, result["updated"])
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["events"])
        self.assertEqual(27, report["strata"][0]["usage"]["provider_total_tokens"]["known_subtotal"])

    def test_feedback_unknown_and_explicit_cases_do_not_inflate_trigger_scores(self):
        self.initialize()
        self.write()
        self.adc.collect(self.directory)
        task = self.adc.summary(self.directory)["tasks"][0]["task_id"]
        initial = self.adc.summary(self.directory)["trigger_feedback"]
        self.assertIsNone(initial["precision"])
        self.assertIsNone(initial["recall"])
        self.adc.record_feedback(self.directory, task, used="no", expected="yes", invocation="implicit")
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["trigger_feedback"]["fn"])
        self.assertEqual(0, report["trigger_feedback"]["recall"])
        self.assertIsNone(report["trigger_feedback"]["precision"])
        self.assertEqual("unknown", report["tasks"][0]["quality"])
        self.adc.record_feedback(self.directory, task, used="yes", expected="yes", invocation="explicit")
        report = self.adc.summary(self.directory)
        self.assertEqual(0, report["trigger_feedback"]["labeled_implicit"])
        with self.assertRaises(ValueError):
            self.adc.record_feedback(self.directory, "f" * 64, used="yes", expected="yes", invocation="implicit")

    def test_disabled_collector_does_not_advance_or_read_sources(self):
        self.initialize()
        self.write()
        self.adc.disable(self.directory)
        self.assertEqual("disabled", self.adc.collect(self.directory)["status"])
        self.assertEqual(0, self.adc.summary(self.directory)["events"])

    def test_missing_ledger_cannot_be_reported_as_zero_usage(self):
        self.initialize()
        (self.directory / "usage.sqlite3").rename(self.directory / "retained.sqlite3")
        with self.assertRaises(ValueError):
            self.adc.summary(self.directory)
        self.assertFalse((self.directory / "usage.sqlite3").exists())

    def test_output_inside_sources_and_linked_source_are_refused(self):
        adc = module()
        with self.assertRaises(ValueError):
            adc.init_ledger(self.source / "ledger", {"codex": self.source}, opt_in=True)
        link = self.root / "source-link"
        try:
            link.symlink_to(self.source, target_is_directory=True)
        except OSError:
            self.skipTest("platform cannot create symlinks")
        with self.assertRaises(ValueError):
            adc.init_ledger(self.directory, {"codex": link}, opt_in=True)

    def test_budget_makes_progress_and_reports_backlog(self):
        self.initialize()
        self.write(rows() + [rows("answer-two")[-1]])
        result = self.adc.collect(self.directory, max_bytes=80)
        self.assertTrue(result["backlog"])
        for _ in range(50):
            if not self.adc.collect(self.directory, max_bytes=80)["backlog"]:
                break
        self.assertEqual(2, self.adc.summary(self.directory)["events"])

    def test_wrapper_forwards_option_first_commands_and_help(self):
        for args in (("usage", "--help"), ("model-select", "--help")):
            result = subprocess.run([sys.executable, "-B", str(SCRIPT.with_name("adc.py")), *args],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
        result = subprocess.run([sys.executable, "-B", str(SCRIPT.with_name("adc.py")), "usage", "init",
            "--directory", str(self.directory), "--source", "codex=" + str(self.source), "--opt-in"],
            capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("enabled", json.loads(result.stdout)["status"])

    def test_later_full_copy_can_repair_unknown_task_linkage(self):
        self.initialize()
        poor = rows()[-1]
        for field in ("thread_id", "session_id", "turn_id", "root_turn_id"):
            del poor["payload"][field]
        self.write([poor])
        self.adc.collect(self.directory)
        self.assertEqual("request", self.adc.summary(self.directory)["tasks"][0]["scope"])
        self.write(name="full.jsonl")
        self.adc.collect(self.directory)
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["events"])
        self.assertEqual("turn", report["tasks"][0]["scope"])

    def test_response_model_evidence_can_replace_contextual_attribution(self):
        self.initialize()
        self.write()
        self.adc.collect(self.directory)
        reported = rows()[-1]
        reported["payload"]["model"] = "reported-service"
        self.write([reported], mode="a")
        self.adc.collect(self.directory)
        report = self.adc.summary(self.directory)
        self.assertEqual(1, report["events"])
        self.assertEqual("reported-service", report["strata"][0]["model"])
        self.assertEqual("usage", report["strata"][0]["model_source"])
        self.write(name="old-copy.jsonl")
        self.adc.collect(self.directory)
        self.assertEqual("reported-service", self.adc.summary(self.directory)["strata"][0]["model"])

    def test_cursor_from_an_older_adapter_is_replayed_for_context_without_double_counting(self):
        self.initialize()
        self.write()
        self.adc.collect(self.directory)
        with closing(sqlite3.connect(self.directory / "usage.sqlite3")) as db, db:
            for key, raw in db.execute("SELECT id,value FROM files").fetchall():
                state = json.loads(raw)
                state["adapter_sha256"] = "previous-method"
                state["parser"] = {}
                db.execute("UPDATE files SET value=? WHERE id=?", (json.dumps(state), key))
        self.write([rows("answer-two")[-1]], mode="a")
        self.adc.collect(self.directory)
        report = self.adc.summary(self.directory)
        self.assertEqual(2, report["events"])
        self.assertEqual(1, len(report["strata"]))
        self.assertEqual("test-standard", report["strata"][0]["model"])


if __name__ == "__main__":
    unittest.main()

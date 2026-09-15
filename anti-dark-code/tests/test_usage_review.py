"""Observed lifecycle and delayed usage, with contrasting review outcomes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2099-01-01T00:00:00Z"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage_rows(thread="thread-a", turn="turn-a", root="root-a", response="response-a", role="agent"):
    return [
        {"timestamp": STAMP, "type": "session_meta", "payload": {
            "id": thread, "session_id": "transport-session", "model_provider": "openai",
            "cli_version": "0.153.0", "source": {"subagent": {"id": "child"}} if role == "subagent" else "cli"}},
        {"timestamp": STAMP, "type": "turn_context", "payload": {
            "turn_id": turn, "root_turn_id": root, "model": "synthetic-model", "effort": "high"}},
        {"timestamp": STAMP, "type": "token_usage_record", "payload": {
            "thread_id": thread, "session_id": "transport-session", "turn_id": turn,
            "root_turn_id": root, "response_id": response,
            "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}}},
    ]


class RoutineReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "sources"
        self.source.mkdir()
        self.directory = self.base / "ledger"
        self.usage = load("adc_usage")
        self.review = load("adc_usage_review")
        self.usage.init_ledger(self.directory, {"codex": self.source}, opt_in=True)

    def enable(self):
        self.review.configure(self.directory, enabled=True, opt_in=True)

    def hook(self, event="UserPromptSubmit", thread="thread-a", turn="turn-a", **extra):
        return self.review.observe(self.directory, {"hook_event_name": event,
            "session_id": thread, "turn_id": turn, **extra})

    def ticket(self, thread="thread-a", turn="turn-a"):
        # Reproduce the specified external identity recipe, without invoking the helper.
        th = hashlib.sha256(("codex:thread:" + thread).encode()).hexdigest()
        tu = hashlib.sha256(("codex:turn:" + turn).encode()).hexdigest()
        return hashlib.sha256(("review:codex:" + th + ":" + tu).encode()).hexdigest()

    def collect(self, **kwargs):
        with (self.source / "source.jsonl").open("a", encoding="utf-8") as stream:
            for row in usage_rows(**kwargs):
                stream.write(json.dumps(row) + "\n")
        return self.usage.collect(self.directory)

    def records(self):
        with sqlite3.connect(self.directory / "usage.sqlite3") as db:
            return {key: json.loads(value) for key, value in db.execute("SELECT id,value FROM reviews")}

    def test_usage_opt_in_does_not_silently_enable_review_collection(self):
        self.assertEqual({}, self.hook())
        self.assertEqual(0, self.usage.summary(self.directory)["review_coverage"]["observed"])
        with self.assertRaises(ValueError):
            self.review.configure(self.directory, enabled=True)
        self.usage.disable(self.directory)
        with self.assertRaises(ValueError):
            self.enable()

    def test_labels_can_precede_usage_and_join_only_after_observation(self):
        self.enable()
        context = self.hook()["hookSpecificOutput"]["additionalContext"]
        ticket = self.ticket()
        self.assertIn(ticket, context)
        self.assertIn("not a skill activation", context)
        result = self.review.submit(self.directory, ticket, used="no", expected="yes", invocation="implicit")
        self.assertEqual("awaiting_usage", result["link_status"])
        self.assertEqual(0, self.usage.summary(self.directory)["trigger_feedback"]["labeled_implicit"])
        self.collect()
        summary = self.usage.summary(self.directory)
        self.assertEqual(1, summary["trigger_feedback_by_reviewer"]["agent-self-review"]["fn"])
        self.assertEqual(1, summary["review_coverage"]["linked"])
        self.assertEqual("unknown", summary["tasks"][0]["quality"])

    def test_concurrent_threads_with_same_turn_are_not_latest_task_guesses(self):
        self.enable()
        self.hook()
        self.collect(thread="other-thread", root="other-root", response="other-response")
        self.review.submit(self.directory, self.ticket(), used="yes", expected="yes", invocation="implicit")
        self.assertEqual("awaiting_usage", self.records()[self.ticket()]["link_status"])
        self.collect()
        report = self.usage.summary(self.directory)
        labeled = [task for task in report["tasks"] if task["feedback"]]
        self.assertEqual(1, len(labeled))
        self.assertEqual(hashlib.sha256(b"codex:root:root-a").hexdigest(), labeled[0]["task_id"])

    def test_stop_never_grades_or_forces_a_continuation(self):
        self.enable()
        self.hook()
        self.assertEqual({}, self.hook("Stop", last_assistant_message="Everything passed", stop_hook_active=False))
        self.collect()
        report = self.usage.summary(self.directory)
        self.assertEqual(1, report["review_coverage"]["stopped_without_labels"])
        self.assertEqual("unknown", report["tasks"][0]["quality"])
        self.assertIsNone(report["trigger_feedback"]["precision"])
        self.assertIsNone(report["tasks"][0]["feedback"])

    def test_usage_without_hook_delivery_stays_visible_as_a_coverage_gap(self):
        self.enable()
        self.collect()
        report = self.usage.summary(self.directory)
        self.assertEqual(0, report["review_coverage"]["observed"])
        self.assertEqual(1, report["review_coverage"]["usage_groups_without_lifecycle_ticket"])
        self.assertIsNone(report["tasks"][0]["feedback"])

    def test_duplicate_delivery_and_submission_preserve_one_review(self):
        self.enable()
        self.hook()
        self.hook()
        self.review.submit(self.directory, self.ticket(), used="no")
        before = self.records()
        self.review.submit(self.directory, self.ticket(), used="no")
        self.hook()
        self.assertEqual(before, self.records())
        self.collect()
        self.collect()
        self.assertEqual(1, self.usage.summary(self.directory)["events"])
        self.assertEqual(1, self.usage.summary(self.directory)["review_coverage"]["observed"])

    def test_child_work_joins_root_usage_without_becoming_parent_review(self):
        self.enable()
        self.hook()
        self.collect(role="subagent")
        self.review.submit(self.directory, self.ticket(), used="yes")
        self.assertEqual("awaiting_usage", self.records()[self.ticket()]["link_status"])
        self.collect(response="parent-response")
        report = self.usage.summary(self.directory)
        self.assertEqual(1, len(report["tasks"]))
        self.assertEqual(2, report["tasks"][0]["events"])
        self.assertEqual("linked", self.records()[self.ticket()]["link_status"])

    def test_later_ambiguity_withdraws_only_derived_feedback(self):
        self.enable()
        self.hook()
        self.collect()
        self.review.submit(self.directory, self.ticket(), used="yes", expected="yes", invocation="implicit")
        self.collect(root="contradictory-root", response="contradictory-response")
        report = self.usage.summary(self.directory)
        self.assertEqual(1, report["review_coverage"]["ambiguous"])
        self.assertEqual(0, report["trigger_feedback"]["labeled_implicit"])
        self.assertEqual("yes", self.records()[self.ticket()]["labels"]["used"])

    def test_independent_feedback_is_never_overwritten_by_hook_replay(self):
        self.enable()
        self.hook()
        self.collect()
        task = self.usage.summary(self.directory)["tasks"][0]["task_id"]
        self.usage.record_feedback(self.directory, task, used="no", expected="yes", invocation="implicit")
        self.review.submit(self.directory, self.ticket(), used="yes", expected="yes", invocation="implicit")
        self.hook("Stop")
        report = self.usage.summary(self.directory)
        self.assertEqual("no", report["tasks"][0]["feedback"]["used"])
        self.assertEqual(1, report["review_coverage"]["feedback_conflict"])
        self.assertEqual(1, report["trigger_feedback_by_reviewer"]["unknown"]["fn"])

    def test_review_corrections_keep_history_and_failed_attempt_labels(self):
        self.enable()
        self.hook()
        self.collect()
        self.review.submit(self.directory, self.ticket(), quality="failed", basis="observed-result", had_failed_attempt="yes")
        self.review.submit(self.directory, self.ticket(), quality="passed", basis="acceptance-checks",
                           evidence_sha256=["a" * 64], had_failed_attempt="yes")
        row = self.records()[self.ticket()]
        self.assertEqual("failed", row["label_history"][0]["quality"])
        self.assertEqual("passed", row["labels"]["quality"])
        self.assertEqual(1, self.usage.summary(self.directory)["review_coverage"]["reported_failed_attempts"])

    def test_unknown_and_explicit_labels_are_excluded_and_reviewers_separated(self):
        self.enable()
        for i, (used, expected, invocation, reviewer) in enumerate([
            ("yes", "yes", "implicit", "agent-self-review"),
            ("yes", "no", "implicit", "agent-self-review"),
            ("no", "yes", "implicit", "human-review"),
            ("no", "no", "implicit", "human-review"),
            ("yes", "yes", "explicit", "agent-self-review"),
            ("unknown", "yes", "implicit", "agent-self-review"),
        ]):
            turn = "turn-" + str(i)
            self.hook(turn=turn)
            self.collect(turn=turn, root="root-" + str(i), response="response-" + str(i))
            self.review.submit(self.directory, self.ticket(turn=turn), used=used, expected=expected,
                               invocation=invocation, reviewer=reviewer)
        report = self.usage.summary(self.directory)
        self.assertEqual(4, report["trigger_feedback"]["labeled_implicit"])
        scores = report["trigger_feedback_by_reviewer"]
        self.assertEqual(.5, scores["agent-self-review"]["precision"])
        self.assertEqual(0, scores["human-review"]["recall"])
        self.assertIsNone(scores["unknown"]["precision"])
        self.assertIsNone(report["savings"])

    def test_known_quality_needs_basis_and_check_basis_needs_evidence(self):
        self.enable()
        self.hook()
        for kwargs in [dict(quality="passed"), dict(quality="failed"), dict(basis="acceptance-checks"),
                       dict(skill_version="sk-private-payload"), dict(evidence_sha256=["secret-payload"]),
                       dict(used="no", skill_version="2026.09.07-unified.14")]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.review.submit(self.directory, self.ticket(), **kwargs)
        self.assertIsNone(self.records()[self.ticket()]["labels"])
        self.review.submit(self.directory, self.ticket(), used="yes", skill_version="2026.09.07-unified.14")
        self.assertEqual("2026.09.07-unified.14", self.records()[self.ticket()]["labels"]["reported_skill_version"])

    def test_disabled_reviews_preserve_history_without_accepting_new_labels(self):
        self.enable()
        self.hook()
        self.review.configure(self.directory, enabled=False)
        before = (self.directory / "usage.sqlite3").read_bytes()
        self.assertEqual({}, self.hook(turn="next-turn"))
        with self.assertRaises(ValueError):
            self.review.submit(self.directory, self.ticket(), used="yes")
        self.assertEqual(before, (self.directory / "usage.sqlite3").read_bytes())
        self.assertEqual(1, self.review.pending(self.directory)["coverage"]["observed"])

    def test_unobserved_ticket_refused_and_payload_text_not_retained(self):
        self.enable()
        with self.assertRaises(ValueError):
            self.review.submit(self.directory, "f" * 64, used="yes")
        self.hook(prompt="PRIVATE-UNIQUE-PROMPT", transcript_path="/private/unique/path", cwd="/private/workspace")
        self.hook("Stop", last_assistant_message="PRIVATE-UNIQUE-ANSWER")
        self.collect()
        data = (self.directory / "usage.sqlite3").read_bytes()
        for forbidden in (b"PRIVATE-UNIQUE", b"/private/unique/path", b"/private/workspace", b"thread-a", b"turn-a"):
            self.assertNotIn(forbidden, data)

    def test_invalid_and_oversized_hook_input_cannot_block_or_echo_payloads(self):
        self.enable()
        for payload in [b'{"secret":"PRIVATE-PAYLOAD"', b"PRIVATE-PAYLOAD" * 100000,
                        json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "PRIVATE-PAYLOAD"}).encode()]:
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/adc_usage_review.py"),
                "hook", "--directory", str(self.directory)], input=payload, capture_output=True)
            self.assertEqual(0, result.returncode)
            self.assertNotIn(b"PRIVATE-PAYLOAD", result.stdout + result.stderr)
            self.assertIn("systemMessage", json.loads(result.stdout))
            self.assertNotIn("decision", json.loads(result.stdout))
        self.assertEqual(3, self.usage.summary(self.directory)["diagnostics"]["review_hook_refused"])

    def test_wrapper_routes_review_workflow_without_extra_collection(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/adc.py"), "usage", "review",
            "enable", "--directory", str(self.directory), "--opt-in"], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("review-enabled", json.loads(result.stdout)["status"])
        self.assertEqual(0, self.usage.summary(self.directory)["events"])


if __name__ == "__main__":
    unittest.main()

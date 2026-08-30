"""The route subcommand, exercised as a process.

These run adc.py rather than importing it. The contract this slice cares about
is partly the exit code: a stale receipt exits 2, and a missing policy refuses
instead of routing. An in-process call can assert the printed text and still
miss a command that returns the wrong status, which is the half a gate runner
actually reads.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())

SKILL_ROOT = Path(__file__).resolve().parents[1]
ADC = SKILL_ROOT / "scripts" / "adc.py"
TEMPLATE = SKILL_ROOT / "assets" / "templates" / "calibration" / "routing-policy.json"

GATES = {
    "schema_version": 1,
    "canonical_full_set": {
        "passes": ["07", "10", "11", "14"],
        "obligations": {
            "V01": ["mutation-replay"],
            "V08": ["distribution"],
            "V09": ["validate-core"],
            "V12": ["hostile-environment"],
            "V21": ["full-suite"],
        },
    },
    "gates": [
        {"id": gate, "enabled": True, "review_status": "approved"}
        for gate in ("validate-core", "full-suite", "distribution",
                     "hostile-environment", "mutation-replay")
    ],
}


@unittest.skipUnless(shutil.which("git"), "git is required")
class RouteCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main", ".")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        (self.repo / "src.py").write_text("one\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "one")
        (self.repo / "src.py").write_text("two\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "two")

        self.calibration = self.repo / "calibration"
        self.calibration.mkdir()
        shutil.copyfile(TEMPLATE, self.calibration / "routing-policy.json")
        self._write_gates(GATES)

    def _write_gates(self, data) -> None:
        (self.calibration / "gates.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              capture_output=True, text=True, timeout=60)

    def _route(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(ADC), "route", "--repo", str(self.repo),
             "--calibration", str(self.calibration), *args],
            capture_output=True, text=True, timeout=300)

    def test_routing_a_change_reports_a_route_and_succeeds(self) -> None:
        done = self._route("--base", "HEAD~1")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("ROUTE ", done.stdout)

    def test_an_unread_policy_routes_everything(self) -> None:
        """Every rule ships proposed, a proposed rule never matches, and an
        unmatched fact forces full. A template nobody has read must not be able
        to make a route cheaper."""
        done = self._route("--base", "HEAD~1")
        self.assertIn("force_full=true", done.stdout)
        self.assertIn("rules=-", done.stdout)
        for gate in ("validate-core", "full-suite", "distribution",
                     "hostile-environment", "mutation-replay"):
            self.assertIn(gate, done.stdout)

    def test_a_missing_policy_refuses_instead_of_routing(self) -> None:
        (self.calibration / "routing-policy.json").unlink()
        done = self._route("--base", "HEAD~1")
        self.assertNotEqual(0, done.returncode)
        self.assertIn("REFUSED", done.stdout + done.stderr)
        self.assertNotIn("ROUTE ", done.stdout)

    def test_an_invalid_policy_refuses_instead_of_routing(self) -> None:
        (self.calibration / "routing-policy.json").write_text(
            json.dumps({"schema_version": 99}), encoding="utf-8")
        done = self._route("--base", "HEAD~1")
        self.assertNotEqual(0, done.returncode)
        self.assertIn("REFUSED", done.stdout + done.stderr)
        self.assertNotIn("ROUTE ", done.stdout)

    def test_gates_without_a_canonical_full_set_refuse(self) -> None:
        """The policy is checked against the full set and cannot supply it, so
        gates missing one is a refusal rather than an empty comparison that
        every recipe passes."""
        stripped = {k: v for k, v in GATES.items() if k != "canonical_full_set"}
        self._write_gates(stripped)
        done = self._route("--base", "HEAD~1")
        self.assertNotEqual(0, done.returncode)
        self.assertIn("canonical_full_set", done.stdout + done.stderr)

    def test_an_unreachable_base_does_not_produce_a_cheap_route(self) -> None:
        done = self._route("--base", "does-not-exist")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("complete=false", done.stdout)
        self.assertIn("force_full=true", done.stdout)

    def _written_receipt(self) -> Path:
        done = self._route("--base", "HEAD~1", "--write")
        self.assertEqual(0, done.returncode, done.stderr)
        written = sorted((self.repo / ".anti-dark-code" / "runs").glob("*.json"))
        self.assertEqual(1, len(written), done.stdout)
        return written[0]

    def test_a_written_receipt_verifies_fresh(self) -> None:
        receipt = self._written_receipt()
        done = self._route("--verify", str(receipt))
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("FRESH", done.stdout)

    def test_a_changed_worktree_makes_the_receipt_stale_and_exits_two(self) -> None:
        receipt = self._written_receipt()
        (self.repo / "src.py").write_text("three\n", encoding="utf-8")
        done = self._route("--verify", str(receipt))
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("STALE", done.stdout)
        self.assertIn("ADC-STALE-004", done.stdout)

    def test_reverting_the_change_makes_the_receipt_fresh_again(self) -> None:
        """Freshness is a comparison, not a one-way marker. A receipt that
        stayed stale after the repository returned to the bound state would be
        binding to the fact that something happened rather than to the state.
        """
        receipt = self._written_receipt()
        original = (self.repo / "src.py").read_text(encoding="utf-8")
        (self.repo / "src.py").write_text("three\n", encoding="utf-8")
        self.assertEqual(2, self._route("--verify", str(receipt)).returncode)
        (self.repo / "src.py").write_text(original, encoding="utf-8")
        done = self._route("--verify", str(receipt))
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)

    def test_a_changed_gate_configuration_makes_the_receipt_stale(self) -> None:
        receipt = self._written_receipt()
        # Add a gate rather than disabling one. Every gate here is named by
        # the full recipe, so disabling one makes the policy invalid and the
        # command refuses to load it, which is correct and is a different
        # behaviour from reporting a receipt stale.
        moved = json.loads(json.dumps(GATES))
        moved["gates"].append({"id": "new-gate", "enabled": True,
                               "review_status": "approved"})
        self._write_gates(moved)
        done = self._route("--verify", str(receipt))
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("ADC-STALE-006", done.stdout)

    def test_routing_writes_nothing_without_the_write_flag(self) -> None:
        done = self._route("--base", "HEAD~1")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertFalse((self.repo / ".anti-dark-code" / "runs").exists(),
                         "routing created a receipt store without --write")


if __name__ == "__main__":
    unittest.main()

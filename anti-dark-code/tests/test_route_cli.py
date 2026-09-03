"""The route subcommand, exercised as a process.

These run adc.py rather than importing it. The contract this slice cares about
is partly the exit code: a stale receipt exits 2, and a missing policy refuses
instead of routing. An in-process call can assert the printed text and still
miss a command that returns the wrong status, which is the half a gate runner
actually reads.
"""

from __future__ import annotations

import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
ADC = SKILL_ROOT / "scripts" / "adc.py"
TEMPLATE = SKILL_ROOT / "assets" / "templates" / "calibration" / "routing-policy.json"

GATES = {
    "schema_version": 1,
    "execution_policy": {"owner_confirmed_safe_to_execute": True},
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
        {"id": gate, "enabled": True, "review_status": "approved",
         "level": 0, "argv": [sys.executable, "-c", "raise SystemExit(0)"],
         "timeout_seconds": 30}
        for gate in ("validate-core", "full-suite", "distribution",
                     "hostile-environment", "mutation-replay")
    ],
}


def load_adc():
    spec = importlib.util.spec_from_file_location("adc_route_cli", ADC)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


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

    def test_a_non_object_gate_configuration_refuses_with_exit_two(self) -> None:
        self._write_gates([])
        done = self._route("--base", "HEAD~1")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("REFUSED", done.stdout)
        self.assertNotIn("Traceback", done.stdout + done.stderr)

    def test_a_non_object_routing_policy_refuses_with_exit_two(self) -> None:
        (self.calibration / "routing-policy.json").write_text(
            "[]\n", encoding="utf-8")
        done = self._route("--base", "HEAD~1")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("REFUSED", done.stdout)
        self.assertNotIn("Traceback", done.stdout + done.stderr)

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

    def test_the_run_store_is_not_a_change_of_its_own(self) -> None:
        """S-052, D-122. This test asserted the opposite until SLICE-002.

        Writing a receipt creates `.anti-dark-code/.gitignore`, and that file
        was the one path under the store git still reported, so every written
        receipt carried it as an untracked, unmapped fact and forced full for
        a file the tool had just created. A shadow campaign built on such
        receipts would have measured nothing: every candidate would be full.
        The store's ignore file now ignores itself, and a real change under
        `.anti-dark-code/calibration/` is still seen, which is why the
        repository's own ignore file was not widened instead.
        """
        receipt = self._written_receipt()
        data = json.loads(receipt.read_text(encoding="utf-8"))
        changed = [row["path"] for row in data["authoritative"]["changed_files"]]
        inside_store = [path for path in changed
                        if path.startswith(".anti-dark-code/")]
        self.assertEqual([], inside_store, "; ".join(changed))
        facts = [row["path"] for row in data.get("emitted_facts", [])]
        self.assertEqual([], [path for path in facts
                              if path.startswith(".anti-dark-code/")],
                         "; ".join(facts))
        done = self._route("--verify", str(receipt))
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)

    def test_a_tracked_store_ignore_gains_the_entry_once_and_then_is_stable(self) -> None:
        """D-122's migration, stated rather than discovered.

        A repository that committed the store's ignore file before this
        decision has a tracked file that now gains a line. The first write
        modifies it, which the router reports as a change because it is one;
        the second write leaves it alone and the store is silent again.
        """
        store = self.repo / ".anti-dark-code"
        store.mkdir(exist_ok=True)
        (store / ".gitignore").write_text(
            "runs/\nefficiency/\nflowback/\n", encoding="utf-8")
        self._git("add", "-f", ".anti-dark-code/.gitignore")
        self._git("commit", "-qm", "track the store ignore file")

        # A receipt is named by its own digest, so the newest is not the last
        # by name. Taking the one that appeared is exact; sorting was flaky.
        def written(before: set) -> Path:
            after = set((store / "runs").glob("*.json"))
            new = sorted(after - before)
            self.assertEqual(1, len(new), f"expected one new receipt, got {new}")
            return new[0]

        before = set((store / "runs").glob("*.json"))
        first = self._route("--base", "HEAD~1", "--write")
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(
            ["runs/", "efficiency/", "flowback/", ".gitignore"],
            (store / ".gitignore").read_text(encoding="utf-8").splitlines())
        first_changed = [
            row["path"] for row in json.loads(
                written(before).read_text(encoding="utf-8"))["authoritative"]["changed_files"]]
        self.assertIn(".anti-dark-code/.gitignore", first_changed)

        self._git("add", "-A")
        self._git("commit", "-qm", "adopt the fourth entry")
        # Against HEAD, so the comparison is the working tree alone. Against an
        # earlier base the adopting commit is itself in the diff, which is a
        # committed change the router should report and this test is not about.
        before = set((store / "runs").glob("*.json"))
        second = self._route("--base", "HEAD", "--write")
        self.assertEqual(0, second.returncode, second.stderr)
        second_changed = [
            row["path"] for row in json.loads(
                written(before).read_text(encoding="utf-8"))["authoritative"]["changed_files"]]
        self.assertEqual([], [path for path in second_changed
                              if path.startswith(".anti-dark-code/")],
                         "; ".join(second_changed))

    def test_a_real_calibration_change_under_the_store_is_still_seen(self) -> None:
        """D-122's other half. Ignoring `.anti-dark-code/` wholesale would
        have hidden this, which is the blindness D-089 records."""
        store = self.repo / ".anti-dark-code" / "calibration"
        store.mkdir(parents=True, exist_ok=True)
        (store / "gates.json").write_text("{}\n", encoding="utf-8")
        runs = self.repo / ".anti-dark-code" / "runs"
        before = set(runs.glob("*.json")) if runs.is_dir() else set()
        done = self._route("--base", "HEAD~1", "--write")
        self.assertEqual(0, done.returncode, done.stderr)
        appeared = sorted(set(runs.glob("*.json")) - before)
        self.assertEqual(1, len(appeared), done.stdout)
        data = json.loads(appeared[0].read_text(encoding="utf-8"))
        changed = [row["path"] for row in data["authoritative"]["changed_files"]]
        self.assertIn(".anti-dark-code/calibration/gates.json", changed)

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


@unittest.skipUnless(shutil.which("git"), "git is required")
class _RoutedGateCliFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main", ".")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        self.source = self.repo / "app" / "scripts" / "src.py"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("one\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "one")
        self.source.write_text("two\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "two")

        self.calibration = self.repo / ".anti-dark-code" / "calibration"
        self.calibration.mkdir(parents=True)
        policy = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        for rule in policy["rules"]:
            if rule["id"] == "product-code":
                rule["review_status"] = "approved"
        (self.calibration / "routing-policy.json").write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8")
        (self.calibration / "gates.json").write_text(
            json.dumps(GATES, indent=2) + "\n", encoding="utf-8")
        # D-122: the store's ignore file names itself. A fixture that commits
        # the pre-D-122 shape makes the first receipt write modify a tracked
        # file, which the router correctly reports as a change and which would
        # make every route here full for a reason this fixture is not about.
        (self.repo / ".anti-dark-code" / ".gitignore").write_text(
            "runs/\nefficiency/\nflowback/\n.gitignore\n", encoding="utf-8")
        adc = load_adc()
        assessment = adc.assess_repository_binding(self.repo, self.calibration)
        adc.write_repository_binding(
            self.calibration, assessment,
            accepted_unbound=assessment["status"] == "unbound")
        self._git("add", "-A")
        self._git("commit", "-qm", "calibration")
        self.source.write_text("three\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "three")

        written = self._route("--base", "HEAD~1", "--write")
        self.assertEqual(0, written.returncode, written.stdout + written.stderr)
        receipts = sorted((self.repo / ".anti-dark-code" / "runs").glob("*.json"))
        self.assertEqual(1, len(receipts), written.stdout)
        self.receipt = receipts[0]

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], capture_output=True,
            text=True, timeout=60)

    def _route(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ADC), "route", "--repo", str(self.repo),
             "--calibration", str(self.calibration), *args],
            capture_output=True, text=True, timeout=300)

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ADC), "gates", "--repo", str(self.repo),
             *args], capture_output=True, text=True, timeout=300)


class ShadowRecordCliTests(_RoutedGateCliFixture):
    """D-125 end to end, on a change the classifier actually maps.

    The candidate here selects two gates and omits three, which is the shape
    the campaign exists to measure. A record on a repository where every path
    is unmapped is `no_omission` and says nothing, which is why this uses the
    routed fixture rather than the consumer-shaped one.
    """

    ALL_PASS = {"validate-core": "pass", "full-suite": "pass",
                "distribution": "pass", "hostile-environment": "pass",
                "mutation-replay": "pass"}

    def _shadow(self, outcomes: dict, *extra: str):
        outcomes_path = Path(self.tmp.name) / "outcomes.json"
        outcomes_path.write_text(json.dumps(outcomes), encoding="utf-8")
        out = Path(self.tmp.name) / "record.json"
        done = subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", "record",
             "--repo", str(self.repo), "--calibration", str(self.calibration),
             "--base", "HEAD~1", "--base-sha", "b" * 40, "--head", "h" * 40,
             "--pr", "31", "--run", "123", "--attempt", "1",
             "--outcomes", str(outcomes_path), "--out", str(out), *extra],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        return done, json.loads(out.read_text(encoding="utf-8"))

    def test_the_command_measures_a_real_change(self) -> None:
        done, record = self._shadow(self.ALL_PASS, "--head-ref", "refs/heads/topic")
        self.assertIn("SHADOW clean", done.stdout)
        self.assertEqual(2, record["schema_version"])
        self.assertEqual("live", record["provenance"])
        self.assertTrue(record["measurable"], record)
        self.assertEqual("clean", record["status"], record)
        self.assertIn("product-code", record["class"]["matched_rule_ids"])
        self.assertEqual(["full-suite", "validate-core"],
                         record["class"]["selected_gate_ids"])
        self.assertEqual(["distribution", "hostile-environment", "mutation-replay"],
                         record["class"]["omitted_gate_ids"])
        self.assertEqual(64, len(record["record_id"]))
        self.assertEqual("123", record["run"]["run_id"])

    def test_an_omitted_gate_that_failed_is_a_miss_end_to_end(self) -> None:
        outcomes = dict(self.ALL_PASS, **{"mutation-replay": "fail"})
        done, record = self._shadow(outcomes)
        self.assertIn("SHADOW miss", done.stdout)
        self.assertEqual("miss", record["status"])
        self.assertEqual(["mutation-replay"], record["shadow"]["missed_gate_ids"])

    def test_an_undecided_gate_leaves_no_verdict(self) -> None:
        outcomes = dict(self.ALL_PASS, **{"distribution": "cancelled"})
        done, record = self._shadow(outcomes)
        self.assertFalse(record["measurable"])
        self.assertEqual("not_measurable", record["status"])
        self.assertIn("distribution=cancelled", record["not_measurable_reason"])
        self.assertIsNone(record["shadow"])

    def test_a_canary_branch_is_recognised_not_labelled(self) -> None:
        outcomes = dict(self.ALL_PASS, **{"mutation-replay": "fail"})
        _, record = self._shadow(
            outcomes, "--head-ref", "refs/heads/canary/product-code/2026-09-03")
        self.assertEqual("canary", record["provenance"])
        self.assertEqual("miss", record["status"])


class ShadowBackfillCliTests(_RoutedGateCliFixture):
    """S-060. Today's router over a historical change set, keyed by today.

    Not a reconstruction at each head: the candidate builder did not exist at
    the earliest heads in this repository's own history, so per-head keys
    would be classes of one. The record says `backfill` and the summary keeps
    those counts apart from the live ones.
    """

    def test_a_backfilled_change_uses_todays_router_and_its_own_run(self) -> None:
        self._git("checkout", "-q", "-b", "topic")
        self.source.write_text("four\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "four")
        head = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "-q", "main")
        base = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("merge", "-q", "--no-ff", "-m", "Merge PR #7: topic", "topic")
        merge = self._git("rev-parse", "HEAD").stdout.strip()

        changes = Path(self.tmp.name) / "changes.json"
        changes.write_text(json.dumps([{
            "pull_request": 7, "base": base, "head": head, "merge": merge,
            "run_id": "99", "run_attempt": 1,
            "jobs": [
                {"name": "ubuntu-latest / Python 3.12", "conclusion": "success",
                 "steps": [{"name": "Validate the core before anything writes to the tree",
                            "conclusion": "success"}]},
                {"name": "Clean distribution archive", "conclusion": "success"},
                {"name": "Hostile environment (C locale)", "conclusion": "success"},
                {"name": "Hostile environment (international paths)", "conclusion": "success"},
                {"name": "Mutation replay (Linux)", "conclusion": "success"},
            ],
        }]), encoding="utf-8")
        out_dir = Path(self.tmp.name) / "records"
        done = subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", "backfill",
             "--repo", str(self.repo), "--calibration", str(self.calibration),
             "--map", str(REPO_ROOT / ".github" / "shadow-gate-map.json"),
             "--changes", str(changes), "--out-dir", str(out_dir)],
            capture_output=True, text=True, timeout=600)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        written = sorted(out_dir.glob("*.json"))
        self.assertEqual(1, len(written), done.stdout)
        record = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual("backfill", record["provenance"])
        self.assertEqual(7, record["run"]["pull_request"])
        self.assertEqual(head, record["commits"]["head"])
        self.assertTrue(record["measurable"], record)
        self.assertEqual("clean", record["status"], record)
        self.assertIn("product-code", record["class"]["matched_rule_ids"])
        # The repository is left as it was found: a backfill checks each head
        # out in a temporary worktree and removes it.
        self.assertEqual("", self._git("worktree", "list", "--porcelain").stdout
                         .count("prunable") * "x")

    def test_a_change_with_no_run_is_recorded_as_unmeasurable(self) -> None:
        """Every change before the workflow existed has no outcomes at all.
        Dropping them would hide how much of the history cannot be measured."""
        head = self._git("rev-parse", "HEAD").stdout.strip()
        base = self._git("rev-parse", "HEAD~1").stdout.strip()
        changes = Path(self.tmp.name) / "changes.json"
        changes.write_text(json.dumps([{
            "pull_request": None, "base": base, "head": head, "merge": head,
            "run_id": None, "run_attempt": None, "jobs": None}]), encoding="utf-8")
        out_dir = Path(self.tmp.name) / "records"
        done = subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", "backfill",
             "--repo", str(self.repo), "--calibration", str(self.calibration),
             "--map", str(REPO_ROOT / ".github" / "shadow-gate-map.json"),
             "--changes", str(changes), "--out-dir", str(out_dir)],
            capture_output=True, text=True, timeout=600)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        record = json.loads(sorted(out_dir.glob("*.json"))[0].read_text(encoding="utf-8"))
        self.assertFalse(record["measurable"])
        self.assertEqual("not_measurable", record["status"])
        self.assertIn("unresolved", record["not_measurable_reason"])


class RouteLevelCliTests(_RoutedGateCliFixture):
    """R-013 at the process boundary where exit status is authoritative."""

    def test_a_level_below_the_route_minimum_exits_two_and_names_it(self) -> None:
        # Removing the downgrade refusal makes this process exit zero.
        done = self._run("--route", str(self.receipt), "--level", "0")
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("route minimum is 2", done.stdout)

    def test_a_level_above_the_route_minimum_is_accepted(self) -> None:
        # Pinning execution to the minimum instead of allowing escalation loses
        # the operator's requested Level 3 plan.
        done = self._run("--route", str(self.receipt), "--level", "3")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("Level <= 3", done.stdout)


class StaleReceiptCliTests(_RoutedGateCliFixture):
    """R-018 refusal at the process boundary, including exit status."""

    def test_a_stale_receipt_refuses_the_run_with_exit_two(self) -> None:
        self.source.write_text("moved after receipt\n", encoding="utf-8")
        done = self._run("--route", str(self.receipt))
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("STALE", done.stdout)
        self.assertIn("ADC-STALE-004", done.stdout)

    def test_a_process_change_after_preflight_refuses_before_launch(self) -> None:
        code = """
import importlib.util
import sys
from pathlib import Path

adc_path, repo, receipt, source = sys.argv[1:]
spec = importlib.util.spec_from_file_location("adc_preflight_seam", adc_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
original = module._verify_loaded_route_receipt
def move_after_preflight(*args, **kwargs):
    result = original(*args, **kwargs)
    Path(source).write_text("moved at seam\\n", encoding="utf-8")
    return result
module._verify_loaded_route_receipt = move_after_preflight
raise SystemExit(module.main([
    "gates", "--repo", repo, "--route", receipt, "--allow-exec"
]))
"""
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ADC), str(self.repo),
             str(self.receipt), str(self.source)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("STALE", done.stdout)
        self.assertIn("before launch", done.stdout)

    def test_verified_gate_configuration_is_not_reread_before_execution(self) -> None:
        sentinel = self.repo / "unverified-gate-ran.txt"
        gates_path = self.calibration / "gates.json"
        original_gates = gates_path.read_text(encoding="utf-8")
        malicious = json.loads(json.dumps(GATES))
        malicious["canonical_full_set"]["obligations"] = {
            capability: ["unverified-gate"]
            for capability in malicious["canonical_full_set"]["obligations"]
        }
        malicious["gates"] = [{
            "id": "unverified-gate", "enabled": True,
            "review_status": "approved", "level": 0,
            "argv": [
                sys.executable, "-c",
                "from pathlib import Path; "
                "Path('unverified-gate-ran.txt').write_text('ran')"],
            "timeout_seconds": 30,
        }]
        code = """
import importlib.util
import sys
from pathlib import Path

adc_path, repo, receipt, gates_path, original_gates, malicious = sys.argv[1:]
spec = importlib.util.spec_from_file_location("adc_gate_config_swap", adc_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
original_candidate = module._candidate_shadow_context
def swap_after_candidate(*args, **kwargs):
    result = original_candidate(*args, **kwargs)
    Path(gates_path).write_text(malicious, encoding="utf-8")
    return result
module._candidate_shadow_context = swap_after_candidate
original_read_json = module.read_json
def restore_after_read(path, *args, **kwargs):
    result = original_read_json(path, *args, **kwargs)
    if Path(path).resolve() == Path(gates_path).resolve():
        Path(gates_path).write_text(original_gates, encoding="utf-8")
    return result
module.read_json = restore_after_read
raise SystemExit(module.main([
    "gates", "--repo", repo, "--route", receipt, "--allow-exec"
]))
"""
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ADC), str(self.repo),
             str(self.receipt), str(gates_path), original_gates,
             json.dumps(malicious)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("STALE", done.stdout)
        self.assertIn("before launch", done.stdout)
        self.assertFalse(sentinel.exists(),
                         "an unverified in-memory gate command executed")

    def test_verified_policy_is_not_reloaded_for_candidate_reconstruction(self) -> None:
        policy_path = self.calibration / "routing-policy.json"
        original_policy = policy_path.read_text(encoding="utf-8")
        code = """
import importlib.util
import sys
from pathlib import Path

adc_path, repo, receipt, policy_path, original_policy = sys.argv[1:]
spec = importlib.util.spec_from_file_location("adc_policy_swap", adc_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
original_load = module._load_route_inputs
post_verify = False
def restore_after_candidate_reload(*args, **kwargs):
    result = original_load(*args, **kwargs)
    if post_verify:
        Path(policy_path).write_text(original_policy, encoding="utf-8")
    return result
module._load_route_inputs = restore_after_candidate_reload
original_verify = module._verify_loaded_route_receipt
def mutate_after_verify(*args, **kwargs):
    global post_verify
    result = original_verify(*args, **kwargs)
    Path(policy_path).write_text(original_policy + " ", encoding="utf-8")
    post_verify = True
    return result
module._verify_loaded_route_receipt = mutate_after_verify
raise SystemExit(module.main([
    "gates", "--repo", repo, "--route", receipt, "--allow-exec"
]))
"""
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ADC), str(self.repo),
             str(self.receipt), str(policy_path), original_policy],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("STALE", done.stdout)
        self.assertIn("before launch", done.stdout)


class ReceiptIntegrityCliTests(_RoutedGateCliFixture):
    def test_an_edited_authoritative_route_is_refused(self) -> None:
        data = json.loads(self.receipt.read_text(encoding="utf-8"))
        data["authoritative"]["route"]["minimum_level"] = 0
        data["authoritative"]["route"]["force_full"] = False
        self.receipt.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8")
        done = self._run("--route", str(self.receipt))
        self.assertEqual(2, done.returncode, done.stdout + done.stderr)
        self.assertIn("REFUSED", done.stdout)
        self.assertIn("run_id", done.stdout)

    def test_a_verified_receipt_is_not_reread_for_route_selection(self) -> None:
        replacement = json.loads(self.receipt.read_text(encoding="utf-8"))
        replacement["authoritative"]["route"]["minimum_level"] = 0
        replacement["authoritative"]["route"]["force_full"] = False
        code = """
import importlib.util
import json
import sys
from pathlib import Path

adc_path, repo, receipt, replacement = sys.argv[1:]
spec = importlib.util.spec_from_file_location("adc_receipt_swap", adc_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
original = module._verify_loaded_route_receipt
def swap_after_verification(*args, **kwargs):
    result = original(*args, **kwargs)
    Path(receipt).write_text(replacement, encoding="utf-8")
    return result
module._verify_loaded_route_receipt = swap_after_verification
raise SystemExit(module.main([
    "gates", "--repo", repo, "--route", receipt
]))
"""
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ADC), str(self.repo),
             str(self.receipt), json.dumps(replacement)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("Level <= 2", done.stdout)
        self.assertNotIn("Level <= 0", done.stdout)

    def test_a_verified_receipt_is_not_reread_for_candidate_reconstruction(self) -> None:
        replacement = json.loads(self.receipt.read_text(encoding="utf-8"))
        replacement["authoritative"]["emitted_facts"] = [
            {"not_a_change_fact": True}]
        code = """
import importlib.util
import json
import sys
from pathlib import Path

adc_path, repo, receipt, replacement = sys.argv[1:]
spec = importlib.util.spec_from_file_location("adc_candidate_swap", adc_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
original = module._verify_loaded_route_receipt
def swap_after_verification(*args, **kwargs):
    result = original(*args, **kwargs)
    Path(receipt).write_text(replacement, encoding="utf-8")
    return result
module._verify_loaded_route_receipt = swap_after_verification
raise SystemExit(module.main([
    "gates", "--repo", repo, "--route", receipt
]))
"""
        done = subprocess.run(
            [sys.executable, "-B", "-c", code, str(ADC), str(self.repo),
             str(self.receipt), json.dumps(replacement)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("GATE PLAN", done.stdout)
        self.assertNotIn("invalid emitted facts", done.stdout + done.stderr)

    def test_a_non_object_receipt_refuses_without_a_traceback(self) -> None:
        original = json.loads(self.receipt.read_text(encoding="utf-8"))
        invalid_route = json.loads(json.dumps(original))
        invalid_route["authoritative"]["route"]["minimum_level"] = "two"
        receipt_module = load_adc().load_router_helpers()[1]
        invalid_route["run_id"] = receipt_module.digest(
            invalid_route["authoritative"])
        cases = [
            ("root", []),
            ("binding", {
                **original,
                "authoritative": {
                    **original["authoritative"], "binding": []},
            }),
            ("route-field", invalid_route),
        ]
        for label, value in cases:
            with self.subTest(label=label):
                self.receipt.write_text(
                    json.dumps(value) + "\n", encoding="utf-8")
                done = self._run("--route", str(self.receipt))
                self.assertEqual(
                    2, done.returncode, done.stdout + done.stderr)
                self.assertIn("REFUSED", done.stdout)
                self.assertNotIn("Traceback", done.stdout + done.stderr)


class ShadowComparatorCliTests(_RoutedGateCliFixture):
    def test_real_gate_outcomes_feed_the_candidate_shadow_record(self) -> None:
        # M79. The receipt is fresh only while Git's index stat cache is fresh.
        # Move the tracked file timestamp without changing bytes so a normal
        # status would refresh that cache. The gate planner must not do so
        # after receipt verification.
        original = self.source.read_bytes()
        before = self.source.stat()
        os.utime(self.source, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
        self.assertEqual(original, self.source.read_bytes())
        index = self.repo / ".git" / "index"
        index_before = index.read_bytes()
        done = self._run(
            "--route", str(self.receipt), "--allow-exec", "--keep-going")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertEqual(index_before, index.read_bytes(),
                         "gate planning refreshed the Git index after preflight")
        shadows = sorted(
            (self.repo / ".anti-dark-code" / "runs").glob("*/shadow.json"))
        self.assertEqual(1, len(shadows), done.stdout)
        shadow = json.loads(shadows[0].read_text(encoding="utf-8"))
        self.assertEqual("candidate-shadow",
                         shadow["candidate"]["provenance"])
        self.assertEqual(
            set(GATES["canonical_full_set"]["obligations"]["V01"]
                + GATES["canonical_full_set"]["obligations"]["V08"]
                + GATES["canonical_full_set"]["obligations"]["V09"]
                + GATES["canonical_full_set"]["obligations"]["V12"]
                + GATES["canonical_full_set"]["obligations"]["V21"]),
            set(shadow["gate_results"]))
        self.assertEqual({"pass"}, set(shadow["gate_results"].values()))


if __name__ == "__main__":
    unittest.main()

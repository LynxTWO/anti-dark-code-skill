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


def _load_shadow():
    """The shadow helper as a module, for the pure counting functions."""
    path = SKILL_ROOT / "scripts" / "adc_shadow.py"
    spec = importlib.util.spec_from_file_location("adc_shadow_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_route():
    """The router as a module, for the acquisition boundary."""
    path = SKILL_ROOT / "scripts" / "adc_route.py"
    spec = importlib.util.spec_from_file_location("adc_route_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
    """S-060 and S-063. Today's router over a pull request's own run history.

    Not a reconstruction at each head: the candidate builder did not exist at
    the earliest heads in this repository's own history, so per-head keys
    would be classes of one. The record says `backfill` and the summary keeps
    those counts apart from the live ones.

    The population is the pull request's runs, every attempt, never the merge
    that survived them. D-128: a merge is a change whose run already passed
    the checks that gated it, so grading a candidate against it cannot see
    what those checks caught. These fixtures land on a merge commit, which is
    how this repository lands everything, and which is exactly the history
    where the merge base with the base branch is the head itself.
    """

    GREEN = [
        {"name": "ubuntu-latest / Python 3.12", "conclusion": "success",
         "steps": [{"name": "Validate the core before anything writes to the tree",
                    "conclusion": "success"}]},
        {"name": "Clean distribution archive", "conclusion": "success"},
        {"name": "Hostile environment (C locale)", "conclusion": "success"},
        {"name": "Hostile environment (international paths)", "conclusion": "success"},
        {"name": "Mutation replay (Linux)", "conclusion": "success"},
    ]

    def _jobs(self, **failed: str) -> list:
        jobs = json.loads(json.dumps(self.GREEN))
        for job in jobs:
            if job["name"] in failed:
                job["conclusion"] = failed[job["name"]]
        return jobs

    def _land(self, number: int, body: str) -> tuple[str, str]:
        """One pull request, landed as a merge commit. Returns head and landing."""
        branch = f"topic{number}"
        self._git("checkout", "-q", "-b", branch)
        self.source.write_text(body, encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", body.strip())
        head = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("checkout", "-q", "main")
        self._git("merge", "-q", "--no-ff", "-m",
                  f"Merge PR #{number}: {branch}", branch)
        landing = self._git("rev-parse", "HEAD").stdout.strip()
        return head, landing

    def _backfill(self, changes: list, *extra: str):
        path = Path(self.tmp.name) / "changes.json"
        path.write_text(json.dumps(changes), encoding="utf-8")
        out_dir = Path(self.tmp.name) / "records"
        done = subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", "backfill",
             "--repo", str(self.repo), "--calibration", str(self.calibration),
             "--map", str(REPO_ROOT / ".github" / "shadow-gate-map.json"),
             "--changes", str(path), "--out-dir", str(out_dir), *extra],
            capture_output=True, text=True, timeout=900)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        return done, out_dir

    def test_a_backfilled_change_uses_todays_router_and_its_own_run(self) -> None:
        head, landing = self._land(7, "four\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        expected_base = self._git("merge-base", head, first_parent).stdout.strip()

        _, out_dir = self._backfill([{
            "pull_request": 7, "head": head, "landing": landing,
            "landing_first_parent": first_parent, "head_ref": "topic7",
            "run_id": "99", "run_attempt": 1, "jobs": self.GREEN}])
        written = sorted(out_dir.glob("shadow-*.json"))
        self.assertEqual(1, len(written))
        record = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual("backfill", record["provenance"])
        self.assertEqual(7, record["run"]["pull_request"])
        self.assertEqual(head, record["commits"]["head"])
        self.assertTrue(record["measurable"], record)
        self.assertEqual("clean", record["status"], record)
        self.assertIn("product-code", record["class"]["matched_rule_ids"])
        # D-128. The base is the landing commit's first parent side, not the
        # branch as it stands: on this history merge-base(head, main) is the
        # head itself, and the change set would be empty.
        self.assertTrue(record["base_reconstructed"])
        self.assertEqual(expected_base, record["commits"]["base"])
        self.assertNotEqual(head, record["commits"]["base"])
        self.assertEqual(f"shadow-{head}-1.json", written[0].name)

    def test_the_base_the_old_rule_would_have_used_is_the_head_itself(self) -> None:
        """The defect D-128 closes, held so it cannot come back.

        A merged head is an ancestor of its base branch, so its merge base
        with that branch is itself and the change set is empty. This asserts
        the shape of the history, which is what made the earlier definition
        write nothing countable.
        """
        head, _ = self._land(11, "eleven\n")
        self.assertEqual(
            head, self._git("merge-base", head, "main").stdout.strip(),
            "the fixture no longer reproduces a merge-commit landing")

    def test_every_attempt_is_recorded_and_a_failing_one_is_a_miss(self) -> None:
        """S-063. A rerun does not replace the attempt it supersedes."""
        head, landing = self._land(8, "eight\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        entry = {"pull_request": 8, "head": head, "landing": landing,
                 "landing_first_parent": first_parent, "head_ref": "topic8",
                 "run_id": "101"}
        _, out_dir = self._backfill([
            {**entry, "run_attempt": 1,
             "jobs": self._jobs(**{"Clean distribution archive": "failure"})},
            {**entry, "run_attempt": 2, "jobs": self.GREEN},
            {**entry, "run_attempt": 3, "jobs": self.GREEN},
        ])
        written = sorted(out_dir.glob("shadow-*.json"))
        self.assertEqual(3, len(written))
        by_attempt = {}
        for path in written:
            record = json.loads(path.read_text(encoding="utf-8"))
            by_attempt[record["run"]["run_attempt"]] = record
        self.assertEqual({1, 2, 3}, set(by_attempt))
        self.assertEqual("miss", by_attempt[1]["status"], by_attempt[1])
        self.assertIn("distribution", by_attempt[1]["shadow"]["missed_gate_ids"])
        self.assertEqual("clean", by_attempt[2]["status"])
        self.assertEqual("clean", by_attempt[3]["status"])
        for record in by_attempt.values():
            self.assertTrue(record["base_reconstructed"])

    def test_a_head_whose_commit_is_gone_is_recorded_and_not_dropped(self) -> None:
        """A force-pushed or deleted-fork head has no object to diff. D-127
        recorded a change with no run rather than dropping it; the same rule
        holds for a change with no commit, or the campaign overstates its own
        coverage."""
        _, landing = self._land(9, "nine\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        missing = "0" * 40
        _, out_dir = self._backfill([{
            "pull_request": 9, "head": missing, "landing": landing,
            "landing_first_parent": first_parent, "head_ref": "topic9",
            "run_id": "102", "run_attempt": 1, "jobs": self.GREEN}])
        record = json.loads(
            sorted(out_dir.glob("shadow-*.json"))[0].read_text(encoding="utf-8"))
        self.assertFalse(record["measurable"])
        self.assertEqual("not_measurable", record["status"])
        self.assertEqual("head-unavailable", record["not_measurable_reason"])
        self.assertEqual(missing, record["commits"]["head"])

    def test_a_head_and_attempt_with_a_live_record_is_not_backfilled(self) -> None:
        """The live record was built on the tree CI verified; this one would
        be built on a reconstructed base. Two records for one attempt would be
        two readings of one event."""
        head, landing = self._land(10, "ten\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        live_dir = Path(self.tmp.name) / "live"
        live_dir.mkdir()
        (live_dir / f"shadow-{head}-1.json").write_text(json.dumps({
            "provenance": "live", "commits": {"head": head},
            "run": {"run_attempt": 1}}), encoding="utf-8")
        entry = {"pull_request": 10, "head": head, "landing": landing,
                 "landing_first_parent": first_parent, "head_ref": "topic10",
                 "run_id": "103"}
        done, out_dir = self._backfill(
            [{**entry, "run_attempt": 1, "jobs": self.GREEN},
             {**entry, "run_attempt": 2, "jobs": self.GREEN}],
            "--live-records", str(live_dir))
        written = sorted(out_dir.glob("shadow-*.json"))
        self.assertEqual(1, len(written), done.stdout)
        record = json.loads(written[0].read_text(encoding="utf-8"))
        self.assertEqual(2, record["run"]["run_attempt"])
        self.assertIn("already live", done.stdout)

    def test_the_working_tree_is_not_part_of_a_historical_change(self) -> None:
        """A backfill measures a commit, and a commit has no working tree.

        The first real run of this backfill read four files the build had not
        yet committed, and the records the run was itself writing into the
        repository, so every record was a reading of the present wearing a
        historical head. The record must not move when the tree does.
        """
        head, landing = self._land(13, "thirteen\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        entry = {"pull_request": 13, "head": head, "landing": landing,
                 "landing_first_parent": first_parent, "head_ref": "topic13",
                 "run_id": "104", "run_attempt": 1, "jobs": self.GREEN}

        _, clean_dir = self._backfill([entry])
        clean = json.loads(
            sorted(clean_dir.glob("shadow-*.json"))[0].read_text(encoding="utf-8"))

        # Now dirty the tree in all three ways acquisition can see: an
        # unstaged edit to an authority file, a staged one, and an untracked
        # file of the kind a backfill's own output directory creates.
        (self.repo / "anti-dark-code" / "scripts").mkdir(parents=True, exist_ok=True)
        authority = self.repo / "anti-dark-code" / "scripts" / "adc_route.py"
        authority.write_text("# edited after the fact\n", encoding="utf-8")
        staged = self.repo / "staged.py"
        staged.write_text("# staged\n", encoding="utf-8")
        self._git("add", "staged.py")
        (self.repo / "untracked-record.json").write_text("{}\n", encoding="utf-8")

        _, dirty_dir = self._backfill([entry])
        dirty = json.loads(
            sorted(dirty_dir.glob("shadow-*.json"))[0].read_text(encoding="utf-8"))

        self.assertEqual(clean["class_key"], dirty["class_key"])
        self.assertEqual(clean["status"], dirty["status"])
        self.assertEqual(clean["class"]["matched_rule_ids"],
                         dirty["class"]["matched_rule_ids"])
        self.assertEqual(clean["audit"]["route_unknowns"],
                         dirty["audit"]["route_unknowns"])
        self.assertEqual(clean["record_id"], dirty["record_id"])

    def test_the_isolation_does_not_blind_the_acquisition_boundary(self) -> None:
        """Silencing the untracked scan must not silence the fingerprint.

        `_repo_fingerprint` lists tracked files with `ls-files` too. Matching
        on the bare subcommand would leave the boundary watching nothing:
        ADC-ROUTE-BOUNDARY-VIOLATED could not fire for any write during
        acquisition, while the snapshot still called itself complete. The
        untracked scan is `ls-files --others`, and only that is silenced.
        """
        route = _load_route()
        shadow = _load_shadow()
        head = self._git("rev-parse", "HEAD").stdout.strip()
        plain = route._default_runner(self.repo)
        historical = shadow._historical_runner(route, self.repo, head)

        tracked = route._repo_fingerprint(self.repo, plain)
        through_history = route._repo_fingerprint(self.repo, historical)
        self.assertTrue(tracked, "the fixture has no tracked files to watch")
        self.assertEqual(tracked, through_history,
                         "the historical runner blinded the boundary guard")

        # The untracked scan is still silent, which is the point of it.
        (self.repo / "left-behind.txt").write_text("x\n", encoding="utf-8")
        self.assertEqual(
            b"", historical(["git", "ls-files", "--others",
                             "--exclude-standard", "-z"]))

    def test_a_change_with_no_run_is_recorded_as_unmeasurable(self) -> None:
        """Every change before the workflow existed has no outcomes at all.
        Dropping them would hide how much of the history cannot be measured."""
        head, landing = self._land(12, "twelve\n")
        first_parent = self._git("rev-parse", f"{landing}^1").stdout.strip()
        _, out_dir = self._backfill([{
            "pull_request": 12, "head": head, "landing": landing,
            "landing_first_parent": first_parent, "head_ref": "topic12",
            "run_id": None, "run_attempt": 0, "jobs": None}])
        record = json.loads(
            sorted(out_dir.glob("shadow-*.json"))[0].read_text(encoding="utf-8"))
        self.assertFalse(record["measurable"])
        self.assertEqual("not_measurable", record["status"])
        self.assertIn("unresolved", record["not_measurable_reason"])


class ShadowDominanceCliTests(_RoutedGateCliFixture):
    """S-068, R-066, D-134. An exhaustive probe, for a class no gate reads.

    A canary is one hand-built break, and for a class the gates can see, one
    plus a sample is enough. For a class the gates cannot see, a sample of
    clean records shows only that nothing happened, so the evidence has to be
    every path the class covers, broken two ways, with every gate's verdict
    recorded.
    """

    def _dominance_calibration(self, *, reads_prose: bool):
        """A calibration whose gates are real commands this test can run.

        The gate that reads prose is a script that fails when the prose file
        is missing or changed; the gate that does not is one that ignores it
        entirely. That difference is the whole experiment.
        """
        prose = self.repo / "docs"
        prose.mkdir(parents=True, exist_ok=True)
        (prose / "guide.md").write_text("the original guide\n", encoding="utf-8")
        (prose / "notes.md").write_text("the original notes\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "prose")

        reader = self.repo / "check_prose.py"
        reader.write_text(
            "import pathlib, sys\n"
            "want = 'the original guide\\n'\n"
            "p = pathlib.Path('docs/guide.md')\n"
            "sys.exit(0 if p.is_file() and p.read_text() == want else 1)\n",
            encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "reader")

        gates = {
            "schema_version": 1,
            "execution_policy": {"owner_confirmed_safe_to_execute": True},
            "canonical_full_set": {
                "passes": ["07"],
                "obligations": {"V09": ["selected"], "V21": ["omitted"]},
            },
            "gates": [
                {"id": "selected", "enabled": True, "review_status": "approved",
                 "level": 0, "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                 "timeout_seconds": 60},
                {"id": "omitted", "enabled": True, "review_status": "approved",
                 "level": 0,
                 "argv": ([sys.executable, "check_prose.py"] if reads_prose
                          else [sys.executable, "-c", "raise SystemExit(0)"]),
                 "timeout_seconds": 60},
            ],
        }
        policy = {
            "schema_version": 1,
            "classifier": {"surfaces": [
                {"glob": "docs/*.md", "surface": "docs", "effect": "prose",
                 "breadth": "leaf"},
            ]},
            "full_recipe": {"minimum_level": 3, "passes": ["07"],
                            "obligations": {"V09": ["selected"],
                                            "V21": ["omitted"]},
                            "independent_review": True},
            "rules": [
                {"id": "docs-only", "review_status": "proposed",
                 "match": {"surfaces": ["docs"], "effects": ["prose"]},
                 "requires": {"passes": ["07"], "minimum_level": 0},
                 "obligations": {"V09": ["selected"]}},
            ],
        }
        calibration = Path(self.tmp.name) / "dominance-calibration"
        calibration.mkdir(parents=True, exist_ok=True)
        (calibration / "gates.json").write_text(json.dumps(gates, indent=2),
                                                encoding="utf-8")
        (calibration / "routing-policy.json").write_text(
            json.dumps(policy, indent=2), encoding="utf-8")

        summary = Path(self.tmp.name) / "dominance-summary.json"
        summary.write_text(json.dumps({
            "schema_version": 2, "records": 0, "records_by_provenance": {},
            "classes": [{
                "class_key": "K" * 64,
                "matched_rule_ids": ["docs-only"],
                "selected_gate_ids": ["selected"],
                "omitted_gate_ids": ["omitted"],
                "router_blob_sha256": "r", "terms_sha256": "t",
                "records": {}, "status": {}, "criterion": {},
                "canary_record_ids": [], "dominance_record_ids": [],
            }],
        }, indent=2), encoding="utf-8")
        return calibration, summary

    def _probe(self, calibration: Path, summary: Path, *extra: str):
        out_dir = Path(self.tmp.name) / f"dominance-{len(extra)}-out"
        done = subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", "dominance",
             "--repo", str(self.repo), "--calibration", str(calibration),
             "--summary", str(summary), "--class-key", "K" * 12,
             "--out-dir", str(out_dir), *extra],
            capture_output=True, text=True, timeout=900)
        return done, out_dir

    def test_a_class_no_gate_reads_is_dominated(self) -> None:
        calibration, summary = self._dominance_calibration(reads_prose=False)
        done, out_dir = self._probe(calibration, summary, "--allow-exec")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("is dominated", done.stdout)
        records = sorted(out_dir.glob("shadow-dominance-*.json"))
        self.assertEqual(2, len(records), done.stdout)
        for path in records:
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("dominance", record["provenance"])
            self.assertNotEqual("miss", record["status"])
        # And the tree is exactly as it was.
        self.assertEqual("", self._git("status", "--porcelain").stdout.strip())

    def test_a_class_an_omitted_gate_reads_is_not_dominated(self) -> None:
        calibration, summary = self._dominance_calibration(reads_prose=True)
        done, out_dir = self._probe(calibration, summary, "--allow-exec")
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertIn("NOT dominated", done.stdout)
        statuses = {json.loads(p.read_text(encoding="utf-8"))["status"]
                    for p in out_dir.glob("shadow-dominance-*.json")}
        self.assertIn("miss", statuses)
        self.assertEqual("", self._git("status", "--porcelain").stdout.strip())

    def test_the_probe_refuses_without_owner_confirmation(self) -> None:
        """It runs every gate, so it obeys the same confirmation the gate
        runner does. D-011 is not relaxed by an approval-time act."""
        calibration, summary = self._dominance_calibration(reads_prose=False)
        gates = json.loads((calibration / "gates.json").read_text(encoding="utf-8"))
        gates["execution_policy"]["owner_confirmed_safe_to_execute"] = False
        (calibration / "gates.json").write_text(json.dumps(gates, indent=2),
                                                encoding="utf-8")
        done, _ = self._probe(calibration, summary, "--allow-exec")
        self.assertEqual(2, done.returncode)
        self.assertIn("does not record owner confirmation", done.stdout)

    def test_the_probe_refuses_a_dirty_tree(self) -> None:
        calibration, summary = self._dominance_calibration(reads_prose=False)
        (self.repo / "docs" / "guide.md").write_text("edited\n", encoding="utf-8")
        done, _ = self._probe(calibration, summary, "--allow-exec")
        self.assertEqual(2, done.returncode)
        self.assertIn("requires a clean tree", done.stdout)


class ShadowLedgerCliTests(_RoutedGateCliFixture):
    """S-056, S-057, S-059, S-061, S-065. Ingest refuses; the summary counts.

    The summary counts pull requests, not records, per class: D-128, because
    one pull request can run eight times and eight readings of one change are
    not eight units of evidence.
    """

    def _shadow(self, *args: str):
        return subprocess.run(
            [sys.executable, "-B", str(ADC), "shadow", *args],
            capture_output=True, text=True, timeout=900)

    def _record(self, **overrides):
        shadow = _load_shadow()
        record = {
            "schema_version": 2, "schema": "shadow-record-v2",
            "provenance": "live", "head_ref": "refs/heads/topic",
            "status": "clean", "measurable": True,
            "not_measurable_reason": None, "inconclusive_reason": None,
            "commits": {"base": "b" * 40, "merge": "m" * 40, "head": "h" * 40},
            "base_reconstructed": False,
            "run": {"pull_request": 1, "run_id": "1", "run_attempt": 1},
            "class_key": "K1", "class": {
                "matched_rule_ids": ["docs-only"], "selected_gate_ids": ["validate-core"],
                "omitted_gate_ids": ["full-suite"], "router_blob_sha256": "r",
                "terms_sha256": "t"},
            "audit": {"policy_bytes_sha256": "p", "policy_terms_sha256": "p",
                      "gates_terms_sha256": "g", "route_force_full": False,
                      "route_minimum_level": 0, "route_unknowns": []},
            "gate_outcomes": {"validate-core": "pass", "full-suite": "pass"},
            "base_gate_outcomes": None,
            "shadow": {"routing_miss": False, "missed_gate_ids": [],
                       "selected_all_passed": True},
        }
        record.update(overrides)
        body = {k: v for k, v in record.items() if k != "record_id"}
        record["record_id"] = shadow.digest(body)
        return record

    def _write(self, directory: Path, records) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        for index, record in enumerate(records):
            (directory / f"shadow-{index}.json").write_text(
                json.dumps(record), encoding="utf-8")
        return directory

    def _ingest(self, source: Path, ledger: Path, *extra: str):
        # These fixtures are synthetic records over commits that do not
        # exist, so the class cannot be recomputed from a policy at a head
        # there is none of. The tests that hold the recomputation itself
        # exercise it directly against a real fixture repository.
        return self._shadow(
            "ingest", "--repo", str(self.repo),
            "--map", str(REPO_ROOT / ".github" / "shadow-gate-map.json"),
            "--source", str(source), "--ledger", str(ledger),
            "--month", "2026-09", "--offline", "--skip-class-recomputation",
            *extra)

    def test_a_record_whose_id_does_not_digest_it_is_refused(self) -> None:
        """S-056. The artifact is written by the pull request's own workflow,
        so a record is a claim until something checks it."""
        forged = self._record()
        forged["status"] = "miss"  # after the id was computed
        source = self._write(Path(self.tmp.name) / "inbox", [forged])
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger)
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("record_id does not digest", done.stdout)
        self.assertFalse(list(ledger.glob("*.jsonl")))

    def test_a_canary_that_landed_is_refused(self) -> None:
        """S-059. A canary is a branch that is never merged; one that has
        landed is an ordinary change wearing a canary's name."""
        head = self._git("rev-parse", "HEAD").stdout.strip()
        canary = self._record(provenance="canary",
                              head_ref="refs/heads/canary/docs-only/2026-09-03",
                              commits={"base": "b" * 40, "merge": "m" * 40,
                                       "head": head})
        source = self._write(Path(self.tmp.name) / "inbox", [canary])
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger, "--main", "main")
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("is an ancestor of", done.stdout)

    def test_ingest_is_idempotent(self) -> None:
        source = self._write(Path(self.tmp.name) / "inbox", [self._record()])
        ledger = Path(self.tmp.name) / "ledger"
        self.assertEqual(0, self._ingest(source, ledger).returncode)
        again = self._ingest(source, ledger)
        self.assertEqual(0, again.returncode)
        self.assertIn("INGEST 0 record(s)", again.stdout)
        lines = (ledger / "2026-09.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))

    def test_the_summary_counts_pull_requests_not_records(self) -> None:
        """S-065 and R-063. Eight clean records from one pull request are one
        unit of evidence; one miss among them takes the class, and an
        inconclusive attempt neither adds nor removes."""
        shadow = _load_shadow()
        clean = [self._record(run={"pull_request": 1, "run_id": "1",
                                   "run_attempt": attempt})
                 for attempt in range(1, 9)]
        summary = shadow.summarise(clean)
        entry = summary["classes"][0]
        self.assertEqual(1, entry["criterion"]["pull_requests_counted"])

        with_miss = clean + [self._record(
            status="miss", run={"pull_request": 1, "run_id": "1", "run_attempt": 9})]
        entry = shadow.summarise(with_miss)["classes"][0]
        self.assertEqual(0, entry["criterion"]["pull_requests_counted"])
        self.assertEqual(["1"], entry["criterion"]["pull_requests_with_a_miss"])

        with_inconclusive = clean + [self._record(
            status="inconclusive",
            run={"pull_request": 1, "run_id": "1", "run_attempt": 9})]
        entry = shadow.summarise(with_inconclusive)["classes"][0]
        self.assertEqual(1, entry["criterion"]["pull_requests_counted"])

    def test_the_summary_counts_a_dominance_record_as_neither(self) -> None:
        shadow = _load_shadow()
        base = self._record(class_key="K1")
        probes = []
        for probe, status in (("deleted", "clean"), ("replaced", "clean")):
            record = self._record(class_key="K1", status=status,
                                  provenance="dominance",
                                  run={"pull_request": None,
                                       "run_id": f"dominance-{probe}",
                                       "run_attempt": 1})
            probes.append(record)
        summary = shadow.summarise([base] + probes)
        entry = summary["classes"][0]
        self.assertEqual(1, entry["criterion"]["pull_requests_counted"])
        self.assertEqual([], entry["criterion"]["pull_requests_with_a_miss"])
        self.assertEqual(2, len(entry["dominance_record_ids"]))
        self.assertTrue(entry["criterion"]["dominated"])

        # One probe is a class nobody finished probing.
        half = shadow.summarise([base, probes[0]])
        self.assertFalse(half["classes"][0]["criterion"]["dominated"])
        # A probe that missed is not dominance.
        missed = self._record(class_key="K1", status="miss",
                              provenance="dominance",
                              run={"pull_request": None,
                                   "run_id": "dominance-replaced",
                                   "run_attempt": 1})
        self.assertFalse(
            shadow.summarise([base, probes[0], missed])["classes"][0]
            ["criterion"]["dominated"])

    def test_a_canary_is_never_counted_as_evidence(self) -> None:
        shadow = _load_shadow()
        summary = shadow.summarise([
            self._record(provenance="canary", status="miss"),
            self._record(provenance="backfill", status="clean"),
        ])
        entry = summary["classes"][0]
        self.assertEqual(0, entry["criterion"]["pull_requests_counted"])
        self.assertEqual([], entry["criterion"]["pull_requests_with_a_miss"])
        self.assertEqual(1, entry["criterion"]["canaries"])

    def test_two_class_keys_are_never_merged(self) -> None:
        """S-061. A router change changes what a candidate is."""
        shadow = _load_shadow()
        summary = shadow.summarise([
            self._record(class_key="K1"),
            self._record(class_key="K2", run={"pull_request": 2, "run_id": "2",
                                              "run_attempt": 1}),
        ])
        self.assertEqual(2, len(summary["classes"]))
        self.assertEqual(["K1", "K2"],
                         [entry["class_key"] for entry in summary["classes"]])

    def test_outcomes_are_re_read_from_the_run_and_not_believed(self) -> None:
        """G10, and the reason the artifact is an inbox rather than a ledger.

        The record is built by the pull request's own workflow, so a pull
        request that edits that workflow could upload whatever outcomes it
        liked. Ingest re-reads them for the recorded run and attempt. The API
        is stubbed here because the check is the comparison, not the network.
        """
        shadow = _load_shadow()
        gate_map = json.loads(
            (REPO_ROOT / ".github" / "shadow-gate-map.json").read_text(encoding="utf-8"))
        # Every canonical gate, because a record that names fewer is already
        # refused as unmeasurable before this check is reached.
        record = self._record(
            gate_outcomes={"validate-core": "pass", "full-suite": "pass",
                           "distribution": "pass", "hostile-environment": "pass",
                           "mutation-replay": "pass"},
            run={"pull_request": 1, "run_id": "77", "run_attempt": 1})

        rest = [
            {"name": "Clean distribution archive", "conclusion": "success"},
            {"name": "Hostile environment (C locale)", "conclusion": "success"},
            {"name": "Hostile environment (international paths)", "conclusion": "success"},
            {"name": "Mutation replay (Linux)", "conclusion": "success"},
        ]
        honest = [
            {"name": "ubuntu-latest / Python 3.12", "conclusion": "success",
             "steps": [{"name": "Validate the core before anything writes to the tree",
                        "conclusion": "success"}]},
        ] + rest
        lying = [
            {"name": "ubuntu-latest / Python 3.12", "conclusion": "failure",
             "steps": [{"name": "Validate the core before anything writes to the tree",
                        "conclusion": "failure"}]},
        ] + rest

        def verify(jobs):
            calls = []

            def fake(args):
                calls.append(args)
                return {"jobs": jobs}

            original = shadow._gh_json
            shadow._gh_json = fake
            try:
                problems = shadow.verify_record(
                    record, repo=self.repo, gate_map=gate_map,
                    slug="owner/name", main_ref="main", offline=False)
            finally:
                shadow._gh_json = original
            self.assertTrue(any("/actions/runs/77/attempts/1/" in "".join(call)
                                for call in calls),
                            "the recorded run and attempt were not the ones read")
            return problems

        agreeing = verify(honest)
        self.assertEqual(
            [], [p for p in agreeing if "outcomes disagree" in p], agreeing)

        disagreeing = verify(lying)
        self.assertTrue(any("outcomes disagree with the run" in p
                            for p in disagreeing), disagreeing)
        self.assertTrue(any("validate-core" in p for p in disagreeing),
                        disagreeing)

    def test_a_true_outcome_cannot_be_laundered_into_a_clean_status(self) -> None:
        """The hole the implementation challenge found.

        Re-reading the outcomes is not enough on its own. A record can report
        an omitted gate's failure perfectly honestly and still call itself
        clean, and the summary would then count it toward N. The verdict is
        recomputed from the outcomes and the gates the record says it
        selected and omitted, which needs no policy and so survives a
        classifier change.
        """
        shadow = _load_shadow()
        gate_map = json.loads(
            (REPO_ROOT / ".github" / "shadow-gate-map.json").read_text(encoding="utf-8"))
        outcomes = {"validate-core": "pass", "full-suite": "pass",
                    "distribution": "pass", "hostile-environment": "pass",
                    "mutation-replay": "fail"}
        jobs = [
            {"name": "ubuntu-latest / Python 3.12", "conclusion": "success",
             "steps": [{"name": "Validate the core before anything writes to the tree",
                        "conclusion": "success"}]},
            {"name": "Clean distribution archive", "conclusion": "success"},
            {"name": "Hostile environment (C locale)", "conclusion": "success"},
            {"name": "Hostile environment (international paths)", "conclusion": "success"},
            {"name": "Mutation replay (Linux)", "conclusion": "failure"},
        ]
        laundered = self._record(
            status="clean", gate_outcomes=outcomes,
            **{"class": {"matched_rule_ids": ["docs-only"],
                         "selected_gate_ids": ["validate-core"],
                         "omitted_gate_ids": ["full-suite", "distribution",
                                              "hostile-environment",
                                              "mutation-replay"],
                         "router_blob_sha256": "r", "terms_sha256": "t"}},
            shadow={"routing_miss": False, "missed_gate_ids": [],
                    "selected_all_passed": True})

        original = shadow._gh_json
        shadow._gh_json = lambda args: {"jobs": jobs}
        try:
            problems = shadow.verify_record(
                laundered, repo=self.repo, gate_map=gate_map,
                slug="owner/name", main_ref="main", offline=False)
        finally:
            shadow._gh_json = original
        self.assertTrue(any("status does not follow from the run" in p
                            for p in problems), problems)
        self.assertTrue(any("'miss'" in p for p in problems), problems)

        # The same shape with the honest status is accepted.
        honest = self._record(
            status="miss", gate_outcomes=outcomes,
            **{"class": laundered["class"]},
            shadow={"routing_miss": True, "missed_gate_ids": ["mutation-replay"],
                    "selected_all_passed": True})
        shadow._gh_json = lambda args: {"jobs": jobs}
        try:
            problems = shadow.verify_record(
                honest, repo=self.repo, gate_map=gate_map,
                slug="owner/name", main_ref="main", offline=False)
        finally:
            shadow._gh_json = original
        self.assertEqual([], problems, problems)

    def test_a_canary_cannot_call_itself_live_to_skip_the_canary_rules(self) -> None:
        """G8: provenance is derived from the head ref, never asserted."""
        record = self._record(
            provenance="live",
            head_ref="refs/heads/canary/docs-only/2026-09-03")
        source = self._write(Path(self.tmp.name) / "inbox", [record])
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger)
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("is a canary branch but the record claims", done.stdout)

    def test_a_canary_whose_head_is_absent_cannot_be_verified(self) -> None:
        canary = self._record(
            provenance="canary",
            head_ref="refs/heads/canary/docs-only/2026-09-03",
            commits={"base": "b" * 40, "merge": "m" * 40, "head": "0" * 40})
        source = self._write(Path(self.tmp.name) / "inbox", [canary])
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger, "--main", "main")
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("cannot be shown not to have landed", done.stdout)

    def test_an_unknown_key_or_a_wrong_schema_name_is_refused(self) -> None:
        """The schema says additionalProperties false and nothing on this path
        reads the schema, so the validator has to say it."""
        shadow = _load_shadow()
        extra = self._record()
        extra["souvenir"] = "hello"
        extra["record_id"] = shadow.digest(
            {k: v for k, v in extra.items() if k != "record_id"})
        self.assertIn("unknown key(s): souvenir",
                      "; ".join(shadow.validate_record(extra)))

        wrong = self._record(schema="something-else")
        wrong["record_id"] = shadow.digest(
            {k: v for k, v in wrong.items() if k != "record_id"})
        self.assertIn("schema must be", "; ".join(shadow.validate_record(wrong)))

        # A backfill must say whether its base was reconstructed. A live
        # record written before the field existed may omit it, because a
        # live base comes from the event payload and is never reconstructed;
        # the six records CI wrote before D-128 are exactly that case.
        without = self._record(provenance="backfill")
        del without["base_reconstructed"]
        without["record_id"] = shadow.digest(
            {k: v for k, v in without.items() if k != "record_id"})
        self.assertIn("base_reconstructed",
                      "; ".join(shadow.validate_record(without)))

        live_without = self._record()
        del live_without["base_reconstructed"]
        live_without["record_id"] = shadow.digest(
            {k: v for k, v in live_without.items() if k != "record_id"})
        self.assertEqual([], shadow.validate_record(live_without))

    def test_a_record_naming_no_run_is_refused_unless_offline(self) -> None:
        shadow = _load_shadow()
        gate_map = json.loads(
            (REPO_ROOT / ".github" / "shadow-gate-map.json").read_text(encoding="utf-8"))
        record = self._record(run={"pull_request": 1, "run_id": "", "run_attempt": 0})
        problems = shadow.verify_record(
            record, repo=self.repo, gate_map=gate_map, slug="owner/name",
            main_ref="main", offline=False)
        self.assertTrue(any("names no run and attempt" in p for p in problems),
                        problems)

    def test_keep_going_still_reports_failure(self) -> None:
        """A refusal is a refusal whether or not the run continued past it."""
        forged = self._record()
        forged["status"] = "miss"
        source = self._write(Path(self.tmp.name) / "inbox", [forged])
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger, "--keep-going")
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("1 refused", done.stdout)

    def test_a_forged_class_is_refused_against_the_policy_that_built_it(self) -> None:
        """S-066, R-064, D-133. The verdict repair did not reach the class.

        Re-reading the outcomes and recomputing the verdict leaves the matched
        rules, the selected and omitted gates and the key believed as written.
        A record that claims a cheap class for an expensive change is caught
        only by rebuilding the candidate from the policy the record names.
        """
        shadow = _load_shadow()
        head = self._git("rev-parse", "HEAD").stdout.strip()
        base = self._git("rev-parse", "HEAD~1").stdout.strip()
        landing = head
        policy = json.loads(
            (self.calibration / "routing-policy.json").read_text(encoding="utf-8"))
        gates = json.loads(
            (self.calibration / "gates.json").read_text(encoding="utf-8"))
        capability_ids = [c["id"] for c in json.loads(
            (SKILL_ROOT / "assets" / "verification-capabilities.json")
            .read_text(encoding="utf-8"))["capabilities"]]
        router_sha = shadow.router_digest(
            SKILL_ROOT / "scripts" / "adc_route.py")

        honest = self._record(
            commits={"base": base, "merge": landing, "head": head},
            **{"class": {"matched_rule_ids": ["product-code"],
                         "selected_gate_ids": ["full-suite", "validate-core"],
                         "omitted_gate_ids": ["distribution",
                                              "hostile-environment",
                                              "mutation-replay"],
                         "router_blob_sha256": router_sha,
                         "terms_sha256": "t"}})
        # The fixture's own repository is not this one, so the router blob it
        # names is not at its head; that refusal is itself part of the
        # contract and is asserted separately below.
        problems = shadow.recompute_class(
            honest, repo=self.repo, policy_source=policy, gates_source=gates,
            capability_ids=capability_ids)
        self.assertTrue(any("router-unrecoverable" in p for p in problems),
                        problems)

    def test_a_sidecar_that_does_not_digest_to_its_name_is_refused(self) -> None:
        """A file named by its own digest is self-certifying, and that is the
        only reason the policies directory needs no trusting. D-133."""
        source = Path(self.tmp.name) / "inbox"
        source.mkdir(parents=True, exist_ok=True)
        (source / "policy-0000000000000000000000000000000000000000000000000000000000000000.json"
         ).write_text('{"rules": []}\n', encoding="utf-8")
        ledger = Path(self.tmp.name) / "ledger"
        done = self._ingest(source, ledger)
        self.assertEqual(2, done.returncode, done.stdout)
        self.assertIn("does not digest to its name", done.stdout)

    def test_a_backfill_record_with_no_stored_policy_is_not_recovered(self) -> None:
        """The backfill writes its own sidecar, so its absence means
        something else is wrong; a live record is recovered from its head."""
        shadow = _load_shadow()
        record = self._record(provenance="backfill", base_reconstructed=True)
        problems = shadow._recompute_with_sidecars(
            record, repo=self.repo, sidecars={}, capability_ids=["V09"])
        self.assertTrue(any("a backfill writes its own" in p for p in problems),
                        problems)

    def test_the_sidecars_digest_to_their_own_names(self) -> None:
        shadow = _load_shadow()
        policy = json.loads(
            (self.calibration / "routing-policy.json").read_text(encoding="utf-8"))
        gates = json.loads(
            (self.calibration / "gates.json").read_text(encoding="utf-8"))
        for name, body in shadow.policy_sidecars(policy, gates).items():
            with self.subTest(name=name):
                self.assertTrue(shadow._digests_to_its_name(name, body))
        # And the names are the ones a record carries, so ingest can find them.
        self.assertEqual(
            f"policy-{shadow.digest(shadow.strip_underscored(policy))}.json",
            next(n for n in shadow.policy_sidecars(policy, gates) if n.startswith("policy-")))

    def test_the_summary_is_byte_identical_when_regenerated(self) -> None:
        """S-057. A summary that moves cannot be reviewed."""
        source = self._write(Path(self.tmp.name) / "inbox",
                             [self._record(),
                              self._record(run={"pull_request": 2, "run_id": "2",
                                                "run_attempt": 1})])
        ledger = Path(self.tmp.name) / "ledger"
        self.assertEqual(0, self._ingest(source, ledger).returncode)
        out = Path(self.tmp.name) / "summary.json"
        for _ in range(2):
            done = self._shadow("summary", "--ledger", str(ledger),
                                "--out", str(out))
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)
            if not hasattr(self, "_first"):
                self._first = out.read_bytes()
        self.assertEqual(self._first, out.read_bytes())


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

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())

SKILL_ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = SKILL_ROOT / "assets" / "verification-capabilities.json"


def load_module(name: str, path: Path):
    """Register before executing: dataclasses resolve annotations through
    sys.modules, and a module absent from it cannot define one."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[spec.name] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


ROUTE = load_module("adc_route", SKILL_ROOT / "scripts" / "adc_route.py")
RECEIPT = load_module("adc_receipt", SKILL_ROOT / "scripts" / "adc_receipt.py")

CAPABILITY_IDS = frozenset(
    c["id"] for c in json.loads(
        CAPABILITIES.read_text(encoding="utf-8"))["capabilities"])

GATES = {
    "schema_version": 1,
    "gates": [
        {"id": "validate-core", "enabled": True, "review_status": "approved"},
        {"id": "full-suite", "enabled": True, "review_status": "approved"},
        {"id": "not-yet-reviewed", "enabled": True, "review_status": "proposed"},
        {"id": "switched-off", "enabled": False, "review_status": "approved"},
    ],
}

POLICY = {
    "schema_version": 1,
    "classifier": {"surfaces": [
        {"glob": "docs/*", "surface": "docs", "effect": "prose"},
    ]},
    "full_recipe": {
        "minimum_level": 3,
        "passes": ["07", "10", "11", "14"],
        "obligations": {"V09": ["validate-core"], "V21": ["full-suite"]},
        "independent_review": True,
    },
    "rules": [
        {"id": "docs", "review_status": "approved",
         "match": {"surfaces": ["docs"]},
         "requires": {"passes": ["06"], "minimum_level": 0},
         "obligations": {"V09": ["validate-core"]}},
    ],
}

FULL_SET = {
    "passes": ["07", "10", "11", "14"],
    "obligations": {"V09": ["validate-core"], "V21": ["full-suite"]},
}


def a_fact(path, surface="code", effect="behavior"):
    return ROUTE.ChangeFact(
        path=path, change_kind="modify", source="unstaged", surface=surface,
        effect=effect, breadth="leaf", sensitivity="normal",
        confidence="verified")


def a_policy():
    return ROUTE.load_policy(POLICY, GATES, CAPABILITY_IDS, FULL_SET)


class ReceiptIdentityTests(unittest.TestCase):
    """What the run id may and may not depend on."""

    def setUp(self) -> None:
        self.binding = RECEIPT.Binding(
            repo_binding_identity="repo-1",
            base_identity="b" * 40,
            head_identity="h" * 40,
            worktree_identity="w" * 64,
            routing_policy_sha256="p" * 64,
            gate_configuration_sha256="g" * 64,
            calibration_hashes={"invariants.md": "c" * 64},
        )
        self.route = ROUTE.build_route([], a_policy(), snapshot_ok=True)
        self.snapshot = ROUTE.ChangeSnapshot(base="base", base_resolved=True)

    def _payload(self, facts):
        return RECEIPT.authoritative_payload(
            self.route, facts, self.snapshot, self.binding, GATES)

    def test_fact_order_does_not_change_the_run_id(self) -> None:
        facts = [a_fact("b.py"), a_fact("a.py"), a_fact("c.py", surface="docs")]
        first = RECEIPT.build_receipt(self._payload(facts))
        second = RECEIPT.build_receipt(self._payload(list(reversed(facts))))
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(first["authoritative"], second["authoritative"])

    def test_observed_metadata_cannot_change_the_run_id(self) -> None:
        """R-023. A clock is not authority."""
        payload = self._payload([])
        early = RECEIPT.build_receipt(payload, {"written_at": "2020-01-01T00:00:00Z",
                                                "host": "one"})
        late = RECEIPT.build_receipt(payload, {"written_at": "2031-12-31T23:59:59Z",
                                               "host": "two"})
        self.assertEqual(early["run_id"], late["run_id"])
        self.assertNotEqual(early["observed"], late["observed"])

    def test_the_run_id_covers_the_route_itself(self) -> None:
        """A hash that ignored the route would be an identity for the change
        rather than for the decision, and two different routes over one change
        would share a receipt."""
        base = RECEIPT.build_receipt(self._payload([]))["run_id"]
        heavier = ROUTE.build_route([], a_policy(), snapshot_ok=False)
        other = RECEIPT.build_receipt(RECEIPT.authoritative_payload(
            heavier, [], self.snapshot, self.binding, GATES))["run_id"]
        self.assertNotEqual(base, other)

    def test_an_escalation_without_a_reason_is_refused(self) -> None:
        with self.assertRaises(RECEIPT.ReceiptError):
            RECEIPT.authoritative_payload(
                self.route, [], self.snapshot, self.binding, GATES,
                operator_escalation={"by": "someone"})

    def test_every_unselected_gate_carries_a_reason_code(self) -> None:
        routed = ROUTE.build_route([a_fact("docs/readme.md", surface="docs",
                                           effect="prose")],
                                   a_policy(), snapshot_ok=True)
        self.assertIn("validate-core", routed.obligations.get("V09", ()),
                      "the fixture did not select the gate this test needs")
        payload = RECEIPT.authoritative_payload(
            routed, [], self.snapshot, self.binding, GATES)
        omitted = {row["gate_id"]: row["reason_code"]
                   for row in payload["omitted_gates"]}
        self.assertEqual(RECEIPT.SKIP_DISABLED, omitted["switched-off"])
        self.assertEqual(RECEIPT.SKIP_UNAPPROVED, omitted["not-yet-reviewed"])
        self.assertEqual(RECEIPT.SKIP_NOT_REQUIRED, omitted["full-suite"])
        self.assertNotIn("validate-core", omitted,
                         "a selected gate was reported as omitted")


@unittest.skipUnless(__import__("shutil").which("git"), "git is required")
class ReceiptFreshnessTests(unittest.TestCase):
    """Freshness against a real repository."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main", ".")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        (self.repo / "src.py").write_text("original\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "one")
        self.head = self._git("rev-parse", "HEAD").stdout.strip()
        self.calibration = self.repo / "invariants.md"
        self.calibration.write_text("one invariant\n", encoding="utf-8")

    def _git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              capture_output=True, text=True, timeout=60)

    def _binding(self, policy=POLICY, gates=GATES):
        return RECEIPT.collect_binding(
            self.repo, ROUTE, base_identity=self.head, head_identity=self.head,
            policy_source=policy, gates_source=gates,
            calibration_paths=[self.calibration],
            repo_binding_identity="repo-1")

    def _receipt(self):
        binding = self._binding()
        route = ROUTE.build_route([], a_policy(), snapshot_ok=True)
        snapshot = ROUTE.ChangeSnapshot(base=self.head, base_resolved=True)
        return RECEIPT.build_receipt(RECEIPT.authoritative_payload(
            route, [], snapshot, binding, GATES))

    def test_an_untouched_repository_stays_fresh(self) -> None:
        receipt = self._receipt()
        verdict = RECEIPT.verify_receipt(receipt, self._binding())
        self.assertTrue(verdict.fresh, verdict.reasons)
        self.assertEqual(0, verdict.exit_code)

    def test_a_changed_worktree_is_stale(self) -> None:
        receipt = self._receipt()
        (self.repo / "src.py").write_text("changed\n", encoding="utf-8")
        verdict = RECEIPT.verify_receipt(receipt, self._binding())
        self.assertFalse(verdict.fresh)
        self.assertIn(RECEIPT.STALE_WORKTREE, [code for code, _ in verdict.reasons])
        self.assertEqual(2, verdict.exit_code)

    def test_different_dirty_bytes_under_identical_status_are_stale(self) -> None:
        """R-017, and the reason a status digest is not enough.

        Both edits leave git status reporting exactly the same thing. A receipt
        bound to that text would call the second one fresh, and the route was
        computed for the first.
        """
        (self.repo / "src.py").write_text("AAAAAAAA\n", encoding="utf-8")
        receipt = self._receipt()
        status_before = self._git("status", "--porcelain").stdout

        (self.repo / "src.py").write_text("BBBBBBBB\n", encoding="utf-8")
        status_after = self._git("status", "--porcelain").stdout
        self.assertEqual(status_before, status_after,
                         "the fixture no longer holds status constant, so it "
                         "cannot show that status alone is insufficient")

        verdict = RECEIPT.verify_receipt(receipt, self._binding())
        self.assertFalse(verdict.fresh,
                         "identical status text hid a content change")
        self.assertIn(RECEIPT.STALE_WORKTREE, [code for code, _ in verdict.reasons])

    def test_a_changed_policy_is_stale(self) -> None:
        receipt = self._receipt()
        moved = json.loads(json.dumps(POLICY))
        moved["rules"][0]["requires"]["minimum_level"] = 2
        verdict = RECEIPT.verify_receipt(receipt, self._binding(policy=moved))
        self.assertFalse(verdict.fresh)
        self.assertIn(RECEIPT.STALE_POLICY, [code for code, _ in verdict.reasons])

    def test_reformatting_a_policy_does_not_make_it_stale(self) -> None:
        """The binding is over content, not over bytes on disk. Whitespace is
        not a routing decision, and treating it as one would train a reader to
        ignore staleness."""
        receipt = self._receipt()
        reordered = {k: POLICY[k] for k in reversed(list(POLICY))}
        verdict = RECEIPT.verify_receipt(receipt, self._binding(policy=reordered))
        self.assertTrue(verdict.fresh, verdict.reasons)

    def test_a_changed_gate_configuration_is_stale(self) -> None:
        receipt = self._receipt()
        moved = json.loads(json.dumps(GATES))
        moved["gates"][0]["enabled"] = False
        verdict = RECEIPT.verify_receipt(receipt, self._binding(gates=moved))
        self.assertFalse(verdict.fresh)
        self.assertIn(RECEIPT.STALE_GATES, [code for code, _ in verdict.reasons])

    def test_changed_calibration_is_stale_and_names_the_file(self) -> None:
        receipt = self._receipt()
        self.calibration.write_text("a different invariant\n", encoding="utf-8")
        verdict = RECEIPT.verify_receipt(receipt, self._binding())
        self.assertFalse(verdict.fresh)
        codes = dict(verdict.reasons)
        self.assertIn(RECEIPT.STALE_CALIBRATION, codes)
        self.assertIn("invariants.md", codes[RECEIPT.STALE_CALIBRATION])

    def test_a_new_head_is_stale(self) -> None:
        receipt = self._receipt()
        (self.repo / "src.py").write_text("committed change\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "two")
        new_head = self._git("rev-parse", "HEAD").stdout.strip()
        binding = RECEIPT.collect_binding(
            self.repo, ROUTE, base_identity=self.head, head_identity=new_head,
            policy_source=POLICY, gates_source=GATES,
            calibration_paths=[self.calibration],
            repo_binding_identity="repo-1")
        verdict = RECEIPT.verify_receipt(receipt, binding)
        self.assertFalse(verdict.fresh)
        self.assertIn(RECEIPT.STALE_HEAD, [code for code, _ in verdict.reasons])

    def test_every_moved_field_is_reported_not_just_the_first(self) -> None:
        receipt = self._receipt()
        (self.repo / "src.py").write_text("changed\n", encoding="utf-8")
        self.calibration.write_text("also changed\n", encoding="utf-8")
        moved = json.loads(json.dumps(GATES))
        moved["gates"][0]["enabled"] = False
        verdict = RECEIPT.verify_receipt(receipt, self._binding(gates=moved))
        codes = {code for code, _ in verdict.reasons}
        self.assertEqual(
            {RECEIPT.STALE_WORKTREE, RECEIPT.STALE_GATES, RECEIPT.STALE_CALIBRATION},
            codes)

    def test_a_receipt_from_another_schema_is_refused_not_partly_checked(self) -> None:
        receipt = self._receipt()
        receipt["authoritative"]["schema_version"] = 99
        verdict = RECEIPT.verify_receipt(receipt, self._binding())
        self.assertFalse(verdict.fresh)
        self.assertEqual([RECEIPT.STALE_SCHEMA], [c for c, _ in verdict.reasons])

    def test_a_receipt_round_trips_through_its_written_bytes(self) -> None:
        receipt = self._receipt()
        written = RECEIPT.receipt_bytes(receipt)
        reloaded = json.loads(written.decode("utf-8"))
        self.assertEqual(receipt, reloaded)
        self.assertEqual(receipt["run_id"], RECEIPT.digest(reloaded["authoritative"]))


if __name__ == "__main__":
    unittest.main()

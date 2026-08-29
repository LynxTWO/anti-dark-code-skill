from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# macOS puts temporary directories under /var, a symlink to /private/var. The
# managed-path guards refuse to write through a link-like component by design,
# so resolve the temp root once and let the guards police the real path.
tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
CAPABILITIES = SKILL_ROOT / "assets" / "verification-capabilities.json"


def load_module(name: str, path: Path):
    """Load a helper module by path.

    The module is registered in sys.modules before execution. Without that,
    dataclasses cannot resolve a field annotation: dataclasses._is_type reads
    sys.modules.get(cls.__module__).__dict__ and finds None. Any module here
    defining a dataclass fails at import without this line.
    """
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


def load_adc():
    return load_module("adc", SKILL_ROOT / "scripts" / "adc.py")


class CapabilityCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        self.caps = self.catalog["capabilities"]

    def test_catalog_carries_the_two_router_capabilities(self) -> None:
        by_id = {c["id"]: c for c in self.caps}
        self.assertIn("V21", by_id)
        self.assertIn("V22", by_id)
        self.assertEqual(by_id["V21"]["name"], "Affected-unit testing")
        self.assertEqual(by_id["V22"]["name"], "Input fuzz testing")

    def test_catalog_ids_are_contiguous_through_v22(self) -> None:
        ids = sorted(c["id"] for c in self.caps)
        self.assertEqual(ids, [f"V{i:02d}" for i in range(1, 23)])

    def test_every_capability_shares_one_field_shape(self) -> None:
        shapes = {tuple(sorted(c.keys())) for c in self.caps}
        self.assertEqual(len(shapes), 1, f"capability entries disagree on fields: {shapes}")

    def test_new_capabilities_carry_every_required_field(self) -> None:
        required = {"id", "slug", "name", "category", "default_level", "cost",
                    "purpose", "local_work", "agent_work", "adaptations", "selection"}
        by_id = {c["id"]: c for c in self.caps}
        for cap_id in ("V21", "V22"):
            self.assertEqual(required - set(by_id[cap_id]), set(),
                             f"{cap_id} is missing required fields")

    def test_adaptations_cover_the_same_repo_types_as_the_rest(self) -> None:
        by_id = {c["id"]: c for c in self.caps}
        reference = set(by_id["V01"]["adaptations"])
        for cap_id in ("V21", "V22"):
            self.assertEqual(set(by_id[cap_id]["adaptations"]), reference,
                             f"{cap_id} adaptations do not match the catalog")


class CapabilityCountContractTests(unittest.TestCase):
    """The count is asserted in several places. Adding an entry must update all of them."""

    def test_validator_accepts_the_live_catalog(self) -> None:
        adc = load_adc()
        errors, _warnings = adc.validate_skill(SKILL_ROOT, mode="universal")
        capability_errors = [e for e in errors if "apabilit" in e]
        self.assertEqual(capability_errors, [])

    def test_catalog_description_does_not_claim_a_stale_count(self) -> None:
        catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        count = len(catalog["capabilities"])
        description = catalog["description"]
        stale = re.findall(r"\b(\d+)\b", description)
        for number in stale:
            self.assertEqual(int(number), count,
                             f"description says {number}, catalog holds {count}")

    def test_no_shipped_code_hard_codes_a_stale_capability_count(self) -> None:
        catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        count = len(catalog["capabilities"])
        offenders: list[str] = []
        # This file states the pattern, so it always matches itself. Excluding
        # it is a false-positive fix, not a hole: nothing else here asserts a
        # capability count.
        scanned = sorted((SKILL_ROOT / "scripts").glob("*.py"))
        scanned += [p for p in sorted((SKILL_ROOT / "tests").glob("*.py"))
                    if p.name != Path(__file__).name]
        for path in scanned:
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if re.search(
                    r"(?i)\b20\b[^\n]{0,40}capabilit|!= 20\b|range\(1, 21\)|V01\.\.V20", line
                ):
                    offenders.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(offenders, [],
                         f"stale capability count, catalog holds {count}")


ROUTE_SCRIPT = SKILL_ROOT / "scripts" / "adc_route.py"


def load_route():
    return load_module("adc_route", ROUTE_SCRIPT)


# Fixtures follow real `git diff --raw -z --no-abbrev` output captured on
# 2026-08-29. Records are NUL separated and NUL terminated, with no newlines.
NUL = chr(0)
ZERO = "0" * 40
OBJ_A = "5626abf9a2b1f8b0c3d4e5f60718293a4b5c6d7e"
OBJ_B = "f719efd8c1a2b3c4d5e6f708192a3b4c5d6e7f80"


def raw(*records: str) -> bytes:
    return "".join(records).encode("utf-8", "surrogateescape")


class RawParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()

    def test_modify_record_keeps_modes_and_objects(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}keep.py{NUL}"), "committed")
        self.assertEqual(result.problems, ())
        row = result.inputs[0]
        self.assertEqual(row.path, "keep.py")
        self.assertEqual(row.change_kind, "modify")
        self.assertEqual(row.source, "committed")
        self.assertEqual(row.old_object, OBJ_A)
        self.assertEqual(row.new_object, OBJ_B)

    def test_mode_only_change_is_not_reported_as_modify(self) -> None:
        # git update-index --chmod=+x produces the same object on both sides.
        # --name-status cannot separate this from a content edit; raw can.
        result = self.route.parse_raw_z(
            raw(f":100644 100755 {OBJ_A} {OBJ_A} M{NUL}tool.sh{NUL}"), "committed")
        self.assertEqual(result.inputs[0].change_kind, "mode")

    def test_same_object_and_same_mode_stays_modify(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_A} M{NUL}odd.py{NUL}"), "committed")
        self.assertEqual(result.inputs[0].change_kind, "modify")

    def test_add_and_delete_carry_the_null_object(self) -> None:
        result = self.route.parse_raw_z(raw(
            f":000000 100644 {ZERO} {OBJ_A} A{NUL}new.py{NUL}",
            f":100644 000000 {OBJ_A} {ZERO} D{NUL}gone.py{NUL}",
        ), "committed")
        self.assertEqual({r.path: r.change_kind for r in result.inputs},
                         {"new.py": "add", "gone.py": "delete"})

    def test_rename_keeps_both_paths(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_A} R100{NUL}old.py{NUL}new.py{NUL}"), "committed")
        row = result.inputs[0]
        self.assertEqual(row.change_kind, "rename")
        self.assertEqual(row.old_path, "old.py")
        self.assertEqual(row.path, "new.py")

    def test_copy_keeps_both_paths(self) -> None:
        # Real git only emits C when copy detection is requested. Acquisition
        # asks for it; without the flag the same change arrives as A.
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_A} C100{NUL}src.py{NUL}copy.py{NUL}"), "committed")
        row = result.inputs[0]
        self.assertEqual(row.change_kind, "copy")
        self.assertEqual(row.old_path, "src.py")
        self.assertEqual(row.path, "copy.py")

    def test_type_change_and_unmerged_are_preserved(self) -> None:
        result = self.route.parse_raw_z(raw(
            f":100644 120000 {OBJ_A} {OBJ_B} T{NUL}link.txt{NUL}",
            f":100644 100644 {OBJ_A} {OBJ_B} U{NUL}conflict.py{NUL}",
        ), "committed")
        kinds = {r.path: r.change_kind for r in result.inputs}
        self.assertEqual(kinds["link.txt"], "type-change")
        self.assertEqual(kinds["conflict.py"], "unmerged")

    def test_unrecognised_status_letter_is_kept_and_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} X{NUL}weird.py{NUL}"), "committed")
        self.assertEqual(result.inputs[0].change_kind, "unknown")
        self.assertIn("ADC-ROUTE-UNKNOWN-STATUS", result.problems)

    def test_hostile_paths_survive(self) -> None:
        result = self.route.parse_raw_z(raw(
            f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}ode/cafe.py{NUL}",
            f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}we\nird.py{NUL}",
            f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}sp ace.py{NUL}",
        ), "committed")
        self.assertEqual(sorted(r.path for r in result.inputs),
                         ["ode/cafe.py", "sp ace.py", "we\nird.py"])
        self.assertEqual(result.problems, ())

    def test_non_ascii_paths_survive(self) -> None:
        path = "odé/café.py"
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}{path}{NUL}"), "committed")
        self.assertEqual(result.inputs[0].path, path)

    def test_garbage_is_reported_not_silently_dropped(self) -> None:
        result = self.route.parse_raw_z(b"this is not a raw record", "committed")
        self.assertEqual(result.inputs, ())
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_truncated_header_is_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 M{NUL}short.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_rename_missing_its_destination_is_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_A} R100{NUL}only-old.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-TRUNCATED-RECORD", result.problems)

    def test_empty_payload_is_empty_and_clean(self) -> None:
        result = self.route.parse_raw_z(b"", "committed")
        self.assertEqual(result.inputs, ())
        self.assertEqual(result.problems, ())

    def test_untracked_payload_becomes_add_records(self) -> None:
        result = self.route.parse_untracked_z(
            f"new/file.py{NUL}other.txt{NUL}".encode("utf-8"))
        self.assertEqual({r.change_kind for r in result.inputs}, {"add"})
        self.assertEqual({r.source for r in result.inputs}, {"untracked"})
        self.assertEqual(sorted(r.path for r in result.inputs),
                         ["new/file.py", "other.txt"])

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.route.parse_raw_z(b"", "not-a-source")


class RecordingRunner:
    """Stands in for git. Records every argv so the commands can be asserted."""

    def __init__(self, table: dict[str, bytes | None]) -> None:
        self.table = table
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> bytes | None:
        self.calls.append(list(args))
        joined = " ".join(args)
        for key, value in self.table.items():
            if key in joined:
                return value
        return b""

    def argv_for(self, needle: str) -> list[str]:
        for call in self.calls:
            if needle in " ".join(call):
                return call
        raise AssertionError(f"no git call matched {needle!r}: {self.calls}")


class AcquisitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()

    def test_snapshot_unions_all_four_sources(self) -> None:
        run = RecordingRunner({
            "merge-base": b"abc123\n",
            "--cached": raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}staged.py{NUL}"),
            "abc123": raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}committed.py{NUL}"),
            "ls-files": f"untracked.py{NUL}".encode("utf-8"),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        by_source = {i.source: i.path for i in snap.inputs}
        self.assertEqual(by_source.get("committed"), "committed.py")
        self.assertEqual(by_source.get("staged"), "staged.py")
        self.assertEqual(by_source.get("untracked"), "untracked.py")
        self.assertTrue(snap.base_resolved)

    def test_staged_and_unstaged_use_different_comparisons(self) -> None:
        # `diff HEAD` returns staged and unstaged together, so using it for the
        # unstaged source counts every staged change twice. Staged compares the
        # index against HEAD; unstaged compares the worktree against the index.
        run = RecordingRunner({"merge-base": b"abc123\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        staged = run.argv_for("--cached")
        self.assertIn("--cached", staged)
        diff_calls = [c for c in run.calls if c and c[0] == "diff"]
        unstaged = [c for c in diff_calls if "--cached" not in c and "abc123" not in c]
        self.assertEqual(len(unstaged), 1, f"expected one worktree diff: {diff_calls}")
        self.assertNotIn("HEAD", unstaged[0])

    def test_acquisition_requests_rename_and_copy_detection(self) -> None:
        # Without -C git reports a copy as an add, losing the source path.
        run = RecordingRunner({"merge-base": b"abc123\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        for call in [c for c in run.calls if c and c[0] == "diff"]:
            self.assertIn("-M", call)
            self.assertIn("-C", call)
            self.assertIn("--no-abbrev", call)

    def test_unreachable_base_is_reported_not_raised(self) -> None:
        run = RecordingRunner({"merge-base": None})
        snap = self.route.read_change_inputs(Path("."), "origin/nope", runner=run)
        self.assertFalse(snap.base_resolved)
        self.assertIn("ADC-ROUTE-BASE-UNREACHABLE", snap.problems)
        self.assertFalse(snap.complete)

    def test_skill_tree_paths_are_not_filtered_out(self) -> None:
        # D-010. changed_files() drops these through TOOLING_PATH_PREFIXES, and
        # they are where gates.json and routing-policy.json live.
        run = RecordingRunner({
            "merge-base": b"abc123\n",
            "abc123": raw(
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}"
                f".agents/skills/anti-dark-code/calibration/gates.json{NUL}",
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}.anti-dark-code/runs/keep.json{NUL}",
            ),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        paths = {i.path for i in snap.inputs}
        self.assertIn(".agents/skills/anti-dark-code/calibration/gates.json", paths)
        self.assertIn(".anti-dark-code/runs/keep.json", paths)

    def test_parser_problems_reach_the_snapshot(self) -> None:
        run = RecordingRunner({"merge-base": b"abc123\n", "abc123": b"garbage"})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", snap.problems)
        self.assertFalse(snap.complete)

    def test_unreadable_source_is_reported(self) -> None:
        run = RecordingRunner({"merge-base": b"abc123\n", "ls-files": None})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-UNTRACKED-UNREADABLE", snap.problems)
        self.assertFalse(snap.complete)

    def test_ordering_is_canonical(self) -> None:
        run = RecordingRunner({
            "merge-base": b"abc123\n",
            "abc123": raw(
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}zeta.py{NUL}",
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}alpha.py{NUL}",
            ),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        committed = [i.path for i in snap.inputs if i.source == "committed"]
        self.assertEqual(committed, sorted(committed))

    def test_clean_snapshot_is_complete(self) -> None:
        run = RecordingRunner({"merge-base": b"abc123\n"})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertTrue(snap.complete)


@unittest.skipUnless(shutil.which("git"), "git is required")
class AcquisitionAgainstRealGitTests(unittest.TestCase):
    """Acquisition against a real repository, not a recorded transcript."""

    def setUp(self) -> None:
        self.route = load_route()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", ".")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        (self.repo / "src.py").write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
        (self.repo / "old.py").write_text("old\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "base")
        self._git("branch", "base-ref")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), *args],
                       check=True, capture_output=True)

    def test_staged_change_is_not_counted_twice(self) -> None:
        (self.repo / "src.py").write_text("a\nb\nc\nd\nSTAGED\n", encoding="utf-8")
        self._git("add", "src.py")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        staged = [i for i in snap.inputs if i.path == "src.py" and i.source == "staged"]
        unstaged = [i for i in snap.inputs if i.path == "src.py" and i.source == "unstaged"]
        self.assertEqual(len(staged), 1)
        self.assertEqual(unstaged, [], "a staged change must not also appear as unstaged")

    def test_untracked_file_is_acquired(self) -> None:
        (self.repo / "fresh.py").write_text("new\n", encoding="utf-8")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        self.assertIn("fresh.py", {i.path for i in snap.inputs if i.source == "untracked"})

    def test_committed_rename_keeps_its_source_path(self) -> None:
        self._git("mv", "old.py", "new.py")
        self._git("commit", "-qm", "rename")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        renames = [i for i in snap.inputs if i.change_kind == "rename"]
        self.assertEqual(len(renames), 1, f"expected one rename: {snap.inputs}")
        self.assertEqual(renames[0].old_path, "old.py")
        self.assertEqual(renames[0].path, "new.py")

    def test_unreachable_base_blocks_completeness(self) -> None:
        snap = self.route.read_change_inputs(self.repo, "refs/heads/no-such-branch")
        self.assertFalse(snap.base_resolved)
        self.assertFalse(snap.complete)


if __name__ == "__main__":
    unittest.main()

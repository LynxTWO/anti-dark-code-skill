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

    def test_catalog_ids_are_contiguous_with_no_gaps(self) -> None:
        # Derived from the one constant rather than a literal, so adding a
        # capability does not leave a second count contract to find by hand.
        adc = load_adc()
        ids = sorted(c["id"] for c in self.caps)
        self.assertEqual(ids, [f"V{i:02d}" for i in range(1, adc.CAPABILITY_COUNT + 1)])

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
BASE = "abc1230000000000000000000000000000000000"


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

    def test_mode_change_survives_when_content_also_changed(self) -> None:
        # H-04. Objects differ, so the change_kind stays modify, but the
        # executable bit still moved. Keying the mode signal off object equality
        # loses it exactly when a file becomes executable in the same commit
        # that edits it, which is the interesting case.
        result = self.route.parse_raw_z(
            raw(f":100644 100755 {OBJ_A} {OBJ_B} M{NUL}tool.sh{NUL}"), "committed")
        row = result.inputs[0]
        self.assertEqual(row.change_kind, "modify")
        self.assertTrue(row.mode_changed, "the mode transition disappeared")

    def test_pure_mode_change_is_both_kind_and_flag(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100755 {OBJ_A} {OBJ_A} M{NUL}tool.sh{NUL}"), "committed")
        self.assertEqual(result.inputs[0].change_kind, "mode")
        self.assertTrue(result.inputs[0].mode_changed)

    def test_creation_and_deletion_are_not_mode_changes(self) -> None:
        result = self.route.parse_raw_z(raw(
            f":000000 100644 {ZERO} {OBJ_A} A{NUL}new.py{NUL}",
            f":100644 000000 {OBJ_A} {ZERO} D{NUL}gone.py{NUL}",
        ), "committed")
        for row in result.inputs:
            self.assertFalse(row.mode_changed,
                             f"{row.path} creation or deletion read as a mode change")

    def test_unchanged_mode_sets_no_flag(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}plain.py{NUL}"), "committed")
        self.assertFalse(result.inputs[0].mode_changed)

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

    def test_payload_without_a_terminal_nul_is_reported(self) -> None:
        # H-02. Truncated transport looked exactly like a clean short diff.
        payload = raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}file.py")
        result = self.route.parse_raw_z(payload, "committed")
        self.assertIn("ADC-ROUTE-UNTERMINATED-PAYLOAD", result.problems)

    def test_a_terminated_payload_is_not_reported(self) -> None:
        payload = raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}file.py{NUL}")
        self.assertEqual(self.route.parse_raw_z(payload, "committed").problems, ())

    def test_nonsense_header_fields_are_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":bad bad bad bad M{NUL}file.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)
        self.assertEqual(result.inputs, (), "a nonsense header must not yield a row")

    def test_a_header_with_extra_fields_is_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} M extra{NUL}file.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_bad_mode_is_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":10064x 100644 {OBJ_A} {OBJ_B} M{NUL}file.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_bad_object_id_is_reported(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 nothex {OBJ_B} M{NUL}file.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_sha256_object_id_is_accepted(self) -> None:
        # Repositories can use sha256. Rejecting a 64 character id would make
        # the parser fail closed on a perfectly ordinary repository.
        long_a, long_b = "a" * 64, "b" * 64
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {long_a} {long_b} M{NUL}file.py{NUL}"), "committed")
        self.assertEqual(result.problems, ())
        self.assertEqual(result.inputs[0].path, "file.py")

    def test_untracked_payload_without_a_terminal_nul_is_reported(self) -> None:
        result = self.route.parse_untracked_z(b"new/file.py")
        self.assertIn("ADC-ROUTE-UNTERMINATED-PAYLOAD", result.problems)

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
            "merge-base": BASE.encode("ascii") + b"\n",
            "--cached": raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}staged.py{NUL}"),
            BASE: raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}committed.py{NUL}"),
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
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        staged = run.argv_for("--cached")
        self.assertIn("--cached", staged)
        diff_calls = [c for c in run.calls if "diff" in c]
        self.assertTrue(diff_calls, "no diff call was made at all")
        unstaged = [c for c in diff_calls if "--cached" not in c and BASE not in c]
        self.assertEqual(len(unstaged), 1, f"expected one worktree diff: {diff_calls}")
        self.assertNotIn("HEAD", unstaged[0])

    def test_acquisition_requests_rename_and_copy_detection(self) -> None:
        # Without -C git reports a copy as an add, losing the source path.
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        diff_calls = [c for c in run.calls if "diff" in c]
        # Without this the loop below asserts nothing when the filter misses.
        self.assertEqual(len(diff_calls), 3, f"expected three diffs: {run.calls}")
        for call in diff_calls:
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
            "merge-base": BASE.encode("ascii") + b"\n",
            BASE: raw(
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
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n", BASE: b"garbage"})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", snap.problems)
        self.assertFalse(snap.complete)

    def test_a_blank_merge_base_result_does_not_count_as_resolved(self) -> None:
        # H-02. A successful call returning whitespace was treated as a resolved
        # base with an empty id, and the snapshot claimed to be complete.
        run = RecordingRunner({"merge-base": b"\n"})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertFalse(snap.base_resolved)
        self.assertFalse(snap.complete)
        self.assertIn("ADC-ROUTE-BASE-UNREACHABLE", snap.problems)

    def test_a_multi_line_merge_base_result_is_rejected(self) -> None:
        run = RecordingRunner({"merge-base": (BASE + "\n" + OBJ_A + "\n").encode("ascii")})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertFalse(snap.complete)

    def test_framing_problems_reach_the_snapshot(self) -> None:
        run = RecordingRunner({
            "merge-base": BASE.encode("ascii") + b"\n",
            "ls-files": b"untracked-without-terminator.py",
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-UNTERMINATED-PAYLOAD", snap.problems)
        self.assertFalse(snap.complete)

    def test_unreadable_source_is_reported(self) -> None:
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n", "ls-files": None})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-UNTRACKED-UNREADABLE", snap.problems)
        self.assertFalse(snap.complete)

    def test_ordering_is_canonical(self) -> None:
        run = RecordingRunner({
            "merge-base": BASE.encode("ascii") + b"\n",
            BASE: raw(
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}zeta.py{NUL}",
                f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}alpha.py{NUL}",
            ),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        committed = [i.path for i in snap.inputs if i.source == "committed"]
        self.assertEqual(committed, sorted(committed))

    def test_clean_snapshot_is_complete(self) -> None:
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n"})
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertTrue(snap.complete)

    def test_every_git_call_disables_repository_configured_programs(self) -> None:
        # A repository can point core.fsmonitor at a program of its choosing and
        # git will run it for us. This module claims to read metadata only, so
        # the isolation flags have to be on every call, not only the diffs.
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertTrue(run.calls)
        for call in run.calls:
            joined = " ".join(call)
            self.assertIn("core.fsmonitor=false", joined, f"unisolated call: {call}")
            self.assertIn("diff.external=", joined, f"unisolated call: {call}")
            self.assertIn("--no-optional-locks", joined, f"unisolated call: {call}")

    def test_diff_calls_refuse_an_external_diff_driver(self) -> None:
        run = RecordingRunner({"merge-base": BASE.encode("ascii") + b"\n"})
        self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        diff_calls = [c for c in run.calls if "diff" in c]
        self.assertTrue(diff_calls, "no diff call was made at all")
        for call in diff_calls:
            self.assertIn("--no-ext-diff", call, f"diff without --no-ext-diff: {call}")


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

    def test_a_copy_from_an_unchanged_source_keeps_its_source_path(self) -> None:
        # H-03. Git only considers an unchanged source with --find-copies-harder.
        # Without it this arrives as an ordinary add and the source path, along
        # with whatever sensitivity it carried, never reaches classification.
        (self.repo / "copied.py").write_text(
            (self.repo / "src.py").read_text(encoding="utf-8"), encoding="utf-8")
        self._git("add", "copied.py")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        copies = [i for i in snap.inputs if i.change_kind == "copy"]
        self.assertEqual(len(copies), 1, f"expected one copy record: {snap.inputs}")
        self.assertEqual(copies[0].old_path, "src.py")
        self.assertEqual(copies[0].path, "copied.py")

    def test_a_staged_content_and_mode_change_keeps_its_mode_signal(self) -> None:
        # H-04 end to end, against real git rather than a fixture.
        tool = self.repo / "tool.sh"
        tool.write_text("#!/bin/sh\necho one\n", encoding="utf-8")
        self._git("add", "tool.sh")
        self._git("commit", "-qm", "add tool")
        tool.write_text("#!/bin/sh\necho two\nCHANGED\n", encoding="utf-8")
        self._git("add", "tool.sh")
        self._git("update-index", "--chmod=+x", "tool.sh")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        rows = [i for i in snap.inputs if i.path == "tool.sh" and i.source == "staged"]
        self.assertTrue(rows, f"no staged record for tool.sh: {snap.inputs}")
        self.assertTrue(any(r.mode_changed for r in rows),
                        "real content-plus-mode change lost its mode signal")

    def test_a_hostile_repository_cannot_run_its_own_program(self) -> None:
        """The boundary the module docstring claims, tested rather than asserted.

        A repository that sets core.fsmonitor to a script gets that script run
        by our own git calls unless the isolation flags are present. This is the
        untrusted-repository case anti-dark-code exists for, and pass 00 forbids
        executing repository code during preflight.
        """
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        sentinel = self.repo / "sentinel.txt"
        probe = hooks / "fsmonitor-probe"
        probe.write_text(
            "#!/bin/sh\n"
            f'echo executed >> "{sentinel.as_posix()}"\n'
            'echo ""\n',
            encoding="utf-8", newline="\n",
        )
        probe.chmod(0o755)
        self._git("config", "core.fsmonitor", ".git/hooks/fsmonitor-probe")
        self._git("config", "diff.external", ".git/hooks/fsmonitor-probe")
        (self.repo / "src.py").write_text("a\nb\nc\nd\nCHANGED\n", encoding="utf-8")

        snap = self.route.read_change_inputs(self.repo, "base-ref")

        self.assertFalse(
            sentinel.exists(),
            "the repository executed its own program during acquisition: "
            + (sentinel.read_text(encoding='utf-8') if sentinel.exists() else ""),
        )
        self.assertTrue(snap.inputs, "acquisition must still work while isolated")

    def test_acquisition_does_not_write_to_the_repository(self) -> None:
        """R-027. Reading must not modify the index or the worktree.

        Git refreshes the index opportunistically during ordinary reads, which
        is a write to a repository the caller was only inspecting.
        GIT_OPTIONAL_LOCKS=0 and --no-optional-locks suppress that.
        """
        (self.repo / "src.py").write_text("a\nb\nc\nd\nCHANGED\n", encoding="utf-8")
        index = self.repo / ".git" / "index"

        def fingerprint() -> tuple:
            worktree = sorted(
                (p.relative_to(self.repo).as_posix(), p.stat().st_size)
                for p in self.repo.rglob("*")
                if p.is_file() and ".git" not in p.parts
            )
            return (index.read_bytes() if index.exists() else b"", worktree)

        before = fingerprint()
        self.route.read_change_inputs(self.repo, "base-ref")
        self.assertEqual(fingerprint(), before,
                         "acquisition modified the index or the worktree")


CLASSIFIER = {
    "surfaces": [
        {"glob": "*.md", "surface": "docs", "effect": "prose", "breadth": "leaf"},
        {"glob": "anti-dark-code/SKILL.md", "surface": "skill-policy",
         "effect": "verification-authority", "breadth": "repository"},
        {"glob": ".github/workflows/*", "surface": "ci",
         "effect": "verification-authority", "breadth": "repository"},
        {"glob": "auth/*", "surface": "product", "effect": "behavior",
         "breadth": "package", "sensitivity": "auth"},
    ]
}


class ClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()

    def _snapshot(self, *inputs):
        return self.route.ChangeSnapshot(
            inputs=tuple(inputs), base="abc", base_resolved=True)

    def _facts(self, *inputs):
        return self.route.collect_change_facts(self._snapshot(*inputs), CLASSIFIER)

    def test_a_broad_glob_cannot_mask_a_specific_one(self) -> None:
        # "*.md" matches SKILL.md and calls it prose. The specific entry calls
        # it verification authority. Both facts must exist, so every rule that
        # would fire does fire and union decides the rest. First-match-wins
        # would silently drop the authority reading.
        facts = self._facts(self.route.ChangeInput(
            path="anti-dark-code/SKILL.md", change_kind="modify", source="committed"))
        effects = {f.effect for f in facts}
        self.assertIn("verification-authority", effects)
        self.assertIn("prose", effects)

    def test_skill_md_is_never_only_inert_documentation(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="anti-dark-code/SKILL.md", change_kind="modify", source="committed"))
        self.assertTrue(any(f.surface == "skill-policy" for f in facts))

    def test_unmapped_path_is_marked_unknown_not_guessed(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="somewhere/new.bin", change_kind="modify", source="committed"))
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].confidence, "unknown")

    def test_a_mapped_path_is_verified(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="README.md", change_kind="modify", source="committed"))
        self.assertEqual({f.confidence for f in facts}, {"verified"})

    def test_rename_emits_facts_for_both_sides(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="README.md", old_path="auth/login.py",
            change_kind="rename", source="committed"))
        by_path = {f.path: f for f in facts}
        self.assertIn("README.md", by_path)
        self.assertIn("auth/login.py", by_path)
        # The sensitive source must not vanish because the destination is docs.
        self.assertEqual(by_path["auth/login.py"].sensitivity, "auth")

    def test_copy_emits_facts_for_both_sides(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="README.md", old_path="auth/login.py",
            change_kind="copy", source="committed"))
        self.assertEqual({f.path for f in facts} & {"auth/login.py"}, {"auth/login.py"})

    def test_related_path_links_both_sides_of_a_rename(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="README.md", old_path="auth/login.py",
            change_kind="rename", source="committed"))
        by_path = {f.path: f for f in facts}
        self.assertEqual(by_path["README.md"].related_path, "auth/login.py")
        self.assertEqual(by_path["auth/login.py"].related_path, "README.md")

    def test_ordering_is_deterministic_under_shuffled_input(self) -> None:
        a = self.route.ChangeInput(path="zeta.md", change_kind="modify", source="committed")
        b = self.route.ChangeInput(path="alpha.md", change_kind="modify", source="committed")
        self.assertEqual(self._facts(a, b), self._facts(b, a))

    def test_every_fact_field_is_a_closed_enum_value(self) -> None:
        facts = self._facts(
            self.route.ChangeInput(path=".github/workflows/tests.yml",
                                   change_kind="modify", source="committed"),
            self.route.ChangeInput(path="auth/login.py",
                                   change_kind="delete", source="staged"),
            self.route.ChangeInput(path="mystery.bin",
                                   change_kind="modify", source="untracked"),
        )
        for fact in facts:
            self.assertIn(fact.surface, self.route.SURFACES)
            self.assertIn(fact.effect, self.route.EFFECTS)
            self.assertIn(fact.breadth, self.route.BREADTHS)
            self.assertIn(fact.sensitivity, self.route.SENSITIVITIES)
            self.assertIn(fact.confidence, self.route.CONFIDENCES)
            self.assertIn(fact.change_kind, self.route.CHANGE_KINDS)
            self.assertIn(fact.source, self.route.CHANGE_SOURCES)

    def test_mode_changed_reaches_the_fact_so_a_rule_can_match_it(self) -> None:
        # H-04. The signal is worthless if it stops at ChangeInput: rules match
        # facts, so a content-plus-mode change would still be invisible.
        facts = self._facts(self.route.ChangeInput(
            path="auth/login.py", change_kind="modify", source="staged",
            old_mode="100644", new_mode="100755", mode_changed=True))
        self.assertTrue(facts)
        self.assertTrue(all(f.mode_changed for f in facts))

    def test_an_ordinary_change_carries_no_mode_flag(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="auth/login.py", change_kind="modify", source="staged"))
        self.assertTrue(all(not f.mode_changed for f in facts))

    def test_change_kind_and_source_survive_classification(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="auth/login.py", change_kind="delete", source="staged"))
        self.assertEqual(facts[0].change_kind, "delete")
        self.assertEqual(facts[0].source, "staged")

    def test_a_classifier_typo_is_rejected_not_passed_through(self) -> None:
        # H-05. The frozensets described valid values without enforcing them, so
        # a one-character policy typo silently changed which rules matched.
        for field, bad in (("surface", "BOGUS"), ("effect", "BOGUS"),
                           ("breadth", "BOGUS"), ("sensitivity", "BOGUS")):
            entry = {"glob": "*.py", "surface": "product", "effect": "behavior",
                     "breadth": "leaf", "sensitivity": "normal"}
            entry[field] = bad
            snap = self._snapshot(self.route.ChangeInput(
                path="a.py", change_kind="modify", source="committed"))
            with self.assertRaises(ValueError, msg=f"{field}={bad} was accepted"):
                self.route.collect_change_facts(snap, {"surfaces": [entry]})

    def test_a_classifier_entry_without_a_glob_is_rejected(self) -> None:
        snap = self._snapshot(self.route.ChangeInput(
            path="a.py", change_kind="modify", source="committed"))
        with self.assertRaises(ValueError):
            self.route.collect_change_facts(
                snap, {"surfaces": [{"surface": "product", "effect": "behavior"}]})

    def test_a_bad_change_kind_or_source_is_rejected(self) -> None:
        for field, bad in (("change_kind", "BOGUS_KIND"), ("source", "BOGUS_SOURCE")):
            kwargs = {"path": "a.py", "change_kind": "modify", "source": "committed"}
            kwargs[field] = bad
            snap = self._snapshot(self.route.ChangeInput(**kwargs))
            with self.assertRaises(ValueError, msg=f"{field}={bad} was accepted"):
                self.route.collect_change_facts(snap, CLASSIFIER)

    def test_duplicate_inputs_collapse_to_one_fact(self) -> None:
        # H-09. The suite claimed deduplication but never submitted a duplicate,
        # so removing the collapse survived every test.
        row = self.route.ChangeInput(
            path="README.md", change_kind="modify", source="committed")
        once = self._facts(row)
        twice = self._facts(row, row)
        self.assertEqual(once, twice)

    def test_ordering_is_stable_across_processes(self) -> None:
        # H-06. Two source-side copy facts tied on every sort key and differed
        # only in related_path, so set iteration order leaked into the result
        # and PYTHONHASHSEED changed it.
        import os
        import subprocess as sp
        script = (
            "import importlib.util,sys;"
            f"spec=importlib.util.spec_from_file_location('adc_route', r'{ROUTE_SCRIPT}');"
            "m=importlib.util.module_from_spec(spec);sys.modules['adc_route']=m;"
            "spec.loader.exec_module(m);"
            "cls={'surfaces':[{'glob':'src.py','surface':'product',"
            "'effect':'behavior','breadth':'leaf'}]};"
            "snap=m.ChangeSnapshot(inputs=("
            "m.ChangeInput(path='a.py',old_path='src.py',change_kind='copy',source='committed'),"
            "m.ChangeInput(path='b.py',old_path='src.py',change_kind='copy',source='committed'),"
            "),base='x',base_resolved=True);"
            "print([(f.path,f.related_path) for f in m.collect_change_facts(snap,cls)])"
        )
        results = set()
        for seed in ("1", "2", "3", "4", "5"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            done = sp.run([sys.executable, "-c", script],
                          capture_output=True, text=True, env=env, timeout=60)
            self.assertEqual(done.returncode, 0, done.stderr)
            results.add(done.stdout.strip())
        self.assertEqual(len(results), 1,
                         f"fact order depends on the hash seed: {results}")

    def test_glob_matching_is_case_sensitive_on_every_platform(self) -> None:
        # H-07. fnmatch applies os.path.normcase, so Windows matched
        # case-insensitively while Linux and macOS did not. Git paths are
        # case-sensitive, so the same diff and policy produced different facts
        # depending on the host, and therefore different receipts.
        facts = self._facts(self.route.ChangeInput(
            path="AUTH/login.py", change_kind="modify", source="committed"))
        self.assertEqual([f.confidence for f in facts], ["unknown"],
                         "AUTH/ matched the auth/ glob; matching is case-folded")

    def test_exact_case_still_matches(self) -> None:
        facts = self._facts(self.route.ChangeInput(
            path="auth/login.py", change_kind="modify", source="committed"))
        self.assertEqual({f.sensitivity for f in facts}, {"auth"})

    def test_backslash_separators_normalize_before_matching(self) -> None:
        # A Windows-shaped path must match a policy written with forward
        # slashes, otherwise the policy would need two spellings per rule.
        facts = self._facts(self.route.ChangeInput(
            path="auth\\login.py", change_kind="modify", source="committed"))
        self.assertEqual({f.sensitivity for f in facts}, {"auth"})

    def test_classification_is_pure_and_takes_no_repository(self) -> None:
        snapshot = self._snapshot(self.route.ChangeInput(
            path="README.md", change_kind="modify", source="committed"))
        first = self.route.collect_change_facts(snapshot, CLASSIFIER)
        second = self.route.collect_change_facts(snapshot, CLASSIFIER)
        self.assertEqual(first, second)


GATES = {
    "schema_version": 1,
    "gates": [
        {"id": "validate-core", "enabled": True, "review_status": "approved"},
        {"id": "distribution", "enabled": True, "review_status": "approved"},
        {"id": "hostile-environment", "enabled": True, "review_status": "approved"},
        {"id": "full-suite", "enabled": True, "review_status": "approved"},
        {"id": "not-yet-reviewed", "enabled": True, "review_status": "proposed"},
        {"id": "switched-off", "enabled": False, "review_status": "approved"},
    ],
}


POLICY = {
    "schema_version": 1,
    "classifier": {"surfaces": []},
    "full_recipe": {
        "minimum_level": 3,
        "passes": ["07", "10", "11", "14"],
        "obligations": {
            "V08": ["distribution"],
            "V09": ["validate-core"],
            "V12": ["hostile-environment"],
            "V21": ["full-suite"],
        },
        "independent_review": True,
    },
    "rules": [
        {"id": "docs", "review_status": "approved",
         "match": {"surfaces": ["docs"]},
         "requires": {"passes": ["06"], "minimum_level": 0},
         "obligations": {"V09": ["validate-core"]}},
        # Deliberately shares capability V09 with the docs rule while naming a
        # different gate. Union keeps both; assignment keeps one. Without a pair
        # like this the monotonic test cannot tell the two apart.
        {"id": "site", "review_status": "approved",
         "match": {"surfaces": ["site"]},
         "requires": {"passes": ["11"], "minimum_level": 2},
         "obligations": {"V09": ["distribution"]}},
        # K-10. Discriminated only by paths, so deleting the path predicate
        # makes it fire on everything and a test notices.
        {"id": "secret-path", "review_status": "approved",
         "match": {"paths": ["secrets/*"]},
         "requires": {"passes": ["04"], "minimum_level": 2},
         "obligations": {"V08": ["distribution"]}},
        # K-11. Discriminated only by mode_changed, for the same reason.
        {"id": "mode-flip", "review_status": "approved",
         "match": {"mode_changed": True},
         "requires": {"passes": ["10"], "minimum_level": 1},
         "obligations": {"V21": ["full-suite"]}},
        {"id": "authority", "review_status": "approved",
         "match": {"effects": ["verification-authority"]},
         "requires": {"passes": ["07", "14"], "minimum_level": 3,
                      "force_full": True, "independent_review": True},
         "obligations": {"V12": ["hostile-environment"]}},
    ],
}


def loaded(route):
    """POLICY as build_route now requires it: validated and frozen."""
    return route.load_policy(POLICY, GATES)


def fact(route, path, **over):
    base = dict(path=path, change_kind="modify", source="committed",
                surface="docs", effect="prose", breadth="leaf",
                sensitivity="normal", confidence="verified")
    base.update(over)
    return route.ChangeFact(**base)


class RouteBuildingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()
        self.loaded = loaded(self.route)

    def test_a_prose_change_takes_the_cheap_route(self) -> None:
        built = self.route.build_route((fact(self.route, "README.md"),), loaded(self.route))
        self.assertEqual(built.minimum_level, 0)
        self.assertFalse(built.force_full)
        self.assertEqual(built.matched_rule_ids, frozenset({"docs"}))

    def test_two_rules_union_their_requirements(self) -> None:
        built = self.route.build_route((
            fact(self.route, "README.md"),
            fact(self.route, "docs/index.html", surface="site"),
        ), self.loaded)
        self.assertEqual(built.passes, frozenset({"06", "11"}))
        self.assertEqual(built.minimum_level, 2)
        self.assertEqual(built.matched_rule_ids, frozenset({"docs", "site"}))

    def test_one_capability_unions_gates_from_several_rules(self) -> None:
        # R-010 and G-007. Assignment would leave one gate here and the route
        # would claim coverage it does not have.
        built = self.route.build_route((
            fact(self.route, "README.md"),
            fact(self.route, "docs/index.html", surface="site"),
        ), self.loaded)
        self.assertEqual(built.obligations["V09"],
                         frozenset({"validate-core", "distribution"}))

    def test_authority_change_forces_the_full_recipe(self) -> None:
        # R-022 and G-004. force_full must populate passes, obligations, and
        # level from the recipe, not merely raise the level.
        built = self.route.build_route((
            fact(self.route, ".github/workflows/tests.yml",
                 surface="ci", effect="verification-authority"),
        ), self.loaded)
        self.assertTrue(built.force_full)
        self.assertEqual(built.minimum_level, 3)
        self.assertTrue(built.passes >= frozenset({"07", "10", "11", "14"}))
        for capability, gates in POLICY["full_recipe"]["obligations"].items():
            self.assertTrue(built.obligations[capability] >= frozenset(gates),
                            f"full route omitted {capability}")
        self.assertTrue(built.independent_review)

    def test_unmapped_path_forces_full_and_is_recorded(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "mystery.bin", confidence="unknown"),), self.loaded)
        self.assertTrue(built.force_full)
        self.assertIn("mystery.bin", built.unmapped_paths)
        self.assertIn("ADC-ROUTE-UNMAPPED-PATH", built.unknowns)

    def test_an_incomplete_snapshot_forces_full(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "README.md"),), self.loaded, snapshot_ok=False)
        self.assertTrue(built.force_full)
        self.assertIn("ADC-ROUTE-SNAPSHOT-INCOMPLETE", built.unknowns)

    def test_a_fact_matching_no_rule_forces_full(self) -> None:
        # A fact can be classified and still match no reviewed rule. That is an
        # unrouted change, not a cheap one.
        built = self.route.build_route(
            (fact(self.route, "odd.py", surface="tests", effect="behavior"),), self.loaded)
        self.assertTrue(built.force_full)

    def test_a_rule_discriminated_only_by_paths_fires_on_the_right_path(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "secrets/key.pem", surface="product",
                  effect="behavior"),), self.loaded)
        self.assertIn("secret-path", built.matched_rule_ids)
        self.assertEqual(built.minimum_level, 2)

    def test_a_rule_discriminated_only_by_paths_ignores_other_paths(self) -> None:
        # If the path predicate were removed this rule would fire here too.
        built = self.route.build_route((fact(self.route, "README.md"),), self.loaded)
        self.assertNotIn("secret-path", built.matched_rule_ids)

    def test_a_rule_discriminated_only_by_mode_fires_on_a_mode_change(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "tool.sh", surface="product", effect="behavior",
                  mode_changed=True),), self.loaded)
        self.assertIn("mode-flip", built.matched_rule_ids)

    def test_a_rule_discriminated_only_by_mode_ignores_ordinary_changes(self) -> None:
        built = self.route.build_route((fact(self.route, "README.md"),), self.loaded)
        self.assertNotIn("mode-flip", built.matched_rule_ids)

    def test_path_matching_is_case_sensitive_in_rules_too(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "SECRETS/key.pem", surface="product",
                  effect="behavior"),), self.loaded)
        self.assertNotIn("secret-path", built.matched_rule_ids)

    def test_order_does_not_change_the_route(self) -> None:
        a = fact(self.route, "README.md")
        b = fact(self.route, "docs/index.html", surface="site")
        self.assertEqual(self.route.build_route((a, b), self.loaded),
                         self.route.build_route((b, a), self.loaded))

    def test_an_unapproved_rule_never_matches(self) -> None:
        policy = json.loads(json.dumps(POLICY))
        policy["rules"][0]["review_status"] = "proposed"
        built = self.route.build_route(
            (fact(self.route, "README.md"),),
            self.route.load_policy(policy, GATES))
        self.assertNotIn("docs", built.matched_rule_ids)
        self.assertTrue(built.force_full, "an unmatched fact must force full")


class HintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()
        self.loaded = loaded(self.route)
        self.loaded = loaded(self.route)
        self.base = self.route.build_route((fact(self.route, "README.md"),), loaded(self.route))

    def test_a_hint_can_raise_the_level(self) -> None:
        raised = self.route.apply_hints(self.base, {"minimum_level": 2})
        self.assertEqual(raised.minimum_level, 2)

    def test_a_hint_can_add_passes_and_obligations(self) -> None:
        raised = self.route.apply_hints(
            self.base, {"passes": ["07"], "obligations": {"V12": ["hostile-environment"]}})
        self.assertIn("07", raised.passes)
        self.assertEqual(raised.obligations["V12"], frozenset({"hostile-environment"}))

    def test_a_hint_can_add_a_gate_to_an_existing_capability(self) -> None:
        raised = self.route.apply_hints(
            self.base, {"obligations": {"V09": ["distribution"]}})
        self.assertEqual(raised.obligations["V09"],
                         frozenset({"validate-core", "distribution"}))

    def test_no_hint_field_can_lower_anything(self) -> None:
        # R-020. Every field, not only the level. A hint that raises one
        # dimension while narrowing another is the case worth catching.
        high = self.route.build_route((
            fact(self.route, ".github/workflows/tests.yml",
                 surface="ci", effect="verification-authority"),
            fact(self.route, "docs/index.html", surface="site"),
        ), self.loaded)
        hostile = [
            {"minimum_level": 0},
            {"force_full": False},
            {"independent_review": False},
            {"passes": []},
            {"obligations": {}},
            {"obligations": {"V09": []}},
            {"matched_rule_ids": []},
            {"unmapped_paths": []},
            {"unknowns": []},
            {"minimum_level": 1, "force_full": False},
        ]
        for hint in hostile:
            after = self.route.apply_hints(high, hint)
            assert_route_not_lower(self, high, after, f"hint {hint}")

    def test_a_hint_cannot_clear_an_existing_reason_or_unmapped_path(self) -> None:
        # K-12 and K-13. The earlier hostile-hint route had both sets empty, so
        # replacing their union with assignment could not show a loss. This
        # route carries a real reason code and a real unmapped path.
        carrying = self.route.build_route(
            (fact(self.route, "mystery.bin", confidence="unknown"),), self.loaded)
        self.assertTrue(carrying.unknowns, "fixture must carry a reason code")
        self.assertTrue(carrying.unmapped_paths, "fixture must carry an unmapped path")
        for hint in ({"unknowns": []}, {"unmapped_paths": []},
                     {"unknowns": ["other"]}, {"unmapped_paths": ["other"]}, {}):
            after = self.route.apply_hints(carrying, hint)
            self.assertIn("ADC-ROUTE-UNMAPPED-PATH", after.unknowns,
                          f"hint {hint} dropped an existing reason code")
            self.assertIn("mystery.bin", after.unmapped_paths,
                          f"hint {hint} dropped an existing unmapped path")

    def test_a_hint_cannot_invent_a_rule_match(self) -> None:
        after = self.route.apply_hints(self.base, {"matched_rule_ids": ["authority"]})
        self.assertEqual(after.matched_rule_ids, self.base.matched_rule_ids)


def assert_route_not_lower(case, smaller, larger, context) -> None:
    """Every field of `larger` must be at least `smaller`.

    Fields are read from the dataclass rather than listed here, so a new Route
    field is covered automatically. An unhandled field type fails loudly instead
    of being skipped, which is how a field silently escapes a property test.
    """
    import dataclasses
    for field in dataclasses.fields(smaller):
        a = getattr(smaller, field.name)
        b = getattr(larger, field.name)
        if isinstance(a, bool):
            if a:
                case.assertTrue(b, f"{context}: {field.name} went true to false")
        elif isinstance(a, int):
            case.assertGreaterEqual(b, a, f"{context}: {field.name} decreased")
        elif isinstance(a, (set, frozenset)):
            case.assertTrue(b >= a, f"{context}: {field.name} lost members")
        elif isinstance(a, dict):
            for key, gates in a.items():
                case.assertIn(key, b, f"{context}: {field.name} dropped {key}")
                case.assertTrue(b[key] >= gates,
                                f"{context}: {field.name}[{key}] lost gates")
        else:
            case.fail(f"{context}: no comparison defined for "
                      f"{field.name} of type {type(a).__name__}")


class MonotonicityTests(unittest.TestCase):
    """R-001. Adding a fact must never lower any part of a route."""

    def setUp(self) -> None:
        self.route = load_route()
        self.loaded = loaded(self.route)
        self.pool = (
            fact(self.route, "README.md"),
            fact(self.route, "docs/index.html", surface="site"),
            fact(self.route, ".github/workflows/tests.yml",
                 surface="ci", effect="verification-authority"),
            fact(self.route, "mystery.bin", confidence="unknown"),
            fact(self.route, "notes.md", surface="docs"),
            fact(self.route, "secrets/key.pem", surface="product", effect="behavior"),
            fact(self.route, "tool.sh", surface="product", effect="behavior",
                 mode_changed=True),
        )

    def test_adding_any_fact_never_lowers_any_field(self) -> None:
        import itertools
        checked = 0
        for size in range(0, len(self.pool)):
            for subset in itertools.combinations(self.pool, size):
                smaller = self.route.build_route(subset, self.loaded)
                for extra in self.pool:
                    if extra in subset:
                        continue
                    larger = self.route.build_route(subset + (extra,), self.loaded)
                    assert_route_not_lower(
                        self, smaller, larger,
                        f"{[f.path for f in subset]} + {extra.path}")
                    checked += 1
        self.assertGreater(checked, 50, "the property was barely exercised")

    def test_every_permutation_gives_the_same_route(self) -> None:
        import itertools
        # Route holds a mapping, so it is not hashable. Compare pairwise
        # against the first ordering rather than collecting into a set.
        for size in (2, 3):
            for subset in itertools.combinations(self.pool, size):
                orders = list(itertools.permutations(subset))
                expected = self.route.build_route(orders[0], self.loaded)
                for order in orders[1:]:
                    self.assertEqual(
                        self.route.build_route(order, self.loaded), expected,
                        f"order changed the route: {[f.path for f in order]}")


class PolicyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()

    def _policy(self, **over):
        policy = json.loads(json.dumps(POLICY))
        policy.update(over)
        return policy

    def _rule(self, **over):
        rule = {"id": "extra", "review_status": "approved",
                "match": {"surfaces": ["docs"]},
                "requires": {"passes": ["06"], "minimum_level": 0},
                "obligations": {"V09": ["validate-core"]}}
        rule.update(over)
        return rule

    def _with_rule(self, **over):
        policy = self._policy()
        policy["rules"] = [self._rule(**over)]
        return policy

    def test_a_valid_policy_loads(self) -> None:
        validated = self.route.load_policy(self._policy(), GATES)
        self.assertEqual(validated.schema_version, 1)

    def test_a_wrong_schema_version_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._policy(schema_version=2), GATES)

    def test_a_missing_full_recipe_is_rejected(self) -> None:
        policy = self._policy()
        del policy["full_recipe"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_a_full_recipe_naming_an_unknown_gate_is_rejected(self) -> None:
        policy = self._policy()
        policy["full_recipe"]["obligations"]["V09"] = ["no-such-gate"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_an_obligation_naming_an_unknown_gate_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["no-such-gate"]}), GATES)

    def test_an_obligation_naming_an_unapproved_gate_is_rejected(self) -> None:
        # A gate nobody reviewed cannot satisfy a capability.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["not-yet-reviewed"]}), GATES)

    def test_an_obligation_naming_a_disabled_gate_is_rejected(self) -> None:
        # A disabled gate will never run, so it covers nothing.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["switched-off"]}), GATES)

    def test_an_empty_obligation_gate_list_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(obligations={"V09": []}), GATES)

    def test_an_unknown_capability_id_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V99": ["validate-core"]}), GATES)

    def test_duplicate_rule_ids_are_rejected(self) -> None:
        policy = self._policy()
        policy["rules"] = [self._rule(), self._rule()]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_duplicate_gate_ids_are_rejected(self) -> None:
        gates = json.loads(json.dumps(GATES))
        gates["gates"].append({"id": "validate-core", "enabled": True,
                               "review_status": "approved"})
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._policy(), gates)

    def test_a_negative_predicate_is_rejected(self) -> None:
        # R-015. A rule that fires on the absence of another fact is not
        # monotonic: adding a file could stop it firing.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(match={"surfaces": ["docs"], "not_paths": ["x"]}), GATES)

    def test_an_empty_match_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(match={}), GATES)

    def test_an_out_of_range_level_is_rejected(self) -> None:
        for level in (-1, 4, "2", None):
            with self.assertRaises(self.route.PolicyError, msg=f"level={level!r}"):
                self.route.load_policy(
                    self._with_rule(requires={"minimum_level": level}), GATES)

    def test_a_non_boolean_flag_is_rejected(self) -> None:
        for flag in ("force_full", "independent_review"):
            with self.assertRaises(self.route.PolicyError, msg=flag):
                self.route.load_policy(
                    self._with_rule(requires={"minimum_level": 1, flag: "yes"}), GATES)

    def test_an_unknown_pass_id_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(requires={"passes": ["99"], "minimum_level": 0}), GATES)

    def test_a_classifier_enum_typo_is_rejected_at_load(self) -> None:
        # Catching this at load rather than only at classification means a bad
        # policy fails before it can route anything.
        policy = self._policy()
        policy["classifier"] = {"surfaces": [
            {"glob": "*.py", "surface": "BOGUS", "effect": "behavior"}]}
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_a_classifier_entry_without_a_glob_is_rejected_at_load(self) -> None:
        policy = self._policy()
        policy["classifier"] = {"surfaces": [{"surface": "docs", "effect": "prose"}]}
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_a_string_path_pattern_is_rejected(self) -> None:
        # K-02, a routing bypass. Iterating a string yields characters, so the
        # "*" in "*.md" matched every path and handed unrelated files the cheap
        # rule. Every plural predicate must be a list.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(match={"paths": "*.md"}), GATES)

    def test_every_plural_predicate_must_be_a_nonempty_list_of_strings(self) -> None:
        for key, bad in (
            ("paths", "*.md"), ("paths", []), ("paths", [""]), ("paths", [1]),
            ("surfaces", "docs"), ("surfaces", []), ("surfaces", [None]),
            ("effects", "prose"), ("change_kinds", "modify"), ("sources", "committed"),
        ):
            with self.assertRaises(self.route.PolicyError, msg=f"{key}={bad!r}"):
                self.route.load_policy(self._with_rule(match={key: bad}), GATES)

    def test_predicate_members_must_be_closed_enum_values(self) -> None:
        for key, bad in (
            ("surfaces", ["BOGUS"]), ("effects", ["BOGUS"]), ("breadths", ["BOGUS"]),
            ("sensitivities", ["BOGUS"]), ("change_kinds", ["BOGUS"]),
            ("sources", ["BOGUS"]),
        ):
            with self.assertRaises(self.route.PolicyError, msg=f"{key}={bad!r}"):
                self.route.load_policy(self._with_rule(match={key: bad}), GATES)

    def test_mode_changed_must_be_an_actual_boolean(self) -> None:
        # bool("false") is True, so a string here inverted the predicate.
        for bad in ("false", "true", 0, 1, None):
            with self.assertRaises(self.route.PolicyError, msg=f"mode_changed={bad!r}"):
                self.route.load_policy(
                    self._with_rule(match={"mode_changed": bad}), GATES)
        self.route.load_policy(self._with_rule(match={"mode_changed": True}), GATES)

    def test_a_full_recipe_below_level_three_is_rejected(self) -> None:
        # K-04. force_full at Level 0 contradicts D-020.
        for level in (0, 1, 2):
            policy = self._policy()
            policy["full_recipe"]["minimum_level"] = level
            with self.assertRaises(self.route.PolicyError, msg=f"level={level}"):
                self.route.load_policy(policy, GATES)

    def test_a_full_recipe_without_passes_is_rejected(self) -> None:
        policy = self._policy()
        policy["full_recipe"]["passes"] = []
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES)

    def test_the_loaded_policy_is_immune_to_later_mutation(self) -> None:
        # K-03, a routing bypass. load_policy returned a shallow copy, so a
        # caller could flip a nested rule from proposed to approved after
        # validation and turn a forced-full route into a cheap one.
        raw = self._policy()
        raw["rules"] = [self._rule(review_status="proposed")]
        loaded = self.route.load_policy(raw, GATES)
        before = self.route.build_route((fact(self.route, "README.md"),), loaded)

        raw["rules"][0]["review_status"] = "approved"
        raw["rules"][0]["requires"]["minimum_level"] = 0
        raw["full_recipe"]["minimum_level"] = 0
        raw["classifier"]["surfaces"].append(
            {"glob": "*", "surface": "docs", "effect": "prose"})

        after = self.route.build_route((fact(self.route, "README.md"),), loaded)
        self.assertEqual(after, before, "mutating the source policy changed routing")
        self.assertTrue(after.force_full)

    def test_build_route_refuses_an_unvalidated_policy(self) -> None:
        # A plain mapping has never been checked. Accepting one lets a caller
        # skip load_policy entirely.
        with self.assertRaises(TypeError):
            self.route.build_route((fact(self.route, "README.md"),), self._policy())

    def test_a_proposed_rule_loads_but_never_matches(self) -> None:
        # D-022. The shipped template carries proposed rules, so loading must
        # accept them. build_route ignores them, which leaves the change
        # unrouted and therefore full.
        policy = self._policy()
        policy["rules"] = [self._rule(review_status="proposed")]
        validated = self.route.load_policy(policy, GATES)
        built = self.route.build_route((fact(self.route, "README.md"),), validated)
        self.assertEqual(built.matched_rule_ids, frozenset())
        self.assertTrue(built.force_full)


if __name__ == "__main__":
    unittest.main()

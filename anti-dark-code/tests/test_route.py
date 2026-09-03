from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest import mock

# macOS puts temporary directories under /var, a symlink to /private/var. The
# managed-path guards refuse to write through a link-like component by design,
# so resolve the temp root once and let the guards police the real path.
tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
CAPABILITIES = SKILL_ROOT / "assets" / "verification-capabilities.json"


def decision_reference_sources(repo_root: Path, skill_root: Path) -> list[Path]:
    """Return every source class that D-090 claims to inspect."""
    sources = [
        *((skill_root / "scripts").rglob("*.py")),
        *((skill_root / "tests").rglob("*.py")),
        *((repo_root / "design" / "routing").rglob("*.md")),
    ]
    return sorted(path for path in sources if path.is_file())


def unresolved_decision_references(repo_root: Path, skill_root: Path) -> list[str]:
    """Return claimed-scope D-ids absent from the routing decision log."""
    decision_log = repo_root / "design" / "routing" / "DECISION-LOG.md"
    recorded = set(re.findall(
        r"^## (D-\d{3})", decision_log.read_text(encoding="utf-8"), re.M
    ))
    unresolved: list[str] = []
    for path in decision_reference_sources(repo_root, skill_root):
        if path == decision_log:
            continue
        text = path.read_text(encoding="utf-8")
        for cited in sorted(set(re.findall(r"\bD-\d{3}\b", text))):
            if cited not in recorded:
                unresolved.append(
                    f"{path.relative_to(repo_root).as_posix()} cites {cited}"
                )
    return sorted(unresolved)


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


def terminate_daemon_process_tree(process) -> None:
    """Stop a Git-for-Windows daemon wrapper and its listener child together."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, text=True, timeout=10, check=False)
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


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
        # Unmerged entries live in the index and the worktree, never in a
        # commit, so this fixture reads them from the source that can hold one.
        result = self.route.parse_raw_z(raw(
            f":100644 120000 {OBJ_A} {OBJ_B} T{NUL}link.txt{NUL}",
            f":100644 100644 {OBJ_A} {OBJ_B} U{NUL}conflict.py{NUL}",
        ), "unstaged")
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

    def test_an_impossible_file_mode_is_rejected(self) -> None:
        # K-05. Any six octal digits passed. Git writes a closed set of modes.
        for mode in ("777777", "123456", "100600"):
            result = self.route.parse_raw_z(
                raw(f":{mode} 100644 {OBJ_A} {OBJ_B} M{NUL}f.py{NUL}"), "committed")
            self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems,
                          f"mode {mode} was accepted")

    def test_every_real_git_mode_parses_into_a_record(self) -> None:
        # Accepted means parsed, not waved through. Every real mode has to
        # produce its record; whether the snapshot stays complete is a separate
        # question, and 160000 is the mode where the two answers differ.
        for mode in ("100644", "100755", "120000", "160000"):
            result = self.route.parse_raw_z(
                raw(f":{mode} {mode} {OBJ_A} {OBJ_B} M{NUL}f.py{NUL}"), "committed")
            self.assertEqual(len(result.inputs), 1, f"mode {mode} produced no record")
            self.assertNotIn("ADC-ROUTE-MALFORMED-RECORD", result.problems,
                             f"mode {mode} was refused as malformed")

    def test_only_the_gitlink_mode_withdraws_snapshot_completeness(self) -> None:
        # D-072. A gitlink names a commit in another repository, which nothing
        # in this snapshot represents, so the record parses and the snapshot
        # stops calling itself complete.
        for mode in ("100644", "100755", "120000"):
            result = self.route.parse_raw_z(
                raw(f":{mode} {mode} {OBJ_A} {OBJ_B} M{NUL}f.py{NUL}"), "committed")
            self.assertEqual(result.problems, (), f"mode {mode} raised a problem")
        gitlink = self.route.parse_raw_z(
            raw(f":160000 160000 {OBJ_A} {OBJ_B} M{NUL}vendor{NUL}"), "committed")
        self.assertEqual(gitlink.problems, ("ADC-ROUTE-SUBMODULE-UNSUPPORTED",))
        self.assertEqual(gitlink.inputs[0].path, "vendor")

    def test_a_submodule_added_or_deleted_is_also_unsupported(self) -> None:
        # The null mode on one side is creation or deletion. Reading only the
        # new mode would miss a submodule being removed, which changes the tree
        # the same way.
        added = self.route.parse_raw_z(
            raw(f":000000 160000 {'0' * 40} {OBJ_B} A{NUL}vendor{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-SUBMODULE-UNSUPPORTED", added.problems)
        deleted = self.route.parse_raw_z(
            raw(f":160000 000000 {OBJ_A} {'0' * 40} D{NUL}vendor{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-SUBMODULE-UNSUPPORTED", deleted.problems)

    def test_a_score_on_a_status_that_cannot_carry_one_is_rejected(self) -> None:
        # Git writes a similarity score only for C and R.
        for status in ("A100", "M50", "D10", "T5"):
            result = self.route.parse_raw_z(
                raw(f":100644 100644 {OBJ_A} {OBJ_B} {status}{NUL}f.py{NUL}"), "committed")
            self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems,
                          f"status {status} was accepted")

    def test_an_out_of_range_similarity_score_is_rejected(self) -> None:
        for status in ("R999", "C101", "R200"):
            result = self.route.parse_raw_z(raw(
                f":100644 100644 {OBJ_A} {OBJ_B} {status}{NUL}a.py{NUL}b.py{NUL}"),
                "committed")
            self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems,
                          f"status {status} was accepted")

    def test_a_valid_similarity_score_is_accepted(self) -> None:
        for status in ("R100", "C100", "R0", "R95"):
            result = self.route.parse_raw_z(raw(
                f":100644 100644 {OBJ_A} {OBJ_B} {status}{NUL}a.py{NUL}b.py{NUL}"),
                "committed")
            self.assertEqual(result.problems, (), f"status {status} was refused")

    def test_mixed_object_widths_in_one_record_are_rejected(self) -> None:
        # A repository has one hash width. Two in one record is corruption.
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {'b' * 64} M{NUL}f.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_null_mode_must_pair_with_a_null_object(self) -> None:
        # A side that does not exist has both null. The converse is legitimate:
        # a worktree comparison writes a null object with a real mode because
        # git has not hashed the file, so that shape must stay accepted.
        result = self.route.parse_raw_z(
            raw(f":000000 100644 {OBJ_A} {OBJ_B} A{NUL}f.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_worktree_side_null_object_with_a_real_mode_is_accepted(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {ZERO} M{NUL}f.py{NUL}"), "unstaged")
        self.assertEqual(result.problems, ())
        self.assertEqual(result.inputs[0].change_kind, "modify")

    def test_a_copy_or_rename_without_a_score_is_rejected(self) -> None:
        # L-06. Git writes a similarity score on C and R. A score-free one
        # passed because "no score present" returned true for every status.
        for status in ("R", "C"):
            result = self.route.parse_raw_z(raw(
                f":100644 100644 {OBJ_A} {OBJ_B} {status}{NUL}a.py{NUL}b.py{NUL}"),
                "committed")
            self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems,
                          f"score-free {status} was accepted")

    def test_a_real_conflict_record_is_accepted(self) -> None:
        # N-04, a regression I introduced. Git writes an unmerged entry with a
        # null old side, captured from a real merge conflict:
        #   :000000 100644 <zeros> <obj> U f.txt
        # The status-sides table required both sides real for U, so every
        # conflict in a repository mid-merge reported as malformed. My
        # synthetic fixture had two real sides and could not see the real shape.
        result = self.route.parse_raw_z(
            raw(f":000000 100644 {ZERO} {OBJ_A} U{NUL}conflict.py{NUL}"), "unstaged")
        self.assertEqual(result.problems, ())
        self.assertEqual(result.inputs[0].change_kind, "unmerged")

    def test_an_unmerged_record_is_accepted_with_either_side_shape(self) -> None:
        # Unmerged entries have their own semantics and more than one shape.
        # None of them should be refused, because refusing one loses the path
        # exactly when the tree is in its most delicate state.
        for old_mode, old_obj, new_mode, new_obj in (
            ("000000", ZERO, "100644", OBJ_A),
            ("100644", OBJ_A, "000000", ZERO),
            ("100644", OBJ_A, "100644", OBJ_B),
            # Both sides null is excluded: it is refused by P-04, because an
            # unmerged entry with nothing on either side is not a state git
            # records.
        ):
            result = self.route.parse_raw_z(
                raw(f":{old_mode} {new_mode} {old_obj} {new_obj} U{NUL}c.py{NUL}"),
                "unstaged")
            self.assertEqual(result.problems, (),
                             f"unmerged {old_mode}/{new_mode} was refused")

    def test_a_plain_raw_conflict_record_is_accepted(self) -> None:
        # Q-02. Captured from git 2.50.1 during a real merge conflict, using
        # plain `git diff --raw -z --no-abbrev`:
        #   :000000 100644 <40 zeros> <40 zeros> U f.txt
        # Both object ids are null and the new mode is real. Deciding whether a
        # side exists from the object ids called that malformed, which is real
        # git output. The production flags change the output and hid this form.
        result = self.route.parse_raw_z(
            raw(f":000000 100644 {ZERO} {ZERO} U{NUL}f.txt{NUL}"), "unstaged")
        self.assertEqual(result.problems, ())
        self.assertEqual(result.inputs[0].change_kind, "unmerged")

    def test_an_unmerged_record_with_both_modes_null_is_rejected(self) -> None:
        # Modes, not object ids, say whether a side exists. Neither side
        # existing is not a state git records.
        result = self.route.parse_raw_z(
            raw(f":000000 000000 {ZERO} {ZERO} U{NUL}f.txt{NUL}"), "unstaged")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_scored_unmerged_record_is_rejected(self) -> None:
        # P-04. Exempting U from the side check exempted it from everything.
        # Git never scores an unmerged entry.
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} U100{NUL}c.py{NUL}"), "unstaged")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_committed_unmerged_record_is_rejected(self) -> None:
        # A commit cannot contain an unmerged entry. Only the index and the
        # worktree can be in that state.
        result = self.route.parse_raw_z(
            raw(f":000000 100644 {ZERO} {OBJ_A} U{NUL}c.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_an_add_with_two_existing_sides_is_rejected(self) -> None:
        # An add has no old side. Two real sides is not a record git writes.
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} A{NUL}f.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_delete_with_two_existing_sides_is_rejected(self) -> None:
        result = self.route.parse_raw_z(
            raw(f":100644 100644 {OBJ_A} {OBJ_B} D{NUL}f.py{NUL}"), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_real_add_and_delete_are_still_accepted(self) -> None:
        result = self.route.parse_raw_z(raw(
            f":000000 100644 {ZERO} {OBJ_A} A{NUL}new.py{NUL}",
            f":100644 000000 {OBJ_A} {ZERO} D{NUL}gone.py{NUL}",
        ), "committed")
        self.assertEqual(result.problems, ())

    def test_one_payload_cannot_mix_object_widths_across_records(self) -> None:
        # A repository has one hash width, so every record in one payload must
        # agree. Checking only within each record let a payload carry both.
        long_a, long_b = "a" * 64, "b" * 64
        result = self.route.parse_raw_z(raw(
            f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}sha1.py{NUL}",
            f":100644 100644 {long_a} {long_b} M{NUL}sha256.py{NUL}",
        ), "committed")
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", result.problems)

    def test_a_consistent_sha256_payload_is_accepted(self) -> None:
        long_a, long_b = "a" * 64, "b" * 64
        result = self.route.parse_raw_z(raw(
            f":100644 100644 {long_a} {long_b} M{NUL}one.py{NUL}",
            f":100644 100644 {long_b} {long_a} M{NUL}two.py{NUL}",
        ), "committed")
        self.assertEqual(result.problems, ())

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

    def test_object_width_is_consistent_across_the_whole_snapshot(self) -> None:
        # P-05. Width was established per parser call, so one snapshot could
        # carry a 40-digit staged record beside a 64-digit committed one. A
        # repository has one object format.
        long_a, long_b = "a" * 64, "b" * 64
        run = RecordingRunner({
            "merge-base": BASE.encode("ascii") + b"\n",
            BASE: raw(f":100644 100644 {long_a} {long_b} M{NUL}wide.py{NUL}"),
            "--cached": raw(f":100644 100644 {OBJ_A} {OBJ_B} M{NUL}narrow.py{NUL}"),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", snap.problems)
        self.assertFalse(snap.complete)

    def test_one_source_cannot_disagree_with_the_merge_base_width(self) -> None:
        # Q-03. The existing width test compares two changed sources against
        # each other, so removing the merge-base seed changed nothing it could
        # see. A repository has one object format, and the resolved base is the
        # first thing that states it.
        long_a, long_b = "a" * 64, "b" * 64
        run = RecordingRunner({
            "merge-base": BASE.encode("ascii") + b"\n",
            BASE: raw(f":100644 100644 {long_a} {long_b} M{NUL}wide.py{NUL}"),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        self.assertIn("ADC-ROUTE-MALFORMED-RECORD", snap.problems,
                      "a 64-character row was accepted beside a 40-character base")
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

    def test_a_repository_mid_merge_still_acquires(self) -> None:
        """N-04 end to end. A conflicted tree is the delicate case.

        Reported as malformed, every conflict would lose its path and the
        snapshot would refuse to be complete for a reason that is not true.
        """
        self._git("checkout", "-qb", "other")
        (self.repo / "src.py").write_text("a\nb\nc\nd\nOTHER\n", encoding="utf-8")
        self._git("commit", "-qam", "other side")
        self._git("checkout", "-q", "base-ref")
        self._git("checkout", "-qb", "mine")
        (self.repo / "src.py").write_text("a\nb\nc\nd\nMINE\n", encoding="utf-8")
        self._git("commit", "-qam", "my side")
        subprocess.run(["git", "-C", str(self.repo), "merge", "other"],
                       capture_output=True)

        snap = self.route.read_change_inputs(self.repo, "base-ref")
        self.assertNotIn("ADC-ROUTE-MALFORMED-RECORD", snap.problems,
                         "a real merge conflict was read as a malformed record")
        self.assertIn("src.py", {i.path for i in snap.inputs})

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

    def _install_filter(self, name: str = "evil") -> Path:
        """Point a content filter at a script that writes a sentinel."""
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        sentinel = self.repo / f"{name}-sentinel.txt"
        probe = hooks / f"{name}-probe"
        probe.write_text(
            "#!/bin/sh\n"
            f'echo executed >> "{sentinel.as_posix()}"\n'
            "cat\n",
            encoding="utf-8", newline="\n",
        )
        probe.chmod(0o755)
        (self.repo / ".gitattributes").write_text(
            f"*.txt filter={name}\n", encoding="utf-8", newline="\n")
        self._git("add", ".gitattributes")
        self._git("commit", "-qm", "attributes")
        self._git("config", f"filter.{name}.clean", f".git/hooks/{name}-probe")
        self._git("config", f"filter.{name}.required", "true")
        return sentinel

    def test_a_content_filter_cannot_run_during_acquisition(self) -> None:
        """K-01. Git applies clean conversion when comparing worktree content.

        Disabling core.fsmonitor and diff.external closed the two paths that
        were named at the time. Content filters are a third, which is why the
        boundary cannot rest on a list of keys somebody remembered.
        """
        sentinel = self._install_filter()
        (self.repo / "data.txt").write_text("changed\n", encoding="utf-8")
        self._git("add", "data.txt")
        self._git("commit", "-qm", "add data")
        (self.repo / "data.txt").write_text("changed again\n", encoding="utf-8")
        # Staging above legitimately ran the filter, so the setup trips the
        # sentinel by itself. Only acquisition is under test.
        sentinel.unlink(missing_ok=True)

        snap = self.route.read_change_inputs(self.repo, "base-ref")

        self.assertFalse(
            sentinel.exists(),
            "a repository-configured content filter ran during acquisition")
        self.assertTrue(snap.inputs, "acquisition must still work while isolated")

    def _install_global_filter(self, name: str = "global-style") -> tuple[Path, Path]:
        """Declare the filter in an isolated global config, not the repository's.

        N-08. The previous version of this test called `_install_filter`, which
        runs `git config` without `--global` and therefore writes the local
        repository config. The "global" test was mechanically identical to the
        local one and proved nothing about global configuration, while R-054
        cited it for exactly that claim.
        """
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        sentinel = self.repo / f"{name}-sentinel.txt"
        probe = hooks / f"{name}-probe"
        probe.write_text(
            "#!/bin/sh\n"
            f'echo executed >> "{sentinel.as_posix()}"\n'
            "cat\n",
            encoding="utf-8", newline="\n",
        )
        probe.chmod(0o755)
        (self.repo / ".gitattributes").write_text(
            f"*.txt filter={name}\n", encoding="utf-8", newline="\n")
        self._git("add", ".gitattributes")
        self._git("commit", "-qm", "attributes")
        config = Path(self.tmp.name) / f"{name}-gitconfig"
        config.write_text(
            f'[filter "{name}"]\n'
            f"\tclean = .git/hooks/{name}-probe\n"
            "\trequired = true\n",
            encoding="utf-8", newline="\n")
        return sentinel, config

    def test_a_globally_configured_filter_is_also_neutralized(self) -> None:
        # git-lfs installs filter.lfs.* globally. A driver the repository did
        # not define locally must be neutralized too.
        sentinel, config = self._install_global_filter()
        (self.repo / "payload.txt").write_text("one\n", encoding="utf-8")
        self._git("add", "payload.txt")
        self._git("commit", "-qm", "payload")
        (self.repo / "payload.txt").write_text("two\n", encoding="utf-8")
        sentinel.unlink(missing_ok=True)

        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(config)}):
            # Prove the fixture before trusting the result. Without this the
            # test passes when the global config is not in effect at all, which
            # is exactly how N-08 survived eight rounds.
            listed = subprocess.run(
                ["git", "-C", str(self.repo), "config", "--get-regexp",
                 r"^filter\."],
                capture_output=True, text=True, timeout=60).stdout
            self.assertIn("filter.global-style.clean", listed,
                          "the global config is not in effect, so this test "
                          "would prove nothing")
            local = subprocess.run(
                ["git", "-C", str(self.repo), "config", "--local",
                 "--get-regexp", r"^filter\."],
                capture_output=True, text=True, timeout=60).stdout
            self.assertNotIn("global-style", local,
                             "the driver must come from global config only")

            self.route.read_change_inputs(self.repo, "base-ref")

        self.assertFalse(
            sentinel.exists(),
            "a globally configured content filter ran during acquisition")

    def test_a_filter_name_containing_an_equals_cannot_run(self) -> None:
        """D-085. `-c key=value` splits on the FIRST `=`.

        A driver named `a=b` made the override land on `filter.a`, leaving
        `filter."a=b".clean` live. Measured before the fix: the program ran
        during acquisition and the snapshot still reported complete with no
        problems, so repository code executed and a selective route was still
        authorised.
        """
        sentinel = self._install_filter("a=b")
        (self.repo / "payload.txt").write_text("one\n", encoding="utf-8")
        self._git("add", "payload.txt")
        self._git("commit", "-qm", "payload")
        (self.repo / "payload.txt").write_text("two\n", encoding="utf-8")
        # Staging above legitimately ran the driver. Only acquisition is under
        # test.
        sentinel.unlink(missing_ok=True)

        # Prove the fixture: git really does resolve this driver name.
        resolved = subprocess.run(
            ["git", "-C", str(self.repo), "check-attr", "filter", "payload.txt"],
            capture_output=True, text=True, timeout=60).stdout
        self.assertIn("filter: a=b", resolved,
                      "the fixture did not configure the driver under test")

        snap = self.route.read_change_inputs(self.repo, "base-ref")

        self.assertFalse(
            sentinel.exists(),
            "a filter whose name contains '=' ran during acquisition")
        # D-088: the environment form expresses this name, so the comparison
        # runs and the record is kept. Nothing is refused and nothing is lost.
        self.assertNotIn("ADC-ROUTE-FILTER-UNNEUTRALIZED", snap.problems)
        self.assertTrue(snap.complete, f"problems: {snap.problems}")
        self.assertIn("unstaged", {row.source for row in snap.inputs})

    def test_an_injected_runner_refuses_rather_than_guessing(self) -> None:
        # D-088. The environment neutralization needs a runner this module
        # built. A caller that injected one gets the D-085 refusal instead,
        # because adding an environment to someone else's runner is not
        # possible and assuming it worked is the thing D-085 removed.
        sentinel = self._install_filter("x=y")
        (self.repo / "payload.txt").write_text("one\n", encoding="utf-8")
        self._git("add", "payload.txt")
        self._git("commit", "-qm", "payload")
        (self.repo / "payload.txt").write_text("two\n", encoding="utf-8")
        sentinel.unlink(missing_ok=True)

        injected = self.route._default_runner(self.repo)
        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=injected)

        self.assertFalse(sentinel.exists(),
                         "the fallback let the driver run")
        self.assertIn("ADC-ROUTE-FILTER-UNNEUTRALIZED", snap.problems)
        self.assertFalse(snap.complete)

    def test_the_environment_form_expresses_a_name_dash_c_cannot(self) -> None:
        # The unit the fallback rests on, stated separately so a failure says
        # which half broke.
        env = self.route._filter_config_env(["a=b"])
        self.assertEqual("4", env["GIT_CONFIG_COUNT"])
        self.assertEqual("filter.a=b.clean", env["GIT_CONFIG_KEY_0"])
        self.assertEqual("", env["GIT_CONFIG_VALUE_0"])
        self.assertEqual({}, self.route._filter_config_env([]))

    def test_an_ordinary_filter_still_allows_a_complete_snapshot(self) -> None:
        # The counterexample. git-lfs installs filter.lfs.*, and a check that
        # refused every repository with a filter would be useless.
        sentinel = self._install_filter("ordinary")
        (self.repo / "payload.txt").write_text("one\n", encoding="utf-8")
        self._git("add", "payload.txt")
        self._git("commit", "-qm", "payload")
        (self.repo / "payload.txt").write_text("two\n", encoding="utf-8")
        sentinel.unlink(missing_ok=True)

        snap = self.route.read_change_inputs(self.repo, "base-ref")

        self.assertFalse(sentinel.exists())
        self.assertNotIn("ADC-ROUTE-FILTER-UNNEUTRALIZED", snap.problems)
        self.assertTrue(snap.complete, f"problems: {snap.problems}")

    def test_a_boundary_violation_is_detected_and_reported(self) -> None:
        """The list of neutralized keys cannot be proven complete.

        So acquisition fingerprints the repository before and after and refuses
        to call the snapshot complete if anything moved. That converts an
        unknown configuration path from a silent escape into a recorded one.
        """
        intruder = self.repo / "written-during-acquisition.txt"

        def meddling_runner(args):
            intruder.write_text("a boundary escape\n", encoding="utf-8")
            return self.route._default_runner(self.repo)(args)

        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=meddling_runner)
        self.assertIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)
        self.assertFalse(snap.complete)

    def test_a_change_to_the_index_alone_is_detected(self) -> None:
        # M33. The fingerprint recorded index state but nothing asserted it, so
        # returning None for it survived every test. Staging a file changes the
        # index without changing any worktree byte.
        (self.repo / "staged-later.txt").write_text("x\n", encoding="utf-8")
        self._git("add", "staged-later.txt")
        self._git("commit", "-qm", "add file")

        target = self.repo / "staged-later.txt"
        original_bytes = target.read_bytes()
        original_stat = target.stat()
        seen: list[int] = []

        def staging_runner(args):
            result = self.route._default_runner(self.repo)(args)
            seen.append(1)
            if len(seen) == 5:
                # Stage a change, then put the worktree file back exactly.
                # Only the index moves, so a fingerprint that ignores index
                # state sees nothing at all.
                target.write_bytes(b"y\n")
                subprocess.run(["git", "-C", str(self.repo), "add", "staged-later.txt"],
                               capture_output=True)
                target.write_bytes(original_bytes)
                os.utime(target, ns=(original_stat.st_atime_ns,
                                     original_stat.st_mtime_ns))
            return result

        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=staging_runner)
        self.assertIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)

    def test_replacing_a_file_with_a_hard_link_is_detected(self) -> None:
        """M36. A hard link swap that holds bytes, size, and mtime equal.

        The earlier version of this test passed for the wrong reason. A hard
        link shares an inode, so setting the target's timestamp also moved the
        twin's, and the detector fired on the twin rather than on topology.
        Aligning both timestamps before the swap removes that side channel, so
        the only thing left that differs is the path topology: link count and
        inode.

        It removed one side channel and not all of them. On Linux git refreshes
        the index during acquisition, the boundary fires on that, and this test
        passes with topology disabled. It holds the guarantee on Windows only,
        which is exactly the kind of platform-shaped hole a single-host matrix
        cannot see. test_path_topology_alone_moves_the_fingerprint takes two
        fingerprints with no acquisition between them and holds it everywhere.
        This one is kept for the end-to-end path it covers.
        """
        target = self.repo / "linked.txt"
        target.write_bytes(b"SAME\n")
        self._git("add", "linked.txt")
        self._git("commit", "-qm", "linked")

        twin = self.repo / "twin-source.txt"
        twin.write_bytes(b"SAME\n")
        original = target.stat()
        # One inode after linking, so one timestamp. Align the twin to the
        # target now and the shared timestamp matches both originals after.
        os.utime(twin, ns=(original.st_atime_ns, original.st_mtime_ns))

        seen: list[int] = []

        def linking_runner(args):
            result = self.route._default_runner(self.repo)(args)
            seen.append(1)
            if len(seen) == 5:
                target.unlink()
                try:
                    os.link(twin, target)
                except (OSError, NotImplementedError) as exc:
                    self.skipTest(f"hard links unavailable on this host: {exc}")
                os.utime(target, ns=(original.st_atime_ns, original.st_mtime_ns))
            return result

        # The indexed path has a new inode after the swap.  Git may otherwise
        # refresh the index while acquisition runs, which is itself a boundary
        # change and can make this test pass even when the topology term is
        # absent.  Restrict its stat comparison to the unchanged bytes/size/
        # mtime and prove the index bytes did not become a side channel.
        self._git("config", "core.trustctime", "false")
        self._git("config", "core.checkStat", "minimal")
        index_before = (self.repo / ".git" / "index").read_bytes()
        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=linking_runner)
        self.assertEqual(
            index_before, (self.repo / ".git" / "index").read_bytes(),
            "the Git index changed during acquisition and reintroduced a "
            "side channel for the topology assertion")

        # Nothing a content-and-metadata fingerprint can see has moved.
        self.assertEqual(target.read_bytes(), b"SAME\n")
        self.assertEqual(target.stat().st_size, original.st_size)
        self.assertEqual(target.stat().st_mtime_ns, original.st_mtime_ns)
        self.assertEqual(twin.stat().st_mtime_ns, original.st_mtime_ns)
        self.assertIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)

    def test_path_topology_alone_moves_the_fingerprint(self) -> None:
        """M36, isolated from everything that can stand in for it.

        The end-to-end test above asserts a boundary violation is reported
        after a hard-link swap. On Linux it passes with topology disabled,
        because git refreshes the index during acquisition and the boundary
        fires on that instead. The guarantee reads as held on one platform and
        not the other, and the difference is the side channel, not the code.

        This takes two fingerprints with nothing in between. No acquisition, so
        no index movement, so the only thing that can differ is the topology of
        the path. Content, size, and mtime are all held equal and asserted so,
        which means a passing run cannot be explained by any of them.
        """
        target = self.repo / "topology.txt"
        target.write_bytes(b"SAME" + bytes([10]))
        self._git("add", "topology.txt")
        self._git("commit", "-qm", "topology")

        twin = self.repo / "topology-twin.txt"
        twin.write_bytes(b"SAME" + bytes([10]))
        original = target.stat()
        # One inode after linking, so one timestamp. Align the twin first and
        # the shared timestamp still matches both originals afterwards.
        os.utime(twin, ns=(original.st_atime_ns, original.st_mtime_ns))

        run = self.route._default_runner(self.repo)
        before = dict((entry[0], entry)
                      for entry in self.route._repo_fingerprint(self.repo, run)[1])

        target.unlink()
        try:
            os.link(twin, target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"hard links unavailable on this host: {exc}")
        os.utime(target, ns=(original.st_atime_ns, original.st_mtime_ns))

        after = dict((entry[0], entry)
                     for entry in self.route._repo_fingerprint(self.repo, run)[1])

        # Everything a content-and-metadata fingerprint can see is unchanged.
        self.assertEqual(b"SAME" + bytes([10]), target.read_bytes())
        self.assertEqual(original.st_size, target.stat().st_size)
        self.assertEqual(original.st_mtime_ns, target.stat().st_mtime_ns)
        self.assertNotEqual(
            before.get("topology.txt"), after.get("topology.txt"),
            "the fingerprint did not move, so path topology is not part of it "
            "and a hard-link swap is invisible to the boundary check")

    def test_a_linked_worktree_index_is_found(self) -> None:
        # P-02. A linked worktree keeps its index under .git/worktrees/<name>,
        # so assuming .git/index fingerprints nothing at all there and the
        # boundary check silently covers less than it claims.
        linked = Path(self.tmp.name) / "linked"
        done = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-q",
             str(linked), "-b", "linked-branch"],
            capture_output=True, text=True)
        if done.returncode != 0:
            self.skipTest(f"git worktree add unavailable: {done.stderr.strip()}")
        run = self.route._default_runner(linked)
        index_state = self.route._repo_fingerprint(linked, run)[0]
        self.assertIsNotNone(
            index_state,
            "no index was fingerprinted for a linked worktree, so the "
            "boundary check covered nothing there")

    def test_a_same_size_index_rewrite_is_detected(self) -> None:
        # P-02. The index contributed size and mtime only, so an index rewritten
        # to the same length with its timestamp restored was invisible, which is
        # the same blind spot L-02 closed for worktree files.
        index = self.repo / ".git" / "index"
        original = index.read_bytes()
        original_stat = index.stat()
        seen: list[int] = []

        def index_rewriting_runner(args):
            result = self.route._default_runner(self.repo)(args)
            seen.append(1)
            if len(seen) == 5:
                swapped = bytearray(original)
                swapped[-1] = (swapped[-1] + 1) % 256
                index.write_bytes(bytes(swapped))
                os.utime(index, ns=(original_stat.st_atime_ns,
                                    original_stat.st_mtime_ns))
            return result

        try:
            snap = self.route.read_change_inputs(
                self.repo, "base-ref", runner=index_rewriting_runner)
            self.assertEqual(index.stat().st_size, original_stat.st_size)
            self.assertIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)
        finally:
            index.write_bytes(original)

    def test_a_symlink_is_identified_not_followed(self) -> None:
        # P-07. lstat was used for metadata and then open() followed the link
        # for content, so a tracked path swapped for a symlink hashed the
        # target's bytes. The fingerprint must record the link, not read
        # through it.
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_bytes(b"SECRET-OUTSIDE\n")
        link = self.repo / "link.txt"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError, AttributeError) as exc:
            self.skipTest(f"symlinks unavailable on this host: {exc}")
        run = self.route._default_runner(self.repo)
        digest = dict(
            (entry[0], entry[3])
            for entry in self.route._repo_fingerprint(self.repo, run)[1])
        recorded = digest.get("link.txt")
        self.assertIsNotNone(recorded, "the symlink was not fingerprinted")
        self.assertIn("symlink:", recorded,
                      "the symlink was followed instead of identified")
        # Q-04. Asserting only the marker let the target text be dropped: the
        # fingerprint would then see one link as equal to any other, and a
        # retarget to different data would be invisible.
        self.assertIn(str(outside), recorded,
                      "the link target text was not recorded")

        # Retarget to a different file of the same length and prove the
        # fingerprint moves. Same length, so size cannot be doing the work.
        other = Path(self.tmp.name) / "other-outside.txt"
        other.write_bytes(b"SECRET-OUTSIDE\n")
        link.unlink()
        os.symlink(other, link)
        after = dict(
            (entry[0], entry[3])
            for entry in self.route._repo_fingerprint(self.repo, run)[1])
        self.assertNotEqual(after.get("link.txt"), recorded,
                            "retargeting the link did not change the fingerprint")

    def test_a_clean_acquisition_reports_no_boundary_violation(self) -> None:
        (self.repo / "src.py").write_text("a\nb\nc\nd\nCHANGED\n", encoding="utf-8")
        snap = self.route.read_change_inputs(self.repo, "base-ref")
        self.assertNotIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)
        self.assertTrue(snap.complete)

    def test_the_runner_environment_blocks_lazy_fetch(self) -> None:
        """L-01. fetch.negotiationAlgorithm=noop chooses a negotiation strategy.

        It does not stop a partial clone fetching a missing object on demand,
        which Codex traced: acquisition started a child git fetch and wrote an
        object while reporting complete. GIT_NO_LAZY_FETCH is the real control.

        This asserts the control is present. The behaviour it prevents is
        held separately, against a real blobless clone, by
        PartialCloneAgainstRealGitDaemonTests. That class needs a git daemon
        and skips without one, so this stays as the check that survives on
        every host.
        """
        import subprocess as sp
        captured: dict[str, str] = {}
        original = sp.run

        def capture(*args, **kwargs):
            if kwargs.get("env"):
                captured.update(kwargs["env"])
            return original(*args, **kwargs)

        sp.run = capture
        try:
            self.route.read_change_inputs(self.repo, "base-ref")
        finally:
            sp.run = original
        self.assertEqual(captured.get("GIT_NO_LAZY_FETCH"), "1")

    def test_negotiation_setting_is_not_used_as_an_isolation_control(self) -> None:
        # The name may appear in a comment explaining why it is not used. What
        # must not happen is it sitting in the isolation flags looking like
        # protection, because it changes negotiation and prevents no fetch.
        flags = " ".join(self.route._GIT_ISOLATION)
        self.assertNotIn("fetch.negotiationAlgorithm", flags)

    def test_a_same_size_rewrite_is_detected(self) -> None:
        """L-02. The fingerprint stored size and mtime, so a write that

        preserved both was invisible: content could change after its own
        comparison and the snapshot still called itself complete.
        """
        victim = self.repo / "victim.txt"
        victim.write_text("AAAA\n", encoding="utf-8", newline="\n")
        self._git("add", "victim.txt")
        self._git("commit", "-qm", "victim")
        original = victim.stat()

        seen: list[int] = []

        def rewriting_runner(args):
            result = self.route._default_runner(self.repo)(args)
            seen.append(1)
            # Calls one and two are the opening fingerprint's own listings, and
            # it hashes after both return. Firing here puts the write after the
            # file's comparison and before the closing fingerprint, which is the
            # window the detector exists to cover.
            if len(seen) == 5:
                # Same byte count, and the timestamp put back afterwards.
                victim.write_text("BBBB\n", encoding="utf-8", newline="\n")
                os.utime(victim, ns=(original.st_atime_ns, original.st_mtime_ns))
            return result

        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=rewriting_runner)
        self.assertEqual(victim.stat().st_size, original.st_size)
        self.assertEqual(victim.stat().st_mtime_ns, original.st_mtime_ns)
        self.assertIn("ADC-ROUTE-BOUNDARY-VIOLATED", snap.problems)
        self.assertFalse(snap.complete)

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

    def test_a_literal_backslash_is_a_filename_character_not_a_separator(self) -> None:
        # K-09. Git reports forward slashes on every platform, verified against
        # real output, so rewriting backslashes solved nothing and corrupted a
        # legal POSIX filename: a file actually named "auth\login.py" was
        # matched against "auth/*" and handed that rule's sensitivity.
        facts = self._facts(self.route.ChangeInput(
            path="auth\\login.py", change_kind="modify", source="committed"))
        self.assertEqual([f.confidence for f in facts], ["unknown"])

    def test_classification_is_pure_and_takes_no_repository(self) -> None:
        snapshot = self._snapshot(self.route.ChangeInput(
            path="README.md", change_kind="modify", source="committed"))
        first = self.route.collect_change_facts(snapshot, CLASSIFIER)
        second = self.route.collect_change_facts(snapshot, CLASSIFIER)
        self.assertEqual(first, second)


CAPABILITY_IDS = frozenset(
    c["id"] for c in json.loads(
        CAPABILITIES.read_text(encoding="utf-8"))["capabilities"]
)

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
        # L-08. Forces full without supplying Level 3 or independent review, so
        # the full recipe is the only thing that can contribute them and a
        # no-op recipe merge becomes observable.
        {"id": "bare-full", "review_status": "approved",
         "match": {"surfaces": ["release"]},
         "requires": {"minimum_level": 0, "force_full": True},
         "obligations": {"V09": ["validate-core"]}},
        {"id": "authority", "review_status": "approved",
         "match": {"effects": ["verification-authority"]},
         "requires": {"passes": ["07", "14"], "minimum_level": 3,
                      "force_full": True, "independent_review": True},
         "obligations": {"V12": ["hostile-environment"]}},
    ],
}


FULL_SET = {
    "passes": ["07", "10", "11", "14"],
    "obligations": {
        "V08": ["distribution"],
        "V09": ["validate-core"],
        "V12": ["hostile-environment"],
        "V21": ["full-suite"],
    },
}


def loaded(route):
    """POLICY as build_route now requires it: validated and frozen."""
    return route.load_policy(POLICY, GATES, CAPABILITY_IDS, FULL_SET)


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

    def test_route_obligations_cannot_be_mutated_after_construction(self) -> None:
        # L-07. Route was a frozen dataclass holding a plain dict, so
        # built.obligations.clear() emptied authority data after the route was
        # computed and without another route computation.
        built = self.route.build_route(
            (fact(self.route, "README.md"),), self.loaded)
        self.assertTrue(built.obligations)
        # mappingproxy raises AttributeError for clear and TypeError for
        # assignment. Both are refusals; the point is that neither succeeds.
        with self.assertRaises((TypeError, AttributeError)):
            built.obligations.clear()
        with self.assertRaises((TypeError, AttributeError)):
            built.obligations["V99"] = frozenset({"x"})
        self.assertTrue(built.obligations, "obligations were emptied")

    def test_a_proxy_over_mutable_backing_does_not_survive_construction(self) -> None:
        """Q-01. A MappingProxyType blocks writes through the proxy only.

        It does not freeze the dictionary behind it, so __post_init__ trusting
        an existing proxy left the Route mutable through that dictionary: the
        backing could be cleared, or a forged obligation written into it, after
        the route was computed.
        """
        from types import MappingProxyType
        backing = {"V09": frozenset({"validate-core"})}
        route = self.route.Route(
            minimum_level=0, passes=frozenset(),
            obligations=MappingProxyType(backing),
            matched_rule_ids=frozenset(), force_full=False,
            independent_review=False)

        backing.clear()
        self.assertEqual(dict(route.obligations),
                         {"V09": frozenset({"validate-core"})},
                         "clearing the backing dictionary emptied the route")

        backing["V99"] = frozenset({"forged"})
        self.assertNotIn("V99", route.obligations,
                         "a write to the backing dictionary reached the route")

    def test_obligations_are_immutable_however_a_route_is_made(self) -> None:
        # P-03. Wrapping at the construction sites froze the value those sites
        # produced, not the field. dataclasses.replace with a plain mapping and
        # direct construction both handed back a mutable one.
        import dataclasses
        built = self.route.build_route(
            (fact(self.route, "README.md"),), self.loaded)
        swapped = dataclasses.replace(
            built, obligations={"V09": frozenset({"validate-core"})})
        direct = self.route.Route(
            minimum_level=0, passes=frozenset(),
            obligations={"V09": frozenset({"validate-core"})},
            matched_rule_ids=frozenset(), force_full=False,
            independent_review=False)
        for name, route in (("replace", swapped), ("direct", direct)):
            with self.assertRaises((TypeError, AttributeError), msg=name):
                route.obligations.clear()
            self.assertTrue(route.obligations, name)

    def test_every_route_construction_path_freezes_obligations(self) -> None:
        # M34 and N-05. Only the build path was checked, so the hint path could
        # hand out a mutable mapping, and dataclasses.replace could build a
        # Route holding one. Immutability has to hold for every path that makes
        # a Route, not the one that happened to have a test.
        import dataclasses
        built = self.route.build_route(
            (fact(self.route, "README.md"),), self.loaded)
        hinted = self.route.apply_hints(built, {"minimum_level": 2}, self.loaded)
        replaced = dataclasses.replace(built, minimum_level=3)
        for name, route in (("built", built), ("hinted", hinted),
                            ("replaced", replaced)):
            self.assertTrue(route.obligations, name)
            with self.assertRaises((TypeError, AttributeError), msg=name):
                route.obligations.clear()

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

    def test_a_bare_force_full_rule_still_gets_the_whole_recipe(self) -> None:
        # L-08. The authority fixture already supplies Level 3 and independent
        # review through its own rule, so deleting the recipe merges changed
        # nothing observable. This rule supplies neither.
        built = self.route.build_route(
            (fact(self.route, "VERSION", surface="release", effect="prose"),),
            self.loaded)
        self.assertTrue(built.force_full)
        self.assertEqual(built.minimum_level, 3, "recipe level was not merged")
        self.assertTrue(built.independent_review, "recipe review was not merged")
        self.assertTrue(built.passes >= frozenset({"07", "10", "11", "14"}))

    def test_a_fact_matching_no_rule_forces_full(self) -> None:
        # A fact can be classified and still match no reviewed rule. That is an
        # unrouted change, not a cheap one.
        built = self.route.build_route(
            (fact(self.route, "odd.py", surface="tests", effect="behavior"),), self.loaded)
        self.assertTrue(built.force_full)
        # L-08. Asserting only force_full let the reason code be deleted with
        # no test noticing, and the two ways a route can be unearned would then
        # be indistinguishable in a receipt.
        self.assertIn("ADC-ROUTE-UNROUTED-FACT", built.unknowns)
        self.assertNotIn("ADC-ROUTE-UNMAPPED-PATH", built.unknowns)

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
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET))
        self.assertNotIn("docs", built.matched_rule_ids)
        self.assertTrue(built.force_full, "an unmatched fact must force full")


class HintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route()
        self.loaded = loaded(self.route)
        self.base = self.route.build_route((fact(self.route, "README.md"),), loaded(self.route))

    def test_a_hint_can_raise_the_level(self) -> None:
        raised = self.route.apply_hints(self.base, {"minimum_level": 2}, self.loaded)
        self.assertEqual(raised.minimum_level, 2)

    def test_a_hint_can_add_passes_and_obligations(self) -> None:
        raised = self.route.apply_hints(
            self.base, {"passes": ["07"], "obligations": {"V12": ["hostile-environment"]}},
            self.loaded)
        self.assertIn("07", raised.passes)
        self.assertEqual(raised.obligations["V12"], frozenset({"hostile-environment"}))

    def test_a_hint_can_add_a_gate_to_an_existing_capability(self) -> None:
        raised = self.route.apply_hints(
            self.base, {"obligations": {"V09": ["distribution"]}}, self.loaded)
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
            {"minimum_level": 1, "force_full": False},
        ]
        for hint in hostile:
            after = self.route.apply_hints(high, hint, self.loaded)
            assert_route_not_lower(self, high, after, f"hint {hint}")

    def test_a_hint_cannot_clear_an_existing_reason_or_unmapped_path(self) -> None:
        # K-12 and K-13. The earlier hostile-hint route had both sets empty, so
        # replacing their union with assignment could not show a loss. This
        # route carries a real reason code and a real unmapped path.
        carrying = self.route.build_route(
            (fact(self.route, "mystery.bin", confidence="unknown"),), self.loaded)
        self.assertTrue(carrying.unknowns, "fixture must carry a reason code")
        self.assertTrue(carrying.unmapped_paths, "fixture must carry an unmapped path")
        # A hint can no longer write these fields at all, so the surviving
        # risk is an allowed hint dropping them on the way through.
        for hint in ({"minimum_level": 3}, {"passes": ["07"]},
                     {"force_full": True}, {}):
            after = self.route.apply_hints(carrying, hint, self.loaded)
            self.assertIn("ADC-ROUTE-UNMAPPED-PATH", after.unknowns,
                          f"hint {hint} dropped an existing reason code")
            self.assertIn("mystery.bin", after.unmapped_paths,
                          f"hint {hint} dropped an existing unmapped path")

    def test_a_hint_cannot_invent_a_pass_capability_or_gate(self) -> None:
        # K-08. Hints took raw strings with no schema, so an agent could add a
        # pass, capability, gate, or reason code that does not exist.
        for hint in ({"passes": ["not-a-pass"]},
                     {"obligations": {"V99": ["validate-core"]}},
                     {"obligations": {"V09": ["not-a-gate"]}}):
            with self.assertRaises(self.route.HintError, msg=f"{hint}"):
                self.route.apply_hints(self.base, hint, self.loaded)

    def test_a_hint_cannot_write_deterministic_fields(self) -> None:
        # These record what the router observed. A hint is judgement, not
        # evidence, so it must not be able to author them at all.
        for field in ("matched_rule_ids", "unmapped_paths", "unknowns"):
            with self.assertRaises(self.route.HintError, msg=field):
                self.route.apply_hints(self.base, {field: ["anything"]}, self.loaded)

    def test_a_valid_hint_still_applies(self) -> None:
        raised = self.route.apply_hints(
            self.base, {"minimum_level": 2, "passes": ["07"],
                        "obligations": {"V12": ["hostile-environment"]}}, self.loaded)
        self.assertEqual(raised.minimum_level, 2)
        self.assertIn("07", raised.passes)
        self.assertEqual(raised.obligations["V12"], frozenset({"hostile-environment"}))

    def test_a_hint_level_must_be_a_real_level(self) -> None:
        # L-05. int() accepted 999 and any numeric string.
        for bad in (999, -1, "2", 2.0, True, None):
            with self.assertRaises(self.route.HintError, msg=f"level={bad!r}"):
                self.route.apply_hints(
                    self.base, {"minimum_level": bad}, self.loaded)

    def test_a_hint_flag_must_be_a_real_boolean(self) -> None:
        # bool("false") is True, so a string inverted the flag.
        for bad in ("false", "true", 1, 0, None):
            for flag in ("force_full", "independent_review"):
                with self.assertRaises(self.route.HintError, msg=f"{flag}={bad!r}"):
                    self.route.apply_hints(self.base, {flag: bad}, self.loaded)

    def test_a_hint_must_name_a_capability_and_gate_that_are_paired(self) -> None:
        # Checking capability membership and gate membership in separate unions
        # let a hint pair a capability with a gate no reviewed rule binds to it.
        with self.assertRaises(self.route.HintError):
            self.route.apply_hints(
                self.base, {"obligations": {"V09": ["hostile-environment"]}},
                self.loaded)

    def test_a_hint_cannot_borrow_a_pairing_from_a_proposed_rule(self) -> None:
        # A proposed rule never matches, so its pairings are not reviewed
        # authority and must not widen what a hint may name.
        policy = json.loads(json.dumps(POLICY))
        policy["rules"].append({
            "id": "not-approved", "review_status": "proposed",
            "match": {"surfaces": ["tests"]},
            "requires": {"minimum_level": 0},
            "obligations": {"V21": ["distribution"]}})
        validated = self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)
        base = self.route.build_route((fact(self.route, "README.md"),), validated)
        with self.assertRaises(self.route.HintError):
            self.route.apply_hints(
                base, {"obligations": {"V21": ["distribution"]}}, validated)

    def test_a_hint_cannot_invent_a_rule_match(self) -> None:
        with self.assertRaises(self.route.HintError):
            self.route.apply_hints(
                self.base, {"matched_rule_ids": ["authority"]}, self.loaded)


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
        elif isinstance(a, Mapping):
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

    def test_obligation_key_order_does_not_depend_on_fact_order(self) -> None:
        # K-07. Set fields compared equal across permutations while the
        # obligation mapping kept first-insertion order. Dataclass equality
        # hides that; a serializer would not.
        import itertools
        for subset in itertools.combinations(self.pool, 3):
            orders = [list(self.route.build_route(order, self.loaded).obligations)
                      for order in itertools.permutations(subset)]
            self.assertEqual(len(set(map(tuple, orders))), 1,
                             f"obligation key order changed: {orders}")
            self.assertEqual(orders[0], sorted(orders[0]),
                             "obligation keys are not in canonical order")

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
        validated = self.route.load_policy(self._policy(), GATES, CAPABILITY_IDS, FULL_SET)
        self.assertEqual(validated.schema_version, 1)

    def test_a_wrong_schema_version_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._policy(schema_version=2), GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_missing_full_recipe_is_rejected(self) -> None:
        policy = self._policy()
        del policy["full_recipe"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_full_recipe_naming_an_unknown_gate_is_rejected(self) -> None:
        policy = self._policy()
        policy["full_recipe"]["obligations"]["V09"] = ["no-such-gate"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_obligation_naming_an_unknown_gate_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["no-such-gate"]}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_obligation_naming_an_unapproved_gate_is_rejected(self) -> None:
        # A gate nobody reviewed cannot satisfy a capability.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["not-yet-reviewed"]}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_obligation_naming_a_disabled_gate_is_rejected(self) -> None:
        # A disabled gate will never run, so it covers nothing.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V09": ["switched-off"]}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_empty_obligation_gate_list_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(obligations={"V09": []}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_unknown_capability_id_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V99": ["validate-core"]}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_duplicate_rule_ids_are_rejected(self) -> None:
        policy = self._policy()
        policy["rules"] = [self._rule(), self._rule()]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_duplicate_gate_ids_are_rejected(self) -> None:
        gates = json.loads(json.dumps(GATES))
        gates["gates"].append({"id": "validate-core", "enabled": True,
                               "review_status": "approved"})
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._policy(), gates, CAPABILITY_IDS, FULL_SET)

    def test_a_negative_predicate_is_rejected(self) -> None:
        # R-015. A rule that fires on the absence of another fact is not
        # monotonic: adding a file could stop it firing.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(match={"surfaces": ["docs"], "not_paths": ["x"]}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_empty_match_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(match={}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_out_of_range_level_is_rejected(self) -> None:
        for level in (-1, 4, "2", None):
            with self.assertRaises(self.route.PolicyError, msg=f"level={level!r}"):
                self.route.load_policy(
                    self._with_rule(requires={"minimum_level": level}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_non_boolean_flag_is_rejected(self) -> None:
        for flag in ("force_full", "independent_review"):
            with self.assertRaises(self.route.PolicyError, msg=flag):
                self.route.load_policy(
                    self._with_rule(requires={"minimum_level": 1, flag: "yes"}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_an_unknown_pass_id_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(requires={"passes": ["99"], "minimum_level": 0}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_classifier_enum_typo_is_rejected_at_load(self) -> None:
        # Catching this at load rather than only at classification means a bad
        # policy fails before it can route anything.
        policy = self._policy()
        policy["classifier"] = {"surfaces": [
            {"glob": "*.py", "surface": "BOGUS", "effect": "behavior"}]}
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_classifier_entry_without_a_glob_is_rejected_at_load(self) -> None:
        policy = self._policy()
        policy["classifier"] = {"surfaces": [{"surface": "docs", "effect": "prose"}]}
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_string_path_pattern_is_rejected(self) -> None:
        # K-02, a routing bypass. Iterating a string yields characters, so the
        # "*" in "*.md" matched every path and handed unrelated files the cheap
        # rule. Every plural predicate must be a list.
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._with_rule(match={"paths": "*.md"}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_every_plural_predicate_must_be_a_nonempty_list_of_strings(self) -> None:
        for key, bad in (
            ("paths", "*.md"), ("paths", []), ("paths", [""]), ("paths", [1]),
            ("surfaces", "docs"), ("surfaces", []), ("surfaces", [None]),
            ("effects", "prose"), ("change_kinds", "modify"), ("sources", "committed"),
        ):
            with self.assertRaises(self.route.PolicyError, msg=f"{key}={bad!r}"):
                self.route.load_policy(self._with_rule(match={key: bad}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_predicate_members_must_be_closed_enum_values(self) -> None:
        for key, bad in (
            ("surfaces", ["BOGUS"]), ("effects", ["BOGUS"]), ("breadths", ["BOGUS"]),
            ("sensitivities", ["BOGUS"]), ("change_kinds", ["BOGUS"]),
            ("sources", ["BOGUS"]),
        ):
            with self.assertRaises(self.route.PolicyError, msg=f"{key}={bad!r}"):
                self.route.load_policy(self._with_rule(match={key: bad}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_mode_changed_must_be_an_actual_boolean(self) -> None:
        # bool("false") is True, so a string here inverted the predicate.
        for bad in ("false", "true", 0, 1, None):
            with self.assertRaises(self.route.PolicyError, msg=f"mode_changed={bad!r}"):
                self.route.load_policy(
                    self._with_rule(match={"mode_changed": bad}), GATES, CAPABILITY_IDS, FULL_SET)
        self.route.load_policy(self._with_rule(match={"mode_changed": True}), GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_full_recipe_below_level_three_is_rejected(self) -> None:
        # K-04. force_full at Level 0 contradicts D-020.
        for level in (0, 1, 2):
            policy = self._policy()
            policy["full_recipe"]["minimum_level"] = level
            with self.assertRaises(self.route.PolicyError, msg=f"level={level}"):
                self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_full_recipe_without_passes_is_rejected(self) -> None:
        policy = self._policy()
        policy["full_recipe"]["passes"] = []
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_the_loaded_policy_is_immune_to_later_mutation(self) -> None:
        # K-03, a routing bypass. load_policy returned a shallow copy, so a
        # caller could flip a nested rule from proposed to approved after
        # validation and turn a forced-full route into a cheap one.
        raw = self._policy()
        raw["rules"] = [self._rule(review_status="proposed")]
        loaded = self.route.load_policy(raw, GATES, CAPABILITY_IDS, FULL_SET)
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

    def test_loading_requires_a_capability_catalog(self) -> None:
        # K-06. Defaulting to V01 through V22 put a count literal back after
        # D-029 removed the others, and made the router guess at a list the
        # catalog file already owns.
        with self.assertRaises(TypeError):
            self.route.load_policy(self._policy(), GATES)

    def test_the_capability_set_comes_from_the_shipped_catalog(self) -> None:
        ids = self.route.capability_ids_from_catalog(CAPABILITIES)
        catalog = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        self.assertEqual(ids, frozenset(c["id"] for c in catalog["capabilities"]))
        self.assertIn("V21", ids)
        self.assertIn("V22", ids)

    def test_the_supplied_capability_set_is_the_one_used(self) -> None:
        # Guessing V01 through V22 is invisible while the guess happens to
        # equal the catalog. This narrows the supplied set so a guess and the
        # real argument disagree, which is what D-029 is actually about.
        narrow = frozenset({"V09"})
        narrow_full = {"passes": ["07"], "obligations": {"V09": ["validate-core"]}}
        policy = self._with_rule(obligations={"V09": ["validate-core"]})
        # The full recipe names V08, V12 and V21, which the narrow set also
        # excludes. Reduce it so only the rule under test varies.
        policy["full_recipe"]["obligations"] = {"V09": ["validate-core"]}
        self.route.load_policy(policy, GATES, narrow, narrow_full)

        policy["rules"][0]["obligations"] = {"V12": ["hostile-environment"]}
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, narrow, narrow_full)

    def test_a_capability_the_catalog_does_not_define_is_rejected(self) -> None:
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                self._with_rule(obligations={"V23": ["validate-core"]}),
                GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_raw_mapping_is_refused_by_the_type_check(self) -> None:
        # M24. The provenance check would also refuse a mapping, so assert the
        # message: a caller passing an unvalidated dict should be told the type
        # is wrong, not sent looking for a loader that never ran.
        with self.assertRaises(TypeError) as caught:
            self.route.build_route((fact(self.route, "README.md"),), self._policy())
        self.assertIn("not dict", str(caught.exception))

    def test_a_directly_constructed_policy_is_refused(self) -> None:
        # L-04. isinstance proves the class, not that anything validated it.
        # A forged policy with an empty Level 0 recipe routed cheap.
        forged = self.route.ValidatedPolicy(
            schema_version=1, classifier=(),
            full_recipe=self.route.ValidatedRecipe(
                minimum_level=0, passes=frozenset(),
                independent_review=False, obligations=()),
            rules=(self.route.ValidatedRule(
                id="cheap", approved=True, match=(("surfaces", ("docs",)),),
                passes=frozenset(), minimum_level=0, force_full=False,
                independent_review=False, obligations=()),))
        with self.assertRaises(TypeError):
            self.route.build_route((fact(self.route, "README.md"),), forged)

    def test_field_replacement_does_not_carry_authority(self) -> None:
        # N-02. dataclasses.replace copies every field including the token, so
        # a tampered policy with a Level 0 recipe and a cheap approved rule
        # routed cheap. A token proves what was stamped, not what was checked.
        import dataclasses
        good = loaded(self.route)
        tampered = dataclasses.replace(
            good,
            full_recipe=self.route.ValidatedRecipe(
                minimum_level=0, passes=frozenset(),
                independent_review=False, obligations=()),
            rules=(self.route.ValidatedRule(
                id="cheap", approved=True, match=(("surfaces", ("docs",)),),
                passes=frozenset(), minimum_level=0, force_full=False,
                independent_review=False, obligations=()),))
        with self.assertRaises(TypeError):
            self.route.build_route((fact(self.route, "README.md"),), tampered)

    def test_the_registry_does_not_pin_policies(self) -> None:
        # M38. A plain dictionary would keep every policy ever loaded alive,
        # so a long-running process leaks one per call. The registry has to
        # hold weak references, and nothing asserted that.
        import gc
        policy = loaded(self.route)
        self.assertIn(id(policy), self.route._VALIDATED_POLICIES)
        marker = id(policy)
        del policy
        gc.collect()
        self.assertNotIn(marker, self.route._VALIDATED_POLICIES,
                         "the registry kept a policy alive after its last use")

    def test_a_loaded_policy_is_accepted(self) -> None:
        built = self.route.build_route(
            (fact(self.route, "README.md"),), loaded(self.route))
        self.assertEqual(built.matched_rule_ids, frozenset({"docs"}))

    def test_a_recipe_missing_a_canonical_pass_is_rejected(self) -> None:
        # L-03. Level 3 plus nonempty sets is not the same as covering the
        # repository's canonical full verification.
        policy = self._policy()
        policy["full_recipe"]["passes"] = ["07"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_recipe_missing_a_canonical_capability_is_rejected(self) -> None:
        # The gate check would also fire here, so assert which error is raised.
        # An absent capability and a capability missing gates are different
        # faults, and a message naming the wrong one sends a policy author
        # looking in the wrong place.
        policy = self._policy()
        policy["full_recipe"]["obligations"] = {"V09": ["validate-core"]}
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)
        self.assertIn("omits canonical capability", str(caught.exception))

    def test_a_recipe_missing_a_canonical_gate_is_rejected(self) -> None:
        policy = self._policy()
        policy["full_recipe"]["obligations"]["V12"] = ["validate-core"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)

    def test_loading_requires_the_canonical_full_set(self) -> None:
        # N-01. Optional validation is not validation. Omitting full_set
        # accepted a Level 3 recipe naming one pass and one capability.
        with self.assertRaises(TypeError):
            self.route.load_policy(self._policy(), GATES, CAPABILITY_IDS)

    def test_an_empty_canonical_full_set_is_rejected(self) -> None:
        # P-01. Making the argument required without checking its contents is
        # the same fault as making it optional: {} satisfied the requirement
        # and validated nothing, so a Level 3 recipe naming one pass and one
        # capability passed as canonical.
        for empty in ({}, {"passes": [], "obligations": {}}, {"passes": []},
                      {"obligations": {}}):
            with self.assertRaises(self.route.PolicyError, msg=f"{empty!r}"):
                self.route.load_policy(self._policy(), GATES, CAPABILITY_IDS, empty)

    def test_a_canonical_set_naming_unknown_ids_is_rejected(self) -> None:
        for bad in ({"passes": ["99"], "obligations": {"V09": ["validate-core"]}},
                    {"passes": ["07"], "obligations": {"V99": ["validate-core"]}},
                    {"passes": ["07"], "obligations": {"V09": ["no-such-gate"]}}):
            with self.assertRaises(self.route.PolicyError, msg=f"{bad!r}"):
                self.route.load_policy(self._policy(), GATES, CAPABILITY_IDS, bad)

    def test_a_recipe_covering_the_canonical_set_is_accepted(self) -> None:
        self.route.load_policy(self._policy(), GATES, CAPABILITY_IDS, FULL_SET)

    def test_a_proposed_rule_loads_but_never_matches(self) -> None:
        # D-022. The shipped template carries proposed rules, so loading must
        # accept them. build_route ignores them, which leaves the change
        # unrouted and therefore full.
        policy = self._policy()
        policy["rules"] = [self._rule(review_status="proposed")]
        validated = self.route.load_policy(policy, GATES, CAPABILITY_IDS, FULL_SET)
        built = self.route.build_route((fact(self.route, "README.md"),), validated)
        self.assertEqual(built.matched_rule_ids, frozenset())
        self.assertTrue(built.force_full)


def _free_loopback_port() -> int:
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]
    finally:
        probe.close()


def _force_rm(path: Path) -> None:
    """Remove a git tree on a host that refuses to unlink read-only files.

    Git marks loose objects and packs read-only. Windows honours that on
    unlink, so a plain rmtree leaves the tree behind and the next run fails on
    a directory that looks like leftover state.
    """
    def clear(func, target, exc):
        os.chmod(target, 0o700)
        func(target)

    if path.exists():
        shutil.rmtree(path, onexc=clear)


@unittest.skipUnless(shutil.which("git"), "git is required")
class PartialCloneAgainstRealGitDaemonTests(unittest.TestCase):
    """Q-05. A real blobless clone holding a genuinely missing promisor object.

    The earlier test asserted only that GIT_NO_LAZY_FETCH was present, and said
    plainly that it could not build a real blobless clone because a local file
    transport ignores the filter. git daemon supplies the missing piece: a real
    git:// transport, bound to loopback, for the life of this class.

    What is held here is not that a flag is set. It is that a missing promisor
    object stops acquisition and is reported as unreadable, and that without
    the guard the same acquisition reaches the network and writes an object
    while reporting the change complete.

    Reaching a missing object at all takes a specific shape. Acquisition runs
    three raw diffs, and a raw diff normally needs object ids rather than
    object content. The exception is inexact rename detection, which must score
    similarity by reading both blobs. So the fixture puts an inexact rename
    across the base, and the base side of that rename is the object the clone
    does not have. A fixture without it passes whether or not the guard exists.
    """

    daemon = None
    root: Path | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.route = load_route()
        cls.root = Path(tempfile.mkdtemp(prefix="adc-promisor-"))
        origin = cls.root / "origin"
        origin.mkdir()
        cls._git("init", "-q", "-b", "main", cwd=origin)
        for key, value in (
            ("user.email", "router@test.invalid"),
            ("user.name", "router test"),
            # Without this the daemon serves the clone but refuses the filter,
            # and the clone comes back complete with nothing missing.
            ("uploadpack.allowFilter", "true"),
            ("uploadpack.allowAnySHA1InWant", "true"),
        ):
            cls._git("config", key, value, cwd=origin)

        (origin / "a.txt").write_text(("shared payload line" + chr(10)) * 60,
                                      encoding="utf-8")
        (origin / "keep.txt").write_text("keep one" + chr(10), encoding="utf-8")
        cls._git("add", "-A", cwd=origin)
        cls._git("commit", "-qm", "base", cwd=origin)
        cls.base_sha = cls._git("rev-parse", "HEAD", cwd=origin).stdout.strip()
        cls.base_blob = cls._git("rev-parse", "HEAD:a.txt",
                                 cwd=origin).stdout.strip()

        # Inexact, so rename detection cannot settle it by object id and has to
        # read the base blob. An exact rename shares the object with the tip,
        # which means the tip checkout fetches it and nothing is ever missing.
        (origin / "renamed.txt").write_text(
            ("shared payload line" + chr(10)) * 57 + "tail change" + chr(10),
            encoding="utf-8")
        (origin / "a.txt").unlink()
        cls._git("add", "-A", cwd=origin)
        cls._git("commit", "-qm", "inexact rename", cwd=origin)
        (origin / "keep.txt").write_text("keep two" + chr(10), encoding="utf-8")
        cls._git("add", "-A", cwd=origin)
        cls._git("commit", "-qm", "tip", cwd=origin)

        # No probe for the subcommand. git daemon lives in libexec rather than
        # on PATH, and its name carries an extension on some hosts, so every
        # cheap presence check is wrong somewhere. Starting it and watching
        # whether it accepts a connection answers the question directly.
        cls.port = _free_loopback_port()
        cls.daemon = subprocess.Popen(
            ["git", "daemon", f"--port={cls.port}", "--listen=127.0.0.1",
             "--export-all", "--enable=upload-pack",
             f"--base-path={cls.root}", str(cls.root)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(100):
            if cls.daemon.poll() is not None:
                break
            try:
                socket.create_connection(("127.0.0.1", cls.port), 0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        else:
            cls._teardown_all()
            raise unittest.SkipTest("git daemon never accepted a connection")
        if cls.daemon.poll() is not None:
            why = (cls.daemon.stderr.read() or b"").decode(errors="replace").strip()
            cls._teardown_all()
            raise unittest.SkipTest(f"git daemon exited during startup: {why}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._teardown_all()

    @classmethod
    def _teardown_all(cls) -> None:
        if cls.daemon is not None:
            terminate_daemon_process_tree(cls.daemon)
            cls.daemon = None
        cls._teardown_root()

    @classmethod
    def _teardown_root(cls) -> None:
        if cls.root is not None:
            _force_rm(cls.root)
            cls.root = None

    @staticmethod
    def _git(*args, cwd=None, env=None):
        environment = dict(os.environ)
        environment.update(env or {})
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, env=environment, timeout=60)

    def _clone(self, name: str) -> Path:
        target = self.root / name
        done = self._git("clone", "-q", "--filter=blob:none",
                         f"git://127.0.0.1:{self.port}/origin", str(target))
        if done.returncode:
            self.skipTest(f"blobless clone failed: {done.stderr.strip()}")
        missing = self._missing_in(target)
        if self.base_blob not in missing:
            # No missing promisor object means there is nothing to prove, and
            # asserting against a complete clone would pass for the wrong
            # reason. Say why rather than reporting a result.
            self.skipTest(
                "clone is not missing the base blob, so the transport or the "
                f"filter did not take effect (missing: {len(missing)})")
        return target

    def _missing_in(self, clone: Path) -> set[str]:
        out = self._git("rev-list", "--objects", "--all", "--missing=print",
                        cwd=clone).stdout
        return {line[1:].split()[0] for line in out.splitlines()
                if line.startswith("?")}

    def test_the_clone_is_missing_a_real_promisor_object(self) -> None:
        clone = self._clone("precondition")
        self.assertIn(self.base_blob, self._missing_in(clone))
        self.assertEqual(
            "true",
            self._git("config", "--get", "remote.origin.promisor",
                      cwd=clone).stdout.strip(),
            "the clone did not record a promisor remote, so a missing object "
            "here would be corruption rather than a partial clone")

    def test_acquisition_reports_the_missing_object_and_fetches_nothing(self) -> None:
        clone = self._clone("guarded")
        before = self._missing_in(clone)
        snapshot = self.route.read_change_inputs(clone, self.base_sha)
        self.assertFalse(snapshot.complete)
        self.assertIn("ADC-ROUTE-COMMITTED-UNREADABLE", snapshot.problems)
        self.assertEqual(before, self._missing_in(clone),
                         "acquisition fetched an object it should have refused")

    def test_without_the_guard_acquisition_reaches_the_network(self) -> None:
        """The counterfactual. Without this the test above proves nothing.

        If acquisition never needed the missing object, it would report
        complete and fetch nothing whether or not the guard existed, and the
        assertion above would hold for a reason that has nothing to do with the
        control it names.
        """
        clone = self._clone("unguarded")
        before = self._missing_in(clone)
        original = subprocess.run

        def without_guard(command, **kwargs):
            environment = kwargs.get("env")
            if environment and "GIT_NO_LAZY_FETCH" in environment:
                kwargs["env"] = {key: value
                                 for key, value in environment.items()
                                 if key != "GIT_NO_LAZY_FETCH"}
            return original(command, **kwargs)

        self.route.subprocess.run = without_guard
        try:
            snapshot = self.route.read_change_inputs(clone, self.base_sha)
        finally:
            self.route.subprocess.run = original

        fetched = before - self._missing_in(clone)
        self.assertIn(self.base_blob, fetched,
                      "removing the guard changed nothing, so this fixture "
                      "does not reach a missing promisor object and the "
                      "guarded result above is not evidence")
        self.assertTrue(snapshot.complete,
                        "unguarded acquisition fetched the object but still "
                        "reported the change incomplete")

TEST_SUITE_DIR = SKILL_ROOT / "tests"


def suite_test_definitions(suite_dir=TEST_SUITE_DIR, repo_root=REPO_ROOT):
    """Return source node ids and duplicate definitions for the whole suite."""
    definitions = []
    duplicates = []
    for path in sorted(suite_dir.rglob("test_*.py")):
        relative = path.relative_to(repo_root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_names: dict[str, list[int]] = {}
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                module_names.setdefault(node.name, []).append(node.lineno)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test"):
                    definitions.append((f"{relative}::{node.name}", node.lineno))
                continue
            if not isinstance(node, ast.ClassDef):
                continue
            method_names: dict[str, list[int]] = {}
            for member in node.body:
                if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not member.name.startswith("test"):
                    continue
                method_names.setdefault(member.name, []).append(member.lineno)
                definitions.append(
                    (f"{relative}::{node.name}::{member.name}", member.lineno))
            for name, lines in method_names.items():
                if len(lines) > 1:
                    duplicates.append(
                        f"{relative}:{node.name}.{name} is defined at lines {lines}; "
                        "only the last definition can run")
        for name, lines in module_names.items():
            if len(lines) > 1:
                duplicates.append(
                    f"{relative}:{name} is defined at module lines {lines}; "
                    "only the last definition is reachable")
    return definitions, duplicates


class SuiteIntegrityTests(unittest.TestCase):
    """Structural checks on the suite, because a test that cannot run is worse
    than one that was never written: it reports as coverage and holds nothing.

    This branch has produced that failure twice. A slice edit deleted
    test_a_same_size_index_rewrite_is_detected and the suite stayed green,
    because a deleted test cannot fail; only a mutation verdict flipping caught
    it. The commit that restored it then pasted the neighbouring test a second
    time, and Python kept the later definition and silently discarded the
    earlier one. Nothing in a green suite distinguishes either case from
    healthy coverage, and both were found by accident.
    """

    def test_no_test_name_is_defined_twice(self) -> None:
        _, duplicates = suite_test_definitions()
        self.assertEqual([], duplicates, "; ".join(duplicates))

    def test_integrity_inventory_covers_every_test_module(self) -> None:
        definitions, _ = suite_test_definitions()
        inventoried = {node_id.split("::", 1)[0] for node_id, _ in definitions}
        candidates = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in TEST_SUITE_DIR.rglob("test_*.py")
        }
        self.assertEqual(
            candidates, inventoried,
            "a test module is outside the duplicate and reachability inventory")

    def test_integrity_inventory_recurses_into_nested_test_modules(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            nested = root / "tests" / "nested" / "test_child.py"
            nested.parent.mkdir(parents=True)
            nested.write_text(
                "def test_nested_case():\n    pass\n", encoding="utf-8")

            definitions, duplicates = suite_test_definitions(
                root / "tests", root)

        self.assertEqual([], duplicates)
        self.assertEqual(
            [("tests/nested/test_child.py::test_nested_case", 1)], definitions)

    def test_every_defined_test_is_collected_across_the_suite(self) -> None:
        """Collection is the authority on decorators, assignments, and names."""
        definitions, _ = suite_test_definitions()
        done = subprocess.run(
            [sys.executable, "-m", "pytest", str(TEST_SUITE_DIR),
             "--collect-only", "-q"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        collected = {
            line.replace("\\", "/")
            for line in done.stdout.splitlines()
            if "::" in line and not line.startswith(" ")
        }
        unreachable = [
            f"{node_id} defined at line {line} is not collected"
            for node_id, line in definitions if node_id not in collected
        ]
        self.assertEqual([], unreachable, "; ".join(unreachable))

    def test_replay_launches_pytest_with_the_current_interpreter(self) -> None:
        """Python 3-only hosts need no ambient ``python`` launcher alias."""
        harness = load_module(
            "adc_replay_launcher",
            REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")
        self.assertEqual(sys.executable, harness.suite_command(("suite.py",))[0])

    def test_replay_restores_the_exact_source_bytes(self) -> None:
        """A CRLF source must not return as LF after a successful replay."""
        harness = load_module(
            "adc_replay_restoration",
            REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\r\nafter = False\r\n"
            source.write_bytes(original)
            harness.REPO_ROOT = root
            harness.host_identity = lambda: {
                "platform": "Test", "release": "1", "python": "3",
                "git": "git version test"}
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            row = {
                "id": "MX", "name": "fixture", "source": "source.py",
                "old": "before = True", "new": "before = False",
                "results": []}

            self.assertEqual(0, harness.replay([row], write=False))
            self.assertEqual(original, source.read_bytes())

    def test_replay_rejects_a_launcher_error_as_no_test_evidence(self) -> None:
        """Exit 1 is meaningful only when pytest actually ran tests."""
        harness = load_module(
            "adc_replay_suite_error",
            REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")
        launcher_error = subprocess.CompletedProcess(
            args=[sys.executable, "-m", "pytest"], returncode=1,
            stdout="", stderr=f"{sys.executable}: No module named pytest\n")
        with mock.patch.object(harness.subprocess, "run",
                               return_value=launcher_error):
            with self.assertRaises(harness.SuiteBroken):
                harness.run_suite(("suite.py",))


class ReplayStructuredEvidenceTests(unittest.TestCase):
    """D-068. A serial replay row is evidence only when it is complete."""

    def _harness(self, name: str):
        return load_module(
            name, REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")

    @staticmethod
    def _row() -> dict:
        return {
            "id": "MX", "name": "fixture", "source": "source.py",
            "old": "before = True", "new": "before = False", "results": [],
        }

    @staticmethod
    def _host() -> dict:
        return {"platform": "Test", "release": "1", "python": "3",
                "git": "git version test"}

    def test_replay_structured_row_records_hashes_and_exact_pytest_evidence(self) -> None:
        """Dropping a row field would make replay evidence non-comparable."""
        harness = self._harness("adc_replay_structured_row")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\r\nafter = False\r\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (
                1, "1 failed, 2 passed, 3 skipped in 0.01s", 3)

            result = harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual("MX", result["id"])
            self.assertEqual("completed", result["status"])
            self.assertEqual("caught", result["verdict"])
            self.assertTrue(result["caught"])
            self.assertEqual("1 failed, 2 passed, 3 skipped in 0.01s",
                             result["pytest"])
            self.assertEqual(3, result["skipped"])
            self.assertEqual(harness.sha256_bytes(original),
                             result["source_hash_before"])
            self.assertEqual(harness.sha256_bytes(original),
                             result["source_hash_after"])
            self.assertEqual("commit-test", result["commit"])
            self.assertEqual("serial", result["worker"])
            self.assertIsInstance(result["duration"], float)
            self.assertGreaterEqual(result["duration"], 0.0)
            self.assertEqual(original, source.read_bytes())

    def test_replay_target_failures_leave_source_unchanged(self) -> None:
        """Changing zero or two targets must not test an arbitrary occurrence."""
        harness = self._harness("adc_replay_target_failures")
        for contents, status in ((b"after = False\n", "target-missing"),
                                 (b"before = True\nbefore = True\n",
                                  "target-ambiguous")):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as raw_root:
                root = Path(raw_root)
                source = root / "source.py"
                source.write_bytes(contents)
                harness.commit_identity = lambda repo_root: "commit-test"

                result = harness.run_row(root, self._row(), self._host(), "serial")

                self.assertEqual(status, result["status"])
                self.assertEqual("INCONCLUSIVE", result["verdict"])
                self.assertIsNone(result["caught"])
                self.assertEqual(contents, source.read_bytes())

    def test_replay_rejects_an_unanchored_pytest_summary(self) -> None:
        """A launcher error must not become a caught mutation on exit one."""
        harness = self._harness("adc_replay_unanchored_summary")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (
                1, "python: No module named pytest", 0)

            result = harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual("inconclusive", result["status"])
            self.assertEqual("INCONCLUSIVE", result["verdict"])
            self.assertIn("no test summary", result["error"])
            self.assertEqual(original, source.read_bytes())

    def test_replay_rejects_an_invalid_pytest_exit(self) -> None:
        """Exit two is an invocation failure even with a pytest-shaped line."""
        harness = self._harness("adc_replay_invalid_exit")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (2, "2 passed in 0.01s", 0)

            result = harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual("inconclusive", result["status"])
            self.assertEqual("INCONCLUSIVE", result["verdict"])
            self.assertIn("pytest exit 2", result["error"])
            self.assertEqual(original, source.read_bytes())

    def test_replay_retains_pytest_failure_output_for_an_invalid_exit(self) -> None:
        """An inconclusive worker result must retain its diagnosis."""
        harness = self._harness("adc_replay_invalid_exit_output")
        completed = subprocess.CompletedProcess(
            args=[sys.executable, "-m", "pytest"], returncode=2,
            stdout="1 error in 0.01s\n", stderr="fixture setup exploded\n")
        with mock.patch.object(harness.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(harness.SuiteBroken, "fixture setup exploded"):
                harness.run_suite(("suite.py",))

    def test_replay_structured_summary_accepts_pytest_minute_duration(self) -> None:
        """A slow valid suite must not lose its mutation verdict at one minute."""
        harness = self._harness("adc_replay_minute_summary")

        self.assertIsNotNone(harness.PYTEST_SUMMARY.fullmatch(
            "2 failed, 258 passed, 1 skipped, 9 deselected, 2 subtests passed "
            "in 62.63s (0:01:02)"))

    def test_replay_structured_summary_rejects_trailing_junk_and_invalid_clock(self) -> None:
        """Anchored evidence cannot accept text after pytest or impossible clocks."""
        harness = self._harness("adc_replay_invalid_minute_summary")
        valid = "2 failed, 258 passed in 62.63s"

        self.assertIsNone(harness.PYTEST_SUMMARY.fullmatch(valid + " trailing"))
        self.assertIsNone(harness.PYTEST_SUMMARY.fullmatch(valid + " (0:99:99)"))

    def test_replay_restoration_hash_mismatch_is_inconclusive(self) -> None:
        """A failed restore must reject the row instead of claiming a verdict."""
        harness = self._harness("adc_replay_restoration_hash")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            real_write_bytes = Path.write_bytes

            def corrupt_restore(path: Path, data: bytes) -> int:
                if path == source and data == original:
                    return real_write_bytes(path, data + b"# restore failed\n")
                return real_write_bytes(path, data)

            with mock.patch.object(Path, "write_bytes", new=corrupt_restore):
                result = harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual("inconclusive", result["status"])
            self.assertEqual("INCONCLUSIVE", result["verdict"])
            self.assertFalse(result["restored"])
            self.assertNotEqual(result["source_hash_before"], result["source_hash_after"])

    def test_replay_restoration_write_failure_records_measured_mutant_state(self) -> None:
        """A failed restore write must return inconclusive evidence, not raise."""
        harness = self._harness("adc_replay_restoration_write_failure")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\n"
            mutant = b"before = False\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            real_write_bytes = Path.write_bytes

            def fail_restore(path: Path, data: bytes) -> int:
                if path == source and data == original:
                    raise OSError("restore write denied")
                return real_write_bytes(path, data)

            with mock.patch.object(Path, "write_bytes", new=fail_restore):
                result = harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual("inconclusive", result["status"])
            self.assertEqual("INCONCLUSIVE", result["verdict"])
            self.assertIsNone(result["caught"])
            self.assertFalse(result["restored"])
            self.assertIn("restoration write failed", result["error"])
            self.assertEqual(harness.sha256_bytes(mutant), result["source_hash_after"])
            self.assertEqual("readable", result["source_after_state"])
            self.assertEqual(mutant, source.read_bytes())

    def test_replay_preserves_mutation_error_when_restoration_also_fails(self) -> None:
        """A second failure in finally must not replace the mutation failure."""
        harness = self._harness("adc_replay_preserves_original_error")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            original = b"before = True\n"
            mutant = b"before = False\n"
            source.write_bytes(original)
            harness.commit_identity = lambda repo_root: "commit-test"
            real_write_bytes = Path.write_bytes

            def fail_mutation_and_restore(path: Path, data: bytes) -> int:
                if path == source and data == mutant:
                    raise OSError("mutation write denied")
                if path == source and data == original:
                    raise OSError("restore write denied")
                return real_write_bytes(path, data)

            with mock.patch.object(Path, "write_bytes", new=fail_mutation_and_restore):
                with self.assertRaisesRegex(OSError, "mutation write denied"):
                    harness.run_row(root, self._row(), self._host(), "serial")

            self.assertEqual(original, source.read_bytes())

    def test_replay_structured_report_is_coordinator_output(self) -> None:
        """A read-only run must emit comparable matrix and row evidence once."""
        harness = self._harness("adc_replay_structured_report")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            source.write_text("before = True\n", encoding="utf-8")
            matrix = root / "matrix.json"
            matrix.write_text(json.dumps([self._row()]), encoding="utf-8")
            report = root / "report.json"
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.host_identity = self._host
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            harness.worktree_status = lambda repo_root: ()

            self.assertEqual(0, harness.main(["MX", "--jobs", "1", "--report", str(report)]))

            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("commit-test", evidence["commit"])
            self.assertEqual(0, evidence["exit_code"])
            self.assertEqual(evidence["matrix_sha256_before"],
                             evidence["matrix_sha256_after"])
            self.assertEqual(["MX"], [row["id"] for row in evidence["rows"]])
            self.assertEqual("serial", evidence["rows"][0]["worker"])

    def test_serial_report_records_dirty_endpoints_without_refusing_read_only(self) -> None:
        """D-103. Dirty serial evidence is labelled, not silently forbidden."""
        harness = self._harness("adc_replay_serial_dirty_report")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            source.write_text("before = True\n", encoding="utf-8")
            matrix = root / "matrix.json"
            matrix.write_text(json.dumps([self._row()]), encoding="utf-8")
            report = root / "report.json"
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.host_identity = self._host
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            harness.worktree_status = mock.Mock(
                side_effect=[(" M handoff.md",), (" M handoff.md",)])

            self.assertEqual(0, harness.main(["--report", str(report)]))

            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual([" M handoff.md"],
                             evidence["serial_worktree_status_before"])
            self.assertEqual([" M handoff.md"],
                             evidence["serial_worktree_status_after"])
            self.assertEqual(["MX"], [row["id"] for row in evidence["rows"]])

    def test_serial_write_refuses_an_initially_dirty_tree_before_any_row(self) -> None:
        """D-103. A dirty tree cannot rewrite the authoritative matrix."""
        harness = self._harness("adc_replay_serial_dirty_write")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            matrix = root / "matrix.json"
            original = json.dumps([self._row()]).encode()
            matrix.write_bytes(original)
            report = root / "report.json"
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.worktree_status = mock.Mock(return_value=(" M handoff.md",))
            harness.run_serial = mock.Mock(side_effect=AssertionError(
                "a dirty write started a row"))

            self.assertEqual(2, harness.main(["--write", "--report", str(report)]))

            self.assertEqual(original, matrix.read_bytes())
            harness.run_serial.assert_not_called()
            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual([], evidence["rows"])
            self.assertEqual([" M handoff.md"],
                             evidence["serial_worktree_status_before"])

    def test_serial_write_refuses_new_dirt_before_matrix_publication(self) -> None:
        """D-103. An edit during replay cannot race the final matrix write."""
        harness = self._harness("adc_replay_serial_write_race")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            source.write_text("before = True\n", encoding="utf-8")
            matrix = root / "matrix.json"
            original = json.dumps([self._row()]).encode()
            matrix.write_bytes(original)
            report = root / "report.json"
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.host_identity = self._host
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.run_suite = lambda paths, repo_root: (1, "1 failed in 0.01s", 0)
            harness.worktree_status = mock.Mock(
                side_effect=[(), (" M handoff.md",), (" M handoff.md",)])

            self.assertEqual(2, harness.main(["--write", "--report", str(report)]))

            self.assertEqual(original, matrix.read_bytes())
            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(["MX"], [row["id"] for row in evidence["rows"]])
            self.assertEqual([" M handoff.md"],
                             evidence["serial_worktree_status_after"])

    def test_serial_console_renders_a_broken_suite_diagnostic_safely(self) -> None:
        """D-106. D-102 rendered the parallel path; serial printed raw text.

        Measured: a serial SuiteBroken carrying a newline and an ANSI escape
        printed a forged replay line on its own line, in colour.
        """
        harness = self._harness("adc_replay_serial_console_safety")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            harness.REPO_ROOT = root
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.host_identity = self._host

            def broken(paths, repo_root):
                raise harness.SuiteBroken(
                    "pytest exit 2: 1 error in 0.01s; output: x\n"
                    "  M01  forged row                                caught\n"
                    "\x1b[32m  1 mutants, 0 not caught: none\x1b[0m")

            harness.run_suite = broken
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                self.assertEqual(1, harness.replay([self._row()], write=False))

        console = buffer.getvalue()
        self.assertNotIn("\n  M01  forged row", console)
        self.assertNotIn("\x1b", console)
        self.assertIn(r"\n  M01  forged row", console)
        self.assertIn(r"\x1b[32m", console)
        self.assertEqual(1, sum("INCONCLUSIVE" in line for line in console.splitlines()))

    def test_an_unskipped_local_survivor_is_a_survivor_despite_a_foreign_record(self) -> None:
        """D-095. A host that skipped nothing and saw the mutant survive found a gap.

        The matrix stores one result per host and no commit per result. Before
        this held, the local verdict was folded into the stored foreign results
        first, so a stored "caught" from the other host turned a fresh local
        survivor into "caught elsewhere", the not-caught list stayed empty, and
        the run exited 0. The round-sixteen Linux replay that measured M92
        surviving reported "0 not caught" for exactly this reason, and the
        Linux CI job would have stayed green for any of the 88 rows Windows had
        once caught.
        """
        harness = self._harness("adc_replay_unskipped_survivor")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = root / "source.py"
            source.write_text("before = True\n", encoding="utf-8")
            harness.REPO_ROOT = root
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.host_identity = lambda: {
                "platform": "Windows", "release": "11", "python": "3",
                "git": "git version test"}
            foreign = {"platform": "Linux", "release": "1", "python": "3",
                       "git": "git version test", "verdict": "caught",
                       "pytest": "1 failed, 2 passed in 0.01s", "skipped": 0,
                       "failed_nodeids": ["source.py::test_guarantee"],
                       "skipped_nodeids": []}

            harness.run_suite = lambda paths, repo_root: (0, "3 passed in 0.01s", 0)
            row = {**self._row(), "results": [dict(foreign)]}
            self.assertEqual(1, harness.replay([row], write=False))
            self.assertEqual("SURVIVED", row["verdict"])

            # Under a skipped test this host observed nothing for the
            # guarantee, and the foreign record legitimately holds the row.
            harness.run_suite = lambda paths, repo_root: harness.SuiteOutcome(
                0, "2 passed, 1 skipped in 0.01s", 1, (),
                ("source.py::test_guarantee",))
            row = {**self._row(), "results": [dict(foreign)]}
            self.assertEqual(0, harness.replay([row], write=False))
            self.assertEqual("caught elsewhere", row["verdict"])

    def test_derive_verdict_lets_no_record_soften_an_unskipped_survivor(self) -> None:
        harness = self._harness("adc_replay_derive_unskipped")
        caught = {"platform": "Linux", "verdict": "caught", "skipped": 0,
                  "failed_nodeids": ["source.py::test_guarantee"],
                  "skipped_nodeids": []}
        survived = {"platform": "Windows", "verdict": "SURVIVED", "skipped": 0}
        under_skip = {**survived, "skipped": 1,
                      "skipped_nodeids": ["source.py::test_guarantee"]}
        self.assertEqual("SURVIVED", harness.derive_verdict([caught, survived]))
        self.assertEqual("SURVIVED", harness.derive_verdict([survived, caught]))
        self.assertEqual("caught elsewhere",
                         harness.derive_verdict([caught, under_skip]))
        self.assertEqual("caught", harness.derive_verdict(
            [caught, {**caught, "platform": "Windows"}]))

    def test_a_row_no_host_caught_is_survived_even_under_skips(self) -> None:
        """D-110. The label "unverified: every host skipped" hid a survivor.

        Measured at 49fed51: M107 survived on Windows under the one skipped
        symlink test with no catching host, the row read unverified, the
        summary read 0 not caught, and only the Linux job, which skips
        nothing, reported it.
        """
        harness = self._harness("adc_replay_no_catch_survived")
        under_skip = {"platform": "Windows", "verdict": "SURVIVED", "skipped": 1,
                      "failed_nodeids": [], "skipped_nodeids": ["suite.py::test_symlink"]}
        self.assertEqual("SURVIVED", harness.derive_verdict([under_skip]))
        self.assertEqual("SURVIVED", harness.derive_verdict(
            [under_skip, {**under_skip, "platform": "Linux"}]))
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            harness.REPO_ROOT = root
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.host_identity = lambda: {
                "platform": "Windows", "release": "11", "python": "3",
                "git": "git version test"}
            harness.run_suite = lambda paths, repo_root: harness.SuiteOutcome(
                0, "2 passed, 1 skipped in 0.01s", 1, (), ("suite.py::test_symlink",))
            row = self._row()
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                self.assertEqual(1, harness.replay([row], write=False))
        console = buffer.getvalue()
        self.assertEqual("SURVIVED", row["verdict"])
        self.assertIn("1 not caught: ['MX']", console)
        self.assertIn("1 skipped: test_symlink", console)

    def test_console_renders_every_matrix_field(self) -> None:
        """D-115. The renderer covered the error field only.

        Measured: a row name carrying a newline and an escape printed a
        forged summary line in colour, in both modes, because ids, names,
        replacement ids, and verdicts were printed raw from matrix.json.
        """
        harness = self._harness("adc_replay_console_fields")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            harness.REPO_ROOT = root
            harness.commit_identity = lambda repo_root: "commit-test"
            harness.host_identity = self._host
            harness.run_suite = lambda paths, repo_root: harness.SuiteOutcome(
                1, "1 failed in 0.01s", 0, ("suite.py::test_holds",), ())
            forged = "x\n\x1b[32m  9 mutants, 0 not caught: none\x1b[0m\n  MZZ  forged"
            rows = [{**self._row(), "name": forged},
                    {**self._row(), "id": "M\x1b[31mY", "name": "old",
                     "superseded_by": "M\nZ"}]
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                harness.replay(rows, write=False)
        console = buffer.getvalue()
        self.assertNotIn("\x1b", console)
        self.assertNotIn("\n  MZZ  forged", console)
        self.assertNotIn("M\nZ", console)
        self.assertIn(r"\x1b[32m", console)
        self.assertIn(r"M\nZ", console)

    def test_a_skipped_survivor_needs_exact_catching_test_attribution(self) -> None:
        """D-104. An unrelated skip cannot borrow another host's catch."""
        harness = self._harness("adc_replay_exact_skip_attribution")
        caught = {
            "platform": "Linux", "verdict": "caught", "skipped": 0,
            "failed_nodeids": ["suite.py::test_holds_mutant"],
            "skipped_nodeids": [],
        }
        relevant_skip = {
            "platform": "Windows", "verdict": "SURVIVED", "skipped": 1,
            "failed_nodeids": [],
            "skipped_nodeids": ["suite.py::test_holds_mutant"],
        }
        unrelated_skip = {
            **relevant_skip,
            "skipped_nodeids": ["suite.py::test_unrelated_platform_case"],
        }
        missing_identity = {
            key: value for key, value in relevant_skip.items()
            if key != "skipped_nodeids"
        }
        self.assertEqual("caught elsewhere",
                         harness.derive_verdict([caught, relevant_skip]))
        self.assertEqual("SURVIVED",
                         harness.derive_verdict([caught, unrelated_skip]))
        self.assertEqual("SURVIVED",
                         harness.derive_verdict([caught, missing_identity]))

    def test_replay_collects_exact_failed_and_skipped_nodeids(self) -> None:
        """D-104. Pytest identities, not summary counts, carry host limits."""
        harness = self._harness("adc_replay_exact_outcome_collection")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            plugin = root / "design" / "routing" / "mutants" / "exact_nodeid_plugin.py"
            plugin.parent.mkdir(parents=True)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py", plugin)
            (root / "test_probe.py").write_text(
                "import pytest\n\n"
                "def test_holds_mutant():\n    assert False\n\n"
                "@pytest.mark.skip(reason='platform probe')\n"
                "def test_unrelated_platform_case():\n    assert True\n",
                encoding="utf-8")

            outcome = harness.run_suite(("test_probe.py",), root)

        self.assertEqual(1, outcome[0])
        self.assertEqual(1, outcome[2])
        self.assertEqual(("test_probe.py::test_holds_mutant",),
                         outcome.failed_nodeids)
        self.assertEqual(("test_probe.py::test_unrelated_platform_case",),
                         outcome.skipped_nodeids)


@unittest.skipUnless(shutil.which("git"), "git is required")
class ReplayParallelCloneTests(unittest.TestCase):
    """D-084/D-068. Parallel replay owns clones, evidence, and cleanup."""

    SOURCE_DIGEST = "5c12e841742b193ea92f98a11951284c45117d17c5d07d794714ae85bb27ef07"

    def _harness(self, name: str):
        return load_module(
            name, REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")

    @staticmethod
    def _row(identifier: str) -> dict:
        return {
            "id": identifier, "name": "fixture", "source": "source.py",
            "old": "before = True", "new": "before = False", "results": [],
        }

    @staticmethod
    def _worker_result(row: dict, index: int, worker: str,
                       source_digest: str, commit: str = "commit-test") -> dict:
        """A complete, hand-written worker payload accepted by the coordinator."""
        return {
            "id": row["id"], "status": "completed", "verdict": "caught",
            "caught": True, "exit_code": 1,
            "pytest": "1 failed, 2 passed in 0.01s", "skipped": 0,
            "failed_nodeids": ["suite.py::test_holds_mutant"],
            "skipped_nodeids": [],
            "source_hash_before": source_digest, "source_hash_after": source_digest,
            "source_after_state": "readable", "restored": True,
            "commit": commit, "worker": worker,
            "host": {"platform": "Windows", "release": "11",
                     "python": "3.14.2", "git": "git version fixture"},
            "duration": 0.01, "matrix_index": index,
            "clone_retired": False,
        }

    @staticmethod
    def _git(repo: Path, *args: str) -> str:
        done = subprocess.run(["git", *args], cwd=repo, check=True,
                              capture_output=True, text=True)
        return done.stdout.strip()

    def _repository(self, root: Path) -> tuple[Path, str]:
        source = root / "source"
        source.mkdir()
        self._git(source, "init", "-q", "-b", "main")
        self._git(source, "config", "user.email", "parallel@test.invalid")
        self._git(source, "config", "user.name", "Parallel Test")
        (source / "source.py").write_text("before = True\n", encoding="utf-8")
        self._git(source, "add", "source.py")
        self._git(source, "commit", "-qm", "fixture")
        return source, self._git(source, "rev-parse", "HEAD")

    def test_windows_daemon_teardown_terminates_the_wrapper_process_tree(self) -> None:
        daemon = mock.Mock(pid=45123)
        with mock.patch.object(os, "name", "nt"), \
             mock.patch.object(subprocess, "run") as run:
            terminate_daemon_process_tree(daemon)

        run.assert_called_once_with(
            ["taskkill", "/PID", "45123", "/T", "/F"],
            capture_output=True, text=True, timeout=10, check=False)
        daemon.terminate.assert_not_called()

    def test_partition_rows_is_deterministic_round_robin_with_original_indices(self) -> None:
        harness = self._harness("adc_replay_parallel_partition")
        rows = [self._row(f"M{index}") for index in range(5)]

        self.assertEqual(
            [[(0, rows[0]), (3, rows[3])], [(1, rows[1]), (4, rows[4])],
             [(2, rows[2])]],
            harness.partition_rows(rows, 3),
        )
        with self.assertRaises(ValueError):
            harness.partition_rows(rows, 0)

    def test_prepare_clone_is_detached_at_the_exact_commit_without_hardlinks(self) -> None:
        harness = self._harness("adc_replay_parallel_clone")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source, commit = self._repository(root)
            matrix = source / "matrix.json"
            matrix.write_text(json.dumps([{
                "id": "M1", "source": "source.py",
                "old": "before = True", "new": "before = False",
            }]), encoding="utf-8")
            self._git(source, "add", "matrix.json")
            self._git(source, "commit", "-qm", "matrix fixture")
            commit = self._git(source, "rev-parse", "HEAD")
            harness.REPO_ROOT = source
            harness.MATRIX = matrix
            clone = root / "owned" / "worker-0"
            global_config = root / "global.gitconfig"
            global_config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
            blob = subprocess.run(
                ["git", "cat-file", "blob", f"{commit}:source.py"],
                cwd=source, capture_output=True, check=True).stdout

            with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(global_config)}):
                harness.prepare_clone(source, clone, commit)

            self.assertEqual(commit, self._git(clone, "rev-parse", "HEAD"))
            self.assertEqual(blob, (clone / "source.py").read_bytes())
            detached = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"],
                                      cwd=clone, capture_output=True)
            self.assertEqual(1, detached.returncode)
            source_tree = self._git(source, "rev-parse", "HEAD^{tree}")
            source_object = source / ".git" / "objects" / source_tree[:2] / source_tree[2:]
            clone_object = clone / ".git" / "objects" / source_tree[:2] / source_tree[2:]
            self.assertTrue(clone_object.is_file())
            self.assertFalse(os.path.samefile(source_object, clone_object))

    def test_parallel_refuses_a_dirty_coordinator_before_creating_workers(self) -> None:
        """A dirty replay authority cannot be mislabeled as its committed HEAD."""
        harness = self._harness("adc_replay_parallel_dirty_coordinator")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            replay = root / "design" / "routing" / "mutants" / "replay.py"
            replay.parent.mkdir(parents=True)
            shutil.copyfile(REPO_ROOT / "design" / "routing" / "mutants" / "replay.py", replay)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py",
                replay.with_name("exact_nodeid_plugin.py"))
            matrix = replay.with_name("matrix.json")
            matrix.write_text(json.dumps([self._row("M1")]), encoding="utf-8")
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            self._git(root, "init", "-q", "-b", "main")
            self._git(root, "config", "user.email", "parallel@test.invalid")
            self._git(root, "config", "user.name", "Parallel Test")
            self._git(root, "config", "core.autocrlf", "false")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "fixture")
            commit = self._git(root, "rev-parse", "HEAD")
            (root / "source.py").write_text("before = dirty\n", encoding="utf-8")
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.__file__ = str(replay)

            with mock.patch.object(harness, "ProcessPoolExecutor") as pool:
                result, cleanup = harness.run_parallel([self._row("M1")], 1, root)

        pool.assert_not_called()
        self.assertEqual([], cleanup)
        self.assertEqual("inconclusive", result[0]["status"])
        self.assertEqual(commit, result[0]["commit"])
        self.assertIn("source verification failed", result[0]["error"])

    def test_parallel_refuses_an_unclean_tree_even_when_every_source_matches_head(self) -> None:
        """D-096. Clones are built from HEAD; the serial path replays the disk.

        The frozen-source check sees only mutation targets. Measured before
        this held: one uncommitted edit to test_receipt.py, which no row
        mutates, made M57 SURVIVED serially and caught in parallel, both exit
        0, with nothing in either report saying the two runs described
        different trees.
        """
        harness = self._harness("adc_replay_parallel_unclean_tree")
        cases = (
            ("tracked suite edit", lambda root: (root / "suite.py").write_text(
                "# weakened\n", encoding="utf-8")),
            ("untracked conftest", lambda root: (root / "conftest.py").write_text(
                "# fixture\n", encoding="utf-8")),
        )
        for label, dirty in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_root:
                root = Path(raw_root)
                replay = root / "design" / "routing" / "mutants" / "replay.py"
                replay.parent.mkdir(parents=True)
                shutil.copyfile(REPO_ROOT / "design" / "routing" / "mutants" / "replay.py", replay)
                shutil.copyfile(
                    REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py",
                    replay.with_name("exact_nodeid_plugin.py"))
                matrix = replay.with_name("matrix.json")
                matrix.write_text(json.dumps([self._row("M1")]), encoding="utf-8")
                (root / "source.py").write_text("before = True\n", encoding="utf-8")
                (root / "suite.py").write_text("# holds M1\n", encoding="utf-8")
                self._git(root, "init", "-q", "-b", "main")
                self._git(root, "config", "user.email", "parallel@test.invalid")
                self._git(root, "config", "user.name", "Parallel Test")
                self._git(root, "config", "core.autocrlf", "false")
                self._git(root, "add", ".")
                self._git(root, "commit", "-qm", "fixture")
                commit = self._git(root, "rev-parse", "HEAD")
                dirty(root)
                harness.REPO_ROOT = root
                harness.MATRIX = matrix
                harness.__file__ = str(replay)

                # A clone must never be attempted: under a preflight that lets
                # the dirty tree through, the mocked pool would otherwise wait
                # on a future that never completes.
                with mock.patch.object(harness, "ProcessPoolExecutor") as pool, \
                     mock.patch.object(harness, "prepare_clone",
                                       side_effect=RuntimeError("must not clone")):
                    result, cleanup = harness.run_parallel([self._row("M1")], 1, root)

                pool.assert_not_called()
                self.assertEqual([], cleanup)
                self.assertEqual("inconclusive", result[0]["status"])
                self.assertEqual(commit, result[0]["commit"])
                self.assertIn("working tree differs from HEAD", result[0]["error"])
                self.assertEqual("before = True\n",
                                 (root / "source.py").read_text(encoding="utf-8"))

    def test_clone_partition_retires_a_clone_after_an_unrestored_row(self) -> None:
        harness = self._harness("adc_replay_parallel_retirement")
        rows = [(0, self._row("M1")), (1, self._row("M2"))]
        broken = {
            "id": "M1", "status": "inconclusive", "verdict": "INCONCLUSIVE",
            "restored": False, "worker": "worker-0",
        }
        with tempfile.TemporaryDirectory() as raw_root:
            clone = Path(raw_root) / "clone"
            clone.mkdir()
            with mock.patch.object(harness, "run_row", return_value=broken) as run_row:
                result = harness.run_clone_partition(clone, rows, "worker-0")

        self.assertEqual(["M1"], [row["id"] for row in result])
        self.assertEqual(1, run_row.call_count)
        self.assertTrue(result[0]["clone_retired"])

    def test_parallel_emits_a_superseded_row_without_creating_a_worker(self) -> None:
        harness = self._harness("adc_replay_parallel_superseded")
        row = self._row("M26")
        row["superseded_by"] = "M27"
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            with mock.patch.object(harness, "commit_identity", return_value="a" * 40), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={}), \
                 mock.patch.object(harness, "ProcessPoolExecutor") as pool:
                result, cleanup = harness.run_parallel([row], 99, root)

        pool.assert_not_called()
        self.assertEqual([], cleanup)
        self.assertEqual("superseded", result[0]["status"])
        self.assertTrue(result[0]["restored"])

    def test_parallel_preflight_failure_preserves_mixed_superseded_order(self) -> None:
        """A failed preflight must not look up a worker for a superseded row."""
        harness = self._harness("adc_replay_parallel_mixed_preflight")
        rows = [self._row("M1"), self._row("M2"), self._row("M3")]
        rows[1]["superseded_by"] = "M4"
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            with mock.patch.object(harness, "commit_identity", return_value="a" * 40), \
                 mock.patch.object(harness, "_verify_coordinator_sources",
                                   side_effect=RuntimeError("preflight")), \
                 mock.patch.object(harness, "ProcessPoolExecutor") as pool:
                result, cleanup = harness.run_parallel(rows, 2, root)

        pool.assert_not_called()
        self.assertEqual([], cleanup)
        self.assertEqual(["M1", "M2", "M3"], [item["id"] for item in result])
        self.assertEqual(["inconclusive", "superseded", "inconclusive"],
                         [item["status"] for item in result])
        self.assertEqual(["worker-0", "serial", "worker-1"],
                         [item["worker"] for item in result])
        self.assertTrue(result[1]["restored"])
        self.assertIn("coordinator source verification failed", result[0]["error"])

    def test_parallel_superseded_only_skips_preflight_and_workers(self) -> None:
        harness = self._harness("adc_replay_parallel_superseded_only")
        rows = [self._row("M1"), self._row("M2")]
        for row in rows:
            row["superseded_by"] = "M3"
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            with mock.patch.object(harness, "commit_identity", return_value="a" * 40), \
                 mock.patch.object(harness, "_verify_coordinator_sources") as verify, \
                 mock.patch.object(harness, "ProcessPoolExecutor") as pool:
                result, cleanup = harness.run_parallel(rows, 8, root)

        verify.assert_not_called()
        pool.assert_not_called()
        self.assertEqual([], cleanup)
        self.assertEqual(["superseded", "superseded"],
                         [item["status"] for item in result])

    def test_worker_suite_uses_owned_parent_cwd_with_absolute_suite_paths(self) -> None:
        """Detached helpers from a suite must not retain the clone as cwd."""
        harness = self._harness("adc_replay_parallel_worker_cwd")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            clone = root / "worker-0"
            clone.mkdir()
            suite = clone / "anti-dark-code" / "tests" / "test_route.py"
            suite.parent.mkdir(parents=True)
            suite.write_text("# fixture\n", encoding="utf-8")
            captured: dict[str, object] = {}
            completed = subprocess.CompletedProcess([], 1, "1 failed in 0.01s\n", "")

            def capture(command, **kwargs):
                captured["command"] = command
                captured["cwd"] = kwargs["cwd"]
                Path(kwargs["env"]["ADC_EVIDENCE_OUTCOMES"]).write_text(
                    json.dumps({
                        "exitstatus": 1,
                        "collect_nodeids": ["suite.py::test_holds_mutant"],
                        "outcomes": {"suite.py::test_holds_mutant": "failed"},
                        "missing": [],
                    }), encoding="utf-8")
                return completed

            harness._WORKER_SUITE_CWD = root
            with mock.patch.object(harness.subprocess, "run", side_effect=capture):
                self.assertEqual((1, "1 failed in 0.01s", 0),
                                 harness.run_suite(("anti-dark-code/tests/test_route.py",), clone))

        self.assertEqual(root, captured["cwd"])
        self.assertIn(str(suite), captured["command"])
        # D-098: the collection tree must not climb above the clone. Without
        # this pytest roots itself at the common ancestor of cwd and the suite
        # path, which on a coordinator beneath the host temp directory is the
        # machine-wide temp directory, and collection dies when any other
        # process removes an entry there mid-scan.
        self.assertIn(f"--rootdir={clone}", captured["command"])

    def test_clone_partition_uses_the_stable_coordinator_cwd_for_its_suite(self) -> None:
        harness = self._harness("adc_replay_parallel_stable_cwd")
        row = self._row("M1")
        observed: list[Path | None] = []
        with tempfile.TemporaryDirectory() as raw_root:
            stable = Path(raw_root) / "stable-coordinator"
            stable.mkdir()
            clone = Path(raw_root) / "owned" / "worker-0"
            clone.parent.mkdir()
            clone.mkdir()
            harness.REPO_ROOT = stable

            def run_row(clone_path, row_data, host, worker):
                observed.append(harness._WORKER_SUITE_CWD)
                return {"id": row_data["id"], "status": "completed",
                        "verdict": "caught", "restored": True, "worker": worker}

            with mock.patch.object(harness, "run_row", side_effect=run_row):
                harness.run_clone_partition(clone, [(0, row)], "worker-0")

            self.assertEqual([stable], observed)

    def test_clone_partition_owns_a_unique_auxiliary_pytest_root(self) -> None:
        harness = self._harness("adc_replay_parallel_auxiliary_root")
        observed: list[Path | None] = []

        def run_row(clone_path, row_data, host, worker):
            observed.append(harness._WORKER_TEMP_ROOT)
            return {"id": row_data["id"], "status": "completed",
                    "verdict": "caught", "restored": True, "worker": worker}

        with tempfile.TemporaryDirectory() as raw_root:
            clone = Path(raw_root) / "owned" / "worker-2"
            clone.parent.mkdir()
            clone.mkdir()
            with mock.patch.object(harness, "run_row", side_effect=run_row):
                harness.run_clone_partition(clone, [(0, self._row("M1"))], "worker-2")

            self.assertEqual([clone.parent / "worker-2-pytest"], observed)

    def test_worker_suite_uses_private_temp_environment_and_pytest_basetemp(self) -> None:
        harness = self._harness("adc_replay_parallel_private_temp")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            clone = root / "worker-0"
            suite = clone / "suite.py"
            clone.mkdir()
            suite.write_text("# fixture\n", encoding="utf-8")
            private = root / "worker-0-pytest"
            private.mkdir()
            captured: dict[str, object] = {}
            completed = subprocess.CompletedProcess([], 1, "1 failed in 0.01s\n", "")

            def capture(command, **kwargs):
                captured["command"] = command
                captured["env"] = kwargs["env"]
                Path(kwargs["env"]["ADC_EVIDENCE_OUTCOMES"]).write_text(
                    json.dumps({
                        "exitstatus": 1,
                        "collect_nodeids": ["suite.py::test_holds_mutant"],
                        "outcomes": {"suite.py::test_holds_mutant": "failed"},
                        "missing": [],
                    }), encoding="utf-8")
                return completed

            harness._WORKER_TEMP_ROOT = private
            hostile = {"PYTHONUSERBASE": str(root / "userbase"),
                       "PYTHONWARNINGS": "error", "PYTHONOPTIMIZE": "2",
                       "PYTHONPYCACHEPREFIX": str(root / "pyc"),
                       "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                       "GIT_CONFIG_VALUE_0": str(root / "hooks"),
                       "GIT_CONFIG_PARAMETERS": "'core.hooksPath=x'", "GIT_DIR": str(root),
                       # D-117: this suite itself runs inside run_suite's
                       # environment under replay, so what run_suite must set
                       # is first given the caller's value and what it must add
                       # is first removed. Otherwise the assertions below pass
                       # on the inherited value: M107 survived on WSL2 at
                       # 2f86f14 with the PYTHONNOUSERSITE assertion passing.
                       "GIT_CONFIG_NOSYSTEM": "0", "GIT_ATTR_NOSYSTEM": "0",
                       "GIT_CONFIG_GLOBAL": str(root / "caller-gitconfig"),
                       "GIT_TEMPLATE_DIR": str(root / "caller-template"),
                       "XDG_CONFIG_HOME": str(root / "caller-xdg")}
            with mock.patch.dict(os.environ, hostile), \
                 mock.patch.object(harness.subprocess, "run", side_effect=capture):
                os.environ.pop("PYTHONNOUSERSITE", None)
                os.environ.pop("PYTHONSAFEPATH", None)
                harness.run_suite(("suite.py",), clone)

        self.assertEqual(str(private), captured["env"]["TMP"])
        self.assertEqual(str(private), captured["env"]["TEMP"])
        self.assertEqual(str(private), captured["env"]["TMPDIR"])
        self.assertIn(f"--basetemp={private / 'pytest'}", captured["command"])
        env = captured["env"]
        # M107, D-105: the contract is asserted here as well as observed. A
        # virtual environment disables the user site by itself, so on such a
        # host the behavioural probe cannot see the mutant; M107 survived on
        # WSL2 in a venv while the CI runner's Python caught it.
        self.assertEqual("1", env["PYTHONNOUSERSITE"])
        self.assertEqual("1", env["PYTHONSAFEPATH"])
        self.assertNotIn("PYTHONUSERBASE", env)
        # D-111: flags that change what a test means.
        for name in ("PYTHONWARNINGS", "PYTHONOPTIMIZE", "PYTHONPYCACHEPREFIX"):
            self.assertNotIn(name, env, name)
        # D-112: git reads only what this run wrote.
        for name in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0",
                     "GIT_CONFIG_PARAMETERS", "GIT_DIR"):
            self.assertNotIn(name, env, name)
        self.assertEqual("1", env["GIT_CONFIG_NOSYSTEM"])
        self.assertEqual("1", env["GIT_ATTR_NOSYSTEM"])
        # A run-owned path is asserted by its prefix under the run's private
        # root; a suffix would accept the caller's file of the same name.
        for name in ("GIT_CONFIG_GLOBAL", "GIT_TEMPLATE_DIR", "XDG_CONFIG_HOME"):
            self.assertTrue(env[name].startswith(str(private)),
                            f"{name} is not run-owned: {env[name]}")
        self.assertTrue(env["GIT_CONFIG_GLOBAL"].endswith("gitconfig"))
        self.assertTrue(env["GIT_TEMPLATE_DIR"].endswith("git-template"))
        self.assertTrue(env["XDG_CONFIG_HOME"].endswith("xdg"))

    def test_worker_suite_refuses_pytest_code_injected_from_outside_its_clone(self) -> None:
        """D-101. Rootdir alone does not contain PYTEST_ADDOPTS plugins."""
        harness = self._harness("adc_replay_parallel_external_plugin")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            coordinator = root / "coordinator"
            clone = root / "owned" / "worker-0"
            private = root / "owned" / "worker-0-pytest"
            marker = root / "outside-plugin-loaded.txt"
            coordinator.mkdir(parents=True)
            clone.mkdir(parents=True)
            private.mkdir(parents=True)
            (clone / "test_probe.py").write_text(
                "def test_inside_clone():\n    assert True\n", encoding="utf-8")
            plugin = clone / "design" / "routing" / "mutants" / "exact_nodeid_plugin.py"
            plugin.parent.mkdir(parents=True)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py", plugin)
            (coordinator / "external_adc_plugin.py").write_text(
                "import os, pathlib\n"
                "pathlib.Path(os.environ['ADC_R18_PLUGIN_MARKER']).write_text("
                "'loaded', encoding='utf-8')\n",
                encoding="utf-8")

            harness._WORKER_SUITE_CWD = coordinator
            harness._WORKER_TEMP_ROOT = private
            with mock.patch.dict(os.environ, {
                    "PYTEST_ADDOPTS": "-p external_adc_plugin",
                    "PYTEST_PLUGINS": "external_adc_plugin",
                    "PYTHONPATH": str(coordinator),
                    "ADC_R18_PLUGIN_MARKER": str(marker),
            }):
                code, summary, skipped = harness.run_suite(("test_probe.py",), clone)

            self.assertEqual(0, code)
            self.assertEqual(0, skipped)
            self.assertRegex(summary, r"^1 passed in ")
            self.assertFalse(marker.exists(),
                             "the worker imported a plugin outside its clone")

    def test_worker_suite_refuses_interpreter_and_config_injection_from_outside_its_clone(self) -> None:
        """D-105. D-101's boundary stopped at pytest; two layers sat beneath it.

        Measured before this held: PYTHONUSERBASE pointed the worker at a user
        site-packages whose usercustomize.py and .pth import line both ran
        inside the suite while it reported one passing test, and a pytest.ini
        at the common ancestor of the coordinator and the clone supplied
        addopts that the worker obeyed.
        """
        harness = self._harness("adc_replay_parallel_interpreter_injection")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            coordinator = root / "coordinator"
            clone = root / "owned" / "worker-0"
            private = root / "owned" / "worker-0-pytest"
            attacker = root / "attacker"
            for directory in (coordinator, clone, private, attacker):
                directory.mkdir(parents=True)
            (clone / "test_probe.py").write_text(
                "def test_inside_clone():\n    assert True\n", encoding="utf-8")
            plugin = clone / "design" / "routing" / "mutants" / "exact_nodeid_plugin.py"
            plugin.parent.mkdir(parents=True)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py", plugin)
            site_marker = root / "usercustomize-ran.txt"
            pth_marker = root / "pth-ran.txt"
            default_marker = root / "default-usercustomize-ran.txt"
            ini_marker = root / "ini-plugin-ran.txt"
            userbase = root / "userbase"
            import sysconfig
            scheme = "nt_user" if os.name == "nt" else "posix_user"
            user_site = Path(sysconfig.get_path("purelib", scheme=scheme,
                                                vars={"userbase": str(userbase)}))
            user_site.mkdir(parents=True)
            (user_site / "usercustomize.py").write_text(
                "import pathlib\n"
                f"pathlib.Path({str(site_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8")
            (user_site / "zz_probe.pth").write_text(
                "import pathlib; "
                f"pathlib.Path({str(pth_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8")
            # The interpreter's *default* user base, which no variable names:
            # %APPDATA%\Python on Windows and ~/.local elsewhere. Popping
            # PYTHONUSERBASE cannot reach this one; only disabling the user
            # site does. The profile is redirected into the fixture so the real
            # one is never touched.
            profile = root / "profile"
            default_base = (profile / "Python") if os.name == "nt" else (profile / ".local")
            default_site = Path(sysconfig.get_path("purelib", scheme=scheme,
                                                   vars={"userbase": str(default_base)}))
            default_site.mkdir(parents=True)
            (default_site / "usercustomize.py").write_text(
                "import pathlib\n"
                f"pathlib.Path({str(default_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8")
            (attacker / "external_adc_plugin.py").write_text(
                "import pathlib\n"
                f"pathlib.Path({str(ini_marker)!r}).write_text('ran', encoding='utf-8')\n",
                encoding="utf-8")
            (root / "pytest.ini").write_text(
                f"[pytest]\naddopts = -p external_adc_plugin\npythonpath = {attacker}\n",
                encoding="utf-8")

            harness._WORKER_SUITE_CWD = coordinator
            harness._WORKER_TEMP_ROOT = private
            redirected = {"PYTHONUSERBASE": str(userbase),
                          "APPDATA": str(profile), "HOME": str(profile)}
            with mock.patch.dict(os.environ, redirected):
                os.environ.pop("PYTHONNOUSERSITE", None)
                code, summary, skipped = harness.run_suite(("test_probe.py",), clone)

            self.assertEqual(0, code)
            self.assertEqual(0, skipped)
            self.assertRegex(summary, r"^1 passed in ")
            self.assertFalse(site_marker.exists(), "usercustomize.py ran inside the worker")
            self.assertFalse(pth_marker.exists(), "a .pth import line ran inside the worker")
            self.assertFalse(default_marker.exists(),
                             "the default user site's usercustomize.py ran inside the worker")
            self.assertFalse(ini_marker.exists(),
                             "a plugin named by an ancestor pytest.ini ran inside the worker")

    def test_worker_suite_refuses_interpreter_flags_and_git_configuration_from_outside_its_clone(self) -> None:
        """D-111 and D-112. Two more layers beneath D-105, measured through this path.

        An ambient PYTHONWARNINGS=error turned a passing probe into a failure,
        PYTHONOPTIMIZE=2 stripped an assertion, and a GIT_CONFIG_GLOBAL file
        carrying core.hooksPath ran a hook from outside the clone during a
        fixture-shaped commit. The last is how a host's git-lfs driver, not a
        test, decided M08's verdict on three hosts.
        """
        harness = self._harness("adc_replay_parallel_flags_and_git")
        warning_probe = ("import warnings\n\n"
                         "def test_probe():\n"
                         "    warnings.warn('x', DeprecationWarning)\n"
                         "    assert True\n")
        optimize_probe = "def test_probe():\n    assert __debug__\n"
        git_probe = (
            "import pathlib, subprocess, tempfile\n\n"
            "def test_probe():\n"
            "    repo = pathlib.Path(tempfile.mkdtemp())\n"
            "    for args in (['init', '-q', '-b', 'main'], ['config', 'user.email', 'f@x'],\n"
            "                 ['config', 'user.name', 'f']):\n"
            "        subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)\n"
            "    (repo / 'a.txt').write_text('a', encoding='utf-8')\n"
            "    subprocess.run(['git', '-C', str(repo), 'add', 'a.txt'], check=True, capture_output=True)\n"
            "    subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'one'], check=True, capture_output=True)\n")
        cases = (("warning filter", warning_probe, {"PYTHONWARNINGS": "error"}),
                 ("optimize strips assertions", optimize_probe, {"PYTHONOPTIMIZE": "2"}),
                 ("global git config names a hook", git_probe, None))
        for label, probe, extra in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_root:
                root = Path(raw_root)
                coordinator = root / "coordinator"
                clone = root / "owned" / "worker-0"
                private = root / "owned" / "worker-0-pytest"
                for directory in (coordinator, clone, private):
                    directory.mkdir(parents=True)
                (clone / "test_probe.py").write_text(probe, encoding="utf-8")
                plugin = clone / "design" / "routing" / "mutants" / "exact_nodeid_plugin.py"
                plugin.parent.mkdir(parents=True)
                shutil.copyfile(
                    REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py", plugin)
                marker = root / "hook-ran.txt"
                if extra is None:
                    hooks = root / "hooks"
                    hooks.mkdir()
                    hook = hooks / "pre-commit"
                    hook.write_text("#!/bin/sh\necho ran > \"" + marker.as_posix() + "\"\n",
                                    encoding="utf-8")
                    hook.chmod(0o755)
                    outside = root / "outside.gitconfig"
                    outside.write_text(f"[core]\n\thooksPath = {hooks.as_posix()}\n",
                                       encoding="utf-8")
                    extra = {"GIT_CONFIG_GLOBAL": str(outside)}

                harness._WORKER_SUITE_CWD = coordinator
                harness._WORKER_TEMP_ROOT = private
                with mock.patch.dict(os.environ, extra):
                    code, summary, skipped = harness.run_suite(("test_probe.py",), clone)

                self.assertEqual(0, code, summary)
                self.assertEqual(0, skipped)
                self.assertRegex(summary, r"^1 passed")
                self.assertFalse(marker.exists(),
                                 "a hook named by an outside git configuration ran inside the worker")

    def test_parallel_aggregates_out_of_order_futures_into_canonical_order_and_cleans(self) -> None:
        harness = self._harness("adc_replay_parallel_order")
        rows = [self._row("M1"), self._row("M2"), self._row("M3")]

        class Future:
            def __init__(self, value):
                self.value = value

            def result(self):
                return self.value

        futures = [
            Future([self._worker_result(rows[0], 0, "worker-0", self.SOURCE_DIGEST),
                    self._worker_result(rows[2], 2, "worker-0", self.SOURCE_DIGEST)]),
            Future([self._worker_result(rows[1], 1, "worker-1", self.SOURCE_DIGEST)]),
        ]

        class Pool:
            def __init__(self, max_workers):
                self.max_workers = max_workers

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return futures.pop(0)

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)

            def make_clone(source: Path, destination: Path, commit: str) -> None:
                destination.mkdir(parents=True)

            with mock.patch.object(harness, "prepare_clone", side_effect=make_clone), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(reversed(items))), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 2, root)

        self.assertEqual(["M1", "M2", "M3"], [row["id"] for row in result])
        self.assertEqual([0, 1, 2], [row["matrix_index"] for row in result])
        self.assertEqual(["worker-0", "worker-1"], [item["worker"] for item in cleanup])
        self.assertTrue(all(item["removed"] for item in cleanup))
        self.assertTrue(all(item["owned_root_removed"] for item in cleanup))
        self.assertTrue(all(not Path(item["clone"]).is_absolute() for item in cleanup))

    def test_parallel_removes_its_owned_root_when_pool_construction_fails(self) -> None:
        """A Windows worker-limit failure cannot strand the root made before it."""
        harness = self._harness("adc_replay_parallel_constructor_cleanup")
        rows = [self._row("M1")]
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            owned = root / "adc-replay-constructor"

            class FailingPool:
                def __init__(self, max_workers):
                    raise RuntimeError("Windows ProcessPoolExecutor worker limit")

            def make_root(**unused):
                owned.mkdir()
                return str(owned)

            with mock.patch.object(harness.tempfile, "mkdtemp", side_effect=make_root), \
                 mock.patch.object(harness, "ProcessPoolExecutor", FailingPool), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                try:
                    harness.run_parallel(rows, 62, root)
                except RuntimeError:
                    pass

            self.assertFalse(owned.exists(), "constructor failure stranded owned root")

    def test_parallel_cleans_every_prepared_clone_when_waiting_for_futures_fails(self) -> None:
        """Failure while waiting still reaches contained clone and root cleanup."""
        harness = self._harness("adc_replay_parallel_wait_cleanup")
        rows = [self._row("M1"), self._row("M2")]
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            owned = root / "adc-replay-wait"

            class Pool:
                def __init__(self, max_workers):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *unused):
                    return False

                def submit(self, *unused):
                    return object()

            def make_root(**unused):
                owned.mkdir()
                return str(owned)

            def make_clone(source, destination, commit):
                destination.mkdir(parents=True)
                (destination.parent / f"{destination.name}-pytest").mkdir()

            with mock.patch.object(harness.tempfile, "mkdtemp", side_effect=make_root), \
                 mock.patch.object(harness, "prepare_clone", side_effect=make_clone), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=RuntimeError("wait failed")), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                try:
                    harness.run_parallel(rows, 2, root)
                except RuntimeError:
                    pass

            self.assertFalse(owned.exists(), "wait failure stranded prepared clone/root")

    def test_parallel_preserves_keyboard_interrupt_after_contained_cleanup(self) -> None:
        harness = self._harness("adc_replay_parallel_interrupt_cleanup")
        rows = [self._row("M1")]
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            owned = root / "adc-replay-interrupt"

            class Pool:
                def __init__(self, max_workers):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *unused):
                    return False

                def submit(self, *unused):
                    return object()

            def make_root(**unused):
                owned.mkdir()
                return str(owned)

            with mock.patch.object(harness.tempfile, "mkdtemp", side_effect=make_root), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=KeyboardInterrupt), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                with self.assertRaises(KeyboardInterrupt):
                    harness.run_parallel(rows, 1, root)

            self.assertFalse(owned.exists(), "interrupt bypassed owned-root cleanup")

    def test_parallel_skips_empty_partitions_when_jobs_exceed_rows(self) -> None:
        harness = self._harness("adc_replay_parallel_nonempty_partitions")
        rows = [self._row("M1")]
        submitted: list[str] = []

        class Future:
            def result(self):
                return [ReplayParallelCloneTests._worker_result(
                    rows[0], 0, "worker-0", ReplayParallelCloneTests.SOURCE_DIGEST)]

        class Pool:
            def __init__(self, max_workers):
                self.max_workers = max_workers

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, function, clone, partition, worker):
                submitted.append(worker)
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 3, root)

        self.assertEqual(["worker-0"], submitted)
        self.assertEqual(["worker-0"], [item["worker"] for item in cleanup])
        self.assertEqual("worker-0", result[0]["worker"])

    def test_parallel_rejects_worker_output_with_wrong_commit_or_restoration_hash(self) -> None:
        harness = self._harness("adc_replay_parallel_untrusted_worker")
        rows = [self._row("M1")]

        class Future:
            def result(self):
                malformed = ReplayParallelCloneTests._worker_result(
                    rows[0], 0, "worker-0", ReplayParallelCloneTests.SOURCE_DIGEST,
                    commit="forged-commit")
                malformed["source_hash_after"] = "b" * 64
                return [malformed]

        class Pool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, _ = harness.run_parallel(rows, 1, root)

        self.assertEqual("inconclusive", result[0]["status"])
        self.assertIn("commit", result[0]["error"])

    def test_parallel_rejects_equal_forged_hashes_not_from_the_frozen_blob(self) -> None:
        """Equal worker hashes must still be the frozen source blob's digest."""
        harness = self._harness("adc_replay_parallel_forged_blob_hash")
        row = self._row("M1")
        commit: str | None = None

        class Future:
            def result(self):
                return [ReplayParallelCloneTests._worker_result(
                    row, 0, "worker-0", "a" * 64, commit=commit)]

        class Pool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            replay = root / "design" / "routing" / "mutants" / "replay.py"
            replay.parent.mkdir(parents=True)
            shutil.copyfile(REPO_ROOT / "design" / "routing" / "mutants" / "replay.py", replay)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py",
                replay.with_name("exact_nodeid_plugin.py"))
            matrix = replay.with_name("matrix.json")
            matrix.write_text(json.dumps([row]), encoding="utf-8")
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            self._git(root, "init", "-q", "-b", "main")
            self._git(root, "config", "user.email", "parallel@test.invalid")
            self._git(root, "config", "user.name", "Parallel Test")
            self._git(root, "config", "core.autocrlf", "false")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "fixture")
            commit = self._git(root, "rev-parse", "HEAD")
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.__file__ = str(replay)

            with mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)):
                result, _ = harness.run_parallel([row], 1, root)

        self.assertEqual("inconclusive", result[0]["status"])
        self.assertIn("frozen source digest", result[0]["error"])

    def test_frozen_row_source_hashes_cache_shared_frozen_blob_not_dirty_bytes(self) -> None:
        """Shared targets derive once from the commit, independent of working bytes."""
        harness = self._harness("adc_replay_parallel_frozen_source_hashes")
        with tempfile.TemporaryDirectory() as raw_root:
            source, commit = self._repository(Path(raw_root))
            expected = hashlib.sha256(subprocess.run(
                ["git", "cat-file", "blob", f"{commit}:source.py"], cwd=source,
                capture_output=True, check=True).stdout).hexdigest()
            (source / "source.py").write_text("before = dirty\n", encoding="utf-8")
            rows = [self._row("M1"), self._row("M2")]

            self.assertEqual(
                {Path("source.py"): expected},
                harness._frozen_row_source_hashes(source, commit, rows),
            )
            with self.assertRaisesRegex(RuntimeError, "committed blob could not be read"):
                harness._frozen_row_source_hashes(
                    source, commit, [{**self._row("MX"), "source": "missing.py"}])

    def test_parallel_refuses_missing_selected_source_before_starting_workers(self) -> None:
        """A selected row absent from frozen HEAD cannot reach a worker."""
        harness = self._harness("adc_replay_parallel_missing_selected_source")
        valid = self._row("M1")
        missing = {**self._row("MX"), "source": "missing.py"}
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            replay = root / "design" / "routing" / "mutants" / "replay.py"
            replay.parent.mkdir(parents=True)
            shutil.copyfile(REPO_ROOT / "design" / "routing" / "mutants" / "replay.py", replay)
            shutil.copyfile(
                REPO_ROOT / "design/routing/mutants/exact_nodeid_plugin.py",
                replay.with_name("exact_nodeid_plugin.py"))
            matrix = replay.with_name("matrix.json")
            matrix.write_text(json.dumps([valid]), encoding="utf-8")
            (root / "source.py").write_text("before = True\n", encoding="utf-8")
            self._git(root, "init", "-q", "-b", "main")
            self._git(root, "config", "user.email", "parallel@test.invalid")
            self._git(root, "config", "user.name", "Parallel Test")
            self._git(root, "config", "core.autocrlf", "false")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "fixture")
            harness.REPO_ROOT = root
            harness.MATRIX = matrix
            harness.__file__ = str(replay)

            with mock.patch.object(harness, "ProcessPoolExecutor") as pool:
                result, cleanup = harness.run_parallel([missing], 1, root)

        pool.assert_not_called()
        self.assertEqual([], cleanup)
        self.assertEqual("inconclusive", result[0]["status"])
        self.assertIn("committed blob could not be read", result[0]["error"])

    def test_worker_validator_surfaces_a_worker_rows_own_error(self) -> None:
        """D-099. An inconclusive row's reason must outlive the schema check."""
        harness = self._harness("adc_replay_parallel_validator_error")
        row = self._row("M1")
        broken = self._worker_result(row, 0, "worker-0", self.SOURCE_DIGEST)
        broken.update(status="inconclusive", verdict="INCONCLUSIVE", caught=None,
                      exit_code=None, pytest=None,
                      error="pytest exit 2: 1 error in 4.25s; output: ERROR collecting test session")
        self.assertEqual(
            "worker row inconclusive: pytest exit 2: 1 error in 4.25s; output: "
            "ERROR collecting test session",
            harness._validate_worker_result(
                broken, 0, row, "worker-0", "commit-test", self.SOURCE_DIGEST))
        # A completed row carrying an error is still a schema violation.
        completed = self._worker_result(row, 0, "worker-0", self.SOURCE_DIGEST)
        completed["error"] = "stray"
        self.assertEqual(
            "worker result schema does not match the required evidence fields",
            harness._validate_worker_result(
                completed, 0, row, "worker-0", "commit-test", self.SOURCE_DIGEST))

    def test_worker_validator_renders_control_characters_before_truncating(self) -> None:
        """D-102. A diagnostic cannot print a forged replay line."""
        harness = self._harness("adc_replay_parallel_validator_terminal_safety")
        payload = "useful\nFORGED\r\x1b[31m\u202e" + ("X" * 3000)
        surfaced = harness._validate_worker_result(
            {"status": "inconclusive", "error": payload}, 0, {"id": "M1"},
            "worker-0", "commit-test", self.SOURCE_DIGEST)
        prefix = "worker row inconclusive: "
        self.assertTrue(surfaced.startswith(prefix))
        rendered = surfaced[len(prefix):]
        self.assertEqual(2000, len(rendered))
        self.assertIn(r"\n", rendered)
        self.assertIn(r"\r", rendered)
        self.assertIn(r"\x1b", rendered)
        self.assertIn(r"\u202e", rendered)
        self.assertFalse(any(character in rendered for character in
                             ("\n", "\r", "\x1b", "\u202e")))

    def test_worker_validator_rejects_each_required_evidence_contract_break(self) -> None:
        """A worker payload is untrusted until every coordinator invariant holds."""
        harness = self._harness("adc_replay_parallel_validator")
        row = self._row("M1")
        cases = {
            "missing field": lambda item: item.pop("pytest"),
            "wrong worker": lambda item: item.update(worker="worker-9"),
            "wrong hash": lambda item: item.update(source_hash_after="b" * 64),
            "restoration false": lambda item: item.update(restored=False),
            "incompatible verdict": lambda item: item.update(verdict="SURVIVED"),
            "incompatible skips": lambda item: item.update(skipped=1),
            "invalid exit": lambda item: item.update(exit_code=2),
        }

        for label, mutate in cases.items():
            with self.subTest(label=label):
                item = self._worker_result(row, 0, "worker-0", self.SOURCE_DIGEST)
                mutate(item)
                self.assertIsNotNone(harness._validate_worker_result(
                    item, 0, row, "worker-0", "commit-test", self.SOURCE_DIGEST))

    def test_parallel_cleans_after_executor_shutdown_raises(self) -> None:
        """A shutdown exception cannot bypass clone, auxiliary, or root cleanup."""
        harness = self._harness("adc_replay_parallel_shutdown_cleanup")
        rows = [self._row("M1")]
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            owned = root / "adc-replay-shutdown"

            class Pool:
                def __init__(self, max_workers):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *unused):
                    raise RuntimeError("shutdown failed")

                def submit(self, *unused):
                    return object()

            def make_root(**unused):
                owned.mkdir()
                return str(owned)

            def make_clone(source, destination, commit):
                destination.mkdir(parents=True)
                (destination.parent / f"{destination.name}-pytest").mkdir()

            with mock.patch.object(harness.tempfile, "mkdtemp", side_effect=make_root), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "prepare_clone", side_effect=make_clone), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 1, root)

            self.assertFalse(owned.exists())
        self.assertEqual("inconclusive", result[0]["status"])
        self.assertIn("shutdown failed", result[0]["error"])
        self.assertTrue(cleanup[0]["removed"])
        self.assertTrue(cleanup[0]["auxiliary_removed"])
        self.assertTrue(cleanup[0]["owned_root_removed"])

    def test_parallel_marks_all_rows_inconclusive_when_head_changes_after_workers(self) -> None:
        harness = self._harness("adc_replay_parallel_head_drift")
        rows = [self._row("M1")]

        class Future:
            def result(self):
                return [ReplayParallelCloneTests._worker_result(
                    rows[0], 0, "worker-0", ReplayParallelCloneTests.SOURCE_DIGEST)]

        class Pool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            identities = iter(("commit-test", "changed-head"))
            with mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", side_effect=lambda repo: next(identities)):
                result, cleanup = harness.run_parallel(rows, 1, root)

        self.assertEqual("inconclusive", result[0]["status"])
        self.assertIn("HEAD changed", result[0]["error"])
        self.assertTrue(cleanup[0]["owned_root_removed"])

    def test_cleanup_rejects_root_home_workspace_and_unresolved_targets(self) -> None:
        harness = self._harness("adc_replay_parallel_cleanup_boundaries")
        with tempfile.TemporaryDirectory() as raw_root, \
             tempfile.TemporaryDirectory() as workspace_root:
            owned = Path(raw_root).resolve()
            clone = owned / "worker-0"
            clone.mkdir()
            workspace = Path(workspace_root).resolve()
            home = Path.home().resolve()

            records = [
                harness._cleanup_clone(owned, owned, "worker-root", workspace),
                harness._cleanup_clone(owned, home, "worker-home", workspace),
                harness._cleanup_clone(owned, workspace, "worker-workspace", workspace),
                harness._cleanup_clone(owned, owned / "missing", "worker-missing", workspace),
            ]
            safe = harness._cleanup_clone(owned, clone, "worker-0", workspace)

        self.assertTrue(all(not record["removed"] for record in records))
        self.assertTrue(all(record["error"] for record in records))
        self.assertTrue(safe["removed"])
        self.assertEqual("worker-0", safe["worker"])
        self.assertFalse(Path(safe["clone"]).is_absolute())

    def test_parallel_marks_worker_exception_and_duplicate_or_missing_rows_inconclusive(self) -> None:
        harness = self._harness("adc_replay_parallel_invalid_results")
        rows = [self._row("M1"), self._row("M2")]

        class Future:
            def result(self):
                raise RuntimeError("worker exploded")

        class Pool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 1, root)

        self.assertEqual(["M1", "M2"], [row["id"] for row in result])
        self.assertTrue(all(row["status"] == "inconclusive" for row in result))
        self.assertTrue(all("worker exception" in row["error"] for row in result))
        self.assertTrue(cleanup[0]["removed"])

    def test_parallel_waits_for_executor_shutdown_before_each_clone_cleanup(self) -> None:
        """Windows keeps a worker's clone cwd open after ``future.result()``."""
        harness = self._harness("adc_replay_parallel_cleanup_after_shutdown")
        rows = [self._row("M1"), self._row("M2")]
        pool_state = {"closed": False}

        class Future:
            def __init__(self, index: int, identifier: str):
                self.index = index
                self.identifier = identifier

            def result(self):
                return [ReplayParallelCloneTests._worker_result(
                    rows[self.index], self.index, f"worker-{self.index}",
                    ReplayParallelCloneTests.SOURCE_DIGEST)]

        class Pool:
            submitted = 0

            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                pool_state["closed"] = True
                return False

            def submit(self, *unused):
                index = Pool.submitted
                Pool.submitted += 1
                return Future(index, rows[index]["id"])

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)

            def cleanup_after_shutdown(owned: Path, clone: Path, worker: str,
                                       workspace: Path) -> dict:
                self.assertTrue(pool_state["closed"],
                                "cleanup ran before the executor joined workers")
                shutil.rmtree(clone)
                return {"worker": worker, "clone": clone.name,
                        "removed": True, "error": None}

            with mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "_cleanup_clone", side_effect=cleanup_after_shutdown), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 2, root)

        self.assertEqual(["M1", "M2"], [row["id"] for row in result])
        self.assertTrue(pool_state["closed"])
        self.assertTrue(all(record["removed"] for record in cleanup))

    def test_parallel_rejects_duplicate_and_missing_worker_indices(self) -> None:
        harness = self._harness("adc_replay_parallel_duplicate_results")
        rows = [self._row("M1"), self._row("M2")]

        class Future:
            def result(self):
                return [
                    {"id": "M1", "status": "completed", "verdict": "caught",
                     "restored": True, "worker": "worker-0", "matrix_index": 0},
                    {"id": "M1", "status": "completed", "verdict": "caught",
                     "restored": True, "worker": "worker-0", "matrix_index": 0},
                ]

        class Pool:
            def __init__(self, max_workers):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                return False

            def submit(self, *unused):
                return Future()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            with mock.patch.object(harness, "prepare_clone", side_effect=lambda s, d, c: d.mkdir(parents=True)), \
                 mock.patch.object(harness, "_verify_coordinator_sources"), \
                 mock.patch.object(harness, "_frozen_row_source_hashes", return_value={Path("source.py"): self.SOURCE_DIGEST}), \
                 mock.patch.object(harness, "ProcessPoolExecutor", Pool), \
                 mock.patch.object(harness, "as_completed", side_effect=lambda items: list(items)), \
                 mock.patch.object(harness, "commit_identity", return_value="commit-test"):
                result, cleanup = harness.run_parallel(rows, 1, root)

        self.assertTrue(all(row["status"] == "inconclusive" for row in result))
        self.assertIn("duplicate", result[0]["error"])
        self.assertIn("duplicate", result[1]["error"])
        self.assertTrue(cleanup[0]["removed"])

    def test_parallel_write_fails_closed_before_workers_or_matrix_rewrite(self) -> None:
        harness = self._harness("adc_replay_parallel_write_closed")
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            matrix = root / "matrix.json"
            matrix.write_text(json.dumps([self._row("M1")]), encoding="utf-8")
            harness.MATRIX = matrix
            with mock.patch.object(harness, "run_parallel") as run_parallel:
                self.assertEqual(2, harness.main(["M1", "--jobs", "2", "--write"]))

        run_parallel.assert_not_called()

INSTALLED_CALIBRATION = (REPO_ROOT / ".agents" / "skills" / "anti-dark-code"
                         / "calibration")


class CanonicalFullTests(unittest.TestCase):
    def test_level_may_raise_the_route_minimum(self) -> None:
        # Accepting the lower request, or defaulting an absent request to zero,
        # would let the command run less verification than the receipt requires.
        check = getattr(load_adc(), "check_route_level", None)
        self.assertIsNotNone(check, "adc.py has no route-level guard")
        self.assertEqual((True, 2), check(2, None))
        self.assertEqual((True, 3), check(2, 3))
        self.assertEqual((False, 2), check(2, 1))

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_force_full_runs_the_canonical_set_despite_include_globs(self) -> None:
        # Applying changed-file globs before honoring force_full removes every
        # canonical gate in this fixture; selecting every enabled gate adds the
        # noncanonical counterexample instead.
        with tempfile.TemporaryDirectory() as raw_root:
            repo = Path(raw_root) / "repo"
            repo.mkdir()

            def git(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["git", "-C", str(repo), *args], capture_output=True,
                    text=True, timeout=60, check=True)

            git("init", "-q", "-b", "main", ".")
            git("config", "user.email", "t@example.invalid")
            git("config", "user.name", "Test")
            (repo / "src.py").write_text("one\n", encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "one")
            (repo / "src.py").write_text("two\n", encoding="utf-8")

            calibration = repo / ".anti-dark-code" / "calibration"
            calibration.mkdir(parents=True)
            policy_path = (SKILL_ROOT / "assets" / "templates" /
                           "calibration" / "routing-policy.json")
            shutil.copyfile(policy_path, calibration / "routing-policy.json")
            canonical_ids = (
                "validate-core", "full-suite", "distribution",
                "hostile-environment", "mutation-replay")
            gates = {
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
                    {"id": gate_id, "enabled": True,
                     "review_status": "approved", "level": 0,
                     "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                     "timeout_seconds": 30, "include_globs": ["docs/**"]}
                    for gate_id in (*canonical_ids, "extra-enabled")
                ],
            }
            (calibration / "gates.json").write_text(
                json.dumps(gates, indent=2) + "\n", encoding="utf-8")
            adc = load_adc()
            assessment = adc.assess_repository_binding(repo, calibration)
            adc.write_repository_binding(
                calibration, assessment,
                accepted_unbound=assessment["status"] == "unbound")

            routed = subprocess.run(
                [sys.executable, "-B", str(SKILL_ROOT / "scripts" / "adc.py"),
                 "route", "--repo", str(repo), "--calibration",
                 str(calibration), "--base", "HEAD", "--write"],
                capture_output=True, text=True, timeout=300)
            self.assertEqual(0, routed.returncode, routed.stdout + routed.stderr)
            receipts = sorted((repo / ".anti-dark-code" / "runs").glob("*.json"))
            self.assertEqual(1, len(receipts), routed.stdout)

            planned = subprocess.run(
                [sys.executable, "-B", str(SKILL_ROOT / "scripts" / "adc.py"),
                 "gates", "--repo", str(repo), "--route", str(receipts[0]),
                 "--changed-from", "HEAD"],
                capture_output=True, text=True, timeout=300)
            self.assertEqual(0, planned.returncode, planned.stdout + planned.stderr)
            self.assertIn("GATE PLAN: 5 approved gate(s)", planned.stdout)
            self.assertIn("Level <= 3", planned.stdout)
            for gate_id in canonical_ids:
                self.assertIn(gate_id, planned.stdout)
            self.assertNotIn("extra-enabled", planned.stdout)


class CandidateRouteTests(unittest.TestCase):
    """Proposed rules produce measurements, never execution authority."""

    def setUp(self) -> None:
        self.route = load_route()
        source = json.loads(json.dumps(POLICY))
        source["rules"][0]["review_status"] = "proposed"
        self.policy = self.route.load_policy(
            source, GATES, CAPABILITY_IDS, FULL_SET)
        self.candidate = self.route.build_candidate_route(
            (fact(self.route, "README.md"),), self.policy,
            snapshot_ok=True)

    def test_proposed_rules_build_a_separate_candidate_type(self) -> None:
        self.assertIsInstance(self.candidate, self.route.CandidateRoute)
        self.assertNotIsInstance(self.candidate, self.route.Route)
        self.assertEqual("candidate-shadow", self.candidate.provenance)
        self.assertEqual(frozenset({"docs"}),
                         self.candidate.considered_rule_ids)
        self.assertEqual(("validate-core",),
                         self.candidate.selected_gate_ids())

    def test_an_incomplete_snapshot_has_no_candidate_route(self) -> None:
        self.assertIsNone(self.route.build_candidate_route(
            (fact(self.route, "README.md"),), self.policy,
            snapshot_ok=False))

    def test_a_candidate_route_is_refused_by_the_receipt_writer(self) -> None:
        receipt = load_module(
            "candidate_receipt",
            SKILL_ROOT / "scripts" / "adc_receipt.py")
        snapshot = self.route.ChangeSnapshot(base="HEAD", base_resolved=True)
        with self.assertRaises(receipt.ReceiptError):
            receipt.authoritative_payload(
                self.candidate, (), snapshot, receipt.Binding(), GATES)
        with self.assertRaises(receipt.ReceiptError):
            receipt.build_receipt(self.candidate)
        with self.assertRaises(receipt.ReceiptError):
            receipt.authoritative_payload(
                self.candidate.as_payload(), (), snapshot,
                receipt.Binding(), GATES)
        with self.assertRaises(receipt.ReceiptError):
            receipt.build_receipt(self.candidate.as_payload())

    def test_a_candidate_selection_cannot_remove_a_gate(self) -> None:
        adc = load_adc()
        with self.assertRaises(TypeError):
            adc.select_route_gates(
                GATES, GATES["gates"], self.candidate,
                level=3, force_full=False)

    def test_a_serialized_candidate_cannot_select_executable_gates(self) -> None:
        adc = load_adc()
        with self.assertRaises(TypeError):
            adc.select_route_gates(
                GATES, GATES["gates"], self.candidate.as_payload(),
                level=3, force_full=False)

    def test_an_unrecognised_outcome_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_adc().shadow_result(
                {"route": {"selected_gate_ids": ["validate-core"]}},
                self.candidate, {"validate-core": "maybe"})

    def test_an_aborted_run_is_not_a_clean_targeted_verification(self) -> None:
        result = load_adc().shadow_result(
            {"route": {"selected_gate_ids": ["validate-core", "full-suite"]}},
            self.candidate,
            {"validate-core": "not-run", "full-suite": "fail"})
        self.assertFalse(result["selected_all_passed"])
        self.assertFalse(result["routing_miss"])

    def test_a_candidate_omitting_a_failing_gate_is_a_routing_miss(self) -> None:
        result = load_adc().shadow_result(
            {"route": {"selected_gate_ids": ["validate-core", "full-suite"]}},
            self.candidate,
            {"validate-core": "pass", "full-suite": "fail"})
        self.assertTrue(result["selected_all_passed"])
        self.assertEqual(["full-suite"], result["missed_gate_ids"])
        self.assertTrue(result["routing_miss"])


@unittest.skipUnless(shutil.which("git"), "git is required")
class GateLifecycleTests(unittest.TestCase):
    """R-018 against a real repository and the real gate subprocess loop."""

    def setUp(self) -> None:
        self.adc = load_adc()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main", ".")
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        (self.repo / "tracked.txt").write_text("before\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "fixture")

        self.calibration = self.repo / ".anti-dark-code" / "calibration"
        self.calibration.mkdir(parents=True)
        self.writer = {
            "id": "writes-during-run", "level": 3, "enabled": True,
            "review_status": "approved", "cwd": ".", "timeout_seconds": 30,
            "argv": [
                sys.executable, "-c",
                "from pathlib import Path; "
                "Path('tracked.txt').write_text('during\\n', encoding='utf-8')",
            ],
        }
        self.stable = {
            "id": "changes-nothing", "level": 3, "enabled": True,
            "review_status": "approved", "cwd": ".", "timeout_seconds": 30,
            "argv": [sys.executable, "-c", "raise SystemExit(0)"],
        }
        self._write_gates([self.writer, self.stable])

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], capture_output=True,
            text=True, timeout=60, check=True)

    def _write_gates(self, gates: list[dict[str, object]]) -> None:
        (self.calibration / "gates.json").write_text(json.dumps({
            "schema_version": 1,
            "execution_policy": {"owner_confirmed_safe_to_execute": True},
            "gates": gates,
        }, indent=2) + "\n", encoding="utf-8")
        assessment = self.adc.assess_repository_binding(
            self.repo, self.calibration)
        self.adc.write_repository_binding(
            self.calibration, assessment,
            accepted_unbound=assessment["status"] == "unbound",
            rebound=assessment["status"] == "mismatch")

    def _summary(self) -> dict[str, object]:
        summaries = sorted(
            (self.repo / ".anti-dark-code" / "runs").glob("*/summary.json"))
        self.assertEqual(1, len(summaries))
        return json.loads(summaries[0].read_text(encoding="utf-8"))

    def test_a_mutation_during_a_gate_marks_that_gate_stale(self) -> None:
        code = self.adc.run_gates(
            self.repo, level=3, allow_exec=True,
            changed_from=None, keep_going=False)
        summary = self._summary()
        stale = {row["gate_id"] for row in summary["stale"]}
        self.assertIn("writes-during-run", stale)
        self.assertNotEqual(summary["stale"][0]["identity_before"],
                            summary["stale"][0]["identity_after"])
        self.assertEqual(2, code)

    def test_a_gate_that_restores_what_it_changed_is_still_stale(self) -> None:
        # R-018 says an input changing *during a gate* stales that gate. A gate
        # that writes a tracked file, uses the changed value, and puts the
        # original back satisfies that antecedent while leaving the bound
        # identity equal at both ends. Before D-077 this passed with exit 0 and
        # no stale row, and the gate's own log recorded that it had read the
        # changed content.
        reverting = {
            "id": "writes-then-reverts", "level": 3, "enabled": True,
            "review_status": "approved", "cwd": ".", "timeout_seconds": 30,
            "argv": [
                sys.executable, "-c",
                "from pathlib import Path;"
                "p = Path('tracked.txt');"
                "original = p.read_text(encoding='utf-8');"
                "p.write_text('during\\n', encoding='utf-8');"
                "p.read_text(encoding='utf-8');"
                "p.write_text(original, encoding='utf-8')",
            ],
        }
        self._write_gates([reverting])
        code = self.adc.run_gates(
            self.repo, level=3, allow_exec=True,
            changed_from=None, keep_going=False)
        summary = self._summary()
        self.assertEqual(2, code)
        self.assertEqual("stale", summary["outcomes"]["writes-then-reverts"])
        row = summary["stale"][0]
        # The bound identity is equal at both ends, which is exactly why the
        # lifecycle identity has to exist. If this assertion ever fails the
        # test has stopped proving what it was written for.
        self.assertEqual(row["identity_before"], row["identity_after"])
        self.assertNotEqual(row["lifecycle_before"], row["lifecycle_after"])
        self.assertTrue(row["restored_during_gate"])
        self.assertEqual(
            "before\n",
            (self.repo / "tracked.txt").read_text(encoding="utf-8"))

    def test_a_gate_that_changes_nothing_is_not_marked_stale(self) -> None:
        self._write_gates([self.stable])
        code = self.adc.run_gates(
            self.repo, level=3, allow_exec=True,
            changed_from=None, keep_going=False)
        summary = self._summary()
        self.assertEqual([], summary["stale"])
        self.assertEqual(1, summary["passed"])
        self.assertEqual(0, code)

    def test_a_stale_gate_result_cannot_satisfy_an_obligation(self) -> None:
        self.assertFalse(self.adc.obligations_are_covered(
            {"V21": {"full-suite"}},
            approved_gate_ids={"full-suite"},
            outcomes={"full-suite": "stale"}))

    def test_an_empty_obligation_map_is_not_covered(self) -> None:
        self.assertFalse(self.adc.obligations_are_covered(
            {}, approved_gate_ids={"full-suite"}, outcomes={}))

    def test_the_run_stops_when_the_tree_moves_even_with_keep_going(self) -> None:
        code = self.adc.run_gates(
            self.repo, level=3, allow_exec=True,
            changed_from=None, keep_going=True)
        summary = self._summary()
        self.assertEqual(2, code)
        self.assertLess(summary["passed"] + len(summary["failures"]),
                        summary["planned"])

    def test_a_change_after_preflight_refuses_before_gate_launch(self) -> None:
        route = load_route()
        receipt = load_module(
            "prelaunch_identity_receipt",
            SKILL_ROOT / "scripts" / "adc_receipt.py")
        expected = receipt.worktree_identity(self.repo, route)
        (self.repo / "tracked.txt").write_text(
            "after preflight\n", encoding="utf-8")

        code = self.adc.run_gates(
            self.repo, level=3, allow_exec=True,
            changed_from=None, keep_going=False,
            expected_worktree_identity=expected,
            verified_receipt_run_id="verified-run")

        summary = self._summary()
        self.assertEqual(2, code)
        self.assertEqual("stale", summary["outcomes"]["writes-during-run"])
        self.assertEqual("before-launch", summary["stale"][0]["phase"])
        self.assertEqual("after preflight\n",
                         (self.repo / "tracked.txt").read_text(encoding="utf-8"))
        self.assertEqual("verified-run", summary["verified_receipt_run_id"])


class SelfGradingAuthorityTests(unittest.TestCase):
    """R-005 and R-021 against the installed policy, with the rules approved.

    Approving the rules in memory is the whole point. D-064 ships every rule
    proposed, so an unapproved policy forces the full recipe on everything and
    every one of these assertions would pass without the classifier saying
    anything about authority at all. That is the reading that let the router
    grade a change to itself as Level 2 product code. See D-071.
    """

    def setUp(self) -> None:
        self.route = load_route()
        self.policy_source = json.loads(
            (INSTALLED_CALIBRATION / "routing-policy.json").read_text(
                encoding="utf-8"))
        self.gates_source = json.loads(
            (INSTALLED_CALIBRATION / "gates.json").read_text(encoding="utf-8"))

    def _approved_policy(self):
        data = json.loads(json.dumps(self.policy_source))
        for rule in data["rules"]:
            rule["review_status"] = "approved"
        return self.route.load_policy(
            data, self.gates_source, sorted(CAPABILITY_IDS),
            self.gates_source["canonical_full_set"])

    def _route_for(self, path: str, policy):
        snapshot = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(
                path=path, change_kind="modify", source="unstaged"),),
            base="HEAD", base_resolved=True, problems=())
        facts = self.route.collect_change_facts(snapshot, policy.classifier_map())
        return self.route.build_route(facts, policy, snapshot_ok=True)

    def test_authority_classes_cannot_be_demoted_by_exact_exceptions(self) -> None:
        """D-093: a representative path cannot stand for an authority class."""
        for path, authority_glob in (
            ("design/routing/mutants/replay.py",
             "design/routing/mutants/*"),
            (".gitattributes", ".gitattributes"),
            (".gitignore", ".gitignore"),
            ("anti-dark-code/SOURCE-SCOPE.json",
             "anti-dark-code/SOURCE-SCOPE.json"),
            ("design/routing/mutants/matrix.json",
             "design/routing/mutants/*"),
        ):
            with self.subTest(path=path):
                data = json.loads(json.dumps(self.policy_source))
                data["classifier"]["surfaces"] = [
                    entry for entry in data["classifier"]["surfaces"]
                    if entry.get("glob") != authority_glob]
                data["classifier"]["surfaces"].append({
                    "glob": path, "surface": "docs", "effect": "prose",
                    "breadth": "leaf",
                })
                with self.assertRaises(self.route.PolicyError) as caught:
                    self.route.load_policy(
                        data, self.gates_source, sorted(CAPABILITY_IDS),
                        self.gates_source["canonical_full_set"])
                self.assertIn(authority_glob, str(caught.exception))

    def test_workflow_authority_cannot_be_split_to_one_exact_path(self) -> None:
        data = json.loads(json.dumps(self.policy_source))
        surfaces = []
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") == ".github/workflows/**":
                exact = dict(entry)
                exact["glob"] = ".github/workflows/tests.yml"
                surfaces.append(exact)
            else:
                surfaces.append(entry)
        surfaces.append({"glob": ".github/workflows/**", "surface": "docs",
                         "effect": "prose", "breadth": "leaf"})
        data["classifier"]["surfaces"] = surfaces
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn(".github/workflows/**", str(caught.exception))

    def test_a_public_contract_surface_cannot_disable_class_enforcement(self) -> None:
        # SKILL.md has instruction authority through its surface rather than
        # the verification-authority effect.  Dropping all of the latter must
        # not switch off D-093 and make another class cheaply exact.
        data = json.loads(json.dumps(self.policy_source))
        data["classifier"]["surfaces"] = [
            entry for entry in data["classifier"]["surfaces"]
            if entry.get("effect") != "verification-authority"
        ]
        data["classifier"]["surfaces"].append({
            "glob": "anti-dark-code/SOURCE-SCOPE.json", "surface": "docs",
            "effect": "prose", "breadth": "leaf",
        })
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("source scope marker", str(caught.exception))

    def test_an_all_cheap_classifier_cannot_disable_class_enforcement(self) -> None:
        # D-093 must not rely on the attacker retaining any authority-labelled
        # entry.  Before this regression, removing them all and leaving this
        # one exact classifier loaded and routed .gitattributes at Level 0.
        data = json.loads(json.dumps(self.policy_source))
        data["classifier"]["surfaces"] = [{
            "glob": ".gitattributes", "surface": "docs", "effect": "prose",
            "breadth": "leaf",
        }]
        for rule in data["rules"]:
            rule["review_status"] = "approved"
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("attributes (.gitattributes)", str(caught.exception))

    def test_shipped_policy_matches_the_canonical_authority_class_contract(self) -> None:
        expected = (
            ("shipped script controls, source", "anti-dark-code/scripts/*.py",
             "product", "verification-authority", "repository", "normal"),
            ("shipped script controls, installed",
             "**/anti-dark-code/scripts/*.py",
             "product", "verification-authority", "repository", "normal"),
            ("tests and shared fixtures", "**/tests/*.py", "tests",
             "verification-authority", "repository", "normal"),
            ("capability catalog", "**/assets/verification-capabilities.json",
             "schema", "verification-authority", "repository", "normal"),
            ("source scope marker", "anti-dark-code/SOURCE-SCOPE.json",
             "schema", "verification-authority", "repository", "normal"),
            ("calibration", "**/calibration/*.json", "schema",
             "verification-authority", "repository", "normal"),
            ("skill instructions", "**/SKILL.md", "skill-policy",
             "public-contract", "repository", "normal"),
            ("routing pass references", "**/references/*.md", "docs",
             "verification-authority", "repository", "normal"),
            ("workflow class", ".github/workflows/**", "ci",
             "verification-authority", "repository", "release"),
            ("code owners", ".github/CODEOWNERS", "ci",
             "verification-authority", "repository", "release"),
            ("attributes", ".gitattributes", "schema",
             "verification-authority", "repository", "normal"),
            ("ignore policy", ".gitignore", "schema",
             "verification-authority", "repository", "normal"),
            ("submodule policy", ".gitmodules", "schema",
             "verification-authority", "repository", "normal"),
            ("mutation and validator harnesses", "design/routing/mutants/*",
             "tests", "verification-authority", "repository", "normal"),
            ("Python project manifest", "pyproject.toml", "schema",
             "verification-authority", "repository", "normal"),
            ("nested Python project manifest", "**/pyproject.toml", "schema",
             "verification-authority", "repository", "normal"),
            ("Python requirements family", "requirements*.txt", "schema",
             "verification-authority", "repository", "normal"),
            ("nested Python requirements family", "**/requirements*.txt", "schema",
             "verification-authority", "repository", "normal"),
            ("Pipfile", "Pipfile", "schema", "verification-authority",
             "repository", "normal"),
            ("nested Pipfile", "**/Pipfile", "schema",
             "verification-authority", "repository", "normal"),
            ("Python lock family", "*.lock", "schema",
             "verification-authority", "repository", "normal"),
            ("nested Python lock family", "**/*.lock", "schema",
             "verification-authority", "repository", "normal"),
            ("setup.py", "setup.py", "schema",
             "verification-authority", "repository", "normal"),
            ("nested setup.py", "**/setup.py", "schema",
             "verification-authority", "repository", "normal"),
            ("setup.cfg", "setup.cfg", "schema", "verification-authority",
             "repository", "normal"),
            ("nested setup.cfg", "**/setup.cfg", "schema",
             "verification-authority", "repository", "normal"),
            ("pytest.ini", "pytest.ini", "schema", "verification-authority",
             "repository", "normal"),
            ("nested pytest.ini", "**/pytest.ini", "schema",
             "verification-authority", "repository", "normal"),
            ("tox.ini", "tox.ini", "schema", "verification-authority",
             "repository", "normal"),
            ("nested tox.ini", "**/tox.ini", "schema",
             "verification-authority", "repository", "normal"),
        )
        self.assertEqual(expected,
                         getattr(self.route, "AUTHORITY_CLASSIFIERS", ()))
        expected_entries = {
            (glob, surface, effect, breadth, sensitivity)
            for _, glob, surface, effect, breadth, sensitivity in expected
        }
        for policy_source in (self.policy_source, json.loads(
                (SKILL_ROOT / "assets/templates/calibration/routing-policy.json")
                .read_text(encoding="utf-8"))):
            actual = {
                (entry.get("glob"), entry.get("surface"), entry.get("effect"),
                 entry.get("breadth", "leaf"), entry.get("sensitivity", "normal"))
                for entry in policy_source["classifier"]["surfaces"]
            }
            self.assertTrue(expected_entries <= actual,
                            sorted(expected_entries - actual))

    def test_every_self_grading_path_class_forces_the_full_recipe(self) -> None:
        policy = self._approved_policy()
        demoted = []
        for label, path in self.route.SELF_GRADING_PATHS:
            route = self._route_for(path, policy)
            if not route.force_full:
                demoted.append(f"{label} ({path}) routed at level "
                               f"{route.minimum_level} without force_full")
        self.assertEqual([], demoted, "; ".join(demoted))

    def test_each_named_self_grading_path_exists(self) -> None:
        # A path that has moved would pass the test above by never matching a
        # cheap rule, which is the accidental pass this contract replaces.
        missing = [f"{label}: {path}"
                   for label, path in self.route.SELF_GRADING_PATHS
                   if not (REPO_ROOT / path).exists()]
        self.assertEqual([], missing, "; ".join(missing))

    def test_an_ordinary_documentation_path_does_not_force_full(self) -> None:
        # The counterexample. Without it, a policy that forced full on
        # everything would satisfy the test above and prove nothing.
        route = self._route_for("design/routing/ARCHITECTURE.md",
                                self._approved_policy())
        self.assertFalse(route.force_full)
        self.assertEqual(0, route.minimum_level)

    def test_the_installed_policy_loads(self) -> None:
        self.route.load_policy(
            json.loads(json.dumps(self.policy_source)), self.gates_source,
            sorted(CAPABILITY_IDS), self.gates_source["canonical_full_set"])

    def test_a_policy_grading_the_router_as_product_code_is_refused(self) -> None:
        data = json.loads(json.dumps(self.policy_source))
        data["classifier"]["surfaces"] = [
            entry for entry in data["classifier"]["surfaces"]
            if entry.get("effect") != "verification-authority"
            or entry.get("glob") == "**/tests/*.py"]
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        # The label, not the bare glob: the source glob is a substring of the
        # installed one, so the bare glob could not tell the halves apart.
        message = str(caught.exception)
        self.assertIn("shipped script controls, source (anti-dark-code/scripts/*.py)", message)
        self.assertIn("shipped script controls, installed (**/anti-dark-code/scripts/*.py)", message)

    def test_one_authority_reference_cannot_cover_two_cheap_ones(self) -> None:
        data = json.loads(json.dumps(self.policy_source))
        surfaces = []
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") == "**/references/*.md":
                exact = dict(entry)
                exact["glob"] = "anti-dark-code/references/00-preflight.md"
                surfaces.append(exact)
            else:
                surfaces.append(entry)
        surfaces.append({"glob": "**/references/*.md", "surface": "docs",
                         "effect": "prose", "breadth": "leaf"})
        data["classifier"]["surfaces"] = surfaces
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("**/references/*.md", str(caught.exception))

    def test_source_only_authority_cannot_hide_the_installed_router(self) -> None:
        # D-071 portability. The managed installer moves this module beneath
        # .agents/skills. A policy that recognizes only the source-tree
        # spelling must not pass the guard while its broad product glob grades
        # the installed router as ordinary code.
        data = json.loads(json.dumps(self.policy_source))
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") in ("anti-dark-code/scripts/*.py",
                                     "**/anti-dark-code/scripts/*.py"):
                entry["glob"] = "anti-dark-code/scripts/adc_route.py"
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("**/anti-dark-code/scripts/*.py", str(caught.exception))

    def test_installed_only_authority_cannot_hide_the_source_router(self) -> None:
        # D-118, the twin of the test above for the source half. The
        # round-twenty-one challenger found a mutant that stopped the contract
        # requiring the source entry surviving the whole suite: with only the
        # installed entry required, the D-093 exact-representative policy
        # loaded and routed work_receipt.py and adc_efficiency.py as Level 2.
        data = json.loads(json.dumps(self.policy_source))
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") == "anti-dark-code/scripts/*.py":
                entry["glob"] = "anti-dark-code/scripts/adc_route.py"
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("shipped script controls, source (anti-dark-code/scripts/*.py)",
                      str(caught.exception))

    def test_a_cheap_rule_that_fires_on_authority_is_refused(self) -> None:
        # The classifier is untouched here, so a guard that checked only the
        # classification passed this policy. Measured against it: ten of the
        # eleven classes stopped forcing full, because build_route sets `fired`
        # on any match and the unrouted fallback never ran. See D-071.
        data = json.loads(json.dumps(self.policy_source))
        data["rules"] = [rule for rule in data["rules"]
                         if rule["id"] != "verification-authority"]
        data["rules"].append({
            "id": "authority-is-cheap-actually",
            "review_status": "approved",
            "match": {"effects": ["verification-authority"]},
            "requires": {"passes": ["06"], "minimum_level": 0},
            "obligations": {"V09": ["validate-core"]},
        })
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("adc_route.py", str(caught.exception))

    def test_a_proposed_cheap_authority_rule_is_refused_too(self) -> None:
        # A proposed rule never matches today, so nothing is unsafe yet. It is
        # still refused: approval is one review away, and load is the last
        # moment where saying no is cheap.
        data = json.loads(json.dumps(self.policy_source))
        data["rules"] = [rule for rule in data["rules"]
                         if rule["id"] != "verification-authority"]
        data["rules"].append({
            "id": "authority-is-cheap-later",
            "review_status": "proposed",
            "match": {"effects": ["verification-authority"]},
            "requires": {"passes": ["06"], "minimum_level": 0},
            "obligations": {"V09": ["validate-core"]},
        })
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])

    def test_a_rule_narrowed_to_the_probe_shape_is_refused(self) -> None:
        # D-078. The guard used to build one fact per classification with
        # change_kind "modify" and source "unstaged". A rule narrowed to that
        # shape satisfied it while a cheap rule took every other shape.
        # Measured before the fix: this policy loaded, and deleting
        # anti-dark-code/tests/test_route.py routed at Level 0.
        data = json.loads(json.dumps(self.policy_source))
        for rule in data["rules"]:
            if rule["id"] == "verification-authority":
                rule["match"]["change_kinds"] = ["modify"]
        data["rules"].append({
            "id": "authority-deletions-are-cheap",
            "review_status": "approved",
            "match": {"effects": ["verification-authority"],
                      "change_kinds": ["delete", "add", "rename"]},
            "requires": {"passes": ["06"], "minimum_level": 0},
            "obligations": {"V09": ["validate-core"]},
        })
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        message = str(caught.exception)
        self.assertIn("test_route.py", message)
        # The message has to name a concrete shape, or a reader cannot act on
        # it. Which shape is reported first is sorted order, not significance,
        # so this checks that one is named rather than which one.
        self.assertRegex(
            message, r"a \w[\w-]* from \w+ with mode_changed=(true|false)")

    def test_a_rule_narrowed_to_one_source_is_refused(self) -> None:
        # The same hole through a different dimension. `sources` and
        # `mode_changed` are match keys too, so covering only change_kinds
        # would leave the class open.
        data = json.loads(json.dumps(self.policy_source))
        for rule in data["rules"]:
            if rule["id"] == "verification-authority":
                rule["match"]["sources"] = ["unstaged"]
        data["rules"].append({
            "id": "committed-authority-is-cheap",
            "review_status": "approved",
            "match": {"effects": ["verification-authority"],
                      "sources": ["committed", "staged", "untracked"]},
            "requires": {"passes": ["06"], "minimum_level": 0},
            "obligations": {"V09": ["validate-core"]},
        })
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])

    def test_every_shape_of_a_self_grading_change_forces_full(self) -> None:
        # The positive form, against the shipped policy with every rule
        # approved: no combination of change kind, source, and mode flag routes
        # a self-grading path below the full recipe.
        policy = self._approved_policy()
        escaped = []
        for _, path in self.route.SELF_GRADING_PATHS:
            for kind in sorted(self.route.CHANGE_KINDS):
                for source in sorted(self.route.CHANGE_SOURCES):
                    snapshot = self.route.ChangeSnapshot(
                        inputs=(self.route.ChangeInput(
                            path=path, change_kind=kind, source=source),),
                        base="HEAD", base_resolved=True, problems=())
                    facts = self.route.collect_change_facts(
                        snapshot, policy.classifier_map())
                    route = self.route.build_route(facts, policy, snapshot_ok=True)
                    if not route.force_full:
                        escaped.append(f"{path} as {kind}/{source}")
        self.assertEqual([], escaped, "; ".join(escaped[:8]))

    def test_the_guard_covers_every_installer_prefix(self) -> None:
        # D-086. The guard's prefix list is a copy of the installer's, and a
        # copy drifts. This is what makes the drift fail rather than quietly
        # leave a layout unprobed: the installer wrote instruction authority to
        # .claude/skills/anti-dark-code/SKILL.md while the guard probed only
        # .agents/skills/.
        adc = load_adc()
        installer = {"/".join(prefix) + "/"
                     for prefix in adc.HOST_SKILL_TREE_PREFIXES}
        guard = set(self.route.INSTALLED_SKILL_PREFIXES)
        self.assertEqual(
            installer, guard,
            "the self-grading guard and the installer disagree about where a "
            "skill tree can live")

    def test_every_calibration_root_is_probed(self) -> None:
        # D-089. Calibration moves for a different reason than the skill tree:
        # adc.calibration_dir() falls back to .anti-dark-code/calibration when
        # no managed install exists, which is the common case. D-086 derived
        # only skill-tree spellings, and the two calibration entries already
        # carried one, so they gained nothing.
        probed = {path for _, path in self.route._self_grading_guard_paths()}
        for root in self.route.CALIBRATION_ROOTS:
            for leaf in ("gates.json", "routing-policy.json"):
                self.assertIn(f"{root}{leaf}", probed)
        self.assertIn(".anti-dark-code/calibration/routing-policy.json", probed)

    def test_a_policy_naming_only_one_calibration_spelling_is_refused(self) -> None:
        # Measured before D-089: this loaded, and
        # .anti-dark-code/calibration/routing-policy.json -- the router's own
        # policy file -- then routed at Level 0 in every shape.
        data = json.loads(json.dumps(self.policy_source))
        surfaces = []
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") == "**/calibration/*.json":
                narrowed = dict(entry)
                narrowed["glob"] = ".agents/skills/anti-dark-code/calibration/*.json"
                surfaces.append(narrowed)
            else:
                surfaces.append(entry)
        # Narrowing alone leaves the other spellings unmapped, and an unmapped
        # path forces full on its own. The attack has to also grade them
        # cheaply, which is what the shipped `**/calibration/*.json` entry was
        # preventing for one spelling out of five.
        surfaces.append({"glob": ".anti-dark-code/calibration/*.json",
                         "surface": "docs", "effect": "prose",
                         "breadth": "leaf"})
        data["classifier"]["surfaces"] = surfaces
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("**/calibration/*.json", str(caught.exception))

    def test_the_shipped_calibration_templates_are_self_grading(self) -> None:
        # initialize_calibration copies these into every fresh install, so they
        # decide what an installing repository will route. They were absent
        # from the list entirely.
        probed = {path for _, path in self.route._self_grading_guard_paths()}
        for leaf in ("gates.json", "routing-policy.json"):
            path = f"anti-dark-code/assets/templates/calibration/{leaf}"
            self.assertIn(path, probed)
            self.assertTrue((REPO_ROOT / path).is_file())

    def test_every_installed_spelling_of_skill_policy_is_probed(self) -> None:
        probed = {path for _, path in self.route._self_grading_guard_paths()}
        for prefix in self.route.INSTALLED_SKILL_PREFIXES:
            self.assertIn(f"{prefix}anti-dark-code/SKILL.md", probed)

    def test_a_policy_naming_only_one_installed_spelling_is_refused(self) -> None:
        # Before D-086 this policy loaded, and a change to
        # .claude/skills/anti-dark-code/SKILL.md then routed at Level 0 in all
        # 72 shapes -- a file this repository's own installer writes.
        data = json.loads(json.dumps(self.policy_source))
        surfaces = []
        for entry in data["classifier"]["surfaces"]:
            if entry.get("glob") == "**/SKILL.md":
                for spelling in ("anti-dark-code/SKILL.md",
                                 ".agents/skills/anti-dark-code/SKILL.md"):
                    narrowed = dict(entry)
                    narrowed["glob"] = spelling
                    surfaces.append(narrowed)
            else:
                surfaces.append(entry)
        data["classifier"]["surfaces"] = surfaces
        with self.assertRaises(self.route.PolicyError) as caught:
            self.route.load_policy(
                data, self.gates_source, sorted(CAPABILITY_IDS),
                self.gates_source["canonical_full_set"])
        self.assertIn("**/SKILL.md", str(caught.exception))

    def test_an_unmapped_self_grading_path_is_not_a_load_failure(self) -> None:
        # A policy with no authority fact cannot use the incomplete-classifier
        # bypass; unknown routing forces full.  D-093 applies once a policy
        # claims any verification-authority classification.
        data = json.loads(json.dumps(self.policy_source))
        data["classifier"]["surfaces"] = []
        policy = self.route.load_policy(
            data, self.gates_source, sorted(CAPABILITY_IDS),
            self.gates_source["canonical_full_set"])
        for _, path in self.route.SELF_GRADING_PATHS:
            self.assertTrue(self._route_for(path, policy).force_full, path)

    def test_every_shipped_script_is_authority_by_location(self) -> None:
        """D-100, amended by D-118. Dynamic loader spellings cannot escape the script boundary."""
        scripts = SKILL_ROOT / "scripts"
        globs = {glob for _, glob, *_ in self.route.AUTHORITY_CLASSIFIERS}
        self.assertIn("anti-dark-code/scripts/*.py", globs)
        self.assertIn("**/anti-dark-code/scripts/*.py", globs)
        policy = self._approved_policy()
        demoted = []
        for script in sorted(scripts.glob("*.py")):
            path = script.relative_to(REPO_ROOT).as_posix()
            if not self._route_for(path, policy).force_full:
                demoted.append(path)
        self.assertEqual([], demoted, "; ".join(demoted))

    def test_nested_consumer_scripts_are_product_code_and_shipped_scripts_are_authority(self) -> None:
        """D-118. The canonical scripts entry names the shipped skill's own directory.

        Measured before D-118 with every rule approved: tools/scripts/build.py,
        packages/app/scripts/migrate.py, docs/scripts/render.py,
        ci/scripts/release.py, and src/scripts/__init__.py in an installing
        repository routed as verification authority at Level 3 with
        force_full under the `**/scripts/*.py` entry, wider than D-100's
        statement (D-107). The cheap `**/scripts/*.py` product entry is what
        returns them to the product route; removing it leaves them unmapped
        and full, which is safe and was not the owner's choice.
        """
        policy = self._approved_policy()
        consumer = ("tools/scripts/build.py", "packages/app/scripts/migrate.py",
                    "docs/scripts/render.py", "ci/scripts/release.py",
                    "src/scripts/__init__.py")
        widened = [path for path in consumer
                   if self._route_for(path, policy).force_full]
        self.assertEqual([], widened, "; ".join(widened))
        for path in consumer:
            self.assertEqual(2, self._route_for(path, policy).minimum_level, path)
        # A root-level scripts directory matches nothing and forces full, as
        # it did before D-118.
        self.assertTrue(self._route_for("scripts/deploy.py", policy).force_full)
        demoted = []
        for script in sorted((SKILL_ROOT / "scripts").glob("*.py")):
            source = script.relative_to(REPO_ROOT).as_posix()
            spellings = (source, *(f"{prefix}{source}"
                                   for prefix in self.route.INSTALLED_SKILL_PREFIXES))
            for path in spellings:
                if not self._route_for(path, policy).force_full:
                    demoted.append(path)
        self.assertEqual([], demoted, "; ".join(demoted))

    def test_a_case_variant_of_an_authority_path_forces_full(self) -> None:
        """D-119. Classification stays case-sensitive (R-040); the route never gets cheaper.

        Measured at 6930274 by the round-twenty-one challenger, with every
        rule approved: ANTI-DARK-CODE/scripts/adc_route.py matched the cheap
        **/scripts/*.py product entry and neither D-118 authority glob, so it
        routed as Level 2 product code, where the old wide entry had made it
        authority. With real git, a commit carrying that path from a
        case-sensitive host was graded product code and, pulled onto an NTFS
        clone, replaced the genuine router on disk.
        """
        policy = self._approved_policy()
        variants = ("ANTI-DARK-CODE/scripts/adc_route.py",
                    "Anti-Dark-Code/scripts/work_receipt.py",
                    ".agents/skills/ANTI-DARK-CODE/scripts/adc_route.py",
                    "ANTI-DARK-CODE/scripts/new_tool.py",
                    ".GITATTRIBUTES",
                    "anti-dark-code/TESTS/test_route.py")
        for path in variants:
            snapshot = self.route.ChangeSnapshot(
                inputs=(self.route.ChangeInput(
                    path=path, change_kind="modify", source="unstaged"),),
                base="HEAD", base_resolved=True, problems=())
            facts = self.route.collect_change_facts(snapshot, policy.classifier_map())
            # R-040: the classifier never folds case, so no fact is authority.
            self.assertFalse(
                any(fact.effect == "verification-authority" for fact in facts), path)
            route = self.route.build_route(facts, policy, snapshot_ok=True)
            self.assertTrue(route.force_full, path)
            self.assertIn("ADC-ROUTE-AUTHORITY-CASE-COLLISION", route.unknowns, path)
        # The genuine spelling is authority without the collision code, and an
        # ordinary consumer script is neither.
        genuine = self._route_for("anti-dark-code/scripts/adc_route.py", policy)
        self.assertTrue(genuine.force_full)
        self.assertNotIn("ADC-ROUTE-AUTHORITY-CASE-COLLISION", genuine.unknowns)
        consumer = self._route_for("tools/scripts/build.py", policy)
        self.assertFalse(consumer.force_full)
        self.assertNotIn("ADC-ROUTE-AUTHORITY-CASE-COLLISION", consumer.unknowns)


class SubmoduleContractTests(unittest.TestCase):
    """R-017 and R-019 for gitlinks, against a real submodule.

    Before D-072 this fixture was the counterexample: an ordinary edit to a
    tracked file inside the submodule left the receipt binding byte-identical
    while git reported the parent dirty, so a receipt taken before the edit
    still verified fresh.
    """

    def setUp(self) -> None:
        self.route = load_route()
        self.receipt = load_module(
            "adc_receipt", SKILL_ROOT / "scripts" / "adc_receipt.py")
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.child, self.parent = root / "child", root / "parent"
        self.child.mkdir()
        self._git(self.child, "init", "-q", "-b", "main", ".")
        self._identify(self.child)
        (self.child / "value.txt").write_text("one\n", encoding="utf-8")
        self._git(self.child, "add", "-A")
        self._git(self.child, "commit", "-qm", "one")
        self.first = self._read(self.child, "rev-parse", "HEAD")
        (self.child / "value.txt").write_text("two\n", encoding="utf-8")
        self._git(self.child, "commit", "-qam", "two")
        self.second = self._read(self.child, "rev-parse", "HEAD")

        self.parent.mkdir()
        self._git(self.parent, "init", "-q", "-b", "main", ".")
        self._identify(self.parent)
        (self.parent / "top.txt").write_text("top\n", encoding="utf-8")
        self._git(self.parent, "add", "-A")
        self._git(self.parent, "commit", "-qm", "top")
        added = subprocess.run(
            ["git", "-C", str(self.parent), "-c", "protocol.file.allow=always",
             "submodule", "add", "-q", self.child.as_uri(), "vendor"],
            capture_output=True, text=True)
        if added.returncode != 0:
            # A host that refuses a file transport cannot hold this claim, and
            # a verdict that does not say so reads as evidence. See D-054.
            self.tmp.cleanup()
            self.skipTest(f"this host cannot add a file submodule: "
                          f"{added.stderr.strip()[:120]}")
        self._git(self.parent, "commit", "-qm", "add submodule")
        self.sub = self.parent / "vendor"
        self.runner = self.route._default_runner(self.parent)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, repo: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                       capture_output=True)

    def _identify(self, repo: Path) -> None:
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "Test")

    def _read(self, repo: Path, *args: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def _binding(self):
        return self.receipt.collect_binding(
            self.parent, self.route, base_identity=None, head_identity=None,
            policy_source={}, gates_source={}, runner=self.runner)

    def test_a_gitlink_is_reported_as_unbindable(self) -> None:
        self.assertEqual(("vendor",), tuple(self._binding().unsupported_paths))

    def test_a_receipt_over_a_submodule_tree_never_verifies_fresh(self) -> None:
        binding = self._binding()
        receipt = self.receipt.build_receipt(
            {"schema_version": self.receipt.SCHEMA_VERSION,
             "binding": binding.as_payload()})
        # Verified against the very binding it was built from. Every field
        # matches, and it is still refused, because a matching field cannot
        # mean the tree stood still when a path in it is unbindable.
        verdict = self.receipt.verify_receipt(receipt, binding)
        self.assertFalse(verdict.fresh)
        self.assertIn(self.receipt.STALE_UNSUPPORTED,
                      {code for code, _ in verdict.reasons})
        self.assertEqual(2, verdict.exit_code)

    def test_an_ordinary_tree_still_verifies_fresh(self) -> None:
        # The counterexample. Without it this contract is satisfied by refusing
        # every receipt.
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        self._git(plain, "init", "-q", "-b", "main", ".")
        self._identify(plain)
        (plain / "top.txt").write_text("top\n", encoding="utf-8")
        self._git(plain, "add", "-A")
        self._git(plain, "commit", "-qm", "top")
        binding = self.receipt.collect_binding(
            plain, self.route, base_identity=None, head_identity=None,
            policy_source={}, gates_source={},
            runner=self.route._default_runner(plain))
        self.assertEqual((), tuple(binding.unsupported_paths))
        receipt = self.receipt.build_receipt(
            {"schema_version": self.receipt.SCHEMA_VERSION,
             "binding": binding.as_payload()})
        self.assertTrue(self.receipt.verify_receipt(receipt, binding).fresh)

    def test_the_identity_alone_still_cannot_see_the_submodule_move(self) -> None:
        # Recorded rather than fixed. This is why the contract refuses the tree
        # instead of binding the pointer: the identity is blind here, and a
        # future change that claims to bind submodule state has to move this.
        before = self.receipt.worktree_identity(self.parent, self.route, self.runner)
        self._git(self.sub, "checkout", "-q", self.first)
        after = self.receipt.worktree_identity(self.parent, self.route, self.runner)
        self.assertEqual(self.first, self._read(self.sub, "rev-parse", "HEAD"))
        self.assertEqual(before, after)

    def test_an_untracked_embedded_repository_is_also_unbindable(self) -> None:
        # Not a submodule: no gitlink, no .gitmodules entry. Git still refuses
        # to look inside it and lists it as a directory with a trailing slash,
        # so the fingerprint can bind its contents no better than a gitlink's.
        # This is why the test is "is a directory" rather than "mode 160000".
        plain = Path(self.tmp.name) / "host"
        plain.mkdir()
        self._git(plain, "init", "-q", "-b", "main", ".")
        self._identify(plain)
        (plain / "top.txt").write_text("top\n", encoding="utf-8")
        self._git(plain, "add", "-A")
        self._git(plain, "commit", "-qm", "top")
        inner = plain / "embedded"
        inner.mkdir()
        self._git(inner, "init", "-q", "-b", "main", ".")
        self._identify(inner)
        (inner / "x.txt").write_text("x\n", encoding="utf-8")
        self._git(inner, "add", "-A")
        self._git(inner, "commit", "-qm", "x")

        binding = self.receipt.collect_binding(
            plain, self.route, base_identity=None, head_identity=None,
            policy_source={}, gates_source={},
            runner=self.route._default_runner(plain))
        self.assertEqual(("embedded/",), tuple(binding.unsupported_paths))
        receipt = self.receipt.build_receipt(
            {"schema_version": self.receipt.SCHEMA_VERSION,
             "binding": binding.as_payload()})
        self.assertFalse(self.receipt.verify_receipt(receipt, binding).fresh)

    def test_an_ordinary_untracked_directory_is_not_unbindable(self) -> None:
        # The counterexample for the case above. An untracked directory git
        # will happily recurse into must not be refused.
        (self.parent / "notes").mkdir()
        (self.parent / "notes" / "a.txt").write_text("a\n", encoding="utf-8")
        binding = self._binding()
        self.assertEqual(("vendor",), tuple(binding.unsupported_paths))

    def test_a_dirty_submodule_makes_the_snapshot_incomplete(self) -> None:
        (self.sub / "value.txt").write_text("edited\n", encoding="utf-8")
        snapshot = self.route.read_change_inputs(self.parent, "HEAD", self.runner)
        self.assertIn("ADC-ROUTE-SUBMODULE-UNSUPPORTED", snapshot.problems)
        self.assertFalse(snapshot.complete)

    def test_so_the_route_forces_full(self) -> None:
        (self.sub / "value.txt").write_text("edited\n", encoding="utf-8")
        snapshot = self.route.read_change_inputs(self.parent, "HEAD", self.runner)
        policy_source = json.loads(
            (INSTALLED_CALIBRATION / "routing-policy.json").read_text(
                encoding="utf-8"))
        gates_source = json.loads(
            (INSTALLED_CALIBRATION / "gates.json").read_text(encoding="utf-8"))
        for rule in policy_source["rules"]:
            rule["review_status"] = "approved"
        policy = self.route.load_policy(
            policy_source, gates_source, sorted(CAPABILITY_IDS),
            gates_source["canonical_full_set"])
        facts = self.route.collect_change_facts(snapshot, policy.classifier_map())
        route = self.route.build_route(facts, policy, snapshot_ok=snapshot.complete)
        self.assertTrue(route.force_full)
        self.assertIn("ADC-ROUTE-SNAPSHOT-INCOMPLETE", route.unknowns)


MATRIX = REPO_ROOT / "design" / "routing" / "mutants" / "matrix.json"
REQUIREMENT_EVIDENCE = (REPO_ROOT / "design" / "routing"
                        / "requirement-evidence.json")


class RequirementTraceabilityTests(unittest.TestCase):
    # Reviewed by Codex in round twelve. R-013, R-018, and R-022 left this set
    # only after their process-level refusals and real runner contracts
    # collected and passed; a node-id mention alone would repeat D-070.
    REVIEWED_UNTRACED = frozenset({
        "R-005", "R-017", "R-019", "R-021"})

    def test_the_requirement_evidence_map_exists(self) -> None:
        self.assertTrue(
            REQUIREMENT_EVIDENCE.is_file(),
            "D-061 requires design/routing/requirement-evidence.json before M4")

    def test_every_registered_requirement_resolves_to_live_evidence(self) -> None:
        evidence = json.loads(REQUIREMENT_EVIDENCE.read_text(encoding="utf-8"))
        engineering = (REPO_ROOT / "design" / "routing"
                       / "ENGINEERING.md").read_text(encoding="utf-8")
        confirmed_text = engineering.split(
            "### 4.1 Confirmed requirements", 1)[1].split("### 4.2", 1)[0]
        verification_text = engineering.split(
            "**Verification ledger.**", 1)[1].split("**Test data rule.**", 1)[0]
        confirmed = set(re.findall(r"^\| (R-\d{3}) \|", confirmed_text, re.M))
        verification = set(re.findall(
            r"^\| (R-\d{3}) \|", verification_text, re.M))
        mapped = set(evidence.get("requirements", {}))
        untraced = set(evidence.get("untraced", []))

        self.assertEqual(2, evidence.get("schema_version"))
        self.assertEqual(confirmed, verification,
                         "confirmed and verification ledgers disagree")
        self.assertEqual(confirmed, mapped,
                         "the evidence map does not cover the requirement ledger")
        self.assertLessEqual(
            untraced, self.REVIEWED_UNTRACED,
            "the explicit untraced list may shrink; adding an id needs review")

        slice_text = (REPO_ROOT / "design" / "routing"
                      / "SLICE-001-route-shadow.md").read_text(encoding="utf-8")
        criteria = re.findall(r"^\| (S-\d{3}) \|.*$", slice_text, re.M)
        missing_links = []
        for criterion in criteria:
            line = next(row for row in slice_text.splitlines()
                        if row.startswith(f"| {criterion} |"))
            if not re.search(r"R-\d{3}", line):
                missing_links.append(criterion)
        self.assertEqual([], missing_links,
                         f"slice criteria without a requirement: {missing_links}")

        definitions, _ = suite_test_definitions()
        defined = {node_id for node_id, _ in definitions}
        problems = []
        for requirement, record in evidence["requirements"].items():
            tests = record.get("tests", [])
            for node_id in tests:
                if node_id not in defined:
                    problems.append(f"{requirement} names missing test {node_id}")
            if requirement in untraced:
                if record.get("partial"):
                    if not tests:
                        problems.append(
                            f"{requirement} is partial but names no live test")
                elif tests or record.get("mutation") or record.get("review"):
                    problems.append(f"{requirement} is untraced but carries evidence")
                continue
            if record.get("partial"):
                problems.append(
                    f"{requirement} is marked partial but omitted from untraced")
                continue
            if tests:
                continue
            mutation = record.get("mutation")
            if mutation:
                for key in ("matrix", "runner"):
                    path = REPO_ROOT / mutation.get(key, "")
                    if not path.is_file():
                        problems.append(
                            f"{requirement} names missing mutation {key} {path}")
                if not mutation.get("command"):
                    problems.append(f"{requirement} mutation evidence has no command")
                continue
            review = record.get("review")
            if review:
                path = REPO_ROOT / review.get("path", "")
                if not path.is_file():
                    problems.append(f"{requirement} names missing review file {path}")
                elif review.get("heading") not in path.read_text(encoding="utf-8"):
                    problems.append(
                        f"{requirement} review heading is absent: {review.get('heading')}")
                continue
            problems.append(f"{requirement} has no evidence and is not untraced")
        self.assertEqual([], problems, "; ".join(problems))


class WorkflowParallelContractTests(unittest.TestCase):
    def test_workflow_uses_proven_parallel_verification(self) -> None:
        text = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        self.assertEqual("adopted", json.loads((REPO_ROOT / "design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json").read_text())["adoption"])
        self.assertEqual(2, text.count("pip install --disable-pip-version-check --quiet pytest pytest-xdist"))
        self.assertGreaterEqual(text.count("python -m pytest anti-dark-code/tests -q -n auto"), 2)
        replay = re.findall(r"^\s*(python design/routing/mutants/replay\.py[^\n]*)$", text, re.M)
        self.assertEqual(["python design/routing/mutants/replay.py --jobs 2"], replay)
        self.assertNotIn("--id", replay[0])
        self.assertNotIn("--write", replay[0])
        # A selector is not an equivalent parallel replay command.
        self.assertNotEqual(replay[0], "python design/routing/mutants/replay.py --jobs 2 --id M01")


@unittest.skipUnless(MATRIX.is_file(), "mutation matrix is not part of this tree")
class MutationMatrixIntegrityTests(unittest.TestCase):
    """The matrix describes the source. This checks it still does.

    Deselected during a replay, not skipped. Replay mutates the tree on
    purpose, so this check would fail for whichever row is applied and every
    mutant would report caught with no behavioural test having noticed. The
    first version skipped instead, which was worse in a quieter way: a skip
    counts toward the per-host skip total, and that total is what decides
    whether an uncaught row reads as SURVIVED or as "nobody could check this".
    Four guaranteed skips on every host would have relabelled every genuine
    survivor as unverified. test_replay_still_deselects_this_class holds the
    filter.

    Outside a replay it holds two things that have both gone wrong here.

    A committed mutant. a92c869 shipped M01 into the router, turning an
    obligation union into an assignment, because the authoritative replay was
    running in the background and `git add -A` took the tree as it was
    mid-row. The suite was green before that commit and green after: the defect
    existed only in the window where no test ran. Nothing in a test run could
    have seen it, and this check would have, because the row's original text
    was missing from the file.

    Matrix rot. M56's target moved when an unrelated fix rewrote the line it
    named, and replay reported TARGET MISSING, which reads like a surviving
    mutant and is really a stale row.
    """

    def setUp(self) -> None:
        self.rows = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_every_mutant_target_is_present_in_its_source(self) -> None:
        missing = []
        for row in self.rows:
            if row.get("superseded_by"):
                continue
            source = REPO_ROOT / row["source"]
            if not source.is_file():
                missing.append(f"{row['id']} names a source that does not exist: "
                               f"{row['source']}")
                continue
            if row["old"] not in source.read_text(encoding="utf-8"):
                missing.append(
                    f"{row['id']} ({row['name']}) cannot be applied: its "
                    f"original text is absent from {row['source']}. Either the "
                    "row is stale, or that file is holding the mutant.")
        self.assertEqual([], missing, "; ".join(missing))

    def test_decision_guard_recurses_through_claimed_source_classes(self) -> None:
        """The fixed source list must not skip nested D-id citations."""
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            skill = root / "anti-dark-code"
            missing_decision = "D-" + "999"
            probes = [
                skill / "scripts/nested/probe.py",
                skill / "tests/nested/test_probe.py",
                root / "design/routing/plans/probe.md",
            ]
            for probe in probes:
                probe.parent.mkdir(parents=True, exist_ok=True)
                probe.write_text(f"See {missing_decision}.\n", encoding="utf-8")
            log = root / "design/routing/DECISION-LOG.md"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("## D-001: recorded\n", encoding="utf-8")
            unresolved = unresolved_decision_references(root, skill)
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in probes},
                {entry.split(" cites ", 1)[0] for entry in unresolved},
            )

    def test_every_referenced_decision_exists(self) -> None:
        """D-090. A comment citing a decision asserts one was recorded.

        D-088 and D-089 were cited by four comments in `adc_route.py`, four in
        `test_route.py`, and three places in a handoff while neither existed.
        The suite passed at 436, validation was clean, 95 mutation rows were
        caught, and a five-agent audit ran, all with eight dangling references
        in the tree. Nothing resolved a decision id, so nothing could notice.
        """
        log = REPO_ROOT / "design" / "routing" / "DECISION-LOG.md"
        self.assertTrue(
            re.search(r"^## D-\d{3}", log.read_text(encoding="utf-8"), re.M),
            "the decision log has no decision headings",
        )
        unresolved = unresolved_decision_references(REPO_ROOT, SKILL_ROOT)
        self.assertEqual([], unresolved, "; ".join(unresolved))

    def test_every_mutant_target_occurs_exactly_once(self) -> None:
        """Presence is not enough: `replay.py` mutates the first site only.

        `original.replace(old, new, 1)` rewrites one occurrence. A row whose
        text appears twice therefore mutates one site, leaves the other
        running, and still reports caught, so the matrix claims coverage of a
        line nothing tested. Six active rows were in that state before D-087,
        including one added the round before by a function that copied a loop.
        """
        ambiguous = []
        for row in self.rows:
            if row.get("superseded_by"):
                continue
            source = REPO_ROOT / row["source"]
            if not source.is_file():
                continue
            found = source.read_text(encoding="utf-8").count(row["old"])
            if found > 1:
                ambiguous.append(
                    f"{row['id']} ({row['name']}) matches {found} places in "
                    f"{row['source']}; replay would mutate only the first")
        self.assertEqual([], ambiguous, "; ".join(ambiguous))

    def test_no_row_records_a_mutant_as_the_current_source(self) -> None:
        """The narrower half, stated separately so a failure names the danger.

        A row whose replacement text is in the file while its original is not
        is not ambiguous: that file is currently mutated.
        """
        mutated = []
        for row in self.rows:
            if row.get("superseded_by"):
                continue
            source = REPO_ROOT / row["source"]
            if not source.is_file():
                continue
            text = source.read_text(encoding="utf-8")
            if row["new"] in text and row["old"] not in text:
                mutated.append(f"{row['source']} holds {row['id']} ({row['name']})")
        self.assertEqual([], mutated, "; ".join(mutated))

    def test_every_row_names_a_suite_that_exists(self) -> None:
        unknown = []
        for row in self.rows:
            for path in row.get("suite", ["anti-dark-code/tests/test_route.py"]):
                if not (REPO_ROOT / path).is_file():
                    unknown.append(f"{row['id']} names a missing suite: {path}")
        self.assertEqual([], unknown, "; ".join(unknown))

    def test_a_verdict_does_not_depend_on_which_host_ran_last(self) -> None:
        """The label is a function of the results, or it is not a record.

        The harness used to read the verdict off whichever host finished the
        run, so the same two results produced "caught" when Linux went last and
        "caught elsewhere" when Windows did. A coverage record that changes
        with replay order is describing the operator.
        """
        harness = load_module(
            "adc_replay",
            REPO_ROOT / "design" / "routing" / "mutants" / "replay.py")
        caught_linux = {"platform": "Linux", "verdict": "caught", "skipped": 0,
                        "failed_nodeids": ["suite.py::test_holds_mutant"],
                        "skipped_nodeids": []}
        skipped_windows = {"platform": "Windows", "verdict": "SURVIVED",
                           "skipped": 1,
                           "failed_nodeids": [],
                           "skipped_nodeids": ["suite.py::test_holds_mutant"]}
        self.assertEqual(
            harness.derive_verdict([caught_linux, skipped_windows]),
            harness.derive_verdict([skipped_windows, caught_linux]))
        self.assertEqual("caught elsewhere",
                         harness.derive_verdict([caught_linux, skipped_windows]))
        self.assertEqual("caught", harness.derive_verdict(
            [caught_linux, {**caught_linux, "platform": "Windows"}]))
        # D-110: a row no host caught is SURVIVED even when every host
        # skipped. The retired label "unverified: every host skipped" kept
        # M107 out of a Windows replay's not-caught list at 49fed51.
        self.assertEqual("SURVIVED", harness.derive_verdict(
            [skipped_windows, {**skipped_windows, "platform": "Linux"}]))
        # A host that ran the test and did not catch the mutant is a finding,
        # and must not be softened by the skipped-everywhere branch.
        self.assertEqual("SURVIVED", harness.derive_verdict(
            [{**skipped_windows, "skipped": 0},
             {**skipped_windows, "platform": "Linux", "skipped": 0}]))

    def test_replay_still_deselects_this_class(self) -> None:
        """If the filter stops matching, four skips return to every row.

        The harness names this class in a -k expression. A rename here would
        leave the expression matching nothing, the tests would run against a
        mutated tree, fail, and report every mutant caught. The coupling is
        real, so it is asserted rather than left to a comment.
        """
        harness = (REPO_ROOT / "design" / "routing" / "mutants"
                   / "replay.py").read_text(encoding="utf-8")
        self.assertIn("not MutationMatrixIntegrity", harness)
        self.assertTrue(type(self).__name__.startswith("MutationMatrixIntegrity"),
                        "this class no longer matches the harness filter")

    def test_mutant_ids_are_unique(self) -> None:
        seen = [row["id"] for row in self.rows]
        duplicates = sorted({i for i in seen if seen.count(i) > 1})
        self.assertEqual([], duplicates,
                         f"the matrix reuses ids: {duplicates}")

if __name__ == "__main__":
    unittest.main()

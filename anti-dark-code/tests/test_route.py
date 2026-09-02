from __future__ import annotations

import ast
import importlib.util
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

    def test_a_globally_configured_filter_is_also_neutralized(self) -> None:
        # git-lfs installs filter.lfs.* globally. A driver the repository did
        # not define locally must be neutralized too.
        sentinel = self._install_filter("global-style")
        (self.repo / "payload.txt").write_text("one\n", encoding="utf-8")
        self._git("add", "payload.txt")
        self._git("commit", "-qm", "payload")
        (self.repo / "payload.txt").write_text("two\n", encoding="utf-8")
        sentinel.unlink(missing_ok=True)
        self.route.read_change_inputs(self.repo, "base-ref")
        self.assertFalse(sentinel.exists())

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

        snap = self.route.read_change_inputs(
            self.repo, "base-ref", runner=linking_runner)

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
            cls.daemon.terminate()
            try:
                cls.daemon.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.daemon.kill()
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
            harness.run_suite = lambda paths: (True, "1 failed", 0)
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

INSTALLED_CALIBRATION = (REPO_ROOT / ".agents" / "skills" / "anti-dark-code"
                         / "calibration")


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
        self.assertIn("adc_route.py", str(caught.exception))

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

    def test_an_unmapped_self_grading_path_is_not_a_load_failure(self) -> None:
        # Unmapped carries confidence unknown, which forces full already. The
        # guard exists for the path that is classified and classified cheaply,
        # not for the one no entry describes.
        data = json.loads(json.dumps(self.policy_source))
        data["classifier"]["surfaces"] = []
        policy = self.route.load_policy(
            data, self.gates_source, sorted(CAPABILITY_IDS),
            self.gates_source["canonical_full_set"])
        for _, path in self.route.SELF_GRADING_PATHS:
            self.assertTrue(self._route_for(path, policy).force_full, path)


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
    REVIEWED_UNTRACED = frozenset({
        "R-005", "R-013", "R-017", "R-018", "R-019", "R-021", "R-022"})

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
        caught_linux = {"platform": "Linux", "verdict": "caught", "skipped": 0}
        skipped_windows = {"platform": "Windows", "verdict": "SURVIVED",
                           "skipped": 1}
        self.assertEqual(
            harness.derive_verdict([caught_linux, skipped_windows]),
            harness.derive_verdict([skipped_windows, caught_linux]))
        self.assertEqual("caught elsewhere",
                         harness.derive_verdict([caught_linux, skipped_windows]))
        self.assertEqual("caught", harness.derive_verdict(
            [caught_linux, {**caught_linux, "platform": "Windows"}]))
        self.assertEqual("unverified: every host skipped", harness.derive_verdict(
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

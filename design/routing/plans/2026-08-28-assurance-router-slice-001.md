# Assurance Router SLICE-001 Implementation Plan

> **For agentic workers:** Execute this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only deterministic change-impact router that explains which passes a change invalidated and which evidence it requires, while remaining structurally unable to skip any verification.

**Architecture:** One impure Git boundary (`read_change_inputs`) feeds two pure functions (`collect_change_facts`, `build_route`). Requirements combine by union and maximum only, never averaging or subtraction. A receipt binds the route to content-level repository identity. The gate runner reads receipts but still runs the full set in this slice.

**Tech Stack:** Python 3.12+, standard library only. `unittest.TestCase` classes run under pytest. No new dependency.

**Spec:** `design/routing/SLICE-001-route-shadow.md`, with `design/routing/ARCHITECTURE.md`, `design/routing/ENGINEERING.md`, and `design/routing/DECISION-LOG.md`. Read all four before starting. The plan argues from them.

**Round-two review gate, 2026-08-29:** Not ready to implement. The executable review in `design/routing/HANDOFF-BACK-PLAN.md` found blocking gaps in Tasks 1, 5, 6, 8, 9, and 10. In particular, the current blocks do not implement content identity, receipt integrity, per-gate freshness checks, or the canonical full recipe. The acceptance mapping at the end of this file is incomplete. Treat the code blocks below as reviewed evidence, not implementation instructions, until every blocking finding in that handoff is closed and this gate is removed.

## Global Constraints

- **Python 3.12+, standard library only.** No new runtime dependency. Every import must survive the hostile-environment matrix and the clean distribution check. `fnmatch` is available and already used for glob matching.
- **Type hints on every public function.** Return types included, `-> None` on test methods.
- **Test framework:** `unittest.TestCase` classes, methods named `test_*`, file ends with `if __name__ == "__main__": unittest.main()`. Modules load via `importlib.util.spec_from_file_location`, matching `tests/test_efficiency.py`.
- **Canonical suite invocation, from the repository root:** `python -m pytest anti-dark-code/tests -q`. Running from another directory produces an `ImportError` that is an invocation artifact, not a defect.
- **Baseline before any change:** `131 passed, 13 skipped, 45 subtests passed`. The skip count is platform dependent; the pass count is not.
- **Core validation:** `python anti-dark-code/scripts/adc.py validate --mode universal`. The `validate` subparser accepts `--skill` and `--mode` only. Do not pass `--repo`. One generated-artifact warning is expected.
- **Writing hygiene for every document and comment:** no em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages.
- **Fail closed, always.** A known unmapped fact or unreachable base produces the canonical full route. Unreadable Git output, an invalid policy, or an invalid full recipe exits 2 and writes no receipt. Never a silent default.
- **Monotonic combination only.** `minimum_level` takes the maximum, set fields take the union, booleans take logical OR, and `force_full` dominates. No averaging. No subtraction. No weighted score.
- **Never reuse `changed_files()` or `current_source_identity()` in router code.** `changed_files` filters `.agents/skills/` and `.anti-dark-code/` through `TOOLING_PATH_PREFIXES` and is `--name-only`. `current_source_identity` hashes porcelain status text and applies the same pathspec exclusions. Both are correct for their own jobs and wrong here. See D-010 and D-019.
- **Nothing in this slice may skip a check.** If a change would let the router reduce work, it belongs to a later slice.

---

## File Structure

| File | Responsibility |
|---|---|
| `anti-dark-code/scripts/adc_route.py` | Create. The Git status reader and the pure router. One explicit self-grading surface, beside `adc_efficiency.py`. |
| `anti-dark-code/scripts/adc.py` | Modify. CLI adapter only: the `route` subcommand, the escalate-only `--level` check, and one validator check for the new template. |
| `anti-dark-code/assets/templates/calibration/routing-policy.json` | Create. Shipped policy template. |
| `anti-dark-code/assets/verification-capabilities.json` | Modify. Add V21 and V22. |
| `anti-dark-code/tests/test_route.py` | Create. All router tests, S-001 through S-023. |

---

## Task 1: Add V21 and V22 to the capability catalog

Per D-016. M1 is exactly two entries. Do not add V23, V24, or V25: Q-001 closed by mapping ten of the twelve proposed labels onto eight existing ids.

**Files:**
- Modify: `anti-dark-code/assets/verification-capabilities.json`
- Modify: `anti-dark-code/scripts/adc.py`
- Modify: `anti-dark-code/tests/test_adc.py`
- Test: `anti-dark-code/tests/test_route.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: capability ids `V21` and `V22`, referenced by routing policy obligations in Task 8 onward.

- [ ] **Step 1: Read an existing capability entry to copy its exact shape**

Run: `python -c "import json;d=json.load(open('anti-dark-code/assets/verification-capabilities.json'));print(json.dumps(d['capabilities'][10],indent=2))"`

Every entry has: `id`, `name`, `slug`, `category`, `default_level`, `cost`, `purpose`, `local_work`, `agent_work`, `adaptations`, `selection`. Copy the `adaptations` key set exactly from a neighbouring entry; the keys are a closed set and a missing one fails validation.

- [ ] **Step 2: Write the failing test**

Create `anti-dark-code/tests/test_route.py`:

```python
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = Path(__file__).resolve().parents[1]
ROUTE_SCRIPT = SKILL_ROOT / "scripts" / "adc_route.py"

CAPABILITIES = SKILL_ROOT / "assets" / "verification-capabilities.json"


def load_route_module():
    spec = importlib.util.spec_from_file_location("adc_route", ROUTE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CapabilityCatalogTests(unittest.TestCase):
    def test_catalog_carries_the_two_router_capabilities(self) -> None:
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        by_id = {c["id"]: c for c in data["capabilities"]}
        self.assertIn("V21", by_id)
        self.assertIn("V22", by_id)
        self.assertEqual(by_id["V21"]["name"], "Affected-unit testing")
        self.assertEqual(by_id["V22"]["name"], "Input fuzz testing")

    def test_catalog_stops_at_twenty_two(self) -> None:
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        ids = sorted(c["id"] for c in data["capabilities"])
        self.assertEqual(len(ids), 22)
        self.assertEqual(ids[-1], "V22")

    def test_every_capability_shares_one_field_shape(self) -> None:
        data = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        shapes = {tuple(sorted(c.keys())) for c in data["capabilities"]}
        self.assertEqual(len(shapes), 1, f"capability entries disagree on fields: {shapes}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: FAIL. `test_catalog_carries_the_two_router_capabilities` fails on `V21` missing.

- [ ] **Step 4: Add the two entries**

Append to the `capabilities` array, copying the `adaptations` key set verbatim from an existing entry:

```json
{
  "id": "V21",
  "name": "Affected-unit testing",
  "slug": "affected-unit-testing",
  "category": "efficiency",
  "default_level": 1,
  "cost": "low",
  "purpose": "Execute the assertions belonging to the slice a change actually touched.",
  "local_work": ["Run the unit and module tests owning the changed paths", "Report the executed set, not the selected set"],
  "agent_work": ["Name ownership edges a path map cannot see"],
  "selection": {"core": true, "signals_any": [], "risks_any": [], "candidate_if_missing": false}
}
```

```json
{
  "id": "V22",
  "name": "Input fuzz testing",
  "slug": "input-fuzz-testing",
  "category": "resilience",
  "default_level": 2,
  "cost": "medium",
  "purpose": "Perturb input values and bytes to find parsing, decoding, and boundary defects.",
  "local_work": ["Generate hostile and malformed inputs against a parser or decoder", "Minimize and record any failing input"],
  "agent_work": ["Choose the input surfaces worth fuzzing and the properties that must hold"],
  "selection": {"core": false, "signals_any": ["generated_or_serialized_output"], "risks_any": [], "candidate_if_missing": true}
}
```

V21 is not V11: V11 selects affected checks, V21 executes their assertions. V22 is not V15: V15 perturbs the environment, V22 perturbs input values.

Update every catalog cardinality contract in the same task. The current implementation rejects any count other than 20, and the existing test asserts 20. At minimum, update the catalog description, the `build_plan` note, the catalog validator count and `V01..V22` set, the `plan` help text, and both assertions in `test_probe_and_plan_evaluate_all_capabilities`. A catalog-only edit makes the existing test fail with `22 != 20` and makes universal validation report the old count contract.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 3 tests.

- [ ] **Step 6: Confirm no existing test regressed**

Run: `python -m pytest anti-dark-code/tests -q`
Expected: `134 passed` or more, `13 skipped` on Windows. `test_probe_and_plan_evaluate_all_capabilities` must now assert 22, and `validate_skill` must accept exactly `V01` through `V22`.

Run: `python anti-dark-code/scripts/adc.py validate --mode universal`
Expected: `0 errors`.

- [ ] **Step 7: Commit**

```bash
git add anti-dark-code/assets/verification-capabilities.json anti-dark-code/tests/test_route.py
git commit -m "Add the two capability ids the router needs

V21 affected-unit testing, because V11 selects affected checks but does
not execute their assertions. V22 input fuzz testing, because V15
perturbs the environment while fuzzing perturbs input values. Q-001
mapped the other ten proposed labels onto eight existing ids, so the
catalog grows by two rather than five."
```

---

## Task 2: Parse Git status records into ChangeInput

The parser is pure: it takes captured bytes and returns records. Task 3 supplies the bytes. Splitting them is what makes hostile-path testing possible without building a repository per case.

**Files:**
- Create: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `V21`, `V22` from Task 1.
- Produces:
  - `ChangeInput` dataclass with fields `path: str`, `old_path: str | None`, `change_kind: str`, `source: str`, `old_mode: str | None`, `new_mode: str | None`, `old_object: str | None`, `new_object: str | None`
  - `CHANGE_KINDS: frozenset[str]` = `{"add","modify","delete","rename","copy","mode","type-change","unmerged","unknown"}`
  - `CHANGE_SOURCES: frozenset[str]` = `{"committed","staged","unstaged","untracked"}`
  - `parse_raw_z(payload: bytes, source: str) -> list[ChangeInput]`
  - `parse_untracked_z(payload: bytes) -> list[ChangeInput]`

**Fixture format, validated against real git on 2026-08-28.** A capture from a scratch repository produced exactly this, with NUL shown as `\0`:

```text
:100644 100644 5626abf f719efd M\0keep.py\0:100644 100644 7898192 7898192 R100\0old.py\0new.py\0:000000 100644 0000000 8ba3a16 A\0untracked.py\0
```

Two behaviours that capture settled:

- **Object ids abbreviate by default.** The router passes `--no-abbrev` so identity binding gets full ids. Equality still works either way, but an abbreviated id is weaker identity than R-017 asks for.
- **A mode change needs `git update-index --chmod=+x`, not `chmod`.** On Windows `core.fileMode` is `false`, so a filesystem `chmod` is invisible to git. Forcing the bit through the index produces `:100644 100755 587be6b 587be6b M`, the same object id on both sides with different modes. That is precisely the record the `old_object == new_object and old_mode != new_mode` branch below detects, so the branch is confirmed against real output rather than assumed.
- **Copy records need explicit detection.** A real staged copy appeared as `A` under the default raw diff and as `C100` only with `--find-copies --find-copies-harder`. Acquisition passes those flags, plus `--find-renames`, on every raw diff.

- [ ] **Step 1: Write the failing test**

Add to `anti-dark-code/tests/test_route.py`:

```python
class RawParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()

    def test_modify_record_carries_modes_and_objects(self) -> None:
        payload = b":100644 100644 aaaa1111 bbbb2222 M\x00scripts/adc.py\x00"
        rows = self.route.parse_raw_z(payload, "committed")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.path, "scripts/adc.py")
        self.assertEqual(row.change_kind, "modify")
        self.assertEqual(row.source, "committed")
        self.assertEqual(row.old_mode, "100644")
        self.assertEqual(row.new_mode, "100644")

    def test_mode_only_change_is_not_reported_as_modify(self) -> None:
        # Same object id on both sides, different mode. --name-status cannot
        # tell this from a content modification, which is why raw is required.
        payload = b":100644 100755 aaaa1111 aaaa1111 M\x00scripts/tool.sh\x00"
        rows = self.route.parse_raw_z(payload, "committed")
        self.assertEqual(rows[0].change_kind, "mode")

    def test_rename_keeps_both_paths(self) -> None:
        payload = b":100644 100644 aaaa1111 bbbb2222 R096\x00old/name.py\x00new/name.py\x00"
        rows = self.route.parse_raw_z(payload, "committed")
        self.assertEqual(rows[0].change_kind, "rename")
        self.assertEqual(rows[0].old_path, "old/name.py")
        self.assertEqual(rows[0].path, "new/name.py")

    def test_copy_keeps_both_paths(self) -> None:
        payload = b":100644 100644 aaaa1111 bbbb2222 C100\x00src/a.py\x00src/b.py\x00"
        rows = self.route.parse_raw_z(payload, "committed")
        self.assertEqual(rows[0].change_kind, "copy")
        self.assertEqual(rows[0].old_path, "src/a.py")
        self.assertEqual(rows[0].path, "src/b.py")

    def test_type_change_and_unmerged_are_preserved_not_flattened(self) -> None:
        payload = (
            b":100644 120000 aaaa1111 bbbb2222 T\x00link.txt\x00"
            b":100644 100644 aaaa1111 bbbb2222 U\x00conflict.py\x00"
        )
        rows = {r.path: r.change_kind for r in self.route.parse_raw_z(payload, "committed")}
        self.assertEqual(rows["link.txt"], "type-change")
        self.assertEqual(rows["conflict.py"], "unmerged")

    def test_unrecognised_status_letter_becomes_unknown_not_dropped(self) -> None:
        payload = b":100644 100644 aaaa1111 bbbb2222 X\x00weird.py\x00"
        rows = self.route.parse_raw_z(payload, "committed")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].change_kind, "unknown")

    def test_paths_with_newlines_and_non_ascii_survive(self) -> None:
        payload = (
            ":100644 100644 aaaa1111 bbbb2222 M\x00odé/café.py\x00"
            ":100644 100644 aaaa1111 bbbb2222 M\x00we\nird.py\x00"
        ).encode("utf-8")
        paths = sorted(r.path for r in self.route.parse_raw_z(payload, "committed"))
        self.assertEqual(paths, ["odé/café.py", "we\nird.py"])

    def test_untracked_payload_becomes_add_records(self) -> None:
        rows = self.route.parse_untracked_z(b"new/file.py\x00other.txt\x00")
        self.assertEqual({r.change_kind for r in rows}, {"add"})
        self.assertEqual({r.source for r in rows}, {"untracked"})

    def test_empty_payload_is_empty_not_an_error(self) -> None:
        self.assertEqual(self.route.parse_raw_z(b"", "committed"), [])
        self.assertEqual(self.route.parse_untracked_z(b""), [])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: FAIL with `FileNotFoundError` or `ModuleNotFoundError` for `adc_route.py`.

- [ ] **Step 3: Write the parser**

Create `anti-dark-code/scripts/adc_route.py`:

```python
#!/usr/bin/env python3
"""Deterministic change-impact routing for Anti-Dark-Code.

This module decides what verification a change requires. It never lowers a
requirement: combination is union and maximum only. Git acquisition is the one
impure boundary; classification and route building are pure so the monotonic
property can be tested exhaustively without a repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

CHANGE_KINDS = frozenset({
    "add", "modify", "delete", "rename", "copy",
    "mode", "type-change", "unmerged", "unknown",
})
CHANGE_SOURCES = frozenset({"committed", "staged", "unstaged", "untracked"})

# Git raw status letters. Anything absent here becomes "unknown", which blocks
# the fast path rather than being silently treated as an ordinary modification.
_RAW_STATUS = {
    "A": "add", "M": "modify", "D": "delete",
    "R": "rename", "C": "copy", "T": "type-change", "U": "unmerged",
}


@dataclass(frozen=True)
class ChangeInput:
    path: str
    change_kind: str
    source: str
    old_path: str | None = None
    old_mode: str | None = None
    new_mode: str | None = None
    old_object: str | None = None
    new_object: str | None = None


def _split_z(payload: bytes) -> list[str]:
    text = payload.decode("utf-8", errors="surrogateescape")
    return [part for part in text.split("\x00") if part != ""]


def parse_raw_z(payload: bytes, source: str) -> list[ChangeInput]:
    """Parse `git diff --raw -z` output into ChangeInput records.

    Raw is required rather than --name-status because only raw carries the mode
    and object columns. Without them a mode-only change is indistinguishable
    from a content modification, and an executable bit flip would route lower
    than it should.
    """
    if source not in CHANGE_SOURCES:
        raise ValueError(f"unknown change source: {source}")
    fields = _split_z(payload)
    rows: list[ChangeInput] = []
    index = 0
    while index < len(fields):
        header = fields[index]
        if not header.startswith(":"):
            index += 1
            continue
        parts = header[1:].split()
        if len(parts) < 5:
            index += 1
            continue
        old_mode, new_mode, old_object, new_object, status = parts[:5]
        letter = status[0]
        kind = _RAW_STATUS.get(letter, "unknown")
        takes_two_paths = kind in ("rename", "copy")
        needed = 2 if takes_two_paths else 1
        if index + needed >= len(fields):
            break
        if takes_two_paths:
            old_path, path = fields[index + 1], fields[index + 2]
        else:
            old_path, path = None, fields[index + 1]
        # A mode-only change keeps the same object on both sides. Git still
        # reports it as M, so the object comparison is the only discriminator.
        if kind == "modify" and old_object == new_object and old_mode != new_mode:
            kind = "mode"
        rows.append(ChangeInput(
            path=path, change_kind=kind, source=source, old_path=old_path,
            old_mode=old_mode, new_mode=new_mode,
            old_object=old_object, new_object=new_object,
        ))
        index += needed + 1
    return rows


def parse_untracked_z(payload: bytes) -> list[ChangeInput]:
    """Parse `git ls-files --others --exclude-standard -z` output."""
    return [
        ChangeInput(path=path, change_kind="add", source="untracked")
        for path in _split_z(payload)
    ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 12 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Parse Git raw status into ChangeInput records

Raw rather than name-status, because only raw carries the mode and object
columns that separate a mode-only change from a content modification. An
unrecognised status letter becomes unknown rather than being dropped, so
it blocks the fast path instead of passing as ordinary."
```

---

## Task 3: Acquire change inputs from Git

The impure boundary. Everything downstream is pure.

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `ChangeInput`, `parse_raw_z`, `parse_untracked_z` from Task 2.
- Produces:
  - `ChangeSnapshot` dataclass: `inputs: tuple[ChangeInput, ...]`, `base: str | None`, `base_resolved: bool`, `unreadable: tuple[str, ...]`
  - `read_change_inputs(repo, base, runner) -> ChangeSnapshot` where `runner` is a callable `(list[str]) -> bytes | None`, defaulting to a real Git call. Injecting the runner is what lets Task 3 be tested without a repository.

- [ ] **Step 1: Write the failing test**

```python
class AcquisitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()

    def _runner(self, table: dict[str, bytes | None]):
        def run(args: list[str]) -> bytes | None:
            for key, value in table.items():
                if key in " ".join(args):
                    return value
            return b""
        return run

    def test_snapshot_unions_all_four_sources(self) -> None:
        run = self._runner({
            "merge-base": b"abc123\n",
            "--find-copies-harder abc123 HEAD": b":100644 100644 a1 b2 M\x00committed.py\x00",
            "--find-copies-harder --cached HEAD": b":100644 100644 a1 b2 M\x00staged.py\x00",
            "diff --raw -z --no-abbrev --find-renames --find-copies --find-copies-harder": b":100644 100644 a1 b2 M\x00unstaged.py\x00",
            "ls-files --others": b"untracked.py\x00",
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        by_source = {i.source: i.path for i in snap.inputs}
        self.assertEqual(by_source["committed"], "committed.py")
        self.assertEqual(by_source["staged"], "staged.py")
        self.assertEqual(by_source["unstaged"], "unstaged.py")
        self.assertEqual(by_source["untracked"], "untracked.py")
        self.assertTrue(snap.base_resolved)

    def test_unreachable_base_is_reported_not_raised(self) -> None:
        run = self._runner({"merge-base": None})
        snap = self.route.read_change_inputs(Path("."), "origin/nope", runner=run)
        self.assertFalse(snap.base_resolved)
        self.assertTrue(snap.unreadable)

    def test_skill_tree_paths_are_not_filtered_out(self) -> None:
        # The whole point of D-010. changed_files() drops these; the router
        # must not, because routing-policy.json and gates.json live there.
        run = self._runner({
            "merge-base": b"abc123\n",
            "--find-copies-harder abc123 HEAD": (
                b":100644 100644 a1 b2 M\x00.agents/skills/anti-dark-code/calibration/gates.json\x00"
                b":100644 100644 a1 b2 M\x00.anti-dark-code/runs/keep.json\x00"
            ),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        paths = {i.path for i in snap.inputs}
        self.assertIn(".agents/skills/anti-dark-code/calibration/gates.json", paths)
        self.assertIn(".anti-dark-code/runs/keep.json", paths)

    def test_snapshot_ordering_is_canonical(self) -> None:
        run = self._runner({
            "merge-base": b"abc123\n",
            "--find-copies-harder abc123 HEAD": (
                b":100644 100644 a1 b2 M\x00zeta.py\x00"
                b":100644 100644 a1 b2 M\x00alpha.py\x00"
            ),
        })
        snap = self.route.read_change_inputs(Path("."), "origin/main", runner=run)
        committed = [i.path for i in snap.inputs if i.source == "committed"]
        self.assertEqual(committed, sorted(committed))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::AcquisitionTests -q`
Expected: FAIL with `AttributeError: module 'adc_route' has no attribute 'read_change_inputs'`.

- [ ] **Step 3: Implement acquisition**

Append to `adc_route.py`:

```python
import subprocess
from pathlib import Path


@dataclass(frozen=True)
class ChangeSnapshot:
    inputs: tuple[ChangeInput, ...]
    base: str | None
    base_resolved: bool
    unreadable: tuple[str, ...] = ()


def _default_runner(repo: Path):
    def run(args: list[str]) -> bytes | None:
        try:
            done = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, timeout=30, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            return None
        return done.stdout
    return run


def read_change_inputs(repo: Path, base: str, runner=None) -> ChangeSnapshot:
    """Acquire every routing-relevant Git record. The one impure boundary.

    This deliberately does not call changed_files(): that helper filters the
    skill trees and .anti-dark-code through TOOLING_PATH_PREFIXES, which is
    where gates.json and routing-policy.json live. Reusing it would make the
    router blind to its own escalators. See D-010.
    """
    run = runner or _default_runner(repo)
    unreadable: list[str] = []
    rows: list[ChangeInput] = []

    merge_base_raw = run(["merge-base", base, "HEAD"])
    base_resolved = bool(merge_base_raw)
    merge_base = merge_base_raw.decode("utf-8", "replace").strip() if merge_base_raw else None
    if not base_resolved:
        unreadable.append("ADC-ROUTE-BASE-UNREACHABLE")

    raw_diff = [
        "diff", "--raw", "-z", "--no-abbrev",
        "--find-renames", "--find-copies", "--find-copies-harder",
    ]

    if merge_base:
        payload = run([*raw_diff, merge_base, "HEAD"])
        if payload is None:
            unreadable.append("ADC-ROUTE-COMMITTED-UNREADABLE")
        else:
            rows.extend(parse_raw_z(payload, "committed"))

    for args, source, code in (
        ([*raw_diff, "--cached", "HEAD"], "staged", "ADC-ROUTE-STAGED-UNREADABLE"),
        (raw_diff, "unstaged", "ADC-ROUTE-UNSTAGED-UNREADABLE"),
    ):
        payload = run(args)
        if payload is None:
            unreadable.append(code)
            continue
        rows.extend(parse_raw_z(payload, source))

    untracked = run(["ls-files", "--others", "--exclude-standard", "-z"])
    if untracked is None:
        unreadable.append("ADC-ROUTE-UNTRACKED-UNREADABLE")
    else:
        rows.extend(parse_untracked_z(untracked))

    ordered = tuple(sorted(rows, key=lambda r: (r.source, r.path, r.change_kind)))
    return ChangeSnapshot(
        inputs=ordered, base=merge_base, base_resolved=base_resolved,
        unreadable=tuple(sorted(set(unreadable))),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 16 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Acquire change inputs at one impure Git boundary

Unions committed, staged, unstaged, and untracked records, and reports
an unreachable base rather than raising. Deliberately does not call
changed_files(), which filters the skill trees where gates.json and
routing-policy.json live. The runner is injectable so acquisition is
testable without building a repository per case."
```

---

## Task 4: Classify inputs into dimensioned facts

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `ChangeSnapshot`, `ChangeInput` from Task 3.
- Produces:
  - `ChangeFact` dataclass: `path`, `related_path`, `change_kind`, `source`, `surface`, `effect`, `breadth`, `sensitivity`, `confidence` (all `str`, `related_path` optional)
  - `collect_change_facts(snapshot: ChangeSnapshot, classifier: Mapping[str, Any]) -> tuple[ChangeFact, ...]`, pure
  - `SURFACES`, `EFFECTS`, `BREADTHS`, `SENSITIVITIES`, `CONFIDENCES` as `frozenset[str]`

- [ ] **Step 1: Write the failing test**

```python
class ClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.classifier = {
            "surfaces": [
                {"glob": "anti-dark-code/scripts/adc_route.py", "surface": "skill-policy",
                 "effect": "verification-authority", "breadth": "repository"},
                {"glob": ".github/workflows/*", "surface": "ci",
                 "effect": "verification-authority", "breadth": "repository"},
                {"glob": "anti-dark-code/SKILL.md", "surface": "skill-policy",
                 "effect": "behavior", "breadth": "repository"},
                {"glob": "README.md", "surface": "docs", "effect": "prose", "breadth": "leaf"},
            ]
        }

    def _snapshot(self, *inputs):
        return self.route.ChangeSnapshot(
            inputs=tuple(inputs), base="abc", base_resolved=True)

    def test_skill_md_is_never_inert_documentation(self) -> None:
        snap = self._snapshot(self.route.ChangeInput(
            path="anti-dark-code/SKILL.md", change_kind="modify", source="committed"))
        fact = self.route.collect_change_facts(snap, self.classifier)[0]
        self.assertEqual(fact.surface, "skill-policy")
        self.assertNotEqual(fact.effect, "prose")

    def test_unmapped_path_is_marked_unknown_not_guessed(self) -> None:
        snap = self._snapshot(self.route.ChangeInput(
            path="somewhere/new.py", change_kind="modify", source="committed"))
        fact = self.route.collect_change_facts(snap, self.classifier)[0]
        self.assertEqual(fact.confidence, "unknown")

    def test_rename_emits_a_fact_for_each_side(self) -> None:
        snap = self._snapshot(self.route.ChangeInput(
            path="README.md", old_path="anti-dark-code/SKILL.md",
            change_kind="rename", source="committed"))
        facts = self.route.collect_change_facts(snap, self.classifier)
        paths = {f.path for f in facts}
        self.assertEqual(paths, {"README.md", "anti-dark-code/SKILL.md"})
        # The sensitive old path must not vanish because the new path is docs.
        surfaces = {f.path: f.surface for f in facts}
        self.assertEqual(surfaces["anti-dark-code/SKILL.md"], "skill-policy")

    def test_facts_are_deterministically_ordered(self) -> None:
        a = self.route.ChangeInput(path="z.py", change_kind="modify", source="committed")
        b = self.route.ChangeInput(path="a.py", change_kind="modify", source="committed")
        first = self.route.collect_change_facts(self._snapshot(a, b), self.classifier)
        second = self.route.collect_change_facts(self._snapshot(b, a), self.classifier)
        self.assertEqual(first, second)

    def test_every_fact_field_is_a_closed_enum_value(self) -> None:
        snap = self._snapshot(self.route.ChangeInput(
            path=".github/workflows/tests.yml", change_kind="modify", source="committed"))
        fact = self.route.collect_change_facts(snap, self.classifier)[0]
        self.assertIn(fact.surface, self.route.SURFACES)
        self.assertIn(fact.effect, self.route.EFFECTS)
        self.assertIn(fact.breadth, self.route.BREADTHS)
        self.assertIn(fact.sensitivity, self.route.SENSITIVITIES)
        self.assertIn(fact.confidence, self.route.CONFIDENCES)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::ClassificationTests -q`
Expected: FAIL, `collect_change_facts` not defined.

- [ ] **Step 3: Implement classification**

Append to `adc_route.py`:

```python
import fnmatch

SURFACES = frozenset({"docs", "product", "tests", "schema", "ci", "release", "skill-policy", "site"})
EFFECTS = frozenset({"prose", "behavior", "public-contract", "persisted-state", "verification-authority"})
BREADTHS = frozenset({"leaf", "package", "runtime", "cross-runtime", "repository"})
SENSITIVITIES = frozenset({"normal", "auth", "privacy", "billing", "deletion", "crypto", "release"})
CONFIDENCES = frozenset({"verified", "inferred", "unknown"})


@dataclass(frozen=True)
class ChangeFact:
    path: str
    change_kind: str
    source: str
    surface: str
    effect: str
    breadth: str
    sensitivity: str
    confidence: str
    related_path: str | None = None


def _classify_path(path: str, classifier: Mapping[str, Any]) -> dict[str, str]:
    for entry in classifier.get("surfaces", []):
        if fnmatch.fnmatch(path, entry["glob"]):
            return {
                "surface": entry["surface"],
                "effect": entry["effect"],
                "breadth": entry.get("breadth", "leaf"),
                "sensitivity": entry.get("sensitivity", "normal"),
                "confidence": "verified",
            }
    # An unmapped path is not a low-risk path. Confidence unknown is what makes
    # R-003 block the fast path rather than guessing a surface.
    return {
        "surface": "product", "effect": "behavior", "breadth": "repository",
        "sensitivity": "normal", "confidence": "unknown",
    }


def collect_change_facts(
    snapshot: ChangeSnapshot, classifier: Mapping[str, Any]
) -> tuple[ChangeFact, ...]:
    """Pure classification of an acquired snapshot into dimensioned facts.

    Rename and copy records emit a fact for each side. Dropping the old path
    would let a rename out of a sensitive location route as though only the
    destination mattered.
    """
    facts: list[ChangeFact] = []
    for row in snapshot.inputs:
        sides = [(row.path, row.old_path)]
        if row.change_kind in ("rename", "copy") and row.old_path:
            sides.append((row.old_path, row.path))
        for path, related in sides:
            attrs = _classify_path(path, classifier)
            facts.append(ChangeFact(
                path=path, related_path=related, change_kind=row.change_kind,
                source=row.source, **attrs,
            ))
    return tuple(sorted(facts, key=lambda f: (f.path, f.source, f.change_kind)))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 21 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Classify change inputs into dimensioned facts

Rename and copy emit a fact for each side, so a move out of a sensitive
location cannot route as though only the destination mattered. An
unmapped path takes confidence unknown rather than a guessed surface,
which is what lets the route block a fast path it has not earned."
```

---

## Task 5: Load and validate the routing policy

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `ChangeFact` from Task 4.
- Produces:
  - `PolicyError(Exception)`
  - `load_policy(data: Mapping[str, Any], known_gate_ids: set[str]) -> dict[str, Any]`, raises `PolicyError`
  - Policy shape: `{"schema_version": 1, "full_recipe": {...}, "rules": [...], "classifier": {...}}`

- [ ] **Step 1: Write the failing test**

```python
class PolicyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.gates = {"validate-core", "full-suite", "distribution", "hostile-environment"}

    def _policy(self, **over):
        base = {
            "schema_version": 1,
            "classifier": {"surfaces": []},
            "full_recipe": {
                "minimum_level": 3,
                "gate_ids": ["validate-core", "full-suite", "distribution", "hostile-environment"],
            },
            "rules": [{
                "id": "docs-only",
                "review_status": "approved",
                "match": {"paths": ["README.md"]},
                "requires": {"passes": ["06"], "minimum_level": 0},
                "obligations": {"V09": ["validate-core"]},
            }],
        }
        base.update(over)
        return base

    def test_valid_policy_loads(self) -> None:
        loaded = self.route.load_policy(self._policy(), self.gates)
        self.assertEqual(loaded["schema_version"], 1)

    def test_obligation_naming_an_unknown_gate_is_rejected(self) -> None:
        bad = self._policy(rules=[{
            "id": "bad", "review_status": "approved",
            "match": {"paths": ["*.py"]}, "requires": {"minimum_level": 1},
            "obligations": {"V09": ["gate-that-does-not-exist"]},
        }])
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_obligation_with_no_gates_is_rejected(self) -> None:
        bad = self._policy(rules=[{
            "id": "bad", "review_status": "approved",
            "match": {"paths": ["*.py"]}, "requires": {"minimum_level": 1},
            "obligations": {"V09": []},
        }])
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_full_recipe_naming_an_unknown_gate_is_rejected(self) -> None:
        bad = self._policy(full_recipe={"minimum_level": 3, "gate_ids": ["nope"]})
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_missing_full_recipe_is_rejected(self) -> None:
        bad = self._policy()
        del bad["full_recipe"]
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_negative_predicate_in_match_is_rejected(self) -> None:
        # R-015: rules match one fact with positive predicates only. A rule
        # that fires on the absence of another fact is not monotonic.
        bad = self._policy(rules=[{
            "id": "bad", "review_status": "approved",
            "match": {"paths": ["*.py"], "not_paths": ["tests/*"]},
            "requires": {"minimum_level": 1}, "obligations": {"V09": ["validate-core"]},
        }])
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_unapproved_rule_is_rejected(self) -> None:
        bad = self._policy(rules=[{
            "id": "bad", "review_status": "proposed",
            "match": {"paths": ["*.py"]}, "requires": {"minimum_level": 1},
            "obligations": {"V09": ["validate-core"]},
        }])
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(bad, self.gates)

    def test_duplicate_rule_ids_are_rejected(self) -> None:
        rule = {
            "id": "dup", "review_status": "approved",
            "match": {"paths": ["*.py"]}, "requires": {"minimum_level": 1},
            "obligations": {"V09": ["validate-core"]},
        }
        with self.assertRaises(self.route.PolicyError):
            self.route.load_policy(self._policy(rules=[rule, dict(rule)]), self.gates)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::PolicyValidationTests -q`
Expected: FAIL, `PolicyError` not defined.

- [ ] **Step 3: Implement policy validation**

Append to `adc_route.py`:

```python
MATCH_KEYS = frozenset({"paths", "surfaces", "effects", "breadths", "sensitivities", "change_kinds"})


class PolicyError(Exception):
    """A routing policy that cannot be trusted. Never falls back to a default."""


def load_policy(data: Mapping[str, Any], known_gate_ids: set[str]) -> dict[str, Any]:
    """Validate a routing policy. An invalid policy is an error, never a default."""
    if not isinstance(data, Mapping):
        raise PolicyError("routing policy must be an object")
    if data.get("schema_version") != 1:
        raise PolicyError("routing policy schema_version must be 1")

    recipe = data.get("full_recipe")
    if not isinstance(recipe, Mapping):
        raise PolicyError("routing policy must define full_recipe")
    recipe_gates = recipe.get("gate_ids")
    if not isinstance(recipe_gates, list) or not recipe_gates:
        raise PolicyError("full_recipe.gate_ids must be a nonempty array")
    for gate_id in recipe_gates:
        if gate_id not in known_gate_ids:
            raise PolicyError(f"full_recipe names unknown gate: {gate_id}")

    rules = data.get("rules")
    if not isinstance(rules, list):
        raise PolicyError("routing policy must define a rules array")

    seen: set[str] = set()
    for rule in rules:
        rule_id = rule.get("id")
        if not rule_id:
            raise PolicyError("every rule needs an id")
        if rule_id in seen:
            raise PolicyError(f"duplicate rule id: {rule_id}")
        seen.add(rule_id)
        if str(rule.get("review_status", "")).lower() != "approved":
            raise PolicyError(f"rule {rule_id} is not approved")
        match = rule.get("match")
        if not isinstance(match, Mapping) or not match:
            raise PolicyError(f"rule {rule_id} needs a nonempty match")
        # Positive predicates only. A rule keyed on the absence or count of
        # other facts breaks monotonicity: adding a file could stop it firing.
        unknown = set(match) - MATCH_KEYS
        if unknown:
            raise PolicyError(f"rule {rule_id} uses non-positive match keys: {sorted(unknown)}")
        obligations = rule.get("obligations", {})
        if not isinstance(obligations, Mapping):
            raise PolicyError(f"rule {rule_id} obligations must be an object")
        for capability, gate_ids in obligations.items():
            if not isinstance(gate_ids, list) or not gate_ids:
                raise PolicyError(f"rule {rule_id} capability {capability} needs a nonempty gate list")
            for gate_id in gate_ids:
                if gate_id not in known_gate_ids:
                    raise PolicyError(f"rule {rule_id} names unknown gate: {gate_id}")
    return dict(data)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 29 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Validate routing policy, binding each capability to real gates

Every obligation names a nonempty set of gate ids that exist, so a route
cannot report coverage that no approved gate provides. Match keys are a
closed positive set: a rule keyed on the absence of another fact would
stop firing when a file is added, which breaks monotonicity."
```

---

## Task 6: Build the route by monotonic union

The heart of the subsystem. Every guardrail lives here.

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `ChangeFact` (Task 4), validated policy (Task 5).
- Produces:
  - `Route` dataclass: `minimum_level: int`, `passes: frozenset[str]`, `obligations: Mapping[str, frozenset[str]]`, `matched_rule_ids: frozenset[str]`, `force_full: bool`, `independent_review: bool`, `unmapped_paths: frozenset[str]`, `unknowns: frozenset[str]`
  - `build_route(facts, policy, hints=None, snapshot_ok=True) -> Route`, pure
  - `apply_hints(route: Route, hints: Mapping[str, Any]) -> Route`, additive only

- [ ] **Step 1: Write the failing test**

```python
class RouteBuildingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.policy = {
            "schema_version": 1,
            "classifier": {"surfaces": []},
            "full_recipe": {"minimum_level": 3, "gate_ids": ["full-suite"]},
            "rules": [
                {"id": "docs", "review_status": "approved",
                 "match": {"surfaces": ["docs"]},
                 "requires": {"passes": ["06"], "minimum_level": 0},
                 "obligations": {"V09": ["validate-core"]}},
                {"id": "authority", "review_status": "approved",
                 "match": {"effects": ["verification-authority"]},
                 "requires": {"passes": ["07", "14"], "minimum_level": 3,
                              "force_full": True, "independent_review": True},
                 "obligations": {"V12": ["hostile-environment"]}},
            ],
        }

    def _fact(self, path, **over):
        base = dict(path=path, change_kind="modify", source="committed",
                    surface="docs", effect="prose", breadth="leaf",
                    sensitivity="normal", confidence="verified")
        base.update(over)
        return self.route.ChangeFact(**base)

    def test_docs_change_takes_the_cheap_route(self) -> None:
        r = self.route.build_route((self._fact("README.md"),), self.policy)
        self.assertEqual(r.minimum_level, 0)
        self.assertFalse(r.force_full)

    def test_adding_an_authority_fact_raises_and_never_lowers(self) -> None:
        docs = self._fact("README.md")
        authority = self._fact(".github/workflows/tests.yml",
                               surface="ci", effect="verification-authority")
        cheap = self.route.build_route((docs,), self.policy)
        both = self.route.build_route((docs, authority), self.policy)
        self.assertGreaterEqual(both.minimum_level, cheap.minimum_level)
        self.assertTrue(both.passes >= cheap.passes)
        self.assertTrue(both.force_full)
        # Thirty README lines cannot cancel one authority change.
        self.assertEqual(both.minimum_level, 3)

    def test_order_does_not_change_the_route(self) -> None:
        a = self._fact("README.md")
        b = self._fact("x.yml", surface="ci", effect="verification-authority")
        self.assertEqual(self.route.build_route((a, b), self.policy),
                         self.route.build_route((b, a), self.policy))

    def test_unknown_confidence_forces_full_and_records_the_path(self) -> None:
        r = self.route.build_route((self._fact("mystery.py", confidence="unknown"),), self.policy)
        self.assertTrue(r.force_full)
        self.assertIn("mystery.py", r.unmapped_paths)

    def test_unreadable_snapshot_forces_full(self) -> None:
        r = self.route.build_route((self._fact("README.md"),), self.policy, snapshot_ok=False)
        self.assertTrue(r.force_full)

    def test_two_rules_union_their_requirements(self) -> None:
        fact = self._fact("both.md", surface="docs", effect="verification-authority")
        r = self.route.build_route((fact,), self.policy)
        self.assertEqual(r.passes, frozenset({"06", "07", "14"}))
        self.assertEqual(set(r.obligations), {"V09", "V12"})
        self.assertEqual(r.matched_rule_ids, frozenset({"docs", "authority"}))

    def test_hints_can_raise_but_never_lower(self) -> None:
        base = self.route.build_route((self._fact("README.md"),), self.policy)
        raised = self.route.apply_hints(base, {"minimum_level": 2, "passes": ["07"]})
        self.assertEqual(raised.minimum_level, 2)
        self.assertIn("07", raised.passes)
        lowered = self.route.apply_hints(raised, {"minimum_level": 0})
        self.assertEqual(lowered.minimum_level, 2)

    def test_hints_cannot_clear_force_full_or_drop_obligations(self) -> None:
        fact = self._fact("x.yml", surface="ci", effect="verification-authority")
        base = self.route.build_route((fact,), self.policy)
        tampered = self.route.apply_hints(base, {"force_full": False, "obligations": {}})
        self.assertTrue(tampered.force_full)
        self.assertEqual(set(tampered.obligations), set(base.obligations))

    def test_monotonic_under_generated_fact_sets(self) -> None:
        import itertools
        pool = [
            self._fact("README.md"),
            self._fact("a.yml", surface="ci", effect="verification-authority"),
            self._fact("m.py", confidence="unknown"),
            self._fact("b.md", surface="docs"),
        ]
        for size in range(1, len(pool)):
            for subset in itertools.combinations(pool, size):
                smaller = self.route.build_route(tuple(subset), self.policy)
                for extra in pool:
                    if extra in subset:
                        continue
                    larger = self.route.build_route(tuple(subset) + (extra,), self.policy)
                    self.assertGreaterEqual(larger.minimum_level, smaller.minimum_level)
                    self.assertTrue(larger.passes >= smaller.passes)
                    self.assertTrue(set(larger.obligations) >= set(smaller.obligations))
                    if smaller.force_full:
                        self.assertTrue(larger.force_full)
                    if smaller.independent_review:
                        self.assertTrue(larger.independent_review)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::RouteBuildingTests -q`
Expected: FAIL, `build_route` not defined.

- [ ] **Step 3: Implement route building**

Append to `adc_route.py`:

```python
@dataclass(frozen=True)
class Route:
    minimum_level: int
    passes: frozenset[str]
    obligations: Mapping[str, frozenset[str]]
    matched_rule_ids: frozenset[str]
    force_full: bool
    independent_review: bool
    unmapped_paths: frozenset[str] = frozenset()
    unknowns: frozenset[str] = frozenset()


def _fact_matches(fact: ChangeFact, match: Mapping[str, Any]) -> bool:
    """One fact against one rule. Positive predicates only, all must hold."""
    if "paths" in match and not any(fnmatch.fnmatch(fact.path, p) for p in match["paths"]):
        return False
    for key, attribute in (
        ("surfaces", "surface"), ("effects", "effect"), ("breadths", "breadth"),
        ("sensitivities", "sensitivity"), ("change_kinds", "change_kind"),
    ):
        if key in match and getattr(fact, attribute) not in match[key]:
            return False
    return True


def _merge_obligations(
    into: dict[str, set[str]], more: Mapping[str, Sequence[str]]
) -> dict[str, set[str]]:
    for capability, gate_ids in more.items():
        into.setdefault(capability, set()).update(gate_ids)
    return into


def build_route(
    facts: Sequence[ChangeFact],
    policy: Mapping[str, Any],
    hints: Mapping[str, Any] | None = None,
    snapshot_ok: bool = True,
) -> Route:
    """Combine every matching rule's requirements. Union and maximum only.

    Averaging or subtraction here would let unrelated low-risk facts dilute a
    critical trigger. Adding a fact must never reduce any field, which is the
    property R-001 tests and the reason there is no numeric score.
    """
    level = 0
    passes: set[str] = set()
    obligations: dict[str, set[str]] = {}
    matched: set[str] = set()
    force_full = not snapshot_ok
    independent_review = False
    unmapped: set[str] = set()
    unknowns: set[str] = set()

    if not snapshot_ok:
        unknowns.add("ADC-ROUTE-SNAPSHOT-INCOMPLETE")

    for fact in facts:
        if fact.confidence == "unknown":
            # An unknown does not mean the code is bad. It means the shortcut
            # has not been earned.
            unmapped.add(fact.path)
            unknowns.add("ADC-ROUTE-UNMAPPED-PATH")
            force_full = True
        for rule in policy.get("rules", []):
            if not _fact_matches(fact, rule["match"]):
                continue
            matched.add(rule["id"])
            requires = rule.get("requires", {})
            level = max(level, int(requires.get("minimum_level", 0)))
            passes.update(requires.get("passes", []))
            force_full = force_full or bool(requires.get("force_full"))
            independent_review = independent_review or bool(requires.get("independent_review"))
            _merge_obligations(obligations, rule.get("obligations", {}))

    if force_full:
        recipe = policy["full_recipe"]
        level = max(level, int(recipe.get("minimum_level", 3)))

    route = Route(
        minimum_level=level, passes=frozenset(passes),
        obligations={k: frozenset(v) for k, v in obligations.items()},
        matched_rule_ids=frozenset(matched), force_full=force_full,
        independent_review=independent_review,
        unmapped_paths=frozenset(unmapped), unknowns=frozenset(unknowns),
    )
    return apply_hints(route, hints) if hints else route


def apply_hints(route: Route, hints: Mapping[str, Any]) -> Route:
    """Apply agent hints. Additive only.

    A hint may add set members, raise the level, or set a boolean true. It may
    not remove, lower, or clear anything. An agent that believes a route is too
    heavy has no recourse here by design: only a reviewed rule backed by
    deterministic evidence may permit less work.
    """
    merged = {k: set(v) for k, v in route.obligations.items()}
    _merge_obligations(merged, hints.get("obligations", {}))
    return Route(
        minimum_level=max(route.minimum_level, int(hints.get("minimum_level", 0))),
        passes=route.passes | frozenset(hints.get("passes", [])),
        obligations={k: frozenset(v) for k, v in merged.items()},
        matched_rule_ids=route.matched_rule_ids,
        force_full=route.force_full or bool(hints.get("force_full")),
        independent_review=route.independent_review or bool(hints.get("independent_review")),
        unmapped_paths=route.unmapped_paths,
        unknowns=route.unknowns | frozenset(hints.get("unknowns", [])),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 38 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Build routes by monotonic union

Level takes the maximum, sets take the union, booleans take logical OR,
and force_full dominates. The exhaustive subset test proves adding a fact
never lowers a field, which is what a weighted score could not promise:
unrelated low-risk facts would dilute a critical trigger. Hints are
additive only, so agent judgment can raise a route and never lower one."
```

---

## Task 7: Ship the routing policy template and this repository's policy

**Files:**
- Create: `anti-dark-code/assets/templates/calibration/routing-policy.json`
- Modify: `anti-dark-code/scripts/adc.py` (validator check near line 805, beside the `gates.json` check)
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `load_policy` from Task 5.
- Produces: a shipped template that `load_policy` accepts, and a validator error when it goes missing.

- [ ] **Step 1: Write the failing test**

```python
class PolicyTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.template = (SKILL_ROOT / "assets" / "templates" / "calibration"
                         / "routing-policy.json")

    def test_template_ships(self) -> None:
        self.assertTrue(self.template.exists(), "routing-policy.json template is missing")

    def test_template_validates_against_its_own_gate_names(self) -> None:
        data = json.loads(self.template.read_text(encoding="utf-8"))
        named = set(data["full_recipe"]["gate_ids"])
        for rule in data["rules"]:
            for gate_ids in rule.get("obligations", {}).values():
                named.update(gate_ids)
        self.route.load_policy(data, named)

    def test_template_classifies_skill_md_as_policy_not_docs(self) -> None:
        data = json.loads(self.template.read_text(encoding="utf-8"))
        snap = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(
                path="anti-dark-code/SKILL.md", change_kind="modify", source="committed"),),
            base="abc", base_resolved=True)
        fact = self.route.collect_change_facts(snap, data["classifier"])[0]
        self.assertEqual(fact.surface, "skill-policy")

    def test_template_treats_docs_directory_as_a_site_not_inert(self) -> None:
        # docs/ in this repository is the published website.
        data = json.loads(self.template.read_text(encoding="utf-8"))
        snap = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(
                path="docs/index.html", change_kind="modify", source="committed"),),
            base="abc", base_resolved=True)
        fact = self.route.collect_change_facts(snap, data["classifier"])[0]
        self.assertEqual(fact.surface, "site")

    def test_every_authority_path_class_forces_full(self) -> None:
        data = json.loads(self.template.read_text(encoding="utf-8"))
        named = set(data["full_recipe"]["gate_ids"])
        for rule in data["rules"]:
            for gate_ids in rule.get("obligations", {}).values():
                named.update(gate_ids)
        policy = self.route.load_policy(data, named)
        authority_paths = [
            "anti-dark-code/scripts/adc_route.py",
            "anti-dark-code/scripts/adc.py",
            ".agents/skills/anti-dark-code/calibration/routing-policy.json",
            ".agents/skills/anti-dark-code/calibration/gates.json",
            ".github/workflows/tests.yml",
            "anti-dark-code/assets/verification-capabilities.json",
            "anti-dark-code/tests/test_route.py",
            "anti-dark-code/SKILL.md",
        ]
        for path in authority_paths:
            snap = self.route.ChangeSnapshot(
                inputs=(self.route.ChangeInput(
                    path=path, change_kind="modify", source="committed"),),
                base="abc", base_resolved=True)
            facts = self.route.collect_change_facts(snap, policy["classifier"])
            built = self.route.build_route(facts, policy)
            self.assertTrue(built.force_full, f"{path} did not force the full route")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::PolicyTemplateTests -q`
Expected: FAIL on the missing template file.

- [ ] **Step 3: Write the template**

Create `anti-dark-code/assets/templates/calibration/routing-policy.json`:

```json
{
  "schema_version": 1,
  "notes": "Repo-owned routing policy. Rules start approved only after review. An unmapped path forces the full route by design; add a reviewed rule rather than widening an existing glob.",
  "full_recipe": {
    "minimum_level": 3,
    "gate_ids": ["validate-core", "full-suite", "distribution", "hostile-environment"]
  },
  "classifier": {
    "surfaces": [
      {"glob": "anti-dark-code/scripts/*.py", "surface": "skill-policy", "effect": "verification-authority", "breadth": "repository"},
      {"glob": "anti-dark-code/tests/*.py", "surface": "tests", "effect": "verification-authority", "breadth": "repository"},
      {"glob": "anti-dark-code/assets/verification-capabilities.json", "surface": "schema", "effect": "verification-authority", "breadth": "repository"},
      {"glob": "anti-dark-code/assets/templates/calibration/*.json", "surface": "schema", "effect": "verification-authority", "breadth": "repository"},
      {"glob": ".agents/skills/anti-dark-code/calibration/*.json", "surface": "schema", "effect": "verification-authority", "breadth": "repository"},
      {"glob": ".github/workflows/*", "surface": "ci", "effect": "verification-authority", "breadth": "repository"},
      {"glob": "anti-dark-code/SKILL.md", "surface": "skill-policy", "effect": "verification-authority", "breadth": "repository"},
      {"glob": "anti-dark-code/references/*.md", "surface": "skill-policy", "effect": "behavior", "breadth": "repository"},
      {"glob": "anti-dark-code/VERSION", "surface": "release", "effect": "public-contract", "breadth": "repository", "sensitivity": "release"},
      {"glob": "docs/*", "surface": "site", "effect": "public-contract", "breadth": "package"},
      {"glob": "docs/data/*", "surface": "site", "effect": "public-contract", "breadth": "package"},
      {"glob": "metrics/*", "surface": "release", "effect": "public-contract", "breadth": "package"},
      {"glob": "design/*", "surface": "docs", "effect": "prose", "breadth": "leaf"},
      {"glob": "README.md", "surface": "docs", "effect": "prose", "breadth": "leaf"},
      {"glob": "CHANGELOG.md", "surface": "docs", "effect": "prose", "breadth": "leaf"},
      {"glob": "CONTRIBUTING.md", "surface": "docs", "effect": "prose", "breadth": "leaf"}
    ]
  },
  "rules": [
    {
      "id": "verification-authority",
      "review_status": "approved",
      "match": {"effects": ["verification-authority"]},
      "requires": {"passes": ["07", "10", "14", "11"], "minimum_level": 3, "force_full": true, "independent_review": true},
      "obligations": {
        "V09": ["validate-core"],
        "V12": ["hostile-environment"],
        "V21": ["full-suite"],
        "V08": ["distribution"]
      }
    },
    {
      "id": "public-surface",
      "review_status": "approved",
      "match": {"effects": ["public-contract"]},
      "requires": {"passes": ["11", "14"], "minimum_level": 2},
      "obligations": {"V08": ["distribution"], "V09": ["validate-core"]}
    },
    {
      "id": "ordinary-prose",
      "review_status": "approved",
      "match": {"surfaces": ["docs"], "effects": ["prose"]},
      "requires": {"passes": ["06"], "minimum_level": 0},
      "obligations": {"V09": ["validate-core"]}
    }
  ]
}
```

Every path that can change what verification means is `verification-authority`, including this repository's own tests, because a change to `test_route.py` alters the router's grader. `docs/` is `site`, not `docs`, because it is the published website.

- [ ] **Step 4: Register the template with the validator**

In `anti-dark-code/scripts/adc.py`, immediately after the `gates_path` block near line 805, add:

```python
    routing_path = template_dir / "routing-policy.json"
    if not routing_path.exists():
        errors.append("Missing calibration template routing-policy.json")
    else:
        try:
            json.loads(routing_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid calibration routing policy template: {exc}")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 43 tests.

Run: `python -m pytest anti-dark-code/tests -q`
Expected: no regression. If `test_validator_rejects_missing_gate_template` or the installer tests fail, the template directory contract changed; read the failure and fix the template, not the test.

Run: `python anti-dark-code/scripts/adc.py validate --mode universal`
Expected: `0 errors`.

- [ ] **Step 6: Commit**

```bash
git add anti-dark-code/assets/templates/calibration/routing-policy.json anti-dark-code/scripts/adc.py anti-dark-code/tests/test_route.py
git commit -m "Ship the routing policy template and register it with the validator

Every path that can change what verification means classifies as
verification-authority, including this repository's own router tests: a
change to the grader is a change to the grade. docs/ classifies as site
rather than docs, because in this repository it is the published
website, not inert documentation."
```

---

## Task 8: Write and verify route receipts

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `Route` from Task 6.
- Produces:
  - `receipt_payload(route, snapshot, identity, policy_sha, gates_sha) -> dict[str, Any]` (authoritative fields only, no clock)
  - `receipt_hash(payload: Mapping[str, Any]) -> str`
  - `write_receipt(payload, repo) -> Path`
  - `verify_receipt(payload, current_identity) -> tuple[bool, str | None]`

- [ ] **Step 1: Write the failing test**

```python
class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.r = self.route.Route(
            minimum_level=1, passes=frozenset({"11"}),
            obligations={"V09": frozenset({"validate-core"})},
            matched_rule_ids=frozenset({"ordinary-prose"}),
            force_full=False, independent_review=False)
        self.snap = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(path="a.md", change_kind="modify", source="committed"),),
            base="abc", base_resolved=True)
        self.identity = {"head": "h1", "content": {"a.md": "sha-1"}, "modes": {"a.md": "100644"}}

    def _payload(self, **over):
        p = self.route.receipt_payload(self.r, self.snap, self.identity, "p1", "g1")
        p.update(over)
        return p

    def test_hash_ignores_input_ordering(self) -> None:
        first = self.route.receipt_payload(self.r, self.snap, self.identity, "p1", "g1")
        shuffled = self.route.Route(
            minimum_level=1, passes=frozenset({"11"}),
            obligations={"V09": frozenset({"validate-core"})},
            matched_rule_ids=frozenset({"ordinary-prose"}),
            force_full=False, independent_review=False)
        second = self.route.receipt_payload(shuffled, self.snap, self.identity, "p1", "g1")
        self.assertEqual(self.route.receipt_hash(first), self.route.receipt_hash(second))

    def test_every_authoritative_array_is_sorted(self) -> None:
        # normalized_json_hash sorts object keys but preserves array order, so
        # the payload has to sort its own arrays or equal routes hash apart.
        p = self.route.receipt_payload(self.r, self.snap, self.identity, "p1", "g1")
        self.assertEqual(p["selected_passes"], sorted(p["selected_passes"]))
        self.assertEqual(p["matched_rule_ids"], sorted(p["matched_rule_ids"]))

    def test_clock_is_not_in_the_authoritative_hash(self) -> None:
        a = self._payload()
        b = self._payload()
        b["observed_at_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(self.route.receipt_hash(a), self.route.receipt_hash(b))

    def test_run_id_derives_from_the_hash(self) -> None:
        p = self._payload()
        self.assertTrue(p["run_id"].endswith(self.route.receipt_hash(p)[:12]))

    def test_changed_content_makes_a_receipt_stale(self) -> None:
        p = self._payload()
        ok, reason = self.route.verify_receipt(p, {**self.identity, "content": {"a.md": "sha-2"}})
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_changed_mode_alone_makes_a_receipt_stale(self) -> None:
        p = self._payload()
        ok, _ = self.route.verify_receipt(p, {**self.identity, "modes": {"a.md": "100755"}})
        self.assertFalse(ok)

    def test_unchanged_identity_verifies(self) -> None:
        p = self._payload()
        ok, reason = self.route.verify_receipt(p, dict(self.identity))
        self.assertTrue(ok, reason)

    def test_policy_change_makes_a_receipt_stale(self) -> None:
        p = self._payload()
        p2 = self.route.receipt_payload(self.r, self.snap, self.identity, "p2", "g1")
        self.assertNotEqual(self.route.receipt_hash(p), self.route.receipt_hash(p2))

    def test_new_untracked_file_makes_a_receipt_stale(self) -> None:
        p = self._payload()
        grown = {**self.identity, "content": {**self.identity["content"], "new.py": "sha-9"}}
        ok, _ = self.route.verify_receipt(p, grown)
        self.assertFalse(ok)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::ReceiptTests -q`
Expected: FAIL, `receipt_payload` not defined.

- [ ] **Step 3: Implement receipts**

Append to `adc_route.py`:

```python
import hashlib
import json
import os


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _canonical(value[k]) for k in sorted(value)}
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def receipt_hash(payload: Mapping[str, Any]) -> str:
    """Hash only the authoritative fields, with every array canonically sorted.

    Arrays must be sorted here rather than relying on the shared JSON hash
    helper, which stabilizes object-key order but preserves array order. Two
    equal routes built from differently ordered input would otherwise hash
    apart. Observational fields are excluded so a clock cannot change identity.
    """
    authoritative = {k: v for k, v in payload.items()
                     if k not in ("observed_at_utc", "run_id", "receipt_sha256")}
    blob = json.dumps(_canonical(authoritative), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def receipt_payload(
    route: Route, snapshot: ChangeSnapshot, identity: Mapping[str, Any],
    policy_sha: str, gates_sha: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "base": snapshot.base,
        "base_resolved": snapshot.base_resolved,
        "identity": _canonical(identity),
        "changed_files": sorted(
            ({"path": i.path, "old_path": i.old_path,
              "change_kind": i.change_kind, "source": i.source}
             for i in snapshot.inputs),
            key=lambda d: (d["path"], d["source"], d["change_kind"]),
        ),
        "routing_policy_sha256": policy_sha,
        "gate_configuration_sha256": gates_sha,
        "matched_rule_ids": sorted(route.matched_rule_ids),
        "selected_passes": sorted(route.passes),
        "minimum_level": route.minimum_level,
        "capability_to_gate_ids": {k: sorted(v) for k, v in sorted(route.obligations.items())},
        "selected_gate_ids": sorted({g for v in route.obligations.values() for g in v}),
        "force_full": route.force_full,
        "independent_review_required": route.independent_review,
        "independent_review_recorded": False,
        "unmapped_paths": sorted(route.unmapped_paths),
        "unknowns": sorted(route.unknowns),
    }
    digest = receipt_hash(payload)
    payload["receipt_sha256"] = digest
    payload["run_id"] = f"ADC-R-{digest[:12]}"
    return payload


def verify_receipt(
    payload: Mapping[str, Any], current_identity: Mapping[str, Any]
) -> tuple[bool, str | None]:
    """Refuse a receipt whose repository state has moved.

    Compares content digests and modes, not porcelain status text. Different
    dirty bytes produce identical status text, so a status digest would call a
    changed worktree fresh. See D-019.
    """
    recorded = payload.get("identity", {})
    if _canonical(recorded) != _canonical(current_identity):
        return False, "ADC-ROUTE-RECEIPT-STALE"
    return True, None


def write_receipt(payload: Mapping[str, Any], repo: Path) -> Path:
    run_dir = repo / ".anti-dark-code" / "runs" / str(payload["run_id"])
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "route.json"
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
```

`changed_files` in the payload is sorted by an explicit key rather than relying on set ordering, so two runs over the same snapshot produce the same bytes.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS, 52 tests.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Bind route receipts to content identity, not status text

Arrays are canonically sorted before hashing, because the shared JSON
hash helper stabilizes object keys but preserves array order, so equal
routes built from differently ordered input would hash apart. run_id
derives from the hash and the clock stays outside it, so no receipt can
change identity by being written at a different time."
```

---

## Task 9: Add the read-only `route` subcommand

**Files:**
- Modify: `anti-dark-code/scripts/adc.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: everything from Tasks 3 through 8.
- Produces: `adc.py route --repo . --changed-from <ref> [--phase task|merge] [--write]`, exit 0 on a computed route, exit 2 on unreadable Git or invalid policy.

- [ ] **Step 1: Write the failing test**

```python
class RouteCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "adc", SKILL_ROOT / "scripts" / "adc.py")
        assert spec and spec.loader
        self.adc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adc)

    def test_route_subcommand_is_registered(self) -> None:
        parser = self.adc.build_parser() if hasattr(self.adc, "build_parser") else None
        # Fall back to invoking main with --help, which must not raise.
        with self.assertRaises(SystemExit) as caught:
            self.adc.main(["route", "--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_route_rejects_a_level_below_the_computed_minimum(self) -> None:
        # R-013. --level may raise, never lower.
        code = self.adc.main(["gates", "--repo", ".", "--level", "0",
                              "--route", "does-not-exist.json"])
        self.assertEqual(code, 2)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::RouteCommandTests -q`
Expected: FAIL, `route` is not a valid subcommand.

- [ ] **Step 3: Register the subcommand**

In `anti-dark-code/scripts/adc.py`, beside the other `sub.add_parser` calls near line 3969:

```python
    p = sub.add_parser("route", help="Read-only change-impact route for the current diff")
    p.add_argument("--repo", default=".")
    p.add_argument("--changed-from", required=True)
    p.add_argument("--phase", choices=("task", "merge"), default="task")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=command_route)
```

Add a loader beside `load_efficiency_helper` at `adc.py:3841`, copying its shape exactly. The `sys.dont_write_bytecode` guard is not optional: without it the import writes `__pycache__` into the skill tree, which the universal validator reports.

```python
def load_route_helper() -> Any:
    helper_path = Path(__file__).with_name("adc_route.py")
    spec = importlib.util.spec_from_file_location("adc_route", helper_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load route helper: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous_bytecode_setting = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
    return module
```

Then the command function:

```python
def command_route(args: argparse.Namespace) -> int:
    route_module = load_route_helper()
    repo = Path(args.repo)
    snapshot = route_module.read_change_inputs(repo, args.changed_from)
    policy_path = safe_calibration_dir(repo, "routing policy read") / "routing-policy.json"
    if not policy_path.exists():
        print("NO POLICY: no routing-policy.json in calibration. Full verification required.")
        return 2
    gate_config = read_json(safe_calibration_dir(repo, "gate configuration read") / "gates.json")
    known_gate_ids = {g["id"] for g in gate_config.get("gates", []) if isinstance(g, dict) and g.get("id")}
    try:
        policy = route_module.load_policy(read_json(policy_path), known_gate_ids)
    except route_module.PolicyError as exc:
        print(f"REFUSED: invalid routing policy: {exc}")
        return 2

    facts = route_module.collect_change_facts(snapshot, policy["classifier"])
    built = route_module.build_route(
        facts, policy, snapshot_ok=snapshot.base_resolved and not snapshot.unreadable)
    identity = route_module.current_route_identity(repo, snapshot)
    payload = route_module.receipt_payload(
        built, snapshot, identity,
        normalized_json_hash(policy), normalized_json_hash(gate_config))

    gates = ",".join(payload["selected_gate_ids"]) or "none"
    print(
        f"ROUTE {payload['run_id']}: {args.phase} L{built.minimum_level}; "
        f"{len(snapshot.inputs)} file(s); rules={','.join(payload['matched_rule_ids']) or 'none'}; "
        f"gates={gates}; full={'yes' if built.force_full else 'no'}; "
        f"unknowns={len(built.unknowns)}"
    )
    if args.write:
        written = route_module.write_receipt(payload, repo)
        print(f"RECEIPT: {written}")
    print("SHADOW ONLY: this route cannot skip anything. Run full verification as normal.")
    return 0
```

Add `current_route_identity(repo, snapshot)` to `adc_route.py`, hashing current bytes and modes for every path in the snapshot. Do not call `current_source_identity`: it digests porcelain status text and excludes the skill trees by pathspec, so it would call a changed `gates.json` fresh.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests -q`
Expected: PASS with no regression.

Run the command for real:
```bash
python anti-dark-code/scripts/adc.py route --repo . --changed-from origin/main
```
Expected: one `ROUTE` line, then `SHADOW ONLY`.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc.py anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Add the read-only route subcommand

Prints one compact route line and writes a bound receipt with --write.
It cannot skip anything, and says so on every run. Identity comes from a
router-owned helper rather than current_source_identity, which digests
porcelain status text and excludes the skill trees by pathspec."
```

---

## Task 10: Bind the gate runner without letting it skip

**Files:**
- Modify: `anti-dark-code/scripts/adc.py` (`run_gates`, near line 2569)
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `verify_receipt` from Task 8.
- Produces: `gates --route <path>` that refuses a stale receipt, refuses a `--level` below the route minimum, and still runs the full approved set.

- [ ] **Step 1: Write the failing test**

```python
class GateBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "adc", SKILL_ROOT / "scripts" / "adc.py")
        assert spec and spec.loader
        self.adc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adc)

    def test_level_below_route_minimum_is_refused(self) -> None:
        self.assertEqual(self.adc.check_route_level(route_minimum=2, requested=0),
                         (False, 2))

    def test_level_above_route_minimum_is_allowed(self) -> None:
        allowed, effective = self.adc.check_route_level(route_minimum=1, requested=3)
        self.assertTrue(allowed)
        self.assertEqual(effective, 3)

    def test_missing_level_takes_the_route_minimum(self) -> None:
        allowed, effective = self.adc.check_route_level(route_minimum=2, requested=None)
        self.assertTrue(allowed)
        self.assertEqual(effective, 2)

    def test_uncovered_obligation_forces_full(self) -> None:
        covered = self.adc.obligations_are_covered(
            {"V09": {"validate-core"}}, approved_gate_ids={"validate-core"})
        self.assertTrue(covered)
        uncovered = self.adc.obligations_are_covered(
            {"V12": {"hostile-environment"}}, approved_gate_ids={"validate-core"})
        self.assertFalse(uncovered)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::GateBindingTests -q`
Expected: FAIL, `check_route_level` not defined.

- [ ] **Step 3: Implement the binding**

In `adc.py`:

```python
def check_route_level(route_minimum: int, requested: int | None) -> tuple[bool, int]:
    """--level may raise above the computed route. It may never lower it.

    Returning the refusal rather than raising keeps the caller's exit code in
    one place. See D-005: deterministic tooling establishes the minimum and
    judgment may only raise it.
    """
    if requested is None:
        return True, route_minimum
    if requested < route_minimum:
        return False, route_minimum
    return True, requested


def obligations_are_covered(
    capability_to_gate_ids: Mapping[str, set[str]], approved_gate_ids: set[str]
) -> bool:
    """Every required capability needs at least one approved covering gate."""
    return all(
        bool(set(gate_ids) & approved_gate_ids)
        for gate_ids in capability_to_gate_ids.values()
    )
```

Add `--route` to the `gates` subparser. When supplied: load the receipt, call `verify_receipt`, print `REFUSED: stale route receipt` and return 2 on a mismatch, then apply `check_route_level`. On refusal print the route minimum by name and return 2.

The receipt is read for its level floor and its coverage report only. This slice still runs every approved, enabled, applicable gate at the effective level. Do not filter the gate list by `selected_gate_ids`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests -q`
Expected: PASS with no regression.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc.py anti-dark-code/tests/test_route.py
git commit -m "Bind the gate runner to a route without letting it skip

--level becomes an escalate-only override: it may raise above the
computed minimum and exits 2 when it would lower it. A stale receipt
refuses execution. The runner still executes every approved applicable
gate, because nothing in this slice is allowed to skip."
```

---

## Task 11: Record shadow comparisons

**Files:**
- Modify: `anti-dark-code/scripts/adc_route.py`
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `Route` (Task 6), receipt payload (Task 8).
- Produces: `shadow_result(payload, gate_results) -> dict[str, Any]` and `write_shadow(result, repo, run_id) -> Path`.

- [ ] **Step 1: Write the failing test**

```python
class ShadowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.route = load_route_module()
        self.payload = {"run_id": "ADC-R-abc", "selected_gate_ids": ["validate-core"],
                        "matched_rule_ids": ["ordinary-prose"], "force_full": False}

    def test_omitted_gate_that_failed_is_a_routing_miss(self) -> None:
        result = self.route.shadow_result(
            self.payload, {"validate-core": "pass", "hostile-environment": "fail"})
        self.assertTrue(result["routing_miss"])
        self.assertIn("hostile-environment", result["missed_gates"])

    def test_omitted_gate_that_passed_is_not_a_miss(self) -> None:
        result = self.route.shadow_result(
            self.payload, {"validate-core": "pass", "hostile-environment": "pass"})
        self.assertFalse(result["routing_miss"])

    def test_selected_gate_failing_is_not_a_routing_miss(self) -> None:
        # The route selected it and it failed. The route was right.
        result = self.route.shadow_result(
            self.payload, {"validate-core": "fail", "hostile-environment": "pass"})
        self.assertFalse(result["routing_miss"])

    def test_route_class_is_recorded_for_per_class_counting(self) -> None:
        result = self.route.shadow_result(self.payload, {"validate-core": "pass"})
        self.assertEqual(result["route_class"], "ordinary-prose")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest anti-dark-code/tests/test_route.py::ShadowTests -q`
Expected: FAIL, `shadow_result` not defined.

- [ ] **Step 3: Implement the comparator**

Append to `adc_route.py`:

```python
def shadow_result(
    payload: Mapping[str, Any], gate_results: Mapping[str, str]
) -> dict[str, Any]:
    """Compare what the route would have run against what actually ran.

    A routing miss is the only outcome that matters: targeted verification
    green while an omitted gate failed. A selected gate failing is the route
    working, not a miss. Results carry their route class because a hundred
    successful documentation routes do not validate the leaf-code route.
    """
    selected = set(payload.get("selected_gate_ids", []))
    omitted_failures = sorted(
        gate_id for gate_id, outcome in gate_results.items()
        if gate_id not in selected and outcome != "pass"
    )
    selected_all_passed = all(
        outcome == "pass" for gate_id, outcome in gate_results.items() if gate_id in selected
    )
    rules = sorted(payload.get("matched_rule_ids", []))
    return {
        "schema_version": 1,
        "run_id": payload.get("run_id"),
        "route_class": ",".join(rules) if rules else "unmapped",
        "selected_gate_ids": sorted(selected),
        "gate_results": dict(sorted(gate_results.items())),
        "missed_gates": omitted_failures,
        "routing_miss": bool(omitted_failures) and selected_all_passed,
    }


def write_shadow(result: Mapping[str, Any], repo: Path, run_id: str) -> Path:
    run_dir = repo / ".anti-dark-code" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "shadow.json"
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
git commit -m "Record shadow comparisons per route class

A routing miss is targeted verification green while an omitted gate
failed. A selected gate failing is the route working. Results carry
their route class, because a hundred successful documentation routes do
not validate the leaf-code route."
```

---

## Task 12: Prove a weakened escalator fails the suite

The mutation test. Without it, every guardrail above is a comment.

**Files:**
- Test: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: everything.
- Produces: no production code. This task only adds tests.

- [ ] **Step 1: Write the mutation tests**

```python
class EscalatorMutationTests(unittest.TestCase):
    """Weakening any hard escalator must fail at least one test.

    These mutate the policy or the route in the way a careless edit would, and
    assert the system notices. A guardrail nothing tests is a comment.
    """

    def setUp(self) -> None:
        self.route = load_route_module()
        template = (SKILL_ROOT / "assets" / "templates" / "calibration"
                    / "routing-policy.json")
        self.data = json.loads(template.read_text(encoding="utf-8"))
        named = set(self.data["full_recipe"]["gate_ids"])
        for rule in self.data["rules"]:
            for gate_ids in rule.get("obligations", {}).values():
                named.update(gate_ids)
        self.gates = named

    def _facts(self, path, policy):
        snap = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(
                path=path, change_kind="modify", source="committed"),),
            base="abc", base_resolved=True)
        return self.route.collect_change_facts(snap, policy["classifier"])

    def test_removing_force_full_from_the_authority_rule_is_detected(self) -> None:
        mutated = json.loads(json.dumps(self.data))
        for rule in mutated["rules"]:
            if rule["id"] == "verification-authority":
                rule["requires"]["force_full"] = False
        policy = self.route.load_policy(mutated, self.gates)
        facts = self._facts(".github/workflows/tests.yml", policy)
        built = self.route.build_route(facts, policy)
        self.assertFalse(built.force_full,
                         "mutation did not take effect; the test proves nothing")
        # The real policy must not behave this way.
        real = self.route.load_policy(self.data, self.gates)
        self.assertTrue(self.route.build_route(
            self._facts(".github/workflows/tests.yml", real), real).force_full)

    def test_reclassifying_skill_md_as_prose_is_detected(self) -> None:
        mutated = json.loads(json.dumps(self.data))
        mutated["classifier"]["surfaces"].insert(
            0, {"glob": "anti-dark-code/SKILL.md", "surface": "docs",
                "effect": "prose", "breadth": "leaf"})
        policy = self.route.load_policy(mutated, self.gates)
        built = self.route.build_route(self._facts("anti-dark-code/SKILL.md", policy), policy)
        self.assertFalse(built.force_full)
        real = self.route.load_policy(self.data, self.gates)
        self.assertTrue(self.route.build_route(
            self._facts("anti-dark-code/SKILL.md", real), real).force_full)

    def test_hints_that_try_to_subtract_are_ignored(self) -> None:
        real = self.route.load_policy(self.data, self.gates)
        built = self.route.build_route(self._facts(".github/workflows/tests.yml", real), real)
        for hostile in ({"force_full": False}, {"minimum_level": 0},
                        {"passes": []}, {"obligations": {}},
                        {"independent_review": False}):
            after = self.route.apply_hints(built, hostile)
            self.assertTrue(after.force_full)
            self.assertGreaterEqual(after.minimum_level, built.minimum_level)
            self.assertTrue(after.passes >= built.passes)

    def test_unknown_path_cannot_be_hinted_into_a_fast_path(self) -> None:
        real = self.route.load_policy(self.data, self.gates)
        snap = self.route.ChangeSnapshot(
            inputs=(self.route.ChangeInput(
                path="totally/unmapped/thing.bin", change_kind="modify", source="committed"),),
            base="abc", base_resolved=True)
        facts = self.route.collect_change_facts(snap, real["classifier"])
        built = self.route.build_route(facts, real)
        self.assertTrue(built.force_full)
        self.assertTrue(self.route.apply_hints(built, {"force_full": False}).force_full)
```

- [ ] **Step 2: Run the tests**

Run: `python -m pytest anti-dark-code/tests/test_route.py::EscalatorMutationTests -q`
Expected: PASS. If any mutation test passes trivially because the mutation had no effect, the assertion `"mutation did not take effect"` fires and tells you the test proves nothing.

- [ ] **Step 3: Run the whole suite and validate**

Run: `python -m pytest anti-dark-code/tests -q`
Expected: PASS on the full suite, well above the 131 baseline.

Run: `python anti-dark-code/scripts/adc.py validate --mode universal`
Expected: `0 errors`.

- [ ] **Step 4: Verify the hygiene rules on everything written**

```bash
grep -rn $'—\|–' anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
grep -rnioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py
```
Expected: both return nothing.

- [ ] **Step 5: Commit**

```bash
git add anti-dark-code/tests/test_route.py
git commit -m "Prove a weakened escalator fails the suite

Each mutation test first asserts the mutation actually took effect, so a
test cannot pass by mutating nothing. Covers removing force_full from the
authority rule, reclassifying SKILL.md as prose, hints that try to
subtract, and hinting an unmapped path onto a fast path."
```

---

## Task 13: Close the slice with evidence

**Files:**
- Modify: `design/routing/SLICE-001-route-shadow.md`, `design/routing/ARCHITECTURE.md`

- [ ] **Step 1: Run every piece of evidence section 9 of the slice brief requires**

```bash
python -m pytest anti-dark-code/tests -q
python anti-dark-code/scripts/adc.py validate --mode universal
python anti-dark-code/scripts/adc.py route --repo . --changed-from origin/main --write
```

Record the actual counts and the receipt path. Do not paraphrase them.

- [ ] **Step 2: Exercise the two required error paths and record what happened**

```bash
python anti-dark-code/scripts/adc.py route --repo . --changed-from refs/heads/does-not-exist
```
Expected: full route with an unreachable-base reason code, or exit 2. Record which.

Temporarily corrupt the calibration `routing-policy.json` with invalid JSON, run the command, confirm exit 2 with no receipt written, then restore the file.

- [ ] **Step 3: Tick section 9 and section 11 of the slice brief with the recorded evidence**

Replace each checkbox with the observed result. A tick with no number beside it is not evidence.

- [ ] **Step 4: Update ADD section 15**

Change the current build boundary to name SLICE-002 as the next brief, and move SLICE-001's modules from "builds" to "built". Set the slice brief status to Done.

- [ ] **Step 5: Commit**

```bash
git add design/routing/
git commit -m "Close SLICE-001 with recorded evidence

Ticks carry observed counts rather than assertions. Error paths for an
unreachable base and an invalid policy were exercised and recorded. The
router explains routes and still cannot skip anything, which was the
whole point of the slice."
```

---

## Self-Review

**Spec coverage.** Incomplete. The round-two execution verified meaningful checks for S-003, S-004, S-006, and part of S-010. S-001, S-002, S-005, S-007 through S-009, and S-011 through S-023 still need stronger or executable checks. A task mention is not coverage. `design/routing/HANDOFF-BACK-PLAN.md` records the criterion-by-criterion gaps.

**Known gaps.** Task 10 describes a before-and-after check but does not show or test it. Task 9 calls `current_route_identity` but does not implement it. Symlink, index, submodule, policy, gates, calibration, repository binding, and concurrent-mutation identity remain unimplemented in this plan.

**Type consistency.** `read_change_inputs` returns `ChangeSnapshot` everywhere. `collect_change_facts(snapshot, classifier)` takes the snapshot, never a repo. `build_route(facts, policy, hints, snapshot_ok)` keeps that order in every call. `receipt_payload` and `verify_receipt` agree on the `identity` mapping shape.

**Placeholder scan.** Failed. Task 9 describes `current_route_identity` without code. Task 10 describes receipt loading, freshness checks, full-recipe selection, and runner integration without code. Task 11 defines a comparator but does not connect it to a full gate run. These are blocking placeholders.

**Plan location.** This plan does not live in `docs/superpowers/plans/`, the skill default, because `docs/` in this repository is the published GitHub Pages site. Writing a plan there would publish it. The same reasoning produced D-015 for the design documents.

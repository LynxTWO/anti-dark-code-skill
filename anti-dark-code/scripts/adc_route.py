#!/usr/bin/env python3
"""Deterministic change-impact routing for Anti-Dark-Code.

This module decides what verification a change requires. It never lowers a
requirement: combination is union and maximum only, so adding a changed file
cannot reduce any part of a route.

Git acquisition is the one impure boundary. Classification and route building
are pure functions over an acquired snapshot, so the monotonic property can be
tested exhaustively without building a repository per case.

Nothing here executes repository code. That is enforced, not assumed: every
git call disables the configuration paths through which a repository can name a
program for git to run. See _GIT_ISOLATION.
"""

from __future__ import annotations

import fnmatch
import re
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

CHANGE_KINDS = frozenset({
    "add", "modify", "delete", "rename", "copy",
    "mode", "type-change", "unmerged", "unknown",
})
CHANGE_SOURCES = frozenset({"committed", "staged", "unstaged", "untracked"})

# Git raw status letters. A letter absent here becomes "unknown" and is
# reported, so an unrecognised record blocks the fast path instead of passing
# as an ordinary modification.
_RAW_STATUS = {
    "A": "add",
    "M": "modify",
    "D": "delete",
    "R": "rename",
    "C": "copy",
    "T": "type-change",
    "U": "unmerged",
}

# Records naming two paths. Git emits the source first, then the destination.
_TWO_PATH_KINDS = frozenset({"rename", "copy"})

# Git writes this mode for the absent side of a creation or deletion.
_NULL_MODE = "000000"

# Header grammar. Git writes a six-digit octal mode, a hex object id of the
# repository's hash width (40 for sha1, 64 for sha256), and a status letter with
# an optional similarity score. Validating the shape is what separates a real
# record from a corrupted or truncated one; without it ":bad bad bad bad M"
# parsed happily and the snapshot claimed to be complete.
_MODE_RE = re.compile(r"\A[0-7]{6}\Z")
_OBJECT_RE = re.compile(r"\A[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\Z")
_STATUS_RE = re.compile(r"\A[A-Z][0-9]{0,3}\Z")


@dataclass(frozen=True)
class ChangeInput:
    """One status-aware record acquired from git before pure classification."""

    path: str
    change_kind: str
    source: str
    old_path: str | None = None
    old_mode: str | None = None
    new_mode: str | None = None
    old_object: str | None = None
    new_object: str | None = None
    mode_changed: bool = False


@dataclass(frozen=True)
class RawParse:
    """Parsed records plus the reason codes for anything that did not parse.

    Problems are carried rather than raised. A malformed record must not be
    silently dropped: routing has to know its picture of the change is
    incomplete so it can refuse to authorize a shortcut.
    """

    inputs: tuple[ChangeInput, ...] = ()
    problems: tuple[str, ...] = ()


def _split_z(payload: bytes) -> tuple[list[str], list[str]]:
    """Split NUL-delimited git output, reporting truncated framing.

    Git terminates every record with NUL, so a nonempty payload that does not
    end in one was cut short. Without this check a truncated transport looked
    exactly like a clean short diff, and the snapshot still claimed to be
    complete.

    surrogateescape keeps a path git emitted that is not valid UTF-8. Losing
    such a path would silently shrink the change set.
    """
    problems: list[str] = []
    if payload and not payload.endswith(b"\x00"):
        problems.append("ADC-ROUTE-UNTERMINATED-PAYLOAD")
    text = payload.decode("utf-8", errors="surrogateescape")
    return [part for part in text.split("\x00") if part != ""], problems


def parse_raw_z(payload: bytes, source: str) -> RawParse:
    """Parse `git diff --raw -z` output into ChangeInput records.

    Raw is required rather than --name-status because only raw carries the mode
    and object columns. Without them a mode-only change cannot be told from a
    content modification, so an executable-bit flip would route lower than it
    should.
    """
    if source not in CHANGE_SOURCES:
        raise ValueError(f"unknown change source: {source}")

    fields, problems = _split_z(payload)
    rows: list[ChangeInput] = []
    index = 0

    while index < len(fields):
        header = fields[index]
        if not header.startswith(":"):
            problems.append("ADC-ROUTE-MALFORMED-RECORD")
            index += 1
            continue

        parts = header[1:].split(" ")
        if len(parts) != 5:
            problems.append("ADC-ROUTE-MALFORMED-RECORD")
            index += 1
            continue

        old_mode, new_mode, old_object, new_object, status = parts
        if not (
            _MODE_RE.match(old_mode) and _MODE_RE.match(new_mode)
            and _OBJECT_RE.match(old_object) and _OBJECT_RE.match(new_object)
            and _STATUS_RE.match(status)
        ):
            problems.append("ADC-ROUTE-MALFORMED-RECORD")
            index += 1
            continue
        kind = _RAW_STATUS.get(status[0], "unknown")
        if kind == "unknown":
            problems.append("ADC-ROUTE-UNKNOWN-STATUS")

        wanted = 2 if kind in _TWO_PATH_KINDS else 1
        if index + wanted >= len(fields):
            problems.append("ADC-ROUTE-TRUNCATED-RECORD")
            break

        if kind in _TWO_PATH_KINDS:
            old_path: str | None = fields[index + 1]
            path = fields[index + 2]
        else:
            old_path = None
            path = fields[index + 1]

        # A file mode moved between two real modes. The null mode 000000 means
        # creation or deletion, which is not a mode transition. This is tracked
        # separately from change_kind because a commit that edits a file and
        # makes it executable has unequal objects, so keying the mode signal off
        # object equality would lose it in exactly that case.
        mode_changed = (
            old_mode != new_mode
            and old_mode not in (None, _NULL_MODE)
            and new_mode not in (None, _NULL_MODE)
        )

        # A pure mode change carries the same object on both sides. Git still
        # reports it as M, so comparing the objects is the only discriminator.
        if kind == "modify" and old_object == new_object and mode_changed:
            kind = "mode"

        rows.append(ChangeInput(
            path=path,
            change_kind=kind,
            source=source,
            old_path=old_path,
            old_mode=old_mode,
            new_mode=new_mode,
            old_object=old_object,
            new_object=new_object,
            mode_changed=mode_changed,
        ))
        index += wanted + 1

    return RawParse(inputs=tuple(rows), problems=tuple(sorted(set(problems))))


def parse_untracked_z(payload: bytes) -> RawParse:
    """Parse `git ls-files --others --exclude-standard -z` output."""
    paths, problems = _split_z(payload)
    rows = tuple(
        ChangeInput(path=path, change_kind="add", source="untracked")
        for path in paths
    )
    return RawParse(inputs=rows, problems=tuple(problems))


# Git will run programs a repository names in its own configuration. This module
# reads untrusted repositories, and pass 00 forbids executing repository code
# during preflight, so every call disables the configuration paths that start a
# program. core.fsmonitor is the demonstrated one: a repository pointing it at a
# script gets that script run by our acquisition. diff.external is disabled for
# the same reason. --no-optional-locks keeps a read from writing to the repo.
#
# Treat this list as load-bearing. Any new git option or subcommand must be
# checked for another executable configuration path before it is added.
_GIT_ISOLATION = (
    "--no-optional-locks",
    "-c", "core.fsmonitor=false",
    "-c", "diff.external=",
    # Detection silently degrades past a default budget of 1000 paths, which
    # would drop rename and copy provenance without saying so. 0 is unlimited.
    "-c", "diff.renameLimit=0",
)

# Rename and copy detection, plus full object ids. Without -C a copy arrives as
# an add and its source path is lost. Without --no-abbrev the object ids are
# seven characters, which is weaker identity than a receipt should bind.
# --no-ext-diff refuses an external diff driver even if one is configured.
# --find-copies-harder is required, not optional: plain -C only considers
# sources that changed in the same commit, so copying an unchanged sensitive
# file arrives as an ordinary add with no source path at all.
_DIFF_FLAGS = (
    "--no-ext-diff", "--raw", "-z", "--no-abbrev",
    "-M", "-C", "--find-copies-harder",
)


def _isolated(args: Sequence[str]) -> list[str]:
    """Prefix the isolation flags. Every git call goes through here."""
    return [*_GIT_ISOLATION, *args]


@dataclass(frozen=True)
class ChangeSnapshot:
    """Every routing-relevant record for one comparison, plus what went wrong."""

    inputs: tuple[ChangeInput, ...] = ()
    base: str | None = None
    base_resolved: bool = False
    problems: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        """True only when the whole change was read. Anything else blocks a shortcut."""
        return self.base_resolved and not self.problems


def _default_runner(repo: Path):
    def run(args: list[str]) -> bytes | None:
        try:
            environment = dict(os.environ)
            environment["GIT_OPTIONAL_LOCKS"] = "0"
            done = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, timeout=30, check=False, env=environment,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            return None
        return done.stdout
    return run


def read_change_inputs(repo: Path, base: str, runner=None) -> ChangeSnapshot:
    """Acquire every routing-relevant git record. The one impure boundary.

    This deliberately does not call adc.changed_files(). That helper filters the
    skill trees and .anti-dark-code through TOOLING_PATH_PREFIXES, which is
    exactly where gates.json and routing-policy.json live, so reusing it would
    leave the router blind to its own escalators. It is also --name-only, so it
    carries no rename, delete, copy, or mode information. See D-010.
    """
    run = runner or _default_runner(repo)
    problems: list[str] = []
    rows: list[ChangeInput] = []

    # A zero exit is not proof of a usable base. Whitespace, an empty result,
    # or several ids all reached here as "resolved" with an empty or ambiguous
    # id, and the snapshot then claimed to be complete.
    merge_base_raw = run(_isolated(["merge-base", base, "HEAD"]))
    merge_base: str | None = None
    if merge_base_raw is not None:
        candidates = merge_base_raw.decode("utf-8", "replace").split()
        if len(candidates) == 1 and _OBJECT_RE.match(candidates[0]):
            merge_base = candidates[0]
    base_resolved = merge_base is not None
    if not base_resolved:
        problems.append("ADC-ROUTE-BASE-UNREACHABLE")

    def collect(args: list[str], source: str, unreadable_code: str) -> None:
        payload = run(_isolated(args))
        if payload is None:
            problems.append(unreadable_code)
            return
        parsed = parse_raw_z(payload, source)
        rows.extend(parsed.inputs)
        problems.extend(parsed.problems)

    if merge_base:
        collect(["diff", *_DIFF_FLAGS, merge_base, "HEAD"],
                "committed", "ADC-ROUTE-COMMITTED-UNREADABLE")

    # The index against HEAD. `diff --cached` is the only comparison that
    # isolates what is staged.
    collect(["diff", *_DIFF_FLAGS, "--cached"],
            "staged", "ADC-ROUTE-STAGED-UNREADABLE")

    # The worktree against the index. `diff HEAD` would return staged and
    # unstaged records together and count every staged change twice.
    collect(["diff", *_DIFF_FLAGS],
            "unstaged", "ADC-ROUTE-UNSTAGED-UNREADABLE")

    untracked = run(_isolated(["ls-files", "--others", "--exclude-standard", "-z"]))
    if untracked is None:
        problems.append("ADC-ROUTE-UNTRACKED-UNREADABLE")
    else:
        parsed_untracked = parse_untracked_z(untracked)
        rows.extend(parsed_untracked.inputs)
        problems.extend(parsed_untracked.problems)

    ordered = tuple(sorted(rows, key=lambda r: (r.source, r.path, r.change_kind)))
    return ChangeSnapshot(
        inputs=ordered,
        base=merge_base,
        base_resolved=base_resolved,
        problems=tuple(sorted(set(problems))),
    )


SURFACES = frozenset({
    "docs", "product", "tests", "schema", "ci", "release", "skill-policy", "site",
})
EFFECTS = frozenset({
    "prose", "behavior", "public-contract", "persisted-state", "verification-authority",
})
BREADTHS = frozenset({"leaf", "package", "runtime", "cross-runtime", "repository"})
SENSITIVITIES = frozenset({
    "normal", "auth", "privacy", "billing", "deletion", "crypto", "release",
})
CONFIDENCES = frozenset({"verified", "inferred", "unknown"})


@dataclass(frozen=True)
class ChangeFact:
    """One dimensioned statement about one changed path."""

    path: str
    change_kind: str
    source: str
    surface: str
    effect: str
    breadth: str
    sensitivity: str
    confidence: str
    related_path: str | None = None
    mode_changed: bool = False


def _matching_classifications(
    path: str, classifier: Mapping[str, Any]
) -> list[dict[str, str]]:
    """Every classifier entry whose glob matches, not merely the first.

    First-match-wins would let a broad early entry mask a specific later one: a
    "*.md" rule calling everything prose would hide the entry that calls
    SKILL.md verification authority. Emitting one fact per matching entry keeps
    both readings, so every rule that would fire does fire and the monotonic
    union in build_route decides the rest. No arbitrary precedence is invented.
    """
    matches: list[dict[str, str]] = []
    for entry in classifier.get("surfaces", []):
        if fnmatch.fnmatch(path, entry["glob"]):
            matches.append({
                "surface": entry["surface"],
                "effect": entry["effect"],
                "breadth": entry.get("breadth", "leaf"),
                "sensitivity": entry.get("sensitivity", "normal"),
                "confidence": "verified",
            })
    return matches


# An unmapped path is not a low-risk path. Confidence unknown is what makes the
# route builder refuse a fast path it has not earned.
_UNMAPPED = {
    "surface": "product",
    "effect": "behavior",
    "breadth": "repository",
    "sensitivity": "normal",
    "confidence": "unknown",
}


def collect_change_facts(
    snapshot: ChangeSnapshot, classifier: Mapping[str, Any]
) -> tuple[ChangeFact, ...]:
    """Pure classification of an acquired snapshot into dimensioned facts.

    Rename and copy records classify both paths. Dropping the source path would
    let a move out of a sensitive location route as though only the destination
    mattered.
    """
    facts: list[ChangeFact] = []
    for row in snapshot.inputs:
        sides: list[tuple[str, str | None]] = [(row.path, row.old_path)]
        if row.change_kind in _TWO_PATH_KINDS and row.old_path:
            sides.append((row.old_path, row.path))
        for path, related in sides:
            for attrs in _matching_classifications(path, classifier) or [_UNMAPPED]:
                facts.append(ChangeFact(
                    path=path,
                    related_path=related,
                    change_kind=row.change_kind,
                    source=row.source,
                    mode_changed=row.mode_changed,
                    **attrs,
                ))
    return tuple(sorted(
        set(facts),
        key=lambda f: (f.path, f.source, f.change_kind, f.surface, f.effect,
                       f.breadth, f.sensitivity, f.confidence),
    ))

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
import hashlib
import json
import weakref
import re
import os
import subprocess
from dataclasses import dataclass, field
from types import MappingProxyType
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
# Git writes a closed set of modes, not any six octal digits. 000000 is the
# absent side of a creation or deletion.
_GIT_MODES = frozenset({"000000", "100644", "100755", "120000", "160000", "040000"})
_OBJECT_RE = re.compile(r"\A[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\Z")
_STATUS_RE = re.compile(r"\A([A-Z])([0-9]{1,3})?\Z")
# Only copy and rename carry a similarity score, and only 0 through 100.
_SCORED_STATUSES = frozenset({"C", "R"})


# Which sides a status has. An add has no old side and a delete no new side.
#
# U is deliberately absent, meaning any shape. A real merge conflict writes
# :000000 100644 <zeros> <obj> U, with the old side null, and requiring both
# sides real reported every conflict in a repository mid-merge as malformed.
# Unmerged entries have their own semantics and more than one shape, and losing
# a path is worst exactly when the tree is in its most delicate state.
_STATUS_SIDES = {
    "A": (False, True), "D": (True, False),
    "M": (True, True), "R": (True, True), "C": (True, True),
    "T": (True, True),
}


def _valid_raw_header(
    old_mode: str, new_mode: str, old_object: str, new_object: str, status: str,
    width: int | None = None,
) -> bool:
    """Check the record grammar git actually writes, not merely its shape.

    Character-class checks accepted records git cannot emit: mode 777777,
    status A100, a similarity score of 999, and one 40-digit object beside one
    64-digit object in the same record. Each of those would have been parsed as
    a real change and marked complete.
    """
    if old_mode not in _GIT_MODES or new_mode not in _GIT_MODES:
        return False
    if not _OBJECT_RE.match(old_object) or not _OBJECT_RE.match(new_object):
        return False
    # A repository has one hash width, so both sides of a record must agree,
    # and so must every record in one payload. Checking only within a record
    # let a single payload carry a 40-digit pair beside a 64-digit pair.
    if len(old_object) != len(new_object):
        return False
    if width is not None and len(old_object) != width:
        return False
    # A null mode means the side does not exist, so its object must be null
    # too. The converse does not hold: for a worktree comparison git writes a
    # null object with a real mode, because it has not hashed the file. A real
    # unstaged record looks like
    # ":100644 100644 <obj> 0000000000000000000000000000000000000000 M path".
    null = "0" * len(old_object)
    if old_mode == _NULL_MODE and old_object != null:
        return False
    if new_mode == _NULL_MODE and new_object != null:
        return False
    matched = _STATUS_RE.match(status)
    if not matched:
        return False
    letter, score = matched.group(1), matched.group(2)

    sides = _STATUS_SIDES.get(letter)
    if sides is None:
        # An unrecognised letter is reported separately and keeps its row, so
        # the router still knows the path changed. Rejecting it here would
        # discard the path entirely, which is a worse outcome than an unknown
        # kind that forces the full route.
        return True
    null = "0" * len(old_object)
    has_old, has_new = (old_object != null), (new_object != null)
    if (has_old, has_new) != sides:
        # A worktree comparison writes a null new object with a real mode,
        # because git has not hashed the file. That is the one legitimate
        # exception to the new side existing.
        if not (sides == (True, True) and has_old and new_mode != _NULL_MODE):
            return False

    if letter in _SCORED_STATUSES:
        # Git always writes a similarity score on a copy or a rename.
        return score is not None and 0 <= int(score) <= 100
    return score is None


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
    # Established by the first well-formed record and enforced on the rest.
    width: int | None = None

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
        if not _valid_raw_header(
            old_mode, new_mode, old_object, new_object, status, width
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

        if width is None:
            width = len(old_object)

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


def _filter_overrides(run) -> list[str]:
    """Neutralize every content filter this repository can see.

    Only the worktree comparison converts content, and conversion is what runs
    a `filter.<driver>.clean` program. Drivers are discovered by reading config,
    which is data rather than execution, and each is overridden to no command
    with required=false. Global drivers such as git-lfs are found the same way,
    because `git config --get-regexp` reports the effective configuration.

    Discovery is used instead of a fixed key list because a fixed list is what
    failed twice: core.fsmonitor was closed, then diff.external, and filters
    were still open. This enumerates what the repository actually declares.
    """
    payload = run([*_GIT_ISOLATION, "config", "--get-regexp", r"^filter\."])
    overrides: list[str] = []
    if not payload:
        return overrides
    names: set[str] = set()
    for line in payload.decode("utf-8", "replace").splitlines():
        key = line.split(" ", 1)[0]
        parts = key.split(".")
        if len(parts) >= 3 and parts[0] == "filter":
            names.add(".".join(parts[1:-1]))
    for name in sorted(names):
        overrides.extend([
            "-c", f"filter.{name}.clean=",
            "-c", f"filter.{name}.smudge=",
            "-c", f"filter.{name}.process=",
            "-c", f"filter.{name}.required=false",
        ])
    return overrides


def _isolated(args: Sequence[str], extra: Sequence[str] = ()) -> list[str]:
    """Prefix the isolation flags. Every git call goes through here."""
    return [*_GIT_ISOLATION, *extra, *args]


def _repo_fingerprint(repo: Path, run) -> tuple[Any, ...]:
    """Cheap evidence that acquisition changed nothing.

    The set of configuration keys through which git can start a program cannot
    be proven complete, so the boundary is checked rather than asserted. If a
    path nobody neutralized runs something that touches the repository, this
    moves and the snapshot refuses to call itself complete.

    Scope is what git reports, tracked plus untracked-not-ignored, rather than
    a walk of the directory tree. Walking everything cost 14.4 seconds on a real
    345-file repository because it crawled 62,245 build artifacts. The narrower
    scope misses a write into an ignored directory, which is an accepted limit:
    an ignored path is not part of the change set and cannot alter a route.
    """
    index = repo / ".git" / "index"
    try:
        stat = index.stat()
        index_state: Any = (stat.st_size, stat.st_mtime_ns)
    except OSError:
        index_state = None

    listed: list[str] = []
    for args in (["ls-files", "-z"],
                 ["ls-files", "--others", "--exclude-standard", "-z"]):
        payload = run(_isolated(args))
        if payload is None:
            return ("unreadable",)
        listed.extend(_split_z(payload)[0])

    # Content and metadata, because neither alone is sufficient. Size and mtime
    # can both be preserved across a rewrite, so a write timed after its own
    # comparison was invisible to metadata. Content alone is equally blind to a
    # rewrite with identical bytes, which only moves the timestamp. Recording
    # both means any one of the three moving is enough.
    #
    # Measured cost of hashing every tracked file: 0.012s at 104 files, 0.038s
    # at 345, 0.273s at 3000.
    entries: list[tuple[str, int, int, str]] = []
    for relative in listed:
        path = repo / relative
        try:
            stat = path.stat()
            size, mtime = stat.st_size, stat.st_mtime_ns
        except OSError:
            entries.append((relative, -1, -1, "unreadable"))
            continue
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
        except OSError:
            entries.append((relative, size, mtime, "unreadable"))
            continue
        entries.append((relative, size, mtime, digest.hexdigest()))
    return (index_state, tuple(sorted(entries)))


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
            # A partial clone fetches a missing object on demand, so a read can
            # reach the network and write an object. fetch.negotiationAlgorithm
            # only chooses a negotiation strategy and prevents nothing; this is
            # the control that does. A missing promisor object then fails the
            # command, which acquisition already reports as unreadable.
            environment["GIT_NO_LAZY_FETCH"] = "1"
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
    before = _repo_fingerprint(repo, run)
    # Only the worktree comparison converts content, so only it can start a
    # filter driver. The other three read objects or names and are safe by
    # construction; paying for discovery on them would be theatre.
    worktree_isolation = _filter_overrides(run)

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

    def collect(args: list[str], source: str, unreadable_code: str,
                extra: Sequence[str] = ()) -> None:
        payload = run(_isolated(args, extra))
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
    # unstaged records together and count every staged change twice. This is
    # the one comparison that reads worktree bytes, so it carries the filter
    # overrides and refuses an external text converter.
    collect(["diff", *_DIFF_FLAGS, "--no-textconv"],
            "unstaged", "ADC-ROUTE-UNSTAGED-UNREADABLE",
            extra=worktree_isolation)

    untracked = run(_isolated(["ls-files", "--others", "--exclude-standard", "-z"]))
    if untracked is None:
        problems.append("ADC-ROUTE-UNTRACKED-UNREADABLE")
    else:
        parsed_untracked = parse_untracked_z(untracked)
        rows.extend(parsed_untracked.inputs)
        problems.extend(parsed_untracked.problems)

    if _repo_fingerprint(repo, run) != before:
        problems.append("ADC-ROUTE-BOUNDARY-VIOLATED")

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


# Every dimension and the frozenset that closes it. Declaring the sets without
# checking them let a one-character policy typo silently change which rules
# matched, which is the quietest way a route can go wrong.
_FACT_DIMENSIONS = (
    ("surface", SURFACES),
    ("effect", EFFECTS),
    ("breadth", BREADTHS),
    ("sensitivity", SENSITIVITIES),
    ("confidence", CONFIDENCES),
)


def _validated_classification(entry: Mapping[str, Any], attrs: dict[str, str]) -> dict[str, str]:
    for field, allowed in _FACT_DIMENSIONS:
        value = attrs[field]
        if value not in allowed:
            raise ValueError(
                f"classifier entry {entry.get('glob', '<no glob>')!r} has "
                f"{field}={value!r}; allowed: {sorted(allowed)}"
            )
    return attrs


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
        glob = entry.get("glob")
        if not glob:
            raise ValueError(f"classifier entry has no glob: {entry!r}")
        # fnmatchcase, not fnmatch. fnmatch applies os.path.normcase, so the
        # same policy and diff would match case-insensitively on Windows and
        # case-sensitively elsewhere, producing different facts and therefore
        # different receipts per host. Git paths are case-sensitive, so that is
        # the semantics the router commits to everywhere. Separators are
        # normalized first so a policy needs one spelling per rule.
        # Patterns and paths both live in git's path space, which uses forward
        # slashes on every platform. Rewriting backslashes was unnecessary for
        # real git output and corrupted a legal POSIX filename containing one.
        if not fnmatch.fnmatchcase(path, glob):
            continue
        matches.append(_validated_classification(entry, {
            "surface": entry.get("surface", ""),
            "effect": entry.get("effect", ""),
            "breadth": entry.get("breadth", "leaf"),
            "sensitivity": entry.get("sensitivity", "normal"),
            "confidence": "verified",
        }))
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


def _fact_sort_key(fact: ChangeFact) -> tuple[Any, ...]:
    """Total order over every serialized field.

    Any field left out of this key is a field two facts can tie on, and a tie is
    broken by set iteration order rather than deterministically.
    """
    return (
        fact.path, fact.related_path or "", fact.source, fact.change_kind,
        fact.surface, fact.effect, fact.breadth, fact.sensitivity,
        fact.confidence, fact.mode_changed,
    )


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
        if row.change_kind not in CHANGE_KINDS:
            raise ValueError(f"unknown change kind: {row.change_kind!r}")
        if row.source not in CHANGE_SOURCES:
            raise ValueError(f"unknown change source: {row.source!r}")
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
    # Every field participates in the key. Leaving one out let two otherwise
    # identical facts tie, and the tie was then broken by set iteration order,
    # which varies with the process hash seed. A router whose output depends on
    # the hash seed cannot produce a byte-stable receipt.
    return tuple(sorted(set(facts), key=_fact_sort_key))


@dataclass(frozen=True)
class Route:
    """What one change requires. Every field is a floor, never a ceiling."""

    minimum_level: int = 0
    passes: frozenset[str] = frozenset()
    obligations: Mapping[str, frozenset[str]] = field(default_factory=dict)
    matched_rule_ids: frozenset[str] = frozenset()
    force_full: bool = False
    independent_review: bool = False
    unmapped_paths: frozenset[str] = frozenset()
    unknowns: frozenset[str] = frozenset()


# Rule match keys. Positive predicates only: a rule may not depend on the
# absence, count, or ordering of other facts. A negative predicate would break
# monotonicity, because adding a file could stop a rule firing. See R-015.
_MATCH_KEYS = frozenset({
    "paths", "surfaces", "effects", "breadths", "sensitivities",
    "change_kinds", "sources", "mode_changed",
})


def _fact_matches(fact: ChangeFact, match: Mapping[str, Any]) -> bool:
    """One fact against one rule. Every named predicate must hold."""
    unknown = set(match) - _MATCH_KEYS
    if unknown:
        raise ValueError(f"rule uses unsupported match keys: {sorted(unknown)}")
    if "paths" in match:
        # Git path space, verbatim. See the note in _matching_classifications.
        if not any(fnmatch.fnmatchcase(fact.path, p) for p in match["paths"]):
            return False
    for key, attribute in (
        ("surfaces", "surface"), ("effects", "effect"), ("breadths", "breadth"),
        ("sensitivities", "sensitivity"), ("change_kinds", "change_kind"),
        ("sources", "source"),
    ):
        if key in match and getattr(fact, attribute) not in match[key]:
            return False
    if "mode_changed" in match and fact.mode_changed is not bool(match["mode_changed"]):
        return False
    return True


def _union_obligations(
    into: dict[str, set[str]], more: Mapping[str, Sequence[str]]
) -> dict[str, set[str]]:
    """Union gate sets per capability.

    Assignment here would be a silent coverage loss: two rules naming the same
    capability with different gates would leave one gate behind, and the route
    would claim a capability was covered by work it never selected.
    """
    for capability, gate_ids in more.items():
        into.setdefault(capability, set()).update(gate_ids)
    return into


def build_route(
    facts: Sequence[ChangeFact],
    policy: ValidatedPolicy,
    hints: Mapping[str, Any] | None = None,
    snapshot_ok: bool = True,
) -> Route:
    """Combine every matching rule's requirements. Union and maximum only.

    Averaging or subtraction would let unrelated low-risk facts dilute a
    critical trigger: thirty README lines cannot cancel one authentication
    schema change. Adding a fact must never reduce any field, which is the
    property R-001 tests and the reason there is no numeric score.
    """
    # A plain mapping has never been validated. Accepting one would let a
    # caller skip load_policy, and would reopen the aliasing hole where a rule
    # is edited from proposed to approved after review.
    if not isinstance(policy, ValidatedPolicy):
        raise TypeError(
            "build_route requires a ValidatedPolicy from load_policy, "
            f"not {type(policy).__name__}"
        )
    if not _is_validated(policy):
        raise TypeError(
            "this ValidatedPolicy was not returned by load_policy. The type is "
            "constructible and dataclasses.replace copies every field, so "
            "neither the class nor a stored token proves it was validated"
        )

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

    rules = [rule for rule in policy.rules if rule.approved]

    for fact in facts:
        if fact.confidence == "unknown":
            # An unknown does not mean the code is bad. It means the shortcut
            # has not been earned.
            unmapped.add(fact.path)
            unknowns.add("ADC-ROUTE-UNMAPPED-PATH")
            force_full = True
        fired = False
        for rule in rules:
            if not _fact_matches(fact, rule.match_map()):
                continue
            fired = True
            matched.add(rule.id)
            level = max(level, rule.minimum_level)
            passes.update(rule.passes)
            force_full = force_full or rule.force_full
            independent_review = independent_review or rule.independent_review
            _union_obligations(obligations, rule.obligation_map())
        if not fired:
            # A classified fact that no reviewed rule describes is an unrouted
            # change, not a cheap one.
            unmapped.add(fact.path)
            unknowns.add("ADC-ROUTE-UNROUTED-FACT")
            force_full = True

    if force_full:
        # The full route is the policy's own reviewed recipe, not merely a
        # higher level. Raising the level alone would leave a route labelled
        # full that still selected the cheap rule's gates.
        recipe = policy.full_recipe
        level = max(level, recipe.minimum_level)
        passes.update(recipe.passes)
        _union_obligations(obligations, recipe.obligation_map())
        independent_review = independent_review or recipe.independent_review

    route = Route(
        minimum_level=level,
        passes=frozenset(passes),
        # Sorted, so the mapping has one order for a given set of obligations.
        # Equality hid the difference; a serializer would not have.
        # Read-only. A frozen dataclass holding a plain dict still let a
        # caller clear authority data after the route was computed.
        obligations=MappingProxyType(
            {k: frozenset(obligations[k]) for k in sorted(obligations)}),
        matched_rule_ids=frozenset(matched),
        force_full=force_full,
        independent_review=independent_review,
        unmapped_paths=frozenset(unmapped),
        unknowns=frozenset(unknowns),
    )
    return apply_hints(route, hints, policy) if hints else route


# Fields a hint may write. The rest record what the router observed, and a
# hint is judgement rather than evidence, so it must not author them.
_HINT_FIELDS = frozenset({
    "minimum_level", "passes", "obligations", "force_full", "independent_review",
})


def apply_hints(
    route: Route, hints: Mapping[str, Any], policy: ValidatedPolicy
) -> Route:
    """Apply agent hints. Additive only, and only over reviewed vocabulary.

    A hint may add set members, raise the level, or set a boolean true. It may
    not remove, lower, or clear anything, and it cannot invent a pass, a
    capability, or a gate: without that check an agent could name evidence no
    policy defines and the route would carry it. An agent that believes a route
    is too heavy has no recourse here by design, because only a reviewed rule
    backed by deterministic evidence may permit less work. See D-006 and R-020.
    """
    unsupported = set(hints) - _HINT_FIELDS
    if unsupported:
        raise HintError(
            f"hints may not write {sorted(unsupported)}: those fields record what "
            "the router observed, not what an agent believes"
        )

    # Types are checked, not coerced. int() accepted 999 and any numeric
    # string, and bool("false") is True, so a string inverted a flag.
    if "minimum_level" in hints:
        level = hints["minimum_level"]
        if isinstance(level, bool) or not isinstance(level, int) or level not in _LEVELS:
            raise HintError(
                f"hint minimum_level must be one of {sorted(_LEVELS)}, "
                f"not {level!r}")
    for flag in ("force_full", "independent_review"):
        if flag in hints and not isinstance(hints[flag], bool):
            raise HintError(f"hint {flag} must be true or false, not {hints[flag]!r}")
    if "passes" in hints and not isinstance(hints["passes"], (list, tuple)):
        raise HintError("hint passes must be a list")
    for pass_id in hints.get("passes", []):
        if pass_id not in _PASS_IDS:
            raise HintError(f"hint names unknown pass {pass_id!r}")

    # Pairs, not two separate unions. Checking capability membership and gate
    # membership independently let a hint bind a capability to a gate no
    # reviewed rule ever paired with it. Proposed rules are excluded: a rule
    # that never matches is not reviewed authority and must not widen this.
    reviewed_pairs: set[tuple[str, str]] = {
        (capability, gate)
        for capability, gates in policy.full_recipe.obligations
        for gate in gates
    }
    for rule in policy.rules:
        if not rule.approved:
            continue
        for capability, gates in rule.obligations:
            reviewed_pairs.update((capability, gate) for gate in gates)
    hinted = hints.get("obligations", {})
    if not isinstance(hinted, Mapping):
        raise HintError("hint obligations must be an object")
    for capability, gate_ids in hinted.items():
        if not isinstance(gate_ids, (list, tuple)):
            raise HintError(f"hint obligation {capability} must name a list of gates")
        for gate_id in gate_ids:
            if (capability, gate_id) not in reviewed_pairs:
                raise HintError(
                    f"hint pairs capability {capability!r} with gate {gate_id!r}, "
                    "which no approved rule or the full recipe binds together"
                )

    merged = {k: set(v) for k, v in route.obligations.items()}
    _union_obligations(merged, hints.get("obligations", {}))
    return Route(
        minimum_level=max(route.minimum_level, int(hints.get("minimum_level", 0))),
        passes=route.passes | frozenset(hints.get("passes", [])),
        obligations=MappingProxyType(
            {k: frozenset(merged[k]) for k in sorted(merged)}),
        # Rule matches are evidence of what fired, not a requirement a hint may
        # add to. Letting a hint write here would let an agent claim a reviewed
        # rule matched when it did not.
        matched_rule_ids=route.matched_rule_ids,
        force_full=route.force_full or bool(hints.get("force_full")),
        independent_review=(
            route.independent_review or bool(hints.get("independent_review"))
        ),
        unmapped_paths=route.unmapped_paths,
        unknowns=route.unknowns,
    )


@dataclass(frozen=True)
class ValidatedRule:
    """One reviewed rule, frozen at load so it cannot change afterwards."""

    id: str
    approved: bool
    match: tuple[tuple[str, Any], ...]
    passes: frozenset[str]
    minimum_level: int
    force_full: bool
    independent_review: bool
    obligations: tuple[tuple[str, frozenset[str]], ...]

    def match_map(self) -> dict[str, Any]:
        return dict(self.match)

    def obligation_map(self) -> dict[str, frozenset[str]]:
        return dict(self.obligations)


@dataclass(frozen=True)
class ValidatedRecipe:
    minimum_level: int
    passes: frozenset[str]
    independent_review: bool
    obligations: tuple[tuple[str, frozenset[str]], ...]

    def obligation_map(self) -> dict[str, frozenset[str]]:
        return dict(self.obligations)


# Registry of values load_policy actually produced, keyed by identity.
#
# A token stored on the value was not enough: dataclasses.replace copies every
# field, so a tampered policy carrying a Level 0 recipe and a cheap approved
# rule kept the token and routed cheap. A token proves what was stamped, not
# what was checked. Recording the identity of the exact object the loader
# returned means a replaced copy is a different object and is refused.
#
# Keyed by object identity, not equality. A WeakSet keys by hash and equality,
# so two equal policies share one entry and collecting either removes it for
# both. Identity is what provenance means here: this exact object came back
# from load_policy. Weak values keep a policy that goes out of scope from
# pinning memory.
#
# This proves provenance, not correctness. It says load_policy returned this
# object, which is what the check needs to say and no more.
_VALIDATED_POLICIES: "weakref.WeakValueDictionary[int, ValidatedPolicy]" = (
    weakref.WeakValueDictionary()
)


def _is_validated(policy: ValidatedPolicy) -> bool:
    return _VALIDATED_POLICIES.get(id(policy)) is policy


@dataclass(frozen=True)
class ValidatedPolicy:
    """A routing policy that has been checked and can no longer change.

    build_route accepts only this type. A plain mapping has never been
    validated, and load_policy previously returned a shallow copy, so a caller
    could flip a nested rule from proposed to approved after validation and turn
    a forced-full route into a cheap one. Freezing the nested records and
    demanding this type at the boundary closes both halves of that.
    """

    schema_version: int
    classifier: tuple[tuple[tuple[str, str], ...], ...]
    full_recipe: ValidatedRecipe
    rules: tuple[ValidatedRule, ...]

    def classifier_map(self) -> dict[str, Any]:
        return {"surfaces": [dict(entry) for entry in self.classifier]}


class PolicyError(Exception):
    """A routing policy that cannot be trusted.

    Loading never falls back to a default. A policy that cannot be validated
    produces no route at all, and the caller uses the documented full
    verification path outside the router.
    """


# Passes 00 through 16 exist in references/. A rule naming anything else is a
# typo, and a typo that silently names no pass would quietly drop work.
_PASS_IDS = frozenset(f"{n:02d}" for n in range(0, 17))
_LEVELS = frozenset({0, 1, 2, 3})


def _usable_gate_ids(gates: Mapping[str, Any]) -> set[str]:
    """Gate ids that could actually run.

    A gate that is disabled will never execute, and a gate nobody approved must
    not execute, so neither can satisfy a capability. Treating them as coverage
    would let a route report an obligation as met by work that cannot happen.
    """
    entries = gates.get("gates", [])
    seen: set[str] = set()
    duplicates: set[str] = set()
    usable: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or not entry.get("id"):
            raise PolicyError("gate configuration contains an entry with no id")
        gate_id = str(entry["id"])
        if gate_id in seen:
            duplicates.add(gate_id)
        seen.add(gate_id)
        if (entry.get("enabled") is True
                and str(entry.get("review_status", "")).lower() == "approved"):
            usable.add(gate_id)
    if duplicates:
        raise PolicyError(
            f"gate configuration has duplicate ids: {sorted(duplicates)}")
    return usable


def _check_obligations(
    where: str, obligations: Any, usable_gate_ids: set[str], capability_ids: set[str]
) -> None:
    if not isinstance(obligations, Mapping):
        raise PolicyError(f"{where}: obligations must be an object")
    for capability, gate_ids in obligations.items():
        if capability not in capability_ids:
            raise PolicyError(f"{where}: unknown capability id {capability!r}")
        if not isinstance(gate_ids, list) or not gate_ids:
            raise PolicyError(
                f"{where}: capability {capability} needs a nonempty gate list")
        for gate_id in gate_ids:
            if gate_id not in usable_gate_ids:
                raise PolicyError(
                    f"{where}: capability {capability} names gate {gate_id!r}, "
                    "which is unknown, disabled, or unapproved"
                )


# Which closed set each plural predicate draws from. Validating membership
# stops a policy typo from naming a value no fact can ever carry, which would
# make the rule silently dead rather than obviously wrong.
_PREDICATE_SETS = {
    "surfaces": SURFACES,
    "effects": EFFECTS,
    "breadths": BREADTHS,
    "sensitivities": SENSITIVITIES,
    "change_kinds": CHANGE_KINDS,
    "sources": CHANGE_SOURCES,
}


def _check_match(where: str, match: Any) -> None:
    """Validate predicate shapes as well as keys.

    A string is iterable, so `paths: "*.md"` was read as a list of single
    characters and its "*" matched every path. That handed unrelated files a
    cheap rule, which is a routing bypass rather than a cosmetic problem.
    """
    if not isinstance(match, Mapping) or not match:
        raise PolicyError(f"{where}: needs a nonempty match")
    unknown = set(match) - _MATCH_KEYS
    if unknown:
        raise PolicyError(
            f"{where}: unsupported match keys {sorted(unknown)}. Rules match one "
            "fact with positive predicates only, because a rule keyed on the "
            "absence of another fact would stop firing when a file is added"
        )
    for key, value in match.items():
        if key == "mode_changed":
            # bool("false") is True, so a string here inverts the predicate.
            if not isinstance(value, bool):
                raise PolicyError(f"{where}: mode_changed must be true or false")
            continue
        if not isinstance(value, list) or not value:
            raise PolicyError(
                f"{where}: {key} must be a nonempty list, not {type(value).__name__}")
        for member in value:
            if not isinstance(member, str) or not member:
                raise PolicyError(f"{where}: {key} contains a non-string member")
            allowed = _PREDICATE_SETS.get(key)
            if allowed is not None and member not in allowed:
                raise PolicyError(
                    f"{where}: {key} member {member!r} is not one of {sorted(allowed)}")


def _check_requires(where: str, requires: Any) -> None:
    if not isinstance(requires, Mapping):
        raise PolicyError(f"{where}: requires must be an object")
    level = requires.get("minimum_level", 0)
    if not isinstance(level, int) or isinstance(level, bool) or level not in _LEVELS:
        raise PolicyError(f"{where}: minimum_level must be one of {sorted(_LEVELS)}")
    passes = requires.get("passes", [])
    if not isinstance(passes, list):
        raise PolicyError(f"{where}: passes must be an array")
    for pass_id in passes:
        if pass_id not in _PASS_IDS:
            raise PolicyError(f"{where}: unknown pass id {pass_id!r}")
    for flag in ("force_full", "independent_review"):
        if flag in requires and not isinstance(requires[flag], bool):
            raise PolicyError(f"{where}: {flag} must be true or false")


def _freeze_obligations(
    obligations: Mapping[str, Any]
) -> tuple[tuple[str, frozenset[str]], ...]:
    """Sorted by capability, so a policy has one canonical shape."""
    return tuple(sorted(
        (capability, frozenset(gate_ids))
        for capability, gate_ids in obligations.items()
    ))


class HintError(Exception):
    """A hint that names something no policy or catalog defines."""


def capability_ids_from_catalog(path: Path) -> frozenset[str]:
    """Read the capability ids from the shipped catalog.

    The catalog file is the source of truth. Guessing the range here is what
    put a count literal back after D-029 removed the others.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return frozenset(entry["id"] for entry in data["capabilities"])


def load_policy(
    data: Mapping[str, Any],
    gates: Mapping[str, Any],
    capability_ids: Sequence[str],
    full_set: Mapping[str, Any] | None = None,
) -> ValidatedPolicy:
    """Validate a routing policy and freeze it.

    Validating at load rather than only at route time means a bad policy fails
    before it can route anything. The result is a frozen ValidatedPolicy built
    from copies, so nothing the caller still holds can change what was reviewed.
    A shallow copy was not enough: flipping a nested rule from proposed to
    approved after validation turned a forced-full route into a cheap one.

    A rule whose review_status is not approved still loads. The shipped template
    ships every rule proposed so an installing repository has to read and
    approve each one, and an unapproved rule simply never matches. See D-022.
    """
    if not isinstance(data, Mapping):
        raise PolicyError("routing policy must be an object")
    if data.get("schema_version") != 1:
        raise PolicyError("routing policy schema_version must be 1")

    known_capabilities = set(capability_ids)
    if not known_capabilities:
        raise PolicyError("a capability catalog is required to validate a policy")
    usable = _usable_gate_ids(gates)

    classifier = data.get("classifier", {})
    if not isinstance(classifier, Mapping):
        raise PolicyError("classifier must be an object")
    frozen_classifier: list[tuple[tuple[str, str], ...]] = []
    for entry in classifier.get("surfaces", []):
        if not isinstance(entry, Mapping) or not entry.get("glob"):
            raise PolicyError(f"classifier entry has no glob: {entry!r}")
        attrs = {
            "surface": entry.get("surface", ""),
            "effect": entry.get("effect", ""),
            "breadth": entry.get("breadth", "leaf"),
            "sensitivity": entry.get("sensitivity", "normal"),
            "confidence": "verified",
        }
        try:
            _validated_classification(entry, attrs)
        except ValueError as exc:
            raise PolicyError(str(exc)) from exc
        frozen_classifier.append(
            tuple(sorted({"glob": str(entry["glob"]), **attrs}.items())))

    recipe_data = data.get("full_recipe")
    if not isinstance(recipe_data, Mapping):
        raise PolicyError("routing policy must define full_recipe")
    _check_requires("full_recipe", recipe_data)
    # The full route is the ceiling, so it is validated against its own rule
    # rather than the generic level check. A recipe at Level 0 would let
    # force_full be true while selecting the cheapest rung of the ladder.
    if recipe_data.get("minimum_level") != 3:
        raise PolicyError(
            "full_recipe.minimum_level must be 3: it is the canonical full route")
    if not recipe_data.get("passes"):
        raise PolicyError("full_recipe must name at least one pass")
    _check_obligations("full_recipe", recipe_data.get("obligations", {}), usable,
                       known_capabilities)
    if not recipe_data.get("obligations"):
        raise PolicyError("full_recipe must name at least one obligation")
    if full_set is not None:
        # Level 3 with nonempty sets is not the same as covering the
        # repository's canonical full verification. Without this a recipe
        # naming one pass and one capability satisfied every structural check
        # while omitting most of what a full route is supposed to run.
        recipe_passes = set(recipe_data.get("passes", []))
        missing_passes = sorted(set(full_set.get("passes", [])) - recipe_passes)
        if missing_passes:
            raise PolicyError(
                f"full_recipe omits canonical passes {missing_passes}")
        recipe_obligations = recipe_data.get("obligations", {})
        for capability, gate_ids in full_set.get("obligations", {}).items():
            present = set(recipe_obligations.get(capability, []))
            missing_gates = sorted(set(gate_ids) - present)
            if capability not in recipe_obligations:
                raise PolicyError(
                    f"full_recipe omits canonical capability {capability}")
            if missing_gates:
                raise PolicyError(
                    f"full_recipe capability {capability} omits canonical "
                    f"gates {missing_gates}")

    rules_data = data.get("rules")
    if not isinstance(rules_data, list):
        raise PolicyError("routing policy must define a rules array")

    seen: set[str] = set()
    rules: list[ValidatedRule] = []
    for rule in rules_data:
        if not isinstance(rule, Mapping) or not rule.get("id"):
            raise PolicyError("every rule needs an id")
        rule_id = str(rule["id"])
        where = f"rule {rule_id}"
        if rule_id in seen:
            raise PolicyError(f"duplicate rule id: {rule_id}")
        seen.add(rule_id)
        _check_match(where, rule.get("match"))
        requires = rule.get("requires", {})
        _check_requires(where, requires)
        _check_obligations(where, rule.get("obligations", {}), usable,
                           known_capabilities)
        rules.append(ValidatedRule(
            id=rule_id,
            approved=str(rule.get("review_status", "")).lower() == "approved",
            match=tuple(sorted(
                (key, tuple(value) if isinstance(value, list) else value)
                for key, value in rule["match"].items()
            )),
            passes=frozenset(requires.get("passes", [])),
            minimum_level=int(requires.get("minimum_level", 0)),
            force_full=bool(requires.get("force_full", False)),
            independent_review=bool(requires.get("independent_review", False)),
            obligations=_freeze_obligations(rule.get("obligations", {})),
        ))

    validated = ValidatedPolicy(
        schema_version=1,
        classifier=tuple(frozen_classifier),
        full_recipe=ValidatedRecipe(
            minimum_level=3,
            passes=frozenset(recipe_data.get("passes", [])),
            independent_review=bool(recipe_data.get("independent_review", False)),
            obligations=_freeze_obligations(recipe_data.get("obligations", {})),
        ),
        rules=tuple(rules),
    )
    _VALIDATED_POLICIES[id(validated)] = validated
    return validated

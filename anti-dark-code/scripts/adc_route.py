#!/usr/bin/env python3
"""Deterministic change-impact routing for Anti-Dark-Code.

This module decides what verification a change requires. It never lowers a
requirement: combination is union and maximum only, so adding a changed file
cannot reduce any part of a route.

Git acquisition is the one impure boundary. Classification and route building
are pure functions over an acquired snapshot, so the monotonic property can be
tested exhaustively without building a repository per case.

Nothing here executes repository code. It reads git metadata and JSON only.
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class RawParse:
    """Parsed records plus the reason codes for anything that did not parse.

    Problems are carried rather than raised. A malformed record must not be
    silently dropped: routing has to know its picture of the change is
    incomplete so it can refuse to authorize a shortcut.
    """

    inputs: tuple[ChangeInput, ...] = ()
    problems: tuple[str, ...] = ()


def _split_z(payload: bytes) -> list[str]:
    """Split NUL-delimited git output.

    surrogateescape keeps a path git emitted that is not valid UTF-8. Losing
    such a path would silently shrink the change set.
    """
    text = payload.decode("utf-8", errors="surrogateescape")
    return [part for part in text.split("\x00") if part != ""]


def parse_raw_z(payload: bytes, source: str) -> RawParse:
    """Parse `git diff --raw -z` output into ChangeInput records.

    Raw is required rather than --name-status because only raw carries the mode
    and object columns. Without them a mode-only change cannot be told from a
    content modification, so an executable-bit flip would route lower than it
    should.
    """
    if source not in CHANGE_SOURCES:
        raise ValueError(f"unknown change source: {source}")

    fields = _split_z(payload)
    rows: list[ChangeInput] = []
    problems: list[str] = []
    index = 0

    while index < len(fields):
        header = fields[index]
        if not header.startswith(":"):
            problems.append("ADC-ROUTE-MALFORMED-RECORD")
            index += 1
            continue

        parts = header[1:].split()
        if len(parts) < 5:
            problems.append("ADC-ROUTE-MALFORMED-RECORD")
            index += 1
            continue

        old_mode, new_mode, old_object, new_object, status = parts[:5]
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

        # A mode-only change carries the same object on both sides. Git still
        # reports it as M, so comparing the objects is the only discriminator.
        if kind == "modify" and old_object == new_object and old_mode != new_mode:
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
        ))
        index += wanted + 1

    return RawParse(inputs=tuple(rows), problems=tuple(sorted(set(problems))))


def parse_untracked_z(payload: bytes) -> RawParse:
    """Parse `git ls-files --others --exclude-standard -z` output."""
    rows = tuple(
        ChangeInput(path=path, change_kind="add", source="untracked")
        for path in _split_z(payload)
    )
    return RawParse(inputs=rows)

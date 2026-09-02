#!/usr/bin/env python3
"""Routing receipts: the auditable record binding one route to one worktree.

A receipt exists to be disbelieved. Its job is not to record that a route was
taken, it is to make a stale route impossible to use by accident: if anything
the route depended on has moved, verification says so and names what moved.

Two rules shape everything here.

Authority is separate from observation. The authoritative payload holds only
what a route actually depends on, and `run_id` is its hash. Timestamps, host
names, and tool versions live outside that hash, because a receipt written
twice from the same inputs on two machines at two times is the same receipt,
and a clock must never be able to change routing authority. See R-023.

Freshness binds bytes, not status text. Git's porcelain status says a file is
modified; it does not say what it now contains. Two different edits to one file
produce identical status output, so a status digest would call a receipt fresh
across a change that alters what the route should have been. Freshness uses
object ids where git already has them and hashes current bytes, executable
modes, and symlink targets where it does not. See R-017.

This module writes and verifies. It does not decide what to run, and reading a
receipt never executes anything: a receipt is data, not an instruction.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 2 since D-072: the binding carries unsupported_paths. A receipt written
# under schema 1 was computed by code that could not see a submodule, so it
# is refused rather than compared field by field.
SCHEMA_VERSION = 2

# Where written receipts land, relative to the repository root.
RUN_STORE = ".anti-dark-code/runs"

# Reason codes for a receipt that can no longer be trusted. Each names the one
# thing that moved, because "stale" alone sends a reader looking through
# everything the receipt touched.
STALE_BINDING = "ADC-STALE-001"
STALE_BASE = "ADC-STALE-002"
STALE_HEAD = "ADC-STALE-003"
STALE_WORKTREE = "ADC-STALE-004"
STALE_POLICY = "ADC-STALE-005"
STALE_GATES = "ADC-STALE-006"
STALE_CALIBRATION = "ADC-STALE-007"
STALE_SCHEMA = "ADC-STALE-008"
# Not a field that moved: a tree this receipt cannot bind at all.
STALE_UNSUPPORTED = "ADC-STALE-009"

# Why a gate is not in this route. A gate omitted with no reason is the thing
# an auditor cannot check, so every omission carries one.
SKIP_NOT_REQUIRED = "ADC-SKIP-001"
SKIP_DISABLED = "ADC-SKIP-002"
SKIP_UNAPPROVED = "ADC-SKIP-003"


class ReceiptError(ValueError):
    """A receipt is malformed, or the inputs to one are unusable."""


def canonical_bytes(value: Any) -> bytes:
    """Deterministic bytes for hashing.

    `sort_keys` settles object key order. It does not settle array order, and
    the EDD is explicit that arrays are sorted by a documented canonical key
    before they reach here. That sorting belongs to whoever builds the payload,
    because only they know which key is canonical for each array. This function
    deliberately does not sort arrays, so a caller that forgot cannot have the
    mistake hidden by the hasher.

    `allow_nan=False` because NaN and Infinity are not JSON, and a value that
    serializes to something no parser accepts is not an auditable record.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    reader = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            reader.update(block)
    return reader.hexdigest()


@dataclass(frozen=True)
class Binding:
    """Everything the route depended on, reduced to comparable identities.

    A receipt is fresh when every field here still matches the repository. The
    fields are separate rather than one combined hash so that verification can
    say which one moved.
    """

    repo_binding_identity: str | None = None
    base_identity: str | None = None
    head_identity: str | None = None
    worktree_identity: str | None = None
    routing_policy_sha256: str | None = None
    gate_configuration_sha256: str | None = None
    calibration_hashes: Mapping[str, str] = field(default_factory=dict)
    # Paths whose state this binding cannot hold. Inside the authoritative
    # payload rather than beside it, because whether a route was computed over
    # a tree containing one is part of what the route depended on.
    unsupported_paths: Sequence[str] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "repo_binding_identity": self.repo_binding_identity,
            "base_identity": self.base_identity,
            "head_identity": self.head_identity,
            "worktree_identity": self.worktree_identity,
            "routing_policy_sha256": self.routing_policy_sha256,
            "gate_configuration_sha256": self.gate_configuration_sha256,
            "calibration_hashes": dict(sorted(self.calibration_hashes.items())),
            "unsupported_paths": sorted(self.unsupported_paths),
        }


@dataclass(frozen=True)
class Staleness:
    """The verdict. `fresh` is true only when nothing moved."""

    fresh: bool
    reasons: tuple[tuple[str, str], ...] = ()

    @property
    def exit_code(self) -> int:
        """2, not 1. A stale receipt is not a failed check, it is a receipt
        that cannot answer the question, and the runner distinguishes them."""
        return 0 if self.fresh else 2


def worktree_identity(repo: Path, route_module: Any, runner: Any = None) -> str:
    """One digest over the repository state a route depends on.

    Delegates to the router's fingerprint rather than reimplementing it. That
    function is the thing the boundary tests hold, it already covers index
    state, content, executable modes, symlink targets, and hard-link topology,
    and a second implementation here would be a second rule to keep in step.
    """
    return _identity_and_unsupported(repo, route_module, runner)[0]


def _identity_and_unsupported(
    repo: Path, route_module: Any, runner: Any = None
) -> tuple[str, tuple[str, ...]]:
    """The identity digest and the paths this fingerprint cannot bind.

    Both come from one fingerprint pass. Asking twice would hash every tracked
    file twice for an answer the first pass already had.

    An unsupported path today is one holding another repository: a submodule
    gitlink, or an untracked embedded repository. Their state lives outside
    this repository, so the entry a fingerprint can record for either does not
    move when their contents do. Reporting them here is what lets verification
    refuse the tree rather than certify a binding that holds nothing. See
    D-072.
    """
    run = runner or route_module._default_runner(repo)
    index_state, entries = route_module._repo_fingerprint(repo, run)
    mark = getattr(route_module, "GITLINK_MARK", "gitlink-unsupported") + ":"
    unsupported = tuple(sorted(
        str(entry[0]) for entry in entries
        if isinstance(entry[3], str) and entry[3].startswith(mark)))
    # Written receipts are outputs, not inputs. Without this exclusion the act
    # of recording a receipt changes the worktree the receipt binds, and the
    # receipt is stale the instant it lands. That was observed, not predicted:
    # the first --write produced a receipt that failed its own verification.
    #
    # Only the run store is excluded, never .anti-dark-code as a whole. The
    # router deliberately does not filter that tree, because policy and gate
    # files live near it and hiding them would blind the router to its own
    # escalators. See D-010.
    # Path and content only. The fingerprint tuple also carries size and
    # mtime, which the acquisition boundary needs to catch a rewrite during its
    # own run. A receipt binds what a route depended on, and a route does not
    # depend on a timestamp: including mtime made a receipt stale after the
    # bytes were restored, which trains a reader to ignore staleness. Size is
    # implied by the digest. Entry 3 carries the content digest and hard-link
    # topology together, so a same-content relink still moves the binding.
    kept = [[entry[0], entry[3]] for entry in entries
            if not str(entry[0]).replace("\\", "/").startswith(RUN_STORE + "/")]
    return digest({
        "index": index_state,
        # Already sorted by _repo_fingerprint, and sorted again here so this
        # does not silently depend on that.
        "entries": sorted(kept),
    }), unsupported


def collect_binding(
    repo: Path,
    route_module: Any,
    base_identity: str | None,
    head_identity: str | None,
    policy_source: Any,
    gates_source: Any,
    calibration_paths: Sequence[Path] = (),
    repo_binding_identity: str | None = None,
    runner: Any = None,
) -> Binding:
    """Read the current identity of everything the route depends on.

    `policy_source` and `gates_source` are the parsed documents rather than
    file paths, so a reformatted file with identical content does not read as a
    changed policy and an edited rule does, whatever the whitespace.
    """
    calibration: dict[str, str] = {}
    for path in calibration_paths:
        # A calibration file that is absent is itself a fact worth binding: if
        # one appears later, the route was computed without it.
        calibration[path.name] = _sha256_file(path) if path.is_file() else ""
    identity, unsupported = _identity_and_unsupported(repo, route_module, runner)
    return Binding(
        repo_binding_identity=repo_binding_identity,
        base_identity=base_identity,
        head_identity=head_identity,
        worktree_identity=identity,
        unsupported_paths=unsupported,
        routing_policy_sha256=digest(policy_source),
        gate_configuration_sha256=digest(gates_source),
        calibration_hashes=calibration,
    )


def _fact_payload(fact: Any) -> dict[str, Any]:
    """A fact reduced to its serialized fields, in canonical key order."""
    from dataclasses import fields as dataclass_fields
    return {f.name: getattr(fact, f.name) for f in dataclass_fields(fact)}


def _omissions(
    route: Any,
    gates_source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Every gate the configuration defines and this route does not select.

    A route that omits nothing still gets an empty list rather than a missing
    key, so a reader never has to decide whether absence means none or means
    the writer forgot.
    """
    selected = {gate for gates in route.obligations.values() for gate in gates}
    omitted: list[dict[str, Any]] = []
    for entry in gates_source.get("gates", []):
        if not isinstance(entry, Mapping):
            raise ReceiptError(f"gate entry is not an object: {entry!r}")
        gate_id = entry.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise ReceiptError(f"gate entry has no id: {entry!r}")
        if gate_id in selected:
            continue
        if not entry.get("enabled", False):
            reason = SKIP_DISABLED
        elif entry.get("review_status") != "approved":
            reason = SKIP_UNAPPROVED
        else:
            reason = SKIP_NOT_REQUIRED
        omitted.append({"gate_id": gate_id, "reason_code": reason})
    return sorted(omitted, key=lambda row: row["gate_id"])


def authoritative_payload(
    route: Any,
    facts: Sequence[Any],
    snapshot: Any,
    binding: Binding,
    gates_source: Mapping[str, Any],
    independent_review_recorded: bool = False,
    operator_escalation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything a route depends on, and nothing that merely describes the run.

    Every array here is sorted by a documented key. Two runs over the same
    change in a different order produce the same bytes, which is what makes the
    hash an identity rather than a timestamp. See R-002 and S-001.
    """
    if operator_escalation is not None:
        if not isinstance(operator_escalation, Mapping):
            raise ReceiptError("operator_escalation must be an object")
        if not operator_escalation.get("reason"):
            # An escalation without a reason is the audit hole this field
            # exists to close.
            raise ReceiptError("operator_escalation requires a reason")

    changed = sorted(
        ({"path": row.path, "change_kind": row.change_kind, "source": row.source,
          "old_path": row.old_path, "mode_changed": bool(row.mode_changed)}
         for row in getattr(snapshot, "inputs", ())),
        key=lambda row: (row["path"], row["source"], row["change_kind"],
                         row["old_path"] or ""))

    return {
        "schema_version": SCHEMA_VERSION,
        "binding": binding.as_payload(),
        "changed_files": changed,
        "emitted_facts": sorted(
            (_fact_payload(fact) for fact in facts),
            key=lambda row: canonical_bytes(row)),
        "route": {
            "minimum_level": route.minimum_level,
            "selected_passes": sorted(route.passes),
            "capability_to_gate_ids": {
                capability: sorted(gates)
                for capability, gates in sorted(route.obligations.items())
            },
            "selected_gate_ids": sorted(
                {gate for gates in route.obligations.values() for gate in gates}),
            "matched_rule_ids": sorted(route.matched_rule_ids),
            "force_full": route.force_full,
            "independent_review_required": route.independent_review,
            "unmapped_paths": sorted(route.unmapped_paths),
            "unknowns": sorted(route.unknowns),
        },
        "omitted_gates": _omissions(route, gates_source),
        "independent_review_recorded": bool(independent_review_recorded),
        "operator_escalation": (dict(sorted(operator_escalation.items()))
                                if operator_escalation is not None else None),
        "snapshot_complete": bool(getattr(snapshot, "complete", False)),
        "snapshot_problems": sorted(getattr(snapshot, "problems", ())),
    }


def build_receipt(
    payload: Mapping[str, Any],
    observed: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap an authoritative payload with its id and non-authoritative notes.

    `observed` is display only. It is stored outside the hashed payload, so
    nothing in it can change `run_id`, and a reader can tell at a glance which
    half of the file carries authority.
    """
    return {
        "run_id": digest(payload),
        "authoritative": dict(payload),
        "observed": dict(observed or {}),
    }


def verify_receipt(
    receipt: Mapping[str, Any],
    current: Binding,
) -> Staleness:
    """Compare a receipt's binding against the repository as it is now.

    Every mismatch is reported, not just the first. A reader chasing one stale
    field at a time learns the worktree moved, fixes that, and only then learns
    the policy moved too.
    """
    if not isinstance(receipt, Mapping):
        raise ReceiptError("receipt must be an object")
    payload = receipt.get("authoritative")
    if not isinstance(payload, Mapping):
        raise ReceiptError("receipt has no authoritative payload")

    reasons: list[tuple[str, str]] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        # Refuse rather than guess. A receipt from another schema may bind
        # fields this code does not compare, and comparing the ones it
        # recognizes would report fresh on a partial check.
        return Staleness(False, ((STALE_SCHEMA,
                                  f"receipt schema_version is "
                                  f"{payload.get('schema_version')!r}, "
                                  f"expected {SCHEMA_VERSION}"),))

    recorded = payload.get("binding")
    if not isinstance(recorded, Mapping):
        raise ReceiptError("receipt binding is not an object")
    now = current.as_payload()

    # Checked before the field comparison, and not as one more field that
    # moved. Every other reason here says the repository changed. This one says
    # the repository holds something no field in this binding can follow, so
    # matching fields would not mean the tree stood still. Fresh is not
    # available for such a tree at any value of the other fields. See D-072.
    blocking = sorted(now.get("unsupported_paths") or ())
    if blocking:
        reasons.append((STALE_UNSUPPORTED, ", ".join(blocking)))

    for key, code in (
        ("repo_binding_identity", STALE_BINDING),
        ("base_identity", STALE_BASE),
        ("head_identity", STALE_HEAD),
        ("worktree_identity", STALE_WORKTREE),
        ("routing_policy_sha256", STALE_POLICY),
        ("gate_configuration_sha256", STALE_GATES),
    ):
        if recorded.get(key) != now.get(key):
            reasons.append((code, key))

    if recorded.get("calibration_hashes") != now.get("calibration_hashes"):
        was = recorded.get("calibration_hashes") or {}
        is_now = now.get("calibration_hashes") or {}
        moved = sorted(set(was) | set(is_now))
        changed = [name for name in moved if was.get(name) != is_now.get(name)]
        reasons.append((STALE_CALIBRATION, ", ".join(changed) or "calibration"))

    return Staleness(not reasons, tuple(reasons))


def receipt_bytes(receipt: Mapping[str, Any]) -> bytes:
    """Bytes for writing to disk. Indented, because a person reads this."""
    return (json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")

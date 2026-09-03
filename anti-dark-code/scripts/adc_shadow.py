#!/usr/bin/env python3
"""Shadow evidence records for SLICE-002.

One record says, for one change that CI verified in full, what the proposed
routing rules would have skipped and whether anything they skipped failed.
The record never asks the router how it did: the outcomes come from the run
that executed the canonical recipe regardless of any route, and this module
refuses to call a record measurable unless every canonical gate is present
with a real outcome. See `design/routing/SLICE-002-shadow-evidence.md`
sections 2 to 6, which are the contract this file implements, and D-125.

Standard library only, like every other shipped script.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 2
SCHEMA_NAME = "shadow-record-v2"

# What a gate outcome may be for a record to mean anything. `shadow_result`
# counts every non-pass omitted outcome as missed and an absent key as clean,
# so a record whose outcomes carry `not-run`, `skipped`, `stale`, or nothing
# at all would read as evidence when it is silence. The brief's Measurable
# paragraph puts this check in front of `shadow_result`, not after it.
DECIDED_OUTCOMES = frozenset({"pass", "fail"})

STATUS_MISS = "miss"
STATUS_CLEAN = "clean"
STATUS_INCONCLUSIVE = "inconclusive"
STATUS_NO_OMISSION = "no_omission"
STATUS_SELECTS_NOTHING = "selects_nothing"
STATUS_NOT_MEASURABLE = "not_measurable"

# Only `clean` and `miss` are evidence for or against a class. The other four
# are recorded and reported so a reader can see what the campaign could not
# measure, which is the count that tells you whether the campaign is working.
EVIDENCE_STATUSES = frozenset({STATUS_CLEAN, STATUS_MISS})

RECORD_REQUIRED_KEYS = (
    "schema_version",
    "record_id",
    "provenance",
    "status",
    "measurable",
    "commits",
    "run",
    "class_key",
    "class",
    "audit",
    "gate_outcomes",
)


class ShadowError(Exception):
    """A record that cannot be trusted is not written."""


def canonical_json(value: Any) -> str:
    """One spelling per value, so a digest means the same thing on every host."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def strip_underscored(value: Any) -> Any:
    """Drop `_`-prefixed keys at every depth.

    A policy's `_note` is prose for a reader. Keying a class on the file's
    bytes made every comment edit start a new class and reset its clock, which
    the design challenge measured; keying on the terms with the notes removed
    is what makes two records comparable. See the brief's section 3.
    """
    if isinstance(value, Mapping):
        return {key: strip_underscored(item) for key, item in value.items()
                if not str(key).startswith("_")}
    if isinstance(value, list):
        return [strip_underscored(item) for item in value]
    return value


def class_terms(policy_source: Mapping[str, Any], gates_source: Mapping[str, Any],
                matched_rule_ids: Sequence[str]) -> dict[str, Any]:
    """The meaning a class rests on: the fired rules, the classifier, the recipe.

    `review_status` is excluded by construction, because only three keys are
    taken from a rule. That is what lets the owner approve one rule without
    resetting every other class's clock, which G6 requires.
    """
    rules = {}
    wanted = set(matched_rule_ids)
    for rule in policy_source.get("rules", []):
        if not isinstance(rule, Mapping) or str(rule.get("id")) not in wanted:
            continue
        rules[str(rule["id"])] = strip_underscored({
            "match": rule.get("match", {}),
            "requires": rule.get("requires", {}),
            "obligations": rule.get("obligations", {}),
        })
    missing = sorted(wanted - set(rules))
    if missing:
        raise ShadowError(f"matched rules absent from the policy: {missing}")
    return {
        "matched_rules": rules,
        "classifier": strip_underscored(policy_source.get("classifier", {})),
        "canonical_full_set": strip_underscored(
            gates_source.get("canonical_full_set", {})),
    }


def class_key(terms: Mapping[str, Any], router_blob_sha256: str,
              omitted_gate_ids: Sequence[str]) -> str:
    """The key two records must share before they count toward one class.

    The router blob is part of it because a router change changes what a
    candidate is; D-119 through D-121 changed candidate building three times
    in one round, and records from either side of that are not the same
    measurement. G5 states it; S-061 holds it.
    """
    return digest({
        "terms": terms,
        "router_blob_sha256": router_blob_sha256,
        "omitted_gate_ids": sorted(omitted_gate_ids),
    })


def canonical_gate_ids(gates_source: Mapping[str, Any]) -> tuple[str, ...]:
    obligations = gates_source.get("canonical_full_set", {}).get("obligations", {})
    if not isinstance(obligations, Mapping) or not obligations:
        raise ShadowError("gates.json has no canonical full set obligations")
    gates: set[str] = set()
    for gate_ids in obligations.values():
        if not isinstance(gate_ids, list) or not gate_ids:
            raise ShadowError("a canonical capability names no gate")
        gates.update(str(gate) for gate in gate_ids)
    return tuple(sorted(gates))


def measurability(outcomes: Mapping[str, str], gates: Sequence[str],
                  candidate: Any) -> tuple[bool, str | None]:
    """Whether this change was verified well enough to say anything.

    Silence never reads as clean. A gate that is absent, or that concluded
    anything other than pass or fail, leaves the record unmeasurable and the
    campaign's counts untouched.
    """
    if candidate is None:
        return False, "snapshot-incomplete"
    absent = sorted(gate for gate in gates if gate not in outcomes)
    if absent:
        return False, f"gates absent from the outcomes: {', '.join(absent)}"
    undecided = sorted(
        f"{gate}={outcomes[gate]}" for gate in gates
        if str(outcomes[gate]) not in DECIDED_OUTCOMES)
    if undecided:
        return False, f"gates without a decided outcome: {', '.join(undecided)}"
    return True, None


def provenance_for(head_ref: str | None, backfill: bool) -> str:
    """Derived, never asserted.

    G8 requires a canary to be recognised by the branch it came from, because
    a free label is a judgement inside a record, which G7 forbids.
    """
    ref = (head_ref or "").strip()
    short = ref.split("refs/heads/", 1)[-1]
    if short.startswith("canary/"):
        return "canary"
    return "backfill" if backfill else "live"


def build_record(
    *,
    policy_source: Mapping[str, Any],
    gates_source: Mapping[str, Any],
    route: Any,
    candidate: Any,
    outcomes: Mapping[str, str],
    base_outcomes: Mapping[str, str] | None,
    commits: Mapping[str, str],
    run: Mapping[str, Any],
    head_ref: str | None,
    backfill: bool,
    router_blob_sha256: str,
    shadow_result,
) -> dict[str, Any]:
    """One record, in the order the brief defines it."""
    gates = canonical_gate_ids(gates_source)
    outcomes = {str(k): str(v) for k, v in outcomes.items()}
    measurable, reason = measurability(outcomes, gates, candidate)

    selected: tuple[str, ...] = ()
    omitted: list[str] = []
    matched: list[str] = []
    shadow: dict[str, Any] | None = None
    status = STATUS_NOT_MEASURABLE
    if candidate is not None:
        selected = tuple(candidate.selected_gate_ids())
        omitted = sorted(set(gates) - set(selected))
        matched = sorted(candidate.matched_rule_ids)

    if measurable:
        if candidate.force_full:
            status = STATUS_NO_OMISSION
        elif not selected:
            # D-123 refuses such a rule at load, so this is unreachable for a
            # policy this repository can load. It is recorded rather than
            # asserted because a consumer's policy is not ours to trust.
            status = STATUS_SELECTS_NOTHING
        else:
            shadow = shadow_result(
                {"route": {"selected_gate_ids": list(gates)}}, candidate, outcomes)
            if shadow["routing_miss"]:
                inherited = [
                    gate for gate in shadow["missed_gate_ids"]
                    if base_outcomes and str(base_outcomes.get(gate)) == "fail"]
                if inherited:
                    status = STATUS_INCONCLUSIVE
                    reason = f"inherited-failure: {', '.join(sorted(inherited))}"
                else:
                    status = STATUS_MISS
            elif shadow["selected_all_passed"]:
                status = STATUS_CLEAN if omitted else STATUS_NO_OMISSION
            else:
                status = STATUS_INCONCLUSIVE
                reason = "a selected gate failed, so the candidate caught it too"

    terms = class_terms(policy_source, gates_source, matched)
    record = {
        "schema_version": SCHEMA_VERSION,
        "schema": SCHEMA_NAME,
        "provenance": provenance_for(head_ref, backfill),
        "head_ref": head_ref or "",
        "status": status,
        "measurable": measurable,
        "not_measurable_reason": reason if not measurable else None,
        "inconclusive_reason": reason if status == STATUS_INCONCLUSIVE else None,
        "commits": {key: str(commits.get(key, "")) for key in ("base", "merge", "head")},
        "run": {
            "pull_request": run.get("pull_request"),
            "run_id": str(run.get("run_id", "")),
            "run_attempt": int(run.get("run_attempt", 0) or 0),
        },
        "class_key": class_key(terms, router_blob_sha256, omitted),
        "class": {
            "matched_rule_ids": matched,
            "selected_gate_ids": sorted(selected),
            "omitted_gate_ids": omitted,
            "router_blob_sha256": router_blob_sha256,
            "terms_sha256": digest(terms),
        },
        "audit": {
            "policy_bytes_sha256": hashlib.sha256(
                canonical_json(policy_source).encode("utf-8")).hexdigest(),
            "policy_terms_sha256": digest(strip_underscored(policy_source)),
            "gates_terms_sha256": digest(strip_underscored(gates_source)),
            "route_force_full": bool(getattr(route, "force_full", False)),
            "route_minimum_level": int(getattr(route, "minimum_level", 0)),
            "route_unknowns": sorted(getattr(route, "unknowns", ()) or ()),
        },
        "gate_outcomes": dict(sorted(outcomes.items())),
        "base_gate_outcomes": (dict(sorted(base_outcomes.items()))
                               if base_outcomes else None),
        "shadow": shadow,
    }
    record["record_id"] = digest(record)
    return record


def validate_record(record: Mapping[str, Any]) -> list[str]:
    """Structural refusal, so a malformed record never reaches the ledger."""
    errors: list[str] = []
    for key in RECORD_REQUIRED_KEYS:
        if key not in record:
            errors.append(f"missing required key: {key}")
    if errors:
        return errors
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if record.get("status") not in {
            STATUS_MISS, STATUS_CLEAN, STATUS_INCONCLUSIVE, STATUS_NO_OMISSION,
            STATUS_SELECTS_NOTHING, STATUS_NOT_MEASURABLE}:
        errors.append(f"unknown status: {record.get('status')!r}")
    if record.get("provenance") not in {"live", "backfill", "canary"}:
        errors.append(f"unknown provenance: {record.get('provenance')!r}")
    if record.get("status") in EVIDENCE_STATUSES and not record.get("measurable"):
        errors.append("an unmeasurable record cannot be evidence")
    if record.get("measurable") and record.get("status") == STATUS_NOT_MEASURABLE:
        errors.append("a measurable record cannot be status not_measurable")
    commits = record.get("commits", {})
    for key in ("base", "merge", "head"):
        if not str(commits.get(key, "")):
            errors.append(f"commits.{key} is empty")
    body = {k: v for k, v in record.items() if k != "record_id"}
    if record.get("record_id") != digest(body):
        errors.append("record_id does not digest the record")
    return errors


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ShadowError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _adc_module(provided=None):
    if provided is not None:
        return provided
    return _load_module("adc_for_shadow", Path(__file__).resolve().with_name("adc.py"))


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        raise ShadowError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout.strip()


def router_digest(route_module_path: Path) -> str:
    """Which router computed the candidate, by the bytes that did it.

    The brief says "the blob sha of `adc_route.py` at the head". Implemented
    as the digest of the router file this process loaded, for two measured
    reasons recorded in D-125: the repository being measured need not contain
    the skill at all, which a consumer-shaped fixture showed immediately, and
    the property the class key needs is which router produced the candidate,
    which the loaded file states exactly. Hashing the file rather than a
    commit's entry is also what makes the backfill honest: it replays today's
    router over a historical change set, and the key says so.
    """
    return hashlib.sha256(Path(route_module_path).read_bytes()).hexdigest()


def command_record(args: argparse.Namespace, adc_module=None) -> int:
    adc = _adc_module(adc_module)
    route_module, _ = adc.load_router_helpers()
    repo = Path(args.repo).resolve()

    calibration = (Path(args.calibration) if args.calibration
                   else repo / adc.ROUTE_CALIBRATION)
    policy_source = json.loads(
        (calibration / "routing-policy.json").read_text(encoding="utf-8"))
    gates_source = json.loads(
        (calibration / "gates.json").read_text(encoding="utf-8"))
    catalog = json.loads((Path(__file__).resolve().parents[1] / "assets"
                          / "verification-capabilities.json").read_text(encoding="utf-8"))
    validated = route_module.load_policy(
        policy_source, gates_source, [c["id"] for c in catalog["capabilities"]],
        gates_source["canonical_full_set"])

    snapshot = route_module.read_change_inputs(repo, args.base)
    facts = route_module.collect_change_facts(snapshot, validated.classifier_map())
    route = route_module.build_route(facts, validated, snapshot_ok=snapshot.complete)
    candidate = route_module.build_candidate_route(
        facts, validated, snapshot_ok=snapshot.complete)

    outcomes = json.loads(Path(args.outcomes).read_text(encoding="utf-8"))
    base_outcomes = (json.loads(Path(args.base_outcomes).read_text(encoding="utf-8"))
                     if args.base_outcomes else None)

    record = build_record(
        policy_source=policy_source,
        gates_source=gates_source,
        route=route,
        candidate=candidate,
        outcomes=outcomes,
        base_outcomes=base_outcomes,
        commits={"base": args.base_sha or args.base,
                 "merge": args.merge or _git(repo, "rev-parse", "HEAD"),
                 "head": args.head or ""},
        run={"pull_request": args.pr, "run_id": args.run,
             "run_attempt": args.attempt},
        head_ref=args.head_ref,
        backfill=args.backfill,
        router_blob_sha256=router_digest(Path(route_module.__file__)),
        shadow_result=adc.shadow_result,
    )
    errors = validate_record(record)
    if errors:
        print("REFUSED: " + "; ".join(errors))
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"SHADOW {record['status']} class={record['class_key'][:12]} "
          f"provenance={record['provenance']} "
          f"omitted={','.join(record['class']['omitted_gate_ids']) or '-'} "
          f"record={record['record_id'][:12]}")
    if not record["measurable"]:
        print(f"  not measurable: {record['not_measurable_reason']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adc.py shadow",
        description="Shadow evidence records for the routing campaign")
    sub = parser.add_subparsers(dest="shadow_command", required=True)

    p = sub.add_parser("record", help="Build one shadow record from a verified run")
    p.add_argument("--repo", default=".")
    p.add_argument("--calibration")
    p.add_argument("--base", required=True,
                   help="Comparison base for the change, as a git ref")
    p.add_argument("--base-sha", help="Base commit recorded in the record")
    p.add_argument("--merge", help="Merge commit CI verified; defaults to HEAD")
    p.add_argument("--head", default="", help="Pull request head commit")
    p.add_argument("--head-ref", help="Head ref, from which provenance is derived")
    p.add_argument("--pr", type=int, help="Pull request number")
    p.add_argument("--run", help="Workflow run id")
    p.add_argument("--attempt", type=int, default=1, help="Workflow run attempt")
    p.add_argument("--outcomes", required=True,
                   help="JSON file mapping canonical gate id to CI conclusion")
    p.add_argument("--base-outcomes",
                   help="JSON file of the base commit's own outcomes")
    p.add_argument("--backfill", action="store_true")
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_record)
    return parser


def main(argv: list[str] | None = None, adc_module=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, adc_module=adc_module)
    except ShadowError as error:
        print(f"REFUSED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

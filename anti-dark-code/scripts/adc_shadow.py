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


def gate_outcomes_from_jobs(jobs: Sequence[Mapping[str, Any]],
                            gate_map: Mapping[str, Any]) -> dict[str, str]:
    """Reduce a run attempt's jobs to one conclusion per canonical gate.

    A gate that resolves to no job at all reads `unresolved`, not `pass`. That
    is the case a renamed or deleted job produces, and it is why the mapping
    needs no separate contract test against the workflow's text: the record
    for that run says it could not be measured, loudly, at the moment the
    rename lands. See D-126.
    """
    outcomes: dict[str, str] = {}
    for gate, spec in sorted(gate_map.get("gates", {}).items()):
        names = [str(name) for name in spec.get("jobs", [])]
        prefixes = [str(prefix) for prefix in spec.get("job_prefixes", [])]
        step_name = spec.get("step")
        matched = [job for job in jobs
                   if str(job.get("name", "")) in names
                   or any(str(job.get("name", "")).startswith(prefix)
                          for prefix in prefixes)]
        if not matched:
            outcomes[gate] = "unresolved"
            continue
        conclusions: list[str] = []
        for job in matched:
            if step_name is None:
                conclusions.append(str(job.get("conclusion") or "in-progress"))
                continue
            steps = [step for step in job.get("steps", [])
                     if str(step.get("name", "")) == step_name]
            if not steps:
                conclusions.append("unresolved")
                continue
            conclusions.extend(
                str(step.get("conclusion") or "in-progress") for step in steps)
        if any(conclusion == "failure" for conclusion in conclusions):
            outcomes[gate] = "fail"
        elif all(conclusion == "success" for conclusion in conclusions):
            outcomes[gate] = "pass"
        else:
            # Cancelled, skipped, timed out, still running, or a step the
            # mapping named and the job does not have. Every one of these
            # leaves the record unmeasurable rather than counting as evidence.
            outcomes[gate] = next(
                conclusion for conclusion in conclusions if conclusion != "success")
    return outcomes


def fetch_attempt_jobs(repository: str, run_id: str, attempt: int,
                       token: str) -> list[dict[str, Any]]:
    """The jobs of one run attempt, from the attempt's own endpoint.

    The brief says `filter=all` so a rerun does not replace the attempt it
    supersedes. The attempts endpoint states the same thing directly: it
    returns the jobs of the attempt asked for and nothing else, so a later
    rerun cannot overwrite what this record measured. D-126.
    """
    import urllib.request

    jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (f"https://api.github.com/repos/{repository}/actions/runs/"
               f"{run_id}/attempts/{attempt}/jobs?per_page=100&page={page}")
        request = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "adc-shadow",
        })
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        batch = payload.get("jobs", [])
        jobs.extend(batch)
        if len(batch) < 100:
            return jobs
        page += 1


def command_outcomes(args: argparse.Namespace, adc_module=None) -> int:
    gate_map = json.loads(Path(args.map).read_text(encoding="utf-8"))
    if args.jobs:
        jobs = json.loads(Path(args.jobs).read_text(encoding="utf-8"))
        if isinstance(jobs, Mapping):
            jobs = jobs.get("jobs", [])
    else:
        import os

        token = os.environ.get("GITHUB_TOKEN", "")
        repository = args.repository or os.environ.get("GITHUB_REPOSITORY", "")
        if not token or not repository:
            print("REFUSED: GITHUB_TOKEN and a repository are required to fetch")
            return 2
        jobs = fetch_attempt_jobs(repository, args.run, args.attempt, token)
    outcomes = gate_outcomes_from_jobs(jobs, gate_map)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(outcomes, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
    for gate, outcome in sorted(outcomes.items()):
        print(f"  {gate:22} {outcome}")
    return 0


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


def _gh_json(args: Sequence[str]) -> Any:
    """One read through the GitHub CLI, which discovery needs and records do not.

    Kept behind this one function so the record path stays pure data: a record
    is built from a change and a jobs payload, both of which a caller can
    supply from a file. Only discovery needs the network.
    """
    done = subprocess.run(["gh", "api", *args], capture_output=True, text=True,
                          timeout=120)
    if done.returncode != 0:
        raise ShadowError(f"gh api {' '.join(args)} failed: {done.stderr.strip()}")
    return json.loads(done.stdout)


def discover_changes(repo: Path, since: str, branch: str = "HEAD",
                     workflow_name: str = "Tests") -> list[dict[str, Any]]:
    """Every merge on the first-parent line since `since`, with its run.

    A merge commit's first parent is the base the pull request was measured
    against and its second is the head, which is what CI verified as
    `refs/pull/N/merge`. A merge with no run under the workflow, which every
    change before the workflow landed on 2026-08-22 has, is returned with no
    run so the caller can record it as not measurable rather than drop it.
    """
    repository = _git(repo, "remote", "get-url", "origin")
    repository = repository.rstrip("/").removesuffix(".git").split(":")[-1]
    repository = "/".join(repository.split("/")[-2:])
    log = _git(repo, "log", "--first-parent", "--merges", "--format=%H\x1f%P\x1f%s",
               f"{since}..{branch}")
    changes: list[dict[str, Any]] = []
    for line in log.splitlines():
        if not line.strip():
            continue
        merge, parents, subject = line.split("\x1f", 2)
        parent_ids = parents.split()
        if len(parent_ids) < 2:
            continue
        number = None
        for token in subject.replace(":", " ").split():
            if token.startswith("#") and token[1:].isdigit():
                number = int(token[1:])
                break
        entry: dict[str, Any] = {
            "pull_request": number,
            "merge": merge,
            "base": parent_ids[0],
            "head": parent_ids[1],
            "subject": subject,
            "run_id": None,
            "run_attempt": None,
            "jobs": None,
        }
        runs = _gh_json([f"/repos/{repository}/actions/runs"
                         f"?head_sha={entry['head']}&per_page=100"])
        candidates = [run for run in runs.get("workflow_runs", [])
                      if run.get("name") == workflow_name]
        if candidates:
            run = max(candidates, key=lambda item: item.get("run_attempt", 1))
            entry["run_id"] = str(run["id"])
            entry["run_attempt"] = int(run.get("run_attempt", 1))
            entry["jobs"] = _gh_json([
                f"/repos/{repository}/actions/runs/{run['id']}/attempts/"
                f"{entry['run_attempt']}/jobs?per_page=100"]).get("jobs", [])
        changes.append(entry)
    return changes


def command_backfill(args: argparse.Namespace, adc_module=None) -> int:
    """Replay today's router over historical change sets.

    Not a reconstruction at each head: the candidate builder did not exist at
    the earliest heads and the policy differed across the stack, so per-head
    keys would be classes of one. Today's router and today's policy over the
    historical change set, keyed by today's digests, is what the brief's
    section 5 defines, and every record carries `provenance: backfill`.
    """
    import shutil
    import tempfile

    adc = _adc_module(adc_module)
    route_module, _ = adc.load_router_helpers()
    repo = Path(args.repo).resolve()
    calibration = (Path(args.calibration).resolve() if args.calibration
                   else repo / adc.ROUTE_CALIBRATION)
    gate_map = json.loads(Path(args.map).read_text(encoding="utf-8"))

    if args.changes:
        changes = json.loads(Path(args.changes).read_text(encoding="utf-8"))
    else:
        if not args.since:
            print("REFUSED: --since or --changes is required")
            return 2
        changes = discover_changes(repo, args.since, args.branch)
    if args.save_changes:
        Path(args.save_changes).write_text(
            json.dumps(changes, indent=2) + "\n", encoding="utf-8", newline="\n")

    policy_source = json.loads(
        (calibration / "routing-policy.json").read_text(encoding="utf-8"))
    gates_source = json.loads(
        (calibration / "gates.json").read_text(encoding="utf-8"))
    catalog = json.loads((Path(__file__).resolve().parents[1] / "assets"
                          / "verification-capabilities.json").read_text(encoding="utf-8"))
    validated = route_module.load_policy(
        policy_source, gates_source, [c["id"] for c in catalog["capabilities"]],
        gates_source["canonical_full_set"])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for entry in changes:
        head = str(entry["head"])
        jobs = entry.get("jobs")
        if isinstance(jobs, str):
            jobs = json.loads(Path(jobs).read_text(encoding="utf-8"))
        if isinstance(jobs, Mapping):
            jobs = jobs.get("jobs", [])
        outcomes = (gate_outcomes_from_jobs(jobs, gate_map) if jobs
                    else {gate: "unresolved"
                          for gate in canonical_gate_ids(gates_source)})

        checkout = Path(tempfile.mkdtemp(prefix=f"adc-backfill-{head[:8]}-"))
        try:
            _git(repo, "worktree", "add", "--detach", "--force", str(checkout), head)
            snapshot = route_module.read_change_inputs(checkout, str(entry["base"]))
            facts = route_module.collect_change_facts(
                snapshot, validated.classifier_map())
            route = route_module.build_route(
                facts, validated, snapshot_ok=snapshot.complete)
            candidate = route_module.build_candidate_route(
                facts, validated, snapshot_ok=snapshot.complete)
        finally:
            subprocess.run(["git", "-C", str(repo), "worktree", "remove",
                            "--force", str(checkout)],
                           capture_output=True, text=True, timeout=120)
            shutil.rmtree(checkout, ignore_errors=True)

        record = build_record(
            policy_source=policy_source, gates_source=gates_source,
            route=route, candidate=candidate, outcomes=outcomes,
            base_outcomes=None,
            commits={"base": str(entry["base"]), "merge": str(entry["merge"]),
                     "head": head},
            run={"pull_request": entry.get("pull_request"),
                 "run_id": entry.get("run_id") or "",
                 "run_attempt": entry.get("run_attempt") or 0},
            head_ref=entry.get("head_ref"), backfill=True,
            router_blob_sha256=router_digest(Path(route_module.__file__)),
            shadow_result=adc.shadow_result,
        )
        errors = validate_record(record)
        if errors:
            print(f"REFUSED {head[:12]}: " + "; ".join(errors))
            return 2
        (out_dir / f"shadow-backfill-{head}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        written += 1
        print(f"  #{str(entry.get('pull_request') or '-'):>4} {head[:12]} "
              f"{record['status']:16} class={record['class_key'][:12]} "
              f"rules={','.join(record['class']['matched_rule_ids']) or '-'} "
              f"omitted={','.join(record['class']['omitted_gate_ids']) or '-'}")
    print(f"BACKFILL {written} record(s) in {out_dir}")
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

    p = sub.add_parser("outcomes",
                       help="Reduce a run attempt's jobs to one outcome per canonical gate")
    p.add_argument("--map", required=True, help="Gate-to-job mapping file")
    p.add_argument("--jobs", help="A saved jobs payload; omit to fetch from the API")
    p.add_argument("--repository", help="owner/name; defaults to GITHUB_REPOSITORY")
    p.add_argument("--run", help="Workflow run id")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_outcomes)

    p = sub.add_parser("backfill",
                       help="Replay today's router over historical change sets")
    p.add_argument("--repo", default=".")
    p.add_argument("--calibration")
    p.add_argument("--map", required=True)
    p.add_argument("--since", help="Replay merges after this commit")
    p.add_argument("--branch", default="HEAD")
    p.add_argument("--changes", help="A saved discovery file; skips the network")
    p.add_argument("--save-changes", help="Write what discovery found")
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=command_backfill)
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

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
from datetime import datetime
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

# Every key a record carries, so an unknown one is refused rather than
# ignored. The schema says `additionalProperties: false` and nothing on the
# ingest path reads the schema, so the validator has to say it too.
RECORD_KEYS = (
    "schema_version", "schema", "record_id", "provenance", "head_ref",
    "status", "measurable", "not_measurable_reason", "inconclusive_reason",
    "commits", "base_reconstructed", "run", "class_key", "class", "audit",
    "gate_outcomes", "base_gate_outcomes", "shadow",
)

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
    base_reconstructed: bool = False,
    unmeasurable_reason: str | None = None,
) -> dict[str, Any]:
    """One record, in the order the brief defines it."""
    gates = canonical_gate_ids(gates_source)
    outcomes = {str(k): str(v) for k, v in outcomes.items()}
    measurable, reason = measurability(outcomes, gates, candidate)
    if not measurable and unmeasurable_reason:
        # D-128: a head whose commit no longer exists is not the same silence
        # as a snapshot that would not read. The caller names which.
        reason = unmeasurable_reason

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
        # D-128. A backfilled record's base is computed now, from the commit
        # that landed the pull request, because the merge commit CI checked
        # out is not recoverable afterwards. A live record's base came from
        # the event payload and is not reconstructed.
        "base_reconstructed": bool(base_reconstructed),
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
    if record.get("schema") != SCHEMA_NAME:
        errors.append(f"schema must be {SCHEMA_NAME!r}")
    unknown = sorted(set(record) - set(RECORD_KEYS))
    if unknown:
        errors.append(f"unknown key(s): {', '.join(unknown)}")
    if "base_reconstructed" in record:
        if not isinstance(record.get("base_reconstructed"), bool):
            errors.append("base_reconstructed must be boolean")
    elif str(record.get("provenance")) == "backfill":
        # Required of a backfill, whose base is computed after the fact and
        # must say so. A record without the key at all predates it, which
        # only the live and canary records CI wrote before D-128 do, and a
        # live record's base came from the event payload and was never
        # reconstructed. Absent is therefore unambiguous for those, and a
        # silent false for a backfill would be a lie.
        errors.append("a backfilled record must carry base_reconstructed")
    if record.get("status") not in {
            STATUS_MISS, STATUS_CLEAN, STATUS_INCONCLUSIVE, STATUS_NO_OMISSION,
            STATUS_SELECTS_NOTHING, STATUS_NOT_MEASURABLE}:
        errors.append(f"unknown status: {record.get('status')!r}")
    if record.get("provenance") not in {"live", "backfill", "canary", "dominance"}:
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
    # D-133: the policy this record was built with, beside it, so ingest can
    # recompute the class rather than believe it. The live job's artifact
    # glob picks these up with the record.
    for name in write_policy_sidecars(out.parent, policy_source, gates_source):
        print(f"  policy sidecar {name}")
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


def repository_slug(repo: Path) -> str:
    """owner/name for the origin remote."""
    remote = _git(repo, "remote", "get-url", "origin")
    remote = remote.rstrip("/").removesuffix(".git").split(":")[-1]
    return "/".join(remote.split("/")[-2:])


def landing_commits(repo: Path, since: str, branch: str = "HEAD"
                    ) -> dict[int, dict[str, str]]:
    """Pull request number to the commit that landed it, and that commit's base.

    First parent, whether the landing was a merge commit or a squash. The
    first parent of a merge is the base branch as it stood at the merge, and
    the parent of a squash is the same thing, which is why one rule serves
    both and why D-128 takes the base from here rather than from the pull
    request API, whose `base.sha` is where the branch pointed when the pull
    request was opened.
    """
    log = _git(repo, "log", "--first-parent", "--format=%H\x1f%P\x1f%s",
               f"{since}..{branch}" if since else branch)
    landings: dict[int, dict[str, str]] = {}
    for line in log.splitlines():
        if not line.strip():
            continue
        landing, parents, subject = line.split("\x1f", 2)
        parent_ids = parents.split()
        if not parent_ids:
            continue
        number = None
        for token in subject.replace(":", " ").replace("(", " ").replace(")", " ").split():
            if token.startswith("#") and token[1:].isdigit():
                number = int(token[1:])
                break
        if number is None or number in landings:
            continue
        landings[number] = {"landing": landing, "first_parent": parent_ids[0],
                            "subject": subject}
    return landings


def discover_pull_request_runs(
    repo: Path, since: str, branch: str = "HEAD", workflow_name: str = "Tests",
    repository: str | None = None, max_pages: int = 20,
) -> list[dict[str, Any]]:
    """Every `pull_request` run attempt of every merged pull request since `since`.

    D-128: the population is the pull request's own runs, not the merge that
    survived them, because a merge is a change whose run already passed the
    checks that gated it and cannot show what they caught.

    A run's `pull_requests` field empties once the branch is merged, so the
    join is on head repository and branch, which the runs listing always
    carries, and `/commits/{sha}/pulls` resolves whatever that leaves. Every
    attempt is enumerated, not only the last, because a rerun does not
    replace the attempt it supersedes.
    """
    slug = repository or repository_slug(repo)
    landings = landing_commits(repo, since, branch)

    runs: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        payload = _gh_json([f"/repos/{slug}/actions/runs"
                            f"?event=pull_request&per_page=100&page={page}"])
        batch = payload.get("workflow_runs", [])
        runs.extend(run for run in batch if run.get("name") == workflow_name)
        if len(batch) < 100:
            break

    # Head repository and branch name the pull request even after the merge.
    by_branch: dict[tuple[str, str], int] = {}
    for number in landings:
        pull = _gh_json([f"/repos/{slug}/pulls/{number}"])
        head = pull.get("head") or {}
        head_repo = ((head.get("repo") or {}).get("full_name") or "")
        by_branch[(str(head_repo), str(head.get("ref") or ""))] = number

    entries: list[dict[str, Any]] = []
    resolved: dict[str, int | None] = {}
    for run in runs:
        head_repo = str(((run.get("head_repository") or {}).get("full_name")) or "")
        key = (head_repo, str(run.get("head_branch") or ""))
        number = by_branch.get(key)
        if number is None:
            named = [p.get("number") for p in (run.get("pull_requests") or [])]
            number = named[0] if named else None
        if number is None:
            head_sha = str(run.get("head_sha") or "")
            if head_sha not in resolved:
                try:
                    pulls = _gh_json([f"/repos/{slug}/commits/{head_sha}/pulls"])
                except ShadowError:
                    pulls = []
                resolved[head_sha] = (int(pulls[0]["number"]) if pulls else None)
            number = resolved[head_sha]
        if number is None or number not in landings:
            continue

        landing = landings[number]
        head = str(run.get("head_sha") or "")
        attempts = int(run.get("run_attempt", 1) or 1)
        for attempt in range(1, attempts + 1):
            try:
                jobs = _gh_json([
                    f"/repos/{slug}/actions/runs/{run['id']}/attempts/{attempt}"
                    f"/jobs?per_page=100"]).get("jobs", [])
            except ShadowError:
                jobs = []
            entries.append({
                "pull_request": number,
                "head": head,
                "head_ref": run.get("head_branch") or "",
                "landing": landing["landing"],
                "landing_first_parent": landing["first_parent"],
                "subject": landing["subject"],
                "run_id": str(run["id"]),
                "run_attempt": attempt,
                "run_conclusion": run.get("conclusion"),
                "jobs": jobs,
            })
    entries.sort(key=lambda item: (item["pull_request"], item["run_id"],
                                   item["run_attempt"]))
    return entries


def _commit_present(repo: Path, sha: str) -> bool:
    done = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                          capture_output=True, text=True, timeout=120)
    return done.returncode == 0


def _historical_runner(route_module, repo: Path, head: str):
    """The production acquisition, pointed at a commit instead of a checkout.

    `read_change_inputs` reads `HEAD`, which a backfill would otherwise have
    to check out: about forty-five seconds a change on a large tree, and
    hours for a campaign. This substitutes the commit for the literal token,
    so every git command, flag, parser, fingerprint and problem code stays
    the production one.

    It also answers the index, worktree and untracked sources with silence,
    which is what they are for a commit. Those three describe the repository
    now, and now is not the change being measured: the first run of this
    backfill read four files this build had not yet committed and the
    thirty-three records the run was itself writing, and every record it
    produced was a reading of the present wearing a historical head. A fresh
    detached checkout gives the same silence, which is why the field study,
    which ran against a clean scratch clone, did not show it.
    """
    base_runner = route_module._default_runner(repo)

    def runner(argv):
        tokens = [str(token) for token in argv]
        # The index (`--cached`), the worktree (`--no-textconv`), and the
        # untracked scan (`ls-files --others`). _DIFF_FLAGS carries none of
        # these, so the committed comparison is never caught by them.
        #
        # The untracked test is `--others`, not `ls-files` alone, because
        # `_repo_fingerprint` also lists tracked files with `ls-files`, and
        # silencing that would leave the acquisition boundary watching
        # nothing: no ADC-ROUTE-BOUNDARY-VIOLATED could then fire, while the
        # snapshot still called itself complete.
        if ("--cached" in tokens or "--no-textconv" in tokens
                or ("ls-files" in tokens and "--others" in tokens)):
            return b""
        return base_runner([head if token == "HEAD" else token for token in tokens])

    return runner


def _push_outcomes(slug: str, sha: str, gate_map: Mapping[str, Any],
                   workflow_name: str, cache: dict[str, dict[str, str] | None],
                   ) -> dict[str, str] | None:
    """The base commit's own run, so an inherited failure is not read as a miss."""
    if sha in cache:
        return cache[sha]
    try:
        # event=push, because the base's own run is what tells an inherited
        # failure from a miss. Without the filter a base that is another
        # pull request's head returns that pull request's merge-ref run,
        # which is a different change.
        payload = _gh_json([f"/repos/{slug}/actions/runs"
                            f"?head_sha={sha}&event=push&per_page=50"])
    except ShadowError:
        cache[sha] = None
        return None
    runs = [run for run in payload.get("workflow_runs", [])
            if run.get("name") == workflow_name]
    if not runs:
        cache[sha] = None
        return None
    run = max(runs, key=lambda item: int(item.get("run_attempt", 1) or 1))
    try:
        jobs = _gh_json([
            f"/repos/{slug}/actions/runs/{run['id']}/attempts/"
            f"{int(run.get('run_attempt', 1) or 1)}/jobs?per_page=100"]).get("jobs", [])
    except ShadowError:
        cache[sha] = None
        return None
    cache[sha] = gate_outcomes_from_jobs(jobs, gate_map) if jobs else None
    return cache[sha]


def command_backfill(args: argparse.Namespace, adc_module=None) -> int:
    """Replay today's router over a pull request's own run history.

    Not a reconstruction at each head: the candidate builder did not exist at
    the earliest heads and the policy differed across the stack, so per-head
    keys would be classes of one. Today's router and today's policy over the
    historical change set, keyed by today's digests, is what the brief's
    section 5 defines, and every record carries `provenance: backfill`.

    The population is the pull request's runs, every attempt, never the merge
    that survived them: D-128, on the field study's measurement that a merge
    is a change whose run already passed the checks that gated it.
    """
    adc = _adc_module(adc_module)
    route_module, _ = adc.load_router_helpers()
    repo = Path(args.repo).resolve()
    calibration = (Path(args.calibration).resolve() if args.calibration
                   else repo / adc.ROUTE_CALIBRATION)
    gate_map = json.loads(Path(args.map).read_text(encoding="utf-8"))

    if args.changes:
        changes = json.loads(Path(args.changes).read_text(encoding="utf-8"))
    else:
        # No --since means the whole branch. The window is an option, not a
        # requirement: making it mandatory is how the first run of this
        # backfill covered nine of thirty-five pull requests without saying
        # so, which the implementation challenge found.
        changes = discover_pull_request_runs(
            repo, args.since or "", args.branch, workflow_name=args.workflow)
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
    router_sha = router_digest(Path(route_module.__file__))

    # A head and attempt CI already recorded live is never backfilled: the
    # live record was built on the tree CI verified, and this one would be
    # built on a reconstructed base. The live record wins.
    already: set[tuple[str, str]] = set()
    for directory in (args.live_records or []):
        for path in sorted(Path(directory).glob("*.json")):
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if str(existing.get("provenance")) == "backfill":
                continue
            already.add((str(existing.get("commits", {}).get("head", "")),
                         str(existing.get("run", {}).get("run_attempt", ""))))

    # Resolved only if a base outcome is actually wanted. A saved discovery
    # file needs no network at all, and a fixture repository has no remote;
    # refusing there would make the offline path depend on the online one.
    slug: str | None = args.repository
    if slug is None:
        try:
            slug = repository_slug(repo)
        except ShadowError:
            slug = None

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_cache: dict[str, dict[str, str] | None] = {}
    written = skipped = 0
    for entry in changes:
        head = str(entry["head"])
        attempt = int(entry.get("run_attempt") or 0)
        if (head, str(attempt)) in already:
            skipped += 1
            continue

        jobs = entry.get("jobs")
        if isinstance(jobs, str):
            jobs = json.loads(Path(jobs).read_text(encoding="utf-8"))
        if isinstance(jobs, Mapping):
            jobs = jobs.get("jobs", [])
        outcomes = (gate_outcomes_from_jobs(jobs, gate_map) if jobs
                    else {gate: "unresolved"
                          for gate in canonical_gate_ids(gates_source)})

        base = ""
        route = candidate = None
        unmeasurable_reason = None
        if not _commit_present(repo, head):
            # A force-pushed or deleted-fork head has no object to diff. That
            # is recorded, not dropped: a campaign that silently skipped it
            # would overstate its own coverage, as D-127 said of a missing run.
            unmeasurable_reason = "head-unavailable"
            base = str(entry.get("landing_first_parent") or "")
        else:
            first_parent = str(entry.get("landing_first_parent") or "")
            base = _git(repo, "merge-base", head, first_parent) if first_parent else ""
            snapshot = route_module.read_change_inputs(
                repo, base, runner=_historical_runner(route_module, repo, head))
            facts = route_module.collect_change_facts(
                snapshot, validated.classifier_map())
            route = route_module.build_route(
                facts, validated, snapshot_ok=snapshot.complete)
            candidate = route_module.build_candidate_route(
                facts, validated, snapshot_ok=snapshot.complete)

        base_outcomes = (_push_outcomes(slug, base, gate_map, args.workflow,
                                        base_cache)
                         if base and slug and not args.no_base_outcomes else None)
        record = build_record(
            policy_source=policy_source, gates_source=gates_source,
            route=route, candidate=candidate, outcomes=outcomes,
            base_outcomes=base_outcomes,
            commits={"base": base or "unavailable",
                     "merge": str(entry.get("landing") or head),
                     "head": head},
            run={"pull_request": entry.get("pull_request"),
                 "run_id": entry.get("run_id") or "",
                 "run_attempt": attempt},
            head_ref=entry.get("head_ref"), backfill=True,
            router_blob_sha256=router_sha, shadow_result=adc.shadow_result,
            base_reconstructed=True, unmeasurable_reason=unmeasurable_reason,
        )
        errors = validate_record(record)
        if errors:
            print(f"REFUSED {head[:12]}: " + "; ".join(errors))
            return 2
        (out_dir / f"shadow-{head}-{attempt}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        written += 1
        print(f"  #{str(entry.get('pull_request') or '-'):>4} {head[:12]}/{attempt} "
              f"{record['status']:16} class={record['class_key'][:12]} "
              f"rules={','.join(record['class']['matched_rule_ids']) or '-'} "
              f"omitted={','.join(record['class']['omitted_gate_ids']) or '-'}")
    # D-133, once per distinct digest rather than once per record.
    for name in write_policy_sidecars(out_dir, policy_source, gates_source):
        print(f"  policy sidecar {name}")
    print(f"BACKFILL {written} record(s) in {out_dir}"
          + (f", {skipped} already live" if skipped else ""))
    return 0


def policy_sidecars(policy_source: Mapping[str, Any],
                    gates_source: Mapping[str, Any]) -> dict[str, str]:
    """The stripped policy and gates a record was built with, named by digest.

    D-133. A record already carries `audit.policy_terms_sha256` and
    `audit.gates_terms_sha256`; what was missing is the bytes those digests
    name, without which ingest cannot recompute the class and the class is a
    claim. A file named by the digest of its own content is self-certifying,
    so nothing about where it was kept needs trusting.
    """
    policy_terms = strip_underscored(policy_source)
    gates_terms = strip_underscored(gates_source)
    return {
        f"policy-{digest(policy_terms)}.json": canonical_json(policy_terms) + "\n",
        f"gates-{digest(gates_terms)}.json": canonical_json(gates_terms) + "\n",
    }


def write_policy_sidecars(out_dir: Path, policy_source: Mapping[str, Any],
                          gates_source: Mapping[str, Any]) -> list[str]:
    """Write the sidecars beside a record, once per distinct digest."""
    written: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, body in policy_sidecars(policy_source, gates_source).items():
        target = out_dir / name
        if target.exists():
            continue
        target.write_text(body, encoding="utf-8", newline="\n")
        written.append(name)
    return written


def _digests_to_its_name(name: str, body: str) -> bool:
    """A sidecar is trusted only because its content hashes to its name."""
    stem = Path(name).stem
    _, _, claimed = stem.partition("-")
    try:
        return digest(json.loads(body)) == claimed
    except json.JSONDecodeError:
        return False


def _load_route_module_at(repo: Path, commit: str | None, expected_digest: str):
    """The router that built a record, checked against the digest it names.

    Where that router is depends on what kind of record it is, and getting
    this wrong reads as a broken record rather than a broken lookup. A live
    or canary record was built by the workflow running at its own head, so
    the router at that head is the one. A backfill record was built by
    replaying today's router over a historical change set, which is what
    D-127 decided and D-128 kept, so its router is the one in the checkout
    that ran the backfill, and the router at its head is a different version
    that never touched it. `commit` is None for that second case.
    """
    import importlib.util
    import tempfile

    if commit is None:
        source = (repo / "anti-dark-code" / "scripts" / "adc_route.py").read_bytes()
    else:
        try:
            source = _git_bytes(repo, "show",
                                f"{commit}:anti-dark-code/scripts/adc_route.py")
        except ShadowError as error:
            raise ShadowError(f"router-unrecoverable: {error}") from error
    actual = hashlib.sha256(source).hexdigest()
    if actual != expected_digest:
        where = f"at {commit[:12]}" if commit else "in this checkout"
        raise ShadowError(
            f"router-unrecoverable: the router {where} digests to "
            f"{actual[:12]} and the record names {expected_digest[:12]}")
    handle = Path(tempfile.mkdtemp(prefix="adc-router-")) / "adc_route.py"
    handle.write_bytes(source)
    name = f"adc_route_{actual[:12]}"
    spec = importlib.util.spec_from_file_location(name, handle)
    module = importlib.util.module_from_spec(spec)
    # Registered before execution: the router defines dataclasses, and
    # dataclasses resolves a field's type through sys.modules[cls.__module__],
    # which is None for a module that has been created and not registered.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git_bytes(repo: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, timeout=300)
    if done.returncode != 0:
        raise ShadowError(
            f"git {' '.join(args)} failed: "
            f"{done.stderr.decode('utf-8', 'replace').strip()[:200]}")
    return done.stdout


def recompute_class(record: Mapping[str, Any], *, repo: Path,
                    policy_source: Mapping[str, Any],
                    gates_source: Mapping[str, Any],
                    capability_ids: Sequence[str]) -> list[str]:
    """Rebuild the record's class from the policy that built it. D-133.

    G10 says ingest recomputes the route. Recomputing the verdict, which the
    implementation challenge forced, needs no policy and so was done first;
    the class needs the policy, the gates and the router the record names,
    and until all three are at hand the matched rules, the selected and
    omitted gates and the key are believed as written.
    """
    problems: list[str] = []
    klass = record.get("class") or {}
    commits = record.get("commits") or {}
    head = str(commits.get("head", ""))
    base = str(commits.get("base", ""))
    if not head or not base or base == "unavailable":
        return [f"the record names no usable base and head, so its class "
                f"cannot be recomputed"]
    if not _commit_present(repo, head):
        return [f"head {head[:12]} is not present, so the class cannot be "
                f"recomputed"]

    # A backfill replayed today's router; a live or canary record was built
    # by the router at its own head. See _load_route_module_at.
    at = None if str(record.get("provenance")) == "backfill" else head
    try:
        route_module = _load_route_module_at(
            repo, at, str(klass.get("router_blob_sha256", "")))
    except ShadowError as error:
        return [str(error)]

    try:
        validated = route_module.load_policy(
            policy_source, gates_source, list(capability_ids),
            gates_source["canonical_full_set"])
    except Exception as error:  # the router's own PolicyError and friends
        return [f"the stored policy does not load: {error}"]

    snapshot = route_module.read_change_inputs(
        repo, base, runner=_historical_runner(route_module, repo, head))
    facts = route_module.collect_change_facts(snapshot, validated.classifier_map())
    candidate = route_module.build_candidate_route(
        facts, validated, snapshot_ok=snapshot.complete)

    if candidate is None:
        recomputed_rules: list[str] = []
        recomputed_selected: list[str] = []
        recomputed_omitted: list[str] = []
    else:
        gates = canonical_gate_ids(gates_source)
        recomputed_rules = sorted(candidate.matched_rule_ids)
        recomputed_selected = sorted(candidate.selected_gate_ids())
        recomputed_omitted = sorted(set(gates) - set(recomputed_selected))
        if candidate.force_full:
            recomputed_omitted = []
            recomputed_selected = sorted(gates)

    for field, recorded, recomputed in (
            ("matched_rule_ids", sorted(klass.get("matched_rule_ids", ())), recomputed_rules),
            ("selected_gate_ids", sorted(klass.get("selected_gate_ids", ())), recomputed_selected),
            ("omitted_gate_ids", sorted(klass.get("omitted_gate_ids", ())), recomputed_omitted)):
        if recorded != recomputed:
            problems.append(
                f"class.{field} does not follow from the stored policy: the "
                f"record says {recorded} and the recomputation gives {recomputed}")

    if not problems:
        terms = class_terms(policy_source, gates_source, recomputed_rules)
        key = class_key(terms, str(klass.get("router_blob_sha256", "")),
                        recomputed_omitted)
        if key != str(record.get("class_key")):
            problems.append(
                f"class_key does not follow from the stored policy: the record "
                f"says {str(record.get('class_key'))[:12]} and the "
                f"recomputation gives {key[:12]}")
    return problems


def _recompute_with_sidecars(record: Mapping[str, Any], *, repo: Path,
                             sidecars: Mapping[str, str],
                             capability_ids: Sequence[str]) -> list[str]:
    """Find the policy a record names and recompute its class with it. D-133.

    A live record whose sidecar is absent everywhere is recovered once from
    the calibration at its own head, which is the tree that ran; a backfill
    record in that state is refused, because the backfill wrote the sidecar
    and its absence means something else is wrong.
    """
    audit = record.get("audit") or {}
    policy_name = f"policy-{audit.get('policy_terms_sha256')}.json"
    gates_name = f"gates-{audit.get('gates_terms_sha256')}.json"
    policy_body = sidecars.get(policy_name)
    gates_body = sidecars.get(gates_name)

    if policy_body is None or gates_body is None:
        provenance = str(record.get("provenance"))
        if provenance == "backfill":
            return [f"no stored policy for this record ({policy_name}), and a "
                    f"backfill writes its own, so it is not recovered"]
        head = str((record.get("commits") or {}).get("head", ""))
        if not head or not _commit_present(repo, head):
            return [f"no stored policy for this record ({policy_name}) and its "
                    f"head is not present to recover one from"]
        recovered = {}
        for name, path in ((policy_name, ".agents/skills/anti-dark-code/"
                                         "calibration/routing-policy.json"),
                           (gates_name, ".agents/skills/anti-dark-code/"
                                        "calibration/gates.json")):
            try:
                raw = _git_bytes(repo, "show", f"{head}:{path}")
            except ShadowError as error:
                return [f"no stored policy for this record and the calibration "
                        f"at {head[:12]} could not be read: {error}"]
            terms = strip_underscored(json.loads(raw.decode("utf-8")))
            if digest(terms) != Path(name).stem.partition("-")[2]:
                return [f"the calibration at {head[:12]} does not digest to the "
                        f"{Path(name).stem.partition('-')[0]} the record names"]
            recovered[name] = canonical_json(terms) + "\n"
        policy_body, gates_body = recovered[policy_name], recovered[gates_name]

    return recompute_class(
        record, repo=repo,
        policy_source=json.loads(policy_body),
        gates_source=json.loads(gates_body),
        capability_ids=capability_ids)


def _ledger_paths(ledger_dir: Path) -> list[Path]:
    return sorted(ledger_dir.glob("*.jsonl"))


def read_ledger(ledger_dir: Path) -> list[dict[str, Any]]:
    """Every record the ledger holds, in file then line order."""
    records: list[dict[str, Any]] = []
    for path in _ledger_paths(ledger_dir):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def _is_ancestor(repo: Path, commit: str, of: str) -> bool:
    done = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, of],
        capture_output=True, text=True, timeout=120)
    return done.returncode == 0


def status_from(outcomes: Mapping[str, str], selected: Sequence[str],
                omitted: Sequence[str],
                base_outcomes: Mapping[str, str] | None) -> str:
    """Section 2's verdict, from outcomes and what a route would have run.

    Pure, and deliberately independent of any policy: it needs only which
    gates a candidate selected, which it omitted, and what each concluded.
    That is what lets ingest recompute a status across a classifier change
    without recomputing a class, which D-129 makes a moving target.
    """
    outcomes = {str(k): str(v) for k, v in outcomes.items()}
    gates = sorted(set(selected) | set(omitted))
    if any(outcomes.get(gate) not in DECIDED_OUTCOMES for gate in gates):
        return STATUS_NOT_MEASURABLE
    if not omitted:
        return STATUS_NO_OMISSION
    if not selected:
        return STATUS_SELECTS_NOTHING
    missed = [gate for gate in omitted if outcomes.get(gate) == "fail"]
    if missed:
        inherited = [gate for gate in missed
                     if base_outcomes and str(base_outcomes.get(gate)) == "fail"]
        return STATUS_INCONCLUSIVE if inherited else STATUS_MISS
    if all(outcomes.get(gate) == "pass" for gate in selected):
        return STATUS_CLEAN
    return STATUS_INCONCLUSIVE


def verify_record(record: Mapping[str, Any], *, repo: Path,
                  gate_map: Mapping[str, Any], slug: str | None,
                  main_ref: str, offline: bool) -> list[str]:
    """Why this record must not enter the ledger, or an empty list.

    G10: the record was built by the pull request's own workflow, so a pull
    request that edits the workflow could upload anything. Two things are
    therefore recomputed rather than believed. The outcomes are re-read from
    the API for the run and attempt the record names. The verdict is then
    recomputed from those outcomes and the gates the record says its
    candidate selected and omitted, and a record whose status does not follow
    is refused: without that, a record could report an omitted gate's failure
    truthfully and still call itself clean, and the summary would count it
    toward N. The class itself is not recomputed against today's policy,
    because the classifier legitimately changes and a record from before
    D-129 is not forged for saying so.
    """
    problems = list(validate_record(record))
    if problems:
        return problems

    body = {k: v for k, v in record.items() if k != "record_id"}
    if record.get("record_id") != digest(body):
        problems.append("record_id does not digest the record")

    provenance = str(record.get("provenance"))
    head = str(record.get("commits", {}).get("head", ""))

    # G8 again: provenance is derived, never asserted, so a record cannot
    # opt out of the canary rules by calling itself live.
    derived = provenance_for(record.get("head_ref"), provenance == "backfill")
    if derived == "canary" and provenance != "canary":
        problems.append(
            f"head_ref {record.get('head_ref')!r} is a canary branch but the "
            f"record claims provenance {provenance!r}")
        provenance = "canary"
    if provenance == "canary":
        # A canary is a branch that is never merged. One that has landed is
        # an ordinary change wearing a canary's name. A head this repository
        # does not have cannot be checked, so it is refused rather than
        # waved through.
        if not head or not _commit_present(repo, head):
            problems.append(
                f"canary head {head[:12] or '(none)'} is not present, so it "
                f"cannot be shown not to have landed")
        elif _is_ancestor(repo, head, main_ref):
            problems.append(f"canary head {head[:12]} is an ancestor of {main_ref}")

    if offline or not slug:
        return problems

    run_id = str(record.get("run", {}).get("run_id", ""))
    attempt = int(record.get("run", {}).get("run_attempt", 0) or 0)
    if not run_id or not attempt:
        problems.append(
            "the record names no run and attempt, so its outcomes cannot be "
            "re-read; ingest it with --offline if that is intended")
        return problems
    try:
        jobs = _gh_json([f"/repos/{slug}/actions/runs/{run_id}/attempts/{attempt}"
                         f"/jobs?per_page=100"]).get("jobs", [])
    except ShadowError as error:
        problems.append(f"outcomes could not be re-read: {error}")
        return problems
    recomputed = gate_outcomes_from_jobs(jobs, gate_map) if jobs else {}
    recorded = {str(k): str(v) for k, v in (record.get("gate_outcomes") or {}).items()}
    if recomputed != recorded:
        differing = sorted(set(recorded) | set(recomputed))
        detail = ", ".join(
            f"{gate}: recorded {recorded.get(gate)!r} but the run says "
            f"{recomputed.get(gate)!r}"
            for gate in differing
            if recorded.get(gate) != recomputed.get(gate))
        problems.append(f"outcomes disagree with the run: {detail}")
        return problems

    klass = record.get("class") or {}
    expected = status_from(
        recomputed,
        [str(gate) for gate in klass.get("selected_gate_ids", ())],
        [str(gate) for gate in klass.get("omitted_gate_ids", ())],
        record.get("base_gate_outcomes"))
    if expected != str(record.get("status")):
        problems.append(
            f"status does not follow from the run: the record says "
            f"{record.get('status')!r} and these outcomes give {expected!r}")
    return problems


def command_ingest(args: argparse.Namespace, adc_module=None) -> int:
    """Move verified records into the committed ledger.

    The artifact is an inbox, never the ledger: it is written by the pull
    request's own workflow. Everything that reaches the ledger has had its
    outcomes re-read from the API and its structure refused on disagreement.
    """
    repo = Path(args.repo).resolve()
    gate_map = json.loads(Path(args.map).read_text(encoding="utf-8"))
    ledger_dir = Path(args.ledger)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    slug: str | None = args.repository
    if slug is None and not args.offline:
        try:
            slug = repository_slug(repo)
        except ShadowError:
            slug = None

    known = {str(record.get("record_id")) for record in read_ledger(ledger_dir)}
    incoming: list[tuple[Path, dict[str, Any]]] = []
    # A sidecar is trusted only because its content hashes to its name, so a
    # bad one is refused here rather than copied and believed later. D-133.
    sidecars: dict[str, str] = {}
    policies_dir = ledger_dir.parent / "policies"
    for existing in sorted(policies_dir.glob("*.json")) if policies_dir.exists() else []:
        sidecars[existing.name] = existing.read_text(encoding="utf-8")
    offered: dict[str, str] = {}
    refused = 0
    for directory in args.source:
        for path in sorted(Path(directory).glob("*.json")):
            if path.name.startswith(("policy-", "gates-")):
                body = path.read_text(encoding="utf-8")
                if not _digests_to_its_name(path.name, body):
                    refused += 1
                    print(f"  REFUSED {path.name}: content does not digest to its name")
                    if not args.keep_going:
                        return 2
                    continue
                offered[path.name] = body
                continue
            try:
                incoming.append((path, json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError) as error:
                print(f"  REFUSED {path.name}: unreadable: {error}")
                if not args.keep_going:
                    return 2
    sidecars.update({k: v for k, v in offered.items() if k not in sidecars})

    catalog = json.loads((Path(__file__).resolve().parents[1] / "assets"
                          / "verification-capabilities.json").read_text(encoding="utf-8"))
    capability_ids = [c["id"] for c in catalog["capabilities"]]

    accepted: list[dict[str, Any]] = []
    for path, record in incoming:
        if str(record.get("record_id")) in known:
            continue
        problems = verify_record(record, repo=repo, gate_map=gate_map, slug=slug,
                                 main_ref=args.main, offline=args.offline)
        if not problems and not args.skip_class_recomputation:
            problems = _recompute_with_sidecars(
                record, repo=repo, sidecars=sidecars,
                capability_ids=capability_ids)
        if problems:
            refused += 1
            print(f"  REFUSED {path.name}: " + "; ".join(problems))
            if not args.keep_going:
                return 2
            continue
        accepted.append(record)
        known.add(str(record.get("record_id")))

    # Only the sidecars an accepted record actually names are kept, so the
    # directory holds the policies the ledger rests on and nothing else.
    if accepted:
        wanted = set()
        for record in accepted:
            audit = record.get("audit") or {}
            wanted.add(f"policy-{audit.get('policy_terms_sha256')}.json")
            wanted.add(f"gates-{audit.get('gates_terms_sha256')}.json")
        policies_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(wanted):
            body = sidecars.get(name)
            target = policies_dir / name
            if body is None or target.exists():
                continue
            target.write_text(body, encoding="utf-8", newline="\n")
            print(f"  kept {name}")

    # One file per ingest month, named by --month, so the ledger grows by
    # append and a month's bytes never move once written.
    by_month: dict[str, list[dict[str, Any]]] = {}
    for record in accepted:
        by_month.setdefault(args.month, []).append(record)
    written = 0
    for month, records in sorted(by_month.items()):
        target = ledger_dir / f"{month}.jsonl"
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        lines = [canonical_json(record) for record in
                 sorted(records, key=lambda item: str(item.get("record_id")))]
        target.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8",
                          newline="\n")
        written += len(lines)

    if args.write_pull_requests:
        # The criterion counts pull requests, over days, by distinct authors,
        # and a record carries none of that: it is deliberately timeless so
        # the summary is byte-reproducible. The join lives beside the ledger
        # rather than inside a record, so no record changes when it is
        # refreshed. The author is the pull request's own, not the commit's,
        # because every commit here is authored by one account.
        path = Path(args.write_pull_requests)
        existing: dict[str, Any] = {}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
        numbers = sorted({str(record.get("run", {}).get("pull_request"))
                          for record in read_ledger(ledger_dir)
                          if record.get("run", {}).get("pull_request") is not None})
        for number in numbers:
            if number in existing or not slug:
                continue
            try:
                pull = _gh_json([f"/repos/{slug}/pulls/{number}"])
            except ShadowError:
                continue
            existing[number] = {
                "author": str((pull.get("user") or {}).get("login") or ""),
                "merged_at": str(pull.get("merged_at") or ""),
                "title": str(pull.get("title") or "")[:120],
            }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
        print(f"  pull request metadata for {len(existing)} pull request(s)")

    print(f"INGEST {written} record(s) into {ledger_dir}"
          + (f", {refused} refused" if refused else ""))
    # A refusal is a refusal whether or not the run continued past it.
    # --keep-going reports every one; it does not forgive them.
    return 2 if refused else 0


def summarise(records: Sequence[Mapping[str, Any]],
              pulls: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The campaign's counts, per class, from the ledger bytes alone.

    D-128: N counts pull requests, not records. In one class a pull request
    advances N when it has at least one clean live record there and no miss;
    an inconclusive record neither adds nor removes; a miss on any attempt is
    the class's miss and is never removed. N is therefore a count that can
    fall when a later attempt misses, not a clock.
    """
    pulls = pulls or {}
    classes: dict[str, dict[str, Any]] = {}
    for record in records:
        key = str(record.get("class_key"))
        entry = classes.setdefault(key, {
            "class_key": key,
            "matched_rule_ids": list(record.get("class", {}).get("matched_rule_ids", [])),
            "omitted_gate_ids": list(record.get("class", {}).get("omitted_gate_ids", [])),
            "router_blob_sha256": str(record.get("class", {}).get("router_blob_sha256", "")),
            "records": {"live": 0, "backfill": 0, "canary": 0, "dominance": 0},
            "status": {},
            "_live_clean": set(),
            "_live_miss": set(),
            "_backfill_miss": set(),
            "_dominance": {},
            "canary_record_ids": [],
            "dominance_record_ids": [],
        })
        provenance = str(record.get("provenance"))
        status = str(record.get("status"))
        if provenance in entry["records"]:
            entry["records"][provenance] += 1
        entry["status"][status] = entry["status"].get(status, 0) + 1
        pull = record.get("run", {}).get("pull_request")
        pull_key = str(pull) if pull is not None else None
        if provenance == "dominance":
            # D-134: an exhaustive probe, not a sample. It is listed and
            # counted in neither N nor the misses, exactly as a canary is;
            # what it decides is whether the class needs either.
            entry["dominance_record_ids"].append(str(record.get("record_id")))
            probe = str(record.get("run", {}).get("run_id", "")).removeprefix(
                "dominance-")
            entry["_dominance"][probe] = status
        elif provenance == "canary":
            # G8: a canary is what shows the comparator sees failures. It is
            # never evidence for or against the class it demonstrates.
            entry["canary_record_ids"].append(str(record.get("record_id")))
        elif provenance == "live" and pull_key:
            if status == STATUS_CLEAN:
                entry["_live_clean"].add(pull_key)
            elif status == STATUS_MISS:
                entry["_live_miss"].add(pull_key)
        elif provenance == "backfill" and pull_key and status == STATUS_MISS:
            entry["_backfill_miss"].add(pull_key)

    out: list[dict[str, Any]] = []
    for key in sorted(classes):
        entry = classes[key]
        clean = entry.pop("_live_clean")
        missed = entry.pop("_live_miss")
        backfill_missed = entry.pop("_backfill_miss")
        probes = entry.pop("_dominance")
        # Dominated only when every probe ran and none of them found a
        # selected gate passing while an omitted one failed. A class with one
        # probe is a class nobody finished probing.
        dominated = (
            bool(probes)
            and all(probe in probes for probe in DOMINANCE_PROBES)
            and all(probes[probe] != STATUS_MISS for probe in DOMINANCE_PROBES))
        counted = sorted(clean - missed)
        authors = sorted({str(pulls.get(pull, {}).get("author", ""))
                          for pull in counted} - {""})
        landed = sorted(str(pulls.get(pull, {}).get("merged_at", ""))
                        for pull in counted)
        landed = [stamp for stamp in landed if stamp]
        span_days = None
        if len(landed) >= 2:
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            span_days = (datetime.strptime(landed[-1], fmt)
                         - datetime.strptime(landed[0], fmt)).days
        entry.update({
            "status": dict(sorted(entry["status"].items())),
            "criterion": {
                "pull_requests_counted": len(counted),
                "pull_requests": counted,
                "pull_requests_with_a_miss": sorted(missed),
                "distinct_authors": len(authors),
                "authors": authors,
                "span_days": span_days,
                "backfill_pull_requests_with_a_miss": sorted(backfill_missed),
                "canaries": len(entry["canary_record_ids"]),
                "dominance_probes": dict(sorted(probes.items())),
                "dominated": dominated,
            },
            "canary_record_ids": sorted(entry["canary_record_ids"]),
            "dominance_record_ids": sorted(entry["dominance_record_ids"]),
        })
        out.append(entry)

    totals: dict[str, int] = {}
    for record in records:
        totals[str(record.get("provenance"))] = (
            totals.get(str(record.get("provenance")), 0) + 1)
    return {
        "schema_version": SCHEMA_VERSION,
        "records": len(records),
        "records_by_provenance": dict(sorted(totals.items())),
        "classes": out,
    }


def command_summary(args: argparse.Namespace, adc_module=None) -> int:
    """Regenerate the summary from the ledger bytes. Deterministic by design."""
    ledger_dir = Path(args.ledger)
    records = read_ledger(ledger_dir)
    pulls: dict[str, Any] = {}
    if args.pull_requests and Path(args.pull_requests).exists():
        pulls = json.loads(Path(args.pull_requests).read_text(encoding="utf-8"))
    payload = summarise(records, pulls)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"SUMMARY {len(records)} record(s), {len(payload['classes'])} class(es) "
          f"in {out}")
    for entry in payload["classes"]:
        criterion = entry["criterion"]
        print(f"  {entry['class_key'][:12]} "
              f"omits={','.join(entry['omitted_gate_ids']) or '-':28} "
              f"N={criterion['pull_requests_counted']} "
              f"misses={len(criterion['pull_requests_with_a_miss'])} "
              f"canaries={criterion['canaries']}")
    return 0


DOMINANCE_PROBES = ("deleted", "replaced")


def class_covered_paths(repo: Path, policy_source: Mapping[str, Any],
                        route_module, class_rule_ids: Sequence[str]) -> list[str]:
    """Every tracked path whose facts would match one of the class's rules.

    The class is what its rules match, so the paths it covers are the paths
    the classifier gives facts those rules fire on. Enumerating the tree
    rather than the globs is what makes the probe exhaustive: a glob can be
    read two ways, a file list cannot.
    """
    tracked = _git(repo, "ls-files").splitlines()
    validated_rules = {rule for rule in class_rule_ids}
    classifier = {"surfaces": policy_source.get("classifier", {}).get("surfaces", [])}
    covered: list[str] = []
    for path in tracked:
        path = path.strip()
        if not path:
            continue
        matches = route_module._matching_classifications(path, classifier)
        if not matches:
            continue
        rules_here = set()
        for attrs in matches:
            for rule in policy_source.get("rules", []):
                match = rule.get("match", {})
                surfaces = match.get("surfaces")
                effects = match.get("effects")
                if surfaces and attrs["surface"] not in surfaces:
                    continue
                if effects and attrs["effect"] not in effects:
                    continue
                if match.get("mode_changed") or match.get("paths"):
                    continue
                if not surfaces and not effects:
                    continue
                rules_here.add(str(rule.get("id")))
        if rules_here and rules_here == validated_rules:
            covered.append(path)
    return sorted(covered)


def command_dominance(args: argparse.Namespace, adc_module=None) -> int:
    """Prove a class no gate reads cannot hide a failure. D-134.

    A canary is one hand-built probe, and for a class the gates can see, one
    probe plus a sample is enough. For a class the gates cannot see, a sample
    of clean records shows only that nothing happened, so the honest evidence
    is exhaustive: break every path the class covers, twice, and record what
    every gate concluded. The class is dominated when no probe leaves a
    selected gate passing while an omitted gate fails.

    It executes gates, so it obeys the same confirmation the gate runner
    does, and it executes everything rather than anything selectively.
    """
    import shutil

    adc = _adc_module(adc_module)
    route_module, _ = adc.load_router_helpers()
    repo = Path(args.repo).resolve()
    calibration = (Path(args.calibration).resolve() if args.calibration
                   else repo / adc.ROUTE_CALIBRATION)
    policy_source = json.loads(
        (calibration / "routing-policy.json").read_text(encoding="utf-8"))
    gates_source = json.loads(
        (calibration / "gates.json").read_text(encoding="utf-8"))

    if not gates_source.get("execution_policy", {}).get(
            "owner_confirmed_safe_to_execute"):
        print("REFUSED: the dominance probe runs every gate, and gates.json "
              "does not record owner confirmation. Review the commands, then "
              "set execution_policy.owner_confirmed_safe_to_execute to true.")
        return 2

    status = _git(repo, "status", "--porcelain")
    if status.strip():
        print("REFUSED: the probe rewrites and restores tracked files, so it "
              "requires a clean tree; commit or stash first.")
        return 2

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    entry = next((c for c in summary.get("classes", [])
                  if str(c.get("class_key")).startswith(args.class_key)), None)
    if entry is None:
        print(f"REFUSED: no class in {args.summary} begins {args.class_key}")
        return 2
    rule_ids = list(entry.get("matched_rule_ids", []))
    omitted = list(entry.get("omitted_gate_ids", []))
    selected = list(entry.get("selected_gate_ids", []))
    if not omitted:
        print(f"REFUSED: class {entry['class_key'][:12]} omits nothing, so "
              f"there is nothing for a probe to hide behind.")
        return 2

    covered = class_covered_paths(repo, policy_source, route_module, rule_ids)
    if not covered:
        print(f"REFUSED: class {entry['class_key'][:12]} covers no tracked "
              f"path, so an exhaustive probe would prove nothing.")
        return 2

    print(f"  class {entry['class_key'][:12]} rules={','.join(rule_ids)}")
    print(f"  covers {len(covered)} tracked path(s); omits {','.join(omitted)}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    originals = {path: (repo / path).read_bytes() for path in covered}
    before = {path: hashlib.sha256(body).hexdigest()
              for path, body in originals.items()}
    router_sha = router_digest(Path(route_module.__file__))
    head = _git(repo, "rev-parse", "HEAD")
    written = 0
    verdicts: dict[str, str] = {}

    for probe in DOMINANCE_PROBES:
        try:
            for path in covered:
                target = repo / path
                if probe == "deleted":
                    target.unlink()
                else:
                    # Content that is not the original, and not empty: an
                    # empty file is a shape some readers accept.
                    target.write_bytes(b"dominance probe: this is not the "
                                       b"content this file had\n")
            outcomes = _run_every_gate(adc, repo, gates_source, args.allow_exec)
        finally:
            for path, body in originals.items():
                target = repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
        after = {path: hashlib.sha256((repo / path).read_bytes()).hexdigest()
                 for path in covered}
        if after != before:
            print("REFUSED: the tree was not restored after the probe; "
                  "the following paths differ: "
                  + ", ".join(p for p in covered if after[p] != before[p]))
            return 2

        status = status_from(outcomes, selected, omitted, None)
        verdicts[probe] = status
        record = build_record(
            policy_source=policy_source, gates_source=gates_source,
            route=None, candidate=None, outcomes=outcomes, base_outcomes=None,
            commits={"base": head, "merge": head, "head": head},
            run={"pull_request": None, "run_id": f"dominance-{probe}",
                 "run_attempt": 1},
            head_ref=None, backfill=False, router_blob_sha256=router_sha,
            shadow_result=adc.shadow_result)
        # The probe is not a route: it says what the gates concluded when the
        # class's own paths were broken, under the class the summary names.
        record["provenance"] = "dominance"
        record["status"] = status
        record["measurable"] = status not in (STATUS_NOT_MEASURABLE,)
        record["class"] = {
            "matched_rule_ids": sorted(rule_ids),
            "selected_gate_ids": sorted(selected),
            "omitted_gate_ids": sorted(omitted),
            "router_blob_sha256": router_sha,
            "terms_sha256": str(entry.get("terms_sha256", "")),
        }
        record["class_key"] = str(entry["class_key"])
        record["gate_outcomes"] = dict(sorted(outcomes.items()))
        record["not_measurable_reason"] = (
            None if record["measurable"] else "a gate did not decide")
        record["record_id"] = digest(
            {k: v for k, v in record.items() if k != "record_id"})
        (out_dir / f"shadow-dominance-{probe}-{entry['class_key'][:12]}.json"
         ).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
        written += 1
        print(f"  probe {probe:9} {status:16} "
              f"outcomes={json.dumps(record['gate_outcomes'])}")

    for name in write_policy_sidecars(out_dir, policy_source, gates_source):
        print(f"  policy sidecar {name}")
    dominated = all(verdicts[probe] != STATUS_MISS for probe in DOMINANCE_PROBES)
    print(f"DOMINANCE {written} probe(s) in {out_dir}: class "
          f"{entry['class_key'][:12]} is "
          + ("dominated" if dominated else "NOT dominated"))
    return 0


def _run_every_gate(adc, repo: Path, gates_source: Mapping[str, Any],
                    allow_exec: bool) -> dict[str, str]:
    """Every canonical gate's own command, run here. Never a subset."""
    outcomes: dict[str, str] = {}
    for gate in gates_source.get("gates", []):
        gate_id = str(gate.get("id"))
        argv = gate.get("argv")
        if not argv:
            outcomes[gate_id] = "config-error"
            continue
        if not allow_exec:
            outcomes[gate_id] = "not-run"
            continue
        done = subprocess.run(
            list(argv), cwd=str(Path(gate.get("cwd", ".")) if Path(
                gate.get("cwd", ".")).is_absolute() else repo / gate.get("cwd", ".")),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=int(gate.get("timeout_seconds", 3600)))
        outcomes[gate_id] = "pass" if done.returncode == 0 else "fail"
    return outcomes


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

    p = sub.add_parser(
        "backfill",
        help="Replay today's router over merged pull requests' own run history")
    p.add_argument("--repo", default=".")
    p.add_argument("--calibration")
    p.add_argument("--map", required=True)
    p.add_argument("--since",
                   help="Replay pull requests landed after this commit; "
                        "omit for the whole branch, which is the honest default")
    p.add_argument("--branch", default="HEAD")
    p.add_argument("--workflow", default="Tests",
                   help="Workflow name whose runs carry the gates")
    p.add_argument("--repository", help="owner/name; defaults to the origin remote")
    p.add_argument("--changes", help="A saved discovery file; skips the network")
    p.add_argument("--save-changes", help="Write what discovery found")
    p.add_argument("--live-records", action="append", default=[],
                   help="A directory of live records; their head and attempt "
                        "are never backfilled")
    p.add_argument("--no-base-outcomes", action="store_true",
                   help="Skip reading each base commit's own run, which is "
                        "what tells an inherited failure from a miss")
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=command_backfill)

    p = sub.add_parser("ingest",
                       help="Verify records and append them to the ledger")
    p.add_argument("--repo", default=".")
    p.add_argument("--map", required=True)
    p.add_argument("--source", action="append", required=True,
                   help="A directory of records; repeatable")
    p.add_argument("--ledger", default="metrics/shadow/ledger")
    p.add_argument("--month", required=True,
                   help="Ledger file to append to, as yyyy-mm")
    p.add_argument("--main", default="origin/main",
                   help="Ref a canary head must not be an ancestor of")
    p.add_argument("--repository", help="owner/name; defaults to the origin remote")
    p.add_argument("--offline", action="store_true",
                   help="Skip re-reading outcomes from the API, which is the "
                        "check that makes an uploaded record more than a claim")
    p.add_argument("--keep-going", action="store_true",
                   help="Report every refusal instead of stopping at the first")
    p.add_argument("--write-pull-requests",
                   help="Refresh the pull request author and merge date the "
                        "criterion needs, beside the ledger")
    p.add_argument("--skip-class-recomputation", action="store_true",
                   help="Skip recomputing each record's class from the policy "
                        "that built it, which is what makes the class more "
                        "than a claim; for a fixture that has no clone")
    p.set_defaults(func=command_ingest)

    p = sub.add_parser(
        "dominance",
        help="Prove a class no gate reads cannot hide a failure (D-134)")
    p.add_argument("--repo", default=".")
    p.add_argument("--calibration")
    p.add_argument("--summary", default="metrics/shadow/summary.json",
                   help="The summary naming the class and its gates")
    p.add_argument("--class-key", required=True,
                   help="The class to probe; a unique prefix is enough")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--allow-exec", action="store_true",
                   help="Run the gates. Without it every gate reads not-run "
                        "and no probe can conclude anything, which is the "
                        "dry run.")
    p.set_defaults(func=command_dominance)

    p = sub.add_parser("summary", help="Regenerate the campaign summary")
    p.add_argument("--ledger", default="metrics/shadow/ledger")
    p.add_argument("--pull-requests",
                   help="JSON map from pull request number to author and "
                        "merged_at, which the criterion's authors and span need")
    p.add_argument("--out", default="metrics/shadow/summary.json")
    p.set_defaults(func=command_summary)
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

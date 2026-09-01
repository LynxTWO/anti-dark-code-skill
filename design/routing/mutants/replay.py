#!/usr/bin/env python3
"""Replay the router mutation matrix.

The previous matrix stored a name, a verdict, and a pytest line. That is a
claim, not a record: reproducing it meant guessing the transformation from the
name, which is what a reviewer had to do and what made the claim unverifiable.

Each row here carries the exact source path, the text replaced, and the
replacement. This script applies one row at a time against a restored source,
runs the router suite, and reports whether the mutant was caught.

Usage, from the repository root:

    python design/routing/mutants/replay.py            # replay every row
    python design/routing/mutants/replay.py M07 M33    # replay named rows
    python design/routing/mutants/replay.py --write    # replay and rewrite verdicts

A mutant is caught when the suite fails. A mutant that survives is a finding:
it names a guarantee the code claims and the tests do not hold it to.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

MATRIX = Path(__file__).with_name("matrix.json")


def host_identity() -> dict:
    """Facts that change what a replay can observe.

    A mutant attacking symlink handling survives on a host that cannot create
    symlinks, because the test skips. That is a fact about the host, not about
    the code, and one unqualified verdict cannot carry both it and the answer
    from a host that can. Every result records where it came from.
    """
    try:
        git = subprocess.run(["git", "--version"], capture_output=True,
                             text=True).stdout.strip()
    except OSError:
        git = "unknown"
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "git": git,
    }
REPO_ROOT = Path(__file__).resolve().parents[3]
# The router file by default. A row may name its own suite, because a mutant
# in one module proves nothing when the tests that hold it are never run, and
# replaying every module for every row costs minutes per mutant to learn that.
DEFAULT_SUITE = ("anti-dark-code/tests/test_route.py",)


# The matrix integrity tests compare the tree against the matrix, and during a
# replay the tree is deliberately wrong. They are deselected rather than
# skipped: a skip counts toward the per-host skip total, and that total decides
# whether an uncaught row reads as SURVIVED or as "nobody could check this". A
# guard that always skips would have quietly relabelled every real survivor.
INTEGRITY_FILTER = "not MutationMatrixIntegrity"
PYTEST_OUTCOME = (
    r"\d+ (?:failed|passed|skipped|deselected|xfailed|xpassed|warnings?|"
    r"errors?|subtests passed)"
)
PYTEST_SUMMARY = re.compile(
    rf"^{PYTEST_OUTCOME}(?:, {PYTEST_OUTCOME})* in \d+(?:\.\d+)?s"
    r"(?: \(\d+:(?:[0-5]\d):(?:[0-5]\d)\))?$")


def suite_command(paths) -> list[str]:
    return [sys.executable, "-m", "pytest", *paths, "-q", "-k", INTEGRITY_FILTER]


class SuiteBroken(RuntimeError):
    """The suite did not run, so the mutant proved nothing either way."""


def sha256_bytes(contents: bytes) -> str:
    """Return the exact byte digest used to prove mutation restoration."""
    return hashlib.sha256(contents).hexdigest()


def commit_identity(repo_root: Path) -> str:
    """Record the committed source that a row exercised."""
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True,
            text=True, check=False)
    except OSError:
        return "unknown"
    return done.stdout.strip() if done.returncode == 0 else "unknown"


def _summary_is_anchored(summary: str) -> bool:
    return PYTEST_SUMMARY.fullmatch(summary) is not None


def run_suite(paths=DEFAULT_SUITE, repo_root: Path = REPO_ROOT) -> tuple[int, str, int]:
    """Return the pytest exit, exact summary line, and skipped count.

    A mutant is caught when tests fail. It is not caught when they pass. A
    suite that could not collect, crashed, or was interrupted says nothing
    about the mutant, and treating that as either verdict would put a false
    row in the record. Those raise instead.
    """
    done = subprocess.run(suite_command(paths), cwd=repo_root,
                          capture_output=True, text=True)
    tail = (done.stdout or done.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    if not _summary_is_anchored(summary):
        raise SuiteBroken(
            f"pytest produced no test summary (exit {done.returncode}): {summary}")
    # pytest exit codes are exact, and text is not. A collection error, an
    # internal error, or no tests collected all print something that reads like
    # a result, and an earlier version of this check read a syntax error as a
    # caught mutant. 1 means tests failed, 0 means they passed, everything else
    # means the suite did not answer the question.
    # A skip means the host could not exercise the guarantee, which is a fact
    # about the host and not about the mutant.
    skipped = 0
    parts = summary.split()
    for index, token in enumerate(parts):
        if token.startswith("skipped") and index:
            try:
                skipped = int(parts[index - 1])
            except ValueError:
                skipped = 0
    if done.returncode not in (0, 1):
        raise SuiteBroken(f"pytest exit {done.returncode}: {summary}")
    return done.returncode, summary, skipped


def _row_evidence(row: dict, host: dict, worker: str, commit: str,
                  started: float, before: str | None = None) -> dict:
    """Start a JSON-compatible result before a row can mutate a source."""
    return {
        "id": row["id"], "status": "inconclusive", "verdict": "INCONCLUSIVE",
        "caught": None, "pytest": None, "skipped": 0,
        "source_hash_before": before, "source_hash_after": before,
        "source_after_state": "unknown",
        "restored": False, "commit": commit, "worker": worker,
        "host": host, "duration": 0.0,
    }


def run_row(repo_root: Path, row: dict, host: dict, worker: str) -> dict:
    """Run exactly one row, restoring its raw source bytes before returning."""
    started = time.perf_counter()
    commit = commit_identity(repo_root)
    source = repo_root / row["source"]
    original = source.read_bytes()
    before = sha256_bytes(original)
    result = _row_evidence(row, host, worker, commit, started, before)
    old = row["old"].encode("utf-8")
    new = row["new"].encode("utf-8")
    target_count = original.count(old)
    if target_count != 1:
        result["status"] = "target-missing" if target_count == 0 else "target-ambiguous"
        result["error"] = f"target occurs {target_count} times"
        result["source_hash_after"] = before
        result["restored"] = True
        result["duration"] = time.perf_counter() - started
        return result

    try:
        source.write_bytes(original.replace(old, new, 1))
        try:
            exit_code, summary, skipped = run_suite(
                tuple(row.get("suite", DEFAULT_SUITE)), repo_root)
            result["pytest"] = summary
            result["skipped"] = skipped
            if not PYTEST_SUMMARY.fullmatch(summary):
                raise SuiteBroken(
                    f"pytest produced no test summary (exit {exit_code}): {summary}")
            if exit_code not in (0, 1):
                raise SuiteBroken(f"pytest exit {exit_code}: {summary}")
            result["status"] = "completed"
            result["caught"] = exit_code == 1
            result["verdict"] = "caught" if result["caught"] else "SURVIVED"
        except SuiteBroken as broken:
            result["error"] = str(broken)
    except BaseException:
        # KeyboardInterrupt and SystemExit derive from BaseException. The
        # finally block restores the source before this interruption escapes.
        raise
    finally:
        restore_error: OSError | None = None
        after_error: OSError | None = None
        try:
            source.write_bytes(original)
        except OSError as caught:
            restore_error = caught
        try:
            after = sha256_bytes(source.read_bytes())
            result["source_hash_after"] = after
            result["source_after_state"] = "readable"
        except OSError as caught:
            after = None
            after_error = caught
            result["source_hash_after"] = None
            result["source_after_state"] = "unreadable"
        result["restored"] = (
            restore_error is None and after_error is None and after == before)
        result["duration"] = time.perf_counter() - started
        if not result["restored"]:
            errors = [result["error"]] if "error" in result else []
            if restore_error is not None:
                errors.append(f"source restoration write failed: {restore_error}")
            if after_error is not None:
                errors.append(f"source unreadable after restoration: {after_error}")
            if after is not None and after != before:
                errors.append("source restoration hash mismatch")
            result.update({
                "status": "inconclusive", "verdict": "INCONCLUSIVE",
                "caught": None,
                "error": "; ".join(errors),
            })
    return result


def run_serial(rows: list[dict], repo_root: Path) -> list[dict]:
    """Execute rows in canonical matrix order on the one authoritative tree."""
    host = host_identity()
    commit = commit_identity(repo_root)
    results: list[dict] = []
    for row in rows:
        if row.get("superseded_by"):
            source = repo_root / row["source"]
            digest = sha256_bytes(source.read_bytes()) if source.is_file() else None
            result = _row_evidence(row, host, "serial", commit,
                                   time.perf_counter(), digest)
            result.update({
                "status": "superseded", "verdict": "superseded",
                "source_hash_after": digest, "restored": True,
            })
            results.append(result)
            continue
        results.append(run_row(repo_root, row, host, "serial"))
    return results


def derive_verdict(results) -> str:
    """What the recorded host results add up to.

    A function of the results and nothing else. The first version read the
    label off whichever host ran last, so identical evidence produced "caught"
    when Linux finished the run and "caught elsewhere" when Windows did. That
    made the coverage record describe the order someone happened to replay in.

    Caught anywhere is caught, because a guarantee held on one host is held.
    Caught everywhere and caught somewhere are still worth distinguishing: the
    second means a host could not check it, and that is a fact about the host
    the record should keep rather than average away.

    Every host skipping is not evidence of absence. It is evidence nobody
    looked, and calling it SURVIVED would put a gap in the record that no host
    has observed.
    """
    caught = [r for r in results if r["verdict"] == "caught"]
    if caught:
        return "caught" if len(caught) == len(results) else "caught elsewhere"
    if results and all(r.get("skipped") for r in results):
        return "unverified: every host skipped"
    return "SURVIVED"


def replay(rows: list[dict], write: bool, wanted_subset: bool = False,
           repo_root: Path | None = None, evidence: list[dict] | None = None) -> int:
    repo_root = REPO_ROOT if repo_root is None else repo_root
    survivors: list[str] = []
    host = host_identity()
    print(f"  host: {host['platform']} {host['release']}, "
          f"python {host['python']}, {host['git']}\n")
    row_results = run_serial(rows, repo_root)
    if evidence is not None:
        evidence.extend(row_results)
    for row, result in zip(rows, row_results, strict=True):
        if result["status"] == "superseded":
            # The behaviour this mutant attacked moved, so applying it is a
            # no-op and it would report as surviving. That reads like a gap and
            # is not one. Its replacement id is recorded on the row.
            print(f"  {row['id']}  {row['name']:42} superseded by "
                  f"{row['superseded_by']}")
            continue
        if result["status"] != "completed":
            print(f"  {row['id']}  {row['name']:42} {result['verdict']}: "
                  f"{result.get('error', 'no row evidence')}")
            survivors.append(row["id"])
            continue
        verdict = result["verdict"]
        results = {r["platform"]: r for r in row.get("results", [])}
        results[host["platform"]] = {**host, "verdict": verdict,
                                     "pytest": result["pytest"],
                                     "skipped": result["skipped"]}
        row["results"] = [results[k] for k in sorted(results)]
        # Caught anywhere is caught. A host that cannot exercise the guarantee
        # reports a skip, and a skip is not evidence of absence.
        row["verdict"] = derive_verdict(row["results"])
        row["pytest"] = result["pytest"]
        note = "" if verdict == row["verdict"] else (
            f"  (here: {verdict}{', ' + str(result['skipped']) + ' skipped' if result['skipped'] else ''})")
        print(f"  {row['id']}  {row['name']:42} {row['verdict']}{note}")
        if row["verdict"] == "SURVIVED":
            survivors.append(row["id"])
    print(f"\n  {len(rows)} mutants, {len(survivors)} not caught: "
          f"{survivors or 'none'}")
    if write:
        if wanted_subset:
            # Writing a filtered run drops every row it did not touch, so the
            # record shrinks each time someone replays one mutant. This is not
            # hypothetical: it truncated the matrix from 43 rows to 1 while
            # this guard was being written, and git had to restore it.
            print("  --write refused for a filtered run: it would truncate the "
                  "matrix to the rows just replayed")
            return 2
        MATRIX.write_text(json.dumps(rows, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    return 1 if survivors else 0


def matrix_sha256() -> str:
    return sha256_bytes(MATRIX.read_bytes())


def main(argv: list[str]) -> int:
    write = False
    report: Path | None = None
    wanted: list[str] = []
    jobs = 1
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--write":
            write = True
        elif arg == "--report":
            index += 1
            if index == len(argv):
                print("--report requires a path")
                return 2
            report = Path(argv[index])
        elif arg == "--jobs":
            index += 1
            if index == len(argv):
                print("--jobs requires a count")
                return 2
            try:
                jobs = int(argv[index])
            except ValueError:
                print("--jobs must be an integer")
                return 2
            if jobs != 1:
                print("only --jobs 1 is supported by serial replay")
                return 2
        elif arg.startswith("--"):
            print(f"unknown option: {arg}")
            return 2
        else:
            wanted.append(arg)
        index += 1
    rows = json.loads(MATRIX.read_text(encoding="utf-8"))
    missing = [m for m in wanted if m not in {r["id"] for r in rows}]
    if missing:
        print(f"unknown mutant ids: {missing}")
        return 2
    if wanted:
        rows = [r for r in rows if r["id"] in wanted]
    before = matrix_sha256()
    evidence: list[dict] = []
    outcome = replay(rows, write, wanted_subset=bool(wanted), repo_root=REPO_ROOT,
                     evidence=evidence)
    after = matrix_sha256()
    if report is not None:
        report.write_text(json.dumps({
            "commit": commit_identity(REPO_ROOT),
            "matrix_sha256_before": before,
            "matrix_sha256_after": after,
            "rows": evidence,
            "cleanup": [],
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return outcome


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

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

import json
import os
import platform
import subprocess
import sys
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


def suite_command(paths) -> list[str]:
    return ["python", "-m", "pytest", *paths, "-q"]


class SuiteBroken(RuntimeError):
    """The suite did not run, so the mutant proved nothing either way."""


def run_suite(paths=DEFAULT_SUITE) -> tuple[bool, str, int]:
    """Return whether the mutant was caught, plus the summary line.

    A mutant is caught when tests fail. It is not caught when they pass. A
    suite that could not collect, crashed, or was interrupted says nothing
    about the mutant, and treating that as either verdict would put a false
    row in the record. Those raise instead.
    """
    # The matrix integrity check compares the tree against the matrix, and
    # during a replay the tree is deliberately wrong. Without this flag that
    # check would fail for whichever row is applied, and every mutant would
    # report caught without any behavioural test having noticed.
    environment = dict(os.environ)
    environment["ADC_MUTATION_REPLAY"] = "1"
    done = subprocess.run(suite_command(paths), cwd=REPO_ROOT,
                          capture_output=True, text=True, env=environment)
    tail = (done.stdout or done.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
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
    if done.returncode == 1:
        return True, summary, skipped
    if done.returncode == 0:
        return False, summary, skipped
    raise SuiteBroken(f"pytest exit {done.returncode}: {summary}")


def replay(rows: list[dict], write: bool, wanted_subset: bool = False) -> int:
    survivors: list[str] = []
    host = host_identity()
    print(f"  host: {host['platform']} {host['release']}, "
          f"python {host['python']}, {host['git']}\n")
    for row in rows:
        if row.get("superseded_by"):
            # The behaviour this mutant attacked moved, so applying it is a
            # no-op and it would report as surviving. That reads like a gap and
            # is not one. Its replacement id is recorded on the row.
            print(f"  {row['id']}  {row['name']:42} superseded by "
                  f"{row['superseded_by']}")
            continue
        source = REPO_ROOT / row["source"]
        original = source.read_text(encoding="utf-8")
        if row["old"] not in original:
            print(f"  {row['id']}  {row['name']:42} TARGET MISSING")
            survivors.append(row["id"])
            continue
        source.write_text(
            original.replace(row["old"], row["new"], 1), encoding="utf-8", newline="")
        try:
            caught, summary, skipped = run_suite(
                tuple(row.get("suite", DEFAULT_SUITE)))
        except SuiteBroken as broken:
            row["verdict"] = "INCONCLUSIVE"
            row["pytest"] = str(broken)
            print(f"  {row['id']}  {row['name']:42} INCONCLUSIVE: {broken}")
            survivors.append(row["id"])
            continue
        except BaseException:
            # KeyboardInterrupt and SystemExit derive from BaseException, so a
            # bare except or a try/finally alone is not enough to guarantee the
            # source comes back. Restore, then re-raise.
            source.write_text(original, encoding="utf-8", newline="")
            print(f"\n  interrupted during {row['id']}; source restored")
            raise
        finally:
            source.write_text(original, encoding="utf-8", newline="")
        verdict = "caught" if caught else "SURVIVED"
        results = {r["platform"]: r for r in row.get("results", [])}
        results[host["platform"]] = {**host, "verdict": verdict,
                                     "pytest": summary, "skipped": skipped}
        row["results"] = [results[k] for k in sorted(results)]
        # Caught anywhere is caught. A host that cannot exercise the guarantee
        # reports a skip, and a skip is not evidence of absence.
        anywhere = [r for r in row["results"] if r["verdict"] == "caught"]
        if anywhere:
            row["verdict"] = "caught" if verdict == "caught" else "caught elsewhere"
        elif all(r.get("skipped") for r in row["results"]):
            # Every host that ran this skipped a test. That is not evidence the
            # guarantee is unheld, it is evidence nobody could check it here.
            # Calling it SURVIVED would put a gap in the record that no host
            # has actually observed.
            row["verdict"] = "unverified: every host skipped"
        else:
            row["verdict"] = "SURVIVED"
        row["pytest"] = summary
        note = "" if verdict == row["verdict"] else (
            f"  (here: {verdict}{', ' + str(skipped) + ' skipped' if skipped else ''})")
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


def main(argv: list[str]) -> int:
    write = "--write" in argv
    wanted = [a for a in argv if not a.startswith("--")]
    rows = json.loads(MATRIX.read_text(encoding="utf-8"))
    missing = [m for m in wanted if m not in {r["id"] for r in rows}]
    if missing:
        print(f"unknown mutant ids: {missing}")
        return 2
    if wanted:
        rows = [r for r in rows if r["id"] in wanted]
    return replay(rows, write, wanted_subset=bool(wanted))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

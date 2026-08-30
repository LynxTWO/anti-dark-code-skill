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
import subprocess
import sys
from pathlib import Path

MATRIX = Path(__file__).with_name("matrix.json")
REPO_ROOT = Path(__file__).resolve().parents[3]
SUITE = ["python", "-m", "pytest", "anti-dark-code/tests/test_route.py", "-q"]


def run_suite() -> tuple[bool, str]:
    done = subprocess.run(SUITE, cwd=REPO_ROOT, capture_output=True, text=True)
    tail = (done.stdout or done.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    return ("failed" in summary), summary


def replay(rows: list[dict], write: bool) -> int:
    survivors: list[str] = []
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
            caught, summary = run_suite()
        finally:
            source.write_text(original, encoding="utf-8", newline="")
        row["verdict"] = "caught" if caught else "SURVIVED"
        row["pytest"] = summary
        print(f"  {row['id']}  {row['name']:42} {row['verdict']}")
        if not caught:
            survivors.append(row["id"])
    if write:
        MATRIX.write_text(json.dumps(rows, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    print(f"\n  {len(rows)} mutants, {len(survivors)} not caught: "
          f"{survivors or 'none'}")
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
    return replay(rows, write)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

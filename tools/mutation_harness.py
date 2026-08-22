#!/usr/bin/env python3
"""Standard-library mutation harness for this repository's own tooling.

A green suite proves the tests ran, not that they would notice a defect. This
harness answers the other question: change one decision in the code, and does
anything go red? Survivors are the finding.

Design constraints, each earned:

- Mutants never touch the working tree. Every run copies the repository into a
  scratch directory first, because a harness that mutates in place can corrupt a
  concurrent reader, and one already did during a review of this project.
- Every mutant is bounded by a timeout, and a hang is reported as its own
  outcome rather than folded into pass or fail. A mutation that hangs is a defect
  in the code under test, and it blocks every later proof.
- Absolute counts are reported beside the score. A perfect score over four
  mutants is narrow evidence.
- Mutant order is deterministic, so two runs of one target agree.

A surviving mutant is not automatically a missing test. It is either a missing
test or an equivalent mutant, and the two demand different responses: write the
test, or delete the code that was not load bearing and name the mechanism that
really owns the behavior. Record which one before changing a threshold.

No third-party dependencies. Python 3.9 or later (needs ast.unparse).
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Mutant:
    """One changed decision, identified well enough to reproduce by hand."""

    target: str
    function: str
    line: int
    operator: str
    before: str
    after: str
    source: str = field(repr=False)

    @property
    def label(self) -> str:
        return f"{self.target}:{self.line} {self.function} [{self.operator}] {self.before} -> {self.after}"


COMPARE_SWAPS = {
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}
BOOL_SWAPS = {ast.And: ast.Or, ast.Or: ast.And}
ARITH_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add}


def enclosing_function(tree: ast.AST, node: ast.AST) -> str:
    """Name the function a node sits in, so a survivor points somewhere specific."""
    best = "<module>"
    best_line = -1
    for candidate in ast.walk(tree):
        if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = candidate.lineno
            end = getattr(candidate, "end_lineno", start)
            if start <= getattr(node, "lineno", -1) <= end and start > best_line:
                best, best_line = candidate.name, start
    return best


def generate_mutants(path: Path, functions: set[str] | None) -> list[Mutant]:
    original = path.read_text(encoding="utf-8")
    tree = ast.parse(original)
    mutants: list[Mutant] = []

    def emit(node: ast.AST, operator: str, before: str, after: str, apply) -> None:
        function = enclosing_function(tree, node)
        if functions and function not in functions:
            return
        fresh = ast.parse(original)
        target_node = None
        for candidate in ast.walk(fresh):
            if (
                type(candidate) is type(node)
                and getattr(candidate, "lineno", None) == getattr(node, "lineno", None)
                and getattr(candidate, "col_offset", None) == getattr(node, "col_offset", None)
            ):
                target_node = candidate
                break
        if target_node is None:
            return
        apply(target_node)
        ast.fix_missing_locations(fresh)
        mutants.append(
            Mutant(path.name, function, getattr(node, "lineno", 0), operator, before, after, ast.unparse(fresh))
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            op = type(node.ops[0])
            if op in COMPARE_SWAPS:
                replacement = COMPARE_SWAPS[op]
                emit(node, "compare", op.__name__, replacement.__name__,
                     lambda n, r=replacement: n.ops.__setitem__(0, r()))
        elif isinstance(node, ast.BoolOp):
            op = type(node.op)
            if op in BOOL_SWAPS:
                replacement = BOOL_SWAPS[op]
                emit(node, "boolean", op.__name__, replacement.__name__,
                     lambda n, r=replacement: setattr(n, "op", r()))
        elif isinstance(node, ast.BinOp):
            op = type(node.op)
            if op in ARITH_SWAPS:
                replacement = ARITH_SWAPS[op]
                emit(node, "arithmetic", op.__name__, replacement.__name__,
                     lambda n, r=replacement: setattr(n, "op", r()))
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            emit(node, "constant", str(node.value), str(not node.value),
                 lambda n: setattr(n, "value", not n.value))
        elif isinstance(node, ast.Return) and node.value is not None:
            # `return None` -> `return None` is a no-op that always survives.
            # Emitting it manufactures a false finding, and a harness that cries
            # wolf teaches its reader to skim the survivor list.
            if isinstance(node.value, ast.Constant) and node.value.value is None:
                continue
            emit(node, "return", "value", "None", lambda n: setattr(n, "value", ast.Constant(value=None)))

    # Deterministic order so two runs of one target agree.
    mutants.sort(key=lambda m: (m.line, m.operator, m.before, m.after))
    return mutants


def run_suite(workdir: Path, tests: list[str], timeout: int) -> tuple[str, str]:
    command = [sys.executable, "-m", "unittest", "-q", *tests] if tests else [sys.executable, "-m", "unittest", "discover", "-q"]
    try:
        proc = subprocess.run(
            command,
            cwd=str(workdir / "anti-dark-code" / "tests"),
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout", ""
    return ("passed" if proc.returncode == 0 else "failed"), (proc.stderr or "")[-400:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mutate one module and report which mutants survive the tests.")
    parser.add_argument("--repo", default=".", help="Repository root to copy into a scratch tree")
    parser.add_argument("--target", default="anti-dark-code/scripts/adc.py", help="Module to mutate, repo-relative")
    parser.add_argument("--function", action="append", default=[], help="Limit to these function names; repeatable")
    parser.add_argument("--test", action="append", default=[], help="unittest target to run; repeatable")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds allowed per mutant")
    parser.add_argument("--limit", type=int, help="Stop after this many mutants")
    parser.add_argument("--json", help="Write the full report here")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    target_rel = Path(args.target)
    functions = set(args.function) or None

    mutants = generate_mutants(repo / target_rel, functions)
    if args.limit:
        mutants = mutants[: args.limit]
    if not mutants:
        print("No mutants generated. Check --target and --function.")
        return 2

    with tempfile.TemporaryDirectory(prefix="adc-mutation-") as tmp:
        workdir = Path(tmp) / "repo"
        shutil.copytree(repo, workdir, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        target_path = workdir / target_rel
        pristine = target_path.read_text(encoding="utf-8")

        started = time.monotonic()
        baseline, detail = run_suite(workdir, args.test, args.timeout)
        if baseline != "passed":
            # Without a green control, every later verdict is meaningless.
            print(f"BASELINE {baseline.upper()}: the unmutated suite must pass before mutation means anything.")
            print(detail)
            return 2
        print(f"baseline: passed ({time.monotonic() - started:.1f}s) | mutants: {len(mutants)}")

        results = []
        killed = survived = timed_out = 0
        for index, mutant in enumerate(mutants, start=1):
            target_path.write_text(mutant.source, encoding="utf-8")
            outcome, _ = run_suite(workdir, args.test, args.timeout)
            target_path.write_text(pristine, encoding="utf-8")

            if outcome == "failed":
                killed += 1
                mark = "killed"
            elif outcome == "timeout":
                timed_out += 1
                mark = "TIMEOUT"
            else:
                survived += 1
                mark = "SURVIVED"
            results.append({"label": mutant.label, "outcome": mark, "function": mutant.function, "line": mutant.line})
            print(f"  [{index}/{len(mutants)}] {mark:9s} {mutant.label}")

    total = len(mutants)
    score = (killed / total * 100) if total else 0.0
    print(f"\nkilled {killed}/{total} ({score:.0f}%)  survived {survived}  timeout {timed_out}")
    if survived or timed_out:
        print("\nSurvivors and hangs are findings. Classify each as a missing test or an equivalent mutant:")
        for item in results:
            if item["outcome"] != "killed":
                print(f"  {item['outcome']:9s} {item['label']}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {"target": str(target_rel), "functions": sorted(functions) if functions else None,
                 "killed": killed, "survived": survived, "timeout": timed_out, "total": total,
                 "results": results},
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    return 0 if not (survived or timed_out) else 1


if __name__ == "__main__":
    raise SystemExit(main())

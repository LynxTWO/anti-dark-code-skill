# Round Sixteen Verification and Parallel Harness Design

Date: 2026-08-31
Base: `bf9aba3f5b98fe9bea5f7fa035bac2b4fd8c1065` on `origin/claude/round-fifteen-verify`
Working branch: `codex/round-sixteen-verify`

## Goal

Independently verify round fifteen, restore the full two-host T540P mutation record, and determine from exact evidence whether disposable-clone process parallelism can replace the serial replay path. The round must preserve routing and evidence authority. It must not approve a routing rule, enable selective execution, mark SLICE-001 Done, or adopt parallel execution on timing alone.

## Baseline and order of work

Work starts from a clean, isolated worktree at the exact base above. Before implementation, the universal validator and full suite establish the pristine baseline. The work then proceeds in this order:

1. Attack D-085 through D-089 and run every walkthrough command literally.
2. Replay the complete 95-row matrix serially on T540P under D-068, then restore the missing Linux per-row entries.
3. Build the disposable-clone process path with tests, run the complete serial and parallel comparison, and evaluate suite stability with repeated serial and xdist trials.
4. Change CI only if local identity and stability evidence support adoption.
5. Re-run all final gates, write the round-sixteen handoff, push, open a PR, and wait for CI on the Codex head.

## Independent adversarial verification

The verification work uses disposable repositories so a successful exploit cannot contaminate the working tree.

For D-085 and D-088, a generated driver-name corpus will cover ordinary names, names containing `=`, leading `=`, punctuation, Unicode, whitespace, config-sensitive spellings, and names that make individual Git queries fail. Each candidate will be configured with an execution marker. The acquisition path must either neutralize the program and finish safely or fail closed without executing it. Git query failure must never be interpreted as proof that no live program exists.

For D-086 and D-089, the attack will deliberately satisfy the self-grading guard while trying to route authority-bearing files cheaply. The starting exploit narrows authority coverage to the exact preflight path while assigning broader reference paths to documentation or prose. The attack must cover every routing-owning pass reference named by R-021 and ENGINEERING, not only the paths already listed in `SELF_GRADING_PATHS`. A reproduced bypass becomes a failing regression before the guard is changed.

For D-087, tests will independently verify both properties of mutation targeting: every active row changes exactly the intended occurrence, and no row is effectively ambiguous after replacement even when its literal target occurs once. Superseded-row exemptions will be checked against their actual status and replacement behavior.

The walkthrough is executable evidence, not explanatory prose. Every command will be copied and run as written from the documented directory and branch. Output, exit status, totals, cited decisions, and expected state transitions will be compared literally. A malformed command or unsupported expectation is a defect even if the intended command is obvious.

Each decision receives one of `upheld`, `amended`, or `broken`, together with the reproducer, regression test, and measured result that justify the verdict.

## T540P replay

The canonical two-host restoration run is the existing serial replay on T540P Linux. It runs the full 95-row matrix under D-068 before parallel replay results are considered. Every mutable source is hashed before and after the run; each row accepts only process exit 0 or 1 with an anchored pytest summary. The eight rows missing Linux bookkeeping receive explicit per-row results only from this run. Any T540P result that contradicts the PR #25 Linux CI fact stops later work until explained.

## Parallel replay architecture

The parallel implementation extends the existing replay command with an explicit worker count while preserving serial mode as the reference path. It uses a standard-library process executor, not threads.

The coordinator performs these steps:

1. Resolve and record the exact source commit and matrix digest.
2. Create a contained temporary root and one disposable clone per worker from that exact commit.
3. Partition active rows deterministically while retaining canonical matrix order for reporting.
4. Send each row to the worker that owns its clone.
5. Aggregate structured row results, validate cleanup and restoration facts, and write output only after all workers finish.

Each worker owns exactly one clone and processes its assigned rows sequentially. For every row it hashes the mutable source before mutation, verifies the target and replacement cardinality, writes the mutant, executes the required tests, parses an anchored pytest summary, accepts only exit 0 or 1, restores the original bytes, and verifies the restoration hash before accepting the result. A clone that cannot prove restoration is retired and cannot process another row.

Workers return structured data only: row id, status, caught or survived verdict, pytest counts, command exit, source hash before and after, commit id, duration, and cleanup-relevant clone identity. They do not edit the matrix, handoff, or evidence files. The coordinator is the only writer.

Temporary paths are generated beneath the owned root, resolved before deletion, and checked for containment. Cleanup is attempted for every clone, including failure paths, and its success or failure is recorded. Failure output is retained in the aggregate result without retaining an unbounded checkout. No cleanup command may target the workspace root, a home directory, or an unresolved path.

## Identity and stability evidence

Parallel replay can be adopted only after a complete 95-row serial run and a complete 95-row parallel run at the same commit and matrix digest. The comparison is keyed by row id and requires exact agreement on active or skipped state, caught or survived verdict, skip reason, pytest result counts, and restoration outcome. Missing, extra, duplicated, or reordered report rows are errors. Timing is recorded but is not part of identity.

Suite stability uses at least three ordinary pytest runs and at least three pytest-xdist runs. Each run emits JUnit XML outside the repository. A normalizer records the exact node-id sets for passed, skipped, and failed tests. Sets must be stable within each mode and equal across modes. Totals alone are insufficient. Any mismatch is investigated as a test-isolation finding and blocks adoption until explained and corrected.

The durable evidence artifact will be `design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json`. It contains normalized commands, commit and matrix digests, environment facts, per-run durations, row comparison results, exact test outcome sets or their deterministic digests with source JUnit paths identified by run label, restoration results, cleanup results, and the adoption decision. It must not contain user-specific absolute temporary paths.

## Tests and implementation sequence

Behavior changes follow test-driven development:

1. Add failing regressions for any reproduced D-085 through D-089 defect, beginning with the policy bypass and then driver-name neutralization cases.
2. Add focused replay tests for deterministic partitioning, worker-owned clone isolation, per-row restoration, structured result validation, anchored-summary enforcement, coordinator ordering, and failure cleanup.
3. Implement the smallest guard and replay changes that pass those tests.
4. Run focused tests, the universal validator, the full suite, matrix integrity checks, the canonical serial replay, and then the parallel replay.
5. Run repeated serial and xdist suite trials and compare exact outcome sets.

Adversarial fixes are committed separately from the parallel harness when they close distinct requirements. The parallel implementation, evidence, any justified CI change, and final handoff remain reviewable commit boundaries. Every commit carries the repository's required `EDD-Checklist: satisfied` trailer.

## CI decision

CI is last. If and only if the local evidence supports adoption, the workflows may install pytest-xdist for suite jobs and invoke the proven parallel options at conservative runner-sized worker counts. The mutation replay workflow may use the new clone pool only at a worker count supported by its local and CI resource limits. No job may select a reduced test or mutation subset.

If row identity, suite stability, cleanup, restoration, or CI evidence fails, parallel execution is declined or limited to the portion independently proved safe. The existing serial command remains available and authoritative.

## Alternatives considered

An external shell sharder was rejected because it would duplicate row partitioning, aggregation, restoration, and failure semantics outside the tested Python harness. Threading was rejected because replay mutates source files and Git state. Suite-only xdist was insufficient because the mutation replay is the dominant cost. A process pool over worker-owned clones keeps isolation and evidence enforcement inside one testable implementation while retaining serial mode as the oracle.

## Completion evidence

The round is complete only when the decision verdicts, literal walkthrough results, full two-host row record, serial-versus-parallel row diff, repeated suite set comparison, final validator and suite results, pushed commit ids, PR URL, and CI results are recorded in `design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md`. The handoff must name every remaining blocker to SLICE-001 Done, including the owner's final approval gate.

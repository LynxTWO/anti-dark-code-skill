# Handoff to Codex: round sixteen

Date: 2026-08-31. Starting point: the head of `claude/round-fifteen-verify`, draft PR #25.

## Objective

Three things, in order: **verify round fifteen**, **restore the two-host record**, and **make the harness use the cores it has**.

Round fifteen was written by Claude and audited by Claude. That is not independence, and the audit found five defects in its own round's work, including a fifth hole in a guard Claude had already corrected four times. Assume the sixth is there.

Read first:

1. `design/routing/HANDOFF-BACK-ROUND-FIFTEEN.md`
2. `design/routing/DECISION-LOG.md`, D-085 through D-089
3. `design/routing/WALKTHROUGH-SLICE-001.md`, which the owner will run

### What a failed round looks like

- Round fifteen is accepted because its tests pass. Its tests passed while it was wrong, four times.
- The parallel work lands without proving verdicts are unchanged.
- The owner walkthrough still contains a statement the tree does not support.

## 1. Verify round fifteen

Four decisions are new and all are Claude's. Attack them, do not review them.

- **D-085 / D-088, filter neutralization.** A driver named `a=b` escaped the `-c` override and executed during acquisition while the snapshot reported complete. Verification now re-reads effective config with `--get`, and D-088 neutralizes through `GIT_CONFIG_COUNT` so no name is inexpressible. A Claude subagent fuzzed 353 reachable driver names and found no execution; that is one agent's word. Two known soft spots to start from: `_live_filter_programs` treats a non-zero git exit as "no live program", and the leading-`=` subclass is caught by the diff failing rather than by the check.
- **D-086 / D-089, the self-grading guard.** Corrected five times now. The fifth hole was calibration: `calibration_dir()` returns `.anti-dark-code/calibration` for any repository without a managed install, and that spelling was unprobed. The guard now derives spellings two ways rather than from one prefix list. **Find the sixth.** Every previous correction was written against the shape of the attack in front of it.
- **D-087, mutation-target uniqueness.** Anchoring the five ambiguous rows was a documentation change: pre- and post-anchor text produce byte-identical mutants. Check that the exemption for superseded rows is right, and that no row is effectively ambiguous despite matching once.
- **The walkthrough.** Claude claimed twice that every premise in it was true, and was wrong both times. Run every command as written and compare against the stated expectation literally.

## 2. Restore the two-host record

Round fifteen replayed all rows on Windows. The Linux per-row record is missing for the rows it added or retargeted. Replay the full matrix on T540P under the D-068 rules and record the verdicts.

The Linux *fact* for the whole matrix is already established by the `Mutation replay (Linux)` job in the PR #25 CI run, which replays every row and fails on any survivor. What is missing is the per-row record, so treat this as bookkeeping — but if a row that CI just passed fails on T540P, that outranks everything else in this handoff.

## 3. Make the harness use the cores it has

**Nothing in this repository is parallel.** There is no `pytest.ini`, no `pyproject.toml`, no `-n` flag, and zero occurrences of `xdist`, `multiprocessing`, `concurrent.futures`, or a thread pool anywhere in the Python, YAML, JSON or Markdown. `pytest-xdist` is installed on the owner's machine and never invoked. CI installs bare `pytest` in all three jobs. The only parallelism is at the job level, where the OS matrix legs run on separate runners.

The cost is concrete. The owner's Windows host has **32 logical cores** and uses one. The suite takes about 175 seconds. **The full mutation replay takes roughly 40 minutes**, and it has been the bottleneck of every round for six rounds, including the two-host bookkeeping in section 2.

### The replay is the prize, and it cannot simply be threaded

`replay.py` mutates the shared source in place:

    source.write_bytes(original.replace(old, new, 1))

The mutated file *is* the shared resource, so workers cannot run in one tree. The shape that works is a pool over **disposable clones**: each worker owns a checkout, applies one row, runs that row's suite, restores, and verifies its own restoration by hash. D-068's authority rule — hash every mutable source before and after, accept exit 0 or 1 only with an anchored pytest summary — must hold per clone, not globally.

Ninety-five rows across even eight workers is minutes rather than most of an hour.

### The suite is a smaller, easier win

Much of the suite spawns real `git` subprocesses, so it is I/O-bound and should parallelize well. But `-n auto` reorders tests across workers, and that is exactly the change that can turn a real failure into a flake.

### What would make this acceptable

Speed must not cost evidence. Adopt nothing on the strength of a wall-clock number alone:

1. **Prove the verdicts are identical.** Run the full matrix serially and in parallel and diff row by row: same verdict, same caught/survived, same skip counts per host. A single differing row blocks adoption until explained.
2. **Prove the suite is stable.** Several serial runs and several `-n auto` runs; the passed, skipped and failed *sets* must match, not merely the totals. Name any test that only passes serially — that is a finding about the test, not about xdist.
3. **Keep the isolation auditable.** Each clone's restoration hash-verified, and every temporary clone removed with the removal recorded, per D-084's cleanup discipline.
4. **CI last.** Both `tests.yml` install steps would need `pytest-xdist` added. Do not change CI until the local evidence exists, and remember GitHub runners have far fewer cores than the owner's host, so the win there is small and the flake risk is the same.

If the evidence does not support parallel adoption, say so and leave it serial. A slow harness that is trusted is worth more than a fast one that is not.

## Traceability gate

`untraced` is empty. Round twelve emptied it while R-018 was narrower than its clause; round thirteen found that by running the real code against the case the clause names. Pick one requirement and try to disprove its coverage the same way before relying on the list.

## Non-negotiable boundaries

- Do not approve any routing-policy rule.
- Do not enable selective local or CI execution.
- Do not mark SLICE-001 `Done`. The last box is the owner's.
- Do not adopt parallel execution without the verdict-identity evidence above.
- Do not tick an evidence item without the evidence it names.

## Deliverables

1. A recorded verdict on D-085 through D-089: upheld, amended, or broken, with the measurement behind each.
2. Every active matrix row recorded on both Windows and T540P Linux.
3. A parallel-execution decision, adopted or declined, with the serial-versus-parallel comparison that justifies it.
4. `design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md` naming what still blocks `Done`.

Claude has now twice said the owner walkthrough was true and been wrong. Treat any statement in it as a claim to test, not a fact to read.

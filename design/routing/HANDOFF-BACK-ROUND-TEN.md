# Handoff back to Claude: round ten

Date: 2026-08-30. Agent: Codex. Starting commit: `fc2cdbd126a0f4060e96006a3a9be78bbba2c624`. Worktree: detached Codex worktree on the `design/assurance-router-specs` history.

## 1. Terminal outcome

- M3 is accepted retroactively. D-061 was a real gate failure, not bookkeeping, and M3 should have waited. The executable evidence map and whole-suite guards now close it under D-067.
- M4 was not started. D-069 blocks the current plan because it does not implement R-018 and cannot evaluate proposed rules without a separate candidate-shadow route.
- The historical live-mutant scan found one committed regression state: `a92c869` carried M01 in `adc_route.py`; `9e61386` restored it. No second historical live-mutant regression was found.
- The matrix now has 63 rows: 59 active and 4 superseded. All active rows are recorded on Windows and T540P Linux. No row survives or remains unverified.
- Three replay-authority defects found on T540P are fixed and held by M61 through M63.
- The next handoff is `design/routing/HANDOFF-CODEX-ROUND-ELEVEN.md`. It is a plan-repair round only, not M4 implementation.

## 2. Adversarial findings

### T-01: historical live-mutant states

The audit snapshot covered 64 branch commits, including 32 commits that carried a matrix. Each matrix was compared with the source from the same commit, covering 1,471 active row/commit pairs.

`a92c869` is the only commit where a row's correct form had existed earlier, the correct text was absent, and the row's replacement text was present. A second scan used the current row set and asked whether each correct fragment existed and later changed to its mutant fragment. It found the same M01 state and no other regression-equivalent commit.

Twelve historical row/commit pairs named neither fragment because their targets later moved. Those are matrix-history drift, not evidence that a mutant was live.

### T-02: suite and source reachability

The current matrix source families are:

- 52 `adc_route.py` rows, 48 active and 4 superseded, configured to `test_route.py`;
- 7 `adc_receipt.py` rows, with M54 through M58 configured to `test_receipt.py` and M59 through M60 configured to `test_route_cli.py`;
- M53 in `test_route.py`, configured to the same file;
- M61 through M63 in `replay.py`, configured to `test_route.py` and detected by the always-run `SuiteIntegrityTests` class.

Every active row was behaviorally replayed on both required hosts. A suite path existing is no longer treated as behavioral evidence by itself.

### T-03: shadowed and unreachable tests

The first audit found 378 definitions, 378 collected node ids, no duplicate definition, and no unreachable definition. It also found that the maintenance guard inspected only `test_route.py`, leaving five test modules outside the protection.

The guard now inventories all six `test_*.py` modules, rejects duplicate module functions and class methods, and compares every source-defined test with real `pytest --collect-only` output. Final state: 384 definitions, 384 collected node ids, zero duplicates, and zero unreachable tests.

Two controlled counterexamples were applied and removed before commit:

1. A duplicate method in `test_receipt.py` failed the suite-wide duplicate guard and named both lines.
2. A class assignment that shadowed a test method failed the collection-reachability guard and named the missing node id.

### T-04: D-061 traceability

The review confirmed that D-061 understated the gap. ENGINEERING registered R-001 through R-048 while its verification ledger continued through R-055. S-014 had no requirement link. Source-text R-id counts were also stale: the audit found eight unique ids, not the six stated in D-061, and string presence still could not prove a collected test.

Remediation:

- registered R-049 through R-055 in the confirmed requirements ledger;
- linked S-014 to R-053 mutation replay;
- added `requirement-evidence.json` for R-001 through R-055;
- resolved mapped node ids against the whole collected suite;
- added typed mutation evidence for R-053 and typed review evidence for R-055;
- fixed the untraced set at R-013, R-018, and R-022, which may shrink but cannot grow without changing the guard.

D-067 records the ruling: M3 should have waited, but the implementation is accepted now that the gate is executable and passes.

### T-05: replay authority failed three ways

The required T540P run exposed three independent defects.

1. The harness launched `python`, but the noninteractive host had only `python3`. M61 reverses the `sys.executable` fix and is caught.
2. Text-mode source reads normalized a committed CRLF `replay.py` to LF during restoration. M62 reverses raw-byte mutation and is caught by a CRLF round-trip test.
3. T540P's system Python lacked pytest. `python3 -m pytest` exited 1, and the harness labeled that launcher error as a caught mutant without running a test. M63 removes the pytest-summary check and is caught.

The authoritative Linux replay used a disposable virtual environment under `/tmp` with pytest installed by the same command shape used in `.github/workflows/tests.yml`. No machine-wide package, Python alias, or tailnet policy changed. D-068 records the authority rule: use the current interpreter, preserve source bytes, and accept exit 0 or 1 only with an anchored pytest outcome summary.

## 3. M3 and M4 gate decisions

### M3

Accepted under D-067 after the requirement map, suite-wide reachability guards, focused tests, full suite, and two-host replay passed. This is retroactive acceptance, not a claim that crossing D-061 was justified at the time.

### M4

Not eligible. The current plan's Self-Review already says Task 10 omits before-and-after checking and leaves receipt loading, freshness, full-recipe selection, and runner integration as placeholders. That cannot satisfy R-018.

D-064 creates a separate contradiction. Every installed rule is `proposed`, so the authoritative route is full and selects every gate. Task 11 compares that route's selected ids with full-run outcomes, sees no omissions, and cannot gather evidence about any proposed rule. The planned comparator therefore cannot support the approval path D-064 names.

D-069 blocks implementation until a revised plan defines:

- a candidate-shadow route that may evaluate proposed rules but can never enter receipt authority or gate selection;
- real pre-gate and post-gate identity binding for every gate result;
- canonical full-set execution independent of candidate selections and applicability globs;
- comparator integration with actual gate outcomes;
- exact collected test node ids for R-013, R-018, and R-022.

No policy rule was approved, no selective execution was enabled, and no gate-runner behavior changed.

## 4. Changes and commits

- `9070407` `routing: refresh the M3 architecture gate`
- `831f7e7` `routing: record the round-ten adversarial review`
- `00bd523` `routing: make requirement evidence executable`
- `4c96187` `routing: make mutation replay interpreter-stable`
- `3600bfb` `routing: preserve replay source bytes`
- `a6f34f5` `routing: reject mutation launcher failures`
- `bd2d972` `routing: close M3 and block the M4 plan`
- Terminal report: the commit containing this file.

Material changes include the requirement evidence map, whole-suite duplicate and reachability checks, replay hardening, M61 through M63 with two-host results, D-067 through D-069, consistent architecture and slice status, an implementation-plan stop gate, and the round-eleven plan-repair handoff.

## 5. Verification results

### Windows 11, Python 3.14.2, Git 2.50.1

- Initial full baseline: 364 passed, 14 skipped, 45 subtests passed.
- Final full suite: 370 passed, 14 skipped, 45 subtests passed in 145.46 seconds.
- Final `test_route.py`: 209 passed, 1 skipped.
- Final `test_receipt.py` plus `test_route_cli.py`: 30 passed.
- Requirement, suite, and matrix integrity focus: 14 passed.
- Full mutation replay: 63 rows, zero not caught, zero restoration mismatches.

### T540P Linux, Python 3.12.3, Git 2.43.0, pytest 9.1.1 in disposable venv

- Full mutation replay: 63 rows, zero not caught.
- Four mutation sources verified against pre-run SHA-256: all OK.
- 59 active rows and 4 superseded rows.
- 56 active rows caught on both hosts.
- M37, M46, and M48 caught on Linux where Windows skips the symlink test that holds them.

### Other checks

- Whole-suite structure: 6 candidate files, 384 definitions, 384 collected node ids, 0 duplicates, 0 unreachable.
- Universal validation: 0 errors, 1 expected warning for generated Python artifacts.
- JSON parse and `git diff --check`: pass.
- macOS: the workflow config contains a `macos-latest` suite leg. No current CI result was observed in this round, and no macOS mutation replay is claimed.

## 6. Cleanup and restoration

All authoritative replay commands hashed every mutable source before and after execution. The final Windows and Linux runs restored all four sources exactly.

Four verified T540P directories under `/tmp/adc-round-ten*` and three verified local transfer archives were removed. Those temporary copies are not recoverable, but each candidate archive is reproducible from its recorded commit. No repository data or host configuration was removed.

## 7. Remaining blockers and next handoff

- M4 remains not started under D-069.
- R-013, R-018, and R-022 remain explicitly untraced because their behavior is not implemented.
- The slice still needs its human walkthrough and approval; its overall status remains Proposed.
- Round eleven must repair and adversarially review the M4 plan. It must not implement M4 or approve a policy rule.

Next handoff path: `design/routing/HANDOFF-CODEX-ROUND-ELEVEN.md`.

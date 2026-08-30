# Handoff back to Claude: round ten

Date: 2026-08-30. Agent: Codex. Reviewed commit: `fc2cdbd126a0f4060e96006a3a9be78bbba2c624`. Worktree: detached Codex worktree on the `design/assurance-router-specs` history.

This round began as an adversarial review of `HANDOFF-CODEX-ROUND-TEN.md`. The implementation and final verification sections below remain open until remediation finishes.

## 1. Pass 07 findings

### T-01: one committed live mutant exists in branch history

- **Verdict:** verified, limited to this branch after its merge base with `main`.
- **Evidence:** 64 branch commits were inspected. For each commit that carried `matrix.json`, every active row was compared with the source in the same commit. This covered 32 matrix-bearing commits and 1,471 active row/commit pairs.
- **Result:** `a92c869` is the only commit where a row's correct text had existed earlier, the correct text was absent, and the mutant text was present. It carried M01 in `adc_route.py`. The same scan against the current 60-row matrix found no other regression-equivalent commit after a row's correct form had appeared.
- **Limit:** twelve historical row/commit pairs named neither the original nor replacement text because the target moved. They are matrix-history drift, not evidence of a live mutant.

### T-02: the configured mutation suites match their current source families

- **Verdict:** verified for clean-suite reachability; final replay remains pending.
- **Evidence:** the matrix has three active source families. Fifty-two `adc_route.py` rows use `test_route.py`; five `adc_receipt.py` rows use `test_receipt.py`; two `adc_receipt.py` rows use the process-level `test_route_cli.py`; M53 mutates `test_route.py` and uses that file. The exact replay filter was used for clean baselines.
- **Result on Windows:** `test_route.py` reported 197 passed, 1 skipped, 6 deselected; `test_receipt.py` reported 19 passed; `test_route_cli.py` reported 11 passed. No configured suite starts red.
- **Limit:** `test_every_row_names_a_suite_that_exists` proves only that a path exists. The replay is the behavioral proof that each configured suite reacts to its row. Both replay hosts must be rerun after remediation.

### T-03: no test is currently shadowed or unreachable, but the guard is too narrow

- **Verdict:** current tree verified; maintenance coverage refuted.
- **Evidence:** an AST inventory and `pytest --collect-only` comparison covered 6 candidate test files. It found 378 test definitions, 378 collected node ids, 0 duplicate definitions, and 0 unreachable definitions.
- **Gap:** both `SuiteIntegrityTests` checks read only `test_route.py`. A duplicate or overwritten test in any of the other five files would be invisible to the guard that was added because this failure happened twice.
- **Risk:** medium. The present tree is clean, but the stated protection does not cover the suite.

### T-04: D-061 understates the traceability problem

- **Verdict:** refuted as a bookkeeping-only gap.
- **Evidence:** ENGINEERING section 4.1 registers R-001 through R-048, while its verification ledger names R-001 through R-055. R-049 through R-055 therefore have checks without registered requirements. The slice has 51 criteria; S-014 names no R id. The current tests contain 8 unique R ids in comments or docstrings, leaving source-text search unsuitable as a traceability mechanism.
- **Consequence:** a file-level evidence column cannot prove the gate, and neither can counting R-id strings in tests. A requirement needs a named collected test or an explicitly typed non-test evidence record.
- **Risk:** high because this register governs whether verification-authority work may advance.

## 2. D-061 ruling

M3 should have waited for an executable mapping. The suite and mutation matrix are stronger behavioral evidence than prose labels, but they do not authorize crossing an explicit prerequisite that the repository could not check. Calling the gap bookkeeping reverses the role of the gate.

This ruling does not reject the M3 implementation. It requires retroactive review before M4:

1. Register R-049 through R-055 in the confirmed requirements ledger.
2. Give S-014 a requirement link.
3. Add a machine-readable requirement-to-evidence map.
4. Resolve mapped test node ids against the whole collected suite.
5. Keep any not-yet-built M4 requirements in a fixed list that may shrink but cannot grow without changing the guard.
6. Re-run the matrix on Windows and the T540P, and verify source restoration on both.

M4 is not started in this review pass. Its eligibility will be decided only after these checks run.

## 3. Baseline evidence

- Windows 11, Python 3.14.2, Git 2.50.1: 364 passed, 14 skipped, 45 subtests passed.
- Universal validation: 0 errors, 1 warning for generated Python artifacts.
- macOS: the workflow config contains a `macos-latest` suite leg. This pass has no observed CI result and makes no macOS replay claim.

## 4. Remediation status

- [ ] Requirement-to-evidence map and integrity check.
- [ ] Suite-wide duplicate and collection reachability guard.
- [ ] Updated D-061 decision and stale verification ledger rows.
- [ ] M3 review verdict after focused and full verification.
- [ ] M4 eligibility ruling.
- [ ] Windows and T540P mutation replay with restored-source proof.
- [ ] Final commit list and next handoff.

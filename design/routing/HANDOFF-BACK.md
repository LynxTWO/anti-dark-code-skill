# Handoff back to Claude: assurance router spec review

Date: 2026-08-28. Agent: Codex. Repository state: branch `design/assurance-router-specs`, base commit `8a3e309ee6643b386118de0e71a65e643269bd56`, reviewed worktree. Suite result: `131 passed, 13 skipped, 45 subtests passed` in 110.79 seconds.

## 1. Verification results

| Claim | Verdict | Evidence | Note |
|---|---|---|---|
| C-01 | verified | `anti-dark-code/scripts/adc.py:3803-3804,3971` | `--level` is passed directly to `run_gates`; argparse limits it to 0 through 3 and defaults to 0. No route input exists today. |
| C-02 | verified | `anti-dark-code/scripts/adc.py:2390-2396` | `gate_applies` returns true when `include_globs` is absent or empty. |
| C-03 | verified | `anti-dark-code/scripts/adc.py:1573-1581`; count command returned `gate_definition_field_count=13` | The bound fields are level, argv, source, source definition hash, confidence, timeout, source files, resource class, cwd, include globs, exclude globs, inherited environment, and environment. No coverage field is bound. |
| C-04 | verified | `anti-dark-code/scripts/adc.py:111-117,971-976,2375-2387`; `anti-dark-code/tests/test_adc.py:2758-2776` | `changed_files` filters with `is_tooling_relpath`, whose prefixes include `.agents/skills/` and `.anti-dark-code/`. The test proves skill-tree paths are dropped. |
| C-05 | verified | `anti-dark-code/scripts/adc.py:2375-2386` | Committed and working diffs use `--name-only`; untracked collection also returns names only. Status, old path, and mode are not retained. |
| C-06 | verified | `.github/workflows/tests.yml:178-202` | `required` uses `always()` and fails each dependency result that is not `success`, including `skipped`. |
| C-07 | verified | `.github/workflows/proposal-intake.yml:19-76`; `.github/workflows/efficiency-ledger.yml:21-75` | Both workflows check out the base validator separately, check out the candidate as data, and invoke the base `adc.py` against the candidate tree. This verifies the configured pattern, not GitHub's out-of-repo branch settings. |
| C-08 | verified | `anti-dark-code/assets/verification-capabilities.json:4,436,785`; parse command returned `capability_count=20` and ids V01 through V20 | V11 and V20 are present with the claimed names. |
| C-09 | verified | `anti-dark-code/references/14-deterministic-verification.md:50-94` | The reference says four levels and defines Level 0, 1, 2, and 3. |
| C-10 | verified | `anti-dark-code/references/00-conventions.md:182` | The conventions table names `.anti-dark-code/runs/` for local run artifacts. |
| C-11 | verified | `README.md:20`; `anti-dark-code/tests/test_adc.py:2920,2928-2931`; live request to `https://lynxtwo.github.io/anti-dark-code-skill/` returned 200 and matched `docs/index.html` after line-ending normalization | The repository calls `docs/index.html` the website and the live Pages document matches it. |

## 2. Findings

### F-01: A downgrade override contradicted the hard minimum

- Severity: blocking
- Affects: ADD guardrails 1 and 2; EDD principles 2 and 5; EDD section 6
- Wrong: the first draft said no route may lower a requirement, then called `operator_override` the only downgrade path.
- Failure: a reason-bearing receipt could authorize less evidence than the deterministic minimum while still looking valid.
- Proposed change: remove the downgrade path. Allow humans to acknowledge missing evidence without satisfying it. D-018 records the rule.

### F-02: R-012 had no machine-checkable coverage relation

- Severity: blocking
- Affects: R-012, D-012, Rule and Receipt
- Wrong: parallel `obligations` and `gate_ids` arrays did not say which gate satisfied which capability.
- Failure: one unrelated approved gate could make a route appear covered.
- Proposed change: bind every capability id to a nonempty set of explicit gate ids inside the hashed routing policy. D-017 records the rule.

### F-03: Receipt freshness did not define content identity or close the execution race

- Severity: major
- Affects: R-008, R-009, receipt verifier, gate runner binding
- Wrong: the receipt named staged, unstaged, and untracked identity without defining bytes or modes. The available `current_source_identity` helper hashes porcelain status text, which stays unchanged when one dirty byte sequence replaces another. Verification also happened only before execution.
- Failure: a receipt could remain fresh across changed bytes, or a gate could run against inputs changed after verification.
- Proposed change: bind object ids, current bytes, modes, symlink targets, index entries, and submodule state. Recheck immediately before and after each gate. D-019 and R-017 to R-018 record the contract.

### F-04: The Git-reading collector was labeled pure

- Severity: major
- Affects: D-002, ADD sections 4 to 6, EDD principles and test design
- Wrong: `collect_change_facts(repo, base)` was said to be pure while also reading Git. D-002 separately said Git output had to be passed in.
- Failure: property tests could silently test a different boundary from production collection.
- Proposed change: add impure `read_change_inputs(repo, base)` and make `collect_change_facts(snapshot)` pure. Put the status reader and pure router in `adc_route.py`.

### F-05: The change model could lose routing-relevant Git states

- Severity: major
- Affects: R-006, D-010, ChangeFact, unknown-path handling
- Wrong: `--name-status` alone cannot distinguish a mode-only change from content modification, and the enum omitted type changes, unmerged states, and unsupported statuses. Rename and copy classification did not require both paths.
- Failure: a sensitive old path or executable-bit change could receive a lower route, and a conflict could fall outside the unknown-path rule.
- Proposed change: acquire NUL-delimited raw and status records, represent every source separately, classify both paths, and force full or block on unsupported records. R-019 holds the table tests.

### F-06: The self-grading hard-trigger set was incomplete

- Severity: major
- Affects: ADD guardrail 3, R-005, self-grading rule
- Wrong: routing code, policy, gates, CI, and shared test helpers omitted the capability catalog, direct router tests, installer and distribution controls, Git interpretation files, `SKILL.md`, pass references, and future shared fixtures or manifests.
- Failure: a change could alter routing authority while relying on an ordinary policy rule or the router under review.
- Proposed change: make all verified authority classes hard full-route triggers and table-test each class. R-021 names the set.

### F-07: `force_full` and invalid-policy behavior were undefined or contradictory

- Severity: major
- Affects: ADD sections 6, 13, and 14; EDD sections 7 and 14
- Wrong: `force_full` did not define passes, capabilities, or gates. Ordinary gate globs could still remove a gate. One section said invalid policy produced full while another said it produced no route.
- Failure: a route labeled full could omit work, or a broken policy could define its own fallback.
- Proposed change: require a validated policy-root full recipe at Level 3 with no changed-file filtering. Invalid policy exits 2 with no selective receipt. D-020 and R-022 record the contract.

### F-08: Byte-stable receipt identity did not constrain arrays, run ids, or the clock

- Severity: minor
- Affects: R-002, Receipt model
- Wrong: `normalized_json_hash` sorts object keys but preserves array order at `adc.py:300-307`. The receipt also carried an undefined `run_id` while claiming byte stability.
- Failure: equal routes could hash differently because input arrays were shuffled or wall-clock metadata changed.
- Proposed change: canonically sort authoritative arrays, derive `run_id` from the authoritative hash, and keep timestamps outside that hash. R-023 records the tests.

### F-09: Hint monotonicity was stated without a safe hint shape

- Severity: minor
- Affects: D-006, R-011
- Wrong: a hint could raise sensitivity while narrowing breadth, changing the comparison base, or replacing a set unless its allowed fields and merge operations were closed.
- Failure: a syntactically valid hint could lower one route dimension while raising another.
- Proposed change: allow hints to add set members, raise the level, or set booleans true only. Hints cannot alter facts, matches, the base, or existing values. R-020 holds the generated property test.

### F-10: The incoming handoff's validation command is not accepted by the parser

- Severity: minor
- Affects: `HANDOFF-CODEX.md` section 8 only
- Wrong: `python anti-dark-code/scripts/adc.py validate --mode universal --repo .` exits 1 because the `validate` subparser accepts `--skill` and `--mode`, not `--repo` (`adc.py:4005-4008`).
- Failure: a correct implementation could be reported as blocked by an invalid verification invocation.
- Proposed change: use `python anti-dark-code/scripts/adc.py validate --mode universal`. The supported command passed with zero errors and one expected generated-artifact warning after the suite.

## 3. Edits applied

- `design/routing/ARCHITECTURE.md`, sections 4 to 7, 9, 13 to 15: added the Git I/O boundary, positive rule matching, content-bound verification, broader self-grading guards, policy-local evidence binding, and canonical full-route behavior. Closes F-02 to F-07 and F-09 at architecture level.
- `design/routing/ENGINEERING.md`, sections 2 to 14 and 16: added R-015 through R-023, ChangeInput, capability-to-gate binding, no-downgrade authority, canonical receipt identity, the self-grading path classes, and test rows. Closed Q-001 and resolved U-004. Closes F-01 through F-09 at requirement level.
- `design/routing/DECISION-LOG.md`: corrected D-002 and D-004, refined D-012, and added D-016 through D-020 with one status and one `Revisit when:` line each. Records the decisions behind every material edit.
- `design/routing/SLICE-001-route-shadow.md`, sections 3, 6 to 8, and 11: reduced M1 to V21 and V22 catalog editing, added the Git reader, widened slice tests to R-001 through R-023, and added S-015 through S-023.
- All four reviewed documents are version 0.2 Audited. The slice remains Proposed because no code exists and the human approval line is still open.

## 4. Edits proposed but NOT applied

- `design/routing/HANDOFF-CODEX.md` section 8 should remove `--repo .` from the universal validation command. I did not edit the incoming handoff because authority was limited to the four specs plus this handoff back.

No owner ruling in the incoming handoff needed to be changed. No file outside `design/routing/` was edited.

## 5. Q-001 outcome

Closed. The catalog needs two new ids, bringing the future total from 20 to 22:

- V21 Affected-unit testing. V11 selects affected checks but does not execute their assertions.
- V22 Input fuzz testing. V15 injects environmental failure and V02 generates stateful action sequences; neither tests hostile input bytes and values as a method.

The other ten labels map to eight existing ids: static to V09; contract and distribution to V08; mutation to V01; replay to V07; performance to V14; independent review to V17; test integrity to V18; cross-platform and hostile-environment to V12.

## 6. Questions back

- Q-002 remains out of slice. Before selective CI, confirm whether branch protection and required-context settings outside the repository add constraints beyond the two trusted-base workflow patterns.
- Q-003 remains open until thirty shadow comparisons establish whether local run artifacts are enough or an aggregate belongs under publication-controlled metrics.
- The owner still needs to approve the proposed slice before implementation. That approval should include review of D-016 through D-020.

## 7. Readiness

Ready with the listed conditions: Daniel Boyd must review D-016 through D-020 and approve SLICE-001, and M1 must add only V21 and V22 before policy rules name those capabilities. The canonical suite and supported universal validation pass. No router implementation exists yet.

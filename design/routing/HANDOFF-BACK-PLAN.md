# Handoff back: assurance router plan review

Date: 2026-08-29. Agent: Codex. Branch: `design/assurance-router-specs`. Reviewed commit: `dd8af6d24cb84fc5bb3e9f69709414b52dec1766`.

## 1. Verification of P-01 through P-12

Executed tasks: the Python and JSON blocks for Tasks 1 through 8, 11, and 12 were extracted into an isolated Python 3.12 tree. After correcting the module loader, Tasks 1 through 8 and 11 were run red then green. Task 12 is tests-only and ran green. Tasks 9 and 10 were read and probed but could not reach green because their required implementations are absent. Task 13 was read only because it is close-out work for code that does not exist.

| Claim | Verdict | Evidence |
|---|---|---|
| P-01 | Refuted | `py_compile` accepted the assembled Python, but the unmodified test block produced 63 failures and 3 passes on Python 3.12. `dataclass` loading failed because neither loader registered the module in `sys.modules`. |
| P-02 | Refuted | With the loader corrected, Tasks 1 through 8 and 11 showed red then green. Tasks 9 and 10 have prose in place of required code. Task 12 is designed to pass when added and has no red phase. The Task 1 full-suite step also fails on the existing hard-coded count of 20. |
| P-03 | Refuted | `current_route_identity` is consumed but never produced. Task 10 does not show the caller for `verify_receipt`, route-aware `run_gates` arguments, or the before-and-after contract. Task 11 produces helpers that no command consumes. The differing sort keys for inputs and facts are deterministic and harmless by themselves. |
| P-04 | Verified for the parser | Real raw `-z` records for add, modify, delete, rename, copy, type change, and unmerged state parsed with both paths, modes, and status. Copy required explicit detection flags. Malformed raw records are a separate fail-closed defect in G-006. |
| P-05 | Verified | In a real repository with `core.fileMode=false`, `git update-index --chmod=+x` produced a same-object `100644` to `100755` raw record, and the parser returned `mode`. |
| P-06 | Refuted | Replacing per-capability gate union with lossy assignment still left all 60 pure tests passing. The four-fact pool does not exercise two gate sets under one capability or compare every Route field. |
| P-07 | Refuted | Forcing `independent_review` to remain false still left all 60 pure tests passing, including Task 12. Only the first Task 12 policy mutation carries the named mutation-effect assertion. |
| P-08 | Refuted | `read_json`, `safe_calibration_dir`, `normalized_json_hash`, and the current gate entrypoints exist. `current_route_identity` does not. The shown Task 10 integration has no implementation to check against the current `run_gates` signature. |
| P-09 | Refuted, plan correction applied | The bytecode guard was present, but the loader failed on the route module's dataclasses. Both shown loaders now register `sys.modules[spec.name]` before execution. |
| P-10 | Refuted | `load_policy` accepts gate ids as a set, so it cannot detect duplicate, disabled, or unapproved gates. It does not validate capability ids or most policy field types. The template test derives its accepted gate set from the template being tested, while the shipped gate template contains no gates. The validator only parses JSON. |
| P-11 | Verified | In a scratch copy with the new template and validator block, `test_validator_rejects_missing_gate_template` and `test_installer_preserves_calibration_and_creates_adapter` both passed. A missing-routing-template test is still needed. |
| P-12 | Refuted | Only S-003, S-004, and S-006 have direct meaningful checks. S-010 is partly checked. The rest are absent, partial, or satisfied by assertions that do not prove the criterion. See G-009. |

## 2. Findings

### G-001: Task 1 regresses existing catalog contracts

- Severity: blocking
- Status: open, plan scope corrected
- Evidence: a scratch run of `test_probe_and_plan_evaluate_all_capabilities` failed with `22 != 20`. `adc.py` also validates a count of 20 and ids `V01..V20`, prints a 20-capability note, and exposes a 20-capability help string. The catalog description also says 20.
- Failure: adding only the two JSON entries cannot pass the full suite or universal validation.
- Required closure: show the code and test edits for every count and id-set contract. Keep D-016's limit of V21 and V22.

### G-002: The route module loaders fail at runtime

- Severity: blocking
- Status: fixed in the plan
- Evidence: the assembled suite produced 63 failures at `dataclasses._is_type` on Python 3.12. The module created by `module_from_spec` was absent from `sys.modules`.
- Applied correction: register `sys.modules[spec.name] = module` in the test loader and `load_route_helper`, while retaining the bytecode guard.

### G-003: Receipt identity and integrity are not implemented

- Severity: blocking
- Status: open
- Evidence: Task 9 calls an absent `current_route_identity`. The shown receipt has no repository binding, index identity, symlink target state, submodule state, calibration hashes, emitted facts, omissions, or hint record. `verify_receipt` compares only a caller-supplied identity mapping. It does not recompute or verify `receipt_sha256`, policy hash, gate hash, calibration, or binding.
- Failure: a lowered or otherwise edited receipt can retain a matching identity. Policy, gates, index, symlink, submodule, and binding changes are not proven stale.
- Required closure: define and implement the authoritative identity schema, bounded receipt validation, digest verification, current policy and gate comparison, and safe atomic writes that refuse link-like run paths.

### G-004: Gate binding and the canonical full recipe are placeholders

- Severity: blocking
- Status: open
- Evidence: `force_full` only raises `minimum_level`. It does not union full passes, capability bindings, or full gate ids. Task 10 describes receipt loading and runner changes without code. It has no pre-gate or post-gate identity check and no stale-output state. The current runner still applies changed-file globs. The level test passes a nonexistent receipt, so exit 2 would not prove downgrade refusal.
- Failure: S-012, S-013, S-018, and S-022 are not executable. A route labeled full can still omit work.
- Required closure: make the validated `full_recipe` populate the Route, bypass applicability filtering when full, bind obligations to selected approved gates, and show the route-aware gate loop with identity checks around each gate.

### G-005: Policy and self-grading validation can authorize a lower route

- Severity: blocking
- Status: open
- Evidence: `load_policy` does not validate classifier shape, closed enum values, capability ids, pass ids, minimum level range, boolean types, gate enabled and approval state, or duplicate gate definitions. Classification is first-match-wins. A broad early entry can classify an authority path as prose. The authority path table omits several classes named in EDD section 12. Type changes, unmerged records, and unknown status letters do not independently force full.
- Failure: S-005, S-016, S-019, and S-021 are not established, and a changed policy can grade itself through its own classifier.
- Required closure: validate the full schema against gate records and the capability catalog, establish a non-policy-controlled authority floor for this slice, and table-test every authority class.

### G-006: Git acquisition is only partly fail closed

- Severity: major
- Status: partly fixed in the plan
- Evidence: real Git showed that the default raw diff reports a copy as add, while explicit copy detection reports `C100`. The original unstaged command compared `HEAD` to the worktree, so it also returned staged changes. The parser returns an empty list for garbage, a truncated header, and a rename missing its destination.
- Applied correction: acquisition now requests rename and copy detection, compares the index to `HEAD` for staged input, and compares the worktree to the index for unstaged input.
- Remaining closure: malformed or undecodable records must produce a stable unreadable reason and prevent a receipt. Add a temporary-repository integration table for overlapping index and worktree state.

### G-007: The monotonic property test misses lossy fields

- Severity: major
- Status: open
- Evidence: replacing `_merge_obligations` union with assignment left 60 tests green. The generated test compares capability keys but not each capability's gate set, `matched_rule_ids`, `unmapped_paths`, or `unknowns`.
- Failure: P-06, S-002, S-010, and S-015 can pass with a lossy implementation.
- Required closure: add at least one fact or rule that adds a second gate to an existing capability and compare every Route field under every one-fact extension and permutation.

### G-008: The hard-escalator mutation suite is incomplete

- Severity: major
- Status: open
- Evidence: forcing `independent_review` false left the whole pure suite green. The hostile hint loop does not assert obligations or independent review. It is an invariant test, not a mutation that proves each named guard fails the suite.
- Failure: P-07 and S-014 overstate what the mutation block establishes.
- Required closure: apply one mutation per hard escalator, assert each mutation changed the target, run the ordinary suite against it, and require a nonzero result tied to a named test.

### G-009: The S-001 through S-023 map counts mentions as coverage

- Severity: major
- Status: open, self-review corrected

| Criterion | State | Gap |
|---|---|---|
| S-001 | absent | The receipt test does not shuffle facts or snapshot inputs. |
| S-002 | partial | Several Route fields and nested gate sets are not compared. |
| S-003 | covered | Unknown confidence forces full and records the path. |
| S-004 | covered | `SKILL.md` is classified as policy, not prose. |
| S-005 | partial | The tested authority table is smaller than the specified table. |
| S-006 | covered | Calibration paths survive acquisition. |
| S-007 | partial | Delete and the full fact-level kind table are not tested. |
| S-008 | partial | Base and generic snapshot checks are separate, with no route-command reason assertion. |
| S-009 | absent | Policy, gates, binding, runner exit, and receipt digest are not verified. |
| S-010 | partial | Pass and capability-key union are checked, not every requirement field or nested gate union. |
| S-011 | partial | Hints are not compared over every field. |
| S-012 | absent | The command test uses a nonexistent receipt and does not assert the named minimum. |
| S-013 | absent | Coverage returns a bool but is not connected to route or gate selection. |
| S-014 | partial | Two policy comparisons and two hint invariants do not cover every hard escalator. |
| S-015 | absent | The property test does not require prior matched rule ids to remain. |
| S-016 | absent | Gate approval, enablement, duplicates, and capability ids are not validated. |
| S-017 | absent | No identity implementation or index, symlink, or submodule test exists. |
| S-018 | absent | No before-and-after gate check exists. |
| S-019 | partial | Parser fixtures are useful, but real acquisition, malformed blocking, overlap, and submodules are missing. |
| S-020 | absent | Hints are not generated, all fields are not compared, and input immutability is not checked. |
| S-021 | partial | The authority table omits specified path classes. |
| S-022 | absent | Full recipe selection and glob bypass are not implemented. |
| S-023 | partial | Hash clock exclusion is checked, but authoritative bytes and shuffled list inputs are not. |

### G-010: The policy template validates itself against invented gates

- Severity: major
- Status: open
- Evidence: the template test builds `known_gate_ids` from the policy under test. The shipped `gates.json` template has an empty gate list. The repository has no populated calibration policy, so the real command in Task 9 cannot produce the expected route line. The core validator checks JSON syntax only.
- Failure: P-10 is false, and Task 13 cannot record the required real-repository receipt without additional reviewed calibration.
- Required closure: validate against a real gate configuration with approved and enabled state, add the repository-owned policy named by the specs, and add a validator test for a missing routing template.

### G-011: Shadow comparison is not connected to a full run

- Severity: major
- Status: open
- Evidence: Task 11 adds `shadow_result` and `write_shadow`, but no command calls them and no gate result map is produced. Task 13 runs pytest and validation directly, not through a comparator.
- Failure: the slice does not record whether a proposed omission missed a failure.
- Required closure: define the bounded adapter from gate results to `shadow_result`, write `shadow.json`, and integration-test selected failure, omitted failure, blocked gate, and stale gate output.

### G-012: Plan close-out included unsafe or unavailable instructions

- Severity: minor
- Status: partly fixed
- Evidence: the plan required a sub-skill that is not present in this workspace. The invalid-policy exercise says to corrupt and restore a calibration file but gives no bounded backup, hash, or no-new-receipt assertion. The original self-review said there were no prose placeholders.
- Applied correction: removed the unavailable sub-skill requirement and replaced the false self-review claims with the verified gaps.
- Remaining closure: make the invalid-policy exercise use a temporary calibrated repository or a same-directory verified backup and assert that the run directory did not gain a receipt.

## 3. Edits applied

- Added a round-two stop gate to the implementation plan. No worker should implement it until the open blocking findings close.
- Corrected Task 1's file scope and named every existing 20-to-22 catalog contract that must change.
- Corrected both route module loaders to register their modules before executing dataclass definitions.
- Corrected Git acquisition to request copy and rename detection and to keep staged and unstaged comparisons separate.
- Replaced the false acceptance and placeholder statements in the plan's self-review with evidence-backed limits.
- Standardized the policy root field as `full_recipe` in ENGINEERING.md and D-020. This is an interface-name correction, not a change to D-020's decision.
- No file under `anti-dark-code/`, `.github/`, `metrics/`, `.agents/`, or `.anti-dark-code/` was edited.

## 4. Proposed but not applied

- A complete replacement for Tasks 5, 6, 8, 9, and 10. Those changes need one coherent identity schema, full-recipe shape, and gate-loop contract. Patching isolated snippets would create another inconsistent plan.
- A new decision for trusted-base self-grading during future selective local execution. CI names a trusted-base pattern, but local candidate code and policy currently grade themselves.
- The repository-owned calibrated policy and approved gate records. Adding approved rules or gate authority requires owner review under the slice guardrails.
- Safe atomic receipt and shadow publication helpers. These should reuse or match the repository's link checks and atomic-write rules rather than add a weaker writer.
- The expanded property, mutation, temporary-Git, identity, command, and shadow integration suites listed in G-006 through G-011.

## 5. Execution evidence

Scratch root: `J:\TEMP\adc-plan-review-4e2664132c844e64963cca4bdee99d6a`. It was verified under `J:\TEMP`, normalized for Windows read-only Git objects, removed, and confirmed absent.

| Command or probe | Result |
|---|---|
| `py -3.12 -m py_compile ...` over assembled route and tests | passed |
| Unmodified assembled `test_route.py` | 3 passed, 63 failed at the missing module registration |
| Staged Task 1 through 8 and 11 red then green, after loader correction | every red run returned 1; every green run returned 0 |
| Task 12 tests-only block | 4 passed |
| Full pure plan suite after loader correction | 60 passed, 6 CLI tests deselected |
| Lossy obligation-union mutation | 60 passed, proving the test gap |
| Disabled independent-review mutation | 60 passed, proving the test gap |
| Existing catalog test with V21 and V22 | failed with `22 != 20` |
| Template installer and missing-gate validator tests | 2 passed |
| Real Git raw probe | add, modify, delete, rename, copy, mode, type-change, and unmerged parsed; copy was `A` without detection flags and `C100` with them |
| Malformed raw probe | garbage and truncated records returned `[]` instead of blocking |
| `python -m pytest anti-dark-code/tests -q` | `131 passed, 13 skipped, 45 subtests passed in 120.91s` |
| `python anti-dark-code/scripts/adc.py validate --mode universal` | `VALID (universal): 0 errors, 1 warning(s)`; warning was generated Python artifacts |
| `git diff --check` before this report | passed; line-ending notices only |

Repository state after the review contains design-only changes: ENGINEERING.md, DECISION-LOG.md, the slice plan, and this handoff. The implementation tree, workflows, metrics, and local calibration trees are unchanged.

## 6. Questions

1. What passes, capability-to-gate bindings, and gate ids make up this repository's `full_recipe`? D-020 requires all three, while the current template names only a level and gate ids.
2. Where should this repository's populated routing policy and approved gates live for the required real-repository walkthrough? No installed or fallback calibration exists in this checkout.
3. Does Daniel Boyd approve the three template rules being marked `approved`? The slice guardrail says adding a rule requires review, but the plan currently pre-approves them.
4. What trusted-base mechanism will prevent modified local router code or classifier order from grading its own change before selective local execution is enabled?

## 7. Readiness

NOT READY

Close G-001, G-003, G-004, and G-005 first, then rewrite and execute Tasks 5 through 10 as one interface-consistent batch. After that, close the property, mutation, coverage, calibration, and shadow gaps before removing the plan's round-two stop gate.

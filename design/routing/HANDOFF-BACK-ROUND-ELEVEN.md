# Handoff back to Codex: round eleven

Date: 2026-08-30. Agent: Claude. Starting commit: `3e4eda3`, the head of `codex/round-ten-evidence-audit` and of draft PR #21. Branch: `claude/round-eleven-evidence-contracts`, in a separate worktree so neither agent's checkout blocks the other.

## 1. Terminal outcome

- **M3 is closed.** The four requirements D-070 reopened are held by collected tests. R-005 and R-021 are closed by contract D-071; R-017 and R-019 by contract D-072. Both contracts were chosen by the owner from written alternatives, not by the agent.
- **M4 is not started, and its plan is repaired.** Tasks 10 through 12 name real seams, real lifecycles, and exact test node ids. No M4 code was written, no policy rule was approved, and no selective execution was enabled.
- **M4 is eligible for an implementation round**, subject to the adversarial review this handoff invites. The three untraced ids are R-013, R-018, and R-022, unchanged, and each now has planned test node ids rather than prose.
- Round ten's headline claims reproduced. Two of them understated what they found, and this round measured the difference.
- The full suite is `389 passed, 14 skipped, 45 subtests passed`, up from 371. The matrix is 68 rows, all caught.

## 2. Round-ten claims, independently checked

### Reproduced exactly

- **Baseline.** `371 passed, 14 skipped, 45 subtests passed` on Windows 11, Python 3.14.2, Git 2.50.1, before any change. The PR's number is correct.
- **T-01, the historical live mutant.** `a92c869` carries M01's replacement text and not its correct text; `9e61386` restores it. Checked directly against both commits rather than by rerunning the scan.
- **D-070's central claim.** Node-id reachability is not clause coverage, and the four requirements it names were genuinely partial. `submodule` appears zero times in `adc_route.py`, `adc_receipt.py`, `test_route.py`, and `test_receipt.py`, against an EDD data model that requires a `submodule_state` object.

### Understated: R-005 and R-021 were wider than three paths

D-070 named three real paths that did not force full. Measuring every path class R-021 enumerates, against the installed classifier with every rule approved in memory, found **five**:

| Class | Path | Route with rules approved |
|---|---|---|
| router code | `anti-dark-code/scripts/adc_route.py` | Level 2 product, `force_full` false |
| router schema | `anti-dark-code/assets/templates/calibration/routing-policy.json` | Level 2 schema, `force_full` false |
| capability catalog | `anti-dark-code/assets/verification-capabilities.json` | Level 2 schema, `force_full` false |
| installer and distribution | `anti-dark-code/scripts/adc.py` | Level 2 product, `force_full` false |
| routing-owning pass reference | `anti-dark-code/references/00-preflight.md` | Level 0 docs, `force_full` false |

The installer and the policy template are the two D-070 did not list.

Two further classes forced full for the wrong reason. `calibration/gates.json` and the installed routing policy matched no classifier glob at all, so they were unmapped, and an unmapped path forces full because its confidence is unknown. Adding one ordinary `**/calibration/*.json` entry to a policy would have removed that protection without touching a rule. Of eleven classes, four forced full because something graded them as authority.

### Understated: R-017 is not unspecified, it is fail-open

D-070 recorded that submodule state was undefined. Measured against a real parent repository with a real submodule, the receipt binding is fail-open, and it needs no adversary:

- **An ordinary edit to a tracked file inside the submodule left `worktree_identity` byte-identical**, while `git status` reported the parent dirty (`M vendor`). No timestamp was touched.
- **Moving the submodule's checked-out commit did the same.**
- A control change to an ordinary tracked file moved the identity, so the harness was sound.

The mechanism: `worktree_identity` keeps each entry's path and its content-and-topology field and drops size and mtime, deliberately and correctly, because a route does not depend on a timestamp. A gitlink is not a regular file, so it has no content digest; its field is the constant `special:<dir mode>:<topology>`. Nothing in it moves when the submodule does.

A receipt taken before either change still verified as fresh. Acquisition had the matching gap: a gitlink record parsed as an ordinary modification and the snapshot called itself complete.

### Not checked

- The 64-commit, 1,471-pair historical scan was spot-verified at its stated conclusion, not rerun.
- No Linux or macOS run. Every number in section 5 is Windows only. The two-host record in the matrix is round ten's, except for the four new rows, which carry one host and say so.

## 3. Contracts, both owner-chosen

The owner was given three written alternatives for each and chose the first in both cases. The rejected options are recorded in D-071 and D-072 rather than deleted.

### D-071: a classifier is what makes a path authority, and it is checked at load

The shipped template now classifies the router, the receipt writer, the installer, the capability catalog, every `calibration/*.json`, and every `references/*.md` with effect `verification-authority`, which the template's existing force-full rule already matches. `load_policy` refuses any policy under which a self-grading path could take a route below the full recipe: it classifies each path in `SELF_GRADING_PATHS` and asks whether every rule that could fire on it still leaves `force_full` true.

The first version of this guard checked only the classification and was wrong. Attacking it before writing this handoff: deleting the `verification-authority` rule and approving one rule matching `effects: ["verification-authority"]` at `minimum_level: 0`, classifier untouched, took **ten of the eleven classes below the full recipe**, because `build_route` sets `fired` on any match and the unrouted fallback never ran. The guard now checks the property instead of a proxy for it, D-071 records the disproven reasoning rather than quietly correcting it, and row M68 holds the corrected form.

A hard escalator in `build_route` was rejected: it would put routing authority in a second place, invisible to whoever reviews the policy.

### D-072: a submodule is refused, not bound

A listed path that is a directory is a gitlink, because `git ls-files` never lists an ordinary directory. The fingerprint marks it, `Binding` carries `unsupported_paths` inside the hashed payload, `verify_receipt` returns not fresh with `ADC-STALE-009` before comparing any other field, `route --write` refuses to write such a receipt, and the raw parser records `ADC-ROUTE-SUBMODULE-UNSUPPORTED` for mode `160000` on either side, which withdraws snapshot completeness and forces the full recipe.

R-017 was amended to say so. R-019 needed no amendment: it already said unsupported records block selective routing.

Binding real submodule state is the better end state and was not taken now. Nested submodules, uninitialized submodules, detached HEADs, and unreachable remotes each need their own real-repository fixture, and a partial implementation of submodule binding is the same failure D-070 exists to record.

**The cost, stated plainly:** a repository containing a submodule cannot use routing receipts and always takes the full recipe.

## 3.5 Criterion-by-criterion mapping for the reviewed untraced set

Every clause of all seven ids, and what holds it. `test_route.py::` is elided from node ids.

### R-005 — routing code, routing policy, gate configuration, CI, and shared test helpers force the full route

| Clause | Held by | State |
|---|---|---|
| routing code | `SelfGradingAuthorityTests::test_every_self_grading_path_class_forces_the_full_recipe`, entry "router code and Git interpretation" | Closed |
| routing policy | same test, entry "routing policy" | Closed |
| gate configuration | same test, entry "gate configuration" | Closed |
| CI | same test, entry "continuous integration" | Closed |
| shared test helpers | same test, entry "shared test support" | Closed |
| the paths named still exist | `test_each_named_self_grading_path_exists` | Closed |
| an ordinary path is not forced full | `test_an_ordinary_documentation_path_does_not_force_full` | Closed |

### R-021 — self-grading inputs force the canonical full route

All eleven classes are rows in `SELF_GRADING_PATHS` and are asserted together by `test_every_self_grading_path_class_forces_the_full_recipe`: router code, router schema, capability catalog, gates, CI, installer and distribution controls, Git interpretation files, router tests, shared test support, `SKILL.md`, and the routing-owning pass references. The measurement runs with every rule approved in memory, which is the only state in which the assertion means anything under D-064.

| Clause | Held by | State |
|---|---|---|
| each class forces full | `test_every_self_grading_path_class_forces_the_full_recipe` | Closed |
| a policy cannot grade one lower | `test_a_policy_grading_the_router_as_product_code_is_refused` | Closed |
| an unmapped path is still safe, and not a load failure | `test_an_unmapped_self_grading_path_is_not_a_load_failure` | Closed |
| the shipped policy satisfies its own guard | `test_the_installed_policy_loads` | Closed |
| the escalator cannot be silently removed | matrix rows M64, M65 | Closed |

### R-017 — receipt freshness binds content, modes, index entries, symlink targets, and refuses a tree it cannot bind

| Clause | Held by | State |
|---|---|---|
| content, not status text | `ReceiptFreshnessTests::test_different_dirty_bytes_under_identical_status_are_stale` | Closed |
| index entries | `AcquisitionAgainstRealGitTests::test_a_same_size_index_rewrite_is_detected` | Closed |
| symlink targets | `AcquisitionAgainstRealGitTests::test_a_symlink_is_identified_not_followed` | Closed |
| a tree holding unbindable state is refused | `SubmoduleContractTests::test_a_receipt_over_a_submodule_tree_never_verifies_fresh` | Closed by D-072 |
| the unbindable path is named | `SubmoduleContractTests::test_a_gitlink_is_reported_as_unbindable` | Closed |
| an ordinary tree still verifies fresh | `SubmoduleContractTests::test_an_ordinary_tree_still_verifies_fresh` | Closed |
| the blindness is recorded, not hidden | `SubmoduleContractTests::test_the_identity_alone_still_cannot_see_the_submodule_move` | Closed |
| the refusal cannot be silently removed | matrix row M67 | Closed |
| **submodule state is bound** | nothing | **Deliberately not built.** D-072 refuses instead; R-017 amended to match |

### R-019 — acquisition represents every supported record, and unsupported records block selective routing

| Clause | Held by | State |
|---|---|---|
| rename keeps both paths | `RawParserTests::test_rename_keeps_both_paths` | Closed |
| copy keeps both paths | `RawParserTests::test_copy_keeps_both_paths` | Closed |
| mode-only and type changes, conflicts | `RawParserTests::test_type_change_and_unmerged_are_preserved` | Closed |
| staged, unstaged, untracked, committed | `AcquisitionTests::test_snapshot_unions_all_four_sources` | Closed |
| a repository mid-merge acquires | `AcquisitionAgainstRealGitTests::test_a_repository_mid_merge_still_acquires` | Closed |
| a submodule record is represented | `RawParserTests::test_every_real_git_mode_parses_into_a_record` | Closed |
| an unsupported record blocks selective routing | `RawParserTests::test_only_the_gitlink_mode_withdraws_snapshot_completeness`, `SubmoduleContractTests::test_a_dirty_submodule_makes_the_snapshot_incomplete`, `test_so_the_route_forces_full` | Closed by D-072 |
| both sides of the mode are read | `RawParserTests::test_a_submodule_added_or_deleted_is_also_unsupported`, matrix row M66 | Closed |

### R-013 — `--level` may raise above the computed route but never lower it

| Clause | Planned node id | State |
|---|---|---|
| a lower level exits 2 and names the minimum | `test_route_cli.py::RouteLevelCliTests::test_a_level_below_the_route_minimum_exits_two_and_names_it` | **Untraced.** Planned in Task 10, not built |
| a higher level is accepted | `test_route_cli.py::RouteLevelCliTests::test_a_level_above_the_route_minimum_is_accepted` | Untraced |
| an absent level takes the route minimum | `CanonicalFullTests::test_level_may_raise_the_route_minimum` | Untraced |

### R-018 — concurrent repository changes cannot produce accepted gate evidence

| Clause | Planned node id | State |
|---|---|---|
| the bound receipt is verified before execution | `test_route_cli.py::StaleReceiptCliTests::test_a_stale_receipt_refuses_the_run_with_exit_two` | **Untraced.** Planned in Task 10, not built |
| identity is captured before each gate and again after | `GateLifecycleTests::test_a_mutation_during_a_gate_marks_that_gate_stale` | Untraced |
| a moved identity marks that gate stale | same | Untraced |
| a gate that changed nothing is not marked stale | `GateLifecycleTests::test_a_gate_that_changes_nothing_is_not_marked_stale` | Untraced |
| a stale result satisfies no obligation | `GateLifecycleTests::test_a_stale_gate_result_cannot_satisfy_an_obligation` | Untraced |
| an empty obligation map is not coverage | `GateLifecycleTests::test_an_empty_obligation_map_is_not_covered` | Untraced |
| the stop-or-continue decision is explicit | `GateLifecycleTests::test_the_run_stops_when_the_tree_moves_even_with_keep_going` | Untraced |
| the escalator cannot be silently removed | matrix rows M68, M69, M70 | Untraced |

### R-022 — the canonical full route is independent of changed-file applicability filters

| Clause | Planned node id | State |
|---|---|---|
| `include_globs` cannot remove a gate under force_full | `CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs` | **Untraced.** Planned in Task 10, not built |
| a candidate selection cannot remove a gate | `CanonicalFullTests::test_a_candidate_selection_cannot_remove_a_gate` | Untraced |
| the validated full recipe runs at Level 3 | `CanonicalFullTests::test_force_full_runs_the_canonical_set_despite_include_globs` | Untraced |
| a candidate never reaches receipt authority | `test_a_candidate_route_is_refused_by_the_receipt_writer`, matrix row M71 | Untraced |

Four ids closed, three untraced with named clauses and named node ids. No id was moved out of `untraced` on the strength of a plan.

## 4. M4 plan repair

All four blocking contradictions are addressed as specification. None is implemented.

1. **Candidate versus authority route.** `CandidateRoute` is a separate frozen dataclass, not a `Route` with a flag, so handing one to the gate selector or the receipt writer is a `TypeError` or a `ReceiptError` at the call site. It carries `considered_rule_ids` and a constant `provenance`, serializes only into `shadow.json`, and is `None` when the snapshot is incomplete.
2. **R-018 before and after.** Task 10 names `run_gates` at `adc.py:2573`, the gate loop at `2691`, the pass and failure paths at `2773` and `2815`, and the summary at `2821`. Identity is captured immediately before `Popen` and again where `duration` is computed. A moved identity marks that gate `stale`, which satisfies no obligation, and the run stops and returns 2 **even with `--keep-going`**, because `--keep-going` is a decision about failing gates and not about the repository moving underneath the run. Cost is two fingerprints per gate, measured at 0.038s over 345 files.
3. **R-022 canonical full execution.** Under `force_full` the gate list comes from `canonical_full_set` and the changed-file filter at `adc.py:2600` is not applied.
4. **Comparator integration.** Outcomes come from the `summary` dict `run_gates` builds. The vocabulary is closed to `pass`, `fail`, `config-error`, `stale`, `not-run`, `skipped`, and an outcome outside it raises. A non-pass omitted outcome is a miss. `selected_all_passed` requires a non-empty selection and an explicit `pass` per gate, because `all()` over a missing gate is vacuously true and would let an aborted run read as clean targeted verification.

Task 12's inline mutation code was stale — it called `load_policy` with two arguments and read `full_recipe["gate_ids"]`, neither of which has existed since D-062. It is replaced with eight matrix rows. Four of them, M64 through M67, are implemented and caught in this round; M68 through M71 land with Tasks 10 and 11.

## 5. Verification results

Windows 11, Python 3.14.2, Git 2.50.1, pytest 9.0.2. One host only.

- Baseline before any change: `371 passed, 14 skipped, 45 subtests passed`.
- Final full suite: `389 passed, 14 skipped, 45 subtests passed`.
- New tests: 8 in `SelfGradingAuthorityTests`, 8 in `SubmoduleContractTests`, and three in `RawParserTests` replacing one, for a net of 18. 371 plus 18 is 389.
- Mutation replay, all 67 rows: `67 mutants, 0 not caught`, then M64 through M68 replayed again after the D-071 correction: `5 mutants, 0 not caught`. M37, M46, and M48 report SURVIVED here and are recorded as caught elsewhere, because Windows skips the symlink test that holds them (D-054).
- M64 through M67 replayed individually first: 4 mutants, 0 not caught.
- Matrix integrity, suite structure, and requirement traceability guards: pass.

The four new rows carry Windows results only. They need a Linux replay before the matrix's two-host property holds again, and that is the first thing this handoff asks for.

## 6. Findings for round twelve, not fixed here

1. **`_repo_fingerprint` can return a one-tuple.** When a `git ls-files` call fails it returns `("unreadable",)`, and both `worktree_identity` and `_identity_and_unsupported` unpack it into two names. That is a `ValueError` traceback, not a refusal. Reachable whenever git fails mid-run, which is exactly when a clean refusal matters. Left unfixed because what "unreadable" should mean for a receipt is a design decision, not a typo.
2. **The traceability guard cannot prevent the failure that produced D-070.** `assertLessEqual(untraced, REVIEWED_UNTRACED)` lets the untraced set shrink freely, so a future round can remove an id and map it to any test that collects. Recorded as U-015. The guard is still worth having; it just cannot hold this.
3. **`**/*.md` and `**/SKILL.md` do not match a root-level file** under `fnmatch`, where `**/` needs at least one separator. A repository with `SKILL.md` at its root leaves it unmapped, which forces full, so the direction is safe. Worth a deliberate decision rather than an accident.
4. **The plan's Self-Review was stale in both directions.** Its Known gaps still listed symlink and index identity as unimplemented long after they were built, while its Placeholder scan was accurate. Corrected in this round.

## 7. Files changed

Production:

- `anti-dark-code/scripts/adc_route.py`: `GITLINK_MODE`, `GITLINK_MARK`, `SELF_GRADING_PATHS`, `_check_self_grading` and its call in `load_policy`, the gitlink branch in `_repo_fingerprint`, the gitlink problem code in `parse_raw_z`.
- `anti-dark-code/scripts/adc_receipt.py`: `SCHEMA_VERSION` 2, `STALE_UNSUPPORTED`, `Binding.unsupported_paths`, `_identity_and_unsupported`, the refusal in `verify_receipt`.
- `anti-dark-code/scripts/adc.py`: unbindable paths printed by `route`, and `route --write` refusing such a tree.
- `anti-dark-code/assets/templates/calibration/routing-policy.json` and `.agents/skills/anti-dark-code/calibration/routing-policy.json`: six classifier entries.

Tests:

- `anti-dark-code/tests/test_route.py`: `SelfGradingAuthorityTests`, `SubmoduleContractTests`, three raw-parser tests replacing one.

One existing test changed. `test_every_real_git_mode_is_accepted` asserted that mode `160000` raised no problem, which is the behaviour D-072 removes. It is now `test_every_real_git_mode_parses_into_a_record`, asserting that every real mode still produces its record and is not refused as malformed, with the completeness question moved to its own test. Flagged here because a test changed in the same patch as the production code it grades deserves the scrutiny.

Design:

- `DECISION-LOG.md`: D-071, D-072.
- `ENGINEERING.md`: R-017 amended; five verification-ledger rows; U-006 and U-008 updated; U-015 added.
- `requirement-evidence.json`: R-005, R-017, R-019, R-021 no longer `partial`, with node ids added; `untraced` is now R-013, R-018, R-022.
- `plans/2026-08-28-assurance-router-slice-001.md`: Tasks 10 through 12 rewritten; Self-Review corrected.
- `SLICE-001-route-shadow.md`, `ARCHITECTURE.md`: M3 status.
- `mutants/matrix.json`: M64 through M67.

## 8. What round twelve should do

1. **Replay M64 through M67 on Linux.** The matrix's two-host property is the strongest evidence this project has, and four rows currently break it.
2. **Adversarially review D-071 and D-072**, particularly whether refusing a submodule tree is the right trade for a repository that has one, and whether `SELF_GRADING_PATHS` is a list that will rot.
3. **Then implement M4** against the repaired Tasks 10 through 12, closing R-013, R-018, and R-022 with the node ids the plan now names.

Do not treat this handoff as acceptance of its own contracts. Round eleven found that round ten's independent review had itself understated two findings; the same should be assumed of this one.

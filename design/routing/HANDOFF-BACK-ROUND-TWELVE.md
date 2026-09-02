# Handoff back: round twelve

Date: 2026-08-30. Agent: Codex. Base: `8f46a76`, the head of `claude/round-eleven-evidence-contracts` and draft PR #22 when this worktree was created. Branch: `codex/round-twelve-m4`, in a separate worktree.

## 1. M4 status

**M4 is implemented.** The work landed in the requested order, with a passing suite and caught matrix rows before each next requirement began.

| Deliverable | Result | Commit |
|---|---|---|
| R-013 | `gates --route` rejects a requested level below the routed minimum and accepts an equal or higher level. Three exact collected nodes are registered. | `c1e007a` |
| R-022 | A `force_full` route selects `canonical_full_set` without applying changed-file applicability filters. Its exact collected node is registered. | `a283962` |
| R-018 | One receipt context is verified before execution; its route payload, validated policy, gate configuration, and repository identity remain fixed through selection and launch; identity is compared immediately before and after each real gate subprocess. A moved tree produces `stale`, satisfies no obligation, stops even with `--keep-going`, and returns 2. Ten exact collected nodes are registered. | `43bae8e`, hardened by `5fdfb9e` and `ca7d797` |
| Candidate shadow route | `CandidateRoute` is a separate immutable type rejected by receipt authority and executable gate selection. The comparator consumes real authoritative gate outcomes and atomically writes `shadow.json`. | `94a39c9` |

No routing-policy rule was approved. Selective local or CI execution was not enabled. Candidate data cannot authorize a receipt or alter the executed gate set.

`requirement-evidence.json` now maps R-013, R-018, and R-022 only to exact collected nodes, and `untraced` is empty. Codex reviewed the shrink of `REVIEWED_UNTRACED` against the implemented clauses and recorded the reason beside that review set.

## 2. Ordered commits

1. `3dfcf20 routing: replay round-eleven matrix on Linux`
2. `8635d8b routing: complete the round-eleven two-host record`
3. `c1e007a routing: enforce the routed gate level floor`
4. `a283962 routing: run the canonical set under force full`
5. `43bae8e routing: bind gate results to repository identity`
6. `94a39c9 routing: isolate and record candidate shadow routes`
7. `5fdfb9e routing: close M4 preflight authority races`
8. `ca7d797 routing: carry verified authority through gate launch`
9. `807e3e2 routing: record Linux replay for verified authority`

The first two commits repair the incoming evidence record. The next four are the M4 implementation commits in the requested order. The last three close independent review findings and record their two-host evidence without changing policy approval or selective-execution state.

## 3. Fixed section 2 review

Each result below is intentionally bounded to the named check.

### D-071

- **Installed layout: amended.** A real `.agents/skills/anti-dark-code/` installation routed all eleven actual shipped path classes full, but the literal source-layout guard can be satisfied by source-only classifier globs while the installed router routes cheaply. D-071 should reopen for portable path authority in round thirteen; this did not block M4.
- **Ordinary catch-all: reversed premise.** `match: {}` is rejected by the policy schema because a rule needs a nonempty match, so there is no legitimate empty-match catch-all suffering the proposed over-refusal.
- **Third cheap classifier: upheld.** Adding a third cheap classification for an authority path still unions with the authority fact and produces Level 3 with `force_full` true.
- **Load-path cost: upheld.** Median measurements were about 0.000296 seconds for policy load, 0.000205 seconds for the self-grading guard, and 0.1480 seconds for the repository fingerprint; the guard was about 0.14 percent of fingerprint cost and remains appropriate on the load path.

### D-072

- **Refuse-versus-bind trade: upheld for the current consumer.** The repository has 126 indexed candidates, no gitlinks, and no `.gitmodules`, so refusal imposes no current receipt cost. The five alternate binding fixtures were not built; that larger design remains a future owner decision.
- **Directory edge cases: upheld with measured scope.** A Windows junction at a tracked path and an indexed but uncommitted submodule were both reported unsupported; a Linux tracked directory symlink remained a symlink and a Git type change, so the parser withdrew completeness rather than mistaking it for a gitlink.
- **Workflow dependency: upheld.** Three files exist under `.github/workflows/`, and none depends on `adc.py route --write` returning 0.

### Round-eleven method

- **Linux behavior: amended.** All 68 incoming rows were replayed on T540P; M37, M46, and M48 were caught there, M64 through M68 behaved as contract failures, and no mutant survived. The replay also exposed missing Windows records for M65 and M68, which were then caught and recorded on Windows.
- **Historical scan: limitation retained.** The 64-commit historical live-mutant scan was not rerun; only its previously recorded conclusion remains available.
- **Changed Git-mode test: upheld.** Reading the split adversarially showed that one test now proves all real modes parse into records while separate tests prove mode `160000` on either side withdraws completeness. M66 holds the both-side check.

## 4. Provisional `_repo_fingerprint` decision

The packet in D-073 retains all three alternatives:

1. raise a typed `ReceiptError` and refuse to construct or verify a binding;
2. return an identity that can never match, making every receipt stale;
3. mark the snapshot incomplete, force the full recipe, and refuse a receipt in the D-072 shape.

Alternative 1 is implemented provisionally. When either Git listing fails, binding construction, receipt verification, route writing, and routed gate preflight now fail closed with a named refusal and exit 2 instead of leaking `ValueError`; M73 catches the old crash. The owner may replace this semantics in round thirteen without reopening M4's requirement behavior.

## 5. Verification and mutation evidence

Linux replay used T540P with Linux `7.0.0-28-generic`, Python 3.12.3, Git 2.43.0, pytest 9.1.1, and a disposable virtual environment. Source hashes matched before and after every replay. All 68 incoming mutants were caught or caught elsewhere under the D-068 rules; the submodule tests ran rather than skipping. After the final replay, `/tmp/adc-round-twelve-replay.hrFk5ntV` was resolved, deleted, and confirmed absent.

The matrix now has 87 rows: 83 active and 4 superseded. Of the active rows, 80 are `caught` and M37, M46, and M48 are `caught elsewhere`; every active row has both a Windows and a T540P Linux result, and there are no survivors or unverified rows.

New escalator rows:

| Row | Contract held | Windows | Linux |
|---|---|---|---|
| M69 | post-gate identity is not reused as the next pre-gate identity | 2 failed | 2 failed |
| M70 | stale execution cannot continue under `--keep-going` | 1 failed | 1 failed |
| M71 | an empty obligation map is not vacuous coverage | 1 failed | 1 failed |
| M72 | candidate construction cannot return an authoritative `Route` | 4 failed | 4 failed |
| M73 | unreadable fingerprint cannot fall through to tuple unpacking | 1 failed | 1 failed |
| M74 | same-schema receipt route tampering cannot bypass `run_id` integrity | 1 failed | 1 failed |
| M75 | post-preflight repository movement cannot become the pre-gate baseline | 1 failed | 1 failed |
| M76 | gate selection cannot reread replaced receipt bytes | 1 failed | 1 failed |
| M77 | serialized candidate provenance cannot reach gate selection | 1 failed | 1 failed |
| M78 | non-object receipt JSON cannot reach mapping access | 1 failed | 1 failed |
| M79 | gate planning cannot refresh the Git index after preflight | 1 failed | 1 failed |
| M80 | serialized candidate provenance cannot reach receipt authority | 1 failed | 1 failed |
| M81 | candidate reconstruction cannot reread replaced receipt bytes | 1 failed | 1 failed |
| M82 | invalid same-schema route fields refuse with exit 2 | 1 failed | 1 failed |
| M83 | gate execution cannot reread replaced gate-configuration bytes | 1 failed | 1 failed |
| M84 | candidate reconstruction cannot reload replaced policy bytes | 1 failed | 1 failed |
| M85 | first-write run-store setup cannot occur outside acquisition | 1 failed | 1 failed |
| M86 | a non-object gate root refuses with exit 2 | 1 failed | 1 failed |
| M87 | a non-object policy root refuses with exit 2 | 1 failed | 1 failed |

The final Windows full-suite result is `420 passed, 14 skipped, 48 subtests passed in 183.01s`. Requirement traceability and mutation-matrix integrity report `8 passed`, and universal validation reports 0 errors with the one expected generated-artifact warning. A final independent review of `807e3e2` reported no critical, important, or minor findings, confirmed all prior findings closed, and assessed the head ready to merge. No current macOS execution was observed; macOS remains only the configured CI suite.

## 6. Additional implementation finding

While wiring candidate reconstruction from a verified receipt, an authority gap was found: `verify_receipt` compared the binding but did not recompute `run_id`, so same-schema edits to authoritative route fields could appear fresh. D-074 records the fix: recompute after the foreign-schema guard and refuse a digest mismatch; M74 catches removal of that check.

The final independent review found two further authority races. A change after preflight could become the pre-gate baseline, and the command verified one receipt read but reread the path for route and candidate data. D-075 closes both: stable artifacts exist before binding and preflight, one immutable verified receipt object feeds every consumer, every pre-gate identity must equal the verified identity, read-only Git diagnostics cannot refresh the index, and malformed or serialized-candidate inputs refuse cleanly. Process-level seam tests and M75 through M82 hold the repaired boundaries.

The independent re-review found two remaining calibration-path races and a first-write acquisition split. D-076 closes them: the verified context now carries the validated policy and canonical gate-configuration bytes through selection and launch, and run-store setup precedes change acquisition. Swap-and-restore process tests plus M83 through M87 hold those boundaries and the related clean shape refusals.

## 7. Exact files changed

Production:

- `anti-dark-code/scripts/adc.py`
- `anti-dark-code/scripts/adc_receipt.py`
- `anti-dark-code/scripts/adc_route.py`

Tests:

- `anti-dark-code/tests/test_receipt.py`
- `anti-dark-code/tests/test_route.py`
- `anti-dark-code/tests/test_route_cli.py`

Evidence and design:

- `design/routing/ARCHITECTURE.md`
- `design/routing/DECISION-LOG.md`
- `design/routing/ENGINEERING.md`
- `design/routing/SLICE-001-route-shadow.md`
- `design/routing/mutants/matrix.json`
- `design/routing/plans/2026-08-28-assurance-router-slice-001.md`
- `design/routing/requirement-evidence.json`
- `design/routing/HANDOFF-BACK-ROUND-TWELVE.md`

## 8. Not checked and carried forward

- No current macOS execution was performed.
- The 64-commit historical live-mutant scan was not rerun.
- The five real-repository variants needed to design submodule binding were not built.
- D-071's literal source-layout guard remains portable only by convention, not by a measured installed-layout invariant. Reopen that portability clause in round thirteen.
- The provisional D-073 owner decision remains open to alternatives 2 or 3.

The branch is pushed as `origin/codex/round-twelve-m4` and is intentionally preserved for review. The original checkout was not changed.

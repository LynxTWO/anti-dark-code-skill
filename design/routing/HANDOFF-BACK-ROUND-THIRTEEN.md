# Handoff back to Codex: round thirteen

Date: 2026-08-31. Agent: Claude. Base: `b9b1e71`, the head of `codex/round-twelve-m4`. Branch: `claude/round-thirteen-audit`, in a separate worktree.

## 1. Terminal outcome

- **Round twelve's numbers reproduce exactly.** The suite, the matrix, and the two-host record are all as claimed. This was a strong round.
- **One claim did not survive.** `untraced` was emptied while R-018's implementation was narrower than R-018's clause. A gate that changes a tracked file, uses the changed value, and restores the original was accepted as a clean pass. D-077 closes it.
- M4 remains implemented. Nothing was reverted, no policy rule was approved, and no selective execution was enabled.
- **Two further defects were found and fixed**, one of them the third hole in this branch's own self-grading guard. D-078 and D-079.

## 2. What reproduced

| Claim | Result |
|---|---|
| `420 passed, 14 skipped, 48 subtests` | Reproduced exactly on Windows before any change |
| 87 rows, 83 active, 4 superseded | Exact |
| Every active row on both Windows and T540P Linux | Exact: 83 of 83, zero rows missing a host |
| 80 `caught`, 3 `caught elsewhere` | Exact, and the three are M37, M46, M48 as stated |
| `untraced` is empty | The list is empty; see section 3 for whether it should have been |
| R-013, R-018, R-022 map only to exact collected nodes | True; the nodes exist and collect |

The R-018 tests are not token mappings. `GateLifecycleTests` builds a real repository, writes a real `gates.json` with `owner_confirmed_safe_to_execute`, and runs the real `run_gates` subprocess loop with a gate that writes into the worktree while it executes. `test_force_full_runs_the_canonical_set_despite_include_globs` builds a fixture whose `include_globs` would remove every canonical gate. This is the runner integration the round-twelve handoff asked for, and it is real.

Round twelve also found three authority gaps of its own (D-074, D-075, D-076) that round eleven's plan had not anticipated: `run_id` was not recomputed on verify, a post-preflight change could become the pre-gate baseline, and the command reread the receipt path for route and candidate data. Those are good findings.

## 3. What did not survive: R-018 was narrower than its clause

R-018 reads: *"given a fresh receipt, when an input changes after preflight **or during a gate**, then that gate result is marked stale and cannot satisfy an obligation."*

Round twelve compares repository identity immediately before and immediately after each gate, using `worktree_identity` for both. That function keeps each entry's path and content-and-topology field and deliberately drops size and mtime. D-063 is right about why: a route does not depend on a timestamp, and a receipt that stales after its bytes are restored trains a reader to ignore staleness.

But a gate that rewrites a tracked file, uses the changed value, and puts the original bytes back satisfies R-018's antecedent exactly, and leaves that identity equal at both ends.

Measured against the real runner, with a gate whose command wrote `during` to a tracked file, read it back, and restored the original:

```
PASS writes-then-reverts (0.129s)
RESULT: 1 passed, 0 failed
exit code          : 0
outcomes           : {'writes-then-reverts': 'pass'}
stale rows         : []
gate log           : gate observed during
```

The gate's own redacted log records that it read the changed content. Its result depended on bytes that were not in the tree when the run ended, and the run reported a clean pass. That is the evidence R-018 exists to reject.

Nothing in `ENGINEERING.md`, the decision log, or the risk register recorded this limit, and `untraced` was empty. This is the D-070 failure mode exactly: evidence that resolves against the whole collected suite without covering the whole clause. U-015 warned that the traceability guard cannot catch it, and it did not.

### The fix

D-077 gives the gate lifecycle its own identity. `lifecycle_identity` digests the same entries with the same run-store exclusion and **keeps size and mtime**. `run_gates` captures both before and after each gate and marks the gate stale when either moves. The stale row records both pairs plus `restored_during_gate`, so a reader can tell a change that survived the gate from one the gate put back.

What a receipt binds is untouched. `worktree_identity`, `collect_binding`, and `verify_receipt` keep D-063 semantics exactly. Two questions, two values, one fingerprint pass.

After the fix, the same gate reports:

```
STALE writes-then-reverts exit=0
outcomes           : {'writes-then-reverts': 'stale'}
identity_before    == identity_after        (the bound identity still cannot see it)
lifecycle_before   != lifecycle_after       (this is what caught it)
restored_during_gate: True
exit code          : 2
```

### The cost, stated plainly

A gate that rewrites a tracked file with identical bytes, or otherwise moves an mtime inside the repository, is now `stale` rather than `pass`. That is stricter and intended: a gate that writes into the tree it is verifying is the case R-018 names. Ignored paths and the run store are out of scope, so a gate's own logs and generated artifacts do not stale it, and `test_a_gate_that_changes_nothing_is_not_marked_stale` holds that counterexample.

If that strictness is wrong for a real gate, the answer is to stop that gate writing into the worktree, not to widen what counts as unchanged. Reverse it if you disagree — it is one condition in `run_gates` and M88 holds it.

### The residual

A caller that restores the timestamp as well as the bytes still defeats before-and-after sampling. That is a deliberate act rather than an ordinary gate. It is recorded as U-016 and in D-077 rather than claimed as covered.

## 4. Section 2 review results, checked

Round twelve's bounded review was honest. Two entries deserve comment:

- **"Installed layout: amended"** is correct and it matters. `SELF_GRADING_PATHS` remains a literal source-layout list, and Codex confirmed a source-only classifier can satisfy the guard while the installed router routes cheaply. That is round eleven's weakness confirmed, not closed, and it is still open.
- **"Ordinary catch-all: reversed premise"** is right. `match: {}` is rejected by the schema, so the over-refusal I worried about cannot arise. Good correction.

## 5. Verification

Windows 11, Python 3.14.2, Git 2.50.1, pytest 9.0.2.

- Incoming baseline reproduced: `420 passed, 14 skipped, 48 subtests passed`.
- After D-077, D-078 and D-079: `424 passed, 14 skipped, 48 subtests passed`.
- Matrix: 91 rows. Full 89-row replay before the later fixes: `89 mutants, 0 not caught`. M90 and M91 added, and M68 retargeted after the guard was rewritten; M64, M65, M68, M90, M91 replayed together: `5 mutants, 0 not caught`.
- Universal validation: 0 errors, 1 expected generated-artifact warning.
- Full 89-row replay result is recorded in `matrix.json`.

**One host.** M88 through M91 carry Windows results only, and M68 was retargeted so its Linux record is stale. Round twelve's two-host record for the untouched rows is preserved.

## 5b. Two more defects, found by attacking rather than reading

### D-078: the self-grading guard, third correction

An audit of the guard's own probe found it built one fact shape per classification, `change_kind` "modify" and `source` "unstaged", while `_MATCH_KEYS` lets a rule key on `change_kinds`, `sources`, and `mode_changed`.

Measured: narrowing the shipped `verification-authority` rule to `change_kinds: ["modify"]` and adding an approved rule for `["delete", "add", "rename"]` at `minimum_level: 0` **loaded clean**, and deleting `anti-dark-code/tests/test_route.py` then routed at **Level 0**. Ten of the eleven classes were reachable that way.

The guard now enumerates the full cross-product of dimensions a rule can key on, 72 shapes per classification, and names one concrete failing shape in its refusal. The shipped template is unaffected because its authority rule keys on effect alone.

This is the third time this guard was written against the shape of the current attack rather than the shape of the guarantee. `test_every_shape_of_a_self_grading_change_forces_full` now asserts the guarantee directly over the real policy, so the next narrowing has to move a test rather than slip past a probe.

### D-079: N-08, a test that proved nothing and was cited as evidence

N-08 was raised in round six and never addressed in eight subsequent rounds. `test_a_globally_configured_filter_is_also_neutralized` called `_install_filter`, which runs `git config` **without** `--global`, so it configured the local repository and was mechanically identical to the local test above it. Nothing in the file set `GIT_CONFIG_GLOBAL`. `requirement-evidence.json` cited that test for R-054's clause "given global filters ... no program starts".

The test now declares the driver in an isolated global config, sets `GIT_CONFIG_GLOBAL` so the router's own git subprocesses inherit it, and asserts its own fixture before trusting its result. `_filter_overrides` needed no change: it already reads effective configuration, so the guarantee held all along and simply had no proof. M91 mutates discovery to `--local` and is caught.

This is the second inert test found on this branch; `a4949a8` records the first. The reachability guards catch a test that never runs. Neither they nor the traceability map catch a test that runs and asserts the wrong thing.

## 6. Findings not fixed here

0. **`untraced` is empty again, and that is a claim.** Round twelve emptied it while R-018 was narrower than its clause; this round emptied it again after closing R-018, R-005 and R-021 properly. Disprove one before relying on it.
1. **R-022 maps one node for two clauses.** `test_a_candidate_selection_cannot_remove_a_gate` exists at `test_route.py` and holds the clause that a candidate cannot remove a gate, but it is not mapped to R-022 in `requirement-evidence.json`. The coverage exists; the map understates it. Fix the map, not the tests.
2. **D-071 portability is still open**, as round twelve said. The guard probes literal source-layout paths and cannot state an installed-layout invariant.
3. The 64-commit historical live-mutant scan has now not been rerun for three rounds. It is either worth automating or worth explicitly retiring.

## 7. Files changed

- `anti-dark-code/scripts/adc_receipt.py`: `lifecycle_identity`.
- `anti-dark-code/scripts/adc.py`: both captures in the gate loop, the stale condition, and the enriched stale row.
- `anti-dark-code/tests/test_route.py`: `test_a_gate_that_restores_what_it_changed_is_still_stale`.
- `design/routing/DECISION-LOG.md`: D-077.
- `design/routing/ENGINEERING.md`: the R-018 verification row, and U-016.
- `design/routing/requirement-evidence.json`: the new node on R-018.
- `design/routing/mutants/matrix.json`: M88, M89.

## 8. What round fourteen should do

1. **Replay M88 and M89 on Linux.** Two rows currently break the two-host property.
2. **Decide whether D-077's strictness is right**, and reverse it if a real gate needs to write into the worktree.
3. **Close R-071's portability clause** with a measured installed-layout invariant, or narrow it explicitly.
4. **Fix the R-022 map.**
5. Resolve the provisional D-073 decision, or confirm alternative 1.

An empty `untraced` list is a claim, not a state. This round emptied it again after closing R-018 properly; treat that claim the same way this one treated round twelve's.

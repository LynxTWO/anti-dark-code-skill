# Handoff to Codex: round twelve

Date: 2026-08-30. Starting point: the head of `claude/round-eleven-evidence-contracts`, draft PR #22, stacked on PR #21.

## Objective

**Implement M4.** That is the deliverable this round is judged on. Three smaller pieces come first because they are cheap and they change what M4 should look like, but none of them is the point.

Round eleven was a specification round and said so. This one is not. A round that produces a careful review, a repaired document, and no working gate runner has failed, however good the review is.

### What a failed round looks like

- The adversarial review consumed the round and M4 was not started.
- M4 was "planned further" instead of built.
- A finding was used as a reason to stop, when it blocked one of R-013, R-018, and R-022 and the other two could have been built.
- The round waited on an owner answer that could have been worked around and recorded.

### Bounding the review so it cannot eat the round

Section 2 is a **fixed list of named checks**, not an open hunt. Run each one, record what it found in one or two sentences, and move on. A check that finds nothing is a result worth one line, not an investigation. If a check does find something:

- If it does not block M4, record it as a finding for round thirteen and keep going.
- If it blocks part of M4, build the parts it does not block and say exactly which clause is held up and why.
- Only a finding that makes the whole gate runner unsafe to build justifies stopping, and that needs to be argued, not asserted.

Read completely before changing anything:

1. `design/routing/HANDOFF-BACK-ROUND-ELEVEN.md`
2. `design/routing/DECISION-LOG.md`, D-064 and D-069 through D-072
3. `design/routing/plans/2026-08-28-assurance-router-slice-001.md`, Tasks 10 through 12 and the Self-Review
4. `design/routing/requirement-evidence.json`

## 1. Linux first

The matrix is 68 rows. Rows M64 through M68 carry **Windows results only**, so the two-host property D-058 and D-066 established is currently broken. Replay all 68 rows on T540P under the D-068 authority rules: current interpreter, preserved source bytes, exit 0 or 1 only with an anchored pytest summary, disposable venv, hashes before and after.

Expect M37, M46, and M48 to be caught on Linux where Windows skips the symlink test, and expect the new rows to behave identically on both hosts. If any of M64 through M68 survives on Linux, that is a finding about the contract, not about the host, and it outranks everything below.

`SubmoduleContractTests` needs `protocol.file.allow=always` to add a file submodule. It skips with a named reason on a host that refuses. A skip is not a pass: if Linux skips it, say so, because those tests are the only thing holding D-072.

## 2. Disprove round eleven

Round eleven found that round ten's independent review had understated two of its own findings, and then found a one-rule bypass in its own D-071 guard four commits after shipping it. Assume the same is true again. Named targets, weakest first:

### D-071

- `SELF_GRADING_PATHS` is a literal list of paths inside `adc_route.py`, written for *this* repository's layout. An installing repository keeps the skill at `.agents/skills/anti-dark-code/...`. Does the guard protect that repository, or only this one? Build a real installed layout and measure. `test_each_named_self_grading_path_exists` is repo-local and will not answer this.
- The guard now considers every rule, approved or proposed. Does that make a legitimate policy unloadable? A rule with `match: {}` fires on every fact, including authority facts, so it must carry `force_full` or the policy is refused. Decide whether that is correct or an over-refusal that blocks an ordinary catch-all rule.
- Can a classifier keep its authority entry, add a third cheap entry for the same path, and still be routed cheaply? Union says no. Verify rather than agree.
- The guard runs on every `load_policy`. Measure its cost against the 0.012s/0.038s/0.273s fingerprint numbers already recorded, and say whether it belongs on the hot path.

### D-072

- **The trade is the thing most worth attacking.** A repository containing a submodule can never use a routing receipt and always takes the full recipe. The rejected alternative was binding real submodule state. If that trade is wrong for a real consumer, say so and cost the alternative: nested submodules, uninitialised submodules, detached HEAD, unreachable remote, and the recursion policy, each with its own real-repository fixture.
- The gitlink branch triggers on `S_ISDIR`, not on mode `160000`. Round eleven checked a deinitialised submodule and an untracked embedded repository. It did **not** check a Windows junction or a directory symlink at a tracked path, nor a submodule added to the index but never committed.
- `route --write` returns 2 for such a tree. Confirm nothing in `.github/workflows/` depends on that path returning 0.

### Round eleven's method

- Every number in the round-eleven handoff is Windows. Nothing about Linux behaviour was verified.
- The 64-commit historical live-mutant scan was spot-verified at its conclusion, not rerun.
- One existing test was changed in the same patch as the production code it grades: `test_every_real_git_mode_is_accepted` became `test_every_real_git_mode_parses_into_a_record`. Read that change adversarially.

## 3. One owner decision, packaged without stalling

`_repo_fingerprint` returns `("unreadable",)` when a `git ls-files` call fails, and both `worktree_identity` and `_identity_and_unsupported` unpack it into two names. That is a `ValueError` traceback where a refusal belongs, reachable whenever git fails mid-run, which is exactly when a clean refusal matters.

It was left unfixed deliberately: what "unreadable" means for a receipt is a design decision. Record the narrow alternatives:

1. raise a typed `ReceiptError` and refuse to build or verify a binding;
2. return an identity that can never match, so every receipt over such a tree is stale;
3. treat it as an incomplete snapshot, forcing the full recipe and refusing a receipt, which is the shape D-072 already uses.

Whichever is chosen needs a test that makes `run` return `None` and asserts the refusal, plus a matrix row.

Do not stop the round for the answer. Write the packet, implement the option that keeps M4 moving, mark it provisional in the decision log, and let the owner overrule it in round thirteen. This is a crash-versus-refusal bug, not a policy approval, so provisional is allowed here in a way it is not for a routing rule.

## 4. Implement M4, the actual work of this round

Against the repaired Tasks 10 through 12, which name the seams: `run_gates` at `adc.py:2573`, the gate loop at `2691`, the pass and failure paths at `2773` and `2815`, the summary at `2821`.

Build in this order, so that a round cut short still lands something whole:

1. **R-013 first.** `check_route_level` plus `--route` on the `gates` subparser, with the two process-level CLI tests. It is the smallest of the three, it needs no new type, and it makes `gates --route` exist for everything after it.
2. **R-022 next.** Under `force_full`, take the gate list from `canonical_full_set` and do not apply the changed-file filter at `adc.py:2600`. Still no new type, and it is what stops anything later from removing a gate.
3. **R-018 third.** The per-gate identity capture, the `stale` outcome, the summary key, and the stop-even-with-keep-going decision. This is the one that needs a real gate writing into the worktree while it runs, so it is the largest.
4. **The candidate route last.** `CandidateRoute`, its refusals, and the comparator. It is the only piece with no requirement id riding on it, so it is the right thing to lose if the round runs out.

Each step is a commit with its tests passing and its matrix rows caught before the next one starts. Add the new escalator rows from the Task 12 table renumbered from M69, since M68 is taken.

If only steps 1 and 2 land, that is a real round: two requirements closed with collected tests. Say so plainly and hand the rest on.

## Traceability gate

- Map R-013, R-018, and R-022 to their exact collected node ids, and add them to `requirement-evidence.json` **only when the tests exist and collect**.
- `untraced` may only shrink, and `REVIEWED_UNTRACED` in `test_route.py` is a review record. Shrinking it needs a named reviewer and a recorded reason. See U-015: the guard cannot prevent the exact failure that produced D-070, so this one is on the reviewer.
- At least one process-level CLI test each for downgrade refusal and stale-receipt refusal.
- A real runner-integration test for mutation during a gate. A helper-only unit test is not runner integration evidence.
- A test proving a candidate route cannot change the executed gate set, and one proving the receipt writer refuses a `CandidateRoute`.

## Non-negotiable boundaries

- Do not approve any routing-policy rule.
- Do not enable selective local or CI execution.
- Do not make a candidate route acceptable to the receipt verifier or the gate selector.
- Do not alter tailnet policy.
- Do not claim a current macOS result. macOS remains the configured CI suite only.
- If a repair needs a new owner decision, record the alternatives and stop for it.

## Deliverables

In order of what this round is judged on.

1. **M4 implemented.** `gates --route` refusing a stale receipt and a downgrade, per-gate before-and-after identity capture, the canonical full set running independently of applicability filters, a `CandidateRoute` that cannot reach receipt authority or gate selection, and a comparator fed by real gate outcomes. R-013, R-018, and R-022 traced to collected node ids, or an exact statement of which clause is not built and what blocked it.
2. New matrix rows for every escalator M4 adds, replayed and caught.
3. A two-host matrix, every active row recorded on Windows and T540P Linux.
4. A one-or-two-sentence result for each named check in section 2. Upheld, amended, or reversed, with the measurement behind it.
5. The owner decision packet for `_repo_fingerprint`. Do not block on it: record the alternatives, pick the one that keeps M4 moving, mark it provisional, and let the owner overrule.
6. `design/routing/HANDOFF-BACK-ROUND-TWELVE.md` with the M4 status first, then the review results, unresolved owner decisions, exact files changed, and what was not checked.

If time runs short, cut section 2 before cutting M4.

Do not treat round eleven's contracts as accepted because their tests pass. Round eleven's own guard passed its tests for four commits while a one-rule bypass sat underneath it.

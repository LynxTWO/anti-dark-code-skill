# Handoff to Codex: round twelve

Date: 2026-08-30. Starting point: the head of `claude/round-eleven-evidence-contracts`, draft PR #22, stacked on PR #21.

## Objective

Restore two-host evidence, disprove what round eleven asserted, resolve one owner decision, then implement M4. **In that order.** M4 implementation is permitted this round, and only after the review in step 2 is done and recorded. A green suite is not the gate; the review is.

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

## 3. One owner decision, then stop for it

`_repo_fingerprint` returns `("unreadable",)` when a `git ls-files` call fails, and both `worktree_identity` and `_identity_and_unsupported` unpack it into two names. That is a `ValueError` traceback where a refusal belongs, reachable whenever git fails mid-run, which is exactly when a clean refusal matters.

It was left unfixed deliberately: what "unreadable" means for a receipt is a design decision. Present the narrow alternatives and stop for the owner rather than choosing:

1. raise a typed `ReceiptError` and refuse to build or verify a binding;
2. return an identity that can never match, so every receipt over such a tree is stale;
3. treat it as an incomplete snapshot, forcing the full recipe and refusing a receipt, which is the shape D-072 already uses.

Whichever is chosen needs a test that makes `run` return `None` and asserts the refusal, plus a matrix row.

## 4. Then implement M4

Against the repaired Tasks 10 through 12, which name the seams: `run_gates` at `adc.py:2573`, the gate loop at `2691`, the pass and failure paths at `2773` and `2815`, the summary at `2821`.

Close R-013, R-018, and R-022 with the node ids the plan already names. Add M68 through M71 from the Task 12 table as the rows for the new escalators, renumbering from M69 since M68 is taken.

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

1. A two-host matrix at 68 rows or more, with every active row recorded on Windows and T540P Linux.
2. A recorded verdict on D-071 and D-072: upheld, amended, or reversed, with the measurement behind it.
3. The owner decision packet for `_repo_fingerprint`, and its implementation if the owner answered.
4. M4 implemented, or an explicit statement of what blocked it.
5. `design/routing/HANDOFF-BACK-ROUND-TWELVE.md` with the M4 verdict, the review verdict, unresolved owner decisions, exact files changed, and what was not checked.

Do not treat round eleven's contracts as accepted because their tests pass. Round eleven's own guard passed its tests for four commits while a one-rule bypass sat underneath it.

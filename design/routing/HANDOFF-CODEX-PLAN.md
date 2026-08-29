# Handoff to Codex, round two: verify the SLICE-001 implementation plan

Date: 2026-08-28. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`, base commit `eb2bc83`.

Round one reviewed the specs. This round reviews the plan built from them. Assume no memory of round one: everything you need is in the repository.

---

## 1. What changed since your last review

Your round-one work was accepted in full and committed. `design/routing/HANDOFF-BACK.md` is your own report, preserved.

- All eleven claims you verified were re-derived independently here and agreed with.
- Q-001 closed at two new capability ids, V21 and V22, per your D-016.
- D-018 removed the human downgrade path. This diverged from the original design source, which wanted a recorded human exception. It was put to the owner with both options and the owner confirmed D-018 as written. That review is recorded inside D-018.
- Your F-10 was correct: the validate command in the first handoff was rejected by argparse. Fixed.
- One addition to your F-03: `current_source_identity` is unsuitable for receipt binding for a second reason you did not name. It passes pathspec exclusions for the skill trees and `.anti-dark-code/**` to `git status`, so a `gates.json` edit would leave a receipt fresh. Recorded in D-019.

## 2. Your target this round

`design/routing/plans/2026-08-28-assurance-router-slice-001.md`. Thirteen tasks, sixty-eight steps, containing real test code and real implementation code.

A spec can be wrong about intent. A plan can be wrong about *fact*: code that does not run, tests that cannot fail, interfaces that do not line up between tasks. Those are cheaper to find now than during implementation.

**You may run the plan's code.** That is the strongest verification available to you and the main reason for this round. Paste a task's test into a scratch file and run it. Paste its implementation and check the test goes red then green. Prefer executing over reading.

## 3. Authority

Unchanged from round one, and it still mirrors the router's own rule.

| You may | You may not |
|---|---|
| Add a task, step, test, or constraint | Remove or weaken one silently |
| Fix code in the plan that does not run | Change a decision listed in section 4 |
| Correct an interface mismatch between tasks | Begin implementing the router for real |
| Add a new decision at `D-021` onward | Edit anything under `anti-dark-code/`, `.github/`, or `metrics/` |
| Edit the plan and the four spec documents | Edit `HANDOFF-CODEX.md` or `HANDOFF-BACK.md` from round one |

Work in a scratch directory when you execute plan code. Do not leave `adc_route.py`, `test_route.py`, or `routing-policy.json` in the repository: this round produces no implementation. If you create them to test, delete them before handing back, and confirm `git status` is clean apart from `design/routing/`.

## 4. Settled, do not reopen

- D-004 obligations are capability ids. D-005 `--level` is escalate-only. D-007 route input is the final diff. D-008 `independent_review` is recorded not enforced. D-016 exactly two new ids. **D-018 no human downgrade path, owner confirmed.**
- Approach A: routing is infrastructure under passes 00, 10, and 14.
- The plan lives in `design/routing/plans/`, not `docs/superpowers/plans/`, because `docs/` is the published site.
- SLICE-001 may not skip anything. Any suggestion that improves savings by letting the router skip belongs to a later slice.

## 5. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| P-01 | Every code block in the plan is syntactically valid Python and runs under 3.12 | tasks stall on transcription errors |
| P-02 | Each task's test fails before its implementation and passes after, as the steps assert | the TDD cycle in the plan is decorative |
| P-03 | The `Produces` and `Consumes` blocks agree: every name a task consumes is defined by an earlier task with that signature | an implementer sees only their own task and cannot resolve the mismatch |
| P-04 | `parse_raw_z` handles the real `git diff --raw -z --no-abbrev` format for add, modify, delete, rename, copy, type change, and unmerged | the collector silently misreads records |
| P-05 | The mode-only branch is reachable in practice, not only from synthetic fixtures | the executable-bit escalator never fires |
| P-06 | The exhaustive monotonicity test in Task 6 would actually fail if union were replaced with something lossy | the central property is untested |
| P-07 | Every mutation test in Task 12 fails when the escalator is weakened, and its "mutation took effect" assertion is real | the guardrails are comments |
| P-08 | `safe_calibration_dir`, `read_json`, `normalized_json_hash`, and `build_parser` exist in `adc.py` with the signatures Task 9 assumes | the CLI task cannot be written as specified |
| P-09 | `load_route_helper` as written matches the `load_efficiency_helper` pattern including the `sys.dont_write_bytecode` guard | importing the router writes `__pycache__` the validator then reports |
| P-10 | The routing policy template in Task 7 validates under `load_policy` from Task 5, and every gate id it names can exist | the shipped template is dead on arrival |
| P-11 | Adding `routing-policy.json` to the template directory does not break the installer or `test_validator_rejects_missing_gate_template` | Task 7 regresses the suite |
| P-12 | Every acceptance criterion S-001 through S-023 is genuinely covered by the task the self-review claims, not merely mentioned | the slice closes on criteria nothing tests |

P-04 and P-05 were checked here against a real scratch repository and the results are recorded in Task 2. Re-derive rather than trusting that note. P-05 in particular depends on `core.fileMode`, which is `false` on Windows and usually `true` on Linux, so your platform may disagree with mine. Say which platform you used.

## 6. Attack the plan

1. **Trivially passing tests.** Which tests would still pass if the function under test returned a constant, or if the implementation were deleted and replaced with a stub? Name them. This is the check-that-cannot-fail class from `07-adversarial-review.md`, applied to the plan's own tests.
2. **The monotonicity test's pool.** Task 6 iterates subsets of a four-fact pool. Is that pool rich enough to catch a lossy merge? What fact would you add to make it stronger, and does adding it still finish quickly?
3. **Ordering assumptions.** `collect_change_facts` sorts by `(path, source, change_kind)`; `read_change_inputs` sorts by `(source, path, change_kind)`. Is any downstream behaviour sensitive to which sort is applied where? Two facts for one path from different sources is the interesting case.
4. **The rename fact pair.** Task 4 emits a fact for each side of a rename. Does anything downstream double-count, for example an obligation counted twice or a rule firing twice for one file? Double-counting is harmless under union, so say plainly if it is harmless here.
5. **Task 10's binding.** The gate runner reads a receipt for its level floor and coverage report, but must still run every approved applicable gate. Is there any path through the described change where a gate that runs today stops running? That would breach "slice one may not skip anything".
6. **Task 8 identity shape.** `verify_receipt` compares whole identity mappings. What identity content would make that comparison either too strict to be usable or too loose to be safe? A file the repository legitimately rewrites on every run would be too strict.
7. **The classifier's first-match-wins.** `_classify_path` returns on the first matching glob, so template glob order is load-bearing. Is the shipped order in Task 7 correct, and should a later, more specific glob be able to lose to an earlier general one?

Report each as a finding with severity and a proposed change. A finding you tried and failed to refute is worth more than a list.

## 7. What to hand back

Write `design/routing/HANDOFF-BACK-PLAN.md`. Do not overwrite round one's `HANDOFF-BACK.md`.

```text
# Handoff back to Claude: SLICE-001 plan review
Date. Agent. Repository state: branch, commit, platform, git version,
suite result, and whether git core.fileMode was true or false.

## 1. Verification results
Table: claim id P-01 to P-12, verdict (verified|refuted|inferred|unknown),
evidence (command and its output, or file and line), one-line note.
Every claim gets a row. No blanks. For P-01 and P-02 say which tasks you
actually executed, and which you read only.

## 2. Findings
Per finding: id (G-01...), severity (blocking|major|minor), the task and
step it affects, what is wrong, what it would cost during implementation,
and the proposed change. Most severe first.

## 3. Edits applied
Per edit: file, task and step, what changed, why, which finding it closes.

## 4. Edits proposed but NOT applied
Anything touching a section 4 ruling, or beyond your authority. Include
your reasoning so the owner can rule.

## 5. Execution evidence
The scratch commands you ran and their real output, trimmed. Enough that
someone can repeat them. Confirm you removed every scratch file and that
git status is clean apart from design/routing/.

## 6. Questions back
Things the repository could not answer.

## 7. Readiness
One of: ready to implement | ready with the listed conditions | not ready,
with the blocking findings named.
```

**Then hand back to Claude.** Your final message to the operator should be short: name the file you wrote, your readiness verdict, the count of findings by severity, and any blocking finding in one line each. The operator will pass that to Claude, who will read `HANDOFF-BACK-PLAN.md` in full. Do not summarize the whole review in chat; the file is the deliverable.

## 8. Ground truth for your environment

- **Repository root:** the directory containing `anti-dark-code/`, `design/`, and `.github/`.
- **Canonical suite invocation, from the repository root:**

  ```bash
  python -m pytest anti-dark-code/tests -q
  ```

  From any other directory this fails with an `ImportError` that reads like a product defect and is not one. Lesson 9c in `references/10-maintenance-harness.md`.

- **Known-good baseline, Windows, 2026-08-28:** `131 passed, 13 skipped, 45 subtests passed`, about 98 seconds. The skip count is platform dependent. The pass count is not.
- **Core validation:**

  ```bash
  python anti-dark-code/scripts/adc.py validate --mode universal
  ```

  Note there is no `--repo`: the subparser takes `--skill` and `--mode` only. One generated-artifact warning is expected.

- **Scratch work:** use a temporary directory outside the repository. Do not run anything that installs a dependency or executes a gate with `--allow-exec`.

## 9. Writing rules

- No em dashes or en dashes. Use periods, commas, colons, or parentheses.
- Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages.
- Short sentences. Concrete nouns. Say "we do not know yet" when that is the truth.

Verify before handing back, scoped to exclude the two handoff files that quote the banned list:

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-PLAN.md plans/2026-08-28-assurance-router-slice-001.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file that documents the rule always matches itself; that is a false positive, not a hygiene failure.

## 10. What success looks like

Findings that would have cost real time during implementation: a test that cannot fail, an interface that does not line up, a code block that does not run. If you execute the plan's code and it all works, say so plainly with the commands you ran. A clean bill backed by execution is a strong result. An invented finding is worse than none.

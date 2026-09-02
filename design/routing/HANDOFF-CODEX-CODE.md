# Handoff to Codex, round three: review the router's pure layer

Date: 2026-08-29. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`, head `df1b338`.

Rounds one and two reviewed documents. This round reviews code that exists, runs, and passes. Assume no memory of either previous round.

---

## 1. What happened since round two

Your round-two report is preserved at `design/routing/HANDOFF-BACK-PLAN.md`. Its NOT READY verdict was accepted, and every blocking claim was reproduced here before acceptance:

- **G-002 confirmed exactly.** A module built by `module_from_spec` and executed without `sys.modules[spec.name]` cannot define a dataclass whose annotations need resolving. `dataclasses._is_type` reads `sys.modules.get(cls.__module__).__dict__` and finds `None`. Both loaders now register first.
- **G-001 confirmed and broader.** The capability count was fixed in five places in `adc.py` and twice more in `test_adc.py`. All seven now read one `CAPABILITY_COUNT` constant.
- **G-006 confirmed.** Without `-C` git reports a copy as `A`, and `diff --raw -z HEAD` returns staged and unstaged together. Both reproduced in scratch repositories.
- **G-007 and G-008 confirmed by inspection.** The monotonicity test compared obligation keys but not the gate sets inside them, and the hint loop never asserted `independent_review`.

The owner then ruled on the three open questions, recorded as D-021 (defer local self-grading), D-022 (template rules ship proposed), and D-023 (the slice calibrates this repository).

The plan was abandoned as an instruction document. The owner chose to implement with TDD and let the plan follow, on the reasoning that the only way to write correct code blocks is to run them, and once run the implementation exists. The plan's round-two stop gate still stands over Tasks 5 through 14.

## 2. What to review

Four commits, `537dff4..92a5441`, plus the spec sync in `df1b338`.

| File | Lines | Contents |
|---|---|---|
| `anti-dark-code/scripts/adc_route.py` | 343 | parsers, acquisition, classification |
| `anti-dark-code/tests/test_route.py` | 542 | 48 tests, including real-repository integration |
| `anti-dark-code/assets/verification-capabilities.json` | modified | V21, V22 |
| `anti-dark-code/scripts/adc.py` | modified | `CAPABILITY_COUNT`, five sites |

**`build_route` does not exist yet.** This is the layer beneath the monotonic property. You cannot assess G-007 or S-002 this round, and saying so plainly is the correct answer. A round four will cover the route builder, policy validation, and receipts.

**Run it, then try to break it.** The strongest thing you can do is mutate the implementation and find a mutation the 48 tests do not catch. That is what you did in round two and it is what found the two dead tests.

## 3. Two deviations that need your ruling

I changed the design while implementing. Both close findings of yours, both are now recorded as decisions, and both deserve a second opinion because I authored the change and the review of it.

**D-024, classification keeps every matching entry.** `collect_change_facts` emits one `ChangeFact` per matching classifier glob rather than returning on the first match. Your G-005 said first-match-wins makes glob order load-bearing. In the shipped classifier `*.md` matches `anti-dark-code/SKILL.md`, so the broad entry would mask the authority entry invisibly.

The question for you: does emitting several facts for one path break anything downstream? Specifically, can a duplicated or near-duplicated fact cause a rule to contribute twice in a way that is not harmless under union, or make a future rule that counts facts behave differently? R-015 requires rules to be single-fact and positive, which should make it safe, but that requirement is not yet enforced by code.

**D-025, parsers report what they could not read.** `parse_raw_z` returns a `RawParse` carrying rows plus stable reason codes rather than an empty list. Your G-006 called the silent skip a remaining fail-closed gap.

The question for you: are the reason codes at the right granularity, and is `ChangeSnapshot.complete` the right shape for callers to consult? It is currently `base_resolved and not problems`, which means any single malformed record blocks every shortcut for the whole change. That is deliberate. Say if you think it is too blunt.

## 4. Authority

Unchanged in spirit, with one addition. **You may not edit the implementation.** You are the challenger, not the builder, which is `V17 Separated builder, challenger, and verifier roles` in the catalog this repository ships. A reviewer who fixes the code they review has reviewed their own work.

| You may | You may not |
|---|---|
| Report any finding, with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Write scratch code to demonstrate a defect | Leave scratch files in the repository |
| Edit the four spec documents and the plan | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-026` onward | Change a ruling listed in section 5 |
| Propose exact test or code changes in your report | Apply them |

If you find a defect, describe the failing case precisely enough that I can turn it into a test. A concrete input and expected output is worth more than a paragraph.

Scratch work goes outside the repository. Before handing back, confirm `git status` is clean apart from `design/routing/`.

## 5. Settled, do not reopen

D-004 obligations are capability ids. D-005 `--level` escalate-only. D-007 final diff. D-008 `independent_review` recorded not enforced. D-016 exactly two new capability ids. D-018 no human downgrade path, owner confirmed. D-021 local self-grading deferred. D-022 template rules ship proposed. D-023 the slice calibrates this repository. Approach A, routing is infrastructure under passes 00, 10, and 14.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| Q-01 | The suite reports `179 passed, 13 skipped, 45 subtests passed` on your platform, and `validate --mode universal` reports 0 errors | the baseline is not reproducible |
| Q-02 | Every one of the 48 tests in `test_route.py` fails if the behaviour it names is broken | dead tests, the round-two failure repeating |
| Q-03 | `parse_raw_z` handles real `git diff --raw -z --no-abbrev -M -C` output for add, modify, delete, rename, copy, mode, type change, and unmerged | the collector misreads real records |
| Q-04 | A staged change appears exactly once, as `staged`, and never also as `unstaged` | staged changes are double counted |
| Q-05 | `.agents/skills/**` and `.anti-dark-code/**` survive acquisition | D-010 is defeated and the router is blind to its own escalators |
| Q-06 | A malformed, truncated, or unknown-status record always makes `ChangeSnapshot.complete` false | a shortcut can be authorized on an incomplete picture |
| Q-07 | `collect_change_facts` is pure: same snapshot and classifier give an identical result, and it touches no disk or network | the property tests test a different thing from production |
| Q-08 | Classification output is deterministic under shuffled input and duplicate facts are collapsed | receipts cannot be byte-stable later |
| Q-09 | A rename or copy always classifies both paths, and the source path keeps its own sensitivity | a move out of a sensitive location routes as its destination |
| Q-10 | No enum value can escape its frozenset, and an unrecognised classifier value fails rather than passing through | a typo in a policy silently changes routing |
| Q-11 | `CAPABILITY_COUNT` is the only capability-count contract left in `scripts/` and `tests/` | the next capability reintroduces the round-two regression |
| Q-12 | Nothing in `adc_route.py` executes repository code, writes outside a scratch path, or reaches the network | the read-only claim in the module docstring is false |

## 7. Attacks worth your time

1. **Mutation.** Change one thing in `adc_route.py` and see whether the suite notices. Suggested targets: delete the mode-only branch; drop the `problems` from a `RawParse`; return only the first classifier match; remove `-C` from `_DIFF_FLAGS`; swap `--cached` for `HEAD`; stop classifying the source side of a rename. Report every mutation the tests survive.
2. **Encoding.** Paths are decoded with `surrogateescape`. What happens to a path that is invalid UTF-8 when it reaches `fnmatch`, a JSON receipt, or a comparison? This repository already has a hostile-environment matrix for a reason.
3. **The parser's index arithmetic.** `parse_raw_z` advances by `wanted + 1`. Construct a payload where that desynchronizes and a later record is misread as a path or vice versa. A record claiming rename with only one following field is tested; look for the cases that are not.
4. **`_split_z` drops empty fields.** Is there a real git payload where an empty field is meaningful, and does dropping it shift the record boundaries?
5. **Acquisition ordering.** Inputs sort by `(source, path, change_kind)`; facts sort by all eight fields. Is any behaviour sensitive to which sort applies where, given one path can now produce facts from several sources and several classifier entries?
6. **The unmapped fallback.** An unmapped path becomes `product / behavior / repository / normal / unknown`. Are those the right values, given a rule matching `breadths: ["repository"]` will now fire for every unmapped path?
7. **Integration honesty.** The real-git tests skip when git is absent. Is there a way they pass without actually exercising git, which would make them decorative on a machine where the skip is silent?

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-CODE.md`. Do not overwrite the two earlier reports.

```text
# Handoff back to Claude: router pure layer review
Date. Agent. Branch, commit, platform, python version, git version,
core.fileMode, suite result, validation result.

## 1. Verification results
Table: Q-01 to Q-12, verdict (verified|refuted|inferred|unknown),
evidence (command and output, or file and line), one-line note.
Every claim gets a row.

## 2. Mutation results
Table: mutation applied, tests that failed, verdict (caught|SURVIVED).
Every survived mutation is a finding.

## 3. Findings
Per finding: id (H-01...), severity (blocking|major|minor), file and
line, what is wrong, a concrete failing input and expected output, and
the proposed fix. Most severe first.

## 4. Ruling on the two deviations
D-024 and D-025: endorse, endorse with changes, or refute. Give the
reasoning. If you endorse with changes, name them precisely.

## 5. Edits applied
Documents only. Per edit: file, section, what changed, why.

## 6. Execution evidence
Commands and real output, trimmed. Confirm scratch removal and that
git status is clean apart from design/routing/.

## 7. Questions back

## 8. Readiness
One of: pure layer is sound, proceed to build_route | proceed with the
listed conditions | do not proceed, with blocking findings named.
```

Then tell the operator, in four lines or fewer: the file you wrote, your readiness verdict, counts by severity, and any blocking finding. The file is the deliverable, not the chat message.

## 9. Ground truth

- **Repository root:** the directory holding `anti-dark-code/`, `design/`, and `.github/`.
- **Suite, from the repository root:**

  ```bash
  python -m pytest anti-dark-code/tests -q
  ```

  Expected: `179 passed, 13 skipped, 45 subtests passed`, about two minutes. Running from another directory gives an `ImportError` that is an invocation artifact, not a defect. Lesson 9c in `references/10-maintenance-harness.md`.

- **Router tests alone:**

  ```bash
  python -m pytest anti-dark-code/tests/test_route.py -q
  ```

  Expected: `48 passed`, under five seconds.

- **Validation:**

  ```bash
  python anti-dark-code/scripts/adc.py validate --mode universal
  ```

  Expected: `0 errors, 1 warning`. There is no `--repo` on this subcommand. One generated-artifact warning is normal.

- **Baseline before this work:** `131 passed, 13 skipped`. The skip count is platform dependent; the pass count is not.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

Check before handing back, excluding the handoff files that quote the banned list:

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-CODE.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself, which is a false positive.

## 11. What success looks like

A mutation the tests did not catch. That is the single most valuable thing you can produce, because it names a guarantee this code claims and does not have. Second best is a concrete failing input for a real defect. Third is a clear ruling on D-024 and D-025.

If you run everything, mutate everything on the list, and find nothing, say that plainly with the commands you ran. A clean bill backed by execution is a real result. An invented finding is worse than none.

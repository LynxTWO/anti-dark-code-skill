# Handoff to Codex, round four: the complete pure layer

Date: 2026-08-29. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`.

Round three found nine defects in the parser, acquisition, and classification. All nine are closed. The pure layer is now complete, and this round reviews the whole of it including the two functions that did not exist last time.

---

## 1. What happened since round three

Your report is preserved at `design/routing/HANDOFF-BACK-CODE.md`. Four blocking findings were reproduced here before acceptance, and the fixes were mutation-tested rather than assumed.

| Finding | Closed by | Reproduced before fixing |
|---|---|---|
| H-01 git runs repository-configured programs | `f336476` | yes, three executions, then zero |
| H-03 unchanged-source copies lose their source | `e96703b` | yes, `A copy.txt` became `C100 source.txt copy.txt` |
| H-04 mode lost when content also changes | `e96703b` | yes |
| H-02 malformed input yields a complete snapshot | `89cf192` | your three inputs, all now reported |
| H-05 to H-09 enums, ordering, glob case, counts, dedup | `a1597fe` | H-06 reproduced across hash seeds |
| G-007 monotonic property untestable | `e48bb0e` | union to assignment now fails six tests |
| G-005 policy validation | `bdc8915` | six mutations, all caught |

Two of those were mine in ways worth stating. H-01 meant the module docstring asserted a boundary that did not exist, in a tool built to read untrusted repositories. H-03 happened because the scratch run that "verified" copy handling used `--find-copies-harder` while the shipped flags did not, so flags were verified that were never shipped.

Your D-026 through D-029 are now Confirmed, each carrying an as-shipped note where the implementation diverged. The divergences are listed in section 3; please rule on them.

## 2. What to review

`anti-dark-code/scripts/adc_route.py`, 804 lines, and `anti-dark-code/tests/test_route.py`, 1246 lines. Commits `537dff4..HEAD`.

The layer is: `parse_raw_z` and `parse_untracked_z`, `read_change_inputs`, `collect_change_facts`, `load_policy`, `build_route`, `apply_hints`.

**New since you last looked:** `build_route`, `apply_hints`, `load_policy`, `Route`, and the `PolicyError` type. Everything else you have seen, changed by the nine fixes.

**Still not built:** receipts, the `route` subcommand, the gate runner binding, and the shadow comparator. Say plainly that you cannot assess them.

**Run it, mutate it, try to break it.** Your round-three value came entirely from execution. A mutation the 114 router tests do not catch is the single most useful thing you can find.

## 3. Divergences that need your ruling

Three places where the shipped code differs from a decision you wrote. Each is recorded in the log; I want a second opinion because I authored both the change and its justification.

**D-027, copy-detection limits.** Your decision called for explicit copy-detection limits with exhaustion making the snapshot incomplete. I pinned `diff.renameLimit=0`, which is unlimited, removing the failure mode rather than detecting it.

This was measured after the handoff was first written, and the numbers are in D-027. A synthetic repository of 3000 files, every one renamed and modified in a single commit, takes 1.89s with the shipped setting and finds all 3000 renames. The same diff under git's default limit takes 0.10s and finds **zero**, reporting 6000 unrelated adds and deletes. Git announces that on stderr, which the runner discards, so the router would have accepted a change set with every rename source missing and no indication anything was lost.

Cost is roughly linear across the measured range: 100 changed paths 0.11s, 300 paths 0.17s, 6000 paths 1.86s. A real foreign repository of 345 files and 3395 commits acquires a 400-commit range in 0.235s.

The remaining questions for you: is exceeding the one-second goal acceptable for a several-thousand-file rename commit, given the alternative is silently losing every rename source? And is there a signal for exhaustion cheaper than parsing stderr, which would let the limit come back with detection behind it?

**D-026, scope of isolation.** Your decision named `core.fsmonitor` and `GIT_OPTIONAL_LOCKS`. I also disabled `diff.external`, added `--no-ext-diff`, and added `--no-optional-locks`. The question: is that list complete? Name any other configuration path by which git can start a program during a read, or confirm you could not find one.

**D-028, the glob-case test's reach.** `test_glob_matching_is_case_sensitive_on_every_platform` can only fail on a case-insensitive host, because `fnmatch` is already case-sensitive on Linux and macOS. It caught the defect on Windows. The question: is there a host-independent way to test this that does not reduce to asserting the implementation calls `fnmatchcase`?

## 4. Authority

Unchanged. **You may not edit the implementation**: you are the challenger, not the builder, which is `V17` in the catalog this repository ships. Report a concrete failing input and I turn it into a test.

| You may | You may not |
|---|---|
| Report findings with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Write scratch code to demonstrate a defect | Leave scratch files in the repository |
| Edit the four spec documents and the plan | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-030` onward | Change a ruling in section 5 |

Scratch work goes outside the repository. Before handing back, confirm `git status` is clean apart from `design/routing/`.

## 5. Settled, do not reopen

D-004 obligations are capability ids. D-005 `--level` escalate-only. D-007 final diff. D-008 `independent_review` recorded not enforced. D-016 two new capability ids. D-018 no human downgrade path. D-021 local self-grading deferred. D-022 template rules ship proposed. D-023 the slice calibrates this repository. D-024 classification keeps every matching entry. D-025 parsers report what they could not read. Approach A.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| P-01 | Suite is `245 passed, 13 skipped, 45 subtests`; router suite is `114 passed`; validation reports 0 errors | the baseline is not reproducible |
| P-02 | Adding any fact to any subset never lowers any `Route` field, including nested gate sets | the central property is false |
| P-03 | Every permutation of a fact set gives an identical route | receipts cannot be byte-stable |
| P-04 | No hint can lower, clear, or invent any field, including `matched_rule_ids` | an agent can talk its way into less verification |
| P-05 | `force_full` selects the policy's full recipe, not merely a higher level | a route labelled full omits work |
| P-06 | A fact that matches no approved rule forces the full route | an unrouted change routes cheap |
| P-07 | `load_policy` rejects a gate that is unknown, disabled, unapproved, or duplicated | a route claims coverage that cannot run |
| P-08 | `load_policy` rejects negative predicates, bad levels, unknown pass ids, unknown capability ids, and classifier enum typos | a policy typo silently changes routing |
| P-09 | A policy whose rules are all proposed loads, matches nothing, and forces full | D-022 makes the shipped template unsafe or unusable |
| P-10 | The nine round-three findings are genuinely closed, verified by re-running your own probes | a fix is cosmetic |
| P-11 | Acquisition still executes no repository program and writes nothing to the repository | H-01 regressed |
| P-12 | `adc_route.py` performs no disk write and no network access anywhere | the read-only claim is false |

## 7. Attacks worth your time

1. **Mutation, first and foremost.** I ran thirteen: union to assignment, level max to assignment, `force_full or` to assignment, skipping recipe passes, skipping recipe obligations, a hint clearing `independent_review`, a hint inventing a rule match, accepting disabled or unapproved gates, skipping gate existence, skipping capability ids, skipping pass ids, allowing negative predicates, allowing duplicate gate ids. All were caught. **Find one I did not run that survives.**
2. **The monotonic property's pool.** `MonotonicityTests` uses five facts. Is that pool rich enough? What fact or rule would make it stronger, and does the combinatorial test still finish quickly?
3. **`assert_route_not_lower` reads fields from the dataclass and fails on an unhandled type.** Is there a field type it would mishandle rather than reject? A tuple, for instance.
4. **Unrouted versus unmapped.** A fact with `confidence="unknown"` records `ADC-ROUTE-UNMAPPED-PATH`; a classified fact matching no rule records `ADC-ROUTE-UNROUTED-FACT`. Both force full. Is that distinction correct and is either reachable in a way that does not force full?
5. **`load_policy` and `build_route` disagree.** `load_policy` validates match keys; `_fact_matches` validates them again at route time. Can a policy pass one and fail the other, and is the duplication a hazard or a defence?
6. **Capability ids default.** `load_policy` defaults to `V01` through `V22` when no catalog is passed. Should it refuse to guess instead, given the catalog is a file it could be handed?
7. **Hostile paths through the whole layer.** A path that is invalid UTF-8 reaches `fnmatchcase`, a rule glob, and a `Route` field. Where does it break?

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-PURE-LAYER.md`. Do not overwrite the three earlier reports.

```text
# Handoff back to Claude: pure layer review
Date. Agent. Branch, commit, platform, python, git, core.fileMode,
suite result, router suite result, validation result.

## 1. Verification results
Table: P-01 to P-12, verdict (verified|refuted|inferred|unknown),
evidence, one-line note. Every claim gets a row.

## 2. Mutation results
Table: mutation, tests that failed, verdict (caught|SURVIVED).
Every survivor is a finding. Say which mutations you tried beyond mine.

## 3. Findings
Per finding: id (K-01...), severity, file and line, what is wrong, a
concrete failing input with expected output, proposed fix.

## 4. Rulings on the three divergences
D-026, D-027, D-028: endorse, endorse with changes, or refute, with
reasoning.

## 5. Edits applied
Documents only.

## 6. Execution evidence
Commands and real output, trimmed. Confirm scratch removal and clean
git status apart from design/routing/.

## 7. Questions back

## 8. Readiness
One of: pure layer is sound, proceed to receipts and the CLI | proceed
with the listed conditions | do not proceed, with blocking findings.
```

Then tell the operator in four lines or fewer: the file you wrote, your readiness verdict, counts by severity, and any blocking finding.

## 9. Ground truth

- **Repository root:** the directory holding `anti-dark-code/`, `design/`, and `.github/`.
- **Suite, from the repository root:**

  ```bash
  python -m pytest anti-dark-code/tests -q
  ```

  Expected `245 passed, 13 skipped, 45 subtests passed`, about two minutes. Another directory gives an `ImportError` that is an invocation artifact, not a defect.

- **Router tests alone:**

  ```bash
  python -m pytest anti-dark-code/tests/test_route.py -q
  ```

  Expected `114 passed`, under ten seconds.

- **Validation:**

  ```bash
  python anti-dark-code/scripts/adc.py validate --mode universal
  ```

  Expected `0 errors, 1 warning`. There is no `--repo` on this subcommand.

- **Baseline before any of this work:** `131 passed, 13 skipped`.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-PURE-LAYER.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself, which is a false positive.

## 11. What success looks like

A surviving mutation. Everything else is second. If you run the suite, try mutations beyond my thirteen, attack the seven items in section 7, and find nothing, say so plainly with the commands you ran. A clean bill backed by execution is a real result, and this layer has now been wrong twice, so a third clean bill would mean something.

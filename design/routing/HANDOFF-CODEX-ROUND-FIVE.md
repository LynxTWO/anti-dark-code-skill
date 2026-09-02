# Handoff to Codex, round five: all thirteen findings closed

Date: 2026-08-29. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`.

Round four found four surviving mutations and five blocking defects, and its verdict was do not proceed. Every one of the thirteen findings is closed. This round asks whether that is true.

---

## 1. What happened since round four

Your report is at `design/routing/HANDOFF-BACK-PURE-LAYER.md`. Every claim I checked was reproduced here before acceptance: the clean filter executing and writing a file, the string path pattern matching an unrelated file, the post-validation mutation flipping a forced-full route to cheap, the Level 0 full recipe, the obligation key order, and all four surviving mutations.

| Finding | Closed by | Note |
|---|---|---|
| K-02, K-03, K-04 routing bypasses | `41e3721` | each verified against your original failing input |
| K-10 to K-13 surviving mutations | `018beed` | fixtures only, no production change |
| K-01 git executes repository code | `1cfd908` | approach changed, see section 3 |
| K-05 to K-09 grammar, catalog, order, hints, paths | `3d633b4` | |
| Specs reconciled | `c3e24fa` | your D-030 to D-035 promoted, not duplicated |

Two of your findings changed how I work rather than only what the code does. K-01 was H-01 repeating, which is what made enumeration untenable. K-12 and K-13 were G-007 repeating in a new place: a fixture too thin to distinguish the mutation from the original.

## 2. Mutation matrix

Twenty-one mutations, run one at a time against a restored source. **All twenty-one are caught.** There are no survivors.

| Mutation | Tests failed |
|---|---|
| obligation union to assignment | 6 |
| force_full or to assignment | 5 |
| level max to assignment | 3 |
| drop terminal-NUL framing check | 3 |
| accept a string predicate | 2 |
| accept any file mode | 2 |
| drop filter overrides | 2 |
| drop fsmonitor isolation | 2 |
| hint may write any field | 2 |
| full route skips recipe passes | 1 |
| drop boundary detector | 1 |
| drop copy detection | 1 |
| accept mixed object widths | 1 |
| score on any status | 1 |
| guess the capability catalog | 1 |
| unsorted obligation keys | 1 |
| hint may invent a pass | 1 |
| rewrite backslashes in paths | 1 |
| accept an unvalidated policy | 1 |
| drop duplicate collapse | 1 |

Your four survivors from round four are in that list and now fail.

## 3. Where I did not follow your proposed fix

**K-01.** You proposed discovering every filter driver and overriding it, plus `--no-textconv`, `--no-lazy-fetch`, and real sentinels. I did that, and added a third layer, because the first two still rest on a list being complete and that list had failed twice.

1. Prefer acquisitions that cannot execute anything. I measured which of the four actually runs a filter: only the worktree comparison, because only it converts content. Committed and staged read objects and untracked reads names.
2. Discover rather than list, as you proposed. Overrides attach only to the one comparison that needs them.
3. **Verify the boundary held.** Acquisition fingerprints the repository before and after and records `ADC-ROUTE-BOUNDARY-VIOLATED` if anything moved.

The third layer is the point: I cannot prove the neutralized set is complete, so an unknown path becomes a recorded failure instead of a silent one.

`--no-lazy-fetch` is not a flag in git 2.50.1, so I used `-c fetch.negotiationAlgorithm=noop` instead. **Please check whether that actually prevents a partial-clone lazy fetch, or whether it is cargo cult.** I did not build a partial clone to test it, and I would rather you refute it than have it sit there looking like protection.

## 4. Two numbers worth checking

**The fingerprint nearly shipped as a 90x regression.** The first version walked the directory tree: 14.4s on a real 345-file repository, because it crawled 62,245 build artifacts, taking acquisition from 0.235s to 21.3s. Scoped to what git reports it is 0.412s. The accepted limit is that a write into an ignored directory is not detected. Is that limit acceptable, and is the fingerprint cheap enough on a repository much larger than 345 files?

**Copy detection, from round four's open question.** A synthetic 3000-file all-rename commit takes 1.89s with `diff.renameLimit=0` and finds all 3000 renames. Under git's default limit it takes 0.10s and finds zero, reporting 6000 unrelated adds and deletes, announcing that only on stderr, which the runner discards. Your D-033 ruled unlimited detection correct; the measurement is recorded there.

## 5. Authority

Unchanged. **You may not edit the implementation.** You are the challenger, not the builder, which is `V17` in the catalog this repository ships.

| You may | You may not |
|---|---|
| Report findings with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Write scratch code to demonstrate a defect | Leave scratch files in the repository |
| Edit the spec documents and the plan | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-036` onward | Change a settled ruling |

Scratch work goes outside the repository. Confirm `git status` is clean apart from `design/routing/` before handing back.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| Q-01 | Suite `279 passed, 13 skipped, 45 subtests`; router suite `148 passed`; validation 0 errors | the baseline is not reproducible |
| Q-02 | All thirteen K findings are closed, re-verified with your own probes | a fix is cosmetic |
| Q-03 | No content filter, textconv, fsmonitor, external diff, or other configured program runs during acquisition | K-01 is not closed |
| Q-04 | A boundary violation is detected and makes the snapshot incomplete | the third layer is decorative |
| Q-05 | `build_route` cannot be called with anything but a `ValidatedPolicy`, and a loaded policy is immune to mutation of its source | K-03 is not closed |
| Q-06 | No hint can lower, clear, invent, or write a deterministic field | K-08 is not closed |
| Q-07 | The parser refuses every record git cannot emit, and accepts every record it can, including the worktree null-object shape | K-05 over-corrected or under-corrected |
| Q-08 | Obligation key order is canonical and independent of fact order | receipts cannot be byte-stable |
| Q-09 | `load_policy` requires a catalog and uses the one supplied, not a guess | K-06 is not closed |
| Q-10 | Paths and patterns are compared verbatim in git path space | K-09 is not closed |
| Q-11 | All twenty-one mutations in section 2 are caught on your machine | the matrix is wrong |
| Q-12 | `-c fetch.negotiationAlgorithm=noop` actually prevents a lazy fetch in a partial clone | a control that does nothing is worse than none |

## 7. Attacks worth your time

1. **Find a twenty-second mutation that survives.** That is the most useful thing you can produce, and it has worked in every round so far.
2. **The boundary detector's own blind spots.** It compares index stat plus size and mtime of git-reported files. What write would it miss? mtime granularity, a same-size same-mtime rewrite, and a change confined to ignored paths are the ones I know about.
3. **`_valid_raw_header` over-correction.** I rejected records git can emit once already, and a real-git test caught it. Build a repository exercising submodules, symlinks, type changes, conflicts, and sha256, and check nothing legitimate is now refused.
4. **Filter discovery gaps.** Discovery parses `git config --get-regexp` line by line, splitting on the first space. What driver name breaks that parse? A name containing a space or a dot is the case I would try.
5. **Hint validation vocabulary.** Known capabilities and gates are gathered from the policy's rules and full recipe. Is there a legitimate hint that should be accepted and is not, and does that make the check too strict to use?
6. **The frozen policy's reach.** `ValidatedRule.match_map()` returns a fresh dict each call. Can a caller reach anything mutable through a `ValidatedPolicy`?
7. **Ordering beyond obligations.** K-07 was found because equality hid it. What other field could differ observably while comparing equal?

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-ROUND-FIVE.md`.

```text
# Handoff back to Claude: round five
Date. Agent. Branch, commit, platform, python, git, core.fileMode,
suite result, router suite result, validation result.

## 1. Verification results
Q-01 to Q-12, verdict, evidence, one-line note. Every claim a row.

## 2. Mutation results
Did all twenty-one reproduce as caught? Which further mutations did you
try, and did any survive?

## 3. Findings
id (L-01...), severity, file and line, what is wrong, a concrete failing
input with expected output, proposed fix.

## 4. Rulings
On the K-01 three-layer approach and on Q-12 specifically.

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

Then tell the operator in four lines or fewer: the file, your readiness verdict, counts by severity, and any blocking finding.

## 9. Ground truth

- **Suite, from the repository root:** `python -m pytest anti-dark-code/tests -q`, expected `279 passed, 13 skipped, 45 subtests passed`, about two minutes.
- **Router tests alone:** `python -m pytest anti-dark-code/tests/test_route.py -q`, expected `148 passed`, about ten seconds.
- **Validation:** `python anti-dark-code/scripts/adc.py validate --mode universal`, expected `0 errors, 1 warning`. No `--repo` on that subcommand.
- **Baseline before any of this work:** `131 passed, 13 skipped`.
- **Still not built:** receipts, the `route` subcommand, the gate runner binding, the shadow comparator. Say plainly that you cannot assess them.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-ROUND-FIVE.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself.

## 11. What success looks like

A twenty-second mutation that survives, or a refutation of Q-12. This layer has been wrong in four consecutive rounds, so a clean bill backed by execution would mean something this time. An invented finding still means nothing.

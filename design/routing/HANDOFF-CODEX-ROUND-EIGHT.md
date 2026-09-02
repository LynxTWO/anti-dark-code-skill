# Handoff to Codex, round eight: nine closed, three mutants alive and named

Date: 2026-08-30. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`.

Round seven found nine issues and one surviving mutant of its own. All nine are closed. Three mutants remain alive and are recorded as such.

---

## 1. What happened since round seven

| Finding | Closed by | Reproduced here first |
|---|---|---|
| P-01 caller data defines away the full set | `5454ece` | yes |
| P-03 Route immutability limited to call sites | `5454ece` | yes, `replace` and direct construction |
| P-04 unmerged exemption too wide | `5454ece` | yes |
| P-05 width local to each call | `5454ece` | yes |
| M38 registry pins policies | `5454ece` | yes |
| P-02 index bytes and linked worktrees | `14000b7` | yes |
| P-06 replay can leave a mutant or truncate | `14000b7` | yes, and it truncated the matrix live |
| P-07 symlink identified then followed | `14000b7` | partly, symlinks unavailable here |
| P-09 D-048 repeats a wrong number | `14000b7` | yes |

Two of these were the same mistake wearing different clothes. **P-01**: I made `full_set` required last round and never checked its contents, so `{}` satisfied the requirement and validated nothing. **P-03**: I wrapped obligations in `MappingProxyType` at each construction site, which froze the value those sites passed rather than the field, so `dataclasses.replace` and direct construction both handed back a mutable mapping. Both are fixing the instance I could see instead of the property.

**P-04 corrected two of my own earlier tests.** They asserted `U` shapes git does not write: a both-null unmerged entry, and an unmerged entry inside a commit. The stricter grammar rejected them, and the tests were wrong rather than the code.

## 2. The matrix

46 rows. **40 caught, 3 superseded, 3 surviving.**

```bash
python design/routing/mutants/replay.py            # all rows, about 12 minutes
python design/routing/mutants/replay.py M36 M37    # named rows
```

**Superseded, not surviving:** M32 and M34 attacked the construction-site wrappers that `Route.__post_init__` replaced, and M35 attacked a `_STATUS_SIDES` entry that is now unreachable because `U` is handled earlier. A mutant whose target moved is a no-op, and letting it report as a survivor would be a false gap. `replay.py` skips them and names the replacement.

**Surviving, and labelled:** M36 and M37 attack the fingerprint's path topology and its use of `lstat`. M46 attacks symlink identification and cannot run on a host without symlink privileges, which is this one.

## 3. The harness now guards its own failure modes

P-06 named three, and all three were real:

- **It truncated the matrix while I was writing the guard for that.** Running the filtered `--write` case to check the refusal, the guard had not applied, and the matrix went from 43 rows to 1. Git restored it. The comment in `replay.py` says so.
- **Verdicts came from text.** An earlier check searched the summary line for "error", and a suite that fails to collect prints several things that read like results. Verdicts now come from pytest exit codes: 1 is caught, 0 is survived, anything else is `INCONCLUSIVE`, because a suite that did not run says nothing about the mutant.
- **Restore did not cover interrupts.** `KeyboardInterrupt` does not derive from `Exception`, so the handler now catches `BaseException`, restores, and re-raises.

Worth checking: my own probe for the broken-suite case was wrong. A syntax error in `adc_route.py` makes tests *fail*, which is correctly "caught", so it did not exercise the `INCONCLUSIVE` path. **I have not actually demonstrated that path firing.**

## 4. Numbers I corrected, again

**D-048 repeated a wrong figure while correcting one.** It said the clone was "about 27 kilobytes", which was measured on a small synthetic repository and attributed to the 345-file one. It is 38,477 bytes. The ruling is now narrowed to the clone forms actually tested, and a representation carrying a complete index and worktree snapshot is left as an open question rather than a closed one.

**The cost goal now separates warm from cold.** Warm is 0.34 to 0.89 seconds. You measured 3.30 seconds cold on the 345-file repository and I could not reproduce a genuinely cold cache, so that observation stands unrefuted rather than argued away. EDD section 3 says both.

## 5. Authority

Unchanged. **You may not edit the implementation.** You are the challenger, not the builder, which is `V17` in the catalog this repository ships.

| You may | You may not |
|---|---|
| Report findings with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Add mutants to `matrix.json` and run `replay.py` | Leave scratch files in the repository |
| Edit the spec documents, the plan, and `mutants/` | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-049` onward | Change a settled ruling |

Confirm `git status` is clean apart from `design/routing/` before handing back.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| T-01 | Suite `319 passed, 14 skipped, 45 subtests`; router suite `188 passed, 1 skipped`; validation 0 errors | the baseline is not reproducible |
| T-02 | `replay.py` reproduces 46 rows: 40 caught, 3 superseded, M36, M37 and M46 surviving | the record still cannot be trusted |
| T-03 | An empty or shaped-but-empty `full_set` is refused | P-01 is not closed |
| T-04 | Route obligations are immutable however a Route is constructed, including `replace` and direct construction | P-03 is not closed |
| T-05 | A scored, both-null, or committed unmerged record is refused, and every real conflict shape is accepted | P-04 over-corrected or under-corrected |
| T-06 | One snapshot cannot mix object widths across sources | P-05 is not closed |
| T-07 | A same-size index rewrite with restored mtime is detected, and a linked worktree's index is found | P-02 is not closed |
| T-08 | A symlink is recorded by target text and never read through | P-07 is not closed. Please test this on a host with symlinks; I could not |
| T-09 | `replay.py` refuses `--write` on a filtered run, restores on interrupt, and reports INCONCLUSIVE for a suite that did not run | P-06 is not closed, and see section 3 |
| T-10 | No configured program runs and no lazy fetch occurs during acquisition | the boundary regressed |
| T-11 | The parser accepts every record real git emits across conflicts, submodules, symlinks, type changes, and sha256 | the grammar over-corrected again |
| T-12 | `adc_route.py` still performs no disk write and no network access of its own | the read-only claim is false |

## 7. Attacks worth your time

1. **Rule on M36, M37, and M46.** Three mutants now stand unheld. Keep the code they attack, or take it out until tests hold it. I would rather you decide than argue my own case.
2. **Demonstrate the INCONCLUSIVE path.** I claim the harness handles a suite that cannot run, and I have not shown it. Find a mutant that breaks collection rather than making tests fail.
3. **Symlinks.** T-08 is untested here. A tracked path swapped for a link to data outside the repository is the case.
4. **Find a forty-seventh mutant that survives.** Seven rounds, seven times this has worked.
5. **The `__post_init__` freeze.** It rebuilds the mapping on every construction. Is there a Route path that skips `__post_init__` entirely, for example `copy`, `pickle`, or `__reduce__`?
6. **The width seed.** Snapshot width is seeded from the merge base. What happens when the base is unresolved and the first record is malformed?
7. **Whether any new test can fail.** Six times now a test of mine passed for the wrong reason. The list is in the round-seven handoff; the hard-link test in section 2 there is still the clearest example. Assume there is a seventh.

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-ROUND-EIGHT.md`.

```text
# Handoff back to Claude: round eight
Date. Agent. Branch, commit, platform, python, git, core.fileMode,
symlink availability, suite result, router suite result, validation.

## 1. Verification results
T-01 to T-12, verdict, evidence, one-line note. Every claim a row.

## 2. Mutation results
Did replay.py reproduce 40 caught, 3 superseded, 3 surviving? Which
mutants did you add, and did any survive?

## 3. Findings
id (Q-01...), severity, file and line, what is wrong, a concrete failing
input with expected output, proposed fix.

## 4. Rulings
On M36, M37, and M46, and on the narrowed D-048 scope.

## 5. Edits applied
Documents and mutants/ only.

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

- **Suite:** `python -m pytest anti-dark-code/tests -q`, expected `319 passed, 14 skipped, 45 subtests passed`, about 100 seconds.
- **Router tests alone:** `python -m pytest anti-dark-code/tests/test_route.py -q`, expected `188 passed, 1 skipped`, about fourteen seconds. The skip is the symlink test.
- **Matrix:** `python design/routing/mutants/replay.py`, about twelve minutes. Each row runs the router suite.
- **Validation:** `python anti-dark-code/scripts/adc.py validate --mode universal`, expected `0 errors, 1 warning`. No `--repo` on that subcommand.
- **Baseline before any of this work:** `131 passed, 13 skipped`.
- **Still not built:** receipts, the `route` subcommand, the gate runner binding, the shadow comparator.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-ROUND-EIGHT.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself.

## 11. What success looks like

A ruling on the three surviving mutants, a demonstration of the INCONCLUSIVE path, and a forty-seventh mutant that survives. The record says three guarantees are unheld and one harness path is unproven, which is the state rather than a summary of it. If you run everything and find nothing further, say so with the commands.

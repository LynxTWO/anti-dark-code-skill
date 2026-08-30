# Handoff to Codex, round seven: seven of eight closed, two mutants left alive on purpose

Date: 2026-08-30. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`.

Round six found eight issues, two surviving mutants, and a costing I had wrong by three orders of magnitude. Seven findings are closed. Two mutants remain alive and are labelled as such rather than papered over.

---

## 1. What happened since round six

| Finding | Closed by | Reproduced here first |
|---|---|---|
| N-04 conflict regression | `aad7891` | yes, real merge conflict |
| N-02 provenance transfers through replace | `aad7891` | yes, tampered policy routed cheap |
| M33 index state untested | `aad7891` | yes |
| M34 hinted route mutable | `aad7891` | yes |
| N-01 canonical set optional | `533c0bf` | yes |
| N-06 matrix not replayable | `533c0bf` | yes, I counted my own rows |
| M24 unvalidated mapping | `533c0bf` | yes |
| N-03 path topology | **partly open**, see section 3 | yes |
| N-07 costing wrong | `79dd8c9` | yes, re-measured |

**N-04 was mine, and it broke real repositories.** Git writes an unmerged entry as `:000000 100644 <zeros> <obj> U`, old side null. Last round's status-sides table demanded both sides real, so every conflict in a repository mid-merge reported as malformed and lost its path. My synthetic `U` fixture had two real sides and could not see the real shape. Fourth time a fixture has been too thin to notice the thing it was written for.

## 2. The matrix replays itself now

`design/routing/mutants/matrix.json` carries the source path, the exact text replaced, and the replacement for every row. `design/routing/mutants/replay.py` applies them one at a time against a restored source.

```bash
python design/routing/mutants/replay.py            # every row
python design/routing/mutants/replay.py M36 M37    # named rows
```

That file exists because you counted my rows and found I had miscounted, and because reconstructing from names is not replay.

**It earned itself on the first run: three survivors, all in code I had just written and called covered.** One is closed. Two are not.

**37 mutants, 35 caught, 2 surviving.**

## 3. Two mutants alive on purpose

**M36 removes the path-topology part of the fingerprint. M37 turns `lstat` back into `stat`.** Both were added for your N-03. Neither is held by a test.

`test_replacing_a_file_with_a_hard_link_is_detected` passes, and I traced why: a hard link shares an inode, so `os.utime` on the target also moves the twin's timestamp, and the detector was firing on the twin rather than on topology. Restoring both timestamps did not fix it either, and I stopped guessing rather than keep spending probes.

So the honest state is: a hard-link swap is detected, but not demonstrably *by* the topology fields. The test's docstring says that, and the matrix records both mutants as SURVIVED.

The question for you: is the topology and `lstat` addition worth keeping without a test that holds it, or should it come out until one exists? Keeping unproven code is the specific habit this review cycle keeps catching me in, and I would rather you rule than have me argue my own case.

## 4. The architecture question, re-costed

You were right that I had it wrong. Re-measured: a bare shared clone of the 345-file repository is **145 to 155ms and about 27KB**, not 5.6s and 38MB. I read `du -sb` bytes as megabytes and timed one cold run. The 82 percent mismatch was also misapplied: it rules out hash-based change detection, not a boundary digest.

Both arguments being wrong, I measured the option again and reached the same answer for a different reason, recorded as D-048.

**Capability, not cost.** Against a repository with one committed, one staged, one unstaged, and one untracked change, a bare clone:

- sees the committed change,
- **answers the staged question wrongly**, reporting every tracked file as deleted, because it compares its own empty index against HEAD while the origin had one modified path,
- cannot see unstaged or untracked at all.

The comparisons a clone isolates are the ones already safe by construction. The one comparison that can execute anything is the worktree diff, which a clone cannot perform. `--shared` does not isolate objects either; it writes an alternates file into the candidate object store.

Check that reasoning. I have now been wrong about this question once already.

## 5. Authority

Unchanged. **You may not edit the implementation.** You are the challenger, not the builder, which is `V17` in the catalog this repository ships.

| You may | You may not |
|---|---|
| Report findings with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Add mutants to `matrix.json` and run `replay.py` | Leave scratch files in the repository |
| Edit the spec documents and the plan | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-049` onward | Change a settled ruling |

Confirm `git status` is clean apart from `design/routing/` before handing back.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| S-01 | Suite `309 passed, 13 skipped, 45 subtests`; router suite `178 passed`; validation 0 errors | the baseline is not reproducible |
| S-02 | `replay.py` reproduces the matrix: 37 rows, 35 caught, M36 and M37 surviving | the record still cannot be trusted |
| S-03 | A repository mid-merge acquires without a malformed record | N-04 is not closed |
| S-04 | `dataclasses.replace` on a loaded policy is refused by `build_route` | N-02 is not closed |
| S-05 | A change to the index alone is detected by the boundary check | M33 is not closed |
| S-06 | Every Route construction path yields immutable obligations | M34 is not closed |
| S-07 | `load_policy` cannot be called without a canonical full set | N-01 is not closed |
| S-08 | The clone measurements in section 4 reproduce, including the wrong staged answer | D-048 rests on bad numbers again |
| S-09 | No configured program runs and no lazy fetch occurs during acquisition | the boundary regressed |
| S-10 | The parser accepts every record real git emits, across conflicts, submodules, symlinks, type changes, and sha256 | L-06 and N-04 over-corrected somewhere else |
| S-11 | Acquisition cost is unchanged in shape: about 0.5s here, under 1s on a few hundred files | the fingerprint got expensive |
| S-12 | `adc_route.py` still performs no disk write and no network access of its own | the read-only claim is false |

## 7. Attacks worth your time

1. **Find a thirty-eighth mutant that survives.** Add it to `matrix.json` and run the harness. Six rounds, six times this has worked.
2. **Rule on M36 and M37.** Keep the unproven fields, or take them out until a test holds them.
3. **The registry.** Provenance is a `WeakValueDictionary` keyed by `id()`. The first version used a `WeakSet` and was wrong, because equal policies shared an entry and collecting either refused the other. Is identity keying right, and can `id()` reuse after collection admit a forged policy?
4. **The unmerged exemption.** `U` is now exempt from the side check entirely. Is that too wide? Name a malformed unmerged record that should be refused and now is not.
5. **The full-set contract.** `full_set` is required, but it is caller-supplied data with no schema. What does a wrong `full_set` let through?
6. **Whether any new test can fail.** Five times now a test of mine passed for the wrong reason: a sentinel tripped by its own setup, a capability check shadowed by a gate check, a mutation timed before its window, an index test whose worktree also moved, and the hard-link test in section 3. Assume there is a sixth.
7. **The harness itself.** `replay.py` restores the source in a `finally`. What happens if the suite is interrupted, and can a mutant be left in the tree?

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-ROUND-SEVEN.md`.

```text
# Handoff back to Claude: round seven
Date. Agent. Branch, commit, platform, python, git, core.fileMode,
suite result, router suite result, validation result.

## 1. Verification results
S-01 to S-12, verdict, evidence, one-line note. Every claim a row.

## 2. Mutation results
Did replay.py reproduce 35 caught and 2 surviving? Which mutants did you
add, and did any survive?

## 3. Findings
id (P-01...), severity, file and line, what is wrong, a concrete failing
input with expected output, proposed fix.

## 4. Rulings
On M36 and M37, and on the D-048 reasoning in section 4.

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

- **Suite:** `python -m pytest anti-dark-code/tests -q`, expected `309 passed, 13 skipped, 45 subtests passed`, about 100 seconds.
- **Router tests alone:** `python -m pytest anti-dark-code/tests/test_route.py -q`, expected `178 passed`, about twelve seconds.
- **Matrix:** `python design/routing/mutants/replay.py`, expected 37 rows with M36 and M37 surviving. It takes several minutes: each row runs the router suite.
- **Validation:** `python anti-dark-code/scripts/adc.py validate --mode universal`, expected `0 errors, 1 warning`. No `--repo` on that subcommand.
- **Baseline before any of this work:** `131 passed, 13 skipped`.
- **Still not built:** receipts, the `route` subcommand, the gate runner binding, the shadow comparator.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-ROUND-SEVEN.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself.

## 11. What success looks like

A ruling on M36 and M37, and a thirty-eighth mutant that survives. The matrix is the honest record now: it says two guarantees are unheld, which is a thing I would previously have written a sentence about instead. If you run the harness, attack section 7, and find nothing further, say so with the commands.

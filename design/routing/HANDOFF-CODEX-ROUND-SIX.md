# Handoff to Codex, round six: nine findings closed, matrix as data

Date: 2026-08-30. From: Claude Opus 5. To: Codex. Status: Open.
Repository: `anti-dark-code-skill`, branch `design/assurance-router-specs`.

Round five refuted my central claim twice: the matrix had twenty rows where I said twenty-one, and it had survivors. All nine findings are closed and the matrix is now data rather than prose.

---

## 1. What happened since round five

| Finding | Closed by | Reproduced here first |
|---|---|---|
| L-01 lazy fetch not prevented | `9a19997` | no, see section 3 |
| L-02 fingerprint misses same-size rewrite | `9a19997` | yes |
| L-03 canonical full set unvalidated | `f50e020` | yes |
| L-04 type check has no provenance | `f50e020` | yes, forged policy routed cheap |
| L-05 hint types and pairings | `94f3070` | yes |
| L-06 impossible raw records accepted | `94f3070` | yes |
| L-07 Route shallowly frozen | `f50e020` | yes, `obligations.clear()` worked |
| L-08 surviving mutations | `94f3070` | yes, and I found a third |
| L-09 matrix not reproducible | `94f3070` | yes, counted my own rows |

Your D-036 through D-041 were already written and Confirmed, so nothing was duplicated. Three carry as-shipped notes where the implementation differs, listed in section 3.

Suite went from 131 at the start of this work to 300.

## 2. The mutation matrix, as data

`design/routing/mutants/matrix.json` holds thirty-two mutants. Each records the exact string replaced, the replacement, the verdict, and the pytest summary line. Each was applied alone against a restored source.

**Thirty-two mutants, zero survivors.**

That file exists because you counted my rows and I had miscounted. Reconstruct from it rather than from prose, and tell me if any entry does not reproduce.

Nine of the thirty-two are new this round: recipe level and review merges, the unrouted reason code, the lazy-fetch control, both fingerprint halves, payload width consistency, status sides, required scores, provenance, and hint pair checking.

## 3. Three places the implementation differs from your decision

**D-036, lazy fetch.** The control is `GIT_NO_LAZY_FETCH=1` and the negotiation setting is gone. I could not reproduce the fetch here: a local file transport ignores the partial-clone filter, and the resulting objects are packed, so no single loose object can be removed. **The test asserts the control is present, not the behaviour it prevents.** That is weaker than your reproduction and the docstring says so. If you can hand me a scriptable way to build a real blobless clone locally, I will turn it into a behavioural test.

**D-037, fingerprints.** You wrote that a size-and-mtime fingerprint is diagnostic only and the check should use content identity. I use content identity **and kept metadata**, because switching to content alone broke the existing boundary test: content cannot see a rewrite with identical bytes, since only the timestamp moves. Mutants M12 and M13 delete one half each and both are caught. Is keeping both right, or does it hide a case where they disagree?

**D-039, raw grammar.** One case is deliberately looser than the decision implies. An unrecognised status letter still produces a row with kind `unknown` plus a separate report, rather than being refused as malformed. Refusing it discards the path, and a lost path seemed worse than an unknown kind that forces the full route anyway. Rule on that.

## 4. Cost, measured

Acquisition: **0.474s** on this repository, **0.853s** on a real 345-file repository, **5.4s** on a synthetic 3000-file commit where every file changed. The last exceeds the goal in EDD section 3, which now says so rather than carrying a target the code does not meet. The two contributors are unlimited copy detection (D-033) and the content fingerprint (D-037), both chosen over silently losing evidence.

The costing exercise that preceded this work is worth checking too. The owner asked whether to move acquisition to an isolated repository representation. I measured and said no:

- A bare `--shared` clone of the 345-file repository costs **5.6s and 38MB** per route.
- Hashing the worktree ourselves instead of asking git produces **82% false positives** on that repository, because `core.autocrlf=true` stores LF and checks out CRLF, so our raw-bytes hash cannot match the index blob id. Every route would force full.

If either measurement is wrong, the architecture conclusion is wrong with it.

## 5. Authority

Unchanged. **You may not edit the implementation.** You are the challenger, not the builder, which is `V17` in the catalog this repository ships.

| You may | You may not |
|---|---|
| Report findings with severity | Edit `adc_route.py`, `adc.py`, or `test_route.py` |
| Write scratch code to demonstrate a defect | Leave scratch files in the repository |
| Edit the spec documents, the plan, and `mutants/` | Edit anything under `.github/` or `metrics/` |
| Add decisions from `D-042` onward | Change a settled ruling |

Confirm `git status` is clean apart from `design/routing/` before handing back.

## 6. Claims to verify

| # | Claim | Consequence if wrong |
|---|---|---|
| R-01 | Suite `300 passed, 13 skipped, 45 subtests`; router suite `169 passed`; validation 0 errors | the baseline is not reproducible |
| R-02 | All nine L findings are closed, re-verified with your own probes | a fix is cosmetic |
| R-03 | Every entry in `mutants/matrix.json` reproduces as caught on your machine | the matrix is wrong again |
| R-04 | No configured program runs during acquisition, and no lazy fetch occurs in a real partial clone | L-01 is not closed |
| R-05 | A write that preserves size and mtime, and a write that preserves content, are both detected | L-02 is half closed |
| R-06 | A `ValidatedPolicy` not produced by `load_policy` is refused | L-04 is not closed |
| R-07 | A recipe missing any canonical pass, capability, or gate is refused, with the message naming the right fault | L-03 is not closed |
| R-08 | No hint can pass a wrong type, an unpaired capability and gate, or a pairing from a proposed rule | L-05 is not closed |
| R-09 | The parser refuses every record git cannot emit, and still accepts every record it can | L-06 over-corrected or under-corrected |
| R-10 | `Route.obligations` cannot be mutated after construction | L-07 is not closed |
| R-11 | The costing in section 4 is correct: the clone cost and the 82% false-positive rate | the architecture decision rests on bad numbers |
| R-12 | `adc_route.py` still performs no disk write and no network access of its own | the read-only claim is false |

## 7. Attacks worth your time

1. **Find a thirty-third mutant that survives.** Five rounds, five times this worked. The matrix records what I thought to try, which is exactly its blind spot.
2. **The status-sides table.** I now assert which sides each status has. Build a repository with submodules, symlinks, type changes, conflicts, and a merge with staged conflict entries, and check nothing legitimate is refused. I over-corrected once already this round and a real-git test caught it.
3. **Payload width consistency.** Width is set by the first well-formed record. What happens when the first record is the malformed one?
4. **Hint pairing.** Pairs come from approved rules and the full recipe. Is there a legitimate escalation a reviewer would want that this now refuses?
5. **Provenance.** The token is a module private. Beyond reaching for it directly, is there another way to obtain a `ValidatedPolicy` carrying it, for example through copy, pickle, or dataclasses.replace?
6. **The fingerprint's remaining blind spots.** Ignored paths are out of scope by design. What else? A file replaced by a symlink to identical content, and a hard link, are the two I would try.
7. **Whether any of my new tests can fail.** Three times now I have written a test that passed for the wrong reason: a sentinel tripped by its own setup, a capability check shadowed by a gate check, a mutation-timing window that closed too early. Assume there is a fourth.

## 8. What to hand back

Write `design/routing/HANDOFF-BACK-ROUND-SIX.md`.

```text
# Handoff back to Claude: round six
Date. Agent. Branch, commit, platform, python, git, core.fileMode,
suite result, router suite result, validation result.

## 1. Verification results
R-01 to R-12, verdict, evidence, one-line note. Every claim a row.

## 2. Mutation results
Did all thirty-two entries in mutants/matrix.json reproduce? Which
further mutants did you try, and did any survive?

## 3. Findings
id (N-01...), severity, file and line, what is wrong, a concrete failing
input with expected output, proposed fix.

## 4. Rulings
On the three divergences in section 3 of the handoff, and on the costing
in section 4.

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

- **Suite, from the repository root:** `python -m pytest anti-dark-code/tests -q`, expected `300 passed, 13 skipped, 45 subtests passed`, about two minutes.
- **Router tests alone:** `python -m pytest anti-dark-code/tests/test_route.py -q`, expected `169 passed`, about fourteen seconds.
- **Validation:** `python anti-dark-code/scripts/adc.py validate --mode universal`, expected `0 errors, 1 warning`. No `--repo` on that subcommand.
- **Baseline before any of this work:** `131 passed, 13 skipped`.
- **Still not built:** receipts, the `route` subcommand, the gate runner binding, the shadow comparator. Say plainly that you cannot assess them.
- **Do not** install a dependency or run a gate with `--allow-exec`.

## 10. Writing rules

No em dashes or en dashes. Banned words: robust, seamless, cutting-edge, powerful, world-class, blazing, game-changing, captures, implies, reframes, strips, weaponize, "the exact", delve, showcases, leverages. Short sentences, concrete nouns, and say "we do not know yet" when that is true.

```bash
cd design/routing
FILES="ARCHITECTURE.md ENGINEERING.md DECISION-LOG.md SLICE-001-route-shadow.md HANDOFF-BACK-ROUND-SIX.md"
grep -n $'—\|–' $FILES
grep -nioE "robust|seamless|cutting-edge|world-class|blazing|game-changing|weaponize|delve|showcases|leverages" $FILES
```

Both should return nothing. A file documenting the rule always matches itself.

## 11. What success looks like

A thirty-third mutant that survives, or a refutation of the costing in section 4. Second best is a ruling on the three divergences. If you run everything and find nothing, say so plainly with the commands: this layer has been wrong in five consecutive rounds, so a clean bill backed by execution would finally mean something.

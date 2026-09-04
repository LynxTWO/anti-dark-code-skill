# Handoff back: the rebuilt backfill, the narrowed classifier, and the ledger

Date: 2026-09-03. From: Opus 5, which implemented `HANDOFF-OPUS-SLICE-002-R2.md` and stopped. For: the owner, and then Sonnet 5 for the campaign's periodic summaries. Branch `claude/slice-002-impl-r2`, four commits on `main` at `bb89b79`.

## 1. Terminal outcome

Every item of the handoff is built: M0, M7's classifier and its canary, M5, and M4. One definition was changed rather than made silently: D-131, which commits the run artifacts unread as an inbox, because they expire on 2026-12-02 and ingest is built after them.

**Section 5 of the first version of this document was wrong, and the correction is the most important thing in it.** It claimed no `docs-only` change in this repository could break an omitted gate after D-129, and it escalated a change to G8 to the owner on that basis. The fresh-context challenge of the implementation disproved it in one measurement, and found that this build had created the counterexample itself. The escalation is withdrawn, the canary is built, and G8 stands untouched. Section 5 now records what actually happened.

The challenge found nine other defects, three of them serious. All are repaired here, held by tests and rows rather than by challenging the repair, per the cap. Section 6 lists them.

## 2. What was built

| Item | Commit | What holds it |
| --- | --- | --- |
| M0 | `2e84e40` | Six records under `metrics/shadow/inbox/`, D-131 |
| M7, classifier | `2e84e40` | `RepositoryCalibrationTests`, four tests; M139, M140 |
| M5, rebuilt | `6235e50` | `ShadowBackfillCliTests`, seven tests; M141 to M144 |
| M5, the real backfill | `235e1dd` | 33 records under `metrics/shadow/backfill/` |
| M4 | `e88a910` | `ShadowLedgerCliTests`, eight tests; M145 to M148 |

Full suite at `e88a910`: 546 passed, 14 skipped, 75 subtests, on Windows. Every mutation row was measured to fail its named suite before commit, and the source restored; all ten are `pending` for the next authoritative two-host replay, as the round-twenty-one procedure requires.

## 3. The class mix, measured

The ledger holds 39 records: 33 backfill, 5 live, 1 canary, in seven classes.

| Class | Rules | Omits | live | backfill | canary | N |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `0d0ee37f` | docs-only, product-code, schema-contract, verification-authority | nothing | 0 | 15 | 0 | 0 |
| `b3d197a8` | docs-only, product-code, verification-authority | nothing | 0 | 10 | 0 | 0 |
| `2208f6b6` | docs-only, verification-authority | nothing | 0 | 6 | 0 | 0 |
| `fac413c9` | docs-only, schema-contract, verification-authority | nothing | 0 | 2 | 0 | 0 |
| `6a6b05ab` | docs-only, product-code, schema-contract, verification-authority | nothing | 4 | 0 | 0 | 0 |
| `17898486` | docs-only, product-code | nothing | 1 | 0 | 0 | 0 |
| `43dd098f` | docs-only | four gates | 0 | 0 | 1 | 0 |

**Every class but one omits nothing.** Every pull request in this repository touches the router, its tests, the calibration, a schema or the workflow, so the self-grading rule forces the full recipe. The single class that omits anything is the old `docs-only` class, and the only record in it is the canary's miss. N is zero everywhere. That is the honest state of the campaign, and it is the same answer the merge-based backfill gave, reached now from a population that could have shown a miss.

Two records are for superseded attempts, PR #29's second and PR #30's second. A merge population cannot contain those by construction, and they are the first evidence in this repository of the thing D-128 was written for.

## 4. What the rebuild changed, and what it caught

**The base rule.** `merge-base(head, landing^1)` returns `cd6704a2` for PR #31, which is the base the API reports. The rule D-128 replaced returns the head itself on this history; a test now asserts that shape directly, so the defect cannot return quietly.

**The working tree is not part of a historical change.** This is the defect the rebuild found in itself. The first real run of the new backfill produced 33 records that were all wrong: acquisition read four files this build had not yet committed and the 33 records the run was itself writing into `metrics/shadow/backfill/`. One record showed it, as `snapshot-incomplete`; the other 32 looked plausible and were not. The field study did not show this because it ran against a clean scratch clone. `_historical_runner` now answers the index, worktree and untracked sources with silence, which is what a commit has, and a test runs the same commit against a clean tree and a deliberately dirty one and requires the same record id. The contaminated records were deleted, not amended; the committed 33 come from a clean re-run and differ in class from the contaminated ones, which is how the contamination was confirmed rather than assumed.

**A row that survived.** M148, which makes ingest believe the outcomes a pull request uploaded, passed its suite on first measurement: every ingest test ran `--offline`, so G10's central check had no test at all. The test that stubs the API was written, and M148 was then measured to fail. The row found a missing test, which is what rows are for.

## 5. The canary, and the claim that was wrong

M7 asks for a `docs-only` canary under the new class key. The first version of this document said none could be constructed, and reasoned as follows: the suite's only repository prose is `design/routing/**/*.md`, which D-129 has just made authority; the skill's own prose is already authority; and of the rest, only the calibration templates are read by a gate, where a personal absolute path fails `distribution` **and** `validate-core`, which is inconclusive rather than a miss. All of that is true and none of it is sufficient, because the enumeration was wrong.

`docs/review/adversarial-pass.md` routes `docs-only` and the suite reads it. This build put it there: commit `2e84e40` moved the self-grading counterexample to that path and, in the same commit, added `self.assertTrue(ordinary.is_file())` so the counterexample could not rot into a vacuous pass. That assertion makes a `docs/` prose file something a gate reads. I then wrote that no gate reads the prose the class covers, and escalated a change to a self-grading guard on that basis. The challenge found it in one probe.

The canary is `canary/docs-only/2026-09-03-b`, pull request #38, **never to be merged**. It deletes that file. Measured before pushing: `validate --mode universal` gives `VALID (universal): 0 errors`, and `SelfGradingAuthorityTests::test_an_ordinary_documentation_path_does_not_force_full` fails. The selected gate passes, an omitted gate fails, and the record should read `status: miss` with `provenance: canary` derived from the branch name. **No change to G8 is needed and the escalation is withdrawn.**

Two things are worth keeping from the wrong answer. The class is much narrower than it was, which is what D-129 was for. And a file whose existence the suite asserts is a file a gate reads, so by D-129's own principle `docs/review/adversarial-pass.md` is arguably authority too; leaving it prose is what makes the canary possible, and that is a tension the next round should look at rather than settle here.

PR #35 stays open and unmerged. Its record is in the ledger as the canary of the old class key, which is what D-129 said it would become.

## 6. What the implementation challenge found, and what was repaired

One fresh-context challenge, per the cap; every repair is held by a test and a row, and the repair was not re-challenged.

| Finding | Verdict | Repair |
| --- | --- | --- |
| A record could report an omitted gate's failure honestly and still call itself `clean`; it was accepted online against a real run and counted toward N | BROKEN | `verify_record` recomputes the verdict from the re-read outcomes and the record's own selected and omitted gates, through a pure `status_from` that needs no policy; M150 |
| A canary could declare itself `live` and skip the ancestor check | BROKEN | Provenance re-derived from the head ref; M151 |
| A canary whose head is absent was waved through | BROKEN | Refused: it cannot be shown not to have landed |
| A record naming no run skipped the API read silently | BROKEN | Refused unless `--offline` says so |
| `--keep-going` exited 0 with refusals | BROKEN | Exits 2; a refusal is a refusal |
| The schema is never applied on the ingest path, so an extra key and a wrong `schema` value both passed | BROKEN | `validate_record` enforces the closed key set, the schema name, and `base_reconstructed` for backfills |
| The isolation matched bare `ls-files`, which `_repo_fingerprint` also uses, so the acquisition boundary watched nothing while the snapshot called itself complete | PARTIAL | Matches `ls-files --others` only; a test compares the fingerprint under both runners; M149 |
| `base_gate_outcomes` came from a `pull_request` run for 26 of 33 records | PARTIAL | `event=push` filter. No record was affected: every base run was green |
| The backfill covered 9 of 35 pull requests with no stated window | BROKEN | `--since` is now optional and omitting it walks the whole branch; the committed backfill is 55 records over PRs #15 to #33 |
| D-128, the brief and this handoff described the base as "the base branch as it stood at the merge"; the code computes the fork point | BROKEN, prose only | The code was right and the prose is corrected; the two differ on seven of nine pull requests |
| The brief still spelled the D-129 glob `design/routing/**/*.md`, the exact mistake M140 exists to catch | BROKEN, prose only | Corrected |

Two the challenge raised that are **not** repaired, and why. M139 repoints the glob rather than removing the entry, which the commit message described loosely; the row's effect on the classifier is what it claims and the name is now the only inaccuracy, so it is left rather than churned. And the summary's byte-determinism is conditional on records ingest accepts: for honestly built records the class key determines the class block, and the real ledger is byte-identical reversed, but two records sharing a key with different class blocks would order-depend. Recomputing the class at ingest is the fix, and it is blocked on the policy drift D-129 created; it belongs to the next round with the evidence in hand.

## 7. Open, and for whom

- **The owner.** The canary question in section 5. Nothing else in this build waits on anything.
- **Measured, not assumed, and still open:** whether a fork pull request's read-only token can upload the artifact. Every run so far has been same-repository. Unchanged since the first handoff.
- **Sonnet 5.** `shadow ingest` and `shadow summary` are the periodic commands. Ingest wants `--source` directories, a `--month`, and `--write-pull-requests` to refresh the author and merge date the criterion needs; the summary takes the ledger and that file. Both are deterministic and the summary is byte-identical on a second run.
- **The next authoritative replay.** M139 to M148 carry `pending` verdicts and no host records.

## 7. Boundaries, unchanged

Nothing selective executes. `required`'s needs are untouched. No rule was approved. No classifier entry was narrowed except the one D-129 names. `sampled` is not in the provenance enum, because D-130 hands it to SLICE-003 together with the step that would derive it. Nothing was written to any repository but this one.

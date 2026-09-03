# Handoff back: the rebuilt backfill, the narrowed classifier, and the ledger

Date: 2026-09-03. From: Opus 5, which implemented `HANDOFF-OPUS-SLICE-002-R2.md` and stopped. For: the owner, and then Sonnet 5 for the campaign's periodic summaries. Branch `claude/slice-002-impl-r2`, four commits on `main` at `bb89b79`.

## 1. Terminal outcome

M0, M7's classifier, M5 and M4 are built, tested, and their data committed. The `docs-only` canary M7 also asks for is **not** built, and the reason is a finding rather than an omission: after D-129 there is no change in this repository that the classifier calls prose and that any omitted gate reads. Section 5 states it with the measurements and says what it costs. That is the one item of the handoff left undone, and it needs an owner decision because it changes what the owner would be approving.

One definition was changed, and it is recorded rather than made silently: D-131, which commits the run artifacts unread as an inbox, because they expire on 2026-12-02 and ingest is built after them.

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

## 5. The canary, and why there is not one

M7 asks for a `docs-only` canary under the new class key: a change the classifier calls prose that deliberately breaks a gate the route omits. I could not construct one, and I believe none exists here now.

What the class omits is `full-suite`, `distribution`, `hostile-environment` and `mutation-replay`; it keeps `validate-core`. So a canary needs prose that one of those four reads and that `validate-core` does not.

- The suite reads exactly one class of repository prose: `design/routing/**/*.md`, through `decision_reference_sources`. D-129 has just made all of it verification authority, so such a change no longer routes `docs-only` at all. That was the point of the decision, and it closes the only construction the old canary used.
- The skill's own prose is already authority through `**/references/*.md` and `**/SKILL.md`.
- The remaining prose the class covers is `docs/`, `metrics/`, the calibration templates, `anti-dark-code/LICENSE.md` and `.github/pull_request_template.md`. Of these, only the templates are read by a gate, and I measured what happens: a personal absolute path added to `anti-dark-code/assets/templates/calibration/README.md` fails `distribution` **and** `validate-core`, because both run the same check on the skill tree. A selected gate that fails makes the record inconclusive, not a miss, so it is not a canary.

The honest reading is that the class is now inert: no gate reads the prose it covers. That is a stronger safety statement than a canary, and it is also the reason G8's canary cannot be produced. But G8 is a requirement, and I have not met it, so **the class cannot reach the criterion as the brief is written**. Two ways out, and the choice is the owner's:

1. **Replace the canary for an inert class with a proof of inertness**: a test that enumerates the paths the class covers and asserts no gate reads any of them. Stronger than a canary and cheap to write, but it changes G8, which is a self-grading guard, and that is exactly the kind of change the brief tells the implementer not to make alone.
2. **Keep G8 strict.** The class then cannot be approved, and the campaign's answer for `docs-only` in this repository is that it is safe and unapprovable. Nothing is lost except the milestone.

PR #35 stays open and unmerged. Its record is in the ledger as the canary of the old class key, which is what D-129 said it would become.

## 6. Open, and for whom

- **The owner.** The canary question in section 5. Nothing else in this build waits on anything.
- **Measured, not assumed, and still open:** whether a fork pull request's read-only token can upload the artifact. Every run so far has been same-repository. Unchanged since the first handoff.
- **Sonnet 5.** `shadow ingest` and `shadow summary` are the periodic commands. Ingest wants `--source` directories, a `--month`, and `--write-pull-requests` to refresh the author and merge date the criterion needs; the summary takes the ledger and that file. Both are deterministic and the summary is byte-identical on a second run.
- **The next authoritative replay.** M139 to M148 carry `pending` verdicts and no host records.

## 7. Boundaries, unchanged

Nothing selective executes. `required`'s needs are untouched. No rule was approved. No classifier entry was narrowed except the one D-129 names. `sampled` is not in the provenance enum, because D-130 hands it to SLICE-003 together with the step that would derive it. Nothing was written to any repository but this one.

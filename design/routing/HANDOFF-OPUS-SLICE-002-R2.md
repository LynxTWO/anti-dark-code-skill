# Handoff to Opus 5: rebuild SLICE-002's backfill, narrow the classifier, then the ledger

Date: 2026-09-03. From: Claude Fable 5.1, which revised the design after the field study, had the revision challenged once, closed what the challenge found, and stopped at the owner's instruction. For: Opus 5, which implements and stops. After you: Sonnet 5 runs the summaries; the top tier returns only for the approval review.

## Why there is a second handoff

The first implementation, PR #34, built M1, M2, M3 and M5 and ran the canary. It was correct, and it was then pointed at four other repositories read-only. `FIELD-STUDY-SLICE-002.md` records what that found. Three of the findings changed the design, and the owner took five further decisions on them, recorded as items 6 to 10 of the brief's section 13 and as D-128, D-129 and D-130. A fresh-context challenge of that revision, `CHALLENGE-SLICE-002-R2.md`, then found two defects that would have made it fail on its own terms and several smaller ones; version 0.4 of the brief and the decisions as they now read close them. This handoff is the closed design as build items. Sections 2 to 4 of the brief did not change; section 5 now says how they apply to a backfill record.

## Read first, in this order

1. `design/routing/CHALLENGE-SLICE-002-R2.md`, so you know what was wrong and what closed it. Two things there are load-bearing for your build: the router's glob matching is `fnmatch.fnmatchcase`, whose `*` crosses `/` and which has no `**`; and this repository lands every pull request as a merge commit, so a merged head's merge base with `main` is the head itself.
2. `design/routing/FIELD-STUDY-SLICE-002.md`. The fourth finding is the reason for D-128; the third is the reason for D-130. Read the method note, because the no-checkout acquisition path it describes is what M5 should use, and it was verified equivalent on eleven records.
3. `design/routing/SLICE-002-shadow-evidence.md` version 0.4: section 5's backfill bullet, section 6's first criterion and closing paragraph, section 7's M4, M5 and M7 rows, section 9's S-063 to S-065, section 12, section 13's items 6 to 10.
4. `design/routing/DECISION-LOG.md`: D-128, D-129, D-130, and D-127 which D-128 amends. D-090 still holds: every decision id you cite must exist before or in the same commit.
5. `design/routing/HANDOFF-BACK-SLICE-002-IMPL.md`, your own report back, for the state of the code and the two items it left open: the fork-token measurement and the narrowing, which D-129 now decides.
6. `design/routing/ENGINEERING.md` requirements R-061 to R-063, which you turn from proposed into tested. In `requirement-evidence.json` they carry `review` evidence pointing at their decisions until you name their tests.

## What you build, in order

| Item | Deliverable | What holds it |
| --- | --- | --- |
| M0 | Before anything else, download the five `shadow-*` artifacts GitHub holds for PR #34 and PR #35 and commit them verbatim under `metrics/shadow/inbox/`, named as uploaded. They are hints per G10 until ingested, and they are the only record of the old class's canary; artifacts expire ninety days from 2026-09-03 and M4 comes after M5. | the files; a one-line decision |
| M7 | `design/routing/*.md` classified surface `docs`, effect `verification-authority`, breadth `repository` in `.agents/skills/anti-dark-code/calibration/routing-policy.json`. The glob is `*`, not `**/*`: under `fnmatchcase`, `design/routing/*.md` matches `design/routing/DECISION-LOG.md` and `design/routing/plans/x.md`; `design/routing/**/*.md` matches only the second. Not in the shipped template and not in `AUTHORITY_CLASSIFIERS`; the collision guard folds calibration authority globs in on its own. A test that a change to a top-level file alone, and separately to a nested one, emits a verification-authority fact and forces full. A mutation row that removes the entry, and one that turns `*` into `**/*`. | S-064; R-062; D-129 |
| M7, canary | A new `docs-only` canary under the new class key: a `canary/docs-only/<date>` branch that changes prose no gate reads and breaks an omitted gate some other way, so the comparator is shown to see it. The old canary, PR #35, stays open and unmerged. | S-059; the canary record; the owner's fifth decision |
| M5, rebuilt | `adc.py shadow backfill` enumerates merged pull requests and every `pull_request` run attempt each produced, superseded heads and attempts included. Runs are found through the runs listing filtered to that event and joined to the pull request on head repository and branch, with `/commits/{sha}/pulls` for a run the listing cannot name; `pull_requests` is empty on every merged branch's run here. One record per head and attempt, named as the live artifacts are; a head and attempt that has a live record is skipped, the live one wins. The change set is the head against `merge-base(head, landing^1)`, the landing commit's first parent, which is the base as it stood at the merge for a merge-commit landing and a squash alike; measured for PR #31: head `49ba9668`, landing `de5ef1d3`, base `cd6704a2`. `base_reconstructed: true` in the record, the schema and `validate_record` together, because `test_the_schema_file_and_the_validator_require_the_same_keys` holds them equal and the schema has `additionalProperties: false`. `base_outcomes` from the base's own push run, so the inherited-failure rule applies. A head whose commit is gone is recorded `not_measurable` with reason `head-unavailable`. The merge-commit replay is removed, not kept beside it. Acquisition runs through the production `read_change_inputs` with a runner that rewrites `HEAD` to the commit, as the field study's method note describes and verified; no worktree per change. A real backfill of this repository's pull requests, committed. | S-060, S-063; R-061; a fixture pull request on a merge-commit history with three attempts, one failing, and one with a missing head; D-128 |
| M4 | `adc.py shadow ingest` and `adc.py shadow summary` as the brief's section 5 defines them, with the summary counting pull requests per class: a pull request advances N by one when, in that class, it has at least one clean live record and no miss; an inconclusive record neither adds nor removes; a miss on any attempt is the class's miss, never removed; N may fall. Backfill and live counted separately; canaries listed, never counted; backfill misses reported beside the criterion, never adjudicated. Ingest verifies a backfill record by recomputation against its recorded head and base, not against a checked-out merge commit. No `sampled` provenance: D-130 hands that to SLICE-003 together with the step that derives it. | S-056, S-057, S-059, S-061, S-065; R-063; D-128 |
| Report back | `HANDOFF-BACK-SLICE-002-IMPL-R2.md`: the pull-request class mix for this repository, the new canary's result whichever way it went, and what stayed open. | the brief's section 11 |

Every item that touches `adc.py`, `adc_route.py`, `adc_shadow.py`, the workflow, the schema, or the calibration is verification authority: a test, a mutation row in `design/routing/mutants/matrix.json` measured to fail before commit, and a decision entry where the brief does not already carry one. The round-twenty-one handoff says how a row is written and measured.

## What not to do

- Do not keep the merge-commit backfill as an option. D-128 retires it because its records are indistinguishable from real evidence, and a flag would put that back.
- Do not write `design/routing/**/*.md`. It does not reach the files the decision was written for.
- Do not take the base from the pull request API's `base.sha`; it is not the base at the merge. Do not take it from `main` as it stands; on this history that is the head itself.
- Do not build sampled full runs, and do not add `sampled` to the provenance enum. A value no deterministic step derives is the label G8 forbids.
- Do not narrow any classifier entry other than the one D-129 names, and do not touch `AUTHORITY_CLASSIFIERS` for it.
- Do not change the class-key terms, the measurability rule, or the record's status vocabulary. `base_reconstructed` is a new field, not a new status; `head-unavailable` is a new `not_measurable` reason, not a new status.
- Do not merge PR #35, and do not open the new canary against `main` with intent to merge.
- Do not adjudicate a miss. If the new canary or the rebuilt backfill produces one, record it and report it.
- One challenger, once, against the implementation; repairs held by tests and rows, never by re-challenging the repair.

## Stop points

Stop and report when M4's summary exists and the rebuilt backfill has been committed, or earlier if the fixture for S-063 shows the record format cannot carry an attempt's outcomes without a definition change. Stop before touching `required`, before any selective execution, and before any write to a repository that is not this one.

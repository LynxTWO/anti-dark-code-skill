# Handoff to Opus 5: rebuild SLICE-002's backfill, narrow the classifier, then the ledger

Date: 2026-09-03. From: Claude Fable 5.1, which revised the design after the field study and stopped at the owner's instruction. For: Opus 5, which implements and stops. After you: Sonnet 5 runs the summaries; the top tier returns only for the approval review.

## Why there is a second handoff

The first implementation, PR #34, built M1, M2, M3 and M5 and ran the canary. It was correct, and it was then pointed at four other repositories read-only. `FIELD-STUDY-SLICE-002.md` records what that found. Three of the findings changed the design, and the owner took five further decisions on them, recorded as items 6 to 10 of the brief's section 13 and as D-128, D-129 and D-130. This handoff is those decisions as build items. Nothing in sections 2 to 4 of the brief changed; section 5's backfill, section 6's count, and section 7's build order did.

## Read first, in this order

1. `design/routing/FIELD-STUDY-SLICE-002.md`. The fourth finding is the reason for D-128; the third is the reason for D-130. Read the method note, because the no-checkout acquisition path it describes is what M5 should use, and it was verified equivalent on eleven records.
2. `design/routing/SLICE-002-shadow-evidence.md` version 0.3: section 5's backfill bullet, section 6's first criterion and closing paragraph, section 7's M4, M5 and M7 rows, section 9's S-063 to S-065, section 13's items 6 to 10.
3. `design/routing/DECISION-LOG.md`: D-128, D-129, D-130, and D-127 which D-128 amends. D-090 still holds: every decision id you cite must exist before or in the same commit.
4. `design/routing/HANDOFF-BACK-SLICE-002-IMPL.md`, your own report back, for the state of the code and the two items it left open: the fork-token measurement and the narrowing, which D-129 now decides.
5. `design/routing/ENGINEERING.md` requirements R-061 to R-063, which you turn from proposed into tested, and `requirement-evidence.json`, where they are listed untraced until you name their tests.

## What you build, in order

| Item | Deliverable | What holds it |
| --- | --- | --- |
| M7 | `design/routing/**/*.md` classified surface `docs`, effect `verification-authority`, breadth `repository` in `.agents/skills/anti-dark-code/calibration/routing-policy.json`; not in the shipped template and not in `AUTHORITY_CLASSIFIERS`, because the entry names a directory of this repository. A test that a change to one such file alone emits a verification-authority fact and forces full. A mutation row that removes the entry. | S-064; R-062; D-129 |
| M7, canary | A new `docs-only` canary under the new class key: a `canary/docs-only/<date>` branch that changes prose no gate reads and breaks an omitted gate some other way, so the comparator is shown to see it. The old canary, PR #35, stays open and unmerged. | S-059; the canary record; the owner's fifth decision |
| M5, rebuilt | `adc.py shadow backfill` enumerates merged pull requests and every `pull_request` run attempt each produced, superseded heads and attempts included; one record per head and attempt named as the live artifacts are; change set is the head against its merge base with the base branch; `base_reconstructed: true` in the record and in the schema; `provenance: backfill`. The merge-commit replay is removed, not kept beside it. Acquisition runs through the production `read_change_inputs` with a runner that rewrites `HEAD` to the commit, as the field study's method note describes and verified; no worktree per change. A real backfill of this repository's pull requests, committed. | S-060, S-063; R-061; a fixture pull request with three attempts, one failing; D-128 |
| M4 | `adc.py shadow ingest` and `adc.py shadow summary` as the brief's section 5 defines them, with the summary counting pull requests per class: a pull request advances N by one when every measurable live record it produced is clean; a miss on any attempt is the class's miss, never removed. Backfill and live counted separately; canaries listed, never counted; `sampled` accepted as a provenance value and counted as live, though nothing produces it yet. | S-056, S-057, S-059, S-061, S-065; R-063; D-128, D-130 |
| Report back | `HANDOFF-BACK-SLICE-002-IMPL-R2.md`: the pull-request class mix for this repository, the new canary's result whichever way it went, and what stayed open. | the brief's section 11 |

Every item that touches `adc.py`, `adc_route.py`, `adc_shadow.py`, the workflow, the schema, or the calibration is verification authority: a test, a mutation row in `design/routing/mutants/matrix.json` measured to fail before commit, and a decision entry where the brief does not already carry one. The round-twenty-one handoff says how a row is written and measured.

## What not to do

- Do not keep the merge-commit backfill as an option. D-128 retires it because its records are indistinguishable from real evidence, and a flag would put that back.
- Do not build sampled full runs. D-130 defines them for SLICE-003; here they are one accepted provenance value in the schema and the summary, nothing more.
- Do not narrow any classifier entry other than the one D-129 names, and do not touch `AUTHORITY_CLASSIFIERS` for it.
- Do not change the class-key terms, the measurability rule, or the record's status vocabulary. `base_reconstructed` is a new field, not a new status.
- Do not merge PR #35, and do not open the new canary against `main` with intent to merge.
- Do not adjudicate a miss. If the new canary or the rebuilt backfill produces one, record it and report it.
- One challenger, once, against the implementation; repairs held by tests and rows, never by re-challenging the repair.

## Stop points

Stop and report when M4's summary exists and the rebuilt backfill has been committed, or earlier if the fixture for S-063 shows the record format cannot carry an attempt's outcomes without a definition change. Stop before touching `required`, before any selective execution, and before any write to a repository that is not this one.

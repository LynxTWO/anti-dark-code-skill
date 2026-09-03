# Handoff to Opus 5: implement SLICE-002, the shadow evidence campaign

Date: 2026-09-03. From: Claude Fable 5.1, which designed the measurement and stopped at the owner's instruction. For: Opus 5, which implements it and stops. After you: Sonnet 5 runs the campaign's summaries, and the top tier returns only for the approval review.

## Objective

Build the measurement that `SLICE-002-shadow-evidence.md` defines, exactly as it defines it, so that real changes to this repository produce records of what the proposed routes would have skipped and whether any skipped gate failed, per route class, with the record never depending on the router's own account of itself. Do not change a definition in sections 2 through 6 of the brief; if one is wrong, record a decision that names the brief and says why, and stop for the owner if the change would alter what the owner would be approving.

## Read first, in this order

1. `design/routing/SLICE-002-shadow-evidence.md`, the brief. Sections 2 to 6 are the contract; section 7 is your build order; section 9 is what your tests must hold; section 13 is what the owner still decides.
2. `design/routing/CHALLENGE-SLICE-002-DESIGN.md`, the fresh-context challenge of the brief and how each finding was closed. Anything it left open is listed at the end of this handoff.
3. `design/routing/HANDOFF-BACK-ROUND-TWENTY-ONE.md`, for the state of the router you are building on: D-118 through D-121, the collision guard, and the observation that every written receipt in this repository is full today because of the run store's own ignore file.
4. `design/routing/DECISION-LOG.md`: D-011, D-022, D-064, D-090, D-093, D-100, D-116, D-118 to D-121. D-090 means every decision id you cite in code, tests, or routing Markdown must exist in the log before or in the same commit.
5. `design/routing/ENGINEERING.md` sections 12 and 13, and the requirements table; you will add requirements for the ledger, the record, and the summary, with acceptance criteria S-052 to S-060 from the brief.
6. `metrics/README.md` and `metrics/schemas/efficiency-receipt-v1.schema.json`, whose conventions the shadow ledger follows.

## What you build, in order

| Item | Deliverable | What holds it |
| --- | --- | --- |
| M1 | `ensure_run_gitignore` writes a fourth entry so the store's `.gitignore` ignores itself; a test that `route --write` on a clean tree emits no fact under `.anti-dark-code/`; a mutation row that drops the entry; a decision | the precondition the whole campaign rests on |
| M2 | `adc.py shadow record --repo --base --head --outcomes <json> --out <path>`: computes the route and the candidate for base..head, takes gate outcomes as data, builds the record with `shadow_result`, adds the class key and the digests of section 3 and G5, validates against `metrics/schemas/shadow-record-v1.schema.json` | tests for S-053, S-054; rows for the miss condition and the class key |
| M3 | Workflow job `shadow` in `tests.yml`: `needs` every gate job, `if: always()`, never in `required`'s `needs`; reads the run's job and step conclusions through the GitHub API with the job's own token; maps them to gate ids as section 2's table says; runs M2; uploads `shadow-<head_sha>.json` | a workflow contract test for S-058; the D-011 check that `required` is unchanged |
| M4 | `adc.py shadow ingest` and `adc.py shadow summary`; `metrics/shadow/ledger/<yyyy-mm>.jsonl` append-only; `metrics/shadow/summary.json` deterministic; refusal rules G2 and G5 | tests for S-055, S-056, S-057, S-059 |
| M5 | `adc.py shadow backfill --since <sha>`; a real backfill of PRs #21 to #32 committed to the ledger with `provenance: backfill` | test on a fixture; S-060 |
| M6 | The canary procedure written into the brief's section 4 companion doc, and one canary executed per class the backfill shows, recorded with `provenance: canary` | the canary records |

Every item that touches `adc.py`, `adc_route.py`, the workflow, or the calibration is verification authority: it gets a test, a mutation row in `design/routing/mutants/matrix.json` that fails when applied, and a decision entry. Follow the round-twenty-one handoff for how a row is written and how it is measured to fail before commit.

## Evidence you owe

- The full suite and `validate --mode universal` green on your tree before each commit.
- Every new mutation row measured to fail its suite when applied, before the commit that adds it.
- For any change to `adc_route.py` or the classifier contract: the two-host serial replay at your head, Windows and WSL2 Ubuntu, merged per platform, as rounds twenty and twenty-one did with `r21_evidence.py`'s pattern; the artifact under `design/routing/`; the walkthrough refreshed. For changes only to `adc.py`'s shadow commands and the workflow, the parallel replay at the head plus the rows measured to fail is enough, and say so.
- One fresh-context challenge of the implementation, dispatched once against your final head, and repairs held by tests and rows. Do not re-challenge a repair; the cap is recorded in `HANDOFF-BACK-ROUND-TWENTY-ONE.md` section 6 and in the owner's words.
- `HANDOFF-BACK-SLICE-002-IMPL.md`: what was built, the backfill's class mix, the canary records, the first live record if one exists, the open items, and the exact heads and run ids.

## Boundaries, not negotiable

- No selective execution, local or CI. The `shadow` job is not required and changes no other job. D-011 stands.
- No rule approved. No change to the canonical full set. No change to the `required` aggregator.
- No agent adjudicates a miss; adjudication is a person's signed line in `metrics/shadow/adjudications.jsonl`.
- No write to the repository from CI unless the owner chooses option B in section 13; the default is option A, artifacts ingested by a person or by Sonnet 5.
- The definitions in the brief's sections 2 to 6 are the contract. Changing one silently is the self-grading defect this slice exists to prevent.
- Stop at the end of M6 and write the handoff back. Do not start SLICE-003.

## The owner's decisions, taken 2026-09-03

Section 13 of the brief records them, so nothing in M4 to M6 waits on a question: the criterion is option 1, N of 30, A of 1, D of 30 days with two authors; storage is option A with the recomputing ingest; `docs-only` is not narrowed before counting, so the first canary records the expected miss and the narrowing is decided on that record; backfill informs and never counts toward N; one canary per class key. Build to them. Stop for the owner only if implementing one shows it wrong, and say what you measured.

## Left open by the design challenge

- Measure in M3, do not assume: whether a fork pull request's read-only token can upload the artifact; what conclusion value a timed-out job reports and that the mapping renders it not measurable; that `actions: read` at job level is enough for the API read under the workflow's `contents: read`.
- Measure in M4: whether run conclusions remain readable through the API past ninety days; if not, the ledger is still the durable record and ingest must run inside the window.
- Take the summary's byte conventions from `adc.py efficiency aggregate`, which the challenger reproduced byte-for-byte under Python 3.14: sorted keys, no timestamps, records ordered by id.
- The first `docs-only` canary is expected to be a real miss, because the suite's decision guard reads `design/routing/*.md`. Record it whichever way it goes; do not narrow the classifier yourself, that is the owner's decision in the brief's section 13.
- The brief's revision closed every other finding; the closures are tabulated in `CHALLENGE-SLICE-002-DESIGN.md`. If you find one of them wrong, record a decision that names the brief and stop for the owner if it changes what the owner would approve.

## How the last rounds worked, so you can reproduce them

- Worktree: `.claude/worktrees/round-twenty` holds the branches; make yours from `main` after PR #32 lands, or stack on `claude/round-twenty-one-verify` if it has not.
- The Bash tool in a worktree session refuses `cd`, shell variables, heredocs, and git operations outside the worktree; put scripts in the scratchpad and run `python <script>`; use the PowerShell tool for WSL.
- Line endings: the worktree checks out CRLF; evidence JSON under `design/routing/` is `eol=lf` by D-114; write JSON with `newline="\n"`.
- Commit trailers: `EDD-Checklist: satisfied` and `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`; PR bodies end with the generated-with line.
- The owner walkthrough is the last box of any slice; do not check it.

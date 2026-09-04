# Handoff to Opus 5: close the two design debts, ship the campaign, and install its first consumer

Date: 2026-09-04. From: Claude Fable 5.1, which decided D-133 to D-135 with the owner and stopped. For: Opus 5, which implements and stops. After you: Sonnet 5 runs the periodic ingest and summary, here and for 1st-downs; the top tier returns only for the approval review.

## Why there is a third handoff

The implementation challenge left two design debts open and named them: ingest recomputes the verdict but not the class, and the suite reads a prose file so the `docs-only` canary exists only because a test asserts that file exists. The owner has Jeremy's consent to install the campaign in 1st-downs, the only measured repository that can meet criterion 4, and the shipped skill carries `adc_shadow.py` with nothing explaining it. D-133, D-134 and D-135 decide all four, and brief version 0.5 carries them as M8 to M11.

## Read first, in this order

1. `design/routing/DECISION-LOG.md`: D-133, D-134, D-135. D-090 holds: every decision id you cite must exist before or in the same commit.
2. `design/routing/SLICE-002-shadow-evidence.md` version 0.5: G8 and G10 in section 4, the two new bullets in section 5, the dominance paragraph in section 6, M8 to M11 in section 7, S-066 to S-069 in section 9, sections 11 to 13.
3. `design/routing/HANDOFF-BACK-SLICE-002-IMPL-R2.md` section 6, the two items the challenge raised that were left open; they are M8 and M9 now.
4. `anti-dark-code/references/shadow-evidence.md`, the consumer-facing reference this handoff ships; keep it true as you build. It says which parts are proposed.
5. `design/routing/consumers/JeremyABurton-1st-downs/README.md`, the first consumer's pull request, step by step.
6. `design/routing/ENGINEERING.md` R-064 to R-067, which you turn from proposed into tested; `requirement-evidence.json` carries `review` evidence until you name their tests.

## What you build, in order

| Item | Deliverable | What holds it |
| --- | --- | --- |
| M8 | Every producer writes the stripped policy and gates beside its record as `policy-<policy_terms_sha256>.json` and `gates-<gates_terms_sha256>.json`: `shadow record` writes them to the same output directory and the live job's artifact glob picks them up; `shadow backfill` writes them once per distinct digest into its output directory. Ingest copies each into `<ledger parent>/policies/` after checking the content digests to the name, never rewrites one present, refuses one that does not digest. Ingest then recomputes the class: load the policy and gates the record names; read `anti-dark-code/scripts/adc_route.py` at the record's head from the clone, check its digest against `class.router_blob_sha256`, load it as a module; acquire the change set from the record's base and head through `_historical_runner`; `collect_change_facts` and `build_candidate_route`; refuse on any difference in matched rules, selected gates, omitted gates or class key. A live record with no policy file anywhere is recovered once from `.agents/skills/anti-dark-code/calibration/` at its head; a backfill record in that state is refused. An unrecoverable router refuses with `router-unrecoverable`. Re-ingest the existing ledger from the inbox and backfill directories under the new check and report what it refused; the six D-131 inbox records and the two canaries are expected to recover from their heads. | S-066; R-064; a test with a forged class, a missing policy, a wrong-named policy file, and a router not at the head; mutation rows for the class comparison and the digest check; D-133 |
| M9 | `test_an_ordinary_documentation_path_does_not_force_full` asserts the classifier, not the tree: the path matches an entry with effect `prose` and none with effect `verification-authority` under the installed calibration; the existence assertion goes; a sweep test asserts no test module opens a path under `docs/`. Then `adc.py shadow dominance --repo --calibration --map --class-key <key> --out-dir`: enumerate every tracked path the class's classifier entries cover; probe one, delete them all and run every canonical gate's local command from `gates.json` when `owner_confirmed_safe_to_execute` is true, else refuse and say so; probe two, restore and replace each file's content with bytes that are not the original, run again; restore and hash-verify the tree; write one record per probe with `provenance: dominance`, the probe's gate outcomes, and the class; the summary lists dominance records beside canaries, counts them in neither N nor misses, and reports a class `dominated` when both probes exist for its key and neither is a miss. Run it for this repository's `docs-only` class and record the result whichever way it goes. | S-067, S-068; R-065, R-066; the counterexample test, the sweep, a fixture class no gate reads and one an omitted gate reads; rows for the counting and the restoration; D-134 |
| M10 | The consumer kit ships: `references/shadow-evidence.md` (written; keep it true), `assets/templates/shadow-job.yml` and `assets/templates/shadow-gate-map.json` (written), the SKILL.md line under supporting references (written), and the CHANGELOG entry naming all four (written). Ingest and summary accept a consumer ledger directory as `--ledger` and keep `policies/` beside it; a test ingests a fixture consumer clone into `metrics/shadow/consumers/<slug>/` and hashes the clone before and after. Then the release: VERSION to the next number, the CHANGELOG `Unreleased` section moved under it, the tag, `release-check` against the tag. The installer refuses an untagged source, so 1st-downs cannot upgrade before this. | S-069; R-067; `validate --mode distribution` clean; `release-check` clean; D-135 |
| M11 | With Jeremy: 1st-downs' pull request, exactly as `consumers/JeremyABurton-1st-downs/README.md` says, its owners editing the proposal as they see fit. Then its first live record ingested under `metrics/shadow/consumers/JeremyABurton-1st-downs/`, and the backfill over its 45 pull requests' run history into the same ledger. | the first consumer record; D-135 |
| Report back | `HANDOFF-BACK-SLICE-002-IMPL-R3.md`: what the re-ingest refused and why, the dominance result for `docs-only` here, the release tag, and 1st-downs' first record and class mix. | the brief's section 11 |

Every item that touches `adc.py`, `adc_route.py`, `adc_shadow.py`, the workflow, the schema, the calibration, a reference or a template is verification authority: a test, a mutation row measured to fail before commit, and a decision entry where the brief does not already carry one.

## What not to do

- Do not recompute the class against today's policy. The policy that built the record is the one kept by its digest; today's is only right for a backfill record made today.
- Do not weaken `additionalProperties: false` or the closed key set to admit the policy files; they are separate files beside the record, not fields in it.
- Do not add `dominance` to the provenance enum without the command that derives it, and do not let a dominance record count toward N or the misses.
- Do not let the dominance probe run a gate when `owner_confirmed_safe_to_execute` is false. It executes everything, twice, and only where execution is confirmed.
- Do not write anything to 1st-downs beyond the four files and the job, and do not copy this repository's calibration into it.
- Do not tag a release whose notes fail to name a changed reference or asset; `release-check` reports it and the notes are wrong, not the check.
- Do not merge PR #35 or PR #38.
- One challenger, once, against the implementation; repairs held by tests and rows.

## Stop points

Stop and report after M10's release is tagged and checked, before M11's pull request is opened, so the owner and Jeremy open it. Stop earlier if M8's re-ingest refuses a record it cannot recover, if a dominance probe cannot restore the tree, or before any write to a repository that is not this one.

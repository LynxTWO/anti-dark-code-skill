# Assurance Router Slice Brief: SLICE-002 shadow evidence campaign

Version: 0.2. Date: 2026-09-03. Status: Proposed, design only, revised once after the fresh-context challenge recorded in `CHALLENGE-SLICE-002-DESIGN.md`. Designed by Claude Fable 5.1 per the owner's model sequence; to be implemented by Opus 5 from `HANDOFF-OPUS-SLICE-002.md`; the campaign's summaries by Sonnet 5; the approval review by the top tier.
Companion documents: ARCHITECTURE.md, ENGINEERING.md, DECISION-LOG.md, SLICE-001-route-shadow.md.

One narrow, production-quality measurement. If it is not in here, it does not get built. Nothing in this slice runs less verification than today.

---

## 1. What the slice proves

- **Central claim:** for real changes to this repository over time, the routes the proposed rules would have chosen, had they been obeyed, would not have skipped a gate that failed. Measured per route class against the gates CI actually ran on the same tree, never against the router's own account of itself.
- **What it does not prove:** that any rule is safe to approve. It produces the evidence D-064 asks for and states the criterion the owner would apply. Approval is SLICE-003's act, with its own adversarial review.
- **Honest stakes:** if the misses per class are not zero, the routing idea does not survive contact for that class, and this slice is the cheapest place to learn it. The design challenge already found the first likely miss: the suite's decision guard reads `design/routing/*.md`, which the `docs-only` route would skip the suite for. Section 6 says what follows from that.
- **Why this is where the defects will be:** every round from ten to twenty-one found the same shape of defect, a measurement that graded itself. A shadow ledger is a measurement of the router made by machinery the router ships with. Section 4 exists to keep the two apart, and the design challenge broke its first draft in four places, all recorded.

## 2. What counts as a miss

Definitions, in the order the record is built.

- **Change.** One pull request, measured on the tree CI verified. CI checks out `refs/pull/N/merge`, the merge of the head into the base as it stood when the run started, not the head; the change set is therefore base-at-run-time to that merge commit. The record carries the pull request number, the run id, the run attempt, the merge commit sha, the head sha, and the base sha, all taken from the event payload and the checkout, never from a later API call, because a run's `pull_requests` field empties after the merge. A change whose base is unreachable in the checkout is not measurable; the shadow job fetches the base explicitly, since a shallow checkout leaves it unreachable and the router then reports `ADC-ROUTE-BASE-UNREACHABLE`. Pushes to `main` after a merge are not measured.
- **Authoritative outcome.** For each gate in the canonical full set, the conclusion of the CI job or step that ran it on that attempt, read through the API with `filter=all` so a rerun does not replace the attempt it supersedes. The local gate runner is never a source: in this repository no gate carries a command and `owner_confirmed_safe_to_execute` is false, so a local shadow record always reads `not-run`. The mapping from gate ids to jobs is data in the workflow, per D-064, and a contract test fails when a job or step it names disappears:

| Gate id | CI evidence | Outcome |
| --- | --- | --- |
| `validate-core` | the validate step of every suite job | `pass` if every step concluded success; `fail` if any concluded failure |
| `full-suite` | every suite matrix job | same rule over the jobs |
| `distribution` | the clean distribution job | same |
| `hostile-environment` | both hostile-environment jobs | same |
| `mutation-replay` | the mutation replay job | same |

- **Measurable.** Every one of the five canonical gates is present in the outcomes with `pass` or `fail`. A gate that is absent, cancelled, skipped, timed out, stale, or in progress makes the record not measurable, and this check runs before `shadow_result`, because `shadow_result` counts any non-pass omitted outcome as missed and an absent key as clean. A candidate whose selected gate set is empty is recorded as `selects-nothing` and is never evidence; a rule that names no obligation must not load, which is a policy validation the implementer adds.
- **Candidate.** `build_candidate_route` over the change's facts with the policy as shipped, every rule proposed, exactly as `_candidate_shadow_context` rebuilds it from a receipt. Its selected gates are what the proposed rules would have run; the omitted gates are the canonical set minus them. A candidate with `force_full` true omits nothing and is recorded as `no_omission`.
- **Routing miss.** An omitted canonical gate concluded `fail` and every selected gate concluded `pass`. Targeted verification green while omitted verification failed, as ENGINEERING's shadow rollout paragraph says.
- **Inconclusive.** A selected gate failed, so the candidate would have caught the change anyway; the record keeps `missed_gate_ids` and the summary reports omitted failures under inconclusive records as their own count, so that signal is not dropped. Also inconclusive: an `inherited-failure`, where the base's own push run failed the same gate that failed here, which the record detects by reading the base sha's run.
- **Clean.** Every gate passed and at least one gate was omitted. One unit of evidence for the class.
- **A miss is never removed.** A rerun that passes at the same head is a second record, keyed by its own attempt. An adjudication, section 6, annotates a miss; it does not delete it.

## 3. How a route class is identified

The class key is what the owner would approve, so it is the rule's meaning and its context, not the bytes of the file it lives in. The design challenge measured a comment edit, an unrelated rule, and an approval each changing the policy's byte digest, which would have reset every class each time. The key is therefore a canonical digest over:

- the matched proposed rules' `match`, `requires`, and `obligations`, with every `_`-prefixed key stripped and without `review_status`;
- the classifier entries, with `_`-prefixed keys stripped;
- the canonical full set from `gates.json`, likewise;
- the blob sha of `adc_route.py` at the head, because a router change changes what a candidate is, as D-119 to D-121 did;
- the sorted ids of the gates the candidate omitted.

The whole policy's byte digest and canonical digest are both recorded for audit but are not part of the key. Two records count toward the same class only when the keys agree. Approving another rule, editing a note, or adding a rule that does not fire leaves the key unchanged; changing the router, the classifier, the canonical set, or the rule's own terms starts a new class. `docs-only` under today's policy is one class: it selects `validate-core` and omits the other four. The summary reports classes by key with the rule ids beside the key and never merges keys.

## 4. How the record avoids grading itself

Each guard names the way a shadow ledger could lie and the measurement that shows it does not. The design challenge broke G2, G5, G6, and G1's read path in the first draft; each is rewritten here to what it measured.

- **G1, outcomes are not the router's.** Outcomes come only from CI conclusions of jobs that ran the canonical full recipe regardless of any route, read with `filter=all` and keyed by attempt. Every canonical gate must be present, or the record is not measurable; silence never reads as clean. The shadow job is not among the `required` aggregator's needs and changes no other job, per D-011. The job carries `actions: read` at job level, because the workflow's `contents: read` sets every other scope to none.
- **G2, the change set is the tree CI verified.** The shadow job checks out the same merge ref the gate jobs did, fetches the base sha from the event payload, and computes the route from base to merge commit. The record carries the merge sha, the head sha, the base sha, the run id, and the attempt. Ingest refuses a record whose merge sha is not the run's checked-out commit, and marks a record `base-drift` when the base sha at record time is not an ancestor of the merge commit.
- **G3, the run store is not a change.** Today every `route --write` creates `.anti-dark-code/.gitignore`, which the repository's ignore file does not cover, so every written receipt carries an unmapped fact and both builders force full. The store's ignore file ignores itself, written by `ensure_run_gitignore` as a fourth entry; the design challenge measured this as the one fix that keeps a new `.anti-dark-code/calibration/` visible, where ignoring the directory in the repository's ignore file would hide it and excluding it in the router would reopen the blindness D-089 records. The CI record does not write the store at all; the fix matters for local receipts and for the precondition test.
- **G4, the record is not a change either.** The shadow job writes its record to a path outside the tree and uploads it as an artifact named `shadow-<head_sha>-<run_attempt>.json`, never overwriting; `write_shadow` is not used, because it requires a local gate run directory.
- **G5, versions do not mix.** The router blob sha is part of the class key, section 3; the policy digests and the `gates.json` digest are recorded; the summary refuses to count records into a class whose key differs.
- **G6, approval later does not rewrite the past.** Because the key excludes `review_status` and other rules, approving one rule leaves every other class's key and clock unchanged.
- **G7, no judgment in a record.** A record is produced by the deterministic step only. Adjudications live in `metrics/shadow/adjudications.jsonl`, each naming the record id, the passing rerun's record id at the same head, the unknown from ENGINEERING section 16 or `docs/unknowns/` that explains the failure by its id, and the person who signed it. A route's own `unknowns` field is never what this means; a measurable record with an omission has none by construction. The summary reports raw misses and adjudicated misses side by side, never subtracts silently, and the criterion caps adjudications.
- **G8, the comparator is known to see failures.** Before a class's clean count means anything, the ledger must contain one canary for that class: a pull request on a branch named `canary/<class-rule-ids>/<date>`, never merged, whose change of that class deliberately breaks an omitted gate, and whose record shows `routing_miss` true. Provenance is derived by the deterministic step from the branch name in the event payload, not from a label; the summary lists canaries by record id, and ingest refuses a canary whose head is an ancestor of `main`. This is the mutation-row principle applied to the measurement.
- **G9, the summary is reproducible.** `metrics/shadow/summary.json` is generated from the ledger bytes by a standard-library command with sorted keys, no timestamps, and records ordered by id, as `metrics/summary.json` is today; a test regenerates it and compares bytes. `metrics/shadow/**` and `metrics/schemas/*.json` carry `text eol=lf` in `.gitattributes` before the first record, so a Windows checkout reads the same bytes, per D-114.
- **G10, the artifact is a hint.** The record is built by the pull request's own workflow, so a pull request that edits `tests.yml` could upload anything. Ingest recomputes the route from the recorded merge commit and reads the outcomes from the API for the recorded run and attempt, and refuses a record whose recomputation disagrees.

## 5. Where the records live

Q-003 asked whether tallies live in `.anti-dark-code/runs/` or `metrics/`. The answer is `metrics/`, fed by artifacts, with the artifact as inbox only.

- **Per change, in CI.** A new non-required job `shadow` in `tests.yml`, `needs` every gate job, `if: always()`, with `actions: read`. It checks out the merge ref with the base fetched, computes the route and candidate, reads the run's job and step conclusions for its own attempt, builds the record, validates it against the schema, and uploads `shadow-<head_sha>-<run_attempt>.json`. Fork pull requests carry a read-only token; whether their artifacts upload is one of the implementer's first measurements.
- **Durably, in the repository.** `metrics/shadow/ledger/<yyyy-mm>.jsonl`, append-only, one record per line, with `metrics/schemas/shadow-record-v2.schema.json`, whose number continues `shadow_result`'s existing `schema_version` 2. A record's id is the SHA-256 of its canonical bytes without the id field. `adc.py shadow ingest` fetches artifacts newer than the ledger's last record, recomputes each per G10, and appends; `adc.py shadow summary` regenerates `metrics/shadow/summary.json`. Both are run by a person or by Sonnet 5 inside the artifact retention window, which is ninety days by default, and committed like any other change; a change under `metrics/shadow/` routes unmapped and forces full, so every ingest runs the full recipe.
- **Option B, not recommended.** The workflow appends to a `shadow-ledger` branch itself with `contents: write`. The design challenge measured why not: a fork's read-only token gets no record, a same-repository pull request's own workflow could rewrite the branch, and the ledger becomes something no person committed.
- **Backfill.** `adc.py shadow backfill --since <sha>` replays merged pull requests whose heads have a recorded run: today's router and today's policy over each historical change set, outcomes from the run that verified that head, keyed by today's digests. It is not a reconstruction at each head, because the candidate builder did not exist at PRs #21 and #22 and the policy blob differed across the stack, so per-head keys would be classes of one. Records carry `provenance: backfill`; heads older than the workflow, which landed 2026-08-22, are not measurable. The summary reports live and backfill counts separately.

## 6. The approval criterion, as a proposal

Per class key, all of the following, evaluated by the summary and read by a person:

1. at least N live clean records;
2. zero unadjudicated misses, and at most A adjudicated misses, each naming a passing rerun at the same head and a recorded unknown by id;
3. one canary miss recorded for the class, section 4;
4. records spanning at least D days and at least two distinct authors, which the summary reports, so a burst by one author in one week does not stand for a season;
5. no change to the class key since the oldest counted record, which the key enforces.

ENGINEERING's rule of three gives the perspective; the design challenge checked it against the exact bound at zero misses: 30 records bound the miss rate near 10 percent, 100 near 3 percent, 300 near 1 percent. The cost column is this repository's measured rate, not a guess: of the 45 first-parent changes on `main` since 2026-08-06, 35 force full and 10 route `docs-only`, and only one of those, PR #31, has a run under the workflow that landed on 2026-08-22. Of the eleven round pull requests, one is `docs-only`. At that rate no option is reached in months; the campaign's early product is the class mix, the canaries, and the machinery, and approval waits on traffic.

| Option | N | A | D | What zero misses bounds | This repository's rate |
| --- | --- | --- | --- | --- | --- |
| 1, recommended as the first milestone | 30 | 1 | 30 days | about 10 percent | about a year of `docs-only` changes at today's rate |
| 2 | 100 | 1 | 60 days | about 3 percent | several years |
| 3 | 300 | 0 | 90 days | about 1 percent | not reachable at today's rate |

The recommendation is option 1 for `docs-only` as a milestone, with SLICE-003's automatic escalation on any miss as the real safety net, and with one caveat the design challenge found: `design/routing/*.md` routes `docs-only` today, and the suite's decision guard reads those files, so a design document citing an unrecorded decision id is a real `routing_miss` for the class. The first canary is expected to be that miss. Until the policy's classifier stops grading prose the suite reads as `docs`, the `docs-only` class cannot meet criterion 2 honestly, and narrowing that entry is an owner decision to record before the campaign counts anything, in the shape D-107 took. Meeting the criterion approves nothing; it makes the approval review possible.

## 7. In scope, with build order

| Item | What | Holds it |
| --- | --- | --- |
| M1 | The run store ignores itself; a rule that names no obligation is refused at load; `metrics/shadow/**` and `metrics/schemas/*.json` get `eol=lf` | tests, mutation rows, decisions |
| M2 | `adc.py shadow record --repo --base --merge --head --pr --run --attempt --outcomes <json> --out <path>`: measurability check, route, candidate, class key, record id, schema `shadow-record-v2` | tests for S-052 to S-055; rows for the miss condition, the measurability check, and the class key |
| M3 | Workflow job `shadow`, non-required, `if: always()`, `actions: read`, merge-ref checkout with the base fetched, API read with `filter=all`, gate-to-job mapping as data, artifact named by head and attempt | workflow contract tests for S-058 and the mapping; the D-011 check that `required` is unchanged; the fork-token measurement |
| M4 | `adc.py shadow ingest` with recomputation and refusals, `adc.py shadow summary`, `metrics/shadow/`, the adjudications file's shape | tests for S-056, S-057, S-059, S-061 |
| M5 | `adc.py shadow backfill --since` with today's router and policy; a real backfill of every merged pull request with a run, committed | test on a fixture; S-060 |
| M6 | The canary procedure and one canary per class the backfill shows, on `canary/` branches, never merged | the canary records; S-062 |

Each item cites the decision the implementer records for it; none cites a decision that does not yet exist.

## 8. Out of scope, on purpose

- Any selective execution, local or CI, per D-011 and SLICE-003.
- Approving a rule, changing the `required` aggregator, or changing the canonical set.
- Narrowing the `docs-only` classifier; that is the owner's decision, recorded before the campaign counts.
- Measuring consumer repositories; this campaign measures this repository's own changes.
- Measuring pushes to `main` separately from the pull requests that produced them.

## 9. Acceptance criteria

| Id | Condition |
| --- | --- |
| S-052 | Given a clean tree, when `route --write` runs, then no emitted fact's path starts with `.anti-dark-code/`. |
| S-053 | Given outcomes in which one omitted gate failed and every selected gate passed, when the record is built, then `routing_miss` is true. |
| S-054 | Given the same change with a selected gate failed, then the record is inconclusive, not a miss, and its `missed_gate_ids` are kept. |
| S-055 | Given outcomes missing any canonical gate, or carrying `not-run`, `skipped`, `stale`, or `config-error` for one, when the record is built, then it is not measurable and `routing_miss` is absent. |
| S-056 | Given a record whose merge sha is not the run's checked-out commit, or whose recomputation disagrees, when ingested, then it is refused with the reason recorded. |
| S-057 | Given the ledger bytes, when the summary runs twice, then the outputs are byte-identical. |
| S-058 | Given the workflow file, then the `shadow` job is absent from `required`'s `needs`, carries `if: always()`, and names every canonical gate in its mapping. |
| S-059 | Given a change on a `canary/` branch, when recorded, then `provenance` is `canary`, derived from the payload, and the summary counts it in neither clean nor miss totals; given a canary head that is an ancestor of `main`, ingest refuses it. |
| S-060 | Given a backfilled pull request, when recorded, then its route is computed by today's router and policy over its historical change set, and its outcomes are the run that verified its head. |
| S-061 | Given two records whose class keys differ only in the router blob sha, when the summary runs, then they are never counted into one class; given two whose policies differ only in a `_note`, they are. |
| S-062 | Given a rule with no obligations, when the policy loads, then it is refused. |

## 10. Agent guardrails for this build

- The implementer does not change a definition in sections 2 through 6 without a decision entry that names this document; a definition changed silently is the self-grading defect this slice exists to avoid.
- A challenger runs once against the implementation; repairs are held by tests and rows, not by re-challenging repairs, per the cap round twenty-one recorded.
- No agent adjudicates a miss. Adjudication is signed by a person.
- Stop and ask before: adding a rule, approving a rule, narrowing a classifier entry, touching `required`, or writing to the repository from CI.

## 11. Slice definition of done

- [ ] M1 through M6 landed with their tests, rows, and decisions, on main.
- [ ] The backfill of every merged pull request with a run is in the ledger, with the class mix recorded in the handoff.
- [ ] One canary per class present in the backfill is recorded, and the `docs-only` canary's result is recorded whichever way it went.
- [ ] The first live record exists, from a pull request opened after the workflow landed.
- [ ] The summary is reproducible and reviewed by a person.
- [ ] A fresh-context challenge of the implementation held or was repaired under the cap.
- [x] The owner has chosen N, A, and D, the storage option, and whether to narrow `docs-only` before counting: section 13, 2026-09-03.

## 12. What this unlocks

SLICE-003, selective local execution for the first class that meets the criterion, with automatic escalation on any miss, after the top-tier approval review. Selective CI stays behind both, per D-011.

## 13. Decisions taken by the owner

Daniel Boyd took these on 2026-09-03, on the recommendations the design's author made after the challenge. Each is a decision the implementer records in the log with the item it lands in, citing this section.

1. **The criterion is option 1 as a milestone, not a certification.** N is 30 live clean records, A is at most one adjudicated miss, D is 30 days with at least two authors. Zero misses at that size bounds the class's miss rate near 10 percent; SLICE-003's automatic escalation on any miss is the safety net, and the number can be raised once a class reaches it.
2. **Storage is option A.** Each run uploads its record as an artifact; `shadow ingest`, run by a person or by Sonnet 5 inside the artifact retention window, recomputes every record from the merge commit and the API before appending it to the committed ledger under `metrics/shadow/`. Option B is not built.
3. **`docs-only` is not narrowed before counting.** The first canary for the class records the expected miss, a design document citing an unrecorded decision id, as evidence; the narrowing of the classifier is then decided on that record, in the shape D-107 took, not on prediction.
4. **Backfilled records never count toward N.** They inform the class mix and catch design errors on the first day, and the summary reports them beside the live count, never inside it.
5. **One canary per class key.** The key already changes when the rule's terms, the classifier, the canonical set, or the router change, which is exactly when the comparator could have gone blind for that class; a policy edit that leaves the key unchanged needs no new canary.

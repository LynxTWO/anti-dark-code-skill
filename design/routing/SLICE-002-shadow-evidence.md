# Assurance Router Slice Brief: SLICE-002 shadow evidence campaign

Version: 0.5. Date: 2026-09-04. Status: Proposed, design only, revised once after the fresh-context challenge recorded in `CHALLENGE-SLICE-002-DESIGN.md`, once after the field study recorded in `FIELD-STUDY-SLICE-002.md` under D-128 to D-130, once more after the challenge of that revision recorded in `CHALLENGE-SLICE-002-R2.md`, and a fourth time after the implementation and its challenge, recorded in `HANDOFF-BACK-SLICE-002-IMPL-R2.md`, under D-133 to D-135. Designed by Claude Fable 5.1 per the owner's model sequence; implemented by Opus 5 from `HANDOFF-OPUS-SLICE-002.md` and, for the revision, `HANDOFF-OPUS-SLICE-002-R2.md`; the campaign's summaries by Sonnet 5; the approval review by the top tier.
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
- **G8, the comparator is known to see failures.** Before a class's clean count means anything, the ledger must contain one canary for that class: a pull request on a branch named `canary/<class-rule-ids>/<date>`, never merged, whose change of that class deliberately breaks an omitted gate, and whose record shows `routing_miss` true. Provenance is derived by the deterministic step from the branch name in the event payload, not from a label; the summary lists canaries by record id, and ingest refuses a canary whose head is an ancestor of `main`. This is the mutation-row principle applied to the measurement. A class no gate reads cannot produce a canary, and is approved by the dominance proof of section 6 instead, whose probes are canaries generated exhaustively rather than one built by hand (D-134).
- **G9, the summary is reproducible.** `metrics/shadow/summary.json` is generated from the ledger bytes by a standard-library command with sorted keys, no timestamps, and records ordered by id, as `metrics/summary.json` is today; a test regenerates it and compares bytes. `metrics/shadow/**` and `metrics/schemas/*.json` carry `text eol=lf` in `.gitattributes` before the first record, so a Windows checkout reads the same bytes, per D-114.
- **G10, the artifact is a hint.** The record is built by the pull request's own workflow, so a pull request that edits `tests.yml` could upload anything. Ingest reads the outcomes from the API for the recorded run and attempt and recomputes the verdict from them; it then recomputes the class, with the policy and gates the record's digests name, kept by digest under `metrics/shadow/policies/`, and the router whose blob digest the record names, read at the record's head commit, over the change set acquired from the recorded base and head; it refuses a record whose outcomes, verdict, matched rules, selected or omitted gates, or class key disagree, and one whose policy or router cannot be recovered (D-133).

## 5. Where the records live

Q-003 asked whether tallies live in `.anti-dark-code/runs/` or `metrics/`. The answer is `metrics/`, fed by artifacts, with the artifact as inbox only.

- **Per change, in CI.** A new non-required job `shadow` in `tests.yml`, `needs` every gate job, `if: always()`, with `actions: read`. It checks out the merge ref with the base fetched, computes the route and candidate, reads the run's job and step conclusions for its own attempt, builds the record, validates it against the schema, and uploads `shadow-<head_sha>-<run_attempt>.json`. Fork pull requests carry a read-only token; whether their artifacts upload is one of the implementer's first measurements.
- **Durably, in the repository.** `metrics/shadow/ledger/<yyyy-mm>.jsonl`, append-only, one record per line, with `metrics/schemas/shadow-record-v2.schema.json`, whose number continues `shadow_result`'s existing `schema_version` 2. A record's id is the SHA-256 of its canonical bytes without the id field. `adc.py shadow ingest` fetches artifacts newer than the ledger's last record, recomputes each per G10, and appends; `adc.py shadow summary` regenerates `metrics/shadow/summary.json`. Both are run by a person or by Sonnet 5 inside the artifact retention window, which is ninety days by default, and committed like any other change; a change under `metrics/shadow/` routes unmapped and forces full, so every ingest runs the full recipe.
- **The policy that built a record.** Every producer writes, beside its record, the stripped policy and gates it used, named by their own digests: `policy-<policy_terms_sha256>.json` and `gates-<gates_terms_sha256>.json`. The live job uploads them in the artifact; the backfill writes them to its output directory. Ingest copies each into `metrics/shadow/policies/` after checking that the content digests to the name, never rewrites one already present, and refuses a file that does not digest to its name. These are what G10's class recomputation loads; a live record whose file is missing everywhere is recovered once from the calibration at its head commit (D-133).
- **A consumer repository.** A repository that installs the campaign carries the skill at a version shipping `adc_shadow.py`, its own calibration with every rule `proposed`, its own `.github/shadow-gate-map.json`, and the `shadow` job from `assets/templates/shadow-job.yml` with `needs` naming its gate jobs. Its evidence lives here, under `metrics/shadow/consumers/<owner>-<name>/` in this same shape, ingested from a clone of the consumer with `--repo <clone> --repository <owner>/<name>` and `--ledger` naming that directory. Nothing under `metrics/` is written to the consumer, and its calibration is authored for it, never transplanted (D-135). The first consumer is 1st-downs, section 12.
- **Option B, not recommended.** The workflow appends to a `shadow-ledger` branch itself with `contents: write`. The design challenge measured why not: a fork's read-only token gets no record, a same-repository pull request's own workflow could rewrite the branch, and the ledger becomes something no person committed.
- **Backfill.** `adc.py shadow backfill` enumerates merged pull requests and replays every run attempt of the CI workflow each produced under the `pull_request` event, superseded heads and attempts included: today's router and today's policy over the pull request's head against `merge-base(head, landing^1)`, the fork point of the head and the base branch as it stood at the merge, which is the same commit a three-dot diff uses and differs from `landing^1` itself whenever the base branch moved after the branch was cut, outcomes from that attempt, one record per head and attempt, keyed exactly as the live artifacts are. The runs are found through the runs listing joined on head repository and branch, with `/commits/{sha}/pulls` for the rest, because a merged branch's runs no longer name their pull request; a head whose commit is gone is recorded `not_measurable` with reason `head-unavailable`; a head and attempt with a live record is never backfilled. It is not a reconstruction at each head, because the candidate builder did not exist at PRs #21 and #22 and the policy blob differed across the stack, so per-head keys would be classes of one. The merge that survived a pull request is never the population: the field study measured it as survivorship, and the challenge of the revision re-derived it like for like, since on vitejs/vite lint failed on none of 216 push runs for merges and in 57 of 309 pull-request runs, one of them a routed miss for the very route the merges showed twelve clean records for (D-128). The merge commit a run checked out is not recoverable later, so a backfill record carries `base_reconstructed: true`, and the base's own push run supplies its `base_outcomes`. Sections 2, G2 and G10 describe live records; a backfill record's commits come from the API and the landing commit, and ingest verifies it by recomputation against its recorded head and base. Records carry `provenance: backfill`; heads older than the workflow, which landed 2026-08-22, are not measurable. The summary reports live and backfill counts separately, and backfill never counts toward N.

## 6. The approval criterion, as a proposal

Per class key, all of the following, evaluated by the summary and read by a person:

1. at least N pull requests that, in this class, have at least one clean live record and no miss, a pull request counting once however many times it ran; an inconclusive record neither adds nor removes, and N is a count that can fall when a later attempt misses, not a clock (D-128);
2. zero unadjudicated misses, and at most A adjudicated misses, each naming a passing rerun at the same head and a recorded unknown by id;
3. one canary miss recorded for the class, section 4, unless the class is dominated, below;
4. records spanning at least D days and at least two distinct authors, which the summary reports, so a burst by one author in one week does not stand for a season;
5. no change to the class key since the oldest counted record, which the key enforces.

ENGINEERING's rule of three gives the perspective; the design challenge checked it against the exact bound at zero misses: 30 records bound the miss rate near 10 percent, 100 near 3 percent, 300 near 1 percent. The cost column is this repository's measured rate, not a guess: of the 45 first-parent changes on `main` since 2026-08-06, 35 force full and 10 route `docs-only`, and only one of those, PR #31, has a run under the workflow that landed on 2026-08-22. Of the eleven round pull requests, one is `docs-only`. That mix was measured over merges, a population D-128 retires; the pull-request mix replaces it once M5 is rebuilt. At that rate no option is reached in months; the campaign's early product is the class mix, the canaries, and the machinery, and approval waits on traffic.

| Option | N | A | D | What zero misses bounds | This repository's rate |
| --- | --- | --- | --- | --- | --- |
| 1, recommended as the first milestone | 30 | 1 | 30 days | about 10 percent | about a year of `docs-only` changes at today's rate |
| 2 | 100 | 1 | 60 days | about 3 percent | several years |
| 3 | 300 | 0 | 90 days | about 1 percent | not reachable at today's rate |

The recommendation is option 1 for `docs-only` as a milestone, with SLICE-003's automatic escalation on any miss as the real safety net. The caveat the design challenge found was measured by the canary: `design/routing/*.md` routed `docs-only`, the suite's decision guard reads those files, and PR #35, a design document citing an unrecorded decision id, recorded the miss. The owner then narrowed the classifier on that record: `design/routing/*.md` is verification authority in this repository's calibration (D-129), the glob spelled with one `*` because the router's `fnmatchcase` has no `**`, so the class can meet criterion 2 honestly, and every class key restarted while no record worth keeping existed. Two further facts from the field study bound what the criterion can conclude. N counts pull requests, not records, because one pull request can run eight times (D-128). And this repository has one author, so criterion 4 is never met from its own history; the class mix here is the campaign's early product, and conclusions come from repositories with two or more authors, measured read-only (D-130). Meeting the criterion approves nothing; it makes the approval review possible.

**The second path: dominance.** A class whose covered paths no omitted gate reads cannot produce a canary, and its clean records prove only that nothing happened. Such a class is approved instead by a dominance proof (D-134): `adc.py shadow dominance --class-key <key>` enumerates every path in the tree the class's classifier entries cover, runs the full recipe with every one of them deleted, then again with every one of them replaced by content that is not the original, and records every gate's conclusion each time. The class is dominated when neither probe produces a selected gate passing while an omitted gate fails; a dominated class needs neither criterion 1 nor criterion 3, because the proof is the comparator seeing every failure the class can cause and finding each caught by a selected gate or caused by nothing. A probe that produces a miss makes the class not dominated, and that probe's record is then the class's canary for the statistical path. The proof is an approval-time act, re-run whenever the class key changes, and its records carry `provenance: dominance`, listed by the summary beside canaries and counted in neither N nor the misses. This repository's `docs-only` class is expected to take this path once the suite stops reading `docs/review/adversarial-pass.md`, and the calibration templates, which `distribution` reads and `validate-core` also reads, are the case the second probe exists to grade.

## 7. In scope, with build order

| Item | What | Holds it |
| --- | --- | --- |
| M1 | The run store ignores itself; a rule that names no obligation is refused at load; `metrics/shadow/**` and `metrics/schemas/*.json` get `eol=lf` | tests, mutation rows, decisions |
| M2 | `adc.py shadow record --repo --base --merge --head --pr --run --attempt --outcomes <json> --out <path>`: measurability check, route, candidate, class key, record id, schema `shadow-record-v2` | tests for S-052 to S-055; rows for the miss condition, the measurability check, and the class key |
| M3 | Workflow job `shadow`, non-required, `if: always()`, `actions: read`, merge-ref checkout with the base fetched, API read with `filter=all`, gate-to-job mapping as data, artifact named by head and attempt | workflow contract tests for S-058 and the mapping; the D-011 check that `required` is unchanged; the fork-token measurement |
| M4 | `adc.py shadow ingest` with recomputation and refusals, `adc.py shadow summary` counting pull requests per class, `metrics/shadow/`, the adjudications file's shape; built after M5 is rebuilt, by the owner's ninth decision | tests for S-056, S-057, S-059, S-061, S-065 |
| M5 | `adc.py shadow backfill` over merged pull requests' run history: runs found through the listing joined on head repository and branch; one record per head and attempt, superseded attempts included; base `merge-base(head, landing^1)`; `base_reconstructed: true` in the record, the schema and the validator together; `base_outcomes` from the base's push run; `head-unavailable` recorded, not dropped; a head and attempt with a live record skipped; the merge-commit replay retired; a real backfill of this repository's pull requests, committed | test on a fixture with several attempts, one failing, on a merge-commit history; S-060, S-063; D-128 |
| M6 | The canary procedure and one canary per class the backfill shows, on `canary/` branches, never merged | the canary records; S-062 |
| M7 | `design/routing/*.md` classified verification authority in the repository calibration, the glob being `*` because the router's `fnmatchcase` crosses `/` and `**/*` would miss the top-level files; the `docs-only` canary re-run under the new class key, on a `canary/` branch that changes prose no gate reads | the classifier test on a top-level file; S-064; D-129; the new canary record |
| M8 | The policy and gates a record was built with, written by its digest beside the record by the live job and the backfill; `metrics/shadow/policies/` filled by ingest from self-certifying files; ingest recomputes the class with the stored policy and the router at the record's head, and refuses disagreement or an unrecoverable input | S-066; R-064; D-133 |
| M9 | The counterexample test asserts the classifier, not the tree, and reads no file under `docs/`; `adc.py shadow dominance --class-key` with its two probes and `provenance: dominance`; the summary lists dominance records beside canaries and counts neither | S-067, S-068; R-065, R-066; D-134 |
| M10 | The consumer kit: `references/shadow-evidence.md` listed in SKILL.md, `assets/templates/shadow-job.yml`, `assets/templates/shadow-gate-map.json`, the CHANGELOG entry naming them, and ingest's consumer ledger path | S-069; R-067; D-135 |
| M11 | 1st-downs' pull request, with its owners: the skill upgraded, the proposal under `design/routing/consumers/JeremyABurton-1st-downs/` copied in as its calibration and map, the job added with `needs: [test]`, its required check untouched; the first live record ingested under `metrics/shadow/consumers/JeremyABurton-1st-downs/` | the first consumer record; D-135 |

Each item cites the decision the implementer records for it; none cites a decision that does not yet exist.

## 8. Out of scope, on purpose

- Any selective execution, local or CI, per D-011 and SLICE-003.
- Approving a rule, changing the `required` aggregator, or changing the canonical set.
- Narrowing any classifier entry other than the one D-129 names.
- Installing anything in a consumer repository. Read-only field studies of other repositories are how the campaign is checked against traffic it cannot generate; their results live in `FIELD-STUDY-SLICE-002.md`.
- Sampled full runs (D-130); they are SLICE-003's precondition, and nothing here executes selectively.
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
| S-063 | Given a merged pull request on a merge-commit history with three run attempts, one of which failed an omitted gate, when backfilled, then three records exist, keyed by head and attempt, each carrying `provenance: backfill` and `base_reconstructed: true`, each with a non-empty change set taken against `merge-base(head, landing^1)`, and the failing attempt's record is a miss; given a head whose commit no longer exists, then its record is `not_measurable` with reason `head-unavailable`. |
| S-064 | Given a change to `design/routing/DECISION-LOG.md` alone, a top-level file, and separately to a file one directory below, when routed under this repository's calibration, then each emits a fact with effect `verification-authority` and the route forces full. |
| S-065 | Given one pull request with eight clean measurable records in a class, when the summary counts N, then the class advances by one; given the same pull request with one miss among them, then the class has a miss and N does not advance; given one inconclusive record among them, then N advances by one and nothing is a miss. |
| S-066 | Given a record whose class block names a rule the stored policy would not have matched for its change set, or whose policy file is absent and, for a backfill, unrecoverable, or whose router blob is not at its head, when ingested, then it is refused naming the disagreement; given a policy file whose content does not digest to its name, then it is refused and not copied. |
| S-067 | Given the installed calibration, when the self-grading counterexample test runs, then it asserts that its path matches a prose entry and no authority entry, and no test in the suite opens a file under `docs/`. |
| S-068 | Given a class whose covered paths no omitted gate reads, when the dominance probe runs, then both probes pass every gate and the class is recorded dominated; given a class where an omitted gate fails a probe while every selected gate passes, then that probe's record is a miss with `provenance: dominance` and the class is not dominated. |
| S-069 | Given a clone of a consumer repository and its slug, when ingest runs with `--ledger metrics/shadow/consumers/<owner>-<name>/ledger`, then records verify against the consumer's API and its calibration at each record's head, the ledger and policies land under that directory, and nothing in the clone changes. |

## 10. Agent guardrails for this build

- The implementer does not change a definition in sections 2 through 6 without a decision entry that names this document; a definition changed silently is the self-grading defect this slice exists to avoid.
- A challenger runs once against the implementation; repairs are held by tests and rows, not by re-challenging repairs, per the cap round twenty-one recorded.
- No agent adjudicates a miss. Adjudication is signed by a person.
- Stop and ask before: adding a rule, approving a rule, narrowing a classifier entry, touching `required`, or writing to the repository from CI.

## 11. Slice definition of done

- [ ] M1 through M7 landed with their tests, rows, and decisions, on main.
- [ ] The backfill of every merged pull request with a run is in the ledger, with the class mix recorded in the handoff.
- [ ] One canary per class present in the backfill is recorded, and the `docs-only` canary's result is recorded whichever way it went.
- [ ] The first live record exists, from a pull request opened after the workflow landed.
- [ ] The summary is reproducible and reviewed by a person.
- [ ] A fresh-context challenge of the implementation held or was repaired under the cap.
- [x] The owner has chosen N, A, and D, the storage option, and whether to narrow `docs-only` before counting: section 13, 2026-09-03.
- [ ] The backfill has been re-run over pull-request run history and the merge-commit records are retired (D-128).
- [ ] The `docs-only` canary under the narrowed classifier is recorded (D-129).
- [x] The owner has decided the backfill population, the narrowing, the campaign's product, M4's timing, and PR #34's disposition: section 13, items 6 to 10, 2026-09-03.
- [ ] Ingest recomputes the class with the policy that built each record (D-133), and the six inbox records and two canaries re-verify under it.
- [ ] The suite reads no repository prose, and the `docs-only` class here has a dominance record (D-134).
- [ ] The shipped skill documents the campaign and carries the consumer templates (D-135).
- [ ] 1st-downs' first live record is ingested under `metrics/shadow/consumers/JeremyABurton-1st-downs/`.
- [x] The owner has decided the policy store, the dominance path, the consumer arrangement, and the first consumer: section 13, items 11 to 14, 2026-09-04.

## 12. What this unlocks

SLICE-003, selective local execution for the first class that meets the criterion, with automatic escalation on any miss, after the top-tier approval review. Selective CI stays behind both, per D-011. SLICE-003 inherits D-130 before it inherits selective execution: a rate in the policy named `sample_every`, a sample chosen after routing as a deterministic function of the class key and the pull request number and recorded in the run, a `sampled` provenance the deterministic step derives from that record and never from a label, and the rule that a class without sampled records after execution starts has a stopped clock. None of that exists in SLICE-002, not even the enum value. The field study's reason is plain: the moment a skip is taken, the measurement that justified it goes blind unless something keeps running the full recipe on purpose.

Before SLICE-003, the campaign's first consumer. This repository has one author and cannot meet criterion 4; 1st-downs has two, 45 pull requests, and a history in which every record was measurable, and its owners have agreed to install the job. It is the first campaign that can reach N, and the first place the audit product D-130 names is measured rather than argued (D-135). Its time prize is nothing, a 34-second CI, and that is the point: the graded record is the product.

## 13. Decisions taken by the owner

Daniel Boyd took these on 2026-09-03, on the recommendations the design's author made after the challenge. Each is a decision the implementer records in the log with the item it lands in, citing this section.

1. **The criterion is option 1 as a milestone, not a certification.** N is 30 live clean records, restated by item 6 as 30 pull requests each counted once, A is at most one adjudicated miss, D is 30 days with at least two authors. Zero misses at that size bounds the class's miss rate near 10 percent; SLICE-003's automatic escalation on any miss is the safety net, and the number can be raised once a class reaches it.
2. **Storage is option A.** Each run uploads its record as an artifact; `shadow ingest`, run by a person or by Sonnet 5 inside the artifact retention window, recomputes every record from the merge commit and the API before appending it to the committed ledger under `metrics/shadow/`. Option B is not built.
3. **`docs-only` is not narrowed before counting.** The first canary for the class records the expected miss, a design document citing an unrecorded decision id, as evidence; the narrowing of the classifier is then decided on that record, in the shape D-107 took, not on prediction.
4. **Backfilled records never count toward N.** They inform the class mix and catch design errors on the first day, and the summary reports them beside the live count, never inside it.
5. **One canary per class key.** The key already changes when the rule's terms, the classifier, the canonical set, or the router change, which is exactly when the comparator could have gone blind for that class; a policy edit that leaves the key unchanged needs no new canary.

Daniel Boyd took these later the same day, after the field study in `FIELD-STUDY-SLICE-002.md`, again on the author's recommendations with the alternatives stated.

6. **The backfill grades pull-request run history, superseded attempts included.** A merge commit is survivorship: on vite, lint failed on none of 216 push runs for merges and in 57 of 309 pull-request runs, one of them a routed miss. The merge-commit replay is retired; D-128.
7. **`docs-only` is narrowed now.** `design/routing/*.md` is verification authority in this repository's calibration, on the canary's evidence; every class key restarts while that costs nothing; the class gets a new canary under its new key; D-129.
8. **Routing's product is audit, not speed, and a skipped class keeps a sampled full run.** Four repositories showed the safe skips already taken by hand and the remaining saving to be a lint job; what the router has that a path filter lacks is the graded record. SLICE-003 inherits the sampling rate and the `sampled` provenance before selective execution; D-130.
9. **M4 waits.** The ledger and summary are built after D-128's backfill and its pull-request count exist, so they are built once.
10. **PR #34 merges as it stands; design changes stack on it.** PR #35 stays open and unmerged as the old class's canary.

Daniel Boyd took these on 2026-09-04, after the implementation and its challenge, on the author's recommendations.

11. **The policy that built a record is kept by its digest, and ingest recomputes the class with it.** The laundering repair recomputed the verdict and not the class; the class is a claim until the policy is at hand. Producers write the policy beside the record, ingest keeps it under `metrics/shadow/policies/`, and the router is read at the record's head; D-133.
12. **The suite reads no repository prose, and a class no gate reads is approved by dominance.** The counterexample test asserts the classifier, not the tree. A class the gates cannot see is approved by an exhaustive probe rather than one hand-built canary and a sample; D-134.
13. **A consumer carries the job, the map and its calibration; its evidence lives here.** 1st-downs is the first consumer, with its owners' consent; nothing under `metrics/` is written to it and nothing of this calibration is transplanted; D-135.
14. **The shipped skill documents the campaign as a supporting reference, not a pass.** `references/shadow-evidence.md` and the two templates ship with a changelog entry that names them; D-135.

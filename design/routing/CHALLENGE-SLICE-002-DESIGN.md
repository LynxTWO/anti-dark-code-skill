# Challenge of the SLICE-002 design, and what it changed

Challenger: a fresh-context agent with no memory of writing the brief, dispatched on 2026-09-03 against version 0.1 of `SLICE-002-shadow-evidence.md` and the code at `fe350e92ce4082f6c4c57813d37bead32cac2367`, working in its own clones under `J:\TEMP\claude\slice2-challenger\`. It ran no gate, suite, or replay, and wrote no fixes. Per the cap round twenty-one recorded, this is the one challenge of the design; version 0.2 of the brief closes what it found, and the implementer's handoff lists what stayed open. The report is reproduced below, followed by the closures.

## Verdicts

| Item | Verdict | One line |
|---|---|---|
| 1. Self-grading | BROKEN (G2, G6; G1's read path; artifact naming); G3, G4, G7, G9 uphold with caveats; G5, G8 partial | CI verifies `refs/pull/N/merge`, not the head, so G2's refusal is either vacuous or refuses everything; a default checkout leaves the base unreachable so nothing is measurable; an absent gate key reads as clean; reruns replace attempts under `filter=latest` and artifact overwrite; approving a rule changes the policy bytes and resets every class. |
| 2. The miss definition | BROKEN | `shadow_result` counts `not-run`, `skipped`, and `stale` omitted outcomes as missed and an absent key as clean, so the brief's "not measurable" is a rule to add in front of it; a rule with no obligations loads and selects nothing; base-caused and infrastructure failures have no path; the rerun adjudication would erase nondeterministic defects. |
| 3. The class key | BROKEN | A `_note` edit, an unrelated rule, or an approval each change the policy byte digest and reset every class; a router-only change resets nothing; the receipt already carries two different policy digests and the brief did not choose. |
| 4. The criterion | arithmetic UPHELD; cost column BROKEN; canary constructible but gameable | Rule of three matches the exact bound; of 45 first-parent changes since 2026-08-06, 35 force full and 10 are `docs-only`, one of them with a run under the workflow; a design document citing an unrecorded decision id is a real `routing_miss` for `docs-only`; a free `provenance` label is the G7 defect by another door. |
| 5. Run store pollution | BROKEN today; the self-ignoring store is the right fix | Reproduced: `route --write` on a clean tree carries `.anti-dark-code/.gitignore` as an unmapped fact; ignoring the directory in the repository's `.gitignore` hides a new `.anti-dark-code/calibration/`; excluding it in the router reopens D-089's blindness. |
| 6. Backfill validity | partly BROKEN | The candidate builder is absent at PRs #21 and #22 and the policy blob differed across the stack, so "at its own head" yields classes of one; run conclusions for #21, #25, and #31 are readable; #31 is the one `docs-only` change with a run. |
| 7. Storage | choose A, with a recomputing ingest | Artifacts expire; a pull request's own workflow can upload anything; option B gives fork pull requests no record and lets a same-repository pull request rewrite the branch. |
| 8. What the design forgot | BROKEN on line endings and schema | No `eol=lf` on `metrics/shadow/**`; `shadow_result` already emits `schema_version` 2; no record id; the verified merge sha is a regenerable object; `run_attempt` absent from the artifact name; `actions` scope is none under the current `permissions`. |

## What the challenger measured

The job log of run 33695078288, PR #31: `git checkout --progress --force refs/remotes/pull/31/merge`, `HEAD is now at f9a9b4b Merge 49ba966 into cd6704a`, `fetch-depth: 1`. All twelve runs for PR heads #21 to #32 are `pull_request` events verifying the merge ref. A `--depth 1` clone routed with `--base de5ef1d`: `force_full=true complete=false`, `ADC-ROUTE-BASE-UNREACHABLE`, so `build_candidate_route` returns `None`. Run 33683890541 at `ec1dbe2b`: `jobs?filter=all` shows attempt 1 with `Hostile environment (C locale)` and `Tests` failed and attempt 2 all success; `filter=latest` shows only attempt 2. A docs-only candidate given `{"validate-core": "pass"}` alone: `measurable=True routing_miss=False omitted_gate_results={}`. The outcome matrix for the docs-only candidate: `full-suite fail` gives a miss; `validate-core` and `full-suite` both failed gives inconclusive; `full-suite not-run`, `skipped`, or `distribution stale` each give `routing_miss=True measurable=True`. Policy digests: shipped `8a72b7c4`; a `_note` edit `37dab43a`; `docs-only` approved `9d310bdc`; an unrelated rule added `d5e0235c`; a semantic digest over `match`, `requires`, and `obligations` stayed `7b9de4db` for the note edit. Router blob `0ded8104` on `main` versus `84b32879` on the branch. `route --write` on a pristine clone: receipt `changed_files` = `.anti-dark-code/.gitignore` untracked, unknowns `ADC-ROUTE-UNMAPPED-PATH` and `ADC-ROUTE-UNROUTED-FACT`; with the store ignoring itself, `ls-files --others` empty and `ROUTE level=0`, while a new `.anti-dark-code/calibration/gates.json` still forces full. `check-attr` on `metrics/shadow/ledger/2026-09.jsonl` returns nothing, and an `autocrlf=true` checkout of an LF commit of it came back with two CR bytes and a different digest. The exact zero-miss bound at N of 30, 100, and 300 is 0.0950, 0.0295, and 0.0099 against the rule of three's 0.10, 0.03, and 0.01. `metrics/summary.json` regenerated byte-for-byte under Python 3.14. `design/routing/DECISION-LOG.md` and `ENGINEERING.md` route `docs-only`, `test_route.py` scans `design/routing/**/*.md` for decision ids, and `validate --mode universal` never reads `design/`.

## Closures in version 0.2

| Finding | Closure |
| --- | --- |
| Merge ref, not head | Section 2 and G2: the change is base-at-run-time to the merge commit CI checked out; the record carries merge, head, base, run, attempt, and pull request number from the payload; ingest refuses a merge sha the run did not check out and marks `base-drift`. |
| Unreachable base | The shadow job fetches the base sha explicitly; an unreachable base is not measurable. |
| Absent key reads clean; non-pass omitted counts as missed | A measurability check runs before `shadow_result`: every canonical gate present with `pass` or `fail`, else not measurable; S-055. |
| Reruns replace attempts | Outcomes read with `filter=all`, records and artifacts keyed by attempt, never overwritten. |
| Hand-maintained job names | The mapping is data in the workflow with a contract test that fails when a named job or step disappears; S-058. |
| Approval or note edits reset classes; router change resets nothing | Section 3: a canonical digest over the matched rules' terms, the classifier, and the canonical set with `_` keys stripped and `review_status` excluded, plus the router blob sha and the omitted set; S-061. |
| G7's unknown unsatisfiable | An adjudication names an ENGINEERING section 16 or `docs/unknowns/` entry by id, never a route unknown; adjudications are capped by A. |
| Rule selecting nothing | A rule with no obligations is refused at load, M1, S-062; a `selects-nothing` candidate is never evidence. |
| Base-caused failure | `inherited-failure` inconclusive, detected from the base sha's own run. |
| Flake versus race | Adjudication requires the passing rerun's record id and a recorded unknown's id, is capped, and stays reported forever; the rerun alone erases nothing. |
| Cost column | Section 6 states the measured rate: ten `docs-only` changes in 45, one with a run; option 1 is the first milestone and approval waits on traffic. |
| Canary is a real miss; label gameable | Section 6 records the expected miss and makes narrowing `docs-only` an owner decision; G8 derives provenance from a `canary/` branch name in the payload, lists canaries by id, and refuses a canary head that is an ancestor of `main`; S-059. |
| Run store | G3 keeps the self-ignoring store as M1 and drops the claim that CI measurability waits on it. |
| Backfill at its own head | Section 5: today's router and policy over the historical change set, outcomes from the run at that head, keyed by today's digests; heads older than the workflow not measurable; S-060 rewritten. |
| Storage | Option A with a recomputing ingest, G10; option B recorded as not recommended with the challenger's reasons. |
| Line endings, schema, id, attempt, permissions, `write_shadow` | G9 adds `eol=lf` for `metrics/shadow/**` and the schema; the schema is `shadow-record-v2`; the record id is the digest of its canonical bytes; the artifact name carries the attempt; the job carries `actions: read`; the CI step writes a path and does not use `write_shadow`. |

## Left open for the implementer

- Whether a fork pull request's read-only token can upload the artifact, and what a timed-out job's conclusion value is; measured, not assumed, in M3.
- Whether run conclusions remain readable through the API past ninety days; the ledger is the durable record either way.
- The exact byte conventions of the summary, taken from `adc.py efficiency aggregate`, which reproduced `metrics/summary.json` byte-for-byte under Python 3.14.

# Handoff back: SLICE-002, the machinery and the first measurements

Date: 2026-09-03. Agent: Claude Opus 5 (1M context), implementing from `HANDOFF-OPUS-SLICE-002.md`. Base: `6097aee`, main after PR #33. Branch: `claude/slice-002-impl`, draft PR #34. Canary: `canary/docs-only/2026-09-03`, draft PR #35, never to be merged. Stopped where the owner asked: M1, M2, M3, M5, and the canary, with a report before M4's ledger is built.

## 1. Terminal outcome

- **The campaign can measure.** A non-required CI job produced the first live record end to end on this branch's own pull request: merge ref measured, base fetched, all five canonical gates decided from the run's own attempt, record uploaded. `Run `33742714194` at `bc51ef6`, pull request 34: merge commit `99314e5c48aa`, base `6097aee388c8`, every canonical gate `pass`, `provenance: live`, `measurable: true`, `status: no_omission` because the change touches the router and the candidate forces full. Nine jobs green including the shadow job itself.`
- **The class mix is the headline, and it is narrow.** Of the 31 merges on main, exactly one class the repository has ever produced omits anything at all. Section 3.
- **The canary caught a real miss for `docs-only`, which is the class the campaign is counting.** Section 4.
- **Nothing was approved and nothing was skipped.** No routing rule is approved, selective execution stays disabled, the required aggregator is unchanged, and CI writes nothing to the repository.
- The owner's five decisions of 2026-09-03 were built to, not reopened. One deviation from the brief's wording is recorded as a decision rather than made silently: D-125's router identity.

## 2. What was built

| Item | What landed | Held by |
| --- | --- | --- |
| M1 | The run store's ignore file names itself (D-122); a rule with no obligations is refused at load (D-123); `metrics/shadow/**` and `metrics/schemas/*.json` carry `eol=lf` (D-124) | R-056, R-057; rows M127 to M129 |
| M2 | `adc.py shadow record`: measurability decided before the comparator, the status vocabulary, the class key, derived provenance, the record id, and the v2 schema (D-125) | R-058; rows M130 to M134 |
| M3 | The non-required `shadow` job, the gate-to-job mapping as data, and `adc.py shadow outcomes` reading one run attempt (D-126) | R-059; rows M135 to M137 |
| M5 | `adc.py shadow backfill`, today's router over historical change sets (D-127) | R-060; row M138 |
| M6 | The canary procedure, executed once for `docs-only` | Section 4 |

Every row was applied and measured to fail its own suite before the commit that added it. The full suite is green at 529 passed, 14 skipped, 67 subtests, and universal validation reports 0 errors.

M4, the ledger and the summary, is deliberately not built. The owner asked for the class mix first, because it decides whether the ledger is worth building.

## 3. The class mix, measured

`adc.py shadow backfill` replayed today's router and calibration over all 31 merges on `main`, reading each head's own CI run.

| Class | Merges | Rules the candidate matched | Gates it omits | Statuses |
| --- | ---: | --- | ---: | --- |
| `6a6b05ab` | 7 | docs-only, product-code, schema-contract, verification-authority | 0 | 6 no_omission, 1 not measurable |
| `325b434b` | 7 | docs-only, product-code, verification-authority | 0 | 5 no_omission, 2 not measurable |
| `43dd098f` | 6 | docs-only | 4 | 2 clean, 4 not measurable |
| `6456f88a` | 5 | product-code, verification-authority | 0 | 5 not measurable |
| `eea3f7a2` | 2 | verification-authority | 0 | 2 not measurable |
| `5862f237` | 2 | docs-only, verification-authority | 0 | 2 not measurable |
| `83523da0` | 1 | five rules including skill-policy | 0 | 1 not measurable |
| `bbc18acd` | 1 | schema-contract, verification-authority | 0 | 1 not measurable |

Read plainly:

- **Seven of the eight classes omit nothing.** Any change that touches the router, the tests, the calibration, the workflow, or a schema matches a force-full rule, so its candidate runs everything and the record can never be evidence for or against a shortcut. That is the policy working as designed, and it means the campaign has one class to measure, not eight.
- **`docs-only` is the whole campaign.** It selects the validate step and omits the other four gates. Six merges in the repository's history fall in it, and two of those have runs: PRs #31 and #33, both clean.
- **Nineteen merges have a run at all**, because the workflow landed on 2026-08-22. Six of those nineteen are unmeasurable because the mutation-replay and hostile-environment jobs did not exist yet, so their gates read `unresolved`. That is D-126 reporting a real gap rather than a pass, on real history.
- **Two live-quality clean records exist in the entire history.** The criterion the owner chose is 30. At the rate this repository produces documentation-only pull requests, that is a long wait, and the wait is the honest answer rather than a reason to lower the bar.

## 4. The canary

`canary/docs-only/2026-09-03`, pull request 35, run `33742816320`, never to be merged. One new Markdown file under `design/routing/` citing a decision id that does not exist.

The route the proposed rules would have taken: Level 0, selecting `validate-core` and omitting the other four gates. What CI actually concluded: the validate step passed, the suite failed on the decision guard in all four legs, both hostile-environment jobs failed, distribution and mutation-replay passed. The mutation-replay job passes because the replay deselects the integrity class the guard lives in, which is worth knowing about the replay rather than about the route.

The record, as written by the job:

```json
{
  "class": {
    "matched_rule_ids": [
      "docs-only"
    ],
    "omitted_gate_ids": [
      "distribution",
      "full-suite",
      "hostile-environment",
      "mutation-replay"
    ],
    "router_blob_sha256": "d0d40e77a26430eacc2851f8641b47d618e8d8550a55cb91de50c49fb70950f7",
    "selected_gate_ids": [
      "validate-core"
    ],
    "terms_sha256": "6b8e7a3288f79cdbddf50a5d6cc4279a215cb24c9dca65ce9a172e6529a76a8f"
  },
  "class_key": "43dd098f71a31d952639334dfd15e54ba74b708a5769960e6bfe6437688fc3a3",
  "commits": {
    "base": "bc51ef63f413f527052a7ef397b588f1f0fdb1b9",
    "head": "d1ece0716b6e9a6fd4b025ad14cd7ade52139905",
    "merge": "0221430c2a1752b6388155bf8312ab0f4abdef22"
  },
  "gate_outcomes": {
    "distribution": "pass",
    "full-suite": "fail",
    "hostile-environment": "fail",
    "mutation-replay": "pass",
    "validate-core": "pass"
  },
  "head_ref": "canary/docs-only/2026-09-03",
  "measurable": true,
  "provenance": "canary",
  "record_id": "72111be5bc02efbe95125ffc227935869074a4cbc5d88dddb6e833a41af5fad1",
  "run": {
    "pull_request": 35,
    "run_attempt": 1,
    "run_id": "33742816320"
  },
  "shadow": {
    "missed_gate_ids": [
      "full-suite",
      "hostile-environment"
    ],
    "omitted_gate_results": {
      "distribution": "pass",
      "full-suite": "fail",
      "hostile-environment": "fail",
      "mutation-replay": "pass"
    },
    "routing_miss": true,
    "selected_all_passed": true
  },
  "status": "miss"
}
```

Three things follow.

- **The comparator sees failures for this class.** G8 is satisfied for `docs-only`, and no clean count for it was worth anything until this record existed.
- **The class key is the same one the two clean records carry**, `43dd098f`. The canary is evidence about the same thing the campaign is counting, not a different thing that happens to fail.
- **The design challenge's prediction was exact.** A `docs-only` change can break the suite, because the suite's own decision guard reads the design documents that the route would skip the suite for. Approving `docs-only` today would have let this change through on the validate step alone while two gates were failing.

The owner's decision of 2026-09-03 was to let the canary record the miss rather than narrow the classifier first, so that the narrowing is decided on evidence. This is the evidence. The narrowing itself is the owner's call and is not made here.

## 5. What I found that the design did not say

- **The precondition was worse than recorded.** Every written receipt in this repository was full because of `.anti-dark-code/.gitignore`, a file the tool creates and never named in its own ignore list. Until D-122 the campaign would have measured nothing at all, because every candidate would have forced full. The design challenge found it; the fix's own consequence is new: a repository that had committed that file gains a line once, and that one write is a change the router correctly reports. Two CLI tests failed on exactly that and now hold the migration.
- **One of my tests was flaky by construction.** It took a receipt by name sort, and receipts are named by their own digest, so which one it read depended on content. It now takes the receipt that appeared, and the CLI suite was run twice to show it. A test that is right on average is not right.
- **A mutation row's pattern is line-ending sensitive.** `replay.py` matches raw bytes, and the authoritative replays run in `core.autocrlf=false` clones where every file is LF, so multi-line rows work there. In a default Windows worktree the same pattern does not match, which is why my local challenge script normalises before applying. The matrix integrity test reads text and so agrees with neither; it passes here and in the replay clones for different reasons. Recorded rather than changed: it is the harness's existing contract, and changing it belongs to whoever next touches the replay.

## 6. Open, and for whom

- **The owner.** Whether to narrow the `docs-only` classifier, on the canary's evidence rather than on prediction. This is the decision the brief's section 13 deferred to exactly this moment.
- **M4, the ledger and summary**, if the mix above makes it worth building: `metrics/shadow/ledger/`, the recomputing ingest, the deterministic summary, and the adjudications file. The record shape, the schema, and the class key it needs are all in place.
- **Measured, not assumed, and still open:** whether a fork pull request's read-only token can upload the artifact. Every run so far has been same-repository. The job carries `actions: read` and that was enough for the API read.
- **Not measured:** whether run conclusions stay readable past ninety days. The ledger is the durable record either way, which is why ingest must run inside the window.

## 7. Boundaries, unchanged

No routing rule is approved. Selective execution is disabled, locally and in CI. The required aggregator's needs are unchanged and a row holds them there. The canonical full set is unchanged. CI writes nothing to the repository. SLICE-001 stays `Done` and no slice status moved.

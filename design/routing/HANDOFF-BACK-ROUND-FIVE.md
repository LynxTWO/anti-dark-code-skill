# Handoff back to Claude: round five

Date: 2026-08-29. Agent: Codex. Branch: `design/assurance-router-specs`.
Commit reviewed: `d710150c8f50821b706a878a4532a6b29246d442`.
Platform: Windows 11 Pro Insider Preview 10.0.26220. Python: 3.14.2.
Git: 2.50.1.windows.1. `core.fileMode=false`.
Suite: `279 passed, 13 skipped, 45 subtests passed in 125.62s`.
Router suite: `148 passed in 13.34s`.
Validation: `VALID (universal): 0 errors, 1 warning(s)`.

## 1. Verification results

| Claim | Verdict | Evidence | Note |
|---|---|---|---|
| Q-01 | verified | The full suite, router suite, and validator reproduced the stated counts. | The warning is the known generated `__pycache__` warning. |
| Q-02 | refuted | K-02, K-06, K-07, K-09, and K-10 through K-13 reproduced as closed. K-01, K-03, K-04, K-05, and K-08 remain open in part or in full. | See L-01 through L-06. |
| Q-03 | refuted | A committed rename in a blobless partial clone caused `git diff` to start `git fetch`. The missing blob appeared and the snapshot returned complete. | Existing clean-filter, fsmonitor, and external-diff tests pass. The universal no-program claim does not. |
| Q-04 | refuted | A tracked file changed after its worktree comparison. Its size and mtime were restored. The snapshot returned complete with no input and no boundary problem. | See L-02. |
| Q-05 | refuted | Source-container mutation no longer changes a loaded policy, and a raw mapping is refused. A caller can directly construct `ValidatedPolicy` and pass a Level 0 empty recipe through the type check. | See L-04. |
| Q-06 | refuted | Hints accepted level 999, string `false`, a cross-capability gate pair, and a pair present only in a proposed rule. | See L-05. |
| Q-07 | refuted | Real SHA-256, type-change, gitlink, and conflict cases parsed. Impossible R, C, A, D, and mixed-payload-width records also parsed without a problem. | See L-06. |
| Q-08 | verified | Obligation key order was identical for both fact orders. The listed unsorted-key mutation failed one test. | Route nested mutability is a separate issue in L-07. |
| Q-09 | verified | `load_policy` requires the capability argument and uses the supplied set. The default-catalog mutation failed one test. | The missing canonical full-set argument is L-03. |
| Q-10 | verified | A literal backslash remained literal. The rewrite mutation failed one test. | Git path text is preserved. |
| Q-11 | refuted | Section 2 contains 20 mutation rows, not 21. All 20 reconstructed mutants were caught, but the copy-detection mutant failed two tests rather than the stated one. No patch or hash identifies a twenty-first mutant. | See section 2 and L-09. |
| Q-12 | refuted | The partial-clone trace contains `diff/fetch`, a child `git fetch`, one wanted object, and one written object while `fetch.negotiationAlgorithm=noop` is active. | The setting changes negotiation. It does not prevent fetching. |

Receipts, the `route` subcommand, gate-runner binding, and shadow comparator are not built. I cannot assess them.

## 2. Mutation results

The 20 listed rows were reconstructed as one replacement at a time against a separate clone at the reviewed commit. The source was restored after each run.

| Listed mutation | Result on this host |
|---|---|
| obligation union to assignment | caught, 6 failed |
| force_full OR to assignment | caught, 5 failed |
| level maximum to assignment | caught, 3 failed |
| drop terminal-NUL framing check | caught, 3 failed |
| accept a string predicate | caught, 2 failed |
| accept any file mode | caught, 2 failed |
| drop filter overrides | caught, 2 failed |
| drop fsmonitor isolation | caught, 2 failed |
| hint may write any field | caught, 2 failed |
| full route skips recipe passes | caught, 1 failed |
| drop boundary detector | caught, 1 failed |
| drop copy detection | caught, 2 failed |
| accept mixed object widths within one record | caught, 1 failed |
| score on any status | caught, 1 failed |
| guess the capability catalog | caught, 1 failed |
| unsorted obligation keys | caught, 1 failed |
| hint may invent a pass | caught, 1 failed |
| rewrite backslashes in paths | caught, 1 failed |
| accept an unvalidated mapping | caught, 1 failed |
| drop duplicate collapse | caught, 1 failed |

Six further mutations were run. All six survived 148 tests.

| Further mutation | Result | Assessment |
|---|---|---|
| skip `recipe.minimum_level` on a full route | survived | non-equivalent, missing route assertion |
| skip `recipe.independent_review` on a full route | survived | non-equivalent, fixture masks the loss |
| drop `ADC-ROUTE-UNROUTED-FACT` | survived | non-equivalent, missing reason assertion |
| drop `fetch.negotiationAlgorithm=noop` | survived | expected because it does not enforce no-fetch behavior |
| remove index state from the fingerprint | survived | non-equivalent, missing boundary assertion |
| drop worktree `--no-textconv` | survived | no focused assertion; raw diff behavior may make this equivalent on current Git |

The first three provide the requested further surviving mutations. They are grouped in L-08.

## 3. Findings

### L-01, blocking (critical risk): partial-clone acquisition fetches and can execute remote machinery

File: `anti-dark-code/scripts/adc_route.py:257` and `anti-dark-code/scripts/adc_route.py:428`.

What is wrong: `fetch.negotiationAlgorithm=noop` does not disable lazy fetch. In a blobless clone, rename detection needed a missing old blob. Git started a fetch, materialized the blob, and returned a complete snapshot. Git documents `noop` as a negotiation choice, while partial clone fetches missing objects on demand through `git fetch`: [fetch configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-fetchnegotiationAlgorithm), [partial clone design](https://git-scm.com/docs/partial-clone).

Concrete input: a partial clone at a commit that renames and edits `tracked.txt`, with the base blob absent. Before acquisition, `git cat-file -e 0266c387...` under `GIT_NO_LAZY_FETCH=1` returned 128. `read_change_inputs(repo, "base-ref")` returned complete and classified a rename. Afterward the object existed.

Expected: no fetch child starts, the object remains absent, and acquisition returns incomplete. Actual: Trace2 recorded `diff/fetch`, `git fetch origin --filter=blob:none --stdin`, one want, and one object written.

Proposed fix: set `GIT_NO_LAZY_FETCH=1` in every runner environment. Treat a missing promisor object as unreadable. Add a real partial-clone regression test and remove the negotiation setting from security claims.

### L-02, blocking (high risk): the boundary fingerprint misses a tracked rewrite

File: `anti-dark-code/scripts/adc_route.py:314-351`.

What is wrong: the fingerprint stores only file size and mtime. It does not read file bytes. A write can occur after the worktree comparison and preserve both values, so the after-check is equal even though the snapshot omitted changed content.

Concrete input: start with tracked `victim.txt` containing `AAAA\n`. After the main untracked query returns, rewrite it to `BBBB\n` and restore its original nanosecond mtime. The size stays five bytes.

Expected: `ADC-ROUTE-BOUNDARY-VIOLATED`, `complete=False`, or an input for `victim.txt`. Actual: `content_after=b'BBBB\n'`, `same_size=True`, `same_mtime=True`, `snapshot_complete=True`, `snapshot_problems=()`, `snapshot_inputs=()`.

Proposed fix: compare content identity for the index and routing-relevant paths, or acquire from an isolated immutable repository representation. Keep metadata only as a performance aid. Add this timing-specific hostile test.

### L-03, blocking (high risk): policy loading does not validate the canonical full set

File: `anti-dark-code/scripts/adc_route.py:1018-1081`.

What is wrong: D-030 and the architecture require `load_policy(data, gates, capability_ids, full_set)`. The implementation has no `full_set` argument. It checks Level 3, a nonempty pass set, and a nonempty obligation set, but not the repository's canonical pass, capability, or gate set.

Concrete input: a policy whose full recipe is Level 3 with only pass `00` and `V01: [validate-core]`, with no rules.

Expected: `PolicyError` for an incomplete canonical full recipe. Actual: `load_policy` returned a `ValidatedPolicy`.

Proposed fix: require a canonical full-set input derived from reviewed repository configuration. Compare all required passes, capability-gate pairs, and approved gates. Add one-at-a-time omission tests.

### L-04, blocking (high risk): the validated-policy type check has no provenance

File: `anti-dark-code/scripts/adc_route.py:686` and `anti-dark-code/scripts/adc_route.py:850`.

What is wrong: the frozen policy records are public constructors. `isinstance(policy, ValidatedPolicy)` proves the class, not that `load_policy` validated it.

Concrete input: directly construct a `ValidatedPolicy` with an empty Level 0 recipe and one approved Level 0 docs rule, then route `README.md`.

Expected: the route boundary rejects a value not produced by validated loading. Actual: `Route(minimum_level=0, passes=frozenset(), obligations={}, matched_rule_ids={'forged-cheap'}, force_full=False)`.

Proposed fix: make the loader the supported authority constructor and check loader provenance, or revalidate the immutable value at the route boundary. Add direct-construction tests for every exported record type.

### L-05, blocking (high risk): hint validation loses types and capability-gate bindings

File: `anti-dark-code/scripts/adc_route.py:763-813`.

What is wrong: levels are converted with `int`, flags with `bool`, and capabilities and gates are checked in separate unions. Rules with `review_status=proposed` expand both unions. A hint can therefore add a gate not reviewed for that capability and can use invalid scalar types.

Concrete failing inputs:

- `{"minimum_level": 999}` returns a route at level 999.
- `{"force_full": "false"}` returns `force_full=True`.
- `{"obligations": {"V08": ["validate-core"]}}` is accepted although the policy binds V08 to `distribution`.
- a proposed-only `V14: [validate-core]` binding becomes valid hint vocabulary.

Expected: `HintError` for every case. Actual: every hint returned a new Route.

Proposed fix: validate a typed hint schema before conversion. Use the closed level set and real booleans. Validate approved capability-gate pairs, not separate id membership, and exclude proposed rules.

### L-06, blocking (high risk): raw parsing still accepts impossible Git records

File: `anti-dark-code/scripts/adc_route.py:67-102` and `anti-dark-code/scripts/adc_route.py:180`.

What is wrong: score-free C and R records pass because any status without a score returns true. Status-specific absent sides are not checked. Object width is checked only within each record, so one payload can mix SHA-1 and SHA-256 records. Git's raw format requires similarity scores on C and R records and defines status-specific path and side semantics: [Git diff raw format](https://git-scm.com/docs/diff-format#_raw_output_format).

Concrete failing inputs: `R` or `C` without a score, `A` with two existing sides, `D` with two existing sides, and a two-record payload with one 40 digit pair and one 64 digit pair.

Expected: zero accepted inputs and `ADC-ROUTE-MALFORMED-RECORD`. Actual: each single-record case returned one input with no problem; the mixed payload returned two inputs with no problem.

Proposed fix: validate required scores and status sides. Pass the repository object format into parsing or establish one payload width from trusted acquisition and enforce it across every record. Retain real Git tests for worktree null objects, SHA-256, type changes, gitlinks, and conflicts.

### L-07, major (medium risk): Route is only shallowly frozen

File: `anti-dark-code/scripts/adc_route.py:612-622` and `anti-dark-code/scripts/adc_route.py:746`.

What is wrong: `Route` is a frozen dataclass, but `obligations` is a dictionary. A caller can clear or replace entries after route construction. That changes authority data without another route computation.

Concrete input: build the README route, save its nonempty obligations, then call `built.obligations.clear()`.

Expected: mutation fails and the Route stays unchanged. Actual: the mapping became empty.

Proposed fix: store obligations as a canonical immutable tuple, with a fresh-map helper only for read convenience. Add nested mutation tests for every Route field.

### L-08, major (medium risk): full-recipe and reason-code mutations survive

File: `anti-dark-code/scripts/adc_route.py:728`, `anti-dark-code/scripts/adc_route.py:736`, and `anti-dark-code/scripts/adc_route.py:739`.

What is wrong: the authority-change fixture already supplies Level 3 and independent review through its matching rule. It cannot detect removal of those values from the full recipe. The unrouted-fact test checks only `force_full`, not its stable reason.

Concrete mutations: replace recipe level and review merges with no-ops, or remove `ADC-ROUTE-UNROUTED-FACT`. Each run returned `148 passed`.

Expected: at least one focused failure per mutation. Actual: all three survived.

Proposed fix: add force-full fixtures whose matching rules do not already supply recipe values. Assert every full-recipe field and each stable reason code separately.

### L-09, minor (low risk): the handoff mutation record is not reproducible as written

File: `design/routing/HANDOFF-CODEX-ROUND-FIVE.md:26-49` and `design/routing/HANDOFF-CODEX-ROUND-FIVE.md:96`.

What is wrong: the table says 21 mutations but contains 20 rows. There are no patches, hashes, or replacement descriptions precise enough to identify a missing row. The stated copy-detection count also differed from a direct reconstruction.

Concrete input: count the section 2 body rows and reconstruct removal of both `-C` and `--find-copies-harder`.

Expected: 21 identified mutants and the stated failure counts. Actual: 20 rows; the reconstructed copy mutant caused two failures.

Proposed fix: record each mutant as a patch or stable replacement with a source commit, expected failing test ids, and observed exit result.

## 4. Rulings

The K-01 three-layer approach is not accepted as a trust boundary.

1. Safe-by-construction acquisition is not established. Rename and copy detection can read missing blobs and start lazy fetch.
2. Effective filter discovery is useful and the real clean-filter cases pass. It covers that command family, not every process or network path Git may start.
3. The metadata fingerprint is diagnostic. It misses a same-size, same-mtime tracked rewrite and does not detect ignored-path writes or off-repository effects.

The narrower route-relevant scope may be acceptable for a content-integrity check after it hashes bytes. It is not evidence that no candidate program ran. The measured 0.412 second cost on 345 files is acceptable for this slice. Performance on a much larger repository is unknown.

Q-12 is refuted. `fetch.negotiationAlgorithm=noop` changes fetch negotiation and remained active on the fetch that the probe observed. It does not disable fetching. D-036 requires `GIT_NO_LAZY_FETCH=1` and a direct partial-clone test.

## 5. Edits applied

Documents only. No implementation, test, CI, or metrics file changed.

- Added this report.
- Added D-036 through D-041 to `DECISION-LOG.md`.
- Added R-043 through R-048 to `ENGINEERING.md`.
- Added S-040 through S-045 and marked M2 round-five blocked in `SLICE-001-route-shadow.md`.
- Updated the architecture gate and invariants in `ARCHITECTURE.md`.
- Added the round-five gate to `plans/2026-08-28-assurance-router-slice-001.md`.

The anti-dark-code writing-hygiene rules and the handoff's banned-term list were applied to touched text.

## 6. Execution evidence

Baseline:

```text
> python -m pytest anti-dark-code/tests/test_route.py -q
148 passed in 13.34s

> python -m pytest anti-dark-code/tests -q
279 passed, 13 skipped, 45 subtests passed in 125.62s

> python anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)
```

Partial clone:

```text
old_blob_present_before=False
snapshot_complete=True
snapshot_problems=()
snapshot_inputs=[('renamed.txt', 'tracked.txt', 'committed', 'rename')]
old_blob_present_after=True

Trace2 child:
git -c fetch.negotiationAlgorithm=noop fetch origin --no-tags
    --no-write-fetch-head --recurse-submodules=no --filter=blob:none --stdin
fetch_count=1, wants=1, wrote=1
```

Hostile fingerprint:

```text
content_after=b'BBBB\n'
same_size=True
same_mtime=True
snapshot_complete=True
snapshot_problems=()
snapshot_inputs=()
```

Real Git grammar:

```text
sha256_complete=True, problems=()
typechange_complete=True, 100644 -> 120000
gitlink_complete=True, mode 160000 represented
conflict_complete=True, unmerged records represented
```

Pure probes:

```text
canonical_full_set_omitted=OK:ValidatedPolicy(...)
parser_rename_without_score=inputs:1,problems:()
parser_copy_without_score=inputs:1,problems:()
parser_mixed_widths_across_records=inputs:2,problems:()
hint_level_999=OK:Route(minimum_level=999,...)
hint_string_false=OK:Route(...force_full=True,...)
hint_cross_capability_gate=OK:Route(...)
hint_proposed_binding=OK:Route(...)
forged_validated_policy=OK:Route(minimum_level=0,...force_full=False)
route_obligations_mutable=True
```

All scratch repositories, probes, traces, and the mutation clone were created under `C:\DEV\skills\anti-dark-code-round-five-review-20260829`, outside the repository. They were removed after results were copied here. Final status is limited to the six authorized documents under `design/routing/`.

## 7. Questions back

1. What patch or replacement is the missing twenty-first mutation in the handoff matrix?
2. Will the next builder treat D-036 through D-041 as the failing-before contract and keep receipt and CLI work blocked?
3. Should the next handoff include mutation patches and test ids so failure counts are independently reproducible?

## 8. Readiness

Do not proceed. L-01 through L-06 are blocking findings in acquisition, boundary detection, policy authority, canonical full-route validation, hint validation, and raw parsing. L-07 and L-08 also need closure before route data is written into receipts. Receipt writing, the CLI, gate binding, and shadow comparison remain unassessed because they are not built.

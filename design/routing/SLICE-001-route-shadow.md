# Assurance Router Slice Brief: SLICE-001 read-only shadow routing

Version: 1.1. Date: 2026-09-02. Status: Done. The owner walkthrough was approved by Daniel Boyd on 2026-09-02 from a fresh default clone at `3e04422`; the record is `WALKTHROUGH-SLICE-001.md` at `4419538`.
Companion documents: ARCHITECTURE.md, ENGINEERING.md, DECISION-LOG.md.

One narrow, production-quality section. If it is not in here, it does not get built.

---

## 1. What the slice proves

- **Central claim:** a deterministic router can explain, for a real change in this repository, exactly which passes were invalidated and which evidence the change requires, and it can be trusted enough to be worth obeying later.
- **The slice in one line:** a developer runs `adc.py route`, gets a compact explained route and a bound receipt, and nothing is skipped.
- **Honest stakes:** if the shadow comparisons show that the router's proposed omissions would have missed real failures, the routing idea does not survive contact with this repository and the design deserves a rethink before any shortcut is permitted.

The slice is deliberately unable to save anything. Its entire value is producing evidence about what it *would* have saved, and what that would have cost.

## 2. The walkthrough

1. A developer makes an ordinary change and runs `python .agents/skills/anti-dark-code/scripts/adc.py route --repo . --base origin/main`.
2. The router collects change facts from git, including renames, deletions, mode changes, staged, unstaged, and untracked paths.
3. Rules from `calibration/routing-policy.json` match the facts, and requirements combine by union and maximum.
4. The router prints one compact line and, with `--write`, writes a receipt bound to the worktree, policy, gates, calibration, and repository identity.
5. The developer runs the existing full verification as normal. Nothing was skipped.
6. The shadow comparator records whether any gate the route would have omitted actually failed.

Every step works against the real repository, real git state, and the real calibration layer. No bypasses.

## 3. In scope, with build order

| Item | Notes |
|---|---|
| `read_change_inputs()` | read-only Git boundary, NUL-delimited and status-aware, sees tooling paths per D-010 |
| `collect_change_facts()` | pure over ChangeSnapshot, classifies both paths of rename and copy records |
| `build_route()` | pure, monotonic by construction per D-009 |
| `routing-policy.json` template and schema | ships in assets, installed copy is repository owned |
| Receipt writer and verifier | bound identity, stable reason codes |
| `adc.py route` subcommand | read-only, `--repo`, `--base`, `--phase`, `--write` |
| Shadow comparator | records misses, changes nothing |
| `test_route.py` | R-001 to R-033 |

| Milestone | Status | Contents |
|---|---|---|
| M1 | Done | Extend the catalog with V21 Affected-unit testing and V22 Input fuzz testing, as settled by D-016. No other capability id is added in this milestone. |
| M2 | Done, 2026-08-30 | The pure layer, closed through round nine. Q-01 through Q-06 are resolved or recorded: Q-05 is proven against a real blobless clone (D-060) rather than blocked, and M36, M47, and M48 are held. Linux is a required replay host (D-058). |
| M3 | Implemented | Policy schema and template, this repository's policy installed with every rule proposed (D-064), the receipt writer and verifier, and the `route` subcommand with `--write` and `--verify`. D-070's four partial requirements are closed by contract: D-071 and D-082 grade source and managed installed self-grading path classes as authority and refuse a policy that does not, while D-072 refuses a tree holding a submodule rather than pretending to bind one. The slice still needs its human walkthrough. |
| M4 | Implemented, 2026-08-30 | R-013, R-018, and R-022 are traced to runner evidence. `CandidateRoute` evaluates proposed rules but is refused by receipts and executable selection; the comparator is written beside real gate outcomes. Under the shipped proposed-only policy, authoritative execution remains the canonical full set. |

M1 is first because a rule cannot name an obligation until the two catalog entries settled by D-016 exist, and D-004 made obligations capability ids.

## 4. Out of scope, on purpose

| Excluded | Where it will connect later | Log entry |
|---|---|---|
| Any selective execution | gate runner binding, after shadow evidence | D-011 |
| Selective CI and a route-aware aggregator | `tests.yml` `required` job | D-011 |
| Gate coverage metadata (`tags`, `covers`, `scope`) | `gates.json` and `gate_definition_hash` | D-012 |
| Cheapest-gate optimizer | route builder | D-013 |
| Provisional pre-implementation routing | `route --phase task` | ADD 10 |
| Enforcing `independent_review` | receipt plus an attestation mechanism | D-008 |
| Publishing shadow results to `metrics/` | efficiency ledger machinery | D-014 |

**Rule.** Out-of-scope items are named, not implied. Silence is how "minimum" quietly becomes the permanent foundation.

## 5. Stubs and their debts

| Stub | Real version arrives when | Behavior for now | Log entry |
|---|---|---|---|
| Gate runner binding | shadow evidence supports one route class | reads a receipt, still runs the full set | D-011 |
| `--phase` argument | provisional routing is built | accepted and recorded, does not change the route | ADD 10 |
| `independent_review` | an attestation mechanism exists | recorded in the receipt, warns only | D-008 |

Stubs are labeled in code. Inside the slice boundary, nothing is a stub.

## 6. Modules touched

Per ADD section 4: Git change reader, fact collector, routing policy, route builder, receipt writer, receipt verifier, shadow comparator, and the narrow gate-runner binding. The binding adds the escalate-only `--level` check and before-and-after receipt verification. It still cannot skip a gate.

The slice passes through the real seams: real git helpers, real calibration paths, real hashing helpers.

## 7. Data subset

Per EDD section 5: ChangeInput, ChangeFact, Rule, Receipt, and Omission in full production shape. Route and Obligation exist as records. ShadowResult exists with its miss counter and route class.

`routing-policy.json` ships as a template under `assets/templates/calibration/`, with a populated copy for this repository under its own calibration directory.

## 8. Acceptance criteria

| ID | Criterion | Verified by |
|---|---|---|
| S-001 | Given a set of change facts, when routed twice with the input order shuffled, then the receipt hash is identical | R-002 test |
| S-002 | Given a route, when a changed file is added to the fact set, then no component of the route decreases | R-001 property test |
| S-003 | Given a path matching no reviewed rule, when routed, then the route is full and the path appears in unknowns | R-003 test |
| S-004 | Given a change to `SKILL.md`, when routed, then it is not classified as inert documentation | R-004 test |
| S-005 | Given a change to routing code, routing policy, gate configuration, CI, or shared test helpers, when routed, then `force_full` is true | R-005 test |
| S-006 | Given a change to `calibration/gates.json`, when facts are collected, then a fact exists for that path | R-014 test |
| S-007 | Given each change kind, when collected, then a fact carries the correct kind | R-006 test |
| S-008 | Given an unreachable comparison base, when routed, then the route is full with a reason code | R-007 test |
| S-009 | Given a written receipt, when the worktree, policy, gates, or binding changes, then verification returns stale and the runner exits 2 | R-008, R-009 tests |
| S-010 | Given two rules matching one change, when routed, then requirements are their union | R-010 test |
| S-011 | Given an agent hint, when routed, then the result is a superset of the hint-free route | R-011 test |
| S-012 | Given a computed route at level 1, when `--level 0` is supplied, then the command exits 2 naming the route minimum | R-013 test |
| S-013 | Given a route, when gates are selected, then every obligation has an approved covering gate, or the route is full | R-012 test |
| S-014 | Given the suite, when a hard escalator is weakened, then at least one test fails | R-053 mutation replay |
| S-015 | Given a matched fact, when unrelated facts are added in any order, then its match and requirements remain present | R-015 test |
| S-016 | Given a capability obligation, when policy validation runs, then explicit approved gate ids cover it or validation blocks | R-016 test |
| S-017 | Given unchanged porcelain status but changed dirty bytes, index entries, modes, symlink targets, or submodule state, when verified, then the receipt is stale | R-017 test |
| S-018 | Given repository mutation before or during a gate, when the gate returns, then its output cannot satisfy an obligation | R-018 test |
| S-019 | Given every supported Git record and hostile path fixture, when acquired, then both paths, status, source, and mode survive or selective routing blocks | R-019 test |
| S-020 | Given generated valid hints, when applied, then every route field is equal or higher and the comparison input is unchanged | R-020 test |
| S-021 | Given each verification-authority path class, when routed, then `force_full` is true | R-021 test |
| S-022 | Given `force_full`, when gate applicability globs would exclude a gate, then the canonical full recipe still selects it | R-022 test |
| S-023 | Given identical authoritative inputs in shuffled order and different clocks, when receipts are built, then authoritative bytes and hashes match | R-023 test |
| S-024 | Given a repository-local filesystem monitor that writes a sentinel, when change acquisition runs, then the sentinel remains absent and repository state is unchanged | R-027 test |
| S-025 | Given malformed Git framing, invalid raw fields, malformed untracked output, or an empty successful base result, when acquired, then `complete` is false with a stable problem code | R-028 test |
| S-026 | Given a real copy from an unchanged source and a content-plus-mode change, when acquired, then copy provenance and the mode transition survive | R-029 test |
| S-027 | Given one invalid value for every input and classifier enum, when facts are collected, then no invalid fact is emitted | R-030 test |
| S-028 | Given duplicate records and two copies from one source, when classification runs under several hash seeds, then duplicates collapse and the full fact order is identical | R-031 test |
| S-029 | Given a path and classifier pattern that differ only by case, when tested on every supported host, then classification is identical | R-032 test |
| S-030 | Given the next capability id, when tests derive the contiguous range, then only `CAPABILITY_COUNT` changes and the V21 and V22 identity checks remain | R-033 test |
| S-031 | Given repository clean and process filters, external diff and text conversion, a filesystem monitor, and a missing promisor object, when acquisition runs, then no program, write, or fetch occurs | R-034 test |
| S-032 | Given a loaded policy, when its source mappings and lists are mutated, then the loaded value and resulting route do not change; a raw mapping cannot enter `build_route` | R-035 test |
| S-033 | Given every rule predicate shape and a non-Level-3 or incomplete full recipe, when policy loading runs, then invalid data is rejected | R-036 test |
| S-034 | Given invalid status scores, modes, null sides, or object widths, when a raw record is parsed, then it is reported and the snapshot is incomplete | R-037 test |
| S-035 | Given every permutation of route facts, when route collections are observed or serialized, then their order is canonical | R-038 test |
| S-036 | Given an invalid hint or a hint that writes computed evidence, when validation runs, then it is rejected without changing the route | R-039 test |
| S-037 | Given simulated host case folding and a POSIX path with literal backslash, when classification runs, then Git path semantics are unchanged | R-040 test |
| S-038 | Given each of the four round-four surviving mutations, when the focused suite runs, then at least one test fails | R-041 test |
| S-039 | Given caller-supplied capability ids extended by one, when policy loading runs, then the new id works without a second count edit; omitted ids are rejected | R-042 test |
| S-040 | Given a blobless partial clone whose rename comparison needs a missing blob, when acquisition runs, then no fetch starts, no object appears, and the snapshot is incomplete | R-043 test |
| S-041 | Given a tracked file rewritten after its comparison with equal size and mtime, when acquisition ends, then a boundary problem makes the snapshot incomplete | R-044 test |
| S-042 | Given a directly constructed policy record or a full recipe missing one canonical member, when routing or loading runs, then the value is rejected | R-045 test |
| S-043 | Given a missing C or R score, invalid status side, or payload with mixed object widths, when parsed, then the payload is malformed | R-046 test |
| S-044 | Given an invalid hint type, level, capability-gate pair, or proposed-only pair, when applied, then `HintError` is raised before routing changes | R-047 test |
| S-045 | Given a built Route or a one-field full-recipe mutation, when mutation is attempted or tests run, then nested state cannot change and the mutant fails | R-048 test |
| S-046 | Given omitted canonical full-set input or a loaded policy copied with changed authority fields, when loading or routing runs, then no selective route is produced | R-049 test |
| S-047 | Given same-size index replacement, linked-worktree index mutation, hard-link replacement, or symlink replacement during acquisition, when the closing boundary check runs, then the snapshot is incomplete | R-050 test |
| S-048 | Given one repository object format and real committed, staged, worktree, and conflict records, when acquisition parses them, then all valid records survive and any cross-source width mismatch blocks | R-051 test |
| S-049 | Given a Route from direct construction, field replacement, copy, build, or hints, when nested mutation is attempted, then authority data cannot change | R-052 test |
| S-050 | Given every stored mutation row, when the replay harness applies it alone, then the source is restored and every authority mutation is caught | R-053 mutation replay |
| S-051 | Given a real global filter and a real blobless clone missing a required blob, when acquisition runs, then no configured program or lazy fetch starts | R-054 test |

## 9. Verification evidence required

- [x] Acceptance coverage: all 51 S-ids name a registered R-id. Forty-nine rest on collected test nodes. S-014 and S-050 rest on R-053 mutation evidence, a typed evidence class accepted by the traceability checker. The final Round Sixteen Windows suite reported `486 passed, 14 skipped, 62 subtests passed`.
- [x] Platform execution is split from acceptance coverage. PR 30 commit `0ace58f2cc95f29ed96a17c407de95690806e89d` passed Linux, macOS, and Windows, plus Python 3.13, in required run `33671714111` on its first attempt; that run also passed both hostile-environment jobs, the clean distribution check, the complete Linux mutation replay of all 114 rows, and the aggregate gate. The run before it, `33668817057` at `2f86f14`, was also green on its first attempt while a WSL2 Linux serial write at the same head saw M107 survive; D-117 records why the CI runner's Python caught what a venv could not, and the repair is the difference between the two heads. Round Nineteen's equivalent receipt was run `33656382905` at `39d745d` on its second attempt, after a macOS temporary-directory cleanup race recorded as an open unknown that did not recur in either round-twenty run. Round Eighteen's was run `33645108730` at `08d0576`; Round Eighteen also ran the full 106-row serial matrix on T540P and challenged R-032 through the real classifier on Windows and Linux. The owner walkthrough still requires the final branch checks on its own head.
- [x] At checkpoint `ea8733c`, `adc.py route --repo . --base origin/main --write` returned Level 3, passes `07,10,11,14`, the five canonical gates, `force_full=true`, and `complete=true`. Receipt `59f3951317c0e7bc897bc5b137fc05f9b29766170d4cd4f47795f62725632137.json` verified `FRESH`. The earlier Task 13 probe verified the same receipt class `STALE` after an untracked edit and `FRESH` after removal.
- [x] Error paths were exercised. An unreachable base returned exit 0 with Level 3, `complete=false`, and `ADC-ROUTE-BASE-UNREACHABLE`. Invalid policy JSON returned exit 2 and wrote no receipt. Exact CLI tests hold missing-policy and missing-canonical-set refusal.
- [~] D-080 withdraws the unreconstructible claim that EDD section 17 passed for every historical change. Before `ea8733c`, the replacement is the qualified slice-level evidence here. From `ea8733c` forward, every commit carries `EDD-Checklist: satisfied` and names the host or workflow evidence used, except the seven round-fifteen commits `30c577c` through `bf9aba3`, which carry no trailer. D-080 says such commits violate it; round eighteen remeasured `ea8733c..d2e8b99` as 58 commits, 51 with the trailer and the same 7 without it. The violation remains recorded rather than rewritten. Those seven are covered by `HANDOFF-BACK-ROUND-FIFTEEN.md` and required run `33434352766` at `9dd7a3b`.
- [x] `validate --skill anti-dark-code --mode universal` reported `VALID (universal): 0 errors, 1 warning(s)`. The warning lists generated `__pycache__` files and is expected.
- [x] The clean distribution archive check passed in required run `33402328694` at `157f10a1b2f0bc1c65e3e1ea92ed49d37316c987`.
- [x] The 30 K, L, and N findings have a per-id closure record below. Twelve retain direct passing-after verdicts, N-08 closes under D-079, and 17 name the successor finding and requirement that carries their substance.
- [x] Every stored mutation is replayable from data. The matrix has 114 rows, 108 active and 6 superseded. Round Twenty's two full serial `--write` replays at `0ace58f`, one on Windows and one on WSL2 Ubuntu, each processed all 114 rows with `0 not caught` from a clean clone; their records were merged per platform, so every active row carries exact failed and skipped identities from both hosts at one commit (D-109), and a read-only Windows parallel replay at the same head agrees with the Windows write row for row. The Linux CI replay in run `33671714111` caught all 114. M37, M46, and M48 are `caught elsewhere` because the exact Windows skipped node is the exact Linux failed node (D-104). M08 is superseded by M114 because its catch on three hosts was each host's git-lfs driver (D-113). The harness restored every active mutation source to its exact pre-run hash (D-068). `SERIAL-EVIDENCE-ROUND-TWENTY.json` records the two writes, the parallel replay, the measurements at `2f86f14` and `39d745d`, the merge, and the boundaries.

### K, L, and N closure ledger

The old failing verdicts remain in their original handoffs. A successor row closes the substance without rewriting that historical verdict.

One row does not close. K-01 asked for a guarantee wider than any requirement now states, and the ledger says so rather than citing the unqualified wording of R-054. Reading a row as "closed" when its successor narrowed the claim is the failure this ledger exists to prevent.

| Finding | Failing-before record | Passing-after or successor closure |
|---|---|---|
| K-01 | `HANDOFF-BACK-PURE-LAYER.md` | Narrowed, not closed as asked. K-01 expected that no repository-configured program starts; the requirement that carries it is **R-034**, which claims every *known* configured program. The lazy-fetch half went to L-01 and R-043, with D-060 supplying the real missing-promisor transport. D-085 closed one such unknown: a driver whose name contains `=` escaped the override and executed. U-009 stays open. |
| K-02 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-03 | `HANDOFF-BACK-PURE-LAYER.md` | L-04, then N-02 and R-049. |
| K-04 | `HANDOFF-BACK-PURE-LAYER.md` | L-04, then N-02 and R-049; the Level 0 recipe case is held under R-036. |
| K-05 | `HANDOFF-BACK-PURE-LAYER.md` | L-06, then N-04 and R-051; the score, mode and null-side cases are held under R-037 and R-046. |
| K-06 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-07 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-08 | `HANDOFF-BACK-PURE-LAYER.md` | L-05, then R-047. |
| K-09 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-10 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-11 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-12 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| K-13 | `HANDOFF-BACK-PURE-LAYER.md` | Round five reproduced it as closed. |
| L-01 | `HANDOFF-BACK-ROUND-FIVE.md` | R-043 and R-054; D-060 closes the real transport case. |
| L-02 | `HANDOFF-BACK-ROUND-FIVE.md` | N-03, then R-050. |
| L-03 | `HANDOFF-BACK-ROUND-FIVE.md` | N-01, then R-049. |
| L-04 | `HANDOFF-BACK-ROUND-FIVE.md` | N-02, then R-049. |
| L-05 | `HANDOFF-BACK-ROUND-FIVE.md` | Round six reproduced it as closed. |
| L-06 | `HANDOFF-BACK-ROUND-FIVE.md` | N-04, then R-051. |
| L-07 | `HANDOFF-BACK-ROUND-FIVE.md` | N-05, then Q-01 and R-052. |
| L-08 | `HANDOFF-BACK-ROUND-FIVE.md` | Round six reproduced it as closed. |
| L-09 | `HANDOFF-BACK-ROUND-FIVE.md` | N-06, then R-053. |
| N-01 | `HANDOFF-BACK-ROUND-SIX.md` | R-049. |
| N-02 | `HANDOFF-BACK-ROUND-SIX.md` | Round seven reproduced the changed-policy refusal as closed; R-049 retains it. |
| N-03 | `HANDOFF-BACK-ROUND-SIX.md` | R-050. |
| N-04 | `HANDOFF-BACK-ROUND-SIX.md` | R-051. |
| N-05 | `HANDOFF-BACK-ROUND-SIX.md` | Q-01, then R-052. |
| N-06 | `HANDOFF-BACK-ROUND-SIX.md` | Round seven reproduced the data-driven matrix; R-053 retains it. |
| N-07 | `HANDOFF-BACK-ROUND-SIX.md` | D-047 and R-055. |
| N-08 | `HANDOFF-BACK-ROUND-SIX.md` | Round thirteen reproduced the inert fixture and closed it under D-079 and R-054; M91 holds the global clause. |

An agent's statement that the slice works is a claim. This list is the evidence.

## 10. Agent guardrails for this build

- **Boundary:** only the modules in section 6, only the data in section 7.
- **Stop and ask before:** adding a rule to the routing policy, changing a hard escalator, extending the capability catalog beyond what Q-001 settles, touching `tests.yml`, or enabling any selective execution.
- **Mode separation:** discovery, then implementation, then verification. No single prompt spans all three.
- **Self-grading:** a change to the router may not be judged by the router. That case forces the full route.
- **Conflicts:** if reality contradicts these documents, stop and surface it. Update through the Decision Log, then continue.

## 11. Slice definition of done

- [x] All 51 acceptance criteria have linked evidence: 49 through collected tests and S-014 and S-050 through R-053 mutation replay.
- [x] D-026 through D-047 are resolved in code. The executable evidence map covers R-001 through R-055. D-071, D-072, D-078, and D-082 close the four partial M3 requirements with collected tests; R-013, R-018, and both R-022 clauses have exact runner nodes. The round-fourteen R-022 challenge attempted candidate gate removal through real selection code and was refused.
- [~] Current and forward EDD guardrails hold with no unlabeled shortcut inside the boundary. D-080 withdraws the unsupported historical per-change claim and anchors the forward review record at `ea8733c`; seven round-fifteen commits inside that forward range carry no trailer, as section 9 records.
- [x] Under the shipped proposed-only policy, every authoritative route forces the full recipe. `gates --route` selects the canonical set by id, bypasses applicability globs, and refuses candidate data at both receipt and executable-selection boundaries.
- [x] V21 and V22 were added exactly as D-016 records. Q-002 and Q-003 remain open and do not block this slice.
- [x] Documents record the actual Task 13 command, receipt and refusal results, the 30-item closure ledger, the evidence qualifications, D-080 through D-117, and the owner walkthrough.
- [x] Human walkthrough completed and approved by Daniel Boyd on 2026-09-02, run as written from a fresh default clone at `3e04422`, all seven questions answered yes, with U-017 named as the accepted residual and D-107 option 2 as the follow-up; the record is `WALKTHROUGH-SLICE-001.md` at `4419538`.

## 12. What this unlocks

- **SLICE-002, shadow evidence campaign.** Run routing in shadow across real changes, count misses per route class, and produce the evidence that would justify enabling one class. Not a code slice so much as a measurement slice.
- **SLICE-003, selective local execution for one route class.** The narrowest class with clean shadow evidence, most likely the public-documentation route, with automatic escalation on any miss.

Selective CI stays behind both, per D-011.

---

*Approved for build by: [name], [date]. Until then, this brief is a proposal. When section 11 closes with evidence, mark the status Done and update ADD section 15 before opening the next brief.*

# Assurance Router Slice Brief: SLICE-001 read-only shadow routing

Version: 0.7. Date: 2026-08-29. Status: Round-five review blocked.
Companion documents: ARCHITECTURE.md, ENGINEERING.md, DECISION-LOG.md.

One narrow, production-quality section. If it is not in here, it does not get built.

---

## 1. What the slice proves

- **Central claim:** a deterministic router can explain, for a real change in this repository, exactly which passes were invalidated and which evidence the change requires, and it can be trusted enough to be worth obeying later.
- **The slice in one line:** a developer runs `adc.py route`, gets a compact explained route and a bound receipt, and nothing is skipped.
- **Honest stakes:** if the shadow comparisons show that the router's proposed omissions would have missed real failures, the routing idea does not survive contact with this repository and the design deserves a rethink before any shortcut is permitted.

The slice is deliberately unable to save anything. Its entire value is producing evidence about what it *would* have saved, and what that would have cost.

## 2. The walkthrough

1. A developer makes an ordinary change and runs `python .agents/skills/anti-dark-code/scripts/adc.py route --repo . --changed-from origin/main`.
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
| `adc.py route` subcommand | read-only, `--repo`, `--changed-from`, `--phase`, `--write` |
| Shadow comparator | records misses, changes nothing |
| `test_route.py` | R-001 to R-033 |

| Milestone | Status | Contents |
|---|---|---|
| M1 | Done | Extend the catalog with V21 Affected-unit testing and V22 Input fuzz testing, as settled by D-016. No other capability id is added in this milestone. |
| M2 | Review blocked, 2026-08-30 | The code exists, but N-01 through N-08 in `HANDOFF-BACK-ROUND-SIX.md` block completion. Canonical full-set validation is optional, policy provenance transfers through field replacement, index and path-topology mutations escape the boundary, repository-wide object format and real conflict grammar are not enforced, Route immutability is not a type invariant, and the stored mutation matrix is not replayable. R-049 through R-055 state the closure evidence. |
| M3 | Not started | Policy schema, the first routing policy for this repository, and the `route` subcommand with receipt writing and verification. |
| M4 | Not started | Shadow comparator, plus the mutation or revert test proving a weakened escalator fails the suite. |

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
| S-014 | Given the suite, when a hard escalator is weakened, then at least one test fails | mutation or revert test |
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
| S-050 | Given every stored mutation row, when the replay harness applies it alone, then the source is restored and every authority mutation is caught | R-053 test |
| S-051 | Given a real global filter and a real blobless clone missing a required blob, when acquisition runs, then no configured program or lazy fetch starts | R-054 test |

## 9. Verification evidence required

- [ ] Automated tests covering every acceptance criterion, passing on Linux, macOS, and Windows.
- [ ] `adc.py route` run against a real change in this repository, receipt recorded.
- [ ] Error paths exercised, at minimum: unreachable base, and invalid policy.
- [ ] EDD section 17 per-change checklist satisfied for every change in the slice.
- [ ] `validate --mode universal` reports zero errors.
- [ ] The clean distribution archive check passes with the new template included.
- [ ] K-01 through K-13, L-01 through L-09, and N-01 through N-08 are closed with failing-before and passing-after evidence.
- [ ] Every stored mutation is replayable from data, and M33 and M34 are caught by focused tests.

An agent's statement that the slice works is a claim. This list is the evidence.

## 10. Agent guardrails for this build

- **Boundary:** only the modules in section 6, only the data in section 7.
- **Stop and ask before:** adding a rule to the routing policy, changing a hard escalator, extending the capability catalog beyond what Q-001 settles, touching `tests.yml`, or enabling any selective execution.
- **Mode separation:** discovery, then implementation, then verification. No single prompt spans all three.
- **Self-grading:** a change to the router may not be judged by the router. That case forces the full route.
- **Conflicts:** if reality contradicts these documents, stop and surface it. Update through the Decision Log, then continue.

## 11. Slice definition of done

- [ ] All acceptance criteria pass with linked evidence.
- [ ] D-026 through D-047 are resolved in code, and S-024 through S-051 pass before receipt work starts.
- [ ] All EDD guardrails hold. No unlabeled shortcuts inside the boundary.
- [ ] Nothing in the repository is able to skip a check as a result of this slice.
- [ ] V21 and V22 added exactly as D-016 records. Q-002 and Q-003 still open and still not blocking.
- [ ] Documents updated: statuses, unknowns, log entries for anything learned.
- [ ] Human walkthrough completed and approved by Daniel Boyd.

## 12. What this unlocks

- **SLICE-002, shadow evidence campaign.** Run routing in shadow across real changes, count misses per route class, and produce the evidence that would justify enabling one class. Not a code slice so much as a measurement slice.
- **SLICE-003, selective local execution for one route class.** The narrowest class with clean shadow evidence, most likely the public-documentation route, with automatic escalation on any miss.

Selective CI stays behind both, per D-011.

---

*Approved for build by: [name], [date]. Until then, this brief is a proposal. When section 11 closes with evidence, mark the status Done and update ADD section 15 before opening the next brief.*

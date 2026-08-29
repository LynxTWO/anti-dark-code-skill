# Assurance Router Architecture Document (ADD)

Version: 0.2 Audited. Date: 2026-08-28. Authors: Daniel Boyd, Claude Opus 5, Codex. Status: Audited.
Companion documents: ENGINEERING.md, DECISION-LOG.md, SLICE-001-route-shadow.md.

This document is the puzzle. ENGINEERING.md holds the rules for placing pieces. Where the two conflict, this document's guardrails control.

---

## 1. One-Page Overview

- **What it is:** a deterministic change-impact router for anti-dark-code. It reads a diff and produces an auditable receipt naming which passes were invalidated and which evidence families the change requires.
- **Who it is for:** primary, an AI agent working in a calibrated repository. Secondary, the human who reviews what was skipped, and CI.
- **The core loop:** collect change facts from git, match reviewed routing rules, union their requirements, write a bound receipt, then execute only what the receipt names.
- **Major pieces:** fact collector, routing policy, route builder, receipt writer, receipt verifier, gate runner binding, shadow comparator.
- **Current slice:** SLICE-001, read-only shadow routing. It computes and explains routes without being allowed to skip anything.
- **What this is not:** not a risk score. Not a permission system for shortcuts. Not a new numbered pass.

The router is not new doctrine. `V11 Change-impact analysis` and `V20 Confidence ladder` are already capabilities in `assets/verification-capabilities.json`. This subsystem is the deterministic engine for two capabilities the skill already names and currently leaves to prose.

## 2. System Context

- **Actors:** the implementing agent, the reviewing human, the CI aggregator.
- **External systems:** git, which is the only source of change facts. The host agent harness. GitHub Actions.
- **Boundary statement:** inside is deciding what verification a change requires, and recording that decision so it can be audited later. Outside is running the verification, which the existing gate runner owns. Also outside: deciding whether a finding is real, which is pass 07, and any product code.

## 3. Product Shape and Platforms

- **Shape:** library plus one CLI subcommand inside an existing Python tool.
- **Platform targets:** Linux, macOS, Windows. The existing test matrix.
- **Offline behavior:** required. Routing must work with no network.
- **Distribution:** ships inside the anti-dark-code universal core.
- **Languages at launch:** one. Reason codes are stable identifiers, not prose, so they do not translate.
- **Code license:** FSL-1.1 MIT Future, same as the core.

DECISION: Product shape and platforms. Status Confirmed. See D-001.

## 4. Module Map

| Module | Responsibility | Owns what data | Talks to |
|---|---|---|---|
| Git change reader | acquire NUL-delimited committed, index, worktree, untracked, mode, and submodule records | ChangeInput records | git helpers, nothing else |
| Fact collector | turn ChangeInput records into typed change facts | ChangeFact records | route builder |
| Routing policy | reviewed rules mapping facts to requirements | `routing-policy.json` | route builder |
| Route builder | union matching requirements into one route | Route record | fact collector, routing policy |
| Receipt writer | bind a route to worktree, policy, gates, calibration, and repo identity | `route.json` | route builder, hashing helpers |
| Receipt verifier | refuse a stale receipt before anything executes | none | receipt writer, gate runner |
| Gate runner binding | select approved gates covering the route's obligations | none | existing `run_gates` |
| Shadow comparator | run full verification anyway, record what a route would have missed | `shadow.json` | gate runner |

**Module rules.**

- One owner per artifact.
- The Git change reader is the impure boundary. The fact collector and route builder are pure functions over passed data. The receipt writer and shadow comparator are the other disk-writing boundaries.
- Dependency direction: the Git change reader feeds the collector, collector and policy feed the builder, the builder feeds the receipt, and the receipt feeds the runner. Never the reverse. The gate runner must not be able to change a route.

## 5. Interfaces and Contracts

- **Interface style:** typed function boundaries in one module, plus one CLI subcommand. No new process boundary.
- **Public interfaces:**
  - `read_change_inputs(repo, base) -> ChangeSnapshot`, impure and read-only
  - `collect_change_facts(snapshot) -> list[ChangeFact]`, pure
  - `build_route(facts, policy, hints) -> Route`, pure
  - `write_receipt(route, repo) -> Path`
  - `verify_receipt(receipt, repo) -> Ok or Stale(reason_code)`
- **Contract rule:** the `routing-policy.json` schema is the one source of truth for rule shape, validated on load. An invalid policy is an error, never a default.
- **Versioning posture:** `schema_version` integer, the same convention `gates.json` already uses.

DECISION: Interface style. Status Confirmed. See D-002.

## 6. Core Data Flow

1. The caller names a comparison base.
2. The Git change reader acquires NUL-delimited records for the final merge-base to `HEAD` diff, index changes, worktree changes, untracked paths, modes, and submodule state. It does not use a names-only helper.
3. The pure collector emits facts across six dimensions: surface, effect, breadth, sensitivity, change kind, confidence. Rename and copy records classify both the old and new path. An unmerged, unsupported, or undecodable record forces the full route and names the record.
4. Each rule matches one fact using positive predicates only. Matching requirements combine monotonically. A rule may not depend on the absence, count, or ordering of other facts.
5. A receipt is written, bound to identity hashes.
6. The gate runner verifies receipt freshness immediately before each gate starts and again after it exits. A concurrent change makes that execution stale and unusable as evidence.
7. The shadow comparator runs the full set anyway and records any gate that failed while the route said it was unnecessary.

- **Trigger points:** the agent before implementation for a provisional route, the agent after implementation for the final route, and CI on a pull request.
- **Slow paths:** none. Routing reads metadata only and must stay under one second.
- **Failure path:** a known unmapped fact produces the canonical full route. Unreadable Git state or a policy load error exits 2 and produces no receipt, so the caller must use the documented full-verification path outside the router. Never a fast path.

## 7. Data Domain Overview

- **Entities:** ChangeInput, ChangeFact, Rule, Route, Obligation, Receipt, Omission, ShadowResult.
- **Key relationships:** a Route is the union over every Rule matched by any ChangeFact. A Rule binds each required capability id to one or more explicit gate ids. A Receipt binds exactly one Route to one content-identified repository state. An Omission explains exactly one gate the Route did not select.
- **Volume expectations:** tens of facts per change, tens of rules, one receipt per run. Nothing here grows with repository size except the fact list, which grows with the diff.

## 8. Technology Selection

### 8.1 Client

CLI subcommand, consistent with `probe`, `plan`, and `gates`. Status Confirmed.

### 8.2 Language

Python 3.12+, standard library only, matching `adc.py`. A new dependency would have to survive the hostile-environment matrix and the clean distribution check, which is a cost with no matching benefit here. Status Confirmed. See D-003.

### 8.3 Backend

None. Status Confirmed.

### 8.4 Database

Plain JSON files, matching `gates.json` and `verification-plan.json`. Status Confirmed.

### 8.5 Authentication

None. Trust comes from repository binding and gate review status, both of which already exist.

### 8.6 AI layer

The agent may supply hints such as "possible public contract change". Hints are inputs that can only escalate. No hint may lower a requirement, and the receipt records which hints were supplied and what they changed. Status Confirmed. See D-006.

### 8.7 Notifications

None.

### 8.8 Hosting and builds

Existing GitHub Actions. Status Confirmed.

## 9. Integration Map

| External service | Purpose | Direction | Failure behavior |
|---|---|---|---|
| git | the only source of change facts | read | incomplete history or an unreliable base forces the full route |
| GitHub Actions | computes the route from the trusted base revision | read and write | no usable route means the full matrix runs |

**Adapter rule.** All git access goes through the subprocess and byte-decoding discipline already used by the git helpers in `adc.py`. The existing `git_paths()` and `changed_files()` shapes are insufficient because they discard status and mode. The Git change reader adds one status-aware helper rather than shelling out from classification code.

## 10. Extension Points

| Future feature | Connects at | What exists now | What is deliberately absent |
|---|---|---|---|
| Gate coverage metadata | `gates.json` | rules name explicit `gate_ids` | `tags`, `covers`, `scope`, held until `gate_definition_hash` binds them |
| Selective CI execution | the `required` aggregator | full matrix always runs | route-aware skip accounting |
| Cheapest-gate optimizer | route builder | explicit route recipes | not built, deliberately |
| Provisional pre-implementation route | `route --phase` | final route only in slice 1 | phase handling |

## 11. Scale and Performance Posture

- **Load expectations:** one route per change.
- **Performance targets:** route computation under one second on this repository.
- **Scaling approach:** rule count is the only growth axis. Matching is linear in facts times rules and bounded by both.

## 12. Deployment Topology

- **Environments:** local and CI.
- **Release path:** ships with the core, version stamped, covered by the existing release check.
- **Rollback:** routing is additive in slice 1. Removing the `route` command restores current behavior exactly, because nothing is permitted to skip yet.

## 13. Failure and Degraded Modes

| Failure | Caller sees | System does | Recovery |
|---|---|---|---|
| Missing or unreachable merge base | full route with a reason code | refuses any fast path | rerun with full history |
| Git output is unreadable or internally inconsistent | error, exit 2 | produces no receipt | run the documented full verification outside the router, then repair collection |
| Policy fails its schema | error, exit 2 | produces no receipt | run the documented full verification outside the router, then fix the policy |
| Receipt no longer matches worktree | exit 2 | refuses to execute | recompute the route |
| Path matches no reviewed rule | full route | records the unmapped path | add a reviewed rule |

## 14. Architecture Guardrails

1. No route may lower a requirement. `minimum_level` uses maximum, set fields use union, and boolean requirements use logical OR. `force_full` dominates every other value and selects the policy's canonical full recipe.
2. No agent hint may lower a requirement. Hints may add passes, capability ids, and gate ids, raise `minimum_level`, or set boolean requirements to true. They may not alter facts, rule matches, the comparison base, or any existing value.
3. A change to routing code, routing policy or schema, gate configuration, capability definitions, CI, installer or distribution controls, Git interpretation files, router tests, or shared test infrastructure forces the full route. `SKILL.md` and the pass 00, 10, and 14 references are verification-authority inputs and force the full route. In CI the trusted base revision computes this decision.
4. The fact collector must not reuse `changed_files()`. That helper drops `.agents/skills/` and `.anti-dark-code/` through `TOOLING_PATH_PREFIXES`, which is exactly where `gates.json` and `routing-policy.json` live. Reusing it would make the router blind to its own escalators.
5. No gate executes from a receipt that no longer matches the content and modes of committed, staged, unstaged, untracked, symlink, and submodule inputs, the routing policy, the gate definitions and bound sources, calibration, or repository binding. A status-shape hash alone is not a content identity.
6. Every omission carries a stable reason code. A skipped check is an explained decision, never an absence.
7. Slice 1 may not skip anything.
8. No routing-relevant candidate may disappear before policy evaluation. Both sides of a rename or copy are evaluated. Type changes, conflicts, unsupported Git statuses, and submodule uncertainty are represented explicitly and force the full route unless a reviewed rule is stricter.
9. The policy binds each required capability id to at least one explicit gate id. Parallel unlinked `obligations` and `gate_ids` arrays are invalid because they cannot prove which gate satisfies which obligation.
10. A full route means the policy's validated full recipe: Level 3, every required pass and capability for that repository, and every enabled approved gate in the recipe without changed-file glob filtering. If the policy cannot validate, no selective receipt exists.

## 15. Current Build Boundary

- **Current slice:** SLICE-001, read-only shadow routing.
- **Modules the slice builds:** Git change reader, fact collector, routing policy, route builder, receipt writer, receipt verifier.
- **Modules the slice stubs:** shadow comparator records only. Gate runner binding reads a receipt but still runs the full set.
- **Everything else:** designed above, deliberately unbuilt.

---

*End of Architecture Document. Sections filled: 15 of 15. Unknowns carried: see ENGINEERING.md section 16.*

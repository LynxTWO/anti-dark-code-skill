# Handoff to Codex: round eleven

Date: 2026-08-30. Starting point: the commit that closes `HANDOFF-BACK-ROUND-TEN.md`.

## Objective

Resolve the D-070 M3 evidence gaps, then repair the M4 implementation plan. Do not implement M4 in this round. The deliverable is an owner-reviewed M3 contract plus a reviewed, executable M4 plan; either may remain blocked when a required authority decision is not supplied.

Read these files completely before changing the plan:

1. `design/routing/HANDOFF-BACK-ROUND-TEN.md`
2. `design/routing/DECISION-LOG.md`, especially D-064 and D-067 through D-070
3. `design/routing/SLICE-001-route-shadow.md`
4. `design/routing/plans/2026-08-28-assurance-router-slice-001.md`, especially Tasks 10 through 12 and its Self-Review
5. `design/routing/requirement-evidence.json`

## M3 evidence gaps to resolve first

### R-005 and R-021: self-grading paths

The current synthetic CI fact is partial evidence. With proposed rules changed to approved in memory, real router code, capability-catalog, and routing-owning pass paths receive non-full routes. Do not add a policy rule or hard escalator without owner review.

Produce a complete authority-path table from the requirement, classify each real path, and present the narrow design alternatives. The chosen contract needs one collected test per authority class and a counterexample proving an ordinary non-authority path does not force full accidentally.

### R-017 and R-019: submodule state

The EDD requires `submodule_state`, but the implemented data model and tests do not define it. Specify which Git records and dirty states are supported, how they enter `ChangeInput`, how receipt identity binds them, and which unsupported form fails closed. Use real repository fixtures where Git behavior is the claim.

Do not mark these requirements traced until the full clauses are implemented and their exact test node ids collect. If the requirements should be narrowed instead, make that an explicit design decision rather than editing the evidence map alone.

## M4 blocking contradictions to resolve after M3

### 1. Candidate route versus authority route

Every installed rule is `proposed` under D-064. The authoritative route therefore forces the canonical full set. The current Task 11 comparator consumes that route's `selected_gate_ids`, sees no omissions, and cannot measure what a proposed rule would have omitted.

Define a separate candidate-shadow result that may evaluate proposed rules for measurement without becoming an executable route, receipt authority, or permission to skip. State its type, provenance, serialization, and failure behavior. A candidate must never flow into gate selection.

### 2. R-018 before-and-after binding

The current Task 10 verifies freshness only before the run. R-018 requires a repository mutation before launch or during a gate to invalidate that gate's evidence.

Show the actual runner lifecycle and exact tests:

- verify the bound receipt before execution;
- capture the authoritative identity immediately before each gate;
- capture it again after the gate;
- mark the gate result stale when the identity moves;
- prevent a stale result from satisfying any obligation;
- keep running or fail closed according to an explicit decision, never by accident.

The plan must name the production seam that returns gate results. A helper-only unit test is not runner integration evidence.

### 3. R-022 canonical full execution

Show how `gates --route` still executes the canonical approved full set during shadow mode. `include_globs`, candidate selections, and proposed rules must not remove a gate. `--level` may raise the route minimum and must exit 2 when it would lower it (R-013).

### 4. Comparator integration

Task 11 currently defines `shadow_result` without connecting it to a full gate run. Define where actual gate outcomes are collected, how the candidate route is compared with them, where `shadow.json` is written, and how incomplete, stale, skipped, or unrecognized gate outcomes are represented. A non-pass omitted outcome must not be silently treated as a pass.

## Traceability gate

Before proposing M4 implementation:

- close or explicitly redesign R-005, R-017, R-019, and R-021 under D-070;
- map R-013, R-018, and R-022 to exact planned test node ids;
- add those node ids to `requirement-evidence.json` only when the tests exist and collect;
- keep the untraced set fixed until then;
- include at least one process-level CLI test for downgrade refusal and stale receipt refusal;
- include a real runner-integration test for mutation during a gate;
- include a test proving proposed-rule candidate evaluation cannot change the executed gate set.

## Non-negotiable boundaries

- Do not approve any routing-policy rule.
- Do not enable selective local or CI execution.
- Do not make a candidate route acceptable to the receipt verifier or gate selector.
- Do not alter tailnet policy.
- Do not claim a current macOS result; macOS evidence remains the configured CI suite only unless an observed run is supplied.
- If the repaired design needs a new owner decision, record the alternatives and stop for that decision instead of choosing authority silently.

## Deliverables

1. An owner-reviewed decision and evidence plan for R-005, R-017, R-019, and R-021.
2. Revised Tasks 10 through 12 with no placeholder prose standing in for code or tests.
3. Updated plan Self-Review with every former blocking placeholder resolved or explicitly left blocking.
4. A criterion-by-criterion mapping for all seven ids in the reviewed untraced set.
5. `design/routing/HANDOFF-BACK-ROUND-ELEVEN.md` containing the M3 verdict, M4 plan-review verdict, unresolved owner decisions, exact files changed, and whether M4 is eligible for an implementation round.

Do not mark M4 started merely because the plan text changed. Eligibility requires the round-eleven adversarial review to pass.

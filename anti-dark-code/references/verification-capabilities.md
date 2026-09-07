# Verification capability index

Use this optional index to interpret a selected capability or an unresolved planning disposition. The authoritative machine definitions, statuses, IDs, defaults and adaptations remain in [verification-capabilities.json](../assets/verification-capabilities.json). This prose does not change its stored semantics.

A comprehensive plan mechanically screens every catalog entry under [verification planning](14-deterministic-verification.md). A narrow task can assess a declared subset without loading all detailed recipes. Apply [core evidence and execution](../SKILL.md): selection is not execution and execution is not a broader guarantee.

| ID | Capability and useful proof | Important limit or trigger |
|---|---|---|
| V01 | Mutation: alter important semantic decisions and examine surviving mutants. | Meaningful tests/stable oracle first; [restoration](specialist-mutation-restoration.md), counts and survivor diagnosis matter more than score. |
| V02 | Model-based stateful tests: legal actions, preconditions, invariants, shrunk traces. | Preserve random exploration; use adversarial sequences for risky transitions. |
| V03 | Executable invariants at state, event, transaction and trust boundaries. | Avoid type restatements, leaking assertions and accidental production crashes; define failure policy. |
| V04 | Differential tests against old/simple/native/reference implementations. | Define equivalence and normalization; shared bugs can make two copies agree. |
| V05 | Metamorphic relations across transformations: chunking, ordering, scaling, round trips. | Assert a valid domain relation; transformation itself may change semantics. |
| V06 | Deterministic mode with explicit clock, RNG, IDs, locale, configuration and initial state. | Capture schedules or limit concurrency claims; raw-representation ties need [canonical-output proof](specialist-verifier-falsifiability.md). |
| V07 | Record/replay corpus from minimized seeds, start state, actions and versions. | Redact sensitive state and bind full replay identity. |
| V08 | Schemas/contracts at external, persisted, generated and process boundaries. | Parse at the boundary; define ownership, compatibility, defaults, migrations and failure policy. |
| V09 | Static architecture checks for layers, forbidden imports, cycles and ownership. | Track exceptions with owner/expiry; include dynamic and non-import edges. |
| V10 | Exact reviewed quality gates with real exits and compact verdicts. | Configured checks alone are not observed behavior; see [gate contract](specialist-exact-gate-contract.md). |
| V11 | Change impact across imports, ownership, coverage, schemas/events and gates. | Add config, content, generated, deployment and control-plane dependencies; incomplete graphs require conservative selection. |
| V12 | Hermetic builds/tests: pinned tools, isolated temp state, locale/timezone, network substitutes. | Hidden downloads, home files and mutable services invalidate hermeticity claims. |
| V13 | Reviewed semantic golden/snapshot comparisons. | Normalize irrelevant differences; reject giant noisy snapshots and blind baseline updates. |
| V14 | Performance/leak budgets for latency, throughput, memory, resources and UI growth. | A claim needs workload, baseline, budget and noise analysis. |
| V15 | Fault injection for timeouts, duplicate/missing events, partial writes and worker/storage failure. | Use disposable isolation and applicable approval; never infer live-system testing permission. |
| V16 | Authoritative map from manifests, counts, entrypoints, dependencies and freshness identity. | Agents interpret purpose, rule authority, ownership and external boundaries; generated maps are incomplete evidence. |
| V17 | Builder/challenger/verifier separation for consequential or unfamiliar work. | Scale to stakes and host support; model voting is not an oracle and trivial edits need no fan-out. |
| V18 | Test-change review of skips, assertions, snapshots, mocks, timeouts and exceptions. | Name the changed contract; reject weakening solely for green. |
| V19 | Minimal failure packet with command, real exit, first failure, identity and replay/log locator. | Bound/redact output; never dump secrets or whole sensitive state. |
| V20 | Confidence ladder from cheap edit checks through task, merge and scheduled checks. | Use existing levels 0-3; measure runtime, failure history and blast radius. |
| V21 | Affected-unit testing with actual executed ownership set. | Record omitted checks; a selected test that never ran supplies no evidence. |
| V22 | Hostile/malformed input fuzzing with minimization and a replay corpus. | Fuzz in-process behind a seam; do not launch external tools or touch user files. |

The planner's configured core selection remains recoverable from the machine catalog. Evidence can justify deferral or non-applicability; defaults are starting points, not permission to install every tool. Mixed repositories combine evidence by runtime unit. A single backend or platform result cannot stand for the rest.

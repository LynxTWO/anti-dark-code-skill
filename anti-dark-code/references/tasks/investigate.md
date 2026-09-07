# Investigate

Use for audits, risk assessment, readiness, or uncertain failures. The [core](../../SKILL.md) controls evidence and authority. Investigation produces findings; remediation needs its own authorization.

## Inputs

Question, requested breadth, symptom or invariant, relevant map fragments, source identity, and existing findings. Comprehensive work needs the inventory from [Understand](understand.md); focused diagnosis needs the paths affecting its claim.

## Procedure

1. State a falsifiable claim or failure condition. Locate the authoritative rule and enforcement path. Record trigger, input, state transition, affected output, and consequence. Classify source facts, configured behavior, observations, and guarantees before selecting proof.
2. Inspect counterevidence: upstream validation, alternate callers, platform branches, ownership boundaries, and existing tests. A keyword hit or plausible story is not a supported defect.
3. Load specialists by observed risk. Logs, telemetry, or error capture load [logging](../04-logging-audit.md). Hidden authority, concurrency, destructive paths, or an adversarial request load [adversarial review](../07-adversarial-review.md). Requests to challenge maps or steering with hypothetical failures load [scenario stress testing](../08-scenario-stress-test.md). For actual stateful journeys, derive input/state/expected-outcome cases under Verify. Locale keys, labels used as state, or saved prose load [language boundaries](../12-transcreation-boundary.md).
4. Search scoped source, not a filename listing. Record query, candidate and finding counts, exclusions, and a known-positive check. Zero candidates leaves a surface unexamined. Trace a concrete path before calling a match a supported finding.
5. Use deterministic checks that distinguish competing explanations. Load [Verify](verify.md) before execution or verification planning. If execution is unavailable, name the missing observation and retain the behavioral claim as inferred or unknown. Directly inspected configuration facts do not require runtime proof.
6. Challenge consequential claims with a counterexample or deterministic oracle. Give participating agents the claim, evidence, and falsification condition; agreement is not verification. Reconcile a comprehensive audit against its inventory, including negative findings and inaccessible external state.

## Evidence and output

Each finding names severity (`low`, `medium`, `high`, `critical`), statement, kind, confidence, trigger, consequence, source evidence, counterevidence, scope, next check, and proposed action. Exposure and evidence categories do not replace severity. Group manifestations only when a shared root cause is demonstrated.

Rank by plausible consequence and evidence, not match counts. Separate source defects from unexercised paths, toolchain/native blockers, unavailable capabilities, and external-state blockers. An unavailable SDK is not a product defect.

For readiness, state the release or operational criterion and satisfying evidence. Load the matching [assurance contract](../assurance-contracts.md) before accepting a guarantee. Independent passing checks do not prove that an audited set is complete, current, or consistent.

## Stop conditions

Stop before protected edits or unauthorized execution. Report sensitive-data classes and redacted locators, never payloads. Where several explanations fit, state the discriminating check. Retry a blocked branch only with changed conditions or a new check. Finish with findings and coverage dispositions, including zero findings and unresolved areas.

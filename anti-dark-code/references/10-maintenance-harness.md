# Maintenance harness and drift prevention

Compatibility reference `10`. Use when the user requests lasting guardrails or a supported drift finding needs repo-fit automation. Enter through [Verify](tasks/verify.md) or [Remediate](tasks/remediate.md). Apply [core authority and evidence](../SKILL.md); this workflow does not automatically install tools, add dependencies or expand into application changes.

## Fit existing workflow

Choose the smallest useful existing PR template, CONTRIBUTING note, reviewer checklist, CI/policy script or maintenance document. Reuse current steering, maps, relevant unknowns and affected-slice reviews. Do not create every possible artifact or invent a bot/platform the repository does not use.

A nontrivial change record states what changed, why, remaining uncertainty, changed risk, approval state, relevant doc changes and checks actually run. Trigger only helpful map/runbook/ADR/manifest/rollback/observability/release/language notes when corresponding critical paths change. Update tracked coverage when obligations or evidence change; tiny unrelated edits do not need ledger churn.

Protected actions follow current core authority and existing owner routing. If approval automation does not exist, state the manual reviewer obligation. A template cannot grant permission.

## Keep load-bearing explanations and contracts

Comments carrying rationale, invariants, trust/privacy/security boundaries, side effects, ordering, idempotency, concurrency, operator repair/rollback hazards or language boundaries must stay accurate when guarded code changes. A removal/move/material rewrite supplies an adjacent replacement preserving the rule, or an intentional retirement note explaining why it no longer applies. Syntax restatements are not protected rationale.

Use a light continuity detector only where it fits: diff/sentinel checks, PR fields or reviewer prompts. It cannot prove equivalent meaning, discover unmarked comments or distinguish a move from deletion perfectly. Calibrate clean and known-bad cases and retain manual semantic review. Track deferred TODOs through [remediation edges](specialist-remediation-edges.md).

Add bounded logging/telemetry checks for actual capture paths: token/raw body patterns, query/header leakage, crash/analytics/AI tool traces and sensitive examples. Pattern checks detect drift; they do not prove privacy. Keep manual review and automation clearly labeled.

## Verification ownership

Use [verification planning](14-deterministic-verification.md) for exact command arrays, reviewed source bindings, execution state and the confidence ladder. A comprehensive plan mechanically screens every catalog entry; a scoped guardrail task assesses only declared obligations and says so. Select useful capabilities, not a mandatory tool suite.

Gate reports retain real producer exit codes, source/environment identity, discovered and executed test counts, expected target/configuration/architecture tuples, required artifact membership/provenance and dynamic registrations. Zero discovery fails the invocation. A manifest proves shape only; allowlisted failures remain debt.

Load conditional recipes when their trigger is present:

- [Gate environment](specialist-gate-environment.md): configured runner, exclusive scratch files, frozen locks, build artifacts and measured timeout margins.
- [Process verdicts](specialist-process-verdicts.md): output wrappers, cleanup and safe process identity.
- [Audited producers](specialist-audited-producers.md): a gate joins a set certified by an audit.
- [Falsifiable verifiers](specialist-verifier-falsifiability.md): equality, thresholds or detectors need meaningful negative fixtures.
- [Restricted builds](specialist-restricted-builds.md): flags remove runtime capabilities.

Use change-impact edges across imports, contracts, configuration, content, generated files, deployment and control planes. Preserve minimized replayable regressions from exploratory failures and retain random exploration alongside stateful models. Games, simulations and other emergent systems need a fixed-input aggregate canary when aggregate behavior is in scope, with reviewed range, false-positive history and rerun cost.

## Result

Return installed/proposed assets, hard gates versus reviewer duties, exact approved/configured/executed evidence, environmental prerequisites and unsupported runtimes/boundaries. Reuse `docs/review/maintenance-harness.md` and relevant unknowns when authorized. Finish when the requested guardrails are reviewable and verified within their actual scope; configured automation is not an observed guarantee.

# Verify

Use for verification planning, test evidence, gate diagnosis, or an audit's verification portion. The [core](../../SKILL.md) controls authority and execution. Selection is not execution or owner approval.

## Inputs

Claim or changed behavior, source identity, runtime/platform tuple, test and configuration evidence, authorized commands and side effects, and coverage contract. Distinguish source facts, configuration, observations, and guarantees before choosing checks.

## Procedure

1. Inspect existing gates and dependencies. Prefer a deterministic check that can falsify the claim. A configured script proves configuration only. Confirm test discovery and path reachability before interpreting green output.
2. When trusted bundled tooling is available and useful, use read-only `scripts/adc.py plan --repo <target>` from the skill directory. It screens the machine catalog. Comprehensive plans reconcile every catalog ID and disposition; inspect selected/candidate entries and risk-material exclusions. Focused tasks state their smaller claim and omitted capabilities. Static planning cannot discover every runtime obligation.
3. Load [verification planning](../14-deterministic-verification.md) for capability selection or gate plans, [maintenance harness](../10-maintenance-harness.md) when defining a harness, and the matching [assurance contract](../assurance-contracts.md) before accepting broader guarantees such as atomicity, availability, repair, readiness, or audited-set completeness.
4. If prerequisites are unavailable, inspect manifests, tests, and target branches manually. Name missing Python/runtime/SDK/permission/format and unperformed checks. Installation is not required to plan. Missing observations leave live claims inferred or unknown.
5. Before repository execution, inspect exact argv, working directory, environment, input paths, dependency hooks, network/persistent effects, and timeout/cleanup. Bind review to current command and source. Carry existing authorization while bindings match; otherwise propose the concrete command and stop for missing execution or protected-effect approval.
6. Preserve dry-run defaults and approval locks. Existing `route` selects verification for a change and binds evidence to a receipt; it is not a task-card selector. Unknown impact requires conservative checks. Do not enable selective execution merely to shorten a run.
7. Capture actual exit status, discovered/executed/failed/skipped counts, target tuple, and exercised boundary. Keep successes compact and failures bounded and redacted. Zero exit with zero tests is unexercised. Failed prerequisites are blockers, not source defects or passes.

## Evidence and output

Return proposed and executed commands separately, capability dispositions, tested scope, observations, limits, and next checks. Cite obligation-specific evidence and source identity for guarantees. Record unavailable targets instead of extrapolating across hosts. Managed wrappers cannot prove native behavior without reaching the native implementation.

Keep exploration reproducible with a seed or trace and named oracle. Preserve mutation restoration and cleanup evidence. A hash or receipt binds recorded inputs; it is neither an owner signature nor correctness proof.

## Stop conditions

Stop before unauthorized execution, changed approval bindings, missing prerequisites, or unreliable cleanup. Changed gates invalidate dependent acceptance. Never hide failures through weaker assertions, skips, or inflated timeouts. A plan completes a planning request, but cannot complete a request for executed verification. Report passed obligations and residual uncertainty separately.

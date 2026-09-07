# Architecture and trust-boundary map

Compatibility reference `02`. Use with [Understand](tasks/understand.md) when the requested outcome needs runtime, ownership, data, or trust-boundary evidence. It does not require an earlier numbered pass. Apply the [core contract](../SKILL.md); application code stays read-only and documentation writes stay within the active authority.

## Inputs and method

Use existing current maps and the requested scope. Inspect manifests, lockfiles, start/build/test configurations, deployment and CI files, schemas, API definitions, migrations, integration tests, scripts and ownership records. Prefer a useful trusted read-only probe under the core execution rule; retain scan limits and contradictions. Missing code in a scaffold stays proposed or `TBD`.

Choose branches from source/runtime evidence. A mixed repository needs a row for each runtime unit, not one winning classification. For large or interrupted work, use [coverage slicing](05-coverage-slicing.md). When source demonstrates quiet operational paths or specialty runtimes, use [hidden control planes](specialist-hidden-control-planes.md).

## Map contract

Record compact tables or flow notes with evidence locators:

- **Runtime unit:** purpose, repo location, entry/start command, caller/trigger, dependencies, owner, data and side effects. Include services, workers, jobs, public libraries, clients and live scripts/tools.
- **Interface:** route, topic, public API, UI action, CLI/task target or hook; validation/authentication, privileges, reads/writes and downstream systems.
- **Data:** stores, entities, important relationships, retention/deletion behavior supported by code, and operational use. Include browser/device storage, saves, caches, vector/model stores and remote infrastructure state where present; avoid exhaustive field dumps.
- **Dependencies/configuration:** why each external system is used, dependent units, required/optional/environment-specific key names, failure/retry/fallback/dead-letter/manual recovery evidence. Record secret names only.
- **Trust edge:** incoming authority, validation, assumptions, privilege changes and failure consequences. Include native bridges, tool execution, deploy runners and vendor consoles when observed.
- **Critical flow:** trigger, participating units, stores, jobs, external calls, irreversible effects, ordering/idempotency and recovery.
- **Rule authority:** canonical implementation, downstream adapters/views/migrations, divergence guard, approved duplicate owner and expiry. State whether diagnostics are observational; authoritative reads from telemetry are a boundary.
- **Language:** ownership, truth/display/mixed, persistence and dependencies on IDs, hashes, replay, ranking, access, pricing or policy. Use [language boundaries](12-transcreation-boundary.md) when present.
- **Operational and external gaps:** deployment, flags, locks, backfills, manual release steps, missing owners and evidence outside this checkout. Submodules, sibling repos and vendor dashboards retain separate unresolved obligations.

A claim that code is dead, unreferenced, imported or reachable must name its graph. Load [native/dynamic reachability](specialist-native-reachability.md) for the implementation-to-build-to-package-to-loader-to-selection-to-invocation chain and target-specific terminal descriptions. A clean-checkout missing generated binary does not establish a blocker.

## Output and stop

Return the scoped map and unresolved obligations using [core evidence](../SKILL.md#evidence). Reuse `docs/architecture/system-map.md` or `service-map.md` and `docs/unknowns/architecture-pass.md` when durable artifacts are useful and authorized; otherwise a report is sufficient.

Finish when every declared unit and boundary has evidence or an explicit gap with impact and next check. Do not let one clean path stand in for a parallel script, native target, sibling repository or remote control plane. Commenting, remediation and harness installation are separate requested outcomes.

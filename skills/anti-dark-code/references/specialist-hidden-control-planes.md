# Hidden entrypoints and control planes

Trigger: mapping or investigating a mixed/specialty repository, or source/configuration shows operational paths outside the main runtime. Apply [core scope and evidence](../SKILL.md). Result: each live path has an owner, trigger, authority, side effects and local/external evidence boundary.

Inspect package scripts, task runners, Makefiles, notebooks, support/admin tools, one-shot repair scripts, bootstrap/import hooks, CI/CD jobs, release automation, migrations/backfills, fixtures that ship, generated code with handwritten neighbors, and incident-only procedures. A configuration or marketing mention is not observed implementation.

Trace feature flags, remote config, CMS content, remote prompt stores, model routing, safety settings and vendor/platform dashboards when they change live behavior. Record submodules, linked workspaces, mirrored trees, sibling deployment repos and manual release actions explicitly. Local inspection cannot establish their current remote state.

Use the matching runtime branch:

| Branch | Entry and authority obligations |
|---|---|
| Service/backend | Routes, webhooks, queues, scheduled/privileged jobs, retries, deletion/export and external sync; follow idempotency and irreversible effects. |
| Frontend/browser | Pages, navigation, state stores, API clients, browser storage, telemetry, flags, build outputs and copy ownership. If code reads rendered text or DOM state as truth, trace it to the authoritative data and test divergence. |
| Library/SDK | Public APIs, extension points, code generation, build targets, dynamic discovery, compatibility and release consumers. |
| Game | Client/server authority, scenes/prefabs/actors, saves and replay, editor tools, asset imports/build hooks, economy, entitlements, anti-cheat, live ops, platform services and narrative versus mechanics. Explain engine-owned serialized assets in adjacent docs. |
| Mobile/native | App/navigation and deep links, permissions, secure/local storage, native bridges, sync, push/background jobs, crash/analytics, provisioning, app-store consoles and release hooks. Backend results do not cover native tuples. |
| Infrastructure | Modules/stacks/accounts, state backends, IAM, secret stores, runners/controllers, ingress/DNS/network/storage, environment overlays and plan/apply/import/drift-repair paths. Apparently read-only helpers may write live state. |
| AI/data | Jobs/notebooks, feature/vector stores, models/registries, evals and labeling lineage, prompt/tool boundaries, filters/routing, remote settings, batch backfills and support access to live content. Separate deterministic pipeline contracts from probabilistic quality. |

At trust changes, name validation and the consequences of bypass. Follow client-to-server, native/secure-storage, runner-to-cloud, release-to-platform, model-to-tool and rendered-language-to-structured-truth edges. Sensitive paths and protected edits follow core authority; discovering a path does not authorize using it.

Before accepting broad coverage, challenge alternate triggers and environments. A flow spanning an unavailable repository or console remains partial, with the missing owner/check named. Use [native reachability](specialist-native-reachability.md) for shipping or invocation claims, [logging audit](04-logging-audit.md) for capture paths and [language boundaries](12-transcreation-boundary.md) for authored/persisted text.

# Reference: Architecture Inventory and Trust-Boundary Map

Use this reference when mapping a repo before any code changes. This is the baseline anti-dark-code inventory pass.

**Mode:** read-only for application code. Docs may be created or updated.

For confidence levels, the unknowns entry shape, and default deliverable paths, see `00-conventions.md`.

## Goal

Create a clear map of the repo so a new engineer can understand what exists, how the system is entered, what data it stores, what it depends on, where trust changes, and which areas are still unclear.

Use the large-repo slicing pass (`05-coverage-slicing.md`) when one map would be too broad to trust.

Use the adversarial edge-case review (`07-adversarial-review.md`) after the first map when the repo has many exceptions, hidden runtimes, or protected areas.

## Pick the repo branch that fits

Inspect the repo type first. Use only the branches that match verified repo evidence. A mixed repo may need more than one branch.

**For a service or web app:** inventory services, routes, jobs, data stores, secrets, third-party systems.

**For a monorepo:** inventory apps, packages, shared libraries, deployment units, internal dependencies, ownership edges.

**For a frontend-only repo:** inventory pages, UI entrypoints, state stores, API clients, browser storage, analytics hooks, feature flags, build outputs, route copy ownership, and locale or translation boundaries when present.

**For a library or SDK:** inventory public APIs, extension points, code generation, build targets, release steps, test harnesses, external integrations.

**For a game repo:** inventory client runtime, authoritative server pieces, scenes or levels, prefabs or actors, save and load paths, asset pipelines, economy logic, authored text versus mechanic truth, entitlement checks, platform services, analytics, live-ops flags, crash reporting, and anti-cheat boundaries when present. Treat editor scripts, build scripts, import pipelines, and engine-owned metadata as part of the repo shape when they affect live behavior.

**For a mobile or native app:** inventory app entrypoints, navigation, local storage, permissions, sync paths, push messaging, background tasks, crash reporting, analytics, secure storage, provisioning hooks, native bridges.

**For an infra-as-code repo:** inventory modules, stacks, accounts or projects, state backends, IAM boundaries, secret stores, controllers, runners, deployment workflows, ingress, DNS, network edges, storage. Treat bootstrap scripts, import or migration steps, plan or apply helpers, and environment overlays as first-class runtime or control-plane paths when they can change live state.

**For an AI or data system:** inventory jobs, notebooks, pipelines, feature stores, vector stores, model registries, eval paths, prompt templates, safety filters, routing layers, tool execution, batch backfills, labeling flows, data lineage edges. Treat notebooks, experiment runners, and offline jobs as live entrypoints when they touch production data, models, or user content.

**For a new repo:** write a proposed system map from scaffolding, manifests, ADRs, and roadmaps. Mark undecided areas as `TBD`. Do not invent routes, tables, jobs, scenes, or pipelines that do not exist.

## Sources to inspect

At minimum:
- root docs and READMEs
- package manifests and lockfiles
- build and test configs
- container or deployment files
- CI workflows
- environment examples
- migration files and schema files
- queue or job configs
- API definitions
- infra-as-code files when present
- integration tests and smoke tests
- package scripts, task runners, Makefiles, npm scripts, editor scripts, notebooks, admin tools, support scripts, one-shot ops scripts when present
- app manifests, platform config, engine config, entitlement files, crash or analytics setup, provisioning files, CI or CD workflows, release automation, remote-config hooks, feature-flag integration points when present
- copy, content, locale, transcreation, text-lint, generated-prose, prompt, and template docs when present

## Deliverables

Create or update:
- `docs/architecture/system-map.md` (or `service-map.md` if the repo already uses that filename)
- `docs/unknowns/architecture-pass.md`

Use a coverage ledger or nested ledgers when one flat map would hide gaps.

Use the `system-map.md` template under `assets/templates/` for structure.

## What to put in `docs/architecture/system-map.md`

### 1. System summary

Short summary:
- what the repo is
- main runtime model
- main data stores
- main external dependencies
- main high-risk domains
- likely non-obvious live entrypoints and control-plane paths, if verified

### 2. Runtime units and entrypoints

List every runtime unit you can confirm: web app, API service, worker, scheduled job, queue consumer, CLI, serverless function, mobile app, browser extension, batch job, data pipeline, game client, authoritative server, editor tool, notebook or ops script that hits live systems, CI or CD job with live side effects, release or migration runner.

For each:
- what it does in one sentence
- where it lives in the repo
- how it starts
- what it depends on
- who calls it or what triggers it
- what data or side effects it owns

### 3. Interface surface

Map the ways the system is entered: REST routes, GraphQL operations, gRPC methods, message topics and consumers, webhooks, CLI commands, scheduled tasks, UI actions that trigger backend flows, public library APIs, package scripts or task targets that touch live systems, notebooks or support tools that can read or write live state, editor import or build hooks when they affect shipped behavior, CI or CD jobs, release scripts, migration runners that can deploy, seed, migrate, backfill, or repair live state.

For each entrypoint:
- method or trigger
- path, topic, command, target, or function name
- what it does
- whether auth or special privileges are required
- what data it reads or writes
- what downstream systems it touches

### 4. Data stores and schemas

List each data store: SQL tables, NoSQL collections, object storage buckets, search indexes, cache keys or namespaces, vector stores, local device storage, save files or cloud saves, feature-flag config, files on disk that matter at runtime, remote state for infra, model registries and eval artifacts.

For each:
- what it stores
- key entities or fields
- important relationships
- retention or deletion notes if visible in code
- anything non-obvious about how it is used

Do not dump every field. Keep the map readable.

### 4a. Language and rendered-text surfaces

If the repo has player-facing or user-facing text, map the surfaces that could blur display and truth: UI copy, authored content, templates, prompts, localized files, generated prose, saved summaries, email text, notifications, policy text, and test snapshots that lock wording.

For each:
- owning layer or package
- whether it is display, truth, or mixed
- whether it is persisted
- whether it feeds ids, hashes, replay, ranking, permissions, billing, analytics, migrations, or validation
- what docs, tests, or validators protect the boundary

### 5. External dependencies

List every external system the repo talks to: identity providers, payment providers, email or SMS services, storage providers, search services, analytics and telemetry vendors, error tracking, AI providers, platform commerce APIs, internal company APIs outside the repo, cloud control planes and secret stores.

For each:
- why the repo uses it
- how it is configured
- which runtime units depend on it
- what breaks if it is down
- any retry, fallback, dead-letter, or manual recovery behavior you can confirm

### 6. Secrets and configuration

List every environment variable, secret name, key config file, config input, and out-of-repo control surface the system needs.

Rules:
- include key names only
- do not include values
- note which runtime unit, control-plane path, or external system uses each one
- note whether it is required, optional, or environment-specific when the code makes that clear
- call out remote config, feature-flag vendors, CMS-backed behavior, app-store or platform consoles, and similar out-of-repo inputs when they change live behavior

### 7. Trust boundaries and privilege edges

Mark where trust changes: internet to API, browser to backend, public user to authenticated user, standard user to admin user, app server to database, service to third-party API, worker consuming untrusted messages, game client to authoritative server, mobile app to native bridge or secure storage, repo runner to cloud control plane, CI or CD system to deploy target or migration target, release tooling to app-store or platform console, model or agent layer to tool execution.

For each boundary:
- what validation or auth happens there
- what assumptions the code makes
- what can go wrong if the boundary is handled loosely

### 8. Critical data flows

Document applicable critical flows at a high level. Examples: signup to first successful login, checkout or billing event, file upload and processing, match or ranking or recommendation generation, admin action with side effects, user deletion or export, message send or notification fanout, third-party webhook ingestion, save or restore of game or mobile state, model prompt to tool call to result storage, infra plan, apply, import, or drift repair path.

For each flow:
- the trigger
- the main entrypoints involved
- which data stores are read or written
- which background jobs or queues are used
- which external systems are hit
- key trust boundaries crossed

### 8a. Rule authority and diagnostics

For each important rule, name:

- the canonical implementation
- downstream views, adapters, migrations, or compatibility layers
- the guard that detects divergence
- any approved duplicate and its expiry or ownership

Also state whether diagnostics, black boxes, tracing, analytics, and test probes are observational only. If authoritative behavior reads diagnostic state, treat that as a trust boundary and explain why.

### 9. Operational notes

Capture anything verifiable about deployment topology, feature flags, retries and backoff, idempotency, locking or concurrency controls, cleanup jobs, backfills or scheduled maintenance, package scripts or notebook flows used for prod support, CI or CD automation and release tooling that can change live behavior, remote config or feature-flag surfaces outside the repo, manual recovery steps that appear in repo docs or scripts.

### 10. Known gaps and rough edges

If something is messy, say so. If ownership is unclear, say that. If one clean path hides a second path through a script, tool, notebook, or admin task, name both.

## What to put in `docs/unknowns/architecture-pass.md`

Record anything you cannot confidently explain. Use the unknowns entry shape from `00-conventions.md`.

## Worked example: a runtime-unit row

A useful row names what runs, where it starts, and what it owns. Both rows below describe the same worker; the first is enough to act on, the second is filler.

```markdown
| Unit | What it does | Where it lives | How it starts | Depends on | Triggered by | Data/side effects |
|---|---|---|---|---|---|---|
| billing-worker | retries failed Stripe charges; writes idempotency keys | services/billing-worker | systemd unit `billing-worker.service` (prod); `pnpm dev:billing` (local) | Stripe API, Postgres `billing_attempts`, Redis lock keys | scheduler in cron-runner | writes `billing_attempts`; emits `billing.retry` events |
| billing-worker | handles billing | apps/billing | runs in production | the system | scheduler | various |
```

The first row can survive a code change. The second cannot.

## Rules

- No application code changes. No inline comments in this pass.
- Prefer tables and short lists over long prose.
- Use the repo's real names for systems and modules.
- Do not let one clean runtime path hide a second entrypoint with side effects.
- Do not flatten out-of-repo control surfaces, submodules, sibling repos, or vendor dashboards into full local coverage.

## Acceptance checklist

The result should let a new teammate answer:
- what runs here
- how requests, jobs, commands, scripts, or tools enter the system
- where important data lives
- which third parties matter
- which secrets and config inputs exist
- where the trust boundaries are
- which non-obvious live entrypoints and control-plane paths exist
- which out-of-repo boundaries still shape behavior
- what is still unclear

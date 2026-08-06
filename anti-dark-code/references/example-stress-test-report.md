# Reference Example: Mock Repo Stress-Test Report

This is an example of what a scenario stress-test report looks like when the check actually surfaces gaps. Use it as a reference for the kind of output the `08-scenario-stress-test.md` pass should produce. It is not a pass to run. It is a worked example.

## Score key

- 0 = missed
- 1 = partly covered
- 2 = clearly covered

## Scenarios

### 1. Legacy fintech monorepo with quiet control planes

Repo shape:
- Node API, Ruby billing worker, SQL migrations, Jenkins deploy jobs, GitHub Actions, LaunchDarkly, support scripts used during incidents

What the prior review got right:
- pushed the reviewer toward hidden scripts, notebooks, support tools, approval gates
- handled auth, billing, deletion, and protected areas well

What still felt soft:
- CI or CD automation and release jobs were present, but not named hard enough as control-plane paths across the whole review
- remote config and feature-flag vendors could still sit in the shadows as "configuration" instead of live behavior

Scores:
- repo-fit detection: 2
- hidden-entrypoint capture: 1
- control-plane capture: 1
- approval safety: 2
- evidence discipline: 2
- coverage honesty: 1

Fix:
- Promote CI or CD jobs, release tooling, migration runners, remote config, and feature-flag vendors to first-class control-plane paths across all passes.

### 2. Unity game repo with backend, live ops, and platform entitlements

Repo shape:
- Unity client, editor tooling, asset import hooks, Go backend, Steam or console entitlement checks, live-ops flags, analytics, crash reporting

What the prior review got right:
- treated game repos as a first-class branch
- called out editor tools, live economy, entitlements, anti-cheat, analytics

What still felt soft:
- platform-console steps and release tooling outside the repo could still change shipped behavior without getting mapped as boundaries
- engine-owned serialized assets were protected from inline comment churn, but cross-repo and vendor-console boundaries needed stronger language

Scores:
- repo-fit detection: 2
- hidden-entrypoint capture: 2
- control-plane capture: 1
- approval safety: 2
- evidence discipline: 2
- coverage honesty: 1

Fix:
- Add release tooling, platform-console actions, and out-of-repo behavior surfaces to the architecture, adversarial, and scenario passes.

### 3. Mobile health app with native code, Terraform, and app-store release hooks

Repo shape:
- React Native app, Swift and Kotlin bridges, Firebase, background sync, crash SDKs, Terraform modules, app-store release pipeline, remote config

What the prior review got right:
- mobile and infra branches, protected-area language, good telemetry coverage

What still felt soft:
- app-store and platform release paths not named strongly enough across steering and mapping
- a mixed mobile plus infra repo could still let one clean app path stand in for the control plane

Scores:
- repo-fit detection: 2
- hidden-entrypoint capture: 1
- control-plane capture: 1
- approval safety: 2
- evidence discipline: 2
- coverage honesty: 1

Fix:
- Add app-store or platform release files, release tooling, and cross-repo or external control-plane boundaries to steering, mapping, coverage, adversarial, and scenario passes.

### 4. AI support platform with notebooks, Airflow, evals, and prompt tracing

Repo shape:
- Python services, Airflow DAGs, Jupyter notebooks, vector store, prompt templates, eval sets, LLM traces, support scripts with prod data access

What the prior review got right:
- treated AI and data repos as first-class branch
- flagged prompt or response logging, tool traces, notebooks, model routing, training data lineage

What still felt soft:
- remote prompt stores, dashboard-managed safety settings, and control planes outside the repo could still hide in the phrase "external dependency" without enough pressure
- the scenario pass needed a scorecard so the exercise produced a sharper verdict

Scores:
- repo-fit detection: 2
- hidden-entrypoint capture: 2
- control-plane capture: 1
- approval safety: 2
- evidence discipline: 2
- coverage honesty: 1

Fix:
- Add out-of-repo control surfaces, remote stores, vendor dashboards, and a scenario scorecard.

### 5. SaaS repo with git submodule and sibling deploy repo

Repo shape:
- Main app repo plus a git submodule for shared SDK logic and a separate deploy repo that owns Helm charts and Argo workflows

What the prior review got right:
- warned against flattening specialty stacks into generic web-app language

What it missed most:
- did not name submodules, workspace links, mirrored trees, sibling repos, and separate deploy repos strongly enough
- a reviewer could still overclaim coverage after mapping only the current repo

Scores:
- repo-fit detection: 1
- hidden-entrypoint capture: 1
- control-plane capture: 0
- approval safety: 1
- evidence discipline: 1
- coverage honesty: 0

Fix:
- Add explicit cross-repo and external-control-plane handling.

## Main themes the stress test surfaced

1. Control-plane paths should be promoted from side notes to first-class repo surfaces.
2. Remote config, feature-flag vendors, CMS-backed behavior, app-store or platform consoles, and vendor dashboards must be named as boundaries or unknowns when they shape live behavior.
3. Submodules, workspace links, sibling repos, mirrored trees, and generated SDKs cannot be flattened into a false local coverage claim.
4. The scenario pass benefits from a scorecard, not a loose narrative.

## Honest limits

A review pack can force better behavior, but it cannot guarantee discipline from a careless operator.

A repo can still hide truth in places the repo does not own (vendor consoles, secret stores, incident-only docs, manual release steps). The pass should push to name those boundaries, lower confidence, and stop overclaiming.

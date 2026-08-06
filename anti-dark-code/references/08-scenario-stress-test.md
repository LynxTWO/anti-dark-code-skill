# Reference: Scenario Stress-Test

Use this reference when testing the current repo understanding against synthetic repo shapes and edge cases before later passes harden the wrong story.

**Mode:** read-only review of current repo docs and instructions.

For confidence levels and the unknowns entry shape, see `00-conventions.md`. For an output example, see `example-stress-test-report.md`.

## Goal

Run synthetic stress tests against the current steering docs, system map, coverage ledger, slice plan, and recent summaries.

Find places where the current rules or docs would overclaim, miss a hidden entrypoint, flatten a specialty stack into generic web-app language, let language become hidden truth, or let a protected-area edit slip through without approval.

## Inputs to review

At minimum:
- the steering files
- the system map
- the coverage ledger
- the slice plan
- the latest unknowns files
- the latest adversarial review, if it exists
- any recent PR notes or task summaries that claim confidence or coverage

## How to run the stress test

Challenge current understanding with fake scenarios that resemble real failure cases.

Use only scenarios that could plausibly fit the repo shape. Do not invent fantasy systems with no tie to the repo.

Good scenario families:
- a package script that hits production but never appeared in the map
- a notebook used for data repair during incidents
- a game editor tool that changes shipped behavior
- a mobile background task that syncs data outside the main app flow
- an infra bootstrap step that writes live state before normal deploys run
- a CI or CD job that deploys, seeds, migrates, or repairs state outside the main runtime map
- a release checklist or platform-console action that changes shipped behavior without a code diff in this repo
- an AI support script that logs prompts or tool traces with user content
- a locale overlay or translation file that changes canonical ids, policy meaning, or mechanics
- a saved rendered summary used in replay or hashes before locale support is mapped
- a support-only admin tool with higher privileges than the main app path
- a mirrored third-party directory that should have been excluded from comment churn
- a clean public API path hiding a second path through a cron job, queue, or import script

## Deliverables

Create or update:
- `docs/review/scenario-stress-test.md`
- `docs/review/scenario-scorecard.md`
- `docs/unknowns/scenario-stress-test.md`

Update the coverage ledger when this pass reveals a real blind spot.

## What to record in `docs/review/scenario-stress-test.md`

For each scenario:
- scenario name
- why the scenario is plausible in this repo
- which current doc, rule, or summary would fail under this scenario
- what blind spot the scenario exposes
- what doc or rule change would close the gap
- whether the gap affects approval gates, coverage claims, or protected-area handling

Short scenarios. Concrete findings. Include a simple score for each scenario.

## What to record in `docs/review/scenario-scorecard.md`

Score each scenario on a small scale such as 0 to 2 or 0 to 3.

Useful score rows:
- repo-fit detection
- hidden-entrypoint capture
- control-plane capture
- approval safety
- language-boundary safety
- evidence discipline
- coverage honesty

For each low score, name the exact rule or prompt change that would raise it.

## What to record in `docs/unknowns/scenario-stress-test.md`

Use the unknowns entry shape from `00-conventions.md`.

## Stress-test checks

Use the checks that fit:
- hidden live entrypoint check
- control-plane and release-path check
- protected-area approval check
- specialty-stack language check
- transcreation or locale-boundary check
- false-completion check
- cross-repo boundary check
- generated or serialized artifact check
- tool-specific steering-file drift check
- support-tool or incident-path check
- telemetry blind-spot check
- mixed-stack flattening check

## Deterministic scenario families

Add the scenario families that fit the repo:

- **Replay:** same source identity, starting state, seed, clock, and action sequence should reproduce the failure.
- **Chunking:** equivalent total work split into different valid chunks should preserve the contract when chunking is meant to be irrelevant.
- **Ordering:** independent inputs or events may be permuted without changing the semantic result.
- **Round trip:** save-load, encode-decode, migrate-read, or export-import preserves the required state.
- **Fault:** timeout, partial write, duplicate event, missing event, storage exhaustion, worker death, or suspended process fails safely.
- **Aggregate canary:** a fixed-input sweep keeps action, economy, difficulty, latency, or population distributions within reviewed bands.
- **Rule authority:** presentation, adapter, or compatibility output agrees with the canonical rule.
- **Diagnostics honesty:** instrumentation records the event but cannot alter authoritative results.

Capture seeds, versions, and minimized action traces. A scenario that cannot replay remains evidence of a concern, not a verified root cause.

## Rules

- No application code changes.
- Do not turn a fake scenario into a claimed repo fact without evidence.
- Do not use the stress test to add fantasy complexity.
- Do use the stress test to challenge broad claims that lack ledger support.
- Do not pass a scenario that depends on sibling repos, submodules, CI, release tooling, or vendor dashboards without naming that boundary.

## Reference example

See `example-stress-test-report.md` for a worked example of the kind of gaps this pass should catch.

## Acceptance checklist

The result should:
- expose weak spots in the current repo story before later passes build on them
- challenge coverage claims that sound too broad
- catch missing approval gates, hidden live entrypoints, or hidden control-plane paths
- catch language or copy surfaces that quietly became runtime truth
- improve the docs or rules without inventing systems that are not there

# Reference: Steering Files for Anti-Dark Code

Use this reference when updating or creating coding-agent steering files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `COPILOT_INSTRUCTIONS.md`, or similar.

**Mode:** docs-only. No application code changes.

For confidence levels, risk levels, status vocabulary, the unknowns entry shape, the canonical sensitive-data class list, and the approval-gated areas list, see `00-conventions.md`.

## Goal

Create or update the repo steering files already present. Those files may live at the repo root or in tool-specific locations the repo already uses.

If no steering file exists, create `AGENTS.md` at the repo root unless the user asked for another target.

Create extra steering files only when the repo already uses them or the user asks for them.

The steering files should tell every later automated contributor how to work in this repo without creating or spreading dark code.

## Hard rules before writing

- Inspect the repo first.
- Keep existing product principles, product promises, standing safety language, and repo invariants intact unless the user explicitly says to change them.
- Keep existing steering files aligned on shared policy.
- Preserve real tool-specific differences when they are intentional and repo-backed.
- Keep the repo's mature style when it fits the rules in this task.
- Point later passes to a coverage ledger when the repo is large, old, mixed, or messy.
- Do not add claims about systems, risks, runtime units, entrypoints, control planes, or external dependencies that you did not verify from the repo.
- When behavior depends on out-of-repo control surfaces (remote config, feature-flag vendors, app-store or platform consoles, CI or CD systems, sibling repos), name the boundary and downgrade confidence instead of flattening it away.
- When language or locale work is in scope, name which strings are display, which fields are truth, and which saved-text surfaces are protected.

## Repo checks to run first

At minimum inspect:
- root docs and existing steering files
- tool-specific instruction files already used by the repo
- primary languages and frameworks
- runtime units (services, apps, workers, jobs, packages, functions, tools, pipelines)
- package scripts, task runners, Make targets, notebooks, admin tools, support scripts, bootstrap scripts, one-shot ops scripts, CI or CD workflows, release tooling, migration runners, deploy helpers that may hit live systems
- repo type (service, monorepo, frontend-only app, game repo, mobile app, infra repo, AI or data system, library, or mixed stack)
- sensitive domains (auth, billing, deletion, messaging, moderation, recommendations, health data, financial data, child data, psychometric data, or other regulated data)
- existing docs, ADRs, runbooks, ownership signals (`CODEOWNERS`), submodules, workspace links, mirrored trees, or sibling repos that carry live behavior
- test setup, CI checks, deployment files, release steps, app-store or platform release files, remote-config hooks, feature-flag integration points, environment files
- copy, content, locale, translation, transcreation, text-lint, or generated-prose docs when the repo has player-facing text
- whether the repo is a new scaffold or an existing system

For an existing repo: reflect real architecture, real risks, real rough edges. Name legacy or unclear areas plainly.

For a new repo: write a forward-looking version. Mark open areas as `TBD`. Do not invent implementation details.

## Required sections

### 1. Purpose and scope

State that the steering files define how AI-assisted work happens in this repo. State the goal in plain words:
- keep code explainable
- keep reviews grounded in evidence
- keep risky work behind approval gates
- keep future changes safer because the repo tells the truth about itself

### 2. Product principles and standing promises

Preserve any existing product principles, product promises, or standing safety language. Keep them intact and update only when the user asks.

If the repo does not use them and the user wants them, add a short repo-fit set. A safe starting frame often covers:
- making truth easier
- making repair normal
- making dignity default
- making ownership unavoidable
- making manipulation unnecessary

Adapt the wording to the project. Do not paste lines that do not fit the repo.

### 3. What dark code means in this repo

Define dark code in plain language. Cover at least:
- unclear purpose
- hidden side effects
- missing ownership
- missing failure-mode notes
- unclear data sensitivity
- critical paths that cannot be explained from the repo alone
- live entrypoints that sit outside the main app path
- text or translated copy that hides mechanics, policy, permissions, saved truth, or runtime decisions
- legacy areas that keep working but have weak explanations

### 4. Repo profile

Add a short repo profile naming:
- repo type
- main languages and frameworks
- runtime model
- highest-risk systems
- sensitive data classes
- main docs and ownership locations

Keep this short. Use repo facts only.

### 5. Working modes

Describe the allowed passes. At minimum include:

**Pass 0: Read-only inventory** - inspection and analysis only, no file changes.

**Pass 1: Docs and comments only** - comments, manifests, maps, runbooks, ADRs, other docs. No logic, control-flow, import, dependency, config, schema, or formatting changes outside touched lines.

Treat behavior-sensitive comments as code. Do not alter shebangs, encoding markers, pragma comments, linter directives, type-affecting docblocks, SQL hints, magic comments, engine metadata comments, or serialized asset comments.

**Pass 2: Behavior-preserving cleanup** - allowed only after baseline docs and comments exist for the touched area. Requires tests or other evidence. No feature work in the same PR or commit.

**Pass 3: Feature or security work** - only when the user asked for it, and only after the needed map, unknowns, and approval gates are in place. Docs, tests, risk notes, and rollback notes stay attached.

### 6. Coverage and slice rules

For large or mixed repos:
- require a coverage ledger
- require risk-ranked slices
- allow nested ledgers when one repo-wide table would hide detail
- make the long-term target clear: cover all applicable critical paths over time
- record exclusions, blind spots, blocked areas, and approval-gated areas
- avoid claims of full coverage unless the ledger supports the claim

### 7. Rules for new code

Require every non-trivial change to include:
- a plain statement of what changed and why
- tests tied to intended behavior
- a security and privacy note when relevant
- an observability note when relevant
- a rollback or failure-handling note when relevant
- doc updates when a subsystem changes
- service or module manifest updates when the repo uses them
- control-plane or release-path notes when deploy, migrate, seed, backfill, or support tooling changed
- language-boundary notes when copy, content, locale, or transcreation work could affect runtime truth

Keep PRs and commits small and single-purpose when possible.

### 7a. Deterministic verification and token discipline

Require:

- the local computer to perform exact enumeration, formatting, type, lint, schema, architecture, test, replay, diff, and gate work where safe
- exact gate command arrays in calibration or a repo-native equivalent
- compact green summaries and bounded failure packets
- change-impact selection before expensive full-suite work
- no automatic dependency installation from a verification suggestion
- no repo-code execution on inherited or unknown repos without the required permission
- one canonical rule implementation when views or adapters need the same behavior
- observational diagnostics that do not influence authoritative state unless explicitly designed and approved

Point contributors to pass `14` and `calibration/verification-plan.json`.

### 8. Unknowns and evidence

Hard rule: do not guess.

Unknowns go under `docs/unknowns/` or the repo's existing unknowns location. Use the canonical entry shape from `00-conventions.md`.

### 9. Sensitive areas that need explicit human approval

Use the approval-gated list from `00-conventions.md` as the baseline. Add repo-specific high-risk areas (live economy logic, anti-cheat, entitlement checks, training data lineage, model routing, infra state backends, platform purchase flows, secure local storage, privileged CI or CD automation, release tooling, support tooling with production reach) when verified from the repo.

If an active leak or gap is found inside a protected area, document it first and stop for approval before editing.

### 10. Data that must never appear in logs, comments, tests, docs, examples, screenshots, or commit text

Use the sensitive-data class list from `00-conventions.md` as the baseline.

If the repo handles high-risk domain data, name it: health, finance, legal, location, biometrics, psychometric results, student data, child data, training data, assessment answers tied to a person.

### 11. Comment, doc, commit, and PR writing rules

Require:
- short sentences
- plain words
- direct naming of the subject, risk, and safeguard
- active voice when it reads cleaner
- ASCII punctuation and straight quotes only

Reject:
- stiff corporate tone
- legal boilerplate tone outside legal text
- stock transition adverbs
- stock wrap-up lines
- mirror-contrast slogans built around a negated first clause
- default triplet cadence when a list of two or four fits better
- vague openings that hide the subject
- apology filler
- hype

If the repo or user supplied a banned-term list, treat it as a hard lint rule.

### 11a. Builder, challenger, verifier, and test-change rules

For medium or high-risk changes:

- separate implementation from adversarial challenge
- let deterministic gates issue the final mechanical verdict
- do not let the verifier edit the code it is grading
- scale extra agent votes by finding class and reproducibility

Flag test changes that skip cases, delete assertions, increase timeouts, broaden mocks, lower coverage or mutation strength, or update snapshots. The change may be valid, but the behavior contract that changed must be named.

### 12. Documentation minimums

Require at least one of these when a subsystem changes:
- service or module manifest
- architecture note
- runbook update
- ADR update
- README section
- contract or schema note
- ops note for deploy, rollback, or support when relevant

Keep the rule useful. Do not build a doc graveyard.

### 13. PR close-out format

Every PR should end with a short note covering:
- what changed in plain English
- unknowns found
- security or privacy impact
- observability impact
- docs touched
- approval gates crossed or still pending
- follow-up work, if any

### 14. Repo-specific appendix

Name:
- critical systems
- sensitive data classes
- highest-risk directories, packages, or runtime units
- likely non-obvious live entrypoints (scripts, admin tools, task runners, CI jobs, release tooling, migration runners) when verified
- preferred locations for unknowns, architecture docs, runbooks, and ADRs
- the steering files kept in sync in this repo

## Output constraints

- Markdown only
- practical and scannable
- plain wording
- no code changes outside the steering files
- keep the core doc tight; push long inventories into companion docs when needed

## Acceptance checklist

The final steering files should:
- define dark code plainly
- preserve existing product principles, product promises, and standing safety language unless the user asked for a change
- separate read-only, doc-only, cleanup, and feature work
- tell future agents how to handle unknowns
- set a coverage rule for large repos
- name sensitive systems and data classes
- set text rules that keep comments and commits sounding human
- require approval for protected areas
- preserve real tool-specific differences while keeping shared policy aligned
- fit the actual repo instead of a generic fantasy version

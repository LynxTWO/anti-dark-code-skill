# Reference: Large Repo Coverage and Slicing Plan

Use this reference when the repo is too large, too mixed, too old, or too messy for one anti-dark-code pass to be honest.

**Mode:** application code stays read-only. Docs may be created or updated.

For confidence levels, status vocabulary, classification labels, the unknowns entry shape, and default deliverable paths, see `00-conventions.md`.

## Goal

Build a coverage plan that lets later passes reach all applicable critical paths without guessing, hand-waving, or pretending that the whole repo was reviewed.

Run the adversarial edge-case review (`07-adversarial-review.md`) after the first slice plan when the repo has hidden runtime paths, protected areas, or specialty stacks.

## When to use this reference

Use it when one or more fit:
- many apps, packages, services, modules, or runtimes
- mixed languages or frameworks
- long-lived legacy code with thin docs
- large asset trees, generated outputs, or binary artifacts
- game repos with client, server, tools, content pipelines
- mobile repos with shared code plus native layers
- infra repos with many modules, accounts, or environments
- AI or data repos with jobs, notebooks, evals, registries, batch flows
- any repo where a one-shot pass would hide blind spots

## Deliverables

Create or update:
- `docs/architecture/coverage-ledger.md`
- `docs/architecture/repo-slices.md`
- `docs/unknowns/coverage-pass.md`

Use nested ledgers when one flat table would hide important detail. A giant monorepo may need one top ledger plus per-domain ledgers.

## What to do

### 1. Take a repo-shape snapshot

Capture:
- top-level apps, packages, services, modules, tools, pipelines
- main languages and frameworks
- generated, vendored, mirrored, minified, serialized, or binary areas
- highest-risk domains
- main ownership signals (`CODEOWNERS`, service catalogs, team docs)
- likely non-obvious entrypoints (scripts, admin tools, notebooks, editor tools, import flows, bootstrap steps, CI or CD jobs, release tooling, migration runners, support tools)
- language and rendered-text surfaces when copy, locale, transcreation, templates, prompts, or generated prose can affect behavior or user understanding

### 2. Classify areas

Use the classification labels from `00-conventions.md`. Keep labels short and factual.

### 3. Rank risk

Assign a risk class to each major area using the risk levels from `00-conventions.md`. Common drivers:
- auth or access control
- money or entitlements
- deletion or retention
- secrets or crypto
- state corruption risk
- irreversible side effects
- regulated data
- user-generated content
- external callbacks
- live economy logic
- infra state writes
- model routing or data lineage
- rendered text mixed with ids, hashes, replay, policy, permissions, pricing, ranking, saved history, or mechanics
- secure local storage or native bridge edges
- package scripts or support tools that can touch production
- CI or CD automation with deploy, seed, migrate, backfill, or repair powers
- out-of-repo control surfaces (remote config, feature-flag vendors, app-store consoles, vendor dashboards)

### 4. Define slices

A slice can be:
- one runtime unit
- one subsystem
- one trust boundary
- one critical flow
- one high-risk directory tree
- one docless legacy pocket
- one environment overlay or control-plane path
- one language, locale, or authored-content boundary
- one script, CI job, release path, or notebook family that can hit live systems

Keep slices large enough to matter and small enough to verify.

### 5. Record exclusions

List what should not be handled with inline comment passes or deep code edits:
- generated files
- vendored code
- mirrored third-party code
- minified bundles
- large binary assets
- machine-generated metadata
- large serialized engine assets
- external systems not represented in the repo
- sibling repos or submodules that own part of the live path

Say how those areas should be explained instead: maps, manifests, runbooks, ownership notes.

## What to put in `docs/architecture/repo-slices.md`

One entry per slice. Use the `repo-slices.md` template under `assets/templates/`. For each:
- slice name
- scope or repo paths
- reason for the slice
- risk class
- classification label
- related runtime units or flows
- blockers
- exit criteria for calling the slice covered enough for this stage
- next pass to run on the slice (architecture map, comment pass, telemetry audit, adversarial review)

Exit criteria should name evidence, not mood.

## What to put in `docs/architecture/coverage-ledger.md`

Use the `coverage-ledger.md` template under `assets/templates/`. Table or short bullet structure with:
- area or slice
- paths
- risk class
- status (use the coverage ledger status values from `00-conventions.md`)
- reason it matters
- evidence used
- likely owner if known
- next pass

Large repos need a real ledger. Small repos can keep it short.

## What to put in `docs/unknowns/coverage-pass.md`

Record anything that blocks honest coverage. Use the unknowns entry shape from `00-conventions.md`.

## Calibration and freshness

When a fresh repo-local coverage ledger exists, reuse it. Do not re-audit a guarded surface until an invalidating path or contract changed. Record the exact invalidation rule so freshness is evidence-backed rather than date-based optimism.

Add verification ownership to each risky slice:

- relevant capability ids from V01 through V20
- confidence-ladder level
- exact gate or next check
- replay or corpus location when applicable
- hardware or runner constraint

## Rules

- No application code changes.
- Do not claim full coverage without ledger support.
- Do not cap coverage at a small fixed number of paths.
- Use risk-ranked slices for order.
- Keep the long-term target clear: all applicable critical paths.
- Do not let one clean service or one clean package stand in for a whole mixed stack.
- Do not let one repo stand in for sibling repos, submodules, or vendor control planes that shape live behavior.

## Acceptance checklist

The result should:
- show the whole repo shape at a useful level
- rank the risky areas first
- separate generated or external material from hand-written code
- produce slices later passes can work through
- keep an honest ledger of what is covered, blocked, approval-gated, or still dark

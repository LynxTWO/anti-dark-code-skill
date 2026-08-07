# Changelog

## 2026.08.06-unified.4

### Real-Repo Write and Execution Hardening

- Verifies and fixes repo-local symlink-blind writes. Install, calibration, adapter, run-artifact, and flow-back paths now fail closed on symbolic-link or Windows-junction components and nested link-like entries.
- Keeps user-level host-discovery aliases compatible with a shared universal core while requiring real repo-local managed directories.
- Uses atomic file replacement for managed-core copies, calibration-template copies, and staged flow-back proposals.
- Treats invalid or link-contaminated calibration as repair-or-quarantine work instead of allowing `--accept-unbound-calibration` to override it.
- Makes blocked gate plans return exit code `2` in dry-run mode as well as execution mode.
- Launches each executed gate in a separate process group and makes a best-effort process-tree termination on timeout.
- Records timeout termination details in bounded failure packets.
- Makes auto validation treat the canonical repo-local path as installed state even when that path is an unsafe symlink, so the validation error cannot be hidden by resolving to the shared target.

### Scan Isolation and Validation Modes

- Excludes `.agents/skills`, `.claude/skills`, `.gemini/skills`, and `.codex/skills` from repository profiling, source identity, and changed-slice routing.
- Detects legacy `.codex/skills/anti-dark-code/calibration` alongside the other supported legacy locations.
- Adds explicit `distribution`, `universal`, `installed`, and `auto` validation modes.
- Keeps distribution validation strict against `incoming/`, repo calibration, managed-install metadata, symbolic links or junctions, `__pycache__`, and `.pyc` artifacts.
- Lets a deployed universal core validate and run its unit suite with staged flow-back proposals and without outer distribution documents.
- Validates installed repo copies through `.adc-managed.json`, managed-core hashes, the core digest, source metadata, local calibration JSON, calibration link safety, and repository binding.
- Allows ordinary live-core flow-back proposals while rejecting symlinked or junction-backed `incoming/` inbox entries.
- Excludes `.codex/skills` from Git worktree identity as well as content scans.

### Migration and Regression Coverage

- Updates repository-neutral migration guidance for symlinked legacy layouts, layered validation, blocked dry-run status, installed-copy integrity, and process-tree timeout behavior.
- Preserves strict package-artifact checks without requiring `python3 -B`.
- Adds regression tests for blocked dry runs, installed-copy validation, universal-core `incoming/` isolation, distribution rejection of runtime inboxes, repo-local link refusal, linked flow-back destinations, sibling-skill isolation across profiling and change routing, and timeout process-tree termination.

## 2026.08.06-unified.3

### Cross-Repo Calibration Isolation

- Adds `SOURCE-SCOPE.json` so installers can identify a clean universal source core.
- Adds `calibration/repo-binding.json` with a hashed one-repository identity.
- Blocks unbound legacy calibration until `--accept-unbound-calibration` is explicit.
- Blocks mismatched calibration until a reviewed `--rebind-calibration` is explicit.
- Records prior hashed repository ids when a binding is deliberately changed.
- Refuses deterministic gate execution and flow-back from unbound or foreign calibration.
- Verifies that a flow-back parent is a clean universal core.
- Reports legacy calibration locations without silently merging competing stores.
- Resets migrated or rebound gates to disabled and proposed, and clears global execution confirmation.
- Uses canonicalized Git remotes for stable binding across a first commit and ordinary SSH-to-HTTPS remote changes.

### Installation Source Hardening

- Blocks unmarked, repo-local, and repo-calibrated installation sources by default.
- Adds `--allow-unsafe-source` for advanced reviewed recovery only.
- Never copies top-level source calibration, even when the recovery override is used.
- Excludes the shared `incoming/` proposal inbox from repo-local managed copies.
- Rejects contaminated calibration templates even under the source override.
- Validates that template bindings are unbound and template gates are disabled and unapproved.
- Preserves nested calibration templates in managed repo copies while still excluding top-level repo calibration and proposal inboxes.
- Rejects a shared flow-back parent that carries a repo-local managed-install manifest.

### Migration and Documentation

- Rewrites `MIGRATION.md` for any old, partial, mixed, model-specific, or repo-customized installation.
- Makes same-repo fact migration, gate conversion, host consolidation, rollback, and multi-repo safety explicit.
- Removes project-specific migration guidance from operational references.
- Clarifies that the universal core flows downward, repo calibration stays local, and only reviewed general proposals flow upward.
- Generalizes personal-path validation beyond two hardcoded developer paths.

### Test Harness Fix

- Fixes the unit-suite packaging false positive caused by the suite's own runtime `__pycache__` files.
- The suite now validates a clean temporary package copy and runs with ordinary `python3`.
- Strict package validation still rejects packaged `__pycache__` directories and `.pyc` files.
- Expands deterministic coverage for clean-source enforcement, source-calibration exclusion, binding creation, stable remote identity, unbound migration, migration gate resets, mismatch rejection, explicit rebind, template completeness, template contamination, foreign-gate refusal, managed-parent refusal, and neutral operational guidance.

## 2026.08.06-unified.2

### Deterministic Gate Hardening

- Detects npm, pnpm, Yarn, or Bun for package-script gates.
- Creates generated gate suggestions disabled and marked `proposed`.
- Requires each enabled gate to be marked `approved` before execution.
- Resets global execution confirmation when generated gates are added, changed, or become stale.
- Fingerprints package-script definitions and blocks a previously approved gate when the underlying script changes.
- Includes committed, uncommitted, and untracked files in changed-slice routing.
- Retains pattern-redacted gate logs and redacts command fields in failure packets.
- Adds microsecond run ids and gate-definition hashes to avoid artifact collisions.

### Calibration and Probe Hardening

- Tracks commit and worktree status for profile freshness.
- Migrates pre-install fallback calibration into the canonical repo-local skill.
- Uses calibration templates from the selected source skill during installation.
- Prunes installed skill trees during repo enumeration.
- Reduces false generated-output and security signals from ordinary `export` and tokenizer code.
- Adds stricter package, capability-catalog, path, and generated-artifact validation without creating `__pycache__` files.
- Expands the deterministic unit suite from 8 to 15 tests.

## 2026.08.06-unified.1

### Unified

- Replaced separate Claude and Codex core trees with one model-neutral skill.
- Preserved optional OpenAI metadata under `agents/openai.yaml`.
- Added host addenda for Claude Code, Codex, Gemini CLI, and generic harnesses.
- Added a thin Claude repo adapter that points to the canonical `.agents/skills` copy.

### Added

- Pass `13`: calibrated local mode.
- Pass `14`: deterministic verification planner.
- Pass `15`: dogfeeding and proposal-only flow-back.
- Machine-readable catalog for all 20 verification capabilities.
- Repo-type adaptations for service/web, frontend, monorepo, library/SDK, game/simulation, mobile/native, infrastructure, AI/data, CLI/desktop, small/new, and mixed repos.
- Repo-owned calibration templates.
- Managed-core installer with checksums and conflict detection.
- Bounded deterministic repo probe.
- 20-capability planner and confidence ladder.
- Exact gate schema, dry-run runner, owner-confirmation gate, real exit-code capture, local logs, and bounded failure packets.
- Content-hashed flow-back proposals and parent inbox staging.
- Skill validator and unit tests.

### Incorporated from Repo-Local Dogfeeding

- calibration-first operation
- fresh-surface re-audit avoidance
- finding-class verification effort
- exact gate reuse and machine constraints
- canonical-rule delegation across projections and adapters
- aggregate canaries for emergent behavior
- output-count probes and configuration unwiring
- aggregation-semantics review
- chunking metamorphic tests
- dependency graph enforcement
- observational diagnostics and replayable UI monkey failures

### Changed

- Updated preflight, steering, architecture, slicing, adversarial review, scenario stress, maintenance, remediation, and orchestration references to use deterministic planning and calibration.
- Updated templates with capability ids, confidence levels, exact gates, failure packets, replay memory, rule authority, and freshness triggers.

### Safety

- No automatic dependency installation.
- No repo-code execution during install, bootstrap, or probe.
- Gate execution requires both `--allow-exec` and recorded owner confirmation.
- Repo-local flow-back cannot directly mutate shared core files.

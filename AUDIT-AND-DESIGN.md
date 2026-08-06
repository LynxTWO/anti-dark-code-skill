# Audit and Design Decision

## Historical Provenance Note

The source archive names in this audit identify the material reviewed during package design. They are provenance only. They are not installation inputs, transferable calibration, default repository assumptions, or operational migration instructions. Repo-specific content from one archive must remain inside that repository unless a separate lesson is generalized, reviewed, and promoted into the universal core.

## Direct Answer to the Three Questions

### 1. Should the 20 techniques be implemented across the general skill?

Yes, with one correction: they are not all tests, and they should not all become mandatory tools in every repo.

The right design is to evaluate all 20 capabilities for every repo, then assign one of four statuses:

- selected
- candidate
- deferred
- not applicable

That distinction matters. Mutation testing is valuable only after meaningful tests exist. Differential testing needs two implementations or a reference oracle. Fault injection needs a real external, persistence, process, or background boundary. A small new library should not inherit the same laboratory as a simulation engine, mobile app, or payment service.

The revised skill now treats the 20 items as a machine-readable capability catalog. The deterministic repo probe gathers evidence. The planner selects the repo-fit subset, adapts it by repo type, assigns a confidence-ladder level, identifies local deterministic work, and separates the judgment that remains for an agent.

This closes the token problem in the right place. The computer handles enumeration, exact gates, replay, diffs, checksums, change impact, exit codes, log storage, and failure packaging. Agents handle risk, invariant design, adversarial properties, contradictions, and safe fixes.

### 2. Should lessons from the repo-local dogfeeding run flow into the shared skill?

Yes. The repo-local variant proved the value of a persistent calibration layer. Its strongest reusable idea was not game-specific testing. It was making a known repo stop pretending to be unfamiliar every time a context window resets.

The revised design imports the following broad lessons:

1. Fresh calibration beats cold re-derivation.
2. Exact gate commands with real exit codes beat subjective claims that the code looks right.
3. Verification effort should follow the finding class and its reproducibility.
4. A view or adapter that re-implements an authoritative rule is a drift risk.
5. Targeted green does not prove aggregate behavior in emergent systems.
6. Fixed-input output-count probes can isolate emergent regressions cheaply.
7. Configuration unwiring can bisect content or policy regressions faster than broad code reading.
8. Aggregation semantics can let one declaration silently reclassify a whole system.
9. Chunking and batching deserve metamorphic tests when they should not change results.
10. Dependency graphs settle cycle and layer claims more cheaply than additional model opinions.
11. UI monkeys, fuzzing, and black-box logging become far more useful when every failure is seed-replayable.
12. Instrumentation should observe authoritative behavior, not quietly influence it.

The shared core now installs into a repo while preserving a repo-owned `calibration/` overlay. Local agents update calibration, not the managed core. A hashed repository binding prevents that overlay from being silently reused in a different repo.

Flow-back has a trust barrier. A repo-local skill can stage a proposal, but it cannot directly write to the developer's global skill. That prevents a compromised or simply overfitted repo from poisoning every future project. A human reviews, generalizes, deduplicates, validates, and promotes the lesson.

### 3. Should the Claude and Codex skills be combined?

Yes.

The two uploaded general variants were already almost the same. Their meaningful differences were:

- one model name in the description
- a short Claude-specific tooling section
- optional OpenAI metadata in the Codex copy

Maintaining two full trees creates drift without buying real specialization.

The revised package uses one standard `SKILL.md`, one reference tree, one script tree, and one asset tree. Host mechanics live in small addenda:

- `host-claude-code.md`
- `host-codex.md`
- `host-gemini-cli.md`
- `host-generic.md`

OpenAI metadata remains in `agents/openai.yaml`. Claude Code gets a thin repo adapter that points to the canonical `.agents/skills/anti-dark-code/` copy. Gemini CLI and Codex use that canonical copy directly. Shared policy is not duplicated.

## Archive Audit

### Anti-Dark-Code-Skill_8-6-2026.zip

The archive contained two nearly identical trees:

```text
CLAUDE SKILL/anti-dark-code/
CODEX Skill/anti-dark-code/
```

Both contained the same passes `00` through `12`, templates, orchestration reference, and remediation workflow.

The Claude copy added host-specific tool notes. The Codex copy added `agents/openai.yaml`. That is adapter material, not a reason for two independent cores.

The original skill was already strong in several areas:

- evidence labels and unknowns
- approval gates
- trust-boundary mapping
- repo-type branches
- bounded passes
- large-repo slicing
- adversarial review
- scenario review
- protected comment continuity
- deterministic shell work inside orchestration
- real exit-code warnings
- token-aware agent tiering and resumable fan-out

Its main gap was that deterministic verification lived mostly as guidance. It did not yet have a capability planner, repo-local calibration installer, exact generic gate schema, compact failure packet runner, or safe flow-back process.

### chronicle-anti-dark-code.zip

The Chronicle archive added:

- `DOGFEEDING.md`
- `LEARNINGS.md`
- repo invariants
- accumulated system map
- exact gates and hardware notes
- coverage freshness and verifier calibration
- an accumulated findings ledger

This version showed that a local skill can act as durable repo memory. It also exposed a design flaw in the old flow-back wording: the parent path was hardcoded, and the repo-local skill was invited to write lessons directly back into two parent variants.

The revised design removes the hardcoded path, removes the two-parent problem, and changes flow-back from direct mutation to proposal staging.

## Unified Architecture

### Shared Core

```text
anti-dark-code/
  SKILL.md
  VERSION
  SOURCE-SCOPE.json
  references/
  assets/
  scripts/
  agents/
  tests/
```

The shared core remains broad enough for service, frontend, monorepo, library, game, mobile, infrastructure, AI/data, CLI/desktop, small, new, and mixed repos.

### Canonical Repo Copy

```text
.agents/skills/anti-dark-code/
```

The installer manages core files and records their checksums in `.adc-managed.json`.

### Repo-Owned Overlay

```text
.agents/skills/anti-dark-code/calibration/
```

Calibration survives upgrades and contains repo facts, exact gates, verification status, coverage freshness, settled findings, and upstream candidates.

`repo-binding.json` binds that calibration to one hashed repository identity. The binding does not store the raw remote or personal path. It blocks accidental cross-repo transfer while still permitting explicit review for a legitimate move, fork, or remote change.

### Host Adapters

A host adapter changes discovery or tool syntax only. It cannot change evidence, safety, verification, or flow-back policy.

### Local Run Artifacts

```text
.anti-dark-code/runs/
```

Full command output stays local and ignored by default. The agent receives a compact summary or bounded failure packet.

## The 20-Capability Implementation

The catalog is stored in:

```text
anti-dark-code/assets/verification-capabilities.json
```

Each capability records:

- purpose
- default confidence level
- machine cost
- deterministic work
- remaining agent judgment
- selection signals
- repo-type adaptations
- dependency policy

The planner outputs all 20 rows to:

```text
calibration/verification-plan.json
```

The selected core for a non-trivial maintained repo will often include:

- executable invariants
- schema and contract validation
- static architecture enforcement
- deterministic quality gates
- change-impact analysis
- authoritative project map
- separated roles scaled to risk
- test-change policing
- minimal failure packets
- confidence ladder

Conditional capabilities then add mutation, stateful models, differential checks, metamorphic properties, deterministic execution, replay corpora, hermetic isolation, goldens, performance budgets, and fault injection where evidence supports them.

## Deterministic Tooling Added

`adc.py` provides seven commands.

### `probe`

Builds a bounded repo profile without executing repo code. It detects languages, manifests, CI, tests, exact package scripts, repo types, and risk indicators while recording scan limits.

### `plan`

Evaluates all 20 capabilities, adapts them to the repo, and generates proposed gate entries. It does not install dependencies.

### `install`

Verifies a clean universal source, copies or updates managed core files, preserves and binds local calibration, detects local core conflicts, writes checksums, and creates a thin Claude adapter when requested. Repo-local or repo-calibrated sources are blocked by default, and source calibration is never copied.

### `bootstrap`

Runs install, probe, and plan in one explicit workflow. It still does not execute repo code.

### `gates`

Dry-runs by default. After both command review and recorded owner confirmation, it executes exact argument arrays without shell interpolation, captures real exit codes, stores pattern-redacted logs, prints compact results, and creates a bounded failure packet.

### `flowback`

Converts `ready` local lessons into a content-hashed proposal. It can stage that proposal in a parent `incoming/` directory but cannot edit shared core files.

### `validate`

Checks frontmatter, references, JSON, capability count, source scope, calibration-template safety, likely personal paths, host neutrality, Python compilation, generated artifacts, and the no-em/no-en-dash style rule.

## Confidence Ladder

The revised skill uses four levels.

Level 0 covers cheap changed-slice static and contract checks.

Level 1 covers affected unit, integration, and replay checks.

Level 2 covers selected property, fuzz, monkey, mutation, performance, and fault checks.

Level 3 covers full suites, long campaigns, soak, migration matrices, platform matrices, broad mutation, and aggregate canaries.

This prevents the two common failures: running almost nothing during development, or running everything after every tiny edit.

## Important Limits

The deterministic probe is intentionally bounded. A missing signal is not proof that a feature or risk does not exist.

The generic runner cannot know whether a repo command is safe merely because it appears in a manifest. Execution still requires review and recorded owner confirmation.

The skill does not automatically install Stryker, dependency-cruiser, Hypothesis, Playwright, a fuzz engine, or any other dependency. It first checks existing tooling and proposes additions for human review.

A generic change-impact graph cannot see every semantic dependency. Shared config, content packs, schemas, generated files, deployment paths, remote control planes, and sibling repos still need human mapping.

Host discovery conventions can evolve. Host addenda are isolated so they can be updated without forking the core.

## Validation Performed

The package validator passed.

The included unit suite passed 32 tests with ordinary `python3`, covering:

- clean package validation without requiring `python3 -B`
- strict rejection of packaged `__pycache__` and `.pyc` artifacts
- frontmatter, capability catalog, source marker, template completeness, path, and host-neutrality checks
- deterministic repo probing and all 20 capability decisions
- package-manager-aware JavaScript gates and unique nested gate ids
- reduced false positives for ordinary TypeScript exports
- managed installation, Claude adapter creation, and calibration preservation
- fresh repository binding creation, local Git stability across the first commit, and canonical remote stability across SSH and HTTPS forms
- explicit acceptance of trusted unbound legacy calibration with migrated gate approvals reset
- mismatch rejection and explicit reviewed rebinding
- repo-local and managed-install sources blocked by default
- source calibration and shared incoming proposals excluded from managed repo copies while nested calibration templates remain installed
- contaminated calibration templates blocked even under the unsafe-source recovery flag
- migration of pre-install fallback calibration into the canonical repo skill
- proposed gates starting disabled and requiring individual approval
- package-script fingerprint invalidation after command changes
- dry-run and executable gate behavior with redacted retained logs and bounded failure packets
- refusal to execute gates without individual approval and global owner confirmation
- refusal to execute gates or flow back lessons from foreign calibration
- refusal to stage flow-back into a repo-calibrated or repo-managed parent
- changed-slice routing that includes committed, uncommitted, and untracked files
- profile freshness tracking across dirty worktree changes while ignoring skill-generated artifacts
- proposal-only flow-back with path and secret-like-value redaction
- general personal-path validation and neutral operational migration guidance
- repo probes ignoring installed skill files while retaining CI discovery

A private migration simulation placed the uploaded repo-specific legacy skill under a synthetic repository's old Claude skill location. The new bootstrap detected that calibration as an unbound legacy store, did not auto-import it, created fresh bound calibration, retained the nested generic calibration templates, and introduced no legacy project name or project-named file into the new calibration.

No uploaded source archive was modified. This is a new package.

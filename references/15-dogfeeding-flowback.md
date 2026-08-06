# Reference: Dogfeeding and Flow-Back

Use this pass when a repo-local anti-dark-code skill has learned something that may improve the shared skill.

**Mode:** calibration and proposal files only. Shared-core changes require a separate human-reviewed promotion.

## Goal

Let known repos become proving grounds without letting repo-specific assumptions or compromised instructions poison the shared skill.

The loop is:

1. Shared core installs into a repo.
2. Repo calibration adapts to local truth.
3. Bounded work produces evidence.
4. Local facts update local calibration.
5. General lessons enter an upstream queue.
6. A deterministic tool stages a proposal.
7. A human reviews, generalizes, tests, and promotes it into the shared core.
8. The updated core is reinstalled into participating repos.

## Read Calibration First

Before a pass, read only the calibration files relevant to the slice.

- invariants prevent accidental boundary violations
- system map prevents cold recrawls
- exact gates prevent command rediscovery
- coverage ledger prevents fresh surfaces from being re-audited
- findings ledger prevents settled work from being re-triaged
- verification plan prevents uniform, wasteful testing

A stale calibration entry is worse than no entry. Check freshness against changed paths and the current source identity.

## Write Local Learning Back

After a pass, update the appropriate local record:

- new load-bearing truth -> `invariants.md`
- new or moved boundary -> `system-map.md`
- audited or invalidated surface -> `coverage-ledger.md`
- opened, fixed, refuted, or deferred issue -> `findings-ledger.md`
- new gate or machine constraint -> `gates.json`
- changed verification need -> `verification-plan.json`

Use evidence labels and cite the source path, command, test, or artifact.

## Upstream Candidate Test

A lesson belongs in `upstream-candidates.md` only when all are true:

- it is useful beyond this repo
- it can be stated without repo names, private paths, or project secrets
- it survived at least one concrete failure, refutation, or measurable comparison
- the evidence and limits are named
- the proposal says which shared reference, template, capability, or script should change

A repo fact is not a general lesson. A preference is not evidence. One surprising incident may be a candidate, but not automatically a core rule.

## Candidate Shape

Use this form:

```markdown
## ADC-LOCAL-001: <short title>

- Status: ready
- Scope: repo-agnostic
- Lesson: <general rule>
- Evidence: <local paths, tests, commands, or findings>
- Limits: <where the rule may not apply>
- Proposed target: <shared file or capability>
- Proposed change: <smallest useful change>
```

Valid statuses are `observing`, `ready`, `staged`, `promoted`, and `rejected`.

## Stage a Proposal

```bash
python .agents/skills/anti-dark-code/scripts/adc.py flowback --repo .
```

The command reads only `ready` entries and creates a content-hashed proposal under `.anti-dark-code/flowback/`. It does not edit the shared skill.

A maintainer may stage the proposal into a shared skill's inbox with an explicit path and flag:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py flowback \
  --repo . \
  --parent /path/to/shared/anti-dark-code \
  --stage-to-parent
```

Staging writes an incoming proposal. It still does not modify core references or scripts.

## Promotion Gate

Before promotion into the shared skill:

1. Remove repo-specific nouns and assumptions.
2. Check whether the rule already exists.
3. Identify repo types where it applies and where it does not.
4. Add or update deterministic tests for any script change.
5. Validate cross-host packaging.
6. Run `adc.py validate` and the skill's unit tests.
7. Record the source candidate and the human decision.
8. Promote in one bounded shared-core change.

A local repo never grants itself permission to rewrite global instructions.

## General Lessons Proven by the Chronicle Dogfeeding Run

The Chronicle variant supplied several broad patterns now incorporated in this unified skill:

- pre-seeded calibration makes a known repo cheaper and safer than cold re-derivation
- verifier count should follow finding class and reproducibility
- exact gates with real exit codes beat subjective review
- duplicated rules across engine, view, adapter, or migration boundaries are drift risks
- targeted green is not world green in emergent systems, so keep an aggregate canary
- deterministic output-count probes plus configuration unwiring can isolate emergent regressions faster than broad code reading
- aggregation semantics in manifests can let one declaration reclassify an entire system
- chunking or batching can be tested metamorphically when total work should remain equivalent
- dependency graphs can settle layering and cycle claims more cheaply than model debate
- UI exploration, fuzzing, and replay become much stronger when the instrumentation is observational and failures are seed-replayable

These are generalized rules. Chronicle-specific invariants and paths remain local.

## Acceptance Checklist

Flow-back is complete when:

- local calibration reflects the pass
- each upstream candidate is genuinely repo-agnostic
- private and repo-specific details stay local
- ready candidates are staged as proposals only
- the shared core was not silently edited
- promotion has a human decision and deterministic validation

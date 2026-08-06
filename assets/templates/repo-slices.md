# Repo Slices

Breakdown of the repo into slices that later passes can work through. Each slice should be large enough to matter and small enough to verify in one pass.

For canonical risk levels, classification labels, and slice status values, see `references/00-conventions.md`.

## Slice entries

### <slice name>

- **Scope (repo paths):** <paths, patterns, or module names>
- **Why this slice:** <what makes this grouping a meaningful unit>
- **Risk class:** <low | medium | high | critical>
- **Classification:** <owned-clear | owned-risky | legacy-unclear | generated | vendored | third-party mirror | binary or asset-heavy | approval-gated | external-control-plane | cross-repo-boundary | blocked>
- **Related runtime units or flows:** <which entrypoints or flows this slice participates in>
- **Blockers:** <anything that prevents this slice from being worked on next>
- **Exit criteria:** <specific evidence required to call this slice "covered enough" at this stage; name evidence, not mood>
- **Verification capability ids:** <V01 through V20>
- **Confidence-ladder level:** <0 | 1 | 2 | 3>
- **Exact gate or next check:** <command id, replay, property, or named manual check>
- **Invalidated by:** <paths, schemas, configs, or control planes>
- **Next pass:** <02 architecture map | 03 critical-path comments | 04 logging audit | 07 adversarial review | 08 scenario stress-test | other>
- **Status:** <open | in progress | done | blocked | deferred>

### <next slice>

(Repeat.)

## Slice order

Suggested order for current run:

1. <slice name> - <one-line why this one first>
2. <slice name> - <one-line why>
3. <slice name> - <one-line why>

## Exclusions

Slices that will not receive deep code-level passes. Explain how they are described instead (map, manifest, runbook, ownership note).

- **<excluded slice>** - <reason> - <where it is explained instead>

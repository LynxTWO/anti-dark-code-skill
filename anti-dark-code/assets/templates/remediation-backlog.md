# Remediation Backlog

Ranked list of findings from the anti-dark-code passes that need follow-up. Built from steering files, architecture map, coverage ledger, unknowns, logging audit, adversarial pass, and scenario stress-test.

Do not guess. Do not claim full coverage unless the ledger supports it.

For canonical confidence levels, risk levels, and item status values, see `references/00-conventions.md`.

## Buckets

1. **Safe to fix now** - behavior-preserving, comment-only, docs-only, or narrow redaction outside protected areas
2. **Approval-gated** - touches a protected area; needs explicit human approval before any edit
3. **Needs more evidence** - the concern is real but the next safe step is not yet clear

## Items

### <short title>

- **Bucket:** <safe to fix now | approval-gated | needs more evidence>
- **Area or slice:** <where it lives>
- **Risk level:** <low | medium | high | critical>
- **Why it matters:** <one sentence on user or system impact>
- **Evidence found:** <files, lines, doc references>
- **Confidence:** <verified | inferred | unknown>
- **Approval needed:** <yes | no>
- **Recommended next pass:** <03 | 04 | 06 | 07 | 08 | 10 | 11 | 13 | 14 | 15>
- **Smallest safe next step:** <the minimum action that moves the item forward>
- **Verification capability ids:** <V01 through V20 that apply>
- **Reproducer:** <seed, trace, failing test, exact diff, invariant, or "not yet reproduced">
- **Verification plan:** <exact gate level and how we confirm the fix actually closed the hole>
- **Failure packet:** <path or n/a>
- **Invalidation trigger:** <what change reopens this finding or makes the evidence stale>
- **Rollback note:** <if applicable>
- **Observability note:** <if applicable>
- **Owner:** <person, team, or "unknown">
- **Status:** <open | ready | in progress | blocked | deferred | fixed>

### <next item>

(Repeat.)

## Grouping view (optional)

Group items by slice, subsystem, runtime unit, or control-plane path when that makes the backlog easier to act on.

### <slice or subsystem name>

- <item title> - <bucket> - <risk>
- <item title> - <bucket> - <risk>

## Holes and external boundaries

Call out gaps caused by:
- hidden runtime entrypoints
- out-of-repo control surfaces (remote config, feature-flag vendors, app-store or platform consoles, vendor dashboards)
- sibling repos, submodules, mirrored trees
- release tooling, migration runners, support scripts outside this repo
- notebooks, admin tools, one-shot ops scripts

List each boundary once. Note what evidence is missing and what the next best check is.

## Changelog

- <YYYY-MM-DD> - <what changed, who made the call>

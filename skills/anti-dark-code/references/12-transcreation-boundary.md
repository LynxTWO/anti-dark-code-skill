# Language, identity, and saved prose

Compatibility reference `12`. Load when locale/copy/authored-content changes or inspected code connect language to runtime truth. Apply the [core](../SKILL.md) and active task's authorization. Mapping is read-only; documentation and behavior changes need their respective scope.

## Trace ownership and consumers

Inspect the relevant schema, renderer, persistence/receipt contract, tests and existing content rules. Inventory only the requested surfaces: stable IDs/enums/keys, application copy, shared widgets, authored content/templates/prompts, generated summaries/logs, saved prose, compiled locale assets and copy-locking fixtures.

For each surface record owner, truth/display/mixed role, persistence, downstream consumers, allowed overlay fields, protecting check and unknowns. Trace whether text affects hashes, identity, deduplication, replay, ranking, permissions, billing, analytics or migration. English-looking identifiers alone do not prove a display field.

## Preserve the boundary

- IDs, tags, enums, payload fields, numbers, contracts and persisted state remain truth unless evidence says otherwise. Copy is display unless consumers make it behavioral.
- Do not translate canonical IDs, parse English to recover state, or make deterministic behavior depend on phrasing, punctuation, word order or grammar. Record existing violations as findings; a copy request does not authorize their repair.
- Translation cannot invent mechanics, outcomes, motives, legal meaning, prices, stats, permissions or state changes.
- Keep content overlays keyed by stable IDs and approved fields. Shared widgets receive caller-owned labels or semantic IDs; inspect existing ownership before proposing a boundary change.
- Preserve exact user-authored bytes unless that content change is explicitly authorized. Saved rendered text used in history, replay, hashes or audits is protected; do not regenerate it from today's locale or normalize it as cleanup.

## Protected decisions

Require explicit authorization covering the concrete change before rewriting saved text; changing receipt/hash/event/audit identity; changing migrations/backfills; changing behavioral/legal meaning in billing, access, entitlement, deletion, retention or compliance copy; adding runtime AI/external translation to a protected path; or adding a remote locale/CMS/flag dependency affecting behavior.

Carry existing approval within its reviewed scope. If missing, prepare evidence, proposed diff, compatibility impact and checks, then stop that edit. Continue independent authorized mapping or comments.

## Comments and evidence

Only when inline edits are authorized, explain the enforced boundary beside its schema, identity construction, renderer or shared widget. Name the actual field, consumer and consequence. A generic comment that says localization is safe cannot prove it. For proposal-only work, return the comment without editing.

Report source locale if known, canonical truth, display fields, mixed/protected surfaces, saved-text/hash risks, ownership, tests, unknowns and pending decisions. Reuse an existing language/content/architecture document when authorized; otherwise keep the report in the task response. No automatic document creation is required.

Before a broader transcreation/replay guarantee, load [claim proof](assurance-claim-proof.md) and [preservation](assurance-preservation.md) for its actual boundaries. Verify that locale changes leave IDs, mechanics, saved state, history and permissions unchanged under the stated contract. Missing runtime or migration evidence remains an explicit limit.

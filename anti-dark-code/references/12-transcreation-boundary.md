# Reference: Transcreation And Language Boundary

Use this reference when language, locale, UI copy, authored content, saved text, or future transcreation work could hide how runtime truth is produced.

**Mode:** primarily read-only mapping and docs. Behavior changes need the normal pass rules, tests, and approval gates. Saved-text or hash-semantics changes are protected when the repo treats them as persisted truth.

For confidence levels, the unknowns entry shape, and the canonical approval-gated areas list, see `00-conventions.md`.

## Goal

Keep rendered language downstream of structured truth.

A repo is transcreation-ready only when a future locale can adapt wording without changing ids, mechanics, saved state, audit history, permissions, prices, rankings, or simulation outcomes.

## When to use this reference

Use it when one or more fit:
- the repo has player-facing copy, authored content, narrative, emails, policy text, help text, prompts, or generated prose
- UI components contain literal copy that may need locale ownership later
- content ids, tags, enums, or mechanic keys are English-looking strings
- saved rows or event logs store rendered text
- text feeds deterministic ids, hashes, ranking, routing, permissions, billing, entitlement, or analytics decisions
- the user mentions localization, i18n, l10n, translation, transcreation, language packs, locale overlays, or copy ownership

## Start with repo evidence

Check existing steering and docs first:
- root and local steering files
- contract or schema docs
- content style guides
- system map or package-boundary docs
- tests or validators for text, content, locale overlays, saved rows, and renderers

If the repo has no language-boundary doc, create the smallest useful one near the repo's existing content, architecture, or review docs.

## What to map

List language surfaces by ownership:
- stable ids, tags, enums, payload keys, route names, table names, and contract fields
- app-owned UI copy and route chrome
- shared UI widgets and library components
- authored content, templates, barks, prompts, lore, emails, notifications, or help text
- runtime-generated summaries, logs, receipts, reports, or chronicle text
- persisted text fields
- derived compiled locale artifacts or generated content
- test fixtures and snapshots that lock copy

For each surface, mark:
- whether it is truth, display, or mixed
- whether it is persisted
- whether it participates in hashes, ids, dedupe, replay, ranking, permissions, billing, analytics, or migration logic
- whether it is approved for locale overlays or transcreation
- what validator or test protects it
- what remains unknown

## Boundary rules

- Stable ids, tags, enums, payload fields, numbers, contracts, and persisted state are truth unless repo evidence says otherwise.
- Rendered copy, prose, and locale text are display unless repo evidence says they currently affect behavior.
- Do not translate, rename, or reinterpret canonical ids to create a locale.
- Do not parse English strings to recover mechanic truth.
- Do not make deterministic systems depend on word order, punctuation, translated phrasing, or source-locale grammar.
- Do not let transcreated prose invent mechanics, outcomes, motives, legal meaning, prices, stats, permissions, or state changes.
- Treat saved rendered text as protected when it participates in replay, hashes, migrations, audit trails, or user history.
- Keep shared widgets copy-light when practical. Pass labels, semantic ids, or caller-owned display strings from the owning layer.
- Keep authored content translation keyed by stable ids and approved fields.

## Comment placement

Add or update nearby comments when code creates or enforces a language boundary:
- a schema limits locale overlays to approved text fields
- a renderer keeps prose downstream of receipts or structured facts
- a shared component receives caller-owned copy to avoid hiding locale policy
- a saved text field is deliberately not locale-ready yet
- rendered text participates in a deterministic id, hash, replay path, or duplicate suppression

Good comment shape:

```ts
// This field is rendered source-locale text, not locale truth. It stays out of
// overlays until saved receipt identity no longer depends on the summary string.
summary: z.string(),
```

Do not add a comment that simply says "localization happens here" unless it names the boundary and the risk.

## Approval gates

Stop for explicit approval before editing when the next step would:
- rewrite existing saved text in place
- change event-log, audit-log, receipt, or hash identity
- change migration or backfill behavior
- change billing, entitlement, access, deletion, retention, or compliance copy where wording carries product or legal meaning
- add runtime AI translation or external translation services to a protected path
- add a new remote locale, CMS, feature flag, or control-plane dependency that affects runtime behavior

Document the finding first. Propose the smallest safe edit. Stop before the protected edit.

## What to document

Use existing repo conventions first. If there is no fit, create one of:
- `docs/content/transcreation-framework.md`
- `docs/architecture/language-boundaries.md`
- `docs/review/transcreation-boundary.md`
- `docs/unknowns/transcreation-boundary.md`

Record:
- source locale if known
- canonical truth surfaces
- transcreation-approved display surfaces
- mixed or protected surfaces
- validators and tests
- unknowns and next checks
- approval gates crossed or still pending

## Unknowns

Use the unknowns entry shape from `00-conventions.md`.

## Acceptance checklist

The final result should:
- separate truth surfaces from display surfaces
- name saved text and hash risks plainly
- identify which copy belongs to app, content, shared UI, or runtime generation
- keep canonical ids and tags language-neutral
- record unknowns instead of guessing
- add comments only where they protect a real language boundary
- say which tests, validators, or docs should move before broad transcreation work

# Reference: Comment Critical Paths Without Changing Behavior

Use this reference when illuminating the repo's most important code paths with comment-only changes.

**Mode:** comment-only. No logic, control-flow, import, signature, dependency, config, or formatting changes outside touched comment lines.

For confidence levels and the unknowns entry shape, see `00-conventions.md`.

This reference may need many passes to cover all applicable critical paths.

## Goal

Add high-value explanatory comments to the most important systems in the repo without changing behavior. Make critical code explainable to the next engineer. Comments should explain why the code exists, what must remain true, and what breaks if it changes carelessly.

## Adapt to the repo before starting

If `docs/architecture/system-map.md` or `docs/architecture/service-map.md` exists, use it.

If not, inspect the code directly.

Use the coverage ledger when the repo is large, mixed, or old.

Pick paths based on actual repo risk, not generic categories. Record why each selected path earned this pass.

Common candidates:
- auth and session handling
- access control and privilege checks
- billing, orders, payouts, credits, purchases, entitlements
- recommendation, ranking, matching, scoring, or model routing logic
- moderation or trust and safety logic
- data deletion, retention, export, compliance workflows
- CI or CD paths that deploy, seed, migrate, backfill, or repair live state
- release tooling or platform hooks with live side effects
- workflow engines and state machines
- webhook intake and external sync
- concurrency, locking, idempotency, replay protection
- background jobs with irreversible side effects
- migrations or backfill logic
- admin-only operations
- save and load flows in games or mobile apps
- notebook, task-runner, or one-shot script paths that touch live systems
- editor tools, import hooks, build scripts when they affect shipped behavior
- locale, transcreation, or copy-rendering boundaries where text could be mistaken for runtime truth

For an existing repo: comment the real code paths that carry the highest operational, security, privacy, or state-corruption risk.

For a new repo: do not invent comments for code that does not exist. Create a short plan in `docs/architecture/critical-path-plan.md` that names future modules and the comment rules they must follow.

## Task

Add comment-only changes to selected critical paths.

Also create or update `docs/unknowns/critical-paths.md`.

## Path selection note

At the start of the pass, record:
- which paths were selected
- why they were selected now
- what remains uncovered
- which next slice should run after this one

Keep this note in the task summary or the repo's coverage ledger.

## What to comment

For each selected path, add comments where they earn their keep. Explain:
- why the subsystem exists
- which invariants must stay true
- which inputs are trusted or untrusted
- which side effects happen
- which failure modes matter
- which security or privacy assumptions matter
- which concurrency or ordering assumptions matter
- which repair or recovery steps a future engineer may need
- which edge cases are easy to break by accident

Do not comment every line. Comment the points where someone could make a dangerous mistake.

## Where comments usually earn their keep

Place comments next to the code that enforces or depends on a rule. Common high-value locations:

- deterministic id, timestamp, seed, hash, or replay construction
- duplicate suppression, idempotent append paths, retries, and recovery paths
- migration reset, backfill, compatibility mirror, or saved-state interpretation
- trust-boundary checks for untrusted input, external callbacks, imports, or local storage
- authorization, entitlement, deletion, retention, or release gates
- concurrency locks, serialized action queues, ordering assumptions, and event tails
- receipt, audit-log, or history construction that later code treats as truth
- narrative, UI, locale, or transcreation renderers that must stay downstream of structured facts
- schema or validator branches that define what content or tooling is allowed to claim

If the safest explanation would live far from the code, prefer an adjacent doc or unknowns entry.

## Comment calibration examples

Good comments name the rule and the risk:

```ts
// Receipt ids include the rendered summary today. Changing summary generation
// changes hash identity, so locale work must add a migration note first.
const id = hashRecord({ heroId, tick, sequence, kind, summary });
```

```ts
// Locale overlays stop at authored text. Saved receipts stay canonical until the
// persistence contract supports render-on-read text.
export const localeOverlayEntrySchema = z.union([...]);
```

```ts
// Serialize startup and resume so two lifecycle events cannot simulate from the
// same receipt tail and then both persist divergent results.
let inFlight: Promise<void> | null = null;
```

Weak comments restate syntax or overclaim:

```ts
// Create an id.
const id = hashRecord({ heroId, tick, sequence, kind, summary });
```

```ts
// This makes localization safe.
export const localeOverlayEntrySchema = z.union([...]);
```

## Worked example: turning a finding into a comment

Finding from a quick read of an idempotent webhook handler:

> The handler reads `request.body.event_id`, looks it up in `processed_events`, and bails early if found. Without this lookup, Stripe retries (which can fire seconds apart) would double-charge.

Good comment:

```ts
// Idempotency: Stripe retries within seconds of a transient 500. The early
// bail on a known event_id prevents a double-charge replay. Move this check
// only if processed_events grows a TTL - without it, the duplicate will leak
// past the gate after rows expire.
const seen = await processedEvents.has(req.body.event_id);
if (seen) return res.status(200).end();
```

Notice what the comment does and does not do: it names the upstream behavior (Stripe retries), the invariant (no double-charge), the failure mode (duplicate leak past TTL), and where the safeguard is. It does not narrate the syntax.

## Commenting rules

- Explain why, not what.
- Keep comments short.
- Use plain language.
- Active voice when clearer.
- Name the risk directly.
- If code enforces a security property, say what property.
- If code depends on ordering, idempotency, or eventual consistency, say so plainly.
- If a branch exists because of a real bug or incident pattern, say so only when repo evidence supports it.

## Do not do these things

- Do not change logic, control flow, imports, signatures, dependencies, or config.
- Do not change formatting outside the lines you are commenting.
- Do not touch generated or vendored files.
- Do not touch mirrored third-party code, minified code, binary assets, or engine-owned serialized artifacts.
- Do not alter toolchain-sensitive comments: pragma comments, linter directives, type-affecting docblocks, SQL hints, framework magic comments, engine metadata comments, serialized asset comments.
- Do not guess when behavior is unclear.

For Unity, Unreal, Godot, or other engine-heavy repos, keep scene files, prefabs, metadata, and large serialized assets out of comment churn unless the repo already treats them as hand-maintained text. Prefer adjacent docs, manifests, or runbooks instead.

## What to do when behavior is unclear

Record the uncertainty in `docs/unknowns/critical-paths.md` using the unknowns entry shape from `00-conventions.md`. Anchor each entry to a specific line range or function.

## Writing rules

Use the voice of a careful senior engineer leaving notes for the next person.

- Plain and direct.
- Avoid stock transitions and stock wrap-up lines.
- Avoid stiff corporate tone.
- Avoid vague openings that hide the subject.
- ASCII punctuation and straight quotes only.

## Pairing with hygiene pass

After adding comments, run the writing hygiene reference (`06-writing-hygiene.md`) on all touched text. Or use `combined-03-06-loop.md` for a slice-by-slice loop that does both in one bounded pass.

## Deliverable summary

When the task is done, return:
- the comment-only changes
- `docs/unknowns/critical-paths.md` contents
- a short summary of which paths were illuminated and what is still unclear
- an estimate of how many more passes should run and what they should hit next

## Acceptance checklist

The final result should:
- cover the highest-risk paths in the current slice
- add comments only where they reduce future mistakes
- explain invariants and failure modes
- preserve behavior exactly
- call out unknowns instead of guessing
- keep serialized or generated artifacts out of inline comment churn

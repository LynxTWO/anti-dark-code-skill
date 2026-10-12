# Readable documents and local work

Load for first setup, audience choice, durable documentation or artifact organization. The [core](../SKILL.md) controls authority and evidence. These rules add no installation, cleanup or publication permission.

## Explanation depth

At setup or first documentation use, offer: "How much explanation would help: plain language, balanced, or developer shorthand?" These select `guided`, `standard`, or `expert`. Experience suggests a default; the person's choice controls. Continue independent work while the choice is pending, using concise standard explanations.

When Scaffold-Kit is present, reuse its Triage Card's Explanation depth (or existing Interview depth). Otherwise save a requested choice in the existing task record or repo-owned calibration README, when writes are authorized. One-off work can keep the choice in the conversation. Do not create a global profile, validated JSON key or second setting. Updates preserve the repo's choice; managed core defaults cannot replace it.

All depths use one canonical document set with identical facts, IDs, statuses, uncertainty, risk, evidence and approval requirements:

- **Guided:** plain sentences, define jargon once, use a concrete example when needed.
- **Standard:** short descriptions with the key tradeoff.
- **Expert:** terse technical terms, IDs and evidence links.

Open with the outcome and a short view of what happens now, how we prove it, what waits, decisions needed and next action. Put necessary technical detail after it or link the canonical source. Remove repetition and empty scaffolding, preserving required evidence fields and stop conditions. Changing depth changes explanations only; do not migrate stored records or generate separate audience copies.

## Ownership and freshness

Code/configuration own implemented behavior. Scaffold-Kit owns intended scope and decision rationale. ADC owns observed maps, findings, coverage and verification evidence. Keep one canonical record per fact or unknown; other documents use a summary and link. Kit risk rows and ADC unknowns have different fields/statuses: preserve the owning record's vocabulary instead of synchronizing copies.

Use an existing documentation index; if authorized and none exists, one short `docs/README.md` can point to current plans, active brief, calibration, evidence and history. Host steering files remain short pointers. Update an active brief and its index/host pointers together. Historical design records carry their date/version, scope and current replacement, and stay out of default startup reads.

On resume or relevant code/configuration change, verify source identity, paths and evidence dependencies before reusing a claim. Refresh invalidated evidence only. Put checked source and triggers in the existing map, coverage row or state record. A matching repository binding proves identity continuity, not freshness.

## Folders and closeout

Reuse one ignored `work/<task-or-slice-id>/` for scratch; note purpose and disposal condition in the existing work record or a tiny README. Reuse it on resume rather than creating numbered scratch directories. Keep [calibration and run stores](00-conventions.md#calibrated-local-paths) in their canonical locations; do not relocate them for tidiness.

At closeout compare the diff and actual checks with approved intent. Record skips as skips. Retain cited evidence durably, or use an approved verifiable archive and preserve references before removing originals. Ignored and uncited do not prove disposable. Cleanup remains the explicit [artifact workflow](09-artifact-gc.md); documentation maintenance never silently deletes or archives files.

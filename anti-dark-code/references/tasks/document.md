# Document

Use for comments, architecture documentation, reports, or prose cleanup. The [core](../../SKILL.md) supplies evidence, privacy, and authority rules. Documentation work does not authorize behavior changes.

## Inputs

Inspect relevant source before loading style guidance; load writing hygiene for the final prose check. Inputs are requested documents or source scope, writing conventions, current evidence, and the distinction between explanatory prose and text consumed as instructions by a runtime, build tool, policy engine, or agent.

## Procedure

1. Inspect relevant source and the current diff. Separate directly supported statements from runtime or external claims. Reuse maps only after checking evidence identity and dependencies.
2. Classify edits before writing. Compiler pragmas, lint/type suppressions, doctests, executable examples, shebangs, generated metadata, skill instructions, release policy, and machine-parsed Markdown can affect behavior. A `.md` suffix or comment syntax does not prove prose-only scope.
3. For critical paths, load [comments](../03-critical-path-comments.md). Explain the invariant, surprising order, ownership, or consequence at its enforcement point. Delete stale or repeated prose first; avoid narrating syntax.
4. For locale files, display strings, IDs, hashes, saved text, or prompts, load [language boundaries](../12-transcreation-boundary.md) before editing. Distinguish application copy from persisted user prose. Do not normalize, translate, or regenerate saved prose under a comment-cleanup request.
5. Convert behavior problems discovered while documenting into findings and proposals. Do not silently fix them in the documentation diff. Separately authorized remediation uses [Remediate](remediate.md), with its own verification and approval bindings.
6. Inspect the exact final diff against the edit classification. Preserve identifiers and data. Apply [writing hygiene](../06-writing-hygiene.md) to changed prose. Brevity cannot remove a necessary stop or proof obligation.

## Evidence and output

Return the requested document or diff with supporting locators and confidence labels for consequential claims. Name excluded behavioral directives and persisted content. Report actual checks establishing the edit's scope; a text-only diff cannot prove unchanged behavior when a consumer interprets that text.

For comments-only edits, inspect syntax and directive placement. Run an existing parser or targeted check only when authorized and when it tests a plausible introduced failure. Do not add tests that mirror prose. For instruction-bearing documentation, use [Verify](verify.md) to select a behavioral check and report unresolved effects.

Create durable artifacts only when requested or when an authorized checkpoint is needed. Prefer the existing document and canonical rule rather than scattering copies across comments and host files.

## Stop conditions

Stop an edit when preserving behavior requires an out-of-scope decision about a directive, identifier, saved prose, or protected area. Prepare the concrete proposal before requesting that decision. Never insert sensitive values as examples or proof. Complete only after reviewing the final diff for unintended behavior changes and reporting what checks did and did not establish.

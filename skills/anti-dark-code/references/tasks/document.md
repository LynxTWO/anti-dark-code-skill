# Document

Use for comments, architecture documentation, reports, or prose cleanup. The [core](../../SKILL.md) supplies evidence, privacy, and authority rules. Documentation work does not authorize behavior changes.

## Inputs

Inspect source before style guidance; load writing hygiene for prose checks. Gather requested scope, conventions and current evidence. Distinguish explanatory prose from runtime, build, policy, or agent instructions.

When explanation depth is unset or the person changes it, load [documentation](../documentation.md).

## Procedure

1. Inspect relevant source and the current diff. Separate directly supported statements from runtime or external claims. Reuse maps only after checking evidence identity and dependencies.
2. Classify edits before writing. Compiler pragmas, lint/type suppressions, doctests, executable examples, shebangs, generated metadata, skill instructions, release policy, and machine-parsed Markdown can affect behavior. A `.md` suffix or comment syntax does not prove prose-only scope. For repository instruction or steering files, load [steering](../01-steering.md).
3. For critical paths, load [comments](../03-critical-path-comments.md). Explain the invariant, surprising order, ownership, or consequence at its enforcement point. Delete stale or repeated prose first; avoid narrating syntax.
4. For locale files, display strings, IDs, hashes, saved text, or prompts, load [language boundaries](../12-transcreation-boundary.md) before editing. Distinguish application copy from persisted user prose. Do not normalize, translate, or regenerate saved prose under a comment-cleanup request.
5. Convert behavior problems discovered while documenting into findings and proposals. Do not silently fix them in the documentation diff. Separately authorized remediation uses [Remediate](remediate.md), with its own verification and approval bindings.
6. Inspect the classified final diff. Preserve identifiers, data, each claim's meaning and uncertainty, checks, evidence, risks, next steps and approvals. Keep untested hypotheses verbatim. Apply [writing hygiene](../06-writing-hygiene.md) to changed prose; brevity cannot remove stops or proof obligations.

## Evidence and output

Return the requested document or diff with supporting locators and confidence labels for consequential claims. Name excluded behavioral directives and persisted content. Report actual checks establishing the edit's scope; a text-only diff cannot prove unchanged behavior when a consumer interprets that text.

For comments-only edits, inspect syntax and directive placement. Run an existing parser or targeted check only when authorized and when it tests a plausible introduced failure. Do not add tests that mirror prose. For instruction-bearing documentation, use [Verify](verify.md) to select a behavioral check and report unresolved effects.

Save artifacts only for requested work or authorized checkpoints. Reuse existing documents and rules. Mark obsolete plans superseded in place, dated and linked to current status; preserve original text and history.

## Stop conditions

Stop an edit when preserving behavior requires an out-of-scope decision about a directive, identifier, saved prose, or protected area. Prepare the concrete proposal before requesting that decision. Never insert sensitive values as examples or proof. Complete only after reviewing the final diff for unintended behavior changes and reporting what checks did and did not establish.

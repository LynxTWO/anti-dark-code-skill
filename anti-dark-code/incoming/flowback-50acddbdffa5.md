# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.07-unified.14`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Bind cached tools to runtime targets

- Scope: repo-agnostic
- Lesson: Correct argv and working directory do not prove which repository a compiled or cached tool will read, validate or modify. Repository-bound tools can retain an embedded path from another checkout. Verify their resolved runtime target before accepting a gate verdict or allowing writes.
- Evidence: A local regression selected an isolated checkout but the existing helper returned its compiled checkout. After runtime workspace validation replaced that behavior, six tests passed, covering two checkouts with one executable, nested workspaces, rejected unrelated or malformed roots, invalid invocation directories and repository-boundary rejection. Four affected existing tests also passed.
- Limits: This is one observed failure class. It does not establish that every build cache reuses binaries across checkouts, or that all tools should derive targets from cwd. Intentionally relocatable tools may use explicit reviewed targets. Filesystem identity checks alone do not prove that every downstream read or write respects the selected root.
- Proposed target: references/specialist-gate-environment.md
- Proposed change: Immediately before Expected work, add a short Runtime target binding section requiring observed target selection, explicit rejection of invalid or foreign roots, and an isolated same-executable two-checkout regression before relying on repository-bound tools.

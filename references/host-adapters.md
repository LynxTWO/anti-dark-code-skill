# Reference: Host Adapters

The anti-dark-code core is model-neutral. Load one host addendum only when discovery paths or tool mechanics matter.

## Router

- Claude Code -> `host-claude-code.md`
- Codex -> `host-codex.md`
- Gemini CLI -> `host-gemini-cli.md`
- another harness -> `host-generic.md`

## Rule

A host addendum may change:

- where the skill is discovered
- which steering file the host reads
- tool names and batching mechanics
- optional host metadata

It may not change:

- evidence labels
- approval gates
- sensitive-data rules
- calibrated-core ownership
- deterministic-first behavior
- verification capability meanings
- flow-back trust boundaries

Do not duplicate the universal skill into several independently edited variants. Keep one core and thin adapters.

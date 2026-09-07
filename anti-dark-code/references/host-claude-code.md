# Claude Code adapter

Load when Claude Code discovery, tooling, permissions, recovery or usage mapping affects the task. Preserve the [core contract](../SKILL.md).

## Discovery and steering

The repository installer maintains the canonical skill under .agents/skills/anti-dark-code/ and can create a thin .claude/skills/anti-dark-code/ adapter. Keep policy in the canonical copy; the adapter points inward and does not carry an independently edited version.

Use existing AGENTS.md for shared repository policy when practical. CLAUDE.md contains Claude-specific mechanics and supported repository facts. Align shared obligations without erasing intentional host differences. Repo-local adapter and managed paths must obey [physical isolation](13-calibrated-local-mode.md); user-level discovery aliases are a separate case.

## Tools and recovery

Inspect available native file, search, edit and process tools in the active session. Prefer those tools for their intended operations, batch independent reads where supported, and serialize shared-output mutations. Model, effort and subagent controls vary with the active host; use only exposed options and the user's existing constraints.

Review exact shell commands before execution. Preserve pre-commit and commit-signing safeguards unless the user explicitly authorizes changing them. Available tools and generated gate configuration do not supply owner permission.

If execution or subagents are unavailable, work inline on accessible evidence and return exact proposed checks with their limitations. A configured command is configuration evidence, not a live result.

Treat any saved run or cache feature as an optional host facility. On resume, inspect source identity, completed output provenance and interrupted operations before reuse or retry. Do not imply preserved output guarantees free model calls or permission to repeat side effects.

## Optional usage mapping

For Claude-style reported counters, normalized input is uncached input plus cache creation plus cache read; normalized output is the reported output. Provider total is normalized input plus output under that declared counter contract. Cache counters are input subsets after normalization, not additional totals.

Keep absent counters null, inspect the exact source format, and pin usage_semantics and adapter version. UI quotas and estimates are not reported token counts. Apply [efficiency rules](16-community-feedback-and-efficiency.md) before recording, comparing or publishing results.

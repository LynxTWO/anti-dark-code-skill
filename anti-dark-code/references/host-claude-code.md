# Host Addendum: Claude Code

Load after the universal `SKILL.md` when running in Claude Code.

## Discovery

The repo installer keeps the canonical skill under `.agents/skills/anti-dark-code/` and may create a thin adapter under `.claude/skills/anti-dark-code/`. The adapter points back to the canonical core and should not carry a second policy copy.

## Tooling

- Prefer native file read, search, and edit tools for file work.
- Use shell execution for deterministic enumeration, version control, builds, and reviewed gates.
- Batch independent reads and searches when the harness supports it.
- Do not skip pre-commit or commit-signing safeguards unless the user explicitly asks.
- Keep long command output in local artifacts and return compact summaries.
- Use subagents only for independent judgment tasks. Do not spend them on file counts, grep, gate monitoring, or log compression.

## Steering

Keep shared policy in `AGENTS.md` when possible. Use `CLAUDE.md` only for Claude-specific mechanics or repo facts already supported by evidence.

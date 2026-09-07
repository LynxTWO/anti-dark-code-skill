# Codex adapter

Load when Codex discovery, permissions, tools, recovery or usage mapping affects the active task. Keep the [core contract](../SKILL.md) unchanged.

## Discovery and steering

Use the canonical project skill at .agents/skills/anti-dark-code/ when the active host supports it. Existing AGENTS.md files provide repository steering; keep them compact and point to calibration instead of copying it. Optional agents/openai.yaml is presentation metadata, not a second policy source.

Check the active tool surface and instructions rather than assuming a particular Codex release. File/search/process tools may be exposed directly or through an orchestration wrapper. Batch independent reads when supported and serialize dependent writes, approvals and shared-output operations. Missing subagents means inline work; model and effort overrides must follow active host/user controls.

## Execution and recovery

Sandbox access and approval mechanics come from the current session. A repository gate proposal cannot override them. Review exact command, cwd, environment and side effects, then use existing authorization; when blocked, retain the proposed command and named prerequisite without claiming an execution result.

Capture the actual process exit code. On PowerShell, native-process status uses $LASTEXITCODE; in-session scripts need terminating errors/try-catch or their own success status. Do not reuse stale native status as script evidence. Keep Windows background helpers hidden unless the user needs visible interaction.

Use saved artifacts or supported session recovery only after rechecking source identity, evidence dependencies and interrupted side effects. A resumed session does not establish free calls or fresh evidence. Record retries and revalidation in measured usage.

## Optional usage mapping

For OpenAI-style reported usage, normalize total input, top-level output and provider total as supplied by the host. Cached input is an optional input subset; reasoning is an optional output subset. Do not add subsets again. Missing breakdowns remain null; preserve the exact reported total.

Pin usage_semantics and adapter version to the inspected source format, especially when reading transcripts. Source formats can change independently of the skill. [Efficiency rules](16-community-feedback-and-efficiency.md) govern opt-in, quality comparisons and publication.

# Host Addendum: Codex

Load after the universal `SKILL.md` when running in Codex.

## Discovery and Metadata

Use the canonical project skill under `.agents/skills/anti-dark-code/`. Optional Codex presentation metadata lives in `agents/openai.yaml` and must not become a second instruction source.

## Tooling

- Keep deterministic repo work in scripts or shell commands with real exit codes.
- Use `AGENTS.md` for compact repo steering and point it to calibration rather than copying calibration into the file.
- Give the model the smallest relevant source slice plus a compact failure packet.
- Keep generated run logs outside the prompt unless a failure requires expansion.
- Do not let an implementation agent weaken tests to make its own patch pass.

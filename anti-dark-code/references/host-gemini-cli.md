# Host Addendum: Gemini CLI

Load after the universal `SKILL.md` when running in Gemini CLI.

## Discovery

Use the canonical `.agents/skills/anti-dark-code/` project copy when supported. Avoid a second `.gemini/skills` core unless the environment cannot use the canonical location. A fallback should be a pointer, not a fork.

## Tooling

- Put repeatable enumeration, parsing, validation, and gate work in deterministic scripts.
- Keep `GEMINI.md` focused on host mechanics and repo pointers.
- Return concise structured output from scripts so the model reads failures, not noise.
- Keep calibration as the durable repo memory and update it only from evidence.

# Host Addendum: Generic Agent Harness

Use the universal skill directory as the source of truth.

If the harness does not discover Agent Skills automatically:

1. Add a short pointer in its existing instruction file.
2. Point to the universal `SKILL.md` and the repo-local `calibration/` directory.
3. Map host file, search, edit, and process tools to the core workflow.
4. Keep deterministic commands in `scripts/adc.py` or repo-native tools.
5. Do not copy the full policy into another file.

When the harness lacks subagents, run passes inline. When it lacks executable tools, produce exact commands and mark live behavior as inferred until a human runs them.

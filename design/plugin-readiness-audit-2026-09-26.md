# Plugin readiness audit, 2026-09-26

Scope: what this repository must change to ship the skill as a Claude Code plugin, an Agent Plugins package (Codex, Cursor, Copilot CLI), and a Gemini CLI extension, while keeping the installer, release provenance and consumers working. Read-only audit; proposals only. Sources are official documentation fetched on the audit date; every claim below names its kind and confidence.

## Requirements shared by every host

| Requirement | Source | This repo today | Status |
|---|---|---|---|
| Skill directory name equals frontmatter `name`; `[a-z0-9-]`, 1 to 64 characters | agentskills.io/specification; cursor.com/docs/context/skills; cli.github.com/manual/gh_skill_publish | `anti-dark-code/` and `name: anti-dark-code` | verified, meets |
| `description` 1 to 1024 characters; hosts truncate or shorten under catalog pressure (Claude Code lists at most 1,536 characters of description plus `when_to_use`; Codex fits all skill descriptions into 2% of context) | agentskills.io/specification; code.claude.com/docs/en/skills; learn.chatgpt.com/docs/build-skills | 846 characters; trigger terms appear last | verified, meets the limit; see F3 |
| Portable frontmatter set: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`; the claude.ai upload path rejects any other key | agentskills.io/specification; code.claude.com/docs/en/skills | `name`, `description` only | verified, meets; see F2 |
| Relative paths from the skill root; scripts run from there; keep references one level deep | agentskills.io/specification; agentskills.io/skill-creation/using-scripts.md | relative paths throughout; `references/tasks/*.md` is two levels deep | verified; see F4 |
| No host-only body syntax (`` !`command` ``, `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`) | code.claude.com/docs/en/skills | none found in `SKILL.md` or `references/` (grep, 74 files) | verified, meets |
| `SKILL.md` under 500 lines and about 5,000 tokens | agentskills.io/specification | 94 lines; 1,139 words once the core-headroom change merges (1,198 before it) | verified, meets |
| Consumers read `.agents/skills/<name>/` (Codex, Gemini, Antigravity, Copilot, Cursor) and `.claude/skills/<name>/` (Claude Code) | learn.chatgpt.com/docs/build-skills; geminicli.com/docs/cli/skills; docs.github.com; cursor.com/docs/context/skills; code.claude.com/docs/en/skills | installer writes copies to both, refuses symlink components | verified, meets |
| Distribution layout `skills/<name>/SKILL.md` at the plugin root | agent-plugins.org/specification; developers.openai.com/codex/plugins/build; geminicli.com/docs/extensions/reference; cli.github.com/manual/gh_skill_publish | core lives at `anti-dark-code/` at the repo root | verified, does not meet; see F1 |

## Findings

### F1. The core is not under `skills/` (high, source_fact, verified)

Every plugin container except Claude Code discovers skills only as immediate children of `skills/`: Agent Plugins 1.0 ("No recursive searching"), Codex plugin manifests (`"skills": "./skills/"`), Gemini extensions (`skills/<name>/SKILL.md`), and `gh skill publish` (`skills/*/SKILL.md`). Claude Code is the exception: its manifest `skills` field accepts "one folder holding `SKILL.md` directly" and `"."` for the plugin root (code.claude.com/docs/en/plugins/manifest-reference.md, Fields table and Path rules).

Consequence: a Claude Code plugin needs no layout change. Everything else does.

The path `anti-dark-code/` is load-bearing: 13 occurrences in `scripts/adc.py` (release-check diff scope `anti-dark-code/references` and `anti-dark-code/assets`, digest computation), 4 in `tests/test_adc.py`, 11 in `.github/workflows/*.yml`, the release ZIP prefix `anti-dark-code-skill/`, and every consumer's installer invocation (`--skill <path>`). A symlink `skills/anti-dark-code -> ../anti-dark-code` is not an option: only Codex documents following symlinked skill folders, Windows checkouts do not reliably materialize them, and this skill's own preservation rule forbids link traversal on managed paths.

Options:

1. Move the core to `skills/anti-dark-code/` in a versioned release (proposed `unified.16`), updating the 28 path references, the ZIP prefix, `MIGRATION.md`, and the consumer install recipe. One source of truth; every container works. Cost: one careful PR with the three-platform suite, a `release-check` run against the new tag, and one consumer install rehearsal (a fork of a consuming repository, installer with `--expect-core-digest`).
2. Keep the layout and publish a generated distribution tree at release time (`dist/skills/anti-dark-code/` plus manifests) as a release asset or a separate plugin repository that vendors the tagged core. No source move; two trees to keep identical; `release-check` would need to verify the generated tree's digest equals the core digest.
3. Claude Code plugin only, now, via the manifest `skills` field; defer the rest.

Recommendation: 3 now, then 1. Option 2 adds a second tree the provenance guards would have to police forever.

### F2. Frontmatter lacks the portable optional fields (medium, source_fact, verified)

Add, in this order, to `SKILL.md`:

```yaml
license: FSL-1.1-MIT. LICENSE.md has complete terms
compatibility: Instructions need nothing. Bundled scripts need Python 3.12 or newer and Git for provenance checks.
```

`license` follows the spec's example form and the core already ships `LICENSE.md`. `compatibility` (limit 500 characters) states the one real requirement, which `README.md` already asserts. `metadata` is optional; do not put the version there, since `VERSION` is canonical and two copies would need a consistency gate. `adc.py validate` checks only that `name` and `description` exist, so the added keys pass; confirm by running it. Keep `allowed-tools` absent: hosts disagree on its form (tool-rule strings in the spec and Claude Code, tool names in Copilot, arrays rejected by `gh skill publish`).

### F3. Description puts its trigger terms last (medium, configured_behavior, inferred)

Hosts shorten or truncate descriptions when many skills are installed; Codex shortens descriptions first when the catalog exceeds its budget. The current 846-character description opens with a purpose sentence and ends with "Trigger terms include ...". Rewrite to lead with the triggering situations and keep the total near 500 characters. The effect on activation rates is not measured; the change also returns roughly 50 words to the core budget. A micro-test (five fresh-context samples per variant against a no-change control, as `design/evals/` already practices) would settle it if anyone doubts the ordering matters.

### F4. Task cards sit two levels deep (low, source_fact, verified)

`references/tasks/*.md` violates the spec's "keep file references one level deep" guidance. Claude Code and Codex resolve the paths correctly today (observed in this repository's own sessions), and the guidance is advisory. Leave it; record it here so nobody flattens the tree by accident during F1.

### F5. Manifests to add (medium, configured_behavior, verified against each reference)

Once F1's decision is made:

- `.claude-plugin/plugin.json`: `name` (kebab-case; note that `anti-dark-code` yields the invocation `/anti-dark-code:anti-dark-code`, which is acceptable for a single-skill plugin and keeps marketplace search obvious), `version` equal to `VERSION`, `description`, `author`, `license`, `repository`, `keywords`, and `skills: ["./anti-dark-code"]` until F1 option 1 lands, then the default `skills/` scan. Validate with `claude plugin validate --strict`.
- Root `plugin.json` per Agent Plugins 1.0: `$schema` fixed to `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`, `name`, `version`, `description`, `license`, `repository`. Closed schema; unknown root fields are ignored with a report. Requires F1 option 1.
- `gemini-extension.json`: `name`, `version`, `description`. Requires F1 option 1. Gemini CLI is being retired for non-enterprise users in favor of Antigravity CLI, whose root `plugin.json` uses a different `$schema` and cannot coexist with the Agent Plugins one in the same directory; do not target Antigravity until its acceptance of the Agent Plugins schema is documented.
- Marketplaces: `.claude-plugin/marketplace.json` with a `github` source and `ref` pinned to the release tag (installs then match this repository's rule that consumers install only from a clean `git archive <tag>`); `.agents/plugins/marketplace.json` for Codex with the same pin.
- `agents/openai.yaml` stays inside the skill; the spec permits additional files and Codex reads it for presentation. In a Claude Code plugin the plugin-root `agents/` directory means subagents, but the skill directory is not the plugin root, so there is no collision.

### F6. Release gates to add (medium, configured_behavior, verified that the tools exist)

Extend `release-check` with optional, tool-present gates, each recorded as `capability unavailable` when its tool is missing rather than silently skipped: `claude plugin validate --strict .`, `skills-ref validate ./anti-dark-code` (the reference validator from agentskills/agentskills; demonstration-grade, still the only spec-owned check), `gh skill publish --dry-run`, and `node scripts/validate_skill.cjs` from the Gemini CLI repository if Gemini remains a target. Add a documentation-contract test asserting every manifest's `version` equals `VERSION` once manifests exist.

### F7. Things that already meet the bar (verified)

Installer writes copies, never symlinks, to both `.agents/skills/` and `.claude/skills/`; `LICENSE.md` ships inside the core; `SKILL.md` carries no Claude-only syntax; the name and directory match; scripts are non-interactive and expose `--help`; the description is under the spec limit; the core is under the size guidance.

## Proposed sequence

1. Now, no layout change: F2 (two frontmatter lines), F3 (description rewrite with a micro-test), `.claude-plugin/plugin.json` pointing at `./anti-dark-code`, `claude plugin validate --strict` in `release-check` behind a tool-present check. Small PR.
2. `unified.16`: F1 option 1, root Agent Plugins `plugin.json`, `gemini-extension.json` if still wanted, both marketplaces, remaining F6 gates, `MIGRATION.md` entry, consumer install rehearsal. One PR plus the release recipe.
3. After the tag: `claude plugin marketplace add LynxTWO/anti-dark-code-skill`, `gh skill publish --tag`, and the Codex marketplace entry. Record the first successful install from each in `docs/`.

## Not examined

Antigravity's plugin loader behavior beyond its documentation; Cursor's recursive standalone scan versus its plugin loader; any host's treatment of an `agents/` subfolder inside a skill directory; size limits for supporting files, which no host documents. None of these blocks step 1.

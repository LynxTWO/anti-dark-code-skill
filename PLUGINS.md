# Plugin packaging

Plugin packaging starts with unified.16. Published unified.15 archives
still use the older `anti-dark-code/` source path and do not include these plugin
manifests. Do not point a plugin installation at a pre-packaging tag.

## One core, several hosts

The sole universal core is `skills/anti-dark-code/`. A standalone installation
still copies its contents to `.agents/skills/anti-dark-code/` in a consuming
repository. Calibration stays with that repository. No symlink or duplicated
distribution tree is needed.

| Host | Package entry point | Skill discovery |
| --- | --- | --- |
| Agent Plugins 1.0 clients | `plugin.json` | `skills/anti-dark-code/SKILL.md` |
| Codex / OpenAI | Portable manifest with `extensions.com.openai`; `.codex-plugin/plugin.json` compatibility fallback | Same core |
| Claude Code | `.claude-plugin/plugin.json` | Same core under `skills/` |
| Gemini CLI | `gemini-extension.json` | Same core under `skills/` |

Both marketplaces expose the repository root as one plugin. Relative `./` means
the marketplace root, not the directory containing its catalog. There is no
second `plugins/anti-dark-code/` copy. Metadata advertises a skill only: no MCP
server, credentials, automatic hooks, telemetry, or background jobs are enabled.
Existing optional collection commands still require their own explicit opt-in.

The host owns its plugin cache. Do not keep both a plugin-provided and a standalone
global copy enabled in one host after switching installation methods. Repository
calibration and an opted-in usage ledger are separate from that discovery choice.

## Install a reviewed package

Use the published `v2026.09.27-unified.16` tag and verify its archive/digest using
the release instructions. Development checkouts are for local testing. Pin the catalog
checkout itself; the catalog's local source then resolves inside that same revision.

Codex can register a pinned Git marketplace:

```sh
codex plugin marketplace add LynxTWO/anti-dark-code-skill --ref v2026.09.27-unified.16
```

Install Anti-Dark-Code from that marketplace in the desktop app and test discovery
in a new chat. For a local test, `codex plugin marketplace add /path/to/checkout`
registers that checkout; registration alone is not installation or runtime proof.
The installed Codex skill is namespaced as `anti-dark-code:anti-dark-code`.

Claude Code can add the marketplace from a clean checkout of the reviewed tag:

```text
/plugin marketplace add /path/to/reviewed-checkout
/plugin install anti-dark-code@anti-dark-code
```

Gemini CLI can install that reviewed local checkout:

```sh
gemini extensions install /path/to/reviewed-checkout
```

Review each host's installation prompt. Installing a plugin does not approve any
subsequent repository edits, tool executions, or optional usage collection.

## Metadata and release checks

The next plugin update adds the Illuminated code logo and a simplified composer
icon. Their editable SVG sources and PNG exports live together in
`skills/anti-dark-code/assets/brand/`. The portable OpenAI overlay and Codex
fallback declare the same files; skill metadata uses skill-relative paths to
those assets. Published unified.16 and installations pinned to that tag retain
their original metadata until the next release is installed.

`VERSION` inside the core remains canonical. Plugin versions normalize numeric
calendar components to strict SemVer: `2026.09.15-unified.15` becomes
`2026.9.15-unified.15`. This is a representation change, not a second release.

Regenerate the six metadata files after changing VERSION or package metadata:

```sh
python3 -B skills/anti-dark-code/scripts/adc_packaging.py --repo . --write
python3 -B skills/anti-dark-code/scripts/adc_packaging.py --repo .
```

The default command is read-only. Add `--host-checks` to run available Claude,
Agent Skills reference and GitHub dry-run validators; missing tools are reported
as `capability_unavailable`. Failed available validators return a failure.
CI checks discovery, all declared metadata, and
the clean Git archive. `adc.py release-check --host-checks` can run those optional
validators on its extracted candidate. Release checking also checks manifests in the
tagged archive using the verifier's own code; it never executes scripts from the
tag being inspected. Historical standalone tags remain supported. Pure path moves
are distinguished from substantive reference changes so moving the tree cannot
hide an undocumented rule change.

Before a release, run the Windows/macOS/Linux suites, clean distribution check and
mutation replay on the final candidate. Rehearse a consumer install and upgrade
with `--expect-core-digest`, retaining that consumer's calibration. Run available
host checks, such as `claude plugin validate --strict .` and `skills-ref validate
skills/anti-dark-code`. Record an unavailable CLI as unavailable, not a passing
host test. Actual installation/discovery in each host is separate evidence from
JSON/schema validation.

Then complete the usual version/changelog/brief provenance updates and the tagged
`release-check` described in OPERATIONS.md. Publishing a tag, GitHub release or
skill-registry entry is a separate release action.

## Native host checks for unified.16

On macOS arm64, the unified.16 core installed through Codex CLI
0.158.0-alpha.2.1, Claude Code 2.1.283 and Gemini CLI 0.61.0. A fresh Codex
app-server `skills/list` returned the enabled plugin skill with no loader errors;
Gemini's `skills list` and `extensions list` found the enabled extension skill.
Claude's strict manifest validator and native plugin installation/listing passed.
These are installation and discovery observations, not model activation-rate or
task-quality measurements. Native host checks on Windows and Linux remain
unmeasured; cross-platform Python CI validates the core tools separately.

## Sources

- [Agent Plugins specification](https://agent-plugins.org/specification)
- [OpenAI plugin packaging and marketplaces](https://developers.openai.com/plugins/build/plugins)
- [Claude Code manifest reference](https://code.claude.com/docs/en/plugins-reference)
- [Gemini CLI extension reference](https://geminicli.com/docs/extensions/reference/)

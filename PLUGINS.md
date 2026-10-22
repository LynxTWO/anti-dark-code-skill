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

The existing marketplace identities now pin the published unified.22 commit,
independently of development on `main`. Historical catalogs used relative `./`,
which resolves inside that catalog's checkout. There is no duplicated core.
Metadata advertises a skill only: no MCP
server, credentials, automatic hooks, telemetry, or background jobs are enabled.
Existing optional collection commands still require their own explicit opt-in. Catalog fetch URLs are explicitly HTTPS, so updates do not depend on SSH host-key setup.

The host owns its plugin cache. Do not keep both a plugin-provided and a standalone
global copy enabled in one host after switching installation methods. Repository
calibration and an opted-in usage ledger are separate from that discovery choice.

## Install a reviewed package

The stable catalogs select published `v2026.10.18-unified.22` at immutable
commit `faeb00f996c87385d8339673b6a9cbb75549fa5c`. Verify its archive/digest
using the release instructions. Catalog updates and the plugin source they select
are separate: following `main` below refreshes the catalog, whose plugin source
stays pinned until a reviewed promotion.

### Claude desktop (chat / Cowork)

Claude plugins require a paid Claude plan (Pro, Max, Team or Enterprise),
according to [Anthropic's plugin help](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
A free desktop account cannot install this as a plugin. In a supported account:

1. Open **Customize > Plugins > Add > Add marketplace** (some app versions use
   **Settings > Plugins**).
2. Enter `https://github.com/LynxTWO/anti-dark-code-skill` and sync the repository.
3. Select **Anti-Dark-Code** and add/install it, then start a new conversation/task.

Use the repository root, not `skills/anti-dark-code/` or a `SKILL.md` URL.
For **Upload plugin**, use the release's `*-plugin-source.zip`, which contains
`.claude-plugin/plugin.json`. The `*-skill.zip` and Agensi core package are
standalone skills, not plugin ZIPs. A skill-only plugin is valid: it needs no
MCP server or automatic hooks. [Anthropic's plugin guide](https://claude.com/docs/plugins/overview)
describes repository sync, ZIP uploads and the supported surfaces. File access
and helper execution still depend on the host; chat installation alone does not
supply local repository access.

### Claude Code

Add the repository marketplace and install its named plugin:

```text
/plugin marketplace add https://github.com/LynxTWO/anti-dark-code-skill.git
/plugin install anti-dark-code@anti-dark-code
```

From a shell, use `claude plugin marketplace add <same-URL>` and
`claude plugin install anti-dark-code@anti-dark-code`. Start a new session or
run `/reload-plugins`. A CLI installation stays on that machine; it does not add
the plugin to your claude.ai account. A locally reviewed catalog checkout also
works with `/plugin marketplace add /path/to/reviewed-checkout`.

### Codex

Register the stable catalog:

```sh
codex plugin marketplace add https://github.com/LynxTWO/anti-dark-code-skill.git --ref main
```

Install Anti-Dark-Code from that marketplace in the desktop app and test discovery
in a new chat. For a local test, `codex plugin marketplace add /path/to/checkout`
registers that checkout; registration alone is not installation or runtime proof.
The installed Codex skill is namespaced as `anti-dark-code:anti-dark-code`.

### Other hosts and fixed historical catalogs

A marketplace registered at an older tag keeps that tag's catalog. In particular,
the immutable `.22` release archive was built before channel promotion, so its
embedded catalog still selects `.18`. Refresh/re-register the repository catalog
above to receive the promoted pin; the `.22` plugin itself is unchanged. The
metadata generator preserves historical catalogs when checking release archives.

Gemini CLI can install that reviewed local checkout:

```sh
gemini extensions install /path/to/reviewed-checkout
```

Review each host's installation prompt. Installing a plugin does not approve any
subsequent repository edits, tool executions, or optional usage collection.

## Metadata and release checks

Python 3.12 is the minimum for bundled helpers, not a required exact version;
newer compatible versions work without downgrading. The helpers can use a separate
Python installation or environment from a project running an older Python. Keep
the project’s own tests and tools on their required runtime.
CI targets every minor from 3.12 through 3.15 on Linux, plus 3.12 and 3.15 on
macOS and Windows. Check the run results for versions actually verified; a
configured matrix is not a passing result. Prefer an upstream-maintained Python
release; future versions need their own checks. Instructions alone need no Python.

Unified.17 adds the Illuminated code logo and a simplified composer
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

Both kits share one [opt-in preview catalog](https://github.com/LynxTWO/scaffold-kit/tree/main/preview), named `lynxtwo-preview`, with immutable candidate pins. Its instructions cover installation and rollback; keep one active copy per kit. Calendar versions remain canonical. A GitHub prerelease label does not control host updates: stable and preview catalogs select separate source commits.

## Release channels and promotion

The default catalogs select published unified.22; the shared preview catalog
selects unified.21. Check [GitHub Releases](https://github.com/LynxTWO/anti-dark-code-skill/releases)
for published versions. A newer source version does not promote either channel.

Publish a reviewed release with its tested ZIP, brief artifacts, checksums and
managed-core digest. Advance the stable catalogs in a separately reviewed
promotion, updating the metadata generator and its historical-release regressions
together. Verify stable-channel install, update and rollback against those final
pins. Keep existing preview archives intact.

Refresh Agensi's core ZIP through its required review before removing Preview
from its individual listing and bundle copy. Retain the documented buyer-delivery,
helper-execution and host-coverage limits. Publication, catalog promotion and
marketplace replacement each require owner authorization.

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

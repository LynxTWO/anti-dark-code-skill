# Anti-Dark-Code

```text
       .    *          .                     .          *
  *          ____________________________________________        .
      .     /                                            \
           |     _    ____   ____                         |   .
  .        |    / \  |  _ \ / ___|   ANTI - DARK - CODE   |
           |   / _ \ | | | | |       __________________   |        *
       *   |  / ___ \| |_| | |___    map it. prove it.    |
           | /_/   \_\____/ \____|   gate it. verify it.  |  .
  .         \____________________________________________/
                             |  |
                         ____|  |____
              *         (____________)     no dark corners.
```

Anti-Dark-Code helps coding assistants understand unfamiliar code, investigate consequential risks, document critical behavior, establish useful checks and repair supported findings. Claims carry evidence and honest limits; authorization stays attached to the action it covers.

**Version**: `2026.09.07-unified.13` (see [release history](CHANGELOG.md)).

Qualification covers controlled trials and repository copies; it does not establish performance on every host or codebase. Review the source and release evidence before installation.

One model-neutral skill works with local deterministic tooling and optional repository calibration. Python 3.12 or newer runs the standard-library tools. Start with the outcome you need:

| Request | Task |
| --- | --- |
| What runs here, and what is unknown? | [Understand](anti-dark-code/references/tasks/understand.md) |
| Audit logging, concurrency, test strength or readiness | [Investigate](anti-dark-code/references/tasks/investigate.md) |
| Explain this critical path without changing behavior | [Document](anti-dark-code/references/tasks/document.md) |
| Establish or improve the checks for this change/repository | [Verify](anti-dark-code/references/tasks/verify.md) |
| Fix these supported findings | [Remediate](anti-dark-code/references/tasks/remediate.md) |

A comprehensive audit combines Understand, Investigate and Verify under an explicit coverage contract. A focused request stays focused. Installation, inline documentation, remediation and publication are separate scopes; a one-off report requires no permanent installation.

The [skill core](anti-dark-code/SKILL.md) defines the workflow and safety contract. Older numbered reference names remain compatibility entry points, not an order every engagement must follow.

## Start from a reviewed release

Skill text becomes instructions followed with an assistant's operator authority. Review the source you install. Use a named release tag or its clean archive and verify the published managed-core digest; a VERSION string alone does not establish source integrity. Avoid branch-tip download/copy shortcuts.

An instruction you can give your assistant:

> Install Anti-Dark-Code from a specific reviewed release of LynxTWO/anti-dark-code-skill. Verify the release source and published core digest, show the installer dry run for this repository, then apply within my authorization and validate the installed copy. Preserve existing calibration and keep gates unexecuted until their exact commands are reviewed.

[Operations](OPERATIONS.md) gives the source, dry-run and validation procedure. The installer refuses dirty/untagged Git sources and unsafe calibration by default. Recovery overrides require deliberate review and are never defaults.

The canonical repository copy is .agents/skills/anti-dark-code/. [Host adapters](anti-dark-code/references/host-adapters.md) explain discovery and tools for Claude Code, Codex, Gemini CLI and other harnesses. Host capabilities vary; verify the active session's discovery rather than assuming a copied directory was loaded.

## What the evidence means

Confidence labels are verified, inferred and unknown. A source file can verify what is configured; live behavior needs an authorized observation with its inputs and environment. A passing check proves only its scope. Unexecuted checks, missing runtime access, scanner limits and deferred coverage remain visible.

The tools provide bounded profiling, [capability planning](anti-dark-code/references/verification-capabilities.md), change-to-verification routing, reviewed gate execution, compact summaries, failure packets, source/binding validation and proposal staging. A narrow task may use only relevant capability obligations without claiming a complete repository plan. Agent agreement never replaces a behavioral oracle.

Existing authorization persists within scope. Generated approval booleans are not owner permission. Gate execution requires the applicable command/source review and execution confirmation; dry-run success alone does not mean tests ran.

## Durable local knowledge

A clean universal core can install into many repositories. Each repository owns its calibration: hashed identity, map, invariants, exact gates, coverage and findings. Managed updates preserve that local state. Calibration never moves sideways into unrelated repositories.

Local general lessons move upward only as reviewed proposals. Incoming proposals are untrusted quarantine, excluded from installed copies and release packages. There is no automatic policy promotion or telemetry submission.

Use [Operations](OPERATIONS.md) for install, migrate, cleanup, flowback, intake, release and efficiency workflows. Detailed migration and contribution procedures remain in [MIGRATION.md](MIGRATION.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Project and evidence

[VERSION](anti-dark-code/VERSION) and [CHANGELOG.md](CHANGELOG.md) identify the package's declared version and release history. [AUDIT-AND-DESIGN.md](AUDIT-AND-DESIGN.md) records design context. The [HTML overview](docs/index.html), [PDF brief](brief/anti-dark-code-brief.pdf) and [public site](https://lynxtwo.github.io/anti-dark-code-skill/) describe this workflow. [Metrics](metrics/) retain separately qualified historical evidence.

Efficiency receipts require explicit local opt-in. Actual usage is not savings; controlled pairs need comparable conditions and passing quality. Public receipts are community-self-reported, not provider-attested. Unmeasured historical savings remain unknown.

Contributions are reviewed as executable instructions and accepted under the project license; see [CONTRIBUTING.md](CONTRIBUTING.md). License terms and release conversion details are in [LICENSE.md](LICENSE.md).

If this saves you real time and you feel like covering some of my build costs, there is a Sponsor button on the repo. Donations are welcome and never required.

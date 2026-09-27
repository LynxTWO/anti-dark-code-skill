# Steering files

Compatibility reference 01. Use with [Document](tasks/document.md) when creating or updating repository instructions; it is not a required first audit pass. Changes are limited to authorized steering files. Apply the [core contract](../SKILL.md).

## Inspect before writing

Read existing root and host instruction files, product principles, standing safety language, ownership records and relevant architecture/runbooks. Inspect languages, runtime units, package scripts, tests, CI, deployment, migrations, support tools and other live entry points. Include sibling repositories and external control surfaces when evidence shows a dependency. A bounded profile supplies inventory; source inspection supplies meaning.

For existing systems, name actual architecture, legacy rough edges and unknowns. For scaffolds, mark unimplemented areas TBD. Do not turn marketing, a directory name or a template into an implemented system. When language work matters, identify display strings, authoritative fields and protected saved prose.

Update the steering files the repository already uses. If none exists and creation is authorized, use root AGENTS.md unless another target was requested. Add host files only for actual discovery needs; keep shared policy aligned and intentional host differences in [adapters](host-adapters.md).

## Compact steering contract

Include these obligations, using links to existing detailed records instead of copying inventories:

- Purpose, repository profile, ownership, critical runtime units and sensitive data classes, all supported by evidence.
- Existing product promises, safety language and invariants preserved unless their change is authorized.
- Work boundaries: read-only inspection; documentation-only changes; behavior-preserving cleanup with touched-area baseline and regression evidence; feature/security work only within requested scope. These are permissions distinctions, not a numbered sequence that every task must traverse.
- Documentation-only work preserves application behavior, imports, dependencies, configuration and schemas. Treat shebangs, encoding markers, pragmas, lint directives, type-affecting docblocks, SQL hints and serialized metadata as behavior-sensitive.
- Large or mixed engagements maintain risk-ranked coverage slices and explicit examined, deferred, excluded and blocked obligations; link [coverage guidance](05-coverage-slicing.md). Full-coverage claims require matching evidence.
- Unknowns use existing repository locations or docs/unknowns/ and the [artifact fields](00-conventions.md). External control planes remain named uncertainties.
- Sensitive-data and protected-action rules link the core, with additional repository-specific protected boundaries supported by evidence. Preserve session authorization and its limits.
- Exact verification commands live in calibration or a repository-native equivalent. Use [Verify](tasks/verify.md) for capability selection, command review and execution evidence. No dependency installation or repository-code execution follows merely from a suggestion.
- Keep authoritative rules canonical across engines, views and adapters. Diagnostics remain observational unless a different role is explicitly designed and authorized.

## Change and review expectations

Non-trivial changes explain what changed and why, behavioral evidence, relevant privacy/observability impact, failure or rollback handling, and affected documentation. Update subsystem manifests, contracts, architecture, runbooks or release/control-plane notes where relevant. Language changes name their truth and persistence boundary.

For consequential changes separate builder and challenger responsibilities; deterministic checks settle mechanical claims. A verifier does not edit what it grades. Review skipped cases, removed assertions, widened mocks, timeout increases, reduced coverage/mutation strength and snapshot changes against the intended behavior contract.

Use plain, short, active prose and ASCII punctuation in newly authored technical text; honor repository banned terms and mature style. Follow [writing guidance](06-writing-hygiene.md) without rewriting protected authored text.

## Result and stop

Deliver a compact Markdown diff with evidence-backed repository facts and links to detailed records. Close out with changes, unknowns, privacy/observability impact, documentation, approvals used or pending and follow-up work. Stop a proposed edit that changes product promises, protected behavior or sensitive directives outside authorization. Do not invent facts to fill a required heading.

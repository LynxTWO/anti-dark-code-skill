# Understand

Use for repo maps, unfamiliar architecture, ownership, or a comprehensive audit's mapping portion. The [core](../../SKILL.md) supplies evidence and authority rules.

## Inputs

Requested scope, repo instructions, relevant maps and calibration, source identity, changed paths, manifests, and runtime entry points. A focused question needs only the relevant subsystem; whole-repo work needs an inventory and explicit exclusions.

## Procedure

1. Check existing evidence and invalidation dependencies. Reuse unchanged observations; inspect changed boundaries. For non-Git directories without a cheap identity, record hashes of inspected files instead of declaring prior evidence fresh.
2. Use the trusted read-only probe when available and useful. Its summary identifies indicators, not complete architecture. Inspect scan bounds, ignored trees, requested exclusions, nested repositories, and unknowns before interpreting negative signals. If unavailable, enumerate manifests and entry points manually and name the missing machine checks.
3. Follow each in-scope entry point through authoritative state, transformations, persistence, external calls, and output. Separate runtime, deployment, and ownership boundaries. Shared language does not prove shared runtime or deployment.
4. Mark generated, vendored, mirrored, serialized, and binary surfaces. They remain dependencies or runtime inputs even when excluded from inline review. Inspect representative owned source for each boundary; directory names alone cannot establish behavior.
5. Load [architecture](../02-architecture-map.md) for runtime or trust-boundary mapping. Load [coverage and slicing](../05-coverage-slicing.md) for multiple runtimes or work exceeding the remaining budget. Load [language boundaries](../12-transcreation-boundary.md) for locale or saved user text. Load no specialist solely because it exists.
6. Trace scripts, CI, notebooks, support tools, feature flags, remote configuration, and sibling repositories when evidence shows they affect the path. Separate visible configuration from unobserved external state. A README cannot establish what production runs.

## Evidence and output

Return the requested map with source locators, runtime units, entry points, trust and data boundaries, owners or unknown owners, and external dependencies. For multiple surfaces, include surface, inspected evidence, coverage disposition, unresolved boundary, and next check. Preserve existing stored statuses when updating calibration.

A focused task delivers its relevant map fragment and limitations. A comprehensive audit uses the inventory as its coverage contract for Investigate and Verify. Explicitly name excluded and blocked areas. A five-file map cannot establish broader repository coverage without an inventory and exclusions.

Do not install calibration or create steering files merely to finish a map. If requested, use the corresponding operator reference while preserving shared-core versus repo-owned knowledge.

## Stop conditions

Stop the affected branch when proof depends on inaccessible external state, source contradicts the map, or further coverage exceeds authorization. Record the smallest discriminating check and continue independent visible surfaces. Contradictions invalidate dependent conclusions; they do not authorize repairing the subject. Completion is limited to the declared inventory and examined paths; unknown deployment state remains unknown.

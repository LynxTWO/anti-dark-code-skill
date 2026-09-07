# Generic harness adapter

Use when the active harness needs an explicit mapping to the universal skill. The [core contract](../SKILL.md) is authoritative; no host fallback creates a weaker policy.

## Discovery and tools

If automatic skill discovery is unavailable, add an authorized short pointer to the host's existing instruction file. Point to the universal SKILL.md and this repository's calibration/; do not copy the full policy into another file.

Inspect and record the host's actual read, search, edit and process capabilities. Map those operations to the active task. Deterministic commands stay in scripts/adc.py or reviewed repository-native tools. Do not invent executable tool names, model controls or permission mechanisms.

Batch independent read operations where supported; serialize dependency chains, approvals and mutable shared-output work. If the harness cannot execute commands, produce their exact proposed argv/cwd and expected evidence, and mark unobserved behavior inferred or unknown. A human's authenticated result may supply observation evidence later.

## Model and recovery limits

Use subagents only where available and authorized by active instructions. Otherwise run the bounded work inline with builder/challenger separation as independent review steps where needed. Choose only model/effort controls actually exposed by the harness, within user constraints.

Saved artifacts, checkpoints, run IDs and cache recovery have host-specific semantics. Establish those semantics before relying on them. Verify source identity, provenance and invalidation dependencies before reusing a result; inspect an interrupted operation before retrying it. Neither a transcript nor several agreeing agents authenticates a behavioral guarantee.

Do not promise free replay or a recoverable in-flight call. Preserve useful checkpoints even when the host has no resumability feature.

## Optional usage mapping

Record only numeric counters whose provider/host semantics are documented. Leave missing values null and preserve reported zero. UI estimates and quota percentages are not actual usage. Pin the adapter version and usage contract; unknown normalization prevents a comparable pair.

Apply [efficiency guidance](16-community-feedback-and-efficiency.md) for explicit opt-in, private receipts, quality qualification and public evidence limits. Tool limitations belong in the task report, not in fabricated coverage.

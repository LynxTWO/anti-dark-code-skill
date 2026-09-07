# Assurance and boundary contracts

Use this index only to select a recipe matching the active claim. Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). These recipes do not grant permission to execute, mutate, publish or cross a protected boundary.

## Claim-kind routing

- `source_fact`: a scoped fact about inspected source/artifacts. A locator and source identity can verify that fact.
- `configured_behavior`: what configuration requests or enables. Reading it can verify configuration, while live enforcement stays unobserved.
- `observed_behavior`: what an authorized run demonstrated for recorded inputs, environment, source and scope. Report missed branches and finalization boundaries.
- `guarantee`: a broader assurance such as atomic, isolated, bit-exact, repaired, compatible, available or release-ready. **Load the matching recipe before accepting the claim.** Use an independent falsifier and retain every unmet obligation.

Confidence remains exactly `verified`, `inferred`, `unknown`. Claim kinds are a reporting/proof distinction, not permission to change stored schemas or reinterpret prior calibration. The word `verified` on a file fact does not trigger every assurance checklist. A successful write, configuration readback, green job or agent vote cannot establish a broader guarantee by itself.

## Select only the triggered recipes

| Observable claim boundary | Recipe and required result |
|---|---|
| Output identity, isolation, recovery activation or review closure | [Claim proof](assurance-claim-proof.md): independent falsifier, exact object scope, finalization and branch activation evidence. |
| Device capability, calibration, cache/reread or nested recovery | [Hardware recovery](assurance-hardware-recovery.md): physical identity, exact command shape, phase roles and real operating-range evidence. |
| Repair/import/migration, concurrency, atomic output or preservation | [Preservation](assurance-preservation.md): coordination domain, owned stage, independent reopen, commit point and failure/cancellation/contention evidence. |
| Subprocess, redistributed executable or native ABI | [Native execution](assurance-native-execution.md): bounded termination, exact executable/ABI tuple and staged-host real work. |
| Native/dynamic availability or dead-code claim | [Reachability](specialist-native-reachability.md): complete graph/target chain, with configuration separated from observed invocation. |
| Dependency/build/signing/SBOM/release closure | [Release closure](assurance-release-closure.md): exact source/dependency/artifact sets and final byte receipts. |
| Approved work becomes executable or published | [Publication integrity](assurance-publication-integrity.md): compare against actual approved authority and reproduce receipt algorithm/normalization. |
| Compatibility, UI result, streaming, external input or hot path | [Runtime boundaries](assurance-runtime-boundaries.md): stable selected identity, bounded immutable inputs, actual final outcomes and budgets. |
| Gate joins an audited evidence family | [Audited producer](specialist-audited-producers.md): audit validation, invalidation, lease and publication canon in the same change. |

A claim crossing multiple listed boundaries needs each matching recipe. Stop at the first missing proof, identify its impact and next check, and keep broader confidence limited. Evidence from one platform, branch or output shape does not transfer automatically to another.

# Native and dynamic reachability

Trigger: a finding calls a module, plugin, codec, binary, model, or optional feature reachable, dead, unavailable, or a build blocker; or a handoff claims a physical client can open a server-backed live target for review.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Name the graph before calling a project, library, module, plugin, codec, binary, model, or optional feature referenced, unreferenced, reachable, imported, or dead:

- solution or workspace membership, including configuration and architecture mappings
- static project, package, module, or source references
- dynamic discovery through registries, reflection, manifests, dependency injection, or directory scans
- copy, package, publish, deployment, or release rules
- runtime native-library, external-process, driver, model, asset, or SDK dependencies

A node outside one graph may remain live through another. Do not infer a build blocker merely because a generated binary is absent from a clean checkout. Trace its source, build target, pinned dependency, preparation step, expected output, and packaging consumer.

## End-to-end reachability proof

Trace every applicable link before assigning a terminal reachability label:

1. implementation source and language or native boundary, including candidate-file and finding counts for negative searches
2. build target, configuration, framework, and architecture mapping
3. copy, package, publish, or deployment rule
4. discovery, registration, reflection, manifest, or loader path
5. native library, external process, driver, model, asset, or SDK dependency and expected location
6. default and user-controlled enablement or selection
7. invocation from a real entrypoint
8. observed build, package, load, selection, and invocation for the exact target tuple

Stop at the first broken or unproven link and name it. Text can prove configuration, but a behavioral reachability claim remains `inferred` until observed. Failure in one target tuple does not prove the feature unreachable in every supported tuple.

Use these terminal descriptions:

- `reachable-observed` - every applicable link, including link 8, was observed for the named tuple
- `configured-not-observed` - links 1 through 7 are evidenced, but link 8 was not observed
- `blocked-at-link-N` - a required link is proven absent or failed for the named tuple
- `unknown-at-link-N` - evidence for the link was unavailable
- `not-applicable` - the link genuinely does not apply; state why

For platform or architecture branches, inspect every else branch for assumptions about an unlisted third target. Distinguish a portable fallback from a sibling-specific capability. Name built/tested targets; unlisted targets must refuse unsupported operations and report unavailable observations honestly. A generated binary absent from a clean checkout is not by itself a build blocker.

## Physical-client handoff

When a handoff claims a physical client can open a server-backed live target,
separate these observations:

1. The server exposes the expected listener, manifest or bundle for the candidate.
2. The client acquires the exact current endpoint through its supported mechanism,
   such as a QR code, deep link or manual entry. Generating a link or QR code alone
   does not show that the client received it.
3. On the named device, the client opens the intended initial route and shows a
   candidate-bound identity marker, or equivalent evidence that rules out a stale
   build or a different target. An HTTP 200 alone does not identify the target.

Record the device/client, candidate identity, transfer method, observed route and
observation time in the existing verification record. Use redacted endpoint
identifiers; do not retain credential-bearing URLs or QR codes as public evidence.

Server checks cannot substitute for the client observation. A browser or emulator
run proves only that tested scope. If the physical client cannot be observed,
keep its result `configured-not-observed` or `unknown-at-link-8`, as supported by
the evidence; do not report that handoff READY. Preserve the separately proven
server result. A client failure does not erase a valid server-only check.

Apply this requirement only to a physical-client handoff claim. Server-only work
does not require a device, and a successful initial opening does not prove other
routes, account flows or full product readiness. Offline or standalone targets
use the applicable reachability links above, without an endpoint-transfer step.
Existing authorization still
governs endpoint transfer and device interaction.

For native ABI or staged-host assurance use [native execution](assurance-native-execution.md).

Result: one terminal description per exact target tuple, backed by the named graph and first unproven or failed link. Static configuration is `configured_behavior`; observed invocation is `observed_behavior`; a broader `guarantee` loads its matching assurance recipe.

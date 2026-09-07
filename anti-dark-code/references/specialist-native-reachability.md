# Native and dynamic reachability

Trigger: a finding calls a module, plugin, codec, binary, model, or optional feature reachable, dead, unavailable, or a build blocker.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Name the graph before calling a project, library, module, plugin, codec, binary, model, or optional feature referenced, unreferenced, reachable, imported, or dead:

- solution or workspace membership, including configuration and architecture mappings
- static project, package, module, or source references
- dynamic discovery through registries, reflection, manifests, dependency injection, or directory scans
- copy, package, publish, deployment, or release rules
- runtime native-library, external-process, driver, model, asset, or SDK dependencies

A node outside one graph may remain live through another. Do not infer a build blocker merely because a generated binary is absent from a clean checkout. Trace its source, build target, pinned dependency, preparation step, expected output, and packaging consumer.

#### End-to-end reachability proof

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

For native ABI or staged-host assurance use [native execution](assurance-native-execution.md).

Result: one terminal description per exact target tuple, backed by the named graph and first unproven or failed link. Static configuration is `configured_behavior`; observed invocation is `observed_behavior`; a broader `guarantee` loads its matching assurance recipe.

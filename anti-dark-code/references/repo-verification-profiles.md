# Reference: Repo Verification Profiles

Use this reference after the deterministic repo probe. A mixed repo combines profiles by runtime unit rather than forcing one generic plan across everything.

## Service or Web Backend

Prioritize:

- V03 invariants around transactions, authorization, idempotency, and state changes
- V08 request, event, config, and persistence contracts
- V09 boundaries between transport, domain, persistence, and privileged jobs
- V15 timeouts, duplicate delivery, partial writes, dependency failure, and retry storms
- V07 replay for request or event sequences
- V12 hermetic service substitutes and fixed timezones
- V14 latency, queue, connection, and memory budgets

Repo-fit adaptations:

- Model-based tests should cover account, order, billing, deletion, and permission state machines.
- Differential tests fit API migrations, old versus new handlers, and database adapter rewrites.
- Metamorphic tests fit idempotency, retry, pagination, ordering, and batch-size relations.
- Never run fault injection against production without explicit approval and isolation.

## Frontend or Browser App

Prioritize:

- V02 stateful navigation and interaction models while retaining a random UI monkey
- V03 UI and state-store invariants
- V07 seed and action replay for crashes or visual leaks
- V08 API, storage, route, and feature-flag contracts
- V13 semantic DOM, view-model, and selective screenshot goldens
- V14 render counts, bundle size, detached nodes, listeners, and long-session memory
- V15 offline, storage quota, tab suspension, stale cache, and slow network faults

Repo-fit adaptations:

- Architecture rules should keep UI from importing private persistence or domain internals.
- Test-change policing should flag broad component mocks and unexplained snapshot updates.
- A state selector that creates fresh nested objects can create render loops even when unit tests are green. Add identity and render-count guards where the framework needs them.

## Monorepo

Prioritize:

- V09 package and layer boundaries
- V11 dependency and ownership based change impact
- V12 hermetic package builds and cache keys
- V16 generated package, runtime, and ownership maps
- V20 package-aware confidence ladders
- V10 one compact root verdict with per-package logs

Repo-fit adaptations:

- Do not claim repo-wide coverage from one package.
- Differential testing fits shared-library migrations and duplicated implementations.
- Mutation and property tests should run only on affected high-risk packages.
- Track external sibling repos and vendor control planes as unknown boundaries.

## Library or SDK

Prioritize:

- V08 public API, serialization, and compatibility contracts
- V04 reference versus optimized and old versus new behavior
- V01 mutation testing for public behavior
- V05 algebraic and metamorphic properties
- V12 cross-version and cross-platform hermetic matrices
- V13 normalized API and generated-artifact goldens

Repo-fit adaptations:

- Architecture rules should separate public API from internals.
- Change impact includes downstream examples, compatibility fixtures, and generated clients.
- Test-change policing should flag removed compatibility cases and silent baseline re-recording.

## Game or Simulation

Prioritize:

- V06 seeded time, RNG, ids, locale, and content identity
- V07 world seed, starting save, action trace, and receipt replay
- V02 random, stateful, and adversarial monkeys
- V03 impossible-state and economy invariants
- V05 chunking, ordering, scaling, resistance, conservation, and save-load relations
- V13 replay, save, map, content, and receipt goldens
- V14 frame, tick, queue, memory, listener, and long-session budgets
- V15 interrupted save, missing asset, worker death, tab suspension, and storage faults

Repo-fit adaptations:

- Keep diagnostics observational. The engine must not read the flight recorder.
- A targeted green battery is not a green world. Keep at least one fixed-seed aggregate canary for action, economy, difficulty, or population distributions.
- Isolate emergent regressions with an output-counting probe, parent-commit diff, and one-config-at-a-time unwiring.
- Projection code should import canonical engine rules rather than re-implementing them.

## Mobile or Native App

Prioritize:

- V02 permission, lifecycle, navigation, offline, and background state machines
- V08 native bridge, storage, push, deep-link, and platform contracts
- V12 device, OS, locale, and build-toolchain isolation
- V15 interruption, low storage, background kill, permission denial, and network change
- V14 startup, frame, battery, memory, bridge, and background budgets
- V07 replayable lifecycle and navigation traces

Repo-fit adaptations:

- Architecture enforcement should block UI or shared code from bypassing secure storage and bridge validation.
- Differential tests fit native versus web or iOS versus Android adapters.
- Full matrices belong at Level 3, not every edit.

## Infrastructure as Code

Prioritize:

- V08 module, variable, policy, and state contracts
- V09 IAM, module, environment, and runner boundaries
- V04 current plan versus intended or previous plan
- V11 environment and module impact
- V12 pinned providers, modules, and isolated test state
- V13 normalized plan or policy goldens
- V15 only in disposable sandboxes

Repo-fit adaptations:

- A plan can be evidence. An apply is a protected action.
- Never treat local reading as proof of remote state.
- Failure packets should redact account ids, secrets, and sensitive addresses.
- Test-change policing should flag policy suppressions and widened exceptions.

## AI or Data System

Prioritize:

- V08 data, feature, prompt, tool, and model-output contracts
- V04 old versus new pipeline, model, route, or feature behavior
- V05 row-order, batch-size, partition, scaling, and paraphrase relations
- V12 pinned data snapshots, model versions, locales, and environments
- V13 eval sets, normalized outputs, reports, and lineage goldens
- V14 cost, latency, memory, throughput, and drift budgets
- V15 missing partitions, malformed rows, service timeouts, and partial backfills

Repo-fit adaptations:

- Separate deterministic pipeline correctness from probabilistic quality evaluation.
- Record model, prompt, tool schema, dataset, and route versions in replay identity.
- Do not log raw sensitive prompts or responses merely to make debugging easier.
- A model vote is not ground truth when a deterministic contract can settle the claim.

## CLI or Desktop Application

Prioritize:

- V08 command, file, config, IPC, and exit-code contracts
- V02 command and UI workflow state machines
- V07 command sequence and fixture replay
- V12 temp directories, home folders, locales, terminals, and OS matrices
- V13 normalized stdout, file, migration, and UI-tree goldens
- V15 missing permissions, locked files, full disks, interrupted writes, and child-process failure
- V14 startup, memory, file handle, and long-session budgets

Repo-fit adaptations:

- Failure packets must preserve the real exit code and command arguments after redaction.
- Differential tests fit legacy versus new file formats and platform adapters.
- Keep shell-specific behavior isolated and tested per supported platform.

## Small or New Repo

Start light:

- V03 a few real invariants
- V08 boundary schemas
- V10 exact quality gate
- V16 compact project map
- V18 test-change rules
- V19 failure packet
- V20 two or three practical levels

Add the other capabilities when architecture and risk make them real. Do not preinstall a laboratory the project does not yet need.

## Cross-Profile Rules

- V17 role separation scales with risk, not repo size alone.
- V01 requires meaningful tests first.
- V04 needs two implementations or a reference oracle.
- V06 and V07 become high value whenever time, randomness, ordering, or intermittent behavior exists.
- V11 must include non-import edges such as schemas, configs, content packs, generated files, deploy paths, and control planes.
- V13 snapshots must be semantic and reviewed.
- V15 must remain isolated and approval-aware.

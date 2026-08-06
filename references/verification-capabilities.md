# Reference: The 20 Verification Capabilities

This catalog is the conceptual source for `assets/verification-capabilities.json`. Evaluate every capability, but select only what repo evidence and change risk justify.

## V01 Mutation Testing

**Catches:** tests that execute code without protecting behavior.

**Computer work:** change operators, branches, constants, and return values; rerun affected tests; report surviving mutants.

**Agent work:** choose high-value modules, interpret equivalent mutants, and improve behavior-focused tests.

**Use when:** meaningful tests already exist, the module carries important rules, or AI wrote both code and tests.

**Avoid:** full-repo mutation on every edit, mutation of generated code, or treating mutation score as product correctness.

## V02 Model-Based Stateful Testing

**Catches:** invalid transitions, sequence bugs, workflow dead ends, and failures random clicking rarely reaches deliberately.

**Computer work:** generate action sequences from a state model, execute them, check invariants, shrink failing sequences, and retain seeds.

**Agent work:** define legal actions, preconditions, state abstractions, and meaningful invariants.

**Use when:** the repo has workflows, UI state, games, transactions, permissions, lifecycle transitions, or multi-step protocols.

**Adaptation:** keep the dumb random monkey. Add a stateful monkey that knows legal transitions and an adversarial monkey that targets risky boundaries.

## V03 Executable Invariants

**Catches:** impossible states near the point they are created.

**Computer work:** assert constraints at mutation, serialization, transaction, event, and trust boundaries.

**Agent work:** identify load-bearing truths and decide where a failed invariant should stop, quarantine, or recover.

**Use when:** almost always for non-trivial stateful code.

**Avoid:** assertions that merely restate types, leak secrets, or crash production without a deliberate policy.

## V04 Differential Testing

**Catches:** divergence between implementations that should agree.

**Computer work:** run old versus new, simple versus optimized, server versus client, native versus web, CPU versus GPU, or reference versus production and diff outputs.

**Agent work:** define equivalence, normalize irrelevant differences, and choose the boring reference oracle.

**Use when:** there are parallel implementations, migrations, rewrites, optimizations, compatibility layers, or projections.

**Avoid:** comparing two copies that share the same bug and calling agreement proof.

## V05 Metamorphic Testing

**Catches:** wrong relationships when an exact expected output is difficult to author.

**Computer work:** transform inputs and verify a required relation between outputs.

**Agent work:** define valid transformations and relations.

**Use when:** generators, search, simulation, numerical code, AI or data pipelines, chunking, batching, sorting, scaling, localization, or configuration make exact oracles hard.

**Examples:** save then load preserves state; splitting one time window into equivalent chunks preserves results; adding resistance cannot increase matching damage; reordering independent inputs does not change the result.

## V06 Deterministic Execution Mode

**Catches:** unreplayable failures and hidden dependence on time, randomness, environment, locale, or ordering.

**Computer work:** inject clocks, seeded RNG, stable ids, fixed locale and timezone, captured config, and explicit starting state.

**Agent work:** define which inputs belong in the replay identity and where nondeterminism is intentional.

**Use when:** the repo touches randomness, time, concurrency, simulation, generated content, retries, or distributed ordering.

**Avoid:** pretending every concurrent system can be perfectly deterministic. Capture schedules or bound the claim honestly.

## V07 Record and Replay Regression Corpus

**Catches:** recurrence of failures found by fuzzing, UI exploration, production diagnostics, or manual testing.

**Computer work:** save seed, initial state, action trace, version, and minimized reproducer; replay it in gates.

**Agent work:** decide what becomes a permanent regression and redact sensitive state.

**Use when:** the system has workflows, user interactions, simulations, parsers, protocols, or intermittent failures.

**Rule:** a monkey without replay creates anecdotes. A monkey with replay builds institutional memory.

## V08 Schema and Contract Validation

**Catches:** malformed data before it travels through several subsystems.

**Computer work:** validate API payloads, events, configs, saves, messages, generated content, and environment variables at boundaries.

**Agent work:** decide ownership, compatibility, defaults, migrations, and failure policy.

**Use when:** almost every repo that reads external, persisted, generated, or cross-process data.

**Rule:** parse at the boundary, trust the validated shape inside.

## V09 Static Architecture Enforcement

**Catches:** forbidden imports, cycles, layer violations, direct clock or network access, private API reach-through, and dependency-direction drift.

**Computer work:** dependency graphs, AST rules, import restrictions, ownership checks, and exception expiry.

**Agent work:** define the intended layers and review whether an exception is real debt or a wrong rule.

**Use when:** more than one layer, package, runtime, or trust boundary exists.

**Avoid:** permanent blanket exemptions. Name and track each exception.

## V10 Deterministic Quality Gate

**Catches:** changes that fail known checks and inconsistent agent verification habits.

**Computer work:** run exact reviewed commands, capture real exit codes, save logs, and return a compact verdict.

**Agent work:** choose the gate set and interpret failures that require judgment.

**Use when:** every maintained repo.

**Rule:** successful checks collapse. Failed checks expand only enough to act.

## V11 Change-Impact Analysis

**Catches:** both under-testing and wasteful full-suite execution.

**Computer work:** map changed files through imports, ownership, coverage, schemas, events, and gate globs to affected checks.

**Agent work:** add semantic edges the static graph cannot see, such as shared config or live control planes.

**Use when:** medium or large repos, monorepos, slow suites, or expensive hardware gates.

**Avoid:** assuming import graphs capture data, configuration, deployment, or generated-code dependencies.

## V12 Hermetic Builds and Tests

**Catches:** machine-specific, cache-specific, timezone, locale, network, and undeclared-input failures.

**Computer work:** pin dependencies and toolchains, isolate temp directories, fix locale and timezone, mock networks, clean builds, and compare outputs.

**Agent work:** identify intentional external dependencies and define a usable local substitute.

**Use when:** CI, releases, code generation, native builds, data pipelines, or cross-platform behavior matters.

**Avoid:** claiming hermeticity while hidden downloads, home-directory files, or mutable service state remain.

## V13 Golden and Semantic Snapshot Testing

**Catches:** drift in complex serialized, generated, rendered, migrated, or compiled output.

**Computer work:** compare normalized artifacts to reviewed baselines.

**Agent work:** decide which fields are semantic, review diffs, and reject blind baseline updates.

**Use when:** save formats, API schemas, generated maps, render trees, transcripts, migrations, compilers, reports, or deterministic simulations exist.

**Avoid:** giant noisy snapshots that reviewers approve without understanding.

## V14 Performance and Leak Budgets

**Catches:** correct code that slowly becomes unusable.

**Computer work:** measure latency, throughput, memory, listener counts, queue depth, render count, bundle size, and resource growth against baselines.

**Agent work:** choose user-relevant budgets and distinguish noise from regression.

**Use when:** long-running processes, UI rendering, games, services, mobile apps, data jobs, or constrained devices matter.

**Rule:** a performance claim needs a baseline, workload, and budget.

## V15 Fault Injection

**Catches:** failures caused by the environment rather than the input value.

**Computer work:** simulate timeouts, duplicate events, missing events, partial writes, storage exhaustion, worker death, clock shifts, tab suspension, unavailable services, and interrupted migrations.

**Agent work:** choose realistic faults and acceptable recovery behavior.

**Use when:** persistence, networks, queues, retries, background work, workers, caches, or external services exist.

**Avoid:** destructive testing against live systems without explicit approval and isolation.

## V16 Authoritative Project Map

**Catches:** agents repeatedly rediscovering or misremembering repo shape.

**Computer work:** generate compact manifests, language counts, entrypoint candidates, dependency summaries, test maps, and freshness hashes.

**Agent work:** explain runtime purpose, trust, ownership, rule authority, and external boundaries.

**Use when:** every repo beyond a tiny scaffold.

**Rule:** generate facts where possible. Hand-maintain only meaning the computer cannot derive.

## V17 Separated Builder, Challenger, and Verifier Roles

**Catches:** one agent defining the requirement, writing the code, writing the tests, and grading itself.

**Computer work:** enforce workflow stages and gate results.

**Agent work:** builder implements, challenger attacks assumptions, verifier reviews evidence without editing.

**Use when:** medium or high-risk changes, unfamiliar code, or AI-authored tests.

**Avoid:** spending three agents on a trivial formatting change. Scale separation to stakes.

## V18 Test-Change Policing

**Catches:** fixes that weaken the test instead of correcting the code.

**Computer work:** flag skipped tests, deleted assertions, snapshot updates, timeout increases, broad mocks, coverage drops, mutation-score drops, and production-plus-test changes.

**Agent work:** decide whether the requirement legitimately changed.

**Use when:** any agent may edit tests.

**Rule:** test changes are allowed, but they must explain which behavior contract changed.

## V19 Minimal Failure Packets

**Catches:** token waste and diagnosis drift caused by giant logs.

**Computer work:** emit failure id, first bad event, violated invariant, expected versus actual, command, exit code, seed, version, affected files, replay command, and full-log path.

**Agent work:** read the packet, request only the missing source slice, and decide the next experiment.

**Use when:** every automated gate or exploratory runner.

**Avoid:** placing secrets, raw personal data, or entire state dumps in the packet.

## V20 Confidence Ladder

**Catches:** slow edit loops and risky merges caused by one undifferentiated gate set.

**Computer work:** run Level 0 through Level 3 checks according to change impact and risk.

**Agent work:** assign and revise levels from measured runtime, failure history, and blast radius.

**Use when:** every repo with more than one check.

**Rule:** cheap blockers run first. Expensive checks run only when the change survives and risk justifies them.

## Selection Summary

The planner should normally select a core of V03, V08, V09, V10, V11, V16, V17, V18, V19, and V20 for a non-trivial maintained repo, then conditionally add the rest. It may defer or mark a core capability not applicable when repo evidence provides a real reason.

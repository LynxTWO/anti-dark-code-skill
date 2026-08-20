# Reference: Deterministic Verification Planner

Use this pass to make the local computer perform every safe, exact verification task it can, while reserving agent tokens for judgment.

**Mode:** planning and harness work by default. Gate execution requires explicit permission and the repo's normal safety rules.

## Important Distinction

The 20 items in this system are verification capabilities, not 20 tests that every repo should run.

Some are test techniques. Some are architecture controls, execution controls, evidence packaging, or review separation. Evaluate all 20 for every repo, then mark each one:

- `selected` - evidence shows it belongs now
- `candidate` - useful if a named condition is confirmed
- `deferred` - useful later, with a reason and trigger
- `not_applicable` - current repo evidence does not support it

Blindly installing every technique would waste machine time, dependencies, and developer attention. The planner's job is to choose the smallest defensible verification set.

## Inputs

Read:

- `calibration/repo-profile.json`, or generate it with `adc.py probe`
- `calibration/invariants.md`
- `calibration/system-map.md`
- package scripts, CI workflows, test configs, and architecture rules
- recent changed files or the planned slice
- `assets/verification-capabilities.json`
- `references/repo-verification-profiles.md`

## Step 1: Generate a Deterministic Repo Profile

```bash
python .agents/skills/anti-dark-code/scripts/adc.py probe --repo . --write
```

The probe reads file names, manifests, selected small configuration files, and bounded code indicators. It does not execute application code. It records evidence paths and scan limits so the result does not pretend to be a full architecture review. It excludes host skill trees under `.agents/skills/`, `.claude/skills/`, `.gemini/skills/`, and `.codex/skills/` so tooling does not pollute product-code classification or evidence.

## Step 2: Evaluate All 20 Capabilities

```bash
python .agents/skills/anti-dark-code/scripts/adc.py plan --repo . --write
```

The planner must produce one row for every capability, including a reason, evidence, confidence-ladder level, local deterministic work, and the remaining agent judgment.

Do not install dependencies from the plan. A tool suggestion is not approval to add it.

## Step 3: Build a Confidence Ladder

Use four levels so fast feedback stays fast.

### Level 0: every meaningful edit

Prefer checks measured in seconds:

- formatting or format check
- affected type check
- affected lint
- schema and policy checks
- static architecture rules
- generated-file drift checks

### Level 1: completed task or bounded slice

Run:

- affected unit and contract tests
- focused integration tests
- relevant replay regressions
- boundary and invariant checks

### Level 2: before merge or for elevated risk

Run selected:

- property and metamorphic tests
- short fuzz campaigns
- short random or model-based UI exploration
- changed-module mutation tests
- performance smoke checks
- targeted fault injection

### Level 3: scheduled, release, or high-risk change

Run selected:

- full suite
- long fuzz or monkey campaigns
- full or broad mutation testing
- memory and leak soak
- save or schema migration matrix
- cross-platform matrix
- long statistical canaries
- broader fault injection

A repo may move one capability up or down a level based on measured cost and risk. Record why.

## Step 4: Configure Exact Gates

Store reviewed commands as argument arrays in `calibration/gates.json`. Do not store vague prose such as "run the tests."

Good gate entry:

```json
{
  "id": "typecheck",
  "level": 0,
  "argv": ["npm", "run", "typecheck"],
  "enabled": true,
  "review_status": "approved",
  "source": "package.json#scripts.typecheck",
  "source_definition_sha256": "<hash captured by the deterministic probe>",
  "inherit_env": true,
  "env": {"DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
  "timeout_seconds": 180,
  "include_globs": ["src/**/*.ts", "src/**/*.tsx"],
  "resource_class": "light"
}
```

Use `include_globs` and `exclude_globs` for change impact. Keep full-suite and soak gates marked heavy. Record hardware restrictions, remote runners, and commands that reach external systems.

Never put secrets in command arguments or failure packets.

`inherit_env` defaults to `true`. Set it to `false` only when the command has been proven to run in a deliberately sparse environment. The optional `env` object accepts a bounded set of reviewed, non-sensitive string overrides; secret-like variable names are refused. Run artifacts record the overlay key names and an opaque fingerprint of execution-relevant environment state, never the raw overlay values. If a child prints an overlay value, the retained log replaces that literal value before preservation.

### Capability-restricting build flags

A build flag chosen for release can remove a runtime capability from every build, including builds that never ship. The code still compiles, so the loss surfaces only when a dependent line executes.

Verified case: an ahead-of-time-compilation opt-in, set for the shipped target, also wrote a reflection-disabled feature switch into the debug runtime configuration, and reflection-based serialization then threw in ordinary debug runs. Three separate code paths failed on that one flag within two days of adoption, each surfaced by a live run rather than a build error, the last one inside a commit path. The test host did not carry the switch, so no gate could reproduce any of the three.

Treat a capability-restricting build flag as a repo-wide change, not a release setting. When one is adopted or changed:

- name the restricted capability and the exact switch that carries it, read from the generated runtime or build configuration rather than from the flag's documentation
- check whether the test and tooling hosts run under that same switch; a gate running in the permissive mode cannot fail on the restriction
- run a one-shot deterministic sweep for every use of that capability across source, test, and script trees, and confirm the sweep separates the restricted form from the safe form before trusting its count
- migrate every site the sweep found, then add a Level 0 gate that fails when an unmigrated site reappears
- either run the selected gates in the same capability mode as the shipped artifact, or adopt the restricted mode as the baseline for every build and every target that shares the code

The second option is not free. Restricted modes often disable the dynamic-code features that debuggers, hot reload, and mocking frameworks depend on. Prefer it when the shared code has more build targets than gates, and record what the restriction costs the inner loop.

How much the compiler helps depends on the ecosystem. Where the restriction arrives as a runtime switch rather than a compile-time condition, a restricted capability still compiles and fails only when its line executes, so without the sweep discovery is one runtime failure at a time.

## Step 5: Run Deterministically and Keep Output Small

Dry run:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py gates --repo . --level 1
```

Execute only after permission:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py gates --repo . --level 1 --allow-exec
```

Optional changed-slice selection:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py gates --repo . --level 1 --allow-exec --changed-from HEAD~1
```

The runner must:

- use real process exit codes
- return `2` for a blocked plan even when execution was not requested
- execute command arrays without a shell
- run only enabled, individually approved, applicable gates
- block package-script gates when the approved source definition changed
- retain pattern-redacted output in local run artifacts
- print a compact success summary
- emit a bounded failure packet on failure
- return nonzero when a gate fails
- launch each executed gate in its own process group
- make a best-effort attempt to terminate the gate's process tree on timeout
- apply only reviewed, non-sensitive environment overlays and record a bounded opaque environment fingerprint when command resolution depends on inherited state

Top-level exit codes are `0` for a valid dry run or all-green execution, `1` for executed gate failures, `2` for a refused plan or execution, and `130` for operator interruption. A timed-out gate is recorded with exit `124` inside its failure packet and makes the overall run fail.

On POSIX systems timeout handling signals the process group. On Windows it uses a new process group and falls back to `taskkill /T /F`. This limits orphaned helpers, but it is not a security sandbox and cannot guarantee termination of a process that deliberately detaches itself.

Do not send full green logs to an agent.

### Shell exit-code contract

Judge a gate by the producer's real exit code. A pipeline normally reports its last command, so `gate | tail`, `gate | grep`, and similar summaries can turn failure into success. Capture output to a file and retain the producer status, use the shell's explicit pipeline-status facility, or execute an argument array without a shell. Test the failure path of every wrapper that summarizes gate output.

### Mutation-testing calibration

Start with the smallest high-stakes pure semantic module that has a stable oracle. Record source lines, test count, mutant count, elapsed time, survivors, no-coverage mutants, timeouts, and errors before expanding scope. A whole-repo first run can hide useful signal in cost.

Keep semantic decisions separate from presentation catalogs, labels, descriptors, and compatibility metadata. Mutating a display-only declaration can create equivalent or low-value mutants that inflate the denominator. Test catalog shape directly, but target mutation gates at behavior whose changed outcome can be falsified.

Report absolute counts beside the score. A perfect score over a tiny denominator is narrow evidence, while a lower score may be dominated by equivalent or no-coverage mutants. Classify each survivor as missing assertion, missing reachability, equivalent mutation, excluded presentation surface, timeout, or tool error before changing thresholds.

Treat unexpectedly fast incremental mutation runs as suspect after fixture-only or data-only test edits. Clean the mutation cache and rerun when the tool cannot prove that test content invalidated prior verdicts.

Typecheck newly authored test batteries separately when the runner transpiles without type information. Passing transformed tests can still assert against shapes the production type system rejects.

## Step 6: Convert Failures into Memory

For a reproduced failure, preserve the smallest practical combination of:

- seed
- starting state or fixture hash
- action sequence
- first bad event
- violated invariant
- expected and actual value
- build or commit identity
- replay command
- full-log path
- minimized regression test or corpus entry

Random exploration becomes valuable when every failure is replayable. Without replay, it produces anecdotes.

## Step 7: Size Agent Verification by Finding Class

Do not give every finding the same number of agent votes.

- A deterministic failing test or exact diff usually needs one strong verifier plus the gate result.
- A claim about economy, incentives, emergent behavior, or statistical balance needs multiple independent refuters or an aggregate probe.
- A presentation or adapter drift claim should compare against the canonical rule implementation.
- A suspected architecture violation should use a dependency graph or AST rule before debate.
- A performance claim needs a baseline and budget, not an impression.
- A security or data-boundary claim needs a concrete source-to-sink trace.

Verifiers receive the claim and evidence, not the finder's persuasive narrative.

## Token and Credit Rules

- Enumerate with scripts, not agents.
- Cache byte-stable inputs and outputs where the harness supports it.
- Summarize success in one line.
- Expand only the first failure and the smallest supporting context.
- Read the relevant source slice, not the whole repo.
- Let gates settle facts before requesting another model opinion.
- Do not ask a high-tier agent to count files, collect imports, deduplicate findings, or monitor a run.
- Run independent cheap gates in parallel when safe.
- Do not run expensive gates after a cheap blocking failure already settled the outcome.

## Acceptance Checklist

Pass `14` is complete when:

- all 20 capabilities have a status and reason
- repo-type adaptations are named
- confidence levels are assigned
- exact gates are proposed or configured
- execution safety and machine limits are recorded
- change-impact rules prevent needless full-suite runs
- successful output is compact
- failure packets are bounded and replay-oriented
- no dependency was added merely because the planner mentioned it

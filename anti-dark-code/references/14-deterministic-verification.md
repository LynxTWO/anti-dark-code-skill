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
  "timeout_seconds": 180,
  "include_globs": ["src/**/*.ts", "src/**/*.tsx"],
  "resource_class": "light"
}
```

Use `include_globs` and `exclude_globs` for change impact. Keep full-suite and soak gates marked heavy. Record hardware restrictions, remote runners, and commands that reach external systems.

Never put secrets in command arguments or failure packets.

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

Top-level exit codes are `0` for a valid dry run or all-green execution, `1` for executed gate failures, `2` for a refused plan or execution, and `130` for operator interruption. A timed-out gate is recorded with exit `124` inside its failure packet and makes the overall run fail.

On POSIX systems timeout handling signals the process group. On Windows it uses a new process group and falls back to `taskkill /T /F`. This limits orphaned helpers, but it is not a security sandbox and cannot guarantee termination of a process that deliberately detaches itself.

Do not send full green logs to an agent.

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

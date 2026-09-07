# Exact gate configuration and execution

Trigger: defining, rebinding or running ADC gates. Apply [core authority and evidence](../SKILL.md). Existing command behavior, approval locks, CLI flags and calibration schema remain unchanged. This is an operator recipe, not a prerequisite for reading source facts.

## Configuration

Store reviewed commands as argument arrays in `calibration/gates.json`. Do not store vague prose such as "run the tests."

A gate bound to source files (`source_files` plus `source_definition_sha256`) is bound to one tree. When those files change, on a commit or on a branch switch, the runner refuses the gate until the binding is reviewed. The targeted repair is `adc.py gates --repo . --rebind GATE --note "why the files changed"`: it recomputes that one gate's binding, keeps the previous digest under `previous_definition_sha256`, appends the note to `owner_notes`, and touches nothing else. It refuses without a note, for an unknown gate, and when nothing drifted. Rerunning the planner also rebinds, and it also replaces the repo profile and the verification plan; use it only when no reviewed plan exists yet. A refusal must name a repair that does not destroy something else, so the runner names the targeted rebind first and the planner second.

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

For comparison and child-result hazards use [falsifiable verifiers](specialist-verifier-falsifiability.md).

Two local cautions:

- Equality assertions over records that contain collections can silently compare references instead of contents. In runtimes where a record or value type delegates member equality to the collection's default equality, two structurally identical payloads compare unequal, and the gate's verdict stops tracking content. Compare serialized canonical forms or compare element-wise, and prove the comparison with a fixture pair that is structurally equal but reference-distinct.
- A value produced in a child context must cross the boundary as an artifact. When verification runs part of its work in a separate process, container, sandbox, or shell, a result assigned to a variable inside the child dies with the child, and the parent then reports whatever its own scope held. Hand results back as a file, an exit code, or a serialized stream the parent reads, and prove the handoff with a case that fails when the artifact is absent.



## Execution and result

Dry run:

```bash
python .agents/skills/anti-dark-code/scripts/adc.py gates --repo . --level 1
```

Execute only within existing user authorization and reviewed gate permission:

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



Inspect exact argv, cwd, inherited environment, inputs and side effects before execution. The examples use the legacy installed path; resolve the trusted actual tool location for this host. For wrappers/cleanup use [process verdicts](specialist-process-verdicts.md); for assurance beyond best-effort termination use [native execution](assurance-native-execution.md). A hash or an editable approval field is not independent human authority.

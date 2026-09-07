# Process verdicts and cleanup

Trigger: a gate wrapper summarizes child output or must stop spawned work.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Judge a gate by the producer's real exit code. The shell composition that collapses a gate to a one-line result is itself a trust boundary, and two ordinary idioms cross it silently.

- A pipeline reports its last command, so `gate | tail`, `gate | grep`, and similar summaries turn failure into success. Capture output to a file and retain the producer status, use the shell's explicit pipeline-status facility, or execute an argument array without a shell.
- A conjunction short-circuits, so `gate && cleanup` skips every later link when an earlier one fails. Cleanup, revert, and restore steps sit at the end of a chain precisely because they matter, which makes them the first casualties. Run them unconditionally through the shell's exit handler rather than chaining them behind the step that can fail.

Piping a failing gate into a summarizer masks its status, which then lets a following conjunction proceed: the chain reports success and the cleanup appears to have run, while the red result is gone. One idiom loses the verdict and the other loses the safety step, so no single fix covers both. Preserve the status and detach the cleanup.

Test the failure path of every wrapper that summarizes gate output, and confirm the cleanup runs when the gate fails, not only when it passes. Then assert the working tree is clean before creating the artifact the chain exists to produce. Detached cleanup can still fail, and a scratch file or a locally modified harness that survives into a commit reproduces only on the machine that made it: local runs stay green while every shared lane goes red.

## Process selection

A harness normally runs an agent command through an interpreter wrapper (`bash -c`, `cmd.exe /c`, `powershell -Command`) whose own argument list contains the command text. Any selector that matches full command lines therefore also matches the caller's own wrapper.

- Do not use a full-command-line selector to signal or terminate. `pkill -f` and `Get-CimInstance Win32_Process | Where-Object CommandLine -match ... | Stop-Process` both select the caller.
- Prefer a process id captured when the harness spawned the process.
- To reach a process the agent did not spawn, resolve the pattern to ids first, drop the current process and its ancestors, then signal only what remains.
- Treat name matching (`pkill -x`, `killall`, `Stop-Process -Name`) as a last resort. It still hits the caller when the target name equals the harness interpreter, and it hits unrelated work when the name is a shared runtime such as a language interpreter. Confirm the real name with `ps -o comm=` or the platform equivalent; some systems compare a truncated name, and a launcher can carry a different name than the binary it starts.
- Keep a destructive process action in its own call.
- Full-command-line search stays appropriate for read-only inspection, where the caller's own wrapper is an expected result.

The exit status varies by host and signal, so do not treat any single number as the signature.

For bounded startup, progress, pipe draining, kill and reap guarantees use [native execution](assurance-native-execution.md).

Result: the producer status survives summaries; failure-path cleanup runs unconditionally; destructive process actions use verified identities and leave unrelated work untouched.

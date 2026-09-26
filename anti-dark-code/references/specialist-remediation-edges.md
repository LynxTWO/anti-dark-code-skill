# External component probes, moves, workspaces, and TODOs

Trigger: a supported fix concerns an external component, a move/extraction, a workspace consolidation, or deferred work recorded in a TODO.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

## Characterizing a component outside the repo

When the misbehaving component sits outside the repo (a device, a driver, a third-party service, a vendored engine), the reproduction forms above stop short: the repo can be instrumented, the component cannot. Characterize the component before reclassifying its failures.

Run a bounded probe matrix that varies one request parameter at a time across several inputs, with a known-good peer, a prior version, or a second instance as a control. Probe an isolated, disposable, or owned instance. If the only reachable instance is production, shared, metered, or someone else's, the probe is an approval-gated action rather than a free one.

Then shape the fix to what the matrix showed:

- Prefer changing the request over reinterpreting the failure code. Widening a retry or tolerate list weakens it for every other caller, including callers the probe never covered.
- Scope the workaround to the exact identity the probe covered (vendor, model, firmware or version), and gate it on a condition the code can check at runtime. Cite the probe receipt in the code comment.
- A probe separates request shape from component state. It does not separate cause from coincidence. A failure that repeats at every probed shape is a state problem, and its cause stays `inferred` until an independent second incident or a control run rules the alternatives out.

## Moves and extractions

A rename or extraction is only half-checked. Symbolic references - imports, types, call sites - are the half a refactoring tool rewrites, and a compiler, type checker, or failed import catches most of what it misses. References held as text sit outside that graph: a path or filename inside a string survives the move unchanged and stays green until something runs it.

The usual holders are release and CI scripts, coverage, lint, and container build configs, dynamic loaders that resolve modules or classes by name, docs citing exact paths, and tests or guards that read source files from disk to assert ordering or invariants.

Before a move or extraction is called done:

- sweep specific to broad: the old relative path first, then the old directory segment, then the bare basename. A path assembled from parts never matches the full path, and the basename alone is the noisiest of the three.
- confirm the basename is distinctive before acting on basename hits. Repeated names are normal (`Program.cs`, `index.ts`, `__init__.py`, `main.go`), and a hit may belong to a different file that did not move.
- cover the test, script, workflow, config, and docs trees, not just the source tree. Exclude build output and vendored trees or the sweep drowns in its own artifacts.
- treat every surviving hit as a required edit or a recorded decision.
- close the sweep in the same change as the move where you can, and before the wave ends at the latest. Rerun it after each follow-up move, where stragglers cluster.

A green build after a move proves the symbols resolved. It does not prove the move is complete, and where there is no build step it proves nothing at all.

Moves also strand generated consumers. Autolinking output, compiler caches and generated native manifests can keep old absolute paths, or entries the configuration removed, after an incremental run. Keep generated output out of the text sweep, but find the consumers that execute next: regenerate identified output from current configuration, inspect the final packaged configuration where it matters, and run the affected build or startup before calling the move done. Delete only identified regenerable output. Preserve signing material, private environments, manual native edits and failure evidence, and do not clear every cache for an unrelated change.

## Workspace consolidation

Folder names and dates do not establish that a copy is redundant. Before moving, merging or deleting checkouts, inventory each one: branch and upstream, dirty and untracked work, worktree links and shared Git storage, private inputs and generated output. An older-looking checkout can own the metadata an active worktree depends on, and a retained file can share a current file's name without sharing its bytes. Treat a copy as redundant only with comparison evidence, move worktrees with Git's own commands, and recheck the relationships afterwards. A small single-repository task may need only a status check, and none of this authorizes deleting unique work.

## TODO lifecycle

A safe fix sometimes has to leave a `TODO` behind because the full fix is approval-gated, blocked on evidence, or larger than the current commit budget. Track every such TODO end-to-end so it does not become the next generation of dark code.

Lifecycle:

1. **Plant** - the TODO comment names the area, the reason, and the unknowns or backlog entry it points to. A bare `TODO: fix this` is not allowed in remediation work.
   ```ts
   // TODO(adc): redaction here is shallow because the trace SDK formats the body
   // upstream. Tracked in docs/review/remediation-backlog.md#auth-trace-redaction
   // and docs/unknowns/logging-audit.md#auth-trace-shape.
   ```
2. **Track** - every planted TODO has a matching backlog row (or unknowns row, when evidence is still soft). The row carries the same status vocabulary the rest of the workflow uses (see the existing artifact schema; do not reinterpret stored statuses).
3. **Clear** - when the underlying work lands, the TODO is removed in the same change that closes the row. The change record names both the TODO removal and the row that closed.
4. **Audit** - the [maintenance harness](10-maintenance-harness.md) should add a reviewer-checklist item asking whether new `TODO(adc):` lines were planted with backlog references, and whether any cleared TODOs left behind a stale comment.

If a TODO outlives the engagement that planted it, the next task touching that obligation rechecks whether its row still makes sense before extending it.

Result: external probes retain exact identity/control evidence, every stale textual reference is edited or dispositioned, generated consumers are regenerated and run after a move, consolidation preserves unique work, and every TODO has a tracked reason and closure path.

# Gate environment and runner identity

Trigger: a gate depends on exclusive files, frozen dependency state, generated outputs, or a particular configured test runner.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

- Keep scratch artifacts outside developer-indexed trees when exclusive access is required. If cleanup or file access fails, inspect the observed error, sandbox permissions, process ancestry, open handles, and producer finalization before proposing a remedy. Use a handle-enumeration tool when available; otherwise record the holder as unknown. A surviving file or absence of a visible user-mode holder cannot identify an indexer, kernel filter, or leaked child by itself. Do not hide a reproduced ownership or cleanup failure with retries or a longer timeout. If a demonstrated remedy requires a tool exclusion, record it as an environment prerequisite and verify the result under that condition.
- Treat audited dependency state as read-only during builds. Name the frozen or no-restore flag for the repo's package manager in the harness prerequisites, run verification builds with it, and gate on an unchanged lock-file hash. Route every restore through the reviewed path that validates the locks, so no other command is allowed to regenerate them as a side effect. The cheap tripwire is a version-control status check after any build that was supposed to be read-only: a modified lock file is the alarm, and it is easy to miss because the damage travels into the next commit looking like ordinary noise.

- A producer that is not a gate declares an output root outside any audited or lease-protected tree, and the reason is commented at the path definition so the next author does not move it back. Writing into an audited tree is an opt-in to that tree's obligations, lease, invalidation, atomic publish, and audit, whether or not the author noticed.

## Configured runner

A test file invoked outside its package's configured runner returns a verdict about the invocation, not about the code. A wrong working directory, an overridden root, or a bypassed configuration manufactures failures that look real: path-relative reads miss their fixtures, discovery resolves against the wrong tree, and assertions fail on absence the canonical runner never sees.

- Record the canonical invocation beside the suite, and use it in evidence.
- When an ad-hoc run disagrees with the canonical runner, distrust the ad-hoc run first.
- Zero discovered tests establishes no tested coverage. Check the canonical runner, working directory, filters, prerequisites, and whether tests exist in the requested scope. Report the observed cause or leave it unknown; zero discovery alone cannot prove a wrong directory or a source defect.
- When a spurious failure has been observed and explained, record the ghost and its explanation where the next reader of the evidence will look.

## Expected work

Inspect the selected test bodies before broadening a runner to ignored, manual, or developer tests. Those labels can include asset generators, baseline writers and user-data tools. Discover names through the configured runner and classify effects; a text search for a test macro may match comments, string literals or the detector itself. Bind an unattended selection to explicit reviewed targets and record excluded obligations. Compilation or listing must not be reported as test execution.

A checked CI box or zero exit code is not enough. Where the repo has tests, multiple targets, plugins, native dependencies, generated outputs, or release packaging, make the gate prove the expected work occurred:

- assert discovered and executed test counts, including a zero-discovery failure
- assert expected target, configuration, platform, and architecture tuples
- assert required artifact members, versions, sizes, hashes, and provenance receipts
- assert expected plugin or dynamic-discovery registrations
- assert warning or policy baselines against the logs that produced collected bytes
- retain the real producer exit code instead of a summarizer or output-filter exit code

Keep assertions scoped. A manifest proves its declared shape, not that every feature works. An allowlisted failure is tracked debt, not healthy behavior.

For a release candidate, bind test receipts to the selected source, dependency lock, fixture bytes, build configuration and final artifact bytes. Check source identity again after long producers finish: successful assertions during a changing tree do not establish a coherent release. Reuse a shared build recipe for packaging and its verification when feature selection affects dependency unification; equal version strings and target directories do not prove equal builds. Preserve prior candidates and receipts when producing a replacement.

Calibrate detector thresholds against clean and known-bad fixtures. Record why the threshold separates meaningful drift, keep a positive fixture that crosses it, and review threshold changes as behavior changes.

Required CI jobs keep a measured timeout margin of at least two to one or are split. Re-measure before opening concurrent PRs.

Result: the canonical command, environment prerequisites, source and lock hashes, discovered/executed counts, target tuples and exact artifacts support the verdict. A zero-test invocation cannot establish tested coverage.

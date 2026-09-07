# Subprocesses, executables, and native ABIs

Trigger: a claim crosses a child process, external executable, native ABI, or staged production host.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

### Subprocess termination

- Bound startup, active work, idle progress, output draining, and post-kill reap according to the real progress contract.
- Drain redirected pipes concurrently or impose a bounded output policy.
- Attempt process-tree termination on timeout and retain termination failure as explicit evidence.
- Return failure when termination cannot be proven. Do not follow a timed wait with an unbounded wait on the timeout path.
- Fault-test normal exit, timeout and kill, kill failure, and a child that remains alive after the deadline when injectable.

### External executable support and redistribution

- Separate invocation support from redistribution permission. Support may stop at a user import until licensing, source, patent, notification, attribution, dependency, and provenance obligations are complete.
- Exercise the exact released executable against intended stdin, file, stdout, mode, error, and finalization behavior. Help text or another version is not execution evidence.
- Require an independent finalized-output verifier for assurance-bearing transforms. Do not infer general decode support from a private self-check.
- Pin the authoritative HTTPS source, archive size and digest, selected entry and digest, version, license, source obligations, and runtime dependencies.
- Resolve a receipt-bound user import before a packaged fallback so updates do not replace package-owned bytes.
- Repeat the executable digest in the artifact contract and runtime resolver. Hash and hold the selected file against replacement through launch and verification.
- Generate notices from the same manifest. Test source drift, archive drift, entry drift, tampered installed bytes, user override, real work, failure, and package completeness.

### Native ABI compatibility

- Pin binding, native source or package, build features, compiler tuple, and architecture as one compatibility set.
- Compare runtime ABI majors before the first call that interprets native structs or enums. Fail with expected and observed identities.
- Make partial initialization transactional. Give every allocation, handle, callback root, and native owner one cleanup path that works when the next step fails.
- Catch managed exceptions at native callback boundaries. Return the native error contract, retain the first failure, and report it after control returns to managed code.
- Exercise EOF drain, final flush, nonzero seek or reset, callback failure, disposed access, and materially different input shapes.
- Run the real native runtime in a process for every shipped architecture. Record filenames, versions, lengths, hashes, licenses, and build inputs.
- Launch from the staged production layout through the shipped host. Probe initialize, work, finalize, and read-back; a version symbol or validator-local load is insufficient.

Result: separate observed support, ABI, termination, redistribution, and packaging evidence for each claimed tuple. See [reachability](specialist-native-reachability.md) for the full source-to-invocation chain.

# Reference: Assurance and Boundary Contracts

Load only the sections that match the active finding. Use these checklists before accepting strong claims such as verified, bit-exact, atomic, repaired, complete, safe, available, or release-ready.

**Mode:** inherits the active pass. These checklists do not grant permission to execute code, mutate data, publish artifacts, or cross an approval gate.

## Contents

- Assurance claims and branch activation
- Measured hardware and nested recovery
- Transactions, preservation, and concurrency
- Subprocesses, external executables, and native ABIs
- Dependency locks, provenance, and release evidence
- Compatibility, UI policy, external content, and hot paths

## Assurance claims and branch activation

Treat an assurance word as a contract, not an adjective. Record:

1. the exact claimed object and scope, such as frame, stream, finalized file, staged output set, or published result
2. the producer path and an independent oracle that can falsify the claim
3. every finalization boundary, including finish, flush, close, child exit, final length, and manifest completion
4. whole-output proof when the claim covers a whole artifact; partial checks do not prove final blocks, metadata, length, or truncation safety
5. positive, mismatch, truncation, finalization-failure, cancellation, and unavailable-capability outcomes when applicable
6. the exact runtime, toolchain, target tuple, observed counts, and skipped boundary
7. every UI, tooltip, log, document, receipt, or downstream copy that repeats or carries the claim

Reopen or independently decode finalized assurance-bearing output. Compare format, expected length or sample count, and all payload bytes or a collision-resistant digest over those exact bytes. A successful write or per-unit check does not cover an ignored final flush.

Treat disagreement between the product verifier and a credible independent oracle as a verifier finding. Preserve the rejected artifact, locate the first failing object and boundary, and test both implementations before changing the producer or suppressing the check.

Trace classifier ancestry. When several parents can reach one recovery child, test every reachable parent/child route. One covered route does not validate siblings.

Treat retry, reset, and fallback scope as operation identity. State whether the budget is global, per job, per address, per payload shape, or per exact command. Test exhaustion and reset at that boundary so one sibling cannot consume another's recovery.

Separate outcome proof from branch-activation proof. A green end-to-end result does not exercise an intermittent recovery branch unless a counter, trace, injected fault, or retained event proves activation. Keep branch coverage `unknown` when activation evidence is zero.

When proof moves across a copy, metadata rewrite, rename, upload, or publication boundary, carry an immutable receipt that binds the exact output set and semantic oracle. Revalidate it at the new boundary or explicitly clear the claim. Prevent time-of-check/time-of-use gaps with an appropriate lease over the bytes being hashed, copied, or reopened.

Verify an isolation property, never the request that asked for it. Sandboxing, isolation, and privilege-restriction interfaces can accept a request and silently not enforce it, and the same request can be enforced on one host and be a no-op on the next. The probe must observe the property in context: attempt exactly what the boundary must prevent and require an observed denial, in every environment the claim covers. Reading back the configuration that requested the isolation is not evidence, because it reproduces the original error. Where the probe cannot run, a gate asserting the property fails rather than passes, and the claim stays `inferred` with the gap named. A probe that tests nothing is indistinguishable from a passing probe, so silence must not be scored as success. Where a property has no cheap in-context probe at all, record it as unverified rather than asserting it.

Treat self-certification as an anti-pattern. A checker satisfied by editing the artifact it checks is a ritual, not evidence; a review-closure signal pinned to a literal the author can update in the same edit certifies nothing. Bind closure signals to something outside the artifact under review: a second artifact, a recorded run, or a reviewer identity. Substitute a check that would fail if the claimed review had not actually happened.

Prefer substantive properties over a single declarative line: no finding left in an open state, no unresolved verdict language in the document, and a hash binding so any edit is visible. Two traps sit in the replacement itself. Scope the scan to the whole document, because a live verdict often lives in a different section than the one a first attempt checks, and a check that passes over the section holding the rejection is no better than the literal it replaced. And distinguish a live claim from an accurate historical record: tense is a reliable discriminator, and closing a check must never require deleting true history.

## Measured hardware and nested recovery

Use this section when correctness depends on device capability, timing, cache behavior, boundary reads, media state, or persisted calibration.

- Treat newly required calibration as a state migration. Trigger it before the first operation that relies on it, version the record, and refuse assurance when the probe cannot complete.
- Distinguish positive evidence from failure to observe. Once a device demonstrates a safety-relevant behavior, a later noisy run that does not observe it does not prove disappearance.
- Retain a conservative high-water measurement only when oversizing costs performance and undersizing invalidates evidence. State why that direction is safe.
- Make proof-establishing side effects complete or explicit. A partial flush, shortened scrub, ignored status, or incomplete seek-away read is not an independent reread.
- Separate bad subject data from device, reader, transport, command, protocol, readiness, or removal failure. Convert only the subject-data class into explicitly untrusted evidence. Keep other failures fatal unless narrower recovery has independent evidence.
- Probe the exact command, transfer shape, flags, range, and offset the runtime consumes. A nearby or larger probe may reject a valid operation; a successful flag is useless if the runtime bypasses it.
- Treat completion of a control command as evidence for that command only. Serialize control transitions with payload I/O, apply only a measured bounded settle, and retry only the observed transition-bound failure.
- Decompose a rejected batch only when items can be read independently. Continue only from independently successful child results. Never consume bytes from a rejected parent.
- Snapshot the innermost failure before another operation can overwrite shared error state. Preserve the child identity, parent ancestry, address, range, and failure class.
- Require corroborating parent evidence and a bounded repeat before a child failure enters an untrusted-subject path. A different repeat keeps its own fatal class.
- Persist semantic evidence roles. Baseline, Test, Copy, confirmation, and tie-break results are not interchangeable values.
- Publish immutable phase evidence when the phase completes. Do not hide or erase it because a later phase failed.
- Keep a completed recoverable stage in an explicit held or pending state when later confirmation fails. Do not auto-promote it, but do not delete the only completed result.
- Bind displayed and persisted capability results to the exact physical device. Invalidate stale identity on selection changes, and freeze or lock selection while an operation owns the device.
- Exercise real hardware beyond the prior failure time, location, or transition. A quick open or metadata smoke test does not prove repeated flush, seek, reread, or edge behavior.
- Report unavailable hardware, access-denied resets, wedged handles, and incomplete probes as evidence gaps, not negative capabilities or passing tests.

## Transactions, preservation, and concurrency

Use this section for repair, import, output publication, multi-file generation, migrations, or any operation advertised as atomic.

- Resolve canonical source, stage, quarantine, backup, and destination paths. Enforce containment and reject traversal or link-like surprises where the threat model requires it.
- State the coordination domain: thread, process, session, host, or shared filesystem. A process-local lock does not serialize another process that reaches the same resource.
- Inventory every shared physical resource, setting, cache, history record, log, stage, and destination. Require identity-bound ownership, same-resource denial, independent cancellation, crash release, and collision-safe publication before claiming safe parallel work.
- Create a unique same-volume sibling stage with an unpredictable ownership token. Remove or quarantine it only after proving ownership; a path name is not ownership.
- Write only to the stage. Keep source and destination unchanged until every producer finalizes and the independent oracle passes.
- Check every finalize, flush, close, and child-process result. Require the exact expected output set, nonempty required files, and no missing tail outputs.
- Reopen staged results through an independent reader or validator. For repair, prove the correction was applied to the repaired copy.
- Define the preserved representation as well as payload. Test names, metadata, artwork, sidecars, ordering, timestamps when promised, and format-specific fields.
- Separate user-authored identity metadata from payload-dependent proof. Preserve representable human fields, but recompute or deliberately remove stale checksums, signatures, confidence values, and verification tags after payload changes.
- Give preservation operations their own policy. Ordinary conversion preferences must not silently disable required names, metadata, or proof.
- Derive names inside the contained stage and reject collisions after normalization, extension changes, and destination case-folding rules before writing output.
- Expose recovery from the producer's completion route as well as later maintenance routes when degraded completed output is recoverable. Exercise every supported output shape.
- Test the platform's real file-lease and directory-rename behavior. Do not infer one from another platform or a child file's sharing flags.
- If proof leases cannot survive an atomic move, retain reservation and ownership, move into pending publication, reopen and verify at the destination, then expose success.
- Bound stored and decoded or expanded bytes before parsing. Validate the complete object graph before republishing it.
- Write completion markers after validation. Publish into an absent destination with the platform's proven atomic primitive.
- Never replace a pre-existing destination by name alone. Require an ownership receipt that binds the exact tree.
- Write a recovery journal before moving an owned destination aside. Bind stage, backup, cleanup, and journal actions to one transaction token; validate publication before deleting backup.
- Name the commit point. Cleanup, callbacks, reservation release, and diagnostics after it must not reclassify success as failure.
- Preserve source and independent evidence on failure or cancellation. Remove only owned incomplete state.
- Fault-test write failure, finalization failure, mismatch, cancellation, contention, missing and extra outputs, stale recovery, stage replacement, and post-commit cleanup failure.

Atomic publication hides partial final results. It does not prove durable storage, content correctness, or successful repair.

## Subprocesses, external executables, and native ABIs

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

## Dependency locks, provenance, and release evidence

### Dependency and source closure

- Discover first-party dependency consumers from declarations. Require the enrolled locked set to equal the observed set.
- Commit direct and transitive lock closure. Regenerate only through an intentional review, then run locked restores through every build host that consumes the graph.
- Exclude immutable vendor worktrees and generated dependency stages from root lock policy, then prove restore and build leave them unchanged.
- Treat locks as dependency-resolution evidence, not artifact identity. Keep build receipts, notices, SBOMs, source inventories, and final hashes as separate proofs.
- Treat source inventories as live assertions. Rehash every selected committed input after any patch, build-script, SDK-source, or vendored-binary change.
- Make provenance independent of ignore rules and checkout visibility. Validate archive-derived trees by exact path, size, and hash against the pinned archive and record the complete closure digest.
- Build patched dependencies from an owned identity-bound stage. Keep dependency worktrees immutable and prove restore, build, test, packaging, and release consumers all use the same stage.
- Keep stage-local generated and compiler output classified as disposable build state. Reject unknown or modified source members.

### Build and release closure

- Distinguish installed component selection, installer inventory, files on disk, and a successful target build. Each proves only its own layer.
- Record the exact build host, compiler, SDK, target, configuration, and architecture tuple.
- Keep clean, dependency preparation, build, receipt, collection, signing, and validation under one orchestrator and one lease over every shared mutable output.
- Recover or refuse retained build intent before cleanup. Preserve failed intent and logs; a corrupt or foreign intent leaves outputs untouched.
- Evaluate warnings and policy from the exact build logs that produced collected bytes.
- Bind collected bytes to the receipt with hashes of the receipt, source inputs, and artifacts. Copy from file objects held against mutation.
- Record each workflow step's effective shell. Validate comments, quoting, variables, multiline syntax, wildcard behavior, and exit propagation in that shell.
- Check native child exit codes immediately. YAML and workflow lint prove structure, not hosted execution or artifact contents.
- Inspect hosted annotations and downloaded artifacts. A green job does not prove the expected runtime, architecture, license, signature, or final bytes.

### Signing and SBOMs

- Derive the exact first-party signing set from the versioned artifact contract. Keep pinned third-party and platform files untouched.
- Treat signing as a byte-mutating build phase. Validate unsigned candidates, sign, verify signer and timestamp, regenerate hash manifests, revalidate, then produce provenance, SBOMs, checksums, archives, and publication records.
- Keep credentials out of repositories and logs. Require one expected code-signing identity in the narrowest temporary store or provider scope.
- Fail closed on credential, timestamp, trust, coverage, or post-sign validation failure. Label unsigned evaluation artifacts and keep them ineligible for production publication.
- Preserve JSON types during SBOM normalization. Refresh dependent sidecars, prove exact artifact membership and a nonempty dependency graph, and run the producer's validator.

## Compatibility, UI policy, external content, and hot paths

- Resolve and health-check the exact selected implementation before scarce-resource ownership or expensive input reads. Freeze its stable identity in the job and queue snapshot.
- Inspect every serializer and migration before changing defaults. A previously omitted old-default value is indistinguishable from unset without an explicit migration.
- Treat public plugin and legacy-assembly signatures as binary contracts. In-repo rebuild success does not prove external compatibility.
- Treat in-process plugins as code-execution grants, not sandboxes. Registration rollback cannot undo arbitrary initialization side effects.
- Exercise real protocol payload, sustained transfer, authentication failure, final flush, and server-side receipt. Connect success alone does not prove streaming.
- Keep persistence and publication results separate from the main operation result in UI state. Never display a side effect that failed or was not attempted.
- Treat UI notifications, progress callbacks, and rendering observers as ancillary. Contain their exceptions after durable transitions so presentation cannot change producer correctness or cleanup.
- For code-drawn, GPU, or animated UI, lock the semantic state contract independently of rendering. Require deterministic offscreen state matrices, actual themed-window captures, and post-warmup allocation bounds for hot loops.
- Carry stable model identity through filtered or sorted views. Never persist a rendered ordinal when rows can move, skip, or fail.
- Keep hot paths allocation, blocking, I/O, dispatch, and ownership aware. Verify behavior first, then measure the touched path against a stated budget.
- For asynchronous presentation, use bounded ownership-safe transfer. A slow UI may drop presentation samples, but it must not block, allocate on, or alter the producer's correctness path.
- Verify optional providers from authoritative documentation. Collect only the credential the protocol uses, protect it with a purpose-specific scope, and keep providers off until attribution, distribution, rate, and failure-isolation rules are satisfied.
- Read local user input once into bounded immutable bytes. Reject unsafe links, unsupported magic, oversized encoded or decoded input, and replacement between validation and use.
- Separate candidate ranking from automatic eligibility. Freeze the user's exact selected bytes and subject generation when a background job begins.
- Test malformed, truncated, oversized, replaced, multi-item, cancellation, outage, rate-limit, stale-generation, override, fallback, no-selection, and final-output cases.

## Acceptance checklist

- each strong claim names its scope and independent falsifier
- finalization and publication boundaries are checked
- retry and recovery ancestry is explicit and activated in evidence
- payload and semantic identity are both preserved where promised
- concurrency authority matches the real shared-resource domain
- external support, redistribution, provenance, ABI, and packaging remain separate findings
- release evidence binds the exact final bytes
- UI and diagnostics remain observational unless explicitly designed as authority
- unavailable capabilities remain evidence gaps rather than passing claims

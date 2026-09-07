# Transactions, preservation, and concurrency

Trigger: repair, import, migration, multi-file generation, or output publication promises atomicity or preservation.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

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

Result: a named commit point, independently validated staged output, ownership-bound recovery, and passing fault cases for the actual coordination domain.

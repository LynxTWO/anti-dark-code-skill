# Artifact cleanup

Compatibility reference 09. An explicit operator workflow for generated logs, snapshots, exports, review bundles and scratch files. Ordinary audits do not automatically run cleanup. Apply the [core authorization contract](../SKILL.md).

## Inventory and classify

Inventory groups read-only: size, counts, timestamps, tracked/ignored status and citations from source, docs, CI and review evidence. Cited outputs support claims; preserve them or an approved copy beside the citation before moving bytes. Record claims, exact regeneration commands, seeds, parameters, costs and dependencies while originals remain available.

| Tier | Handling |
| --- | --- |
| Protected | Tracked content, steering-protected assets, review evidence and history stay untouched in this workflow. Pruning them requires a separately scoped authorized change. |
| Regenerable-cheap | Record recipe, spot-check byte parity, archive originals as fallback; default retention 30 days. Remove only within the group's granted authorization. |
| Regenerable-expensive or irreplaceable | Checksum, archive, decompress and rehash against manifest. Add parity data, about 10 percent, whenever the archive becomes the only copy. Original removal requires explicit group authorization; default retention 90 days. |
| Unknown provenance | Leave in place or archive untouched within authorization, record an unknown and resolve provenance before deletion. Lack of references does not prove dispensability. |

Split mixed groups into tier-uniform rows. Record depends-on relationships; do not delete dependencies before dependents are regenerated, archived or themselves authorized for deletion. Until claims and recipes are recorded, treat the artifact as protected.

## Stage safely

Prepare per-group actions and reuse existing approval only when it covers those groups and operations. Quarantine first, verify archives, then delete approved originals. Never start with bare deletion of material with nonzero regeneration cost. If reclaiming space, an authorized quarantine on another volume frees the source volume; moving within a full volume does not.

Before recursive mutation, resolve the absolute target and every existing parent component. Reject symlink, junction, mount-point and reparse-point traversal unless specifically reviewed and authorized; inspect descendants without following links and refuse recursion when link-like descendants exist. Recheck targets, descendants and evidence destination leaves immediately before mutation. A lexical prefix alone proves no containment.

Keep receipts outside the artifacts they describe. Artifact names must be single filenames, not paths. Hash source inputs separately from generated residue; classify intermediates by type/count and never silently omit or traverse link-like entries while hashing. Propose recurring ignore rules and local-state definitions; steering changes require their own authorized scope.

## Evidence and result

Write authorized records to docs/maintenance/artifact-gc-ledger-<date>.md and docs/maintenance/manifests/<group>-manifest.json, or existing equivalents. Each ledger row records tier, evidence, size, action, archive location, checksums and retention expiry. Each manifest entry records file, hash, supported claim, regeneration/cost and dependencies. Store archives in an ignored directory or outside the worktree, with parity files beside the only copy.

Completion requires every group disposition, recoverable evidence for removed bytes, untouched protected groups, explicit unresolved provenance and proposed regrowth controls.

## Identifier changes are separate work

History rewrites, re-signing and identifier migrations can strand evidence; cleanup never performs a rewrite or force-push. First search docs, pins, lockfiles, CI and release records for affected identifiers. If none are cited, record that bounded result.

When an owner separately authorizes a rewrite with cited identifiers, prepare these obligations before publication:

- Compare old/new tree sequences; a message-only rewrite preserves every non-gitlink entry.
- Track the old-to-new map and a dated explanation.
- Inventory citations and pins across dependent repositories/submodules; authorized remaps must resolve in new history.
- Decide whether each published evidence artifact is retained with an annotation or withdrawn; never silently leave unresolved evidence.
- Verify host/clone retention limits. Secret removal also requires authorized rotation and incident handling; rewriting history alone does not erase existing copies.

Other-repository edits require authority for those repositories. The result is a reviewable evidence-migration packet, not cleanup permission to alter history.

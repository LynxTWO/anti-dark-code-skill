# Reference: Artifact Garbage Collection

Use this reference after heavy passes, harness runs, or build phases have littered the repo with generated artifacts: logs, snapshots, scratch scripts, exports, review bundles, screenshots, stale baselines.

**Mode:** read-only on application code and on protected artifacts. Docs and archives may be created. Deletion happens only through the staged path below.

For confidence levels, unknowns entry shape, approval gates, and default doc paths, see `00-conventions.md`.

## Goal

Separate the claim from the artifact. The durable value of a generated file is the claim it supports plus the recipe that regenerates it. Distill both into tracked records first. After that, the artifact itself drops to a tier and gets handled by tier rules, not by mood.

An artifact nobody can explain is dark data, the same failure as dark code. The manifest this pass produces is what keeps archives from becoming that.

## When to run this

- generated artifacts have accumulated across passes or build sessions
- a user asks to clean up, declutter, or reclaim space
- before a maintenance handoff (pass `10`), so the harness starts from a clean floor
- after any orchestrated fan-out that wrote working files

## The four tiers

- **protected.** Named by steering files (docs, review artifacts, assets, repo history) or git-tracked. Never deleted, moved, or rewritten by this pass, no matter how broad the user's cleanup request sounds. Pruning stale tracked content is a separate, explicitly scoped engagement with its own approval.
- **regenerable-cheap.** One recorded command or seed reproduces it quickly. Record the recipe in the manifest, spot-check regeneration for byte parity, archive the originals as a fallback with a short retention window (default 30 days), then remove them.
- **regenerable-expensive or irreplaceable.** Archive first, delete later, never the reverse. Checksum every file, compress (tar plus zstd, or 7z), verify by decompress and re-hash against the manifest, and add parity data (par2, about 10 percent) whenever the archive becomes the only copy. Ask explicitly before removing originals. Retention default 90 days.
- **unknown provenance.** Hard stop. Archive untouched or leave in place, record an unknowns entry, and ask. Absence of references proves unused-by-current-code, not unimportant. Do not let "nobody remembers this" become "safe to delete."

## What to do

1. **Inventory** (read-only; fan-out safe under `orchestration-mode.md`). Per artifact group: size, file count, oldest and newest mtimes, tracked or ignored status. Then cross-reference: grep tracked content (docs, review reports, coverage files, source, CI config) for citations of artifact paths or filenames. A cited artifact is evidence; keep it or copy it beside the citation before anything moves.
2. **Distill before bytes move.** Extract claims and regeneration recipes (seeds, parameters, exact commands, cost estimates) into the manifest while the originals are still in place.
3. **Classify** every group into one of the four tiers, with an evidence label per claim.
4. **Approval gate.** State the scope reading up front (protected groups are out of scope even though the request said "clean it all up"). Ask per-group questions, never one blanket yes. Unknown-provenance groups are a blocking question.
5. **Execute staged.** Quarantine first (move, reversible), verify archives against the manifest, then delete originals only where approved. Two phases, always. Never a bare delete as the first action on anything with nonzero regeneration cost. When disk pressure motivated the pass, quarantine to a different volume: moving bytes around a full disk relieves nothing, and an off-volume quarantine already frees space without waiting on any delete approval.
6. **Guard against regrowth.** Propose gitignore additions for the recurring artifact paths and a durable definition of what counts as local dev state in this repo. Steering-file edits are proposed, not applied; steering files are themselves protected.

## Deliverables

- `docs/maintenance/artifact-gc-ledger-<date>.md` - one row per group: tier, size, evidence found, action taken, archive location, checksums, retention expiry date.
- `docs/maintenance/manifests/<group>-manifest.json` - per file: name, hash, the claim it supports, and the regeneration command or cost.
- Archives in a gitignored archive directory or outside the working tree, with parity files beside any archive that is the only copy.
- An unknowns entry for every unresolved group.

Do not place the ledger inside a protected folder it catalogues.

## Rules

- Git-tracked content is never auto-deleted. Steering-file protections override the user's broad phrasing.
- The manifest is load-bearing: a future session must answer "where did it go and how do I get it back" from the ledger alone.
- Retention expiry is a date written in the ledger, not a memory.
- Deletion approval is per group. Risk profiles differ too much for one bundled yes.
- Distill first. If the claim or recipe is not recorded, the artifact is not yet eligible for any tier but protected.
- One tier per ledger row. Split a mixed group (final versus intermediate checkpoints, cited versus uncited outputs) into tier-uniform rows instead of forcing one tier onto all of it.
- Artifacts form chains. Record depends-on in the manifest, and never delete a dependency before its dependents are regenerated, archived, or approved for deletion themselves. A cheap regeneration recipe that points at a deleted input is not cheap.

## History rewrites and other identifier changes

A history rewrite is an evidence event, not a cleanup. Rewriting commits changes every id that docs, receipts, lockfiles, submodule pins, and release evidence cite, so the citations survive while the objects they name do not. The same rule covers any operation that re-mints recorded identifiers: id migrations, artifact re-signing, tag or release renumbering.

This pass never performs the rewrite and never force-pushes. Repo history stays protected. What this pass does is inventory what the rewrite will strand and hand the owner that list.

Start with a cheap existence check: does anything outside the object store cite these ids? Grep docs, lockfiles, pins, CI config, and release evidence for id-shaped tokens. A repo that cites none of its own ids is done here and needs none of what follows.

When ids are cited and the owner directs a rewrite, require all of this before the force-push:

- **Prove the content is unchanged.** Compare the tree sequence old versus new and record the result. A message-only rewrite must leave every non-gitlink tree entry identical.
- **Keep the old-to-new map as a tracked artifact.** It is the only thing that can later repair a citation, a pin, or a branch that missed the rewrite. Rewrite tools write the map into a scratch directory that the next clean wipes; a map you did not commit is a map you do not have.
- **Remap every pin that points at the rewritten repo,** in sibling repos and submodules as well, and prove each remapped pin resolves in the new history.
- **Sweep citations across every repo that cites this one,** not only the rewritten one. Record how many citations in how many files moved, and write a dated note saying why the ids changed.
- **Decide, per artifact, what happens to evidence citing pre-rewrite ids.** Withdrawing an unconsumed artifact is cheap. Withdrawing a published one breaks downstream pins and lockfiles and is usually worse than the dangling citation, so annotate it with a pointer to the rewrite note instead. Either way the decision is recorded. What is not allowed is evidence that silently resolves to nothing.
- **State what the rewrite cannot remove.** Hosts keep old objects reachable from merged or closed change requests, and existing clones keep them on any local branch nobody rewrote. Verify retention per host and per clone instead of assuming. When the rewrite existed to remove a secret, this limb is a security action rather than a footnote: the secret is still readable, so rotate it and treat the rewrite as containment, not deletion.

Remapping pins and sweeping citations in other repos are edits to protected content. Propose them and take the same per-repo approval this pass requires everywhere else.

The dated note is the deliverable. If a later reader cannot tell from the repo why a cited id changed, the rewrite produced dark data.

## Acceptance checklist

- every artifact group has a ledger row with a tier and evidence labels
- every removed byte has a manifest entry plus a verified archive or a spot-checked regeneration recipe
- protected groups were not touched
- unknown-provenance groups are archived or untouched, recorded, and asked about
- regrowth guards were proposed

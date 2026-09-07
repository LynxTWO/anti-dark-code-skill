# Dependency, signing, and release closure

Trigger: a claim covers dependency closure, build provenance, signing, SBOMs, or released bytes.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

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

Result: receipts bind exact source, build, signing and final artifact sets. Apply [publication integrity](assurance-publication-integrity.md) when approved work crosses a publication boundary.

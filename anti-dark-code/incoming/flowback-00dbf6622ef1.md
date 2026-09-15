# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.15-unified.15`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Inventory repository relationships before consolidation

- Scope: repo-agnostic
- Lesson: Folder names and dates do not establish deletion safety. Inventory branches, upstreams, dirty and untracked work, worktree relationships, common Git storage, private inputs and generated artifacts before choosing the canonical entry point.
- Evidence: ORG-01 found an older-looking checkout holding Git metadata used by the active worktree. ORG-02 found retained uncommitted files whose names existed in current source but whose bytes differed. Those relationships and files were preserved.
- Limits: A small single-repository task may need only a short status check. This does not require a workspace redesign or authorize deleting unique work.
- Proposed target: references/specialist-remediation-edges.md
- Proposed change: Add a consolidation checklist that preserves dirty, untracked and shared Git state, uses Git-aware worktree moves, and verifies repository relationships afterward. Require comparison evidence before treating an older copy as redundant.

## ADC-LOCAL-002: Separate workspace layout from source and publication scope

- Scope: repo-agnostic
- Lesson: One project entry folder can contain separate repositories, artifacts and archives. A workspace index should identify active source, unfinished work, historical evidence and private inputs. Sharing a parent folder must not make everything active source or a release input.
- Evidence: ORG-03 found repository-wide linters traversing archived and sibling project material. Moving active source into a workspace child restored the intended scan boundary without broadening exclusions. An index retained the locations and purposes of unfinished work and private inputs.
- Limits: This is an observed workspace shape, not a mandatory taxonomy. Monorepos and existing coherent layouts may need different boundaries. An index is neither a lock nor an authority grant.
- Proposed target: references/02-architecture-map.md
- Proposed change: Add an optional workspace-boundary row when sibling checkouts or archives affect a task. Record active checkouts, retained work, generated output and private-material boundaries without copying their contents into the map.

## ADC-LOCAL-003: Check generated consumers after moves and configuration changes

- Scope: repo-agnostic
- Lesson: Exclude generated output from broad source edits, but check the generated consumers that execute next. Autolinking and compiler caches can retain old absolute paths. Regenerate identified caches and manifests from current configuration instead of rewriting binaries or recreating obsolete folders.
- Evidence: ORG-04 reproduced a native build failure because generated autolinking still selected a dependency under the old checkout path. A native manifest also retained a removed permission-exclusion entry after an incremental generator run. Current source layout and configuration did not prove current generated output.
- Limits: Delete only identified regenerable output. Preserve signing material, private environments, manual native edits and failure evidence. This does not justify clearing all caches or forcing clean builds for unrelated changes.
- Proposed target: references/specialist-remediation-edges.md
- Proposed change: Extend the existing move sweep with a separate generated-consumer check. Identify stale paths, regenerate affected output, inspect final packaged configuration when relevant, and run the affected build or startup before declaring completion.

## ADC-LOCAL-004: Share source while separating machine-local state

- Scope: repo-agnostic
- Lesson: Synchronize reviewed source through version control while keeping dependencies, credentials, databases and generated caches local to each operating system. Record one editing owner and exact source identities with returned evidence. Offline snapshot checks must not claim fresh remote state.
- Evidence: ORG-05 used checksum-verified Git bundles when a verification host lacked repository authentication. Clean detached Windows and WSL checkouts matched the coordinator, with separate dependencies. Failed cross-OS database checks and successful same-OS checks remained distinct evidence.
- Limits: Authenticated fetch and fast-forward workflows remain preferable when available. Editing ownership is a convention, not a distributed lock. Matching source does not make clocks or provider state equivalent.
- Proposed target: references/14-deterministic-verification.md
- Proposed change: Add a compact multi-host example covering source synchronization, separate local state, refusal of dirty or unpublished work, offline limits, and returning failures as well as successes to the coordinating workspace.

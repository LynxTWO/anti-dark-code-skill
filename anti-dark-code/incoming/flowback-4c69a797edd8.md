# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.04-unified.9`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: A profiler must stop at a nested checkout

- Scope: repo-agnostic
- Lesson: A deterministic profile is only as honest as its scan scope. Agent harnesses keep linked Git worktrees inside the repository they belong to (Claude Code keeps them under `.claude/worktrees/`), and each one is a complete second checkout of some branch. A profiler that descends into them counts every file, manifest, and steering file once per checkout, and its signal detection, gate discovery, and capability selection then describe the union of several branches rather than the tree under audit. Treat any directory below the root that carries its own `.git` entry as a separate repository and do not descend, and name the harness worktree roots in the ignore rule beside the skill trees.
- Evidence: With 2026.09.04-unified.9 installed in this repository, `probe` reported 1383 files seen; the working tree holds 387 files outside `.git`, the run store, the skill trees, and build output, and 1029 more under `.claude/worktrees/`. The profile listed an `AGENTS.md` inside `.claude/worktrees/` as a second steering file and bound its one discovered gate to six solution files, four of them inside `.claude/worktrees/`. `plan` on that profile selected all 22 capabilities and deferred none, against the human-reviewed plan of 10 selected, 7 candidate, and 3 deferred. The installed `IGNORED_DIRS` set names neither `.claude` nor a nested-repository rule, and neither `probe` nor `plan` accepts an exclusion argument, so the only way to obtain an honest profile was to not run `--write`.
- Limits: One repository and one harness convention. Other harnesses may place worktrees elsewhere; the `.git`-marker rule covers those, the name rule does not. A repository that vendors another project as a plain directory without a `.git` marker is still scanned, which is the correct default.
- Proposed target: scripts/adc.py
- Proposed change: In the profiler's walk, skip any subdirectory below the root that contains a `.git` file or directory, add `.claude/worktrees` to the ignore rule, record the skipped nested repositories in the profile's scan block so the exclusion is visible, and give `probe` and `plan` an `--exclude` argument for the cases no rule can know.

## ADC-LOCAL-002: An unrecognized language is an unknown, not an absence

- Scope: repo-agnostic
- Lesson: A source-extension table is an allow-list. A language missing from it is not merely uncounted; it vanishes from the language list, contributes nothing to repo-type classification, and the repository is then classified from whatever secondary languages the table does know. A profiler that sees a large count of one unrecognized extension must report it as an unknown in the profile rather than omit it, because the omission reads as a confident inventory.
- Evidence: 2026.09.04-unified.9 recognizes neither `.vb` as a source extension nor Visual Basic .NET as a language. Its probe of this repository put 451 `.vb` files in the extension histogram of the same scan, yet reported 87 source files across C/C++, PowerShell, C++, C#, and Python, and collapsed the repo types from four to `mixed` alone. The working tree holds 147 `.vb` files outside build output and nested checkouts; the human-calibrated profile it would have replaced lists Visual Basic .NET as the primary language.
- Limits: The table gap is one line to fix. The general rule is the reporting one: any allow-list inventory should surface what it declined to count when that residue is large.
- Proposed target: scripts/adc.py
- Proposed change: Add `.vb` to `SOURCE_EXTENSIONS` and the language map, treat `.vbproj` as a .NET manifest, and emit an `unrecognized_source_extensions` note in the profile whenever an unlisted extension's count exceeds the largest recognized language.

# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.06-unified.11`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: A finding that crossed a context boundary is a hypothesis again

- Scope: repo-agnostic
- Lesson: A claim carried across a summary, a handoff, or a session boundary loses the thing that made it a finding, which is the act of having looked. It arrives as a sentence with a file and a line number attached, and it is indistinguishable in form from a claim that was verified. Treat every such claim as unverified until re-measured, and re-measure before it is written anywhere durable. The cost of re-checking is seconds; the cost of a wrong line citation in a committed document is that a reader trusts it, and the document's other claims inherit the doubt when it is found.
- Evidence: Five defects carried across a context summary were re-checked against the source before being filed. Three held exactly, and one of those turned out to be worse than recorded once the enum values behind it were read. Two did not survive: a claimed asymmetry between two encoders was absent, because both files did the same thing at the same position, and a claimed cross-thread UI write rested on a parallel construct that does not appear in the named file at all. Both had precise-looking line citations. The two refuted claims were then recorded as refuted in the same document, with what was actually found, so the same wrong lead could not be reopened later as though it were new.
- Limits: One session, five claims. The ratio is not the point and should not be quoted; the point is that form does not distinguish a remembered claim from a verified one, so the boundary crossing itself is the trigger to re-measure.
- Proposed target: references/00-conventions.md
- Proposed change: In the confidence-label guidance, state that a claim inherited across a context boundary carries no label until re-verified in the current session, and that refuted claims are recorded as refuted rather than deleted, so a wrong lead cannot return as a new one.

## ADC-LOCAL-002: An unaudited producer needs its own output root

- Scope: repo-agnostic
- Lesson: When a repository has an audited artifact tree, anything that writes there must participate in the tree's discipline, and the way a new tool acquires that obligation is simply by choosing the directory. A diagnostic, a benchmark, or a scratch recorder that writes into the audited directory has silently joined a protocol it does not implement: no lease, no invalidation, no atomic publish, and an auditor that must now either account for the file or be surprised by it. The fix is a separate output root, chosen deliberately and commented with the reason, so the next author does not "helpfully" move it back.
- Evidence: A measurement harness was written to record timings beside the gate evidence, because that is where artifacts in the repository live. It held no writer lease and was explicitly not a gate, so its first successful run placed an unaudited file inside a tree published under a shared lease and certified as a set. The path was moved to a sibling measurements root before the harness was committed, the stray file was removed, and the reason was recorded in the script beside the path so the choice reads as deliberate rather than arbitrary.
- Limits: One repository with an unusually strict evidence protocol. The general rule is weaker and still useful: the output directory is part of a tool's contract, and writing into a protected tree is an opt-in to that tree's obligations whether or not the author noticed.
- Proposed target: references/10-maintenance-harness.md
- Proposed change: In the harness-installation guidance, require that a non-gate producer declare an output root outside any audited or lease-protected tree, and that the choice be commented at the path definition.

## ADC-LOCAL-003: Enumerate the channels before reporting an absence

- Scope: repo-agnostic
- Lesson: An availability survey inherits the blind spots of whatever channel it looks at. When an ecosystem is mid-migration between distribution channels, inspecting the channel that is being abandoned yields a confident, well-cited, and wrong conclusion of absence, because the artifacts genuinely are not there. Before concluding that something is unavailable, enumerate which channels could carry it and say which were checked. An absence is only reportable as an absence when its scope is stated.
- Evidence: A survey of a plugin ecosystem's platform support found close to zero support for a target platform in the projects' release pages. The same ecosystem had been migrating distribution to a package index, where over ninety percent of the same projects published artifacts for that platform. The two channels disagreed by roughly an order of magnitude, and the release-page figure would have been reported as the answer. The clearest single case built the target platform's artifacts in continuous integration on every change and attached none of them to any release, so the artifacts existed, were current, and were invisible to the obvious survey.
- Limits: One ecosystem, one migration. The general rule is that a negative result about availability is a claim about the channels searched, and it should be written that way.
- Proposed target: references/00-conventions.md
- Proposed change: In the unknowns and evidence guidance, require that a reported absence name the sources searched, and note that mid-migration ecosystems make single-channel surveys systematically negative.

## ADC-LOCAL-004: A line-ending override plus a sweep commit rewrites the repository

- Scope: repo-agnostic
- Lesson: On a checkout whose line endings are normalized on the way in and out, a commit that both overrides the normalization setting and stages everything modified will see every normalized text file as changed and commit whole-file rewrites of them. The status view that was checked beforehand ran without the override and showed only the intended files, so the review that should have caught it was performed under a different rule than the commit. Stage explicit paths, commit without a sweep flag, let the attribute file decide line endings, and read the diff stat of every commit against its base before pushing.
- Evidence: A release commit meant to change four lines in four files was made with a normalization override and a sweep flag on a Windows checkout. The pull request then listed 58 changed files with roughly 10,000 line deltas, all whole-file line-ending rewrites of files no attribute rule pinned. The pre-commit status had shown four files. It was caught from the pull-request file list, the branch was rebuilt from the intended paths with a plain add, and the rebuilt diff was 8 files, 10 insertions, 10 deletions.
- Limits: The specific flags belong to one version-control system, but the shape, review under one rule and commit under another, is general. Repositories that pin every text path with an attribute rule are immune to this particular sweep and still benefit from the diff-stat check.
- Proposed target: references/00-conventions.md
- Proposed change: Under bounded execution and commit hygiene, require explicit staging, forbid sweep commits combined with environment overrides, and require a diff stat against the base before any push, with the 58-file rewrite as the named failure shape.

## ADC-LOCAL-005: A required job at the edge of its timeout is a flake waiting for contention

- Scope: repo-agnostic
- Lesson: A continuous-integration job whose normal duration sits within a few percent of its timeout passes alone and fails whenever runners are shared, and the failure reads as a defect in the change under review. Measure each required job's duration against its ceiling and keep at least a two-to-one margin, or split the job, before opening several pull requests at once. A timeout that has never fired is not evidence that it is generous.
- Evidence: A mutation-replay job with a 25-minute ceiling had completed in 24 to 25 minutes on every recorded run. Three pull requests opened within an hour ran it concurrently; one was canceled at 25 minutes 15 seconds with no verdict, while the same tree passed the job on another pull request. The failing pull request carried a one-file documentation proposal.
- Limits: One workflow on one hosted-runner platform. Some jobs cannot be split, and some ceilings exist to bound cost; the rule is to know the margin, not to remove ceilings.
- Proposed target: references/10-maintenance-harness.md
- Proposed change: In the harness prerequisites, add a duration-to-timeout margin check for every required job, with the concurrent-pull-request case as the trigger to review it.

## ADC-LOCAL-006: A refusal must name a repair that does not destroy something else

- Scope: repo-agnostic
- Lesson: When a guard refuses because a bound input drifted, the message names the repair the operator will run. If the named repair is a broad regeneration that also overwrites human-reviewed records, the guard has traded one loss for another, and an operator in a hurry will take the trade. Offer a targeted repair for the one binding that drifted, and keep the broad regeneration for the case where nothing reviewed exists yet.
- Evidence: Gates bound to a hash of their build files refused after a branch switch with the message to rerun the planner and re-approve. Rerunning the planner would have replaced a hand-merged verification plan and profile. The operator instead recomputed the four bindings with the tool's own hashing function from a script, recorded the previous digests and the drift, and reran the dry run; this happened twice in two days because every branch whose build files differ trips it again. No command existed for that targeted repair.
- Limits: One tool. The general rule applies to any guard whose only suggested remedy is wider than the fault.
- Proposed target: scripts/adc.py
- Proposed change: Add a `gates --rebind GATE` operation that recomputes one gate's source binding, keeps the previous digest, requires an owner note, and leaves the profile and plan untouched; change the refusal message to name it first and the planner second. Document the branch-switch case in `references/14-deterministic-verification.md`.

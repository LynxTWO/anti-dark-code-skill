# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.08.20-unified.6`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Treat "a check that cannot fail" as a named defect class

- Scope: repo-agnostic
- Lesson: An assertion that no execution can fail is worse than a missing assertion, because it reports coverage that does not exist. For every check, name a concrete, producible input that makes it fail. If none exists, the check is a defect. The recurring shapes are: a field written as a fixed literal by a producer and pinned to that same literal by a checker; an assertion comparing a value to itself, or to a constant it was already compared against; a claimed property with no probe behind it; a boolean literal asserted in place of a captured outcome; and a checker pinned to a document string that later becomes false. Once the class is named, sweep for it across the whole verification surface rather than repairing the one instance that surfaced.
- Evidence: Seven independent instances were found in one verification harness over a single engagement, each verified by reading the code and, where applicable, by mutation. Two were introduced by remediations for earlier instances of the same class, after the class had been named. One made an entire acceptance criterion permanently unsatisfiable: the producer could emit only one value and the checker required exactly that value, so an honest recording of a genuine result would have been rejected. Adversarial review rated this the slice's defining failure mode.
- Limits: Not every unfalsifiable assertion is a defect. A restatement of a property already proved by a named probe elsewhere is acceptable when the probe is cited at the restatement. The danger is the undocumented case, where a value with no probe hides among values that have one. Requiring each restatement to name its probe is the cheap discriminator.
- Proposed target: references/07-adversarial-review.md
- Proposed change: Also cross-reference from references/14-deterministic-verification.md. Add a named finding class with the five shapes above and the falsifying-input test, plus the rule that naming the class obliges a surface-wide sweep.

## ADC-LOCAL-002: A fix without a guard is a fix that can be deleted

- Scope: repo-agnostic
- Lesson: When a fix widens a detector, rule set, or matcher, add a case that fails if the widening is removed, and prove it by reverting the change and requiring the test to go red. A probe an author ran once is not a guard, because it does not run again. State this as part of the finding's own smallest-safe-step, and treat the guard as part of the fix rather than follow-up work.
- Evidence: Two remediations in one engagement were independently rejected for exactly this. In the first, a detector was correctly widened to catch a new credential form, but the only self-test case covered a form that already worked before the change; mutation proved the entire fix could be deleted with every check still green. In the second, from an earlier session, six of seven detectors were repaired and the seventh was missed while the finding recorded the work as complete. Both fixes were correct in substance and unguarded in practice.
- Limits: Applies to changes whose effect is detection or matching breadth. A behaviour-preserving refactor may not need a new case, though it still needs an existing one to exercise the path.
- Proposed target: references/11-remediation-loop.md
- Proposed change: Require every widening-class fix to ship a guard case and a recorded revert-mutation result, and add both to the acceptance checklist.

## ADC-LOCAL-003: Verify an isolation property, never trust the request that asked for it

- Scope: repo-agnostic
- Lesson: Sandboxing, isolation, and privilege-restriction interfaces can accept a request, return success, and silently apply nothing, depending on host policy. Evidence that a property was requested is not evidence that it holds. Probe the property from inside the restricted context and record the observation, not the request. When a probe cannot run, fail rather than pass, because a probe that tests nothing is indistinguishable from a passing probe.
- Evidence: A process-isolation property was requested on two hosts running the same supervisor version. On one it applied; on the other it silently did not, while the supervisor returned success both times. The difference was a distribution-default kernel hardening setting. Proven by intervention: relaxing the setting made the isolation appear and restoring it made the isolation vanish. In the same harness, a second isolation property was recorded as a fixed literal with no probe at all and was therefore unverifiable on any host.
- Limits: The probe must observe the property, not the configuration that requests it. Reading back the requested setting reproduces the original error. Some properties have no cheap in-context probe; those should be recorded as unverified rather than asserted.
- Proposed target: references/assurance-contracts.md
- Proposed change: In the native-runtime and claim sections, add an isolation-claim checklist requiring an in-context probe, an explicit failure when the probe cannot run, and a recorded observation rather than a restatement of the request.

## ADC-LOCAL-004: Keep verification artifacts out of trees that developer tooling indexes

- Scope: repo-agnostic
- Lesson: A gate that needs exclusive file access must not run inside a directory an editor indexer, search service, anti-malware scanner, backup agent, or sync client is walking. Such a tool can hold a handle without share-delete and make an unrelated gate fail intermittently, and the failure presents as a defect in the code under test. Record the exclusion as an environmental prerequisite of the gate, because a result that depends on it is not reproducible without it.
- Evidence: A cleanup step failed roughly two runs in three with a timeout deleting a single file, on identical source. Two investigations misattributed it, first to leaked child processes and then to anti-malware, and an adversarial review rejected the proposed remedy. A live capture using a handle-enumeration API named the holder: an editor language-service indexer walking the workspace, holding one cache file at a time. The single-survivor pattern matched an indexer and ruled out the process-based hypotheses. Adding a workspace exclusion resolved it, and the elapsed time of the passing gate dropped by roughly half.
- Limits: The diagnosis needs a handle-enumeration mechanism; where none is available, absence of a user-mode holder is itself evidence pointing at a kernel filter. The exclusion is a property of the developer environment and cannot be enforced from inside the repository, so it must be documented as a prerequisite rather than assumed.
- Proposed target: references/10-maintenance-harness.md
- Proposed change: Add environment contention to the harness prerequisites, with the guidance to identify the holder before proposing a timing remedy, and to record any required exclusion alongside the gate.

## ADC-LOCAL-005: A sequence of passing producers is not audited evidence

- Scope: repo-agnostic
- Lesson: Producers passing in sequence and an audit certifying them as a set are different claims, and only the second supports a release decision. Treat any producer record written after an audit attempt as unaudited. Where an audit emits an artifact, require that artifact on disk before describing a set as passing, and require every producer record to predate it.
- Evidence: A set of producer gates was reported as "passing together" while the audit artifact had never been written and one producer record had been regenerated twenty-six minutes after the audit failed. The same report quoted check counts that did not match the files on disk, and one gate's count varied across runs, so no single number described it. An independent review identified the absence of the audit artifact, rather than any individual defect, as the decisive reason the set could not be accepted.
- Limits: Applies where an audit or correspondence step exists and emits a durable artifact. Where none exists, the equivalent discipline is to record the ordering and completeness of the run explicitly, since no artifact can carry it.
- Proposed target: references/00-conventions.md
- Proposed change: In the evidence and negative-search section, define audited-set evidence separately from per-gate evidence, and add the rule that a record written after an audit attempt is unaudited.

## ADC-LOCAL-006: Verify that review is complete, not that it says it is complete

- Scope: repo-agnostic
- Lesson: A checker satisfied by editing the artifact it checks is a ritual, not evidence. Binding closure to a version stamp, status word, or single declarative line lets one keystroke on the reviewed document turn a whole verification green while its body still records the opposite. Verify substantive properties instead: no finding left in an open state, no unresolved verdict language in the document, and a hash binding so any edit is visible. Where a document must be scanned for an unresolved verdict, distinguish a live claim from an accurate historical record, so closing the check never requires deleting true history.
- Evidence: An evidence auditor pinned one literal version line as its only review-closure signal. The pinned constant had also gone stale, so satisfying it would have required decrementing a version number on a document whose body reported rejection. Replacing it with substantive checks immediately exposed a further defect in the replacement: the first version scanned only one section, and the document's live verdict lived in another, so the new check passed over a document that still declared the work unaccepted. Tense proved a reliable discriminator between a live verdict and a historical one in the same document.
- Limits: Substantive checks need a stable vocabulary for statuses and section structure. Where a project has no such convention, the first step is to establish one, not to add the check.
- Proposed target: references/assurance-contracts.md
- Proposed change: In the publication and claim sections, add a self-certification anti-pattern with the substitution above, including the requirement that closure checks must not be satisfiable by editing the checked artifact.

## ADC-LOCAL-007: A value produced in a child context must cross the boundary as an artifact

- Scope: repo-agnostic
- Lesson: When verification runs part of its work in a separate process, container, sandbox, or job, values computed there are invisible to the parent unless they cross as a file, stream, or structured result. An in-memory assignment silently leaves the parent holding its initial value. Follow whatever handoff mechanism the surrounding code already uses, and have the reader validate the received value rather than assume it arrived.
- Evidence: A newly added probe assigned its result to a variable inside a supervised child context while the consumer ran in the parent. The consumer therefore always saw the initial placeholder and refused to publish, which would have made the gate unable to succeed at all. Every other result in the same script already crossed the boundary as a file; the new one did not. The defect was found by review before the gate ran, so the author never observed it.
- Limits: Obvious once stated, and easy to miss when adding a value to code that reads as one continuous script. The reliable check is to trace the value from where it is produced to where it is read and confirm the two points are in the same process.
- Proposed target: references/14-deterministic-verification.md
- Proposed change: Add a boundary-handoff caution to the gate-authoring guidance, with the trace rule and the instruction to reuse the existing handoff mechanism.

## ADC-LOCAL-008: Anchor repository identity to immutable history, and report which component failed

- Scope: repo-agnostic
- Lesson: Repository identity should be anchored to something the repository cannot change casually, such as its root commit set. A remote URL is mutable and legitimately changes with a protocol switch, rename, mirror, or fork, so a binding that leans on it will report a mismatch for a repository that is plainly the same. When a binding has several components, report which one failed, because "binding mismatch" otherwise conflates "this is a different repository" with "you changed how you clone it". The first must stop a flow-back; the second should refresh the binding and continue.
- Evidence: A binding check failed on its remote-URL component while the root-commit component matched exactly, in a repository whose history was demonstrably continuous. Treating the combined result as a stop condition would have discarded valid local learning; treating it as a pass would have skipped a real staleness signal. Distinguishing the components resolved it without weakening either safeguard.
- Limits: Root commits are stable but not universally unique: forks share them by design, so they establish continuity rather than exclusivity. A binding should keep both signals and weigh them differently rather than replacing one with the other.
- Proposed target: references/15-dogfeeding-flowback.md
- Proposed change: Update the reference and the binding logic in the bundled script. Require per-component binding results, treat a root-commit match as continuity, treat a remote-URL mismatch alone as a refresh trigger rather than a stop condition, and stop only when the immutable component disagrees.

## ADC-LOCAL-009: Revert-mutation proofs need a committed baseline

- Scope: repo-agnostic
- Lesson: A revert-mutation proof restores the code by version-control checkout, and checkout cannot restore a file the version control does not yet track. Running mutation proofs on a brand-new unit before its first commit leaves every mutation silently in place while the operator believes it reverted. Either commit the unit before the proofs, or close every proof session with a full green run, which converts a silent failed revert into a loud test failure.
- Evidence: Three mutation proofs on a new, uncommitted unit each produced the expected red, and each checkout-based revert failed with an unknown-pathspec error that scrolled past unnoticed. The mandatory restored-state green run then failed, exposing that all three mutations were still present; restoration was completed by inverse edit and verified green. The closing green run is what contained the damage.
- Limits: One incident. The closing-green-run discipline is the load-bearing half and is cheap everywhere; the commit-first half trades commit granularity for revert safety and teams may reasonably differ.
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, require either a committed baseline before revert-mutations or a mandatory full green run after restoration, and state why checkout is not a revert for untracked files.

## ADC-LOCAL-010: Whole-record equality over collection members is a hidden reference comparison

- Scope: repo-shape:managed-desktop
- Lesson: In runtimes where a record or value type delegates member equality to the default comparer, a collection-typed member compares by backing reference, so a whole-record equality between two separately built instances can never pass even when every element agrees. An assertion built on it reports false divergence, and its inverse, an inequality guard, is a check that cannot fail. Compare structured payloads per section, with sequence equality over the collections and value equality over the leaves.
- Evidence: A cross-version stability assertion compared two normalized payload records whole; it failed while every field agreed, because the payload's immutable-array members compared by reference. Rewritten per section with sequence equality, the same data passed, and the sectioned form also names which section diverges when one truly does.
- Limits: One incident, in one runtime family. The general shape, default equality silently comparing references inside an assertion, appears in several managed runtimes but the candidate is scoped to the shape it was proven on.
- Proposed target: references/14-deterministic-verification.md
- Proposed change: Add a caution to the gate-authoring guidance: equality assertions over structured payloads must state what the comparer actually compares, and collection members need sequence comparison, not container equality.

## ADC-LOCAL-011: An implicit restore is a silent mutation of audited dependency state

- Scope: repo-agnostic
- Lesson: Where dependency lock files are audited evidence, a routine build that implicitly restores can rewrite them for the build's own narrower context, for example dropping a cross-compilation target the audit requires, and the damage travels into the next commit unnoticed. Local builds in such a repository must run with restore disabled, and restore must happen only through the reviewed path that validates the locks. The cheap tripwire is any version-control status check after a build: a modified lock file after a supposedly read-only build is the alarm.
- Evidence: A test build without the no-restore flag rewrote five lock files, removing the cross-target sections the final dependency audit derives its closure from, and the rewritten locks were committed. The commit's own file list exposed them; the repair restored the audited versions, and the reviewed locked-mode restore gate then passed its full check count against them without rewriting, proving the restored state and the gate agree.
- Limits: One incident, one package manager. The general mechanism, a build tool mutating its own declared-state files as a side effect, exists across ecosystems, but the flag names differ and some ecosystems make lock rewriting opt-in rather than default.
- Proposed target: references/10-maintenance-harness.md
- Proposed change: Add audited dependency state to the harness prerequisites: name the no-restore or equivalent flag for local builds, route all restores through the reviewed gate, and add the modified-lock-after-build tripwire to the review checklist.

## ADC-LOCAL-012: A remediation must fix exactly the set the gate names

- Scope: repo-agnostic
- Lesson: When a gate names the artifacts that violate a rule, the fix must target that named set and nothing wider. A remediation loop that re-derives its own candidate set, for example "every changed file", silently re-implements the gate's file classification without the gate's exclusions, and applies a text rule to artifacts the gate deliberately exempted. Binary artifacts under a text rule are the sharp case: they almost never satisfy a trailing-newline or encoding invariant, so a sweeping fixer mutates them every time, and hash-pinned fixtures are corrupted by exactly the two bytes the fixer believed were a repair.
- Evidence: A whitespace gate failed naming one markdown file lacking a final newline. The repair iterated all changed files instead and appended a newline terminator to any file not ending in one, which appended two bytes to three binary media fixtures whose hashes are recorded in a committed manifest. The corruption was committed and pushed before being noticed; restoration from the committed originals re-verified all four fixture hashes against the manifest. The gate itself had classified correctly and flagged only the text file.
- Limits: One incident. The narrow rule, fix only what the gate names, trades off against genuinely proactive cleanup; where a wider sweep is intended, it must reuse the gate's own classifier rather than approximate it.
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the fix-application guidance, require the fix set to equal the finding set, and state that any wider sweep must invoke the gate's classification logic rather than re-derive it.

## ADC-LOCAL-013: A mutation proof that hangs is a defect in the code, not the proof

- Scope: repo-agnostic
- Lesson: A revert-mutation proof expects red; a third outcome exists: the suite never finishes. When a mutation neutralizes a safety action, any unbounded wait downstream of that action, a reap, a join, a drain, converts the neutralization into a hang, and a hang is worse evidence than a pass because it also blocks every later proof. The hang is not a flaw in the mutation exercise; it is the exercise finding that the system's failure handling depends on the very action being tested, with no bound behind it. The fix is in the product: bound every cleanup wait and surface expiry as a typed failure, which simultaneously makes the mutation observable as ordinary red.
- Evidence: Neutralizing a process-tree kill did not turn the harness red; the suite wedged behind a child blocked writing to a full pipe while the reap waited on it without a bound, and an external timeout had to kill the run. Bounding the reap and surfacing a surviving child as a typed reason class made the same mutation fail the suite cleanly in seconds, and the bound is unreachable when the kill works.
- Limits: One incident. Bounding a cleanup wait needs a bound chosen honestly: long enough that expiry cannot occur in legitimate operation, or the typed failure becomes a new flake source.
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, name the hang as the third proof outcome, require it to be treated as a product defect in cleanup bounding, and require cleanup waits downstream of any mutated safety action to be bounded and typed.

## ADC-LOCAL-014: A surviving mutant demands a diagnosis, and the diagnosis is a finding

- Scope: repo-agnostic
- Lesson: When a mutation survives, the possibilities are a missing test or an equivalent mutant, and both are findings, never noise. An equivalent mutant means the mutated code was not load bearing on any observable path: a dead branch, or a check whose refusal is silently duplicated by a neighboring mechanism. Leaving the code as written after such a diagnosis records a claim the code does not keep; the honest close is to rewrite the code to say what is actually true, delete the dead branch, document which mechanism really owns each behavior, and re-prove with a mutation that is load bearing. A guard that survives mutation because a neighbor masks it will also mislead every future reader about where the enforcement lives.
- Evidence: Two mutations of a filesystem probe both survived a corpus that genuinely exercised the mutated behaviors. Diagnosis showed one refusal branch was unreachable, the platform's existence test already refuses directories, and one masked, a missing file reads its attributes as all bits set, so a later attribute refusal also refuses absence. The probe was rewritten to name the true mechanisms, the dead branch deleted, and the surviving proof, a verdict flip, went red correctly.
- Limits: One incident. Distinguishing equivalent mutants from missing tests requires reading the runtime's actual semantics, not re-running the suite harder; the diagnosis cost is real and worth budgeting.
- Proposed target: references/11-remediation-loop.md
- Proposed change: In the guard-and-mutation guidance, add the surviving-mutant rule: every survivor is dispositioned in writing as missing-test or equivalent-mutant, equivalent mutants trigger a rewrite that removes the dead or masked claim, and the unit is not done until a load-bearing mutation goes red.

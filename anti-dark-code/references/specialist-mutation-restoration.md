# Mutation evidence and restoration

Trigger: mutation testing or a revert-fix proof is selected to challenge a guard.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

Start with the smallest high-stakes pure semantic module that has a stable oracle. Record source lines, test count, mutant count, elapsed time, survivors, no-coverage mutants, timeouts, and errors before expanding scope.

Keep semantic decisions separate from presentation catalogs, labels, descriptors, and compatibility metadata. Mutating a display-only declaration can create equivalent or low-value mutants that inflate the denominator. Test catalog shape directly, but target mutation gates at behavior whose changed outcome can be falsified.

Report absolute counts beside the score. A perfect score over a tiny denominator is narrow evidence, while a lower score may be dominated by equivalent or no-coverage mutants. Classify each survivor as missing assertion, missing reachability, equivalent mutation, excluded presentation surface, timeout, or tool error before changing thresholds.

Treat unexpectedly fast incremental mutation runs as suspect after fixture-only or data-only test edits. Clean the mutation cache and rerun when the tool cannot prove that test content invalidated prior verdicts.

Typecheck newly authored test batteries separately when the runner transpiles without type information. Passing transformed tests can still assert against shapes the production type system rejects.

## Revert proof

A guard is proven by a controlled failure, not by a green run. When stakes justify it, run a revert-mutation proof: undo the fix, watch the guard go red, restore the fix, watch it go green.

- Run the proof against a committed baseline. Version control cannot restore a file it does not track, so on a brand-new unit the restoring checkout fails with an unknown-pathspec error and the mutation stays in place while the operator believes it was reverted. Commit or otherwise durably preserve the unit before the first mutation, and close every proof session with a full green run on the exact tree that will ship.
- Expect three outcomes, not two. The suite can go red, stay green, or never return. A hang is worse evidence than a pass, because it also blocks every later proof. It is not a flaw in the exercise; it is the exercise finding that the system's failure handling depends on the action being neutralized, with no bound behind it. Fix it in the product: bound every cleanup wait downstream of a mutated safety action and surface expiry as a typed failure, not as a silent stall. A bound chosen honestly cannot expire in legitimate operation, and it makes the same mutation show up as ordinary red in seconds.
- A surviving mutant demands a diagnosis, and the diagnosis is a finding. There are two possibilities, and they are not the same: a missing test, or an equivalent mutant. An equivalent mutant means the mutated code was not load bearing on any observable path, either a dead branch or a check whose refusal is silently duplicated by a neighboring mechanism. The honest close is to rewrite the code to say what is true: delete the dead branch, document which mechanism really owns each behavior, and re-prove with a mutation that is load bearing. The unit is not done until a load-bearing mutation goes red. Write the classification down rather than letting the survivor disappear.

## Required safety and closure

Preserve every affected tracked and untracked file durably before mutation; record original byte hashes and restore in an unconditional finally/exit path. A committed baseline is sufficient only for tracked files. Never use a destructive checkout that overwrites unrelated local work. Keep cleanup bounded, preserve producer exit status, and prove restored bytes match before the final green run on the exact deliverable tree.

A widening fix ships a guard for the newly caught form, with a pre-fix red run and post-fix green run. A one-off probe is not a recurring guard. Repair exactly the gate-named set; a wider sweep must use the gate classifier and its exclusions. Record survivors as missing assertion, missing reachability, equivalent mutation, excluded presentation surface, timeout, or tool error. Equivalent mutants need a code/ownership diagnosis and an actually load-bearing mutation, not an unexplained waiver.

Result: restored source identity and a final green run accompany every completed proof; survivors and hangs remain explicit findings until diagnosed.

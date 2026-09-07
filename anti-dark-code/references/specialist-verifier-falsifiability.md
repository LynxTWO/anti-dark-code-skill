# Falsifiable verifiers and canonical output

Trigger: a test, detector, closure check, equality comparison, or canonical-output claim may accept evidence that cannot expose the defect.

Apply the [core contract](../SKILL.md) and [evidence rules](../SKILL.md#evidence). This recipe inherits the active task and grants no additional authority.

An assertion that no execution can fail is worse than a missing assertion, because it reports coverage that does not exist. Treat one as a finding, not a style nit.

The recurring shapes, in the order they tend to surface:

- a field written as a fixed literal by a producer and pinned to that same literal by a checker
- an assertion comparing a value to itself, or to a constant it was already compared against
- a claimed property with no probe behind it
- a boolean literal asserted in place of a captured outcome
- a checker pinned to a document string that later becomes false
- a tolerance or threshold wider than the reachable range, or a matcher that accepts every candidate

The test for the class is the falsifying input: name the concrete, producible input or state that would make the check fail. A check whose author cannot name one gets rewritten or removed. In the sharpest form of this defect the producer can emit only one value and the checker requires exactly that value, which makes the acceptance criterion permanently unsatisfiable and would reject an honest recording of a genuine result.

Sweep the whole verification surface once the class is named, and re-sweep after remediating it.

The exception is a deliberate restatement of a property already proven elsewhere. Such a restatement must cite the probe that proves it, at the restatement. Deterministic gates share this rule; see the gate-authoring cautions in `14-deterministic-verification.md`.

## Canonical output

Ordering keyed on a parsed or normalized value is not total over raw representations. Two distinct raw spellings can parse equal (a timestamp with a different offset, a number with trailing zeros, a case-folded key), so a shuffle-stability test can pass while output order inside the equal class still follows input order. Tie-break canonical comparators on the raw representation after the parsed comparison, or reject equivalent-but-distinct representations at the input boundary, and never let the choice fall through silently. Every determinism suite includes a fixture pair of distinct raw representations of one parsed value and requires byte-identical canonical output across shuffles.

## Equality and handoffs

Collection-bearing records may compare references instead of contents. Compare canonical serialized forms or elements; retain a structurally equal, reference-distinct fixture. Child process/container/shell results must cross the boundary as an artifact, exit code, or serialized stream. Prove the handoff fails when its artifact is missing.

Detector thresholds need clean and known-bad fixtures, a documented separating rationale, and a positive fixture that crosses the threshold. Review threshold changes as behavior changes.

Result: every check has a concrete producible falsifier, negative fixtures exercise comparisons and missing handoffs, and canonical-output tests include equal parsed values with distinct raw forms.

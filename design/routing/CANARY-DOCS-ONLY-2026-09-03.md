# Canary: the docs-only class, 2026-09-03

**This branch is never merged.** It exists to prove that the shadow
comparator can see a failure for the `docs-only` route class, which is
SLICE-002's guard G8: before a class's clean count means anything, the ledger
must hold one record for that class where an omitted gate failed and the
comparator said so.

## What this change is

One new Markdown file under `design/routing/`, which the shipped classifier
maps to `docs` and `prose`. Under the proposed rules, that routes `docs-only`:
Level 0, selecting `validate-core` alone and omitting `distribution`,
`full-suite`, `hostile-environment`, and `mutation-replay`.

## What it breaks, deliberately

The line below cites a decision that does not exist. D-090 requires every
decision id cited anywhere under `design/routing/**/*.md` to resolve to a real
heading in the decision log, and the test that holds it,
`test_every_referenced_decision_exists`, runs inside the suite. The suite is
`full-suite` and the hostile-environment jobs, both of which the `docs-only`
route omits. The validate step it does select reads only the skill tree and
passes.

The deliberate citation: see D-999.

## What the record should say

`status: miss`, `provenance: canary`, derived from this branch's name rather
than from any label, with `full-suite` and `hostile-environment` in
`missed_gate_ids` and `validate-core` passing. If instead it reads `clean`,
the comparator cannot see failures for this class and no clean count for it
means anything.

## Why this was expected before it was run

The SLICE-002 design challenge found it by reading, not by running: the
suite's own decision guard reads the design documents that the `docs-only`
route would skip the suite for. The owner's decision of 2026-09-03 was to let
the canary record the miss rather than narrow the classifier first, so that
the narrowing is decided on evidence. This file is that evidence.

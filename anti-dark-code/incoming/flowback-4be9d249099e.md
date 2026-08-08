# Anti-Dark-Code Flow-Back Proposal

Source repo identity: `279f97277b71eccd5d9375aa47325b25d40200c1`
Installed skill version: `2026.08.06-unified.4`

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-012: Pilot mutation testing on the smallest highest-stakes pure files first

- Scope: repo-agnostic
- Lesson: A mutation pilot scoped to a few hundred lines of pure, high-stakes functions (this repo: clock, rng, receipt ordering, hash; 217 lines, 149 mutants, 5 minutes) calibrates real runtime cost AND finds untested surface immediately, because pure kernels are usually only tested through their consumers. First run here: 31 survivors + 14 no-coverage, including an input path that would crash. The kill battery that closes them doubles as an exact-value regression pin on the determinism kernel.
- Evidence: 2026-08-07 Stryker pilot, 79.2% -> 97.3% (100% of killable), 16 tests, 1.4s battery cost
- Limits: single repo; per-module scoping is what kept it cheap, whole-repo first would have hidden the signal in cost
- Proposed target: deterministic-verification reference (V01 guidance)
- Proposed change: a "start with the smallest highest-stakes pure module" paragraph with the cost math

## ADC-LOCAL-013: Mutation-tool incremental caches can serve stale verdicts after fixture-only test edits

- Scope: repo-agnostic
- Lesson: Stryker's incremental mode reused prior kill/survive verdicts after a test file's fixture DATA changed without any test names changing; the run finished suspiciously fast (36s vs 89s) and reported survivors the updated tests provably kill. A clean-cache run confirmed the kills. Treat a too-fast incremental run as a signal, and clean the cache whenever test content changes without name changes.
- Evidence: 2026-08-07 pilot runs 2 vs 3 vs clean; receiptOrdering comparator mutants
- Limits: observed on Stryker 9.6.1 + jest runner; may be version-specific
- Proposed target: deterministic-verification reference (V01 guidance)
- Proposed change: one caveat line next to any incremental-mode recommendation

## ADC-LOCAL-014: Verify a gate by its exit code, never by grepping its output

- Scope: repo-agnostic
- Lesson: A pipeline like `npm run gate 2>&1 | tail -2` returns the exit status of `tail`, not the gate, so a failing gate reads as success. This is the same masking class as the already-recorded `npm test | tail` trap, but it bit again through a different shape (grep/head in a summary pipeline) during an autonomous run, and a commit was pushed that failed the repo's own gate. The durable fix is a rule about the shell contract, not about one command: capture output to a file, read `$?` from the command itself, or use `set -o pipefail`.
- Evidence: 2026-08-08 mutation campaign; 416 green tests hid 42 TypeScript errors because jest transforms do not typecheck, and the typecheck failure was masked by a grep pipeline in the verification step
- Limits: none known; applies to any harness that reports gate results through a shell pipeline
- Proposed target: the deterministic-verification reference, next to the existing exit-code semantics section
- Proposed change: state the shell contract explicitly (pipelines return the last command's status) and require exit-code capture in any documented verification recipe

## ADC-LOCAL-015: Transform-based test runners do not typecheck their own tests

- Scope: repo-agnostic
- Lesson: With babel- or swc-style transforms (jest-expo, ts-jest in isolatedModules, vitest esbuild), a test suite can be fully green while its test files contain type errors: optional values dereferenced without guards, literals outside a union, object literals missing required fields. Newly authored test batteries should be typechecked separately before they are trusted as evidence, because a test that does not typecheck may be asserting against a shape the production code never produces.
- Evidence: 2026-08-08, 17 mutation battery suites at 416 passing tests carried 42 tsc errors
- Limits: only applies where the runner transpiles without type information; a tsc-based runner would have caught these at authoring time
- Proposed target: deterministic-verification reference (test-change policing capability)
- Proposed change: add a line requiring a typecheck pass over new test files as part of accepting AI-authored tests as evidence

# Reference: Combined 03 + 06 Loop (Critical-Path Comments with Hygiene)

Use this reference when you want a slice-by-slice comment loop that adds explanatory comments and immediately cleans the touched text before each commit.

**Mode:** comment-only on application code, text-only cleanup on touched docs and summaries.

This is a runnable loop, not a numbered pass. It is useful when the next best move is comment-only clarification rather than behavior changes.

## Goal

Run `03-critical-path-comments.md` and `06-writing-hygiene.md` together on a single slice so the comments land, the text stays clean, and the commit boundary stays tight.

## How the loop runs

1. Pick the next slice from the coverage ledger.
2. Read `03-critical-path-comments.md` and apply its rules to that slice only.
3. Read `06-writing-hygiene.md` and apply its rules to every touched comment, doc, unknowns file, and task summary.
4. Commit the slice as one bounded unit.
5. Update the coverage ledger and `docs/unknowns/critical-paths.md`.
6. Repeat on the next slice.

If the slice involves language, locale, authored content, generated prose, or saved text, also check `12-transcreation-boundary.md` before writing comments.

## Bounded execution

- review checkpoint every 10 commits
- hard stop after 20 commits unless the user says continue
- stop sooner if the slice touches a protected area, reveals stale maps, or turns into something bigger than comment-only clarification
- stop sooner if evidence goes soft or a map turns out to be out of date

## After each slice, return

- what code path was clarified
- which invariants or edge cases the new comments explain
- which language boundaries the new comments protect, if any
- what remains unclear
- which next slice should run
- whether the repo is still in comment-only mode or now needs a behavior-preserving cleanup pass

## Do not

- bundle multiple slices into one commit
- edit logic, control flow, imports, signatures, dependencies, or config
- touch generated, vendored, mirrored, minified, serialized, or engine-owned artifacts
- alter toolchain-sensitive comments (pragmas, linter directives, type-affecting docblocks, SQL hints, engine metadata)
- rewrite a comment into a vague restatement
- let hygiene cleanup drift into content changes that were not the original intent

## Rationale

Running 03 then 06 back-to-back on one slice keeps the commit reviewable, keeps the text voice consistent, and prevents "clean-up passes" from smearing across the repo. It also avoids a common failure mode where an agent adds comments, moves on, and the text never gets the tone pass.

This loop is the only sanctioned interleave under the "no parallel passes" rule in `SKILL.md`. It works because `06` is text-cleanup of work `03` just produced, not a separate pass with its own deliverable.

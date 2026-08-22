# Mutation findings: adc.py high-stakes modules

First mutation pilot on this repository's own tooling, run with `tools/mutation_harness.py`.
Targets were chosen the way this skill tells other repositories to choose them: the smallest
high-stakes modules with a stable oracle, not the whole file.

Every survivor below is classified. A surviving mutant is either a missing test or an
equivalent mutant, and the two demand different responses.

## Round 1: digest, provenance, and release-notes logic

Targets: `core_digest`, `managed_source_files`, `assess_source_provenance`,
`only_version_churn`, `changelog_section`.

| | mutants | killed | survived |
|---|---|---|---|
| before | 32 | 21 (66%) | 11 |
| after | 31 | 27 (87%) | 4 |

Tests added, each written after watching the mutant survive:

- `test_managed_source_files_never_follows_links_into_the_distributed_core` - a symlinked
  directory and a symlinked file inside a source core must not be packaged.
- `test_only_version_churn_edge_cases` - an empty version set dismisses nothing, and a file
  whose diff carries no content lines (a mode change) is not reported as undescribed.
- `dirty` assertions added to the provenance test for all four source kinds.

One mutant was removed from the harness rather than the code: `return None` mutated to
`return None` is a no-op that always survives, and a harness that manufactures a false
finding teaches its reader to skim the survivor list.

### Equivalent mutants, with the mechanism that really owns the behavior

- `managed_source_files`: `os.walk(..., followlinks=False)` flipped to `True`, and the
  `d not in excluded_here and not path_is_linklike(...)` filter flipped to `or`. Each
  survives **because the other exists**: the directory filter prunes link-like entries
  before the walk can descend, and `followlinks=False` prevents descent even if a
  link-like directory were listed. Single-order mutation cannot see a guard that is
  covered by a second guard. This redundancy is deliberate for a security-relevant path
  and should not be "simplified" on the strength of a surviving mutant.
- `managed_source_files`: the `r.startswith("calibration/") or r.startswith("incoming/")`
  file filter flipped to `and`. No path starts with both prefixes, so `and` excludes
  nothing, yet the result is unchanged because the top-level directory exclusion and the
  `rel_dir.parts[0]` check both already prevent those files from being reached. Third
  layer of the same defense.
- `only_version_churn`: `return False` flipped to `return None` on the empty-version-set
  guard. Both values are falsy and the result is only ever consumed in a boolean test.

## Round 2: the redaction and parsing path

Targets: `redact_line`, `sanitize_for_proposal`, `replace_path_variants`,
`repository_name_variants`, `parse_candidates`. This is the highest-stakes surface in the
repository: a miss here puts a private path, a project name, or a secret into a proposal
that gets published as a public pull request.

| | mutants | killed | survived |
|---|---|---|---|
| before | 17 | 9 (53%) | 8 |
| after | 17 | 16 (94%) | 1 |

The most consequential finding: in `repository_name_variants`, mutating
`token.lower() not in generic` to `in` meant only generic words became redaction targets,
so **real project names would have stopped being redacted** and nothing failed. That is a
privacy leak with no test standing in its way.

Tests added:

- `test_parse_candidates_handles_a_missing_file_and_multiple_entries` - a missing file
  returns an empty list, and three candidates parse with correct per-entry boundaries.
  This is the function that once shipped a silent truncation bug; its section boundaries
  are now pinned.
- `test_replace_path_variants_prefers_the_longest_match_and_ignores_root` - a nested path
  is consumed whole, and the filesystem root is never treated as a replaceable variant.
- `test_repository_name_variants_keeps_real_tokens_and_drops_generic_ones` - a distinctive
  token survives, generic words and short tokens do not, the five-character threshold is
  pinned from both sides, and a short non-generic token stays out so both halves of the
  length-and-generic rule are load bearing.
- `test_sanitize_for_proposal_redacts_without_explicit_names` - redaction still works when
  the caller does not pass an explicit name list, which every prior test did.

### Equivalent mutant

- `replace_path_variants`: `sorted(..., key=len, reverse=True)` flipped to `reverse=False`.
  The three variants are one resolved path with its separators swapped, and separator
  substitution preserves length, so the three are always the same length and sort order
  cannot change the result. The longest-first intent is sound defensive coding for a case
  the current variant set cannot produce; it is kept rather than deleted so a future
  variant of a different length is handled correctly.

## How to reproduce

```bash
python3 tools/mutation_harness.py --repo . \
  --target anti-dark-code/scripts/adc.py \
  --function core_digest --function managed_source_files \
  --function assess_source_provenance --function only_version_churn \
  --function changelog_section \
  --test test_adc.AntiDarkCodeToolsTests
```

The harness copies the repository into a scratch tree before mutating, bounds every mutant
with a timeout, reports a hang as its own outcome, and refuses to report anything at all
unless the unmutated suite passes first.

## Round 3: fuzzing the untrusted input boundary

`validate_flowback_proposal_bytes` is the only function here that reads a file written by a
stranger. Proposals arrive as pull requests, and this repository's own README says skill text
becomes instructions executed by an assistant with its operator's authority. That pairing is
why this boundary is fuzzed rather than sampled.

Harness: `tools/fuzz_proposal_validator.py`, standard library only, deterministic by seed. It
checks four invariants, each a real failure mode:

- **I1 never raises.** A crash on hostile bytes is a denial of service against contributors'
  pull-request checks, and an exception escaping into a broad handler can read as a pass.
- **I2 never hangs.** The validator runs several regular expressions over attacker-controlled
  text, and catastrophic backtracking is the classic way a validator becomes a weapon. Bounded
  with a real interval timer, because backtracking does not yield to a thread timeout.
- **I3 fails closed.** Anything that is not byte-for-byte a known-good proposal must produce at
  least one error. An empty error list means accepted.
- **I4 can still say yes.** A known-good proposal must validate clean, or the other three
  invariants are satisfied by a validator that rejects everything and proves nothing.

Result: **19,000 inputs across five seeds, zero failures.** No crash, no hang, nothing junk
accepted. Strategies covered bit-flips and splices of a valid proposal, uniformly random bytes,
truncations, filename attacks including traversal, and an adversarial fragment set: terminal
escapes, bidirectional overrides, zero-width joiners, homoglyph domains, credential shapes,
private-key headers, HTML and image embeds, disallowed URI schemes, NUL bytes, invalid UTF-8,
oversized lines, and nested groups chosen to provoke backtracking.

The harness earned its I4 invariant immediately: the inbox also holds a hand-written local-mode
proposal, which is legitimately not a valid public submission. Treating it as a control produced
a false failure, so seeds are now selected by validating them first.

A bounded, self-contained version runs in the suite as
`test_proposal_validator_survives_hostile_input`, generating its control through the real
`flowback` path so the test does not depend on inbox contents.

One finding landed against this repository rather than the validator: an early fixture embedded
a literal personal-looking absolute path, and the skill's own personal-path detector correctly
flagged its distributed source. The fixture now assembles that string at runtime.

## Round 4: fault injection on gate termination

`run_gates` executes reviewed commands with a timeout and claims **process-tree** termination.
`references/assurance-contracts.md` requires that a claim be proven by observation rather than
asserted, so it is.

Three injected faults:

- **A gate that never returns** must fail on its bound and be recorded as exit `124`, not wait.
- **A gate that spawns a background process and then hangs.** This is the shape that separates
  process-tree termination from child termination: killing only the direct child leaves the
  grandchild running, and it keeps running after the gate is reported failed. The test waits past
  the grandchild's own sleep and asserts its marker file was never written.
- **A gate that ignores `SIGTERM`.** Polite termination is a request; the bound has to hold when
  it is refused, so the run must still finish and record `124`.

All three pass. More usefully, the orphan test was proven to have teeth: replacing
`os.killpg(pgid, ...)` with `proc.terminate()` and `proc.kill()` in a scratch copy makes it fail
with `a grandchild outlived the timed-out gate: the process tree was not terminated`. A
termination test that has never been watched failing is indistinguishable from one that asserts
nothing.

## Not yet covered

The binding functions (`compute_repository_binding`, `assess_repository_binding`) have not been
mutated. Windows process-tree termination through `taskkill` is untested here; the POSIX path is
proven and the Windows path remains `inferred`. A gate that deliberately detaches from its
process group with `setsid` is a documented limitation rather than a defect, and is not asserted
either way.

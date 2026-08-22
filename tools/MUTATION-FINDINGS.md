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

## Not yet mutated

`run_gates` and the process-termination path, the binding functions, and
`validate_flowback_proposal_bytes`. The proposal validator is the repository's untrusted
input boundary and deserves fuzzing rather than mutation alone.

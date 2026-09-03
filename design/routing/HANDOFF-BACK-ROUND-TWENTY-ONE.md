# Handoff back: round twenty-one

Date: 2026-09-02. Agent: Claude. Base: `de5ef1d`, main after PRs #21 through #31 landed. Branch: `claude/round-twenty-one-verify`, PR #32. Implementation head: `fe350e9`. This is the one verifying round D-116 gives a router change, opened under its condition (c) because D-118 changed the router's canonical classifier, and it stops when it closes.

## 1. Terminal outcome

- **D-118 is implemented and held.** The canonical scripts authority entry is now `anti-dark-code/scripts/*.py` and `**/anti-dark-code/scripts/*.py`, in the router's contract, the shipped template, and this repository's installed policy. The five consumer paths D-107 measured route as product code at Level 2; every shipped script forces full in the source spelling and under each of the four installed prefixes; a root-level `scripts/deploy.py` stays unmapped and full. One new test holds the width, M100 is re-anchored, and M115 and M116 hold the two spellings.
- **D-107 is decided.** The owner chose option 2 in the SLICE-001 walkthrough; the log records it and D-100 is amended by D-118.
- **Both hosts' records are current at `fe350e9`.** Section 4.
- **Three fresh-context challengers, and a cap.** The first broke D-118 at `6930274`, the second broke D-119's stated property at `5872e92`, and the third upheld D-120 on NTFS with real git at `38cdff8` and found the fold set's two edges and three test gaps, which D-121 closes. There was no fourth: the owner asked that the round not chase its tail, and a fourth attack on a repair of a repair, on a property whose remaining unknowns are filesystems no host here can measure, is that. D-121's repairs are held by tests and by rows measured to fail. Sections 3 and 6.
- **The D-116 conditions at this head.** Section 6.
- No routing rule was approved, selective execution stays disabled, and SLICE-001, marked Done by the owner before this round, is unchanged.

## 2. Where this round started

The owner ran the SLICE-001 walkthrough on 2026-09-02 from a fresh default clone at `3e04422`, answered all seven questions yes, named D-107 option 2 as the follow-up under Question 6, and checked the last box. PRs #21 through #30 landed on main in order with merge commits, PR #31 marked the slice Done and moved the build boundary to SLICE-002, and main's run at `de5ef1d` passed every job. Round twenty's `HANDOFF-BACK-ROUND-TWENTY.md` has the D-107 measurement this round implements.

## 3. What round twenty-one did

### D-118: the scripts authority entry names the shipped skill's own directory

D-100's statement was the right boundary and its implementation was wider: the canonical `**/scripts/*.py` entry reached every nested scripts directory of an installing repository, and D-093 requires the canonical entries in every policy that pairs a classifier with a non-force-full rule, so the width shipped to every consumer. The entry is now two, the source spelling and the installed spelling, and the cheap `**/scripts/*.py` product entry stays because it is what returns a consumer's nested scripts to the product route.

Measured after the change, with every rule approved in memory, through the real `load_policy`, `collect_change_facts`, and `build_route`:

| Path | Route |
| --- | --- |
| `anti-dark-code/scripts/adc.py`, `adc_route.py`, `adc_receipt.py`, `adc_efficiency.py`, `work_receipt.py` | Level 3, `force_full` |
| the same five under `.agents`, `.claude`, `.codex`, and `.gemini` skill prefixes | Level 3, `force_full` |
| `scripts/deploy.py` at a repository root | Level 3, `force_full`, unmapped |
| `tools/scripts/build.py`, `packages/app/scripts/migrate.py`, `docs/scripts/render.py`, `ci/scripts/release.py`, `src/scripts/__init__.py` | Level 2, product code |

Tests: `test_nested_consumer_scripts_are_product_code_and_shipped_scripts_are_authority` holds the table; `test_every_shipped_script_is_authority_by_location`, `test_shipped_policy_matches_the_canonical_authority_class_contract`, `test_a_policy_grading_the_router_as_product_code_is_refused`, and `test_source_only_authority_cannot_hide_the_installed_router` were re-pointed at the two entries. Rows: M100 re-anchored to the source entry and narrowed to `adc*.py`, which demotes `work_receipt.py`; M115 widens the installed entry back to `**/scripts/*.py`; M116 narrows it to `.agents/skills/` alone. Applied one at a time before the commit, each failed between ten and eleven of the self-grading tests.

One consequence is stated rather than hidden: a copy of the skill installed under a directory not named `anti-dark-code` is outside both spellings. The installer never writes one and the self-grading guard does not probe one, so the change narrows nothing the guard proves.

### The challenger, and D-119

A fresh-context agent attacked D-118 at `6930274`, the round's first head, in its own clones; its report is committed as `CHALLENGE-ROUND-TWENTY-ONE.md`. It upheld the installer's directory name, the consumer-path table, the load-time contract against fourteen policy variants, and the template's identity with the installed policy. It broke D-118 in one place and found one gap in its verification.

The hole: `ANTI-DARK-CODE/scripts/adc_route.py`, and the same variant under `.agents/skills/`, matched the cheap `**/scripts/*.py` product entry and neither new authority glob, so with every rule approved it routed as Level 2 product code in all 36 change shapes, where the parent commit's wide entry had forced full. With real git the challenger built the commit a case-sensitive host would produce, three files under `ANTI-DARK-CODE/scripts/` containing `# replaced router`, routed it against the base as product code with no `force_full`, and pulled it onto an NTFS clone: the genuine `anti-dark-code/scripts/adc_route.py`, `adc_efficiency.py`, and `work_receipt.py` were replaced on disk, with `git status` showing the genuine paths modified. A file written through the variant spelling on NTFS itself is recorded by git under the genuine name, so the variant must come from a case-sensitive host or from `update-index`; that is exactly the shape a hostile contribution takes.

D-119 closes it in both route builders: a path whose case-folded spelling would match a canonical authority glob that the path itself does not match forces the full recipe and records `ADC-ROUTE-AUTHORITY-CASE-COLLISION`. The classifier is untouched, so R-040 stands as written, no fact changes, and the receipt names the reason. The check covers every canonical class, so `.GITATTRIBUTES` and `anti-dark-code/TESTS/test_route.py` escalate the same way. `test_a_case_variant_of_an_authority_path_forces_full` holds six variants and two controls; M118 disables the check and fails it.

The gap: a mutant that stops the contract requiring the source-spelling entry survived the whole suite, because the only test of that kind covered the installed half, and the bare-glob assertion `anti-dark-code/scripts/*.py` matched a substring of the installed glob. Under that mutant the D-093 exact-representative policy loaded and routed `work_receipt.py` and `adc_efficiency.py` as Level 2. `test_installed_only_authority_cannot_hide_the_source_router` is the twin, the assertion now names the label, and M117 is the mutant. The challenger also observed that M115 and M116 fail the same fourteen tests through the load refusal rather than through the behaviours their notes describe; both are caught, and the notes now say how.

Two nuances went into D-118's consequences rather than into code: a consumer file named `adc.py` or `adc_receipt.py` under any `scripts/` directory is still forced full by the template's older name-based entries, and a file nested below `anti-dark-code/scripts/` is authority because `fnmatch` lets `*` cross a slash, which is wider than "directly under" and fail-closed.

### The second challenger, and D-120

A second fresh-context agent attacked D-119 at `5872e92`. It upheld the policy side, since no classifier entry, rule, or hint reaches the check and hints that try to write `unknowns` raise; the candidate side at that head; the receipt, which recorded `ADC-ROUTE-AUTHORITY-CASE-COLLISION` with the full route for a staged collision through the real CLI and verified `FRESH`; and the rows, M117 now failing the twin test and M118 the D-119 test. It recorded the false positives: six consumer paths such as `docs/skill.md` and a `References/` directory moved from below full to full, all in the safe direction.

It broke D-119's stated property in two spellings the rule did not reach. On a volume that generates NTFS short names, `ANTI-D~1/scripts/adc_route.py` aliases the genuine directory; it routed as Level 2 product code with no code, and `git reset --hard` or `git checkout -f` of a commit carrying it, the commands git's own refusal message points a developer at, wrote the replaced router over the genuine file. And `tools/scripts/ADC.py` routed cheap while the template's own `**/scripts/adc.py` entry makes `tools/scripts/adc.py` authority and a plain pull overwrote it, because the check read only the canonical globs. Two of its own mutants survived: the candidate-side check disabled, under which the shadow record read the router-replacing commit as a cheap candidate that omitted three gates, and `lower()` for `casefold()`, because every test variant was ASCII.

D-120 widens the rule to the property. The fold set is the canonical globs, every classifier entry the loaded policy declares as verification authority, and every force-full rule's path globs. The spelling key strips format characters, applies NFKC normalization, and case-folds. A component shaped like an NTFS short name, or ending in a dot or a space, is an ambiguous spelling that forces full with `ADC-ROUTE-AMBIGUOUS-SPELLING`, because the router cannot resolve what it aliases. The test now holds ten collision spellings and five ambiguous ones in both builders, with the genuine and consumer controls; M118 is re-anchored, M119 disables the candidate side, M120 the ambiguity rule, M121 the policy-declared globs, and M122 the normalization. What the router does not model, APFS and HFS+ ignorable code points beyond the format category, ext4 casefold directories, and git older than 2.24.1, is recorded under D-116 as the owner's environment, not as a guarantee.

### The third challenger, and D-121

A third fresh-context agent attacked D-120 at `38cdff8`. On NTFS it upheld the rule with real git: for every spelling in its battery it built the commit a case-sensitive host would produce and applied it by `checkout -f`, `reset --hard`, `pull`, and a fresh clone on a volume with 8.3 names. Every spelling git wrote over a genuine authority file, the case variants, the upper- and lower-case short names, and the Win32-stripped trailing dot, was forced full with a code; every spelling that routed cheap without a code was either refused by git, the tab, the empty component, the data stream, and the backslash, or written as a distinct name beside the genuine one, the dotless i, the leading and no-break spaces, the Cyrillic and Greek confusables. A sweep of every code point in the Basic Multilingual Plane found none that NTFS equates to an ASCII letter. It found HFS+'s ignorable set to be entirely format characters, which the key strips, and analysed APFS's folding as covered, without a Mac to measure. It upheld the policy side, the receipt, and the candidate side, and reported the cost: three times the parent's for a 5,000-fact route, because every glob's key was recomputed for every fact.

It found the fold set narrower than D-120's property in one direction and wider in another. An approved rule with `paths` that raises the level, adds passes or obligations, or requires review without forcing full was outside the set, so `Secrets/notes.md` routed at Level 0 without review while `secrets/notes.md` was Level 3 with it. A proposed force-full rule's paths were inside it, so an unreviewed rule changed routes, against D-022. Three of its own mutants survived: the short-name pattern restricted to upper case, under which real git wrote `anti-d~1/scripts/adc_route.py` over the router; force-full rule paths dropped from the set, which no test built a policy to notice; and the glob compared unfolded, under which `docs/skill.md` routed as prose while `docs/SKILL.md` is skill policy and NTFS aliases them.

D-121 closes all of it. The fold set is the canonical globs, the policy's verification-authority entries, and the path globs of every approved rule that requires anything beyond the empty route; a proposed rule contributes nothing; each glob's key is computed once per route. `test_an_approved_path_rule_protects_its_case_variants` holds the rule half beside its proposed twin, and the collision test gains the lower-case short name and four lower-case spellings of upper-case globs. M123 lets proposed rules in, M124 keeps only force-full rules, M125 compares the glob unfolded, and M126 restricts the short-name pattern to upper case.

One observation is the owner's rather than the router's. In this repository every `route --write` creates the run store's own `.gitignore`, which the repository's ignore file does not cover, so every written receipt carries that file as an unmapped fact and is full for that reason alone; a collision can be isolated only by the read-only `route` command, which is what the second challenger used. Ignoring `.anti-dark-code/` as a whole would remove the permanent unmapped fact from every receipt; it is a change to the repository's ignore file, not to the router, and it is left for the owner.

## 4. Verification

Windows 11, Python 3.14.2, Git 2.50.1 for the Windows runs, each in a fresh `core.autocrlf=false` clone of the pushed head beneath the scratch directory. WSL2 Ubuntu, kernel 6.18.33.2-microsoft-standard-WSL2, Python 3.12.3 in a venv, pytest 9.1.1, Git 2.43.0, for the Linux runs, each in a fresh clone under the WSL home directory.

- After the D-118 change, CI-shaped suite: `504 passed, 14 skipped, 67 subtests passed` (one new test). After the D-119 repair: `506 passed, 14 skipped, 67 subtests passed` (two more). Universal validation: 0 errors, the one expected warning after pytest, both times. Integrity, traceability, and workflow contracts pass with 118 rows.
- Windows parallel replay at `6930274`, `--jobs 8`, read-only: exit 0, `116 mutants, 0 not caught: none`, 107 caught and 3 survived under the exact symlink skip, every row restored, all eight clones removed, 1,050 s, report SHA-256 `c588eab2cf7afc251136e36a35547fd1f64228ce8bf6f6f897f1fb07c50764f7`. M100, M115, and M116 caught with 11, 12, and 12 exact failed identities.
- WSL2 full serial `--write` at `6930274`: exit 0, `116 mutants, 0 not caught: none`, 1,314 s, report SHA-256 `b651c7ebb9970e22b3caffdddcc5e23edfd40cad419eece52098391c5ae9f28c`. Its matrix was not imported; the head was superseded by the D-119 repair.
- Windows serial `--write` at `6930274`: stopped after about eight minutes when the head went stale; no report.
- CI on PR #32 at `6930274`: run `33697471094`, all nine jobs on the first attempt, mutation replay 11m40s.
- Challenge at `6930274`: section 3. M117, the challenger's surviving mutant, was reproduced on the repaired tree before the fix: with the harness's tests, it passed the whole suite; after the fix it fails two tests, and M118 fails one.
- Windows parallel replay at `5872e92`, `--jobs 8`, read-only: exit 0, `118 mutants, 0 not caught: none`, 109 caught and 3 survived under the exact symlink skip, every row restored, cleanup complete, 1,049 s, report SHA-256 `fec709b61c9c5c8ea18e8fbbe6143f9f314ebc7175dee3c64ad41bcf7d027cf4`. M100, M115, and M116 caught with 14 exact failed identities each; M117 with 2; M118 with 1.
- WSL2 full serial `--write` at `5872e92`: exit 0, `118 mutants, 0 not caught: none`, 112 caught, no skips, 1,341 s, report SHA-256 `cb4951115137e8492a46d3478aa32c1f736790eb3619a7651ce96ba96d30e23d`. Its matrix was not imported; the head was superseded by the D-120 repair.
- Windows serial `--write` at `5872e92`: stopped after about nine minutes when the head went stale; no report.
- CI on PR #32 at `5872e92`: run `33699688243`, all nine jobs on the first attempt, mutation replay 12m24s, macOS 39 s.
- Second challenge at `5872e92`: section 3. M119 to M122 were applied to the repaired tree before the commit; each fails the D-120 test, and M118 still does.
- Windows parallel replay at `38cdff8`, `--jobs 8`, read-only: exit 0, `122 mutants, 0 not caught: none`, 113 caught and 3 survived under the exact symlink skip, every row restored, cleanup complete, 1,074 s, report SHA-256 `be082e64b0cd892a8f8c2cc9f47c97c2caa4a4df5359d088115f537c645a81ca`. M100, M115, and M116 caught with 14 exact failed identities each; M117 with 2; M118 to M122 with 1 each.
- WSL2 full serial `--write` at `38cdff8`: exit 0, `122 mutants, 0 not caught: none`, 116 caught, no skips, 1,390 s, report SHA-256 `7e4e54e93c5f932ba57256dccd80357895763f75e224cfb6e6eda086defe1ca9`. Its matrix was not imported; the head was superseded by the D-121 repair.
- Windows serial `--write` at `38cdff8`: stopped after about twenty minutes when the head went stale; no report.
- CI on PR #32 at `38cdff8`: run `33702102859`, all nine jobs on the first attempt, mutation replay 13m00s, macOS 36 s.
- Third challenge at `38cdff8`: section 3. M123 to M126 were applied to the repaired tree before the commit; each fails the suite, and M118 to M122 still do.
- Windows parallel replay at `fe350e9`, `--jobs 8`, read-only: exit 0, `126 mutants, 0 not caught: none`, 117 caught and 3 survived under the exact symlink skip, every row restored, cleanup complete, 1,105 s, report SHA-256 `baec909feb95c86000798e86a2f95fb0a60d6abe7f76f0c6df0e93f9318a15ef`. M100, M115, and M116 caught with 15 exact failed identities each; M117 and M118 with 2; M119 to M126 with 1 each.
- WSL2 full serial `--write` at `fe350e9`: exit 0, `126 mutants, 0 not caught: none`, 120 caught, no skips, status empty before and only `matrix.json` modified after, 1,429 s, report SHA-256 `13c4c3a6dbdcf2018d1d43d285bf5b1225e8efa020bddbcfe3b74d1ebd9ca060`. M100, M115, and M116 caught with 15 exact failed identities each; M117 and M118 with 2; M119 to M126 with 1 each.
- Windows full serial `--write` at `fe350e9`, from a second clean clone: exit 0, `126 mutants, 0 not caught: none`, 117 caught and 3 survived under the exact symlink skip, status empty before and only `matrix.json` modified after, 5,578 s, report SHA-256 `583133fbe61743f57239c0923604e5bcdbfe123cf5c9d73e322da22137d4fc89`. Agrees with the parallel replay row for row on verdict and skip count.
- Merge: for every active row the Windows record is the Windows write's and the Linux record is the Linux write's, and the row verdict is `derive_verdict` over the two. 120 of 120 active rows carry exact identities from both hosts; M37, M46, and M48 are `caught elsewhere` by exact intersection; no row's verdict differs between the hosts. Matrix SHA-256 `3889850a775ea8d9c01294a87977f73261064e2ec65d4ab03a5d292c7e240a33`. `SERIAL-EVIDENCE-ROUND-TWENTY-ONE.json` records all of it, with the three superseded heads as measurements.
- CI on PR #32 at `fe350e9`: run `33705247810`, all nine jobs on the first attempt, mutation replay 13m27s, macOS 53 s.
- No fourth challenge at `fe350e9`, by the cap in section 6. M123 to M126 were applied to the repaired tree before the commit; each fails the suite, and M118 to M122 still do.
- The owner walkthrough at the documentation head, and that head's exact CI run, are recorded in section 4a by the receipt commit that follows it.

## 4a. Receipt at the documentation head

The documentation head is `1ba6026`. Required run [`33712448096`](https://github.com/LynxTWO/anti-dark-code-skill/actions/runs/33712448096) at exactly that commit passed every job on its first attempt; the mutation job ran 13m20s and ended `126 mutants, 0 not caught: none`.

| Job | Result | Duration |
| --- | --- | ---: |
| Ubuntu / Python 3.12 | success | 32s |
| Ubuntu / Python 3.13 | success | 33s |
| Windows / Python 3.12 | success | 1m41s |
| macOS / Python 3.12 | success | 36s |
| Hostile environment (C locale) | success | 31s |
| Hostile environment (international paths) | success | 34s |
| Clean distribution archive | success | 8s |
| Mutation replay (Linux) | success | 13m20s |
| Aggregate `Tests` | success | 3s |

The owner walkthrough was run as written, in PowerShell, on a fresh default clone, `core.autocrlf=true`, detached at `1ba6026`. Every stated expectation held: the six proposed rules; `False` and `[]`; `3 passed`; the `ROUTE` line with `level=3`, `passes=07,10,11,14`, the five gates, `force_full=true`, `complete=true`, and `rules=-`; `FRESH`, then `STALE` with `ADC-STALE-004 worktree_identity`, then `FRESH`; `507 passed, 14 skipped, 67 subtests passed`; `VALID (universal): 0 errors, 1 warning(s)`; `rows 126 | active 120 | recorded on both hosts 120` with nothing awaiting; the Round Sixteen through Round Twenty-One artifact checks, `True` for every blob comparison, including the round-twenty-one check against the matrix blob at the evidence commit `1322eb1`; every required PR check `pass`, the mutation job having been pending during the run and re-checked once it passed; D-080 and section 9 printed; thirty-seven decision sections in step 5. The run store was the only untracked path afterwards. The owner's own answers and record from 2026-09-02 stay in section 6 of the walkthrough untouched; this run re-verified the script's expectations at the new head and checked no box.

This receipt commit follows `1ba6026` and therefore triggers one more exact-head run; its receipt belongs on PR #32.

## 5. Round twenty-one's own defects

- **D-118 opened a hole its own measurement did not reach.** Round twenty measured option 2 against consumer paths and the guard's probe set, none of which is a case variant of a shipped path. The variant was found by the challenger at the round's first head, `6930274`, before anything landed, and D-119 closes it; the evidence at that head is kept as a measurement, not as a record.
- **The source half of the contract had no test.** M117 survived the whole suite at `6930274`. Found by the same challenger; section 3.
- **Round twenty's R-053 row kept a stale tail.** The ENGINEERING row still said the Linux records were Round Eighteen's T540P records and that M107 to M109 awaited theirs, after round twenty's merge had refreshed every Linux record. Round twenty's edit replaced only the front of the row. The row is rewritten whole.
- **The Windows serial write at `6930274` was stopped** after about eight minutes when the head went stale, as round nineteen's and round twenty's were; the parallel replay and the WSL write at that head are recorded in the artifact as measurements.
- **D-119 implemented a narrower rule than the property it argued from.** The second challenger measured the gap at `5872e92`, section 3, and D-120 closes it; the parallel replay and the WSL write at that head are measurements too, and its Windows serial write was stopped after about nine minutes.
- **D-120 stated its fold set narrower than its property in one direction and wider in another**, and its test held only upper-case short names. The third challenger measured both at `38cdff8`, and D-121 closes them; that head's runs are measurements, and its Windows serial write was stopped after about twenty minutes.

## 6. The D-116 conditions at this head

1. Both hosts' full serial writes report zero not caught with exact-identity records on every active row. At `fe350e9`: it holds. Both writes report `126 mutants, 0 not caught: none`, all 120 active rows carry exact identities from both hosts, and the parallel replay agrees row for row; it also held at each of the three superseded heads for the rows that existed there.
2. A fresh-context challenger finds only channels the harness cannot own, or reproductions of closed decisions. At `fe350e9`: it holds as measured at `38cdff8` by the third challenger, whose real-git battery upheld the spelling rule on NTFS. D-121's repairs of the two edges and three test gaps it found are held by tests and by M123 to M126, measured to fail when applied, and were not re-challenged, by the cap below. What no host here can measure, macOS and ext4 casefold aliasing, is the owner's environment under D-116.
3. The owner walkthrough passes literally on a fresh default clone. At `1ba6026`: it holds, as measured by the agent. Every stated expectation matched on a fresh default clone with `core.autocrlf=true`, section 4a; the owner's own record from 2026-09-02 stands untouched, and no box was checked.

The line stops here. It reopens only on the triggers D-116 names.

The cap this round applied, so that a verifying round cannot become the loop D-116 ended: a repair found by a challenger is verified by tests and mutation rows measured to fail, and by the two-host replay at the head that carries it, not by another challenge of the repair itself. A challenger is dispatched against a change once; when it upholds the property and finds only edges, the edges are closed and the round proceeds to its evidence. Three cycles was one more than this round needed, and the third was the one that measured the rule holding. Anything found after the final head that is not a document defect is an open item for the owner under D-116, not a fourth cycle.

## 7. Runtime

About 5h30m from the owner's "let's do it" to this round's receipt commit. The authoritative replays sum to about 4h50m, partly overlapped:

| Command | Wall time |
| --- | ---: |
| parallel replay at `6930274` | 17m30s |
| WSL2 Linux full serial write at `6930274`, alongside it | 21m54s |
| Windows full serial write at `6930274`, stopped when the head went stale | about eightm, discarded |
| parallel replay at `5872e92` | 17m29s |
| WSL2 Linux full serial write at `5872e92`, alongside it | 22m21s |
| Windows full serial write at `5872e92`, stopped when the head went stale | about ninem, discarded |
| parallel replay at `38cdff8` | 17m54s |
| WSL2 Linux full serial write at `38cdff8`, alongside it | 23m10s |
| Windows full serial write at `38cdff8`, stopped when the head went stale | about twentym, discarded |
| parallel replay at `fe350e9` | 18m25s |
| WSL2 Linux full serial write at `fe350e9`, alongside it | 23m49s |
| Windows full serial write at `fe350e9` | 1h32m58s |
| fresh-context challengers at `6930274`, `5872e92`, and `38cdff8` | about 21m, 24m, and 36m, each concurrent with the replays |
| owner walkthrough at `1ba6026`, on a fresh default clone | about 7m |

The gap between the replays and the elapsed time was D-118 with its test and rows, the first challenge, D-119 and the source-half test after it, and the documents.

# Handoff back: round twenty

Date: 2026-09-02. Agent: Claude, in Codex's place; Codex is out of credits until 2026-09-06. Base: `cbdc03e`, the head of `claude/round-nineteen-verify`, PR #29. Branch: `claude/round-twenty-verify`, draft PR #30. Implementation head: `0ace58f`, which carries every repair, row, and decision; the evidence below was produced at that commit and the documents that report it follow it.

## 1. Terminal outcome

- **Round nineteen's numbers reproduce**, and its owner walkthrough held on a fresh default clone at `c0b1497` in every step. The reproduction is section 2.
- **Two of round nineteen's boundaries were broken again**, by a fresh-context challenger with no memory of writing them. Beneath D-105, an ambient `PYTHONWARNINGS` or `PYTHONOPTIMIZE` changed what a worker's test meant, and the suite's git read the caller's global configuration, which ran a hook from outside the clone. D-106's renderer covered the error field only. D-111, D-112, and D-115 repair them, each with a test and a mutation row.
- **One mutation row was held by the host, not by the suite.** A WSL2 Ubuntu replay at round nineteen's head saw M08 survive; the catch on Windows, T540P, and the CI runners was each host's global git-lfs driver. D-113 supersedes M08 with M114, which is caught by fixture-local tests on any host.
- **D-110 landed.** A row no host caught is `SURVIVED` under skips, with the skipped tests named. M110 holds it.
- **The stopping rule caught something before it was adopted.** At `2f86f14`, the round's first evidence head, the Linux write saw M107 survive while Windows caught it. The contract assertion that was meant to hold M107 on a venv host inherited the value it asserted from the harness the suite runs inside. D-117 inverts the contract test, and the evidence was re-run at `0ace58f`.
- **Both hosts' records are current at one commit.** Two full serial writes at `0ace58f`, Windows and WSL2 Ubuntu, refreshed every active row with exact identities; M107, M108, and M109 have their Linux records; the new rows have both. Section 4.
- **A stopping rule is proposed, not applied.** D-116 names the conditions under which the harness line is closed and what reopens it, and section 8 reports which of them hold at this head. The owner decides it, with D-107.
- SLICE-001 remains `Proposed`. No routing rule was approved, selective execution stays disabled, and the last box is still the owner's.

## 2. Round nineteen, reproduced before its conclusions were read

Windows 11, Python 3.14.2, Git 2.50.1. The challenger worked in its own `core.autocrlf=false` clone and a default clone at `39d745d`, round nineteen's code head; the walkthrough ran on a fresh default clone at `c0b1497`, the documentation head.

| Claim | Result |
| --- | --- |
| Suite `500 passed, 14 skipped, 64 subtests` | `500 passed, 14 skipped, 64 subtests passed in 218.69s` on the walkthrough clone |
| Universal validation 0 errors | `0 errors, 1 warning(s)`, the generated-artifact warning |
| Matrix 109 rows, 104 active, 5 superseded, 101 on both hosts, M107 to M109 awaiting Linux | 109 rows, 104 active, 101 recorded on both hosts, awaiting `['M107', 'M108', 'M109']` |
| Round-nineteen artifact: implementation commit `39d745d`, `109 mutants, 0 not caught: none`, report `18073613…`, 91 stale Windows records before, first-test M107 `SURVIVED` | All matched, and the committed matrix blob matched the serial write |
| PR #29 green at the exact head | Run `33665998028` at `c0b1497`, every job `success` |
| Every commit carries the trailer | 5 of 5 |
| Owner walkthrough true on a fresh default clone | Steps 0 through 5 matched at `c0b1497`, including the D-108 blob check that had failed at `08d0576` |
| R-040 upheld | Measured by the challenger with the real classifier on Windows; upheld, including for the authority glob the fixture test does not exercise |

Two things round nineteen said about itself were incomplete rather than wrong. Its renderer decision, D-106, said no console line could carry a raw control character in either mode, and its code rendered one field. Its handoff said M08 was caught on every host, which was true, and did not know why.

## 3. What round twenty found

### D-111: a worker inherited flags that change what a test means

D-105 owned where a worker's code comes from. The interpreter also reads flags that change what a test means. Through the real `run_suite`, with a clone-owned probe test, `PYTHONWARNINGS=error` turned a probe emitting a `DeprecationWarning` from `1 passed` into `1 failed`, and `PYTHONOPTIMIZE=2` turned `assert __debug__` from a pass into a failure. A surviving mutant can therefore be recorded as caught because the shell that launched the coordinator exported a warning filter: the D-095 class with the environment as the foreign record.

Fix: the suite environment drops the eighteen `PYTHON*` flags that change test semantics; the locale and encoding variables stay because the hostile-environment jobs exist to run the suite under them. The env-capture test asserts the contract; a second test attacks through the real worker path with a warning probe and an `assert __debug__` probe. M111 restores `PYTHONWARNINGS` and `PYTHONOPTIMIZE` to the inherited set and fails both.

### D-112: the suite's git read the caller's configuration

The real-git fixtures run `git` with the worker's environment, so `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_COUNT`, and `HOME` all reached the suite subprocess. A global configuration naming `core.hooksPath` ran a `pre-commit` from outside the clone during a fixture-shaped `git commit`; `core.fsmonitor` ran a script during `git status`. The acquisition code under test neutralizes hostile configuration (R-034, R-054); the fixtures that build every real-git test did not.

Fix: every git the suite runs reads an empty run-owned global configuration file, no system configuration, no system attributes, an empty template directory, and a run-owned XDG directory; the `GIT_*` variables that redirect git are dropped. The attack test writes a global configuration with `core.hooksPath` outside the clone and a hook that leaves a marker, runs a fixture-shaped commit through the worker path, and asserts the marker never appears. M112 renames the pin and fails it.

### D-113: M08 was held by the host, not by the suite

M08 replaces `_filter_overrides(run)` with an empty list. On Windows at `39d745d`, with the host's git configuration, one test fails under it; with an empty global configuration and the system configuration disabled, the five filter tests and the whole route suite pass under it. The catch on three hosts was `filter.lfs.required=true` staying live once the `-c` overrides were dropped. WSL2 Ubuntu, with no driver, saw the mutant survive: `109 mutants, 2 not caught: ['M08', 'M107']` at `39d745d`.

The code says why the suite could not hold it. In production the runner is the default one, so with the overrides gone `_live_filter_programs` reports every driver live, `read_change_inputs` builds the D-088 environment runner and runs the comparison neutralized through it. The result is the same by another route. A caller-injected runner, which tests use, is denied that fallback, which is why an injected-runner test noticed the difference only where the host's global configuration declared a driver.

Fix: M08 is superseded by M114, which disables the environment neutralization by never setting `GIT_CONFIG_COUNT`; two fixture-local filter tests fail under it on any host. The `-c` overrides stay as defense in depth, as D-094 kept the layout derivation.

### D-114: the matrix carried no line-ending attribute

`.gitattributes` scoped `text eol=lf` to `anti-dark-code/**`, so a default Windows clone rewrote the matrix and every evidence artifact under `design/routing/` on checkout while `git status` stayed clean. D-108 had moved the walkthrough check to the committed blob; this was the second root cause. `design/routing/**/*.json` is now `text eol=lf`.

### D-115: the renderer covered one field

`replay()` rendered a broken row's error and printed the row's id, name, replacement id, and verdict, and the summary's survivor ids, raw from `matrix.json`. A row name carrying a newline and an escape printed a forged coloured summary line in both modes. Every field printed from the matrix now passes through the renderer; the JSON report keeps the raw values. M113 prints the name raw and fails the test that captures both consoles.

### D-110: landed

The `unverified: every host skipped` branch is removed. With no catching host the row is `SURVIVED` on every host, the console names the exact tests the host skipped, and a later catching host restores `caught elsewhere` through D-104's intersection. M110 reinstates the branch and fails two tests.

### D-117: the contract assertion inherited what it asserted

Round nineteen's WSL2 run had seen M107 survive because a venv disables the user site itself, so removing `PYTHONNOUSERSITE` changes nothing there; the CI runner's non-venv Python is where it was caught. This round's first repair asserted the environment contract directly, `PYTHONNOUSERSITE == "1"` in the captured worker environment, so that a venv host would catch it too. The WSL2 write at `2f86f14` reported `114 mutants, 1 not caught: ['M107']` with `318 passed`.

The route suite runs inside `run_suite` under replay, so every variable `run_suite` sets for its worker is already in the suite process's environment, and the nested `run_suite` under test starts from that. Under M107 the assertion passed on the inherited `1`. The Windows parallel replay at the same head caught M107 only through the behavioural probe; the contract assertion was masked on both hosts, and only the venv host had nothing else. The same shape masked the `GIT_CONFIG_NOSYSTEM` assertion and the suffix checks on the run-owned git paths.

Fix: the contract test first installs the state the harness must replace. What `run_suite` must add is removed from the inherited environment before the call; what it must overwrite is set to a caller-owned value; a run-owned path is asserted by its prefix under the run's private root. Measured after the fix, with the harness's own values present in the outer environment: M107, M112, and M111 each fail the contract test, and the unmutated tree passes it. This round's Linux write at `0ace58f` records M107 `caught`, `1 failed, 317 passed`, by the inverted contract test on WSL2.

### D-107, measured for the owner

Both options were loaded and routed on Windows at `39d745d` through the real `load_policy`, `collect_change_facts`, and `build_route`, with every rule approved in memory. Under both, all 71 self-grading guard paths, in source, installed, and calibration spellings, force the full recipe.

| Path | Option 1, current `**/scripts/*.py` | Option 2, `anti-dark-code/scripts/*.py` and `**/anti-dark-code/scripts/*.py` |
| --- | --- | --- |
| `anti-dark-code/scripts/adc.py`, `adc_route.py`, `adc_receipt.py`, `adc_efficiency.py`, `work_receipt.py` | Level 3, `force_full` | Level 3, `force_full` |
| `.agents`, `.claude`, `.codex`, `.gemini` installed spellings of the same scripts | Level 3, `force_full` | Level 3, `force_full` |
| `scripts/deploy.py` at a repository root | Level 3, `force_full` (unmapped) | Level 3, `force_full` (unmapped) |
| `tools/scripts/build.py`, `packages/app/scripts/migrate.py`, `docs/scripts/render.py`, `ci/scripts/release.py`, `src/scripts/__init__.py` | Level 3, `force_full` | Level 2, product-code route |

Option 2 keeps the cheap `**/scripts/*.py` product entry, which is what returns nested consumer scripts to the product route; removing that entry too leaves them unmapped and full, which a first draft of this measurement did. Option 1 costs every installing repository a full route for any nested `scripts/*.py`; option 2 costs nothing measured here and matches D-100's own statement. Option 3, name-based authority behind a stronger loader guard, was not measured, because round eighteen showed the loader scan could be bypassed by assembling the name at runtime. The decision is the owner's.

### Checked and found sound

- R-040, by the challenger, with the real classifier on Windows.
- Ancestor `conftest.py` files in the coordinator's directory, the clone's parent and grandparent, and the temp root: all contained by D-105's pinned configuration and rootdir.
- `_terminal_safe_diagnostic` itself: it escapes ESC, CR, LF, BEL, BS, U+202E, ZWJ, U+2028, and U+2029; combining marks and wide characters pass and only corrupt visually.
- One observation without a change: `**/*.md` never matches a top-level file, so `README.md` is unmapped and forces the full route. Fail-closed, and the docs surface silently excludes root-level Markdown. Recorded for the owner with D-107.

## 4. Verification

Windows 11, Python 3.14.2, Git 2.50.1 for the Windows runs, each in a fresh `core.autocrlf=false` clone of the pushed head beneath the scratch directory. WSL2 Ubuntu, kernel 6.18.33.2-microsoft-standard-WSL2, Python 3.12.3 in a venv, pytest 9.1.1, Git 2.43.0, for the Linux runs, each in a fresh clone under the WSL home directory.

- After the changes, CI-shaped suite: `503 passed, 14 skipped, 67 subtests passed` (three new tests). Universal validation: 0 errors, the one expected warning after pytest. Integrity, traceability, and workflow contracts pass with 114 rows.
- Windows parallel replay at `2f86f14`, `--jobs 8`, read-only: exit 0, `114 mutants, 0 not caught: none`, 105 caught and 3 survived under the exact symlink skip, every row restored, all eight clones removed, 958 s, report SHA-256 `1567a0d2bdec096fbd3ffad84783c772008b687b7fbce879a2402fd452a1e67e`. M107 was caught by the behavioural probe alone.
- WSL2 full serial `--write` at `2f86f14`: exit 1, `114 mutants, 1 not caught: ['M107']`, 107 caught, M107 `318 passed`, status empty before and only `matrix.json` modified after, 1,210 s, report SHA-256 `b1cecea01afd1d200a05982988c8f4ba475eec60bfe48d3bfc8b9955db29acee`. Its matrix was not imported. Section 3, D-117.
- Windows serial `--write` at `2f86f14`: stopped after about 7 minutes when the head went stale; no report.
- CI on PR #30 at `2f86f14`: run `33668817057`, all nine jobs on the first attempt, mutation replay 12m16s, macOS 53 s. Green while the Linux write disagreed, because the CI runner's Python has a live user site and the behavioural probe caught M107 there.
- D-117 check on the repaired tree, with the harness's own values present in the outer environment: M107, M112, and M111 each fail the contract test; the unmutated tree passes it.
- Windows parallel replay at `0ace58f`, `--jobs 8`, read-only: exit 0, `114 mutants, 0 not caught: none`, 105 caught and 3 survived under the exact symlink skip, every row restored, cleanup complete, 971 s, report SHA-256 `a232c480abde21c982487c56285f72546396ab852b24b31de13fa7af60e01965`. M107 caught by both the contract test and the behavioural probe.
- WSL2 full serial `--write` at `0ace58f`: exit 0, `114 mutants, 0 not caught: none`, 108 caught, no skips, status empty before and only `matrix.json` modified after, 1,237 s, report SHA-256 `a5350416a9fbfef94093f29915a2bf0e6fff65dfc787c676584d4229aa6e7b4a`. M107 caught by the inverted contract test, `test_worker_suite_uses_private_temp_environment_and_pytest_basetemp`. M110 to M114 caught with one to two exact failed identities each.
- Windows full serial `--write` at `0ace58f`, from a second clean clone: exit 0, `114 mutants, 0 not caught: none`, 105 caught and 3 survived under the exact symlink skip, status empty before and only `matrix.json` modified after, 4,902 s, report SHA-256 `a2467a4239bd84bf2aa76797a17c9c0103228846901654da8becc41a562d6c93`. Agrees with the parallel replay row for row on verdict and skip count.
- Merge: for every active row the Windows record is the Windows write's and the Linux record is the Linux write's, and the row verdict is `derive_verdict` over the two. 108 of 108 active rows carry exact identities from both hosts; M37, M46, and M48 are `caught elsewhere` by exact intersection; no row's verdict differs between the hosts. Matrix SHA-256 `e4a4cda2ed55c5f7bc4c0bede189aad36cdbd39d20a1bf7302d1c6ec7277b8f8`, from the committed `72f0be84a216858c520e904d220abdb97c6276479a40edc23d9656c954d8fd1a`. `SERIAL-EVIDENCE-ROUND-TWENTY.json` records all of it.
- CI on PR #30 at `0ace58f`: run `33671714111`, all nine jobs on the first attempt, mutation replay 11m33s, macOS 45 s.
- The owner walkthrough at the documentation head, and that head's exact CI run, are recorded in section 4a by the receipt commit that follows it.

## 5. Round twenty's own defects

- The renderer widening was first cited as "D-106 as amended" in a test docstring, a code comment, and the M113 row before D-115 existed; the log's convention is a new decision that amends the old one, so it became D-115 and the three citations were retargeted before the commit.
- The round cited D-111 and D-112 in code before writing them, and D-090's guard refused the tree until they existed. Fifth round in a row.
- **The round's first evidence head carried a masked assertion.** The Windows parallel replay and CI at `2f86f14` were green, and the Linux write at the same head was the only thing that disagreed. The Windows serial write at `2f86f14` was stopped after about 7 minutes when the head went stale; the parallel replay and the WSL write at that head are kept as measurements in the evidence artifact, not as records in the matrix.
- **The walkthrough's round-nineteen check hashed the matrix at `HEAD`.** The literal walkthrough on a fresh default clone at `5843737` printed `False` for it, because the current head's matrix is this round's merge, not round nineteen's write. D-108 says a check compares the blob at the commit the artifact names; the round-nineteen command named `HEAD` and was true only until the next write. It now names `ce71481`, the commit that carried that write, and the walkthrough was re-run on a fresh clone of the corrected head; section 4a.
- A first version of this round's evidence script compared host verdicts without D-104's intersection and flagged M37, M46, and M48 as cross-host disagreements; it also crashed on a superseded row with no results key. Both were fixed before the write, and the second merge was byte-identical to the first.

## 6. What happens next

Nothing opens automatically. The owner runs `WALKTHROUGH-SLICE-001.md` on a fresh default clone of this branch's final head, answers its seven questions, decides D-107 and D-116, and, if the last box is checked, a separate change marks SLICE-001 `Done` and lands PRs #21 through #30 in order. If a reopen condition in D-116 fires, one round verifies the change and stops. Codex returns on 2026-09-06 and can be that round's challenger or its author.

## 7. Runtime

About 2h50m from this round's first command after round nineteen's receipt to its own receipt commit. The authoritative replays sum to about 2h42m, partly overlapped:

| Command | Wall time |
| --- | ---: |
| parallel replay at `2f86f14` | 15m58s |
| WSL2 Linux full serial write at `2f86f14`, alongside it | 20m10s |
| Windows full serial write at `2f86f14`, stopped when the head went stale | about 7m, discarded |
| parallel replay at `0ace58f` | 16m11s |
| WSL2 Linux full serial write at `0ace58f`, alongside it | 20m37s |
| Windows full serial write at `0ace58f` | 1h21m42s |
| owner walkthrough at the documentation head | recorded in section 4a by the receipt commit |
| WSL2 Linux full serial write at `39d745d` and the fresh-context challenger | counted in round nineteen |

The gap between the replays and the elapsed time was the decisions, the rows, the D-117 repair after the first Linux write disagreed, and the documents.

## 8. Whether this converges

The count of findings per round has not moved: rounds fourteen through twenty each closed with four to six decisions. Their subject has. Through round sixteen they were about the router and its inputs. Since round seventeen, sixteen of nineteen decisions are about the replay harness, its evidence files, or its console, and the three that touch the router are one question about where verification authority lives, which has been the owner's since round nineteen. The harness findings have one shape: a channel through which the coordinator's host reaches a worker. Rootdir, then pytest's environment, then the user site and configuration files, then interpreter flags, then git configuration. After D-112, the channels left are the ones the harness cannot write: `PATH`, which chooses the interpreter and the git binary, that interpreter's system site-packages, and the operating system. Pinning those means choosing binaries, which is an environment the owner provides, not a repair the harness can make.

So the endpoint is not a quiet round, because a round finds what it goes looking for and there is always a next channel to look in. D-116 makes it a condition at one commit that anyone can check:

1. Both hosts' full serial writes report zero not caught, with exact-identity records for every active row at that commit. At `2f86f14` this did not hold: Linux saw M107 survive and Windows caught it, and the round repaired the test rather than the record. At `0ace58f`: it holds. Both writes report `114 mutants, 0 not caught: none`, all 108 active rows carry exact identities from both hosts, and the parallel replay agrees row for row.
2. A fresh-context challenger at that commit finds only channels the harness cannot own, or reproductions of closed decisions. At `0ace58f`: it holds as far as this round can say. Every finding of the fresh-context challenger at `39d745d` is repaired and re-measured here, the one finding this round's own evidence added, D-117, is repaired and re-measured, and the channels left open are `PATH`, the interpreter's system site-packages, and the operating system.
3. The owner walkthrough passes literally on a fresh default clone of that commit. At the documentation head: to be run on a fresh default clone after this document is committed; the receipt commit records the result in section 4a.

The owner walkthrough has been the last box since round fourteen, and agents have passed it on fresh clones in rounds sixteen, eighteen, nineteen, and twenty. Passing it a fifth time is not evidence the owner has seen it.

Do not treat this handoff as acceptance of its own contracts. Round nineteen's renderer decision was broken within a day by a reader with no memory of writing it; this round's will be read the same way if the line reopens.

# Handoff back to Codex: round nineteen

Date: 2026-09-02. Agent: Claude. Base: `08d0576`, the head of `codex/round-eighteen-verify`, PR #28. Branch: `claude/round-nineteen-verify`, draft PR #29. Implementation head: `49fed51` for the harness and router changes, corrected by the test commit `39d745d` after the first CI run caught M107 surviving; the evidence and documentation commits follow `39d745d` and change no mutation source.

## 1. Terminal outcome

- **Round eighteen's numbers reproduce exactly**, and its owner walkthrough is true on a fresh clone at `08d0576` in every step but one: the Round Eighteen evidence check hashes the checkout, and on this machine's default clone the checkout is CRLF, so the check fails for the owner. Round eighteen's own run passed because its clone was made with `core.autocrlf=false`.
- **Two of round eighteen's boundaries were broken**, both beneath the layer round eighteen closed: a caller's `PYTHONUSERBASE` executed code inside a worker that reported one passing test, and an ancestor `pytest.ini` reached a worker's options. The serial console still printed a forged replay line that D-102 had removed from the parallel console. D-105 and D-106 close them.
- **One contract is wider than its decision.** D-100's canonical entry forces the full route for every nested `scripts/*.py` in any installing repository. Recorded as an owner decision, D-107, not changed.
- **One record set was stale by commit.** Ninety-one of the 101 active rows carried Windows records from before D-100 through D-104, with no exact identities. D-109 measures it and refreshes every Windows record from a full serial write at this round's implementation head.
- SLICE-001 remains `Proposed`. No routing rule was approved, selective execution stays disabled, and the last box is still the owner's. M107, M108, and M109 are new and carry Windows records only until the next T540P run.

## 2. Round eighteen, reproduced before its conclusions were read

Windows 11, Python 3.14.2, Git 2.50.1, in a clean worktree at `08d0576`.

| Claim | Result |
| --- | --- |
| Suite `498 passed, 14 skipped, 64 subtests` | `498 passed, 14 skipped, 64 subtests passed in 24.55s`, CI-shaped, 25 s wall |
| Universal validation 0 errors | `0 errors, 1 warning(s)`, the generated-artifact warning |
| Integrity, traceability, workflow contracts | `12 passed` |
| Matrix 106 rows, 101 active, 5 superseded, both hosts on every active row | 106/101/5; 101 Linux `caught`; 98 Windows `caught` and 3 Windows `SURVIVED` under the exact symlink node; M37, M46, and M48 intersect on `AcquisitionAgainstRealGitTests::test_a_symlink_is_identified_not_followed`; SHA-256 `d1eb1f3c…` equals the artifact's final digest |
| Every commit carries the trailer | 4 of 4 |
| PR #28 green at the exact head | Run `33645108730` at `08d0576`, all nine jobs `success`, mutation replay 10m20s |
| Owner walkthrough true on a fresh clone | Steps 0 through 3 and every step 4 and 5 expectation matched, except the Round Eighteen artifact check, which raised `AssertionError` on a default clone. See D-108 |
| R-032 upheld across five cases on two hosts | Not re-run; the review record and unknowns entry exist and say what the handoff says |

Two records did not match their own handoff. The decision index and the section status lines for D-095 through D-099 all still read `Confirmed`, while the handoff and the artifact say amended, superseded, or broken. Corrected to the log's own convention. And the Windows records: see D-109.

## 3. What round nineteen found

### D-105: D-101's boundary stopped at pytest

D-101 removed the pytest option and plugin variables, disabled autoload, removed `PYTHONPATH`, and enabled safe-path. Two layers sit beneath that.

The interpreter runs site initialization before pytest reads an option. Measured through `run_suite` with a clone-owned probe test, exactly as D-101's own test is built: with `PYTHONUSERBASE` pointed at a caller-controlled directory whose site-packages held a `usercustomize.py` and a `.pth` import line, both wrote their marker inside the worker while the suite reported `1 passed`. With `PYTHONNOUSERSITE=1`, neither ran.

pytest searches for `pytest.ini`, `tox.ini`, `setup.cfg`, and `pyproject.toml` from the common ancestor of the invocation directory and the arguments upward, and `--rootdir` does not stop the search. A `pytest.ini` at that ancestor with `addopts = -p external_adc_plugin` reached the worker: the row went inconclusive with the plugin's import error. For a worker the ancestor is the host temp directory; for serial replay it is every parent of the repository, which on T540P is `/tmp`.

Fix: the suite environment drops `PYTHONUSERBASE`, `PYTHONSTARTUP`, `PYTHONHOME`, `PYTHONEXECUTABLE`, and `PYTHONINSPECT` and sets `PYTHONNOUSERSITE=1`; every suite command pins an empty run-owned `pytest.ini` with `-c`; serial replay pins `--rootdir` to the repository root so node ids keep their spelling in both modes. M107 and M108 hold it. D-101's own tuple is untouched so M101 still matches.

### D-106: the serial console printed raw text

D-102 renders control characters before a worker diagnostic reaches the coordinator. The serial path printed `result["error"]` directly. Measured: a serial `SuiteBroken` carrying a newline and an ANSI escape printed `M01 forged row caught` on its own line and a coloured forged summary after it. Fix: the same renderer on both paths; the JSON report keeps the raw text. M109 holds it.

### D-107: D-100 reaches every scripts directory

Measured with every rule approved: `tools/scripts/build.py`, `packages/app/scripts/migrate.py`, and `docs/scripts/render.py` in an installing repository route as verification authority at Level 3 with `force_full`, where the previous `**/scripts/adc*.py` entry left them at Level 2. The decision text names only the shipped skill's own scripts. The entry is canonical, so every installing policy must carry it. Three options are recorded for the owner. Nothing changed.

### D-108: the walkthrough failed on the owner's own configuration

Measured by running it. The Round Eighteen artifact check now hashes the committed blob through `git cat-file`, named by commit, and prints whether it matches.

### D-109: the Windows records were stale by commit

Measured from the matrix: 91 of 101 active rows carried Windows results without `failed_nodeids` or `skipped_nodeids`, which only the round-eighteen refresh writes, so those 91 records predate D-100 through D-104; only M37, M46, M48, and M100 through M106 were replayed on Windows at the round-eighteen head. The Linux side was complete and current.

Measured: a full read-only parallel replay at `08d0576` agreed with every stored Windows verdict, and found one record that no longer describes the head. M68's stored Windows record says ten tests fail under it; the fresh run says eleven, and the Linux record written at the round-eighteen head already said eleven. The suite gained a catching test after the Windows record was written. The mutant was never at risk; the record was stale, which is the claim.

### D-110: a survivor with no catching host cannot fail a Windows replay

Found by this round's own evidence run, not by reading. Under the first D-105 test, M107 survived on Windows with `314 passed, 1 skipped`, and `derive_verdict` labelled it `unverified: every host skipped` because no host had caught it and Windows skips the symlink test on every row. The summary read `109 mutants, 0 not caught: none`, the exit was 0, and the disclosure line said the row rested on another host's record when no other host had one. The Linux CI job at the same commit reported `1 not caught: ['M107']`. D-095 closed this shape for rows with a stored foreign catch; the branch for rows with none predates it and runs first. Recorded as D-110 with the intended repair, deferred to round twenty so this round's evidence stays at one head.

### Two survivors on WSL, observed by this round and handed to round twenty

A full serial `--write` replay on WSL2 Ubuntu at `39d745d`, run to supply the Linux records Codex's T540P would have supplied, ended `109 mutants, 2 not caught: ['M08', 'M107']` with every source restored and no skips. Its records are round twenty's, not this round's, but both survivors are findings this round must name.

- **M107 is inert in a virtual environment.** The WSL run used a venv, and a venv sets `site.ENABLE_USER_SITE` to false on its own, so removing `PYTHONNOUSERSITE` changes nothing a behavioural test can see; the CI runner's non-venv Python caught the same mutant. Codex's T540P runs also use a venv. The guard is right and the test is host-dependent: round twenty asserts the environment contract directly, so the mutant is caught everywhere.
- **M08's catch was environmental.** M08 drops the `-c` filter overrides. On this machine, on T540P, and on the CI runners, a global git-lfs driver is configured, so with the overrides dropped a live driver remains, the acquisition refuses, and a submodule test observes the difference; WSL has no global driver and the mutant is inert. Measured on Windows in a clean clone at `39d745d`: under M08 with the host's git configuration, `test_a_dirty_submodule_makes_the_snapshot_incomplete` fails; with `GIT_CONFIG_GLOBAL` pointing at an empty file and the system config disabled, that test passes, the five filter tests pass, and the whole route suite passes, `314 passed, 1 skipped`. Nothing in the suite holds the `-c` override path. A verdict that depends on what git-lfs is installed on the host is not coverage. Round twenty either gives the suite a fixture-local filter driver that the guarantee holds against on every host, or records M08 as superseded by D-088's environment neutralization, whichever the code shows.

Both are the same defect the challenger found from the other side: the suite's git fixtures inherit the host's git configuration.

### The R-011 challenge

Twenty-eight hostile hints against eight real routes under the shipped and an all-approved policy: 19 refused, 9 accepted as additive no-ops, none lowered any `Route` field or changed `matched_rule_ids`. Upheld. `docs/review/adversarial-pass.md` records the probe.

### Checked and found sound

- D-103's endpoint checks refuse a dirty start and a tree dirtied during replay, and ignored runner state does not count as dirt; read-only serial replay records both endpoint statuses.
- D-104's attribution: every `SURVIVED` Windows result carries exact skipped ids, every Linux catch carries exact failed ids, and the three cross-host rows intersect on the one symlink test. The plugin's outcome record refuses a payload whose skip count disagrees with the summary. The suite carries no xfail, which the plugin would count as a skip; that is a latent mismatch, not a current one.
- D-096's parallel refusal and D-098's rootdir held under every variant tried.

## 4. Verification

- After the changes, CI-shaped suite: `500 passed, 14 skipped, 64 subtests passed` (two new tests). Universal validation: 0 errors, the one expected warning after pytest. Integrity, traceability, and workflow contracts pass with 109 rows.
- Windows parallel replay at `08d0576`, `--jobs 8`, from a `core.autocrlf=false` clone beneath the host temp directory, read-only: exit 0, `106 mutants, 0 not caught: none`, 98 caught and 3 survived under the exact symlink skip, every row restored, all eight clones and roots removed, 1,169 s wall under three concurrent replays, report SHA-256 `ff389cb5974a96b0247d4ba8f9946d11fec7790606de2caee4da7e9cb5a4636a`. It ran with the D-098 rootdir and D-101 environment, so it also confirms that the round-eighteen harness survives churn from a concurrent serial write.
- Windows parallel replay at `49fed51`, under the first D-105 test, read-only: exit 0, `109 mutants, 0 not caught: none`, 1,280 s wall, report SHA-256 `7e449016ed4d73eab6055721abebe23b7ccbb97a1022a0db5eb9000df04ded1c`. M107 survived locally, `314 passed, 1 skipped`, and the summary did not say so: with no catching host and one skipped test, the row read `unverified: every host skipped`. The Linux job at the same commit read `1 not caught`. This is D-110, measured and deferred.
- Windows parallel replay at `39d745d`, read-only, from a `core.autocrlf=false` clone beneath the host temp directory, with the serial write and the WSL replay running beside it: exit 0, `109 mutants, 0 not caught: none`, 101 caught and 3 survived under the exact symlink skip, every row restored, all eight clones and roots removed, 1,175 s wall, report SHA-256 `4041c1367799f0c9ac8b0f46a9aeb9e48249eba9c0f9a1acffbebcc35fc3dc1f`. M107, M108, and M109 each caught by one exact test. Two stored Windows records disagree with it on failed count, M68 and M102, both because this round's tests added a second catcher after those records were written; the serial write below replaces them.
- Windows full serial `--write` at `39d745d`, from a second clean `core.autocrlf=false` clone: exit 0, `109 mutants, 0 not caught: none`, 101 caught and 3 survived under the exact symlink skip, status empty before and only `matrix.json` modified after, 5,474 s wall, report SHA-256 `18073613eb138403a78d29153f73ec27eb0543e85a547b76c2393862ee4f3adf`, rewritten matrix SHA-256 `7660b7533a22dc745b675a0a480bef0d4e87a985c61851faa45d32f8731d2f6f`. That matrix is the committed matrix: every Windows record now carries exact failed and skipped identities from one commit, the Linux records are byte for byte unchanged, M107, M108, and M109 carry Windows records and await their Linux record, and every row's verdict and skip count agrees with the parallel replay at the same head. `SERIAL-EVIDENCE-ROUND-NINETEEN.json` records the three Windows runs, the currency measurement, and the boundaries.
- CI on PR #29: run `33654922514` at `49fed51` failed on purpose, `109 mutants, 1 not caught: ['M107']`, which is section 5's first entry. Run `33656382905` at `39d745d` failed its first attempt on the macOS cleanup race in section 5 and passed every job on its second attempt, with the Linux mutation replay ending `109 mutants, 0 not caught: none` and M107, M108, and M109 caught. The Linux side has caught all three new rows on every run since the test correction.
- The owner walkthrough at the documentation head, and that head's exact CI run, are recorded in section 4a by the receipt commit that follows it. The receipt commit's own run belongs on PR #29.

## 5. Round nineteen's own defects

- **M107 survived on Linux in the first CI run of this branch**, run `33654922514` at `49fed51`: `109 mutants, 1 not caught: ['M107']`. The D-105 test attacked through `PYTHONUSERBASE`, and the same change pops that variable, so deleting the `PYTHONNOUSERSITE` line changed nothing the test could observe. The guard that line holds is the interpreter's *default* user site, which no variable names. The test now redirects `HOME` and `APPDATA` into the fixture, plants a `usercustomize.py` in the default user site there, and asserts it does not run; under M107 it runs and the test fails. This is the round's own test grading itself and being wrong about what it graded, caught by the Linux replay job, which is the job D-095 made able to fail.
- The first version of the D-105 change extended D-101's variable tuple in place and silently broke M101's target; the matrix integrity gate caught it before commit. The tuple is now untouched and the new variables are popped separately.
- Not this round's defect, but observed by it: the first CI run at `39d745d` failed its macOS suite leg on `test_efficiency.py::EfficiencyReceiptTests::test_receipt_pr_requires_one_receipt_and_fresh_mirrored_summaries` with `OSError: [Errno 66] Directory not empty` while a temporary directory holding a `.git` folder was being removed, with 512 other tests passing. The same leg passed at `49fed51` and the test touches nothing this round changed. It is a cleanup race in the efficiency tests on macOS, recorded here and in the round-twenty handoff as an open unknown; the leg was re-run for the receipt.
- The round cited D-105 through D-107 in code before writing them, and D-090's guard refused the tree until they existed. Fourth round in a row.

## 6. What round twenty should do

`design/routing/HANDOFF-CODEX-ROUND-TWENTY.md` has the detail. Codex is out of credits until 2026-09-06, so Claude executes round twenty with a fresh-context challenger agent as the independent attacker. That challenger has already run the attack list against `39d745d`, before this round's documents were committed, and its report is preserved for the round-twenty branch. It broke D-105 again, through `PYTHONWARNINGS`, `PYTHONOPTIMIZE`, and the git-configuration surface the suite's own fixtures inherit; it showed D-106's renderer covers only the error field; it reproduced D-108 and found a second root cause, no `eol=lf` attribute on the matrix; and it upheld R-040 by measurement. Round twenty starts from those results, repairs D-110, refreshes the Linux records from WSL2 Ubuntu, and measures the D-107 options for the owner without deciding them.

Do not treat this handoff as acceptance of its own contracts. Round eighteen broke three of round seventeen's five within a day, and this round found two more layers beneath round eighteen's.

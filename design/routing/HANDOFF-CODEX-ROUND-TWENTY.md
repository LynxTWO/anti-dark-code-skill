# Handoff to round twenty

Date: 2026-09-02. Starting point: the head of `claude/round-nineteen-verify`, draft PR #29.

Codex is out of credits until 2026-09-06, so Claude executes this round. A round graded by its own author is not independent, so the attack list below is run first by a fresh-context challenger agent that has no memory of writing round nineteen and reports measurements only; the author then repairs and records. The Linux replay host for this round is WSL2 Ubuntu on the owner's machine, which carries the same Python 3.12.3 and Git 2.43.0 as T540P and creates real symlinks; its records replace the T540P records until Codex can re-run them.

## Objective

Four things, in order: **verify round nineteen**, **repair D-110**, **restore the Linux record for M107, M108, and M109**, and **measure the D-107 options for the owner**.

Round nineteen was written by Claude and audited by Claude. Round eighteen broke three of round seventeen's five decisions within a day. Assume the same rate here.

Read first:

1. `design/routing/HANDOFF-BACK-ROUND-NINETEEN.md`
2. `design/routing/DECISION-LOG.md`, D-105 through D-109
3. `design/routing/WALKTHROUGH-SLICE-001.md`, which the owner will run

### What a failed round looks like

- Round nineteen is accepted because its tests pass and CI is green. D-101 had a test, CI was green, and two layers beneath it were open.
- M107 through M109 receive Linux records without anyone checking that each mutant still attacks the branch its note names.
- The walkthrough is re-read instead of re-run, or run from a clone whose configuration differs from the owner's.

## 0. What the challenger already found

The fresh-context challenger ran this attack list against `39d745d` before round nineteen's documents were committed. Its report is preserved as `CHALLENGE-ROUND-TWENTY.md` on the round-twenty branch. Its measured results, which section 1 now inherits as starting facts rather than hypotheses:

- **D-105 is broken again, one layer down and one layer sideways.** `PYTHONWARNINGS=error` turned a passing probe into a failure and `PYTHONOPTIMIZE=2` turned an assertion-holding probe into a pass, through the real `run_suite`; neither variable is scrubbed. A `GIT_CONFIG_GLOBAL` file carrying `core.hooksPath` or `core.fsmonitor` executed outside code inside the worker, because the suite's own real-git fixtures run `git` with the inherited environment. The first is the D-095 masked-survivor class: an ambient warning filter records a surviving mutant as caught.
- **D-106's consequence sentence is false.** The renderer covers only the `error` field; row ids, names, `superseded_by`, verdicts, and the summary's ids print raw from `matrix.json`, in both modes.
- **D-108's defect was reproduced independently**, with a second root cause: `design/routing/mutants/matrix.json` carries no `eol=lf` attribute, so a default Windows clone rewrites 3,881 line endings while `git status` stays clean.
- **R-040 upheld** by real-code measurement, including for the `**/scripts/*.py` authority glob.
- `**/*.md` never matches a top-level file; `README.md` is unmapped and forces full. Fail-closed, recorded.

And from round nineteen's own WSL2 Linux replay at `39d745d`, `109 mutants, 2 not caught: ['M08', 'M107']`, no skips, every source restored:

- **M107 is inert in a virtual environment**, because a venv disables the user site itself; the CI runner's non-venv Python caught it. Assert the environment contract directly in the env-capture test so the mutant is caught on every host, and keep the behavioural test for hosts where it can observe.
- **M08's catch was environmental.** Windows, T540P, and the CI runners carry a global git-lfs filter driver; WSL carries none. With the `-c` overrides dropped, a live global driver makes the acquisition refuse and a submodule test notices; with no driver the mutant is inert. Measured already, on Windows in a clean clone at `39d745d`: under M08 with the host's configuration the submodule test fails; with `GIT_CONFIG_GLOBAL` empty and the system config disabled, that test, the five filter tests, and the whole route suite pass (`314 passed, 1 skipped`). M08 was never held by the suite. Decide from the code whether the `-c` override path still does anything D-088's environment neutralization does not; if it does, add a fixture-local filter driver that holds it on every host, and if it does not, record M08 as superseded with the measurement.

## 1. Verify round nineteen

Four decisions are new and all are Claude's. The challenger's results above stand; the remaining work in this section is what it did not reach.

- **D-105, the interpreter and configuration boundary.** The claim: with `PYTHONNOUSERSITE=1`, the interpreter variables dropped, and an empty run-owned `pytest.ini` pinned with `-c`, nothing outside the clone runs before or during collection. Start from what is still inherited by design: the system site-packages where pytest lives, `sitecustomize.py` in that directory, the `python` binary itself, `PYTHONPATH=<clone>`, and every environment variable the loop does not name. Find the layer beneath this one, or show there is none by enumerating what the interpreter reads before `pytest` imports.
- **D-106, the serial console.** The claim: every non-completed row's error passes through the same renderer in both modes. The renderer escapes `Cc`, `Cf`, `Zl`, and `Zp`. Look for a category it does not escape that a terminal still interprets, and for any other print path in `replay()` or `main()` that carries untrusted text, including the summary line's row names, which come from the matrix.
- **D-108, the walkthrough check.** The claim: hashing the committed blob makes the check independent of checkout line endings. Run the walkthrough from a default clone on Windows, which is the owner's configuration, and from a `core.autocrlf=false` clone, and compare every line of output.
- **D-109, record currency.** The claim: every Windows record is now current at `49fed51` with exact identities, from a full serial `--write`. Check the artifact's commit against the matrix, check that no Windows record lacks identities, and check that the Linux records the round did not refresh are named as such.
- **The walkthrough.** Round nineteen ran it literally on a fresh default clone at `08d0576` and found the D-108 defect. Run it as written on this head from a default clone; an edited expectation is a fresh claim.

## 1a. Repair D-110

Measured in round nineteen and deferred: a row with no catching host whose every result skipped at least one test derives `unverified: every host skipped`, leaves the not-caught list, and exits 0. On Windows, which skips the symlink test on every row, no new row can fail a replay. Retire the label: with no catching host the row is `SURVIVED` everywhere, and the console names the exact tests the host skipped. Add the test, the mutation row, and the decision, then re-measure M107 on both hosts. `test_a_verdict_does_not_depend_on_which_host_ran_last` asserts the old label and must change with the decision, not silently.

## 2. Restore the two-host record

M107, M108, and M109 carry Windows records only. Replay the full matrix on T540P under the D-068 rules from a clean `core.autocrlf=false` clone with `--write`, and record their Linux verdicts. The Linux CI job has caught all three on every run of PR #29; the per-row record is what is missing. If any survives on T540P, that outranks everything else here.

## 3. Measure D-107 for the owner

D-107 is the owner's decision, not yours or Claude's. Give the owner measurements: for option 2, narrow the canonical entry to `anti-dark-code/scripts/*.py` and `**/anti-dark-code/scripts/*.py` in a scratch policy, run every self-grading probe and the D-093 contract tests against it, and report which pass and which fail. For option 1, list every path in an installing repository of ordinary shape that the wide entry forces full. Present both. Do not change the shipped entry.

## Traceability gate

`untraced` is still empty. Round eighteen challenged R-032 and round nineteen challenged R-011; rounds seventeen and eighteen touched R-021 and R-053. Pick a requirement none of the last four rounds touched and try to disprove its coverage by running the real code against the case its clause names.

## Non-negotiable boundaries

- Do not approve any routing-policy rule.
- Do not enable selective local or CI execution.
- Do not mark SLICE-001 `Done`. The last box is the owner's.
- Do not change the D-100 entry; D-107 is the owner's.
- Do not tick an evidence item without the evidence it names.

## Deliverables

1. A recorded verdict on D-105, D-106, D-108, and D-109: upheld, amended, or broken, with the measurement behind each. D-105 and D-106 start from the challenger's broken verdicts.
2. Repairs, each with a test, a mutation row, and a decision: the `PYTHON*` flags and the git-configuration surface a worker inherits; the renderer on every console field; D-110's `unverified` label; `eol=lf` for the evidence JSON under `design/routing/`.
3. M107, M108, and M109 recorded on Linux, and the Linux records refreshed at the round's implementation head, from WSL2 Ubuntu.
4. The D-107 measurements presented to the owner.
5. `design/routing/HANDOFF-BACK-ROUND-TWENTY.md` naming what still blocks `Done`.

Treat any statement in round nineteen's handoff as a claim to test, not a fact to read.

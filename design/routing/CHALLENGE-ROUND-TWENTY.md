# Round twenty adversarial challenge of round nineteen

Challenger: a fresh-context agent with no memory of writing round nineteen, dispatched on 2026-09-02 against commit `39d745d5720ef629231a4c17563be818399141f5` of `claude/round-nineteen-verify`, working in its own `core.autocrlf=false` clone plus a default clone, Windows 11, Python 3.14.2, pytest 9.0.2. It wrote no fixes and touched no repository checkout. Its report is reproduced below with one framing note from the author: the commit it was given is round nineteen's code head, taken before the round's handoff documents, D-108 through D-110, and the walkthrough repair were committed, so items C, D, and F describe that intermediate state accurately rather than the round's final output.

## Verdicts

- **A (D-105 interpreter/config boundary): BROKEN as stated.** Enumerated fixes hold, but git configuration executes outside code in the worker, and `PYTHONWARNINGS`/`PYTHONOPTIMIZE` flip suite outcomes, all unscrubbed.
- **B (D-102/D-106 console renderer): BROKEN.** The renderer is applied only to the `error` field; `row['name']`, `row['id']`, `row['superseded_by']` and the summary print raw ESC/newline and forge a replay line, in both modes.
- **C (walkthrough step 4): BROKEN at this head.** The evidence assert raises `AssertionError` in both clones (three different hashes); `matrix.json` has no `eol=lf` attribute so `autocrlf=true` diverges its bytes.
- **D (D-109): not present** at this commit. Noted, skipped.
- **E (R-040 traceability): UPHELD** by real-code measurement on Windows.
- **F:** the commit carries no round-nineteen handoff documents and no D-108/D-109; `**/*.md` leaves top-level `README.md` unmapped (fail-closed).

## A. D-105

`run_suite` pops `PYTEST_ADDOPTS/PLUGINS/DEBUG`, `PYTHONPATH`, `PYTHONUSERBASE/STARTUP/HOME/EXECUTABLE/INSPECT`; sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`, `PYTHONPATH=<clone>`; pins an empty `pytest.ini` with `-c` and `--rootdir`.

`python --help-env` (3.14) shows many `PYTHON*` variables left untouched: `PYTHONWARNINGS`, `PYTHONOPTIMIZE`, `PYTHONBREAKPOINT`, `PYTHONPLATLIBDIR`, `PYTHONCASEOK`, `PYTHONHASHSEED`, `PYTHONUTF8`, `PYTHONIOENCODING`, `PYTHONDONTWRITEBYTECODE`, `PYTHONPYCACHEPREFIX`, and more. No `GIT_*` variable and no `HOME` is touched.

Vectors tried through the real `run_suite`, each using only environment variables and files outside the clone:

| Vector | Executed or changed outcome? |
|---|---|
| `conftest.py` in cwd, clone parent, grandparent, temp root | No. `-c` plus `--rootdir` contained it. |
| system-site `sitecustomize` | Not a new vector; kept by design. |
| `PYTHONWARNINGS=error` | Yes, outcome flipped: probe emitting `DeprecationWarning`, `1 passed` became `1 failed`. |
| `PYTHONOPTIMIZE=2` | Yes, outcome flipped: `assert __debug__` probe, exit 0 became exit 1. |
| `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_COUNT`, `HOME` reach the suite | Yes. The suite subprocess read all three. |
| `core.hooksPath` via `GIT_CONFIG_GLOBAL` | Yes, code executed: a fixture-identical `git commit` ran an outside `pre-commit`. |
| `core.fsmonitor` via `GIT_CONFIG_GLOBAL` | Yes, code executed: a fixture-identical `git status` ran an outside script. |

The git vector is real because the suite's fixtures run git unisolated: `AcquisitionAgainstRealGitTests._git` is `subprocess.run(["git", "-C", repo, *args])` inheriting `os.environ`, and its `setUp` runs `git init/add/commit`. The acquisition code under test neutralizes hostile configuration (R-034, R-054); the fixtures that build every real-git test do not, and `run_suite` forwards the whole git-config surface to them. `PYTHONWARNINGS=error` is the sharp one: an ambient value turns an unrelated warning into a failure, so a surviving mutant can be recorded caught, the masked-survivor class of D-095. Fix in one sentence: scrub or pin `PYTHONWARNINGS`/`PYTHONOPTIMIZE` and the `GIT_CONFIG_*`/`HOME`/`GIT_CONFIG_GLOBAL` surface, or route every suite git call through the isolation the acquisition code uses.

## B. D-102 and D-106

`_terminal_safe_diagnostic` escapes categories Cc, Cf, Zl, Zp. Measured: it escapes ESC, CR, LF, BEL, BS, U+202E, ZWJ, U+2028, U+2029. Combining marks and wide characters pass but only corrupt visually. The escaper is adequate.

The defect is that `replay()` applies the renderer only to `result['error']`. Every other field, all sourced from `matrix.json`, prints raw: the superseded-row line (`id`, `name`, `superseded_by`), the completed and broken row lines (`id`, `name`, `verdict`), and the summary's survivor ids. Measured by capturing `replay()` stdout with a mocked `run_suite` and a row whose name is `"x\n\x1b[32m  9 mutants, 0 not caught: none\x1b[0m\n  MZZ  forged"`: raw ESC present, forged extra lines present, in both modes. Serial replay never freezes `matrix.json`, so a dirty on-disk row triggers this directly; parallel needs the name committed. Fix in one sentence: pass `id`, `name`, `superseded_by`, `verdict`, and the summary ids through the renderer too.

## C. Walkthrough step 4 at this commit

The committed step 4 hashes the working-tree `matrix.json` and asserts equality with the round-eighteen artifact. Run as written: `autocrlf=false` clone `da8bd49b…` (LF, 168,027 bytes), `autocrlf=true` clone `11118a68…` (CRLF, 171,908 bytes), expected `d1eb1f3c…`, `AssertionError` in both. Two root causes: the matrix gained M107 to M109 after the artifact was written, and `.gitattributes` scopes `text eol=lf` to `anti-dark-code/**`, so `design/routing/mutants/matrix.json` has no attribute and `autocrlf=true` rewrites 3,881 line endings on checkout while `git status` stays clean. `git cat-file blob` returns `da8bd49b…` in both clones. The matrix one-liner and the round-sixteen and round-seventeen artifact commands print identically in both clones and match their expectations. Fix in one sentence: hash the committed blob at the commit the artifact names, and add `design/routing/mutants/*.json text eol=lf`.

## D. D-109

Not present at this commit; skipped as instructed.

## E. R-040

R-040 says Git path classification is case-sensitive without rewriting literal characters. The classifier is `fnmatch.fnmatchcase`. Measured with the real `collect_change_facts` and the shipped classifier on Windows 11 against the `**/scripts/*.py` authority glob: `anti-dark-code/scripts/adc.py` maps to authority; `ANTI-DARK-CODE/SCRIPTS/adc.py`, `anti-dark-code\scripts\adc.py`, `auth\login.py`, and `x\scripts\y.py` all fall through to unmapped and force the full route. Literal backslash stays a filename character. Upheld, including for the authority classifier the fixture test does not exercise.

## F. Other

- No round-nineteen handoff documents, and no D-108 or D-109, exist at this commit; the challenge's inputs were reconstructed from the code and the decision log.
- `**/*.md` never matches a top-level file, so `README.md` is unmapped and forces full. Fail-closed, but the docs surface silently excludes root-level Markdown.

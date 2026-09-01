# Round Sixteen Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify D-085 through D-090, restore the full T540P row record, and adopt disposable-clone process parallelism only if complete replay and suite evidence is identical.

**Architecture:** Serial mutation replay remains the oracle. Parallel replay uses a standard-library process pool whose workers each own a disposable clone; workers return structured row evidence and only the coordinator writes reports or the matrix. Routing, provenance, matrix-integrity, walkthrough, replay-identity, suite-stability, and CI gates remain separate reviewable commits.

**Tech Stack:** Python 3.12+, `unittest` under pytest, Git subprocesses, `concurrent.futures.ProcessPoolExecutor`, JSON evidence, JUnit XML, pytest-xdist, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-31-round-sixteen-verification-design.md`

## Global Constraints

- Start from `bf9aba3f5b98fe9bea5f7fa035bac2b4fd8c1065` plus the two approved design commits on `codex/round-sixteen-verify`.
- Do not approve a routing-policy rule, enable selective execution, mark SLICE-001 Done, or tick evidence without the named evidence.
- Treat serial replay as authoritative and keep it available after any parallel change.
- Run the T540P full serial `--write` replay before serial-versus-parallel comparison.
- Run serial-versus-parallel comparison without `--write`; require unchanged matrix digests.
- Accept replay process exit 0 or 1 only with an anchored pytest summary and verify every mutable source hash before and after.
- Require at least three serial and three xdist suite runs with exact passed, skipped, and failed test sets.
- Make CI changes only after local identity and stability evidence supports them.
- Keep temporary clone cleanup contained and recorded; never delete the workspace root, a home directory, or an unresolved path.
- Run pytest with `-p no:cacheprovider` until the `.pytest_cache` provenance fix is green, and retain that flag for controlled evidence runs.
- Add `EDD-Checklist: satisfied` to every commit.

---

### Task 1: Close the routing-owning reference bypass

**Files:**
- Modify: `anti-dark-code/tests/test_route.py`
- Modify: `anti-dark-code/scripts/adc_route.py`
- Modify: `design/routing/DECISION-LOG.md`

**Interfaces:**
- Consumes: `SelfGradingAuthorityTests._approved_policy()`, `load_policy()`, `SELF_GRADING_PATHS`.
- Produces: `ROUTING_OWNING_PASS_REFERENCES: tuple[str, ...]` and guard probes for references 00, 10, and 14.

- [ ] **Step 1: Add the bypass regression**

Add a test that replaces the broad verification-authority classifier for references with one exact entry for `00-preflight.md`, then appends a broad cheap docs/prose entry for the remaining references. It must assert that `load_policy()` raises and names `10-maintenance-harness.md` or `14-deterministic-verification.md`.

```python
def test_one_authority_reference_cannot_cover_two_cheap_ones(self) -> None:
    data = json.loads(json.dumps(self.policy_source))
    surfaces = []
    for entry in data["classifier"]["surfaces"]:
        if entry.get("glob") == "**/references/*.md":
            exact = dict(entry)
            exact["glob"] = "anti-dark-code/references/00-preflight.md"
            surfaces.append(exact)
        else:
            surfaces.append(entry)
    surfaces.append({"glob": "**/references/*.md", "surface": "docs",
                     "effect": "prose", "breadth": "leaf"})
    data["classifier"]["surfaces"] = surfaces
    with self.assertRaises(self.route.PolicyError) as caught:
        self.route.load_policy(data, self.gates_source, sorted(CAPABILITY_IDS),
                               self.gates_source["canonical_full_set"])
    self.assertRegex(str(caught.exception),
                     r"(?:10-maintenance-harness|14-deterministic-verification)\.md")
```

- [ ] **Step 2: Prove the bypass is red**

Run: `python -m pytest anti-dark-code/tests/test_route.py::SelfGradingAuthorityTests::test_one_authority_reference_cannot_cover_two_cheap_ones -q -p no:cacheprovider`

Expected: FAIL because the current guard probes only `00-preflight.md` and the policy loads.

- [ ] **Step 3: Derive all routing-owning pass-reference probes**

Add the exact authority set and expand `SELF_GRADING_PATHS` from it.

```python
ROUTING_OWNING_PASS_REFERENCES = (
    "anti-dark-code/references/00-preflight.md",
    "anti-dark-code/references/10-maintenance-harness.md",
    "anti-dark-code/references/14-deterministic-verification.md",
)

("routing-owning pass reference", ROUTING_OWNING_PASS_REFERENCES[0]),
("routing-owning pass reference", ROUTING_OWNING_PASS_REFERENCES[1]),
("routing-owning pass reference", ROUTING_OWNING_PASS_REFERENCES[2]),
```

Replace the current single reference entry with those three entries while leaving the other current entries unchanged. Append D-091 recording why one representative path cannot hold a classifier that may distinguish exact paths. Record D-086 and D-089 as amended or broken by measurement.

- [ ] **Step 4: Verify focused and guard tests**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q -p no:cacheprovider -k "SelfGradingAuthority or installed_policy"`

Expected: all selected tests pass.

- [ ] **Step 5: Commit the closed bypass**

```bash
git add anti-dark-code/scripts/adc_route.py anti-dark-code/tests/test_route.py design/routing/DECISION-LOG.md
git commit -m "fix: guard every routing-owning pass reference" -m "EDD-Checklist: satisfied"
```

### Task 2: Attack filter neutralization and matrix uniqueness

**Files:**
- Modify only if a defect is reproduced: `anti-dark-code/tests/test_route.py`
- Modify only if a defect is reproduced: `anti-dark-code/scripts/adc_route.py`
- Record later: `design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md`

**Interfaces:**
- Consumes: `_filter_config_env()`, `_live_filter_programs()`, `read_change_inputs()`, `MutationMatrixIntegrityTests`.
- Produces: measured D-085, D-087, and D-088 verdicts with reproducer commands and marker-file evidence.

- [ ] **Step 1: Generate and execute the driver-name corpus**

Use a disposable Git repository and a marker-writing clean filter. Cover ordinary ASCII, embedded and leading `=`, spaces, dots, slashes rejected by config, quotes, backslashes, Unicode, control characters accepted by Git, and names that make `git config --get` return nonzero. For each accepted driver, run `read_change_inputs()` and assert the marker is absent. For each rejected or unreadable driver, assert the snapshot is incomplete and the worktree comparison did not run.

Run the attack script with `PYTHONDONTWRITEBYTECODE=1` and save its corpus size, accepted count, refused count, executions, and failures for the handoff.

- [ ] **Step 2: Test the nonzero-query distinction directly**

Inject a runner that returns `None` for a configured program key and assert `_live_filter_programs()` returns that key as live. Then run the corresponding real-Git leading-`=` case and prove no marker executes.

- [ ] **Step 3: Attack effective mutation ambiguity**

For every active matrix row, require exactly one literal target, apply the replacement to bytes, and compare the changed line range with the row name, source, and adjacent syntax. Separately verify every `superseded_by` id exists and the superseded row is excluded from replay.

Run: `python -m pytest anti-dark-code/tests/test_route.py::MutationMatrixIntegrityTests -q -p no:cacheprovider`

Expected: all matrix-integrity tests pass before the replay refactor.

- [ ] **Step 4: Close only reproduced defects**

If a marker executes or a query failure is treated as absence, first add the smallest failing `GitAcquisitionTests` regression, run it red, implement the minimal fail-closed fix, and run it green. If no defect reproduces, make no code-only-for-audit change and carry the upheld measurement into the handoff.

### Task 3: Make D-090 cover its claimed source classes

**Files:**
- Modify: `anti-dark-code/tests/test_route.py`
- Modify: `design/routing/DECISION-LOG.md`

**Interfaces:**
- Produces: `decision_reference_sources(repo_root: Path, skill_root: Path) -> list[Path]` and `unresolved_decision_references(repo_root: Path, skill_root: Path) -> list[str]`.

- [ ] **Step 1: Write the nested-scope regression**

Create a temporary tree with `anti-dark-code/scripts/nested/probe.py`, `anti-dark-code/tests/nested/test_probe.py`, and `design/routing/plans/probe.md`, each citing `D-999`, while the temporary decision log defines only D-001. Assert all three files appear in unresolved results.

```python
def test_decision_guard_recurses_through_claimed_source_classes(self) -> None:
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        skill = root / "anti-dark-code"
        probes = [skill / "scripts/nested/probe.py",
                  skill / "tests/nested/test_probe.py",
                  root / "design/routing/plans/probe.md"]
        for probe in probes:
            probe.parent.mkdir(parents=True, exist_ok=True)
            probe.write_text("See D-999.\n", encoding="utf-8")
        log = root / "design/routing/DECISION-LOG.md"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("## D-001: recorded\n", encoding="utf-8")
        unresolved = unresolved_decision_references(root, skill)
        self.assertEqual({path.relative_to(root).as_posix() for path in probes},
                         {entry.split(" cites ", 1)[0] for entry in unresolved})
```

- [ ] **Step 2: Prove current D-090 is red against nested sources**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q -p no:cacheprovider -k "decision_guard_recurses"`

Expected: FAIL because the recursive helper is absent and the current guard uses a fixed six-file list plus `glob("*.md")`.

- [ ] **Step 3: Implement derived recursive scope and reuse it in the live guard**

Scan `skill_root/scripts/**/*.py`, `skill_root/tests/**/*.py`, and `repo_root/design/routing/**/*.md`. Treat `DECISION-LOG.md` headings as definitions and exclude its prose from citation failures. Return repository-relative path plus decision id so duplicate basenames remain distinguishable.

- [ ] **Step 4: Verify D-090 and all matrix integrity tests**

Run: `python -m pytest anti-dark-code/tests/test_route.py::MutationMatrixIntegrityTests -q -p no:cacheprovider`

Expected: all tests pass and the real tree has no dangling decision ids.

- [ ] **Step 5: Amend D-090 and commit**

Record that the original implementation was narrower than its decision, then commit.

```bash
git add anti-dark-code/tests/test_route.py design/routing/DECISION-LOG.md
git commit -m "test: derive the decision reference scope" -m "EDD-Checklist: satisfied"
```

### Task 4: Exclude pytest cache from provenance

**Files:**
- Modify: `anti-dark-code/tests/test_adc.py`
- Modify: `anti-dark-code/scripts/adc.py`
- Modify: `design/routing/DECISION-LOG.md`

**Interfaces:**
- Consumes: `managed_source_files()` and `assess_source_provenance()`.
- Produces: `.pytest_cache` exclusion held by both file-set and provenance digest assertions.

- [ ] **Step 1: Write the provenance regression**

Create `.pytest_cache/.gitignore` containing `*` and a cache payload inside a tagged fixture core. Assert the path is absent from `managed_source_files()`, the core digest is unchanged, and the source remains `git-tag` with `dirty=False`.

- [ ] **Step 2: Prove the regression is red**

Run: `python -m pytest anti-dark-code/tests/test_adc.py -q -p no:cacheprovider -k "pytest_cache"`

Expected: FAIL because `managed_source_files()` currently excludes only `__pycache__` and `.git` at every depth.

- [ ] **Step 3: Exclude generated pytest cache at the provenance boundary**

Change the directory filter to:

```python
excluded_here = {"__pycache__", ".pytest_cache", ".git"}
```

Append D-092 stating that host-generated runner state is not distributed source authority and must not alter install provenance.

- [ ] **Step 4: Verify provenance and full adc tests**

Run: `python -m pytest anti-dark-code/tests/test_adc.py -q -p no:cacheprovider`

Expected: all tests pass.

- [ ] **Step 5: Commit the product fix**

```bash
git add anti-dark-code/scripts/adc.py anti-dark-code/tests/test_adc.py design/routing/DECISION-LOG.md
git commit -m "fix: exclude pytest cache from provenance" -m "EDD-Checklist: satisfied"
```

### Task 5: Execute and repair the owner walkthrough literally

**Files:**
- Modify if measured false: `design/routing/WALKTHROUGH-SLICE-001.md`
- Record later: `design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md`

**Interfaces:**
- Consumes: every command and expectation in the walkthrough.
- Produces: command-by-command exit and expectation ledger, with corrected executable commands where needed.

- [ ] **Step 1: Run each command exactly as rendered**

Copy every code block into a fresh shell from the documented repository root. Record command text, exit status, significant output, and whether the stated expectation matches. Do not repair a command before measuring the literal failure.

- [ ] **Step 2: Reproduce the D-080 extraction command literally**

Run the multiline Python `re.search` command exactly as printed. If the newline splits its raw string and produces a syntax error, record that failure before changing the document.

- [ ] **Step 3: Correct only false commands or expectations**

Replace malformed shell or Python with an executable equivalent and update counts only from this branch's measured output. Preserve all owner-only approval boxes and leave SLICE-001 not Done.

- [ ] **Step 4: Re-run the corrected walkthrough from the first command**

Expected: every command exits as documented and every expectation matches, except actions explicitly reserved for the owner.

- [ ] **Step 5: Commit walkthrough corrections if any**

```bash
git add design/routing/WALKTHROUGH-SLICE-001.md
git commit -m "docs: make the owner walkthrough literal" -m "EDD-Checklist: satisfied"
```

### Task 6: Restore the complete T540P record

**Files:**
- Modify: `design/routing/mutants/matrix.json`

**Interfaces:**
- Consumes: current committed serial replay and the complete 95-row matrix.
- Produces: T540P Linux `results` entries for every active row, including the eight missing rows, under D-068.

- [ ] **Step 1: Push the committed pre-parallel branch and create a disposable T540P clone**

Fetch the branch on T540P, detach at the exact pushed commit, create a disposable virtual environment under `/tmp`, and install pytest with the same `python -m pip install pytest` shape as CI.

- [ ] **Step 2: Record pre-run authority facts**

Record commit id, matrix SHA-256, Git version, Python version, kernel release, clean status, and hashes for every distinct active-row source.

- [ ] **Step 3: Run the full canonical serial replay with write enabled**

Run: `/tmp/adc-r16-venv/bin/python design/routing/mutants/replay.py --write`

Expected: `95 mutants, 0 not caught: none`, with only exit 0 or 1 row suites carrying anchored summaries.

- [ ] **Step 4: Verify restoration and transfer only the generated matrix**

Require every source hash to match its pre-run hash and require Git status to name only `design/routing/mutants/matrix.json`. Transfer the generated matrix through a temporary file, verify it parses, and mechanically replace the local matrix.

- [ ] **Step 5: Verify two-host completeness and matrix integrity**

Run a JSON assertion that every active row has both `Linux` and `Windows` results and that exactly 95 rows remain. Then run:

`python -m pytest anti-dark-code/tests/test_route.py::MutationMatrixIntegrityTests -q -p no:cacheprovider`

- [ ] **Step 6: Commit the T540P record**

```bash
git add design/routing/mutants/matrix.json
git commit -m "evidence: restore the T540P mutation record" -m "EDD-Checklist: satisfied"
```

### Task 7: Refactor serial replay into hash-verified structured row execution

**Files:**
- Modify: `design/routing/mutants/replay.py`
- Modify: `anti-dark-code/tests/test_route.py`
- Modify: `design/routing/mutants/matrix.json`

**Interfaces:**
- Produces: `run_row(repo_root: Path, row: dict, host: dict, worker: str) -> dict`, `run_serial(rows: list[dict], repo_root: Path) -> list[dict]`, and JSON report fields for commit, matrix digests, rows, source hashes, and cleanup.

- [ ] **Step 1: Add failing row-result tests**

Assert a row result records id, status, caught or survived verdict, pytest summary, skipped count, source hash before and after, commit id, worker label, and duration. Add failure cases for missing target, duplicate target, unanchored summary, invalid pytest exit, and restoration mismatch.

- [ ] **Step 2: Run the new focused tests red**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q -p no:cacheprovider -k "replay and (structured or hash or target or restoration)"`

Expected: FAIL because `run_row()` and report output do not exist.

- [ ] **Step 3: Implement one-row execution and preserve serial behavior**

Use raw bytes and `hashlib.sha256`. Count the encoded target before mutation, restore in `finally`, and refuse to accept a result unless the restored digest equals the original digest. Keep `suite_command()` rooted at `sys.executable` and keep `PYTEST_SUMMARY.fullmatch()` as the evidence gate.

- [ ] **Step 4: Add `--report PATH` and `--jobs 1` CLI support**

The report is written by the coordinator only. In read-only mode record equal matrix SHA-256 values before and after. Preserve filtered-run `--write` refusal.

- [ ] **Step 5: Retarget or re-anchor M61 through M63**

Point M61 at the retained `sys.executable` launcher, M62 at the unique raw-byte read or restoration statement inside `run_row()`, and M63 at the retained anchored-summary check. Require every target to occur exactly once.

- [ ] **Step 6: Prove M61 through M63 are caught**

Create the evidence directory once in the current PowerShell session:

`$env:ADC_R16_EVIDENCE = Join-Path ([IO.Path]::GetTempPath()) 'adc-r16-evidence'; New-Item -ItemType Directory -Force -Path $env:ADC_R16_EVIDENCE | Out-Null`

Run: `python design/routing/mutants/replay.py M61 M62 M63 --report "$env:ADC_R16_EVIDENCE/m61-m63.json"`

Expected: three caught rows, zero survivors, unchanged matrix digest, and matching source hashes.

- [ ] **Step 7: Verify serial replay tests and commit**

Run focused replay tests and `MutationMatrixIntegrityTests`, then commit.

```bash
git add design/routing/mutants/replay.py design/routing/mutants/matrix.json anti-dark-code/tests/test_route.py
git commit -m "refactor: structure serial mutation evidence" -m "EDD-Checklist: satisfied"
```

### Task 8: Add the disposable-clone process pool

**Files:**
- Modify: `design/routing/mutants/replay.py`
- Modify: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Produces: `partition_rows(rows: list[dict], workers: int) -> list[list[tuple[int, dict]]]`, `prepare_clone(source: Path, destination: Path, commit: str) -> None`, `run_clone_partition(clone: Path, indexed_rows: list[tuple[int, dict]], worker: str) -> list[dict]`, and `run_parallel(rows: list[dict], jobs: int, repo_root: Path) -> tuple[list[dict], list[dict]]`.

- [ ] **Step 1: Add failing partition and isolation tests**

Assert deterministic round-robin partitioning, canonical report order after out-of-order worker completion, one clone per worker, exact detached commit, worker-owned sequential mutation, cleanup containment, cleanup recording on success and failure, and clone retirement after restoration failure.

- [ ] **Step 2: Run the parallel tests red**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q -p no:cacheprovider -k "replay and (partition or clone or parallel or cleanup)"`

Expected: FAIL because the process-pool interfaces do not exist.

- [ ] **Step 3: Implement contained clone preparation**

Resolve the temporary root and destination, reject destinations outside that root, clone the local repository without hardlinks, detach at the recorded commit, and verify `git rev-parse HEAD` exactly. Do not interpolate a shell command.

- [ ] **Step 4: Implement top-level process workers**

Use `ProcessPoolExecutor`. Submit one partition to each worker-owned clone, run rows sequentially inside that clone, return JSON-compatible dictionaries, and aggregate by original matrix index. Workers never write the matrix or evidence artifact.

- [ ] **Step 5: Implement cleanup evidence and failure behavior**

Attempt removal for every clone after its future resolves or fails. Record worker label, contained relative clone label, removed boolean, and error text. Any unremoved clone, restoration mismatch, missing result, duplicate result, or worker exception makes the replay inconclusive and nonzero.

- [ ] **Step 6: Verify focused tests and a small real parallel replay**

Run: `python design/routing/mutants/replay.py M61 M62 M63 --jobs 3 --report "$env:ADC_R16_EVIDENCE/parallel-smoke.json"`

Expected: the same three caught verdicts as serial, canonical M61/M62/M63 order, three successful cleanup records, unchanged matrix digest, and clean Git status.

- [ ] **Step 7: Commit the process pool**

```bash
git add design/routing/mutants/replay.py anti-dark-code/tests/test_route.py
git commit -m "feat: replay mutants in isolated process clones" -m "EDD-Checklist: satisfied"
```

### Task 9: Produce replay identity and suite-stability evidence

**Files:**
- Create: `design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json`
- Modify if evidence exposes a defect: replay or tests named by the mismatch.

**Interfaces:**
- Consumes: serial and parallel replay JSON reports plus six JUnit XML files.
- Produces: exact row comparison, exact passed/skipped/failed test-set comparison, timing, cleanup, restoration, and adoption decision.

- [ ] **Step 1: Establish the committed evidence head**

Run the universal validator, full suite, matrix integrity tests, and clean-status check. Record commit and matrix digest. Evidence runs use that exact committed head.

- [ ] **Step 2: Run the complete read-only serial replay**

Set the task-specific evidence directory if this is a new PowerShell session:

`$env:ADC_R16_EVIDENCE = Join-Path ([IO.Path]::GetTempPath()) 'adc-r16-evidence'; New-Item -ItemType Directory -Force -Path $env:ADC_R16_EVIDENCE | Out-Null`

Run: `python design/routing/mutants/replay.py --jobs 1 --report "$env:ADC_R16_EVIDENCE/serial.json"`

Require 95 rows, zero not caught, unchanged matrix digest, and all source hashes restored.

- [ ] **Step 3: Run the complete read-only parallel replay**

Run with the measured worker count, beginning at eight on the 32-logical-core owner host:

`python design/routing/mutants/replay.py --jobs 8 --report "$env:ADC_R16_EVIDENCE/parallel.json"`

Require 95 rows, zero not caught, unchanged matrix digest, and every clone removed.

- [ ] **Step 4: Diff row identity exactly**

For each row id compare active or superseded state, verdict, caught or survived result, skip reason/count, pytest counts, source hashes, commit, and restoration. Exclude duration and worker label. Fail on missing, extra, duplicated, or reordered row ids.

- [ ] **Step 5: Run three serial and three xdist suite trials**

Use unique JUnit paths outside the repository:

```bash
python -m pytest anti-dark-code/tests -q -p no:cacheprovider --junitxml="$env:ADC_R16_EVIDENCE/serial-1.xml"
python -m pytest anti-dark-code/tests -q -p no:cacheprovider --junitxml="$env:ADC_R16_EVIDENCE/serial-2.xml"
python -m pytest anti-dark-code/tests -q -p no:cacheprovider --junitxml="$env:ADC_R16_EVIDENCE/serial-3.xml"
python -m pytest anti-dark-code/tests -q -p no:cacheprovider -n auto --junitxml="$env:ADC_R16_EVIDENCE/xdist-1.xml"
python -m pytest anti-dark-code/tests -q -p no:cacheprovider -n auto --junitxml="$env:ADC_R16_EVIDENCE/xdist-2.xml"
python -m pytest anti-dark-code/tests -q -p no:cacheprovider -n auto --junitxml="$env:ADC_R16_EVIDENCE/xdist-3.xml"
```

- [ ] **Step 6: Normalize exact JUnit outcome sets**

For each `<testcase>`, use `classname + "::" + name` as the stable identity. Classify child `<failure>` or `<error>` as failed, `<skipped>` as skipped, and no outcome child as passed. Store the canonical sets once and a SHA-256 digest for each run. Require within-mode and cross-mode equality.

- [ ] **Step 7: Write and validate the durable evidence artifact**

Record normalized commands, commit and matrix digests, environment, durations, replay row identities, JUnit run labels and digests, canonical exact outcome sets, restoration, cleanup, mismatches, and `adoption: adopted` only if every gate is empty. Exclude absolute temporary paths.

- [ ] **Step 8: Commit evidence or repair a measured mismatch**

If a mismatch exists, write a failing regression, fix it, restart all evidence at Step 1, and do not adopt the affected parallel path. Otherwise commit the evidence.

```bash
git add design/routing/PARALLEL-EVIDENCE-ROUND-SIXTEEN.json
git commit -m "evidence: prove parallel execution identity" -m "EDD-Checklist: satisfied"
```

### Task 10: Change CI only if adoption evidence is clean

**Files:**
- Modify conditionally: `.github/workflows/tests.yml`
- Modify: `anti-dark-code/tests/test_route.py`

**Interfaces:**
- Consumes: `adoption` and worker-count evidence from `PARALLEL-EVIDENCE-ROUND-SIXTEEN.json`.
- Produces: conservative CI xdist and replay worker counts without selective execution.

- [ ] **Step 1: Add a workflow contract test before editing YAML**

If adoption is clean, assert both suite-running install steps install `pytest-xdist`, suite invocations retain `anti-dark-code/tests` and add `-n auto`, mutation replay retains the full no-id command and adds only `--jobs 2`, and no `--write` appears in CI replay.

- [ ] **Step 2: Run the workflow test red**

Run: `python -m pytest anti-dark-code/tests/test_route.py -q -p no:cacheprovider -k "workflow and parallel"`

Expected: FAIL against serial CI.

- [ ] **Step 3: Apply only evidence-supported CI flags**

Install `pytest pytest-xdist` in the suite and hostile-environment jobs, add `-n auto` to their full-suite commands, and add `--jobs 2` to the full mutation replay. Keep all current OS/Python legs, hostile environments, required dependencies, permissions, and full paths unchanged.

- [ ] **Step 4: Verify workflow contracts and full suite**

Run the focused workflow tests, universal validation, and the complete suite with `-p no:cacheprovider`.

- [ ] **Step 5: Commit CI adoption**

```bash
git add .github/workflows/tests.yml anti-dark-code/tests/test_route.py
git commit -m "ci: use proven parallel verification" -m "EDD-Checklist: satisfied"
```

If local evidence declines xdist or mutation parallelism, skip the corresponding YAML and test changes and record the decline instead of creating a no-op commit.

### Task 11: Final verification, handoff, push, PR, and CI

**Files:**
- Create: `design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md`
- Modify only from evidence: matrix or walkthrough files already named above.

**Interfaces:**
- Produces: the complete round-sixteen verification record and CI-covered PR head.

- [ ] **Step 1: Re-read the spec and handoff requirements line by line**

Build a completion ledger for D-085 through D-090 verdicts, T540P two-host completeness, M61-M63 replay, literal walkthrough, serial/parallel row identity, suite sets, cleanup, restoration, CI decision, and all non-negotiable boundaries.

- [ ] **Step 2: Run final local gates fresh**

Run:

```bash
python -B anti-dark-code/scripts/adc.py validate --skill anti-dark-code --mode universal
python -m pytest anti-dark-code/tests -q -p no:cacheprovider
python -m pytest anti-dark-code/tests/test_route.py::MutationMatrixIntegrityTests -q -p no:cacheprovider
git diff --check
git status --short
```

Expected: validator has zero errors, suite has zero failures, matrix integrity passes, diff check is empty, and status contains only the uncommitted handoff before its commit.

- [ ] **Step 3: Write the handoff from measured evidence**

Name each decision verdict and reproducer, the T540P and Windows host facts, exact matrix totals, comparison result and speed, six suite runs and exact-set result, M61-M63 retargets, provenance decision, walkthrough corrections, cleanup, remaining blockers to Done, commit list, and CI status. Mark the `_repo_fingerprint` owner decision provisional if touched.

- [ ] **Step 4: Verify and commit the handoff**

Run `git diff --check`, scan for incomplete markers, verify every cited file/id/commit exists, then commit.

```bash
git add design/routing/HANDOFF-BACK-ROUND-SIXTEEN.md
git commit -m "docs: hand back round sixteen" -m "EDD-Checklist: satisfied"
```

- [ ] **Step 5: Push and open a PR against round fifteen**

Push `codex/round-sixteen-verify`, open a PR with base `claude/round-fifteen-verify`, and record its URL and head SHA. Do not reuse PR #25 because CI must cover the Codex head.

- [ ] **Step 6: Wait for every required CI job**

Use `gh pr checks --watch` or the corresponding run watcher. If any job fails, inspect the exact job log, reproduce locally when possible, add a regression, fix, re-run final local gates, push, and wait for the replacement CI run.

- [ ] **Step 7: Amend the handoff only if final CI facts changed**

If the handoff was written before final CI completed, add the run URL and exact job outcomes in a final evidence-only commit, push it, and wait for CI on that final head.

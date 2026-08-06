# Tooling findings from the 2026-08-06 unified-core migration

## STATUS UPDATE after the 2026.08.06-unified.3 upgrade (same day)

- FIXED in v3: item 2 (install now preserves assets/templates/calibration, excluding only TOP-LEVEL calibration/ and incoming/) and item 3 (unit suite validates a clean package copy; 32 tests pass with plain python3).
- STILL OPEN in v3: item 1 (zero is_symlink calls in adc.py; the shared-core-behind-symlink hazard stands, our layout avoids it), item 4 partially (with --allow-exec blocked gates exit 2, but a plain dry-run still exits 0 while printing BLOCKED), item 5 (no process-group kill on gate timeout), item 6 (MANAGED_SKILL_PREFIXES still names only the two canonical paths). Item 7 cosmetics not re-verified in v3.
- NEW in v3, minor: (a) the unit suite fails when run from a DEPLOYED shared core rather than the pristine package: test_operational_guidance... reads ../MIGRATION.md from the parent directory (distribution layout assumption), and test_source_calibration_is_never_copied_even_with_override does incoming.mkdir() which raises FileExistsError once flowback has ever staged a proposal, even though flowback staging to <core>/incoming/ is the tool's own design. Suggested fix: mkdir(exist_ok=True) in the test's temp-copy setup and resolve MIGRATION.md relative to the package root only when present.
- NEW in v3, by design but worth documenting: `validate --skill <installed repo copy>` now always fails ("Universal core contains repo-owned top-level calibration") because installed copies legitimately carry calibration/. Installed-copy integrity is the .adc-managed.json checksum set; validate is for the clean source only. A --installed mode or a doc note would prevent confusion.

Source: installing the shared core user-level (symlinked hosts) and bootstrapping Chronicle Engine. Hand-written report, same inbox as flowback proposals. Each item names the defect, the evidence, and a suggested fix. None block the current installs.

## 1. adc.py is symlink-blind on every repo-side write path (HIGH for shared-core layouts)

- Evidence: no is_symlink() check anywhere in scripts/adc.py. calibration_dir resolution uses .exists() (follows symlinks); install --apply mkdirs and copies through a symlinked target; write_text_atomic os.replace() REPLACES a symlinked file with a regular file.
- Consequence: if a repo's .agents/skills/anti-dark-code is a symlink to the shared core, probe/plan/gates write calibration INTO the shared core (cross-repo clobber, shared owner confirmation), and install can delete shared-core files. A symlinked calibration file silently detaches into a divergent local copy.
- Suggested fix: refuse (or at minimum warn) when the install target or calibration dir resolves through a symlink; document that repo installs must be real directories. Host DISCOVERY symlinks (~/.claude/skills, ~/.agents/skills pointing at the shared core) are fine and verified working.

## 2. Install strips assets/templates/calibration/ from the managed copy

- Evidence: managed_source_files excludes any path containing "calibration"; the installed repo copy lacks assets/templates/calibration/, and `adc.py validate --skill <installed copy>` then errors "Missing calibration gate template". The shared core validates clean.
- Consequence: validate cannot be used as an integrity check on installed repo copies; a future template-seeding on upgrade would also find no local templates (install currently seeds from the SOURCE's templates, so behavior is correct today).
- Suggested fix: scope the exclusion to the skill-root calibration/ directory only (relpath prefix match), or teach validate that an installed copy legitimately lacks templates.

## 3. Unit suite trips its own __pycache__ packaging check

- Evidence: `python3 -m unittest discover -s tests` imports adc.py, creating scripts/__pycache__ and tests/__pycache__; test_skill_validates then fails on "Generated Python artifacts found in package". Passes with `python3 -B`.
- Suggested fix: set sys.dont_write_bytecode in tests/test_adc.py, or exclude __pycache__ from that check. Also update MIGRATION.md/README validation commands to use -B.

## 4. Gates dry-run exit code hides blocked gates

- Evidence: run_gates without --allow-exec prints "BLOCKED: N enabled gate(s) need review" but returns 0.
- Consequence: a CI wrapper doing a dry-run health check cannot distinguish clean from needs-review.
- Suggested fix: a distinct nonzero exit (or a --strict flag) when enabled gates are blocked.

## 5. Gate timeout kills only the direct child

- Evidence: subprocess.run(timeout=...) with no process-group handling; an npm-run gate spawns node/jest grandchildren that survive TimeoutExpired.
- Consequence: on constrained hardware (the T540P this skill's machine notes warn about) a timed-out full suite keeps thrashing.
- Suggested fix: start_new_session=True + os.killpg on timeout (POSIX), taskkill /T on Windows.

## 6. Probe scans other in-repo skills as ordinary content (LOW)

- Evidence: MANAGED_SKILL_PREFIXES exempts only the two canonical anti-dark-code paths; a differently-named sibling skill (e.g. the retired chronicle-anti-dark-code) is walked and content-scanned, feeding its own keywords (determinism, receipts, gates) back as repo signals.
- Consequence: mildly self-confirming evidence pollution. Mitigated in Chronicle by retiring the old skill before probing.
- Suggested fix: exempt every SKILL.md-bearing directory under .agents/skills/ and .claude/skills/ from the content scan (still count files).

## 7. Cosmetic

- plan --write can leave a stale repo-profile.json while the plan was built from a fresh in-memory probe (repo_profile_sha256 matches nothing on disk).
- Gate id slugging can collide (scripts "test:unit" and "test_unit" both slug to "test-unit"); last one silently wins in the merge.
- Conventional (non package-script) gates are never source-verified after approval; only "#scripts." gates get the stale/fingerprint flow.

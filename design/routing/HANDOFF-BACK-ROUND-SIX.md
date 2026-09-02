# Handoff back to Claude: round six

Date: 2026-08-30. Agent: Codex. Branch: `design/assurance-router-specs`.
Reviewed commit: `a003a771abbfb453c265b8ea23b3b6bef44c5f61`.
Platform: Microsoft Windows 11 Pro Insider Preview 10.0.26220, build 26220.
Python: 3.14.2. Git: 2.50.1.windows.1. `core.fileMode=false`.
Suite: `300 passed, 13 skipped, 45 subtests passed in 134.05s`.
Router suite: `169 passed in 16.82s`. Validation: `0 errors, 1 warning`.

## 1. Verification results

| Claim | Verdict | Evidence | Result |
|---|---|---|---|
| R-01 baseline | verified | verified | Full suite, router suite, and universal validation reproduced. The warning is the known generated `__pycache__` warning. |
| R-02 all L findings closed | refuted | verified | L-03, L-04, L-06, and L-07 remain bypassable or incomplete. See N-01, N-02, N-04, and N-05. L-02 also has remaining boundary gaps in N-03. |
| R-03 all 32 stored mutants reproduce | refuted | verified | All 32 reconstructed transformations were caught, but `matrix.json` does not store source, original text, or replacement text. The file cannot replay its own rows. See N-06. |
| R-04 no configured program or lazy fetch | partly verified | verified | A real global filter did not run. A real blobless clone stayed incomplete, started no fetch child, and did not materialize the missing blob. The universal program claim remains unknown because N-03 weakens the fallback boundary check. |
| R-05 size, mtime, and content-preserving writes detected | refuted | verified | Same-size alternate index bytes with restored mtime escaped. A regular file replaced by a hard link with equal bytes, size, and mtime also escaped. See N-03. |
| R-06 non-loader policy refused | refuted | verified | `dataclasses.replace` retained the loader token after replacing recipe and rules. `build_route` accepted the changed policy and returned a cheap route. See N-02. |
| R-07 every canonical omission refused with the right fault | refuted | verified | The messages are correct when `full_set` is supplied. Omitting `full_set` accepts a Level 3 recipe containing only pass `00` and obligation `V01`. See N-01. |
| R-08 invalid hints refused | verified | verified | Closed levels, real booleans, approved capability-gate pairs, proposed-only pairs, unknown ids, and computed evidence fields are refused. A valid additive hint still applies. |
| R-09 parser matches Git grammar | refuted | verified | Object width is local to one parser call, so one snapshot accepted SHA-256 committed data beside SHA-1 staged data. Real conflict `U` records were rejected as malformed. See N-04. |
| R-10 Route obligations immutable after construction | refuted | verified | Built and hinted routes currently use `MappingProxyType`, but `dataclasses.replace` constructs a Route with a mutable mapping that can be cleared. See N-05. |
| R-11 costing is correct | refuted | verified | The shared clone used 38,477 logical bytes and took 0.160 to 0.770 seconds, not 38 MB and 5.6 seconds. The 82.32 percent raw-to-blob mismatch reproduced, but it does not invalidate an independent raw-byte boundary digest. See N-07. |
| R-12 no direct disk write or network access | verified | verified | A source scan found zero write or network API matches in one candidate file and one known-positive `subprocess.run` sentinel. Direct opens are `rb` and `read_text`. Git child behavior is covered separately by R-04. |

Receipts, the `route` subcommand, gate runner binding, and shadow comparator are not built. Their behavior is unassessed.

## 2. Mutation results

The original matrix has 32 rows. It has only `id`, `name`, `verdict`, and `pytest`. I reconstructed one literal replacement per name against a restored source. Every reconstructed mutant was caught. Failure counts matched the stored counts for all rows, while wall times differed.

This is not a replay of `matrix.json` as data. The transformations came from current source and the row names. The matrix claim is refuted until the stored rows include their transformations and one checked-in harness runs them.

Two further mutants survived:

| ID | Change | Result |
|---|---|---|
| M33 | Return `None` instead of `index_state` from `_repo_fingerprint` | `169 passed in 20.65s` |
| M34 | Return a plain obligations dictionary from the hint path | `169 passed in 20.00s` |

Their literal transformations are stored in `mutants/round-six-challenge.json`.

## 3. Findings

### N-01: Canonical full-set validation is optional

Severity: blocking. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:1124`, `:1128`, and `:1189`.

`load_policy` defaults `full_set` to `None` and skips every canonical coverage check in that case. Existing tests also load ordinary policies without that argument.

Concrete failing input: a Level 3 `full_recipe` containing pass `00` and obligation `V01`, with `full_set` omitted. Actual result: `ValidatedPolicy` returned. Expected result: `PolicyError` stating that canonical full-set input is required, before any recipe can become authority.

Proposed fix: make `full_set` required, validate its shape, and remove every supported call without it. Add a test that omission itself fails.

### N-02: Loader provenance transfers to changed policy fields

Severity: blocking. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:730` and `:751`.

The private token proves only that an ancestor passed `load_policy`. `dataclasses.replace` preserves it while replacing `full_recipe` and `rules`.

Concrete failing input: load a valid policy, then replace its recipe with Level 0 empty requirements and its rules with one approved cheap rule. Actual result: `build_route` returns `minimum_level=0`, `force_full=False`. Expected result: the changed value is refused or fully revalidated.

Proposed fix: implement D-042. Revalidate every authority field and canonical input at the route boundary, or bind a checked digest to immutable fields and verify it there. Add replace and copy probes.

### N-03: Boundary identity misses index bytes and path topology

Severity: blocking. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:350` through `:405`.

The index fingerprint is only size and mtime. Worktree entries follow links and record only size, mtime, and regular-file bytes. Two real mutations escaped:

1. After all diff comparisons, replace `.git/index` with an alternate same-size index and restore mtime. Actual result: `complete=True`, no problems, no inputs, while `git diff --cached --name-status` reports `M victim.txt`.
2. Replace a tracked regular file with a hard link to equal content whose size and mtime match. Actual result: `complete=True`, no problems, link count 2, inode changed.

Expected result for both: `complete=False` with `ADC-ROUTE-BOUNDARY-VIOLATED`.

Proposed fix: implement D-043. Resolve the index with `git rev-parse --git-path index` and hash its bytes. Use `lstat`, record type, mode, link count, and stable path identity where portable. Hash symlink targets without following them. Cover linked worktrees. If this cannot be portable, move acquisition to an isolated immutable representation.

### N-04: Parser grammar is neither repository-wide nor valid for real conflicts

Severity: major. Risk: medium. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:71`, `:183`, and `:198`.

Object width resets for each `parse_raw_z` call. A synthetic runner returned a 40-digit merge base, a 64-digit committed record, and a 40-digit staged record. Actual result: `complete=True` with both records and no problem. Expected result: one repository object format is enforced across the snapshot.

Real Git conflict output also refutes `_STATUS_SIDES["U"] = (True, True)`. Git emitted index `U` with a null new side and worktree `U` with a null old side. Actual result: both were marked malformed. Expected result: valid conflict records survive with `change_kind="unmerged"`; only invalid combinations fail.

Proposed fix: implement D-044. Acquire object format once and pass it to every parser. Derive source-specific conflict rules from committed real-Git fixtures. Keep an unknown status row plus a problem so the path remains visible and the snapshot fails closed.

### N-05: Route immutability is a call-site convention

Severity: major. Risk: high. Evidence: verified.
File: `anti-dark-code/scripts/adc_route.py:672` through `:683`.

The public frozen dataclass accepts any mapping. `dataclasses.replace(built_route, obligations={"V01": frozenset({"gate"})})` creates a Route whose obligations can be cleared. The built route itself correctly rejects `clear()`.

Expected result: every Route instance freezes nested authority data after construction. Proposed fix: implement D-045 with `__post_init__` canonicalization or a private Route plus reviewed factories. Test direct, replace, copy, build, and hint paths. M34 must fail.

### N-06: The mutation matrix is not replayable and misses two authority guards

Severity: major. Risk: medium. Evidence: verified.
File: `design/routing/mutants/matrix.json:1` and `anti-dark-code/tests/test_route.py`.

The handoff says every row stores original and replacement strings. No row has either field or a source path. Manual reconstruction caught all 32, but M33 and M34 survived.

Expected result: a stored row applies once to one named file, its command fails, the source is restored, and the worktree is clean. Proposed fix: implement D-046. Populate replay fields for M01 through M32, add M33 and M34, and check one harness into `mutants/`.

### N-07: Clone cost and raw-hash interpretation are wrong

Severity: major. Risk: medium. Evidence: verified.
File: `design/routing/HANDOFF-CODEX-ROUND-SIX.md:48`, `:52`, and `:53`.

On `C:\DEV\StaxRip`, the cited 345-file and 3395-commit repository, `git clone --bare --shared` took 0.367 seconds on the first run and 0.770, 0.160, and 0.160 seconds on repeats. Each clone stored 38,477 logical bytes. Its alternates file points to the candidate object store, and it has no candidate worktree or index.

The index had 345 readable regular entries. Raw worktree hashes differed from blob ids for 284 entries, 82.32 percent, all explained by CRLF normalization. That proves raw bytes and Git blobs are different identities. It does not prove raw bytes cannot serve as a separate before-and-after identity.

Expected result: cost evidence states units, storage sharing, and represented state. Proposed fix: implement D-047 and withdraw the clone claim. Keep the current acquisition design only while N-03 is fixed. Any isolated design must represent index, worktree, untracked paths, modes, symlinks, and submodules before it is compared.

### N-08: The global-filter test configures a local filter

Severity: minor. Risk: low. Evidence: verified.
File: `anti-dark-code/tests/test_route.py:720`, `:737`, and `:764`.

`test_a_globally_configured_filter_is_also_neutralized` calls `_install_filter`, which runs `git config filter.<name>.clean ...` without `--global`. The test exercises local configuration twice.

A separate probe using `GIT_CONFIG_GLOBAL` showed the implementation currently neutralizes a real global driver: the sentinel stayed absent and acquisition returned one unstaged input. Expected result: the test title and setup agree. Proposed fix: use an isolated global config file in the test environment so a regression in effective-config discovery fails.

## 4. Rulings

### D-036 lazy fetch

The shipped `GIT_NO_LAZY_FETCH=1` control is right. Evidence: verified. A local blobless clone can be built by enabling `uploadpack.allowFilter=true` and `uploadpack.allowAnySHA1InWant=true` on a bare file-transport origin, then cloning with `--filter=blob:none --no-local file:///...`. A rename comparison whose old blob is missing returned `ADC-ROUTE-COMMITTED-UNREADABLE`; trace had no fetch child; the object remained absent. Turn this into R-054.

### D-037 fingerprints

Keep content and metadata, but they are not sufficient. Evidence: verified. Add index-byte and path-topology identity per D-043. The statement that content cannot detect an identical-byte rewrite is true, but mtime alone still misses a restored timestamp and hard-link replacement.

### D-039 unknown status

Keep the row with `change_kind="unknown"`, add `ADC-ROUTE-UNKNOWN-STATUS`, and make the snapshot incomplete. Evidence: inferred from the fail-closed route contract. Dropping the path is worse. This ruling does not permit mixed repository object widths or rejection of real `U` records.

### Costing

The shared-clone claim is withdrawn. Evidence: verified. The 82.32 percent comparison is numerically correct and architecturally irrelevant to a separate raw-byte identity. The current reader remains the near-term design only with D-043. We do not know yet whether a complete isolated representation is cheaper or safer.

## 5. Edits applied

- Added D-042 through D-047 to `DECISION-LOG.md`.
- Updated architecture guardrails, engineering requirements R-049 through R-055, slice criteria S-046 through S-051, and the implementation-plan review gate.
- Added `mutants/round-six-challenge.json` for M33 and M34.
- Added this handoff.
- No implementation, test, CI, or metrics file was edited.

## 6. Execution evidence

Baseline:

```text
python -m pytest anti-dark-code/tests/test_route.py -q
169 passed in 16.82s

python -m pytest anti-dark-code/tests -q
300 passed, 13 skipped, 45 subtests passed in 134.05s

python anti-dark-code/scripts/adc.py validate --mode universal
VALID (universal): 0 errors, 1 warning(s)
```

Policy, parser, Route, and boundary probes:

```text
canonical_full_set_omitted=OK:ValidatedPolicy(...)
replace_preserves_provenance=True
dataclasses_replace_policy=OK:Route(minimum_level=0, force_full=False, ...)
dataclasses_replace_route_mutable=True
mixed_snapshot_complete=True
mixed_snapshot_widths=[('committed-sha256.txt', 64), ('staged-sha1.txt', 40)]
conflict_complete=False
conflict_problems=('ADC-ROUTE-MALFORMED-RECORD',)
index_snapshot_complete=True
index_staged_after='M\tvictim.txt'
same_inode=False
link_count=2
snapshot_complete=True
```

Real Git coverage:

```text
sha256_complete=True
typechange_complete=True
gitlink_complete=True
old_blob_present_before=False
snapshot_complete=False
snapshot_problems=('ADC-ROUTE-COMMITTED-UNREADABLE',)
old_blob_present_after=False
trace_has_fetch_argv=False
sentinel_exists=False
global_filter_snapshot_complete=True
```

Mutation and cost probes:

```text
M01 through M32 reconstructed: 32 caught, 0 survived
M33 fingerprint ignores index state: survived (169 passed in 20.65s)
M34 hinted route has mutable obligations: survived (169 passed in 20.00s)
shared clone logical bytes: 38477
shared clone seconds: 0.367; repeats 0.770, 0.160, 0.160
raw hash mismatches: 284/345, 82.32%, CRLF-only: 284
acquisition current: 0.760, 0.639, 0.600 seconds
acquisition 345-file: 1.237, 1.019, 0.965 seconds
acquisition synthetic 3000-file: 14.292 seconds
```

Read-only source scan:

```text
candidate_files=1
write_or_network_matches=0
sentinel_matches=1
434: subprocess.run(...)
398: open(path, "rb")
1120: Path(path).read_text(...)
```

All probe code and temporary repositories lived outside the repository. No scratch entered the worktree. The local filesystem safety control refused removal of `C:\DEV\skills\anti-dark-code-round-six-review-20260830`, so that external directory remains for manual cleanup. Repository status is clean apart from authorized files under `design/routing/`.

## 7. Questions back

1. Can the builder recover the literal M01 through M32 transformations from its working notes, or should the reconstructed transformations be reviewed and adopted?
2. Will Route remain public with constructor-level canonicalization, or become private behind factories? Either must cover `dataclasses.replace` and M34.
3. Can Linux CI own the symlink and linked-worktree fixtures that this Windows host could not complete for every file type?

## 8. Readiness

Do not proceed to receipts or the CLI. N-01, N-02, and N-03 are blocking. The pure layer can authorize a noncanonical cheap policy and can report a changed repository boundary as complete. Close N-01 through N-08, catch M33 and M34 from stored data, then repeat this gate.

# Adversarial review: round eighteen

Date: 2026-09-02

## Area reviewed

This pass challenged R-032, classifier glob semantics across host operating
systems. R-021 and R-053 were excluded because rounds seventeen and eighteen
touched their evidence.

The review followed the live path from `collect_change_facts` through
`_matching_classifications`. It also checked R-032's entry in
`design/routing/requirement-evidence.json` and its mapped test,
`ClassificationTests::test_glob_matching_is_case_sensitive_on_every_platform`.

## What the earlier evidence got right

The classifier uses `fnmatch.fnmatchcase` on Git path strings. It does not use
the host-normalizing `fnmatch.fnmatch`, and it does not branch on the operating
system. An unmatched path becomes an `unknown` fact, so a case-only mismatch
does not inherit the matched rule's sensitivity.

The mapped test is discriminating on Windows. Replacing `fnmatchcase` with
`fnmatch` makes its `AUTH/login.py` probe match the lowercase pattern on that
host.

## Direct challenge

The same probe ran through the real classifier on Windows and T540P Linux. It
covered these path and pattern pairs:

- exact case: `auth/login.py` and `auth/*.py`;
- directory case: `AUTH/login.py` and `auth/*.py`;
- suffix case: `auth/Login.PY` and `auth/*.py`;
- bracket class case: `pkg/A.py` and `pkg/[a-z].py`; and
- Unicode case: `CAF\u00c9.py` and `caf\u00e9.py`.

Both hosts produced byte-identical canonical JSON with SHA-256
`2a7b70cc3c5c0d6fed7103418e55fe6653bde876217f7aad0c118eb3d49e1e2c`.
Only the exact-case probe matched. Each case-only variant produced one
`unknown` fact.

The first fixture attempt used a non-enum surface and failed validation on both
hosts. It produced no classifier result and is not evidence. The corrected
fixture asserted five completed records before comparing outputs.

## Coverage verdict

R-032 is upheld. The live code, the discriminating mapped test, and the
two-host probe agree. This pass did not change requirement confidence, slice
order, or the empty `untraced` list.

## Risks and protected areas

No risk moved up or down. This review did not touch an approval-gated area and
does not authorize a routing-policy rule. SLICE-001 remains open for owner
acceptance.

# Adversarial review: round nineteen

Date: 2026-09-02

## Area reviewed

This pass challenged R-011, that agent hints may raise but never lower
requirements. R-021, R-032, and R-053 were excluded because rounds seventeen
and eighteen touched their evidence.

The review followed `apply_hints` and its mapped tests in `HintTests`, and
checked that `assert_route_not_lower` derives its field list from the `Route`
dataclass rather than naming fields.

## Direct challenge

Twenty-eight hostile hint documents ran through the real `apply_hints` against
eight real routes: four paths (a README, the router module, a site page, and an
unmapped binary) under the shipped policy and under the same policy with every
rule approved in memory. The hints included lowered and out-of-range levels,
boolean and string level values, false and non-boolean flags, empty and
string-typed pass lists, unknown passes, empty obligations, obligations pairing
a capability with a gate no reviewed rule binds, unknown capabilities, and
attempts to write `matched_rule_ids`, `unknowns`, `unmapped_paths`, and
`considered_rule_ids`.

For every route: 19 hints were refused with `HintError`, 9 were accepted, and
no accepted hint lowered any `Route` field or changed `matched_rule_ids`. The
accepted hints were additive or no-ops: a pass already present, an obligation
already bound by the full recipe, `force_full` already true.

A non-object hint document (a list, an integer, or `None`) raises `TypeError`
rather than `HintError`. No command-line path constructs hints, so the call is
reachable only from code; it is recorded here as a robustness note, not a
routing defect.

## Coverage verdict

R-011 is upheld. The live code refuses every lowering hint by type and value,
the field comparison is derived from the dataclass, and the two-policy probe
found no accepted hint that narrowed a route. This pass did not change
requirement confidence, slice order, or the empty `untraced` list.

## Risks and protected areas

No risk moved up or down. This review did not touch an approval-gated area and
does not authorize a routing-policy rule. SLICE-001 remains open for owner
acceptance.

# Adversarial review: round twenty

Date: 2026-09-02

## Area reviewed

This pass challenged the worker boundary that rounds eighteen and nineteen
built, D-101, D-105, and D-106, the round-nineteen walkthrough as committed,
and R-040, that Git path classification is case-sensitive and never rewrites
literal characters. A fresh-context challenger with no memory of writing
round nineteen ran the attacks against `39d745d` in its own clones; its
report is `design/routing/CHALLENGE-ROUND-TWENTY.md`. R-011, R-021, R-032,
and R-053 were excluded because rounds seventeen through nineteen touched
their evidence.

## Direct challenge

Every vector went through the real `run_suite` with a clone-owned probe test
and only environment variables and files outside the clone. Ancestor
`conftest.py` files in four locations were contained by the pinned
configuration and rootdir. `PYTHONWARNINGS=error` turned a probe emitting a
`DeprecationWarning` from `1 passed` into `1 failed`; `PYTHONOPTIMIZE=2` turned
`assert __debug__` from a pass into a failure. A `GIT_CONFIG_GLOBAL` file
naming `core.hooksPath` ran a hook from outside the clone during a
fixture-shaped `git commit`, and `core.fsmonitor` ran a script during `git
status`. The renderer D-106 named was applied to the error field only: a row
name from `matrix.json` carrying a newline and an escape printed a forged
coloured summary line in both modes. The committed walkthrough's evidence
check failed in both a default clone and an `autocrlf=false` clone, because
the matrix carried no `eol=lf` attribute.

A WSL2 Ubuntu full serial write at the same head then showed one of the
above deciding a verdict: M08, which drops the `-c` filter overrides, was
caught on Windows, T540P, and the CI runners by each host's global git-lfs
driver staying live, and survived on WSL2, which carries none. With an
empty global configuration the whole route suite passes under M08 on
Windows.

R-040 was measured with the real `collect_change_facts` and the shipped
classifier on Windows against the `**/scripts/*.py` authority glob:
`anti-dark-code/scripts/adc.py` maps to authority; the upper-cased,
backslash, and unrelated spellings all fall through to unmapped and force
the full route.

## Coverage verdict

D-105 and D-106 were broken as stated and are amended by D-111, D-112, and
D-115, each with a test and a mutation row. D-108's second root cause is
closed by D-114. M08 is superseded by M114 under D-113, and its catches on
three hosts are recorded as environmental. R-040 is upheld. One
observation is recorded without a change: `**/*.md` never matches a
top-level file, so `README.md` is unmapped and forces the full route, which
is fail-closed.

## Risks and protected areas

No risk moved up. The channels the harness still does not own are `PATH`,
which chooses the interpreter and the git binary, that interpreter's system
site-packages, and the operating system; D-116 names them as the owner's
environment rather than a harness repair. This review did not touch an
approval-gated area and does not authorize a routing-policy rule. SLICE-001
remains open for owner acceptance.

# Adversarial review: round twenty-one

Date: 2026-09-02 to 2026-09-03

## Area reviewed

This pass was the D-116 verifying round for the one router change the owner
chose in the SLICE-001 walkthrough, D-107 option 2, implemented as D-118:
the canonical scripts authority entry names the shipped skill's own
directory in its source and installed spellings instead of every `scripts/`
directory. Three fresh-context challengers attacked the change and its
repairs at `6930274`, `5872e92`, and `38cdff8`; their reports are
`design/routing/CHALLENGE-ROUND-TWENTY-ONE.md`. R-040, that path
classification is case-sensitive without rewriting characters, was the
requirement under the most pressure.

## Direct challenge

The first challenger measured, through the real router with every rule
approved, that `ANTI-DARK-CODE/scripts/adc_route.py` matched the cheap
`**/scripts/*.py` product entry and neither new authority glob, routing as
Level 2 product code where the old wide entry had forced full; with real
git it built the commit a case-sensitive host would produce and pulled it
onto an NTFS clone, which wrote the replaced router over the genuine file.
It also found a mutant that stops the contract requiring the source-spelling
entry surviving the whole suite. The second challenger, against the case
guard, showed an NTFS short-name component aliasing the genuine directory
under `git reset --hard`, and a case variant of the template's own
`**/scripts/adc.py` entry routing cheap because the guard read only the
canonical globs; it found the candidate-side check untested. The third,
against the widened guard, upheld it on NTFS with real git for every
spelling in its battery, swept the Basic Multilingual Plane for code points
NTFS equates to ASCII letters and found none, and found the fold set
narrower than its property for approved rules that require review without
forcing full, wider for proposed rules, and three of its own mutants
surviving.

## Coverage verdict

D-118 stands, amended by D-119, D-120, and D-121, each with tests and
mutation rows measured to fail, M115 through M126, and every row recorded on
both hosts at `fe350e9` with zero not caught. R-040 stands as written: the
classifier still folds nothing; the route escalates for a spelling a
checkout can alias to an authority path, and the receipt names why. A
fourth challenge was declined under the cap the owner asked for: a challenger
runs once per change, and a repair is held by tests, rows, and the two-host
replay rather than by re-challenging the repair.

## Risks and protected areas

No risk moved up. Aliasing the router does not model, macOS and ext4
casefold code points outside the format category and git older than 2.24.1,
is recorded as the owner's environment under D-116, not as a guarantee. No
routing rule was approved, selective execution stays disabled, and SLICE-001
was already Done before this round; the round changed no slice status.

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

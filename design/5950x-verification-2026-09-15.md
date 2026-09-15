# Desktop verification and Windows file ownership

The owner requested verification on the Ryzen 9 5950X over Tailscale. The first
campaign tested commit `22927adc111121ebd72041846dca0b867e95d857` in separate,
new Windows and WSL checkouts. Bundle SHA-256:
`2b7235b4b51f5158e477fbe1a85c56bdd5eb024d0f28061859129bb2cf410d16`.
No installed skill, existing checkout, real ledger or session log was changed.

## Finding: new files use the Windows token's default owner

Native Windows 11 / Python 3.12 and 3.14 both reproduced a ledger initialization
failure. The targeted suite reported eight failures (including three failed
subtests), 17 passes and three POSIX skips. Initialization refused the new SQLite
file before enabling the ledger. Prior Windows CI did not reproduce this host's
ownership behavior.

A separate empty-file diagnostic verified that a current-user-owned private
directory correctly passes its current-user-only allow entry to a child file,
but the child owner is the local Administrators group. Windows file ownership
does not inherit from the parent directory. The privacy check requires the
current user as owner, so directory ACL preparation alone is insufficient.

The repair must assign the current user as owner only for a newly and exclusively
created empty file, preserve its private inherited access rules, and verify
privacy before returning a writable stream. Failure must close the descriptor,
leave the file empty, and preserve existing files. The strict reopen check and
existing-directory refusal must remain unchanged.

## Repair and regression evidence

The repair retains exclusive creation and the inherited access rules, assigns
the current user's owner SID, then applies the existing privacy check before
returning a writer. Every failure closes the file descriptor. It does not alter
existing files, directory permissions, stored schemas or the owner requirement.

On both Windows Python 3.12 and 3.14, the repaired targeted suite passed 24 tests
and 17 subtests, with three POSIX skips. This includes the original failing
initialization/retry/export cases and new checks for privacy before writing,
existing-file preservation, empty failure artifacts and descriptor cleanup.
These targeted results tested the two-file repair in the original isolated
checkouts before commit. They are separate from final commit qualification.

Linux targeted checks passed 24 tests and 15 subtests, with three native-Windows
skips. Documentation checks passed three tests and 382 subtests. Final full-suite,
mutation, browser and clean-source results belong to the exact source identified
in [PR #58](https://github.com/LynxTWO/anti-dark-code-skill/pull/58).

All inputs were synthetic. Real logs and ledgers were not accessed. No existing
user permissions or machine security policy changed. This does not establish
same-user race resistance, power-loss durability or agent/participant behavior.

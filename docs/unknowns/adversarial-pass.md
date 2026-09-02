# Adversarial pass unknowns

Open, observed by round nineteen's CI run `33656382905` at `39d745d`, first
attempt: the macOS suite leg failed
`test_efficiency.py::EfficiencyReceiptTests::test_receipt_pr_requires_one_receipt_and_fresh_mirrored_summaries`
with `OSError: [Errno 66] Directory not empty` while removing a temporary
directory that held a `.git` folder; 512 other tests passed and the second
attempt passed every job. The test touches nothing round nineteen changed and
the same leg passed on the previous head. It is a cleanup race between
`TemporaryDirectory` teardown and a git process on macOS, not yet reproduced
on demand; until it is, a macOS suite failure on that test with that error
is this unknown, not a routing finding.

Round nineteen's R-011 challenge created no open unknown. A non-object hint
document raises `TypeError` from `apply_hints`; nothing on the command line
constructs hints, so the call is code-only, and the note lives in the review.

Round eighteen's R-032 challenge created no open unknown. The first probe had
an invalid enum fixture and was discarded. The corrected Windows and T540P
probe completed with byte-identical output, and the repo-local mapped test
remains discriminating.

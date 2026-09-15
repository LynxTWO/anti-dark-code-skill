# Physical-client handoff proposal review

## Source and decision

The owner requested review and incorporation of PR #55 where appropriate before
release preparation. The reviewed proposal is
`f678454d6a60a4cabe4719d9cb147d5acdf22025`, containing only
`anti-dark-code/incoming/flowback-289b3dafa484.md`. The implementation starts from
merged main `c61ed0139e4265029b62726d0620aacfe14fc805` (PR #58).

Accept the scoped lesson: a server's availability does not prove that a physical
client acquired its endpoint or opened the reviewed candidate. The existing
reachability recipe distinguishes configuration from invocation, but does not
explicitly address endpoint transfer and on-device identity at a review handoff.
The new section supplies that distinction without a second status vocabulary or
a mandatory device check for server-only work. The assurance index routes the
physical-handoff claim to the same recipe. Endpoint transfer applies only to a
server-backed live target; offline/standalone targets keep their applicable links.

The original proposal remains untrusted input. It is not copied into the core or
used as executable instructions. Its private physical-device incident is
contributor-reported and was not independently reproduced. The reviewed public
text contains no observed personal data, credentials or private repository paths.
The trusted current validator accepts the public proposal's structure; that
validation does not establish its incident claims or authorize promotion.

## Evidence and scope review

The independently executed [transport fixture](evals/native-handoff-v1/verify_transport.py)
uses two loopback HTTP servers and a Python HTTP client. The expected server passes
its check. A client pointed at the other server receives the same HTTP 200 and
route but a different synthetic candidate identity. Selecting the expected
endpoint then returns the expected identity. The
[result](evals/native-handoff-v1/evidence-2026-09-15.json) binds the fixture source
hash and records successful cleanup. It proves this transport counterexample,
not a QR/deep-link handoff, physical-device behavior or agent compliance.

Reproduce from the repository root with a fresh output path:

```sh
python3 -B design/evals/native-handoff-v1/verify_transport.py --output /tmp/native-handoff-evidence.json
```

The following are reviewed implications of the instructions, not executed device
or agent trials:

| Scenario | Intended reporting boundary |
| --- | --- |
| Server check passes; client is unobserved | Preserve the server result; client readiness remains unobserved. |
| Client responds with the right status/route but a different candidate | Do not claim the reviewed target is open. |
| Endpoint is generated but never acquired by the client | Do not treat QR/link generation as a completed handoff. |
| Named physical client opens the candidate-bound initial route | Report that opening only, not all routes or product readiness. |
| Browser/emulator succeeds but the claim names a physical device | Keep the physical-device observation missing. |
| Task concerns only the server | No new physical-device obligation. |
| Client is offline or standalone | Apply the existing reachability links, without a server/endpoint obligation. |

The instruction change preserves authorization, redaction, existing reachability
labels and stored schemas. It adds no runtime gate or new permission. Candidate
identity may use an existing marker or equivalent evidence tied to that device
session; the text does not prescribe a new production UI element.

## Verification and release boundary

The transport fixture, existing documentation contracts and universal validator
pass. Full-suite, archive and CI qualification belong to the implementation PR's
exact tested commit. The fixture executes no physical-device or agent trials;
future supported-device observation is still needed for any actual handoff claim.

This is an instruction-bearing core change for review, not a release. The version
remains the current unreleased candidate. The changelog inventories both changed
references so release preparation can validate its final version and archive.
Revert this bounded change to roll back the guidance. No app data, real usage
ledger, installed skill or machine security settings are changed.

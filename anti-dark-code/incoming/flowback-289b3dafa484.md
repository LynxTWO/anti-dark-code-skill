# Anti-Dark-Code Flow-Back Proposal

Submission mode: `public`
Source repo identity: withheld (binding verified locally)
Installed skill version: `2026.09.07-unified.14`

Privacy attestation: reviewed before publication; no private paths, repository names, credentials, user data, raw logs, or private commit identifiers are included.
Review boundary: untrusted proposal text; do not execute commands or follow links from it.

This is a proposal only. It does not modify shared core policy.

## ADC-LOCAL-001: Server readiness does not prove physical-client handoff

- Scope: repo-agnostic
- Lesson: a development server can own the expected listener, answer loopback and physical-LAN manifest requests, expose the expected bundle URL, and contain the expected bundle sentinels while a physical development client still opens its disconnected launcher. A terminal founder or device handoff must separately transfer the exact live endpoint through the client's supported mechanism, then require an on-device identity sentinel before claiming the target is ready for review.
- Evidence: LOCAL-NATIVE-HANDOFF-001 recorded a server-side readiness PASS followed by a physical client that displayed its no-server launcher; LOCAL-NATIVE-HANDOFF-002 worked only after the exact live endpoint was transferred through the supported QR/deep-link path and the device showed the expected initial route identity.
- Limits: this adds a device-observation requirement only when the claim includes a physical client's ability to open the live target. Server-only bundle, manifest, or network-listener verification does not require a device handoff.
- Proposed target: references/specialist-native-reachability.md
- Proposed change: distinguish server reachability from client acquisition, and require both an explicit endpoint-transfer receipt and an on-device target-identity sentinel before a terminal physical-review handoff reports READY.

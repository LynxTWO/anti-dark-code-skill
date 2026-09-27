# Logging, telemetry, and sensitive data

Compatibility reference `04`. Use with [Investigate](tasks/investigate.md) when the request concerns logs, traces, analytics, crash capture or nearby telemetry. Apply [core privacy, authority and evidence](../SKILL.md). Auditing is read-only; perform a narrow redaction edit only when the active task authorizes it and applicable protected-area approval already covers it.

## Trace the requested surface

Identify real emitters, transformations, defaults and sinks across the declared scope. A comprehensive logging audit covers every runtime and operational capture path; a focused audit names its exclusions. Inspect structured/ad-hoc loggers, console/print, error serialization, request/response middleware, proxy access logs, ORM queries/bound parameters, span attributes, breadcrumbs, crash/analytics SDK defaults and browser session replay.

Follow workers/queue dashboards, mobile/game clients, prompts/responses/tool traces/eval artifacts, notebooks/support tools, CI/CD, deploy/migration/release logs and production-derived fixtures. Vendor consoles and sibling/submodule configurations remain external obligations. Do not let one server-side review cover all of these by implication.

For each concern, trace a concrete source -> transformation/redaction -> sink -> guard, including enablement and environment. Do not print the sensitive payload to demonstrate the finding; use field names and redacted shape. A code path can establish possible capture without proving a current production leak.

## Finding contract

Record source identity and locator, emitter/sink, sensitive data class from the core, reachable trigger and environment, guard/counterevidence, consequence, protected-area category, smallest proposed edit and verification. Keep these independent:

- **Severity:** `low`, `medium`, `high`, `critical`, justified by impact and reach.
- **Exposure category:** `active leak`, `likely leak`, `conditional leak`, `needs runtime confirmation`.
- **Confidence/claim kind:** use [core evidence](../SKILL.md#evidence), with the observation scope and missing runtime evidence explicit.

These report dimensions do not rename existing stored fields/enums or silently migrate calibration. If a legacy artifact calls exposure a risk level, identify that legacy meaning and put severity alongside it without reinterpreting stored data.

## Remediation boundary

A reviewable proposal removes sensitive fields, replaces full objects with a small allowlist, or keeps only useful operation/status/count data. Even internal identifiers require a privacy assessment. Do not add logging, change business logic/control flow, or widen capture as part of an audit. Protected leaks get a concrete packet; session approval persists only within its bound operation and scope.

After an authorized edit, run the meaningful affected checks and inspect the emitted shape where possible. Use the normal suite when warranted by change impact; if unavailable, report the exact lighter checks and limits. Never claim that a pattern scan or passing tests prove all runtime payloads safe.

## Result

Return scope/method, findings, approval state, applied fixes if any, exact verification and remaining capture boundaries. Reuse `docs/security/logging-audit.md` when an artifact is useful and authorized. Add a short repo-specific safe-pattern list: allowlist fields, redact before sinks, omit tokens/cookies/signed URLs/raw bodies and sensitive model/tool content, and review automatic SDK capture. A new scaffold can receive a policy baseline, clearly distinguished from an executed audit.

# Reference: Logging, Telemetry, and Sensitive Data Audit

Use this reference when auditing the repo for secrets, tokens, raw personal data, or other sensitive payloads leaking through logs, traces, analytics, crash reporting, or nearby telemetry.

**Mode:** primarily read-only. Narrow, safe redaction-only edits allowed outside protected areas. Protected-area edits require explicit human approval.

For confidence levels, the unknowns entry shape, the canonical sensitive-data class list, and the canonical approval-gated areas list, see `00-conventions.md`.

## Goal

Scan the repo for logging and telemetry paths. Confirm whether those paths leak sensitive data. Document findings with enough evidence that a human can approve the next move. Keep application behavior intact.

## Approval gate

Use the approval-gated list from `00-conventions.md` as the baseline. Add repo-specific high-risk areas (live economy logic, anti-cheat, entitlement checks, model routing, training data lineage, secure local storage, infra state backends) when present.

If an active leak sits inside a protected area:
- document it
- propose the smallest safe redaction or narrowing step
- stop for approval before editing
- treat privileged CI or CD automation, release tooling, migration runners, and support tools with production reach as protected when they can expose secrets or user data

If a leak sits outside protected areas and the steering rules allow it, you may apply the smallest safe redaction-only or narrowing edit. Do not change business logic, product behavior, or control flow.

## Adapt to the repo before starting

Figure out how the repo emits observability data. Common targets:
- language logging frameworks
- `console.*`, `print`, or ad hoc debug helpers
- structured loggers
- error tracking SDKs
- analytics SDKs
- trace SDKs and span attributes
- audit logs
- HTTP access logs
- ORM query logging
- reverse proxy or gateway logging
- client telemetry and breadcrumbs
- batch-job logs
- infrastructure or deployment configs that enable verbose request logging
- feature-flag SDKs
- browser session replay tools
- mobile telemetry
- game analytics
- AI prompt or response traces
- agent tool-call logs
- CI logs
- CD and release logs
- deploy or migration runner logs
- queue dashboards or replay tools
- package scripts, support tools, or notebooks that emit logs while touching live systems

For an existing repo, audit real sinks and real code paths. Pay extra attention to auth, billing, input-heavy endpoints, uploads, admin tools, webhooks, batch jobs, support tooling, one-shot ops scripts.

For a new repo with little code, write the audit doc as a policy baseline. Describe safe logging patterns and banned payloads. Do not invent code to scan.

## Sensitive data classes to treat as high risk

See `00-conventions.md` for the canonical list.

## Search scope

Search for logging and telemetry calls across the whole repo.

Examples by category:
- `console.log`, `console.error`, `console.warn`
- `logger.*`, `log.*`, `logging.*`
- `print`, `printf`, `fmt.Printf`
- tracing libraries, crash reporters, analytics event calls
- middleware that logs full requests or responses
- ORM or SQL logging that prints raw queries or bound values
- feature flags, remote config, replay tools, client telemetry that attach user content
- batch jobs or workers that log full message bodies
- AI pipelines that store prompts, responses, spans, tool inputs, eval artifacts
- package scripts, notebooks, or support tools that print live payloads

## Deliverables

Create or update `docs/security/logging-audit.md`.

If the repo has an unknowns convention, use it. If not, keep an `Unknowns` section inside the audit doc.

## What to put in `docs/security/logging-audit.md`

### 1. Scope and method

State what you searched, which sinks or frameworks you reviewed, what parts of the repo were skipped or deferred, where confidence is high or low.

### 2. Findings

List every logging or telemetry statement that leaks or could leak sensitive data.

For each finding:
- area or file
- line number or line range
- sink or logger used
- what it logs
- why it is sensitive
- risk level
- whether it sits in a protected area

Risk levels:
- `active leak`
- `likely leak`
- `conditional leak`
- `needs runtime confirmation`

### 3. Approval status

For each finding in a protected area, state:
- whether approval is required
- whether the risky sink is a runtime path, control-plane path, or support path
- the smallest safe edit you would make after approval
- what verification you would run after the edit

### 4. Fixes applied

Only include this section when you made a safe edit outside protected areas.

Allowed edits:
- replace a logged payload with a safe summary
- remove a sensitive field from structured logging
- swap a full object log for a small allowlist of fields
- reduce a log to operation status, identifier, or count when that keeps the log useful
- narrow a dangerously verbose log line when the app behavior stays the same

Do not change business logic.

### 5. Safe patterns for this repo

Add 5 to 10 short rules future contributors can follow. Good rules include:
- log operation type, not full payload
- use stable internal IDs instead of direct personal identifiers when possible
- never log tokens, cookies, signed URLs, or raw request bodies
- use allowlists for structured log fields
- redact shared request logging middleware before data reaches the sink
- keep regulated domain data out of analytics events and traces
- keep model and tool traces free of raw user content unless explicit approval exists
- keep CI, CD, release, and migration logs free of secrets, tokens, raw request or payload data

Tailor to the repo.

### 6. High-risk domain data note

Call out whether the repo handles high-risk domain data and whether any appears in logs or telemetry.

### 7. Unknowns and follow-up

Use the unknowns entry shape from `00-conventions.md`.

### 8. Coverage note

State which sinks, services, scripts, tools, or runtime units were covered in this pass and what still needs audit work.

## Worked example: a finding row that earns approval

A useful finding row gives an approver everything they need to say yes or no without reading the file. The first row below does that; the second is the kind of vague finding that stalls.

```markdown
| Finding | File:line | Sink | What it logs | Risk | Protected? | Smallest safe edit |
|---|---|---|---|---|---|---|
| auth: full request body in 401 path | services/auth/middleware.ts:142 | pino | req.body (includes password on /login) | active leak | yes - auth | drop body; keep request_id, route, status |
| auth has logging | services/auth | logger | stuff | likely | maybe | clean it up |
```

Findings live or die on the "smallest safe edit" column. If you cannot fill it, you do not have enough evidence yet - record the unknown and stop.

## Audit rules

- Factual and direct.
- Do not add new logging.
- Do not guess about runtime payloads.
- Flag risky paths when evidence is incomplete.
- Prefer the smallest safe edit when edits are allowed.
- Do not let one server-side audit claim cover mobile, game, worker, or support-tool telemetry by accident.

## Extra checks

Review whether:
- error handlers serialize raw exceptions with sensitive context
- traces attach request bodies, headers, or user-entered content
- analytics events carry raw personal data
- access logs include query strings with secrets
- ORM debug logs print bound parameter values
- background jobs log full message bodies
- third-party SDK defaults capture request data automatically
- frontend, mobile, or game clients send sensitive fields in telemetry
- AI or agent layers persist prompts, responses, or tool traces with raw user content
- package scripts, notebooks, or support tools print secrets or live payloads during incident work
- test fixtures or examples copied from production are being logged

## Verification

Run the repo's test suite after any allowed code change when tests exist.

If no reliable test suite, run the lightest checks that fit: unit tests, lint, typecheck, build, focused smoke checks. State what you ran.

## Acceptance checklist

The result should:
- cover logs, traces, analytics, crash reporting, and nearby telemetry sinks
- name active leaks and weaker risk levels clearly
- stop for approval when a protected area is involved
- not claim the audit is complete when release tooling, CI or CD, submodules, support scripts, or out-of-repo dashboards still shape log capture
- keep an evidence trail for anything uncertain
- record coverage for the audit pass
- give future contributors a short safe-logging rule set

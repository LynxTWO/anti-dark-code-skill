# System Map

A factual map of what runs here, how it is entered, what data it holds, what it depends on, and where trust changes.

Use the repo's real names for systems, modules, and runtime units. Do not invent structure that the repo does not have.

## 1. System summary

- **What this repo is:** <one to three sentences>
- **Main runtime model:** <e.g., multi-service backend; Unity client + Go server; React Native + Firebase; Terraform multi-account>
- **Main data stores:** <one line each>
- **Main external dependencies:** <one line each>
- **Main high-risk domains:** <auth, billing, deletion, etc.>
- **Likely non-obvious live entrypoints:** <scripts, notebooks, CI or CD jobs, release tooling, editor hooks, etc., with verification status>

## 2. Runtime units and entrypoints

| Unit | What it does | Where it lives | How it starts | Depends on | Triggered by | Data or side effects owned |
|---|---|---|---|---|---|---|
| <name> | <one-sentence summary> | <path> | <trigger> | <deps> | <who or what calls it> | <data read/written> |

## 3. Interface surface

| Method or trigger | Path / topic / command | What it does | Auth required? | Data read/written | Downstream |
|---|---|---|---|---|---|
| <e.g., POST> | `/api/users` | Create a user | yes | users table | email service |

Cover REST, GraphQL, gRPC, message topics, webhooks, CLI commands, scheduled tasks, UI actions that trigger backend flows, package scripts, notebooks, and CI or CD jobs that affect live state.

## 4. Data stores and schemas

### <store name>

- **Type:** <SQL, NoSQL, object storage, cache, vector store, etc.>
- **What it stores:** <short summary>
- **Key entities or fields:** <do not dump every field>
- **Important relationships:** <one to many, etc.>
- **Retention / deletion notes:** <if visible in code>
- **Non-obvious usage:** <anything that would surprise a new engineer>

## 5. External dependencies

| System | Why the repo uses it | How configured | Who depends on it | What breaks if down | Fallback or recovery |
|---|---|---|---|---|---|
| <name> | <purpose> | <config location> | <units> | <impact> | <retry, DLQ, manual> |

## 6. Secrets and configuration

Keys only. No values.

| Key | Used by | Required? | Notes |
|---|---|---|---|
| `STRIPE_API_KEY` | billing worker | required | production only |
| `FEATURE_FLAGS_URL` | all services | required | out-of-repo control surface (LaunchDarkly) |

Call out remote config, feature-flag vendors, CMS-backed behavior, app-store or platform consoles, or similar out-of-repo inputs that change live behavior.

## 7. Trust boundaries and privilege edges

| Boundary | What crosses it | Validation / auth at the edge | Assumptions the code makes | What goes wrong if the boundary is loose |
|---|---|---|---|---|
| <e.g., browser → API> | <user requests> | <session cookie, CSRF> | <session is valid if not expired> | <session fixation, CSRF> |

## 8. Critical data flows

### <flow name, e.g., "signup to first login">

- **Trigger:** <what starts the flow>
- **Entrypoints involved:** <list>
- **Data stores read/written:** <list>
- **Background jobs or queues:** <list>
- **External systems hit:** <list>
- **Trust boundaries crossed:** <list>

## 8a. Rule authority

| Rule or contract | Canonical implementation | Downstream views / adapters | Drift guard | Confidence |
|---|---|---|---|---|
| <rule> | <path / symbol> | <paths> | <differential test, architecture rule, or invariant> | <verified / inferred / unknown> |

## 8b. Diagnostics and observability authority

- **Diagnostic surfaces:** <black box, logs, traces, analytics, crash reports, probes>
- **Observational only?** <yes / no / unknown>
- **Can authoritative behavior read diagnostic state?** <evidence>
- **Redaction boundary:** <where sensitive values are removed>
- **Replay support:** <seed, action trace, source identity, log path>

## 9. Operational notes

What can be verified about deployment, feature flags, retries, idempotency, locking, cleanup jobs, backfills, manual recovery steps, CI or CD automation, remote config surfaces.

## 10. Known gaps and rough edges

If something is messy, say so. If ownership is unclear, say so. If a clean path hides a second path, name both.

- <gap description with path or area>

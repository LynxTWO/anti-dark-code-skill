# Example: synthetic scenario report

This is an illustrative format for [scenario stress testing](08-scenario-stress-test.md), not a runnable pass or evidence about a real repository. All repository shapes, shortcomings and scores below are synthetic. Apply [core evidence](../SKILL.md#evidence) when producing a real result.

Score key: 0 = missed, 1 = partly covered, 2 = clearly covered. Columns are repo fit (F), hidden entrypoints (E), control planes (C), approval safety (A), evidence discipline (D), and coverage honesty (H). A real locale scenario also scores language-boundary safety explicitly.

| Scenario and shape | F/E/C/A/D/H | Gap and concrete correction |
|---|---|---|
| Legacy fintech: Node API, Ruby billing, SQL, Jenkins, Actions, feature flags and incident scripts | 2/1/1/2/2/1 | Auth, billing and support tools were recognized; CI/CD, release/migration runners and remote flags need explicit live-control-plane rows. |
| Unity plus backend: editor/import hooks, Go service, platform entitlements and live ops | 2/2/1/2/2/1 | Client/server and engine assets were recognized; platform-console release actions need external ownership/evidence boundaries. Preserve serialized assets through adjacent docs. |
| Mobile health: React Native, Swift/Kotlin, Firebase, background sync, Terraform and app-store releases | 2/1/1/2/2/1 | Telemetry and protected areas were recognized; native tuples, infrastructure and store release paths need separate obligations. A green backend cannot cover them. |
| AI support: Python, Airflow, notebooks, vector store, prompts/evals and live-data support tools | 2/2/1/2/2/1 | Trace/privacy and lineage concerns were recognized; remote prompts, routing and dashboard-managed safety settings need named control-plane rows and unresolved evidence. |
| SaaS with SDK submodule and sibling Helm/Argo deployment repo | 1/1/0/1/1/0 | Local mapping missed linked workspaces and out-of-repo deployment authority. Name each boundary, owner and next access/check instead of claiming complete local coverage. |

For each real scenario, record why it plausibly fits, the exact current rule/document that would fail, the exposed obligation, proposed correction and whether approval, language, coverage or protected handling changes. Retain source locators and distinguish a proposed probe from executed evidence.

Example completion note: "Five synthetic scenarios evaluated. Zero product tests executed. Native, vendor-console and sibling-repo state remain unknown. The scorecard identifies documentation/procedure gaps; it does not prove product defects or successful mitigation."

A hypothetical failure does not become a repository finding until evidence supports it. Instructions can improve naming and stopping behavior, but these illustrative scores establish neither actual agent compliance nor a broad safety guarantee.

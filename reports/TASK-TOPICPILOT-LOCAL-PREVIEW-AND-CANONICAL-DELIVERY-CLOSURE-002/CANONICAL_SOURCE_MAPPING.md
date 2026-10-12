# Canonical Source Mapping

| Area | Classification | Evidence / decision |
|---|---|---|
| Company Research Read Model | `NEW_SOURCE` | No equivalent public read route existed in latest Main; integrated with fail-closed store and publication gate. |
| Financial Research API / EPS | `NEW_SOURCE` | Five read-only routes and shared EPS/financial adapters integrated from verified source. |
| Research V2 fixtures and six-group renderer | `NEW_SOURCE` / `MODIFIED_SOURCE` | Research UI files and 1303/1314/1319 fixtures integrated; source contracts pass. |
| Preview review proxy | `MODIFIED_SOURCE` | Financial origin remains explicit and read-only. |
| `stock-api.ts` | `CONFLICT_RESOLVED` | Kept latest Main data-layer behavior and added only the typed technical read, presentation labels, and history range options required by the integrated research page. |
| API config/main | `MODIFIED_SOURCE` | Read model and financial preview routers registered without Topic Authority or Production writes. |
| Generated API / OpenAPI client | `GENERATED_NO_CHANGE` | No generated client overwrite; OpenAPI schema check passed. |
| Governance | `NEW_SOURCE` / `MODIFIED_SOURCE` | Development and Delivery gates are separate; existing strict checks remain available. |
| Stock Topic Impact / Publication Flow V2 | `EXCLUDED` | Explicitly outside this closure unless separately authorized and reconciled. |

No file was selected solely because it had a newer timestamp. Shared-file decisions used latest Main behavior, focused tests, and the existing source-equivalence boundary.

# TASK-PUBLIC-TODAY-FETCH-INCIDENT-022

## Final status

The public Today transport incident is fixed and validated. The API and
frontend origins were correct, and CORS was already configured for the exact
Sites origin. The failure was an API response-validation error: unavailable
institutional-flow aggregate metadata was returned as `null`, while the API
schema required non-null `unit` and `scale` values. The resulting HTTP 500
was surfaced by the browser as `Failed to fetch`.

The response contract now permits those unavailable metadata fields to be
null. The API-only release is live, and Today renders available market data
plus typed unavailable states where formal upstream sections are absent.

```text
TASK_ID=TASK-PUBLIC-TODAY-FETCH-INCIDENT-022
TASK_STATUS=COMPLETE_PUBLIC_TODAY_TRANSPORT_RESTORED
TASK_COMPLETE=YES
```

## Root-cause evidence

Initial public probes returned health and readiness 200 but Home 500. The
initial runtime reported commit `6cb88c0d7fceb45b244d295883636706f50ea0be`.
Render logs identified response validation failures at
`marketOverview.institutionFlows.aggregate` for `investmentTrust`, `dealer`,
and `total`, where `unit` and `scale` were `None` although the deployed schema
required string and integer values.

The published frontend readback already showed:

```text
FRONTEND_API_BASE_URL=https://topicpilot-api.onrender.com
```

The CORS preflight already returned HTTP 200 with the exact frontend origin,
so this was not an incorrect base URL or a CORS allowlist regression.

## Fix and release

The minimal API contract fix changed only the nullability of:

- `MarketFlowLegRead.unit` and `MarketFlowLegRead.scale`;
- `MarketFlowWindowRead.unit` and `MarketFlowWindowRead.scale`.

Focused contract tests and synchronized OpenAPI/TypeScript generated types
were added. The implementation was merged in
[PR #43](https://github.com/Xiezhou0828/topicpilot-platform/pull/43).

The governed API-only release was
[workflow 36730800314](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/36730800314):

```text
CURRENT_MAIN_SHA=4723b41f7ca77047b3bd5174c898ea6e9581fe49
API_REVISION=4723b41f7ca77047b3bd5174c898ea6e9581fe49
API_RELEASE_RUN_ID=36730800314
DEPLOYMENT_ID=dep-dauhuh5g1s2s73d0o57g
API_RELEASE_STATUS=LIVE
```

Worker, Web, and migration jobs were skipped.

## Public API validation

```text
HEALTHZ_HTTP=200
HEALTHZ_BODY={"status":"ok","gitSha":"4723b41f7ca77047b3bd5174c898ea6e9581fe49"}
READYZ_HTTP=200
READYZ_BODY={"status":"ready","gitSha":"4723b41f7ca77047b3bd5174c898ea6e9581fe49"}
OPENAPI_HTTP=200
HOME_HTTP=200
HOME_RESPONSE_CLASS=HTTP_200_TYPED_HOME_JSON
HOME_TRANSPORT_STATUS=REACHABLE
HOME_PUBLICATION_STATE=PUBLISHED
HOME_DATA_DATE=2026-09-30
```

The Home response returned `v2.home-read-model.v2`, with available market
overview and signal data. Topic-dependent sections that lack formal upstream
publication remain typed unavailable; no transport error is used for those
states.

## CORS and browser validation

```text
CORS_STATUS=PASS
ACCESS_CONTROL_ALLOW_ORIGIN=https://topicpilot-platform.game0962046460.chatgpt.site
CORS_GET_ALLOWED=GET
FRONTEND_API_BASE_STATUS=PASS
BROWSER_HOME_REQUEST_URL=https://topicpilot-api.onrender.com/api/v2/home
BROWSER_HOME_REQUEST_RESULT=HTTP_200; Today rendered available and typed unavailable states
BROWSER_CONSOLE_ERROR=NONE
```

After reloading the published frontend, the page rendered market overview,
market signals, and publication markers. Main Topics, Topic Pulse, fast
rotation, and Opportunity retained their existing typed unavailable states.
The page no longer contains `Failed to fetch`.

## Safety boundary

```text
POST_CLOSE_RETRIED=NO
PRODUCTION_DB_MUTATED=NO
MIGRATION_CHANGED=NO
TODAY_SEMANTICS_CHANGED=NO
WORKER_DEPLOYED=NO
WEB_DEPLOYED=NO
PRIMARY_ROOT_CAUSE=API_HOME_RESPONSE_VALIDATION_FAILURE
FIX_APPLIED=API_SCHEMA_NULLABILITY_AND_GOVERNED_API_ONLY_RELEASE
NEXT_RECOMMENDED_TASK=NONE_FOR_THIS_TRANSPORT_INCIDENT
```

No database contents, migration, Worker schedule, `2026-09-30` recovery,
Topic score, Lifecycle, or Today semantic policy was changed.

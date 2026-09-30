# TASK-PUBLIC-TODAY-FETCH-INCIDENT-022

## Final status

The public Today transport incident is fixed and validated. The frontend API
origin and CORS configuration were correct. The failure was an API response
validation error on `/api/v2/home`: unavailable institutional-flow aggregate
metadata was returned as `null`, while the API response schema required
non-null `unit` and `scale` values. The browser surfaced the resulting HTTP
500, which lacked a usable CORS response header, as `Failed to fetch`.

The fix makes those unavailable metadata fields explicitly nullable and was
released through the governed API-only path. Today now renders its available
market sections and typed unavailable states for sections whose formal data is
not present.

```text
TASK_ID=TASK-PUBLIC-TODAY-FETCH-INCIDENT-022
TASK_STATUS=COMPLETE_PUBLIC_TODAY_TRANSPORT_RESTORED
TASK_COMPLETE=YES
```

## Before-fix evidence

The initial public probes showed:

```text
HEALTHZ_HTTP=200
READYZ_HTTP=200
API_RUNTIME_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be
HOME_HTTP=500
FRONTEND_API_BASE_URL=https://topicpilot-api.onrender.com
CORS_PREFLIGHT=200
ACCESS_CONTROL_ALLOW_ORIGIN=https://topicpilot-platform.game0962046460.chatgpt.site
```

The Render API log for the failed Home request reported response validation
errors at `marketOverview.institutionFlows.aggregate` for `investmentTrust`,
`dealer`, and `total`: `unit` and `scale` were `None` although the deployed
schema required `string` and `integer`. This established an API response
contract/runtime failure, not an incorrect frontend base URL or a CORS
allowlist regression.

## Fix and deployment

The API contract change is limited to:

- `MarketFlowLegRead.unit` and `.scale`: nullable;
- `MarketFlowWindowRead.unit` and `.scale`: nullable;
- focused contract coverage for unavailable institutional-flow metadata;
- synchronized OpenAPI and generated TypeScript API declarations.

The change was merged in [PR #43](https://github.com/Xiezhou0828/topicpilot-platform/pull/43).
The governed API-only release was [workflow run 36730800314](https://github.com/Xiezhou0828/topicpilot-platform/actions/runs/36730800314):

```text
CURRENT_MAIN_SHA=4723b41f7ca77047b3bd5174c898ea6e9581fe49
API_DEPLOYED_SHA=4723b41f7ca77047b3bd5174c898ea6e9581fe49
API_RELEASE_RUN_ID=36730800314
RENDER_API_DEPLOYMENT=dep-dauhuh5g1s2s73d0o57g
API_RELEASE_STATUS=LIVE
```

Worker, Web, and migration jobs were skipped. The Worker remained at its
previous validated runtime SHA and was not redeployed.

## Public API validation

```text
HEALTHZ_HTTP=200
HEALTHZ_BODY={"status":"ok","gitSha":"4723b41f7ca77047b3bd5174c898ea6e9581fe49"}

READYZ_HTTP=200
READYZ_BODY={"status":"ready","gitSha":"4723b41f7ca77047b3bd5174c898ea6e9581fe49"}

OPENAPI_HTTP=200
HOME_HTTP=200
HOME_RESPONSE_CLASS=HTTP_200_TYPED_HOME_JSON
API_RUNTIME_SHA=4723b41f7ca77047b3bd5174c898ea6e9581fe49
```

The successful Home response reported:

```text
HOME_TRANSPORT_STATUS=REACHABLE
HOME_PUBLICATION_STATE=PUBLISHED
HOME_DATA_DATE=2026-09-30
HOME_CONTRACT_VERSION=v2.home-read-model.v2
```

The API response contains available market overview and signal data. Formal
Topic-dependent sections remain explicitly unavailable where their upstream
publication is absent; this is typed application state, not a transport
failure.

## CORS and frontend origin

```text
CORS_STATUS=PASS
ACCESS_CONTROL_ALLOW_ORIGIN=https://topicpilot-platform.game0962046460.chatgpt.site
CORS_GET_ALLOWED=GET
FRONTEND_API_BASE_URL=https://topicpilot-api.onrender.com
FRONTEND_API_BASE_STATUS=PASS (published <html data-api-base-url> readback)
```

The preflight returned HTTP 200 with the exact frontend origin and allowed
`GET`. The successful GET response also returned the exact
`Access-Control-Allow-Origin` value.

## Browser reproduction after fix

The published frontend was reloaded after the API deployment. Its rendered
runtime configuration was:

```text
BROWSER_HOME_REQUEST_URL=https://topicpilot-api.onrender.com/api/v2/home
BROWSER_HOME_REQUEST_RESULT=HTTP_200; Today rendered available sections and typed unavailable states
BROWSER_CONSOLE_ERROR=NONE
```

The page no longer contains `Failed to fetch`. Market overview, market
signals, and their data-date/publication markers render normally. Main Topics,
Topic Pulse, fast rotation, and Opportunity sections render their existing
typed unavailable states where formal evidence is not available.

## Safety boundaries

```text
POST_CLOSE_RETRIED=NO
PRODUCTION_DB_MUTATED=NO
MIGRATION_CHANGED=NO
TODAY_SEMANTICS_CHANGED=NO
WORKER_DEPLOYED=NO
WEB_DEPLOYED=NO
```

Only the API response contract and its generated API artifacts changed. No
database contents, migration, Worker schedule, `2026-09-30` recovery, Topic
score, Lifecycle, or Today semantic policy was changed.

```text
PRIMARY_ROOT_CAUSE=API_HOME_RESPONSE_VALIDATION_FAILURE
FIX_APPLIED=API_SCHEMA_NULLABILITY_AND_GOVERNED_API_ONLY_RELEASE
TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=NONE_FOR_THIS_TRANSPORT_INCIDENT
```

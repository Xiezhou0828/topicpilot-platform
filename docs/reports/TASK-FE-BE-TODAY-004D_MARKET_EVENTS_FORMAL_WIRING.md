# TASK-FE-BE-TODAY-004D｜Market Events / Market Story Formal Wiring

## Scope

This isolated implementation starts from `origin/main` at
`eb50d2d1e242290e2b9c6c95389bd7cd257caf26`. It wires the existing Today Market
Events contract into the shared Today Home resource. It does not merge main,
push main, deploy, mutate Production, or modify the DATA-REF path.

## Contract audit

| Product section | Backend authority | Current contract state |
| --- | --- | --- |
| Market Events | `HomeResponse.marketPulse` / `HomeMarketPulseEvent[]` | `PARTIAL` / `TEMPORARY`: schema exists, events are derived from topic snapshots and `dataQuality.temporarySections` includes `marketPulse` |
| Market Story | `HomeResponse.dailyFocus` / `HomeDailyFocus` | `PARTIAL` / `TEMPORARY`: already wired by 004C; current source is `POSTGRES_TOPIC_SNAPSHOT_RULE` and `temporary=true` |

The event fields are `eventTime`, `topic`, `eventType`, `description`,
`severity`, `topicSlug`, and `source`. No backend route, schema, OpenAPI, or
generated-client change was required.

## Implementation

- Added `TodayMarketEventsResource` to the existing `TodayHomeResource`
  projection path.
- Added fail-closed validation for all event identity, content, event type,
  severity, topic slug, and source fields.
- Preserved backend array order; no browser sorting, ranking, event derivation,
  lifecycle inference, or narrative generation was added.
- Removed the hardcoded Today Market Events array from `TodayMarketPage.tsx`.
- Rendered backend event description, type, severity, source, topic identity,
  and shared data metadata.
- Preserved `FORMAL`, `TEMPORARY`, `PREVIEW`, and `UNAVAILABLE` semantics.
  Temporary data is visible only as `TEMPORARY`; it is never promoted to
  `FORMAL`. Empty, incomplete, gated, and transport-error data fail closed.
- Kept Daily Focus, main topics, heating, and cooling on the same single
  `getHome()` request.

## Validation

- Focused Market Events and Today regression: `20/20` passed.
- Frontend full test/build: `113/113` passed.
- API client generated-contract drift and tests: `3/3` passed.
- TypeScript: passed.
- Targeted and full lint: passed; one pre-existing unrelated warning remains in
  `TopicDetailPage.tsx:114`.
- Demo snapshot check, diff check, and changed-file secret sanity scan: passed.

## Fixed status

```text
HOME_REQUEST_REUSED = YES
EXTRA_HOME_REQUESTS_ADDED = 0
MARKET_EVENTS_BACKEND_FIELD = marketPulse
MARKET_STORY_BACKEND_FIELD = dailyFocus
CONTRACT_STATE = PARTIAL / TEMPORARY
HARDCODED_MARKET_EVENTS_REMOVED = YES
HARDCODED_MARKET_STORY_REMOVED = ALREADY_REMOVED_BY_004C
BACKEND_ORDER_PRESERVED = YES
BACKEND_HEADLINE_OWNED = YES
BACKEND_SUMMARY_OWNED = YES
MODE_PRESERVED = YES
SOURCE_PRESERVED = YES
DATA_DATE_PRESERVED = YES
AS_OF_PRESERVED = YES
API_ERROR_FALLBACK_TO_MOCK = NO
BROWSER_EVENT_DERIVATION = NO
BROWSER_RANKING = NO
BROWSER_NARRATIVE_GENERATION = NO
BACKEND_CONTRACT_CHANGED = NO
OPENAPI_SEMANTICS_CHANGED = NO
DATA_REF_FILES_TOUCHED = NO
PUSH_MAIN = NO
MERGE_MAIN = NO
DEPLOY = NO
PRODUCTION_MUTATION = NO
NEXT_TASK_MODIFIED = NO
FINAL_STATUS = READY_FOR_TODAY_004D_INTEGRATION_REVIEW
```

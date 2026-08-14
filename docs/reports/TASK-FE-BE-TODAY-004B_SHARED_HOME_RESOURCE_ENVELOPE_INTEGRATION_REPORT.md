# TASK-FE-BE-TODAY-004B | Shared Home Resource Envelope Integration

Status: `READY_FOR_TODAY_004B_INTEGRATION_REVIEW`

## Authority and scope

- `CURRENT_MAIN_SHA`: `8a818935fe63eb3c3db9592c5068363c7ec941e9`
- `BRANCH`: `codex/task-fe-be-today-004b-20260813`
- `RESOURCE_REFACTOR_STRATEGY`: create `today-home.ts` as the single Home transport/publication/resource boundary, then keep `today-mainlines.ts` as a compatibility projection for the existing TODAY-002/003 UI.
- The implementation is frontend-only. FastAPI, OpenAPI, generated declarations, database, provider authority, migrations, Scheduler, and gate state were not changed.

The implementation reuses the existing `GET /api/v2/home` runtime path through `createTopicPilotClient().getHome()`. It adds no alternate Home client and no extra Home request.

## Today page section audit

| Section | Current UI state | Contract and dependency | Classification | 004B result / next boundary |
|---|---|---|---|---|
| Market Overview | Existing metric UI still contains hardcoded/mock presentation values with selective snapshot wiring | `HomeResponse.marketOverview` exists, but the current backend read model is `PARTIAL`; market health may be present while indices, turnover, and the V2 topic-domain fields remain outside the formal contract | `B`; formal promotion also depends on `D` | Mapped into the shared resource. UI unchanged. A later contract/UI slice must wait for complete backend authority and `downstreamReady`/gate evidence. |
| Daily Focus / Market Story | Page still renders the existing hardcoded story copy | `HomeResponse.dailyFocus` exists and is explicitly `temporary`, sourced from the topic-snapshot rule projection | `A` for frontend wiring, with temporary publication guard; `E` whenever backend metadata marks it SHADOW/PREVIEW | Mapped into `TodayHomeResource` only. UI replacement is deferred to a later slice. |
| Main Topics | Existing TODAY-002 UI consumes the Home main topic cards | `HomeResponse.mainTopics` / `HomeTopicCard`, backed by the Home read model and topic snapshot/reference dependencies | `A` | Shared resource now owns the section; the compatibility projection preserves backend order, nulls, and slugs. |
| Market Events | Page still renders its hardcoded `events` array | `HomeResponse.marketPulse` exists, but the current Home source is derived from topic snapshots and listed as temporary; no standalone formal event read model/route is present | `A` for Home-field wiring; `C` for a formal event surface; `E` for SHADOW/PREVIEW-only input | Mapped into `TodayHomeResource` only. No browser event classification, severity calculation, sorting, or deduplication was added. |
| Heating / Cooling | Existing TODAY-003 UI consumes Home rotation arrays | `HomeResponse.heatingTopics` / `coolingTopics` / `HomeRotationTopic`, ordered by backend | `A` | Shared resource now owns both sections. Existing order, topic slugs, and fail-closed semantics remain intact. |
| Opportunity | Page still renders its hardcoded Opportunity teaser | `HomeResponse.opportunities` exists but is marked temporary; formal Opportunity authority remains downstream of the existing shadow surfaces and is not a formal Home promotion | `A` for Home-field wiring; `C` for a formal Home Opportunity read model; `E` for SHADOW/PREVIEW-only data; formal promotion also has `D` dependencies | Mapped into `TodayHomeResource` only. No UI replacement, qualification, ranking, BUY/SELL derivation, target, stop, or score logic was added. |

## Existing routes and contract gaps

| Surface | Existing route | Current contract status |
|---|---|---|
| Home envelope and all six Home sections | `GET /api/v2/home` | Existing generated `HomeResponse`; one request reused by the frontend. |
| Main Topics | `HomeResponse.mainTopics` | Present; formal availability remains backend/publication controlled. |
| Heating / Cooling | `HomeResponse.heatingTopics`, `HomeResponse.coolingTopics` | Present; formal availability remains backend/publication controlled. |
| Daily Focus | `HomeResponse.dailyFocus` | Present but temporary/rule-derived; no separate formal route required for 004B. |
| Market Pulse / Events | `HomeResponse.marketPulse` | Present but temporary/derived; no standalone formal event route/read model. |
| Market Overview | `HomeResponse.marketOverview` | Present but partial; no browser-side index, turnover, or breadth completion is allowed. |
| Opportunity shadow surfaces | `/api/v1/opportunities/shadow`, `/api/v1/topics/{topic_id}/opportunities/shadow`, `/api/v1/stocks/{instrument_id}/opportunities/shadow`, `/api/v1/opportunities/shadow/{opportunity_id}` | SHADOW-only surfaces. They cannot be presented as formal Home recommendations. |

## Shared resource implementation

`apps/web/app/lib/today-home.ts` now defines the typed `TodayHomeResource` envelope:

- transport state: `LOADING | READY | ERROR`;
- publication state: `FORMAL | TEMPORARY | PREVIEW | UNAVAILABLE`;
- raw `HomeResponse | null`;
- `mainTopics`, `heatingTopics`, `coolingTopics`, `dailyFocus`, `marketPulse`, `opportunities`, and `marketOverview` sections;
- `dataDate`, `asOf`, `source`, generated `HomeDataQuality`, `temporarySections`, `missingSections`, `classification`, `status`, and `reason` metadata.

`fetchTodayHomeResource()` performs exactly one `client.getHome({ signal })`. API errors produce `ERROR` plus `UNAVAILABLE`; they never substitute hardcoded formal data. Null values stay null and empty arrays stay empty.

`apps/web/app/lib/today-mainlines.ts` now projects the shared resource for the existing page. This keeps TODAY-002/003 compatibility without a second request. The projection validates required rotation fields but does not sort, rank, infer direction, derive lifecycle, calculate breadth, classify events, or qualify/rank opportunities.

The page component was intentionally not changed. Daily Focus, Market Events, Opportunity, and Market Overview remain existing UI surfaces until their own safe vertical slices are approved.

## Gate and publication dependencies

- `FORMAL`: only when the Home publication metadata is complete and does not mark the payload as partial, temporary, unavailable, synthetic, fixture, demo, shadow, G1-blocked, or downstream-unready.
- `TEMPORARY`: explicit backend partial/temporary metadata is propagated and remains fail-closed for the existing formal Today mainline projection.
- `PREVIEW`: non-formal data is exposed only when the explicit Today preview flag is enabled.
- `UNAVAILABLE`: transport errors, incomplete publication metadata, unavailable/gated sources, and empty/incomplete formal sections do not become formal UI data.
- G1/G2/G3, downstream readiness, Canary, Scheduler, reference remediation, and Production activation were not run or changed by this task.

## Safe vertical slice order after 004B

1. **TODAY-004C | Daily Focus resource-to-UI wiring** — depends only on the shared resource and explicit `temporary`/publication metadata. Safe to implement in parallel with DATA-REF-005C only if the UI remains status-first and never claims formal publication.
2. **TODAY-004D | Market Pulse/Event resource-to-UI wiring** — same dependency and safety boundary; render backend event fields only, without browser classification, severity, ordering, or deduplication.
3. **TODAY-004E | Market Overview contract completion audit/adapter** — can prepare typed mapping and missing-field tests in parallel, but UI promotion waits for the formal market read model and downstream readiness.
4. **TODAY-004F | Opportunity shadow/temporary surface** — only after an explicit SHADOW/PREVIEW presentation contract is approved; must not become a formal recommendation surface.
5. **Formal Today promotion** — after the relevant G1 → G2 → G3 and downstream/Canary evidence is actually available. This is not part of 004B.

The first four slices can be prepared without touching DATA-REF-005C, provider authority, migrations, Production DB, or gate execution, provided their publication state remains explicit. Formal activation cannot be safely parallelized before those dependencies converge.

## Validation and scope

- `HOME_REQUEST_REUSED=YES`
- `EXTRA_HOME_REQUESTS_ADDED=0`
- `GENERATED_HOME_RESPONSE_USED=YES`
- `SHARED_HOME_RESOURCE_CREATED_OR_REFACTORED=YES`
- `DATA_QUALITY_PROPAGATED=YES`
- `TEMPORARY_METADATA_PROPAGATED=YES`
- `SOURCE_METADATA_PROPAGATED=YES`
- `AS_OF_METADATA_PROPAGATED=YES`
- `TRANSPORT_PUBLICATION_STATE_SEPARATED=YES`
- `TODAY_002_REGRESSION=PASS`
- `TODAY_003_REGRESSION=PASS`
- `API_ERROR_FALLBACK_TO_MOCK=NO`
- `FRONTEND_RANKING_ADDED=NO`
- `FRONTEND_EVENT_LOGIC_ADDED=NO`
- `FRONTEND_OPPORTUNITY_LOGIC_ADDED=NO`
- `DAILY_FOCUS_UI_REPLACED=NO`
- `MARKET_EVENTS_UI_REPLACED=NO`
- `OPPORTUNITY_UI_REPLACED=NO`
- `MARKET_OVERVIEW_UI_CHANGED=NO`
- `BACKEND_CONTRACT_CHANGED=NO`
- `OPENAPI_SEMANTICS_CHANGED=NO`

Validation passed: focused Today/Home tests `21/21`, frontend suite `83/83`, API client tests `3/3`, TypeScript, targeted ESLint, full ESLint (one unrelated pre-existing warning in `TopicDetailPage.tsx`), frontend build, OpenAPI gate, OpenAPI generated-contract idempotence, `git diff --check`, and changed-file secret-pattern scan.

Files changed by this task:

- `apps/web/app/lib/today-home.ts`
- `apps/web/app/lib/today-mainlines.ts`
- `apps/web/tests/today-home-resource.test.mjs`
- `apps/web/tests/today-mainlines.test.mjs`
- this report
- append-only `docs/AI_WORKLOG.md`

`PRODUCTION_MUTATION=NO`, `PUSH=NO`, `MERGE_MAIN=NO`, `DEPLOY=NO`, `NEXT_TASK_MODIFIED=NO`.

`COMMIT_SHA`: `f87014e83acb13d859326515a5f4f980733a4711`

# TopicPilot Preview Review Environment

`TASK_ID=TASK-PREVIEW-REVIEW-ENVIRONMENT-001`

`TASK_STATUS=COMPLETE_LOCAL_PREVIEW_READY`

`TASK_TYPE=implementation`

`REQUIRED_TERMINAL_STATE=CANONICALIZED`

`LOCAL_PREVIEW_REVIEW_ENVIRONMENT_READY=YES`

`REAL_PRODUCT_REVIEW_CAN_BEGIN=YES`

`REAL_FORMAL_DATA_REVIEW_READY=YES`

## Decision summary

This task keeps Preview local-first and free-first. The selected architecture is
the existing local vinext runtime plus a fixed-target, localhost-only,
read-only proxy to the already-public formal API. No cloud Preview, paid
infrastructure, staging database, Production CORS change, writer credential, or
Production mutation was introduced.

`SELECTED_ARCHITECTURE=OPTION_B_LOCAL_VINEXT_PREVIEW_PLUS_FIXED_TARGET_READ_ONLY_PROXY`

`LOCAL_FIRST=YES`

`FREE_FIRST=YES`

`CLOUD_PREVIEW_REQUIRED=NO`

`HOSTED_PREVIEW_PROVISIONED=NO`

`NEW_COST_CREATED=NO`

`STAGING_DATABASE_REQUIRED=NO`

The implementation is intentionally additive. Topic Overview and Topic Detail
V1.1 remain the existing product surfaces; this task only makes them reusable
for human review under an explicit Preview environment.

## Canonical and implementation state

| Field | Value |
| --- | --- |
| `CANONICAL_REPOSITORY` | `Xiezhou0828/topicpilot-platform` |
| `CANONICAL_BRANCH` | `main` |
| `CANONICAL_BASE` | `8894138fc930b4512541cacd5214162cd66b4c8f` |
| `ORIGIN_MAIN_AT_START` | `8894138fc930b4512541cacd5214162cd66b4c8f` |
| `IMPLEMENTATION_BRANCH` | `codex/task-preview-review-environment-001` |
| `IMPLEMENTATION_HEAD` | `5081d28dc464a57ee553f0d89a007d4a6be41fdf` |
| `CANONICAL_HEAD_FINAL` | `dd95fd410d59fcf34cd432ba3852dfeb3a07d3cc` |
| `WORKTREE` | `C:\Users\acer\Desktop\topicpilot-platform-review-env-001` |
| `WORKTREE_STATE` | clean at exact `IMPLEMENTATION_HEAD` after validation |
| `CANONICAL_INTEGRATION` | PR #71 merged into `main`; no direct main mutation |

The shared checkout was not reset, cleaned, or overwritten. It contained an
unrelated closure/publication branch, so implementation was isolated in a
separate clean worktree created from verified `origin/main`.

## Owner start and stop

Fast iterative review:

```bash
npm run preview:review -- --mode iterative --port 4317
```

`ITERATIVE_LOCAL` is intentionally allowed to be dirty and hot-reloadable. It
is not an exact release candidate and must not be described as exact.

Reproducible formal-data review:

```bash
npm run preview:review -- --mode exact-sha \
  --candidate-ref 46f211e349a256a325b410de48769342d35239e3 \
  --read-api-origin https://topicpilot-api.onrender.com \
  --port 4317
```

`EXACT_SHA_CANDIDATE` requires a clean worktree and `HEAD` equal to the
requested candidate SHA. It writes and verifies Preview provenance before
starting the local server. The verified review URL was:

`PREVIEW_URL=http://localhost:4317`

`OWNER_STOP_COMMAND=Ctrl+C`

Port `3000` was already occupied by an unrelated Docker Desktop listener in the
review environment. The runner now fails clearly when a requested port is busy;
it does not silently switch to another port.

## Data mode and boundary

| Field | Value |
| --- | --- |
| `DATA_MODE` | `REAL_READ_ONLY` when `--read-api-origin` is supplied |
| `REAL_FORMAL_DATA_REVIEW_READY` | `YES` |
| `DATA_TARGET` | `https://topicpilot-api.onrender.com` |
| `LOCAL_PROXY_USED` | `YES` in real-data mode |
| `REPRESENTATIVE_SYNTHETIC_MODE` | available when no read-only origin is supplied |
| `PRODUCTION_CORS_CHANGED` | `NO` |
| `WRITER_AUTHORITY` | `NONE` |
| `PRODUCTION_MUTATION_CAPABILITY` | `NONE` |
| `CREDENTIALS_FORWARDING` | `NONE` |
| `DIAGNOSTICS_DEFAULT` | `OFF` |

The public formal API was checked read-only at task start. Its topic catalog
returned formal data (`total=132`, current data date `2026-10-05`). Direct
browser access from `http://localhost:3000` had no CORS allow-origin header,
while the existing public Sites origin was allowlisted. The local proxy avoids
that CORS gap without changing the Production API.

Proxy controls are fixed in `apps/web/preview_proxy.mjs`:

- upstream is HTTPS-only, except for local loopback development origins;
- only `GET` and `HEAD` are accepted;
- only `/api/v1/snapshot`, `/api/v1/topic-intelligence`, and `/api/v2` prefixes
  are forwarded;
- authorization, cookie, proxy-authorization, API-key, API-token, and forwarded
  authorization headers are stripped;
- non-allowlisted API paths return `404`, and mutating methods return `405`.

## Owner usability validation

The final exact candidate completed the runner and read-only browser smoke on
`2026-10-05`:

| Surface | Result |
| --- | --- |
| Local home `/` | `200`, formal market read model visible |
| Topic Overview `/topics` | `200`, `107` Leaf topics and formal map/explorer visible |
| Topic Detail `/topics/SiC%20晶圓／基板` | `200`, formal grade/lifecycle/history/members visible |
| Default diagnostics | engineering/lineage section remained collapsed |
| Formal API through localhost proxy | successful catalog response with formal items |
| `POST /api/v2/topic-catalog` | `405` |
| `GET /api/v1/admin` | `404` |

Observed product behavior was truthful: unavailable formal fields stayed
labelled unavailable rather than being filled with synthetic research values.

## Validation evidence

The following checks passed on the implementation line:

- `node --test infra/scripts/tests/preview_proxy.test.mjs infra/scripts/tests/preview_review.test.mjs` — 7 passed;
- `node --test infra/scripts/tests/preview_provenance.test.mjs` — 8 passed;
- `node --test apps/web/tests/topic-catalog-formal-integration.test.mjs` — 3 passed;
- `npm run demo:snapshot:check --prefix apps/web` — snapshot matches fixtures;
- `npm run lint --prefix apps/web` — 0 errors, one pre-existing `FavoriteButton.tsx` hook warning;
- `npx tsc --noEmit` from `apps/web` — passed;
- `npm run build --prefix apps/web` — passed;
- exact runner frontend suite — 206 passed;
- `git diff --check` — passed;
- exact provenance record — `REAL_READ_ONLY_API_TARGET`, `previewWriteAuthority=NONE`, `productionPromotion=NOT_AUTHORIZED_NOT_EXECUTED`.

The exact runner intentionally performs the same checks before starting the
server. It reports:

```text
TOPICPILOT_PREVIEW_REVIEW=READY
REVIEW_MODE=EXACT_SHA_CANDIDATE
PREVIEW_CANDIDATE_SHA=5081d28dc464a57ee553f0d89a007d4a6be41fdf
DATA_MODE=REAL_READ_ONLY
LOCAL_PROXY_USED=YES
DIAGNOSTICS_DEFAULT=OFF
PREVIEW_URL=http://localhost:4317
```

## Route and V1.1 readiness

`TOPIC_OVERVIEW_REVIEW_READY=YES`

`TOPIC_DETAIL_REVIEW_READY=YES`

`TOPIC_OVERVIEW_V1_1_IMPLEMENTED_BY_THIS_TASK=NO`

`TOPIC_DETAIL_V1_1_IMPLEMENTED_BY_THIS_TASK=NO`

The review environment reuses the canonical Topic Overview/Detail behavior
already present on the candidate. It does not reimplement or broaden those
surfaces.

## Infrastructure and security outcome

`PRODUCTION_DEPLOY_EXECUTED=NO`

`SITES_PUBLISH_EXECUTED=NO`

`PRODUCTION_CORS_MUTATION_EXECUTED=NO`

`SCHEDULER_OR_PUBLICATION_MUTATION_EXECUTED=NO`

`DATABASE_MIGRATION_EXECUTED=NO`

`DNS_OR_SECRET_MUTATION_EXECUTED=NO`

`PAID_INFRASTRUCTURE_CREATED=NO`

The local process exposes only the web Preview and the allowlisted read proxy.
No writer credentials are loaded or forwarded, and no request path grants
Production mutation authority.

## Follow-up and terminal state

`TASK_COMPLETE=YES`

`FOLLOW_UP_REQUIRED=NO`

`FOLLOW_UP_REASON=Owner product review remains a human decision; no infrastructure authorization is required.`

Canonical integration is complete through PR #71. No cloud hosting, Production
CORS authorization, staging database, or paid service is required for the Owner
to begin local product review.


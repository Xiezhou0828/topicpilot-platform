# TASK-PREVIEW-STAGING-RELEASE-LANE-001

## Status

`TASK=TASK-PREVIEW-STAGING-RELEASE-LANE-001`

`TASK_STATUS=READY_FOR_OWNER_AUTHORIZATION`

`TASK_TYPE=implementation`

`REQUIRED_TERMINAL_STATE=CANONICALIZED`

`ACHIEVED_TERMINAL_STATE=VALIDATED`

`TASK_COMPLETE=NO`

`FOLLOW_UP_REQUIRED=YES`

`PREVIEW_LANE_CURRENT_READINESS=PARTIAL`

`CANONICAL_BRANCH=main`

`CANONICAL_HEAD=a687c748e1b7d512449b69884626c58ac7d86d12`

`ORIGIN_MAIN=a687c748e1b7d512449b69884626c58ac7d86d12`

`WORKTREE=C:/Users/acer/Desktop/題材領航/task-021-checkpoint-lifecycle`

`CURRENT_BRANCH=codex/task-preview-staging-release-lane-001`

`ALEMBIC_HEAD=0048_task_checkpoint_provider_metric_applicability`

The bounded non-Production implementation is present and locally validated on
the task branch. No push, merge, hosted Preview publication, CORS mutation,
Production mutation, or Production promotion was authorized or performed.

## Forensic baseline

| Field | Finding |
| --- | --- |
| `CANONICAL_REPOSITORY` | `Xiezhou0828/topicpilot-platform` |
| `CANONICAL_BRANCH` | `main` |
| `CANONICAL_HEAD_AT_START` | `a687c748e1b7d512449b69884626c58ac7d86d12` |
| `ORIGIN_MAIN_AT_START` | `a687c748e1b7d512449b69884626c58ac7d86d12` |
| `TASK_BRANCH` | `codex/task-preview-staging-release-lane-001` |
| `EXISTING_PREVIEW_CAPABILITY` | `NOT_OBSERVED` |
| `EXISTING_SITES_VERSIONING` | `YES` |
| `EXISTING_ARTIFACT_PROVENANCE` | `YES_CANONICAL_ONLY` |
| `EXISTING_PREVIEW_URL_CAPABILITY` | `NO_CURRENT_URL` |
| `EXISTING_CORS_SUPPORT` | `EXACT_ORIGINS_NO_CREDENTIALS_GET_ONLY` |
| `EXISTING_STAGING_API_CAPABILITY` | `NOT_OBSERVED` |
| `CURRENT_SITES_LIVE_URL` | `https://topicpilot-platform.game0962046460.chatgpt.site` |
| `CURRENT_SITES_VERSION` | `73` |
| `CURRENT_SITES_SOURCE_SHA` | `771afdcfa5342a9ffd9d90b8c2f5ee0e78a132c0` |
| `CURRENT_SITES_DEPLOYMENT` | `SUCCEEDED_READ_ONLY_OBSERVATION` |

The existing `web-artifact-verification.yml` is a canonical-main verification
workflow. The existing manual release workflow and Sites publishing flow are
Production authorities. Neither was changed or invoked for this task.

## Current authority map

| Field | Authority |
| --- | --- |
| `CURRENT_WEB_BUILD_AUTHORITY` | Existing manual `deploy.yml` `package_web` path for Production; additive `preview-web.yml` for candidate Preview builds |
| `CURRENT_ARTIFACT_AUTHORITY` | `infra/scripts/web_deployment_provenance.mjs` for canonical-main artifacts; `infra/scripts/preview_provenance.mjs` for Preview records |
| `CURRENT_SITES_VERSION_AUTHORITY` | Sites project `appgprj_6a6ce02bd75c81919ab3678ebf013c53`, saved version history, current live version 73 |
| `CURRENT_PRODUCTION_PROMOTION_AUTHORITY` | Protected Production jobs in `deploy.yml` plus the Sites publishing flow; not invoked |

## Selected architecture

| Field | Decision |
| --- | --- |
| `SELECTED_PREVIEW_ARCHITECTURE` | Manual GitHub Actions candidate-ref to immutable artifact |
| `PREVIEW_TRIGGER` | `workflow_dispatch` with required `candidate_ref` |
| `PREVIEW_REFERENCE_TYPE` | GitHub Actions artifact, named by candidate SHA and run id |
| `UI_ONLY_PREVIEW` | Synthetic checked-in snapshot, explicit Preview flags |
| `FULL_STACK_PREVIEW` | Deferred until isolated staging API and disposable DB exist |
| `PREVIEW_DATA_SOURCE` | Synthetic by default; optional exact HTTPS read-only API origin |
| `PREVIEW_WRITE_AUTHORITY` | `NONE` |
| `PREVIEW_PRODUCTION_PROMOTION` | `NOT_AUTHORIZED_NOT_EXECUTED` |
| `CORS_STRATEGY` | No Production mutation; future staging uses exact origins only |
| `ARTIFACT_RETENTION` | 14 days |

The frontend Preview gate now requires explicit `NEXT_PUBLIC_PREVIEW_MODE=true`
and `NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW=true`. Normal Production builds remain
fail-closed without a formal API origin. The Preview workflow also blanks the
AI Studio orchestration URL, so no external writer or service authority is
introduced.

## Provenance and implementation

Added:

- `.github/workflows/preview-web.yml` — manual, artifact-only Preview build;
- `infra/scripts/preview_provenance.mjs` — exact candidate SHA, data mode,
  API-origin, and no-write/no-promotion provenance record;
- `infra/scripts/tests/preview_provenance.test.mjs` — provenance and artifact
  boundary tests;
- explicit Preview gate in `apps/web/app/lib/topic-api.ts`;
- the formal catalog fail-closed assertion in
  `apps/web/tests/topic-catalog-formal-integration.test.mjs`;
- this report and the deployment runbook Preview section.

`client/__preview.json` is generated during the Preview build and copied into
the client artifact. It records `candidateGitSha`, `candidateRef`, build time,
the synthetic/read-only API mode, `previewWriteAuthority=NONE`, and
`productionPromotion=NOT_AUTHORIZED_NOT_EXECUTED`.

## Owner product-review gate

The Owner review must inspect the artifact across Topic Overview, Topic Detail,
Strength, A/B/D, lifecycle-uneven states, long names, empty/unavailable/
loading/error states, drawer/navigation/mobile behavior, Taiwan red/green
semantics, and engineering-leakage/fabricated-ranking checks. Review approval
is not stored as Production authorization by this workflow.

## Validation and release boundary

| Field | Result |
| --- | --- |
| `CANDIDATE_SHA_PROVENANCE` | Exact checked-out `HEAD` is required and recorded |
| `PREVIEW_ARTIFACT_PROVENANCE` | `client/__preview.json` is verified after build |
| `PREVIEW_URL_OR_REFERENCE` | Immutable GitHub Actions artifact reference; no hosted URL created |
| `PRODUCTION_SITE_BEFORE` | Existing public Sites live URL/version 73 observed read-only |
| `PRODUCTION_SITE_AFTER` | No Sites or Production mutation performed |
| `PRODUCTION_UNCHANGED` | `YES` within this task's authorized operations |
| `PUSH` | `NOT_AUTHORIZED_NOT_EXECUTED` |
| `MERGE` | `NOT_AUTHORIZED_NOT_EXECUTED` |
| `DEPLOY` | `NOT_AUTHORIZED_NOT_EXECUTED` |
| `PRODUCTION_MUTATION` | `NOT_AUTHORIZED_NOT_EXECUTED` |
| `NEXT_TASK` | `UNCHANGED` |

The local validation record is complete:

| Check | Result |
| --- | --- |
| Preview provenance tests | `PASS` — 8/8 |
| Focused frontend boundary tests | `PASS` — 7/7 |
| Synthetic fixture check | `PASS` |
| TypeScript check | `PASS` |
| Frontend lint | `PASS_WITH_WARNING` — 0 errors, 1 pre-existing React Hook warning |
| Preview build | `PASS` |
| Built artifact exact-SHA verification | `PASS` |
| Full frontend tests | `PASS` — 206/206 |
| `git diff --check` | `PASS` |

This report remains `VALIDATED`, not `CANONICALIZED`, until the Owner
authorizes integration.

## Required final handoff fields

`TESTS=PASS — Preview provenance 8/8; focused frontend boundary 7/7; full
frontend suite 206/206`

`BUILD=PASS — Preview build completed and emitted the candidate artifact`

`VALIDATION=PASS — exact candidate SHA, artifact provenance, snapshot,
TypeScript, lint (0 errors), and clean diff verification`

`OWNER_PRODUCT_REVIEW=DOCUMENTED_CHECKLIST_NOT_YET_APPROVED`

`PREVIEW_TRIGGER=workflow_dispatch(candidate_ref, optional api_base_url)`

`PREVIEW_URL_OR_REFERENCE=GitHub Actions artifact topicpilot-preview-<sha>-<run_id>; no hosted URL safely created`

`REPORT=docs/reports/TASK-PREVIEW-STAGING-RELEASE-LANE-001.md`

## Parallel-work protection

The shared Production release workflow, canonical web-artifact verification,
Render configuration, Sites project metadata, CORS configuration, daily
publication orchestration, and `NEXT_TASK` were treated as protected surfaces.
The Preview lane is additive and contains no call to Sites save/deploy, Render,
database migration, scheduler activation, or Production promotion.

## Owner authorization required

The remaining steps require explicit Owner or platform authorization:

1. authorize the branch push/merge or another approved canonical integration;
2. provision a private isolated Sites Preview or staging API/disposable DB if
   a real hosted/full-stack review is required;
3. approve any exact API CORS origin needed by that isolated host; and
4. run the Preview workflow and distribute its immutable artifact reference.

Deferred non-v1 work is hosted Preview URL provisioning, full-stack staging,
artifact cleanup automation beyond retention, and screenshot/browser
automation. None is represented as complete here.

## Release boundary declarations

`PRODUCTION_DEPLOY=NOT_AUTHORIZED_NOT_EXECUTED`

`PRODUCTION_SITES_PROMOTION=NOT_AUTHORIZED_NOT_EXECUTED`

`PRODUCTION_MIGRATION=NOT_AUTHORIZED_NOT_EXECUTED`

`POST_CLOSE_MUTATION=NOT_AUTHORIZED_NOT_EXECUTED`

`FORMAL_PUBLICATION_MUTATION=NOT_AUTHORIZED_NOT_EXECUTED`

`PUSH=NOT_AUTHORIZED_NOT_EXECUTED`

`NEXT_TASK=UNCHANGED`

`NEXT_RECOMMENDED_ACTION=Owner authorizes canonical integration, then runs the
manual Preview workflow; provision isolated private Sites/staging API only if
a hosted or full-stack product review is required.`

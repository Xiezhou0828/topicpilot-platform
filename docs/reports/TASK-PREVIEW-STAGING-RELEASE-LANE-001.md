# TASK-PREVIEW-STAGING-RELEASE-LANE-001

## Status

`TASK=TASK-PREVIEW-STAGING-RELEASE-LANE-001`

`TASK_STATUS=COMPLETE`

`TASK_TYPE=implementation`

`REQUIRED_TERMINAL_STATE=CANONICALIZED`

`ACHIEVED_TERMINAL_STATE=CANONICALIZED`

`TASK_COMPLETE=YES`

`FOLLOW_UP_REQUIRED=YES`

`FOLLOW_UP_REASON=Hosted Preview infrastructure intentionally remains separate and unprovisioned; it is not a blocker for the canonical software and governance lane.`

`PREVIEW_LANE_CURRENT_READINESS=PARTIAL`

`CANONICAL_BRANCH=main`

`CANONICAL_HEAD=f904fba9fa26e106ff5877dc742c0114f2a6a944`

`ORIGIN_MAIN=f904fba9fa26e106ff5877dc742c0114f2a6a944`

`WORKTREE=C:/Users/acer/Desktop/題材領航/task-021-checkpoint-lifecycle`

`CURRENT_BRANCH=codex/task-preview-staging-release-lane-001`

`ALEMBIC_HEAD=0048_task_checkpoint_provider_metric_applicability`

The bounded non-Production implementation was integrated through PR #69 using
the repository's merge-commit procedure. The canonical software and governance
lane is complete. No hosted Preview publication, CORS mutation, Production
mutation, or Production promotion was authorized or performed.

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
| `PUSH` | `PERFORMED — task-scoped canonical integration branch and PR #69` |
| `MERGE` | `PERFORMED — PR #69 merge commit` |
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

The Owner authorized canonical integration and final validation. PR #69 merged
the implementation into canonical `main`; the hosted Preview environment remains
a separate follow-up decision.

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

The canonical integration and final validation authorized for this task are
complete. The following remain a separate owner decision only if hosted or
full-stack review is required:

1. provision a private isolated Sites Preview or other non-Production host;
2. choose a UI-only read-only-compatible API or an isolated staging API with a
   disposable DB for contract-changing review;
3. approve the exact API CORS allowlist, secrets, access, and cost boundary; and
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

`PUSH=PERFORMED_VIA_PR_69_WITHOUT_PRODUCTION_DEPLOYMENT`

`NEXT_TASK=UNCHANGED`

`NEXT_RECOMMENDED_ACTION=TASK-HOSTED-PREVIEW-ENVIRONMENT-001 — owner decides
whether to provision a private non-Production host; UI-only review may use the
read-only-compatible API or synthetic default, while contract-changing review
requires an isolated staging API and disposable DB.`

## Owner-authorized canonical integration closure

`OWNER_AUTHORIZATION=GRANTED_FOR_CANONICAL_INTEGRATION_AND_FINAL_VALIDATION`

`PREVIOUS_CANDIDATE_SHA=e86bc65a9700c2a917fa569994dbc5f74cdc6797`

`CURRENT_ORIGIN_MAIN_BEFORE_INTEGRATION=a687c748e1b7d512449b69884626c58ac7d86d12`

`MAIN_ADVANCED_SINCE_HANDOFF=NO`

`RECONCILIATION_REQUIRED=NO`

`FINAL_TASK_BRANCH_SHA=e86bc65a9700c2a917fa569994dbc5f74cdc6797`

`LOCAL_CANONICAL_INTEGRATION_COMMITS=5beb64b4847637f1f941150d9e42a9c46db29d9f, 79b7179bdfc4891c4370f1db1005ee7ba4293bf9`

`CANONICAL_INTEGRATION_COMMIT=f904fba9fa26e106ff5877dc742c0114f2a6a944`

`CANONICAL_HEAD=f904fba9fa26e106ff5877dc742c0114f2a6a944`

`VALIDATED_CANONICAL_SHA=f904fba9fa26e106ff5877dc742c0114f2a6a944`

`PREVIEW_TESTS=PASS — 8/8`

`FOCUSED_TESTS=PASS — 7/7`

`FRONTEND_TESTS=PASS — 206/206`

`TYPECHECK=PASS`

`BUILD=PASS`

`PROVENANCE_VALIDATION=PASS — exact candidate SHA and built artifact SHA verified`

`LINT_OR_EQUIVALENT=PASS — 0 errors; one existing warning at apps/web/app/components/FavoriteButton.tsx:155:112`

`DIFF_SCOPE=PASS — exact eight-file task scope; no forbidden Production, CORS, scheduler, worker, or migration surface changed`

`CI_STATUS=PASS — run 37294311967; Backend/migration/OpenAPI job 111711816587; Frontend job 111711816602; Secret scan job 111711816306; Docker Compose smoke job 111712975430`

`PREVIEW_LANE_CANONICAL=YES`

`EXACT_SHA_PROVENANCE_READY=YES`

`READ_ONLY_BOUNDARY_READY=YES`

`PRODUCTION_SEPARATION_READY=YES`

`DEFAULT_PREVIEW_PRODUCT_SURFACE_DIAGNOSTICS_FREE=YES`

`HOSTED_PREVIEW_AVAILABLE=NO — current Sites current_preview_url was null; no hosted Preview was provisioned`

`PRODUCTION_MUTATED=NO`

`SITES_PRODUCTION_MUTATED=NO`

`CORS_PRODUCTION_MUTATED=NO`

`SCHEDULER_MUTATED=NO`

`FORMAL_PUBLICATION_DATA_MUTATED=NO`

`PREVIEW_LANE_FORMALLY_ACCEPTED=YES`

`FOLLOW_UP_RECOMMENDATION=TASK-HOSTED-PREVIEW-ENVIRONMENT-001 — provision a private/non-Production web host or Sites Preview only after Owner decision; UI-only review uses the read-only-compatible API or synthetic default, while contract-changing review uses an isolated staging/candidate API and disposable DB.`

`OWNER_DECISION_REQUIRED_FOR_FOLLOW_UP=YES — private host choice, staging API/disposable DB, exact CORS allowlist, secrets, environment access, and cost decisions.`

`PRODUCTION_DEPLOY=NOT_AUTHORIZED_NOT_EXECUTED`

`PRODUCTION_SITES_PROMOTION=NOT_AUTHORIZED_NOT_EXECUTED`

`PRODUCTION_MIGRATION=NOT_AUTHORIZED_NOT_EXECUTED`

`POST_CLOSE_MUTATION=NOT_AUTHORIZED_NOT_EXECUTED`

`FORMAL_PUBLICATION_MUTATION=NOT_AUTHORIZED_NOT_EXECUTED`

`NEXT_TASK=UNCHANGED`

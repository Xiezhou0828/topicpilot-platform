# TASK-DATA-REF-006H-P Production Runtime Freeze and Reference Transition Dry-Run Evidence

Date: 2026-08-14
Final status: READY_FOR_REFERENCE_REGISTRY_TRANSITION_ACTIVATION_AUTHORIZATION

## Scope

TASK-DATA-REF-006H-P seals the Production read-only gate after the 006G
reference-registry transition contract was integrated, pushed, CI-validated,
and deployed. It does not authorize transition activation. No Production
reference mutation, bootstrap retry, G2, G3, Canary, or Scheduler action was
performed.

## Application release provenance

APPLICATION_RELEASE_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
EXACT_SHA_CI_RUN = 31765247955
EXACT_SHA_CI = PASS
DEPLOY_RUN = 31765407955
DEPLOY = PASS
NON_FORCE_PUSH = YES

The application SHA is the 006G implementation-plus-documentation fast-forward
on origin/main. Any later documentation-only local commit must not be treated
as the application runtime authority.

## Production runtime freeze evidence

The operator executed the provenance checks in the authenticated Render
Production Shell:

RUNTIME_GIT_COMMIT = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
PROVIDER_LINEAGE_BUILD_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
PROVIDER_STATUS = READY
RUNTIME_SHA_VERIFIED = YES
G0 = PASS

Provider authority remained unchanged and canonical:

TPE = TWSE_OFFICIAL_DAILY / twse-official-daily.v2 / marketBatch=true
TWO = TPEX_OFFICIAL_DAILY / tpex-official-daily.v2 / marketBatch=true
Fallback providers are not canonical and cannot pass G2.

## Production migration and reference baseline

alembic current returned:

0030_task_data_ref_006g_registry_transition (head)

The operator reference check for the existing source registry returned:

SOURCE_REFERENCE_VERSION = tw-reference-v1
SOURCE_REFERENCE_ACTIVE = YES
SOURCE_REFERENCE_LOAD_STATUS = READY
MARKET_COUNT = 2
INSTRUMENT_COUNT = 507
MISSING_MARKETS = []
MISSING_INSTRUMENTS = []
DUPLICATE_IDENTITIES = []
REFERENCE_CALENDAR_DATE_COUNT = 24
registrySetCount = 1
requiredContextCount = 1
missingReferenceContexts = []

The source registry remains the prior active registry with the exact reviewed
source hash:

SOURCE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6

## Reference transition dry-run

The exact runbook command was executed with dry-run only:

topicpilot-reference-transition \
  --from-reference-version tw-reference-v1 \
  --expected-from-bundle-sha256 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6 \
  --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --dry-run

Machine-readable result:

operation = PLAN
status = VALIDATED
dryRun = true
fromReferenceVersion = tw-reference-v1
fromBundleSha256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
toReferenceVersion = tw-reference-v1-rollover-daf19e9eb051255c
toBundleSha256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
createdMarkets = 0
createdInstruments = 0
createdReferenceRows = 38
noopReferenceRows = 0
retiredRegistrySets = 1 (PLAN metadata; no retirement was committed)
oldRegistryPreserved = true
transitionRecorded = false
transactional = true
idempotent = true
sameVersionHashOverwrite = false
singleActiveRegistry = true
nonReferenceWriteSet = []

The planned write set is reference-only:

instruments
markets
reference_adjustments
reference_calendar_dates
reference_currencies
reference_instrument_lifecycles
reference_registry_sets
reference_registry_transitions
reference_sessions
reference_timezones
reference_trading_statuses

The committed 006G bundle and disposable PostgreSQL evidence establish that
the dry-run validation includes TPE:6806 lifecycle evidence and the
date-effective 2026-08-13 universe of TPE=313 and TWO=193. Those values are
validation criteria, not Production writes, and the transition CLI does not
emit them as separate aggregate JSON fields.

## Zero-mutation postcheck

After the dry-run, the operator reran the source reference check. It remained
ACTIVE/READY with 2 markets, 507 instruments, 24 calendar dates, no missing
markets or instruments, no duplicate identities, one registry set, and one
required context.

TRANSITION_DRY_RUN_MUTATION = NO
REFERENCE_STATE_CHANGED = NO
PRE_POST_REFERENCE_STATE_CHANGED = NO
PRODUCTION_MUTATION = NO
REFERENCE_TRANSITION_ACTIVATED = NO

No activate mode, manual SQL, ordinary bootstrap retry, G2, G3, Canary, or
Scheduler command was executed. No Production credentials or connection
strings were requested or exposed.

## Fixed report

TASK_DATA_REF_006H_P = COMPLETE
APPLICATION_RELEASE_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
RUNTIME_GIT_COMMIT = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
PROVIDER_LINEAGE_BUILD_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
RUNTIME_SHA_VERIFIED = YES
G0 = PASS
ALEMBIC_CURRENT = 0030_task_data_ref_006g_registry_transition (head)
MIGRATION_0029_STATE = PRESENT AS ANCESTOR OF 0030
SOURCE_REFERENCE_VERSION = tw-reference-v1
SOURCE_REFERENCE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
SOURCE_REFERENCE_ACTIVE = YES
SOURCE_REFERENCE_LOAD_STATUS = READY
MARKET_COUNT = 2
INSTRUMENT_COUNT = 507
MISSING_MARKETS = []
MISSING_INSTRUMENTS = []
DUPLICATE_IDENTITIES = []
TARGET_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
TARGET_REFERENCE_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
TRANSITION_DRY_RUN = true
TRANSITION_OPERATION = PLAN
TRANSITION_STATUS = VALIDATED
SOURCE_REGISTRY_MATCH = YES
TARGET_REGISTRY_VALIDATED = YES
SINGLE_ACTIVE_INVARIANT = YES
LIFECYCLE_6806_INCLUDED = YES
DATE_EFFECTIVE_TPE_2026_08_13 = 313
DATE_EFFECTIVE_TWO_2026_08_13 = 193
NON_REFERENCE_WRITE_SET = []
TRANSITION_DRY_RUN_MUTATION = NO
PRE_POST_REFERENCE_STATE_CHANGED = NO
PRODUCTION_MUTATION = NO
REFERENCE_TRANSITION_ACTIVATED = NO
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
FINAL_STATUS = READY_FOR_REFERENCE_REGISTRY_TRANSITION_ACTIVATION_AUTHORIZATION
BLOCKER = NONE

STOP. A separate one-shot Production activation authorization is required
before the transition activate mode may be considered.

# TASK-DATA-REF-006I One-Shot Production Reference Registry Transition Activation and G1 Revalidation

Date: 2026-08-14
Final status: READY_FOR_G2_PRODUCTION_PREFLIGHT_AUTHORIZATION

## Scope and authorization

TASK-DATA-REF-006I executed the separately authorized one-shot Production
reference registry transition from tw-reference-v1 to the immutable
lifecycle-bearing rollover registry. The mutation was limited to the
reference transition contract. No market-data/provider persistence, ordinary
bootstrap retry, G2 provider preflight, G3, Canary, or Scheduler action was
executed.

## Runtime authority and preconditions

APPLICATION_RUNTIME_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
RUNTIME_GIT_COMMIT = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
PROVIDER_LINEAGE_BUILD_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
PROVIDER_STATUS = READY
RUNTIME_SHA_VERIFIED = YES
G0 = PASS

Production migration was:

0030_task_data_ref_006g_registry_transition (head)

The source baseline before activation was:

SOURCE_REFERENCE_VERSION = tw-reference-v1
SOURCE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
SOURCE_REFERENCE_ACTIVE = YES
SOURCE_REFERENCE_LOAD_STATUS = READY
SOURCE_MARKET_COUNT = 2
SOURCE_INSTRUMENT_COUNT = 507
SOURCE_MISSING_MARKETS = []
SOURCE_MISSING_INSTRUMENTS = []
SOURCE_DUPLICATE_IDENTITIES = []
SOURCE_MISSING_REFERENCE_CONTEXTS = []

The final dry-run immediately before activation returned PLAN/VALIDATED with
the exact source hash, exact target hash, single-active invariant,
same-version hash overwrite rejection, transactional/idempotent semantics,
and nonReferenceWriteSet=[].

## One-shot activation result

The exact authorized command was executed once:

topicpilot-reference-transition \
  --from-reference-version tw-reference-v1 \
  --expected-from-bundle-sha256 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6 \
  --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --activate

The machine-readable activation result was:

TRANSITION_ACTIVATION_EXECUTED = YES
TRANSITION_ACTIVATION_RESULT = TRANSITION_ACTIVATED / ACTIVE
TRANSITION_TRANSACTIONAL = YES
TRANSITION_IDEMPOTENT = YES
CREATED_MARKETS = 0
CREATED_INSTRUMENTS = 0
CREATED_REFERENCE_ROWS = 38
RETIRED_REGISTRY_SETS = 1
OLD_REGISTRY_PRESERVED = YES
TRANSITION_PROVENANCE_RECORDED = YES
NON_REFERENCE_WRITE_SET = []

The target authority was:

TARGET_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
TARGET_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295

The activation output write set was reference-only:

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

## Target G1 revalidation

The target reference check returned:

TARGET_REFERENCE_ACTIVE = YES
TARGET_REFERENCE_LOAD_STATUS = READY
MARKET_COUNT = 2
PHYSICAL_INSTRUMENT_COUNT = 507
MISSING_MARKETS = []
MISSING_INSTRUMENTS = []
DUPLICATE_IDENTITIES = []
MISSING_REFERENCE_CONTEXTS = []
REFERENCE_CALENDAR_DATE_COUNT = 24
REGISTRY_SET_COUNT = 1
REQUIRED_CONTEXT_COUNT = 1
TRADING_STATUS_CATALOGUE_COUNT = 7
ADJUSTMENT_CATALOGUE_COUNT = 3
G1 = PASS

## Registry and lifecycle integrity

The read-only registry inspection returned:

ACTIVE_REGISTRY_COUNT = 1
ACTIVE_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
ACTIVE_REFERENCE_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
SOURCE_REGISTRY_RETIRED = YES
SOURCE_REGISTRY_PROVENANCE_PRESERVED = YES
TRANSITION_PROVENANCE_RECORDED = YES
TRANSITION_PROVENANCE_COUNT = 1
PHYSICAL_INSTRUMENT_COUNT = 507
REFERENCE_LIFECYCLE_ACTIVE = YES
REFERENCE_LIFECYCLE_ROW_COUNT = 1
REFERENCE_6806_LIFECYCLE_ACTIVE = YES

The target lifecycle row is:

market_code = TPE
instrument_code = 6806
status_code = DELISTED
effective_from = 2026-06-23
effective_to = NULL

The physical market counts are TPE=314 and TWO=193. Applying the committed
date-effective eligibility contract to 2026-08-13 excludes TPE:6806 because
DELISTED is an ineligible lifecycle status effective from 2026-06-23:

DATE_EFFECTIVE_RUN_DATE = 2026-08-13
DATE_EFFECTIVE_TPE_EXPECTED = 313
DATE_EFFECTIVE_TWO_EXPECTED = 193
TPE_6806_ELIGIBLE = NO

## Production mutation boundary

PRODUCTION_MUTATION = YES (authorized reference registry transition only)
PRODUCTION_MARKET_DATA_MUTATION = NO
PRODUCTION_PROVIDER_DATA_WRITE = NO
PRODUCTION_BOOTSTRAP_RETRY = NO
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO

The application runtime authority remains eb50d2d1e242290e2b9c6c95389bd7cd257caf26.
Any documentation-only commit created after this execution is a separate
DOCUMENTATION_SHA, is not the application runtime authority, and is not
pushed in this closure.

## Fixed report

TASK_DATA_REF_006I = COMPLETE
APPLICATION_RUNTIME_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
RUNTIME_SHA_VERIFIED = YES
G0 = PASS
SOURCE_REFERENCE_VERSION = tw-reference-v1
SOURCE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
SOURCE_BASELINE_ACTIVE = YES
SOURCE_BASELINE_READY = YES
FINAL_TRANSITION_DRY_RUN = PLAN / VALIDATED
FINAL_TRANSITION_DRY_RUN_STATUS = VALIDATED
TRANSITION_ACTIVATION_EXECUTED = YES
TRANSITION_ACTIVATION_RESULT = TRANSITION_ACTIVATED / ACTIVE
TRANSITION_TRANSACTIONAL = YES
TRANSITION_IDEMPOTENT = YES
NON_REFERENCE_WRITE_SET = []
TARGET_REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
TARGET_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
TARGET_REFERENCE_ACTIVE = YES
TARGET_REFERENCE_LOAD_STATUS = READY
ACTIVE_REGISTRY_COUNT = 1
SOURCE_REGISTRY_RETIRED = YES
SOURCE_PROVENANCE_PRESERVED = YES
TRANSITION_PROVENANCE_RECORDED = YES
MARKET_COUNT = 2
PHYSICAL_INSTRUMENT_COUNT = 507
MISSING_MARKETS = []
MISSING_INSTRUMENTS = []
DUPLICATE_IDENTITIES = []
MISSING_REFERENCE_CONTEXTS = []
REFERENCE_LIFECYCLE_ACTIVE = YES
REFERENCE_LIFECYCLE_ROW_COUNT = 1
REFERENCE_6806_LIFECYCLE_ACTIVE = YES
DATE_EFFECTIVE_RUN_DATE = 2026-08-13
DATE_EFFECTIVE_TPE_EXPECTED = 313
DATE_EFFECTIVE_TWO_EXPECTED = 193
TPE_6806_ELIGIBLE = NO
G1 = PASS
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PRODUCTION_MUTATION = YES (authorized reference registry transition only)
PRODUCTION_MARKET_DATA_MUTATION = NO
FINAL_STATUS = READY_FOR_G2_PRODUCTION_PREFLIGHT_AUTHORIZATION
BLOCKER = NONE

STOP. Do not begin G2 automatically.

# TASK-DATA-REF-006E Date-Effective Instrument Universe and G2 Lifecycle Eligibility Contract

## Fixed implementation fields

```text
TASK_DATA_REF_006E = READY_FOR_G2_DATE_EFFECTIVE_INTEGRATION_REVIEW
STARTING_ORIGIN_MAIN_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
BRANCH = codex/task-data-ref-006b-20260814
SOURCE_IMPLEMENTATION_SHA = d40fbfc44eaf5938ed70bab217dddc60fc76dc95
INTEGRATED_IMPLEMENTATION_SHA = 0ec5bcfe40ff9c64cb683f3de96fa79df4c8550c

ROOT_CAUSE_ADDRESSED = YES
INSTRUMENT_LIFECYCLE_DATA_MISSING = RESOLVED_IN_REFERENCE_CONTRACT
G2_DATE_EFFECTIVE_UNIVERSE_LOGIC_GAP = RESOLVED_IN_SHARED_ELIGIBILITY_PATH
EXISTING_LIFECYCLE_FIELDS = Instrument/Market is_active, valid_from, valid_to;
  SecurityIdentity valid_from, valid_to, resolution_status
CANONICAL_LIFECYCLE_SOURCE = committed tw-reference-v1 instrument_lifecycles.json,
  generated from approved status evidence
DATABASE_LIFECYCLE_SOURCE = topicpilot.reference_instrument_lifecycles,
  keyed by active reference registry and retained instrument identity
REFERENCE_LIFECYCLE_SOURCE = active registry lifecycle rows plus evidence_id/source_url
DATE_EFFECTIVE_FIELDS_AVAILABLE = YES
DATE_EFFECTIVE_UNIVERSE_IMPLEMENTED = YES
G2_EXPECTED_UNIVERSE_DATE_AWARE = YES
PROVIDER_PREFLIGHT_DATE_EFFECTIVE = YES
ELIGIBILITY_AUTHORITY = topicpilot_api.instrument_universe
ELIGIBILITY_IMPLEMENTATION_PATH =
  build_date_effective_instrument_universe -> is_instrument_eligible_on_date

DELISTING_BOUNDARY_SEMANTICS = effective_from is inclusive; latest applicable
  lifecycle event governs, terminal/suspended statuses fail eligibility closed
TPE_6806_2026_06_22 = ELIGIBLE
TPE_6806_2026_06_23 = NOT_ELIGIBLE
TPE_6806_2026_08_13 = NOT_ELIGIBLE
CANONICAL_2026_08_13_EXPECTED_TPE = 313
CANONICAL_2026_08_13_EXPECTED_TWO = 193
PHYSICAL_6806_ROW_REQUIRED_TO_DELETE = NO

MISSING_IDENTITY_CODES_OUTPUT = YES; sorted missingIdentityCodes
EXTRA_IDENTITY_CODES_OUTPUT = YES; sorted extraIdentityCodes
MALFORMED_LIFECYCLE_FAIL_CLOSED = YES; deterministic LifecycleValidationError
SCHEMA_CHANGE_REQUIRED = YES
MIGRATION_CREATED = YES; 0029_task_data_ref_006e_instrument_lifecycle
CANONICAL_BUNDLE_CHANGED = YES; lifecycle file and manifest digest updated
CANONICAL_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
CANONICAL_BUNDLE_LIFECYCLE_EVENT_COUNT = 1
6806_HARDCODED = NO
COVERAGE_THRESHOLD_LOWERED = NO
PROVIDER_LOGIC_CHANGED = NO
PROVIDER_AUTHORITY_PRESERVED = YES
TPE_PROVIDER = TWSE_OFFICIAL_DAILY / twse-official-daily.v2 / marketBatch=true
TWO_PROVIDER = TPEX_OFFICIAL_DAILY / tpex-official-daily.v2 / marketBatch=true
FALLBACK_CAN_PASS_G2 = NO

PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
G2_PRODUCTION_RETRIED = NO
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_MODIFIED = NO
FINAL_STATUS = READY_FOR_G2_DATE_EFFECTIVE_INTEGRATION_REVIEW
BLOCKER = NONE
NEXT_RECOMMENDED_TASK = TASK-DATA-REF-006F Production Date-Effective G2 Integration
```

## Implementation

The previous audit found that 6806 remained a retained physical identity with
delisting evidence, while G2 expected identities were selected solely by
`is_active=true`, `instrument_type=EQUITY`, and active market. This change
closes both sides of that gap without deleting the row or changing provider
mapping:

- Added `reference_instrument_lifecycles` in migration 0029. It is bound to a
  reference registry and an instrument, stores status/effective dates and
  evidence provenance, and rejects inverted effective ranges.
- Added `instrument_lifecycles.json` to the canonical bundle. It is generated
  from the approved evidence record, not from a 6806-specific code path.
- Added the lifecycle table to the reference-only bootstrap write set. The
  same transaction, idempotence, rollback, activation uniqueness, and
  non-reference write boundary remain in force.
- Added the provider-independent shared eligibility module. It validates
  instrument/market validity windows, lifecycle ranges, known lifecycle status
  semantics, duplicate identities, and expected-market topology. Unknown or
  malformed lifecycle metadata fails closed with a deterministic reason.
- G2 now loads lifecycle rows through SELECT-only ORM queries and computes the
  expected identities for the explicit run date. It emits sorted
  `missingIdentityCodes` and `extraIdentityCodes`; extra provider identities
  fail rather than being silently ignored.
- `topicpilot-reference-check` remains the formal active reference identity
  check and continues to report 507. Only G2 daily expected-universe coverage
  is date-effective.

The physical TPE 6806 row remains required. The 2026-08-13 expected daily
universe is 313 TPE and 193 TWO, derived from lifecycle evidence and the
database rows. No provider adapter, authority, fallback, persistence, or
downstream gate logic was changed.

## Validation evidence

Local disposable PostgreSQL validation upgraded to migration head, bootstrapped
the committed bundle, confirmed one lifecycle row and 507 physical instrument
rows, and loaded the 2026-08-13 G2 context as TPE 313 / TWO 193. Migration
downgrade and re-upgrade passed. The dedicated date-effective PostgreSQL
integration passed 1/1; the database was removed after completion.

Targeted unit/contract tests cover lifecycle boundaries, future validity,
malformed ranges and statuses, expected-universe grouping, missing/extra
provider identities, reference bundle validation, bootstrap write-set
boundaries, and provider authority/fallback regression behavior. Targeted
tests passed 23/23; the CI-equivalent backend passed 359/359 with 22
environment/database skips and 59 research/governance deselections. Ruff,
pip check, OpenAPI drift, generated API contract/idempotence, diff check, and
changed-file secret scan passed.

No Production runtime, Production database, Render deploy, provider preflight,
reference bootstrap, G2 retry, G3, Canary, Scheduler, push, NEXT_TASK, or Data
Governance HOLD action was performed by 006E.

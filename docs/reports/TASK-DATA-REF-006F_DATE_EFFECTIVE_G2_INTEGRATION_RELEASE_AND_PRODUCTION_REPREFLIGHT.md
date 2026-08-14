# TASK-DATA-REF-006F｜Date-Effective G2 Integration, Release, and Production Re-Preflight

**Date:** 2026-08-14
**Application runtime authority:** `121e66194238818f35f0167ddf280d5a6835de5e`
**Final status:** `BLOCKED_REFERENCE_BUNDLE_VERSION_AUTHORITY_AMBIGUOUS`

## Outcome

The corrected TASK-DATA-REF-006E implementation authority
`d40fbfc44eaf5938ed70bab217dddc60fc76dc95` was reconciled onto the clean,
unchanged `origin/main` baseline
`3366ee61ba71a4f98ad886b53284e3faedbf44e0`. The functional patch was
preserved exactly, the 006E append-only documentation was reconciled without
rewriting historical evidence, and the result was pushed by fast-forward only.

Exact-SHA CI and the protected deployment workflow passed. Production operator
evidence then proved that both `RENDER_GIT_COMMIT` and
`topicpilot-provider-lineage.buildSha` equal the integrated release SHA. The
provider lineage remains READY and unchanged.

Production migration 0029 is applied and the lifecycle table exists, but the
only ACTIVE `tw-reference-v1` registry still records the previously activated
bundle hash. It has zero lifecycle rows and no lifecycle evidence for
`TPE:6806`. The newly deployed canonical bundle retains the same reference
version with a different hash. Repository bootstrap governance treats this as
a version collision and stops before mutation. Therefore no reference
bootstrap/activation or G2 provider request was executed.

## Integration provenance

| Field | Evidence |
|---|---|
| Authorized pre-integration main | `3366ee61ba71a4f98ad886b53284e3faedbf44e0` |
| Corrected 006E implementation source | `d40fbfc44eaf5938ed70bab217dddc60fc76dc95` |
| 006E documentation source | `f9a3f82baec6910cd8f3e0076056f20f8d9a12d4` |
| Documentation parent matches implementation | YES |
| Integrated implementation commit | `0ec5bcfe40ff9c64cb683f3de96fa79df4c8550c` |
| Integrated main/application release | `121e66194238818f35f0167ddf280d5a6835de5e` |
| Source/integrated functional patch-id | `98803088c1c3a707d7faf52ce3ba6a058909c995` / exact match |
| Push | Non-force fast-forward |
| Migration collision | NO |
| Concurrent bundle conflict | NO |
| Concurrent main change | NO |

The 006E report was corrected to distinguish the actual source implementation
SHA from its clean-main integrated implementation SHA. No 006E behavior,
provider authority, coverage threshold, lifecycle rule, or physical identity
was changed during reconciliation.

## Validation and release evidence

- Focused lifecycle, bundle, provider-preflight, bootstrap, and PostgreSQL
  tests: `25 passed`.
- CI-equivalent backend boundary: `359 passed, 22 skipped, 59 deselected`.
- PostgreSQL empty migration upgrade, downgrade, and re-upgrade: PASS.
- Ruff, Python compile, pip check, OpenAPI drift, generated-contract
  idempotence, API-client tests, diff check, and local secret-pattern scan:
  PASS.
- Exact-SHA CI run `31762397487`: PASS for Backend/migration/OpenAPI,
  Frontend, Docker Compose smoke, and Gitleaks.
- Protected deploy workflow `31762561599`: PASS with
  `release_ref=121e66194238818f35f0167ddf280d5a6835de5e`, API deploy enabled,
  and web packaging skipped.
- Public `/healthz` and `/readyz`: healthy after deployment.

## Production runtime and G0

Operator evidence from one authenticated Render Production runtime reported:

- `RENDER_GIT_COMMIT = 121e66194238818f35f0167ddf280d5a6835de5e`;
- `topicpilot-provider-lineage.buildSha` equals the same SHA;
- lineage status is `READY`;
- TPE remains `TWSE_OFFICIAL_DAILY` / `twse-official-daily.v2`;
- TWO remains `TPEX_OFFICIAL_DAILY` / `tpex-official-daily.v2`;
- canonical daily providers remain market-batched;
- Yahoo remains verification-only and Taishin remains intraday-only.

Accordingly, runtime provenance and G0 passed without authority rebind.

## Migration, reference, and G1 evidence

The secret-safe SELECT-only operator audit reported the same database name for
the runtime and migration bindings, revision
`0029_task_data_ref_006e_instrument_lifecycle`, and table
`topicpilot.reference_instrument_lifecycles` on both bindings.

The fresh reference check returned:

- ACTIVE and READY `tw-reference-v1`;
- 2 markets and 507 physical/formal instruments;
- no missing markets or instruments;
- no duplicate identities or missing reference contexts;
- 24 calendar dates, 7 trading-status rows, and 3 adjustment rows.

This preserves G1. The physical `TPE:6806` identity remains present as required.

The active-registry audit returned:

- ACTIVE registry count for `tw-reference-v1`: 1;
- active registry bundle SHA:
  `5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`;
- deployed canonical bundle SHA:
  `daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295`;
- active lifecycle row count: 0;
- active `TPE:6806` lifecycle rows: none;
- physical instrument rows: 507.

## Fail-closed decision

The registry contract has a unique `reference_data_version`, while the
transactional loader raises `ReferenceBootstrapConflict` when that version
already exists with a different non-null bundle hash. The production runbook
also defines a version collision with a different bundle hash as a STOP
condition. The repository does not provide a reviewed same-version replacement,
registry rollover, or lifecycle-only activation procedure.

Consequently:

- the new lifecycle authority is not active;
- an activation attempt would be outside unambiguous repository authority;
- no bootstrap dry-run was treated as authorization to replace the registry;
- no `--activate`, manual SQL, active-registry edit, or lifecycle write was
  attempted;
- G2 was not run because its required active date-effective universe was not
  available.

The blocker is governance/versioning authority, not a migration failure, G1
regression, provider change, coverage-threshold issue, or a reason to delete
6806.

## Mutation boundary

Deployment startup applied the repository-authorized migration 0029. That
schema migration and Alembic revision advance are the only Production mutation
in 006F. All post-deploy database inspection was SELECT-only.

- Production reference-data mutation: NONE.
- Production market-data mutation: NONE.
- Reference bootstrap/activation: NOT RUN.
- Provider G2 request: NOT RUN.
- G3, Canary, and Scheduler: NOT RUN / unchanged.

## Fixed report

```text
TASK_DATA_REF_006F = BLOCKED_REFERENCE_BUNDLE_VERSION_AUTHORITY_AMBIGUOUS

CURRENT_ORIGIN_MAIN_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
006E_IMPLEMENTATION_SHA = d40fbfc44eaf5938ed70bab217dddc60fc76dc95
006E_DOCUMENTATION_SHA = f9a3f82baec6910cd8f3e0076056f20f8d9a12d4
DOCUMENTATION_PARENT_MATCHES_ACTUAL_IMPLEMENTATION = YES

MIGRATION_COLLISION = NO
CANONICAL_BUNDLE_CONFLICT = NO
CONCURRENT_MAIN_CHANGE = NO
RECONCILIATION_RESULT = PASS

INTEGRATED_IMPLEMENTATION_SHA = 0ec5bcfe40ff9c64cb683f3de96fa79df4c8550c
INTEGRATED_MAIN_SHA = 121e66194238818f35f0167ddf280d5a6835de5e
APPLICATION_RUNTIME_AUTHORITY_SHA = 121e66194238818f35f0167ddf280d5a6835de5e
NON_FORCE_PUSH = YES

EXACT_SHA_CI_RUN = 31762397487
EXACT_SHA_CI = PASS

DEPLOY_WORKFLOW_RUN = 31762561599
DEPLOY_RESULT = PASS

RUNTIME_GIT_COMMIT = 121e66194238818f35f0167ddf280d5a6835de5e
PROVIDER_LINEAGE_BUILD_SHA = 121e66194238818f35f0167ddf280d5a6835de5e
RUNTIME_SHA_VERIFIED = YES
G0 = PASS

MIGRATION_0029_PRODUCTION_STATE = APPLIED_HEAD

CANONICAL_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
ACTIVE_REFERENCE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
ACTIVE_REFERENCE_BUNDLE_COMPATIBLE = NO
REFERENCE_LIFECYCLE_ACTIVE = NO
REFERENCE_LIFECYCLE_ROW_COUNT = 0
REFERENCE_6806_LIFECYCLE_ACTIVE = NO

G1_REFERENCE_ACTIVE = YES
G1_REFERENCE_LOAD_STATUS = READY
G1_MARKET_COUNT = 2
G1_INSTRUMENT_COUNT = 507
G1_MISSING_MARKETS = []
G1_MISSING_INSTRUMENTS = []
G1_DUPLICATE_IDENTITIES = []
G1 = PASS

AUTHORIZED_G2_RUN_DATE = 2026-08-13
G2_TPE_EXPECTED = 313_CANONICAL_NOT_EXECUTED
G2_TPE_PROVIDER_COUNT = NOT_RUN
G2_TPE_MISSING_IDENTITY_CODES = NOT_RUN
G2_TPE_EXTRA_IDENTITY_CODES = NOT_RUN

G2_TWO_EXPECTED = 193_CANONICAL_NOT_EXECUTED
G2_TWO_PROVIDER_COUNT = NOT_RUN
G2_TWO_MISSING_IDENTITY_CODES = NOT_RUN
G2_TWO_EXTRA_IDENTITY_CODES = NOT_RUN

TPE_PROVIDER = TWSE_OFFICIAL_DAILY
TPE_PROVIDER_VERSION = twse-official-daily.v2
TWO_PROVIDER = TPEX_OFFICIAL_DAILY
TWO_PROVIDER_VERSION = tpex-official-daily.v2

FALLBACK_USED = NOT_APPLICABLE_G2_NOT_RUN
FALLBACK_CAN_PASS_G2 = NO
G2 = NOT_RUN_FAIL_CLOSED

PRODUCTION_DB_CONNECTED = YES_SELECT_ONLY_POST_DEPLOY_AUDIT
PRODUCTION_MUTATION = MIGRATION_0029_ONLY
PRODUCTION_REFERENCE_DATA_MUTATION = NO
PRODUCTION_MARKET_DATA_MUTATION = NO
REFERENCE_BOOTSTRAP = NOT_RUN
REFERENCE_ACTIVATION = NOT_RUN

G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO

DOCUMENTATION_SHA = LOCAL_CLOSURE_COMMIT_REPORTED_IN_FINAL_HANDOFF
DOCUMENTATION_PUSH = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO

NEXT_RECOMMENDED_TASK = NONE_UNTIL_REFERENCE_VERSION_AUTHORITY_IS_RESOLVED
FINAL_STATUS = BLOCKED_REFERENCE_BUNDLE_VERSION_AUTHORITY_AMBIGUOUS
BLOCKER = ACTIVE_TW_REFERENCE_V1_USES_OLD_BUNDLE_HASH_AND_REPOSITORY_HAS_NO_AUTHORIZED_SAME_VERSION_REPLACEMENT_PATH
```

STOP. Do not start TASK-DATA-REF-007 or G3 until a separately reviewed
reference-version/registry transition contract resolves this blocker.

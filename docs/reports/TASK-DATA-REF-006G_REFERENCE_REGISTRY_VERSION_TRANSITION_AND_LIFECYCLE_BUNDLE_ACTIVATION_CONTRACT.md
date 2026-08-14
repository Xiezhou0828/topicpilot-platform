# TASK-DATA-REF-006G｜Reference Registry Version Transition and Lifecycle Bundle Activation Contract

**Date:** 2026-08-14
**Final status:** `READY_FOR_REFERENCE_REGISTRY_TRANSITION_INTEGRATION_REVIEW`

## Scope and outcome

TASK-DATA-REF-006G resolves the TASK-DATA-REF-006F blocker
`BLOCKED_REFERENCE_BUNDLE_VERSION_AUTHORITY_AMBIGUOUS` as a repository
contract. It does not run Production, change the active Production registry,
deploy, push, run G2, or start G3.

The new contract makes `reference_data_version` immutable. An existing ACTIVE
version with a different bundle hash cannot be overwritten. A reviewed bundle
rollover instead derives a new registry version from the source version and
the first 16 lowercase hexadecimal characters of the full bundle SHA-256:

```text
<source-version>-rollover-<bundle-sha256[:16]>
```

For the current lifecycle-bearing canonical bundle:

```text
SOURCE_REFERENCE_VERSION = tw-reference-v1
OLD_ACTIVE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
CANONICAL_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
TRANSITION_TARGET_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
```

The complete old and new hashes, registry IDs, versions, and transition kind
are preserved in `reference_registry_transitions`. The old registry and all
of its reference rows remain historical provenance; no overwrite or delete is
used.

## Repository implementation

Implementation commit:

```text
be976963c1c6fc3b040390c3d7e6687322c365d0
```

Implemented components:

- migration `0030_task_data_ref_006g_registry_transition`;
- ORM model `ReferenceRegistryTransition` with immutable from/to provenance,
  full bundle hashes, distinct-set constraint, and one-target constraint;
- `transition_reference_registry` atomic service;
- deterministic `derive_transition_version` policy;
- explicit CLI `topicpilot-reference-transition` with required source version,
  expected source bundle hash, bundle directory, and mutually exclusive
  `--dry-run` / `--activate` modes;
- transaction-safe bootstrap composition so the target bundle write and
  retire/activate/provenance operations share one transaction;
- architecture freeze and migration-head tests updated for the new
  reference-only table;
- operator runbook and documentation index entry.

## Transition contract

The exact operator path is documented in
`docs/operations/reference-registry-transition.md`.

`--dry-run` validates the source ACTIVE registry, exact old hash, bundle
identity/catalogue/calendar/lifecycle state, derived target version, and
reference-only write set without mutation.

`--activate` owns one transaction that:

1. locks and revalidates the ACTIVE source and expected old bundle hash;
2. creates or reconciles the derived target registry and all reference rows;
3. validates the complete target state, including lifecycle evidence;
4. retires the previous ACTIVE registry;
5. promotes the validated target to ACTIVE;
6. records one immutable transition provenance row.

The existing partial unique ACTIVE index guarantees one ACTIVE registry. Any
failure rolls back target rows, retirement, activation, and transition
provenance together. Rerunning an already completed transition returns
`operation=NOOP` after validating the target and provenance.

The transition write set is strictly:

```text
markets
instruments
reference_registry_sets
reference_registry_transitions
reference_currencies
reference_timezones
reference_sessions
reference_trading_statuses
reference_adjustments
reference_calendar_dates
reference_instrument_lifecycles
```

```text
NON_REFERENCE_WRITE_SET = []
```

Topics, relations, raw/timeline/canonical observations, Lifecycle,
Opportunity, audit tables, and Scheduler state are not imported or written.

## Governance answers

```text
REFERENCE_VERSION_IMMUTABLE = YES
SAME_VERSION_DIFFERENT_HASH_ALLOWED = NO
REGISTRY_ROLLOVER_SUPPORTED_TODAY = YES
REGISTRY_RETIREMENT_SUPPORTED_TODAY = YES
ATOMIC_ACTIVATION_SUPPORTED_TODAY = YES
MULTIPLE_ACTIVE_REGISTRY_PREVENTED = YES
REFERENCE_VERSION_NAMING_POLICY = <source>-rollover-<bundle_sha256[:16]>
FULL_BUNDLE_HASH_PRESERVED = YES
OLD_REFERENCE_PROVENANCE_PRESERVED = YES
LIFECYCLE_ROWS_BOUND_TO_REGISTRY = YES
PROVIDER_PREFLIGHT_USES_ACTIVE_REGISTRY = YES
REFERENCE_CHECK_USES_ACTIVE_REGISTRY = YES
ROLLBACK_ON_ACTIVATION_FAILURE = PASS
PARTIAL_REFERENCE_ACTIVATION_POSSIBLE = NO
SAME_VERSION_HASH_OVERWRITE = NO
```

The existing ordinary bootstrap remains the correct path for a new version
whose manifest version is already unique. The transition path is required for
the current same-source-version/different-hash case and never mutates the old
hash.

## Disposable PostgreSQL evidence

The disposable PostgreSQL database was migrated through 0030 and tested with
an old ACTIVE `tw-reference-v1` registry carrying the reviewed old bundle
hash, physical identity creation, and the new lifecycle-bearing bundle.

Evidence passed:

- transition dry-run returned a PLAN and left the registry/identity state
  unchanged;
- same-version hash overwrite was rejected;
- atomic activation created the derived target registry and one transition
  provenance row;
- old registry became RETIRED and remained queryable;
- exactly one registry remained ACTIVE;
- 507 physical instruments were preserved;
- one lifecycle row for `TPE:6806` was bound to the target registry;
- target reference-check was ACTIVE/READY with 2 markets and 507 identities;
- date-effective 2026-08-13 universe was TPE 313 and TWO 193;
- second exact transition execution returned NOOP;
- injected market-context failure rolled back target creation, retirement,
  activation, and transition provenance;
- non-reference table counts were unchanged.

## Validation

- Targeted transition PostgreSQL tests: `3 passed`.
- Full backend CI-equivalent suite: `360 passed, 24 skipped, 59 deselected`;
  one pre-existing SQLAlchemy transaction warning remained.
- Ruff: PASS.
- Python 3.12 compile: PASS.
- PostgreSQL migration upgrade, downgrade, and re-upgrade: PASS.
- `pip check`: PASS.
- New CLI help and mutually exclusive mode surface: PASS.
- Diff check and changed-file secret scan: PASS.

Research and governance tests remained excluded by the existing CI boundary;
no research/governance behavior was changed.

## Production boundary

```text
APPLICATION_RUNTIME_AUTHORITY_SHA = 121e66194238818f35f0167ddf280d5a6835de5e
PRODUCTION_DB_CONNECTED = NO
PRODUCTION_MUTATION = NO
REFERENCE_BOOTSTRAP = NOT_RUN
REFERENCE_ACTIVATION = NOT_RUN
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
```

The 006F Production state and its old ACTIVE registry were not retried or
modified. A future Production execution requires separate runtime authority,
transition dry-run evidence, one-shot activation authorization, target-version
reference-check, and then a separately authorized G2 re-preflight.

## Fixed report

```text
TASK_DATA_REF_006G = READY_FOR_REFERENCE_REGISTRY_TRANSITION_INTEGRATION_REVIEW
IMPLEMENTATION_COMMIT_SHA = be976963c1c6fc3b040390c3d7e6687322c365d0

REFERENCE_TRANSITION_CONTRACT = IMPLEMENTED
REFERENCE_VERSION_AUTHORITY = UNAMBIGUOUS
OLD_REGISTRY_PROVENANCE_PRESERVED = YES
SAME_VERSION_HASH_OVERWRITE = NO
ATOMIC_ACTIVATION = YES
ROLLBACK_ON_FAILURE = PASS
SINGLE_ACTIVE_REGISTRY = GUARANTEED
LIFECYCLE_ACTIVATION_SUPPORTED = YES
TPE_6806_PHYSICAL_IDENTITY_PRESERVED = YES
DATE_EFFECTIVE_2026_08_13_TPE = 313
DATE_EFFECTIVE_2026_08_13_TWO = 193

SOURCE_REFERENCE_VERSION = tw-reference-v1
OLD_ACTIVE_BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
CANONICAL_BUNDLE_SHA256 = daf19e9eb051255c631d0fff6d8fecf1273aecf52f9e958a62c778dfb6906295
TRANSITION_TARGET_VERSION = tw-reference-v1-rollover-daf19e9eb051255c

PRODUCTION_MUTATION = NO
PRODUCTION_DB_CONNECTED = NO
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PUSH = NO
MERGE_MAIN = NO
DEPLOY = NO

DOCUMENTATION_PUSH = NO
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
FINAL_STATUS = READY_FOR_REFERENCE_REGISTRY_TRANSITION_INTEGRATION_REVIEW
BLOCKER = NONE
NEXT_RECOMMENDED_TASK = TASK-DATA-REF-006G_INTEGRATION_REVIEW
```

STOP. This task establishes the contract only. Do not execute the Production
transition or begin G2/G3 from this task.

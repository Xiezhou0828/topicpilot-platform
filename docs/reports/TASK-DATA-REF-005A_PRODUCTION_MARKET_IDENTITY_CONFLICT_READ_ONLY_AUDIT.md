# TASK-DATA-REF-005A — Production Market Identity Conflict Read-Only Audit

## Final status

`READY_FOR_MARKET_IDENTITY_REMEDIATION_REVIEW`

TASK-DATA-REF-005A audits the single blocked activation attempt from
TASK-DATA-REF-005. It does not authorize a retry, repair, or any additional
Production mutation. The conflict is reproducible from the exact-SHA
repository contract and the supplied Production read-only evidence.

## Scope and safety boundary

The only Production evidence accepted for this audit is read-only market
diagnostic output, the blocked bootstrap result, and the SELECT-only reference
check after the failure. No `INSERT`, `UPDATE`, `DELETE`, migration, seed,
manual SQL repair, bundle regeneration, provider change, daily observation
write, G2/G3, Canary #2, or Scheduler action was performed by this audit.

## Fixed release and pre-attempt evidence

```text
TASK_DATA_REF_005A = YES
RELEASE_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
RUNTIME_SHA_VERIFIED = YES (operator evidence)
G0 = PASS (operator evidence)
REFERENCE_VERSION = tw-reference-v1
BUNDLE_SHA256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6
BUNDLE_HASH_MATCH = PASS
PRODUCTION_BUNDLE_DRIFT = NO
DATA_REF_004_DRY_RUN = PASS / PLAN / VALIDATED
DRY_RUN_MUTATION = NO
DRY_RUN_DB_STATE_CHANGED = NO
PRODUCTION_BOOTSTRAP_AUTHORIZED = YES (TASK-DATA-REF-005 scope)
BOOTSTRAP_COMMAND_ATTEMPTED = YES (one attempt)
```

The final pre-attempt Production baseline was:

| Field | Result |
| --- | --- |
| `REFERENCE_ACTIVE` | `NO` |
| `MARKET_COUNT` | `2` |
| `INSTRUMENT_COUNT` | `0` |
| `DUPLICATE_IDENTITIES` | `[]` |
| `MISSING_INSTRUMENTS` | `PRESENT` |
| `REFERENCE_LOAD_STATUS` | `NOT_READY` |

## Blocked activation and post-failure evidence

The single authorized command was:

```console
topicpilot-reference-bootstrap \
  --bundle-dir /app/src/topicpilot_api/reference_data/bundles/tw-reference-v1 \
  --activate
```

The secret-safe result was:

```json
{"status":"BLOCKED","error":"bundle/database conflict in market TPE name"}
```

The immediate SELECT-only post-failure check remained:

```text
MARKET_COUNT = 2
INSTRUMENT_COUNT = 0
DUPLICATE_IDENTITIES = []
MISSING_INSTRUMENTS = PRESENT
REFERENCE_ACTIVE = NO
REFERENCE_LOAD_STATUS = NOT_READY
BOOTSTRAP_MUTATION_OCCURRED = NO
ROLLBACK_REQUIRED = NO
PARTIAL_STATE_LEFT = NO
```

This is a blocked bootstrap attempt, not a successful bootstrap. The
Production reference registry remains absent/inactive and G1 is therefore
not reached.

## Canonical bundle identity

The exact-SHA bundle contains:

| Market | Bundle code | Bundle name | Bundle exchange code |
| --- | --- | --- | --- |
| TPE | `TPE` | `TWSE Listed` | `TWSE` |
| TWO | `TWO` | `TPEx OTC` | `TPEx` |

The bundle is at:

`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/`

Its manifest is exact-SHA validated with:

`bundleSha256 = 5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6`

The repository-derived market identity definitions are in
`services/api/src/topicpilot_api/reference_data/bundle.py:36-50`. The same
TPE/TWO defaults are repeated by the current exact-SHA live identity helper
at `services/api/src/topicpilot_api/live/bootstrap.py:203-226`.

## Production market identity evidence

The read-only Production market diagnostic reports:

| Market | Production code | Production name | Production exchange code | Active |
| --- | --- | --- | --- | --- |
| TPE | `TPE` | `Taiwan Stock Exchange` | `TPE` | `true` |
| TWO | `TWO` | `Taipei Exchange` | `TWO` | `true` |

Comparison:

| Market | Name comparison | Exchange-code comparison | Conflict |
| --- | --- | --- | --- |
| TPE | `TWSE Listed` ≠ `Taiwan Stock Exchange` | `TWSE` ≠ `TPE` | YES |
| TWO | `TPEx OTC` ≠ `Taipei Exchange` | `TPEx` ≠ `TWO` | YES |

The observed error names TPE because the bootstrap iterates the bundle's
market rows in order and fails at the first conflicting field. It does not
prove that TWO would be accepted; the read-only comparison independently
shows that TWO also conflicts.

## Conflict-path code audit

The exact-SHA repository path is:

`services/api/src/topicpilot_api/reference_data/bootstrap.py`

Relevant behavior:

1. `_ensure_market()` looks up by stable market code.
2. For an existing market, `_check_same()` compares the bundle name exactly
   with `market.name` and then the bundle exchange code exactly with
   `market.exchange_code` (`bootstrap.py:108-123`). There is no trim,
   case-fold, alias table, or display-name normalization.
3. A mismatch raises `ReferenceBootstrapConflict` with the field-specific
   message, which explains `bundle/database conflict in market TPE name`.
4. The activation function owns one `with session.begin()` transaction
   (`bootstrap.py:327-350`). It creates/flushes a provisional registry row
   before iterating market rows (`bootstrap.py:360-379`), but the conflict
   exception aborts the transaction. Existing market identity fields are not
   assigned before the checks, and no reference rows or instruments are
   reached on the first TPE conflict.
5. The CLI catches `ReferenceBootstrapConflict`, emits a secret-safe BLOCKED
   result, and exits without a commit. The Production post-failure
   SELECT-only evidence confirms that the provisional transaction left no
   persisted registry or identity state.

The important distinction is that the conflict check precedes mutation of the
conflicting market row, while the transaction may contain a provisional
registry INSERT that is rolled back. Therefore the correct conclusion is
`BOOTSTRAP_MUTATION_OCCURRED=NO` at the durable Production state boundary,
not that no SQL statement was ever flushed inside the failed transaction.

## Repository tests and write boundary

Local exact-SHA targeted tests passed:

```text
tests/test_reference_bundle.py
tests/test_reference_bootstrap_contract.py
5 passed in 1.30s
```

The PostgreSQL integration test is present at
`services/api/tests/test_reference_bootstrap_postgres.py`; it includes a
conflicting-market rollback case (`:146-153`) and asserts the registry count
after the failed activation. It was not run in this audit because no
`TEST_DATABASE_URL` was configured; the ordinary `DATABASE_URL` was not used
and no Production credential was read.

The declared reference write set is exactly:

- `reference_registry_sets`
- `reference_currencies`
- `reference_timezones`
- `reference_sessions`
- `reference_trading_statuses`
- `reference_adjustments`
- `reference_calendar_dates`
- `markets`
- `instruments`

`NON_REFERENCE_WRITE_SET = NONE` in the repository contract. No actual
non-reference write occurred.

## Authority and provenance decision

`CANONICAL_NAMING_AUTHORITY` is the approved `tw-reference-v1` bundle at the
exact release SHA, interpreted with the provider registry and current identity
bootstrap defaults named by the bundle manifest. The Production market rows
are existing-state conflict evidence, not an authority override.

`EXISTING_MARKETS_PROVENANCE` is not conclusively persisted in the market row
itself. The observed names match the earlier legacy identity convention, but
this audit does not claim a definitive historical seed path without a
Production lineage record. The provenance is therefore recorded as
`LEGACY_CONVENTION_MATCH / EXACT_SEED_PATH_NOT_PROVEN`.

`ROOT_CAUSE_CLASS = PRODUCTION_LEGACY_NAME_DRIFT`.

This classification includes exchange-code drift, not only display-name drift.
It is not classified as a canonical bundle error because the bundle hash,
market definitions, and current exact-SHA identity defaults agree locally.
It is not classified as normalization-too-strict because the two sides use
different exchange-code identities as well as different names.

## Remediation boundary

Recommended next step is a separate market-identity remediation review that
must decide, from approved authority, whether:

- the canonical bundle's market names/exchange codes are correct and
  Production identity rows require an explicitly governed migration; or
- the existing Production naming convention is the approved authority and a
  new reviewed bundle/version must be generated with updated source/governance
  evidence.

No manual UPDATE/DELETE/INSERT, no direct SQL repair, no bundle regeneration,
and no bootstrap retry is authorized by TASK-DATA-REF-005A. After an approved
remediation, rerun the dry-run and require a fresh review before activation.

## Fixed final fields

```text
TASK_DATA_REF_005A = YES
RELEASE_SHA = a5fba9319a177a5da9fb8123b265ed05e7ff9f6c
BUNDLE_TPE_CODE = TPE
BUNDLE_TPE_NAME = TWSE Listed
BUNDLE_TPE_EXCHANGE_CODE = TWSE
BUNDLE_TWO_CODE = TWO
BUNDLE_TWO_NAME = TPEx OTC
BUNDLE_TWO_EXCHANGE_CODE = TPEx
PRODUCTION_TPE_CODE = TPE
PRODUCTION_TPE_NAME = Taiwan Stock Exchange
PRODUCTION_TPE_EXCHANGE_CODE = TPE
PRODUCTION_TWO_CODE = TWO
PRODUCTION_TWO_NAME = Taipei Exchange
PRODUCTION_TWO_EXCHANGE_CODE = TWO
TPE_CONFLICT = NAME_AND_EXCHANGE_CODE
TWO_CONFLICT = NAME_AND_EXCHANGE_CODE
CONFLICT_CODE_PATH = services/api/src/topicpilot_api/reference_data/bootstrap.py:108-123
CONFLICT_COMPARISON = exact equality; no normalization or alias mapping
NORMALIZATION_BEHAVIOR = NONE
CONFLICT_BEFORE_MUTATION = YES for conflicting market identity fields; provisional registry flush rolled back
BOOTSTRAP_MUTATION_OCCURRED = NO (durable Production state)
ROLLBACK_REQUIRED = NO
PARTIAL_STATE_LEFT = NO
EXISTING_MARKETS_PROVENANCE = LEGACY_CONVENTION_MATCH / EXACT_SEED_PATH_NOT_PROVEN
CANONICAL_NAMING_AUTHORITY = exact-SHA tw-reference-v1 bundle plus provider/identity defaults
ROOT_CAUSE_CLASS = PRODUCTION_LEGACY_NAME_DRIFT
RECOMMENDED_REMEDIATION = separate governed market-identity remediation review; no repair/retry here
PRODUCTION_MUTATION_THIS_TASK = NO
BOOTSTRAP_RETRY = NO
G1 = NOT_REACHED (effective gate FAIL)
G2 = NOT_RUN
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
AI_WORKLOG_UPDATED = YES (append-only)
NEXT_TASK_MODIFIED = NO
DATA_GOVERNANCE_HOLD_TOUCHED = NO
FINAL_STATUS = READY_FOR_MARKET_IDENTITY_REMEDIATION_REVIEW
BLOCKER = Existing Production TPE/TWO market identity fields conflict with the approved bundle; authority decision and governed remediation are pending.
```

Stop here. Do not retry TASK-DATA-REF-005 activation until the market identity
conflict has a separately approved remediation decision.

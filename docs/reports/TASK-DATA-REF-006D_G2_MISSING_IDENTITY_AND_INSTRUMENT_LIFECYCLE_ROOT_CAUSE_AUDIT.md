# TASK-DATA-REF-006D G2 Missing Identity and Instrument Lifecycle Root-Cause Audit

## Fixed audit fields

```text
TASK-DATA-REF-006D = AUDIT_COMPLETE_READY_FOR_006E
APPLICATION_RUNTIME_SHA = 3366ee61ba71a4f98ad886b53284e3faedbf44e0
G0 = PASS
G1 = PASS
REFERENCE_ACTIVE = YES
REFERENCE_LOAD_STATUS = READY
MARKET_COUNT = 2
INSTRUMENT_COUNT = 507
TPE_COUNT = 314
TWO_COUNT = 193

AUTHORIZED_G2_RUN_DATE = 2026-08-13
TPE_MISSING_IDENTITY_CODES = [TPE:6806]
MISSING_IDENTITY_CONFIRMED = YES (reconciled from repository and prior
  official row-level evidence; the 006C aggregate JSON emitted count=1 but
  did not emit the code)
EXPECTED_TPE_COUNT = 314
PROVIDER_TPE_COUNT = 313 covered expected identities
MISSING_IDENTITY_IN_CANONICAL_BUNDLE = NO
MISSING_IDENTITY_IN_DATABASE = NO (identity retained; absent from provider
  daily response)

ROOT_CAUSE = Canonical/reference identity retention includes TPE:6806 after
  its evidenced 2026-06-23 delisting, while G2 derives a date-blind active
  EQUITY expected universe and does not apply lifecycle validity to the
  authorized run date. The official provider no-row is therefore expected
  delisting/no-trade evidence, not a provider mapping failure.
ROOT_CAUSE_CLASS = [INSTRUMENT_LIFECYCLE_DATA_MISSING,
  G2_DATE_EFFECTIVE_UNIVERSE_LOGIC_GAP]
PROVIDER_IDENTITY_MAPPING_ERROR = NO
PROVIDER_DATA_OMISSION = NO
REFERENCE_DATA_ERROR = NO

INSTRUMENT_LIFECYCLE_SUPPORTED = PARTIAL
LIFECYCLE_FIELDS = Instrument.is_active, valid_from, valid_to; Market.is_active,
  valid_from, valid_to; SecurityIdentity.valid_from, valid_to,
  resolution_status; canonical trading-status status_code, status_reason,
  status_context
DATE_EFFECTIVE_UNIVERSE_SUPPORTED = NO (operationally; nullable validity
  columns exist but are not populated/used by G2 eligibility)
PROVIDER_PREFLIGHT_DATE_EFFECTIVE = NO
G2_EXPECTED_UNIVERSE_SOURCE = Production DB SELECT of active EQUITY Instrument
  rows joined to active TPE/TWO Market rows
G2_EXPECTED_UNIVERSE_DATE_AWARE = NO

DELETE_REQUIRED = NO
SCHEMA_CHANGE_REQUIRED = UNDETERMINED (existing validity columns can support
  a minimum date-effective fix; persisted lifecycle/status governance may
  require a separately reviewed schema/data contract)
DATA_REMEDIATION_REQUIRED = YES
PROVIDER_LOGIC_CHANGE_REQUIRED = NO
CLI_MISSING_IDENTITY_OBSERVABILITY_GAP = YES

PRODUCTION_DB_CONNECTED = YES (operator preflight SELECT-only path)
PRODUCTION_MUTATION = NO
G2_RETRIED = NO
G3 = NOT_RUN
CANARY_2 = NOT_RUN
SCHEDULER_CHANGED = NO
PUSH = NO
DEPLOY = NO
NEXT_RECOMMENDED_TASK = TASK-DATA-REF-006E Instrument Lifecycle / Date-Effective
  Universe Contract
FINAL_STATUS = AUDIT_COMPLETE_READY_FOR_006E
BLOCKER = NONE for the audit; G2 remains failed until a separately reviewed
  006E contract resolves date-effective eligibility and approved no-trade
  semantics.
```

## Evidence chain

### Exact missing identity

The committed canonical bundle contains 314 TPE instruments and includes
`instrument_code=6806` in
`services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1/instruments.json`.
Its `evidence.json` record contains:

```text
market = TPE
status = DELISTED
effectiveFrom = 2026-06-23
evidenceId = TWSE-DELISTED-6806-20260623
```

The 006C Production G2 result reported TPE coverage `313/314`,
`missingInstrumentCount=1`, and `PARTIAL_PROVIDER_COVERAGE`. The CLI does not
emit missing identity codes. The repository's prior official row-level
diagnostic independently resolved the absent TWSE symbol as `TPE:6806` and
classified it as an explicit official no-row result. This reconciles the 006C
count to `TPE:6806` without claiming that the 006C aggregate JSON contained
the code. No new provider request was made by this audit.

```text
expected TPE identity count = 314
official covered expected identities = 313
missing expected identity = TPE:6806
extra provider identities = NOT_EMITTED_BY_006C_CLI
```

### Root cause

The canonical bundle intentionally retains 6806 as a formal identity and the
architecture/runbook require identity retention with nullable price and
explicit no-trade evidence. The official-provider diagnostic records 6806 as
having no TWSE row and uses `EXCHANGE_CONFIRMED_NO_DATA`; it does not fabricate
a bar or substitute Yahoo/Taishin. This is consistent with the committed
delisting evidence effective before `2026-08-13`.

The mismatch is therefore between a retained historical/formal identity and
the daily date-effective provider universe. It is not a provider mapping error
and does not justify deleting 6806.

### Instrument lifecycle model audit

The ORM and migration contain lifecycle-shaped fields: `Instrument` and
`Market` have nullable `valid_from`, `valid_to`, and `is_active`; security
identities have required `valid_from`, nullable `valid_to`, and
`resolution_status`. Canonical trading-status observations separately carry
`status_code`, `status_reason`, and `status_context`.

This is only partial lifecycle capability. Bundle instrument rows contain
identity/name/type/currency but no effective dates or per-instrument listing
status. Bootstrap creates or reactivates an instrument with `is_active=True`
and does not populate validity dates or bind 6806 status evidence to the
instrument row.

### G2 expected-universe audit

`provider_preflight.load_g2_preflight_context` derives expected identity codes
through SELECT-only ORM queries. The eligibility predicates are exactly:

```text
Instrument.is_active = true
Instrument.instrument_type = 'EQUITY'
Market.is_active = true
Market.code in ('TPE', 'TWO')
```

The query does not predicate on `Instrument.valid_from`, `Instrument.valid_to`,
`Market.valid_from`, `Market.valid_to`, security-identity validity, or an
instrument-level status/evidence row. The `--run-date` is used for calendar
session validation and provider response date matching, but not for expected
identity eligibility. Therefore `G2_EXPECTED_UNIVERSE_DATE_AWARE=NO`.

`reference-check` has the same active-only identity shape and documents that
its count is formal active EQUITY identity count, not daily provider coverage.
The two checks are separate contracts; the missing contract is the bridge from
retained identity to date-effective daily expected universe.

### CLI observability gap

The G2 evaluator computes the set intersection internally and emits only
`expectedInstrumentCount`, `coveredInstrumentCount`, `missingInstrumentCount`,
and `coverageComplete`. It does not serialize
`expected_codes - provider_codes` or `provider_codes - expected_codes`.
This is a secret-safe but material auditability gap. 006E should add
deterministic `missingIdentityCodes` and `extraIdentityCodes`, with an
explicit output-size policy, without allowing partial coverage to PASS.

## Scope and stop conditions

This audit made no Production request, retry, mutation, deletion, update,
bootstrap, activation, calendar remediation, provider fallback, deployment,
G3, Canary, or Scheduler change. It did not modify the canonical bundle,
migrations, `NEXT_TASK`, or Data Governance HOLD. The next task is limited to
the instrument lifecycle/date-effective universe contract and its tests;
implementation is not part of 006D.

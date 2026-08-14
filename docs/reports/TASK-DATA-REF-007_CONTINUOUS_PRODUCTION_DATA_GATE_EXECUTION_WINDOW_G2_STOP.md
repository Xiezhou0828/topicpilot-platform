# TASK-DATA-REF-007｜Continuous Production Data-Gate Execution Window

## Scope and stop decision

This report records the operator evidence for the authorized continuous
Production data-gate window. The window stopped at G2 because both official
market payloads contained identities outside the date-effective target
reference universe. No retry, date substitution, fallback, remediation,
post-close persistence, G3, Canary, or Scheduler action was performed.

The evidence was captured in the authenticated Render runtime using the
repository-authoritative command:

```console
topicpilot-provider-preflight \\
  --run-date 2026-08-13 \\
  --reference-version tw-reference-v1-rollover-daf19e9eb051255c
```

## Runtime and preserved G1 authority

The runtime SHA and provider lineage were verified immediately before G2:

- Application runtime SHA: `eb50d2d1e242290e2b9c6c95389bd7cd257caf26`
- `topicpilot-provider-lineage.buildSha`: the same SHA
- Provider lineage status: `READY`
- TPE: `TWSE_OFFICIAL_DAILY / twse-official-daily.v2`, `marketBatch=true`
- TWO: `TPEX_OFFICIAL_DAILY / tpex-official-daily.v2`, `marketBatch=true`
- Reference version: `tw-reference-v1-rollover-daf19e9eb051255c`
- Preserved G1: ACTIVE/READY, 2 markets, 507 physical identities, complete
  reference context, no missing or duplicate formal identities
- Date-effective universe for `2026-08-13`: TPE 313, TWO 193; TPE:6806 is not
  eligible under the active lifecycle evidence

## G2 result

The target date was a valid session (`targetDateIsSession=true`) and both
official providers were reachable, parsed, and matched the target date. The
gate nevertheless failed because the strict result contract rejects extra
provider identities even when all date-effective expected identities are
covered.

| Market | Authority / adapter | Expected | Covered | Missing | Extra | Result |
|---|---|---:|---:|---:|---:|---|
| TPE | `TWSE_OFFICIAL_DAILY / twse-official-daily.v2` | 313 | 313 | 0 | 1,065 | FAIL |
| TWO | `TPEX_OFFICIAL_DAILY / tpex-official-daily.v2` | 193 | 193 | 0 | 10,281 | FAIL |

The raw operator JSON contains the complete `extraIdentityCodes` arrays. The
reported sanitized metrics are:

- TPE: `coverageComplete=false`, `errorCode=EXTRA_PROVIDER_IDENTITIES`,
  `recordCount=1378`, `missingInstrumentCount=0`,
  `extraInstrumentCount=1065`
- TWO: `coverageComplete=false`, `errorCode=EXTRA_PROVIDER_IDENTITIES`,
  `recordCount=10474`, `missingInstrumentCount=0`,
  `extraInstrumentCount=10281`

Global read-only contract evidence:

```text
gate = G2
status = FAIL
targetDate = 2026-08-13
targetDateIsSession = true
readOnly = true
fallbackAllowed = false
productionWriteSet = []
nonReferenceWriteSet = []
```

The failure is not a missing-coverage failure and is not evidence that the
reference registry is incomplete. It is a strict provider identity-set
compatibility failure: the official market responses include broader
instrument classes than the date-effective formal `EQUITY` universe accepted
by this G2 contract.

## Gate ordering and boundaries

- `G0 = PASS`
- `G1 = PASS_PRESERVED`
- `G2 = FAIL`
- `G3 = NOT_RUN`
- `CANARY_EXECUTED = NO`
- `CANARY = NOT_RUN`
- `PRODUCTION_MARKET_DATA_MUTATION = NO`
- `PRODUCTION_DATA_IN_DB = NOT_EVALUATED`
- `PRODUCTION_DATA_IN_API = NOT_EVALUATED`
- `PRODUCTION_DATA_VISIBLE_IN_FRONTEND = NOT_EVALUATED`
- `SCHEDULER_CHANGED = NO`
- `RUNTIME_CHANGED_DURING_WINDOW = NO EVIDENCE OF CHANGE`
- `DOCUMENTATION_PUSH = NO`

Per TASK-DATA-REF-007, a failed G2 stops the window. No G3 authority was
executed or invented, and no Canary or downstream verification was attempted.
The existing repository documentation continues to define G3 as a separate
6806/no-trade semantics gate, but that later gate is not reachable from this
failed G2 evidence.

## Fixed completion fields

```text
TASK_DATA_REF_007 = COMPLETE_TO_G2_STOP
CONTINUOUS_EXECUTION_WINDOW = AUTHORIZED
APPLICATION_RUNTIME_SHA = eb50d2d1e242290e2b9c6c95389bd7cd257caf26
REFERENCE_VERSION = tw-reference-v1-rollover-daf19e9eb051255c
G1 = PASS_PRESERVED
G2_RUN_DATE = 2026-08-13
G2_TPE_EXPECTED = 313
G2_TPE_COVERED = 313
G2_TPE_MISSING_CODES = []
G2_TPE_EXTRA_CODES = 1065 (complete list retained in raw operator JSON)
G2_TWO_EXPECTED = 193
G2_TWO_COVERED = 193
G2_TWO_MISSING_CODES = []
G2_TWO_EXTRA_CODES = 10281 (complete list retained in raw operator JSON)
G2 = FAIL
G3_AUTHORITY = NOT_REACHED_AFTER_G2_FAIL
G3_ENTRYPOINT = NOT_RUN
G3_EXECUTION_CLASS = NOT_RUN
G3 = NOT_RUN
CANARY_AUTHORITY = NOT_REACHED_AFTER_G2_FAIL
CANARY_EXECUTED = NO
CANARY = NOT_RUN
PRODUCTION_MARKET_DATA_MUTATION = NO
PRODUCTION_DATA_IN_DB = NOT_EVALUATED
PRODUCTION_DATA_IN_API = NOT_EVALUATED
PRODUCTION_DATA_VISIBLE_IN_FRONTEND = NOT_EVALUATED
SCHEDULER_CHANGED = NO
RUNTIME_CHANGED_DURING_WINDOW = NO EVIDENCE OF CHANGE
DOCUMENTATION_PUSH = NO
FINAL_STATUS = G2_FAILED_REMEDIATION_REQUIRED
BLOCKER = EXTRA_PROVIDER_IDENTITIES: TPE=1065, TWO=10281
```

STOP. Do not retry the provider, substitute the date, lower identity-set
criteria, use a fallback provider, run `topicpilot-live`, enter G3, run a
Canary, or change Scheduler state from this task.

# TASK-DATA-REF-007B｜G2 Production Re-preflight Stop

## Result

The post-deployment Production G2 preflight did not pass. The execution
stopped before G3, with no retry, date substitution, fallback, persistence,
Canary, or Scheduler action.

Command used:

```console
topicpilot-provider-preflight \\
  --run-date 2026-08-13 \\
  --reference-version tw-reference-v1-rollover-daf19e9eb051255c
```

## Evidence

The reference context remained ACTIVE/READY with 507 formal identities and
the target date remained a valid session. The preflight was read-only with
`productionWriteSet=[]` and `nonReferenceWriteSet=[]`.

TPE reported:

- official authority/version: `TWSE_OFFICIAL_DAILY /
  twse-official-daily.v2`
- target date matched: true
- expected: 313
- covered: 313
- missing: 0
- extra: 1,065
- `errorCode=EXTRA_PROVIDER_IDENTITIES`
- `status=FAIL`

The committed fix at `fdfd37845aa39130cc459902148857f8addbc692` no longer
emits `EXTRA_PROVIDER_IDENTITIES` as a failure. Therefore this output does
not demonstrate that the deployed runtime is executing the corrected G2
contract. The operator evidence did not include a runtime SHA or provider
lineage for this invocation, so runtime implementation provenance remains
unverified.

TWO independently reported:

- official authority/version: `TPEX_OFFICIAL_DAILY /
  tpex-official-daily.v2`
- `errorCode=PROVIDER_REQUEST_FAILED`
- reachable: false
- payload parsed: false
- expected: 193
- covered: 0
- missing: 193
- status: FAIL

## Gate boundary

```text
G2 = FAIL
G3 = NOT_RUN
CANARY = NOT_RUN
PRODUCTION_MARKET_DATA_MUTATION = NO
PRODUCTION_WRITE_SET = []
NON_REFERENCE_WRITE_SET = []
SCHEDULER_CHANGED = NO
FALLBACK_USED = NO
FINAL_STATUS = BLOCKED_G2_PRODUCTION_REPREFLIGHT
BLOCKER = TPE runtime contract not proven at corrected SHA; TWO PROVIDER_REQUEST_FAILED
```

The next permitted diagnostic is deployment provenance confirmation for the
exact release SHA, followed by one exact G2 preflight when the corrected
runtime is confirmed. Do not re-run G0/G1/reference/bootstrap/lifecycle
audits, and do not enter G3 from this failed result.

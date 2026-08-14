# TASK-DATA-REF-007A｜G2 Expected-EQUITY Coverage Scope Fix

## Decision

The G2 contract is corrected to match the approved data-gate semantics:

> Every date-effective expected formal `EQUITY` identity must be present in
> the official provider response. Provider securities outside that expected
> universe do not constitute a coverage failure.

This is a narrow evaluator-contract correction. It does not change provider
authority, the target date, the reference registry, the date-effective
universe, coverage thresholds, persistence, or any Production data.

## Root cause

The previous evaluator computed the diagnostic set
`provider_identity_codes - expected_equity_codes`, but incorrectly included
that set in `coverageComplete` and returned `EXTRA_PROVIDER_IDENTITIES` when it
was non-empty. The Production G2 evidence showed the consequence: all
expected identities were covered (TPE 313/313 and TWO 193/193), but broader
provider payloads caused a false FAIL.

## Corrected contract

- `missingIdentityCodes` remains a hard failure.
- `coveredInstrumentCount` remains the intersection with expected identities.
- `extraIdentityCodes` and `extraInstrumentCount` remain emitted for
  observability but are diagnostic-only.
- `coverageComplete` is true when the expected universe is non-empty and has
  no missing expected identities.
- Provider authority/version, reachability, parsing, target-date matching,
  non-empty payload, reference readiness, and read-only write-set criteria are
  unchanged.

The targeted tests cover both sides: out-of-scope provider identities no
longer fail complete expected coverage, while a missing expected identity
still fails even if an out-of-scope provider identity is present.

## Production boundary

No Production command, database mutation, provider request, deployment,
Scheduler change, push, or Canary was performed by this implementation task.
The earlier 007 operator preflight evidence remains preserved as historical
evidence of the pre-fix evaluator result. A new exact-SHA release and fresh
operator preflight are required before changing G2 status.

## Fixed fields

```text
TASK_DATA_REF_007A = COMPLETE_IMPLEMENTATION_SCOPE_FIX
G2_EXPECTED_UNIVERSE_CONTRACT = EXPECTED_EQUITY_IDENTITIES_REQUIRED
OUT_OF_SCOPE_PROVIDER_IDENTITIES = DIAGNOSTIC_ONLY
MISSING_EXPECTED_IDENTITIES = HARD_FAIL
PROVIDER_AUTHORITY_CHANGED = NO
REFERENCE_VERSION_CHANGED = NO
PRODUCTION_MUTATION = NO
DEPLOY = NO
PUSH = NO
G2_PRODUCTION_REPREFLIGHT = NOT_RUN
FINAL_STATUS = READY_FOR_EXACT_SHA_CI_AND_PRODUCTION_REPREFLIGHT
BLOCKER = NONE
```

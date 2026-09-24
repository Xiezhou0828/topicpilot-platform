# Frontend regression validation

## Candidate validation

```text
TODAY_FRONTEND_TEST_STATUS=PASS (167 passed, 0 failed, 0 skipped)
API_CLIENT_TEST_STATUS=PASS (4 passed, 0 failed)
TYPESCRIPT_STATUS=PASS (tsc --noEmit)
FRONTEND_BUILD_STATUS=PASS
LINT_STATUS=PASS (0 errors, 1 existing warning)
FRONTEND_REGRESSION_STATUS=PASS
```

The one lint warning is the pre-existing missing `state` dependency warning in
`apps/web/app/components/FavoriteButton.tsx`; it is outside this Today change.
The candidate dependency install used `npm ci` from the committed web lockfile.
Npm reported existing audit advisories; no audit remediation was performed.

## Baseline comparison

```text
BASELINE_SHA=c177b949df9dbd53044bc598b9f0a1a48cb6db12
BASELINE_TESTS=162 passed, 0 failed, 0 skipped
CANDIDATE_TESTS=167 passed, 0 failed, 0 skipped
TEST_COUNT_DELTA=+5
TEST_COUNT_DELTA_REASON=Five Today-focused tests were added by the validated candidate.
BASELINE_FAILURE_COUNT=0
CANDIDATE_FAILURE_COUNT=0
NEW_FAILURE_COUNT=0
```

The baseline install attempt was stopped by the E: volume space limit while
creating a second copy of `node_modules`. For this diagnostic comparison only,
the baseline used the candidate's lockfile-equivalent installed dependency
directory through an E:-local junction; both baseline build and test then
passed. The candidate's own clean `npm ci` and full build/test run are the
reproducible validation evidence for promotion.

No backend tests, migration application, or database operation was required or
performed because the final diff contains no backend or migration changes.

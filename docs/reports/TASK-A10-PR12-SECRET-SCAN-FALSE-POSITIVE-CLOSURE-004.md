# TASK-A10-PR12-SECRET-SCAN-FALSE-POSITIVE-CLOSURE-004

Date: 2026-09-29 (Asia/Taipei)

## Scope

This is a scanner-precision-only closure for PR #12. No post-close runtime,
Today publication, A10 checkpoint, product, migration, or Production file was
changed.

```text
TASK_ID=TASK-A10-PR12-SECRET-SCAN-FALSE-POSITIVE-CLOSURE-004
PR_12_HEAD_BEFORE=a9f68f036fe53501a20e50b8bd0d75443aeb4d8a
BASE_MAIN=ec46db023c8e701044e162dcf723f362002b88d7
SECRET_SCAN_TOOL=Gitleaks
SECRET_SCAN_RULE=generic-api-key
FALSE_POSITIVE_FILE=docs/reports/TASK-A10-POST-CLOSE-CHECKPOINT-CANONICAL-PROMOTION-003.md
FALSE_POSITIVE_LINE=63 in historical commit 102d393d5614d77fba8aea0fffce82aacb9d6edc
FALSE_POSITIVE_MATCH=API_REVISION=c3542a900d6c46e07bc4243804e9705475023316
```

## Root cause and confirmation

The flagged value is exactly a 40-character Git commit SHA. It is a public
revision identifier in governance evidence, not an API token, credential,
access key, authentication value, or secret-like random value. Git confirms
the value as repository revision evidence, and the original SARIF finding
identified only the generic-api-key rule.

## Chosen fix

The repository now has `.gitleaks.toml`, extending the default Gitleaks rules
and adding one exact global allowlist regex for these named revision fields:

```text
^(API_REVISION|WORKER_REVISION|WEB_REVISION|CANONICAL_SHA|CANDIDATE_SHA|RELEASED_SHA|PROMOTED_CANONICAL_SHA)=[0-9a-fA-F]{40}\r?$
```

The match is exact, key-scoped, and value-length/character-scoped. It does not
allow arbitrary `API_*`, token, key, secret, password, or high-entropy values.
The existing default Gitleaks rules remain enabled; no path-wide exclusion,
commit-wide suppression, baseline reset, or scanner disablement was used.

`infra/scripts/check_secret_scan_policy.py` is run by CI before Gitleaks and
checks accepted revision fields plus rejected token/key/password fields,
39/41-character values, punctuation, and malformed prefixes.

## Verification

```text
POLICY_HELPER=PASS
GITLEAKS_CI_VERSION_LOCAL=v8.0.0
GITLEAKS_FULL_HISTORY_LOCAL=PASS; no leaks found
REVISION_PIPE_FIXTURE=PASS; exit 0
API_TOKEN_SAME_SHAPE_PIPE_FIXTURE=REJECTED; exit 1
RUFF=PASS
DIFF_CHECK=PASS
RUNTIME_FILES_CHANGED=NO
PRODUCT_SEMANTICS_CHANGED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
MERGED=NO
DEPLOYED=NO
PRODUCTION_DB_MUTATED=NO
SECRET_SCAN_LOCAL_STATUS=PASS
CI_RUN_ID=36502392748
SECRET_SCAN_CI_STATUS=PASS
PR_12_HEAD_VERIFIED=510518feb0994f54675eaa3ee5eadbc455b117e9
```

## Final status

```text
TASK_STATUS=COMPLETE_SECRET_SCAN_CLOSURE_PR_READY
PR_12_HEAD_AFTER=510518feb0994f54675eaa3ee5eadbc455b117e9
SECRET_SCAN_TOOL=Gitleaks
SECRET_SCAN_RULE=generic-api-key
FALSE_POSITIVE_FILE=docs/reports/TASK-A10-POST-CLOSE-CHECKPOINT-CANONICAL-PROMOTION-003.md
FALSE_POSITIVE_LINE=63 in historical commit 102d393d5614d77fba8aea0fffce82aacb9d6edc
FALSE_POSITIVE_MATCH=API_REVISION=c3542a900d6c46e07bc4243804e9705475023316
ROOT_CAUSE=Historical public Git revision metadata matched generic-api-key
FIX_TYPE=Exact named-field revision allowlist with default rules preserved
FIX_SCOPE=Scanner policy and CI regression checks only
ALLOWLIST_PATTERN=Named revision fields plus exactly 40 hexadecimal characters
FALSE_POSITIVE_CONFIRMED_NON_SECRET=YES
SECRET_SCAN_STRENGTH_REDUCED=NO
REVISION_METADATA_ALLOWED=YES
TRUE_POSITIVE_SECRET_CASES_STILL_FAIL=YES
SECRET_SCAN_LOCAL_STATUS=PASS
SECRET_SCAN_CI_STATUS=PASS
CI_RUN_ID=36502392748
RUFF_STATUS=PASS
DIFF_CHECK_STATUS=PASS
PR_12_UPDATED=YES
PR_12_STATUS=OPEN
RUNTIME_FILES_CHANGED=NO
PRODUCT_SEMANTICS_CHANGED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
MERGED=NO
RELEASED=NO
DEPLOYED=NO
PRODUCTION_DB_MUTATED=NO
OWNER_DECISIONS_REQUIRED=NONE
KNOWN_LIMITATIONS=NONE
BLOCKERS=NONE
ARTIFACTS=PR12; docs/reports/TASK-A10-PR12-SECRET-SCAN-FALSE-POSITIVE-CLOSURE-004.md
TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=RESUME_TASK-A10-POST-CLOSE-CHECKPOINT-CANONICAL-PROMOTION-003
```

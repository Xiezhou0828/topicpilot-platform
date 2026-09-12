# B2 Contract Baseline Closure | Lifecycle Publication Schema Canonicalization

```text
TASK=B2 Contract Baseline Closure | Lifecycle Publication Schema Canonicalization
BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
EXACT_SHA_BEFORE=a18ff3d40cf6e993bfaea328e6a8a52ec580ad79
EXACT_SHA_AFTER=THIS_COMMIT
COMMIT_SHA=THIS_COMMIT
COMMIT_MESSAGE=chore(api): canonicalize lifecycle publication schema
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_RUN

B2_SCHEMA_BASELINE_CANONICALIZED=PASS
LIFECYCLE_PUBLICATION_FIELDS=5/5
AS_OF_AT_CONTRACT=PASS
PUBLICATION_STATUS_CONTRACT=PASS
CONTRACT_VERSION_CONTRACT=PASS
CALCULATION_VERSION_CONTRACT=PASS
EVALUATION_MODE_CONTRACT=PASS
RUNTIME_OPENAPI_SAVED_CONTRACT_PARITY=PASS
GENERATED_CLIENT_CONTRACT_PARITY=PASS
NO_B2_EVALUATOR_MUTATION=PASS
NO_B2_PUBLICATION_PIPELINE_MUTATION=PASS
NO_B2_DB_OR_MIGRATION_MUTATION=PASS
NO_FORMAL_DATA_MUTATION=PASS
WSB_OPENAPI_BLOCKER_RESOLVED=YES
SAFE_TO_RETRY_WSB_CANONICALIZATION=YES

HUNK_LEVEL_RECONCILIATION_USED=YES
REASON=schemas.py is shared with preserved B2 owner work; only the five-field additive hunk was canonicalized
HEAD_INDEX_WORKTREE_AUDIT=PASS
POST_RECONCILIATION_CLEAN_CANDIDATE=PASS
PUSH=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_MUTATION=NO
```

`THIS_COMMIT` denotes the commit containing this report, because a Git commit
cannot embed its own object ID. The resolved object ID is recorded in the task
handoff immediately after commit creation.

## Decision and exact write-set

The committed OpenAPI already declared five optional formal-publication
metadata properties on `TopicLifecycleRead`, while the clean runtime schema at
the starting commit did not. This closure canonicalizes exactly the existing
five-line additive schema hunk:

- `as_of_at: datetime | None`, alias `asOfAt`, default `None`;
- `publication_status: str | None`, alias `publicationStatus`, default `None`;
- `contract_version: str | None`, alias `contractVersion`, default `None`;
- `calculation_version: str | None`, alias `calculationVersion`, default `None`;
- `evaluation_mode: str | None`, alias `evaluationMode`, default `None`.

The write-set is limited to `services/api/src/topicpilot_api/schemas.py`, one
direct contract test in
`services/api/tests/test_topic_lifecycle_contract.py`, and this report. No
OpenAPI or generated-client artifact changed.

The test proves all five camelCase aliases serialize with their existing
values, appear in the Pydantic JSON schema, and remain outside the required
property list. The saved OpenAPI independently confirms `asOfAt` as nullable
`date-time`, the other four as nullable strings, and none of the five as
required.

## Clean-candidate parity evidence

Two candidates were produced from `git archive` of the exact starting SHA.
The schema-only candidate overlaid only the five-field schema hunk and its
test. Its runtime `TopicLifecycleRead` schema exactly equaled the saved
OpenAPI schema. Full runtime comparison then differed only by the four known
WS-B Topic Catalog paths: runtime 40 paths versus saved 44.

The second candidate added the previously isolated exact WS-B five-file
overlay solely as diagnostic evidence. Runtime OpenAPI then equaled the saved
contract as a complete JSON object: 44/44 paths, no missing or extra paths,
and exact `TopicLifecycleRead` schema equality. This proves the Lifecycle
blocker is resolved without including any WS-B file in this commit. WS-B must
still be canonicalized by its own bounded task.

## Validation

- Clean candidate focused Lifecycle/Topic contract tests: 18 passed, 0 failed,
  0 skipped. This includes 11/11 for the new contract test plus Topic Catalog
  provider coverage and 7 additional Lifecycle contract-closure tests.
- Direct schema-only contract file: 4 passed, including the one new test.
- API client: 4 passed, 0 failed/skipped.
- Generated-client regeneration/check: PASS. Saved OpenAPI,
  `packages/api-client/src/schema.d.ts`, and
  `apps/web/app/lib/generated-api.d.ts` remained byte-identical to HEAD after
  regeneration.
- Frontend generated type smoke: PASS. All five properties are present as
  optional nullable fields in the committed generated web type.
- Python 3.12 compile and Ruff for touched Python scope: PASS.
- `git diff --check` for the task write-set: PASS.
- PostgreSQL tests: NOT RUN; this schema-only task does not require a database.
  No migration or database command was executed.

The prior direct lifecycle contract file had 3 tests; it now has 4
(`TEST_COUNT_PRE=3`, `TEST_COUNT_POST=4`, `TEST_COUNT_DELTA=+1`) because the
five committed metadata fields now have an explicit runtime schema and
serialization assertion. The broader focused run is impact-selected and is
not represented as a replacement for the B2 full-suite counts.

The first generated-client attempt could not write its npm cache because the
C: workspace disk had approximately 40 MB free. Re-running with an E: task
cache succeeded. This environmental retry did not alter repository artifacts.
The four incomplete C: diagnostic candidate directories were subsequently
moved, at owner request, under
`E:/topicpilot-platform-canonical/work/c-drive-incomplete-diagnostics-20260909`;
the validated candidate remains under the adjacent ignored `work/` directory.

## Mutation and preservation boundary

No evaluator, formal publisher, ORM, migration, operator, scheduler,
production read-model behavior, WS-B provider, frontend product behavior,
deployment configuration, or `NEXT_TASK` file is included. No database was
read or written, no Lifecycle row was materialized, and no migration was
executed.

All pre-existing owner and parallel tracked/untracked changes outside the
five-line schema hunk were retained in the working tree and excluded from the
staged diff. The post-commit handoff records the resolved commit SHA and final
dirty-state audit. The only authorized next step is to retry WS-B Backend
Canonicalization; this closure does not run WS-B or replay F9.

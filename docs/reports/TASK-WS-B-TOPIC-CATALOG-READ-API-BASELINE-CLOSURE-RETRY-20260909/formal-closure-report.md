# WS-B Backend Canonicalization | Topic Catalog Read API Baseline Closure — PASS

```text
TASK=WS-B Backend Canonicalization | Topic Catalog Read API Baseline Closure — RETRY AFTER B2
BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
EXACT_SHA_BEFORE=d27981a7f9369762a31ecb06f3ab9c8b23a62ba3
EXACT_SHA_AFTER=THIS_COMMIT
COMMIT_SHA=THIS_COMMIT
COMMIT_MESSAGE=feat(topics): publish topic catalog read api
CANONICAL_STATUS=CANONICALIZED
RELEASE_STATUS=NOT_RELEASE_CANDIDATE
PRODUCTION_VERIFICATION=NOT_RUN

TOPIC_CATALOG_BACKEND_CANONICALIZED=PASS
CLEAN_HEAD_TOPIC_CATALOG_ROUTES=4/4
TOPIC_CATALOG_ROOT_ROUTE=PASS
TOPIC_CATALOG_DETAIL_ROUTE=PASS
TOPIC_CATALOG_CURRENT_SNAPSHOT_ROUTE=PASS
TOPIC_CATALOG_BOUNDED_HISTORY_ROUTE=PASS
PARENT_LEAF_BOUNDARY=PASS
FORMAL_SNAPSHOT_BOUNDARY=PASS
UNAVAILABLE_NO_FALLBACK=PASS
BOUNDED_366_DAY_HISTORY=PASS
RUNTIME_OPENAPI_SAVED_CONTRACT_PARITY=PASS
GENERATED_CLIENT_CONTRACT_PARITY=PASS
B2_SCHEMA_BASELINE_PRESERVED=PASS
F9_TOPIC_BACKEND_BLOCKER_RESOLVED=YES
C_DRIVE_ARTIFACTS_CREATED=0
SAFE_TO_REPLAY_F9=YES

HUNK_LEVEL_RECONCILIATION_USED=YES
REASON=main.py is shared with preserved owner work; its complete diff was verified as only the two WS-B router-registration lines
HEAD_INDEX_WORKTREE_AUDIT=PASS
POST_RECONCILIATION_CLEAN_CANDIDATE=PASS
PUSH=NO
MERGE=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_MUTATION=NO
```

`THIS_COMMIT` denotes the commit containing this report because a Git commit
cannot embed its own object ID. The resolved object ID is recorded in the final
handoff after commit creation.

## Exact write-set

- `services/api/src/topicpilot_api/main.py`: import and include the Topic Catalog router; the staged diff contains exactly two added lines.
- `services/api/src/topicpilot_api/topic_catalog.py`: read-only identity, hierarchy, effective membership, current formal snapshot, and bounded formal history provider.
- `services/api/src/topicpilot_api/topic_catalog_api.py`: four GET routes and truthful 503/422 problem mapping.
- `services/api/src/topicpilot_api/topic_catalog_schemas.py`: minimum catalog, availability, source, publication, snapshot, and history response schemas.
- `services/api/tests/test_topic_catalog.py`: seven focused provider, boundary, OpenAPI, and route tests.
- This closure report.

No OpenAPI, generated-client, frontend, migration, ORM, evaluator, publication,
scheduler, deployment, Production, or `NEXT_TASK` file is in the write-set.

## Contract and behavior

The committed surface contains `GET /api/v2/topic-catalog`, detail, current
snapshot, and snapshot-history routes. It preserves identity, name, status,
as-of, Parent/Leaf hierarchy, Leaf members, availability and reason fields,
and source/reference metadata. Parent topics expose diagnostic identity and
hierarchy only; their members and snapshots are `NOT_APPLICABLE`.

Leaf snapshot consumption remains restricted to `FORMAL`, `PUBLISHED`,
`PIT_FORMAL`, `FINAL`, non-superseded, effective-date-valid rows with complete
membership, hash, relation, snapshot identity, and lineage fields. The provider
does not calculate snapshots and has no legacy, research, shadow, or demo
fallback. History windows are limited to 366 days.

## Clean candidate and validation

The clean candidate was built from `git archive` of exact SHA
`d27981a7f9369762a31ecb06f3ab9c8b23a62ba3` and overlaid with only the five
WS-B source/test files. It is stored entirely at
`E:/topicpilot-platform-canonical/work/wsb-retry-20260909/candidate`. `TEMP`,
`TMP`, tool caches, dependency installs, the archive, manifests, and diagnostics
were directed under the adjacent E: task directory. No new artifact was created
on C: (`C_DRIVE_ARTIFACTS_CREATED=0`).

- Focused Topic Catalog plus Lifecycle/B2 preservation: 18 passed, 0 failed, 0 skipped.
- Direct Topic Catalog backend: 7 passed within the 18-test focused run.
- F2/F3 Topic Catalog and history frontend compatibility: 20 passed, 0 failed/skipped.
- API client: 4 passed, including all four Topic Catalog calls.
- Runtime OpenAPI versus saved contract: exact JSON equality, 44/44 paths; Topic Catalog 4/4.
- Generated client regeneration: saved OpenAPI, API schema types, and Web generated types remained equal.
- Root route unavailable-authority probe: HTTP 503 with `Topic catalog unavailable` and `Topic identity read model is unavailable`.
- Python 3.12 compile and Ruff for touched backend/test files: PASS.
- `git diff --check` for the exact WS-B patch: PASS.
- PostgreSQL integration: NOT RUN because no explicit PostgreSQL test database was configured; no database read/write or migration was performed.

The predecessor WS-B replay ran 7 backend, 20 frontend, and 4 API-client tests.
This retry retains those counts and adds the B2/Lifecycle preservation subset
for 18 total focused backend contract tests. There is no unexplained test-count
reduction.

## Preservation and disposition

All pre-existing owner, A10, B2 implementation, frontend, deployment, and
diagnostic dirty files were excluded from the commit. Their pre-task SHA-256
manifest is stored under the E: task directory and is compared after commit.
No reset, clean, checkout, overwrite, stash manipulation, broad staging, push,
merge, deploy, Production mutation, scheduler action, or `NEXT_TASK` mutation
occurred. The next authorized recommendation is F9 replay; it was not executed.

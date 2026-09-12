# TASK-FE-BE-TODAY-005B-INDEX-CONTRACT

## Market Index Typed Contract & Fixture Boundary

FINAL_STATUS=TODAY_MARKET_INDEX_CONTRACT_ARCHIVED_WAITING_SOURCE_USE_APPROVAL
CONTRACT_SLICE_STATUS=TODAY_MARKET_INDEX_TYPED_CONTRACT_READY
TWSE_INDEX_CONTRACT=READY
TPEX_INDEX_CONTRACT=READY
TWSE_CHANGE_PCT=PROVIDER_OWNED
TPEX_CHANGE_PCT=NULL_FAIL_CLOSED
TURNOVER_STATUS=BLOCKED_PENDING_TPEX_SEMANTICS_AND_SOURCE_USE_APPROVAL

This report records the contract-and-fixture slice only. It does not authorize
market-index persistence, post-close capture, Home/API publication, generated
client or frontend wiring, turnover implementation, scheduler, canary, deploy,
or Production writes.

## CURRENT_STATE

CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_START_SHA=af3baa8a85a4974af0392f523f1faf0d611e3660
CANONICAL_FINAL_SHA=017460da9d0a8fde2905e85f39e8670b5393b9c9
CURRENT_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
DIRTY_STATE=PRE_EXISTING_USER_AND_PARALLEL_WORKSTREAM_CHANGES_PRESERVED
WORKTREE_USED=CANONICAL_REPOSITORY
WORKTREE_RECONCILED=YES_FOR_TASK_WRITE_SET
WORKTREE_CLEANUP=NO_UNRELATED_FILES_REMOVED
LOCAL_COMMIT=017460da9d0a8fde2905e85f39e8670b5393b9c9

The expected handoff file `docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md` is not
present; repository instructions explicitly prohibit creating a duplicate.
The current authority was therefore checked against `PROJECT_CONTEXT.md`,
`AGENTS.md`, `docs/ROADMAP.md`, the current DATA/Reference reports, and the
existing provider/read-model code.

## STALE_GATE_CORRECTION

STALE_GATE_BASELINE_FOUND=YES
STALE_GATE_BASELINE_CORRECTED=YES_IN_THIS_SUPERSEDING_REPORT
CURRENT_PROTECTED_BASELINE=TASK-DATA-REF-009A_RUNTIME_ACTIVE_REFERENCE_BINDING_FIX_AND_SINGLE_POST_CLOSE_CANARY_RETRY
G1_CURRENT_AUTHORITY=PASS
G2_CURRENT_AUTHORITY=PASS
G3_CURRENT_AUTHORITY=PASS
CANARY_CURRENT_AUTHORITY=PASS

The predecessor 005B0 report retains historical wording (`G1=PRESERVED FAIL`,
2 markets / 0 instruments / missing instruments). Current owner documents and
`TASK-DATA-REF-009A` supersede that stale gate evidence: the protected
reference baseline is 506/506 with downstream readiness true and G0/G1/G2/G3
plus the post-close canary passing. No gate was rerun or changed by this task.

## SOURCE_IDENTITY

TWSE_AGGREGATE_SOURCE_IDENTITY=TWSE_OFFICIAL_MARKET_AGGREGATE
TPEX_AGGREGATE_SOURCE_IDENTITY=TPEX_OFFICIAL_MARKET_AGGREGATE
SOURCE_REGISTRY_CHANGED=NO
SOURCE_REGISTRY_RUNTIME_ACTIVATED=NO

The implementation declares provider-neutral aggregate identities locally in
the contract module. It does not alter the runtime source registry or activate
any Production provider path.

## TWSE_INDEX

TWSE_INDEX_IDENTITY=TWSE:TAIEX
TWSE_SOURCE_DATASET=exchangeReport.MI_INDEX
TWSE_SOURCE_ENDPOINT=https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX
TWSE_ROW_SELECTOR=`指數 == 發行量加權股價指數`
TWSE_TRADING_DATE_FIELD=日期
TWSE_VALUE_FIELD=收盤指數
TWSE_CHANGE_FIELD=漲跌符號 + 漲跌點數
TWSE_CHANGE_PCT_FIELD=漲跌百分比
TWSE_PREVIOUS_CLOSE_DERIVATION=`previous_close = value - signed_change` in the backend adapter only
TWSE_DATA_STATUS=AVAILABLE_ON_EXACT_VALID_ROW_ELSE_UNAVAILABLE

The sign parser accepts explicit positive, negative, and zero values and
rejects missing or unknown signs. The provider-supplied percentage remains the
authoritative percentage; the browser is not permitted to recompute it.

## TPEX_INDEX

TPEX_INDEX_IDENTITY=TPEX:TPEx
TPEX_SOURCE_DATASET=tpex_daily_trading_index
TPEX_SOURCE_ENDPOINT=https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index
TPEX_TRADING_DATE_FIELD=Date
TPEX_VALUE_FIELD=TPExIndex
TPEX_CHANGE_FIELD=Change
TPEX_CHANGE_PCT=NULL_IN_V1_CONTRACT
TPEX_PREVIOUS_CLOSE_DERIVATION=BLOCKED_AND_NULL_UNTIL_SAME_SERIES_DERIVATION_IS_APPROVED
TPEX_CROSSCHECK_SOURCE=https://www.tpex.org.tw/openapi/v1/tpex_index
TPEX_DATA_STATUS=AVAILABLE_ON_EXACT_VALID_ROW_ELSE_UNAVAILABLE

The TPEx adapter handles the official multi-day response by selecting an exact
normalized target date when one is supplied; an ambiguous multi-day response
without a target is unavailable. The cross-check source is parsed separately
and is not promoted to replace the primary daily-index identity.

## TYPED_CONTRACT

MARKET_INDEX_TYPED_RESULT=`MarketIndexResult`, immutable and provider-neutral
RAW_PROVIDER_DATE_PRESERVED=YES
DATE_NORMALIZATION=ROC_YYYMMDD_AND_GREGORIAN_YYYYMMDD_TO_ISO_DATE
FINALITY_SEMANTICS=`source_publication=DAILY_RESPONSE_AS_PUBLISHED`; `finality=NOT_EXPLICITLY_DECLARED_BY_SOURCE`
CORRECTION_EVIDENCE=SOURCE_ENDPOINT_PLUS_RAW_PROVIDER_DATE_PLUS_CONTENT_HASH_AND_LINEAGE
NULL_SEMANTICS=MISSING_OR_UNAPPROVED_NUMERIC_FIELDS_REMAIN_NULL; NEVER_COERCE_TO_ZERO
PREVIEW_BOUNDARY=PREVIEW_IS_EXPLICIT_CALLER_STATE_ONLY
PROVIDER_ERROR_FALLBACK_TO_PREVIEW=NO
TURNOVER_INCLUDED=NO

The result carries market, identity, display name, normalized trading date,
value, previous close, change, change percentage, source identity/dataset/
endpoint/field path, retrieval and as-of timestamps, publication/finality,
correction evidence, lineage, data status, quality status, and response hash.
Statuses are `AVAILABLE`, `UNAVAILABLE`, and `PREVIEW`; a parser or provider
failure is fail-closed to `UNAVAILABLE`, never an implicit preview.

## FIXTURES_TESTS

TWSE_VALID_FIXTURE=`services/api/tests/fixtures/market_index/twse_mi_index_valid.json`
TWSE_NEGATIVE_FIXTURES=`twse_mi_index_missing_target.json`, `twse_mi_index_malformed_date.json`, `twse_mi_index_invalid_sign.json`, `twse_mi_index_missing_change_pct.json`
TPEX_VALID_FIXTURE=`services/api/tests/fixtures/market_index/tpex_daily_trading_index_valid.json`
TPEX_NEGATIVE_FIXTURES=`tpex_daily_trading_index_missing_value.json`, `tpex_daily_trading_index_malformed_date.json`, `tpex_daily_trading_index_invalid_change.json`
TPEX_CROSSCHECK_FIXTURE=`services/api/tests/fixtures/market_index/tpex_index_crosscheck_valid.json`
DATE_TESTS=ROC_TWSE_TPEX_AND_GREGORIAN_CROSSCHECK_PASS
PREVIOUS_CLOSE_TESTS=TWSE_BACKEND_DERIVATION_PASS; TPEX_DERIVATION_BLOCKED_NULL_PASS
NULL_FAIL_CLOSED_TESTS=PASS_FOR_MISSING_ROW_DATE_NUMERIC_SIGN_PERCENTAGE_AND_PROVIDER_ERROR
NO_TURNOVER_REGRESSION=PASS

Fixtures are reduced official-shaped samples, deterministic, secret-free, and
contain no turnover fields, private data, credentials, or Production dump.

## IMPLEMENTATION_BOUNDARY

Implementation files:

- `services/api/src/topicpilot_api/market_data/index_contract.py`
- `services/api/src/topicpilot_api/market_data/__init__.py`
- `services/api/tests/test_market_index_contract.py`
- `services/api/tests/fixtures/market_index/`

DB_CHANGED=NO
MIGRATION_CREATED=NO
POST_CLOSE_CHANGED=NO
HOME_API_CHANGED=NO
OPENAPI_CHANGED=NO
GENERATED_CLIENT_CHANGED=NO
FRONTEND_CHANGED=NO
TURNOVER_CHANGED=NO
PRODUCTION_CAPTURE_ENABLED=NO

## SOURCE_USE_GATE

TWSE_SOURCE_USE_APPROVAL=PENDING
TPEX_SOURCE_USE_APPROVAL=PENDING
TWSE_INDEX_PRODUCTION_CAPTURE=BLOCKED_PENDING_SOURCE_USE_APPROVAL
TPEX_INDEX_PRODUCTION_CAPTURE=BLOCKED_PENDING_SOURCE_USE_APPROVAL

Technical API availability and fixture parsing do not constitute approval to
retain, publish, or capture official responses in Production.

## NEXT_SLICE

NEXT_TODAY_INDEX_SLICE=BLOCKED_PENDING_SOURCE_USE_APPROVAL_FOR_PERSISTENCE
TURNOVER_STATUS=BLOCKED_PENDING_TPEX_SEMANTICS_AND_SOURCE_USE_APPROVAL

After source-use approval and a protected implementation gate, the next index
slice may design persistence and post-close capture. It must preserve the same
typed contract and must not add browser-side calculations. Turnover remains a
separate blocked slice.

## DOCUMENTATION

ROADMAP_UPDATED=YES_TASK_HUNK_RECONCILED
PROJECT_CONTEXT_UPDATED=YES_TASK_HUNK_RECONCILED
WORK_ORDERS_UPDATED=YES_TASK_HUNK_RECONCILED
PRODUCT_ROADMAP_UPDATED=N/A
DOCUMENTATION_INDEX_UPDATED=N/A
DAILY_PROGRESS_UPDATED=N/A

The three owner-document additions are reconciled as task-specific hunks only;
pre-existing unrelated dirty changes in those files remain unstaged.

## VALIDATION

FOCUSED_TWSE_TESTS=PASS
FOCUSED_TPEX_TESTS=PASS
DATE_PARSER_TESTS=PASS
NEGATIVE_FIXTURE_TESTS=PASS
RELEVANT_BACKEND_TESTS=PASS (34 total: 9 focused plus 25 existing exchange/provider/preflight tests)
RUFF=PASS
FORMAT=PASS
IMPORT_COMPILE=PASS
DIFF_CHECK=PASS
SECRET_SCAN=PASS
FIXTURE_SAFETY=PASS

Protected G1/G2/G3 and canary status is preserved from the current 009A
authority; those Production gates were not rerun by this contract-only task.

## SAFETY

PRODUCTION_MUTATION=NO
PRODUCTION_DB=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
HISTORICAL_CHANGED=NO
STOCK_CHANGED=NO
TOPIC_CHANGED=NO
TAXONOMY_CHANGED=NO
RELATIONS_CHANGED=NO
OPPORTUNITY_CHANGED=NO
RECOMMENDATION_CHANGED=NO
G1=PRESERVED PASS
G2=PRESERVED PASS
G3=PRESERVED PASS
POST_CLOSE_CANARY=PRESERVED PASS

IMPLEMENTATION_COMPLETE=YES
CANONICAL_RECONCILIATION=YES_FOR_TASK_WRITE_SET
NEW_REPORT=docs/reports/TASK-FE-BE-TODAY-005B_INDEX_TYPED_CONTRACT_AND_FIXTURE_BOUNDARY.md

## FINAL_CLOSURE

CLOSURE_STATUS=COMPLETE_ARCHIVED_WAITING_SOURCE_USE_APPROVAL
CANONICAL_COMMIT=017460da9d0a8fde2905e85f39e8670b5393b9c9
OWNER_DOC_RECONCILIATION=COMPLETED_TASK_HUNKS_ONLY
SOURCE_USE_GATE=OPEN_BLOCKER
TURNOVER_GATE=OPEN_BLOCKER
NEXT_IMPLEMENTATION=WAITING_SOURCE_USE_APPROVAL
ARCHIVE_STATE=MARKET_INDEX_TYPED_CONTRACT_COMPLETE; PRODUCTION_CAPABILITY_NOT_COMPLETE
REPORT_FINALIZED=YES
STALE_COMMIT_SHA_PENDING_REMOVED=YES
STALE_GATE_AUTHORITY_CORRECT=YES
MAINLINE_C_NAMING_POLLUTION_FOUND=NO
MAINLINE_C_NAMING_POLLUTION_CORRECTED=NOT_APPLICABLE
APPLICATION_CODE_CHANGED=NO
PROVIDER_CHANGED=NO
SOURCE_REGISTRY_RUNTIME_ACTIVATED=NO

VALIDATION_COMMIT_REACHABILITY=PASS
VALIDATION_IMPLEMENTATION_PRESENCE=PASS
VALIDATION_OWNER_DOCS=PASS_TASK_HUNKS_ONLY
VALIDATION_STALE_PLACEHOLDERS=PASS_CURRENT_REPORT_NO_PENDING_SHA
VALIDATION_STALE_GATE=PASS_TASK_DATA_REF_009A
VALIDATION_NAMING=PASS
VALIDATION_LINKS=PASS
DIFF_CHECK=PASS
SECRET_SCAN=PASS

No Production mutation, reference bootstrap, provider-authority change,
turnover implementation, frontend/API/OpenAPI work, scheduler/canary,
push, merge, deploy, or NEXT_TASK action was performed.

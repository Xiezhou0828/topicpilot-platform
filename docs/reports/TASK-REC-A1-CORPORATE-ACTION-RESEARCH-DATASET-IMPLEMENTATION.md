# TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION

Review date: 2026-08-15

Final status: REC_A1_CORPORATE_ACTION_DATASET_IMPLEMENTED_WITH_COVERAGE_GAPS_FREEZE_BLOCKED

This task implements the smallest research-only Corporate Action semantic
dataset contract and a versioned local artifact. It does not download or
retain bulk official responses, rewrite historical OHLCV, alter trading
decisions, create a Production table, or run REC-A1.

## 1. Executive Summary

The dataset implementation is real but intentionally partial:

~~~text
DATASET_IMPLEMENTED=PARTIAL
DATASET_VERSION=REC-A1-CA-EVENTS-V0
DATASET_ROWS=2
TWSE_ROWS=2
TPEX_ROWS=0
TWSE_COVERAGE=PARTIAL
TPEX_COVERAGE=UNKNOWN
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
~~~

The two materialized rows are:

1. TPE:2330 cash dividend/ex-dividend, announcement 2026-06-10,
   effective 2026-06-11;
2. TPE:6806 lifecycle termination, effective 2026-06-23, sourced from
   the already validated tw-reference-v1 lifecycle authority.

The TPEx source method remains MANUAL_OR_BOUNDED_QUERY_ONLY; no operator
bounded TPEx artifact was supplied for this task, and no unattended TPEx
query was run. The next blocker is precise TPEx bounded-artifact
coverage closure, not Owner approval.

## 2. Canonical Preflight

~~~text
TASK_ID=TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_PRE_SHA=6831cf3448506abea8e62e3790014d021b208868
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
PRE_EXISTING_DIRTY_FILE_COUNT=162
ACTIVE_WORKTREES=15
WORKTREE_USED=NO
WORKTREE_CREATED=NO
WORKTREE_REMOVED=NOT_APPLICABLE
~~~

The canonical checkout was used directly because this task's write set is
limited to a new research package, one artifact directory, one focused test,
and this report. Existing modified and untracked files were preserved and
were not reset, stashed, cleaned, or staged.

Exact task write set:

- services/api/src/topicpilot_api/research/__init__.py
- services/api/src/topicpilot_api/research/corporate_action_dataset.py
- services/api/tests/test_corporate_action_dataset.py
- reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json
- docs/reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION.md

## 3. Prior Authority Baseline

The direct authority is the
[source-use and event-semantics closure](TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE.md).
The following values are carried forward:

~~~text
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
CORPORATE_ACTION_EVENT_SCHEMA_READY=YES
EVENT_EXCLUDED_RAW_POLICY=READY
UNKNOWN_EVENT_AUTHORITY_FAIL_CLOSED=YES
TRADING_DECISION_LOOKAHEAD=NO
POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES
UNIVERSE_POLICY=LIFECYCLE_GATED_507
REFERENCE_VERSION=tw-reference-v1
CURRENT_FIXED_UNIVERSE=507
HISTORICAL_WINDOW=2026-02-02_TO_2026-08-13
HIST_002B_ROWS=63826
SURVIVORSHIP_SAFE_CLAIM=NO
RS=OMITTED
TOPIC_CONTEXT=OMITTED
~~~

The predecessor contract remains separate from the dataset implementation:
corporate-action events can exclude post-hoc outcome episodes, but cannot
change Gate, Rank, Trigger, Entry, signal date, or historical recommendation.

## 4. Source Acquisition Boundary

### TWSE

- Documented OpenAPI endpoints remain the only conditionally permitted
  automated path. This implementation did not call them.
- Public historical HTML/CSV/query surfaces are represented as
  MANUAL_OR_BOUNDED_QUERY_ONLY.
- Paid T48/E-Shop products remain NOT_AUTHORIZED; no entitlement evidence
  exists in this repository.
- The 2330 control uses the reviewed official notice as a reduced semantic
  record. Its PDF is not copied into the repository.
- The 6806 control uses the existing canonical lifecycle bundle row and its
  official TWSE source URL.

### TPEx

- AUTOMATED_EXTRACTION_TPEX=BLOCKED.
- No crawler, browser automation, script scraping, bulk extractor, or
  anti-bot bypass was used.
- build_event is the import/normalization contract for an
  operator-provided bounded reduced semantic artifact. It does not fetch
  TPEx data.
- No TPEx event row is claimed from absence of a query result.

The official terms and product boundaries remain documented in the
[TWSE OpenAPI catalog](https://openapi.twse.com.tw/),
[TWSE website terms](https://www.twse.com.tw/en/terms/use.html), and
[TPEx E-Data Shop terms](https://eshop.tpex.org.tw/en/useTerms/index).

## 5. Dataset Architecture

The implementation is a pure, research-only package:

~~~text
operator bounded reduced row
        |
        v
build_event / strict schema validation
        |
        +--> stable event key
        +--> normalized semantic hash
        +--> manifest/checkpoint lineage
        |
        v
versioned NORMALIZED_SEMANTIC_DATASET artifact
        |
        +--> EVENT_EXCLUDED_RAW_V0 overlap evaluation
        +--> no OHLCV write
        +--> no Production publication
~~~

The code is at
[corporate_action_dataset.py](../../services/api/src/topicpilot_api/research/corporate_action_dataset.py).
It has no HTTP client, scheduler, SQL write, ORM mutation, or frontend
dependency.

## 6. CA-EVENT-SCHEMA-V0

The normalized event contract is CA-EVENT-SCHEMA-V0. Each row requires:

~~~text
source_name
official_product_or_surface
access_method
source_url
source_record_id_or_canonical_row_key
market_code
instrument_code
canonical_identity
event_type
announcement_date_if_available
primary_effective_date
reference_price_if_officially_returned
source_as_of_if_available
retrieved_at
source_content_hash_if_storage_permitted
normalized_semantic_hash
semantic_version
authority_state
query_or_export_manifest_id
checkpoint_id
reason_code
stable_event_key
~~~

Missing official fields remain null. The validator rejects guessed dates,
numeric coercion of nulls, non-finite prices, unknown fields, invalid official
hosts, unsupported event types, and mismatched hashes.

## 7. Storage Decision

The artifact is intentionally separate from raw source material:

~~~text
DATASET_STORAGE_TYPE=VERSIONED_LOCAL_RESEARCH_ARTIFACT
ARTIFACT_TYPE=NORMALIZED_SEMANTIC_DATASET
RAW_SOURCE_ARTIFACT=NOT_STORED
DEFAULT_ARTIFACT=REDUCED_SEMANTIC_EVENT_RECORD_PLUS_LINEAGE_AND_HASH
DATABASE_MUTATION=NO
PRODUCTION_TABLE=NO
~~~

The artifact is
[REC-A1-CA-EVENTS-V0.json](../../reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json).
It contains no OHLCV values, raw response body, adjusted price, or total
return field.

## 8. Dataset Version

~~~text
DATASET_SCHEMA_VERSION=rec-a1-corporate-action-research-dataset.v0
DATASET_VERSION=REC-A1-CA-EVENTS-V0
SEMANTIC_VERSION=CA-EVENT-SCHEMA-V0
REFERENCE_VERSION=tw-reference-v1
RESEARCH_WINDOW_START=2026-02-02
RESEARCH_WINDOW_END=2026-08-13
UNIVERSE_POLICY=LIFECYCLE_GATED_507
SOURCE_METHOD_VERSION=source-method-closure-2026-08-15
DATASET_CONTENT_HASH=bcb06d776bcd2dea1c3f4c0d0e3d11799bf5d5ff80848e832741c220bd974398
~~~

The content hash is computed over a canonical ordering of manifests,
checkpoints, events, and version metadata. Reordering these lists does not
change the dataset identity.

## 9. Source Method Matrix

| Exchange | Surface/method | Materialized rows | Coverage | Automation | Raw storage | Status |
|---|---|---:|---|---|---|---|
| TWSE | Official 2026-06-10 notice, bounded operator review | 1 | PARTIAL | MANUAL_OR_BOUNDED_QUERY_ONLY | Not stored | Ready for reduced semantic row |
| TWSE | tw-reference-v1 lifecycle authority | 1 | PARTIAL | CANONICAL_REFERENCE_BUNDLE | Existing hashed bundle only | Ready for known 6806 lifecycle |
| TWSE | Documented OpenAPI | 0 | Not used in this artifact | Conditionally allowed only for documented endpoints | Method-dependent | Not exercised |
| TWSE | Paid T48/E-Shop | 0 | Not authorized | Blocked absent entitlement | Not authorized | NOT_AUTHORIZED |
| TPEx | Official public query/export | 0 | UNKNOWN | AUTOMATED_EXTRACTION_BLOCKED | No artifact supplied | Bounded import contract only |

TPEX_ROWS=0 means zero rows were imported from a TPEx source. It does not
mean that TPEx has no corporate actions.

## 10. Identity Mapping

The validator loads the canonical
[tw-reference-v1 bundle](../../services/api/src/topicpilot_api/reference_data/bundles/tw-reference-v1)
and requires:

~~~text
IDENTITY_FORMAT=MARKET_CODE:INSTRUMENT_CODE
CURRENT_UNIVERSE=507_PHYSICAL_IDENTITIES
LIFECYCLE_POLICY=LIFECYCLE_GATED_507
~~~

Both materialized rows validate against the bundle:

~~~text
TPE:2330 -> TPE:2330
TPE:6806 -> TPE:6806
~~~

The implementation never infers a successor from company name, price,
nearest code, or same-code coincidence. Old/new identity discontinuities
remain fail-closed.

## 11. Event Effective-Date Semantics

primary_effective_date is the mechanical trading/effective date. It is
separate from announcement_date_if_available.

| Event | Primary effective date | Announcement/publication | Result |
|---|---|---|---|
| Cash dividend/ex-dividend | ex_dividend_date | 2026-06-10 for 2330 | 2026-06-11 event key |
| Stock dividend/ex-right | Official ex_right_date | Separate provenance | Contract supported; no row materialized |
| Rights/capital increase | Reference-price effective trading date | Separate provenance | Contract supported; no row materialized |
| Capital reduction | Resume/reference-price effective date | Separate announcement field | Contract supported; no row materialized |
| Listing/termination | Lifecycle effective date | Separate when available | 2026-06-23 for 6806 |

Announcement date is never substituted for the mechanical price or identity
boundary.

## 12. Manifest Contract

Each bounded acquisition/import manifest contains:

~~~text
manifest_id
source_name
source_method
official_surface
query_window_start
query_window_end
retrieved_at
source_as_of_if_available
record_count
content_hash_if_allowed
semantic_version
reference_version
status
~~~

The artifact contains two completed manifests:

~~~text
REC-A1-MANIFEST-TWSE-2330-20260815 -> 1 row, READY
REC-A1-MANIFEST-TWSE-6806-20260815 -> 1 row, READY
~~~

The absent TPEx operator artifact is represented in source_coverage as
TPEx.status=UNKNOWN; no empty-event row is fabricated.

## 13. Hash / Lineage Contract

Every event has source/product, access method, official URL, source record
identity, canonical identity, retrieval timestamp, manifest ID, checkpoint ID,
semantic version, authority state, stable key, and normalized semantic hash.

~~~text
HASH_LINEAGE_COMPLETE=YES_FOR_REDUCED_SEMANTIC_ROWS
SOURCE_CONTENT_HASH_POLICY=NULL_WHEN_RAW_NOT_STORED
2330_NORMALIZED_HASH=550ebefcd98af1645b7e737e1cc699131a55daa1ac361986c85128cc42fa4c20
6806_NORMALIZED_HASH=d869157ed9c89ab648a81350ad065d1a7f8123e56c22ae9400eb0b9b7050bc46
~~~

The 6806 row also carries the existing
instrument_lifecycles.json SHA-256. The 2330 PDF content hash is null
because the official raw response was not retained.

## 14. Replay Contract

Deterministic replay is claimed only when all of the following are unchanged:

~~~text
same source method
same source/export identity
same semantic version
same reference version
same manifest/query window
same lineage inputs
~~~

If an operator artifact cannot be re-obtained, replay is not a success; the
scope becomes CA_AUTHORITY_UNKNOWN. TPEx replay is not claimed because no
TPEx artifact was supplied.

~~~text
REPLAY_CONTRACT_READY=YES
REPLAY_EXECUTED=NO_FOR_TPEX
~~~

## 15. Checkpoint / Idempotence

Each manifest has a completed checkpoint whose event key set is sorted and
hashed. The stable event key is:

~~~text
source|market|instrument|event_type|primary_effective_date|source_record_id
~~~

The focused validation reruns the same semantic row and returns one reused
row with one duplicate input, without creating a second semantic identity.

~~~text
MANIFEST_IMPLEMENTED=YES
CHECKPOINT_IMPLEMENTED=YES
IDEMPOTENT=PASS_FOR_STABLE_EVENT_KEY
DUPLICATES=0_IN_VERSIONED_ARTIFACT
~~~

## 16. Event Family Coverage

The V0 contract covers:

~~~text
CASH_DIVIDEND_EX_DIVIDEND
STOCK_DIVIDEND_EX_RIGHT
RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET
CAPITAL_REDUCTION
~~~

Semantic partial families remain:

~~~text
SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE
MERGER_SHARE_CONVERSION_DEMERGER
LISTING_TERMINATION_RESUMPTION_DISCONTINUITY
~~~

The artifact materializes the cash-dividend control and one authoritative
known lifecycle control. It does not pretend that the other families have
complete 507-universe coverage.

## 17. Research Window Coverage

~~~text
RESEARCH_WINDOW=2026-02-02_TO_2026-08-13
WINDOW_RANGE_VALIDATION=PASS
TWSE_COVERAGE=PARTIAL
TPEX_COVERAGE=UNKNOWN
CURRENT_507_SURVIVORSHIP_SAFE=NO
~~~

The artifact's event-date range is 2026-06-11 through 2026-06-23.
This is the range of materialized events, not a claim that every day,
identity, or event family in the research window was queried.

## 18. Unknown / Fail-Closed Semantics

The implementation distinguishes:

~~~text
PASS_NO_EVENT =
query completed
AND source authority sufficient
AND requested scope explicit
AND response semantics prove empty

otherwise = CA_AUTHORITY_UNKNOWN
~~~

Missing TPEx artifact, failed query, ambiguous response, incomplete identity,
or unproven historical completeness never becomes PASS_NO_EVENT.

~~~text
UNKNOWN_FAIL_CLOSED=YES
PASS_NO_EVENT_CONTRACT=IMPLEMENTED_AND_TESTED
UNKNOWN_ROWS=0
~~~

UNKNOWN_ROWS=0 is a count of materialized normalized event rows, not a claim
that the unmaterialized coverage has no unknown scope.

## 19. EVENT_EXCLUDED_RAW_V0 Overlap Engine

evaluate_episode implements the predecessor's four post-hoc stages:

| Stage | Rule | Output |
|---|---|---|
| Feature dependency | Effective event date is within feature dependency through signal date | PRE_SIGNAL_FEATURE_CONTAMINATION |
| Trigger window | Event date is one of the frozen trigger bars | TRIGGER_WINDOW_CONTAMINATION |
| Execution/open | Event date equals the exact execution date | EXECUTION_CONTAMINATION |
| Outcome | Event date is in entry through T+10/MFE/MAE dates | OUTCOME_CONTAMINATION |

An unknown-authority event emits CA_AUTHORITY_UNKNOWN as its event reason.
The engine returns an exclusion record only; it does not mutate Gate, Rank,
Trigger, Entry, signal date, or execution facts.

~~~text
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
EVENT_EXCLUDED_RAW_POLICY=READY
EXCLUDED_EPISODE_IS_NOT_LOSS=YES
EXCLUDED_EPISODE_IS_NOT_NO_TRIGGER=YES
EXCLUDED_EPISODE_IS_NOT_IN_OUTCOME_DENOMINATORS=YES
~~~

## 20. Control Cases

### Control A — TPE:2330

~~~text
IDENTITY=TPE:2330
ANNOUNCEMENT_DATE=2026-06-10
PRIMARY_EFFECTIVE_DATE=2026-06-11
REASON_CODE=CA_EX_DIVIDEND
CONTROL_2330=PASS
~~~

The source record is the official
[TWSE notice](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69e6379f4019eb0d0cfa601e0.pdf).
The effective date is not replaced by the announcement date, and the
overlap engine maps the event to EVENT_EXCLUDED_RAW_V0 without entering
trading decision logic.

### Control B — TPE:6806

~~~text
IDENTITY=TPE:6806
TERMINATION_EFFECTIVE_DATE=2026-06-23
LAST_RAW_OHLC_DATE=2026-06-22
POST_TERMINATION_ROWS=0
REASON_CODE=CA_LISTING_TERMINATION
CONTROL_6806=PASS
~~~

The dataset row is checked against the canonical lifecycle evidence and does
not create a synthetic OHLCV bar after termination.

### Semantic fixtures

~~~text
PRE_SIGNAL_FEATURE_CONTAMINATION=PASS
TRIGGER_WINDOW_CONTAMINATION=PASS
EXECUTION_CONTAMINATION=PASS
OUTCOME_CONTAMINATION=PASS
PASS_NO_EVENT=PASS
CA_AUTHORITY_UNKNOWN=PASS
SEMANTIC_FIXTURE_6=PASS
~~~

## 21. Dataset Statistics

All values below come from the artifact loader and canonical reference-bundle
validation, not estimates:

~~~text
DATASET_ROWS=2
TWSE_ROWS=2
TPEX_ROWS=0
UNKNOWN_ROWS=0
COVERED_IDENTITIES=2
COVERED_EVENTS=2
DATE_RANGE=2026-06-11_TO_2026-06-23
DUPLICATES=0
INVALID_IDENTITIES=0
INVALID_EFFECTIVE_DATES=0
MISSING_LINEAGE=0
SEMANTIC_HASH_COLLISIONS=0
~~~

These statistics describe the materialized artifact only. They do not close
the unmaterialized TPEx or full 507-universe coverage.

## 22. Validation

Validation performed:

~~~text
ARTIFACT_SCHEMA_VALIDATION=PASS
REFERENCE_BUNDLE_VALIDATION=PASS
IDENTITY_VALIDATION=PASS
EFFECTIVE_DATE_VALIDATION=PASS
NULLABLE_FIELD_PRESERVATION=PASS
AUTHORITY_STATE_VALIDATION=PASS
MANIFEST_VALIDATION=PASS
SEMANTIC_HASH_DETERMINISM=PASS
STABLE_EVENT_KEY=PASS
IDEMPOTENT_RERUN=PASS
DUPLICATE_DETECTION=PASS
UNKNOWN_FAIL_CLOSED=PASS
PASS_NO_EVENT_SEMANTICS=PASS
CONTROL_2330=PASS
CONTROL_6806=PASS
SEMANTIC_FIXTURE_6=PASS
FOCUSED_PYTEST=12_PASSED
RUFF=PASS
PYTHON_COMPILE=PASS
FULL_A1_BACKTEST=NOT_RUN
WALK_FORWARD=NOT_RUN
PARAMETER_SEARCH=NOT_RUN
~~~

G1/G2/G3/Post-Close Canary are preserved rather than rerun: this task has no
reference registry, provider runtime, historical OHLCV, persistence, or
Production mutation impact.

## 23. Remaining Gaps

1. No operator-provided bounded TPEx event artifact exists in this task;
   TPEX_COVERAGE=UNKNOWN.
2. TWSE coverage is not a complete 507-identity historical event archive.
3. Stock dividend, rights/capital increase, and capital-reduction rows are
   contract-supported but not materialized in this artifact.
4. Split/par-value and merger/conversion identity continuity remain
   SEMANTIC_PARTIAL.
5. PASS_NO_EVENT has been implemented as a strict contract, but no empty
   exchange query is asserted here because no complete TPEx query artifact was
   provided.

The minimum next task is:

~~~text
NEXT_RECOMMENDED_TASK=TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE
~~~

It must obtain or validate an operator-controlled bounded TPEx artifact
without changing the blocked automation boundary.

## 24. Freeze Gate

The freeze gate remains closed because the required event coverage and
research-window completeness are not yet sufficient:

~~~text
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_EXECUTED=NO
~~~

The implementation does satisfy the structural prerequisites for a bounded
artifact, including versioning, identity validation, effective-date
semantics, lineage, semantic hashing, manifests, checkpoints, idempotence,
unknown fail-closed behavior, overlap rules, and controls. It does not lower
the coverage gate.

## 25. Final Handoff

~~~text
TASK_ID=TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION
FINAL_STATUS=REC_A1_CORPORATE_ACTION_DATASET_IMPLEMENTED_WITH_COVERAGE_GAPS_FREEZE_BLOCKED
CANONICAL_PRE_SHA=6831cf3448506abea8e62e3790014d021b208868
CANONICAL_POST_SHA=LOCAL_TASK_COMMIT_SHA_REPORTED_AT_HANDOFF
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO
WORKTREE_CREATED=NO
WORKTREE_REMOVED=NOT_APPLICABLE

OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
DATASET_IMPLEMENTATION_AUTHORIZED=YES
DATASET_IMPLEMENTED=PARTIAL
DATASET_VERSION=REC-A1-CA-EVENTS-V0
DATASET_STORAGE_TYPE=VERSIONED_LOCAL_RESEARCH_ARTIFACT

RESEARCH_WINDOW=2026-02-02_TO_2026-08-13
UNIVERSE_POLICY=LIFECYCLE_GATED_507
REFERENCE_VERSION=tw-reference-v1

TWSE_SOURCE_METHOD=MANUAL_OR_BOUNDED_QUERY_ONLY_PLUS_CANONICAL_REFERENCE_BUNDLE
TPEX_SOURCE_METHOD=MANUAL_OR_BOUNDED_QUERY_ONLY_IMPORT_CONTRACT_NO_ARTIFACT
TWSE_COVERAGE=PARTIAL
TPEX_COVERAGE=UNKNOWN
AUTOMATED_EXTRACTION_TWSE=DOCUMENTED_OPENAPI_ONLY;NOT_USED_HERE
AUTOMATED_EXTRACTION_TPEX=BLOCKED
MANUAL_BOUNDED_INGESTION=TWSE_CONTROL_ROWS_READY;TPEX_IMPORT_CONTRACT_READY

COVERED_EVENT_FAMILIES=CASH_DIVIDEND_EX_DIVIDEND;STOCK_DIVIDEND_EX_RIGHT;RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET;CAPITAL_REDUCTION
MATERIALIZED_EVENT_FAMILIES=CASH_DIVIDEND_EX_DIVIDEND;LISTING_TERMINATION_CONTROL
SEMANTIC_PARTIAL_EVENT_FAMILIES=SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE;MERGER_SHARE_CONVERSION_DEMERGER;LISTING_TERMINATION_RESUMPTION_DISCONTINUITY

DATASET_ROWS=2
TWSE_ROWS=2
TPEX_ROWS=0
UNKNOWN_ROWS=0
COVERED_IDENTITIES=2
COVERED_EVENTS=2
DATE_RANGE=2026-06-11_TO_2026-06-23
DUPLICATES=0
INVALID_IDENTITIES=0
INVALID_EFFECTIVE_DATES=0
MISSING_LINEAGE=0
SEMANTIC_HASH_COLLISIONS=0

MANIFEST_IMPLEMENTED=YES
CHECKPOINT_IMPLEMENTED=YES
IDEMPOTENT=PASS
HASH_LINEAGE_COMPLETE=YES_FOR_REDUCED_SEMANTIC_ROWS
REPLAY_CONTRACT_READY=YES

UNKNOWN_FAIL_CLOSED=YES
PASS_NO_EVENT_CONTRACT=IMPLEMENTED_AND_TESTED
EVENT_EXCLUDED_RAW_POLICY=READY

CONTROL_2330=PASS
CONTROL_6806=PASS
SEMANTIC_FIXTURE_6=PASS

HISTORICAL_OHLCV_CHANGED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED

REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_EXECUTED=NO
NEXT_RECOMMENDED_TASK=TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE

REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
PROJECT_CONTEXT_UPDATED=NO
ROADMAP_UPDATED=NO
WORK_ORDERS_UPDATED=NO

APPLICATION_CODE_CHANGED=YES_RESEARCH_ONLY_PACKAGE
DATABASE_MUTATION=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO

G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS
~~~

The task stops here. It does not execute dataset/protocol freeze, walk-forward,
backtest, parameter search, Recommendation engine changes, scheduler,
deployment, or Production operations.

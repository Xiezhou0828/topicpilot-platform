# TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION

## Closure

```text
TASK_ID=TASK-TOPIC-DAILY-STATE-PIT-FORMAL-SCHEMA-AND-BOUNDED-MATERIALIZATION
FINAL_STATUS=COMPLETE / FORMAL_AUTHORITY_IMPLEMENTED_AND_BOUNDED_MATERIALIZED
CANONICAL_PRE_SHA=a69b1ec7b861e6163bf63e4a5dac10ce92e52a73
CANONICAL_POST_SHA=ad3d90c02161f183e6a7fa0aa13229138b8535b5
IMPLEMENTATION_COMMIT=ad3d90c02161f183e6a7fa0aa13229138b8535b5
REPORT_COMMIT=THIS_REPORT_COMMIT_RECORDED_IN_FINAL_HANDOFF
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
MIGRATION_CREATED=YES
MIGRATION_FROM=0029_task_data_ref_006e_instrument_lifecycle
MIGRATION_TO=0030_task_topic_daily_state_formal_authority
FORMAL_MAPPING_EARLIEST_DATE=2026-08-07
PRE_BOUNDARY_BACKFILL=NO
```

Authoritative baseline: `TASK-TOPIC-PIT-MEMBERSHIP-AND-DAILY-STATE-CONTRACT-CLOSURE.md`.
The contract was followed as written; no PIT, role, lifecycle, ranking, concentration,
recommendation, or CORE/Leader policy was invented.

## Authority and isolation

```text
PIT_MEMBERSHIP_AUTHORITY=effective-dated instrument_topic_relations + date-valid topic/instrument/market identity + reference lifecycle eligibility + active reference/session/calendar binding
PUBLICATION_MODES=FORMAL | RESEARCH_ONLY | SHADOW
FORMAL_FILTER_IMPLEMENTED=YES; FORMAL + PUBLISHED + non-superseded only
MEMBERSHIP_SNAPSHOT_IMPLEMENTED=YES
MEMBERSHIP_HASH_DETERMINISTIC=YES; stable across repeated dry-runs
MEMBER_FACT_REPLAY_IMPLEMENTED=YES; exact-date accepted canonical PRICE/VOLUME/TRADING_STATUS authority
IMMUTABLE_CORRECTION_IMPLEMENTED=YES; immutable snapshot identity + correction sequence + explicit supersedes/superseded state
```

The legacy/current-mapping writer is explicitly `RESEARCH_ONLY` and cannot query or
upsert formal rows. Formal topic read-model SQL uses an inner join to the latest formal
published snapshot, so topics without a formal published row are not exposed as formal.
Research reconstruction and shadow lifecycle values remain isolated.

```text
NO_TRADE_SEMANTICS=only accepted explicit NO_TRADE or EXCHANGE_CONFIRMED_NO_DATA; no accepted TRADING_STATUS rows existed in the bounded source set
UNKNOWN_SEMANTICS=missing accepted observation is UNKNOWN; absence is never converted to zero
IDENTITY_SEMANTICS=immutable instrumentId is bounded authority; absent security_identities do not imply historical symbol continuity
6806_CONTROL=excluded on every bounded date with DELISTED:TWSE-DELISTED-6806-20260623; never entered eligible membership
```

## Schema and materialization

Migration `0030` adds typed publication, membership, session/calendar, finality,
quality, coverage, lineage, correction, and immutable member-fact authority. Formal
strong/weak counts are nullable with no server default; deferred fields therefore stay
`NULL`, not synthetic zero. `metadata_payload` remains diagnostic only.

```text
MATERIALIZATION_DATES=2026-08-07, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13
TOPIC_SNAPSHOT_ROWS_BEFORE=0
TOPIC_SNAPSHOT_ROWS_AFTER=460
FORMAL_ROWS_WRITTEN=460 (92 topics x 5 dates)
RESEARCH_ROWS_WRITTEN=0
SHADOW_ROWS_WRITTEN=0
MEMBER_FACT_ROWS/ARTIFACTS=4235 rows (847 per date); deterministic fact hashes/artifacts
IDEMPOTENT_RERUN=YES; second run rowsBefore=460, rowsAfter=460, rowsWritten=0, idempotentRows=92 per date
DATABASE_MUTATION=LOCAL_CONTROLLED_ONLY
```

The date enumeration dry-run found the five dates above. Each date had 92 ready
topics; topics without date-valid relations were fail-closed and not written. No
pre-boundary date was enumerated or materialized.

## Derived policy state

```text
SCORE_GRADE_STATE=NULL / DEFERRED
PARTICIPATION_STATE=RAW_COUNTS_AND_COVERAGE_ONLY
BREADTH_STATE=DEFERRED
LEADERSHIP_STATE=UNAVAILABLE
CONCENTRATION_STATE=DEFERRED
RANKING_STATE=DEFERRED
LIFECYCLE_STATE=SHADOW_ONLY/UNPUBLISHED
```

Final local audit: 460/460 snapshots are `FORMAL/PUBLISHED`, 0 are pre-boundary,
0 are `RESEARCH_ONLY`, 0 are `SHADOW`, all strong/weak fields are `NULL`,
`noTradeCount=0`, and all 4,235 member facts are `OBSERVED`. This does not mean
Lifecycle production is ready.

## API and generated contracts

```text
OPENAPI_CHANGED=YES
GENERATED_CLIENT_CHANGED=YES
FRONTEND_CHANGED=NO (generated API declaration synchronized; no frontend source change)
```

Validated HTTP readback from the temporary local API image:

- `/api/v2/topic-snapshots?date=2026-08-07` returned 92 formal `PIT_FORMAL` rows with lineage hashes and nullable deferred fields.
- `/api/v2/topic-snapshots?date=2026-08-06` returned zero rows with `UNAVAILABLE_PRE_FORMAL_BOUNDARY`.
- `/api/v2/topics` returned 92 formal topics, excluding topics without formal published snapshots.
- Research/shadow rows were not visible to either formal consumer.

## Validation

```text
MIGRATION_UPGRADE_DOWNGRADE=PASS; 0029 -> 0030 -> 0029 -> 0030
BOUNDARY_AND_HASH_TESTS=PASS
6806_LIFECYCLE_EXCLUSION_TEST=PASS
DUPLICATE_OVERLAP_FAIL_CLOSED=IMPLEMENTED_AND_UNIT-COVERED
NO_TRADE_VS_UNKNOWN=IMPLEMENTED; source had zero accepted TRADING_STATUS rows
MISSING_NOT_ZERO=PASS
MEMBERSHIP_HASH_STABILITY=PASS
MEMBER_FACT_ARTIFACT_DETERMINISM=PASS
IMMUTABLE_CORRECTION_SUPERSESSION=PASS; unit-covered
IDEMPOTENT_RERUN=PASS
FORMAL_RESEARCH_SHADOW_ISOLATION=PASS
TOPIC_SNAPSHOT_ENGINE_READ_MODEL_API=PASS
OPENAPI_GENERATED_CLIENT_CONSISTENCY=PASS
FOCUSED_BACKEND_TESTS=9 passed
API_CLIENT_TESTS=3 passed
RUFF=PASS
PYTHON_COMPILE=PASS
OPENAPI_DRIFT_CHECK=PASS
DIFF_CHECK=PASS
SECRET_SCAN=NO_HIGH_RISK_LITERAL_MATCHES
```

```text
G1=PRESERVED PASS / NOT RERUN
G2=PRESERVED PASS / NOT RERUN
G3=PRESERVED PASS / NOT RERUN
POST_CLOSE_CANARY=PRESERVED PASS / NOT RERUN
```

The preserved gates were not rerun because this task did not change the provider,
reference bootstrap, or existing post-close canary authority; it only consumed those
authorities and added the formal snapshot boundary.

```text
HISTORICAL_OHLCV_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
NEXT_RECOMMENDED_TASK=Formal Topic Map publication/read-model closure or Lifecycle SHADOW replay, as a separate explicitly authorized task
```

No next task was started.

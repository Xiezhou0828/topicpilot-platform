# TASK-021 bounded follow-up — corporate-action authority and checkpoint observability

## Candidate disposition

This is an implementation candidate based on the exact TASK-024 canonical
baseline. It is not a Production release, a recovery, a replay, or a claim
that TASK-021 has been resolved.

```text
TASK_ID=TASK-021-BOUNDED-FOLLOW-UP-CORPORATE-ACTION-AND-CHECKPOINT
TASK_TYPE=bounded implementation follow-up
REQUIRED_TERMINAL_STATE=IMPLEMENTED_CANDIDATE_READY
ACHIEVED_TERMINAL_STATE=IMPLEMENTED_CANDIDATE_READY
TASK_STATUS=IMPLEMENTED_CANDIDATE_READY
TASK_COMPLETE=YES_FOR_IMPLEMENTATION_SCOPE_ONLY
TASK_021_RESOLVED_BY_NEW_TASK=NOT_PROVEN_UNTIL_PRODUCTION_VALIDATION
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Canonical reconciliation, release, runtime verification, and any production validation remain separately authorized steps.
FINAL_CANONICAL_MAIN_SHA=5ff2a91c5fad39d50434a3187011d93abcc058e3
SOURCE_BASE_SHA=5ff2a91c5fad39d50434a3187011d93abcc058e3
CANONICAL_STATUS=NOT_CANONICALIZED
RELEASE_STATUS=NOT_RELEASED
PRODUCTION_VERIFICATION=NOT_PERFORMED
CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION
OWNER_DECISION_REQUIRED=NO
```

## Root-cause follow-up status

```text
TASK_021_ROOT_CAUSE_PART_1_STATUS=REMEDIATED_IN_IMPLEMENTATION_CANDIDATE
TASK_021_ROOT_CAUSE_PART_2_STATUS=REMEDIATED_IN_IMPLEMENTATION_CANDIDATE
CORPORATE_ACTION_AUTHORITY_STATUS=GENERIC_TWSE_TPEX_OFFICIAL_SNAPSHOT_ADAPTER_CONNECTED
2601_STATUS_ON_2026_09_30=SUSPENDED
RECONCILIATION_CONSUMES_RESOLVED_STATUS=YES
CHECKPOINT_SEMANTICS_STATUS=SEPARATED_PROVIDER_INGESTION_PERSISTENCE_FLOW_READBACK_FORMAL_PUBLICATION
NESTED_READBACK_REASON_STATUS=PASS_SANITIZED_NESTED_FAILURE_REASON
```

Part 1 is the missing formal corporate-action authority path. The candidate
adds a typed TWSE/TPEx official corporate-action adapter and a sanitized,
effective-dated snapshot boundary. It is event-type driven, not a permanent
2601-only code path. Capital reduction resolves to `SUSPENDED` with
`CAPITAL_REDUCTION_TRADING_SUSPENSION`; the exact 2601 interval is
2026-09-23 through 2026-10-03 with resume date 2026-10-05.

The resolver gives active corporate-action authority precedence over an
ordinary same-session close and lifecycle-only authority, while conflicting
active corporate-action records remain `UNKNOWN` and fail closed. Legitimate
unavailable instruments remain in the universe, retain a null current close,
are excluded from priced counts, and do not block the existing formal gate.
Unknown, provider-error, date-mismatch, missing-authority, and official
available-without-close states remain blocking according to the existing
publication semantics. No unknown-to-topic-only publication change was made,
so no Owner decision was required.

Part 2 is the checkpoint ambiguity. The candidate separates the durable
checkpoints into `MARKET_FACTS_PROVIDER_INGESTION`,
`MARKET_FACTS_PERSISTENCE`, `INSTITUTIONAL_FLOW_READBACK`, and the existing
`FORMAL_MARKET_FACTS:OFFICIAL` publication checkpoint. The latter is explicitly
marked `FORMAL_MARKET_FACTS_PUBLICATION` and is no longer a provider-ingestion
checkpoint. Actual provider request counts are recorded when calls are made;
non-provider checkpoints use the existing JSON metadata boundary with
`providerMetrics.applicable=false` and a null request count. The legacy
non-null ORM column remains physically compatible by storing its required
sentinel, but forensic output never interprets that sentinel as an applicable
provider metric. A zero request count is emitted only for the provider
ingestion checkpoint before any provider call, where no call has been made.

Forensic readback retains only sanitized nested failure reason fields:
readback status, reason code, institutional-flow status, market-facts
publication status, failed section, and failure classification. Credentials,
private URLs, and sensitive Production payloads are not exposed.

## Required 2601 boundary matrix

The unit and reconciliation fixtures cover these date boundaries only; no
Worker, POST_CLOSE, recovery, retry, replay, or Production read/write action
was performed for 2026-09-30.

| Trading date | Resolver result | Price treatment |
|---|---|---|
| 2026-09-22 | `AVAILABLE` | A supplied same-session close remains the price evidence. |
| 2026-09-23 | `SUSPENDED`, capital-reduction reason | Current close remains null. |
| 2026-09-30 | `SUSPENDED`, capital-reduction reason | No close is added, zero-filled, or forward-filled. |
| 2026-10-03 | `SUSPENDED`, capital-reduction reason | Current close remains null. |
| 2026-10-05 | `AVAILABLE` | A supplied same-session close is eligible. |

## Validation evidence

```text
FOCUSED_TEST_STATUS=PASS_130
BACKEND_TEST_STATUS=PASS_999_SKIP_60_FAIL_0
TEST_COUNT_PRE=1046
TEST_COUNT_POST=1059
PASS_PRE=986
PASS_POST=999
SKIP_PRE=60
SKIP_POST=60
FAIL_PRE=0
FAIL_POST=0
TEST_COUNT_DELTA=+13
TEST_COUNT_DELTA_REASON=The candidate adds 13 bounded corporate-action, reconciliation, checkpoint, and forensic-readback tests; existing discovery and skip set are unchanged.
TEST_COUNT_DELTA_STATUS=PASS
BASELINE_FAILURE_ATTRIBUTION=No baseline or candidate failures; FAIL_PRE=0 and FAIL_POST=0.
```

Checks completed:

- Focused resolver, corporate-action, availability, reconciliation, scheduler,
  post-close, runtime, daily-forward, and forensic tests: `130 passed`.
- Full backend suite from the exact baseline and candidate worktree:
  candidate `999 passed, 60 skipped, 0 failed`; the 60 skips require an
  explicit PostgreSQL test database and are unchanged from the baseline.
- Ruff on all changed Python source and test files: passed.
- Python compile check on all changed source files: passed.
- `git diff --check`: passed.
- Alembic graph: one existing head,
  `0047_task_topic_role_strength_design_freeze`.
- OpenAPI drift check against the committed baseline: passed. No OpenAPI or
  generated API contract file changed.
- Generated API client tests: `4 passed`.

No migration is needed: no ORM schema or migration file changed, and the
existing JSON metadata representation is sufficient for the nullable/N/A
provider-metric semantics at the readback boundary.

## Scope and safety invariants

```text
MIGRATION_REQUIRED=NO
MIGRATION_ID=NONE
PRODUCTION_DB_MUTATED=NO
PRODUCTION_DEPLOYED=NO
POST_CLOSE_RETRIED=NO
HISTORICAL_BACKFILL=NO
RECOVERY_PERFORMED_BY_THIS_TASK=NO
API_DEPLOYED=NO
WEB_DEPLOYED=NO
SCHEDULER_ACTIVATED=NO
NEXT_TASK_CHANGED=NO
TOPIC_SCORE_CHANGED=NO
GRADE_CHANGED=NO
LIFECYCLE_CHANGED=NO
LEADER_CHANGED=NO
STRUCTURAL_ROLE_CHANGED=NO
TODAY_UI_CHANGED=NO
OPPORTUNITY_CHANGED=NO
WHOLE_MARKET_DISTRIBUTION_CHANGED=NO
```

The canonical TASK-024 schedule remains unchanged at `13:45 Asia/Taipei` in
the existing runtime default and `render.yaml`; this follow-up does not edit
that schedule. No deployment, push, merge, Production database mutation,
POST_CLOSE execution, retry, historical backfill, or `NEXT_TASK` modification
was performed.

## Changed source surface

- `services/api/src/topicpilot_api/market_data/corporate_action_authority.py`
  and its sanitized authority snapshot: official corporate-action source
  boundary and generic normalization.
- `services/api/src/topicpilot_api/trading_status_authority.py`: corporate
  action authority class, effective/resume dates, precedence, conflict
  handling, and operator readback fields.
- `services/api/src/topicpilot_api/daily_market.py`: reconciliation and formal
  readiness consume the resolved authority.
- `services/api/src/topicpilot_api/live/post_close.py`: authority injection and
  separated market-facts checkpoints.
- `services/api/src/topicpilot_api/production_forensic_readback.py`: safe
  provider-metric interpretation and nested failure readback.
- Bounded unit and forensic tests covering the required matrix.

The candidate is ready for a separately authorized canonical reconciliation;
it is not itself canonicalized or released.

# TASK-BE-021A Topic Lifecycle Shadow Replay & Calibration Readiness Report

**Date:** 2026-08-12
**Scope:** Lifecycle shadow replay, PM review contract, calibration export, and
representative-case readiness
**Activation:** No production lifecycle activation

## 1. Executive Summary

TASK-BE-021A extends the completed lifecycle shadow engine with deterministic
calibration tooling. It does not change the five PM-frozen stage meanings,
threshold policy, state machine, persistence authority, FastAPI contract, or
frontend behavior.

The new review projection exposes every evidence group needed for PM review,
blank PM judgement fields, replay summary counts, deterministic representative
case selection, and JSON/CSV/Markdown export. It reads only persisted `SHADOW`
rows generated from canonical accepted DAILY_BAR observations, effective-dated
membership, and formal topic snapshots.

The current repository/live audit still finds no formal replay dates: the public
service has zero topic snapshot rows and no accepted observation coverage. The
tooling is therefore ready for review, while `FORMAL_REPLAY_DATA` remains
`WAITING`, `HISTORICAL_REPLAY` remains `BLOCKED_BY_DATA`, and production
activation remains off.

## 2. Existing Engine Audit

The audit re-read:

- `topic_lifecycle_engine.py` and `LifecyclePolicy`;
- `topic_lifecycle_cli.py`;
- canonical evidence selection in `topic_snapshot_engine.py`;
- `TopicSnapshot`, `TopicLifecycleResult`, and combined migration `0027`;
- post-close orchestration and retry-safe shadow persistence;
- lifecycle API schema/read model and Topic List/Detail rendering;
- lifecycle product/architecture/report/worklog documents;
- lifecycle unit/contract/snapshot/freeze/observation tests.

The audit confirms the prior engine already implements stage semantics,
transition confirmation, hysteresis, Day N, re-entry, insufficient-data holds,
evidence groups, policy lineage, and `evaluation_mode=SHADOW`. TASK-BE-021A adds
only a review projection over those facts.

## 3. Calibration Objective

The objective is to make persisted shadow evidence reviewable by PMs without
letting the review surface invent observations, fill missing values, derive a
stage in the client, or write production semantic decisions.

The review projection is versioned as
`topic-lifecycle-calibration-review.v1`. It is deterministic for a fixed set of
persisted rows and policy version.

## 4. PM Review Contract

Each `LifecycleCalibrationRecord` contains:

- identity: topic ID, topic key/slug, display name, evaluation date;
- result: previous/candidate/final stage, transition decision/reason, stage
  entry date, and Day N;
- participation: expected members, observed members, coverage, positive breadth,
  and sample confidence;
- group strength: average member change, strong breadth, and weak ratio;
- leadership: role-semantic availability, leader/proxy member, change, and full
  leadership evidence;
- persistence: previous candidate, candidate streak, and confirmation state;
- status/lineage: evaluation status, data status, confidence, policy version,
  and calculation version;
- blank PM fields: `PM_EXPECTED_STAGE`, `PM_RESULT`, and `PM_NOTE` (with stable
  lowercase JSON/CSV aliases `pm_expected_stage`, `pm_result`, and `pm_note`).

The engine never writes PM fields. If a reviewer later supplies a result, the
allowed values are `MATCH`, `TOO_EARLY`, `TOO_LATE`, `TOO_STRONG`, `TOO_WEAK`,
`WRONG_STAGE`, and `INSUFFICIENT_EVIDENCE`.

## 5. Calibration Export

The operator command supports:

```text
topicpilot-lifecycle --replay --export --format json
topicpilot-lifecycle --replay --export --format csv
topicpilot-lifecycle --replay --export --format markdown --representatives
```

`--date YYYY-MM-DD` scopes a review to one formal snapshot date. `--topic`
scopes exported records to one topic key. `--output PATH` writes the selected
format; without it the result is emitted to stdout.

JSON contains the complete records, summary, policy/review versions, and (when
requested) representative cases. CSV contains one stable row per persisted
result, including PM placeholders and JSON-encoded evidence columns. Markdown
contains replay summary, stage distribution, representative-case table, and
human-readable per-record evidence.

No export path calls Yahoo, Google Sheets, frontend preview data, or a fixture
market source.

## 6. Representative Case Selection

Selection is deterministic: candidates are ordered by confidence descending,
coverage descending, evaluation date ascending, topic key, then topic ID. The
tool returns one record or an explicit `found=false` result for each category:

1. SPROUTING;
2. FERMENTING;
3. MAIN_RISE;
4. MATURE;
5. DECLINING;
6. transition candidate;
7. confirmed transition;
8. strong jump;
9. strong decline;
10. MATURE -> MAIN_RISE re-entry;
11. insufficient data;
12. small sample.

Missing cases are reported as missing. They are never filled with synthetic
market results.

## 7. Formal Replay Status

The replay path remains the existing `topicpilot-lifecycle --replay` path. It
walks distinct `TopicSnapshot.snapshot_date` values in ascending order, uses the
same canonical evidence and effective membership authority as the engine,
preserves the active provisional policy version, and does not fabricate
intermediate stage history.

When no snapshot dates exist, the CLI emits `BLOCKED_BY_DATA` and an empty
review record set. When rows exist, the export includes all persisted lifecycle
results for the evaluated dates and reports replay counts from those rows.

## 8. Replay Summary

The summary contains trading dates, date count, topics evaluated, result count,
stage distribution including `PENDING`, transition decision counts, pending
confirmation count, insufficient-data count, strong jump/decline counts,
MATURE-to-MAIN_RISE re-entry count, and coverage min/max/average.

It also exposes machine-readable readiness fields:

```text
formalReplayData = READY | WAITING
historicalReplay = PASS | BLOCKED_BY_DATA
pmCalibration = READY_FOR_REVIEW | WAITING_FOR_DATA
```

## 9. Stage Distribution

Stage distribution is calculated only from persisted final stages. A row without
a final stage is counted as `PENDING`; it is not coerced to SPROUTING. This
preserves the distinction between missing evidence and a real lifecycle stage.

## 10. Transition Analysis

Transition counts use persisted transition decisions and previous/final stages.
Strong jump and strong decline counts require the engine's explicit
`JUMP_TRANSITION` decision; candidate breadth alone cannot turn a row into a
strong signal in the report. Re-entry counts require persisted
`MATURE` -> `MAIN_RISE` state.

## 11. Leadership Proxy Status

The export carries `leaderSemanticAvailable`, leader/proxy ID, role, and change
inside the leadership evidence. Current relation data does not provide an
approved leader/core semantic, so the engine's strongest-observed-member proxy
remains clearly labelled. Calibration review can compare `PROXY` evidence with a
future official role authority without rewriting old rows.

## 12. Threshold Policy Status

All numeric values remain in `LifecyclePolicy` and remain
`PROVISIONAL_TUNABLE`. No calibration tool optimizes, searches, or rewrites
thresholds. A future policy change must use a new policy version rather than
overwrite `topic-lifecycle-policy.provisional.1` rows.

## 13. PM Calibration Readiness

The repository contract is `READY_FOR_REVIEW` when persisted replay rows exist.
The current external data state is `WAITING_FOR_DATA`; there are no formal dates
to review, no representative market cases to select, and no PM judgement to
claim.

## 14. Production Activation Gate

Activation remains gated on all of the following:

1. DATA-022/022A formal daily pipeline and downstream-ready contract;
2. accepted official daily observations, including trading-status/no-trade
   coverage;
3. topic snapshots on multiple formal trading dates;
4. deterministic shadow replay;
5. PM review of representative cases;
6. calibration decision with a new policy version if required;
7. API and Sites reconciliation.

The repository contains canonical trading-status observation models and the
accepted DAILY_BAR path, but no DATA-022/022A task document was present in this
worktree and no live formal observations were available during this audit. This
task does not implement DATA-022/022A.

## 15. Tests

Added deterministic tests cover:

- complete review-contract field mapping;
- blank PM fields and allowed review surface shape;
- replay/stage/transition/coverage summary counts;
- missing representative cases without synthetic substitution;
- small-sample selection;
- stable JSON, CSV, and Markdown export.

Targeted lifecycle/calibration/contract/snapshot/freeze/observation tests pass
(30 passed in the final targeted run). Existing broad backend and
frontend suites retain unrelated baseline failures documented in the prior
TASK-BE-021 report; the final broad backend run was 256 passed, 31 skipped, and
36 unrelated baseline failures. No production deployment or database write was
performed.

## 16. Files Changed

- `services/api/src/topicpilot_api/topic_lifecycle_calibration.py`
- `services/api/src/topicpilot_api/topic_lifecycle_cli.py`
- `services/api/tests/test_topic_lifecycle_calibration.py`
- `docs/product/TOPICPILOT_TOPIC_LIFECYCLE_SPEC.md`
- `docs/architecture/TOPICPILOT_V2_PRODUCTION_DATA_ARCHITECTURE.md`
- `docs/AI_WORKLOG.md`
- `docs/WORK_ORDERS.md`
- this report

## 17. Documents Updated

The lifecycle product spec now documents the PM review contract and export
formats. The architecture document records the calibration boundary. The worklog
and work-order register record TASK-BE-021A. The actual `NEXT_TASK` file was not
modified.

## 18. Known Issues

- No DATA-022/022A task document or formal observation dates are available in
  this worktree/live environment.
- No real representative topic can be named until formal replay rows exist.
- Official leader/core role metadata remains deferred; current evidence may use
  a proxy.
- PostgreSQL-backed replay integration requires a configured database URL.

## 19. Risks / Technical Debt

- PM labels are intentionally external and are not yet persisted as production
  semantic facts.
- Threshold calibration remains a human decision; automatic tuning is out of
  scope.
- A later activation task must re-run API/Sites reconciliation after migration
  and observation ingestion.

## 20. Final Acceptance Matrix

| Requirement | Result | Evidence |
|---|---|---|
| Lifecycle product meaning | FROZEN | Existing lifecycle product spec and TASK-BE-021 audit |
| Engine reuse/no semantic drift | PASS | Calibration projection reads persisted SHADOW rows only |
| PM review contract | PASS | `LifecycleCalibrationRecord` and blank PM fields |
| Calibration export | PASS | JSON, CSV, Markdown exporters and CLI flags |
| Representative selection | PASS | Twelve deterministic categories with explicit missing cases |
| Replay summary | PASS | Stage/transition/coverage/readiness summary builder |
| Formal replay data | WAITING | No formal snapshot dates in live readback |
| Historical replay | BLOCKED_BY_DATA | No accepted observations/topic snapshots |
| PM calibration | WAITING_FOR_DATA | No review rows available externally |
| Thresholds | PROVISIONAL_TUNABLE | Central `LifecyclePolicy`, no auto-tuning |
| Production activation | NO | No deploy/write/flag/semantic overwrite |
| NEXT_TASK | NO MODIFICATION | No NEXT_TASK file changed |

## 21. Suggested NEXT_TASK

After DATA-022/022A produces multiple formal trading dates, run the bounded
Markdown/JSON replay export, review the twelve representative categories, attach
PM expected stage/result/note labels outside the engine, and decide whether a
new policy version is warranted. Keep production activation as a separate gate;
Recommendation Engine and Opportunity Engine remain out of scope.

## Final Status Markers

```text
LIFECYCLE_PRODUCT_DEFINITION = FROZEN
LIFECYCLE_ENGINE = PASS
CALIBRATION_REVIEW_CONTRACT = PASS
CALIBRATION_EXPORT = PASS
REPRESENTATIVE_CASE_SELECTION = PASS
FORMAL_REPLAY_DATA = WAITING
HISTORICAL_REPLAY = BLOCKED_BY_DATA
PM_CALIBRATION = WAITING_FOR_DATA
LIFECYCLE_THRESHOLDS = PROVISIONAL_TUNABLE
LIFECYCLE_PRODUCTION_ACTIVATION = NO
NEXT_TASK_MODIFIED = NO
```

# TASK-POST-CLOSE-FLOAT-CANONICALIZATION-RUNTIME-FAILURE-RECONCILIATION-001

## 1. Executive Summary

The Production failure is confirmed and reproducible. It is not a provider,
date, corporate-action, or business-policy failure. The failure occurs while
the terminal POST_CLOSE run is constructing the immutable publication-receipt
hash:

`PostCloseUpdater._finish()` → `append_receipt_for_run()` →
`normalizer.stable_hash()` → `_canonical()`.

`DailyMarketReconciliation.to_dict()` emits the legitimate finite metrics
`coveragePct` and `coveredCoveragePct` as Python `float` values. The receipt
feature routes that bounded read-model payload through the shared normalizer,
whose contract intentionally rejects Python floats. The failed Production run
therefore aborts closed at receipt hashing with:

`TypeError: unsupported canonical value: float`

The remediation is limited to the receipt hash boundary. Finite floats are
converted through `Decimal(str(value))` before the existing deterministic
normalizer is called. Non-finite floats still fail closed. The shared global
normalizer is unchanged.

## 2. Governance Boundary

- No Production deployment, DB write, migration, scheduler mutation, manual
  POST_CLOSE, recovery, publication, 2026-10-05 touch, Preview mutation,
  push, merge, or NEXT_TASK mutation was performed.
- Implementation worktree: `E:\TopicPilot\w\pcf001`.
- Protected Preview worktree was not entered or modified.
- The original Production failed execution remains the latest read-only
  authority and its receipt remains absent.

## 3. Repository / Git Lineage

- `origin/main`: `e97f590cad497c0a23fb027fce39ec5891ea4bc1` (unchanged on final
  readback).
- Research/release base: `dd7fa597cdc66243f80df1f8ad6d4b6dd7f82c8e`.
- TASK-005 implementation: `c610f86302504bba1df4529b8461bbce7042d201`.
- TASK-005 evidence closure: `876489301a8b243e71c19097b428d20b4e2fa231`.
- Runtime implementation commit: `edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91`.
- Candidate branch: `codex/post-close-float-canonicalization-reconciliation-001`.
- The runtime commit is a direct descendant of `dd7fa59`, which is a direct
  descendant of TASK-005 evidence closure. TASK-005 is therefore an ancestor
  of this candidate; no separate release composition commit is required.

## 4. Production Baseline

Final read-only Production readback on 2026-10-06:

- API SHA: `6fff533168b1823052071f6d88d1f266397d327d`.
- Worker SHA: `6fff533168b1823052071f6d88d1f266397d327d` (preserved Render
  runtime readback).
- Alembic head: `0049_task_daily_formal_publication_receipt`.
- Scheduler: configured and active by current heartbeat/last-run readback;
  `postCloseStart=13:45`, `softTarget=14:30`, `hardDeadline=15:00`,
  timezone `Asia/Taipei`. No competing scheduler was identified in the
  preserved forensic readback.
- G2 reference: `tw-reference-v1-rollover-0578862f98914eb7`.
- Final API `/healthz` and `/readyz`: HTTP 200, both reporting the Production
  API SHA above.

## 5. Failed POST_CLOSE Execution

- Execution ID: `06d44574-214e-539d-ada4-dbf73d9eb971`.
- Session date: `2026-10-06`.
- Started: `2026-10-06T05:46:21.097285Z`.
- Completed: `2026-10-06T05:56:27.517615Z`.
- Requested count: `553`.
- Status: `FAILED`.
- Failure code: `POST_CLOSE_FINALIZATION_FAILED`.
- Failure message: `TypeError: unsupported canonical value: float`.
- Provider status: `ERROR`; freshness: `PARTIAL`.
- Final readback still reports no receipt for 2026-10-06 and no receipt for
  2026-10-05.

The public Production surface does not expose a full traceback or checkpoint
listing. The equivalent evidence is the exact exception, the deployed source
at the exact Production SHA, the deterministic call path below, and the
sanitized local reproduction.

## 6. Exact Failure / Pipeline Stage

The deployed 6fff source contains the same receipt path and the same shared
canonicalizer. The failure path is:

1. `DailyMarketReconciliation.to_dict()` creates the reconciliation read
   model.
2. `_finish()` places that read model in `hash_material` for the receipt.
3. `append_receipt_for_run()` calls `stable_hash(hash_material)`.
4. `normalizer.contracts._canonical()` has no Python-float case and raises
   `TypeError`.

Classification:

- `POST_CLOSE_STAGE_REACHED=FINAL_PUBLICATION/COMPLETION`.
- `POST_CLOSE_STAGE_FAILED=RECEIPT_HASHING`.
- `UPSTREAM_STAGES_COMPLETED=run claim, input/readiness checkpoints, market
  collection/finalization path entered; terminal receipt and completion
  checkpoint did not complete`.
- Pipeline layer: `RECEIPT` / `HASHING` / deterministic serialization.
- This is a valid calculation rejected by an incorrectly routed canonical
  representation, not a provider-date or finality authority failure.

## 7. Failed Semantic Field and Type Provenance

- Semantic fields: `coveragePct` and `coveredCoveragePct` in the daily-market
  reconciliation read model.
- Raw inputs: integer counts (`priced_count`, `covered_count`,
  `expected_count`).
- Introduction point: Python division and `round()` in
  `DailyMarketReconciliation.coverage_pct` and
  `DailyMarketReconciliation.covered_coverage_pct`; `to_dict()` exposes the
  resulting values as `float`.
- Example sanitized value: `99.8192` (`float`).
- Value class: ordinary finite float.
- Non-finite value involved: `NO`; NaN, +Infinity, and -Infinity are not the
  Production failure shape.
- Expected canonical type at this boundary: finite `Decimal` converted by the
  existing normalizer to its scale-independent canonical decimal string.
- Value source: in-process reconciliation metric derived from integer counts,
  not provider JSON, SQL `DOUBLE PRECISION`, pandas, numpy, a symbol-specific
  fixture, or a manual cast.
- Canonicalizer before fix:
  `topicpilot_api.normalizer.contracts.stable_hash` → `canonical_json` →
  `_canonical`.

## 8. Local Reproduction

Before the fix, the following 3.12 reproduction produced the same exception:

```powershell
$env:PYTHONPATH='services/api/src'
& 'C:\Users\acer\Desktop\題材領航\topicpilot-api-venv-003b-20260813\Scripts\python.exe' -c "from datetime import date; from topicpilot_api.daily_market import assess_daily_coverage; from topicpilot_api.normalizer.contracts import stable_hash; r=assess_daily_coverage(trade_date=date(2026,10,6), expected_by_market={'TPE':500,'TWO':53}, observed_by_market={'TPE':500,'TWO':53}, priced_by_market={'TPE':499,'TWO':53}, covered_by_market={'TPE':499,'TWO':53}); p=r.to_dict(); print([(k,v,type(v).__name__) for k,v in p.items() if k.endswith('Pct')]); stable_hash({'reconciliation':p})"
```

Observed before-fix result included:

`coveragePct=99.8192 (float)` and
`TypeError: unsupported canonical value: float`.

After the fix, the same semantic payload crosses the actual
`append_receipt_for_run()` boundary and produces a receipt hash. The shared
global `stable_hash({"coveragePct": 99.8192})` still rejects the float.

## 9. Root Cause and TASK-005 Relationship

Root cause is proven: the daily formal publication receipt implementation
introduced a receipt hash material path that included reconciliation float
metrics, while reusing a normalizer contract intentionally limited to
`None`, booleans, integers, strings, `Decimal`, dates/times, UUIDs, mappings,
and sequences. The receipt path lacked a bounded numeric adapter and lacked a
test for the real reconciliation payload.

Git proves the defect predates TASK-005: Production SHA `6fff533` already
contains the receipt feature and the failing float path; TASK-005 implementation
`c610f86` and its evidence closure are later ancestors of this candidate and
were never deployed to Production.

`TASK_005_RELATION=UNRELATED_PREEXISTING_PRODUCTION_DEFECT`.
`TASK_005_RELEASE_EVIDENCE_REMAINS_CLOSED=YES`.

## 10. Production Impact / Idempotency

- Failure scope: the whole terminalization of the affected POST_CLOSE run,
  not one symbol, Topic, or dimension.
- Publication impact: receipt-backed formal completion was blocked; no claim of
  successful formal publication is made.
- Persistence impact: the final run failure audit is present in the public
  status readback. `_finish()` fails before its final commit and the dedicated
  failure handler records the terminal failure in a separate recovery session.
- Receipt impact: no receipt exists for 2026-10-06; no receipt exists for
  2026-10-05.
- Checkpoint impact: the completion checkpoint is after `_finish()` and was not
  reached; earlier checkpoint writes, if any, are not exposed by the public
  read-only API and were not altered.
- `PARTIAL_WRITE_DETECTED=NO at the receipt-hash transaction boundary; upstream
  attempted/persisted rows cannot be proven from the public read-only surface`.
- Retry collision risk is contained by deterministic run identity and the
  absence of a receipt. Existing non-completed checkpoint reuse rules still
  require the governed recovery/owner-reauthorization path; no retry was run.

## 11. Generic Fix

Implementation commit `edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91` adds:

- `_canonicalize_receipt_hash_value()` in `live/receipt.py`.
- Finite float conversion through `Decimal(str(value))` only for bounded
  receipt hash material.
- Explicit rejection of non-finite floats.
- `_receipt_stable_hash()` used by normal, correction, and operational receipt
  hash paths without changing non-float canonical output.

This is a generic semantic-class fix for receipt read-model numeric metrics,
not a symbol/date workaround. It does not change Topic membership, strength,
grade, Lifecycle, corporate-action, benchmark, calendar, scheduler, or
publication policy.

- `SYMBOL_SPECIFIC_FIX=NO`.
- `DATE_SPECIFIC_FIX=NO`.
- `GLOBAL_FLOAT_COERCION=NO`.
- `BUSINESS_POLICY_CHANGED=NO`.
- `MIGRATION_REQUIRED=NO`.
- `SCHEDULER_CHANGE_REQUIRED=NO`.

## 12. Tests and Determinism

- Focused Windows tests: `69 passed`.
- Corporate-action / G2 / no-trade regression: `71 passed`.
- Ruff changed-scope check: passed.
- Linux candidate focused, POST_CLOSE, Worker cold-process, and corporate-
  action scope: `156 passed`.
- Linux broad backend regression from repository root, matching CI path:
  `1277 passed, 23 skipped, 148 deselected, 1 warning, 0 failed`.
- Numeric edge cases: finite float, Decimal equivalence, zero/negative and
  repeating coverage metrics, and NaN/+Infinity/-Infinity rejection covered
  at the receipt boundary. The global normalizer remains float-rejecting.
- Determinism: repeated/order-independent receipt hash material uses the
  existing sorted canonical JSON contract; finite float and equivalent Decimal
  produce the same receipt hash; non-finite values never become zero or text.
- `TASK_OWNED_REGRESSION=NONE`.

## 13. Corporate-Action Regression

The TASK-005 authority fixture remains intact and passes the regression suite:

- `previous_traded_close=5.91`.
- `daily_comparison_reference=7.06`.
- `current_close=6.45`.
- `6.45 / 7.06 - 1 = -0.0864022662889518413597733711`.
- `6.44` remains the displayed bid, never the close.

No production code special-cases 2601 or 2026-10-05.

## 14. Worker / Linux Validation

The repository’s Windows cold-process Worker/import suite produced five
pre-existing `0xC000070A` process-launch failures in the Windows environment
for `live.cli` / provider-preflight imports and dry-run startup. Eleven related
tests passed. The failure is not an assertion or candidate traceback and is
not caused by the receipt diff.

The same candidate was then validated in a fresh Linux 3.12 container. The
receipt boundary and the full Worker cold-process suite passed as part of the
`156 passed` Linux focused run. The Linux broad backend run also passed with
zero failures. This is the required release-boundary evidence that the prior
Windows launch behavior does not reproduce as a candidate runtime defect on
Linux.

## 15. Release Composition

- `TASK_005_ANCESTOR_OF_CANDIDATE=YES`.
- Candidate ancestry: `c610f86` → `8764893` → `dd7fa59` → `edcd73c`.
- `RUNTIME_FIX_COMPOSITION=TASK-005 implementation and evidence closure are
  naturally included as ancestors of the runtime-fix candidate`.
- `COMPOSED_RELEASE_CANDIDATE_REQUIRED=NO`.
- `RUNTIME_FIX_RELEASE_READY=YES` for the normal governed release gate;
  this does not mean Production deployed.

## 16. Historical / Explicit Non-Actions

- Formal Historical Genesis Date remains
  `PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION`.
- `D0_MANUFACTURED=NO`.
- `TARGET_DATE_2026_10_05_TOUCHED=NO`.
- `HISTORICAL_RECOVERY_EXECUTED=NO`.
- `ORIGINAL_FAILED_EXECUTION_PRESERVED=YES`.
- `PRODUCTION_DEPLOYMENT_EXECUTED=NO`.
- `PRODUCTION_WRITE_SET=NONE`.
- `PREVIEW_TOUCHED=NO`.
- `DB_WRITE_EXECUTED=NO`.
- `MIGRATION_EXECUTED=NO`.
- `SCHEDULER_MUTATED=NO`.
- `PUSH_EXECUTED=NO`.
- `NEXT_TASK_MODIFIED=NO`.

## 17. Terminal Output

```text
TASK_STATUS=COMPLETE_RUNTIME_FAILURE_RECONCILIATION

CANONICAL_REMOTE_HEAD=e97f590cad497c0a23fb027fce39ec5891ea4bc1
RESEARCHED_BASE_SHA=dd7fa597cdc66243f80df1f8ad6d4b6dd7f82c8e
WORKTREE=E:\\TopicPilot\\w\\pcf001
BRANCH=codex/post-close-float-canonicalization-reconciliation-001
IMPLEMENTATION_SHA=edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91
EVIDENCE_CLOSURE_SHA=REPORT_COMMIT_RECORDED_AT_CLOSURE

TASK_005_IMPLEMENTATION_SHA=c610f86302504bba1df4529b8461bbce7042d201
TASK_005_EVIDENCE_CLOSURE_SHA=876489301a8b243e71c19097b428d20b4e2fa231
TASK_005_RELATION=UNRELATED_PREEXISTING_PRODUCTION_DEFECT
TASK_005_RELEASE_EVIDENCE_REMAINS_CLOSED=YES

PRODUCTION_API_SHA=6fff533168b1823052071f6d88d1f266397d327d
PRODUCTION_WORKER_SHA=6fff533168b1823052071f6d88d1f266397d327d
PRODUCTION_ALEMBIC_HEAD=0049_task_daily_formal_publication_receipt
PRODUCTION_SCHEDULER_STATE=ACTIVE_CONFIGURED;COMPETING_SCHEDULER=NONE_CONFIRMED

LATEST_POST_CLOSE_EXECUTION_ID=06d44574-214e-539d-ada4-dbf73d9eb971
LATEST_POST_CLOSE_SESSION_DATE=2026-10-06
FAILURE_CONFIRMED=YES
FAILURE_CLASS=POST_CLOSE_FINALIZATION_RECEIPT_HASHING
FAILURE_MESSAGE=TypeError: unsupported canonical value: float
FAILURE_STAGE=RECEIPT_HASHING
SEMANTIC_FIELD=coveragePct;coveredCoveragePct
FAILING_VALUE_CLASS=FINITE_RECONCILIATION_METRIC
FAILING_RUNTIME_TYPE=float
EXPECTED_CANONICAL_TYPE=Decimal
VALUE_SOURCE=DailyMarketReconciliation coverage metrics from integer counts
CANONICALIZER=normalizer.contracts.stable_hash via canonical_json/_canonical

NON_FINITE_VALUE_INVOLVED=NO
FLOAT_INTRODUCTION_POINT=DailyMarketReconciliation.coverage_pct and covered_coverage_pct division/rounding
ROOT_CAUSE_PROVEN=YES
ROOT_CAUSE=Receipt hash material included finite reconciliation floats but used the shared float-rejecting normalizer

FAILURE_SCOPE=WHOLE_POST_CLOSE_TERMINALIZATION
PUBLICATION_IMPACT=FORMAL_COMPLETION_BLOCKED;NO_SUCCESS_CLAIM
PERSISTENCE_IMPACT=RUN_FAILURE_AUDIT_PERSISTED;FINAL_FINISH_COMMIT_ABORTED
RECEIPT_IMPACT=ABSENT_FOR_2026-10-06
CHECKPOINT_IMPACT=COMPLETION_CHECKPOINT_NOT_REACHED;EARLIER_CHECKPOINTS_NOT_PUBLICLY_READABLE
PARTIAL_WRITE_DETECTED=NO_AT_RECEIPT_BOUNDARY;UPSTREAM_ATTEMPTS_NOT_PROVABLE_PUBLICLY
RETRY_COLLISION_RISK=CONTAINED_BY_DETERMINISTIC_RUN_ID;GOVERNED_REAUTH_REQUIRED

LOCAL_REPRODUCTION=PASS
REPRODUCTION_COMMAND=3.12 sanitized DailyMarketReconciliation fixture through stable_hash; same TypeError before fix

GENERIC_FIX_IMPLEMENTED=YES
FIX_SCOPE=Receipt-boundary finite-float-to-Decimal canonicalization only
SYMBOL_SPECIFIC_FIX=NO
DATE_SPECIFIC_FIX=NO
GLOBAL_FLOAT_COERCION=NO
BUSINESS_POLICY_CHANGED=NO
MIGRATION_REQUIRED=NO
SCHEDULER_CHANGE_REQUIRED=NO

CANONICALIZATION_DETERMINISM=PASS
NUMERIC_EDGE_CASE_TESTS=PASS
CORPORATE_ACTION_REGRESSION=PASS
EXPECTED_2601_RETURN=-0.0864022662889518413597733711

FOCUSED_TESTS=69 passed; corporate-action/G2/no-trade=71 passed
POST_CLOSE_BOUNDARY_VALIDATION=PASS
WORKER_COLD_PROCESS_VALIDATION=PASS_LINUX;WINDOWS_0xC000070A_ENVIRONMENT_FAILURE_RECORDED
LINUX_CANDIDATE_VALIDATION=PASS
FULL_BACKEND_RESULT=1277 passed, 23 skipped, 148 deselected, 1 warning, 0 failed
TASK_OWNED_REGRESSION=NONE

TASK_005_ANCESTOR_OF_CANDIDATE=YES
RUNTIME_FIX_COMPOSITION=TASK-005 lineage naturally included before runtime commit
COMPOSED_RELEASE_CANDIDATE_REQUIRED=NO
RUNTIME_FIX_RELEASE_READY=YES

FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
D0_MANUFACTURED=NO

TARGET_DATE_2026_10_05_TOUCHED=NO
HISTORICAL_RECOVERY_EXECUTED=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES

PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_WRITE_SET=NONE
PREVIEW_TOUCHED=NO
DB_WRITE_EXECUTED=NO
MIGRATION_EXECUTED=NO
SCHEDULER_MUTATED=NO
PUSH_EXECUTED=NO
NEXT_TASK_MODIFIED=NO

REPORT_PATH=E:\\TopicPilot\\w\\pcf001\\docs\\reports\\TASK-POST-CLOSE-FLOAT-CANONICALIZATION-RUNTIME-FAILURE-RECONCILIATION-001.md
EVIDENCE_ARTIFACT=E:\\TopicPilot\\w\\pcf001\\reports\\TASK-POST-CLOSE-FLOAT-CANONICALIZATION-RUNTIME-FAILURE-RECONCILIATION-001\\post-close-float-canonicalization-evidence.v1.json
OWNER_DECISION_REQUIRED=Normal governed release approval before any deployment; no technical ambiguity remains
NEXT_ACTION=Resume TASK-FORMAL-DIMENSION-ELIGIBILITY-PRODUCTION-RELEASE-004 with exact candidate edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91 through normal release gates; do not auto-deploy
```

## 18. Traditional Chinese Owner Summary

1. Production 掛掉的是 `06d44574-214e-539d-ada4-dbf73d9eb971`，2026-10-06 的 POST_CLOSE。
2. 真正失敗在 terminal finalization 的 receipt hash / canonical serialization stage。
3. 失敗欄位是 reconciliation 的 `coveragePct` 與 `coveredCoveragePct`。
4. 它由整數 counts 做 division/rounding，在 `DailyMarketReconciliation` 變成 Python float。
5. 是普通 finite float，不是 NaN、Infinity 或 -Infinity。
6. 共用 normalizer 的 canonicalizer 明確不接受 Python float；receipt path 沒有做 bounded numeric adaptation。
7. 不是 TASK-005 引入；Production 6fff 已先含有這條缺陷路徑，TASK-005 仍維持 closed。
8. 影響整個該次 POST_CLOSE 的 terminalization/receipt completion，不是單一 Topic 或 dimension。
9. Receipt 沒有產生；`_finish` 的 final commit 未完成；completion checkpoint 未到達；上游 checkpoint 是否存在由公開 API 無法證明，未被本任務修改。
10. Generic fix 是 receipt-boundary finite float 以 `Decimal(str(value))` deterministic canonicalize；非 workaround，且 global normalizer 仍拒絕 float。
11. 沒有任何 symbol/date special case。
12. 2601 的 `5.91 / 7.06 / 6.45` authority 完整，預期報酬仍為 `-0.0864022662889518413597733711`。
13. Linux focused/Worker/POST_CLOSE boundary 全過，broad backend 為 `1277 passed`；Windows cold-process 的既有 `0xC000070A` 已明列，不被隱藏。
14. 是；candidate `edcd73c...` 的 ancestry 已同時包含 TASK-005 implementation/evidence closure 與本 runtime fix。
15. 可以安全 Resume TASK-004 的 release gates，但尚未 Production deploy；仍需正常 Owner release approval。
16. 技術上沒有未解 blocker；只缺正常 release approval/deployment gate。
17. 是，Production 完全未被動到，所有 Production readback 都是 GET/read-only。
18. 是，2026-10-05 沒有 recovery、publication 或 receipt write。
19. 是，D0 仍等待下一個自然成功交易日。
20. 唯一建議：以 exact candidate `edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91` 恢復 TASK-004 的正式 release gate，不要在本任務自行 deploy。

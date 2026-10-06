# TASK-FORMAL-DIMENSION-ELIGIBILITY-PRODUCTION-RELEASE-004

## RESUME — governed Production release attempt

Resume evidence date: 2026-10-06 (Asia/Taipei)

This section preserves the earlier blocked release attempt. It does not rewrite
the historical blocker as resolved. The authorized release candidate remains
exactly:

`edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91`

The candidate contains the TASK-005 Corporate Action / provider-finality
lineage and the POST_CLOSE finite-float receipt-boundary remediation. TASK-005
is an ancestor of the candidate; no replacement SHA was selected.

## Release-lineage and repository readback

```text
AUTHORIZED_RELEASE_CANDIDATE=edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91
CANDIDATE_OBJECT_EXISTS=YES
CURRENT_ORIGIN_MAIN=e97f590cad497c0a23fb027fce39ec5891ea4bc1
MERGE_BASE=e97f590cad497c0a23fb027fce39ec5891ea4bc1
CANDIDATE_AHEAD_BY=7
CANDIDATE_BEHIND_BY=0
TASK_005_ANCESTOR_OF_CANDIDATE=YES
RUNTIME_FIX_PRESENT=YES
UNRELATED_DIFF_PRESENT=NO
CANDIDATE_TREE_CLEAN=YES
CURRENT_EVIDENCE_HEAD=136c70d2675697813cdc24166d42fc0d313c9c30
```

The candidate-to-current-evidence delta contains only the release report and
machine-readable release evidence; it does not alter the candidate runtime
tree. No Preview, Selection, Web, migration, scheduler, or historical-recovery
work is included.

Origin/main has not moved since the validated base. No rebase or merge was
performed.

## Pre-deploy Production readback

Fresh public read-only readback was performed immediately before the gate
decision against `https://topicpilot-api.onrender.com`:

```text
PREDEPLOY_API_SHA=6fff533168b1823052071f6d88d1f266397d327d
PREDEPLOY_API_HEALTH=PASS (/healthz 200; /readyz 200)
PREDEPLOY_WORKER_SHA=6fff533168b1823052071f6d88d1f266397d327d (last governed Worker provenance; no public Worker SHA endpoint)
PREDEPLOY_ALEMBIC_HEAD=0049_task_daily_formal_publication_receipt
PREDEPLOY_SCHEDULER_STATE=ACTIVE_CONFIGURED
PREDEPLOY_SCHEDULER_TIMEZONE=Asia/Taipei
PREDEPLOY_SCHEDULER_TIMING=13:45 earliest; 14:30 soft; 15:00 hard
PREDEPLOY_CALENDAR=TW_MARKET / REGULAR
PREDEPLOY_REFERENCE_VERSION=tw-reference-v1-rollover-0578862f98914eb7
PREDEPLOY_COMPETING_SCHEDULER=NONE_CONFIRMED
PREDEPLOY_LATEST_POST_CLOSE=06d44574-214e-539d-ada4-dbf73d9eb971 / 2026-10-06 / FAILED
PREDEPLOY_LATEST_RECEIPT=NOT_FOUND for 2026-10-05 and 2026-10-06
PREDEPLOY_LATEST_FORMAL_DATE=NONE_PUBLICLY_READABLE
```

The preserved 2026-10-06 failure remains:

`POST_CLOSE_FINALIZATION_FAILED — TypeError: unsupported canonical value: float`

No replay, retry, replacement receipt, or manual POST_CLOSE was performed.

## Mandatory gate result

The release gate is blocked before any Production mutation.

The exact unresolved blocker is the current canonical Production provider/date/
finality preflight. The public Production API exposes no provider-preflight or
G2 readback endpoint, and this execution has no protected Production database
credential/runtime channel with which to run the repository-owned
`topicpilot-provider-preflight --run-date 2026-10-05` against the canonical
Production context.

The preserved TASK-005 candidate evidence remains valid for its own read-only
reconstruction and proves the Corporate Action comparator values. Current
official source checks also confirm the 2601 values, but they do not substitute
for the protected canonical Production preflight:

```text
CORPORATE_ACTION_REGRESSION=PASS
OFFICIAL_2601_CLOSE=6.45
OFFICIAL_2601_LAST_BID=6.44
PREVIOUS_TRADED_CLOSE=5.91 (2026-09-22)
DAILY_COMPARISON_REFERENCE=7.06 (2026-10-05)
EXPECTED_2601_RETURN=-0.0864022662889518413597733711
NO_2601_SPECIAL_CASE=YES
```

The direct official TPEx checks reinforce the fail-closed decision. The
target-date request returned HTTP 200 but a non-target response date (`20261001`)
from the target-date endpoint; the official OpenAPI snapshot returned the
current date (`20261006`), not `20261005`. HTTP success therefore cannot prove
target-date authority or finality. No alternate source, fallback, synthetic
bar, or ad-hoc importer was used.

The current Production configuration still reports the canonical reference
version, and the prior G2 closure reports READY. That is not treated as a
fresh protected provider/date/finality PASS. The release remains blocked until
the exact canonical Production preflight is executed or read back with
target-date and finality evidence.

```text
MIGRATION_REQUIRED=NO
PROVIDER_DATE_AUTHORITY=UNPROVEN_BLOCKING
PROVIDER_FINALITY_AUTHORITY=UNPROVEN_BLOCKING
PROVIDER_CONTRACT_PREFLIGHT=BLOCKED_CURRENT_PROTECTED_READBACK_UNAVAILABLE
G2_REVALIDATED=PARTIAL_REFERENCE_CONFIG_READBACK_ONLY
G2_PRODUCTION_READY=NOT_CURRENTLY_PROVEN_BY_PROTECTED_READBACK
PRODUCTION_RELEASE_GATE=BLOCKED_PREDEPLOY_GATE
```

## Candidate validation evidence retained

The exact candidate evidence remains attached and was not reused from another
tree:

```text
CANONICALIZATION_DETERMINISM=PASS
POST_CLOSE_BOUNDARY_VALIDATION=PASS
WORKER_RELEASE_BOUNDARY=PASS_LINUX
LINUX_CANDIDATE_VALIDATION=PASS
FULL_BACKEND_VALIDATION=1277 passed, 23 skipped, 148 deselected, 1 warning, 0 failed
WINDOWS_0xC000070A=RECORDED_ENVIRONMENT_LIMITATION; NOT WAIVED
ROLLBACK_API_SHA=6fff533168b1823052071f6d88d1f266397d327d
ROLLBACK_WORKER_SHA=6fff533168b1823052071f6d88d1f266397d327d
ROLLBACK_DB_HEAD=0049_task_daily_formal_publication_receipt
ROLLBACK_READY=YES
```

No deployment was attempted, so no mixed-version state was created.

## Non-actions and historical preservation

```text
DEPLOYMENT_EXECUTED=NO
PRODUCTION_RELEASED=NO
POST_DEPLOY_VERIFIED=NO
TARGET_DATE_2026_10_05_TOUCHED=NO
ORIGINAL_2026_10_05_FAILED_EXECUTION_PRESERVED=YES
TARGET_DATE_2026_10_06_REPLAYED=NO
ORIGINAL_2026_10_06_FAILED_EXECUTION_PRESERVED=YES
HISTORICAL_RECOVERY_EXECUTED=NO
MANUAL_POST_CLOSE_EXECUTED=NO
MANUAL_PUBLICATION_EXECUTED=NO
FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
D0_MANUFACTURED=NO
WEB_DEPLOYMENT_REQUIRED=NO
WEB_DEPLOYMENT_EXECUTED=NO
PUSH_REQUIRED_FOR_DEPLOYMENT=YES (candidate must be available to GitHub Actions)
PUSH_EXECUTED=NO
CANONICAL_PROMOTION_REQUIRED=NO
CANONICAL_PROMOTION_EXECUTED=NO
SELECTION_WORK_TOUCHED=NO
PREVIEW_TOUCHED=NO
DB_DATA_WRITE_OUTSIDE_DEPLOYMENT=NO
MIGRATION_EXECUTED=NO
SCHEDULER_MUTATED=NO
NEXT_TASK_MODIFIED=NO
```

Because a mandatory gate failed, the exact candidate was not pushed and the
existing governed deployment workflow was not dispatched. No Production
write, deployment metadata mutation, database mutation, or scheduler change
occurred.

## Required next action

Obtain a protected, read-only canonical Production execution/readback of the
exact G2 provider preflight for `2026-10-05`, including reference context,
per-market provider authority, exact response date, finality, and failure
classification. Resume deployment only if that gate returns PASS. Do not
deploy based on HTTP 200, the public reference configuration alone, or the
preserved candidate reconstruction.

## Terminal state

```text
TASK_STATUS=BLOCKED_PREDEPLOY_GATE
AUTHORIZED_RELEASE_CANDIDATE=edcd73ce5b9f7390e6a5f9ee60915b6053ec3f91
OWNER_DECISION_REQUIRED=Protected canonical Production provider/date/finality preflight readback; no permission is needed to stop, and no gate may be weakened
NEXT_ACTION=Obtain exact protected canonical G2/provider-preflight PASS for 2026-10-05, then resume the existing release gates; do not push or deploy before that proof
```

## Traditional Chinese Owner Summary

1. 最後實際部署的 exact SHA：本次沒有部署；Production 仍是 API/Worker `6fff533168b1823052071f6d88d1f266397d327d`。
2. API 與 Worker 是否同一 SHA：現有回讀與保存的 Worker provenance 顯示兩者都是 `6fff533…`。
3. 部署前 Production SHA：`6fff533168b1823052071f6d88d1f266397d327d`。
4. DB 是否仍為 0049：是，`0049_task_daily_formal_publication_receipt`；沒有 migration。
5. Scheduler 是否改動：沒有；仍為 Asia/Taipei、TW_MARKET，13:45/14:30/15:00。
6. Provider date/finality/preflight：本次無法取得受保護 canonical preflight readback，因此不能宣稱 PASS；這是唯一阻塞門。
7. G2：Production config 仍指向 canonical reference version，但本次未能取得 fresh protected G2 READY 證明。
8. 2601：仍使用 previous traded close `5.91`、daily comparison reference `7.06`、official close `6.45`。
9. 6.44：仍只視為最後揭示買價，不是收盤價。
10. Float canonicalization fix：存在於 exact candidate `edcd73ce…`，但尚未進入 Production runtime。
11. API health：目前 Production `/healthz` 與 `/readyz` 都 PASS；不是新版本部署後驗證。
12. Worker health：目前保存的 Worker runtime provenance 為 `6fff533…`；本次未部署新 Worker。
13. 新 Production runtime error：沒有新增部署後錯誤；既有 10/06 float failure 保持原樣。
14. 10/05 recovery：完全沒有。
15. 10/06 replay：完全沒有。
16. 兩個 failed execution：均完整保留。
17. 手動 POST_CLOSE/publication：沒有。
18. D0：`PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION`。
19. 下一個自然交易日：只觀察正常 Scheduler 是否自然成功、provider/date/finality、DATA_READY、receipt/checkpoint 與 runtime SHA；不可手動觸發。
20. 新架構是否正式 release：尚未；候選已驗證但未通過 Production pre-deploy gate。
21. Rollback：沒有 rollback；Production 實際仍停在 `6fff533…`，rollback path 已確認可用。
22. 下一步唯一建議：取得 exact `2026-10-05` canonical Production provider/G2 protected read-only PASS；在此之前不 push、不 deploy。

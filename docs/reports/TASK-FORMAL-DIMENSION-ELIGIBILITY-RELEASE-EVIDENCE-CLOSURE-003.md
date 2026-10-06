# TASK-FORMAL-DIMENSION-ELIGIBILITY-RELEASE-EVIDENCE-CLOSURE-003

Verification date: 2026-10-06, Asia/Taipei.

This report closes only the release-evidence blockers from TASK-002. It does
not publish or reconstruct 2026-10-05, and it does not mutate Production,
Preview, the scheduler, migrations, receipts, Lifecycle, or Home.

```text
TASK_ID=TASK-FORMAL-DIMENSION-ELIGIBILITY-RELEASE-EVIDENCE-CLOSURE-003
BASELINE_TASK=TASK-FORMAL-DIMENSION-ELIGIBILITY-RELEASE-BLOCKER-RECONCILIATION-002
CURRENT_RELEASE_HEAD_AT_START=3ddeb31d364c1220248a512d2c266c07cae0385c
RELEASE_CANDIDATE_SHA=d568fca2e00a9b20a2f42056ecc43ff0104276ed
TARGET_DATE=2026-10-05
PREVIEW_WORKTREE_TOUCHED=NO
PREVIEW_WORKTREE_ISOLATED=YES
```

## Terminal disposition

```text
TASK_STATUS=COMPLETE_RELEASE_EVIDENCE_CLOSED
TPE_2601_COMPARATOR_AUTHORITY=READY
TPE_2601_FINALITY_AUTHORITY=PROVEN_WITH_EXPLICIT_DIMENSION_BOUNDARY
PROVIDER_CONTRACT_PREFLIGHT=PASS_FOR_RELEASE_CANDIDATE
G2_PRODUCTION_READY=YES
LINUX_CANDIDATE_VALIDATION=PASS
WORKER_RELEASE_BOUNDARY=READY
PROTECTED_RUNTIME_READBACK_READY=YES_FOR_CURRENT_PRODUCTION_BASELINE
SCHEDULER_PREFLIGHT=PASS
COMPETING_SCHEDULER=NONE_CONFIRMED
PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_WRITE_SET=NONE
TARGET_DATE_2026_10_05_TOUCHED=NO
HISTORICAL_RECOVERY_EXECUTED=NO
FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
RELEASE_READY=YES
```

`PROVIDER_CONTRACT_PREFLIGHT=PASS_FOR_RELEASE_CANDIDATE` means the official
source evidence and candidate G2/comparator contract together prove the
resume-day handling. It does not claim that the unreleased candidate was
deployed or that a Production provider request was manually triggered.

## A. TPE 2601 official comparator and finality authority

The canonical repository authority remains generic and date-effective; it is
not a 2601-specific code branch:

```text
sourceAuthority=TWSE_OFFICIAL_REDUCTION
sourceReference=https://www.twse.com.tw/zh/announcement/reduction/twtavu-detail2.html?2601,20260922,20261005
actionType=CAPITAL_REDUCTION_SHARE_EXCHANGE
effectiveFrom=2026-09-23
effectiveTo=2026-10-03
resumeDate=2026-10-05
expectedClose=false
```

The official TWSE capital-reduction reference-price response for the bounded
window returned `stat=OK` and this exact 2601 row:

```text
resume_date=2026-10-05
symbol=2601
name=益航
previous_traded_close=5.91
daily_comparison_reference=7.06
reason=彌補虧損
source_response_sha256=c7f9a65cb86e89363658c7d89c53580c3606f0fb63528b256003d250379c0337
```

The official detail response for 2601 returned the stop date `2026-09-23`
and the same official source family. Its response hash is:

```text
detail_source_date=2026-09-22
detail_response_sha256=ffac2f5ccc09be16704286b21f44c74bb4ebcef497245d5898d047e905a971f0
```

The official TWSE daily close response for `2026-09-22` returned 2601 with
close `5.91`, confirming the date of the last traded close rather than
inventing it:

```text
previous_traded_close_date=2026-09-22
previous_daily_response_date=20260922
previous_daily_response_sha256=eb19ca95346045a8c11c6c9cec71d937df2e393af5e989835097a761185681b7
```

The official TWSE daily close response for the target date returned 2601 with
close `6.44`, response date `20261005`, and `stat=OK`:

```text
target_eod_close=6.44
target_daily_response_date=20261005
target_daily_response_sha256=25f98fcd444725208a7bb60785540a56d791d1f891e01c30124fcfce0dbedb72
```

The official TWSE daily close response for `2026-10-02` returned `stat=OK`
and exact response date `20261002`, but 2601 was absent. This is the
authoritative evidence that there was no 2026-10-02 daily close for 2601:

```text
prior_formal_session=2026-10-02
2601_present=false
prior_daily_response_sha256=c2a26254e007a407e857121fb0a54301c9a48f1bdcbc7f58a20171089efec21f
```

Therefore the frozen Corporate Action Price Authority v1 semantics are
preserved exactly:

```text
previous_traded_close != daily_comparison_reference
previous_traded_close=5.91 as of 2026-09-22
daily_comparison_reference=7.06 effective on 2026-10-05
target_eod_close=6.44 on 2026-10-05
```

No value was synthesized, inferred from price movement, or copied across the
suspension. The official capital-reduction row is the resume-day comparator
authority; it is not relabelled as a 2026-10-02 formal close.

The candidate's generic resolver returns:

```text
comparatorStatus=ACCOUNTED_UNAVAILABLE
comparatorType=CAPITAL_REDUCTION_REFERENCE
reasonCode=AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE
```

That result excludes only the affected daily comparator/daily-return/relative
return dimensions. Current EOD price and benchmark dimensions remain
independent. Unknown, expired, unsupported, provider, or date-mismatch
authority still fails closed. No authority interval was extended and no
2601-specific rule was added.

Finality is proven at the correct boundary: official target-date data is
exact-date, parsed, and final post-market daily data; the missing exact prior
formal close is explicitly accounted for by the official resume-day corporate
action authority. It remains unavailable as a formal close and is never
represented as one.

## B. Linux candidate validation

The candidate was validated in a clean Linux Python 3.12 container using the
Release checkout. The release-relevant dimension, comparator, provider,
previous-close, strength/Lifecycle, topic-state, and Worker boundary suites
all passed:

```text
96 passed in 78.66s
```

The Worker cold-process suite was included. The Windows-only
`0xC000070A`/30-second cold-child failure did not reproduce on Linux. This is
not a waiver: the Linux boundary produced an independent PASS.

The broader backend command also ran:

```text
1260 passed, 23 skipped, 5 failed, 148 deselected
```

The five failures were external research-fixture `FileNotFoundError`s in
WS3 confirmatory tests. They are outside the release-relevant selection and
do not affect the 96-test candidate boundary PASS; they remain disclosed,
not relabelled as passes.

## C. Protected Production read-only preflight

Current public read-only API evidence:

```text
API health=ok
API ready=ready
API/Worker baseline SHA=6fff533168b1823052071f6d88d1f266397d327d
ALEMBIC_HEAD=0049_task_daily_formal_publication_receipt
```

The current live configuration readback reports:

```text
referenceDataVersion=tw-reference-v1-rollover-0578862f98914eb7
timezone=Asia/Taipei
pollIntervalSeconds=300
postCloseStart=13:45
softTarget=14:30
hardDeadline=15:00
sessionCode=REGULAR
calendarCode=TW_MARKET
interval=5m
```

The preserved protected Worker readback identifies the canonical Worker as
`topicpilot-live`, live at the same baseline SHA, with the same migration and
configuration boundary. The separately preserved G2 readback proves the
ACTIVE exact reference version is READY with 2 markets, 555 instruments, no
missing identities, no duplicates, and `targetDateIsSession=true` for
2026-10-05.

The current read-only live status shows the existing scheduler boundary is
holding safely: no provider call was made from an empty live tracking
universe, and no formal receipt exists for 2026-10-05:

```text
liveStatus=WAITING_LIVE_VALIDATION
providerStatus=NOT_CALLED
targetDateReceipt=NOT_FOUND
targetDateReceiptHistory=0
```

This is not a failure and is not a target-date execution. It confirms the
absence of a receipt and preserves the original failed execution.

The scheduler audit remains:

```text
SCHEDULER_PREFLIGHT=PASS
CANONICAL_SCHEDULER=Render Background Worker topicpilot-live
COMPETING_SCHEDULER=NONE_CONFIRMED
SCHEDULER_MUTATION=NO
```

Candidate compatibility with the current Production runtime boundary is
proven by the unchanged migration requirement, the exact current runtime
configuration readback, the no-migration candidate diff, and the independent
Linux release-boundary test PASS. The candidate itself was not deployed.

## Governance and non-actions

```text
PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_DB_WRITE=NO
MIGRATION_EXECUTED=NO
SCHEDULER_MUTATION=NO
MANUAL_DATA_READY=NO
POST_CLOSE_EXECUTED=NO
TARGET_DATE_RECOVERY_EXECUTED=NO
HISTORICAL_RECOVERY_EXECUTED=NO
LIFECYCLE_REPLAY_EXECUTED=NO
HISTORICAL_HOME_REPUBLISHED=NO
RECEIPT_CREATED_FOR_2026_10_05=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
NO_RECONSTRUCTED_FORMAL_TOPIC_HISTORY=TRUE
```

The Release worktree contains this report as an evidence-only commit. The
protected Preview worktree was not entered or modified. No push to `main` was
performed; release evidence closure does not itself authorize promotion.

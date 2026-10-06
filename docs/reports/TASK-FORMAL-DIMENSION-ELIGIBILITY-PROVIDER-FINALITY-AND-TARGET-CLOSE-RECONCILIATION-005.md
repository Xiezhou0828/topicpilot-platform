# TASK-FORMAL-DIMENSION-ELIGIBILITY-PROVIDER-FINALITY-AND-TARGET-CLOSE-RECONCILIATION-005

## 1. Executive Summary

This task closes the release-evidence blockers from TASK-004 on the isolated
Release worktree. The official TWSE MI_INDEX response for 2026-10-05 maps
`收盤價` to `6.45`, `最後揭示買價` to `6.44`, and `最後揭示賣價` to `6.45`.
The prior `6.44` current-close evidence was therefore a report/forensic
field-selection error, not an application provider mapping defect.

The bounded generic fix adds a separate official Corporate Action Price
Authority input. It preserves the distinction between the last actual traded
close, the session comparison reference, and the target close. A corporate-
action resume day becomes comparator-ready only when the status interval, the
official comparison reference, the last-traded-close provenance, source
identity, target date, and finality all agree. No database schema or migration
was added.

The candidate provider reconstruction passes for the target date and TPE
2601. Linux focused and Worker-boundary validation pass. The current public
Production runtime is still the historical `6fff533...` baseline and was not
deployed; its latest independent 2026-10-06 POST_CLOSE run is recorded as an
external runtime incident (`TypeError: unsupported canonical value: float`).
That incident was not caused or changed by this task and is not silently
reclassified as a candidate result.

## 2. Canonical Lineage

```text
ORIGIN_MAIN=e97f590cad497c0a23fb027fce39ec5891ea4bc1
TASK_001_IMPLEMENTATION_SHA=04ad3e3c7e4840cad2bf4643369162a0affdc956
TASK_002_SHA=3ddeb31d364c1220248a512d2c266c07cae0385c
TASK_003_CANDIDATE_SHA=d568fca2e00a9b20a2f42056ecc43ff0104276ed
TASK_003_EVIDENCE_SHA=6d882712b84523cb2b0841ab96fd53a666494ccd
TASK_004_SHA=UNCOMMITTED_WORKTREE_REPORT_ONLY
TASK_004_SOFTWARE_DELTA=NONE
TASK_005_BASE_SHA=6d882712b84523cb2b0841ab96fd53a666494ccd
WORKTREE=C:\Users\acer\Desktop\題材領航\topicpilot-platform
BRANCH=codex/formal-dimension-release-blocker-reconciliation-002
PREVIEW_WORKTREE=C:\Users\acer\Desktop\題材領航\topicpilot-preview-v1-1-flat-canvas
PREVIEW_ISOLATED=YES
```

TASK-004 was an uncommitted report in the shared Release worktree and did not
change software. The protected Preview worktree was not entered or modified.
The original failed recovery execution remains preserved under the lineage
recorded by TASK-002 (`5890eda0-c81b-50d8-9cfc-05e5a6e7b5a0`).

## 3. TASK-003 / TASK-004 Supersession

```text
SUPERSEDES_TASK_003_TARGET_CLOSE_EVIDENCE=YES
SUPERSEDES_TASK_003_PROVIDER_PREFLIGHT_EVIDENCE=YES
TASK_004_BLOCKER_TARGET_CLOSE_RESOLVED=YES
TASK_004_BLOCKER_PROVIDER_FINALITY_RESOLVED=YES
```

TASK-003's `current_close=6.44` and its release-ready conclusion are
superseded by the direct official field mapping below. TASK-003's semantic
separation of unavailable dimensions remains preserved, but its specific
release evidence did not have an admitted official target close or the new
price-basis authority.

TASK-004 correctly identified two blockers: the target-close contradiction and
the immediate-prior-close coupling. The target-close contradiction is resolved
by official field evidence. The provider blocker is resolved on the candidate
by the generic price authority; the current Production baseline remains
unchanged because deployment is explicitly outside this task.

## 4. Official TWSE Field Evidence

The official target endpoint returned HTTP 200, `stat=OK`, and response date
`20261005`. Its selected table header is:

```text
證券代號|證券名稱|成交股數|成交筆數|成交金額|開盤價|最高價|最低價|收盤價|漲跌(+/-)|漲跌價差|最後揭示買價|最後揭示買量|最後揭示賣價|最後揭示賣量|本益比
```

The exact 2601 row is recorded in the machine-readable evidence artifact at
`reports/TASK-FORMAL-DIMENSION-ELIGIBILITY-PROVIDER-FINALITY-AND-TARGET-CLOSE-RECONCILIATION-005/official-source-evidence.json`:

```text
2601|益航|8,488,264|5,080|54,496,294|7.01|7.02|6.36|6.45|<p>X</p>|0.00|6.44|107|6.45|30|0.00
```

Therefore:

```text
TWSE_2601_20261005_CLOSE=6.45
TWSE_2601_20261005_LAST_BID=6.44
TWSE_2601_20261005_LAST_ASK=6.45
OFFICIAL_TARGET_CLOSE_CONFLICT_CONFIRMED=YES
TARGET_DAILY_RAW_RESPONSE_SHA256=25f98fcd444725208a7bb60785540a56d791d1f891e01c30124fcfce0dbedb72
```

The same header-driven mapping was checked against ordinary rows from the
same official table: 2330 close/bid/ask `2575/2575/2580`, 1303
`286/286/--`, 1101 `25.00/25.00/25.05`, and 0050
`115.95/115.90/115.95`. This is a general field distinction, not a 2601
exception.

## 5. 6.44 vs 6.45 Root Cause

```text
TARGET_CLOSE_ROOT_CAUSE=REPORT_EVIDENCE_ERROR
APPLICATION_PROVIDER_MAPPING_BUG=NO
FORENSIC_TOOLING_MAPPING_BUG=YES_AT_REPORT_EXTRACTION_BOUNDARY
SOURCE_SELECTION_ERROR=NO
SCHEMA_DRIFT=NO
```

The repository provider already maps the TWSE MI_INDEX row by the official
positional contract: `row[8]` is `收盤價`; `row[11]` is `最後揭示買價`.
Repository search found no application mapping or fixture that assigned `6.44`
to close. The predecessor evidence copied the bid-side value into the report
as `current_close`. The corrected evidence is therefore `6.45`; no production
parser rewrite was needed.

## 6. Provider Mapping Audit

`TwseOfficialDailyProvider._fetch_market_day_once` selects the table whose
first field is `證券代號`, validates the target response date, and maps open,
high, low, close, and volume to fields 5, 6, 7, 8, and 2 respectively. The
explicit previous-close reader only accepts a named previous-close field; it
does not derive a close from bid, ask, or price movement.

The new contract test uses the full official-shaped 2601 row and asserts:

```text
normalized close=6.45
last bid remains 6.44 in the source row
last ask remains 6.45 in the source row
```

No parser mapping change was required. The scope is limited to protecting the
official semantics at the evidence and comparator boundary.

## 7. Previous-Close / Finality Root Cause

The old path was:

```text
run_provider_preflight
  -> price.previous() is absent
  -> resolve_missing_daily_comparator
  -> status-only corporate-action authority
  -> MISSING_PREVIOUS_FORMAL_CLOSE / PREVIOUS_CLOSE_AUTHORITY_NOT_READY
```

The canonical calendar selected `2026-10-02` as the previous formal session
for target `2026-10-05`. The official 2026-10-02 MI_INDEX payload does not
contain 2601, while the official 2026-09-22 payload contains 2601 close `5.91`.
The reduction authority reports resume date 2026-10-05 and comparison reference
`7.06`. Thus:

```text
WHY_IS_2026_10_02_BEING_REQUESTED=TW_MARKET previous formal session calendar
IS_2026_10_02_A_REAL_TRADED_CLOSE_FOR_2601=NO
```

The old contract treated an exact previous formal-session close as a required
comparator even when the instrument was in an authorized price-basis-changing
suspension. It also had no place to carry the official comparison reference.
That coupled target-date finality to one comparator shape. The fix keeps target
EOD finality independent and resolves comparator authority separately.

## 8. Generic Resume-Day Contract

The implementation preserves the six governed cases:

| Case | Candidate behavior |
| --- | --- |
| A normal continuity | Formal prior close is both provenance and comparison reference. |
| B pure suspension/resume | A formally authorized last actual close may be used when no price-basis reset is required. |
| C price-basis-changing resume | A matching official price authority makes the comparison reference READY while retaining the last actual traded close as separate provenance. |
| D missing comparator authority | The affected dimensions remain unavailable or error; no value is synthesized. |
| E non-final/current-date-invalid target close | Provider/date/finality gate fails closed. |
| F authority conflict | Multiple or mismatched authorities fail closed. |

Effective intervals are matched exactly. The implementation does not extend a
corporate-action interval, infer an action from price movement, forward-fill,
use zero, or use the latest available price as an undocumented fallback.

## 9. Implementation

Implementation commit:

```text
IMPLEMENTATION_SHA=c610f86302504bba1df4529b8461bbce7042d201
```

The bounded change:

- adds `corporate_action_price_authority.py` and a separate official evidence
  registry, leaving status-only authority free of price payloads;
- validates identity, action interval, resume date, positive official values,
  source authority, SHA-256 lineage, and `FINAL` status;
- extends `ComparatorResolution` with distinct previous-traded and comparison-
  reference fields;
- makes a matching official reference comparator READY without collapsing it
  into `previousClose`;
- computes formal daily return from the comparison reference on a price-basis
  reset day while preserving `SelectedMemberFact.previous_close` semantics;
- keeps normal-day behavior and membership behavior unchanged; and
- adds no database column, no migration, no writer, and no publication action.

```text
MIGRATION_REQUIRED=NO
NO_2601_SPECIAL_CASE=YES
SYNTHETIC_OR_FILL_USED=NO
```

The only 2601 occurrence in the implementation is the official evidence data
record and test fixture; control flow is symbol-agnostic and date-agnostic.

## 10. Test Matrix

The focused suite covers ordinary continuity, pure/status-only resume,
price-basis-changing resume, missing prior-session close, missing current
close, date and identity mismatch, invalid/non-final authority, authority
conflict, official close/bid/ask mapping, 2601 as a generic fixture, ordinary
instrument coverage, provider preflight, interval expiry, membership
preservation, and no-zero/no-forward-fill behavior.

Key new assertions are:

```text
test_generic_price_authority_keeps_provenance_distinct_from_comparison_reference
test_price_authority_conflict_fails_closed_without_selecting_a_value
test_real_2601_provider_preflight_uses_official_reference_not_bid_side_value
test_resume_day_daily_return_uses_reference_not_last_traded_close
test_corporate_action_price_authority_must_match_the_authorized_resume_interval
test_twse_mi_index_close_is_not_last_bid_or_last_ask
```

## 11. Linux Validation

The candidate was executed on the established Linux release boundary, not
Windows-only. The Worker cold-process/import boundary was included in the
release-boundary run.

```text
FOCUSED_LINUX_RESULT=101 passed
LINUX_CANDIDATE_VALIDATION=PASS
WORKER_RELEASE_BOUNDARY=READY / 110 passed
```

The first broad collection attempt lacked the container's `httpx2` TestClient
dependency; that was classified as ENVIRONMENT, the dependency was supplied in
the ephemeral test container, and the exact scopes were rerun.

## 12. Full Regression

```text
FULL_BACKEND_PASS=1271
FULL_BACKEND_FAIL=0
FULL_BACKEND_SKIP=23
FULL_BACKEND_DESELECTED=148 (research, governance, postgres markers excluded from release scope)
RESEARCH_MARKER=84 passed, 0 failed
GOVERNANCE_MARKER=7 passed, 0 failed
TASK_OWNED_REGRESSION=NONE
```

The 23 PostgreSQL skips were due to absent test database URLs. They were not
converted to passes. Ruff check passed on all changed files. `ruff format
--check` still reports five pre-existing formatting differences in files that
were already unformatted at TASK-003; the new authority module is formatted,
and no unrelated bulk formatting was introduced. This is classified
`PRE_EXISTING`, not a task-owned regression.

## 13. Provider Preflight

The candidate was reconstructed through the real TWSE provider for target
2026-10-05. A formal canonical previous close was supplied only for the normal
2330 control; 2601 had no fabricated previous-session close. The candidate
result was:

```text
TPE_RECONSTRUCTED_STATUS=PASS
TPE_RECONSTRUCTED_ERROR=None
2601_CLOSE=6.45
2601_COMPARATOR_STATUS=READY
2601_PREVIOUS_TRADED_CLOSE=5.91 (2026-09-22)
2601_DAILY_COMPARISON_REFERENCE=7.06 (2026-10-05)
SYNTHETIC_OR_FILL_USED=NO
```

Target-date authority is proven by the exact official target date, source,
instrument, EOD `收盤價` field, `stat=OK`, raw response lineage, and the
candidate provider's date gate. Finality is not inferred from HTTP success
alone; the target-date EOD table and field semantics are independently mapped,
and the price authority is explicitly `FINAL`.

```text
TARGET_DATE=2026-10-05
PROVIDER_DATE_AUTHORITY=PASS
PROVIDER_FINALITY_AUTHORITY=PASS
PREVIOUS_TRADED_CLOSE_AUTHORITY=PROVEN
DAILY_COMPARISON_REFERENCE_AUTHORITY=PROVEN
CURRENT_CLOSE_AUTHORITY=PROVEN
PROVIDER_CONTRACT_PREFLIGHT=PASS_FOR_CANDIDATE_READ_ONLY_RECONSTRUCTION
```

Forensic calculation only, never published:

```text
EXPECTED_2601_DAILY_RETURN=6.45 / 7.06 - 1
= -0.0864022662889518413597733711
percentage=-8.640226628895184135977337110%
```

## 14. G2 Production Readback

The current public configuration still binds the runtime to the exact active
reference version, and the preserved direct Production registry readback from
the G2 remediation remains unchanged:

```text
G2_REVALIDATED=YES
G2_PRODUCTION_READY=YES
G2_ACTIVE_REGISTRY=tw-reference-v1-rollover-0578862f98914eb7
G2_MARKET_COUNT=2
G2_INSTRUMENT_COUNT=555
G2_DUPLICATES=0
G2_MISSING=0
G2_TARGET_SESSION_2026_10_05=YES (targetDateReason=null)
```

No registry mutation occurred in TASK-005. The current API configuration
readback reports the same exact `referenceDataVersion`.

## 15. Production Runtime Readback

Fresh public read-only checks on 2026-10-06 returned:

```text
PRODUCTION_API_SHA=6fff533168b1823052071f6d88d1f266397d327d
PRODUCTION_WORKER_SHA=6fff533168b1823052071f6d88d1f266397d327d (preserved exact Worker readback)
PRODUCTION_ALEMBIC_HEAD=0049_task_daily_formal_publication_receipt
HEALTHZ=200 / ok
READYZ=200 / ready
SCHEDULER=canonical Render Background Worker topicpilot-live; configuration active
COMPETING_SCHEDULER=NONE_CONFIRMED
```

The fresh live status also reports an independently occurring 2026-10-06
POST_CLOSE failure:

```text
LAST_RUN_ID=06d44574-214e-539d-ada4-dbf73d9eb971
LAST_RUN_TYPE=POST_CLOSE
LAST_RUN_COMPLETED_AT=2026-10-06T05:56:27.517615Z
LAST_RUN_FAILURE=POST_CLOSE_FINALIZATION_FAILED
LAST_RUN_FAILURE_MESSAGE=TypeError: unsupported canonical value: float
```

The source error is in the already deployed normalizer canonicalization path,
not in the TASK-005 candidate. It is classified `PRE_EXISTING / EXTERNAL
PRODUCTION RUNTIME INCIDENT`. It was not repaired here because this task
forbids unrelated Production mutation. The incident is fully disclosed as a
release-attempt operational risk; it does not change the exact SHA/config/G2
baseline or the task-owned write set.

## 16. Exact Candidate SHA

```text
CANONICAL_BASE=e97f590cad497c0a23fb027fce39ec5891ea4bc1
IMPLEMENTATION_SHA=c610f86302504bba1df4529b8461bbce7042d201
EVIDENCE_CLOSURE_SHA=876489301a8b243e71c19097b428d20b4e2fa231
RELEASE_CANDIDATE_SHA=876489301a8b243e71c19097b428d20b4e2fa231
CANDIDATE_TREE_STATUS=TRACKED_FILES_CLEAN; pre-existing unrelated untracked reports preserved
CANONICAL_PUSH=NO
```

The evidence closure commit is the exact report/evidence commit above. A
follow-up metadata-only commit fills these self-describing identifiers and
does not stage or modify any predecessor or unrelated untracked report.

## 17. Non-Actions / Governance Proof

```text
PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_WRITE_SET=NONE_BY_TASK_005
MIGRATION_EXECUTED=NO
SCHEDULER_MUTATION=NO
G2_MUTATION=NO
TARGET_DATE_2026_10_05_TOUCHED=NO_PRODUCTION_WRITE
HISTORICAL_RECOVERY_EXECUTED=NO
POST_CLOSE_2026_10_05_EXECUTED=NO
DATA_READY_2026_10_05_EXECUTED=NO
FORMAL_PUBLICATION_2026_10_05_EXECUTED=NO
LIFECYCLE_REPLAY_EXECUTED=NO
HISTORICAL_HOME_REPUBLISHED=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
PREVIEW_WORKTREE_TOUCHED=NO
NEXT_TASK_MODIFIED=NO
```

Official HTTP reads, candidate reconstruction, tests, and public Production
readbacks are evidence collection only. No recovery receipt or publication
receipt was manufactured; the target-date receipt remains `NOT_FOUND`.

## 18. Remaining Risks

The only unresolved item is the independently observed current Production
POST_CLOSE runtime incident described in §15. It is not an authority blocker
for the candidate's target-date provider contract, but the next governed
Production release attempt should review that incident before deployment.
This task does not authorize or perform that remediation.

```text
OWNER_DECISION_REQUIRED=NO
EXTERNAL_AUTHORITY_REQUIRED=NO_FOR_TASK_005_CANDIDATE_EVIDENCE
SAFE_NEXT_ACTION=Resume TASK-004 as a subsequent governed release attempt; first review the current independent Production POST_CLOSE runtime incident, then perform its protected pre-deploy gates. Do not recover 2026-10-05.
```

## 19. Release Recommendation

The candidate release evidence is closed and ready for a subsequent governed
Production release attempt. “Ready” means the candidate passed the bounded
provider, authority, Linux, and regression gates; it does not mean deployed,
published, or recovered. The current live runtime incident must remain visible
to the next release operator.

```text
TASK_STATUS=COMPLETE_RELEASE_EVIDENCE_CLOSED
RELEASE_READY=YES
FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
NO_RECONSTRUCTED_FORMAL_TOPIC_HISTORY=TRUE
```

## Terminal Summary

```text
TASK_STATUS=COMPLETE_RELEASE_EVIDENCE_CLOSED
CANONICAL_BASE=e97f590cad497c0a23fb027fce39ec5891ea4bc1
IMPLEMENTATION_SHA=c610f86302504bba1df4529b8461bbce7042d201
EVIDENCE_CLOSURE_SHA=876489301a8b243e71c19097b428d20b4e2fa231

OFFICIAL_TWSE_2601_20261005_CLOSE=6.45
OFFICIAL_TWSE_2601_20261005_LAST_BID=6.44
OFFICIAL_TARGET_CLOSE_CONFLICT_CONFIRMED=YES
TARGET_CLOSE_ROOT_CAUSE=REPORT_EVIDENCE_ERROR

PREVIOUS_TRADED_CLOSE_DATE=2026-09-22
PREVIOUS_TRADED_CLOSE=5.91
DAILY_COMPARISON_REFERENCE_DATE=2026-10-05
DAILY_COMPARISON_REFERENCE=7.06
CURRENT_CLOSE_DATE=2026-10-05
CURRENT_CLOSE=6.45
EXPECTED_2601_DAILY_RETURN=-0.0864022662889518413597733711

PREVIOUS_CLOSE_AUTHORITY_ROOT_CAUSE=IMMEDIATE_FORMAL_SESSION_CLOSE_WRONGLY_COUPLED_TO_RESUME-DAY_COMPARATOR
GENERIC_RESUME_DAY_FIX_IMPLEMENTED=YES
NO_2601_SPECIAL_CASE=YES

PROVIDER_DATE_AUTHORITY=PASS
PROVIDER_FINALITY_AUTHORITY=PASS
PREVIOUS_TRADED_CLOSE_AUTHORITY=PROVEN
DAILY_COMPARISON_REFERENCE_AUTHORITY=PROVEN
CURRENT_CLOSE_AUTHORITY=PROVEN
PROVIDER_CONTRACT_PREFLIGHT=PASS_FOR_CANDIDATE_READ_ONLY_RECONSTRUCTION

G2_REVALIDATED=YES
G2_PRODUCTION_READY=YES

FOCUSED_TESTS=101 passed
LINUX_CANDIDATE_VALIDATION=PASS
WORKER_RELEASE_BOUNDARY=READY / 110 passed
FULL_BACKEND_RESULT=1271 passed, 23 skipped, 0 failed, 148 deselected; research 84 passed; governance 7 passed
TASK_OWNED_REGRESSION=NONE

PRODUCTION_API_SHA=6fff533168b1823052071f6d88d1f266397d327d
PRODUCTION_WORKER_SHA=6fff533168b1823052071f6d88d1f266397d327d
PRODUCTION_ALEMBIC_HEAD=0049_task_daily_formal_publication_receipt
PRODUCTION_SCHEDULER_STATE=ACTIVE_CONFIGURED; LAST_RUN_EXTERNAL_FAILURE_POST_CLOSE_FINALIZATION_FAILED
COMPETING_SCHEDULER=NONE_CONFIRMED

SUPERSEDES_TASK_003_TARGET_CLOSE_EVIDENCE=YES
SUPERSEDES_TASK_003_PROVIDER_PREFLIGHT_EVIDENCE=YES
TASK_004_BLOCKER_TARGET_CLOSE_RESOLVED=YES
TASK_004_BLOCKER_PROVIDER_FINALITY_RESOLVED=YES

MIGRATION_REQUIRED=NO
CANONICAL_PUSH=NO
PRODUCTION_DEPLOYMENT_EXECUTED=NO
PRODUCTION_WRITE_SET=NONE_BY_TASK_005
TARGET_DATE_2026_10_05_TOUCHED=NO_PRODUCTION_WRITE
HISTORICAL_RECOVERY_EXECUTED=NO
ORIGINAL_FAILED_EXECUTION_PRESERVED=YES
PREVIEW_WORKTREE_TOUCHED=NO
NEXT_TASK_MODIFIED=NO

FORMAL_HISTORICAL_GENESIS_DATE=PENDING_FIRST_NATURAL_SUCCESSFUL_TRADING_SESSION
RELEASE_READY=YES
OWNER_DECISION_REQUIRED=NO
NEXT_ACTION=Resume TASK-004 as a subsequent governed release attempt; review the independent current Production POST_CLOSE runtime failure before any deployment, and do not recover 2026-10-05.
```

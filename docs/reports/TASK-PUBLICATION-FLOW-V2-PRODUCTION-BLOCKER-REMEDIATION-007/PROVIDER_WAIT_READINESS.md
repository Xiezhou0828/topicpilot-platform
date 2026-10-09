# Provider wait readiness

## Calendar

The official TWSE 2026 schedule marks 2026-10-09 as a National Day substitute holiday:
https://www.twse.com.tw/holidaySchedule/holidaySchedule?queryYear=115&response=html

The official TPEx 2026 schedule independently marks 2026-10-09 as the same holiday:
https://www.tpex.org.tw/storage/zh-tw/web/bulletin/trading_date/trading_date_115.htm

Both markets therefore treat 2026-10-09 as non-trading. The next ordinary eligible session is 2026-10-12, subject to any later exceptional notice.

## Runtime evidence

For schedulerDate=2026-10-08, the Worker first emitted WAIT_PROVIDER_NOT_READY with status WAITING_LIVE_VALIDATION. The compact event does not identify whether TWSE or TPEx, the exact product/field, the freshness predicate, or the provider response body. Later repeated events show REFERENCE_PREFLIGHT_PendingRollbackError with status BLOCKED and targetDate=2026-10-08.

Historical source contracts identify separate TWSE/TPEx readiness and date-mismatch codes, but those codes do not identify the actual 2026-10-08 failing product. No Production replay or manual publication was used to infer it.

PROVIDER_WAIT_ROOT_CAUSE=WAIT_PROVIDER_NOT_READY_OBSERVED; EXACT_PROVIDER_AND_FIELD_UNKNOWN
PROVIDER_WAIT_BEHAVIOR=UNRESOLVED
PROVIDER_WAIT_REMEDIATION=BLOCKED

The initial wait may be a legitimate provider-window wait, but the later reference preflight rollback blocker prevents classifying the complete cycle as EXPECTED. Owner-provided provider-level logs or an approved diagnostic role is required.

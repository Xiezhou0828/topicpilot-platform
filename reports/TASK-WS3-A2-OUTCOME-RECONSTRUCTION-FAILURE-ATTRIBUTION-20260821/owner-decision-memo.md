# Owner Decision Memo — TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821

## Decision posture

`STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED`. This run is bounded evidence only. It does not accept, reject, retune, or publish A2.

## What was reconstructed

- Frozen A2 cohort: **5277 events**; accepted daily price rows queried: **288881**.
- Raw daily path was reconstructed for every requested horizon T+1 through T+10 where the accepted surface had enough sessions.
- MFE, MAE, endpoint return, excursion timing, and MFE-before-MAE ordering are null-suppressed for unresolved discontinuity/corporate-action cases.
- Existing MA60-above eligibility was preserved; no MA20 eligibility was introduced.

## Answers for Owner review

1. **Endpoint-only conclusion:** the old T+10 proxy is not a sufficient success/failure semantic. The new path dataset records positive excursion and path ordering; however, the 30 Owner labels are not populated in the repository pack, so a formal success/failure relabel rate cannot be signed off yet.
2. **What appears to be the main issue:** outcome interpretation and data-quality/universe attribution are plausible contributors. Evidence is not sufficient to conclude that A2 formation itself is weak or strong.
3. **Candidate filters:** price >=20, volume >=500 lots, and their combination are reported as ablations only. Retained counts are 4756 / 4759 / 4313 versus 5277 baseline; excluded positive proxies remain an opportunity-cost check, not a rule recommendation.
4. **Clean failures vs successes:** cannot be formally separated until Owner supplies labels for all 30 cases. Source-only path candidates are explicitly marked descriptive and are not substituted for Owner labels.
5. **2327 / 2025-08-05:** adjustment is unresolved and the path metrics are fail-closed; do not interpret its raw MFE/MAE or endpoint.
6. **3675 / 2026-07-06:** no PIT-safe TAIEX, breadth, or same-theme/industry evidence was available in the reviewed artifacts. Performance remains included when data-quality checks permit; it is not deleted or automatically marked as systematic shock.

## Required Owner decisions

- Populate the canonical 30-case Owner labels and rerun the reconciliation.
- Provide or authorize the PIT-safe market breadth/index/peer panel needed for regime attribution.
- Confirm adjusted-series/corporate-action coverage for the full outcome window, especially 2327/2025-08-05.
- Only then decide whether evidence is sufficient for a separate A2 strategy-review work item. No candidate filter is a production rule in this run.

`A_SETUP_ACCEPTED=NO` · `A_STRATEGY_ACCEPTED=NO` · `PRODUCTION_MUTATION=NO` · `DEPLOY=NO` · `PUSH=NO` · `NEXT_TASK_CHANGED=NO`

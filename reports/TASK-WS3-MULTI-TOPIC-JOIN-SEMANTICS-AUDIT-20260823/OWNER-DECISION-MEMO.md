# Owner Decision Memo — TASK-WS3-MULTI-TOPIC-JOIN-SEMANTICS-AUDIT-20260823

## Requested Owner Review

Please review whether the unique-topic join should remain the research join for lifecycle-conditioned evidence. This task makes no production or strategy decision and does not rerun final expectancy/performance conclusions.

## Evidence answer

The ambiguity is primarily legitimate multi-topic exposure, not an invalid signal. The prior selector treated multiple current topic relations without a unique representative/primary as unusable. The exposure audit retains all signal-date-valid relations and deduplicates the signal observation after exposure-level lifecycle evaluation.

Ambiguous root-cause primary counts: `{"MULTIPLE_LEGITIMATE_TOPIC_RELATIONS": 1602, "MULTIPLE_MAIN_RISE_EXPOSURES": 204, "MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES": 229, "MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE": 130}`.

| Cohort | prior ambiguous | strict signal-date exposure eligible | recovered from ambiguous | D-1 confirmed current | D-1 strict exposure | D-1 current-taxonomy proxy* |
|---|---:|---:|---:|---:|---:|---:|
| A2 | 1226 | 14 | 2 | 8 | 0 | 14 |
| LEGACY5 | 631 | 7 | 0 | 5 | 0 | 5 |
| BOTH_SAME_SESSION | 308 | 0 | 0 | 0 | 0 | 0 |

*The current-taxonomy proxy is an upper-bound diagnostic only: it ignores relation effective dates and is not signal-date-valid eligibility. The strict exposure counts are therefore fail-closed where the current authority does not support historical relation validity.

Across the full signal cohorts, strict signal-date-valid exposure eligibility is A2=14, Legacy-5=7, BOTH=0; the current-taxonomy non-PIT proxy is A2=1,416, Legacy-5=652, BOTH=262. Among previously ambiguous observations, strict recovery is A2=2, Legacy-5=0, BOTH=0, while the non-PIT proxy upper bound is A2=361, Legacy-5=167, BOTH=72.

## Owner decisions not made here

- `CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE` is answered **NO for research exposure analysis**; it remains a conservative fail-closed selector for any surface that explicitly requires one topic.
- `EXPOSURE_BASED_JOIN_RESEARCH_READY` is **YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS**.
- No Lifecycle policy or product contract change is proposed by this artifact.
- No accepted strategy, recommendation publication, Opportunity activation, production filter, DB mutation, deploy, push, or NEXT_TASK change is authorized.

## Final statuses

```text
MULTI_TOPIC_AMBIGUITY_ROOT_CAUSE=LEGITIMATE_MULTI_TOPIC_EXPOSURE_PREDOMINANT
CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE=NO_FOR_RESEARCH_EXPOSURE_CONTEXT
EXPOSURE_BASED_JOIN_RESEARCH_READY=YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS
LOOKAHEAD_LEAKAGE_SAFE=YES_WITH_SIGNAL_DATE_RELATION_BOUNDARY
EVENT_LEVEL_DEDUP_SAFE=YES
D1_SAMPLE_IMPACT=SEE_PRE_MAIN_RISE_SAMPLE_IMPACT_PREVIEW_CSV
PRODUCTION_CHANGE=NO
```

# Formal Closure — TASK-WS3-MULTI-TOPIC-JOIN-SEMANTICS-AUDIT-20260823

## Disposition

`COMPLETE_PASS_WITH_BOUNDED_RESEARCH_LIMITATIONS; STOP_AT_OWNER_REVIEW`. This is a WS3-only join-semantics audit and sample-impact preview. It is not a final expectancy rerun, accepted strategy, recommendation publication, Opportunity activation, or production filter.

## Dataset and authority

- L5: current-taxonomy historical lifecycle reconstruction, 16,250 topic/date rows, declared identity `17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95`; retrospective/non-PIT.
- Current relation authority: 852 selected rows; relation hash `6f376241f8f6ee4f548ce54b628695bf3ff6563c0e06a8bbbf228c77c657a8a2`.
- A2: existing 5,277 event observations; Legacy-5: existing 2,471 distinct episodes; BOTH: existing 560 same-session pairs represented as 1,120 source observations.
- Signal definitions and Lifecycle policy were not changed.

## Root-cause conclusion

The prior unique-topic join marked **2165** observations ambiguous across A2/Legacy-5/BOTH. The primary reason distribution is `{"MULTIPLE_LEGITIMATE_TOPIC_RELATIONS": 1602, "MULTIPLE_MAIN_RISE_EXPOSURES": 204, "MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES": 229, "MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE": 130}`. The exposure semantic makes **2** currently ambiguous observations research-eligible under the strict rule of at least one signal-date-valid relation with a valid five-stage L5 row; the current-taxonomy non-PIT proxy upper bound for ambiguous recovery is A2=361, Legacy-5=167, BOTH=72.

This supports legitimate multi-topic membership as the dominant root cause in the current-taxonomy candidate relation set. However, strict signal-date-valid exposure eligibility is bounded by the relation effective-date evidence; current-taxonomy proxy counts are not promoted to historical membership truth. Missing/no-topic and lifecycle-unavailable evidence remain separate fail-closed categories and are not silently rescued.

## D-1 / transition impact

The sample-impact preview evaluates current versus exposure-based linkage for candidate onset and confirmed transition events across D-3/D-2/D-1/D0. Counts are signal observations after event-level deduplication; exposure links are disclosed separately. D0 is contemporaneous only.

| Cohort | current D-1 confirmed | strict exposure D-1 | recovered from current ambiguity | current-taxonomy proxy D-1* | proxy links collapsed |
|---|---:|---:|---:|---:|---:|
| A2 | 8 | 0 | 0 | 14 | 0 |
| LEGACY5 | 5 | 0 | 0 | 5 | 0 |
| BOTH_SAME_SESSION | 0 | 0 | 0 | 0 | 0 |

*The proxy ignores relation effective dates and is not a valid historical sample. It is included only to quantify the possible effect if current taxonomy were later authorized as a retrospective exposure proxy; it is not used as a conclusion here.*
No final expectancy, MFE/MAE, barrier, or performance conclusion was recalculated in this task. The preview is a Strategy Review input for deciding whether a separately authorized exposure-based re-run is warranted.

## Look-ahead and deduplication controls

- Topic membership uses only signal-date-valid relations; future transition information is not used for assignment.
- Each exposure uses the same-date L5 row; D-3/D-2/D-1 exclude later transition evidence; D0 is separately labeled.
- Multiple topic exposures do not create duplicate returns; deduplication key is `cohort|signal_id`.
- Browser/ad-hoc replacement and imputation: NO.

## Governance

```text
WS3_ONLY=YES
RESEARCH_ONLY=YES
E_DRIVE_ONLY=YES
C_DRIVE_NEW_ARTIFACTS_CREATED=NO
LIFECYCLE_POLICY_CHANGED=NO
A2_DEFINITION_CHANGED=NO
LEGACY5_DEFINITION_CHANGED=NO
BOTH_DEFINITION_CHANGED=NO
STRATEGY_DEFINITION_CHANGED=NO
STRENGTH_SCORE_CREATED=NO
PRODUCTION_FILTER_CREATED=NO
FORMAL_RECOMMENDATION_PUBLICATION=NO
OPPORTUNITY_PRODUCTION_ACTIVATION=NO
DB_MUTATION=NO
DEPLOY=NO
PUSH=NO
NEXT_TASK_CHANGED=NO
FINAL_EXPECTANCY_RERUN=NO
STOP_AT_OWNER_REVIEW=YES
```

## Final statuses

```text
MULTI_TOPIC_AMBIGUITY_ROOT_CAUSE=LEGITIMATE_MULTI_TOPIC_EXPOSURE_PREDOMINANT
CURRENT_UNIQUE_JOIN_SEMANTICS_APPROPRIATE=NO_FOR_RESEARCH_EXPOSURE_CONTEXT
EXPOSURE_BASED_JOIN_RESEARCH_READY=YES_WITH_BOUNDED_RETROSPECTIVE_NON_PIT_LIMITATIONS
LOOKAHEAD_LEAKAGE_SAFE=YES_WITH_SIGNAL_DATE_RELATION_BOUNDARY
EVENT_LEVEL_DEDUP_SAFE=YES
D1_SAMPLE_IMPACT=STRICT_EXPOSURE_COUNTS_AND_NON_PIT_PROXY_COUNTS_IN_PREVIEW_CSV
PRODUCTION_CHANGE=NO
```

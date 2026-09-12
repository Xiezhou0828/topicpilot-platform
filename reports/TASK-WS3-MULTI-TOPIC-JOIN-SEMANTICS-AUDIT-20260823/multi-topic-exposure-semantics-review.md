# Multi-Topic Exposure Semantics Review — TASK-WS3-MULTI-TOPIC-JOIN-SEMANTICS-AUDIT-20260823

## Question under review

The previous research join assumed `Signal → unique Topic → Lifecycle`. This review tests whether the ambiguity gate was caused by legitimate multi-topic membership and whether a research-only alternative should be `Signal → all legitimate signal-date exposures → Lifecycle per exposure → event-level deduplication`.

## Current implementation

The prior selector reads the current 852-row non-superseded, open-ended relation authority. It accepts one unique REPRESENTATIVE, then one unique PRIMARY/REPRESENTATIVE, then one unique relation. Multiple unresolved candidates become `AMBIGUOUS_TOPIC_MATCH`; the signal is not silently assigned to one topic.

This is conservative for a one-topic surface, but it is too lossy for a research question such as `has_MAIN_RISE_exposure`. A stock may legitimately belong to several topics with different stages, or several topics at the same stage, without creating several return observations.

## Root-cause results

The audit classified all **2165** ambiguous observations. Primary reasons: `{"MULTIPLE_LEGITIMATE_TOPIC_RELATIONS": 1602, "MULTIPLE_MAIN_RISE_EXPOSURES": 204, "MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES": 229, "MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE": 130}`. Relation duplicate/data-quality ambiguity was zero. Missing/no-topic and missing lifecycle rows remain separate coverage categories, not reclassified as multi-topic ambiguity.

| Reason | Count | Interpretation |
|---|---:|---|
| MULTIPLE_LEGITIMATE_TOPIC_RELATIONS | 1,602 | More than one current-taxonomy topic relation; no unique representative/primary answer |
| MULTIPLE_MAIN_RISE_EXPOSURES | 204 | Multiple current-taxonomy candidate topics have MAIN_RISE L5 evidence |
| MULTIPLE_TOPICS_DIFFERENT_LIFECYCLE_STAGES | 229 | Candidate exposures show more than one valid Lifecycle stage |
| MULTIPLE_TOPICS_SAME_LIFECYCLE_STAGE | 130 | Candidate exposures share one valid Lifecycle stage |

These categories are primary-reason labels; the CSV also carries overlapping reason flags, per-topic candidate details, signal-date-valid exposure details, and lifecycle-evidence flags for row-level review.

## Strict exposure semantics versus retrospective proxy

Strict research eligibility requires a relation effective at the signal date and a same-date L5 row with one of the five lifecycle stages. The current relation authority has `valid_from` dates in a narrow late-August 2026 range, so early signal dates do not have sufficient PIT relation evidence. Those rows fail closed.

The current-taxonomy proxy is reported only as an upper bound: it keeps all current relation candidates and joins their same-date retrospective L5 rows while explicitly ignoring relation effective dates. It is not a historical membership claim and is not used as a final sample.

| Cohort | observations | strict exposure eligible | strict recovery from ambiguous | current-taxonomy proxy eligible* | proxy recovery from ambiguous* |
|---|---:|---:|---:|---:|---:|
| A2 | 5277 | 14 | 2 | 1416 | 361 |
| LEGACY5 | 2471 | 7 | 0 | 652 | 167 |
| BOTH_SAME_SESSION | 1120 | 0 | 0 | 262 | 72 |

*Proxy values are not PIT-eligible and must not be used to restate prior expectancy conclusions.*

## D-window impact preview

D-3/D-2/D-1/D0 are evaluated as signal-date exposure linkage only. Candidate onset and confirmed transition remain separate. D0 is contemporaneous and not predictive. The CSV reports current unique-join counts, strict exposure counts, event-level deduplicated signal counts, and non-PIT proxy upper bounds for every window.

| Cohort | confirmed D-1 current | confirmed D-1 strict exposure | confirmed D-1 proxy upper bound |
|---|---:|---:|---:|
| A2 | 8 | 0 | 14 |
| LEGACY5 | 5 | 0 | 5 |
| BOTH_SAME_SESSION | 0 | 0 | 0 |

## Research disposition

Exposure-based joining is suitable for a separately authorized retrospective research rerun only after the membership/PIT limitation is resolved or explicitly accepted as a non-PIT proxy. It is not a Lifecycle policy change, product contract promotion, or production filter. No final expectancy/performance conclusion is rerun here.

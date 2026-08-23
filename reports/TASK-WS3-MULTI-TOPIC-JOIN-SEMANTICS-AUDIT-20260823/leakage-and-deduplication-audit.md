# Leakage and Deduplication Audit — TASK-WS3-MULTI-TOPIC-JOIN-SEMANTICS-AUDIT-20260823

## Scope and non-goals

This is an audit-only, WS3 research artifact. It does not rerun final expectancy/performance conclusions and does not modify Lifecycle policy, taxonomy, signal definitions, A2, Legacy-5, BOTH, DB, frontend, production filters, or NEXT_TASK.

The L5 input is the current-taxonomy historical reconstruction (`CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION`), not PIT historical authority. It is retained as retrospective research evidence only.

## Current versus exposure semantics

The prior implementation first selected one current, non-superseded relation per instrument using a unique REPRESENTATIVE/PRIMARY fallback. Two or more unresolved candidates became `AMBIGUOUS_TOPIC_MATCH`; no return observation was emitted from that join.

The audited research semantic filters the same relation authority by `valid_from <= signal_date <= valid_to` (open-ended `valid_to` is allowed), keeps every legitimate topic exposure, joins each exposure to the same-date L5 row, and qualifies the signal when at least one exposure has a five-stage lifecycle row.

No future lifecycle stage, candidate onset, confirmed transition date, or forward outcome is used to choose a topic or construct the signal-date exposure set.

Strict signal-date-valid exposure observations with a five-stage L5 row: **A2=14, LEGACY5=7, BOTH_SAME_SESSION=0**. Observations with current relations but no relation effective at the signal date: **A2=4579, LEGACY5=2190, BOTH_SAME_SESSION=990**. This is a source-coverage limitation, not permission to use a current-taxonomy proxy as PIT truth.

## D-window leakage controls

- D-3 uses only the event inventory's D-3 date and the signal-date-valid exposure set.
- D-2 excludes D-1 and D0 transition evidence; D-1 excludes D0 evidence.
- D0 is separately labeled `CONTEMPORANEOUS_TRANSITION_CONDITIONED`; it is not presented as predictive lift.
- Candidate onset and confirmed transition are separate event semantics; neither is used to assign a signal topic.
- Transition event topic IDs are used only after signal-date membership is resolved, to test retrospective event linkage.
- No browser-side or ad-hoc replacement values are used.

## Event-level deduplication

The deduplication key is `cohort|signal_id`. Exposure links may be one-to-many, but a stock-date-signal observation remains one return observation. The preview reports both exposure links and unique signal observations; `event_level_dedup_collapsed_exposure_links` is the explicit difference.

Duplicate link audit rows with non-zero duplicate collapse count: **0** (duplicate links are collapsed deterministically, not counted as separate returns).

## Research limitations

- Current relations are the 852-row current authority selection; signal-date validity is evaluated from relation effective dates but historical topic membership remains retrospective/non-PIT.
- Missing/no-topic and unavailable lifecycle evidence remain fail-closed and are not imputed.
- Exact matched-control inference is not performed by this task.
- The audit produces sample-impact input only; it does not accept or reject a strategy.

Source root: `E:\topicpilot-platform-canonical`; current relation selection hash: `6f376241f8f6ee4f548ce54b628695bf3ff6563c0e06a8bbbf228c77c657a8a2`.

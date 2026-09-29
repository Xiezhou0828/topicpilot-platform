# Today Lower-Half V1 Contract

Status: implementation candidate for `TASK-TODAY-MAINLINE-TOPIC-PULSE-ROTATION-CANONICAL-REDESIGN-013`.

This contract governs the three lower-half Today sections:

1. 今日主線 (`mainTopics`)
2. 題材動態快訊 (`marketPulse` / `marketEvents`)
3. 快速升溫／快速退潮 (`heatingTopics` / `coolingTopics`)

## Authority and boundary

All three sections read the current effective formal Topic universe from
published, final, non-superseded `topic_snapshots`, joined to the published
formal Topic Strength and Lifecycle results for the same evaluation date.
The universe is dynamic: enabled/retired status, formal publication state,
effective date, finality, and supersession determine inclusion. No fixed Topic
count is used.

Today is a read/presentation layer. It does not recalculate Topic Strength,
Grade, Lifecycle, Structural Role, Relation Weight, observation policy,
candidate confirmation, or rotation thresholds. Missing formal authority is
typed as unavailable and is never filled from legacy snapshot heuristics.

## 今日主線

An item is eligible only when the current formal row is evaluable, has at least
three formal members, has a formal Daily Grade and Lifecycle, has valid
authority quality, and is not `DECLINING`. `DECLINING` remains visible in the
other two sections.

The result is exactly the first three eligible rows when three or more exist;
otherwise it contains the available eligible rows and remains fail-closed.
The deterministic lexicographic order is:

1. Lifecycle: `MAIN_RISE > FERMENTING > MATURE > SPROUTING > BASE`
2. Daily Grade: `S > A > B > D`
3. valid forward Lifecycle candidate first, only within the same Lifecycle and
   Grade tier
4. absolute Topic Strength descending
5. relative Strength descending, when available
6. formal coverage descending as a late quality tie-breaker
7. Topic slug ascending

No Mainline Score, weighted composite, or browser-side ranking is introduced.
Cards expose Grade, Lifecycle, absolute/relative scores, candidate progress,
formal member count, and authority metadata. `currentState` is retained only
as a compatibility field and is not Today authority.

Topics with one or two formal members are `X_NOT_FOCUS` / `X／暫不關注` and are
not Mainline or rotation candidates. Other incomplete rows are
`NOT_EVALUABLE`; Grade, Lifecycle, and scores are not fabricated.

## 題材動態快訊

The backend returns every current effective formal Topic, not the Mainline Top
3 and not only changed rows. Each item links to `/topics/{slug}`. Evaluable
items expose formal Grade/Lifecycle; small samples expose X and other
authority gaps expose `NOT_EVALUABLE` without invented state.

One deterministic primary event is selected per Topic with this priority:

1. confirmed Lifecycle transition
2. new candidate or candidate confirmation progress
3. Daily Grade change
4. material absolute/relative divergence
5. renewed expansion
6. newly accepted observation flag
7. persistence / `狀態延續`

Change classification compares the current row with the latest previous
governed/evaluable formal row. If no comparable row exists, the Topic remains
visible with `NO_HISTORY`, and no transition, grade change, or streak is
invented. Event payloads contain `dataDate`, formal source, priority, typed
from/to state, and evidence; `eventTime` is nullable and is not populated with
a fake intraday timestamp.

The frontend defaults to `全部`, provides `有變化`, shows counts from the
backend envelope, and uses explicit keyboard-accessible pagination. There is
no automatic marquee and no Play/Pause ticker model.

## 快速升溫／快速退潮

The trigger is formal absolute Topic Strength only:

`strengthDelta5d = current_absolute_score - median(previous five governed/evaluable formal sessions)`

The current session is excluded from the baseline. Fewer than five complete
prior sessions, missing formal scores, or missing any Topic session make that
Topic not evaluable; no zero-fill, calendar-day fallback, `average_change`,
Grade, Lifecycle, or relative-score trigger is used.

`FAST_WARMING` is `delta >= +10.0`; `FAST_COOLING` is `delta <= -10.0`.
Every qualifying Topic is returned. Warming is ordered by delta descending;
cooling by delta ascending, then stable Topic slug. Grade/Lifecycle and
relative score are context only. The frontend exposes the delta, current
absolute score, Grade, Lifecycle, baseline median, and explicit section state.

Insufficient startup history makes only these two sections
`INSUFFICIENT_FORMAL_STRENGTH_HISTORY`; it does not block Mainline or Topic
Pulse.

## Publication and compatibility

`marketOverview`, Daily Focus, and the existing Home publication gate remain
unchanged. Lower-half section failure is represented in its own section
status and does not invalidate an otherwise valid Home publication. The
existing Market Signal V1 and Opportunity authorities are separate contracts.

Legacy fields may remain in generated compatibility payloads, but they are not
used as formal Today authority:

| Legacy behavior | Disposition |
| --- | --- |
| completeness/coverage/positive-count/average-change ranking | `REMOVED_FROM_FORMAL_TODAY` |
| `topic_direction`, `WARMING`, `COOLING`, `FLAT` presentation | `REMOVED_FROM_FORMAL_TODAY` |
| `average_change` display as strength | `SUPERSEDED` |
| 14-session endpoint rotation | `SUPERSEDED` |
| Top-3 rotation truncation | `REMOVED_FROM_FORMAL_TODAY` |
| `TopicPulseTicker` duplicate Mainline resource | `REMOVED_FROM_FORMAL_TODAY` |
| compatibility fields required by older clients | `LEGACY_COMPATIBILITY_ONLY` |

No migration or persistent schema change is required: existing formal Topic
snapshot, Score, Lifecycle, and history tables are sufficient.

# TASK-TODAY-MAINLINE-TOPIC-PULSE-ROTATION-CANONICAL-REDESIGN-013

## Scope

This candidate replaces the legacy lower-half Today semantics for Mainline,
Topic Pulse, and Fast Warming/Cooling. It does not change Topic Strength or
Lifecycle policy, Opportunity authority, Market Signal V1, A10 publication
machinery, or production state.

## Repository and authority lineage

- Repository: `E:\TopicPilot\topicpilot-platform`
- Canonical base SHA: `6cb88c0d7fceb45b244d295883636706f50ea0be`
- Topic Strength/Lifecycle authority lineage SHA:
  `eb358c10968a78772376020a605edd62253e6dc4`
- Candidate branch: `codex/today-mainline-topic-pulse-rotation-redesign-013`
- Candidate SHA: filled after the final candidate commit

The candidate was developed in an isolated worktree and preserved the newer
Owner-seeded V0 forward-observation lineage and the existing Market Signal V1
read path.

## Legacy audit and disposition

| Legacy behavior | Status | Replacement |
| --- | --- | --- |
| completeness / observed count / coverage / positive count / average-change Mainline heuristic | `REMOVED_FROM_FORMAL_TODAY` | Formal authority + lexicographic Lifecycle/Grade/candidate/absolute/relative/coverage/slug order |
| `topic_direction` as Today state | `REMOVED_FROM_FORMAL_TODAY` | Formal Lifecycle and typed authority state |
| `WARMING`, `COOLING`, `FLAT` Mainline presentation | `REMOVED_FROM_FORMAL_TODAY` | Grade, Lifecycle, absolute and relative Strength |
| `average_change` as Mainline strength | `SUPERSEDED` | Formal absolute Topic Strength |
| 14-session endpoint rotation | `SUPERSEDED` | Previous five-session absolute-strength median |
| Top-3 heating/cooling truncation | `REMOVED_FROM_FORMAL_TODAY` | Return all threshold-qualified Topics |
| `TopicPulseTicker` reusing Mainline Top 3 | `REMOVED_FROM_FORMAL_TODAY` | Full formal Topic universe with primary events and explicit pagination |
| old compatibility fields required by clients | `LEGACY_COMPATIBILITY_ONLY` | Retained only where generated/runtime contracts require them |

## Implemented authority map

`_formal_topic_state_rows` dynamically reads current effective formal snapshots
and joins published active formal Score and Lifecycle rows. Superseded,
retired, unavailable, or incomplete rows fail closed. No Topic count is
hard-coded and no migration is needed.

### Mainline

Mainline eligibility requires evaluable formal authority, at least three formal
members, formal Daily Grade, formal Lifecycle, valid authority quality, and a
Lifecycle other than `DECLINING`. Lifecycle order is
`MAIN_RISE > FERMENTING > MATURE > SPROUTING > BASE`; Grade order is
`S > A > B > D`. Candidate presence is only a tie-breaker within equal
Lifecycle and Grade. Absolute Strength precedes relative Strength; coverage is
a late deterministic tie-breaker. The backend returns at most three eligible
rows and never fills with X or NOT_EVALUABLE rows.

### Topic Pulse

The backend returns all current formal Topics, including X and
NOT_EVALUABLE rows. Current state is compared with the latest previous formal
row when available. Primary event priority is Lifecycle transition, candidate
progress, Grade change, absolute/relative divergence, renewed expansion,
observation flag, then persistence. Without history it returns `NO_HISTORY`
and does not invent a change or streak. `eventTime` is nullable; the payload
uses formal `dataDate` and typed evidence instead of a fake intraday time.

The web surface uses `全部` and `有變化` filters and explicit pagination. Every
row links to `/topics/{slug}`.

### Fast Warming/Cooling

The backend compares current formal absolute Strength with the median of the
previous five governed/evaluable formal sessions. The current session is
excluded. `>= +10.0` is warming and `<= -10.0` is cooling; strict interior
values are excluded. All qualifying rows are returned, ordered by delta
descending for warming and ascending for cooling, then stable slug. Relative
Strength and Grade/Lifecycle are context only. Fewer than five complete prior
sessions yields `INSUFFICIENT_FORMAL_STRENGTH_HISTORY` for rotation only.

## API and frontend changes

- Extended `HomeTopicCard`, `HomeMarketPulseEvent`, and `HomeRotationTopic`
  with formal Topic ID, absolute/relative fields, Lifecycle/candidate and
  confirmation metadata, persistence/observation evidence, event priority and
  state transitions, and canonical 5D rotation fields.
- Kept the existing Home top-level sections and publication gate.
- Regenerated `packages/api-client/openapi.json`, the package schema, and the
  web generated API declarations.
- Replaced Mainline card legacy state emphasis with formal Grade, Lifecycle,
  absolute/relative scores, and candidate progress.
- Replaced the duplicate ticker with a full-universe Topic Pulse panel;
  automatic scrolling and Play/Pause controls are removed.
- Rotation cards show formal absolute score, baseline median, delta, Grade,
  and Lifecycle without browser-side calculation.

## Validation

Validated during this candidate:

- focused backend: `29 passed`
- OpenAPI drift: passed
- generated client check: passed
- frontend typecheck: passed
- frontend tests: `183 passed`
- frontend production build: passed
- frontend lint: passed with one pre-existing warning in
  `apps/web/app/components/FavoriteButton.tsx`
- Ruff: passed for changed backend modules/tests
- migration graph: one linear head, `0047_task_topic_role_strength_design_freeze`
- broader backend excluding the unrelated corporate-action fixture suite:
  `883 passed, 59 skipped`
- full backend: `898 passed, 59 skipped, 10 failed` in the pre-existing
  corporate-action/reference-bundle suite because the checked-in
  `tw-reference-v1` fixture version/effective-date controls do not match the
  current corporate-action expectations; no files in that suite were changed
- diff check: passed

Migration graph, broader backend suite, and final diff/remote checks are
recorded in the final status block below after completion.

## Migration and production status

`MIGRATION_REQUIRED=NO`. No migration was created or applied. No production
database was mutated, no Home publication was manually changed, and nothing
was deployed or merged.

## Final status

The candidate is intended to finish in:
`COMPLETE_TODAY_TOPIC_LOWER_HALF_V1_IMPLEMENTATION_CANDIDATE_READY`.

Final machine-readable status is maintained in the delivery response and must
include the candidate SHA, remote branch SHA, validation outcomes, and the
bounded startup limitation that rotation remains unavailable until five prior
formal absolute-score sessions exist.

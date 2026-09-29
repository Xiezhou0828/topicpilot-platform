# TASK-TODAY-MAINLINE-TOPIC-PULSE-ROTATION-CANONICAL-PROMOTION-014

## Promotion scope

This promotion reconciles the Today lower-half V1 delta from Task 013 onto
the latest canonical `main`. It does not replay the pre-promotion Topic
Strength/Lifecycle lineage and does not deploy or activate production.

| Item | Value |
| --- | --- |
| Latest canonical main at refresh | `1a1bc1a6fb925887e743b694c6d132c061578e9b` |
| Original 013 candidate | `08e25e15a9977a503b42889d866468a5e7fd3c4e` |
| Refresh merge base | `eb358c10968a78772376020a605edd62253e6dc4` |
| Refresh divergence | `ahead 6 / behind 14` |
| Reconciled implementation candidate | `47e4bb7` (`feat(today): finalize formal lower-half redesign`) |
| Migration | None created or applied |

## Canonical reconciliation

- Topic Strength/Lifecycle remains owned by the canonical formal result read
  models already on `main`: formal Daily Grade, Absolute Score, Relative Score,
  Lifecycle, candidate/confirmation progress, persistence, and observation
  flags are consumed as persisted facts.
- Today Market Signal V1 from PR #13 remains in place, including its frozen
  catalog, five families, temporal state, 20-day occurrence, frequency text,
  backend authority, and frontend non-rederivation. The conflict in
  `home_v2_publication.py` was resolved by retaining institutional flow,
  signal observations, signal history, and the existing Home publication gate,
  while adding Topic Pulse and five-session absolute-strength rotation.
- Mainline now ranks only formal/evaluable rows with lifecycle order
  `MAIN_RISE > FERMENTING > MATURE > SPROUTING > BASE`, excludes `DECLINING`,
  then applies grade, candidate, absolute score, relative score, coverage,
  and stable slug tie-breakers. No synthetic Mainline Score is introduced.
- Topic Pulse returns the full current effective formal Topic universe, orders
  changed items first, supports ALL and CHANGED frontend filters, and uses a
  deterministic primary event/persistence presentation. Small samples remain
  visible as `X_NOT_FOCUS` without fabricated Grade/Lifecycle.
- Fast rotation uses formal Absolute Score against the median of the previous
  five governed/evaluable sessions, with inclusive `+10` warming and `-10`
  cooling thresholds. It returns all qualifying Topics and remains
  `INSUFFICIENT_FORMAL_STRENGTH_HISTORY` until five prior sessions exist.
- Legacy 14D `average_change` rotation, formal WARMING/COOLING/FLAT Mainline
  states, TopicPulseTicker duplication, and rotation Top-3 truncation remain
  superseded.

## Schema and generated contract

The canonical FastAPI schema was checked and the committed OpenAPI document
was regenerated from the application source. The generated API schema and
frontend declaration were synchronized with `packages/api-client` and the
client contract tests passed. No migration was needed because this delta is a
read-model/presentation change over existing canonical tables.

## Validation

- Focused backend: 38 passed, covering lower-half semantics, Home publication,
  Market Signal V1, and Topic Strength/Lifecycle read-model behavior.
- Frontend: build passed; TypeScript passed; full suite passed 183/183.
- API client: 4 generated-client tests passed; OpenAPI drift passed; Ruff
  passed; frontend lint passed with one existing warning in
  `apps/web/app/components/FavoriteButton.tsx` (missing `state` hook
  dependency, no lint errors).
- Migration graph: one head, `0047_task_topic_role_strength_design_freeze`;
  database foundation tests: 4 passed, 1 PostgreSQL integration test skipped
  because no test database URL was configured.
- Diff check and secret-scan policy passed.
- Full backend comparison was run on both latest canonical `main` and the
  reconciled candidate. Both had the identical 10 failures in
  `test_corporate_action_dataset.py` caused by the checked-in
  corporate-action/reference-bundle mismatch; the candidate introduced no
  new failure. These are classified `PRE_EXISTING_CANONICAL`.
- Docker Compose smoke was attempted with the repository CI flow. The local
  environment has Docker Desktop's CLI but no running Linux engine / WSL
  integration, so the smoke could not start the daemon. This remains a CI
  environment limitation and is not classified as a code regression.

## PR and merge

The preferred PR title is:

> Promote Today Mainline, Topic Pulse and Fast Rotation V1

The PR body states that Topic Strength authority is already canonical, Today
Market Signal V1 is preserved, the lower-half semantics are the new delta,
and legacy WARMING/COOLING plus 14D rotation remain superseded.

- PR: [#16](https://github.com/Xiezhou0828/topicpilot-platform/pull/16)
- Title: `Promote Today Mainline, Topic Pulse and Fast Rotation V1`
- PR head when opened: `d2ec93a24e544cc5b9b470d3462bee44db7051ee`
- Remote required CI and merge: pending at this report revision; the final
  exact head, CI result, merge commit, and post-merge CI are recorded in the
  promotion status block.

## Production boundary

No deployment was performed. No production runtime was activated and no
production database was mutated. The next task is the separately governed
production activation task:

`TASK-TODAY-TOPIC-LOWER-HALF-PRODUCTION-ACTIVATION-015`

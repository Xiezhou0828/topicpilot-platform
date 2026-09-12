# Collision reconciliation report

Task: `TASK-WS1-LIFECYCLE-CANONICAL-COLLISION-RECONCILIATION-AND-PROMOTION-READINESS-20260822`

## Result

`RECONCILIATION=PASS`

`PROMOTION=NO_OWNER_DIRTY_STATE_PRESERVED_AND_BASELINE_TS_GATE`

The fresh candidate is based directly on latest canonical `b569430d2a358cab6a5915aeaacff2810df4913c`. WS1 source implementation `f7894b4` was applied as a working-tree patch and then rebased onto the newer canonical WS3-only commit. The reconciled candidate code commit is `c46506e`.

## Overlap provenance

The two canonical overlap files are uncommitted Owner working-tree changes. No commit hash was available for their provenance; the local evidence is the canonical `git diff` plus the related untracked publication-disclosure regression test.

- `apps/web/app/components/v2/TopicListPage.tsx`: Owner adds field-level publication disclosure, formal/unavailable state badges, and preserves the no-formal-publication boundary.
- `apps/web/app/lib/topic-api.ts`: Owner changes transport/source disclosure and prevents configured API failures from silently falling back to Preview rotation data.

## Three-way result

- `TopicListPage.tsx`: semantic overlap existed in imports, lifecycle rendering, and source typing. The candidate retains Owner disclosure behavior and WS1 backend-enum lifecycle mapping through `ownerStageFromBackend`; no stage or threshold was changed.
- `topic-api.ts`: Owner source/fallback behavior and WS1 lifecycle availability/lineage typing were combined cleanly.
- `f7894b4` to `c46506e` differs only in these two overlap files; the candidate rebase additionally carries canonical WS3 commit `b569430d` unchanged.
- Backend lifecycle engine, migration, persistence, scheduler hook, and shadow probe are byte-equivalent to the WS1 source implementation.

## Promotion disposition

The WS1-scoped candidate code and tests are ready, but global promotion is held. Committing or overwriting the two dirty Owner files would change Owner dirty-state semantics. Full-project TypeScript also has an existing non-WS1 failure in `today-home.ts` versus the canonical untracked `api-client` contract; the changed-file TypeScript check passes. The canonical working tree remains untouched; do not blind cherry-pick `f7894b4` or `c46506e`.

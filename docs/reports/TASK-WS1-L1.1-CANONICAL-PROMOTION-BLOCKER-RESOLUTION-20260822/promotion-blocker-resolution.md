# L1.1 Canonical Promotion Blocker Resolution

Task: `TASK-WS1-L1.1-CANONICAL-PROMOTION-BLOCKER-RESOLUTION-20260822`

Date: 2026-08-22

## Decision

- `PROMOTION=NO`
- `CANONICAL_FORWARD_SHADOW_RUNTIME_READY=NO`
- `OWNER_DIRTY_INTEGRATION=SAFE_IN_ISOLATED_CANDIDATE`
- `UNIQUE_REMAINING_BLOCKER=GENERATED_API_CLIENT_DATASTATUS_CONTRACT_DRIFT`
- `LIFECYCLE_SEMANTICS_MODIFIED=NO`

The WS1 candidate was not promoted. Canonical was not modified, reset, cleaned, or overwritten.

## Canonical and candidate lineage

- Latest canonical HEAD: `b569430d2a358cab6a5915aeaacff2810df4913c`
- Isolated candidate HEAD: `c9239d66bcc3c330010ab8830d4184430efe9bfc5`
- WS1 implementation commit: `c46506e8dd3fd35cba103c0f0728da03e1a5eaf9`
- Candidate merge-base with canonical: `b569430d2a358cab6a5915aeaacff2810df4913c`
- Candidate branch status: clean
- Canonical Owner tracked dirty overlap remains exactly:
  - `apps/web/app/components/v2/TopicListPage.tsx`
  - `apps/web/app/lib/topic-api.ts`

The latest canonical commit is the WS3 A2 artifact promotion. Its changed paths do not overlap the WS1 implementation paths.

## Blocker 1 — Owner dirty overlap

### Result: safely reconcilable in isolation

The candidate contains the Owner changes in both overlapping files. A read-only candidate-versus-Owner-worktree comparison showed only WS1 additions/remapping on top of the Owner content:

- `TopicListPage.tsx`: Owner publication disclosure and preview fail-closed UI content is retained; WS1 adds backend lifecycle enum mapping and shadow availability handling.
- `topic-api.ts`: Owner API/preview publication behavior is retained; WS1 adds lifecycle availability and lineage typing.

No Owner publication-disclosure line was overwritten by the candidate. This blocker can be resolved through a new collision-aware reconciliation/promotion commit after the remaining type gate is cleared. The old isolated commits must not be cherry-picked blindly.

## Blocker 2 — today-home / api-client `dataStatus` mismatch

### Result: blocking

The candidate commit `c46506e` changed:

`apps/web/app/lib/generated-api.d.ts`

from:

```ts
dataStatus: string;
```

to a lifecycle-oriented union on `HomeMarketOverview`.

The canonical working tree's untracked `packages/api-client/src/schema.d.ts` and `client.d.mts` still expose the same API field as `string`. `apps/web/app/lib/today-home.ts` receives the API-client `HomeResponse` and passes it to the local generated-schema mapper. Full candidate TypeScript validation fails at `today-home.ts:230` because the API-client `string` is not assignable to the candidate's narrowed local union.

Evidence:

- Canonical base `HEAD:apps/web/app/lib/generated-api.d.ts` still declares `HomeMarketOverview.dataStatus: string`.
- Candidate commit `c46506e` is the provenance of the narrowing.
- Candidate full TypeScript check reproduces exactly one error at `apps/web/app/lib/today-home.ts(230,39)`.
- The mismatch is therefore not an unchanged canonical baseline that can be waived for this promotion; it is a candidate-induced cross-package contract drift.

This task was limited to read-only source confirmation for this blocker. No `today-home.ts`, API client, OpenAPI, or generated schema file was changed.

## Gate disposition

The Owner dirty overlap is safe to preserve and reconcile. The candidate-induced generated-schema/API-client drift remains unresolved. Promotion is therefore fail-closed with one remaining blocker.

## Required next routing

Resolve the authority for `HomeMarketOverview.dataStatus` through a separate, minimal contract-reconciliation step (or remove the candidate-only narrowing if it is not required by the authoritative schema), then rerun the full TypeScript gate and a fresh collision-aware promotion rehearsal against the latest canonical HEAD. Do not cherry-pick the old WS1 commits directly.

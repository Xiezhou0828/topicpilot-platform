# `today-home.ts` / `api-client` `dataStatus` Read-only Review

## Source of mismatch

The canonical base declares `HomeMarketOverview.dataStatus` as `string` in `apps/web/app/lib/generated-api.d.ts`. The untracked canonical API-client package also declares the field as `string` in `packages/api-client/src/schema.d.ts`.

The WS1 candidate commit `c46506e` narrowed only the local generated declaration to:

```ts
"AVAILABLE" | "FORMAL_AVAILABLE" | "SHADOW_AVAILABLE" | "INSUFFICIENT_DATA" | "PENDING" | "PREVIEW" | "NOT_AVAILABLE" | "WAITING_FOR_FORMAL_LINEAGE"
```

`apps/web/app/lib/today-home.ts` calls `createTopicPilotClient().getHome()`, then passes that result into the local `HomeResponse` mapper. The API-client result remains wider (`string`), producing the full TypeScript error at `today-home.ts:230`.

## Scope decision

This is not an unchanged canonical baseline defect: the narrowing was introduced by the WS1 candidate. It is outside Lifecycle runtime semantics, but it is inside the promotion contract gate because it creates a cross-package type incompatibility. It cannot be waived as a pre-existing scope-out issue for this promotion.

## Action in L1.1

Read-only analysis only. No source, generated schema, OpenAPI, API-client, or `today-home.ts` file was modified. Promotion remains blocked until the authority is reconciled in a separately controlled change.

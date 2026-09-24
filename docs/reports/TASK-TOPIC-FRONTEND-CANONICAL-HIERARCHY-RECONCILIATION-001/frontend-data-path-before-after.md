# Frontend data path: before and after

## Before

The formal topic adapter called `/api/v2/topics?limit=200&offset=0` for the overview and `/api/v2/topics/{slug}` for detail. Browse grouping was derived from the flat row's `groupName`, and market lanes excluded rows by checking `topicType !== "MAJOR_GROUP"`. This made the flat state read model responsible for identity, hierarchy, and state at the same time. A Parent without a latest snapshot could therefore disappear or be treated as a market row.

## After

`fetchTopics()` requests both sources in parallel:

1. `/api/v2/topic-catalog?limit=500&offset=0` is the canonical identity/hierarchy universe.
2. `/api/v2/topics?limit=500&offset=0` is an optional Leaf-state join keyed by slug.

The Catalog response is mapped first. Every Catalog node remains visible when the Leaf-state request is unavailable. The state response can enrich Leaf rows but cannot invent identity, hierarchy, kind, or Parent state. The complete Catalog count is therefore preserved while market lanes explicitly select `kind === "LEAF"`.

`fetchTopic(slug)` follows the same boundary: Catalog detail is required for formal identity and hierarchy; the flat detail response is optional Leaf state and relation data. Parent detail renders its hierarchy and explicit `NOT_APPLICABLE` state without attempting to load or synthesize a daily snapshot.

## Changed frontend surfaces

- `apps/web/app/lib/topic-api.ts`: Catalog-first typed adapter, optional Leaf-state join, Parent/Leaf publication boundaries, and fail-closed availability.
- `apps/web/app/components/v2/TopicListPage.tsx`: canonical Parent grouping and Leaf-only market/list lanes.
- `apps/web/app/components/v2/TopicDetailPage.tsx`: explicit hierarchy plus separate Parent and Leaf detail branches.
- `apps/web/app/components/v2/FavoritesWorkspacePage.tsx`: Parent favorites remain non-market entities.
- `apps/web/app/components/v2/StockExplorerPage.tsx`: only Leaf topics enter stock filters.

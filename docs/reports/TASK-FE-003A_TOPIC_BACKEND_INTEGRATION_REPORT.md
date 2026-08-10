# TASK-FE-003A — Topic Backend Integration Report

**Status:** Implemented; preview deployment pending final publish verification
**Scope:** V2 Topic List, Topic Detail, Home → Topic route, and shared Stock Drawer data boundary. V1 routes and business pages remain untouched.

## Backend inventory

| Backend surface | Read model / repository | Frontend use | Status |
|---|---|---|---|
| `GET /api/v1/topics` | `Page[TopicSummary]`, `list_topics()` | `/topics` table and heatmap entry list | Connected |
| `GET /api/v1/topics/{slug}` | `TopicResponse`, `get_topic()` | Topic identity, strength, grade, state, count, constituents | Connected |
| `GET /api/v1/analytics/topic-rotation` | `TopicRotationResponse`, `topic_rotation()` | Not used as lifecycle; available for a later contract-specific phase | Existing API, deferred |
| `GET /api/v1/topic-intelligence/latest` | `TopicIntelligenceResponse` | Not used as page source because provider is fail-closed and may return 503 | Deferred |
| Topic snapshot / ingestion tables | `topics`, `topic_snapshots`, `stock_topic_relations` and repository SQL | Exposed through the two customer Topic endpoints above | Existing source |

## Coverage and gaps

Available from the formal Topic contract: slug/name, group, topic type, enabled state, data date, score, grade, strength state, coverage percentage, constituent count, and constituent code/name/relation/weight.

Still missing from the customer Topic read model: readable summary copy, hierarchy breadcrumb ancestry, lifecycle segments and trading-day durations, event/timeline history, curated news, related topics, user-scoped topic favorites, constituent price/change/freshness, and downstream opportunity links. These fields are represented as explicit `資料待更新` states. The browser does not infer business scores, lifecycle, heatmap sizing, or recommendations.

## Implemented flow

```text
Home 今日主線
      ↓ real slug link
Topic List /topics
      ↓ formal Topic API row
Topic Detail /topics/[slug]
      ↓ constituent row
Shared Stock Drawer / 560px
```

- Topic List supports search, lightweight state filtering, grade, strength, readable state, constituent count, local prototype favorite affordance, row navigation, and a restrained map below the list.
- Topic Detail reads the formal API, presents the frozen identity order, neutral role chips, unified constituent table, and shared drawer.
- Home preserves the approved latest visual edits: topic name and grade share one header row, and the mainline cards keep the raised height.
- `web_snapshot.json` is used only when no API origin is configured, as the existing clearly labelled public synthetic preview fallback. An API error is not silently converted into new mock business data.

## Verification

- `npm run lint` — passed.
- `npm run build` — passed; `/topics` and `/topics/:slug` are present in the production route manifest.
- Repository-wide TypeScript check remains blocked by pre-existing errors in `data-source.ts`, `snapshot-store.tsx`, `watchlist/page.tsx`, `vite.config.ts`, and Cloudflare worker globals; no new errors were reported in the TASK-FE-003A files.

## Explicit stop boundary

This report closes TASK-FE-003A. No Home, Stock, Favorites, Opportunity, lifecycle derivation, news integration, or backend schema/provider work is started automatically.

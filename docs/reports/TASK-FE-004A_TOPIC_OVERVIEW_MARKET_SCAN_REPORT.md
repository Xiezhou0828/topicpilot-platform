# TASK-FE-004A｜Topic Overview / Market Scan Implementation Report

**Status:** Implemented; deployed and verified
**Route:** `/topics`
**Scope:** V2 Topic Overview only. Topic Detail remains the research surface.

## 1. Product positioning

The Topic Overview is now defined as a Market Scan between Home and Topic Detail. Its first job is to let a user understand the market's topic distribution and strength classification in approximately ten seconds. Research content remains downstream in Topic Detail.

## 2. Implemented changes

- Replaced the previous ranking/list-first opening with a four-lane `S / A / B / D` Kanban board.
- Limited each Kanban card to topic name, today's topic score, today's direction, and `深入研究 →`.
- Added a small direction rail and arrow to every Kanban card. Direction styling uses brand taupe for strengthening, muted sage for weakening, and warm gray for flat; price red/green tokens are not reused for topic direction.
- Preserved `市場輪動` as a time-sorted event list with direction markers, grade transitions, and direct Topic Detail links.
- Added collapsible `依大族群瀏覽` navigation with child-topic links.
- Replaced the research-heavy previous list surface with a compact `全部題材` list containing name, group, grade, score, direction, constituent count, and favorite.
- Preserved search, direction filtering, grade filtering, favorite interaction, hover feedback, keyboard focus, and Topic Detail routing.
- Updated Preview labeling to `Preview（Mock Data）· 等待正式 Read Model` for missing read-model surfaces.
- Kept Topic Detail's lifecycle, research metrics, constituents, timeline, news, related topics, and detail map in the downstream route.

## 3. Formal API versus Preview Data

| Surface | Formal source | Preview fallback |
|---|---|---|
| Topic identity, name, group, grade, score, state, date, count | `GET /api/v1/topics` | Existing public snapshot plus schema-compatible topic identities |
| Topic Detail core and constituents | `GET /api/v1/topics/{slug}` | Existing preview identities when no API origin is configured |
| Market rotation summary | `GET /api/v1/analytics/topic-rotation` when available | Time-ordered mock rotation events with explicit Preview badge when event fields are missing |
| Direction arrow and rail | Formal strength/change fields when present | Preview overview metadata only when the formal field is absent |
| Group browse | Formal `groupName` | Preview group metadata only when the formal group is absent |

Preview metadata is additive. A non-null formal grade, score, group, or state is never replaced by frontend mock data.

## 4. Backend read models still needed

- A canonical topic direction/read model for today's `↑ / ↓ / →` state.
- A canonical topic rotation event model with event timestamp, event type, previous grade, and next grade.
- Topic hierarchy/group ancestry beyond the current `groupName` field.
- User-scoped favorite persistence for topic rows.

## 5. Direct-switch path

When the backend supplies direction, rotation events, and hierarchy, the Preview metadata adapters can be removed without changing the Kanban, rotation, group-browse, or compact-list UI structure. Existing formal Topic API mapping remains the authoritative core path.

## 6. Boundary confirmation

- No backend schema or scoring logic was modified.
- Home, Stock, Favorites, Opportunity, and V1 business pages were not redesigned.
- Topic Detail remains the research page; Overview does not contain lifecycle, events, news, representative stocks, related-topic research, or constituent details.

## 7. Verification

- Targeted ESLint for changed V2 files: passed.
- `npm run build`: passed; `/topics` and `/topics/:slug` are present in the route manifest.
- Full-project ESLint scan: exceeded the execution window; no error output was produced before timeout, so targeted lint is the authoritative scoped lint result.
- Public deployment verification: passed on `/topics` and `/topics/ai-server` after the final deployment.

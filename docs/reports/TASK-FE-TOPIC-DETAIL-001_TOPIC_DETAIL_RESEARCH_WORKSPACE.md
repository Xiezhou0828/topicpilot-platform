# TASK-FE-TOPIC-DETAIL-001 — Topic Detail Research Workspace

## Executive Result

Implemented the Topic Detail Research Workspace as a frontend-only, formal-state-aware information architecture and presentation slice. The page now leads with research summary, then the three existing Topic status dimensions, formal constituents/relations, lifecycle disclosure, description, hierarchy/related topics, and a fail-closed historical/rotation placeholder.

The implementation preserves the current field-level publication authority from `TASK-TOPIC-PUB-001` and does not fabricate score, grade, lifecycle, leadership, breadth, concentration, or historical values. Current backend/data gaps remain visible as deferred, unavailable, Preview, or contract-gap states.

## Canonical State

- `TASK_ID`: `TASK-FE-TOPIC-DETAIL-001`
- `TASK_NAME`: `Topic Detail Research Workspace`
- Canonical repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
- Canonical branch at audit: `codex/task-ops-023a-p3c-runtime-sha-audit-20260813`
- `CANONICAL_PRE_SHA_AT_RECONCILIATION_START`: `88a4dcc897e986b0c5667f97cad27bb0f0131610`
- `ORIGIN_MAIN`: `26f635b95d8d88fd7ed7e43949583347f3ab5feb`
- `WORKTREE_USED`: isolated worktree because the previous Topic publication owner had an exact dirty-file collision on `TopicDetailPage.tsx`.
- Temporary isolated baseline commit `e5fc35d` preserved the prior dirty Topic publication baseline only; it is not a canonical reconciliation target.
- No production mutation, production database change, push, merge, deployment, scheduler change, or next task change was authorized or performed.

## Current Topic Detail Audit

Before implementation, the current route, component tree, adapter, tests, and publication report were inspected. The prior Detail surface contained formal identity and relationship data, deferred score/grade behavior, shadow lifecycle semantics, Preview/fallback sections, and synthetic research sections that could visually imply unsupported history or analysis.

Current authority was confirmed against:

- `TASK-TOPIC-PUB-001_FIELD_LEVEL_PUBLICATION_DISCLOSURE_REPORT_2026-08-14.md`
- `TOPIC_FORMAL_DATA_AUDIT_REPORT_2026-08-14.md`
- `apps/web/app/lib/topic-api.ts`
- `apps/web/app/components/v2/TopicDetailPage.tsx`
- existing Topic Detail and Topic UI regression tests

The current adapter enum is used exactly: `FORMAL`, `FORMAL_NOT_WIRED`, `TEMPORARY`, `PREVIEW`, `DEFERRED`, `UNAVAILABLE`, and `CONTRACT_GAP`.

## CURRENT_TOPIC_DETAIL_FIELD_MATRIX

| UI section / field | Current source | Publication state / formal availability | Existing component | Desired treatment |
|---|---|---|---|---|
| Header identity: slug, name, topic type, enabled, data date | `TopicSummary` from the formal Topic adapter | Formal identity when API catalog/detail is formal; Preview is explicit | `TopicDetailPage` header and breadcrumb | Render directly with source and publication disclosure; no source-wide promotion of other fields |
| Parent / group context | `TopicSummary.groupName` and formal topic identity | Formal when present; otherwise unavailable | Header breadcrumb | Render only when provided by the adapter; no browser hierarchy inference |
| Score / grade | `TopicSummary.score`, `TopicSummary.grade` | Deferred/null in current authority; Preview may have explicit temporary values | Existing grade/score area | Preserve null/deferred state and disclose it; never calculate or promote Preview |
| Today strength state | `strengthState`, `readableState`, `direction`, `dataDate`, `coveragePct` | Direct field-level state; mixed formal/deferred/unavailable possible | New `TodayStatusSection` | Render direct backend values; missing fields use state-aware empty values |
| Three core structure dimensions | `TopicStatus` keys `族群表現`, `領漲核心`, `動能擴散`; each item has nullable `state` and evidence | Formal only when the individual item is present and formal; missing values remain deferred/unavailable | New `TopicStatusSection` | Keep the current three dimensions; show missing values without inventing metrics or formulas |
| Constituents / related stocks | Formal `stocks` relation projection in backend order | Formal relations when provided; source/error state remains explicit | New `ConstituentsSection` using existing stock drawer behavior | Render relation order only; distinguish relation role from leadership; no arbitrary top-N or browser ranking |
| Leader / core label | Existing relation role and `領漲核心` status field only | No formal Leader Set/ranking authority in current contract | `ConstituentsSection` and status card | Explain the boundary; never call backend order “leaders” and never compute a leader score |
| Lifecycle | `TopicLifecycle.dataStatus`, `currentStage`, `provenance` | Current `SHADOW_AVAILABLE`/Preview/unavailable/deferred; not formal historical publication | New `FormalLifecycle` | Fail closed with disclosure and empty/deferred state; no stage marker unless a future formal lifecycle status is supplied |
| Description / narrative | Current Topic adapter summary field where present | Formal only when current authority marks it formal; Preview is explicitly Preview | New `DescriptionSection` | Render formal narrative only; otherwise preserve unavailable/deferred state |
| Related topics / hierarchy | Formal group/relations from adapter | Formal only when supplied; no name-similarity contract | New `RelatedTopicsSection` | Render formal hierarchy/relations; otherwise empty/deferred, never inferred in browser |
| Historical / rotation / heatmap | No publication-ready formal series in current contract | Deferred, unavailable, or contract gap; Preview is not formal history | New `HistoricalSection` | Render a section shell/empty state only; no synthetic chart or browser-derived time series |

## Research Workspace IA

The reading order is now:

1. Header and identity context.
2. `今日狀態` / research summary.
3. `核心結構三格` using the existing Topic status dimensions.
4. `正式成分與關聯股票`.
5. Lifecycle availability and provenance.
6. Formal description/narrative availability.
7. Formal hierarchy and related-topic availability.
8. Historical/rotation placeholder with publication disclosure.

The implementation reuses the existing V2 foundation, cards, tables, empty states, badges, and stock drawer interaction. It adds workspace-specific layout/state CSS without changing the site-wide visual language or the Topic List accordion grid behavior.

## Formal-State Rendering Rules

- `FORMAL`: render the field normally from the adapter.
- `FORMAL_NOT_WIRED`: retain an explicit not-wired disclosure and do not imply formal availability.
- `TEMPORARY`: use the existing temporary semantics; do not promote to formal.
- `PREVIEW`: display a visible Preview disclosure and keep Preview content separate from formal content.
- `DEFERRED`: show an explicit deferred state.
- `UNAVAILABLE`: show an explicit unavailable state.
- `CONTRACT_GAP`: show a conservative contract-gap presentation, while retaining developer/test semantics in data attributes and publication metadata.
- API errors remain unavailable and never silently fall back to Preview.

## Three-Core-Metric Decision/Availability

The Detail surface keeps the existing three status dimensions, `族群表現`, `領漲核心`, and `動能擴散`, rather than adding a fourth overlapping card or inventing a new scoring formula. Each card renders the adapter-provided nullable state and evidence only. No browser calculation of score, grade, participation, breadth, concentration, heating, cooling, or S/A/B/D is introduced.

Current availability is mixed and field-level: identity and relations can be formal, while status members, score/grade, and related analytical fields can be deferred or unavailable. Missing values render a state-aware placeholder and never fabricated numeric values.

## Constituent/Leadership Boundary

Constituents are rendered in the existing backend relation order. The UI labels the relation role and clearly states that the current contract does not provide a formal Leader Set or leader ranking. A stock is not called a leader merely because it appears early in the relation list, and no leader score, concentration, or ranking is calculated in the browser.

## Lifecycle Boundary

The current lifecycle result is shadow/deferred rather than formal historical publication. `SHADOW_AVAILABLE`, Preview, unavailable, deferred, and contract-gap states now fail closed with clear disclosure. A lifecycle stage/current marker is rendered only when both the lifecycle data status and field-level publication authority are formal. The prior synthetic stage/timeline presentation was removed.

## Hierarchy/Related Topics

Formal group context is retained in the identity header. Related-topic content is rendered only from formal adapter relations. The browser does not derive related topics from name similarity, local sorting, or other heuristic matching.

## Preview/API/Error Boundary

Explicit Preview resources remain visible as Preview. API error/unavailable resources remain unavailable. No error path silently substitutes the Preview snapshot, and no source-level `api` label is treated as proof that every field in the payload is formal.

## Backend Contract Gaps

The following remain intentionally outside this frontend-only task:

- formal publication of Topic score/grade and the resulting S/A/B/D state;
- formal lifecycle history, stage, provenance, and historical series;
- formal Leader Set / leadership ranking and concentration authority;
- formal participation/breadth/heating/cooling and rotation history;
- formal events, news, heatmap, and research narrative contracts where absent;
- a unified formal contract for the three structure dimensions if their future semantics differ from the current status keys;
- reconciliation of Topic fields with the separate Today/Home `public.*` versus Topic `topicpilot.*` publication contracts;
- broader stock EOD semantic reconciliation, which belongs to the existing stock workstream.

No backend endpoint, generated OpenAPI contract, database schema, or backend runtime was changed.

## Implementation Files

- `apps/web/app/components/v2/TopicDetailPage.tsx`
- `apps/web/app/globals.css`
- `apps/web/tests/topic-detail-research-workspace.test.mjs`
- `docs/reports/TASK-FE-TOPIC-DETAIL-001_TOPIC_DETAIL_RESEARCH_WORKSPACE.md`

## Tests/Validation

- Focused Topic tests: PASS, including formal identity, mixed field states, no score/grade derivation, lifecycle fail-closed behavior, constituent/leadership boundary, Preview/API error boundary, and responsive structure checks.
- Full frontend tests: PASS, `113/113` (canonical run, including the existing publication disclosure tests).
- TypeScript: PASS, `npx tsc --noEmit`.
- Changed-file ESLint: PASS for `TopicDetailPage.tsx`.
- Production build: PASS; build output enumerated `/topics` and `/topics/:slug`.
- Route smoke: not run because the environment does not permit the required background runtime; build route evidence is not treated as runtime smoke.
- Diff check: required for the exact task write set at closure.
- Secret scan: required for the exact task write set at closure.
- Topic List accordion/grid regression: PASS in the full frontend suite; existing `align-items:start` protection remains.
- Protected runtime gates: `G1/G2/G3/POST_CLOSE_CANARY = PRESERVED PASS`; no protected runtime was changed.

## Documentation Reconciliation

The report is the formal task artifact. `DAILY_PROGRESS.md` receives an append-only milestone entry only during canonical closure after confirming current owner-doc state. `PROJECT_CONTEXT.md`, `docs/ROADMAP.md`, `docs/WORK_ORDERS.md`, the product roadmap, and the documentation index are not overwritten; any update is limited to an exact semantic change and is deferred when it collides with a current owner-doc write set.

## Remaining Topic Gaps

The UI is ready as a research workspace shell with honest field-level states, but the Topic backend still needs formal score/grade publication, lifecycle history, leadership authority, and historical/rotation contracts before those sections can become analytical visualizations.

## Parallel Collision Audit

At task start, the canonical repository contained dirty Topic publication files owned by the preceding Topic disclosure workstream and separate active work on adjustment/corporate actions, PIT universe, research harness architecture, and stock EOD wiring. Because `TopicDetailPage.tsx` was an exact dirty-file collision, implementation used the isolated worktree. The temporary baseline contained only the previous Topic publication changes so this task’s final application diff could remain exact. No unrelated owner changes were staged, reset, stashed, or overwritten.

## Final Status

Target final status: `TOPIC_DETAIL_RESEARCH_WORKSPACE_FRONTEND_COMPLETE_WITH_FORMAL_DATA_GAPS_PRESERVED`.

Fixed flags: `PRODUCTION_MUTATION=NO`, `PRODUCTION_DB=NO`, `PUSH_REMOTE=NO`, `MERGE_MAIN=NO`, `DEPLOY=NO`, `SCHEDULER=NO`, `NEXT_TASK_CHANGED=NO`.

No next Topic task was opened automatically.

## Closure Reconciliation Record

- `CANONICAL_PRE_SHA`: `88a4dcc897e986b0c5667f97cad27bb0f0131610`
- `CANONICAL_POST_SHA`: `d7b28e01b3a26ecfc914a74d9127fa09e8f53fff`
- `COMMIT_SHA`: `d7b28e01b3a26ecfc914a74d9127fa09e8f53fff`
- `CANONICAL_RECONCILIATION`: completed on the latest canonical branch state.
- `DAILY_PROGRESS_UPDATED`: yes, append-only milestone recorded in `docs/DAILY_PROGRESS.md`.
- `PROJECT_CONTEXT_UPDATED`: deferred; current owner-doc dirty write set preserved.
- `ROADMAP_UPDATED`: deferred; current owner-doc dirty write set preserved.
- `PRODUCT_ROADMAP_UPDATED`: no semantic update required.
- `WORK_ORDERS_UPDATED`: deferred; current owner-doc dirty write set preserved.
- `DOCUMENTATION_INDEX_UPDATED`: no semantic update required.
- The canonical commit carries the final `TopicDetailPage.tsx` content and therefore carries forward the already-dirty Topic publication baseline in that same exact file; no unrelated files were staged, reset, stashed, or overwritten.

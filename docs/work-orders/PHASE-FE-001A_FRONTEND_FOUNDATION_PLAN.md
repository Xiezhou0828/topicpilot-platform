# PHASE-FE-001A — Frontend Foundation Audit + Implementation Plan

**Status:** A-stage complete; awaiting PM approval for B
**Verdict:** `READY_FOR_B`
**Scope:** audit and foundation planning only. No V2 page-business implementation is authorized by this artifact.

## Executive summary

The repository and canonical V2 design specification are present and readable. The frontend is a Next 16 / React 19 App Router application built and deployed through vinext, Vite, and Cloudflare tooling. Existing customer-facing pages are operational V1 scaffolding and remain in scope for preservation, but their current visual language is not authoritative for V2.

V2 foundation can proceed without changing V1 APIs, data workflows, or product behavior. The recommended B scope is a shared shell and tokenized primitive layer, plus route placeholders only. Home, Topic, Stock, Favorites, and Opportunity business sections must remain out of B. AI研究室 is a navigation/route entry only and must not block launch.

## Current frontend repository audit

### Verified paths

- Repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`
- Canonical spec: `docs/architecture/TOPICPILOT_V2_FRONTEND_DESIGN_SPEC.md`
- Frontend root: `apps/web`
- Work-order output: this file

### Stack and runtime

- Next `16.2.12`, React/React DOM `19.2.8`, TypeScript `5.9.3`.
- App Router under `apps/web/app`; route files are `page.tsx`.
- vinext `0.0.50` with Vite `8.2.0`, Cloudflare Vite plugin, Wrangler, and a worker entry at `apps/web/worker/index.ts`.
- Styling is primarily one large `apps/web/app/globals.css` with Tailwind 4 imported, but the existing UI uses extensive hand-authored CSS variables/classes rather than a coherent V2 token layer.
- `lucide-react` is available for icons.
- Validation scripts: ESLint, TypeScript through the build, `npm test` (build plus Node tests), demo snapshot check, and production build.

### Existing application structure

- Root provider: `app/layout.tsx` wraps the app in `SnapshotProvider`.
- Shared customer navigation: `app/components/AppNav.tsx`.
- Existing shared data-state surface: `LiveDataBanner.tsx`; fallback/empty presentation: `EmptyState.tsx`.
- Snapshot/data layer: `app/lib/snapshot-store.tsx`, `data-source.ts`, `live-data.mjs`, `snapshot-adapter.ts`, `generated-api.d.ts`, and related view-model modules.
- Existing customer routes include `/`, `/market`, `/topics`, `/stocks/[code]`, `/favorites`, `/watchlist`, `/guide`, `/studio`, and `/topics/intelligence`. Admin routes are separate under `/admin`.
- API contracts already expose snapshot, status, topics, topic detail, stocks, stock detail, price history, favorites-related data, strategy/candidate, rotation, and intelligence endpoints. Search is not established as a dedicated V2 contract.

## Reuse vs retire matrix

| Area | Reuse in B | Retire/contain | Decision |
|---|---|---|---|
| App Router, root layout, provider boundary | Yes | — | Technical scaffolding only |
| Snapshot provider, refresh/evaluation, generated API types | Yes, behind adapter boundaries | Do not add browser business inference | Reuse |
| Existing AppNav route knowledge | Partially | Do not copy its visual CSS wholesale | Extract route intent only |
| LiveDataBanner and EmptyState behavior | Concepts and state semantics | Existing presentation may be restyled later | Reuse contract, recompose UI |
| `globals.css` variables/classes | No as V2 visual authority | Dark palette, teal/green semantics, large legacy class surface | Replace incrementally behind V2 tokens |
| Admin pages and admin primitives | No | Keep operational and isolated | V1/admin boundary |
| Stock/topic business components | No for B | Must not determine foundation architecture | Defer to later phases |
| `lucide-react` | Yes | Avoid bespoke icon glyphs where an icon exists | Reuse |
| Studio assets/routes | No for V2 customer shell | Keep `/studio` operational as legacy/Phase 2 surface | Contain |

## Legacy visual findings

The current stylesheet contains a dark navy/black background, teal brand accents, saturated green/red/amber/blue variables, translucent backgrounds, `backdrop-filter: blur`, gradients, and a large shadow (`0 20px 48px ...`). It also contains dense card grids, card walls, and dashboard-like panels. These are V1/legacy implementation details and must not shape V2.

V2 must explicitly avoid neon accents, AI gradients, glow effects, glassmorphism, heavy shadows, saturated rainbow heatmaps, and recommendation-dashboard card walls. V1 remains operational; retirement means visual containment in V2, not deleting or breaking V1.

## Proposed component tree for PHASE-FE-001B

```text
app/
  (v2)/
    layout.tsx
    page.tsx                         # 今日市場 route shell only in B
    topics/page.tsx                  # placeholder shell
    stocks/page.tsx                  # placeholder shell
    favorites/page.tsx               # placeholder shell
    opportunities/page.tsx           # placeholder shell
    research/page.tsx                # AI研究室 entry/placeholder
  components/v2/
    shell/AppShell.tsx
    shell/PrimaryNav.tsx
    shell/UtilityBar.tsx
    shell/PageContainer.tsx
    shell/PageHeader.tsx
    primitives/Surface.tsx
    primitives/Card.tsx
    primitives/Table.tsx
    primitives/Button.tsx
    primitives/IconButton.tsx
    primitives/Tabs.tsx
    primitives/SegmentedControl.tsx
    primitives/GradeChip.tsx
    primitives/RoleChip.tsx
    primitives/FavoriteStar.tsx
    primitives/Freshness.tsx
    primitives/Tooltip.tsx
    primitives/SearchInput.tsx
    primitives/Skeleton.tsx
    primitives/EmptyState.tsx
    primitives/DataState.tsx
    search/GlobalSearchShell.tsx
  styles/v2-tokens.css
```

The exact folder names may be adjusted to the repository's existing route-group conventions during B, but the ownership boundaries must remain.

## Proposed token system

Use semantic CSS custom properties, with raw values centralized in `styles/v2-tokens.css` or the chosen equivalent. Do not scatter literals.

```text
--tp-color-brand-primary: #8A7462
--tp-color-page: warm off-white
--tp-color-surface / --tp-color-surface-muted: white/light warm neutrals
--tp-color-text-primary / --tp-color-text-secondary / --tp-color-border
--tp-color-price-up / --tp-color-price-down
--tp-color-warning / --tp-color-error
--tp-color-grade-s / --tp-color-grade-a / --tp-color-grade-b / --tp-color-grade-d
--tp-radius-sm / --tp-radius-md: 10–12px baseline
--tp-space-1 ... --tp-space-8: 8px rhythm
--tp-shadow-none / --tp-shadow-subtle
--tp-font-body / --tp-font-display / --tp-font-mono-data
--tp-focus-ring
```

Price red/green tokens are semantic and may be used only when rendering actual price movement. Topic state, grade, lifecycle, and availability use restrained warm-neutral hierarchy. Amber is warning only; error red is for actual system errors.

## Proposed routing shell

V2 customer routes to create as empty foundation shells in B:

| Product page | Proposed route | B behavior |
|---|---|---|
| 今日市場 | `/` | Shell/header/state placeholder only |
| 題材 | `/topics` | Shell/header/state placeholder only |
| 股票 | `/stocks` | Shell/header/state placeholder only; preserve `/stocks/[code]` V1 route |
| 收藏 | `/favorites` | Shell/header/state placeholder only; preserve existing V1 behavior until migration is approved |
| 機會 | `/opportunities` | New shell only |
| AI研究室 | `/research` | Entry/Coming Later only; does not block launch |

Route-group isolation is preferred so V2 shell work cannot accidentally change admin or current V1 routes. If the repository cannot support parallel route ownership cleanly, B must use an explicit compatibility boundary and PM approval before replacing an existing customer page.

## Shared primitive inventory

Required B inventory: AppShell, PrimaryNav, UtilityBar, PageContainer, PageHeader, Surface/Card, dense-but-readable Table, Button, IconButton, Tabs, SegmentedControl, GradeChip, RoleChip, FavoriteStar, Freshness/UpdateState, Tooltip, SearchInput, GlobalSearchShell, Skeleton, EmptyState, and Error/Unavailable/Stale presentation.

All primitives require keyboard focus styling, semantic HTML, accessible names, and token-only colors. No primitive may calculate topic scores, grade, lifecycle, heatmap size, recommendation status, or other business meaning.

## Global data-state UX contract

| State | Presentation |
|---|---|
| Initial loading | Local skeletons matching the expected layout; no full-page spinner as the default |
| Incremental refresh | Preserve current content, show compact updating/freshness affordance, update as-of after success |
| AVAILABLE | Normal surface with visible as-of where currentness may be misunderstood |
| STALE | Preserve last valid data, mark stale, show last as-of, offer retry/refresh |
| UNAVAILABLE | Explain that data is not currently available; keep shell usable |
| PROVIDER_ERROR | Distinguish provider failure from empty data; show retry and non-destructive explanation |
| 盤中更新 | Plain-language intraday update state and timestamp |
| 盤後更新 | Plain-language post-close state and timestamp |
| 資料待更新 | Pending state; do not imply a zero or negative business result |

The existing snapshot refresh/evaluation machinery is a candidate source for these states, but V2 presentation must be a new semantic wrapper. All surfaces that show current prices or live rankings must make freshness visible.

## Global search shell plan

The shell owns input, open/close behavior, keyboard navigation, loading/error/empty states, and result grouping. Results are separated into `題材` and `股票`, with route links returned by the backend contract.

The browser must not infer matching, rank results, derive topic membership, or synthesize business labels. A dedicated search API/read contract is not verified in the current generated contract; therefore B may implement the shell with an explicit pending/dependency state or a typed adapter boundary, but must not invent permanent client-side search data.

## PHASE-FE-001B implementation whitelist

1. Add the isolated V2 shell and token layer.
2. Add primary navigation and utility placeholders for the six frozen IA entries.
3. Add route shells with page title/description placeholders and shared state slots only.
4. Add the shared primitives listed above, with stories/tests or focused route smoke coverage where the repository's test style permits.
5. Add semantic data-state and freshness wrappers without changing V1 data fetching or API contracts.
6. Add the global search shell contract boundary, leaving backend search integration explicitly pending.
7. Verify V1 routes remain unchanged and operational.

## Explicit non-goals

- No Home/Topic/Stock/Favorites/Opportunity business sections, rankings, cards, tables with real business content, recommendation logic, lifecycle derivation, heatmap sizing, or technical score UI in B.
- No API, schema, provider, scoring, or data-workflow changes.
- No V1 visual migration, compatibility rewrite, or deletion of existing routes.
- No parallel mobile redesign; implementation is desktop-first with responsive degradation boundaries only.
- No AI研究室 implementation beyond route/nav entry and Coming Later state.

## API/data dependencies

These do not block foundation implementation: existing snapshot provider, refresh status, generated TypeScript API contracts, existing route navigation, and existing favorite action interfaces can be kept behind adapters.

These remain dependencies for later page phases: canonical Home aggregates and event labels; topic ranking/state/heatmap/lifecycle payloads; stock full-database and drawer fields; opportunity read model; curated news; institutional/technical runtime fields; and a dedicated global-search contract. B must not fill these gaps with browser inference or synthetic permanent business logic.

## Risks and blockers

- The current spec file displays mojibake in the PowerShell text preview for some Chinese strings, although headings and structure are readable. The canonical file remains the authority; B should preserve UTF-8 and verify rendered labels in the app.
- Existing customer routes are already occupied by V1 pages. Route-group isolation or an explicit migration boundary needs to be chosen before replacing any of them. This is a B implementation decision, not a blocker for planning.
- The current global CSS is large and V1-specific. Incremental scoping is safer than rewriting it in place.
- Search has no verified dedicated backend contract. The shell can proceed, integration cannot.

No PM decision is required to start a shell-only B, provided B remains within the whitelist and preserves V1. PM approval is required before replacing existing customer page implementations or changing route ownership.

## PHASE-FE-001C acceptance checklist

- [ ] `npm run lint` passes.
- [ ] Typecheck/build validation passes through the production build.
- [ ] Existing web tests pass; new foundation tests cover shell/primitive behavior where appropriate.
- [ ] Production build succeeds with the configured vinext/Cloudflare pipeline.
- [ ] Desktop routing smoke passes for `/`, `/topics`, `/stocks`, `/favorites`, `/opportunities`, and `/research`.
- [ ] V1/admin routes remain reachable and their APIs/data workflows are unchanged.
- [ ] Desktop rendering shows the frozen IA and shared shell consistently.
- [ ] Keyboard navigation, visible focus, button names, and basic landmark semantics work.
- [ ] Basic contrast/accessibility checks pass for text, borders, states, and focus.
- [ ] No neon, AI gradient, glow, glassmorphism, or heavy-shadow V2 styling is present.
- [ ] Brand/token consistency is verified; no scattered V2 literals.
- [ ] Taiwan red/green appears only for actual price movement.
- [ ] No accidental page-business logic or browser-side business inference is present.
- [ ] Incremental refresh preserves content and exposes freshness/as-of.
- [ ] AI研究室 is only an entry/Coming Later route and does not block launch.

## Final verdict

`READY_FOR_B`

The foundation plan is sufficiently concrete to begin PHASE-FE-001B after PM approval. Stop here; do not start B automatically.

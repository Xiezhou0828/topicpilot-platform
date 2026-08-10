# TASK-STOCK-UI-02｜Stock Explorer UI Implementation Report

**Status:** Implemented; production build verified
**Route:** `/stocks`
**Scope:** Stock Explorer route, local Stock Explorer component, stock-page-only styles. No backend, API, schema, Header, Home, Topic, Favorites, or Opportunity changes.

## 1. Product alignment

The route now uses the existing V2 App Shell and Modern Financial Workspace tokens: warm light surface, restrained borders, brown brand accent, calm secondary controls, and Taiwan red-up / green-down price semantics.

## 2. Toolbar

The first row is one aligned toolbar containing `Market`, `Sort`, `Advanced filters`, and the lightweight outline `Re-sort` utility. Advanced filters expand directly below the toolbar as a horizontal panel. LIVE / EOD segmentation remains a compact secondary row.

## 3. Stock tiles

Tiles use a fixed `190px × 124px` geometry with compact name, code/topic, quote, change, and LIVE/EOD state. EOD keeps the same geometry and displays a restrained post-close note. Prices and change values remain snapshot-driven; no browser business scoring or backend contract changes were added.

## 4. Stock Drawer

Selecting a tile inserts a push-style right panel into the workspace layout. The grid remains visible and another tile can be selected while the panel is open. The panel includes identity, price/change, freshness, topic and role context, and `View opportunity →`. Header close and Escape behavior restore the full-width grid.

## 5. Data boundary

The page consumes the existing `useSnapshot` / `StockView` read model. Topic roles are shown only when an existing relation role is present; missing fields remain explicit as pending data. No new API contract or mock backend data was introduced.

## 6. Verification

- `npm run build` passed for the web app.
- `/stocks` appears in the production route manifest.
- Existing Topic, Home, Header, Backend, API, and Read Model files were not modified.

## 7. Remaining dependency

The formal read model currently determines whether a stock is LIVE/EOD through its existing freshness field. Exact production role labels and richer advanced-filter options remain dependent on fields already exposed by the formal read model; this UI does not invent them.

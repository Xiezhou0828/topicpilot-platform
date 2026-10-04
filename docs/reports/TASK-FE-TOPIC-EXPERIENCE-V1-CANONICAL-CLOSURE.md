# TASK-FE-TOPIC-EXPERIENCE-V1 — Canonical Closure

**Status:** `IMPLEMENTED / VALIDATED / PRODUCTION UNCHANGED`

**Scope:** Topic Overview、Topic Detail、shared formal presentation boundary、cross-surface regression closure。

**Canonical frontend:** `apps/web`

## Delivered

- Added `app/lib/topic-presentation.ts` as the shared presentation boundary for
  absolute/relative Grade labels and Overview/Detail Lifecycle labels.
- Added `app/lib/topic-knowledge.ts` as a structured, curated Topic Knowledge
  layer. It does not own membership, relation roles, Strength, Grade,
  Lifecycle, ranking, or recommendations.
- Extended `topic-api.ts` with formal Strength availability and bounded formal
  Topic snapshot history. Missing relative history remains unavailable; it is
  never reconstructed from Absolute history.
- Rebuilt Topic Overview around:
  - 今日題材地圖;
  - 絕對強度／相對市場 switch;
  - S/A/B/D semantic lanes;
  - bounded cards with full-list Drawer;
  - five-stage Lifecycle board;
  - Parent navigation, global search, Grade/Lifecycle filters, sorting, and
    local watch/favorite state;
  - explicit formal/Preview/unavailable copy and a working guide Drawer.
- Rebuilt Topic Detail as one continuous research page:
  - Hero and 今日判讀;
  - structured 題材介紹 with safe fallback;
  - 強度與結構;
  - formal Lifecycle with BASE rendered as 尚未形成 and repeated history
    segments preserved;
  - formal history observation points with explicit gaps and separate
    categorical Lifecycle rail;
  - exact member columns `股號 / 股名 / 角色 / 今日漲跌幅`;
  - member overflow Drawer and direct Stock Detail navigation;
  - folded diagnostics for publication, quality, lineage, and Owner-seeded
    observation data.
- Added responsive warm-neutral presentation styles and updated regression
  tests to assert the V1 contract rather than the retired accordion/dashboard
  structure.

## Validation

The following commands pass from `apps/web`:

```text
npm run build
npm run lint
npm test
```

The frontend test suite covers the existing V2 surfaces plus the new Topic
Experience V1 contract. Business authority remains backend-owned; the browser
does not calculate score thresholds, Grade, Lifecycle, member roles, ranking,
or relative-strength proxies.

## Production boundary

This work order does not authorize a new Production deploy, migration,
scheduler mutation, Worker rollout, or GitHub push. The previously verified
Production readback remains a separate release record. Production deployment
must be run only by the release work order that explicitly authorizes this
Topic Experience artifact and verifies API, Web, Worker, and public readback
against the intended commit.

## Follow-up dependency

The current formal snapshot API exposes Absolute history only. The Detail UI
therefore shows Relative history as unavailable until a formal Relative
history field is published by the backend contract. No frontend workaround is
permitted.

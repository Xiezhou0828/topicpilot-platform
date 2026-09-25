# TopicPilot current project context

**Status:** `CURRENT STARTUP / HANDOFF NAVIGATION`
**Last reviewed:** `2026-09-22`
**Evidence baseline before this documentation commit:** `main` at `f88ff51`

This file is the short cold-start handoff. It points to authority and records
only the facts needed to resume work; it does not duplicate detailed reports.

## Read first

1. [Collaboration and safety rules](AGENTS.md)
2. [Execution roadmap](docs/ROADMAP.md)
3. [Product roadmap](docs/product/TOPICPILOT_PRODUCT_ROADMAP.md)
4. [Product decisions](docs/product/TOPICPILOT_PRODUCT_DECISIONS.md)
5. [Architecture authority map](docs/architecture/README.md)
6. [Documentation governance](docs/DOCUMENTATION_GOVERNANCE.md)
7. [Owner-approved development process](docs/policies/development-process.md)

## Canonical boundary

- Canonical repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
- Canonical completion requires accepted content committed to `main`. A task
  branch, worktree, report, or passing test is evidence until integrated.
- Release Candidate, Production release, and post-deploy readback are later,
  separately proven states.
- V2 is the active product generation. V1 remains a protected legacy bridge
  until replacement, parity, and explicit cutover approval.

## Current operating map

### A — Formal Data / Topic Engine

- **A1 Current Formal Pipeline:** current formal Topic scope can materialize at
  107/107 in committed M1 integration evidence. The complete post-2026-09-12
  lineage is not yet integrated into current `main`, so A1 is
  `CANONICAL_RECONCILIATION_REQUIRED`, not product-complete.
- **A2 Historical Data Foundation:** Production canonical OHLCV begins on
  2026-08-13 and contains gaps. The earlier two-year bootstrap is
  non-Production evidence.
- **A3 Formal Historical Continuity:** historical Topic snapshots and derived
  Score/Grade/Lifecycle/Opportunity chains are incomplete. Rotation has 14 of
  15 required formal sessions as of 2026-09-21.

### B — User-facing Product

- **B1 Today:** the product role is market orientation. Committed lineages
  cover index/turnover, market and stock institutional flow,
  breadth/distribution, and deterministic signals, but they are not all in
  current `main`. Missing dependencies must be `PARTIAL`/`UNAVAILABLE`.
- **B2 Opportunity:** the product role is downstream qualification and
  explanation. Full-universe consumption and FUND-C enrichment have committed
  evidence; formal provider/publication remains gated and fail-closed.
- **B3 Topic:** identity, membership, Structural Role, Score, Daily Grade,
  Lifecycle, ranking and explanation retain separate provenance. `107` is a
  dynamic observed count, not a constant.
- **B4 Stock:** search/filter, EOD, and historical-price foundations are
  canonical. Technical/institutional evidence must complete backend contract
  integration before user-facing completion is claimed.

### C — Decision Intelligence

- **C1 Statistical Research:** evidence-only, PIT-safe, no-look-ahead studies.
- **C2 Feature Validation:** coverage, stability, robustness, concentration,
  and failure-mode review; validation is not policy.
- **C3 Decision Layer:** owner review → formal contract → `main` integration →
  release → Production readback.

## Frozen product principles

- Daily Grade and Lifecycle are independent.
- Structural Role and selected Leader/importance are separate owner-curated,
  effective-dated formal inputs.
- Research history is not formal history.
- Frontend code never recalculates formal business logic.
- Today explains market state; Opportunity evaluates downstream candidates.
- Completed implementation counts as product-complete only after canonical
  `main` integration and validation; Production visibility remains separate.
- Missing values stay unavailable/`null`, never implicit zero.

## Current priority and handoff

1. **P0:** reconcile accepted A1/shared daily-pipeline commits after `f88ff51`
   into canonical `main`, with exact source-to-main provenance and validation.
2. **P1:** recover authoritative Production history and formal historical
   continuity without using research rows as backfill.
3. **P2:** complete Today and Topic formal consumption, then Stock evidence
   publication.
4. **P3:** activate formal Opportunity only after the complete upstream and
   provider chain is canonical; continue research without policy promotion.

The 2026-08-22 handoff is stale as current status. Historical reports and Git
history remain unchanged and may still be cited as evidence.

## Blockers and non-blockers

- **Canonical blocker:** accepted later implementation lineages are committed
  but not all ancestors of current `main`.
- **Data blocker:** Production history and historically effective formal inputs
  are incomplete.
- **Owner decision blocker:** none for this documentation reconciliation. A
  future policy change, formal backfill, or promotion of research evidence
  would require a separate owner decision.

## Safety state for this handoff

This documentation task authorizes no application-code change, Production
mutation, deployment, migration execution, scheduler activation, or
`NEXT_TASK` change. `TOPICPILOT_PRODUCT_IDEAS.md` remains the deferred-ideas
owner and is referenced rather than duplicated.

# TopicPilot execution roadmap

**Status:** `CANONICAL / ACTIVE EXECUTION ROUTING`
**Last reviewed:** `2026-09-22`
**Evidence baseline before this documentation commit:** `main` at `f88ff51`

This document owns execution sequence, dependency routing, and current status.
Product intent belongs in [the product roadmap](product/TOPICPILOT_PRODUCT_ROADMAP.md),
and settled semantics belong in [the decision register](product/TOPICPILOT_PRODUCT_DECISIONS.md).
Work orders and reports remain detailed evidence, not competing roadmaps.

## Execution principles

- Canonical `main` is the completion boundary. A branch/worktree PASS is
  committed evidence, not a completed product capability.
- `IMPLEMENTED → VALIDATED → CANONICALIZED → RELEASE_CANDIDATE →
  PRODUCTION_RELEASED → POST_DEPLOY_VERIFIED` are separate states.
- Research history is not formal history. Formal replay requires
  date-effective authority and publication lineage for every required input.
- Daily Grade and Lifecycle are independent. Structural Role and selected
  Leader/importance are separate owner-curated formal inputs.
- The frontend consumes backend-owned formal semantics and never recreates
  Score, Grade, Lifecycle, ranking, eligibility, or signal policy.
- `107` is a current observed Topic scope, not a fixed business constant.
- Documentation-only work does not authorize Production mutation, deployment,
  migration execution, scheduler activation, or `NEXT_TASK` changes.

## Current state ledger

The ledger deliberately distinguishes canonical `main`, committed integration
evidence, and Production observations.

| Area | Canonical `main` | Committed evidence outside current `main` | Current disposition |
|---|---|---|---|
| Formal Topic / A1 | Formal authority infrastructure through the 2026-09-12 lineage; governance guard at `f88ff51` | M1 line through `5eefc33` demonstrates current 107/107 materialization plus downstream recovery candidates | `CANONICAL_RECONCILIATION_REQUIRED` |
| Historical / A2-A3 | Canonical OHLCV and historical read foundations | Continuity audit: Production begins 2026-08-13, has gaps; derived formal history is incomplete; rotation 14/15 | `FORMAL_CONTINUITY_INCOMPLETE` |
| Today / B1 | Existing Home/Today baseline with partial semantics | Today Signals, market/stock institutional flow, breadth/distribution, index/turnover integrations on governed development lineages | `CANONICAL_RECONCILIATION_REQUIRED` |
| Opportunity / B2 | Shadow and bounded formal consumer foundations | Full-universe consumer and FUND-C evidence enrichment; formal provider still fail-closed | `UPSTREAM_AND_PROVIDER_GATED` |
| Topic / B3 | Catalog, PIT state, Structural Role, lifecycle/score contract foundations | Complete current-day chain candidates; historical completeness absent | `CURRENT_PIPELINE_RECONCILIATION_REQUIRED` |
| Stock / B4 | Search/filter, EOD, raw history and technical foundations | Stock institutional-flow formal capability on governed development lineage | `CANONICAL_RECONCILIATION_REQUIRED` |
| Decision Intelligence / C | Research tooling and evidence corpus | Additional feature-validation studies | `RESEARCH_ONLY_UNTIL_FORMALIZED` |

## A — Formal Data / Topic Engine

### A1 — Current Formal Pipeline

**Goal:** One governed daily chain for effective Topic universe → membership →
Structural Role/Leader input → Score → Daily Grade → Lifecycle → Topic/Today
publication → eligible downstream consumers.

**Current evidence:**

- Current formal Topic scope can materialize at 107/107 on the M1 integration
  lineage. Runtime must continue to resolve dynamic scope by as-of date.
- Structural Role authority is formal input; the selected Leader/importance
  projection is a separate owner-curated input and may not be inferred from
  research Leader Set or member order.
- Score/Daily Grade and Lifecycle are distinct formal outputs with independent
  availability and lineage.
- The post-`f88ff51` candidate chain contains corrections and hardening that are
  not yet on `main`; therefore A1 is not canonically complete.

**Next bounded execution:**

1. Reconstruct the accepted post-`f88ff51` ancestry and classify every path.
2. Reconcile only accepted implementation/authority artifacts into `main` via
   commit-preserving integration.
3. Run governance, focused backend, API/OpenAPI/client, frontend, migration
   single-head, and clean-candidate validation as applicable.
4. Record exact source-to-main SHA mapping. Release/Production remains a
   separate owner-authorized lane.

### A2 — Historical Data Foundation

**Goal:** Authoritative, continuous, point-in-time market and reference inputs.

**Current evidence:** Production daily observations begin on 2026-08-13 and
are not continuous. The older two-year bootstrap belongs to a non-Production
environment. Adjustment state, lifecycle, provider coverage, and missing
session gaps stay explicit.

**Next bounded execution:** inventory authoritative Production gaps, establish
date-effective reference/provider coverage, and create a governed recovery
plan. Do not copy research/bootstrap rows into Production formal history.

### A3 — Formal Historical Continuity

**Goal:** Replayable historical Topic/Score/Grade/Lifecycle/Opportunity state.

**Current evidence:** historical Topic snapshots are partial, no audited
session has a complete formal derived chain, and rotation has 14 observed
formal sessions against a 15-session requirement as of 2026-09-21.

**Next bounded execution:** wait for/generate genuinely governed sessions,
close historically effective authority gaps, then validate continuity by date.
No forward-fill, retrospective taxonomy rewrite, or research-to-formal
promotion is permitted.

## B — User-facing Product

### B1 — Today

Today owns market orientation: indices, turnover, institutional flow,
breadth/distribution, events, and deterministic signals. It must expose
dependency completeness. Missing signal inputs mean `PARTIAL`/`UNAVAILABLE`,
not “no abnormal signal”.

Execution order: canonicalize shared formal facts → validate Home read model →
validate generated contracts → render only backend-owned states → release and
read back separately.

### B2 — Opportunity

Opportunity owns downstream qualification and explanation, not market summary.
It consumes formal upstream authority through a backend composition boundary.
The full-universe consumer and FUND-C evidence enrichment remain additive and
must not create scores, gates, ranking changes, or a recommendation by
themselves.

Execution order: A1 complete → formal provider active → deterministic writer/
read model → API/client → frontend → Production readback. Until then, fail
closed and preserve shadow/research labels.

### B3 — Topic

Complete the formal Topic page from canonical identity, membership, roles,
Score, Daily Grade, Lifecycle, ranking, breadth, leadership, concentration,
history, and disclosure. Do not treat API mode as proof that every field is
formal, and do not hard-code 107.

### B4 — Stock

Preserve completed search/filter, EOD, and historical-price paths. Canonicalize
technical and institutional evidence through formal backend contracts before
claiming current user-facing availability. Event/corporate-action context and
Opportunity remain separate downstream contracts.

## C — Decision Intelligence

### C1 — Statistical Research

Continue PIT-safe, no-look-ahead research with explicit dataset provenance.
Outputs are evidence-only.

### C2 — Feature Validation

Require coverage, missingness, temporal stability, concentration, robustness,
and failure-mode review. A validated feature is still not formal policy.

### C3 — Decision Layer

Owner review chooses accept/reject. Accepted evidence then receives a formal,
versioned, effective-dated contract, canonical `main` implementation, release,
and Production readback before it may alter eligibility, ranking, state, or
explanation.

## Priority order

| Priority | Execution outcome |
|---|---|
| **P0** | Canonical reconciliation of A1 and shared daily-pipeline candidates into `main`; exact-SHA validation and handoff. |
| **P1** | A2/A3 Production history and formal continuity recovery, including the 15-session rotation requirement. |
| **P2** | B1 Today and B3 Topic formal product completion; B4 evidence publication. |
| **P3** | B2 formal Opportunity provider/publication after upstream completion; C1/C2 continue without policy promotion. |
| **P4/P5** | Intraday expansion, advanced UX/notifications, and AI Studio remain deferred. |

Parallel execution is allowed only where ownership and write sets do not
conflict. P0 is a dependency priority, not permission to merge every candidate.

## Validation and closeout requirements

For this documentation reconciliation and future canonical promotion:

- explicit-path staging only;
- Markdown path/link validation and `git diff --check`;
- documentation governance/system-of-record validation;
- secret-safe scan for the modified files;
- exact `MAIN_HEAD`, source SHA, canonical SHA, validation result, and blocker
  reporting;
- confirmation of Production, deploy, migration, scheduler, push, and
  `NEXT_TASK` state.

## Stale-status handling

All 2026-08-22 “current” status blocks are superseded by this roadmap. They
remain valid historical evidence in reports and Git history, but they do not
override the 2026-09-22 ledger. No historical report is rewritten by this
reconciliation.

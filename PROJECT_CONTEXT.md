# TopicPilot current project context

**Status:** `CURRENT STARTUP / HANDOFF NAVIGATION`
**Last reviewed:** `2026-08-14`

This file is deliberately short. It tells a contributor where the current
authority lives and what is true at handoff; it is not a duplicate product,
architecture, schema, or work-order authority.

## Read first

1. [Collaboration and safety rules](AGENTS.md)
2. [Execution roadmap](docs/ROADMAP.md)
3. [High-level product roadmap](docs/product/TOPICPILOT_PRODUCT_ROADMAP.md)
4. [Architecture authority map](docs/architecture/README.md)
5. [Accepted product surfaces contract](docs/architecture/PRODUCT_SURFACES_AND_UX_CONTRACT.md)
6. [Documentation index](docs/DOCUMENTATION_INDEX.md)

## Canonical boundary

- Canonical repository: `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
- All permanent changes belong in this repository. Task/worktree folders are
  isolated execution areas and are not formal authority.
- Do not modify application code, schema, migration, runtime/deploy config,
  Production data, or `NEXT_TASK` during a documentation handoff.
- V1 is `LEGACY BRIDGE / PARTIAL RETIREMENT`; V2 is the active platform path.
  Legacy retirement requires V2 replacement plus dual-run/parity and an
  explicit cutover decision.

## Current workstream handoff

- **Mainline A — DATA / Reference / Post-Close:** complete through
  `TASK-DATA-REF-009A`. G0, G1, G2, G3, and Canary are current `PASS` evidence;
  the 2026-08-13 TPE 313 + TWO 193 date-effective universe reconciled to
  `506/506`, with `DOWNSTREAM_READY=true`. A is no longer the general product
  development critical path. Re-run its protected gates only when the impact
  reaches a protected boundary.
- **Mainline B — Historical:** `HIST-001` is complete. Follow-up work is the
  six-month local/full seed, historical provenance, and technical/recommendation
  inputs. Historical OHLCV readiness is not historical Topic/System State
  readiness: six months of prices cannot fully replay historical topic scores,
  grades, lifecycle, or relation state without point-in-time inputs and lineage.
- **Mainline C — Today:** Daily Focus and Market Events isolated wiring is
  complete. Market Overview and the remaining formal-data/read-model gaps are
  follow-up work; temporary or partial Home data must stay visibly temporary,
  preview, or unavailable.
- **Mainline E — Stock:** formal code/name search and formal topic-filter wiring
  are complete in isolation. Follow-up work is reconciliation, EOD
  presentation, percentage-change semantics, Drawer regression/detail data,
  and other missing detail fields.

## Product surface gaps and deferrals

- Topic page still needs formal publication for the Today Topic Map `S/A/B/D`
  groups, formal Topic Lifecycle data, missing detail fields, and a fix for the
  large-group accordion same-row height coupling bug.
- Favorites is mainly UI polish and shared Drawer/favorite-state cleanup.
- Opportunity keeps its shadow/production wiring boundary; it is not a
  production recommendation publication.
- Intraday quote update is deferred. AI Studio is deferred.
- Master Data/Admin, News/Event foundation, AI Topic Discovery, and correction
  suggestions follow the sequence in the execution and product roadmaps. AI may
  suggest; it may not directly change canonical taxonomy or relations.

## Priority and parallelism

The product priority order is P0 Product Completion, P1 Historical +
Recommendation research, P2 Data Management + News + Discovery, P3 Opportunity
+ Favorites polish, P4 Intraday, and P5 AI Studio. This is a product priority
and dependency order, not a global serialization lock. Independent workstreams
may run in parallel when their contracts and write sets do not conflict.

Recommendation candidates A1 Pre-Breakout, A2 Confirmed Breakout, A3 Strong
Pullback/Retest, and Catch-up/rotation are `RESEARCH CANDIDATE` only. The
required path is Historical/Proxy Backtest → Point-in-time/Walk-forward →
Strategy Review → Accepted/Rejected → Formal Contract → Production
Implementation. `HIST-001` completion does not authorize production
recommendation implementation.

## Stale-document rule

Old `TASK-LIVE-002 = WAITING_LIVE_VALIDATION`, provider-activation blockers,
old migration-head summaries, repository-status snapshots, and old Opportunity
“next gate” wording are historical evidence unless the current authority above
links them as active. Do not use them to override this 2026-08-14 handoff.
The repository does not currently contain a separate
`docs/DOCUMENTATION_AUTHORITY_INDEX.md` or
`docs/handoffs/TOPICPILOT_CURRENT_HANDOFF.md`; do not create a parallel copy.

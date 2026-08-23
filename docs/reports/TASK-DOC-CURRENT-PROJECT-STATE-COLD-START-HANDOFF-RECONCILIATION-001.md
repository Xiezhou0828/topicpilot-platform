# TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001

**Date:** `2026-08-16`
**Scope:** canonical startup/current-state documentation only. This task does
not authorize product development, release-chain closure, deployment, or
Production mutation.

## Closure fields

```text
TASK_ID=TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001
FINAL_STATUS=CURRENT_PROJECT_STATE_COLD_START_HANDOFF_RECONCILIATION_COMPLETE
CANONICAL_PRE_SHA=147b991a03d3e8868a9a7c345a93e270260802f4
CANONICAL_POST_SHA=f539640e6245c73c3b53b2bddb272fa4489c01be
BOOTSTRAP_DOCS_AUDITED=6
LATEST_CLOSURES_AUDITED=A_STOCK_004;B_DOCUMENTATION_PROVIDER_DB_FIXTURE;HIST_AUTHORITY;STOCK_006A;TOPIC_PIT_DAILY_STATE;REC_A1_FREEZE;TODAY_MAINLINE;OPPORTUNITY_V1
CURRENT_STATE_EVIDENCE_LEDGER_CREATED=YES
CURRENT_STATE_EVIDENCE_LEDGER=docs/reports/TASK-DOC-CURRENT-PROJECT-STATE-COLD-START-HANDOFF-RECONCILIATION-001/current-state-evidence-ledger.json
```

The six audited bootstrap documents are `AGENTS.md`, `PROJECT_CONTEXT.md`,
`docs/ROADMAP.md`, `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`,
`docs/DOCUMENTATION_INDEX.md`, and `docs/DOCUMENTATION_GOVERNANCE.md`. A and B
are the latest release-hygiene closures. Capability evidence was rebuilt from
committed history, reports, work orders, and committed code; owner-untracked
reports were not used as required evidence.

## Current state answer

### Stock

| Capability | Current state | Evidence level |
|---|---|---|
| EOD | StockEodRead list/detail and Explorer/Drawer presentation are closed through 005B/005C | `IMPLEMENTED / VALIDATED / CANONICALIZED` |
| Search/filter | Code/name search and formal topic filtering are closed by Stock-004 | `IMPLEMENTED / VALIDATED / CANONICALIZED` |
| Historical bar backend | Bounded V2 raw historical bar read is published from the shared authority | `IMPLEMENTED / VALIDATED / CANONICALIZED`; adjustment state remains `UNKNOWN` |
| Historical price frontend | Formal bounded raw history is wired without preview, mock, or browser-derived technical fallback | `IMPLEMENTED / VALIDATED / CANONICALIZED` |
| Technical publication | Basic/advanced technical outputs and continuity indicators are not ready | `DEFERRED / RESEARCH_ONLY` |
| Timeline/event markers | Price-history timeline is available; event timeline and corporate-action markers are deferred | `PARTIAL / DEFERRED` |
| Institution flow | Unavailable | `DEFERRED` |
| Narrative | Unavailable | `DEFERRED` |
| Opportunity/recommendation | Unavailable; historical-price closure does not authorize publication | `DEFERRED / RESEARCH_ONLY` |

### Today

Home/Today wiring is canonicalized for Daily Focus, Main Topics,
Heating/Cooling, Market Events, and Market Overview. It preserves explicit
`FORMAL`, `TEMPORARY`, `PREVIEW`, `PARTIAL`, and `UNAVAILABLE` states.

The 005B index work is a typed TWSE/TPEx contract and fixture boundary only;
source-use approval, persistence, post-close capture, Home/API projection, and
frontend activation are not complete. Turnover remains blocked by TPEx
semantics and source-use approval. Market indices, turnover, narrative,
volume-trend, bullish/bearish, and derived market score/data-gap fields must
remain nullable or unavailable; the browser may not derive them.

### Topic

PIT membership and daily formal state are not completely absent. Migration 0030
implements the formal authority and bounded materialization: five dates,
`460` formal published non-superseded snapshots, and `4,235` member facts.
Formal-only endpoints exclude research/shadow rows and the materialization has
deterministic replay, immutability, and isolation evidence.

That foundation is deliberately not conflated with derived publication:

- Score is `NULL / DEFERRED`.
- S/A/B/D Grade and formal ranking are not published.
- Participation is limited to raw counts/coverage; breadth and concentration
  are deferred, and leadership is unavailable.
- Lifecycle engine/state-machine work exists at a shadow boundary;
  `LIFECYCLE_STATE=SHADOW_ONLY / UNPUBLISHED`.
- Topic Overview/Market Map UI is implemented, but formal lanes are data
  dependent and must not synthesize missing fields.
- Topic Detail disclosure/UI exists, while several formal detail domains remain
  unavailable or contract gaps.

### Historical boundary

The V2 canonical observation chain is the sole V1/V2 historical publication
authority for the reconciled `63,826` price and volume rows covering
`2026-02-02..2026-08-13` across `507` symbols. The legacy table is evidence and
staging only. This is price-history authority, not historical Topic/System
State. Historical Topic State would additionally require point-in-time topic
membership, effective-dated relations, reference/session/calendar bindings,
policy versions, and lineage. Corporate-action adjustment continuity remains
deferred/unknown.

### REC-A1 and Opportunity

REC-A1 Dataset/Protocol Freeze is canonicalized as a research-only,
owner-accepted residual-risk support dataset. It is not exchange-grade
completeness and does not alter Production or historical OHLCV authority.
Core V0 walk-forward is `READY_FOR_OWNER_AUTHORIZATION`; it was **not executed**.

A1 Pre-Breakout, A2 Confirmed Breakout, A3 Strong Pullback/Retest, and
Catch-up/rotation remain `RESEARCH CANDIDATE`. Opportunity has deterministic
shadow contracts, policy, read API, and UI wiring with synthetic fixtures, but
no completed performance/backtest, walk-forward, strategy review/acceptance,
or formal recommendation publication.

### Release state

Stock-004 A closed `BLK-HYGIENE-01`; B closed `BLK-HYGIENE-02/03/04`, passed the
DB integration fixture, and preserved/classified owner dirty/untracked state.
The current state is:

```text
REPOSITORY_HYGIENE_STATUS=READY_FOR_RELEASE_CHAIN_CLOSURE
READY_FOR_RELEASE_CHAIN_CLOSURE=YES
READY_FOR_PRODUCTION_RELEASE=NO
RELEASE_CANDIDATE=NO
PRODUCTION_RELEASED=NO
POST_DEPLOY_VERIFIED=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
```

There is no evidence in this closure of a release-candidate SHA, owner-
authorized release promotion, runtime revision, or public post-deploy
verification. Release-chain work remains Owner-controlled and is not started
by this documentation task.

## Stale-claim scan and disposition

The scan covered the six bootstrap documents and their current-state sections.
The following stale or ambiguous claims were found and resolved without
rewriting historical reports:

| Stale claim | Disposition |
|---|---|
| Topic Snapshot is wholly unavailable | Replaced with the exact 0030 bounded result: 460 formal snapshots and 4,235 member facts; derived Score/Grade/Lifecycle remain incomplete. |
| Historical price has not been published | Replaced with Stock-006A backend/frontend canonicalized raw-history state; adjustment and derived technical state remain deferred. |
| REC-A1 Freeze is blocked | Superseded in current docs by the later canonical closure: freeze authorized and canonicalized for research-only residual risk; walk-forward still not executed. |
| Stock search/filter is not canonicalized or EOD remains the next slice | Replaced with A, 005B, and 005C closure state. |
| Topic frontend publication task is the current dependency authority | Removed from current-state routing; current docs now link to committed PIT closure and this reconciliation. |
| Owner-untracked Topic audit reports are required to reconstruct state | Removed as current navigation dependencies; only committed closure reports are linked. |

Historical reports retain their original audit-time claims. They are not
rewritten to match this later transition.

## Cold-start handoff acceptance

A clean-reader simulation was performed against the six bootstrap documents,
the explicitly navigated committed closure reports, this report, and the
machine-readable ledger. It can answer all required questions without chat
memory or owner-untracked files:

1. Current canonical/release state: hygiene ready for release-chain closure;
   production release not ready; no push/merge/deploy.
2. Stock: search/filter, EOD, raw historical backend/frontend are canonical;
   technical/events/institution/narrative/Opportunity/recommendation remain
   deferred or unavailable.
3. Today: Home wiring is canonical; formal indices are contract-only and
   turnover, narrative, score, and other formal gaps remain.
4. Topic: PIT daily state exists under migration 0030; Score/Grade/ranking,
   breadth, leadership, concentration, and formal Lifecycle publication do not
   complete from that foundation.
5. Historical OHLCV is price/volume observation authority; it is not historical
   Topic/System State.
6. REC-A1 Freeze is canonicalized research-only; Core V0 walk-forward is ready
   for owner authorization but not executed.
7. Opportunity candidates have not completed performance backtest, strategy
   acceptance, or recommendation publication.
8. Production release is not allowed because no owner-authorized release
   candidate/promotion/runtime evidence exists and `READY_FOR_PRODUCTION_RELEASE=NO`.
9. The next stage is a dependency choice among deferred formal-data/research
   workstreams or Owner-authorized release-chain closure; only Owner can start
   the release-chain path and `NEXT_TASK` is unchanged.

```text
COLD_START_HANDOFF_TEST=PASS
COLD_START_REQUIRES_CHAT_MEMORY=NO
COLD_START_REQUIRES_OWNER_UNTRACKED_DOCS=NO
```

## Validation and preservation

The final values below are filled after the proven documentation commit and
scoped checks. The task intentionally leaves application files and owner
dirty/untracked artifacts outside its write set.

```text
PROJECT_CONTEXT_FRESHNESS=PASS
ROADMAP_FRESHNESS=PASS
PRODUCT_ROADMAP_FRESHNESS=PASS
DOCUMENTATION_INDEX_FRESHNESS=PASS
STOCK_STATE_RECONCILED=YES
TODAY_STATE_RECONCILED=YES
TOPIC_STATE_RECONCILED=YES
HISTORICAL_STATE_RECONCILED=YES
REC_A1_STATE_RECONCILED=YES
OPPORTUNITY_STATE_RECONCILED=YES
RELEASE_STATE_RECONCILED=YES
TOPIC_PIT_DAILY_STATE=IMPLEMENTED_VALIDATED_CANONICALIZED
TOPIC_SCORE_STATE=DEFERRED
TOPIC_GRADE_STATE=DEFERRED
TOPIC_LIFECYCLE_STATE=SHADOW_ONLY_UNPUBLISHED
HISTORICAL_PRICE_PUBLICATION_STATE=IMPLEMENTED_VALIDATED_CANONICALIZED_RAW
REC_A1_FREEZE_STATE=CANONICALIZED_RESEARCH_ONLY
CORE_V0_WALK_FORWARD_STATE=READY_FOR_OWNER_AUTHORIZATION_NOT_EXECUTED
OPPORTUNITY_BACKTEST_STATE=NOT_EXECUTED
READY_FOR_RELEASE_CHAIN_CLOSURE=YES
READY_FOR_PRODUCTION_RELEASE=NO
LINK_CHECK=PASS
GOVERNANCE_TESTS=PASS
DIFF_CHECK=PASS
SECRET_SCAN=PASS
OWNER_DIRTY_STATE_PRESERVED=YES
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
PRODUCTION_MUTATION=NO
NEXT_TASK_CHANGED=NO
REPORT_CREATED=YES
```

The proven documentation commit SHA is recorded in `CANONICAL_POST_SHA` after
the explicit-path commit; the final report commit is the immediately following
report/index commit. No release-chain or product task is started here.

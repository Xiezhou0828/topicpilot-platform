# TopicPilot Product Ideas

**Status:** `CANONICAL / DEFERRED IDEAS`
**Last reviewed:** 2026-08-12

Ideas are deliberately not roadmap commitments. Moving an item to `APPROVED_LATER` still requires an explicit PM decision and a roadmap/work-order update.

## Current PM Decision — Opportunity Engine

**Decision date:** 2026-08-12
**Status:** `FROZEN PRODUCT DIRECTION; SHADOW IMPLEMENTATION / CALIBRATION ONLY`

TopicPilot's downstream stock-selection capability is now positioned as an **Opportunity Engine / 機會篩選與研究整合層**, not a black-box AI tip or `Buy / Sell / Strong Buy` recommendation system. The product flow is:

```text
市場 → 題材 → 題材內股票 → Stock Encyclopedia → Opportunity / 查看機會
```

The system first decides whether a topic deserves research, then evaluates stock eligibility, technical/risk structure, and current entry quality. It does not directly rank the whole market and does not treat every input as points in one composite score. Hard Gates remain separate from ranking factors; news/Radar is catalyst/context, chip data is confirmation, and every surfaced Opportunity requires structured evidence.

Current user-facing states are `升溫候選`、`轉強觀察`、`精選機會`、`等待回測`、`失效`. Backend ranking may exist for ordering, but customer presentation is status-first and evidence-first rather than `87.4 分`、星等、AI confidence, or imperative trading language.

The detailed current specification is [TopicPilot Opportunity Engine Product & Architecture Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md). Thresholds, formulas, weights, support-distance bands, cooldowns, transition rules, validity periods, and intraday reordering remain `OPEN / NOT PM-FROZEN`.

### Historical continuity

Earlier concepts such as `題材 × 技術面綜合分數`, `推薦分數`, `補漲候選／落後補漲`, strategy candidates, and Candidate Recommendation Score/Rank remain part of TopicPilot's product and migration history. They are not deleted and may still describe legacy data or implemented read-model boundaries. For current product direction, the Opportunity Engine decision above takes priority; historical numbers/examples must not be silently promoted into formal Opportunity rules.

| ID | Title | Status | First discussed | Target |
|---|---|---|---|---|
| IDEA-001 | Topic Peek / 題材卡 Hover 抽屜預覽 | IDEA | 2026-08-10 | V2.2/V3 candidate |
| IDEA-002 | 題材通知 | IDEA | 2026-08-10 | TBD |
| IDEA-003 | 收藏提醒規則 | IDEA | 2026-08-10 | TBD |
| IDEA-004 | 題材生命週期動畫與進階互動 | IDEA | 2026-08-10 | V3 candidate |
| IDEA-005 | AI研究室多 Agent 辯論式體驗 | IDEA | 2026-08-10 | V3/later |

## Current PM Decision - Opportunity Engine V1 Strategies

**Decision date:** 2026-08-12
**Status:** `V1 SHADOW / CALIBRATION; PRODUCTION ACTIVATION NOT AUTHORIZED`

The first Opportunity Engine strategy layer is intentionally multi-strategy:

```text
Theme Context → Eligibility → Exclusion → Evidence → Strategy Ranking → Opportunity Result
```

V1 implements two independent, strategy-specific shadow paths:

- `TREND_CONTINUATION` - a policy-eligible topic with a stock already holding healthy trend structure, positive relative strength, volume/context evidence, and no hard exclusion.
- `CATCH_UP` - a policy-eligible topic with a lagging-but-not-structurally-weak stock, relative-strength inflection/improvement, healthy trend, and volume activation evidence.

`EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain `FUTURE_NOT_IMPLEMENTED` and are not V1 ranking inputs. Trend and Catch-up rankings remain separate; there is no global cross-strategy winner or strategy feedback into Topic Score. Internal rank values are calibration metadata only, while confidence is a separate evidence-quality label rather than a probability.

The V1 strategy policy is versioned as `topic-opportunity-policy.provisional.1`. Allowed Grade/Lifecycle values, lag windows, relative-strength windows, volume activation, extension context, ranking weights, and confidence semantics remain `PROVISIONAL / TUNABLE`; no old V1 magic number or Recommendation score is promoted silently.

The implementation is shadow-only and consumes formal upstream Theme Context, effective membership, canonical daily OHLCV, and explicit no-trade/data-quality facts. Replay is deterministic and as-of bounded. No API, database schema, frontend, scheduler, lifecycle activation, trading behavior, or legacy V1 source is changed by this decision.

See [Opportunity Engine Product & Architecture Specification](TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md) and the TASK-BE-024 report for the architecture reconciliation labels `KEEP / REUSE / ADAPT / DEPRECATE_LATER / HISTORICAL_ONLY`.

### Current PM Decision - Opportunity decision/read contract (TASK-BE-024A)

The shadow strategy layer now has a deterministic decision contract with the
current Opportunity states `SELECTED`, `WAITING_RETEST`,
`WAITING_CONFIRMATION`, `DEFERRED`, and `EXCLUDED`. A provider-neutral read
projection carries identity, state, internal rank metadata, entry/support/risk
context, upstream topic context, and structured explanation. Frontend work,
when separately authorized, must be evidence-first and status-first; it must
not calculate state, gates, leaders, technical classes, stars, AI confidence,
or imperative buy/sell language in the browser.

Trend and Catch-up ranking profiles are independent and explicitly provisional;
no global cross-strategy winner exists. Fixtures cover all decision states and
the calibration interface is a schema placeholder only. Numeric weights,
thresholds, transition rules, validity periods, and outcome evaluation remain
`OPEN / NOT PM-FROZEN`; this document update does not activate production.

## IDEA-001 — Topic Peek

- **Problem/opportunity:** Home should remain visually calm while allowing fast topic discovery.
- **Concept:** On hover, the topic card opens from the right toward the left like a light drawer/tear-open panel. The second layer reveals lifecycle stage, day count, representative stocks, and related-stock count; the bottom CTA then offers `進入完整題材頁`.
- **Why it may help:** Preserves first-glance simplicity while making topic structure discoverable and memorable.
- **Risks:** Hover accessibility, motion sensitivity, mobile behavior, density, and interaction cost.
- **Dependencies:** Topic lifecycle API contract, representative-stock read model, related-stock count, responsive interaction design.
- **Status:** `IDEA`; does not block V2. Candidate signature interaction for V2.2/V3.

## IDEA-002 — 題材通知

- **Problem/opportunity:** Users may miss meaningful topic-state changes.
- **Concept:** Notify on entering S, rapid warming, cooling/退潮, or other explicitly governed lifecycle transitions.
- **Why it may help:** Turns lifecycle intelligence into timely user awareness.
- **Risks:** Alert fatigue, threshold ambiguity, false positives, notification permissions.
- **Dependencies:** Lifecycle contract, event taxonomy, notification infrastructure and user preferences.

## IDEA-003 — 收藏提醒規則

- **Problem/opportunity:** Saved topics/stocks need useful factual change signals without becoming advice.
- **Concept:** User-configurable reminders for factual changes such as freshness, lifecycle transition, or institution-flow events.
- **Why it may help:** Makes 收藏 a living monitoring surface.
- **Risks:** Blurring monitoring and recommendation, noisy rules, privacy and delivery concerns.
- **Dependencies:** Saved-item persistence, canonical event model, notification delivery.

## IDEA-004 — 題材生命週期動畫與進階互動

- **Problem/opportunity:** Lifecycle is conceptually important but can be hard to scan.
- **Concept:** Calm editorial timeline animation and richer transition/re-entry interactions.
- **Why it may help:** Improves comprehension of topic evolution.
- **Risks:** Decorative motion overpowering evidence, accessibility, unclear semantic mapping.
- **Dependencies:** Canonical lifecycle history and motion/accessibility design.

## IDEA-005 — AI研究室多 Agent 辯論式體驗

- **Problem/opportunity:** Deep research could benefit from structured perspectives after core intelligence is stable.
- **Concept:** Multiple research agents debate evidence and assumptions with inspectable provenance.
- **Why it may help:** Supports deeper exploration without making AI the product identity.
- **Risks:** Hallucination, authority confusion, cost, latency, and unsupported advice.
- **Dependencies:** AI research workspace, evidence provenance, policy/safety boundaries, approved product scope.

## Capture rule

Future ideas should use the fields above. A chat idea becomes a decision only through explicit PM approval and a source-document pointer.

## Future UX Ideas

The following direction is consolidated here so it is not scattered across chat
messages or completed work orders. It is future product direction and does not
imply that the current UI is already changed.

### UX-001 今日市場首頁：Market Pulse

- Use one consistent section-heading pattern outside white content cards.
- Keep 今日市場重點 as a compact, one-sentence market read.
- Replace the fixed-count 盤中重要事件 block with a compact, horizontally
  moving topic-event carousel that can represent an open-ended number of
  intraday events without making the page taller.
- Pause on mouse hover; support manual browsing; provide a topic filter such as
  全部、AI、BBU、PCB、機器人; and let each event click through to its topic page.
- Keep events topic-first, with cues for 升級、降級、升溫、退潮、首次進榜、
  主線形成. Motion should aid scanning rather than add decorative noise.
- Status: `APPROVED_LATER`; implementation needs keyboard, reduced-motion, and
  mobile acceptance criteria.

### UX-002 題材卡片 Hover 展開（V2）

Retain the approved right-side peel-open animation as a future V2 UX. The
expanded layer reveals topic context without forcing navigation, has an
accessible non-hover equivalent, respects reduced motion, and preserves the
primary topic link.

### UX-003 題材頁資料呈現策略

Connect the topic page to formal data first. If a required source is not yet
available, render a complete Mock Data experience with an explicit
「示範資料／Mock Data」 label and a concise contextual data-quality note. Do
not fill the page with repeated 「資料待更新」 placeholders.

Status: `APPROVED_LATER`; promote to the roadmap/work orders when the formal
topic-page data contract is ready.

## Current PM Decision - Opportunity Qualification Policy V1 (TASK-BE-024B)

**Decision date:** 2026-08-12
**Status:** `IMPLEMENTED / SHADOW ONLY; PRODUCTION ACTIVATION NOT AUTHORIZED`

This is an incremental PM semantic freeze over the existing BE-024 and
BE-024A shadow engine. It does not delete or replace earlier Opportunity ideas.
The Topic Engine remains the authority for Topic Score, Grade, and Lifecycle;
Opportunity consumes those upstream facts and does not recalculate them.

### Frozen qualification semantics

- `S` and `A` are the formal Opportunity universe for both Trend Continuation
  and Catch-up.
- `B` is not a normal formal candidate. It may enter only as a warming/improving
  `EXCEPTION_CANDIDATE` with explicit exception provenance.
- `D` is a hard exclusion for new Opportunities.
- Lifecycle is strategy-specific: Sprouting waits for confirmation; Fermenting
  is high-fit for Trend and medium-high-fit for Catch-up; Main Rise is high-fit
  for both; Mature is low/downgraded for Trend and retained with stricter gates
  for Catch-up; Declining hard-excludes new A/B Opportunities.
- `Close >= 20MA` is a hard gate. Missing 20MA evidence is `DEFERRED` and
  `Close < 20MA` is `EXCLUDED`. 60MA is structure/ranking/explainability
  evidence only and is never a hard gate.
- Risk/exclusion is evaluated before ranking. A/B ranking stays independent;
  there is no global winner.
- The stable states are `SELECTED`, `WAITING_RETEST`,
  `WAITING_CONFIRMATION`, `DEFERRED`, and `EXCLUDED`.
- Presentation is capped at Trend Top 3 and Catch-up Top 2 per topic. The
  backend retains the complete strategy-local ranking for research/debugging.
- Formal ranking is post-close. Intraday is status-only in V1; it does not
  perform high-frequency full reranking.

### Provisional and calibration boundaries

All numeric thresholds, weights, lifecycle rank multipliers, support-distance
rules, lag/RS/volume parameters, and maturity penalties are centralized,
versioned, `PROVISIONAL / TUNABLE`, and not claimed to be optimized. Future
historical replay reserves 1D/3D/5D/10D forward horizons, return/MFE/MAE,
threshold-hit, support/invalidation, and selection-provenance metrics with
no-look-ahead. No fake calibration, production write, scheduler change, or
customer publication is authorized by this decision.

`EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain future strategies. Chip or
institution evidence remains optional confirmation and cannot bypass a hard
gate. See the [TASK-BE-024B report](../reports/TASK-BE-024B_OPPORTUNITY_QUALIFICATION_POLICY_REPORT.md)
and [policy decision record](../architecture/decisions/OPPORTUNITY_QUALIFICATION_POLICY_V1.md).

## Current PM Decision — TASK-BE-024B Opportunity Qualification Policy V1

The Opportunity Engine is a topic-first research and qualification layer, not
a black-box AI tip or `Buy / Sell / Strong Buy` recommendation. The current
qualification order is Market Context → Topic Qualification → Stock Eligibility
→ Technical Structure → Risk Gate → Entry Quality → Chip Confirmation →
Opportunity State → Evidence / Explanation.

The compact pipeline sentence above is retained as historical context. For the
current TASK-BE-024B shadow policy, the normative order is Topic Qualification
-> Lifecycle Qualification -> 20MA Hard Gate -> Data Quality -> Risk/Exclusion
-> Strategy Evidence -> independent A/B Ranking -> Entry Quality -> Opportunity
State -> Evidence/Explanation.

For the current shadow policy, `S`/`A` topics form the formal Trend and Catch-up
universe; `B` can enter only as a provenance-backed warming/improving
`EXCEPTION_CANDIDATE`; `D` and `DECLINING` are hard excluded. `Close >= 20MA`
is the hard gate, while 60MA is structure/ranking context. Risk is evaluated
before ranking, Trend and Catch-up remain independent, and presentation is
capped at Trend Top 3 / Catch-up Top 2. Ranking is post-close and intraday is
status-only.

This decision supersedes earlier illustrative “topic × technical score”,
“catch-up candidate”, and “recommendation score” ideas for current semantics;
those concepts remain historical/provisional and are not deleted. All numeric
thresholds, weights, pattern definitions, cooldowns, exception upgrades, and
state-transition parameters remain `OPEN / PROVISIONAL / VERSIONED` pending PM
calibration. No implementation or production activation is implied here.

## Current PM Decision - TASK-BE-024C Shadow Read Surface

The first integration surface for Opportunity is a read-only Shadow API and
frontend adapter. It is not a production Recommendation API and does not
publish a buy/sell decision. The formal flow remains:

`Market Context -> Topic Qualification -> Stock Eligibility -> Technical Structure -> Risk Gate -> Entry Quality -> Chip Confirmation -> Opportunity State -> Evidence / Explanation`

The backend read service projects topic-oriented, stock-oriented, list, and
detail views from the existing BE-024B semantic authority. It exposes
strategy-local Trend/Catch-up sections, A/B provenance, policy and parameter
versions, structured evidence, and explicit loading/empty/deferred/unavailable
semantics. Trend Top 3 and Catch-up Top 2 are presentation caps; the complete
backend ranking remains available for detail/research and is not a global A/B
winner.

The frontend adapter only consumes formal backend semantic fields, groups
sections, formats display keys, and follows backend display order. It must not
derive eligibility, risk, state, ranking, technical classification, or an
exception from raw fields. Existing topic x technical score, catch-up
candidate, and legacy Recommendation wording remains historical or provisional
unless explicitly superseded by a later PM decision.

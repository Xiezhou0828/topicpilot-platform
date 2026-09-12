# WS2 — Stock Technical V0

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; the policy and provider/consumer contracts
own the formal rules.

## Scope

Technical V0 is the bounded, point-in-time stock technical evidence surface. It
covers the fixed indicator set, raw-observed price basis, continuity and
known-event authority, as-of/lineage binding, unavailable states, and the
consumer publication boundary.

## Current state

- The current policy is `stock-technical-v0-policy.v4`.
- The fixed V0 set contains exactly 14 indicators: MA5, MA10, MA20, MA60,
  distance-to-MA20, raw close returns 5D/20D, volume MA5/MA20, volume ratio 20,
  RSI14, and MACD 12/26/9 line/signal/histogram.
- Technical result, event authority, and publication status are independent
  dimensions.
- The evidence surface covers 507 instruments and 63,826 canonical OHLCV rows.
  The latest inventory reports 0 instruments with ordinary formal evidence
  publication, 85 `AVAILABLE_WITH_LIMITATION`, 422 blocked at the current
  surface, and no calculation errors.
- Values are evidence only. Technical V0 does not emit recommendation or
  strategy-acceptance semantics.

## Canonical authority

- [Stock Technical V0 Policy Contract](../architecture/STOCK_TECHNICAL_V0_POLICY_CONTRACT.md)
- [Stock Technical V0 Formal Evidence Provider & Consumer Contract](../architecture/STOCK_TECHNICAL_V0_FORMAL_EVIDENCE_PROVIDER_CONSUMER_CONTRACT.md)
- [Stock Technical V0 Continuity Authority Closure](../architecture/STOCK_TECHNICAL_V0_CONTINUITY_AUTHORITY_CLOSURE.md)
- [Architecture authority map](../architecture/README.md)

## Completed

- Owner policy and publication dimensions are canonicalized.
- The 14-indicator identity, deterministic numeric policy, raw-observed basis,
  and minimum-history rules are fixed.
- Known-event-aware overlay and bounded `AVAILABLE_WITH_LIMITATION` behavior
  are defined.
- PIT/as-of, identity, algorithm/version, continuity, source lineage, and
  unavailable-reason requirements are defined.

## Unfinished / unpublished

- Formal Evidence Provider & Consumer Contract integration into the mainline
  consumer surface.
- Ordinary formal evidence publication for qualified instruments.
- Event/corporate-action markers, institution flow, narrative, Opportunity,
  and recommendation remain separate contracts.

## Dependencies and blockers

- Canonical historical observation identity and accepted-session windows.
- Known-event lookup authority and source lineage.
- The Owner-authorized provider/consumer integration boundary.

## Do not do

- Do not add indicators or retune Technical V0 policy in this series.
- Do not treat missing event evidence as `NO_EVENT` or as formal clearance.
- Do not convert raw-observed values into adjusted-price or total-return truth.
- Do not turn technical evidence into Buy/Sell/Hold, entry, stop, target,
  position sizing, or strategy acceptance.
- Do not activate Production merely because local calculations pass.

## Historical evidence

- [Technical V0 publication closure](../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818.md)
- [Technical V0 indicator/evidence inventory](../reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819.md)
- [Technical V0 public coverage validation](../reports/TASK-WS2-TECHNICAL-V0-REAL-PUBLICATION-COVERAGE-VALIDATION-AND-MAINLINE-RESUME-20260818.md)
- [Technical V0 provider/consumer closure](../reports/TASK-WS2-E2-TECHNICAL-V0-FORMAL-EVIDENCE-PROVIDER-CONSUMER-CONTRACT-AND-603-MAINLINE-CLOSURE-20260820.md)

## Next bounded route

Integrate the existing normalized, read-only evidence surface through the
Owner-authorized Formal Evidence Provider & Consumer Contract. Preserve the
three independent status dimensions and bounded limitations. This is not a new
indicator, strategy, recommendation, migration, or Production activation.

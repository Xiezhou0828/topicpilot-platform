# Opportunity Qualification Policy V1

**Decision date:** 2026-08-12
**Status:** `COMMITTED / SHADOW ONLY`

## Context

TASK-BE-024 and TASK-BE-024A already provide independent Trend Continuation and
Catch-up shadow strategies, deterministic state mapping, explainability, and a
provider-neutral read contract. They did not yet provide one explicit PM policy
for Grade, Lifecycle, technical gates, risk ordering, presentation, and
cadence.

## Decision

The Qualification Policy V1 is an additive deterministic policy layer above the
existing engine. Topic Engine remains authoritative for Topic Score, Grade,
Lifecycle, and Strength; Opportunity consumes those values and never
recalculates them.

| Concern | Frozen semantic | Runtime representation |
|---|---|---|
| Grade | S/A formal; B warming/improving exception with provenance; D hard exclude | `OpportunityQualificationPolicy` and qualification decision |
| Lifecycle | Sprouting waits; Fermenting high/medium-high fit; Main Rise high fit; Mature Trend low/downgraded and Catch-up stricter; Declining hard excludes new A/B | lifecycle strategy matrix/evidence |
| 20MA | Close >= 20MA required; below excludes; missing defers | technical qualification stage |
| 60MA | Structure/ranking/explainability factor; never a hard gate | technical evidence and provisional rank context |
| Risk | Hard risk precedes ranking and cannot be rescued by score | risk qualification and rank nulling |
| Ranking | A and B remain independent; no global winner | strategy-local rank and mixed-list rejection |
| State | SELECTED / WAITING_RETEST / WAITING_CONFIRMATION / DEFERRED / EXCLUDED | decision/read contracts |
| Presentation | Trend Top 3; Catch-up Top 2; full backend ranking retained | `presentation_candidates` |
| Cadence | Post-close ranking; intraday status-only, no V1 reranking | policy metadata |

## Freeze versus provisional boundary

PM philosophy and semantic ordering above are frozen for the shadow contract.
Exact support distance, lag/RS/volume thresholds, weights, lifecycle rank
multipliers, maturity penalties, cooldowns, validity, and future intraday rules
are `PROVISIONAL / TUNABLE / VERSIONED`. They require point-in-time production
history and future replay/calibration across 1D/3D/5D/10D horizons. No fake
calibration is permitted.

The following remain explicitly `OPEN / NOT PM-FROZEN`: Grade qualification
threshold details; Lifecycle qualification mechanics; whether 20MA is the only
mandatory gate; any 60MA gate/bonus; support-distance and formal price/volume
pattern thresholds; risk cooldown days; Topic Quality/Technical/Entry/Chip
weights; maximum stocks per topic; Opportunity validity/expiry; intraday
automatic reranking; Exception upgrade and institution/chip confirmation
thresholds; and all Opportunity state-transition thresholds/timing.

## Consequences and boundaries

- B exception provenance remains visible in result/read/explainability output.
- Missing data remains `DEFERRED`; it is not treated as bearish or zero-filled.
- A high rank cannot override a hard risk or 20MA failure.
- Backend ranking is retained beyond the presentation cap.
- `EARLY_STRENGTH` and `PULLBACK_ACCEPTANCE` remain future strategy slots.
- No database migration, production API publication, scheduler, or Topic
  Score/Grade/Lifecycle algorithm change is authorized by this decision.
- Historical decisions are preserved; this ADR is incremental and does not
  rewrite earlier BE-024/024A reports.

## Evidence

- [TASK-BE-024 report](../../reports/TASK-BE-024_OPPORTUNITY_ENGINE_V1_REPORT.md)
- [TASK-BE-024A report](../../reports/TASK-BE-024A_OPPORTUNITY_DECISION_CONTRACT_REPORT.md)
- [TASK-BE-024B report](../../reports/TASK-BE-024B_OPPORTUNITY_QUALIFICATION_POLICY_REPORT.md)

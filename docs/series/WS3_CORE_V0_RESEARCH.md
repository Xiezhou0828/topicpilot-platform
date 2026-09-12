# WS3 — Core V0 Research

**Last reconciled date:** `2026-08-22`

**Canonical baseline:** `b1731a05a44c1e880acb0be2a1bd4dfc26b4029`

**Summary role:** navigation only; research and strategy contracts own the
formal boundaries.

## Scope

Core V0 is the governed research lane for A1/A2 candidate definitions,
breakout formation, entry and invalidation evidence, point-in-time replay,
coverage, and forward validation. It is not a Production recommendation
engine.

## Current state

- A1 quality-filter confirmatory evidence is
  `FROZEN_AWAITING_FORWARD_EVIDENCE`; seven frozen candidates were not
  promoted.
- A2 confirmed-breakout formation remains frozen. Entry and invalidation work
  is bounded, descriptive, and evidence-only; no provisional entry/stop rule
  or Production strategy exists.
- The origin-attribution result is `EVIDENCE_ONLY_NOT_PROMOTED`: direct-entry
  A2 remains valid, and A1-origin context is not a formation requirement.
- The expanded 96-stock reference pack is staging-only toward a 603-candidate
  universe. Runtime identity/security validation, historical bootstrap,
  coverage/quality checks, and expanded-universe qualification remain future
  bounded routes.

## Canonical authority

- [Core V0 Candidate Definition Authority Contract](../architecture/CORE_V0_CANDIDATE_DEFINITION_AUTHORITY_CONTRACT.md)
- [Core V0 A1/A2 Breakout Formation Policy](../architecture/CORE_V0_A1_A2_BREAKOUT_FORMATION_POLICY_V0.md)
- [Core V0 Executable Candidate Panel Contract](../architecture/CORE_V0_A1_A2_EXECUTABLE_CANDIDATE_PANEL_CONTRACT.md)
- [Core V0 Real Coverage and Walk-forward Preflight Contract](../architecture/CORE_V0_REAL_COVERAGE_AND_WALK_FORWARD_PREFLIGHT_CONTRACT.md)
- [Core V0 Research Executability Authority Contract](../architecture/CORE_V0_RESEARCH_EXECUTABILITY_AUTHORITY_CONTRACT.md)

## Completed

- A1 dataset/protocol freeze and residual-risk research boundary.
- A1 quality-filter confirmation boundary and frozen candidate panel.
- A2 breakout-formation, entry, invalidation, and origin-attribution research
  boundaries.
- No-look-ahead and point-in-time research framing.

## Unfinished / not promoted

- A1 forward evidence and any future promotion decision.
- A2 bounded review and any later strategy acceptance.
- Expanded-universe runtime identity, historical coverage, and quality
  qualification.
- Formal strategy contract, Production implementation, and recommendation
  publication.

## Dependencies and blockers

- Canonical, point-in-time historical data and source lineage.
- Forward 1D/3D/5D/10D outcome evidence under an approved protocol.
- Owner review of research evidence before any semantic promotion.

## Do not do

- Do not retune thresholds or change A1/A2 algorithms from a report or fixture.
- Do not call a research candidate a Production strategy or recommendation.
- Do not use synthetic fixtures as calibration or forward evidence.
- Do not infer look-ahead-safe results from a later-updated dataset.

## Historical evidence

- [A1 confirmatory validation](../reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818.md)
- [A2 entry and invalidation research](../reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819.md)
- [A2 confirmatory validation](../reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-INVALIDATION-CANDIDATE-CONFIRMATORY-VALIDATION-20260819.md)
- [96-stock expansion reference pack](../reports/TASK-INSTRUMENT-UNIVERSE-96-STOCK-EXPANSION-REFERENCE-PACK-AND-RUNTIME-HANDOFF-20260819.md)
- [REC-A1 dataset/protocol freeze](../reports/TASK-REC-A1-DATASET-PROTOCOL-FREEZE_CANONICAL_CLOSURE.md)

## Next bounded route

Run only the approved forward-evidence and expanded-universe qualification
work. Preserve A1/A2 frozen semantics, provenance, and no-look-ahead checks;
stop at evidence review unless an Owner-approved strategy decision exists.

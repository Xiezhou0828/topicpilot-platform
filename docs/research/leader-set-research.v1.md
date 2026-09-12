# TopicPilot V2 Leader Set Candidate Research

**Research version:** `leader-set-research.v1`
**Status:** `NEEDS_REVIEW / DATA-UNAVAILABLE`
**Researched at:** 2026-08-09 (Asia/Taipei)
**Scope:** non-production master-data research only

## Executive result

No Leader Set candidate is proposed in this version. The repository audit found no real enabled topic universe and no real CORE membership population that can be cross-checked against public-market evidence:

- Canonical PostgreSQL tables `topicpilot.topics`, `topicpilot.instruments`, and `topicpilot.instrument_topic_relations` are empty.
- The only populated relation data is the legacy/public demo read model: 4 synthetic stocks and 5 synthetic relations.
- The checked-in `fixtures/demo/*` files contain the same synthetic universe (`digital-infrastructure`, `edge-ai`, `cloud-security`, `clean-energy`) and synthetic instrument codes (`DEMO-*`).
- Synthetic names are not valid securities and must not be researched or promoted into a governed Leader Set.

Therefore all four fixture topics are recorded as `NEEDS_REVIEW` with `membership_review_needed=true`; there are zero researched Leader Sets and zero candidates. This is an evidence-preserving stop condition, not a production blocker introduced by this research track.

## Methodology and source hierarchy

The intended research method is:

1. Read canonical topic and relation records; use only existing topic IDs/slugs/names.
2. Restrict the candidate pool to current CORE membership (with `PRIMARY` as the current conceptual basis).
3. For each real instrument, assess structural relevance, market recognition, scale/influence, durability, and topic sensitivity.
4. Prefer company filings and official investor materials, then regulatory/exchange disclosures, reputable industry/financial publications, and only then classification or market-data sources.
5. Use only `1.00`, `0.75`, or `0.50`; never use one-day performance as leader evidence.
6. Record alternatives and ambiguity; do not silently repair membership classification.

Because step 1 produced no real population, steps 2–6 were not executed against public companies. No external source was used to manufacture a candidate outside the repository universe.

## Topic universe audit

| Universe source | Topics | Instruments | CORE/PRIMARY relations | Result |
|---|---:|---:|---:|---|
| Canonical PostgreSQL `topicpilot` schema | 0 | 0 | 0 | No researchable universe |
| Legacy/public demo read model | 4 | 4 synthetic | 3 synthetic PRIMARY | Demo-only; excluded |
| Checked-in `fixtures/demo` | 4 enabled synthetic | 4 synthetic | 3 synthetic PRIMARY | Demo-only; excluded |

The four demo topics are listed in the machine-readable audit file for traceability, but none has a valid candidate population.

## PM review shortlist

1. Provide or import the real canonical topic master data and versioned instrument-topic relations.
2. Confirm the exact meaning of `CORE` in the source export. The current schema stores `relation_type` and `relation_version`; no populated canonical CORE dataset is present.
3. After data availability, approve the initial as-of date and research universe before any Leader Set candidate can be evaluated.
4. Decide whether topics with fewer than two well-supported CORE members remain `NEEDS_REVIEW` or receive a separately governed exception. This research does not decide that policy.

## Classification debt and ambiguity

- The current demo model contains `PRIMARY`, `SECONDARY`, and `RELATED`, while the PM brief describes CORE as the governed basis. The mapping from current relation types to CORE is not materialized in the available data.
- The canonical and legacy topic domains are separate schemas/models. Their IDs are not interchangeable.
- Demo/API `leaders` data, if present in compatibility fixtures, is not treated as approved evidence.

## Governance disposition

This artifact is a research candidate package only. It does not mark any row `APPROVED`, does not create a production Leader Set, does not change membership, and does not authorize provider activation. A future populated version must create a new immutable research/governance version and preserve source URLs, publication dates, evidence dimensions, confidence, alternatives, and reviewer decisions per row.

## Related canonical documents

- [PM Formula Approval Brief](../reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md)
- [Theme Governance & Knowledge System](../architecture/THEME_GOVERNANCE_KNOWLEDGE_SYSTEM.md)
- [Topic Engine contract](../architecture/PHASE_3_7_001_TOPIC_ENGINE_CONTRACT.md)

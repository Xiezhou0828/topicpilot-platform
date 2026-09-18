# FUND-001 Institution Flow Initiation Packet

**Status:** `PROPOSED / OWNER_DECISION_REQUIRED`
**Date:** `2026-09-13`
**Scope:** authority and execution-readiness questions only

This packet records the minimum decisions required before starting a formal
institutional-flow/FUND line. It does not select FinMind, create a provider,
add a migration, change the API, activate a scheduler, or implement a
frontend. The repository currently contains no evidence that FUND-001 has
started or that a formal institution-flow authority has been approved.

## Required decisions

1. **Owner and approver:** Who owns the institutional-flow contract, source
   approval, release gate, and rollback decision?
2. **Product surface:** Is the first approved surface Today Market Signals,
   stock detail, a dedicated institutional-flow page, or an internal/admin
   read only surface?
3. **Source authority:** Which provider is formally authoritative? If FinMind
   is proposed, what exact endpoint, license/use permission, account, and
   response contract are approved? A proposal is not an approval.
4. **Market and universe:** Which markets, instrument identities, and formal
   reference bundle version are in scope? How are excluded, delisted, and
   unmapped instruments represented?
5. **Point-in-time date:** What trading date/as-of/session semantics apply, and
   how are ROC/Gregorian dates normalized?
6. **Freshness and completeness:** What freshness window, expected coverage,
   no-trade behavior, missing-provider behavior, and completeness thresholds
   are required before publication?
7. **Schema:** Which fields are formal in V1 (for example buy/sell/net flow,
   lots/shares, value, source status, and as-of), and which are explicitly
   nullable or deferred?
8. **Lineage:** What provider version, request artifact, response hash, policy
   version, and effective date must be stored or exposed for replayability?
9. **Persistence and corrections:** Is the data append-only, correction-based,
   or snapshot-replaced? What migration, idempotence, supersession, and
   correction propagation rules are approved?
10. **API and consumer contract:** What endpoint/read model and publication
    states are approved, and which frontend consumer may render it? Browser
    aggregation and fallback to synthetic/shadow data are not assumed.
11. **Operations:** What scheduler time, retry/backoff/rate-limit behavior,
    protected credentials, manual backfill procedure, and operator owner are
    required?
12. **Acceptance and release:** What exact tests, source-to-SHA provenance,
    runtime readback, rollback evidence, and production data verification are
    required before `FORMAL` publication?

## Gate

```yaml
FUND_001: PROPOSED
OWNER_DECISION: REQUIRED
SOURCE_AUTHORITY: UNKNOWN
FORMAL_PROVIDER: NOT_CONFIGURED
SCHEMA_MIGRATION: NOT_STARTED
API_CONSUMER: NOT_STARTED
SCHEDULER: NOT_STARTED
PRODUCTION_WRITE: NO
PRODUCTION_PUBLICATION: NO
NEXT_ACTION: OWNER_ANSWER_12_QUESTIONS_AND_APPROVE_OR_REJECT_SCOPE
```

Until the packet is answered and approved, existing nullable or legacy
institution fields remain historical/partial evidence and must not be
presented as a formal FUND authority.

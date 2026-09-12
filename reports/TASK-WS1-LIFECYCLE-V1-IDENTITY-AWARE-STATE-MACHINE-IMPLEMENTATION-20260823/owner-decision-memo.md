# Owner Decision Memo

## Decision

Accept the V1 implementation for Owner validation in the isolated E: worktree. Do not deploy or promote it yet.

## Why

The implementation now has the requested five-stage identity-aware state machine and deterministic state memory. The production issue remains an evidence/provenance gap: 130 topics are exposed, but all are fail-closed as `INSUFFICIENT_DATA`; the available read-only probe cannot identify whether the first missing layer is materialization, scheduler execution, canonical price evidence, identity authority, persistence, or read-model selection.

The isolated 2026-08-12 evidence is useful as a comparison point, not as production truth. The current release/provenance gap is WS4-owned and is not repeated or repaired here.

## Smallest safe next WS1 action

Perform one read-only production chain check in this order: migration current/schema columns → runtime SHA/image → materializer latest date and counts → member-fact role/price coverage → lifecycle scheduler last run → persisted lifecycle result rows → API selection. Stop at the first missing evidence. No threshold change, backfill, replay, or mutation.

## Owner gates

- Lifecycle policy change: **NO**.
- Strength score or label: **NO**.
- Production DB mutation: **NO**.
- Historical reconstruction: required, but currently **blocked by local DB endpoint unavailable**; no synthetic result was substituted.
- Deploy/push/NEXT_TASK: **NO**.

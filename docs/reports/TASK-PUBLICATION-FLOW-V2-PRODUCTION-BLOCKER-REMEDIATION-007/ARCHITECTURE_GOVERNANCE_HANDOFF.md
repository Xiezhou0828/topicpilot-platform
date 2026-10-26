# Architecture and governance handoff

## Observed governance gaps

1. Canonical main and the live API/Worker revisions diverge. A deployment hook success alone is insufficient; provider live revision readback is now the required evidence.
2. The forensic role is nominally read-only but cannot SELECT the core formal read-model tables, so the approved diagnostic cannot inspect the failure it was designed to investigate.
3. Render's compact Worker events identify WAIT_PROVIDER_NOT_READY but omit provider, product, freshness predicate, response date, and correlation identifiers.
4. Neon readback now confirms a 6-hour history window with no snapshot or backup schedule, but the deployment architecture documentation still does not state the required backup policy, restore operator, isolated target, or restore-drill objectives.
5. A later reference preflight rollback error is emitted as a compact reason code without the underlying exception context.

## Handoff boundary

These findings are operational evidence, not a new authority specification. Formal Topic authority, manual structural roles, Leader definitions, selection rules, V1 retirement, and NEXT_TASK remain unchanged.

Recommended architecture follow-up: add non-secret runtime provenance, provider-level readiness fields, correlation IDs, safe exception summaries, and documented recovery SLOs to the existing contracts. Such changes require a separate Owner-approved task.

# Governance Two-Gate Implementation

## Development Preflight

`infra/scripts/governance/development_preflight.mjs` requires a named `codex/*` branch, a safe repository/common directory, explicit Preview and Financial API origins, explicit Research Read Model mode, and no peer write-set conflict. Dirty paths are reported and allowed. Missing preservation is a warning, not a reason to disguise normal local iteration as a delivery failure.

## Delivery Preflight

`infra/scripts/governance/delivery_preflight.mjs` requires a clean Task Branch, complete source inventory, verified preservation, passing validation, passing secret scan, generated-artifact consistency, source mapping, and a source SHA equal to `HEAD`. It reports `DELIVERY_READY` or fails closed; it does not Push, open a PR, Merge, Deploy, migrate, or write Production.

The two gates are covered by `two_gate.test.mjs`: a dirty fixture passes Development and is blocked by Delivery. Existing strict `task_preflight.mjs`, `task_delivery_check.mjs`, preservation, and governance checks remain available for compatibility.

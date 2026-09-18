---
name: topicpilot-release-gate
description: Check exact source and runtime provenance, migration lineage, formal data readiness, and fail-closed release boundaries.
---

Read the release manifest and current release/runtime evidence. Run
scripts/governance/check_release_gate.py with the candidate migration and
Production migration heads plus exact API/Web/Worker SHA readbacks.

If Production migration is newer than the candidate, return BLOCKED_MIGRATION.
If lineages diverge at the same revision, return BLOCKED_MIGRATION_LINEAGE.
Never downgrade, rollback, force-deploy, or treat an endpoint 200, opaque
deployment ID, research/shadow/fixture/synthetic data, or local validation as
Production proof. Release remains separate from product development.

---
name: topicpilot-integration-gate
description: Qualify a bounded task for canonical integration through ownership, commit, shared-surface, dependency, and baseline-failure checks.
---

Read the source manifest, current governed base, ownership registry, baseline
failure registry, and the source task report. Run
scripts/governance/check_integration_gate.py.

A task is READY_FOR_INTEGRATION only when its implementation commit is present,
owned paths pass, dependencies are satisfied or explicitly blocked, and
observed failures are known and correctly attributed. A known failure owned by
another workstream does not automatically block an unrelated task. An unknown
failure blocks qualification.

The integration agent ports or reconciles a validated commit; it does not
rewrite product semantics, silently resolve owner decisions, or make a
candidate Production.

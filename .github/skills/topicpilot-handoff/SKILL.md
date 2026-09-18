---
name: topicpilot-handoff
description: Produce a durable TopicPilot task handoff that separates implementation, integration, deployment, and verification.
---

At finish, record TASK, RESULT, BASE, BRANCH, WORKTREE,
IMPLEMENTATION_COMMITS, GOVERNANCE_COMMITS, TESTS, BASELINE_FAILURES,
DEPENDENCIES, OWNER_DECISION_REQUIRED, READY_FOR_INTEGRATION,
PRODUCTION_TOUCHED, and RECOMMENDED_NEXT_TASK.

State exactly what is proven at source, canonical, release, and runtime layers.
A task marked IMPLEMENTATION COMPLETE is not INTEGRATED; INTEGRATED is not
PRODUCTION VERIFIED. Include dirty/staged state and any shared surface needing
serial reconciliation. Preserve prior reports and decisions; link rather than
rewrite them.

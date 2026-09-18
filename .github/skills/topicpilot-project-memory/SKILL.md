---
name: topicpilot-project-memory
description: Recover TopicPilot project state, active work, ownership, dependencies, and release boundaries from repository evidence before mutation.
---

Use this skill at task start or after context loss.

Read in order:
1. AGENTS.md and PROJECT_CONTEXT.md.
2. CURRENT_PROJECT_STATE.md, ACTIVE_WORK.md, INCOMPLETE_WORK_REGISTRY.md,
   BRANCH_RECOVERY_MATRIX.md, and PARALLEL_EXECUTION_MATRIX.md.
3. The applicable docs/ROADMAP.md, docs/WORK_ORDERS.md, and
   docs/DOCUMENTATION_INDEX.md entries.
4. The latest implementation, canonicalization, release, and handoff reports
   named by those authorities.
5. Git HEAD, branch, worktree, status, recent commits, and relevant source
   history.

Produce a recovery snapshot with TASK_ID, canonical and development bases,
production API/Web/Worker/DB evidence, migration head, active workstreams,
related tasks, last known good commits, partial/blocked/superseded work,
baseline failures, owned/shared/forbidden surfaces, dependencies, owner
decisions, and recommended base.

Repository and runtime evidence outrank prompts, reports from another layer,
and chat memory. Code existence, isolated tests, HTTP 200, or a deployment
label do not establish canonicalization, deployment, or post-deploy
verification. Preserve dirty owner state and stop when evidence is missing.

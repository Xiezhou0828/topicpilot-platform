---
name: topicpilot-task-lifecycle
description: Validate TopicPilot task states, legal transitions, completion boundaries, and explicit abandonment or supersession evidence.
---

Load docs/governance/task_lifecycle.json and the selected task manifest.

Use only the declared statuses and transitions. IMPLEMENTED or source
existence is not VALIDATED; VALIDATED is not CANONICALIZED; canonicalized is
not INTEGRATED, RELEASED, DEPLOYED, or POST_DEPLOY_VERIFIED. A passing focused
test does not advance a task by itself.

READY_FOR_INTEGRATION requires an implementation commit. ABANDONED requires
disposition_evidence or supersedes evidence. Unknown dependencies, duplicate
task IDs, invalid status, and unexplained test-count reduction block the task.
Run check_task_manifest.py and check_task_lifecycle.py before handoff.

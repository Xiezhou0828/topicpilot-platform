---
name: topicpilot-parallel-worktree
description: Start and verify a bounded TopicPilot task in one named branch and one isolated E: worktree.
---

Before mutation, read the selected manifest and run
scripts/governance/check_worktree.py. The current path must match the manifest,
the branch must match, and the base SHA must be an ancestor of HEAD.

The canonical owner checkout at
C:\Users\acer\Desktop\題材領航\topicpilot-platform is read-only while dirty.
Do not stage, commit, stash, reset, restore, clean, build, or generate there.
Do not create a second development repository. Keep one task's changes inside
owned_paths; shared_paths require an integration-owner reconciliation.

At handoff record branch, worktree, base, dirty/staged state, exact commits,
validation, blockers, next task, and whether any shared surface needs serial
integration. Do not delete a historical worktree or branch without an explicit
disposition.

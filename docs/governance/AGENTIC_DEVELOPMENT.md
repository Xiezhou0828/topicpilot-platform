# TopicPilot Agentic Development Runtime

This guide is the short operating contract for a new agent or engineer. It is
a routing document, not a replacement for the canonical project state,
architecture, product, or work-order authorities.

## Start a governed task

1. Read AGENTS.md, PROJECT_CONTEXT.md, the applicable roadmap/work order, and the
   current-state reports named by those files.
2. Select the task manifest under docs/governance/tasks/.
3. Verify the branch, isolated worktree, base ancestry, and dirty state.
4. Load project memory, task lifecycle, and parallel-worktree skills.
5. Run the governance validator before mutation.
6. Work only inside the manifest owned_paths. Treat shared_paths as
   SHARED_REQUIRES_RECONCILIATION.
7. Run focused validation and record handoff evidence.
8. Stop at an integration gate, owner decision, operator gate, or release gate.

Repository evidence, the governance registry, the task manifest, and the
validated commit outrank chat history or a task prompt.

## Canonical runtime contracts

- Task status and dependencies: docs/governance/tasks/*.yaml, validated by
  scripts/governance/check_task_manifest.py.
- Lifecycle transitions: docs/governance/task_lifecycle.json.
- Workstream path ownership: docs/governance/WORKSTREAM_OWNERSHIP.yaml.
- Known failure attribution: docs/governance/BASELINE_FAILURE_REGISTRY.yaml.
- Authority routing: docs/governance/GOVERNANCE_AUTHORITY_MATRIX.md.
- Planned collisions: docs/governance/PLANNED_PARALLEL_COLLISION_MATRIX.md.
- Reusable handoff shape: .github/skills/topicpilot-handoff/SKILL.md.

The .yaml files are JSON-compatible YAML: JSON syntax is valid YAML and lets
the portable validator run without an unpinned parser dependency.

## Status semantics

Implemented source is not validated, validated is not canonicalized,
canonicalized is not integrated, integrated is not deployed, and deployed is
not post-deploy verified. ABANDONED requires explicit disposition or
supersession evidence. Old, unused, or unwired artifacts remain
ORPHAN_CANDIDATE, PARTIAL, UNKNOWN, or REVIEW_REQUIRED until an owner
disposition exists.

## Parallel safety

One mutation task uses one named branch and one isolated E: worktree. The
canonical owner checkout at C:\Users\acer\Desktop\題材領航\topicpilot-platform
is evidence-only while it is dirty. OpenAPI, generated clients, shared schemas,
migrations, release configuration, and formal publication contracts are
serial integration surfaces.

Future tasks should write their own manifest and report. Central status views
should be updated by a reconciler or a small owner-reviewed navigation change,
rather than by every parallel task.

## Portable commands

~~~text
python scripts/governance/validate_governance.py
python scripts/governance/validate_governance.py --self-test
python scripts/governance/check_task_ownership.py --manifest docs/governance/tasks/<TASK-ID>.yaml --paths <repo-relative-path>
python scripts/governance/check_worktree.py --manifest docs/governance/tasks/<TASK-ID>.yaml --require-clean
python scripts/governance/audit_incomplete_work.py --path . --summary
~~~

The repository-side scripts are authoritative and can run from a local CLI,
GitHub Actions, or another agent runtime. Copilot hooks are an additional
guard only; a hook availability gap never becomes a false claim of enforcement.

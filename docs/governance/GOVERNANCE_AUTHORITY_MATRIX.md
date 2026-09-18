# Governance Authority Matrix

One question has one canonical source. Reports and chat are evidence or
navigation unless the authority column says otherwise.

| Question | Canonical source | Evidence / validation |
|---|---|---|
| Task status | docs/governance/tasks/<TASK-ID>.yaml | Manifest validator and lifecycle contract |
| Worktree | Task manifest plus Git worktree metadata | check_worktree.py |
| Branch | Task manifest plus Git ref | check_worktree.py and commit ancestry |
| Owner | WORKSTREAM_OWNERSHIP.yaml plus manifest owner_role | check_task_ownership.py |
| Dependencies | Task manifest dependencies | check_task_manifest.py |
| Implementation commit | Task manifest implementation_commits plus Git object | Integration gate |
| Governance commit | Task manifest governance_commits plus Git object | Handoff/report |
| Production API/Web/Worker SHA | CURRENT_PROJECT_STATE.md and latest release/runtime report | Operator readback; opaque deployment IDs do not replace SHA |
| Production migration head | CURRENT_PROJECT_STATE.md and release/runtime evidence | Release gate; newer Production lineage never downgrades |
| Product decision | Existing product/architecture decision authority | ADR or decision document; no duplicate decision |
| Baseline failure | BASELINE_FAILURE_REGISTRY.yaml plus dated reconciliation report | Clean-base comparison and expiry/recheck |
| Incomplete artifact | INCOMPLETE_WORK_REGISTRY.md plus dated audit report | File-level mapping and owner disposition |
| Canonical integration readiness | Integration gate output and accepted canonical report | Ownership, commit, shared-surface, and test evidence |

When two sources disagree, the latest repository/runtime evidence at the
declared authority layer wins. A later report explains a transition; it does
not rewrite an earlier report's historical claim.

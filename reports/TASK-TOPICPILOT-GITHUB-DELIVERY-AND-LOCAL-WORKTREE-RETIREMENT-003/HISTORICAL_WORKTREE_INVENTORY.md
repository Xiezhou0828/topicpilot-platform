# Historical Worktree Inventory

## Inventory boundary

The prior bounded Git Recovery 002/003 inventory recorded 41 E-drive worktrees. The current E:\TopicPilot\w directory contains 42 direct worktree directories after adding `topicpilot-local-preview-canonical-delivery-002`. No unbounded disk scan was performed.

Historical source:
`E:\TopicPilot\reports\TASK-TOPICPILOT-GIT-RECOVERY-002-INCREMENTAL-BRANCH-AND-ARTIFACT-READBACK-003\FINAL_RECEIPT.md`

## Current classification

| Classification | Count | Basis |
|---|---:|---|
| ACTIVE | 1 | Existing `frontend-production-deployment-002` remains the 4317 user-visible Preview and is protected. |
| RETAIN_FOR_INTEGRATION | 1 | New `topicpilot-local-preview-canonical-delivery-002` Task Branch and its Draft PR delivery. |
| PRESERVATION_REQUIRED | 3 | Dirty C-common-dir worktrees: frontend production candidate, Stock Topic Impact, and stock-research-bootstrap. |
| RETIREMENT_READY | 0 | No item has itemized Owner retirement approval. |
| BLOCKED_UNKNOWN | 37 | Historical worktrees require current per-item status/dependency confirmation before any deletion. |
| RETIRED | 0 | No retirement operation was authorized or executed. |

Total: `42`.

The prior targeted readback found 14 tracked dirty paths in the frontend candidate, 9 tracked plus 13 untracked paths in Stock Topic Impact, 9 tracked plus 4,906 untracked paths in stock-research-bootstrap, and a bounded clean readback for tw-bb-research-integration-002. These are not deletion authorizations.

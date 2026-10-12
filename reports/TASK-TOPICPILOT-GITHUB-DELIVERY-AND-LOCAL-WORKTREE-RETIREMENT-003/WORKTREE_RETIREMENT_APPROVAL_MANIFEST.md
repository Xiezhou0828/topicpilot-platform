# Worktree Retirement Approval Manifest

No Worktree retirement is approved by this task without an Owner decision for the exact path and contents. This manifest is therefore a review queue, not an execution authorization.

| Exact path | Branch / HEAD | Preservation location | Planned operation | Restore method | Risk | Owner approval |
|---|---|---|---|---|---|---|
| `E:\TopicPilot\w\frontend-production-deployment-002` | detached / `deea8325` | C-drive shared history plus prior bounded preservation | retain; no operation | restore original checkout and preserved source | high; active 4317 Preview and dirty | NO |
| `E:\TopicPilot\w\stock-topic-impact-direction-evidence-ui-001` | detached / `b17355ea` | prior bounded preservation; additional snapshot review required | retain; no operation | restore preserved source and reports | high; untracked deliverables | NO |
| `E:\TopicPilot\w\stock-research-bootstrap-v1` | detached / `9852f03b` | prior bounded preservation; 4,906 untracked paths require classification | retain; no operation | restore source snapshot and research artifacts | critical; mixed research/bootstrap forest | NO |
| `E:\TopicPilot\w\tw-bb-research-integration-002` | detached / `76ee82c0` | E canonical-main repository; current owner not proven | retain pending review | restore from existing Git object and path | medium; cross-repository dependency unknown | NO |
| `E:\TopicPilot\w\topicpilot-local-preview-canonical-delivery-002` | `codex/topicpilot-local-preview-canonical-delivery-002` / `acdd76f` | local Git plus future remote Task Branch | retain through PR review; do not retire now | checkout remote Task Branch | low for code, active delivery dependency | NO |

The remaining 37 historical worktrees are `BLOCKED_UNKNOWN` and are not listed as deletion targets until their exact paths and dependencies are read back. No planned operation is executable under this manifest.

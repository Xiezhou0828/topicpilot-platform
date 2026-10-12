# Local Branch and Commit Recovery Matrix

| Item | Path | HEAD / branch | Common directory | Recovery disposition |
|---|---|---|---|---|
| Delivery candidate | `E:\TopicPilot\w\topicpilot-local-preview-canonical-delivery-002` | `acdd76f` / `codex/topicpilot-local-preview-canonical-delivery-002` | own E-drive `.git` | Retain through PR review; local commits remain recoverable. |
| User-visible Preview | `E:\TopicPilot\w\frontend-production-deployment-002` | `deea8325` / detached | C-drive shared `.git` | Protected; no reset, clean, removal, or branch operation. |
| Stock Topic Impact | `E:\TopicPilot\w\stock-topic-impact-direction-evidence-ui-001` | `b17355ea` / detached | C-drive shared `.git` | Preservation required; not integrated or deleted. |
| Research bootstrap | `E:\TopicPilot\w\stock-research-bootstrap-v1` | `9852f03b` / detached | C-drive shared `.git` | High-risk mixed artifact forest; preservation required. |
| Bounded clean candidate | `E:\TopicPilot\w\tw-bb-research-integration-002` | `76ee82c0` / detached | `E:\TopicPilot\canonical-main\.git` | Not proven disposable; owner decision still required. |

The remaining 37 historical worktrees are carried forward as `BLOCKED_UNKNOWN` until their current branch, common directory, local-only commits, ignored artifacts, and cross-workstream dependencies are individually read back.

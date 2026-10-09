# Canonical and runtime baseline

## Repository readback

| Item | Evidence |
|---|---|
| Current canonical branch | origin/main |
| Current canonical HEAD | fc11856... |
| Starting Task 007 SHA | 9703c956... |
| Task worktree | E:\TopicPilot\w\publication-flow-v2-production-blocker-remediation-007 |
| Task worktree branch | codex/publication-flow-v2-production-blocker-remediation-007-diag2 |
| Local diagnostic content SHA | 2513829... |
| Protected checkout | C:\Users\acer\Desktop\題材領航\topicpilot-platform |
| Protected checkout state | dirty pre-existing state, untouched |
| Preview worktree | not a verified Git worktree in the requested path; not modified |

The protected checkout was not reset, cleaned, rebased, merged, or overwritten. The Preview workstream was not inspected as clean and is not claimed as unaffected; it was left untouched.

## Scope of merged changes

PR #80, PR #82 and PR #83 changed only the Production forensic readback allowlist/implementation, its GitHub workflow schema validation, and focused tests. No migration file, frontend file, formal Topic policy, selection rule, or scheduler activation setting was changed.

Evidence:

- PR #80: https://github.com/Xiezhou0828/topicpilot-platform/pull/80
- PR #82: https://github.com/Xiezhou0828/topicpilot-platform/pull/82
- PR #83: https://github.com/Xiezhou0828/topicpilot-platform/pull/83

## Runtime divergence

Canonical main is fc11856..., while both Render Production services remain on 9703c956.... The forensic improvements are therefore not deployed. This is an explicit identity mismatch, not evidence of an unsafe deployment.

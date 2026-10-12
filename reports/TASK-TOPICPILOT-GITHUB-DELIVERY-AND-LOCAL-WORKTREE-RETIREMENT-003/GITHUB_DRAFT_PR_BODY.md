# TopicPilot Local Preview and Company Research V3 Delivery

## Task

`TASK-TOPICPILOT-GITHUB-DELIVERY-AND-LOCAL-WORKTREE-RETIREMENT-003`

## Delivery scope

This Draft PR delivers the already validated local Company Research V3 / Financial Research / EPS read-only integration from the latest GitHub Main baseline. It includes the 4317 Preview-facing research surface and the supporting fail-closed contracts for stocks 1303, 1314, and 1319.

## Boundary

- Research content remains Preview/review material; it is not a Production publication.
- Formal Topic Authority and formal stock-topic relations are unchanged.
- No database migration, Production write, deployment, or release is included.
- Stock Topic Impact and Publication Flow V2 are excluded from this PR.
- Main merge is intentionally left to Owner review.

## Evidence

- Base Main SHA: `0cf8779145f16df479a7b6cc5edb21a4c21e4d43`.
- Local candidate integration commit: `6e7276f91f747022f490d6b036c24318b053ba48`.
- Frontend: build passed; `218 passed, 0 failed`; TypeScript passed.
- Backend focused suite: `46 passed, 0 failed`.
- Ruff, OpenAPI drift, secret scan, governance gates, and Delivery Preflight passed.
- 4317 Preview read back Company Research content for 1303, 1314, and 1319.

## Known limitations

- Some research fields are explicitly unavailable or not disclosed; no missing value is fabricated.
- Preview research data is not automatically published.
- Historical Worktree cleanup is a separate approval gate and is not performed by this PR.

## Rollback

Before merge, close the Draft PR or revert the Task Branch commits. Main is unchanged by this delivery.

## Owner decisions required

- Review and approve/reject this Draft PR.
- Separately decide whether and when to merge to Main.
- Separately approve exact Worktree retirement paths, if any.

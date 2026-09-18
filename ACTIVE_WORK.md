# Active Work and Ownership

**Registry state:** `OWNER CLOSURE CANONICAL / 2026-09-16`

This is the canonical parallel-work registry. A row may be registered without
being authorized to implement product behavior. Every active row has an
isolated branch and worktree, or explicitly records why it has none.

## Owner closure checkpoint

| Task | State | Owner | Base / branch / worktree | Dependencies | Next named task / acceptance |
|---|---|---|---|---|---|
| TASK-OWNER-TOPICPILOT-CANONICAL-PROMOTION-RELEASE-AND-RUNTIME-CLOSURE-001 | INTEGRATED / HISTORICAL CLOSED / RELEASE EXTERNAL GATE | Canonical integration, release, runtime, and baseline owner | 277a49382240503fcd0767e9cfb17e2fd974e8a3; codex/task-owner-topicpilot-canonical-promotion-release-runtime-closure-001-20260916; E:\topicpilot-worktrees\owner-topicpilot-canonical-promotion-release-runtime-closure-20260916 | Exact Web/Worker provenance and operator-authorized canary | Recover exact Web/Worker readback, confirm current API/DB, then authorize governed exact-SHA release; remediate POST_CLOSE freshness separately |

## Active and recovery workstreams

| Task | State | Owner | Base / branch / worktree | Dependencies | Next named task / acceptance |
|---|---|---|---|---|---|
| `TASK-OPP-REC-002` | `BLOCKED` — formal authority absent | Product/Release Owner with formal-data authority | `a8357d46194f...`; `codex/task-opp-rec-002-formal-authority-readiness-20260913`; `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-opportunity-20260913` | Approved provider authority, effective date, formal read model, release owner | `OPP-FORMAL-AUTHORITY-READINESS-001`: produce provider/authority/readiness packet; no algorithm or publication activation |
| `TASK-TODAY-REC-002` | `IN_PROGRESS` — recovery audit only | Today FE/BE owner with integration owner | `a8357d46194f...`; `codex/task-today-rec-002-mainline-recovery-20260913`; `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-today-20260913` | Main Home contract, generated client/schema mapping, source-branch review, explicit integration approval | `TODAY-MAINLINE-RECOVERY-001`: reconcile branch-only Signals/UI/backend chain and produce bounded port list; no blind cherry-pick |
| `TASK-A10-A9-REC-002` | `BLOCKED` — operator and integration review | DATA/Live/Release owner | `a8357d46194f...`; `codex/task-a10-a9-rec-002-writer-quote-reconciliation-20260913`; `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-a10-a9-20260913` | POST_CLOSE operator readback, provider resilience evidence, migration reservation, release composition | `A10-A9-RECOVERY-RECONCILIATION-001`: map writer/quote changes and 0040 boundary; no scheduler/migration activation |
| `TASK-TOPIC-REC-002` | `BLOCKED` — structural-role authority incomplete | WS1/B2 owner | `a8357d46194f...`; `codex/task-topic-rec-002-b2-authority-recovery-20260913`; `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-topic-20260913` | Owner-reviewed effective-dated structural-role authority and approved projection input | `TOPIC-AUTHORITY-RECOVERY-001`: prepare authority readback and fail-closed acceptance; no semantic redesign or Score/Grade publication |
| `B3-INITIATION-REVIEW-001` | `LOCKED / NOT_STARTED` | Product Owner | No branch/worktree by design | B2 authority and explicit scope/owner decision | Confirm whether B3 exists in repository evidence, then issue a governed implementation packet |
| `B4-INITIATION-REVIEW-001` | `LOCKED / NOT_STARTED` | Product Owner | No branch/worktree by design | B2 authority and explicit scope/owner decision | Confirm whether B4 exists in repository evidence, then issue a governed implementation packet |
| `REL-002-OPERATOR-READBACK-001` | `BLOCKED / INDEPENDENT` | Release operator | Candidate branch `codex/rel-002-release-candidate-20260913`; clean candidate worktree retained | Protected runtime access and operator-authorized release procedure | Read exact API/Web/Worker/DB revision, migration, data, and POST_CLOSE evidence; remains independent of recovery worktrees |

## Historical or non-active lines

| Line | Evidence status | Ownership rule |
|---|---|---|
| F4-F9 | `SUPERSEDED / BRANCH_ONLY_CLOSED` | Preserve closure reports on the Today branches. Any runtime or UI reconciliation is a new owner-approved task, not a reopen of the old closure. |
| F1-F3 | `UNKNOWN` | No canonical closure evidence identified. Do not claim completion and do not implement without an owner-approved packet. |
| FUND-001 | `PROPOSED / OWNER_DECISION_REQUIRED` | Use the existing initiation packet. No branch, schema, provider, scheduler, API, frontend, or Production work is authorized. |
| Old Topic/Today/WS1/WS2/WS3 worktrees | `HISTORICAL / RETAIN` | Keep as evidence until owner disposition; never use as a new development base. |

## Ownership and write-set rules

- A recovery worktree owns only its task-scoped audit notes and later approved
  bounded changes. It does not own shared governance files until integration
  review assigns a specific hunk.
- `services/api` schemas, Alembic migrations, OpenAPI/generated clients,
  release configuration, and shared Home/Topic contracts are serial integration
  surfaces. They may be audited in parallel but are integrated one task at a
  time from a current committed base.
- Frontend-only changes can run in parallel only when their routes/assets do
  not overlap. Generated artifacts are changed only with their source contract
  and a drift check in the same governed task.
- No task may use the canonical owner checkout for development while its
  tracked/untracked state is dirty. The owner checkout remains an evidence and
  governance checkout.
- Each handoff must name the base SHA, branch, worktree, files touched,
  validation, blockers, next task, and whether any shared surface needs serial
  integration.

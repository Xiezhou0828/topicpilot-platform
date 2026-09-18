# Branch Recovery Matrix

**Matrix state:** `OWNER CLOSURE CANONICAL / 2026-09-16`

All dispositions are evidence classifications, not deletion instructions.
`Ahead/behind` values below are relative to the named base or `origin/main`.

## Owner-controlled canonical closure

| Ref | Tip / base | Relation | Disposition |
|---|---|---|---|
| codex/task-owner-topicpilot-canonical-promotion-release-runtime-closure-001-20260916 | 277a49382240503fcd0767e9cfb17e2fd974e8a3; source d6371af5994f0c2d5e0612969f100f6cef26b772 | Clean owner-controlled documentation descendant of the verified unified candidate | CANONICAL_FORWARD_BASE / HISTORICAL_CLOSURE_COMPLETE / RELEASE_EXTERNAL_GATE |

## Relevant remote and local branches

| Branch / ref | Tip SHA | Relation | Disposition |
|---|---|---|---|
| `origin/main` | `b2eaf33e0ec5...` | Canonical remote baseline | `CANONICAL_BASELINE` |
| `codex/rel-002-release-candidate-20260913` | `a8357d46194f...` | main-derived; candidate includes 2 commits over `origin/main` | `RETAIN_RELEASE_CANDIDATE / DEVELOPMENT_INTEGRATION_BASE` |
| `origin/codex/today-production-convergence-20260913` | `bf68cc8bf0a4...` | 51 ahead / 8 behind; merge-base `12b0c7c97031...` | `SOURCE_FOR_RECOVERY / DO_NOT_CONTINUE_DIRECTLY` |
| `origin/codex/today-commercial-investor-release-20260912` | `569d2b4d5f4b...` | 51 ahead / 6 behind; merge-base `12b0c7c97031...` | `SOURCE_FOR_RECOVERY / DO_NOT_CONTINUE_DIRECTLY` |
| `origin/codex/a10-a9-isolated-quote-closure-20260912` | `51dbe48db203...` | 3 ahead / 0 behind `origin/main` | `SOURCE_FOR_RECOVERY / SPLIT_REQUIRED` |
| `origin/codex/a9-b2-production-writer-closure-20260912` | `68600af6f095...` | 2 ahead / 0 behind `origin/main` | `SOURCE_FOR_RECOVERY / OPERATOR_GATED` |
| `origin/codex/a10-production-20260908` | `ce61762bd5f3...` | Ancestor/content already in main; 26/0 at historical comparison | `SUPERSEDED_BUT_RETAIN` |
| `origin/codex/a10-batch-speed-20260908` | `74226c387ff3...` | Ancestor/content already in main; 17/0 at historical comparison | `SUPERSEDED_BUT_RETAIN` |
| `origin/codex/b2-protected-topic-authority-20260911` | `a50346b9b6df...` | Ancestor/content already in main; 11/0 at historical comparison | `ALREADY_PRESENT / SUPERSEDED_BUT_RETAIN` |
| `codex/task-topic-daily-state-20260815` | `39b03b922dfa...` | Old local Topic workstream branch | `HISTORICAL_SOURCE_ONLY / RETAIN` |

The current canonical owner branch remains
`codex/task-ops-023a-p3c-runtime-sha-audit-20260813` at governance parent
`6f03372b38ef...`, with 152 pre-existing status entries. Its tracked and
untracked owner state is intentionally preserved and it is not a development
worktree. The owner-controlled closure ref above is the safe clean lineage for
forward development; it does not assert that Production serves its SHA.

## New recovery branches and worktrees

| Task | Branch | Tip/base | Worktree | Checkout state |
|---|---|---|---|---|
| Opportunity recovery | `codex/task-opp-rec-002-formal-authority-readiness-20260913` | `a8357d46194f...` / `a8357d46194f...` | `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-opportunity-20260913` | Clean task-scoped sparse worktree; 30 tracked files materialized |
| Today recovery | `codex/task-today-rec-002-mainline-recovery-20260913` | `a8357d46194f...` / `a8357d46194f...` | `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-today-20260913` | Clean task-scoped sparse worktree; 39 tracked files materialized |
| A10/A9 recovery | `codex/task-a10-a9-rec-002-writer-quote-reconciliation-20260913` | `a8357d46194f...` / `a8357d46194f...` | `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-a10-a9-20260913` | Clean task-scoped sparse worktree; 57 tracked files materialized |
| Topic recovery | `codex/task-topic-rec-002-b2-authority-recovery-20260913` | `a8357d46194f...` / `a8357d46194f...` | `C:\Users\acer\Desktop\題材領航\topicpilot-platform-recovery-topic-20260913` | Clean task-scoped sparse worktree; 117 tracked files materialized |

These worktrees are registration and isolation artifacts only. They contain no
GOV-002 product implementation commit. Sparse checkout is a disk-safety and
scope control; a task must explicitly expand its read set before relying on an
absent path as evidence of nonexistence.

## Branch-only commit disposition

| Source commit | Line | Disposition |
|---|---|---|
| `1501468da8b7...` | Today commercial investor market view | `SOURCE_FOR_RECOVERY`; broad UI/contract chain requires review |
| `c976d41f9b61...`, `dca709e5741e...` | Today mobile layout | `PORT_AFTER_UI_REVIEW`; no direct port |
| `34f16bcebed5...`, `f931593938c4...`, `0fee4390e208...` | Today persisted focus/breadth normalization | `SOURCE_FOR_RECOVERY`; bounded mapping required |
| `c544e2a5a6e3...` | Today convergence and visual parity | `CONFLICTING / SPLIT_REQUIRED`; contains broad changes and 0040 |
| `bf68cc8bf0a4...` | Today deterministic signals publication | `SOURCE_FOR_RECOVERY`; generated contract and prior chain must be mapped |
| `17523a8c8043...` | A10/A9 formal writers and release wiring | `CONFLICTING / SPLIT_REQUIRED` |
| `68600af6f095...` | A9/B2 13:35 POST_CLOSE trigger | `SOURCE_FOR_RECOVERY / OPERATOR_GATED` |
| `51dbe48db203...` | Isolated quote publication and 0040 | `SOURCE_FOR_RECOVERY / SPLIT_REQUIRED`; migration `0040` is `DO_NOT_PORT_NOW` |

No old branch is deleted, force-rebased, or force-pushed by GOV-002.

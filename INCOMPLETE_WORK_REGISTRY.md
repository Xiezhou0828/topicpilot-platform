# Incomplete Work Registry
does not establish liveness or completion. They remain `UNKNOWN`, `PARTIAL`, or
`SUPERSEDED` until a file-level owner maps each item to a current consumer and
runtime contract. Cleanup is a later, explicitly approved task; GOV-002 does
not delete, rename, or rewrite any of them.
**Registry state:** `OWNER CLOSURE CANONICAL / 2026-09-16`

This registry prevents unfinished code, branch-only closure, and missing
runtime proof from being mistaken for completed product capability. No item is
marked `ABANDONED` merely because it is old; abandonment requires an explicit
owner or repository disposition.

## Current owner closure overlay — 2026-09-16

The following is the current owner-controlled classification for the recovered
historical scope and supersedes older row descriptions where newer evidence is
explicitly named. Historical recovery is CLOSED and canonical lineage is
VERIFIED; remaining entries are normal forward work or external release/runtime
dependencies, not unidentified historical implementations.

| Scope | Current classification | Evidence boundary / next action |
|---|---|---|
| Historical implementations and provenance | CLOSED / VERIFIED | Unified candidate d6371af5994f0c2d5e0612969f100f6cef26b772 and owner closure baseline 277a49382240503fcd0767e9cfb17e2fd974e8a3 reconciled; no unknown historical implementation remains in task scope |
| Production release provenance | PARTIAL / BLOCKED_PROVENANCE | API exact bf68cc8bf0a4432d7623db43f42e9219c94d7b6b and DB revision 0040 verified by readback; exact Web/Worker SHA unavailable; release owner readback required |
| Production canary | NOT_AUTHORIZED | No deploy or canary was authorized; do not infer release from branch or opaque Web deployment id |
| POST_CLOSE data pipeline | FAIL / PARTIAL | Latest 2026-09-15 POST_CLOSE reported FAILED, EXCHANGE_NO_DATA, 0 success, 347 failures, 206 skipped; forward provider/freshness remediation required |
| Formal Opportunity | BLOCKED | Formal route absent in current readback; shadow route remains non-formal; formal input and daily recommendation are not ready |
| Repository hygiene | OWNER_CONTROLLED | Dirty owner checkout is preserved exactly; disposition is separate and no cleanup is authorized by this closure |

| Item | Status | Evidence / last known commit | Why it is incomplete | Safe next action |
|---|---|---|---|---|
| Formal Opportunity provider/public API | `BLOCKED` | Candidate contract `da9383614c2f...`, integrated candidate `a8357d46194f...`; runtime shadow only | No configured formal provider; `/api/v2/opportunities` was 404; publication and data authority are absent | Run `OPP-FORMAL-AUTHORITY-READINESS-001` in isolated recovery worktree |
| Today Market Signals production convergence | `PARTIAL` | Runtime `bf68cc8...`; branch-only chain includes `bf68cc8...` and prior Today commits | Runtime is on a diverged branch; source-to-canonical mapping and formal data completeness are unresolved | Run `TODAY-MAINLINE-RECOVERY-001`; do not port broad release commit blindly |
| A10/A9 writer and isolated quote path | `PARTIAL / BLOCKED` | `51dbe48db203...`, `68600af6f095...`, `17523a8c8043...` | Branch-only writer/quote/release changes, POST_CLOSE partial, operator readback absent, migration 0040 requires reservation | Run `A10-A9-RECOVERY-RECONCILIATION-001`; keep 0040 out of integration |
| A10 migration `0040_task_a10_recovery_checkpoint_observability` | `SUPERSEDED_FOR_CURRENT_BASE / RETAIN` | Present in branch-only history and some broad Today/A10 commits | It is not part of the candidate migration line and may conflict with current migration composition | Audit migration intent and dependency before any separately approved migration task |
| Topic Lifecycle derived publication | `BLOCKED` | Mainline Topic/B2 contracts through migration 0039; runtime readback 2026-09-09 | Structural-role authority is incomplete; Lifecycle/Score/Grade/ranking are deferred or fail-closed | Run `TOPIC-AUTHORITY-RECOVERY-001`; do not redesign Topic semantics |
| B3 | `UNKNOWN / NOT_STARTED` | No implementation or branch evidence found in GOV-001/GOV-002 scan | Scope and authoritative acceptance criteria are absent | `B3-INITIATION-REVIEW-001` only |
| B4 | `UNKNOWN / NOT_STARTED` | No implementation or branch evidence found in GOV-001/GOV-002 scan | Scope and authoritative acceptance criteria are absent | `B4-INITIATION-REVIEW-001` only |
| F1-F3 | `UNKNOWN` | No canonical closure file or equivalent mainline evidence identified | Chat/history hints are not repo truth | Owner decision and evidence search before any reopen |
| F4-F9 | `SUPERSEDED / BRANCH_ONLY_CLOSED` | Closure reports exist on Today branches, including `569d2b4...` branch history | Closure evidence is not in current `origin/main`; later branch/runtime changes require reconciliation | Preserve history; create a new post-closure reconciliation task only if Owner requests |
| FUND-001 institution flow | `PROPOSED / OWNER_DECISION_REQUIRED` | `docs/work-orders/FUND-001-INSTITUTION-FLOW-INITIATION-PACKET-20260913.md` | Formal source authority, PIT contract, provider, persistence, consumer, and release gates are unapproved | Obtain Owner decision; no code branch |
| API/Web/Worker/DB exact release provenance | `BLOCKED` | REL-002 candidate `a8357d...`; API runtime `bf68cc8...`; Web opaque deployment version | Web/Worker exact SHA and protected DB revision are not readable; API differs from candidate | Keep `REL-002-OPERATOR-READBACK-001` independent |
| POST_CLOSE data pipeline | `PARTIAL` | Runtime latest run: 552 requested, 347 success, 205 failure, 240 retry | Provider request failures and full-universe freshness are unresolved | Operator/provider evidence and bounded recovery task; no scheduler activation |
| Repository hygiene debt | `IN_PROGRESS / OWNER_CONTROLLED` | Canonical owner checkout at GOV-002 start: 1 tracked modification and 151 untracked entries; no staged entries | Owner changes and historical artifacts are unattributed to this task | Preserve exactly; disposition separately, never blanket-clean |

## Orphan, dead, legacy, mock, and placeholder inventory rule

The archaeology scan found candidates across legacy/V1 routes, branch-only
fixtures, generated artifacts, mock/synthetic data, and partially wired UI
surfaces (including Header, AI Research, Search, and Account). Their presence
does not establish liveness or completion. They remain `UNKNOWN`, `PARTIAL`, or
`SUPERSEDED` until a file-level owner maps each item to a current consumer and
runtime contract. Cleanup is a later, explicitly approved task; GOV-002 does
not delete, rename, or rewrite any of them.

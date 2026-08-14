# TASK-DOC-OPPORTUNITY-001｜Opportunity Engine Strategy Authority Documentation Report

**Scope:** documentation-only authority consolidation.

**Audit base:** `origin/main` at
`8a818935fe63eb3c3db9592c5068363c7ec941e9` after reconciliation onto the
latest `origin/main`.

**Final status:** `READY_FOR_OPPORTUNITY_DOCUMENTATION_REVIEW`

## Authority decision

An existing canonical authority was found and updated:

- **Authority entry:** `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md`
- **Action:** `UPDATED_EXISTING`; no duplicate Opportunity strategy authority
  was created.
- **Supporting index:** `docs/DOCUMENTATION_AUTHORITY_INDEX.md` was created
  because that authority map was absent on the audited `origin/main`.
- **Repository entry point:** `docs/DOCUMENTATION_INDEX.md` now links both
  authority files.

The repository authority takes precedence over the attached task prompt when a
release or operational claim differs. In particular, the repository is now at
`8a818935…`, while earlier deployment/runtime reports refer to earlier exact
release SHAs. This report does not promote those earlier runtime claims to the
current audit SHA.

## Strategy authority result

| Requirement | Current documented result |
|---|---|
| A: Trend Continuation | V1 shadow implemented; independent strategy-local ranking |
| B: Catch-up Opportunity | V1 shadow implemented; independent strategy-local ranking |
| Catch-up Window | Defined as policy-controlled relative-performance window; numeric values remain provisional/tunable |
| Lag + Inflection | Defined as relative lag plus stabilizing/improving relative strength; no new numeric rule added |
| Momentum Strength vs Extension Risk | Separate evidence dimensions; extension cannot bypass gates |
| C: Early Strength | Roadmap / `FUTURE_NOT_IMPLEMENTED`; no detailed rules invented |
| D: Pullback Acceptance | Roadmap / `FUTURE_NOT_IMPLEMENTED`; no detailed rules invented |
| Score | Setup-quality/ranking metadata; `SCORE_IS_PROBABILITY=NO` |
| Confidence | Separate evidence sufficiency/reliability basis; not score-derived and not probability |
| Opportunity vs Recommendation | Separate boundary; Opportunity is not Buy/Sell or trading authorization |
| Policy versioning | `topic-opportunity-policy.provisional.1`; numeric parameters remain provisional/tunable/versioned |
| Evidence provider model | Provider-neutral extension model with lineage, as-of, freshness, availability, and stable codes |
| Fibonacci | Roadmap candidate evidence for D only; no implementation, threshold, or approved D rule |

## Current State Snapshot

This is a documentation audit snapshot, not a claim that the audited commit is
deployed. Earlier runtime/CI evidence is retained with its original exact
release SHA and is not projected onto `8a818935…`.

| Field | Current documented value |
|---|---|
| `CURRENT_RELEASE_SHA` | `8a818935fe63eb3c3db9592c5068363c7ec941e9` |
| `GITHUB_CI` | `NOT_REASSERTED_FOR_AUDIT_SHA` |
| `RENDER_DEPLOYED_SHA/EVIDENCE` | `NOT_REASSERTED_FOR_AUDIT_SHA` |
| `RUNTIME_SHA_VERIFIED` | `NOT_CURRENTLY_CERTIFIED_FOR_AUDIT_SHA`; prior exact-SHA evidence preserved |
| `DAILY_MARKET/REFERENCE_DATA` | Latest recorded baseline `2 markets / 0 instruments / NOT_READY`; not rechecked for audit SHA |
| `G0/G1/G2/G3` | Prior G0 evidence `PASS` but not reasserted; G1 `FAIL / NOT_REACHED`; G2/G3 `NOT_RUN` |
| `CANARY` | Canary #2 `NOT_RUN` |
| `DOWNSTREAM_READY` | `NO / NOT_CERTIFIED` |
| `TOPIC_SNAPSHOT` | `NOT_RUN / NOT_CERTIFIED` |
| `LIFECYCLE` | `NOT_RUN / production activation not authorized` |
| `OPPORTUNITY` | `SHADOW_ONLY`; production publication not authorized |
| `FRONTEND_REAL_DATA` | `NOT_CERTIFIED` for Opportunity production data |
| `INTRADAY_DATA` | `NOT_CERTIFIED` by this task |
| `SCHEDULER` | `NOT_AUTHORIZED / UNCHANGED` |
| `DATA_GOVERNANCE` | Existing HOLD preserved; not modified |
| `CURRENT_BLOCKER` | `tw-reference-v1` Production reference infrastructure / market-identity reconciliation before G1 |
| `ACTIVE_WORK_IN_PROGRESS` | This documentation branch; DATA-REF reference work continues separately |
| `NEXT_APPROVED_GATE` | Review and reconcile this documentation-only package |

## Documentation updates

- Updated the existing Opportunity Engine specification with the consolidated
  taxonomy and semantic boundaries.
- Created the repository-wide documentation authority index and supersession
  map.
- Added the authority links to `docs/DOCUMENTATION_INDEX.md`.
- Appended the task record to `docs/AI_WORKLOG.md`; the worklog remains
  append-only.
- No historical report was deleted or rewritten.
- `CURRENT_HANDOFF_MODIFIED=NO`: no current handoff exists on the audited
  `origin/main`, and no unverified operational handoff was synthesized.
- `NEXT_TASK_MODIFIED=NO`.
- `NON_DOC_FILES_CHANGED=NO`.

## Operational boundary

This task did not run or authorize production operations. The current
documentation package does not certify a deployed runtime for the audit SHA,
does not re-certify G0, and records G1 as not reached/failed in the latest
repository baseline. G2/G3, Canary #2, Scheduler, Topic Snapshot, Lifecycle,
and Opportunity production publication remain outside this task and are not
written as completed.

`TASK-DATA-REF-001` and related reference remediation continue separately in
another worktree. No incomplete reference bootstrap result was recorded as a
current Opportunity or production fact.

## Validation handoff

Required before commit handoff:

- Markdown/link/path sanity: run against changed documentation and referenced
  local paths.
- Duplicate-authority audit: confirm the existing Opportunity specification is
  the sole strategy authority and the new index is only a navigation map.
- Secret-pattern scan: no deploy hook, database URL, token, or credential may
  appear in the documentation diff.
- `git diff --check`.
- Confirm changed paths are documentation only.

No push, merge, deploy, production database mutation, Scheduler action, or
Canary action is part of this task.

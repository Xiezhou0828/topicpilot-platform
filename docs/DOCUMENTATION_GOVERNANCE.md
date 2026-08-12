# TopicPilot Documentation Governance

**Status:** `CANONICAL / DOCUMENT LIFECYCLE POLICY`
**Effective:** 2026-08-10

## Authority hierarchy

1. Explicit PM-approved product contracts and decision records.
2. Canonical architecture, data contract, source strategy, API, frontend design, operations, and product documents listed in [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
3. Current roadmap/status and active work orders.
4. Reports, task prompts, worklogs, screenshots, and validation artifacts as historical evidence.
5. Chat messages and uncommitted drafts are context only.

If documents conflict, record the conflict and point to the higher authority. Do not silently rewrite history.

## Canonical versus historical

Canonical documents answer “what is current?” and have an owner, status, date, and source links. Historical evidence answers “what happened and what proved it?” Completed task prompts, implementation/acceptance reports, old phase plans, superseded drafts, and repeated runtime evidence are historical even when technically useful.

## Lifecycle

`DRAFT` -> `REVIEW` -> `ACCEPTED`/`COMMITTED` -> `SUPERSEDED` or `ARCHIVED`. `REJECTED` is retained when the rejection is useful evidence. A work order does not become canonical merely because it was completed.

## Archive rules

- Keep completed work orders in `docs/work-orders/` while they are actively referenced; later, archive by year/month only after inbound links are updated.
- Keep reports in `docs/reports/`; future completed-report batches may use `docs/reports/archive/<year>/<month>/`.
- Put old planning documents in `docs/archive/` only after checking links and adding a superseded pointer.
- Never delete solely for neatness. `DELETE_CANDIDATE` is a review recommendation, not an instruction.
- Do not change evidence content except for a clearly labelled archive/superseded header.

## Worklog rule

Long-term worklog entries contain Date/Task ID, Outcome, Key verification, Canonical docs affected, Evidence pointer, and Remaining issues. Full prompts and raw evidence stay in their original task/report files or a historical worklog archive. This repository currently has no `AI/AI_WORKLOG.md`; create it only when an active worklog owner and source are identified.

## Safe cleanup protocol

Before moving a file: inventory exact path, search inbound links, classify role, choose destination, move with Git-visible history, update links, and verify links. When the worktree is already heavily modified or file role is uncertain, leave the file in place and record the recommended action in the cleanup report.

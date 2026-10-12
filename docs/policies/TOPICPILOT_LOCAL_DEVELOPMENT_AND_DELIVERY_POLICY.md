# TopicPilot Local Development and Delivery Policy

Status: governed local-development policy for Task Branches

## Purpose

TopicPilot development is local-preview-first. Engineers may iterate locally for as long as needed, preserve recoverable checkpoints, and perform GitHub delivery only after a separately reviewed delivery gate. Local success never authorizes Production release.

## Local development stage

- Work on a named `codex/*` Task Branch; do not use Detached HEAD as a long-lived development state.
- Dirty worktrees are allowed during normal iteration.
- A change does not require a Commit, Push, PR, or Deploy after every edit.
- Local Preview may be restarted and updated repeatedly without GitHub or Production access.
- Preview fixtures, formal API data, Financial API data, and Research Read Model data must remain explicitly separated.
- Before a high-risk operation, create a checkpoint using a local commit or a bounded preservation snapshot with a manifest and hashes.
- The Development Preflight reports the observable branch, common directory, dirty paths, preview origins, research mode, and any unpreserved high-risk warning.

## Checkpoint stage

A checkpoint makes work recoverable; it is not Canonicalized and is not a GitHub delivery. A checkpoint must identify the exact files, commit or snapshot identity, and validation state. Historical dirty worktrees are preserved in place and are never cleaned to make a gate pass.

## Feature delivery stage

When a feature reaches an acceptance milestone:

1. classify the complete source inventory;
2. verify preservation and source mapping;
3. run the required build, type, unit, API, governance, generated-artifact, and secrets checks;
4. create one or more meaningful local commits organized by feature boundary;
5. run Delivery Preflight on the clean committed Task Branch;
6. prepare Push/PR information without performing remote writes unless separately authorized.

Delivery Preflight is distinct from Development Preflight. It requires a clean worktree, complete inventory, preservation evidence, passing validation, secrets scan, generated-artifact check, source mapping, and a source SHA matching `HEAD`. Dirty status is a Delivery blocker, not a normal development error.

## Status vocabulary

`IMPLEMENTED_LOCAL` means code exists in the Task Branch.

`LOCAL_PREVIEW_VALIDATED` means the isolated Preview and required local tests passed.

`LOCAL_CHECKPOINTED` means the current milestone is recoverable by a local commit or bounded snapshot.

`COMMITTED_LOCAL` means the Task Branch has a local commit with no unclassified changes.

`DELIVERY_READY` means Delivery Preflight passed. It does not mean pushed or merged.

`PUSHED_BRANCH`, `PR_OPEN`, and `CI_VALIDATED` are remote delivery states and require explicit authorization and receipts.

`CANONICALIZED` means the Owner-approved canonical integration completed.

`PRODUCTION_RELEASED` requires an independent Release Authority and Owner approval.

No single `COMPLETE` label may collapse these states.

## Authority boundaries

- Local Preview, local commits, and local reports do not publish research or mutate Formal Topic Authority.
- Research publication and Formal Topic acceptance remain separate decisions.
- Main merge, Production migration, Production database writes, deployment, and schedule changes require their own authorization.
- C-drive Owner Checkout and pre-existing dirty or detached worktrees are read-only inputs for reconciliation; they are not delivery targets.

## Required receipts

Each delivery candidate should retain the baseline/main SHA readback, source inventory, mapping and conflict report, Preview/API readback, test report, commit receipt, remote-readiness report, and Owner next-action decision.

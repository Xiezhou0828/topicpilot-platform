# Preservation and Restore Validation

## Current delivery scope

The One-Shot 002 preservation marker remains valid at:
`E:\TopicPilot\preservation\TASK-TOPICPILOT-LOCAL-PREVIEW-AND-CANONICAL-DELIVERY-CLOSURE-002-BOUNDED\PRESERVATION_VERIFIED`

Recorded result: 61 rows, 59 copied, 2 explicitly skipped, 0 missing, 0 mismatched.

The current delivery repository has its own `.git` directory and a clean local Task Branch. The integrated commit and receipt commits are recoverable from the local branch and, after push, the remote Task Branch.

## Historical worktrees

The older One-Shot 001 preservation has two known source-content mismatches caused by later source drift and was not overwritten. The three C-common-dir dirty worktrees remain in place and are not candidates for deletion. Their preservation obligations are carried forward as `PRESERVATION_REQUIRED`.

## Restore procedure

1. Restore the remote/local Task Branch at its recorded SHA.
2. Restore the bounded E-drive preservation snapshot if source review requires it.
3. Keep C-drive shared Git metadata untouched.
4. Re-run source and hash validation before any future retirement operation.

`PRESERVATION_VERIFIED=YES_FOR_CURRENT_DELIVERY_SCOPE`
`HISTORICAL_RETIREMENT_RESTORE_VALIDATION=BLOCKED_UNTIL_ITEMIZED_OWNER_REVIEW`

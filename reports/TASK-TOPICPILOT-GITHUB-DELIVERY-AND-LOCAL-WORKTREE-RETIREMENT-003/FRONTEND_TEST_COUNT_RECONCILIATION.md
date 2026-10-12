# Frontend Test Count Reconciliation

`TEST_COUNT_RECONCILIATION=PASS_WITH_HISTORICAL_BASELINE_DIFFERENCE_DOCUMENTED`

## Current Main-derived candidate

- Latest Main contains 40 frontend test files.
- The Task Branch contains those same Main test files plus 3 research tests:
  - `financial-research-preview-contract.test.mjs`
  - `stock-research-ui.test.mjs`
  - `stock-topic-evidence-story.test.mjs`
- No existing Main frontend test file was deleted or renamed by this candidate.
- Current authoritative run: `npm test` completed with `218 passed, 0 failed`.
- TypeScript check: `npx tsc --noEmit` passed.

## Why the historical number was 227

The prior `227 passed` result came from the dirty C-common-dir frontend candidate at `deea8325bb63c58e6e6c1f3625df155ca6dde218`, not from the latest GitHub Main-derived clean Task Branch. That prior worktree contained seven older UI test files absent from current Main and one additional `stock-sidebar-research-contract.test.mjs` outside this closure's approved scope. The current branch intentionally did not copy those non-canonical dirty-worktree tests.

Therefore, the difference is explained by Main-baseline and scope-set changes, not an accidental deletion from current Main. The current 218-result is the correct delivery baseline for this branch.

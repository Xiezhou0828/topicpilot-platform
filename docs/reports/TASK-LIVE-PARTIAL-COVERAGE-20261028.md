# 2026-10-28 Limited Coverage Recovery

```text
TASK_ID=TASK-LIVE-PARTIAL-COVERAGE-20261028
TASK_TYPE=release
REQUIRED_TERMINAL_STATE=POST_DEPLOY_VERIFIED
AUTHORITY_BOUNDARY=Owner authorized canonical promotion, deployment of the API/Worker and relevant stock UI, and a one-time formal history recovery limited to 2026-10-28; no schema migration, scheduler change, or secret/configuration mutation.
CANONICAL_SHA=PENDING
SOURCE_SHA=cf9b7e46dda796e53439e79a7e6cdfecb60fa143
MIGRATION_HEAD=0050_task_purge_retired_topics (Production API readback, 2026-10-29 Asia/Taipei)
FILES_CHANGED=See git change list and work-order register entry.
SEMANTICS_CHANGED=An official TPEx row with null OHLC and zero volume is explicit NO_TRADE; 1-9 individually identified quote gaps may continue with visible per-instrument disclosure. No prices or volume are synthesized.
PRODUCTION_DEPENDENCY=Deploy the validated exact SHA; run the existing one-shot history recovery for 2026-10-28; verify append-only receipt and formal readbacks.
FOLLOW_UP_REQUIRED=YES — exact production revision is newer than canonical main and on a divergent unmerged lineage; preserve and reconcile that lineage before releasing.
WORKTREE_STATUS=Isolated worktree C:\Users\acer\Desktop\題材領航\task-live-partial-coverage-20261028; canonical shared checkout untouched.
```

## Starting production evidence

Read-only API evidence on 2026-10-29 Asia/Taipei:

- `/healthz` and `/readyz` reported runtime SHA `2fd2f28cfa8911fddfabf5e5b6cca5aab335e81d`.
- Production migration head is `0050_task_purge_retired_topics`.
- The 2026-10-28 formal receipt is revision 4, `DEADLINE_EXCEEDED`, with 553 expected, 552 priced and covered, and one unexplained gap. TWSE is complete at 347/347; TPEx has 205/206, with 3191 雲嘉南 as the lone `MISSING_MARKET_DATA` item.
- The exact deployed API SHA is two commits ahead of and two commits divergent from canonical `main`; the associated branch is not merged. Do not release an older SHA over that live code.
- Owner confirmed 3191 is an active instrument with zero trading volume and no traded price on 2026-10-28. Preserve null price/volume and publish its explicit no-trade state only when official source evidence supports it.

## Implementation and validation

- Coverage reconciliation accepts no more than nine individually identified quote gaps only when all market totals reconcile, the gaps carry allowed per-instrument reasons, and no hard provider/date/duplicate/closed-market/empty-universe failure exists. Ten or more remain blocked.
- Offline target-universe diagnostics remain strict; the limited tolerance is for the formal production daily publication path.
- Successful tolerated runs preserve raw failure/skip counters while allowing downstream formal readbacks, and do not invent a `NO_TRADING_DAY_DATA` state for tolerated gaps.
- Stock surfaces distinguish `NO_TRADE` from `UNAVAILABLE` with Traditional Chinese labels.
- Backend suite: 1,467 passed, 79 skipped because the PostgreSQL integration test database is not configured. Frontend production build and 206 tests passed. Ruff, TypeScript, lint, and whitespace checks passed; lint emitted one pre-existing `FavoriteButton.tsx` hook-dependency warning.

## Promotion and recovery ledger

Pending canonical promotion, exact-SHA deployment/readback, the one-time 2026-10-28 history recovery, and formal receipt verification. This report must be updated with the final deployed SHA, workflow and deployment evidence, recovery run identity, coverage totals, 3191 status, and receipt/readback result before the task can claim `POST_DEPLOY_VERIFIED`.

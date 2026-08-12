# TASK-REPO-003 — TopicPilot V2 Selective Staging & Release Commits

Date: 2026-08-13
Repository: `topicpilot-platform`
Branch: `main`
Starting HEAD: `e333ed3`
Final release HEAD: `a0eaa3b`

## Scope and safety boundary

This task performed explicit-path staging and local commits only. No blanket
`git add .`, `git add -A`, or `git add --all` was used. No push, force-push,
reset, clean, rebase, amend of `e333ed3`, deployment, production canary,
Neon write, scheduler activation, migration, or `NEXT_TASK` modification was
performed.

The research/data-governance hold remained unstaged throughout:

- `reports/TASK-BE-006/**`
- `fixtures/research/**`
- `docs/research/**`
- `docs/reports/TASK-BE-006_DATA_COLLECTION_GO_LIVE_PREPARATION_REPORT.md`
- other evidence containing real issuer identifiers, market research data, or
  source/licensing references

## Release commit sequence

| Commit | Hash | Scope | Result |
|---|---|---|---|
| 1 | `c9b3356` | `chore(repo): establish V2 release hygiene and documentation governance` | Created |
| 2 | `2e256ef` | `feat(market-data): complete FIX01A official daily provider adapter-v2` | Created |
| 3 | `b1e4e8e` | `ops(deploy): add adapter-v2 provenance and production preflight` | Created |
| 4 | `77dfd08` | `feat(opportunity): add BE-024 through BE-024C shadow decision pipeline` | Created |
| 5 | `a0eaa3b` | `feat(frontend): integrate V2 topic lifecycle and completed UI surfaces` | Created |

### Commit 1 — Repository / Governance

Explicitly staged `.gitignore`, `AGENTS.md`, `README.md`, `PROJECT_CONTEXT.md`,
governance/index/roadmap/work-order documents, Daily Progress, the AI worklog,
and the TASK-REPO-001 hygiene report. Four visible `??` encoding remnants in
historical headings were normalized to standard em dashes before staging.

### Commit 2 — Daily Market / FIX01A

Explicitly staged the official TWSE/TPEx adapter-v2 implementation, registry,
post-close market-batch wiring, no-trade contract tests, DATA-022/FIX01A
reports, and the shared API guide. Provider authority, no-data semantics, and
historical fallback boundaries were preserved.

### Commit 3 — OPS / P3A

Explicitly staged provider-lineage and reference-check CLIs, deployment
preflight tests, package entry points, Compose/CI health and rollback checks,
deployment/data-architecture docs, and OPS-023A P2/P3A reports. The staged
deployment material is operator handoff only; it does not deploy or activate
anything.

The secret sanity scan matched only test/local placeholders and standard
GitHub secret references (`POSTGRES_PASSWORD` test defaults, an empty local
Taishin password fallback, and `GITHUB_TOKEN` expression). No credential value
was present.

### Commit 4 — Opportunity BE-024 through BE-024C

Explicitly staged the shadow-only Opportunity contract, qualification policy,
strategy layer, read service/API, typed schemas/router exports, frontend
adapter, focused tests, API/architecture/product documents, and BE-024 through
BE-024C evidence reports. The commit preserves read-only/shadow semantics,
strategy-local ranking, presentation caps, and no BUY/SELL or production
activation behavior.

### Commit 5 — Lifecycle + V2 Frontend

Explicitly staged the V2 `TopicListPage` integration, REPO-002 migrated frontend
tests, V2 frontend specification changes, approved frontend foundation/release
reports, Favorites evidence, and 12 reviewed UI screenshots. Screenshot review
found app viewport captures only: no browser chrome, URL, token, or credential
was visible. No frontend production source beyond the approved V2 surface was
reverted or weakened.

## Validation

| Check | Result |
|---|---|
| Frontend `npm test` | PASS — build complete; 72 passed, 0 failed, 0 skipped |
| Frontend production build | PASS |
| TypeScript `npx tsc --noEmit` | PASS |
| Frontend lint | PASS — 1 existing unused-variable warning in `TopicDetailPage.tsx` |
| Focused backend contracts | PASS — 34 passed |
| Full backend suite | PASS — 362 passed, 31 skipped because PostgreSQL test DB variables were unavailable |
| `git diff --check` | PASS |
| Per-commit staged diff checks | PASS |
| Per-commit secret sanity | PASS; P3A placeholders/references reviewed above |
| Destructive staged changes | None — no delete or rename in any release commit |

## Cross-cutting and deferred worktree

After Commit 5, no paths were staged. The remaining worktree has three tracked
documentation modifications and 130 untracked entries, all intentionally
outside the five release boundaries. They include the broader architecture
book, Phase 2/3 work orders, research evidence, TASK-BE-006 collection/go-live
materials, and deferred screenshots/reports. They require separate review and
must not be swept into a release with blanket staging.

`NEXT_TASK` was checked and remains unmodified.

## Final flags

```text
TASK_REPO_003 = COMPLETE
STARTING_BRANCH = main
STARTING_HEAD = e333ed3
FINAL_HEAD = a0eaa3b
COMMIT_1 = c9b3356 / chore(repo): establish V2 release hygiene and documentation governance
COMMIT_2 = 2e256ef / feat(market-data): complete FIX01A official daily provider adapter-v2
COMMIT_3 = b1e4e8e / ops(deploy): add adapter-v2 provenance and production preflight
COMMIT_4 = 77dfd08 / feat(opportunity): add BE-024 through BE-024C shadow decision pipeline
COMMIT_5 = a0eaa3b / feat(frontend): integrate V2 topic lifecycle and completed UI surfaces
REPORT_COMMIT = dbbd676 / docs(repo): record V2 selective release commit report
SELECTIVE_STAGING = PASS
BLANKET_GIT_ADD = NO
DATA_GOVERNANCE_FILES_STAGED = NO
SECRET_SCAN = PASS
GIT_DIFF_CHECK = PASS
BACKEND_FOCUSED_TESTS = 34 PASSED
BACKEND_FULL_TESTS = 362 PASSED / 31 SKIPPED
FRONTEND_TESTS = 72 PASSED / 0 FAILED
FRONTEND_BUILD = PASS
TYPECHECK = PASS
LINT = PASS (one existing warning)
DAILY_MARKET_RELEASE_COMMITTED = YES
OPS_P3A_RELEASE_COMMITTED = YES
OPPORTUNITY_RELEASE_COMMITTED = YES
LIFECYCLE_FRONTEND_RELEASE_COMMITTED = YES
REPO_HYGIENE_COMMITTED = YES
REMAINING_WORKTREE = REVIEW_REQUIRED / DATA_GOVERNANCE_HOLD
DATA_GOVERNANCE_GATE = DEFERRED_FROM_THIS_RELEASE
GIT_PUSH_PERFORMED = NO
PRODUCTION_DEPLOYMENT = NO
PRODUCTION_CANARY = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
LOCAL_RELEASE_COMMITS_READY = YES
```

Recommended next operator step: inspect the five local commits and the
remaining governance/research hold, then separately authorize any future push,
deployment, reference verification, or Canary #2 work. Those actions are not
part of TASK-REPO-003.

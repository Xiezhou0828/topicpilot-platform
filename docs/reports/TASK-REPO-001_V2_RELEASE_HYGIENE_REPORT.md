# TASK-REPO-001 — TopicPilot V2 Release Hygiene Report

Date: 2026-08-12
Repository: `topicpilot-platform`
Branch: `main`
HEAD: `e333ed3`

## Scope and safety boundary

This report covers repository hygiene and commit preparation only. No `git add`,
commit, push, clean, reset, checkout, deployment, production canary, scheduler
activation, database write, business-rule change, or `NEXT_TASK` modification
was performed.

## Hygiene actions completed

- Added `work/` and `*.tsbuildinfo` to `.gitignore`.
- Confirmed `.venv-live/` remains ignored.
- Removed the clearly accidental root-level file:
  `-files --others --exclude-standard  Measure-Object`.
- Repaired the import-block formatting in
  `infra/scripts/phase3_6_001b_legacy_import.py` without changing runtime or
  migration behavior.

The exact accidental filename was verified absent after removal. No source,
documentation, fixture, test, report, or deployment file was deleted.

## Inventory after hygiene

At the inventory checkpoint after the hygiene edits (before adding this report):

- Tracked modifications: 27
- Untracked files visible to Git: 199
- Ignored local work directory: yes
- Ignored TypeScript incremental cache: yes
- Ignored `.venv-live/`: yes

The report itself is an intentional new documentation artifact and is not
included in the preceding count.

## Validation evidence

| Check | Result |
|---|---|
| `git diff --check` | PASS |
| Targeted Ruff for `infra/scripts/phase3_6_001b_legacy_import.py` | PASS |
| Full backend tests | 362 passed, 31 skipped (PostgreSQL unavailable) |
| Backend focused release tests | 74 passed |
| Frontend production build | PASS |
| Frontend tests | 59 passed, 13 failed |
| Secret/credential pattern scan | No explicit secret value found |

The 13 frontend failures are concentrated in source-shape and Home/workspace
expectations that still inspect pre-router page source while the current UI
routes through `V2Page`, plus related market/strategy copy expectations. They
must be classified as either test migration debt or a real regression before a
frontend release commit is declared ready.

Full-repository Ruff still reports historical debt. The only newly identified
change-scope Ruff issue was the import-order issue repaired above; targeted Ruff
now passes.

## Release inventory

### RELEASE_INCLUDE

- Daily Market / TASK-DATA-022 / FIX01A provider adapter changes, focused tests,
  and the corresponding report.
- Adapter-v2 lineage, reference preflight CLI/tests, and OPS-023A-P3A operator
  handoff documentation.
- Opportunity BE-024 through BE-024C contract, qualification, strategy,
  shadow-read API, frontend adapter, tests, and reports.
- Existing Lifecycle engine/read-model integration and its tests, subject to
  the frontend gate below.
- V2 source, tests, architecture, product, governance, work-order, and formal
  report documents that are not listed under review.
- Existing UI evidence images under `docs/reports/` when manually checked for
  public-safe content.

### LOCAL_IGNORE

- `work/` (temporary build bundles, tarballs, logs, research scratch output,
  and caches).
- `*.tsbuildinfo`, `.venv-live/`, `__pycache__/`, test caches, and runtime logs.

### DELETE_CANDIDATE

- The accidental root-level `-files --others --exclude-standard  Measure-Object`
  file was removed after exact-path verification.

### DATA_GOVERNANCE_REVIEW

These files are not automatically rejected, but require human confirmation of
public-data policy and licensing before staging:

- `reports/TASK-BE-006/`
- `fixtures/research/leader_set_candidates.v2.csv`
- `fixtures/research/leader_set_candidate_pool.v1.csv`
- `fixtures/research/topic_universe_mapping.v1.csv`
- Other research CSV/JSON containing real issuer identifiers or source URLs.

### FRONTEND_GATE

The V2 frontend build is successful, but the full frontend test suite remains
`59 PASSED / 13 FAILED`. The frontend release group is therefore
`REVIEW_REQUIRED` and should not be represented as fully verified.

### SECRET_RISK

The scan found no explicit API key, password, bearer token, private key, or
credential-bearing database URL in the changed file set. `.env` is not tracked;
`.env.example` is the tracked template. Research data and deployment references
remain governance concerns, not confirmed credential leakage.

## Proposed commit boundaries

1. `chore(repo): establish V2 release hygiene and documentation governance`
2. `feat(market-data): complete FIX01A official daily provider adapter-v2`
3. `ops(deploy): add adapter-v2 provenance and production preflight`
4. `feat(opportunity): add BE-024 through BE-024C shadow decision pipeline`
5. `feat(frontend): integrate V2 topic lifecycle and completed UI surfaces`
   (only after the frontend test gate is resolved or explicitly accepted)
6. `docs(research): add approved architecture history and research evidence`
   (only after the data-governance review)

### Path-group proposal

The following path groups are intentionally explicit; a blanket `git add .` is
not part of this preparation:

| Group | Candidate paths |
|---|---|
| Repo/governance | `.gitignore`, `AGENTS.md`, `README.md`, `PROJECT_CONTEXT.md`, `docs/AI_WORKLOG.md`, `docs/DAILY_PROGRESS.md`, `docs/DOCUMENTATION_GOVERNANCE.md`, `docs/DOCUMENTATION_INDEX.md`, `docs/ROADMAP.md`, `docs/WORK_ORDERS.md` |
| FIX01A market data | `services/api/src/topicpilot_api/market_data/exchange.py`, `services/api/src/topicpilot_api/market_data/registry.py`, `services/api/src/topicpilot_api/live/post_close.py`, `services/api/tests/test_no_trade_contract.py`, `docs/reports/TASK-DATA-022*` |
| Adapter-v2/P3A | `services/api/src/topicpilot_api/market_data/lineage.py`, `services/api/src/topicpilot_api/provider_lineage_cli.py`, `services/api/src/topicpilot_api/reference_check.py`, `services/api/src/topicpilot_api/reference_cli.py`, `services/api/tests/test_deployment_preflight.py`, `docs/reports/TASK-OPS-023A-P3A_ADAPTER_V2_DEPLOYMENT_PREFLIGHT_REPORT.md`, related deployment/API docs |
| Opportunity shadow | `services/api/src/topicpilot_api/topic_engine/opportunity_*.py`, `services/api/src/topicpilot_api/opportunity_shadow_*.py`, `services/api/tests/test_opportunity_*.py`, `apps/web/app/lib/opportunity-shadow-adapter.ts`, `apps/web/tests/opportunity-shadow-adapter.test.mjs`, the BE-024/024A/024B/024C reports and API/architecture docs |
| Lifecycle/frontend | `apps/web/app/components/v2/TopicListPage.tsx`, lifecycle integration tests, related frontend specs/reports and approved screenshots; hold until the frontend gate is resolved |
| Governance review hold | `reports/TASK-BE-006/**`, `fixtures/research/leader_set_candidates.v2.csv`, `fixtures/research/leader_set_candidate_pool.v1.csv`, `fixtures/research/topic_universe_mapping.v1.csv` |

The glob groups above are a preparation map, not authorization to stage every
matching file. The two review-hold groups require human confirmation first.

## Gate result

```text
REPOSITORY_HYGIENE = PASS
WORK_DIRECTORY_IGNORED = YES
VENV_LIVE_IGNORED = YES
TSBUILDINFO_IGNORED = YES
ACCIDENTAL_FILE = REMOVED
CURRENT_CHANGE_RUFF = PASS
GIT_DIFF_CHECK = PASS
BACKEND_FOCUSED_TESTS = PASS
BACKEND_FULL_TESTS = PASS (31 integration tests skipped)
FRONTEND_BUILD = PASS
FRONTEND_TESTS = 59 PASSED / 13 FAILED
FRONTEND_RELEASE_GATE = REVIEW_REQUIRED
DATA_GOVERNANCE_GATE = REVIEW_REQUIRED
SECRET_SCAN = PASS
DAILY_MARKET_RELEASE = READY (provider-only; production canary not run)
OPS_P3A_RELEASE = READY (operator handoff; production not deployed)
OPPORTUNITY_RELEASE = READY (shadow/read-only boundary)
LIFECYCLE_RELEASE = REVIEW_REQUIRED (frontend gate)
RELEASE_BASELINE_SAFE_TO_STAGE = NO
GIT_ADD_PERFORMED = NO
GIT_COMMIT_PERFORMED = NO
GIT_PUSH_PERFORMED = NO
PRODUCTION_DEPLOYMENT = NO
PRODUCTION_CANARY = NO
SCHEDULER_CHANGED = NO
NEXT_TASK_MODIFIED = NO
```

The reviewed INCLUDE subsets can be staged selectively after the listed human
reviews. The mixed working tree as a whole is not safe for broad staging yet.

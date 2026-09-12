# TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001

Date: 2026-08-16
Scope: Release-hygiene blocker closure for Stock-004 only

This report is the closure record for predecessor blocker BLK-HYGIENE-01. The authoritative predecessor is `docs/reports/TASK-OPS-REPOSITORY-HYGIENE-AND-RELEASE-CANDIDATE-REVALIDATION-001.md`.

## Fixed handoff

TASK_ID=TASK-OPS-STOCK-004-CANONICAL-RECONCILIATION-001
FINAL_STATUS=STOCK_004_CANONICAL_RECONCILIATION_COMPLETE
CANONICAL_PRE_SHA=43ace8e7cc45556e664556f78151768cd91a857a
CANONICAL_PROMOTION_SHA=606a63ab95e986ca4ffa7e295453d92b6567fe07
CANONICAL_POST_SHA=606a63ab95e986ca4ffa7e295453d92b6567fe07
SOURCE_COMMITS=06437119c0064ba8541be9734b571b8c05d8125f,429bff35368a7e90558fa5b00364c64cd8fd1d2b
CANONICAL_COMMITS=606a63ab95e986ca4ffa7e295453d92b6567fe07
STOCK_004_CAPABILITY=CODE_NAME_SEARCH_AND_FORMAL_TOPIC_FILTER
SOURCE_TO_CANONICAL_PROVENANCE=0643711 -> clean-candidate lineage -> 606a63a; 429bff3 -> clean-candidate lineage -> 606a63a; clean candidate 1875510dc87079986f24f388ee7880d953f7107b -> 606a63a
CLEAN_SOURCE_STATE=PASS
REPRODUCIBLE_DEPENDENCY_STATE=PASS
HIDDEN_DEPENDENCY_CHECK=PASS_APPLICATION_SCOPE
STOCK_SEARCH_CANONICALIZED=YES
TOPIC_FILTER_CANONICALIZED=YES
API_CONTRACT_STATE=PASS
OPENAPI_STATE=PASS
GENERATED_CLIENT_STATE=PASS
FRONTEND_WIRING_STATE=PASS
BACKEND_TESTS=PASS
FRONTEND_FOCUSED_TESTS=PASS
FRONTEND_FULL_TESTS=PASS
TYPESCRIPT=PASS
ESLINT=PASS_WITH_EXISTING_WARNING
BUILD=PASS
RUFF=PASS
COMPILE=PASS_CHANGED_BOUNDARY
OPENAPI_DRIFT=PASS
API_CLIENT_TESTS=PASS
TEST_COUNT_PRE=backend 373 passed / 41 skipped / 84 deselected; frontend 116 passed; API client 3 passed
TEST_COUNT_POST=backend 376 passed / 41 skipped / 84 deselected; frontend 142 passed; API client 3 passed
TEST_COUNT_DELTA=backend +3 passed; frontend +26 passed; API client 0
TEST_COUNT_DELTA_REASON=The three backend tests are the new production-read-model search contract tests; the 26 frontend tests are the new Stock explorer query contract suite. No test discovery reduction was used. Skips, deselections, and xfailed status were tracked separately; no xfailed result was observed.
OWNER_DIRTY_STATE_PRESERVED=YES
BLK_HYGIENE_01_CLOSED=YES
OTHER_HYGIENE_BLOCKERS_PRESERVED=YES
READY_FOR_RELEASE_CHAIN_CLOSURE=NO
READY_FOR_PRODUCTION_RELEASE=NO
APPLICATION_CODE_CHANGED=YES
DATABASE_MUTATION=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
REPORT_CREATED=YES

## Provenance and dependency determination

The predecessor inventory identified Stock-004 as the only `COMPLETE_NOT_CANONICALIZED` lineage. Commit `06437119c0064ba8541be9734b571b8c05d8125f` is an ancestor of `429bff35368a7e90558fa5b00364c64cd8fd1d2b`; therefore the required order is 0643711 first, then 429bff3. Both commits are required:

1. 0643711 supplies the formal backend/API search contract, generated OpenAPI/client types, frontend search wiring, and focused search tests.
2. 429bff3 supplies the formal topic-filter wiring and the topic-filter query contract tests on top of that search contract.

The clean candidate was rebuilt from canonical committed SHA 43ace8e7, then promoted through the source lineage and a final clean-candidate reconciliation commit:

- first source promotion: candidate commit 1130786af059c5ef09847eb794b0449ce0bb0ab;
- second source promotion: candidate commit d74c8178fdcbe1122eed17120dff529e84833107;
- final candidate reconciliation and validation commit: 1875510dc87079986f24f388ee7880d953f7107b.

The candidate used lockfile-derived npm installation with `npm ci` in `apps/web` and `packages/api-client`, plus a fresh Python 3.12 virtual environment installed from the API package's declared development constraints. No dependency directory from another dirty worktree was used as release evidence. The temporary Python environment was moved outside the candidate after validation.

## Canonical promotion and collision attribution

The initial commit-based cherry-pick of the first source promotion was blocked by an active owner modification to `apps/web/app/globals.css`. This was a proven shared-file overlap, not an application semantic collision:

- the owner hunk changes the Home opportunity-list article presentation around the existing opportunity-list rules;
- the Stock-004 hunk adds Stock toolbar search styling around the Stock explorer controls;
- the hunks are disjoint and independently attributable.

The safe exception was therefore limited to explicit path restoration for nine clean target paths and a separate Stock-only hunk application in `globals.css`. No owner hunk was overwritten, and no broad add or cleanup operation was used. The resulting canonical promotion commit 606a63a contains exactly these ten Stock-004 paths:

- `apps/web/app/components/v2/StockExplorerPage.tsx`
- `apps/web/app/globals.css`
- `apps/web/app/lib/generated-api.d.ts`
- `apps/web/app/lib/stock-api.ts`
- `apps/web/tests/stock-explorer-query.test.mjs`
- `packages/api-client/openapi.json`
- `packages/api-client/src/schema.d.ts`
- `services/api/src/topicpilot_api/production_read_model.py`
- `services/api/src/topicpilot_api/production_read_model_api.py`
- `services/api/tests/test_production_read_model_search.py`

The canonical content of all ten paths matches the validated clean candidate exactly. No residual staged changes remained after the promotion commit. `HUNK_LEVEL_RECONCILIATION_USED=YES`.
REASON=The canonical branch had a later Stock EOD/Favorites/test topology and an active owner globals.css hunk; explicit clean-path restoration plus a separate Stock toolbar hunk preserved both states without overwriting owner work.
HEAD_INDEX_WORKTREE_AUDIT=PASS
POST_RECONCILIATION_CLEAN_CANDIDATE=PASS

## Contract closure

Stock code/name search is backend-owned, case-insensitive substring search with trimmed input and the generated query contract. The frontend applies the 250 ms debounce and resets offset on query changes; it does not perform a second browser-side search over the returned result set.

Formal topic filtering uses the topic catalog returned by `fetchTopics()`, canonical topic slugs, and the formal API query. The topic selector is unavailable while the catalog is loading or unavailable, and the API result path does not apply a second browser-side topic filter. The frontend, backend, OpenAPI document, generated client declarations, and focused tests are committed together.

## Validation evidence

| Gate | Result | Evidence |
|---|---|---|
| Stock-004 focused frontend contract | PASS | 26 passed, 0 failed |
| Affected backend search tests | PASS | 3 passed, 0 failed |
| Backend release-safe suite | PASS | 376 passed, 41 skipped, 84 deselected, 0 xfailed |
| Full frontend suite | PASS | 142 passed, 0 failed |
| Generated API client tests | PASS | 3 passed |
| TypeScript | PASS | `npx tsc --noEmit` |
| ESLint | PASS with existing warning | 0 errors; one existing `FavoriteButton.tsx` dependency warning |
| Production build | PASS | production build completed |
| OpenAPI drift and route validation | PASS | required read-only routes and schema validation passed |
| Ruff | PASS | changed backend Python boundary |
| Compile | PASS | changed Python files compiled successfully |
| Diff check | PASS | staged promotion diff passed `git diff --cached --check` |
| Secret scan | PASS, heuristic | no high-risk secret matches in changed files; gitleaks was unavailable |

The predecessor's DB-enabled suite was intentionally not rerun as part of this application-only canonicalization. Its environment blocker remains authoritative: 485 passed, 5 skipped, 4 failed, and 4 errors because the approved HIST-002B historical/reference fixture environment was unavailable. This task did not create or mutate fixtures, databases, or production data.

## Owner state and release boundary

`OWNER_DIRTY_STATE_PRESERVED=YES`. Before promotion the active worktree had 174 status entries, including 18 tracked dirty paths and owner-untracked files. After promotion it still had 174 status entries; only the explicit Stock-004 target paths were committed. The unrelated owner modification in `apps/web/app/globals.css` remains unstaged, and all other owner dirty/untracked state remains untouched.

The following predecessor hygiene blockers remain open and intentionally preserved for their separate workflows:

- BLK-HYGIENE-02: documentation providers and clean-checkout documentation self-containment;
- BLK-HYGIENE-03: approved DB integration fixture/environment;
- BLK-HYGIENE-04: branch/worktree and owner disposition.

Accordingly, this report closes BLK-HYGIENE-01 only. It does not authorize release-chain closure, production release, merge, push, deployment, scheduler work, database mutation, or work on Stock-006B, historical price, Topic lifecycle, or Recommendation Engine scope.

REPOSITORY_HYGIENE_STATUS=BLOCKED_PRESERVED
STOP=STOCK_004_CANONICAL_RECONCILIATION_COMPLETE

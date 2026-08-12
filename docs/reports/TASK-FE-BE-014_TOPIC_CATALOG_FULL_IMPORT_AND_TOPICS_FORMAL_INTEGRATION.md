# TASK-FE-BE-014｜Topic Catalog Full Import & `/topics` Formal API Integration

用途：記錄 NEXT / V2 Topic Catalog 從 PostgreSQL、FastAPI 到 `/topics` 的資料完整性稽核、最小修正與驗證證據。
更新日期：2026-08-12
責任來源：PM 工單 TASK-FE-BE-014；repository/runtime evidence

## Executive Summary

問題不在「題材尚未匯入」。稽核開始時的實際 PostgreSQL 為 130 topics，130 enabled，130 distinct names，130 distinct slugs，null/blank names 0；hierarchy 107，instrument-topic relations 848。實際 `GET /api/v2/topics?limit=200&offset=0` 同樣回傳 `total=130`、`items=130`，且 130 筆 score、grade 均維持 `null`，未被改寫成 0、D 或 X。

根因位於 frontend data-source boundary：`fetchTopics()` 在沒有 `NEXT_PUBLIC_API_BASE_URL` 時會直接改用 bundled `web_snapshot.json` 加 preview identities，因此 production 可顯示一小組 synthetic topics，而不是正式 130-topic catalog。另有兩個會模糊正式 identity 的問題：formal API 名稱仍經過 preview label mapper；formal Topic Detail 仍插入 synthetic 摘要、生命週期、新聞與 related topics。

本次已將 production `/topics` 改為 formal API fail-closed；synthetic topic catalog 僅在 `NODE_ENV=development` 且明確設定 `NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW=true` 時可用。Formal API 的 name/group 原樣保留。全部題材區塊不因 score/grade/lifecycle 缺值隱藏 identity，並顯示 catalog count；Topic Map 只呈現有正式 grade 的 subset；formal Lifecycle 在 read model 尚未提供時呈現 unavailable，不使用 mock stage。

程式與 build/test 已通過，但本機 fresh served browser verification 未完成：工作區已有多個殘留 Vinext dev/start processes；新的 isolated server 與 compose web build 均未成功開始監聽。compose web 嘗試亦暴露 Docker Desktop metadata filesystem read-only，之後 host 8000/5432 連接失效。資料 volume 未刪除，既有 containers 一度仍報 healthy，但 Docker daemon 無法 recreate migrate service。正式 URL 也無法由 in-app browser 連線。因此不得宣稱 deployment 或 browser render PASS。

## Canonical Topic Catalog Count

- Canonical V2 source: `topicpilot.topics`，由既有 versioned/idempotent legacy import 建立；本任務未讀寫或修改 V1 master。
- 正式 enabled 條件：`status NOT IN ('DISABLED', 'RETIRED')`，與 formal read model 一致。
- Total: 130；enabled: 130；disabled/retired: 0。
- Distinct names: 130；distinct slugs: 130；null/blank names: 0；duplicate names/slugs: 0。
- 本次未執行 import：DB 已完整，不需也不允許從 frontend mock 建 master。
- 可比對 artifact：runtime `GET /api/v2/topics?limit=200&offset=0` 是按 slug 排序的完整 130-row catalog；本次 browser/terminal 回讀確認 `total=130` 與 `items=130`。因 Docker Desktop 後續故障，未另寫一份可能過期的 duplicated master TSV。

## PostgreSQL Evidence

| Metric | Runtime value |
|---|---:|
| topics total | 130 |
| enabled topics | 130 |
| distinct names | 130 |
| distinct slugs | 130 |
| null/blank names | 0 |
| hierarchy rows | 107 |
| instrument-topic relation rows | 848 |
| topic snapshots covered | 130 topics |
| snapshot score/grade | all null / DEFERRED per existing BE-007 evidence and API readback |

Schema/read-model evidence: `TOPIC_ROWS_SQL` starts from `topicpilot.topics`, left joins latest snapshot and parent hierarchy, and filters only disabled/retired rows. It does not require snapshot, score, grade, lifecycle, stock membership, or market-state availability.

## FastAPI Evidence

- Endpoint: `GET /api/v2/topics`; default limit 200, maximum 500. Runtime request with `limit=200&offset=0` returned 130/130.
- Detail: `GET /api/v2/topics/{slug}` queries catalog identity first and left joins optional snapshot. A catalog topic is not rejected for null score/grade/lifecycle.
- Pagination did not truncate the current 130-row catalog. Frontend explicitly requests 200.
- Runtime list evidence: 130 null scores and 130 null grades were preserved as null.
- No backend code/schema/business-rule change was required.

## Frontend Data Path Audit

Before:

`/topics` → `TopicListPage` → `fetchTopics()` → formal `/api/v2/topics` only when API base exists; otherwise bundled `web_snapshot.json` + preview identities.

Filters found:

- `topicType !== 'MAJOR_GROUP'` in TopicListPage. Current formal API emits `topicType='TOPIC'` for all 130, so it removes 0 current rows.
- Search and grade filters affect only the user-selected 「全部題材」view; default grade filter is 「全部」.
- Topic Map is grade-lane-only, so null-grade topics correctly do not enter S/A/B/D lanes.
- Lifecycle previously assigned preview/default lifecycle to every formal topic; this was removed for formal mode.
- API pagination is explicitly `limit=200`, sufficient for current N=130.

After:

- Production missing/unavailable API → unavailable empty state; no synthetic replacement.
- Preview → development plus explicit opt-in only, with existing disclosure.
- Formal names/groups → exact API identity, no preview translation/masking.
- 全部題材 → all 130 formal identities when API is available; null market-state fields display `—`/pending semantics.
- Formal Topic Detail → identity/status/constituents remain formal; synthetic summary/lifecycle/news/related/heatmap are not rendered.

## DB → API → UI Reconciliation

| Layer | Count | Result |
|---|---:|---|
| PostgreSQL enabled catalog | 130 | PASS |
| FastAPI list runtime | 130 | PASS |
| Frontend resource after formal fetch | designed to consume all 130, no default catalog filter | code/test PASS |
| Browser final rendered rows | not established | BLOCKED by local served runtime/Docker environment |

## Missing Topic List / Root Causes

- DB missing: none (0).
- API filtered: none (0).
- Pagination truncated: none (0) at N=130 and limit=200.
- Duplicate slug/name: none (0).
- Disabled: none (0).
- Previous frontend-visible missing set: formal catalog minus the small synthetic snapshot/preview set; exact deployed set could not be read because the production URL was unreachable.
- Root cause: frontend fallback dataset selected when production API origin was absent, plus presentation code that treated preview market state as if it applied to formal catalog rows.

## Implementation Changes

- `apps/web/app/lib/topic-api.ts`: preview is dev+explicit-opt-in only; production fail-closed; formal name/group preserved exactly.
- `apps/web/app/components/v2/TopicListPage.tsx`: unavailable state, catalog count/copy, formal lifecycle unavailable state, no preview lifecycle for formal topics.
- `apps/web/app/components/v2/TopicDetailPage.tsx`: formal identity can render with unavailable market-state sections; synthetic research sections only render for explicit synthetic source.
- `apps/web/tests/topic-catalog-formal-integration.test.mjs`: regression coverage for fail-closed behavior, formal identity preservation, full-fetch/default filter, and detail preview isolation.

## Formal vs Preview Behavior

| Situation | Behavior |
|---|---|
| API configured and available | use formal API only |
| API configured but fails | unavailable; no synthetic overlay |
| production API origin missing | unavailable; no synthetic catalog |
| local development + explicit preview flag | synthetic snapshot allowed with Preview disclosure |

## Topic Detail Spot Checks

Repository/read-model proof confirms detail identity is independent of snapshot fields and returns 404 only when the catalog slug is absent. The requested three post-fix browser spot checks could not be completed because no fresh frontend server could be made to listen. A PowerShell spot-check attempt also demonstrated that non-UTF-8 URL handling can corrupt Chinese slugs; this was a shell-client encoding issue, not accepted as API evidence. Follow-up should use browser navigation or a UTF-8 HTTP client once runtime is restored.

## Browser Verification

- Existing `127.0.0.1:4173/topics` was reachable but served an older in-memory placeholder bundle; it was rejected as evidence for this change.
- Fresh 3001/3220 Vinext processes did not listen despite processes being created.
- `docker compose up -d --build web` timed out and later Docker Desktop reported its container metadata database as read-only.
- Production `https://topicpilot-platform.game0962046460.chatgpt.site/topics` was unreachable from the in-app browser.
- Result: served/deployed browser render count and three clickable low-data detail routes remain pending. No deployment was performed.

## Tests / Build

- Frontend targeted Node tests: 3 passed.
- Frontend targeted ESLint: PASS.
- Frontend TypeScript `tsc --noEmit`: PASS.
- Frontend Vinext production build: PASS; `/topics` and `/topics/:slug` included.
- Backend full suite from repository root: 251 passed, 31 skipped (PostgreSQL integration env variables not configured), 1 deprecation warning.
- Live DB/API integration: PASS before Docker Desktop failure (130 → 130 reconciliation).
- OpenAPI/type sync: no schema or response type changed; existing generated `/api/v2/topics` definitions remain applicable. Frontend local interface retained nullable score/grade/lifecycle fields.
- `git diff --check`: attempted, but the repository-wide check timed out amid the very large pre-existing dirty worktree; targeted edited files passed ESLint/typecheck/build.

## Remaining Gaps

1. Repair/restart Docker Desktop so compose can recreate services and republish host ports; verify API health and unchanged 130/107/848 counts afterward.
2. Start one isolated fresh web runtime and verify browser DOM contains 130 「全部題材」 rows.
3. Click three zero/low-data formal topics and confirm identity renders without 404 and without synthetic state.
4. Deploy through the existing approved workflow, then repeat the same checks on the provided production URL.
5. Run `git diff --check` once repository/process contention is cleared.

## Fixed Output

`TOPIC_CATALOG_DB = READY`
`TOPIC_LIST_API = READY`
`TOPICS_FRONTEND_FORMAL_DATA = PARTIAL`
`ALL_ENABLED_TOPIC_NAMES_VISIBLE = FAIL`
`LEGACY_TOPIC_FALLBACK_IN_PRODUCTION = PARTIAL`

The frontend code path is corrected, but runtime/deployment evidence is required before the final three values may be promoted to READY/PASS/REMOVED.

## Post-bootstrap production reconciliation (2026-08-12)

The historical local-runtime blocker is resolved by the user-provisioned Neon
bootstrap and the existing Render/Sites deployment. The current evidence is:

- Neon `topicpilot.topics = 130`; the user also confirmed 107 hierarchy edges
  and 848 instrument-topic relations.
- `GET /api/v2/topics?limit=200&offset=0` returns `total=130` and 130 items.
- The production browser `/topics` shows `130 個題材`; null score/grade rows
  remain visible with pending semantics and do not enter grade-only Topic Map
  lanes.
- `/topics/ASIC` returns a formal detail with 34 constituents and no synthetic
  lifecycle/news/related/heatmap content.
- The configured production origin is
  `https://topicpilot-api.onrender.com`; demo fallback is disabled and no
  Preview catalog rows are used.

During this verification, formal topic detail with a null `dataDate` was found
to display `Preview` as a presentation fallback. `TopicDetailPage` now displays
`資料日期待補` for formal API data and preserves Preview only for explicit local
preview mode. This does not change catalog filtering, lifecycle, score, grade,
or identity semantics.

### Current fixed output

```text
TOPIC_CATALOG_DB = READY
TOPIC_LIST_API = READY
TOPICS_FRONTEND_FORMAL_DATA = READY
ALL_ENABLED_TOPIC_NAMES_VISIBLE = PASS
LEGACY_TOPIC_FALLBACK_IN_PRODUCTION = REMOVED
```
